"""FSD label map under sampled actions B10: does the label-to-J map survive the policy's own noise?

Exploration, next research judgment in the direction notebook:
docs/research/candidates/flexible_skill_duration/NOTES.md (2026-09-20 16:03 PDT, next research
judgment, B10).

B09 measured, at the trained D1280's fixed weights, what each *constant* skill label scores when
every agent holds it for the whole episode.  It found six distinct panels spanning about .13 to .22 J
on the three blocks.  Every one of those panels ran through the frozen evaluation route, which
executes the low level's *mean* action: the panel calls `agent.step(..., deterministic=True)`
(scripts/run_fsd_baseline_interruption_b01.py:224-225) and that flag reaches the diagonal Gaussian's
`action = dist.mean` branch (hmasd/r_mappo_utils.py:91-94).  Training never executes that action: it
executes a sample from the same Gaussian, whose standard deviation on this construction is about 2.9
action units per dimension.  B10 asks the one question that separates the two: do the labels' score
differences survive when the executed action is *sampled* as in training?

Two commands, both at fixed weights and both taking no optimizer step.

`probe` runs thirteen panels on one block's 32 evaluation worlds, in this fixed order:

  (a) `as_trained`                   the frozen route, nothing replaced, mean actions; then the
                                     B09/B08 faithful-load check, by exact equality of the 32 native
                                     world scores with the recorded rollout-45 panel.  The probe
                                     stops there if it fails, and the check is never relaxed
  (b) `sampled_constant_c_r{0,1}`    for each noise replicate r and each agent label c: B09's own
                                     `constant_c` label rule *and* a sampled low-level action

The label rule is B09's, unchanged and not re-implemented: the panels run through `b09.bound_rules()`
and `b09.run_rule_panel`, so the executed labels come from `b09.MapExecutionRule` and are checked by
`b09.check_rule_record` under B09's own rule name, and only the panel's *name* in this object's
records is `sampled_constant_c_r{r}`.  Nothing of this object ever enters B08's or B09's rule tables.

The action noise is imposed without editing frozen code, by wrapping the evaluator agent
*instance's* `_batched_select_action` for the duration of one panel - the same instance-attribute
pattern as `b08.ExecutionRule.attached`, removed in a `finally`, the class untouched - and calling
the frozen method with `deterministic=False`.  That is the narrowest wrapper that reaches the low
level alone: `step` passes its own `deterministic` to the coordinator at hmasd/agent.py:3249-3251 and
to the action selection at hmasd/agent.py:3266-3268, so wrapping `step` itself would also turn the
coordinator's argmax into a sample.  Under a constant-label rule the coordinator's labels are
overwritten anyway (see `SOURCE_NOTES['coordinator_determinism_under_a_constant_label']`), but
leaving that path exactly as B09 ran it keeps the sampled panel one change away from B09's own, and
that change is the executed action.

Sampling consumes the global torch generator.  The frozen `evaluate_panel` re-seeds every global
stream from the block's evaluation seed at its own start
(scripts/run_fsd_baseline_interruption_b01.py:202-205), so a seed applied before the call would be
overwritten and both replicates would draw the same stream.  This object therefore seeds *inside*
the panel, at its first action selection, from sha256 of `"<evaluation_seed>:<rule>"`, and restores
the Python, NumPy and torch states it saved in a `finally`.  A sampled panel is then a function of
(block, label, replicate) alone: reproducible, independent of the order the panels ran in, and
unable to move the `as_trained` panel, which stays bit-identical to the recorded one whether or not
sampled panels ran before it.

`reduce` is a pure reading of published summaries and carries no admission.  It reads this object's
three probes beside B09's three probes of the same three checkpoints and refuses a block whose
weights sha256, launch sha or `as_trained` world scores do not agree with B09's.

Nothing here is a fit: these are deployment-time interventions on fixed weights and say nothing
about what training under a fixed label would produce.
"""
import argparse
import hashlib
import inspect
import json
import random
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
import run_fsd_label_content_b08 as b08
import run_fsd_label_map_b09 as b09

shared = b09.shared
DIRECTION = "flexible_skill_duration"
OBJECT_ID = "FSD_LABEL_MAP_SAMPLED_B10"
CARD = ("docs/research/candidates/flexible_skill_duration/NOTES.md "
        "(2026-09-20 16:03 PDT, next research judgment, B10)")
BLOCKS = dict(b09.BLOCKS)  # 772803, 772903, 773003
SAVE_ARM = b09.SAVE_ARM  # the recorded stage-1 D1280 construction, unchanged
BASELINE_RULE = b09.BASELINE_RULE  # "as_trained"
N_LABELS = b09.N_LABELS  # 6; `run_probe` refuses any other width
REPLICATES = (0, 1)  # two independent noise draws of every label
WEIGHTS_NAME = b09.WEIGHTS_NAME
SIDECAR_NAME = b09.SIDECAR_NAME
# The two sizes the notebook entry's statements are declared with. .05 is the direction's declared
# size for a J difference; .08 is the entry's own "the gap is still visible" size.
E1_MARGIN = .05
E2_MARGIN = .08
PANEL_NOISE = b09.PANEL_NOISE  # .03: a mean-action panel's conditional evaluation noise
# The read-only capture that proves the executed actions are not the mean actions: B08's own actor
# hook at an even stride of the panel, and the mean action recomputed afterwards at the same inputs.
ACTION_CHECK_CALLS = 8
STD_RATIO_TOLERANCE = 2.  # the factor the executed-minus-mean RMS must sit within of the policy std


def sampled_rule(label, replicate):
    """The panel name that executes agent label `label` everywhere with sampled low-level actions."""
    return f"sampled_constant_{int(label)}_r{int(replicate)}"


def sampled_parts(name):
    """`(label, replicate)` of one of this object's sampled panels, or `(None, None)`."""
    if name not in SAMPLED_RULES:
        return None, None
    parts = name.split("_")
    return int(parts[2]), int(parts[3][1:])


SAMPLED_RULES = tuple(sampled_rule(label, replicate)
                      for replicate in REPLICATES for label in range(N_LABELS))
RULES = (BASELINE_RULE,) + SAMPLED_RULES  # 13 panels

SEED_DERIVATION = (
    "torch.manual_seed(int.from_bytes(sha256(f'{evaluation_seed}:{rule}').digest()[:8], 'big') "
    "% 2 ** 63)")

