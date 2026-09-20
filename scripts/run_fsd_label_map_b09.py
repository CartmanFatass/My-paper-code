"""FSD label map B09: what does each *fixed* skill label do at the trained D1280's weights?

Exploration, prospective entry in the direction notebook:
docs/research/candidates/flexible_skill_duration/NOTES.md (2026-09-20 08:41 PDT next research
judgment; B09 prospective entry).

B08 measured the label's content by *destroying* the coordinator's assignment (freeze it, redraw it
every step, redraw it every ten steps) and read the drop in J.  B09 keeps the same fixed weights and
the same 32 evaluation worlds and asks the complementary question: what is the *map* from a label to
a score?  One panel per constant label - every agent, every lane, every step executes agent label c -
plus one panel of a uniformly drawn per-episode assignment, all beside B08's own `as_trained` panel.
That gives, per block, the whole label-to-J map, the spread between the best and the worst constant
label, the per-world envelope of the constant labels, and a place to put B08's `uniform_every_10`.

Two commands.

`probe` takes no optimizer step (every optimizer `step` of both agents raises for the whole command)
and carries no admission: like B08's probe it is policy execution at fixed weights, recorded as
exposure.  It is the B08 probe's construction and route, re-used rather than re-implemented: the same
`bind()`, the same `build_learner`/`load_model`/`build_evaluator`, the same recorded-D1280
configuration guard, the same weights sidecar verification, the same `run_rule_panel`, the same
`_panel_record`, and the same faithful-load check - the first panel, unmodified, must reproduce the
recorded rollout-45 panel's 32 native world scores bit for bit, and the probe stops there if it does
not.  The panels, in this fixed order:

  (a) `as_trained`              B08's own baseline panel, unchanged; then `faithful_load`
  (b) `constant_0` .. `constant_5`  one panel per agent label, executed everywhere and always
  (c) `uniform_frozen_episode`  one assignment drawn uniformly at each lane's episode reset and held

The rules are imposed exactly as B08 imposes its own, without touching `hmasd/`: `ExecutionRule`
wraps the evaluator agent instance's `_batched_assign_skills` for the duration of one panel and
writes the executed labels back into `env_team_skills`/`env_agent_skills`, and its guard refuses to
run at all unless both interruption costs are infinite (with a finite cost the held label enters the
trigger statistic, so replacing it would move the decision boundary as well as the behaviour).  This
object adds one subclass, `MapExecutionRule`, for the two new label maps, and binds it - together
with the new rule definitions - into B08's own module tables for the duration of the run only,
restoring them in a `finally`; after `probe` returns, B08's `RULES`, `RULE_DEFINITIONS`, `RULE_CAPS`,
`RANDOM_RULES`, `BASELINE_RULE` and `ExecutionRule` are the objects they were.  No cap is moved: the
caps-10 cadence is the frozen one on every panel, so the coordinator still decides at the same ticks
and only its *choice* is discarded.

`reduce` is a pure reading of published summaries and carries no admission.  It reads this object's
three probes beside B08's own three probes of the same three checkpoints and refuses a block whose
weights sha256, launch sha or `as_trained` world scores do not agree with B08's.

Nothing here is a fit: the label map is a deployment-time intervention on fixed weights and says
nothing about what training under a fixed label would produce.
"""
import argparse
import json
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for _directory in (ROOT, ROOT / "scripts"):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

import run_fsd_baseline_interruption_b01 as b01
import run_fsd_label_content_b08 as b08

shared = b08.shared
DIRECTION = "flexible_skill_duration"
OBJECT_ID = "FSD_LABEL_MAP_B09"
CARD = ("docs/research/candidates/flexible_skill_duration/NOTES.md "
        "(2026-09-20 08:41 PDT next research judgment; B09 prospective entry)")
BLOCKS = dict(b08.BLOCKS)  # 772803, 772903, 773003
SAVE_ARM = b08.SAVE_ARM  # the recorded stage-1 D1280 construction, unchanged
BASELINE_RULE = b08.BASELINE_RULE  # "as_trained"
# `config.n_Z = config.n_z = 6` on this construction
# (scripts/run_fsd_uav_individual_renewal_b01.py:92); `run_probe` refuses any other width rather
# than silently probing a label set that is not this one.
N_LABELS = 6
FROZEN_RULE = "uniform_frozen_episode"
CONSTANT_RULES = tuple(f"constant_{label}" for label in range(N_LABELS))
MAP_RULES = CONSTANT_RULES + (FROZEN_RULE,)
RULES = (BASELINE_RULE,) + MAP_RULES
# B08's rule this object's map is read against: the same cadence, the coordinator's choice replaced
# by a uniform draw at each decision.
REFERENCE_RULE = "uniform_every_10"
# The notebook entry's own sizes. A panel's conditional evaluation noise on this direction is about
# .03 J, which is the margin the three loosely held predictions are stated with; the envelope
# prediction is stated at .05, the direction's declared size for a J difference.
PANEL_NOISE = .03
PREDICTION_MARGIN = .03
ENVELOPE_MARGIN = b08.DIFFERENCE_THRESHOLD  # .05
WEIGHTS_NAME = b08.WEIGHTS_NAME
SIDECAR_NAME = b08.SIDECAR_NAME

