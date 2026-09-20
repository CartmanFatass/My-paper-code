"""Matched finite-episode evaluation components; no launcher or checkpoint admission.

The caller supplies a separate evaluation agent/worlds and owns their lifetime. This
function freezes and resets that agent, so it must never run on live training lanes.
Only initialized tiny models are used by the accompanying correctness tests.
"""
from contextlib import contextmanager
import copy
from numbers import Integral
import time

import numpy as np
import torch

from scripts.run_flexible_skill_duration_e0 import _preserve_rng
from scripts.run_fsd_label_content_b08 import ExecutionRule, label_generator

from .runtime import Scenario1Features, freeze_foundation


RULES = ("as_trained", "uniform_every_10", "joint", "independent")
COMPONENTS = ("coverage_reward", "quality_reward", "energy_penalty", "total_reward")


class EvaluationFailure(RuntimeError):
    """A failed panel with actual returned-transition counts and partial returns."""

    def __init__(self, summary):
        self.summary = summary
        super().__init__(summary["failure"])


@contextmanager
def _gate(agent, policy, features):
    existed = "_optional_end_hook" in vars(agent)
    if policy is not None:
        # No mode/RNG changes on the caller's policy, including a live training gate.
        gate = copy.deepcopy(policy).eval()

        def choose(snapshot, *, deterministic):
            if not deterministic:
                raise ValueError("this evaluator requires deterministic gate decisions")
            context = features.encode(snapshot)
            eligible = torch.from_numpy(snapshot["eligible"].copy())
            forced = torch.from_numpy(snapshot["forced_end"].copy())
            sample = gate.sample(context, eligible, forced, deterministic=True)
            return (sample.actions & eligible).cpu().numpy()

        agent.set_optional_end_hook(choose)
    try:
        yield
    finally:
        if policy is not None:
            agent.set_optional_end_hook(None)
            if not existed:
                vars(agent).pop("_optional_end_hook", None)