SOURCE_NOTES = {
    "deterministic_effects": (
        "everything the frozen evaluation route's `deterministic` flag controls, and nothing else. "
        "The panel calls `agent.step(..., deterministic=True)` "
        "(scripts/run_fsd_baseline_interruption_b01.py:224-225). `step` passes that one flag to two "
        "places: (1) hmasd/agent.py:3249-3251 `_batched_assign_skills`, which on this construction "
        "dispatches to `_batched_assign_skills_d2` (hmasd/agent.py:2085-2092) and reaches "
        "`SkillCoordinator.assign_partial_batch(..., deterministic=deterministic)` "
        "(hmasd/agent.py:2652-2661), where it selects argmax over sample for the team label "
        "(hmasd/networks.py:1072) and for each agent label (hmasd/networks.py:1099); and (2) "
        "hmasd/agent.py:3266-3268 `_batched_select_action`, which passes it as the fourth positional "
        "argument of the low-level actor's forward (hmasd/agent.py:3116-3123) through "
        "`SkillDiscoverer.forward` (hmasd/networks.py:1801-1807), `R_Actor.forward` "
        "(hmasd/networks.py:1463) and `ACTLayer.forward`'s Box branch "
        "(hmasd/r_mappo_utils.py:254-255) to `DiagGaussian.forward`, where `action = dist.mean if "
        "deterministic else dist.sample()` (hmasd/r_mappo_utils.py:91-94). It switches nothing else: "
        "`deterministic` occurs exactly once inside `_batched_select_action` (hmasd/agent.py:3120) "
        "and exactly once inside `_batched_assign_skills_d2` (hmasd/agent.py:2660), so the decision "
        "cadence, the GRU hidden-state bookkeeping (hmasd/agent.py:3187-3191), the observation and "
        "state normalisation (hmasd/agent.py:3062, 3074) and the ValueNorm denormalisation "
        "(hmasd/agent.py:3139-3140) run identically under either value"),
    "no_learner_state_written": (
        "`step` writes no buffer and takes no optimizer step under either value of `deterministic`: "
        "rollout storage is `store_rollout_step` (hmasd/agent.py:3331) and the high-level "
        "counterpart, and the evaluation panel calls neither - it calls only "
        "`agent.step(..., return_step_data=True, build_infos=False)` "
        "(scripts/run_fsd_baseline_interruption_b01.py:224-225) and then `env.step`. Train/eval mode "
        "is not a function of the flag either: `Evaluator._sync` calls `agent.train(False)` before "
        "every panel (scripts/run_flexible_skill_duration_e0.py:319-335), which is why the probe "
        "publishes `coordinator_training_mode`. The running observation and state normalisers are "
        "disabled on this construction (`use_obsnorm` and `use_statenorm` are False, so "
        "`_normalize_observations` and `_normalize_states` return their input unchanged, "
        "hmasd/agent.py:1502-1503, 1554-1555), and both agents' optimizer `step` raises for the whole "
        "command anyway (`run_fsd_flat_input_scale_b05._forbid_optimizer_steps`). Nothing needed "
        "neutralising: the flag reaches two label/action selections and no learner state at all"),
    "action_sampling_attachment": (
        "the evaluator agent instance's `_batched_select_action` (hmasd/agent.py:3007, called by the "
        "frozen `step` at hmasd/agent.py:3266-3268) is wrapped for the duration of one panel and the "
        "frozen method is called with `deterministic=False`; the wrapper is an instance attribute "
        "only and is removed in a `finally`, so the class is untouched, exactly as "
        "`b08.ExecutionRule.attached` wraps `_batched_assign_skills`. It is the narrowest callable "
        "that carries the flag to the low level alone: wrapping `step` would sample the "
        "coordinator's labels as well, and the actor's own forward is an `nn.Module.__call__` shared "
        "with the after-the-panel mean-action recomputation. The wrapper records the value the "
        "frozen caller asked for and refuses the panel unless it was `True`, which is the runtime "
        "proof that the panel really is the frozen evaluation route with this one flag replaced"),
    "coordinator_determinism_under_a_constant_label": (
        "the coordinator's own determinism cannot reach the executed behaviour of a constant-label "
        "panel, so this object leaves it at the frozen route's argmax. Under `constant_c` B09's rule "
        "overwrites the labels the coordinator returned - "
        "`scripts/run_fsd_label_map_b09.py:212-213` sets every agent label to c and the team label to "
        "`c % n_Z` - and writes them back into `env_team_skills`/`env_agent_skills` "
        "(scripts/run_fsd_label_map_b09.py:236-238); `step` then passes those returned labels, not "
        "the coordinator's, to `_batched_select_action` (hmasd/agent.py:3266-3268). The decision "
        "cadence is set before the coordinator runs (the caps, both interruption costs being "
        "infinite on this construction), so it does not depend on the flag either"),
    "sampling_seed": (
        "the executed action is drawn from the global torch generator "
        "(hmasd/r_mappo_utils.py:94 `dist.sample()` on a `FixedNormal`), so a sampled panel is "
        "seeded locally and deterministically: " + SEED_DERIVATION + ", applied *inside* the panel "
        "at its first action selection. It has to be inside, because the frozen `evaluate_panel` "
        "re-seeds Python, NumPy and torch from the block's evaluation seed at its own start "
        "(scripts/run_fsd_baseline_interruption_b01.py:202-205, "
        "run_fsd_uav_individual_renewal_b01.py:38-41): a seed applied before the call would be "
        "overwritten and the two replicates would draw the identical stream. Everything the panel "
        "does before its first action - the environment construction and reset - is therefore the "
        "frozen seeded route's, identical on every panel. The Python, NumPy and torch states are "
        "saved before the panel and restored in a `finally`, so a sampled panel cannot move any "
        "other panel: a sampled panel is a function of (block, label, replicate) alone, independent "
        "of the order the panels ran in, and `as_trained` is bit-identical to the recorded panel "
        "whether or not sampled panels ran before it. The environments draw from their own "
        "`numpy.random.RandomState` (envs/pettingzoo/uav_env.py:98, 223), not from the global stream"),
    "executed_action_check": (
        "the runtime proof that the panel executed samples and not means, taken read-only: B08's own "
        "actor hook (`b08.ActorCapture`, a forward hook on the evaluator's `skill_discoverer` that "
        "only copies) keeps the actor's own inputs and the action it returned at an even stride of "
        "the panel, and *after* the panel, under `torch.no_grad()` and preserved RNG, the "
        "deterministic action at exactly those inputs and that same held label is recomputed with "
        "B08's `_deterministic_actions`. The executed action is then compared with the mean action "
        "row by row. This is the comparison the entry asked for and it is feasible read-only, so no "
        "surrogate is used: the report carries the fraction of rows that differ from the mean, the "
        "root mean square of (executed - mean) per action dimension, and that RMS over the policy's "
        "own per-dimension standard deviation, which is 1 in expectation when the action is a draw "
        "from the policy's Gaussian. The panel is refused if no row differs from its mean, or if the "
        f"ratio leaves a factor of {STD_RATIO_TOLERANCE} of the policy standard deviation"),
    "action_standard_deviation": (
        "the policy's per-dimension action standard deviation, read from the actor at the saved "
        "weights by B08's own reader `b08.action_standard_deviation` "
        "(scripts/run_fsd_label_content_b08.py:667-693): exp of the state-independent `AddBias` "
        "log-std the diagonal Gaussian head uses (hmasd/r_mappo_utils.py:82, 89), with the head's "
        "own clamp where it has one. It is read after the `as_trained` panel, because the evaluator "
        "receives the loaded weights through `Evaluator._sync` inside the panel and not before it"),
    "replicate_noise": (
        "two panels of the same block and the same label differ only in the seed of the action "
        "draw, so `r1 - r0` is a paired draw of this panel's own sampling noise on the same 32 "
        "worlds. Its root mean square over the six labels is `sampled_panel_noise_estimate`: the "
        "size of the difference this measurement can resolve, from two replicates per label and "
        "nothing else. It is a noise estimate on 6 paired differences, not an interval"),
    "team_label_path": b09.SOURCE_NOTES["team_label_path"],
    "constant_write_back": b09.SOURCE_NOTES["constant_write_back"],
    "lane_to_world": b09.SOURCE_NOTES["lane_to_world"],
    "execution_rule_attachment": b09.SOURCE_NOTES["execution_rule_attachment"],
    "weight_transfer_to_evaluator": b09.SOURCE_NOTES["weight_transfer_to_evaluator"],
    "evaluation_route": b09.SOURCE_NOTES["evaluation_route"],
    "low_level_actor_label": b09.SOURCE_NOTES["low_level_actor_label"],
}

