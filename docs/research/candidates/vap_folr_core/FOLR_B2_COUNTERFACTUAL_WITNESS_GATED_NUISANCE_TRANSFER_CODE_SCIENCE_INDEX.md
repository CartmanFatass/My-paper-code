# FOLR-B2 counterfactual-witness gated nuisance transfer: code-science index

This index binds the frozen `CAND-VAP-FOLR-CORE@constructive-revision-v6`
question to the implementation surfaces that can produce one FOLR-B2 result.
It does not state a scientific outcome and does not authorize a run.

## Frozen proposition and admission

FOLR-B2 asks whether the already-specified revision-v5 lifecycle rule—retain
only counterfactually invariant survivor-private state in S03, invalidate
partner-scoped state, and rebuild it in S04—improves finite-budget transfer
from diagonal old/new partner-bit compositions to changed compositions.  The
comparison is against an isomorphic generic memory and a complete-reset
calibration arm on one three-transition host.

`MatchedWitnessActor` and `build_frozen_manifest` in
`experiments/candidates/folr_core/counterfactual_witness_gated_nuisance_transfer.py`
freeze the admission witness.  Both learned arms have the same 16-dimensional
memory, ordered parameters, initialization tensors, learned writer/update/
reader/WAIT/action-head call trace, descriptors, examples, uniforms, optimizer
and update count.  `fixed_lifecycle_routing_after_identical_learned_candidates`
is recorded as the sole learned-arm delta.  Drift fails in
`_validate_manifest` or `validate_train` before a full result can validate.

## Host and lifecycle observables

`CounterfactualWitnessHost` in
`experiments/candidates/folr_core/counterfactual_witness_gated_nuisance_transfer_host.py`
uses the public typed membership DTOs for one real atomic
`TERMINAL_LEAVE(old_partner) + JOIN(new_partner)` transaction.  The continuing
`owner_t@0` record and epoch are checked directly.  Each ordinary t1 writer
emits an immutable `StateProvenance` containing state scope, owner key/epoch,
source-partner binding and dependencies, writer-call identity and descriptor
digest.  `derive_counterfactual_lineage` applies the concrete departed-partner
to joined-partner substitution to those bindings and derives roster/partner
invariance from binding equality and survival.  No arm label supplies a
witness.  `CounterfactualLineage` and `RoutingWitness` retain both predicate
results rather than inferring a blocker from check order:

- survivor-private owner lineage has roster and partner substitution
  invariance and may retain S03 `[0:8]`;
- old-partner lineage names its source partner, fails partner-substitution
  invariance, and is invalidated;
- the serialized replacement witness proves S04 is absent before transition
  2, while a separate post-t2 witness proves the new-partner S04 `[8:16]`
  rebuild; neither witness overwrites the other;
- transition 3 reads only the selected owner-memory backend, emits one complete
  four-action kernel, and clears every lifecycle record on termination.

The host public observation excludes bits, arm, regime, identity and role.
Partner identity/role descriptors are supplied identically to the learned
arms through `_descriptor`; no descriptor contains a bit, answer or branch.

## Data, optimization and activity identity

`registered_config` freezes arms in the order
`TYPED_WITNESS_S03_S04`, `ISOMORPHIC_GENERIC_MEMORY`, `COMPLETE_RESET`, master
seeds 94031–94038, 32 batches of 64 diagonal training episodes per arm/seed,
and two 512-episode evaluation regimes.  `build_frozen_manifest` makes each
training batch exactly 16 examples of each `(s,n_old,n_new)` diagonal cell and
each evaluation regime exactly 128 examples of each allowed cell.  Identities
and roles cycle independently within every bit cell, so CHANGED withholds only
composition.

`_expected_sidecar_rows` constructs canonical train/evaluation maps from the
frozen manifest.  Validators compare every sidecar row across phase,
episode/order, batch/regime, pair index, root, all three bits, both identities,
both roles, sampling uniform and every RNG identity; missing, duplicate, extra
or changed rows fail.  `_validate_identity_role_independence` conditions each
old/new identity and role position on both values of `s`, `n_old` and `n_new`,
rather than accepting global set coverage.

The full identity is exactly 24 actor runs, 49,152 training episodes, 147,456
training transitions/policy calls, 768 learner/trainer/Adam updates, 24,576
evaluation episodes, 73,728 evaluation transitions/policy calls, and 73,728
episodes / 221,184 transitions-policy calls overall.  `_validate_mode`,
`_expected_counts`, `validate_train`, `validate_evaluation`, and
`validate_result` independently enforce that identity.  A technical smoke has
its own exact configuration and always emits
`TECHNICAL_ONLY_NO_SCIENTIFIC_DECISION` with
`scientific_terminal_admitted=false`.

