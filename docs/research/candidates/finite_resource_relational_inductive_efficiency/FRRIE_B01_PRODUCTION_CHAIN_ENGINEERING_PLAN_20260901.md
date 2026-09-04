# FRRIE B01 production-chain engineering plan

Date: 2026-09-01
Scope: engineering plan only; no production launch authority

## Current disposition

The arithmetic/native/collector milestone was integrated and pushed as commit
`1fc04ab3`.  A subsequent committed-source degraded TEST smoke exposed one
outcome-blind primitive-validation defect: the producer used the ABI's FP32
waste ratio while the artifact validator duplicated it with Python binary64
division.  The shared authoritative FP32 primitive-to-return repair is now
commit-ready: the bounded B01 suite passed `94 passed, 3 deselected`, and the
independent reviewer returned `CLEAN`.  The deselected cases are actual native
invocations.  All three quarantined integrated TEST attempts remain non-result
technical evidence and are not read, resumed, or salvaged.

Production remains `REPAIR_REQUIRED`.  No production CLI exists, and the
complete panel and descriptive analysis remain fail-closed.  This plan must not
be used to create roots, RNG masters, models, optimizers, checkpoints, or
results.  Every later implementation wave must first restore a commit-bound,
scoped-clean FRRIE source milestone after its own changes are integrated.

## Frozen engineering target

Build one non-injectable, source-bound B01 chain that executes the unchanged
scientific contract:

- initial seeds `001,002,003`; extension seeds `004,005` only through the
  immutable parent-initial continuation contract;
- 512 paired updates per seed, with 64 episodes/update in literal `(9,15)*32`
  order and exactly 4,928 training slots/arm/update;
- paired checkpoints at updates `0,32,64,128,256,512`;
- learned evaluation for both arms, all six checkpoints, rosters
  `6,9,15,21`, both interventions, and 256 episodes/cell;
- one Uniform intact cell for N=9 and N=15 per seed, reused horizontally;
- direct support census, ordered-28 quantities, intact-versus-shadow V rows,
  symmetric between-arm action-TV sidecar, and post-contact parameter-distance
  trace under their already frozen contracts;
- create-once seed-local artifacts, immutable initial/extension merge, and
  process-tree telemetry across admission, build/load, train, checkpoint,
  evaluation, reduction, and publication.

No scientific formula, threshold, branch, seed law, RNG address, dtype,
checkpoint, contact definition, or work count is changed by this wave.

## Ownership slices

Only one semantic implementer may own a slice at a time.  Shared files are
integrated serially by CM.

### Slice A — formal runner and seed-worker effects

Owned paths:

- new `b01/production_runner.py`
- `b01/contract.py`, `b01/preflight.py`, `b01/lifecycle.py`
- new `test_production_runner_contract.py`

Deliverables:

- a non-injectable formal worker that accepts a validated manifest and one
  planned seed locator, then performs its own fresh 4 GiB admission immediately
  before native build/load, RNG, model, optimizer, or output creation;
- actual HEAD plus scoped-FRRIE clean-source binding before Effects;
- initial three-way and extension two-way bounded seed pools, capacity four,
  deterministic manifest-order collection, seed-local roots, and failure
  quarantine;
- no caller-supplied adapter, worker function, seed-label override, admission
  receipt, code revision, or production-token Boolean;
- `launch_capable=false` until every downstream validator below is complete and
  Root records a commit-bound source milestone.

### Slice B — full 512-update paired trainer

Owned paths:

- `b01/batch_collector.py`, `b01/trainer.py`, `b01/checkpoint.py`
- new `b01/training_runner.py`
- trainer, collector, checkpoint, and resume tests

Deliverables:

- the production native-width-32 collector on every update, Torch threads=1,
  paired transactional update/rollback, and exact direct loss-reduction receipt;
- streamed per-update paired state/work/projection shards rather than an
  in-memory 512-update mega-object;
- literal checkpoint write, reopen, decode, temporary restore, and resume at
  all six legal checkpoints;
- formal kappa derivation only from complete paired training shards;
- write-once parameter state/raw records for every post-contact update, with
  the Pro-final L-infinity full/beta/nonbeta contract;
- direct ledgers for factual, seven-alternative, three-audit, optimizer, native
  calls, checkpoint, and resume work.

Acceptance includes uninterrupted-versus-resume equality, pre-contact paired
byte laws including the kappa boundary, failed-second-arm rollback, exact
2,523,136 training slots/arm/seed, and no scientific early stop.

### Slice C — streamed evaluation and diagnostic capture