INTERPRETATION_LIMIT = (
    "a fixed-weight forward measurement, not a fit: zero optimizer steps, one block, one panel per "
    "(label, replicate) on the same 32 worlds and the same evaluation seeds. Exploration; three "
    "blocks; one checkpoint per block; the weights are fixed and nothing here is trained under a "
    "label or under action noise. The sampled panels isolate *action* noise alone: training also "
    "differs from these panels by drawing its skill labels instead of holding one, and by its own "
    "caps cadence, so a small or a large spread here says nothing about what a fit under a held "
    "label would do. The comparison with B09 is paired within a block - the same checkpoint, the "
    "same worlds, the same evaluation seeds - and a mean-action panel's conditional evaluation "
    f"noise on this direction is about {PANEL_NOISE} J, while the sampled panels carry their own "
    "noise, which the two replicates estimate. A fixed-weight panel is bit-reproducible only on the "
    "host that trained the checkpoint - B08's own local probe attempts failed the faithful load off "
    "that host - so this command runs on wsl_4070.")


def rule_definitions():
    """This object's thirteen panel definitions; the label rule of each is B09's own."""
    definitions = {BASELINE_RULE: b09.RULE_DEFINITIONS[BASELINE_RULE]}
    for name in SAMPLED_RULES:
        label, replicate = sampled_parts(name)
        definitions[name] = (
            f"B09's `{b09.constant_rule(label)}` label rule - at every step, in every lane, every "
            f"agent executes agent label {label} and the team label is {label} % n_Z, imposed by "
            "`b09.MapExecutionRule` and checked by `b09.check_rule_record` - with the low level's "
            f"action *sampled* from the policy's own Gaussian instead of taken at its mean, on noise "
            f"replicate {replicate}. " + SOURCE_NOTES["action_sampling_attachment"] + ". "
            + SOURCE_NOTES["sampling_seed"])
    return definitions


RULE_DEFINITIONS = rule_definitions()


# ---------------------------------------------------------------------------
# the action noise: one panel's low-level actions drawn from the policy's Gaussian
# ---------------------------------------------------------------------------


def panel_seed(evaluation_seed, rule):
    """The local torch seed of one sampled panel: a function of (block, label, replicate) alone."""
    digest = hashlib.sha256(f"{int(evaluation_seed)}:{rule}".encode("utf-8")).digest()[:8]
    return int.from_bytes(digest, "big") % 2 ** 63


def attachment_site():
    """file:line of the statement that wraps the evaluator agent's action selection."""
    lines, start = inspect.getsourcelines(SampledActions.attached)
    offsets = [index for index, text in enumerate(lines)
               if text.strip().startswith("agent._batched_select_action =")]
    line = start + offsets[0] if offsets else start
    return (f"{Path(__file__).resolve().relative_to(ROOT).as_posix()}:{line} wraps the evaluator "
            "agent instance's `_batched_select_action` for the duration of one panel; the frozen "
            "`step` calls it at hmasd/agent.py:3266-3268")


class SampledActions:
    """Run one panel's low-level actions as draws from the policy's Gaussian, and put everything back.

    The wrapper calls the frozen `_batched_select_action` with `deterministic=False` and changes
    nothing else about it: the hidden-state bookkeeping, the normalisation and the value
    denormalisation are the frozen method's own. It is an instance attribute, removed in a `finally`;
    the class is untouched. The global Python, NumPy and torch states are saved on the way in and
    restored on the way out, and the panel's own torch seed is applied at its first action selection.
    """

    def __init__(self, agent, rule, evaluation_seed):
        self.agent = agent
        self.rule = str(rule)
        self.evaluation_seed = int(evaluation_seed)
        self.seed = panel_seed(evaluation_seed, rule)
        self.calls = 0
        self.seeded_at_call = None
        self.requested = set()  # what the frozen caller asked for; must be {True}
        self.rng_restored = False

    @contextmanager
    def attached(self):
        agent = self.agent
        if "_batched_select_action" in agent.__dict__:
            raise ValueError("the evaluator agent's action selection is already wrapped")
        original = agent._batched_select_action
        py_state = random.getstate()
        np_state = np.random.get_state()
        torch_state = torch.get_rng_state().clone()

        def select(*args, **kwargs):
            if self.seeded_at_call is None:  # inside the panel: the frozen route has re-seeded
                self.seeded_at_call = self.calls
                torch.manual_seed(int(self.seed))
            self.calls += 1
            if "deterministic" in kwargs:
                self.requested.add(bool(kwargs["deterministic"]))
                return original(*args, **dict(kwargs, deterministic=False))
            if len(args) < 6:
                raise ValueError(
                    "the frozen action selection was called without its `deterministic` argument, "
                    "so this wrapper cannot say what the route asked for")
            self.requested.add(bool(args[5]))
            return original(*args[:5], False, *args[6:], **kwargs)

        agent._batched_select_action = select  # an instance attribute only; the class is untouched
        try:
            yield self
        finally:
            agent.__dict__.pop("_batched_select_action", None)
            random.setstate(py_state)
            np.random.set_state(np_state)
            torch.set_rng_state(torch_state)
            self.rng_restored = True

    def require_frozen_route(self):
        """Refuse a panel that was not the frozen evaluation route with this one flag replaced."""
        if not self.calls:
            raise ValueError(f"the {self.rule} panel selected no action, so nothing was sampled")
        if self.requested != {True}:
            raise ValueError(
                f"the {self.rule} panel's caller asked for deterministic="
                f"{sorted(self.requested)}, not the frozen evaluation route's deterministic=True")
        if self.seeded_at_call != 0:
            raise ValueError(f"the {self.rule} panel was seeded at call {self.seeded_at_call}")
        return self

    def record(self):
        return {
            "action_sampling": True, "rule": self.rule,
            "evaluation_seed": self.evaluation_seed, "torch_seed": int(self.seed),
            "seed_derivation": SEED_DERIVATION,
            "seeded_at_action_selection_call": self.seeded_at_call,
            "action_selection_calls": self.calls,
            "deterministic_requested_by_the_frozen_route": sorted(self.requested),
            "deterministic_executed": False,
            "rng_states_restored": bool(self.rng_restored),
            "attached_at": attachment_site(),
            "definition": SOURCE_NOTES["action_sampling_attachment"],
            "seed_note": SOURCE_NOTES["sampling_seed"],
            "effects": SOURCE_NOTES["deterministic_effects"],
            "learner_state": SOURCE_NOTES["no_learner_state_written"]}


