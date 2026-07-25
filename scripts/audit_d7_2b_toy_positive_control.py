"""D7.2B toy positive control — evaluation-only audit.

Contract: `docs/research/designs/D7_2B_TOY_POSITIVE_CONTROL_REALIZATION.md`.
Pass conditions A/B/C: `docs/research/designs/D7_R30_RENEWAL_DIAGNOSTIC.md`.
Estimands, clocks, continuation and normalization: `D0_CARRIER_AND_ESTIMAND.md`.

The policy is frozen. Freezing is not a compromise here -- `U_pi` is
policy-conditional, so both arms of every pair refer to one snapshot.

Nothing in this file may renegotiate a threshold. They are read from the frozen
contract below and reported against, whatever they say.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import torch

from ha_ctse_process import train as process_train
from ha_ctse_process.r30_fixed_clock import INVALID_SKILL, KEEP_TOKEN, SET_TOKEN
from ha_ctse_process.standalone_agent import (
    FixedSkillPrimitivePolicy,
    StandaloneProcessAgent,
)

# --- frozen thresholds, D7 "Pass conditions, fixed before the run" ------------
A_MATCH_FLOOR = 0.75
B_DIFF_FLOOR = 0.20
B_FLEX_FLOOR = 0.10
B_STABLE_CEIL = 0.05
C_SET_GAP_FLOOR = 0.50
C_SET_FLEX_FLOOR = 0.75
C_KEEP_STABLE_FLOOR = 0.75
C_FULL_SYNC_CEIL = 0.25

# The toy's two duties, by the axis of the skill that serves them.
SLOW_AXIS_SKILLS = (0, 1)   # +x, -x
FAST_AXIS_SKILLS = (2, 3)   # +y, -y


def regime_of(skill: int, active: bool) -> str:
    if not active or int(skill) == INVALID_SKILL:
        return "undefined"
    if int(skill) in FAST_AXIS_SKILLS:
        return "flex"
    if int(skill) in SLOW_AXIS_SKILLS:
        return "stable"
    return "undefined"


def target_skills_from_state(state: np.ndarray) -> tuple[int, int]:
    """(slow-serving skill, fast-serving skill) implied by the target signs.

    state = [slow_sign, 0, 0, fast_sign, fast_phase, slow_phase].
    """
    flat = np.asarray(state, dtype=np.float32).reshape(-1)
    if flat.size < 4:
        raise RuntimeError("toy state is missing its target signs")
    slow = 0 if float(flat[0]) > 0.0 else 1
    fast = 2 if float(flat[3]) > 0.0 else 3
    return slow, fast


# --- statistics ---------------------------------------------------------------

def clustered_mean_ci(clusters: list[list[float]], z: float = 1.959963985) -> dict:
    """Mean and normal 95% interval, clustered by episode.

    Checks inside one episode share the seeded target signs, so treating them as
    independent would understate the interval.
    """
    per_cluster = [float(np.mean(c)) for c in clusters if len(c) > 0]
    n = len(per_cluster)
    if n == 0:
        return {"mean": float("nan"), "lcb95": float("nan"), "ucb95": float("nan"),
                "clusters": 0, "points": 0}
    mean = float(np.mean(per_cluster))
    points = int(sum(len(c) for c in clusters))
    if n == 1:
        return {"mean": mean, "lcb95": float("-inf"), "ucb95": float("inf"),
                "clusters": 1, "points": points}
    se = float(np.std(per_cluster, ddof=1)) / math.sqrt(n)
    return {"mean": mean, "lcb95": mean - z * se, "ucb95": mean + z * se,
            "clusters": n, "points": points}


# --- ledger -------------------------------------------------------------------

@dataclass
class CheckRow:
    env_id: int
    episode_id: int
    step: int
    check_index: int
    agent_id: int
    act_sequence_branch: str
    token_kind: str
    keep_prob: float
    incumbent_skill: int
    set_skill: int
    skill_age_at_check: int
    urgency_regime: str
    mixed_urgency_check: bool
    slow_match: float
    fast_match: float
    team_reward: float
    termination_reason: str
    right_censored: bool


@dataclass
class EpisodeTrace:
    episode_id: int
    # The policy stream this history was generated under. Paired branches must
    # replay the *same* one, or they branch from a different pre-decision state
    # than the one whose incumbents and urgency regimes were recorded.
    policy_seed: int = 0
    rows: list[CheckRow] = field(default_factory=list)
    step_rewards: list[float] = field(default_factory=list)
    step_slow_match: list[float] = field(default_factory=list)
    step_fast_match: list[float] = field(default_factory=list)
    check_steps: list[int] = field(default_factory=list)
    # Per check: {agent_id: (incumbent_skill, active)} as of the pre-decision state.
    check_incumbents: list[dict] = field(default_factory=list)
    check_states: list[np.ndarray] = field(default_factory=list)
    actions: list[np.ndarray] = field(default_factory=list)


# --- the host -----------------------------------------------------------------

class ToyAuditHost:
    def __init__(self, config, agent: StandaloneProcessAgent, args):
        self.config = config
        self.agent = agent
        self.args = args
        self.k0 = int(getattr(config, "r39_toy_k0", 5))
        self.slow_blocks = int(getattr(config, "r39_toy_slow_period_blocks", 6))
        self.max_steps = int(getattr(config, "max_steps", 40))
        self.branch = self._branch_identity()

    def _branch_identity(self) -> str:
        """D0 section 8: recorded per run, never per config file."""
        agent = self.agent
        if bool(getattr(agent, "r39_native_categorical_edit", False)):
            return "native_categorical"
        if bool(getattr(agent, "r30_force_refresh_every_check", False)):
            return "full_refresh"
        if getattr(agent.high, "keep_head", None) is None:
            return "no_keep_head"
        return "learned_keep"

    def _env(self, seed: int):
        return process_train.create_env(
            self.config, self.config.scenario, seed, rank=0, scale_mode="eval"
        )

    def rollout(
        self,
        *,
        episode_seed: int,
        policy_seed: int,
        forced_at_check: int | None = None,
        forced_tokens: dict | None = None,
        post_seed: int | None = None,
        deterministic: bool = False,
        scripted: str | None = None,
    ) -> EpisodeTrace:
        """One episode from reset.

        The toy is a deterministic function of its two seeded initial signs and
        the action sequence, so replaying from reset under the same policy seed
        reproduces a pre-intervention history exactly -- which is what D0's
        admissibility conditions 1, 2 and 6 require. `post_seed` reseeds the
        policy stream immediately *after* the focal check, matched across arms, so
        the continuation randomness is shared while the prefix stays identical.

        `scripted` runs a source control instead of the policy: "constructive"
        always holds the skill each duty needs, "null" holds the initial
        assignment for the whole episode and never renews.
        """
        agent = self.agent
        env = self._env(episode_seed)
        torch.manual_seed(policy_seed)
        np.random.seed(policy_seed)
        obs, info = env.reset(seed=episode_seed)
        state = info.get("state")
        agent.reset_env_state(0)

        trace = EpisodeTrace(
            episode_id=int(episode_seed), policy_seed=int(policy_seed)
        )
        step = 0
        check_index = -1
        null_assignment: np.ndarray | None = None

        while True:
            due = bool(
                not np.all(agent.has_active_skill[0])
                or int(agent.steps_to_check[0]) <= 0
            )
            if scripted is None:
                if due:
                    check_index += 1
                    incumbents = {
                        int(a): (
                            int(agent.active_skills[0][a]),
                            bool(agent.has_active_skill[0][a]),
                        )
                        for a in range(agent.n_agents)
                    }
                    trace.check_incumbents.append(incumbents)
                    trace.check_steps.append(step)
                    trace.check_states.append(np.asarray(state, dtype=np.float32).copy())
                forced = (
                    forced_tokens
                    if (due and forced_at_check is not None and check_index == forced_at_check)
                    else None
                )
                agent.maybe_assign_skills(
                    obs,
                    state=state,
                    step=step,
                    k=self.k0,
                    env_id=0,
                    deterministic=deterministic,
                    collect_r31=False,
                    forced_tokens=forced,
                )
                if forced is not None and post_seed is not None:
                    # Matched continuation stream across arms.
                    torch.manual_seed(int(post_seed))
                if due:
                    self._append_rows(trace, step, check_index, obs, state)
                actions, _, _ = agent.act_low(
                    obs, env_id=0, deterministic=deterministic, state=state
                )
            else:
                slow_skill, fast_skill = target_skills_from_state(state)
                if scripted == "constructive":
                    skills = np.asarray([slow_skill, fast_skill], dtype=np.int64)
                elif scripted == "null":
                    if null_assignment is None:
                        null_assignment = np.asarray(
                            [slow_skill, fast_skill], dtype=np.int64
                        )
                    skills = null_assignment
                else:
                    raise ValueError(f"unknown scripted control {scripted!r}")
                table = FixedSkillPrimitivePolicy(4, 2, "continuous").action_table
                actions = table[torch.as_tensor(skills)].numpy().astype(np.float32)

            trace.actions.append(np.asarray(actions, dtype=np.float32).copy())
            obs, reward, terminated, truncated, last_info = env.step(actions)
            state = last_info.get("next_state", state)
            metrics = last_info.get("reward_info") or {}
            if not metrics:
                per_agent = last_info.get(0) or {}
                metrics = per_agent.get("reward_info", {}) if isinstance(per_agent, dict) else {}
            trace.step_rewards.append(float(reward))
            trace.step_slow_match.append(float(metrics.get("r39_toy_slow_match", float("nan"))))
            trace.step_fast_match.append(float(metrics.get("r39_toy_fast_match", float("nan"))))
            step += 1
            done = bool(terminated or truncated) or step >= self.max_steps
            if scripted is None:
                agent.record_environment_step(
                    0,
                    reward=float(reward),
                    next_obs=obs,
                    next_state=state,
                    done=done,
                    collect_r31=False,
                )
            if done:
                break
        env.close()
        return trace

    def _append_rows(self, trace, step, check_index, obs, state) -> None:
        """Read the decision the buffer just recorded for this check."""
        agent = self.agent
        buf = agent.high_check_buffer
        pending = buf.pending[0] if buf is not None else None
        if pending is None:
            return
        slow_target, fast_target = target_skills_from_state(state)
        prev = trace.check_incumbents[-1]
        regimes = {
            a: regime_of(prev[a][0], prev[a][1]) for a in range(agent.n_agents)
        }
        mixed = sorted(regimes.values()) == ["flex", "stable"]
        order = np.asarray(pending.agent_order, dtype=np.int64).reshape(-1)
        kinds = np.asarray(pending.token_kind, dtype=np.int64).reshape(-1)
        sets = np.asarray(pending.set_skill, dtype=np.int64).reshape(-1)
        keeps = np.asarray(pending.keep_prob, dtype=np.float32).reshape(-1)
        ages = np.asarray(pending.prev_ages, dtype=np.int64).reshape(-1)
        for position, agent_id in enumerate(order):
            agent_id = int(agent_id)
            trace.rows.append(
                CheckRow(
                    env_id=0,
                    episode_id=trace.episode_id,
                    step=int(step),
                    check_index=int(check_index),
                    agent_id=agent_id,
                    act_sequence_branch=self.branch,
                    token_kind="KEEP" if int(kinds[position]) == KEEP_TOKEN else "SET",
                    keep_prob=float(keeps[position]),
                    incumbent_skill=int(prev[agent_id][0]),
                    set_skill=int(sets[position]),
                    skill_age_at_check=int(ages[agent_id]),
                    urgency_regime=regimes[agent_id],
                    mixed_urgency_check=bool(mixed),
                    slow_match=float("nan"),
                    fast_match=float("nan"),
                    team_reward=float("nan"),
                    termination_reason=(
                        "renewal" if int(kinds[position]) == SET_TOKEN else "none"
                    ),
                    right_censored=False,
                )
            )
        del obs, slow_target, fast_target


# --- the audit ----------------------------------------------------------------

def window_return(trace: EpisodeTrace, from_step: int, horizon: int) -> float:
    end = min(from_step + horizon, len(trace.step_rewards))
    if end <= from_step:
        return float("nan")
    return float(np.sum(trace.step_rewards[from_step:end]))


def measure_b_h(host: ToyAuditHost, episodes: list[int], horizons: list[int]) -> dict:
    """D0's second normalizer form, measured from two source controls before the
    audit. Never estimated from an audited history.

    Averaged over windows starting at **every check boundary**, not just step 0.
    A step-0 window is degenerate on this source: the fast target does not flip
    until the first check elapses, so a no-renewal null is trivially optimal
    there and the measured gap collapses to exactly zero for `H = k0`. The
    estimand's windows start at focal checks, so the normalizer's must too.
    """
    out = {}
    controls = {
        seed: {
            name: host.rollout(episode_seed=seed, policy_seed=seed, scripted=name)
            for name in ("constructive", "null")
        }
        for seed in episodes
    }
    for horizon in horizons:
        constructive, null = [], []
        for seed in episodes:
            pair = controls[seed]
            length = len(pair["constructive"].step_rewards)
            starts = [s for s in range(0, length, host.k0) if s + horizon <= length]
            if not starts:
                starts = [0]
            for start in starts:
                for name, dest in (("constructive", constructive), ("null", null)):
                    value = window_return(pair[name], start, horizon)
                    if np.isfinite(value):
                        dest.append(value)
        gap = float(np.mean(constructive)) - float(np.mean(null))
        out[str(horizon)] = {
            "constructive_mean": float(np.mean(constructive)),
            "null_mean": float(np.mean(null)),
            "windows": len(constructive),
            "window_starts": "every check boundary with a full horizon",
            "b_h": gap,
        }
    return out


def condition_a(traces: list[EpisodeTrace]) -> dict:
    slow = [[v for v in t.step_slow_match if np.isfinite(v)] for t in traces]
    fast = [[v for v in t.step_fast_match if np.isfinite(v)] for t in traces]
    slow_ci = clustered_mean_ci(slow)
    fast_ci = clustered_mean_ci(fast)
    passed = (
        slow_ci["lcb95"] >= A_MATCH_FLOOR and fast_ci["lcb95"] >= A_MATCH_FLOOR
    )
    return {
        "slow_match": slow_ci,
        "fast_match": fast_ci,
        "floor": A_MATCH_FLOOR,
        "passed": bool(passed),
    }


def condition_c(traces: list[EpisodeTrace]) -> dict:
    set_flex, keep_stable, full_sync = [], [], []
    for trace in traces:
        flex_c, stable_c, sync_c = [], [], []
        by_check: dict[int, list[CheckRow]] = {}
        for row in trace.rows:
            if not row.mixed_urgency_check:
                continue
            by_check.setdefault(row.check_index, []).append(row)
            if row.urgency_regime == "flex":
                flex_c.append(1.0 if row.token_kind == "SET" else 0.0)
            elif row.urgency_regime == "stable":
                stable_c.append(1.0 if row.token_kind == "KEEP" else 0.0)
        for rows in by_check.values():
            sync_c.append(1.0 if all(r.token_kind == "SET" for r in rows) else 0.0)
        set_flex.append(flex_c)
        keep_stable.append(stable_c)
        full_sync.append(sync_c)
    p_set_flex = clustered_mean_ci(set_flex)
    p_keep_stable = clustered_mean_ci(keep_stable)
    p_full_sync = clustered_mean_ci(full_sync)
    # P(SET|stable) = 1 - P(KEEP|stable); the gap uses the same clusters.
    gap_clusters = [
        [f - (1.0 - s) for f, s in zip(fc, sc)]
        for fc, sc in zip(set_flex, keep_stable)
        if fc and sc and len(fc) == len(sc)
    ]
    gap = clustered_mean_ci(gap_clusters)
    passed = (
        gap["lcb95"] >= C_SET_GAP_FLOOR
        and p_set_flex["lcb95"] >= C_SET_FLEX_FLOOR
        and p_keep_stable["lcb95"] >= C_KEEP_STABLE_FLOOR
        and p_full_sync["ucb95"] <= C_FULL_SYNC_CEIL
    )
    return {
        "p_set_given_flex": p_set_flex,
        "p_keep_given_stable": p_keep_stable,
        "p_set_gap": gap,
        "p_full_sync_set_mixed": p_full_sync,
        "same_label_renewal": "NOT_APPLICABLE_STRUCTURALLY_EXCLUDED",
        "thresholds": {
            "gap_floor": C_SET_GAP_FLOOR,
            "set_flex_floor": C_SET_FLEX_FLOOR,
            "keep_stable_floor": C_KEEP_STABLE_FLOOR,
            "full_sync_ceiling": C_FULL_SYNC_CEIL,
        },
        "passed": bool(passed),
    }


def condition_b(
    host: ToyAuditHost,
    traces: list[EpisodeTrace],
    b_h: dict,
    horizon: int,
    replicates: int,
    base_policy_seed: int,
) -> dict:
    """Paired KEEP-versus-SET at every mixed-urgency check."""
    n_skills = int(host.agent.n_skills)
    b_value = float(b_h[str(horizon)]["b_h"])
    if not np.isfinite(b_value) or abs(b_value) < 1e-9:
        # No renewal headroom over this horizon: U~ is not defined, and dividing
        # anyway would report an arbitrary number as an effect size.
        return {
            "horizon": horizon,
            "b_h": b_value,
            "measurable": False,
            "reason": "no renewal headroom over this horizon; U~ is undefined",
            "passed": False,
        }
    flex_clusters: list[list[float]] = []
    stable_clusters: list[list[float]] = []
    diff_clusters: list[list[float]] = []
    opp_flex_clusters: list[list[float]] = []
    dropped = 0
    pairs = 0

    for trace in traces:
        flex_c, stable_c, diff_c, opp_c = [], [], [], []
        by_check: dict[int, list[CheckRow]] = {}
        for row in trace.rows:
            if row.mixed_urgency_check:
                by_check.setdefault(row.check_index, []).append(row)
        for check_index, rows in sorted(by_check.items()):
            focal_step = trace.check_steps[check_index]
            per_regime: dict[str, float] = {}
            for row in rows:
                if row.urgency_regime not in {"flex", "stable"}:
                    continue
                if not (0 <= row.incumbent_skill < n_skills):
                    dropped += 1
                    continue
                keep_returns, pi_returns = [], []
                opp_returns: dict[int, list[float]] = {
                    z: [] for z in range(n_skills) if z != row.incumbent_skill
                }

                def branch(forced, post):
                    return host.rollout(
                        episode_seed=trace.episode_id,
                        policy_seed=trace.policy_seed,
                        forced_at_check=check_index,
                        forced_tokens={row.agent_id: forced},
                        post_seed=post,
                    )

                for rep in range(replicates):
                    post = base_policy_seed + 7919 * (rep + 1)
                    keep = branch((KEEP_TOKEN, INVALID_SKILL), post)
                    pi = branch((SET_TOKEN, INVALID_SKILL), post)
                    admissible = (
                        _prefix_matches(keep, pi, focal_step)
                        and _focal_state_matches(keep, trace, check_index)
                        and _focal_state_matches(pi, trace, check_index)
                    )
                    if not admissible:
                        dropped += 1
                        continue
                    keep_returns.append(window_return(keep, focal_step, horizon))
                    pi_returns.append(window_return(pi, focal_step, horizon))
                    for z in opp_returns:
                        arm = branch((SET_TOKEN, z), post)
                        if not _focal_state_matches(arm, trace, check_index):
                            dropped += 1
                            continue
                        opp_returns[z].append(window_return(arm, focal_step, horizon))
                if not keep_returns or not pi_returns:
                    continue
                pairs += 1
                keep_mean = float(np.mean(keep_returns))
                u_pi = (float(np.mean(pi_returns)) - keep_mean) / b_value
                per_regime[row.urgency_regime] = u_pi
                if row.urgency_regime == "flex":
                    flex_c.append(u_pi)
                    u_opp = _split_sample_u_opp(opp_returns, keep_mean, b_value)
                    if u_opp is not None:
                        opp_c.append(u_opp)
                else:
                    stable_c.append(u_pi)
            if "flex" in per_regime and "stable" in per_regime:
                diff_c.append(per_regime["flex"] - per_regime["stable"])
        for src, dest in (
            (flex_c, flex_clusters),
            (stable_c, stable_clusters),
            (diff_c, diff_clusters),
            (opp_c, opp_flex_clusters),
        ):
            dest.append(src)

    u_flex = clustered_mean_ci(flex_clusters)
    u_stable = clustered_mean_ci(stable_clusters)
    u_diff = clustered_mean_ci(diff_clusters)
    u_opp_flex = clustered_mean_ci(opp_flex_clusters)
    passed = (
        u_diff["lcb95"] >= B_DIFF_FLOOR
        and u_flex["lcb95"] >= B_FLEX_FLOOR
        and u_stable["ucb95"] <= B_STABLE_CEIL
    )
    return {
        "horizon": horizon,
        "b_h": b_value,
        "u_pi_flex": u_flex,
        "u_pi_stable": u_stable,
        "u_pi_difference": u_diff,
        "u_opp_flex_split_sample": u_opp_flex,
        "pairs": pairs,
        "dropped_pairs": dropped,
        "thresholds": {
            "difference_floor": B_DIFF_FLOOR,
            "flex_floor": B_FLEX_FLOOR,
            "stable_ceiling": B_STABLE_CEIL,
        },
        "passed": bool(passed),
    }


def _prefix_matches(a: EpisodeTrace, b: EpisodeTrace, focal_step: int) -> bool:
    """D0 admissibility 6: the pre-intervention history must be equal, checked
    rather than assumed. A failing pair is dropped and counted, never repaired."""
    if focal_step <= 0:
        return True
    if len(a.actions) < focal_step or len(b.actions) < focal_step:
        return False
    return all(
        np.array_equal(a.actions[i], b.actions[i]) for i in range(focal_step)
    ) and np.allclose(
        a.step_rewards[:focal_step], b.step_rewards[:focal_step], rtol=0, atol=0
    )


def _focal_state_matches(
    branch: EpisodeTrace, natural: EpisodeTrace, check_index: int
) -> bool:
    """D0 admissibility 2: the incumbent skills, active mask and ages at the focal
    check must equal the ones the natural history recorded, since those are what
    the urgency regime and the intervention were defined against."""
    if check_index >= len(branch.check_incumbents):
        return False
    if check_index >= len(natural.check_incumbents):
        return False
    return branch.check_incumbents[check_index] == natural.check_incumbents[check_index]


def _split_sample_u_opp(
    opp_returns: dict[int, list[float]], keep_mean: float, b_value: float
) -> float | None:
    """D0 section 3: the maximizing skill is selected on one replicate set and
    valued on an independent one. Maximizing and valuing on the same sample
    manufactures an optimistic source effect, because the selection is itself an
    estimate."""
    usable = {z: v for z, v in opp_returns.items() if len(v) >= 2}
    if not usable:
        return None
    half = min(len(v) for v in usable.values()) // 2
    if half < 1:
        return None
    select = {z: float(np.mean(v[:half])) for z, v in usable.items()}
    best = max(select, key=select.get)
    evaluate = float(np.mean(usable[best][half : 2 * half]))
    return (evaluate - keep_mean) / b_value


def verdict(a: dict, b: dict, c: dict, b_h: dict, horizon: int) -> tuple[str, str]:
    """D7's branch table, first match. Identification and access precede
    behaviour, so an access failure never reads as a renewal result."""
    if abs(float(b_h[str(horizon)]["b_h"])) < 1e-9:
        return (
            "NO_RENEWAL_HEADROOM_D7_TOY_SOURCE",
            "constructive and null source controls are indistinguishable over H, "
            "so nothing downstream is measurable",
        )
    if not a["passed"]:
        return (
            "NO_ACCESS_D7_TOY_POSITIVE_CONTROL",
            "competence prerequisite failed; this does not update R30 renewal capacity",
        )
    if not b["passed"]:
        return (
            "NONFORMAL_NO_URGENCY_SEPARATION_D7_2B",
            "access held but the interventional contrast did not separate the "
            "regimes; the learned skill support or this source does not expose "
            "urgency as registered",
        )
    if not c["passed"]:
        return (
            "NONFORMAL_CAPABILITY_WITHOUT_ALIGNMENT_D7_2B",
            "the capability is present but the policy or its credit does not use it",
        )
    return (
        "NONFORMAL_CARRIER_EXPRESSES_URGENCY_D7_2B",
        "carrier can express urgency where it provably exists; proceed to the "
        "main source. Not a claim about variable k",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--config", default="config_d7_2b_toy_learned_keep")
    parser.add_argument("--out", required=True)
    parser.add_argument("--episodes", type=int, default=24)
    parser.add_argument("--replicates", type=int, default=4)
    parser.add_argument("--seed", type=int, default=3229000)
    parser.add_argument("--horizon", type=int, default=30)
    parser.add_argument("--horizon-secondary", type=int, default=5)
    parser.add_argument("--skill_interval", type=int, default=5)
    parser.add_argument("--eval_max_steps", type=int, default=0)
    args = parser.parse_args()

    torch.set_num_threads(1)
    config = importlib.import_module(args.config).Config()
    config.scenario = process_train.normalize_scenario(config.scenario)
    agent = StandaloneProcessAgent(
        obs_dim=int(config.obs_dim),
        action_dim=int(config.action_dim),
        n_agents=int(config.n_agents),
        config=config,
        device="cpu",
        action_space_type=str(config.action_space_type),
        num_envs=1,
    )
    process_train.load_checkpoint(args.checkpoint, agent, load_optimizers=False)
    for module in (agent.high, agent.high_value):
        if module is not None:
            module.eval()

    host = ToyAuditHost(config, agent, args)
    if host.branch != "learned_keep":
        raise RuntimeError(
            f"D7.2B requires the learned-keep branch; this run is {host.branch!r}. "
            "Renewal urgency is observable only there (D0 section 2)."
        )

    episodes = [int(args.seed) + 100000 + i for i in range(int(args.episodes))]
    horizons = sorted({int(args.horizon), int(args.horizon_secondary)})

    # Order matters: B_H is frozen from source controls *before* the audit.
    b_h = measure_b_h(host, episodes, horizons)
    traces = [
        host.rollout(episode_seed=seed, policy_seed=int(args.seed) + seed)
        for seed in episodes
    ]

    a = condition_a(traces)
    c = condition_c(traces)
    b = condition_b(
        host, traces, b_h, int(args.horizon), int(args.replicates), int(args.seed)
    )
    b_secondary = condition_b(
        host,
        traces,
        b_h,
        int(args.horizon_secondary),
        int(args.replicates),
        int(args.seed),
    )

    branch, reason = verdict(a, b, c, b_h, int(args.horizon))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "d7_2b_event_ledger.jsonl").open("w", encoding="utf-8") as handle:
        for trace in traces:
            for row in trace.rows:
                handle.write(json.dumps(asdict(row), ensure_ascii=False) + "\n")
    result = {
        "branch": branch,
        "reason": reason,
        "act_sequence_branch": host.branch,
        "checkpoint": str(args.checkpoint),
        "config": args.config,
        "episodes": len(episodes),
        "replicates": int(args.replicates),
        "b_h_measured": b_h,
        "condition_a_competence": a,
        "condition_b_interventional": b,
        "condition_b_secondary_horizon": b_secondary,
        "condition_c_natural_alignment": c,
        "contract": "docs/research/designs/D7_2B_TOY_POSITIVE_CONTROL_REALIZATION.md",
    }
    with (out / "d7_2b_audit_result.json").open("w", encoding="utf-8") as handle:
        json.dump(result, handle , ensure_ascii=False, indent=2)
    print(f"D7_2B_BRANCH={branch}")
    print(f"D7_2B_REASON={reason}")
    print(json.dumps(
        {
            "b_h": b_h,
            "A": {k: a[k] for k in ("slow_match", "fast_match", "passed")},
            "B": {k: b.get(k) for k in ("u_pi_flex", "u_pi_stable", "u_pi_difference",
                                        "pairs", "dropped_pairs", "measurable",
                                        "passed")},
            "C": {k: c[k] for k in ("p_set_given_flex", "p_keep_given_stable",
                                    "p_set_gap", "passed")},
        },
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
