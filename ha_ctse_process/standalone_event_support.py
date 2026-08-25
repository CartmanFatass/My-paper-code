"""Shared support for variable-roster event training and evaluation.

This module owns event-model/runtime construction, event-only persistence, and
the frozen Stage C evaluation/provenance projections.  It deliberately does
not import :mod:`ha_ctse_process.train`.
"""

from __future__ import annotations

import argparse
import csv
from copy import deepcopy
from dataclasses import fields, is_dataclass
from datetime import datetime
import json
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from ha_ctse_process.standalone_contracts import is_variable_roster_event


def _event_jsonable(value: Any) -> Any:
    """Convert event payload values using the historical train JSON rules."""

    if isinstance(value, np.ndarray):
        return _event_jsonable(value.tolist())
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, (tuple, list)):
        return [_event_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _event_jsonable(item) for key, item in value.items()}
    if isinstance(value, Path):
        return str(value)
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def enforce_variable_roster_event_resume_boundary(config, args: argparse.Namespace) -> None:
    if not is_variable_roster_event(config):
        return
    path = str(getattr(args, "resume_from", "") or "")
    if path and not Path(path).is_file():
        raise ValueError(
            "Stage C --resume_from fails closed because the checkpoint does not "
            f"exist: {path}"
        )


def _write_event_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_event_jsonable(dict(payload)), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    _replace_event_file(temporary, path)


def _replace_event_file(temporary: Path, path: Path) -> None:
    """Bounded Windows fallback for the desktop's transient replace denial."""

    for attempt in range(10):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt == 9:
                path.write_bytes(temporary.read_bytes())
                try:
                    temporary.unlink(missing_ok=True)
                except PermissionError:
                    pass
                return
            time.sleep(0.05)


def _write_event_arm_status(args: argparse.Namespace, **fields: Any) -> None:
    _write_event_json(
        Path(args.log_dir) / "arm_status.json",
        {
            **fields,
            "updated": datetime.now().astimezone().isoformat(timespec="seconds"),
        },
    )


def _write_event_csv_rows(
    path: Path,
    *,
    fieldnames: Sequence[str],
    rows: Sequence[Mapping[str, Any]],
) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        writer.writerows([dict(row) for row in rows])
    _replace_event_file(temporary, path)


def _event_live_checkpoint_paths(
    checkpoint_dir: Path,
    *,
    update_idx: int,
    save_interval: int,
) -> tuple[Path, ...]:
    index = int(update_idx)
    interval = max(int(save_interval), 1)
    paths = [checkpoint_dir / "latest.pt"]
    if index == 0 or index % interval == 0 or index == 250:
        paths.append(checkpoint_dir / f"update_{index:03d}_live.pt")
    return tuple(paths)


def _event_identity_normalizers() -> dict[str, Any]:
    state = {"schema_version": 1, "enabled": False, "kind": "identity"}
    return {"high": deepcopy(state), "low": deepcopy(state)}


def _nested_state_maximum_difference(left: Any, right: Any) -> float:
    if isinstance(left, (torch.Tensor, np.ndarray)) or isinstance(
        right, (torch.Tensor, np.ndarray)
    ):
        lhs = torch.as_tensor(left).detach().cpu()
        rhs = torch.as_tensor(right).detach().cpu()
        if lhs.shape != rhs.shape:
            return float("inf")
        if lhs.numel() == 0:
            return 0.0
        return float(torch.max(torch.abs(lhs.float() - rhs.float())).item())
    if is_dataclass(left) or is_dataclass(right):
        if not (is_dataclass(left) and is_dataclass(right)) or type(left) is not type(
            right
        ):
            return float("inf")
        return _nested_state_maximum_difference(
            {field.name: getattr(left, field.name) for field in fields(left)},
            {field.name: getattr(right, field.name) for field in fields(right)},
        )
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        if set(left) != set(right):
            return float("inf")
        return max(
            (_nested_state_maximum_difference(left[key], right[key]) for key in left),
            default=0.0,
        )
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        if len(left) != len(right):
            return float("inf")
        return max(
            (_nested_state_maximum_difference(a, b) for a, b in zip(left, right)),
            default=0.0,
        )
    return 0.0 if left == right else float("inf")


def _event_state_dict_finite(core) -> bool:
    return all(
        bool(torch.isfinite(tensor).all().item())
        for module in (
            core.commitment_model,
            core.event_critic,
            core.low_actor,
            core.low_critic,
        )
        for tensor in module.state_dict().values()
    )


