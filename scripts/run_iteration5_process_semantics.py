"""Single Iteration-5 spatial process-semantics evidence runner.

Formal mode launches both F0 semantic arms and the architecture-matched direct
controller concurrently.  ``--smoke`` is operational-only and never evaluates
the registered scientific gates.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys
import time
import traceback
from types import SimpleNamespace
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process.dynamic_roster_direct import (
    BOOTSTRAP_SEED,
    LEARNING_RATE,
    MODEL_INITIALIZATION_SEED,
    PPO_PASSES,
    DirectPrimitiveARPolicy,
    collect_direct_trajectory,
    evaluate_direct_policy,
    make_action_uniforms,
    optimize_direct_update,
    paired_bootstrap_ci,
    load_checkpoint,
    maximum_state_difference,
    model_state_copy,
    nested_state_maximum_difference,
    save_checkpoint,
    state_dict_finite,
)
from ha_ctse_process.dynamic_roster_spatial_testbed import (
    HORIZON,
    SpatialDynamicRosterEventEnv,
    constructive_spatial_actions,
    make_spatial_dynamic_roster_ledger,
    make_spatial_environment,
)
from ha_ctse_process.collectors import SyncEnvCollector
from ha_ctse_process.train import _make_event_model_owner, _make_event_runtime
from ha_ctse_process.variable_roster_event import batched_low_step, make_pcg64_rng


FORMAL_NUM_ENVS = 16
FORMAL_UPDATES = 250
FORMAL_EVAL_EPISODES = 256


def _git_source_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    source_commit = completed.stdout.strip().lower()
    if len(source_commit) != 40 or any(
        character not in "0123456789abcdef" for character in source_commit
    ):
        raise RuntimeError("Iteration-5 source commit is not a full Git SHA")
    return source_commit


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    _replace_file(temporary, path)


def _replace_file(temporary: Path, path: Path) -> None:
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


def _status(path: Path, **fields: Any) -> None:
    value = {
        **fields,
        "updated": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        "".join(f"{key}={item}\n" for key, item in value.items()), encoding="utf-8"
    )
    _replace_file(temporary, path)


def _carrier_controls(episodes: int) -> dict[str, Any]:
    constructive = []
    random_values = []
    for episode_id in range(int(episodes)):
        environment = SpatialDynamicRosterEventEnv(task_master_seed=57_057)
        environment.reset_event_runtime(episode_id)
        rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([57_057, episode_id])))
        for _ in range(HORIZON):
            assert environment.environment is not None
            view = environment.environment.observe()
            actions = constructive_spatial_actions(environment.environment, view)
            environment.step_event_runtime({str(key): action for key, action in actions.items()})
        assert environment.environment is not None
        outcome = environment.environment.outcome()
        constructive.append((outcome.persistent_score, outcome.short_score, outcome.utility))

        random_env = SpatialDynamicRosterEventEnv(task_master_seed=57_057)
        random_env.reset_event_runtime(episode_id)
        for _ in range(HORIZON):
            assert random_env.environment is not None
            view = random_env.environment.observe()
            random_env.step_event_runtime(
                {str(key): int(rng.integers(0, 3)) for key in view.active_keys}
            )
        assert random_env.environment is not None
        random_values.append(float(random_env.environment.outcome().utility))
    values = np.asarray(constructive, dtype=np.float64)
    random_array = np.asarray(random_values, dtype=np.float64)
    return {
        "constructive_persistent_min": float(values[:, 0].min()),
        "constructive_short_min": float(values[:, 1].min()),
        "constructive_utility_min": float(values[:, 2].min()),
        "random_positive_utility_fraction": float(np.mean(random_array > 0.0)),
        "random_utility_mean": float(random_array.mean()),
    }


def _load_hierarchical_owner(checkpoint: Path, device: torch.device):
    payload = torch.load(checkpoint, map_location=device, weights_only=False)
    event = payload.get("event_architecture")
    if not isinstance(event, dict) or "event_semantic" not in event:
        raise ValueError("Iteration-5 audit requires the strict semantic checkpoint")
    owner = _make_event_model_owner(
        SimpleNamespace(
            event_architecture_mode="f0",
            event_member_hidden_dim=64,
            event_high_hidden_dim=64,
            event_low_hidden_dim=64,
            event_skill_embedding_dim=16,
        ),
        device,
    )
    owner.commitment_model.load_state_dict(event["commitment_model_state"], strict=True)
    owner.event_critic.load_state_dict(event["event_critic_state"], strict=True)
    owner.low_actor.load_state_dict(event["low_actor_state"], strict=True)
    owner.low_critic.load_state_dict(event["low_critic_state"], strict=True)
    return owner


def _nested_maximum_difference(left: Any, right: Any) -> float:
    if isinstance(left, (torch.Tensor, np.ndarray)) or isinstance(right, (torch.Tensor, np.ndarray)):
        lhs = torch.as_tensor(left).detach().cpu().float()
        rhs = torch.as_tensor(right).detach().cpu().float()
        if lhs.shape != rhs.shape:
            return float("inf")
        return 0.0 if lhs.numel() == 0 else float(torch.max(torch.abs(lhs - rhs)))
    if isinstance(left, dict) and isinstance(right, dict):
        if set(left) != set(right):
            return float("inf")
        return max((_nested_maximum_difference(left[key], right[key]) for key in left), default=0.0)
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        if len(left) != len(right):
            return float("inf")
        return max((_nested_maximum_difference(a, b) for a, b in zip(left, right)), default=0.0)
    return 0.0 if left == right else float("inf")


@torch.no_grad()
def _skill_action_probabilities(owner, observation: np.ndarray, hidden: np.ndarray) -> np.ndarray:
    actor = owner.low_actor
    batch_size = int(owner.n_skills)
    obs = torch.as_tensor(
        observation, dtype=torch.float32, device=owner.device
    ).reshape(1, -1).expand(batch_size, -1)
    skills = torch.arange(batch_size, dtype=torch.long, device=owner.device)
    state = torch.as_tensor(
        hidden, dtype=torch.float32, device=owner.device
    ).reshape(1, -1).expand(batch_size, -1)
    features = actor._features(obs, skills)
    features, _ = actor.actor_rnn(
        features,
        state,
        torch.ones(batch_size, 1, dtype=torch.float32, device=owner.device),
    )
    value = np.asarray(
        actor.actor_act.action_out(features).probs.detach().cpu().numpy(),
        dtype=np.float64,
    )
    if value.shape != (3, 3) or not np.isfinite(value).all():
        raise RuntimeError("Iteration-5 action-probability audit shape is invalid")
    return value


@torch.no_grad()
def _branch_process_effect(
    *,
    owner,
    source_core,
    source_environment,
    source_snapshot,
    episode_id: int,
    audit_index: int,
    focal_key: str,
    forced_skill: int | None,
    replica: int,
) -> np.ndarray:
    collector = SyncEnvCollector([source_environment])
    collector_snapshot = collector.snapshot_event_runtime()
    checkpoint = source_core.checkpoint_payload(
        collector_snapshot=collector_snapshot,
        current_observation_state_boundary={
            "physical_time": int(source_core.physical_time),
            "episode_id": int(episode_id),
        },
        optimizer_states={"high": {}, "low": {}},
        normalizer_states={
            "high": {"schema_version": 1, "enabled": False, "kind": "identity"},
            "low": {"schema_version": 1, "enabled": False, "kind": "identity"},
        },
        pending_membership_transaction=source_core.pending_membership_transaction,
    )
    environment = SpatialDynamicRosterEventEnv(task_master_seed=97_057)
    branch_collector = SyncEnvCollector([environment])
    core = _make_event_runtime(
        owner,
        environment_index=0,
        episode_id=episode_id,
        event_master_seed=77_057,
        action_master_seed=87_057,
    )
    core.restore_checkpoint_payload(checkpoint, collector=branch_collector)
    core.action_rng = make_pcg64_rng(87_057, int(audit_index), 200 + int(replica))
    snapshot = source_snapshot
    start = float(environment.process_state_mapping([focal_key])[focal_key])
    states = []
    for _ in range(12):
        record = core.records.get(focal_key)
        if record is None or record.status != "ACTIVE":
            raise RuntimeError("forced process focal lifecycle left before 12 steps")
        if forced_skill is not None:
            record.active_skill = int(forced_skill)
        actions, _logp, _values = core.low_step(snapshot, deterministic=False)
        routed = {
            key: int(np.asarray(actions[index].detach().cpu()).reshape(-1)[0])
            for index, key in enumerate(snapshot.keys)
        }
        step = environment.step_event_runtime(routed)
        states.append(float(step.info["process_state"][focal_key]))
        core.complete_primitive_transition(float(step.reward))
        if step.terminated:
            if len(states) != 12:
                raise RuntimeError("forced process branch terminated early")
            core.close_terminal()
            break
        if step.next_transaction is None:
            raise RuntimeError("forced process branch lost transaction")
        bound = core.bind_due_frontier(step.next_transaction)
        core.apply_transaction(bound, deterministic_policy=False)
        snapshot = bound.post_membership_pre_policy_snapshot
    branch_collector.close()
    states_array = np.asarray(states, dtype=np.float64)
    if states_array.shape != (12,):
        raise RuntimeError("forced process branch did not execute exactly 12 steps")
    return np.asarray(
        [states_array[-1] - start, float(np.mean(states_array[6:] - start))],
        dtype=np.float64,
    )


@torch.no_grad()
def _batched_branch_process_effects(
    *,
    owner,
    source_core,
    source_environment,
    source_snapshot,
    episode_id: int,
    audit_index: int,
    focal_key: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Evaluate all forced skills and the natural branch in one model batch."""

    branch_specs = (
        (0, 0),
        (0, 1),
        (1, 0),
        (1, 1),
        (2, 0),
        (2, 1),
        (None, 0),
    )
    source_collector = SyncEnvCollector([source_environment])
    branch_collectors: list[SyncEnvCollector] = []
    try:
        collector_snapshot = source_collector.snapshot_event_runtime()
        checkpoint = source_core.checkpoint_payload(
            collector_snapshot=collector_snapshot,
            current_observation_state_boundary={
                "physical_time": int(source_core.physical_time),
                "episode_id": int(episode_id),
            },
            optimizer_states={"high": {}, "low": {}},
            normalizer_states={
                "high": {"schema_version": 1, "enabled": False, "kind": "identity"},
                "low": {"schema_version": 1, "enabled": False, "kind": "identity"},
            },
            pending_membership_transaction=source_core.pending_membership_transaction,
        )

        environments = []
        cores = []
        snapshots = []
        starts = []
        states: list[list[float]] = [[] for _ in branch_specs]
        for _forced_skill, replica in branch_specs:
            environment = SpatialDynamicRosterEventEnv(task_master_seed=97_057)
            collector = SyncEnvCollector([environment])
            core = _make_event_runtime(
                owner,
                environment_index=0,
                episode_id=episode_id,
                event_master_seed=77_057,
                action_master_seed=87_057,
            )
            core.restore_checkpoint_payload(checkpoint, collector=collector)
            core.action_rng = make_pcg64_rng(
                87_057, int(audit_index), 200 + int(replica)
            )
            environments.append(environment)
            branch_collectors.append(collector)
            cores.append(core)
            snapshots.append(source_snapshot)
            starts.append(float(environment.process_state_mapping([focal_key])[focal_key]))

        for step_index in range(12):
            for (forced_skill, _replica), core in zip(branch_specs, cores):
                record = core.records.get(focal_key)
                if record is None or record.status != "ACTIVE":
                    raise RuntimeError("forced process focal lifecycle left before 12 steps")
                if forced_skill is not None:
                    record.active_skill = int(forced_skill)

            low_step = batched_low_step(cores, snapshots, deterministic=False)
            next_snapshots = list(snapshots)
            for branch_index, (core, environment, routed) in enumerate(
                zip(cores, environments, low_step.routed_actions)
            ):
                step = environment.step_event_runtime(routed)
                states[branch_index].append(
                    float(step.info["process_state"][focal_key])
                )
                core.complete_primitive_transition(float(step.reward))
                if step.terminated:
                    if step_index != 11:
                        raise RuntimeError("forced process branch terminated early")
                    core.close_terminal()
                    continue
                if step.next_transaction is None:
                    raise RuntimeError("forced process branch lost transaction")
                bound = core.bind_due_frontier(step.next_transaction)
                core.apply_transaction(bound, deterministic_policy=False)
                next_snapshots[branch_index] = (
                    bound.post_membership_pre_policy_snapshot
                )
            snapshots = next_snapshots

        effects = []
        for branch_states, start in zip(states, starts):
            states_array = np.asarray(branch_states, dtype=np.float64)
            if states_array.shape != (12,):
                raise RuntimeError("forced process branch did not execute exactly 12 steps")
            effects.append(
                np.asarray(
                    [
                        states_array[-1] - start,
                        float(np.mean(states_array[6:] - start)),
                    ],
                    dtype=np.float64,
                )
            )
        forced = np.asarray(effects[:6], dtype=np.float64).reshape(3, 2, 2)
        natural = np.asarray(effects[6], dtype=np.float64)
        return forced, natural
    finally:
        for collector in reversed(branch_collectors):
            collector.close()
        source_collector.close()


