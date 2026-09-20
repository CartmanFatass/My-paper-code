"""FSD persistence B07: the D1280 skill held ten steps against the same D redrawn every step.

Exploration (six fits), prospective entry in the direction notebook:
docs/research/candidates/flexible_skill_duration/NOTES.md, "2026-09-19 23:58 PDT - prospective:
persistence contrast inside the D family, skill held 10 steps against redrawn every step".

Thin entry over the frozen baseline x interruption B01 runner, as the matched-information,
flat-entropy (B03), flat-update (B04) and flat-input-scale (B05) entries are: the same collector
loop, panel law, summary and fit validation, rebound to this object's identity, on blocks 772803 /
772903 / 773003 with 45 rollouts and the matched-information stage-1 panels (5, 10, ... 45).

  D_K10   the stage-1 D1280 construction exactly: the frozen runner's `("D0", 1280)` arm with
          `skill_cap_k_max = team_cap_k_Z = k = 10`.  Nothing at all is changed, so its recorded
          configuration snapshot must equal the published stage-1 D1280 fit of the same block.
  D_K1    the same construction with three fields set, and only those three:

            skill_cap_k_max         10 -> 1
            team_cap_k_Z            10 -> 1
            coordinator_batch_size  1280 -> 12800

          `config.k` stays 10.  On the d2 route the decision cadence is governed by the two caps
          (hmasd/agent.py:2596, 2613 against the ages kept at hmasd/agent.py:2709-2719), and
          `config.k` is only the low-level update's truncated-BPTT chunk length
          (hmasd/agent.py update_discoverer_from_rollout; the sampler carries the skills per step,
          hmasd/utils.py get_discoverer_sampler) and two buffer fields nothing consumes.  So both
          arms run the identical low-level update law, and the coordinator's batch is raised to
          12800 so that both arms take exactly one full-pool minibatch per epoch (the pool is
          num_envs x rollout_length // k rows at caps of 10 and num_envs x rollout_length at caps
          of 1; `hmasd/utils.py:1523-1527` cuts ceil(rows / coordinator_batch_size) minibatches per
          epoch).  The pool size itself cannot be matched; the notebook entry names that, the
          per-hop discount and the one-step segment return as the package differences.

`make_config` builds the D1280 construction for both arms and applies the arm's overrides to it,
then re-runs `validate_config()` and `calculate_and_set_buffer_sizes()` in `update_env_dims`'s own
order and refuses any configuration-snapshot difference from the D1280 construction other than the
arm's declared fields.  Where the published stage-1 D1280 summary of the block is readable, the
snapshot is compared with it as well, by B06's guard (`probe_fsd_d_state_scale_b06`): only the
fields the host geometry forces may differ, and only on a shrunken test host.  The execution node's
sparse checkout does not carry `runs/`, so an unreadable recorded fit is recorded as unavailable
with its reason rather than failing the fit; `reduce` makes that comparison mandatory.

During training collection a read-only capture wraps the learner agent's own `step` for the
duration of the fit and records, per rollout, the executed actions' autocorrelation, the UAVs'
visited 50 m cells and path length, and the fraction of steps on which a skill changes.  It calls
through to the frozen method, consumes no RNG, copies every array before storing it and is removed
in a `finally`; `D_K10`'s panel scores are bit-identical to the published D1280 fit's, which is the
runtime proof that it changes nothing, and `reduce` reports that per block.

`fit` is result-bearing and runs only through `scripts/hmasd_launch.py` (runner-side admission).
`reduce` is a pure reading of published summaries and carries no admission.
"""
import argparse
import inspect
import json
import sys
from pathlib import Path

import numpy as np

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
from scripts.hmasd_admission import require_admission

shared = b01.shared
DIRECTION = "flexible_skill_duration"
OBJECT_ID = "FSD_PERSISTENCE_B07"
CARD = ("docs/research/candidates/flexible_skill_duration/NOTES.md "
        "(2026-09-19 23:58 PDT, persistence contrast inside the D family, skill held 10 steps "
        "against redrawn every step)")
BLOCKS = dict(scale.BLOCKS)  # 772803, 772903, 773003
# The frozen runner dispatches on the arm name; both arms are the `D0` renewal route, so this
# object names them itself and `factorial_arm` carries the real arm name.
ARMS = {"D_K10": ("D0", 1280), "D_K1": ("D0", 12800)}
PERSISTENCE_ARMS = ("D_K10", "D_K1")
REFERENCE_ARM = "D_K10"  # the construction both arms are built from
# The only configuration fields either arm may move away from the D1280 construction.
ARM_OVERRIDES = {"D_K10": {},
                 "D_K1": {"skill_cap_k_max": 1, "team_cap_k_Z": 1, "coordinator_batch_size": 12800}}
ARM_CAPS = {"D_K10": (10, 10), "D_K1": (1, 1)}  # (skill_cap_k_max, team_cap_k_Z)
FROZEN_CAPS = ARM_CAPS[REFERENCE_ARM]
SKILL_PERIOD = 10  # `config.k`, identical in both arms
D_REFERENCE = "D1280"  # the published stage-1 fits of FSD_MATCHED_INFORMATION_BASELINE_B01
FLAT_CONTEXT = scale.INPUT_SCALE_ARMS[0]  # CF_S, supplied as context only
RECORDED_FITS = dict(probe.RECORDED_FITS)  # runs/.../b01_s1_d1280_<block>_a01/summary.json
GEOMETRY_FIELDS = probe.GEOMETRY_FIELDS
ROLLOUTS = matched.ROLLOUTS  # 45
PANEL_ROLLOUTS = matched.PANEL_ROLLOUTS  # 5, 10, ... 45
# B05's reduce reads its windows as the first four and the last four panels; this object keeps that
# definition and reports the notebook entry's three-panel late window beside it.
EARLY_PANELS, LATE_PANELS = PANEL_ROLLOUTS[:4], PANEL_ROLLOUTS[-4:]
LATE_PANELS_35_45 = PANEL_ROLLOUTS[-3:]
DIAGNOSTIC_ROLLOUTS = update.DIAGNOSTIC_ROLLOUTS  # (1,) + the nine panel rollouts
# One-based training rollouts of the two behaviour windows the notebook entry names.
BEHAVIOUR_EARLY_ROLLOUTS = tuple(range(1, 6))
BEHAVIOUR_LATE_ROLLOUTS = tuple(range(35, ROLLOUTS + 1))
WALL_PLANS = {"D_K10": 10300., "D_K1": 20600.}  # the D1280 plan, and twice it; not deadlines
PRIMARY_NAME = f"J_{ROLLOUTS}"
DIFFERENCE_THRESHOLD = .05  # the notebook entry's declared size for J and for the lag-5 reading
AUTOCORRELATION_LAGS = (1, 2, 5, 9, 10, 20)
CELL_METRES = 50.
CURRENT = {"persistence_arm": None, "admission": None, "summary": None, "capture": None}
_orig_make_config = matched._orig_make_config  # the frozen `run_fsd_baseline_interruption_b01`'s
_orig_build_learner = b01.build_learner
_orig_base_summary = shared.base_summary
_FLAG = "_persistence_wrapper"

