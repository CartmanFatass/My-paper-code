"""FSD flat input scale B05: the central-input flat learner with the appended state on the
observations' own scale.

Exploration (a zero-fit forward probe, then three fits), prospective entry in the direction
notebook: docs/research/candidates/flexible_skill_duration/NOTES.md, "2026-09-19 20:40 PDT -
prospective: CF with the appended physical coordinates on the observations' own scale".

Thin entry over the frozen baseline x interruption B01 runner, as the flat-entropy (B03) and
flat-update (B04) entries are: the same collector loop, panel law, summary and fit validation,
rebound to this object's identity. The learner is B03's CF_E0005 construction exactly (the
matched-information CF flag, actor/critic rates at the selected multiplier 0.5, `lambda_l` =
0.0005, the learner's default sequence minibatch) with a single field added:

  central_snapshot_state_affine   the environment's own convention for a physical coordinate:
                                  x and y divided by the area size, UAV height as
                                  (z - h_min) / (h_max - h_min), the normalised clock untouched

`hmasd/networks.py` `SkillDiscoverer._apply_central_input` applies it to the leading `state_dim`
entries of the CF central input, at the single point that serves acting, replayed update and
evaluation; with the field absent that path is byte-for-byte the one that ran before it existed.
Nothing else changes: same information, same width, same held-snapshot clock, same FiLM, GRU,
critic (still the raw state), rewards and update law.

The field is not one of the frozen configuration-snapshot fields
(`run_flexible_skill_duration_e0.CONFIG_DUMP_FIELDS`, which this object does not modify), so the
recorded `learner_config` of a fit of this object is identical to the recorded `learner_config`
of its CF_E0005 reference, and the affine is recorded at the top level of this object's own
summary together with the environment bounds it was derived from. `fit_endpoint` validates it
there and recomputes it from those bounds.

Commands:

  fit     one of the three planned fits; result-bearing, so it runs only through
          `scripts/hmasd_launch.py` (runner-side admission).
  probe   the notebook entry's Step 1, zero optimizer steps: for the unscaled and the scaled
          construction of one block, the untrained policy is run through the frozen runner's own
          evaluation panel (32 worlds, the block's evaluation seeds, deterministic) and the actor
          inputs met there are measured. Every optimizer `step` raises for the whole command, and
          the summary records `optimizer_steps: 0`, the evaluation episodes and the wall. The
          notebook entry records that policy execution as exposure, not as a fit, so this command
          carries no admission and is run locally.
  reduce  a pure reading of published summaries; no admission.
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
import run_fsd_flat_entropy_b03 as entropy
import run_fsd_flat_update_b04 as update
import run_fsd_matched_information_baseline_b01 as matched
from scripts.hmasd_admission import require_admission

shared = b01.shared
DIRECTION = "flexible_skill_duration"
OBJECT_ID = "FSD_FLAT_INPUT_SCALE_B05"
CARD = ("docs/research/candidates/flexible_skill_duration/NOTES.md "
        "(2026-09-19 20:40 PDT, CF with the appended physical coordinates on the observations' "
        "own scale)")
BLOCKS = dict(entropy.BLOCKS)  # 772803, 772903, 773003
CF_ARM = matched.CF_ARM  # the frozen runner knows one flat arm by this name
FLAT_REFERENCE = "CF_E0005"
SKILL_REFERENCE = "D1280"
ENTROPY_COEFFICIENT = entropy.ENTROPY_ARMS[FLAT_REFERENCE]
LR_MULTIPLIER = entropy.SELECTED_MULTIPLIER
AFFINE_FIELD = "central_snapshot_state_affine"
BOUNDS_FIELD = "central_snapshot_state_bounds"
INPUT_SCALE_ARMS = ("CF_S",)  # one arm, run as the frozen runner's CF arm
ROLLOUTS = matched.ROLLOUTS
PANEL_ROLLOUTS = matched.PANEL_ROLLOUTS
EARLY_PANELS, LATE_PANELS = PANEL_ROLLOUTS[:4], PANEL_ROLLOUTS[-4:]  # panels 5-20 and 30-45
DIAGNOSTIC_ROLLOUTS = update.DIAGNOSTIC_ROLLOUTS  # (1,) + the nine panel rollouts
WALL_PLANS = {CF_ARM: 7000.}  # CF_E0005's measured wall as the plan; not a deadline
PRIMARY_NAME = f"J_{ROLLOUTS}"
# Nothing in the frozen configuration snapshot may differ from the CF_E0005 fit of the block:
# the declared difference is the affine, which that snapshot does not carry.
PAIR_DIFFERENCES = frozenset()
# 0.5 * ln(2 * pi * e) = 1.41893853...; the notebook entry's constant, kept literally.
GAUSSIAN_ENTROPY_PER_DIMENSION = 1.4189
ACTION_DIMENSIONS = 3  # the log-std parameter of this host's DiagGaussian head
STATE_LAYOUT_NOTE = (
    "envs/pettingzoo/uav_env.py MultiUAVEnv._get_state (lines 353-366) concatenates "
    "n_uavs x (x, y, z) UAV positions in metres, then n_users x (x, y) user positions in metres, "
    "then current_step / max_steps. The affine is the convention the same environment already "
    "uses for an agent's own position in its observation: x, y / area_size and "
    "(z - height_range[0]) / (height_range[1] - height_range[0]) "
    "(_get_observation_vectorized lines 386-390, _get_observation_reference lines 443-445); the "
    "normalised clock is left untouched (offset 0, scale 1).")
CURRENT = {"input_scale_arm": None, "admission": None, "summary": None}
_orig_make_config = matched._orig_make_config
_orig_base_summary = shared.base_summary
_FLAG = "_flat_input_scale_wrapper"


def bind(wrap=False):
    """Rebind the frozen runner's identities to this object; loop, panel law and validation stand.

    Readers need the identities only. A fit or probe also wraps `shared.base_summary`, and the
    command takes the wrapper off again, so a later reader or fit of another object in the same
    process is not marked.
    """
    global shared, _orig_base_summary
    shared = b01.shared
    b01.OBJECT_ID, b01.CARD = OBJECT_ID, CARD
    b01.BLOCKS, b01.ROLLOUTS, b01.PANEL_ROLLOUTS = dict(BLOCKS), ROLLOUTS, PANEL_ROLLOUTS
    b01.ARMS, b01.FLAT_ARM = {CF_ARM: matched.ARMS[CF_ARM]}, CF_ARM
    b01.WALL_PLANS = dict(WALL_PLANS)
    b01.make_config = make_config
    if wrap:
        current = shared.base_summary  # only ever wrap a plain function, exactly once
        for flag, module in (("_matched_information_wrapper", matched), (entropy._FLAG, entropy),
                             (update._FLAG, update)):
            if getattr(current, flag, False):
                current = module._orig_base_summary
        if not getattr(current, _FLAG, False):
            _orig_base_summary = current
        shared.base_summary = base_summary


# ---------------------------------------------------------------------------
# the state affine, from the actual environment instances
# ---------------------------------------------------------------------------


def state_affine_from_bounds(n_uavs, n_users, area_size, height_range, state_dim):
    """(offset, scale) for `MultiUAVEnv._get_state` on the observations' own scale."""
    area = float(area_size)
    low, high = float(height_range[0]), float(height_range[1])
    if not math.isfinite(area) or area <= 0.:
        raise ValueError(f"area_size {area_size!r} is not a positive finite length")
    if not math.isfinite(low) or not math.isfinite(high) or high <= low:
        raise ValueError(f"height_range {height_range!r} is not an increasing finite interval")
    offset, scale = [], []
    for _ in range(int(n_uavs)):  # UAV positions: x, y in metres, z in the height band
        offset.extend([0., 0., low])
        scale.extend([area, area, high - low])
    for _ in range(int(n_users)):  # user positions: x, y in metres
        offset.extend([0., 0.])
        scale.extend([area, area])
    offset.append(0.)  # the clock is already normalised
    scale.append(1.)
    if len(offset) != int(state_dim):
        raise ValueError(
            f"the state layout of n_uavs={n_uavs}, n_users={n_users} gives {len(offset)} entries, "
            f"not the configured state_dim {state_dim}")
    return offset, scale