def _make_event_model_owner(config, device: torch.device):
    from ha_ctse_process.dynamic_roster_testbed import ACTION_COUNT, OBSERVATION_DIM
    from ha_ctse_process.variable_roster_event import VariableRosterEventCore

    return VariableRosterEventCore(
        architecture_mode=str(config.event_architecture_mode),
        obs_dim=OBSERVATION_DIM,
        critic_member_dim=OBSERVATION_DIM,
        critic_global_dim=8,
        n_skills=3,
        action_dim=ACTION_COUNT,
        member_hidden_dim=int(getattr(config, "event_member_hidden_dim", 64)),
        high_hidden_dim=int(getattr(config, "event_high_hidden_dim", 64)),
        low_hidden_dim=int(getattr(config, "event_low_hidden_dim", 64)),
        skill_embedding_dim=int(getattr(config, "event_skill_embedding_dim", 16)),
        gamma=0.99,
        gae_lambda=0.95,
        environment_index=-1,
        device=device,
    )


def _make_event_runtime(
    model_owner,
    *,
    environment_index: int,
    episode_id: int,
    event_master_seed: int,
    action_master_seed: int,
):
    from ha_ctse_process.variable_roster_event import VariableRosterEventCore

    return VariableRosterEventCore(
        architecture_mode=model_owner.architecture_mode,
        obs_dim=model_owner.obs_dim,
        critic_member_dim=model_owner.critic_member_dim,
        critic_global_dim=model_owner.critic_global_dim,
        n_skills=model_owner.n_skills,
        action_dim=model_owner.action_dim,
        member_hidden_dim=model_owner.member_hidden_dim,
        high_hidden_dim=model_owner.high_hidden_dim,
        low_hidden_dim=model_owner.low_hidden_dim,
        skill_embedding_dim=model_owner.skill_embedding_dim,
        gamma=model_owner.gamma,
        gae_lambda=model_owner.gae_lambda,
        environment_index=int(environment_index),
        opportunity_seed=int(event_master_seed),
        frontier_seed=int(event_master_seed),
        action_seed=int(action_master_seed),
        rng_episode_id=int(episode_id),
        opportunity_stream_id=0,
        frontier_stream_id=1,
        action_stream_id=0,
        device=model_owner.device,
        shared_models_from=model_owner,
    )


def _paired_mean_ci(
    values: Sequence[float],
    *,
    seed: int,
    repetitions: int = 10_000,
) -> list[float]:
    array = np.asarray(values, dtype=np.float64).reshape(-1)
    if array.size <= 0 or not np.isfinite(array).all():
        raise ValueError("bootstrap values must be finite and non-empty")
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([int(seed)])))
    draws = np.empty(int(repetitions), dtype=np.float64)
    for index in range(int(repetitions)):
        draws[index] = float(np.mean(array[rng.integers(0, array.size, array.size)]))
    return [
        float(np.quantile(draws, 0.025)),
        float(np.mean(array)),
        float(np.quantile(draws, 0.975)),
    ]


def _event_prefix_rows(core, rows, *, episode_id: int) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        if (
            int(row.physical_event_time) <= 0
            or len(row.frontier) < 2
            or int(row.token_position) <= 0
        ):
            continue
        initial = core.replay_token_distribution(row, summary_source="initial")
        working = core.replay_token_distribution(row, summary_source="working")
        actual_source = "initial" if core.architecture_mode == "f0" else "working"
        replayed_actual = core.replay_token_distribution(
            row, summary_source=actual_source
        )
        action = int(row.combined_action)
        replayed_action_probability = float(replayed_actual[action])
        replayed_action_log_probability = float(
            np.log(max(replayed_action_probability, np.finfo(np.float64).tiny))
        )
        stored_action_log_probability = float(row.old_token_log_probability)
        stored_action_probability = float(np.exp(stored_action_log_probability))
        owner_index = row.active_lifecycle_keys.index(row.owner_lifecycle_key)
        output.append(
            {
                "episode_id": int(episode_id),
                "physical_time": int(row.physical_event_time),
                "token_position": int(row.token_position),
                "owner_index": int(owner_index),
                "owner_incumbent_skill": int(
                    row.pre_token_working_skills[owner_index]
                ),
                "combined_action": action,
                "initial_skills": row.initial_skills.tolist(),
                "working_skills": row.pre_token_working_skills.tolist(),
                "legal_mask": row.exact_legal_mask.tolist(),
                "p_initial": initial.tolist(),
                "p_working": working.tolist(),
                "p_actual_replay": replayed_actual.tolist(),
                "stored_action_log_probability": stored_action_log_probability,
                "replayed_action_log_probability": replayed_action_log_probability,
                "stored_action_probability": stored_action_probability,
                "replayed_action_probability": replayed_action_probability,
                "actual_replay_logp_error": float(
                    abs(replayed_action_log_probability - stored_action_log_probability)
                ),
                "actual_replay_probability_error": float(
                    abs(replayed_action_probability - stored_action_probability)
                ),
                "working_initial_tv": float(0.5 * np.abs(working - initial).sum()),
                "common_support_applied_vs_initial_tv": float(
                    0.5 * np.abs(replayed_actual - initial).sum()
                ),
            }
        )
    return output


