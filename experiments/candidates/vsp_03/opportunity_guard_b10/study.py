"""One fixed t22 feasibility guard on the published B08 development panels."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import torch

from experiments.candidates.vsp_03.opportunity_b08.opportunity import Planner
from experiments.candidates.vsp_03.opportunity_b08.study import (
    activity_counter,
    artifact_hashes,
    first_coupling_disagreements,
    save_panel,
)
from experiments.candidates.vsp_03.vsp03_b01.b01 import peak_rss, write_json
from experiments.candidates.vsp_03.vsp03_b02.b02 import difference, metrics, rollout


SEEDS = (21801, 21802, 21803)
EVAL_EPISODES = 4096
HORIZON = 40
SOURCE_REVISION = "a5a87aa223727b2673781009c90810e7a4842584"
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
SOURCE_RUN_ROOT = REPOSITORY_ROOT / "runs/vsp_03/opportunity_b08_21801_21803"
REQUIRED_INPUTS = (
    "fitted_model.json",
    "evaluation_worlds.npz",
    "G.json",
    "O.json",
    "O_self.json",
    "O_self_decisions.npz",
)
REFERENCE_ARMS = ("G", "O", "O_self")
CONTRASTS = (("guard", "O_self"), ("O", "guard"), ("guard", "G"))
ROW_FIELDS = (
    "return",
    "fixed_clocks",
    "pending_clocks",
    "eligible_decisions",
    "blocked_pending",
    "blocked_final_clocks",
    "expired_at_own_clock",
    "blocked_final_ready",
    "submit_blocks_partner_next_clock",
    "submit_blocks_partner_last_clock",
    "wait_when_ready",
    "submit_when_not_ready",
)
JOB_FIELDS = ("success", "attempt", "failed_attempt", "non_submission", "waiting_ticks")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_root_artifacts(out: Path) -> dict[str, dict[str, object]]:
    result = {}
    for name in ("config.json", "input_digests.json"):
        path = out / name
        if path.is_file():
            result[name] = {"sha256": _sha256(path), "bytes": path.stat().st_size}
    return result


def validate_inputs(source_run: Path = SOURCE_RUN_ROOT) -> dict[int, dict[str, object]]:
    """Validate every required B08 input against its block artifact record."""
    source_run = Path(source_run).resolve()
    result = {}
    for seed in SEEDS:
        block = source_run / str(seed)
        summary_path = block / "summary.json"
        summary = _load_json(summary_path)
        if summary.get("status") != "complete" or summary.get("seed") != seed:
            raise ValueError(f"B08 block {seed} is not the fixed complete seed")
        artifacts = summary.get("artifacts", {})
        verified = {}
        for name in REQUIRED_INPUTS:
            path = block / name
            expected = artifacts.get(name)
            if not isinstance(expected, dict):
                raise ValueError(f"B08 block {seed} lacks artifact identity for {name}")
            actual = {"sha256": _sha256(path), "bytes": path.stat().st_size}
            expected_identity = {
                "sha256": expected.get("sha256"),
                "bytes": expected.get("bytes"),
            }
            if actual != expected_identity:
                raise ValueError(
                    f"B08 block {seed} artifact mismatch for {name}: "
                    f"expected {expected_identity}, got {actual}"
                )
            verified[name] = actual
        result[seed] = {
            "seed": seed,
            "source_block": str(block),
            "source_revision": SOURCE_REVISION,
            "summary": summary,
            "artifacts": verified,
        }
    return result


def _reference_metrics(rows: list[dict[str, object]]) -> dict[str, float | int]:
    result = metrics(rows)
    for name in ROW_FIELDS[6:]:
        result[name + "_per_team"] = float(np.mean([row[name] for row in rows]))
    return result


def _validate_reference_metrics(seed: int, arm: str, actual: dict, expected: dict) -> None:
    for name, value in actual.items():
        if name not in expected or not np.isclose(value, expected[name], rtol=0, atol=1e-12):
            raise ValueError(
                f"B08 block {seed} {arm} metric mismatch for {name}: "
                f"expected {expected.get(name)!r}, got {value!r}"
            )


def _load_source_block(manifest: dict[str, object]) -> dict[str, object]:
    seed = int(manifest["seed"])
    block = Path(manifest["source_block"])
    summary = manifest["summary"]
    fitted = _load_json(block / "fitted_model.json")
    metadata = fitted.get("metadata", {})
    if not metadata.get("success", fitted.get("success", False)):
        raise ValueError(f"B08 block {seed} fitted model is not converged")
    c, p = float(fitted["c"]), float(fitted["p"])

    with np.load(block / "evaluation_worlds.npz", allow_pickle=False) as saved:
        if not {"draws", "phase"}.issubset(saved.files):
            raise ValueError(f"B08 block {seed} evaluation worlds lack draws/phase")
        draws = saved["draws"].copy()
        phase = saved["phase"].copy()
    if draws.shape != (EVAL_EPISODES, HORIZON, 2) or phase.shape != (EVAL_EPISODES,):
        raise ValueError(f"B08 block {seed} evaluation world shape mismatch")

    rows = {arm: _load_json(block / f"{arm}.json") for arm in REFERENCE_ARMS}
    for arm, arm_rows in rows.items():
        if len(arm_rows) != EVAL_EPISODES:
            raise ValueError(f"B08 block {seed} {arm} row count mismatch")
        for world, row in enumerate(arm_rows):
            if row.get("world") != world or row.get("phase_zero_identity") != int(phase[world]):
                raise ValueError(f"B08 block {seed} {arm} world identity mismatch at {world}")
        actual = _reference_metrics(arm_rows)
        _validate_reference_metrics(seed, arm, actual, summary["arms"][arm])

    with np.load(block / "O_self_decisions.npz", allow_pickle=False) as saved:
        needed = {"x", "actions", "episode_ids", "times"}
        if not needed.issubset(saved.files):
            raise ValueError(f"B08 block {seed} O_self decisions lack required arrays")
        isolated = {name: saved[name].copy() for name in needed}
    n = len(isolated["x"])
    if (isolated["x"].shape != (n, 14) or
            any(isolated[name].shape != (n,) for name in ("actions", "episode_ids", "times")) or
            np.any((isolated["episode_ids"] < 0) | (isolated["episode_ids"] >= EVAL_EPISODES))):
        raise ValueError(f"B08 block {seed} O_self decision shape or identity mismatch")

    return {
        "seed": seed,
        "c": c,
        "p": p,
        "draws": draws,
        "phase": phase,
        "rows": rows,
        "metrics": {arm: _reference_metrics(rows[arm]) for arm in REFERENCE_ARMS},
        "isolated": isolated,
        "summary": summary,
    }


def guard_actions(planner: Planner, x: np.ndarray) -> np.ndarray:
    """Published O_self, except force SUBMIT at the fixed t22 two-job boundary."""
    observations = np.asarray(x)
    if observations.ndim != 2 or observations.shape[1] != 14:
        raise ValueError("guard observations must have shape (rows, 14)")
    raw_time = observations[:, 0].astype(np.float64) * HORIZON
    clocks = np.rint(raw_time).astype(np.int64)
    if not np.all(np.isfinite(raw_time)) or not np.all(np.abs(raw_time - clocks) <= 1e-4):
        raise ValueError("guard observation time must encode an integer clock")
    partner_pending = observations[:, 11] == 1
    return planner.actions(observations, mode="self") | ((clocks == 22) & partner_pending)


def _row_values(row: dict[str, object]) -> dict[str, float]:
    values = {name: float(row[name]) for name in ROW_FIELDS}
    for name in JOB_FIELDS:
        values[name + "_per_team"] = float(sum(job[name] for job in row["jobs"]))
    expected = (
        200 * values["success_per_team"]
        - 10 * values["attempt_per_team"]
        - values["waiting_ticks_per_team"]
    ) / 400
    if not np.isclose(values["return"], expected, rtol=0, atol=1e-12):
        raise AssertionError("paired source row violates native return accounting")
    return values


def _paired_rows(panels: dict[str, list[dict]], phase: np.ndarray) -> tuple[list[dict], dict]:
    raw, component_means = [], {}
    for left, right in CONTRASTS:
        key = left + "-" + right
        diffs = []
        for world in range(EVAL_EPISODES):
            left_values = _row_values(panels[left][world])
            right_values = _row_values(panels[right][world])
            diffs.append({name: left_values[name] - right_values[name] for name in left_values})
        component_means[key] = {
            name: float(np.mean([row[name] for row in diffs])) for name in diffs[0]
        }
        if not np.isclose(
                component_means[key]["return"],
                (200 * component_means[key]["success_per_team"]
                 - 10 * component_means[key]["attempt_per_team"]
                 - component_means[key]["waiting_ticks_per_team"]) / 400,
                rtol=0, atol=1e-12):
            raise AssertionError(f"{key} mean components do not reconstruct J")
        for world, values in enumerate(diffs):
            if len(raw) <= world:
                raw.append({"world": world, "phase": int(phase[world])})
            raw[world][key] = values
    return raw, component_means


def _guard_disagreements(guard: dict, isolated: dict, guard_rows: list[dict],
                         isolated_rows: list[dict]) -> list[dict]:
    result = first_coupling_disagreements(guard, isolated, guard_rows, isolated_rows)
    if len(result) != EVAL_EPISODES:
        raise AssertionError("first-disagreement output must retain every world")
    for record in result:
        found = record["first_disagreement"]
        if found is None:
            continue
        if (found["t"] != 22 or found["public_x"][11] != 1 or
                found["direction"] != "joint_SUBMIT_self_WAIT"):
            raise AssertionError("guard/self first disagreement is outside the fixed legal intervention")
        found["direction"] = "guard_SUBMIT_self_WAIT"
    return result


def evaluate_block(source: dict[str, object], out: Path, launch_sha: str) -> dict[str, object]:
    seed = int(source["seed"])
    out.mkdir(parents=True, exist_ok=False)
    wall_start = time.perf_counter()
    activity = activity_counter()
    summary = {
        "seed": seed,
        "launch_sha": launch_sha,
        "status": "incomplete",
        "fits_started": 0,
        "fits_completed": 0,
        "optimizer_steps": 0,
        "gradient_steps": 0,
        "panels_started": 0,
        "panels_completed": 0,
        "evaluation": activity,
        "reference_metrics": source["metrics"],
    }
    try:
        plan_start = time.perf_counter()
        planner = Planner(source["c"], source["p"])
        summary["planning_wall_s"] = time.perf_counter() - plan_start
        summary["planner_parameters"] = {"c": source["c"], "p": source["p"]}

        summary["panels_started"] = 1
        panel_start = time.perf_counter()
        batch = rollout(
            source["draws"],
            source["phase"],
            scripted=lambda ids, t, own, x: guard_actions(planner, x),
            activity=activity,
            trace=True,
        )
        guard_rows, guard_metrics = save_panel(out, "guard", batch, source["phase"])
        summary["guard_panel_wall_s"] = time.perf_counter() - panel_start
        summary["panels_completed"] = 1
        panels = {"guard": guard_rows, **source["rows"]}

        guard_decisions = {name: batch[name] for name in ("x", "actions", "episode_ids", "times")}
        disagreements = _guard_disagreements(
            guard_decisions, source["isolated"], guard_rows, source["rows"]["O_self"]
        )
        write_json(out / "first_guard_self_disagreements.json", disagreements)
        summary["guard_activation"] = {
            "worlds": sum(r["first_disagreement"] is not None for r in disagreements),
            "guard_SUBMIT_self_WAIT": sum(
                r["first_disagreement"] is not None and
                r["first_disagreement"]["direction"] == "guard_SUBMIT_self_WAIT"
                for r in disagreements
            ),
            "guard_WAIT_self_SUBMIT": 0,
            "all_first_disagreements_t22_two_pending": True,
        }

        paired, components = _paired_rows(panels, source["phase"])
        write_json(out / "paired_differences.json", paired)
        summary["arms"] = {"guard": guard_metrics, **source["metrics"]}
        summary["comparisons"] = {
            left + "-" + right: {
                **difference(panels[left], panels[right]),
                "signed_components": components[left + "-" + right],
            }
            for left, right in CONTRASTS
        }
        fixed = difference(source["rows"]["O"], source["rows"]["O_self"])
        expected_fixed = source["summary"]["comparisons"]["O-O_self"]
        if not np.isclose(fixed["mean"], expected_fixed["mean"], rtol=0, atol=1e-15):
            raise AssertionError("fixed B08 O-O_self contrast does not match its block summary")
        summary["fixed_O-O_self"] = fixed

        if activity["episodes_completed"] != EVAL_EPISODES:
            raise AssertionError("guard panel episode count mismatch")
        if activity["team_ticks"] != EVAL_EPISODES * HORIZON:
            raise AssertionError("guard panel team tick count mismatch")
        if activity["target_transitions"] != EVAL_EPISODES * HORIZON * 2:
            raise AssertionError("guard panel target transition count mismatch")
        if activity["rollout_policy_forwards"] != 0:
            raise AssertionError("guard panel performed a neural policy forward")
        summary["status"] = "complete"
    except Exception as exc:
        summary["error"] = repr(exc)
        raise
    finally:
        summary["block_wall_s_through_publication_start"] = time.perf_counter() - wall_start
        summary["peak_rss_bytes"] = peak_rss()
        summary["peak_rss_scope"] = "single research process lifetime maximum, not block increment"
        summary["artifacts"] = artifact_hashes(out)
        write_json(out / "summary.json", summary)
    return summary


def aggregate(blocks: list[dict[str, object]]) -> tuple[dict, dict]:
    if [block["seed"] for block in blocks] != list(SEEDS) or any(
            block["status"] != "complete" for block in blocks):
        raise ValueError("B10 requires all three fixed complete B08 blocks in order")
    comparisons = {}
    for left, right in CONTRASTS:
        key = left + "-" + right
        values = [block["comparisons"][key]["mean"] for block in blocks]
        block_component_names = blocks[0]["comparisons"][key]["signed_components"].keys()
        components = {
            name: {
                "per_block": [block["comparisons"][key]["signed_components"][name]
                              for block in blocks],
                "mean": float(np.mean([block["comparisons"][key]["signed_components"][name]
                                       for block in blocks])),
            }
            for name in block_component_names
        }
        comparisons[key] = {"per_block": values, "mean": float(np.mean(values)),
                            "blocks": 3, "signed_components": components}
    denominator_values = [block["fixed_O-O_self"]["mean"] for block in blocks]
    denominator = float(np.mean(denominator_values))
    numerator = comparisons["guard-O_self"]["mean"]
    fraction = None if denominator == 0 else numerator / denominator
    majority = bool(
        all(value > 0 for value in comparisons["guard-O_self"]["per_block"])
        and fraction is not None and fraction > 0.5
    )
    reading = {
        "label": "MAJORITY_EXPLANATION" if majority else "NOT_MAJORITY_EXPLANATION",
        "guard_improves_J_all_three_blocks": bool(
            all(value > 0 for value in comparisons["guard-O_self"]["per_block"])
        ),
        "signed_capture_fraction": fraction,
        "capture_numerator_mean_guard-O_self": numerator,
        "capture_denominator_mean_fixed_O-O_self": denominator,
        "capture_denominator_per_block": denominator_values,
        "threshold": "positive guard-O_self in all three blocks and signed fraction > 0.5",
        "scope": "descriptive old-development-panel reading; no causal mediation, equivalence, or confirmation claim",
    }
    return comparisons, reading


def run(out: Path, launch_sha: str, seeds=SEEDS, source_run: Path | None = None) -> dict:
    if tuple(seeds) != SEEDS:
        raise ValueError("B10 fixes the published B08 seeds 21801 21802 21803")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    source_run = SOURCE_RUN_ROOT if source_run is None else Path(source_run)
    config = {
        "object": "VSP03_OPPORTUNITY_GUARD_B10",
        "seeds": list(SEEDS),
        "launch_sha": launch_sha,
        "source_revision": SOURCE_REVISION,
        "source_run": str(source_run.resolve()),
        "intervention": "published fitted O_self; force SUBMIT only at t22 with partner pending",
        "planned_fits": 0,
        "planned_optimizer_steps": 0,
        "planned_gradient_steps": 0,
        "planned_guard_panels": 3,
        "planned_evaluation_episodes": 12_288,
        "planned_team_ticks": 491_520,
        "planned_target_transitions": 983_040,
        "reference_panels_replayed": 0,
        "new_worlds": 0,
        "threads": 1,
        "device": "cpu",
        "dtype": "float64 planner; inherited float64 worlds",
        "selection": "one fixed Pro-proposed feasibility boundary; no threshold or score search",
    }
    write_json(out / "config.json", config)
    summary = {**config, "status": "incomplete", "blocks": [], "technical_failures": []}
    start = time.perf_counter()
    try:
        try:
            manifests = validate_inputs(source_run)
            write_json(out / "input_digests.json", {
                "source_revision": SOURCE_REVISION,
                "source_run": str(source_run.resolve()),
                "blocks": {str(seed): {"seed": seed, "source_block": manifests[seed]["source_block"],
                                       "artifacts": manifests[seed]["artifacts"]}
                           for seed in SEEDS},
            })
            # Load and semantically validate every fixed source block before the
            # first result-bearing guard rollout.
            sources = {seed: _load_source_block(manifests[seed]) for seed in SEEDS}
        except Exception as exc:
            summary["technical_failures"].append({"stage": "input_validation", "error": repr(exc)})
            raise

        for seed in SEEDS:
            try:
                block = evaluate_block(sources[seed], out / str(seed), launch_sha)
                summary["blocks"].append(block)
                print(json.dumps({"seed": seed, "status": "complete",
                                  "guard-O_self": block["comparisons"]["guard-O_self"]["mean"]}),
                      flush=True)
            except Exception as exc:
                summary["technical_failures"].append(
                    {"stage": "guard_panel", "seed": seed, "error": repr(exc)}
                )
                raise
        summary["comparisons"], summary["reading"] = aggregate(summary["blocks"])
        summary["status"] = "complete"
    finally:
        summary["study_wall_s_through_publication_start"] = time.perf_counter() - start
        summary["peak_rss_bytes"] = peak_rss()
        summary["peak_rss_scope"] = "single research process lifetime maximum"
        retained = [
            _load_json(out / str(seed) / "summary.json")
            for seed in SEEDS if (out / str(seed) / "summary.json").exists()
        ]
        summary["fits_started"] = sum(block["fits_started"] for block in retained)
        summary["fits_completed"] = sum(block["fits_completed"] for block in retained)
        summary["optimizer_steps"] = sum(block["optimizer_steps"] for block in retained)
        summary["gradient_steps"] = sum(block["gradient_steps"] for block in retained)
        summary["panels_started"] = sum(block["panels_started"] for block in retained)
        summary["panels_completed"] = sum(block["panels_completed"] for block in retained)
        summary["actual_evaluation_episodes"] = sum(
            block["evaluation"]["episodes_completed"] for block in retained
        )
        summary["actual_team_ticks"] = sum(block["evaluation"]["team_ticks"] for block in retained)
        summary["actual_target_transitions"] = sum(
            block["evaluation"]["target_transitions"] for block in retained
        )
        summary["actual_planning_reconstructions"] = len(retained)
        summary["planning_wall_s"] = sum(block.get("planning_wall_s", 0.0) for block in retained)
        # Supervisor-owned stdout/status files can still change after the study
        # returns.  Only stable runner-written scientific root inputs are bound
        # here; each block separately binds its completed scientific artifacts.
        summary["artifacts"] = _stable_root_artifacts(out)
        write_json(out / "summary.json", summary)
    return summary
