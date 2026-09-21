"""FSD coordinator signal B11: does the coordinator's own learning signal rank the labels?

Exploration, next research judgment in the direction notebook:
docs/research/candidates/flexible_skill_duration/NOTES.md (2026-09-20 16:40 PDT, next research
judgment, B11).

B09 measured, at the trained D1280's fixed weights, what each *constant* agent label scores when
every agent holds it for a whole episode (mean actions); B10 repeated that with the low level's
action *sampled* as training executes it and found the gaps compressed by about 40 % but neither
erased nor reordered.  Both are joint, 500-step, all-six-agents interventions.  The coordinator
never sees that experiment.  What it sees is its own PPO signal: one advantage per (decision,
agent) over a ten-step segment whose reward is the team's, against a label-free baseline.  B11 asks
the one question those two panels cannot answer: **at the same saved weights, does the
coordinator's own advantage estimate - computed exactly as `update_coordinator_d2` computes it -
rank the six agent labels the way the fixed-weight label maps do?**

Two commands, both at fixed weights, both taking no optimizer step, neither of them a fit.

`probe` runs, per block:

  (a) the frozen `as_trained` panel and B08/B09's faithful-load check, by exact equality of the 32
      native world scores with the recorded rollout-45 panel; the probe stops there if it fails and
      the check is never relaxed;
  (b) four training-law rollouts of the frozen collector's own per-step calls - `agent.step(...,
      deterministic=False, return_step_data=True, build_infos=False)`, `env.step`,
      `agent.store_transition_batch(...)`, `agent.reset_env_state(lane)` - with **no update**, and
      after each rollout the coordinator's own credit arithmetic: the bootstrap block of
      `HMASDAgent.update`, `_d2_flush_open_segments`, `compute_high_level_advantages` and
      `get_d2_tables`, with the same arguments the update passes, followed by the frozen
      `clear_buffers` the fit's loop calls at the same place.

`update_coordinator_d2` is never called: it takes optimizer steps and it updates
`value_norm_coordinator`.  Every optimizer `step` of both agents raises for the whole command
(`run_fsd_flat_input_scale_b05._forbid_optimizer_steps`), and the probe hashes the coordinator, the
discoverer, both discriminators and both value normalisers before and after the whole run.

The measures, per block, pooled over the rollouts and per rollout:

  (a) the agent-label table: count, share, mean raw advantage with an iid and a lane-clustered
      standard error, mean segment return, mean stored value, and the mean *standardised* advantage
      (standardised per rollout with the one shared team+agent mean and standard deviation the
      update computes for that rollout's single minibatch, hmasd/agent.py:6153-6164);
  (b) the team-label table, which is a placebo row: the team label never reaches the low-level
      actor (hmasd/networks.py:1801-1809);
  (c) the between-label spread of the mean raw advantage, its lane-cluster bootstrap standard error
      and percentile interval, and eta^2;
  (d) a *perfect-credit reference*: the segment-level additive regression of each team segment's
      discounted reward on the six counts of agents holding each label, with and without the
      segment's stored team value as a state control.  It asks whether a label effect is detectable
      at the ten-step decision level *at all*, given perfect per-agent credit; it is not the
      coordinator's signal and is labelled so everywhere;
  (e) the executed label law: the shares, and the mean of -log q of the chosen label, which is an
      unbiased estimate of the law's conditional entropy, beside ln 6;
  (f) descriptive, approximate: the per-label policy-gradient pull at the logit level for one PPO
      step at ratio 1, beside `lambda_h` and the entropy gap to ln 6.

The collection worlds are not the fit's.  The fit's own training stream is long gone, so this
object seeds its collection from a dedicated derivation - `sha256(f"{training_seed}:b11:rollout{r}")`
for the Python, NumPy and torch streams of rollout r, and sixteen lanes seeded
`training_seed + 500 + rank` in the way `run_fit` seeds its lanes - and saves and restores the
global streams around the whole collection.  A block's collection is therefore a function of
(block, rollout count) alone, and it cannot move the `as_trained` panel.

`reduce` is a pure reading of published summaries and carries no admission.  It reads this object's
three probes beside B09's and B10's probes of the same three checkpoints and refuses a block whose
weights sha256 or `as_trained` world scores do not agree with both.
"""
import argparse
import hashlib
import inspect
import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import run_fsd_baseline_interruption_b01 as b01
import run_fsd_label_content_b08 as b08
import run_fsd_label_map_b09 as b09
import run_fsd_label_map_sampled_b10 as b10

shared = b09.shared
DIRECTION = "flexible_skill_duration"
OBJECT_ID = "FSD_COORDINATOR_SIGNAL_B11"
CARD = ("docs/research/candidates/flexible_skill_duration/NOTES.md "
        "(2026-09-20 16:40 PDT, next research judgment, B11)")
BLOCKS = dict(b09.BLOCKS)  # 772803, 772903, 773003
SAVE_ARM = b09.SAVE_ARM  # the recorded stage-1 D1280 construction, unchanged
BASELINE_RULE = b09.BASELINE_RULE  # "as_trained"
N_LABELS = b09.N_LABELS  # 6; `run_probe` refuses any other width
WEIGHTS_NAME = b09.WEIGHTS_NAME
SIDECAR_NAME = b09.SIDECAR_NAME
ROLLOUTS = 4  # the notebook entry's four training-law rollouts; `--rollouts` records what ran
# The collection lanes are the fit's own sixteen, seeded from a base this far above the block's
# training seed, so the worlds are not the fit's first rollout and collide with no other block's
# training lanes (which span `seed .. seed + 15`) or evaluation lanes (which are in the 78xxxx range).
WORLD_SEED_OFFSET = 500
BOOTSTRAP_RESAMPLES = 1000
BOOTSTRAP_INTERVAL = (2.5, 97.5)
SPREAD_MULTIPLE = 2.  # the notebook's "twice its standard error"
SKILL_PERIOD = b08.SKILL_PERIOD  # 10: the frozen caps cadence, and the expected segment length
CAUSES_EXPECTED = ("reset", "team_cap")  # every other D2 cause must be zero on this construction

SEED_DERIVATION = (
    "seed_rng(int.from_bytes(sha256(f'{training_seed}:b11:rollout{r}').digest()[:8], 'big') "
    "% 2 ** 31) at the start of rollout r, where `seed_rng` is the frozen "
    "run_fsd_uav_individual_renewal_b01.seed_rng (random.seed, numpy.random.seed, "
    "torch.manual_seed); the collection lanes are "
    "`run_flexible_skill_duration_e0._make_envs(16, training_seed + 500, ...)`, which seeds lane "
    "`rank` with `training_seed + 500 + rank` exactly as `run_fit` seeds its lanes from the block "
    "seed")

SOURCE_NOTES = {
    "collector_transcription": (
        "the collection is the frozen collector's own per-step calls, in its own order, with its "
        "own arguments: `scripts/run_fsd_baseline_interruption_b01.py:95-151` "
        "(`collect_training`). That function both collects *and* calls `agent.update` at line 158, "
        "so it is not called here; its per-step body is reproduced call for call - "
        "`shared.e0._reset_all(envs)` once (line 98), `agent.train(True)` (line 101), and per step "
        "`agent.step(states, observations, env_steps, dones, deterministic=False, "
        "return_step_data=True, build_infos=False)` (lines 112-113), `env.step(actions[lane])` per "
        "lane (line 120), `agent.store_transition_batch(...)` with the identical keyword arguments "
        "(lines 134-136), the terminal-lane reset with `agent.reset_env_state(lane)` (lines "
        "141-148), and the same `require_finite` guards and the same terminal-episode refusal "
        "(lines 152-153). Where the frozen loop calls `agent.update` this object computes the "
        "coordinator's credit arithmetic instead and takes no optimizer step; everything the loop "
        "does after the update - `shared.renewal_metrics(agent)` (line 167) and "
        "`agent.clear_buffers()` (line 172) - is called unchanged. The sha256 of the frozen "
        "`collect_training` source text is published as `frozen_collector_source_sha256` so a "
        "reader can see which text this transcription mirrors"),
    "no_update": (
        "`agent.update` and `update_coordinator_d2` are never called. `update_coordinator_d2` "
        "takes 15 optimizer steps per rollout (hmasd/agent.py:6207-6218) and updates "
        "`value_norm_coordinator` before the first of them (hmasd/agent.py:6075-6078), and "
        "`agent.update` additionally increments `global_step`, updates the discoverer and the "
        "discriminators and steps the schedulers. This probe calls only the three read-only pieces "
        "of the credit path: the bootstrap block, `_d2_flush_open_segments` and "
        "`compute_high_level_advantages`, which write nothing but the rollout-scoped advantage and "
        "return tables that `clear_buffers` resets at the same boundary a fit resets them"),
    "bootstrap": (
        "the bootstrap values are the inline block of `HMASDAgent.update` "
        "(hmasd/agent.py:7029-7097), reproduced with its own arguments: under `torch.no_grad()`, "
        "`_normalize_states(last_state)` and `_normalize_observations(last_observations)` (both "
        "the identity on this construction, `use_obsnorm` and `use_statenorm` are False and the "
        "probe refuses to run if they are not), `skill_coordinator.get_value(state, obs)`, then "
        "`_denormalize_values(..., value_norm_coordinator)` (hmasd/agent.py:1475-1489), which only "
        "reads the running statistics, and the `{'state': [envs], 'agents': [envs, agents]}` "
        "dictionary the update builds. `last_state`/`last_observations` are the collector's own "
        "post-reset arrays, exactly as `collect_training` passes them (line 159). The update "
        "computes this block *before* `update_coordinator` flushes the open segments (line 7188 "
        "against hmasd/agent.py:5646-5650); neither reads the other's state, and this probe keeps "
        "the update's order. The frozen block swallows an exception and continues with "
        "`coord_bootstrap_values = None`; here it raises, because a probe that measures the credit "
        "arithmetic may not silently measure the fallback"),
    "advantages": (
        "`rollout_buffer.compute_high_level_advantages(bootstrap, gamma=config.gamma, "
        "value_normalizer=None)` with the arguments of hmasd/agent.py:6046-6050, which dispatches "
        "to `_compute_d2_high_level_advantages` (hmasd/utils.py:894, 1018): one discounted-GAE "
        "sequence per (env, team) over the valid team rows and one per (env, agent) over that "
        "agent's valid rows, `discounts = gamma ** elapsed`, `gae_lambda` at the function default "
        ".95, which equals `config.gae_lambda` on this construction (the call does not pass it). "
        "The stored segment values and the bootstrap values are already denormalised at collection "
        "(hmasd/agent.py:2664-2674), which is why `value_normalizer` must be None"),
    "segment_reward": (
        "a segment's reward is the gamma-discounted sum of the raw scalar environment (team) "
        "reward over the segment (hmasd/agent.py:2348-2355, accumulating `current_reward`, which "
        "is the collector's own scalar `rewards[lane]`, hmasd/agent.py:3873-3875). No "
        "discriminator, entropy or process term enters a coordinator segment's reward"),
    "standardisation": (
        "hmasd/agent.py:6153-6164: per minibatch, one shared mean and standard deviation over the "
        "masked team *and* agent advantages of that minibatch, then `(advantage - mean) / (std + "
        "1e-8)` for both heads. On this construction one minibatch is the whole rollout: "
        "`coordinator_batch_size` is 1280 and a rollout has 800 valid rows "
        "(hmasd/utils.py:1460-1465 yields one batch per epoch), so the standardisation constants "
        "are a property of the rollout and not of the shuffle. The probe refuses to publish a "
        "standardised column if the rollout carries more valid rows than the batch size"),
    "row_geometry": (
        "a valid row is a closed segment written at its start index "
        "(hmasd/utils.py:567-599). `valid` implies `sampled` (ADR 01 invariant 6) and a team "
        "decision samples every agent (invariant 7), which on this construction makes every team "
        "row carry six valid agent rows: the recorded D1280 fits log `rows_M` 800, `rows_M_agent` "
        "4800 and `rows_M_team` 800 for all 45 rollouts, with causes `reset` and `team_cap` only "
        "and mean segment length 10. The probe checks all of that at runtime and refuses the "
        "collection if the geometry it produced is not the recorded fit's"),
    "agent_label_of_a_row": (
        "the label a row is grouped by is the label the segment executed: `d2_agent_skills[t, e, "
        "i]` is written at the decision step from `self.env_agent_skills` after the assignment "
        "(hmasd/agent.py:2322-2333, 2714-2716) and the segment row sits at that decision step. The "
        "team row's label is `d2_team_skill[t, e]` the same way"),
    "team_label_is_a_placebo": (
        "the team label never reaches the low-level actor: `SkillDiscoverer.forward` "
        "(hmasd/networks.py:1801-1809) passes only the observation, the *agent* label and the "
        "hidden state. It reaches the low-level critic (hmasd/networks.py:1557-1560) and the "
        "coordinator's own decoder. At fixed weights it therefore cannot move an executed action, "
        "so the team-label table is a placebo row: any structure in it is the state's, not the "
        "label's"),
    "label_free_baseline": (
        "an agent's advantage is the team's segment return minus a label-free baseline: the "
        "coordinator's critic reads the state and the agent's encoded observation, not the label "
        "(hmasd/networks.py:734-735, 1210-1213), and every agent's segment reward is the same team "
        "reward. The other five agents' labels are noise in one agent's advantage, which is the "
        "dilution E2b names"),
    "lane_cluster": (
        "segments within one lane-episode share a world, a state trajectory and five other agents' "
        "labels, so rows are not independent. The cluster is the (rollout, lane) pair - one "
        "episode of one lane, since HORIZON equals `rollout_length` and every lane terminates at "
        "the end of every rollout - giving `rollouts * 16` clusters. A clustered standard error is "
        "the spread of the per-cluster means; the iid standard error beside it treats the rows as "
        "independent and is reported only because the notebook asked for both"),
    "additive_reference": (
        "the segment-level additive model is a *perfect-credit reference*, not the coordinator's "
        "signal: it regresses each team segment's own discounted reward on the six counts of "
        "agents holding each label in that segment (the counts sum to six, so the model carries no "
        "intercept and the coefficients are read as the reward per agent-segment of holding that "
        "label, up to one common additive shift). A second fit adds the segment's stored team "
        "value `V(s)` as a state control. It asks whether a label effect is detectable at the "
        "ten-step decision level at all when credit is perfect; the coordinator's own signal is "
        "the advantage table, which carries the label-free baseline and the GAE"),
    "score_function_estimate": (
        "the per-label old probabilities are not stored: `d2_agent_old_log_probs` carries the "
        "log-probability of the *chosen* label alone (hmasd/utils.py:551-553). Recovering `q_c` "
        "for every label would mean re-running the coordinator's decoder in the stored decode "
        "order, which is new machinery and a second forward pass over every decision, so this "
        "block reports the shares-based score-function estimate instead: `mean(A_std * "
        "1[label = c]) - share_c * mean(A_std)`, which is the exact per-logit pull of one PPO step "
        "at ratio 1 with `q_c` replaced by the executed share. It is descriptive and approximate, "
        "and it is labelled so"),
    "weights_and_route": b09.SOURCE_NOTES["weight_transfer_to_evaluator"],
    "evaluation_route": b09.SOURCE_NOTES["evaluation_route"],
    "lane_to_world": b09.SOURCE_NOTES["lane_to_world"],
}