def _summarize_event_prefix_rows(
    prefix_rows: Sequence[Mapping[str, Any]],
    *,
    persistent_skill: int,
    architecture_mode: str,
) -> dict[str, Any]:
    replay_logp_max = max(
        (float(row["actual_replay_logp_error"]) for row in prefix_rows),
        default=0.0,
    )
    replay_probability_max = max(
        (float(row["actual_replay_probability_error"]) for row in prefix_rows),
        default=0.0,
    )
    tv_by_episode: dict[int, list[float]] = {}
    direction_by_episode: dict[int, list[float]] = {}
    direction_cases = {
        "no_persistent_in_roster": 0,
        "other_persistent_in_roster": 0,
        "excluded_focal_persistent": 0,
    }
    for row in prefix_rows:
        episode_id = int(row["episode_id"])
        tv_by_episode.setdefault(episode_id, []).append(
            float(row["common_support_applied_vs_initial_tv"])
        )
        working_skills = [int(value) for value in row["working_skills"]]
        owner_index = int(row["owner_index"])
        incumbent = int(row["owner_incumbent_skill"])
        if incumbent == int(persistent_skill):
            direction_cases["excluded_focal_persistent"] += 1
            continue
        p_initial = np.asarray(row["p_initial"], dtype=np.float64)
        p_working = np.asarray(row["p_working"], dtype=np.float64)
        other_skills = [
            skill for index, skill in enumerate(working_skills) if index != owner_index
        ]
        if int(persistent_skill) not in working_skills:
            direction = float(
                p_working[int(persistent_skill)] - p_initial[int(persistent_skill)]
            )
            direction_cases["no_persistent_in_roster"] += 1
        elif int(persistent_skill) in other_skills:
            direction = float(
                p_initial[int(persistent_skill)] - p_working[int(persistent_skill)]
            )
            direction_cases["other_persistent_in_roster"] += 1
        else:
            continue
        direction_by_episode.setdefault(episode_id, []).append(direction)
    tv_episode_means = [
        float(np.mean(tv_by_episode[key])) for key in sorted(tv_by_episode)
    ]
    direction_episode_means = [
        float(np.mean(direction_by_episode[key]))
        for key in sorted(direction_by_episode)
    ]
    return {
        "eligible_natural_rows": len(prefix_rows),
        "actual_replay_logp_max_error": replay_logp_max,
        "actual_replay_probability_max_error": replay_probability_max,
        "directional_eligible_rows": sum(
            len(values) for values in direction_by_episode.values()
        ),
        "directional_case_counts": direction_cases,
        "working_initial_tv_ci95": (
            _paired_mean_ci(tv_episode_means, seed=107_057)
            if tv_episode_means
            else [0.0, 0.0, 0.0]
        ),
        "directional_composition_shift_ci95": (
            _paired_mean_ci(direction_episode_means, seed=107_058)
            if direction_episode_means
            else [0.0, 0.0, 0.0]
        ),
        "f0_common_support_tv_max": (
            max(
                (
                    float(row["common_support_applied_vs_initial_tv"])
                    for row in prefix_rows
                ),
                default=0.0,
            )
            if str(architecture_mode) == "f0"
            else None
        ),
        "rows": list(prefix_rows),
    }


