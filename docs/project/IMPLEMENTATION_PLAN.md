# HA-CTSE Active Implementation Plan

Updated: 2026-07-22
Status: IMPLEMENTATION_READY
Work ID: `event-held-commitment-battery-partial-migration-20260722-retry1`
Base/source boundary: `a2908ba578b27f5b5ce783a659ea3cfedb0c8f09`

The accepted mainline package at the source boundary is the starting
implementation state. The interrupted isolated WIP is read-only candidate
evidence: no tracked file is copied wholesale, its shortened plan is rejected,
and only individually verified symbols may be adapted. The scientific design
remains frozen. This boundary implements the accepted
`BATTERY_REQUIRES_MINIMAL_CORRECTION` causal decomposition without authorizing
formal training or registered evaluation and without changing `G`, the three
arms, treatment, model, reward, observation, task distribution, PPO objective,
seed, registered budget, threshold or result meaning.
Scientific source: `docs/research/designs/EVENT_HELD_COMMITMENT_LINK_G0.md`

## Outcome and authority

Replace the superseded noncalendar H/C/S/D executable benchmark with one
three-arm `OR`/`DUM`/`EHC` package for the controller-adopted
`EVENT_HELD_COMMITMENT_LINK_G0` source. The package must be runnable for a
short explicitly non-formal smoke and fully package the registered formal
training, evaluation and analysis contract, but this work does not launch
formal training or registered evaluation.

The adopted design is the only scientific authority. The implementation may
change only:

- `docs/project/IMPLEMENTATION_PLAN.md`;
- `ha_ctse_process/`;
- `scripts/`;
- `tests/`.

No Git mutation, experiment launch, reward/observation/task change, compatibility
adapter, successor route or project-control edit is authorized.

## Behavioral-battery partial-migration repair

Replace the active two-branch natural-fork measurement surface, not the frozen
training or primary-estimand path, with one held-out evaluation-only causal
audit. Delete the active `fork_*`/`natural_fork` API and schema rather than
preserving an alias. The only active branch names, in order, are:

```text
KEEP_HELD_MARK
RENEW_DERANGED_MARK
RENEW_CANDIDATE_MARK
```

`KEEP_HELD_MARK` forces `KEEP` with the focal row's installed mark;
`RENEW_CANDIDATE_MARK` forces `RENEW` with that row's already-drawn candidate
mark; and `RENEW_DERANGED_MARK` forces `RENEW` with a candidate mark donated by
another selected row in the same `(replicate, natural_action)` stratum. No
branch adds a draw, changes likelihood or gradient exposure, or enters
training. All three branches start from the same pre-opportunity state and use
the existing cloned CRN continuation contract.

Selection retains the existing registered quota, seeds and outcome-blind
selection stream. Build one compact pre-outcome raw event trace at the actual
collector boundary. It contains only the frozen selection coordinates,
natural event kind, installed mark and unmasked candidate `u/z` as exact
float32 payloads plus their origin binding; it contains no reward, terminal
outcome, future trajectory or utility. The validator independently derives
the eligible inventory, action strata, selected keys and donor mapping from
this trace. Self-digested eligible/selected summaries are never authority.

Within each replicate and natural-action stratum, sort selected rows by the
frozen selection key and cyclically shift the exact candidate-mark payload by
one position. Persist recipient key, donor key, donor candidate `u/z` float32
bytes/digest and mapping position. The mapping consumes no RNG, has no fixed
key, preserves the selected candidate-mark multiset byte-for-byte and fails
closed on missing, duplicate, cross-stratum, re-signed or coherently tampered
trace/donor evidence.

For a natural `KEEP` row freeze:

```text
C_total  = U(KEEP_HELD_MARK) - U(RENEW_CANDIDATE_MARK)
C_timing = U(KEEP_HELD_MARK) - U(RENEW_DERANGED_MARK)
C_mark   = U(RENEW_DERANGED_MARK) - U(RENEW_CANDIDATE_MARK)
```

For a natural `RENEW` row freeze:

```text
C_total  = U(RENEW_CANDIDATE_MARK) - U(KEEP_HELD_MARK)
C_timing = U(RENEW_DERANGED_MARK) - U(KEEP_HELD_MARK)
C_mark   = U(RENEW_CANDIDATE_MARK) - U(RENEW_DERANGED_MARK)
```

Compute all three contrasts by their direct frozen utility subtractions. Record
and independently recompute the binary64 closure residual
`abs(C_total-(C_timing+C_mark))`; admit only the deterministic rounding bound
`4 * max(ulp(contrasts and branch utilities))`. This is an arithmetic evidence
rule, not a scientific threshold. `C_total` replaces only the old
`A_KEEP/A_RENEW` measurement input under the same frozen interval and
point-floor gates; timing and mark components are separately reported causal
interpretations and do not change first-match result precedence.

Persist the full `TrackingOutcome` for each branch: tracking/completion values,
utility, terminal reward, integer numerators/denominators, roster sizes and the
complete reward trace. Validation reconstructs tracking, completion, utility
and terminal-reward equality from the raw leaves, recomputes every contrast and
rejects outcome/utility/contrast co-tampering. Natural-branch equality compares
the complete reconstructed outcome, not utility alone.

Keep the existing strict checkpoint schema transition and restore identity,
but make every restore metric an exact non-boolean finite nonnegative numeric
leaf `<=1e-7`. Coverage includes saved Python, global NumPy, CPU and every CUDA
torch RNG state plus every owned ledger, order, primitive, opportunity, event
and mark stream; discrete state/key-set equality remains exact. Add independent
mutations for missing, boolean, non-finite, negative and over-tolerance leaves
and for every RNG ownership class.

Adapt only the verified WIP throughput structure: cache prepared prefixes and
row scripts per `(batch,time)`, bind all branches to one shared schedule, retain
selected state until validation completes, aggregate branch/output errors on
device, and transfer only completed packed evidence at a cell-batch boundary.
Expose prefix, branch and total wall-time telemetry plus selected-state count,
collector-call count and serialized size. Telemetry remains descriptive. The
registered width is 16; five selected states produce fifteen branch rows plus
one padding row per collector call. There is no production scalar audit,
per-field CUDA-to-host loop, repeated prefix reconstruction or serial
per-opportunity execution.

Acceptance requires: a width-16 mixed-time/multi-batch CUDA three-branch oracle;
donor no-fixed-point/multiset/additivity positives; raw-trace and donor coherent
tamper negatives; strict restore/RNG negatives; full `TrackingOutcome`
recomputation and co-tamper negatives; a static sweep proving no active legacy
fork API, production scalar audit or per-field CUDA host loop; telemetry/size
evidence; the preserved focused CUDA suite; and one unmistakably non-formal
`formal_path_exercise` through the shared formal cores.

## Operational-readiness repair boundary

This is one coupled replacement package across
`ha_ctse_process/event_held_commitment_link.py`,
`ha_ctse_process/noncalendar_commitment_testbed.py`,
`scripts/run_noncalendar_commitment_benchmark_g0.py` and the focused test file.
The prior executable path is replaced in place; no old schema, scalar replay
gate, direct-write helper, scalar evaluation fallback or compatibility loader
remains active.

### Formal replay gate repair

The formal train failure after three indexed updates is operational evidence,
not a scientific result. Its exact-support, state, detach, support-leak, RNG
and event-joint assembly checks passed. The failing fourth collection/replay
comparison reported a `mark_component` drift of
`1.9073486328125e-6`; the event-joint error was the same while its registered
compositional bound was `1.0300217821000548e-5`.

The executable cause is a split arithmetic path, not an inadequate tolerance.
The collector computes both event logits and Normal mark parameters with the
explicit row-local multiply/reduce helper so one request is independent of the
number and ordering of other packed requests. Teacher replay instead sends the
compacted event rows through `nn.Linear`, allowing CUDA GEMM shape and
reduction selection to change after the weights evolve. The first three
archived updates already show non-zero 2--20 ULP component drift while passing
the mixed and ratio gates; the next trajectory crosses only the component
gate. A derived-joint bound correctly passing does not override a failed
actual factor.

