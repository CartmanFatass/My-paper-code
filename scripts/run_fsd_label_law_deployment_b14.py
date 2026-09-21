"""FSD label law deployment B14: does the ten-step credit pay in its own regime? Zero fits.

Prospective entry in the direction notebook:
docs/research/candidates/flexible_skill_duration/NOTES.md, "2026-09-21 02:59 PDT - owner allows the
reopening probe; prospective B14 (zero fits): does the ten-step credit pay in its own regime?".

B13 deployed its estimate as *one constant label for everyone for a whole episode* and found no
gain.  The estimate it deployed was fitted on ten-step commitments under mixed teams, so the
strongest remaining alternative is that credit and deployment were misaligned, not that the credit
is worthless.  B14 is the one observation named at 02:51 as able to reverse the reserve
recommendation: on each of the six B13 final checkpoints, with the weights and the estimate frozen,
every agent's label is redrawn independently at every ten-step boundary from B13's own declared law
`q = .7 * softmax(z) + .3 * uniform`, against `uniform_every_10` on the same 32 worlds.

Zero fits: no optimizer step, no ValueNorm update, no buffer flush effect on weights.  Every
optimizer `step` of both agents raises for the whole command (B05's `_forbid_optimizer_steps`, the
guard B09/B10/B12 use), the weights file's sha256 is recomputed after the panels and compared, and
the probe refuses itself if any counter moved.

Two commands.

`probe --fit-root <b13 fit root>` takes one B13 fit root - `summary.json`, `weights.json`,
`final_weights.pt`, `bandit.jsonl` - and carries no admission: like the B09-B12 probes it is policy
execution at fixed weights, recorded as exposure, and it is run directly rather than through
`scripts/hmasd_launch.py`.  It

  (a) refuses a fit that is not a complete B13 fit of this object's arms and blocks (B13's own
      `fit_endpoint` reader), a weights file whose sha256 is not its sidecar's, and a sidecar that
      was written by another object, arm or block;
  (b) reads the fit's *own* final estimate - the last record of `bandit.jsonl` - and builds `q`
      with B13's own `label_law`, its constants untouched (`SOURCE_NOTES['estimate']`);
  (c) rebuilds the learner exactly as the fit did (the fit's own recorded configuration snapshots,
      including `disable_high_level_training = True`), loads `final_weights.pt` and runs the
      **faithful-load check**: `uniform_every_10` under the *fit's own* panel stream must reproduce
      the fit's recorded rollout-45 `uniform_every_10` panel by exact equality of the 32 native
      world scores - B08's convention, unrelaxed.  On a mismatch the probe writes a summary with
      status `failed_faithful_load`, the maximum absolute difference and no rule scores, and exits
      non-zero;
  (d) then runs the four declared panels on the same 32 worlds, mean actions, the frozen caps-10
      cadence: `uniform_every_10` and `law_every_10`, each under two fresh dedicated label streams
      (replicates `a`, `b`), so label-draw noise is measured and not read as an effect.

The rules are imposed exactly as B08 and B09 impose theirs, without touching `hmasd/`:
`DeploymentRule` extends `b09.MapExecutionRule` (so every foreign rule name keeps its own
behaviour), wraps the evaluator agent instance's `_batched_assign_skills` for the duration of one
panel through B08's `ExecutionRule.attached`, and writes the executed labels back into
`env_team_skills`/`env_agent_skills`.  This object's rule class, its rule definitions, its panel
stream constructor and its rule names are bound into B08's own module tables for the duration of
the four panels only and restored in a `finally`; the faithful-load panel runs *outside* that
binding, under `b09.bound_rules()` exactly as B13's own fan-out ran it.  No cap is moved: the
caps-10 cadence is the frozen one on every panel, so the decision boundaries of `law_every_10` are
the boundaries of `uniform_every_10` and only the label drawn at them differs.

`reduce --probes <six probe summaries>` is a pure reading of published summaries and carries no
admission.  Per checkpoint it takes `G = J(law_every_10) - J(uniform_every_10)` paired by world,
averaged over the two replicates, with the replicate difference and the two label-draw noise
differences beside it, and it groups the checkpoints by the fit's arm: the three `UNIFORM`
checkpoints are the primary group (Pro's test, equal label exposure during the fit), the three
`BANDIT` checkpoints the secondary one, never pooled.

Nothing here is a fit: these are deployment-time interventions on fixed weights and say nothing
about what training under this law would produce.
"""
import argparse
import hashlib
import json
import math
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
import run_fsd_label_bandit_b13 as b13
import run_fsd_label_content_b08 as b08
import run_fsd_label_map_b09 as b09

shared = b13.shared
DIRECTION = "flexible_skill_duration"
OBJECT_ID = "FSD_LABEL_LAW_DEPLOYMENT_B14"
CARD = ("docs/research/candidates/flexible_skill_duration/NOTES.md "
        "(2026-09-21 02:59 PDT, prospective B14)")
BLOCKS = dict(b13.BLOCKS)  # 772803, 772903, 773003
ARMS = tuple(sorted(b13.ARMS))  # BANDIT, UNIFORM: the arm of the *fit* whose checkpoint is probed
PRIMARY_ARM = b13.UNIFORM_ARM   # the entry's primary group: equal label exposure during the fit
SECONDARY_ARM = b13.BANDIT_ARM  # reported separately, never pooled with the primary
N_LABELS = b13.N_LABELS  # 6
REPLICATES = ("a", "b")
UNIFORM_RULE = b13.REFERENCE_RULE  # "uniform_every_10": B08's own rule, and the fit's own panel
LAW_RULE = "law_every_10"
BASE_RULES = (UNIFORM_RULE, LAW_RULE)
WEIGHTS_NAME = b13.WEIGHTS_NAME  # final_weights.pt
SIDECAR_NAME = b13.SIDECAR_NAME  # weights.json
RECORDS_NAME = "bandit.jsonl"    # B13's per-rollout estimator records
SUMMARY_NAME = "summary.json"
# the entry's declared sizes; none of them is a decision rule
GAIN_MARGIN = .03       # "mean G below .03"; "G >= .03 in the mean"
SHARE_TOLERANCE = .03   # the intermediate check: largest executed share within .03 of max q
REVERSAL_BLOCKS = 2     # "a positive paired gain on at least two blocks"
SHORTFALL_BLOCKS = 1    # "at most one block at or above .03"
REPLICATE_FACTOR = 2.   # "larger than twice the replicate difference"
PANEL_NOISE = b09.PANEL_NOISE  # .03 J conditional evaluation noise of a mean-action panel

GENERATOR_DERIVATION = (
    "numpy.random.default_rng([evaluation_seed, replicate_index, sha256(panel_rule_name)[:8]])")


def panel_rule(base, replicate):
    """The panel name that runs base rule `base` under label stream replicate `replicate`."""
    if base not in BASE_RULES or replicate not in REPLICATES:
        raise ValueError(f"unknown panel rule {base}_{replicate}")
    return f"{base}_{replicate}"


def rule_parts(name):
    """`(base rule, replicate)` of one of this object's four panels, or `(None, None)`."""
    for base in BASE_RULES:
        for replicate in REPLICATES:
            if name == f"{base}_{replicate}":
                return base, replicate
    return None, None


PANEL_RULES = tuple(panel_rule(base, replicate)
                    for replicate in REPLICATES for base in BASE_RULES)
LAW_PANELS = tuple(panel_rule(LAW_RULE, replicate) for replicate in REPLICATES)
UNIFORM_PANELS = tuple(panel_rule(UNIFORM_RULE, replicate) for replicate in REPLICATES)

# `CURRENT["law"]` is how the law reaches the rule: B08's `run_rule_panel` constructs the rule
# itself, exactly as B13's `CURRENT` carries a fit's state to its wrappers. `bound_rules` sets it
# and restores it in a `finally`.
CURRENT = {"law": None, "estimate": None}
_orig_label_generator = b08.label_generator

