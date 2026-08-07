"""Exposure stratification of the loop-3 registered comparisons (Pro guard A).

External Pro's ruling on revision ``7accc4c8`` (terminal
``MSSR_CHANGE_F_POSTCOMMIT_MATCHED_PAIR_REQUIRED``) named the UNSTRATIFIED
full-match aggregate the LARGEST interpretive risk of the loop-3 result: the 316
full ``Z_not_P`` reconvergences mix pre-perturbation opportunities, exposed and
unexposed post-perturbation opportunities, and genuine post-exposure
reconvergences, and only the exposed cases inform whether the two observation
folds (P and ``high_hidden``) forget together.  Pro directed stratification "by
the target's PartnerInteractionRow provenance" with the flags::

    pre_perturbation | post_perturbation_but_target_unexposed |
    target_exposed_with_equal_payload | target_exposed_with_different_payload |
    post_exposure_environment_reconverged | post_exposure_full_non_P_reconverged

This module computes that stratification MECHANICALLY over the loop-3
registered budget (``history_reconvergence_search.registered_designs``).  It
re-runs the registered search, collects the target's pre-token
partner-interaction row trajectory in both arms of every design, and classifies
every compared opportunity.  The classification RULE is registered below
(see ``classify``); the READING of the strata belongs to External Pro.  This
module licenses no scientific or value claim.

Registered operationalization (stated so Pro can correct it):

* ``pre_perturbation`` -- the opportunity's physical time is <= the design's
  single flip step.  The opportunity read precedes the flipped primitive (the
  flip at step ``s`` alters the primitive taken AFTER the event at time ``s``),
  so such opportunities cannot carry any perturbation effect.
* Rows are compared POSITIONALLY in append order across arms (the two arms
  share the scripted frontier skeleton, hence the same write occasions;
  ``event_index`` repeats across events and is not a key), exactly the loop-4
  ``exposure_positive`` predicate: a length mismatch or any aligned pair
  differing in partner or payload is a differing exposure.
* ``target_exposed_with_different_payload`` -- rows differ at the compared
  opportunity: a prior differing partner write actually reached the target's
  history.  Refined by the loop-3 digest flags of the SAME comparison:
  ``post_exposure_environment_reconverged`` iff the minus-``high_hidden`` digest
  matched, ``post_exposure_full_non_P_reconverged`` iff the full digest matched.
* ``target_exposed_with_equal_payload`` -- rows are byte-equal at the compared
  opportunity but at least one row was WRITTEN after the flip (visible at the
  compared time): a post-flip write occurred and recorded an equal partner and
  payload, i.e. the flip never moved what the write recorded.
* ``post_perturbation_but_target_unexposed`` -- rows are byte-equal and no row
  was written after the flip: no write occasion has sampled the perturbation
  window yet.

The four primary flags partition every compared opportunity; the two
``post_exposure_*`` flags are refinements of the exposed-with-different-payload
class.  "Written after the flip" is computed from the row-count trajectory:
rows visible at the compared time ``t`` minus rows visible at the FIRST
snapshot time strictly after the flip step (rows only grow at the target's own
tokens, and every write at a snapshot time <= flip step precedes the flip).
"""

from __future__ import annotations

import functools
from typing import Mapping, Sequence

from experiments.candidates.vsp_06_mssr.history_reconvergence_search import (
    Design,
    OpportunityComparison,
    Tape,
    _partner_flip_primitive,
    BASE_FAMILY_BY_NAME,
    make_core,
    make_environment,
    registered_designs,
    run_search,
)
from experiments.candidates.vsp_06_mssr.d1_change_f_matched_pair import (
    ACTIVE,
    _drive,
    exposure_positive,
)

RAW_OUTPUT_BINDING = "vsp_06_mssr.exposure_stratification.v1"