Owned paths:

- new `b01/evaluation_runner.py`
- `b01/tapes.py`, `b01/panel.py`
- evaluation, direct-trace, shadow, support, and diagnostic tests

Deliverables:

- canonical common addressed evaluation tapes whose bytes are identical across
  arms, cuts, and checkpoints; checkpoint is metadata only;
- package-native 12-slot learned rollouts and Uniform baseline rows;
- typed contiguous, create-once shards for the 25,088 primitive rows/seed and
  direct per-slot traces; no production mega-JSON;
- cell-level event/basin/role/legal-opportunity support census separated from
  actual action-execution census;
- intact PHY one-step semantic-column shadow inventory for ordered-28 V;
- symmetric natural-history between-arm TV sidecar with explicit pre-contact
  availability and scope-only measurement defects;
- validation replay work recorded separately from frozen scientific work.

This slice may start only after the checkpoint restore surface from Slice B is
stable.  Evaluation must run under `torch.no_grad()` and preserve model mode.

### Slice D — exact panel index and reducers

Owned paths:

- `b01/panel.py`, `b01/analysis.py`, `b01/raw_control.py`
- new `b01/panel_index.py`
- panel, ordered-28, raw-control, action-TV, and parameter-distance tests

Deliverables:

- an immutable top-level index that validates containment, exact typed shard
  descriptors, cardinalities, coordinate order, and cross-bindings before
  minting a `ValidatedCellSet`;
- exact inventories per seed: 98 cells, 25,088 primitive rows, 1,024 arm-update
  receipts, six paired checkpoint/restore receipts, and 168 ordered quantity
  values;
- direct J recomputation from DW/DE/radio/waste facts, cell-first reducers,
  cell-level nonidentification, and all 28 quantities in canonical order;
- exact V, symmetric between-arm TV, parameter-distance, and raw-control
  descriptive reducers without branch or polarity inference;
- `validate_complete_panel` and `descriptive_analysis` remain fail-closed until
  every direct inventory and cross-binding is implemented.  Candidate helpers
  never mint a production token.

### Slice E — atomic whole-chain publication and performance evidence

Owned paths:

- new `b01/production_telemetry.py`
- `b01/lifecycle.py`, `b01/cli.py`
- whole-chain transaction, cleanup, telemetry, and source-gate tests

Deliverables:

- one seed-local `.creating` transaction with post-publication literal
  readback, `.incomplete` quarantine on any failure, and no COMPLETE artifact
  when package-native cleanup fails;
- per-member process-tree CPU/I/O accounting across short-lived children,
  simultaneous RSS peak, process/thread peaks, scratch/durable high-water,
  direct build-artifact census, stage wall time, and scientific-work throughput;
- parent initial/extension merge that never rewrites initial evidence;
- final CLI exposure only after the source gate, panel validator, descriptive
  reducer, and performance disposition all pass directly.

## Critical path and integration order

1. Integrate the commit-ready primitive-to-return repair on top of the pushed
   arithmetic/native/collector baseline and require a clean scoped source gate.
2. Implement Slice A's non-effecting formal plan and fail-closed worker entry.
3. Complete Slice B through update 512, legal checkpoints, resume, and direct
   training/parameter shards using synthetic/component tests only.
4. Build Slice C on the frozen checkpoint restore and canonical tape surfaces.
5. Build Slice D against retained typed fixtures from B/C; remove the explicit
   `PRODUCTION_*_UNAVAILABLE` raises only when all exact inventories validate.
6. Wrap A-D in Slice E's transaction and telemetry, then run a fresh admitted
   bounded whole-chain performance assessment approved by DM/Root.
7. Assign exactly one performance disposition.  Long initial-three-seed launch
   is forbidden unless the actual formal chain is `PERFORMANCE_READY` and the
   source remains commit-bound and scoped-clean.

Slices B schema work and C fixture/schema work may proceed in parallel only
when they do not edit `panel.py` or share checkpoint/tape definitions.  All
`panel.py`, `analysis.py`, `lifecycle.py`, and CLI integration is serialized.

## Stop conditions

Stop and keep `REPAIR_REQUIRED` if any of the following remains: source drift;
caller-injectable formal runtime; missing worker-local admission; incomplete
512-update/resume evidence; missing one of the 98 cells; non-streamable raw
inventory; summary-only support/work/tape/checkpoint evidence; unavailable exact
ordered-28 validation; incomplete process-tree telemetry; or absent actual
whole-chain performance evidence.  Passing unit tests alone cannot upgrade the
production disposition.
