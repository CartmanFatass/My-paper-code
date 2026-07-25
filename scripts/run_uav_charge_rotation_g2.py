"""Source-first train, evaluate, analyze, and validate UAV charge-rotation G2."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import random
import re
import sys
from typing import Any, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process.uav_charge_rotation_g2 import (
    CONSTRUCTIVE_CHARGE_ROTATION,
    ENERGY_PROFILE_VALUES,
    FIXED_MASK_REC,
    HORIZON,
    NO_PROACTIVE_ROTATION,
    PREFIX_NORMALIZED_OPEN_ROSTER,
    ConstructiveChargeRotationController,
    EnergyProfile,
    MatchedChargeRotationPolicy,
    NoProactiveRotationController,
    PersistentG2VectorEnv,
    evaluate_g2_controller,
    evaluate_g2_policy,
    g2_checkpoint_state,
    load_g2_checkpoint_state,
    make_g2_environment,
    make_g2_episode_ledger,
    maximum_state_difference,
    model_state_copy,
    optimize_g2_update,
    collect_g2_trajectory,
)


SOURCE_FAMILY = "UAV_CHARGE_ROTATION_ROSTER_G2"
RUN_SCHEMA = "hmasd.uav_charge_rotation_g2.run.v1"
LAUNCH_SCHEMA = "hmasd.uav_charge_rotation_g2.launch.v1"
SOURCE_SCREEN_SCHEMA = "hmasd.uav_charge_rotation_g2.source_screen.v1"
SOURCE_SCREEN_CHUNK_SCHEMA = "hmasd.uav_charge_rotation_g2.source_chunk.v1"
RESUME_SCHEMA = "hmasd.uav_charge_rotation_g2.resume.v1"
CHECKPOINT_SCHEMA = "hmasd.uav_charge_rotation_g2.final_checkpoint.v1"
EVALUATION_ROW_SCHEMA = "hmasd.uav_charge_rotation_g2.evaluation_row.v1"
EVALUATION_CHUNK_SCHEMA = "hmasd.uav_charge_rotation_g2.evaluation_chunk.v1"
EVALUATION_SCHEMA = "hmasd.uav_charge_rotation_g2.evaluation.v1"
ANALYSIS_SCHEMA = "hmasd.uav_charge_rotation_g2.analysis.v1"
COMMIT_SCHEMA = "hmasd.uav_charge_rotation_g2.immutable_commit.v1"
FORMAL_AUTHORIZATION_TOKEN = (
    "AUTHORIZE_UAV_CHARGE_ROTATION_ROSTER_G2_FORMAL_CPU_V1"
)

TRAIN_COMPLETE = "TRAIN_COMPLETE"
TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE = "TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE"
ARM_NAMES = (FIXED_MASK_REC, PREFIX_NORMALIZED_OPEN_ROSTER)
CONTROL_NAMES = (CONSTRUCTIVE_CHARGE_ROTATION, NO_PROACTIVE_ROTATION)
EVALUATION_PROFILES = (
    EnergyProfile.IID,
    EnergyProfile.LOW_ENERGY,
    EnergyProfile.SYNCHRONIZED_PRESSURE,
)
ACTION_MODES = ("deterministic", "stochastic")
STRATA = tuple((profile.value, mode) for profile in EVALUATION_PROFILES for mode in ACTION_MODES)
STRATUM_KEYS = tuple(f"{profile}:{mode}" for profile, mode in STRATA)

ACCESS_THRESHOLD = 1.0
EVENT_ACCESS_FLOOR = 0.80
ORDINARY_ACCESS_FLOOR = 0.90
CONSTRUCTIVE_FLOOR = 0.90
LOAD_BEARING_MARGIN = 0.10
SAFETY_LIMIT = 0.05
SERVICE_GAIN_MARGIN = 0.03
REJOIN_GAIN_MARGIN = 0.02
ORDINARY_NONINFERIORITY_MARGIN = -0.02
REPLAY_TOLERANCE = 1.0e-6
LEARNING_RATE = 3.0e-4
REJOIN_LATEST_STEP = 1440

INVALID_RESULT = "INVALID_UAV_CHARGE_ROTATION_G2"
SOURCE_NON_IDENTIFIABLE_RESULT = "SOURCE_NON_IDENTIFIABLE_UAV_CHARGE_ROTATION_G2"
NO_ACCESS_RESULT = "NO_ACCESS_UAV_CHARGE_ROTATION_G2"
UNDERPOWERED_RESULT = "UNDERPOWERED_ACCESS_UAV_CHARGE_ROTATION_G2"
MASK_SUFFICIENT_RESULT = "USABLE_MASK_SUFFICIENT_UAV_CHARGE_ROTATION_G2"
DYNAMIC_SUPPORTED_RESULT = "DYNAMIC_LIFECYCLE_SUPPORTED_UAV_CHARGE_ROTATION_G2"
MIXED_RESULT = "MIXED_ANOMALOUS_UAV_CHARGE_ROTATION_G2"
NONFORMAL_RESULT = "NONFORMAL_UAV_CHARGE_ROTATION_G2_EXERCISE_COMPLETE"


@dataclass(frozen=True)
class RunConfig:
    replicates: int
    updates: int
    num_envs: int
    horizon: int
    ppo_passes: int
    evaluation_episodes: int
    evaluation_batch_size: int
    control_episodes: int
    bootstrap_resamples: int
    checkpoint_selection: str


@dataclass(frozen=True)
class SeedRegistry:
    model_initialization: int = 2_310_000
    training_ledger: int = 2_311_000
    training_environment: int = 2_312_000
    training_action: int = 2_313_000
    evaluation_ledger: int = 2_314_000
    evaluation_environment: int = 2_315_000
    evaluation_action: int = 2_316_000
    control: int = 2_317_000
    bootstrap: int = 2_318_000


FORMAL_CONFIG = RunConfig(
    replicates=3,
    updates=128,
    num_envs=8,
    horizon=1500,
    ppo_passes=4,
    evaluation_episodes=128,
    evaluation_batch_size=16,
    control_episodes=128,
    bootstrap_resamples=10_000,
    checkpoint_selection="final_update_128_only",
)
EXERCISE_CONFIG = RunConfig(
    replicates=1,
    updates=1,
    num_envs=1,
    horizon=8,
    ppo_passes=1,
    evaluation_episodes=1,
    evaluation_batch_size=1,
    control_episodes=1,
    bootstrap_resamples=32,
    checkpoint_selection="final_update_1_only",
)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_json_immutable(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def _write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"{path} must contain one JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        value = json.loads(line)
        if type(value) is not dict:
            raise ValueError(f"{path}:{line_number} must contain one JSON object")
        rows.append(value)
    return rows


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _commit_artifact(root: Path, reference: str, schema: str) -> dict[str, str]:
    artifact = root / reference
    marker_reference = f"{reference}.complete.json"
    marker = root / marker_reference
    payload = {
        "schema": COMMIT_SCHEMA,
        "artifact_schema": schema,
        "artifact_reference": reference,
        "artifact_sha256": _sha256_file(artifact),
    }
    _write_json_immutable(marker, payload)
    return {
        "reference": reference,
        "complete_reference": marker_reference,
        "sha256": payload["artifact_sha256"],
    }


def _validate_committed_artifact(
    root: Path, binding: Mapping[str, Any], *, schema: str
) -> Path:
    reference = binding.get("reference")
    complete_reference = binding.get("complete_reference")
    digest = binding.get("sha256")
    if (
        type(reference) is not str
        or type(complete_reference) is not str
        or complete_reference != f"{reference}.complete.json"
        or type(digest) is not str
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
    ):
        raise ValueError("artifact binding is malformed")
    artifact = (root / reference).resolve()
    marker_path = (root / complete_reference).resolve()
    try:
        artifact.relative_to(root.resolve())
        marker_path.relative_to(root.resolve())
    except ValueError as error:
        raise ValueError("artifact binding escapes run root") from error
    if not artifact.is_file() or not marker_path.is_file():
        raise ValueError("artifact binding references a missing file")
    marker = _read_json(marker_path)
    expected = {
        "schema": COMMIT_SCHEMA,
        "artifact_schema": schema,
        "artifact_reference": reference,
        "artifact_sha256": digest,
    }
    if marker != expected or _sha256_file(artifact) != digest:
        raise ValueError("artifact binding SHA-256 mismatch")
    return artifact


def _recover_binding(root: Path, reference: str, *, schema: str) -> dict[str, str] | None:
    artifact = root / reference
    marker = root / f"{reference}.complete.json"
    if not artifact.exists() and not marker.exists():
        return None
    if artifact.is_file() and not marker.exists():
        artifact.unlink()
        return None
    if not artifact.is_file() or not marker.is_file():
        raise ValueError("committed artifact recovery encountered a split pair")
    try:
        value = _read_json(marker)
    except (json.JSONDecodeError, UnicodeError):
        marker.unlink()
        artifact.unlink()
        return None
    binding = {
        "reference": reference,
        "complete_reference": f"{reference}.complete.json",
        "sha256": value.get("artifact_sha256"),
    }
    _validate_committed_artifact(root, binding, schema=schema)
    return binding


def _read_binding_or_truncated(path: Path) -> dict[str, Any] | None:
    try:
        return _read_json(path)
    except (json.JSONDecodeError, UnicodeError):
        return None


def _terminal_binding(
    root: Path,
    binding_path: Path,
    *,
    reference: str,
    schema: str,
) -> dict[str, Any] | None:
    if binding_path.exists():
        binding = _read_binding_or_truncated(binding_path)
        if binding is not None:
            return binding
        binding_path.unlink()
    recovered = _recover_binding(root, reference, schema=schema)
    if recovered is not None:
        _write_json_immutable(binding_path, recovered)
    return recovered


def _recover_attempt_binding(
    root: Path,
    *,
    directory: Path,
    artifact_pattern: str,
    artifact_name_pattern: str,
    schema: str,
) -> dict[str, str] | None:
    candidates: list[tuple[int, dict[str, str]]] = []
    if not directory.exists():
        return None
    for artifact in directory.glob(artifact_pattern):
        match = re.fullmatch(artifact_name_pattern, artifact.name)
        if match is None:
            continue
        marker = Path(f"{artifact}.complete.json")
        if not marker.exists():
            continue
        try:
            marker_value = _read_json(marker)
        except (json.JSONDecodeError, UnicodeError):
            continue
        reference = artifact.relative_to(root).as_posix()
        binding = {
            "reference": reference,
            "complete_reference": f"{reference}.complete.json",
            "sha256": marker_value.get("artifact_sha256"),
        }
        _validate_committed_artifact(root, binding, schema=schema)
        candidates.append((int(match.group(1)), binding))
    return max(candidates, key=lambda row: row[0])[1] if candidates else None


def configure_runtime(seed: int) -> None:
    random.seed(int(seed))
    np.random.seed(int(seed))
    torch.manual_seed(int(seed))
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)


def _runtime_identity() -> dict[str, Any]:
    return {
        "backend": "cpu",
        "torch": str(torch.__version__),
        "torch_threads": int(torch.get_num_threads()),
        "python": str(Path(sys.executable).resolve()),
    }


def _replicate_seeds(replicate: int) -> dict[str, int]:
    if type(replicate) is not int or replicate < 0:
        raise ValueError("replicate must be a nonnegative exact integer")
    offset = replicate * 10_000
    return {name: int(value) + offset for name, value in asdict(SeedRegistry()).items()}


def _validate_launch(
    *, formal: bool, authorization_token: str | None, config: RunConfig
) -> None:
    if formal:
        if authorization_token != FORMAL_AUTHORIZATION_TOKEN:
            raise ValueError("formal G2 authorization token mismatch")
        if config != FORMAL_CONFIG:
            raise ValueError("formal G2 counts differ from the frozen contract")
    elif authorization_token is not None:
        raise ValueError("nonformal G2 run cannot carry a formal authorization token")
    integer_values = (
        config.replicates,
        config.updates,
        config.num_envs,
        config.horizon,
        config.ppo_passes,
        config.evaluation_episodes,
        config.evaluation_batch_size,
        config.control_episodes,
        config.bootstrap_resamples,
    )
    if any(type(value) is not int or value <= 0 for value in integer_values):
        raise ValueError("G2 counts must be positive exact integers")
    if config.evaluation_episodes % config.evaluation_batch_size != 0:
        raise ValueError("evaluation episodes must divide into immutable batches")
    if formal and config.horizon != HORIZON:
        raise ValueError("formal G2 horizon must be exactly 1500")
    if not formal and config.horizon > HORIZON:
        raise ValueError("nonformal horizon cannot exceed the frozen physical horizon")
    expected_checkpoint = f"final_update_{config.updates}_only"
    if config.checkpoint_selection != expected_checkpoint:
        raise ValueError("checkpoint selection must designate only the final update")


def _validate_source_commit(source_commit: object, *, formal: bool) -> str:
    if type(source_commit) is not str or not source_commit:
        raise ValueError("source commit must be a non-empty string")
    if formal and re.fullmatch(r"[0-9a-f]{40}", source_commit) is None:
        raise ValueError("formal source commit must be a lowercase 40-character Git commit")
    return source_commit


def _launch_identity(
    *, source_commit: str, formal: bool, authorization_token: str | None, config: RunConfig
) -> dict[str, Any]:
    return {
        "schema": LAUNCH_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": source_commit,
        "formal": formal,
        "authorization_token": authorization_token,
        "config": asdict(config),
        "seed_registry": asdict(SeedRegistry()),
        "runtime": _runtime_identity(),
    }


def _open_launch(root: Path, identity: Mapping[str, Any]) -> bool:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "launch_identity.json"
    if path.exists():
        if not path.is_file():
            raise ValueError("same-root resume launch identity mismatch")
        try:
            existing = _read_json(path)
        except (json.JSONDecodeError, UnicodeError):
            if list(root.iterdir()) != [path]:
                raise ValueError(
                    "truncated launch identity cannot be recovered after artifacts exist"
                )
            path.unlink()
            _write_json_immutable(path, identity)
            return True
        if existing != identity:
            raise ValueError("same-root resume launch identity mismatch")
        return True
    if any(root.iterdir()):
        raise ValueError("fresh run root is not empty")
    _write_json_immutable(path, identity)
    return False


def _finite_number(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, np.integer, np.floating)):
        raise ValueError(f"{name} must be a finite number")
    result = float(value)
    if not np.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _interval(draws: np.ndarray, point: float) -> dict[str, float]:
    if draws.ndim != 1 or draws.size < 1 or not np.all(np.isfinite(draws)):
        raise ValueError("bootstrap draws must be one-dimensional and finite")
    return {
        "mean": float(point),
        "lcb95": float(np.percentile(draws, 2.5)),
        "ucb95": float(np.percentile(draws, 97.5)),
    }


def hierarchical_paired_interval(
    values: np.ndarray, *, resamples: int, seed: int
) -> dict[str, float]:
    """Replicate-first bootstrap with whole paired episode IDs shared by strata."""

    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 3 or min(array.shape) < 1 or not np.all(np.isfinite(array)):
        raise ValueError("paired values must be finite [replicate,stratum,episode]")
    if type(resamples) is not int or resamples <= 0:
        raise ValueError("resamples must be a positive exact integer")
    replicates, _strata, episodes = array.shape
    rng = np.random.default_rng(int(seed))
    replicate_draws = rng.integers(0, replicates, size=(resamples, replicates))
    episode_draws = rng.integers(
        0, episodes, size=(resamples, replicates, episodes)
    )
    draws = np.empty(resamples, dtype=np.float64)
    for draw_index in range(resamples):
        selected: list[np.ndarray] = []
        for slot, replicate in enumerate(replicate_draws[draw_index]):
            selected.append(array[replicate, :, episode_draws[draw_index, slot]])
        draws[draw_index] = float(np.mean(np.stack(selected)))
    return _interval(draws, float(np.mean(array)))


def source_identification(
    intervals: Mapping[str, Mapping[str, Mapping[str, object]]],
    support: Mapping[str, object],
) -> dict[str, bool]:
    profile_performance: list[bool] = []
    constructive_feasibility: list[bool] = []
    load_bearing: list[bool] = []
    for profile in EVALUATION_PROFILES:
        row = intervals.get(profile.value)
        if type(row) is not dict:
            raise ValueError("source intervals omit a registered energy profile")
        mean_phi = _finite_number(
            "constructive Phi mean", row["constructive_phi"]["mean"]
        )
        contrast_lcb = _finite_number(
            "constructive contrast LCB",
            row["constructive_minus_no_rotation"]["lcb95"],
        )
        constructive_feasibility.append(mean_phi >= CONSTRUCTIVE_FLOOR)
        load_bearing.append(contrast_lcb > LOAD_BEARING_MARGIN)
        profile_performance.append(
            mean_phi >= CONSTRUCTIVE_FLOOR and contrast_lcb > LOAD_BEARING_MARGIN
        )

    def exact_zero(name: str) -> bool:
        value = support.get(name)
        return type(value) is int and value == 0

    def per_replicate_floor(name: str, floor: int) -> bool:
        value = support.get(name)
        return (
            type(value) is list
            and len(value) > 0
            and all(type(item) is int and item >= floor for item in value)
        )

    pressure = support.get("no_rotation_pressure_counts")
    pressure_pass = type(pressure) is dict
    if pressure_pass:
        pressure_pass = all(
            type(pressure[profile.value]) is list
            and len(pressure[profile.value]) > 0
            and all(type(item) is int and item >= 96 for item in pressure[profile.value])
            for profile in EVALUATION_PROFILES
        )
    support_pass = all(
        (
            exact_zero("constructive_cutoff_events"),
            exact_zero("constructive_depletion_events"),
            exact_zero("constructive_positive_return_cost_rows"),
            per_replicate_floor("iid_complete_cycles_per_replicate", 128),
            per_replicate_floor("low_energy_complete_cycles_per_replicate", 256),
            per_replicate_floor("synchronized_pressure_complete_cycles_per_replicate", 256),
            exact_zero("late_rejoin_count"),
            exact_zero("episodes_without_station_use"),
            per_replicate_floor("synchronized_concurrent_episode_counts", 64),
            pressure_pass,
            support.get("physical_consistency") is True,
            support.get("energy_profile_law") is True,
            support.get("control_behavior") is True,
            support.get("no_future_leakage") is True,
            support.get("source_pressure") is True,
        )
    )
    result = {
        "constructive_feasibility_pass": all(constructive_feasibility),
        "load_bearing_pass": all(load_bearing),
        "support_pass": support_pass,
    }
    result["source_identifiable"] = all(profile_performance) and support_pass
    return result


def classify_arm_access(
    access_interval: Mapping[str, object],
    safety_intervals: Mapping[str, Mapping[str, Mapping[str, object]]],
) -> dict[str, bool]:
    access_lcb = _finite_number("access LCB", access_interval.get("lcb95"))
    access_ucb = _finite_number("access UCB", access_interval.get("ucb95"))
    if set(safety_intervals) != set(STRATUM_KEYS):
        raise ValueError("arm safety inventory must contain exactly six profile-mode cells")
    safe_pass = True
    safe_fail = False
    for key in STRATUM_KEYS:
        cell = safety_intervals[key]
        catastrophe = cell.get("catastrophe_fraction")
        burden = cell.get("return_cost_burden")
        if type(catastrophe) is not dict or type(burden) is not dict:
            raise ValueError("arm safety cell is malformed")
        cat_lcb = _finite_number("catastrophe LCB", catastrophe.get("lcb95"))
        cat_ucb = _finite_number("catastrophe UCB", catastrophe.get("ucb95"))
        ret_lcb = _finite_number("return burden LCB", burden.get("lcb95"))
        ret_ucb = _finite_number("return burden UCB", burden.get("ucb95"))
        safe_pass = safe_pass and cat_ucb <= SAFETY_LIMIT and ret_ucb <= SAFETY_LIMIT
        safe_fail = safe_fail or cat_lcb > SAFETY_LIMIT or ret_lcb > SAFETY_LIMIT
    access_pass = access_lcb >= ACCESS_THRESHOLD and safe_pass
    access_fail = access_ucb < ACCESS_THRESHOLD or safe_fail
    return {
        "access_pass": access_pass,
        "access_fail": access_fail,
        "access_underpowered": not access_pass and not access_fail,
        "safe_pass": safe_pass,
        "safe_fail": safe_fail,
    }


def select_result_branch(predicate_inputs: Mapping[str, object]) -> str:
    required_bools = (
        "operational_valid",
        "source_identifiable",
        "fixed_access_pass",
        "fixed_access_fail",
        "open_access_pass",
        "open_access_fail",
    )
    if any(type(predicate_inputs.get(name)) is not bool for name in required_bools):
        raise ValueError("branch predicate booleans are missing or malformed")
    if not predicate_inputs["operational_valid"]:
        return INVALID_RESULT
    if not predicate_inputs["source_identifiable"]:
        return SOURCE_NON_IDENTIFIABLE_RESULT
    fixed_pass = bool(predicate_inputs["fixed_access_pass"])
    fixed_fail = bool(predicate_inputs["fixed_access_fail"])
    open_pass = bool(predicate_inputs["open_access_pass"])
    open_fail = bool(predicate_inputs["open_access_fail"])
    if fixed_fail and open_fail:
        return NO_ACCESS_RESULT
    if not fixed_pass and not open_pass and (not fixed_fail or not open_fail):
        return UNDERPOWERED_RESULT
    if predicate_inputs.get("comparisons_complete", True) is not True:
        return MIXED_RESULT
    g_svc_lcb = _finite_number("G_svc LCB", predicate_inputs.get("g_svc_lcb"))
    g_svc_ucb = _finite_number("G_svc UCB", predicate_inputs.get("g_svc_ucb"))
    g_rejoin_lcb = _finite_number("G_rejoin LCB", predicate_inputs.get("g_rejoin_lcb"))
    g_rejoin_ucb = _finite_number("G_rejoin UCB", predicate_inputs.get("g_rejoin_ucb"))
    g_ordinary_lcb = _finite_number(
        "G_ordinary LCB", predicate_inputs.get("g_ordinary_lcb")
    )
    if (
        fixed_pass
        and g_svc_ucb <= SERVICE_GAIN_MARGIN
        and g_rejoin_ucb <= REJOIN_GAIN_MARGIN
    ):
        return MASK_SUFFICIENT_RESULT
    if (
        open_pass
        and g_svc_lcb > SERVICE_GAIN_MARGIN
        and g_rejoin_lcb > REJOIN_GAIN_MARGIN
        and g_ordinary_lcb >= ORDINARY_NONINFERIORITY_MARGIN
    ):
        return DYNAMIC_SUPPORTED_RESULT
    return MIXED_RESULT


def synthetic_control_rows(
    *, replicates: int, episodes: int, constructive_phi: float, no_rotation_phi: float
) -> list[dict[str, object]]:
    """Test-only deterministic source rows; never called by production paths."""

    rows: list[dict[str, object]] = []
    for replicate in range(replicates):
        for profile in EVALUATION_PROFILES:
            for episode_id in range(episodes):
                common = {
                    "replicate": replicate,
                    "profile": profile.value,
                    "episode_id": episode_id,
                    "ledger_id": f"synthetic:{replicate}:{profile.value}:{episode_id}",
                    "cutoff_events": 0,
                    "depletion_events": 0,
                    "positive_return_cost_rows": 0,
                    "complete_cycles": 2,
                    "latest_rejoin_step": min(REJOIN_LATEST_STEP, 1),
                    "station_used": True,
                    "max_concurrent_absent": 2,
                    "pressure_event": True,
                    "physical_consistency": True,
                    "energy_profile_law": True,
                    "control_behavior": True,
                    "no_future_leakage": True,
                    "source_pressure": True,
                    "environment_seed": 9000 + episode_id,
                    "energy_permutation": list(range(8)),
                    "initial_energy_ratios": list(ENERGY_PROFILE_VALUES[profile]),
                    "action_path_sha256": f"{episode_id:064x}",
                    "queue_uav_steps": 0,
                    "max_queue_length": 0,
                }
                evidence = {
                    "candidate_order": [0],
                    "projected_terminal_margins": [-0.1, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7],
                    "station_assignments": [0, -1, -1, -1, -1, -1, -1, -1],
                    "departure_steps": [1, 1501, 1501, 1501, 1501, 1501, 1501, 1501],
                    "first_departure_step": 1,
                    "candidate_iff_negative_terminal_margin": True,
                    "strict_nearest_station_assignment": True,
                    "latest_safe_departure_verified": True,
                    "common_actions_before_first_departure": True,
                    "reallocation_after_every_leave_rejoin": True,
                    "reallocation_event_steps": [2, 3],
                    "lifecycle_boundary_steps": [2, 3],
                    "current_only_planning": True,
                    "future_user_channel_queue_policy_rng_used": False,
                    "physical_consistency": True,
                    "projection_audit_history": [
                        {
                            "physical_step": 0,
                            "trigger": "RESET",
                            "candidate_order": [0],
                            "projected_terminal_margins": [
                                -0.1,
                                0.1,
                                0.2,
                                0.3,
                                0.4,
                                0.5,
                                0.6,
                                0.7,
                            ],
                            "station_assignments": [0, -1, -1, -1, -1, -1, -1, -1],
                            "departure_steps": [1, 1501, 1501, 1501, 1501, 1501, 1501, 1501],
                            "planned_completion_steps": [2, -1, -1, -1, -1, -1, -1, -1],
                            "candidate_order_verified": True,
                            "strict_nearest_station_assignment": True,
                            "latest_safe_departure_verified": True,
                            "current_only_planning": True,
                        }
                    ],
                    "projection_audit_count": 1,
                    "initial_candidate_order": [0],
                    "initial_source_pressure": True,
                    "all_projection_audits_pass": True,
                    "plan_consistency": True,
                }
                rows.append(
                    common
                    | {
                        "control": CONSTRUCTIVE_CHARGE_ROTATION,
                        "Phi": constructive_phi,
                        "source_evidence": evidence
                        | {
                            "controller_name": CONSTRUCTIVE_CHARGE_ROTATION,
                            "targets_frozen_at_first_departure": None,
                            "target_freeze_step": None,
                        },
                    }
                )
                rows.append(
                    common
                    | {
                        "control": NO_PROACTIVE_ROTATION,
                        "Phi": no_rotation_phi,
                        "source_evidence": evidence
                        | {
                            "controller_name": NO_PROACTIVE_ROTATION,
                            "targets_frozen_at_first_departure": True,
                            "target_freeze_step": 1,
                        },
                    }
                )
    return rows


def _source_intervals_and_support(
    rows: Sequence[Mapping[str, object]],
    *,
    config: RunConfig,
    bootstrap_seed: int,
) -> tuple[dict[str, dict[str, dict[str, float]]], dict[str, object]]:
    expected = (
        config.replicates
        * len(EVALUATION_PROFILES)
        * config.control_episodes
        * len(CONTROL_NAMES)
    )
    if len(rows) != expected:
        raise ValueError("source-screen control row count mismatch")
    paired: dict[tuple[int, str, int], dict[str, Mapping[str, object]]] = {}
    for row in rows:
        replicate = row.get("replicate")
        profile = row.get("profile")
        episode_id = row.get("episode_id")
        control = row.get("control")
        if (
            type(replicate) is not int
            or replicate not in range(config.replicates)
            or profile not in {item.value for item in EVALUATION_PROFILES}
            or type(episode_id) is not int
            or episode_id not in range(config.control_episodes)
            or control not in CONTROL_NAMES
        ):
            raise ValueError("source-screen row key is outside the frozen inventory")
        _finite_number("control Phi", row.get("Phi"))
        if (
            type(row.get("action_path_sha256")) is not str
            or re.fullmatch(r"[0-9a-f]{64}", str(row.get("action_path_sha256")))
            is None
            or type(row.get("queue_uav_steps")) is not int
            or int(row["queue_uav_steps"]) < 0
            or type(row.get("max_queue_length")) is not int
            or int(row["max_queue_length"]) < 0
        ):
            raise ValueError("source action-path/queue evidence is malformed")
        key = (replicate, str(profile), episode_id)
        subjects = paired.setdefault(key, {})
        if str(control) in subjects:
            raise ValueError("source-screen control row is duplicated")
        subjects[str(control)] = row
    if any(
        set(subjects) != set(CONTROL_NAMES)
        or len({str(row.get("ledger_id")) for row in subjects.values()}) != 1
        or len({int(row.get("environment_seed", -1)) for row in subjects.values()}) != 1
        or len(
            {
                json.dumps(row.get("energy_permutation"), sort_keys=True)
                for row in subjects.values()
            }
        )
        != 1
        for subjects in paired.values()
    ):
        raise ValueError("source controls do not share exact physical/random episode ledgers")

    energy_profile_law = True
    control_behavior = True
    no_future_leakage = True
    source_pressure = True

    def projection_audits_pass(evidence: Mapping[str, object]) -> bool:
        audits = evidence.get("projection_audit_history")
        if (
            type(audits) is not list
            or not audits
            or evidence.get("projection_audit_count") != len(audits)
            or evidence.get("all_projection_audits_pass") is not True
            or evidence.get("plan_consistency") is not True
        ):
            return False
        for audit in audits:
            if type(audit) is not dict:
                return False
            candidates = audit.get("candidate_order")
            margins = audit.get("projected_terminal_margins")
            if type(candidates) is not list or type(margins) is not list or len(margins) != 8:
                return False
            expected_candidates = sorted(
                [index for index, margin in enumerate(margins) if float(margin) < 0.0],
                key=lambda index: (float(margins[index]), index),
            )
            if candidates != expected_candidates or not all(
                (
                    audit.get("candidate_order_verified") is True,
                    audit.get("strict_nearest_station_assignment") is True,
                    audit.get("latest_safe_departure_verified") is True,
                    audit.get("current_only_planning") is True,
                )
            ):
                return False
        initial_order = evidence.get("initial_candidate_order")
        return bool(
            initial_order == audits[0]["candidate_order"]
            and evidence.get("initial_source_pressure") is bool(initial_order)
        )

    for (replicate, profile_name, episode_id), subjects in paired.items():
        permutation = subjects[CONSTRUCTIVE_CHARGE_ROTATION].get("energy_permutation")
        ratios = subjects[CONSTRUCTIVE_CHARGE_ROTATION].get("initial_energy_ratios")
        profile = EnergyProfile(profile_name)
        if type(permutation) is not list or type(ratios) is not list:
            energy_profile_law = False
        else:
            try:
                indices = np.asarray(permutation, dtype=np.int64)
                observed = np.asarray(ratios, dtype=np.float64)
                expected_ratios = np.asarray(ENERGY_PROFILE_VALUES[profile])[indices]
                energy_profile_law = energy_profile_law and (
                    indices.shape == (8,)
                    and sorted(indices.tolist()) == list(range(8))
                    and np.array_equal(observed, expected_ratios)
                )
            except (IndexError, TypeError, ValueError):
                energy_profile_law = False
        constructive = subjects[CONSTRUCTIVE_CHARGE_ROTATION].get("source_evidence")
        no_rotation = subjects[NO_PROACTIVE_ROTATION].get("source_evidence")
        if type(constructive) is not dict or type(no_rotation) is not dict:
            control_behavior = False
            no_future_leakage = False
            source_pressure = False
            continue
        candidates = constructive.get("candidate_order")
        margins = constructive.get("projected_terminal_margins")
        candidate_order_exact = False
        if type(candidates) is list and type(margins) is list and len(margins) == 8:
            expected_candidates = sorted(
                [index for index, margin in enumerate(margins) if float(margin) < 0.0],
                key=lambda index: (float(margins[index]), index),
            )
            candidate_order_exact = candidates == expected_candidates
        constructive_behavior = all(
            (
                constructive.get("controller_name") == CONSTRUCTIVE_CHARGE_ROTATION,
                constructive.get("candidate_iff_negative_terminal_margin") is True,
                candidate_order_exact,
                constructive.get("strict_nearest_station_assignment") is True,
                constructive.get("latest_safe_departure_verified") is True,
                constructive.get("common_actions_before_first_departure") is True,
                constructive.get("reallocation_after_every_leave_rejoin") is True,
                constructive.get("lifecycle_boundary_steps")
                == constructive.get("reallocation_event_steps"),
                projection_audits_pass(constructive),
                constructive.get("physical_consistency") is True,
            )
        )
        freeze_step = no_rotation.get("target_freeze_step")
        first_departure = no_rotation.get("first_departure_step")
        no_rotation_behavior = all(
            (
                no_rotation.get("controller_name") == NO_PROACTIVE_ROTATION,
                no_rotation.get("common_actions_before_first_departure") is True,
                no_rotation.get("targets_frozen_at_first_departure") is True,
                type(freeze_step) is int,
                freeze_step == first_departure,
                projection_audits_pass(no_rotation),
                no_rotation.get("physical_consistency") is True,
            )
        )
        control_behavior = control_behavior and constructive_behavior and no_rotation_behavior
        no_future_leakage = no_future_leakage and all(
            evidence.get("current_only_planning") is True
            and evidence.get("future_user_channel_queue_policy_rng_used") is False
            for evidence in (constructive, no_rotation)
        )
        source_pressure = source_pressure and (
            constructive.get("initial_source_pressure") is True
        )

    intervals: dict[str, dict[str, dict[str, float]]] = {}
    for profile_index, profile in enumerate(EVALUATION_PROFILES):
        constructive = np.empty(
            (config.replicates, 1, config.control_episodes), dtype=np.float64
        )
        contrast = np.empty_like(constructive)
        for replicate in range(config.replicates):
            for episode_id in range(config.control_episodes):
                subjects = paired[(replicate, profile.value, episode_id)]
                constructive_value = float(subjects[CONSTRUCTIVE_CHARGE_ROTATION]["Phi"])
                no_rotation_value = float(subjects[NO_PROACTIVE_ROTATION]["Phi"])
                constructive[replicate, 0, episode_id] = constructive_value
                contrast[replicate, 0, episode_id] = constructive_value - no_rotation_value
        intervals[profile.value] = {
            "constructive_phi": hierarchical_paired_interval(
                constructive,
                resamples=config.bootstrap_resamples,
                seed=bootstrap_seed + profile_index * 2,
            ),
            "constructive_minus_no_rotation": hierarchical_paired_interval(
                contrast,
                resamples=config.bootstrap_resamples,
                seed=bootstrap_seed + profile_index * 2 + 1,
            ),
        }

    constructive_rows = [
        row for row in rows if row["control"] == CONSTRUCTIVE_CHARGE_ROTATION
    ]
    no_rotation_rows = [
        row for row in rows if row["control"] == NO_PROACTIVE_ROTATION
    ]
    support: dict[str, object] = {
        "constructive_cutoff_events": sum(int(row.get("cutoff_events", -1)) for row in constructive_rows),
        "constructive_depletion_events": sum(int(row.get("depletion_events", -1)) for row in constructive_rows),
        "constructive_positive_return_cost_rows": sum(
            int(row.get("positive_return_cost_rows", -1)) for row in constructive_rows
        ),
        "late_rejoin_count": sum(
            int(row.get("latest_rejoin_step", HORIZON + 1)) > REJOIN_LATEST_STEP
            for row in constructive_rows
        ),
        "episodes_without_station_use": sum(
            row.get("station_used") is not True for row in constructive_rows
        ),
        "physical_consistency": all(
            row.get("physical_consistency") is True for row in constructive_rows
        ),
        "energy_profile_law": energy_profile_law,
        "control_behavior": control_behavior,
        "no_future_leakage": no_future_leakage,
        "source_pressure": source_pressure,
    }
    cycle_keys = {
        EnergyProfile.IID: "iid_complete_cycles_per_replicate",
        EnergyProfile.LOW_ENERGY: "low_energy_complete_cycles_per_replicate",
        EnergyProfile.SYNCHRONIZED_PRESSURE: "synchronized_pressure_complete_cycles_per_replicate",
    }
    for profile, name in cycle_keys.items():
        support[name] = [
            sum(
                int(row.get("complete_cycles", -1))
                for row in constructive_rows
                if row["profile"] == profile.value and row["replicate"] == replicate
            )
            for replicate in range(config.replicates)
        ]
    support["synchronized_concurrent_episode_counts"] = [
        sum(
            int(row.get("max_concurrent_absent", -1)) >= 2
            for row in constructive_rows
            if row["profile"] == EnergyProfile.SYNCHRONIZED_PRESSURE.value
            and row["replicate"] == replicate
        )
        for replicate in range(config.replicates)
    ]
    support["no_rotation_pressure_counts"] = {
        profile.value: [
            sum(
                row.get("pressure_event") is True
                for row in no_rotation_rows
                if row["profile"] == profile.value and row["replicate"] == replicate
            )
            for replicate in range(config.replicates)
        ]
        for profile in EVALUATION_PROFILES
    }
    return intervals, support


def _nonformal_source_identifiable(
    intervals: Mapping[str, Mapping[str, Mapping[str, object]]],
    support: Mapping[str, object],
) -> bool:
    performance = all(
        float(intervals[profile.value]["constructive_phi"]["mean"])
        >= CONSTRUCTIVE_FLOOR
        and float(
            intervals[profile.value]["constructive_minus_no_rotation"]["lcb95"]
        )
        > LOAD_BEARING_MARGIN
        for profile in EVALUATION_PROFILES
    )
    return performance and all(
        (
            support.get("constructive_cutoff_events") == 0,
            support.get("constructive_depletion_events") == 0,
            support.get("constructive_positive_return_cost_rows") == 0,
            support.get("late_rejoin_count") == 0,
            support.get("episodes_without_station_use") == 0,
            support.get("physical_consistency") is True,
            support.get("energy_profile_law") is True,
            support.get("control_behavior") is True,
            support.get("no_future_leakage") is True,
            support.get("source_pressure") is True,
        )
    )


def _source_screen_payload(
    launch: Mapping[str, object],
    rows: Sequence[Mapping[str, object]],
    *,
    config: RunConfig,
) -> dict[str, object]:
    intervals, support = _source_intervals_and_support(
        rows,
        config=config,
        bootstrap_seed=int(launch["seed_registry"]["bootstrap"]),
    )
    if launch["formal"]:
        identification = source_identification(intervals, support)
    else:
        diagnostic = _nonformal_source_identifiable(intervals, support)
        identification = {
            "constructive_feasibility_pass": diagnostic,
            "load_bearing_pass": diagnostic,
            "support_pass": diagnostic,
            "source_identifiable": diagnostic,
        }
    return {
        "schema": SOURCE_SCREEN_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": launch["source_commit"],
        "formal": launch["formal"],
        "status": "SOURCE_SCREEN_COMPLETE",
        "config": asdict(config),
        "seed_registry": asdict(SeedRegistry()),
        "row_count": len(rows),
        "metrics": intervals,
        "support": support,
        "identification": identification,
        "source_identifiable": identification["source_identifiable"],
        "conclusion_bearing": bool(launch["formal"]),
    }


def _metric_mapping(metrics: object) -> dict[str, object]:
    if hasattr(metrics, "__dataclass_fields__"):
        return asdict(metrics)
    if type(metrics) is dict:
        return dict(metrics)
    raise ValueError("G2 episode metrics are not serializable")


def _source_metric_row(
    *,
    metrics: object,
    control: str,
    replicate: int,
    profile: EnergyProfile,
    episode_id: int,
    ledger: object,
    evidence: object,
    environment_seed: int,
) -> dict[str, object]:
    value = _metric_mapping(metrics)
    aliases = {
        "Phi": ("phi",),
        "cutoff_events": ("cutoff_events", "new_cutoff_events"),
        "depletion_events": ("depletion_events", "new_depletion_events"),
        "complete_cycles": ("complete_charge_cycles",),
        "station_used": ("station_used", "occupied_station"),
        "max_concurrent_absent": ("max_concurrent_absence",),
        "pressure_event": ("no_charge_pressure",),
        "physical_consistency": ("physical_consistency",),
    }
    normalized: dict[str, object] = {}
    for target, names in aliases.items():
        for name in names:
            if name in value:
                normalized[target] = value[name]
                break
        else:
            raise ValueError(f"G2 source metrics omit {target}")
    normalized["positive_return_cost_rows"] = int(
        _finite_number(
            "mean return-cost burden", value.get("mean_return_cost_burden")
        )
        > 0.0
    )
    normalized["latest_rejoin_step"] = (
        REJOIN_LATEST_STEP
        if value.get("complete_recovery_windows") is True
        else HORIZON + 1
    )
    evidence_value = json.loads(json.dumps(_metric_mapping(evidence), sort_keys=True))
    normalized["source_evidence"] = evidence_value
    normalized["action_path_sha256"] = value.get("action_path_sha256")
    normalized["queue_uav_steps"] = value.get("queue_uav_steps")
    normalized["max_queue_length"] = value.get("max_queue_length")
    normalized["environment_seed"] = int(environment_seed)
    normalized["energy_permutation"] = [
        int(item) for item in np.asarray(ledger.energy_permutation).tolist()
    ]
    normalized["initial_energy_ratios"] = [
        float(item) for item in np.asarray(ledger.initial_energy_ratios).tolist()
    ]
    ledger_id = getattr(ledger, "ledger_id", None)
    if type(ledger_id) is not str or not ledger_id:
        raise ValueError("G2 source ledger omits immutable ledger_id")
    return {
        "schema": EVALUATION_ROW_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "control": control,
        "replicate": replicate,
        "profile": profile.value,
        "episode_id": episode_id,
        "ledger_id": ledger_id,
    } | normalized


def _collect_source_rows(
    *, config: RunConfig, launch: Mapping[str, object]
) -> list[dict[str, object]]:
    """Unjournaled test seam; production source collection is chunked below."""
    rows: list[dict[str, object]] = []
    for replicate in range(config.replicates):
        for profile in EVALUATION_PROFILES:
            for start in range(0, config.control_episodes, config.evaluation_batch_size):
                rows.extend(
                    _collect_source_batch(
                        config=config,
                        replicate=replicate,
                        profile=profile,
                        start=start,
                    )
                )
    return rows


_PRODUCTION_COLLECT_SOURCE_ROWS = _collect_source_rows


def _collect_source_batch(
    *, config: RunConfig, replicate: int, profile: EnergyProfile, start: int
) -> list[dict[str, object]]:
    seeds = _replicate_seeds(replicate)
    episode_ids = tuple(
        range(start, min(start + config.evaluation_batch_size, config.control_episodes))
    )
    ledgers = [
        make_g2_episode_ledger(
            profile,
            episode_id,
            energy_seed=seeds["evaluation_ledger"],
        )
        for episode_id in episode_ids
    ]
    environment_seeds = [seeds["control"] + episode_id for episode_id in episode_ids]
    rows: list[dict[str, object]] = []
    for control in CONTROL_NAMES:
        with PersistentG2VectorEnv(ledgers, environment_seeds) as vector:
            evaluation = evaluate_g2_controller(vector, kind=control)
        for episode_id, ledger, metrics, evidence in zip(
            episode_ids, ledgers, evaluation.metrics, evaluation.evidence
        ):
            rows.append(
                _source_metric_row(
                    metrics=metrics,
                    control=control,
                    replicate=replicate,
                    profile=profile,
                    episode_id=episode_id,
                    ledger=ledger,
                    evidence=evidence,
                    environment_seed=seeds["control"] + episode_id,
                )
            )
    return rows


def _source_chunk_stem(
    *, replicate: int, profile: EnergyProfile, control: str, start: int
) -> str:
    return (
        f"source_chunks/replicate_{replicate:02d}/{profile.value}/{control}/"
        f"batch_{start:04d}"
    )


def _load_source_chunk(
    root: Path,
    *,
    launch: Mapping[str, object],
    config: RunConfig,
    replicate: int,
    profile: EnergyProfile,
    control: str,
    start: int,
) -> tuple[list[dict[str, object]] | None, int]:
    stem = _source_chunk_stem(
        replicate=replicate, profile=profile, control=control, start=start
    )
    binding_path = root / f"{stem}.binding.json"
    attempts = [
        path
        for path in (root / Path(stem).parent).glob(f"{Path(stem).name}.attempt_*.json")
        if re.fullmatch(
            re.escape(Path(stem).name) + r"\.attempt_[0-9]{4}\.json",
            path.name,
        )
    ]
    binding = None
    if binding_path.exists():
        binding = _read_binding_or_truncated(binding_path)
        if binding is None:
            binding_path.unlink()
    if binding is None:
        binding = _recover_attempt_binding(
            root,
            directory=root / Path(stem).parent,
            artifact_pattern=f"{Path(stem).name}.attempt_*.json",
            artifact_name_pattern=(
                re.escape(Path(stem).name) + r"\.attempt_([0-9]{4})\.json"
            ),
            schema=SOURCE_SCREEN_CHUNK_SCHEMA,
        )
        if binding is None:
            return None, len(attempts)
        _write_json_immutable(binding_path, binding)
    artifact = _validate_committed_artifact(
        root, binding, schema=SOURCE_SCREEN_CHUNK_SCHEMA
    )
    payload = _read_json(artifact)
    expected_identity = {
        "schema": SOURCE_SCREEN_CHUNK_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": launch["source_commit"],
        "formal": launch["formal"],
        "config": asdict(config),
        "replicate": replicate,
        "profile": profile.value,
        "control": control,
        "start_episode": start,
        "episode_count": min(config.evaluation_batch_size, config.control_episodes - start),
    }
    if any(payload.get(key) != value for key, value in expected_identity.items()):
        raise ValueError("source-screen chunk identity mismatch")
    rows = payload.get("rows")
    if type(rows) is not list or len(rows) != expected_identity["episode_count"]:
        raise ValueError("source-screen chunk row inventory mismatch")
    for offset, row in enumerate(rows):
        if (
            type(row) is not dict
            or row.get("replicate") != replicate
            or row.get("profile") != profile.value
            or row.get("control") != control
            or row.get("episode_id") != start + offset
        ):
            raise ValueError("source-screen chunk contains a misdirected row")
    return [dict(row) for row in rows], max(0, len(attempts) - 1)


def _commit_source_chunk(
    root: Path,
    *,
    launch: Mapping[str, object],
    config: RunConfig,
    replicate: int,
    profile: EnergyProfile,
    control: str,
    start: int,
    rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    stem = _source_chunk_stem(
        replicate=replicate, profile=profile, control=control, start=start
    )
    directory = root / Path(stem).parent
    directory.mkdir(parents=True, exist_ok=True)
    attempt = len(
        [
            path
            for path in directory.glob(f"{Path(stem).name}.attempt_*.json")
            if re.fullmatch(
                re.escape(Path(stem).name) + r"\.attempt_[0-9]{4}\.json",
                path.name,
            )
        ]
    )
    reference = f"{stem}.attempt_{attempt:04d}.json"
    payload = {
        "schema": SOURCE_SCREEN_CHUNK_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": launch["source_commit"],
        "formal": launch["formal"],
        "config": asdict(config),
        "replicate": replicate,
        "profile": profile.value,
        "control": control,
        "start_episode": start,
        "episode_count": min(config.evaluation_batch_size, config.control_episodes - start),
        "rows": list(rows),
    }
    _write_json_immutable(root / reference, payload)
    binding = _commit_artifact(root, reference, SOURCE_SCREEN_CHUNK_SCHEMA)
    _write_json_immutable(root / f"{stem}.binding.json", binding)
    return [dict(row) for row in rows]


def _after_source_chunk_commit(
    *, replicate: int, profile: str, control: str, start_episode: int
) -> None:
    """Focused-test interruption seam; production deliberately does nothing."""


def _run_source_screen(
    root: Path, *, launch: Mapping[str, object], config: RunConfig
) -> tuple[dict[str, object], dict[str, str]]:
    binding_path = root / "source_screen.binding.json"
    _terminal_binding(
        root,
        binding_path,
        reference="source_screen.json",
        schema=SOURCE_SCREEN_SCHEMA,
    )
    if any((root / name).exists() for name in ("checkpoints", "resume", "train_manifest.json")):
        raise ValueError("learned artifacts exist before the source screen")
    injected_rows = (
        _collect_source_rows(config=config, launch=launch)
        if _collect_source_rows is not _PRODUCTION_COLLECT_SOURCE_ROWS
        else None
    )
    rows: list[dict[str, object]] = []
    for replicate in range(config.replicates):
        for profile in EVALUATION_PROFILES:
            for start in range(0, config.control_episodes, config.evaluation_batch_size):
                cached: dict[str, list[dict[str, object]] | None] = {}
                for control in CONTROL_NAMES:
                    cached[control], _ignored = _load_source_chunk(
                        root,
                        launch=launch,
                        config=config,
                        replicate=replicate,
                        profile=profile,
                        control=control,
                        start=start,
                    )
                missing = [control for control in CONTROL_NAMES if cached[control] is None]
                if missing:
                    if injected_rows is not None:
                        collected = [
                            dict(row)
                            for row in injected_rows
                            if row.get("replicate") == replicate
                            and row.get("profile") == profile.value
                            and type(row.get("episode_id")) is int
                            and start <= int(row["episode_id"])
                            < min(start + config.evaluation_batch_size, config.control_episodes)
                        ]
                    else:
                        collected = _collect_source_batch(
                            config=config,
                            replicate=replicate,
                            profile=profile,
                            start=start,
                        )
                    for control in missing:
                        control_rows = [
                            row for row in collected if row.get("control") == control
                        ]
                        cached[control] = _commit_source_chunk(
                            root,
                            launch=launch,
                            config=config,
                            replicate=replicate,
                            profile=profile,
                            control=control,
                            start=start,
                            rows=control_rows,
                        )
                        _after_source_chunk_commit(
                            replicate=replicate,
                            profile=profile.value,
                            control=control,
                            start_episode=start,
                        )
                for control in CONTROL_NAMES:
                    assert cached[control] is not None
                    rows.extend(cached[control])
    rows.sort(
        key=lambda row: (
            int(row["replicate"]),
            tuple(item.value for item in EVALUATION_PROFILES).index(str(row["profile"])),
            int(row["episode_id"]),
            CONTROL_NAMES.index(str(row["control"])),
        )
    )
    payload = _source_screen_payload(launch, rows, config=config)
    if binding_path.exists():
        binding = _read_json(binding_path)
        artifact = _validate_committed_artifact(root, binding, schema=SOURCE_SCREEN_SCHEMA)
        actual = _read_json(artifact)
        rows_binding = actual.get("rows")
        if type(rows_binding) is not dict:
            raise ValueError("source-screen terminal row binding is missing")
        expected = dict(payload)
        expected["rows"] = rows_binding
        if actual != expected:
            raise ValueError("source-screen terminal evidence differs from chunk assembly")
        return actual, dict(binding)
    rows_path = root / "source_screen_rows.jsonl"
    rows_binding = _recover_binding(
        root, "source_screen_rows.jsonl", schema=SOURCE_SCREEN_CHUNK_SCHEMA
    )
    if rows_binding is None:
        _write_jsonl(rows_path, rows)
        rows_binding = _commit_artifact(
            root, "source_screen_rows.jsonl", SOURCE_SCREEN_CHUNK_SCHEMA
        )
    elif _read_jsonl(rows_path) != rows:
        raise ValueError("committed source terminal rows differ from chunk assembly")
    payload["rows"] = rows_binding
    artifact = root / "source_screen.json"
    if artifact.exists():
        artifact.unlink()
    _write_json_immutable(artifact, payload)
    binding = _commit_artifact(root, "source_screen.json", SOURCE_SCREEN_SCHEMA)
    _write_json_immutable(binding_path, binding)
    return payload, binding


def _learned_arrays(
    rows: Sequence[Mapping[str, object]], config: RunConfig
) -> dict[str, dict[str, np.ndarray]]:
    expected = (
        len(ARM_NAMES)
        * config.replicates
        * len(STRATA)
        * config.evaluation_episodes
    )
    if len(rows) != expected:
        raise ValueError("learned evaluation row count mismatch")
    shape = (config.replicates, len(STRATA), config.evaluation_episodes)
    names = (
        "J_event",
        "J_rejoin",
        "Q_ordinary",
        "catastrophe_episode",
        "return_cost_burden",
    )
    arrays = {
        arm: {name: np.full(shape, np.nan, dtype=np.float64) for name in names}
        for arm in ARM_NAMES
    }
    seen: set[tuple[str, int, str, str, int]] = set()
    paired_identity: dict[
        tuple[int, str, str, int], dict[str, tuple[object, object]]
    ] = {}
    stratum_index = {stratum: index for index, stratum in enumerate(STRATA)}
    for row in rows:
        arm = row.get("arm")
        replicate = row.get("replicate")
        profile = row.get("profile")
        mode = row.get("action_mode")
        episode_id = row.get("episode_id")
        key = (str(arm), int(replicate), str(profile), str(mode), int(episode_id)) if all(
            type(value) is int for value in (replicate, episode_id)
        ) else None
        if (
            arm not in ARM_NAMES
            or type(replicate) is not int
            or replicate not in range(config.replicates)
            or (profile, mode) not in stratum_index
            or type(episode_id) is not int
            or episode_id not in range(config.evaluation_episodes)
            or key in seen
        ):
            raise ValueError("learned evaluation key is malformed or duplicated")
        seen.add(key)
        if (
            row.get("deterministic") is not (mode == "deterministic")
            or row.get("action_seed")
            != _replicate_seeds(replicate)["evaluation_action"]
        ):
            raise ValueError("evaluation action-mode/seed evidence mismatch")
        pair_key = (replicate, str(profile), str(mode), episode_id)
        arm_identity = paired_identity.setdefault(pair_key, {})
        arm_identity[str(arm)] = (row.get("ledger_id"), row.get("action_seed"))
        index = (replicate, stratum_index[(str(profile), str(mode))], episode_id)
        for name in names:
            value = row.get(name)
            if name == "J_rejoin" and value is None:
                continue
            arrays[str(arm)][name][index] = _finite_number(name, value)
    for arm in ARM_NAMES:
        for name in names:
            if name != "J_rejoin" and not np.all(np.isfinite(arrays[arm][name])):
                raise ValueError("learned evaluation metric inventory is incomplete")
    if any(
        set(arms) != set(ARM_NAMES) or len(set(arms.values())) != 1
        for arms in paired_identity.values()
    ):
        raise ValueError("paired learned arms do not share ledger/action RNG identity")
    return arrays


def learned_intervals(
    rows: Sequence[Mapping[str, object]],
    *,
    config: RunConfig,
    seed: int,
) -> dict[str, object]:
    arrays = _learned_arrays(rows, config)
    replicates = config.replicates
    episodes = config.evaluation_episodes
    rng = np.random.default_rng(int(seed))
    replicate_draws = rng.integers(
        0, replicates, size=(config.bootstrap_resamples, replicates)
    )
    episode_draws = rng.integers(
        0,
        episodes,
        size=(config.bootstrap_resamples, replicates, episodes),
    )

    def draw_selected(array: np.ndarray, draw_index: int) -> np.ndarray:
        return np.stack(
            [
                    array[int(replicate)][:, episode_draws[draw_index, slot]]
                for slot, replicate in enumerate(replicate_draws[draw_index])
            ]
        )

    access_draws = {
        arm: np.empty(config.bootstrap_resamples, dtype=np.float64)
        for arm in ARM_NAMES
    }
    safety_draws = {
        arm: {
            key: {
                "catastrophe_fraction": np.empty(config.bootstrap_resamples),
                "return_cost_burden": np.empty(config.bootstrap_resamples),
            }
            for key in STRATUM_KEYS
        }
        for arm in ARM_NAMES
    }
    gain_draws = {
        name: np.empty(config.bootstrap_resamples, dtype=np.float64)
        for name in ("g_svc", "g_rejoin", "g_ordinary")
    }
    heldout = np.array(
        [profile != EnergyProfile.IID.value for profile, _mode in STRATA],
        dtype=np.bool_,
    )
    comparisons_complete = all(
        np.all(np.isfinite(arrays[arm]["J_rejoin"][:, heldout])) for arm in ARM_NAMES
    )
    for draw_index in range(config.bootstrap_resamples):
        selected = {
            arm: {
                name: draw_selected(array, draw_index)
                for name, array in metrics.items()
            }
            for arm, metrics in arrays.items()
        }
        for arm in ARM_NAMES:
            event_cell = selected[arm]["J_event"].mean(axis=(0, 2))
            ordinary_cell = selected[arm]["Q_ordinary"].mean(axis=(0, 2))
            access_draws[arm][draw_index] = float(
                np.min(
                    np.minimum(
                        event_cell / EVENT_ACCESS_FLOOR,
                        ordinary_cell / ORDINARY_ACCESS_FLOOR,
                    )
                )
            )
            for stratum, key in enumerate(STRATUM_KEYS):
                safety_draws[arm][key]["catastrophe_fraction"][draw_index] = float(
                    selected[arm]["catastrophe_episode"][:, stratum].mean()
                )
                safety_draws[arm][key]["return_cost_burden"][draw_index] = float(
                    selected[arm]["return_cost_burden"][:, stratum].mean()
                )
        fixed = selected[FIXED_MASK_REC]
        opened = selected[PREFIX_NORMALIZED_OPEN_ROSTER]
        gain_draws["g_svc"][draw_index] = float(
            (opened["J_event"][:, heldout] - fixed["J_event"][:, heldout]).mean()
        )
        gain_draws["g_ordinary"][draw_index] = float(
            (
                opened["Q_ordinary"][:, heldout]
                - fixed["Q_ordinary"][:, heldout]
            ).mean()
        )
        gain_draws["g_rejoin"][draw_index] = (
            float(
                (
                    opened["J_rejoin"][:, heldout]
                    - fixed["J_rejoin"][:, heldout]
                ).mean()
            )
            if comparisons_complete
            else np.nan
        )

    access: dict[str, dict[str, float]] = {}
    safety: dict[str, dict[str, dict[str, dict[str, float]]]] = {}
    for arm in ARM_NAMES:
        event_point = arrays[arm]["J_event"].mean(axis=(0, 2))
        ordinary_point = arrays[arm]["Q_ordinary"].mean(axis=(0, 2))
        point = float(
            np.min(
                np.minimum(
                    event_point / EVENT_ACCESS_FLOOR,
                    ordinary_point / ORDINARY_ACCESS_FLOOR,
                )
            )
        )
        access[arm] = _interval(access_draws[arm], point)
        safety[arm] = {}
        for stratum, key in enumerate(STRATUM_KEYS):
            safety[arm][key] = {
                name: _interval(
                    draws,
                    float(arrays[arm][metric][:, stratum].mean()),
                )
                for name, metric, draws in (
                    (
                        "catastrophe_fraction",
                        "catastrophe_episode",
                        safety_draws[arm][key]["catastrophe_fraction"],
                    ),
                    (
                        "return_cost_burden",
                        "return_cost_burden",
                        safety_draws[arm][key]["return_cost_burden"],
                    ),
                )
            }
    gains: dict[str, object] = {
        "g_svc": _interval(
            gain_draws["g_svc"],
            float(
                (
                    arrays[PREFIX_NORMALIZED_OPEN_ROSTER]["J_event"][:, heldout]
                    - arrays[FIXED_MASK_REC]["J_event"][:, heldout]
                ).mean()
            ),
        ),
        "g_ordinary": _interval(
            gain_draws["g_ordinary"],
            float(
                (
                    arrays[PREFIX_NORMALIZED_OPEN_ROSTER]["Q_ordinary"][:, heldout]
                    - arrays[FIXED_MASK_REC]["Q_ordinary"][:, heldout]
                ).mean()
            ),
        ),
    }
    gains["g_rejoin"] = (
        _interval(
            gain_draws["g_rejoin"],
            float(
                (
                    arrays[PREFIX_NORMALIZED_OPEN_ROSTER]["J_rejoin"][:, heldout]
                    - arrays[FIXED_MASK_REC]["J_rejoin"][:, heldout]
                ).mean()
            ),
        )
        if comparisons_complete
        else {"complete": False}
    )
    return {
        "access": access,
        "safety": safety,
        "gains": gains,
        "comparisons_complete": comparisons_complete,
    }


def _analysis_from_evaluation(
    evaluation: Mapping[str, object], *, config: RunConfig
) -> dict[str, object]:
    operational_valid = evaluation.get("operational_valid") is True
    source_identifiable_value = evaluation.get("source_identifiable") is True
    if evaluation.get("formal") is not True:
        return {
            "schema": ANALYSIS_SCHEMA,
            "source_family": SOURCE_FAMILY,
            "source_commit": evaluation["source_commit"],
            "formal": False,
            "operational_valid": operational_valid,
            "source_identifiable": source_identifiable_value,
            "learned_gates_evaluated": bool(evaluation.get("learned_rows")),
            "result": NONFORMAL_RESULT if operational_valid else INVALID_RESULT,
            "predicate_inputs": None,
            "conclusion_bearing": False,
        }
    if not operational_valid or not source_identifiable_value:
        predicates = {
            "operational_valid": operational_valid,
            "source_identifiable": source_identifiable_value,
            "fixed_access_pass": False,
            "fixed_access_fail": False,
            "open_access_pass": False,
            "open_access_fail": False,
        }
        return {
            "schema": ANALYSIS_SCHEMA,
            "source_family": SOURCE_FAMILY,
            "source_commit": evaluation["source_commit"],
            "formal": True,
            "operational_valid": operational_valid,
            "source_identifiable": source_identifiable_value,
            "learned_gates_evaluated": False,
            "result": select_result_branch(predicates),
            "predicate_inputs": predicates,
            "conclusion_bearing": True,
        }
    rows_reference = evaluation.get("learned_rows")
    if type(rows_reference) is not dict:
        raise ValueError("source-valid formal evaluation omits learned rows")
    rows = evaluation["_learned_rows_value"]
    intervals = learned_intervals(
        rows,
        config=config,
        seed=int(evaluation["seed_registry"]["bootstrap"]),
    )
    fixed = classify_arm_access(
        intervals["access"][FIXED_MASK_REC], intervals["safety"][FIXED_MASK_REC]
    )
    opened = classify_arm_access(
        intervals["access"][PREFIX_NORMALIZED_OPEN_ROSTER],
        intervals["safety"][PREFIX_NORMALIZED_OPEN_ROSTER],
    )
    gains = intervals["gains"]
    complete = intervals["comparisons_complete"] is True
    predicates: dict[str, object] = {
        "operational_valid": True,
        "source_identifiable": True,
        "fixed_access_pass": fixed["access_pass"],
        "fixed_access_fail": fixed["access_fail"],
        "open_access_pass": opened["access_pass"],
        "open_access_fail": opened["access_fail"],
        "comparisons_complete": complete,
    }
    if complete:
        predicates |= {
            "g_svc_lcb": gains["g_svc"]["lcb95"],
            "g_svc_ucb": gains["g_svc"]["ucb95"],
            "g_rejoin_lcb": gains["g_rejoin"]["lcb95"],
            "g_rejoin_ucb": gains["g_rejoin"]["ucb95"],
            "g_ordinary_lcb": gains["g_ordinary"]["lcb95"],
        }
    return {
        "schema": ANALYSIS_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": evaluation["source_commit"],
        "formal": True,
        "operational_valid": True,
        "source_identifiable": True,
        "learned_gates_evaluated": True,
        "intervals": intervals,
        "arm_classification": {
            FIXED_MASK_REC: fixed,
            PREFIX_NORMALIZED_OPEN_ROSTER: opened,
        },
        "predicate_inputs": predicates,
        "result": select_result_branch(predicates),
        "conclusion_bearing": True,
    }


def _torch_save_immutable(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        torch.save(dict(payload), handle)


def _torch_load(path: Path) -> dict[str, object]:
    value = torch.load(path, map_location="cpu", weights_only=False)
    if type(value) is not dict:
        raise ValueError("checkpoint payload must be one mapping")
    return value


def _checkpoint_reference(replicate: int, arm: str) -> str:
    if arm not in ARM_NAMES:
        raise ValueError("unknown G2 arm")
    return f"checkpoints/replicate_{replicate:02d}/{arm}/update_0128.pt"


def _resume_base(replicate: int, arm: str, completed_updates: int) -> str:
    return f"resume/replicate_{replicate:02d}/{arm}/update_{completed_updates:04d}"


def _save_resume(
    root: Path,
    *,
    replicate: int,
    arm: str,
    completed_updates: int,
    model: MatchedChargeRotationPolicy,
    optimizer: torch.optim.Optimizer,
    seeds: Mapping[str, int],
    num_envs: int,
    cumulative: Mapping[str, object],
) -> None:
    base = _resume_base(replicate, arm, completed_updates)
    directory = root / Path(base).parent
    directory.mkdir(parents=True, exist_ok=True)
    attempts = [
        path
        for path in directory.glob(f"{Path(base).name}.attempt_*.pt")
        if re.fullmatch(
            re.escape(Path(base).name) + r"\.attempt_[0-9]{4}\.pt", path.name
        )
    ]
    attempt = len(attempts)
    attempt_base = f"{base}.attempt_{attempt:04d}"
    checkpoint_reference = f"{attempt_base}.pt"
    metadata_reference = f"{attempt_base}.json"
    marker_reference = f"{attempt_base}.complete.json"
    payload = g2_checkpoint_state(
        model=model,
        optimizer=optimizer,
        completed_updates=completed_updates,
        next_episode_id=completed_updates * num_envs,
        seed_contract=seeds,
    )
    payload["python_rng_state"] = random.getstate()
    payload["numpy_rng_state"] = np.random.get_state()
    payload["runner_cumulative"] = dict(cumulative)
    _torch_save_immutable(root / checkpoint_reference, payload)
    metadata = {
        "schema": RESUME_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "replicate": replicate,
        "arm": arm,
        "completed_updates": completed_updates,
        "checkpoint_reference": checkpoint_reference,
        "checkpoint_sha256": _sha256_file(root / checkpoint_reference),
        "seed_contract": dict(seeds),
    }
    _write_json_immutable(root / metadata_reference, metadata)
    marker = {
        "schema": COMMIT_SCHEMA,
        "artifact_schema": RESUME_SCHEMA,
        "artifact_reference": metadata_reference,
        "artifact_sha256": _sha256_file(root / metadata_reference),
        "checkpoint_reference": checkpoint_reference,
        "checkpoint_sha256": metadata["checkpoint_sha256"],
    }
    _write_json_immutable(root / marker_reference, marker)


def _after_resume_commit(
    *, replicate: int, arm: str, completed_updates: int
) -> None:
    """Focused-test interruption seam; production deliberately does nothing."""


def _latest_resume(
    root: Path, *, replicate: int, arm: str, seeds: Mapping[str, int]
) -> tuple[dict[str, object] | None, int]:
    directory = root / f"resume/replicate_{replicate:02d}/{arm}"
    if not directory.exists():
        return None, 0
    if not directory.is_dir():
        raise ValueError("resume path is not a directory")
    ignored = 0
    candidates: list[tuple[int, int, dict[str, object]]] = []
    committed_files: set[str] = set()
    parse_ignored_files: set[str] = set()
    for marker_path in directory.glob("update_*.attempt_*.complete.json"):
        try:
            marker = _read_json(marker_path)
        except (json.JSONDecodeError, UnicodeError):
            ignored += 1
            parse_ignored_files.add(marker_path.name)
            continue
        match = re.fullmatch(
            r"update_([0-9]{4})\.attempt_([0-9]{4})\.complete\.json",
            marker_path.name,
        )
        if match is None:
            raise ValueError("resume completion marker has an invalid name")
        completed = int(match.group(1))
        attempt = int(match.group(2))
        attempt_base = f"{_resume_base(replicate, arm, completed)}.attempt_{attempt:04d}"
        metadata_reference = f"{attempt_base}.json"
        checkpoint_reference = f"{attempt_base}.pt"
        metadata_path = root / metadata_reference
        checkpoint_path = root / checkpoint_reference
        if marker != {
            "schema": COMMIT_SCHEMA,
            "artifact_schema": RESUME_SCHEMA,
            "artifact_reference": metadata_reference,
            "artifact_sha256": marker.get("artifact_sha256"),
            "checkpoint_reference": checkpoint_reference,
            "checkpoint_sha256": marker.get("checkpoint_sha256"),
        }:
            raise ValueError("resume completion marker is malformed")
        if (
            not metadata_path.is_file()
            or not checkpoint_path.is_file()
            or _sha256_file(metadata_path) != marker["artifact_sha256"]
            or _sha256_file(checkpoint_path) != marker["checkpoint_sha256"]
        ):
            raise ValueError("resume completion marker is malformed")
        metadata = _read_json(metadata_path)
        if metadata != {
            "schema": RESUME_SCHEMA,
            "source_family": SOURCE_FAMILY,
            "replicate": replicate,
            "arm": arm,
            "completed_updates": completed,
            "checkpoint_reference": checkpoint_reference,
            "checkpoint_sha256": marker["checkpoint_sha256"],
            "seed_contract": dict(seeds),
        }:
            raise ValueError("resume metadata identity mismatch")
        candidates.append((completed, attempt, metadata))
        committed_files.update(
            {
                Path(checkpoint_reference).name,
                Path(metadata_reference).name,
                marker_path.name,
            }
        )
    ignored += sum(
        path.name not in committed_files and path.name not in parse_ignored_files
        for path in directory.iterdir()
    )
    return (
        max(candidates, key=lambda row: (row[0], row[1]))[2]
        if candidates
        else None
    ), ignored


def _restore_resume(
    root: Path,
    metadata: Mapping[str, object],
    *,
    model: MatchedChargeRotationPolicy,
    optimizer: torch.optim.Optimizer,
    seeds: Mapping[str, int],
) -> tuple[int, dict[str, object]]:
    payload = _torch_load(root / str(metadata["checkpoint_reference"]))
    restored = load_g2_checkpoint_state(
        payload,
        model=model,
        optimizer=optimizer,
        expected_seed_contract=seeds,
    )
    random.setstate(payload["python_rng_state"])
    np.random.set_state(payload["numpy_rng_state"])
    completed = int(restored["completed_updates"])
    if completed != int(metadata["completed_updates"]):
        raise ValueError("resume checkpoint and metadata update counts differ")
    cumulative = payload.get("runner_cumulative")
    if type(cumulative) is not dict:
        raise ValueError("resume checkpoint omits cumulative runner audit")
    return completed, dict(cumulative)


def _ensure_final_checkpoint(
    root: Path,
    *,
    replicate: int,
    arm: str,
    config: RunConfig,
    model: MatchedChargeRotationPolicy,
    optimizer: torch.optim.Optimizer,
    seeds: Mapping[str, int],
    cumulative: Mapping[str, object],
) -> dict[str, object]:
    reference = _checkpoint_reference(replicate, arm)
    if config.updates != 128:
        reference = f"checkpoints/replicate_{replicate:02d}/{arm}/update_{config.updates:04d}.pt"
    marker_reference = f"{reference}.complete.json"
    if (root / marker_reference).exists():
        try:
            marker = _read_json(root / marker_reference)
        except (json.JSONDecodeError, UnicodeError):
            (root / marker_reference).unlink()
            if (root / reference).exists():
                (root / reference).unlink()
            marker = None
        if marker is None:
            pass
        else:
            checkpoint = {
                "replicate": replicate,
                "arm": arm,
                "reference": reference,
                "complete_reference": marker_reference,
                "sha256": marker.get("artifact_sha256"),
                "completed_updates": config.updates,
            }
            _checkpoint_payload(root, checkpoint, config=config)
            return checkpoint
    if (root / reference).exists():
        (root / reference).unlink()
    payload = g2_checkpoint_state(
        model=model,
        optimizer=optimizer,
        completed_updates=config.updates,
        next_episode_id=config.updates * config.num_envs,
        seed_contract=seeds,
    )
    payload["python_rng_state"] = random.getstate()
    payload["numpy_rng_state"] = np.random.get_state()
    payload["runner_cumulative"] = dict(cumulative)
    _torch_save_immutable(root / reference, payload)
    digest = _sha256_file(root / reference)
    _write_json_immutable(
        root / marker_reference,
        {
            "schema": COMMIT_SCHEMA,
            "artifact_schema": CHECKPOINT_SCHEMA,
            "artifact_reference": reference,
            "artifact_sha256": digest,
            "replicate": replicate,
            "arm": arm,
            "completed_updates": config.updates,
        },
    )
    return {
        "replicate": replicate,
        "arm": arm,
        "reference": reference,
        "complete_reference": marker_reference,
        "sha256": digest,
        "completed_updates": config.updates,
    }


def _paired_model_spec(config: RunConfig, seeds: Mapping[str, int]) -> dict[str, int]:
    ledger = make_g2_episode_ledger(
        EnergyProfile.IID, 0, energy_seed=seeds["training_ledger"]
    )
    environment = make_g2_environment(ledger, seeds["training_environment"])
    try:
        environment.reset()
        view = environment.current_view()
        return {
            "observation_dim": int(view.observations.shape[-1]),
            "critic_state_dim": int(view.critic_state.size),
        }
    finally:
        environment.close()


def _empty_training_cumulative() -> dict[str, object]:
    return {
        "finite_updates": True,
        "active_tokens": 0,
        "maximum_gradient_norm": 0.0,
        "maximum_errors": {
            name: 0.0
            for name in (
                "logp_max_error",
                "joint_logp_max_error",
                "value_max_error",
                "hidden_max_error",
                "prefix_max_error",
                "inactive_logp_max_abs",
                "inactive_action_max_abs",
                "inactive_hidden_change_max_abs",
            )
        },
    }


def _trajectory_audit(trajectory: object) -> dict[str, float]:
    inactive = ~trajectory.active_mask
    inactive_action = torch.where(
        inactive.unsqueeze(-1), trajectory.actions, 0.0
    ).abs()
    inactive_logp = torch.where(inactive, trajectory.old_log_probs, 0.0).abs()
    hidden_delta = torch.where(
        inactive.unsqueeze(-1),
        trajectory.hidden_after - trajectory.hidden_before,
        0.0,
    ).abs()
    return {
        "inactive_action_max_abs": float(inactive_action.max()),
        "inactive_logp_max_abs": float(inactive_logp.max()),
        "inactive_hidden_change_max_abs": float(hidden_delta.max()),
    }


def train_run(
    root: Path,
    *,
    source_commit: str,
    formal: bool,
    authorization_token: str | None = None,
    config: RunConfig | None = None,
) -> Path:
    root = Path(root)
    chosen = FORMAL_CONFIG if formal else (config or EXERCISE_CONFIG)
    _validate_launch(formal=formal, authorization_token=authorization_token, config=chosen)
    source_commit = _validate_source_commit(source_commit, formal=formal)
    configure_runtime(SeedRegistry().model_initialization)
    launch = _launch_identity(
        source_commit=source_commit,
        formal=formal,
        authorization_token=authorization_token,
        config=chosen,
    )
    root_preexisted = _open_launch(root, launch)
    terminal_binding_path = root / "train_manifest.binding.json"
    _terminal_binding(
        root,
        terminal_binding_path,
        reference="train_manifest.json",
        schema=RUN_SCHEMA,
    )
    if terminal_binding_path.exists():
        binding = _read_json(terminal_binding_path)
        artifact = _validate_committed_artifact(root, binding, schema=RUN_SCHEMA)
        manifest = _read_json(artifact)
        if manifest.get("source_commit") != source_commit or manifest.get("config") != asdict(chosen):
            raise ValueError("terminal training manifest conflicts with launch identity")
        return artifact

    if formal:
        screen, screen_binding = _run_source_screen(root, launch=launch, config=chosen)
    else:
        try:
            existing_screen_binding = root / "source_screen.binding.json"
            recovered_screen_binding = _terminal_binding(
                root,
                existing_screen_binding,
                reference="source_screen.json",
                schema=SOURCE_SCREEN_SCHEMA,
            )
            if recovered_screen_binding is not None:
                screen_binding = recovered_screen_binding
                screen_path = _validate_committed_artifact(
                    root, screen_binding, schema=SOURCE_SCREEN_SCHEMA
                )
                screen = _read_json(screen_path)
                if (
                    screen.get("source_commit") != source_commit
                    or screen.get("config") != asdict(chosen)
                ):
                    raise ValueError("nonformal source-screen resume identity mismatch")
            elif _collect_source_rows is _PRODUCTION_COLLECT_SOURCE_ROWS:
                rows = synthetic_control_rows(
                    replicates=chosen.replicates,
                    episodes=chosen.control_episodes,
                    constructive_phi=1.0,
                    no_rotation_phi=0.5,
                )
                screen = _source_screen_payload(launch, rows, config=chosen)
                rows_path = root / "source_screen_rows.jsonl"
                _write_jsonl(rows_path, rows)
                screen["rows"] = _commit_artifact(
                    root, "source_screen_rows.jsonl", SOURCE_SCREEN_CHUNK_SCHEMA
                )
                _write_json_immutable(root / "source_screen.json", screen)
                screen_binding = _commit_artifact(
                    root, "source_screen.json", SOURCE_SCREEN_SCHEMA
                )
                _write_json_immutable(root / "source_screen.binding.json", screen_binding)
            else:
                screen, screen_binding = _run_source_screen(root, launch=launch, config=chosen)
        finally:
            pass
    if not bool(screen["source_identifiable"]):
        if (root / "checkpoints").exists() or (root / "resume").exists():
            raise ValueError("failed source screen encountered learned artifacts")
        manifest = {
            "schema": RUN_SCHEMA,
            "source_family": SOURCE_FAMILY,
            "source_commit": source_commit,
            "formal": formal,
            "authorization_token": authorization_token,
            "status": TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE,
            "runtime": _runtime_identity(),
            "config": asdict(chosen),
            "seed_registry": asdict(SeedRegistry()),
            "source_screen": screen_binding,
            "arms": list(ARM_NAMES),
            "training_results": [],
            "checkpoint_references": [],
            "resume_telemetry": {"root_preexisted": root_preexisted},
        }
        _write_json_immutable(root / "train_manifest.json", manifest)
        binding = _commit_artifact(root, "train_manifest.json", RUN_SCHEMA)
        _write_json_immutable(terminal_binding_path, binding)
        return root / "train_manifest.json"

    training_results: list[dict[str, object]] = []
    checkpoint_references: list[dict[str, object]] = []
    for replicate in range(chosen.replicates):
        seeds = _replicate_seeds(replicate)
        spec = _paired_model_spec(chosen, seeds)
        configure_runtime(seeds["model_initialization"])
        fixed_initial = MatchedChargeRotationPolicy(
            spec["observation_dim"], spec["critic_state_dim"], routing_mode=FIXED_MASK_REC
        )
        configure_runtime(seeds["model_initialization"])
        open_initial = MatchedChargeRotationPolicy(
            spec["observation_dim"],
            spec["critic_state_dim"],
            routing_mode=PREFIX_NORMALIZED_OPEN_ROSTER,
        )
        initialization_error = maximum_state_difference(
            model_state_copy(fixed_initial), model_state_copy(open_initial)
        )
        if initialization_error != 0.0 or fixed_initial.parameter_count != open_initial.parameter_count:
            raise ValueError("paired arms do not have exact matched initialization/parameters")
        for arm in ARM_NAMES:
            configure_runtime(seeds["model_initialization"])
            model = MatchedChargeRotationPolicy(
                spec["observation_dim"], spec["critic_state_dim"], routing_mode=arm
            ).to(torch.device("cpu"))
            optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
            marker, ignored = _latest_resume(root, replicate=replicate, arm=arm, seeds=seeds)
            completed = 0
            cumulative = _empty_training_cumulative()
            if marker is not None:
                completed, cumulative = _restore_resume(
                    root, marker, model=model, optimizer=optimizer, seeds=seeds
                )
            metrics: dict[str, float] = {}
            for update in range(completed, chosen.updates):
                episode_ids = tuple(
                    range(update * chosen.num_envs, (update + 1) * chosen.num_envs)
                )
                ledgers = [
                    make_g2_episode_ledger(
                        EnergyProfile.IID,
                        episode_id,
                        energy_seed=seeds["training_ledger"],
                    )
                    for episode_id in episode_ids
                ]
                environment_seeds = [
                    seeds["training_environment"] + episode_id
                    for episode_id in episode_ids
                ]
                with PersistentG2VectorEnv(ledgers, environment_seeds) as vector:
                    trajectory = collect_g2_trajectory(
                        model,
                        vector,
                        episode_ids=episode_ids,
                        action_seed=seeds["training_action"],
                        device=torch.device("cpu"),
                        horizon=chosen.horizon,
                    )
                metrics = optimize_g2_update(
                    model,
                    optimizer,
                    trajectory,
                    device=torch.device("cpu"),
                    ppo_passes=chosen.ppo_passes,
                )
                audit = _trajectory_audit(trajectory)
                cumulative["finite_updates"] = bool(
                    cumulative["finite_updates"]
                    and bool(metrics.get("finite_update", 0.0))
                    and all(np.isfinite(float(value)) for value in metrics.values())
                )
                cumulative["active_tokens"] = int(cumulative["active_tokens"]) + int(
                    trajectory.active_token_count
                )
                cumulative["maximum_gradient_norm"] = max(
                    float(cumulative["maximum_gradient_norm"]),
                    float(metrics.get("gradient_norm", float("inf"))),
                )
                maximum_errors = cumulative["maximum_errors"]
                assert type(maximum_errors) is dict
                for name in maximum_errors:
                    maximum_errors[name] = max(
                        float(maximum_errors[name]),
                        float((metrics | audit).get(name, 0.0)),
                    )
                _save_resume(
                    root,
                    replicate=replicate,
                    arm=arm,
                    completed_updates=update + 1,
                    model=model,
                    optimizer=optimizer,
                    seeds=seeds,
                    num_envs=chosen.num_envs,
                    cumulative=cumulative,
                )
                _after_resume_commit(
                    replicate=replicate, arm=arm, completed_updates=update + 1
                )
            checkpoint = _ensure_final_checkpoint(
                root,
                replicate=replicate,
                arm=arm,
                config=chosen,
                model=model,
                optimizer=optimizer,
                seeds=seeds,
                cumulative=cumulative,
            )
            checkpoint_references.append(checkpoint)
            training_results.append(
                {
                    "replicate": replicate,
                    "arm": arm,
                    "parameter_count": model.parameter_count,
                    "paired_initialization_max_error": initialization_error,
                    "updates": chosen.updates,
                    "optimizer_steps": chosen.updates * chosen.ppo_passes,
                    "environment_transitions": chosen.updates * chosen.num_envs * chosen.horizon,
                    "checkpoint": checkpoint,
                    "last_update_metrics": metrics,
                    "cumulative_audit": cumulative,
                    "ignored_incomplete_resume_fragments": ignored,
                }
            )
    manifest = {
        "schema": RUN_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": source_commit,
        "formal": formal,
        "authorization_token": authorization_token,
        "status": TRAIN_COMPLETE,
        "runtime": _runtime_identity(),
        "config": asdict(chosen),
        "seed_registry": asdict(SeedRegistry()),
        "source_screen": screen_binding,
        "arms": list(ARM_NAMES),
        "training_results": training_results,
        "checkpoint_references": checkpoint_references,
        "resume_telemetry": {"root_preexisted": root_preexisted},
    }
    _write_json_immutable(root / "train_manifest.json", manifest)
    binding = _commit_artifact(root, "train_manifest.json", RUN_SCHEMA)
    _write_json_immutable(terminal_binding_path, binding)
    return root / "train_manifest.json"


def _checkpoint_payload(
    root: Path,
    checkpoint: Mapping[str, object],
    *,
    config: RunConfig,
) -> dict[str, object]:
    reference = checkpoint.get("reference")
    marker_reference = checkpoint.get("complete_reference")
    digest = checkpoint.get("sha256")
    replicate = checkpoint.get("replicate")
    arm = checkpoint.get("arm")
    if (
        type(reference) is not str
        or type(marker_reference) is not str
        or type(digest) is not str
        or type(replicate) is not int
        or arm not in ARM_NAMES
    ):
        raise ValueError("checkpoint inventory row is malformed")
    path = root / reference
    marker_path = root / marker_reference
    if not path.is_file() or not marker_path.is_file() or _sha256_file(path) != digest:
        raise ValueError("checkpoint inventory content binding mismatch")
    if _read_json(marker_path) != {
        "schema": COMMIT_SCHEMA,
        "artifact_schema": CHECKPOINT_SCHEMA,
        "artifact_reference": reference,
        "artifact_sha256": digest,
        "replicate": replicate,
        "arm": arm,
        "completed_updates": config.updates,
    }:
        raise ValueError("checkpoint completion marker mismatch")
    payload = _torch_load(path)
    if int(payload.get("completed_updates", -1)) != config.updates:
        raise ValueError("only the final registered update may be evaluated")
    return payload


def _training_operational_errors(
    manifest: Mapping[str, object], config: RunConfig
) -> list[str]:
    if manifest.get("status") != TRAIN_COMPLETE:
        return []
    rows = manifest.get("training_results")
    if type(rows) is not list:
        return ["training result inventory malformed"]
    errors: list[str] = []
    parameter_counts: set[int] = set()
    for row in rows:
        if type(row) is not dict:
            errors.append("training result row malformed")
            continue
        count = row.get("parameter_count")
        if type(count) is not int or count <= 0:
            errors.append("invalid parameter count")
        else:
            parameter_counts.add(count)
        if row.get("paired_initialization_max_error") != 0.0:
            errors.append("paired initialization mismatch")
        if row.get("updates") != config.updates:
            errors.append("update exposure mismatch")
        if row.get("optimizer_steps") != config.updates * config.ppo_passes:
            errors.append("optimizer exposure mismatch")
        if row.get("environment_transitions") != config.updates * config.num_envs * config.horizon:
            errors.append("environment exposure mismatch")
        audit = row.get("cumulative_audit")
        if type(audit) is not dict or audit.get("finite_updates") is not True:
            errors.append("non-finite PPO update")
            continue
        if type(audit.get("active_tokens")) is not int or int(audit["active_tokens"]) <= 0:
            errors.append("training collected no active likelihood tokens")
        if not np.isfinite(float(audit.get("maximum_gradient_norm", float("nan")))):
            errors.append("non-finite gradient norm")
        maximum_errors = audit.get("maximum_errors")
        if type(maximum_errors) is not dict:
            errors.append("replay audit missing")
            continue
        for name in (
            "logp_max_error",
            "joint_logp_max_error",
            "value_max_error",
            "hidden_max_error",
            "prefix_max_error",
            "inactive_logp_max_abs",
            "inactive_action_max_abs",
            "inactive_hidden_change_max_abs",
        ):
            try:
                value = float(maximum_errors[name])
            except (KeyError, TypeError, ValueError):
                errors.append(f"{name} audit missing")
                continue
            if not np.isfinite(value) or value > REPLAY_TOLERANCE:
                errors.append(f"{name} exceeds replay tolerance")
    if len(parameter_counts) > 1:
        errors.append("paired arm parameter counts differ")
    return sorted(set(errors))


def _learned_evaluation_row(
    *,
    metrics: object,
    arm: str,
    replicate: int,
    profile: EnergyProfile,
    mode: str,
    episode_id: int,
    ledger: object,
    checkpoint: Mapping[str, object],
    action_seed: int,
) -> dict[str, object]:
    value = _metric_mapping(metrics)
    required = {
        "J_event": "j_event",
        "Q_ordinary": "q_ordinary",
        "catastrophe_episode": "catastrophe_episode",
        "return_cost_burden": "mean_return_cost_burden",
        "cutoff_events": "cutoff_events",
        "depletion_events": "depletion_events",
        "complete_charge_cycles": "complete_charge_cycles",
        "complete_recovery_windows": "complete_recovery_windows",
        "station_used": "station_used",
        "max_concurrent_absence": "max_concurrent_absence",
        "no_charge_pressure": "no_charge_pressure",
        "physical_consistency": "physical_consistency",
        "action_path_sha256": "action_path_sha256",
        "queue_uav_steps": "queue_uav_steps",
        "max_queue_length": "max_queue_length",
    }
    row: dict[str, object] = {}
    for target, source in required.items():
        if source not in value:
            raise ValueError(f"G2 learned metrics omit {target}")
        row[target] = value[source]
    row["J_rejoin"] = value.get("j_rejoin")
    ledger_id = getattr(ledger, "ledger_id", None)
    if type(ledger_id) is not str or not ledger_id:
        raise ValueError("G2 evaluation ledger omits immutable ledger_id")
    return {
        "schema": EVALUATION_ROW_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "arm": arm,
        "replicate": replicate,
        "profile": profile.value,
        "action_mode": mode,
        "episode_id": episode_id,
        "ledger_id": ledger_id,
        "checkpoint_reference": checkpoint["reference"],
        "checkpoint_sha256": checkpoint["sha256"],
        "action_seed": int(action_seed),
        "deterministic": mode == "deterministic",
    } | row


def _synthetic_learned_metrics() -> dict[str, object]:
    return {
        "j_event": 0.8,
        "j_rejoin": 0.8,
        "q_ordinary": 0.9,
        "catastrophe_episode": 0,
        "mean_return_cost_burden": 0.0,
        "cutoff_events": 0,
        "depletion_events": 0,
        "complete_charge_cycles": 1,
        "complete_recovery_windows": True,
        "station_used": True,
        "max_concurrent_absence": 1,
        "no_charge_pressure": False,
        "physical_consistency": True,
        "action_path_sha256": "0" * 64,
        "queue_uav_steps": 0,
        "max_queue_length": 0,
    }


def _evaluation_operational_errors(
    rows: Sequence[Mapping[str, object]],
) -> list[str]:
    errors: list[str] = []
    for row in rows:
        for name in ("J_event", "Q_ordinary"):
            value = _finite_number(name, row.get(name))
            if not 0.0 <= value <= 1.0:
                errors.append(f"{name} outside [0,1]")
        if row.get("J_rejoin") is not None:
            value = _finite_number("J_rejoin", row.get("J_rejoin"))
            if not 0.0 <= value <= 1.0:
                errors.append("J_rejoin outside [0,1]")
        catastrophe = row.get("catastrophe_episode")
        if type(catastrophe) is not int or catastrophe not in (0, 1):
            errors.append("catastrophe indicator malformed")
        burden = _finite_number("return-cost burden", row.get("return_cost_burden"))
        if not 0.0 <= burden <= 1.0:
            errors.append("return-cost burden outside [0,1]")
        for name in (
            "cutoff_events",
            "depletion_events",
            "complete_charge_cycles",
            "max_concurrent_absence",
        ):
            if type(row.get(name)) is not int or int(row[name]) < 0:
                errors.append(f"{name} malformed")
        if row.get("physical_consistency") is not True:
            errors.append("learned evaluation physical consistency failed")
        digest = row.get("action_path_sha256")
        if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            errors.append("learned action-path digest malformed")
        if type(row.get("queue_uav_steps")) is not int or int(row["queue_uav_steps"]) < 0:
            errors.append("learned queue duration malformed")
        if type(row.get("max_queue_length")) is not int or int(row["max_queue_length"]) < 0:
            errors.append("learned maximum queue length malformed")
    return sorted(set(errors))


def _evaluation_chunk_reference(
    *, replicate: int, arm: str, profile: EnergyProfile, mode: str, start: int
) -> str:
    return (
        f"evaluation_chunks/replicate_{replicate:02d}/{arm}/"
        f"{profile.value}/{mode}/batch_{start:04d}.json"
    )


def _load_or_write_evaluation_chunk(
    root: Path,
    *,
    reference: str,
    rows: Sequence[Mapping[str, object]] | None,
) -> tuple[list[dict[str, object]], dict[str, str]]:
    binding_path = root / f"{reference}.binding.json"
    binding = None
    if binding_path.exists():
        binding = _read_binding_or_truncated(binding_path)
        if binding is None:
            binding_path.unlink()
    if binding is None:
        logical = Path(reference)
        binding = _recover_attempt_binding(
            root,
            directory=root / logical.parent,
            artifact_pattern=f"{logical.stem}.attempt_*.json",
            artifact_name_pattern=(
                re.escape(logical.stem) + r"\.attempt_([0-9]{4})\.json"
            ),
            schema=EVALUATION_CHUNK_SCHEMA,
        )
        if binding is not None:
            _write_json_immutable(binding_path, binding)
    if binding is not None:
        artifact = _validate_committed_artifact(
            root, binding, schema=EVALUATION_CHUNK_SCHEMA
        )
        payload = _read_json(artifact)
        if payload.get("schema") != EVALUATION_CHUNK_SCHEMA or type(payload.get("rows")) is not list:
            raise ValueError("evaluation chunk is malformed")
        return list(payload["rows"]), dict(binding)
    if rows is None:
        raise ValueError("missing evaluation chunk cannot be assembled")
    logical = Path(reference)
    directory = root / logical.parent
    directory.mkdir(parents=True, exist_ok=True)
    stem = logical.stem
    attempts = [
        path
        for path in directory.glob(f"{stem}.attempt_*.json")
        if re.fullmatch(
            re.escape(stem) + r"\.attempt_[0-9]{4}\.json", path.name
        )
    ]
    attempt_reference = str(
        logical.parent / f"{stem}.attempt_{len(attempts):04d}.json"
    ).replace("\\", "/")
    payload = {"schema": EVALUATION_CHUNK_SCHEMA, "rows": list(rows)}
    _write_json_immutable(root / attempt_reference, payload)
    binding = _commit_artifact(root, attempt_reference, EVALUATION_CHUNK_SCHEMA)
    _write_json_immutable(binding_path, binding)
    return [dict(row) for row in rows], binding


def _after_evaluation_chunk_commit(*, reference: str) -> None:
    """Focused-test interruption seam; production deliberately does nothing."""


def evaluate_run(root: Path) -> Path:
    root = Path(root)
    configure_runtime(SeedRegistry().evaluation_action)
    manifest_binding = _read_json(root / "train_manifest.binding.json")
    manifest_path = _validate_committed_artifact(root, manifest_binding, schema=RUN_SCHEMA)
    manifest = _read_json(manifest_path)
    config = RunConfig(**manifest["config"])
    terminal_binding_path = root / "evaluation.binding.json"
    _terminal_binding(
        root,
        terminal_binding_path,
        reference="evaluation.json",
        schema=EVALUATION_SCHEMA,
    )
    if terminal_binding_path.exists():
        binding = _read_json(terminal_binding_path)
        return _validate_committed_artifact(root, binding, schema=EVALUATION_SCHEMA)
    source_screen = _validate_committed_artifact(
        root, manifest["source_screen"], schema=SOURCE_SCREEN_SCHEMA
    )
    source_payload = _read_json(source_screen)
    learned_rows: list[dict[str, object]] = []
    chunk_bindings: list[dict[str, str]] = []
    operational_errors = _training_operational_errors(manifest, config)
    if manifest["status"] == TRAIN_COMPLETE and not operational_errors:
        checkpoint_map = {
            (int(row["replicate"]), str(row["arm"])): row
            for row in manifest["checkpoint_references"]
        }
        for replicate in range(config.replicates):
            seeds = _replicate_seeds(replicate)
            spec = _paired_model_spec(config, seeds)
            for arm in ARM_NAMES:
                checkpoint = checkpoint_map[(replicate, arm)]
                payload = _checkpoint_payload(root, checkpoint, config=config)
                configure_runtime(seeds["model_initialization"])
                model = MatchedChargeRotationPolicy(
                    spec["observation_dim"], spec["critic_state_dim"], routing_mode=arm
                ).to(torch.device("cpu"))
                optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
                load_g2_checkpoint_state(
                    payload,
                    model=model,
                    optimizer=optimizer,
                    expected_seed_contract=seeds,
                )
                for profile in EVALUATION_PROFILES:
                    for mode in ACTION_MODES:
                        for start in range(
                            0, config.evaluation_episodes, config.evaluation_batch_size
                        ):
                            reference = _evaluation_chunk_reference(
                                replicate=replicate,
                                arm=arm,
                                profile=profile,
                                mode=mode,
                                start=start,
                            )
                            existing_binding = root / f"{reference}.binding.json"
                            if existing_binding.exists():
                                rows, binding = _load_or_write_evaluation_chunk(
                                    root, reference=reference, rows=None
                                )
                            else:
                                episode_ids = tuple(
                                    range(
                                        start,
                                        min(
                                            start + config.evaluation_batch_size,
                                            config.evaluation_episodes,
                                        ),
                                    )
                                )
                                ledgers = [
                                    make_g2_episode_ledger(
                                        profile,
                                        episode_id,
                                        energy_seed=seeds["evaluation_ledger"],
                                    )
                                    for episode_id in episode_ids
                                ]
                                if manifest["formal"]:
                                    environment_seeds = [
                                        seeds["evaluation_environment"] + episode_id
                                        for episode_id in episode_ids
                                    ]
                                    with PersistentG2VectorEnv(
                                        ledgers, environment_seeds
                                    ) as vector:
                                        metric_rows = evaluate_g2_policy(
                                            model,
                                            vector,
                                            episode_ids=episode_ids,
                                            action_seed=seeds["evaluation_action"],
                                            device=torch.device("cpu"),
                                            deterministic=mode == "deterministic",
                                        )
                                else:
                                    metric_rows = tuple(
                                        _synthetic_learned_metrics() for _ in episode_ids
                                    )
                                candidate_rows = [
                                    _learned_evaluation_row(
                                        metrics=metrics,
                                        arm=arm,
                                        replicate=replicate,
                                        profile=profile,
                                        mode=mode,
                                        episode_id=episode_id,
                                        ledger=ledger,
                                        checkpoint=checkpoint,
                                        action_seed=seeds["evaluation_action"],
                                    )
                                    for episode_id, ledger, metrics in zip(
                                        episode_ids, ledgers, metric_rows
                                    )
                                ]
                                rows, binding = _load_or_write_evaluation_chunk(
                                    root, reference=reference, rows=candidate_rows
                                )
                                _after_evaluation_chunk_commit(reference=reference)
                            learned_rows.extend(rows)
                            chunk_bindings.append(binding)
    operational_errors = sorted(
        set(operational_errors + _evaluation_operational_errors(learned_rows))
    )
    rows_binding: dict[str, str] | None = None
    if learned_rows:
        rows_binding = _recover_binding(
            root, "evaluation_rows.jsonl", schema=EVALUATION_ROW_SCHEMA
        )
        if rows_binding is None:
            _write_jsonl(root / "evaluation_rows.jsonl", learned_rows)
            rows_binding = _commit_artifact(
                root, "evaluation_rows.jsonl", EVALUATION_ROW_SCHEMA
            )
        elif _read_jsonl(root / "evaluation_rows.jsonl") != learned_rows:
            raise ValueError("committed learned rows differ from evaluation chunks")
    evaluation: dict[str, object] = {
        "schema": EVALUATION_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": manifest["source_commit"],
        "formal": manifest["formal"],
        "status": "EVALUATION_COMPLETE",
        "runtime": _runtime_identity(),
        "config": manifest["config"],
        "seed_registry": manifest["seed_registry"],
        "operational_valid": not operational_errors,
        "operational_errors": operational_errors,
        "source_identifiable": source_payload["source_identifiable"],
        "source_screen": manifest["source_screen"],
        "training_manifest": manifest_binding,
        "learned_rows": rows_binding,
        "evaluation_chunks": chunk_bindings,
        "checkpoint_inventory": manifest["checkpoint_references"],
        "conclusion_bearing": bool(manifest["formal"]),
    }
    _write_json_immutable(root / "evaluation.json", evaluation)
    binding = _commit_artifact(root, "evaluation.json", EVALUATION_SCHEMA)
    _write_json_immutable(terminal_binding_path, binding)
    return root / "evaluation.json"


def analyze_run(root: Path) -> Path:
    root = Path(root)
    configure_runtime(SeedRegistry().bootstrap)
    evaluation_binding = _read_json(root / "evaluation.binding.json")
    evaluation_path = _validate_committed_artifact(
        root, evaluation_binding, schema=EVALUATION_SCHEMA
    )
    evaluation = _read_json(evaluation_path)
    config = RunConfig(**evaluation["config"])
    analysis_binding_path = root / "analysis.binding.json"
    _terminal_binding(
        root,
        analysis_binding_path,
        reference="analysis.json",
        schema=ANALYSIS_SCHEMA,
    )
    if analysis_binding_path.exists():
        binding = _read_json(analysis_binding_path)
        analysis_path = _validate_committed_artifact(
            root, binding, schema=ANALYSIS_SCHEMA
        )
        return _ensure_terminal_result(root, _read_json(analysis_path), binding)
    learned_binding = evaluation.get("learned_rows")
    rows: list[dict[str, object]] = []
    if type(learned_binding) is dict:
        rows_path = _validate_committed_artifact(
            root, learned_binding, schema=EVALUATION_ROW_SCHEMA
        )
        rows = _read_jsonl(rows_path)
    evaluation_for_analysis = dict(evaluation)
    evaluation_for_analysis["_learned_rows_value"] = rows
    analysis = _analysis_from_evaluation(evaluation_for_analysis, config=config)
    analysis["evaluation"] = evaluation_binding
    _write_json_immutable(root / "analysis.json", analysis)
    binding = _commit_artifact(root, "analysis.json", ANALYSIS_SCHEMA)
    _write_json_immutable(analysis_binding_path, binding)
    _after_analysis_commit()
    return _ensure_terminal_result(root, analysis, binding)


def _after_analysis_commit() -> None:
    """Focused-test interruption seam; production deliberately does nothing."""


def _expected_terminal_result(
    analysis: Mapping[str, object], binding: Mapping[str, object]
) -> dict[str, object]:
    return {
        "schema": ANALYSIS_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": analysis["source_commit"],
        "formal": analysis["formal"],
        "operational_valid": analysis["operational_valid"],
        "result": analysis["result"],
        "analysis": dict(binding),
        "conclusion_bearing": analysis["conclusion_bearing"],
    }


def _ensure_terminal_result(
    root: Path,
    analysis: Mapping[str, object],
    binding: Mapping[str, object],
) -> Path:
    expected = _expected_terminal_result(analysis, binding)
    recovered = _recover_binding(root, "result.json", schema=ANALYSIS_SCHEMA)
    if recovered is not None:
        actual = _read_json(root / "result.json")
        if actual != expected:
            raise ValueError("committed terminal result differs from analysis authority")
        return root / "result.json"
    _write_json_immutable(root / "result.json", expected)
    _commit_artifact(root, "result.json", ANALYSIS_SCHEMA)
    return root / "result.json"


def _nested_equal(left: object, right: object) -> bool:
    if isinstance(left, torch.Tensor) and isinstance(right, torch.Tensor):
        return left.dtype == right.dtype and left.shape == right.shape and torch.equal(left, right)
    if isinstance(left, np.ndarray) and isinstance(right, np.ndarray):
        return left.dtype == right.dtype and left.shape == right.shape and np.array_equal(left, right)
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return left.keys() == right.keys() and all(
            _nested_equal(left[key], right[key]) for key in left
        )
    if type(left) in (list, tuple) and type(right) is type(left):
        return len(left) == len(right) and all(
            _nested_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


def validate_run_artifacts(root: Path, *, require_formal: bool) -> None:
    root = Path(root)
    configure_runtime(SeedRegistry().bootstrap)
    launch = _read_json(root / "launch_identity.json")
    if launch.get("schema") != LAUNCH_SCHEMA or launch.get("source_family") != SOURCE_FAMILY:
        raise ValueError("launch identity schema/source mismatch")
    formal = launch.get("formal") is True
    if require_formal and not formal:
        raise ValueError("formal validation rejects nonformal G2 artifacts")
    config = RunConfig(**launch["config"])
    _validate_launch(
        formal=formal,
        authorization_token=launch.get("authorization_token"),
        config=config,
    )
    _validate_source_commit(launch.get("source_commit"), formal=formal)
    if launch.get("seed_registry") != asdict(SeedRegistry()):
        raise ValueError("launch seed registry mismatch")
    runtime = launch.get("runtime")
    if (
        type(runtime) is not dict
        or runtime.get("backend") != "cpu"
        or runtime.get("torch_threads") != 1
        or runtime.get("python") != str(Path(sys.executable).resolve())
    ):
        raise ValueError("runtime identity violates CPU one-thread contract")

    source_binding = _read_json(root / "source_screen.binding.json")
    source_path = _validate_committed_artifact(
        root, source_binding, schema=SOURCE_SCREEN_SCHEMA
    )
    source = _read_json(source_path)
    rows_binding = source.get("rows")
    if type(rows_binding) is not dict:
        raise ValueError("source screen omits committed control rows")
    rows_path = _validate_committed_artifact(
        root, rows_binding, schema=SOURCE_SCREEN_CHUNK_SCHEMA
    )
    source_rows = _read_jsonl(rows_path)
    if formal:
        assembled_source_rows: list[dict[str, object]] = []
        for replicate in range(config.replicates):
            for profile in EVALUATION_PROFILES:
                for start in range(
                    0, config.control_episodes, config.evaluation_batch_size
                ):
                    for control in CONTROL_NAMES:
                        chunk_rows, _ignored = _load_source_chunk(
                            root,
                            launch=launch,
                            config=config,
                            replicate=replicate,
                            profile=profile,
                            control=control,
                            start=start,
                        )
                        if chunk_rows is None:
                            raise ValueError("formal source-screen chunk is missing")
                        assembled_source_rows.extend(chunk_rows)
        assembled_source_rows.sort(
            key=lambda row: (
                int(row["replicate"]),
                tuple(item.value for item in EVALUATION_PROFILES).index(
                    str(row["profile"])
                ),
                int(row["episode_id"]),
                CONTROL_NAMES.index(str(row["control"])),
            )
        )
        if source_rows != assembled_source_rows:
            raise ValueError("terminal source rows differ from immutable chunk assembly")
    expected_source = _source_screen_payload(launch, source_rows, config=config)
    expected_source["rows"] = rows_binding
    if source != expected_source:
        raise ValueError("source-screen evidence does not reproduce exactly")

    manifest_binding = _read_json(root / "train_manifest.binding.json")
    manifest_path = _validate_committed_artifact(root, manifest_binding, schema=RUN_SCHEMA)
    manifest = _read_json(manifest_path)
    expected_manifest_identity = {
        "schema": RUN_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": launch["source_commit"],
        "formal": formal,
        "authorization_token": launch["authorization_token"],
        "runtime": launch["runtime"],
        "config": launch["config"],
        "seed_registry": launch["seed_registry"],
        "source_screen": source_binding,
        "arms": list(ARM_NAMES),
    }
    if any(manifest.get(key) != value for key, value in expected_manifest_identity.items()):
        raise ValueError("training manifest identity binding mismatch")
    if bool(source["source_identifiable"]) != (manifest.get("status") == TRAIN_COMPLETE):
        raise ValueError("training status conflicts with source-screen disposition")
    checkpoint_inventory = manifest.get("checkpoint_references")
    training_results = manifest.get("training_results")
    if type(checkpoint_inventory) is not list or type(training_results) is not list:
        raise ValueError("training inventories are malformed")
    if manifest["status"] == TRAIN_SKIPPED_SOURCE_NON_IDENTIFIABLE:
        if checkpoint_inventory or training_results:
            raise ValueError("source-screen-skipped run retained learned artifacts")
        if (root / "checkpoints").exists() or (root / "resume").exists():
            raise ValueError("source-screen-skipped run contains learned paths")
    else:
        expected_pairs = {
            (replicate, arm)
            for replicate in range(config.replicates)
            for arm in ARM_NAMES
        }
        actual_pairs = {
            (int(row["replicate"]), str(row["arm"])) for row in checkpoint_inventory
        }
        result_pairs = {
            (int(row["replicate"]), str(row["arm"])) for row in training_results
        }
        if actual_pairs != expected_pairs or result_pairs != expected_pairs:
            raise ValueError("training pair inventory is incomplete or duplicated")
        for checkpoint in checkpoint_inventory:
            payload = _checkpoint_payload(root, checkpoint, config=config)
            replicate = int(checkpoint["replicate"])
            arm = str(checkpoint["arm"])
            seeds = _replicate_seeds(replicate)
            latest, _ignored = _latest_resume(
                root, replicate=replicate, arm=arm, seeds=seeds
            )
            if latest is None or int(latest["completed_updates"]) != config.updates:
                raise ValueError("final resume authority is missing")
            resume_payload = _torch_load(root / str(latest["checkpoint_reference"]))
            for key in (
                "model_state",
                "optimizer_state",
                "torch_rng_state",
                "runner_cumulative",
            ):
                if not _nested_equal(payload[key], resume_payload[key]):
                    raise ValueError("final checkpoint differs from final resume authority")
        for row in training_results:
            if (
                row.get("updates") != config.updates
                or row.get("optimizer_steps") != config.updates * config.ppo_passes
                or row.get("environment_transitions")
                != config.updates * config.num_envs * config.horizon
                or row.get("paired_initialization_max_error") != 0.0
            ):
                raise ValueError("training exposure/initialization audit mismatch")
            checkpoint = next(
                item
                for item in checkpoint_inventory
                if item["replicate"] == row["replicate"]
                and item["arm"] == row["arm"]
            )
            payload = _torch_load(root / str(checkpoint["reference"]))
            if not _nested_equal(
                row.get("cumulative_audit"), payload.get("runner_cumulative")
            ):
                raise ValueError("training audit differs from checkpoint authority")

    training_operational_errors = _training_operational_errors(manifest, config)
    evaluation_binding = _read_json(root / "evaluation.binding.json")
    evaluation_path = _validate_committed_artifact(
        root, evaluation_binding, schema=EVALUATION_SCHEMA
    )
    evaluation = _read_json(evaluation_path)
    if any(
        evaluation.get(key) != value
        for key, value in {
            "schema": EVALUATION_SCHEMA,
            "source_family": SOURCE_FAMILY,
            "source_commit": launch["source_commit"],
            "formal": formal,
            "status": "EVALUATION_COMPLETE",
            "runtime": launch["runtime"],
            "config": launch["config"],
            "seed_registry": launch["seed_registry"],
            "source_identifiable": source["source_identifiable"],
            "source_screen": source_binding,
            "training_manifest": manifest_binding,
            "checkpoint_inventory": checkpoint_inventory,
            "conclusion_bearing": formal,
        }.items()
    ):
        raise ValueError("evaluation identity/source binding mismatch")
    learned_rows: list[dict[str, object]] = []
    chunk_bindings = evaluation.get("evaluation_chunks")
    if type(chunk_bindings) is not list:
        raise ValueError("evaluation chunk inventory is malformed")
    for binding in chunk_bindings:
        if type(binding) is not dict:
            raise ValueError("evaluation chunk binding is malformed")
        chunk_path = _validate_committed_artifact(
            root, binding, schema=EVALUATION_CHUNK_SCHEMA
        )
        chunk = _read_json(chunk_path)
        if chunk.get("schema") != EVALUATION_CHUNK_SCHEMA or type(chunk.get("rows")) is not list:
            raise ValueError("evaluation chunk payload is malformed")
        learned_rows.extend(chunk["rows"])
    expected_operational_errors = sorted(
        set(
            training_operational_errors
            + _evaluation_operational_errors(learned_rows)
        )
    )
    if (
        evaluation.get("operational_valid") is not (not expected_operational_errors)
        or evaluation.get("operational_errors") != expected_operational_errors
    ):
        raise ValueError("evaluation operational predicate mismatch")
    learned_binding = evaluation.get("learned_rows")
    if manifest["status"] == TRAIN_COMPLETE and not training_operational_errors:
        expected_chunk_count = (
            config.replicates
            * len(ARM_NAMES)
            * len(STRATA)
            * (config.evaluation_episodes // config.evaluation_batch_size)
        )
        if len(chunk_bindings) != expected_chunk_count or type(learned_binding) is not dict:
            raise ValueError("evaluation chunk inventory count mismatch")
        learned_path = _validate_committed_artifact(
            root, learned_binding, schema=EVALUATION_ROW_SCHEMA
        )
        if _read_jsonl(learned_path) != learned_rows:
            raise ValueError("terminal learned rows differ from immutable chunk assembly")
        _learned_arrays(learned_rows, config)
    elif chunk_bindings or learned_binding is not None:
        raise ValueError("pruned evaluation retained learned rows")

    analysis_binding = _read_json(root / "analysis.binding.json")
    analysis_path = _validate_committed_artifact(root, analysis_binding, schema=ANALYSIS_SCHEMA)
    analysis = _read_json(analysis_path)
    evaluation_for_analysis = dict(evaluation)
    evaluation_for_analysis["_learned_rows_value"] = learned_rows
    expected_analysis = _analysis_from_evaluation(
        evaluation_for_analysis, config=config
    )
    expected_analysis["evaluation"] = evaluation_binding
    if analysis != expected_analysis:
        raise ValueError("analysis result does not reproduce frozen first-match semantics")
    result_binding = {
        "reference": "result.json",
        "complete_reference": "result.json.complete.json",
        "sha256": _sha256_file(root / "result.json"),
    }
    result_path = _validate_committed_artifact(root, result_binding, schema=ANALYSIS_SCHEMA)
    result = _read_json(result_path)
    if result != {
        "schema": ANALYSIS_SCHEMA,
        "source_family": SOURCE_FAMILY,
        "source_commit": analysis["source_commit"],
        "formal": analysis["formal"],
        "operational_valid": analysis["operational_valid"],
        "result": analysis["result"],
        "analysis": analysis_binding,
        "conclusion_bearing": analysis["conclusion_bearing"],
    }:
        raise ValueError("terminal result differs from committed analysis")
    if require_formal and analysis["result"] == NONFORMAL_RESULT:
        raise ValueError("formal validator rejects nonformal result meaning")


def validate_formal_result(root: Path) -> None:
    validate_run_artifacts(root, require_formal=True)


def exercise(root: Path, *, source_commit: str = "NONFORMAL_WORKTREE") -> Path:
    train_run(root, source_commit=source_commit, formal=False)
    evaluate_run(root)
    result = analyze_run(root)
    validate_run_artifacts(root, require_formal=False)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    train = subparsers.add_parser("train")
    train.add_argument("--root", type=Path, required=True)
    train.add_argument("--source-commit", required=True)
    train.add_argument("--formal", action="store_true")
    train.add_argument("--authorization-token")
    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--root", type=Path, required=True)
    analyze = subparsers.add_parser("analyze")
    analyze.add_argument("--root", type=Path, required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("--root", type=Path, required=True)
    validate.add_argument("--require-formal", action="store_true")
    bounded = subparsers.add_parser("exercise")
    bounded.add_argument("--root", type=Path, required=True)
    bounded.add_argument("--source-commit", default="NONFORMAL_WORKTREE")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "train":
        path = train_run(
            args.root,
            source_commit=args.source_commit,
            formal=args.formal,
            authorization_token=args.authorization_token,
        )
    elif args.command == "evaluate":
        path = evaluate_run(args.root)
    elif args.command == "analyze":
        path = analyze_run(args.root)
    elif args.command == "validate":
        validate_run_artifacts(args.root, require_formal=args.require_formal)
        path = args.root / "result.json"
    else:
        path = exercise(args.root, source_commit=args.source_commit)
    print(str(path))


if __name__ == "__main__":
    main()