STATE_LAYOUT_NOTE = (
    "envs/pettingzoo/uav_env.py MultiUAVEnv._get_state (lines 353-366) concatenates "
    "n_uavs x (x, y, z) UAV positions in metres, then n_users x (x, y) user positions in metres, "
    "then current_step / max_steps; the UAV block is the leading 3 * n_uavs entries and x, y are "
    "clipped to [0, area_size] and z to the height band by the environment's own step")
EXECUTED_ACTION_NOTE = (
    "the array `agent.step` returns at run_fsd_baseline_interruption_b01.py:113, which the frozen "
    "collector hands lane by lane to the training environment at "
    "run_fsd_baseline_interruption_b01.py:121 without touching it; the environment converts it to "
    "a velocity and never writes into it (envs/pettingzoo/uav_env.py:280-294), and the capture "
    "stores a copy")


def bind(wrap=False):
    """Rebind the frozen runner's identities to this object; loop, panel law and validation stand.

    Readers need the identities only. A fit also wraps `shared.base_summary` and the frozen
    `build_learner` (the one point at which this object's read-only capture reaches the learner
    agent), and `run_fit` takes both off again, so a later reader or fit of another object in the
    same process is not marked.
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
                             (update._FLAG, update), (scale._FLAG, scale)):
            if getattr(current, flag, False):
                current = module._orig_base_summary
        if not getattr(current, _FLAG, False):
            _orig_base_summary = current
        shared.base_summary = base_summary
        b01.build_learner = build_learner


# ---------------------------------------------------------------------------
# the construction: the D1280 one, plus this arm's declared overrides and nothing else
# ---------------------------------------------------------------------------


def host_geometry():
    """This object's own lanes and horizon; B06's `FROZEN_GEOMETRY` is the frozen host's."""
    return {"train_lanes": int(shared.TRAIN_LANES), "eval_lanes": int(shared.EVAL_LANES),
            "horizon": int(shared.HORIZON)}


def config_differences(config, other):
    """Every snapshot field where `config` differs from `other` (B06's comparison)."""
    return probe.config_differences(config, other)


def allowed_differences(arm):
    """The fields a fit of `arm` may differ from the recorded D1280 fit in."""
    allowed = set(ARM_OVERRIDES[arm])
    if host_geometry() != probe.FROZEN_GEOMETRY:  # a shrunken test host, never the frozen one
        allowed |= set(GEOMETRY_FIELDS)
    return allowed


