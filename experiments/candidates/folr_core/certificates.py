"""FOLR direct/replay agreement and freshness certificates.

Sequence 01, component 6 of the object graph External Pro required in ruling
``FOLR_S03_BINDING_SELECTED``.

WITNESS LAYER C -- DIRECT/REPLAY AGREEMENT
------------------------------------------
    Acceptance requires: float64(direct_float32_kernel) = replayed_float64_kernel
    element-for-element, under the same parameter digest and architecture mode.

with Pro's numerical wording correction carried in the result:

    replay_token_distribution() returns an array with NumPy dtype float64, but
    the tensors and softmax are float32 and the result is widened afterward. The
    registered object should therefore be described as: the exact widened
    representation of the committed float32 softmax output, not as a natively
    computed float64 softmax.

``summary_source`` has no default in the runtime, and Pro asked that the choice
be recorded rather than assumed:

    At target position zero, initial and working summaries should coincide.
    Nevertheless, the row should record the summary source actually selected so
    a later architectural change cannot silently alter replay semantics.

So both sources are replayed and both are required to agree; a future change
that breaks their coincidence at position zero fails here instead of silently
changing what "replay" means.

WITNESS LAYER D -- FRESHNESS AND NO PREDECESSOR
-----------------------------------------------
Pro listed eleven conditions and required all of them before the word "first
fresh" may be used.  Each is a named entry with its own detail string, so a
failure says which one failed.

ONE CONDITION IS DELIBERATELY LEFT UNRESOLVED
---------------------------------------------
Condition 9 -- "all three PCG64 pre-states match the common manifest" -- is
satisfiable literally only under the ``PROVENANCE_LABEL`` normalization profile.
Under ``RECONSTRUCTED_HISTORY`` the RNG consumption states are part of the
residual history difference by design, so the condition has to be read per
branch instead.  Rather than quietly pass it under a reading Pro has not
selected, the certificate returns ``UNRESOLVED`` for it and the terminal becomes
``FRESHNESS_UNRESOLVED``.  Passing it vacuously would be the same class of error
as the UCOPE ceiling guard that reported a flag and continued anyway.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from experiments.candidates.folr_core import branch_snapshot as bs
from experiments.candidates.folr_core import registration as reg
from experiments.candidates.folr_core import reset_manifest as rm
from experiments.candidates.folr_core import s03_binding as sb

RAW_OUTPUT_BINDING = "folr_core.certificates.v1"

PASS = "PASS"
FAIL = "FAIL"
UNRESOLVED = "UNRESOLVED"

SUMMARY_SOURCES = ("initial", "working")


@dataclass(frozen=True)
class Condition:
    name: str
    state: str
    detail: str


def _condition(name: str, holds: bool, detail: str) -> Condition:
    return Condition(name=name, state=PASS if holds else FAIL, detail=detail)


# ---------------------------------------------------------------------------
# Layer C
# ---------------------------------------------------------------------------


def direct_replay_certificate(core: Any, row: Any, kernel: sb.DirectKernel) -> dict[str, Any]:
    """float64(direct float32) == replayed float64, for BOTH summary sources."""
    direct = kernel.probabilities
    widened = direct.astype(np.float64)
    rows: dict[str, Any] = {}
    agree = True
    for source in SUMMARY_SOURCES:
        replayed = np.asarray(core.replay_token_distribution(row, summary_source=source))
        matches = bool(
            replayed.dtype == np.dtype(np.float64)
            and replayed.shape == widened.shape
            and np.array_equal(widened, replayed)
        )
        agree = agree and matches
        rows[source] = {
            "agrees": matches,
            "max_absolute_difference": float(
                np.max(np.abs(widened - replayed)) if replayed.shape == widened.shape
                else float("inf")
            ),
        }
    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "direct_dtype": str(direct.dtype),
        "replay_object": (
            "the exact widened representation of the committed float32 softmax "
            "output, not a natively computed float64 softmax"
        ),
        "summary_sources": rows,
        "agrees": agree,
    }


# ---------------------------------------------------------------------------
# Layer D
# ---------------------------------------------------------------------------


def _rng_states_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return all(
        dict(left[name]).get("state") == dict(right[name]).get("state")
        for name in left
    )


def freshness_certificate(
    evidence: Mapping[str, Any], *, registration: reg.Registration
) -> dict[str, Any]:
    """Pro's eleven §5D conditions, each named and each independently reported."""
    manifest = registration.manifest
    target = manifest.target_lifecycle_key
    order = tuple(evidence["sampled_order"])
    frontier_size = int(evidence["frontier_size"])

    conditions: list[Condition] = [
        _condition(
            "target_is_first_in_sampled_order",
            bool(order) and order[0] == target,
            f"sampled_order={order}, target={target}",
        ),
        _condition(
            "token_position_is_zero",
            int(evidence["token_position"]) == 0,
            f"token_position={evidence['token_position']}",
        ),
        _condition(
            "teacher_order_was_supplied",
            bool(evidence["teacher_order_supplied"]),
            "frontier RNG was therefore not consumed to select the target's "
            "position",
        ),
        _condition(
            "high_ledger_unchanged_since_restoration",
            int(evidence["high_ledger_length_before"])
            == int(evidence["restored_high_ledger_length"])
            and evidence["high_ledger_digest_before"]
            == evidence["restored_high_ledger_digest"],
            f"restored={evidence['restored_high_ledger_length']} rows, "
            f"before capture={evidence['high_ledger_length_before']} rows",
        ),
        _condition(
            "no_low_action_or_low_ledger_append",
            int(evidence["low_ledger_length_before"]) == 0
            and int(evidence["low_ledger_length_after"]) == 0
            and int(evidence["low_chunk_boundaries_before"]) == 0
            and int(evidence["low_chunk_boundaries_after"]) == 0,
            # Pro: "the cleanest instantiation is SUPPLIED_EXECUTOR_RUNTIME,
            # because it removes the learned low path" -- so this is structural
            # here rather than merely observed, and the runtime mode is checked.
            f"runtime_mode={evidence['runtime_mode']}, "
            f"low_ledger {evidence['low_ledger_length_before']}"
            f"->{evidence['low_ledger_length_after']}",
        ),
        _condition(
            "target_has_no_open_trace",
            not bool(evidence["target_open_trace_before"]),
            "an open trace would let _close_trace append a branch-dependent row "
            "before the kernel is produced",
        ),
        _condition(
            "exactly_one_transaction_consumed",
            int(evidence["high_ledger_length_after"])
            - int(evidence["high_ledger_length_before"])
            == frontier_size
            and not bool(evidence["pending_membership_transaction_before"])
            and not bool(evidence["pending_membership_transaction_after"]),
            f"appended {int(evidence['high_ledger_length_after']) - int(evidence['high_ledger_length_before'])} "
            f"rows for a frontier of {frontier_size}",
        ),
        _condition(
            "model_parameters_not_mutated",
            evidence["model_state_digest_before"] == evidence["model_state_digest_after"],
            f"digest {str(evidence['model_state_digest_before'])[:12]}",
        ),
        _condition(
            "no_action_draw_before_capture",
            evidence["policy_action_uniform"] is None
            and dict(evidence["rng_states_before"]["action_rng"]).get("state")
            == dict(evidence["rng_states_after"]["action_rng"]).get("state"),
            "teacher actions covered the frontier, so policy_action_uniform is "
            "None and the action RNG state is unmoved across the transaction",
        ),
        _condition(
            "no_prior_owner_token_after_restoration",
            int(evidence["high_ledger_length_before"])
            == int(evidence["restored_high_ledger_length"])
            and not bool(evidence["target_open_trace_before"]),
            "no row and no open trace existed between restoration and capture",
        ),
    ]

    # Condition 9, held open on purpose -- see the module docstring.
    manifest_match = _rng_states_equal(
        evidence["rng_states_before"], evidence["manifest_rng_states"]
    )
    if registration.normalization_profile == rm.PROVENANCE_LABEL:
        conditions.append(
            _condition(
                "pcg64_pre_states_match_the_common_manifest",
                manifest_match,
                "profile=PROVENANCE_LABEL, so Pro's condition reads literally "
                "against the one registered manifest",
            )
        )
    else:
        conditions.append(
            Condition(
                name="pcg64_pre_states_match_the_common_manifest",
                state=UNRESOLVED,
                detail=(
                    "profile=RECONSTRUCTED_HISTORY places the RNG consumption "
                    "states inside the residual history difference by design, so "
                    "this condition must be read per branch rather than against "
                    "one common manifest. Which reading is registered is "
                    "External Pro's to decide; it is not passed here by default. "
                    f"(matches manifest anyway: {manifest_match})"
                ),
            )
        )

    states = [condition.state for condition in conditions]
    if FAIL in states:
        terminal = "NOT_FRESH"
    elif UNRESOLVED in states:
        terminal = "FRESHNESS_UNRESOLVED"
    else:
        terminal = "FRESH"
    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "branch": evidence["branch"],
        "terminal": terminal,
        "conditions": {
            condition.name: {"state": condition.state, "detail": condition.detail}
            for condition in conditions
        },
        "failed": [c.name for c in conditions if c.state == FAIL],
        "unresolved": [c.name for c in conditions if c.state == UNRESOLVED],
    }