INTERPRETATION_LIMIT = (
    "a fixed-weight measurement, not a fit: zero optimizer steps, and nothing here is trained. "
    "Exploration; three blocks; one checkpoint per block, and that checkpoint is the end of "
    "training, when the label law is what 45 rollouts made it - this says nothing about the "
    "coordinator's signal earlier in training, when the low level's six policies were still "
    "forming. Four rollouts per block. The collection worlds are the block's own sixteen lanes "
    "seeded 500 above the training seed and are not the fit's worlds, and the collection's "
    "random streams are this object's, not the fit's long-gone training stream: the tables are a "
    "sample of the trained law's signal, not a replay of any rollout the fit actually took. The "
    "advantage table is the coordinator's own signal; the additive regression beside it is a "
    "perfect-credit reference and is not that signal. A fixed-weight panel is bit-reproducible "
    "only on the host that trained the checkpoint - B08's own local probe attempts failed the "
    "faithful load off that host - so this command runs on wsl_4070.")


# ---------------------------------------------------------------------------
# seeds, digests and small readers
# ---------------------------------------------------------------------------


def collection_seed(training_seed, rollout):
    """The dedicated seed of one collection rollout: a function of (block, rollout) alone."""
    digest = hashlib.sha256(f"{int(training_seed)}:b11:rollout{int(rollout)}".encode("utf-8"))
    return int.from_bytes(digest.digest()[:8], "big") % 2 ** 31


def world_base_seed(training_seed):
    """The base seed of the collection lanes; lane `rank` is seeded `base + rank`."""
    return int(training_seed) + WORLD_SEED_OFFSET


def bootstrap_generator(training_seed):
    """The lane-cluster bootstrap's own generator; it touches no global stream."""
    digest = hashlib.sha256(b"b11:lane_cluster_bootstrap").digest()[:8]
    return np.random.default_rng([int(training_seed), int.from_bytes(digest, "big")])


def value_norm_record(normaliser):
    """The running statistics of one ValueNorm, as plain numbers."""
    if normaliser is None:
        return None
    return {key: float(np.asarray(getattr(normaliser, key), dtype=np.float64).reshape(-1)[0])
            for key in ("mean", "var", "count")}


def parameter_digest(agent):
    """A sha256 over every weight and running statistic an update could have moved."""
    digest = hashlib.sha256()
    modules = [("skill_coordinator", agent.skill_coordinator),
               ("skill_discoverer", agent.skill_discoverer)]
    for name in ("team_discriminator", "individual_discriminator",
                 "value_norm_coordinator", "value_norm_discoverer"):
        module = getattr(agent, name, None)
        if module is not None:
            modules.append((name, module))
    for name, module in modules:
        digest.update(name.encode("utf-8"))
        if hasattr(module, "state_dict"):
            for key, tensor in sorted(module.state_dict().items()):
                digest.update(key.encode("utf-8"))
                digest.update(np.ascontiguousarray(tensor.detach().cpu().numpy()).tobytes())
            continue
        for key in ("mean", "var", "count"):
            digest.update(key.encode("utf-8"))
            digest.update(np.ascontiguousarray(
                np.asarray(getattr(module, key), dtype=np.float64)).tobytes())
    return digest.hexdigest()


def learner_state_record(agent):
    """The digest and the readable ValueNorm statistics, taken together."""
    return {"parameter_digest": parameter_digest(agent),
            "value_norm_coordinator": value_norm_record(
                getattr(agent, "value_norm_coordinator", None)),
            "value_norm_discoverer": value_norm_record(
                getattr(agent, "value_norm_discoverer", None)),
            "covers": ("skill_coordinator, skill_discoverer, both discriminators and both "
                       "ValueNorm running statistics (mean, var, count)")}


def rng_digest():
    """A digest of the three global random streams, so a restore can be recorded, not assumed."""
    digest = hashlib.sha256()
    digest.update(repr(random.getstate()).encode("utf-8"))
    state = np.random.get_state()
    digest.update(str(state[0]).encode("utf-8"))
    digest.update(np.ascontiguousarray(state[1]).tobytes())
    digest.update(str(state[2:]).encode("utf-8"))
    digest.update(torch.get_rng_state().numpy().tobytes())
    return digest.hexdigest()


def frozen_collector_source():
    """The frozen collector this object's collection transcribes, recorded, never executed."""
    lines, start = inspect.getsourcelines(b01.collect_training)
    text = "".join(lines)
    return {"function": "scripts/run_fsd_baseline_interruption_b01.py:collect_training",
            "lines": f"{start}-{start + len(lines) - 1}",
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "note": SOURCE_NOTES["collector_transcription"]}


def recorded_row_geometry(recorded):
    """The (rows_M, rows_M_agent, rows_M_team) the recorded D1280 fit logged for every rollout."""
    rows = recorded.get("training_rows") or []
    seen = set()
    for row in rows:
        metrics = row.get("d2_metrics") or {}
        if not metrics:
            continue
        seen.add((int(metrics.get("rows_M", -1)), int(metrics.get("rows_M_agent", -1)),
                  int(metrics.get("rows_M_team", -1))))
    if len(seen) != 1:
        return None
    rows_M, rows_M_agent, rows_M_team = next(iter(seen))
    return {"rows_M": rows_M, "rows_M_agent": rows_M_agent, "rows_M_team": rows_M_team,
            "rollouts": len(rows)}


# ---------------------------------------------------------------------------
# the credit arithmetic: exactly the pieces the update calls, and nothing else
# ---------------------------------------------------------------------------


def coordinator_bootstrap_values(agent, last_state, last_observations):
    """The inline bootstrap block of `HMASDAgent.update` (hmasd/agent.py:7029-7097), read-only."""
    if getattr(agent, "use_ha_ctse", False):
        raise ValueError("this probe reproduces the non-HA-CTSE bootstrap branch only")
    if last_state is None or last_observations is None:
        raise ValueError("the bootstrap block needs the collector's own last state and observations")
    with torch.no_grad():
        last_state_norm = agent._normalize_states(last_state)
        last_obs_norm = agent._normalize_observations(last_observations)
        state_tensor = torch.FloatTensor(last_state_norm).to(agent.device)
        obs_tensor = torch.FloatTensor(last_obs_norm).to(agent.device)
        state_val, agent_vals, _ = agent.skill_coordinator.get_value(state_tensor, obs_tensor)
        if agent.config.use_valuenorm and agent.value_norm_coordinator is not None:
            state_val = agent._denormalize_values(state_val, agent.value_norm_coordinator)
            agent_vals = [agent._denormalize_values(v, agent.value_norm_coordinator)
                          for v in agent_vals]
        if agent_vals is not None and len(agent_vals) > 0:
            agent_vals_np = np.array([v.cpu().numpy().flatten() for v in agent_vals]).T
        else:
            agent_vals_np = np.zeros((agent.config.num_envs, agent.config.n_agents))
        return {"state": state_val.cpu().numpy().flatten(), "agents": agent_vals_np}


def standardise_minibatch(team_advantages, agent_advantages, team_valid, agent_valid):
    """hmasd/agent.py:6153-6164, in its own float32 arithmetic, on one minibatch.

    `team_advantages` is [M] and `agent_advantages` is [M, N] at the minibatch's rows, with the
    per-head valid masks as float, exactly as `get_d2_coordinator_sampler` packs them.
    """
    team_a = torch.as_tensor(np.ascontiguousarray(team_advantages), dtype=torch.float32)
    agent_a = torch.as_tensor(np.ascontiguousarray(agent_advantages), dtype=torch.float32)
    team_mask = torch.as_tensor(np.ascontiguousarray(team_valid), dtype=torch.float32)
    agent_mask = torch.as_tensor(np.ascontiguousarray(agent_valid), dtype=torch.float32)
    team_batch = team_a * team_mask
    agent_batch = agent_a * agent_mask
    all_advantages = torch.cat([team_batch.reshape(-1), agent_batch.reshape(-1)], dim=0)
    all_mask = torch.cat([team_mask.reshape(-1), agent_mask.reshape(-1)], dim=0)
    mask_total = torch.clamp(all_mask.sum(), min=1.0)
    global_mean = (all_advantages * all_mask).sum() / mask_total
    global_var = ((all_advantages - global_mean) ** 2 * all_mask).sum() / mask_total
    global_std = torch.sqrt(global_var) + 1e-8
    team_std = (team_a - global_mean) / global_std
    agent_std = (agent_a - global_mean) / global_std
    return {"team": team_std.numpy().astype(np.float64),
            "agent": agent_std.numpy().astype(np.float64),
            "mean": float(global_mean.item()), "std": float(global_std.item()),
            "masked_entries": int(all_mask.sum().item()),
            "definition": SOURCE_NOTES["standardisation"]}


