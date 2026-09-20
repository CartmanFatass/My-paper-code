"""FSD label content B08: does the trained D1280's skill label carry behavioural content?

Exploration, prospective entry in the direction notebook:
docs/research/candidates/flexible_skill_duration/NOTES.md, "2026-09-20 05:45 PDT - prospective:
label content at fixed weights, B08 (explore; three fits that are exact D1280 reruns with the final
weights saved, then zero-fit probes)".

Three commands.

`fit` is the recorded stage-1 D1280 construction with *no* configuration difference at all: the
frozen baseline x interruption B01 runner's `("D0", 1280)` arm as the matched-information object
builds it, 45 rollouts, panels after 5, 10, ... 45, rebound to this object's identity exactly as
B07's `D_K10` arm is.  `make_config` re-runs `validate_config()` and `calculate_and_set_buffer_sizes()`
and refuses any snapshot difference from that construction; where the published stage-1 D1280 summary
of the block is readable it is compared field by field as well (B06's guard), and `reduce` makes that
comparison mandatory.  The only addition to the frozen route is that *after* `run_fit` has returned -
the collector loop, its 45 updates and the rollout-45 panel are all finished, so nothing can be
perturbed - the learner agent's final weights are written with the agent's own `save_model`
(hmasd/agent.py:7351) to `<output-root>/final_weights.pt`, and a sidecar `weights.json` records the
file's sha256, its size, the checkpoint's own keys and the fit's launch sha and block.  A fit that is
not `complete` saves nothing.  `*.pt` is gitignored; the checkpoint is a run artifact, not a source.
Proof that the addition changed nothing: all nine panels are bit-identical to the published
`b01_s1_d1280_<block>_a01` fit, which `reduce` reports per block.

`probe` takes no optimizer step (every optimizer `step` of both agents raises for the whole command)
and carries no admission: it is policy execution, recorded as exposure.  It builds the learner and
the evaluator exactly as a fit does, loads the saved checkpoint into the learner with the agent's own
`load_model` (hmasd/agent.py:7554) after verifying its sha256 against the sidecar, and then runs four
evaluation panels through the frozen `evaluate_panel`, whose own `Evaluator._sync`
(scripts/run_flexible_skill_duration_e0.py:319-335) is the route by which weights, the running
observation/state normalisers and the ValueNorm statistics reach the evaluator, followed by
`train(False)` and a per-lane `reset_env_state`.  That is the same transfer the fit's panels used, so
the first panel must reproduce the recorded rollout-45 panel's 32 world scores bit for bit
(`faithful_load`); if it does not, the probe stops there.

  (a) faithful load   the first panel, unmodified, against the recorded rollout-45 panel
  (b) label effect    during that panel, on an even stride, the low-level actor's own inputs and
                      outputs and the low-level critic's own inputs and outputs are captured; after
                      the panel, under `torch.no_grad()` and preserved RNG, the deterministic action
                      is recomputed at the same input under each of the n_z agent labels, and the
                      critic's raw value under each of the n_Z team labels.  A one-step measure at a
                      fixed hidden state: the cumulative effect through the GRU is what (c) measures.
  (c) execution rules `as_trained` (that first panel), `frozen_episode`, `uniform_every_step` and
                      `uniform_every_10`, one panel each, same weights, same 32 worlds and
                      evaluation seeds, each from a freshly reset evaluator.

The rules are imposed without touching `hmasd/`: the evaluator agent's own `_batched_assign_skills`
is wrapped on the instance for the duration of one panel and removed in a `finally`, and
`uniform_every_step` additionally sets that instance's `d2_k_max`/`d2_k_Z` (hmasd/agent.py:482-483)
to 1 for that panel and restores them, so the D2 route takes a decision at every step.  Random labels
come from a `numpy.random.Generator` seeded from the block's evaluation seed and the rule name; it
touches no global NumPy, Python or torch stream.

`reduce` is a pure reading of published summaries and carries no admission.
"""
import argparse
import hashlib
import inspect
import json
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

import probe_fsd_d_state_scale_b06 as probe
import run_fsd_baseline_interruption_b01 as b01
import run_fsd_flat_entropy_b03 as entropy
import run_fsd_flat_input_scale_b05 as scale
import run_fsd_flat_update_b04 as update
import run_fsd_matched_information_baseline_b01 as matched
import run_fsd_persistence_b07 as persistence
from scripts.hmasd_admission import require_admission

shared = b01.shared
DIRECTION = "flexible_skill_duration"
OBJECT_ID = "FSD_LABEL_CONTENT_B08"
CARD = ("docs/research/candidates/flexible_skill_duration/NOTES.md "
        "(2026-09-20 05:45 PDT, prospective: label content at fixed weights, B08)")
BLOCKS = dict(scale.BLOCKS)  # 772803, 772903, 773003
# One arm: the frozen runner's `("D0", 1280)` renewal route, which is the recorded D1280
# construction. The frozen runner dispatches on the arm name, so this object names its own.
ARMS = {"D_SAVE": ("D0", 1280)}
SAVE_ARM = "D_SAVE"
ARM_OVERRIDES = {"D_SAVE": {}}  # no configuration difference at all is the point of this arm
ARM_CAPS = (10, 10)  # skill_cap_k_max, team_cap_k_Z: the frozen D1280 caps
SKILL_PERIOD = 10  # `config.k`
D_REFERENCE = "D1280"  # the published stage-1 fits of FSD_MATCHED_INFORMATION_BASELINE_B01
RECORDED_FITS = dict(probe.RECORDED_FITS)  # runs/.../b01_s1_d1280_<block>_a01/summary.json
# The fit whose panel `faithful_load` is read against. The same three files in production; a test
# points it at a tiny fit of this object's own arm, which is why it is data and not a literal.
REFERENCE_FITS = dict(RECORDED_FITS)
GEOMETRY_FIELDS = probe.GEOMETRY_FIELDS
ROLLOUTS = matched.ROLLOUTS  # 45
PANEL_ROLLOUTS = matched.PANEL_ROLLOUTS  # 5, 10, ... 45
WALL_PLANS = {"D_SAVE": matched.WALL_PLANS[D_REFERENCE]}  # the D1280 plan; not a deadline
PRIMARY_NAME = f"J_{ROLLOUTS}"
WEIGHTS_NAME = "final_weights.pt"
SIDECAR_NAME = "weights.json"
# The identity `reference_panel` requires of the fit it reads, and the panel it takes from it.
REFERENCE = {"object_id": matched.OBJECT_ID, "factorial_arm": D_REFERENCE,
             "panel_rollouts": ROLLOUTS}
DIFFERENCE_THRESHOLD = .05  # the notebook entry's declared size for a J difference
SMALL_DIFFERENCE = .02  # the entry's "within .02 of J as trained"
ACTOR_CAPTURE_CALLS = 25  # evenly spaced calls of the panel, with a hard row limit (B06's bound)
CRITIC_CAPTURE_CALLS = 25
RULES = ("as_trained", "frozen_episode", "uniform_every_step", "uniform_every_10")
BASELINE_RULE = "as_trained"
RANDOM_RULES = ("uniform_every_step", "uniform_every_10")  # the rules that draw labels
# The only instance attributes a rule may move, and only for the duration of its own panel.
RULE_CAPS = {"uniform_every_step": {"d2_k_max": 1, "d2_k_Z": 1}}
CURRENT = {"label_content_arm": None, "admission": None, "summary": None, "agent": None}
_orig_make_config = matched._orig_make_config  # the frozen `run_fsd_baseline_interruption_b01`'s
_orig_build_learner = b01.build_learner
_orig_base_summary = shared.base_summary
_FLAG = "_label_content_wrapper"

