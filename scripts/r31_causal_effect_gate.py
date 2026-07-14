"""Run the reward-off R31 natural-window causal effect-information gate."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch  # noqa: E402

from ha_ctse_process.config_alice_bob_asymmetric import Config  # noqa: E402
from ha_ctse_process.process_posterior import FixedWindowEffectPosterior  # noqa: E402
from ha_ctse_process.r31_effect_information import (  # noqa: E402
    build_effect_and_context,
    causal_between_within_metrics,
    matched_context_shuffle,
)
from ha_ctse_process import train as train_mod  # noqa: E402


NATURAL_RESET_GROUPS = 64
TRAIN_RESET_GROUPS = 48
HELDOUT_RESET_GROUPS = 16
EPISODE_STEPS = 80
WINDOW = 10
N_SKILLS = 4
CAUSAL_CONTEXTS = 128
CAUSAL_REPLICAS = 2
POSTERIOR_EPOCHS = 200
POSTERIOR_BATCH_SIZE = 128
POSTERIOR_LR = 1e-3
SCHEMA_VERSION = 1

THRESHOLDS = {
    "natural_effect_information_mean_nats": 0.02,
    "natural_effect_information_ci_lower": 0.0,
    "per_skill_effect_information_mean_nats": 0.005,
    "per_skill_heldout_windows": 64,
    "causal_ratio_median": 1.5,
    "causal_ratio_ci_lower": 1.0,
    "per_skill_pooled_causal_ratio": 1.0,
    "shuffle_absolute_max": 0.005,
    "shuffle_fraction_of_natural": 0.25,
    "hard_fail_shuffle_fraction_of_natural": 0.50,
}


@dataclass(frozen=True)
class NaturalSample:
    reset_group: int
    focal_agent: int
    skill: int
    effect: np.ndarray
    context: np.ndarray
    start_positions: np.ndarray
    active_skills: np.ndarray


@dataclass(frozen=True)
class DecisionContext:
    context_id: int
    reset_group: int
    focal_agent: int
    observations: np.ndarray
    state: np.ndarray
    env_snapshot: dict[str, object]
    policy_runtime: dict[str, np.ndarray]


def _set_seed(seed: int, device: torch.device) -> None:
    np.random.seed(int(seed) % (2**32 - 1))
    torch.manual_seed(int(seed))
    if device.type == "cuda":
        torch.cuda.manual_seed_all(int(seed))


def _set_eval_mode(agent) -> None:
    seen: set[int] = set()
    for value in vars(agent).values():
        if id(value) in seen:
            continue
        seen.add(id(value))
        eval_fn = getattr(value, "eval", None)
        if callable(eval_fn):
            eval_fn()


_RUNTIME_ARRAY_FIELDS = (
    "active_skills",
    "active_duration_indices",
    "duration_remaining",
    "skill_age",
    "has_active_skill",
    "active_team_codes",
    "episode_steps",
    "episode_ids",
    "steps_to_check",
    "low_actor_hxs",
    "low_critic_hxs",
)


def _capture_policy_runtime(agent) -> dict[str, np.ndarray]:
    return {
        name: np.asarray(getattr(agent, name)).copy()
        for name in _RUNTIME_ARRAY_FIELDS
    }


def _restore_policy_runtime(agent, snapshot: dict[str, np.ndarray]) -> None:
    for name in _RUNTIME_ARRAY_FIELDS:
        target = getattr(agent, name)
        target[...] = snapshot[name]
    agent._last_low_context[0] = None


def _checkpoint_manifest(path: Path) -> dict[str, Any]:
    loader = getattr(train_mod, "_load_adjacent_run_manifest", None)
    if not callable(loader):
        return {}
    return loader(path)


def _fail_closed_config(config, metadata: dict[str, Any], manifest: dict[str, Any]) -> None:
    if str(metadata.get("high_controller")) != "r30_fixed_clock_ar_edit":
        raise ValueError("R31 gate requires a frozen R30 fixed-clock checkpoint")
    if str(metadata.get("scenario")) != "alice_bob_asymmetric_cycles":
        raise ValueError("R31 gate requires an Alice-Bob checkpoint")
    if int(metadata.get("n_agents") or 0) != 2 or int(metadata.get("n_skills") or 0) != N_SKILLS:
        raise ValueError("R31 gate requires the two-agent, four-skill Alice-Bob policy")
    r30_contract = metadata.get("r30_contract") or {}
    if int(r30_contract.get("k0") or metadata.get("skill_interval") or 0) != WINDOW:
        raise ValueError("R31 effect window must equal the source R30 k0=10")
    algorithm = manifest.get("algorithm_config") if isinstance(manifest, dict) else {}
    if not isinstance(algorithm, dict) or "r30_force_refresh_every_check" not in algorithm:
        raise ValueError("R31 cannot verify that the source is adaptive R30")
    if bool(algorithm["r30_force_refresh_every_check"]):
        raise ValueError("R31 gate requires adaptive R30, not the shared-k comparator")
    if bool(getattr(config, "alice_bob_semantic_reward_enabled", False)):
        raise ValueError("legacy Alice-Bob semantic reward must be disabled")
    if float(getattr(config, "transition_skill_reward_coef", 0.0)) != 0.0:
        raise ValueError("transition-skill online reward must be disabled")
    if str(getattr(config, "r28_g1_arm", "off")) != "off":
        raise ValueError("R28 online reward must be disabled")
    if str(getattr(config, "r29_action_info_mode", "off")) != "off":
        raise ValueError("R29 online reward must be disabled")
    for name in (
        "process_reward_injection",
        "outcome_residual_injection",
        "topology_role_injection",
        "topology_potential_injection",
        "skill_effect_reward_injection",
        "skill_force_reward_injection",
    ):
        if str(getattr(config, name, "none")).lower() != "none":
            raise ValueError(f"R31 reward-off gate forbids {name}")
    if int(getattr(config, "r31_effect_window", 0)) != int(getattr(config, "skill_interval", 0)):
        raise ValueError("r31_effect_window must equal skill_interval")
    if float(getattr(config, "alice_bob_progress_reward_coef", 0.0)) != 0.0:
        raise ValueError("Alice-Bob environment shaping must remain disabled")


def _make_agent_and_env(args: argparse.Namespace):
    checkpoint = Path(args.checkpoint).resolve()
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("--device cuda requested but CUDA is unavailable")
    device = torch.device(args.device)
    config = Config()
    config.scenario = "alice_bob_asymmetric_cycles"
    config.skill_interval = WINDOW
    config.r31_effect_mode = "probe_only"
    config.r31_effect_view_name = "alice_bob_normalized_joint_positions_v1"
    config.r31_effect_gate_status = "UNTESTED"
    metadata = train_mod.load_checkpoint_metadata(checkpoint)
    structure_args = argparse.Namespace(high_controller="", n_agents=0)
    train_mod.apply_checkpoint_structure(config, structure_args, metadata)
    manifest = _checkpoint_manifest(checkpoint)
    _fail_closed_config(config, metadata, manifest)

    env = train_mod.create_env(
        config,
        scenario=config.scenario,
        seed=int(args.seed),
        rank=0,
        scale_mode="eval",
    )
    _set_seed(int(args.seed) + 500_000, device)
    agent_args = argparse.Namespace(device=str(args.device))
    agent = train_mod.create_agent(
        config,
        agent_args,
        env,
        num_envs=1,
        state_dim=int(env.state_dim),
    )
    total_steps, update_idx = train_mod.load_checkpoint(
        checkpoint,
        agent,
        load_optimizers=False,
    )
    _set_eval_mode(agent)
    return checkpoint, config, env, agent, metadata, total_steps, update_idx, device


def _collect_natural_windows(
    *,
    env,
    agent,
    source_update: int,
    base_seed: int,
    device: torch.device,
) -> tuple[list[NaturalSample], list[DecisionContext]]:
    raw_env = env.env
    samples: list[NaturalSample] = []
    decision_contexts: list[DecisionContext] = []
    heldout_context_index = 0

    for reset_group in range(NATURAL_RESET_GROUPS):
        reset_seed = int(base_seed) + reset_group
        _set_seed(reset_seed, device)
        observations, info = env.reset(seed=reset_seed)
        state = np.asarray(info["state"], dtype=np.float32)
        agent.reset_env_state(0)

        for block in range(EPISODE_STEPS // WINDOW):
            agent.maybe_assign_skills(
                observations,
                state=state,
                step=block * WINDOW,
                k=WINDOW,
                env_id=0,
                deterministic=False,
                policy_update=int(source_update),
                collect_r31=False,
            )
            high_row = agent.high_check_buffer.pending[0]
            if high_row is None or not bool(high_row.decision_mask):
                raise RuntimeError("natural R31 window did not start at a real R30 check")
            active_skills = agent.active_skills[0].astype(np.int64, copy=True)
            if np.any(active_skills < 0):
                raise RuntimeError("R30 did not assign every Alice-Bob skill")
            effect_views = [raw_env.intrinsic_effect_view()]

            if reset_group >= TRAIN_RESET_GROUPS:
                focal_agent = heldout_context_index % int(agent.n_agents)
                decision_contexts.append(
                    DecisionContext(
                        context_id=heldout_context_index,
                        reset_group=reset_group,
                        focal_agent=focal_agent,
                        observations=np.asarray(observations, dtype=np.float32).copy(),
                        state=state.copy(),
                        env_snapshot=copy.deepcopy(raw_env.get_probe_snapshot()),
                        policy_runtime=_capture_policy_runtime(agent),
                    )
                )
                heldout_context_index += 1

            done = False
            for primitive in range(WINDOW):
                actions, _logp, _values = agent.act_low(
                    observations,
                    env_id=0,
                    deterministic=False,
                    state=state,
                )
                observations, reward, terminated, truncated, next_info = env.step(actions)
                state = np.asarray(next_info["next_state"], dtype=np.float32)
                done = bool(terminated or truncated)
                effect_views.append(raw_env.intrinsic_effect_view())
                agent.record_environment_step(
                    0,
                    reward=float(reward),
                    next_obs=observations,
                    next_state=state,
                    done=done,
                    collect_r31=False,
                )
                if done and not (
                    block == EPISODE_STEPS // WINDOW - 1
                    and primitive == WINDOW - 1
                ):
                    raise RuntimeError("Alice-Bob ended before a complete R31 window")

            sequence = np.asarray(effect_views, dtype=np.float32)
            for focal_agent in range(int(agent.n_agents)):
                effect, context = build_effect_and_context(
                    sequence,
                    active_skills,
                    focal_agent,
                    int(agent.n_skills),
                )
                samples.append(
                    NaturalSample(
                        reset_group=reset_group,
                        focal_agent=focal_agent,
                        skill=int(active_skills[focal_agent]),
                        effect=effect,
                        context=context,
                        start_positions=sequence[0].copy(),
                        active_skills=active_skills.copy(),
                    )
                )
        if not done:
            raise RuntimeError("Alice-Bob natural rollout did not reach exactly 80 steps")
        agent.segments.flush(env_id=0, reason="episode")
        agent.segments.pop_completed()
        agent.high_check_buffer.pop_completed()

    expected_samples = NATURAL_RESET_GROUPS * (EPISODE_STEPS // WINDOW) * int(agent.n_agents)
    if len(samples) != expected_samples or len(decision_contexts) != CAUSAL_CONTEXTS:
        raise RuntimeError(
            f"R31 collection count mismatch: samples={len(samples)}, "
            f"contexts={len(decision_contexts)}"
        )
    return samples, decision_contexts


def _arrays(samples: list[NaturalSample]) -> dict[str, np.ndarray]:
    return {
        "effects": np.stack([row.effect for row in samples]).astype(np.float32),
        "contexts": np.stack([row.context for row in samples]).astype(np.float32),
        "labels": np.asarray([row.skill for row in samples], dtype=np.int64),
        "groups": np.asarray([row.reset_group for row in samples], dtype=np.int64),
        "starts": np.stack([row.start_positions for row in samples]).astype(np.float32),
        "skills": np.stack([row.active_skills for row in samples]).astype(np.int64),
        "focals": np.asarray([row.focal_agent for row in samples], dtype=np.int64),
    }


def _train_posterior(
    train_rows: dict[str, np.ndarray],
    *,
    model: FixedWindowEffectPosterior,
    device: torch.device,
    seed: int,
) -> tuple[FixedWindowEffectPosterior, torch.optim.Optimizer, dict[str, float]]:
    if int(model.effect_dim) != int(train_rows["effects"].shape[1]):
        raise ValueError("R31 posterior effect dimension does not match gate data")
    if int(model.context_dim) != int(train_rows["contexts"].shape[1]):
        raise ValueError("R31 posterior context dimension does not match gate data")
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=POSTERIOR_LR)
    generator = np.random.default_rng(int(seed))
    _set_seed(int(seed), device)
    effect = torch.as_tensor(train_rows["effects"], dtype=torch.float32, device=device)
    context = torch.as_tensor(train_rows["contexts"], dtype=torch.float32, device=device)
    labels = torch.as_tensor(train_rows["labels"], dtype=torch.long, device=device)
    final = {"loss": 0.0, "full_loss": 0.0, "context_loss": 0.0}
    model.train()
    for _epoch in range(POSTERIOR_EPOCHS):
        order = generator.permutation(effect.shape[0])
        totals = {name: 0.0 for name in final}
        seen = 0
        for start in range(0, effect.shape[0], POSTERIOR_BATCH_SIZE):
            index = torch.as_tensor(
                order[start : start + POSTERIOR_BATCH_SIZE],
                dtype=torch.long,
                device=device,
            )
            full_logits, context_logits = model(effect[index], context[index])
            losses = model.losses(full_logits, context_logits, labels[index])
            optimizer.zero_grad(set_to_none=True)
            losses["loss"].backward()
            optimizer.step()
            count = int(index.numel())
            seen += count
            for name in totals:
                totals[name] += float(losses[name].detach().cpu().item()) * count
        final = {name: value / float(max(seen, 1)) for name, value in totals.items()}
    model.eval()
    return model, optimizer, final


def _score(
    model: FixedWindowEffectPosterior,
    effects: np.ndarray,
    contexts: np.ndarray,
    labels: np.ndarray,
    device: torch.device,
) -> np.ndarray:
    with torch.no_grad():
        effect_t = torch.as_tensor(effects, dtype=torch.float32, device=device)
        context_t = torch.as_tensor(contexts, dtype=torch.float32, device=device)
        labels_t = torch.as_tensor(labels, dtype=torch.long, device=device)
        full_logits, context_logits = model(effect_t, context_t)
        full_logp = model.log_prob_for_labels(full_logits, labels_t)
        context_logp = model.log_prob_for_labels(context_logits, labels_t)
    return (full_logp - context_logp).detach().cpu().numpy().astype(np.float64)


def _cluster_bootstrap_ci(
    values: np.ndarray,
    cluster_ids: np.ndarray,
    *,
    repetitions: int,
    rng: np.random.Generator,
    statistic: Callable[[np.ndarray], float],
) -> tuple[float, float]:
    values = np.asarray(values, dtype=np.float64)
    cluster_ids = np.asarray(cluster_ids, dtype=np.int64).reshape(-1)
    if values.shape[0] != cluster_ids.shape[0]:
        raise ValueError("bootstrap values and cluster ids disagree")
    clusters = np.unique(cluster_ids)
    draws = np.empty(int(repetitions), dtype=np.float64)
    row_indices = {cluster: np.flatnonzero(cluster_ids == cluster) for cluster in clusters}
    for draw in range(int(repetitions)):
        sampled = rng.choice(clusters, size=clusters.size, replace=True)
        index = np.concatenate([row_indices[int(cluster)] for cluster in sampled])
        draws[draw] = float(statistic(values[index].reshape(-1)))
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def _run_forced_branch(
    *,
    env,
    agent,
    decision: DecisionContext,
    focal_skill: int,
    replica_seed: int,
    device: torch.device,
) -> tuple[np.ndarray, np.ndarray]:
    raw_env = env.env
    raw_env.set_probe_snapshot(copy.deepcopy(decision.env_snapshot))
    raw_env.np_random = np.random.default_rng(int(replica_seed))
    _restore_policy_runtime(agent, decision.policy_runtime)
    agent.active_skills[0, decision.focal_agent] = int(focal_skill)
    _set_seed(int(replica_seed), device)
    observations = decision.observations.copy()
    state = decision.state.copy()
    active_skills = agent.active_skills[0].astype(np.int64, copy=True)
    effect_views = [raw_env.intrinsic_effect_view()]
    for primitive in range(WINDOW):
        actions, _logp, _values = agent.act_low(
            observations,
            env_id=0,
            deterministic=False,
            state=state,
        )
        observations, _reward, terminated, truncated, info = env.step(actions)
        state = np.asarray(info["next_state"], dtype=np.float32)
        effect_views.append(raw_env.intrinsic_effect_view())
        if (terminated or truncated) and primitive != WINDOW - 1:
            raise RuntimeError("forced R31 branch ended before W=10")
    return build_effect_and_context(
        np.asarray(effect_views, dtype=np.float32),
        active_skills,
        decision.focal_agent,
        int(agent.n_skills),
    )


def _causal_probe(
    *,
    env,
    agent,
    decisions: list[DecisionContext],
    posterior: FixedWindowEffectPosterior,
    base_seed: int,
    device: torch.device,
) -> dict[str, Any]:
    between_rows: list[np.ndarray] = []
    within_rows: list[np.ndarray] = []
    ratio_rows: list[np.ndarray] = []
    forced_effect_rows: list[np.ndarray] = []
    forced_context_rows: list[np.ndarray] = []
    forced_label_rows: list[int] = []
    pairs: np.ndarray | None = None

    for decision in decisions:
        effects = np.zeros((N_SKILLS, CAUSAL_REPLICAS, 8), dtype=np.float32)
        reference_context: np.ndarray | None = None
        for replica in range(CAUSAL_REPLICAS):
            replica_seed = int(base_seed) + 1_000_000 + decision.context_id * 100 + replica
            for skill in range(N_SKILLS):
                effect, context = _run_forced_branch(
                    env=env,
                    agent=agent,
                    decision=decision,
                    focal_skill=skill,
                    replica_seed=replica_seed,
                    device=device,
                )
                effects[skill, replica] = effect
                if reference_context is None:
                    reference_context = context
                elif not np.array_equal(reference_context, context):
                    raise RuntimeError("focal skill leaked into the R31 context vector")
                forced_effect_rows.append(effect)
                forced_context_rows.append(context)
                forced_label_rows.append(skill)
        metrics = causal_between_within_metrics(effects)
        if pairs is None:
            pairs = metrics["skill_pairs"]
        between_rows.append(metrics["between"])
        within_rows.append(metrics["within"])
        ratio_rows.append(metrics["ratio"])

    between = np.stack(between_rows).astype(np.float64)
    within = np.stack(within_rows).astype(np.float64)
    ratio = np.stack(ratio_rows).astype(np.float64)
    forced_residual = _score(
        posterior,
        np.stack(forced_effect_rows),
        np.stack(forced_context_rows),
        np.asarray(forced_label_rows, dtype=np.int64),
        device,
    )
    forced_labels = np.asarray(forced_label_rows, dtype=np.int64)
    pooled_by_skill: dict[str, float] = {}
    for skill in range(N_SKILLS):
        involved = np.any(pairs == skill, axis=1)
        pooled_between = float(np.mean(between[:, involved]))
        pooled_within = float(np.mean(within[:, involved]))
        pooled_by_skill[str(skill)] = pooled_between / (pooled_within + 1e-8)
    forced_residual_by_skill = {
        str(skill): float(np.mean(forced_residual[forced_labels == skill]))
        for skill in range(N_SKILLS)
    }
    return {
        "skill_pairs": pairs,
        "between": between,
        "within": within,
        "ratio": ratio,
        "pooled_ratio_by_skill": pooled_by_skill,
        "forced_posterior_residual_mean": float(np.mean(forced_residual)),
        "forced_posterior_residual_by_skill": forced_residual_by_skill,
    }


def _decide(
    *,
    natural_mean: float,
    natural_ci: tuple[float, float],
    per_skill: dict[str, dict[str, float | int | None]],
    shuffle_mean: float | None,
    causal_median: float,
    causal_ci: tuple[float, float],
    pooled_ratio_by_skill: dict[str, float],
) -> tuple[str, list[str], str]:
    reasons: list[str] = []
    enough_skill_rows = all(
        int(row["count"]) >= int(THRESHOLDS["per_skill_heldout_windows"])
        for row in per_skill.values()
    )
    shuffle_available = shuffle_mean is not None
    hard_shuffle = (
        shuffle_available
        and natural_mean > 0.0
        and abs(float(shuffle_mean))
        > THRESHOLDS["hard_fail_shuffle_fraction_of_natural"] * natural_mean
    )
    if natural_mean <= 0.0:
        reasons.append("natural_effect_information_nonpositive")
    if causal_median <= 1.0:
        reasons.append("causal_ratio_not_above_execution_noise")
    if hard_shuffle:
        reasons.append("matched_shuffle_exceeds_half_natural_signal")
    if reasons:
        return "FAIL", reasons, "retire R31-CFEI; do not enable online reward"

    power_reasons: list[str] = []
    if natural_mean < THRESHOLDS["natural_effect_information_mean_nats"]:
        power_reasons.append("natural_mean_below_0.02")
    if causal_median < THRESHOLDS["causal_ratio_median"]:
        power_reasons.append("causal_median_below_1.5")
    if not shuffle_available:
        power_reasons.append("matched_shuffle_unavailable")
    else:
        shuffle_limit = min(
            THRESHOLDS["shuffle_absolute_max"],
            THRESHOLDS["shuffle_fraction_of_natural"] * natural_mean,
        )
        if abs(float(shuffle_mean)) > shuffle_limit:
            power_reasons.append("matched_shuffle_above_gate")
    if any(
        value < THRESHOLDS["per_skill_pooled_causal_ratio"]
        for value in pooled_ratio_by_skill.values()
    ):
        power_reasons.append("per_skill_causal_ratio_below_1")
    if any(
        row["mean_nats"] is None
        or float(row["mean_nats"])
        < THRESHOLDS["per_skill_effect_information_mean_nats"]
        for row in per_skill.values()
    ):
        power_reasons.append(
            "per_skill_natural_effect_information_below_0.005"
        )
    if not enough_skill_rows:
        power_reasons.append("per_skill_heldout_windows_below_64")
    if natural_ci[0] <= THRESHOLDS["natural_effect_information_ci_lower"]:
        power_reasons.append("natural_effect_information_ci_crosses_zero")
    if causal_ci[0] <= THRESHOLDS["causal_ratio_ci_lower"]:
        power_reasons.append("causal_ratio_ci_crosses_one")
    if power_reasons:
        return (
            "UNDERPOWERED",
            power_reasons,
            "append one identical 64-reset reward-off batch; do not change target or thresholds",
        )
    return (
        "PASS",
        ["M1_and_M2_pass"],
        "authorize only the matched R30 probe_only versus real_reward pair",
    )


def _write_gate_passed_checkpoint(
    *,
    source: Path,
    destination: Path,
    posterior: FixedWindowEffectPosterior,
    optimizer: torch.optim.Optimizer,
    config,
) -> None:
    """Copy the frozen source payload and add only the passed R31 state."""

    if source.resolve() == destination.resolve():
        raise ValueError("gate-passed checkpoint must not overwrite its frozen source")
    payload = torch.load(source, map_location="cpu")
    payload["effect_posterior"] = {
        name: value.detach().cpu()
        for name, value in posterior.full_head.state_dict().items()
    }
    payload["effect_context_posterior"] = {
        name: value.detach().cpu()
        for name, value in posterior.context_head.state_dict().items()
    }
    payload["effect_optimizer"] = optimizer.state_dict()
    payload["r31_effect_mode"] = "probe_only"
    payload["r31_effect_schema_version"] = int(config.r31_effect_schema_version)
    payload["effect_gate_status"] = "PASS"
    payload["effect_view_name"] = str(config.r31_effect_view_name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, destination)


def run(args: argparse.Namespace) -> dict[str, Any]:
    (
        checkpoint,
        config,
        env,
        agent,
        metadata,
        source_total_steps,
        source_update,
        device,
    ) = _make_agent_and_env(args)
    try:
        natural_samples, decisions = _collect_natural_windows(
            env=env,
            agent=agent,
            source_update=source_update,
            base_seed=int(args.seed),
            device=device,
        )
        train_samples = [row for row in natural_samples if row.reset_group < TRAIN_RESET_GROUPS]
        heldout_samples = [row for row in natural_samples if row.reset_group >= TRAIN_RESET_GROUPS]
        train_rows = _arrays(train_samples)
        heldout_rows = _arrays(heldout_samples)
        if agent.r31_effect_posterior is None:
            raise RuntimeError("R31 posterior was not initialized")
        posterior, posterior_optimizer, final_losses = _train_posterior(
            train_rows,
            model=agent.r31_effect_posterior,
            device=device,
            seed=int(args.seed) + 500_000,
        )
        natural_delta = _score(
            posterior,
            heldout_rows["effects"],
            heldout_rows["contexts"],
            heldout_rows["labels"],
            device,
        )
        bootstrap_rng = np.random.default_rng(int(args.seed) + 700_000)
        natural_ci = _cluster_bootstrap_ci(
            natural_delta,
            heldout_rows["groups"],
            repetitions=int(args.bootstrap_repetitions),
            rng=bootstrap_rng,
            statistic=np.mean,
        )
        natural_mean = float(np.mean(natural_delta))
        per_skill: dict[str, dict[str, float | int | None]] = {}
        for skill in range(int(agent.n_skills)):
            mask = heldout_rows["labels"] == skill
            per_skill[str(skill)] = {
                "count": int(np.sum(mask)),
                "mean_nats": float(np.mean(natural_delta[mask])) if np.any(mask) else None,
            }

        shuffled_effects, donor_indices, shuffle_valid = matched_context_shuffle(
            heldout_rows["effects"],
            heldout_rows["starts"],
            heldout_rows["skills"],
            heldout_rows["focals"],
            position_bins=5,
            rng=int(args.seed) + 800_000,
        )
        shuffle_mean: float | None = None
        if np.any(shuffle_valid):
            shuffled_delta = _score(
                posterior,
                shuffled_effects[shuffle_valid],
                heldout_rows["contexts"][shuffle_valid],
                heldout_rows["labels"][shuffle_valid],
                device,
            )
            shuffle_mean = float(np.mean(shuffled_delta))

        causal = _causal_probe(
            env=env,
            agent=agent,
            decisions=decisions,
            posterior=posterior,
            base_seed=int(args.seed),
            device=device,
        )
        context_ids = np.arange(len(decisions), dtype=np.int64)
        causal_ci = _cluster_bootstrap_ci(
            causal["ratio"],
            context_ids,
            repetitions=int(args.bootstrap_repetitions),
            rng=bootstrap_rng,
            statistic=np.median,
        )
        causal_median = float(np.median(causal["ratio"]))
        status, reasons, next_action = _decide(
            natural_mean=natural_mean,
            natural_ci=natural_ci,
            per_skill=per_skill,
            shuffle_mean=shuffle_mean,
            causal_median=causal_median,
            causal_ci=causal_ci,
            pooled_ratio_by_skill=causal["pooled_ratio_by_skill"],
        )
        gate_checkpoint: Path | None = None
        if status == "PASS":
            output_path = Path(args.output).resolve()
            gate_checkpoint = (
                Path(args.gate_checkpoint).resolve()
                if str(args.gate_checkpoint)
                else output_path.with_name(output_path.stem + "_gate_passed.pt")
            )
            _write_gate_passed_checkpoint(
                source=checkpoint,
                destination=gate_checkpoint,
                posterior=posterior,
                optimizer=posterior_optimizer,
                config=config,
            )

        return {
            "schema_version": SCHEMA_VERSION,
            "experiment": "R31-CFEI reward-off causal gate",
            "status": status,
            "reasons": reasons,
            "authorized_next_action": next_action,
            "source": {
                "checkpoint": str(checkpoint),
                "checkpoint_total_steps": int(source_total_steps),
                "checkpoint_update": int(source_update),
                "high_controller": metadata.get("high_controller"),
                "environment": "alice_bob_asymmetric_cycles",
                "external_reward": "collection_only",
                "gate_passed_checkpoint": (
                    str(gate_checkpoint) if gate_checkpoint is not None else None
                ),
            },
            "contract": {
                "natural_reset_groups": NATURAL_RESET_GROUPS,
                "posterior_train_reset_groups": TRAIN_RESET_GROUPS,
                "heldout_reset_groups": HELDOUT_RESET_GROUPS,
                "episode_steps": EPISODE_STEPS,
                "window": WINDOW,
                "natural_windows": len(natural_samples),
                "posterior_train_windows": len(train_samples),
                "heldout_natural_windows": len(heldout_samples),
                "causal_contexts": len(decisions),
                "forced_skills_per_context": N_SKILLS,
                "stochastic_replicas_per_skill": CAUSAL_REPLICAS,
                "forced_windows": len(decisions) * N_SKILLS * CAUSAL_REPLICAS,
                "forced_primitive_steps": len(decisions)
                * N_SKILLS
                * CAUSAL_REPLICAS
                * WINDOW,
                "posterior_epochs": POSTERIOR_EPOCHS,
                "posterior_batch_size": POSTERIOR_BATCH_SIZE,
                "posterior_lr": POSTERIOR_LR,
                "posterior_hidden_dim": int(config.r31_effect_hidden_dim),
                "bootstrap_repetitions": int(args.bootstrap_repetitions),
                "device": str(device),
                "forced_windows_used_for_posterior_training": 0,
                "policy_updates": 0,
                "source_policy_state_modified": False,
                "gate_passed_checkpoint_written": int(gate_checkpoint is not None),
            },
            "thresholds": THRESHOLDS,
            "metrics": {
                "M1_natural_effect_information": {
                    "mean_nats": natural_mean,
                    "ci95": [natural_ci[0], natural_ci[1]],
                    "per_skill": per_skill,
                    "posterior_train_final_losses": final_losses,
                },
                "matched_shuffle": {
                    "mean_nats": shuffle_mean,
                    "valid_rows": int(np.sum(shuffle_valid)),
                    "total_rows": int(shuffle_valid.size),
                    "valid_fraction": float(np.mean(shuffle_valid)),
                    "self_donors": int(np.sum(donor_indices == np.arange(donor_indices.size))),
                },
                "M2_causal_persistence": {
                    "median_ratio": causal_median,
                    "ci95": [causal_ci[0], causal_ci[1]],
                    "mean_between": float(np.mean(causal["between"])),
                    "mean_within": float(np.mean(causal["within"])),
                    "pooled_ratio_by_skill": causal["pooled_ratio_by_skill"],
                    "skill_pairs": causal["skill_pairs"].tolist(),
                    "forced_posterior_residual_mean": causal[
                        "forced_posterior_residual_mean"
                    ],
                    "forced_posterior_residual_by_skill": causal[
                        "forced_posterior_residual_by_skill"
                    ],
                },
            },
        }
    finally:
        env.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the frozen-policy R31 reward-off causal effect gate."
    )
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--gate_checkpoint",
        default="",
        help="PASS-only output; defaults beside --output with _gate_passed.pt",
    )
    parser.add_argument("--seed", type=int, default=31031)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument("--bootstrap_repetitions", type=int, default=10_000)
    args = parser.parse_args()
    if int(args.bootstrap_repetitions) <= 0:
        parser.error("--bootstrap_repetitions must be positive")
    return args


def main() -> None:
    args = parse_args()
    result = run(args)
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