def require_recorded_construction(config, recorded_config, phase, arm):
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
    fit cannot depend on this file existing. The declared-difference guard in `make_config` needs
    no file at all; this comparison is additional, and `reduce` requires it. A file that is present
    but is not that block's completed D1280 fit fails loudly: `probe.recorded_fit` raises.
    """
    path = RECORDED_FITS[int(seed)]
    if not path.exists():
        return None, f"{path.relative_to(ROOT).as_posix()} is not in this checkout"
    return probe.recorded_fit(int(seed))[0], None


def _record_recorded_comparison(phase, arm, snapshot, block_seed):
    """Compare one phase's snapshot with the recorded D1280 fit's and put the result on the summary."""
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
    """The frozen D1280 construction, then this arm's declared overrides and nothing else.

    Both arms are built from `ARMS[REFERENCE_ARM]`, so the baseline is literally the stage-1 D1280
    construction of the block; the arm's overrides are applied to it and the resulting snapshot may
    differ from that baseline in exactly the arm's declared fields. `configs/config_1.py`'s
    `update_env_dims` runs `validate_config()` and then `calculate_and_set_buffer_sizes()` after the
    environment dimensions are set; both are re-run here in that order after the overrides, and the
    difference guard below shows that neither moved a recorded field (the cap fields feed the d2
    validator only, and no buffer field is derived from them or from `coordinator_batch_size`).
    """
    if arm not in ARM_OVERRIDES:
        raise ValueError(f"unknown arm {arm}")
    config = _orig_make_config(REFERENCE_ARM, envs, seed)
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
    for field, value in overrides.items():
        if differences[field]["probe"] != value:
            raise ValueError(f"{arm}'s {field} was not set to {value!r}")
    if CURRENT["persistence_arm"] is not None:  # None reproduces the construction alone (tests)
        summary = CURRENT.get("summary")
        block_seed = int(summary["block_seed"]) if summary else int(seed)
        phase = "learner_config" if (summary or {}).get("learner_config") is None else "evaluation_config"
        _record_recorded_comparison(phase, arm, snapshot, block_seed)
    return config


# ---------------------------------------------------------------------------
# read-only behaviour capture of the training collection
# ---------------------------------------------------------------------------


DEFINITIONS = {
    "action_autocorrelation": (
        "per (lane, agent, action dimension) series of the executed action over the rollout's "
        "steps: with x the series and m its mean over the rollout, "
        "r(h) = sum_t (x_t - m)(x_{t+h} - m) / sum_t (x_t - m)^2, the sums over every t for which "
        "both entries exist; the reported value is the mean of r(h) over the series whose entries "
        "are not all exactly equal and whose mean-removed sum of squares is positive, and the "
        "others are counted in `action_series_skipped`. Lags cross episode boundaries only if a "
        "rollout "
        "holds more than one episode, which the frozen loop's full-terminal-episode rule forbids"),
    "executed_actions": EXECUTED_ACTION_NOTE,
    "cells_visited": (
        f"number of distinct ({CELL_METRES:g} m x {CELL_METRES:g} m) cells, indexed by "
        f"floor(x / {CELL_METRES:g}) and floor(y / {CELL_METRES:g}), that a UAV's position occupies "
        "over the steps of one episode, averaged over the lanes and the UAVs of the rollout; the "
        "positions are the ones the learner was handed at each of its own steps, so an episode "
        "contributes its `rollout_length` visited positions"),
    "path_length": (
        "sum over consecutive steps of one episode of the Euclidean distance in metres between a "
        "UAV's (x, y, z) positions, averaged over the lanes and the UAVs of the rollout"),
    "net_displacement": (
        "Euclidean distance in metres between a UAV's last and first (x, y, z) position of one "
        "episode, averaged over the lanes and the UAVs of the rollout"),
    "path_over_net_displacement": (
        "per (lane, UAV) episode, path length divided by net displacement, averaged over the lanes "
        "and UAVs with a positive net displacement; the others are counted in "
        "`net_displacement_zero_series`"),
    "skill_change_fraction": (
        "fraction of the (step, lane, agent) triples of the rollout whose previous step belongs to "
        "the same episode on which the agent's skill differs from that previous step's, and the "
        "same over (step, lane) for the team skill; the skills are the ones `agent.step` returns "
        "in its `step_data` for the step it just decided (hmasd/agent.py:3285-3287)"),
    "decision_fraction": (
        "fraction of the (step, lane) pairs on which the d2 route took a team decision, and the "
        "mean over (step, lane, agent) of its sampled mask, both read from the same `step_data` "
        "(hmasd/agent.py:3297-3300); at caps of 1 every step is a team decision and every agent is "
        "in S_t, at caps of 10 one step in ten is"),
    "state_layout": STATE_LAYOUT_NOTE,
}


class BehaviourCapture:
    """Per-rollout behaviour of one fit's training collection; reads only.

    The learner agent's own `step` is wrapped on the instance for the duration of the fit: the
    wrapper calls the frozen method first and then copies what it returns, so the collector, the
    environments, the RNG streams and every array handed on are exactly the unwrapped route's. The
    evaluator is a different agent instance and is never touched, so the evaluation panels are the
    frozen ones.
    """

    def __init__(self, summary, *, horizon=None, rollouts=None,
                 lags=AUTOCORRELATION_LAGS, cell_metres=CELL_METRES):
        self.summary = summary
        self.horizon = int(shared.HORIZON if horizon is None else horizon)
        self.rollouts = int(ROLLOUTS if rollouts is None else rollouts)
        self.lags = tuple(int(lag) for lag in lags)
        self.cell_metres = float(cell_metres)
        self.rows = [] if summary is None else summary.setdefault("behaviour", [])
        self.calls, self.finalized = 0, 0
        self.agent, self._original_step, self._provenance = None, None, None
        self._buffer = []

    # -- attachment ---------------------------------------------------------

    def attach(self, agent):
        if self._original_step is not None:
            raise ValueError("the behaviour capture is already attached")
        config = agent.config
        self.n_agents, self.n_users = int(config.n_agents), int(config.n_users)
        self.state_dim = int(config.state_dim)
        expected = 3 * self.n_agents + 2 * self.n_users + 1
        if self.state_dim != expected:
            raise ValueError(
                f"the state layout of n_uavs={self.n_agents}, n_users={self.n_users} gives "
                f"{expected} entries, not the configured state_dim {self.state_dim}; the UAV "
                "positions cannot be read from it")
        original = agent.step

        def step(*args, **kwargs):
            result = original(*args, **kwargs)
            if not isinstance(result, tuple) or len(result) != 3:
                raise ValueError(
                    "the behaviour capture expects the collector's `return_step_data=True` call")
            self._record(args, kwargs, result[0], result[2])
            return result

        agent.step = step  # an instance attribute only; the class is untouched
        self.agent, self._original_step = agent, original
        self._provenance = self.provenance()
        if self.summary is not None:
            self.summary["behaviour_capture"] = self._provenance
        return self

    def detach(self):
        """Idempotent; always called in the fit's `finally`."""
        if self.agent is not None and self._original_step is not None:
            self.agent.__dict__.pop("step", None)
        self.agent, self._original_step = None, None
        self._buffer = []
        return self

    # -- recording ----------------------------------------------------------

    @staticmethod
    def _argument(args, kwargs, index, *names):
        """The collector calls positionally (b01:113); a keyword call is read by name."""
        if len(args) > index:
            return args[index]
        for name in names:
            if name in kwargs:
                return kwargs[name]
        raise ValueError(f"the learner's step was called without {names[0]}")

    def _record(self, args, kwargs, actions, step_data):
        states = self._argument(args, kwargs, 0, "states_batch", "states")
        env_steps = self._argument(args, kwargs, 2, "env_steps_batch", "env_steps")
        self.calls += 1
        states = np.asarray(states, dtype=np.float64)
        actions = np.array(actions, dtype=np.float64, copy=True)
        lanes = int(states.shape[0])
        if states.shape[1] != self.state_dim:
            raise ValueError(
                f"the collector's state is {states.shape[1]} wide, not the configured "
                f"{self.state_dim}")
        if actions.ndim != 3 or actions.shape[:2] != (lanes, self.n_agents):
            raise ValueError("the executed actions are not [lanes, agents, action dimensions]")
        entry = {
            "positions": states[:, :3 * self.n_agents].reshape(lanes, self.n_agents, 3).copy(),
            "actions": actions,
            "env_steps": np.array(env_steps, dtype=np.int64, copy=True).reshape(lanes),
            "team_skills": np.array(step_data["team_skills"], dtype=np.int64, copy=True).reshape(lanes),
            "agent_skills": np.array(step_data["agent_skills"], dtype=np.int64,
                                     copy=True).reshape(lanes, self.n_agents)}
        for name, key, shape in (("team_decision", "d2_team_decision", (lanes,)),
                                 ("sampled", "d2_sampled_mask", (lanes, self.n_agents))):
            value = step_data.get(key)
            entry[name] = (None if value is None
                           else np.array(value, dtype=bool, copy=True).reshape(shape))
        self._buffer.append(entry)
        if len(self._buffer) == self.horizon:
            self.finalize()

    def finalize(self):
        """Reduce one rollout's buffer to its behaviour row and drop it."""
        if not self._buffer:
            return None
        row = self.measure(self._buffer)
        row["rollout"] = self.finalized + 1
        self._buffer = []
        self.finalized += 1
        self.rows.append(row)
        if self._provenance is not None:  # the running summary keeps the true counts
            self._provenance.update(agent_step_calls=self.calls, finalized_rollouts=self.finalized)
        return row

    # -- the measures -------------------------------------------------------

    def measure(self, buffer):
        actions = np.stack([entry["actions"] for entry in buffer])  # [T, lanes, agents, dims]
        positions = np.stack([entry["positions"] for entry in buffer])  # [T, lanes, agents, 3]
        env_steps = np.stack([entry["env_steps"] for entry in buffer])  # [T, lanes]
        team_skills = np.stack([entry["team_skills"] for entry in buffer])
        agent_skills = np.stack([entry["agent_skills"] for entry in buffer])
        row = {"steps": int(actions.shape[0]), "lanes": int(actions.shape[1]),
               "agents": int(actions.shape[2]), "action_dimensions": int(actions.shape[3])}
        row.update(autocorrelation(actions, self.lags))
        row.update(displacement_measures(positions, env_steps, self.cell_metres))
        row.update(skill_change_measures(team_skills, agent_skills, env_steps))
        row.update(decision_measures(buffer))
        return row

    # -- provenance ---------------------------------------------------------

    def provenance(self):
        return {"attached_at": attachment_site(),
                "agent_step_calls": self.calls, "finalized_rollouts": self.finalized,
                "steps_per_rollout": self.horizon, "lags": list(self.lags),
                "cell_metres": self.cell_metres,
                "definitions": dict(DEFINITIONS)}