Freeze one shared event/mark-head evaluation helper. Collection, teacher
replay, stochastic/deterministic modes and fork collection all call that same
row-local float32 linear evaluation for both heads. Sampling support, masks,
categorical action, transformed-Normal formula, stored `u/z`, factorization,
joint assembly, RNG draw order and gradients remain unchanged. Do not convert
the behavior policy or replay to float64 and do not widen, reinterpret or
replace any registered tolerance.

The existing component predicate remains authoritative at every eligible
coordinate:

```text
absolute_error <= 1e-6 + (8 * 2^-24) * max_abs
abs(expm1(replayed - stored)) <= 1e-4
```

The worst-coordinate selector continues to rank the maximum of mixed-bound
severity and ratio severity. `float32_ulp_at_max_magnitude` and
`ulp_distance` remain exact recomputable evidence for the selected stored and
replayed binary32 values; ULP is not a third admission gate and cannot rescue
a component that fails either registered predicate. State fields remain
absolute-only, exact semantic/support/detach fields remain exact, and the
event-joint compositional/assembly and ratio gates remain independent.

No replay, artifact or checkpoint schema increment is required because the
serialized predicates, fields and scientific meaning do not change. The old
split replay arithmetic path is deleted rather than retained as a fallback.
Formal train, non-formal exercise and archived-evidence validation continue to
share one report generator and one fail-closed record validator.

Acceptance requires all of the following on CUDA without a formal run:

1. A bounded shared training-core reproduction executes replicate 0, all
   `OR/DUM/EHC` arms, four 16x80 updates and four PPO passes. All four update
   shards publish and revalidate; the fourth update's primitive/categorical/
   mark records satisfy their mixed and ratio gates and the event joint
   satisfies its unchanged assembly, compositional and ratio gates.
2. A shape/order test proves that the shared event/mark helper gives the same
   row result when requests are evaluated together, permuted or partitioned,
   and that collection and teacher replay call this helper rather than a
   separate `nn.Linear` route.
3. Existing and new negatives still reject wrong factor masks/actions,
   support leakage, detach changes, omitted or sign-reversed Jacobian,
   missing mark components, a re-signed stored component beyond its mixed or
   ratio gate, non-finite/ULP/coordinate tampering and joint assembly
   corruption. A passing joint never admits a failing component.
4. The three archived accepted update shards remain valid under the unchanged
   schema. The recorded failure artifact remains evidence of the superseded
   split arithmetic path and is never relabeled as a scientific result.
5. The complete focused CUDA suite and one fresh bounded
   `formal_path_exercise` pass, formal analysis still rejects exercise
   artifacts, checkpoint continuation remains within `1e-7`, and no
   temporary residue or new scalar CUDA/packing path appears.

### Formal evidence streaming repair

This is one newly authorized launch-readiness repair over the complete
evidence-contract WIP. It changes only publication and analysis layout. All
scientific fields, strict recomputation predicates, RNG ownership, optimizer
evidence, checkpoints, registered budgets and result meanings remain
unchanged. There is no compatibility reader for the former monolithic formal
manifest.

Formal training publishes one self-contained evidence shard for each
`(replicate, update)` only after the three arms and their paired record pass the
existing recomputation validator. The authoritative layout is:

- `train/replicate_<r>/evidence/update_<u>.json` for the bounded verbose shard;
- `train/replicate_<r>/indexes/index_<generation>.json` for immutable ordered
  update-catalogue generations and the final arm/checkpoint summary;
- `train_manifest.json` for the small root state.

Each index entry contains the update number, root-relative path, SHA-256 and
byte count. Paths must resolve beneath the evidence root. Every index
generation is immutable: publication writes and hashes a new generation, then
atomically replaces the root reference. A failure between those writes leaves
the preceding root/index pair authoritative and the unreferenced new
generation non-authoritative; a referenced path is never overwritten behind
its recorded hash. The replicate index
contains exactly updates `1..250` without gaps, duplicates or reordering and
chains exposure and RNG state across shards. The root manifest contains only
formal identity, contract, status/branch and ordered replicate-index
references with their hashes, sizes and progress; it never contains verbose
updates. It is atomically refreshed after every accepted shard/index
publication and after each final checkpoint summary. At most the current
update shard, current small index and root manifest may be resident in memory.
Once a shard has been indexed, the production path releases the trajectory and
evidence object before collecting the next update.

Evaluation cell artifacts remain bounded independent artifacts. The small
`evaluation_manifest.json` is atomically refreshed after every accepted cell
and contains only ordered cell references, hashes, sizes, completion progress
and formal identity. It never embeds cell payloads. A failure publishes one
atomic failure artifact and replaces the relevant root manifest with terminal
`INVALID_OPERATIONAL`, preserving references to all previously indexed
artifacts. A shard written but not indexed is non-authoritative and ignored on
recomputation. No `.tmp` file is authoritative or may remain after success or
handled failure.

`last_complete_evidence` in an operational failure is empty or a reference to
the last atomically indexed update/cell only. An in-progress batch is never
embedded or described as complete; its replicate, arm, cell and batch
coordinates travel only in the failure context fields. A mid-cell or
pre-publication failure validates against the preceding root state.

JSON publication streams the current bounded object directly to a same-
directory temporary file with an encoder `default` for NumPy scalars/arrays,
Torch tensors and the already supported record objects. It must not first make
a recursive JSON-ready copy of the object. SHA-256 and byte count are computed
from the completed file in bounded chunks before the atomic index update.

The formal analyzer reads the small root manifests, verifies root-relative
path containment plus every recorded hash and byte count, and then validates
one replicate index, update shard or evaluation cell at a time. It reuses the
existing strict update/cell validators, maintains only the compact cross-shard
RNG/exposure state and statistical episode/fork summaries needed downstream,
and releases verbose payloads immediately. It rejects a missing, duplicate,
out-of-order, unindexed, truncated, corrupt, size-mismatched, digest-mismatched
or path-escaping artifact. It must not call `read_text` on evidence artifacts,
construct a multi-replicate verbose manifest, or retain all evaluation cells.
Reference byte counts, replicate/update/batch/episode identities and every
deterministic Stage-2 integer require exact non-boolean integer types; hashes
require canonical lowercase 64-character hexadecimal strings. Stringified,
floating or boolean substitutes fail even when dependent digests are
recomputed.

Stage-2 `execution` contains only deterministic contract fields: `engine`,
`registered_width`, `selected_pairs` and `collector_calls`. Wall-clock
`elapsed_seconds` and derived `pairs_per_second`, when reported, live in a
separate descriptive `telemetry` record. Their absence, value or finite status
does not enter formal operational validity or the scientific result; mutation
of a deterministic execution field still invalidates the evidence.

This repair increments the affected strict artifact/index schemas and the
checkpoint-bound registered contract exactly as required by the new layout.
It preserves the formal/exercise separation: exercise artifacts use distinct
non-formal schemas and remain rejected by the formal analyzer while sharing
the same sharded publication and streaming validation core.

Acceptance requires focused CUDA checks proving all of the following before
the fresh final read-only review:

1. Two or more synthetic updates and evaluation cells become visible one at a
   time through atomic shard, index and root-manifest publication, with exact
   ordered digests and no temporary residue.
2. Injected failure after an accepted shard preserves earlier indexed evidence
   and yields one recomputable terminal `INVALID_OPERATIONAL` manifest; an
   unindexed orphan cannot be counted complete. Injected failures between an
   immutable index-generation write and root swap, mid-cell, and immediately
   before cell publication leave the preceding root/reference set valid.
3. Missing, duplicate, out-of-order, truncated, corrupt, wrong-size,
   wrong-digest and path-escaping shards fail closed.
4. Writer instrumentation proves there is no recursive full-object JSON copy,
   root manifests contain no verbose update/cell records, and bounded-memory
   analyzer instrumentation proves no more than one verbose shard is live.
5. Streaming/indexed analysis reproduces the existing operational and result
   outcome on bounded evidence without loading a monolithic manifest.