def _episode_cluster_ci(
    values: np.ndarray,
    episodes: np.ndarray,
    *,
    seed: int,
    repetitions: int = 10_000,
) -> list[float]:
    values = np.asarray(values, dtype=np.float64).reshape(-1)
    episodes = np.asarray(episodes, dtype=np.int64).reshape(-1)
    unique = np.unique(episodes)
    if values.size != episodes.size or unique.size == 0 or not np.isfinite(values).all():
        raise ValueError("cluster bootstrap inputs are invalid")
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed])))
    draws = np.empty(int(repetitions), dtype=np.float64)
    by_episode = {episode: values[episodes == episode] for episode in unique}
    for index in range(draws.size):
        selected = rng.choice(unique, size=unique.size, replace=True)
        draws[index] = float(np.mean(np.concatenate([by_episode[int(item)] for item in selected])))
    return [float(np.quantile(draws, 0.025)), float(values.mean()), float(np.quantile(draws, 0.975))]


def _cross_replica_skill_energy(
    forced: np.ndarray, left: int, right: int
) -> np.ndarray:
    difference = forced[:, left] - forced[:, right]
    return np.maximum(np.sum(difference[:, 0] * difference[:, 1], axis=1), 0.0)


def _select_reference_pair(reference_forced: np.ndarray) -> tuple[tuple[int, int], dict[tuple[int, int], float]]:
    """Freeze one lexicographic maximum-energy pair from the reference fold."""

    pair_energy = {
        (left, right): float(
            _cross_replica_skill_energy(reference_forced, left, right).mean()
        )
        for left in range(3)
        for right in range(left + 1, 3)
    }
    selected = sorted(pair_energy, key=lambda pair: (-pair_energy[pair], pair))[0]
    return selected, pair_energy