def attachment_site():
    """file:line of the statement that wraps the learner agent's `step`; located, never guessed."""
    lines, start = inspect.getsourcelines(BehaviourCapture.attach)
    offsets = [index for index, text in enumerate(lines) if text.strip().startswith("agent.step =")]
    line = start + offsets[0] if offsets else start
    return (f"{Path(__file__).resolve().relative_to(ROOT).as_posix()}:{line} wraps the learner "
            "agent instance's `step`, from the build_learner wrapper this object binds onto "
            "run_fsd_baseline_interruption_b01; the frozen collector calls it at "
            "run_fsd_baseline_interruption_b01.py:113")


def autocorrelation(actions, lags=AUTOCORRELATION_LAGS):
    """Mean autocorrelation of the executed-action series at each lag. See DEFINITIONS."""
    steps = int(actions.shape[0])
    series = actions.reshape(steps, -1)
    constant = np.all(series == series[0:1], axis=0)
    centred = series - series.mean(axis=0, keepdims=True)
    denominator = (centred * centred).sum(axis=0)
    usable = (~constant) & (denominator > 0.)
    values = {}
    for lag in lags:
        if lag >= steps or not usable.any():
            values[str(lag)] = None
            continue
        numerator = (centred[:-lag] * centred[lag:]).sum(axis=0)
        values[str(lag)] = float(np.mean(numerator[usable] / denominator[usable]))
    return {"action_autocorrelation": values,
            "action_series": int(series.shape[1]),
            "action_series_used": int(usable.sum()),
            "action_series_skipped": int((~usable).sum())}


def _episode_segments(env_steps):
    """(lane, start, stop) of every episode of one rollout, from the collector's own step counter."""
    steps, lanes = env_steps.shape
    segments = []
    for lane in range(lanes):
        starts = [t for t in range(steps) if int(env_steps[t, lane]) == 0]
        if not starts or starts[0] != 0:
            starts = [0] + starts
        for index, start in enumerate(starts):
            stop = starts[index + 1] if index + 1 < len(starts) else steps
            segments.append((lane, start, stop))
    return segments


def displacement_measures(positions, env_steps, cell_metres=CELL_METRES):
    """Visited cells, path length and net displacement per UAV per episode. See DEFINITIONS."""
    cells, path, net, ratio = [], [], [], []
    zero_net = 0
    for lane, start, stop in _episode_segments(env_steps):
        track = positions[start:stop, lane]  # [steps, agents, 3]
        if track.shape[0] == 0:
            continue
        indices = np.floor(track[:, :, :2] / float(cell_metres)).astype(np.int64)
        for agent in range(track.shape[1]):
            occupied = {(int(x), int(y)) for x, y in indices[:, agent, :]}
            cells.append(len(occupied))
            steps_ = np.linalg.norm(np.diff(track[:, agent, :], axis=0), axis=-1)
            length = float(steps_.sum())
            displacement = float(np.linalg.norm(track[-1, agent, :] - track[0, agent, :]))
            path.append(length)
            net.append(displacement)
            if displacement > 0.:
                ratio.append(length / displacement)
            else:
                zero_net += 1
    mean = lambda values: float(np.mean(values)) if values else None
    return {"cells_visited_mean": mean(cells), "cells_visited_max": max(cells) if cells else None,
            "path_length_metres_mean": mean(path), "net_displacement_metres_mean": mean(net),
            "path_over_net_displacement_mean": mean(ratio),
            "net_displacement_zero_series": zero_net,
            "episode_series": len(cells)}


def skill_change_measures(team_skills, agent_skills, env_steps):
    """Fraction of steps on which a skill differs from the previous step's. See DEFINITIONS."""
    steps = int(env_steps.shape[0])
    same_episode = env_steps[1:] > 0  # [T-1, lanes]; a zero counter is a fresh episode
    if steps < 2 or not same_episode.any():
        return {"agent_skill_change_fraction": None, "team_skill_change_fraction": None,
                "skill_change_comparisons": 0}
    team_changed = (team_skills[1:] != team_skills[:-1]) & same_episode
    agent_changed = (agent_skills[1:] != agent_skills[:-1]) & same_episode[:, :, None]
    comparisons = int(same_episode.sum())
    agents = int(agent_skills.shape[2])
    return {"agent_skill_change_fraction": float(agent_changed.sum() / (comparisons * agents)),
            "team_skill_change_fraction": float(team_changed.sum() / comparisons),
            "skill_change_comparisons": comparisons}


def decision_measures(buffer):
    """The d2 decision masks the learner already returns for the step it decided."""
    team = [entry["team_decision"] for entry in buffer if entry["team_decision"] is not None]
    sampled = [entry["sampled"] for entry in buffer if entry["sampled"] is not None]
    return {"team_decision_fraction": float(np.mean(np.stack(team))) if team else None,
            "agent_sampled_fraction": float(np.mean(np.stack(sampled))) if sampled else None,
            "decision_steps_recorded": len(team)}


# ---------------------------------------------------------------------------
# the fit
# ---------------------------------------------------------------------------


def build_learner(arm, summary, out, training_seed):
    """The frozen learner construction, with this object's capture attached to the agent it built.

    The one point at which the capture reaches the learner: the frozen `build_learner` runs first
    and unchanged, and the agent it returns is the one the frozen collector then steps.
    """
    envs, agent, theta0, counters = _orig_build_learner(arm, summary, out, training_seed)
    if CURRENT["persistence_arm"] is not None:
        capture = BehaviourCapture(summary)
        CURRENT["capture"] = capture
        capture.attach(agent)
        shared.publish(out, summary, "behaviour capture attached")
    return envs, agent, theta0, counters


def base_summary(*args, **kwargs):
    summary = _orig_base_summary(*args, **kwargs)
    arm = CURRENT["persistence_arm"]
    summary.update(persistence_object=OBJECT_ID, persistence_arm=arm,
                   arm_overrides=dict(ARM_OVERRIDES.get(arm, {})),
                   skill_period_k=SKILL_PERIOD, admission=CURRENT["admission"],
                   primary=PRIMARY_NAME, behaviour=[], behaviour_capture=None,
                   learner_config_differences_from_recorded_d1280=None,
                   evaluation_config_differences_from_recorded_d1280=None)
    CURRENT["summary"] = summary
    return summary


setattr(base_summary, _FLAG, True)


def plan_guard(arm, seed):
    """The notebook entry's six fits: both arms on the three blocks."""
    if arm not in ARMS:
        raise SystemExit(f"unknown arm {arm}")
    if seed not in BLOCKS:
        raise SystemExit("this object runs on blocks 772803, 772903 and 773003")


