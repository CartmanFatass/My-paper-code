# CRTO RAW pilot evidence — 2026-08-31

Object: `CRTO-COMMON-HISTORY-RAW-PILOT-20260831-01`

Claim ceiling: `TWO_SLOT_RAW_LONG_DEVELOPMENT_FEASIBILITY_ONLY`

## Attempt `2026-08-31.1`

### Question

Did this invocation completely implement the frozen two-slot RAW-LONG pilot assignment and produce
an interpretable feasibility observation?

### Inputs

- the fixed pilot object, namespace `2026083191`, and slots `(0,1)` in
  `CRTO_COMMON_HISTORY_GATE_R01_COMPETENCE_AND_CENSUS_FREEZE_20260831.md`;
- the pilot entry in `IMPLEMENTATION_THRESHOLD.md`;
- the three fresh memory receipts listed below; and
- direct operator observation reconciled with
  `pilot.py::_run_raw_only_pilot_worker` and the resource CLI's lowercase `run_id` law.

### Direct observation

The operator, pre-scan, and post-scan launch memory receipts all passed the 4 GiB physical and
effective floor:

| receipt | physical/effective available bytes |
| --- | ---: |
| `2026-08-31.1-operator-memory.json` | `16,199,634,944` |
| `2026-08-31.1-prescan-memory.json` | `16,171,368,448` |
| `2026-08-31.1-launch-memory.json` | `16,161,722,368` |

The worker then requested the post-scan `assess-run` receipt with generated `run_id`
`CRTO-COMMON-HISTORY-RAW-PILOT-20260831-01-LAUNCH`. The shared resource CLI accepts only lowercase
`[a-z0-9_-]` identifiers and refused that value. No `assess-run` receipt was created. The operator
observed no pilot output root or result, and at the `.1` audit time the pilot runtime directory
contained only the three memory receipts above.

In the source path, the post-scan memory receipt is created only after the structural scan returns
`passed=true`; thread binding, staging-root creation, predictor/model construction, optimizer work,
and result publication occur only after the failed `assess-run` call. Thus the durable third receipt
and control flow establish that execution crossed the result-blind scan gate but stopped before any
question-bearing pilot work. The scan itself was not published, so no row, branch, cell, or support
count is accepted from this attempt.

### Limitations

There is no RAW checkpoint, competence cell, learner action, scientific root, result payload, or
TRUE/DERANGED activity to inspect. The operator error was not a scientific endpoint. Passing memory
receipts establish only resource availability at their capture instants; they do not establish
pilot feasibility.

### Judgment impact

Disposition: `INCOMPLETE_ASSIGNMENT_NO_CONSUMPTION`.

The missing required post-scan `assess-run` admission makes this an incomplete implementation of the
frozen assignment. It has no competence, representation, optimization, policy-return, or Portfolio
polarity and does not consume either the pilot object or the untouched fixed-eight confirmation
object. The three receipts are retained only as engineering evidence; there is no scientific result
to salvage or reinterpret.

The cheapest next action is the result-blind engineering correction to the internally fixed
lowercase `run_id`, followed by implementation re-review. A fresh outcome-blind replacement may
then execute the unchanged pilot with new create-only output, result, memory, and `assess-run`
paths. The object ID, namespace, slots, data, budgets, thresholds, stop law, and claim ceiling remain
unchanged.

### Exact evidence paths

- `temp/directions/crto/pilot/2026-08-31.1-operator-memory.json`
- `temp/directions/crto/pilot/2026-08-31.1-prescan-memory.json`
- `temp/directions/crto/pilot/2026-08-31.1-launch-memory.json`
- `experiments/candidates/commitment_residual_triggered_options_common_history_gate_r01/pilot.py`
- `scripts/hmasd_resource_preflight.py`

## Replacement attempt `2026-08-31.2`

### Question

Does the unchanged fixed two-slot development population provide both material KEEP and material
REPLAN rows in every slot, and, only if it does, is RAW-LONG competent at the frozen `0.01` ceiling?

### Inputs

- the unchanged pilot object, namespace, slots, population, row law, support law, budgets, and claim
  ceiling above;
- fresh operator, pre-scan, launch-memory, and launch-`assess-run` admissions; and
- the create-only result and byte-identical output receipt listed below.

The direct result validator passed, and the external result bytes equal the direction-owned
`pilot_receipt.json` bytes.

### Direct observation

The result is valid `NONIDENTIFYING_PILOT_K8_SUPPORT`. Both slots retained all 64 fixed-K8
evaluation rows, and the result-blind scan retained and supported all `1,152/1,152` TRAIN plus
EVALUATION boundaries. However, the prospectively defined material counts were:

| slot | `KEEP_MATERIAL` | `REPLAN_MATERIAL` |
| ---: | ---: | ---: |
| 0 | 0 | 14 |
| 1 | 0 | 18 |

Each slot therefore failed the required minimum of eight `KEEP_MATERIAL` rows before RAW gate
construction. The execution created two fresh predictor models but zero RAW gate models, zero RAW
optimizer updates, no checkpoint, and no competence cell. `summaries` is empty. TRUE and DERANGED
training/evaluation, final-namespace reads, and final-artifact reads are all zero, and
`final_namespace_untouched=true`.

The prospective and actual work ledgers agree exactly: `3,632` common-future branches, `58,112`
common-future steps, `425,984` base steps, and `484,096` total primitive team steps. Runtime was
`736.922` seconds with peak RSS `1,968,742,400` bytes, one worker, and one thread. Every recorded
memory and `assess-run` admission passed, and all work stayed below the registered ceilings.

### Technical acceptance

The strict result validator passes the external result directly. The operator, pre-scan, and launch
memory receipts independently pass the 4 GiB validator; the launch `assess-run` receipt passes its
one-worker/one-thread envelope validator. The three worker-bound receipts embedded in the result
exactly equal their corresponding files. The output directory contains only `pilot_receipt.json`;
that file and the external result are byte-identical at `7,971` bytes, and no staging residue is
present.

The observed peak RSS leaves `178,741,248` bytes (`170.461 MiB`, `8.323%`) below the 2 GiB ceiling.
The wall observation leaves `6,463.078` seconds below 7,200 seconds, and the exact work leaves
`2,112,768` primitive team steps below the fixed ceiling. These margins accept the support-stop
transaction only; they do not measure RAW training or long confirmation throughput. Neither the
preflight nor production launcher reads pilot artifacts, and the exact failed
`long_production_efficiency_review` gate remains mandatory, so this artifact cannot unlock full
production.

### Limitations

The empty KEEP stratum prevents the four-cell two-sided competence estimand from existing on this
finite pilot target. Consequently, this is not `PILOT_RAW_LONG_INCOMPETENT`: no RAW learner was
trained or evaluated. Two fixed development slots are a complete target for this pilot, not a
probability sample, so their common support failure estimates neither the frequency of failure nor
the support status of confirmation addresses `0..7` in namespace `2026083001`.

The observed wall and RSS cover the support-stop path through two predictor fits and exact G16
enumeration. They do not measure RAW gate optimization, six representation-by-budget cells, or the
full confirmation path and therefore do not close the separate long-production efficiency question.

### Judgment impact

The smallest supported proposition is:

> On the complete fixed pilot target `(namespace 2026083191, slots 0 and 1)`, structural support and
> resource/work validity passed, but neither slot contained a material KEEP row, so the registered
> two-sided RAW-LONG competence question was nonidentifying before RAW training.

This valid completed support branch consumes
`CRTO-COMMON-HISTORY-RAW-PILOT-20260831-01`; it must not be rerun, resumed, or rescued by changing
the material margin, row law, addresses, minimum count, or checkpoint. It does not consume the
disjoint fixed-eight confirmation object, which remains scientifically live and directly observed
as untouched. It supplies no residual, representation, optimization, policy-return, MARL,
promotion, closure, or confirmation polarity, and it does not establish that RAW is incompetent.

The leading explanation is a support mismatch between the frozen K8 first-boundary surface and the
two-sided KEEP/REPLAN competence estimand. The strongest surviving alternative is address-specific
finite-panel variation: the untouched confirmation addresses may contain material KEEP rows, but
this pilot supplies no probability law for that possibility.

Before investing in confirmation, the cheapest next discriminator is an exact source-level
derivation or finite development-only support census of
`A=max_replacement G16-G16(KEEP)` under the frozen K8 first-boundary law. It should ask whether any
reachable event-by-cost-onset cell can satisfy `A<=-0.02`, without reading namespace `2026083001`
and without training a learner. A proof that none can do so makes the current confirmation
competence gate structurally nonidentifying. A constructive material-KEEP witness instead justifies
a separately registered, disjoint support-only object to determine whether that witness is actually
reachable under a prospectively fixed population. Neither branch retroactively changes this pilot.

### Exact evidence paths

- `temp/directions/crto/pilot/2026-08-31.2-operator-memory.json`
- `temp/directions/crto/pilot/2026-08-31.2-prescan-memory.json`
- `temp/directions/crto/pilot/2026-08-31.2-launch-memory.json`
- `temp/directions/crto/pilot/2026-08-31.2-launch-assess-run.json`
- `temp/directions/crto/pilot/2026-08-31.2-result.json`
- `temp/directions/crto/pilot/2026-08-31.2-output/pilot_receipt.json`