def _event_semantic_primitive_probabilities(
    model_owner,
    rows: Sequence[Any],
) -> list[list[float]]:
    """Replay already-emitted low rows without sampling or advancing a runtime."""

    if not rows:
        return []
    if int(model_owner.action_dim) != 3 or str(model_owner.action_space_type) != (
        "discrete"
    ):
        raise ValueError("semantic provenance requires three discrete primitives")
    actor = model_owner.low_actor
    observations = torch.as_tensor(
        np.stack([row.observation for row in rows]),
        dtype=torch.float32,
        device=model_owner.device,
    )
    skills = torch.as_tensor(
        [int(row.skill) for row in rows],
        dtype=torch.long,
        device=model_owner.device,
    )
    hidden = torch.as_tensor(
        np.stack([row.actor_hidden_before for row in rows]),
        dtype=torch.float32,
        device=model_owner.device,
    )
    features = actor._features(observations, skills)
    features, _unused_hidden = actor.actor_rnn(
        features,
        hidden,
        torch.ones(
            features.shape[0], 1, dtype=torch.float32, device=model_owner.device
        ),
    )
    probabilities = actor.actor_act.action_out(features).probs.detach().cpu().numpy()
    if probabilities.shape != (len(rows), 3) or not np.isfinite(probabilities).all():
        raise RuntimeError("semantic provenance primitive probabilities are invalid")
    output = probabilities.astype(np.float64).tolist()
    for row, probability in zip(rows, output):
        action_values = np.asarray(row.action).reshape(-1)
        if action_values.size != 1:
            raise RuntimeError("semantic provenance requires scalar discrete actions")
        action = int(action_values[0])
        replayed_logp = float(
            np.log(max(float(probability[action]), np.finfo(np.float64).tiny))
        )
        if abs(replayed_logp - float(row.old_log_probability)) > 1e-5:
            raise RuntimeError("semantic provenance low-policy replay mismatch")
    return output


def _project_event_semantic_natural_row(
    row,
    *,
    arm: str,
    episode_id: int,
    active_set_size: int,
    primitive_probabilities: Sequence[float],
) -> dict[str, Any]:
    """Project one emitted low row into the leakage-free natural schema."""

    action_values = np.asarray(row.action).reshape(-1)
    probabilities = np.asarray(primitive_probabilities, dtype=np.float64).reshape(-1)
    if action_values.size != 1 or probabilities.shape != (3,):
        raise ValueError("semantic provenance natural row has invalid action shape")
    if not np.isfinite(probabilities).all():
        raise ValueError("semantic provenance natural probabilities must be finite")
    return {
        "arm": str(arm),
        "task_master_seed": 97_057,
        "episode_id": int(episode_id),
        "physical_time": int(row.physical_time),
        "lifecycle_key": str(row.lifecycle_key),
        "membership_epoch": int(row.membership_epoch),
        "observation": np.asarray(row.observation, dtype=np.float32).tolist(),
        "actor_hidden_before": np.asarray(
            row.actor_hidden_before, dtype=np.float32
        ).tolist(),
        "natural_skill": int(row.skill),
        "natural_action": int(action_values[0]),
        "natural_action_log_probability": float(row.old_log_probability),
        "primitive_legal_support": [0, 1, 2],
        "primitive_probabilities": probabilities.tolist(),
        "active_set_size": int(active_set_size),
    }


def _capture_event_semantic_source(
    *,
    core,
    snapshot,
    transaction,
    focal_key: str,
) -> dict[str, Any]:
    """Capture source-only routing and owned-PCG64 state before branch cloning."""

    key = str(focal_key)
    if key not in snapshot.keys:
        raise ValueError("semantic provenance focal key is not active")
    active_skills = core.active_skills()
    if set(active_skills) != set(snapshot.keys):
        raise RuntimeError("semantic provenance active skill routing is incomplete")
    return {
        "focal_index": int(snapshot.keys.index(key)),
        "active_keys": list(snapshot.keys),
        "active_membership_epochs": [
            int(member.membership_epoch) for member in snapshot.members
        ],
        "active_skills": [int(active_skills[active]) for active in snapshot.keys],
        "frontier": list(snapshot.frontier),
        "membership_deltas": [
            {
                "kind": str(delta.kind),
                "lifecycle_key": str(delta.lifecycle_key),
                "expected_membership_epoch": int(delta.expected_membership_epoch),
            }
            for delta in transaction.atomic_membership_delta
        ],
        "source_rng_ledger": {
            "episode_id": int(core.rng_episode_id),
            "opportunity": {
                "master_seed": int(core.opportunity_master_seed),
                "stream_id": int(core.opportunity_stream_id),
            },
            "frontier_order": {
                "master_seed": int(core.frontier_master_seed),
                "stream_id": int(core.frontier_stream_id),
            },
            "policy_action": {
                "master_seed": int(core.action_master_seed),
                "stream_id": int(core.action_stream_id),
            },
        },
        "source_rng_states": {
            "opportunity": deepcopy(core.opportunity_rng.bit_generator.state),
            "frontier_order": deepcopy(core.frontier_rng.bit_generator.state),
            "policy_action": deepcopy(core.action_rng.bit_generator.state),
        },
    }