def rollout_frame(agent, num_steps, last_state, last_observations, rollout, lanes):
    """One rollout's coordinator tables: bootstrap, flush, advantages, `get_d2_tables`, copied out.

    The order is the update's own: the bootstrap block runs first (hmasd/agent.py:7029-7097), then
    `update_coordinator` flushes the still-open segments (hmasd/agent.py:5646-5650) and
    `update_coordinator_d2` computes the advantages (hmasd/agent.py:6046-6050) and reads the tables.
    """
    bootstrap = coordinator_bootstrap_values(agent, last_state, last_observations)
    flushed = int(agent._d2_flush_open_segments(num_steps))
    agent.rollout_buffer.compute_high_level_advantages(
        bootstrap, gamma=agent.config.gamma, value_normalizer=None)
    tables = agent.rollout_buffer.get_d2_tables(num_steps)
    if tables is None:
        raise ValueError("the rollout buffer carries no D2 tables")

    team_valid = np.asarray(tables["team_valid"], dtype=bool)
    agent_valid = np.asarray(tables["agent_valid"], dtype=bool)
    row_mask = agent_valid.any(axis=-1) | team_valid
    rows_M = int(row_mask.sum())
    if rows_M == 0:
        raise ValueError("the rollout produced no valid coordinator rows")
    # `valid` implies `sampled` (ADR 01 invariant 6), and a team decision samples every agent
    # (invariant 7), which is what makes the segment-level additive model well defined here.
    if bool((agent_valid & ~np.asarray(tables["sampled_mask"], dtype=bool)).any()):
        raise ValueError("a valid agent row was not a sampled position")
    if bool((team_valid & ~np.asarray(tables["sample_Z"], dtype=bool)).any()):
        raise ValueError("a valid team row was not a team-decision position")
    if not np.array_equal(row_mask, team_valid) or not np.array_equal(
            agent_valid.all(axis=-1), team_valid):
        raise ValueError("the team rows and the six agent rows do not renew together")

    steps, envs = np.where(row_mask)
    team_advantages = np.asarray(tables["team_advantages"], dtype=np.float64)[steps, envs]
    agent_advantages = np.asarray(tables["agent_advantages"], dtype=np.float64)[steps, envs]
    team_mask = team_valid[steps, envs].astype(np.float64)
    agent_mask = agent_valid[steps, envs].astype(np.float64)
    standardisation = standardise_minibatch(team_advantages, agent_advantages,
                                            team_mask, agent_mask)

    labels = np.asarray(tables["agent_skills"], dtype=np.int64)[steps, envs]
    counts = np.stack([(labels == label).sum(axis=1) for label in range(N_LABELS)], axis=1)
    team = {
        "rollout": np.full(rows_M, int(rollout), dtype=np.int64),
        "lane": envs.astype(np.int64), "step": steps.astype(np.int64),
        "label": np.asarray(tables["team_skill"], dtype=np.int64)[steps, envs],
        "advantage": team_advantages,
        "standardised_advantage": standardisation["team"],
        "return": np.asarray(tables["team_returns"], dtype=np.float64)[steps, envs],
        "value": np.asarray(tables["team_value"], dtype=np.float64)[steps, envs],
        "reward": np.asarray(tables["team_reward"], dtype=np.float64)[steps, envs],
        "elapsed": np.asarray(tables["team_elapsed"], dtype=np.int64)[steps, envs],
        "terminal": np.asarray(tables["team_terminal"], dtype=bool)[steps, envs],
        "old_log_prob": np.asarray(tables["team_old_log_prob"], dtype=np.float64)[steps, envs],
        "counts": counts.astype(np.float64)}
    n_agents = int(labels.shape[1])
    flat = lambda array: np.asarray(array, dtype=np.float64)[steps, envs].reshape(-1)
    rows = {
        "rollout": np.full(rows_M * n_agents, int(rollout), dtype=np.int64),
        "lane": np.repeat(envs.astype(np.int64), n_agents),
        "step": np.repeat(steps.astype(np.int64), n_agents),
        "agent": np.tile(np.arange(n_agents, dtype=np.int64), rows_M),
        "label": labels.reshape(-1),
        "advantage": agent_advantages.reshape(-1),
        "standardised_advantage": standardisation["agent"].reshape(-1),
        "return": flat(tables["agent_returns"]),
        "value": flat(tables["agent_values"]),
        "reward": flat(tables["agent_reward"]),
        "elapsed": np.asarray(tables["agent_elapsed"], dtype=np.int64)[steps, envs].reshape(-1),
        "old_log_prob": flat(tables["agent_old_log_probs"])}
    return {
        "rollout": int(rollout), "lanes": int(lanes), "rows_M": rows_M,
        "rows_M_agent": int(agent_valid.sum()), "rows_M_team": int(team_valid.sum()),
        "flushed_open_segments": flushed,
        "bootstrap": {"state_mean": float(np.mean(bootstrap["state"])),
                      "agents_mean": float(np.mean(bootstrap["agents"])),
                      "envs": int(np.asarray(bootstrap["state"]).size),
                      "definition": SOURCE_NOTES["bootstrap"]},
        "standardisation": {key: standardisation[key]
                            for key in ("mean", "std", "masked_entries", "definition")},
        "team": team, "agent": rows}


# ---------------------------------------------------------------------------
# the measures
# ---------------------------------------------------------------------------


def _mean(values):
    return float(np.mean(values)) if len(values) else None


def _se(values):
    values = np.asarray(values, dtype=np.float64)
    if values.size < 2:
        return None
    return float(np.std(values, ddof=1) / math.sqrt(values.size))


def clusters_of(rows):
    """The (rollout, lane) cluster index of every row: one lane-episode is one cluster."""
    rollout = np.asarray(rows["rollout"], dtype=np.int64)
    lane = np.asarray(rows["lane"], dtype=np.int64)
    stride = int(lane.max()) + 1 if lane.size else 1
    return rollout * stride + lane


def cluster_means(values, clusters, mask=None):
    """The per-cluster means of `values` over the rows `mask` selects."""
    values = np.asarray(values, dtype=np.float64)
    clusters = np.asarray(clusters, dtype=np.int64)
    if mask is not None:
        values, clusters = values[mask], clusters[mask]
    if values.size == 0:
        return np.zeros(0, dtype=np.float64)
    order = np.unique(clusters)
    return np.asarray([values[clusters == key].mean() for key in order], dtype=np.float64)


def label_table(rows, clusters, *, n_labels=N_LABELS, primary="advantage"):
    """Per label: the count, the share and the mean of every column, with two standard errors."""
    labels = np.asarray(rows["label"], dtype=np.int64)
    total = int(labels.size)
    columns = ("advantage", "standardised_advantage", "return", "value", "reward")
    table = {}
    for label in range(n_labels):
        mask = labels == label
        count = int(mask.sum())
        entry = {"label": label, "count": count,
                 "share": count / total if total else None}
        for column in columns:
            if column not in rows:
                continue
            values = np.asarray(rows[column], dtype=np.float64)[mask]
            entry[f"mean_{column}"] = _mean(values)
            entry[f"se_{column}"] = _se(values)
        means = cluster_means(rows[primary], clusters, mask)
        entry.update({
            "clusters": int(means.size),
            "mean_of_cluster_means": _mean(means),
            f"clustered_se_{primary}": _se(means)})
        table[str(label)] = entry
    return table


def ranking_of(table, key):
    """The labels from the highest to the lowest `key`, the lowest label breaking an exact tie."""
    values = {int(label): entry[key] for label, entry in table.items()
              if entry.get(key) is not None}
    order = sorted(values, key=lambda label: (-values[label], label))
    return [int(label) for label in order], values


def spread_of(values):
    """max - min over the labels that carry a value, with the labels that produced it."""
    if not values:
        return None
    best = max(values, key=lambda label: (values[label], -label))
    worst = min(values, key=lambda label: (values[label], -label))
    return {"max_minus_min": float(values[best] - values[worst]),
            "best_label": int(best), "worst_label": int(worst),
            "best": float(values[best]), "worst": float(values[worst])}


def eta_squared(values, labels, n_labels=N_LABELS):
    """The between-label share of the total variance of `values`."""
    values = np.asarray(values, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.int64)
    if values.size == 0:
        return None
    grand = float(values.mean())
    total = float(((values - grand) ** 2).sum())
    if total <= 0.:
        return None
    between = 0.
    for label in range(n_labels):
        mask = labels == label
        count = int(mask.sum())
        if count:
            between += count * (float(values[mask].mean()) - grand) ** 2
    return float(between / total)


def spread_bootstrap(values, labels, clusters, generator, *, n_labels=N_LABELS,
                     resamples=BOOTSTRAP_RESAMPLES):
    """The lane-cluster bootstrap of the between-label spread of the mean of `values`."""
    values = np.asarray(values, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.int64)
    clusters = np.asarray(clusters, dtype=np.int64)
    order = np.unique(clusters)
    groups = len(order)
    if groups < 2 or values.size == 0:
        return None
    sums = np.zeros((groups, n_labels), dtype=np.float64)
    counts = np.zeros((groups, n_labels), dtype=np.float64)
    for index, key in enumerate(order):
        rows = clusters == key
        for label in range(n_labels):
            mask = rows & (labels == label)
            counts[index, label] = float(mask.sum())
            sums[index, label] = float(values[mask].sum())
    spreads = np.zeros(resamples, dtype=np.float64)
    drawn = 0
    for index in range(resamples):
        choice = generator.integers(0, groups, groups)
        total = counts[choice].sum(axis=0)
        if not np.all(total > 0.):  # a resample that lost a label cannot carry its spread
            continue
        means = sums[choice].sum(axis=0) / total
        spreads[drawn] = float(means.max() - means.min())
        drawn += 1
    if drawn < 2:
        return None
    spreads = spreads[:drawn]
    low, high = np.percentile(spreads, list(BOOTSTRAP_INTERVAL))
    return {
        "clusters": groups, "resamples": int(resamples), "usable_resamples": int(drawn),
        "clustered_se": float(spreads.std(ddof=1)),
        "percentile_interval": [float(low), float(high)],
        "interval_percentiles": list(BOOTSTRAP_INTERVAL),
        "bootstrap_mean": float(spreads.mean()),
        "definition": (
            "the (rollout, lane) clusters are resampled with replacement from a dedicated "
            "generator; each resample recomputes the six per-label means from the resampled "
            "clusters' rows and takes max minus min. `clustered_se` is the standard deviation of "
            f"those {resamples} spreads and the interval is their {BOOTSTRAP_INTERVAL[0]}th and "
            f"{BOOTSTRAP_INTERVAL[1]}th percentiles. A resample that loses a label entirely is "
            "dropped and counted. " + SOURCE_NOTES["lane_cluster"])}