# --- Pro's registered flag vocabulary (verbatim from the 7accc4c8 ruling). ----
EXPOSURE_PRE_PERTURBATION = "pre_perturbation"
EXPOSURE_POST_PERTURBATION_TARGET_UNEXPOSED = (
    "post_perturbation_but_target_unexposed"
)
EXPOSURE_TARGET_EXPOSED_EQUAL_PAYLOAD = "target_exposed_with_equal_payload"
EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD = (
    "target_exposed_with_different_payload"
)
PRIMARY_CLASSES = (
    EXPOSURE_PRE_PERTURBATION,
    EXPOSURE_POST_PERTURBATION_TARGET_UNEXPOSED,
    EXPOSURE_TARGET_EXPOSED_EQUAL_PAYLOAD,
    EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD,
)

#: Pro's loop-4 C5 naming correction: ``target_exposed_with_equal_payload``
#: proves only a post-flip WRITE OCCASION with an equal record -- it does NOT
#: prove the perturbation reached the target's P source.  The flag string is
#: kept (frozen vocabulary of the 7accc4c8 ruling) but its corrected semantics
#: travel with every report; these cases are CONTROLS, not P-exposure cases.
EQUAL_PAYLOAD_CORRECTED_NAME = "post_flip_target_write_with_equal_record"

# --- Differ-kind decomposition of the row-different class (Pro loop-4 C5). ---
DIFFER_KIND_PARTNER_IDENTITY_ONLY = "partner_identity_only"
DIFFER_KIND_PAYLOAD_SEQUENCE = "payload_sequence_different"
DIFFER_KIND_ROW_COUNT = "row_count_or_write_occasion_different"
DIFFER_KINDS = (
    DIFFER_KIND_PARTNER_IDENTITY_ONLY,
    DIFFER_KIND_PAYLOAD_SEQUENCE,
    DIFFER_KIND_ROW_COUNT,
)
P_SUBCLASS_STILL_DIFFERENT = "current_P_still_different"
P_SUBCLASS_NEVER_CHANGED = "payload_difference_never_changed_current_P"
P_SUBCLASS_DECAYED = "payload_difference_changed_P_then_decayed_to_exact_equality"
P_SUBCLASS_CANCELLED = "multiple_payload_differences_cancelled_in_the_EMA"
P_SUBCLASSES = (
    P_SUBCLASS_STILL_DIFFERENT,
    P_SUBCLASS_NEVER_CHANGED,
    P_SUBCLASS_DECAYED,
    P_SUBCLASS_CANCELLED,
)


def collect_history_trajectory(tape: Tape, target_key: str) -> dict[int, dict]:
    """The target's PRE-TOKEN partner-interaction state at every event time.

    A read-only preframe (fires once per ``apply_transaction`` after membership
    commit, before the frontier loop) snapshots the target's accumulated rows
    AND the retained scalar ``current_p``.  The target's rows are owner-private
    and grow ONLY at the target's own token, so the post-commit pre-frontier
    snapshot equals the pre-token snapshot at every event, including
    non-opportunity events (harmless extras).  Returns
    ``{physical_time: {"rows": ((event_index, partner_lifecycle_key, payload),
    ...), "current_p": float}}`` for every event time at which the target holds
    an ACTIVE record (``current_p`` is 0.0 while the history object is absent,
    matching the loop-3 ``current_p`` reader).
    """
    core = make_core(tape.episode_id)
    env = make_environment()
    target = str(target_key)
    trajectory: dict[int, dict] = {}

    def reader(c) -> None:
        record = c.records.get(target)
        if record is None or record.status != ACTIVE:
            return
        history = record.partner_interaction_history
        rows = (
            ()
            if history is None
            else tuple(
                (int(row.event_index), str(row.partner_lifecycle_key), float(row.payload))
                for row in history.rows
            )
        )
        trajectory[int(c.physical_time)] = {
            "rows": rows,
            "current_p": 0.0 if history is None else float(history.current_p),
        }

    _drive(core, env, tape, preframe=reader, sink=None)
    return trajectory


def collect_row_trajectory(
    tape: Tape, target_key: str
) -> dict[int, tuple[tuple[int, str, float], ...]]:
    """Rows-only view of ``collect_history_trajectory`` (kept for the frozen
    classification interface; same rollout, same snapshot semantics)."""
    return {
        time: snapshot["rows"]
        for time, snapshot in collect_history_trajectory(tape, target_key).items()
    }