6. Changing, removing or making Stage-2 timing telemetry non-finite does not
   change strict validity, while changing any deterministic execution field
   fails it. Rehashed type-only mutations of references and deterministic
   identities also fail.
7. The complete focused CUDA suite, the bounded CUDA
   `formal_path_exercise`, strict checkpoint round trips and formal rejection
   of exercise artifacts still pass.

### Final evidence-contract repair

This is one newly authorized repair cycle over the preserved operational-
readiness WIP. It changes no scientific estimand or registered execution
contract. It closes exactly three launch-blocking evidence defects and does not
reopen the already accepted replay, lifecycle, no-op, exposure, atomicity,
checkpoint, CUDA batching or result-precedence work.

#### Independent Stage-2 natural continuation

Delete `event_references` from the collector interface and from every batched
and sequential fork caller. No fork path may copy or overwrite a future event
kind, categorical action, candidate mark, event input, likelihood component,
joint likelihood or installed commitment from the collected reference
trajectory. The collected trajectory is comparison evidence only.

Use one batch-shape-stable event/mark linear evaluation in both ordinary
collection and fork collection so a row's logits and Normal parameters depend
only on its frozen input and weights, not the number or ordering of other
requests packed beside it. This is an algebraically identical implementation
of the existing heads and is applied identically to DUM and EHC; it changes no
support, factorization, draw, objective or treatment. Prefix replay remains at
the registered width 16 and must reproduce the collected prefix exactly before
a fork is admitted.

At the focal opportunity, the two branches differ only in the forced focal
`KEEP` versus `RENEW(candidate_z)` intervention. From the immediately pre-
opportunity cursor onward, every later ledger, order, primitive, opportunity,
event and mark draw is consumed independently from cloned CRN state or an
independently replayed row script. The natural branch receives no reference
override. It must reproduce the collected continuation by executing those
draws through the normal lifecycle, event and primitive paths. Check every
natural branch against the collected continuation for exact discrete actions,
membership, lifecycle/event kinds, segment and terminal outcome; exact final
owned RNG states; and continuous tensors and utility within `1e-7` (utility is
exact for this environment). Any mismatch raises operational invalidity.

The production width-16 batched engine and the test-only sequential oracle
must reconstruct their prefixes separately from the batch-origin state, clone
their branch states separately and execute independently. They may share only
pure canonical serialization and comparison helpers. The oracle must not call
the production batched fork engine, consume its output, share its mutable
generators or use a reference overwrite. Their outputs must agree under the
existing registered-width discrete/RNG/utility exactness and continuous
`1e-7` contract.

#### Re-derived RNG and CRN bindings

Replace digest-only RNG claims with strict versioned binding records. A binding
has an exact key set and domain-separated context containing mode, formal flag,
replicate, arm, update or evaluation cell/batch, and, for Stage 2, the stable
fork ID, original episode coordinate, natural action and branch action. It
also contains the authoritative registered seed, canonical start state, an
ordered draw schedule (operation, dtype, shape and logical coordinates), a
digest of the generated draw bytes, canonical end state and one binding digest
over all preceding fields.

Create bindings through a single audited draw/replay helper. Validation must
not compare one supplied SHA-256 string with another. It reconstructs the
registered generator from the authoritative seed for the first record, chains
each later start state to the independently validated prior end state, replays
the ordered draw schedule on a fresh cloned generator, regenerates and hashes
the draw bytes, checks the canonical end state, and then recomputes the binding
digest. Training records chain by `(replicate, arm, stream, update)`;
evaluation records chain by `(replicate, arm, cell, stream, batch)`. Paired
OR-DUM and DUM-EHC equality is checked only after both arm-local bindings have
independently validated.

Stage-2 row-script bindings start from the already validated held-out cell-
batch stream state at the fork coordinate. Their draw schedule is generated
from the natural trajectory's exact request coordinates but contains no future
sampled value copied from that trajectory. The validator independently replays
the schedule, binds it to the stable fork/episode/time/lifecycle coordinate,
checks both branches consume the same schedule and reach the same end state,
and checks that the natural branch's executed continuation matches the
collected one. Mutating a seed, coordinate, operation, shape, schedule order,
draw digest, start/end state, branch label or binding digest must fail even if
all duplicated convenience digest fields are changed consistently.

Persist only the compact ordered draw schedule plus canonical start/end states
and digests; do not persist duplicate sampled trajectories or add a second RNG
path. The registered generators, seeds, draw order and coupling remain
unchanged.

#### Recomputable optimizer evidence

For every PPO pass and applicable optimizer group, persist one strict raw
record containing pass index; optimizer step before/after; the finite scalar
loss before backward; the unclipped group gradient norm returned by the
existing clip operation; the applied clip coefficient or its exactly derived
equivalent; and a canonical per-parameter summary. Each parameter summary
contains its fully qualified model name, shape, number of elements, dtype,
gradient-present flag, finite/non-finite and zero counts, squared L2 norm,
maximum absolute value and a digest of the contiguous pre-clip gradient bytes.

Persist a canonical optimizer-ownership manifest for each arm/group with the
ordered parameter names, shapes and element counts. Validate it against the
frozen exact ownership: OR base owns the ordinary base only; DUM/EHC base owns
the identical ordinary base plus `W_z`; DUM/EHC event owns only event and mark
heads; OR has no event group; groups are disjoint and cover every trainable
parameter exactly once. DUM and EHC manifests and counts must match.

The validator recomputes non-None, zero and non-finite counts from the
per-parameter records; recomputes the group norm as the square root of summed
squared L2 norms; checks it against the recorded unclipped norm under a fixed
floating comparison recorded in the contract; derives the clip coefficient;
checks all loss/norm/summary scalars are finite; and enforces the already
frozen four base steps plus four applicable event steps and absolute exposure
continuity. Aggregate counts and `finite` flags are derived conveniences only.
Missing, duplicate, foreign-owner, renamed, reordered, non-finite or
internally inconsistent pass/parameter records are operational invalidity.

Focused negative tests must independently mutate each of the three repaired
boundaries: remove reference independence or perturb an independently sampled
natural continuation; consistently alter digest conveniences plus one seed,
coordinate, schedule, raw state or generated-draw binding; and alter a raw
loss, group norm, per-parameter squared norm/digest, owner identity or step.
Every mutation must be rejected by recomputation. The bounded CUDA
`formal_path_exercise` must execute Stage 2 and serialize the new binding and
optimizer records through the same shared formal cores. Older WIP evidence and
checkpoints fail the incremented strict schemas; no compatibility path is
added.

#### One final-review repair cycle

The fresh integrated review found that the first implementation still derived
event/mark/opportunity coordinates after collection in lifecycle-key order,
while the collector consumed them in frontier request order; it also retained
summary-only optimizer evidence. This authorized repair cycle replaces those
two self-consistency boundaries without changing any draw or optimizer step.

Record the RNG audit trace at the actual generator call site. Every draw entry
contains the stream, operation, dtype, shape and the exact logical coordinates
in the same ordered `requests` list used by the collector. Do not reconstruct
coordinates later with `nonzero`, `argwhere`, sorted keys or an artifact copy.
Ledger generation and frontier-order priority generation must emit the same
actual-call trace rather than an empty binding schedule. The independently
serialized lifecycle/request and frontier-order evidence must reconstruct the
expected request sequence, and validation requires it to equal the call-site
trace before replaying the generator schedule. A binding is invalid when the
same count and generated bytes are attributed to another coordinate or order.

For every Stage-2 branch and stream, persist the actual row-script consumption
position, the digest of the bytes consumed through that position and the
terminal stream state. Validate these facts against the independently replayed
fork schedule slice for that stable fork and branch. `rng_equal`, position
equality or another boolean is never accepted as evidence by itself. Paired
branch equality is derived only after each branch's actual consumed slice has
validated. Add a negative that changes request coordinates and re-signs every
binding and convenience digest while leaving the independent call-site/order/
lifecycle trace unchanged; it must fail. Add branch position and consumed-byte
co-tamper negatives.