def clustered_covariance(design, residuals, clusters, *, correction=True):
    """The cluster-robust sandwich covariance of a least-squares fit, clusters as given."""
    design = np.asarray(design, dtype=np.float64)
    residuals = np.asarray(residuals, dtype=np.float64)
    clusters = np.asarray(clusters, dtype=np.int64)
    rows, width = design.shape
    bread = np.linalg.pinv(design.T @ design)
    meat = np.zeros((width, width), dtype=np.float64)
    order = np.unique(clusters)
    for key in order:
        mask = clusters == key
        score = design[mask].T @ residuals[mask]
        meat += np.outer(score, score)
    groups = int(order.size)
    scale = 1.
    if correction and groups > 1 and rows > width:
        scale = (groups / (groups - 1.)) * ((rows - 1.) / (rows - width))
    return bread @ meat @ bread * scale, groups, scale


def additive_model(counts, reward, clusters, *, value=None, n_labels=N_LABELS):
    """The perfect-credit reference: segment reward on the six label counts, numpy least squares."""
    counts = np.asarray(counts, dtype=np.float64)
    reward = np.asarray(reward, dtype=np.float64)
    clusters = np.asarray(clusters, dtype=np.int64)
    if counts.shape[0] != reward.size or counts.shape[0] == 0:
        return None
    design = counts if value is None else np.concatenate(
        [counts, np.asarray(value, dtype=np.float64).reshape(-1, 1)], axis=1)
    beta, _residuals, rank, _singular = np.linalg.lstsq(design, reward, rcond=None)
    fitted = design @ beta
    errors = reward - fitted
    covariance, groups, scale = clustered_covariance(design, errors, clusters)
    standard_errors = np.sqrt(np.clip(np.diag(covariance), 0., None))
    coefficients = {str(label): float(beta[label]) for label in range(n_labels)}
    errors_by_label = {str(label): float(standard_errors[label]) for label in range(n_labels)}
    spread = spread_of({label: float(beta[label]) for label in range(n_labels)})
    gap_se = None
    if spread is not None:
        best, worst = spread["best_label"], spread["worst_label"]
        variance = (covariance[best, best] + covariance[worst, worst]
                    - 2. * covariance[best, worst])
        gap_se = float(math.sqrt(variance)) if variance > 0. else 0.
    total = float(((reward - reward.mean()) ** 2).sum())
    order, _values = ranking_of(
        {str(label): {"coefficient": float(beta[label])} for label in range(n_labels)},
        "coefficient")
    return {
        "segments": int(reward.size), "columns": int(design.shape[1]), "rank": int(rank),
        "clusters": groups, "small_sample_correction": float(scale),
        "state_control": value is not None,
        "coefficients": coefficients,
        "clustered_se": errors_by_label,
        "value_coefficient": None if value is None else float(beta[n_labels]),
        "value_clustered_se": None if value is None else float(standard_errors[n_labels]),
        "ranking": order,
        "best_label": None if spread is None else spread["best_label"],
        "worst_label": None if spread is None else spread["worst_label"],
        "max_minus_min": None if spread is None else spread["max_minus_min"],
        "max_minus_min_clustered_se": gap_se,
        "residual_sd": float(errors.std(ddof=1)) if errors.size > 1 else None,
        "r_squared": (None if total <= 0. else float(1. - float((errors ** 2).sum()) / total)),
        "definition": (
            "ordinary least squares (numpy.linalg.lstsq) of each team segment's own discounted "
            "reward on the six counts of agents holding each label in that segment; the counts sum "
            "to six, so the model carries no intercept and a coefficient is the reward per "
            "agent-segment of holding that label, identified up to one common additive shift"
            + (" . The segment's stored team value V(s) is added as a state control, so the "
               "coefficients are read at a fixed state value" if value is not None else "")
            + ". Standard errors are the cluster-robust sandwich with the (rollout, lane) cluster "
              "and the usual G/(G-1) (M-1)/(M-K) correction; the gap's standard error is "
              "sqrt(V_bb + V_ww - 2 V_bw) of the best and worst coefficients. "
            + SOURCE_NOTES["additive_reference"])}


def law_summary(rows, team, *, n_labels=N_LABELS):
    """The executed label law: shares, and -log q of the chosen label as an entropy estimate."""
    labels = np.asarray(rows["label"], dtype=np.int64)
    total = int(labels.size)
    shares = [float((labels == label).sum()) / total if total else None
              for label in range(n_labels)]
    agent_log_probs = np.asarray(rows["old_log_prob"], dtype=np.float64)
    team_log_probs = np.asarray(team["old_log_prob"], dtype=np.float64)
    team_labels = np.asarray(team["label"], dtype=np.int64)
    uniform = float(np.log(n_labels))
    entropy = None if agent_log_probs.size == 0 else float(-agent_log_probs.mean())
    team_entropy = None if team_log_probs.size == 0 else float(-team_log_probs.mean())
    return {
        "agent_label_shares": shares,
        "agent_label_counts": [int((labels == label).sum()) for label in range(n_labels)],
        "team_label_shares": [float((team_labels == label).sum()) / team_labels.size
                              if team_labels.size else None for label in range(n_labels)],
        "agent_label_entropy_estimate": entropy,
        "agent_label_entropy_se": _se(-agent_log_probs) if agent_log_probs.size > 1 else None,
        "team_label_entropy_estimate": team_entropy,
        "mean_chosen_agent_label_probability": (None if agent_log_probs.size == 0
                                                else float(np.exp(agent_log_probs).mean())),
        "uniform_entropy": uniform,
        "agent_entropy_gap_to_uniform": None if entropy is None else float(uniform - entropy),
        "team_entropy_gap_to_uniform": (None if team_entropy is None
                                        else float(uniform - team_entropy)),
        "definition": (
            "the shares are the executed (decision, agent) label counts of the collection. The "
            "entropy estimate is the mean of -log q of the *chosen* label over the same rows, "
            "which is an unbiased estimate of the law's conditional entropy; `uniform_entropy` is "
            "ln 6, the entropy of a flat law over the six labels. The log-probabilities are the "
            "ones the decision stored (hmasd/utils.py:551-553), so this is the law that actually "
            "ran, not a recomputation")}


def policy_gradient_block(rows, law, lambda_h, *, n_labels=N_LABELS):
    """Descriptive, approximate: the per-label logit pull of one PPO step at ratio 1."""
    labels = np.asarray(rows["label"], dtype=np.int64)
    advantages = np.asarray(rows["standardised_advantage"], dtype=np.float64)
    total = int(labels.size)
    if total == 0:
        return None
    overall = float(advantages.mean())
    pulls = {}
    for label in range(n_labels):
        mask = labels == label
        share = float(mask.sum()) / total
        term = float((advantages * mask).mean())
        pulls[str(label)] = {"share": share, "mean_standardised_advantage_indicator": term,
                             "policy_gradient_pull": float(term - share * overall)}
    values = {label: pulls[str(label)]["policy_gradient_pull"] for label in range(n_labels)}
    spread = spread_of(values)
    return {
        "estimator": "score_function_with_shares_as_q",
        "per_label": pulls,
        "mean_standardised_advantage": overall,
        "max_minus_min": None if spread is None else spread["max_minus_min"],
        "entropy_coefficient_lambda_h": float(lambda_h),
        "label_law_entropy_estimate": law.get("agent_label_entropy_estimate"),
        "label_law_entropy_gap_to_ln6": law.get("agent_entropy_gap_to_uniform"),
        "reading_note": (
            "descriptive, approximate. This is not a measured gradient: it is "
            "`mean(A_std * 1[label = c]) - share_c * mean(A_std)`, the per-logit pull one PPO step "
            "at ratio 1 would apply if the law's own `q_c` were the executed share. It is put "
            "beside `lambda_h` and the entropy gap to ln 6 only so the two pulls on a nearly flat "
            "law can be compared in the reading. " + SOURCE_NOTES["score_function_estimate"])}


def block_measures(frames, training_seed, lambda_h):
    """Every measure of one block, pooled over the rollouts and per rollout."""
    def stack(side, column):
        return np.concatenate([frame[side][column] for frame in frames])

    pooled_agent = {column: stack("agent", column) for column in
                    ("rollout", "lane", "step", "agent", "label", "advantage",
                     "standardised_advantage", "return", "value", "reward", "elapsed",
                     "old_log_prob")}
    pooled_team = {column: stack("team", column) for column in
                   ("rollout", "lane", "step", "label", "advantage", "standardised_advantage",
                    "return", "value", "reward", "elapsed", "old_log_prob")}
    pooled_team["counts"] = np.concatenate([frame["team"]["counts"] for frame in frames])
    agent_clusters = clusters_of(pooled_agent)
    team_clusters = clusters_of(pooled_team)

    agent_table = label_table(pooled_agent, agent_clusters)
    team_table = label_table(pooled_team, team_clusters)
    agent_order, agent_values = ranking_of(agent_table, "mean_advantage")
    team_order, team_values = ranking_of(team_table, "mean_advantage")
    spread = spread_of(agent_values)
    bootstrap = spread_bootstrap(pooled_agent["advantage"], pooled_agent["label"], agent_clusters,
                                 bootstrap_generator(training_seed))
    law = law_summary(pooled_agent, pooled_team)
    reference = additive_model(pooled_team["counts"], pooled_team["reward"], team_clusters)
    controlled = additive_model(pooled_team["counts"], pooled_team["reward"], team_clusters,
                                value=pooled_team["value"])

    per_rollout = []
    for frame in frames:
        rollout_agent_clusters = clusters_of(frame["agent"])
        rollout_team_clusters = clusters_of(frame["team"])
        table = label_table(frame["agent"], rollout_agent_clusters)
        order, values = ranking_of(table, "mean_advantage")
        per_rollout.append({
            "rollout": frame["rollout"], "rows_M": frame["rows_M"],
            "rows_M_agent": frame["rows_M_agent"], "rows_M_team": frame["rows_M_team"],
            "flushed_open_segments": frame["flushed_open_segments"],
            "standardisation": frame["standardisation"], "bootstrap": frame["bootstrap"],
            "agent_label_table": table, "agent_label_ranking": order,
            "agent_label_spread": spread_of(values),
            "team_label_table": label_table(frame["team"], rollout_team_clusters),
            "additive_reference": additive_model(frame["team"]["counts"], frame["team"]["reward"],
                                                 rollout_team_clusters),
            "mean_segment_reward": _mean(frame["team"]["reward"]),
            "mean_team_advantage": _mean(frame["team"]["advantage"]),
            "mean_agent_advantage": _mean(frame["agent"]["advantage"])})

    spread_se = None if bootstrap is None else bootstrap["clustered_se"]
    return {
        "rollouts": len(frames),
        "agent_rows": int(pooled_agent["label"].size),
        "team_rows": int(pooled_team["label"].size),
        "clusters": int(np.unique(agent_clusters).size),
        "agent_label_table": agent_table,
        "agent_label_ranking": agent_order,
        "agent_label_mean_advantage": {str(label): agent_values.get(label)
                                       for label in range(N_LABELS)},
        "agent_label_spread": spread,
        "agent_label_spread_bootstrap": bootstrap,
        "agent_label_spread_over_clustered_se": (
            None if spread is None or not spread_se else
            float(spread["max_minus_min"] / spread_se)),
        "agent_label_spread_exceeds_twice_its_clustered_se": (
            None if spread is None or spread_se is None else
            bool(spread["max_minus_min"] > SPREAD_MULTIPLE * spread_se)),
        "agent_advantage_eta_squared": eta_squared(pooled_agent["advantage"],
                                                   pooled_agent["label"]),
        "agent_standardised_advantage_eta_squared": eta_squared(
            pooled_agent["standardised_advantage"], pooled_agent["label"]),
        "team_label_table": team_table,
        "team_label_ranking": team_order,
        "team_label_spread": spread_of(team_values),
        "team_label_placebo_note": SOURCE_NOTES["team_label_is_a_placebo"],
        "additive_reference": reference,
        "additive_reference_with_state_control": controlled,
        "label_law": law,
        "policy_gradient": policy_gradient_block(pooled_agent, law, lambda_h),
        "per_rollout": per_rollout,
        "mean_segment_reward": _mean(pooled_team["reward"]),
        "mean_segment_elapsed": _mean(pooled_team["elapsed"]),
        "definitions": {
            "advantage": SOURCE_NOTES["advantages"],
            "segment_reward": SOURCE_NOTES["segment_reward"],
            "standardised_advantage": SOURCE_NOTES["standardisation"],
            "label": SOURCE_NOTES["agent_label_of_a_row"],
            "baseline": SOURCE_NOTES["label_free_baseline"],
            "clustered_se": SOURCE_NOTES["lane_cluster"],
            "team_label": SOURCE_NOTES["team_label_is_a_placebo"],
            "additive_reference": SOURCE_NOTES["additive_reference"]}}