SOURCE_NOTES = {
    "team_label_path": (
        "hmasd/networks.py:1801-1809 `SkillDiscoverer.forward` passes only the observation, the "
        "*agent* label and the hidden state, so the team label never reaches the low-level actor: it "
        "reaches the low-level critic (hmasd/networks.py:1557-1560) and the coordinator only. On a "
        "fixed-weight execution panel neither of those can move an action, so under `constant_c` the "
        "team label `c % n_Z` is bookkeeping - it keeps the agent's held team label and the executed "
        "one equal - and the behaviour is the agent label c alone"),
    "constant_write_back": (
        "the executed labels are written back into `env_team_skills`/`env_agent_skills` exactly as "
        "B08's rewriting rules write them (scripts/run_fsd_label_content_b08.py, "
        "`ExecutionRule._step`), so the label the agent holds is the label it executed. No cap is "
        "moved (`RULE_CAPS` adds nothing for these rules): the frozen caps-10 cadence stands, the "
        "coordinator decides at the same ticks as `as_trained` and only its choice is discarded"),
    "lane_to_world": (
        "an evaluation panel gives every lane exactly one episode of the whole horizon and scores "
        "that lane as its own world: `run_fsd_baseline_interruption_b01.py:211-254` sets "
        "`episode_ids` to `range(lanes)` and fills `return_sums_U`, `returns_U` and "
        "`native_scores_J` per lane, so entry `lane` of a per-lane record is index `lane` of "
        "`J_world_scores`. The drawn assignments are recorded in lane order with their own lane "
        "index and their episode index, and `episodes_per_lane` records how many episodes each lane "
        "actually ran: a lane with more than one would make the record a lane record and not a "
        "world record, which is why the count is published rather than assumed"),
    "oracle_envelope": (
        "for each world separately, the maximum over the constant labels of that world's score, "
        "averaged over the worlds. It is an upper envelope *selected on the same 32 scores it is "
        "computed from*: with 6 labels and a per-panel conditional evaluation noise of about .03 J "
        "the maximum of 6 noisy scores is biased upward by construction, so the envelope is a "
        "ceiling on what a perfect per-world label oracle could have scored here and is not an "
        "achievable policy, not a held-out estimate and not a difference anyone can act on"),
    "execution_rule_attachment": b08.SOURCE_NOTES["execution_rule_attachment"],
    "weight_transfer_to_evaluator": b08.SOURCE_NOTES["weight_transfer_to_evaluator"],
    "evaluation_route": b08.SOURCE_NOTES["evaluation_route"],
    "low_level_actor_label": b08.SOURCE_NOTES["low_level_actor_label"],
}

INTERPRETATION_LIMIT = (
    "a fixed-weight forward measurement, not a fit: zero optimizer steps, one block, one panel per "
    "execution rule on the same 32 worlds and the same evaluation seeds. Exploration; three blocks; "
    "one checkpoint per block. These rules are deployment-time interventions on fixed weights and "
    "say nothing about what training under a fixed label would produce, and nothing about what the "
    "coordinator would learn if a label were held. A panel's conditional evaluation noise on this "
    "direction is about .03 J, so smaller J differences between rules are not read; the oracle "
    "constant envelope is an upper envelope selected on the same scores. A fixed-weight panel is "
    "bit-reproducible only on the host that trained the checkpoint - B08's own local probe attempts "
    "failed the faithful load off that host - so this command runs on wsl_4070.")


# ---------------------------------------------------------------------------
# the label map: the rules and their definitions
# ---------------------------------------------------------------------------


def constant_rule(label):
    """The rule name that executes agent label `label` everywhere and always."""
    return f"constant_{int(label)}"


def constant_label(name):
    """The label a `constant_c` rule executes, or None where `name` is not one."""
    return int(name.split("_")[1]) if name in CONSTANT_RULES else None


def rule_definitions():
    """This object's rule definitions, and B08's own for the baseline panel it re-uses."""
    definitions = {
        name: (
            f"at every step, in every lane, every agent executes agent label {constant_label(name)} "
            f"and the team label is {constant_label(name)} % n_Z. "
            + SOURCE_NOTES["constant_write_back"] + ". " + SOURCE_NOTES["team_label_path"])
        for name in CONSTANT_RULES}
    definitions[FROZEN_RULE] = (
        "at each lane's episode reset the team label and each agent's label are drawn uniformly at "
        "random from a dedicated generator, `label_generator(evaluation_seed, "
        f"'{FROZEN_RULE}')`, and then held for the whole episode by the same holding logic B08's "
        "`frozen_episode` uses for the coordinator's own reset labels; the drawn labels are written "
        "back like every other rewriting rule and the caps-10 cadence is untouched, so the "
        "coordinator still decides at the same ticks and its choice is discarded. It is the random "
        "counterpart of `frozen_episode`: one fixed assignment per episode that the coordinator did "
        "not choose. The draws come from that dedicated generator alone and touch no global NumPy, "
        "Python or torch stream. The drawn assignment of every lane-episode is recorded, so a "
        "reading can relate the heterogeneity of an assignment to the world score it produced")
    definitions[BASELINE_RULE] = b08.RULE_DEFINITIONS[BASELINE_RULE]
    return definitions