def executed_action_check(agent, capture, standard_deviation, label):
    """Are the executed actions the policy's mean actions? Read-only, after the panel; raises if so.

    The mean action is recomputed at exactly the captured observation, actor GRU hidden state and
    held label with B08's own `_deterministic_actions`, so the comparison is row for row against the
    action the panel's own forward returned.
    """
    std = np.asarray(standard_deviation, dtype=np.float64)
    captured = list(capture.captured)
    if not captured:
        raise ValueError("the sampled panel captured no actor call, so nothing proves it sampled")
    rows, dimensions, equal_rows, maximum = 0, None, 0, 0.
    squares = None
    with shared.e0._preserve_rng(), torch.no_grad():
        for entry in captured:
            held = np.asarray(entry["agent_skill"].detach().cpu().numpy(),
                              dtype=np.int64).reshape(-1)
            if set(held.tolist()) != {int(label)}:
                raise ValueError(
                    f"the captured rows do not all hold label {label}: {sorted(set(held.tolist()))}")
            mean = b08._deterministic_actions(
                agent.skill_discoverer, entry, [int(label)])[:, 0, :].numpy()
            executed = entry["action"].detach().double().numpy()
            if executed.shape != mean.shape:
                raise ValueError("the executed and the recomputed mean actions differ in shape")
            difference = executed - mean
            if dimensions is None:
                dimensions = int(difference.shape[1])
                squares = np.zeros(dimensions, dtype=np.float64)
            elif int(difference.shape[1]) != dimensions:
                raise ValueError("the captured actions change width between calls")
            rows += int(difference.shape[0])
            squares += (difference ** 2).sum(axis=0)
            equal_rows += int((np.abs(difference).max(axis=1) == 0.).sum())
            maximum = max(maximum, float(np.abs(difference).max()))
    rms = np.sqrt(squares / max(rows, 1))
    ratio = rms / std
    within = bool(np.all(ratio <= STD_RATIO_TOLERANCE) and np.all(ratio >= 1. / STD_RATIO_TOLERANCE))
    if equal_rows == rows:
        raise ValueError(
            "every executed action equals the policy's mean action, so the panel did not sample")
    if not within:
        raise ValueError(
            "the executed actions sit at "
            f"{[round(float(value), 4) for value in ratio]} of the policy's own action standard "
            f"deviation, outside a factor of {STD_RATIO_TOLERANCE} of it")
    return {
        "rows": rows, "captured_calls": len(captured), "action_dimensions": dimensions,
        "rows_equal_to_the_mean_action": equal_rows,
        "fraction_of_rows_differing_from_the_mean_action": (rows - equal_rows) / max(rows, 1),
        "rms_executed_minus_mean_per_dimension": rms.tolist(),
        "action_standard_deviation_per_dimension": std.tolist(),
        "rms_executed_minus_mean_over_std_per_dimension": ratio.tolist(),
        "rms_executed_minus_mean_over_std_mean": float(ratio.mean()),
        "within_the_std_tolerance": within,
        "std_tolerance_factor": STD_RATIO_TOLERANCE,
        "max_absolute_executed_minus_mean": maximum,
        "comparison": "executed action against the recomputed mean action at the same input",
        "definition": SOURCE_NOTES["executed_action_check"],
        "standard_deviation_source": SOURCE_NOTES["action_standard_deviation"]}


def run_rule_panel(name, learner, evaluator, summary, out, index, *, evaluation_seed,
                   standard_deviation=None):
    """One panel: B09's own rule panel, with this object's action noise where the name asks for it."""
    label, replicate = sampled_parts(name)
    if label is None:  # `as_trained`: B09's panel exactly, mean actions, nothing replaced
        return b09.run_rule_panel(name, learner, evaluator, summary, out, index,
                                  evaluation_seed=evaluation_seed)
    if standard_deviation is None:
        raise ValueError("a sampled panel needs the policy's own action standard deviation")
    constant = b09.constant_rule(label)
    sampler = SampledActions(evaluator.agent, name, evaluation_seed)
    capture = b08.ActorCapture(evaluator.agent, capture_calls=ACTION_CHECK_CALLS)
    with sampler.attached():
        with capture.attached():
            record = b09.run_rule_panel(constant, learner, evaluator, summary, out, index,
                                        evaluation_seed=evaluation_seed)
    sampler.require_frozen_route()
    record = dict(record)
    record.update({
        "rule": name, "action_sampling": True, "replicate": int(replicate),
        "label": int(label), "label_rule": constant,
        "label_rule_definition": b09.RULE_DEFINITIONS[constant],
        "definition": RULE_DEFINITIONS[name],
        "action_sampling_record": sampler.record(),
        "executed_action_check": executed_action_check(
            evaluator.agent, capture, standard_deviation, label),
        "actor_capture": capture.provenance(),
        "actor_capture_deterministic_arguments": sorted(
            {bool(entry["deterministic"]) for entry in capture.captured})})
    return record


# ---------------------------------------------------------------------------
# the readings taken from the panels
# ---------------------------------------------------------------------------


SAMPLED_RANKING_DEFINITION = (
    "the labels ranked by their sampled panel J, averaged over the two noise replicates of the same "
    "block, the lowest label breaking an exact tie; `max_minus_min` is the spread of those replicate "
    "means over the six labels. Two panels per label on the same 32 worlds and the same evaluation "
    "seeds, so every comparison is paired within the block; `sampled_panel_noise_estimate` is the "
    "size this measurement can resolve")


def sampled_map(j_by_rule):
    """Per label: the two replicate panels, their mean, and the replicate difference r1 - r0."""
    replicates = {label: [float(j_by_rule[sampled_rule(label, r)]) for r in REPLICATES]
                  for label in range(N_LABELS)}
    means = {label: float(np.mean(replicates[label])) for label in range(N_LABELS)}
    differences = {label: replicates[label][1] - replicates[label][0] for label in range(N_LABELS)}
    return replicates, means, differences


def noise_estimate(differences):
    """The RMS over the labels of the replicate difference: this panel's own sampling noise."""
    values = np.asarray([differences[label] for label in sorted(differences)], dtype=np.float64)
    return float(np.sqrt(float((values ** 2).mean()))) if values.size else None


def sampled_reading(j_by_rule, baseline):
    """The whole sampled label map of one block: replicates, means, spread, ranking and noise."""
    replicates, means, differences = sampled_map(j_by_rule)
    best = b09.best_constant({b09.constant_rule(label): means[label]
                              for label in range(N_LABELS)}, baseline)
    best["definition"] = SAMPLED_RANKING_DEFINITION
    return {
        "sampled_J_by_label": {str(label): means[label] for label in range(N_LABELS)},
        "sampled_J_by_label_and_replicate": {
            str(label): {str(r): replicates[label][index] for index, r in enumerate(REPLICATES)}
            for label in range(N_LABELS)},
        "sampled_J_minus_as_trained_by_label": {
            str(label): means[label] - baseline for label in range(N_LABELS)},
        "replicate_difference_by_label": {str(label): differences[label]
                                          for label in range(N_LABELS)},
        "sampled_panel_noise_estimate": noise_estimate(differences),
        "sampled_max_minus_min": best["max_minus_min"],
        "sampled_ranking": list(best["ranking"]),
        "sampled_best_constant": best,
        "sampled_map_definitions": {
            "sampled_J_by_label": SAMPLED_RANKING_DEFINITION,
            "replicate_difference": SOURCE_NOTES["replicate_noise"],
            "sampled_panel_noise_estimate": SOURCE_NOTES["replicate_noise"]}}