SOURCE_NOTES = {
    "estimate": (
        "the deployed law is built from the fit's *own* final estimate and nothing is re-fitted: "
        "the last record of the fit's `bandit.jsonl` (its rollout number must be the fit's last) "
        "carries `estimate.beta_hat`, `estimate.standard_error` and `estimate.z`, and this object "
        "uses **exactly the `z` the fit recorded**. As a check and not as a source it also "
        "recomputes `beta_hat / standard_error` with the fit's own formula "
        "(run_fsd_label_bandit_b13.py:583-584 `z = beta / standard_errors()`, whose denominator is "
        "the recorded `standard_error`) and refuses the probe unless the two agree exactly. The "
        "record is also required to be the same object as `summary['label_bandit_final']` and as "
        "the last `training_rows[-1]['label_bandit']`, so the three copies of the fit's final "
        "estimate agree before any panel runs"),
    "law": (
        "`q = .7 * softmax(z) + .3 * uniform` is B13's own declared law, computed by B13's own "
        "`run_fsd_label_bandit_b13.label_law(estimate, 'BANDIT')` with B13's constants "
        "(`EXPLOIT_WEIGHT`, `FLOOR_WEIGHT`, `SOFTMAX_TEMPERATURE`, `LABEL_FLOOR`), imported and "
        "not retyped, so the floating-point result is the fit's own to the last bit. Nothing is "
        "tuned and no alternative floor, temperature or law is computed. On a `BANDIT` fit it is "
        "*also* the law that fit executed, so its last record's `q_next` is compared with this "
        "one by exact list equality and a mismatch refuses the probe; on a `UNIFORM` fit the "
        "recorded `q_next` is uniform by construction (the estimator ran passively), so there is "
        "nothing to compare and `q_matches_recorded_q_next` is null with that reason"),
    "panel_streams": (
        "each of the four panels draws from its own dedicated generator, "
        + GENERATOR_DERIVATION + ", built once per panel by B08's own `run_rule_panel` through "
        "this object's `label_generator`, which is bound into B08's module for the duration of the "
        "four "
        "panels and restored in a `finally`; every other rule name is delegated to B08's own "
        "constructor unchanged. The four streams are distinct from each other (the panel rule name "
        "carries the replicate) and distinct from the fit's own panel stream, which is "
        "`numpy.random.default_rng([evaluation_seed, sha256('uniform_every_10')[:8]])` (a "
        "two-element seed sequence against this object's three-element one): the fit's stream is "
        "used by the faithful-load rerun alone and never by a scored panel. The draws come from "
        "those generators alone and touch no global NumPy, Python or torch stream"),
    "law_draws": (
        "at every step the rule draws one `[lanes]` team label and one `[lanes, agents]` agent "
        "label array and applies them only where the frozen `_d2_last_step` mask says a decision "
        "was taken (`sample_Z` for the team label, `sampled_mask` for the agent labels), which is "
        "exactly how B08's `uniform_every_10` draws (scripts/run_fsd_label_content_b08.py:1797-"
        "1801); between decisions the drawn labels are held. Under `uniform_every_10_{a,b}` the "
        "agent labels are `generator.integers(0, n_z)`, B08's own draw; under `law_every_10_{a,b}` "
        "they are `generator.choice(n_z, p=q)`, independently per (lane, agent). The *team* label "
        "is drawn uniformly under both rules: it never reaches the low-level actor "
        "(hmasd/networks.py:1801-1809, B09's `team_label_path`), and drawing it the same way under "
        "both rules keeps the agent-label law the only difference between them. Both interruption "
        "costs are infinite on this construction and no cap is moved, so the decision boundaries "
        "are the caps' own and are identical across the four panels; the probe records each "
        "panel's decision step indices and refuses if they are not"),
    "executed_shares": (
        "`agent_label_histogram` counts every executed (step, lane, agent) position of the panel "
        "and `decision_label_histogram` counts the positions at which a label was actually drawn. "
        "With one cadence and every agent redrawn at every decision the two shares are the same "
        "quantity up to the last partial commitment; the declared intermediate check reads the "
        "executed shares, and the decision shares are published beside them. The check is "
        "`|largest executed share - max q| <= " + f"{SHARE_TOLERANCE}" + "`: it asks whether the "
        "estimate really moved ten-step exposure, and it is recorded, never raised"),
    "faithful_load": (
        "the native world scores of `uniform_every_10`, rerun from the loaded weights under the "
        "*fit's own* panel stream through the frozen evaluator sync, compared with the fit's "
        "recorded rollout-45 `uniform_every_10` panel by exact list equality; this is B08's own "
        "check (scripts/run_fsd_label_map_b09.py:332-346) and it is not relaxed. Only the 32 "
        "native world scores enter it: no wall-clock, counter or exposure field is compared. The "
        "rerun runs under `b09.bound_rules()` and `b09.run_rule_panel`, which is how B13's own "
        "panel fan-out ran that panel (scripts/run_fsd_label_bandit_b13.py:1129-1134), and the "
        "panel is re-seeded from the block's evaluation seed inside the frozen `evaluate_panel` "
        "(scripts/run_fsd_baseline_interruption_b01.py:202-205), so it depends on the loaded "
        "weights and the block alone. A fixed-weight panel is bit-reproducible only on the host "
        "that trained the checkpoint, so this command runs on the fit host"),
    "construction": (
        "the probe rebuilds the learner and the evaluator through the frozen "
        "`run_fsd_baseline_interruption_b01.build_learner`/`build_evaluator` with B13's identities "
        "bound (`run_fsd_label_bandit_b13.bind()`), so the construction is B13's own, including "
        "its one declared configuration difference `disable_high_level_training = True`. The guard "
        "compares the probe's two configuration snapshots with the *fit's own recorded* "
        "`learner_config` and `evaluation_config` and refuses any difference the host geometry "
        "does not explain (`run_fsd_label_bandit_b13.allowed_differences`, empty on the production "
        "host). Comparing against the fit's own record rather than against the published D1280 "
        "summary is deliberate: the execution node's sparse checkout does not carry `runs/`, which "
        "is what failed the first B08/B09 probe attempts, and the fit root is an input here by "
        "construction. `disable_high_level_training` is not a snapshot field, so it is read "
        "directly off both configuration objects as well"),
    "no_optimizer_step": (
        "every optimizer `step` of both agents raises for the whole command "
        "(`run_fsd_flat_input_scale_b05._forbid_optimizer_steps`, the guard B09, B10 and B12 use), "
        "restored in a `finally`; the frozen per-network counters of the learner and the "
        "`evaluator_optimizer_calls` of every panel are summed afterwards and the probe refuses "
        "itself unless the total is zero. The evaluator is in eval mode for every panel "
        "(`Evaluator._sync` calls `agent.train(False)`, scripts/run_flexible_skill_duration_e0.py:"
        "319-335), the panel writes no rollout buffer (B10's `no_learner_state_written`), and the "
        "weights file's sha256 is recomputed after the panels and compared with the one read "
        "before them"),
    "paired_difference": (
        "the mean over the 32 evaluation worlds of the per-world difference of two panels of the "
        "same checkpoint, with the sample standard deviation of those 32 differences and "
        "`sd / sqrt(32)` beside it. The two panels run on the same weights, the same worlds and "
        "the same evaluation seeds, so the difference is paired by world; the standard error is "
        "the conditional one of that pairing and is not an interval over blocks, over label "
        "streams or over training seeds"),
    "grouping": (
        "the checkpoints are grouped by the arm of the fit that produced them and never pooled. "
        "`UNIFORM` is the primary group: those three fits gave the six labels equal exposure, so "
        "their estimate is the one the entry's test is about. `BANDIT` is the secondary group, "
        "where the same law was also the training law (matched training and deployment); the entry "
        "declares no prediction of sign for it. The two predictions are evaluated on the primary "
        "group alone"),
    "team_label_path": b09.SOURCE_NOTES["team_label_path"],
    "execution_rule_attachment": b09.SOURCE_NOTES["execution_rule_attachment"],
    "weight_transfer_to_evaluator": b09.SOURCE_NOTES["weight_transfer_to_evaluator"],
    "evaluation_route": b09.SOURCE_NOTES["evaluation_route"],
    "low_level_actor_label": b09.SOURCE_NOTES["low_level_actor_label"],
    "coordinator_off": b13.SOURCE_NOTES["disable_high_level_training"],
}

INTERPRETATION_LIMIT = (
    "a fixed-weight forward measurement, not a fit: zero fits, zero optimizer steps, four panels "
    "per checkpoint on the same 32 worlds and the same evaluation seeds. Three reused blocks, "
    "which have carried every setting in this direction since B01, so no size claim and no "
    "competence claim. Mean actions only: the panels execute the low level's mean action, as "
    "B13's own panels do, while training executes a sample, so nothing here says what training "
    "under this law would produce. The deployed estimate is each fit's own final one, frozen, on "
    "its own checkpoint - not a shared or held-out estimate - and the law is B13's declared "
    f"`q = .7 softmax(z) + .3 uniform` with its .3 floor, nothing tuned. A panel's conditional "
    f"evaluation noise on this direction is about {PANEL_NOISE} J, which is why every comparison "
    "here is paired by world and why the two label-stream replicates are reported. The `UNIFORM` "
    "and `BANDIT` checkpoints are separate groups and are never pooled. A fixed-weight panel is "
    "bit-reproducible only on the host that trained the checkpoint, so these panels run on "
    "wsl_4070.")


