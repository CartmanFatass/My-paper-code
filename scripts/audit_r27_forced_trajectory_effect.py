"""Collect and aggregate the frozen R27-G2 forced-label intervention."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch  # noqa: E402

from ha_ctse_process.r27_g2_collector import (  # noqa: E402
    BRANCH_COUNT,
    BRANCH_STEPS,
    R27G2ResetArtifact,
    collect_reset_evidence,
    prefix_policy_seed_for_reset,
    prefix_steps_for_reset,
    write_reset_collection,
)
from ha_ctse_process.r27_g2_runtime import (  # noqa: E402
    R27G2ContractError,
    capture_value_norm_payload,
    capture_value_norm_state,
    configure_deterministic_cuda,
    value_norm_states_equal,
)


REGISTERED_CHECKPOINTS: dict[str, dict[str, Any]] = {
    "arm0_update25": {
        "path": "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_25.pt",
        "update": 25,
        "total_steps": 800000,
    },
    "arm0_update30": {
        "path": "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_update_30.pt",
        "update": 30,
        "total_steps": 960000,
    },
    "arm0_final": {
        "path": "dist/logs_cloud_r25_qa_verification_1m/arm0_arch_only/seed1/standalone_process_core_final.pt",
        "update": 32,
        "total_steps": 1000000,
    },
}
CHECKPOINT_IDS = tuple(REGISTERED_CHECKPOINTS)
DESIGN_PATH = "docs/research/R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md"
SCIENTIFIC_CONTRACT: dict[str, Any] = {
    "experiment_id": "EXP-20260712-r27-g2-forced-z-trajectory-effect",
    "checkpoint_ids": list(CHECKPOINT_IDS),
    "checkpoint_slots": copy.deepcopy(REGISTERED_CHECKPOINTS),
    "reset_ids": list(range(64)),
    "reset_seeds": list(range(1, 65)),
    "reset_groups_per_checkpoint": 64,
    "environments_per_reset_worker": 1,
    "default_reset_worker_limit": 64,
    "allowed_reset_worker_limit": [2, 64],
    "prefix_policy_seeds": [prefix_policy_seed_for_reset(i) for i in range(64)],
    "prefix_steps": [prefix_steps_for_reset(i) for i in range(64)],
    "n_agents": 6,
    "n_skills": 4,
    "action_dim": 4,
    "skill_interval": 10,
    "duration_candidates": [1, 2, 3, 4],
    "branches_per_reset": BRANCH_COUNT,
    "branch_steps": BRANCH_STEPS,
    "environment_steps_per_checkpoint": 708000,
    "environment_steps_total": 2124000,
    "device": "cuda",
    "design_path": DESIGN_PATH,
}


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return str(value)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_jsonable(payload), indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def _path_matches_registered(actual: str | Path, expected: str) -> bool:
    actual_parts = tuple(part.lower() for part in Path(actual).parts)
    expected_parts = tuple(part.lower() for part in Path(expected).parts)
    suffixes = [expected_parts]
    if expected_parts and expected_parts[0] == "dist":
        suffixes.append(expected_parts[1:])
    return any(
        suffix
        and len(actual_parts) >= len(suffix)
        and actual_parts[-len(suffix) :] == suffix
        for suffix in suffixes
    )


def validate_collect_args(args: argparse.Namespace) -> dict[str, Any]:
    if args.checkpoint_id not in REGISTERED_CHECKPOINTS:
        raise ValueError(f"checkpoint-id must be one of {CHECKPOINT_IDS}")
    registered = REGISTERED_CHECKPOINTS[args.checkpoint_id]
    if not _path_matches_registered(args.checkpoint, registered["path"]):
        raise ValueError("checkpoint path does not match the registered R25 artifact")
    if int(args.checkpoint_update) != int(registered["update"]):
        raise ValueError("checkpoint update does not match the registered R25 artifact")
    if not 0 <= int(args.reset_id) < 64:
        raise ValueError("reset-id must be in 0..63")
    for name, actual, expected in (
        ("config", args.config, "ha_ctse_process.config"),
        ("scenario", args.scenario, "energy"),
        ("preset", args.preset, "S7-S1"),
        ("n_agents", int(args.n_agents), 6),
        ("device", str(args.device).lower(), "cuda"),
    ):
        if actual != expected:
            raise ValueError(f"{name} must equal {expected!r}; got {actual!r}")
    design = ROOT / DESIGN_PATH
    if not design.is_file() or design.stat().st_size <= 0:
        raise R27G2ContractError("R27-G2 registered design is missing or empty")
    checkpoint = Path(args.checkpoint)
    if not checkpoint.is_file() or checkpoint.stat().st_size <= 0:
        raise FileNotFoundError(checkpoint)
    return copy.deepcopy(registered)


def _set_eval_mode(agent: Any) -> None:
    seen: set[int] = set()
    for value in vars(agent).values():
        if id(value) in seen:
            continue
        seen.add(id(value))
        if isinstance(value, torch.nn.Module):
            value.eval()


def _state_from_info(info: Any) -> Any:
    mapping = info if isinstance(info, dict) else {}
    state = mapping.get("next_state", mapping.get("state"))
    if state is None:
        raise R27G2ContractError("R27-G2 source environment did not expose state")
    return state


def _configure_agent(args: argparse.Namespace):
    from ha_ctse_process import train as train_mod

    config = train_mod.load_config(args.config, args.preset or None)
    config.scenario = train_mod.normalize_scenario(args.scenario)
    metadata = train_mod.load_checkpoint_metadata(args.checkpoint)
    train_mod.apply_checkpoint_structure(config, args, metadata)
    if metadata.get("n_agents") is None:
        config.n_agents = int(args.n_agents)
        config.n_uavs = int(args.n_agents)
        config.max_observed_uavs = max(
            int(args.n_agents),
            int(getattr(config, "max_observed_uavs", args.n_agents)),
        )
    probe_env = train_mod.create_env(
        config,
        config.scenario,
        int(args.reset_id) + 1,
        rank=0,
        scale_mode="eval",
    )
    try:
        _obs, info = probe_env.reset(seed=int(args.reset_id) + 1)
        state_dim = int(torch.as_tensor(_state_from_info(info)).numel())
        agent = train_mod.create_agent(
            config,
            args,
            probe_env,
            num_envs=1,
            state_dim=state_dim,
        )
        total_steps, loaded_update = train_mod.load_checkpoint(
            args.checkpoint, agent, load_optimizers=False
        )
        checkpoint_payload = torch.load(Path(args.checkpoint), map_location="cpu")
        expected_value_norm_state = capture_value_norm_payload(checkpoint_payload)
        loaded_value_norm_state = capture_value_norm_state(agent)
        if not value_norm_states_equal(
            loaded_value_norm_state, expected_value_norm_state
        ):
            raise R27G2ContractError(
                "R27-G2 loaded ValueNorm state does not match checkpoint payload"
            )
        _set_eval_mode(agent)
    finally:
        probe_env.close()

    def env_factory():
        return train_mod.create_env(
            config,
            config.scenario,
            int(args.reset_id) + 1,
            rank=0,
            scale_mode="eval",
        )

    return (
        config,
        metadata,
        agent,
        env_factory,
        int(total_steps),
        int(loaded_update),
        True,
    )


def run_collect_reset(args: argparse.Namespace) -> dict[str, Any]:
    configure_deterministic_cuda(args.device)
    registered = validate_collect_args(args)
    checkpoint = Path(args.checkpoint)
    (
        config,
        metadata,
        agent,
        env_factory,
        total_steps,
        loaded_update,
        loaded_value_norm_equal,
    ) = _configure_agent(args)
    if loaded_update != int(registered["update"]):
        raise R27G2ContractError(
            f"loaded update mismatch expected={registered['update']} actual={loaded_update}"
        )
    if total_steps != int(registered["total_steps"]):
        raise R27G2ContractError(
            f"loaded total_steps mismatch expected={registered['total_steps']} actual={total_steps}"
        )
    try:
        result = collect_reset_evidence(
            env_factory=env_factory,
            agent=agent,
            reset_id=int(args.reset_id),
            checkpoint_id=str(args.checkpoint_id),
            checkpoint_update=loaded_update,
            checkpoint_path=checkpoint,
        )
    except R27G2ContractError as error:
        invalid_manifest = {
            "experiment_id": "EXP-20260712-r27-g2-forced-z-trajectory-effect",
            "status": "INVALID",
            "invalid_reasons": [str(error)],
            "excluded_reason": None,
            "calibration_complete": False,
            "reset_id": int(args.reset_id),
            "reset_seed": int(args.reset_id) + 1,
            "prefix_policy_seed": prefix_policy_seed_for_reset(int(args.reset_id)),
            "prefix_steps": prefix_steps_for_reset(int(args.reset_id)),
            "checkpoint_id": str(args.checkpoint_id),
            "checkpoint_update": loaded_update,
            "checkpoint_path": str(checkpoint),
            "checkpoint_file_nonempty": checkpoint.stat().st_size > 0,
            "module_state_equal": False,
            "value_norm_state_equal": False,
            "loaded_value_norm_equal": loaded_value_norm_equal,
            "checkpoint_metadata": _jsonable(metadata),
            "config_scenario": str(config.scenario),
            "device": str(args.device),
            "scientific_contract": SCIENTIFIC_CONTRACT,
        }
        manifest_path = Path(args.output_dir) / "reset_manifest.json"
        _write_json(manifest_path, invalid_manifest)
        return {
            "status": "INVALID",
            "artifact": None,
            "manifest": str(manifest_path),
            "reset_id": int(args.reset_id),
            "checkpoint_id": str(args.checkpoint_id),
        }
    module_state_equal = bool(result.manifest.get("module_state_equal"))
    value_norm_state_equal = bool(result.manifest.get("value_norm_state_equal"))
    manifest = dict(result.manifest)
    manifest.update(
        {
            "checkpoint_path": str(checkpoint),
            "checkpoint_file_nonempty": checkpoint.stat().st_size > 0,
            "module_state_equal": module_state_equal,
            "value_norm_state_equal": value_norm_state_equal,
            "loaded_value_norm_equal": loaded_value_norm_equal,
            "checkpoint_metadata": _jsonable(metadata),
            "config_scenario": str(config.scenario),
            "device": str(args.device),
            "scientific_contract": SCIENTIFIC_CONTRACT,
        }
    )
    if not (module_state_equal and value_norm_state_equal and loaded_value_norm_equal):
        manifest["status"] = "INVALID"
        manifest.setdefault("invalid_reasons", []).append(
            "full module state or ValueNorm state failed direct equality"
        )
    result = type(result)(artifact=result.artifact, manifest=manifest)
    shard_path, manifest_path = write_reset_collection(result, args.output_dir)
    return {
        "status": manifest["status"],
        "artifact": str(shard_path),
        "manifest": str(manifest_path),
        "reset_id": int(args.reset_id),
        "checkpoint_id": str(args.checkpoint_id),
    }


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise R27G2ContractError(f"expected JSON object: {path}")
    return value


def _validate_reset_inventory(run_root: Path) -> int:
    """Require the complete registered reset inventory before aggregation."""

    count = 0
    for checkpoint_id in CHECKPOINT_IDS:
        reset_root = run_root / checkpoint_id / "resets"
        expected_paths = [
            reset_root / f"reset_{reset_id:02d}" / "reset_manifest.json"
            for reset_id in range(64)
        ]
        found_paths = sorted(reset_root.glob("reset_*/reset_manifest.json"))
        if found_paths != expected_paths:
            raise R27G2ContractError(
                f"{checkpoint_id} reset manifest inventory/path mismatch"
            )
        count += len(expected_paths)
    return count


def _first_exclusion_event(
    artifact: R27G2ResetArtifact,
) -> tuple[int, int, str] | None:
    branchpoint_hits = np.flatnonzero(artifact.branchpoint_focal_failure)
    step_hits = np.argwhere(
        artifact.step_valid
        & (artifact.terminated | artifact.truncated | artifact.focal_failure)
    )
    candidates: list[tuple[int, int, str]] = []
    for branch_id in branchpoint_hits:
        candidates.append(
            (
                int(branch_id),
                -1,
                f"branch={int(branch_id)} branchpoint "
                "terminated=False truncated=False focal_failure=True",
            )
        )
    for branch_id, step in step_hits:
        candidates.append(
            (
                int(branch_id),
                int(step),
                f"branch={int(branch_id)} step={int(step) + 1} "
                f"terminated={bool(artifact.terminated[branch_id, step])} "
                f"truncated={bool(artifact.truncated[branch_id, step])} "
                f"focal_failure={bool(artifact.focal_failure[branch_id, step])}",
            )
        )
    if not candidates:
        return None
    return min(candidates, key=lambda item: (item[0], item[1]))


def _expected_excluded_reason(artifact: R27G2ResetArtifact) -> str | None:
    event = _first_exclusion_event(artifact)
    return None if event is None else event[2]


def _status_evidence_failures(
    manifest: dict[str, Any],
    artifact: R27G2ResetArtifact | None,
    *,
    context: str,
) -> list[str]:
    failures: list[str] = []
    status = str(manifest.get("status", ""))
    reasons = manifest.get("invalid_reasons")
    excluded_reason = manifest.get("excluded_reason")
    valid_reason_list = isinstance(reasons, list) and all(
        isinstance(item, str) and bool(item.strip()) for item in reasons
    )
    if status not in {"OK", "EXCLUDED", "INVALID"}:
        return [f"{context} has unknown status {status!r}"]
    if not valid_reason_list:
        failures.append(f"{context} invalid_reasons is not a list of nonempty strings")
        reasons = []

    if status == "INVALID":
        if not reasons:
            failures.append(f"{context} INVALID has no recorded reason")
        return failures

    if reasons:
        failures.append(f"{context} {status} carries invalid_reasons")
    if artifact is None:
        failures.append(f"{context} {status} is missing its typed artifact")
        return failures
    if manifest.get("calibration_complete") is not True:
        failures.append(f"{context} {status} lacks complete prefix calibration")
    if np.any(
        (artifact.terminated | artifact.truncated | artifact.focal_failure)
        & ~artifact.step_valid
    ):
        failures.append(f"{context} contains an exclusion event outside valid steps")

    expected_exclusion = _expected_excluded_reason(artifact)
    if status == "EXCLUDED":
        if not isinstance(excluded_reason, str) or not excluded_reason.strip():
            failures.append(f"{context} EXCLUDED has no excluded_reason")
        elif excluded_reason != expected_exclusion:
            failures.append(
                f"{context} EXCLUDED reason/event mismatch: "
                f"reason={excluded_reason!r} event={expected_exclusion!r}"
            )
        if expected_exclusion is None:
            failures.append(f"{context} EXCLUDED has no recorded boundary/failure event")
        else:
            event = _first_exclusion_event(artifact)
            if event is None:
                raise AssertionError("exclusion reason exists without an event")
            branch_id, step, _reason = event
            expected_steps = np.zeros_like(artifact.step_valid)
            if step >= 0:
                expected_steps[branch_id, : step + 1] = True
            if branch_id > 0:
                expected_steps[:branch_id] = True
            expected_completed = np.zeros_like(artifact.branch_completed)
            if branch_id > 0:
                expected_completed[:branch_id] = True
            if step == artifact.step_valid.shape[1] - 1:
                expected_completed[branch_id] = True
            if not np.array_equal(artifact.step_valid, expected_steps):
                failures.append(
                    f"{context} EXCLUDED step progression is inconsistent with its first event"
                )
            if not np.array_equal(artifact.branch_completed, expected_completed):
                failures.append(
                    f"{context} EXCLUDED branch progression is inconsistent with its first event"
                )
        return failures

    if excluded_reason not in (None, ""):
        failures.append(f"{context} OK carries an excluded_reason")
    if expected_exclusion is not None:
        failures.append(f"{context} OK contains an exclusion event")
    if not bool(np.all(artifact.branch_completed)):
        failures.append(f"{context} OK has an incomplete branch matrix")
    if float(artifact.reference_act_low_parity_abs_error.max()) > 1e-6:
        failures.append(f"{context} OK failed registered act_low parity")
    return failures


def _checkpoint_inputs(run_root: Path, checkpoint_id: str):
    reset_root = run_root / checkpoint_id / "resets"
    manifests = sorted(reset_root.glob("reset_*/reset_manifest.json"))
    if len(manifests) != 64:
        raise R27G2ContractError(
            f"{checkpoint_id} requires exactly 64 reset manifests; found {len(manifests)}"
        )
    artifacts: list[R27G2ResetArtifact | None] = []
    manifest_values: list[dict[str, Any]] = []
    for expected_reset, manifest_path in enumerate(manifests):
        manifest = _read_json(manifest_path)
        if int(manifest.get("reset_id", -1)) != expected_reset:
            raise R27G2ContractError(
                f"{checkpoint_id} reset manifest order/identity mismatch"
            )
        if manifest.get("checkpoint_id") != checkpoint_id:
            raise R27G2ContractError(f"{checkpoint_id} manifest checkpoint mismatch")
        if manifest.get("scientific_contract") != SCIENTIFIC_CONTRACT:
            raise R27G2ContractError(f"{checkpoint_id} scientific contract mismatch")
        artifact_name = manifest.get("artifact")
        if artifact_name:
            if str(artifact_name) != f"reset_{expected_reset:04d}.npz":
                raise R27G2ContractError(
                    f"{checkpoint_id} reset artifact path/name mismatch"
                )
            artifact_path = manifest_path.parent / str(artifact_name)
            if not artifact_path.is_file() or artifact_path.stat().st_size <= 0:
                raise R27G2ContractError(
                    f"{checkpoint_id} reset artifact is missing or empty"
                )
            artifacts.append(R27G2ResetArtifact.read(artifact_path))
        elif manifest.get("status") == "INVALID":
            artifacts.append(None)
        else:
            raise R27G2ContractError(
                f"{checkpoint_id} non-invalid reset is missing its typed artifact"
            )
        manifest_values.append(manifest)
    return artifacts, manifest_values


def _branch_index(
    artifact: R27G2ResetArtifact,
    *,
    kind: str,
    focal_agent: int | None = None,
    target_skill: int | None = None,
) -> int:
    mask = artifact.branch_kind == str(kind)
    if focal_agent is not None:
        mask &= artifact.branch_focal_agent == int(focal_agent)
    if target_skill is not None:
        mask &= artifact.branch_target_skill == int(target_skill)
    matches = np.flatnonzero(mask)
    if matches.size != 1:
        raise R27G2ContractError(
            "R27-G2 branch lookup must resolve exactly once: "
            f"kind={kind} focal_agent={focal_agent} target_skill={target_skill} "
            f"matches={matches.tolist()}"
        )
    return int(matches[0])


def _diagnostic_slot(
    artifact: R27G2ResetArtifact, *, branch_id: int, agent_id: int
) -> int:
    matches = np.flatnonzero(
        (artifact.diagnostic_branch_id == int(branch_id))
        & (artifact.diagnostic_agent_id == int(agent_id))
    )
    if matches.size != 1:
        raise R27G2ContractError(
            f"R27-G2 diagnostic slot mismatch branch={branch_id} agent={agent_id}"
        )
    return int(matches[0])


def _derive_checkpoint_analysis_input(
    checkpoint_id: str,
    artifacts: list[R27G2ResetArtifact | None],
    manifests: list[dict[str, Any]],
    *,
    gate_a_valid_repetition: bool = False,
):
    from ha_ctse_process import r27_g2_analysis as analysis

    if len(artifacts) != 64 or len(manifests) != 64:
        raise R27G2ContractError("R27-G2 checkpoint adapter requires 64 reset records")
    registered = REGISTERED_CHECKPOINTS[checkpoint_id]
    failures: list[str] = []

    # Freeze the registered prefix-only standardizers before consulting any
    # branch status, outcome, exclusion, or gate evidence.
    present_artifacts = [item for item in artifacts if item is not None]
    missing_artifact_count = len(artifacts) - len(present_artifacts)
    if missing_artifact_count:
        failures.append(
            f"{missing_artifact_count} reset artifacts/calibration blocks are missing"
        )
    observation_dim = (
        int(present_artifacts[0].calibration_observation.shape[-1])
        if present_artifacts
        else 1
    )
    calibration_action = (
        np.concatenate(
            [
                np.asarray(item.calibration_action, dtype=np.float64)
                for item in present_artifacts
            ],
            axis=0,
        )
        if present_artifacts
        else np.zeros((0, 6, 4), dtype=np.float64)
    )
    calibration_observation = (
        np.concatenate(
            [
                np.asarray(item.calibration_observation, dtype=np.float64)
                for item in present_artifacts
            ],
            axis=0,
        )
        if present_artifacts
        else np.zeros((0, 6, observation_dim), dtype=np.float64)
    )
    if calibration_action.shape != (64 * 50, 6, 4):
        failures.append("checkpoint action calibration does not contain 19,200 rows")
    if calibration_observation.shape[:2] != (64 * 50, 6):
        failures.append("checkpoint observation calibration does not contain 19,200 rows")
    if not np.isfinite(calibration_action).all() or not np.isfinite(
        calibration_observation
    ).all():
        failures.append("checkpoint calibration contains non-finite values")
    flattened_action_calibration = calibration_action.reshape(-1, 4)
    flattened_observation_calibration = calibration_observation.reshape(
        -1, observation_dim
    )
    if flattened_action_calibration.shape[0] == 0:
        flattened_action_calibration = np.zeros((1, 4), dtype=np.float64)
    if flattened_observation_calibration.shape[0] == 0:
        flattened_observation_calibration = np.zeros(
            (1, observation_dim), dtype=np.float64
        )
    action_mean = flattened_action_calibration.mean(axis=0, dtype=np.float64)
    action_population_std = flattened_action_calibration.std(axis=0, ddof=0)
    action_standard_deviation = np.maximum(action_population_std, 1e-3)
    observation_mean = flattened_observation_calibration.mean(
        axis=0, dtype=np.float64
    )
    observation_population_std = flattened_observation_calibration.std(
        axis=0, ddof=0
    )
    observation_standard_deviation = np.maximum(
        observation_population_std, 1e-3
    )
    calibration_report = {
        "reset_count": 64,
        "present_reset_count": len(present_artifacts),
        "complete": missing_artifact_count == 0,
        "steps_per_reset": 50,
        "agents_per_step": 6,
        "rows": int(calibration_action.shape[0] * 6),
        "expected_rows": 64 * 50 * 6,
        "ddof": 0,
        "standard_deviation_floor": 1e-3,
        "action_mean": action_mean.tolist(),
        "action_population_standard_deviation": action_population_std.tolist(),
        "action_frozen_standard_deviation": action_standard_deviation.tolist(),
        "observation_mean": observation_mean.tolist(),
        "observation_population_standard_deviation": observation_population_std.tolist(),
        "observation_frozen_standard_deviation": observation_standard_deviation.tolist(),
    }

    for reset_index, (artifact, manifest) in enumerate(
        zip(artifacts, manifests, strict=True)
    ):
        reset_id = (
            int(artifact.reset_id) if artifact is not None else int(reset_index)
        )
        status = str(manifest.get("status", ""))
        failures.extend(
            _status_evidence_failures(
                manifest, artifact, context=f"reset {reset_id}"
            )
        )
        if status == "INVALID":
            failures.append(
                f"reset {reset_id} invalid: {manifest.get('invalid_reasons', [])}"
            )
        if manifest.get("checkpoint_id") != checkpoint_id:
            failures.append(f"reset {reset_id} checkpoint_id mismatch")
        if int(manifest.get("checkpoint_update", -1)) != int(registered["update"]):
            failures.append(f"reset {reset_id} checkpoint update mismatch")
        checkpoint_path = manifest.get("checkpoint_path")
        if not checkpoint_path or not _path_matches_registered(
            str(checkpoint_path), str(registered["path"])
        ):
            failures.append(f"reset {reset_id} checkpoint path mismatch")
        if manifest.get("checkpoint_file_nonempty") is not True:
            failures.append(f"reset {reset_id} checkpoint is missing or empty")
        if manifest.get("module_state_equal") is not True:
            failures.append(f"reset {reset_id} full state_dict mutation flag")
        if manifest.get("value_norm_state_equal") is not True:
            failures.append(f"reset {reset_id} ValueNorm mutation flag")
        if manifest.get("loaded_value_norm_equal") is not True:
            failures.append(f"reset {reset_id} loaded ValueNorm mismatch")
        if str(manifest.get("device", "")).lower() != "cuda":
            failures.append(f"reset {reset_id} device is not exact CUDA")
        if manifest.get("scientific_contract") != SCIENTIFIC_CONTRACT:
            failures.append(f"reset {reset_id} scientific contract mismatch")
        if artifact is not None and status == "OK" and not bool(
            np.all(artifact.module_state_equal)
        ):
            failures.append(f"reset {reset_id} branch module-state equality failure")
        if artifact is not None and status == "OK" and not bool(
            np.all(artifact.value_norm_state_equal)
        ):
            failures.append(f"reset {reset_id} branch ValueNorm equality failure")

    valid_pairs = [
        (artifact, manifest)
        for artifact, manifest in zip(artifacts, manifests, strict=True)
        if artifact is not None
        and manifest.get("status") == "OK"
        and bool(np.all(artifact.branch_completed))
    ]
    for artifact, manifest in zip(artifacts, manifests, strict=True):
        if artifact is not None and manifest.get("status") == "OK" and not bool(
            np.all(artifact.branch_completed)
        ):
            failures.append(
                f"reset {int(artifact.reset_id)} status OK but branch matrix incomplete"
            )

    # Validity has precedence.  A structural placeholder keeps support
    # assessment typed even when every reset is invalid; gate metrics are not
    # evaluated in that branch.
    if valid_pairs:
        selected = [pair[0] for pair in valid_pairs]
        valid_reset_ids = np.asarray(
            [int(item.reset_id) for item in selected], dtype=np.int64
        )
    else:
        selected = []
        valid_reset_ids = np.asarray([], dtype=np.int64)
    reset_ids = (
        valid_reset_ids
        if valid_reset_ids.size
        else np.asarray([0], dtype=np.int64)
    )
    reset_count = max(len(selected), 1)
    gate_a_active = np.zeros((reset_count, 6, 6), dtype=np.float64)
    gate_a_inactive = np.zeros_like(gate_a_active)
    gate_a_distance = np.zeros_like(gate_a_active)
    b1_active = np.zeros((reset_count, 6, 4, 50, 6), dtype=np.float64)
    b1_inactive = np.zeros_like(b1_active)
    b1_action = np.zeros_like(b1_active)
    natural_labels = np.zeros((reset_count, 6), dtype=np.int64)
    target_labels = np.zeros((reset_count, 6, 3), dtype=np.int64)
    d_hold = np.zeros((reset_count, 6, 3), dtype=np.float64)
    d_pulse = np.zeros_like(d_hold)
    e_hold = np.zeros_like(d_hold)
    e_pulse = np.zeros_like(d_hold)
    b3_features = np.zeros((reset_count, 6, 4, 12), dtype=np.float64)
    b3_labels = np.broadcast_to(
        np.arange(4, dtype=np.int64).reshape(1, 1, 4),
        (reset_count, 6, 4),
    ).copy()
    hold_present = np.zeros((reset_count, 6, 4), dtype=np.bool_)
    pair_present = np.zeros((reset_count, 6), dtype=np.bool_)
    reference_swap_skl = np.zeros((reset_count, 6, 3), dtype=np.float64)
    pulse_swap_skl = np.zeros((reset_count, 6, 3, 3), dtype=np.float64)
    local_effect_endpoints = {
        horizon: np.zeros((reset_count, 6, 3, 2), dtype=np.float64)
        for horizon in (20, 40, 50)
    }
    global_state_endpoints = {
        horizon: np.zeros((reset_count, 6, 3, 2), dtype=np.float64)
        for horizon in (20, 40, 50)
    }
    nonfocal_action_distance = np.zeros(
        (reset_count, 6, 3, 2), dtype=np.float64
    )

    if valid_pairs:
        pair_lookup = {pair: index for index, pair in enumerate(analysis.LABEL_PAIRS)}
        for reset_index, artifact in enumerate(selected):
            reference_id = _branch_index(artifact, kind="reference")
            natural_labels[reset_index] = artifact.prefix_skill[-1]
            for agent_id in range(6):
                reference_slot = _diagnostic_slot(
                    artifact, branch_id=reference_id, agent_id=agent_id
                )
                active_mean = artifact.diagnostic_active_mean[
                    reference_slot, 0
                ]
                active_logstd = artifact.diagnostic_active_logstd[
                    reference_slot, 0
                ]
                inactive_mean = artifact.diagnostic_inactive_mean[
                    reference_slot, 0
                ]
                inactive_logstd = artifact.diagnostic_inactive_logstd[
                    reference_slot, 0
                ]
                gate_a_active[reset_index, agent_id] = analysis.enumerated_pair_skl(
                    active_mean, active_logstd
                )
                gate_a_inactive[
                    reset_index, agent_id
                ] = analysis.enumerated_pair_skl(inactive_mean, inactive_logstd)
                gate_a_distance[
                    reset_index, agent_id
                ] = analysis.enumerated_pair_stdmean_distance(
                    active_mean, active_logstd
                )
                reference_step_skl = analysis.enumerated_pair_skl(
                    artifact.diagnostic_active_mean[reference_slot],
                    artifact.diagnostic_active_logstd[reference_slot],
                ).mean(axis=-1)
                for window_index, window in enumerate(
                    (
                        analysis.WINDOW_EARLY,
                        analysis.WINDOW_MID,
                        analysis.WINDOW_LATE,
                    )
                ):
                    reference_swap_skl[
                        reset_index, agent_id, window_index
                    ] = float(reference_step_skl[window].mean())

                reference_action = artifact.joint_action[
                    reference_id, :, agent_id, :
                ]
                reference_observation = artifact.local_observation[
                    reference_id, analysis.H40_INDEX, agent_id, :
                ]
                natural = int(natural_labels[reset_index, agent_id])
                nonnatural = [label for label in range(4) if label != natural]
                target_labels[reset_index, agent_id] = nonnatural
                for label in range(4):
                    hold_id = _branch_index(
                        artifact,
                        kind="hold",
                        focal_agent=agent_id,
                        target_skill=label,
                    )
                    hold_present[reset_index, agent_id, label] = bool(
                        artifact.branch_completed[hold_id]
                    )
                    hold_slot = _diagnostic_slot(
                        artifact, branch_id=hold_id, agent_id=agent_id
                    )
                    b1_active[
                        reset_index, agent_id, label
                    ] = analysis.enumerated_pair_skl(
                        artifact.diagnostic_active_mean[hold_slot],
                        artifact.diagnostic_active_logstd[hold_slot],
                    )
                    b1_inactive[
                        reset_index, agent_id, label
                    ] = analysis.enumerated_pair_skl(
                        artifact.diagnostic_inactive_mean[hold_slot],
                        artifact.diagnostic_inactive_logstd[hold_slot],
                    )
                    b1_action[
                        reset_index, agent_id, label
                    ] = analysis.enumerated_pair_action_distance(
                        artifact.diagnostic_active_action[hold_slot],
                        action_standard_deviation,
                    )
                    b3_features[
                        reset_index, agent_id, label
                    ] = analysis.late_action_features(
                        artifact.joint_action[
                            hold_id, analysis.WINDOW_LATE, agent_id, :
                        ]
                    )

                for target_index, target in enumerate(nonnatural):
                    hold_id = _branch_index(
                        artifact,
                        kind="hold",
                        focal_agent=agent_id,
                        target_skill=target,
                    )
                    pulse_id = _branch_index(
                        artifact,
                        kind="pulse",
                        focal_agent=agent_id,
                        target_skill=target,
                    )
                    pulse_slot = _diagnostic_slot(
                        artifact, branch_id=pulse_id, agent_id=agent_id
                    )
                    pulse_step_skl = analysis.enumerated_pair_skl(
                        artifact.diagnostic_active_mean[pulse_slot],
                        artifact.diagnostic_active_logstd[pulse_slot],
                    ).mean(axis=-1)
                    for window_index, window in enumerate(
                        (
                            analysis.WINDOW_EARLY,
                            analysis.WINDOW_MID,
                            analysis.WINDOW_LATE,
                        )
                    ):
                        pulse_swap_skl[
                            reset_index,
                            agent_id,
                            target_index,
                            window_index,
                        ] = float(pulse_step_skl[window].mean())
                    d_hold[reset_index, agent_id, target_index] = float(
                        analysis.trajectory_distance(
                            artifact.joint_action[
                                hold_id, :, agent_id, :
                            ][None, ...],
                            reference_action,
                            action_standard_deviation,
                        )[0]
                    )
                    d_pulse[reset_index, agent_id, target_index] = float(
                        analysis.trajectory_distance(
                            artifact.joint_action[
                                pulse_id, :, agent_id, :
                            ][None, ...],
                            reference_action,
                            action_standard_deviation,
                        )[0]
                    )
                    e_hold[reset_index, agent_id, target_index] = float(
                        analysis.h40_effect_distance(
                            artifact.local_observation[
                                hold_id, analysis.H40_INDEX, agent_id, :
                            ],
                            reference_observation,
                            observation_standard_deviation,
                        )
                    )
                    e_pulse[reset_index, agent_id, target_index] = float(
                        analysis.h40_effect_distance(
                            artifact.local_observation[
                                pulse_id, analysis.H40_INDEX, agent_id, :
                            ],
                            reference_observation,
                            observation_standard_deviation,
                        )
                    )
                    for horizon in (20, 40, 50):
                        local_effect_endpoints[horizon][
                            reset_index, agent_id, target_index, 0
                        ] = float(
                            analysis.h40_effect_distance(
                                artifact.local_observation[
                                    hold_id, horizon, agent_id, :
                                ],
                                artifact.local_observation[
                                    reference_id, horizon, agent_id, :
                                ],
                                observation_standard_deviation,
                            )
                        )
                        local_effect_endpoints[horizon][
                            reset_index, agent_id, target_index, 1
                        ] = float(
                            analysis.h40_effect_distance(
                                artifact.local_observation[
                                    pulse_id, horizon, agent_id, :
                                ],
                                artifact.local_observation[
                                    reference_id, horizon, agent_id, :
                                ],
                                observation_standard_deviation,
                            )
                        )
                        global_state_endpoints[horizon][
                            reset_index, agent_id, target_index, 0
                        ] = float(
                            np.sqrt(
                                np.mean(
                                    np.square(
                                        artifact.global_state[hold_id, horizon]
                                        - artifact.global_state[
                                            reference_id, horizon
                                        ]
                                    )
                                )
                            )
                        )
                        global_state_endpoints[horizon][
                            reset_index, agent_id, target_index, 1
                        ] = float(
                            np.sqrt(
                                np.mean(
                                    np.square(
                                        artifact.global_state[pulse_id, horizon]
                                        - artifact.global_state[
                                            reference_id, horizon
                                        ]
                                    )
                                )
                            )
                        )
                    nonfocal_agents = [
                        other for other in range(6) if other != agent_id
                    ]
                    for branch_offset, comparison_id in enumerate(
                        (hold_id, pulse_id)
                    ):
                        standardized = (
                            artifact.joint_action[
                                comparison_id,
                                analysis.WINDOW_LATE,
                            ][:, nonfocal_agents, :]
                            - artifact.joint_action[
                                reference_id,
                                analysis.WINDOW_LATE,
                            ][:, nonfocal_agents, :]
                        ) / action_standard_deviation.reshape(1, 1, -1)
                        nonfocal_action_distance[
                            reset_index,
                            agent_id,
                            target_index,
                            branch_offset,
                        ] = float(
                            np.sqrt(np.mean(np.square(standardized), axis=(1, 2))).mean()
                        )
                    if bool(
                        artifact.branch_completed[hold_id]
                        and artifact.branch_completed[pulse_id]
                    ):
                        pair = tuple(sorted((natural, int(target))))
                        pair_present[reset_index, pair_lookup[pair]] = True

    support_reset_ids = valid_reset_ids
    if not valid_pairs:
        support_hold_present = np.zeros((0, 6, 4), dtype=np.bool_)
        support_pair_present = np.zeros((0, 6), dtype=np.bool_)
    else:
        support_hold_present = hold_present
        support_pair_present = pair_present
    support = analysis.SupportEvidence(
        reset_ids=support_reset_ids,
        hold_cell_present=support_hold_present,
        pair_contrast_present=support_pair_present,
        b3_reset_ids=support_reset_ids,
    )
    typed_input = analysis.CheckpointAnalysisInput(
        validity=analysis.ValidityEvidence(
            passed=not failures,
            failures=tuple(dict.fromkeys(failures)),
        ),
        support=support,
        gate_a=analysis.GateAInput(
            reset_ids=reset_ids,
            active_pair_skl=gate_a_active,
            inactive_pair_skl=gate_a_inactive,
            active_pair_stdmean_distance=gate_a_distance,
        ),
        gate_b1=analysis.GateB1Input(
            reset_ids=reset_ids,
            active_pair_skl=b1_active,
            inactive_pair_skl=b1_inactive,
            active_pair_action_distance=b1_action,
        ),
        gate_b2=analysis.GateB2Input(
            reset_ids=reset_ids,
            natural_labels=natural_labels,
            target_labels=target_labels,
            d_hold=d_hold,
            d_pulse=d_pulse,
        ),
        gate_b3=analysis.GateB3Input(
            reset_ids=reset_ids,
            features=b3_features,
            labels=b3_labels,
        ),
        gate_c=analysis.GateCInput(
            reset_ids=reset_ids,
            natural_labels=natural_labels,
            target_labels=target_labels,
            e_hold=e_hold,
            e_pulse=e_pulse,
        ),
        gate_a_valid_repetition=bool(gate_a_valid_repetition),
    )

    def contrast_summary(values: np.ndarray) -> dict[str, float]:
        hold_reset = values[..., 0].mean(axis=(1, 2))
        pulse_reset = values[..., 1].mean(axis=(1, 2))
        delta_reset = (values[..., 0] - values[..., 1]).mean(axis=(1, 2))
        ratio_reset = np.median(
            values[..., 0] / np.maximum(values[..., 1], 1e-6),
            axis=(1, 2),
        )
        return {
            "hold_mean": float(hold_reset.mean()),
            "pulse_mean": float(pulse_reset.mean()),
            "hold_minus_pulse_mean": float(delta_reset.mean()),
            "hold_over_pulse_median": float(np.median(ratio_reset)),
        }

    descriptions_available = bool(valid_pairs) and not failures and bool(
        calibration_report["complete"]
    )
    descriptive_report: dict[str, Any] = {
        "available": descriptions_available,
        "valid_reset_count": len(valid_pairs),
    }
    if descriptions_available:
        descriptive_report.update(
            {
                "window_names": [
                    "W_early_1_10",
                    "W_mid_11_20",
                    "W_late_31_40",
                ],
                "reference_state_swap_skl": {
                    name: float(reference_swap_skl[..., index].mean())
                    for index, name in enumerate(("early", "mid", "late"))
                },
                "pulse_state_swap_skl": {
                    name: float(pulse_swap_skl[..., index].mean())
                    for index, name in enumerate(("early", "mid", "late"))
                },
                "focal_action_wlate": contrast_summary(
                    np.stack((d_hold, d_pulse), axis=-1)
                ),
                "nonfocal_joint_action_wlate": contrast_summary(
                    nonfocal_action_distance
                ),
                "focal_local_observation_effect": {
                    f"H{horizon}": contrast_summary(local_effect_endpoints[horizon])
                    for horizon in (20, 40, 50)
                },
                "global_state_raw_rms_effect": {
                    f"H{horizon}": contrast_summary(global_state_endpoints[horizon])
                    for horizon in (20, 40, 50)
                },
                "gate_boundary": (
                    "Only H40 focal full-local-observation effect enters Gate C; "
                    "all other fields in this block are descriptive only."
                ),
            }
        )
    else:
        descriptive_report["unavailable_reason"] = (
            "checkpoint validity and complete prefix calibration are required"
        )
    return typed_input, calibration_report, descriptive_report


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# R27-G2 Forced-Z Trajectory/Effect Intervention",
        "",
        f"- Family status: `{report.get('status')}`",
        f"- Classification: `{report.get('classification')}`",
        f"- Registered structured reset evidence: {report.get('reset_evidence_count')} shards",
        "",
        "## Checkpoints",
        "",
    ]
    for checkpoint in report.get("checkpoints", []):
        lines.extend(
            [
                f"### {checkpoint.get('checkpoint_id')}",
                "",
                f"- Status: `{checkpoint.get('status')}`",
                f"- Classification: `{checkpoint.get('classification')}`",
                f"- Gate A/B1/B2/B3/C: {checkpoint.get('gate_a')} / {checkpoint.get('gate_b1')} / {checkpoint.get('gate_b2')} / {checkpoint.get('gate_b3')} / {checkpoint.get('gate_c')}",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "This reward-off frozen-checkpoint diagnostic does not authorize reward, actor/critic, FiLM/GRU, environment, optimizer, or training changes.",
            "",
        ]
    )
    return "\n".join(lines)


def run_aggregate(args: argparse.Namespace) -> dict[str, Any]:
    if tuple(args.checkpoint_ids) != CHECKPOINT_IDS:
        raise ValueError(f"checkpoint-ids must equal {CHECKPOINT_IDS}")
    configure_deterministic_cuda("cuda")
    run_root = Path(args.run_root)
    checkpoint_inputs = {
        checkpoint_id: _checkpoint_inputs(run_root, checkpoint_id)
        for checkpoint_id in CHECKPOINT_IDS
    }
    from ha_ctse_process.r27_g2_analysis import (
        analyze_checkpoint,
        classify_family,
    )

    checkpoint_reports: list[dict[str, Any]] = []
    decisions = []
    repetition_checkpoints = set(args.gate_a_valid_repetition_checkpoints)
    for checkpoint_id in CHECKPOINT_IDS:
        artifacts, manifests = checkpoint_inputs[checkpoint_id]
        typed_input, calibration_report, descriptive_report = _derive_checkpoint_analysis_input(
            checkpoint_id,
            artifacts,
            manifests,
            gate_a_valid_repetition=checkpoint_id in repetition_checkpoints,
        )
        checkpoint_result = analyze_checkpoint(
            typed_input,
            bootstrap_reps=10_000,
            b3_device="cuda",
        )
        decision = checkpoint_result.decision
        decisions.append(decision)
        checkpoint_reports.append(
            {
                "checkpoint_id": checkpoint_id,
                "status": decision.status,
                "classification": decision.outcome,
                "gate_a": decision.gate_a,
                "gate_b1": decision.gate_b1,
                "gate_b2": decision.gate_b2,
                "gate_b3": decision.gate_b3,
                "gate_b": decision.gate_b,
                "gate_c": decision.gate_c,
                "validity": _jsonable(typed_input.validity),
                "calibration": calibration_report,
                "descriptive": descriptive_report,
                "support": _jsonable(checkpoint_result.support),
                "gate_a_result": _jsonable(checkpoint_result.gate_a),
                "gate_b1_result": _jsonable(checkpoint_result.gate_b1),
                "gate_b2_result": _jsonable(checkpoint_result.gate_b2),
                "gate_b3_result": _jsonable(checkpoint_result.gate_b3),
                "gate_c_result": _jsonable(checkpoint_result.gate_c),
            }
        )
    family = classify_family(decisions)
    report: dict[str, Any] = {
        "status": family.status,
        "classification": family.outcome,
        "checkpoints": checkpoint_reports,
        "gate_a_valid_repetition_checkpoints": sorted(repetition_checkpoints),
    }
    report["reset_evidence_count"] = _validate_reset_inventory(run_root)
    report["scientific_contract"] = SCIENTIFIC_CONTRACT
    report["prohibited_next_actions"] = [
        "reward activation or reward design without a separate authorization",
        "actor/critic/FiLM/GRU redesign",
        "natural-renewal Stage 2 or H100",
        "training or environment changes",
    ]
    json_path = run_root / "r27_g2_forced_trajectory_effect.json"
    md_path = run_root / "r27_g2_forced_trajectory_effect.md"
    json_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(_markdown(report), encoding="utf-8")
    return report


def run_validate_reset(args: argparse.Namespace) -> dict[str, Any]:
    manifest_path = Path(args.manifest)
    manifest = _read_json(manifest_path)
    checkpoint_id = str(args.checkpoint_id)
    reset_id = int(args.reset_id)
    if checkpoint_id not in REGISTERED_CHECKPOINTS:
        raise R27G2ContractError("reset validation checkpoint is unregistered")
    registered = REGISTERED_CHECKPOINTS[checkpoint_id]
    status = str(manifest.get("status", ""))
    if status not in {"OK", "EXCLUDED", "INVALID"}:
        raise R27G2ContractError(f"reset scientific status is invalid: {status!r}")
    if manifest.get("checkpoint_id") != checkpoint_id:
        raise R27G2ContractError("reset manifest checkpoint_id mismatch")
    if int(manifest.get("checkpoint_update", -1)) != int(registered["update"]):
        raise R27G2ContractError("reset manifest checkpoint update mismatch")
    if int(manifest.get("reset_id", -1)) != reset_id:
        raise R27G2ContractError("reset manifest reset_id mismatch")
    if not _path_matches_registered(
        str(manifest.get("checkpoint_path", "")), str(registered["path"])
    ):
        raise R27G2ContractError("reset manifest checkpoint path mismatch")
    if manifest.get("checkpoint_file_nonempty") is not True:
        raise R27G2ContractError("reset manifest checkpoint is missing or empty")
    if manifest.get("scientific_contract") != SCIENTIFIC_CONTRACT:
        raise R27G2ContractError("reset manifest scientific contract mismatch")
    if str(manifest.get("device", "")).lower() != "cuda":
        raise R27G2ContractError("reset manifest device is not exact CUDA")
    artifact_name = manifest.get("artifact")
    if not artifact_name:
        if status != "INVALID":
            raise R27G2ContractError("non-invalid reset is missing its artifact")
        evidence_failures = _status_evidence_failures(
            manifest, None, context=f"reset {reset_id}"
        )
        if evidence_failures:
            raise R27G2ContractError("; ".join(evidence_failures))
        return {
            "valid": True,
            "scientific_status": status,
            "checkpoint_id": checkpoint_id,
            "reset_id": reset_id,
            "artifact": None,
        }
    if str(artifact_name) != f"reset_{reset_id:04d}.npz":
        raise R27G2ContractError("reset artifact path/name mismatch")
    artifact_path = manifest_path.parent / str(artifact_name)
    if not artifact_path.is_file() or artifact_path.stat().st_size <= 0:
        raise R27G2ContractError("reset artifact is missing or empty")
    artifact = R27G2ResetArtifact.read(artifact_path)
    if int(artifact.reset_id) != reset_id:
        raise R27G2ContractError("reset artifact identity mismatch")
    evidence_failures = _status_evidence_failures(
        manifest, artifact, context=f"reset {reset_id}"
    )
    if evidence_failures:
        raise R27G2ContractError("; ".join(evidence_failures))
    if status in {"OK", "EXCLUDED"}:
        if manifest.get("module_state_equal") is not True:
            raise R27G2ContractError(f"{status} reset module mutation flag")
        if manifest.get("value_norm_state_equal") is not True:
            raise R27G2ContractError(f"{status} reset ValueNorm mutation flag")
        if manifest.get("loaded_value_norm_equal") is not True:
            raise R27G2ContractError(f"{status} reset loaded ValueNorm mismatch")
    return {
        "valid": True,
        "scientific_status": status,
        "checkpoint_id": checkpoint_id,
        "reset_id": reset_id,
        "artifact": str(artifact_path),
    }


def run_validate_aggregate(args: argparse.Namespace) -> dict[str, Any]:
    """Validate an aggregate just rebuilt from the current reset inventory.

    Use ``validate-run`` for a standalone custody check; it rebuilds first.
    """

    run_root = Path(args.run_root)
    json_path = run_root / "r27_g2_forced_trajectory_effect.json"
    markdown_path = run_root / "r27_g2_forced_trajectory_effect.md"
    report = _read_json(json_path)
    if not markdown_path.is_file() or markdown_path.stat().st_size <= 0:
        raise R27G2ContractError("aggregate Markdown report is missing or empty")
    if markdown_path.read_text(encoding="utf-8") != _markdown(report):
        raise R27G2ContractError("aggregate Markdown report does not match JSON")
    if report.get("scientific_contract") != SCIENTIFIC_CONTRACT:
        raise R27G2ContractError("aggregate scientific contract mismatch")
    status = str(report.get("status", ""))
    classification = str(report.get("classification", ""))
    if status not in {"PASS", "FAIL", "MIXED", "INVALID", "UNDERPOWERED"}:
        raise R27G2ContractError(f"aggregate scientific status is invalid: {status!r}")
    if classification not in {
        "INVALID",
        "UNDERPOWERED",
        "PASS_BEHAVIOR_EFFECT",
        "PASS_BEHAVIOR_NO_STABLE_EFFECT",
        "FAIL_BEHAVIOR_FAMILY",
        "MIXED_TEMPORAL_INSTABILITY",
    }:
        raise R27G2ContractError(
            f"aggregate classification is invalid: {classification!r}"
        )
    valid_combinations = {
        ("INVALID", "INVALID"),
        ("UNDERPOWERED", "UNDERPOWERED"),
        ("PASS", "PASS_BEHAVIOR_EFFECT"),
        ("PASS", "PASS_BEHAVIOR_NO_STABLE_EFFECT"),
        ("FAIL", "FAIL_BEHAVIOR_FAMILY"),
        ("MIXED", "MIXED_TEMPORAL_INSTABILITY"),
    }
    if (status, classification) not in valid_combinations:
        raise R27G2ContractError(
            "aggregate status/classification combination is invalid"
        )
    checkpoints = report.get("checkpoints")
    if not isinstance(checkpoints, list) or [
        item.get("checkpoint_id") for item in checkpoints if isinstance(item, dict)
    ] != list(CHECKPOINT_IDS):
        raise R27G2ContractError("aggregate checkpoint inventory/order mismatch")
    reset_evidence_count = _validate_reset_inventory(run_root)
    if report.get("reset_evidence_count") != reset_evidence_count:
        raise R27G2ContractError("aggregate reset-evidence count mismatch")
    return {
        "valid": True,
        "scientific_status": status,
        "classification": classification,
        "json": str(json_path),
        "markdown": str(markdown_path),
    }


def run_validate_run(args: argparse.Namespace) -> dict[str, Any]:
    """Revalidate every reset, rebuild the aggregate, then validate its reports."""

    run_root = Path(args.run_root)
    status_counts = {"OK": 0, "EXCLUDED": 0, "INVALID": 0}
    validated_resets = 0
    for checkpoint_id in CHECKPOINT_IDS:
        for reset_id in range(64):
            reset_dir = (
                run_root
                / checkpoint_id
                / "resets"
                / f"reset_{reset_id:02d}"
            )
            result = run_validate_reset(
                argparse.Namespace(
                    manifest=str(reset_dir / "reset_manifest.json"),
                    checkpoint_id=checkpoint_id,
                    reset_id=reset_id,
                )
            )
            status = str(result["scientific_status"])
            status_counts[status] += 1
            validated_resets += 1
    run_aggregate(
        argparse.Namespace(
            run_root=str(run_root),
            checkpoint_ids=list(CHECKPOINT_IDS),
            gate_a_valid_repetition_checkpoints=list(
                getattr(args, "gate_a_valid_repetition_checkpoints", [])
            ),
        )
    )
    aggregate = run_validate_aggregate(
        argparse.Namespace(run_root=str(run_root))
    )
    return {
        "valid": True,
        "validated_resets": validated_resets,
        "reset_status_counts": status_counts,
        "scientific_status": aggregate["scientific_status"],
        "classification": aggregate["classification"],
        "json": aggregate["json"],
        "markdown": aggregate["markdown"],
    }


def _add_source_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--checkpoint-id", required=True, choices=CHECKPOINT_IDS)
    parser.add_argument("--checkpoint-update", required=True, type=int)
    parser.add_argument("--config", default="ha_ctse_process.config")
    parser.add_argument("--scenario", default="energy")
    parser.add_argument("--preset", default="S7-S1")
    parser.add_argument("--n-agents", dest="n_agents", type=int, default=6)
    parser.add_argument("--device", default="cuda")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Frozen R27-G2 forced-z trajectory/effect intervention"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    collect = subparsers.add_parser("collect-reset")
    _add_source_args(collect)
    collect.add_argument("--reset-id", required=True, type=int)
    collect.add_argument("--output-dir", required=True)
    aggregate = subparsers.add_parser("aggregate")
    aggregate.add_argument("--run-root", required=True)
    aggregate.add_argument("--checkpoint-ids", nargs="+", required=True)
    aggregate.add_argument(
        "--gate-a-valid-repetition-checkpoints",
        nargs="*",
        choices=CHECKPOINT_IDS,
        default=[],
        help=(
            "Only for the one permitted unchanged-contract Gate-A "
            "instrumentation repetition; omitted for the initial run."
        ),
    )
    validate_reset = subparsers.add_parser("validate-reset")
    validate_reset.add_argument("--manifest", required=True)
    validate_reset.add_argument(
        "--checkpoint-id", required=True, choices=CHECKPOINT_IDS
    )
    validate_reset.add_argument("--reset-id", required=True, type=int)
    validate_aggregate = subparsers.add_parser("validate-aggregate")
    validate_aggregate.add_argument("--run-root", required=True)
    validate_run = subparsers.add_parser("validate-run")
    validate_run.add_argument("--run-root", required=True)
    validate_run.add_argument(
        "--gate-a-valid-repetition-checkpoints",
        nargs="*",
        choices=CHECKPOINT_IDS,
        default=[],
    )
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def main() -> None:
    args = parse_args()
    if args.command == "collect-reset":
        result = run_collect_reset(args)
    elif args.command == "aggregate":
        result = run_aggregate(args)
    elif args.command == "validate-reset":
        result = run_validate_reset(args)
    elif args.command == "validate-aggregate":
        result = run_validate_aggregate(args)
    else:
        result = run_validate_run(args)
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