RULE_DEFINITIONS = rule_definitions()


class MapExecutionRule(b08.ExecutionRule):
    """B08's execution rule with this object's two label maps added; everything else is B08's.

    Attachment, the infinite-interruption-cost guard, the cap handling, the write-back, the
    histograms and the change fractions are all inherited unchanged; only the choice of executed
    label is this object's, and only for the rules in `MAP_RULES`. A name B08 already defines runs
    B08's own `_step`, so the `as_trained` panel is the same panel with this class bound or not.
    """

    def __init__(self, name, agent, *, generator=None, horizon=None):
        super().__init__(name, agent, generator=generator, horizon=horizon)
        self.constant = constant_label(name)
        if self.constant is not None and self.constant >= self.n_z:
            raise ValueError(f"{name} is outside the agent's {self.n_z} agent labels")
        # `uniform_frozen_episode` only: one record per (lane, episode), in lane order.
        self.episode_labels = []
        self.episodes = None

    # -- the rule -----------------------------------------------------------

    def _step(self, team, agents):
        if self.name not in MAP_RULES:
            return super()._step(team, agents)  # B08's own rules, unchanged
        last = self.agent._d2_last_step
        reset = np.asarray(last["team_cause"], dtype=np.int64) == self.agent.D2_CAUSE_RESET
        team = np.asarray(team, dtype=np.int64).copy()
        agents = np.asarray(agents, dtype=np.int64).copy()
        lanes = int(team.shape[0])
        if self.constant is not None:
            agents[:, :] = self.constant
            team[:] = self.constant % self.n_Z  # bookkeeping: see SOURCE_NOTES["team_label_path"]
        else:
            if self.held_team is None or self.held_team.shape[0] != lanes:
                self.held_team = np.full(lanes, -1, dtype=np.int64)
                self.held_agents = np.full((lanes, agents.shape[1]), -1, dtype=np.int64)
                self.episodes = np.zeros(lanes, dtype=np.int64)
            if reset.any():  # B08's own draw, taken at the episode reset instead of at a decision
                drawn_team = self.generator.integers(0, self.n_Z, size=lanes)
                drawn_agents = self.generator.integers(0, self.n_z, size=agents.shape)
                for lane in np.flatnonzero(reset):
                    lane = int(lane)
                    labels = [int(value) for value in drawn_agents[lane]]
                    self.held_team[lane] = int(drawn_team[lane])
                    self.held_agents[lane] = drawn_agents[lane]
                    self.episode_labels.append({
                        "lane": lane, "episode": int(self.episodes[lane]), "step": int(self.steps),
                        "team_label": int(drawn_team[lane]), "agent_labels": labels,
                        "distinct_agent_labels": len(set(labels))})
                    self.episodes[lane] += 1
            # B08's `frozen_episode` holding, with the drawn labels in place of the coordinator's
            known = self.held_team >= 0
            team = np.where(known, self.held_team, team)
            agents = np.where(known[:, None] & (self.held_agents >= 0), self.held_agents, agents)
        for lane in range(lanes):  # every map rule rewrites; the held label is the executed one
            self.agent.env_team_skills[lane] = int(team[lane])
            self.agent.env_agent_skills[lane] = agents[lane].copy()
        self._record(team, agents, reset)
        return team, agents

    # -- the record ---------------------------------------------------------

    def measures(self):
        record = super().measures()
        if self.constant is not None:
            record["constant_label"] = int(self.constant)
            record["constant_team_label"] = int(self.constant % self.n_Z)
        if self.name == FROZEN_RULE:
            record["episode_labels"] = list(self.episode_labels)
            record["episodes"] = len(self.episode_labels)
            record["episodes_per_lane"] = (None if self.episodes is None
                                           else self.episodes.tolist())
            record["distinct_agent_labels_per_episode"] = [
                entry["distinct_agent_labels"] for entry in self.episode_labels]
            record["episode_label_definition"] = SOURCE_NOTES["lane_to_world"]
        return record


@contextmanager
def bound_rules():
    """Bind this object's rules into B08's tables for one run, and restore them on the way out.

    The direction's established bind-and-restore: B08's `run_rule_panel` reads `ExecutionRule` and
    `RANDOM_RULES` and B08's `ExecutionRule` reads `RULE_DEFINITIONS`, all as module globals, so the
    new rules are added there rather than by copying the panel routine. `RULES`, `RULE_CAPS` and
    `BASELINE_RULE` are not touched at all: no cap moves here and B08's own four-rule list is not
    this object's eight-rule one. Everything is put back in the `finally`, so a later reader, reduce
    or B08 command in the same process sees B08's own tables.
    """
    definitions = dict(b08.RULE_DEFINITIONS)
    random_rules, rule_class = b08.RANDOM_RULES, b08.ExecutionRule
    b08.RULE_DEFINITIONS.update(RULE_DEFINITIONS)
    b08.RANDOM_RULES = tuple(random_rules) + (FROZEN_RULE,)  # so the panel builds its generator
    b08.ExecutionRule = MapExecutionRule
    try:
        yield
    finally:
        b08.ExecutionRule = rule_class
        b08.RANDOM_RULES = random_rules
        b08.RULE_DEFINITIONS.clear()
        b08.RULE_DEFINITIONS.update(definitions)