def _project_event_semantic_forced_source(
    natural_row: Mapping[str, Any],
    *,
    source: Mapping[str, Any],
    forced_effects: Sequence[Any],
) -> dict[str, Any]:
    """Join a captured source to its already-produced focal natural row."""

    effects = np.asarray(forced_effects, dtype=np.float64)
    if effects.shape != (3, 2, 4) or not np.isfinite(effects).all():
        raise ValueError("semantic provenance forced effects have invalid shape")
    focal_index = int(source["focal_index"])
    if str(source["active_keys"][focal_index]) != str(natural_row["lifecycle_key"]):
        raise RuntimeError("semantic provenance focal source does not match natural row")
    if int(source["active_membership_epochs"][focal_index]) != int(
        natural_row["membership_epoch"]
    ):
        raise RuntimeError("semantic provenance focal epoch does not match natural row")
    return {
        **deepcopy(dict(natural_row)),
        **deepcopy(dict(source)),
        "forced_effects": effects.tolist(),
    }


@torch.no_grad()
def _forced_event_snapshot_effects(
    *,
    model_owner,
    core,
    environment,
    snapshot,
    episode_id: int,
    audit_index: int,
    focal_key: str | None = None,
) -> list[list[list[float]]]:
    from ha_ctse_process.collectors import SyncEnvCollector
    from ha_ctse_process.dynamic_roster_testbed import (
        DynamicRosterEventEnv,
        PERSIST,
        SHORT,
    )
    from ha_ctse_process.variable_roster_event_support import make_pcg64_rng

    if int(core.physical_time) <= 0 or int(core.physical_time) > 68:
        raise ValueError("forced audit snapshot must allow exactly 12 future steps")
    source_collector = SyncEnvCollector([environment])
    collector_snapshot = source_collector.snapshot_event_runtime()
    checkpoint = core.checkpoint_payload(
        collector_snapshot=collector_snapshot,
        current_observation_state_boundary={
            "physical_time": int(core.physical_time),
            "episode_id": int(episode_id),
            "fresh_eval": True,
        },
        optimizer_states={"high": {}, "low": {}},
        normalizer_states=_event_identity_normalizers(),
        pending_membership_transaction=core.pending_membership_transaction,
    )
    selected_focal_key = (
        snapshot.keys[int(audit_index) % len(snapshot.keys)]
        if focal_key is None
        else str(focal_key)
    )
    if selected_focal_key not in snapshot.keys:
        raise ValueError("forced audit focal key is not active in the source snapshot")
    skill_results: list[list[list[float]]] = []
    for skill in range(model_owner.n_skills):
        replica_results: list[list[float]] = []
        for replica in range(2):
            branch_environment = DynamicRosterEventEnv(task_master_seed=97_057)
            branch_collector = SyncEnvCollector([branch_environment])
            branch_core = _make_event_runtime(
                model_owner,
                environment_index=0,
                episode_id=episode_id,
                event_master_seed=77_057,
                action_master_seed=87_057,
            )
            branch_core.restore_checkpoint_payload(checkpoint, collector=branch_collector)
            branch_core.action_rng = make_pcg64_rng(
                87_057, int(audit_index), 100 + int(replica)
            )
            branch_snapshot = deepcopy(snapshot)
            if branch_environment.environment is None:
                raise RuntimeError("forced audit environment restore failed")
            start_persistent = int(branch_environment.environment.persistent_units)
            start_short = int(branch_environment.environment.short_completed_total)
            wave = branch_environment.environment.current_wave
            short_denominator = 1 if wave is None else max(int(wave.required_work), 1)
            persist_actions = 0
            short_actions = 0
            for _step in range(12):
                if selected_focal_key not in branch_core.records or (
                    branch_core.records[selected_focal_key].status != "ACTIVE"
                ):
                    raise RuntimeError("forced focal lifecycle left before audit window closed")
                branch_core.records[selected_focal_key].active_skill = int(skill)
                actions, _logp, _values = branch_core.low_step(
                    branch_snapshot, deterministic=False
                )
                routed = {
                    key: int(actions[index].detach().cpu())
                    for index, key in enumerate(branch_snapshot.keys)
                }
                focal_action = int(routed[selected_focal_key])
                persist_actions += int(focal_action == PERSIST)
                short_actions += int(focal_action == SHORT)
                event_step = branch_environment.step_event_runtime(routed)
                branch_core.complete_primitive_transition(float(event_step.reward))
                if event_step.terminated or event_step.next_transaction is None:
                    raise RuntimeError("forced audit branch ended before 12 steps")
                bound = branch_core.bind_due_frontier(event_step.next_transaction)
                branch_core.apply_transaction(bound, deterministic_policy=False)
                branch_snapshot = bound.post_membership_pre_policy_snapshot
            assert branch_environment.environment is not None
            replica_results.append(
                [
                    float(persist_actions) / 12.0,
                    float(short_actions) / 12.0,
                    float(
                        branch_environment.environment.persistent_units
                        - start_persistent
                    )
                    / 12.0,
                    float(
                        branch_environment.environment.short_completed_total
                        - start_short
                    )
                    / float(short_denominator),
                ]
            )
        skill_results.append(replica_results)
    return skill_results


