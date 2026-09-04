# CRTO K8 first-boundary support census result

Date: `2026-08-31`

Object: `CRTO-K8-FIRST-BOUNDARY-SUPPORT-CENSUS-20260831-01`

Status: `VALID_COMPLETED_DIRECTION_EVIDENCE`

First-true disposition: `CENSUS_NO_KEEP_WITNESS_ON_FIXED_TARGET`

Claim ceiling: `FIXED_EIGHT_SLOT_K8_FIRST_BOUNDARY_SUPPORT_ONLY`

## Attempt chronology

The first operator invocation is quarantined as
`INCOMPLETE_PRE_RESULT_INTERPRETER_DEPENDENCY`. It stopped during package import before the isolated
worker started and did not consume the object. Its facts and outcome-blind repair are recorded in
`CRTO_K8_FIRST_BOUNDARY_PRE_RESULT_INTERPRETER_REPAIR_20260831.md`.

Root granted one replacement slot after the repaired command and independent review passed. The
replacement used the exact bundled interpreter and fresh `.2` paths, passed its external memory
admission, ran the registered CLI exactly once, and exited `0`. There was no retry, resume, alternate
interpreter, alternate path, learner, pilot read, confirmation read, commit, or push.

## Durable artifacts

- external result:
  `temp/directions/commitment_residual_triggered_options/support_census/2026-08-31.2-result.json`
- direction receipt:
  `temp/directions/commitment_residual_triggered_options/support_census/2026-08-31.2-direction/support_census_receipt.json`
- direction completion marker:
  `temp/directions/commitment_residual_triggered_options/support_census/2026-08-31.2-direction/PUBLICATION_COMPLETE.json`
- operator memory admission:
  `temp/directions/commitment_residual_triggered_options/support_census/2026-08-31.2-operator-memory.json`
- worker memory admission:
  `temp/directions/commitment_residual_triggered_options/support_census/2026-08-31.2-worker-memory.json`
- worker run assessment:
  `temp/directions/commitment_residual_triggered_options/support_census/2026-08-31.2-worker-run-assessment.json`

The external result and direction receipt are directly byte-equal and each contains `79130125`
bytes. The direction root contains only the receipt and completion marker. The marker is complete,
names the frozen object, and carries the registered external-first/direction-second publication law.

## Admission and resource observations

The fresh operator admission immediately before launch recorded:

```text
available physical bytes = 15447609344
effective available bytes = 15447609344
physical floor = PASS
effective floor = PASS
```

The isolated worker's fresh admission recorded:

```text
available physical bytes = 15384293376
effective available bytes = 15384293376
physical floor = PASS
effective floor = PASS
```

The worker run assessment recorded:

```text
total memory bytes = 31982620672
effective limit GiB = 29.786137
effective available GiB = 14.320030
reserve GiB = 5.957227
usable GiB = 8.362803
adjusted prospective peak GiB = 2.5
memory floor = PASS
memory safe = true
workers / threads = 1 / 1
```

The final monitored runtime record is:

```text
wall seconds = 104.5309999999954          ceiling = 7200
CPU seconds = 84.25
CPU occupancy fraction = 0.8059810008514575
peak RSS bytes = 744304640                 ceiling = 2147483648
scratch high-water bytes = 324909136
durable high-water bytes = 324910653
read bytes = 799689896
write bytes = 799690676
charged primitive team steps = 314208      ceiling = 393216
workers / threads = 1 / 1
measurement cutoff = AFTER_FINAL_DUAL_STAGING_FSYNC_BEFORE_COMMIT_RENAMES
```

The final candidate staging rehearsal observed `74.531` wall seconds, `74.25` CPU seconds,
`744304640` peak RSS bytes, `474780760` read bytes, and `474781540` write bytes. The frozen commit
headroom remained `10` wall seconds, `2` CPU seconds, `33554432` RSS bytes, and `1048576` bytes for
each I/O direction.

## Technical validity

The pure receipt validator passed after publication. It did not invoke the tape builder, host, or
G16 rollout.

Both complete passes were present in the ledger:

```text
materialization base episodes / transitions = 512 / 67584
validation base episodes / transitions = 512 / 67584
materialization branches / future steps = 1627 / 26032
validation branches / future steps = 1627 / 26032
total branches / future steps = 3254 / 52064
```

