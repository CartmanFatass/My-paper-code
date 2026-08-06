"""FOLR eight branches: four transplant, two reset, two wrong-owner.

Sequence 01, component 5 of the object graph External Pro required in ruling
``FOLR_S03_BINDING_SELECTED``.

WHY EIGHT AND NOT SIX
---------------------
    Six kernels are logically sufficient given a complete extensional closure
    proof.

    Eight kernels are the selected executable design for this repository, whose
    current types and interfaces do not yet provide that proof by construction.

The two extra branches are the information-matched wrong-owner null ``W_0, W_1``,
which the reset null cannot supply:

    Reset removes the information whose routing is being tested, so it is not
    information-matched to the S03 transplant.

WHAT EACH BRANCH IS
-------------------
``K_{p,b}``  transplant.  Restore common pretreatment snapshot ``S_b``, install
             payload ``h_p`` into the target's ``high_hidden`` at the registered
             write point, capture the target's first kernel.

``R_b``      complete reset.  Run provenance history ``b``, then build a FRESH
             runtime from the registered manifest (target at ``h_neutral``) and
             capture.  Tests that the reset construction is branch-invariant.

``W_p``      wrong owner.  Restore the canonical snapshot, hold the target at
             ``h_neutral``, install ``h_p`` into ``records[shadow].high_hidden``,
             capture the target's kernel.  Requires ``W_0 = W_1``.

THE CRITIC READS WHAT THE ACTOR DOES NOT
----------------------------------------
``_process_frontier`` evaluates ``event_critic.values(...)`` over the whole
active ``high_hidden`` array *before* the target's logits.  So in ``W_p`` the
shadow's payload genuinely moves ``old_owner_value``.  Pro anticipated this and
fixed the comparison accordingly:

    the direct outcome compared is the target probability vector and its
    actor-preimage digest, not complete equality of every critic-only row field.

and required that the target hold no open trace, so no callback or ledger
mutation can route that critic value back toward the actor.  Both are enforced:
``normalize_to_manifest`` clears open traces, and the comparison helpers in
``s03_binding`` operate on probabilities.

NO RANDOMNESS REACHES THE KERNEL
--------------------------------
``teacher_order`` puts the target at position 0, so the frontier permutation RNG
is never drawn.  ``teacher_actions`` covers every frontier owner, so the action
RNG is never drawn -- the row's ``policy_action_uniform`` stays ``None``, which
is the mechanical witness.  The opportunity-gap draw happens after the capture
point within the same token.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np

from ha_ctse_process import variable_roster_event as vre
from ha_ctse_process.variable_roster_event_types import MembershipTransaction

from experiments.candidates.folr_core import branch_snapshot as bs
from experiments.candidates.folr_core import registration as reg
from experiments.candidates.folr_core import reset_manifest as rm
from experiments.candidates.folr_core import s03_binding as sb

RAW_OUTPUT_BINDING = "folr_core.branches.v1"

TRANSPLANT = "TRANSPLANT"
RESET = "RESET"
WRONG_OWNER = "WRONG_OWNER"


@dataclass(frozen=True)
class BranchSpec:
    name: str
    kind: str
    payload_slot: str | None
    provenance_branch: int | None


BRANCHES: tuple[BranchSpec, ...] = (
    BranchSpec("K_0_0", TRANSPLANT, sb.PAYLOAD_ZERO, 0),
    BranchSpec("K_1_0", TRANSPLANT, sb.PAYLOAD_ONE, 0),
    BranchSpec("K_0_1", TRANSPLANT, sb.PAYLOAD_ZERO, 1),
    BranchSpec("K_1_1", TRANSPLANT, sb.PAYLOAD_ONE, 1),
    BranchSpec("R_0", RESET, None, 0),
    BranchSpec("R_1", RESET, None, 1),
    BranchSpec("W_0", WRONG_OWNER, sb.PAYLOAD_ZERO, None),
    BranchSpec("W_1", WRONG_OWNER, sb.PAYLOAD_ONE, None),
)


@dataclass(frozen=True)
class BranchResult:
    spec: BranchSpec
    kernel: sb.DirectKernel
    row: Any
    evidence: Mapping[str, Any]


# ---------------------------------------------------------------------------
# Driving the runtime
# ---------------------------------------------------------------------------


def _expire_gaps(core: vre.VariableRosterEventCore) -> None:
    """Tick physical time until every active owner is due again."""
    for _ in range(64):
        if all(
            int(record.active_gap_remaining or 0) <= 0
            for record in core.records.values()
            if record.status == vre.ACTIVE
        ):
            return
        core.complete_primitive_transition(0.0)
    raise RuntimeError("FOLR provenance history failed to expire the opportunity gaps")


def _frontier_transaction(
    core: vre.VariableRosterEventCore, manifest: rm.ResetManifest
) -> MembershipTransaction:
    pre = rm.boundary_snapshot(
        manifest, physical_time=core.physical_time, frontier=()
    )
    post = rm.boundary_snapshot(manifest, physical_time=core.physical_time)
    return MembershipTransaction(pre, (), post)


def run_provenance_history(
    core: vre.VariableRosterEventCore,
    registration: reg.Registration,
    *,
    branch: int,
) -> None:
    """Two genuinely different pretreatment histories.

    They differ in the number of committed tokens, the teacher actions taken,
    the resulting hidden states, the ledger contents, the physical history and
    the **opportunity** RNG consumption state.

    They do NOT differ in all three RNG streams, and an earlier version of this
    docstring wrongly said they did.  Pro:

        teacher_order bypasses frontier sampling and teacher_actions bypasses
        action sampling. Only the opportunity stream advances during those
        histories.

    That is by design -- it is the same property the freshness certificate
    relies on to show no action or frontier draw preceded the capture -- but it
    means the divergence between B=0 and B=1 is narrower than "all three
    streams" claimed, and the claim is corrected rather than restated.

    ``normalize_to_manifest`` then puts the registered actor-read set back, so
    what survives into the capture is exactly the residue the registered
    normalization profile permits -- and ``K_{p,0} = K_{p,1}`` tests that none
    of that residue reaches the kernel.
    """
    manifest = registration.manifest
    keys = tuple(manifest.frontier)
    n_skills = int(manifest.architecture["n_skills"])
    rounds = 1 if branch == 0 else 2
    for index in range(rounds):
        _expire_gaps(core)
        core.apply_transaction(
            _frontier_transaction(core, manifest),
            teacher_order=keys,
            teacher_actions={
                key: (index + branch + position) % n_skills
                for position, key in enumerate(keys)
            },
        )
        core.complete_primitive_transition(float(index + branch))


def common_snapshot(
    registration: reg.Registration, *, branch: int
) -> bs.CoreSnapshot:
    """``S_b``: one pretreatment state shared by both payload arms of branch b."""
    core = rm.construct_reset_runtime(registration.manifest)
    run_provenance_history(core, registration, branch=branch)
    rm.normalize_to_manifest(
        core, registration.manifest, profile=registration.normalization_profile
    )
    return bs.capture(core)


def _payload_intervention(
    registration: reg.Registration, *, spec: BranchSpec
) -> Any:
    """The callable installed at Pro's registered write point."""
    binding = registration.binding
    target = binding.target_lifecycle_key
    shadow = binding.shadow_lifecycle_key
    if spec.kind == RESET:
        return None
    payload = binding.payload(spec.payload_slot)
    if spec.kind == WRONG_OWNER:
        neutral = binding.payload(sb.PAYLOAD_NEUTRAL)

        def wrong_owner(core: vre.VariableRosterEventCore) -> None:
            core.records[target].high_hidden = neutral.copy()
            core.records[shadow].high_hidden = payload.copy()

        return wrong_owner

    def transplant(core: vre.VariableRosterEventCore) -> None:
        core.records[target].high_hidden = payload.copy()

    return transplant