def _balanced_episode_cluster_ci(
    values: np.ndarray,
    labels: np.ndarray,
    episodes: np.ndarray,
    pair: tuple[int, int],
    *,
    seed: int,
    repetitions: int,
) -> tuple[list[float], bool]:
    """Macro-average the frozen pair while clustering within source episode."""

    episode_means: dict[int, np.ndarray] = {}
    for skill in pair:
        skill_episodes = np.unique(episodes[labels == skill])
        if skill_episodes.size < 2:
            return [0.0, 0.0, 0.0], False
        episode_means[skill] = np.asarray(
            [
                values[(labels == skill) & (episodes == episode)].mean()
                for episode in skill_episodes
            ],
            dtype=np.float64,
        )
    observed = float(np.mean([episode_means[skill].mean() for skill in pair]))
    rng = np.random.Generator(np.random.PCG64(np.random.SeedSequence([seed])))
    draws = np.empty(int(repetitions), dtype=np.float64)
    for index in range(draws.size):
        draws[index] = float(
            np.mean(
                [
                    rng.choice(
                        episode_means[skill],
                        size=episode_means[skill].size,
                        replace=True,
                    ).mean()
                    for skill in pair
                ]
            )
        )
    return [
        float(np.quantile(draws, 0.025)),
        observed,
        float(np.quantile(draws, 0.975)),
    ], True