def run_fit(arm, seed, out, admission=None):
    plan_guard(arm, seed)
    bind(wrap=True)
    CURRENT.update(persistence_arm=arm, admission=admission, capture=None)
    try:
        return b01.run_fit(arm, seed, out)
    finally:
        capture = CURRENT.get("capture")
        if capture is not None:
            capture.detach()
        CURRENT.update(persistence_arm=None, admission=None, summary=None, capture=None)
        if shared.base_summary is base_summary:
            shared.base_summary = _orig_base_summary
        if b01.build_learner is build_learner:
            b01.build_learner = _orig_build_learner


# ---------------------------------------------------------------------------
# reading one fit
# ---------------------------------------------------------------------------


def persistence_panels(summary):
    """The frozen B01 panel reader's law, with this arm's declared caps.

    `run_fsd_baseline_interruption_b01.arm_panels` hard-codes `skill_cap_k_max = team_cap_k_Z = 10`
    for every non-flat arm (line 344), so it cannot read a fit whose caps are 1. Everything else is
    the frozen reader's own check, in its order: identity, exposure counts, learner updates,
    per-phase construction, lane seeds and the per-panel primary. `D_K10` is read by the frozen
    reader itself (`arm_panels`), and a test pins that this reader agrees with it there.
    """
    seed, arm = summary["block_seed"], summary["factorial_arm"]
    if arm not in ARMS:
        raise ValueError("not one of this object's arms")
    renewal, batch = ARMS[arm]
    k_max, k_Z = ARM_CAPS[arm]
    evaluation_seed = BLOCKS[seed]
    lanes, horizon = shared.EVAL_LANES, shared.HORIZON
    if (summary["object_id"] != OBJECT_ID or summary["card"] != CARD or summary["arm"] != renewal
            or summary["status"] != "complete" or summary["training_seed"] != seed
            or summary["evaluation_seed"] != evaluation_seed or summary["rollouts"] != ROLLOUTS
            or summary["panel_rollouts"] != list(PANEL_ROLLOUTS)):
        raise ValueError("incomplete or wrong arm/block/object")
    counts = summary["counts"]
    expected_counts = {
        "model_constructions": 2, "training_starts": 1, "checkpoint_loads": 0,
        "training_transitions": shared.TRAIN_LANES * horizon * ROLLOUTS,
        "stored_training_transitions": shared.TRAIN_LANES * horizon * ROLLOUTS,
        "training_episodes": shared.TRAIN_LANES * ROLLOUTS, "update_stages": ROLLOUTS,
        "training_agent_step_batches": horizon * ROLLOUTS,
        "evaluation_steps": lanes * horizon * len(PANEL_ROLLOUTS),
        "evaluation_agent_step_batches": horizon * len(PANEL_ROLLOUTS),
        "evaluation_episodes": lanes * len(PANEL_ROLLOUTS)}
    if any(counts[k] != v for k, v in expected_counts.items()):
        raise ValueError("incomplete training/panel exposure")
    rows = summary["training_rows"]
    if (len(rows) != ROLLOUTS or [r["rollout_index"] for r in rows] != list(range(ROLLOUTS))
            or not all(r["updated"] for r in rows)
            or any(summary["optimizer_calls"][k] <= 0
                   for k in ("discoverer_actor", "discoverer_critic"))):
        raise ValueError("missing learner updates")
    if summary["optimizer_calls"]["coordinator"] <= 0:
        raise ValueError("renewal arm without coordinator updates")
    for key, count, phase_seed in (("learner_config", shared.TRAIN_LANES, seed),
                                   ("evaluation_config", lanes, evaluation_seed)):
        config = summary[key]
        expected = {"n_agents": shared.N_UAVS, "n_users": shared.N_USERS, "num_envs": count,
                    "rollout_length": horizon, "seed": phase_seed,
                    "policy_interruption_mode": "d2", "interruption_cost_c_Z": "Infinity",
                    "interruption_cost_c": "Infinity", "interruption_delta": 1,
                    "age_feature": "off", "n_Z": 6, "n_z": 6, "k": SKILL_PERIOD,
                    "skill_cap_k_max": k_max, "team_cap_k_Z": k_Z,
                    "coordinator_batch_size": batch}
        if any(config.get(key_) != value for key_, value in expected.items()):
            raise ValueError("arm construction mismatch: " + key)
    if (summary["training_lane_seeds"] != list(range(seed, seed + shared.TRAIN_LANES))
            or summary["evaluation_lane_seeds"] != list(range(evaluation_seed, evaluation_seed + lanes))
            or [p["panel_rollouts"] for p in summary["panels"]] != list(PANEL_ROLLOUTS)):
        raise ValueError("wrong lane seeds or panel schedule")
    scores = {}
    for panel in summary["panels"]:
        if (panel["status"] != "complete" or panel["after_update"] != panel["panel_rollouts"]
                or panel["episode_ids"] != list(range(lanes))
                or panel["lane_seeds"] != summary["evaluation_lane_seeds"]
                or panel["steps_per_lane"] != [horizon] * lanes
                or panel["completed_episodes"] != lanes
                or any(panel["evaluator_optimizer_calls"].values())):
            raise ValueError(f"wrong panel {panel['panel_rollouts']}")
        values = np.asarray(panel["native_scores_J"], dtype=np.float64)
        returns = np.asarray(panel["returns_U"], dtype=np.float64)
        if values.shape != (lanes,) or returns.shape != values.shape:
            raise ValueError("missing primary values")
        shared.require_finite((values, returns), "panel primary")
        if not np.allclose(returns * shared.N_UAVS / horizon, values, rtol=1e-9, atol=1e-9):
            raise ValueError("native return scaling mismatch")
        scores[panel["panel_rollouts"]] = values
    return scores


def arm_panels(summary):
    """`D_K10` is read by the frozen reader; `D_K1`'s caps are outside its hard-coded expectation."""
    arm = summary.get("factorial_arm")
    if arm not in ARMS:
        raise ValueError("not one of this object's arms")
    if ARM_CAPS[arm] == FROZEN_CAPS:
        return b01.arm_panels(summary)
    return persistence_panels(summary)


