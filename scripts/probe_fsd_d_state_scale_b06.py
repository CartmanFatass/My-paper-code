"""FSD D state scale B06: a zero-fit forward probe of the untrained D1280 coordinator and critic.

Exploration, prospective entry in the direction notebook:
docs/research/candidates/flexible_skill_duration/NOTES.md, "2026-09-19 23:20 PDT - zero-fit
inspection planned: does D's coordinator see the state?".

No learner change at all. The construction is the completed B01 stage-1 D1280 fit's: the frozen
baseline x interruption B01 runner (`run_fsd_baseline_interruption_b01`) with the `D1280` arm as
rebound by `run_fsd_matched_information_baseline_b01`, same seed handling as a fit, untrained.
Every optimizer `step` of the learner and of the evaluator raises for the whole command, and the
summary records `optimizer_steps: 0`.  The recorded `learner_config` and `evaluation_config` are
compared field by field with the published D1280 fit of the same block
(`runs/flexible_skill_duration/b01_s1_d1280_<block>_a01/summary.json`); only the four fields the
host geometry determines may differ, and only on a shrunken test host.

One frozen evaluation panel runs (32 worlds, the block's evaluation seeds, the runner's own
evaluation routine, deterministic, unperturbed): `J_init` is its level.  While it runs, read-only
capture takes the coordinator's inputs at its decision calls and the low-level critic's inputs at
its own calls, on an evenly spaced stride; the panel itself is untouched and its per-world scores
are bit-identical to the frozen route without this probe.

After the panel, under `torch.no_grad()` and preserved RNG, the captured rows are measured twice
with the same weights and two state versions:

  raw        the state exactly as the panel fed it (metres; `use_statenorm` is False on this
             construction, so no running normaliser touches it)
  prescaled  the same state mapped by B05's affine from the actual environment bounds
             (`run_fsd_flat_input_scale_b05.state_affine`): x, y / area_size,
             (z - h_min) / (h_max - h_min), the normalised clock untouched

Only the state input differs between the two; the observations, the hidden states, the masks, the
held skills and every weight are the same.  A state perturbation is applied in metres *before* the
affine, so both versions see the same physical move.

`probe` is the only command.  The notebook entry records this policy execution as exposure, not as
a fit, so it carries no admission; it writes `<output-root>/summary.json` and prints one line.
"""
import argparse
import json
import math
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import run_fsd_baseline_interruption_b01 as b01
import run_fsd_flat_input_scale_b05 as scale
import run_fsd_matched_information_baseline_b01 as matched

shared = b01.shared
DIRECTION = "flexible_skill_duration"
OBJECT_ID = "FSD_D_STATE_PROBE_B06"
CARD = ("docs/research/candidates/flexible_skill_duration/NOTES.md "
        "(2026-09-19 23:20 PDT, zero-fit inspection: does D's coordinator see the state?)")
BLOCKS = dict(scale.BLOCKS)  # 772803, 772903, 773003
D_ARM = "D1280"  # the frozen runner knows this arm as ("D0", coordinator_batch_size=1280)
REFERENCE_OBJECT_ID = matched.OBJECT_ID
RECORDED_FITS = {seed: ROOT / "runs" / DIRECTION / f"b01_s1_d1280_{seed}_a01" / "summary.json"
                 for seed in BLOCKS}
# The configuration fields the lane count and the horizon alone determine: `num_envs`,
# `rollout_length` and `episode_length` are those two, `total_timesteps` is their product with the
# rollout count (run_flexible_skill_duration_e0.py:250) and the four buffer/batch fields are
# derived from them (configs/config_1.py:750-772). They are equal on the frozen host and differ
# only on a shrunken test host; every other field must equal the recorded fit's.
GEOMETRY_FIELDS = ("num_envs", "rollout_length", "episode_length", "total_timesteps",
                   "buffer_size", "batch_size", "high_level_buffer_size", "high_level_batch_size")
FROZEN_GEOMETRY = {"train_lanes": 16, "eval_lanes": 32, "horizon": 500}

# Capture: evenly spaced calls of the panel, with a hard row limit, so memory stays bounded.
COORDINATOR_CAPTURE_CALLS = 25
CRITIC_CAPTURE_CALLS = 25
# Perturbations. The relative step is B05's; the physical move and the swap are this entry's.
RELATIVE_PERTURBATION = scale.RELATIVE_PERTURBATION  # own observation x (1 + 0.05)
PERTURBED_AGENT = 0
SWAPPED_AGENTS = (0, 1)
MOVED_UAV = 0
MOVE_METRES = 50.  # + 50 m in x, applied to the metre state before any affine
SATURATION_LOW, SATURATION_HIGH = scale.SATURATION_LOW, scale.SATURATION_HIGH  # .05 / .95
STATE_VERSIONS = ("raw", "prescaled")