def environment_bounds(envs):
    """The bounds of the actual environment instances handed to `make_config`; never guessed.

    `ParallelToArrayAdapter` re-exports `area_size`, `height_range`, `n_uavs` and `n_users` of the
    wrapped Scenario 1 environment. A lane that does not expose them, or a phase whose lanes
    disagree, fails here rather than producing a silently wrong transform.
    """
    values = []
    for index, env in enumerate(envs):
        entry = {}
        for name in ("area_size", "height_range", "n_uavs", "n_users"):
            value = getattr(env, name, None)
            if value is None:
                raise ValueError(
                    f"environment lane {index} does not expose {name}; the state affine of "
                    f"{OBJECT_ID} cannot be built from it")
            entry[name] = value
        try:
            entry["height_range"] = [float(entry["height_range"][0]), float(entry["height_range"][1])]
            entry["area_size"] = float(entry["area_size"])
            entry["n_uavs"], entry["n_users"] = int(entry["n_uavs"]), int(entry["n_users"])
        except (TypeError, ValueError, IndexError, KeyError) as exc:
            raise ValueError(f"environment lane {index} has unreadable bounds: {exc}") from None
        values.append(entry)
    if not values:
        raise ValueError("no environment was handed to make_config")
    if any(entry != values[0] for entry in values[1:]):
        raise ValueError("the lanes of one phase do not share their environment bounds")
    return values[0]


def state_affine(envs, state_dim):
    bounds = environment_bounds(envs)
    offset, scale = state_affine_from_bounds(
        bounds["n_uavs"], bounds["n_users"], bounds["area_size"], bounds["height_range"], state_dim)
    return {"offset": offset, "scale": scale}, bounds


def _record_affine(affine, bounds):
    """Put the affine on the running summary, and refuse a learner/evaluator disagreement.

    `make_config` is called once for the learner and once for the evaluator, from that phase's own
    environments; both must produce the same transform or the phases would not be comparable.
    """
    summary = CURRENT.get("summary")
    if summary is None:
        return
    previous = summary.get(AFFINE_FIELD)
    if previous is not None and (previous != affine or summary.get(BOUNDS_FIELD) != bounds):
        raise ValueError("the learner and evaluator phases built different state affines")
    summary[AFFINE_FIELD], summary[BOUNDS_FIELD] = affine, bounds


def make_config(arm, envs, seed):
    """B03's CF_E0005 construction, then this object's state affine when the arm is set."""
    config = _orig_make_config(arm, envs, seed)
    setattr(config, matched.CF_FLAG, True)
    setattr(config, entropy.ENTROPY_FIELD, ENTROPY_COEFFICIENT)
    for field in matched.TUNED_FIELDS:
        setattr(config, field, getattr(config, field) * LR_MULTIPLIER)
    if CURRENT["input_scale_arm"] is not None:  # None reproduces the CF_E0005 construction (tests)
        affine, bounds = state_affine(envs, int(config.state_dim))
        setattr(config, AFFINE_FIELD, (list(affine["offset"]), list(affine["scale"])))
        _record_affine(affine, bounds)
    return config


def base_summary(*args, **kwargs):
    summary = _orig_base_summary(*args, **kwargs)
    arm = CURRENT["input_scale_arm"]
    summary.update(flat_input_scale_object=OBJECT_ID, input_scale_arm=arm,
                   entropy_coefficient=ENTROPY_COEFFICIENT, lr_multiplier=LR_MULTIPLIER,
                   admission=CURRENT["admission"], primary=PRIMARY_NAME,
                   state_affine_convention=STATE_LAYOUT_NOTE)
    summary.setdefault(AFFINE_FIELD, None)  # `make_config` fills these in from the actual lanes
    summary.setdefault(BOUNDS_FIELD, None)
    CURRENT["summary"] = summary
    return summary