# ---------------------------------------------------------------------------
# the rules: B08's execution rule with this object's two ten-step deployment laws
# ---------------------------------------------------------------------------


def rule_definitions():
    """This object's four panel definitions; their cadence and write-back are B08's own."""
    definitions = {}
    for name in PANEL_RULES:
        base, replicate = rule_parts(name)
        if base == UNIFORM_RULE:
            law = ("every agent's label and the team label are drawn uniformly at random at each "
                   "ten-step decision, which is B08's own `uniform_every_10`")
        else:
            law = ("every agent's label is drawn independently from B13's declared law "
                   "`q = .7 * softmax(z) + .3 * uniform` at each ten-step decision, with `z` the "
                   "fit's own frozen final estimate; the team label is drawn uniformly, as under "
                   "`uniform_every_10`")
        definitions[name] = (
            f"{law}, on label-stream replicate {replicate}. Between decisions the drawn labels are "
            "held, exactly as the coordinator's argmax ones would be; the frozen caps-10 cadence "
            "is untouched, so the coordinator still decides at the same ticks and only its choice "
            "is discarded. " + SOURCE_NOTES["law_draws"] + ". " + SOURCE_NOTES["panel_streams"])
    return definitions


RULE_DEFINITIONS = rule_definitions()


def label_generator(evaluation_seed, rule):
    """This object's dedicated panel stream; every other rule name is B08's own generator."""
    base, replicate = rule_parts(rule)
    if base is None:
        return _orig_label_generator(evaluation_seed, rule)
    digest = hashlib.sha256(rule.encode("utf-8")).digest()[:8]
    return np.random.default_rng([int(evaluation_seed), int(REPLICATES.index(replicate)),
                                  int.from_bytes(digest, "big")])


def require_law(law, *, n_labels=N_LABELS):
    """The deployed law, checked against B13's own declared shape, sum and floor."""
    law = np.asarray(law, dtype=np.float64)
    if law.shape != (int(n_labels),):
        raise ValueError(f"the label law is not a vector over the {n_labels} agent labels")
    if not np.isfinite(law).all() or abs(float(law.sum()) - 1.) > 1e-12:
        raise ValueError(f"the label law does not sum to one: {law.tolist()}")
    if float(law.min()) < b13.LABEL_FLOOR - 1e-12:
        raise ValueError(f"the label law is below B13's declared floor: {law.tolist()}")
    return law


class DeploymentRule(b09.MapExecutionRule):
    """B08's execution rule with this object's four panels added; everything else is inherited.

    Attachment, the infinite-interruption-cost guard, the cap handling, the write-back, the
    histograms and the change fractions are B08's; B09's constant maps are inherited untouched.
    Only the choice of executed label is this object's, and only for the names in `PANEL_RULES`, so
    a foreign name (`as_trained`, `constant_c`, `uniform_every_10`) runs exactly as it always does.
    """

    def __init__(self, name, agent, *, generator=None, horizon=None):
        super().__init__(name, agent, generator=generator, horizon=horizon)
        self.base, self.replicate = rule_parts(name)
        self.law = None
        if self.base == LAW_RULE:
            self.law = require_law(CURRENT["law"], n_labels=self.n_z)
        self.decision_histogram = np.zeros(self.n_z, dtype=np.int64)
        self.decision_positions = 0
        self.decision_step_indices = []
        self.label_draws = 0

    # -- the rule -----------------------------------------------------------

    def _step(self, team, agents):
        if self.base is None:
            return super()._step(team, agents)  # B09's and B08's own rules, unchanged
        last = self.agent._d2_last_step
        reset = np.asarray(last["team_cause"], dtype=np.int64) == self.agent.D2_CAUSE_RESET
        sampled = np.asarray(last["sampled_mask"], dtype=bool)
        sample_team = np.asarray(last["sample_Z"], dtype=bool)
        team = np.asarray(team, dtype=np.int64).copy()
        agents = np.asarray(agents, dtype=np.int64).copy()
        lanes = int(team.shape[0])
        # One `[lanes]` and one `[lanes, agents]` draw per step, applied only where the frozen mask
        # says a decision was taken: B08's own draw pattern, so the stream position is a function
        # of the step count alone.
        drawn_team = self.generator.integers(0, self.n_Z, size=lanes)
        if self.law is None:
            drawn_agents = self.generator.integers(0, self.n_z, size=agents.shape)
        else:
            drawn_agents = self.generator.choice(self.n_z, size=agents.shape, p=self.law)
        self.label_draws += int(np.prod(agents.shape))
        team = np.where(sample_team, drawn_team, team)
        agents = np.where(sampled, drawn_agents, agents)
        for lane in range(lanes):  # the executed label is the label the agent holds
            self.agent.env_team_skills[lane] = int(team[lane])
            self.agent.env_agent_skills[lane] = agents[lane].copy()
        if sampled.any():
            self.decision_step_indices.append(int(self.steps))
            drawn = agents[sampled]
            self.decision_histogram += np.bincount(drawn.reshape(-1), minlength=self.n_z)
            self.decision_positions += int(sampled.sum())
        self._record(team, agents, reset)
        return team, agents

    # -- the record ---------------------------------------------------------

    def measures(self):
        record = super().measures()
        if self.base is None:
            return record
        executed = np.asarray(record["agent_label_histogram"], dtype=np.float64)
        decisions = self.decision_histogram.astype(np.float64)
        shares = (executed / executed.sum()).tolist() if executed.sum() else None
        decision_shares = (decisions / decisions.sum()).tolist() if decisions.sum() else None
        record.update({
            "panel_rule": self.name, "base_rule": self.base, "replicate": self.replicate,
            "n_agents": self.n_agents, "n_labels": self.n_z,
            "law": None if self.law is None else self.law.tolist(),
            "law_source": "uniform" if self.law is None else "b13_softmax_z",
            "max_q": None if self.law is None else float(self.law.max()),
            "argmax_q": None if self.law is None else int(np.argmax(self.law)),
            "executed_label_shares": shares,
            "largest_executed_share": None if shares is None else float(max(shares)),
            "most_executed_label": (None if shares is None
                                    else int(np.argmax(np.asarray(shares)))),
            "decision_label_histogram": self.decision_histogram.tolist(),
            "decision_label_shares": decision_shares,
            "decision_positions": int(self.decision_positions),
            "decision_step_indices": list(self.decision_step_indices),
            "decision_steps_recorded": len(self.decision_step_indices),
            "label_draws": int(self.label_draws),
            "definitions_b14": {"law_draws": SOURCE_NOTES["law_draws"],
                                "executed_shares": SOURCE_NOTES["executed_shares"],
                                "panel_streams": SOURCE_NOTES["panel_streams"]}})
        return record


@contextmanager
def bound_rules(law):
    """Bind this object's four panels into B08's tables for one run; restore them on the way out.

    The direction's established bind-and-restore (B09's `bound_rules` is the template): B08's
    `run_rule_panel` reads `ExecutionRule`, `RANDOM_RULES` and `label_generator` and B08's
    `ExecutionRule` reads `RULE_DEFINITIONS`, all as module globals, so this object's rules are
    added there rather than by copying the panel routine. `RULES`, `RULE_CAPS` and `BASELINE_RULE`
    are not touched at all: no cap moves here. Everything, including `CURRENT["law"]`, is put back
    in the `finally`, so a later reader, reduce or command in the same process sees B08's own
    tables.
    """
    definitions = dict(b08.RULE_DEFINITIONS)
    random_rules, rule_class = b08.RANDOM_RULES, b08.ExecutionRule
    generator, current = b08.label_generator, dict(CURRENT)
    b08.RULE_DEFINITIONS.update(RULE_DEFINITIONS)
    b08.RANDOM_RULES = tuple(random_rules) + PANEL_RULES  # so the panel builds its generator
    b08.ExecutionRule = DeploymentRule
    b08.label_generator = label_generator
    CURRENT["law"] = None if law is None else require_law(law).tolist()
    try:
        yield
    finally:
        b08.ExecutionRule = rule_class
        b08.RANDOM_RULES = random_rules
        b08.label_generator = generator
        b08.RULE_DEFINITIONS.clear()
        b08.RULE_DEFINITIONS.update(definitions)
        CURRENT.clear()
        CURRENT.update(current)


