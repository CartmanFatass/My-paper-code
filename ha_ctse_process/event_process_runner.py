"""Iteration-5 process-semantics production runner."""

from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch

from ha_ctse_process.standalone_contracts import (
    enforce_iteration5_process_semantics_contract,
)
from ha_ctse_process.standalone_event_support import (
    _event_identity_normalizers,
    _make_event_model_owner,
    _make_event_runtime,
    _nested_state_maximum_difference,
    _replace_event_file,
    _write_event_arm_status,
    _write_event_json,
)


def _iteration5_semantic_checkpoint(
    base_payload: Mapping[str, Any],
    *,
    trainer,
    ledgers,
    intrinsic_applied_count: int,
    replay: Mapping[str, float],
    high_intrinsic_isolated: bool,
    posterior_policy_gradient_isolated: bool,
) -> dict[str, Any]:
    from ha_ctse_process.process_semantics import snapshot_event_semantic_bundle

    payload = deepcopy(dict(base_payload))
    event = payload.get("event_architecture")
    if (
        not isinstance(event, dict)
        or "event_semantic" in event
        or "iteration5_evidence_state" in event
    ):
        raise ValueError("Iteration-5 checkpoint requires one clean event bundle")
    event["event_semantic"] = snapshot_event_semantic_bundle(
        trainer=trainer,
        ledgers=ledgers,
        intrinsic_applied_count=int(intrinsic_applied_count),
    )
    replay_value = {str(name): float(value) for name, value in dict(replay).items()}
    required_replay = {
        "high_logp_max_error",
        "high_value_max_error",
        "low_logp_max_error",
        "low_value_max_error",
    }
    if set(replay_value) != required_replay or any(
        not np.isfinite(value) or value < 0.0 for value in replay_value.values()
    ):
        raise ValueError("Iteration-5 checkpoint replay evidence is invalid")
    event["iteration5_evidence_state"] = {
        "schema_version": 1,
        "replay": replay_value,
        "high_intrinsic_isolated": bool(high_intrinsic_isolated),
        "posterior_policy_gradient_isolated": bool(
            posterior_policy_gradient_isolated
        ),
    }
    return payload


def _restore_iteration5_vector_checkpoint(
    payload: Mapping[str, Any],
    *,
    model_owner,
    cores,
    collector,
    trainer,
    ledgers,
):
    from ha_ctse_process.process_semantics import restore_event_semantic_bundle
    from ha_ctse_process.variable_roster_event_checkpoint import (
        restore_vector_event_checkpoint,
    )

    value = deepcopy(dict(payload))
    event = value.get("event_architecture")
    if (
        not isinstance(event, dict)
        or "event_semantic" not in event
        or "iteration5_evidence_state" not in event
    ):
        raise ValueError("Iteration-5 checkpoint is missing semantic/evidence state")
    semantic = event.pop("event_semantic")
    evidence = deepcopy(dict(event.pop("iteration5_evidence_state")))
    if set(evidence) != {
        "schema_version",
        "replay",
        "high_intrinsic_isolated",
        "posterior_policy_gradient_isolated",
    } or int(evidence["schema_version"]) != 1:
        raise ValueError("Iteration-5 checkpoint evidence schema mismatch")
    replay = {str(name): float(value) for name, value in dict(evidence["replay"]).items()}
    if set(replay) != {
        "high_logp_max_error",
        "high_value_max_error",
        "low_logp_max_error",
        "low_value_max_error",
    } or any(not np.isfinite(value) or value < 0.0 for value in replay.values()):
        raise ValueError("Iteration-5 restored replay evidence is invalid")
    evidence["replay"] = replay
    evidence["high_intrinsic_isolated"] = bool(
        evidence["high_intrinsic_isolated"]
    )
    evidence["posterior_policy_gradient_isolated"] = bool(
        evidence["posterior_policy_gradient_isolated"]
    )
    optimizer_states, normalizers, counters = restore_vector_event_checkpoint(
        value, model_owner=model_owner, cores=cores, collector=collector
    )
    semantic_count = restore_event_semantic_bundle(
        semantic, trainer=trainer, ledgers=ledgers
    )
    if int(counters["intrinsic_applied_count"]) != int(semantic_count):
        raise ValueError("Iteration-5 intrinsic counters disagree across bundles")
    return optimizer_states, normalizers, counters, evidence


