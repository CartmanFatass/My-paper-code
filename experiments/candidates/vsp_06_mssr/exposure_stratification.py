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


def collect_row_trajectory(
    tape: Tape, target_key: str
) -> dict[int, tuple[tuple[int, str, float], ...]]:
    """The target's PRE-TOKEN partner-interaction rows at every event time.

    A read-only preframe (fires once per ``apply_transaction`` after membership
    commit, before the frontier loop) snapshots the target's accumulated rows.
    The target's rows are owner-private and grow ONLY at the target's own token,
    so the post-commit pre-frontier snapshot equals the pre-token snapshot at
    every event, including non-opportunity events (harmless extras).  Returns
    ``{physical_time: ((event_index, partner_lifecycle_key, payload), ...)}``
    for every event time at which the target holds an ACTIVE record.
    """
    core = make_core(tape.episode_id)
    env = make_environment()
    target = str(target_key)
    trajectory: dict[int, tuple[tuple[int, str, float], ...]] = {}

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
        trajectory[int(c.physical_time)] = rows

    _drive(core, env, tape, preframe=reader, sink=None)
    return trajectory


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

    base_cache: dict[tuple, dict[int, tuple]] = {}
    perturbed_cache: dict[tuple, dict[int, tuple]] = {}
    classified: list[dict] = []
    for comparison in result.comparisons:
        base_key = (
            comparison.episode_id,
            comparison.base_family,
            comparison.target_key,
        )
        if base_key not in base_cache:
            base_cache[base_key] = collect_row_trajectory(
                _base_tape(comparison), comparison.target_key
            )
        perturbed_key = base_key + (comparison.partner_key, comparison.window)
        if perturbed_key not in perturbed_cache:
            perturbed_cache[perturbed_key] = collect_row_trajectory(
                _perturbed_tape(comparison), comparison.target_key
            )
        flags = classify(
            comparison, base_cache[base_key], perturbed_cache[perturbed_key]
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
            }
        )

    def primary_counts(rows: Sequence[dict]) -> dict[str, int]:
        return {
            name: sum(1 for row in rows if row["primary"] == name)
            for name in PRIMARY_CLASSES
        }

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
    "what the exposed full-match count establishes) belongs to External Pro."
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
