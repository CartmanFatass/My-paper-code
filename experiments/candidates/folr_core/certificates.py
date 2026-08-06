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

CONDITION 9 AND THE SELECTED PROFILE
------------------------------------
Condition 9 -- "all three PCG64 pre-states match the common manifest" -- reads
literally only under one normalization profile, so the first pass left it
``UNRESOLVED`` rather than passing it under a reading Pro had not selected.
Pro then selected:

    PROVENANCE_LABEL […] Under this profile, condition 9 reads literally:
    Immediately before the registered capture transaction, the complete states
    of opportunity_rng, frontier_rng, and action_rng must each equal the
    corresponding state in the single registered reset manifest.

Under the registered profile the condition is therefore a live PASS/FAIL gate.
The ``UNRESOLVED`` branch is kept for ``RECONSTRUCTED_HISTORY``, which Pro
called "a legitimate later robustness experiment, but not the registered
primary design" -- there the RNG states are residual history by construction.

WITNESS LAYER B -- WHICH PAYLOAD ACTUALLY REACHED THE TOKEN
-----------------------------------------------------------
    The binding digest proves which payload vectors were registered; it does
    not prove which vector reached a particular token.

``payload_read_certificate`` closes that with whole-vector dtype/shape/byte
digests against the eight registered expectations.

WHAT "COMPLETE" MEANS FOR AN RNG STATE
--------------------------------------
Pro's other correction here: the first pass compared only the nested ``state``
member of each PCG64 mapping.  That omits ``has_uint32`` and ``uinteger``, the
cached-32-bit-draw fields, so two generators could compare equal and still
produce different next values.  ``rng_state_digest`` digests the whole mapping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from experiments.candidates.folr_core import branch_snapshot as bs
from experiments.candidates.folr_core import branches as br
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


def rng_state_digest(state: Mapping[str, Any]) -> str:
    """Digest the COMPLETE canonical PCG64 state mapping.

    Pro:

        _rng_states_equal currently compares only each mapping's nested "state"
        member. The condition says complete PCG64 pre-state, so the certificate
        must compare the entire canonical state mapping, not a selected
        subfield.

    The old comparison ignored ``bit_generator``, ``has_uint32`` and
    ``uinteger`` -- the last two are the cached-32-bit-draw fields, so two
    generators could compare equal here and still produce different next
    values.  ``bs.digest_of`` is the fail-closed serializer, which refuses any
    type it cannot canonicalize rather than falling back to ``repr``.
    """
    return bs.digest_of(dict(state))