def _balanced_margin(
    natural: np.ndarray,
    centroids: np.ndarray,
    labels: np.ndarray,
    pair: tuple[int, int],
) -> tuple[np.ndarray, float]:
    margins = np.empty(labels.size, dtype=np.float64)
    for index, skill in enumerate(labels):
        other = pair[1] if int(skill) == pair[0] else pair[0]
        margins[index] = float(
            np.linalg.norm(natural[index] - centroids[other])
            - np.linalg.norm(natural[index] - centroids[int(skill)])
        )
    return margins, float(
        np.mean([margins[labels == skill].mean() for skill in pair])
    )


def _matched_shuffle_residual_ci(
    *,
    natural: np.ndarray,
    centroids: np.ndarray,
    labels: np.ndarray,
    masks: np.ndarray,
    starts: np.ndarray,
    pair: tuple[int, int],
    repetitions: int,
) -> tuple[list[float], bool]:
    """Frozen context/mask-matched label-shuffle overlap residual."""

    if any(np.count_nonzero(labels == skill) == 0 for skill in pair):
        return [0.0, 0.0, 0.0], False
    _observed_rows, observed = _balanced_margin(natural, centroids, labels, pair)
    groups = {
        stratum: np.asarray(
            [
                index
                for index in range(labels.size)
                if (int(masks[index]), float(starts[index])) == stratum
            ],
            dtype=np.int64,
        )
        for stratum in sorted(
            {(int(mask), float(start)) for mask, start in zip(masks, starts)}
        )
    }
    rng = np.random.Generator(np.random.PCG64(307_058))
    residuals = np.empty(int(repetitions), dtype=np.float64)
    for draw_index in range(residuals.size):
        shuffled = labels.copy()
        for indices in groups.values():
            shuffled[indices] = rng.permutation(labels[indices])
        if any(np.count_nonzero(shuffled == skill) == 0 for skill in pair):
            return [0.0, 0.0, 0.0], False
        _rows, shuffled_value = _balanced_margin(
            natural, centroids, shuffled, pair
        )
        residuals[draw_index] = observed - shuffled_value
    return [
        float(np.quantile(residuals, 0.025)),
        float(np.mean(residuals)),
        float(np.quantile(residuals, 0.975)),
    ], True


