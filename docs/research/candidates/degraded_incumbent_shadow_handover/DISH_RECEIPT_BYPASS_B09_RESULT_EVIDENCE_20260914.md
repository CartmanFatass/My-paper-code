# DISH B09 result evidence — 2026-09-14

**Complete one-pair B/EXPLORE result: BYPASS−REPLACE = −35.25 service ticks.**
Raw [summary](evidence/b09_seed149_20260914/RAW_SUMMARY.json), independent arithmetic/
checkpoint [readback](evidence/b09_seed149_20260914/CHECKED_RESULT.json), full native
[comparison](evidence/b09_seed149_20260914/COMPARISON.json) and
[artifact hashes](evidence/b09_seed149_20260914/ARTIFACT_HASHES.json) retain the evidence.
No scientific rerun or additional evaluation was used for this intake.

## 1. Identity and completeness

Frozen [B09 card](DISH_RECEIPT_BYPASS_B09_SCIENCE_CARD_20260914.md) selected one fresh
seed149 REPLACE/BYPASS pair. Scientific source `3a749256d2aaf16345308827518283c8d2b91ad7`,
corrected command binding `2d8badfe6c77bdd35304b62f9c0b84c7b0d931cb`, accepted handle
`dish-b09-s149-3a749256-20260914-submit02`, remote exact-SHA worktree
`/home/wu/hmasd-worktrees/dish-b09-3a749256` on configured hmasd-wsl-node.
The supervisor ended exit0 at2026-09-14T10:21:10+08:00 and runner status COMPLETE.
Actual admission passed at15,634,288,640 available bytes against4GiB floor; the recorded
single-shell wrapper performs admission immediately before the runner with `&&`.

Both complete learners have16 updates,65,536 ordinary transitions and512 optimizer calls;
total131,072 transitions and1,024 calls. All32 update receipts report finite loss/gradient
and both AdamW rates3e-5. CPU policy float32/native float64 and one-thread source/command
configuration are retained. No initial-policy evaluation; each arm has exactly four final
update16 modal rows. All eight reach1200 ticks, with zero unstepped remainder. Coordinate
sets/reset rows match the recorded fresh-master design; no result/condition filtering.

The master `83dc510a3929ffcfa51aa1d67ba82619c4b7eeeeba03a4e37472eb09ccd68abc`
equals SHA256 of ASCII `DISH-RECEIPT-BYPASS-B09/seed/149`. Shared initializer has zero
actor/snapshot/critic Welford counts and no optimizer states. The common initial model norm
is38.21434617906663. Final checkpoints preserve their respective modes and both3e-5 rates.
Every model tensor is finite float32, with204,211 stored parameters per arm. Relative L2
movement is4.568700696% REPLACE and4.753711969% BYPASS. REPLACE's four snapshot-encoder/
bridge tensors move; BYPASS's four remain byte-value equal to the initializer, as intended.
REPLACE optimizer state has36 parameter counters at512 and four at365; BYPASS has36 at512.
Unused weights are not required to receive512 AdamW updates. Source tests separately
establish live/replay/reset/promotion behavior; state evolution alone is not learning.

Final Welford actor/snapshot/critic counts are262144/5757/65536 for REPLACE and
262144/6615/65536 for BYPASS. Snapshot counts are masked normalization samples, not
independent messages or training replications. They corroborate ordinary receipt exposure;
BYPASS still receives native packets while omitting their arrival-state preparation.

## 2. All final native rows

| Condition | REPLACE service | BYPASS service | Difference | REPLACE energy | BYPASS energy | Invalid commits R/B |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TARGET_VISUAL_MASK/K8 | 428 | 434 | +6 | 280213.161662 | 283072.975607 | 105/110 |
| TARGET_VISUAL_MASK/K4_TO_K12 | 478 | 448 | -30 | 295428.128724 | 295987.629659 | 25/22 |
| TERRAIN_RELAY_MASK/K8 | 269 | 223 | -46 | 277237.732479 | 282510.501552 | 103/104 |
| TERRAIN_RELAY_MASK/K4_TO_K12 | 471 | 400 | -71 | 287714.548886 | 292452.838297 | 34/13 |

Mean service411.5 versus376.25; difference−35.25 =−2.9375% of1200 ticks and−8.566221%
relative to this REPLACE mean. The four differences are+6,−30,−46,−71. Their equal mean
crosses−24; the positive exception is preserved. Mean energy rises3357.593341 units, and
energy rises in every condition. Final invalid commits total267/249 (REPLACE/BYPASS).
The other six hard-event categories—buffer_clear, command_slew_breach, dual_owner,
dual_payload, separation_breach, token_gap—are zero in all eight rows.

Every final row has zero legal CAS and null first-transfer tick. All service is recorded
before any legal transfer. These are1200-tick ordinary EVAL denominators per row,4800 per
arm, not post-CAS samples or causal source attribution. Native terminal cause is fixed
horizon in all rows; the raw rows retain batteries, separation and reset parameters.

## 3. TRAIN companions and actual work