Replace each summary-only per-parameter gradient record with canonical raw
pre-clip gradient material. Encode the contiguous little-endian gradient bytes
in a strict deterministic payload (optionally deterministic zlib plus base64),
with dtype, shape and uncompressed byte count. Absence is explicit for a
missing gradient. The validator decodes this payload and independently derives
the byte digest, finite/non-finite and zero counts, squared L2 norm, maximum
absolute value, group norm and clip coefficient; none of those supplied
summaries is an authority. Keep the exact ownership manifest and reject payload
length, dtype, shape or owner mismatch.

Persist the actual scalar loss and its named algebraic components for each
base/event pass. Recompute the loss from the frozen PPO/value/entropy
coefficients and require equality to the recorded raw loss under one strict
registered numerical rule. This does not create a new objective or tolerance;
it audits the existing scalar construction. Negative tests co-alter the
summary, gradient digest, group norm, clip coefficient and outer record digest
while leaving the raw payload fixed, and co-alter raw loss plus the outer
digest while leaving its components fixed; both must fail. Evidence payload
size and encode/decode time are reported by the exercise and inspected for
formal-scale storage risk, but they do not authorize thinning evidence or a
second unverified path.

### Replacement ledger

- Replace the flat absolute gate over all replayed continuous quantities with
  two disjoint classes: mixed absolute-relative plus probability-ratio gating
  for actual log-likelihood components, and the unchanged absolute-only gate
  for value/state tensors. Exact semantic fields remain exact.
- Replace maximum-error-only component evidence with a worst-coordinate record
  carrying the stored and replayed values, absolute error, applied mixed bound,
  ratio drift, local float32 spacing, ULP distance and full tensor coordinate.
- Retain the existing compositional joint and float64 assembly checks. Add the
  accepted `expm1` ratio-drift cap to the final event joint; do not convert the
  behavior policy, sampling path, PPO likelihood or gradients to float64.
- Replace direct JSON and checkpoint writes with same-directory temporary-file,
  flush/fsync and atomic-replace publication. A failed write never leaves a
  file at the authoritative final path.
- Replace trusted operational booleans with per-update and per-evaluation-batch
  numeric/count/digest evidence from which replay, lifecycle, RNG, no-op,
  exposure and finiteness are recomputed by the validator.
- Replace separate untested formal-only loops with one parameterized training
  core and one parameterized evaluation core. Formal wrappers retain the exact
  authorization token and registered dimensions. A separate
  `formal_path_exercise` wrapper uses the same cores with an unmistakably
  non-formal schema and cannot be consumed by the formal analyzer.
- Replace the production `(environment, physical-step, lifecycle)` scalar
  intervention path and scalar CUDA count reductions with one trajectory-batch
  teacher-forced computation. Only genuine autoregressive position remains a
  loop; GPU-to-host transfer occurs once at the completed cell-batch boundary.

### Replay numerical and evidence contract

Freeze these constants in the registered contract:

```text
REPLAY_LOG_COMPONENT_ATOL = 1e-6
REPLAY_LOG_COMPONENT_RTOL = 8 * 2^-24 = 4.76837158203125e-7
REPLAY_LOG_RATIO_DRIFT_CAP = 1e-4
REPLAY_STATE_ATOL = 1e-6
RESUME_TOLERANCE = 1e-7
```

`primitive_component`, `categorical_component` and `mark_component` pass only
when, at every eligible coordinate, both

```text
abs(replayed - stored)
  <= REPLAY_LOG_COMPONENT_ATOL
     + REPLAY_LOG_COMPONENT_RTOL * max(abs(replayed), abs(stored))
abs(expm1(replayed - stored)) <= REPLAY_LOG_RATIO_DRIFT_CAP
```

hold. The same `expm1` cap gates the final event-joint replay ratio. `value`,
`hidden`, `prefix`, `event_input`, `event_new_z` and `primitive_event_z` retain
the absolute-only `1e-6` gate. Masks, kind/action support, support leakage,
detach state, lifecycle ownership and discrete fields retain exact equality.
Non-finite data fails before any comparison. The primitive/event compositional
joint bounds and float64 assembly audit remain unchanged.

Every likelihood component serializes its deciding coordinate as integer
indices and these exact fields:

```text
stored_value, replayed_value, absolute_error, mixed_bound,
ratio_drift, ratio_cap, float32_ulp_at_max_magnitude, ulp_distance,
coordinate
```

The coordinate is `(time, environment, lifecycle)` for primitive/categorical
and adds `mark_component` for the transformed mark. ULP distance is computed
from the ordered finite binary32 encodings of the actual stored and replayed
values; spacing is the distance from the larger-magnitude finite binary32 value
to its next representable neighbor. Empty-support records are explicit and are
legal only for the OR event factors. The event-joint ratio record likewise
names its deciding values and coordinate. The serialized replay record has one
strict incremented schema and exact key sets; validators recompute every pass
predicate from the numeric record rather than trust `passed` or a failure list.

An independent focused reference computes the transformed-Normal log density
in standalone float64 arithmetic without calling the production helper. It
covers ordinary and saturated inputs and proves that omitted Jacobian, reversed
Jacobian sign, wrong mask and missing-component mutations fail. This is kept
separate from runtime collection/replay equivalence because replay cannot catch
a shared common-mode formula defect.

### Atomic artifacts and recomputable operational status

JSON artifacts and checkpoints are published atomically from unique sibling
temporary files. JSON and checkpoint bytes are flushed and fsynced before
`os.replace`; the temporary file is removed on failure. Checkpoint schema and
the registered replay block are incremented, so every older development
checkpoint fails strict load. There is no migration or compatibility path.

After formal authorization has been validated, each training, evaluation and
analysis wrapper owns a terminal manifest. Success and operational failure both
publish it atomically. An operational exception first publishes an immutable
failure artifact containing mode, `formal`, stage/replicate/arm/cell/batch,
exception type and message, completed artifact paths and the last complete
recomputable evidence record; it then publishes a terminal manifest whose
status and branch are `INVALID_OPERATIONAL` and which points to that failure
artifact. The exception may then propagate. Authorization rejection occurs
before artifact creation and is not mislabeled as a scientific result.

For every training update, persist arm-local replay records, lifecycle/factor
counts, named finite checks, optimizer exposure before/delta/after and seed-map
plus owned-stream state digests. Persist paired OR-DUM exact tensor differences
and the paired-stream digests needed to recompute no-op and RNG equality. For
every 16-episode evaluation cell batch, persist episode IDs, the same replay,
lifecycle, finite and RNG evidence, reduction/intervention counts and checkpoint
origin. Aggregate `operational` booleans are derived conveniences only: the
formal validator independently re-derives them from these records, requires
all expected updates/cell batches exactly once and rejects missing, duplicate,
non-finite, internally inconsistent or foreign-schema evidence.

### Shared-core non-formal CUDA exercise

Add CLI mode `formal_path_exercise`. It never accepts or supplies the formal
authorization token. It calls the same parameterized training/evaluation cores
as the formal wrappers with exactly:

```text
formal = false
replicates = [0]
arms = [OR, DUM, EHC]
updates = 1
num_envs = 16
horizon = 80
ppo_passes = 4
evaluation cells = all four registered cells
episodes per cell = 16
checkpoint = update_1.pt, strict save/load round trip
device = cuda
```

Its manifest and every child artifact use a distinct
`formal_path_exercise` schema, carry `formal=false`, use a separate output
subtree, and terminate only as `FORMAL_PATH_EXERCISE_COMPLETE` or
`INVALID_OPERATIONAL`. The formal analyzer requires the formal schema,
`formal=true`, formal mode names, update-250 origin and all registered counts;
it therefore rejects exercise artifacts even if paths are copied or renamed.

### Batched evaluation structure