SOURCE_NOTES = {
    "weight_transfer_to_evaluator": (
        "scripts/run_flexible_skill_duration_e0.py:319-335 `Evaluator._sync`, called by the frozen "
        "`run_fsd_baseline_interruption_b01.evaluate_panel` at line 207 of that file, before every "
        "panel: `skill_coordinator` and `skill_discoverer` are moved by `load_state_dict` of the "
        "learner's own `state_dict`, the team and individual discriminators likewise where both "
        "exist, and `obs_norm`, `state_norm`, `value_norm_coordinator` and `value_norm_discoverer` "
        "are `copy.deepcopy`d; then `agent.train(False)` and `reset_env_state(lane)` for every lane, "
        "so the evaluator starts each panel in eval mode with no held skill, zero timers and zero "
        "recurrent state. This probe loads the checkpoint into the learner and lets that same route "
        "carry it to the evaluator, so nothing about the transfer differs from a fit's panel"),
    "checkpoint_contents": (
        "hmasd/agent.py:7351-7501 `save_model` writes the `skill_coordinator` and `skill_discoverer` "
        "state dicts (the low-level actor's FiLM generator, MLP base, GRU, action head and its "
        "state-independent log-std bias `actor.act.action_out.logstd._bias` are inside the second), "
        "the discriminators, every optimizer state, the pickled `config`, interface and diagnostic "
        "metadata, the rollout sampler RNG state, and - because `use_valuenorm` is True on this "
        "construction - `valuenorm_state` (the coordinator's and the discoverer's running mean, "
        "variance and count). `use_obsnorm` and `use_statenorm` are False here, so no "
        "`normalization_state` block is written and none is needed: `_normalize_observations` and "
        "`_normalize_states` return their input unchanged (hmasd/agent.py:1502-1503, 1554-1555)"),
    "checkpoint_load": (
        "hmasd/agent.py:7554-7872 `load_model`: `torch.load(..., weights_only=False)`, then "
        "`load_state_dict(..., strict=False)` for every module, the optimizer states, the rollout "
        "sampler RNG state and the ValueNorm statistics. `strict=False` means a key mismatch would "
        "be silent, which is why `faithful_load` compares the reloaded policy's panel with the "
        "recorded one bit for bit rather than trusting the load"),
    "low_level_actor_label": (
        "hmasd/networks.py:1449-1452 `R_Actor.forward`: the agent label's one-hot goes through "
        "`film_generator` (an nn.Linear from n_z to 2 * hidden_size) and the resulting (gamma, beta) "
        "modulate the MLP base's features *before* the GRU and the action head. The team label does "
        "not reach the actor at all: `SkillDiscoverer.forward` (hmasd/networks.py:1801-1809) passes "
        "only the observation, the agent label and the hidden state. The team label reaches the "
        "low-level critic the same way (hmasd/networks.py:1557-1560) and the coordinator"),
    "action_distribution": (
        "hmasd/r_mappo_utils.py:73-95 `DiagGaussian`: the deterministic action is `dist.mean`, i.e. "
        "`fc_mean(features)` with no squashing, and the log-std is a state-independent bias "
        "(`AddBias`, hmasd/r_mappo_utils.py:166-182), so the action standard deviation is one vector "
        "per action dimension. With `continuous_action_distribution = 'tanh_gaussian'` the head "
        "would be `TanhDiagGaussian` (line 112) and the deterministic action would be squashed; the "
        "summary records which head actually ran"),
    "execution_rule_attachment": (
        "the evaluator agent instance's `_batched_assign_skills` (hmasd/agent.py:2067, the "
        "dispatcher `step` calls at hmasd/agent.py:3249) is wrapped for the duration of one panel: "
        "the wrapper calls the frozen method, reads the D2 decision masks the method just recorded "
        "in `_d2_last_step` (hmasd/agent.py:2721-2733) and replaces the executed labels according to "
        "the rule, writing them back into `env_team_skills`/`env_agent_skills` so the agent's held "
        "label is the executed one. Both interruption costs are infinite on this construction, so "
        "the held label cannot move a decision boundary: only the caps can, and the probe refuses to "
        "run a rule if either cost is finite"),
    "value_norm": (
        "hmasd/agent.py:3139-3140 denormalises the low-level critic's output with "
        "`value_norm_discoverer` after the forward call; the label-effect reading below is the raw "
        "network output, before that step, exactly as B06 reports it"),
    "evaluation_route": (
        "the panel calls `agent.step(..., deterministic=True)` "
        "(run_fsd_baseline_interruption_b01.py:224-225), so the coordinator's team and agent labels "
        "are argmax choices, not samples, and the low-level action is the Gaussian's mean"),
}


def bind(wrap=False):
    """Rebind the frozen runner's identities to this object; loop, panel law and validation stand.

    Readers need the identities only. A fit also wraps `shared.base_summary` and the frozen
    `build_learner` (the one point at which this object reaches the learner agent, to hold the
    reference whose weights are saved afterwards), and `run_fit` takes both off again, so a later
    reader or fit of another object in the same process is not marked.
    """
    global shared, _orig_base_summary
    shared = b01.shared
    b01.OBJECT_ID, b01.CARD = OBJECT_ID, CARD
    b01.BLOCKS, b01.ROLLOUTS, b01.PANEL_ROLLOUTS = dict(BLOCKS), ROLLOUTS, PANEL_ROLLOUTS
    b01.ARMS, b01.FLAT_ARM = dict(ARMS), matched.CF_ARM  # no flat arm runs here
    b01.WALL_PLANS = dict(WALL_PLANS)
    b01.make_config = make_config
    if wrap:
        current = shared.base_summary  # only ever wrap a plain function, exactly once
        for flag, module in (("_matched_information_wrapper", matched), (entropy._FLAG, entropy),
                             (update._FLAG, update), (scale._FLAG, scale),
                             (persistence._FLAG, persistence)):
            if getattr(current, flag, False):
                current = module._orig_base_summary
        if not getattr(current, _FLAG, False):
            _orig_base_summary = current
        shared.base_summary = base_summary
        b01.build_learner = build_learner


# ---------------------------------------------------------------------------
# the construction: the recorded D1280 one, and nothing else
# ---------------------------------------------------------------------------


def host_geometry():
    """This object's own lanes and horizon; B06's `FROZEN_GEOMETRY` is the frozen host's."""
    return {"train_lanes": int(shared.TRAIN_LANES), "eval_lanes": int(shared.EVAL_LANES),
            "horizon": int(shared.HORIZON)}


def config_differences(config, other):
    """Every snapshot field where `config` differs from `other` (B06's comparison)."""
    return probe.config_differences(config, other)


def allowed_differences(arm=SAVE_ARM):
    """The fields a fit of this object may differ from the recorded D1280 fit in."""
    allowed = set(ARM_OVERRIDES[arm])  # empty: this arm declares no override
    if host_geometry() != probe.FROZEN_GEOMETRY:  # a shrunken test host, never the frozen one
        allowed |= set(GEOMETRY_FIELDS)
    return allowed


def require_recorded_construction(config, recorded_config, phase, arm=SAVE_ARM):
    """Refuse any difference from the recorded D1280 fit the arm or the host does not explain."""
    differences = config_differences(config, recorded_config)
    unexpected = {key: value for key, value in differences.items()
                  if key not in allowed_differences(arm)}
    if unexpected:
        raise ValueError(
            f"the {arm} {phase} is not the recorded D1280 fit's construction: {sorted(unexpected)}")
    return differences


def recorded_fit(seed):
    """The published stage-1 D1280 summary of a block, or None with the reason it is unavailable.

    The execution node's sparse checkout (`.codex/hmasd-compute.toml`) does not carry `runs/`, so a
    fit cannot depend on this file existing. The declared-difference guard in `make_config` needs no
    file at all; this comparison is additional, and `reduce` requires it.
    """
    path = RECORDED_FITS[int(seed)]
    if not path.exists():
        return None, f"{path.relative_to(ROOT).as_posix()} is not in this checkout"
    return probe.recorded_fit(int(seed))[0], None


def _record_recorded_comparison(phase, arm, snapshot, block_seed):
    """Compare one phase's snapshot with the recorded D1280 fit's and put it on the summary."""
    summary = CURRENT.get("summary")
    recorded, reason = recorded_fit(block_seed)
    if recorded is None:
        result = {"available": False, "reason": reason, "differences": None}
    else:
        result = {"available": True, "reason": None,
                  "differences": require_recorded_construction(
                      snapshot, recorded[phase], phase, arm)}
    if summary is not None:
        key = f"{phase}_differences_from_recorded_d1280"
        if summary.get(key) is not None:
            raise ValueError(f"{phase} was built twice in one fit")
        summary[key] = result
    return result


def make_config(arm, envs, seed):
    """The frozen D1280 construction, with no override at all; any difference is refused.

    `configs/config_1.py`'s `update_env_dims` runs `validate_config()` and then
    `calculate_and_set_buffer_sizes()` after the environment dimensions are set; both are re-run here
    in that order, as B07 does after its overrides, and the guard below shows that neither moved a
    recorded field.
    """
    if arm not in ARM_OVERRIDES:
        raise ValueError(f"unknown arm {arm}")
    config = _orig_make_config(SAVE_ARM, envs, seed)
    baseline = shared.config_snapshot(config)
    overrides = ARM_OVERRIDES[arm]
    for field, value in overrides.items():
        setattr(config, field, value)
    config.validate_config()
    config.calculate_and_set_buffer_sizes()
    snapshot = shared.config_snapshot(config)
    differences = config_differences(snapshot, baseline)
    if set(differences) != set(overrides):
        raise ValueError(
            f"{arm} differs from the D1280 construction in {sorted(differences)}, not in the "
            f"declared {sorted(overrides)}")
    if CURRENT["label_content_arm"] is not None:  # None reproduces the construction alone
        summary = CURRENT.get("summary")
        block_seed = int(summary["block_seed"]) if summary else int(seed)
        phase = ("learner_config" if (summary or {}).get("learner_config") is None
                 else "evaluation_config")
        _record_recorded_comparison(phase, arm, snapshot, block_seed)
    return config


# ---------------------------------------------------------------------------
# the fit: the frozen route, and the final weights written after it has returned
# ---------------------------------------------------------------------------


def build_learner(arm, summary, out, training_seed):
    """The frozen learner construction; this object only keeps the reference it returns.

    Nothing is attached to the agent: the fit is the frozen route exactly, and the reference is used
    once, after `run_fit` has returned, to write the final weights.
    """
    envs, agent, theta0, counters = _orig_build_learner(arm, summary, out, training_seed)
    if CURRENT["label_content_arm"] is not None:
        CURRENT["agent"] = agent
    return envs, agent, theta0, counters


def base_summary(*args, **kwargs):
    summary = _orig_base_summary(*args, **kwargs)
    arm = CURRENT["label_content_arm"]
    summary.update(label_content_object=OBJECT_ID, label_content_arm=arm,
                   arm_overrides=dict(ARM_OVERRIDES.get(arm, {})),
                   skill_period_k=SKILL_PERIOD, admission=CURRENT["admission"],
                   primary=PRIMARY_NAME, final_weights=None,
                   learner_config_differences_from_recorded_d1280=None,
                   evaluation_config_differences_from_recorded_d1280=None)
    CURRENT["summary"] = summary
    return summary


setattr(base_summary, _FLAG, True)


def plan_guard(arm, seed):
    """The notebook entry's three fits: the one arm on the three blocks."""
    if arm not in ARMS:
        raise SystemExit(f"unknown arm {arm}")
    if seed not in BLOCKS:
        raise SystemExit("this object runs on blocks 772803, 772903 and 773003")