def check_rule_record(name, record):
    """The run-time proof that a panel executed the label map it declares; raises where it did not.

    A histogram is the whole executed record of the panel, so it is the strongest available check:
    under `constant_c` every one of the (step, lane, agent) positions must carry c, and under
    `uniform_frozen_episode` no executed agent label may ever change within an episode.
    """
    agent_histogram = list(record.get("agent_label_histogram") or [])
    team_histogram = list(record.get("team_label_histogram") or [])
    changes = record.get("agent_label_change_fraction")
    team_changes = record.get("team_label_change_fraction")
    label = constant_label(name)
    if label is not None:
        if len(agent_histogram) <= label or "constant_team_label" not in record:
            raise ValueError(f"{name} carries no executed record of its own label map")
        elsewhere = {index: int(value) for index, value in enumerate(agent_histogram)
                     if index != label and value}
        if elsewhere or not agent_histogram[label]:
            raise ValueError(f"{name} executed agent labels other than {label}: {agent_histogram}")
        wanted = int(record["constant_team_label"])
        elsewhere = {index: int(value) for index, value in enumerate(team_histogram)
                     if index != wanted and value}
        if elsewhere:
            raise ValueError(f"{name} executed team labels other than {wanted}: {team_histogram}")
    if name in MAP_RULES and label is None:  # uniform_frozen_episode
        if changes is None or team_changes is None:
            raise ValueError(f"{name} recorded no label comparison, so it proves no holding")
    if name in MAP_RULES:
        if changes not in (0., None) or team_changes not in (0., None):
            raise ValueError(
                f"{name} changed an executed label within an episode: agent {changes}, "
                f"team {team_changes}")
    return record


def run_rule_panel(name, learner, evaluator, summary, out, index, *, evaluation_seed):
    """B08's own rule panel, with this object's run-time check of what it executed."""
    record = b08.run_rule_panel(name, learner, evaluator, summary, out, index,
                                evaluation_seed=evaluation_seed)
    return check_rule_record(name, record)


# ---------------------------------------------------------------------------
# the readings taken from the panels
# ---------------------------------------------------------------------------


def faithful_load_record(panel, reference):
    """B08's faithful-load check, unrelaxed: exact list equality of the 32 native world scores."""
    mine, theirs = panel["native_scores_J"], reference["native_scores_J"]
    faithful = mine == theirs
    first = next((index for index, (a, b) in enumerate(zip(mine, theirs)) if a != b), None)
    return {
        "faithful_load": bool(faithful),
        "first_differing_world": None if faithful else first,
        "worlds": len(mine),
        "reference_panel_rollouts": int(reference["panel_rollouts"]),
        "definition": (
            "the native world scores of the unmodified `as_trained` panel, run from the loaded "
            "weights through the frozen evaluator sync, compared with the recorded fit's own "
            "reference panel by exact list equality; this is B08's own check and it is not relaxed"),
        "weight_transfer": SOURCE_NOTES["weight_transfer_to_evaluator"]}


def constant_map(j_by_rule):
    """The label-to-J map of the constant panels: {label: J}."""
    return {label: float(j_by_rule[constant_rule(label)]) for label in range(N_LABELS)}


def best_constant(j_by_rule, baseline):
    """The constant label with the highest panel J, and the whole ranking beside it."""
    values = constant_map(j_by_rule)
    order = sorted(values, key=lambda label: (-values[label], label))  # ties to the lowest label
    best, worst = order[0], order[-1]
    return {
        "label": int(best), "J": values[best], "J_minus_as_trained": values[best] - baseline,
        "worst_label": int(worst), "worst_J": values[worst],
        "max_minus_min": values[best] - values[worst],
        "J_by_label": {str(label): values[label] for label in range(N_LABELS)},
        "ranking": [int(label) for label in order],
        "definition": (
            "the constant label whose own panel has the highest mean J on this block's 32 worlds, "
            "the lowest label breaking an exact tie; `ranking` is every label from the highest to "
            "the lowest panel J. One panel per label on the same worlds and the same evaluation "
            "seeds, so the comparison is paired; the conditional noise of a panel is about "
            f"{PANEL_NOISE} J and a gap smaller than that is not read")}


def per_world_best_constant(scores_by_rule, baseline_scores):
    """For each evaluation world the best constant label there, and the envelope of those maxima."""
    worlds = len(scores_by_rule[CONSTANT_RULES[0]])
    records, counts = [], {str(label): 0 for label in range(N_LABELS)}
    for world in range(worlds):
        values = {label: float(scores_by_rule[constant_rule(label)][world])
                  for label in range(N_LABELS)}
        best = min(values, key=lambda label: (-values[label], label))
        counts[str(best)] += 1
        records.append({"world": int(world), "label": int(best), "J": values[best],
                        "as_trained_J": float(baseline_scores[world]),
                        "J_minus_as_trained": values[best] - float(baseline_scores[world]),
                        "J_by_label": [values[label] for label in range(N_LABELS)]})
    envelope = float(np.mean([record["J"] for record in records])) if records else None
    return {
        "records": records, "worlds": worlds, "label_counts": counts,
        "oracle_constant_envelope_J": envelope,
        "definition": (
            "per world, the constant label with the highest score in that world (the lowest label "
            "breaking an exact tie) and that score; `oracle_constant_envelope_J` is the mean of "
            "those per-world maxima and `label_counts` is how often each label wins a world"),
        "selection_note": SOURCE_NOTES["oracle_envelope"]}