For one completed trajectory, flatten `(time, environment)` into a batch,
prepare the ordinary base once, and teacher-force all active lifecycles across
the fixed autoregressive-position loop. Gather/scatter focal keys and prefixes
on device. Construct the same ascending-active-key cyclic `z` derangement in
batch, evaluate natural and permuted `W_z` biases in packed calls, and return
the `I_TV` tensor and eligibility mask for the whole trajectory. Event kind,
KEEP/RENEW/non-CREATE counts and multi-opportunity lifecycle counts reduce on
device across time/lifecycle dimensions. Transfer the reduced episode tensors
and packed intervention values once per 16-episode cell batch, then construct
JSON rows on CPU. No `.item()`, `.tolist()` or device-to-host scalar conversion
is permitted inside an environment, physical-time or lifecycle loop on the
formal evaluation path.

The old scalar production functions are deleted. A test-only independent
sequential oracle preserves the prior estimand and must agree with the batched
implementation on eligibility, coordinates and counts exactly and on
intervention values within `1e-7` under the registered 16-environment CUDA
shape.

## Replacement ledger

- Preserve the current noncalendar ledger generator, anonymous 15-field
  observations, membership schedule, target/duration distributions and external
  G0 utility exactly.
- Use the full anonymous observation for all three new arms. The superseded
  calendar-masked arm, hindsight H/C/S/D solvers, old result tree, old checkpoint
  schema and their runner/test entry points are removed rather than retained
  behind flags or aliases.
- Keep `dynamic_roster_direct.DirectPrimitiveARPolicy` as the single ordinary
  recurrent base. Any optional prepared-step or primitive-logit-bias interface
  must leave the no-bias `OR` path exactly equal in parameters, state, actions,
  log probabilities, values, hidden transitions and PPO algebra under matched
  weights and RNG.
- The active executable surface remains
  `ha_ctse_process/noncalendar_commitment_testbed.py`,
  `scripts/run_noncalendar_commitment_benchmark_g0.py` and
  `tests/ha_ctse_process_noncalendar_commitment_benchmark_g0_test.py`; add a
  narrowly named helper module only if it eliminates duplication without
  preserving an obsolete path.

## Frozen model and treatment

Initialize one ordinary base with seed `58058`, clone it strictly into `DUM`
and `EHC`, then initialize the additions once from dedicated event/mark RNG
state and clone those additions strictly between `DUM` and `EHC`.

- `OR`: the existing 14,980-parameter direct recurrent actor-critic only.
- `DUM` and `EHC`: the same base plus bias-free `W_z: Linear(8,3)` (24
  parameters), `event_head: Linear(87,2)` (176), and
  `mark_head: Linear(87,16)` (1,408), for exactly 1,608 added trainable
  parameters in each arm.
- Existing source state is 32-wide locally and its anonymous active-set context
  is also 32-wide. Therefore the source's `h_64` event feature is frozen as
  `concat(h_pre_32, context_32)`. This is a parameter-free use of the two
  already-computed source states; neither widens nor changes the ordinary base.
  Event inputs are exactly
  `stopgrad(concat(o_15, h_pre_32, context_32, z_pre_8))`.
- Event and mark heads share no parameter and no gradient with the base trunk.
  The critic never reads `z`.
- The sole arm treatment is
  `primitive_logits = base_logits + W_z(m * stopgrad(z))`, with `m=0` for
  `DUM` and `m=1` for `EHC`. `OR` supplies no bias. No other arm-conditioned
  branch is permitted in sampling, storage, replay, loss or execution.

`W_z` belongs to the primitive/base optimizer because it is identified only by
primitive PPO. The base optimizer owns base parameters plus `W_z` in DUM/EHC;
the event optimizer owns only the categorical and mark heads. In `DUM`, the
zero treatment input produces an explicit zero gradient for `W_z`, so its Adam
step exposure matches `EHC` while its primitive effect is exactly zero.

## Clocks, lifecycle and execution

Maintain a per-environment table keyed only by the ledger lifecycle key. Each
entry owns membership epoch, `h`, `z`, `q`, open segment ID/start, and complete
or censored segment records. Keys never enter a model input.

For each physical row, use this order:

1. Apply the environment membership transition and reconcile lifecycle state.
   Genuine `JOIN` resets `h=0`, forces `CREATE`, samples a mark and samples
   `Delta` uniformly from `{4,8,12}`, setting `q=Delta`. Temporary leave freezes
   the full entry. Rejoin restores it. Terminal leave forces `CLOSE` after that
   lifecycle's preceding final reward and deletes it.
2. For every active entry with `q=0`, process exactly one opportunity before
   its primitive action. Support is exactly `KEEP`/`RENEW`. `KEEP` retains mark,
   segment ID and start and resamples only `q`; `RENEW` records a complete
   segment, increments the segment ID, samples a new mark and `q`, and opens the
   new segment. A due opportunity on rejoin is processed before its action.
3. Form the detached event-held mark table and execute the existing
   autoregressive primitive policy with the arm's sole logit treatment.
4. Step the unchanged environment, attach reward/terminal data, then decrement
   `q` exactly once for each lifecycle that took an active primitive action.
5. At episode end, after the final reward, force `CLOSE`, record every remaining
   open segment as right-censored and delete all lifecycle entries.

Inactive physical time never decrements `q`. Forced `CREATE` and `CLOSE` have no
categorical likelihood. A rollout cutoff is not an event: preserve `z,q`, the
segment and lifecycle table, carry the environment, detach `h` in all arms, and
bootstrap the unchanged critic. No forced close or event row is created.

The collector must support a resumable partial rollout for focused lifecycle
tests even though the registered update is 16 complete 80-step environments.
Batch environment/member/event tensors; retain loops only for simulator,
membership, recurrent and autoregressive causal order.

## Probability and trajectory contract

At forced `CREATE` and policy `RENEW`, sample a non-reparameterized mark using a
dedicated stream:

```text
u ~ Normal(mu, diag(sigma^2))
sigma = 0.1 + 0.9 * sigmoid(s)
z = detach(tanh(u))
```

For numerical stability compute each transformed component with
`log(1-tanh(u)^2) = 2*(log(2)-u-softplus(-2u))`. Mark log probability is the
sum of Normal component log probabilities minus this Jacobian. No gradient may
flow through sampled `u/z` into either head.

Store primitive rows with observation, `h_pre`, `z_pre`, action, old primitive
log probability, value, reward, terminal/continuation/bootstrap and active
masks, order/prefix, membership epoch, segment, `q` and owned RNG/collector
position. Store at most one padded event row per active lifecycle and physical
row with kind, 87-vector input, factor masks, categorical action, `u`, new `z`,
categorical old log probability, per-mark-component old log probabilities and
joint old log probability.

Likelihood support is exact:

- `CREATE`: mark factor only;
- `KEEP`: categorical factor only;
- `RENEW`: categorical plus transformed-mark factors;
- `CLOSE`: no policy row.

Teacher replay uses the recorded primitive action, categorical event action and
`u`; it recomputes the identical inputs, masks, factors and joint sums.

The replay bound now combines the 2026-07-21 compositional-joint correction with
the accepted 2026-07-22 executable component contract in
`docs/external-review/gpt5_6_pro/20260722_per_component_tolerance_unexecutable/`.
Before any update the contract has four classes:

- **Exact, zero error**: event support and factor masks, categorical event
  action, action and lifecycle masks, kind support, detach status, discrete
  actions, order and membership ownership.
- **Ordinary continuous state, absolute-only `<=1e-6`**: values, hidden states,
  prefixes, event inputs, reconstructed marks and primitive event marks.
- **Actual log-likelihood components**: primitive, categorical and each
  transformed-mark component must each satisfy the frozen mixed
  `1e-6 + (8*2^-24)*max_abs` bound and the `abs(expm1(delta))<=1e-4`
  probability-ratio cap at every eligible coordinate.
- **Derived joints**: `primitive_joint` and `event_joint` retain the sum of
  eligible component differences plus the float32 reduction allowance over the
  actual factor count. `event_joint` additionally satisfies the `1e-4` ratio
  cap, with `gamma_9 = 9u/(1-9u)` and unit roundoff `u=2^-24`.

The reduction allowance follows from the per-factor bound and conservative
float32 summation; it is not fitted to an observed value. Validating both joints
against a float64 recomputation from the recorded factors is the preferred
implementation, because it tests correct factor assembly rather than demanding
that nine accumulated float32 terms stay inside a one-component tolerance. A
fixed `1e-5` event-joint ceiling is the conservative fallback.