## Lossless evidence and decision binding

`_episode_batch` records every action, reward, decoded component, lifecycle
witness, identity/role/event manifest, RNG identity, memory digest and complete
pre-sampling kernel.  `_kernel_payload` stores both logits and probabilities
as numeric float32 values plus exact little-endian bytes and SHA-256 digests.
Its row-bound chronology token is created before `_sample_actions`; the sampler
must consume that capture, and validation recomputes both byte views, token,
uniform-derived action and capture-before-sampling sequence.  `validate_train` and
`validate_evaluation` scan the lossless gzip JSONL sidecars and reject missing
rows, nonfinite kernels, count or cell imbalance, public-bit dependence,
stale lineage, second carriers, caches, pending actions, unexpected updates or
non-final checkpoints.

`validate_evaluation` recomputes every arm/seed/regime metric and every
composition, old/new identity and old/new role group row directly from the
lossless sidecar.  `_build_paired_rows` is a pure reconstruction of all three
complete counterfactual tables from the retained 2×2×2 evaluation cube; it
performs no environment activity.  `validate_result` compares every retained
pair row and summary against that reconstruction.  `_decision` implements the
nine-branch precedence; branch 6 requires an absolute learned-arm gap strictly
below the existing 0.08 material boundary, while branch 7 owns generic
advantages at or above 0.08 or typed failure, so the predicates are mutually
exclusive.  Correct-action probability is indexed from the retained
four-action kernel; it is never substituted by mean return.

`analyze` always writes and fully validates the canonical run-root result and
all run-root bindings first.  An optional external result is then written
atomically and validated against an explicit canonical `output_root`; its
destination directory can never replace the run root for artifact resolution.

## Focused proof map

`tests/experiments/candidates/folr_core/test_counterfactual_witness_gated_nuisance_transfer.py`
checks:

- typed atomic replacement and explicit survivor/partner lineage witnesses;
- tensor-exact architecture and initialization matching before routing;
- exact typed old-partner and reset survivor kernel invariances;
- diagonal training balance, complete evaluation cube and frozen caps;
- wrong-provenance, exact-manifest-row and conditioned identity/role failures;
- coordinated metric/result tampering and pair-sidecar tampering;
- all nine decision branches plus the exact 0.08 branch-6/7 boundary;
- logits/probability byte capture and sampling chronology tampering;
- direct correct-action probability decoding from the full kernel;
- one CLI train→evaluate→analyze technical-only smoke, external-result
  lifecycle validation and all validators;
- the narrow CLI surface, with no sweep entry.

The production entry is
`scripts/run_folr_b2_counterfactual_witness_gated_nuisance_transfer.py`.

## Boundaries and alternatives

The package contains no B1 replay, critic, recurrence outside the memory
interface, attention, replay, history stack, cached kernel/action/logit,
checkpoint selection, preliminary scientific run, retry, rescue, sweep,
fourth arm, additional seed/composition, hypothetical transition, C treatment
or External Pro request.

Even a positive branch can support only a finite-budget, host-local inductive
bias of the pre-specified routing rule.  An isomorphic generic memory may learn
the same routing with more optimization, and the diagonal-to-changed split may
favor pre-specified typed structure.  A failure does not establish that typed
state is useless outside this host or that generic memory is universally
sufficient.

## Accepted full result

Conclusion: the sole authorized full package is mechanically accepted and its
canonical result is published without alteration.  The accepted run is
`folr_b2_counterfactual_witness_gated_nuisance_transfer_e533993c_r1` from
source commit `e533993cb842657a75a0962047bd2dfa52b6cf70`.  Its Experiment
Operator receipt is `COMPLETE`; `validate-train --require-full`,
`validate-evaluate --require-full`, and `validate-result --require-full` each
passed.  The clean-candidate source-readiness receipt is schema-3 `PASSED`,
attempt `folr_b2_e533993c_r2`, for the same candidate commit.

The accepted full records 24 actor runs; 49,152 training episodes; 24,576
evaluation episodes; 73,728 complete episodes; 221,184 environment transitions
and policy calls; 768 learner/trainer/optimizer updates; zero hypothetical
transitions; 24 final checkpoints; and all five admission predicates true.
Its unique frozen code-produced branch is
`RESET_LEAK_OR_NEW_PARTNER_CALIBRATION_FAILED`.

The public canonical result is
`docs/research/candidates/vap_folr_core/FOLR_B2_COUNTERFACTUAL_WITNESS_GATED_NUISANCE_TRANSFER_RESULT.json`.

### Publication claim boundary

This branch is a host-local, finite-budget code decision only.  Publication does
not claim promotion, retirement, C readiness, formal validity, generic
impossibility, cross-task generalization, sibling-direction meaning, or
Explorer scientific intake.
