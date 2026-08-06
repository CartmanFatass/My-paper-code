"""FOLR outcome controller: External Pro's §6 partition, in precedence order.

Sequence 01, second half of component 7 of the object graph required by ruling
``FOLR_S03_BINDING_SELECTED``.

    Apply the categories in this precedence order: interface validity, closure
    controls, reset control, then payload contrast.

Each terminal carries its *maximum conclusion* and its *explicitly forbidden*
claims, both transcribed from Pro's table rather than paraphrased.  The point of
transcribing them is that the forbidden list travels with the number: a result
read out of this module cannot be quoted without the sentence saying what it
does not license.

THE ONE PIECE OF ROUTING THAT IS EASY TO GET BACKWARDS
------------------------------------------------------
    One qualification applies to "payload access refuted": if the registered
    cell carries an analytic construction that mathematically guarantees a
    nonzero effect, observing no effect contradicts the construction. That
    result belongs in interface/instance insufficient, not scientific
    refutation.

The registered cell here *is* such a construction -- ``registration.py`` derives
``2 * (GELU(2) - GELU(0))`` in closed form -- so a null payload contrast in this
design is evidence that the harness is broken, never that the runtime lacks the
access.  ``_route`` implements that, and
``test_a_null_against_an_analytic_guarantee_is_an_engineering_failure`` pins it.

Nothing in this module decides anything scientific.  It sorts a measured pattern
into the box Pro assigned it and reports the ceiling on what may be said.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from experiments.candidates.folr_core import registration as reg

RAW_OUTPUT_BINDING = "folr_core.outcome.v1"

NARROW_CLAIM_SUPPORTED = "NARROW_CLAIM_SUPPORTED"
PAYLOAD_ACCESS_REFUTED = "PAYLOAD_ACCESS_REFUTED"
FIXED_PAYLOAD_NULL_FAILURE = "FIXED_PAYLOAD_NULL_FAILURE"
RESET_NULL_FAILURE = "RESET_NULL_FAILURE"
INTERFACE_INSUFFICIENT = "INTERFACE_OR_INSTANCE_INSUFFICIENT"

#: Transcribed from Pro's §6 table.
MAXIMUM_CONCLUSION = {
    NARROW_CLAIM_SUPPORTED: (
        "The registered target's first kernel is causally sensitive to the "
        "installed owner-private S03 value at this exact model and boundary"
    ),
    PAYLOAD_ACCESS_REFUTED: (
        "No detectable S03 access at the exact registered cell, encoding and "
        "snapshot"
    ),
    FIXED_PAYLOAD_NULL_FAILURE: (
        "Branch/provenance or non-owner payload information reaches the kernel, "
        "or closure is incomplete"
    ),
    RESET_NULL_FAILURE: (
        "The reset implementation is incomplete or branch-sensitive. The "
        "transplant contrast may be retained only as a provisional pointwise "
        "observation"
    ),
    INTERFACE_INSUFFICIENT: "Engineering failure or unexecuted design only",
}

FORBIDDEN = {
    NARROW_CLAIM_SUPPORTED: (
        "Natural retention, cross-epoch carry, event-history mediation, task "
        "value, return, delayed credit, coordination, generalization to other "
        "cells or learned policies"
    ),
    PAYLOAD_ACCESS_REFUTED: (
        "Global refutation of FOLR, refutation of all high_hidden encodings, or "
        "a claim that owner-private recurrence is generally inaccessible"
    ),
    FIXED_PAYLOAD_NULL_FAILURE: (
        "Attribution of the P-contrast to target S03; both positive and "
        "negative payload-access conclusions"
    ),
    RESET_NULL_FAILURE: (
        "Any claim involving complete erasure, reset neutrality or absence of "
        "historical state; final acceptance under the frozen six/eight-kernel "
        "contract"
    ),
    INTERFACE_INSUFFICIENT: (
        "Any scientific positive, negative or null conclusion"
    ),
}

#: Pro §7, on the constructed cell.  Applies whenever the positive terminal is
#: reached in a cell whose sensitivity was built in.
CONSTRUCTED_CELL_EXCLUSIONS = (
    "a naturally trained policy discovered S03 use",
    "the environment creates a need for the mechanism",
    "the mechanism improves behavior",
    "typical cells are S03-sensitive",
)


@dataclass(frozen=True)
class Gate:
    name: str
    passed: bool
    detail: str


def _interface_gates(
    certificates: Mapping[str, Any],
    results: Mapping[str, Any],
    registration: reg.Registration,
) -> list[Gate]:
    branches = certificates["branches"]
    freshness = certificates["freshness_terminals"]
    binding = registration.binding
    kernels = [entry["kernel"] for entry in branches.values()]
    digests = {
        entry["evidence"]["model_state_digest_before"]
        for entry in ({"evidence": r.evidence} for r in results.values())
    }
    return [
        Gate(
            "registry_present",
            bool(registration.registration_digest()),
            f"registration digest {registration.registration_digest()[:12]}",
        ),
        Gate(
            "freshness_valid",
            all(state == "FRESH" for state in freshness.values()),
            f"terminals={dict(freshness)}",
        ),
        Gate(
            "direct_replay_agree",
            bool(certificates["all_direct_replay_agree"]),
            "float64(direct float32) == replayed float64 on every branch",
        ),
        Gate(
            "kernels_belong_to_the_registered_owner_and_epoch",
            all(
                kernel["owner"] == binding.target_lifecycle_key
                and kernel["membership_epoch"] == binding.target_membership_epoch
                for kernel in kernels
            ),
            f"target={binding.target_lifecycle_key}"
            f"@{binding.target_membership_epoch}",
        ),
        Gate(
            "model_digest_identical_across_branches",
            len(digests) == 1,
            f"{len(digests)} distinct model digests across the branches",
        ),
        Gate(
            "intervention_manifest_digest_matches_the_registry",
            all(
                kernel["intervention_manifest_digest"] == binding.manifest_digest()
                for kernel in kernels
            ),
            f"registry digest {binding.manifest_digest()[:12]}",
        ),
    ]


def _closure_gates(contrasts: Mapping[str, Any]) -> list[Gate]:
    gates: list[Gate] = []
    for entry in contrasts["fixed_payload_nulls"]:
        left, right = entry["pair"]
        gates.append(
            Gate(
                f"fixed_payload_null_{left}_{right}",
                bool(entry["probabilities_bitwise_equal"]),
                f"||.||_inf = {entry['infinity_norm']}",
            )
        )
        gates.append(
            Gate(
                f"actor_preimage_closure_{left}_{right}",
                bool(entry["actor_preimage_digests_equal"]),
                # Pro: "The actor-preimage equality certificate is primary;
                # output equality is its negative-control consequence."
                "the preimage certificate is primary, not the output equality",
            )
        )
    wrong = contrasts["wrong_owner_null"]
    gates.append(
        Gate(
            "wrong_owner_null_W_0_W_1",
            bool(wrong["probabilities_bitwise_equal"]),
            f"||.||_inf = {wrong['infinity_norm']}",
        )
    )
    gates.append(
        Gate(
            "wrong_owner_actor_preimage_closure",
            bool(wrong["actor_preimage_digests_equal"]),
            "the shadow's payload moves the critic's old_owner_value by design; "
            "only the probability vector and the preimage digest are compared",
        )
    )
    return gates


def _route(
    *,
    interface: list[Gate],
    closure: list[Gate],
    reset: Gate,
    contrast: Mapping[str, float],
    registration: reg.Registration,
) -> tuple[str, str]:
    if not all(gate.passed for gate in interface):
        return INTERFACE_INSUFFICIENT, "interface validity failed"
    if not all(gate.passed for gate in closure):
        return FIXED_PAYLOAD_NULL_FAILURE, "a closure control failed"
    if not reset.passed:
        return RESET_NULL_FAILURE, "R_0 != R_1"
    margin = float(registration.delta_cell)
    exceeds = all(float(value) > margin for value in contrast.values())
    if exceeds:
        return NARROW_CLAIM_SUPPORTED, (
            f"payload contrast exceeds the registered margin {margin} in both b"
        )
    if registration.analytic_logit_separation > 0.0:
        # Pro's §6 qualification. The cell mathematically guarantees a nonzero
        # effect, so its absence contradicts the construction and is an
        # engineering failure -- never a scientific refutation.
        return INTERFACE_INSUFFICIENT, (
            "the registered cell analytically guarantees a logit separation of "
            f"{registration.analytic_logit_separation:.6f}, so a contrast at or "
            "below the margin contradicts the construction rather than refuting "
            "payload access"
        )
    return PAYLOAD_ACCESS_REFUTED, (
        f"payload contrast did not exceed the registered margin {margin}"
    )


def decide(
    *,
    results: Mapping[str, Any],
    contrasts: Mapping[str, Any],
    certificates: Mapping[str, Any],
    registration: reg.Registration,
) -> dict[str, Any]:
    """Sort the measured pattern into Pro's partition. Decides nothing else."""
    interface = _interface_gates(certificates, results, registration)
    closure = _closure_gates(contrasts)
    reset_entry = contrasts["reset_null"]
    reset = Gate(
        "reset_null_R_0_R_1",
        bool(reset_entry["probabilities_bitwise_equal"]),
        f"||.||_inf = {reset_entry['infinity_norm']}",
    )
    terminal, reason = _route(
        interface=interface,
        closure=closure,
        reset=reset,
        contrast=contrasts["payload_contrast"],
        registration=registration,
    )

    report: dict[str, Any] = {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        "registration_digest": registration.registration_digest(),
        "cell_identifier": registration.cell_identifier,
        "terminal": terminal,
        "reason": reason,
        "maximum_conclusion": MAXIMUM_CONCLUSION[terminal],
        "explicitly_forbidden": FORBIDDEN[terminal],
        "gates": {
            "interface_validity": [vars(gate) for gate in interface],
            "closure_controls": [vars(gate) for gate in closure],
            "reset_control": vars(reset),
        },
        "payload_contrast": dict(contrasts["payload_contrast"]),
        "delta_cell": registration.delta_cell,
        "analytic_logit_separation": registration.analytic_logit_separation,
    }
    if terminal == NARROW_CLAIM_SUPPORTED:
        report["constructed_cell_exclusions"] = list(CONSTRUCTED_CELL_EXCLUSIONS)
        report["constructed_cell_note"] = (
            "The sensitivity in this cell was built in analytically. The "
            "admissible reading is that the runtime correctly transports and "
            "reads a registered owner-private recurrent payload in a "
            "constructed sensitivity cell."
        )
    if registration.development_only:
        report["terminal"] = INTERFACE_INSUFFICIENT
        report["development_only_override"] = (
            "This is the DEVELOPMENT_ONLY decoy cell. No scientific conclusion "
            "of any sign may be drawn from it; the terminal above is retained "
            "only as harness diagnostics."
        )
        report["harness_terminal"] = terminal
        report["maximum_conclusion"] = MAXIMUM_CONCLUSION[INTERFACE_INSUFFICIENT]
        report["explicitly_forbidden"] = FORBIDDEN[INTERFACE_INSUFFICIENT]
    return report