def lead_over_the_others(values, label):
    """One label's J minus the mean of the other five, on the same block and the same worlds."""
    others = [values[other] for other in sorted(values) if other != label]
    return float(values[label] - np.mean(others)) if others else None


def lead_over_the_next_best(values, label):
    """One label's J minus the best of the other five: negative where that label is not the best."""
    others = [values[other] for other in sorted(values) if other != label]
    return float(values[label] - max(others)) if others else None


def _ranks(values):
    """Ordinary ranks, ties sharing their average rank."""
    values = list(values)
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks, position = [0.] * len(values), 0
    while position < len(order):
        stop = position
        while stop + 1 < len(order) and values[order[stop + 1]] == values[order[position]]:
            stop += 1
        average = (position + stop) / 2. + 1.
        for index in range(position, stop + 1):
            ranks[order[index]] = average
        position = stop + 1
    return ranks


def spearman(first, second):
    """Spearman's rank correlation of two equal-length vectors; None where either is constant."""
    first, second = list(first), list(second)
    if len(first) != len(second) or len(first) < 2:
        return None
    a, b = np.asarray(_ranks(first)), np.asarray(_ranks(second))
    a, b = a - a.mean(), b - b.mean()
    denominator = float(np.sqrt(float((a ** 2).sum()) * float((b ** 2).sum())))
    return float((a * b).sum() / denominator) if denominator > 0. else None


# ---------------------------------------------------------------------------
# the probe
# ---------------------------------------------------------------------------


def run_probe(seed, weights, out, launch_sha=None):
    """One block: B09's construction and saved weights, thirteen panels, no update."""
    if seed not in BLOCKS:
        raise SystemExit("this object probes blocks 772803, 772903 and 773003")
    b08.bind()  # B08's own probe binding: the frozen runner's construction, this object's panels
    started = time.perf_counter()
    evaluation_seed = BLOCKS[seed]
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "object_id": OBJECT_ID, "card": CARD, "command": "probe",
        "launch_sha": shared.e0._git("rev-parse", "HEAD"), "requested_launch_sha": launch_sha,
        "arm": SAVE_ARM, "block_seed": seed, "evaluation_seed": evaluation_seed,
        "weights": str(weights), "rules": list(RULES), "labels": N_LABELS,
        "replicates": [int(value) for value in REPLICATES],
        "construction_source": (
            f"{b08.OBJECT_ID} {SAVE_ARM} (the recorded stage-1 {b08.D_REFERENCE} construction): the "
            "frozen baseline x interruption B01 runner with B08's identities bound, B08's saved "
            f"final weights loaded, zero optimizer steps; {b09.OBJECT_ID}'s constant-label rules "
            "bound for the panels, and this object's action noise on the sampled ones"),
        "reference_object_ids": [b09.OBJECT_ID, b08.OBJECT_ID],
        "recorded_d1280_summary": str(b08.RECORDED_FITS[seed]),
        "reference_summary": str(b08.REFERENCE_FITS[seed]),
        "host_geometry": b08.host_geometry(),
        "frozen_host_geometry": b08.host_geometry() == b08.probe.FROZEN_GEOMETRY,
        "source_notes": dict(SOURCE_NOTES),
        "sampled_panel_seeds": {
            name: {"torch_seed": panel_seed(evaluation_seed, name),
                   "derivation": SEED_DERIVATION} for name in SAMPLED_RULES},
        "status": "incomplete", "failure": None, "faithful_load": None}
    construction = out / "construction"
    try:
        _run(result, seed, evaluation_seed, construction, Path(weights))
        result["status"] = "complete"
    except Exception as exc:  # the partial facts stay recorded
        result["status"], result["failure"] = "incomplete", f"{type(exc).__name__}: {exc}"
    finally:
        result["wall_seconds"] = time.perf_counter() - started
        result["interpretation_limit"] = INTERPRETATION_LIMIT
        shared.write_json(out / "summary.json", result)
    print(json.dumps({
        "status": result["status"], "failure": result["failure"], "block_seed": seed,
        "faithful_load": (result.get("faithful_load") or {}).get("faithful_load"),
        "J_by_rule": {name: (result.get("rules_measured") or {}).get(name, {}).get("J_mean")
                      for name in RULES},
        "sampled_J_by_label": result.get("sampled_J_by_label"),
        "sampled_max_minus_min": result.get("sampled_max_minus_min"),
        "sampled_panel_noise_estimate": result.get("sampled_panel_noise_estimate"),
        "optimizer_steps": result.get("optimizer_steps"),
        "wall_seconds": result.get("wall_seconds")}))
    return 0 if result["status"] == "complete" else 1


