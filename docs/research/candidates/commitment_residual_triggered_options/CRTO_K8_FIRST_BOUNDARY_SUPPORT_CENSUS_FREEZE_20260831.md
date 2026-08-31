# CRTO K8 first-boundary support census freeze

Date: `2026-08-31`

Object: `CRTO-K8-FIRST-BOUNDARY-SUPPORT-CENSUS-20260831-01`

RNG namespace: `2026083192`

Freeze status: `FINAL_FOR_SUPPORT_ONLY_EXECUTION`

Execution status: `CONSUMED_BY_VALID_2026-08-31.2_RESULT`

Result evidence: `CRTO_K8_FIRST_BOUNDARY_SUPPORT_CENSUS_RESULT_20260831.md`

Claim ceiling: `FIXED_EIGHT_SLOT_K8_FIRST_BOUNDARY_SUPPORT_ONLY`

## Decision and reason for the object

The consumed two-slot RAW pilot observed zero material-KEEP rows, but that finite target does not
prove that the frozen K8 first-boundary law can never produce one. Source inspection also does not
close the existence question. The replacement charge by itself is bounded by
`4.05 / 256 = 0.0158203125`, below the material threshold `0.02`, while branch-dependent service,
overflow, energy, later review charges, terminal potential, and the complete-tape denominator can
change the sign and magnitude of the full G16 contrast. Therefore neither the fee bound nor the
pilot's two fixed addresses is an impossibility proof.

This object is the smallest complete finite census that can apply the existing all-eight-slot K8
support admission without reading the untouched confirmation namespace or training a learner. It
decides only whether its own prospectively fixed target supplies the two material strata. It does
not decide global reachability over every possible tape.

## Frozen scientific question

On every member of the fixed target below, apply the unchanged K8 first-boundary and common-future
G16 laws and define

```text
A = max_legal_replacement G16 - G16(KEEP).
```

Does every one of the eight fixed slots contain at least eight retained rows with `A <= -0.02` and
at least eight retained rows with `A >= +0.02`, after the unchanged structural support gates? If
not, does this complete target contain any constructive material-KEEP witness at all?

## Fixed target and disjointness

The complete target is exactly:

```text
rng_namespace = 2026083192
slots = (0,1,2,3,4,5,6,7)
split = EVALUATION
regime = K8
episode_indices_per_slot = 832..895
episode_count_per_slot = 64
```

For each slot, construct the tapes with the existing `build_balanced_tapes` law, `count=64`, and
`first_episode_index=832`. The 64 rows are one complete crossed block of the four event classes,
the two costs `(0.25,4.0)`, and the eight fixed-K8 onsets. Counter addressing, manifest shuffling,
episode materialization, deterministic scripted behavior, and printed order remain unchanged.

Namespace `2026083192` was source-searched before this freeze and had no tracked use. It is distinct
from the consumed pilot namespace `2026083191` and the untouched confirmation namespace
`2026083001`. This object must not instantiate, derive a seed from, scan, read, or compare either of
those namespaces or any prior result artifact.

All eight slots and all 512 preassigned episodes must be scanned. No early stop, available-slot
subset, retry, replacement address, caller-selected seed, or post-result expansion is allowed.

## Frozen boundary and value law

For each tape, traverse the base host under the exact deterministic `scripted_decisions` law. Scan
primitive time and then environment slot in canonical order. Retain only the first legal
discretionary review that has a different legal replacement, a continuous commitment, elapsed
horizon in `{4,8,12,16}`, `event_or_pseudo_onset+4 <= t <= event_or_pseudo_onset+20`,
`abs(t-128)>8`, and `t+16<=256`. Boundary selection may inspect no future, G16 value, residual,
learner action, or result.

At a retained boundary enumerate KEEP followed by every legal changed option in printed order.
Other simultaneous decisions are the aligned script decisions. Starting at the next primitive
step, the unchanged script controls all agents. Every branch uses the same immutable future tape,
executes exactly 16 steps, charges the target action exactly once at the boundary, and computes the
existing discounted reward plus terminal-potential G16 divided by the complete-tape physical
arrival count. No predictor or residual packet is needed to compute this support object.

Classify endpoints inclusively and leave the middle unstratified:

```text
KEEP_MATERIAL   if A <= -0.02
MIDDLE          if -0.02 < A < +0.02
REPLAN_MATERIAL if A >= +0.02.
```

## Completeness, evidence, and validation

A valid receipt contains every preassigned row, including an explicit absent-boundary record. For
every retained row it records at least:

- slot, episode index, event, cost, onset, episode seed, primitive time, target agent, and elapsed
  horizon;
- the legal printed-action mask, finite legal G16 vector, KEEP G16, maximum-replacement G16,
  maximizing printed replacement, exact `A`, and material class;