def classify(
    comparison: OpportunityComparison,
    base_trajectory: Mapping[int, tuple],
    perturbed_trajectory: Mapping[int, tuple],
) -> dict:
    """Classify ONE compared opportunity by the registered exposure rule."""
    if len(comparison.window) != 1:
        raise ValueError(
            "the registered exposure rule is defined for single-step flip windows"
        )
    flip_step = int(comparison.window[0])
    time = int(comparison.physical_time)

    if time <= flip_step:
        primary = EXPOSURE_PRE_PERTURBATION
        rows_differ = False
        post_flip_write_count = 0
    else:
        base_rows = tuple(base_trajectory.get(time, ()))
        perturbed_rows = tuple(perturbed_trajectory.get(time, ()))
        rows_differ = exposure_positive(base_rows, perturbed_rows)
        post_flip_times = sorted(t for t in base_trajectory if t > flip_step)
        if post_flip_times:
            anchor_rows = base_trajectory[post_flip_times[0]]
            post_flip_write_count = max(0, len(base_rows) - len(anchor_rows))
        else:
            post_flip_write_count = 0
        if rows_differ:
            primary = EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD
        elif post_flip_write_count > 0:
            primary = EXPOSURE_TARGET_EXPOSED_EQUAL_PAYLOAD
        else:
            primary = EXPOSURE_POST_PERTURBATION_TARGET_UNEXPOSED

    exposed_different = primary == EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD
    return {
        "primary": primary,
        "rows_differ": bool(rows_differ),
        "post_flip_write_count": int(post_flip_write_count),
        "post_exposure_environment_reconverged": bool(
            exposed_different and comparison.znp_minus_hidden_match
        ),
        "post_exposure_full_non_p_reconverged": bool(
            exposed_different and comparison.znp_full_match
        ),
    }


def decompose_row_different(
    comparison: OpportunityComparison,
    base_history: Mapping[int, dict],
    perturbed_history: Mapping[int, dict],
) -> dict:
    """Differ-kind decomposition of ONE row-different comparison (Pro C5).

    Registered rule (mechanical; the READING belongs to Pro):

    * ``row_count_or_write_occasion_different`` -- the two arms' row counts at
      the compared time differ (a write occasion itself moved).
    * ``payload_sequence_different`` -- equal counts, and >=1 positionally
      aligned row differs in PAYLOAD (the quantity the P update consumes;
      partner identity may also differ).
    * ``partner_identity_only`` -- equal counts, all aligned payloads equal,
      >=1 aligned row differs in partner identity alone.  The current P update
      uses payload, not partner identity, so this is NOT a differing scalar-P
      exposure.

    For ``payload_sequence_different`` (the P-effective kind) the retained-P
    consequence is subclassified from the measured pre-token ``current_p``
    trajectories at the event times both arms share, up to the compared time:

    * ``current_P_still_different`` -- P differs at the compared time;
    * ``payload_difference_never_changed_current_P`` -- P byte-equal at every
      shared time;
    * ``..._changed_P_then_decayed_to_exact_equality`` -- P differed at some
      earlier shared time, is equal at the compared time, and exactly ONE
      aligned payload position differs;
    * ``multiple_payload_differences_cancelled_in_the_EMA`` -- as above but
      with >=2 differing aligned payload positions.
    """
    if len(comparison.window) != 1:
        raise ValueError(
            "the registered exposure rule is defined for single-step flip windows"
        )
    time = int(comparison.physical_time)
    base_rows = tuple(base_history[time]["rows"])
    perturbed_rows = tuple(perturbed_history[time]["rows"])
    row_count_differs = len(base_rows) != len(perturbed_rows)
    payload_diff_positions = [
        index
        for index, (base_row, pert_row) in enumerate(zip(base_rows, perturbed_rows))
        if base_row[2] != pert_row[2]
    ]
    partner_diff_positions = [
        index
        for index, (base_row, pert_row) in enumerate(zip(base_rows, perturbed_rows))
        if base_row[1] != pert_row[1]
    ]
    if row_count_differs:
        differ_kind = DIFFER_KIND_ROW_COUNT
    elif payload_diff_positions:
        differ_kind = DIFFER_KIND_PAYLOAD_SEQUENCE
    elif partner_diff_positions:
        differ_kind = DIFFER_KIND_PARTNER_IDENTITY_ONLY
    else:
        raise ValueError("comparison is not row-different at the compared time")

    shared_times = sorted(
        t for t in base_history if t in perturbed_history and t <= time
    )
    p_pairs = [
        (
            float(base_history[t]["current_p"]),
            float(perturbed_history[t]["current_p"]),
        )
        for t in shared_times
    ]
    p_ever_differed = any(left != right for left, right in p_pairs)
    p_equal_now = (
        float(base_history[time]["current_p"])
        == float(perturbed_history[time]["current_p"])
    )
    p_subclass = None
    if differ_kind == DIFFER_KIND_PAYLOAD_SEQUENCE:
        if not p_equal_now:
            p_subclass = P_SUBCLASS_STILL_DIFFERENT
        elif not p_ever_differed:
            p_subclass = P_SUBCLASS_NEVER_CHANGED
        elif len(payload_diff_positions) == 1:
            p_subclass = P_SUBCLASS_DECAYED
        else:
            p_subclass = P_SUBCLASS_CANCELLED
    return {
        "differ_kind": differ_kind,
        "p_subclass": p_subclass,
        "row_count_differs": bool(row_count_differs),
        "payload_diff_position_count": len(payload_diff_positions),
        "partner_diff_position_count": len(partner_diff_positions),
        "p_ever_differed_pre_comparison": bool(p_ever_differed),
        "p_equal_at_comparison": bool(p_equal_now),
    }


