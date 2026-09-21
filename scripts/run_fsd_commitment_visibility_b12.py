"""FSD commitment visibility B12: how far does a label's own credit see it, as the commitment grows?

Exploration, next research judgment in the direction notebook:
docs/research/candidates/flexible_skill_duration/NOTES.md (2026-09-20 19:11 PDT, B12 specified
before any score).

B11 measured the coordinator's own signal at the frozen ten-step cadence and found no usable label
ranking in it: the agent-label advantage spread is what the *team*-label placebo row - a label that
cannot reach the actor - already shows, and even a perfect-credit regression of a ten-step segment's
reward on the six label counts finds 4-12 % of a ten-step reward with R^2 <= .013, while the same
labels held by everyone for a whole episode differ by 25-40 % of J (B09, B10).  The reading was that
a label's consequence is averaged away before it can appear in the return that credits it.

B12 is the direct test of that reading, at the same fixed weights and with no fit at all: hold the
commitment longer and see whether the label becomes visible in its own credit.  Per block, for each
commitment cap in (10, 50, 100, 500), sixteen training-law rollouts through B11's own collection with
the *learner* instance's two D2 caps set to that value and restored afterwards; labels are still
sampled from the coordinator's law, per agent, all six renewing together.  `d2_k_Z` and `d2_k_max`
are the only two attributes the decision cadence reads (hmasd/agent.py:2596, 2613, both inside
`_batched_assign_skills_d2`); `skill_cap_k_max`/`team_cap_k_Z` are read from the config once, at
construction (hmasd/agent.py:482-484), and nothing else - not the rollout buffer, not the storage
path - carries a cap.

Two commands, both at fixed weights, both taking no optimizer step, neither of them a fit and
neither of them a `k` sweep for performance: nothing is trained, and no J claim is made.

`probe` runs, per block:

  (a) B11's construction, weights verification, optimizer-step prohibition, `as_trained` panel and
      the unrelaxed faithful-load check, exactly as B11 runs them;
  (b) per cap, in the order (10, 50, 100, 500), sixteen rollouts of B11's `collect_training_law` -
      the frozen collector's per-step calls with the credit arithmetic where the update would be -
      inside a context manager that sets the two caps on the learner instance and restores them in a
      `finally`, and with this object's own cap-specific seed derivation bound over B11's for the
      duration of the cap.  The geometry of every rollout is checked against the cadence the cap
      implies (`lanes * ceil(horizon / cap)` team rows, six times that agent rows, causes `reset` and
      `team_cap` only, all six agents renewing together at the same start with the same elapsed) and
      refused where it is not.

The measures, per cap, for two responses of one commitment - the frozen credit quantity (the
gamma-discounted sum of the raw team reward over the commitment, hmasd/agent.py:2348-2355) and the
undiscounted mean reward per step of the same commitment:

  (a) least squares (numpy.linalg.lstsq) of the response on the six agent-label counts with one
      fixed effect per commitment position in the episode, the six coefficients reported re-centred
      to mean zero, with lane-episode-clustered standard errors and the between-label spread;
  (b) a permutation calibration of that spread: 1,000 permutations of whole six-label vectors among
      the commitments at the same position, from a dedicated generator, and the observed spread's
      percentile and p-value in that distribution;
  (c) a placebo: the same regression on the one-hot of the *team* label, which never reaches the
      low-level actor (hmasd/networks.py:1801-1809), with its own permutation calibration;
  (d) at cap 500 only, a non-additivity term `sum_c n_c^2` added to the additive model, with its
      clustered standard error and its own permutation p-value, and the additive model's predicted
      all-equal-configuration score per label, converted to an episode J by the runner's own
      reporting factor `N_UAVS / HORIZON` (scripts/run_fsd_uav_individual_renewal_b01.py:140,
      scripts/run_fsd_baseline_interruption_b01.py:254);
  (e) secondary, and labelled arithmetic rather than signal off cap 10 because the value head was
      trained on ten-step targets: B11's own agent-label advantage table per cap;
  (f) the executed label law, the behaviour's own quality per cap (mean episode return U with a
      lane-episode standard error) and the wall seconds the cap took.

`reduce` is a pure reading of published summaries and carries no admission.  The criterion is the
notebook's, declared before any score: a cap *shows the ranking* if its agent-label coefficient
spread exceeds the 95th percentile of its own permutation spread **and** B09's best mean-action label
is ranked first or second by the centred coefficients, read on the undiscounted response with the
discounted one reported beside it.  A passing placebo invalidates that cap's reading and is flagged.
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
import run_fsd_coordinator_signal_b11 as b11
import run_fsd_label_content_b08 as b08
import run_fsd_label_map_b09 as b09
import run_fsd_label_map_sampled_b10 as b10

shared = b11.shared
entropy = b08.entropy  # the direction's own across-block description helper
DIRECTION = "flexible_skill_duration"
OBJECT_ID = "FSD_COMMITMENT_VISIBILITY_B12"
CARD = ("docs/research/candidates/flexible_skill_duration/NOTES.md "
        "(2026-09-20 19:11 PDT, B12 specified before any score)")
BLOCKS = dict(b11.BLOCKS)  # 772803, 772903, 773003
SAVE_ARM = b11.SAVE_ARM
BASELINE_RULE = b11.BASELINE_RULE  # "as_trained"
N_LABELS = b11.N_LABELS  # 6
WEIGHTS_NAME = b11.WEIGHTS_NAME
SIDECAR_NAME = b11.SIDECAR_NAME
FROZEN_CAP = b08.ARM_CAPS[0]  # 10: the caps the fit ran at, and B11's own cadence
CAPS = (10, 50, 100, 500)  # the notebook entry's four commitment caps, in this order
ROLLOUTS_PER_CAP = 16  # the entry's sixteen rollouts = 256 lane-episodes per cap
PERMUTATIONS = 1000  # the entry's 1,000 permutations of whole label vectors
PERMUTATION_PERCENTILE = 95.  # the entry's criterion percentile
CAUSES_EXPECTED = b11.CAUSES_EXPECTED  # ("reset", "team_cap")
UNDISCOUNTED = "undiscounted_mean_reward_per_step"
DISCOUNTED = "discounted_segment_reward"
RESPONSES = (UNDISCOUNTED, DISCOUNTED)
PRIMARY_RESPONSE = UNDISCOUNTED  # the criterion is read here; the other is reported beside it
NON_ADDITIVITY_CAP = 500  # the entry's non-additivity check is cap 500 only
DROP_LABEL = N_LABELS - 1  # the label whose count column is dropped to break the collinearity
ALTERNATIVE_FRACTION = .5  # "below half of B10's sampled constant-label spread"
DISCOUNTED_AGREEMENT_TOLERANCE = 1e-5  # float32 storage of a float64 accumulation

SEED_DERIVATION = (
    "seed_rng(int.from_bytes(sha256(f'{training_seed}:b12:cap{cap}:rollout{r}').digest()[:8], "
    "'big') % 2 ** 31) at the start of rollout r of cap `cap`, where `seed_rng` is the frozen "
    "run_fsd_uav_individual_renewal_b01.seed_rng (random.seed, numpy.random.seed, "
    "torch.manual_seed). B11's `collect_training_law` calls its own module-global "
    "`collection_seed(training_seed, rollout)`, so this object binds that global to its "
    "cap-specific derivation for the duration of one cap's collection and restores it in a "
    "`finally` (`run_fsd_commitment_visibility_b12.b11_collection_seed_bound`); B11's own function "
    "object is put back untouched, and B11's file is not edited. The collection lanes are "
    "`run_flexible_skill_duration_e0._make_envs(16, training_seed + 500, ...)` - B11's own lanes, "
    "rebuilt once per cap so every cap sees the same sixteen worlds")

SOURCE_NOTES = {
    "cap_attributes": (
        "the D2 decision cadence reads two attributes of the agent *instance*: "
        "`self.d2_k_Z` at hmasd/agent.py:2596 (`team_cap_fire = team_ages[eval_indices] >= "
        "self.d2_k_Z`) and `self.d2_k_max` at hmasd/agent.py:2613 (`agent_cap_fire = "
        "agent_ages[hold_idx] >= self.d2_k_max`), both inside `_batched_assign_skills_d2` "
        "(hmasd/agent.py:2480). They are set once from `config.skill_cap_k_max` and "
        "`config.team_cap_k_Z` at construction (hmasd/agent.py:482-484) and read nowhere else on "
        "the collection path: the rollout buffer allocates on the rollout length and never on a cap "
        "(hmasd/utils.py:485-516), the D2 storage path keys its rows on the segment's start index "
        "and its discounted accumulator on `t - start` with no length bound "
        "(hmasd/agent.py:2264-2377), and `config.k` reaches the D2 route nowhere - the three "
        "`env_steps % config.k` boundaries at hmasd/agent.py:2107, 2791 and 3283 are the `off` and "
        "HA-CTSE routes, and hmasd/agent.py:3283 takes the D2 decision mask instead when "
        "`d2_enabled`. The one remaining `config.k`, the GRU chunk length at hmasd/agent.py:6309, "
        "is inside the low-level update, which this probe never calls. B08 sets the same two "
        "attributes on the *evaluator* instance for one panel "
        "(scripts/run_fsd_label_content_b08.py:139 `RULE_CAPS`, `ExecutionRule.attached`); this "
        "object sets them on the *learner*, which is the instance that collects"),
    "cap_restoration": (
        "the caps are set inside a context manager that restores the two attributes in a `finally` "
        "(`commitment_cap`), so a failure inside a cap's collection cannot leave the learner "
        "carrying that cap for the next one. The manager refuses to run at all unless both "
        "interruption costs are infinite - with a finite cost the held label enters the trigger "
        "statistic and the cap would not be the only thing that moved - and unless the D2 "
        "discriminator age feature is `off`, because `_d2_normalized_team_age` and "
        "`_d2_normalized_agent_age` (hmasd/agent.py:4253-4263) divide the stored age by the same "
        "two attributes"),
    "expected_geometry": (
        "a team decision fires at the episode reset (`env_steps == 0`, hmasd/agent.py:2518) and "
        "thereafter whenever the team age reaches the cap, and the age at step `t` of an episode is "
        "`t`, so a cap of `k` decides at t = 0, k, 2k, ... and one lane-episode of `horizon` steps "
        "carries `ceil(horizon / k)` team commitments. With `d2_k_max = d2_k_Z` the agent cap can "
        "never fire before the team cap, so every commitment samples all six agents (ADR 01 "
        "invariant 7) and the causes are `reset` and `team_cap` only. The probe checks the row "
        "counts, the causes, `valid implies sampled`, the six agent segments sharing the team "
        "segment's start, and every segment's elapsed against `min(cap, horizon - start)`, and "
        "refuses the collection where they are not the cadence's"),
    "per_step_reward": (
        "the response's undiscounted term needs the raw scalar team reward of every step, which the "
        "frozen storage keeps only in discounted form. B11's `collect_training_law` offers no "
        "per-step hook, so this object records the reward from the *environment* side: a `RewardTape` "
        "replaces `env.step` on each collection lane - an instance attribute on an environment this "
        "object constructed, popped in a `finally` - with a wrapper that calls the original first "
        "and unchanged, appends `result[1]` and returns the original result object. B11's loop, its "
        "call order and its arguments are untouched, and the tape draws no randomness. Each lane is "
        "stepped exactly once per step of every rollout, so the tape's flat per-lane list reshapes "
        "to (rollouts, horizon) and the probe refuses any other length. The recomputed "
        "gamma-discounted sum of the taped rewards over each commitment is compared with the "
        "buffer's own `team_reward` and the maximum difference is published"),
    "responses": (
        "two responses per commitment. `discounted_segment_reward` is the frozen credit quantity: "
        "the gamma-discounted sum of the raw team reward over the commitment, accumulated by "
        "hmasd/agent.py:2348-2355 and read from the buffer's own `team_reward` row - at cap 500 it "
        "sees mostly the first hundred steps, since gamma ** 100 is about .37 and gamma ** 500 "
        "about .0066. `undiscounted_mean_reward_per_step` is the undiscounted sum of the same raw "
        "per-step rewards over the commitment's steps divided by its elapsed steps, so it is "
        "comparable across caps and is the response the criterion is read on"),
    "position_fixed_effects": (
        "reward drifts within an episode, and a long commitment sits at a different part of the "
        "episode than a short one, so the model carries one fixed effect per commitment position "
        "(0-based commitment number within the lane-episode). The six counts sum to six and the "
        "position dummies sum to one, so the two blocks are exactly collinear: the design drops one "
        "label's count column (label 5 by default) and keeps every position dummy, which identifies "
        "the five remaining coefficients as differences from the dropped label. The published "
        "coefficients are then re-centred to mean zero over the six labels, which is invariant to "
        "*which* label was dropped (dropping label d gives beta_c - beta_d, and centring removes the "
        "common shift); the probe fits the model a second time with a different dropped label and "
        "publishes the maximum difference between the two centred vectors"),
    "centred_coefficients": (
        "the six centred coefficients are `C A beta` where `A` selects the count columns with a zero "
        "row for the dropped label and `C = I - 11'/6` centres them, so their clustered covariance "
        "is `C A V A' C'` with `V` the cluster-robust sandwich of the whole fit. The spread is "
        "max minus min of the six, which is the same number before and after centring"),
    "permutation": (
        "1,000 permutations of whole six-label vectors among the commitments at the same position "
        "index within this block and cap, from a generator seeded by (evaluation_seed, cap, "
        "response) and touching no global stream. Permuting the whole vector keeps every "
        "commitment's configuration intact and only breaks its link to its own reward; permuting "
        "within a position keeps the fixed effects exactly as they are. Every draw is the same "
        "`fit_centred` least squares on the same design the observed estimate used - there is no "
        "second estimator - and the routine refuses to run at all unless it reproduces the observed "
        "statistic at the identity permutation. `p_value` is "
        "(1 + #{permuted >= observed}) / (1 + permutations)"),
    "placebo": (
        "the team label never reaches the low-level actor: `SkillDiscoverer.forward` "
        "(hmasd/networks.py:1801-1809) passes only the observation, the *agent* label and the hidden "
        "state. At fixed weights it therefore cannot move an executed action, so the same regression "
        "on the one-hot of the team label (counts summing to one) measures what this design finds "
        "when there is nothing to find. A placebo that passes the spread test invalidates that cap's "
        "reading, and `reduce` flags it"),
    "non_additivity": (
        "the strongest alternative the notebook names is that the joint map is not additive - a "
        "label pays only when all six agents hold it. `sum_c n_c^2` is the homogeneity of the "
        "configuration (6 when all six agents hold different labels, 36 when they all hold the "
        "same), centred to its own mean so it does not absorb the level; a positive coefficient is "
        "the coordination term. Beside it, the additive model's predicted all-equal score for each "
        "label, `6 * beta_c + mean_p delta_p` in the drop parametrisation, which is invariant to the "
        "dropped label, converted to an episode J by the reporting factor"),
    "reporting_factor": (
        "the runner converts a scalar episode return U to the native score J by the pure factor "
        "`N_UAVS / HORIZON` = 6 / 500 = .012: "
        "`scripts/run_fsd_baseline_interruption_b01.py:254` computes `native_scores_J = "
        "shared.N_UAVS * returns / horizon` with `horizon = shared.HORIZON` (line 201), and "
        "`scripts/run_fsd_uav_individual_renewal_b01.py:140` publishes the same number as "
        "`native_score_factor` on every summary. There is no offset and no per-world term, so a mean "
        "reward per step multiplied by N_UAVS is an episode J, and the additive model's predicted "
        "all-equal mean reward per step converts directly"),
    "secondary_advantage_table": (
        "B11's own agent-label advantage table, computed by B11's `label_table` on this cap's rows. "
        "Off cap 10 it is arithmetic and not the signal a retrained critic would give: the value "
        "head was trained on ten-step targets, so at cap 50, 100 and 500 the stored segment value is "
        "a ten-step value being differenced against a much longer return. It is published as a "
        "secondary block and labelled so everywhere"),
    "lane_cluster": b11.SOURCE_NOTES["lane_cluster"],
    "collector_transcription": b11.SOURCE_NOTES["collector_transcription"],
    "no_update": b11.SOURCE_NOTES["no_update"],
    "advantages": b11.SOURCE_NOTES["advantages"],
    "segment_reward": b11.SOURCE_NOTES["segment_reward"],
    "agent_label_of_a_row": b11.SOURCE_NOTES["agent_label_of_a_row"],
    "label_free_baseline": b11.SOURCE_NOTES["label_free_baseline"],
    "row_geometry": b11.SOURCE_NOTES["row_geometry"],
    "weights_and_route": b11.SOURCE_NOTES["weights_and_route"],
    "evaluation_route": b11.SOURCE_NOTES["evaluation_route"],
    "lane_to_world": b11.SOURCE_NOTES["lane_to_world"],
}

INTERPRETATION_LIMIT = (
    "a fixed-weight measurement, not a fit and not a `k` sweep for performance: zero optimizer "
    "steps, nothing is trained and no J claim is made; it measures how visible a label is in its "
    "own credit as a function of the commitment length. Exploration; three blocks; one checkpoint "
    "per block, and that checkpoint is the end of training. The assignment is the coordinator's own "
    "near-flat law and not an exact randomisation - shares .14-.19 with a weak state dependence - so "
    "the permutation calibration is the reference for what no effect looks like here, and the "
    "regression is not an experiment with assigned treatment. The low level's weights were trained "
    "under ten-step commitments, so a long commitment executes six policies that were never asked "
    "to hold that long, and the coordinator's value head was trained on ten-step targets, which is "
    "why the advantage table off cap 10 is labelled arithmetic rather than signal. The collection "
    "worlds are the block's own sixteen lanes seeded 500 above the training seed and are not the "
    "fit's worlds, and the collection's random streams are this object's. A fixed-weight panel is "
    "bit-reproducible only on the host that trained the checkpoint - B08's own local probe attempts "
    "failed the faithful load off that host - so this command runs on wsl_4070.")


# ---------------------------------------------------------------------------
# seeds, caps and the per-step reward tape
# ---------------------------------------------------------------------------


def collection_seed(training_seed, cap, rollout):
    """The dedicated seed of one collection rollout: a function of (block, cap, rollout) alone."""
    digest = hashlib.sha256(
        f"{int(training_seed)}:b12:cap{int(cap)}:rollout{int(rollout)}".encode("utf-8"))
    return int.from_bytes(digest.digest()[:8], "big") % 2 ** 31


def permutation_generator(evaluation_seed, cap, response):
    """The permutation calibration's own generator; it touches no global stream."""
    digest = hashlib.sha256(f"b12:permutation:{response}".encode("utf-8")).digest()[:8]
    return np.random.default_rng(
        [int(evaluation_seed), int(cap), int.from_bytes(digest, "big")])