SOURCE_NOTES = {
    "coordinator_state_input": (
        "hmasd/agent.py:2561-2575 (the D2 teacher-forced gap pass, `_normalize_states(..., "
        "update=False)`) and hmasd/agent.py:2642-2661 (the decision pass, `assign_partial_batch`): "
        "the coordinator reads the global state and the six agent observations; with "
        "use_statenorm=False and use_obsnorm=False `_normalize_states`/`_normalize_observations` "
        "return their input unchanged (hmasd/agent.py:1502-1503, 1554-1555), so the state arrives "
        "in metres"),
    "coordinator_tokens": (
        "hmasd/networks.py:749-754 `SkillCoordinator._build_entity_sequence`: one nn.Linear "
        "embeds the 119-entry state into one token, one nn.Linear embeds each agent observation, "
        "and the seven tokens are summed with the positional encoding; "
        "hmasd/networks.py:716-723 builds the post-norm nn.TransformerEncoder over them"),
    "coordinator_logits": (
        "hmasd/networks.py:795-868 `assign_and_value_batch` is the deterministic logits path: the "
        "team skill is the argmax of the clamped team logits and each agent's logits are decoded "
        "autoregressively on that chain. hmasd/networks.py:968-1025 `evaluate_held_batch` replays "
        "one held chain without sampling and returns the same logits; both clamp to [-50, 50] "
        "after nan_to_num (networks.py:813-817, 834-838, 995, 1007) and the decoder itself clamps "
        "at the same threshold (networks.py:623-627, 697-701)"),
    "low_level_critic_input": (
        "hmasd/networks.py:1668 `cent_obs_space = (config.state_dim,)` and "
        "hmasd/networks.py:1811-1815 `SkillDiscoverer.get_value(state, team_skill, "
        "critic_hidden_state)` -> `R_Critic.forward` (hmasd/networks.py:1539-1573): the low-level "
        "critic reads the global state alone (no observation), modulated by the team skill's "
        "one-hot through FiLM, then the GRU. On the D path the caller is "
        "hmasd/agent.py:3131-3136 in `_batched_select_action`, with the state repeated per agent "
        "(hmasd/agent.py:3070-3074) and each agent's own critic hidden state"),
    "value_norm": (
        "hmasd/agent.py:3139-3140 denormalises the critic output with `value_norm_discoverer` "
        "after the forward call; this probe reports the raw network output, before that step"),
    "evaluation_route": (
        "the panel calls `agent.step(..., deterministic=True)` "
        "(run_fsd_baseline_interruption_b01.py:224-225), so the coordinator's team and agent "
        "skills are argmax choices, not samples (hmasd/networks.py:1072, 1099); at a team "
        "decision every agent is in S_t and the decode order is canonical, so the executed chain "
        "is exactly `assign_and_value_batch`'s deterministic chain"),
}


def bind():
    """Rebind the frozen runner to the matched-information object's D1280 construction.

    The loop, panel law and summary of `run_fsd_baseline_interruption_b01` stand; only the
    identities this probe runs under change.  `shared.base_summary` is *not* wrapped: this object
    writes its own summary and must not mark another object's.
    """
    global shared
    shared = b01.shared
    b01.OBJECT_ID, b01.CARD = OBJECT_ID, CARD
    b01.BLOCKS = dict(BLOCKS)
    b01.ROLLOUTS, b01.PANEL_ROLLOUTS = matched.ROLLOUTS, matched.PANEL_ROLLOUTS
    b01.ARMS, b01.FLAT_ARM = {D_ARM: matched.ARMS[D_ARM]}, matched.CF_ARM
    b01.WALL_PLANS = dict(matched.WALL_PLANS)
    b01.make_config = matched.make_config  # D1280 ignores the CF-only multiplier


# ---------------------------------------------------------------------------
# the construction is the recorded D1280 fit's
# ---------------------------------------------------------------------------


def host_geometry():
    return {"train_lanes": int(shared.TRAIN_LANES), "eval_lanes": int(shared.EVAL_LANES),
            "horizon": int(shared.HORIZON)}


def recorded_fit(seed):
    path = RECORDED_FITS[int(seed)]
    summary = json.loads(path.read_text(encoding="utf-8"))
    if (summary.get("object_id") != REFERENCE_OBJECT_ID or summary.get("factorial_arm") != D_ARM
            or summary.get("status") != "complete" or int(summary.get("block_seed", -1)) != int(seed)):
        raise ValueError(f"{path} is not the completed stage-1 D1280 fit of block {seed}")
    return summary, path


def config_differences(probe_config, recorded_config):
    """Every field where this probe's configuration snapshot differs from the recorded fit's."""
    keys = set(probe_config) | set(recorded_config)
    return {key: {"probe": probe_config.get(key, None), "recorded": recorded_config.get(key, None)}
            for key in sorted(keys) if probe_config.get(key, None) != recorded_config.get(key, None)}


def require_recorded_construction(probe_config, recorded_config, phase):
    """Refuse any difference from the recorded D1280 fit that the host geometry does not force."""
    differences = config_differences(probe_config, recorded_config)
    allowed = () if host_geometry() == FROZEN_GEOMETRY else GEOMETRY_FIELDS
    unexpected = {key: value for key, value in differences.items() if key not in allowed}
    if unexpected:
        raise ValueError(
            f"the probe's {phase} is not the recorded D1280 fit's: {sorted(unexpected)}")
    return differences