def file_sha256(path, chunk=1 << 22):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def checkpoint_inventory(path):
    """What `save_model` actually wrote, read without materialising the tensors where possible."""
    try:  # `mmap` keeps the storages lazy, so listing the keys costs no resident memory
        checkpoint = torch.load(path, map_location="cpu", mmap=True, weights_only=False)
        mapped = True
    except (RuntimeError, ValueError, TypeError, NotImplementedError):
        checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        mapped = False
    try:
        keys = sorted(str(key) for key in checkpoint)
        modules = {}
        for name in ("skill_coordinator", "skill_discoverer", "team_discriminator",
                     "individual_discriminator"):
            value = checkpoint.get(name)
            if isinstance(value, dict):
                modules[name] = {"entries": len(value), "keys": sorted(str(k) for k in value)}
        discoverer = modules.get("skill_discoverer", {}).get("keys", [])
        return {
            "memory_mapped_read": mapped,
            "keys": keys,
            "empty_keys": sorted(key for key in keys if checkpoint.get(key) is None),
            "module_state_dicts": {name: value["entries"] for name, value in modules.items()},
            "skill_discoverer_keys": discoverer,
            "skill_coordinator_entries": modules.get("skill_coordinator", {}).get("entries"),
            "valuenorm_state": sorted(checkpoint.get("valuenorm_state", {}) or {}),
            "normalization_state": sorted(checkpoint.get("normalization_state", {}) or {}),
            "low_level_actor_logstd_key": next(
                (key for key in discoverer if key.endswith("act.action_out.logstd._bias")), None),
            "definition": SOURCE_NOTES["checkpoint_contents"]}
    finally:
        del checkpoint


def save_final_weights(agent, summary, out):
    """Write the learner's final weights and the sidecar; only ever after a complete fit."""
    if summary.get("status") != "complete":
        raise ValueError("a fit that is not complete saves no weights")
    path = Path(out) / WEIGHTS_NAME
    agent.save_model(str(path))
    record = {
        "object_id": OBJECT_ID, "file": WEIGHTS_NAME,
        "sha256": file_sha256(path), "bytes": int(path.stat().st_size),
        "launch_sha": summary.get("launch_sha"), "block_seed": summary.get("block_seed"),
        "training_seed": summary.get("training_seed"),
        "evaluation_seed": summary.get("evaluation_seed"),
        "arm": summary.get("label_content_arm"), "rollouts": summary.get("rollouts"),
        "saved_after": ("run_fit returned complete: the frozen collector loop, its updates and the "
                        f"rollout-{summary.get('rollouts')} panel had all finished"),
        "writer": "hmasd/agent.py:7351 HMASDAgent.save_model",
        "inventory": checkpoint_inventory(path)}
    shared.write_json(Path(out) / SIDECAR_NAME, record)
    return record


def run_fit(arm, seed, out, admission=None):
    plan_guard(arm, seed)
    bind(wrap=True)
    CURRENT.update(label_content_arm=arm, admission=admission, agent=None)
    try:
        status = b01.run_fit(arm, seed, out)
        summary, agent = CURRENT.get("summary"), CURRENT.get("agent")
        if status == 0 and summary is not None and agent is not None:
            # Nothing above this line touched the learner; the frozen fit is over.
            summary["final_weights"] = save_final_weights(agent, summary, out)
            shared.publish(out, summary, "final weights written")
        return status
    finally:
        CURRENT.update(label_content_arm=None, admission=None, summary=None, agent=None)
        if shared.base_summary is base_summary:
            shared.base_summary = _orig_base_summary
        if b01.build_learner is build_learner:
            b01.build_learner = _orig_build_learner


# ---------------------------------------------------------------------------
# reading one fit
# ---------------------------------------------------------------------------


def fit_endpoint(summary, recorded=None):
    """Validated per-panel world scores of one complete fit of this object.

    The caps are the frozen ones, so the frozen reader (`b01.arm_panels`) reads this fit itself.
    With `recorded` (the published stage-1 D1280 summary of the same block) the recorded
    construction is compared as well, which is what `reduce` always does.
    """
    bind()
    if summary.get("label_content_object") != OBJECT_ID:
        raise ValueError("not a label-content fit")
    arm = summary.get("label_content_arm")
    if arm != SAVE_ARM or int(summary.get("block_seed", -1)) not in BLOCKS:
        raise ValueError("not one of this object's three planned fits")
    if summary.get("factorial_arm") != arm:
        raise ValueError("the recorded arm name and the frozen runner's arm disagree")
    scores = b01.arm_panels(summary)
    if summary.get("arm_overrides") != ARM_OVERRIDES[arm]:
        raise ValueError("the fit does not record an empty override set")
    epochs = int(summary["learner_config"]["ppo_epochs"])
    if summary["optimizer_calls"]["coordinator"] != epochs * ROLLOUTS:
        raise ValueError(
            f"{arm} took {summary['optimizer_calls']['coordinator']} coordinator steps, not the "
            f"{epochs * ROLLOUTS} of one full-pool minibatch per epoch")
    if recorded is not None:
        for phase in ("learner_config", "evaluation_config"):
            require_recorded_construction(summary[phase], recorded[phase], phase, arm)
    return scores


def bit_identical_panels(summary, recorded):
    """Whether every panel's native world scores of a fit equal the recorded fit's exactly (B07)."""
    mine = {int(p["panel_rollouts"]): p["native_scores_J"] for p in summary["panels"]}
    theirs = {int(p["panel_rollouts"]): p["native_scores_J"] for p in recorded["panels"]}
    if sorted(mine) != list(PANEL_ROLLOUTS) or sorted(theirs) != list(PANEL_ROLLOUTS):
        return {"bit_identical": False, "failure": "the panel schedules differ",
                "first_differing_panel": None}
    for rollout in PANEL_ROLLOUTS:
        if mine[rollout] != theirs[rollout]:
            return {"bit_identical": False, "failure": None, "first_differing_panel": rollout}
    return {"bit_identical": True, "failure": None, "first_differing_panel": None}


def reference_panel(seed):
    """The recorded fit's reference panel of a block: scores, and the summary it came from."""
    path = REFERENCE_FITS[int(seed)]
    summary = json.loads(path.read_text(encoding="utf-8"))
    if (summary.get("object_id") != REFERENCE["object_id"]
            or summary.get("factorial_arm") != REFERENCE["factorial_arm"]
            or summary.get("status") != "complete"
            or int(summary.get("block_seed", -1)) != int(seed)):
        raise ValueError(f"{path} is not the completed reference fit of block {seed}")
    wanted = int(REFERENCE["panel_rollouts"])
    panels = [p for p in summary.get("panels", []) if int(p["panel_rollouts"]) == wanted]
    if len(panels) != 1 or panels[0].get("status") != "complete":
        raise ValueError(f"{path} has no completed rollout-{wanted} panel")
    return panels[0], summary, path


# ---------------------------------------------------------------------------
# (b): read-only capture of the low level during the unmodified panel
# ---------------------------------------------------------------------------


