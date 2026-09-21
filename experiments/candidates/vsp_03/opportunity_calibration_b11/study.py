"""Fixed low-data R0 calibration and fresh descriptive opportunity panels."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import torch

from experiments.candidates.vsp_03.opportunity_b08.opportunity import (
    EndpointCounts,
    Planner,
    fit_model,
)
from experiments.candidates.vsp_03.opportunity_b08.study import (
    activity_counter,
    artifact_hashes,
    save_panel,
)
from experiments.candidates.vsp_03.vsp03_b01.b01 import peak_rss, write_json
from experiments.candidates.vsp_03.vsp03_b02.b02 import difference, rollout, worlds


SEEDS = (22001, 22002, 22003)
REFERENCE_SEEDS = {22001: 21801, 22002: 21802, 22003: 21803}
COLLECTION_BATCHES = 4
COLLECTION_BATCH_SIZE = 128
EVAL_EPISODES = 4096
HORIZON = 40
SOURCE_REVISION = "a5a87aa223727b2673781009c90810e7a4842584"
REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
REFERENCE_RUN_ROOT = REPOSITORY_ROOT / "runs/vsp_03/opportunity_b08_21801_21803"
FROZEN_MODEL_IDENTITIES = {
    21801: {"sha256": "e16c7bb048c1544c2900fa3ae459898cdef64431adaf30613f2917c350b73bc7",
            "bytes": 37008},
    21802: {"sha256": "095dc71376317c8c6601fcf83f177ca397203bf76b349c33d8a0a4cd015f3a25",
            "bytes": 38144},
    21803: {"sha256": "f7252a0adb6bdf03d3e1494caabeb244ac872db2024d5213e31b075a029017af",
            "bytes": 39506},
}
ARMS = ("O_R0", "O_full", "R0")
CONTRASTS = (("O_R0", "O_full"), ("O_R0", "R0"))
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


def validate_references(reference_root: Path = REFERENCE_RUN_ROOT) -> dict[int, dict[str, object]]:
    """Validate all three preassigned B08 fitted models before scientific work."""
    reference_root = Path(reference_root).resolve()
    result = {}
    for old_seed in REFERENCE_SEEDS.values():
        path = reference_root / str(old_seed) / "fitted_model.json"
        actual = {"sha256": _sha256(path), "bytes": path.stat().st_size}
        expected = FROZEN_MODEL_IDENTITIES[old_seed]
        if actual != expected:
            raise ValueError(
                f"frozen B08 fitted model {old_seed} identity mismatch: "
                f"expected {expected}, got {actual}"
            )
        fitted = _load_json(path)
        metadata = fitted.get("metadata", {})
        if not metadata.get("success", fitted.get("success", False)):
            raise ValueError(f"frozen B08 fitted model {old_seed} is not converged")
        result[old_seed] = {
            "seed": old_seed,
            "path": str(path),
            "source_revision": SOURCE_REVISION,
            "identity": actual,
            "c": float(fitted["c"]),
            "p": float(fitted["p"]),
        }
    return result


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
        raise AssertionError("panel row violates native return accounting")
    return values


def _paired_rows(panels: dict[str, list[dict]], phase: np.ndarray) -> tuple[list[dict], dict]:
    raw, component_means = [], {}
    for left, right in CONTRASTS:
        key = left + "-" + right
        differences = []
        for world in range(EVAL_EPISODES):
            left_values = _row_values(panels[left][world])
            right_values = _row_values(panels[right][world])
            differences.append({name: left_values[name] - right_values[name]
                                for name in left_values})
        component_means[key] = {
            name: float(np.mean([row[name] for row in differences]))
            for name in differences[0]
        }
        for world, values in enumerate(differences):
            if len(raw) <= world:
                raw.append({"world": world, "phase": int(phase[world])})
            raw[world][key] = values
    return raw, component_means


def collect_public_endpoints(seed: int, out: Path, activity: dict) -> EndpointCounts:
    """Collect exactly four R0 batches and retain only public fit endpoints."""
    counts = EndpointCounts()
    public_x, public_ids, public_times = [], [], []
    for batch_index in range(COLLECTION_BATCHES):
        first = batch_index * COLLECTION_BATCH_SIZE
        draws, phase = worlds(seed, 100, first, COLLECTION_BATCH_SIZE)
        batch = rollout(draws, phase, rule="R0", activity=activity)
        public = {name: batch[name] for name in ("x", "episode_ids", "times")}
        counts.add_batch(public)
        np.savez_compressed(
            out / f"collection_batch_{batch_index:02d}.npz",
            draws=draws,
            phase=phase,
            public_x=public["x"],
            public_episode_ids=public["episode_ids"],
            public_times=public["times"],
        )
        public_x.append(public["x"].copy())
        public_ids.append(public["episode_ids"].copy() + first)
        public_times.append(public["times"].copy())

    np.savez_compressed(
        out / "calibration_public_endpoints.npz",
        x=np.concatenate(public_x),
        episode_ids=np.concatenate(public_ids),
        times=np.concatenate(public_times),
    )
    np.savez_compressed(out / "public_endpoint_counts.npz", counts=counts.counts)
    return counts


def evaluate_block(seed: int, reference: dict[str, object], out: Path,
                   launch_sha: str) -> dict[str, object]:
    out.mkdir(parents=True, exist_ok=False)
    wall_start = time.perf_counter()
    collection_activity = activity_counter()
    evaluation_activity = activity_counter()
    summary = {
        "seed": seed,
        "reference_seed": int(reference["seed"]),
        "reference_identity": reference["identity"],
        "launch_sha": launch_sha,
        "status": "incomplete",
        "fits_started": 0,
        "fits_completed": 0,
        "fit_calls": 0,
        "optimizer_steps": 0,
        "optimizer_steps_scope": "neural updates only; MLE iterations are reported separately",
        "gradient_steps": 0,
        "neural_model_constructions": 0,
        "neural_policy_forwards": 0,
        "panels_started": 0,
        "panels_completed": 0,
        "collection": collection_activity,
        "evaluation": evaluation_activity,
        "arms": {},
    }
    try:
        collection_start = time.perf_counter()
        counts = collect_public_endpoints(seed, out, collection_activity)
        summary["collection_wall_s"] = time.perf_counter() - collection_start
        summary["fits_started"] = 1
        summary["fit_calls"] = 1
        fit_start = time.perf_counter()
        try:
            fitted = fit_model(counts)
        finally:
            summary["fit_wall_s"] = time.perf_counter() - fit_start
        write_json(out / "fitted_model.json", fitted)
        summary["fit_optimizer_metadata"] = fitted["metadata"]
        summary["public_endpoint_transitions"] = counts.transitions
        if not fitted["metadata"]["success"]:
            raise RuntimeError(
                "O_R0 likelihood fit did not converge: " + fitted["metadata"]["message"]
            )
        summary["fits_completed"] = 1

        plan_start = time.perf_counter()
        calibrated = Planner(fitted["c"], fitted["p"])
        frozen = Planner(reference["c"], reference["p"])
        summary["planning_wall_s_both_models"] = time.perf_counter() - plan_start
        summary["model_parameters"] = {
            "O_R0": {"c": fitted["c"], "p": fitted["p"]},
            "O_full": {"c": reference["c"], "p": reference["p"],
                       "source_seed": reference["seed"], "identity": reference["identity"]},
        }
        np.savez_compressed(
            out / "planner_tables.npz",
            even_clocks=np.arange(0, 33, 2),
            O_R0_solo=calibrated.solo[::2],
            O_R0_joint=calibrated.joint[::2],
            O_full_solo=frozen.solo[::2],
            O_full_joint=frozen.joint[::2],
        )

        # Evaluation data are first created after the new public-endpoint fit is complete.
        eval_draws, eval_phase = worlds(seed, 200, 0, EVAL_EPISODES)
        np.savez_compressed(out / "evaluation_worlds.npz", draws=eval_draws, phase=eval_phase)
        panels = {}
        for name in ARMS:
            summary["panels_started"] += 1
            panel_start = time.perf_counter()
            kwargs = {"activity": evaluation_activity, "trace": True}
            if name == "R0":
                kwargs["rule"] = "R0"
            else:
                selected = calibrated if name == "O_R0" else frozen
                kwargs["scripted"] = lambda ids, t, own, x, p=selected: p.actions(x, mode="joint")
            batch = rollout(eval_draws, eval_phase, **kwargs)
            rows, absolute = save_panel(out, name, batch, eval_phase)
            panels[name] = rows
            summary["arms"][name] = {
                **absolute,
                "panel_wall_s": time.perf_counter() - panel_start,
            }
            summary["panels_completed"] += 1

        paired, components = _paired_rows(panels, eval_phase)
        write_json(out / "paired_differences.json", paired)
        summary["comparisons"] = {
            left + "-" + right: {
                **difference(panels[left], panels[right]),
                "signed_components": components[left + "-" + right],
                "scope": "descriptive development comparison",
            }
            for left, right in CONTRASTS
        }

        expected_collection = COLLECTION_BATCHES * COLLECTION_BATCH_SIZE
        if collection_activity["episodes_completed"] != expected_collection:
            raise AssertionError("R0 calibration episode count mismatch")
        if collection_activity["team_ticks"] != expected_collection * HORIZON:
            raise AssertionError("R0 calibration team tick count mismatch")
        if collection_activity["target_transitions"] != expected_collection * HORIZON * 2:
            raise AssertionError("R0 calibration target transition count mismatch")
        if evaluation_activity["episodes_completed"] != len(ARMS) * EVAL_EPISODES:
            raise AssertionError("evaluation panel episode count mismatch")
        if evaluation_activity["team_ticks"] != len(ARMS) * EVAL_EPISODES * HORIZON:
            raise AssertionError("evaluation panel team tick count mismatch")
        if evaluation_activity["target_transitions"] != len(ARMS) * EVAL_EPISODES * HORIZON * 2:
            raise AssertionError("evaluation panel target transition count mismatch")
        if collection_activity["rollout_policy_forwards"] != 0 or evaluation_activity[
                "rollout_policy_forwards"] != 0:
            raise AssertionError("B11 performed a neural policy forward")
        summary["status"] = "complete"
    except Exception as exc:
        summary["error"] = repr(exc)
        raise
    finally:
        summary["block_wall_s_through_publication_start"] = time.perf_counter() - wall_start
        summary["peak_rss_bytes"] = peak_rss()
        summary["peak_rss_scope"] = "single research process lifetime maximum, not block increment"
        summary["neural_policy_forwards"] = (
            collection_activity["rollout_policy_forwards"]
            + evaluation_activity["rollout_policy_forwards"]
        )
        summary["artifacts"] = artifact_hashes(out)
        write_json(out / "summary.json", summary)
    return summary


def aggregate(blocks: list[dict[str, object]]) -> dict[str, object]:
    if [block["seed"] for block in blocks] != list(SEEDS) or any(
            block["status"] != "complete" for block in blocks):
        raise ValueError("B11 requires all three fixed complete blocks in order")
    result = {}
    for left, right in CONTRASTS:
        key = left + "-" + right
        per_block = [block["comparisons"][key]["mean"] for block in blocks]
        component_names = blocks[0]["comparisons"][key]["signed_components"].keys()
        result[key] = {
            "per_block": per_block,
            "mean": float(np.mean(per_block)),
            "blocks": 3,
            "signed_components": {
                name: {
                    "per_block": [block["comparisons"][key]["signed_components"][name]
                                  for block in blocks],
                    "mean": float(np.mean([
                        block["comparisons"][key]["signed_components"][name]
                        for block in blocks
                    ])),
                }
                for name in component_names
            },
            "scope": "descriptive development comparison; no inferential or equivalence label",
        }
    return result


def run(out: Path, launch_sha: str, seeds=SEEDS,
        reference_root: Path | None = None) -> dict[str, object]:
    if tuple(seeds) != SEEDS:
        raise ValueError("B11 fixes seeds 22001 22002 22003")
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    reference_root = REFERENCE_RUN_ROOT if reference_root is None else Path(reference_root)
    config = {
        "object": "VSP03_OPPORTUNITY_CALIBRATION_B11",
        "seeds": list(SEEDS),
        "reference_seeds": {str(seed): REFERENCE_SEEDS[seed] for seed in SEEDS},
        "launch_sha": launch_sha,
        "source_revision": SOURCE_REVISION,
        "reference_run": str(reference_root.resolve()),
        "collection": "split100 episodes0..511 in four batches of128 under R0",
        "evaluation": "fresh split200 episodes0..4095; O_R0, frozen O_full, R0",
        "primary": "descriptive O_R0-O_full",
        "secondary": "descriptive O_R0-R0",
        "package_intervention": "same public data rights and model family; collector and amount both change",
        "planned_fits": 3,
        "planned_neural_models": 0,
        "planned_optimizer_steps": 0,
        "optimizer_steps_scope": "neural updates only; see each block fit_optimizer_metadata for MLE work",
        "planned_gradient_steps": 0,
        "planned_collection_episodes": 1_536,
        "planned_evaluation_episodes": 36_864,
        "planned_total_episodes": 38_400,
        "planned_team_ticks": 1_536_000,
        "planned_target_transitions": 3_072_000,
        "threads": 1,
        "device": "cpu",
        "selection": "fixed collector, amount, references, seeds and panels; no sweep",
        "claim_scope": "development only; no inferential, confirmation, noninferiority or equivalence claim",
    }
    write_json(out / "config.json", config)
    summary = {**config, "status": "incomplete", "blocks": [], "technical_failures": []}
    start = time.perf_counter()
    try:
        try:
            references = validate_references(reference_root)
            write_json(out / "input_digests.json", {
                "source_revision": SOURCE_REVISION,
                "reference_run": str(reference_root.resolve()),
                "models": {str(seed): references[seed] for seed in sorted(references)},
            })
        except Exception as exc:
            summary["technical_failures"].append({"stage": "reference_validation",
                                                  "error": repr(exc)})
            raise

        for seed in SEEDS:
            old_seed = REFERENCE_SEEDS[seed]
            try:
                block = evaluate_block(seed, references[old_seed], out / str(seed), launch_sha)
                summary["blocks"].append(block)
                print(json.dumps({"seed": seed, "status": "complete",
                                  "O_R0-O_full": block["comparisons"]["O_R0-O_full"]["mean"]}),
                      flush=True)
            except Exception as exc:
                summary["technical_failures"].append(
                    {"stage": "block", "seed": seed, "error": repr(exc)}
                )
                raise
        summary["comparisons"] = aggregate(summary["blocks"])
        summary["status"] = "complete"
    finally:
        summary["study_wall_s_through_publication_start"] = time.perf_counter() - start
        summary["peak_rss_bytes"] = peak_rss()
        summary["peak_rss_scope"] = "single research process lifetime maximum"
        retained = [
            _load_json(out / str(seed) / "summary.json")
            for seed in SEEDS if (out / str(seed) / "summary.json").exists()
        ]
        for name in ("fits_started", "fits_completed", "fit_calls", "optimizer_steps",
                     "gradient_steps", "neural_model_constructions", "neural_policy_forwards",
                     "panels_started", "panels_completed"):
            summary[name] = sum(block[name] for block in retained)
        summary["actual_collection_episodes"] = sum(
            block["collection"]["episodes_completed"] for block in retained
        )
        summary["actual_evaluation_episodes"] = sum(
            block["evaluation"]["episodes_completed"] for block in retained
        )
        summary["actual_total_episodes"] = (
            summary["actual_collection_episodes"] + summary["actual_evaluation_episodes"]
        )
        summary["actual_team_ticks"] = sum(
            block["collection"]["team_ticks"] + block["evaluation"]["team_ticks"]
            for block in retained
        )
        summary["actual_target_transitions"] = sum(
            block["collection"]["target_transitions"]
            + block["evaluation"]["target_transitions"] for block in retained
        )
        summary["collection_wall_s"] = sum(
            block.get("collection_wall_s", 0.0) for block in retained
        )
        summary["fit_wall_s"] = sum(
            block.get("fit_wall_s", 0.0) for block in retained
        )
        summary["planning_wall_s"] = sum(
            block.get("planning_wall_s_both_models", 0.0) for block in retained
        )
        summary["artifacts"] = _stable_root_artifacts(out)
        write_json(out / "summary.json", summary)
    return summary