def check_rule_record(name, record):
    """The run-time proof that a panel executed the rule it declares; raises where it did not."""
    base, replicate = rule_parts(name)
    if base is None:
        return record
    if record.get("rule") != name or record.get("panel_rule") != name:
        raise ValueError(f"the {name} panel does not record its own rule name")
    histogram = [int(value) for value in record.get("agent_label_histogram") or []]
    positions = int(record["steps_recorded"]) * int(record["lanes"]) * int(record["n_agents"])
    if sum(histogram) != positions:
        raise ValueError(
            f"the {name} panel's executed histogram covers {sum(histogram)} positions, not the "
            f"{positions} of the panel")
    if not record.get("decision_step_indices"):
        raise ValueError(f"the {name} panel took no decision, so no label was ever drawn")
    changes = record.get("agent_label_change_fraction")
    if not changes:
        raise ValueError(
            f"the {name} panel never changed an executed agent label, so it redrew nothing")
    if base == LAW_RULE and not record.get("law"):
        raise ValueError(f"the {name} panel carries no record of the law it deployed")
    return record


def run_rule_panel(name, learner, evaluator, summary, out, index, *, evaluation_seed):
    """One panel: B08's own rule panel, with this object's stream record and run-time check."""
    record = b08.run_rule_panel(name, learner, evaluator, summary, out, index,
                                evaluation_seed=evaluation_seed)
    base, replicate = rule_parts(name)
    record["random_labels"] = {
        "generator": GENERATOR_DERIVATION, "evaluation_seed": int(evaluation_seed),
        "rule": name, "base_rule": base, "replicate": replicate,
        "replicate_index": None if replicate is None else int(REPLICATES.index(replicate)),
        "note": SOURCE_NOTES["panel_streams"]}
    return check_rule_record(name, record)


def share_check(record):
    """The entry's intermediate check on one `law_every_10` panel; recorded, never raised."""
    shares = record.get("executed_label_shares")
    law = record.get("law")
    if not shares or not law:
        return None
    largest = float(max(shares))
    maximum = float(max(law))
    return {
        "largest_executed_share": largest,
        "most_executed_label": int(np.argmax(np.asarray(shares, dtype=np.float64))),
        "max_q": maximum, "argmax_q": int(np.argmax(np.asarray(law, dtype=np.float64))),
        "difference": largest - maximum,
        "tolerance": SHARE_TOLERANCE,
        "within_tolerance": bool(abs(largest - maximum) <= SHARE_TOLERANCE),
        "most_executed_label_is_argmax_q": bool(
            int(np.argmax(np.asarray(shares, dtype=np.float64)))
            == int(np.argmax(np.asarray(law, dtype=np.float64)))),
        "executed_label_shares": [float(value) for value in shares],
        "q": [float(value) for value in law],
        "definition": SOURCE_NOTES["executed_shares"]}


# ---------------------------------------------------------------------------
# the fit this probe reads
# ---------------------------------------------------------------------------


class FaithfulLoadFailure(RuntimeError):
    """The loaded weights did not reproduce the fit's own panel: a technical failure, no score."""


def reference_boundary():
    """The fit's last boundary; read from B13 at call time so a tiny test host can shrink it."""
    return int(b13.ROLLOUTS)


def fit_reference_panel(summary):
    """The fit's own recorded last-boundary `uniform_every_10` panel, and the frozen record of it.

    The fan-out keeps the schedule slot in `summary['panels']` and moves every other panel of the
    boundary into `summary['extra_panels']` in the order it ran
    (scripts/run_fsd_label_bandit_b13.py:1136-1150), so the two records of the same panel can be
    matched by that order and compared; the check is that this object identified the right panel.
    """
    boundary = reference_boundary()
    at_boundary = [entry for entry in summary.get("panel_runs") or []
                   if int(entry["panel_rollouts"]) == boundary]
    entries = [entry for entry in at_boundary if entry["rule"] == UNIFORM_RULE]
    if len(entries) != 1:
        raise ValueError(
            f"the fit does not carry exactly one {UNIFORM_RULE} panel at rollout {boundary}")
    entry = entries[0]
    extras = [panel for panel in summary.get("extra_panels") or []
              if int(panel["panel_rollouts"]) == boundary]
    others = [other for other in at_boundary if not other["schedule_slot"]]
    if len(extras) != len(others):
        raise ValueError(
            f"the fit's rollout-{boundary} fan-out records {len(others)} non-schedule panels and "
            f"{len(extras)} frozen panel records")
    frozen = [panel for panel, other in zip(extras, others) if other is entry]
    if len(frozen) != 1:
        raise ValueError(f"the fit's {UNIFORM_RULE} panel has no frozen panel record beside it")
    if list(frozen[0]["native_scores_J"]) != list(entry["J_world_scores"]):
        raise ValueError(
            f"the fit's two records of its {UNIFORM_RULE} panel do not carry the same world scores")
    return entry, frozen[0]


def fit_estimate(summary, records):
    """The fit's own frozen final estimate, and the law B13's own `label_law` builds from it."""
    boundary = reference_boundary()
    last = records[-1]
    if int(last["rollout"]) != boundary:
        raise ValueError(
            f"the fit's last estimator record is rollout {last['rollout']}, not {boundary}")
    estimate = last["estimate"]
    beta = np.asarray(estimate["beta_hat"], dtype=np.float64)
    errors = np.asarray(estimate["standard_error"], dtype=np.float64)
    z = np.asarray(estimate["z"], dtype=np.float64)
    if beta.shape != (N_LABELS,) or errors.shape != z.shape != beta.shape:
        raise ValueError("the fit's final estimate is not a vector over the six agent labels")
    if not np.array_equal(beta / errors, z):
        raise ValueError(
            "the fit's recorded z is not `beta_hat / standard_error` under its own formula")
    final = summary.get("label_bandit_final") or {}
    if (list(final.get("z") or []) != list(estimate["z"])
            or list(final.get("beta_hat") or []) != list(estimate["beta_hat"])):
        raise ValueError("the fit's final state and its last estimator record disagree")
    rows = summary.get("training_rows") or []
    if (rows[-1].get("label_bandit") or {}).get("estimate", {}).get("z") != list(estimate["z"]):
        raise ValueError("the fit's last training row and its `bandit.jsonl` record disagree")

    frozen = FrozenEstimate(z)
    law, source = b13.label_law(frozen, b13.BANDIT_ARM)
    law = require_law(law)
    recorded = list(last.get("q_next") or [])
    if last.get("q_next_source") == "softmax_z":
        matches = law.tolist() == recorded
        if not matches:
            raise ValueError(
                "this object's law is not the law the fit itself executed at its last rollout")
    else:
        matches = None  # a UNIFORM fit's recorded `q_next` is uniform; there is nothing to compare
    return {
        "rollout": int(last["rollout"]),
        "beta_hat": beta.tolist(), "standard_error": errors.tolist(), "z": z.tolist(),
        "z_source": "exactly the `z` the fit recorded",
        "z_recomputed_from_beta_and_standard_error_matches": True,
        "argmax_beta_hat": int(estimate["argmax_beta_hat"]),
        "estimate_available": bool(estimate["estimate_available"]),
        "rollouts_used": int(estimate["rollouts_used"]),
        "q": law.tolist(), "q_source": source,
        "max_q": float(law.max()), "argmax_q": int(np.argmax(law)),
        "label_floor": b13.LABEL_FLOOR,
        "exploit_weight": b13.EXPLOIT_WEIGHT, "floor_weight": b13.FLOOR_WEIGHT,
        "softmax_temperature": b13.SOFTMAX_TEMPERATURE,
        "recorded_q_next": recorded, "recorded_q_next_source": last.get("q_next_source"),
        "q_matches_recorded_q_next": matches,
        "q_comparison_note": (
            "the fit executed this law itself, so the comparison is exact list equality"
            if matches is not None else
            "the fit's own law was uniform (its estimator ran passively), so its recorded `q_next` "
            "is not this law and nothing is compared"),
        "definition": SOURCE_NOTES["estimate"], "law_definition": SOURCE_NOTES["law"]}