- exactly-16 branch-step and charge-once validation; and
- the exact scenario/counter coordinates and, for every canonical tape field, its dtype, shape, and
  raw-byte length; before either rollout pass, that pass independently rebuilds the tape from the
  fixed namespace, slot, and episode member and directly compares every field's raw bytes.

The receipt also records per-slot availability and KEEP/MIDDLE/REPLAN counts, global counts and A
extrema, exact base and common-future work for both passes, wall/RSS facts,
object/namespace/claim-ceiling constants, and activity counters. Within the same monitored worker,
the first pass independently constructs all 512 canonical tapes and records the complete boundary
and branch provenance. Before publication, a second pass independently constructs every tape again
without reusing the first pass's tape cache, traverses the exact host, finds the canonical first
boundary, and repeats every complete common-future G16 branch. The worker directly compares the
second pass's full provenance with the first pass's recorded provenance row by row. The prospective
worst-case work ceiling is exactly `393216` primitive team steps:

```text
2 * 512 * (256 base steps + 8 legal branches * 16 future steps).
```

The receipt validator is deliberately different from those two worker passes: it performs only
schema, ordering, direct recorded-value, arithmetic, continuity, G16, count, witness, resource, and
disposition recomputation over the complete recorded provenance. It cannot call the host, tape
builder, boundary selector, or G16 rollout. It rejects duplicate, missing, unordered, or mismatched
rows and requires all 512 target members.

The inherited K8 support admission remains unchanged: every slot has all 64 unreplaced episodes,
at least 48 retained boundaries, finite legal G16 labels, valid common futures, and at least eight
retained rows in each material stratum. No 80% derangement-cell gate is needed because this object
constructs no derangement; it must still report elapsed-horizon/cost cell counts so a successor
cannot silently infer representation support from this census.

## Mutually exclusive disposition

After technical validity, route exactly one branch:

```text
CENSUS_SUPPORT_FEASIBLE
    every slot passes availability/common-future validity and has
    KEEP_MATERIAL >= 8 and REPLAN_MATERIAL >= 8

CENSUS_KEEP_WITNESS_BUT_KEEP_MINIMUM_FAIL
    at least one KEEP_MATERIAL witness exists, but one or more slots has
    KEEP_MATERIAL < 8; REPLAN support remains a diagnostic on this branch

CENSUS_KEEP_MINIMUM_PASS_REPLAN_MINIMUM_FAIL
    every slot has KEEP_MATERIAL >= 8, but one or more slots has
    REPLAN_MATERIAL < 8

CENSUS_NO_KEEP_WITNESS_ON_FIXED_TARGET
    no retained member of the complete 512-episode target has A <= -0.02
```

Any missing target member, malformed/nonfinite value, resource refusal, namespace leak, partial
publication, or incomplete execution is `INCOMPLETE_ASSIGNMENT_NO_CONSUMPTION`, not a scientific
branch. A valid completed branch consumes this census object.

`CENSUS_NO_KEEP_WITNESS_ON_FIXED_TARGET` is an exact no-witness statement only for these 512 fixed
members. Either witness-bearing failure proves constructive reachability only for the recorded
member(s). `CENSUS_SUPPORT_FEASIBLE` proves only support feasibility of this fixed target. None of
the branches estimates a seed frequency or changes RAW competence, residual, representation,
optimization, policy, MARL, safety, or deployment polarity.

## Result-blind execution and resource law

The implementation and launcher must remain import-safe and fail closed. They may import the
physical host, tape construction, frozen boundary selector, common-future G16, and shared resource
helpers. They may not import Torch, predictor/model/training/calibration/packet/derangement paths;
construct a model, optimizer, checkpoint, scientific learner root, or TRUE/DERANGED cell; or read
the pilot, confirmation, or any existing result namespace.

Immediately before every result-bearing invocation, retry, resume, or slice, run

```text
python scripts/hmasd_resource_preflight.py admit-memory --out <fresh-receipt>
```

and require both physical and effective available memory to be at least 4 GiB. The census command
must itself require and validate a fresh create-only memory receipt and same-envelope `assess-run`
receipt before constructing its first RNG address or tape. Both complete rollout passes, final
summarization, encoding, staging writes, flushes, and filesystem synchronization occur inside the
same resource monitor and before scientific commit. Publication preparation iterates the terminal
runtime snapshot, complete receipt validation, encoding, and both create-only staging files until
the validated bytes and the staged bytes are the same terminal candidate. It then applies the
frozen resource checks and reserves exactly `10.0` wall seconds, `2.0` CPU seconds, `33554432` peak
RSS bytes, `1048576` read bytes, and `1048576` write bytes as commit headroom. The short commit tail is explicitly
outside the measured scientific runtime and may only rename the two already-synchronized staged
files and create the direction completion marker; no host work, result validation, resource check,
or byte comparison may occur after commit begins. The direction completion marker is the sole
commit authority, so an external file without that marker is an uninterpretable orphan. No partial
witness or count may be interpreted before the marker and the prospectively checked direct byte
equality of the two staged candidates.

