#!/usr/bin/env python3
"""Independent train/evaluate/analyze runner for the frozen G1 source."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sys
import time
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ha_ctse_process.ehc_g1 import (
    CHECKPOINT_SCHEMA,
    HIDDEN_WIDTH,
    SeedRegistry,
    collect_rollout,
    initialize_matched_arms,
    load_checkpoint,
    optimize_rollout,
    save_checkpoint,
)
from ha_ctse_process.temporal_duty_g1 import (
    HORIZON,
    TemporalDutyG1Env,
    make_episode_spec,
)


SOURCE_FAMILY = "ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1"
RUNNER_SCHEMA = "access_positive_mechanism_matched_ehc_g1_runner_v1"
ANALYSIS_SCHEMA = "access_positive_mechanism_matched_ehc_g1_analysis_v1"
EVALUATION_ROW_SCHEMA = "access_positive_mechanism_matched_ehc_g1_eval_row_v1"
SOURCE_CONTROL_SCHEMA = "access_positive_mechanism_matched_ehc_g1_controls_v1"
AUDIT_ROW_SCHEMA = "access_positive_mechanism_matched_ehc_g1_audit_row_v1"
MANIFEST_SCHEMA = "access_positive_mechanism_matched_ehc_g1_manifest_v1"

_ATOMIC_REPLACE_ATTEMPTS = 100
_ATOMIC_REPLACE_RETRY_DELAY_SECONDS = 0.05


def _replace_with_permission_retry(temporary: Path, destination: Path) -> None:
    for attempt in range(_ATOMIC_REPLACE_ATTEMPTS):
        try:
            os.replace(temporary, destination)
            return
        except PermissionError:
            if attempt + 1 == _ATOMIC_REPLACE_ATTEMPTS:
                raise
            time.sleep(_ATOMIC_REPLACE_RETRY_DELAY_SECONDS)

ARMS = ("OR", "DUM", "EHC")
REPLICATES = tuple(range(5))
EVALUATION_PROFILES = (
    "iid_deterministic",
    "iid_stochastic",
    "heldout_deterministic",
    "heldout_stochastic",
)
DETERMINISTIC_PROFILES = frozenset(
    ("iid_deterministic", "heldout_deterministic")
)
EVALUATION_EPISODES = 256
EVALUATION_BASE_IDS = 128
BOOTSTRAP_REPETITIONS = 10_000
FORMAL_AUTHORIZATION_TOKEN = (
    "AUTHORIZE_ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1_FORMAL_CPU_V1"
)
SEED_REGISTRY = asdict(SeedRegistry())
FORMAL_BUDGET: dict[str, Any] = {
    "environments": 16,
    "horizon": 80,
    "updates": 250,
    "episodes_per_arm": 4_000,
    "transitions_per_arm": 320_000,
    "base_optimizer_steps": 1_000,
    "event_optimizer_steps": {"OR": 0, "DUM": 1_000, "EHC": 1_000},
    "ppo_passes": 4,
    "evaluation_episodes_per_cell": 256,
    "bootstrap_repetitions": 10_000,
}


def configure_cpu_runtime() -> None:
    """Apply the frozen one-backend, one-thread runtime fence."""

    if torch.cuda.is_initialized():
        raise RuntimeError("G1 cannot start after a CUDA runtime was initialized")
    torch.set_num_threads(1)
    try:
        torch.set_num_interop_threads(1)
    except RuntimeError:
        if torch.get_num_interop_threads() != 1:
            raise
    if torch.get_num_threads() != 1 or torch.get_num_interop_threads() != 1:
        raise RuntimeError("G1 requires exactly one Torch CPU thread")


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise ValueError(f"{name} must be a non-boolean finite number")
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"{name} must be finite")
    return converted


def _exact_bool(value: object, name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{name} must be boolean")
    return value


def _triplet(value: object, name: str) -> tuple[float, float, float]:
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError(f"{name} must contain exactly K=1, K=2, K>=3")
    return tuple(_finite_number(item, f"{name}[{index}]") for index, item in enumerate(value))  # type: ignore[return-value]


def select_result_branch(
    *,
    operational_valid: object,
    source_identifiable: object,
    max_arm_lcb: object,
    max_arm_ucb: object,
    g_dum_lcb: object,
    g_dum_ucb: object,
    g_or_lcb: object,
    g_or_ucb: object,
    k_lcbs: object,
    k_ucbs: object,
    i_tv_lcb: object,
    i_tv_ucb: object,
    c_keep_lcb: object,
    c_keep_ucb: object,
    c_renew_lcb: object,
    c_renew_ucb: object,
    c_keep_mean: object,
    c_renew_mean: object,
) -> str:
    """Apply the frozen G1 first-match result without importing any G0 selector."""

    try:
        operational = _exact_bool(operational_valid, "operational_valid")
        identifiable = _exact_bool(source_identifiable, "source_identifiable")
        numeric = {
            name: _finite_number(value, name)
            for name, value in {
                "max_arm_lcb": max_arm_lcb,
                "max_arm_ucb": max_arm_ucb,
                "g_dum_lcb": g_dum_lcb,
                "g_dum_ucb": g_dum_ucb,
                "g_or_lcb": g_or_lcb,
                "g_or_ucb": g_or_ucb,
                "i_tv_lcb": i_tv_lcb,
                "i_tv_ucb": i_tv_ucb,
                "c_keep_lcb": c_keep_lcb,
                "c_keep_ucb": c_keep_ucb,
                "c_renew_lcb": c_renew_lcb,
                "c_renew_ucb": c_renew_ucb,
                "c_keep_mean": c_keep_mean,
                "c_renew_mean": c_renew_mean,
            }.items()
        }
        k_lower = _triplet(k_lcbs, "k_lcbs")
        k_upper = _triplet(k_ucbs, "k_ucbs")
        if any(lower > upper for lower, upper in zip(k_lower, k_upper, strict=True)):
            raise ValueError("K confidence bounds are inverted")
        for prefix in ("max_arm", "g_dum", "g_or", "i_tv", "c_keep", "c_renew"):
            if numeric[f"{prefix}_lcb"] > numeric[f"{prefix}_ucb"]:
                raise ValueError(f"{prefix} confidence bounds are inverted")
    except (TypeError, ValueError):
        return "INVALID_OPERATIONAL_G1"

    if not operational:
        return "INVALID_OPERATIONAL_G1"
    if not identifiable:
        return "SOURCE_NON_IDENTIFIABLE_G1"
    if numeric["max_arm_ucb"] < 0.80:
        return "NO_ACCESS_THIS_G1_SOURCE"
    if numeric["max_arm_lcb"] < 0.80 and numeric["max_arm_ucb"] >= 0.80:
        return "UNDERPOWERED_ACCESS_G1"

    gains_pass = numeric["g_dum_lcb"] > 0.10 and numeric["g_or_lcb"] > 0.10
    k_pass = sum(lower > 0.10 for lower in k_lower) >= 2
    intervals_pass = (
        k_pass
        and numeric["i_tv_lcb"] > 0.10
        and numeric["c_keep_lcb"] > 0.0
        and numeric["c_renew_lcb"] > 0.0
    )
    points_pass = (
        numeric["c_keep_mean"] >= 0.02 and numeric["c_renew_mean"] >= 0.02
    )
    if gains_pass and intervals_pass and points_pass:
        return "COMMITMENT_SUPPORTED_G1"

    k_confident_failure = sum(upper > 0.10 for upper in k_upper) < 2
    interval_confident_failure = (
        k_confident_failure
        or numeric["i_tv_ucb"] <= 0.10
        or numeric["c_keep_ucb"] <= 0.0
        or numeric["c_renew_ucb"] <= 0.0
    )
    if gains_pass and interval_confident_failure:
        return "REPRESENTATION_ONLY_G1"
    if numeric["g_dum_ucb"] <= 0.10 or numeric["g_or_ucb"] <= 0.10:
        return "ORDINARY_EXPLANATION_G1"
    return "MIXED_UNDERPOWERED_G1"


def hierarchical_bootstrap(
    rows: Sequence[Mapping[str, object]],
    *,
    repetitions: int,
    base_ids_per_replicate: int,
    seed: int,
) -> list[list[dict[str, object]]]:
    """Resample replicate triples, then base IDs, retaining whole paired clusters."""

    if type(repetitions) is not int or repetitions <= 0:
        raise ValueError("repetitions must be a positive integer")
    if type(base_ids_per_replicate) is not int or base_ids_per_replicate <= 0:
        raise ValueError("base_ids_per_replicate must be a positive integer")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    by_replicate_base: dict[tuple[int, int], list[dict[str, object]]] = {}
    replicate_values: set[int] = set()
    for original in rows:
        if not isinstance(original, Mapping):
            raise ValueError("bootstrap rows must be mappings")
        replicate = original.get("replicate")
        base_id = original.get("base_id")
        if type(replicate) is not int or type(base_id) is not int:
            raise ValueError("bootstrap row identities must be integers")
        if replicate not in REPLICATES or not 0 <= base_id < base_ids_per_replicate:
            raise ValueError("bootstrap row identity is outside the registered inventory")
        replicate_values.add(replicate)
        by_replicate_base.setdefault((replicate, base_id), []).append(dict(original))
    if replicate_values != set(REPLICATES):
        raise ValueError("bootstrap requires all five paired replicate triples")
    for replicate in REPLICATES:
        for base_id in range(base_ids_per_replicate):
            if (replicate, base_id) not in by_replicate_base:
                raise ValueError("bootstrap cluster inventory is incomplete")

    generator = np.random.Generator(np.random.PCG64(seed))
    output: list[list[dict[str, object]]] = []
    for _ in range(repetitions):
        replicate_draws = generator.integers(0, len(REPLICATES), size=len(REPLICATES))
        sample: list[dict[str, object]] = []
        for replicate_draw, selected_index in enumerate(replicate_draws.tolist()):
            replicate = REPLICATES[int(selected_index)]
            base_draws = generator.integers(
                0, base_ids_per_replicate, size=base_ids_per_replicate
            )
            for base_draw, base_id in enumerate(base_draws.tolist()):
                for original in by_replicate_base[(replicate, int(base_id))]:
                    row = dict(original)
                    row["bootstrap_replicate_draw"] = replicate_draw
                    row["bootstrap_base_draw"] = base_draw
                    sample.append(row)
        output.append(sample)
    return output


def validate_relative_reference(reference: object) -> str:
    if not isinstance(reference, str) or not reference:
        raise ValueError("artifact reference must be a nonempty string")
    if "\\" in reference or ":" in reference:
        raise ValueError("artifact references must be relative POSIX paths")
    path = PurePosixPath(reference)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError("artifact reference escapes the run directory")
    if str(path) != reference:
        raise ValueError("artifact reference is not canonical")
    return reference


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read exact JSON artifact {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"JSON artifact must contain an object: {path}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise ValueError(f"cannot read exact JSONL artifact {path}") from error
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        if not line:
            raise ValueError(f"blank JSONL row at {path}:{index + 1}")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"malformed JSONL row at {path}:{index + 1}") from error
        if not isinstance(row, dict):
            raise ValueError(f"JSONL row must be an object at {path}:{index + 1}")
        rows.append(row)
    return rows


def _exact_checkpoint_references() -> list[str]:
    return [
        f"checkpoints/replicate_{replicate}/{arm}/update_250.pt"
        for replicate in REPLICATES
        for arm in ARMS
    ]


def _exact_evaluation_references() -> list[str]:
    return [
        f"evaluation/replicate_{replicate}/{arm}/{profile}.jsonl"
        for replicate in REPLICATES
        for arm in ARMS
        for profile in EVALUATION_PROFILES
    ]


def _resolve_reference(run_dir: Path, reference: object) -> Path:
    canonical = validate_relative_reference(reference)
    candidate = run_dir.joinpath(*PurePosixPath(canonical).parts)
    if not candidate.is_file():
        raise ValueError(f"artifact reference does not close: {canonical}")
    return candidate


def validate_formal_result(run_dir: str | os.PathLike[str]) -> dict[str, Any]:
    """Fail closed unless one exact conclusion-bearing G1 inventory closes."""

    root = Path(run_dir)
    result = _read_json(root / "analysis_result.json")
    if result.get("formal") is not True:
        raise ValueError("formal result validation requires formal=true")
    expected_identity = {
        "schema": ANALYSIS_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "backend": "cpu",
        "torch_threads": 1,
        "authorization_token": FORMAL_AUTHORIZATION_TOKEN,
        "seed_registry": SEED_REGISTRY,
        "budget": FORMAL_BUDGET,
        "bootstrap_repetitions": BOOTSTRAP_REPETITIONS,
    }
    for key, expected in expected_identity.items():
        if result.get(key) != expected:
            raise ValueError(f"formal analysis {key} does not match the frozen contract")
    source_commit = result.get("source_commit")
    if not isinstance(source_commit, str) or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("formal analysis source_commit is not one exact Git identity")
    manifest = _read_json(root / "manifest.json")
    expected_manifest = _manifest(
        formal=True, source_commit=source_commit, budget=FORMAL_BUDGET
    )
    if manifest != expected_manifest:
        raise ValueError("formal manifest is not the exact canonical G1 manifest")
    result_name = result.get("result")
    valid_results = {
        "INVALID_OPERATIONAL_G1",
        "SOURCE_NON_IDENTIFIABLE_G1",
        "NO_ACCESS_THIS_G1_SOURCE",
        "UNDERPOWERED_ACCESS_G1",
        "COMMITMENT_SUPPORTED_G1",
        "REPRESENTATION_ONLY_G1",
        "ORDINARY_EXPLANATION_G1",
        "MIXED_UNDERPOWERED_G1",
    }
    if result_name not in valid_results:
        raise ValueError("formal analysis has an unknown G1 result")

    expected_checkpoints = _exact_checkpoint_references()
    if result.get("checkpoint_references") != expected_checkpoints:
        raise ValueError("formal checkpoint inventory is not the exact 5x3 final set")
    checkpoint_paths = [_resolve_reference(root, item) for item in expected_checkpoints]
    retained_checkpoints = sorted(root.rglob("*.pt"))
    if set(retained_checkpoints) != set(checkpoint_paths):
        raise ValueError("formal run retained an unregistered checkpoint")
    for reference, checkpoint_path in zip(expected_checkpoints, checkpoint_paths, strict=True):
        parts = PurePosixPath(reference).parts
        replicate = int(parts[1].removeprefix("replicate_"))
        arm = parts[2]
        payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
        expected_payload = {
            "schema": CHECKPOINT_SCHEMA,
            "source_family": SOURCE_FAMILY,
            "backend": "cpu",
            "torch_threads": 1,
            "arm": arm,
            "replicate": replicate,
            "update": 250,
            "seed_registry": SEED_REGISTRY,
            "base_optimizer_steps": 1_000,
            "event_optimizer_steps": 0 if arm == "OR" else 1_000,
        }
        if not isinstance(payload, dict) or any(payload.get(key) != value for key, value in expected_payload.items()):
            raise ValueError(f"formal checkpoint payload is malformed: {reference}")

    expected_evaluation = _exact_evaluation_references()
    if result.get("evaluation_references") != expected_evaluation:
        raise ValueError("formal evaluation inventory is not the exact 5x3x4 set")
    evaluation_root = root / "evaluation"
    actual_evaluation = {
        path.relative_to(root).as_posix()
        for path in evaluation_root.rglob("*.jsonl")
        if path.is_file()
    } if evaluation_root.is_dir() else set()
    if actual_evaluation != set(expected_evaluation):
        raise ValueError("formal evaluation directory contains missing or extra JSONL cells")
    episode_rows: list[dict[str, Any]] = []
    derived_operational_errors: list[str] = []
    for reference in expected_evaluation:
        rows = _read_jsonl(_resolve_reference(root, reference))
        parts = PurePosixPath(reference).parts
        expected_replicate = int(parts[1].removeprefix("replicate_"))
        expected_arm = parts[2]
        expected_profile = parts[3].removesuffix(".jsonl")
        if len(rows) != EVALUATION_EPISODES:
            raise ValueError(f"evaluation cell does not have 256 rows: {reference}")
        identity = {
            (row.get("base_id"), row.get("sign_mate")) for row in rows
        }
        expected_identity_rows = {
            (base_id, sign_mate)
            for base_id in range(EVALUATION_BASE_IDS)
            for sign_mate in (-1, 1)
        }
        if identity != expected_identity_rows:
            raise ValueError(f"evaluation cell identity inventory is malformed: {reference}")
        if any(row.get("schema") != EVALUATION_ROW_SCHEMA for row in rows):
            raise ValueError(f"evaluation cell row schema is malformed: {reference}")
        for row in rows:
            if (
                row.get("source_family") != SOURCE_FAMILY
                or row.get("source_commit") != source_commit
                or row.get("replicate") != expected_replicate
                or row.get("arm") != expected_arm
                or row.get("profile") != expected_profile
                or row.get("sign_mate") not in (-1, 1)
            ):
                raise ValueError(f"evaluation row identity does not match its path: {reference}")
            utility = _finite_number(row.get("utility"), "utility")
            reward_sum = _finite_number(row.get("reward_sum"), "reward_sum")
            if not (0.0 <= utility <= 1.0) or abs(utility - reward_sum) > 1e-9:
                raise ValueError(f"evaluation utility/reward identity fails: {reference}")
            if type(row.get("operational_valid")) is not bool:
                raise ValueError(f"evaluation operational_valid is not boolean: {reference}")
            if row["operational_valid"] is False:
                derived_operational_errors.append(
                    f"evaluation operational invariant failed: {reference}"
                )
            for count_name in (
                "roster_size", "temp_rejoin_span", "completed_segments",
                "censored_segments", "non_create_opportunities",
                "lifecycles_with_two_plus", "natural_keep", "natural_renew",
                "spell_k1", "spell_k2", "spell_k3_plus",
            ):
                count_value = row.get(count_name)
                if type(count_value) is not int or count_value < 0:
                    raise ValueError(f"evaluation count field is malformed: {reference}")
            if row.get("roster_size") not in (2, 3):
                raise ValueError(f"evaluation roster support is malformed: {reference}")
            durations = row.get("durations")
            if (
                not isinstance(durations, list)
                or not durations
                or any(type(value) is not int or value not in (6, 10, 14, 18) for value in durations)
                or durations != sorted(set(durations))
            ):
                raise ValueError(f"evaluation duration support is malformed: {reference}")
        episode_rows.extend(rows)

    if result.get("source_control_reference") != "source_controls.json":
        raise ValueError("formal source-control reference is not canonical")
    controls = _read_json(_resolve_reference(root, "source_controls.json"))
    _validate_source_controls(controls, formal=True, source_commit=source_commit)

    if result.get("audit_reference") != "causal_audit.jsonl":
        raise ValueError("formal audit reference is not canonical")
    audit_rows = _read_jsonl(_resolve_reference(root, "causal_audit.jsonl"))
    integer_domains = {
        "replicate": set(REPLICATES),
        "selection_index": set(range(16)),
        "base_id": set(range(EVALUATION_BASE_IDS)),
        "sign_mate": {-1, 1},
        "time": set(range(HORIZON)),
        "lifecycle": set(range(4)),
    }
    for row in audit_rows:
        if any(
            type(row.get(name)) is not int or row.get(name) not in domain
            for name, domain in integer_domains.items()
        ) or row.get("action") not in ("KEEP", "RENEW"):
            raise ValueError("formal causal-audit coordinate is malformed")
    audit_identity = {
        (row.get("replicate"), row.get("action"), row.get("selection_index"))
        for row in audit_rows
    }
    expected_audit_identity = {
        (replicate, action, selection_index)
        for replicate in REPLICATES
        for action in ("KEEP", "RENEW")
        for selection_index in range(16)
    }
    for replicate in REPLICATES:
        for action in ("KEEP", "RENEW"):
            indices = sorted(
                row.get("selection_index")
                for row in audit_rows
                if row.get("replicate") == replicate and row.get("action") == action
            )
            if indices != list(range(len(indices))) or len(indices) > 16:
                raise ValueError("causal audit is not a unique outcome-blind prefix")
    if any(row.get("schema") != AUDIT_ROW_SCHEMA for row in audit_rows):
        raise ValueError("formal causal-audit row schema is malformed")
    for row in audit_rows:
        if (
            row.get("source_family") != SOURCE_FAMILY
            or row.get("source_commit") != source_commit
            or row.get("profile") != "heldout_stochastic"
        ):
            raise ValueError("formal causal-audit row identity is malformed")
        action = row.get("action")
        expected_origin = "audit" if action == "KEEP" else "evaluation_mark"
        if (
            row.get("coordinate_stable_crn") is not True
            or row.get("candidate_mark_origin") != expected_origin
            or type(row.get("held_mark")) is not int
            or row.get("held_mark") not in (-1, 1)
            or type(row.get("candidate_mark")) is not int
            or row.get("candidate_mark") not in (-1, 1)
        ):
            raise ValueError("formal causal audit violates CRN or candidate-mark ownership")
        if action == "RENEW" and (
            row.get("natural_sampled_mark") not in (-1, 1)
            or row.get("candidate_mark") != row.get("natural_sampled_mark")
        ):
            raise ValueError("natural RENEW audit lost its evaluation-mark candidate")
        if action == "KEEP" and row.get("natural_sampled_mark") is not None:
            raise ValueError("natural KEEP audit must not report a sampled natural mark")
        i_tv = _finite_number(row.get("i_tv"), "i_tv")
        keep_utility = _finite_number(row.get("keep_terminal_utility"), "keep_terminal_utility")
        renew_utility = _finite_number(row.get("renew_terminal_utility"), "renew_terminal_utility")
        c_total = _finite_number(row.get("c_total"), "c_total")
        expected_c = keep_utility - renew_utility if action == "KEEP" else renew_utility - keep_utility
        if not 0.0 <= i_tv <= 1.0 or not 0.0 <= keep_utility <= 1.0 or not 0.0 <= renew_utility <= 1.0:
            raise ValueError("formal causal-audit metric is outside its domain")
        if abs(c_total - expected_c) > 1e-12:
            raise ValueError("formal causal-audit C_total formula is malformed")
    if len(audit_identity) != len(audit_rows):
        raise ValueError("formal causal-audit row identity is duplicated")
    coordinate_identity = {
        (row["replicate"], row["action"], row["base_id"], row["sign_mate"], row["time"], row["lifecycle"])
        for row in audit_rows
    }
    if len(coordinate_identity) != len(audit_rows):
        raise ValueError("formal causal-audit coordinate is duplicated")

    derived_metrics = _compact_analysis_statistics(
        episode_rows, audit_rows, formal=True
    )
    derived_source_identifiable = _source_identifiable(
        episode_rows, controls, formal=True
    )
    if derived_source_identifiable and audit_identity != expected_audit_identity:
        raise ValueError("identifiable formal audit does not contain the exact 160 selected rows")
    derived_predicates = _predicate_inputs_from_evidence(
        derived_metrics,
        operational_errors=derived_operational_errors,
        source_identifiable=derived_source_identifiable,
    )
    _require_analysis_binding(
        result,
        metrics=derived_metrics,
        predicate_inputs=derived_predicates,
        operational_errors=derived_operational_errors,
    )
    recomputed = select_result_branch(**derived_predicates)
    if recomputed != result_name:
        raise ValueError("formal result does not equal the evidence-derived first-match branch")
    return result


def _atomic_json(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    if temporary.exists():
        raise FileExistsError(f"temporary artifact already exists: {temporary}")
    try:
        temporary.write_text(
            json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n",
            encoding="utf-8",
        )
        _replace_with_permission_retry(temporary, path)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    if temporary.exists():
        raise FileExistsError(f"temporary artifact already exists: {temporary}")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(
                    json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False)
                    + "\n"
                )
        _replace_with_permission_retry(temporary, path)
    except BaseException:
        if temporary.exists():
            temporary.unlink()
        raise


def _require_formal_authorization(formal: bool, token: str | None) -> None:
    if type(formal) is not bool:
        raise ValueError("formal must be boolean")
    if formal and token != FORMAL_AUTHORIZATION_TOKEN:
        raise PermissionError("formal G1 training requires the exact authorization token")
    if not formal and token is not None:
        raise ValueError("nonformal work must not carry the formal authorization token")


def _require_source_commit(source_commit: object, *, formal: bool) -> str:
    if formal:
        if not isinstance(source_commit, str) or re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
            raise ValueError("formal work requires one lowercase 40-hex Git source commit")
        return source_commit
    if source_commit not in (None, "NONFORMAL_EXERCISE"):
        raise ValueError("nonformal exercise source identity must be NONFORMAL_EXERCISE")
    return "NONFORMAL_EXERCISE"


def _episode_specs(
    *,
    profile: str,
    replicate: int,
    base_ids: Iterable[int],
    evaluation: bool,
) -> list[Any]:
    offset = SEED_REGISTRY["replicate_offset"] * replicate
    prefix = "evaluation" if evaluation else "train"
    return [
        make_episode_spec(
            profile,
            task_seed=SEED_REGISTRY[f"{prefix}_task"] + offset,
            membership_seed=SEED_REGISTRY[f"{prefix}_membership"] + offset,
            duty_seed=SEED_REGISTRY[f"{prefix}_duty"] + offset,
            opportunity_seed=SEED_REGISTRY[f"{prefix}_opportunity"] + offset,
            base_id=base_id,
            sign_mate=sign_mate,
        )
        for base_id in base_ids
        for sign_mate in (-1, 1)
    ]


def _manifest(
    *, formal: bool, source_commit: str, budget: Mapping[str, object]
) -> dict[str, object]:
    return {
        "schema": MANIFEST_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "formal": formal,
        "backend": "cpu",
        "torch_threads": 1,
        "source_commit": source_commit,
        "authorization_token": FORMAL_AUTHORIZATION_TOKEN if formal else None,
        "arms": list(ARMS),
        "replicates": list(REPLICATES if formal else (0,)),
        "evaluation_profiles": list(EVALUATION_PROFILES),
        "seed_registry": SEED_REGISTRY,
        "budget": dict(budget),
    }


def _load_or_create_manifest(
    run_dir: Path,
    *,
    formal: bool,
    source_commit: str,
    budget: Mapping[str, object],
) -> dict[str, Any]:
    expected = _manifest(formal=formal, source_commit=source_commit, budget=budget)
    path = run_dir / "manifest.json"
    if path.exists():
        actual = _read_json(path)
        if actual != expected:
            raise ValueError("existing manifest does not match the exact requested G1 run")
        return actual
    _atomic_json(path, expected)
    return expected


def _verify_completed_training_state(state: Any, *, updates: int) -> None:
    if state.update != updates:
        raise ValueError("checkpoint update does not match the registered budget")
    expected_steps = updates * FORMAL_BUDGET["ppo_passes"]
    if state.base_optimizer_steps != expected_steps:
        raise ValueError("checkpoint base optimizer exposure is malformed")
    expected_event = 0 if state.arm == "OR" else expected_steps
    if state.event_optimizer_steps != expected_event:
        raise ValueError("checkpoint event optimizer exposure is malformed")


def train(
    *,
    run_dir: Path,
    formal: bool,
    authorization_token: str | None,
    source_commit: str | None,
    updates_override: int | None = None,
) -> None:
    """Train independent paired arms with one rolling recovery checkpoint."""

    _require_formal_authorization(formal, authorization_token)
    configure_cpu_runtime()
    source_identity = _require_source_commit(source_commit, formal=formal)
    if formal:
        if updates_override is not None:
            raise ValueError("formal training does not accept budget overrides")
        replicates = REPLICATES
        updates = int(FORMAL_BUDGET["updates"])
        budget = FORMAL_BUDGET
    else:
        if type(updates_override) is not int or updates_override != 1:
            raise ValueError("the bounded exercise uses exactly one update")
        replicates = (0,)
        updates = 1
        budget = {
            **FORMAL_BUDGET,
            "environments": 4,
            "updates": 1,
            "episodes_per_arm": 4,
            "transitions_per_arm": 4 * HORIZON,
            "base_optimizer_steps": 4,
            "event_optimizer_steps": {"OR": 0, "DUM": 4, "EHC": 4},
            "evaluation_episodes_per_cell": 4,
            "bootstrap_repetitions": 8,
        }
    run_dir.mkdir(parents=True, exist_ok=True)
    _load_or_create_manifest(
        run_dir, formal=formal, source_commit=source_identity, budget=budget
    )
    progress_path = run_dir / "progress.json"
    for replicate in replicates:
        for arm in ARMS:
            arm_dir = run_dir / "checkpoints" / f"replicate_{replicate}" / arm
            final_path = arm_dir / f"update_{updates}.pt"
            latest_path = arm_dir / "latest.pt"
            if final_path.is_file():
                state = load_checkpoint(
                    final_path,
                    arm=arm,
                    replicate=replicate,
                    backend="cpu",
                    torch_threads=1,
                )
                _verify_completed_training_state(state, updates=updates)
                if latest_path.exists():
                    latest_path.unlink()
                continue
            if latest_path.is_file():
                state = load_checkpoint(
                    latest_path,
                    arm=arm,
                    replicate=replicate,
                    backend="cpu",
                    torch_threads=1,
                )
            else:
                state = initialize_matched_arms(
                    replicate, backend="cpu", torch_threads=1
                )[arm]
            if state.update > updates:
                raise ValueError("rolling checkpoint exceeds the requested budget")
            while state.update < updates:
                update_index = state.update
                if formal:
                    base_ids = range(8 * update_index, 8 * update_index + 8)
                else:
                    base_ids = range(2)
                specs = _episode_specs(
                    profile="train",
                    replicate=replicate,
                    base_ids=base_ids,
                    evaluation=False,
                )
                batch = collect_rollout(state, specs, deterministic=False)
                metrics = optimize_rollout(state, batch)
                save_checkpoint(latest_path, state)
                _atomic_json(
                    progress_path,
                    {
                        "schema": RUNNER_SCHEMA,
                        "formal": formal,
                        "replicate": replicate,
                        "arm": arm,
                        "update": state.update,
                        "base_optimizer_steps": metrics["base_optimizer_steps"],
                        "event_optimizer_steps": metrics["event_optimizer_steps"],
                    },
                )
            _verify_completed_training_state(state, updates=updates)
            save_checkpoint(final_path, state)
            if latest_path.exists():
                latest_path.unlink()
    _atomic_json(
        progress_path,
        {
            "schema": RUNNER_SCHEMA,
            "formal": formal,
            "status": "TRAIN_COMPLETE",
            "replicates": list(replicates),
            "arms": list(ARMS),
            "updates": updates,
        },
    )


def _coordinate_samples(
    logits: torch.Tensor,
    *,
    deterministic: bool,
    namespace_seed: int,
    coordinates: Sequence[tuple[int, int, int, int, int, int]],
) -> torch.Tensor:
    if logits.ndim != 2 or logits.shape[0] != len(coordinates):
        raise ValueError("coordinate sample logits/coordinates are misaligned")
    if deterministic:
        return logits.argmax(dim=-1)
    uniforms = [
        float(
            np.random.Generator(
                np.random.Philox(
                    np.random.SeedSequence([namespace_seed, *coordinate])
                )
            ).random()
        )
        for coordinate in coordinates
    ]
    cumulative = torch.softmax(logits, dim=-1).cumsum(dim=-1)
    draws = torch.tensor(uniforms, dtype=cumulative.dtype).unsqueeze(-1)
    return (draws > cumulative).sum(dim=-1).clamp_max(logits.shape[-1] - 1)


def _profile_parts(profile: str) -> tuple[str, bool, int]:
    try:
        profile_index = EVALUATION_PROFILES.index(profile)
    except ValueError as error:
        raise ValueError("unknown evaluation profile") from error
    source_profile = "heldout" if profile.startswith("heldout") else "iid"
    return source_profile, profile in DETERMINISTIC_PROFILES, profile_index


def _evaluation_coordinate(
    replicate: int,
    profile_index: int,
    spec: Any,
    time: int,
    slot: int,
    draw_kind: int,
) -> tuple[int, int, int, int, int, int]:
    return (
        replicate,
        profile_index,
        int(spec.base_id),
        0 if int(spec.sign_mate) == -1 else 1,
        time * 16 + slot,
        draw_kind,
    )


def _trim_contexts(
    contexts: list[dict[str, Any]], candidate: dict[str, Any]
) -> None:
    contexts.append(candidate)
    contexts.sort(
        key=lambda item: (
            item["base_id"],
            item["sign_mate"],
            item["time"],
            item["lifecycle"],
        )
    )
    del contexts[16:]


def _evaluate_policy_cell(
    state: Any,
    *,
    profile: str,
    base_ids: range,
    collect_audit_contexts: bool,
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    source_profile, deterministic, profile_index = _profile_parts(profile)
    specs = _episode_specs(
        profile=source_profile,
        replicate=state.replicate,
        base_ids=base_ids,
        evaluation=True,
    )
    environments = [TemporalDutyG1Env(spec) for spec in specs]
    count = len(environments)
    capacity = 4
    hidden = torch.zeros(count, capacity, HIDDEN_WIDTH)
    held_marks = torch.zeros(count, capacity, dtype=torch.long)
    has_mark = torch.zeros(count, capacity, dtype=torch.bool)
    pending_reset = torch.zeros(count, capacity, dtype=torch.bool)
    natural_keep = np.zeros(count, dtype=np.int64)
    natural_renew = np.zeros(count, dtype=np.int64)
    non_create = np.zeros(count, dtype=np.int64)
    event_by_lifecycle = np.zeros((count, capacity), dtype=np.int64)
    spell_open_counts = np.zeros((count, capacity), dtype=np.int64)
    spell_bins = np.zeros((count, 3), dtype=np.int64)
    contexts: dict[str, list[dict[str, Any]]] = {"KEEP": [], "RENEW": []}
    offset = SEED_REGISTRY["replicate_offset"] * state.replicate
    event_seed = SEED_REGISTRY["evaluation_event"] + offset
    mark_seed = SEED_REGISTRY["evaluation_mark"] + offset
    primitive_seed = SEED_REGISTRY["evaluation_primitive"] + offset

    state.model.eval()
    with torch.no_grad():
        for time in range(HORIZON):
            observations = [environment.observe() for environment in environments]
            actor = torch.zeros(count, capacity, 6)
            critic = torch.zeros(count, capacity, 10)
            active = torch.zeros(count, capacity, dtype=torch.bool)
            opportunity = torch.zeros(count, capacity, dtype=torch.long)
            for env_index, episode_observations in enumerate(observations):
                for slot, observation in episode_observations.items():
                    actor[env_index, slot] = torch.tensor(observation.actor)
                    critic[env_index, slot] = torch.tensor(observation.critic)
                    active[env_index, slot] = True
                    pending_reset[env_index, slot] |= observation.actor[3] == 1.0
                    if state.arm != "OR":
                        opportunity[env_index, slot] = (
                            1 if observation.opportunity_kind == "CREATE" else
                            2 if observation.opportunity_kind == "EVENT" else 0
                        )
            hidden = torch.where(
                pending_reset.unsqueeze(-1), torch.zeros_like(hidden), hidden
            )
            pending_reset.zero_()
            features_flat, _ = state.model.actor_step(
                actor.reshape(-1, 6), hidden.reshape(-1, HIDDEN_WIDTH)
            )
            features = features_flat.reshape(count, capacity, HIDDEN_WIDTH)
            hidden = torch.where(active.unsqueeze(-1), features, hidden)
            event_logits, mark_logits = state.model.event_mark_logits(features)
            held_before = held_marks.clone()
            has_before = has_mark.clone()

            create_mask = opportunity == 1
            if create_mask.any():
                create_coordinates = create_mask.nonzero(as_tuple=False).tolist()
                selected = _coordinate_samples(
                    mark_logits[create_mask],
                    deterministic=deterministic,
                    namespace_seed=mark_seed,
                    coordinates=[
                        _evaluation_coordinate(
                            state.replicate, profile_index, specs[e], time, s, 1
                        )
                        for e, s in create_coordinates
                    ],
                )
                held_marks[create_mask] = 2 * selected - 1
                has_mark[create_mask] = True

            event_mask = opportunity == 2
            selected_events = torch.empty(0, dtype=torch.long)
            selected_event_by_coordinate: dict[tuple[int, int], int] = {}
            selected_mark_by_coordinate: dict[tuple[int, int], int] = {}
            if event_mask.any():
                if torch.any(~has_mark[event_mask]):
                    raise RuntimeError("evaluation EVENT occurred without a held mark")
                event_coordinates = event_mask.nonzero(as_tuple=False).tolist()
                selected_events = _coordinate_samples(
                    event_logits[event_mask],
                    deterministic=deterministic,
                    namespace_seed=event_seed,
                    coordinates=[
                        _evaluation_coordinate(
                            state.replicate, profile_index, specs[e], time, s, 2
                        )
                        for e, s in event_coordinates
                    ],
                )
                renew_mask = event_mask.clone()
                renew_mask[event_mask] = selected_events == 1
                if renew_mask.any():
                    renew_coordinates = renew_mask.nonzero(as_tuple=False).tolist()
                    selected_marks = _coordinate_samples(
                        mark_logits[renew_mask],
                        deterministic=deterministic,
                        namespace_seed=mark_seed,
                        coordinates=[
                            _evaluation_coordinate(
                                state.replicate, profile_index, specs[e], time, s, 3
                            )
                            for e, s in renew_coordinates
                        ],
                    )
                    held_marks[renew_mask] = 2 * selected_marks - 1
                    selected_mark_by_coordinate = {
                        (e, s): int(2 * selected_marks[index].item() - 1)
                        for index, (e, s) in enumerate(renew_coordinates)
                    }
                selected_event_by_coordinate = {
                    (e, s): int(selected_events[index].item())
                    for index, (e, s) in enumerate(event_coordinates)
                }
                for env_index, slot in event_coordinates:
                    event_index = selected_event_by_coordinate[(env_index, slot)]
                    action = "KEEP" if event_index == 0 else "RENEW"
                    non_create[env_index] += 1
                    event_by_lifecycle[env_index, slot] += 1
                    spell_open_counts[env_index, slot] += 1
                    if action == "KEEP":
                        natural_keep[env_index] += 1
                    else:
                        natural_renew[env_index] += 1
                        k_value = int(spell_open_counts[env_index, slot])
                        spell_bins[env_index, min(k_value, 3) - 1] += 1
                        spell_open_counts[env_index, slot] = 0

                    if collect_audit_contexts:
                        natural_mark = int(held_marks[env_index, slot])
                        natural_logits = state.model.primitive_head(
                            features[env_index, slot]
                        ) + natural_mark * state.model.mark_treatment
                        deranged_logits = state.model.primitive_head(
                            features[env_index, slot]
                        ) - natural_mark * state.model.mark_treatment
                        i_tv = 0.5 * float(
                            (
                                torch.softmax(natural_logits, dim=-1)
                                - torch.softmax(deranged_logits, dim=-1)
                            ).abs().sum().item()
                        )
                        candidate = {
                            "replicate": state.replicate,
                            "profile": profile,
                            "base_id": int(specs[env_index].base_id),
                            "sign_mate": int(specs[env_index].sign_mate),
                            "time": time,
                            "lifecycle": next(
                                ledger.logical_lifecycle
                                for ledger in specs[env_index].lifecycle_ledgers
                                if ledger.physical_slot == slot
                            ),
                            "physical_slot": slot,
                            "action": action,
                            "held_mark_before": int(held_before[env_index, slot]),
                            "natural_mark": natural_mark,
                            "natural_sampled_mark": selected_mark_by_coordinate.get(
                                (env_index, slot)
                            ),
                            "i_tv": i_tv,
                        }
                        current = contexts[action]
                        key = (
                            candidate["base_id"], candidate["sign_mate"],
                            candidate["time"], candidate["lifecycle"],
                        )
                        if len(current) < 16 or key < (
                            current[-1]["base_id"], current[-1]["sign_mate"],
                            current[-1]["time"], current[-1]["lifecycle"],
                        ):
                            candidate.update(
                                environment=environments[env_index].snapshot_state(),
                                hidden_after_actor=hidden[env_index].clone(),
                                held_marks_before=held_before[env_index].clone(),
                                has_mark_before=has_before[env_index].clone(),
                            )
                            _trim_contexts(current, candidate)

            primitive_logits = state.model.primitive_head(features)
            if state.arm == "EHC":
                primitive_logits = primitive_logits + (
                    held_marks.to(primitive_logits.dtype).unsqueeze(-1)
                    * state.model.mark_treatment
                )
            active_coordinates = active.nonzero(as_tuple=False).tolist()
            selected_actions = _coordinate_samples(
                primitive_logits[active],
                deterministic=deterministic,
                namespace_seed=primitive_seed,
                coordinates=[
                    _evaluation_coordinate(
                        state.replicate, profile_index, specs[e], time, s, 4
                    )
                    for e, s in active_coordinates
                ],
            )
            action_values = torch.tensor((-1, 0, 1), dtype=torch.long)[
                selected_actions
            ].tolist()
            for index, (env_index, slot) in enumerate(active_coordinates):
                # Pack below per environment without a device scalar extraction.
                _ = index, env_index, slot
            cursor = 0
            for env_index, environment in enumerate(environments):
                slots = active[env_index].nonzero(as_tuple=False).squeeze(-1).tolist()
                count_active = len(slots)
                transition = environment.step(
                    dict(
                        zip(
                            slots,
                            action_values[cursor : cursor + count_active],
                            strict=True,
                        )
                    )
                )
                cursor += count_active
                for segment_event in transition["segment_events"]:
                    slot = int(segment_event["slot"])
                    if segment_event["status"] == "COMPLETED":
                        hidden[env_index, slot].zero_()
                        pending_reset[env_index, slot] = True
                    elif segment_event["status"] == "CENSORED_TERMINAL":
                        hidden[env_index, slot].zero_()
                        held_marks[env_index, slot] = 0
                        has_mark[env_index, slot] = False
                        spell_open_counts[env_index, slot] = 0
            if cursor != len(action_values):
                raise RuntimeError("evaluation primitive action packing lost a row")

    rows: list[dict[str, Any]] = []
    for env_index, (environment, spec) in enumerate(zip(environments, specs, strict=True)):
        outcome = environment.outcome()
        durations = sorted(
            {
                int(segment["duration"])
                for segment in environment.snapshot_state()["segment_records"]
            }
        )
        temp_leave = next(t for t, name, _ in spec.membership_events if name == "TEMP_LEAVE")
        rejoin = next(t for t, name, _ in spec.membership_events if name == "REJOIN")
        rows.append(
            {
                "schema": EVALUATION_ROW_SCHEMA,
                "source_family": SOURCE_FAMILY,
                "replicate": state.replicate,
                "arm": state.arm,
                "profile": profile,
                "base_id": int(spec.base_id),
                "sign_mate": int(spec.sign_mate),
                "utility": float(outcome["utility"]),
                "reward_sum": float(outcome["reward_sum"]),
                "roster_size": int(spec.roster_size),
                "durations": durations,
                "temp_rejoin_span": int(rejoin - temp_leave),
                "completed_segments": int(outcome["completed_segments"]),
                "censored_segments": int(
                    outcome["eligible_segments"] - outcome["completed_segments"]
                ),
                "non_create_opportunities": int(non_create[env_index]),
                "lifecycles_with_two_plus": int(
                    (event_by_lifecycle[env_index] >= 2).sum()
                ),
                "natural_keep": int(natural_keep[env_index]),
                "natural_renew": int(natural_renew[env_index]),
                "spell_k1": int(spell_bins[env_index, 0]),
                "spell_k2": int(spell_bins[env_index, 1]),
                "spell_k3_plus": int(spell_bins[env_index, 2]),
                "operational_valid": bool(
                    math.isfinite(float(outcome["utility"]))
                    and abs(float(outcome["utility"]) - float(outcome["reward_sum"])) <= 1e-9
                ),
            }
        )
    return rows, contexts


def _single_policy_continuation(
    state: Any,
    context: Mapping[str, Any],
    *,
    forced_event: str,
) -> tuple[float, int, str]:
    if forced_event not in ("KEEP", "RENEW"):
        raise ValueError("forced_event must be KEEP or RENEW")
    environment = TemporalDutyG1Env.from_snapshot_state(dict(context["environment"]))
    spec = environment.spec
    _, deterministic, profile_index = _profile_parts(str(context["profile"]))
    hidden = context["hidden_after_actor"].clone()
    held_marks = context["held_marks_before"].clone()
    has_mark = context["has_mark_before"].clone()
    target_slot = int(context["physical_slot"])
    start_time = int(context["time"])
    pending_reset = torch.zeros(4, dtype=torch.bool)
    offset = SEED_REGISTRY["replicate_offset"] * state.replicate
    event_seed = SEED_REGISTRY["evaluation_event"] + offset
    mark_seed = SEED_REGISTRY["evaluation_mark"] + offset
    primitive_seed = SEED_REGISTRY["evaluation_primitive"] + offset
    audit_seed = SEED_REGISTRY["audit"] + offset
    candidate_mark = 0
    candidate_origin = "none"

    state.model.eval()
    with torch.no_grad():
        for time in range(start_time, HORIZON):
            observations = environment.observe()
            active_slots = sorted(observations)
            actor = torch.zeros(4, 6)
            active = torch.zeros(4, dtype=torch.bool)
            opportunity = torch.zeros(4, dtype=torch.long)
            for slot, observation in observations.items():
                actor[slot] = torch.tensor(observation.actor)
                active[slot] = True
                if observation.actor[3] == 1.0:
                    pending_reset[slot] = True
                opportunity[slot] = (
                    1 if observation.opportunity_kind == "CREATE" else
                    2 if observation.opportunity_kind == "EVENT" else 0
                )
            if time != start_time:
                hidden = torch.where(
                    pending_reset.unsqueeze(-1), torch.zeros_like(hidden), hidden
                )
                pending_reset.zero_()
                candidate, _ = state.model.actor_step(actor, hidden)
                hidden = torch.where(active.unsqueeze(-1), candidate, hidden)
            features = hidden
            event_logits, mark_logits = state.model.event_mark_logits(features)
            create_slots = opportunity.eq(1).nonzero(as_tuple=False).squeeze(-1).tolist()
            if create_slots:
                selected = _coordinate_samples(
                    mark_logits[create_slots],
                    deterministic=deterministic,
                    namespace_seed=mark_seed,
                    coordinates=[
                        _evaluation_coordinate(
                            state.replicate, profile_index, spec, time, slot, 1
                        )
                        for slot in create_slots
                    ],
                )
                for index, slot in enumerate(create_slots):
                    held_marks[slot] = 2 * selected[index] - 1
                    has_mark[slot] = True

            event_slots = opportunity.eq(2).nonzero(as_tuple=False).squeeze(-1).tolist()
            if any(not bool(has_mark[slot]) for slot in event_slots):
                raise RuntimeError("audit continuation EVENT occurred without a held mark")
            if event_slots:
                selected_events = _coordinate_samples(
                    event_logits[event_slots],
                    deterministic=deterministic,
                    namespace_seed=event_seed,
                    coordinates=[
                        _evaluation_coordinate(
                            state.replicate, profile_index, spec, time, slot, 2
                        )
                        for slot in event_slots
                    ],
                )
                for index, slot in enumerate(event_slots):
                    event_index = int(selected_events[index])
                    if time == start_time and slot == target_slot:
                        event_index = 0 if forced_event == "KEEP" else 1
                    if event_index == 1:
                        if time == start_time and slot == target_slot and forced_event == "RENEW":
                            if context["action"] == "RENEW":
                                if context.get("natural_sampled_mark") not in (-1, 1):
                                    raise ValueError("natural RENEW audit row lost its selected mark")
                                chosen = int(context["natural_sampled_mark"])
                                candidate_origin = "evaluation_mark"
                            else:
                                audit_selected = _coordinate_samples(
                                    mark_logits[slot].unsqueeze(0),
                                    deterministic=False,
                                    namespace_seed=audit_seed,
                                    coordinates=[
                                        _evaluation_coordinate(
                                            state.replicate,
                                            profile_index,
                                            spec,
                                            time,
                                            slot,
                                            5,
                                        )
                                    ],
                                )
                                chosen = int(2 * audit_selected.item() - 1)
                                candidate_origin = "audit"
                            candidate_mark = chosen
                        else:
                            selected_mark = _coordinate_samples(
                                mark_logits[slot].unsqueeze(0),
                                deterministic=deterministic,
                                namespace_seed=mark_seed,
                                coordinates=[
                                    _evaluation_coordinate(
                                        state.replicate,
                                        profile_index,
                                        spec,
                                        time,
                                        slot,
                                        3,
                                    )
                                ],
                            )
                            chosen = int(2 * selected_mark.item() - 1)
                        held_marks[slot] = chosen

            primitive_logits = state.model.primitive_head(features)
            primitive_logits = primitive_logits + (
                held_marks.to(primitive_logits.dtype).unsqueeze(-1)
                * state.model.mark_treatment
            )
            selected_actions = _coordinate_samples(
                primitive_logits[active],
                deterministic=deterministic,
                namespace_seed=primitive_seed,
                coordinates=[
                    _evaluation_coordinate(
                        state.replicate, profile_index, spec, time, slot, 4
                    )
                    for slot in active_slots
                ],
            )
            action_values = [(-1, 0, 1)[index] for index in selected_actions.tolist()]
            transition = environment.step(dict(zip(active_slots, action_values, strict=True)))
            for segment_event in transition["segment_events"]:
                slot = int(segment_event["slot"])
                if segment_event["status"] == "COMPLETED":
                    hidden[slot].zero_()
                    pending_reset[slot] = True
                elif segment_event["status"] == "CENSORED_TERMINAL":
                    hidden[slot].zero_()
                    held_marks[slot] = 0
                    has_mark[slot] = False
                    pending_reset[slot] = False
    utility = float(environment.outcome()["utility"])
    if not math.isfinite(utility):
        raise FloatingPointError("audit continuation produced non-finite utility")
    return utility, candidate_mark, candidate_origin


def _build_causal_audit(
    run_dir: Path,
    contexts: Sequence[Mapping[str, Any]],
    *,
    formal: bool,
) -> list[dict[str, Any]]:
    expected_replicates = REPLICATES if formal else (0,)
    expected_per_action = 16 if formal else 1
    by_identity: dict[tuple[int, str], list[Mapping[str, Any]]] = {}
    for context in contexts:
        by_identity.setdefault(
            (int(context["replicate"]), str(context["action"])), []
        ).append(context)
    rows: list[dict[str, Any]] = []
    updates = 250 if formal else 1
    for replicate in expected_replicates:
        checkpoint = run_dir / "checkpoints" / f"replicate_{replicate}" / "EHC" / f"update_{updates}.pt"
        state = load_checkpoint(
            checkpoint,
            arm="EHC",
            replicate=replicate,
            backend="cpu",
            torch_threads=1,
        )
        for action in ("KEEP", "RENEW"):
            selected = sorted(
                by_identity.get((replicate, action), ()),
                key=lambda item: (
                    item["base_id"], item["sign_mate"], item["time"], item["lifecycle"]
                ),
            )[:expected_per_action]
            if len(selected) != expected_per_action:
                if not selected:
                    continue
            for selection_index, context in enumerate(selected):
                keep_utility, _, _ = _single_policy_continuation(
                    state, context, forced_event="KEEP"
                )
                renew_utility, candidate_mark, candidate_origin = _single_policy_continuation(
                    state, context, forced_event="RENEW"
                )
                c_total = (
                    keep_utility - renew_utility
                    if action == "KEEP"
                    else renew_utility - keep_utility
                )
                rows.append(
                    {
                        "schema": AUDIT_ROW_SCHEMA,
                        "source_family": SOURCE_FAMILY,
                        "replicate": replicate,
                        "profile": "heldout_stochastic",
                        "action": action,
                        "selection_index": selection_index,
                        "base_id": int(context["base_id"]),
                        "sign_mate": int(context["sign_mate"]),
                        "time": int(context["time"]),
                        "lifecycle": int(context["lifecycle"]),
                        "held_mark": int(context["held_mark_before"]),
                        "natural_sampled_mark": context.get("natural_sampled_mark"),
                        "candidate_mark": candidate_mark,
                        "candidate_mark_origin": candidate_origin,
                        "i_tv": float(context["i_tv"]),
                        "keep_terminal_utility": keep_utility,
                        "renew_terminal_utility": renew_utility,
                        "c_total": c_total,
                        "coordinate_stable_crn": True,
                    }
                )
    return rows


def _control_episode_utilities(
    *,
    source_profile: str,
    replicate: int,
    base_ids: range,
    controller: str,
) -> np.ndarray:
    specs = _episode_specs(
        profile=source_profile,
        replicate=replicate,
        base_ids=base_ids,
        evaluation=True,
    )
    environments = [TemporalDutyG1Env(spec) for spec in specs]
    history_seed = SEED_REGISTRY["evaluation_primitive"] + SEED_REGISTRY["replicate_offset"] * replicate
    for _ in range(HORIZON):
        for environment in environments:
            actions = (
                environment.oracle_actions()
                if controller == "oracle"
                else environment.history_free_actions(seed=history_seed)
            )
            environment.step(actions)
    return np.asarray(
        [environment.outcome()["utility"] for environment in environments],
        dtype=np.float64,
    ).reshape(len(base_ids), 2)


def _compact_mean_interval(values: np.ndarray, *, repetitions: int, seed: int) -> tuple[float, float, float]:
    if values.ndim != 3 or values.shape[2] != 2:
        raise ValueError("compact interval values must be [replicate,base,sign]")
    generator = np.random.Generator(np.random.Philox(seed))
    estimates = np.empty(repetitions, dtype=np.float64)
    replicate_count, base_count, _ = values.shape
    for start in range(0, repetitions, 256):
        stop = min(start + 256, repetitions)
        size = stop - start
        replicate_draw = generator.integers(0, replicate_count, (size, replicate_count))
        base_draw = generator.integers(0, base_count, (size, replicate_count, base_count))
        selected = values[
            replicate_draw[:, :, None],
            base_draw,
            :,
        ]
        estimates[start:stop] = selected.mean(axis=(1, 2, 3))
    lower, upper = np.percentile(estimates, (2.5, 97.5))
    return float(values.mean()), float(lower), float(upper)


def _source_control_summary(
    values: np.ndarray,
    *,
    repetitions: int,
    seed: int,
) -> dict[str, Any]:
    mean, lower, upper = _compact_mean_interval(
        values, repetitions=repetitions, seed=seed
    )
    return {
        "mean": mean,
        "lcb95": lower,
        "ucb95": upper,
        "utilities": values.tolist(),
    }


def _build_source_controls(*, formal: bool) -> dict[str, Any]:
    replicates = REPLICATES if formal else (0,)
    base_ids = range(EVALUATION_BASE_IDS if formal else 2)
    repetitions = BOOTSTRAP_REPETITIONS if formal else 8
    rows: list[dict[str, Any]] = []
    cache: dict[tuple[str, str], np.ndarray] = {}
    for profile_index, profile in enumerate(EVALUATION_PROFILES):
        source_profile, _, _ = _profile_parts(profile)
        for controller_index, controller in enumerate(("oracle", "history_free")):
            key = (source_profile, controller)
            if key not in cache:
                cache[key] = np.stack(
                    [
                        _control_episode_utilities(
                            source_profile=source_profile,
                            replicate=replicate,
                            base_ids=base_ids,
                            controller=controller,
                        )
                        for replicate in replicates
                    ],
                    axis=0,
                )
            summary = _source_control_summary(
                cache[key],
                repetitions=repetitions,
                seed=SEED_REGISTRY["bootstrap"] + profile_index * 10 + controller_index,
            )
            rows.append(
                {
                    "profile": profile,
                    "controller": controller,
                    **summary,
                }
            )
    return {
        "schema": SOURCE_CONTROL_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "formal": formal,
        "profiles": list(EVALUATION_PROFILES),
        "replicates": list(replicates),
        "base_ids": list(base_ids),
        "sign_mates": [-1, 1],
        "bootstrap_repetitions": repetitions,
        "rows": rows,
    }


def _validate_source_controls(
    controls: Mapping[str, Any],
    *,
    formal: bool,
    source_commit: str,
) -> list[dict[str, Any]]:
    replicates = REPLICATES if formal else (0,)
    base_count = EVALUATION_BASE_IDS if formal else 2
    repetitions = BOOTSTRAP_REPETITIONS if formal else 8
    expected_keys = {
        "schema", "source_family", "formal", "source_commit", "profiles",
        "replicates", "base_ids", "sign_mates", "bootstrap_repetitions", "rows",
    }
    if set(controls) != expected_keys:
        raise ValueError("source-control top-level schema is not exact")
    expected_identity = {
        "schema": SOURCE_CONTROL_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "formal": formal,
        "source_commit": source_commit,
        "profiles": list(EVALUATION_PROFILES),
        "replicates": list(replicates),
        "base_ids": list(range(base_count)),
        "sign_mates": [-1, 1],
        "bootstrap_repetitions": repetitions,
    }
    for key, value in expected_identity.items():
        if controls.get(key) != value:
            raise ValueError(f"source-control {key} identity is malformed")
    rows = controls.get("rows")
    if not isinstance(rows, list) or len(rows) != 8 or any(not isinstance(row, dict) for row in rows):
        raise ValueError("source-control row inventory is malformed")
    identities = [(row.get("profile"), row.get("controller")) for row in rows]
    expected_identities = [
        (profile, controller)
        for profile in EVALUATION_PROFILES
        for controller in ("oracle", "history_free")
    ]
    if identities != expected_identities:
        raise ValueError("source-control row identities or order are malformed")
    for profile_index, profile in enumerate(EVALUATION_PROFILES):
        for controller_index, controller in enumerate(("oracle", "history_free")):
            row = rows[profile_index * 2 + controller_index]
            if set(row) != {"profile", "controller", "mean", "lcb95", "ucb95", "utilities"}:
                raise ValueError("source-control cluster row schema is not exact")
            utilities = row.get("utilities")
            if not isinstance(utilities, list):
                raise ValueError("source-control utilities must be a nested list")
            try:
                values = np.asarray(utilities, dtype=np.float64)
            except (TypeError, ValueError) as error:
                raise ValueError("source-control utilities are not a rectangular numeric tensor") from error
            if values.shape != (len(replicates), base_count, 2):
                raise ValueError("source-control utilities must have [replicate,base,sign] shape")
            if not np.isfinite(values).all() or np.any(values < 0.0) or np.any(values > 1.0):
                raise ValueError("source-control utility is non-finite or outside [0,1]")
            if any(
                type(value) not in (int, float)
                for replicate_values in utilities
                for base_values in replicate_values
                for value in base_values
            ):
                raise ValueError("source-control utility must be a non-boolean JSON number")
            expected_summary = _source_control_summary(
                values,
                repetitions=repetitions,
                seed=SEED_REGISTRY["bootstrap"] + profile_index * 10 + controller_index,
            )
            for key in ("mean", "lcb95", "ucb95"):
                if row.get(key) != expected_summary[key]:
                    raise ValueError(f"source-control {key} is not derived from its clusters")
    return rows


def evaluate(*, run_dir: Path, formal: bool) -> None:
    configure_cpu_runtime()
    manifest = _read_json(run_dir / "manifest.json")
    if manifest.get("formal") is not formal:
        raise ValueError("evaluate formal flag does not match the run manifest")
    replicates = REPLICATES if formal else (0,)
    base_ids = range(EVALUATION_BASE_IDS if formal else 2)
    updates = 250 if formal else 1
    all_contexts: list[dict[str, Any]] = []
    for replicate in replicates:
        for arm in ARMS:
            checkpoint = run_dir / "checkpoints" / f"replicate_{replicate}" / arm / f"update_{updates}.pt"
            state = load_checkpoint(
                checkpoint,
                arm=arm,
                replicate=replicate,
                backend="cpu",
                torch_threads=1,
            )
            _verify_completed_training_state(state, updates=updates)
            for profile in EVALUATION_PROFILES:
                rows, contexts = _evaluate_policy_cell(
                    state,
                    profile=profile,
                    base_ids=base_ids,
                    collect_audit_contexts=(
                        arm == "EHC" and profile == "heldout_stochastic"
                    ),
                )
                for row in rows:
                    row["source_commit"] = manifest["source_commit"]
                reference = (
                    run_dir / "evaluation" / f"replicate_{replicate}" / arm / f"{profile}.jsonl"
                )
                _write_jsonl(reference, rows)
                if arm == "EHC" and profile == "heldout_stochastic":
                    all_contexts.extend(contexts["KEEP"])
                    all_contexts.extend(contexts["RENEW"])
    # Branch continuations and source controls are completed by the helpers below.
    audit_rows = _build_causal_audit(run_dir, all_contexts, formal=formal)
    for row in audit_rows:
        row["source_commit"] = manifest["source_commit"]
    _write_jsonl(run_dir / "causal_audit.jsonl", audit_rows)
    controls = _build_source_controls(formal=formal)
    controls["source_commit"] = manifest["source_commit"]
    _atomic_json(run_dir / "source_controls.json", controls)


def _bootstrap_bounds(values: np.ndarray) -> tuple[float, float]:
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all():
        raise ValueError("bootstrap statistic must be one-dimensional and finite")
    lower, upper = np.percentile(values, (2.5, 97.5))
    return float(lower), float(upper)


def _metric_summary(observed: float, bootstrap_values: np.ndarray) -> dict[str, float]:
    observed = _finite_number(observed, "observed metric")
    lower, upper = _bootstrap_bounds(bootstrap_values)
    return {"mean": observed, "lcb95": lower, "ucb95": upper}


def _compact_analysis_statistics(
    episode_rows: Sequence[Mapping[str, Any]],
    audit_rows: Sequence[Mapping[str, Any]],
    *,
    formal: bool,
) -> dict[str, Any]:
    replicates = REPLICATES if formal else (0,)
    base_count = EVALUATION_BASE_IDS if formal else 2
    repetitions = BOOTSTRAP_REPETITIONS if formal else 8
    utility = np.full(
        (len(replicates), base_count, 2, len(ARMS), len(EVALUATION_PROFILES)),
        np.nan,
        dtype=np.float64,
    )
    support = np.zeros((len(replicates), base_count, 2, 5), dtype=np.float64)
    replicate_index = {replicate: index for index, replicate in enumerate(replicates)}
    for row in episode_rows:
        r = replicate_index[int(row["replicate"])]
        b = int(row["base_id"])
        s = 0 if int(row["sign_mate"]) == -1 else 1
        a = ARMS.index(str(row["arm"]))
        p = EVALUATION_PROFILES.index(str(row["profile"]))
        if math.isfinite(utility[r, b, s, a, p]):
            raise ValueError("duplicate evaluation episode identity")
        utility[r, b, s, a, p] = _finite_number(row["utility"], "utility")
        if a == ARMS.index("EHC") and p == EVALUATION_PROFILES.index("heldout_stochastic"):
            support[r, b, s] = np.asarray(
                [
                    row["spell_k1"], row["spell_k2"], row["spell_k3_plus"],
                    row["non_create_opportunities"], row["lifecycles_with_two_plus"],
                ],
                dtype=np.float64,
            )
    if not np.isfinite(utility).all():
        raise ValueError("evaluation utility tensor is incomplete or non-finite")

    audit_sum = np.zeros((len(replicates), base_count, 3), dtype=np.float64)
    audit_count = np.zeros_like(audit_sum)
    for row in audit_rows:
        r = replicate_index[int(row["replicate"])]
        b = int(row["base_id"])
        audit_sum[r, b, 0] += _finite_number(row["i_tv"], "i_tv")
        audit_count[r, b, 0] += 1
        metric = 1 if row["action"] == "KEEP" else 2
        audit_sum[r, b, metric] += _finite_number(row["c_total"], "c_total")
        audit_count[r, b, metric] += 1

    generator = np.random.Generator(
        np.random.Philox(SEED_REGISTRY["bootstrap"])
    )
    arm_samples = np.empty((repetitions, len(ARMS)), dtype=np.float64)
    k_samples = np.empty((repetitions, 3), dtype=np.float64)
    audit_samples = np.empty((repetitions, 3), dtype=np.float64)
    for start in range(0, repetitions, 128):
        stop = min(start + 128, repetitions)
        size = stop - start
        replicate_draw = generator.integers(
            0, len(replicates), (size, len(replicates))
        )
        base_draw = generator.integers(
            0, base_count, (size, len(replicates), base_count)
        )
        selected_utility = utility[
            replicate_draw[:, :, None], base_draw, :, :, :
        ]
        arm_samples[start:stop] = selected_utility[
            ..., EVALUATION_PROFILES.index("heldout_stochastic")
        ].mean(axis=(1, 2, 3))
        selected_support = support[
            replicate_draw[:, :, None], base_draw, :, :
        ].sum(axis=(1, 2, 3))
        spell_total = selected_support[:, :3].sum(axis=1)
        k_samples[start:stop] = np.divide(
            selected_support[:, :3],
            spell_total[:, None],
            out=np.zeros((size, 3), dtype=np.float64),
            where=spell_total[:, None] > 0,
        )
        selected_audit_sum = audit_sum[
            replicate_draw[:, :, None], base_draw, :
        ].sum(axis=(1, 2))
        selected_audit_count = audit_count[
            replicate_draw[:, :, None], base_draw, :
        ].sum(axis=(1, 2))
        audit_samples[start:stop] = np.divide(
            selected_audit_sum,
            selected_audit_count,
            out=np.zeros((size, 3), dtype=np.float64),
            where=selected_audit_count > 0,
        )

    heldout_utility = utility[..., EVALUATION_PROFILES.index("heldout_stochastic")]
    observed_arms = heldout_utility.mean(axis=(0, 1, 2))
    arm_intervals = {
        arm: _metric_summary(float(observed_arms[index]), arm_samples[:, index])
        for index, arm in enumerate(ARMS)
    }
    g_dum = arm_samples[:, ARMS.index("EHC")] - arm_samples[:, ARMS.index("DUM")]
    g_or = arm_samples[:, ARMS.index("EHC")] - arm_samples[:, ARMS.index("OR")]
    observed_g_dum = float(observed_arms[ARMS.index("EHC")] - observed_arms[ARMS.index("DUM")])
    observed_g_or = float(observed_arms[ARMS.index("EHC")] - observed_arms[ARMS.index("OR")])
    observed_spell_counts = support[..., :3].sum(axis=(0, 1, 2))
    observed_spell_total = float(observed_spell_counts.sum())
    observed_k = np.divide(
        observed_spell_counts,
        observed_spell_total,
        out=np.zeros(3, dtype=np.float64),
        where=observed_spell_total > 0,
    )
    total_audit_sum = audit_sum.sum(axis=(0, 1))
    total_audit_count = audit_count.sum(axis=(0, 1))
    observed_audit = np.divide(
        total_audit_sum,
        total_audit_count,
        out=np.zeros(3, dtype=np.float64),
        where=total_audit_count > 0,
    )
    max_arm = {
        key: max(interval[key] for interval in arm_intervals.values())
        for key in ("mean", "lcb95", "ucb95")
    }
    return {
        "arm_utility": arm_intervals,
        "max_arm": max_arm,
        "g_dum": _metric_summary(observed_g_dum, g_dum),
        "g_or": _metric_summary(observed_g_or, g_or),
        "k_bins": [
            _metric_summary(float(observed_k[index]), k_samples[:, index])
            for index in range(3)
        ],
        "i_tv": _metric_summary(float(observed_audit[0]), audit_samples[:, 0]),
        "c_keep": _metric_summary(float(observed_audit[1]), audit_samples[:, 1]),
        "c_renew": _metric_summary(float(observed_audit[2]), audit_samples[:, 2]),
        "support_totals": {
            "non_create_opportunities": int(support[..., 3].sum()),
            "lifecycles_with_two_plus": int(support[..., 4].sum()),
        },
    }


def _source_identifiable(
    episode_rows: Sequence[Mapping[str, Any]],
    controls: Mapping[str, Any],
    *,
    formal: bool,
) -> bool:
    if not formal:
        return False
    control_rows = controls.get("rows")
    if not isinstance(control_rows, list) or len(control_rows) != 8:
        return False
    for profile in EVALUATION_PROFILES:
        oracle = next(
            (row for row in control_rows if row.get("profile") == profile and row.get("controller") == "oracle"),
            None,
        )
        history = next(
            (row for row in control_rows if row.get("profile") == profile and row.get("controller") == "history_free"),
            None,
        )
        if oracle is None or history is None:
            return False
        if _finite_number(oracle.get("lcb95"), "oracle_lcb") < 0.80:
            return False
        if _finite_number(history.get("ucb95"), "history_ucb") >= 0.80:
            return False
    held = [
        row for row in episode_rows
        if row["arm"] == "EHC" and row["profile"] == "heldout_stochastic"
    ]
    if {duration for row in held for duration in row["durations"]} != {6, 10, 14, 18}:
        return False
    if {row["roster_size"] for row in held} != {2, 3}:
        return False
    if {row["sign_mate"] for row in held} != {-1, 1}:
        return False
    if not any(row["completed_segments"] > 0 for row in held):
        return False
    if not any(row["censored_segments"] > 0 for row in held):
        return False
    if sum(row["non_create_opportunities"] for row in held) < 1_000:
        return False
    if sum(row["lifecycles_with_two_plus"] for row in held) < 250:
        return False
    if sum(row["natural_keep"] for row in held) < 128 or sum(row["natural_renew"] for row in held) < 128:
        return False
    for replicate in REPLICATES:
        replicate_rows = [row for row in held if row["replicate"] == replicate]
        if sum(row["natural_keep"] for row in replicate_rows) < 16:
            return False
        if sum(row["natural_renew"] for row in replicate_rows) < 16:
            return False
    return True


def _predicate_inputs_from_evidence(
    metrics: Mapping[str, Any],
    *,
    operational_errors: Sequence[str],
    source_identifiable: bool,
) -> dict[str, Any]:
    return {
        "operational_valid": len(operational_errors) == 0,
        "source_identifiable": source_identifiable,
        "max_arm_lcb": metrics["max_arm"]["lcb95"],
        "max_arm_ucb": metrics["max_arm"]["ucb95"],
        "g_dum_lcb": metrics["g_dum"]["lcb95"],
        "g_dum_ucb": metrics["g_dum"]["ucb95"],
        "g_or_lcb": metrics["g_or"]["lcb95"],
        "g_or_ucb": metrics["g_or"]["ucb95"],
        "k_lcbs": [row["lcb95"] for row in metrics["k_bins"]],
        "k_ucbs": [row["ucb95"] for row in metrics["k_bins"]],
        "i_tv_lcb": metrics["i_tv"]["lcb95"],
        "i_tv_ucb": metrics["i_tv"]["ucb95"],
        "c_keep_lcb": metrics["c_keep"]["lcb95"],
        "c_keep_ucb": metrics["c_keep"]["ucb95"],
        "c_renew_lcb": metrics["c_renew"]["lcb95"],
        "c_renew_ucb": metrics["c_renew"]["ucb95"],
        "c_keep_mean": metrics["c_keep"]["mean"],
        "c_renew_mean": metrics["c_renew"]["mean"],
    }


def _require_analysis_binding(
    result: Mapping[str, Any],
    *,
    metrics: Mapping[str, Any],
    predicate_inputs: Mapping[str, Any],
    operational_errors: Sequence[str],
) -> None:
    if result.get("metrics") != metrics:
        raise ValueError("formal serialized metrics do not match referenced evidence")
    if result.get("predicate_inputs") != predicate_inputs:
        raise ValueError("formal predicate_inputs do not match derived metrics and source evidence")
    if result.get("operational_errors") != list(operational_errors):
        raise ValueError("formal operational_errors do not match referenced evidence")


def _write_and_validate_analysis(
    run_dir: Path,
    result: Mapping[str, Any],
    *,
    formal: bool,
) -> None:
    _atomic_json(run_dir / "analysis_result.json", result)
    if formal:
        validate_formal_result(run_dir)


def analyze(*, run_dir: Path, formal: bool) -> dict[str, Any]:
    configure_cpu_runtime()
    manifest = _read_json(run_dir / "manifest.json")
    if manifest.get("formal") is not formal:
        raise ValueError("analyze formal flag does not match the run manifest")
    replicates = REPLICATES if formal else (0,)
    evaluation_references = (
        _exact_evaluation_references()
        if formal
        else [
            f"evaluation/replicate_0/{arm}/{profile}.jsonl"
            for arm in ARMS for profile in EVALUATION_PROFILES
        ]
    )
    checkpoint_references = (
        _exact_checkpoint_references()
        if formal
        else [f"checkpoints/replicate_0/{arm}/update_1.pt" for arm in ARMS]
    )
    episode_rows: list[dict[str, Any]] = []
    operational_errors: list[str] = []
    try:
        expected_updates = 250 if formal else 1
        expected_base_steps = 1_000 if formal else 4
        for reference in checkpoint_references:
            checkpoint_path = _resolve_reference(run_dir, reference)
            parts = PurePosixPath(reference).parts
            replicate = int(parts[1].removeprefix("replicate_"))
            arm = parts[2]
            payload = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
            if (
                not isinstance(payload, dict)
                or payload.get("schema") != CHECKPOINT_SCHEMA
                or payload.get("source_family") != SOURCE_FAMILY
                or payload.get("backend") != "cpu"
                or payload.get("torch_threads") != 1
                or payload.get("arm") != arm
                or payload.get("replicate") != replicate
                or payload.get("update") != expected_updates
                or payload.get("base_optimizer_steps") != expected_base_steps
                or payload.get("event_optimizer_steps") != (0 if arm == "OR" else expected_base_steps)
            ):
                raise ValueError(f"checkpoint payload is malformed: {reference}")
        for reference in evaluation_references:
            cell_rows = _read_jsonl(_resolve_reference(run_dir, reference))
            expected_count = EVALUATION_EPISODES if formal else 4
            if len(cell_rows) != expected_count:
                raise ValueError(f"evaluation cell row count is malformed: {reference}")
            parts = PurePosixPath(reference).parts
            replicate = int(parts[1].removeprefix("replicate_"))
            arm = parts[2]
            profile = parts[3].removesuffix(".jsonl")
            expected_ids = {
                (base_id, sign_mate)
                for base_id in range(EVALUATION_BASE_IDS if formal else 2)
                for sign_mate in (-1, 1)
            }
            if {(row.get("base_id"), row.get("sign_mate")) for row in cell_rows} != expected_ids:
                raise ValueError(f"evaluation cell identity inventory is malformed: {reference}")
            for row in cell_rows:
                if (
                    row.get("schema") != EVALUATION_ROW_SCHEMA
                    or row.get("source_family") != SOURCE_FAMILY
                    or row.get("source_commit") != manifest["source_commit"]
                    or row.get("replicate") != replicate
                    or row.get("arm") != arm
                    or row.get("profile") != profile
                ):
                    raise ValueError(f"evaluation row/path identity is malformed: {reference}")
                utility = _finite_number(row.get("utility"), "utility")
                reward_sum = _finite_number(row.get("reward_sum"), "reward_sum")
                if abs(utility - reward_sum) > 1e-9:
                    raise ValueError(f"evaluation reward identity is malformed: {reference}")
                if type(row.get("operational_valid")) is not bool:
                    raise ValueError(f"evaluation operational flag is malformed: {reference}")
                if row["operational_valid"] is False:
                    operational_errors.append(
                        f"evaluation operational invariant failed: {reference}"
                    )
            episode_rows.extend(cell_rows)
        audit_rows = _read_jsonl(_resolve_reference(run_dir, "causal_audit.jsonl"))
        controls = _read_json(_resolve_reference(run_dir, "source_controls.json"))
        metrics = _compact_analysis_statistics(
            episode_rows, audit_rows, formal=formal
        )
    except (KeyError, TypeError, ValueError, OSError) as error:
        operational_errors.append(str(error))
        metrics = {
            "max_arm": {"lcb95": 0.0, "ucb95": 0.0},
            "g_dum": {"lcb95": 0.0, "ucb95": 0.0},
            "g_or": {"lcb95": 0.0, "ucb95": 0.0},
            "k_bins": [{"lcb95": 0.0, "ucb95": 0.0}] * 3,
            "i_tv": {"lcb95": 0.0, "ucb95": 0.0},
            "c_keep": {"mean": 0.0, "lcb95": 0.0, "ucb95": 0.0},
            "c_renew": {"mean": 0.0, "lcb95": 0.0, "ucb95": 0.0},
        }
        audit_rows = []
        controls = {}
    source_identifiable = False
    if not operational_errors:
        try:
            source_identifiable = _source_identifiable(
                episode_rows, controls, formal=formal
            )
        except (KeyError, TypeError, ValueError) as error:
            operational_errors.append(str(error))
    predicate_inputs = _predicate_inputs_from_evidence(
        metrics,
        operational_errors=operational_errors,
        source_identifiable=source_identifiable,
    )
    result_name = select_result_branch(**predicate_inputs)
    result = {
        "schema": ANALYSIS_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "formal": formal,
        "backend": "cpu",
        "torch_threads": 1,
        "source_commit": manifest["source_commit"],
        "result": result_name,
        "authorization_token": manifest["authorization_token"],
        "seed_registry": SEED_REGISTRY,
        "budget": manifest["budget"],
        "checkpoint_references": checkpoint_references,
        "evaluation_references": evaluation_references,
        "source_control_reference": "source_controls.json",
        "audit_reference": "causal_audit.jsonl",
        "bootstrap_repetitions": manifest["budget"]["bootstrap_repetitions"],
        "operational_errors": operational_errors,
        "predicate_inputs": predicate_inputs,
        "metrics": metrics,
    }
    _write_and_validate_analysis(run_dir, result, formal=formal)
    return result


def exercise(*, run_dir: Path) -> dict[str, Any]:
    configure_cpu_runtime()
    train(
        run_dir=run_dir,
        formal=False,
        authorization_token=None,
        source_commit="NONFORMAL_EXERCISE",
        updates_override=1,
    )
    evaluate(run_dir=run_dir, formal=False)
    result = analyze(run_dir=run_dir, formal=False)
    if result.get("formal") is not False:
        raise RuntimeError("exercise analysis must remain nonformal")
    try:
        validate_formal_result(run_dir)
    except ValueError as error:
        if "formal=true" not in str(error):
            raise
    else:
        raise RuntimeError("formal validator accepted a nonformal exercise")
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("train", "evaluate", "analyze", "exercise"):
        child = subparsers.add_parser(command)
        child.add_argument("--run-dir", type=Path, required=True)
        if command == "train":
            child.add_argument("--formal", action="store_true")
            child.add_argument("--authorization-token")
            child.add_argument("--source-commit")
        elif command in ("evaluate", "analyze"):
            child.add_argument("--formal", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.command == "train":
        train(
            run_dir=arguments.run_dir,
            formal=arguments.formal,
            authorization_token=arguments.authorization_token,
            source_commit=arguments.source_commit,
        )
    elif arguments.command == "evaluate":
        evaluate(run_dir=arguments.run_dir, formal=arguments.formal)
    elif arguments.command == "analyze":
        analyze(run_dir=arguments.run_dir, formal=arguments.formal)
    else:
        exercise(run_dir=arguments.run_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