def _run(result, seed, evaluation_seed, out, weights):
    """Build as B09's probe does, load its weights, run the thirteen panels, then read them."""
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

    summary = shared.base_summary(b08.ARMS[SAVE_ARM][0], training_seed=seed,
                                  evaluation_seed=evaluation_seed, object_id=OBJECT_ID,
                                  card=CARD, caps=None)
    summary.update(command="probe", factorial_arm=SAVE_ARM, block_seed=seed, rollouts=0,
                   panel_rollouts=[], panels=[],
                   coordinator_batch_size=b08.ARMS[SAVE_ARM][1], ordinary_wall_plan_seconds=None,
                   cost_law="zero optimizer steps; one evaluation panel per execution rule")
    out.mkdir(parents=True, exist_ok=True)
    envs, learner, _theta0, counters = b01.build_learner(SAVE_ARM, summary, out, seed)
    learner_differences = b08.require_recorded_construction(
        summary["learner_config"], recorded["learner_config"], "learner configuration")
    restore = b08.scale._forbid_optimizer_steps(learner)
    try:
        learner.load_model(str(weights))  # the agent's own load routine
        learner.train(False)
        evaluator = b01.build_evaluator(SAVE_ARM, summary, out, evaluation_seed)
        evaluation_differences = b08.require_recorded_construction(
            summary["evaluation_config"], recorded["evaluation_config"], "evaluation configuration")
        restore += b08.scale._forbid_optimizer_steps(evaluator.agent)
        config = evaluator.agent.config
        if (int(config.n_z), int(config.n_Z)) != (N_LABELS, N_LABELS):
            raise ValueError(
                f"the construction carries n_z={int(config.n_z)}, n_Z={int(config.n_Z)}, not the "
                f"{N_LABELS} labels this object's constant panels are defined on")
        measured, standard_deviation = {}, None
        with b09.bound_rules():
            for index, name in enumerate(RULES):
                measured[name] = run_rule_panel(name, learner, evaluator, summary, out, index,
                                                evaluation_seed=evaluation_seed,
                                                standard_deviation=standard_deviation)
                result["rules_measured"] = dict(measured)
                if name == BASELINE_RULE:
                    faithful = b09.faithful_load_record(summary["panels"][-1], reference)
                    result["faithful_load"] = faithful
                    if not faithful["faithful_load"]:
                        raise ValueError(
                            "the loaded weights do not reproduce the recorded panel; first "
                            f"differing world index {faithful['first_differing_world']}")
                    # After the panel: the evaluator receives the loaded weights inside it.
                    standard_deviation, std_note = b08.action_standard_deviation(
                        evaluator.agent.skill_discoverer.actor)
                    result["action_standard_deviation"] = dict(
                        std_note, per_dimension=[float(value) for value in standard_deviation],
                        mean=float(np.mean(standard_deviation)),
                        reader=SOURCE_NOTES["action_standard_deviation"])
    finally:
        for optimizer, original in restore:
            optimizer.step = original

    learner_calls = shared.optimizer_counts(counters)
    steps = sum(learner_calls.values()) + sum(
        sum(panel["evaluator_optimizer_calls"].values()) for panel in summary["panels"])
    if steps != 0:
        raise ValueError("the probe is defined by taking no optimizer step")
    j_by_rule = {name: float(measured[name]["J_mean"]) for name in RULES}
    baseline = j_by_rule[BASELINE_RULE]
    reading = sampled_reading(j_by_rule, baseline)
    result.update({
        "optimizer_steps": steps, "optimizer_calls": learner_calls,
        "rules_measured": measured,
        "J_by_rule": j_by_rule,
        "J_minus_as_trained": {name: j_by_rule[name] - baseline for name in RULES},
        "evaluation_panels": len(summary["panels"]),
        "evaluation_episodes": summary["counts"]["evaluation_episodes"],
        "evaluation_steps": summary["counts"]["evaluation_steps"],
        "evaluation_lanes": shared.EVAL_LANES, "horizon": shared.HORIZON,
        "evaluation_route_determinism": {
            "coordinator_labels": (
                "argmax on every panel: the frozen route asks for `deterministic=True` and this "
                "object never changes the coordinator's path"),
            "low_level_action": (
                "the Gaussian's mean on `as_trained`; a draw from the same Gaussian on the twelve "
                "sampled panels"),
            "source": SOURCE_NOTES["deterministic_effects"],
            "under_a_constant_label": SOURCE_NOTES["coordinator_determinism_under_a_constant_label"],
            "learner_state": SOURCE_NOTES["no_learner_state_written"]},
        "training_lanes_constructed": len(envs),
        "training_lane_seeds": summary["training_lane_seeds"],
        "evaluation_lane_seeds": summary["evaluation_lane_seeds"],
        "construction_summary": "construction/summary.json",
        "learner_config": summary["learner_config"],
        "evaluation_config": summary["evaluation_config"],
        "learner_config_differences_from_recorded_d1280": learner_differences,
        "evaluation_config_differences_from_recorded_d1280": evaluation_differences,
        "coordinator_training_mode": bool(evaluator.agent.skill_coordinator.training),
        "rule_definitions": dict(RULE_DEFINITIONS)})
    result.update(reading)
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
    measured = summary.get("rules_measured") or {}
    if sorted(measured) != sorted(RULES):
        raise ValueError("the probe does not carry all thirteen panels")
    if summary.get("optimizer_steps") != 0:
        raise ValueError("the probe took an optimizer step")
    scores = {name: list(measured[name]["J_world_scores"]) for name in RULES}
    widths = {len(value) for value in scores.values()}
    if len(widths) != 1:
        raise ValueError("the probe's panels do not all carry the same worlds")
    for name in SAMPLED_RULES:
        record = measured[name]
        if not record.get("action_sampling"):
            raise ValueError(f"the {name} panel does not record that it sampled its actions")
        check = record.get("executed_action_check") or {}
        if not check.get("rows") or check.get("rows_equal_to_the_mean_action") == check.get("rows"):
            raise ValueError(f"the {name} panel carries no proof that it left the mean action")
    j_by_rule = {name: float(measured[name]["J_mean"]) for name in RULES}
    return {
        "block_seed": seed, "launch_sha": summary.get("launch_sha"),
        "weights_sha256": (summary.get("weights_record") or {}).get("sha256"),
        "faithful_load": True, "worlds": next(iter(widths)),
        "J_by_rule": j_by_rule,
        "J_world_scores": scores,
        "J_minus_as_trained": {name: j_by_rule[name] - j_by_rule[BASELINE_RULE] for name in RULES},
        "executed_action_checks": {
            name: measured[name]["executed_action_check"] for name in SAMPLED_RULES},
        "action_standard_deviation": summary.get("action_standard_deviation"),
        "published_sampled_max_minus_min": summary.get("sampled_max_minus_min"),
        "published_sampled_panel_noise_estimate": summary.get("sampled_panel_noise_estimate"),
        "wall_seconds": summary.get("wall_seconds")}


def b09_probe_row(summary):
    """One B09 probe of the same checkpoint, read by B09's own validated reader."""
    row = b09.probe_row(summary)  # refuses an incomplete, unfaithful or rule-short probe
    row["as_trained_world_scores"] = list(row["J_world_scores"][BASELINE_RULE])
    row["mean_action_J_by_label"] = {
        label: float(row["J_by_rule"][b09.constant_rule(label)]) for label in range(N_LABELS)}
    return row