### Frozen host interpreter and replacement operator command

The first operator invocation is quarantined as
`INCOMPLETE_PRE_RESULT_INTERPRETER_DEPENDENCY`. Its fresh external admission passed, but the
PATH-resolved interpreter lacked NumPy and failed while importing package configuration. The
isolated worker never started; no direction root, worker receipt, tape, host state, or result was
created. That attempt did not consume the scientific object, and its memory receipt must not be
reused.

The outcome-blind replacement fixes the exact interpreter to:

```text
C:\Users\fires\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe
```

Before creating its fresh external admission receipt, that interpreter must successfully import
NumPy, the registered launcher, the support receipt module, and the isolated worker. The import
precheck may create no direction root, tape, host state, worker receipt, or result. The operator
first fixes the repository working directory, binds all five replacement targets to exact absolute
paths, and refuses if any target exists. It repeats the same five-path refusal immediately after
the import precheck and before the admission receipt can be written. There is no PATH fallback or
alternate executable after the precheck. The same exact interpreter must then run the fresh memory
admission and, if both 4 GiB floors pass, the one registered census command.

The reviewed replacement command and fresh paths are exactly:

```powershell
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'C:\Projects\HMASD'
$crtoPython = 'C:\Users\fires\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$crtoOperatorReceipt = 'C:\Projects\HMASD\temp\directions\commitment_residual_triggered_options\support_census\2026-08-31.2-operator-memory.json'
$crtoOutputRoot = 'C:\Projects\HMASD\temp\directions\commitment_residual_triggered_options\support_census\2026-08-31.2-direction'
$crtoResultPath = 'C:\Projects\HMASD\temp\directions\commitment_residual_triggered_options\support_census\2026-08-31.2-result.json'
$crtoWorkerMemory = 'C:\Projects\HMASD\temp\directions\commitment_residual_triggered_options\support_census\2026-08-31.2-worker-memory.json'
$crtoWorkerAssessment = 'C:\Projects\HMASD\temp\directions\commitment_residual_triggered_options\support_census\2026-08-31.2-worker-run-assessment.json'
$crtoFreshPaths = @($crtoOperatorReceipt, $crtoOutputRoot, $crtoResultPath, $crtoWorkerMemory, $crtoWorkerAssessment)
if (@($crtoFreshPaths | Where-Object { Test-Path -LiteralPath $_ }).Count -ne 0) { exit 92 }
& $crtoPython -c "import numpy; import experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.run; import experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.support_census; import experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.support_census_worker"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (@($crtoFreshPaths | Where-Object { Test-Path -LiteralPath $_ }).Count -ne 0) { exit 93 }
& $crtoPython scripts/hmasd_resource_preflight.py admit-memory --out $crtoOperatorReceipt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$crtoAdmission = Get-Content -Raw -LiteralPath $crtoOperatorReceipt | ConvertFrom-Json
if (-not $crtoAdmission.passed -or -not $crtoAdmission.physical_floor_pass -or -not $crtoAdmission.effective_floor_pass -or [int64]$crtoAdmission.available_physical_bytes -lt 4294967296 -or [int64]$crtoAdmission.effective_available_bytes -lt 4294967296) { exit 91 }
& $crtoPython -m experiments.candidates.commitment_residual_triggered_options_common_history_gate_r01.run support-census --output-root $crtoOutputRoot --result $crtoResultPath --resource-receipt $crtoWorkerMemory --run-resource-receipt $crtoWorkerAssessment
exit $LASTEXITCODE
```

The replacement remains forbidden until its non-result import/help/regression checks and independent
review pass and Root grants a new unique outcome-bearing slot.

## Decision effect and flip conditions

- `CENSUS_SUPPORT_FEASIBLE` supports registering a separate, prospectively frozen successor
  confirmation object; it does not unlock or inspect namespace `2026083001` automatically.
- Either witness-bearing support failure supports recasting the competence population or boundary
  object around an explicitly sampled material-decision target. It does not justify lowering
  `0.02` or the per-slot minimum after observation.
- `CENSUS_NO_KEEP_WITNESS_ON_FIXED_TARGET`, combined with the consumed pilot's zero witnesses,
  supports closing the current natural first-boundary CRTO investment for lack of decision support,
  while preserving re-entry on a source-level constructive witness or a newly justified target law.

The Portfolio lifecycle action belongs to Root. This document freezes a direction-local scientific
object and its interpretation only.