`RESUME_TOLERANCE = 1e-7` is a separate same-checkpoint continuation invariant
and is unchanged. The relaxed joint rule must never be used to admit a
reconstruction that could instead be made bitwise exact.

`registered_contract()` carries the structured state, likelihood, ratio,
joint, ULP-evidence and non-finite rules, so checkpoints written under either
older replay contract fail strict load. No compatibility path is added. The
evaluation artifact serializes strict-schema per-factor errors, applied bounds,
worst-coordinate/ULP records and recomputable operational evidence.
`validate_replay`, both shared execution cores, `validate_operational_records`,
the contract dictionary and the focused tests move together.

All arms and paired replicates execute on one backend and one thread
configuration. Mixing devices or thread counts across arms or replicates would
let device-dependent optimization trajectories become an arm or replicate
confound.

## Credit, losses and exposure

Use the unchanged primitive recurrent PPO and GAE with `gamma=0.99`,
`lambda=0.95`, clip `0.2`, value coefficient `0.5`, primitive entropy
coefficient `0.01`, and correct terminal/continuation bootstrap masks. Every
event row receives the same scalar advantage as the primitive action it
precedes.

- Primitive loss: clipped primitive PPO + `0.5` clipped value loss - `0.01`
  primitive categorical entropy.
- Event loss: clipped PPO on the row's joint event likelihood - `0.01`
  categorical entropy for later `KEEP/RENEW` opportunities; mark entropy bonus
  is exactly zero and forced `CREATE` has no categorical entropy.
- Optimizers: separate Adam, learning rate `3e-4`, epsilon `1e-5`, weight decay
  `0`; separate gradient-norm clipping at `0.5`.

Each registered update is `16 x 80` rows and four full recurrent-sequence
epochs. It increments base optimizer exposure by four for every arm and event
exposure by four for DUM/EHC only. At update 250 the exact totals are 1,000 base
steps for all arms, 1,000 event steps for DUM/EHC and zero event steps for OR.
Report parameter counts, optimizer parameter counts, non-None/zero-gradient
counts, event-factor counts and optimizer steps separately by arm and group.
Pack/transfer each collected trajectory once and reuse it for all four epochs.

## RNG and pairing

For replicate `r`, add `1000*r` to base initialization `58058`, ledger `68058`,
order `78058`, primitive `88058`, opportunity `90058`, event `92058`, mark
`94058`, IID evaluation `98058`, and held-out evaluation `99058`. Bootstrap seed
is `108058`.

Ledger, order and primitive streams are paired across all arms without
consumption coupling. Opportunity/event/mark streams are paired between DUM and
EHC. Parameter initialization and every stream have separate owned state; no
arm's branch may advance another stream. Deterministic evaluation uses
categorical argmax, `z=tanh(mu)` and the existing deterministic primitive rule.

## Checkpoint and runner package

Checkpoint only at update boundaries with an asserted empty rollout buffer.
Use the atomic publication protocol, a strict incremented key set and the
registered-contract header. Save and restore:

- every model and both applicable optimizer states;
- completed update, next ledger/episode IDs, parameter and optimizer exposure;
- explicit `normalizers=None`;
- collector position, pending environments/membership snapshots and accumulator
  state (explicit empty values at the registered complete-episode boundary);
- all lifecycle/segment tables and masks;
- Python, global NumPy, CPU/CUDA torch and every dedicated ledger, order,
  primitive, opportunity, event and mark RNG state.

Load strictly rejects arm, replicate, shape, registered seed/threshold/budget or
key-set mismatch. A save/load continuation must reproduce one complete rollout
and one four-epoch update with exact discrete choices and RNG states, and with
continuous values, likelihoods, model and optimizer tensors differing by at
most `1e-7`. Formal evaluation accepts only a strict update-250 checkpoint.

The runner exposes explicit non-formal smoke, non-formal shared-core
`formal_path_exercise`, formal train, update-250 evaluation and
aggregate-analysis modes. Formal modes require the exact explicit authorization
flag; default invocation only prints the contract. Artifacts identify arm,
replicate, formal status, mode, strict schema, registered contract, counts,
checkpoint origin and recomputable evidence. This implementation task runs only
focused CUDA tests and the bounded `formal_path_exercise`.

Formal packaging fixes five paired replicates `r=0..4`, 16 environments,
horizon 80, 250 updates, 320,000 transitions/4,000 episodes per arm, and four
evaluation cells of 256 paired episodes per arm/replicate: IID deterministic,
IID stochastic, held-out deterministic and held-out stochastic. Evaluate only
`update_250.pt`.

## Statistical and result contract

Use 10,000 paired hierarchical-bootstrap repetitions. Resample the five
replicate seed triples, then whole paired episode IDs within each selected
replicate. Preserve all agents, events, complete/censored segments and paired
arm rows. Percentile intervals are 95%; all declared pass inequalities are
strict.

Primary `G` is held-out stochastic `U_EHC-U_DUM`; secondary `V` is held-out
stochastic `U_EHC-U_OR`. Access uses held-out stochastic arm utility and floor
`0.78`. Support, lifetime and intervention measurements use EHC held-out
stochastic trajectories.

This battery was revised on 2026-07-21 under external disposition
`docs/external-review/gpt5_6_pro/20260721_lifetime_battery_contract_question/`,
before any result was observed. The superseded battery gated on `P_KEEP`,
`P_RENEW`, `CV(T)`, physical-time lifetime bins and a raw logit-residual norm.
Each was passable without learned commitment timing: the usage gates only
require non-degeneracy of a binary support; `CV(T)` mixes policy timing with
exogenous gap variance, so `CV(T)=0.408` under always-`RENEW` while a crisply
learned deterministic `K=3` rule yields `0.236` and fails; and a residual
proportional to `(c,c,c)` has positive norm yet leaves the three-action softmax
exactly unchanged.

### BATTERY_CONTRACT_RECONCILED

The active result contract is the executable `registered_contract()` and
`select_result_branch()` battery: support counts, `K==1`/`K==2`/`K>=3`,
`I_TV`, and both natural-action `C_total` interval and point-floor gates. The
retired timing diagnostics remain descriptive only.

Define `K` for each commitment spell as the number of exogenous opportunity
intervals it contains, so terminating `RENEW` at the first later opportunity is
`K=1`, one `KEEP` then `RENEW` is `K=2`, and so on. `K` is policy-determined.
Temporary absence contributes neither a gap nor active duration. Spells
censored by terminal leave, forced close or rollout cutoff are excluded from
complete-spell `K` statistics and reported separately.

- Support, not evidence: at least `128` eligible natural `KEEP` rows and at
  least `128` eligible natural `RENEW` rows. `P_KEEP` and `P_RENEW` remain
  reported diagnostics and gate nothing.
- Policy-generated lifetime: over complete spells, bins `K=1`, `K=2`,
  `K>=3` require at least two with `LCB(proportion)>0.10`.
- Executable mark dependence: at states with at least two active lifecycles,
  derange `z` across lifecycles while holding observation, recurrent hidden
  state, action mask, active-set context and primitive prefix fixed. Require
  `LCB(I_TV)>0.10` where
  `I_TV = E[0.5 * sum_a |pi(a|o,h,z) - pi(a|o,h,z_perm)|]`. This is invariant
  to a softmax-common logit shift by construction.
- Identifiability requires at least 1,000 non-CREATE opportunities and at least
  250 lifecycles with two or more such opportunities across all five seeds.

`T`, `CV(T)` and the physical-time bins `[1,8]`, `[9,16]`, `[17,infinity]`
remain computed and serialized as descriptive outputs. They gate nothing.

For the source phrase "behavior confidently fails", use the exact statistical
dual of the LCB pass rule: at least one required lifetime-bin or intervention
condition has `UCB <=` its registered threshold. Support-count failures are not
part of this dual; they resolve earlier as non-identifiable. This introduces no
new threshold and leaves intervals crossing a threshold to the underpowered
branch.

## Natural event-decision consequence