@contextmanager
def b11_collection_seed_bound(cap):
    """Bind B11's module-global `collection_seed` to this object's cap-specific derivation.

    `b11.collect_training_law` resolves `collection_seed(training_seed, rollout)` from its own module
    globals at call time, and the function hard-codes `:b11:rollout{r}`.  Rather than edit B11 (its
    file is frozen), this object binds the global for the duration of one cap's collection and puts
    B11's own function object back in a `finally`.
    """
    original = b11.collection_seed

    def cap_collection_seed(training_seed, rollout):
        return collection_seed(training_seed, cap, rollout)

    b11.collection_seed = cap_collection_seed
    try:
        yield cap_collection_seed
    finally:
        b11.collection_seed = original


@contextmanager
def commitment_cap(agent, cap):
    """Set the learner instance's two D2 caps for one cap's collection and restore them after."""
    if not getattr(agent, "d2_enabled", False):
        raise ValueError("the commitment caps are defined on the D2 route")
    if np.isfinite(agent.d2_cost_c) or np.isfinite(agent.d2_cost_c_Z):
        # With a finite cost the trigger statistic reads the held label, so the cap would not be
        # the only thing this object moved.
        raise ValueError("this object requires infinite interruption costs")
    if str(getattr(agent, "d2_age_feature", "off")) != "off":
        # The age feature divides the stored age by these same two attributes.
        raise ValueError("this object requires the D2 discriminator age feature to be off")
    if int(cap) < 1:
        raise ValueError("a commitment cap is at least one step")
    restore = {"d2_k_max": int(agent.d2_k_max), "d2_k_Z": int(agent.d2_k_Z)}
    agent.d2_k_max = int(cap)
    agent.d2_k_Z = int(cap)
    try:
        yield restore
    finally:
        for name, value in restore.items():
            setattr(agent, name, value)


