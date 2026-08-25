#!/usr/bin/env python3
"""Train, evaluate, and analyze count-preserving roster G4."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ha_ctse_process.count_preserving_roster_g4 import (
    ARM_NAMES,
    DEMAND_SUPPORT,
    EFFECTS,
    EVENT_KINDS,
    PASS_SOURCE_CONTROL,
    PROFILE_CONTRACTS,
    PROFILES,
    SOURCE_CONTROL_SCHEMA,
    SOURCE_FAMILY,
    ArmState,
    PackedSpecs,
    SeedRegistry,
    collect_arm_batch,
    evaluate_source_controls,
    initialize_matched_arms,
    load_arm_checkpoint,
    make_episode_spec,
    optimize_arm_batch,
    pack_specs,
    replay_errors,
    save_arm_checkpoint,
)
from ha_ctse_process.async_commitment_roster_g3 import (
    PASS_RESULT as STRUCTURAL_GATE_PASS,
    evaluate_information_gate as evaluate_structural_information_gate,
)


RUNNER_SCHEMA = "count_preserving_roster_g4_runner_v1"
EVALUATION_SCHEMA = "count_preserving_roster_g4_evaluation_manifest_v1"
EVALUATION_ROW_SCHEMA = "count_preserving_roster_g4_evaluation_row_v1"
AUDIT_ROW_SCHEMA = "count_preserving_roster_g4_audit_row_v1"
ANALYSIS_SCHEMA = "count_preserving_roster_g4_analysis_v1"
FORMAL_AUTHORIZATION_TOKEN = "AUTHORIZE_COUNT_PRESERVING_ROSTER_G4_FORMAL_CPU_V1"

INVALID_RESULT = "INVALID_OPERATIONAL_COUNT_ROSTER_G4"
SOURCE_INVALID_RESULT = "SOURCE_NON_IDENTIFIABLE_COUNT_ROSTER_G4"
NO_ACCESS_RESULT = "NO_ACCESS_COUNT_ROSTER_G4"
UNDERPOWERED_RESULT = "UNDERPOWERED_ACCESS_COUNT_ROSTER_G4"
SUPPORTED_RESULT = "COUNT_PRESERVING_ROSTER_SUPPORTED_G4"
ATTENTION_SUFFICIENT_RESULT = "ROSTER_ATTN_SUFFICIENT_COUNT_ROSTER_G4"
TEAM_SUFFICIENT_RESULT = "TEAM_REC_SUFFICIENT_COUNT_ROSTER_G4"
REPRESENTATION_ONLY_RESULT = "COUNT_ROSTER_REPRESENTATION_ONLY_G4"
MIXED_RESULT = "MIXED_UNDERPOWERED_COUNT_ROSTER_G4"

ACCESS_FLOOR = 0.90
GAIN_MARGIN = 0.10
NATURAL_THRESHOLD = 0.90
CONSEQUENCE_THRESHOLD = 0.10

_ATOMIC_REPLACE_ATTEMPTS = 100
_ATOMIC_REPLACE_DELAY_SECONDS = 0.05


@dataclass(frozen=True, slots=True)
class RunConfig:
    replicates: int
    updates: int
    episodes_per_update: int
    ppo_passes: int
    evaluation_episodes: int
    audit_episodes: int
    bootstrap_repetitions: int


FORMAL_CONFIG = RunConfig(
    replicates=5,
    updates=120,
    episodes_per_update=512,
    ppo_passes=4,
    evaluation_episodes=512,
    audit_episodes=128,
    bootstrap_repetitions=10_000,
)
EXERCISE_CONFIG = RunConfig(
    replicates=1,
    updates=2,
    episodes_per_update=64,
    ppo_passes=1,
    evaluation_episodes=32,
    audit_episodes=16,
    bootstrap_repetitions=200,
)
EVALUATION_PROFILES = (
    "iid",
    "heldout_cardinality",
    "heldout_gap",
    "heldout_joint",
)
EVALUATION_MODES = ("deterministic", "stochastic")


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.parent / f".{path.name}.{os.getpid()}.tmp"
    temporary.write_text(text, encoding="utf-8")
    for attempt in range(_ATOMIC_REPLACE_ATTEMPTS):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt + 1 == _ATOMIC_REPLACE_ATTEMPTS:
                raise
            time.sleep(_ATOMIC_REPLACE_DELAY_SECONDS)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _atomic_text(
        path,
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
    )


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    text = "".join(
        json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in rows
    )
    _atomic_text(path, text)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if type(payload) is not dict:
        raise ValueError(f"{path} must contain an exact JSON object")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        payload = json.loads(line)
        if type(payload) is not dict:
            raise ValueError(f"{path}:{line_number} is not an exact object")
        rows.append(payload)
    return rows


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _config_for_formal(formal: bool) -> RunConfig:
    return FORMAL_CONFIG if formal else EXERCISE_CONFIG


def _validate_source_commit(source_commit: str) -> None:
    if re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("source_commit must be an exact 40-character lowercase hash")


def _require_cpu_one_thread() -> None:
    if torch.version.cuda is not None or "+cpu" not in torch.__version__:
        raise RuntimeError("registered useful-effect execution requires CPU-only torch")
    torch.set_num_threads(1)
    if torch.get_num_threads() != 1:
        raise RuntimeError("torch thread contract is not one")


def _training_specs(
    *,
    replicate: int,
    update_index: int,
    count: int,
    seed_registry: SeedRegistry,
) -> tuple[Any, ...]:
    start = replicate * 100_000_000 + update_index * count
    return tuple(
        make_episode_spec(
            "train",
            base_id=start + index,
            seed_registry=seed_registry,
        )
        for index in range(count)
    )


def train_run(
    root: Path,
    *,
    source_commit: str,
    formal: bool,
    authorization_token: str | None = None,
) -> Path:
    _require_cpu_one_thread()
    _validate_source_commit(source_commit)
    root = Path(root)
    if root.exists():
        raise FileExistsError("run root must be fresh")
    if formal and authorization_token != FORMAL_AUTHORIZATION_TOKEN:
        raise ValueError("formal authorization token mismatch")
    if not formal and authorization_token is not None:
        raise ValueError("nonformal exercise cannot carry a formal token")
    root.mkdir(parents=True)
    config = _config_for_formal(formal)
    seed_registry = SeedRegistry()
    checkpoint_references: list[str] = []
    exposure: dict[str, dict[str, int]] = {}
    telemetry: dict[str, float] = {
        "maximum_replay_logp_error": 0.0,
        "maximum_replay_value_error": 0.0,
        "maximum_forbidden_gradient": 0.0,
        "maximum_gradient": 0.0,
    }

    controls = evaluate_source_controls()
    structural_controls = evaluate_structural_information_gate()
    controls["structural_gate_result"] = structural_controls["result"]
    controls["structural_gate_case_count"] = structural_controls["case_count"]
    controls["structural_gate_pass"] = (
        structural_controls["result"] == STRUCTURAL_GATE_PASS
    )
    controls.update({"source_commit": source_commit, "run_formal": formal})
    _write_json(root / "source_controls.json", controls)

    for replicate in range(config.replicates):
        states = initialize_matched_arms(
            replicate=replicate,
            source_commit=source_commit,
            seed_registry=seed_registry,
        )
        for update_index in range(config.updates):
            packed = pack_specs(
                _training_specs(
                    replicate=replicate,
                    update_index=update_index,
                    count=config.episodes_per_update,
                    seed_registry=seed_registry,
                )
            )
            for arm in ARM_NAMES:
                state = states[arm]
                batch = collect_arm_batch(state, packed)
                errors = replay_errors(state.model, batch)
                telemetry["maximum_replay_logp_error"] = max(
                    telemetry["maximum_replay_logp_error"], errors["logp"]
                )
                telemetry["maximum_replay_value_error"] = max(
                    telemetry["maximum_replay_value_error"], errors["value"]
                )
                metrics = optimize_arm_batch(
                    state, batch, passes=config.ppo_passes
                )
                telemetry["maximum_forbidden_gradient"] = max(
                    telemetry["maximum_forbidden_gradient"],
                    float(metrics["maximum_forbidden_gradient"]),
                )
                telemetry["maximum_gradient"] = max(
                    telemetry["maximum_gradient"],
                    float(metrics["maximum_gradient"]),
                )
            if (update_index + 1) % max(1, min(10, config.updates)) == 0:
                _write_json(
                    root / "progress.json",
                    {
                        "schema": RUNNER_SCHEMA,
                        "formal": formal,
                        "status": "TRAINING",
                        "replicate": replicate,
                        "update": update_index + 1,
                    },
                )
        for arm in ARM_NAMES:
            state = states[arm]
            checkpoint = (
                root
                / "checkpoints"
                / arm
                / f"replicate_{replicate}"
                / f"update_{config.updates}.pt"
            )
            save_arm_checkpoint(checkpoint, state)
            checkpoint_references.append(_relative(checkpoint, root))
            exposure[f"{arm}:replicate_{replicate}"] = {
                "updates": state.completed_updates,
                "optimizer_steps": state.optimizer_steps,
                "episodes_completed": state.episodes_completed,
            }

    manifest = {
        "schema": RUNNER_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": source_commit,
        "formal": formal,
        "authorization_token": authorization_token,
        "backend": "cpu",
        "torch_version": torch.__version__,
        "torch_threads": torch.get_num_threads(),
        "config": asdict(config),
        "seed_registry": asdict(seed_registry),
        "checkpoint_references": sorted(checkpoint_references),
        "training_exposure": exposure,
        "telemetry": telemetry,
        "status": "TRAIN_COMPLETE",
    }
    _write_json(root / "manifest.json", manifest)
    _write_json(
        root / "progress.json",
        {
            "schema": RUNNER_SCHEMA,
            "formal": formal,
            "status": "TRAIN_COMPLETE",
            "replicates": config.replicates,
            "updates": config.updates,
        },
    )
    return root / "manifest.json"


def _evaluation_generator(seed: int) -> torch.Generator:
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    return generator


def _load_trained_state(
    root: Path,
    manifest: Mapping[str, Any],
    *,
    arm: str,
    replicate: int,
) -> ArmState:
    states = initialize_matched_arms(
        replicate=replicate,
        source_commit=str(manifest["source_commit"]),
        seed_registry=SeedRegistry(**manifest["seed_registry"]),
    )
    state = states[arm]
    config = manifest["config"]
    checkpoint = (
        root
        / "checkpoints"
        / arm
        / f"replicate_{replicate}"
        / f"update_{config['updates']}.pt"
    )
    load_arm_checkpoint(
        checkpoint, state, source_commit=str(manifest["source_commit"])
    )
    return state


def _evaluation_rows(
    state: ArmState,
    *,
    profile: str,
    mode: str,
    count: int,
    formal: bool,
    seed_registry: SeedRegistry,
) -> list[dict[str, Any]]:
    profile_index = EVALUATION_PROFILES.index(profile)
    base_start = (
        2_000_000_000
        + state.replicate * 10_000_000
        + profile_index * 1_000_000
    )
    specs = tuple(
        make_episode_spec(
            profile,
            base_id=base_start + index,
            seed_registry=seed_registry,
        )
        for index in range(count)
    )
    packed = pack_specs(specs)
    with torch.no_grad():
        logits = state.model.edit_logits(state.arm, packed)
        probabilities = torch.softmax(logits, dim=-1)
        if mode == "deterministic":
            actions = logits.argmax(dim=-1)
        elif mode == "stochastic":
            generator = _evaluation_generator(
                seed_registry.evaluation
                + state.replicate * seed_registry.replicate_offset
                + profile_index * 10_000
            )
            actions = torch.multinomial(
                probabilities, 1, generator=generator
            ).squeeze(-1)
        else:
            raise ValueError("unknown evaluation mode")
    rows: list[dict[str, Any]] = []
    for index, spec in enumerate(specs):
        choice = int(actions[index])
        rows.append(
            {
                "schema": EVALUATION_ROW_SCHEMA,
                "source_family": SOURCE_FAMILY,
                "source_commit": state.source_commit,
                "formal": formal,
                "arm": state.arm,
                "replicate": state.replicate,
                "profile": profile,
                "mode": mode,
                "episode_index": index,
                "base_id": spec.base_id,
                "source_cluster": f"{profile}:{spec.base_id}",
                "active_count": spec.active_count,
                "demand": list(spec.demand),
                "deficit": spec.deficit,
                "event_kind": spec.event_kind,
                "gap": spec.gap,
                "duty": spec.duty,
                "duplicate_demand": max(spec.demand) > 1,
                "zero_demand_label": any(value == 0 for value in spec.demand),
                "choice": choice,
                "optimal": choice == spec.deficit,
                "optimal_probability": float(probabilities[index, spec.deficit]),
                "utility": spec.utility(choice),
            }
        )
    return rows


def _audit_rows(
    state: ArmState,
    *,
    count: int,
    formal: bool,
    seed_registry: SeedRegistry,
) -> list[dict[str, Any]]:
    if state.arm != "ROSTER_SUM":
        raise ValueError("causal audit is defined only for ROSTER_SUM")
    base_start = 3_000_000_000 + state.replicate * 10_000_000
    rows: list[dict[str, Any]] = []
    for index in range(count):
        spec = make_episode_spec(
            "heldout_joint",
            base_id=base_start + index,
            seed_registry=seed_registry,
        )
        intervened, source_optimal_after = spec.intervene_roster()
        if spec.query != intervened.query:
            raise AssertionError("roster intervention changed the base query")
        natural_packed = pack_specs((spec,))
        intervened_packed = pack_specs((intervened,))
        with torch.no_grad():
            natural_logits = state.model.edit_logits(state.arm, natural_packed)
            intervened_logits = state.model.edit_logits(
                state.arm, intervened_packed
            )
            natural_probabilities = torch.softmax(natural_logits, dim=-1)[0]
            intervened_probabilities = torch.softmax(intervened_logits, dim=-1)[0]
        natural_choice = int(natural_logits.argmax(dim=-1)[0])
        adapted_choice = int(intervened_logits.argmax(dim=-1)[0])
        replay_utility = intervened.utility(natural_choice)
        adapted_utility = intervened.utility(adapted_choice)
        rows.append(
            {
                "schema": AUDIT_ROW_SCHEMA,
                "source_family": SOURCE_FAMILY,
                "source_commit": state.source_commit,
                "formal": formal,
                "arm": state.arm,
                "replicate": state.replicate,
                "audit_index": index,
                "base_id": spec.base_id,
                "source_cluster": f"audit:{spec.base_id}",
                "active_count": spec.active_count,
                "demand": list(spec.demand),
                "deficit": spec.deficit,
                "source_optimal_after": source_optimal_after,
                "duplicate_demand": max(spec.demand) > 1,
                "zero_demand_label": any(value == 0 for value in spec.demand),
                "natural_choice": natural_choice,
                "adapted_choice": adapted_choice,
                "natural_optimal_probability": float(
                    natural_probabilities[spec.deficit]
                ),
                "natural_utility": spec.utility(natural_choice),
                "roster_intervention_tv": float(
                    0.5
                    * (natural_probabilities - intervened_probabilities)
                    .abs()
                    .sum()
                ),
                "replayed_utility": replay_utility,
                "adapted_utility": adapted_utility,
                "adapted_minus_replayed_utility": adapted_utility
                - replay_utility,
            }
        )
    return rows


def evaluate_run(root: Path) -> Path:
    _require_cpu_one_thread()
    root = Path(root)
    manifest = _read_json(root / "manifest.json")
    if manifest.get("status") != "TRAIN_COMPLETE":
        raise ValueError("training manifest is not complete")
    config = RunConfig(**manifest["config"])
    seed_registry = SeedRegistry(**manifest["seed_registry"])
    references: list[str] = []
    audit_rows: list[dict[str, Any]] = []
    for replicate in range(config.replicates):
        for arm in ARM_NAMES:
            state = _load_trained_state(
                root, manifest, arm=arm, replicate=replicate
            )
            for profile in EVALUATION_PROFILES:
                for mode in EVALUATION_MODES:
                    rows = _evaluation_rows(
                        state,
                        profile=profile,
                        mode=mode,
                        count=config.evaluation_episodes,
                        formal=bool(manifest["formal"]),
                        seed_registry=seed_registry,
                    )
                    path = (
                        root
                        / "evaluation"
                        / arm
                        / f"replicate_{replicate}"
                        / f"{profile}_{mode}.jsonl"
                    )
                    _write_jsonl(path, rows)
                    references.append(_relative(path, root))
            if arm == "ROSTER_SUM":
                audit_rows.extend(
                    _audit_rows(
                        state,
                        count=config.audit_episodes,
                        formal=bool(manifest["formal"]),
                        seed_registry=seed_registry,
                    )
                )
    audit_path = root / "causal_audit.jsonl"
    _write_jsonl(audit_path, audit_rows)
    evaluation_manifest = {
        "schema": EVALUATION_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": manifest["source_commit"],
        "formal": manifest["formal"],
        "backend": "cpu",
        "torch_threads": torch.get_num_threads(),
        "config": asdict(config),
        "evaluation_references": sorted(references),
        "audit_reference": _relative(audit_path, root),
        "source_control_reference": "source_controls.json",
        "status": "EVALUATION_COMPLETE",
    }
    _write_json(root / "evaluation_manifest.json", evaluation_manifest)
    return root / "evaluation_manifest.json"


def _finite_number(name: str, value: object) -> float:
    if type(value) not in (int, float) or isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    return normalized


def select_result_branch(predicate_inputs: Mapping[str, object]) -> str:
    required_booleans = (
        "operational_valid",
        "source_identifiable",
        "battery_pass",
        "battery_confident_fail",
    )
    for name in required_booleans:
        if predicate_inputs.get(name) not in (True, False) or type(
            predicate_inputs.get(name)
        ) is not bool:
            raise ValueError(f"{name} must be an exact boolean")
    numeric = {
        name: _finite_number(name, predicate_inputs.get(name))
        for name in (
            "sum_lcb",
            "sum_ucb",
            "g_attn_lcb",
            "g_attn_ucb",
            "g_team_lcb",
            "g_team_ucb",
        )
    }
    if not predicate_inputs["operational_valid"]:
        return INVALID_RESULT
    if not predicate_inputs["source_identifiable"]:
        return SOURCE_INVALID_RESULT
    if numeric["sum_ucb"] < ACCESS_FLOOR:
        return NO_ACCESS_RESULT
    if numeric["sum_lcb"] < ACCESS_FLOOR <= numeric["sum_ucb"]:
        return UNDERPOWERED_RESULT
    if (
        numeric["g_attn_lcb"] > GAIN_MARGIN
        and numeric["g_team_lcb"] > GAIN_MARGIN
        and predicate_inputs["battery_pass"]
    ):
        return SUPPORTED_RESULT
    if numeric["g_attn_ucb"] <= GAIN_MARGIN:
        return ATTENTION_SUFFICIENT_RESULT
    if numeric["g_team_ucb"] <= GAIN_MARGIN:
        return TEAM_SUFFICIENT_RESULT
    if (
        numeric["g_attn_lcb"] > GAIN_MARGIN
        and numeric["g_team_lcb"] > GAIN_MARGIN
        and predicate_inputs["battery_confident_fail"]
    ):
        return REPRESENTATION_ONLY_RESULT
    return MIXED_RESULT


def _bootstrap_intervals(
    arrays: Mapping[str, np.ndarray],
    *,
    repetitions: int,
    seed: int,
) -> dict[str, dict[str, float]]:
    if not arrays:
        raise ValueError("bootstrap requires arrays")
    reference_shape = next(iter(arrays.values())).shape
    if len(reference_shape) != 2 or any(
        array.shape != reference_shape for array in arrays.values()
    ):
        raise ValueError("bootstrap arrays must share replicate x cluster shape")
    replicate_count, cluster_count = reference_shape
    rng = np.random.default_rng(seed)
    draws = {name: np.empty(repetitions, dtype=np.float64) for name in arrays}
    offset = 0
    while offset < repetitions:
        batch = min(100, repetitions - offset)
        replicate_indices = rng.integers(
            0, replicate_count, size=(batch, replicate_count)
        )
        cluster_indices = rng.integers(
            0, cluster_count, size=(batch, replicate_count, cluster_count)
        )
        for name, array in arrays.items():
            sampled = array[
                replicate_indices[:, :, None],
                cluster_indices,
            ]
            draws[name][offset : offset + batch] = np.nanmean(
                sampled, axis=(1, 2)
            )
        offset += batch
    result: dict[str, dict[str, float]] = {}
    for name, array in arrays.items():
        result[name] = {
            "mean": float(np.nanmean(array)),
            "lcb95": float(np.nanquantile(draws[name], 0.025)),
            "ucb95": float(np.nanquantile(draws[name], 0.975)),
        }
    return result


def _primary_arrays(
    rows: Sequence[Mapping[str, Any]], *, config: RunConfig
) -> dict[str, np.ndarray]:
    by_arm_rep: dict[tuple[str, int], list[Mapping[str, Any]]] = {}
    for arm in ARM_NAMES:
        for replicate in range(config.replicates):
            selected = [
                row
                for row in rows
                if row["arm"] == arm
                and row["replicate"] == replicate
                and row["profile"] == "heldout_joint"
                and row["mode"] == "deterministic"
            ]
            selected.sort(key=lambda row: int(row["base_id"]))
            if len(selected) != config.evaluation_episodes:
                raise ValueError("primary evaluation inventory is incomplete")
            by_arm_rep[(arm, replicate)] = selected
    arrays: dict[str, np.ndarray] = {}
    for arm in ARM_NAMES:
        arrays[arm] = np.array(
            [
                [float(row["utility"]) for row in by_arm_rep[(arm, replicate)]]
                for replicate in range(config.replicates)
            ],
            dtype=np.float64,
        )
    for replicate in range(config.replicates):
        clusters = [
            [row["source_cluster"] for row in by_arm_rep[(arm, replicate)]]
            for arm in ARM_NAMES
        ]
        if any(cluster != clusters[0] for cluster in clusters[1:]):
            raise ValueError("primary arms do not share paired source clusters")
    arrays["g_attn"] = arrays["ROSTER_SUM"] - arrays["ROSTER_ATTN"]
    arrays["g_team"] = arrays["ROSTER_SUM"] - arrays["TEAM_REC"]
    return arrays


def _audit_arrays(
    rows: Sequence[Mapping[str, Any]], *, config: RunConfig
) -> dict[str, np.ndarray]:
    metrics = (
        "natural_optimal_probability",
        "natural_utility",
        "roster_intervention_tv",
        "adapted_minus_replayed_utility",
    )
    result: dict[str, list[list[float]]] = {name: [] for name in metrics}
    result["duplicate_utility"] = []
    result["zero_demand_utility"] = []
    for replicate in range(config.replicates):
        selected = [row for row in rows if row["replicate"] == replicate]
        selected.sort(key=lambda row: int(row["audit_index"]))
        if len(selected) != config.audit_episodes:
            raise ValueError("audit inventory is incomplete")
        for name in metrics:
            result[name].append([float(row[name]) for row in selected])
        result["duplicate_utility"].append(
            [
                float(row["natural_utility"])
                if row["duplicate_demand"]
                else float("nan")
                for row in selected
            ]
        )
        result["zero_demand_utility"].append(
            [
                float(row["natural_utility"])
                if row["zero_demand_label"]
                else float("nan")
                for row in selected
            ]
        )
    return {
        name: np.asarray(values, dtype=np.float64)
        for name, values in result.items()
    }


def _collect_evaluation_rows(root: Path, evaluation: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for reference in evaluation["evaluation_references"]:
        rows.extend(_read_jsonl(root / reference))
    return rows


def _expected_source_cells(profile: str) -> set[tuple[tuple[int, ...], int, str]]:
    return {
        (tuple(demand), deficit, event_kind)
        for active_count in PROFILE_CONTRACTS[profile].active_counts
        for demand in DEMAND_SUPPORT[active_count]
        for deficit, value in enumerate(demand)
        if value > 0
        for event_kind in EVENT_KINDS
    }


def _evaluation_ledger_balance_pass(
    rows: Sequence[Mapping[str, Any]], *, config: RunConfig, require_complete: bool
) -> bool:
    for arm in ARM_NAMES:
        for replicate in range(config.replicates):
            for profile in EVALUATION_PROFILES:
                expected = _expected_source_cells(profile)
                for mode in EVALUATION_MODES:
                    selected = [
                        row
                        for row in rows
                        if row["arm"] == arm
                        and row["replicate"] == replicate
                        and row["profile"] == profile
                        and row["mode"] == mode
                    ]
                    counts = {cell: 0 for cell in expected}
                    for row in selected:
                        cell = (
                            tuple(int(value) for value in row["demand"]),
                            int(row["deficit"]),
                            str(row["event_kind"]),
                        )
                        if cell not in counts:
                            return False
                        counts[cell] += 1
                    if require_complete and any(value == 0 for value in counts.values()):
                        return False
                    if max(counts.values()) - min(counts.values()) > 1:
                        return False
    return True


def analyze_run(root: Path) -> Path:
    root = Path(root)
    manifest = _read_json(root / "manifest.json")
    evaluation = _read_json(root / "evaluation_manifest.json")
    config = RunConfig(**manifest["config"])
    rows = _collect_evaluation_rows(root, evaluation)
    audit_rows = _read_jsonl(root / evaluation["audit_reference"])
    controls = _read_json(root / evaluation["source_control_reference"])
    primary = _primary_arrays(rows, config=config)
    primary_intervals = _bootstrap_intervals(
        primary,
        repetitions=config.bootstrap_repetitions,
        seed=int(manifest["seed_registry"]["bootstrap"]),
    )
    audit = _audit_arrays(audit_rows, config=config)
    audit_intervals = _bootstrap_intervals(
        audit,
        repetitions=config.bootstrap_repetitions,
        seed=int(manifest["seed_registry"]["bootstrap"]) + 1,
    )

    arm_names = ("TEAM_REC", "ROSTER_ATTN", "ROSTER_SUM")
    sum_interval = primary_intervals["ROSTER_SUM"]
    source_identification = {
        "source_control_pass": controls.get("result") == PASS_SOURCE_CONTROL
        and controls.get("all_source_checks") is True
        and controls.get("structural_gate_pass") is True,
        "evaluation_inventory_pass": len(evaluation["evaluation_references"])
        == config.replicates
        * len(ARM_NAMES)
        * len(EVALUATION_PROFILES)
        * len(EVALUATION_MODES),
        "evaluation_ledger_balance_pass": _evaluation_ledger_balance_pass(
            rows,
            config=config,
            require_complete=bool(manifest["formal"]),
        ),
        "natural_quota_pass": all(
            len([row for row in audit_rows if row["replicate"] == replicate])
            >= FORMAL_CONFIG.audit_episodes
            for replicate in range(config.replicates)
        ),
    }
    source_identifiable = all(source_identification.values())
    telemetry = manifest["telemetry"]
    operational_errors: list[str] = []
    if float(telemetry["maximum_replay_logp_error"]) > 1e-6:
        operational_errors.append("replay_logp")
    if float(telemetry["maximum_replay_value_error"]) > 1e-6:
        operational_errors.append("replay_value")
    if float(telemetry["maximum_forbidden_gradient"]) != 0.0:
        operational_errors.append("gradient_fence")
    if float(telemetry["maximum_gradient"]) <= 0.0:
        operational_errors.append("no_gradient")
    operational_valid = not operational_errors

    battery_pass = (
        audit_intervals["natural_optimal_probability"]["lcb95"]
        >= NATURAL_THRESHOLD
        and audit_intervals["natural_utility"]["lcb95"] >= NATURAL_THRESHOLD
        and audit_intervals["roster_intervention_tv"]["lcb95"]
        > CONSEQUENCE_THRESHOLD
        and audit_intervals["adapted_minus_replayed_utility"]["lcb95"]
        > CONSEQUENCE_THRESHOLD
        and audit_intervals["duplicate_utility"]["lcb95"]
        >= NATURAL_THRESHOLD
        and audit_intervals["zero_demand_utility"]["lcb95"]
        >= NATURAL_THRESHOLD
    )
    confident_fail = any(
        audit_intervals[name]["ucb95"] <= threshold
        for name, threshold in (
            ("natural_optimal_probability", NATURAL_THRESHOLD),
            ("natural_utility", NATURAL_THRESHOLD),
            ("roster_intervention_tv", CONSEQUENCE_THRESHOLD),
            ("adapted_minus_replayed_utility", CONSEQUENCE_THRESHOLD),
            ("duplicate_utility", NATURAL_THRESHOLD),
            ("zero_demand_utility", NATURAL_THRESHOLD),
        )
    )
    predicate_inputs = {
        "operational_valid": operational_valid,
        "source_identifiable": source_identifiable,
        "sum_lcb": sum_interval["lcb95"],
        "sum_ucb": sum_interval["ucb95"],
        "g_attn_lcb": primary_intervals["g_attn"]["lcb95"],
        "g_attn_ucb": primary_intervals["g_attn"]["ucb95"],
        "g_team_lcb": primary_intervals["g_team"]["lcb95"],
        "g_team_ucb": primary_intervals["g_team"]["ucb95"],
        "battery_pass": battery_pass,
        "battery_confident_fail": confident_fail,
    }
    result = select_result_branch(predicate_inputs)
    aggregate_exposure: dict[str, dict[str, int]] = {}
    for arm in ARM_NAMES:
        cells = [
            manifest["training_exposure"][f"{arm}:replicate_{replicate}"]
            for replicate in range(config.replicates)
        ]
        aggregate_exposure[arm] = {
            key: sum(int(cell[key]) for cell in cells)
            for key in ("updates", "optimizer_steps", "episodes_completed")
        }
    payload = {
        "schema": ANALYSIS_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": manifest["source_commit"],
        "formal": manifest["formal"],
        "status": "COMPLETE",
        "operational_valid": operational_valid,
        "operational_errors": operational_errors,
        "source_identifiable": source_identifiable,
        "source_identification": source_identification,
        "tested_arm": "ROSTER_SUM",
        "metrics": {
            "arm_utility": {
                arm: primary_intervals[arm] for arm in arm_names
            },
            "g_attn": primary_intervals["g_attn"],
            "g_team": primary_intervals["g_team"],
            "battery": audit_intervals,
        },
        "predicate_inputs": predicate_inputs,
        "result": result,
        "training_exposure": aggregate_exposure,
        "config": asdict(config),
    }
    _write_json(root / "analysis_result.json", payload)
    return root / "analysis_result.json"


def _validate_evaluation_row(
    row: Mapping[str, Any],
    *,
    source_commit: str,
    formal: bool,
    arm: str,
    replicate: int,
    profile: str,
    mode: str,
) -> None:
    for key, expected in (
        ("schema", EVALUATION_ROW_SCHEMA),
        ("source_family", SOURCE_FAMILY),
        ("source_commit", source_commit),
        ("formal", formal),
        ("arm", arm),
        ("replicate", replicate),
        ("profile", profile),
        ("mode", mode),
    ):
        if row.get(key) != expected or type(row.get(key)) is not type(expected):
            if key == "source_commit":
                raise ValueError("evaluation source commit mismatch")
            raise ValueError(f"evaluation row {key} mismatch")
    demand = row.get("demand")
    if type(demand) is not list or len(demand) != 4 or any(
        type(value) is not int or value < 0 for value in demand
    ):
        raise ValueError("evaluation demand is malformed")
    choice = row.get("choice")
    if type(choice) is not int or choice not in EFFECTS:
        raise ValueError("evaluation choice is malformed")
    active_count = row.get("active_count")
    if type(active_count) is not int or sum(demand) != active_count:
        raise ValueError("evaluation active count/demand mismatch")
    service = list(row.get("demand"))
    deficit = row.get("deficit")
    if type(deficit) is not int or deficit not in EFFECTS:
        raise ValueError("evaluation deficit is malformed")
    service[deficit] -= 1
    service[choice] += 1
    expected_utility = sum(
        min(service[index], demand[index]) for index in EFFECTS
    ) / active_count
    if abs(_finite_number("utility", row.get("utility")) - expected_utility) > 1e-12:
        raise ValueError("evaluation utility does not match realized service")


def validate_run_artifacts(root: Path, *, require_formal: bool) -> None:
    root = Path(root)
    manifest = _read_json(root / "manifest.json")
    evaluation = _read_json(root / "evaluation_manifest.json")
    analysis = _read_json(root / "analysis_result.json")
    if manifest.get("schema") != RUNNER_SCHEMA:
        raise ValueError("training manifest schema mismatch")
    if evaluation.get("schema") != EVALUATION_SCHEMA:
        raise ValueError("evaluation manifest schema mismatch")
    if analysis.get("schema") != ANALYSIS_SCHEMA:
        raise ValueError("analysis schema mismatch")
    if any(
        artifact.get("source_family") != SOURCE_FAMILY
        for artifact in (manifest, evaluation, analysis)
    ):
        raise ValueError("artifact source family mismatch")
    source_commit = manifest.get("source_commit")
    if type(source_commit) is not str:
        raise ValueError("source commit is missing")
    _validate_source_commit(source_commit)
    formal = manifest.get("formal")
    if type(formal) is not bool:
        raise ValueError("formal flag must be exact boolean")
    if require_formal and formal is not True:
        raise ValueError("formal validation requires formal=true")
    if formal and manifest.get("authorization_token") != FORMAL_AUTHORIZATION_TOKEN:
        raise ValueError("formal manifest authorization token mismatch")
    if not formal and manifest.get("authorization_token") is not None:
        raise ValueError("nonformal manifest carries a formal token")
    if (
        manifest.get("status") != "TRAIN_COMPLETE"
        or evaluation.get("status") != "EVALUATION_COMPLETE"
        or manifest.get("backend") != "cpu"
        or evaluation.get("backend") != "cpu"
        or manifest.get("torch_threads") != 1
        or evaluation.get("torch_threads") != 1
        or "+cpu" not in str(manifest.get("torch_version"))
    ):
        raise ValueError("train/evaluation backend or completion contract mismatch")
    if evaluation.get("formal") is not formal or analysis.get("formal") is not formal:
        raise ValueError("formal flags disagree across artifacts")
    if evaluation.get("source_commit") != source_commit or analysis.get("source_commit") != source_commit:
        raise ValueError("artifact source commit mismatch")
    expected_config = FORMAL_CONFIG if require_formal else _config_for_formal(formal)
    if manifest.get("config") != asdict(expected_config):
        raise ValueError("run config does not match registered budget")
    if evaluation.get("config") != manifest.get("config"):
        raise ValueError("evaluation config does not match training manifest")
    if manifest.get("seed_registry") != asdict(SeedRegistry()):
        raise ValueError("run seed registry does not match G4 contract")
    config = RunConfig(**manifest["config"])
    expected_checkpoints = config.replicates * len(ARM_NAMES)
    references = manifest.get("checkpoint_references")
    if type(references) is not list or len(references) != expected_checkpoints:
        raise ValueError("checkpoint inventory mismatch")
    for reference in references:
        path = root / reference
        if not path.is_file():
            raise ValueError("checkpoint reference is missing")
        payload = torch.load(path, map_location="cpu", weights_only=False)
        if (
            type(payload) is not dict
            or payload.get("source_commit") != source_commit
            or payload.get("completed_updates") != config.updates
            or payload.get("optimizer_steps") != config.updates * config.ppo_passes
            or payload.get("episodes_completed")
            != config.updates * config.episodes_per_update
        ):
            raise ValueError("checkpoint provenance/exposure mismatch")
    expected_evaluations = (
        config.replicates
        * len(ARM_NAMES)
        * len(EVALUATION_PROFILES)
        * len(EVALUATION_MODES)
    )
    evaluation_references = evaluation.get("evaluation_references")
    if type(evaluation_references) is not list or len(evaluation_references) != expected_evaluations:
        raise ValueError("evaluation reference inventory mismatch")
    for reference in evaluation_references:
        match = re.fullmatch(
            r"evaluation/(TEAM_REC|ROSTER_ATTN|ROSTER_SUM)/replicate_(\d+)/(iid|heldout_cardinality|heldout_gap|heldout_joint)_(deterministic|stochastic)\.jsonl",
            reference,
        )
        if match is None:
            raise ValueError("evaluation reference path is malformed")
        arm, replicate_text, profile, mode = match.groups()
        replicate = int(replicate_text)
        if not 0 <= replicate < config.replicates:
            raise ValueError("evaluation replicate is outside the registered range")
        rows = _read_jsonl(root / reference)
        if len(rows) != config.evaluation_episodes:
            raise ValueError("evaluation row count mismatch")
        for row in rows:
            _validate_evaluation_row(
                row,
                source_commit=source_commit,
                formal=formal,
                arm=arm,
                replicate=replicate,
                profile=profile,
                mode=mode,
            )
    all_evaluation_rows = _collect_evaluation_rows(root, evaluation)
    if not _evaluation_ledger_balance_pass(
        all_evaluation_rows,
        config=config,
        require_complete=require_formal,
    ):
        raise ValueError("evaluation demand/deficit/event ledger is imbalanced")
    audit_rows = _read_jsonl(root / str(evaluation.get("audit_reference")))
    if len(audit_rows) != config.replicates * config.audit_episodes:
        raise ValueError("audit row count mismatch")
    for row in audit_rows:
        if row.get("source_commit") != source_commit:
            raise ValueError("audit source commit mismatch")
        if (
            row.get("formal") is not formal
            or row.get("schema") != AUDIT_ROW_SCHEMA
            or row.get("source_family") != SOURCE_FAMILY
            or row.get("arm") != "ROSTER_SUM"
            or type(row.get("replicate")) is not int
            or not 0 <= int(row["replicate"]) < config.replicates
        ):
            raise ValueError("audit schema/formal mismatch")
        for name in (
            "natural_optimal_probability",
            "natural_utility",
            "roster_intervention_tv",
            "replayed_utility",
            "adapted_utility",
            "adapted_minus_replayed_utility",
        ):
            _finite_number(name, row.get(name))
        demand = row.get("demand")
        active_count = row.get("active_count")
        deficit = row.get("deficit")
        source_optimal_after = row.get("source_optimal_after")
        natural_choice = row.get("natural_choice")
        adapted_choice = row.get("adapted_choice")
        if (
            type(demand) is not list
            or len(demand) != 4
            or any(type(value) is not int or value < 0 for value in demand)
            or type(active_count) is not int
            or sum(demand) != active_count
            or type(deficit) is not int
            or deficit not in EFFECTS
            or type(source_optimal_after) is not int
            or source_optimal_after not in EFFECTS
            or type(natural_choice) is not int
            or natural_choice not in EFFECTS
            or type(adapted_choice) is not int
            or adapted_choice not in EFFECTS
        ):
            raise ValueError("audit source/action fields are malformed")
        natural_counts = list(demand)
        natural_counts[deficit] -= 1
        intervened_counts = list(natural_counts)
        intervened_counts[source_optimal_after] -= 1
        intervened_counts[deficit] += 1

        def realized_utility(counts: list[int], choice: int) -> float:
            service = list(counts)
            service[choice] += 1
            return sum(
                min(service[index], demand[index]) for index in EFFECTS
            ) / active_count

        expected_natural = realized_utility(natural_counts, natural_choice)
        expected_replayed = realized_utility(intervened_counts, natural_choice)
        expected_adapted = realized_utility(intervened_counts, adapted_choice)
        for name, actual, expected in (
            ("natural_utility", row.get("natural_utility"), expected_natural),
            ("replayed_utility", row.get("replayed_utility"), expected_replayed),
            ("adapted_utility", row.get("adapted_utility"), expected_adapted),
            (
                "adapted_minus_replayed_utility",
                row.get("adapted_minus_replayed_utility"),
                expected_adapted - expected_replayed,
            ),
        ):
            if abs(float(actual) - expected) > 1e-12:
                raise ValueError(f"audit utility mismatch: {name}")
        for name in ("natural_optimal_probability", "roster_intervention_tv"):
            value = float(row[name])
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"audit probability mismatch: {name}")
    controls = _read_json(root / str(evaluation.get("source_control_reference")))
    if (
        controls.get("source_commit") != source_commit
        or controls.get("source_family") != SOURCE_FAMILY
        or controls.get("schema") != SOURCE_CONTROL_SCHEMA
        or controls.get("run_formal") is not formal
        or controls.get("result") != PASS_SOURCE_CONTROL
        or controls.get("structural_gate_pass") is not True
        or controls.get("structural_gate_result") != STRUCTURAL_GATE_PASS
    ):
        raise ValueError("source-control evidence mismatch")
    exposure = manifest.get("training_exposure")
    if type(exposure) is not dict:
        raise ValueError("training exposure is missing")
    for replicate in range(config.replicates):
        for arm in ARM_NAMES:
            expected = {
                "updates": config.updates,
                "optimizer_steps": config.updates * config.ppo_passes,
                "episodes_completed": config.updates * config.episodes_per_update,
            }
            if exposure.get(f"{arm}:replicate_{replicate}") != expected:
                raise ValueError("training exposure mismatch")
    if analysis.get("status") != "COMPLETE" or analysis.get("operational_errors") != []:
        raise ValueError("analysis is not operationally complete")
    predicates = analysis.get("predicate_inputs")
    if type(predicates) is not dict or select_result_branch(predicates) != analysis.get("result"):
        raise ValueError("analysis result does not follow frozen selector")
    residue = [
        path
        for path in root.rglob("*")
        if path.name.endswith(".tmp") or "latest" in path.name.lower()
    ]
    if residue:
        raise ValueError("run retains temporary/latest residue")


def validate_formal_result(root: Path) -> None:
    validate_run_artifacts(root, require_formal=True)


def run_exercise(root: Path, *, source_commit: str) -> Path:
    train_run(root, source_commit=source_commit, formal=False)
    evaluate_run(root)
    analysis = analyze_run(root)
    validate_run_artifacts(root, require_formal=False)
    return analysis


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    train = subparsers.add_parser("train")
    train.add_argument("--run-root", type=Path, required=True)
    train.add_argument("--source-commit", required=True)
    train.add_argument("--formal", action="store_true")
    train.add_argument("--authorization-token")

    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--run-root", type=Path, required=True)

    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--run-root", type=Path, required=True)

    exercise = subparsers.add_parser("exercise")
    exercise.add_argument("--run-root", type=Path, required=True)
    exercise.add_argument("--source-commit", required=True)

    args = parser.parse_args()
    if args.command == "train":
        result = train_run(
            args.run_root,
            source_commit=args.source_commit,
            formal=args.formal,
            authorization_token=args.authorization_token,
        )
    elif args.command == "evaluate":
        result = evaluate_run(args.run_root)
    elif args.command == "analyze":
        result = analyze_run(args.run_root)
    else:
        result = run_exercise(args.run_root, source_commit=args.source_commit)
    print(result)


if __name__ == "__main__":
    main()