# ---------------------------------------------------------------------------
# the collection: the frozen collector's own calls, with no update
# ---------------------------------------------------------------------------


def collect_training_law(envs, agent, summary, out, *, rollouts, training_seed, measure,
                         counters=None, check=None):
    """The frozen collector's per-step loop (b01.py:95-151) with the update replaced by `measure`.

    `b01.collect_training` both collects and calls `agent.update`, so it is not called here; this is
    its body call for call, with `shared.renewal_metrics` and `agent.clear_buffers()` at the same
    boundary, and `measure(rollout, states, observations)` where the update would be.
    """
    lanes, horizon = len(envs), shared.HORIZON
    states, observations = shared.e0._reset_all(envs)
    shared.require_finite((states, observations), "collection reset inputs")
    env_steps, dones = np.zeros(lanes, dtype=int), np.zeros(lanes, dtype=bool)
    agent.train(True)
    frames = []
    for rollout in range(rollouts):
        seed = collection_seed(training_seed, rollout)
        shared.seed_rng(seed)
        row = {"rollout_index": rollout, "transitions": 0, "stored_transitions": 0,
               "completed_episodes": 0, "stored_batches": 0, "updated": False,
               "collection_seed": int(seed), "return_sums": [0.] * lanes,
               "episode_returns_U": None}
        summary["training_rows"].append(row)
        returns = np.zeros(lanes, dtype=np.float64)
        for t in range(horizon):
            shared.check_deadline(summary, "training-law collection")
            actions, _, data = agent.step(states, observations, env_steps, dones,
                                          deterministic=False, return_step_data=True,
                                          build_infos=False)
            summary["counts"]["training_agent_step_batches"] += 1
            shared.require_finite(actions, "collection actions")
            shared.require_finite(data, "sampled step data")
            next_states, next_observations = [], []
            rewards = np.zeros(lanes, dtype=np.float64)
            next_dones = np.zeros(lanes, dtype=bool)
            for lane, env in enumerate(envs):
                obs, reward, term, trunc, info = env.step(actions[lane])
                summary["counts"]["training_transitions"] += 1
                row["transitions"] += 1
                next_dones[lane] = bool(term or trunc)
                row["completed_episodes"] += int(next_dones[lane])
                summary["counts"]["training_episodes"] += int(next_dones[lane])
                shared.require_finite(reward, "collection scalar reward")
                rewards[lane] = reward  # Never multiply learner rewards by the reporting factor.
                returns[lane] += reward
                row["return_sums"] = returns.tolist()
                next_states.append(np.asarray(info["next_state"], dtype=np.float64))
                next_observations.append(np.asarray(obs, dtype=np.float32))
            next_states, next_observations = np.stack(next_states), np.stack(next_observations)
            shared.require_finite((next_states, next_observations), "collection next inputs")
            agent.store_transition_batch(
                states=states, next_states=next_states.copy(), observations=observations,
                next_observations=next_observations.copy(), actions=actions, rewards=rewards,
                dones=next_dones, infos_batch=None, rollout_step_idx=t, step_data=data)
            row["stored_transitions"] += lanes
            row["stored_batches"] += 1
            summary["counts"]["stored_training_transitions"] += lanes
            # Storage already owns terminal next values; both subsequent inputs must be fresh.
            for lane, env in enumerate(envs):
                if next_dones[lane]:
                    reset_obs, reset_info = env.reset()
                    next_observations[lane] = np.asarray(reset_obs, dtype=np.float32)
                    next_states[lane] = np.asarray(reset_info["state"], dtype=np.float64)
                    shared.require_finite((next_states[lane], next_observations[lane]),
                                          "collection reset inputs")
                    agent.reset_env_state(lane)
                    env_steps[lane] = 0
                else:
                    env_steps[lane] += 1
            states, observations, dones = next_states, next_observations, next_dones
        if not dones.all() or row["completed_episodes"] != lanes:
            raise ValueError("collection rollout does not contain the required full terminal episodes")
        row["episode_returns_U"] = shared.measured(returns, "collection returns")
        shared.publish(out, summary, f"collection rollout {rollout} collected")
        # Where the frozen loop calls `agent.update`: the credit arithmetic, and no optimizer step.
        frame, record = measure(rollout, states, observations)
        frames.append(frame)
        row.update(record)
        row.update(shared.renewal_metrics(agent))  # per-rollout metrics, before ordinary clear
        if counters is not None:  # the frozen loop's own per-rollout optimizer line
            row["optimizer_calls_total"] = shared.optimizer_counts(counters)
            if any(row["optimizer_calls_total"].values()):
                raise ValueError("the collection took an optimizer step")
        with (out / "collection.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(shared.measured(row, "collection row"), allow_nan=False) + "\n")
        shared.publish(out, summary, f"collection rollout {rollout} measured")
        if check is not None:  # the geometry of this rollout, refused here and not four later
            check(rollout, row, frame)
        agent.clear_buffers()
    return frames


def check_rollout_geometry(row, frame, metrics, expected, *, frozen_geometry):
    """The run-time geometry of one collected rollout, refused where it is not the fit's."""
    segments = row.get("segments") or {}
    causes = dict((metrics or {}).get("cause_counts") or {})
    record = {
        "rows_M": frame["rows_M"], "rows_M_agent": frame["rows_M_agent"],
        "rows_M_team": frame["rows_M_team"],
        "flushed_open_segments": frame["flushed_open_segments"],
        "cause_counts": causes,
        "segment_length_agent_mean": (metrics or {}).get("segment_length_agent_mean"),
        "segment_length_team_mean": (metrics or {}).get("segment_length_team_mean"),
        "agent_segments": (segments.get("agent") or {}).get("count"),
        "team_segments": (segments.get("team") or {}).get("count"),
        "expected_rows": dict(expected) if expected else None,
        "frozen_host_geometry": bool(frozen_geometry),
        "definition": SOURCE_NOTES["row_geometry"]}
    unexpected = {name: int(count) for name, count in causes.items()
                  if name not in CAUSES_EXPECTED and int(count)}
    if unexpected:
        raise ValueError(f"the collection fired unexpected D2 decision causes: {unexpected}")
    if int(metrics.get("rows_M", -1)) != frame["rows_M"]:
        raise ValueError("the agent's own rows_M and the probe's disagree")
    if frozen_geometry:
        if expected is None:
            raise ValueError("the recorded D1280 fit carries no single row geometry to check")
        for key in ("rows_M", "rows_M_agent", "rows_M_team"):
            if frame[key] != expected[key]:
                raise ValueError(
                    f"the collection produced {key}={frame[key]}, not the recorded fit's "
                    f"{expected[key]} for the same construction")
        for key in ("segment_length_agent_mean", "segment_length_team_mean"):
            if record[key] != float(SKILL_PERIOD):
                raise ValueError(f"{key} is {record[key]}, not the frozen cadence {SKILL_PERIOD}")
    return record


# ---------------------------------------------------------------------------
# the probe
# ---------------------------------------------------------------------------


def run_probe(seed, weights, out, launch_sha=None, rollouts=ROLLOUTS):
    """One block: B09's construction and saved weights, one panel, four rollouts, no update."""
    if seed not in BLOCKS:
        raise SystemExit("this object probes blocks 772803, 772903 and 773003")
    if int(rollouts) < 1:
        raise SystemExit("a collection needs at least one rollout")
    b08.bind()  # B08's own probe binding: the frozen runner's construction, this object's measures
    started = time.perf_counter()
    evaluation_seed = BLOCKS[seed]
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "object_id": OBJECT_ID, "card": CARD, "command": "probe",
        "launch_sha": shared.e0._git("rev-parse", "HEAD"), "requested_launch_sha": launch_sha,
        "arm": SAVE_ARM, "block_seed": seed, "evaluation_seed": evaluation_seed,
        "weights": str(weights), "labels": N_LABELS, "rollouts": int(rollouts),
        "baseline_rule": BASELINE_RULE,
        "collection_seeds": {str(rollout): collection_seed(seed, rollout)
                             for rollout in range(int(rollouts))},
        "collection_lane_base_seed": world_base_seed(seed),
        "collection_lane_seeds": list(range(world_base_seed(seed),
                                            world_base_seed(seed) + shared.TRAIN_LANES)),
        "seed_derivation": SEED_DERIVATION,
        "construction_source": (
            f"{b08.OBJECT_ID} {SAVE_ARM} (the recorded stage-1 {b08.D_REFERENCE} construction): the "
            "frozen baseline x interruption B01 runner with B08's identities bound, B08's saved "
            "final weights loaded, zero optimizer steps; one `as_trained` panel and this object's "
            "training-law collection"),
        "reference_object_ids": [b10.OBJECT_ID, b09.OBJECT_ID, b08.OBJECT_ID],
        "recorded_d1280_summary": str(b08.RECORDED_FITS[seed]),
        "reference_summary": str(b08.REFERENCE_FITS[seed]),
        "host_geometry": b08.host_geometry(),
        "frozen_host_geometry": b08.host_geometry() == b08.probe.FROZEN_GEOMETRY,
        "frozen_collector_source": frozen_collector_source(),
        "source_notes": dict(SOURCE_NOTES),
        "status": "incomplete", "failure": None, "faithful_load": None}
    construction = out / "construction"
    try:
        _run(result, seed, evaluation_seed, construction, Path(weights), int(rollouts))
        result["status"] = "complete"
    except Exception as exc:  # the partial facts stay recorded
        result["status"], result["failure"] = "incomplete", f"{type(exc).__name__}: {exc}"
    finally:
        result["wall_seconds"] = time.perf_counter() - started
        result["interpretation_limit"] = INTERPRETATION_LIMIT
        shared.write_json(out / "summary.json", result)
    measures = result.get("measures") or {}
    print(json.dumps({
        "status": result["status"], "failure": result["failure"], "block_seed": seed,
        "faithful_load": (result.get("faithful_load") or {}).get("faithful_load"),
        "rollouts": result.get("rollouts"),
        "agent_label_mean_advantage": measures.get("agent_label_mean_advantage"),
        "agent_label_ranking": measures.get("agent_label_ranking"),
        "agent_label_spread": (measures.get("agent_label_spread") or {}).get("max_minus_min"),
        "agent_label_spread_clustered_se": (
            (measures.get("agent_label_spread_bootstrap") or {}).get("clustered_se")),
        "additive_reference_max_minus_min": (
            (measures.get("additive_reference") or {}).get("max_minus_min")),
        "optimizer_steps": result.get("optimizer_steps"),
        "parameters_unchanged": (result.get("learner_state") or {}).get("unchanged"),
        "wall_seconds": result.get("wall_seconds")}))
    return 0 if result["status"] == "complete" else 1