setattr(base_summary, _FLAG, True)


def plan_guard(arm, seed):
    """The notebook entry's three fits: the one scaled arm on the three blocks."""
    if arm not in INPUT_SCALE_ARMS:
        raise SystemExit(f"unknown arm {arm}")
    if seed not in BLOCKS:
        raise SystemExit("this object runs on blocks 772803, 772903 and 773003")


def run_fit(arm, seed, out, admission=None):
    plan_guard(arm, seed)
    bind(wrap=True)
    CURRENT.update(input_scale_arm=arm, admission=admission)
    try:
        return b01.run_fit(CF_ARM, seed, out)
    finally:
        CURRENT.update(input_scale_arm=None, admission=None, summary=None)
        if shared.base_summary is base_summary:
            shared.base_summary = _orig_base_summary


def validate_recorded_affine(summary):
    """The recorded affine must be the one the recorded bounds and state layout imply."""
    affine, bounds = summary.get(AFFINE_FIELD), summary.get(BOUNDS_FIELD)
    if not isinstance(affine, dict) or not isinstance(bounds, dict):
        raise ValueError("the fit does not record its state affine and the bounds it came from")
    config = summary["learner_config"]
    offset, scale = state_affine_from_bounds(
        bounds["n_uavs"], bounds["n_users"], bounds["area_size"], bounds["height_range"],
        int(config["state_dim"]))
    if ([float(v) for v in affine.get("offset", ())] != offset
            or [float(v) for v in affine.get("scale", ())] != scale):
        raise ValueError("the recorded affine is not the one the recorded bounds imply")
    if int(bounds["n_uavs"]) != int(config["n_agents"]) or int(bounds["n_users"]) != int(config["n_users"]):
        raise ValueError("the recorded bounds are not this fit's own host")
    return {"offset": offset, "scale": scale}


def fit_endpoint(summary):
    """Validated per-panel world scores of one complete fit of this object."""
    bind()
    if summary.get("flat_input_scale_object") != OBJECT_ID:
        raise ValueError("not a flat-input-scale fit")
    arm = summary.get("input_scale_arm")
    if arm not in INPUT_SCALE_ARMS or int(summary["block_seed"]) not in BLOCKS:
        raise ValueError("not one of this object's three planned fits")
    scores = b01.arm_panels(summary)
    if summary.get("lr_multiplier") != LR_MULTIPLIER:
        raise ValueError(f"{arm} does not carry the selected learning-rate multiplier")
    for key in ("learner_config", "evaluation_config"):
        if (summary[key].get(entropy.ENTROPY_FIELD) != ENTROPY_COEFFICIENT
                or not summary[key].get(matched.CF_FLAG)):
            raise ValueError(f"{arm} {key} is not the declared construction")
    validate_recorded_affine(summary)
    return scores


def pair_view(summary):
    """Everything a new fit shares with the CF_E0005 fit of its block; the launch sha is reported."""
    common = entropy.host_view(summary)
    for phase in ("learner_config", "evaluation_config"):
        common[phase] = {k: v for k, v in summary[phase].items() if k not in PAIR_DIFFERENCES}
    return common


# ---------------------------------------------------------------------------
# probe: zero optimizer steps, one untrained evaluation panel per construction
# ---------------------------------------------------------------------------


PROBE_CONSTRUCTIONS = (("unscaled", None), ("scaled", INPUT_SCALE_ARMS[0]))
SATURATION_LOW, SATURATION_HIGH = .05, .95  # the notebook entry's gate-saturation thresholds
RELATIVE_PERTURBATION = .05  # own observation x (1 + 0.05)
ADDITIVE_PERTURBATION = .05  # own observation + 0.05 x its per-entry SD over the panel
EGO_SHIFT = 1  # the ego one-hot moved to the next agent's identity, cyclically
SENSITIVITY_CAPTURE_STEPS = 25  # evenly spaced steps of the panel carry the perturbation pass


def _forbid_optimizer_steps(agent):
    """Make every optimizer step of one agent raise; returns the restore list."""
    restore = []
    for name in shared.NETWORKS:
        optimizer = getattr(agent, name + "_optimizer", None)
        if optimizer is None:
            continue
        original = optimizer.step

        def refuse(*args, _name=name, **kwargs):
            raise RuntimeError(f"the probe took an optimizer step on {_name}")

        optimizer.step = refuse
        restore.append((optimizer, original))
    return restore