def fit_endpoint(summary, recorded=None):
    """Validated per-panel world scores of one complete fit of this object.

    With `recorded` (the published stage-1 D1280 summary of the same block) the recorded
    construction is compared as well, which is what `reduce` always does.
    """
    bind()
    if summary.get("persistence_object") != OBJECT_ID:
        raise ValueError("not a persistence fit")
    arm = summary.get("persistence_arm")
    if arm not in PERSISTENCE_ARMS or int(summary.get("block_seed", -1)) not in BLOCKS:
        raise ValueError("not one of this object's six planned fits")
    if summary.get("factorial_arm") != arm:
        raise ValueError("the recorded arm name and the frozen runner's arm disagree")
    scores = arm_panels(summary)
    if summary.get("arm_overrides") != ARM_OVERRIDES[arm]:
        raise ValueError(f"{arm} does not record its declared overrides")
    epochs = int(summary["learner_config"]["ppo_epochs"])
    if summary["optimizer_calls"]["coordinator"] != epochs * ROLLOUTS:
        raise ValueError(
            f"{arm} took {summary['optimizer_calls']['coordinator']} coordinator steps, not the "
            f"{epochs * ROLLOUTS} of one full-pool minibatch per epoch")
    behaviour = summary.get("behaviour")
    if not isinstance(behaviour, list) or [r.get("rollout") for r in behaviour] != list(
            range(1, ROLLOUTS + 1)):
        raise ValueError(f"{arm} does not carry one behaviour row per rollout")
    if recorded is not None:
        for phase in ("learner_config", "evaluation_config"):
            require_recorded_construction(summary[phase], recorded[phase], phase, arm)
    return scores


def host_view(summary):
    """What every fit of a block must share, whatever its arm."""
    return entropy.host_view(summary)


def pair_view(summary):
    """Everything the two arms of a block must share; the declared overrides are excluded."""
    common = host_view(summary)
    differences = set(ARM_OVERRIDES["D_K1"])
    for phase in ("learner_config", "evaluation_config"):
        common[phase] = {k: v for k, v in summary[phase].items() if k not in differences}
    return common


def diagnostics(summary):
    """B04's per-rollout learner records, plus the coordinator's and the d2 segment lengths."""
    result = update.diagnostics(summary)
    rows = summary["training_rows"]
    for rollout in DIAGNOSTIC_ROLLOUTS:
        row = rows[rollout - 1]
        losses = row.get("losses") or {}
        displacement = row.get("relative_initialization_displacement") or {}
        segments = row.get("segments") or {}
        result[str(rollout)].update(
            coordinator_policy_loss=losses.get("coordinator_policy_loss"),
            coordinator_value_loss=losses.get("coordinator_value_loss"),
            team_skill_entropy=losses.get("team_skill_entropy"),
            agent_skill_entropy=losses.get("agent_skill_entropy"),
            mean_high_level_reward=losses.get("mean_high_level_reward"),
            coordinator_displacement=displacement.get("coordinator"),
            segment_length_agent_mean=(segments.get("agent") or {}).get("mean"),
            segment_length_team_mean=(segments.get("team") or {}).get("mean"))
    values = [(row.get("losses") or {}).get("coordinator_policy_loss") for row in rows]
    result["mean_coordinator_policy_loss"] = (
        float(np.mean(values)) if all(v is not None for v in values) else None)
    entropies = [(row.get("losses") or {}).get("team_skill_entropy") for row in rows]
    result["mean_team_skill_entropy"] = (
        float(np.mean(entropies)) if all(v is not None for v in entropies) else None)
    return result


BEHAVIOUR_KEYS = ("cells_visited_mean", "path_length_metres_mean", "net_displacement_metres_mean",
                  "path_over_net_displacement_mean", "agent_skill_change_fraction",
                  "team_skill_change_fraction", "team_decision_fraction",
                  "agent_sampled_fraction")


def behaviour_window(summary, rollouts):
    """Every behaviour measure of one fit, averaged over the one-based training rollouts given."""
    rows = {int(row["rollout"]): row for row in summary.get("behaviour") or []}
    selected = [rows[r] for r in rollouts if r in rows]
    mean = lambda values: float(np.mean(values)) if values else None
    result = {"rollouts": list(rollouts), "available_rollouts": len(selected)}
    for key in BEHAVIOUR_KEYS:
        result[key] = mean([row[key] for row in selected if row.get(key) is not None])
    result["action_autocorrelation"] = {
        str(lag): mean([row["action_autocorrelation"][str(lag)] for row in selected
                        if (row.get("action_autocorrelation") or {}).get(str(lag)) is not None])
        for lag in AUTOCORRELATION_LAGS}
    result["action_series_skipped"] = sum(int(row.get("action_series_skipped") or 0)
                                          for row in selected)
    return result


def fit_row(summary, scores):
    level = {r: float(np.mean(scores[r])) for r in PANEL_ROLLOUTS}
    return {"J_by_rollout": {str(r): level[r] for r in PANEL_ROLLOUTS},
            "J_early_window": float(np.mean([level[r] for r in EARLY_PANELS])),
            "J_late_window": float(np.mean([level[r] for r in LATE_PANELS])),
            "J_late_window_35_45": float(np.mean([level[r] for r in LATE_PANELS_35_45])),
            "endpoint_scores_J": np.asarray(scores[ROLLOUTS], dtype=np.float64).tolist(),
            "object_id": summary["object_id"], "launch_sha": summary["launch_sha"],
            "coordinator_batch_size": summary["learner_config"].get("coordinator_batch_size"),
            "skill_cap_k_max": summary["learner_config"].get("skill_cap_k_max"),
            "team_cap_k_Z": summary["learner_config"].get("team_cap_k_Z"),
            "k": summary["learner_config"].get("k"),
            "diagnostics": diagnostics(summary),
            "actor_displacement_parts": {str(r): scale.displacement_parts(summary, r)
                                         for r in (1, ROLLOUTS)},
            "behaviour": {"early": behaviour_window(summary, BEHAVIOUR_EARLY_ROLLOUTS),
                          "late": behaviour_window(summary, BEHAVIOUR_LATE_ROLLOUTS)},
            "behaviour_capture": summary.get("behaviour_capture"),
            "counts": summary["counts"], "optimizer_calls": summary["optimizer_calls"],
            "wall_seconds_before_publication": summary.get("wall_seconds_before_publication"),
            "peak_rss_bytes": summary.get("peak_rss_bytes")}


def reference_row(summary, scores, arm):
    """A published reference fit, read by its own object's validator."""
    level = {r: float(np.mean(scores[r])) for r in PANEL_ROLLOUTS}
    return {"J_by_rollout": {str(r): level[r] for r in PANEL_ROLLOUTS},
            "J_early_window": float(np.mean([level[r] for r in EARLY_PANELS])),
            "J_late_window": float(np.mean([level[r] for r in LATE_PANELS])),
            "J_late_window_35_45": float(np.mean([level[r] for r in LATE_PANELS_35_45])),
            "endpoint_scores_J": np.asarray(scores[ROLLOUTS], dtype=np.float64).tolist(),
            "object_id": summary["object_id"], "launch_sha": summary["launch_sha"],
            "arm": arm, "diagnostics": update.diagnostics(summary),
            "counts": summary["counts"], "optimizer_calls": summary["optimizer_calls"],
            "wall_seconds_before_publication": summary.get("wall_seconds_before_publication")}