def _summarize_forced_audit(
    effects: Sequence[Any],
    *,
    natural_skill_counts: Sequence[int],
) -> dict[str, Any]:
    values = np.asarray(effects, dtype=np.float64)
    if values.shape != (128, 3, 2, 4):
        raise ValueError(f"forced audit effect shape mismatch: {values.shape}")
    skill_means = values.mean(axis=(0, 2))
    persistent_order = np.argsort(skill_means[:, 0])
    reactive_order = np.argsort(skill_means[:, 1])
    persistent_skill = int(persistent_order[-1])
    reactive_skill = int(reactive_order[-1])
    persistent_margin = float(
        skill_means[persistent_order[-1], 0]
        - skill_means[persistent_order[-2], 0]
    )
    reactive_margin = float(
        skill_means[reactive_order[-1], 1]
        - skill_means[reactive_order[-2], 1]
    )

    def rho_for(sample: np.ndarray) -> float:
        means = sample.mean(axis=2)
        between = []
        for left in range(3):
            for right in range(left + 1, 3):
                between.extend(np.linalg.norm(means[:, left] - means[:, right], axis=-1))
        within = np.linalg.norm(sample[:, :, 0] - sample[:, :, 1], axis=-1).reshape(-1)
        return float(np.median(between) / (np.median(within) + 1e-8))

    rho = rho_for(values)
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([107_057, 1])))
    bootstrap = np.empty(10_000, dtype=np.float64)
    for index in range(10_000):
        selected = rng.integers(0, values.shape[0], values.shape[0])
        bootstrap[index] = rho_for(values[selected])
    counts = np.asarray(natural_skill_counts, dtype=np.float64)
    shares = counts / max(float(counts.sum()), 1.0)
    executable = bool(
        float(np.quantile(bootstrap, 0.025)) > 1.0
        and persistent_skill != reactive_skill
        and persistent_margin > 0.15
        and reactive_margin > 0.15
        and bool(np.all(shares >= 0.10))
    )
    return {
        "snapshot_count": 128,
        "skills_per_snapshot": 3,
        "replicas_per_skill": 2,
        "steps_per_replica": 12,
        "forced_environment_steps": 128 * 3 * 2 * 12,
        "effect_shape": list(values.shape),
        "rho": rho,
        "rho_ci95": [
            float(np.quantile(bootstrap, 0.025)),
            rho,
            float(np.quantile(bootstrap, 0.975)),
        ],
        "skill_signature_means": skill_means.tolist(),
        "persistent_like_skill": persistent_skill,
        "reactive_like_skill": reactive_skill,
        "persistent_occupancy_margin": persistent_margin,
        "reactive_occupancy_margin": reactive_margin,
        "natural_skill_step_counts": counts.astype(np.int64).tolist(),
        "natural_skill_step_shares": shares.tolist(),
        "executable_naturally_used_skills": executable,
        "effects": values.tolist(),
    }