def block_reading(row, other):
    """One block: this object's sampled label map beside B09's own mean-action map."""
    j_by_rule = row["J_by_rule"]
    baseline = j_by_rule[BASELINE_RULE]
    reading = sampled_reading(j_by_rule, baseline)
    sampled = {label: float(reading["sampled_J_by_label"][str(label)])
               for label in range(N_LABELS)}
    mean_action = dict(other["mean_action_J_by_label"])
    mean_best = b09.best_constant({b09.constant_rule(label): mean_action[label]
                                   for label in range(N_LABELS)}, baseline)
    best_label = int(mean_best["label"])
    sampled_ranking = list(reading["sampled_ranking"])
    return {
        "J_as_trained": baseline,
        "b09_J_as_trained": float(other["J_by_rule"][BASELINE_RULE]),
        "mean_action_J_by_label": {str(label): mean_action[label] for label in range(N_LABELS)},
        "sampled_J_by_label": dict(reading["sampled_J_by_label"]),
        "sampled_J_by_label_and_replicate": dict(reading["sampled_J_by_label_and_replicate"]),
        "sampled_minus_mean_action_by_label": {
            str(label): sampled[label] - mean_action[label] for label in range(N_LABELS)},
        "mean_action_max_minus_min": float(mean_best["max_minus_min"]),
        "sampled_max_minus_min": float(reading["sampled_max_minus_min"]),
        "sampled_max_minus_min_minus_mean_action_max_minus_min": float(
            reading["sampled_max_minus_min"] - mean_best["max_minus_min"]),
        "mean_action_ranking": [int(label) for label in mean_best["ranking"]],
        "sampled_ranking": [int(label) for label in sampled_ranking],
        "rank_correlation": spearman([mean_action[label] for label in range(N_LABELS)],
                                     [sampled[label] for label in range(N_LABELS)]),
        "rank_correlation_definition": (
            "Spearman's rank correlation between the six labels' mean-action panel J (B09's probe of "
            "this checkpoint) and their sampled panel J (the mean of this object's two replicates), "
            "ties sharing their average rank; 1 is the same order, -1 the reverse, and None where "
            "either side is constant. Six paired points: it is a description of the order, not a "
            "test"),
        "best_mean_action_label": best_label,
        "best_mean_action_label_lead_under_mean_actions": lead_over_the_others(
            mean_action, best_label),
        "best_mean_action_label_lead_under_sampling": lead_over_the_others(sampled, best_label),
        "best_mean_action_label_lead_over_the_second_best_sampled_label": lead_over_the_next_best(
            sampled, best_label),
        "lead_definition": (
            "`lead_under_...` is B09's best mean-action label's J minus the *mean* of the other five "
            "labels' J on the same block, under mean actions and under sampling; "
            "`..._over_the_second_best_sampled_label` is instead that label's sampled J minus the "
            "best of the other five sampled J, which is negative where it is no longer the best. "
            "Paired within the block: the same checkpoint, the same 32 worlds, the same evaluation "
            "seeds"),
        "sampled_best_label": int(sampled_ranking[0]),
        "best_label_is_b09s": bool(int(sampled_ranking[0]) == best_label),
        "replicate_difference_by_label": dict(reading["replicate_difference_by_label"]),
        "sampled_panel_noise_estimate": reading["sampled_panel_noise_estimate"],
        "sampled_panel_noise_definition": SOURCE_NOTES["replicate_noise"],
        "published_sampled_max_minus_min": row["published_sampled_max_minus_min"],
        "sampled_max_minus_min_matches_the_published_one": bool(
            row["published_sampled_max_minus_min"] == reading["sampled_max_minus_min"]),
        "executed_action_check_over_std": {
            name: (row["executed_action_checks"][name] or {}).get(
                "rms_executed_minus_mean_over_std_mean") for name in SAMPLED_RULES},
        "action_standard_deviation": (row["action_standard_deviation"] or {}).get("per_dimension"),
        "weights_sha256": row["weights_sha256"],
        "worlds": row["worlds"]}


def block_outcome(reading):
    """E1, E2 or neither, from this block's sampled spread alone; arithmetic, not a verdict."""
    spread = reading.get("sampled_max_minus_min")
    if spread is None:
        return None
    if spread < E1_MARGIN:
        return "E1"
    return "E2" if spread > E2_MARGIN else "neither"