def reference_endpoint(summary):
    """A published stage-1 D1280 fit or a published B05 CF_S fit, by its own object's validator."""
    if int(summary.get("block_seed", -1)) not in BLOCKS:
        raise ValueError("the references are fits of the three blocks")
    if summary.get("factorial_arm") == D_REFERENCE and summary.get("stage") == 1:
        return D_REFERENCE, matched.fit_endpoint(summary)
    if summary.get("input_scale_arm") == FLAT_CONTEXT:
        return FLAT_CONTEXT, scale.fit_endpoint(summary)
    raise ValueError("the references are the stage-1 D1280 fits and the B05 CF_S fits")


# ---------------------------------------------------------------------------
# reduce
# ---------------------------------------------------------------------------


def bit_identical_panels(summary, recorded):
    """Whether every panel's native world scores of a fit equal the recorded fit's exactly."""
    mine = {int(p["panel_rollouts"]): p["native_scores_J"] for p in summary["panels"]}
    theirs = {int(p["panel_rollouts"]): p["native_scores_J"] for p in recorded["panels"]}
    if sorted(mine) != list(PANEL_ROLLOUTS) or sorted(theirs) != list(PANEL_ROLLOUTS):
        return {"bit_identical": False, "failure": "the panel schedules differ",
                "first_differing_panel": None}
    for rollout in PANEL_ROLLOUTS:
        if mine[rollout] != theirs[rollout]:
            return {"bit_identical": False, "failure": None, "first_differing_panel": rollout}
    return {"bit_identical": True, "failure": None, "first_differing_panel": None}


def _difference(left, right):
    return None if left is None or right is None else left - right