@torch.no_grad()
def _semantic_materiality_audit(
    owner, natural_shares: list[float], *, smoke: bool = False
) -> dict[str, Any]:
    records = []
    audit_index = 0
    episode_count = 2 if smoke else 32
    repetitions = 100 if smoke else 10_000
    for episode_id in range(episode_count):
        environment = SpatialDynamicRosterEventEnv(task_master_seed=97_057)
        core = _make_event_runtime(
            owner,
            environment_index=0,
            episode_id=episode_id,
            event_master_seed=77_057,
            action_master_seed=87_057,
        )
        bound = core.bind_due_frontier(environment.reset_event_runtime(episode_id))
        core.apply_transaction(bound, deterministic_policy=False)
        snapshot = bound.post_membership_pre_policy_snapshot
        selected_times = (
            {1}
            if smoke
            else {
                1 + episode_id % 8,
                21 + episode_id % 8,
                41 + episode_id % 8,
                61 + episode_id % 8,
            }
        )
        for physical_time in range(HORIZON):
            if physical_time in selected_times:
                focal_key = snapshot.keys[audit_index % len(snapshot.keys)]
                focal_index = snapshot.keys.index(focal_key)
                record = core.records[focal_key]
                natural_skill = int(record.active_skill)
                probabilities = _skill_action_probabilities(
                    owner,
                    np.asarray(snapshot.members[focal_index].observation, dtype=np.float32),
                    np.asarray(record.low_actor_hidden, dtype=np.float32),
                )
                forced, natural_effect = _batched_branch_process_effects(
                    owner=owner,
                    source_core=core,
                    source_environment=environment,
                    source_snapshot=snapshot,
                    episode_id=episode_id,
                    audit_index=audit_index,
                    focal_key=focal_key,
                )
                records.append(
                    {
                        "episode": episode_id,
                        "mask": len(snapshot.keys),
                        "start": float(environment.process_state_mapping([focal_key])[focal_key]),
                        "natural_skill": natural_skill,
                        "probabilities": probabilities,
                        "forced": forced,
                        "natural_effect": natural_effect,
                    }
                )
                audit_index += 1
            actions, _logp, _values = core.low_step(snapshot, deterministic=False)
            routed = {
                key: int(np.asarray(actions[index].detach().cpu()).reshape(-1)[0])
                for index, key in enumerate(snapshot.keys)
            }
            step = environment.step_event_runtime(routed)
            core.complete_primitive_transition(float(step.reward))
            if step.terminated:
                core.close_terminal()
                break
            assert step.next_transaction is not None
            bound = core.bind_due_frontier(step.next_transaction)
            core.apply_transaction(bound, deterministic_policy=False)
            snapshot = bound.post_membership_pre_policy_snapshot
    expected_sources = 2 if smoke else 128
    if len(records) != expected_sources:
        raise RuntimeError("Iteration-5 semantic audit source count is not exact")
    source_count = len(records)
    reference_episodes = {0} if smoke else set(range(16))
    inference_episodes = {1} if smoke else set(range(16, 32))
    reference = [row for row in records if int(row["episode"]) in reference_episodes]
    inference = [row for row in records if int(row["episode"]) in inference_episodes]
    expected_fold_sources = 1 if smoke else 64
    if len(reference) != expected_fold_sources or len(inference) != expected_fold_sources:
        raise RuntimeError("Iteration-5 reference/inference folds are not exact")
    reference_forced = np.asarray([row["forced"] for row in reference])
    selected_pair, pair_energy = _select_reference_pair(reference_forced)
    episodes = np.asarray([row["episode"] for row in inference], dtype=np.int64)
    pair_rows = {}
    inference_forced = np.asarray([row["forced"] for row in inference])
    for left in range(3):
        for right in range(left + 1, 3):
            tv = np.asarray(
                [
                    0.5
                    * np.abs(
                        row["probabilities"][left]
                        - row["probabilities"][right]
                    ).sum()
                    for row in inference
                ]
            )
            effect = np.sqrt(
                _cross_replica_skill_energy(inference_forced, left, right)
            )
            tv_ci = _episode_cluster_ci(
                tv,
                episodes,
                seed=117_057 + 10 * left + right,
                repetitions=repetitions,
            )
            effect_ci = _episode_cluster_ci(
                effect,
                episodes,
                seed=127_057 + 10 * left + right,
                repetitions=repetitions,
            )
            selected = (left, right) == selected_pair
            passes = bool(
                selected
                and tv_ci[0] > 1.0 / 12.0
                and effect_ci[0] > 1.0 / 12.0
                and natural_shares[left] >= 0.10
                and natural_shares[right] >= 0.10
            )
            pair_rows[f"{left}-{right}"] = {
                "selected_on_reference_fold": selected,
                "reference_mean_cross_replica_energy": pair_energy[(left, right)],
                "action_tv_ci95": tv_ci,
                "forced_process_effect_distance_ci95": effect_ci,
                "natural_share_left": float(natural_shares[left]),
                "natural_share_right": float(natural_shares[right]),
                "material_pair_pass": passes,
            }
    reference_centroids = np.asarray(
        [reference_forced[:, skill].mean(axis=(0, 1)) for skill in range(3)]
    )
    selected_inference = [
        row for row in inference if int(row["natural_skill"]) in selected_pair
    ]
    if selected_inference and all(
        any(int(row["natural_skill"]) == skill for row in selected_inference)
        for skill in selected_pair
    ):
        natural = np.asarray(
            [row["natural_effect"] for row in selected_inference], dtype=np.float64
        )
        skills = np.asarray(
            [row["natural_skill"] for row in selected_inference], dtype=np.int64
        )
        natural_episodes = np.asarray(
            [row["episode"] for row in selected_inference], dtype=np.int64
        )
        masks = np.asarray([row["mask"] for row in selected_inference], dtype=np.int64)
        starts = np.asarray(
            [row["start"] for row in selected_inference], dtype=np.float64
        )
        overlap_margin, _observed_overlap = _balanced_margin(
            natural, reference_centroids, skills, selected_pair
        )
        overlap_ci, overlap_support = _balanced_episode_cluster_ci(
            overlap_margin,
            skills,
            natural_episodes,
            selected_pair,
            seed=307_057,
            repetitions=repetitions,
        )
        residual_ci, shuffle_support = _matched_shuffle_residual_ci(
            natural=natural,
            centroids=reference_centroids,
            labels=skills,
            masks=masks,
            starts=starts,
            pair=selected_pair,
            repetitions=repetitions,
        )
    else:
        overlap_ci, residual_ci = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
        overlap_support = shuffle_support = False
    selected_name = f"{selected_pair[0]}-{selected_pair[1]}"
    return {
        "scientific": not smoke,
        "source_count": source_count,
        "effect_shape": [source_count, 3, 2, 2],
        "process_view": "route_only_position_endpoint_and_second_half_mean",
        "pairs": pair_rows,
        "reference_episodes": sorted(reference_episodes),
        "inference_episodes": sorted(inference_episodes),
        "selected_pair": list(selected_pair),
        "selected_pair_support": {
            "natural_overlap": bool(overlap_support),
            "matched_shuffle": bool(shuffle_support),
            "selected_inference_sources": len(selected_inference),
        },
        "natural_to_forced_overlap_margin_ci95": overlap_ci,
        "context_mask_matched_shuffle_residual_ci95": residual_ci,
        "material_semantics_pass": bool(
            pair_rows[selected_name]["material_pair_pass"]
            and overlap_support
            and shuffle_support
            and overlap_ci[0] > 0.0
            and residual_ci[0] > 0.0
        ),
    }