Adopted 2026-07-21 under
`docs/external-review/gpt5_6_pro/20260721_replacement_c_scope_followup/`. This
is a **held-out evaluation-only** measurement. Training behavior, the PPO
objective, the behavior-policy likelihood, optimizer state and the checkpoint
schema are unchanged, and no additional RNG draw is permitted anywhere.

The collector already draws a mark candidate for every request before the
categorical mask is applied, and discards it on `KEEP`. The measurement
therefore requires retention of an existing quantity, not new sampling.

Retain the unmasked `candidate_u` and `candidate_z = tanh(candidate_u)` for
every opportunity. On a natural `CREATE` or `RENEW` row this is the executed
mark; on a natural `KEEP` row it is an auxiliary counterfactual mark. Candidate
fields are stored in all modes for a uniform trajectory schema and are
audit-only: they never enter a likelihood, loss, gradient or optimizer state.

At each eligible held-out non-`CREATE` opportunity, fork the frozen state into
two common-randomness branches. The `KEEP` branch retains `z`; the `RENEW`
branch applies the stored `candidate_z`. Both advance to episode termination
under identical realized future demand and membership, opportunity gaps,
primitive order, primitive-action uniforms, later event uniforms and later
candidate marks. Each branch owns cloned state; the two branches of a pair must
not share one mutable generator, because advancing one would shift the draws the
other sees. Truncating a branch to a fixed horizon is prohibited: this
environment pays zero reward until the terminal step, so a truncated branch
estimates a different quantity.

For a natural `KEEP` row,
`C_total_KEEP = U(KEEP_HELD_MARK) - U(RENEW_CANDIDATE_MARK)`; for a natural
`RENEW` row,
`C_total_RENEW = U(RENEW_CANDIDATE_MARK) - U(KEEP_HELD_MARK)`. Cluster by
original sign-paired base episode, never by event row; multiple selected rows
from one cluster travel together in every resample. Batch membership is not a
statistical unit.

Gates are `LCB(C_total_KEEP)>0` and `LCB(C_total_RENEW)>0` with frozen point
floors `mean(C_total_KEEP)>=0.02` and `mean(C_total_RENEW)>=0.02`.

Forks are a batched forced-branch dimension per the binding engineering
constraints, sized in units of the registered 16-environment width. Batched and
sequential execution must agree exactly on discrete membership, event and
primitive actions, on terminal outcomes and utilities, and on RNG states after
continuation, with continuous values within `1e-7`; the natural-action branch
must additionally reproduce the originally collected continuation exactly. If
either equality fails the batched engine is invalid.

Default is full per-opportunity forking. The only accepted reduced form is 32
natural `KEEP` and 32 natural `RENEW` opportunities per replicate, selected
after natural trajectories are collected but before any fork outcome is
computed, by simple random sampling without replacement within each
`(replicate, natural_action)` stratum from a dedicated deterministic stream
derived from the registered bootstrap seed under a separate namespace. The
selection key may use only replicate, base episode ID and sign parity, physical
time, opaque lifecycle key, membership epoch, segment ID and the natural
action; it may not use observation values, mark values, future trajectory,
utility or counterfactual advantage. If any replicate has fewer than 32 eligible
rows for either natural action, the run is `BENCHMARK_NON_IDENTIFIABLE` rather
than repaired by changing the quota. Adaptive post-result resampling and
post-result top-up are prohibited.

Implementation is staged. Stage 1 is retention only. Stage 2 is the batched
fork engine and its equivalence evidence. The result contract does not consume
`C_total_KEEP`/`C_total_RENEW` until stage 2 is accepted.

Candidate presence is determined by `event_kind != 0`, never by testing
`candidate_u` against zero. Padded no-request positions hold zeros, and under
deterministic evaluation `candidate_u = mu` may itself be exactly zero, so a
value test would conflate a real candidate with padding. No separate presence
mask is added because the kind field already carries it.

### Stage 2 executable design

Fork state is cloned through the existing environment contract
`NoncalendarTrackingEnv.snapshot_state` and `from_snapshot_state`, which deep
copy the ledger, members, time, counters, reward trace, membership change and
terminated flag under strict key-set validation, and return an independent
instance. Measured cost is 288 microseconds per clone, about 1.2 seconds across
the full fork budget, so the ledger is cloned rather than shared and no
optimization is warranted. Do not re-derive this.

Each fork owns independent environment, lifecycle, recurrent hidden, commitment
and RNG storage. Paired branches receive cloned generator state rather than a
shared mutable generator, because advancing one branch would shift the draws the
other observes. Pairs carry a stable pair identifier so they survive compaction;
no tensor is written across fork identifiers, and batch position, padding and
termination masks never influence RNG indexing.

Stage 2 executes canonical full-width layers cloned from each original
`(batch,time)` prefix. One natural-control layer retains all original slots;
counterfactuals share a layer only when their original environment indices do
not collide. Serial per-opportunity execution and selected-row repacking are
rejected.

The prefix and every continuation preserve the original 16-environment width
and slot layout. Dense-kernel batch-invariance measurements remain descriptive
only: neither exact zero nor backend-specific nonzero error admits or rejects a
canonical continuation.

Acceptance requires exact discrete membership, event and primitive actions,
terminal outcomes, utilities and RNG states. Every natural continuation is
checked inside the engine, with continuous values bounded solely by
`CAUSAL_AUDIT_CONTINUOUS_ATOL = 1e-7`; batched and sequential evidence retain
the same protected semantics.

`registered_contract()` gains the `C_total_KEEP` and `C_total_RENEW` gate
thresholds and their point floors when this stage lands. That changes the contract dictionary,
and `load_checkpoint` rejects on contract inequality, so every checkpoint
written before this stage becomes unloadable. Formal training must therefore be
launched only after this stage is accepted and the contract is final.

Apply exactly this first-match result priority:

1. `INVALID_OPERATIONAL` for any probability, replay, no-op, lifecycle, RNG or
   resume invariant failure.
2. `BENCHMARK_NON_IDENTIFIABLE` if either identifiability count floor or either
   `128`-row support floor is missed.
3. `NO_ACCESS_THIS_BENCHMARK` if maximum arm utility UCB is `<0.78`.
4. `UNDERPOWERED_ACCESS` if maximum arm utility LCB is `<0.78` while its UCB
   reaches the floor.
5. `COMMITMENT_SUPPORTED` if access is established, `LCB(G)>0.10`, every
   `K`-bin and intervention condition passes, and both
   `LCB(C_total_KEEP)>0`/`LCB(C_total_RENEW)>0` plus their frozen point floors
   pass.
6. `REPRESENTATION_ONLY` if `LCB(G)>0.10` and behavior confidently fails as
   defined above, including either `UCB(C_total_KEEP)<=0` or
   `UCB(C_total_RENEW)<=0`.
7. `ORDINARY_OR_CAPACITY_EXPLANATION_SUPPORTED` if `UCB(G)<=0.10`.
8. `MIXED_UNDERPOWERED` for every other valid numerical pattern.

The analyzer returns exactly one branch and the inputs used for every earlier
predicate; it never selects a successor, changes a threshold or performs a
post-result rescue.

## Focused acceptance evidence

The integrated package is accepted only after all of the following pass:

1. Exact CREATE/KEEP/RENEW/CLOSE transitions, q ordering and complete versus
   censored segment accounting.
2. Temporary leave/rejoin freezes and restores `h,z,q`/segment state; a due
   opportunity precedes the rejoin action; a partial rollout cutoff preserves
   lifecycle state and bootstraps without a synthetic event.
3. Matched-base OR and DUM with identical weights, observations, orders and
   primitive uniforms produce exact actions/log probabilities/values/hidden
   states when the DUM treatment input is zero.
4. DUM/EHC added parameter counts and optimizer ownership/exposure are equal;
   W_z treatment is the only primitive difference.
5. CREATE/KEEP/RENEW support is exact; all three likelihood component classes
   pass both the mixed bound and ratio cap, state fields pass absolute-only
   `1e-6`, the event joint passes its compositional/assembly and ratio gates,
   and every likelihood record contains correct worst-coordinate and ULP
   evidence. Independent float64 ordinary/saturated density references pass,
   while omitted/reversed Jacobian, wrong-mask and missing-component mutations
   fail decisively. Sampled `z` and event inputs remain detached as specified.