class FrozenEstimate:
    """The fit's final `z`, frozen: `available` and `z()` are all `b13.label_law` reads."""

    def __init__(self, z):
        self._z = np.asarray(z, dtype=np.float64)
        self.available = True

    def z(self):
        return self._z.copy()


def verify_sidecar(sidecar, summary):
    """The weights sidecar must be the one this fit wrote, for this object, arm and block."""
    expected = {"object_id": b13.OBJECT_ID, "file": WEIGHTS_NAME,
                "block_seed": int(summary["block_seed"]),
                "training_seed": int(summary["training_seed"]),
                "evaluation_seed": int(summary["evaluation_seed"]),
                "arm": summary["label_bandit_arm"], "rollouts": int(summary["rollouts"]),
                "launch_sha": summary.get("launch_sha")}
    wrong = {key: sidecar.get(key) for key, value in expected.items() if sidecar.get(key) != value}
    if wrong:
        raise ValueError(f"the weights sidecar is not this fit's: {sorted(wrong)}")
    recorded = (summary.get("final_weights") or {}).get("sha256")
    if recorded is not None and recorded != sidecar.get("sha256"):
        raise ValueError("the fit's summary and its weights sidecar record different sha256")
    return expected


def read_fit(fit_root):
    """One B13 fit root, validated by B13's own reader; the inputs of one checkpoint's probe."""
    fit_root = Path(fit_root)
    summary_path = fit_root / SUMMARY_NAME
    records_path = fit_root / RECORDS_NAME
    weights = fit_root / WEIGHTS_NAME
    for path in (summary_path, records_path, weights):
        if not path.exists():
            raise ValueError(f"{path} does not exist; the fit root is not a complete B13 fit")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("object_id") != b13.OBJECT_ID or summary.get(
            "label_bandit_object") != b13.OBJECT_ID:
        raise ValueError(f"{summary_path} is not a fit of {b13.OBJECT_ID}")
    if summary.get("status") != "complete":
        raise ValueError(f"the fit is {summary.get('status')}, not complete")
    arm, seed = summary.get("label_bandit_arm"), int(summary.get("block_seed", -1))
    if arm not in b13.ARMS or seed not in BLOCKS:
        raise ValueError("the fit is not one of B13's six planned fits")
    if int(summary.get("evaluation_seed", -1)) != BLOCKS[seed]:
        raise ValueError("the fit does not carry this block's evaluation seed")
    # B13's own reader: exposure, panels, its declared refusals, zero coordinator optimizer steps
    b13.fit_endpoint(summary)
    records = [json.loads(line) for line in
               records_path.read_text(encoding="utf-8").strip().splitlines() if line.strip()]
    rows = b13.bandit_rows(summary)
    if [record["rollout"] for record in records] != [row["rollout"] for row in rows]:
        raise ValueError("the fit's `bandit.jsonl` and its training rows are not the same records")
    # the sha256 is recomputed from the file and compared with the sidecar's, and the block checked
    weights_record = b09.verify_weights(seed, weights)
    verify_sidecar(weights_record["sidecar_record"], summary)
    entry, frozen = fit_reference_panel(summary)
    return {
        "root": fit_root, "summary": summary, "weights": weights,
        "weights_record": weights_record, "records": records,
        "arm": arm, "block_seed": seed, "evaluation_seed": int(summary["evaluation_seed"]),
        "launch_sha": summary.get("launch_sha"),
        "reference_panel": entry, "reference_frozen_panel": frozen,
        "estimate": fit_estimate(summary, records)}


def require_fit_construction(config, recorded_config, phase, arm):
    """Refuse a difference from the *fit's own* recorded construction the host does not explain."""
    differences = b13.config_differences(config, recorded_config)
    unexpected = {key: value for key, value in differences.items()
                  if key not in b13.allowed_differences(arm)}
    if unexpected:
        raise ValueError(
            f"the probe's {phase} is not the fit's own construction: {sorted(unexpected)}")
    return differences


def faithful_load_record(record, reference):
    """B08's faithful-load check, unrelaxed: exact list equality of the 32 native world scores."""
    mine = [float(value) for value in record["J_world_scores"]]
    theirs = [float(value) for value in reference["J_world_scores"]]
    faithful = bool(len(mine) == len(theirs) and mine == theirs)
    first = next((index for index, (a, b) in enumerate(zip(mine, theirs)) if a != b), None)
    maximum = (float(np.max(np.abs(np.asarray(mine) - np.asarray(theirs))))
               if len(mine) == len(theirs) and mine else None)
    return {
        "faithful_load": faithful,
        "first_differing_world": None if faithful else first,
        "max_abs_difference": maximum,
        "worlds": len(mine), "reference_worlds": len(theirs),
        "reference_panel_rollouts": int(reference["panel_rollouts"]),
        "reference_rule": UNIFORM_RULE,
        "rerun_J_mean": float(record["J_mean"]) if faithful else None,
        "rerun_decision_steps": record.get("decision_steps"),
        "definition": SOURCE_NOTES["faithful_load"],
        "weight_transfer": SOURCE_NOTES["weight_transfer_to_evaluator"]}


# ---------------------------------------------------------------------------
# the probe
# ---------------------------------------------------------------------------


def run_probe(fit_root, out, launch_sha=None):
    """One checkpoint: B13's construction and saved weights, five panels, no update."""
    b13.bind()  # identities only: the frozen runner's construction, this object's panels
    started = time.perf_counter()
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "object_id": OBJECT_ID, "card": CARD, "command": "probe",
        "launch_sha": shared.e0._git("rev-parse", "HEAD"), "requested_launch_sha": launch_sha,
        "fit_root": str(fit_root), "fit_object_id": b13.OBJECT_ID,
        "rules": list(PANEL_RULES), "base_rules": list(BASE_RULES),
        "replicates": list(REPLICATES), "labels": N_LABELS,
        "faithful_load_rule": UNIFORM_RULE,
        "construction_source": (
            f"{b13.OBJECT_ID} (the recorded stage-1 D1280 construction with B13's one declared "
            "difference `disable_high_level_training = True`): the frozen baseline x interruption "
            "B01 runner with B13's identities bound, that fit's own saved final weights loaded, "
            "zero optimizer steps; this object adds execution rules only"),
        "reference_object_ids": [b13.OBJECT_ID, b09.OBJECT_ID, b08.OBJECT_ID],
        "host_geometry": b13.host_geometry(),
        "frozen_host_geometry": b13.host_geometry() == b13.probe.FROZEN_GEOMETRY,
        "source_notes": dict(SOURCE_NOTES),
        "status": "incomplete", "failure": None, "faithful_load": None,
        "rules_measured": None, "J_by_rule": None}
    construction = out / "construction"
    try:
        _run(result, Path(fit_root), construction)
        result["status"] = "complete"
    except FaithfulLoadFailure as exc:
        # A technical failure of the load, never a score: no rule panel ran and none is recorded.
        result["status"], result["failure"] = "failed_faithful_load", str(exc)
        result["rules_measured"], result["J_by_rule"] = None, None
    except Exception as exc:  # the partial facts stay recorded
        result["status"], result["failure"] = "incomplete", f"{type(exc).__name__}: {exc}"
    finally:
        result["wall_seconds"] = time.perf_counter() - started
        result["interpretation_limit"] = INTERPRETATION_LIMIT
        shared.write_json(out / SUMMARY_NAME, result)
    print(json.dumps({
        "status": result["status"], "failure": result["failure"],
        "block_seed": result.get("block_seed"), "checkpoint_arm": result.get("checkpoint_arm"),
        "faithful_load": (result.get("faithful_load") or {}).get("faithful_load"),
        "max_abs_difference": (result.get("faithful_load") or {}).get("max_abs_difference"),
        "J_by_rule": result.get("J_by_rule"),
        "largest_executed_share": {name: (result.get("share_checks") or {}).get(name, {}).get(
            "largest_executed_share") for name in LAW_PANELS},
        "optimizer_steps": result.get("optimizer_steps"),
        "weights_unchanged": result.get("weights_unchanged"),
        "wall_seconds": result.get("wall_seconds")}))
    return 0 if result["status"] == "complete" else 1