def _run_direct_arm(
    *, output_root: Path, device: torch.device, num_envs: int, updates: int, eval_episodes: int
) -> dict[str, Any]:
    torch.manual_seed(MODEL_INITIALIZATION_SEED)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(MODEL_INITIALIZATION_SEED)
    model = DirectPrimitiveARPolicy().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    initial_state = model_state_copy(model)
    episode_ids = tuple(range(eval_episodes))
    uniforms = make_action_uniforms(episode_ids)
    zero_det = evaluate_direct_policy(
        model,
        episode_ids=episode_ids,
        deterministic=True,
        device=device,
        ledger_factory=make_spatial_dynamic_roster_ledger,
        environment_factory=make_spatial_environment,
    )
    zero_stoch = evaluate_direct_policy(
        model,
        episode_ids=episode_ids,
        deterministic=False,
        device=device,
        uniforms=uniforms,
        ledger_factory=make_spatial_dynamic_roster_ledger,
        environment_factory=make_spatial_environment,
    )
    maxima = {
        "logp_max_error": 0.0,
        "joint_logp_max_error": 0.0,
        "value_max_error": 0.0,
        "hidden_max_error": 0.0,
        "prefix_max_error": 0.0,
    }
    for update in range(updates):
        trajectory = collect_direct_trajectory(
            model,
            ledger_ids=range(update * num_envs, (update + 1) * num_envs),
            ledger_seed=57_057,
            device=device,
            ledger_factory=make_spatial_dynamic_roster_ledger,
            environment_factory=make_spatial_environment,
        )
        metrics = optimize_direct_update(
            model, optimizer, trajectory, device=device, ppo_passes=PPO_PASSES
        )
        for name in maxima:
            maxima[name] = max(maxima[name], float(metrics[name]))
    checkpoint_path = output_root / "checkpoints" / "latest.pt"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    save_checkpoint(
        checkpoint_path,
        model=model,
        optimizer=optimizer,
        completed_updates=updates,
        next_ledger_id=updates * num_envs,
    )
    reloaded = DirectPrimitiveARPolicy().to(device)
    reload_optimizer = torch.optim.Adam(reloaded.parameters(), lr=LEARNING_RATE)
    checkpoint_bundle = load_checkpoint(
        checkpoint_path, model=reloaded, optimizer=reload_optimizer
    )
    checkpoint_state_error = maximum_state_difference(
        model_state_copy(model), model_state_copy(reloaded)
    )
    checkpoint_optimizer_error = nested_state_maximum_difference(
        optimizer.state_dict(), reload_optimizer.state_dict()
    )
    final_det = evaluate_direct_policy(
        reloaded,
        episode_ids=episode_ids,
        deterministic=True,
        device=device,
        ledger_factory=make_spatial_dynamic_roster_ledger,
        environment_factory=make_spatial_environment,
    )
    final_stoch = evaluate_direct_policy(
        reloaded,
        episode_ids=episode_ids,
        deterministic=False,
        device=device,
        uniforms=uniforms,
        ledger_factory=make_spatial_dynamic_roster_ledger,
        environment_factory=make_spatial_environment,
    )
    ci = paired_bootstrap_ci(
        final_det["utility"] - zero_det["utility"], repetitions=10_000, seed=BOOTSTRAP_SEED
    )
    final_state = model_state_copy(model)
    parameter_drift = maximum_state_difference(initial_state, final_state)
    implementation_valid = bool(
        all(value <= 1e-6 for value in maxima.values())
        and state_dict_finite(final_state)
        and parameter_drift > 1e-8
        and checkpoint_state_error == 0.0
        and checkpoint_optimizer_error == 0.0
        and int(checkpoint_bundle["completed_updates"]) == updates
        and int(checkpoint_bundle["next_ledger_id"]) == updates * num_envs
    )
    payload = {
        "arm": "c3_direct",
        "implementation_valid": implementation_valid,
        "counts": {
            "environment_steps": updates * num_envs * HORIZON,
            "optimizer_steps": updates * PPO_PASSES,
        },
        "replay": maxima,
        "parameter_drift_max_abs": parameter_drift,
        "checkpoint_state_max_error": checkpoint_state_error,
        "checkpoint_optimizer_max_error": checkpoint_optimizer_error,
        "zero": {
            "deterministic": {name: zero_det[name] for name in ("persistent_mean", "short_mean", "utility_mean")},
            "stochastic": {name: zero_stoch[name] for name in ("persistent_mean", "short_mean", "utility_mean")},
        },
        "final": {
            "deterministic": {name: final_det[name] for name in ("persistent_mean", "short_mean", "utility_mean")},
            "stochastic": {name: final_stoch[name] for name in ("persistent_mean", "short_mean", "utility_mean")},
        },
        "paired_final_minus_zero_deterministic_utility_ci95": ci,
    }
    _atomic_json(output_root / "result" / "iteration5_arm.json", payload)
    return payload