def execute_branch(
    registration: reg.Registration, spec: BranchSpec
) -> BranchResult:
    """Run one branch end to end and collect its freshness evidence."""
    manifest = registration.manifest
    target = registration.binding.target_lifecycle_key

    if spec.kind == RESET:
        # Run the history so the process really has lived through branch b,
        # then discard it: the reset constructor never sees that core.
        historical = rm.construct_reset_runtime(manifest)
        run_provenance_history(historical, registration, branch=spec.provenance_branch)
        core = rm.construct_reset_runtime(manifest)
    else:
        branch = (
            registration.canonical_provenance_branch
            if spec.provenance_branch is None
            else spec.provenance_branch
        )
        core = rm.construct_reset_runtime(manifest)
        bs.restore(core, common_snapshot(registration, branch=branch))

    # Taken AFTER the core reaches its pretreatment state, so the freshness
    # certificate can compare "at restoration" against "just before capture"
    # through one uniform object for all three branch kinds.
    restored = bs.capture(core)
    snapshot_digest = restored.digest()
    model_digest_before = sb.model_state_digest(core.commitment_model)
    sink = sb.KernelCaptureSink(
        binding=registration.binding,
        model_digest=model_digest_before,
        snapshot_digest=snapshot_digest,
    )
    core.install_kernel_capture(sink)
    core.install_preframe_intervention(_payload_intervention(registration, spec=spec))

    rng_before = {
        name: dict(getattr(core, name).bit_generator.state)
        for name in bs.RNG_FIELDS
    }
    evidence: dict[str, Any] = {
        "branch": spec.name,
        "kind": spec.kind,
        "common_snapshot_digest": snapshot_digest,
        "model_state_digest_before": model_digest_before,
        "restored_high_ledger_length": len(restored.mutable_state["high_ledger"]),
        "restored_high_ledger_digest": bs.digest_of(
            restored.mutable_state["high_ledger"]
        ),
        "high_ledger_length_before": len(core.high_ledger),
        "high_ledger_digest_before": bs.digest_of(core.high_ledger),
        "frontier_size": len(manifest.frontier),
        "low_ledger_length_before": len(core.low_ledger),
        "low_chunk_boundaries_before": len(core.low_chunk_boundaries),
        "target_open_trace_before": core.records[target].open_event_trace is not None,
        "pending_membership_transaction_before": (
            core.pending_membership_transaction is not None
        ),
        "rng_states_before": rng_before,
        "manifest_rng_states": {
            "opportunity_rng": dict(manifest.rng_states["opportunity_rng_state"]),
            "frontier_rng": dict(manifest.rng_states["frontier_order_rng_state"]),
            "action_rng": dict(manifest.rng_states["policy_action_rng_state"]),
        },
        "teacher_order_supplied": True,
        "runtime_mode": core.runtime_mode,
    }

    result = core.apply_transaction(
        _frontier_transaction(core, manifest),
        teacher_order=tuple(manifest.target_token_order),
        teacher_actions=dict(registration.teacher_actions),
    )

    row = next(
        candidate
        for candidate in result.token_rows
        if candidate.owner_lifecycle_key == target
    )
    evidence.update(
        {
            "sampled_order": tuple(result.sampled_order),
            # The presentation order of `active_high_hidden`, so the execution
            # gate can check that the shadow index resolves to the registered
            # owner rather than to whoever happens to sit at that position.
            "active_lifecycle_keys": tuple(row.active_lifecycle_keys),
            "token_position": int(row.token_position),
            "policy_action_uniform": row.policy_action_uniform,
            "exact_legal_mask": row.exact_legal_mask.tolist(),
            "high_ledger_length_after": len(core.high_ledger),
            "low_ledger_length_after": len(core.low_ledger),
            "low_chunk_boundaries_after": len(core.low_chunk_boundaries),
            "model_state_digest_after": sb.model_state_digest(core.commitment_model),
            "rng_states_after": {
                name: dict(getattr(core, name).bit_generator.state)
                for name in bs.RNG_FIELDS
            },
            "pending_membership_transaction_after": (
                core.pending_membership_transaction is not None
            ),
            "target_membership_epoch": int(row.membership_epoch),
            # Pro §6C asks that the target AND shadow indexes resolve to the
            # registered owners *and epochs*; the target's epoch is on the row,
            # the shadow's is not, so it is read from the record.
            "shadow_membership_epoch": int(
                core.records[registration.binding.shadow_lifecycle_key].membership_epoch
            ),
            "core": core,
        }
    )
    return BranchResult(spec=spec, kernel=sink.first(), row=row, evidence=evidence)


