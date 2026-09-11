# DISH B08 E0 result evidence — 2026-09-10

The sole matched seed137 pair is a complete **B/EXPLORE native-service result**:
`Delta_bridge=-6.5` ticks. REPLACE averages441 and HALF_RETAIN434.5. This is a small
negative inside the±24 effect band, with one independent training pair. The scientific
decision is recorded in the [result intake](DISH_ARRIVAL_BRIDGE_RETENTION_B08_RESULT_INTAKE_20260910.md).

## 1. Frozen question and rule

The [B08 card](DISH_ARRIVAL_BRIDGE_RETENTION_B08_SCIENCE_CARD_20260910.md) §§1–6 was frozen
at `db2480c2ca1e21592a785582c0c5ec0c2c4cb3c6`; its prospective internal reserve correction
is in§7 at `a01522a6f6cf12e5549b3e03596ce58642b68cf1`. At the actual received-snapshot
mask, after reset and before the normal GRU, HALF_RETAIN uses `0.5*h+0.5*b`; REPLACE uses
the complete learned bridge `b`. Both are fresh STRUCTURED/DIRECT_MEAN learners with
the original PPO/AdamW, private labels and LOW_LR recipe on retained A03. Update16 is
the sole selected checkpoint; there are no initial-policy evaluation episodes.

The primary rule, verbatim: **`Delta_bridge = (1/4) * sum_r(J_HALF_RETAIN,r - J_REPLACE,r)`**.
The applicable card§4 rows, verbatim:

| Observation | Reading rule and recommendation |
| --- | --- |
| Negative mean, especially≤−24, or gain outweighed by native harm | Favor REPLACE and ending this fixed candidate's extension. Proxies cannot rescue adverse service. |
| No ordinary CAS | Final-service comparison remains readable; source-origin and COPY−RETAIN/SHADOW−COPY remain unestimated. |

The mean is negative but does **not** cross−24. No equality, stable inferiority, population
interval or mechanism diagnosis follows. No input, recurrent-state, learner or primary
defect was found. Missing resource/cost coverage below limits its dependent cost claim.

## 2. Execution, bytes and technical acceptance

- Source: `a01522a6f6cf12e5549b3e03596ce58642b68cf1`; committed command binding:
  `fdc813bfe638966469c4c39c1d1876940c2ef1b5`.
- One accepted handle: `dish-b08-s137-a01522a6-20260910`, wsl_4070 via `hmasd-wsl-node`;
  CPU policy float32, native float64, one Torch/BLAS compute thread.
- Actual run root ended `arrival_bridge_retention_b08_seed137_20260910_run01` within
  `/home/wu/hmasd-worktrees/dish-b08-db2480c2/temp/directions/degraded_incumbent_shadow_handover/exp/`.
  The abbreviated Root terminal message omitted `_run01`; that abbreviated path did not
  exist. The committed command, supervisor record, Monitor receipt and collected bytes agree
  on the actual path. This is a receipt correction, not a second invocation.
- Adjacent [memory admission](evidence/2026-09-10-b08-memory-admission.json) passed at
  2026-09-10T21:18:16.757Z, physical/effective available15,631,826,944 bytes each≥4GiB.
  The complete supervisor command joins admission and runner with`&&`.
- Terminal supervisor status is finished/exit0; remote exit2026-09-11T05:25:51+08:00,
  equivalently2026-09-10T21:25:51Z. The native process was detached and Monitor-adopted.

The [execution record](evidence/2026-09-10-b08-execution.json), prior independent recurrent
review and twelve accepted focused cases are reused. They cover live/replay preparation,
both owners/reset/masks, likelihood, retained-state gradients, checkpoint reconstruction,
primary reduction, genuine early terminals and publication. No broad suite or scientific
execution was repeated during collection. The earlier missing test-basetemp parent and
failed source-staging operations remain charged in the execution record.

The [collection manifest](evidence/2026-09-10-b08-collection.json) records all14 retained
files with sizes and SHA256 digests. It includes both final checkpoints, initial payload,
resets, summary, adjacent receipts and supervisor records. Important byte identities:

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| summary.json | 70423 | `918dba48bc428d1d08e3656e186969a3888c9f491734afac602debcc1bd45f4c` |
| REPLACE checkpoint_update16.pt | 2356639 | `24d88f533ad722ba6cd8b6d29a07fbde43ceceb2c1c97b42b700a190a6e1b0c0` |
| HALF_RETAIN checkpoint_update16.pt | 2356639 | `dd55c0c799261b46f1f3cbe247bd241b2e581ef2fb9a3af1ca92cefb74569a99` |
| shared initial_state.pt | 836667 | `24c7e28f880b73a4f603e891d5c79d6b614820dd4830217b69886a0a4d165982` |
| complete_evidence.tar.gz | 4589570 | `abb98590a104842175ae43e8062020ffc336c5f9e765cccb4e334999ce56655e` |