The independent pass rebuilt all `512` tapes, directly matched all `512` scenario records, directly
matched `3072` tape arrays, compared `8914944` raw bytes per side, and directly matched all `512`
complete boundary/G16 provenance records. Every assigned episode produced a retained boundary; no
member was missing, replaced, or stopped early.

Activity accounting was:

```text
support tapes / boundaries materialized = 1024 / 1024
common-future rollouts = 3254
learner, predictor, and gate models = 0
optimizer updates / checkpoints = 0 / 0
pilot reads / confirmation reads = 0 / 0
TRUE / DERANGED activity = 0 / 0
```

## Registered scientific result

| Slot | Retained | KEEP | MIDDLE | REPLAN | Minimum A | Maximum A |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 64 | 0 | 40 | 24 | -0.0159721338 | 0.0542003385 |
| 1 | 64 | 0 | 48 | 16 | -0.0159002011 | 0.0540146022 |
| 2 | 64 | 0 | 45 | 19 | -0.0161997883 | 0.0568122381 |
| 3 | 64 | 0 | 41 | 23 | -0.0156151378 | 0.0384942348 |
| 4 | 64 | 0 | 45 | 19 | -0.0161624725 | 0.0547787430 |
| 5 | 64 | 0 | 42 | 22 | -0.0159246704 | 0.0533134021 |
| 6 | 64 | 0 | 43 | 21 | -0.0155300337 | 0.0551266093 |
| 7 | 64 | 0 | 49 | 15 | -0.0154916979 | 0.0534374347 |

Global counts were:

```text
KEEP = 0
MIDDLE = 353
REPLAN = 159
minimum A = -0.01619978828524196
maximum A = 0.056812238064408105
```

All `512` retained rows occurred at elapsed horizon `4`; each slot retained the complete `32/32`
cost split. Every slot exceeded the existing minimum of eight REPLAN rows, while every slot had
zero KEEP rows. The most KEEP-favoring member was slot `2`, episode `883`, event `NONE`, onset `66`,
cost `4.0`, boundary time `76`, agent `0`; its `A=-0.01619978828524196` remained in MIDDLE and missed
the inclusive material threshold by approximately `0.0038002117`.

## Scientific interpretation and external advice

This completed object proves exactly that the prospectively fixed 512-member generator target has
no material-KEEP first boundary. It does not prove that every integer-addressed K8 tape lacks such a
boundary and does not estimate a witness frequency.

Together with the consumed two-slot pilot, the direction now has `640` valid fixed generated rows
across ten complete slot blocks and zero material-KEEP observations. This is a descriptive union of
two fixed objects, not a sample from a claimed population.

The archived Pro response supplied a credible component-valid reset-tape construction with a
material-KEEP boundary. That lower-domain construction remains useful: it shows that host dynamics
alone do not make KEEP impossible. It is not a generated-address witness. The new result therefore
localizes the contradiction rather than erasing it: component-valid host support contains a witness,
but the ten completed generated slot blocks supplied no witness under their exact address laws.

No representation or optimization conclusion follows. The result does not test RAW, residual,
TRUE, DERANGED, a predictor, a gate, a checkpoint, policy return, variable K, MARL, safety, or
deployment value.

## Direction-local lifecycle recommendation

Recommend that Root close the current natural first-boundary CRTO investment and leave the untouched
confirmation object unread. The direction's own admission law requires at least eight material KEEP
and eight material REPLAN rows in every slot. The registered census found adequate REPLAN support in
all eight slots and exactly zero KEEP support in all eight. Training a learner or opening the final
confirmation target cannot repair that missing prerequisite without changing the scientific object.

Do not lower `0.02`, change the first-boundary selector, search more addresses because of this null,
or reinterpret MIDDLE rows as KEEP. Any such move would be outcome-informed claim drift.

Re-entry requires a genuinely new, prospectively justified object, such as:

- a concrete generated-address material-KEEP construction derived without searching after this
  result;
- a source-level characterization that connects a nontrivial material-KEEP tape set to the exact
  generator image; or
- a scientifically motivated population or boundary estimand defined independently of this result,
  with its own support law and thresholds.

The external lower-domain construction alone is insufficient for re-entry because it still lacks a
generated address. Another arbitrary finite address block is also insufficient: it would be an
outcome-informed extension of the consumed support search rather than a new scientific reason.

Portfolio closure belongs to Root. Direction-local evidence supports
`CLOSE_CURRENT_CRTO_NATURAL_FIRST_BOUNDARY_INVESTMENT`, with no successor registration and no final
namespace read.