def reduce_fits(summaries, references):
    """Six new fits; the three published D1280 fits and, as context only, the three CF_S fits."""
    bind()
    shas = {s.get("launch_sha") for s in summaries}
    if len(shas) > 1:
        raise ValueError(f"mixed launch shas within the batch: {sorted(str(s) for s in shas)}")
    recorded, context, reference_failures, seen = {}, {}, {}, set()
    for summary in references:
        seed = int(summary.get("block_seed", -1))
        label = summary.get("factorial_arm") or summary.get("input_scale_arm")
        try:
            arm, values = reference_endpoint(summary)
        except (KeyError, TypeError, ValueError) as exc:
            reference_failures[f"{seed}:{label}"] = str(exc)
            continue
        if (seed, arm) in seen:
            raise ValueError("duplicate reference arm/block")
        seen.add((seed, arm))
        target = recorded if arm == D_REFERENCE else context
        target[seed] = (summary, reference_row(summary, values, arm))
    bind()  # the reference readers rebind the frozen runner to their own objects

    rows, sources, failures, supplied = {}, {}, {}, set()
    for summary in summaries:
        seed = int(summary.get("block_seed", -1))
        arm = summary.get("persistence_arm")
        if (seed, arm) in supplied:  # a second fit of the same cell is never a choice
            raise ValueError("duplicate arm/block")
        supplied.add((seed, arm))
        try:
            if summary.get("persistence_object") != OBJECT_ID:
                raise ValueError("not a fit of this object")
            if seed not in recorded:
                raise ValueError("the published D1280 fit of this block was not supplied")
            values = fit_endpoint(summary, recorded=recorded[seed][0])
        except (KeyError, TypeError, ValueError) as exc:
            failures[(seed, arm)] = str(exc)
            bind()
            continue
        bind()
        rows[(seed, arm)], sources[(seed, arm)] = fit_row(summary, values), summary

    blocks = []
    for seed in sorted(BLOCKS):
        cells = [(seed, arm) for arm in PERSISTENCE_ARMS]
        entry = {"training_seed": seed, "evaluation_seed": BLOCKS[seed],
                 "arms": {arm: rows[(s, arm)] for s, arm in cells if (s, arm) in rows},
                 "missing_or_invalid_arms": {arm: failures.get((s, arm), "not supplied")
                                             for s, arm in cells if (s, arm) not in rows},
                 "references": {D_REFERENCE: recorded[seed][1] if seed in recorded else None,
                                FLAT_CONTEXT: context[seed][1] if seed in context else None}}
        key = (seed, REFERENCE_ARM)
        if key in rows and seed in recorded:
            entry["capture_bit_identical"] = bit_identical_panels(sources[key], recorded[seed][0])
        else:
            entry["capture_bit_identical"] = {
                "bit_identical": False, "first_differing_panel": None,
                "failure": "the D_K10 fit or the published D1280 fit of this block is missing"}
        capture_inert = bool(entry["capture_bit_identical"]["bit_identical"])
        if all((seed, arm) in rows for arm in PERSISTENCE_ARMS):
            entry["status"] = "complete"
            if pair_view(sources[(seed, "D_K10")]) != pair_view(sources[(seed, "D_K1")]):
                entry.update(status="incomplete",
                             failure="the two arms differ outside the declared overrides")
        else:
            entry["status"] = "incomplete"
        if entry["status"] == "complete":
            level = {arm: {"late": rows[(seed, arm)]["J_late_window"],
                           "late_35_45": rows[(seed, arm)]["J_late_window_35_45"],
                           "J45": rows[(seed, arm)]["J_by_rollout"][str(ROLLOUTS)]}
                     for arm in PERSISTENCE_ARMS}
            for name in ("late", "late_35_45", "J45"):
                entry[f"D_K10_minus_D_K1_{name}"] = level["D_K10"][name] - level["D_K1"][name]
            entry["J"] = {arm: {"late": rows[(seed, arm)]["J_late_window"],
                                "late_35_45": rows[(seed, arm)]["J_late_window_35_45"],
                                "J45": rows[(seed, arm)]["J_by_rollout"][str(ROLLOUTS)]}
                          for arm in PERSISTENCE_ARMS}
            entry["training_return_U_rollouts_35_45"] = {
                arm: rows[(seed, arm)]["diagnostics"]["training_return_U_rollouts_35_45"]
                for arm in PERSISTENCE_ARMS}
            entry["coordinator"] = {
                arm: {"mean_policy_loss": rows[(seed, arm)]["diagnostics"]["mean_coordinator_policy_loss"],
                      "mean_team_skill_entropy": rows[(seed, arm)]["diagnostics"]["mean_team_skill_entropy"],
                      "displacement_by_rollout": {
                          str(r): rows[(seed, arm)]["diagnostics"][str(r)]["coordinator_displacement"]
                          for r in DIAGNOSTIC_ROLLOUTS},
                      "team_skill_entropy_by_rollout": {
                          str(r): rows[(seed, arm)]["diagnostics"][str(r)]["team_skill_entropy"]
                          for r in DIAGNOSTIC_ROLLOUTS},
                      "actor_displacement_parts": rows[(seed, arm)]["actor_displacement_parts"]}
                for arm in PERSISTENCE_ARMS}
            if capture_inert:
                entry["behaviour"] = {
                    "status": "read",
                    **{arm: rows[(seed, arm)]["behaviour"] for arm in PERSISTENCE_ARMS}}
                late = {arm: rows[(seed, arm)]["behaviour"]["late"]["action_autocorrelation"]
                        for arm in PERSISTENCE_ARMS}
                entry["behaviour"]["lag_autocorrelation_difference_late"] = {
                    str(lag): _difference(late["D_K10"][str(lag)], late["D_K1"][str(lag)])
                    for lag in AUTOCORRELATION_LAGS}
                entry["behaviour"]["cells_visited_difference_late"] = _difference(
                    rows[(seed, "D_K10")]["behaviour"]["late"]["cells_visited_mean"],
                    rows[(seed, "D_K1")]["behaviour"]["late"]["cells_visited_mean"])
            else:
                entry["behaviour"] = {
                    "status": "not_read",
                    "reason": ("D_K10's panel scores are not bit-identical to the published D1280 "
                               "fit's on this block, so the capture is not established as inert "
                               "here")}
        blocks.append(entry)

    complete = [b for b in blocks if b["status"] == "complete"]
    readable = [b for b in complete if b["behaviour"]["status"] == "read"]
    summary_out = {
        "object_id": OBJECT_ID, "card": CARD,
        "reference_object_ids": [matched.OBJECT_ID, scale.OBJECT_ID],
        "launch_sha": shared.e0._git("rev-parse", "HEAD"),
        "batch_launch_sha": next(iter(shas), None) if len(shas) == 1 else None,
        "status": "complete" if len(complete) == len(BLOCKS) else "incomplete",
        "arms": {arm: {"overrides": dict(ARM_OVERRIDES[arm]),
                       "coordinator_batch_size": ARMS[arm][1],
                       "caps": {"skill_cap_k_max": ARM_CAPS[arm][0], "team_cap_k_Z": ARM_CAPS[arm][1]}}
                 for arm in PERSISTENCE_ARMS},
        "quantity": (
            "J45 = mean of the 32 final world scores; `late` is the mean over panels "
            f"{', '.join(str(r) for r in LATE_PANELS)} (B05's reduce's window) and `late_35_45` the "
            f"mean over panels {', '.join(str(r) for r in LATE_PANELS_35_45)}; behaviour windows are "
            "training rollouts 1-5 and 35-45; differences are D_K10 minus D_K1 on the same training "
            "and evaluation seeds"),
        "declared_difference": (
            "skill_cap_k_max, team_cap_k_Z and coordinator_batch_size only; every other recorded "
            "configuration field of both arms must equal the published stage-1 D1280 fit of the "
            "block, and config.k stays 10 in both"),
        "blocks": blocks,
        "capture_bit_identical_blocks": int(sum(b["capture_bit_identical"]["bit_identical"]
                                                for b in blocks)),
        "behaviour_definitions": dict(DEFINITIONS),
        "invalid_inputs": {f"{seed}:{arm}": text for (seed, arm), text in failures.items()},
        "invalid_references": dict(reference_failures),
        "refusals": (
            "a batch of fits at more than one launch sha, a duplicate arm/block, a summary that is "
            "not this object's, an incomplete fit, a block whose published D1280 fit was not "
            "supplied, and any configuration difference from that fit outside the arm's three "
            "declared fields (the host-geometry fields are exempt only on a shrunken test host)"),
        "interpretation_limit": (
            "exploration; three blocks; the D1280 reference is the published stage-1 fit and is not "
            "contemporaneous; these blocks carried every flat and skill setting since B01, so no "
            "gap-size claim and no competence claim; the coordinator's sample pool, its per-hop "
            "discount and its one-step segment return differ with the caps and are not separable "
            "from persistence; no MEI verdict"),
    }
    counted = {}
    for name in ("late", "late_35_45", "J45"):
        values = [b[f"D_K10_minus_D_K1_{name}"] for b in complete]
        summary_out[f"D_K10_minus_D_K1_{name}"] = entropy.described(values)
        counted[f"D_K10_minus_D_K1_{name}"] = int(sum(v >= DIFFERENCE_THRESHOLD for v in values))
    lag_differences = [b["behaviour"]["lag_autocorrelation_difference_late"]["5"] for b in readable
                       if b["behaviour"]["lag_autocorrelation_difference_late"]["5"] is not None]
    summary_out["lag5_autocorrelation_difference_late"] = (
        entropy.described(lag_differences) if lag_differences else None)
    counted["lag5_autocorrelation_difference_late"] = int(
        sum(v >= DIFFERENCE_THRESHOLD for v in lag_differences))
    cells = [b["behaviour"]["cells_visited_difference_late"] for b in readable
             if b["behaviour"]["cells_visited_difference_late"] is not None]
    summary_out["cells_visited_difference_late"] = entropy.described(cells) if cells else None
    summary_out["blocks_at_or_above_threshold"] = dict(
        counted, threshold=DIFFERENCE_THRESHOLD, planned_blocks=len(BLOCKS),
        definition=("number of blocks whose D_K10 minus D_K1 difference is at least the threshold; "
                    "the J counts are over the blocks read as complete and the lag-5 count over "
                    "the blocks whose behaviour was read"))
    summary_out["blocks_with_behaviour_read"] = len(readable)
    return summary_out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    fit = sub.add_parser("fit")
    fit.add_argument("--arm", choices=tuple(PERSISTENCE_ARMS), required=True)
    fit.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    fit.add_argument("--launch-sha", help="must equal the admitted source SHA")
    fit.add_argument("--output-root", type=Path, required=True)
    red = sub.add_parser("reduce")
    red.add_argument("--summaries", type=Path, nargs="+", required=True, help="this object's six fits")
    red.add_argument("--references", type=Path, nargs="+", required=True,
                     help="the published stage-1 D1280 (B01) and, as context, the CF_S (B05) "
                          "summaries of the three blocks")
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

    args.output_root.mkdir(parents=True, exist_ok=True)
    result = reduce_fits([load(p) for p in args.summaries], [load(p) for p in args.references])
    result["input_summaries"] = [str(p) for p in args.summaries]
    result["reference_summaries"] = [str(p) for p in args.references]
    shared.write_json(args.output_root / "summary.json", result)
    print(json.dumps({"status": result["status"],
                      "capture_bit_identical_blocks": result["capture_bit_identical_blocks"],
                      "D_K10_minus_D_K1_late_mean": result["D_K10_minus_D_K1_late"]["mean"],
                      "lag5_autocorrelation_difference_late_mean":
                          (result["lag5_autocorrelation_difference_late"] or {}).get("mean")}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
