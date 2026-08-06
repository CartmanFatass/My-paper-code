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
access.

AND THE PART OF THAT WHICH WAS OVERSTATED
-----------------------------------------
The first pass took this too far and routed *every* contrast at or below
``delta_cell`` to engineering failure, calling it a contradiction of the logit
separation.  Pro rejected the inference: the derivation bounds a **logit**
displacement, and a logit displacement does not bound a probability-space
infinity norm, because a third dominant logit can hold both softmax vectors
arbitrarily close together.  So there are now three outcomes below the
threshold, not one:

* ``min_b ||K_1b - K_0b||_inf > delta_cell`` -- supports the narrow claim;
* ``0 < min_b ... <= delta_cell`` -- real but immaterial dependence, routed to
  interface/instance insufficient with Pro's own sentence, and explicitly
  neither a refutation nor a contradiction;
* bitwise equal -- also interface/instance insufficient, describable as
  inconsistent with the intended positive control, but *not* as a mathematical
  contradiction, since no finite-precision probability-separation witness is
  registered.

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
        "VariableRosterEventCore correctly transports and reads the registered "
        "owner-private recurrent payload at the registered synthetic boundary "
        "in the constructed sensitivity cell: the registered target's first "
        "kernel is causally sensitive to the installed owner-private S03 value "
        "at this exact model and boundary"
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
    # Pro §3, on the registered core-only object graph.
    "DynamicRosterEventEnv has been exercised",
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
    expected_registration_digest: str | None,
) -> list[Gate]:
    branches = certificates["branches"]
    freshness = certificates["freshness_terminals"]
    binding = registration.binding
    manifest = registration.manifest
    kernels = [entry["kernel"] for entry in branches.values()]
    evidences = [result.evidence for result in results.values()]
    digests = {evidence["model_state_digest_before"] for evidence in evidences}

    registered_model_digest = str(registration.weight_witness["model_state_digest"])
    registered_mask = manifest.legal_action_support.tolist()
    current_digest = registration.registration_digest()
    executed_fingerprint = reg.actor_path_source_identity()["actor_path_fingerprint"]
    registered_fingerprint = str(registration.source_identity["actor_path_fingerprint"])

    gates = [
        Gate(
            "registry_present",
            bool(current_digest),
            f"registration digest {current_digest[:12]}",
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
            # Pro §6B: the binding digest proves which vectors were REGISTERED;
            # this proves which vector actually reached each token.
            "payload_read_certified_on_every_branch",
            bool(certificates["all_payload_reads_certified"]),
            f"terminals={dict(certificates['payload_read_terminals'])}",
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
            # Pro §4: "Eight branches could therefore share the same wrong model
            # and pass that gate."  Identity across branches is necessary but
            # says nothing about WHICH model ran; the analytic witness is about
            # commitment_model specifically, so that exact digest is load-bearing.
            "executed_model_digest_equals_the_registered_witness",
            all(
                evidence["model_state_digest_before"] == registered_model_digest
                for evidence in evidences
            ),
            f"registered witness {registered_model_digest[:12]}, "
            f"executed {sorted(d[:12] for d in digests)}",
        ),
        Gate(
            "legal_mask_equals_the_registered_support",
            all(
                list(evidence["exact_legal_mask"]) == registered_mask
                for evidence in evidences
            ),
            f"registered support {registered_mask}",
        ),
        Gate(
            "shadow_index_resolves_to_the_registered_owner",
            all(
                binding.shadow_lifecycle_key in tuple(evidence["active_lifecycle_keys"])
                for evidence in evidences
            ),
            f"shadow={binding.shadow_lifecycle_key}",
        ),
        Gate(
            "intervention_manifest_digest_matches_the_registry",
            all(
                kernel["intervention_manifest_digest"] == binding.manifest_digest()
                for kernel in kernels
            ),
            f"registry digest {binding.manifest_digest()[:12]}",
        ),
        Gate(
            # Pro §6C.  Without this, an amended registration could be executed
            # while the approved digest was the earlier one.
            "registration_digest_equals_the_precommitment",
            expected_registration_digest is not None
            and current_digest == expected_registration_digest,
            "no precommitted digest was supplied"
            if expected_registration_digest is None
            else f"expected {expected_registration_digest[:12]}, "
            f"current {current_digest[:12]}",
        ),
        Gate(
            # The content-addressed half of the source identity: the commit may
            # legitimately have moved for unrelated reasons, but the actor path
            # itself must be byte-identical to the approved one.
            "execution_actor_path_matches_the_approved_source_identity",
            executed_fingerprint == registered_fingerprint,
            f"registered {registered_fingerprint[:12]}, "
            f"executed {executed_fingerprint[:12]}",
        ),
    ]
    return gates


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
    # Pro §6A, "the most important missing gate": the identifying closure runs
    # at fixed B, across the payload arms.  The fixed-payload nulls above hold
    # the payload and vary B, so neither implies the other -- and it is this one
    # that licenses attributing a positive contrast to S03 at all.
    for entry in contrasts["payload_closure"]:
        left, right = entry["pair"]
        for field, description in (
            ("actor_preimage_digests_equal", "non-S03 actor preimage"),
            ("common_snapshot_digests_equal", "common snapshot"),
            ("model_state_digests_equal", "registered model"),
            ("legal_masks_equal", "legal mask"),
            ("target_identity_equal", "target key, epoch and token position"),
        ):
            gates.append(
                Gate(
                    f"payload_closure_{field}_{left}_{right}",
                    bool(entry[field]),
                    f"{description} must be identical across the payload arms "
                    "at fixed B, or the contrast is not identified",
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
            # Pro kept these branches after the critic finding: "The observed
            # shadow-value movement is useful as a non-vacuity diagnostic [...]
            # Neither replaces the target-kernel null."
            "the shadow's payload moves the shadow's critic row by design; only "
            "the target probability vector and the non-S03 preimage digest are "
            "compared",
        )
    )
    return gates


