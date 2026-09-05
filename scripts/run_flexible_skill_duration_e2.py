"""E2 runner - D2 interruption-cost sweep against the fixed-`k` sweep on the homogeneous corridor.

Launch contract: `docs/Claude_docs/experiments/E2_INTERRUPTION_COST_SWEEP_20260903.md`.
Claim ceiling **B (EXPLORE)**.  Nothing this script writes is a performance claim.

One arm-seed per invocation.  Contract section 6 asks for a runner that "imports the E0
runner's manifest, preflight and summary conventions and the corridor driver; does not copy
the E0 loop".  This module therefore

* imports `scripts/run_flexible_skill_duration_e0.py` for `_jsonable`, `_git`,
  `_preserve_rng`, `_sha256_arrays`, `_capture_theta0`, `_exposure_line`, `_StepCounter`
  and `run_preflight` (the manifest / preflight / summary conventions), and
* runs the **corridor** rollout loop of `envs.relay_corridor.hmasd_driver`
  (`RelayCorridorHMASDDriver.run_rollout`), which is the loop ADR 02 fixes for this host.

Nothing under `hmasd/`, `envs/`, `config_1.py`, `config.py`, `tests/fixtures/` or the E0/E1
runners is modified.  The extra per-step quantities contract section 3 asks for that the
driver does not return (the agent gaps `g_i` / `g_Z`, the per-position boundary causes and
the host's per-step region change flags) are captured by wrapping three **bound methods on
the instances this runner owns** - `adapter.step`, `agent.get_d2_metrics` and `agent.update`
- which leaves the imported modules untouched.

Usage (explicit interpreter, per CLAUDE.md):

    C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe \
        scripts/run_flexible_skill_duration_e2.py \
        --arm d0_k40 --seed 1 --rollouts 20 --num-envs 16 --threads 4 \
        --launch-commit <sha> \
        --output-root temp/directions/flexible_skill_duration/exp/E2_20260903
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import platform
import socket
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from config_1 import Config  # noqa: E402
from envs.relay_corridor.adapter import RelayCorridorAdapter  # noqa: E402
from envs.relay_corridor.config import RelayCorridorConfig, validate_horizon  # noqa: E402
from envs.relay_corridor.hmasd_driver import (  # noqa: E402
    RelayCorridorHMASDDriver,
    build_corridor_learner_config,
)
from envs.relay_corridor.references import enumerate_references  # noqa: E402
from hmasd.agent import HMASDAgent  # noqa: E402

import run_flexible_skill_duration_e0 as e0  # noqa: E402

_jsonable = e0._jsonable
_git = e0._git
_preserve_rng = e0._preserve_rng
_sha256_arrays = e0._sha256_arrays
_utc_now = e0._utc_now
run_preflight = e0.run_preflight


CONTRACT = "docs/Claude_docs/experiments/E2_INTERRUPTION_COST_SWEEP_20260903.md"

# ---------------------------------------------------------------------------
# The host point and the arm table (contract section 2)
# ---------------------------------------------------------------------------

#: The mechanics page's first-object point **except the hazard**, which contract
#: section 2 makes homogeneous at the small row's second-region rate.
HOST_POINT = dict(
    n_agents=6,
    n_roles=2,
    n_zones=4,
    n_regions=2,
    horizon=400,
    delta=0.4,
    event_process="bernoulli",
    lambda_regions=(0.02, 0.02),
    d0_k_set=(1, 2, 5, 20, 40),
    rho=0.0,
    c_probe=0.0,
    role_decode="argmax",
)

#: D0 fixed-`k` grid (the mechanics page's grid).
D0_K_SET = (1, 2, 5, 20, 40)
#: Finite `c` grid, from E0's D0 gap histogram (contract section 2).
D2_C_SET = (0.25, 0.5, 1.0, 2.0)
#: Both caps of the D2 arms.
D2_K_CAP = 40

INF = float("inf")


def _c_slug(c: float) -> str:
    """`0.25 -> 0p25`, `0.5 -> 0p5`, `1.0 -> 1p0`, `2.0 -> 2p0` (directory-safe)."""
    return str(float(c)).replace(".", "p")


#: arm id -> family and grid point.  Nine arms; `c = inf` is the D0 arm at each `k`.
ARMS = {}
for _k in D0_K_SET:
    ARMS["d0_k%d" % _k] = {"family": "d0", "k": int(_k), "c": INF}
for _c in D2_C_SET:
    ARMS["d2_c%s" % _c_slug(_c)] = {"family": "d2", "k": D2_K_CAP, "c": float(_c)}

#: Contract section 2 launch order: the central pair first, then the other `k`,
#: then the other `c`; seed 1 before seed 2 inside each arm.
ARM_ORDER = (
    "d0_k40", "d2_c1p0",
    "d0_k1", "d0_k2", "d0_k5", "d0_k20",
    "d2_c0p25", "d2_c0p5", "d2_c2p0",
)
#: Contract section 4.4: the outer arms whose seed 2 is dropped first.
OUTER_ARMS = ("d0_k1", "d0_k2", "d2_c0p25", "d2_c2p0")
#: Contract section 2's matched pair (first rollout bit-identical until the first interruption).
MATCHED_PAIR = ("d0_k40", "d2_c1p0")
#: The pair contract section 2 names for the bit-identity check.
BIT_IDENTITY_PAIR = ("d0_k40", "d2_c2p0")


def corridor_config(**overrides) -> RelayCorridorConfig:
    """The frozen E2 host point (contract section 2)."""
    kwargs = dict(HOST_POINT)
    kwargs.update(overrides)
    return RelayCorridorConfig(**kwargs)


def arm_parameters(arm: str) -> dict:
    """The learner overrides for one arm.

    D0 (`k` sweep): `c = c_Z = inf`, `k_max = k_Z = k`, the fair D0 of ADR 01.
    D2 (`c` sweep): `c = c_Z = c`, `k_max = k_Z = 40`.
    Every arm runs `policy_interruption_mode = "d2"` with `age_feature = "off"`
    (E1 settled the age input; review Part XI.2).
    """
    if arm not in ARMS:
        raise KeyError(f"unknown arm {arm!r}; known arms: {sorted(ARMS)}")
    row = ARMS[arm]
    return {
        "policy_interruption_mode": "d2",
        "interruption_delta": 1,
        "interruption_cost_c": float(row["c"]),
        "interruption_cost_c_Z": float(row["c"]),
        "skill_cap_k_max": int(row["k"]),
        "team_cap_k_Z": int(row["k"]),
        "age_feature": "off",
    }


class E2CorridorConfig(Config):
    """Module-level config class so `agent.save_model` can pickle it.

    `build_corridor_learner_config` builds a config whose class is defined inside a
    function body, which `torch.save` cannot pickle.  The runner rebinds the
    instance's `__class__` to this one immediately after construction.  Both are
    empty subclasses of `config_1.Config`, so no attribute, default or behaviour
    changes; only the pickle path does.
    """


# ---------------------------------------------------------------------------
# Boundary causes (read from the agent, never redefined here)
# ---------------------------------------------------------------------------

CAUSE_NONE = HMASDAgent.D2_CAUSE_NONE
CAUSE_RESET = HMASDAgent.D2_CAUSE_RESET
CAUSE_TEAM_GAP = HMASDAgent.D2_CAUSE_TEAM_GAP
CAUSE_TEAM_CAP = HMASDAgent.D2_CAUSE_TEAM_CAP
CAUSE_GAP = HMASDAgent.D2_CAUSE_GAP
CAUSE_CAP = HMASDAgent.D2_CAUSE_CAP
CAUSE_NAMES = dict(HMASDAgent.D2_CAUSE_NAMES)

DECILE_QUANTILES = tuple(round(0.1 * i, 1) for i in range(1, 10))


def decile_summary(values) -> dict:
    """Count, moments and the nine deciles of a 1-D sample (empty-safe)."""
    array = np.asarray(values, dtype=np.float64).ravel()
    array = array[np.isfinite(array)]
    if array.size == 0:
        return {"count": 0, "mean": None, "std": None, "min": None, "max": None,
                "quantiles": list(DECILE_QUANTILES), "deciles": None}
    return {
        "count": int(array.size),
        "mean": float(array.mean()),
        "std": float(array.std()),
        "min": float(array.min()),
        "max": float(array.max()),
        "quantiles": list(DECILE_QUANTILES),
        "deciles": [float(q) for q in np.quantile(array, DECILE_QUANTILES)],
    }


def event_alignment(sampled, change_flag, region_of_agent) -> dict:
    """Contract section 3 item 2: the event-alignment fraction.

    `sampled[t, b, i]` is True when agent `i` of lane `b` was re-decided at step
    `t` (the D2 sampled mask, which is exactly the `RENEW` mask the host sees).
    `change_flag[t, b, r]` is the host's region change flag **visible at step
    `t`**: the host raises it at the step the event is realised into.

    "within one step after the agent's region flag flipped" is read as the two-step
    window `{t_flip, t_flip + 1}`, i.e. an interruption at step `t` counts when the
    agent's region flag is up at `t` or was up at `t - 1`.  The one-step reading
    (`t` only) is reported beside it as `aligned_fraction_strict` so a reader can
    apply either.
    """
    sampled = np.asarray(sampled, dtype=bool)
    change_flag = np.asarray(change_flag).astype(bool)
    region_of_agent = np.asarray(region_of_agent, dtype=np.int64)
    flag_agent = change_flag[:, :, region_of_agent]            # [T, B, N]
    previous = np.zeros_like(flag_agent)
    previous[1:] = flag_agent[:-1]
    window = flag_agent | previous
    total = int(sampled.sum())
    return {
        "interruptions": total,
        "aligned_window": "{t_flip, t_flip + 1}",
        "aligned_count": int((sampled & window).sum()),
        "aligned_fraction": (float((sampled & window).sum()) / total) if total else None,
        "aligned_count_strict": int((sampled & flag_agent).sum()),
        "aligned_fraction_strict": (
            float((sampled & flag_agent).sum()) / total) if total else None,
        "flag_up_steps_per_agent_step": float(flag_agent.mean()),
        "window_steps_per_agent_step": float(window.mean()),
    }


def interruption_record(rollout_index, arm, seed, sampled, agent_cause, team_cause,
                        change_flag, region_of_agent, segment_lengths_agent,
                        segment_lengths_team, k_max) -> dict:
    """Contract section 3 item 2, per rollout."""
    sampled = np.asarray(sampled, dtype=bool)
    agent_cause = np.asarray(agent_cause, dtype=np.int64)
    team_cause = np.asarray(team_cause, dtype=np.int64)
    steps, lanes, agents = sampled.shape
    agent_steps = steps * lanes * agents

    cause_counts = {name: int((agent_cause == code).sum())
                    for code, name in CAUSE_NAMES.items()}
    sampled_cause_counts = {name: int((sampled & (agent_cause == code)).sum())
                            for code, name in CAUSE_NAMES.items()}
    total = int(sampled.sum())
    cap_closed = sampled_cause_counts["cap"] + sampled_cause_counts["team_cap"]
    gap_closed = sampled_cause_counts["gap"] + sampled_cause_counts["team_gap"]

    gap_only = sampled & ((agent_cause == CAUSE_GAP) | (agent_cause == CAUSE_TEAM_GAP))
    alignment = event_alignment(sampled, change_flag, region_of_agent)
    alignment_gap_only = event_alignment(gap_only, change_flag, region_of_agent)

    lengths = np.asarray(segment_lengths_agent, dtype=np.float64)
    team_lengths = np.asarray(segment_lengths_team, dtype=np.float64)
    return {
        "rollout": int(rollout_index),
        "arm": arm,
        "seed": int(seed),
        "steps": int(steps),
        "lanes": int(lanes),
        "agents": int(agents),
        "agent_steps": int(agent_steps),
        "interruptions": total,
        "interruption_rate_per_agent_step": float(total) / float(agent_steps),
        "team_decision_steps": int((team_cause != CAUSE_NONE).sum()),
        "team_switch_count_gap": int((team_cause == CAUSE_TEAM_GAP).sum()),
        "team_switch_rate_gap_per_env_step": float(
            (team_cause == CAUSE_TEAM_GAP).sum()) / float(steps * lanes),
        "team_cap_count": int((team_cause == CAUSE_TEAM_CAP).sum()),
        "team_reset_count": int((team_cause == CAUSE_RESET).sum()),
        "cause_counts_all_positions": cause_counts,
        "cause_counts_sampled_positions": sampled_cause_counts,
        "fraction_closed_by_cap": (float(cap_closed) / total) if total else None,
        "fraction_closed_by_gap": (float(gap_closed) / total) if total else None,
        "k_max": int(k_max),
        "event_alignment": alignment,
        "event_alignment_gap_caused_only": alignment_gap_only,
        "segment_length_agent": decile_summary(lengths),
        "segment_length_team": decile_summary(team_lengths),
    }


def gap_record(rollout_index, arm, seed, gap_agent, gap_team) -> dict:
    """Contract section 3 item 3, per rollout: deciles of `g_i` and `g_Z` at every step."""
    return {
        "rollout": int(rollout_index),
        "arm": arm,
        "seed": int(seed),
        "gap_agent": decile_summary(gap_agent),
        "gap_team": decile_summary(gap_team),
        "note": (
            "g_i and g_Z at every step (not only at interruptions). Steps whose "
            "boundary cause is `reset` carry no gap (the coordinator is not "
            "evaluated there) and are excluded as non-finite."
        ),
    }


# ---------------------------------------------------------------------------
# The instrumented driver
# ---------------------------------------------------------------------------


class DriverRecorder:
    """Capture the per-step quantities `run_rollout` does not return.

    Three bound methods on the instances this runner owns are wrapped; nothing in
    `envs/` or `hmasd/` is edited.

    * `adapter.step` - called once per step, **after** `agent.step`, so the agent's
      `_d2_last_step` still holds this step's gaps, sampled mask and causes; the
      host's `info['change_flag']` is the flag visible at the same step.
    * `agent.get_d2_metrics` - called by the driver after `agent.update()` and
      before `clear_buffers()`; the raw segment-length lists are snapshotted there
      because `clear_buffers` drops them.
    * `agent.update` - wrapped only to keep its returned loss dict, which
      `run_rollout` does not pass back.
    """

    def __init__(self, driver: RelayCorridorHMASDDriver) -> None:
        self.driver = driver
        self.agent = driver.agent
        self.adapter = driver.adapter
        self._adapter_step = driver.adapter.step
        self._get_d2_metrics = driver.agent.get_d2_metrics
        self._update = driver.agent.update
        driver.adapter.step = self._wrapped_adapter_step
        driver.agent.get_d2_metrics = self._wrapped_get_d2_metrics
        driver.agent.update = self._wrapped_update
        self.reset_rollout()

    # -- lifecycle ------------------------------------------------------
    def reset_rollout(self) -> None:
        self.gap_agent = []
        self.gap_team = []
        self.agent_cause = []
        self.team_cause = []
        self.sampled = []
        self.change_flag = []
        self.raw_segments = {"segment_lengths_agent": [], "segment_lengths_team": []}
        self.update_info = None

    def stacked(self) -> dict:
        return {
            "gap_agent": np.asarray(self.gap_agent, dtype=np.float64),
            "gap_team": np.asarray(self.gap_team, dtype=np.float64),
            "agent_cause": np.asarray(self.agent_cause, dtype=np.int64),
            "team_cause": np.asarray(self.team_cause, dtype=np.int64),
            "sampled": np.asarray(self.sampled, dtype=bool),
            "change_flag": np.asarray(self.change_flag, dtype=np.int64),
        }

    # -- wrappers -------------------------------------------------------
    def _wrapped_adapter_step(self, actions, renew_mask=None, **kwargs):
        last = self.agent._d2_last_step
        if last is not None:
            self.gap_agent.append(np.array(last["g_agents"], dtype=np.float64))
            self.gap_team.append(np.array(last["g_team"], dtype=np.float64))
            self.agent_cause.append(np.array(last["agent_cause"], dtype=np.int64))
            self.team_cause.append(np.array(last["team_cause"], dtype=np.int64))
            self.sampled.append(np.array(last["sampled_mask"], dtype=bool))
        out = self._adapter_step(actions, renew_mask=renew_mask, **kwargs)
        info = out[4]
        self.change_flag.append(np.asarray(info["change_flag"], dtype=np.int64).copy())
        return out

    def _wrapped_get_d2_metrics(self):
        raw = self.agent.d2_metrics
        if raw is not None:
            self.raw_segments = {
                "segment_lengths_agent": [int(v) for v in raw["segment_lengths_agent"]],
                "segment_lengths_team": [int(v) for v in raw["segment_lengths_team"]],
            }
        return self._get_d2_metrics()

    def _wrapped_update(self, *args, **kwargs):
        info = self._update(*args, **kwargs)
        self.update_info = info
        return info


# ---------------------------------------------------------------------------
# Evaluation on the matched tapes (contract section 3 item 1)
# ---------------------------------------------------------------------------


def eval_episode_ids(episodes: int):
    return list(range(int(episodes)))


def tape_digest_and_events(corridor: RelayCorridorConfig, master_seed: int,
                           episodes: int, chunk: int) -> dict:
    """Digest of the matched evaluation tapes and their per-episode event counts.

    The tapes are the host's keyed streams: they depend on `(master seed, episode
    id)` alone, so every arm, seed and checkpoint that uses the same evaluation
    master seed and the same episode ids runs the *same* 4,096 episodes.  The
    digest is taken chunk by chunk in ascending episode order over the four named
    tape arrays, using the E0 `_sha256_arrays` recipe per chunk and hashing the
    chunk digests in order.
    """
    from envs.relay_corridor.host import RelayCorridorHost

    outer = hashlib.sha256()
    counts = []
    per_region = []
    for start in range(0, int(episodes), int(chunk)):
        ids = list(range(start, min(start + int(chunk), int(episodes))))
        host = RelayCorridorHost(corridor, batch_size=len(ids),
                                 master_seed=int(master_seed), episode_ids=ids)
        tapes = host.stream_tapes()
        outer.update(_sha256_arrays(tapes).encode("utf-8"))
        # Event realisations are a deterministic function of the tape: one draw per
        # region per transition against the (constant) Bernoulli hazard.
        hazard = np.asarray([law.hazard_table(1)[0] for law in corridor.region_laws()],
                            dtype=np.float64)
        events = tapes["event_u"] < hazard[None, :, None]      # [B, R, H]
        events = events[:, :, : corridor.horizon - 1]          # H - 1 transitions
        per_region.append(events.sum(axis=2))
        counts.append(events.sum(axis=(1, 2)))
    counts = np.concatenate(counts).astype(np.int64)
    per_region = np.concatenate(per_region, axis=0).astype(np.int64)
    return {
        "episodes": int(episodes),
        "master_seed": int(master_seed),
        "episode_ids": f"0..{int(episodes) - 1}",
        "chunk": int(chunk),
        "content_sha256": outer.hexdigest(),
        "digest_recipe": (
            "for each ascending chunk of episode ids: E0 `_sha256_arrays` over the "
            "host's four keyed tape arrays (theta0, event_u, switch_u, role0); the "
            "chunk hex digests are then fed, in order, into one outer sha256."
        ),
        "event_counts": counts,
        "event_counts_per_region": per_region,
        "event_count_median": float(np.median(counts)),
        "event_count_mean": float(counts.mean()),
        "event_count_min": int(counts.min()),
        "event_count_max": int(counts.max()),
    }


class CorridorEvaluator:
    """Deterministic evaluation on the matched tapes, on its own agent instance.

    The E0 mechanism: a second `HMASDAgent`, weight- and normaliser-synced from the
    learner before each evaluation, held in `train(False)`, constructed and run
    inside `_preserve_rng`, so the learner's RNG and per-lane state are untouched.
    The policy is deterministic: `agent.step(deterministic=True)` gives the greedy
    coordinator and the mean low-level action, and the host decodes the role by
    `argmax` (ADR 02 `role_decode = argmax`).
    """

    def __init__(self, corridor: RelayCorridorConfig, overrides: dict, *, chunk: int,
                 master_seed: int, log_dir: Path, seed: int) -> None:
        self.corridor = corridor
        self.chunk = int(chunk)
        self.master_seed = int(master_seed)
        self.horizon = int(corridor.horizon)
        self.adapter = RelayCorridorAdapter(
            corridor, num_envs=self.chunk, master_seed=self.master_seed,
            episode_ids=list(range(self.chunk)), squeeze_batch=False,
        )
        self.config = build_corridor_learner_config(
            corridor, self.adapter, mode="d2", num_envs=self.chunk,
            rollout_length=self.horizon, k=int(overrides["skill_cap_k_max"]),
            seed=int(seed), overrides=dict(overrides),
        )
        self.config.__class__ = E2CorridorConfig
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        self.agent = HMASDAgent(self.config, log_dir=str(log_dir), device=torch.device("cpu"))
        self.agent.train(False)
        self.count = 0

    # -- sync (E0 `Evaluator._sync`) -------------------------------------
    def _sync(self, learner) -> None:
        self.agent.skill_coordinator.load_state_dict(learner.skill_coordinator.state_dict())
        self.agent.skill_discoverer.load_state_dict(learner.skill_discoverer.state_dict())
        if learner.team_discriminator is not None and self.agent.team_discriminator is not None:
            self.agent.team_discriminator.load_state_dict(
                learner.team_discriminator.state_dict())
        if (learner.individual_discriminator is not None
                and self.agent.individual_discriminator is not None):
            self.agent.individual_discriminator.load_state_dict(
                learner.individual_discriminator.state_dict())
        self.agent.obs_norm = copy.deepcopy(learner.obs_norm)
        self.agent.state_norm = copy.deepcopy(learner.state_norm)
        self.agent.value_norm_coordinator = copy.deepcopy(learner.value_norm_coordinator)
        self.agent.value_norm_discoverer = copy.deepcopy(learner.value_norm_discoverer)
        self.agent.train(False)

    def _reset_lanes(self) -> None:
        self.agent.clear_buffers()
        for lane in range(self.chunk):
            self.agent.reset_env_state(lane)

    # -- one evaluation ---------------------------------------------------
    def run(self, learner, episodes: int, tape_events: np.ndarray, references: dict,
            rollout_index: int) -> dict:
        self._sync(learner)
        episodes = int(episodes)
        started = time.perf_counter()
        returns = np.zeros(episodes, dtype=np.float64)
        renew_fraction = np.zeros(episodes, dtype=np.float64)
        service = np.zeros(episodes, dtype=np.float64)
        for start in range(0, episodes, self.chunk):
            ids = list(range(start, min(start + self.chunk, episodes)))
            lanes = len(ids)
            self.adapter._episode_ids = list(ids) + list(
                range(episodes, episodes + self.chunk - lanes))
            observations, info = self.adapter.reset()
            self._reset_lanes()
            observations = np.asarray(observations, dtype=np.float32)
            states = np.asarray(info["state"], dtype=np.float64)
            env_steps = np.zeros(self.chunk, dtype=int)
            dones_tracker = np.zeros(self.chunk, dtype=bool)
            reward_sum = np.zeros(self.chunk, dtype=np.float64)
            renew_sum = np.zeros(self.chunk, dtype=np.float64)
            service_sum = np.zeros(self.chunk, dtype=np.float64)
            for _t in range(self.horizon):
                actions, _infos, step_data = self.agent.step(
                    states, observations, env_steps, dones_tracker,
                    deterministic=True, return_step_data=True, build_infos=False,
                )
                renew = np.asarray(step_data["d2_sampled_mask"], dtype=bool)
                next_observations, _reward, _terminated, _truncated, step_info = (
                    self.adapter.step(np.asarray(actions), renew_mask=renew))
                reward_sum += np.asarray(step_info["shared_reward"],
                                         dtype=np.float64).reshape(self.chunk)
                renew_sum += renew.mean(axis=1)
                service_sum += np.asarray(
                    step_info["service_indicators"], dtype=np.float64).mean(axis=1)
                observations = np.asarray(next_observations, dtype=np.float32)
                states = np.asarray(step_info["state"], dtype=np.float64)
                env_steps += 1
            returns[start:start + lanes] = reward_sum[:lanes] / float(self.horizon)
            renew_fraction[start:start + lanes] = renew_sum[:lanes] / float(self.horizon)
            service[start:start + lanes] = service_sum[:lanes] / float(self.horizon)

        self.count += 1
        events = np.asarray(tape_events, dtype=np.int64)[:episodes]
        median = float(np.median(events))
        low = events <= median
        high = events > median
        mean = float(returns.mean())
        std = float(returns.std(ddof=1)) if episodes > 1 else 0.0
        return {
            "evaluation_index": self.count,
            "rollout": int(rollout_index),
            "episodes": episodes,
            "eval_master_seed": self.master_seed,
            "episode_ids": f"0..{episodes - 1}",
            "return_definition": (
                "mean per-step shared reward over one 400-step episode, so it is on "
                "the same scale as the exact references J (both are Delta-weighted "
                "mean per-step service fractions)"),
            "return_mean": mean,
            "return_std": std,
            "return_stderr": (std / math.sqrt(episodes)) if episodes > 1 else 0.0,
            "return_min": float(returns.min()),
            "return_max": float(returns.max()),
            "gap_to_J_switch": float(references["J_switch"]) - mean,
            "gap_to_J_best_fixed_k": float(references["J_best_fixed_k"]) - mean,
            "J_switch": float(references["J_switch"]),
            "J_best_fixed_k": float(references["J_best_fixed_k"]),
            "best_fixed_k": int(references["best_fixed_k"]),
            "mean_renew_fraction": float(renew_fraction.mean()),
            "mean_service_fraction": float(service.mean()),
            "event_count_median": median,
            "regime_low_events": {
                "episodes": int(low.sum()),
                "return_mean": float(returns[low].mean()) if low.any() else None,
                "return_stderr": (
                    float(returns[low].std(ddof=1) / math.sqrt(int(low.sum())))
                    if int(low.sum()) > 1 else None),
            },
            "regime_high_events": {
                "episodes": int(high.sum()),
                "return_mean": float(returns[high].mean()) if high.any() else None,
                "return_stderr": (
                    float(returns[high].std(ddof=1) / math.sqrt(int(high.sum())))
                    if int(high.sum()) > 1 else None),
            },
            "wall_seconds": float(time.perf_counter() - started),
        }


# ---------------------------------------------------------------------------
# the run
# ---------------------------------------------------------------------------


CONFIG_DUMP_FIELDS = e0.CONFIG_DUMP_FIELDS
LOSS_FIELDS = e0.LOSS_FIELDS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="E2 interruption-cost sweep runner")
    parser.add_argument("--arm", choices=tuple(ARM_ORDER), required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--rollouts", type=int, default=20)
    parser.add_argument("--num-envs", type=int, default=16)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--launch-commit", required=True,
                        help="the commit that carries this runner (contract section 1)")
    parser.add_argument("--eval-interval", type=int, default=5)
    parser.add_argument("--eval-tape-set", type=int, default=4096,
                        help="the declared matched tape set (contract section 3): episode "
                             "ids 0..N-1 at --eval-master-seed. Its digest and per-episode "
                             "event counts are recorded whatever is evaluated")
    parser.add_argument("--eval-episodes", type=int, default=4096,
                        help="tapes evaluated at the final checkpoint: the first N of the "
                             "declared set. Below --eval-tape-set this is a recorded deviation")
    parser.add_argument("--eval-intermediate-episodes", type=int, default=4096,
                        help="tapes evaluated at the intermediate checkpoints: the first N "
                             "of the same declared set. Below --eval-episodes this is a "
                             "recorded deviation")
    parser.add_argument("--eval-chunk", type=int, default=512)
    parser.add_argument("--eval-master-seed", type=int, default=770001)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--timing-only", action="store_true",
                        help="timing run: one rollout, no evaluation, no checkpoint; "
                             "NOT EVIDENCE")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    run_name = args.run_name or f"{args.arm}_seed{args.seed}"
    run_dir = Path(args.output_root).resolve() / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    try:
        return _execute(args, run_dir)
    except BaseException:  # noqa: BLE001 - every failure quarantines the arm
        text = traceback.format_exc()
        (run_dir / "QUARANTINED").write_text(
            "This arm-seed is an incomplete attempt (contract section 4.3).\n"
            "It yields no observation. No interpretation, no resume, no salvage.\n\n"
            f"time: {_utc_now()}\n\n{text}",
            encoding="utf-8",
        )
        sys.stderr.write(text)
        return 2


def _execute(args, run_dir: Path) -> int:
    # 1. resource preflight, before any RNG master, model, optimizer or result exists
    preflight = run_preflight(run_dir)

    torch.set_num_threads(int(args.threads))
    started_wall = time.perf_counter()
    started_at = _utc_now()

    arm = args.arm
    overrides = arm_parameters(arm)
    rollouts = int(args.rollouts) if not args.timing_only else 1
    num_envs = int(args.num_envs)

    corridor = corridor_config()
    horizon = int(corridor.horizon)
    horizon_record = validate_horizon(corridor, mode="d0_fixed_k")

    # 2. exact references for this host point, before the first run
    references = enumerate_references(corridor)
    reference_record = references.as_dict()

    # 3. the matched evaluation tapes (digest and per-episode event counts)
    if int(args.eval_episodes) > int(args.eval_tape_set):
        raise ValueError("--eval-episodes cannot exceed --eval-tape-set")
    if int(args.eval_intermediate_episodes) > int(args.eval_episodes):
        raise ValueError("--eval-intermediate-episodes cannot exceed --eval-episodes")
    tape_record = None
    if not args.timing_only:
        tape_record = tape_digest_and_events(
            corridor, int(args.eval_master_seed), int(args.eval_tape_set),
            int(args.eval_chunk))

    # 4. learner
    driver = RelayCorridorHMASDDriver(
        corridor,
        mode="d2",
        num_envs=num_envs,
        rollout_length=horizon,
        k=int(overrides["skill_cap_k_max"]),
        master_seed=int(args.seed),
        seed=int(args.seed),
        log_dir=str(run_dir / "logs"),
        device=torch.device("cpu"),
        config_overrides=dict(overrides),
    )
    # `RelayCorridorHMASDDriver.__init__` pins one torch thread; the contract runs at
    # four.  Restored here, after construction, so the thread count is the run's.
    torch.set_num_threads(int(args.threads))
    driver.config.__class__ = E2CorridorConfig
    config = driver.config
    agent = driver.agent
    recorder = DriverRecorder(driver)
    theta0 = e0._capture_theta0(agent)

    counters = {
        "coordinator": e0._StepCounter(agent.coordinator_optimizer),
        "discoverer_actor": e0._StepCounter(agent.discoverer_actor_optimizer),
        "discoverer_critic": e0._StepCounter(agent.discoverer_critic_optimizer),
    }
    if agent.team_discriminator_optimizer is not None:
        counters["team_discriminator"] = e0._StepCounter(agent.team_discriminator_optimizer)
    if agent.individual_discriminator_optimizer is not None:
        counters["individual_discriminator"] = e0._StepCounter(
            agent.individual_discriminator_optimizer)

    evaluator = None
    if not args.timing_only:
        with _preserve_rng():
            evaluator = CorridorEvaluator(
                corridor, overrides, chunk=int(args.eval_chunk),
                master_seed=int(args.eval_master_seed),
                log_dir=run_dir / "eval_logs", seed=int(args.seed))

    # 5. manifest
    manifest = {
        "schema_version": 1,
        "contract": CONTRACT,
        "claim_ceiling": "B (EXPLORE)",
        "runner": "scripts/run_flexible_skill_duration_e2.py",
        "launch_commit": str(args.launch_commit),
        "arm": arm,
        "arm_family": ARMS[arm]["family"],
        "arm_parameters": overrides,
        "arm_grid_point": {"k": ARMS[arm]["k"], "c": ARMS[arm]["c"]},
        "seed": int(args.seed),
        "rollouts": rollouts,
        "timing_only": bool(args.timing_only),
        "code_sha": _git("rev-parse", "HEAD"),
        "code_branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "code_dirty": bool(_git("status", "--porcelain")),
        "command": list(sys.argv),
        "host_point": corridor.parameter_record(),
        "host_horizon_validation": horizon_record,
        "references": reference_record,
        "reference_note": (
            "computed by envs.relay_corridor.references.enumerate_references on this "
            "host point before the first rollout; references, not outcomes"),
        "config": {name: _jsonable(getattr(config, name, None))
                   for name in CONFIG_DUMP_FIELDS},
        "env": {
            "host": "envs.relay_corridor.host.RelayCorridorHost",
            "adapter": "envs.relay_corridor.adapter.RelayCorridorAdapter",
            "driver": "envs.relay_corridor.hmasd_driver.RelayCorridorHMASDDriver",
            "num_envs": num_envs,
            "rollout_length": horizon,
            "episode_length": horizon,
            "master_seed": int(args.seed),
            "state_dim": int(driver.adapter.state_dim),
            "obs_dim": int(driver.adapter.obs_dim),
        },
        "evaluation": None if args.timing_only else {
            "declared_tape_set": int(args.eval_tape_set),
            "episodes": int(args.eval_episodes),
            "intermediate_episodes": int(args.eval_intermediate_episodes),
            "reduced_from_contract": bool(int(args.eval_episodes) < 4096
                                          or int(args.eval_intermediate_episodes) < 4096),
            "chunk": int(args.eval_chunk),
            "master_seed": int(args.eval_master_seed),
            "interval_rollouts": int(args.eval_interval),
            "deterministic": True,
            "tapes": {k: v for k, v in tape_record.items()
                      if k not in ("event_counts", "event_counts_per_region")},
        },
        "machine": {
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "python": sys.version.split()[0],
            "executable": sys.executable,
        },
        "versions": {"torch": torch.__version__, "numpy": np.__version__},
        "torch_num_threads": int(torch.get_num_threads()),
        "device": "cpu",
        "preflight": preflight,
        "started_at": started_at,
        "ended_at": None,
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(_jsonable(manifest), indent=2, ensure_ascii=False), encoding="utf-8")

    metrics_path = run_dir / "metrics.jsonl"
    eval_path = run_dir / "eval.jsonl"
    interruptions_path = run_dir / "interruptions.jsonl"
    gaps_path = run_dir / "gaps.jsonl"
    for path in (metrics_path, eval_path, interruptions_path, gaps_path):
        path.write_text("", encoding="utf-8")

    tape_events = (tape_record["event_counts"] if tape_record is not None
                   else np.zeros(0, dtype=np.int64))

    rollout_rows = []
    evaluations = []
    instability = None
    cumulative_transitions = 0
    cumulative_episodes = 0

    for rollout_index in range(1, rollouts + 1):
        recorder.reset_rollout()
        before_counts = {name: counter.count for name, counter in counters.items()}
        started_rollout = time.perf_counter()
        summary = driver.run_rollout(update=True)
        rollout_seconds = time.perf_counter() - started_rollout
        captured = recorder.stacked()

        d2_metrics = summary.get("d2_metrics")
        rows_M = int(d2_metrics["rows_M"]) if d2_metrics else 0
        rewards = np.asarray(summary["rewards"], dtype=np.float64)   # [T, B]
        episode_returns = rewards.mean(axis=0)                       # one episode per lane
        cumulative_transitions += horizon * num_envs
        cumulative_episodes += num_envs

        exposure = e0._exposure_line(agent, theta0)
        losses = {}
        if isinstance(recorder.update_info, dict):
            for key in LOSS_FIELDS:
                if key in recorder.update_info:
                    losses[key] = _jsonable(recorder.update_info[key])
        non_finite = [name for name, value in losses.items()
                      if isinstance(value, str) and value in ("NaN", "Infinity", "-Infinity")]
        mean_return = float(episode_returns.mean())
        if not math.isfinite(mean_return):
            non_finite.append("episode_return")

        if rollout_index == 1:
            np.savez(
                run_dir / "rollout1_match.npz",
                sampled=captured["sampled"],
                roles=np.asarray(summary["roles"], dtype=np.int64),
                rewards=rewards,
                service=np.asarray(summary["service_indicators"], dtype=bool),
                gap_agent=captured["gap_agent"],
                gap_team=captured["gap_team"],
                agent_cause=captured["agent_cause"],
                change_flag=captured["change_flag"],
            )

        row = {
            "rollout": rollout_index,
            "arm": arm,
            "seed": int(args.seed),
            "transitions_this_rollout": horizon * num_envs,
            "transitions_cumulative": cumulative_transitions,
            "episodes_this_rollout": num_envs,
            "episodes_cumulative": cumulative_episodes,
            "optimizer_steps_cumulative": {n: c.count for n, c in counters.items()},
            "optimizer_steps_this_rollout": {
                n: c.count - before_counts[n] for n, c in counters.items()},
            "rows_M": rows_M,
            "rows_M_agent": int(d2_metrics["rows_M_agent"]) if d2_metrics else 0,
            "rows_M_team": int(d2_metrics["rows_M_team"]) if d2_metrics else 0,
            "mean_episode_return": mean_return,
            "episode_returns": [float(v) for v in episode_returns],
            "mean_shared_reward": float(summary["mean_shared_reward"]),
            "service_rate_per_agent": [float(v) for v in summary["service_rate_per_agent"]],
            "renew_fraction": float(summary["renew_fraction"]),
            "exposure_line": exposure,
            "losses": losses,
            "rollout_wall_seconds": rollout_seconds,
            "d2_metrics": _jsonable(d2_metrics) if d2_metrics is not None else None,
            "evaluation": None,
        }

        if non_finite:
            instability = {"kind": "non-finite loss or return",
                           "rollout": rollout_index, "fields": non_finite}

        interruptions = interruption_record(
            rollout_index, arm, int(args.seed), captured["sampled"],
            captured["agent_cause"], captured["team_cause"], captured["change_flag"],
            corridor.region_of_agent, recorder.raw_segments["segment_lengths_agent"],
            recorder.raw_segments["segment_lengths_team"],
            int(overrides["skill_cap_k_max"]))
        gaps = gap_record(rollout_index, arm, int(args.seed),
                          captured["gap_agent"], captured["gap_team"])
        with open(interruptions_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(_jsonable(interruptions), ensure_ascii=False) + "\n")
        with open(gaps_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(_jsonable(gaps), ensure_ascii=False) + "\n")

        do_eval = evaluator is not None and (
            rollout_index % int(args.eval_interval) == 0
            or rollout_index == rollouts
            or instability is not None)
        if do_eval:
            final = (rollout_index == rollouts) or (instability is not None)
            episodes = int(args.eval_episodes if final
                           else args.eval_intermediate_episodes)
            with _preserve_rng():
                evaluation = evaluator.run(agent, episodes, tape_events,
                                           reference_record, rollout_index)
            evaluation["final_checkpoint"] = bool(final)
            row["evaluation"] = evaluation
            evaluations.append(evaluation)
            with open(eval_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(_jsonable(evaluation), ensure_ascii=False) + "\n")

        rollout_rows.append(row)
        with open(metrics_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(_jsonable(row), ensure_ascii=False) + "\n")

        if instability is not None:
            break

    checkpoint_path = None
    if not args.timing_only:
        checkpoint_path = run_dir / "checkpoint_final.pt"
        agent.save_model(str(checkpoint_path))

    ended_at = _utc_now()
    total_seconds = time.perf_counter() - started_wall
    manifest["ended_at"] = ended_at
    manifest["wall_seconds"] = total_seconds
    (run_dir / "manifest.json").write_text(
        json.dumps(_jsonable(manifest), indent=2, ensure_ascii=False), encoding="utf-8")

    completed = instability is None and len(rollout_rows) == rollouts
    final_eval = None
    for evaluation in evaluations:
        if evaluation.get("final_checkpoint"):
            final_eval = evaluation
    last_interruption = None
    if interruptions_path.exists():
        lines = [line for line in
                 interruptions_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            last_interruption = json.loads(lines[-1])

    summary_payload = {
        "schema_version": 1,
        "contract": CONTRACT,
        "arm": arm,
        "arm_family": ARMS[arm]["family"],
        "arm_grid_point": {"k": ARMS[arm]["k"], "c": ARMS[arm]["c"]},
        "arm_parameters": overrides,
        "seed": int(args.seed),
        "launch_commit": str(args.launch_commit),
        "code_sha": manifest["code_sha"],
        "rollouts_requested": rollouts,
        "rollouts_completed": len(rollout_rows),
        "completed": completed,
        "timing_only": bool(args.timing_only),
        "instability": instability,
        "num_envs": num_envs,
        "rollout_length": horizon,
        "transitions_total": cumulative_transitions,
        "episodes_total": cumulative_episodes,
        "optimizer_steps_total": {n: c.count for n, c in counters.items()},
        "references": reference_record,
        "evaluation_count": len(evaluations),
        "evaluations": evaluations,
        "final_evaluation": final_eval,
        "final_evaluation_return_mean": final_eval["return_mean"] if final_eval else None,
        "final_evaluation_return_stderr": (
            final_eval["return_stderr"] if final_eval else None),
        "final_interruption_record": last_interruption,
        "rows_M_per_rollout": [r["rows_M"] for r in rollout_rows],
        "mean_episode_return_per_rollout": [r["mean_episode_return"] for r in rollout_rows],
        "rollout_wall_seconds": [r["rollout_wall_seconds"] for r in rollout_rows],
        "wall_seconds_total": total_seconds,
        "seconds_per_rollout_mean": (
            float(np.mean([r["rollout_wall_seconds"] for r in rollout_rows]))
            if rollout_rows else None),
        "exposure_line_rollout_1": rollout_rows[0]["exposure_line"] if rollout_rows else None,
        "exposure_line_rollout_last": rollout_rows[-1]["exposure_line"] if rollout_rows else None,
        "torch_num_threads": int(torch.get_num_threads()),
        "checkpoint": str(checkpoint_path) if checkpoint_path else None,
        "started_at": started_at,
        "ended_at": ended_at,
    }
    (run_dir / "summary.json").write_text(
        json.dumps(_jsonable(summary_payload), indent=2, ensure_ascii=False),
        encoding="utf-8")

    if not completed:
        (run_dir / "QUARANTINED").write_text(
            "This arm-seed is an incomplete attempt (contract section 4.3).\n"
            "It yields no observation. No interpretation, no resume, no salvage.\n\n"
            f"time: {ended_at}\ninstability: {json.dumps(_jsonable(instability))}\n"
            f"rollouts completed: {len(rollout_rows)} of {rollouts}\n",
            encoding="utf-8")

    print(json.dumps(_jsonable({
        "arm": arm,
        "seed": int(args.seed),
        "completed": completed,
        "rollouts_completed": len(rollout_rows),
        "transitions_total": cumulative_transitions,
        "episodes_total": cumulative_episodes,
        "optimizer_steps_total": summary_payload["optimizer_steps_total"],
        "evaluation_count": len(evaluations),
        "final_evaluation_return_mean": summary_payload["final_evaluation_return_mean"],
        "final_evaluation_return_stderr": summary_payload["final_evaluation_return_stderr"],
        "event_alignment_fraction_last_rollout": (
            last_interruption["event_alignment"]["aligned_fraction"]
            if last_interruption else None),
        "segment_length_agent_mean_last_rollout": (
            last_interruption["segment_length_agent"]["mean"]
            if last_interruption else None),
        "interruption_rate_per_agent_step_last_rollout": (
            last_interruption["interruption_rate_per_agent_step"]
            if last_interruption else None),
        "wall_seconds_total": total_seconds,
        "seconds_per_rollout_mean": summary_payload["seconds_per_rollout_mean"],
        "run_dir": str(run_dir),
    }), ensure_ascii=False))
    return 0 if completed else 3


if __name__ == "__main__":
    raise SystemExit(main())