def _perturbed_tape(comparison: OpportunityComparison) -> Tape:
    base = BASE_FAMILY_BY_NAME[comparison.base_family]
    flip = _partner_flip_primitive(base, comparison.partner_key)
    perturbation = {
        (int(step), str(comparison.partner_key)): int(flip)
        for step in comparison.window
    }
    return Tape.make(
        comparison.episode_id,
        comparison.target_key,
        perturbation,
        base_family=comparison.base_family,
    )


def _base_tape(comparison: OpportunityComparison) -> Tape:
    return Tape.make(
        comparison.episode_id,
        comparison.target_key,
        {},
        base_family=comparison.base_family,
    )


def stratify(designs: Sequence[Design] | None = None) -> dict:
    """Run the registered search and classify EVERY compared opportunity.

    Returns the full report: the registered classification rule, the primary
    partition counts over all comparisons, the stratification of the FULL-match
    set (Pro's named risk), of the minus-``high_hidden`` reconverged set with a
    ``high_hidden`` residual, and of the loop-4 sourcing set (reconverged,
    P-different), plus the class of every classified comparison for downstream
    joins.
    """
    resolved = registered_designs() if designs is None else tuple(designs)
    result = run_search(resolved)

    base_cache: dict[tuple, dict[int, dict]] = {}
    perturbed_cache: dict[tuple, dict[int, dict]] = {}
    classified: list[dict] = []
    for comparison in result.comparisons:
        base_key = (
            comparison.episode_id,
            comparison.base_family,
            comparison.target_key,
        )
        if base_key not in base_cache:
            base_cache[base_key] = collect_history_trajectory(
                _base_tape(comparison), comparison.target_key
            )
        perturbed_key = base_key + (comparison.partner_key, comparison.window)
        if perturbed_key not in perturbed_cache:
            perturbed_cache[perturbed_key] = collect_history_trajectory(
                _perturbed_tape(comparison), comparison.target_key
            )
        base_history = base_cache[base_key]
        perturbed_history = perturbed_cache[perturbed_key]
        base_rows_view = {t: snap["rows"] for t, snap in base_history.items()}
        perturbed_rows_view = {
            t: snap["rows"] for t, snap in perturbed_history.items()
        }
        flags = classify(comparison, base_rows_view, perturbed_rows_view)
        decomposition = (
            decompose_row_different(comparison, base_history, perturbed_history)
            if flags["primary"] == EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD
            else {"differ_kind": None, "p_subclass": None}
        )
        classified.append(
            {
                "base_family": comparison.base_family,
                "target_key": comparison.target_key,
                "partner_key": comparison.partner_key,
                "window": list(comparison.window),
                "physical_time": comparison.physical_time,
                "znp_full_match": comparison.znp_full_match,
                "znp_minus_hidden_match": comparison.znp_minus_hidden_match,
                "delta_p": comparison.delta_p,
                "high_hidden_l2_gap": comparison.high_hidden_l2_gap,
                **flags,
                **decomposition,
            }
        )

    def primary_counts(rows: Sequence[dict]) -> dict[str, int]:
        return {
            name: sum(1 for row in rows if row["primary"] == name)
            for name in PRIMARY_CLASSES
        }

    exposed_different = [
        row
        for row in classified
        if row["primary"] == EXPOSURE_TARGET_EXPOSED_DIFFERENT_PAYLOAD
    ]
    full_matches = [row for row in classified if row["znp_full_match"]]
    hidden_residual = [
        row
        for row in classified
        if row["znp_minus_hidden_match"] and row["high_hidden_l2_gap"] > 0.0
    ]
    sourcing_set = [row for row in hidden_residual if row["delta_p"] > 0.0]

    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "scope": SCOPE,
        "classification_rule": {
            "pre_perturbation": "physical_time <= flip_step (single-step window)",
            "rows_comparison": (
                "positional in append order; length mismatch or any aligned "
                "(partner, payload) difference = differing exposure "
                "(loop-4 exposure_positive predicate)"
            ),
            "target_exposed_with_equal_payload": (
                "rows byte-equal AND >=1 row written after the flip step and "
                "visible at the compared time"
            ),
            "post_perturbation_but_target_unexposed": (
                "rows byte-equal AND no row written after the flip step"
            ),
            "post_exposure_refinements": (
                "environment_reconverged iff znp_minus_hidden_match; "
                "full_non_P_reconverged iff znp_full_match; both only over the "
                "exposed-with-different-payload class"
            ),
            "equal_payload_corrected_name": EQUAL_PAYLOAD_CORRECTED_NAME,
            "equal_payload_semantics": (
                "proves a post-flip WRITE OCCASION with an equal record; does "
                "NOT prove the perturbation reached the target's P source -- a "
                "control, not a P-exposure case (Pro loop-4 C5)"
            ),
            "row_different_differ_kinds": (
                "row_count_or_write_occasion_different (counts differ) > "
                "payload_sequence_different (>=1 aligned payload differs; the "
                "P update consumes payload) > partner_identity_only (aligned "
                "payloads equal, partner identity differs; NOT a differing "
                "scalar-P exposure)"
            ),
            "p_subclasses": (
                "over payload_sequence_different only, from measured pre-token "
                "current_p trajectories at shared event times <= compared time: "
                "current_P_still_different | never_changed | exactly-one "
                "differing payload then equal = decayed_to_exact_equality | "
                ">=2 differing payloads then equal = cancelled_in_the_EMA"
            ),
        },
        "counts": {
            "comparisons": len(classified),
            "primary": primary_counts(classified),
            "post_exposure_environment_reconverged": sum(
                1 for row in classified
                if row["post_exposure_environment_reconverged"]
            ),
            "post_exposure_full_non_p_reconverged": sum(
                1 for row in classified
                if row["post_exposure_full_non_p_reconverged"]
            ),
        },
        "full_match_stratification": {
            "total": len(full_matches),
            "primary": primary_counts(full_matches),
        },
        "hidden_residual_stratification": {
            "total": len(hidden_residual),
            "primary": primary_counts(hidden_residual),
        },
        "reconverged_p_different_stratification": {
            "total": len(sourcing_set),
            "primary": primary_counts(sourcing_set),
        },
        "row_different_decomposition": {
            "total": len(exposed_different),
            "differ_kind": {
                name: sum(
                    1 for row in exposed_different if row["differ_kind"] == name
                )
                for name in DIFFER_KINDS
            },
            "p_subclass": {
                name: sum(
                    1 for row in exposed_different if row["p_subclass"] == name
                )
                for name in P_SUBCLASSES
            },
            "delta_p_zero_cases": [
                {
                    "base_family": row["base_family"],
                    "target_key": row["target_key"],
                    "partner_key": row["partner_key"],
                    "window": row["window"],
                    "physical_time": row["physical_time"],
                    "znp_minus_hidden_match": row["znp_minus_hidden_match"],
                    "differ_kind": row["differ_kind"],
                    "p_subclass": row["p_subclass"],
                    "payload_diff_position_count": row[
                        "payload_diff_position_count"
                    ],
                    "partner_diff_position_count": row[
                        "partner_diff_position_count"
                    ],
                    "row_count_differs": row["row_count_differs"],
                    "p_ever_differed_pre_comparison": row[
                        "p_ever_differed_pre_comparison"
                    ],
                }
                for row in exposed_different
                if row["delta_p"] == 0.0
            ],
        },
        "classified": classified,
    }