# ---------------------------------------------------------------------------
# the probe
# ---------------------------------------------------------------------------


def verify_weights(seed, weights):
    """B08's weights record: the sidecar beside the checkpoint, with its sha256 recomputed."""
    sidecar_path = Path(weights).parent / SIDECAR_NAME
    if not Path(weights).exists():
        raise ValueError(f"{weights} does not exist")
    if not sidecar_path.exists():
        raise ValueError(f"{sidecar_path} does not exist; the weights carry no sidecar record")
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    digest = b08.file_sha256(weights)
    if sidecar.get("sha256") != digest:
        raise ValueError("the weights file does not match the sha256 its sidecar records")
    if int(sidecar.get("block_seed", -1)) != int(seed):
        raise ValueError("the weights were saved by a fit of another block")
    return {"sidecar": str(sidecar_path), "sha256": digest,
            "bytes": int(Path(weights).stat().st_size), "sidecar_record": sidecar,
            "verified": "sha256 recomputed from the file and compared"}


def run_probe(seed, weights, out, launch_sha=None):
    """One block: B08's construction and saved weights, one panel per label, no update."""
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
        "construction_source": (
            f"{b08.OBJECT_ID} {SAVE_ARM} (the recorded stage-1 {b08.D_REFERENCE} construction): the "
            "frozen baseline x interruption B01 runner with B08's identities bound, B08's saved "
            "final weights loaded, zero optimizer steps; this object adds execution rules only"),
        "reference_object_id": b08.OBJECT_ID,
        "recorded_d1280_summary": str(b08.RECORDED_FITS[seed]),
        "reference_summary": str(b08.REFERENCE_FITS[seed]),
        "host_geometry": b08.host_geometry(),
        "frozen_host_geometry": b08.host_geometry() == b08.probe.FROZEN_GEOMETRY,
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
        result["interpretation_limit"] = INTERPRETATION_LIMIT
        shared.write_json(out / "summary.json", result)
    print(json.dumps({
        "status": result["status"], "failure": result["failure"], "block_seed": seed,
        "faithful_load": (result.get("faithful_load") or {}).get("faithful_load"),
        "J_by_rule": {name: (result.get("rules_measured") or {}).get(name, {}).get("J_mean")
                      for name in RULES},
        "best_constant_label": (result.get("best_constant_label") or {}).get("label"),
        "oracle_constant_envelope_J": result.get("oracle_constant_envelope_J"),
        "optimizer_steps": result.get("optimizer_steps"),
        "wall_seconds": result.get("wall_seconds")}))
    return 0 if result["status"] == "complete" else 1