6. Strict checkpoint reload reproduces one rollout and update with exact
   discrete/RNG equality and all continuous/model/optimizer errors `<=1e-7`.
7. The eight result branches are mutually exclusive by first-match precedence,
   including equality and interval-crossing boundaries.
7b. `K` accounting is exact: a `CREATE`-opened spell closed by `RENEW` after two
   `KEEP` decisions records `K=3`; censored spells are excluded from complete-
   spell statistics and reported separately; temporary absence adds no
   opportunity. `I_TV` lies in `[0,1]`, is exactly zero under a softmax-common
   logit shift, and is computed from the same held-fixed state as the natural
   action.
8. Atomic JSON/checkpoint corruption and injected operational failures leave no
   authoritative partial file, publish one recomputable failure artifact and
   terminal manifest, and map by first-match semantics to
   `INVALID_OPERATIONAL`. Validators reject trusted-boolean tampering,
   missing/duplicate update or cell-batch evidence, and every copied exercise
   artifact at the formal boundary.
9. One bounded CUDA `formal_path_exercise` executes replicate 0, OR/DUM/EHC,
   one 16x80 update with four PPO passes, all four 16-episode evaluation cells,
   strict atomic `update_1.pt` round trips and exactly one
   `FORMAL_PATH_EXERCISE_COMPLETE` branch through the shared formal cores while
   every artifact remains `formal=false`.
10. Batched and independent sequential-oracle intervention/count outputs agree
    at the registered 16-environment CUDA shape; the production formal path has
    no per-environment/per-physical-step scalar CUDA intervention or event/count
    reduction, repeated trajectory packing or premature synchronization.

All local focused tests and the bounded exercise use the current default CUDA
device; tests must fail closed rather than silently fall back to CPU when CUDA
is not available. After focused checks pass, one fresh read-only Sol-xhigh reviewer inspects this
plan, the complete diff and evidence for the scientific invariants, replay and
checkpoint equivalence, throughput structure and numerical stability. At most
one concrete repair cycle is allowed before manager acceptance or a blocker.

## Implementation acceptance

Manager acceptance was completed on 2026-07-22 without launching formal
training or registered evaluation. The shared row-stable event/mark-head
helper is the sole arithmetic route for collection and teacher replay; the
registered mixed, ratio, ULP-evidence, event-joint and exact-semantic rules are
unchanged. The original CUDA collector digests remain pinned and the helper's
gradient path is non-zero for its input, weights and biases. Direct helper
permutation, partition and single-row equivalence remains exact; full stochastic
and deterministic replay is accepted only by the registered exact-field,
state, mixed-component, ratio and joint predicates, never by an additional
exact-zero requirement on tolerated continuous likelihood factors.

The complete focused CUDA file passed `54/54` in `696.06s` before removal of
one test that depended on untracked runtime logs. The final self-contained
targeted CUDA set then passed `6/6` in `150.86s`; an independent verifier
repeated the same six checks in `150.74s` and separately passed strict
checkpoint continuation. The bounded four-update shared training-core
reproduction published and revalidated all four update shards for
`OR/DUM/EHC` at 16 environments, horizon 80 and four PPO passes; its fourth
update had zero primitive, categorical, mark and event-joint replay error.
The three archived accepted formal updates revalidated under the unchanged
contract for all nine arm records, while component, support, leak, RNG,
likelihood, joint-assembly and evidence-corruption negatives remained closed.

A fresh non-formal shared-core exercise completed at
`logs/verifier_eventheld_replay_gate_repair_20260722/formal_path_exercise` with
one update, all 12 evaluation cells, strict checkpoint round trip and zero
temporary residue. Its streamed operational record validated, and the formal
analyzer and CPU fallback correctly rejected the exercise identity. The fresh
read-only final reviewer independently reran six CUDA checks and approved the
integrated package without a repair request.

The remaining risk is formal-scale runtime, storage and future backend-kernel
behavior across five replicates and 250 updates. Formal-scale execution was
intentionally unmeasured, and any future reduction drift remains fail-closed by
the unchanged per-component mixed and ratio predicates rather than being
masked by the passing compositional joint bound.

## Behavioral-battery partial-migration acceptance

The bounded partial-migration package was manager-accepted on 2026-07-22. The
active audit surface is exactly `KEEP_HELD_MARK`, `RENEW_DERANGED_MARK` and
`RENEW_CANDIDATE_MARK`; selected rows are derived outcome-blind from the compact
pre-outcome raw event trace, and the deterministic cyclic donor mapping has no
fixed key, preserves the selected candidate-mark multiset, consumes no RNG and
binds recipient/donor identity plus exact float32 payload to executed branch
evidence and the Stage-2 RNG context. Full `TrackingOutcome` leaves, roster and
count identities, utilities and frozen additive contrasts are independently
recomputed. Strict checkpoint restore leaves, collector-call telemetry,
atomic streamed publication and the width-16 CUDA execution contract remain
fail-closed.

The final post-repair CUDA acceptance file passed `54/54` in `495.34s`. The
single reviewer-requested evidence repair additionally passed the three new
coherent selected/donor/collector tamper negatives, a seven-test combined
Stage-2 regression, a four-test post-batching CUDA rerun, and the direct
synthetic-operational integration check. The existing bounded non-formal
`formal_path_exercise` completed with `formal=false`, one `16x80` update, four
PPO passes, all four 16-episode cells, `update_1.pt` round trip, width 16 and no
temporary residue; the final acceptance file also preserves formal-analyzer
rejection of exercise identity. A fresh custom CUDA verifier returned
`VERIFIED`, and the same fresh read-only final reviewer re-inspected the repaired
diff and returned `APPROVED` with all three findings closed.

Formal-scale five-replicate/250-update runtime and storage remain intentionally
unmeasured, and no new standalone exercise manifest was regenerated after the
final evidence-only repair. Assurance for that repair rests on the final full
CUDA acceptance suite and its focused independent-evidence negatives; no
formal scientific result has been produced.

## CPU Stage-2 canonical-packing repair boundary

The bounded prelaunch repair preserves the existing causal estimand and freezes
`CAUSAL_AUDIT_CONTINUOUS_ATOL = 1e-7` as the sole natural-continuation
continuous tolerance in runtime, serialization, validation and focused tests.
Discrete choices, RNG consumption, lifecycle/segment state, outcomes and
utilities remain exact. A failing natural-continuation check reports the worst
continuous field, coordinate, collected and regenerated binary32 values and
their float32 ULP distance without expanding the persisted audit-row schema.

Stage 2 no longer isolates selected environments or repacks selected branch
rows. For each selected `(batch_index, time)` cell, the original 16-environment
prefix cursor is cloned in its original episode/environment order, and one
independently regenerated authoritative future row-stream map is supplied for
every original environment. One full-width natural-control continuation
regenerates all selected natural rows in the cell simultaneously. The two
non-natural branch specifications per selected row are greedily partitioned
into full-width layers with at most one focal intervention per original
environment; distinct environments share a layer and same-environment
collisions open another layer. Every result remains bound to its original
`env_index`; all non-focal rows are independently regenerated peers rather than
padding, donors or copied future references.

The evidence budget remains three logical branch rows per selected state. The
execution record changes only to identify canonical full-width natural-control
and counterfactual layers and to count their physical rows and collector calls
honestly. There is no compatibility reader. No Stage-2 future trajectory value,
action, event, mark, hidden state, outcome or utility is copied into a branch;
no new RNG draw or DirectPrimitiveARPolicy change is permitted.

## Prohibited mechanisms

No environment-specific intrinsic reward, task shaping, identity/role input,
skill catalogue, duration action, learned hazard/terminate action, graph/team
latent, communication module, new credit objective, ordinary-access admission
gate, reward/observation/G0 change, altered budget/seed/threshold/result meaning,
formal run, compatibility path or successor selection.