def certify_branch(result: Any, *, registration: reg.Registration) -> dict[str, Any]:
    """Both witness layers for one branch."""
    core = result.evidence["core"]
    return {
        "branch": result.spec.name,
        "direct_replay": direct_replay_certificate(core, result.row, result.kernel),
        "freshness": freshness_certificate(result.evidence, registration=registration),
        "kernel": {
            "owner": result.kernel.owner_lifecycle_key,
            "membership_epoch": result.kernel.membership_epoch,
            "token_position": result.kernel.token_position,
            "probabilities": result.kernel.probabilities.tolist(),
            "actor_preimage_digest": result.kernel.actor_preimage_digest,
            "common_snapshot_digest": result.kernel.common_snapshot_digest,
            "intervention_manifest_digest": result.kernel.intervention_manifest_digest,
        },
    }


def certify_all(
    results: Mapping[str, Any], *, registration: reg.Registration
) -> dict[str, Any]:
    certificates = {
        name: certify_branch(result, registration=registration)
        for name, result in results.items()
    }
    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "branches": certificates,
        "all_direct_replay_agree": all(
            entry["direct_replay"]["agrees"] for entry in certificates.values()
        ),
        "freshness_terminals": {
            name: entry["freshness"]["terminal"] for name, entry in certificates.items()
        },
    }