def prediction_rows(readings):
    """The statements the notebook entry declared before the run, counted where they are read.

    Arithmetic on the blocks that were read, with the statement each count belongs to. A count is
    not a weight of evidence, and none of these margins is a decision rule.
    """
    declared = {
        "E1_the_sampled_spread_is_below_the_margin_on_every_block": {
            "blocks": tuple(sorted(BLOCKS)),
            "statement": ("the gap is invisible under training noise: on all three blocks the "
                          "sampled spread over the six labels, max minus min on the replicate "
                          f"means, is smaller than {E1_MARGIN} J"),
            "value": lambda r: r["sampled_max_minus_min"],
            "holds": lambda value: value < E1_MARGIN,
            "value_definition": ("max minus min over the six labels of the sampled panel J, each "
                                 "the mean of that label's two noise replicates")},
        "E1_the_best_mean_action_labels_sampled_lead_on_772903_is_below_the_margin": {
            "blocks": (772903,),
            "statement": ("the gap is invisible under training noise: on block 772903 the label "
                          "B09 measured as the best under mean actions - label 1 on that block's "
                          "recorded B09 probe - leads the second-best sampled label by less than "
                          f"{E1_MARGIN} J"),
            "value": lambda r: r["best_mean_action_label_lead_over_the_second_best_sampled_label"],
            "holds": lambda value: value < E1_MARGIN,
            "value_definition": ("B09's best mean-action label's sampled J minus the best of the "
                                 "other five labels' sampled J on that block; the label itself is "
                                 "published as `best_mean_action_label`")},
        "E2_the_sampled_spread_is_above_the_margin_on_every_block": {
            "blocks": tuple(sorted(BLOCKS)),
            "statement": ("the gap is still visible: on all three blocks the sampled spread over "
                          f"the six labels is larger than {E2_MARGIN} J"),
            "value": lambda r: r["sampled_max_minus_min"],
            "holds": lambda value: value > E2_MARGIN,
            "value_definition": ("max minus min over the six labels of the sampled panel J, each "
                                 "the mean of that label's two noise replicates")},
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
    rows["outcome_by_block"] = {
        str(seed): block_outcome(reading) for seed, reading in sorted(readings.items())}
    rows["counting_note"] = (
        "the counts are the arithmetic of statements declared before the run, on the blocks that "
        f"were read. A sampled spread between {E1_MARGIN} and {E2_MARGIN} J is neither E1 nor E2, "
        "which `outcome_by_block` reports per block. A count of three blocks is not an interval and "
        "not a weight of evidence, and no margin here is a decision rule; a mean-action panel's "
        f"conditional evaluation noise on this direction is about {PANEL_NOISE} J and the sampled "
        "panels' own noise is estimated by the two replicates")
    return rows


def reduce_inputs(probes, b09_probes):
    """This object's three probes beside B09's three probes of the same three checkpoints."""
    b08.bind()  # the pure reading B08's own reduce takes: identities only, nothing wrapped
    shas = {summary.get("launch_sha") for summary in probes}
    if len(shas) > 1:
        raise ValueError(f"mixed launch shas among the probes: {sorted(str(s) for s in shas)}")
    b09_shas = {summary.get("launch_sha") for summary in b09_probes}

    rows, failures, seen = {}, {}, set()
    for summary in probes:
        seed = int(summary.get("block_seed", -1))
        if seed in seen:  # a second probe of the same block is never a choice
            raise ValueError("duplicate probe block")
        seen.add(seed)
        try:
            rows[seed] = probe_row(summary)
        except (KeyError, TypeError, ValueError) as exc:
            failures[seed] = str(exc)

    others, other_failures, other_seen = {}, {}, set()
    for summary in b09_probes:
        seed = int(summary.get("block_seed", -1))
        if seed in other_seen:
            raise ValueError("duplicate B09 probe block")
        other_seen.add(seed)
        try:
            others[seed] = b09_probe_row(summary)
        except (KeyError, TypeError, ValueError) as exc:
            other_failures[seed] = str(exc)

    blocks, readings = [], {}
    for seed in sorted(BLOCKS):
        entry = {"training_seed": seed, "evaluation_seed": BLOCKS[seed], "status": "incomplete",
                 "missing_or_invalid": {}}
        if seed not in rows:
            entry["missing_or_invalid"]["probe"] = failures.get(seed, "not supplied")
        if seed not in others:
            entry["missing_or_invalid"]["b09_probe"] = other_failures.get(seed, "not supplied")
        if seed in rows and seed in others:
            row, other = rows[seed], others[seed]
            entry["weights_match"] = bool(row["weights_sha256"]
                                          and row["weights_sha256"] == other["weights_sha256"])
            identical = row["J_world_scores"][BASELINE_RULE] == other["as_trained_world_scores"]
            entry["as_trained_identical_to_b09"] = bool(identical)
            if not entry["weights_match"]:
                entry["missing_or_invalid"]["weights"] = (
                    "this probe's weights sha256 is not the one B09's probe of the same block "
                    "recorded, so the two are not readings of one checkpoint")
            elif not identical:
                entry["missing_or_invalid"]["as_trained"] = (
                    "this probe's `as_trained` world scores are not B09's own, so the two probes "
                    "are not the same policy on the same worlds and the block is not read")
            else:
                entry["status"] = "complete"
                entry.update(block_reading(row, other))
                readings[seed] = entry
        else:
            entry["weights_match"] = None
            entry["as_trained_identical_to_b09"] = None
        blocks.append(entry)

    complete = [block for block in blocks if block["status"] == "complete"]
    across = b08._across
    result = {
        "object_id": OBJECT_ID, "card": CARD, "command": "reduce",
        "launch_sha": shared.e0._git("rev-parse", "HEAD"),
        "probe_launch_sha": next(iter(shas), None) if len(shas) == 1 else None,
        "b09_probe_launch_sha": next(iter(b09_shas), None) if len(b09_shas) == 1 else None,
        "reference_object_ids": [b09.OBJECT_ID, b08.OBJECT_ID],
        "status": "complete" if len(complete) == len(BLOCKS) else "incomplete",
        "arm": {"name": SAVE_ARM, "overrides": dict(b08.ARM_OVERRIDES[SAVE_ARM]),
                "coordinator_batch_size": b08.ARMS[SAVE_ARM][1],
                "caps": {"skill_cap_k_max": b08.ARM_CAPS[0], "team_cap_k_Z": b08.ARM_CAPS[1]}},
        "rules": list(RULES), "rule_definitions": dict(RULE_DEFINITIONS),
        "b09_rules": list(b09.RULES), "labels": N_LABELS,
        "replicates": [int(value) for value in REPLICATES],
        "quantity": (
            "J of a panel is the mean of its native world scores at the saved weights. A sampled "
            "label's J is the mean of its two noise replicates; a mean-action label's J is B09's own "
            "panel of the same checkpoint. Every comparison here is paired within a block: the same "
            "weights, the same 32 worlds and the same evaluation seeds, and the only difference "
            "between a sampled panel and B09's constant panel of the same label is that the low "
            "level executes a draw from its Gaussian instead of its mean"),
        "blocks": blocks,
        "blocks_read": len(complete),
        "invalid_probes": {str(seed): text for seed, text in failures.items()},
        "invalid_b09_probes": {str(seed): text for seed, text in other_failures.items()},
        "refusals": (
            "a batch of probes at more than one launch sha, a duplicate block among either set of "
            "probes, a summary that is not this object's probe, an incomplete probe, a probe "
            "without all thirteen panels or with an optimizer step, a probe whose sampled panel "
            "carries no proof that it left the mean action, a probe that did not establish a "
            "faithful load, a block whose B09 probe was not supplied or is not readable by B09's "
            "own reader, a block whose weights sha256 is not B09's probe's, and a block whose "
            "`as_trained` world scores are not exactly B09's"),
        "interpretation_limit": INTERPRETATION_LIMIT,
        "source_notes": dict(SOURCE_NOTES),
    }
    for key in ("sampled_max_minus_min", "mean_action_max_minus_min",
                "sampled_max_minus_min_minus_mean_action_max_minus_min",
                "rank_correlation", "sampled_panel_noise_estimate",
                "best_mean_action_label_lead_under_mean_actions",
                "best_mean_action_label_lead_under_sampling",
                "best_mean_action_label_lead_over_the_second_best_sampled_label"):
        result[key] = across(complete, lambda b, key=key: b[key])
    for label in range(N_LABELS):
        result[f"sampled_minus_mean_action_label_{label}"] = across(
            complete, lambda b, label=label: b["sampled_minus_mean_action_by_label"][str(label)])
    result["sampled_J_by_label"] = {
        str(label): across(complete, lambda b, label=label: b["sampled_J_by_label"][str(label)])
        for label in range(N_LABELS)}
    result["mean_action_J_by_label"] = {
        str(label): across(complete, lambda b, label=label: b["mean_action_J_by_label"][str(label)])
        for label in range(N_LABELS)}
    result["ranking_by_block"] = {
        str(block["training_seed"]): {"mean_action": block.get("mean_action_ranking"),
                                      "sampled": block.get("sampled_ranking")}
        for block in blocks}
    result["best_label_by_block"] = {
        str(block["training_seed"]): {"mean_action": block.get("best_mean_action_label"),
                                      "sampled": block.get("sampled_best_label")}
        for block in blocks}
    result["one_sampled_best_label_across_blocks"] = (
        complete[0]["sampled_best_label"]
        if complete and len({block["sampled_best_label"] for block in complete}) == 1
        else None)
    result["blocks_where_the_sampled_best_label_is_b09s"] = [
        int(block["training_seed"]) for block in complete if block["best_label_is_b09s"]]
    result["predictions"] = prediction_rows(readings)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prb = sub.add_parser("probe", help="zero-update execution of one block's saved weights")
    prb.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    prb.add_argument("--weights", type=Path, required=True,
                     help=f"B08's fit {WEIGHTS_NAME}; its {SIDECAR_NAME} must sit beside it")
    prb.add_argument("--launch-sha", required=True, help="must equal the source HEAD; recorded")
    prb.add_argument("--output-root", type=Path, required=True)
    red = sub.add_parser("reduce")
    red.add_argument("--probes", type=Path, nargs="+", required=True,
                     help="this object's three probe summaries")
    red.add_argument("--b09-probes", type=Path, nargs="+", required=True,
                     help="the B09 probe summaries of the same three checkpoints")
    red.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))

    if args.command == "probe":
        head = shared.e0._git("rev-parse", "HEAD")
        if not head or args.launch_sha != head:
            parser.error("--launch-sha must equal the source HEAD")
        return run_probe(args.seed, args.weights.resolve(), args.output_root.resolve(),
                         launch_sha=args.launch_sha)

    args.output_root.mkdir(parents=True, exist_ok=True)
    result = reduce_inputs([load(path) for path in args.probes],
                           [load(path) for path in args.b09_probes])
    result["input_probes"] = [str(path) for path in args.probes]
    result["input_b09_probes"] = [str(path) for path in args.b09_probes]
    shared.write_json(args.output_root / "summary.json", result)
    print(json.dumps({
        "status": result["status"], "blocks_read": result["blocks_read"],
        "sampled_max_minus_min": (result["sampled_max_minus_min"] or {}).get("mean"),
        "mean_action_max_minus_min": (result["mean_action_max_minus_min"] or {}).get("mean"),
        "rank_correlation": (result["rank_correlation"] or {}).get("mean"),
        "sampled_panel_noise_estimate": (result["sampled_panel_noise_estimate"] or {}).get("mean"),
        "best_label_by_block": result["best_label_by_block"],
        "predictions": {name: entry["blocks_holding"] for name, entry in
                        result["predictions"].items() if isinstance(entry, dict)
                        and "blocks_holding" in entry},
        "outcome_by_block": result["predictions"]["outcome_by_block"]}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