def _reset_gates(contrasts: Mapping[str, Any]) -> list[Gate]:
    """Pro §6F: close the reset control extensionally, not just on the output.

        Equal kernels can arise from cancellation despite unequal reset inputs.

    So the input-side digests are required alongside the kernel equality.  The
    two reset snapshots are built from the same canonical manifest, so their
    common-snapshot digests should be equal too -- if they are not, the reset
    constructor is not the deterministic function of the manifest it claims to
    be, whatever the kernels happen to show.
    """
    entry = contrasts["reset_null"]
    return [
        Gate(
            "reset_null_R_0_R_1",
            bool(entry["probabilities_bitwise_equal"]),
            f"||.||_inf = {entry['infinity_norm']}",
        ),
        Gate(
            "reset_actor_preimage_digests_equal",
            bool(entry["actor_preimage_digests_equal"]),
            "unequal reset inputs can still cancel to equal kernels",
        ),
        Gate(
            "reset_common_snapshot_digests_equal",
            bool(entry["common_snapshot_digests_equal"]),
            "both reset runtimes are constructed from the same canonical "
            "manifest, so their pretreatment snapshots must agree",
        ),
    ]


def _route(
    *,
    interface: list[Gate],
    closure: list[Gate],
    reset: list[Gate],
    contrast: Mapping[str, float],
    registration: reg.Registration,
) -> tuple[str, str]:
    """Pro's precedence order, with the corrected margin routing.

    The first pass routed every contrast at or below ``delta_cell`` to an
    engineering failure on the ground that it *contradicted* the analytic logit
    separation.  Pro rejected that inference:

        That proves logit-level functional dependence. It does not by itself
        prove ||K_1 - K_0||_inf > 10^-3. [...] Current outcome.py routes every
        contrast at or below 10^-3 to engineering failure on the ground that it
        "contradicts" the analytic logit separation. That conclusion does not
        follow.

    So the sub-margin band is now its own outcome: real but immaterial payload
    dependence, which is neither a refutation nor a contradiction.  Only the
    exact null is describable as inconsistent with the intended positive
    control, and even then it may be called a mathematical contradiction only
    after a finite-precision probability-separation witness is added -- which
    this registration does not carry.
    """
    if not all(gate.passed for gate in interface):
        failed = [gate.name for gate in interface if not gate.passed]
        return INTERFACE_INSUFFICIENT, f"interface validity failed: {failed}"
    if not all(gate.passed for gate in closure):
        failed = [gate.name for gate in closure if not gate.passed]
        return FIXED_PAYLOAD_NULL_FAILURE, f"a closure control failed: {failed}"
    if not all(gate.passed for gate in reset):
        failed = [gate.name for gate in reset if not gate.passed]
        return RESET_NULL_FAILURE, f"the reset control failed: {failed}"

    margin = float(registration.delta_cell)
    values = [float(value) for value in contrast.values()]
    minimum = min(values) if values else 0.0

    if minimum > margin:
        return NARROW_CLAIM_SUPPORTED, (
            f"min_b ||K_1b - K_0b||_inf = {minimum:.9g} exceeds the registered "
            f"materiality threshold {margin}"
        )
    if minimum > 0.0:
        return INTERFACE_INSUFFICIENT, (
            "The registered cell exhibits nonzero payload dependence below the "
            "prospectively registered probability-space materiality threshold. "
            f"(min_b ||K_1b - K_0b||_inf = {minimum:.9g}, threshold {margin}.) "
            "This is neither a refutation nor a contradiction of the logit "
            "construction."
        )
    if registration.analytic_logit_separation > 0.0:
        return INTERFACE_INSUFFICIENT, (
            "The captured kernels are bitwise equal. This is inconsistent with "
            "the intended positive-control realization of a cell whose logit "
            f"separation is {registration.analytic_logit_separation:.6f}, but it "
            "may NOT be called a mathematical contradiction: no finite-precision "
            "probability-separation witness ruling out softmax saturation, "
            "underflow and rounding at the exact registered model and preimage "
            "is registered."
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
    expected_registration_digest: str | None = None,
) -> dict[str, Any]:
    """Sort the measured pattern into Pro's partition. Decides nothing else.

    ``expected_registration_digest`` is the digest External Pro approved.  It
    is a required input for an accepting terminal: without it the execution
    could be running an amended registration while the approval named an
    earlier one, which is exactly the failure Pro's §6C gate exists to catch.
    """
    interface = _interface_gates(
        certificates, results, registration, expected_registration_digest
    )
    closure = _closure_gates(contrasts)
    reset = _reset_gates(contrasts)
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
        "expected_registration_digest": expected_registration_digest,
        "cell_identifier": registration.cell_identifier,
        "object_graph_scope": reg._scope_record(registration.object_graph_scope),
        "source_identity": dict(registration.source_identity),
        "terminal": terminal,
        "reason": reason,
        "maximum_conclusion": MAXIMUM_CONCLUSION[terminal],
        "explicitly_forbidden": FORBIDDEN[terminal],
        "gates": {
            "interface_validity": [vars(gate) for gate in interface],
            "closure_controls": [vars(gate) for gate in closure],
            "reset_control": [vars(gate) for gate in reset],
        },
        "payload_contrast": dict(contrasts["payload_contrast"]),
        "delta_cell": registration.delta_cell,
        "delta_cell_status": (
            "a prospectively registered materiality threshold, not a numerical "
            "tolerance and not a guaranteed lower bound"
        ),
        "analytic_logit_separation": registration.analytic_logit_separation,
    }
    if terminal == NARROW_CLAIM_SUPPORTED:
        report["constructed_cell_exclusions"] = list(CONSTRUCTED_CELL_EXCLUSIONS)
        report["admissible_positive_sentence"] = registration.object_graph_scope[
            "admissible_positive_sentence"
        ]
        report["constructed_cell_note"] = (
            "The sensitivity in this cell was built in analytically. The "
            "admissible reading names the core -- the registered object graph "
            "excludes DynamicRosterEventEnv, the environment return and the "
            "environment task dynamics, so no run of it may say the environment "
            "has been exercised."
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