class ActorCapture:
    """The low-level actor's own inputs and outputs at an even stride of one evaluation panel.

    `SkillDiscoverer.forward` is reached through `nn.Module.__call__` (hmasd/agent.py:3116), so a
    forward hook on the evaluator's own module instance sees exactly the arguments the panel passed
    and the action it produced. The hook only copies, so the panel is the unwrapped route's.
    """

    def __init__(self, agent, capture_calls=ACTOR_CAPTURE_CALLS, horizon=None):
        config = agent.config
        self.discoverer = agent.skill_discoverer
        self.obs_dim, self.hidden_size = int(config.obs_dim), int(config.gru_hidden_size)
        self.n_agents, self.n_z = int(config.n_agents), int(config.n_z)
        horizon = shared.HORIZON if horizon is None else int(horizon)
        # The actor is called once per step of the panel, for every (lane, agent) row.
        self.capture_stride = max(1, horizon // max(1, int(capture_calls)))
        self.capture_limit = max(1, int(capture_calls))
        self.calls, self.rows = 0, 0
        self.captured = []
        self._handle = None

    @contextmanager
    def attached(self):
        self._handle = self.discoverer.register_forward_hook(self._hook, with_kwargs=True)
        try:
            yield self
        finally:
            self._handle.remove()
            self._handle = None

    def _hook(self, module, args, kwargs, output):
        observation = args[0] if args else kwargs["observation"]
        agent_skill = args[1] if len(args) > 1 else kwargs["agent_skill"]
        hidden = args[2] if len(args) > 2 else kwargs["hidden_state"]
        deterministic = bool(args[3] if len(args) > 3 else kwargs.get("deterministic", False))
        index = self.calls
        self.calls += 1
        if index % self.capture_stride != 0 or len(self.captured) >= self.capture_limit:
            return
        if observation.dim() != 2 or int(observation.shape[1]) != self.obs_dim:
            raise ValueError(f"the actor's observation is not [rows, {self.obs_dim}]")
        if agent_skill.shape[0] != observation.shape[0]:
            raise ValueError("the actor's labels do not match its observation rows")
        compact = kwargs.get("compact_context")
        central = kwargs.get("central_input")
        self.captured.append({
            "observation": observation.detach().clone(),
            "agent_skill": agent_skill.detach().clone(),
            "hidden": hidden.detach().clone(),
            "deterministic": deterministic,
            "compact_context": None if compact is None else compact.detach().clone(),
            "central_input": None if central is None else central.detach().clone(),
            "action": output[0].detach().clone()})
        self.rows += int(observation.shape[0])

    def provenance(self):
        return {"actor_calls": self.calls, "captured_calls": len(self.captured),
                "captured_rows": self.rows, "capture_stride": self.capture_stride,
                "capture_limit": self.capture_limit,
                "definition": (
                    "the arguments of `SkillDiscoverer.forward` (own observation, agent label, actor "
                    "GRU hidden state, the deterministic flag and the two optional context inputs, "
                    "both None on this construction) and the action it returned, at every "
                    "`capture_stride`-th actor call of the panel, up to `capture_limit` calls; the "
                    "evaluation route calls the actor once per step for all (lane, agent) rows at "
                    "once, so the hidden states are the panel's own and nothing is invented. The "
                    "entry mask is not an argument: `SkillDiscoverer.forward` builds "
                    "`masks = torch.ones(rows, 1)` itself (hmasd/networks.py:1806) and the label "
                    "sweep goes through that same forward, so it sees the identical mask")}


class CriticCapture(probe.CriticCapture):
    """B06's low-level critic capture, with the value the panel's own forward returned."""

    def __init__(self, agent, capture_calls=CRITIC_CAPTURE_CALLS, horizon=None):
        super().__init__(agent, capture_calls=capture_calls, horizon=horizon)
        self._value_handle = None

    @contextmanager
    def attached(self):
        with super().attached():
            self._value_handle = self.critic.register_forward_hook(self._value_hook)
            try:
                yield self
            finally:
                self._value_handle.remove()
                self._value_handle = None

    def _value_hook(self, module, args, output):
        if self.captured and "value" not in self.captured[-1]:
            self.captured[-1]["value"] = output[0].detach().clone()


# ---------------------------------------------------------------------------
# (b): the measures
# ---------------------------------------------------------------------------


def action_standard_deviation(actor):
    """The policy's own per-dimension action standard deviation: exp of the log-std it uses."""
    head = actor.act.action_out
    logstd = getattr(head, "logstd", None)
    mean_layer = getattr(head, "fc_mean", None)
    if logstd is None or mean_layer is None:
        raise ValueError("the low-level actor's head is not a diagonal Gaussian")
    zeros = torch.zeros(1, int(mean_layer.out_features))
    values = logstd(zeros)
    low, high = getattr(head, "logstd_min", None), getattr(head, "logstd_max", None)
    clamped = low is not None and high is not None
    if clamped:
        values = torch.clamp(values, float(low), float(high))
    squashed = type(head).__name__ == "TanhDiagGaussian"
    return values.exp().reshape(-1).detach().double().numpy(), {
        "head": type(head).__name__,
        "log_std_clamped": bool(clamped),
        "deterministic_action_is_squashed": bool(squashed),
        "mean_and_std_share_a_space": not bool(squashed),
        "definition": (
            "exp of the actor's own log-std, read from the state-independent `AddBias` the head "
            "uses (hmasd/r_mappo_utils.py:82, 126), with the head's own clamp where it has one; one "
            "value per action dimension. It is the standard deviation of the Gaussian whose mean "
            "the deterministic action is, so the ratio below is in units of the policy's own action "
            "noise. A squashed head would report the pre-tanh standard deviation against a squashed "
            "mean, which `mean_and_std_share_a_space` flags"),
        "source": SOURCE_NOTES["action_distribution"]}


def _deterministic_actions(discoverer, entry, labels):
    """The deterministic action at one captured input under each label, stacked [rows, labels, d]."""
    rows = int(entry["observation"].shape[0])
    stacked = []
    for label in labels:
        skills = torch.full((rows,), int(label), dtype=entry["agent_skill"].dtype)
        actions = discoverer(entry["observation"], skills, entry["hidden"], True,
                             compact_context=entry["compact_context"],
                             central_input=entry["central_input"])[0]
        stacked.append(actions.detach().double())
    return torch.stack(stacked, dim=1)


def label_action_effect(discoverer, captured, standard_deviation, *, n_z):
    """The agent label's effect on the low level's deterministic action at a fixed input.

    One step, one fixed observation and hidden state: what the label does to the *mean action* right
    there. It says nothing about the cumulative effect of holding a label through the GRU, which is
    what the execution rules measure.
    """
    std = np.asarray(standard_deviation, dtype=np.float64)
    labels = list(range(int(n_z)))
    rows, dimensions = 0, None
    totals = {}
    pairwise_std, held_std = 0., 0.
    reproduces, difference = True, 0.
    for entry in captured:
        actions = _deterministic_actions(discoverer, entry, labels)  # [rows, labels, dims]
        count, _, dims = actions.shape
        if dimensions is None:
            dimensions = int(dims)
            for name in ("rms_deviation", "max_pairwise", "held_to_others", "absolute_action"):
                totals[name] = np.zeros(dimensions, dtype=np.float64)
        elif int(dims) != dimensions:
            raise ValueError("the captured actions change width between calls")
        values = actions.numpy()
        rows += int(count)
        centred = values - values.mean(axis=1, keepdims=True)
        totals["rms_deviation"] += np.sqrt((centred ** 2).mean(axis=1)).sum(axis=0)
        gaps = np.abs(values[:, :, None, :] - values[:, None, :, :])  # [rows, l, l', dims]
        totals["max_pairwise"] += gaps.max(axis=(1, 2)).sum(axis=0)
        standardised = np.sqrt(((gaps / std) ** 2).sum(axis=-1))  # [rows, l, l']
        pairwise_std += float(standardised.max(axis=(1, 2)).sum())
        held = np.asarray(entry["agent_skill"].detach().cpu().numpy(), dtype=np.int64).reshape(-1)
        held_actions = values[np.arange(count), held, :]  # [rows, dims]
        others = np.ones((count, len(labels)), dtype=bool)
        others[np.arange(count), held] = False
        deltas = np.abs(values - held_actions[:, None, :])  # [rows, labels, dims]
        totals["held_to_others"] += (deltas * others[:, :, None]).sum(axis=1).sum(axis=0) / max(
            1, len(labels) - 1)
        held_distance = np.sqrt(((deltas / std) ** 2).sum(axis=-1))  # [rows, labels]
        held_std += float((held_distance * others).sum() / max(1, len(labels) - 1))
        totals["absolute_action"] += np.abs(values.mean(axis=1)).sum(axis=0)
        panel_action = entry["action"].detach().double().numpy()
        gap = float(np.abs(held_actions - panel_action).max()) if panel_action.size else 0.
        difference = max(difference, gap)
        reproduces = reproduces and gap == 0.
    divisor = max(rows, 1)
    per_dimension = {name: (total / divisor) for name, total in totals.items()}
    ratio = per_dimension["rms_deviation"] / std
    pairwise_ratio = per_dimension["max_pairwise"] / std
    held_ratio = per_dimension["held_to_others"] / std
    return {
        "rows": rows, "labels": len(labels), "action_dimensions": dimensions,
        "action_standard_deviation_per_dimension": std.tolist(),
        "mean_absolute_action_per_dimension": per_dimension["absolute_action"].tolist(),
        "rms_label_deviation_per_dimension": per_dimension["rms_deviation"].tolist(),
        "rms_label_deviation_mean": float(per_dimension["rms_deviation"].mean()),
        "rms_label_deviation_over_std_per_dimension": ratio.tolist(),
        "rms_label_deviation_over_std_mean": float(ratio.mean()),
        "max_pairwise_label_distance_per_dimension": per_dimension["max_pairwise"].tolist(),
        "max_pairwise_label_distance_over_std_per_dimension": pairwise_ratio.tolist(),
        "max_pairwise_label_distance_over_std_mean": float(pairwise_ratio.mean()),
        "max_pairwise_label_distance_in_std_units": pairwise_std / divisor,
        "held_label_to_others_distance_per_dimension": per_dimension["held_to_others"].tolist(),
        "held_label_to_others_over_std_per_dimension": held_ratio.tolist(),
        "held_label_to_others_over_std_mean": float(held_ratio.mean()),
        "held_label_to_others_in_std_units": held_std / divisor,
        "recomputed_action_at_held_label_reproduces_the_panel": bool(reproduces),
        "max_absolute_difference_from_the_panel_action": difference,
        "definitions": {
            "rms_label_deviation": (
                "per captured row and action dimension, the root mean square over the n_z agent "
                "labels of (action under that label - the mean over labels of the action), with the "
                "observation, the actor GRU hidden state, the entry mask and every weight held "
                "fixed; averaged over the captured rows. The action is the one the actor's own "
                "forward returns with `deterministic=True`, which is the Gaussian's mean"),
            "over_std": (
                "the same quantity divided, per action dimension, by the policy's own action "
                "standard deviation; `_mean` is the unweighted mean of the per-dimension ratios"),
            "max_pairwise_label_distance": (
                "per captured row, the maximum over the n_z * (n_z - 1) / 2 label pairs of "
                "|action under l - action under l'|, per action dimension, averaged over rows; "
                "`_in_std_units` is instead the maximum over pairs of the Euclidean distance after "
                "dividing each dimension by its own standard deviation"),
            "held_label_to_others": (
                "per captured row, the mean over the other n_z - 1 labels of |action under the "
                "label the row actually held - action under that other label|, per action "
                "dimension, averaged over rows; `_in_std_units` is the same with the per-dimension "
                "Euclidean distance in standard-deviation units"),
            "recomputed_action_at_held_label_reproduces_the_panel": (
                "the recomputation at the row's own held label is compared with the action the "
                "panel's own forward returned at that call; exact equality is the runtime proof "
                "that the label sweep runs the panel's route with only the label changed"),
            "scope": (
                "a one-step measure at a fixed hidden state: it is the immediate effect of the FiLM "
                "input on the mean action (hmasd/networks.py:1449-1452), not the cumulative effect "
                "of executing a label over a segment, which the execution rules measure"),
            "label_path": SOURCE_NOTES["low_level_actor_label"]}}


def label_value_effect(critic, captured, *, n_Z, use_valuenorm):
    """The team label's effect on the low-level critic's raw value at a fixed input."""
    labels = list(range(int(n_Z)))
    rows, spread, absolute, pairwise, held_gap = 0, 0., 0., 0., 0.
    reproduces, difference = True, 0.
    for entry in captured:
        state, hidden = entry["cent_obs"], entry["hidden"]
        masks = entry["masks"]
        values = []
        for label in labels:
            team = torch.full_like(entry["team_skill"], int(label))
            values.append(critic(state, hidden, masks, team)[0].detach().double().reshape(-1))
        stacked = torch.stack(values, dim=1).numpy()  # [rows, labels]
        count = int(stacked.shape[0])
        rows += count
        centred = stacked - stacked.mean(axis=1, keepdims=True)
        spread += float(np.sqrt((centred ** 2).mean(axis=1)).sum())
        absolute += float(np.abs(stacked).mean(axis=1).sum())
        pairwise += float((stacked.max(axis=1) - stacked.min(axis=1)).sum())
        held = np.asarray(entry["team_skill"].detach().cpu().numpy(), dtype=np.int64).reshape(-1)
        held_values = stacked[np.arange(count), held]
        others = np.ones_like(stacked, dtype=bool)
        others[np.arange(count), held] = False
        held_gap += float((np.abs(stacked - held_values[:, None]) * others).sum() / max(
            1, len(labels) - 1))
        panel_value = entry.get("value")
        if panel_value is not None:
            gap = float((panel_value.detach().double().reshape(-1) - torch.as_tensor(
                held_values)).abs().max())
            difference = max(difference, gap)
            reproduces = reproduces and gap == 0.
    divisor = max(rows, 1)
    mean_absolute = absolute / divisor
    return {
        "rows": rows, "labels": len(labels),
        "rms_label_spread": spread / divisor,
        "mean_absolute_value": mean_absolute,
        "rms_label_spread_over_mean_absolute_value": (spread / divisor / mean_absolute
                                                      if mean_absolute > 0. else None),
        "max_pairwise_label_spread": pairwise / divisor,
        "held_label_to_others_mean_distance": held_gap / divisor,
        "recomputed_value_at_held_label_reproduces_the_panel": bool(reproduces),
        "max_absolute_difference_from_the_panel_value": difference,
        "value_norm": {"use_valuenorm": bool(use_valuenorm), "note": SOURCE_NOTES["value_norm"]},
        "definitions": {
            "rms_label_spread": (
                "per captured critic row, the root mean square over the n_Z team labels of (value "
                "under that label - the mean over labels), at the row's own central state, GRU "
                "hidden state and entry mask; averaged over rows. `v` is the raw network output of "
                "`R_Critic.v_out`, before the ValueNorm denormalisation the agent applies at "
                "hmasd/agent.py:3139-3140"),
            "mean_absolute_value": "mean over rows and labels of |v|; the spread is reported over it",
            "held_label_to_others_mean_distance": (
                "mean over rows and over the other n_Z - 1 labels of |v(held label) - v(other)|"),
            "scope": ("the team label does not enter the low-level actor at all; this is its effect "
                      "on the low level's value estimate, reported beside the action measure"),
            "label_path": SOURCE_NOTES["low_level_actor_label"]}}


# ---------------------------------------------------------------------------
# (c): the four execution rules
# ---------------------------------------------------------------------------


RULE_DEFINITIONS = {
    "as_trained": (
        "the frozen evaluation route exactly: deterministic (argmax) coordinator labels, caps of 10, "
        "nothing replaced. The labels are only read, so this panel is the unmodified one that (a) "
        "compares with the recorded fit"),
    "frozen_episode": (
        "the team and agent labels chosen at the episode's reset decision are held for the whole "
        "episode: at every later decision of the panel the coordinator's returned labels are "
        "replaced by the currently held ones, which are also written back as the agent's held "
        "labels. The decision cadence is unchanged (caps of 10) and the coordinator still runs"),
    "uniform_every_step": (
        "every step, every agent's label and the team label are drawn uniformly at random. The "
        "evaluator instance's `d2_k_max` and `d2_k_Z` are set to 1 for this panel only, so the D2 "
        "route takes a decision at every step, and every drawn label replaces the coordinator's"),
    "uniform_every_10": (
        "the normal caps-10 cadence, with the labels drawn uniformly at random instead of taken "
        "from the coordinator's argmax at each decision; between decisions the drawn labels are "
        "held, exactly as the argmax ones would be"),
}


def label_generator(evaluation_seed, rule):
    """A dedicated generator per (block, rule); it touches no global NumPy, Python or torch stream."""
    digest = hashlib.sha256(rule.encode("utf-8")).digest()[:8]
    return np.random.default_rng([int(evaluation_seed), int.from_bytes(digest, "big")])


def attachment_site():
    """file:line of the statement that wraps the evaluator agent's skill assignment."""
    lines, start = inspect.getsourcelines(ExecutionRule.attached)
    offsets = [index for index, text in enumerate(lines)
               if text.strip().startswith("agent._batched_assign_skills =")]
    line = start + offsets[0] if offsets else start
    return (f"{Path(__file__).resolve().relative_to(ROOT).as_posix()}:{line} wraps the evaluator "
            "agent instance's `_batched_assign_skills` for the duration of one panel; the frozen "
            "`step` calls it at hmasd/agent.py:3249")


class ExecutionRule:
    """One execution rule, attached to the evaluator agent's own instance for one panel.

    The wrapper calls the frozen `_batched_assign_skills` first and unchanged, then replaces the
    executed labels according to the rule and writes them back as the agent's held labels, so the
    agent's bookkeeping and the executed behaviour agree. `as_trained` replaces nothing and writes
    nothing back: it only records, which is why (a)'s comparison with the recorded panel is also the
    proof that the recording is inert.
    """

    def __init__(self, name, agent, *, generator=None, horizon=None):
        if name not in RULE_DEFINITIONS:
            raise ValueError(f"unknown execution rule {name}")
        config = agent.config
        self.name, self.agent = name, agent
        self.n_Z, self.n_z = int(config.n_Z), int(config.n_z)
        self.n_agents = int(config.n_agents)
        self.horizon = int(shared.HORIZON if horizon is None else horizon)
        self.generator = generator
        self.caps = dict(RULE_CAPS.get(name, {}))
        self.rewrites = name != BASELINE_RULE
        self.draws = name in RANDOM_RULES
        if self.draws and generator is None:
            raise ValueError(f"{name} needs its own label generator")
        self.steps, self.lanes = 0, 0
        self.resets = 0
        self.team_changes, self.team_comparisons = 0, 0
        self.agent_changes, self.agent_comparisons = 0, 0
        self.team_histogram = np.zeros(self.n_Z, dtype=np.int64)
        self.agent_histogram = np.zeros(self.n_z, dtype=np.int64)
        self.held_team, self.held_agents = None, None
        self._previous_team, self._previous_agents = None, None

    # -- attachment ---------------------------------------------------------

    @contextmanager
    def attached(self):
        agent = self.agent
        if not getattr(agent, "d2_enabled", False):
            raise ValueError("the execution rules are defined on the D2 route")
        if np.isfinite(agent.d2_cost_c) or np.isfinite(agent.d2_cost_c_Z):
            # With a finite cost the trigger statistic reads the held label, so replacing the
            # executed label would move the decision boundary as well as the behaviour.
            raise ValueError("the execution rules require infinite interruption costs")
        original = agent._batched_assign_skills
        restore = {name: getattr(agent, name) for name in self.caps}
        for name, value in self.caps.items():
            setattr(agent, name, int(value))

        def assign(*args, **kwargs):
            team, agents, log_probs = original(*args, **kwargs)
            team, agents = self._step(team, agents)
            return team, agents, log_probs

        agent._batched_assign_skills = assign  # an instance attribute only; the class is untouched
        try:
            yield self
        finally:
            agent.__dict__.pop("_batched_assign_skills", None)
            for name, value in restore.items():
                setattr(agent, name, value)

    # -- the rule -----------------------------------------------------------

    def _step(self, team, agents):
        last = self.agent._d2_last_step
        reset = np.asarray(last["team_cause"], dtype=np.int64) == self.agent.D2_CAUSE_RESET
        team = np.asarray(team, dtype=np.int64).copy()
        agents = np.asarray(agents, dtype=np.int64).copy()
        lanes = int(team.shape[0])
        if self.name == "frozen_episode":
            if self.held_team is None or self.held_team.shape[0] != lanes:
                self.held_team = np.full(lanes, -1, dtype=np.int64)
                self.held_agents = np.full((lanes, agents.shape[1]), -1, dtype=np.int64)
            self.held_team[reset] = team[reset]
            self.held_agents[reset] = agents[reset]
            known = self.held_team >= 0
            team = np.where(known, self.held_team, team)
            agents = np.where(known[:, None] & (self.held_agents >= 0), self.held_agents, agents)
        elif self.draws:
            drawn_team = self.generator.integers(0, self.n_Z, size=lanes)
            drawn_agents = self.generator.integers(0, self.n_z, size=agents.shape)
            team = np.where(np.asarray(last["sample_Z"], dtype=bool), drawn_team, team)
            agents = np.where(np.asarray(last["sampled_mask"], dtype=bool), drawn_agents, agents)
        if self.rewrites:  # the executed label is the label the agent holds
            for lane in range(lanes):
                self.agent.env_team_skills[lane] = int(team[lane])
                self.agent.env_agent_skills[lane] = agents[lane].copy()
        self._record(team, agents, reset)
        return team, agents

    def _record(self, team, agents, reset):
        self.steps += 1
        self.lanes = int(team.shape[0])
        self.resets += int(reset.sum())
        self.team_histogram += np.bincount(team.reshape(-1), minlength=self.n_Z)
        self.agent_histogram += np.bincount(agents.reshape(-1), minlength=self.n_z)
        if self._previous_team is not None and self._previous_team.shape == team.shape:
            comparable = ~reset  # a fresh episode is not a change of the held label
            self.team_comparisons += int(comparable.sum())
            self.team_changes += int(((team != self._previous_team) & comparable).sum())
            self.agent_comparisons += int(comparable.sum()) * int(agents.shape[1])
            self.agent_changes += int(
                ((agents != self._previous_agents) & comparable[:, None]).sum())
        self._previous_team, self._previous_agents = team.copy(), agents.copy()

    # -- the record ---------------------------------------------------------

    def measures(self):
        return {
            "rule": self.name, "definition": RULE_DEFINITIONS[self.name],
            "steps_recorded": self.steps, "lanes": self.lanes, "reset_rows": self.resets,
            "caps_applied": dict(self.caps),
            "agent_label_change_fraction": (self.agent_changes / self.agent_comparisons
                                            if self.agent_comparisons else None),
            "team_label_change_fraction": (self.team_changes / self.team_comparisons
                                           if self.team_comparisons else None),
            "agent_label_comparisons": self.agent_comparisons,
            "team_label_comparisons": self.team_comparisons,
            "agent_label_histogram": self.agent_histogram.tolist(),
            "team_label_histogram": self.team_histogram.tolist(),
            "uniform_label_change_reference": 1. - 1. / self.n_z,
            "attached_at": attachment_site(),
            "definitions": {
                "label_change_fraction": (
                    "fraction of the (step, lane, agent) triples of the panel whose executed agent "
                    "label differs from the previous step's executed label of the same lane and "
                    "agent, over the steps that are not an episode reset; and the same over "
                    "(step, lane) for the team label. These are the labels this object actually "
                    "executed, after the rule; the `switch_rate_by_agent` of the panel's own d2 "
                    "metrics is the frozen agent's count of coordinator re-decisions that changed "
                    "the held label, which under a replacing rule is not the executed change"),
                "label_histogram": (
                    "count of each label over all executed (step, lane, agent) positions, and over "
                    "all (step, lane) positions for the team label"),
                "uniform_label_change_reference": (
                    "1 - 1/n_z, the change fraction a uniform redraw at every step would give")}}


# ---------------------------------------------------------------------------
# the probe
# ---------------------------------------------------------------------------


def _panel_record(panel, rule, index):
    """One rule's panel, read from the frozen runner's own panel record."""
    scores = np.asarray(panel["native_scores_J"], dtype=np.float64)
    metrics = panel.get("d2_metrics") or {}
    steps, decisions = int(metrics.get("steps", 0)), int(metrics.get("decision_steps", 0))
    record = {
        "panel_index": index,
        "J_mean": float(scores.mean()),
        "J_world_scores": scores.tolist(),
        "J_world_sd": float(scores.std(ddof=1)) if scores.size > 1 else None,
        "returns_U": panel["returns_U"], "component_means": panel.get("component_means"),
        "d2_metrics": metrics, "segments": panel.get("segments"),
        "decision_steps": decisions, "steps": steps,
        "decision_fraction": (decisions / steps if steps else None),
        "switch_rate_by_agent": metrics.get("switch_rate_by_agent"),
        "evaluator_optimizer_calls": panel["evaluator_optimizer_calls"]}
    record.update(rule.measures())
    return record


def run_rule_panel(name, learner, evaluator, summary, out, index, *, evaluation_seed,
                   captures=()):
    """One rule's panel: the frozen `evaluate_panel`, with the rule attached for its duration."""
    generator = label_generator(evaluation_seed, name) if name in RANDOM_RULES else None
    rule = ExecutionRule(name, evaluator.agent, generator=generator)
    with rule.attached():
        if captures:
            with captures[0].attached(), captures[1].attached():
                b01.evaluate_panel(learner, evaluator, summary, out, index)
        else:
            b01.evaluate_panel(learner, evaluator, summary, out, index)
    panel = summary["panels"][-1]
    if panel["status"] != "complete":
        raise ValueError(f"the {name} panel did not complete")
    if any(panel["evaluator_optimizer_calls"].values()):
        raise ValueError(f"the {name} panel took an optimizer step")
    record = _panel_record(panel, rule, index)
    if name == "uniform_every_step" and record["decision_steps"] != record["steps"]:
        raise ValueError(
            f"uniform_every_step fired {record['decision_steps']} decisions in {record['steps']} "
            "agent-steps, not one per step")
    if generator is not None:
        record["random_labels"] = {
            "generator": "numpy.random.default_rng([evaluation_seed, sha256(rule)[:8]])",
            "evaluation_seed": int(evaluation_seed), "rule": name,
            "note": ("a dedicated generator; the global NumPy, Python and torch streams are "
                     "untouched by the draws")}
    else:
        record["random_labels"] = None
    return record


def run_probe(seed, weights, out, launch_sha=None):
    """One block: the recorded construction, the saved weights, one panel per rule, no update."""
    if seed not in BLOCKS:
        raise SystemExit("this object probes blocks 772803, 772903 and 773003")
    bind()
    started = time.perf_counter()
    evaluation_seed = BLOCKS[seed]
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "object_id": OBJECT_ID, "card": CARD, "command": "probe",
        "launch_sha": shared.e0._git("rev-parse", "HEAD"), "requested_launch_sha": launch_sha,
        "arm": SAVE_ARM, "block_seed": seed, "evaluation_seed": evaluation_seed,
        "weights": str(weights), "rules": list(RULES),
        "construction_source": (
            f"{OBJECT_ID} {SAVE_ARM} (the recorded stage-1 {D_REFERENCE} construction): the frozen "
            "baseline x interruption B01 runner with this object's identities bound, the saved "
            "final weights loaded, zero optimizer steps"),
        "recorded_d1280_summary": str(RECORDED_FITS[seed]),
        "reference_summary": str(REFERENCE_FITS[seed]),
        "host_geometry": host_geometry(),
        "frozen_host_geometry": host_geometry() == probe.FROZEN_GEOMETRY,
        "source_notes": dict(SOURCE_NOTES),
        "status": "incomplete", "failure": None, "faithful_load": None}
    construction = out / "construction"
    try:
        _run(result, seed, evaluation_seed, construction, Path(weights))
        result["status"] = "complete"
    except Exception as exc:  # the partial facts stay recorded
        result["status"], result["failure"] = "incomplete", f"{type(exc).__name__}: {exc}"
    finally:
        result["wall_seconds"] = time.perf_counter() - started
        result["interpretation_limit"] = (
            "a fixed-weight forward measurement, not a fit: zero optimizer steps, one block, one "
            "panel per execution rule on the same 32 worlds and evaluation seeds; the label-effect "
            "reading is a one-step measure at the panel's own hidden states; a panel's conditional "
            "evaluation noise on this direction is about .03 J, so smaller J differences are not "
            "read")
        shared.write_json(out / "summary.json", result)
    print(json.dumps({"status": result["status"], "failure": result["failure"],
                      "block_seed": seed,
                      "faithful_load": (result.get("faithful_load") or {}).get("faithful_load"),
                      "J_by_rule": {name: (result.get("rules_measured") or {}).get(name, {}).get(
                          "J_mean") for name in RULES},
                      "optimizer_steps": result.get("optimizer_steps")}))
    return 0 if result["status"] == "complete" else 1


