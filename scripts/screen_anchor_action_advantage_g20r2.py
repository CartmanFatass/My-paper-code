"""Run the bounded paired G20R2 anchor-policy action-advantage screen.

Implements the re-registered contract in
``docs/research/designs/ANCHOR_POLICY_ACTION_ADVANTAGE_G20R2.md``. Same
layering as the retired ``screen_anchor_action_advantage_g20r.py``: G17/G18
trajectory collection, fast-then-delayed training, behavioral evaluation, and
a result-json with the same top-level shape (``schema_version``, ``algorithm``,
``runtime``, ``configuration``, ``source_controls``, ``source_results``,
``metrics``, ``wall_seconds``) plus a ``branches`` dict keyed by source instead
of a single ``branch`` field, because design section 8 forbids a global
identification Boolean across sources.

No compute is authorized by this task. This module is built and unit-tested
at small scale only; nothing here invokes ``run_screen`` end to end, and
nothing writes under ``logs/``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from typing import Any, Callable, Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import continuous_service_roster_proxy_g17 as g17_source
from ha_ctse_process import delayed_battery_roster_g18 as battery_source
from ha_ctse_process.anchor_action_advantage_g20r2 import (
    AnchorActionTrajectory,
    BASELINE_SAMPLES_K,
    FastAnchorActionAdvantagePolicy,
    attach_prefix_credit,
    maximum_state_difference,
    optimize_delayed_update,
    optimize_fast_update,
    optimize_qualification_update,
    residual_action_space_score,
    stage_a_p2_authority_check,
    stage_a_source_effect,
    stage_b1_contrast_alignment,
    stage_b1_recalibrated_r2,
    stage_b2_gradient_alignment,
    validate_disjoint_roles,
)
from ha_ctse_process.separated_credit_g18 import evaluate_battery_policy
from scripts import run_continuous_service_roster_proxy_g17 as g17_runner


SCHEMA_VERSION = 1
ALGORITHM_ID = "ANCHOR_POLICY_ACTION_ADVANTAGE_G20R2"
GAMMA = 0.99
HIDDEN_DIM = 32
LEARNING_RATE = 1e-3
INITIAL_LOG_STD = -1.0
PPO_PASSES = 2
NUM_ENVS = 8
G17_QUALIFICATION_UPDATES = 40
G17_FAST_UPDATES = 100
G17_DELAYED_UPDATES = 100
G18_QUALIFICATION_UPDATES = 40
G18_FAST_UPDATES = 100
G18_DELAYED_UPDATES = 300
G17_EVAL_EPISODES = 48
G18_SLOT_PERMUTATIONS = 3
AUDIT_EPISODES = 8
AUDIT_PROBE_POINTS_PER_EPISODE = 3
AUDIT_SUFFIX_REPLICATES = 4

# Design section 11's frozen seeds -- a fresh block disjoint from every
# earlier package including G20R. `qualification` and `audit_prefix` /
# `audit_suffix` are free engineering-choice additions: section 11 does not
# separately enumerate a stream for the critic-only qualification collection
# (it reuses the same `*_action`/`*_model` training stream at a disjoint
# episode-id block, exactly as G20R distinguished its fast and delayed
# phases) or for the two audit sub-streams the paired-replay procedure needs
# (a "prefix" stream that fixes the decision history h, and a "suffix"
# stream that is deliberately re-drawn per Monte Carlo replicate to average
# out suffix noise, design section 2's "accounting for suffix Monte Carlo
# uncertainty"). Both derive deterministically from the registered
# `g17_audit` / `g18_audit` seed so they never touch the training seeds.
SEEDS = {
    "g17": {
        "model": 3_019_000,
        "train_ledger": 3_029_000,
        "action": 3_039_000,
        "evaluation_ledger": 3_049_000,
        "evaluation_action": 3_059_000,
        "audit": 3_069_000,
        "baseline": 3_079_000,
    },
    "g18": {
        "model": 3_119_000,
        "action": 3_139_000,
        "audit": 3_149_000,
        "baseline": 3_159_000,
    },
}
BASELINE_SAMPLES_K_CONFIGURED = BASELINE_SAMPLES_K  # design section 11: 8

REPLAY_TOLERANCE = 1e-6
G17_UTILITY_FLOOR = 0.90
G17_GAIN_FLOOR = 0.10
G17_MINIMUM_EPISODE_FLOOR = 0.80
G17_CORRELATION_FLOOR = 0.90
G17_MAE_CEILING = 0.05
G18_UTILITY_FLOOR = 0.95
G18_GAIN_FLOOR = 0.10
G18_SPIKE_UTILITY_FLOOR = 0.90
G18_ROTATING_EFFORT_SHARE_FLOOR = 0.75

if len(battery_source.GATE_SLOT_ORDERS) != G18_SLOT_PERMUTATIONS:
    raise ValueError("G20R2 screen slot-permutation count differs from the frozen design")


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _runtime_identity() -> dict[str, Any]:
    return {
        "backend": "cpu",
        "torch": str(torch.__version__),
        "torch_threads": int(torch.get_num_threads()),
        "python": str(Path(sys.executable).resolve()),
    }


def _configuration() -> dict[str, Any]:
    return {
        "gamma": GAMMA,
        "hidden_dim": HIDDEN_DIM,
        "learning_rate": LEARNING_RATE,
        "initial_log_std": INITIAL_LOG_STD,
        "ppo_passes": PPO_PASSES,
        "num_envs": NUM_ENVS,
        "g17_qualification_updates": G17_QUALIFICATION_UPDATES,
        "g17_fast_updates": G17_FAST_UPDATES,
        "g17_delayed_updates": G17_DELAYED_UPDATES,
        "g18_qualification_updates": G18_QUALIFICATION_UPDATES,
        "g18_fast_updates": G18_FAST_UPDATES,
        "g18_delayed_updates": G18_DELAYED_UPDATES,
        "g17_eval_episodes": G17_EVAL_EPISODES,
        "baseline_samples_k": BASELINE_SAMPLES_K_CONFIGURED,
        "audit_episodes": AUDIT_EPISODES,
        "audit_probe_points_per_episode": AUDIT_PROBE_POINTS_PER_EPISODE,
        "audit_suffix_replicates": AUDIT_SUFFIX_REPLICATES,
        "fast_optimizer": "adam",
        "qualification_critic_optimizer": "adam",
        "delayed_residual_optimizer": "adam",
        "critic_optimizer": "adam",
        "delayed_residual_initialization": "exact_zero_output",
        "delayed_credit_rule": "anchor_policy_conditional_action_advantage_g20r2",
        "delayed_centering_rule": "active_set_exact",
        "identification_protocol": "stage_a_b1_b2_sequential_source_specific",
    }


def _dimensions(source: str) -> tuple[int, int, int, int]:
    if source == "g17":
        return (
            g17_source.OBSERVATION_DIM,
            g17_source.CRITIC_STATE_DIM,
            g17_source.CAPACITY,
            g17_source.ACTION_DIM,
        )
    if source == "g18":
        return (
            battery_source.OBSERVATION_DIM,
            battery_source.CRITIC_STATE_DIM,
            battery_source.CAPACITY,
            battery_source.ACTION_DIM,
        )
    raise ValueError(f"unknown G20R2 source: {source}")


def make_model(source: str) -> FastAnchorActionAdvantagePolicy:
    observation_dim, critic_state_dim, capacity, action_dim = _dimensions(source)
    model = FastAnchorActionAdvantagePolicy(
        observation_dim,
        critic_state_dim,
        member_capacity=capacity,
        action_dim=action_dim,
        hidden_dim=HIDDEN_DIM,
        current_observation_residual=True,
    )
    with torch.no_grad():
        model.log_std.fill_(INITIAL_LOG_STD)
    return model


def _battery_action_noise(
    episode_ids: Iterable[int], *, action_seed: int, stream: int = 380
) -> np.ndarray:
    rows = []
    for episode_id in episode_ids:
        rng = np.random.default_rng(
            np.random.SeedSequence([int(action_seed), int(episode_id), int(stream)])
        )
        rows.append(
            rng.standard_normal(
                (
                    battery_source.HORIZON,
                    battery_source.CAPACITY,
                    battery_source.ACTION_DIM,
                )
            ).astype(np.float32)
        )
    if not rows:
        raise ValueError("G20R2 battery collection requires an episode")
    return np.stack(rows, axis=1)


def collect_battery_trajectory(
    model: FastAnchorActionAdvantagePolicy,
    *,
    episode_ids: Iterable[int],
    action_seed: int,
    baseline_seed: int,
    device: torch.device,
    deterministic: bool = False,
) -> AnchorActionTrajectory:
    ids = tuple(int(value) for value in episode_ids)
    if not ids:
        raise ValueError("G20R2 battery collection requires at least one episode")
    ledgers = tuple(
        battery_source.make_ledger(
            battery_source.GATE_SLOT_ORDERS[
                episode_id % len(battery_source.GATE_SLOT_ORDERS)
            ]
        )
        for episode_id in ids
    )
    environments = tuple(
        battery_source.BatteryRosterEnv(ledger) for ledger in ledgers
    )
    batch = len(ids)
    noise = _battery_action_noise(ids, action_seed=action_seed)
    hidden = torch.zeros(
        (batch, battery_source.CAPACITY, model.hidden_dim),
        dtype=torch.float32,
        device=device,
    )
    shapes = {
        "observations": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            battery_source.OBSERVATION_DIM,
        ),
        "active_mask": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
        ),
        "critic_states": (
            battery_source.HORIZON,
            batch,
            battery_source.CRITIC_STATE_DIM,
        ),
        "actions": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            battery_source.ACTION_DIM,
        ),
        "pre_tanh_actions": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            battery_source.ACTION_DIM,
        ),
        "old_log_probs": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
        ),
        "rewards": (battery_source.HORIZON, batch),
        "hidden_before": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            model.hidden_dim,
        ),
        "hidden_after": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            model.hidden_dim,
        ),
        "prefix_action_sums": (
            battery_source.HORIZON,
            batch,
            battery_source.CAPACITY,
            battery_source.ACTION_DIM,
        ),
    }
    rows: dict[str, torch.Tensor] = {}
    for name, shape in shapes.items():
        dtype = torch.bool if name == "active_mask" else torch.float32
        rows[name] = torch.empty(shape, dtype=dtype)

    model.eval()
    with torch.no_grad():
        for time_index in range(battery_source.HORIZON):
            views = tuple(environment.observe() for environment in environments)
            observations = torch.as_tensor(
                np.stack([view.observations for view in views]), device=device
            )
            active_mask = torch.as_tensor(
                np.stack([view.active_mask for view in views]), device=device
            )
            critic_states = torch.as_tensor(
                np.stack([view.critic_state for view in views]), device=device
            )
            hidden_before = hidden.clone()
            arguments = {
                "observations": observations,
                "active_mask": active_mask,
                "critic_state": critic_states,
                "hidden": hidden,
            }
            if deterministic:
                output = model.forward_step(**arguments, deterministic=True)
            else:
                output = model.forward_step(
                    **arguments,
                    sampling_noise=torch.as_tensor(noise[time_index], device=device),
                )
            action_values = output.actions.detach().cpu().numpy()
            rewards = np.empty(batch, dtype=np.float32)
            for index, environment in enumerate(environments):
                reward, _terminal, _info = environment.step(action_values[index])
                rewards[index] = reward
            values = {
                "observations": observations,
                "active_mask": active_mask,
                "critic_states": critic_states,
                "actions": output.actions,
                "pre_tanh_actions": output.pre_tanh_actions,
                "old_log_probs": output.token_log_probs,
                "rewards": torch.as_tensor(rewards, device=device),
                "hidden_before": hidden_before,
                "hidden_after": output.next_hidden,
                "prefix_action_sums": output.prefix_action_sums,
            }
            for name, value in values.items():
                rows[name][time_index].copy_(value.detach().cpu())
            hidden = output.next_hidden

    provisional = SimpleNamespace(
        **rows,
        outcomes=tuple(environment.outcome() for environment in environments),
        ledgers=ledgers,
    )
    return attach_prefix_credit(
        model, provisional, device=device, baseline_seed=baseline_seed
    )


def _baseline_seed_for_call(source: str, episode_ids: tuple[int, ...]) -> int:
    """Derive a per-collection baseline seed from the fixed per-source stream.

    Mirrors G20R's own convention: mixing in the batch's starting episode id
    keeps the K=8 anchor-resample noise distinct per update while remaining
    fully deterministic, and never touches the action or ledger seeds.
    """

    return int(SEEDS[source]["baseline"]) + int(episode_ids[0])


def _collect(
    source: str,
    model: FastAnchorActionAdvantagePolicy,
    *,
    episode_ids: tuple[int, ...],
) -> AnchorActionTrajectory:
    seeds = SEEDS[source]
    baseline_seed = _baseline_seed_for_call(source, episode_ids)
    if source == "g17":
        raw = g17_source.collect_trajectory(
            model,
            episode_ids=episode_ids,
            ledger_seed=seeds["train_ledger"],
            action_seed=seeds["action"],
            device=torch.device("cpu"),
            profiles=g17_source.TRAIN_PROFILES,
        )
        return attach_prefix_credit(
            model, raw, device=torch.device("cpu"), baseline_seed=baseline_seed
        )
    return collect_battery_trajectory(
        model,
        episode_ids=episode_ids,
        action_seed=seeds["action"],
        baseline_seed=baseline_seed,
        device=torch.device("cpu"),
    )


def _trajectory_contract_valid(source: str, trajectory: AnchorActionTrajectory) -> bool:
    inactive_actions = torch.where(
        trajectory.active_mask.unsqueeze(-1),
        torch.zeros_like(trajectory.actions),
        trajectory.actions,
    )
    if int(torch.count_nonzero(inactive_actions)) != 0:
        return False
    if not all(
        bool(torch.isfinite(row).all())
        for row in (
            trajectory.observations,
            trajectory.critic_states,
            trajectory.actions,
            trajectory.pre_tanh_actions,
            trajectory.old_log_probs,
            trajectory.old_values,
            trajectory.old_immediate_baselines,
            trajectory.old_baseline,
            trajectory.old_prefix_advantage,
            trajectory.rewards,
        )
    ):
        return False
    for ledger, outcome in zip(trajectory.ledgers, trajectory.outcomes):
        if source == "g17":
            if outcome.roster_sizes != ledger.expected_roster_sizes:
                return False
        elif outcome.roster_sizes != (
            4, 4, 4, 4, 4, 4, 2, 2, 2, 2, 4, 4,
        ):
            return False
    return True


# ---------------------------------------------------------------------------
# Episode-id block allocation: D_fit and D_credit are disjoint, deterministic
# windows over the same per-source training stream (design section 5); this
# is the same mechanism G20R used to separate its fast and delayed phases,
# extended by one more disjoint block for the qualification phase.
# ---------------------------------------------------------------------------


def _qualification_episode_block(source: str, update: int) -> tuple[int, ...]:
    first = update * NUM_ENVS
    return tuple(range(first, first + NUM_ENVS))


def _credit_episode_block(source: str, qualification_updates: int, update: int) -> tuple[int, ...]:
    first = (qualification_updates + update) * NUM_ENVS
    return tuple(range(first, first + NUM_ENVS))


# ---------------------------------------------------------------------------
# D_audit: paired-replay oracle-advantage collection (design section 2-4).
#
# The environment can be reconstructed exactly by creating a fresh instance
# from the same ledger and replaying the identical action prefix (external
# ruling, section 3) -- no new method on either source module is required.
# Branching at one (time, routing-position) decision point is realized with
# a single noise substitution rather than a second sampling mode: the
# routing loop is a deterministic function of (content, prefix, noise), so
# holding every noise entry fixed except the intervened one reproduces the
# untouched prefix bit-for-bit and lets positions/timesteps after the
# intervention regenerate under common random numbers.
# ---------------------------------------------------------------------------


def paired_replay_return(
    model: FastAnchorActionAdvantagePolicy,
    env_factory: Callable[[], Any],
    *,
    horizon: int,
    capacity: int,
    hidden_dim: int,
    gamma: float,
    intervention_time: int,
    intervention_position: int,
    probe_action: torch.Tensor,
    noise: torch.Tensor,
) -> tuple[float, torch.Tensor, torch.Tensor, torch.Tensor, int]:
    """Roll out one episode, forcing ``probe_action`` at exactly one decision point.

    ``noise`` (``[horizon, capacity, action_dim]``) is used unmodified except
    at ``[intervention_time, member]`` (the routed member occupying
    ``intervention_position`` at that step), which is overwritten so the
    resulting post-tanh action equals ``probe_action``. Because the routing
    loop is a deterministic function of (content, prefix, noise), every
    position strictly before the intervention reproduces bit-for-bit
    relative to any other call sharing the same ``noise`` up to that point,
    and every position/timestep after it uses common random numbers (the
    same ``noise`` entries) across different ``probe_action`` calls.

    Returns ``(discounted_return, raw_probe_action, mean_at_intervention,
    std, active_count_at_intervention)`` -- the latter three let the caller
    build the Stage B2 action-space score without a second environment
    reconstruction.
    """

    env = env_factory()
    hidden = torch.zeros(1, capacity, hidden_dim)
    rewards: list[float] = []
    working_noise = noise.clone()
    raw_probe = torch.zeros(probe_action.shape)
    mean_at_intervention = torch.zeros(probe_action.shape)
    std = torch.exp(model.log_std.clamp(-5.0, 2.0)).detach()
    active_count_at_intervention = 0
    for time_index in range(horizon):
        view = env.observe()
        observations = torch.as_tensor(np.asarray(view.observations)).unsqueeze(0)
        active_mask = torch.as_tensor(np.asarray(view.active_mask)).unsqueeze(0)
        critic_state = torch.as_tensor(np.asarray(view.critic_state)).unsqueeze(0)
        step_noise = working_noise[time_index : time_index + 1].clone()
        if time_index == intervention_time:
            order = model.policy._routing_order(active_mask, observations)
            member = int(order[0, intervention_position])
            active_count_at_intervention = int(active_mask[0].sum())
            with torch.no_grad():
                reference = model.forward_step(
                    observations=observations,
                    active_mask=active_mask,
                    critic_state=critic_state,
                    hidden=hidden,
                    sampling_noise=step_noise,
                )
            mean_at_intervention = (
                reference.pre_tanh_actions[0, member] - std * step_noise[0, member]
            ).detach()
            desired_raw = torch.atanh(torch.clamp(probe_action, -0.999999, 0.999999))
            raw_probe = desired_raw.detach()
            step_noise[0, member] = (desired_raw - mean_at_intervention) / std
        with torch.no_grad():
            output = model.forward_step(
                observations=observations,
                active_mask=active_mask,
                critic_state=critic_state,
                hidden=hidden,
                sampling_noise=step_noise,
            )
        action_values = output.actions[0].detach().cpu().numpy()
        reward, _terminal, _info = env.step(action_values)
        rewards.append(float(reward))
        hidden = output.next_hidden

    running = 0.0
    for time_index in range(horizon - 1, -1, -1):
        continuation = 0.0 if time_index == horizon - 1 else 1.0
        running = rewards[time_index] + float(gamma) * continuation * running
    return running, raw_probe, mean_at_intervention, std, active_count_at_intervention


def _audit_probe_points(source: str, generator: np.random.Generator) -> list[tuple[int, int]]:
    """Deterministically choose (time, routing-position) audit points.

    One is always t=0 for G18 (the pivotal decision point the source's own
    information gate audits, external ruling section 3); the rest are drawn
    uniformly at random from the source's (horizon, capacity) grid.
    """

    horizon = battery_source.HORIZON if source == "g18" else g17_source.HORIZON
    capacity = battery_source.CAPACITY if source == "g18" else g17_source.CAPACITY
    points: list[tuple[int, int]] = []
    if source == "g18":
        points.append((0, 0))
    while len(points) < AUDIT_PROBE_POINTS_PER_EPISODE:
        points.append(
            (int(generator.integers(0, horizon)), int(generator.integers(0, capacity)))
        )
    return points[:AUDIT_PROBE_POINTS_PER_EPISODE]


def collect_audit_clusters(
    source: str,
    model: FastAnchorActionAdvantagePolicy,
    *,
    episode_ids: Sequence[int],
) -> dict[str, list[torch.Tensor]]:
    """Build one Stage A/B1/B2 cluster per audited episode (design section 5).

    Every episode is one cluster. Within a cluster's audit points, ``K``
    anchor-resampled probe actions supply both Stage A's oracle-advantage
    sample and Stage B1's "action probes" (design section 3's
    ``g_hk``/``q_hk``); the environment interventions use the registered
    ``*_audit`` seed exclusively, never the training seeds, and never
    updates the critic or the actor -- this split's trajectories are read
    only by the functions in this section.
    """

    if source == "g17":
        env_factory_for = lambda ledger: g17_source.ContinuousServiceRosterEnv(ledger)
        horizon = g17_source.HORIZON
        capacity = g17_source.CAPACITY
        action_dim = g17_source.ACTION_DIM

        def make_ledger(episode_id: int):
            return g17_source.make_ledger(
                episode_id,
                master_seed=SEEDS["g17"]["audit"],
                profiles=g17_source.TRAIN_PROFILES,
            )

    elif source == "g18":
        env_factory_for = lambda ledger: battery_source.BatteryRosterEnv(ledger)
        horizon = battery_source.HORIZON
        capacity = battery_source.CAPACITY
        action_dim = battery_source.ACTION_DIM

        def make_ledger(episode_id: int):
            return battery_source.make_ledger(
                battery_source.GATE_SLOT_ORDERS[
                    episode_id % len(battery_source.GATE_SLOT_ORDERS)
                ]
            )

    else:
        raise ValueError(f"unknown G20R2 audit source: {source}")

    oracle_clusters: list[torch.Tensor] = []
    critic_clusters: list[torch.Tensor] = []
    score_clusters: list[torch.Tensor] = []
    std = torch.exp(model.log_std.clamp(-5.0, 2.0)).detach()

    for episode_id in episode_ids:
        ledger = make_ledger(int(episode_id))
        point_generator = np.random.default_rng(
            np.random.SeedSequence(
                [int(SEEDS[source]["audit"]), int(episode_id), 700]
            )
        )
        prefix_generator = np.random.default_rng(
            np.random.SeedSequence(
                [int(SEEDS[source]["audit"]), int(episode_id), 701]
            )
        )
        prefix_noise = torch.as_tensor(
            prefix_generator.standard_normal((horizon, capacity, action_dim)).astype(
                np.float32
            )
        )
        oracle_rows: list[float] = []
        critic_rows: list[float] = []
        score_rows: list[list[float]] = []

        for point_index, (intervention_time, intervention_position) in enumerate(
            _audit_probe_points(source, point_generator)
        ):
            # Determine the anchor mean at this decision point via one
            # reference rollout (factual probe = the anchor mean itself,
            # noise=0 offset), then draw K anchor-resampled probes.
            probe_generator = np.random.default_rng(
                np.random.SeedSequence(
                    [int(SEEDS[source]["audit"]), int(episode_id), 702, point_index]
                )
            )
            # First pass learns `mean_at_intervention`/`std` via the factual
            # (unperturbed) noise so probes can be drawn from N(mean, std).
            gamma_local = GAMMA
            _, _raw0, mean_at_intervention, _std, _active = paired_replay_return(
                model,
                lambda ledger=ledger: env_factory_for(ledger),
                horizon=horizon,
                capacity=capacity,
                hidden_dim=model.hidden_dim,
                gamma=gamma_local,
                intervention_time=intervention_time,
                intervention_position=intervention_position,
                probe_action=torch.tanh(torch.zeros(action_dim)),
                noise=prefix_noise,
            )
            probe_actions = []
            for _ in range(BASELINE_SAMPLES_K_CONFIGURED):
                eps = torch.as_tensor(
                    probe_generator.standard_normal(action_dim).astype(np.float32)
                )
                probe_actions.append(torch.tanh(mean_at_intervention + std * eps))

            returns_for_point: list[float] = []
            raw_for_point: list[torch.Tensor] = []
            for probe_action in probe_actions:
                replicate_returns = []
                for replicate in range(AUDIT_SUFFIX_REPLICATES):
                    suffix_generator = np.random.default_rng(
                        np.random.SeedSequence(
                            [
                                int(SEEDS[source]["audit"]),
                                int(episode_id),
                                703,
                                point_index,
                                replicate,
                            ]
                        )
                    )
                    suffix_noise = prefix_noise.clone()
                    suffix_noise[intervention_time:] = torch.as_tensor(
                        suffix_generator.standard_normal(
                            (horizon - intervention_time, capacity, action_dim)
                        ).astype(np.float32)
                    )
                    returned, raw_probe, _mean, _std2, _active2 = paired_replay_return(
                        model,
                        lambda ledger=ledger: env_factory_for(ledger),
                        horizon=horizon,
                        capacity=capacity,
                        hidden_dim=model.hidden_dim,
                        gamma=gamma_local,
                        intervention_time=intervention_time,
                        intervention_position=intervention_position,
                        probe_action=probe_action,
                        noise=suffix_noise,
                    )
                    replicate_returns.append(returned)
                returns_for_point.append(float(np.mean(replicate_returns)))
                raw_for_point.append(raw_probe)

            g_values = torch.as_tensor(returns_for_point, dtype=torch.float32)
            g_centered = g_values - g_values.mean()

            # Critic response q_hk at the same probes/history, via a single
            # cheap forward pass (no environment rollout needed): reuse the
            # factual prefix up to the intervention (from the first
            # reference rollout above) as `prefix_actions`, and evaluate the
            # K probe actions as `focal_actions`.
            with torch.no_grad():
                observations_ref, active_mask_ref, critic_state_ref, hidden_ref, order_ref, prefix_actions_ref = (
                    _replay_decision_history(
                        model,
                        lambda ledger=ledger: env_factory_for(ledger),
                        horizon=horizon,
                        capacity=capacity,
                        hidden_dim=model.hidden_dim,
                        intervention_time=intervention_time,
                        intervention_position=intervention_position,
                        noise=prefix_noise,
                    )
                )
                focal = torch.stack(probe_actions, dim=0)  # [K, action_dim]
                prefix_k = prefix_actions_ref.unsqueeze(0).expand(
                    BASELINE_SAMPLES_K_CONFIGURED, *prefix_actions_ref.shape
                ).clone()
                # Only the intervened position's own row is queried per probe
                # (`q_all_positions[..., intervention_position]` below);
                # `_qj_forward` reads prefix rows strictly before the
                # intervened position, which are already factual/unchanged,
                # so every other row of `focal_actions` is simply ignored.
                from ha_ctse_process.anchor_action_advantage_g20r2 import _qj_forward

                q_all_positions = _qj_forward(
                    model,
                    critic_state=critic_state_ref.unsqueeze(0).expand(
                        BASELINE_SAMPLES_K_CONFIGURED, *critic_state_ref.shape
                    ),
                    active_mask=active_mask_ref.unsqueeze(0).expand(
                        BASELINE_SAMPLES_K_CONFIGURED, *active_mask_ref.shape
                    ),
                    observations=observations_ref.unsqueeze(0).expand(
                        BASELINE_SAMPLES_K_CONFIGURED, *observations_ref.shape
                    ),
                    hidden_before=hidden_ref.unsqueeze(0).expand(
                        BASELINE_SAMPLES_K_CONFIGURED, *hidden_ref.shape
                    ),
                    order=order_ref.unsqueeze(0).expand(
                        BASELINE_SAMPLES_K_CONFIGURED, *order_ref.shape
                    ),
                    prefix_actions=prefix_k,
                    focal_actions=_scatter_focal(prefix_k, intervention_position, focal),
                )
                q_values = q_all_positions[:, intervention_position]
            q_centered = q_values - q_values.mean()

            for k in range(BASELINE_SAMPLES_K_CONFIGURED):
                oracle_rows.append(float(g_centered[k]))
                critic_rows.append(float(q_centered[k]))
                score = residual_action_space_score(
                    raw_for_point[k], mean_at_intervention, std
                )
                score_rows.append(score.detach().cpu().tolist())

        oracle_clusters.append(torch.as_tensor(oracle_rows).unsqueeze(-1))
        critic_clusters.append(torch.as_tensor(critic_rows).unsqueeze(-1))
        score_clusters.append(torch.as_tensor(score_rows, dtype=torch.float32))

    return {
        "oracle": oracle_clusters,
        "critic": critic_clusters,
        "score": score_clusters,
    }


def _scatter_focal(
    prefix_k: torch.Tensor, position: int, focal_values: torch.Tensor
) -> torch.Tensor:
    """Overwrite one routing position's row with the probe action, per sample.

    ``prefix_k``: ``[K, capacity, action_dim]`` (factual, position-indexed).
    Returns a copy with row ``position`` replaced by ``focal_values``
    (``[K, action_dim]``) -- ``_qj_forward`` reads ``focal_actions`` only at
    the query row itself (``a_j,t``) when computing that row's own ``Q_j``,
    so only that one row needs to carry the counterfactual value; every
    other row keeps its factual (and therefore irrelevant-to-this-query)
    value.
    """

    out = prefix_k.clone()
    out[:, position, :] = focal_values
    return out


def _replay_decision_history(
    model: FastAnchorActionAdvantagePolicy,
    env_factory: Callable[[], Any],
    *,
    horizon: int,
    capacity: int,
    hidden_dim: int,
    intervention_time: int,
    intervention_position: int,
    noise: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """Replay up to (and including) the intervention step's factual prefix.

    Returns the decision-history tensors ``Q_j`` needs at that step:
    ``(observations, active_mask, critic_state, hidden_before, order,
    factual_position_actions)``, each with the leading batch dimension
    squeezed to a single (episode) row.
    """

    env = env_factory()
    hidden = torch.zeros(1, capacity, model.hidden_dim)
    for time_index in range(intervention_time + 1):
        view = env.observe()
        observations = torch.as_tensor(np.asarray(view.observations)).unsqueeze(0)
        active_mask = torch.as_tensor(np.asarray(view.active_mask)).unsqueeze(0)
        critic_state = torch.as_tensor(np.asarray(view.critic_state)).unsqueeze(0)
        hidden_before = hidden.clone()
        step_noise = noise[time_index : time_index + 1]
        with torch.no_grad():
            output = model.forward_step(
                observations=observations,
                active_mask=active_mask,
                critic_state=critic_state,
                hidden=hidden,
                sampling_noise=step_noise,
            )
        if time_index == intervention_time:
            order = model.policy._routing_order(active_mask, observations)
            position_actions = torch.gather(
                output.actions,
                1,
                order.unsqueeze(-1).expand(-1, -1, output.actions.shape[-1]),
            )
            return (
                observations[0],
                active_mask[0],
                critic_state[0],
                hidden_before[0],
                order[0],
                position_actions[0],
            )
        action_values = output.actions[0].detach().cpu().numpy()
        env.step(action_values)
        hidden = output.next_hidden
    raise RuntimeError("G20R2 audit intervention time exceeds horizon")


# ---------------------------------------------------------------------------
# Identification-stage wiring (design sections 2-4).
# ---------------------------------------------------------------------------


def run_identification_stages(
    source: str, clusters: dict[str, list[torch.Tensor]], *, seed: int
) -> dict[str, Any]:
    generator = torch.Generator()
    generator.manual_seed(int(seed))

    stage_a = stage_a_source_effect(clusters["oracle"], generator=generator)
    p2 = stage_a_p2_authority_check(clusters["oracle"], clusters["score"])

    n = len(clusters["oracle"])
    half = n // 2
    if half < 2 or (n - half) < 2:
        raise ValueError(
            "G20R2 identification stages require at least 4 audit-episode "
            "clusters so the Stage B1 R^2 calibration/audit split has >=2 "
            "clusters on each side -- the audit split must never be filled "
            "in by reusing calibration data (design section 5: 'the untouched "
            "audit split')"
        )
    cal_oracle = torch.cat(clusters["oracle"][:half], dim=0).squeeze(-1)
    cal_critic = torch.cat(clusters["critic"][:half], dim=0).squeeze(-1)
    audit_oracle = clusters["oracle"][half:]
    audit_critic = clusters["critic"][half:]

    stage_b1_rho = stage_b1_contrast_alignment(
        [row.squeeze(-1) for row in audit_oracle],
        [row.squeeze(-1) for row in audit_critic],
        generator=generator,
    )
    audit_pairs = [
        torch.cat((g, q), dim=-1)
        for g, q in zip(audit_oracle, audit_critic)
    ]
    stage_b1_r2 = stage_b1_recalibrated_r2(
        cal_oracle, cal_critic, audit_pairs, generator=generator
    )
    stage_b2 = stage_b2_gradient_alignment(
        clusters["score"],
        [
            torch.as_tensor(row) if not isinstance(row, torch.Tensor) else row
            for row in clusters["critic"]
        ],
        clusters["oracle"],
        generator=generator,
    )
    return {
        "stage_a": stage_a,
        "stage_a_passed": bool(stage_a["passed"]),
        "p2_authority": p2,
        "p2_outside_authority": bool(p2["outside_authority"]),
        "stage_b1_contrast": stage_b1_rho,
        "stage_b1_r2": stage_b1_r2,
        "stage_b1_passed": bool(stage_b1_rho["passed"] and stage_b1_r2["passed"]),
        "stage_b2": stage_b2,
        "stage_b2_passed": bool(stage_b2["passed"]),
    }


# ---------------------------------------------------------------------------
# Result system -- design section 8: six sequential, source-specific,
# first-match branches. No global identification Boolean across sources:
# `select_g17_branch` and `select_g18_branch` each read only their own
# source's metrics dict, so nothing in one source's evidence can reach the
# other's branch computation.
# ---------------------------------------------------------------------------

INVALID_BRANCH_TEMPLATE = "INVALID_G20R2_EVIDENCE_CONTRACT_{suffix}"
STAGE_A_FAIL_TEMPLATE = "SOURCE_LOCAL_ACTION_EFFECT_NOT_IDENTIFIED_{suffix}"
P2_FAIL_TEMPLATE = "SOURCE_EFFECT_OUTSIDE_CENTERED_AUTHORITY_{suffix}"
STAGE_B1_FAIL_TEMPLATE = "NON_IDENTIFIED_ACTION_CRITIC_{suffix}"
STAGE_B2_FAIL_TEMPLATE = "NON_IDENTIFIED_ACTION_CREDIT_DIRECTION_{suffix}"

NO_G18_ACCESS_BRANCH = "NONFORMAL_NO_DELAYED_ACCESS_ANCHOR_ACTION_G20R2_G18"
NO_G18_MECHANISM_BRANCH = "NONFORMAL_NO_DELAYED_MECHANISM_ANCHOR_ACTION_G20R2_G18"
PROMISING_BRANCH_G18 = "NONFORMAL_ANCHOR_ACTION_ADVANTAGE_PROMISING_G20R2_G18"

G17_QUALIFIED_PASS_BRANCH = "NONFORMAL_G17_COMPATIBILITY_QUALIFIED_PASS_G20R2_G17"
G17_QUALIFIED_FAIL_BRANCH = "NONFORMAL_G17_COMPATIBILITY_QUALIFIED_FAIL_G20R2_G17"
G17_DIAGNOSTIC_PASS_BRANCH = (
    "NONFORMAL_G17_DIAGNOSTIC_COMPATIBILITY_PASS_UNQUALIFIED_G20R2_G17"
)
G17_UNQUALIFIED_LOSS_BRANCH = (
    "NONFORMAL_G17_UNQUALIFIED_CRITIC_COMPATIBILITY_LOSS_G20R2_G17"
)


def _identification_gate_failure(source: str, metrics: dict[str, Any]) -> str | None:
    """First-match failure among gates 1-5 (design section 8), or None if all pass."""

    suffix = source.upper()
    if not bool(metrics["operational_valid"]):
        return INVALID_BRANCH_TEMPLATE.format(suffix=suffix)
    if not bool(metrics["stage_a_passed"]):
        return STAGE_A_FAIL_TEMPLATE.format(suffix=suffix)
    if bool(metrics["p2_outside_authority"]):
        return P2_FAIL_TEMPLATE.format(suffix=suffix)
    if not bool(metrics["stage_b1_passed"]):
        return STAGE_B1_FAIL_TEMPLATE.format(suffix=suffix)
    if not bool(metrics["stage_b2_passed"]):
        return STAGE_B2_FAIL_TEMPLATE.format(suffix=suffix)
    return None


def _g18_behavior_branch(metrics: dict[str, Any]) -> str:
    if not (
        float(metrics["g18_final_utility"]) >= G18_UTILITY_FLOOR
        and float(metrics["g18_gain_over_anchor"]) >= G18_GAIN_FLOOR
        and float(metrics["g18_spike_utility"]) >= G18_SPIKE_UTILITY_FLOOR
    ):
        return NO_G18_ACCESS_BRANCH
    if float(metrics["g18_rotating_effort_share"]) < G18_ROTATING_EFFORT_SHARE_FLOOR:
        return NO_G18_MECHANISM_BRANCH
    return PROMISING_BRANCH_G18


def select_g18_branch(metrics: dict[str, Any]) -> str:
    """G18: identification/qualification are load-bearing before ANY
    delayed-credit conclusion (design section 8) -- stop at the first
    failing gate, never read behavior under an unqualified critic."""

    failure = _identification_gate_failure("g18", metrics)
    if failure is not None:
        return failure
    return _g18_behavior_branch(metrics)


def _g17_behavior_passed(metrics: dict[str, Any]) -> bool:
    return (
        float(metrics["g17_final_iid_utility"]) >= G17_UTILITY_FLOOR
        and float(metrics["g17_final_heldout_utility"]) >= G17_UTILITY_FLOOR
        and float(metrics["g17_gain"]) >= G17_GAIN_FLOOR
        and float(metrics["g17_minimum_episode"]) >= G17_MINIMUM_EPISODE_FLOOR
        and float(metrics["g17_effort_correlation"]) >= G17_CORRELATION_FLOOR
        and float(metrics["g17_mix_correlation"]) >= G17_CORRELATION_FLOOR
        and float(metrics["g17_effort_mae"]) <= G17_MAE_CEILING
        and float(metrics["g17_mix_mae"]) <= G17_MAE_CEILING
    )


def select_g17_branch(metrics: dict[str, Any]) -> str:
    """G17: an identification failure with a behavioral pass is diagnostic
    (design section 8) -- it still reads behavior, but returns a distinctly
    labeled diagnostic/unqualified branch, never a G18 branch code, and
    never masks a qualified G18 result (the two functions read disjoint
    metrics dicts and share no state)."""

    failure = _identification_gate_failure("g17", metrics)
    if failure is not None:
        return (
            G17_DIAGNOSTIC_PASS_BRANCH
            if _g17_behavior_passed(metrics)
            else G17_UNQUALIFIED_LOSS_BRANCH
        )
    return (
        G17_QUALIFIED_PASS_BRANCH
        if _g17_behavior_passed(metrics)
        else G17_QUALIFIED_FAIL_BRANCH
    )


def select_result_branch(source: str, metrics: dict[str, Any]) -> str:
    if source == "g17":
        return select_g17_branch(metrics)
    if source == "g18":
        return select_g18_branch(metrics)
    raise ValueError(f"unknown G20R2 source: {source}")


def _g17_evaluate(
    model: FastAnchorActionAdvantagePolicy, domain: str
) -> dict[str, Any]:
    profiles = (
        g17_source.TRAIN_PROFILES
        if domain == "iid"
        else g17_source.HELDOUT_PROFILES
    )
    outcomes = g17_source.evaluate_policy(
        model,
        episode_ids=range(G17_EVAL_EPISODES),
        ledger_seed=SEEDS["g17"]["evaluation_ledger"],
        action_seed=SEEDS["g17"]["evaluation_action"],
        device=torch.device("cpu"),
        profiles=profiles,
        deterministic=True,
    )
    utilities = [float(row.utility) for row in outcomes]
    return {
        "utility_mean": float(np.mean(utilities)),
        "minimum_episode": float(np.min(utilities)),
    }


def _evaluate_phase(
    source: str, model: FastAnchorActionAdvantagePolicy
) -> dict[str, Any]:
    if source == "g17":
        return {
            "iid": _g17_evaluate(model, "iid"),
            "heldout": _g17_evaluate(model, "heldout"),
        }
    rows = evaluate_battery_policy(model, device=torch.device("cpu"))
    return {"slot_rows": rows}


def _phase_updates(source: str) -> tuple[int, int, int]:
    if source == "g17":
        return G17_QUALIFICATION_UPDATES, G17_FAST_UPDATES, G17_DELAYED_UPDATES
    return G18_QUALIFICATION_UPDATES, G18_FAST_UPDATES, G18_DELAYED_UPDATES


def _train_source(source: str) -> dict[str, Any]:
    seeds = SEEDS[source]
    g17_runner.configure_runtime(seeds["model"])
    model = make_model(source)
    zero_evaluation = _evaluate_phase(source, model)
    fast_optimizer = torch.optim.Adam(
        model.fast_actor_parameters() + tuple(model.immediate_baseline.parameters()),
        lr=LEARNING_RATE,
    )
    qualification_updates, fast_updates, delayed_updates = _phase_updates(source)
    maximum_replay_errors: dict[str, float] = {}
    lifecycle_valid = True
    finite = True
    active_rows = 0

    # --- fast phase (unchanged, protected fast path) -----------------------
    for update in range(fast_updates):
        first_episode = update * NUM_ENVS
        trajectory = _collect(
            source, model, episode_ids=tuple(range(first_episode, first_episode + NUM_ENVS))
        )
        lifecycle_valid = lifecycle_valid and _trajectory_contract_valid(source, trajectory)
        metrics = optimize_fast_update(
            model, fast_optimizer, trajectory, device=torch.device("cpu"), ppo_passes=PPO_PASSES
        )
        finite = finite and bool(metrics["finite_update"])
        for name, value in metrics.items():
            if name.endswith("_error") or name.endswith("_max_abs"):
                maximum_replay_errors[name] = max(
                    maximum_replay_errors.get(name, 0.0), float(value)
                )
        active_rows += trajectory.active_token_count
    anchor_evaluation = _evaluate_phase(source, model)
    anchor_state = model.anchor_state()

    # --- qualification phase (design section 6: critic-only, D_fit) --------
    model.begin_qualification_phase()
    critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=LEARNING_RATE)
    qualification_episode_ids: list[int] = []
    for update in range(qualification_updates):
        episode_ids = tuple(
            fast_updates * NUM_ENVS + index
            for index in _qualification_episode_block(source, update)
        )
        qualification_episode_ids.extend(episode_ids)
        trajectory = _collect(source, model, episode_ids=episode_ids)
        lifecycle_valid = lifecycle_valid and _trajectory_contract_valid(source, trajectory)
        metrics = optimize_qualification_update(
            model, critic_optimizer, trajectory, device=torch.device("cpu"),
            ppo_passes=PPO_PASSES, gamma=GAMMA,
        )
        finite = finite and bool(metrics["finite_update"])
        if metrics["residual_output_layer_maximum_absolute_value"] != 0.0:
            raise RuntimeError(
                "G20R2 residual moved during the critic-only qualification phase"
            )
        active_rows += trajectory.active_token_count

    # --- identification audit (design sections 2-4, D_audit) ---------------
    audit_episode_ids = tuple(
        (fast_updates + qualification_updates) * NUM_ENVS + 10_000 + index
        for index in range(AUDIT_EPISODES)
    )
    validate_disjoint_roles(
        qualification_episode_ids, [], audit_episode_ids
    )
    audit_clusters = collect_audit_clusters(source, model, episode_ids=audit_episode_ids)
    identification = run_identification_stages(
        source, audit_clusters, seed=seeds["audit"]
    )
    stage_b_passed = bool(
        identification["stage_a_passed"]
        and not identification["p2_outside_authority"]
        and identification["stage_b1_passed"]
        and identification["stage_b2_passed"]
    )

    # --- delayed phase (design section 6: only reachable post-qualification) -
    model.begin_delayed_phase(stage_b_passed=stage_b_passed)
    residual_optimizer = torch.optim.Adam(model.residual_parameters(), lr=LEARNING_RATE)
    credit_critic_optimizer = torch.optim.Adam(model.critic_parameters(), lr=LEARNING_RATE)
    credit_episode_ids: list[int] = []
    for update in range(delayed_updates):
        episode_ids = tuple(
            (fast_updates + qualification_updates) * NUM_ENVS + 20_000 + index
            for index in _credit_episode_block(source, 0, update)
        )
        credit_episode_ids.extend(episode_ids)
        trajectory = _collect(source, model, episode_ids=episode_ids)
        lifecycle_valid = lifecycle_valid and _trajectory_contract_valid(source, trajectory)
        metrics = optimize_delayed_update(
            model, residual_optimizer, credit_critic_optimizer, trajectory,
            device=torch.device("cpu"), ppo_passes=PPO_PASSES, gamma=GAMMA,
        )
        finite = finite and bool(metrics["finite_update"])
        for name, value in metrics.items():
            if name.endswith("_error") or name.endswith("_max_abs"):
                maximum_replay_errors[name] = max(
                    maximum_replay_errors.get(name, 0.0), float(value)
                )
        active_rows += trajectory.active_token_count

    validate_disjoint_roles(qualification_episode_ids, credit_episode_ids, audit_episode_ids)

    final_evaluation = _evaluate_phase(source, model)
    mapping = None
    if source == "g17":
        mapping = g17_runner._mapping_diagnostic(
            model,
            episode_ids=tuple(range(G17_EVAL_EPISODES)),
            ledger_seed=seeds["evaluation_ledger"],
        )
    return {
        "source": source,
        "seeds": seeds,
        "qualification_updates": qualification_updates,
        "fast_updates": fast_updates,
        "delayed_updates": delayed_updates,
        "active_rows": int(active_rows),
        "finite_updates": bool(finite),
        "lifecycle_contract_valid": bool(lifecycle_valid),
        "maximum_replay_errors": maximum_replay_errors,
        "anchor_maximum_difference": maximum_state_difference(anchor_state, model.anchor_state()),
        "residual_output_layer_maximum_absolute_value": (
            model.residual_output_layer_maximum_absolute_value()
        ),
        "identification": identification,
        "stage_b_passed": stage_b_passed,
        "zero_evaluation": zero_evaluation,
        "anchor_evaluation": anchor_evaluation,
        "final_evaluation": final_evaluation,
        "mapping": mapping,
    }


def _battery_means(evaluation: dict[str, Any]) -> dict[str, float]:
    rows = evaluation["slot_rows"]
    return {
        "utility": float(np.mean([row["utility"] for row in rows])),
        "spike_utility": float(np.mean([row["spike_utility"] for row in rows])),
        "rotating_effort_share": float(
            np.mean([row["low_rotating_effort_share"] for row in rows])
        ),
        "minimum_step_utility": float(
            np.min([row["minimum_step_utility"] for row in rows])
        ),
    }


def _source_metrics(row: dict[str, Any]) -> dict[str, Any]:
    """Per-source metrics dict consumed by `select_g17_branch`/`select_g18_branch`."""

    operational_valid = bool(
        row["finite_updates"]
        and row["lifecycle_contract_valid"]
        and max(row["maximum_replay_errors"].values(), default=0.0) <= REPLAY_TOLERANCE
        and row["anchor_maximum_difference"] == 0.0
    )
    identification = row["identification"]
    metrics: dict[str, Any] = {
        "operational_valid": operational_valid,
        "stage_a_passed": bool(identification["stage_a_passed"]),
        "p2_outside_authority": bool(identification["p2_outside_authority"]),
        "stage_b1_passed": bool(identification["stage_b1_passed"]),
        "stage_b2_passed": bool(identification["stage_b2_passed"]),
    }
    if row["source"] == "g17":
        zero = row["zero_evaluation"]
        anchor = row["anchor_evaluation"]
        final = row["final_evaluation"]
        mapping = row["mapping"]
        assert isinstance(mapping, dict)
        metrics.update(
            {
                "g17_final_iid_utility": float(final["iid"]["utility_mean"]),
                "g17_final_heldout_utility": float(final["heldout"]["utility_mean"]),
                "g17_gain": float(
                    min(
                        final["iid"]["utility_mean"] - zero["iid"]["utility_mean"],
                        final["heldout"]["utility_mean"] - zero["heldout"]["utility_mean"],
                    )
                ),
                "g17_minimum_episode": float(
                    min(final["iid"]["minimum_episode"], final["heldout"]["minimum_episode"])
                ),
                "g17_effort_correlation": float(mapping["effort_correlation"]),
                "g17_mix_correlation": float(mapping["mix_correlation"]),
                "g17_effort_mae": float(mapping["effort_mae"]),
                "g17_mix_mae": float(mapping["mix_mae"]),
            }
        )
    else:
        anchor = _battery_means(row["anchor_evaluation"])
        final = _battery_means(row["final_evaluation"])
        metrics.update(
            {
                "g18_final_utility": final["utility"],
                "g18_gain_over_anchor": float(final["utility"] - anchor["utility"]),
                "g18_spike_utility": final["spike_utility"],
                "g18_rotating_effort_share": final["rotating_effort_share"],
                "g18_minimum_step_utility": final["minimum_step_utility"],
            }
        )
    return metrics


def run_screen(*, run_root: Path, source_commit: str) -> dict[str, Any]:
    if not source_commit or source_commit == "NONFORMAL_WORKTREE":
        raise ValueError("G20R2 screen requires an integrated source commit")
    run_root.mkdir(parents=True, exist_ok=False)
    g17_runner.configure_runtime(SEEDS["g17"]["model"])
    started = time.perf_counter()
    source_rows = [_train_source(source) for source in ("g17", "g18")]
    by_source = {row["source"]: row for row in source_rows}
    source_metrics = {
        source: _source_metrics(row) for source, row in by_source.items()
    }
    source_controls = {
        "g17": g17_runner._source_controls(),
        "g18": battery_source.run_information_gate(),
    }
    for source in ("g17", "g18"):
        source_metrics[source]["operational_valid"] = bool(
            source_metrics[source]["operational_valid"]
            and (
                source != "g17"
                or (
                    source_controls["g17"]["constructive_access_valid"]
                    and source_controls["g17"]["all_schedules_exact"]
                )
            )
            and (
                source != "g18"
                or source_controls["g18"]["branch"] == battery_source.PASS_BRANCH
            )
        )
    branches = {
        source: select_result_branch(source, source_metrics[source])
        for source in ("g17", "g18")
    }
    result = {
        "schema_version": SCHEMA_VERSION,
        "algorithm": ALGORITHM_ID,
        "stage": "screen",
        "status": "COMPLETE",
        "formal": False,
        "source_commit": source_commit,
        "runtime": _runtime_identity(),
        "configuration": _configuration(),
        "source_controls": source_controls,
        "source_results": source_rows,
        "metrics": source_metrics,
        "branches": branches,
        "wall_seconds": float(time.perf_counter() - started),
    }
    _write_json(run_root / "result.json", result)
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    return parser.parse_args()


def main() -> None:
    arguments = _parse_args()
    result = run_screen(run_root=arguments.run_root, source_commit=arguments.source_commit)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