class ActorProbe:
    """Streaming measurements on the actor inputs met during one evaluation panel.

    The panel itself is untouched: the hooks only read, and the finite-perturbation forwards run
    after the panel, on an evenly spaced capture of its inputs, inside `_preserve_rng` and with
    the hooks inert. The recomputed baseline action of every captured row is compared with the
    action the panel actually produced, which is recorded as `baseline_reproduces_panel_action`.
    """

    def __init__(self, agent, capture_steps=SENSITIVITY_CAPTURE_STEPS, horizon=None):
        discoverer = agent.skill_discoverer
        self.actor = discoverer.actor
        self.gru = discoverer.actor.rnn.rnn
        config = agent.config
        self.obs_dim, self.state_dim = int(config.obs_dim), int(config.state_dim)
        self.n_agents = int(config.n_agents)
        width = self.actor.base.mlp[0].in_features
        expected = self.obs_dim + self.state_dim + self.n_agents * self.obs_dim + self.n_agents
        if width != expected:
            raise ValueError(
                f"the actor reads {width} entries, not the CF layout's {expected}; the block "
                "shares would be meaningless")
        head = self.actor.act.action_out
        if type(head).__name__ != "DiagGaussian":
            raise ValueError(
                f"the mean action is read from a DiagGaussian head, not {type(head).__name__}")
        joint = self.obs_dim + self.state_dim
        self.blocks = {
            "own_observation": slice(0, self.obs_dim),
            "state": slice(self.obs_dim, joint),
            "joint_observations": slice(joint, joint + self.n_agents * self.obs_dim),
            "ego_one_hot": slice(width - self.n_agents, width)}
        horizon = shared.HORIZON if horizon is None else int(horizon)
        self.capture_stride = max(1, horizon // max(1, int(capture_steps)))
        self.capture_limit = max(1, int(capture_steps))
        self.calls, self.rows = 0, 0
        self._busy = False
        self._gru_arguments = None
        self._handles = []
        self._preactivation = {name: 0. for name in self.blocks}
        self._raw = {name: 0. for name in self.blocks}
        self._gates = {"update": [0, 0], "reset": [0, 0]}  # saturated units, total units
        self._own_sum = torch.zeros(self.obs_dim, dtype=torch.float64)
        self._own_squares = torch.zeros(self.obs_dim, dtype=torch.float64)
        self._captured = []

    @contextmanager
    def attached(self):
        self._handles = [
            self.gru.register_forward_pre_hook(self._gru_hook),
            self.actor.register_forward_hook(self._actor_hook, with_kwargs=True)]
        try:
            yield self
        finally:
            for handle in self._handles:
                handle.remove()
            self._handles = []

    def _gru_hook(self, module, args):
        if self._busy:
            return
        # `RNNLayer.forward` has already applied the entry mask to the hidden state.
        self._gru_arguments = (args[0].detach(), args[1].detach())

    def _actor_hook(self, module, args, kwargs, output):
        if self._busy:
            return
        observation = args[0].detach()
        self.calls += 1
        self.rows += int(observation.shape[0])
        weight = self.actor.base.mlp[0].weight.detach()
        for name, block in self.blocks.items():
            part = observation[:, block]
            self._raw[name] += float(part.double().pow(2).sum())
            # The first layer's pre-activation is sum_b W[:, b] x_b + bias; the share below is
            # the per-block squared norm of those contributions, without the bias or cross terms.
            self._preactivation[name] += float((part @ weight[:, block].t()).double().pow(2).sum())
        own = observation[:, self.blocks["own_observation"]].double()
        self._own_sum += own.sum(0)
        self._own_squares += own.pow(2).sum(0)
        self._accumulate_gates()
        if (self.calls - 1) % self.capture_stride == 0 and len(self._captured) < self.capture_limit:
            self._captured.append({
                "observation": observation.clone(), "hidden": args[1].detach().clone(),
                "masks": args[2].detach().clone(), "skill": args[3].detach().clone(),
                "action": output[0].detach().clone()})

    def _accumulate_gates(self):
        if self._gru_arguments is None:
            return
        gru_input, hidden = self._gru_arguments
        # `nn.GRU` exposes no gate activations, so they are recomputed from the layer's own
        # weights and the captured inputs. PyTorch packs the gates as [reset, update, new].
        input_terms = torch.nn.functional.linear(gru_input, self.gru.weight_ih_l0, self.gru.bias_ih_l0)
        hidden_terms = torch.nn.functional.linear(hidden, self.gru.weight_hh_l0, self.gru.bias_hh_l0)
        reset_i, update_i, _ = input_terms.chunk(3, dim=-1)
        reset_h, update_h, _ = hidden_terms.chunk(3, dim=-1)
        for name, value in (("reset", torch.sigmoid(reset_i + reset_h)),
                            ("update", torch.sigmoid(update_i + update_h))):
            saturated = (value < SATURATION_LOW) | (value > SATURATION_HIGH)
            self._gates[name][0] += int(saturated.sum())
            self._gates[name][1] += int(value.numel())

    def _own_observation_sd(self):
        count = max(self.rows, 1)
        mean = self._own_sum / count
        variance = (self._own_squares / count - mean.pow(2)).clamp_min(0.)
        return variance.sqrt().to(torch.float32)

    def _perturbed(self, observation, block, values):
        changed = observation.clone()
        changed[:, block] = values
        return changed

    def sensitivity(self):
        """Mean absolute change in the mean action, at fixed hidden state, per perturbation."""
        if not self._captured:
            return None
        sd = self._own_observation_sd()
        own, ego = self.blocks["own_observation"], self.blocks["ego_one_hot"]
        totals = {"own_observation_relative": 0., "own_observation_additive": 0., "ego_one_hot": 0.}
        baselines, components, matches = 0., 0, True
        self._busy = True
        try:
            with shared.e0._preserve_rng(), torch.no_grad():
                for entry in self._captured:
                    observation = entry["observation"]
                    call = (entry["hidden"], entry["masks"], entry["skill"])
                    base = self.actor(observation, *call, deterministic=True)[0]
                    matches = matches and bool(torch.equal(base, entry["action"]))
                    baselines += float(base.abs().sum())
                    components += int(base.numel())
                    perturbations = (
                        ("own_observation_relative",
                         self._perturbed(observation, own,
                                         observation[:, own] * (1. + RELATIVE_PERTURBATION))),
                        ("own_observation_additive",
                         self._perturbed(observation, own,
                                         observation[:, own] + ADDITIVE_PERTURBATION * sd)),
                        ("ego_one_hot",
                         self._perturbed(observation, ego,
                                         torch.roll(observation[:, ego], EGO_SHIFT, dims=-1))))
                    for name, changed in perturbations:
                        moved = self.actor(changed, *call, deterministic=True)[0]
                        totals[name] += float((moved - base).abs().sum())
        finally:
            self._busy = False
        divisor = max(components, 1)
        return {
            "mean_absolute_change_in_mean_action": {k: v / divisor for k, v in totals.items()},
            "mean_absolute_mean_action": baselines / divisor,
            "captured_steps": len(self._captured), "capture_stride": self.capture_stride,
            "action_components": components,
            "own_observation_sd_mean": float(sd.mean()), "own_observation_sd_max": float(sd.max()),
            "baseline_reproduces_panel_action": matches,
            "definition": (
                "mean over captured rows and action components of |mean action(perturbed) - mean "
                f"action|, at the row's own hidden state; relative step x (1 + {RELATIVE_PERTURBATION}) "
                f"and additive step {ADDITIVE_PERTURBATION} x the entry's SD over the whole panel "
                "on the agent's own current observation block, and the ego one-hot moved to the "
                "next agent's identity")}

    def read(self):
        preactivation = sum(self._preactivation.values())
        raw = sum(self._raw.values())
        return {
            "actor_input_dim": self.actor.base.mlp[0].in_features,
            "actor_calls": self.calls, "actor_rows": self.rows,
            "first_layer_preactivation_squared_norm_share": {
                name: (value / preactivation if preactivation > 0. else None)
                for name, value in self._preactivation.items()},
            "input_squared_norm_share": {
                name: (value / raw if raw > 0. else None) for name, value in self._raw.items()},
            "share_definition": (
                "per input block b, ||W[:, b] x_b||^2 of the actor's first linear layer (and ||x_b||^2 "
                "for the raw input), summed over every actor row of the panel and divided by the sum "
                "of those four block terms; the bias and the cross terms between blocks are left "
                "out, so this is not a share of the squared norm of the actual pre-activation"),
            "first_layer_preactivation_squared_norm_total": preactivation,
            "input_squared_norm_total": raw,
            "gru_gate_saturation": {
                name: {"fraction_saturated": (counts[0] / counts[1] if counts[1] else None),
                       "saturated_units": counts[0], "total_units": counts[1]}
                for name, counts in self._gates.items()},
            "gate_saturation_definition": (
                f"fraction of gate units below {SATURATION_LOW} or above {SATURATION_HIGH}; the "
                "update and reset gates are recomputed from nn.GRU's own weight_ih_l0/weight_hh_l0 "
                "and bias terms on the captured GRU inputs and entry-masked hidden states, "
                "because nn.GRU returns no gate activations"),
            "mean_action_sensitivity": self.sensitivity()}


def _probe_construction(label, arm, seed, out):
    """One construction of one block: build as a fit would, then one untrained panel."""
    evaluation_seed = BLOCKS[seed]
    CURRENT.update(input_scale_arm=arm)
    started = time.perf_counter()
    summary = shared.base_summary(matched.ARMS[CF_ARM][0], training_seed=seed,
                                  evaluation_seed=evaluation_seed, object_id=OBJECT_ID,
                                  card=CARD, caps=None)
    summary.update(command="probe", construction=label, factorial_arm=CF_ARM, block_seed=seed,
                   rollouts=0, panel_rollouts=[], panels=[], coordinator_batch_size=None,
                   ordinary_wall_plan_seconds=None,
                   cost_law="zero optimizer steps; one untrained evaluation panel per construction")
    out.mkdir(parents=True, exist_ok=True)
    envs, learner, _theta0, counters = b01.build_learner(CF_ARM, summary, out, seed)
    restore = _forbid_optimizer_steps(learner)
    try:
        evaluator = b01.build_evaluator(CF_ARM, summary, out, evaluation_seed)
        restore += _forbid_optimizer_steps(evaluator.agent)
        probe = ActorProbe(evaluator.agent)
        with probe.attached():
            b01.evaluate_panel(learner, evaluator, summary, out, 0)
        measurements = probe.read()
    finally:
        for optimizer, original in restore:
            optimizer.step = original
    panel = summary["panels"][-1]
    if panel["status"] != "complete":
        raise ValueError(f"the {label} panel did not complete")
    scores = np.asarray(panel["native_scores_J"], dtype=np.float64)
    learner_calls = shared.optimizer_counts(counters)
    steps = sum(learner_calls.values()) + sum(panel["evaluator_optimizer_calls"].values())
    if steps != 0:
        raise ValueError("the probe is defined by taking no optimizer step")
    result = {
        "construction": label, "input_scale_arm": arm,
        "central_snapshot_state_affine": summary.get(AFFINE_FIELD),
        "central_snapshot_state_bounds": summary.get(BOUNDS_FIELD),
        "J_init_mean": float(scores.mean()), "J_init_world_scores": scores.tolist(),
        "J_init_world_sd": float(scores.std(ddof=1)) if scores.size > 1 else None,
        "returns_U": panel["returns_U"], "component_means": panel.get("component_means"),
        "optimizer_steps": steps, "optimizer_calls": learner_calls,
        "evaluator_optimizer_calls": panel["evaluator_optimizer_calls"],
        "evaluation_episodes": summary["counts"]["evaluation_episodes"],
        "evaluation_steps": summary["counts"]["evaluation_steps"],
        "evaluation_lanes": shared.EVAL_LANES, "horizon": shared.HORIZON,
        "training_lanes_constructed": len(envs), "learner_config": summary["learner_config"],
        "initial_parameter_norms": summary["initial_parameter_norms"],
        "measurements": measurements,
        "wall_seconds": time.perf_counter() - started}
    shared.write_json(out / "probe.json", result)
    return result


def run_probe(seed, out, launch_sha=None):
    """Step 1 of the notebook entry: both constructions of one block, zero optimizer steps."""
    if seed not in BLOCKS:
        raise SystemExit("this object probes blocks 772803, 772903 and 773003")
    bind(wrap=True)
    started = time.perf_counter()
    out.mkdir(parents=True, exist_ok=True)
    result = {"object_id": OBJECT_ID, "card": CARD, "command": "probe",
              "launch_sha": shared.e0._git("rev-parse", "HEAD"), "requested_launch_sha": launch_sha,
              "block_seed": seed, "evaluation_seed": BLOCKS[seed],
              "state_affine_convention": STATE_LAYOUT_NOTE,
              "constructions": {}, "status": "incomplete", "failure": None}
    try:
        for label, arm in PROBE_CONSTRUCTIONS:
            result["constructions"][label] = _probe_construction(label, arm, seed, out / label)
        scaled = result["constructions"]["scaled"]
        result[AFFINE_FIELD] = scaled["central_snapshot_state_affine"]
        result[BOUNDS_FIELD] = scaled["central_snapshot_state_bounds"]
        if result[AFFINE_FIELD] is None:
            raise ValueError("the scaled construction recorded no state affine")
        if result["constructions"]["unscaled"]["central_snapshot_state_affine"] is not None:
            raise ValueError("the unscaled construction must carry no affine")
        result["optimizer_steps"] = sum(c["optimizer_steps"] for c in result["constructions"].values())
        result["evaluation_episodes"] = sum(
            c["evaluation_episodes"] for c in result["constructions"].values())
        result["J_init"] = {label: c["J_init_mean"] for label, c in result["constructions"].items()}
        result["status"] = "complete"
    except Exception as exc:  # the partial facts stay recorded
        result["status"], result["failure"] = "incomplete", f"{type(exc).__name__}: {exc}"
    finally:
        CURRENT.update(input_scale_arm=None, admission=None, summary=None)
        if shared.base_summary is base_summary:
            shared.base_summary = _orig_base_summary
        result["wall_seconds"] = time.perf_counter() - started
        result["interpretation_limit"] = (
            "a forward measurement of the untrained policy, not a fit: zero optimizer steps, one "
            "evaluation panel per construction, one block; J_init is a level, never a comparison "
            "of learning")
        shared.write_json(out / "summary.json", result)
    print(json.dumps({"status": result["status"], "failure": result["failure"],
                      "block_seed": seed, "J_init": result.get("J_init"),
                      "optimizer_steps": result.get("optimizer_steps")}))
    return 0 if result["status"] == "complete" else 1


def probe_endpoint(summary):
    """Validated J_init of one probe: this object, zero steps, both constructions complete."""
    if summary.get("object_id") != OBJECT_ID or summary.get("command") != "probe":
        raise ValueError("not a probe of this object")
    if summary.get("status") != "complete" or int(summary.get("block_seed", -1)) not in BLOCKS:
        raise ValueError("incomplete probe or wrong block")
    if summary.get("optimizer_steps") != 0:
        raise ValueError("a probe that took an optimizer step is not a probe")
    if int(summary.get("evaluation_seed", -1)) != BLOCKS[int(summary["block_seed"])]:
        raise ValueError("the probe is not on this block's evaluation seed")
    if not summary.get("launch_sha") or summary.get("requested_launch_sha") != summary["launch_sha"]:
        raise ValueError("the probe does not record the source it was asked to run at")
    constructions = summary.get("constructions") or {}
    values = {}
    for label, _arm in PROBE_CONSTRUCTIONS:
        entry = constructions.get(label)
        if not isinstance(entry, dict) or entry.get("J_init_mean") is None:
            raise ValueError(f"the probe carries no {label} construction")
        if (entry.get("evaluation_lanes") != shared.EVAL_LANES or entry.get("horizon") != shared.HORIZON
                or entry.get("evaluation_episodes") != shared.EVAL_LANES):
            raise ValueError(f"the {label} construction is not the frozen evaluation panel")
        if not isinstance(entry.get("learner_config"), dict):
            raise ValueError(f"the {label} construction records no learner configuration")
        values[label] = float(entry["J_init_mean"])
    if constructions["unscaled"]["learner_config"] != constructions["scaled"]["learner_config"]:
        raise ValueError("the probe's two constructions differ in a recorded configuration field")
    return values


def probe_mismatch(probe, new_fit, flat_fit):
    """Why this probe's J_init may not be subtracted from these two fits, or None."""
    constructions = probe["constructions"]
    if constructions["scaled"]["learner_config"] != new_fit["learner_config"]:
        return "the probe's scaled construction is not the new fit's recorded configuration"
    if constructions["unscaled"]["learner_config"] != flat_fit["learner_config"]:
        return "the probe's unscaled construction is not the reference fit's recorded configuration"
    if probe.get(AFFINE_FIELD) != new_fit.get(AFFINE_FIELD):
        return "the probe's state affine is not the new fit's"
    if probe["launch_sha"] != new_fit["launch_sha"]:
        return "the probe and the new fit ran at different sources"
    return None


# ---------------------------------------------------------------------------
# reduce
# ---------------------------------------------------------------------------


def displacement_parts(summary, rollout):
    """Split the recorded actor displacement into its log-std and network parts.

    The log-std parameter is the only actor parameter whose movement the recorded action entropy
    determines: for a diagonal Gaussian of `ACTION_DIMENSIONS` components at equal scale,
    log sigma = H / d - 0.5 ln(2 pi e), so its relative displacement is
    sqrt(d) |H / d - 1.4189| / ||theta_0||. The rest is orthogonal to it in the parameter vector,
    so the network part is sqrt(total^2 - logstd^2).
    """
    row = summary["training_rows"][rollout - 1]
    total = (row.get("relative_initialization_displacement") or {}).get("discoverer_actor")
    action_entropy = (row.get("losses") or {}).get("action_entropy")
    norm = (summary.get("initial_parameter_norms") or {}).get("discoverer_actor")
    result = {"rollout": rollout, "total": total, "action_entropy": action_entropy,
              "initial_actor_parameter_norm": norm, "logstd_part": None, "network_part": None,
              "clamped_at_zero": None}
    recorded_dimensions = (summary.get("learner_config") or {}).get("action_dim")
    if recorded_dimensions is not None and int(recorded_dimensions) != ACTION_DIMENSIONS:
        result["failure"] = "the recorded action dimension is not the one the log-std correction assumes"
        return result
    if total is None or action_entropy is None or not norm:
        result["failure"] = ("the recorded inputs of the log-std correction are incomplete: the "
                             "displacement, the action entropy or the initial actor norm is missing")
        return result
    logstd = (math.sqrt(ACTION_DIMENSIONS)
              * abs(action_entropy / ACTION_DIMENSIONS - GAUSSIAN_ENTROPY_PER_DIMENSION) / norm)
    difference = float(total) ** 2 - logstd ** 2
    result.update(logstd_part=logstd, network_part=math.sqrt(max(difference, 0.)),
                  clamped_at_zero=bool(difference < 0.),
                  constant=GAUSSIAN_ENTROPY_PER_DIMENSION, action_dimensions=ACTION_DIMENSIONS)
    return result


def fit_row(summary, scores):
    level = {r: float(np.mean(scores[r])) for r in PANEL_ROLLOUTS}
    return {"J_by_rollout": {str(r): level[r] for r in PANEL_ROLLOUTS},
            "J_early_window": float(np.mean([level[r] for r in EARLY_PANELS])),
            "J_late_window": float(np.mean([level[r] for r in LATE_PANELS])),
            "endpoint_scores_J": np.asarray(scores[ROLLOUTS], dtype=np.float64).tolist(),
            "object_id": summary["object_id"], "launch_sha": summary["launch_sha"],
            "lr_discoverer_actor": summary["learner_config"].get("lr_discoverer_actor"),
            entropy.ENTROPY_FIELD: summary["learner_config"].get(entropy.ENTROPY_FIELD),
            "diagnostics": update.diagnostics(summary),
            "actor_displacement_parts": {str(r): displacement_parts(summary, r) for r in (1, ROLLOUTS)},
            "counts": summary["counts"], "optimizer_calls": summary["optimizer_calls"],
            "wall_seconds_before_publication": summary.get("wall_seconds_before_publication"),
            "peak_rss_bytes": summary.get("peak_rss_bytes")}


def reduce_fits(summaries, references, probes=()):
    """Three new fits; the CF_E0005 and D1280 fits of the three blocks; optionally three probes."""
    rows, sources, failures, supplied = {}, {}, {}, set()
    for summary, side in [(s, "new") for s in summaries] + [(s, "reference") for s in references]:
        seed = int(summary.get("block_seed", -1))
        label = (summary.get("input_scale_arm") if side == "new"
                 else summary.get("entropy_arm") or summary.get("factorial_arm"))
        try:
            arm, values = ((label, fit_endpoint(summary)) if side == "new"
                           else update.reference_endpoint(summary))
        except (KeyError, TypeError, ValueError) as exc:
            arm, values = label, None
            failures[(seed, arm)] = str(exc)
        if (seed, arm, side) in supplied:  # a second fit of the same cell is never a choice
            raise ValueError("duplicate arm/block")
        supplied.add((seed, arm, side))
        if values is not None:
            rows[(seed, arm)], sources[(seed, arm)] = fit_row(summary, values), summary
    initial, probe_failures, probe_seeds, probe_sources = {}, {}, set(), {}
    for summary in probes:
        seed = int(summary.get("block_seed", -1))
        if seed in probe_seeds:
            raise ValueError("duplicate probe block")
        probe_seeds.add(seed)
        try:
            initial[seed] = probe_endpoint(summary)
            probe_sources[seed] = summary
        except (KeyError, TypeError, ValueError) as exc:
            probe_failures[seed] = str(exc)
    blocks, arms = [], {}
    for seed in sorted(BLOCKS):
        cells = [(seed, arm) for arm in (*INPUT_SCALE_ARMS, FLAT_REFERENCE, SKILL_REFERENCE)]
        blocks.append({"training_seed": seed, "evaluation_seed": BLOCKS[seed],
                       "arms": {arm: rows[(s, arm)] for s, arm in cells if (s, arm) in rows},
                       "missing_or_invalid_arms": {arm: failures.get((s, arm), "not supplied")
                                                   for s, arm in cells if (s, arm) not in rows},
                       "J_init": initial.get(seed)})
    for arm in INPUT_SCALE_ARMS:
        pairs = []
        for seed in sorted(BLOCKS):
            new, flat, skills = (seed, arm), (seed, FLAT_REFERENCE), (seed, SKILL_REFERENCE)
            entry = {"training_seed": seed}
            if not all(key in rows for key in (new, flat, skills)):
                entry.update(status="incomplete",
                             missing_operands=[a for _, a in (new, flat, skills) if (seed, a) not in rows])
            elif pair_view(sources[new]) != pair_view(sources[flat]):
                entry.update(status="incomplete", failure="unplanned difference from the CF_E0005 reference")
            elif entropy.host_view(sources[new]) != entropy.host_view(sources[skills]):
                entry.update(status="incomplete", failure="unplanned difference from the D1280 reference")
            else:
                entry["status"] = "complete"
                for name, value in (("J45", lambda cell: rows[cell]["J_by_rollout"][str(ROLLOUTS)]),
                                    ("late", lambda cell: rows[cell]["J_late_window"])):
                    entry[f"new_minus_flat_{name}"] = value(new) - value(flat)
                    entry[f"D1280_minus_new_{name}"] = value(skills) - value(new)
                    entry[f"D1280_minus_flat_{name}"] = value(skills) - value(flat)
                entry["late_minus_early_window"] = rows[new]["J_late_window"] - rows[new]["J_early_window"]
                entry["training_return_U_rollouts_35_45"] = {
                    a: rows[(seed, a)]["diagnostics"]["training_return_U_rollouts_35_45"]
                    for a in (arm, FLAT_REFERENCE, SKILL_REFERENCE)}
                entry["actor_displacement_parts"] = {
                    a: rows[(seed, a)]["actor_displacement_parts"]
                    for a in (arm, FLAT_REFERENCE, SKILL_REFERENCE)}
                mismatch = (probe_mismatch(probe_sources[seed], sources[new], sources[flat])
                            if seed in initial else None)
                if mismatch is not None:
                    entry["J_late_minus_J_init"], entry["probe_failure"] = None, mismatch
                elif seed in initial:
                    entry["J_late_minus_J_init"] = {
                        arm: rows[new]["J_late_window"] - initial[seed]["scaled"],
                        FLAT_REFERENCE: rows[flat]["J_late_window"] - initial[seed]["unscaled"]}
                    entry["J_init"] = dict(initial[seed])
                    entry["new_minus_flat_rise_from_J_init"] = (
                        entry["J_late_minus_J_init"][arm] - entry["J_late_minus_J_init"][FLAT_REFERENCE])
                elif seed in probe_failures:
                    entry["J_late_minus_J_init"] = None
            pairs.append(entry)
        complete = [p for p in pairs if p["status"] == "complete"]
        with_probe = [p for p in complete if p.get("J_late_minus_J_init")]
        arms[arm] = {"pairs": pairs, "lr_multiplier": LR_MULTIPLIER,
                     entropy.ENTROPY_FIELD: ENTROPY_COEFFICIENT,
                     "status": "complete" if len(complete) == len(BLOCKS) else "incomplete"}
        for name in ("new_minus_flat_J45", "D1280_minus_new_J45",
                     "new_minus_flat_late", "D1280_minus_new_late"):
            arms[arm][name] = entropy.described([p[name] for p in complete])
        arms[arm]["blocks_above_flat_in_late_window"] = int(sum(p["new_minus_flat_late"] > 0 for p in complete))
        arms[arm]["blocks_above_flat_at_J45"] = int(sum(p["new_minus_flat_J45"] > 0 for p in complete))
        arms[arm]["blocks_with_smaller_gap_than_flat"] = int(
            sum(p["D1280_minus_new_late"] < p["D1280_minus_flat_late"] for p in complete))
        arms[arm]["new_minus_flat_rise_from_J_init"] = (
            entropy.described([p["new_minus_flat_rise_from_J_init"] for p in with_probe])
            if with_probe else None)
        arms[arm]["blocks_with_larger_rise_from_J_init"] = int(
            sum(p["new_minus_flat_rise_from_J_init"] > 0 for p in with_probe))
    return {
        "object_id": OBJECT_ID, "card": CARD,
        "reference_object_ids": [entropy.OBJECT_ID, matched.OBJECT_ID],
        "launch_sha": shared.e0._git("rev-parse", "HEAD"),
        "status": "complete" if all(a["status"] == "complete" for a in arms.values()) else "incomplete",
        "quantity": "J45 = mean of the 32 final world scores; window means over panels 5-20 and "
                    "30-45; differences on the same training and evaluation seeds against "
                    "completed fits; J_init is the untrained level from the probe of the block",
        "declared_difference": (
            "central_snapshot_state_affine only; it is not one of the frozen configuration-snapshot "
            "fields, so every recorded configuration field must equal the CF_E0005 reference's"),
        "blocks": blocks, "arms": arms,
        "invalid_inputs": {f"{seed}:{arm}": text for (seed, arm), text in failures.items()},
        "invalid_probes": {str(seed): text for seed, text in probe_failures.items()},
        "interpretation_limit": (
            "exploration; three blocks; historical references that are not contemporaneous; these "
            "blocks were already used for every flat setting since B01, so no gap-size claim and no "
            "competence claim; no MEI verdict"),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fit = sub.add_parser("fit")
    fit.add_argument("--arm", choices=tuple(INPUT_SCALE_ARMS), required=True)
    fit.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    fit.add_argument("--launch-sha", help="must equal the admitted source SHA")
    fit.add_argument("--output-root", type=Path, required=True)
    probe = sub.add_parser("probe", help="zero-update forward measurement of both constructions")
    probe.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    probe.add_argument("--launch-sha", required=True, help="must equal the source HEAD; recorded")
    probe.add_argument("--output-root", type=Path, required=True)
    red = sub.add_parser("reduce")
    red.add_argument("--summaries", type=Path, nargs="+", required=True, help="this object's three fits")
    red.add_argument("--references", type=Path, nargs="+", required=True,
                     help="the completed CF_E0005 (B03) and D1280 (B01 stage 1) summaries of the three blocks")
    red.add_argument("--probes", type=Path, nargs="+", default=(),
                     help="optional: this object's probe summaries of the three blocks")
    red.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))

    if args.command == "fit":
        # Refuse an out-of-plan arm or block before the single-use admission is spent.
        plan_guard(args.arm, args.seed)
        # Nothing scientific has happened yet: no output, environment, learner or evaluator.
        # The literal direction is the launch kernel's guard contract; keep it inline.
        admission = require_admission(__file__, direction="flexible_skill_duration")
        if args.launch_sha is not None and args.launch_sha != admission["sha"]:
            parser.error("--launch-sha must equal the admitted source SHA")
        head = shared.e0._git("rev-parse", "HEAD")
        if head and head != admission["sha"]:
            parser.error("runner source HEAD is not the admitted SHA")
        return run_fit(args.arm, args.seed, args.output_root.resolve(),
                       admission={"sha": admission["sha"],
                                  "command_sha256": admission["command_sha256"]})

    if args.command == "probe":
        head = shared.e0._git("rev-parse", "HEAD")
        if not head or args.launch_sha != head:
            parser.error("--launch-sha must equal the source HEAD")
        return run_probe(args.seed, args.output_root.resolve(), launch_sha=args.launch_sha)

    args.output_root.mkdir(parents=True, exist_ok=True)
    result = reduce_fits([load(p) for p in args.summaries], [load(p) for p in args.references],
                         [load(p) for p in args.probes])
    result["input_summaries"] = [str(p) for p in args.summaries]
    result["reference_summaries"] = [str(p) for p in args.references]
    result["probe_summaries"] = [str(p) for p in args.probes]
    shared.write_json(args.output_root / "summary.json", result)
    print(json.dumps({"status": result["status"],
                      "new_minus_flat_late_mean": {a: v["new_minus_flat_late"]["mean"]
                                                   for a, v in result["arms"].items()},
                      "D1280_minus_new_late_mean": {a: v["D1280_minus_new_late"]["mean"]
                                                    for a, v in result["arms"].items()}}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