def _run(result, seed, evaluation_seed, out, weights, rollouts):
    """Build as B09's probe does, load its weights, run the panel, then collect and measure."""
    result["weights_record"] = b09.verify_weights(seed, weights)
    recorded, reason = b08.recorded_fit(seed)
    if recorded is None:  # the probe reads the recorded fit's construction and its panel
        raise ValueError(f"the recorded D1280 fit of block {seed} is unreadable: {reason}")
    reference, reference_summary, reference_path = b08.reference_panel(seed)
    result["reference"] = {
        "summary": str(reference_path), "object_id": reference_summary.get("object_id"),
        "factorial_arm": reference_summary.get("factorial_arm"),
        "panel_rollouts": int(reference["panel_rollouts"]),
        "launch_sha": reference_summary.get("launch_sha")}
    expected_rows = recorded_row_geometry(recorded)
    result["recorded_row_geometry"] = expected_rows

    summary = shared.base_summary(b08.ARMS[SAVE_ARM][0], training_seed=seed,
                                  evaluation_seed=evaluation_seed, object_id=OBJECT_ID,
                                  card=CARD, caps=None)
    summary.update(command="probe", factorial_arm=SAVE_ARM, block_seed=seed, rollouts=0,
                   panel_rollouts=[], panels=[],
                   coordinator_batch_size=b08.ARMS[SAVE_ARM][1], ordinary_wall_plan_seconds=None,
                   cost_law=("zero optimizer steps; one evaluation panel and "
                             f"{rollouts} training-law rollouts with no update"))
    out.mkdir(parents=True, exist_ok=True)
    envs, learner, _theta0, counters = b01.build_learner(SAVE_ARM, summary, out, seed)
    learner_differences = b08.require_recorded_construction(
        summary["learner_config"], recorded["learner_config"], "learner configuration")
    restore = b08.scale._forbid_optimizer_steps(learner)
    frames = []
    try:
        learner.load_model(str(weights))  # the agent's own load routine
        learner.train(False)
        before = learner_state_record(learner)
        result["learner_state"] = {"before": before, "after": None, "unchanged": None}
        evaluator = b01.build_evaluator(SAVE_ARM, summary, out, evaluation_seed)
        evaluation_differences = b08.require_recorded_construction(
            summary["evaluation_config"], recorded["evaluation_config"], "evaluation configuration")
        restore += b08.scale._forbid_optimizer_steps(evaluator.agent)
        config = learner.config
        if (int(config.n_z), int(config.n_Z)) != (N_LABELS, N_LABELS):
            raise ValueError(
                f"the construction carries n_z={int(config.n_z)}, n_Z={int(config.n_Z)}, not the "
                f"{N_LABELS} labels this object's tables are defined on")
        if bool(getattr(config, "use_obsnorm", False)) or bool(getattr(config, "use_statenorm", False)):
            raise ValueError(
                "this construction normalises observations or states, so a training-mode "
                "collection would move running statistics the probe promises not to move")

        # (a) the frozen `as_trained` panel and the faithful-load check.
        panel = b08.run_rule_panel(BASELINE_RULE, learner, evaluator, summary, out, 0,
                                   evaluation_seed=evaluation_seed)
        result["rules_measured"] = {BASELINE_RULE: panel}
        faithful = b09.faithful_load_record(summary["panels"][-1], reference)
        result["faithful_load"] = faithful
        if not faithful["faithful_load"]:
            raise ValueError(
                "the loaded weights do not reproduce the recorded panel; first differing world "
                f"index {faithful['first_differing_world']}")

        # (b) the training-law collection, with no update at all.
        geometry, rows = [], []
        frozen_geometry = b08.host_geometry() == b08.probe.FROZEN_GEOMETRY

        def measure(rollout, states, observations):
            frame = rollout_frame(learner, shared.HORIZON, states.copy(), observations.copy(),
                                  rollout, shared.TRAIN_LANES)
            if frame["rows_M"] > int(config.coordinator_batch_size):
                raise ValueError(
                    f"the rollout carries {frame['rows_M']} valid rows, more than the "
                    f"{int(config.coordinator_batch_size)} of one minibatch, so the update's "
                    "standardisation is not this rollout's single pool")
            return frame, {"rows_M": frame["rows_M"], "rows_M_agent": frame["rows_M_agent"],
                           "rows_M_team": frame["rows_M_team"],
                           "flushed_open_segments": frame["flushed_open_segments"],
                           "standardisation": frame["standardisation"],
                           "coordinator_bootstrap": frame["bootstrap"]}

        def check(_rollout, row, frame):
            geometry.append(check_rollout_geometry(
                row, frame, row.get("d2_metrics") or {}, expected_rows,
                frozen_geometry=frozen_geometry))
            rows.append({key: row.get(key) for key in
                         ("rollout_index", "collection_seed", "transitions", "stored_transitions",
                          "completed_episodes", "episode_returns_U", "rows_M", "rows_M_agent",
                          "rows_M_team", "flushed_open_segments", "standardisation",
                          "coordinator_bootstrap", "segments", "optimizer_calls_total")})

        collection_envs = None
        rng_before = rng_digest()
        with shared.e0._preserve_rng():  # the collection cannot move any other stream
            collection_envs = shared.e0._make_envs(
                shared.TRAIN_LANES, world_base_seed(seed), shared.N_UAVS, shared.N_USERS,
                shared.HORIZON)
            frames = collect_training_law(collection_envs, learner, summary, out,
                                          rollouts=rollouts, training_seed=seed, measure=measure,
                                          counters=counters, check=check)
        learner.train(False)
        rng_after = rng_digest()
        result["collection_rng"] = {
            "digest_before": rng_before, "digest_after": rng_after,
            "restored": bool(rng_before == rng_after),
            "definition": (
                "the whole collection - the lane construction, the rollouts and the credit "
                "arithmetic - runs inside `run_flexible_skill_duration_e0._preserve_rng`, so the "
                "Python, NumPy and torch streams leave it where they entered; the digests record "
                "it rather than asserting it. " + SEED_DERIVATION)}
        if not result["collection_rng"]["restored"]:
            raise ValueError("the collection did not restore the global random streams")
        after = learner_state_record(learner)
        unchanged = after["parameter_digest"] == before["parameter_digest"]
        result["learner_state"] = {"before": before, "after": after, "unchanged": bool(unchanged),
                                   "definition": SOURCE_NOTES["no_update"]}
        if not unchanged:
            raise ValueError("the probe moved a parameter or a value normaliser")
    finally:
        for optimizer, original in restore:
            optimizer.step = original

    learner_calls = shared.optimizer_counts(counters)
    steps = sum(learner_calls.values()) + sum(
        sum(panel["evaluator_optimizer_calls"].values()) for panel in summary["panels"])
    if steps != 0:
        raise ValueError("the probe is defined by taking no optimizer step")
    measures = block_measures(frames, seed, float(learner.config.lambda_h))
    result.update({
        "optimizer_steps": steps, "optimizer_calls": learner_calls,
        "measures": measures,
        "collection_rows": rows, "collection_geometry": geometry,
        "collection_lanes": len(collection_envs), "horizon": shared.HORIZON,
        "collection_transitions": summary["counts"]["training_transitions"],
        "collection_episodes": summary["counts"]["training_episodes"],
        "collection_agent_step_batches": summary["counts"]["training_agent_step_batches"],
        "collection_worlds": (
            f"the block's own sixteen lanes seeded {world_base_seed(seed)}..."
            f"{world_base_seed(seed) + shared.TRAIN_LANES - 1}; not the fit's training worlds"),
        "J_as_trained": float(panel["J_mean"]),
        "as_trained_world_scores": list(panel["J_world_scores"]),
        "evaluation_panels": len(summary["panels"]),
        "evaluation_episodes": summary["counts"]["evaluation_episodes"],
        "evaluation_steps": summary["counts"]["evaluation_steps"],
        "evaluation_lanes": shared.EVAL_LANES,
        "training_lanes_constructed": len(envs),
        "training_lane_seeds": summary["training_lane_seeds"],
        "evaluation_lane_seeds": summary["evaluation_lane_seeds"],
        "construction_summary": "construction/summary.json",
        "learner_config": summary["learner_config"],
        "evaluation_config": summary["evaluation_config"],
        "learner_config_differences_from_recorded_d1280": learner_differences,
        "evaluation_config_differences_from_recorded_d1280": evaluation_differences,
        "coordinator_training_mode": bool(learner.skill_coordinator.training),
        "update_law": {
            "gamma": float(learner.config.gamma),
            "gae_lambda": float(learner.config.gae_lambda),
            "clip_epsilon": float(learner.config.clip_epsilon),
            "ppo_epochs": int(learner.config.ppo_epochs),
            "lambda_h": float(learner.config.lambda_h),
            "lr_coordinator": float(learner.config.lr_coordinator),
            "coordinator_batch_size": int(learner.config.coordinator_batch_size),
            "note": ("the law the measured advantages would enter; this probe runs none of it. "
                     + SOURCE_NOTES["no_update"])}})
    return result


# ---------------------------------------------------------------------------
# reduce
# ---------------------------------------------------------------------------


def probe_row(summary):
    """Validated readings of one complete probe of this object."""
    if summary.get("object_id") != OBJECT_ID or summary.get("command") != "probe":
        raise ValueError("not a probe of this object")
    if summary.get("status") != "complete":
        raise ValueError("incomplete probe")
    seed = int(summary.get("block_seed", -1))
    if seed not in BLOCKS or int(summary.get("evaluation_seed", -1)) != BLOCKS[seed]:
        raise ValueError("not one of this object's three blocks")
    if not (summary.get("faithful_load") or {}).get("faithful_load"):
        raise ValueError("the probe did not establish a faithful load")
    if summary.get("optimizer_steps") != 0:
        raise ValueError("the probe took an optimizer step")
    state = summary.get("learner_state") or {}
    if not state.get("unchanged"):
        raise ValueError("the probe does not record unchanged parameters and value normalisers")
    measures = summary.get("measures") or {}
    table = measures.get("agent_label_table") or {}
    if sorted(table) != [str(label) for label in range(N_LABELS)]:
        raise ValueError("the probe does not carry a six-label advantage table")
    if not measures.get("additive_reference"):
        raise ValueError("the probe carries no perfect-credit reference")
    if int(measures.get("rollouts", 0)) < 1:
        raise ValueError("the probe carries no collected rollout")
    scores = summary.get("as_trained_world_scores")
    if not scores:
        raise ValueError("the probe carries no `as_trained` world scores")
    return {
        "block_seed": seed, "launch_sha": summary.get("launch_sha"),
        "weights_sha256": (summary.get("weights_record") or {}).get("sha256"),
        "faithful_load": True, "as_trained_world_scores": list(scores),
        "J_as_trained": float(summary.get("J_as_trained")),
        "rollouts": int(measures["rollouts"]),
        "agent_rows": int(measures.get("agent_rows", 0)),
        "team_rows": int(measures.get("team_rows", 0)),
        "clusters": int(measures.get("clusters", 0)),
        "measures": measures,
        "collection_geometry": summary.get("collection_geometry"),
        "update_law": summary.get("update_law"),
        "wall_seconds": summary.get("wall_seconds")}


def b09_probe_row(summary):
    """One B09 probe of the same checkpoint, read by B09's own validated reader."""
    row = b09.probe_row(summary)  # refuses an incomplete, unfaithful or rule-short probe
    row["as_trained_world_scores"] = list(row["J_world_scores"][BASELINE_RULE])
    row["mean_action_J_by_label"] = {label: float(row["J_by_rule"][b09.constant_rule(label)])
                                     for label in range(N_LABELS)}
    best = b09.best_constant(row["J_by_rule"], float(row["J_by_rule"][BASELINE_RULE]))
    row["best_mean_action_label"] = int(best["label"])
    row["mean_action_ranking"] = [int(label) for label in best["ranking"]]
    histogram = [int(value) for value in row["label_histogram_by_rule"][BASELINE_RULE]]
    row["as_trained_agent_label_histogram"] = histogram
    row["coordinator_most_used_label"] = int(np.argmax(histogram)) if sum(histogram) else None
    return row