def _rng_states_equal(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    if set(left) != set(right):
        return False
    return all(
        rng_state_digest(left[name]) == rng_state_digest(right[name])
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
            # Complete canonical state, not the nested "state" subfield: the
            # cached-uint32 fields move on a 32-bit draw even when the counter
            # pair does not, so a subfield comparison could miss a draw.
            and rng_state_digest(evidence["rng_states_before"]["action_rng"])
            == rng_state_digest(evidence["rng_states_after"]["action_rng"]),
            "teacher actions covered the frontier, so policy_action_uniform is "
            "None and the complete action-RNG state is unmoved across the "
            "transaction",
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


# ---------------------------------------------------------------------------
# Which payload actually reached the token
# ---------------------------------------------------------------------------


def payload_read_certificate(
    result: Any, *, registration: reg.Registration
) -> dict[str, Any]:
    """Prove which registered vector the token actually read.

    Pro:

        The binding digest proves which payload vectors were registered; it
        does not prove which vector reached a particular token.

    ``EventTokenRow`` already carries ``pre_token_high_hidden`` (the target's
    own S03 input) and ``active_high_hidden`` (the whole active array, ordered
    by ``active_lifecycle_keys``), so no new runtime hook is needed -- the
    certificate reads witnesses the runtime already commits.

    The eight registered expectations, verbatim from §6B:

        K_{0,b}: target pre-hidden = h0
        K_{1,b}: target pre-hidden = h1
        R_b:     target pre-hidden = h_neutral
        W_0:     target pre-hidden = h_neutral, shadow active-hidden = h0
        W_1:     target pre-hidden = h_neutral, shadow active-hidden = h1

    A ninth check goes beyond the list and is worth having: on the branches
    where the shadow is *not* a treatment arm, its active-hidden row must still
    equal the registered manifest value.  Without it, a payload leaking into the
    shadow on a transplant branch would go unnoticed, and the wrong-owner null
    would then be comparing two contaminated states rather than one clean pair.
    """
    binding = registration.binding
    manifest = registration.manifest
    spec = result.spec
    row = result.row

    if spec.kind in (br.RESET, br.WRONG_OWNER):
        expected_target_slot = sb.PAYLOAD_NEUTRAL
    else:
        expected_target_slot = spec.payload_slot

    target_actual = sb.vector_digest(np.asarray(row.pre_token_high_hidden))
    target_expected = sb.vector_digest(binding.payload(expected_target_slot))

    keys = tuple(row.active_lifecycle_keys)
    epochs = tuple(row.active_membership_epochs)
    shadow = binding.shadow_lifecycle_key
    # Pro §5: locating the shadow by key alone certifies a hidden vector without
    # certifying whose epoch it belongs to. The index is resolved once and the
    # (key, epoch) pair at that index is what gets checked, so the vector and
    # the identity provably come from the same row.
    shadow_index = keys.index(shadow) if shadow in keys else None
    shadow_identity_matches = (
        shadow_index is not None
        and len(epochs) == len(keys)
        and int(epochs[shadow_index]) == binding.shadow_membership_epoch
    )
    shadow_actual = (
        sb.vector_digest(np.asarray(row.active_high_hidden)[shadow_index])
        if shadow_index is not None
        else "ABSENT"
    )
    if spec.kind == br.WRONG_OWNER:
        shadow_expected_name = spec.payload_slot
        shadow_expected = sb.vector_digest(binding.payload(spec.payload_slot))
    else:
        shadow_expected_name = "registered manifest value"
        shadow_expected = sb.vector_digest(
            np.asarray(manifest.owner(shadow).high_hidden, dtype=np.float32)
        )

    # Under RECONSTRUCTED_HISTORY the shadow's high_hidden is deliberately NOT
    # normalized, so its manifest equality is residual history rather than a
    # violation.  Only the selected profile makes it a gate.
    shadow_is_a_gate = (
        spec.kind == br.WRONG_OWNER
        or registration.normalization_profile == rm.PROVENANCE_LABEL
    )
    shadow_matches = shadow_actual == shadow_expected

    conditions = [
        _condition(
            "target_pre_hidden_is_the_registered_payload",
            target_actual == target_expected,
            f"expected {expected_target_slot}, "
            f"digest {target_expected[:12]} vs actual {target_actual[:12]}",
        ),
        _condition(
            "shadow_row_is_the_registered_owner_and_epoch",
            shadow_identity_matches,
            f"(key, epoch) at index {shadow_index} must be "
            f"({shadow}, {binding.shadow_membership_epoch}); "
            f"row carries keys={keys} epochs={epochs}",
        ),
    ]
    if shadow_is_a_gate:
        conditions.append(
            _condition(
                "shadow_active_hidden_is_the_registered_value",
                shadow_matches,
                f"expected {shadow_expected_name}, "
                f"digest {shadow_expected[:12]} vs actual {shadow_actual[:12]}",
            )
        )
    else:
        conditions.append(
            Condition(
                name="shadow_active_hidden_is_the_registered_value",
                state=UNRESOLVED,
                detail=(
                    "profile=RECONSTRUCTED_HISTORY leaves the shadow's hidden "
                    "state inside the residual history difference by design, so "
                    "manifest equality is not required on this branch "
                    f"(matches anyway: {shadow_matches})"
                ),
            )
        )

    states = [condition.state for condition in conditions]
    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "branch": spec.name,
        "terminal": (
            "PAYLOAD_READ_NOT_CERTIFIED"
            if FAIL in states
            else "PAYLOAD_READ_UNRESOLVED"
            if UNRESOLVED in states
            else "PAYLOAD_READ_CERTIFIED"
        ),
        "expected_target_slot": expected_target_slot,
        "target_pre_hidden_digest": target_actual,
        "shadow_active_hidden_digest": shadow_actual,
        "conditions": {
            condition.name: {"state": condition.state, "detail": condition.detail}
            for condition in conditions
        },
        "failed": [c.name for c in conditions if c.state == FAIL],
    }


def certify_branch(result: Any, *, registration: reg.Registration) -> dict[str, Any]:
    """All three witness layers for one branch."""
    core = result.evidence["core"]
    return {
        "branch": result.spec.name,
        "direct_replay": direct_replay_certificate(core, result.row, result.kernel),
        "freshness": freshness_certificate(result.evidence, registration=registration),
        "payload_read": payload_read_certificate(result, registration=registration),
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
        "payload_read_terminals": {
            name: entry["payload_read"]["terminal"]
            for name, entry in certificates.items()
        },
        "all_payload_reads_certified": all(
            entry["payload_read"]["terminal"] == "PAYLOAD_READ_CERTIFIED"
            for entry in certificates.values()
        ),
    }