The declared seed/master were verified against SHA256 of ASCII
`DISH-ARRIVAL-BRIDGE-RETENTION-B08/seed/137`:
`65e6b46904b9e362207dd1f9cd103243dadb4a9208efe6884cee0e2c559a1ae7`.
All four paired reset dictionaries match each other and the recorded master/coordinates.
The shared initializer has zero Welford counts. Its raw default optimizer rate3e-4 is
rewritten before arm training; both groups are3e-5 in all16 update receipts and final
checkpoints. Both checkpoints restore their exact arrival mode, contain204,211 finite
float32 model values and preserve update16.

| Learner fact | REPLACE | HALF_RETAIN |
| --- | ---: | ---: |
| Ordinary transitions / next-label steps | 65536 / 65536 | 65536 / 65536 |
| Completed updates / optimizer calls | 16 / 512 | 16 / 512 |
| Initial model norm | 38.19922591660154 | 38.19922591660154 |
| Parameter L2 displacement | 1.884492348853397 | 1.9350219357396847 |
| Relative L2 displacement | 0.04933326012856163 | 0.05065605098816194 |
| Actor / critic Welford count | 262144 / 65536 | 262144 / 65536 |
| Masked snapshot Welford count | 13263 | 13949 |
| Adam per-parameter step values present | 398,512 | 397,512 |

The last row is distinct from the512 optimizer calls per arm. A post-run extraction check
incorrectly required every parameter counter to equal512; that analysis assumption was
removed and the stored values reported. No runner, checkpoint, optimizer or frozen exposure
was changed. Snapshot Welford samples follow the received mask in the accepted source;
they establish training exposure, not independent samples or useful memory causality.
All update loss/gradient finiteness flags are true; large finite gradient norms remain.

## 3. All final service outcomes and native companions

Each condition uses speed4, slot0, block0, modal deployment at update16, with a fresh native
and recurrent state and the arm's fixed training normalization. All eight episodes completed
1200 ticks with fixed-horizon native termination; unstepped zero-service remainders are0.

| Condition | REPLACE service | HALF_RETAIN service | Difference | REPLACE energy | HALF_RETAIN energy | Energy difference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TARGET_VISUAL_MASK / K8 | 507 | 492 | -15 | 272828.953055 | 272157.631769 | -671.321286 |
| TARGET_VISUAL_MASK / K4_TO_K12 | 163 | 163 | 0 | 268951.689506 | 270019.610005 | +1067.920500 |
| TERRAIN_RELAY_MASK / K8 | 921 | 913 | -8 | 269910.668264 | 269718.952470 | -191.715794 |
| TERRAIN_RELAY_MASK / K4_TO_K12 | 173 | 170 | -3 | 261032.184238 | 250842.544572 | -10189.639666 |
| Equal-condition mean | 441 | 434.5 | **-6.5** | 268180.873766 | 265684.684704 | -2496.189061 |

All final legal-transfer counts are0, first transfer ticks are null, owner/actuator owner
remain0, service-before-transfer equals total service and service-at/after-transfer is0.
The temporal split cannot identify packet/source value. All adverse rows remain in the
primary. `new:LOW_LR:update16` is the inherited recipe label in each raw row; the arm,
arrival-mode and checkpoint fields identify the actual B08 comparison.

| Native event count | TRAIN REPLACE | TRAIN HALF_RETAIN | EVAL REPLACE | EVAL HALF_RETAIN |
| --- | ---: | ---: | ---: | ---: |
| buffer_clear | 0 | 0 | 0 | 0 |
| command_slew_breach | 0 | 0 | 0 | 0 |
| dual_owner | 0 | 0 | 0 | 0 |
| dual_payload | 0 | 0 | 0 | 0 |
| invalid_commit | 2725 | 2983 | 0 | 4 |
| separation_breach | 1 | 1 | 0 | 0 |
| token_gap | 0 | 0 | 0 | 0 |

All four EVAL invalid commits occur in HALF_RETAIN's TERRAIN/K4_TO_K12 episode. TRAIN
denominators are65,536 ordinary transitions per arm; EVAL denominators are4,800 actual ticks
per arm. These counts are not per-opportunity probabilities or a safety claim. Training
service is20257/20226, energy14823579.448653633/14797143.800520549, terminal episodes33/33
and ordinary legal transfers0/0 (REPLACE/HALF_RETAIN). Training summaries are not pooled
with final evaluation. Lower mean EVAL energy accompanies less service and is not an
equal-service efficiency comparison.