SCOPE = (
    "MECHANICAL exposure stratification of the loop-3 registered CONTROL-budget "
    "comparisons, as directed by External Pro's ruling on 7accc4c8 (guard A: the "
    "unstratified full-match aggregate is not mechanistically diagnostic). "
    "Classifies every compared target opportunity by the target's "
    "PartnerInteractionRow provenance into Pro's flags: pre_perturbation | "
    "post_perturbation_but_target_unexposed | target_exposed_with_equal_payload | "
    "target_exposed_with_different_payload, refined over the exposed-different "
    "class by post_exposure_environment_reconverged (minus-high_hidden digest "
    "match) and post_exposure_full_non_P_reconverged (full digest match). The "
    "classification RULE is registered in this module (see docstring and "
    "classification_rule in the report): pre_perturbation means the opportunity "
    "read precedes the flipped primitive; rows are compared positionally in "
    "append order; exposed-with-equal-payload means a post-flip write occurred "
    "and recorded byte-equal (partner, payload); unexposed means no post-flip "
    "write. Counts are MEASURED properties of the finite registered budget under "
    "controlled legal arms; they carry no population, support, or overlap claim, "
    "and the READING of the strata (which classes inform joint forgetting, and "
    "what the exposed full-match count establishes) belongs to External Pro. "
    "Pro loop-4 C5 corrections registered here: (a) target_exposed_with_equal_"
    "payload has the corrected semantics post_flip_target_write_with_equal_record "
    "-- it proves a post-flip write occasion, NOT that the perturbation reached "
    "the target's P source; these cases are CONTROLS, not P-exposure cases. "
    "(b) 'genuine differing exposure' is NARROWED to 'provenance-row-different "
    "history': the row-different class is decomposed into partner_identity_only "
    "(NOT a differing scalar-P exposure -- the P update consumes payload, not "
    "partner identity), payload_sequence_different, and row_count_or_write_"
    "occasion_different, with the retained-P consequence of the payload kind "
    "subclassified from measured pre-token current_p trajectories "
    "(still_different | never_changed | decayed_to_exact_equality | "
    "cancelled_in_the_EMA). The decomposition is evidence hygiene for reading "
    "the dP=0 row-different cases; it is NOT needed to accept the D1 sourced "
    "pair, whose current P values differ."
)


@functools.lru_cache(maxsize=1)
def _cached_report() -> dict:
    return stratify()


def proof() -> dict:
    """The registered stratification report over the full loop-3 budget."""
    return _cached_report()


if __name__ == "__main__":  # pragma: no cover
    import json

    report = proof()
    slim = {k: v for k, v in report.items() if k != "classified"}
    print(json.dumps(slim, indent=2, default=str))