def b10_probe_row(summary):
    """One B10 probe of the same checkpoint, read by B10's own validated reader."""
    row = b10.probe_row(summary)  # refuses an incomplete or unproven sampled probe
    reading = b10.sampled_reading(row["J_by_rule"], float(row["J_by_rule"][BASELINE_RULE]))
    row["as_trained_world_scores"] = list(row["J_world_scores"][BASELINE_RULE])
    row["sampled_J_by_label"] = {label: float(reading["sampled_J_by_label"][str(label)])
                                 for label in range(N_LABELS)}
    row["sampled_ranking"] = [int(label) for label in reading["sampled_ranking"]]
    return row


def rank_of(ranking, label):
    """1-based position of a label in a ranking, or None where it does not appear."""
    ranking = [int(value) for value in ranking]
    return ranking.index(int(label)) + 1 if int(label) in ranking else None


def _series(values, n_labels=N_LABELS):
    """The six labels' values in label order, or None where any label is missing."""
    ordered = [values.get(label) for label in range(n_labels)]
    return None if any(value is None for value in ordered) else [float(v) for v in ordered]


def _spearman(first, second):
    """B10's own tie-corrected Spearman, or None where either side is incomplete."""
    if first is None or second is None:
        return None
    return b10.spearman(first, second)


def block_reading(row, b09_row, b10_row):
    """One block: this object's advantage table beside B09's and B10's label maps."""
    measures = row["measures"]
    advantage = {label: measures["agent_label_mean_advantage"].get(str(label))
                 for label in range(N_LABELS)}
    advantage_ranking = [int(label) for label in measures["agent_label_ranking"]]
    reference = measures["additive_reference"]
    coefficients = {label: float(reference["coefficients"][str(label)])
                    for label in range(N_LABELS)}
    coefficient_ranking = [int(label) for label in reference["ranking"]]
    mean_action = dict(b09_row["mean_action_J_by_label"])
    sampled = dict(b10_row["sampled_J_by_label"])
    best_label = int(b09_row["best_mean_action_label"])
    most_used = b09_row["coordinator_most_used_label"]
    spread = measures.get("agent_label_spread") or {}
    bootstrap = measures.get("agent_label_spread_bootstrap") or {}
    spread_se = bootstrap.get("clustered_se")
    series = _series
    return {
        "J_as_trained": row["J_as_trained"],
        "rollouts": row["rollouts"], "agent_rows": row["agent_rows"],
        "team_rows": row["team_rows"], "clusters": row["clusters"],
        "agent_label_mean_advantage": {str(label): advantage[label] for label in range(N_LABELS)},
        "agent_label_ranking": advantage_ranking,
        "agent_label_spread": spread.get("max_minus_min"),
        "agent_label_spread_clustered_se": spread_se,
        "agent_label_spread_over_clustered_se": measures.get(
            "agent_label_spread_over_clustered_se"),
        "agent_label_spread_percentile_interval": bootstrap.get("percentile_interval"),
        "agent_label_spread_exceeds_twice_its_clustered_se": measures.get(
            "agent_label_spread_exceeds_twice_its_clustered_se"),
        "agent_advantage_eta_squared": measures.get("agent_advantage_eta_squared"),
        "agent_label_clustered_se": {
            str(label): measures["agent_label_table"][str(label)].get("clustered_se_advantage")
            for label in range(N_LABELS)},
        "team_label_spread": (measures.get("team_label_spread") or {}).get("max_minus_min"),
        "team_label_ranking": [int(label) for label in measures.get("team_label_ranking", [])],
        "team_label_placebo_note": SOURCE_NOTES["team_label_is_a_placebo"],
        "additive_coefficients": {str(label): coefficients[label] for label in range(N_LABELS)},
        "additive_clustered_se": dict(reference["clustered_se"]),
        "additive_ranking": coefficient_ranking,
        "additive_max_minus_min": reference.get("max_minus_min"),
        "additive_max_minus_min_clustered_se": reference.get("max_minus_min_clustered_se"),
        "additive_exceeds_twice_its_clustered_se": (
            None if reference.get("max_minus_min") is None
            or not reference.get("max_minus_min_clustered_se") else
            bool(reference["max_minus_min"]
                 > SPREAD_MULTIPLE * reference["max_minus_min_clustered_se"])),
        "additive_with_state_control": measures.get("additive_reference_with_state_control"),
        "additive_reference_note": SOURCE_NOTES["additive_reference"],
        "mean_action_J_by_label": {str(label): mean_action[label] for label in range(N_LABELS)},
        "sampled_J_by_label": {str(label): sampled[label] for label in range(N_LABELS)},
        "mean_action_ranking": [int(label) for label in b09_row["mean_action_ranking"]],
        "sampled_ranking": [int(label) for label in b10_row["sampled_ranking"]],
        "rank_correlation_advantage_vs_mean_action": _spearman(
            series(advantage), series(mean_action)),
        "rank_correlation_advantage_vs_sampled": _spearman(
            series(advantage), series(sampled)),
        "rank_correlation_additive_vs_mean_action": _spearman(
            series(coefficients), series(mean_action)),
        "rank_correlation_additive_vs_sampled": _spearman(
            series(coefficients), series(sampled)),
        "rank_correlation_definition": (
            "Spearman's rank correlation, ties sharing their average rank (B10's own function), "
            "between the six labels' mean raw advantage in this probe's collection and their "
            "fixed-weight panel J - B09's mean-action map and B10's sampled map of the same "
            "checkpoint. Six paired points: a description of the order, not a test. The same "
            "correlation is reported for the additive-model coefficients, which are the "
            "perfect-credit reference and not the coordinator's signal"),
        "best_mean_action_label": best_label,
        "best_mean_action_label_advantage_rank": rank_of(advantage_ranking, best_label),
        "best_mean_action_label_is_first_by_advantage": bool(
            advantage_ranking and advantage_ranking[0] == best_label),
        "best_mean_action_label_additive_rank": rank_of(coefficient_ranking, best_label),
        "best_mean_action_label_is_first_by_additive": bool(
            coefficient_ranking and coefficient_ranking[0] == best_label),
        "coordinator_most_used_label": most_used,
        "coordinator_most_used_label_advantage_rank": (
            None if most_used is None else rank_of(advantage_ranking, most_used)),
        "coordinator_most_used_label_additive_rank": (
            None if most_used is None else rank_of(coefficient_ranking, most_used)),
        "coordinator_most_used_label_definition": (
            "the agent label the coordinator executed most often during the unmodified "
            "`as_trained` panel of this block (B09's own histogram), and where the same label "
            "sits in this probe's advantage ranking and in the perfect-credit reference"),
        "label_law": measures.get("label_law"),
        "policy_gradient": measures.get("policy_gradient"),
        "weights_sha256": row["weights_sha256"]}


def prediction_rows(readings):
    """E2a and E2b as the notebook declared them, counted where they are read.

    Arithmetic on the blocks that were read, with the statement each count belongs to. A count is
    not a weight of evidence, and none of these margins is a decision rule.
    """
    bottom_half = lambda rank: rank is not None and rank > N_LABELS // 2
    declared = {
        "E2a_the_advantage_spread_exceeds_twice_its_clustered_standard_error": {
            "blocks": tuple(sorted(BLOCKS)),
            "statement": ("the signal is present and the update does not use it: the between-label "
                          "spread of the mean raw advantage exceeds twice its lane-clustered "
                          "standard error"),
            "value": lambda r: r["agent_label_spread_exceeds_twice_its_clustered_se"],
            "holds": bool,
            "value_definition": ("max minus min over the six labels of the mean raw advantage of "
                                 "the valid agent rows, against twice the lane-cluster bootstrap "
                                 "standard error of that spread")},
        "E2a_on_772903_label_1_is_first_and_label_0_is_in_the_bottom_half": {
            "blocks": (772903,),
            "statement": ("the signal is present: on block 772903 - where B09 measured label 1 as "
                          "the best constant and the coordinator deploys label 0 - the advantage "
                          "ranking puts label 1 first and label 0 in the bottom half"),
            "value": lambda r: {"ranking": r["agent_label_ranking"],
                                "label_1_rank": rank_of(r["agent_label_ranking"], 1),
                                "label_0_rank": rank_of(r["agent_label_ranking"], 0)},
            "holds": lambda value: bool(value["label_1_rank"] == 1
                                        and bottom_half(value["label_0_rank"])),
            "value_definition": ("the labels ordered by their mean raw advantage, highest first, "
                                 "the lowest label breaking an exact tie; the bottom half of six "
                                 "is ranks 4 to 6")},
        "E2b_the_advantage_spread_is_within_twice_its_clustered_standard_error": {
            "blocks": tuple(sorted(BLOCKS)),
            "statement": ("the signal is absent at the decision level: the between-label spread of "
                          "the mean raw advantage is within twice its lane-clustered standard "
                          "error on all three blocks"),
            "value": lambda r: (None if r["agent_label_spread_exceeds_twice_its_clustered_se"]
                                is None else
                                not r["agent_label_spread_exceeds_twice_its_clustered_se"]),
            "holds": bool,
            "value_definition": ("the negation of the E2a spread statement on the same numbers; "
                                 "the two are exhaustive on a block that was read")},
        "REFERENCE_the_additive_coefficient_spread_exceeds_twice_its_clustered_standard_error": {
            "blocks": tuple(sorted(BLOCKS)),
            "statement": ("perfect-credit reference, not the coordinator's signal: the "
                          "between-label spread of the additive-model coefficients exceeds twice "
                          "its lane-clustered standard error"),
            "value": lambda r: r["additive_exceeds_twice_its_clustered_se"],
            "holds": bool,
            "value_definition": ("max minus min over the six coefficients of the segment-level "
                                 "additive model, against twice the cluster-robust standard error "
                                 "of that difference")},
        "REFERENCE_on_772903_label_1_is_first_and_label_0_is_in_the_bottom_half": {
            "blocks": (772903,),
            "statement": ("perfect-credit reference, not the coordinator's signal: on block 772903 "
                          "the additive-model coefficients put label 1 first and label 0 in the "
                          "bottom half"),
            "value": lambda r: {"ranking": r["additive_ranking"],
                                "label_1_rank": rank_of(r["additive_ranking"], 1),
                                "label_0_rank": rank_of(r["additive_ranking"], 0)},
            "holds": lambda value: bool(value["label_1_rank"] == 1
                                        and bottom_half(value["label_0_rank"])),
            "value_definition": ("the labels ordered by their additive-model coefficient, highest "
                                 "first, the lowest label breaking an exact tie")},
    }
    rows = {}
    for name, entry in declared.items():
        per_block = {}
        for seed in entry["blocks"]:
            reading = readings.get(seed)
            if reading is None:
                per_block[str(seed)] = {"read": False, "holds": None, "value": None}
                continue
            value = entry["value"](reading)
            per_block[str(seed)] = {"read": True, "value": value,
                                    "holds": None if value is None else bool(entry["holds"](value))}
        rows[name] = {
            "statement": entry["statement"], "value_definition": entry["value_definition"],
            "blocks_considered": [int(seed) for seed in entry["blocks"]],
            "blocks_read": int(sum(row["read"] for row in per_block.values())),
            "blocks_holding": int(sum(bool(row["holds"]) for row in per_block.values())),
            "per_block": per_block}
    rows["counting_note"] = (
        "the counts are the arithmetic of statements declared before the run, on the blocks that "
        "were read. E2a and E2b are read on the advantage table, which is the coordinator's own "
        "signal; the two REFERENCE rows repeat the same arithmetic on the perfect-credit "
        "regression and are not that signal. A count of three blocks is not an interval and not a "
        "weight of evidence, and `twice its standard error` is the notebook's declared reading "
        "rule, not a test")
    return rows