def _run(result, seed, evaluation_seed, out, weights):
    """Build as B08's probe does, load its weights, run the eight panels, then read them."""
    result["weights_record"] = verify_weights(seed, weights)
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
        measured = {}
        with bound_rules():
            for index, name in enumerate(RULES):
                measured[name] = run_rule_panel(name, learner, evaluator, summary, out, index,
                                                evaluation_seed=evaluation_seed)
                result["rules_measured"] = dict(measured)
                if name == BASELINE_RULE:
                    faithful = faithful_load_record(summary["panels"][-1], reference)
                    result["faithful_load"] = faithful
                    if not faithful["faithful_load"]:
                        raise ValueError(
                            "the loaded weights do not reproduce the recorded panel; first "
                            f"differing world index {faithful['first_differing_world']}")
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
    envelope = per_world_best_constant(
        {name: measured[name]["J_world_scores"] for name in CONSTANT_RULES},
        measured[BASELINE_RULE]["J_world_scores"])
    result.update({
        "optimizer_steps": steps, "optimizer_calls": learner_calls,
        "rules_measured": measured,
        "J_by_rule": j_by_rule,
        "J_minus_as_trained": {name: j_by_rule[name] - baseline for name in RULES},
        "best_constant_label": best_constant(j_by_rule, baseline),
        "per_world_best_constant": envelope["records"],
        "per_world_best_constant_definition": envelope["definition"],
        "per_world_best_constant_label_counts": envelope["label_counts"],
        "oracle_constant_envelope_J": envelope["oracle_constant_envelope_J"],
        "oracle_envelope_minus_as_trained": (envelope["oracle_constant_envelope_J"] - baseline
                                             if envelope["oracle_constant_envelope_J"] is not None
                                             else None),
        "oracle_envelope_selection_note": envelope["selection_note"],
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
        raise ValueError("the probe does not carry all eight execution rules")
    if summary.get("optimizer_steps") != 0:
        raise ValueError("the probe took an optimizer step")
    scores = {name: list(measured[name]["J_world_scores"]) for name in RULES}
    widths = {len(value) for value in scores.values()}
    if len(widths) != 1:
        raise ValueError("the probe's panels do not all carry the same worlds")
    j_by_rule = {name: float(measured[name]["J_mean"]) for name in RULES}
    return {
        "block_seed": seed, "launch_sha": summary.get("launch_sha"),
        "weights_sha256": (summary.get("weights_record") or {}).get("sha256"),
        "faithful_load": True, "worlds": next(iter(widths)),
        "J_by_rule": j_by_rule,
        "J_world_scores": scores,
        "J_minus_as_trained": {name: j_by_rule[name] - j_by_rule[BASELINE_RULE] for name in RULES},
        "label_histogram_by_rule": {name: measured[name]["agent_label_histogram"]
                                    for name in RULES},
        "label_change_fraction_by_rule": {name: measured[name]["agent_label_change_fraction"]
                                          for name in RULES},
        "episode_labels": measured[FROZEN_RULE].get("episode_labels"),
        "episodes_per_lane": measured[FROZEN_RULE].get("episodes_per_lane"),
        "published_oracle_constant_envelope_J": summary.get("oracle_constant_envelope_J"),
        "wall_seconds": summary.get("wall_seconds")}


def b08_probe_row(summary):
    """One B08 probe of the same checkpoint, read by B08's own validated reader."""
    row = b08.probe_row(summary)  # refuses an incomplete, unfaithful or four-rule-short probe
    measured = summary.get("rules_measured") or {}
    row["as_trained_world_scores"] = list(measured[BASELINE_RULE]["J_world_scores"])
    return row


def block_reading(row, other):
    """One block: this object's label map beside B08's own four rules on the same checkpoint."""
    j_by_rule, scores = row["J_by_rule"], row["J_world_scores"]
    baseline = j_by_rule[BASELINE_RULE]
    constants = constant_map(j_by_rule)
    best = best_constant(j_by_rule, baseline)
    envelope = per_world_best_constant({name: scores[name] for name in CONSTANT_RULES},
                                       scores[BASELINE_RULE])
    reference = float(other["J_by_rule"][REFERENCE_RULE])
    histogram = [int(value) for value in row["label_histogram_by_rule"][BASELINE_RULE]]
    b08_histogram = [int(value) for value in other["label_histogram_by_rule"][BASELINE_RULE]]
    executions = sum(histogram)
    most_used = int(np.argmax(histogram)) if executions else None
    published = row["published_oracle_constant_envelope_J"]
    recomputed = envelope["oracle_constant_envelope_J"]
    return {
        "J_by_rule": j_by_rule,
        "J_minus_as_trained": row["J_minus_as_trained"],
        "b08_J_by_rule": dict(other["J_by_rule"]),
        "b08_J_minus_as_trained": dict(other["J_minus_as_trained"]),
        "best_constant": best,
        "best_constant_minus_as_trained": best["J"] - baseline,
        f"best_constant_minus_b08_{REFERENCE_RULE}": best["J"] - reference,
        "max_constant_minus_min_constant": best["max_minus_min"],
        "constants_above_as_trained_by_the_margin": [
            int(label) for label in range(N_LABELS)
            if constants[label] - baseline > PREDICTION_MARGIN],
        f"constants_at_or_below_b08_{REFERENCE_RULE}": [
            int(label) for label in range(N_LABELS) if constants[label] <= reference],
        f"every_constant_at_or_below_b08_{REFERENCE_RULE}": bool(
            max(constants.values()) <= reference),
        f"{FROZEN_RULE}_minus_as_trained": j_by_rule[FROZEN_RULE] - baseline,
        f"{FROZEN_RULE}_minus_b08_{REFERENCE_RULE}": j_by_rule[FROZEN_RULE] - reference,
        "oracle_constant_envelope_J": recomputed,
        "oracle_envelope_minus_as_trained": (None if recomputed is None
                                             else recomputed - baseline),
        "oracle_envelope_selection_note": envelope["selection_note"],
        "per_world_best_constant_label_counts": envelope["label_counts"],
        "published_oracle_constant_envelope_J": published,
        "oracle_envelope_matches_the_published_one": bool(published == recomputed),
        "constant_ranking": [
            {"rank": position + 1, "label": int(label), "J": constants[label],
             "J_minus_as_trained": constants[label] - baseline,
             f"J_minus_b08_{REFERENCE_RULE}": constants[label] - reference,
             "as_trained_executions": histogram[label],
             "as_trained_execution_fraction": (histogram[label] / executions
                                               if executions else None)}
            for position, label in enumerate(best["ranking"])],
        "as_trained_agent_label_histogram": histogram,
        "b08_as_trained_agent_label_histogram": b08_histogram,
        # The two `as_trained` panels are already required to carry identical world scores; the
        # executed histograms of one deterministic panel must then agree too, and this records it
        # rather than assuming it. It refuses nothing: the scores are the tie that was required.
        "as_trained_histogram_matches_b08": bool(histogram == b08_histogram),
        "coordinator_most_used_label": {
            "label": most_used,
            "executions": None if most_used is None else histogram[most_used],
            "execution_fraction": (None if most_used is None
                                   else histogram[most_used] / executions),
            "rank_among_constants": (None if most_used is None
                                     else best["ranking"].index(most_used) + 1),
            "J_as_a_constant": None if most_used is None else constants[most_used],
            "J_as_a_constant_minus_as_trained": (None if most_used is None
                                                 else constants[most_used] - baseline),
            "is_the_best_constant": bool(most_used == best["label"]),
            "is_the_worst_constant": bool(most_used == best["worst_label"]),
            "definition": (
                "the agent label the coordinator executed most often during the unmodified "
                "`as_trained` panel of this block, and where the same label ranks when it is the "
                "*only* label executed. A rank is a rank on 6 paired panels with a conditional "
                "noise of about .03 J; it is not a statement about what the coordinator's choice "
                "is for")},
        "weights_sha256": row["weights_sha256"],
        "episodes_per_lane": row["episodes_per_lane"],
        "frozen_episode_assignments": row["episode_labels"],
        "worlds": row["worlds"]}


def prediction_rows(readings):
    """The four statements the notebook entry declared before the run, counted where they are read.

    Arithmetic on the blocks that were read, with the statement each count belongs to. A count is
    not a weight of evidence, and none of these margins is a decision rule.
    """
    declared = {
        "P1_a_constant_label_beats_as_trained_on_772903": {
            "blocks": (772903,),
            "statement": ("on block 772903 at least one constant label's panel J exceeds "
                          f"`as_trained` by more than {PREDICTION_MARGIN} J"),
            "value": lambda r: r["best_constant_minus_as_trained"],
            "holds": lambda value: value > PREDICTION_MARGIN,
            "value_definition": "best constant J minus as_trained J on that block"},
        "P2_the_best_constant_is_within_the_margin_on_772803_and_773003": {
            "blocks": (772803, 773003),
            "statement": ("on blocks 772803 and 773003 the best constant label's panel J is within "
                          f"{PREDICTION_MARGIN} J of `as_trained`"),
            "value": lambda r: r["best_constant_minus_as_trained"],
            "holds": lambda value: abs(value) <= PREDICTION_MARGIN,
            "value_definition": "best constant J minus as_trained J on that block"},
        "P3_the_oracle_envelope_exceeds_as_trained_on_every_block": {
            "blocks": tuple(sorted(BLOCKS)),
            "statement": ("on all three blocks the oracle constant envelope exceeds `as_trained` "
                          f"by more than {ENVELOPE_MARGIN} J"),
            "value": lambda r: r["oracle_envelope_minus_as_trained"],
            "holds": lambda value: value > ENVELOPE_MARGIN,
            "value_definition": ("mean of the per-world maxima over the constant labels, minus "
                                 "as_trained J; " + SOURCE_NOTES["oracle_envelope"])},
        f"A_every_constant_at_or_below_b08_{REFERENCE_RULE}_on_772903": {
            "blocks": (772903,),
            "statement": ("the strongest alternative: on block 772903 every constant label's panel "
                          f"J is at or below B08's `{REFERENCE_RULE}`"),
            "value": lambda r: r[f"every_constant_at_or_below_b08_{REFERENCE_RULE}"],
            "holds": bool,
            "value_definition": (f"whether max over labels of constant J <= B08's {REFERENCE_RULE} "
                                 "J on that block")},
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
        "were read. A count of three blocks is not an interval and not a weight of evidence, and "
        "no margin here is a decision rule; a panel's conditional evaluation noise on this "
        f"direction is about {PANEL_NOISE} J")
    return rows


def reduce_inputs(probes, b08_probes):
    """This object's three probes beside B08's three probes of the same three checkpoints."""
    b08.bind()  # the pure reading B08's own reduce takes: identities only, nothing wrapped
    shas = {summary.get("launch_sha") for summary in probes}
    if len(shas) > 1:
        raise ValueError(f"mixed launch shas among the probes: {sorted(str(s) for s in shas)}")
    b08_shas = {summary.get("launch_sha") for summary in b08_probes}

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
    for summary in b08_probes:
        seed = int(summary.get("block_seed", -1))
        if seed in other_seen:
            raise ValueError("duplicate B08 probe block")
        other_seen.add(seed)
        try:
            others[seed] = b08_probe_row(summary)
        except (KeyError, TypeError, ValueError) as exc:
            other_failures[seed] = str(exc)

    blocks, readings = [], {}
    for seed in sorted(BLOCKS):
        entry = {"training_seed": seed, "evaluation_seed": BLOCKS[seed], "status": "incomplete",
                 "missing_or_invalid": {}}
        if seed not in rows:
            entry["missing_or_invalid"]["probe"] = failures.get(seed, "not supplied")
        if seed not in others:
            entry["missing_or_invalid"]["b08_probe"] = other_failures.get(seed, "not supplied")
        if seed in rows and seed in others:
            row, other = rows[seed], others[seed]
            entry["weights_match"] = bool(row["weights_sha256"]
                                          and row["weights_sha256"] == other["weights_sha256"])
            identical = row["J_world_scores"][BASELINE_RULE] == other["as_trained_world_scores"]
            entry["as_trained_identical_to_b08"] = bool(identical)
            if not entry["weights_match"]:
                entry["missing_or_invalid"]["weights"] = (
                    "this probe's weights sha256 is not the one B08's probe of the same block "
                    "recorded, so the two are not readings of one checkpoint")
            elif not identical:
                entry["missing_or_invalid"]["as_trained"] = (
                    "this probe's `as_trained` world scores are not B08's own, so the two probes "
                    "are not the same policy on the same worlds and the block is not read")
            else:
                entry["status"] = "complete"
                entry.update(block_reading(row, other))
                readings[seed] = entry
        else:
            entry["weights_match"] = None
            entry["as_trained_identical_to_b08"] = None
        blocks.append(entry)

    complete = [block for block in blocks if block["status"] == "complete"]
    across = b08._across
    result = {
        "object_id": OBJECT_ID, "card": CARD, "command": "reduce",
        "launch_sha": shared.e0._git("rev-parse", "HEAD"),
        "probe_launch_sha": next(iter(shas), None) if len(shas) == 1 else None,
        "b08_probe_launch_sha": next(iter(b08_shas), None) if len(b08_shas) == 1 else None,
        "reference_object_ids": [b08.OBJECT_ID],
        "status": "complete" if len(complete) == len(BLOCKS) else "incomplete",
        "arm": {"name": SAVE_ARM, "overrides": dict(b08.ARM_OVERRIDES[SAVE_ARM]),
                "coordinator_batch_size": b08.ARMS[SAVE_ARM][1],
                "caps": {"skill_cap_k_max": b08.ARM_CAPS[0], "team_cap_k_Z": b08.ARM_CAPS[1]}},
        "rules": list(RULES), "rule_definitions": dict(RULE_DEFINITIONS),
        "b08_rules": list(b08.RULES), "b08_reference_rule": REFERENCE_RULE,
        "quantity": (
            "J of a rule is the mean of its panel's native world scores at the saved weights; a "
            "difference is the rule minus `as_trained` on the same block, the same worlds and the "
            "same evaluation seeds, so every comparison here is paired within a block. B08's four "
            f"rules come from B08's own probe of the same checkpoint, and `{REFERENCE_RULE}` is the "
            "rule this map is read against"),
        "blocks": blocks,
        "blocks_read": len(complete),
        "invalid_probes": {str(seed): text for seed, text in failures.items()},
        "invalid_b08_probes": {str(seed): text for seed, text in other_failures.items()},
        "refusals": (
            "a batch of probes at more than one launch sha, a duplicate block among either set of "
            "probes, a summary that is not this object's probe, an incomplete probe, a probe "
            "without all eight rules or with an optimizer step, a probe that did not establish a "
            "faithful load, a block whose B08 probe was not supplied or is not readable by B08's "
            "own reader, a block whose weights sha256 is not B08's probe's, and a block whose "
            "`as_trained` world scores are not exactly B08's"),
        "interpretation_limit": INTERPRETATION_LIMIT,
    }
    result["J_by_rule"] = {
        name: across(complete, lambda b, name=name: b["J_by_rule"][name]) for name in RULES}
    result["b08_J_by_rule"] = {
        name: across(complete, lambda b, name=name: b["b08_J_by_rule"][name])
        for name in b08.RULES}
    for name in RULES:
        result[f"J_{name}_minus_as_trained"] = across(
            complete, lambda b, name=name: b["J_minus_as_trained"][name])
    for key in ("best_constant_minus_as_trained",
                f"best_constant_minus_b08_{REFERENCE_RULE}",
                "max_constant_minus_min_constant",
                f"{FROZEN_RULE}_minus_as_trained",
                f"{FROZEN_RULE}_minus_b08_{REFERENCE_RULE}",
                "oracle_envelope_minus_as_trained"):
        result[key] = across(complete, lambda b, key=key: b[key])
    result["best_constant_label_by_block"] = {
        str(block["training_seed"]): (block.get("best_constant") or {}).get("label")
        for block in blocks}
    result["constant_ranking_by_block"] = {
        str(block["training_seed"]): (block.get("best_constant") or {}).get("ranking")
        for block in blocks}
    result["as_trained_agent_label_histogram_by_block"] = {
        str(block["training_seed"]): block.get("as_trained_agent_label_histogram")
        for block in blocks}
    result["coordinator_most_used_label_by_block"] = {
        str(block["training_seed"]): block.get("coordinator_most_used_label")
        for block in blocks}
    result["one_best_constant_label_across_blocks"] = (
        complete[0]["best_constant"]["label"]
        if complete and len({block["best_constant"]["label"] for block in complete}) == 1
        else None)
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
    red.add_argument("--b08-probes", type=Path, nargs="+", required=True,
                     help="the B08 probe summaries of the same three checkpoints")
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
                           [load(path) for path in args.b08_probes])
    result["input_probes"] = [str(path) for path in args.probes]
    result["input_b08_probes"] = [str(path) for path in args.b08_probes]
    shared.write_json(args.output_root / "summary.json", result)
    print(json.dumps({
        "status": result["status"], "blocks_read": result["blocks_read"],
        "best_constant_label_by_block": result["best_constant_label_by_block"],
        "best_constant_minus_as_trained": (result["best_constant_minus_as_trained"] or {}).get(
            "mean"),
        "oracle_envelope_minus_as_trained": (result["oracle_envelope_minus_as_trained"] or {}).get(
            "mean"),
        "predictions": {name: entry["blocks_holding"] for name, entry in
                        result["predictions"].items() if isinstance(entry, dict)}}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