def _run(result, fit_root, out):
    """Read the fit, rebuild it, check the load, then run the four panels. No update, no fit."""
    fit = read_fit(fit_root)
    arm, seed, evaluation_seed = fit["arm"], fit["block_seed"], fit["evaluation_seed"]
    result.update({
        "checkpoint_arm": arm, "block_seed": seed, "evaluation_seed": evaluation_seed,
        "primary_group": bool(arm == PRIMARY_ARM),
        "weights": str(fit["weights"]), "weights_record": fit["weights_record"],
        "fit": {"object_id": fit["summary"].get("object_id"),
                "card": fit["summary"].get("card"),
                "launch_sha": fit["launch_sha"], "status": fit["summary"].get("status"),
                "arm": arm, "block_seed": seed, "evaluation_seed": evaluation_seed,
                "rollouts": int(fit["summary"]["rollouts"]),
                "summary": str(fit["root"] / SUMMARY_NAME),
                "records": str(fit["root"] / RECORDS_NAME),
                "declared_config_difference": fit["summary"].get("declared_config_difference"),
                "optimizer_calls": fit["summary"].get("optimizer_calls"),
                "final_weights_sha256": (fit["summary"].get("final_weights") or {}).get("sha256")},
        "estimate": fit["estimate"], "q": fit["estimate"]["q"],
        "reference_panel": {
            "rule": UNIFORM_RULE, "panel_rollouts": int(fit["reference_panel"]["panel_rollouts"]),
            "J_mean": float(fit["reference_panel"]["J_mean"]),
            "worlds": len(fit["reference_panel"]["J_world_scores"])},
        "rule_definitions": dict(RULE_DEFINITIONS)})

    summary = shared.base_summary(b13.ARMS[arm][0], training_seed=seed,
                                  evaluation_seed=evaluation_seed, object_id=OBJECT_ID,
                                  card=CARD, caps=None)
    summary.update(command="probe", factorial_arm=arm, block_seed=seed, rollouts=0,
                   panel_rollouts=[], panels=[],
                   coordinator_batch_size=b13.ARMS[arm][1], ordinary_wall_plan_seconds=None,
                   cost_law="zero optimizer steps; one evaluation panel per declared rule")
    out.mkdir(parents=True, exist_ok=True)
    envs, learner, _theta0, counters = b01.build_learner(arm, summary, out, seed)
    learner_differences = require_fit_construction(
        summary["learner_config"], fit["summary"]["learner_config"], "learner configuration", arm)
    restore = b08.scale._forbid_optimizer_steps(learner)
    try:
        learner.load_model(str(fit["weights"]))  # the agent's own load routine
        learner.train(False)
        evaluator = b01.build_evaluator(arm, summary, out, evaluation_seed)
        evaluation_differences = require_fit_construction(
            summary["evaluation_config"], fit["summary"]["evaluation_config"],
            "evaluation configuration", arm)
        restore += b08.scale._forbid_optimizer_steps(evaluator.agent)
        for name, agent in (("learner", learner), ("evaluator", evaluator.agent)):
            config = agent.config
            if (int(config.n_z), int(config.n_Z)) != (N_LABELS, N_LABELS):
                raise ValueError(
                    f"the {name} carries n_z={int(config.n_z)}, n_Z={int(config.n_Z)}, not the "
                    f"{N_LABELS} labels this object's law is defined on")
            if getattr(config, b13.DECLARED_FIELD, None) is not True:
                raise ValueError(
                    f"the {name} does not carry B13's declared {b13.DECLARED_FIELD}")
        result["declared_config_difference"] = {
            "field": b13.DECLARED_FIELD, "probe": True,
            "fit": (fit["summary"].get("declared_config_difference") or {}).get("fit"),
            "in_config_snapshot": b13.DECLARED_FIELD in summary["learner_config"],
            "definition": SOURCE_NOTES["construction"],
            "effects": SOURCE_NOTES["coordinator_off"]}

        # (c) the faithful load: the fit's own panel, its own stream, its own worlds
        with b09.bound_rules():
            rerun = b09.run_rule_panel(UNIFORM_RULE, learner, evaluator, summary, out,
                                       reference_boundary(), evaluation_seed=evaluation_seed)
        faithful = faithful_load_record(rerun, fit["reference_panel"])
        result["faithful_load"] = faithful
        if not faithful["faithful_load"]:
            raise FaithfulLoadFailure(
                "the loaded weights do not reproduce the fit's own "
                f"{UNIFORM_RULE} panel at rollout {faithful['reference_panel_rollouts']}; first "
                f"differing world index {faithful['first_differing_world']}, max |difference| "
                f"{faithful['max_abs_difference']}")

        # (d) the four declared panels, on the same worlds and the same evaluation seeds
        measured = {}
        with bound_rules(fit["estimate"]["q"]):
            for index, name in enumerate(PANEL_RULES):
                measured[name] = run_rule_panel(name, learner, evaluator, summary, out, index,
                                                evaluation_seed=evaluation_seed)
                result["rules_measured"] = dict(measured)
    finally:
        for optimizer, original in restore:
            optimizer.step = original

    learner_calls = shared.optimizer_counts(counters)
    steps = sum(learner_calls.values()) + sum(
        sum(panel["evaluator_optimizer_calls"].values()) for panel in summary["panels"])
    if steps != 0:
        raise ValueError("the probe is defined by taking no optimizer step")
    digest_after = b08.file_sha256(fit["weights"])
    if digest_after != fit["weights_record"]["sha256"]:
        raise ValueError("the weights file changed while the probe ran")
    boundaries = {name: list(measured[name]["decision_step_indices"]) for name in PANEL_RULES}
    distinct = {tuple(value) for value in boundaries.values()}
    if len(distinct) != 1:
        raise ValueError(
            "the four panels did not take their decisions at the same steps, so the rules do not "
            "share the frozen cadence")
    j_by_rule = {name: float(measured[name]["J_mean"]) for name in PANEL_RULES}
    result.update({
        "optimizer_steps": steps, "optimizer_calls": learner_calls,
        "weights_sha256_before": fit["weights_record"]["sha256"],
        "weights_sha256_after": digest_after,
        "weights_unchanged": bool(digest_after == fit["weights_record"]["sha256"]),
        "rules_measured": measured,
        "J_by_rule": j_by_rule,
        "J_world_scores": {name: [float(value) for value in measured[name]["J_world_scores"]]
                           for name in PANEL_RULES},
        "share_checks": {name: share_check(measured[name]) for name in LAW_PANELS},
        "executed_label_shares": {name: measured[name]["executed_label_shares"]
                                  for name in PANEL_RULES},
        "decision_label_shares": {name: measured[name]["decision_label_shares"]
                                  for name in PANEL_RULES},
        "agent_label_histogram": {name: measured[name]["agent_label_histogram"]
                                  for name in PANEL_RULES},
        "decision_steps": {name: int(measured[name]["decision_steps"]) for name in PANEL_RULES},
        "decision_positions": {name: int(measured[name]["decision_positions"])
                               for name in PANEL_RULES},
        "decision_boundaries_identical": True,
        "decision_boundary_count": len(next(iter(distinct))),
        "evaluator_optimizer_calls": {name: measured[name]["evaluator_optimizer_calls"]
                                      for name in PANEL_RULES},
        "evaluation_panels": len(summary["panels"]),
        "evaluation_episodes": summary["counts"]["evaluation_episodes"],
        "evaluation_steps": summary["counts"]["evaluation_steps"],
        "evaluation_lanes": shared.EVAL_LANES, "horizon": shared.HORIZON,
        "evaluation_deterministic": True,
        "training_lanes_constructed": len(envs),
        "training_lane_seeds": summary["training_lane_seeds"],
        "evaluation_lane_seeds": summary["evaluation_lane_seeds"],
        "construction_summary": f"construction/{SUMMARY_NAME}",
        "learner_config": summary["learner_config"],
        "evaluation_config": summary["evaluation_config"],
        "learner_config_differences_from_the_fit": learner_differences,
        "evaluation_config_differences_from_the_fit": evaluation_differences,
        "coordinator_training_mode": bool(evaluator.agent.skill_coordinator.training)})
    return result


# ---------------------------------------------------------------------------
# reduce
# ---------------------------------------------------------------------------


def paired_difference(first, second):
    """The per-world difference of two panels of one checkpoint: mean, sd and its paired se."""
    a = np.asarray(first, dtype=np.float64)
    b = np.asarray(second, dtype=np.float64)
    if a.ndim != 1 or a.shape != b.shape or not a.size:
        raise ValueError("a paired difference needs two equal-length vectors of world scores")
    difference = a - b
    worlds = int(difference.size)
    sd = float(np.std(difference, ddof=1)) if worlds > 1 else None
    return {
        "mean": float(difference.mean()), "worlds": worlds, "sample_sd": sd,
        "paired_se": (sd / math.sqrt(worlds)) if sd is not None else None,
        "positive_worlds": int((difference > 0.).sum()),
        "negative_worlds": int((difference < 0.).sum()),
        "per_world": difference.tolist(),
        "definition": SOURCE_NOTES["paired_difference"]}