def _hierarchical_command(
    *, arm: str, output_root: Path, num_envs: int, updates: int, smoke: bool
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "ha_ctse_process.train",
        "--config",
        "ha_ctse_process.config",
        "--high_controller",
        "variable_roster_event",
        "--event_architecture_mode",
        "f0",
        "--iteration5_process_semantics_arm",
        arm,
        "--scenario",
        "generic_short_dynamic_roster",
        "--device",
        "cuda",
        "--collector_backend",
        "sync",
        "--num_envs",
        str(num_envs),
        "--rollout_length",
        str(HORIZON),
        "--total_timesteps",
        str(num_envs * HORIZON * updates),
        "--log_dir",
        str(output_root),
    ]
    if smoke:
        command.append("--iteration5_smoke")
    return command


def run_iteration5(
    *, output_root: Path, smoke: bool, num_envs: int, updates: int, eval_episodes: int
) -> dict[str, Any]:
    if not smoke and (num_envs, updates, eval_episodes) != (
        FORMAL_NUM_ENVS,
        FORMAL_UPDATES,
        FORMAL_EVAL_EPISODES,
    ):
        raise ValueError("formal Iteration-5 requires the exact 16x250x256 contract")
    if not torch.cuda.is_available():
        raise RuntimeError("Iteration-5 requires CUDA")
    output_root.mkdir(parents=True, exist_ok=True)
    run_root = output_root.resolve()
    run_id = output_root.name
    source_commit = _git_source_commit()
    status_path = output_root / "runner_status.txt"
    arms = {
        name: output_root / name
        for name in ("c1_semantic_on", "c1_semantic_off", "c3_direct")
    }
    for path in arms.values():
        path.mkdir(parents=True, exist_ok=True)
    _status(
        status_path,
        state="running",
        phase="training",
        scientific=not smoke,
        run_id=run_id,
        run_root=run_root,
        source_commit=source_commit,
    )
    processes: dict[str, subprocess.Popen] = {}
    try:
        processes = {
            arm: subprocess.Popen(
                _hierarchical_command(
                    arm=arm,
                    output_root=arms[arm],
                    num_envs=num_envs,
                    updates=updates,
                    smoke=smoke,
                ),
                cwd=PROJECT_ROOT,
            )
            for arm in ("c1_semantic_on", "c1_semantic_off")
        }
        # The direct arm trains in this parent while both hierarchical workers are
        # live, so all three registered arms overlap on the same CUDA launch.
        direct = _run_direct_arm(
            output_root=arms["c3_direct"],
            device=torch.device("cuda"),
            num_envs=num_envs,
            updates=updates,
            eval_episodes=eval_episodes,
        )
    except BaseException:
        for process in processes.values():
            if process.poll() is None:
                process.terminate()
        for process in processes.values():
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        raise
    return_codes = {arm: process.wait() for arm, process in processes.items()}
    failures = {arm: code for arm, code in return_codes.items() if code != 0}
    if failures:
        raise RuntimeError(f"Iteration-5 hierarchical workers failed: {failures}")
    on = json.loads((arms["c1_semantic_on"] / "result" / "iteration5_arm.json").read_text(encoding="utf-8"))
    off = json.loads((arms["c1_semantic_off"] / "result" / "iteration5_arm.json").read_text(encoding="utf-8"))
    zero_on = torch.load(
        arms["c1_semantic_on"] / "checkpoints" / "update_000_eval.pt",
        map_location="cpu",
        weights_only=False,
    )["event_architecture"]
    zero_off = torch.load(
        arms["c1_semantic_off"] / "checkpoints" / "update_000_eval.pt",
        map_location="cpu",
        weights_only=False,
    )["event_architecture"]
    policy_initial_error = max(
        _nested_maximum_difference(zero_on[name], zero_off[name])
        for name in (
            "commitment_model_state",
            "event_critic_state",
            "low_actor_state",
            "low_critic_state",
        )
    )
    semantic_on_state = dict(zero_on["event_semantic"]["trainer"])
    semantic_off_state = dict(zero_off["event_semantic"]["trainer"])
    semantic_on_state.pop("beta")
    semantic_off_state.pop("beta")
    semantic_initial_error = _nested_maximum_difference(
        semantic_on_state, semantic_off_state
    )
    controls = _carrier_controls(8 if smoke else 256)
    carrier_pass = bool(
        controls["constructive_persistent_min"] >= 0.95
        and controls["constructive_short_min"] >= 0.95
        and controls["constructive_utility_min"] >= 0.95
        and controls["random_positive_utility_fraction"] >= 0.20
        and controls["random_utility_mean"] < 0.55
    )
    implementation_valid = bool(
        on["implementation_valid"]
        and off["implementation_valid"]
        and direct["implementation_valid"]
        and policy_initial_error == 0.0
        and semantic_initial_error == 0.0
    )
    if smoke:
        status = (
            "SMOKE_COMPLETE"
            if implementation_valid and carrier_pass
            else "SMOKE_INVALID"
        )
        semantic_audit = None
        semantic_pass = False
        task_access = False
        direct_access = False
        on_minus_off_ci = None
        final_minus_zero_ci = None
    else:
        owner = _load_hierarchical_owner(
            arms["c1_semantic_on"] / "checkpoints" / "latest.pt",
            torch.device("cuda"),
        )
        natural_shares = list(
            on["final"]["stochastic"]["natural_skill_step_shares"]
        )
        semantic_audit = _semantic_materiality_audit(owner, natural_shares)
        semantic_pass = bool(semantic_audit["material_semantics_pass"])
        on_final = on["final"]["deterministic"]
        on_zero = on["zero"]["deterministic"]
        off_final = off["final"]["deterministic"]
        final_minus_zero_ci = paired_bootstrap_ci(
            np.asarray(on_final["utility"], dtype=np.float64)
            - np.asarray(on_zero["utility"], dtype=np.float64),
            repetitions=10_000,
            seed=157_057,
        )
        on_minus_off_ci = paired_bootstrap_ci(
            np.asarray(on_final["utility"], dtype=np.float64)
            - np.asarray(off_final["utility"], dtype=np.float64),
            repetitions=10_000,
            seed=167_057,
        )
        task_access = bool(
            float(on_final["utility_mean"]) >= 0.60
            and float(on_final["persistent_mean"]) >= 0.55
            and float(on_final["short_mean"]) >= 0.55
            and final_minus_zero_ci[0] > 0.10
            and on_minus_off_ci[0] > 0.03
        )
        c3_final = direct["final"]
        direct_access = bool(
            float(c3_final["deterministic"]["utility_mean"]) >= 0.70
            and float(c3_final["deterministic"]["persistent_mean"]) >= 0.65
            and float(c3_final["deterministic"]["short_mean"]) >= 0.65
            and float(c3_final["stochastic"]["utility_mean"]) >= 0.60
            and float(direct["paired_final_minus_zero_deterministic_utility_ci95"][0]) > 0.15
        )
        semantic_off_initial_equal = bool(
            on["zero"] == off["zero"]
        )
        implementation_valid = bool(implementation_valid and semantic_off_initial_equal)
        if not implementation_valid:
            status = "INVALID_ITERATION5_IMPLEMENTATION"
        elif not carrier_pass or not direct_access:
            status = "RETIRE_SPATIAL_CARRIER_NO_DIRECT_ACCESS"
        elif not semantic_pass:
            status = "FAIL_C1_NO_MATERIAL_SEMANTICS"
        elif not task_access:
            status = "FAIL_C1_SEMANTICS_WITHOUT_TASK_VALUE"
        else:
            status = "PASS_C1_PROCESS_SEMANTICS"
    result = {
        "schema_version": 1,
        "stage": "iteration5_spatial_process_semantics",
        "scientific": not smoke,
        "run_id": run_id,
        "run_root": str(run_root),
        "source_commit": source_commit,
        "status": status,
        "implementation_valid": implementation_valid,
        "carrier": controls,
        "initialization": {
            "policy_max_error": policy_initial_error,
            "semantic_excluding_beta_max_error": semantic_initial_error,
        },
        "arms": {"c1_semantic_on": on, "c1_semantic_off": off, "c3_direct": direct},
        "semantic_audit": semantic_audit,
        "semantic_pass": semantic_pass,
        "task_access_pass": task_access,
        "direct_access_pass": direct_access,
        "paired_semantic_on_minus_off_utility_ci95": on_minus_off_ci,
        "paired_semantic_on_final_minus_zero_utility_ci95": final_minus_zero_ci,
        "thresholds": {
            "material_action_tv_lcb_exclusive": 1.0 / 12.0,
            "material_forced_effect_lcb_exclusive": 1.0 / 12.0,
            "selected_skill_natural_share_min": 0.10,
            "overlap_margin_lcb_exclusive": 0.0,
            "matched_shuffle_residual_lcb_exclusive": 0.0,
            "c1_utility_min": 0.60,
            "c1_persistent_min": 0.55,
            "c1_short_min": 0.55,
            "c1_final_minus_zero_lcb_exclusive": 0.10,
            "c1_on_minus_off_lcb_exclusive": 0.03,
            "c3_utility_deterministic_min": 0.70,
            "c3_persistent_deterministic_min": 0.65,
            "c3_short_deterministic_min": 0.65,
            "c3_utility_stochastic_min": 0.60,
            "c3_final_minus_zero_lcb_exclusive": 0.15,
        },
        "reason": (
            "non-scientific operational smoke"
            if smoke
            else "registered priority disposition from carrier, semantic and task evidence"
        ),
    }
    result_path = output_root / "result" / "iteration5_process_semantics.json"
    _atomic_json(result_path, result)
    _status(
        status_path,
        state="complete",
        phase="terminal",
        status=status,
        result=result_path,
        run_id=run_id,
        run_root=run_root,
        source_commit=source_commit,
    )
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--num-envs", type=int, default=FORMAL_NUM_ENVS)
    parser.add_argument("--updates", type=int, default=FORMAL_UPDATES)
    parser.add_argument("--eval-episodes", type=int, default=FORMAL_EVAL_EPISODES)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        run_iteration5(
            output_root=args.output_root,
            smoke=bool(args.smoke),
            num_envs=int(args.num_envs),
            updates=int(args.updates),
            eval_episodes=int(args.eval_episodes),
        )
        return 0
    except Exception as error:
        args.output_root.mkdir(parents=True, exist_ok=True)
        (args.output_root / "runner_stderr.log").write_text(traceback.format_exc(), encoding="utf-8")
        _status(
            args.output_root / "runner_status.txt",
            state="failed",
            phase="runner",
            error=f"{type(error).__name__}: {error}",
            run_id=args.output_root.name,
            run_root=args.output_root.resolve(),
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