def _open_iteration5_window(
    *, ledger, core, snapshot, lifecycle_key: str, process_state: float
) -> None:
    key = str(lifecycle_key)
    member_index = snapshot.keys.index(key)
    member = snapshot.members[member_index]
    record = core.records[key]
    if record.active_skill is None:
        raise RuntimeError("Iteration-5 active lifecycle has no skill")
    ledger.open_window(
        lifecycle_key=key,
        membership_epoch=int(record.membership_epoch),
        policy_version=int(core.policy_version),
        skill=int(record.active_skill),
        start_observation=np.asarray(member.observation, dtype=np.float32),
        start_actor_hidden=np.asarray(record.low_actor_hidden, dtype=np.float32),
        start_process_state=float(process_state),
    )


def _apply_iteration5_transaction_hooks(
    *, ledger, core, transaction, result, snapshot, process_state: Mapping[str, float]
) -> None:
    from ha_ctse_process.variable_roster_event_types import event_action_hooks

    member_by_key = {str(member.lifecycle_key): member for member in snapshot.members}
    for hook in event_action_hooks(result):
        key = str(hook.lifecycle_key)
        ledger_key = (key, int(hook.membership_epoch), int(hook.policy_version))
        if ledger_key not in ledger.open_keys:
            _open_iteration5_window(
                ledger=ledger,
                core=core,
                snapshot=snapshot,
                lifecycle_key=key,
                process_state=float(process_state[key]),
            )
            continue
        record = core.records[key]
        member = member_by_key[key]
        ledger.apply_event_boundary(
            lifecycle_key=key,
            membership_epoch=int(hook.membership_epoch),
            policy_version=int(hook.policy_version),
            action_kind=str(hook.action_kind),
            next_skill=int(hook.next_skill),
            observation=np.asarray(member.observation, dtype=np.float32),
            actor_hidden=np.asarray(record.low_actor_hidden, dtype=np.float32),
            process_state=float(process_state[key]),
        )
    for key in snapshot.keys:
        record = core.records[str(key)]
        ledger_key = (str(key), int(record.membership_epoch), int(core.policy_version))
        if ledger_key not in ledger.open_keys:
            _open_iteration5_window(
                ledger=ledger,
                core=core,
                snapshot=snapshot,
                lifecycle_key=str(key),
                process_state=float(process_state[str(key)]),
            )


@torch.no_grad()
def _evaluate_iteration5_spatial_model(
    model_owner,
    *,
    deterministic: bool,
    episodes: int,
) -> dict[str, Any]:
    from ha_ctse_process.dynamic_roster_spatial_testbed import (
        HORIZON,
        SpatialDynamicRosterEventEnv,
    )
    from ha_ctse_process.collectors import SyncEnvCollector
    from ha_ctse_process.variable_roster_event_batching import batched_low_step

    persistent: list[float] = []
    short: list[float] = []
    utility: list[float] = []
    skill_counts = np.zeros(model_owner.n_skills, dtype=np.int64)
    episode_count = int(episodes)
    if episode_count <= 0:
        raise ValueError("Iteration-5 evaluation requires at least one episode")
    environments = [
        SpatialDynamicRosterEventEnv(task_master_seed=97_057)
        for _episode_id in range(episode_count)
    ]
    collector = SyncEnvCollector(environments)
    try:
        transactions = collector.reset_event_runtime(tuple(range(episode_count)))
        cores = []
        snapshots = []
        for episode_id, transaction in enumerate(transactions):
            core = _make_event_runtime(
                model_owner,
                environment_index=0,
                episode_id=episode_id,
                event_master_seed=77_057,
                action_master_seed=87_057,
            )
            bound = core.bind_due_frontier(transaction)
            core.apply_transaction(bound, deterministic_policy=bool(deterministic))
            cores.append(core)
            snapshots.append(bound.post_membership_pre_policy_snapshot)
        for physical_time in range(HORIZON):
            for core in cores:
                for skill in core.active_skills().values():
                    skill_counts[int(skill)] += 1
            low = batched_low_step(
                cores, snapshots, deterministic=bool(deterministic)
            )
            steps = collector.step_event_runtime(low.routed_actions)
            terminal_flags = tuple(bool(step.terminated) for step in steps)
            for core, step in zip(cores, steps):
                core.complete_primitive_transition(float(step.reward))
            if any(terminal_flags):
                if not all(terminal_flags) or physical_time != HORIZON - 1:
                    raise RuntimeError(
                        "Iteration-5 evaluation episodes lost their shared horizon"
                    )
                for core, step in zip(cores, steps):
                    core.close_terminal()
                    persistent.append(float(step.info["persistent_score"]))
                    short.append(float(step.info["short_score"]))
                    utility.append(float(step.info["utility"]))
                break
            next_snapshots = []
            for core, step in zip(cores, steps):
                if step.next_transaction is None:
                    raise RuntimeError(
                        "Iteration-5 evaluation lost its next transaction"
                    )
                bound = core.bind_due_frontier(step.next_transaction)
                core.apply_transaction(
                    bound, deterministic_policy=bool(deterministic)
                )
                next_snapshots.append(bound.post_membership_pre_policy_snapshot)
            snapshots = next_snapshots
        if len(persistent) != episode_count:
            raise RuntimeError("Iteration-5 evaluation did not complete every episode")
    finally:
        collector.close()
    counts = skill_counts.astype(np.float64)
    return {
        "episodes": int(episodes),
        "deterministic": bool(deterministic),
        "persistent": persistent,
        "short": short,
        "utility": utility,
        "persistent_mean": float(np.mean(persistent)),
        "short_mean": float(np.mean(short)),
        "utility_mean": float(np.mean(utility)),
        "natural_skill_step_counts": skill_counts.tolist(),
        "natural_skill_step_shares": (counts / max(float(counts.sum()), 1.0)).tolist(),
    }