def evaluate_episode(envs, agent, *, rule, evaluation_seed, horizon,
                     policy=None, features=None):
    """Run one complete finite native episode per lane, with zero optimizer steps.

    World seeds are ``evaluation_seed + lane`` for every rule. R10 reuses the
    published B08 execution wrapper and its dedicated (seed, rule) RNG: it draws
    at every tick but applies replacements only at the original clock decisions.
    Primitive actions and the J/I masks/selector are deterministic. R10's labels
    remain random; calling its actor deterministic does not make that rule greedy.

    J = n_agents * the adapter's reward sum / horizon, as in the FSD panels.
    Label changes count returned native transitions, not the original decoder's
    pre-replacement switch metric. Decision counts count batched policy queries;
    on failure some of those decisions may not have reached a native step.
    No GAE, gate-critic forward or optimizer is needed.
    Failures after starting the panel raise EvaluationFailure with partial facts.
    Setup errors raise ValueError before resetting or stepping a world.

    This component neither verifies a production checkpoint nor grants permission
    for native evaluation. A future admitted runner must supply those bindings.
    """
    if rule not in RULES:
        raise ValueError("unknown termination evaluation rule")
    if (not isinstance(horizon, Integral) or isinstance(horizon, bool) or horizon <= 0
            or not isinstance(evaluation_seed, Integral) or isinstance(evaluation_seed, bool)
            or evaluation_seed < 0):
        raise ValueError("horizon and evaluation_seed must be valid integers")
    if getattr(agent, "_optional_end_hook", None) is not None:
        raise ValueError("evaluation requires a separate agent without a live gate")
    if "_batched_assign_skills" in vars(agent):
        raise ValueError("evaluation requires an unwrapped skill assignment method")
    lanes = len(envs)
    if lanes != agent.config.num_envs or lanes == 0:
        raise ValueError("evaluation lane count mismatch")
    schema = features or Scenario1Features(
        agent.config.n_agents, agent.config.n_users, agent.config.obs_dim)
    if (schema.n_agents != agent.config.n_agents or schema.n_users != agent.config.n_users
            or schema.obs_dim != agent.config.obs_dim or schema.state_dim != agent.config.state_dim
            or (schema.local_cap, schema.team_cap, schema.n_agent_labels, schema.n_team_labels)
            != (10, 10, 6, 6)):
        raise ValueError("evaluation feature schema differs from foundation")
    gated = rule in ("joint", "independent")
    if gated:
        if (policy is None or policy.mode != rule or policy.context_dim != schema.context_dim
                or policy.n_agents != schema.n_agents
                or any(p.device.type != "cpu" for p in policy.parameters())):
            raise ValueError("gate rule, features and CPU policy must match")
    elif policy is not None:
        raise ValueError("a fixed reference must not receive a gate policy")
    for env in envs:
        raw = env.env
        if (raw.max_steps != horizon or raw.n_uavs != schema.n_agents
                or raw.n_users != schema.n_users or raw.area_size != schema.area_size):
            raise ValueError("evaluation world differs from declared geometry")
    freeze_foundation(agent)
    label_rule = "uniform_every_10" if rule == "uniform_every_10" else "as_trained"
    execution = ExecutionRule(label_rule, agent, horizon=horizon,
                              generator=label_generator(evaluation_seed, label_rule))
    summary = {
        "status": "incomplete", "failure": None, "rule": rule,
        "evaluation_seed": int(evaluation_seed),
        "lane_seeds": [int(evaluation_seed) + lane for lane in range(lanes)],
        "horizon": int(horizon), "n_agents": schema.n_agents,
        "evaluation_steps": 0, "steps_per_lane": [0] * lanes,
        "evaluation_agent_step_batches": 0, "completed_episodes": 0,
        "foundation_optimizer_steps": 0, "gate_optimizer_steps": 0,
        "foundation_buffer_writes": 0, "decision_rows": 0, "team_decision_rows": 0,
        "resampled_local_bits": 0, "optional_end_bits": 0,
        "return_sums_U": [0.0] * lanes, "native_scores_J": None, "J_mean": None,
        "native_score_factor": schema.n_agents / horizon,
        "primitive_actions_deterministic": True,
        "gate_deterministic": True if gated else None,
        "selector_rule": "uniform" if label_rule == "uniform_every_10" else "argmax",
        "caps": {"local": 10, "team": 10},
        "component_sums": {key: [0.0] * lanes for key in COMPONENTS},
    }
    returns = np.zeros(lanes, dtype=np.float64)
    components = {key: np.zeros(lanes, dtype=np.float64) for key in COMPONENTS}
    previous_agents = np.full((lanes, schema.n_agents), -1, dtype=np.int64)
    previous_team = np.full(lanes, -1, dtype=np.int64)
    agent_histogram, team_histogram = np.zeros(6, dtype=np.int64), np.zeros(6, dtype=np.int64)
    label_changes = dict(agents=0, team=0, agent_comparisons=0, team_comparisons=0)
    started = time.perf_counter()
    try:
        with _preserve_rng(), torch.no_grad(), _gate(agent, policy, schema), execution.attached():
            states, observations = [], []
            for lane, env in enumerate(envs):
                obs, info = env.reset(seed=summary["lane_seeds"][lane])
                agent.reset_env_state(lane)
                states.append(np.asarray(info["state"], dtype=np.float64))
                observations.append(np.asarray(obs, dtype=np.float32))
            states, observations = np.stack(states), np.stack(observations)
            if not np.isfinite(states).all() or not np.isfinite(observations).all():
                raise ValueError("nonfinite evaluation reset inputs")
            steps, dones = np.zeros(lanes, dtype=np.int64), np.zeros(lanes, dtype=bool)
            for tick in range(horizon):
                actions, _, _ = agent.step(states, observations, steps, dones,
                                            deterministic=True, return_step_data=True,
                                            build_infos=False)
                summary["evaluation_agent_step_batches"] += 1
                if not np.isfinite(actions).all():
                    raise ValueError("nonfinite evaluation action")
                last = agent._d2_last_step
                summary["decision_rows"] += int(last["decision"].sum())
                summary["team_decision_rows"] += int(last["sample_Z"].sum())
                summary["resampled_local_bits"] += int(last["sampled_mask"].sum())
                if gated:
                    summary["optional_end_bits"] += int(last["optional_end"].sum())
                for lane, env in enumerate(envs):
                    obs, reward, term, trunc, info = env.step(actions[lane])
                    # A returned transition counts even if subsequent validation fails.
                    summary["evaluation_steps"] += 1
                    summary["steps_per_lane"][lane] += 1
                    dones[lane] = bool(term or trunc)
                    summary["completed_episodes"] += int(dones[lane])
                    labels = np.asarray(agent.env_agent_skills[lane], dtype=np.int64)
                    team_label = int(agent.env_team_skills[lane])
                    agent_histogram += np.bincount(labels, minlength=6)
                    team_histogram[team_label] += 1
                    if previous_team[lane] >= 0:
                        label_changes["agents"] += int((labels != previous_agents[lane]).sum())
                        label_changes["team"] += int(team_label != previous_team[lane])
                        label_changes["agent_comparisons"] += schema.n_agents
                        label_changes["team_comparisons"] += 1
                    previous_agents[lane], previous_team[lane] = labels, team_label
                    if not np.isfinite(reward):
                        raise ValueError("nonfinite evaluation reward")
                    returns[lane] += float(reward)
                    if not np.isfinite(returns[lane]):
                        raise ValueError("nonfinite accumulated evaluation return")
                    summary["return_sums_U"] = returns.tolist()
                    values = info["reward_components"]["reward_info"]
                    if not all(np.isfinite(values[key]) for key in COMPONENTS):
                        raise ValueError("nonfinite native reward component")
                    for key in COMPONENTS:
                        components[key][lane] += float(values[key])
                    summary["component_sums"] = {k: v.tolist() for k, v in components.items()}
                    states[lane] = np.asarray(info["next_state"], dtype=np.float64)
                    observations[lane] = np.asarray(obs, dtype=np.float32)
                    if not np.isfinite(states[lane]).all() or not np.isfinite(observations[lane]).all():
                        raise ValueError("nonfinite evaluation successor")
                if ((tick < horizon - 1 and dones.any())
                        or (tick == horizon - 1 and not dones.all())):
                    raise ValueError("evaluation ended outside the declared finite horizon")
                steps += 1
        scores = schema.n_agents * returns / horizon
        summary.update(status="complete", native_scores_J=scores.tolist(),
                       J_mean=float(scores.mean()),
                       component_means={k: (v / horizon).tolist() for k, v in components.items()})
    except Exception as error:
        summary["failure"] = f"{type(error).__name__}: {error}"
        raise EvaluationFailure(summary) from error
    finally:
        summary["wall_seconds"] = time.perf_counter() - started
        summary["label_change_counts"] = label_changes
        summary["executed_label_histograms"] = {
            "agents": agent_histogram.tolist(), "team": team_histogram.tolist()}
    return summary