class RewardTape:
    """The raw scalar team reward of every collected step, per lane, in the loop's own call order.

    The wrapper calls the frozen `env.step` first and unchanged and returns its own result object, so
    the collection is B11's loop on B11's calls; only a copy of `result[1]` is kept.
    """

    def __init__(self, envs):
        self.envs = list(envs)
        self.rewards = [[] for _ in self.envs]
        self.calls = 0

    @contextmanager
    def attached(self):
        for env in self.envs:
            if "step" in env.__dict__:  # never shadow a wrapper this object did not put there
                raise ValueError("a collection lane already carries an instance-level `step`")
        originals = [env.step for env in self.envs]
        for lane, env in enumerate(self.envs):
            env.step = self._wrap(lane, originals[lane])
        try:
            yield self
        finally:
            for env in self.envs:
                env.__dict__.pop("step", None)

    def _wrap(self, lane, original):
        store = self.rewards[lane]

        def step(*args, **kwargs):
            result = original(*args, **kwargs)
            store.append(float(result[1]))
            self.calls += 1
            return result

        return step

    def require_shape(self, rollouts, horizon):
        """Refuse a tape whose per-lane length is not one call per step of every rollout."""
        expected = int(rollouts) * int(horizon)
        lengths = [len(store) for store in self.rewards]
        if any(length != expected for length in lengths):
            raise ValueError(
                f"the reward tape carries {sorted(set(lengths))} steps per lane, not the "
                f"{expected} the collection takes")
        return expected

    def rollout(self, index, horizon):
        """The taped rewards of one rollout as [horizon, lanes], in the collector's own order."""
        start, stop = int(index) * int(horizon), (int(index) + 1) * int(horizon)
        return np.asarray([store[start:stop] for store in self.rewards],
                          dtype=np.float64).T


def expected_team_rows(lanes, horizon, cap):
    """`lanes * ceil(horizon / cap)`: the cadence a cap implies on a whole-episode rollout."""
    return int(lanes) * int(math.ceil(float(horizon) / float(cap)))


# ---------------------------------------------------------------------------
# the commitments of one rollout
# ---------------------------------------------------------------------------


def commitment_frame(frame, rewards, *, cap, gamma, horizon, n_labels=N_LABELS):
    """One rollout's commitments: the team segments with both responses and their configuration."""
    team = frame["team"]
    rows = int(frame["rows_M"])
    labels_flat = np.asarray(frame["agent"]["label"], dtype=np.int64)
    if labels_flat.size % max(1, rows):
        raise ValueError("the agent rows do not divide into the team rows")
    n_agents = labels_flat.size // rows if rows else 0
    labels = labels_flat.reshape(rows, n_agents)
    agent_elapsed = np.asarray(frame["agent"]["elapsed"], dtype=np.int64).reshape(rows, n_agents)
    lane = np.asarray(team["lane"], dtype=np.int64)
    start = np.asarray(team["step"], dtype=np.int64)
    elapsed = np.asarray(team["elapsed"], dtype=np.int64)
    rewards = np.asarray(rewards, dtype=np.float64)

    # every team commitment carries its six agent segments at the same start with the same elapsed
    if not np.array_equal(agent_elapsed, np.repeat(elapsed[:, None], n_agents, axis=1)):
        raise ValueError("an agent segment does not share its team commitment's elapsed steps")
    if np.any(elapsed < 1) or np.any(start + elapsed > int(horizon)):
        raise ValueError("a commitment runs outside the rollout's own horizon")
    expected_elapsed = np.minimum(int(cap), int(horizon) - start)
    if not np.array_equal(elapsed, expected_elapsed):
        raise ValueError(
            f"a commitment's elapsed steps are not the cadence of cap {int(cap)}")

    undiscounted = np.zeros(rows, dtype=np.float64)
    discounted = np.zeros(rows, dtype=np.float64)
    for index in range(rows):
        window = rewards[start[index]:start[index] + elapsed[index], lane[index]]
        undiscounted[index] = float(window.sum())
        discounted[index] = float(
            (np.power(float(gamma), np.arange(window.size, dtype=np.float64)) * window).sum())

    # the 0-based commitment number within the lane-episode, by the order the starts ran in
    position = np.zeros(rows, dtype=np.int64)
    for key in np.unique(lane):
        mask = lane == key
        order = np.argsort(start[mask], kind="stable")
        ranks = np.empty(int(mask.sum()), dtype=np.int64)
        ranks[order] = np.arange(int(mask.sum()), dtype=np.int64)
        position[mask] = ranks
    counts = np.asarray(team["counts"], dtype=np.float64)
    if not np.array_equal(counts.sum(axis=1), np.full(rows, float(n_agents))):
        raise ValueError("a commitment's label counts do not sum to the team size")
    team_label = np.asarray(team["label"], dtype=np.int64)
    one_hot = np.zeros((rows, n_labels), dtype=np.float64)
    if rows:
        one_hot[np.arange(rows), team_label] = 1.
    return {
        "cap": np.full(rows, int(cap), dtype=np.int64),
        "rollout": np.asarray(team["rollout"], dtype=np.int64),
        "lane": lane, "start": start, "elapsed": elapsed, "position": position,
        "labels": labels, "team_label": team_label,
        "counts": counts, "team_one_hot": one_hot,
        "homogeneity": (counts ** 2).sum(axis=1),
        DISCOUNTED: np.asarray(team["reward"], dtype=np.float64),
        "discounted_from_tape": discounted,
        "undiscounted_sum": undiscounted,
        UNDISCOUNTED: undiscounted / elapsed.astype(np.float64),
        "advantage": np.asarray(team["advantage"], dtype=np.float64),
        "value": np.asarray(team["value"], dtype=np.float64),
        "n_agents": n_agents}


def stack_commitments(frames, *, n_labels=N_LABELS):
    """Every rollout's commitments of one cap, pooled into one table."""
    vectors = ("cap", "rollout", "lane", "start", "elapsed", "position", "team_label",
               "homogeneity", DISCOUNTED, "discounted_from_tape", "undiscounted_sum",
               UNDISCOUNTED, "advantage", "value")
    pooled = {name: np.concatenate([frame[name] for frame in frames]) for name in vectors}
    for name in ("labels", "counts", "team_one_hot"):
        pooled[name] = np.concatenate([frame[name] for frame in frames], axis=0)
    pooled["n_agents"] = int(frames[0]["n_agents"]) if frames else 0
    pooled["clusters"] = b11.clusters_of(pooled)
    return pooled


# ---------------------------------------------------------------------------
# the regression: the six counts with one fixed effect per commitment position
# ---------------------------------------------------------------------------


def _label_columns(drop_label, n_labels=N_LABELS):
    return [label for label in range(n_labels) if label != int(drop_label)]


def design_matrix(counts, positions, n_positions, *, drop_label, extra=None, n_labels=N_LABELS):
    """[five label counts | optional extra columns | one dummy per commitment position]."""
    columns = _label_columns(drop_label, n_labels)
    blocks = [np.asarray(counts, dtype=np.float64)[:, columns]]
    if extra is not None:
        blocks.append(np.asarray(extra, dtype=np.float64).reshape(len(positions), -1))
    dummies = np.zeros((len(positions), int(n_positions)), dtype=np.float64)
    dummies[np.arange(len(positions)), positions] = 1.
    blocks.append(dummies)
    design = np.concatenate(blocks, axis=1)
    layout = {"label_columns": columns, "extra_width": 0 if extra is None else blocks[1].shape[1],
              "position_width": int(n_positions)}
    return design, layout


def _centring_contrast(layout, width, n_labels=N_LABELS):
    """`C A`: the linear map from the fitted parameters to the six centred label coefficients."""
    selector = np.zeros((n_labels, width), dtype=np.float64)
    for index, label in enumerate(layout["label_columns"]):
        selector[label, index] = 1.
    centring = np.eye(n_labels) - np.full((n_labels, n_labels), 1. / n_labels)
    return centring @ selector, selector


def fit_centred(counts, positions, response, *, n_positions, drop_label=DROP_LABEL, extra=None,
                n_labels=N_LABELS):
    """One least-squares fit of the design, and the six centred label coefficients it implies.

    This is the one arithmetic the observed estimate and every permutation draw share, so there is no
    second estimator to keep consistent with the first.
    """
    design, layout = design_matrix(counts, positions, n_positions, drop_label=drop_label,
                                   extra=extra, n_labels=n_labels)
    beta, _residuals, rank, _singular = np.linalg.lstsq(design, response, rcond=None)
    contrast, selector = _centring_contrast(layout, design.shape[1], n_labels)
    return {"design": design, "layout": layout, "beta": beta, "rank": int(rank),
            "centred": contrast @ beta, "raw": selector @ beta,
            "contrast": contrast,
            "extra": beta[len(layout["label_columns"]):
                          len(layout["label_columns"]) + layout["extra_width"]]}


def label_regression(counts, positions, response, clusters, *, n_positions, drop_label=DROP_LABEL,
                     extra=None, extra_name=None, team_size=N_LABELS, n_labels=N_LABELS):
    """Least squares of `response` on the label counts with position fixed effects.

    The counts sum to the team size and the position dummies sum to one, so one label's count column
    is dropped; the published coefficients are re-centred to mean zero over the six labels, which is
    invariant to which label was dropped.
    """
    counts = np.asarray(counts, dtype=np.float64)
    response = np.asarray(response, dtype=np.float64)
    positions = np.asarray(positions, dtype=np.int64)
    clusters = np.asarray(clusters, dtype=np.int64)
    if counts.shape[0] != response.size or response.size == 0:
        return None
    fit = fit_centred(counts, positions, response, n_positions=n_positions, drop_label=drop_label,
                      extra=extra, n_labels=n_labels)
    design, layout, beta, rank = fit["design"], fit["layout"], fit["beta"], fit["rank"]
    errors = response - design @ beta
    covariance, groups, scale = b11.clustered_covariance(design, errors, clusters)
    contrast, centred = fit["contrast"], fit["centred"]
    centred_covariance = contrast @ covariance @ contrast.T
    standard_errors = np.sqrt(np.clip(np.diag(centred_covariance), 0., None))
    values = {label: float(centred[label]) for label in range(n_labels)}
    spread = b11.spread_of(values)
    gap_se = None
    if spread is not None:
        best, worst = spread["best_label"], spread["worst_label"]
        variance = (centred_covariance[best, best] + centred_covariance[worst, worst]
                    - 2. * centred_covariance[best, worst])
        gap_se = float(math.sqrt(variance)) if variance > 0. else 0.
    order, _ranked = b11.ranking_of(
        {str(label): {"coefficient": float(centred[label])} for label in range(n_labels)},
        "coefficient")
    # the drop parametrisation's own coefficients and the mean position effect, which together give
    # an all-equal prediction that does not depend on which label was dropped
    raw = fit["raw"]
    position_start = design.shape[1] - layout["position_width"]
    position_mean = float(np.mean(design[:, position_start:] @ beta[position_start:]))
    total = float(((response - response.mean()) ** 2).sum())
    result = {
        "segments": int(response.size), "columns": int(design.shape[1]), "rank": int(rank),
        "full_rank": bool(int(rank) == int(design.shape[1])),
        "clusters": int(groups), "positions": int(n_positions),
        "small_sample_correction": float(scale),
        "dropped_label": int(drop_label),
        "centred_coefficients": {str(label): float(centred[label]) for label in range(n_labels)},
        "clustered_se": {str(label): float(standard_errors[label]) for label in range(n_labels)},
        "ranking": order,
        "best_label": None if spread is None else spread["best_label"],
        "worst_label": None if spread is None else spread["worst_label"],
        "max_minus_min": None if spread is None else spread["max_minus_min"],
        "max_minus_min_clustered_se": gap_se,
        "drop_parametrised_coefficients": {str(label): float(raw[label])
                                           for label in range(n_labels)},
        "mean_position_effect": position_mean,
        "all_equal_prediction": {str(label): float(team_size) * float(raw[label]) + position_mean
                                 for label in range(n_labels)},
        "residual_sd": float(errors.std(ddof=1)) if errors.size > 1 else None,
        "r_squared": (None if total <= 0. else float(1. - float((errors ** 2).sum()) / total)),
        "definition": SOURCE_NOTES["position_fixed_effects"] + " " + SOURCE_NOTES[
            "centred_coefficients"]}
    if extra is not None:
        index = len(layout["label_columns"])
        errors_extra = np.sqrt(np.clip(np.diag(covariance), 0., None))
        result["extra"] = {
            "name": extra_name, "coefficient": float(beta[index]),
            "clustered_se": float(errors_extra[index]),
            "width": int(layout["extra_width"])}
    return result