@torch.no_grad()
def _evaluate_event_model(
    model_owner,
    *,
    deterministic: bool,
    capture_prefix: bool,
    capture_forced_audit: bool,
    capture_semantic_provenance: bool = False,
) -> dict[str, Any]:
    from ha_ctse_process.dynamic_roster_testbed import DynamicRosterEventEnv, HORIZON

    modules = (
        model_owner.commitment_model,
        model_owner.event_critic,
        model_owner.low_actor,
        model_owner.low_critic,
    )
    previous_training = [module.training for module in modules]
    for module in modules:
        module.eval()
    episode_ids = tuple(range(256))
    persistent: list[float] = []
    short: list[float] = []
    utility: list[float] = []
    prefix_rows: list[dict[str, Any]] = []
    timing_rows: list[dict[str, Any]] = []
    natural_skill_counts = np.zeros(model_owner.n_skills, dtype=np.int64)
    forced_effects: list[Any] = []
    semantic_natural_rows: list[dict[str, Any]] = []
    semantic_forced_sources: list[dict[str, Any]] = []
    try:
        for episode_id in episode_ids:
            environment = DynamicRosterEventEnv(task_master_seed=97_057)
            core = _make_event_runtime(
                model_owner,
                environment_index=0,
                episode_id=episode_id,
                event_master_seed=77_057,
                action_master_seed=87_057,
            )
            transaction = environment.reset_event_runtime(episode_id)
            bound = core.bind_due_frontier(transaction)
            result = core.apply_transaction(
                bound, deterministic_policy=bool(deterministic)
            )
            snapshot = bound.post_membership_pre_policy_snapshot
            if capture_prefix:
                prefix_rows.extend(
                    _event_prefix_rows(core, result.token_rows, episode_id=episode_id)
                )
            selected_times = set()
            if (capture_forced_audit or capture_semantic_provenance) and episode_id < 32:
                selected_times = {
                    1 + episode_id % 8,
                    20 + episode_id % 9,
                    40 + episode_id % 9,
                    60 + episode_id % 8,
                }
            for primitive_time in range(HORIZON):
                semantic_source = None
                source_forced_effects = None
                if primitive_time in selected_times:
                    audit_index = len(forced_effects)
                    focal_key = snapshot.keys[audit_index % len(snapshot.keys)]
                    if capture_semantic_provenance:
                        semantic_source = _capture_event_semantic_source(
                            core=core,
                            snapshot=snapshot,
                            transaction=bound,
                            focal_key=focal_key,
                        )
                    source_forced_effects = _forced_event_snapshot_effects(
                        model_owner=model_owner,
                        core=core,
                        environment=environment,
                        snapshot=snapshot,
                        episode_id=episode_id,
                        audit_index=audit_index,
                        focal_key=focal_key,
                    )
                    forced_effects.append(source_forced_effects)
                skills_now = core.active_skills()
                for skill in skills_now.values():
                    natural_skill_counts[int(skill)] += 1
                environment_state = environment.environment
                if environment_state is None:
                    raise RuntimeError("evaluation environment is missing state")
                current_wave = environment_state.current_wave
                opportunity_keys = sorted(
                    {row.owner_lifecycle_key for row in result.token_rows}
                )
                short_completed_before = int(environment_state.short_completed_total)
                timing_row = {
                    "episode_id": episode_id,
                    "physical_time": primitive_time,
                    "active_keys": list(snapshot.keys),
                    "active_skills": [int(skills_now[key]) for key in snapshot.keys],
                    "opportunity_keys_at_time": opportunity_keys,
                    "wave_index": (
                        None if current_wave is None else int(current_wave.index)
                    ),
                    "wave_arrival_time": (
                        None
                        if current_wave is None
                        else int(current_wave.arrival_time)
                    ),
                    "wave_required": (
                        0 if current_wave is None else int(current_wave.required_work)
                    ),
                    "wave_completed_before_action": (
                        0 if current_wave is None else int(current_wave.completed_work)
                    ),
                    "persistent_owner_exists": bool(
                        environment_state.persistent_owner is not None
                    ),
                }
                low_ledger_start = (
                    len(core.low_ledger)
                    if capture_semantic_provenance and episode_id < 32
                    else None
                )
                actions, _logp, _values = core.low_step(
                    snapshot, deterministic=bool(deterministic)
                )
                if low_ledger_start is not None:
                    emitted_low_rows = core.low_ledger[low_ledger_start:]
                    if len(emitted_low_rows) != len(snapshot.keys) or {
                        (str(row.lifecycle_key), int(row.membership_epoch))
                        for row in emitted_low_rows
                    } != {
                        (str(member.lifecycle_key), int(member.membership_epoch))
                        for member in snapshot.members
                    }:
                        raise RuntimeError(
                            "semantic provenance low-ledger source slice is not exact"
                        )
                    probability_rows = _event_semantic_primitive_probabilities(
                        model_owner, emitted_low_rows
                    )
                    projected_rows = [
                        _project_event_semantic_natural_row(
                            row,
                            arm=model_owner.architecture_mode,
                            episode_id=episode_id,
                            active_set_size=len(snapshot.keys),
                            primitive_probabilities=probabilities,
                        )
                        for row, probabilities in zip(
                            emitted_low_rows, probability_rows
                        )
                    ]
                    semantic_natural_rows.extend(projected_rows)
                    if semantic_source is not None:
                        focal_index = int(semantic_source["focal_index"])
                        focal_key = str(semantic_source["active_keys"][focal_index])
                        focal_epoch = int(
                            semantic_source["active_membership_epochs"][focal_index]
                        )
                        focal_rows = [
                            row
                            for row in projected_rows
                            if str(row["lifecycle_key"]) == focal_key
                            and int(row["membership_epoch"]) == focal_epoch
                        ]
                        if len(focal_rows) != 1 or source_forced_effects is None:
                            raise RuntimeError(
                                "semantic provenance forced source lacks one natural match"
                            )
                        semantic_forced_sources.append(
                            _project_event_semantic_forced_source(
                                focal_rows[0],
                                source=semantic_source,
                                forced_effects=source_forced_effects,
                            )
                        )
                routed = {
                    key: int(actions[index].detach().cpu())
                    for index, key in enumerate(snapshot.keys)
                }
                step = environment.step_event_runtime(routed)
                completed_this_action = max(
                    int(step.info["short_completed_total"]) - short_completed_before,
                    0,
                )
                timing_row["wave_completed_after_action"] = (
                    0
                    if current_wave is None
                    else min(
                        int(current_wave.required_work),
                        int(timing_row["wave_completed_before_action"])
                        + completed_this_action,
                    )
                )
                timing_row["persistent_owner_exists_after_action"] = bool(
                    environment.environment is not None
                    and environment.environment.persistent_owner is not None
                )
                timing_rows.append(timing_row)
                core.complete_primitive_transition(float(step.reward))
                if step.terminated:
                    core.close_terminal()
                    persistent.append(float(step.info["persistent_score"]))
                    short.append(float(step.info["short_score"]))
                    utility.append(float(step.info["utility"]))
                    break
                if step.next_transaction is None:
                    raise RuntimeError("evaluation nonterminal step lacks transaction")
                bound = core.bind_due_frontier(step.next_transaction)
                result = core.apply_transaction(
                    bound, deterministic_policy=bool(deterministic)
                )
                snapshot = bound.post_membership_pre_policy_snapshot
                if capture_prefix:
                    prefix_rows.extend(
                        _event_prefix_rows(
                            core, result.token_rows, episode_id=episode_id
                        )
                    )
        if len(persistent) != 256 or len(short) != 256 or len(utility) != 256:
            raise RuntimeError("Stage C evaluation episode count is not exact")
        payload: dict[str, Any] = {
            "episode_ids": list(episode_ids),
            "deterministic": bool(deterministic),
            "persistent": persistent,
            "short": short,
            "utility": utility,
            "persistent_mean": float(np.mean(persistent)),
            "short_mean": float(np.mean(short)),
            "utility_mean": float(np.mean(utility)),
            "environment_steps": 256 * HORIZON,
            "natural_skill_step_counts": natural_skill_counts.tolist(),
            "prefix_rows": prefix_rows,
            "timing_rows": timing_rows if capture_prefix else [],
        }
        if capture_forced_audit:
            payload["forced_audit"] = _summarize_forced_audit(
                forced_effects,
                natural_skill_counts=natural_skill_counts,
            )
        if capture_semantic_provenance:
            if len(semantic_forced_sources) != 128:
                raise RuntimeError("semantic provenance forced source count is not exact")
            payload["semantic_provenance"] = {
                "schema": 1,
                "natural_rows": semantic_natural_rows,
                "forced_sources": semantic_forced_sources,
            }
        return payload
    finally:
        for module, was_training in zip(modules, previous_training):
            module.train(was_training)