def probe_row(summary):
    """Validated readings of one complete probe of this object."""
    if summary.get("object_id") != OBJECT_ID or summary.get("command") != "probe":
        raise ValueError("not a probe of this object")
    if summary.get("status") != "complete":
        raise ValueError(f"incomplete probe: status {summary.get('status')}")
    seed = int(summary.get("block_seed", -1))
    arm = summary.get("checkpoint_arm")
    if seed not in BLOCKS or arm not in b13.ARMS:
        raise ValueError("not one of this object's six checkpoints")
    if int(summary.get("evaluation_seed", -1)) != BLOCKS[seed]:
        raise ValueError("the probe does not carry this block's evaluation seed")
    if not (summary.get("faithful_load") or {}).get("faithful_load"):
        raise ValueError("the probe did not establish a faithful load")
    if summary.get("optimizer_steps") != 0:
        raise ValueError("the probe took an optimizer step")
    if not summary.get("weights_unchanged"):
        raise ValueError("the probe did not establish that the weights are unchanged")
    if not summary.get("decision_boundaries_identical"):
        raise ValueError("the probe's panels did not share the frozen decision cadence")
    measured = summary.get("rules_measured") or {}
    if sorted(measured) != sorted(PANEL_RULES):
        raise ValueError("the probe does not carry all four declared panels")
    scores = {name: [float(value) for value in measured[name]["J_world_scores"]]
              for name in PANEL_RULES}
    widths = {len(value) for value in scores.values()}
    if len(widths) != 1:
        raise ValueError("the probe's panels do not all carry the same worlds")
    law = list(summary.get("q") or [])
    if len(law) != N_LABELS:
        raise ValueError("the probe carries no record of the law it deployed")
    return {
        "block_seed": seed, "checkpoint_arm": arm,
        "launch_sha": summary.get("launch_sha"),
        "fit_launch_sha": (summary.get("fit") or {}).get("launch_sha"),
        "weights_sha256": (summary.get("weights_record") or {}).get("sha256"),
        "faithful_load": True, "worlds": next(iter(widths)),
        "J_by_rule": {name: float(measured[name]["J_mean"]) for name in PANEL_RULES},
        "J_world_scores": scores,
        "q": law, "max_q": float(max(law)), "argmax_q": int(np.argmax(np.asarray(law))),
        "estimate": summary.get("estimate"),
        "share_checks": dict(summary.get("share_checks") or {}),
        "executed_label_shares": dict(summary.get("executed_label_shares") or {}),
        "decision_steps": dict(summary.get("decision_steps") or {}),
        "wall_seconds": summary.get("wall_seconds")}


def checkpoint_reading(row):
    """One checkpoint: the paired gain per replicate, their mean, and the label-draw noise."""
    scores = row["J_world_scores"]
    gains = {replicate: paired_difference(scores[panel_rule(LAW_RULE, replicate)],
                                          scores[panel_rule(UNIFORM_RULE, replicate)])
             for replicate in REPLICATES}
    means = [gains[replicate]["mean"] for replicate in REPLICATES]
    gain = float(np.mean(means))
    replicate_difference = abs(means[0] - means[1])
    uniform_noise = paired_difference(scores[panel_rule(UNIFORM_RULE, REPLICATES[0])],
                                      scores[panel_rule(UNIFORM_RULE, REPLICATES[1])])
    law_noise = paired_difference(scores[panel_rule(LAW_RULE, REPLICATES[0])],
                                  scores[panel_rule(LAW_RULE, REPLICATES[1])])
    checks = {name: (row["share_checks"].get(name) or {}).get("within_tolerance")
              for name in LAW_PANELS}
    return {
        "block_seed": row["block_seed"], "checkpoint_arm": row["checkpoint_arm"],
        "J_by_rule": dict(row["J_by_rule"]),
        "G_by_replicate": {replicate: gains[replicate]["mean"] for replicate in REPLICATES},
        "G_paired_by_replicate": {replicate: gains[replicate] for replicate in REPLICATES},
        "G": gain,
        "G_definition": (
            f"`J({LAW_RULE}) - J({UNIFORM_RULE})` paired by world on this checkpoint, averaged "
            "over the two label-stream replicates; the per-replicate entries carry the mean of the "
            "32 per-world differences and its paired standard error"),
        "replicate_difference": replicate_difference,
        "replicate_difference_definition": (
            "|G_a - G_b|: how much the gain moved when only the label stream changed"),
        f"{UNIFORM_RULE}_a_minus_b": uniform_noise,
        f"{LAW_RULE}_a_minus_b": law_noise,
        "label_draw_noise_definition": (
            "the same rule under its two label streams, paired by world: the size of a difference "
            "this measurement cannot distinguish from the label draw"),
        "G_exceeds_twice_the_replicate_difference": bool(
            gain > REPLICATE_FACTOR * replicate_difference),
        "G_positive": bool(gain > 0.),
        "G_at_or_above_the_margin": bool(gain >= GAIN_MARGIN),
        "share_check_by_panel": checks,
        "share_checks": dict(row["share_checks"]),
        "share_check_holds": bool(all(value is True for value in checks.values())),
        "max_q": row["max_q"], "argmax_q": row["argmax_q"], "q": list(row["q"]),
        "weights_sha256": row["weights_sha256"], "fit_launch_sha": row["fit_launch_sha"],
        "worlds": row["worlds"], "wall_seconds": row["wall_seconds"]}


def group_reading(readings, arm):
    """One arm's checkpoints, described together; the two groups are never pooled."""
    values = [reading for reading in readings if reading["checkpoint_arm"] == arm]
    across = b08._across
    gains = [reading["G"] for reading in values]
    return {
        "arm": arm, "role": "primary" if arm == PRIMARY_ARM else "secondary",
        "checkpoints_read": len(values),
        "checkpoints_planned": len(BLOCKS),
        "blocks": [reading["block_seed"] for reading in values],
        "G_by_block": {str(reading["block_seed"]): reading["G"] for reading in values},
        "G": across(values, lambda reading: reading["G"]),
        "mean_G": float(np.mean(gains)) if gains else None,
        "G_a": across(values, lambda reading: reading["G_by_replicate"][REPLICATES[0]]),
        "G_b": across(values, lambda reading: reading["G_by_replicate"][REPLICATES[1]]),
        "replicate_difference": across(values, lambda reading: reading["replicate_difference"]),
        f"{UNIFORM_RULE}_a_minus_b": across(
            values, lambda reading: reading[f"{UNIFORM_RULE}_a_minus_b"]["mean"]),
        f"{LAW_RULE}_a_minus_b": across(
            values, lambda reading: reading[f"{LAW_RULE}_a_minus_b"]["mean"]),
        "J_by_rule": {name: across(values, lambda reading, name=name: reading["J_by_rule"][name])
                      for name in PANEL_RULES},
        "blocks_with_G_at_or_above_the_margin": [
            reading["block_seed"] for reading in values if reading["G_at_or_above_the_margin"]],
        "blocks_with_a_positive_G_above_twice_the_replicate_difference": [
            reading["block_seed"] for reading in values
            if reading["G_positive"] and reading["G_exceeds_twice_the_replicate_difference"]],
        "share_check_by_block": {str(reading["block_seed"]): reading["share_check_by_panel"]
                                 for reading in values},
        "blocks_where_the_share_check_holds": [
            reading["block_seed"] for reading in values if reading["share_check_holds"]],
        "definition": SOURCE_NOTES["grouping"]}