def _position_groups(positions, n_positions):
    return [np.flatnonzero(positions == position) for position in range(int(n_positions))]


def permutation_calibration(counts, positions, response, generator, *, n_positions, observed,
                            drop_label=DROP_LABEL, statistic="spread", homogeneity=False,
                            permutations=PERMUTATIONS, n_labels=N_LABELS,
                            percentile=PERMUTATION_PERCENTILE):
    """The permutation distribution of the statistic under label vectors reshuffled within position.

    `statistic` is either the centred coefficients' spread or, where `homogeneity` is set, the
    coefficient of the recomputed `sum_c n_c^2` column.  Every draw is the same `fit_centred` the
    observed estimate used, so the routine checks itself against the observed value at the identity
    permutation before it permutes anything.
    """
    counts = np.asarray(counts, dtype=np.float64)
    positions = np.asarray(positions, dtype=np.int64)
    response = np.asarray(response, dtype=np.float64)
    if counts.shape[0] != response.size or response.size == 0:
        return None

    # the position dummies never move under this permutation, so the design is built once and only
    # its label-count columns (and the homogeneity column they imply) are rewritten per draw
    columns = _label_columns(drop_label, n_labels)
    width = len(columns)
    design, layout = design_matrix(
        counts, positions, n_positions, drop_label=drop_label,
        extra=(np.zeros((counts.shape[0], 1)) if homogeneity else None), n_labels=n_labels)
    contrast, _selector = _centring_contrast(layout, design.shape[1], n_labels)

    def compute(table):
        design[:, :width] = table[:, columns]
        if homogeneity:
            column = (table ** 2).sum(axis=1)
            design[:, width] = column - column.mean()
        beta, _residuals, _rank, _singular = np.linalg.lstsq(design, response, rcond=None)
        if statistic == "extra":
            return float(beta[width])
        centred = contrast @ beta
        return float(centred.max() - centred.min())

    if observed is None:
        return None
    identity = compute(counts)
    if not np.isfinite(identity):
        return None
    if abs(identity - float(observed)) > 1e-8 * max(1., abs(float(observed))):
        raise ValueError(
            "the permutation routine does not reproduce the fitted statistic at the identity "
            f"permutation: {identity} against {observed}")
    groups = _position_groups(positions, n_positions)
    draws = np.zeros(int(permutations), dtype=np.float64)
    permuted = np.empty_like(counts)
    for index in range(int(permutations)):
        for rows in groups:
            if rows.size:
                permuted[rows] = counts[rows[generator.permutation(rows.size)]]
        draws[index] = compute(permuted)
    reference = np.abs(draws) if statistic == "extra" else draws
    target = abs(float(observed)) if statistic == "extra" else float(observed)
    exceed = int(np.sum(reference >= target))
    threshold = float(np.percentile(reference, float(percentile)))
    return {
        "permutations": int(permutations),
        "statistic": "centred coefficient spread" if statistic != "extra" else "extra coefficient",
        "observed": float(observed),
        "identity_check": identity,
        "percentile": float(percentile),
        "percentile_value": threshold,
        "exceeds_percentile_value": bool(target > threshold),
        "p_value": float((1 + exceed) / (1 + int(permutations))),
        "upper_p_value": float((1 + int(np.sum(draws >= float(observed))))
                               / (1 + int(permutations))),
        "distribution": {"mean": float(reference.mean()), "sd": float(reference.std(ddof=1)),
                         "min": float(reference.min()), "max": float(reference.max()),
                         "median": float(np.median(reference))},
        "definition": SOURCE_NOTES["permutation"] + (
            " For the homogeneity term the reference distribution and the comparison are taken on "
            "the absolute coefficient, and `upper_p_value` is the one-sided count above the signed "
            "observed value." if statistic == "extra" else "")}


# ---------------------------------------------------------------------------
# one cap's measures
# ---------------------------------------------------------------------------


def response_block(commitments, response, *, evaluation_seed, cap, n_positions,
                   reporting_factor, non_additivity=False, n_labels=N_LABELS):
    """The regression, its permutation calibration and the placebo, for one response of one cap."""
    counts = commitments["counts"]
    positions = commitments["position"]
    clusters = commitments["clusters"]
    values = commitments[response]
    team_size = int(commitments["n_agents"])
    agent = label_regression(counts, positions, values, clusters, n_positions=n_positions,
                             team_size=team_size, n_labels=n_labels)
    alternate_drop = (DROP_LABEL + 1) % n_labels
    alternate = label_regression(counts, positions, values, clusters, n_positions=n_positions,
                                 drop_label=alternate_drop, team_size=team_size, n_labels=n_labels)
    drop_difference = None
    if agent is not None and alternate is not None:
        drop_difference = float(max(
            abs(agent["centred_coefficients"][str(label)]
                - alternate["centred_coefficients"][str(label)]) for label in range(n_labels)))
    calibration = permutation_calibration(
        counts, positions, values,
        permutation_generator(evaluation_seed, cap, response),
        n_positions=n_positions, observed=None if agent is None else agent["max_minus_min"])
    placebo = label_regression(commitments["team_one_hot"], positions, values, clusters,
                               n_positions=n_positions, team_size=1, n_labels=n_labels)
    placebo_calibration = permutation_calibration(
        commitments["team_one_hot"], positions, values,
        permutation_generator(evaluation_seed, cap, response + "|placebo"),
        n_positions=n_positions, observed=None if placebo is None else placebo["max_minus_min"])
    block = {
        "response": response,
        "response_definition": SOURCE_NOTES["responses"],
        "mean": float(np.mean(values)) if values.size else None,
        "sd": float(np.std(values, ddof=1)) if values.size > 1 else None,
        "agent_label_regression": agent,
        "agent_label_permutation": calibration,
        "centred_coefficient_drop_invariance": {
            "alternate_dropped_label": int(alternate_drop),
            "max_absolute_difference": drop_difference,
            "definition": ("the same model refitted with a different dropped label; the centred "
                           "coefficients are invariant to the choice, so this is a check and not a "
                           "second estimate")},
        "placebo_regression": placebo,
        "placebo_permutation": placebo_calibration,
        "placebo_note": SOURCE_NOTES["placebo"],
        "shows_the_ranking_spread_clause": (
            None if calibration is None else bool(calibration["exceeds_percentile_value"])),
        "placebo_spread_clause": (
            None if placebo_calibration is None
            else bool(placebo_calibration["exceeds_percentile_value"]))}
    if non_additivity:
        homogeneity = commitments["homogeneity"]
        centred_homogeneity = (homogeneity - homogeneity.mean()).reshape(-1, 1)
        model = label_regression(counts, positions, values, clusters, n_positions=n_positions,
                                 extra=centred_homogeneity, extra_name="sum_c n_c^2 (centred)",
                                 team_size=team_size, n_labels=n_labels)
        model_calibration = permutation_calibration(
            counts, positions, values,
            permutation_generator(evaluation_seed, cap, response + "|homogeneity"),
            n_positions=n_positions,
            observed=None if model is None else model["extra"]["coefficient"],
            statistic="extra", homogeneity=True)
        block["non_additivity"] = {
            "homogeneity_mean": float(homogeneity.mean()),
            "homogeneity_min": float(homogeneity.min()) if homogeneity.size else None,
            "homogeneity_max": float(homogeneity.max()) if homogeneity.size else None,
            "model": model, "permutation": model_calibration,
            "definition": SOURCE_NOTES["non_additivity"]}
        if agent is not None:
            predictions = {label: float(agent["all_equal_prediction"][str(label)])
                           for label in range(n_labels)}
            spread = b11.spread_of(predictions)
            block["all_equal_prediction"] = {
                "response": response,
                "prediction_by_label": {str(label): predictions[label]
                                        for label in range(n_labels)},
                "max_minus_min": None if spread is None else spread["max_minus_min"],
                "best_label": None if spread is None else spread["best_label"],
                "is_a_mean_reward_per_step": response == UNDISCOUNTED,
                "reporting_factor": float(reporting_factor),
                "episode_J_by_label": (
                    {str(label): float(predictions[label]) * float(commitments["n_agents"])
                     for label in range(n_labels)} if response == UNDISCOUNTED else None),
                "episode_J_max_minus_min": (
                    None if spread is None or response != UNDISCOUNTED
                    else float(spread["max_minus_min"]) * float(commitments["n_agents"])),
                "conversion": SOURCE_NOTES["reporting_factor"],
                "definition": SOURCE_NOTES["non_additivity"]}
    return block


def behaviour_block(returns, *, horizon, n_uavs):
    """Does behaviour quality itself change with the cap at fixed weights? The episode returns."""
    returns = np.asarray(returns, dtype=np.float64)
    if returns.size == 0:
        return None
    native = float(n_uavs) * returns / float(horizon)
    return {
        "lane_episodes": int(returns.size),
        "mean_episode_return_U": float(returns.mean()),
        "clustered_se_episode_return_U": b11._se(returns),
        "mean_episode_J": float(native.mean()),
        "clustered_se_episode_J": b11._se(native),
        "mean_reward_per_step": float(returns.mean()) / float(horizon),
        "definition": (
            "one lane-episode is one cluster - the whole episode of one collection lane - so the "
            "standard error over the lane-episodes is already the clustered one. J is the runner's "
            "own native score of the same return. " + SOURCE_NOTES["reporting_factor"])}