def execute_all(registration: reg.Registration) -> dict[str, BranchResult]:
    """All eight branches, keyed by name."""
    return {spec.name: execute_branch(registration, spec) for spec in BRANCHES}


# ---------------------------------------------------------------------------
# The contrasts Pro registered
# ---------------------------------------------------------------------------


def contrasts(results: Mapping[str, BranchResult]) -> dict[str, Any]:
    """The fixed-payload nulls, the wrong-owner null, the reset null, and the
    positive discriminator -- as raw measurements with no verdict attached.

    Routing these numbers to a conclusion is ``outcome.py``'s job, and the
    scientific reading of that conclusion is External Pro's.
    """

    def equal(left: str, right: str) -> dict[str, Any]:
        a, b = results[left].kernel, results[right].kernel
        return {
            "pair": [left, right],
            "probabilities_bitwise_equal": sb.kernels_bitwise_equal(a, b),
            "actor_preimage_digests_equal": (
                a.actor_preimage_digest == b.actor_preimage_digest
            ),
            # Pro §6F: "Equal kernels can arise from cancellation despite unequal
            # reset inputs", so the input-side digests are reported for every
            # pair rather than only where a null happens to be expected.
            "common_snapshot_digests_equal": (
                a.common_snapshot_digest == b.common_snapshot_digest
            ),
            "model_state_digests_equal": (
                a.model_state_digest == b.model_state_digest
            ),
            "infinity_norm": sb.kernel_infinity_norm(a, b),
        }

    def closure_at_fixed_b(left: str, right: str) -> dict[str, Any]:
        """Everything except S03 must be identical ACROSS the payload contrast.

        Pro called this "the most important missing gate":

            It does not verify the more fundamental identifying closure at fixed
            B: D(K_{0,0}) = D(K_{1,0}), D(K_{0,1}) = D(K_{1,1}). Without those
            two gates, a positive contrast could be accompanied by an
            unrecognized non-S03 input difference.

        The fixed-payload nulls run the other way -- they hold the payload and
        vary the provenance branch -- so neither implies the other.  This one is
        the identifying assumption: if it fails, the measured contrast cannot be
        attributed to the payload at all.

        ``actor_preimage_digest`` excludes ``pre_token_high_hidden`` by
        construction (it *is* S03), which is what makes the equality
        non-vacuous here.
        """
        a, b = results[left], results[right]
        left_kernel, right_kernel = a.kernel, b.kernel
        return {
            "pair": [left, right],
            "actor_preimage_digests_equal": (
                left_kernel.actor_preimage_digest
                == right_kernel.actor_preimage_digest
            ),
            "common_snapshot_digests_equal": (
                left_kernel.common_snapshot_digest
                == right_kernel.common_snapshot_digest
            ),
            "model_state_digests_equal": (
                left_kernel.model_state_digest == right_kernel.model_state_digest
            ),
            "legal_masks_equal": (
                a.evidence["exact_legal_mask"] == b.evidence["exact_legal_mask"]
            ),
            "target_identity_equal": (
                (
                    left_kernel.owner_lifecycle_key,
                    left_kernel.membership_epoch,
                    left_kernel.token_position,
                )
                == (
                    right_kernel.owner_lifecycle_key,
                    right_kernel.membership_epoch,
                    right_kernel.token_position,
                )
            ),
        }

    return {
        "raw_output_binding": RAW_OUTPUT_BINDING,
        # Pro: "The two fixed-payload nulls are K_{0,0} = K_{0,1}, K_{1,0} = K_{1,1}"
        "fixed_payload_nulls": [equal("K_0_0", "K_0_1"), equal("K_1_0", "K_1_1")],
        # Pro §6A: the identifying closure, at fixed B across the payload arms.
        "payload_closure": [
            closure_at_fixed_b("K_0_0", "K_1_0"),
            closure_at_fixed_b("K_0_1", "K_1_1"),
        ],
        # Pro: "Add two information-matched wrong-owner branches ... require W_0 = W_1"
        "wrong_owner_null": equal("W_0", "W_1"),
        # Pro: reset kernels are calibration controls; require R_0 = R_1
        "reset_null": equal("R_0", "R_1"),
        # Pro: "The positive discriminator is ||K_{1,b} - K_{0,b}||_inf > delta_cell"
        "payload_contrast": {
            "b0": sb.kernel_infinity_norm(
                results["K_1_0"].kernel, results["K_0_0"].kernel
            ),
            "b1": sb.kernel_infinity_norm(
                results["K_1_1"].kernel, results["K_0_1"].kernel
            ),
        },
    }


if __name__ == "__main__":  # pragma: no cover
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--development-cell",
        action="store_true",
        help="run against the DEVELOPMENT_ONLY decoy cell",
    )
    arguments = parser.parse_args()
    if not arguments.development_cell:
        raise SystemExit(
            "The registered cell must not be executed before External Pro has "
            "approved the frozen registration: 'No cell may be selected, "
            "replaced or modified after observing any of the main, reset or "
            "wrong-owner kernels.' Use --development-cell."
        )
    registration = reg.development_registration()
    print(json.dumps(contrasts(execute_all(registration)), indent=2, default=str))
