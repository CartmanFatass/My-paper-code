# VSP02-B5R1 Windows-resource-admission freeze packet

Status: `REPAIR_FRESH_CANDIDATE`

This packet is the public, repo-relative scientific freeze for the fresh
candidate requested after the B5 closure.  It records a resource-admission
repair only; it is not a result and it does not reopen the B5 question.

## Provenance and closure

- Direction: `CAND-VSP-02`.
- Prior source/index: `experiments/candidates/vsp_02/vsp02_b5_full_adam_state_continuity.py`
  and `docs/research/candidates/vsp_02/VSP02_B5_FULL_ADAM_STATE_CONTINUITY_CODE_SCIENCE_INDEX.md`.
- Corrected internal handoff SHA-256: `86e2327e1895be8a9a7ced0304b62c9b4833e82943bfba0012c4398ae16be0f8`.
- Accepted B4 signature pattern: `CREDIT_SIGN_SELF_FEEDBACK` with the
  paired B4 endpoint and its retained-row, first-match branch discipline.
- B5 closure literal: `B5_INVALID_OR_INACTIVE`.

The B5 closure supplied no scientific evidence, no validated result, and no
promotion or retirement evidence.  It authorizes neither retry nor rescue,
and no External Pro review was performed for that closure.  The consumed B5
namespace and any artifacts from it remain closed and are not inputs to this
candidate.

## Fresh candidate and unchanged science

The fresh candidate is `CAND-VSP-02@adversarial-revision-v10`, with treatment
`VSP02-B5R1-FULL-ADAM-STATE-CONTINUITY` and registered full
`VSP02-B5R1-REGISTERED-FULL-01`.  It is a full run, not a preview or a
shadow.  Its two arms remain exactly `ADAM_CARRY` and `ADAM_RESET`.

Fresh units are `VSP02-B5R1-U01` through `VSP02-B5R1-U05`; fresh paired roots
are `22051001` through `22051005`; and the seed prefix is exactly
`VSP02-B5R1-V1\0`.  The assignment, tape, checkpoint, batch, model, optimizer,
and result namespaces are all fresh.  No B1--B5 or G52 root, seed, tape,
checkpoint, batch, model, optimizer, or result may be reused.

All scientific literals remain byte-for-byte those frozen for B5: one common
update-0 oracle-sign step; complete Adam carry versus canonical Adam reset;
the common update-1 batch, forward values, loss, raw and clipped gradients,
pre-clip norm and clip factor; later updates as causal descendants; the
oracle firewall; immutable batches; fixed arm order and noninterference; the
address-indexed exogenous tape; the held-out common evaluation panel; exact
success requiring all cue-0 rows to choose HOLD, all cue-1 rows to choose
RELEASE, and no argmax tie; and the six exhaustive branches, in this order:

1. `B5_INVALID_OR_INACTIVE`
2. `B5_NEITHER_ARM_EXACT_SUCCESS_ON_PANEL`
3. `B5_CARRY_DIRECTION_DISCORDANCE_ONLY`
4. `B5_RESET_DIRECTION_DISCORDANCE_ONLY`
5. `B5_NO_EXACT_ENDPOINT_LOCALIZATION_ON_PANEL`
6. `B5_BIDIRECTIONAL_PAIRED_ROOT_TAPE_DISCORDANCE`

The counts and caps are unchanged: one common update plus 127 updates per arm
per root; 128 effective steps per arm; 1,275 optimizer steps; 10,200 training
episodes; 1,280 evaluation episodes; ten final checkpoints; 57,400 environment
transitions; one pool unit; 30 CPU minutes; 2 GiB peak memory; and exactly one
result-bearing full with zero retry, rescue, sweep, extra root, checkpoint,
threshold, or boundary.  Claims remain finite paired-root/tape local only.
There is no population, superiority, necessity, equivalence, component,
mediator, transfer, generic-Adam, B4-explanation, or promotion claim.

## Sole admission delta

The sole delta from the B5 implementation contract is the Windows resource
admission measurement: the hard-cap check obtains process RSS through the
Windows FFI (`GetProcessMemoryInfo`) and records the verified working-set
sample in the preclaim receipt.  No training, evaluation, branch, seed,
identity, scientific predicate, or result schema changes.  The FFI call is
only an admission/readiness gate; it cannot create evidence and cannot rescue
an over-cap or unreadable run.

The real host must emit a preclaim receipt proving the FFI path, process
identity, memory sample, CPU-time sample, configured caps, and clean zero-start
state before any full claim.  A missing, unreadable, stale, or non-Windows
receipt is an admission failure, not a scientific result.

## Execution and review gate

CM authority is limited to implementation and bounded readiness.  Root owns
the clean source, publication ancestry, exclusive namespace, runtime dispatch,
and Git binding.  No full run is permitted until Root re-consults the same
direction EM after implementation/readiness evidence.  The reserved result
must remain absent until the authorized sole full completes.

External Pro is `NOT_MATERIAL` before a result: it is not a code, readiness,
or admission reviewer.  If a valid result is later produced, the scientific
convergence review must use the existing VSP02 session/page, with the result
and commit-pinned public inputs, and must not use an unrelated or mixed
direction session.  No Answer-now/Continue/Retry/Stop control is part of this
packet.

publication_commit=PENDING_ROOT_PUBLICATION