def cap_measures(cap, frames, commitments, returns, *, evaluation_seed, horizon, lanes,
                 lambda_h, n_uavs, wall_seconds, n_labels=N_LABELS):
    """Every measure of one cap: the two responses, the label law, the behaviour and the secondary."""
    n_positions = int(commitments["position"].max()) + 1 if commitments["position"].size else 0
    pooled_agent = {column: np.concatenate([frame["agent"][column] for frame in frames])
                    for column in ("rollout", "lane", "step", "agent", "label", "advantage",
                                   "standardised_advantage", "return", "value", "reward",
                                   "elapsed", "old_log_prob")}
    pooled_team = {column: np.concatenate([frame["team"][column] for frame in frames])
                   for column in ("rollout", "lane", "step", "label", "advantage",
                                  "standardised_advantage", "return", "value", "reward",
                                  "elapsed", "old_log_prob")}
    agent_clusters = b11.clusters_of(pooled_agent)
    agent_table = b11.label_table(pooled_agent, agent_clusters, n_labels=n_labels)
    agent_order, agent_values = b11.ranking_of(agent_table, "mean_advantage")
    law = b11.law_summary(pooled_agent, pooled_team, n_labels=n_labels)
    reporting_factor = float(n_uavs) / float(horizon)
    responses = {
        response: response_block(
            commitments, response, evaluation_seed=evaluation_seed, cap=cap,
            n_positions=n_positions, reporting_factor=reporting_factor,
            non_additivity=(int(cap) == NON_ADDITIVITY_CAP), n_labels=n_labels)
        for response in RESPONSES}
    agreement = float(np.max(np.abs(commitments[DISCOUNTED]
                                    - commitments["discounted_from_tape"]))) \
        if commitments[DISCOUNTED].size else None
    return {
        "cap": int(cap),
        "rollouts": len(frames),
        "lane_episodes": len(frames) * int(lanes),
        "commitments": int(commitments["position"].size),
        "commitments_per_lane_episode": n_positions,
        "expected_team_rows_per_rollout": expected_team_rows(lanes, horizon, cap),
        "team_rows": int(pooled_team["label"].size),
        "agent_rows": int(pooled_agent["label"].size),
        "clusters": int(np.unique(agent_clusters).size),
        "positions": n_positions,
        "mean_commitment_elapsed": b11._mean(commitments["elapsed"]),
        "responses": responses,
        "behaviour": behaviour_block(returns, horizon=horizon, n_uavs=n_uavs),
        "label_law": law,
        "secondary_agent_advantage": {
            "agent_label_table": agent_table,
            "agent_label_ranking": agent_order,
            "agent_label_mean_advantage": {str(label): agent_values.get(label)
                                           for label in range(n_labels)},
            "agent_label_spread": b11.spread_of(agent_values),
            "agent_advantage_eta_squared": b11.eta_squared(
                pooled_agent["advantage"], pooled_agent["label"], n_labels),
            "entropy_coefficient_lambda_h": float(lambda_h),
            "reading_note": SOURCE_NOTES["secondary_advantage_table"]},
        "discounted_reward_agreement": {
            "max_absolute_difference": agreement,
            "tolerance": DISCOUNTED_AGREEMENT_TOLERANCE,
            "definition": ("the buffer's own discounted segment reward against the same sum "
                           "recomputed from the taped per-step rewards; the buffer stores a float64 "
                           "accumulation in float32. " + SOURCE_NOTES["per_step_reward"])},
        "wall_seconds": float(wall_seconds),
        "definitions": {
            "caps": SOURCE_NOTES["cap_attributes"],
            "geometry": SOURCE_NOTES["expected_geometry"],
            "responses": SOURCE_NOTES["responses"],
            "clustered_se": SOURCE_NOTES["lane_cluster"],
            "secondary": SOURCE_NOTES["secondary_advantage_table"]}}


def check_cap_geometry(cap, row, frame, commitments, *, lanes, horizon):
    """One collected rollout's geometry against the cadence the cap implies; refused here."""
    metrics = row.get("d2_metrics") or {}
    causes = dict(metrics.get("cause_counts") or {})
    expected_team = expected_team_rows(lanes, horizon, cap)
    record = {
        "cap": int(cap), "rollout_index": row.get("rollout_index"),
        "rows_M": frame["rows_M"], "rows_M_agent": frame["rows_M_agent"],
        "rows_M_team": frame["rows_M_team"],
        "expected_rows_M_team": expected_team,
        "expected_rows_M_agent": expected_team * int(commitments["n_agents"]),
        "flushed_open_segments": frame["flushed_open_segments"],
        "cause_counts": causes,
        "segment_length_agent_mean": metrics.get("segment_length_agent_mean"),
        "segment_length_team_mean": metrics.get("segment_length_team_mean"),
        "commitments_per_lane_episode": int(commitments["position"].max()) + 1,
        "mean_commitment_elapsed": b11._mean(commitments["elapsed"]),
        # the definition is published once per cap, on `measures[cap]["definitions"]["geometry"]`,
        # rather than on all sixty-four of these records
        "definition": "source_notes.expected_geometry"}
    unexpected = {name: int(count) for name, count in causes.items()
                  if name not in CAUSES_EXPECTED and int(count)}
    if unexpected:
        raise ValueError(f"the collection fired unexpected D2 decision causes: {unexpected}")
    if int(metrics.get("rows_M", -1)) != frame["rows_M"]:
        raise ValueError("the agent's own rows_M and the probe's disagree")
    if frame["rows_M_team"] != expected_team or frame["rows_M"] != expected_team:
        raise ValueError(
            f"cap {int(cap)} produced {frame['rows_M_team']} team rows, not the "
            f"{expected_team} its cadence implies")
    if frame["rows_M_agent"] != expected_team * int(commitments["n_agents"]):
        raise ValueError("the six agent segments do not renew with the team commitment")
    if int(causes.get("reset", 0)) != int(lanes):
        raise ValueError("the collection did not reset every lane exactly once")
    if int(causes.get("team_cap", 0)) != expected_team - int(lanes):
        raise ValueError("the team cap did not fire at the cadence the cap implies")
    return record


# ---------------------------------------------------------------------------
# the probe
# ---------------------------------------------------------------------------


def run_probe(seed, weights, out, launch_sha=None, caps=CAPS, rollouts_per_cap=ROLLOUTS_PER_CAP):
    """One block: B11's construction and panel, then one collection per commitment cap, no update."""
    if seed not in BLOCKS:
        raise SystemExit("this object probes blocks 772803, 772903 and 773003")
    caps = tuple(int(cap) for cap in caps)
    if not caps or len(set(caps)) != len(caps):
        raise SystemExit("the commitment caps are a set of distinct positive step counts")
    if min(caps) < 1:
        raise SystemExit("a commitment cap is at least one step")
    if int(rollouts_per_cap) < 1:
        raise SystemExit("a cap needs at least one rollout")
    b08.bind()  # B08's own probe binding: the frozen runner's construction, this object's measures
    started = time.perf_counter()
    evaluation_seed = BLOCKS[seed]
    out.mkdir(parents=True, exist_ok=True)
    result = {
        "object_id": OBJECT_ID, "card": CARD, "command": "probe",
        "launch_sha": shared.e0._git("rev-parse", "HEAD"), "requested_launch_sha": launch_sha,
        "arm": SAVE_ARM, "block_seed": seed, "evaluation_seed": evaluation_seed,
        "weights": str(weights), "labels": N_LABELS,
        "caps": list(caps), "frozen_cap": FROZEN_CAP,
        "rollouts_per_cap": int(rollouts_per_cap),
        "responses": list(RESPONSES), "primary_response": PRIMARY_RESPONSE,
        "permutations": PERMUTATIONS, "permutation_percentile": PERMUTATION_PERCENTILE,
        "baseline_rule": BASELINE_RULE,
        "collection_seeds": {str(cap): {str(rollout): collection_seed(seed, cap, rollout)
                                        for rollout in range(int(rollouts_per_cap))}
                             for cap in caps},
        "collection_lane_base_seed": b11.world_base_seed(seed),
        "collection_lane_seeds": list(range(b11.world_base_seed(seed),
                                            b11.world_base_seed(seed) + shared.TRAIN_LANES)),
        "seed_derivation": SEED_DERIVATION,
        "construction_source": (
            f"{b08.OBJECT_ID} {SAVE_ARM} (the recorded stage-1 {b08.D_REFERENCE} construction) "
            f"through {b11.OBJECT_ID}'s own collection: the frozen baseline x interruption B01 "
            "runner with B08's identities bound, B08's saved final weights loaded, zero optimizer "
            "steps; one `as_trained` panel and one training-law collection per commitment cap"),
        "reference_object_ids": [b11.OBJECT_ID, b10.OBJECT_ID, b09.OBJECT_ID, b08.OBJECT_ID],
        "recorded_d1280_summary": str(b08.RECORDED_FITS[seed]),
        "reference_summary": str(b08.REFERENCE_FITS[seed]),
        "host_geometry": b08.host_geometry(),
        "frozen_host_geometry": b08.host_geometry() == b08.probe.FROZEN_GEOMETRY,
        "frozen_collector_source": b11.frozen_collector_source(),
        "source_notes": dict(SOURCE_NOTES),
        "status": "incomplete", "failure": None, "faithful_load": None}
    construction = out / "construction"
    try:
        _run(result, seed, evaluation_seed, construction, Path(weights), caps,
             int(rollouts_per_cap))
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
        "caps": result.get("caps"), "rollouts_per_cap": result.get("rollouts_per_cap"),
        "spread_by_cap": {
            str(cap): ((((measures.get(str(cap)) or {}).get("responses") or {})
                        .get(PRIMARY_RESPONSE) or {}).get("agent_label_regression") or {}
                       ).get("max_minus_min") for cap in result.get("caps") or ()},
        "permutation_95th_by_cap": {
            str(cap): ((((measures.get(str(cap)) or {}).get("responses") or {})
                        .get(PRIMARY_RESPONSE) or {}).get("agent_label_permutation") or {}
                       ).get("percentile_value") for cap in result.get("caps") or ()},
        "optimizer_steps": result.get("optimizer_steps"),
        "parameters_unchanged": (result.get("learner_state") or {}).get("unchanged"),
        "wall_seconds": result.get("wall_seconds")}))
    return 0 if result["status"] == "complete" else 1