TRAIN service is30024/30032, energy15147447.306544468/15242462.324348306 and invalid
commits2111/2408 (REPLACE/BYPASS), each over65,536 ordinary transitions. Other six hard
events and legal CAS are zero for both. Training terminals are32 each. TRAIN is neither
the selected final primary nor pooled with EVAL or historical objects.

Next-label native steps65536 per arm, next-mask count65504. Service-label eligibility
E=12641/13501; delay calls25282/27002. Under actual2N+2E+H accounting, H remains unmeasured,
with bounds0..252820/270020. Ordinary/label/delay/consequence native TRAIN call bounds are
156354..409174 REPLACE and158074..428094 BYPASS, pair314428..837268. EVAL contributes
9600 actual native ticks across both arms. Shared initializer calls1; initial evaluation0.
These are the runner's distinct work factors, not independent observations.

## 4. Cost, repairs and technical acceptance

[Full cost limits](evidence/b09_seed149_20260914/COST.json): exclusive arms
193.615983943/190.897073988s; each meets its900s planning allowance. External runner wall
395.21s includes publication/interpreter exit; raw summary stops at387.294012008s, so
7.915987992s is added at the outer boundary rather than dropping it. The180s conservative
prior support allocation is an estimate, not a measured total. Accounted pair charge
through the named intake components is587.402524700s plus unresolved components; this
is not a total measured-cost or complete2700s-conformance certificate.

The original monitor receipt's243.6s total is inconsistent with its rows and conflates
waits with command timing. Preserve it and its [reconciliation](evidence/b09_seed149_20260914/monitor_submit02_reconciliation.json).
Only1.9s is retained as directly reported SSH timing; remaining combined-call SSH portions
and reliable read/delivery timestamps are unknown. Do not charge sleeps or supervisor
uptime as extra experiment work. Terminal state is independently corroborated by the full
supervisor files and outer timing. Exact H, aggregate CPU, peak scratch and full support/
provider/agent USD cost are unknown. Separate self/reaped-child peak RSS maxima are
625,741,824 bytes each; they are not additive simultaneous peaks. Resource gaps do not
invalidate this independently checked service result or establish a measured budget breach.

Submit01 failed before admission/training due to supervisor command serialization; its
failed wrapper/log and stray0.03s preflight timer are archived. Output absence and `&&`
prove that no scientific runner executed. The accepted/reviewed correction changed only
serialization and handle, preserving source/seed/exposure/accounting. No scientific retry.
The local checkpoint reader initially lacked repository PYTHONPATH; its5.4187014s failed
import is retained. Setting the required import path allowed the same read-only reduction
to pass in2.3712077s. No evidence was rewritten or scientific execution repeated.

DM accepts the source's independent high-risk review and10 focused synthetic cases,
actual complete primary and checkpoint readback. No remaining integrity finding depends
on more testing. [CHECK_RECORDED.py](evidence/b09_seed149_20260914/CHECK_RECORDED.py)
retains the intake calculation; its scratch copy is removed after evidence retention.

## 5. Preservation and remaining producer

Complete archive4,298,237 bytes, SHA256
`f6f2392d09e9048228e2e406dd81f5cf590cb6ba9342a1f3c9aea548c0dd9ac1`, contains all scientific
outputs, both supervisor histories, actual admission/timing and the failed stray receipt.
[Collection receipt](evidence/b09_seed149_20260914/collection.json) verifies identical
archives in both designated-direction and main evidence roots:
`temp/directions/degraded_incumbent_shadow_handover/exp/b09_s149_3a749256_collected/complete_evidence.tar.gz`.
Final REPLACE checkpoint SHA256 `f6550a810d934b670870c8752e1993ea23792ff1f422a2e0335b139deddef4dc`;
BYPASS `5abf845d782a9e97611d2b6197dd181c5e9aeb182740d5526c5d15c6e8253a43`.

Monitor active set is empty. DM owns bounded post-result scientific review, its response,
remote checkout cleanup and final lifecycle handoff; no next experiment is selected.


### Completed remote closeout

At2026-09-14T02:38:44.871228Z the terminal exact-SHA execution checkout was removed.
[Inspection](evidence/b09_seed149_20260914/REMOTE_CLEANUP_INSPECTION.json) found clean
tracked source, no ordinary untracked files and only the eight scientific/receipt files
plus the archive itself as ignored content. Every data file matched its archive member,
and both local archives were rehashed before removal. Both exact supervisor handles were
terminal with no tmux session. [Cleanup receipt](evidence/b09_seed149_20260914/REMOTE_CLEANUP.json)
confirms absence on disk and in Git worktree registration. The failed home receipt was
also byte-verified against the archive and removed. Historical supervisor directories
remain, with immutable copies already archived. No other worktree or evidence root was
removed; source3a749256 remains published and both checkpoint archives remain accessible.
Inspection0.9788666s and cleanup0.8117919s are added once to known support; overall cost
coverage remains incomplete. The direction authoring checkout still owns live Pro review
and DM acceptance; its eventual reclamation is Clerk-owned.