def prediction_rows(primary):
    """The entry's two declared outcomes, on the primary group alone. Arithmetic, not a verdict."""
    gains = [reading["G"] for reading in primary]
    mean = float(np.mean(gains)) if gains else None
    at_or_above = [reading["block_seed"] for reading in primary
                   if reading["G_at_or_above_the_margin"]]
    reversal_blocks = [
        reading["block_seed"] for reading in primary
        if reading["G_positive"] and reading["G_exceeds_twice_the_replicate_difference"]]
    shortfall = (None if mean is None
                 else bool(mean < GAIN_MARGIN and len(at_or_above) <= SHORTFALL_BLOCKS))
    reversal = (None if mean is None
                else bool(mean >= GAIN_MARGIN and len(reversal_blocks) >= REVERSAL_BLOCKS))
    return {
        "DM_G_falls_short": {
            "statement": (
                f"the DM's prediction: the mean G over the three `{PRIMARY_ARM}` checkpoints is "
                f"below {GAIN_MARGIN} J and at most {SHORTFALL_BLOCKS} block is at or above it"),
            "value_definition": (
                "the mean over the primary checkpoints read of G, and the number of them whose own "
                f"G is at or above {GAIN_MARGIN}"),
            "mean_G": mean, "blocks_at_or_above_the_margin": at_or_above,
            "blocks_read": len(primary), "blocks_considered": len(BLOCKS),
            "holds": shortfall},
        "REVERSAL": {
            "statement": (
                f"the reversal outcome fixed at 02:51: the mean G over the three `{PRIMARY_ARM}` "
                f"checkpoints is at least {GAIN_MARGIN} J, with a positive paired gain larger than "
                f"{REPLICATE_FACTOR:g} times the replicate difference on at least "
                f"{REVERSAL_BLOCKS} blocks"),
            "value_definition": (
                "the mean over the primary checkpoints read of G, and the number of them with "
                "G > 0 and G > 2 |G_a - G_b|"),
            "mean_G": mean, "blocks_with_a_qualifying_gain": reversal_blocks,
            "blocks_read": len(primary), "blocks_considered": len(BLOCKS),
            "holds": reversal},
        "intermediate_check": {
            "statement": (
                "the intermediate check: the executed label shares under `law_every_10` follow q, "
                f"i.e. the largest executed share is within {SHARE_TOLERANCE} of max q on both "
                "replicates of a checkpoint"),
            "blocks_where_it_holds": [reading["block_seed"] for reading in primary
                                      if reading["share_check_holds"]],
            "by_block": {str(reading["block_seed"]): reading["share_check_by_panel"]
                         for reading in primary},
            "blocks_read": len(primary),
            "value_definition": SOURCE_NOTES["executed_shares"]},
        "counting_note": (
            "the counts are the arithmetic of statements declared before the run, on the "
            "checkpoints that were read, and only on the primary group. A count of three blocks is "
            "not an interval and not a weight of evidence, and no margin here is a decision rule; "
            f"a panel's conditional evaluation noise on this direction is about {PANEL_NOISE} J, "
            "which is why G is paired by world and why the replicate difference is reported beside "
            "it. No p-value is computed and none is implied"),
    }


def reduce_inputs(probes):
    """This object's six probes: the three primary and the three secondary checkpoints."""
    b13.bind()  # the pure reading B13's own reduce takes: identities only, nothing wrapped
    shas = {summary.get("launch_sha") for summary in probes}
    if len(shas) > 1:
        raise ValueError(f"mixed launch shas among the probes: {sorted(str(s) for s in shas)}")

    rows, failures, seen = {}, {}, set()
    for summary in probes:
        key = (int(summary.get("block_seed", -1)), summary.get("checkpoint_arm"))
        if key in seen:  # a second probe of the same checkpoint is never a choice
            raise ValueError(f"duplicate checkpoint {key[1]} {key[0]}")
        seen.add(key)
        try:
            rows[key] = probe_row(summary)
        except (KeyError, TypeError, ValueError) as exc:
            failures[f"{key[0]}:{key[1]}"] = str(exc)

    checkpoints, readings = [], []
    for arm in ARMS:
        for seed in sorted(BLOCKS):
            key = (seed, arm)
            entry = {"block_seed": seed, "checkpoint_arm": arm,
                     "evaluation_seed": BLOCKS[seed], "status": "incomplete",
                     "missing_or_invalid": None}
            if key in rows:
                entry["status"] = "complete"
                entry.update(checkpoint_reading(rows[key]))
                readings.append(entry)
            else:
                entry["missing_or_invalid"] = failures.get(f"{seed}:{arm}", "not supplied")
            checkpoints.append(entry)

    primary = [reading for reading in readings if reading["checkpoint_arm"] == PRIMARY_ARM]
    fit_shas = {row["fit_launch_sha"] for row in rows.values()}
    result = {
        "object_id": OBJECT_ID, "card": CARD, "command": "reduce",
        "launch_sha": shared.e0._git("rev-parse", "HEAD"),
        "probe_launch_sha": next(iter(shas), None) if len(shas) == 1 else None,
        "fit_launch_sha": next(iter(fit_shas), None) if len(fit_shas) == 1 else None,
        "one_fit_launch_sha": bool(len(fit_shas) == 1),
        "fit_launch_sha_by_checkpoint": {f"{seed}:{arm}": rows[(seed, arm)]["fit_launch_sha"]
                                         for (seed, arm) in sorted(rows)},
        "reference_object_ids": [b13.OBJECT_ID, b09.OBJECT_ID, b08.OBJECT_ID],
        "status": "complete" if len(readings) == len(ARMS) * len(BLOCKS) else "incomplete",
        "rules": list(PANEL_RULES), "base_rules": list(BASE_RULES),
        "replicates": list(REPLICATES), "labels": N_LABELS,
        "rule_definitions": dict(RULE_DEFINITIONS),
        "primary_arm": PRIMARY_ARM, "secondary_arm": SECONDARY_ARM,
        "quantity": (
            "J of a panel is the mean of its native world scores at the fit's own saved weights. "
            f"G is `J({LAW_RULE}) - J({UNIFORM_RULE})` paired by world - the same checkpoint, the "
            "same 32 worlds, the same evaluation seeds, mean actions on both sides - averaged over "
            "the two label-stream replicates; the replicate difference and the two same-rule "
            "differences are the label-draw noise of that pairing. The law is each fit's own "
            "frozen final estimate through B13's declared `q = .7 softmax(z) + .3 uniform`"),
        "checkpoints": checkpoints,
        "checkpoints_read": len(readings),
        "checkpoints_planned": len(ARMS) * len(BLOCKS),
        "probes_supplied": len(probes),
        "invalid_probes": dict(failures),
        "refusals": (
            "a batch of probes at more than one launch sha, a duplicate (block, arm) among them, a "
            "summary that is not this object's probe, a probe that is not complete - including one "
            "that stopped at `failed_faithful_load` - a probe that did not establish a faithful "
            "load, that took an optimizer step, whose weights digest moved, whose panels did not "
            "share the frozen decision cadence, or that does not carry all four declared panels on "
            "the same worlds. An invalid probe is listed with its reason under `invalid_probes` "
            "and is left out of the counts; it is never silently dropped"),
        "groups": {arm: group_reading(readings, arm) for arm in ARMS},
        "predictions": prediction_rows(primary),
        "interpretation_limit": INTERPRETATION_LIMIT,
        "source_notes": dict(SOURCE_NOTES),
    }
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prb = sub.add_parser("probe", help="zero-update execution of one B13 checkpoint's weights")
    prb.add_argument("--fit-root", type=Path, required=True,
                     help=f"a B13 fit root: {SUMMARY_NAME}, {WEIGHTS_NAME}, {SIDECAR_NAME} and "
                          f"{RECORDS_NAME}")
    prb.add_argument("--launch-sha", required=True, help="must equal the source HEAD; recorded")
    prb.add_argument("--output-root", type=Path, required=True)
    red = sub.add_parser("reduce")
    red.add_argument("--probes", type=Path, nargs="+", required=True,
                     help="this object's six probe summaries")
    red.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    load = lambda path: json.loads(path.read_text(encoding="utf-8"))

    if args.command == "probe":
        head = shared.e0._git("rev-parse", "HEAD")
        if not head or args.launch_sha != head:
            parser.error("--launch-sha must equal the source HEAD")
        return run_probe(args.fit_root.resolve(), args.output_root.resolve(),
                         launch_sha=args.launch_sha)

    args.output_root.mkdir(parents=True, exist_ok=True)
    result = reduce_inputs([load(path) for path in args.probes])
    result["input_probes"] = [str(path) for path in args.probes]
    shared.write_json(args.output_root / SUMMARY_NAME, result)
    print(json.dumps({
        "status": result["status"], "checkpoints_read": result["checkpoints_read"],
        "invalid_probes": result["invalid_probes"],
        "mean_G": {arm: result["groups"][arm]["mean_G"] for arm in ARMS},
        "G_by_block": {arm: result["groups"][arm]["G_by_block"] for arm in ARMS},
        "predictions": {name: entry["holds"] for name, entry in result["predictions"].items()
                        if isinstance(entry, dict) and "holds" in entry}}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