def _run(result, seed, evaluation_seed, out, weights, caps, rollouts_per_cap):
    """B11's construction and panel, then one capped collection per cap, with nothing trained."""
    result["weights_record"] = b09.verify_weights(seed, weights)
    recorded, reason = b08.recorded_fit(seed)
    if recorded is None:
        raise ValueError(f"the recorded D1280 fit of block {seed} is unreadable: {reason}")
    reference, reference_summary, reference_path = b08.reference_panel(seed)
    result["reference"] = {
        "summary": str(reference_path), "object_id": reference_summary.get("object_id"),
        "factorial_arm": reference_summary.get("factorial_arm"),
        "panel_rollouts": int(reference["panel_rollouts"]),
        "launch_sha": reference_summary.get("launch_sha")}
    result["recorded_row_geometry"] = b11.recorded_row_geometry(recorded)

    summary = shared.base_summary(b08.ARMS[SAVE_ARM][0], training_seed=seed,
                                  evaluation_seed=evaluation_seed, object_id=OBJECT_ID,
                                  card=CARD, caps=None)
    summary.update(command="probe", factorial_arm=SAVE_ARM, block_seed=seed, rollouts=0,
                   panel_rollouts=[], panels=[],
                   coordinator_batch_size=b08.ARMS[SAVE_ARM][1], ordinary_wall_plan_seconds=None,
                   cost_law=("zero optimizer steps; one evaluation panel and "
                             f"{len(caps)} x {rollouts_per_cap} training-law rollouts with no "
                             "update"))
    out.mkdir(parents=True, exist_ok=True)
    envs, learner, _theta0, counters = b01.build_learner(SAVE_ARM, summary, out, seed)
    learner_differences = b08.require_recorded_construction(
        summary["learner_config"], recorded["learner_config"], "learner configuration")
    restore = b08.scale._forbid_optimizer_steps(learner)
    measures, geometry, rows, cap_frames = {}, [], [], {}
    try:
        learner.load_model(str(weights))  # the agent's own load routine
        learner.train(False)
        before = b11.learner_state_record(learner)
        result["learner_state"] = {"before": before, "after": None, "unchanged": None}
        evaluator = b01.build_evaluator(SAVE_ARM, summary, out, evaluation_seed)
        evaluation_differences = b08.require_recorded_construction(
            summary["evaluation_config"], recorded["evaluation_config"],
            "evaluation configuration")
        restore += b08.scale._forbid_optimizer_steps(evaluator.agent)
        config = learner.config
        if (int(config.n_z), int(config.n_Z)) != (N_LABELS, N_LABELS):
            raise ValueError(
                f"the construction carries n_z={int(config.n_z)}, n_Z={int(config.n_Z)}, not the "
                f"{N_LABELS} labels this object's tables are defined on")
        if bool(getattr(config, "use_obsnorm", False)) or bool(
                getattr(config, "use_statenorm", False)):
            raise ValueError(
                "this construction normalises observations or states, so a training-mode "
                "collection would move running statistics the probe promises not to move")
        if (int(getattr(config, "skill_cap_k_max", -1)), int(getattr(config, "team_cap_k_Z", -1))) \
                != tuple(int(value) for value in b08.ARM_CAPS):
            raise ValueError("the construction is not the frozen caps-10 fit's")
        result["construction_caps"] = {"d2_k_max": int(learner.d2_k_max),
                                       "d2_k_Z": int(learner.d2_k_Z),
                                       "skill_cap_k_max": int(config.skill_cap_k_max),
                                       "team_cap_k_Z": int(config.team_cap_k_Z),
                                       "interruption_cost_c": str(config.interruption_cost_c),
                                       "interruption_cost_c_Z": str(config.interruption_cost_c_Z),
                                       "age_feature": str(getattr(config, "age_feature", "off")),
                                       "definition": SOURCE_NOTES["cap_attributes"]}

        # (a) the frozen `as_trained` panel and the faithful-load check, exactly as B11 runs them.
        panel = b08.run_rule_panel(BASELINE_RULE, learner, evaluator, summary, out, 0,
                                   evaluation_seed=evaluation_seed)
        result["rules_measured"] = {BASELINE_RULE: panel}
        faithful = b09.faithful_load_record(summary["panels"][-1], reference)
        result["faithful_load"] = faithful
        if not faithful["faithful_load"]:
            raise ValueError(
                "the loaded weights do not reproduce the recorded panel; first differing world "
                f"index {faithful['first_differing_world']}")

        # (b) one training-law collection per commitment cap, with no update at all.
        lanes, horizon = shared.TRAIN_LANES, shared.HORIZON
        rng_before = b11.rng_digest()
        for cap in caps:
            cap_started = time.perf_counter()
            frames, commitments, returns, cap_geometry = [], [], [], []

            def measure(rollout, states, observations, _cap=cap, _frames=frames,
                        _commitments=commitments):
                frame = b11.rollout_frame(learner, horizon, states.copy(), observations.copy(),
                                          rollout, lanes)
                if frame["rows_M"] > int(config.coordinator_batch_size):
                    raise ValueError(
                        f"the rollout carries {frame['rows_M']} valid rows, more than the "
                        f"{int(config.coordinator_batch_size)} of one minibatch")
                taped = tape.rollout(rollout, horizon)
                commitment = commitment_frame(frame, taped, cap=_cap, gamma=float(config.gamma),
                                              horizon=horizon)
                _commitments.append(commitment)
                agreement = float(np.max(np.abs(commitment[DISCOUNTED]
                                                - commitment["discounted_from_tape"])))
                if agreement > DISCOUNTED_AGREEMENT_TOLERANCE:
                    raise ValueError(
                        "the buffer's discounted segment reward and the taped recomputation "
                        f"differ by {agreement}")
                return frame, {"commitment_cap": int(_cap), "rows_M": frame["rows_M"],
                               "rows_M_agent": frame["rows_M_agent"],
                               "rows_M_team": frame["rows_M_team"],
                               "flushed_open_segments": frame["flushed_open_segments"],
                               "commitments": int(commitment["position"].size),
                               "discounted_reward_agreement": agreement,
                               "standardisation": frame["standardisation"],
                               "coordinator_bootstrap": frame["bootstrap"]}

            def check(rollout, row, frame, _cap=cap, _commitments=commitments,
                      _geometry=cap_geometry, _returns=returns):
                _geometry.append(check_cap_geometry(_cap, row, frame, _commitments[rollout],
                                                    lanes=lanes, horizon=horizon))
                _returns.append(list(row["episode_returns_U"]))
                rows.append({key: row.get(key) for key in
                             ("commitment_cap", "rollout_index", "collection_seed", "transitions",
                              "completed_episodes", "episode_returns_U", "rows_M", "rows_M_agent",
                              "rows_M_team", "commitments", "discounted_reward_agreement",
                              "flushed_open_segments", "standardisation", "segments",
                              "optimizer_calls_total")})

            with shared.e0._preserve_rng():  # the collection cannot move any other stream
                collection_envs = shared.e0._make_envs(
                    lanes, b11.world_base_seed(seed), shared.N_UAVS, shared.N_USERS, horizon)
                tape = RewardTape(collection_envs)
                with commitment_cap(learner, cap), b11_collection_seed_bound(cap), tape.attached():
                    frames.extend(b11.collect_training_law(
                        collection_envs, learner, summary, out, rollouts=rollouts_per_cap,
                        training_seed=seed, measure=measure, counters=counters, check=check))
                tape.require_shape(rollouts_per_cap, horizon)
            if (int(learner.d2_k_max), int(learner.d2_k_Z)) != tuple(
                    int(value) for value in b08.ARM_CAPS):
                raise ValueError("the cap was not restored after the collection")
            geometry.extend(cap_geometry)
            cap_frames[int(cap)] = len(frames)
            measures[str(cap)] = cap_measures(
                cap, frames, stack_commitments(commitments),
                np.concatenate(returns) if returns else np.zeros(0),
                evaluation_seed=evaluation_seed, horizon=horizon, lanes=lanes,
                lambda_h=float(config.lambda_h), n_uavs=shared.N_UAVS,
                wall_seconds=time.perf_counter() - cap_started)
            shared.publish(out, summary, f"cap {int(cap)} measured")
        learner.train(False)
        rng_after = b11.rng_digest()
        result["collection_rng"] = {
            "digest_before": rng_before, "digest_after": rng_after,
            "restored": bool(rng_before == rng_after),
            "definition": (
                "every cap's collection - the lane construction, the rollouts and the credit "
                "arithmetic - runs inside `run_flexible_skill_duration_e0._preserve_rng`, so the "
                "Python, NumPy and torch streams leave it where they entered; the digests record "
                "it rather than asserting it. " + SEED_DERIVATION)}
        if not result["collection_rng"]["restored"]:
            raise ValueError("the collection did not restore the global random streams")
        after = b11.learner_state_record(learner)
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
    result.update({
        "optimizer_steps": steps, "optimizer_calls": learner_calls,
        "measures": measures,
        "rollouts_collected": {str(cap): int(count) for cap, count in cap_frames.items()},
        "collection_rows": rows, "collection_geometry": geometry,
        "collection_lanes": shared.TRAIN_LANES, "horizon": shared.HORIZON,
        "collection_transitions": summary["counts"]["training_transitions"],
        "collection_episodes": summary["counts"]["training_episodes"],
        "collection_agent_step_batches": summary["counts"]["training_agent_step_batches"],
        "collection_worlds": (
            f"the block's own sixteen lanes seeded {b11.world_base_seed(seed)}..."
            f"{b11.world_base_seed(seed) + shared.TRAIN_LANES - 1}, rebuilt once per cap; not the "
            "fit's training worlds"),
        "reporting_factor": float(shared.N_UAVS) / float(shared.HORIZON),
        "reporting_factor_note": SOURCE_NOTES["reporting_factor"],
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
            "note": ("the law the measured quantities would enter; this probe runs none of it. "
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
    caps = [int(cap) for cap in summary.get("caps") or []]
    measures = summary.get("measures") or {}
    if not caps or sorted(measures) != sorted(str(cap) for cap in caps):
        raise ValueError("the probe does not carry one measured block per declared cap")
    for cap in caps:
        block = measures[str(cap)]
        responses = block.get("responses") or {}
        for response in RESPONSES:
            regression = (responses.get(response) or {}).get("agent_label_regression")
            if not regression:
                raise ValueError(f"cap {cap} carries no {response} regression")
            if sorted(regression.get("centred_coefficients") or {}) != [
                    str(label) for label in range(N_LABELS)]:
                raise ValueError(f"cap {cap} does not carry a six-label coefficient table")
            if not (responses.get(response) or {}).get("agent_label_permutation"):
                raise ValueError(f"cap {cap} carries no {response} permutation calibration")
        if int(block.get("rollouts", 0)) < 1:
            raise ValueError(f"cap {cap} carries no collected rollout")
    scores = summary.get("as_trained_world_scores")
    if not scores:
        raise ValueError("the probe carries no `as_trained` world scores")
    return {
        "block_seed": seed, "launch_sha": summary.get("launch_sha"),
        "weights_sha256": (summary.get("weights_record") or {}).get("sha256"),
        "faithful_load": True, "as_trained_world_scores": list(scores),
        "J_as_trained": float(summary.get("J_as_trained")),
        "caps": caps, "rollouts_per_cap": int(summary.get("rollouts_per_cap", 0)),
        "measures": measures,
        "reporting_factor": summary.get("reporting_factor"),
        "collection_geometry": summary.get("collection_geometry"),
        "update_law": summary.get("update_law"),
        "wall_seconds": summary.get("wall_seconds")}


def b10_sampled_spread(b10_row):
    """B10's measured sampled constant-label spread in J: max minus min of its own label map."""
    values = [float(value) for value in b10_row["sampled_J_by_label"].values()]
    return float(max(values) - min(values)) if values else None


def cap_reading(cap, block, b09_row, b10_row):
    """One cap of one block: the criterion, the placebo and the rank agreement with B09 and B10."""
    responses = block.get("responses") or {}
    best_label = int(b09_row["best_mean_action_label"])
    mean_action = dict(b09_row["mean_action_J_by_label"])
    sampled = dict(b10_row["sampled_J_by_label"])
    reading = {"cap": int(cap), "rollouts": block.get("rollouts"),
               "lane_episodes": block.get("lane_episodes"),
               "commitments": block.get("commitments"),
               "commitments_per_lane_episode": block.get("commitments_per_lane_episode"),
               "clusters": block.get("clusters"),
               "mean_commitment_elapsed": block.get("mean_commitment_elapsed"),
               "behaviour": block.get("behaviour"),
               "label_law_entropy_estimate": (block.get("label_law") or {}).get(
                   "agent_label_entropy_estimate"),
               "best_mean_action_label": best_label,
               "wall_seconds": block.get("wall_seconds")}
    for response in RESPONSES:
        entry = responses.get(response) or {}
        regression = entry.get("agent_label_regression") or {}
        calibration = entry.get("agent_label_permutation") or {}
        placebo = entry.get("placebo_regression") or {}
        placebo_calibration = entry.get("placebo_permutation") or {}
        coefficients = {label: regression.get("centred_coefficients", {}).get(str(label))
                        for label in range(N_LABELS)}
        ranking = [int(label) for label in regression.get("ranking") or []]
        rank = b11.rank_of(ranking, best_label)
        spread_clause = (None if not calibration else
                         bool(calibration["exceeds_percentile_value"]))
        ranking_clause = None if rank is None else bool(rank <= 2)
        reading[response] = {
            "centred_coefficients": {str(label): coefficients[label]
                                     for label in range(N_LABELS)},
            "clustered_se": dict(regression.get("clustered_se") or {}),
            "ranking": ranking,
            "max_minus_min": regression.get("max_minus_min"),
            "max_minus_min_clustered_se": regression.get("max_minus_min_clustered_se"),
            "r_squared": regression.get("r_squared"),
            "residual_sd": regression.get("residual_sd"),
            "permutation_percentile_value": calibration.get("percentile_value"),
            "permutation_p_value": calibration.get("p_value"),
            "spread_exceeds_permutation_percentile": spread_clause,
            "best_mean_action_label_rank": rank,
            "best_mean_action_label_in_top_two": ranking_clause,
            "shows_the_ranking": (None if spread_clause is None or ranking_clause is None
                                  else bool(spread_clause and ranking_clause)),
            "placebo_max_minus_min": placebo.get("max_minus_min"),
            "placebo_permutation_percentile_value": placebo_calibration.get("percentile_value"),
            "placebo_permutation_p_value": placebo_calibration.get("p_value"),
            "placebo_passes_the_same_spread_test": (
                None if not placebo_calibration
                else bool(placebo_calibration["exceeds_percentile_value"])),
            "placebo_invalidates_this_reading": (
                None if not placebo_calibration
                else bool(placebo_calibration["exceeds_percentile_value"])),
            "rank_correlation_with_mean_action_b09": b11._spearman(
                b11._series(coefficients), b11._series(mean_action)),
            "rank_correlation_with_sampled_b10": b11._spearman(
                b11._series(coefficients), b11._series(sampled)),
            "criterion": (
                "the notebook's, declared before any score: the cap shows the ranking if the "
                "centred coefficient spread exceeds the 95th percentile of its own permutation "
                "spread *and* B09's best mean-action label is ranked first or second by the same "
                "coefficients. It is read on the undiscounted response; the discounted one is "
                "reported beside it. A placebo that passes the same spread test invalidates the "
                "cap's reading"),
            "drop_invariance": entry.get("centred_coefficient_drop_invariance")}
    non_additivity = (responses.get(PRIMARY_RESPONSE) or {}).get("non_additivity")
    prediction = (responses.get(PRIMARY_RESPONSE) or {}).get("all_equal_prediction")
    if non_additivity or prediction:
        model = (non_additivity or {}).get("model") or {}
        calibration = (non_additivity or {}).get("permutation") or {}
        sampled_spread = b10_sampled_spread(b10_row)
        predicted = None if prediction is None else prediction.get("episode_J_max_minus_min")
        reading["non_additivity"] = {
            "homogeneity_coefficient": (model.get("extra") or {}).get("coefficient"),
            "homogeneity_clustered_se": (model.get("extra") or {}).get("clustered_se"),
            "homogeneity_permutation_p_value": calibration.get("p_value"),
            "homogeneity_permutation_percentile_value": calibration.get("percentile_value"),
            "homogeneity_exceeds_permutation_percentile": (
                None if not calibration else bool(calibration["exceeds_percentile_value"])),
            "all_equal_prediction_episode_J": (None if prediction is None
                                               else prediction.get("episode_J_by_label")),
            "all_equal_prediction_J_max_minus_min": predicted,
            "b10_sampled_J_max_minus_min": sampled_spread,
            "prediction_fraction_of_b10_sampled_spread": (
                None if predicted is None or not sampled_spread
                else float(predicted / sampled_spread)),
            "prediction_below_half_of_b10_sampled_spread": (
                None if predicted is None or sampled_spread is None
                else bool(predicted < ALTERNATIVE_FRACTION * sampled_spread)),
            "definition": SOURCE_NOTES["non_additivity"]}
    return reading


def block_reading(row, b09_row, b10_row):
    """One block: every cap's reading, beside B09's mean-action map and B10's sampled map."""
    caps = [int(cap) for cap in row["caps"]]
    caps_read = {cap: cap_reading(cap, row["measures"][str(cap)], b09_row, b10_row)
                 for cap in caps}
    passing = [cap for cap in caps
               if caps_read[cap][PRIMARY_RESPONSE]["shows_the_ranking"]]
    placebo_flagged = [cap for cap in caps
                       if caps_read[cap][PRIMARY_RESPONSE]["placebo_invalidates_this_reading"]]
    return {
        "J_as_trained": row["J_as_trained"],
        "caps": caps, "rollouts_per_cap": row["rollouts_per_cap"],
        "by_cap": {str(cap): caps_read[cap] for cap in caps},
        "caps_showing_the_ranking": passing,
        "smallest_cap_showing_the_ranking": min(passing) if passing else None,
        "caps_with_a_passing_placebo": placebo_flagged,
        "placebo_flag": bool(placebo_flagged),
        "spread_by_cap": {str(cap): caps_read[cap][PRIMARY_RESPONSE]["max_minus_min"]
                          for cap in caps},
        "permutation_percentile_by_cap": {
            str(cap): caps_read[cap][PRIMARY_RESPONSE]["permutation_percentile_value"]
            for cap in caps},
        "permutation_p_value_by_cap": {
            str(cap): caps_read[cap][PRIMARY_RESPONSE]["permutation_p_value"] for cap in caps},
        "rank_correlation_with_sampled_b10_by_cap": {
            str(cap): caps_read[cap][PRIMARY_RESPONSE]["rank_correlation_with_sampled_b10"]
            for cap in caps},
        "rank_correlation_with_mean_action_b09_by_cap": {
            str(cap): caps_read[cap][PRIMARY_RESPONSE]["rank_correlation_with_mean_action_b09"]
            for cap in caps},
        "mean_episode_return_U_by_cap": {
            str(cap): (caps_read[cap]["behaviour"] or {}).get("mean_episode_return_U")
            for cap in caps},
        "mean_episode_J_by_cap": {
            str(cap): (caps_read[cap]["behaviour"] or {}).get("mean_episode_J") for cap in caps},
        "wall_seconds_by_cap": {str(cap): caps_read[cap]["wall_seconds"] for cap in caps},
        "mean_action_J_by_label": {str(label): b09_row["mean_action_J_by_label"][label]
                                   for label in range(N_LABELS)},
        "sampled_J_by_label": {str(label): b10_row["sampled_J_by_label"][label]
                               for label in range(N_LABELS)},
        "mean_action_ranking": [int(label) for label in b09_row["mean_action_ranking"]],
        "sampled_ranking": [int(label) for label in b10_row["sampled_ranking"]],
        "best_mean_action_label": int(b09_row["best_mean_action_label"]),
        "sampled_J_max_minus_min": b10_sampled_spread(b10_row),
        "coordinator_most_used_label": b09_row["coordinator_most_used_label"],
        "rank_correlation_definition": (
            "Spearman's rank correlation, ties sharing their average rank (B10's own function), "
            "between the six centred coefficients of one cap and the six labels' fixed-weight "
            "panel J - B09's mean-action map and B10's sampled map of the same checkpoint. Six "
            "paired points: a description of the order, not a test"),
        "weights_sha256": row["weights_sha256"]}


def prediction_rows(readings, caps):
    """The notebook's four declared predictions, counted where they are read.

    Arithmetic on the blocks that were read, with the statement each count belongs to. A count is
    not a weight of evidence, and none of these margins is a decision rule.
    """
    blocks = tuple(sorted(BLOCKS))
    smallest_expected = tuple(cap for cap in (50, 100) if cap in caps)
    declared = {
        "P1_cap_10_fails_the_criterion": {
            "blocks": blocks,
            "statement": ("cap 10 fails the criterion on 3/3: B11's reading again, at the frozen "
                          "cadence"),
            "value": lambda r: (None if "10" not in r["by_cap"] else
                                r["by_cap"]["10"][PRIMARY_RESPONSE]["shows_the_ranking"]),
            "holds": lambda value: not bool(value),
            "unread_when_none": True,
            "value_definition": ("`shows_the_ranking` at cap 10 on the undiscounted response; the "
                                 "prediction holds where it is False")},
        "P2_cap_500_passes_the_criterion": {
            "blocks": blocks,
            "statement": "cap 500 passes the criterion on 3/3",
            "value": lambda r: (None if "500" not in r["by_cap"] else
                                r["by_cap"]["500"][PRIMARY_RESPONSE]["shows_the_ranking"]),
            "holds": bool,
            "unread_when_none": True,
            "value_definition": "`shows_the_ranking` at cap 500 on the undiscounted response"},
        "P3_the_smallest_passing_cap_is_50_or_100": {
            "blocks": blocks,
            "statement": ("the smallest passing cap is 50 or 100 on at least 2/3 of the blocks"),
            "value": lambda r: r["smallest_cap_showing_the_ranking"],
            "holds": lambda value: value in smallest_expected,
            "value_definition": ("the smallest cap whose undiscounted reading passes both clauses "
                                 "of the criterion, or None where none does")},
        "ALTERNATIVE_the_map_is_joint_not_additive": {
            "blocks": blocks,
            "statement": ("the strongest alternative, on at least 2/3 of the blocks: cap 500 fails "
                          "the criterion *and* the additive model's all-equal predictions span less "
                          f"than {ALTERNATIVE_FRACTION} of B10's measured sampled constant-label "
                          "spread in J on that block"),
            "value": lambda r: {
                "cap_500_shows_the_ranking": (
                    None if "500" not in r["by_cap"] else
                    r["by_cap"]["500"][PRIMARY_RESPONSE]["shows_the_ranking"]),
                "prediction_below_half_of_b10_sampled_spread": (
                    ((r["by_cap"].get("500") or {}).get("non_additivity") or {})
                    .get("prediction_below_half_of_b10_sampled_spread")),
                "all_equal_prediction_J_max_minus_min": (
                    ((r["by_cap"].get("500") or {}).get("non_additivity") or {})
                    .get("all_equal_prediction_J_max_minus_min")),
                "b10_sampled_J_max_minus_min": r.get("sampled_J_max_minus_min")},
            "holds": lambda value: bool(
                value["cap_500_shows_the_ranking"] is False
                and value["prediction_below_half_of_b10_sampled_spread"]),
            "value_definition": ("cap 500's own criterion outcome beside the additive model's "
                                 "predicted all-equal episode-J spread and B10's measured sampled "
                                 "spread on the same block")},
        "PLACEBO_no_cap_has_a_passing_placebo": {
            "blocks": blocks,
            "statement": ("not a prediction but a validity check: no cap's team-label placebo "
                          "passes the same spread test. A block where one does has that cap's "
                          "reading invalidated"),
            "value": lambda r: r["caps_with_a_passing_placebo"],
            "holds": lambda value: not value,
            "value_definition": ("the caps whose placebo spread exceeds the 95th percentile of its "
                                 "own permutation distribution on the undiscounted response")},
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
            unread = value is None and entry.get("unread_when_none", False)
            per_block[str(seed)] = {"read": True, "value": value,
                                    "holds": None if unread else bool(entry["holds"](value))}
        rows[name] = {
            "statement": entry["statement"], "value_definition": entry["value_definition"],
            "blocks_considered": [int(seed) for seed in entry["blocks"]],
            "blocks_read": int(sum(row["read"] for row in per_block.values())),
            "blocks_holding": int(sum(bool(row["holds"]) for row in per_block.values())),
            "per_block": per_block}
    rows["counting_note"] = (
        "the counts are the arithmetic of statements declared before the run, on the blocks that "
        "were read. The criterion is the notebook's own and is read on the undiscounted response; "
        "the discounted response is reported beside it and is counted nowhere. A count of three "
        "blocks is not an interval and not a weight of evidence, and the permutation percentile is "
        "the notebook's declared reading rule, not a test of a model this design fits")
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
    b09_rows, b09_failures = read(b09_probes, b11.b09_probe_row, "B09")
    b10_rows, b10_failures = read(b10_probes, b11.b10_probe_row, "B10")
    cap_sets = {tuple(row["caps"]) for row in rows.values()}
    if len(cap_sets) > 1:
        raise ValueError(f"the probes do not carry one set of caps: {sorted(cap_sets)}")
    caps = list(next(iter(cap_sets))) if cap_sets else list(CAPS)

    blocks, readings = [], {}
    for seed in sorted(BLOCKS):
        entry = {"training_seed": seed, "evaluation_seed": BLOCKS[seed], "status": "incomplete",
                 "missing_or_invalid": {}}
        for name, source, failed in (("probe", rows, failures),
                                     ("b09_probe", b09_rows, b09_failures),
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
        "reference_object_ids": [b11.OBJECT_ID, b10.OBJECT_ID, b09.OBJECT_ID, b08.OBJECT_ID],
        "status": "complete" if len(complete) == len(BLOCKS) else "incomplete",
        "arm": {"name": SAVE_ARM, "overrides": dict(b08.ARM_OVERRIDES[SAVE_ARM]),
                "coordinator_batch_size": b08.ARMS[SAVE_ARM][1],
                "frozen_caps": {"skill_cap_k_max": b08.ARM_CAPS[0],
                                "team_cap_k_Z": b08.ARM_CAPS[1]}},
        "labels": N_LABELS, "caps": caps, "primary_response": PRIMARY_RESPONSE,
        "responses": list(RESPONSES),
        "rollouts_per_cap": {str(block["training_seed"]): block.get("rollouts_per_cap")
                             for block in blocks},
        "quantity": (
            "a commitment is one closed team segment of the D2 route; its two responses are the "
            "frozen discounted credit quantity and the undiscounted mean reward per step over the "
            "same steps. A cap's coefficient for a label is the least-squares effect of one more "
            "agent holding that label in a commitment, with a fixed effect per commitment position "
            "and the six coefficients centred to mean zero, and its calibration is the permutation "
            "distribution of the same statistic under label vectors reshuffled among commitments at "
            "the same position. B09's mean-action J and B10's sampled J are those objects' own "
            "fixed-weight panels of the same checkpoint, so every comparison is within one block, "
            "one checkpoint and one set of weights - but the coefficients are collected on this "
            "object's own sixteen worlds and the panels on the block's 32 evaluation worlds, so the "
            "pairing is the checkpoint, not the world"),
        "blocks": blocks,
        "blocks_read": len(complete),
        "invalid_probes": {str(seed): text for seed, text in failures.items()},
        "invalid_b09_probes": {str(seed): text for seed, text in b09_failures.items()},
        "invalid_b10_probes": {str(seed): text for seed, text in b10_failures.items()},
        "refusals": (
            "a batch of this object's probes at more than one launch sha or with different cap "
            "sets, a duplicate block among any of the three sets, a summary that is not this "
            "object's probe, an incomplete probe, a probe that took an optimizer step or does not "
            "record unchanged parameters and value normalisers, a probe without a six-label "
            "coefficient table or a permutation calibration for both responses at every declared "
            "cap, a probe that did not establish a faithful load, a block whose B09 or B10 probe "
            "was not supplied or is not readable by that object's own reader, a block whose weights "
            "sha256 is not B09's and B10's, and a block whose `as_trained` world scores are not "
            "exactly theirs"),
        "interpretation_limit": INTERPRETATION_LIMIT,
        "source_notes": dict(SOURCE_NOTES),
    }
    result["caps_showing_the_ranking_by_block"] = {
        str(block["training_seed"]): block.get("caps_showing_the_ranking") for block in blocks}
    result["smallest_cap_showing_the_ranking_by_block"] = {
        str(block["training_seed"]): block.get("smallest_cap_showing_the_ranking")
        for block in blocks}
    result["placebo_flag_by_block"] = {
        str(block["training_seed"]): block.get("placebo_flag") for block in blocks}
    result["blocks_showing_the_ranking_by_cap"] = {
        str(cap): [int(block["training_seed"]) for block in complete
                   if cap in (block.get("caps_showing_the_ranking") or [])]
        for cap in caps}
    for key, read in (
            ("spread_by_cap", lambda b, cap: b["spread_by_cap"].get(str(cap))),
            ("permutation_percentile_by_cap",
             lambda b, cap: b["permutation_percentile_by_cap"].get(str(cap))),
            ("permutation_p_value_by_cap",
             lambda b, cap: b["permutation_p_value_by_cap"].get(str(cap))),
            ("rank_correlation_with_sampled_b10_by_cap",
             lambda b, cap: b["rank_correlation_with_sampled_b10_by_cap"].get(str(cap))),
            ("rank_correlation_with_mean_action_b09_by_cap",
             lambda b, cap: b["rank_correlation_with_mean_action_b09_by_cap"].get(str(cap))),
            ("mean_episode_return_U_by_cap",
             lambda b, cap: b["mean_episode_return_U_by_cap"].get(str(cap))),
            ("mean_episode_J_by_cap", lambda b, cap: b["mean_episode_J_by_cap"].get(str(cap))),
            ("wall_seconds_by_cap", lambda b, cap: b["wall_seconds_by_cap"].get(str(cap)))):
        result[key] = {str(cap): across(complete, lambda b, cap=cap, read=read: read(b, cap))
                       for cap in caps}
    result["centred_coefficients_by_cap"] = {
        str(cap): {str(label): across(
            complete,
            lambda b, cap=cap, label=label: (b["by_cap"][str(cap)][PRIMARY_RESPONSE]
                                             ["centred_coefficients"].get(str(label))))
            for label in range(N_LABELS)} for cap in caps}
    result["ranking_by_block_and_cap"] = {
        str(block["training_seed"]): {
            str(cap): ((block.get("by_cap") or {}).get(str(cap)) or {}).get(
                PRIMARY_RESPONSE, {}).get("ranking") for cap in caps}
        for block in blocks}
    result["reference_rankings_by_block"] = {
        str(block["training_seed"]): {
            "mean_action_b09": block.get("mean_action_ranking"),
            "sampled_b10": block.get("sampled_ranking"),
            "best_mean_action_label": block.get("best_mean_action_label")}
        for block in blocks}
    result["non_additivity_by_block"] = {
        str(block["training_seed"]): (
            ((block.get("by_cap") or {}).get(str(NON_ADDITIVITY_CAP)) or {}).get("non_additivity"))
        for block in blocks}
    result["predictions"] = prediction_rows(readings, caps)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prb = sub.add_parser("probe", help="zero-update capped training-law collections at saved weights")
    prb.add_argument("--seed", type=int, choices=tuple(BLOCKS), required=True)
    prb.add_argument("--weights", type=Path, required=True,
                     help=f"B08's fit {WEIGHTS_NAME}; its {SIDECAR_NAME} must sit beside it")
    prb.add_argument("--launch-sha", required=True, help="must equal the source HEAD; recorded")
    prb.add_argument("--output-root", type=Path, required=True)
    prb.add_argument("--caps", type=int, nargs="+", default=list(CAPS),
                     help="the commitment caps, in the order they are collected (default 10 50 100 500)")
    prb.add_argument("--rollouts-per-cap", type=int, default=ROLLOUTS_PER_CAP,
                     help="training-law rollouts per cap, with no update (default 16)")
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
                         launch_sha=args.launch_sha, caps=tuple(args.caps),
                         rollouts_per_cap=args.rollouts_per_cap)

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
        "spread_by_cap": {cap: (value or {}).get("mean")
                          for cap, value in result["spread_by_cap"].items()},
        "permutation_percentile_by_cap": {
            cap: (value or {}).get("mean")
            for cap, value in result["permutation_percentile_by_cap"].items()},
        "blocks_showing_the_ranking_by_cap": result["blocks_showing_the_ranking_by_cap"],
        "smallest_cap_showing_the_ranking_by_block": result[
            "smallest_cap_showing_the_ranking_by_block"],
        "placebo_flag_by_block": result["placebo_flag_by_block"],
        "predictions": {name: entry["blocks_holding"] for name, entry in
                        result["predictions"].items() if isinstance(entry, dict)
                        and "blocks_holding" in entry}}))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