def _run(result, seed, evaluation_seed, out, weights):
    """Build as a fit does, load the weights, run the four panels, then measure. No update."""
    sidecar_path = weights.parent / SIDECAR_NAME
    if not weights.exists():
        raise ValueError(f"{weights} does not exist")
    if not sidecar_path.exists():
        raise ValueError(f"{sidecar_path} does not exist; the weights carry no sidecar record")
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    digest = file_sha256(weights)
    if sidecar.get("sha256") != digest:
        raise ValueError("the weights file does not match the sha256 its sidecar records")
    if int(sidecar.get("block_seed", -1)) != int(seed):
        raise ValueError("the weights were saved by a fit of another block")
    result["weights_record"] = {"sidecar": str(sidecar_path), "sha256": digest,
                                "bytes": int(weights.stat().st_size),
                                "sidecar_record": sidecar,
                                "verified": "sha256 recomputed from the file and compared"}
    recorded, reason = recorded_fit(seed)
    if recorded is None:  # the probe reads the recorded fit's construction and its panel
        raise ValueError(f"the recorded D1280 fit of block {seed} is unreadable: {reason}")
    reference, reference_summary, reference_path = reference_panel(seed)
    result["reference"] = {
        "summary": str(reference_path), "object_id": reference_summary.get("object_id"),
        "factorial_arm": reference_summary.get("factorial_arm"),
        "panel_rollouts": int(reference["panel_rollouts"]),
        "launch_sha": reference_summary.get("launch_sha")}

    summary = shared.base_summary(ARMS[SAVE_ARM][0], training_seed=seed,
                                  evaluation_seed=evaluation_seed, object_id=OBJECT_ID,
                                  card=CARD, caps=None)
    summary.update(command="probe", factorial_arm=SAVE_ARM, block_seed=seed, rollouts=0,
                   panel_rollouts=[], panels=[],
                   coordinator_batch_size=ARMS[SAVE_ARM][1], ordinary_wall_plan_seconds=None,
                   cost_law="zero optimizer steps; one evaluation panel per execution rule")
    out.mkdir(parents=True, exist_ok=True)
    envs, learner, _theta0, counters = b01.build_learner(SAVE_ARM, summary, out, seed)
    learner_differences = require_recorded_construction(
        summary["learner_config"], recorded["learner_config"], "learner configuration")
    restore = scale._forbid_optimizer_steps(learner)
    try:
        learner.load_model(str(weights))  # the agent's own load routine
        learner.train(False)
        evaluator = b01.build_evaluator(SAVE_ARM, summary, out, evaluation_seed)
        evaluation_differences = require_recorded_construction(
            summary["evaluation_config"], recorded["evaluation_config"],
            "evaluation configuration")
        restore += scale._forbid_optimizer_steps(evaluator.agent)
        config = evaluator.agent.config
        actor = ActorCapture(evaluator.agent)
        critic = CriticCapture(evaluator.agent)

        measured = {}
        for index, name in enumerate(RULES):
            measured[name] = run_rule_panel(
                name, learner, evaluator, summary, out, index,
                evaluation_seed=evaluation_seed,
                captures=(actor, critic) if name == BASELINE_RULE else ())
            result["rules_measured"] = dict(measured)
            if name == BASELINE_RULE:
                scores = measured[name]["J_world_scores"]
                panel = summary["panels"][-1]
                faithful = panel["native_scores_J"] == reference["native_scores_J"]
                first = next((i for i, (mine, theirs) in enumerate(
                    zip(panel["native_scores_J"], reference["native_scores_J"]))
                    if mine != theirs), None)
                result["faithful_load"] = {
                    "faithful_load": bool(faithful),
                    "first_differing_world": None if faithful else first,
                    "worlds": len(scores),
                    "reference_panel_rollouts": int(reference["panel_rollouts"]),
                    "definition": (
                        "the 32 native world scores of the unmodified panel, run from the loaded "
                        "weights through the frozen evaluator sync, compared with the recorded "
                        "fit's own reference panel by exact list equality"),
                    "weight_transfer": SOURCE_NOTES["weight_transfer_to_evaluator"]}
                if not faithful:
                    raise ValueError(
                        "the loaded weights do not reproduce the recorded panel; first differing "
                        f"world index {first}")
                if not actor.captured or not critic.captured:
                    raise ValueError("the panel produced no actor call or no critic call")
                standard_deviation, std_note = action_standard_deviation(
                    evaluator.agent.skill_discoverer.actor)
                with shared.e0._preserve_rng(), torch.no_grad():
                    result["label_effect"] = {
                        "action_standard_deviation": std_note,
                        "action": label_action_effect(
                            evaluator.agent.skill_discoverer, actor.captured, standard_deviation,
                            n_z=int(config.n_z)),
                        "low_level_value": label_value_effect(
                            evaluator.agent.skill_discoverer.critic, critic.captured,
                            n_Z=int(config.n_Z), use_valuenorm=bool(config.use_valuenorm))}
                result["capture"] = {"actor": actor.provenance(),
                                     "low_level_critic": critic.provenance()}
    finally:
        for optimizer, original in restore:
            optimizer.step = original

    learner_calls = shared.optimizer_counts(counters)
    steps = sum(learner_calls.values()) + sum(
        sum(panel["evaluator_optimizer_calls"].values()) for panel in summary["panels"])
    if steps != 0:
        raise ValueError("the probe is defined by taking no optimizer step")
    baseline = measured[BASELINE_RULE]["J_mean"]
    result.update({
        "optimizer_steps": steps, "optimizer_calls": learner_calls,
        "rules_measured": measured,
        "J_by_rule": {name: measured[name]["J_mean"] for name in RULES},
        "J_minus_as_trained": {name: measured[name]["J_mean"] - baseline for name in RULES},
        "evaluation_panels": len(summary["panels"]),
        "evaluation_episodes": summary["counts"]["evaluation_episodes"],
        "evaluation_steps": summary["counts"]["evaluation_steps"],
        "evaluation_lanes": shared.EVAL_LANES, "horizon": shared.HORIZON,
        "evaluation_deterministic": True,
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
    return result


# ---------------------------------------------------------------------------
# reduce
# ---------------------------------------------------------------------------


def weights_row(record):
    """The fit's weights sidecar, without the checkpoint's full key list."""
    inventory = record.get("inventory") or {}
    return {key: record.get(key) for key in ("sha256", "bytes", "launch_sha", "block_seed",
                                             "file", "writer", "saved_after")} | {
        "checkpoint_keys": inventory.get("keys"),
        "valuenorm_state": inventory.get("valuenorm_state"),
        "normalization_state": inventory.get("normalization_state"),
        "low_level_actor_logstd_key": inventory.get("low_level_actor_logstd_key"),
        "module_state_dicts": inventory.get("module_state_dicts")}


def fit_row(summary, scores, weights):
    level = {r: float(np.mean(scores[r])) for r in PANEL_ROLLOUTS}
    return {"J_by_rollout": {str(r): level[r] for r in PANEL_ROLLOUTS},
            "endpoint_scores_J": np.asarray(scores[ROLLOUTS], dtype=np.float64).tolist(),
            "object_id": summary["object_id"], "launch_sha": summary["launch_sha"],
            "coordinator_batch_size": summary["learner_config"].get("coordinator_batch_size"),
            "skill_cap_k_max": summary["learner_config"].get("skill_cap_k_max"),
            "team_cap_k_Z": summary["learner_config"].get("team_cap_k_Z"),
            "k": summary["learner_config"].get("k"),
            "weights": weights_row(weights),
            "counts": summary["counts"], "optimizer_calls": summary["optimizer_calls"],
            "wall_seconds_before_publication": summary.get("wall_seconds_before_publication"),
            "peak_rss_bytes": summary.get("peak_rss_bytes")}


def reference_row(summary, scores):
    level = {r: float(np.mean(scores[r])) for r in PANEL_ROLLOUTS}
    return {"J_by_rollout": {str(r): level[r] for r in PANEL_ROLLOUTS},
            "endpoint_scores_J": np.asarray(scores[ROLLOUTS], dtype=np.float64).tolist(),
            "object_id": summary["object_id"], "launch_sha": summary["launch_sha"],
            "arm": D_REFERENCE, "counts": summary["counts"],
            "optimizer_calls": summary["optimizer_calls"],
            "wall_seconds_before_publication": summary.get("wall_seconds_before_publication")}


def weights_record(path):
    """The sidecar written beside a fit's summary, or None with the reason it is unavailable."""
    sidecar = Path(path).parent / SIDECAR_NAME
    if not sidecar.exists():
        return None, f"{sidecar} does not exist"
    record = json.loads(sidecar.read_text(encoding="utf-8"))
    if record.get("object_id") != OBJECT_ID or not record.get("sha256"):
        return None, f"{sidecar} is not this object's weights record"
    return record, None


def probe_row(summary):
    """Validated readings of one complete probe of this object."""
    if summary.get("object_id") != OBJECT_ID or summary.get("command") != "probe":
        raise ValueError("not a probe of this object")
    if summary.get("status") != "complete":
        raise ValueError("incomplete probe")
    seed = int(summary.get("block_seed", -1))
    if seed not in BLOCKS or int(summary.get("evaluation_seed", -1)) != BLOCKS[seed]:
        raise ValueError("not one of this object's three blocks")
    faithful = summary.get("faithful_load") or {}
    if not faithful.get("faithful_load"):
        raise ValueError("the probe did not establish a faithful load")
    measured = summary.get("rules_measured") or {}
    if sorted(measured) != sorted(RULES):
        raise ValueError("the probe does not carry all four execution rules")
    action = (summary.get("label_effect") or {}).get("action") or {}
    value = (summary.get("label_effect") or {}).get("low_level_value") or {}
    if not action or not value:
        raise ValueError("the probe carries no label-effect reading")
    if summary.get("optimizer_steps") != 0:
        raise ValueError("the probe took an optimizer step")
    baseline = float(measured[BASELINE_RULE]["J_mean"])
    return {
        "block_seed": seed, "launch_sha": summary.get("launch_sha"),
        "weights_sha256": (summary.get("weights_record") or {}).get("sha256"),
        "faithful_load": True,
        "reference": summary.get("reference"),
        "label_effect": {
            "rms_label_deviation_over_std_mean": action["rms_label_deviation_over_std_mean"],
            "rms_label_deviation_over_std_per_dimension":
                action["rms_label_deviation_over_std_per_dimension"],
            "max_pairwise_label_distance_over_std_mean":
                action["max_pairwise_label_distance_over_std_mean"],
            "max_pairwise_label_distance_in_std_units":
                action["max_pairwise_label_distance_in_std_units"],
            "held_label_to_others_over_std_mean": action["held_label_to_others_over_std_mean"],
            "held_label_to_others_in_std_units": action["held_label_to_others_in_std_units"],
            "action_standard_deviation_per_dimension":
                action["action_standard_deviation_per_dimension"],
            "low_level_value_rms_spread_over_mean_absolute_value":
                value["rms_label_spread_over_mean_absolute_value"],
            "rows": action["rows"], "critic_rows": value["rows"]},
        "J_by_rule": {name: float(measured[name]["J_mean"]) for name in RULES},
        "J_minus_as_trained": {name: float(measured[name]["J_mean"]) - baseline for name in RULES},
        "label_change_fraction_by_rule": {
            name: measured[name]["agent_label_change_fraction"] for name in RULES},
        "decision_fraction_by_rule": {name: measured[name]["decision_fraction"] for name in RULES},
        "label_histogram_by_rule": {
            name: measured[name]["agent_label_histogram"] for name in RULES}}


def reduce_inputs(fits, probes, references):
    """Three fits, three probes and the three published D1280 fits of the same blocks."""
    bind()
    shas = {s.get("launch_sha") for s in fits}
    if len(shas) > 1:
        raise ValueError(f"mixed launch shas within the batch: {sorted(str(s) for s in shas)}")
    recorded, reference_failures, seen = {}, {}, set()
    for summary in references:
        seed = int(summary.get("block_seed", -1))
        try:
            if seed not in BLOCKS:
                raise ValueError("the references are fits of the three blocks")
            if summary.get("factorial_arm") != D_REFERENCE or summary.get("stage") != 1:
                raise ValueError("the references are the published stage-1 D1280 fits")
            values = matched.fit_endpoint(summary)
        except (KeyError, TypeError, ValueError) as exc:
            reference_failures[f"{seed}:{summary.get('factorial_arm')}"] = str(exc)
            bind()
            continue
        bind()  # the reference reader rebinds the frozen runner to its own object
        if seed in seen:
            raise ValueError("duplicate reference block")
        seen.add(seed)
        recorded[seed] = (summary, reference_row(summary, values))

    rows, sources, failures, supplied = {}, {}, {}, set()
    for summary in fits:
        seed = int(summary.get("block_seed", -1))
        if seed in supplied:  # a second fit of the same block is never a choice
            raise ValueError("duplicate block")
        supplied.add(seed)
        try:
            if summary.get("label_content_object") != OBJECT_ID:
                raise ValueError("not a fit of this object")
            if seed not in recorded:
                raise ValueError("the published D1280 fit of this block was not supplied")
            values = fit_endpoint(summary, recorded=recorded[seed][0])
            weights, reason = weights_record(summary.get("__path__", ""))
            if weights is None:
                weights = summary.get("final_weights")
                if not weights or not weights.get("sha256"):
                    raise ValueError(f"no weights record for this fit: {reason}")
        except (KeyError, TypeError, ValueError) as exc:
            failures[seed] = str(exc)
            bind()
            continue
        bind()
        rows[seed], sources[seed] = fit_row(summary, values, weights), summary

    probe_rows, probe_failures, probed = {}, {}, set()
    for summary in probes:
        seed = int(summary.get("block_seed", -1))
        if seed in probed:
            raise ValueError("duplicate probe block")
        probed.add(seed)
        try:
            probe_rows[seed] = probe_row(summary)
        except (KeyError, TypeError, ValueError) as exc:
            probe_failures[seed] = str(exc)

    blocks = []
    for seed in sorted(BLOCKS):
        entry = {"training_seed": seed, "evaluation_seed": BLOCKS[seed],
                 "fit": rows.get(seed), "probe": probe_rows.get(seed),
                 "reference": recorded[seed][1] if seed in recorded else None,
                 "missing_or_invalid": {}}
        if seed not in rows:
            entry["missing_or_invalid"]["fit"] = failures.get(seed, "not supplied")
        if seed not in probe_rows:
            entry["missing_or_invalid"]["probe"] = probe_failures.get(seed, "not supplied")
        if seed in rows and seed in recorded:
            entry["capture_bit_identical"] = bit_identical_panels(sources[seed], recorded[seed][0])
        else:
            entry["capture_bit_identical"] = {
                "bit_identical": False, "first_differing_panel": None,
                "failure": "the fit or the published D1280 fit of this block is missing"}
        identical = bool(entry["capture_bit_identical"]["bit_identical"])
        entry["status"] = "incomplete"
        if seed in rows and seed in probe_rows:
            fit_sha = (rows[seed]["weights"] or {}).get("sha256")
            probe_sha = probe_rows[seed]["weights_sha256"]
            entry["weights_match"] = bool(fit_sha and fit_sha == probe_sha)
            if not entry["weights_match"]:
                entry["missing_or_invalid"]["weights"] = (
                    "the probe's weights sha256 is not the sha256 this block's fit recorded")
            elif not identical:
                entry["missing_or_invalid"]["capture"] = (
                    "this block's fit is not bit-identical to the published D1280 fit, so its "
                    "weights are not established as the recorded policy's and the probe is not read")
            else:
                entry["status"] = "complete"
                entry["faithful_load"] = probe_rows[seed]["faithful_load"]
                entry["label_effect"] = probe_rows[seed]["label_effect"]
                entry["J_by_rule"] = probe_rows[seed]["J_by_rule"]
                entry["J_minus_as_trained"] = probe_rows[seed]["J_minus_as_trained"]
                entry["label_change_fraction_by_rule"] = probe_rows[seed][
                    "label_change_fraction_by_rule"]
                entry["decision_fraction_by_rule"] = probe_rows[seed]["decision_fraction_by_rule"]
        else:
            entry["weights_match"] = None
        blocks.append(entry)

    complete = [b for b in blocks if b["status"] == "complete"]
    result = {
        "object_id": OBJECT_ID, "card": CARD,
        "reference_object_ids": [matched.OBJECT_ID],
        "launch_sha": shared.e0._git("rev-parse", "HEAD"),
        "batch_launch_sha": next(iter(shas), None) if len(shas) == 1 else None,
        "status": "complete" if len(complete) == len(BLOCKS) else "incomplete",
        "arm": {"name": SAVE_ARM, "overrides": dict(ARM_OVERRIDES[SAVE_ARM]),
                "coordinator_batch_size": ARMS[SAVE_ARM][1],
                "caps": {"skill_cap_k_max": ARM_CAPS[0], "team_cap_k_Z": ARM_CAPS[1]}},
        "rules": list(RULES), "rule_definitions": dict(RULE_DEFINITIONS),
        "quantity": (
            "J of a rule is the mean of its panel's 32 native world scores at the saved weights; "
            "differences are the rule minus `as_trained` on the same block, the same 32 worlds and "
            "the same evaluation seeds. The label-effect ratios are the probe's own one-step "
            "measures at fixed observation and hidden state"),
        "declared_difference": (
            "none: every recorded configuration field of the fit must equal the published stage-1 "
            "D1280 fit of the block (the host-geometry fields are exempt only on a shrunken test "
            "host), and the only addition to the frozen route is the checkpoint written after the "
            "fit returned"),
        "blocks": blocks,
        "capture_bit_identical_blocks": int(sum(b["capture_bit_identical"]["bit_identical"]
                                                for b in blocks)),
        "faithful_load_blocks": int(sum(bool(b.get("faithful_load")) for b in blocks)),
        "invalid_fits": {str(seed): text for seed, text in failures.items()},
        "invalid_probes": {str(seed): text for seed, text in probe_failures.items()},
        "invalid_references": dict(reference_failures),
        "refusals": (
            "a batch of fits at more than one launch sha, a duplicate block among the fits or the "
            "probes, a summary that is not this object's, an incomplete fit or probe, a block whose "
            "published D1280 fit was not supplied, any configuration difference from that fit, a "
            "probe whose weights sha256 is not the one its block's fit recorded, and a probe of a "
            "block whose fit is not bit-identical to the published D1280 fit"),
        "interpretation_limit": (
            "exploration; three blocks; one checkpoint per block; the D1280 reference is the "
            "published stage-1 fit; these blocks carried every flat and skill setting since B01, so "
            "no size claim and no competence claim; the execution rules are deployment-time "
            "interventions on fixed weights and say nothing about what training under them would "
            "produce; a panel's conditional evaluation noise is about .03 J"),
    }
    ratios = ("rms_label_deviation_over_std_mean", "max_pairwise_label_distance_over_std_mean",
              "max_pairwise_label_distance_in_std_units", "held_label_to_others_over_std_mean",
              "held_label_to_others_in_std_units",
              "low_level_value_rms_spread_over_mean_absolute_value")
    result["label_effect"] = {
        name: entropy.described([b["label_effect"][name] for b in complete
                                 if b["label_effect"].get(name) is not None])
        if complete else None for name in ratios}
    result["J_by_rule"] = {
        name: entropy.described([b["J_by_rule"][name] for b in complete]) if complete else None
        for name in RULES}
    counted = {}
    for name in RULES:
        values = [b["J_minus_as_trained"][name] for b in complete]
        result[f"J_{name}_minus_as_trained"] = entropy.described(values) if values else None
        counted[name] = {
            "blocks_at_or_above_threshold": int(sum(abs(v) >= DIFFERENCE_THRESHOLD
                                                    for v in values)),
            "blocks_below_small_difference": int(sum(abs(v) < SMALL_DIFFERENCE for v in values)),
            "blocks_read": len(values)}
    result["J_difference_counts"] = dict(
        counted, threshold=DIFFERENCE_THRESHOLD, small_difference=SMALL_DIFFERENCE,
        planned_blocks=len(BLOCKS),
        definition=("per rule, the number of blocks read as complete whose |J(rule) - J(as "
                    "trained)| is at least the threshold, and the number whose difference is "
                    "smaller than `small_difference`"))
    result["label_change_fraction_by_rule"] = {
        name: entropy.described([b["label_change_fraction_by_rule"][name] for b in complete
                                 if b["label_change_fraction_by_rule"][name] is not None])
        if complete else None for name in RULES}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fit = sub.add_parser("fit")
    fit.add_argument("--arm", choices=tuple(ARMS), default=SAVE_ARM)
    fit.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    fit.add_argument("--launch-sha", help="must equal the admitted source SHA")
    fit.add_argument("--output-root", type=Path, required=True)
    prb = sub.add_parser("probe", help="zero-update execution of one block's saved weights")
    prb.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    prb.add_argument("--weights", type=Path, required=True,
                     help=f"the fit's {WEIGHTS_NAME}; its {SIDECAR_NAME} sidecar must sit beside it")
    prb.add_argument("--launch-sha", required=True, help="must equal the source HEAD; recorded")
    prb.add_argument("--output-root", type=Path, required=True)
    red = sub.add_parser("reduce")
    red.add_argument("--fits", type=Path, nargs="+", required=True, help="this object's three fits")
    red.add_argument("--probes", type=Path, nargs="+", required=True,
                     help="this object's three probe summaries")
    red.add_argument("--references", type=Path, nargs="+", required=True,
                     help="the published stage-1 D1280 (B01) summaries of the three blocks")
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
        return run_probe(args.seed, args.weights.resolve(), args.output_root.resolve(),
                         launch_sha=args.launch_sha)

    args.output_root.mkdir(parents=True, exist_ok=True)
    fits = []
    for path in args.fits:  # the sidecar is read from beside the fit's own summary
        summary = load(path)
        summary["__path__"] = str(path)
        fits.append(summary)
    result = reduce_inputs(fits, [load(p) for p in args.probes], [load(p) for p in args.references])
    result["input_fits"] = [str(p) for p in args.fits]
    result["input_probes"] = [str(p) for p in args.probes]
    result["reference_summaries"] = [str(p) for p in args.references]
    shared.write_json(args.output_root / "summary.json", result)
    print(json.dumps({"status": result["status"],
                      "capture_bit_identical_blocks": result["capture_bit_identical_blocks"],
                      "faithful_load_blocks": result["faithful_load_blocks"],
                      "J_difference_counts": {name: result["J_difference_counts"][name]
                                              for name in RULES}}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