# ---------------------------------------------------------------------------
# read-only capture during the panel
# ---------------------------------------------------------------------------


class CoordinatorCapture:
    """The coordinator's inputs at its decision calls of one evaluation panel.

    `SkillCoordinator` is never called through `nn.Module.__call__` on this route, so there is no
    forward hook to register: the three batch entry points are wrapped on the evaluator's own
    instance for the duration of the panel.  Each wrapper records and calls through, so the panel
    is bit-identical to the unwrapped route, and the wrappers are removed before any measurement.
    """

    def __init__(self, agent, capture_calls=COORDINATOR_CAPTURE_CALLS, horizon=None):
        config = agent.config
        self.coordinator = agent.skill_coordinator
        self.state_dim, self.obs_dim = int(config.state_dim), int(config.obs_dim)
        self.n_agents = int(config.n_agents)
        horizon = shared.HORIZON if horizon is None else int(horizon)
        # A D1280 decision fires at reset and at every skill cap (k steps); c = c_Z = inf, so no
        # gap boundary can add one.  The limit bounds memory whatever the actual count turns out
        # to be.
        expected_calls = max(1, horizon // max(1, int(config.k)))
        self.capture_stride = max(1, expected_calls // max(1, int(capture_calls)))
        self.capture_limit = max(1, int(capture_calls))
        self.decision_calls, self.gap_calls, self.sampling_calls = 0, 0, 0
        self.rows = 0
        self.captured = []

    @contextmanager
    def attached(self):
        coordinator = self.coordinator
        names = ("assign_partial_batch", "evaluate_held_batch", "assign_and_value_batch")
        originals = {name: getattr(coordinator, name) for name in names}

        def decision(state, observations, *args, **kwargs):
            self._record(state, observations)
            return originals["assign_partial_batch"](state, observations, *args, **kwargs)

        def gap(state, observations, *args, **kwargs):
            self.gap_calls += 1
            return originals["evaluate_held_batch"](state, observations, *args, **kwargs)

        def sampling(state, observations, *args, **kwargs):
            self.sampling_calls += 1
            return originals["assign_and_value_batch"](state, observations, *args, **kwargs)

        coordinator.assign_partial_batch = decision
        coordinator.evaluate_held_batch = gap
        coordinator.assign_and_value_batch = sampling
        try:
            yield self
        finally:
            for name in names:  # instance attributes only; the class is untouched
                coordinator.__dict__.pop(name, None)

    def _record(self, state, observations):
        index = self.decision_calls
        self.decision_calls += 1
        if index % self.capture_stride != 0 or len(self.captured) >= self.capture_limit:
            return
        if state.dim() != 2 or int(state.shape[1]) != self.state_dim:
            raise ValueError(f"the coordinator's state is not [rows, {self.state_dim}]")
        if observations.dim() != 3 or tuple(observations.shape[1:]) != (self.n_agents, self.obs_dim):
            raise ValueError(
                f"the coordinator's observations are not [rows, {self.n_agents}, {self.obs_dim}]")
        self.captured.append({"state": state.detach().clone(),
                              "observations": observations.detach().clone()})
        self.rows += int(state.shape[0])

    def provenance(self):
        return {"decision_calls": self.decision_calls, "gap_pass_calls": self.gap_calls,
                "sampling_path_calls": self.sampling_calls,
                "captured_calls": len(self.captured), "captured_rows": self.rows,
                "capture_stride": self.capture_stride, "capture_limit": self.capture_limit,
                "definition": (
                    "the state and the six agent observations handed to "
                    "`SkillCoordinator.assign_partial_batch` (the D route's decision call) at every "
                    "`capture_stride`-th decision call of the panel, up to `capture_limit` calls; "
                    "`gap_pass_calls` counts `evaluate_held_batch` (the D2 trigger statistic) and "
                    "`sampling_path_calls` counts `assign_and_value_batch`, which the D route does "
                    "not use")}


class CriticCapture:
    """The low-level critic's inputs at its own calls of one evaluation panel."""

    def __init__(self, agent, capture_calls=CRITIC_CAPTURE_CALLS, horizon=None):
        config = agent.config
        self.critic = agent.skill_discoverer.critic
        self.gru = self.critic.rnn.rnn
        self.state_dim = int(config.state_dim)
        self.hidden_size = int(config.gru_hidden_size)
        horizon = shared.HORIZON if horizon is None else int(horizon)
        self.capture_stride = max(1, horizon // max(1, int(capture_calls)))
        self.capture_limit = max(1, int(capture_calls))
        self.calls, self.rows = 0, 0
        self.captured = []
        self._handle = None

    @contextmanager
    def attached(self):
        self._handle = self.critic.register_forward_pre_hook(self._hook)
        try:
            yield self
        finally:
            self._handle.remove()
            self._handle = None

    def _hook(self, module, args):
        cent_obs, rnn_states, masks, team_skill = args[:4]
        index = self.calls
        self.calls += 1
        if index % self.capture_stride != 0 or len(self.captured) >= self.capture_limit:
            return
        rows = int(cent_obs.shape[0])
        if cent_obs.dim() != 2 or int(cent_obs.shape[1]) != self.state_dim:
            raise ValueError(f"the critic's central input is not [rows, {self.state_dim}]")
        hidden = (torch.zeros(rows, self.hidden_size) if rnn_states is None
                  else rnn_states.detach().clone())
        self.captured.append({"cent_obs": cent_obs.detach().clone(), "hidden": hidden,
                              "masks": masks.detach().clone(),
                              "team_skill": team_skill.detach().clone()})
        self.rows += rows

    def provenance(self):
        return {"critic_calls": self.calls, "captured_calls": len(self.captured),
                "captured_rows": self.rows, "capture_stride": self.capture_stride,
                "capture_limit": self.capture_limit,
                "definition": (
                    "the four arguments of `R_Critic.forward` (central input, GRU hidden state, "
                    "entry masks, team skill) at every `capture_stride`-th critic call of the "
                    "panel, up to `capture_limit` calls; the evaluation route calls the critic "
                    "once per step for every (lane, agent) row, so the hidden states and masks "
                    "are the panel's own and nothing is invented")}


# ---------------------------------------------------------------------------
# the two state versions
# ---------------------------------------------------------------------------


def identity_transform(state):
    return state


def prescale_transform(affine):
    """B05's affine as a callable on a metre state: `(state - offset) / scale`."""
    offset = torch.as_tensor(affine["offset"], dtype=torch.float32)
    values = torch.as_tensor(affine["scale"], dtype=torch.float32)
    if not bool((values > 0).all()):
        raise ValueError("the state affine has a non-positive scale entry")

    def transform(state):
        return (state - offset) / values

    return transform


def state_transforms(affine):
    return {"raw": identity_transform, "prescaled": prescale_transform(affine)}


def move_metres(state, n_uavs, uav=MOVED_UAV, metres=MOVE_METRES):
    """UAV `uav` moved `metres` in x, in the metre state, before any affine."""
    index = 3 * int(uav)  # MultiUAVEnv._get_state lays out n_uavs x (x, y, z) first
    if not 0 <= index < int(state.shape[-1]) or int(uav) >= int(n_uavs):
        raise ValueError(f"UAV {uav} has no x entry in a state of width {int(state.shape[-1])}")
    moved = state.clone()
    moved[..., index] = moved[..., index] + float(metres)
    return moved


# ---------------------------------------------------------------------------
# (a), (b), (d) and (c): the coordinator
# ---------------------------------------------------------------------------


def first_layer_attention_weights(coordinator, tokens):
    """Per-head self-attention weights of the first encoder layer, from its own projection.

    `nn.MultiheadAttention` returns no weights on the fused path, so they are recomputed from
    `in_proj_weight`/`in_proj_bias` on exactly the sequence the layer receives: with
    `norm_first=False` (the default this construction uses) that is the positional-encoded token
    sequence itself, otherwise `norm1` of it.
    """
    layer = coordinator.encoder.layers[0]
    attention = layer.self_attn
    inputs = layer.norm1(tokens) if bool(getattr(layer, "norm_first", False)) else tokens
    projected = torch.nn.functional.linear(inputs, attention.in_proj_weight, attention.in_proj_bias)
    query, key, _value = projected.chunk(3, dim=-1)
    rows, count, width = inputs.shape
    heads = int(attention.num_heads)
    head_dim = width // heads
    query = query.view(rows, count, heads, head_dim).transpose(1, 2)
    key = key.view(rows, count, heads, head_dim).transpose(1, 2)
    scores = torch.matmul(query, key.transpose(-2, -1)) / math.sqrt(head_dim)
    return torch.softmax(scores, dim=-1)  # [rows, heads, queries, keys]


def _total_variation(left, right):
    return .5 * (left - right).abs().sum(-1)


def coordinator_reading(coordinator, captured, transform, *, n_uavs):
    """(a), (b), (c) and (d) of the notebook entry on one state version of the captured rows."""
    n_agents = len(coordinator.value_heads_obs)
    heads = int(coordinator.encoder.layers[0].self_attn.num_heads)
    n_Z, n_z = int(coordinator.n_Z), int(coordinator.n_z)
    rows = 0
    state_norm, observation_norm = 0., 0.
    maximum = torch.zeros(heads, dtype=torch.float64)
    entropy = torch.zeros(heads, dtype=torch.float64)
    state_mass = torch.zeros(heads, dtype=torch.float64)
    team_entropy, agent_entropy = 0., torch.zeros(n_agents, dtype=torch.float64)
    perturbations = ("own_observation_agent0_relative", "uav0_plus_50m_x",
                     "swap_observations_agents_0_and_1")
    totals = {name: {"team_tv": 0., "agent_tv": torch.zeros(n_agents, dtype=torch.float64),
                     "team_logit": 0., "agent_logit": torch.zeros(n_agents, dtype=torch.float64)}
              for name in perturbations}
    chain_matches, chain_difference = True, 0.

    for entry in captured:
        metres, observations = entry["state"], entry["observations"]
        state = transform(metres)
        count = int(state.shape[0])
        rows += count

        # (a) token embedding norms, before the encoder.
        state_norm += float(coordinator.state_embedding(state).norm(dim=-1).double().sum())
        embedded = coordinator.obs_embedding(observations.reshape(-1, int(observations.shape[-1])))
        observation_norm += float(embedded.norm(dim=-1).double().sum()) / n_agents

        # (b) first encoder layer attention on the sequence the layer actually receives.
        weights = first_layer_attention_weights(
            coordinator, coordinator._build_entity_sequence(state, observations))
        maximum += weights.max(dim=-1).values.double().mean(dim=-1).sum(dim=0)
        entropy += torch.special.entr(weights).sum(-1).double().mean(dim=-1).sum(dim=0)
        state_mass += weights[..., 0].double().mean(dim=-1).sum(dim=0)

        # (c)/(d) the deterministic chain of the unperturbed input, then the held replay.
        assignment = coordinator.assign_and_value_batch(state, observations, deterministic=True)
        held_Z, held_z = assignment["team_skills"], assignment["agent_skills"]
        base = coordinator.evaluate_held_batch(state, observations, held_Z, held_z)
        difference = float((base["Z_logits"] - assignment["Z_logits"]).abs().max())
        for index in range(n_agents):
            difference = max(difference, float(
                (base["z_logits"][:, index, :] - assignment["z_logits"][index]).abs().max()))
        chain_difference = max(chain_difference, difference)
        chain_matches = chain_matches and difference == 0.

        base_team = torch.softmax(base["Z_logits"], dim=-1)
        base_agent = torch.softmax(base["z_logits"], dim=-1)
        team_entropy += float(torch.special.entr(base_team).sum(-1).double().sum())
        agent_entropy += torch.special.entr(base_agent).sum(-1).double().sum(dim=0)

        for name in perturbations:
            if name == "own_observation_agent0_relative":
                changed = observations.clone()
                changed[:, PERTURBED_AGENT, :] = (changed[:, PERTURBED_AGENT, :]
                                                  * (1. + RELATIVE_PERTURBATION))
                moved_state, moved_observations = state, changed
            elif name == "uav0_plus_50m_x":
                moved_state = transform(move_metres(metres, n_uavs))
                moved_observations = observations
            else:
                changed = observations.clone()
                left, right = SWAPPED_AGENTS
                changed[:, left, :], changed[:, right, :] = (observations[:, right, :],
                                                             observations[:, left, :])
                moved_state, moved_observations = state, changed
            perturbed = coordinator.evaluate_held_batch(
                moved_state, moved_observations, held_Z, held_z)
            totals[name]["team_tv"] += float(
                _total_variation(torch.softmax(perturbed["Z_logits"], dim=-1), base_team)
                .double().sum())
            totals[name]["agent_tv"] += _total_variation(
                torch.softmax(perturbed["z_logits"], dim=-1), base_agent).double().sum(dim=0)
            totals[name]["team_logit"] += float(
                (perturbed["Z_logits"] - base["Z_logits"]).abs().double().mean(-1).sum())
            totals[name]["agent_logit"] += (
                (perturbed["z_logits"] - base["z_logits"]).abs().double().mean(-1).sum(dim=0))

    divisor = max(rows, 1)
    sensitivity = {}
    for name in perturbations:
        agent_tv = (totals[name]["agent_tv"] / divisor).tolist()
        agent_logit = (totals[name]["agent_logit"] / divisor).tolist()
        sensitivity[name] = {
            "team_skill_total_variation": totals[name]["team_tv"] / divisor,
            "agent_skill_total_variation_per_agent": agent_tv,
            "agent_skill_total_variation_mean": float(np.mean(agent_tv)),
            "team_logit_mean_absolute_change": totals[name]["team_logit"] / divisor,
            "agent_logit_mean_absolute_change_per_agent": agent_logit,
            "agent_logit_mean_absolute_change_mean": float(np.mean(agent_logit))}
    agent_entropy_values = (agent_entropy / divisor).tolist()
    return {
        "rows": rows,
        "token_embedding_norms": {
            "state_token": state_norm / divisor,
            "observation_token": observation_norm / divisor,
            "state_over_observation": (state_norm / observation_norm
                                       if observation_norm > 0. else None),
            "definition": (
                "mean over captured rows of ||state_embedding(state)||_2, and mean over rows and "
                "over the six agents of ||obs_embedding(observation_i)||_2; both before the "
                "positional encoding and the encoder, and their ratio")},
        "first_encoder_layer_attention": {
            "heads": heads,
            "norm_first": bool(getattr(coordinator.encoder.layers[0], "norm_first", False)),
            "mean_max_weight_per_head": (maximum / divisor).tolist(),
            "mean_max_weight": float((maximum / divisor).mean()),
            "mean_entropy_nats_per_head": (entropy / divisor).tolist(),
            "mean_entropy_nats": float((entropy / divisor).mean()),
            "mean_mass_on_state_token_per_head": (state_mass / divisor).tolist(),
            "mean_mass_on_state_token": float((state_mass / divisor).mean()),
            "uniform_entropy_nats": math.log(1 + n_agents),
            "uniform_mass_on_state_token": 1. / (1 + n_agents),
            "definition": (
                "attention weights of the first encoder layer, recomputed from that layer's own "
                "self_attn.in_proj_weight/in_proj_bias on the sequence it receives (the "
                "positional-encoded seven tokens: the state token first, then the six agent "
                "tokens; norm1 first when norm_first): per head, the mean over queries and rows "
                "of the maximum attention weight, the mean attention entropy in nats, and the "
                "mean attention mass on the state token (key position 0)")},
        "skill_distributions": {
            "team_skill_entropy_nats": team_entropy / divisor,
            "agent_skill_entropy_nats_per_agent": agent_entropy_values,
            "agent_skill_entropy_nats_mean": float(np.mean(agent_entropy_values)),
            "ln_n_Z": math.log(n_Z), "ln_n_z": math.log(n_z),
            "definition": (
                "mean over captured rows of the Shannon entropy in nats of softmax(team logits) "
                "and of each agent's softmax(agent logits), on the unperturbed input, with the "
                "agent logits conditioned on the deterministic chain below; ln(n_Z) and ln(n_z) "
                "are the uniform references")},
        "skill_sensitivity": dict(sensitivity, definition=(
            "mean over captured rows of the total-variation distance between the skill "
            "probability vector of the perturbed input and of the unperturbed input, and the mean "
            "over rows and logit components of the absolute logit change; the perturbations are "
            f"agent {PERTURBED_AGENT}'s own observation x (1 + {RELATIVE_PERTURBATION}), UAV "
            f"{MOVED_UAV} moved +{MOVE_METRES:g} m in x in the state (applied in metres before the "
            "affine, so both state versions see the same physical move), and the observations of "
            f"agents {SWAPPED_AGENTS[0]} and {SWAPPED_AGENTS[1]} swapped")),
        "conditioning": {
            "team_skill": "the argmax team skill of this version's unperturbed input",
            "agent_skills": "the unperturbed input's deterministic autoregressive argmax chain",
            "held_replay_reproduces_assign_and_value": bool(chain_matches),
            "max_absolute_logit_difference": chain_difference,
            "definition": (
                "the agent-skill logits depend on the chosen team skill and on the preceding "
                "agents' skills, so every perturbed forward is teacher-forced "
                "(`evaluate_held_batch`) on the chain `assign_and_value_batch(deterministic=True)` "
                "produces for the unperturbed input of the same state version; the chain is "
                "therefore identical between the perturbed and unperturbed forwards of a version, "
                "and each version uses its own unperturbed chain. "
                "`held_replay_reproduces_assign_and_value` checks on every captured batch that the "
                "held replay of the unperturbed input returns exactly the sampling path's logits")},
    }


# ---------------------------------------------------------------------------
# (e): the low-level critic
# ---------------------------------------------------------------------------


def gate_saturation(gru, gru_input, hidden):
    """Saturated update/reset gate units, recomputed from `nn.GRU`'s own weights (as B05 does)."""
    input_terms = torch.nn.functional.linear(gru_input, gru.weight_ih_l0, gru.bias_ih_l0)
    hidden_terms = torch.nn.functional.linear(hidden, gru.weight_hh_l0, gru.bias_hh_l0)
    reset_i, update_i, _new_i = input_terms.chunk(3, dim=-1)  # PyTorch packs [reset, update, new]
    reset_h, update_h, _new_h = hidden_terms.chunk(3, dim=-1)
    counts = {}
    for name, value in (("reset", torch.sigmoid(reset_i + reset_h)),
                        ("update", torch.sigmoid(update_i + update_h))):
        saturated = (value < SATURATION_LOW) | (value > SATURATION_HIGH)
        counts[name] = (int(saturated.sum()), int(value.numel()))
    return counts


def critic_reading(critic, captured, transform, *, n_uavs, use_valuenorm):
    """(e) of the notebook entry on one state version of the captured critic rows."""
    gru = critic.rnn.rnn
    gates = {"update": [0, 0], "reset": [0, 0]}
    rows, baseline, change = 0, 0., 0.
    for entry in captured:
        metres, hidden = entry["cent_obs"], entry["hidden"]
        masks, team_skill = entry["masks"], entry["team_skill"]
        state = transform(metres)
        rows += int(state.shape[0])
        # The module's own path: MLPBase, then FiLM by the team skill's one-hot, then the GRU.
        features = critic.base(state)
        one_hot = torch.nn.functional.one_hot(
            team_skill.long(), num_classes=critic.film_generator.in_features).float()
        gamma, beta = torch.chunk(critic.film_generator(one_hot), 2, dim=-1)
        features = gamma * features + beta
        counts = gate_saturation(gru, features, hidden * masks)
        for name, (saturated, total) in counts.items():
            gates[name][0] += saturated
            gates[name][1] += total
        values, _hidden = critic(state, hidden, masks, team_skill)
        moved, _hidden = critic(transform(move_metres(metres, n_uavs)), hidden, masks, team_skill)
        baseline += float(values.abs().double().sum())
        change += float((moved - values).abs().double().sum())
    divisor = max(rows, 1)
    return {
        "rows": rows,
        "input": SOURCE_NOTES["low_level_critic_input"],
        "gru_gate_saturation": {
            name: {"fraction_saturated": (counts[0] / counts[1] if counts[1] else None),
                   "saturated_units": counts[0], "total_units": counts[1]}
            for name, counts in gates.items()},
        "gate_saturation_definition": (
            f"fraction of gate units below {SATURATION_LOW} or above {SATURATION_HIGH}; the update "
            "and reset gates are recomputed from nn.GRU's own weight_ih_l0/weight_hh_l0 and bias "
            "terms on the critic's FiLM-modulated features and the captured entry-masked hidden "
            "states, because nn.GRU returns no gate activations"),
        "mean_absolute_raw_value": baseline / divisor,
        "mean_absolute_value_change_uav0_plus_50m_x": change / divisor,
        "value_definition": (
            f"mean over captured critic rows of |v(state with UAV {MOVED_UAV} moved "
            f"+{MOVE_METRES:g} m in x) - v(state)|, at the row's own hidden state, entry mask and "
            "team skill, with the move applied in metres before the affine; v is the raw network "
            "output of `R_Critic.v_out`"),
        "value_norm": {"use_valuenorm": bool(use_valuenorm), "note": SOURCE_NOTES["value_norm"]},
    }


# ---------------------------------------------------------------------------
# the probe
# ---------------------------------------------------------------------------


def run_probe(seed, out, launch_sha=None):
    """One block: the untrained D1280 construction, one frozen panel, then the measurements."""
    if seed not in BLOCKS:
        raise SystemExit("this object probes blocks 772803, 772903 and 773003")
    bind()
    started = time.perf_counter()
    evaluation_seed = BLOCKS[seed]
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "object_id": OBJECT_ID, "card": CARD, "command": "probe",
        "launch_sha": shared.e0._git("rev-parse", "HEAD"), "requested_launch_sha": launch_sha,
        "arm": D_ARM, "block_seed": seed, "evaluation_seed": evaluation_seed,
        "construction_source": (
            f"{REFERENCE_OBJECT_ID} stage-1 {D_ARM}: the frozen baseline x interruption B01 runner "
            "with this object's identities bound, untrained, zero optimizer steps"),
        "recorded_d1280_summary": str(RECORDED_FITS[seed].relative_to(ROOT).as_posix()),
        "host_geometry": host_geometry(), "frozen_host_geometry": host_geometry() == FROZEN_GEOMETRY,
        "state_affine_convention": scale.STATE_LAYOUT_NOTE,
        "source_notes": dict(SOURCE_NOTES),
        "status": "incomplete", "failure": None}
    construction = out / "construction"
    try:
        result.update(_run(seed, evaluation_seed, construction))
        result["status"] = "complete"
    except Exception as exc:  # the partial facts stay recorded
        result["status"], result["failure"] = "incomplete", f"{type(exc).__name__}: {exc}"
    finally:
        result["wall_seconds"] = time.perf_counter() - started
        result["interpretation_limit"] = (
            "a forward measurement of the untrained D1280 construction, not a fit: zero optimizer "
            "steps, one evaluation panel, one block; J_init is a level and is the raw state only, "
            "because the pre-scaled state is a forward calculation on the same weights and not a "
            "policy that was executed")
        shared.write_json(out / "summary.json", result)
    print(json.dumps({"status": result["status"], "failure": result["failure"],
                      "block_seed": seed, "J_init": result.get("J_init_mean"),
                      "optimizer_steps": result.get("optimizer_steps")}))
    return 0 if result["status"] == "complete" else 1


def _run(seed, evaluation_seed, out):
    """Build as a fit would, run one untrained panel with capture, then measure. No update."""
    recorded, _path = recorded_fit(seed)
    summary = shared.base_summary(matched.ARMS[D_ARM][0], training_seed=seed,
                                  evaluation_seed=evaluation_seed, object_id=OBJECT_ID,
                                  card=CARD, caps=None)
    summary.update(command="probe", factorial_arm=D_ARM, block_seed=seed, rollouts=0,
                   panel_rollouts=[], panels=[],
                   coordinator_batch_size=matched.ARMS[D_ARM][1],
                   ordinary_wall_plan_seconds=None,
                   cost_law="zero optimizer steps; one untrained evaluation panel")
    out.mkdir(parents=True, exist_ok=True)
    envs, learner, _theta0, counters = b01.build_learner(D_ARM, summary, out, seed)
    learner_differences = require_recorded_construction(
        summary["learner_config"], recorded["learner_config"], "learner configuration")
    restore = scale._forbid_optimizer_steps(learner)
    try:
        evaluator = b01.build_evaluator(D_ARM, summary, out, evaluation_seed)
        evaluation_differences = require_recorded_construction(
            summary["evaluation_config"], recorded["evaluation_config"], "evaluation configuration")
        restore += scale._forbid_optimizer_steps(evaluator.agent)
        config = evaluator.agent.config
        affine, bounds = scale.state_affine(envs, int(config.state_dim))
        evaluation_affine, evaluation_bounds = scale.state_affine(
            evaluator.envs, int(config.state_dim))
        if affine != evaluation_affine or bounds != evaluation_bounds:
            raise ValueError("the learner and evaluator lanes do not share their environment bounds")
        coordinator = CoordinatorCapture(evaluator.agent)
        critic = CriticCapture(evaluator.agent)
        with coordinator.attached(), critic.attached():
            b01.evaluate_panel(learner, evaluator, summary, out, 0)
    finally:
        for optimizer, original in restore:
            optimizer.step = original
    panel = summary["panels"][-1]
    if panel["status"] != "complete":
        raise ValueError("the evaluation panel did not complete")
    learner_calls = shared.optimizer_counts(counters)
    steps = sum(learner_calls.values()) + sum(panel["evaluator_optimizer_calls"].values())
    if steps != 0:
        raise ValueError("the probe is defined by taking no optimizer step")
    if not coordinator.captured or not critic.captured:
        raise ValueError("the panel produced no coordinator decision call or no critic call")
    scores = np.asarray(panel["native_scores_J"], dtype=np.float64)

    measurements = {}
    transforms = state_transforms(affine)
    with shared.e0._preserve_rng(), torch.no_grad():
        for label in STATE_VERSIONS:
            measurements[label] = {
                "coordinator": coordinator_reading(
                    evaluator.agent.skill_coordinator, coordinator.captured, transforms[label],
                    n_uavs=bounds["n_uavs"]),
                "low_level_critic": critic_reading(
                    evaluator.agent.skill_discoverer.critic, critic.captured, transforms[label],
                    n_uavs=bounds["n_uavs"], use_valuenorm=bool(config.use_valuenorm))}
    return {
        "J_init_mean": float(scores.mean()), "J_init_world_scores": scores.tolist(),
        "J_init_world_sd": float(scores.std(ddof=1)) if scores.size > 1 else None,
        "returns_U": panel["returns_U"], "component_means": panel.get("component_means"),
        "optimizer_steps": steps, "optimizer_calls": learner_calls,
        "evaluator_optimizer_calls": panel["evaluator_optimizer_calls"],
        "evaluation_episodes": summary["counts"]["evaluation_episodes"],
        "evaluation_steps": summary["counts"]["evaluation_steps"],
        "evaluation_lanes": shared.EVAL_LANES, "horizon": shared.HORIZON,
        "evaluation_deterministic": True,
        "training_lanes_constructed": len(envs),
        "training_lane_seeds": summary["training_lane_seeds"],
        "evaluation_lane_seeds": summary["evaluation_lane_seeds"],
        # The frozen runner's own summary of the construction and the panel, published beside this
        # one: lane seeds, counts, per-panel exposure and the D2 renewal metrics of the panel.
        "construction_summary": "construction/summary.json",
        "learner_config": summary["learner_config"],
        "evaluation_config": summary["evaluation_config"],
        "learner_config_differences_from_recorded_d1280": learner_differences,
        "evaluation_config_differences_from_recorded_d1280": evaluation_differences,
        "initial_parameter_norms": summary["initial_parameter_norms"],
        "state_affine": affine, "state_affine_bounds": bounds,
        "coordinator_dropout": float(getattr(config, "coordinator_dropout", 0.)),
        "coordinator_training_mode": bool(evaluator.agent.skill_coordinator.training),
        "capture": {"coordinator": coordinator.provenance(), "low_level_critic": critic.provenance()},
        "state_versions": {
            "raw": ("the state exactly as the panel fed it: metres, because use_statenorm is "
                    "False on this construction"),
            "prescaled": ("the same state mapped by `(state - offset) / scale` of the B05 affine "
                          "from the actual environment bounds: x, y / area_size, "
                          "(z - h_min) / (h_max - h_min), the normalised clock untouched; the "
                          "weights are identical in both versions and only this input differs")},
        "measurements": measurements}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    probe = sub.add_parser("probe", help="zero-update forward measurement of the untrained D1280")
    probe.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    probe.add_argument("--launch-sha", required=True, help="must equal the source HEAD; recorded")
    probe.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    head = shared.e0._git("rev-parse", "HEAD")
    if not head or args.launch_sha != head:
        parser.error("--launch-sha must equal the source HEAD")
    return run_probe(args.seed, args.output_root.resolve(), launch_sha=args.launch_sha)


if __name__ == "__main__":
    raise SystemExit(main())