def reduce_inputs(probes, b09_probes, b10_probes):
    """This object's three probes beside B09's and B10's probes of the same three checkpoints."""
    b08.bind()  # the pure reading B08's own reduce takes: identities only, nothing wrapped
    shas = {summary.get("launch_sha") for summary in probes}
    if len(shas) > 1:
        raise ValueError(f"mixed launch shas among the probes: {sorted(str(s) for s in shas)}")
    b09_shas = {summary.get("launch_sha") for summary in b09_probes}
    b10_shas = {summary.get("launch_sha") for summary in b10_probes}

    def read(summaries, reader, what):
        rows, failures, seen = {}, {}, set()
        for summary in summaries:
            seed = int(summary.get("block_seed", -1))
            if seed in seen:  # a second probe of the same block is never a choice
                raise ValueError(f"duplicate {what} probe block")
            seen.add(seed)
            try:
                rows[seed] = reader(summary)
            except (KeyError, TypeError, ValueError) as exc:
                failures[seed] = str(exc)
        return rows, failures

    rows, failures = read(probes, probe_row, "this object's")
    b09_rows, b09_failures = read(b09_probes, b09_probe_row, "B09")
    b10_rows, b10_failures = read(b10_probes, b10_probe_row, "B10")

    blocks, readings = [], {}
    for seed in sorted(BLOCKS):
        entry = {"training_seed": seed, "evaluation_seed": BLOCKS[seed], "status": "incomplete",
                 "missing_or_invalid": {}}
        for name, source, failed in (("probe", rows, failures), ("b09_probe", b09_rows, b09_failures),
                                     ("b10_probe", b10_rows, b10_failures)):
            if seed not in source:
                entry["missing_or_invalid"][name] = failed.get(seed, "not supplied")
        if not entry["missing_or_invalid"]:
            row, b09_row, b10_row = rows[seed], b09_rows[seed], b10_rows[seed]
            digests = {row["weights_sha256"], b09_row["weights_sha256"], b10_row["weights_sha256"]}
            entry["weights_match"] = bool(row["weights_sha256"] and len(digests) == 1)
            identical = (row["as_trained_world_scores"] == b09_row["as_trained_world_scores"]
                         == b10_row["as_trained_world_scores"])
            entry["as_trained_identical_to_b09_and_b10"] = bool(identical)
            if not entry["weights_match"]:
                entry["missing_or_invalid"]["weights"] = (
                    "this probe's weights sha256 is not the one B09's and B10's probes of the same "
                    "block recorded, so they are not readings of one checkpoint")
            elif not identical:
                entry["missing_or_invalid"]["as_trained"] = (
                    "this probe's `as_trained` world scores are not B09's and B10's own, so the "
                    "probes are not the same policy on the same worlds and the block is not read")
            else:
                entry["status"] = "complete"
                entry.update(block_reading(row, b09_row, b10_row))
                readings[seed] = entry
        else:
            entry["weights_match"] = None
            entry["as_trained_identical_to_b09_and_b10"] = None
        blocks.append(entry)

    complete = [block for block in blocks if block["status"] == "complete"]
    across = b08._across
    result = {
        "object_id": OBJECT_ID, "card": CARD, "command": "reduce",
        "launch_sha": shared.e0._git("rev-parse", "HEAD"),
        "probe_launch_sha": next(iter(shas), None) if len(shas) == 1 else None,
        "b09_probe_launch_sha": next(iter(b09_shas), None) if len(b09_shas) == 1 else None,
        "b10_probe_launch_sha": next(iter(b10_shas), None) if len(b10_shas) == 1 else None,
        "reference_object_ids": [b10.OBJECT_ID, b09.OBJECT_ID, b08.OBJECT_ID],
        "status": "complete" if len(complete) == len(BLOCKS) else "incomplete",
        "arm": {"name": SAVE_ARM, "overrides": dict(b08.ARM_OVERRIDES[SAVE_ARM]),
                "coordinator_batch_size": b08.ARMS[SAVE_ARM][1],
                "caps": {"skill_cap_k_max": b08.ARM_CAPS[0], "team_cap_k_Z": b08.ARM_CAPS[1]}},
        "labels": N_LABELS, "rollouts_per_block": {
            str(block["training_seed"]): block.get("rollouts") for block in blocks},
        "quantity": (
            "an advantage is the coordinator's own per-segment GAE at the saved weights, computed "
            "by the same three calls its update makes; a label's value in the table is the mean "
            "raw advantage of the valid agent rows that executed it. B09's mean-action J and "
            "B10's sampled J are those objects' own fixed-weight panels of the same checkpoint, so "
            "every comparison is within one block, one checkpoint and one set of weights - but the "
            "advantage table is collected on this object's own sixteen worlds and the panels on "
            "the block's 32 evaluation worlds, so the pairing is the checkpoint, not the world"),
        "blocks": blocks,
        "blocks_read": len(complete),
        "invalid_probes": {str(seed): text for seed, text in failures.items()},
        "invalid_b09_probes": {str(seed): text for seed, text in b09_failures.items()},
        "invalid_b10_probes": {str(seed): text for seed, text in b10_failures.items()},
        "refusals": (
            "a batch of this object's probes at more than one launch sha, a duplicate block among "
            "any of the three sets, a summary that is not this object's probe, an incomplete "
            "probe, a probe that took an optimizer step or does not record unchanged parameters "
            "and value normalisers, a probe without a six-label advantage table or without the "
            "perfect-credit reference, a probe that did not establish a faithful load, a block "
            "whose B09 or B10 probe was not supplied or is not readable by that object's own "
            "reader, a block whose weights sha256 is not B09's and B10's, and a block whose "
            "`as_trained` world scores are not exactly theirs"),
        "interpretation_limit": INTERPRETATION_LIMIT,
        "source_notes": dict(SOURCE_NOTES),
    }
    for key in ("agent_label_spread", "agent_label_spread_clustered_se",
                "agent_label_spread_over_clustered_se", "agent_advantage_eta_squared",
                "team_label_spread", "additive_max_minus_min",
                "additive_max_minus_min_clustered_se",
                "rank_correlation_advantage_vs_mean_action",
                "rank_correlation_advantage_vs_sampled",
                "rank_correlation_additive_vs_mean_action",
                "rank_correlation_additive_vs_sampled"):
        result[key] = across(complete, lambda b, key=key: b[key])
    result["agent_label_mean_advantage"] = {
        str(label): across(complete,
                           lambda b, label=label: b["agent_label_mean_advantage"][str(label)])
        for label in range(N_LABELS)}
    result["additive_coefficients"] = {
        str(label): across(complete, lambda b, label=label: b["additive_coefficients"][str(label)])
        for label in range(N_LABELS)}
    result["ranking_by_block"] = {
        str(block["training_seed"]): {
            "advantage": block.get("agent_label_ranking"),
            "additive_reference": block.get("additive_ranking"),
            "mean_action_b09": block.get("mean_action_ranking"),
            "sampled_b10": block.get("sampled_ranking"),
            "team_label_placebo": block.get("team_label_ranking")}
        for block in blocks}
    result["best_label_by_block"] = {
        str(block["training_seed"]): {
            "advantage": (block.get("agent_label_ranking") or [None])[0],
            "additive_reference": (block.get("additive_ranking") or [None])[0],
            "mean_action_b09": block.get("best_mean_action_label"),
            "coordinator_most_used": block.get("coordinator_most_used_label")}
        for block in blocks}
    result["best_mean_action_label_rank_by_block"] = {
        str(block["training_seed"]): {
            "by_advantage": block.get("best_mean_action_label_advantage_rank"),
            "by_additive_reference": block.get("best_mean_action_label_additive_rank")}
        for block in blocks}
    result["coordinator_most_used_label_rank_by_block"] = {
        str(block["training_seed"]): {
            "label": block.get("coordinator_most_used_label"),
            "by_advantage": block.get("coordinator_most_used_label_advantage_rank"),
            "by_additive_reference": block.get("coordinator_most_used_label_additive_rank")}
        for block in blocks}
    result["blocks_where_b09s_best_label_is_first_by_advantage"] = [
        int(block["training_seed"]) for block in complete
        if block["best_mean_action_label_is_first_by_advantage"]]
    result["blocks_where_b09s_best_label_is_first_by_additive_reference"] = [
        int(block["training_seed"]) for block in complete
        if block["best_mean_action_label_is_first_by_additive"]]
    result["label_law_by_block"] = {
        str(block["training_seed"]): {
            "entropy_estimate": ((block.get("label_law") or {})
                                 .get("agent_label_entropy_estimate")),
            "entropy_gap_to_ln6": ((block.get("label_law") or {})
                                   .get("agent_entropy_gap_to_uniform")),
            "shares": (block.get("label_law") or {}).get("agent_label_shares")}
        for block in blocks}
    result["predictions"] = prediction_rows(readings)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prb = sub.add_parser("probe", help="zero-update training-law collection at saved weights")
    prb.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    prb.add_argument("--weights", type=Path, required=True,
                     help=f"B08's fit {WEIGHTS_NAME}; its {SIDECAR_NAME} must sit beside it")
    prb.add_argument("--launch-sha", required=True, help="must equal the source HEAD; recorded")
    prb.add_argument("--output-root", type=Path, required=True)
    prb.add_argument("--rollouts", type=int, default=ROLLOUTS,
                     help="training-law rollouts collected with no update (default 4)")
    red = sub.add_parser("reduce")
    red.add_argument("--probes", type=Path, nargs="+", required=True,
                     help="this object's three probe summaries")
    red.add_argument("--b09-probes", type=Path, nargs="+", required=True,
                     help="the B09 probe summaries of the same three checkpoints")
    red.add_argument("--b10-probes", type=Path, nargs="+", required=True,
                     help="the B10 probe summaries of the same three checkpoints")
    red.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))

    if args.command == "probe":
        head = shared.e0._git("rev-parse", "HEAD")
        if not head or args.launch_sha != head:
            parser.error("--launch-sha must equal the source HEAD")
        return run_probe(args.seed, args.weights.resolve(), args.output_root.resolve(),
                         launch_sha=args.launch_sha, rollouts=args.rollouts)

    args.output_root.mkdir(parents=True, exist_ok=True)
    result = reduce_inputs([load(path) for path in args.probes],
                           [load(path) for path in args.b09_probes],
                           [load(path) for path in args.b10_probes])
    result["input_probes"] = [str(path) for path in args.probes]
    result["input_b09_probes"] = [str(path) for path in args.b09_probes]
    result["input_b10_probes"] = [str(path) for path in args.b10_probes]
    shared.write_json(args.output_root / "summary.json", result)
    print(json.dumps({
        "status": result["status"], "blocks_read": result["blocks_read"],
        "agent_label_spread": (result["agent_label_spread"] or {}).get("mean"),
        "agent_label_spread_clustered_se": (
            result["agent_label_spread_clustered_se"] or {}).get("mean"),
        "rank_correlation_advantage_vs_mean_action": (
            result["rank_correlation_advantage_vs_mean_action"] or {}).get("mean"),
        "rank_correlation_advantage_vs_sampled": (
            result["rank_correlation_advantage_vs_sampled"] or {}).get("mean"),
        "rank_correlation_additive_vs_mean_action": (
            result["rank_correlation_additive_vs_mean_action"] or {}).get("mean"),
        "best_label_by_block": result["best_label_by_block"],
        "predictions": {name: entry["blocks_holding"] for name, entry in
                        result["predictions"].items() if isinstance(entry, dict)
                        and "blocks_holding" in entry}}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
