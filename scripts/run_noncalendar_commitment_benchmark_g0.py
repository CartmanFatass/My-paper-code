"""Package EVENT_HELD_COMMITMENT_LINK_G0 contract, smoke, train, eval, analysis."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process.event_held_commitment_link import (
    ArmName,
    CREATE,
    KEEP,
    RENEW,
    RNG_NAMES,
    authoritative_seed_map,
    collect_trajectory,
    compare_continuations,
    factor_counts,
    initialize_arms,
    load_checkpoint,
    make_training_state,
    nested_state_maximum_difference,
    optimize_update,
    parameter_and_optimizer_counts,
    replay_errors,
    replay_trajectory,
    runtime_rng_snapshot,
    save_checkpoint,
    validate_replay,
)
from ha_ctse_process.noncalendar_commitment_testbed import (
    BOOTSTRAP_REPETITIONS,
    BOOTSTRAP_SEED,
    FORMAL_EVAL_EPISODES,
    FORMAL_UPDATES,
    HORIZON,
    REGISTERED_CONTRACT,
    registered_contract,
    select_result_branch,
)

FORMAL_AUTHORIZATION = "AUTHORIZE_EVENT_HELD_COMMITMENT_LINK_G0_FORMAL"
TRAIN_MANIFEST_SCHEMA = 1
EVALUATION_CELL_SCHEMA = 1
ARMS: tuple[ArmName, ...] = ("OR", "DUM", "EHC")
EVALUATION_CELLS = (
    ("iid", True, "iid_deterministic"),
    ("iid", False, "iid_stochastic"),
    ("held_out", True, "held_out_deterministic"),
    ("held_out", False, "held_out_stochastic"),
)


def _require_cuda(device_name: str) -> torch.device:
    if device_name != "cuda":
        raise ValueError("focused and formal execution requires --device cuda")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required; CPU fallback is forbidden")
    return torch.device("cuda")


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict): return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [_json_ready(v) for v in value]
    if isinstance(value, np.ndarray): return value.tolist()
    if isinstance(value, np.generic): return value.item()
    if isinstance(value, torch.Tensor): return value.detach().cpu().tolist()
    if hasattr(value, "__dict__"): return _json_ready(vars(value))
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_json_ready(value), indent=2, ensure_ascii=False), encoding="utf-8")


def _owned_rng_equal(left: Any, right: Any, names: tuple[str, ...]) -> bool:
    return all(
        repr(left.rngs[name].bit_generator.state)
        == repr(right.rngs[name].bit_generator.state)
        for name in names
    )


def _no_op_equal(ordinary: Any, dummy: Any) -> bool:
    return all(
        torch.equal(getattr(ordinary, name), getattr(dummy, name))
        for name in (
            "observations", "active_mask", "orders", "actions",
            "old_log_probs", "old_values", "hidden_before", "hidden_after",
            "prefix_counts", "rewards", "terminal",
        )
    )


def validate_operational_records(
    training_manifest: dict[str, Any],
    evaluation_payloads: dict[tuple[int, str, str], dict[str, Any]],
    *,
    expected_replicates: tuple[int, ...] = tuple(range(5)),
) -> tuple[bool, list[str]]:
    """Fail-closed validation of all conclusion-bearing operational evidence."""

    errors: list[str] = []
    if set(training_manifest) != {
        "schema_version", "contract", "mode", "replicates"
    }:
        errors.append("training_manifest_schema")
    if training_manifest.get("schema_version") != TRAIN_MANIFEST_SCHEMA:
        errors.append("training_manifest_version")
    if training_manifest.get("contract") != registered_contract():
        errors.append("training_manifest_contract")
    if training_manifest.get("mode") != "formal_train":
        errors.append("training_manifest_mode")
    replicates = training_manifest.get("replicates", {})
    if set(replicates) != {str(value) for value in expected_replicates}:
        errors.append("training_replicate_set")
    for replicate in expected_replicates:
        record = replicates.get(str(replicate), {})
        if set(record) != {"operational", "updates", "arms"}:
            errors.append(f"training_record_schema:{replicate}")
            continue
        operational = record.get("operational", {})
        required_families = {
            "no_op", "probability_replay", "lifecycle", "finiteness",
            "rng_pairing", "checkpoint_resume", "exposure",
        }
        if set(operational) != required_families or not all(
            operational.get(name) is True for name in required_families
        ):
            errors.append(f"training_operational:{replicate}")
        if len(record.get("updates", [])) != FORMAL_UPDATES:
            errors.append(f"training_update_count:{replicate}")
        arms = record.get("arms", {})
        if set(arms) != set(ARMS):
            errors.append(f"training_arm_set:{replicate}")
            continue
        for arm in ARMS:
            entry = arms[arm]
            expected_event = 0 if arm == "OR" else 1000
            if (
                entry.get("arm") != arm
                or entry.get("replicate") != replicate
                or entry.get("checkpoint_origin") != "update_250.pt"
                or entry.get("completed_update") != 250
                or entry.get("next_episode_id") != 4000
                or entry.get("base_steps") != 1000
                or entry.get("event_steps") != expected_event
                or entry.get("seed_map") != authoritative_seed_map("train", replicate)
                or entry.get("checkpoint_resume") is not True
            ):
                errors.append(f"training_arm_evidence:{replicate}:{arm}")

    expected_keys = {
        (replicate, arm, cell)
        for replicate in expected_replicates
        for arm in ARMS
        for _profile, _deterministic, cell in EVALUATION_CELLS
    }
    if set(evaluation_payloads) != expected_keys:
        errors.append("evaluation_artifact_set")
    for replicate in expected_replicates:
        for profile, deterministic, cell in EVALUATION_CELLS:
            paired_ids: tuple[int, ...] | None = None
            for arm in ARMS:
                payload = evaluation_payloads.get((replicate, arm, cell), {})
                required = {
                    "schema_version", "contract", "arm", "replicate", "cell",
                    "profile", "mode", "checkpoint", "checkpoint_origin",
                    "counts", "seed_map", "replay", "operational", "episodes",
                }
                if set(payload) != required:
                    errors.append(f"evaluation_schema:{replicate}:{arm}:{cell}")
                    continue
                expected_mode = "deterministic" if deterministic else "stochastic"
                counts = payload.get("counts", {})
                operational = payload.get("operational", {})
                training_checkpoint = (
                    replicates.get(str(replicate), {})
                    .get("arms", {}).get(arm, {}).get("checkpoint")
                )
                if (
                    payload.get("schema_version") != EVALUATION_CELL_SCHEMA
                    or payload.get("contract") != registered_contract()
                    or payload.get("arm") != arm
                    or payload.get("replicate") != replicate
                    or payload.get("cell") != cell
                    or payload.get("profile") != profile
                    or payload.get("mode") != expected_mode
                    or payload.get("checkpoint_origin") != "update_250.pt"
                    or payload.get("checkpoint") != training_checkpoint
                    or counts != {"episodes": FORMAL_EVAL_EPISODES, "horizon": HORIZON}
                    or payload.get("seed_map") != authoritative_seed_map(profile, replicate)
                    or set(operational) != {"probability_replay", "lifecycle", "rng", "checkpoint", "finite"}
                    or not all(value is True for value in operational.values())
                    or float(payload.get("replay", {}).get("maximum_error", float("inf"))) > 1e-6
                ):
                    errors.append(f"evaluation_operational:{replicate}:{arm}:{cell}")
                episode_ids = tuple(
                    int(value.get("episode_id", -1))
                    for value in payload.get("episodes", [])
                )
                if episode_ids != tuple(range(FORMAL_EVAL_EPISODES)):
                    errors.append(f"evaluation_episode_ids:{replicate}:{arm}:{cell}")
                if paired_ids is None:
                    paired_ids = episode_ids
                elif episode_ids != paired_ids:
                    errors.append(f"evaluation_pairing:{replicate}:{cell}")
    return not errors, errors


def _lifecycle_valid(trajectory: Any, arm: ArmName) -> bool:
    counts = factor_counts(trajectory)
    if arm == "OR":
        return all(value == 0 for value in counts.values())
    return bool(
        counts["categorical"] == counts["keep"] + counts["renew"]
        and counts["mark"] == counts["create"] + counts["renew"]
        and all(record.active_lifetime >= 1 for rows in trajectory.segments for record in rows)
    )


def run_smoke(output_root: Path, *, device_name: str = "cuda") -> dict[str, Any]:
    """One real, bounded, explicitly non-formal CUDA package exercise."""

    device = _require_cuda(device_name)
    arms, base_optimizers, event_optimizers = initialize_arms(device)
    states = {name: make_training_state(name, 0) for name in ARMS}
    evidence: dict[str, Any] = {}
    trajectories: dict[str, Any] = {}
    for name in ARMS:
        arm = arms[name]
        trajectory = collect_trajectory(
            arm, states[name], device=device, episode_ids=(0,)
        )
        trajectories[name] = trajectory
        _replay, replay = validate_replay(arm, trajectory, device=device)
        update = optimize_update(
            arm, base_optimizers[name], event_optimizers[name],
            states[name], trajectory, device=device,
        )
        checkpoint = output_root / "checkpoints" / name / "smoke_update_001.pt"
        save_checkpoint(
            checkpoint, arm=arm, base_optimizer=base_optimizers[name],
            event_optimizer=event_optimizers[name], state=states[name],
        )
        loaded_arm, loaded_base, loaded_event, loaded_state = load_checkpoint(
            checkpoint, device=device, expected_arm=name, expected_replicate=0
        )
        evidence[name] = {
            "replay": replay,
            "update": update,
            "factors": factor_counts(trajectory),
            "lifecycle_valid": _lifecycle_valid(trajectory, name),
            "counts": parameter_and_optimizer_counts(
                arm, base_optimizers[name], event_optimizers[name]
            ),
            "checkpoint_model_error": nested_state_maximum_difference(
                arm.state_dict(), loaded_arm.state_dict()
            ),
            "checkpoint_base_optimizer_error": nested_state_maximum_difference(
                base_optimizers[name].state_dict(), loaded_base.state_dict()
            ),
            "checkpoint_event_optimizer_error": nested_state_maximum_difference(
                None if event_optimizers[name] is None else event_optimizers[name].state_dict(),
                None if loaded_event is None else loaded_event.state_dict(),
            ),
            "checkpoint_state_equal": (
                states[name].completed_update == loaded_state.completed_update
                and states[name].next_episode_id == loaded_state.next_episode_id
                and states[name].base_optimizer_steps == loaded_state.base_optimizer_steps
                and states[name].event_optimizer_steps == loaded_state.event_optimizer_steps
            ),
            "artifact": str(checkpoint),
        }
    no_op = _no_op_equal(trajectories["OR"], trajectories["DUM"])

    checkpoint = output_root / "checkpoints" / "EHC" / "continuation_origin.pt"
    save_checkpoint(
        checkpoint, arm=arms["EHC"], base_optimizer=base_optimizers["EHC"],
        event_optimizer=event_optimizers["EHC"], state=states["EHC"],
    )
    left_arm, left_base, left_event, left_state = load_checkpoint(
        checkpoint, device=device, expected_arm="EHC", expected_replicate=0
    )
    left_trajectory = collect_trajectory(
        left_arm, left_state, device=device, episode_ids=(1,)
    )
    optimize_update(
        left_arm, left_base, left_event, left_state,
        left_trajectory, device=device,
    )
    left_global_rng = runtime_rng_snapshot()

    right_arm, right_base, right_event, right_state = load_checkpoint(
        checkpoint, device=device, expected_arm="EHC", expected_replicate=0
    )
    right_trajectory = collect_trajectory(
        right_arm, right_state, device=device, episode_ids=(1,)
    )
    optimize_update(
        right_arm, right_base, right_event, right_state,
        right_trajectory, device=device,
    )
    right_global_rng = runtime_rng_snapshot()
    continuation = compare_continuations(
        left_arm, right_arm, left_trajectory, right_trajectory,
        left_base, right_base, left_event, right_event,
        left_state, right_state, left_global_rng, right_global_rng,
    )
    result = {
        "mode": "non_formal_smoke",
        "device": str(device),
        "registered_contract": REGISTERED_CONTRACT,
        "formal": False,
        "arms": evidence,
        "or_dum_no_op": no_op,
        "continuation": continuation,
    }
    _write_json(output_root / "smoke_result.json", result)
    return result


def formal_train(
    output_root: Path, *, device_name: str, authorization: str
) -> dict[str, Any]:
    if authorization != FORMAL_AUTHORIZATION:
        raise PermissionError("formal train requires the exact authorization token")
    device = _require_cuda(device_name)
    manifest: dict[str, Any] = {
        "schema_version": TRAIN_MANIFEST_SCHEMA,
        "contract": registered_contract(),
        "mode": "formal_train",
        "replicates": {},
    }
    for replicate in range(5):
        arms, base_optimizers, event_optimizers = initialize_arms(
            device, replicate=replicate
        )
        states = {arm: make_training_state(arm, replicate) for arm in ARMS}
        update_evidence: list[dict[str, Any]] = []
        all_operational = {
            "no_op": True,
            "probability_replay": True,
            "lifecycle": True,
            "finiteness": True,
            "rng_pairing": True,
            "checkpoint_resume": True,
            "exposure": True,
        }
        for update_index in range(FORMAL_UPDATES):
            trajectories = {
                arm: collect_trajectory(
                    arms[arm], states[arm], device=device
                )
                for arm in ARMS
            }
            no_op = _no_op_equal(trajectories["OR"], trajectories["DUM"])
            rng_pairing = bool(
                _owned_rng_equal(
                    states["OR"], states["DUM"],
                    ("ledger", "order", "primitive"),
                )
                and _owned_rng_equal(
                    states["DUM"], states["EHC"],
                    ("ledger", "order", "primitive", "opportunity", "event", "mark"),
                )
            )
            lifecycle = all(
                _lifecycle_valid(trajectories[arm], arm) for arm in ARMS
            )
            update_metrics = {
                arm: optimize_update(
                    arms[arm], base_optimizers[arm], event_optimizers[arm],
                    states[arm], trajectories[arm], device=device,
                )
                for arm in ARMS
            }
            replay_maximum = max(
                max(metrics["replay"].values())
                for metrics in update_metrics.values()
            )
            finite = all(metrics["finite"] for metrics in update_metrics.values())
            exposure = all(
                metrics["base_steps"] == 4
                and metrics["primitive_replays"] == 4
                and metrics["packed_trajectory_count"] == 1
                and metrics["event_steps"] == (0 if arm == "OR" else 4)
                for arm, metrics in update_metrics.items()
            )
            base_noop_error = nested_state_maximum_difference(
                arms["OR"].base.state_dict(), arms["DUM"].base.state_dict()
            )
            no_op = no_op and base_noop_error == 0.0
            current = {
                "update": update_index + 1,
                "no_op": no_op,
                "base_noop_error": base_noop_error,
                "replay_maximum": replay_maximum,
                "lifecycle": lifecycle,
                "finite": finite,
                "rng_pairing": rng_pairing,
                "exposure": exposure,
            }
            update_evidence.append(current)
            all_operational["no_op"] &= no_op
            all_operational["probability_replay"] &= replay_maximum <= 1e-6
            all_operational["lifecycle"] &= lifecycle
            all_operational["finiteness"] &= finite
            all_operational["rng_pairing"] &= rng_pairing
            all_operational["exposure"] &= exposure
            if not all(
                (no_op, replay_maximum <= 1e-6, lifecycle, finite, rng_pairing, exposure)
            ):
                raise RuntimeError(f"formal training operational failure {current}")

        arm_records: dict[str, Any] = {}
        for arm in ARMS:
            checkpoint = (
                output_root / "train" / f"replicate_{replicate}"
                / arm / "update_250.pt"
            )
            save_checkpoint(
                checkpoint, arm=arms[arm], base_optimizer=base_optimizers[arm],
                event_optimizer=event_optimizers[arm], state=states[arm],
            )
            loaded_arm, loaded_base, loaded_event, loaded_state = load_checkpoint(
                checkpoint, device=device, expected_arm=arm,
                expected_replicate=replicate, formal_evaluation=True,
            )
            resume_valid = bool(
                nested_state_maximum_difference(
                    arms[arm].state_dict(), loaded_arm.state_dict()
                ) == 0.0
                and nested_state_maximum_difference(
                    base_optimizers[arm].state_dict(), loaded_base.state_dict()
                ) == 0.0
                and nested_state_maximum_difference(
                    None if event_optimizers[arm] is None else event_optimizers[arm].state_dict(),
                    None if loaded_event is None else loaded_event.state_dict(),
                ) == 0.0
                and loaded_state.completed_update == FORMAL_UPDATES
                and loaded_state.next_episode_id == 4000
            )
            all_operational["checkpoint_resume"] &= resume_valid
            arm_records[arm] = {
                "arm": arm,
                "replicate": replicate,
                "checkpoint": str(checkpoint),
                "checkpoint_origin": "update_250.pt",
                "completed_update": states[arm].completed_update,
                "next_episode_id": states[arm].next_episode_id,
                "base_steps": states[arm].base_optimizer_steps,
                "event_steps": states[arm].event_optimizer_steps,
                "seed_map": dict(states[arm].seed_map),
                "checkpoint_resume": resume_valid,
            }
        if not all(all_operational.values()):
            raise RuntimeError(
                f"formal training terminal operational failure {all_operational}"
            )
        manifest["replicates"][str(replicate)] = {
            "operational": all_operational,
            "updates": update_evidence,
            "arms": arm_records,
        }
    _write_json(output_root / "train_manifest.json", manifest)
    return manifest


def _evaluation_state(
    arm: ArmName, replicate: int, *, profile: str
) -> Any:
    if profile not in ("iid", "held_out"):
        raise ValueError("formal evaluation profile must be iid or held_out")
    return make_training_state(arm, replicate, profile=profile)

def _trajectory_episode_rows(trajectory: Any, arm: Any) -> list[dict[str, Any]]:
    rows = []
    for env_index, outcome in enumerate(trajectory.outcomes):
        kinds = trajectory.event_kind[:, env_index]
        active = trajectory.active_mask[:, env_index]
        intervention: list[float] = []
        if arm.arm == "EHC" and arm.W_z is not None:
            with torch.no_grad():
                for time in range(trajectory.time_steps):
                    keys = torch.flatnonzero(active[time])
                    if len(keys) >= 2:
                        z = trajectory.primitive_z[time, keys].to(next(arm.parameters()).device); perm = torch.roll(z, 1, 0); values = arm.W_z(z - perm).norm(dim=-1) / math.sqrt(3.0); intervention.extend(values.detach().cpu().tolist())
        segments = [vars(v) | {"active_lifetime": v.active_lifetime} for v in trajectory.segments[env_index]]
        rows.append({"episode_id": trajectory.ledger_ids[env_index], "utility": outcome.utility, "keep": int((kinds == KEEP).sum()), "renew": int((kinds == RENEW).sum()), "non_create": int(((kinds == KEEP) | (kinds == RENEW)).sum()), "multi_opportunity_lifecycles": int(sum(int((((kinds == KEEP) | (kinds == RENEW))[:, key]).sum()) >= 2 for key in range(kinds.shape[-1]))), "segments": segments, "intervention": intervention})
    return rows


def formal_evaluate(
    output_root: Path, *, device_name: str, authorization: str
) -> dict[str, Any]:
    if authorization != FORMAL_AUTHORIZATION:
        raise PermissionError("formal evaluation requires the exact authorization token")
    device = _require_cuda(device_name)
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "contract": registered_contract(),
        "mode": "formal_evaluate",
        "artifacts": {},
    }
    for replicate in range(5):
        for arm_name in ARMS:
            checkpoint = (
                output_root / "train" / f"replicate_{replicate}"
                / arm_name / "update_250.pt"
            )
            arm, _, _, checkpoint_state = load_checkpoint(
                checkpoint, device=device, expected_arm=arm_name,
                expected_replicate=replicate, formal_evaluation=True,
            )
            for profile, deterministic, cell in EVALUATION_CELLS:
                state = _evaluation_state(
                    arm_name, replicate, profile=profile
                )
                episode_rows: list[dict[str, Any]] = []
                replay_maximum = 0.0
                lifecycle_valid = True
                finite = True
                for start in range(0, FORMAL_EVAL_EPISODES, 16):
                    trajectory = collect_trajectory(
                        arm, state, device=device,
                        episode_ids=range(start, start + 16),
                        deterministic=deterministic, profile=profile,
                    )
                    _replay, errors = validate_replay(
                        arm, trajectory, device=device
                    )
                    replay_maximum = max(replay_maximum, max(errors.values()))
                    lifecycle_valid &= _lifecycle_valid(trajectory, arm_name)
                    finite &= all(
                        bool(torch.isfinite(getattr(trajectory, name)).all().detach().cpu())
                        for name in (
                            "old_log_probs", "old_values", "hidden_after",
                            "event_old_joint_logp",
                        )
                    )
                    episode_rows.extend(
                        _trajectory_episode_rows(trajectory, arm)
                    )
                operational = {
                    "probability_replay": replay_maximum <= 1e-6,
                    "lifecycle": lifecycle_valid,
                    "rng": (
                        state.seed_map
                        == authoritative_seed_map(profile, replicate)
                        and set(state.rngs) == set(RNG_NAMES)
                    ),
                    "checkpoint": (
                        checkpoint_state.completed_update == 250
                        and checkpoint_state.next_episode_id == 4000
                    ),
                    "finite": finite,
                }
                if not all(operational.values()):
                    raise RuntimeError(
                        f"formal evaluation operational failure "
                        f"{replicate}:{arm_name}:{cell}:{operational}"
                    )
                payload = {
                    "schema_version": EVALUATION_CELL_SCHEMA,
                    "contract": registered_contract(),
                    "arm": arm_name,
                    "replicate": replicate,
                    "cell": cell,
                    "profile": profile,
                    "mode": "deterministic" if deterministic else "stochastic",
                    "checkpoint": str(checkpoint),
                    "checkpoint_origin": "update_250.pt",
                    "counts": {
                        "episodes": len(episode_rows),
                        "horizon": HORIZON,
                    },
                    "seed_map": authoritative_seed_map(profile, replicate),
                    "replay": {"maximum_error": replay_maximum},
                    "operational": operational,
                    "episodes": episode_rows,
                }
                path = (
                    output_root / "evaluation" / f"replicate_{replicate}"
                    / arm_name / f"{cell}.json"
                )
                _write_json(path, payload)
                manifest["artifacts"][f"{replicate}:{arm_name}:{cell}"] = str(path)
    _write_json(output_root / "evaluation_manifest.json", manifest)
    return manifest

def _percentile(values: list[float]) -> tuple[float, float]:
    return float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))


def aggregate_analysis(
    output_root: Path, *, authorization: str
) -> dict[str, Any]:
    if authorization != FORMAL_AUTHORIZATION:
        raise PermissionError("formal analysis requires the exact authorization token")
    training_manifest = json.loads(
        (output_root / "train_manifest.json").read_text(encoding="utf-8")
    )
    evaluation_payloads: dict[tuple[int, str, str], dict[str, Any]] = {}
    for replicate in range(5):
        for arm in ARMS:
            for _profile, _deterministic, cell in EVALUATION_CELLS:
                path = (
                    output_root / "evaluation" / f"replicate_{replicate}"
                    / arm / f"{cell}.json"
                )
                if path.is_file():
                    evaluation_payloads[(replicate, arm, cell)] = json.loads(
                        path.read_text(encoding="utf-8")
                    )
    operational_valid, operational_errors = validate_operational_records(
        training_manifest, evaluation_payloads
    )
    if not operational_valid:
        inputs = {
            "operational_valid": False,
            "non_create_opportunities": 0,
            "multi_opportunity_lifecycles": 0,
            "utility_ci": {arm: (0.0, 0.0) for arm in ARMS},
            "g_ci": (0.0, 0.0),
            "keep_ci": (0.0, 0.0),
            "renew_ci": (0.0, 0.0),
            "cv_ci": (0.0, 0.0),
            "lifetime_bin_cis": [(0.0, 0.0)] * 3,
            "intervention_ci": (0.0, 0.0),
        }
        result = {
            "branch": select_result_branch(**inputs),
            "predicate_inputs": inputs,
            "operational_errors": operational_errors,
            "registered_contract": REGISTERED_CONTRACT,
        }
        _write_json(output_root / "analysis_result.json", result)
        return result

    data = {
        (replicate, arm): evaluation_payloads[
            (replicate, arm, "held_out_stochastic")
        ]["episodes"]
        for replicate in range(5)
        for arm in ARMS
    }
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    utilities = {arm: [] for arm in ARMS}
    gains: list[float] = []
    secondary_gains: list[float] = []
    keep_values: list[float] = []
    renew_values: list[float] = []
    cv_values: list[float] = []
    bin_values: list[list[float]] = [[], [], []]
    intervention_values: list[float] = []
    for _ in range(BOOTSTRAP_REPETITIONS):
        sampled_replicates = rng.integers(0, 5, size=5)
        sampled: dict[str, list[dict[str, Any]]] = {arm: [] for arm in ARMS}
        for replicate in sampled_replicates:
            episode_indices = rng.integers(
                0, FORMAL_EVAL_EPISODES, size=FORMAL_EVAL_EPISODES
            )
            for arm in ARMS:
                sampled[arm].extend(
                    data[(int(replicate), arm)][int(index)]
                    for index in episode_indices
                )
        means = {
            arm: float(np.mean([row["utility"] for row in rows]))
            for arm, rows in sampled.items()
        }
        for arm in ARMS:
            utilities[arm].append(means[arm])
        gains.append(means["EHC"] - means["DUM"])
        secondary_gains.append(means["EHC"] - means["OR"])
        ehc = sampled["EHC"]
        keep = sum(row["keep"] for row in ehc)
        renew = sum(row["renew"] for row in ehc)
        opportunities = keep + renew
        keep_values.append(keep / max(opportunities, 1))
        renew_values.append(renew / max(opportunities, 1))
        lifetimes = [
            segment["active_lifetime"]
            for row in ehc for segment in row["segments"]
            if not segment["censored"]
        ]
        cv_values.append(
            float(np.std(lifetimes) / max(np.mean(lifetimes), 1e-12))
            if lifetimes else 0.0
        )
        for index, (low, high) in enumerate(
            ((1, 8), (9, 16), (17, float("inf")))
        ):
            bin_values[index].append(
                sum(low <= value <= high for value in lifetimes)
                / max(len(lifetimes), 1)
            )
        intervention = [value for row in ehc for value in row["intervention"]]
        intervention_values.append(
            float(np.mean(intervention)) if intervention else 0.0
        )
    utility_ci = {
        arm: _percentile(values) for arm, values in utilities.items()
    }
    ehc_rows = [
        row for replicate in range(5) for row in data[(replicate, "EHC")]
    ]
    inputs = {
        "operational_valid": True,
        "non_create_opportunities": sum(
            row["non_create"] for row in ehc_rows
        ),
        "multi_opportunity_lifecycles": sum(
            row["multi_opportunity_lifecycles"] for row in ehc_rows
        ),
        "utility_ci": utility_ci,
        "g_ci": _percentile(gains),
        "keep_ci": _percentile(keep_values),
        "renew_ci": _percentile(renew_values),
        "cv_ci": _percentile(cv_values),
        "lifetime_bin_cis": [_percentile(values) for values in bin_values],
        "intervention_ci": _percentile(intervention_values),
    }
    result = {
        "branch": select_result_branch(**inputs),
        "predicate_inputs": inputs,
        "secondary_v_ci": _percentile(secondary_gains),
        "operational_errors": [],
        "registered_contract": REGISTERED_CONTRACT,
    }
    _write_json(output_root / "analysis_result.json", result)
    return result

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(); parser.add_argument("--mode", choices=("contract", "smoke", "train", "evaluate", "analyze"), default="contract"); parser.add_argument("--output-root", type=Path, default=Path("logs/event_held_commitment_link_g0")); parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda"); parser.add_argument("--authorize-formal", default=""); return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.mode == "contract": result = registered_contract()
    elif args.mode == "smoke": result = run_smoke(args.output_root, device_name=args.device)
    elif args.mode == "train": result = formal_train(args.output_root, device_name=args.device, authorization=args.authorize_formal)
    elif args.mode == "evaluate": result = formal_evaluate(args.output_root, device_name=args.device, authorization=args.authorize_formal)
    else: result = aggregate_analysis(args.output_root, authorization=args.authorize_formal)
    print(json.dumps(_json_ready(result), ensure_ascii=False)); return 0


if __name__ == "__main__":
    raise SystemExit(main())