def _run_iteration5_process_semantics_branch(config, args: argparse.Namespace, writer):
    """Separate spatial F0 branch with rollout-frozen process semantics."""

    from ha_ctse_process.collectors import SyncEnvCollector
    from ha_ctse_process.dynamic_roster_spatial_testbed import (
        HORIZON,
        SpatialDynamicRosterEventEnv,
    )
    from ha_ctse_process.process_semantics import (
        ConditionalProcessPosterior,
        ProcessSemanticTrainer,
        ProcessWindowLedger,
    )
    from ha_ctse_process.variable_roster_event import (
        apply_event_ppo_update,
        pack_event_ppo_data,
    )
    from ha_ctse_process.variable_roster_event_checkpoint import (
        event_model_only_checkpoint_payload,
        vector_event_checkpoint_payload,
    )
    from ha_ctse_process.variable_roster_event_batching import batched_low_step
    from ha_ctse_process.variable_roster_event_types import (
        event_action_hooks,
        lifecycle_boundary_hooks,
        low_row_index_hooks,
    )

    enforce_iteration5_process_semantics_contract(config, args)
    arm = str(config.iteration5_process_semantics_arm)
    smoke = bool(getattr(config, "iteration5_smoke", False))
    num_envs = int(args.num_envs)
    rollout = int(args.rollout_length)
    total_target = int(args.total_timesteps)
    if rollout != HORIZON or total_target <= 0 or total_target % (num_envs * HORIZON):
        raise ValueError("Iteration-5 requires whole 80-step vector rollouts")
    updates_total = total_target // (num_envs * HORIZON)
    if not smoke and (num_envs, updates_total, total_target) != (16, 250, 320_000):
        raise ValueError("formal Iteration-5 requires 16 envs, 250 updates and 320000 steps")
    if str(getattr(args, "device", "cuda")).lower() != "cuda" or not torch.cuda.is_available():
        raise RuntimeError("Iteration-5 training requires available CUDA")
    device = torch.device("cuda")
    beta = 0.05 if arm == "c1_semantic_on" else 0.0
    output_root = Path(args.log_dir)
    checkpoint_dir = output_root / "checkpoints"
    result_dir = output_root / "result"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    result_dir.mkdir(parents=True, exist_ok=True)

    with torch.random.fork_rng(devices=[torch.cuda.current_device()]):
        torch.manual_seed(57_057)
        torch.cuda.manual_seed_all(57_057)
        model_owner = _make_event_model_owner(config, device)
        posterior = ConditionalProcessPosterior(
            observation_dim=model_owner.obs_dim,
            actor_hidden_dim=model_owner.low_hidden_dim,
            n_skills=model_owner.n_skills,
            hidden_dim=32,
        )
    high_optimizer = torch.optim.Adam(
        tuple(model_owner.commitment_model.parameters())
        + tuple(model_owner.event_critic.parameters()),
        lr=3e-4,
    )
    low_optimizer = torch.optim.Adam(
        tuple(model_owner.low_actor.parameters())
        + tuple(model_owner.low_critic.parameters()),
        lr=3e-4,
    )
    semantic_trainer = ProcessSemanticTrainer(
        posterior, beta=beta, device=device, sampler_seed=67_057
    )
    normalizers = _event_identity_normalizers()
    environments = [
        SpatialDynamicRosterEventEnv(task_master_seed=57_057) for _ in range(num_envs)
    ]
    collector = SyncEnvCollector(environments)
    ledgers = [ProcessWindowLedger(max_window_length=12) for _ in range(num_envs)]
    zero_checkpoint_path = checkpoint_dir / "update_000_eval.pt"
    if not str(getattr(args, "resume_from", "") or ""):
        zero_base = event_model_only_checkpoint_payload(
            model_owner=model_owner,
            normalizer_states=normalizers,
            total_steps=0,
            update_idx=0,
        )
        zero_payload = _iteration5_semantic_checkpoint(
            zero_base,
            trainer=semantic_trainer,
            ledgers=ledgers,
            intrinsic_applied_count=0,
            replay={
                "high_logp_max_error": 0.0,
                "high_value_max_error": 0.0,
                "low_logp_max_error": 0.0,
                "low_value_max_error": 0.0,
            },
            high_intrinsic_isolated=True,
            posterior_policy_gradient_isolated=True,
        )
        zero_temporary = zero_checkpoint_path.with_suffix(".pt.tmp")
        torch.save(zero_payload, zero_temporary)
        _replace_event_file(zero_temporary, zero_checkpoint_path)
    elif not zero_checkpoint_path.is_file():
        raise FileNotFoundError("Iteration-5 resume requires its update-0 checkpoint")
    zero_payload = torch.load(
        zero_checkpoint_path, map_location=device, weights_only=False
    )
    zero_event = zero_payload.get("event_architecture")
    if not isinstance(zero_event, Mapping) or "event_semantic" not in zero_event:
        raise ValueError("Iteration-5 update-0 checkpoint is incomplete")
    zero_owner = _make_event_model_owner(config, device)
    zero_owner.commitment_model.load_state_dict(
        zero_event["commitment_model_state"], strict=True
    )
    zero_owner.event_critic.load_state_dict(zero_event["event_critic_state"], strict=True)
    zero_owner.low_actor.load_state_dict(zero_event["low_actor_state"], strict=True)
    zero_owner.low_critic.load_state_dict(zero_event["low_critic_state"], strict=True)
    total_steps = 0
    update_idx = 0
    high_steps = 0
    low_steps = 0
    posterior_steps = 0
    intrinsic_count = 0
    next_episode_id = 0
    posterior_policy_gradient_isolated = True
    high_intrinsic_isolated = True
    replay = {
        "high_logp_max_error": 0.0,
        "high_value_max_error": 0.0,
        "low_logp_max_error": 0.0,
        "low_value_max_error": 0.0,
    }

    def prepare(episode_ids: Sequence[int]):
        transactions = collector.reset_event_runtime(episode_ids)
        cores = []
        snapshots = []
        for env_index, (episode_id, transaction) in enumerate(zip(episode_ids, transactions)):
            core = _make_event_runtime(
                model_owner,
                environment_index=env_index,
                episode_id=int(episode_id),
                event_master_seed=77_057,
                action_master_seed=87_057,
            )
            bound = core.bind_due_frontier(transaction)
            result = core.apply_transaction(bound, deterministic_policy=False)
            snapshot = bound.post_membership_pre_policy_snapshot
            process = environments[env_index].process_state_mapping(snapshot.keys)
            _apply_iteration5_transaction_hooks(
                ledger=ledgers[env_index],
                core=core,
                transaction=bound,
                result=result,
                snapshot=snapshot,
                process_state=process,
            )
            cores.append(core)
            snapshots.append(snapshot)
        return cores, snapshots

    resume_path = str(getattr(args, "resume_from", "") or "")
    if resume_path:
        resolved_resume = Path(resume_path).resolve()
        if resolved_resume.parent != checkpoint_dir.resolve():
            raise ValueError("Iteration-5 resume checkpoint must belong to this arm root")
        payload = torch.load(resolved_resume, map_location=device, weights_only=False)
        runtime_payloads = list(payload["event_architecture"]["runtime_payloads"])
        cores = []
        for env_index, runtime_payload in enumerate(runtime_payloads):
            rng = runtime_payload["rng_ledger"]
            cores.append(
                _make_event_runtime(
                    model_owner,
                    environment_index=env_index,
                    episode_id=int(rng["episode_id"]),
                    event_master_seed=int(rng["opportunity"]["master_seed"]),
                    action_master_seed=int(rng["policy_action"]["master_seed"]),
                )
            )
        optimizer_states, normalizers, counters, evidence = (
            _restore_iteration5_vector_checkpoint(
                payload,
                model_owner=model_owner,
                cores=cores,
                collector=collector,
                trainer=semantic_trainer,
                ledgers=ledgers,
            )
        )
        high_optimizer.load_state_dict(optimizer_states["high"])
        low_optimizer.load_state_dict(optimizer_states["low"])
        total_steps = int(counters["total_steps"])
        update_idx = int(counters["update_idx"])
        high_steps = int(counters["high_optimizer_steps"])
        low_steps = int(counters["low_optimizer_steps"])
        next_episode_id = int(counters["next_episode_id"])
        intrinsic_count = int(counters["intrinsic_applied_count"])
        posterior_steps = int(semantic_trainer.posterior_steps)
        replay = dict(evidence["replay"])
        high_intrinsic_isolated = bool(evidence["high_intrinsic_isolated"])
        posterior_policy_gradient_isolated = bool(
            evidence["posterior_policy_gradient_isolated"]
        )
        if not 0 < update_idx < updates_total:
            raise ValueError("Iteration-5 resume update lies outside the active run")
        if (
            total_steps != update_idx * num_envs * HORIZON
            or high_steps != update_idx * 4
            or low_steps != update_idx * 4
            or posterior_steps != update_idx * 4
            or next_episode_id != update_idx * num_envs
            or intrinsic_count < 0
        ):
            raise ValueError("Iteration-5 resume counter ledger mismatch")
        if any(ledger.open_keys for ledger in ledgers):
            raise ValueError("Iteration-5 terminal resume retained an open semantic window")
        # Live checkpoints are emitted only after a complete 80-step episode batch.
        # Restore validates their runtime/collector state, then the next update starts
        # a fresh registered episode batch; terminal boundaries intentionally have no
        # observation snapshot to resume inside an episode.
        cores = []
        snapshots = []
    else:
        cores = []
        snapshots = []

    zero_episodes = 2 if smoke else 256
    zero = {
        "deterministic": _evaluate_iteration5_spatial_model(
            zero_owner, deterministic=True, episodes=zero_episodes
        ),
        "stochastic": _evaluate_iteration5_spatial_model(
            zero_owner, deterministic=False, episodes=zero_episodes
        ),
    }
    update_rows: list[dict[str, Any]] = []
    try:
        for update in range(update_idx + 1, updates_total + 1):
            if not cores:
                episode_ids = tuple(range(next_episode_id, next_episode_id + num_envs))
                next_episode_id += num_envs
                cores, snapshots = prepare(episode_ids)
            for _physical_time in range(HORIZON):
                starts = [len(core.low_ledger) for core in cores]
                low = batched_low_step(cores, snapshots)
                steps = collector.step_event_runtime(low.routed_actions)
                next_snapshots = []
                for env_index, (core, step) in enumerate(zip(cores, steps)):
                    ledger = ledgers[env_index]
                    core.complete_primitive_transition(float(step.reward))
                    post_process = dict(step.info.get("process_state", {}))
                    for hook in low_row_index_hooks(core, starts[env_index]):
                        ledger.observe_transition(
                            lifecycle_key=hook.lifecycle_key,
                            membership_epoch=hook.membership_epoch,
                            policy_version=hook.policy_version,
                            low_row_index=hook.low_row_index,
                            post_process_state=float(post_process[hook.lifecycle_key]),
                        )
                    if step.terminated:
                        for key, epoch, version in tuple(ledger.open_keys):
                            ledger.apply_lifecycle_boundary(
                                lifecycle_key=key,
                                membership_epoch=epoch,
                                policy_version=version,
                                boundary_kind="EPISODE_TERMINAL",
                            )
                        core.close_terminal()
                        next_snapshots.append(None)
                        continue
                    if step.next_transaction is None:
                        raise RuntimeError("Iteration-5 nonterminal step lost transaction")
                    transaction = step.next_transaction
                    for boundary in lifecycle_boundary_hooks(transaction):
                        if boundary.boundary_kind in {"TEMPORARY_LEAVE", "TERMINAL_LEAVE"}:
                            record = core.records.get(boundary.lifecycle_key)
                            if record is not None:
                                ledger.apply_lifecycle_boundary(
                                    lifecycle_key=boundary.lifecycle_key,
                                    membership_epoch=int(record.membership_epoch),
                                    policy_version=int(core.policy_version),
                                    boundary_kind=boundary.boundary_kind,
                                )
                    bound = core.bind_due_frontier(transaction)
                    result = core.apply_transaction(bound, deterministic_policy=False)
                    next_snapshot = bound.post_membership_pre_policy_snapshot
                    next_process = environments[env_index].process_state_mapping(next_snapshot.keys)
                    member_by_key = {
                        str(member.lifecycle_key): member for member in next_snapshot.members
                    }
                    for key, epoch, version in tuple(ledger.open_keys):
                        if key in next_snapshot.keys:
                            record = core.records[key]
                            member = member_by_key[key]
                            ledger.roll_full_window(
                                lifecycle_key=key,
                                membership_epoch=epoch,
                                policy_version=version,
                                observation=np.asarray(member.observation, dtype=np.float32),
                                actor_hidden=np.asarray(record.low_actor_hidden, dtype=np.float32),
                                process_state=float(next_process[key]),
                            )
                    _apply_iteration5_transaction_hooks(
                        ledger=ledger,
                        core=core,
                        transaction=bound,
                        result=result,
                        snapshot=next_snapshot,
                        process_state=next_process,
                    )
                    next_snapshots.append(next_snapshot)
                snapshots = next_snapshots
                total_steps += num_envs

            windows_by_env = []
            for ledger in ledgers:
                ledger.close_rollout()
                windows_by_env.append(ledger.drain_closed_windows())
            all_windows = [window for rows in windows_by_env for window in rows]
            packed_windows = semantic_trainer.pack_closed_windows(all_windows)
            scores = semantic_trainer.score_closed_windows(packed_windows)
            high_rewards_before = [
                tuple(
                    (float(row.discounted_reward), float(row.return_target))
                    for row in core.closed_event_rows
                )
                for core in cores
            ]
            score_offset = 0
            for core, owned_windows in zip(cores, windows_by_env):
                owned_scores = scores[score_offset : score_offset + len(owned_windows)]
                score_offset += len(owned_windows)
                if owned_windows:
                    intrinsic_count += semantic_trainer.apply_low_rewards(
                        core.low_ledger,
                        owned_windows,
                        owned_scores,
                    )
            high_intrinsic_isolated = high_intrinsic_isolated and all(
                before
                == tuple(
                    (float(row.discounted_reward), float(row.return_target))
                    for row in core.closed_event_rows
                )
                for before, core in zip(high_rewards_before, cores)
            )
            posterior_metrics = semantic_trainer.update_posterior(
                packed_windows, passes=4
            )
            posterior_steps += int(posterior_metrics["posterior_steps"])
            posterior_policy_gradient_isolated = (
                posterior_policy_gradient_isolated
                and all(
                    parameter.grad is None
                    for module in (
                        model_owner.commitment_model,
                        model_owner.event_critic,
                        model_owner.low_actor,
                        model_owner.low_critic,
                    )
                    for parameter in module.parameters()
                )
            )
            packed = pack_event_ppo_data(cores)
            metrics = None
            first_pass_replay = None
            for ppo_pass in range(4):
                metrics = apply_event_ppo_update(
                    packed,
                    high_optimizer=high_optimizer,
                    low_optimizer=low_optimizer,
                )
                high_steps += 1
                low_steps += 1
                if ppo_pass == 0:
                    first_pass_replay = {
                        name: float(metrics[name]) for name in replay
                    }
            high_optimizer.zero_grad(set_to_none=True)
            low_optimizer.zero_grad(set_to_none=True)
            assert metrics is not None
            assert first_pass_replay is not None
            for name in replay:
                replay[name] = max(replay[name], first_pass_replay[name])
            update_idx = update
            update_rows.append(
                {
                    "update": update,
                    "steps": total_steps,
                    "high_optimizer_steps": high_steps,
                    "low_optimizer_steps": low_steps,
                    "posterior_optimizer_steps": posterior_steps,
                    "intrinsic_applied_count": intrinsic_count,
                    **replay,
                }
            )
            checkpoint_interval = max(int(args.save_interval), 1)
            checkpoint_due = (
                update_idx % checkpoint_interval == 0
                or update_idx == updates_total
            )
            if checkpoint_due:
                boundaries = [
                    {
                        "physical_time": int(core.physical_time),
                        "episode_id": int(core.rng_episode_id),
                        "terminal": True,
                    }
                    for core in cores
                ]
                base = vector_event_checkpoint_payload(
                    model_owner=model_owner,
                    cores=cores,
                    collector_snapshot=collector.snapshot_event_runtime(),
                    current_boundaries=boundaries,
                    optimizer_states={
                        "high": high_optimizer.state_dict(),
                        "low": low_optimizer.state_dict(),
                    },
                    normalizer_states=normalizers,
                    counters={
                        "total_steps": total_steps,
                        "update_idx": update_idx,
                        "high_optimizer_steps": high_steps,
                        "low_optimizer_steps": low_steps,
                        "next_episode_id": next_episode_id,
                        "intrinsic_applied_count": intrinsic_count,
                    },
                )
                payload = _iteration5_semantic_checkpoint(
                    base,
                    trainer=semantic_trainer,
                    ledgers=ledgers,
                    intrinsic_applied_count=intrinsic_count,
                    replay=replay,
                    high_intrinsic_isolated=high_intrinsic_isolated,
                    posterior_policy_gradient_isolated=(
                        posterior_policy_gradient_isolated
                    ),
                )
                latest = checkpoint_dir / "latest.pt"
                temporary = latest.with_suffix(".pt.tmp")
                torch.save(payload, temporary)
                _replace_event_file(temporary, latest)
            cores = []
            snapshots = []
            _write_event_arm_status(
                args,
                state="running",
                phase="training",
                mode=arm,
                update=update_idx,
                updates_total=updates_total,
                steps=total_steps,
                steps_total=total_target,
            )

        eval_episodes = 2 if smoke else 256
        final = {
            "deterministic": _evaluate_iteration5_spatial_model(
                model_owner, deterministic=True, episodes=eval_episodes
            ),
            "stochastic": _evaluate_iteration5_spatial_model(
                model_owner, deterministic=False, episodes=eval_episodes
            ),
        }
        live_payload = torch.load(
            checkpoint_dir / "latest.pt", map_location=device, weights_only=False
        )
        verification_owner = _make_event_model_owner(config, device)
        verification_trainer = ProcessSemanticTrainer(
            ConditionalProcessPosterior(
                observation_dim=verification_owner.obs_dim,
                actor_hidden_dim=verification_owner.low_hidden_dim,
                n_skills=verification_owner.n_skills,
                hidden_dim=32,
            ),
            beta=beta,
            device=device,
            sampler_seed=1,
        )
        verification_ledgers = [
            ProcessWindowLedger(max_window_length=12) for _ in range(num_envs)
        ]
        verification_environments = [
            SpatialDynamicRosterEventEnv(task_master_seed=1) for _ in range(num_envs)
        ]
        verification_collector = SyncEnvCollector(verification_environments)
        runtime_payloads = list(live_payload["event_architecture"]["runtime_payloads"])
        verification_cores = []
        for env_index, runtime_payload in enumerate(runtime_payloads):
            rng = runtime_payload["rng_ledger"]
            verification_cores.append(
                _make_event_runtime(
                    verification_owner,
                    environment_index=env_index,
                    episode_id=int(rng["episode_id"]),
                    event_master_seed=int(rng["opportunity"]["master_seed"]),
                    action_master_seed=int(rng["policy_action"]["master_seed"]),
                )
            )
        (
            restored_optimizers,
            restored_normalizers,
            restored_counters,
            restored_evidence,
        ) = (
            _restore_iteration5_vector_checkpoint(
                live_payload,
                model_owner=verification_owner,
                cores=verification_cores,
                collector=verification_collector,
                trainer=verification_trainer,
                ledgers=verification_ledgers,
            )
        )
        checkpoint_roundtrip_error = max(
            _nested_state_maximum_difference(
                model_owner.commitment_model.state_dict(),
                verification_owner.commitment_model.state_dict(),
            ),
            _nested_state_maximum_difference(
                model_owner.event_critic.state_dict(),
                verification_owner.event_critic.state_dict(),
            ),
            _nested_state_maximum_difference(
                model_owner.low_actor.state_dict(),
                verification_owner.low_actor.state_dict(),
            ),
            _nested_state_maximum_difference(
                model_owner.low_critic.state_dict(),
                verification_owner.low_critic.state_dict(),
            ),
            _nested_state_maximum_difference(
                semantic_trainer.state_dict(), verification_trainer.state_dict()
            ),
            _nested_state_maximum_difference(normalizers, restored_normalizers),
            _nested_state_maximum_difference(
                {
                    "total_steps": total_steps,
                    "update_idx": update_idx,
                    "high_optimizer_steps": high_steps,
                    "low_optimizer_steps": low_steps,
                    "next_episode_id": next_episode_id,
                    "intrinsic_applied_count": intrinsic_count,
                },
                restored_counters,
            ),
            _nested_state_maximum_difference(
                high_optimizer.state_dict(), restored_optimizers["high"]
            ),
            _nested_state_maximum_difference(
                low_optimizer.state_dict(), restored_optimizers["low"]
            ),
            _nested_state_maximum_difference(
                {
                    "schema_version": 1,
                    "replay": replay,
                    "high_intrinsic_isolated": high_intrinsic_isolated,
                    "posterior_policy_gradient_isolated": (
                        posterior_policy_gradient_isolated
                    ),
                },
                restored_evidence,
            ),
        )
        verification_collector.close()
        formal_counts = (
            total_steps == total_target
            and high_steps == updates_total * 4
            and low_steps == updates_total * 4
            and posterior_steps == updates_total * 4
        )
        m0 = {
            "exposure_exact": bool(formal_counts),
            "sampling_replay_probability": max(
                replay["high_logp_max_error"], replay["low_logp_max_error"]
            ) <= 1e-6,
            "sampling_replay_value": max(
                replay["high_value_max_error"], replay["low_value_max_error"]
            ) <= 1e-6,
            "high_intrinsic_count_zero": bool(high_intrinsic_isolated),
            "posterior_policy_gradient_isolated": bool(
                posterior_policy_gradient_isolated
            ),
            "strict_semantic_checkpoint_round_trip": checkpoint_roundtrip_error
            == 0.0,
        }
        result = {
            "schema_version": 1,
            "stage": "iteration5_process_semantics",
            "scientific": not smoke,
            "arm": arm,
            "implementation_valid": all(m0.values()),
            "m0": m0,
            "contract": {
                "num_envs": num_envs,
                "horizon": HORIZON,
                "updates": updates_total,
                "transitions": total_target,
                "ppo_passes": 4,
                "posterior_passes": 4,
                "beta": beta,
            },
            "counts": update_rows[-1] if update_rows else {},
            "replay": replay,
            "checkpoint_roundtrip_max_error": checkpoint_roundtrip_error,
            "zero": zero,
            "final": final,
        }
        path = result_dir / "iteration5_arm.json"
        _write_event_json(path, result)
        _write_event_arm_status(
            args,
            state="complete",
            phase="terminal",
            mode=arm,
            update=update_idx,
            updates_total=updates_total,
            steps=total_steps,
            steps_total=total_target,
            result_path=str(path),
        )
        return model_owner, total_steps, update_idx
    finally:
        collector.close()