## 4. Exposure, resources and complete cost boundary

Machine-checked exposure: **2 fresh learners,1 matched training pair,131,072 ordinary
training transitions,131,072 next-label steps,1,024 optimizer calls,8 final episodes,
9,600 evaluation ticks,0 initial evaluations**. Service-label eligible counts are
27334/27953; next-mask counts65503/65503. With the retained cost law`2N+2E+H`, recorded
counts bound training native calls to372,718..1,478,458 for the pair, plus9,600 evaluation
steps. Exact H remains unmeasured; zero service does not reveal omitted consequence calls.

| Recorded machine-time quantity | Seconds | Boundary |
| --- | ---: | --- |
| REPLACE exclusive | 224.20338408101816 | complete arm, below900 |
| HALF_RETAIN exclusive | 226.97875767503865 | complete arm, below900 |
| Runner summary in-run | 454.032020866056 | measured before final serialization/process exit |
| External complete runner process | 454.50 | `/usr/bin/time`, centisecond reporting, exit0 |
| Prior shared charge | 215.0 | conservative enclosing charge; known prelaunch subtotal209.4782804 |
| Shared process work including final exit | 3.31785824394319 | external runner wall minus both exclusive arms |

The original summary's shared217.84987910999916 and pair669.032020866056 end before final
serialization/exit. External process timing adds0.467979133944s to shared, yielding
shared218.31785824394319 and pair669.50 **before** external observation/collection/intake/
closeout. The [accounting record](evidence/2026-09-10-b08-accounting.json) adds these later
measured commands, including failed analysis, preservation/removal and publication charges.
Do not add the containing SSH/pytest or experiment Duration455 again.

Monitor's [raw terminal receipt](evidence/b08_seed137_20260910/monitor_terminal.txt) reports
`local_observation_time=2026-09-10T21:26:14-07:00`, inconsistent with its contemporaneous
remote exit/dispatch chronology. Root reconciled this as a timestamp label issue; raw bytes
are preserved. It contains no observation-command duration. **Monitor command wall is
unmeasured**, not0 and not the experiment's455s. Root explicitly accepted this factual
limit. Therefore complete S≤300 / charged-arm≤1050 / pair≤2100 conformance cannot be
certified from available coverage; no measured breach is inferred. Measured exclusive
limits passed. Engineering source/test budgets were met with no unnamed§4 machinery.

Peak self RSS621,748,224 bytes and peak child RSS621,748,224 bytes are recorded separately,
not added. Exact aggregate CPU, H and scratch peak remain unmeasured;
`resources_unmeasured=true`. These limits do not damage the independently checked native
primary under evidence-spec§11.8.7. Administrative/provider latency is separate from
machine work, not an exemption for necessary computation.

## 5. Descriptive reduction, preservation and closeout

The unchanged raw [summary](evidence/b08_seed137_20260910/summary.json) preserves curves,
resets, all rows and native companions. [Analysis](evidence/b08_seed137_20260910/analysis.json)
independently reads recorded checkpoint tensors and reduces the four paired rows; it
creates no model, optimizer, native state, rollout or scientific exposure. The generic
scientific-tools `summarize_runs.py` reads the following two arm means with
`--paired --baseline REPLACE`. The derived CSV is kept in direction runtime storage; the
repository excludes CSV artifacts, so its complete input is preserved here:

```csv
task,seed,arm,score
DISH-B08-A03,137,REPLACE,441.0
DISH-B08-A03,137,HALF_RETAIN,434.5
```

Its [output](evidence/b08_seed137_20260910/run_summary.json) reports n=1 paired difference−6.5
and null sample SD. Four within-pair conditions are not four independent learners.

The full verified archive is preserved on primary control at
`C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/exp/b08_s137_a01522a6_collected/complete_evidence.tar.gz`.
The collection checkout also retains the archive and extracted records. Before removal,
all eight ignored remote evidence files matched the archive, no tracked/untracked changes
or live experiment PID remained, and the exact source was an ancestor of the pushed
direction branch. Scoped `git worktree remove` succeeded. The
[inventory](evidence/2026-09-10-b08-cleanup-inventory.json) and
[cleanup receipt](evidence/2026-09-10-b08-cleanup.json) verify the remote checkout's absence
on disk and from Git registration. The small supervisor receipt directory remains as a
terminal record. The shared authoring checkout remains the designated direction checkout;
Root owns integration and accepts retention/reclamation. Historical checkouts were untouched.
