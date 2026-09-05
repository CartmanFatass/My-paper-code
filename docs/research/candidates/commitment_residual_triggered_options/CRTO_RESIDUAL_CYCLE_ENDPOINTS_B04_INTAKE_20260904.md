# CRTO residual complete-cycle endpoints B04 intake

Date2026-09-04; `CRTO-RESIDUAL-CYCLE-ENDPOINTS-B04`; **VALID B/EXPLORE**.
Frozen branch: **BR-D — NO_TRUE_GAIN**. Source
`c53f3bb19c91d01ef87cb2c4b9737811eb10d795`; CM E0/full result
`c56ae92b3944c670cccaab01969e35085d8c58ed`; card `53576cb1aa975dc5f4d5171431e13f54ce17e7cf`.

## What was checked

CM accepted the exact-source run and published
`CRTO_RESIDUAL_CYCLE_ENDPOINTS_B04_RESULT_EVIDENCE_20260904.md` and
`CRTO_RESIDUAL_CYCLE_ENDPOINTS_B04_RESULT_20260904.json`. DM checked them against the card,
not against the prediction. A separate standard-library calculation parsed all32 original
B01 pairs/64 members; checked48 canonical TRAIN addresses and their direct native advantages;
checked48/16 TRAIN/EVAL donor bijections with no fixed points; reconstructed every recipient
and donor's22/172 occurrences; and verified all six representation-labelled, finite positive
exposure lines and identical within-run initial scales.

DM recomputed all96 legal prediction maxima with printed-order ties, signed native labels,
oracle actions, regret, side counts, side means, competence, three pairwise contrasts and the
first-match branch. Native labels agree across all six readouts and the exact selected members.
Predictor/calibration population, nonzero learner counts, actual node/SHA/argv/thread/admission
and cost fields match. Calibration has64 tapes,16128 examples, episodes256..319 and pooledK4/K8,
with12160/3968 horizon4/8 examples and zero12/16. No confirmation namespace or old learner state
was read.

Independent calculation receipt:
`temp/directions/commitment_residual_triggered_options/exp/residual_cycle_endpoints_b04_20260904/dm_recompute.json`,
checked2026-09-05T01:40:13Z. A first DM read-script assembly accidentally omitted its row loop;
the resulting empty-key assertion was corrected and the complete calculation passed. This
changed no source, artifact or scientific output and was not a run instrumentation failure.

## Direct observation and rule applied verbatim

All cells contain8 KEEP and8 REPLAN EVAL rows. Positive d_RT favors TRUE.

| representation | update | KEEP exact | KEEP regret | REPLAN exact | REPLAN regret | equal-side R | competent |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| RAW | 33 | 1/8 | .013163761979059926 | 8/8 | 0 | .006581880989529963 | no |
| RAW | 258 | 6/8 | .003754710220270765 | 6/8 | .0038081499511370583 | .0037814300857039115 | yes |
| TRUE_RESIDUAL | 33 | 5/8 | .012175594008410113 | 3/8 | .024052430160218897 | .018114012084314506 | no |
| TRUE_RESIDUAL | 258 | 6/8 | .006773246198944587 | 5/8 | .015057821229055236 | .010915533713999911 | no |
| CALIBRATED_DERANGEMENT | 33 | 4/8 | .010769355639354404 | 6/8 | .008212780732112474 | .009491068185733439 | no |
| CALIBRATED_DERANGEMENT | 258 | 2/8 | .014621648680206439 | 6/8 | .004681041050934722 | .00965134486557058 | no |

| endpoint | d_RT | d_DT | d_RD |
| --- | ---: | ---: | ---: |
| SHORT33 | -.011532131094784542 | -.008622943898581066 | -.002909187196203476 |
| LONG258 | -.007134103628296 | -.0012641888484293314 | -.005869914779866668 |

The card's first-match rule:

1. **`BR-A — ALIGNED_SHORT_ONLY`**: RAW-LONG is competent; d_RT(SHORT)>delta and
   d_DT(SHORT)>delta; all three LONG pairwise absolute differences<=delta;
   R(RAW,SHORT)-R(RAW,LONG)>delta; R(TRUE,LONG)-R(TRUE,SHORT)<=delta.
2. **`BR-B — PERSISTENT_ALIGNED_SIGNAL`**: RAW-LONG is competent and d_RT and d_DT both
   exceed delta at SHORT and LONG.
3. **`BR-C — GENERIC_PREPROCESSING`**: RAW-LONG is competent; d_RT(SHORT)>delta,
   d_RD(SHORT)>delta and abs(d_DT(SHORT))<=delta.
4. **`BR-D — NO_TRUE_GAIN`**: RAW-LONG is competent and d_RT(SHORT)<=delta and
   d_RT(LONG)<=delta.
5. **`BR-E — COMPARATOR_WEAK`**: RAW-LONG fails either material-side competence condition.
6. **`BR-F — MIXED_OR_UNRESOLVED`**: every other technically complete combination.

Here delta=.0025. BranchesA/B/C are false because d_RT(SHORT) is negative; RAW-LONG
is competent and both d_RT values are below delta, soD is the first match. The observed
TRUE costs exceed MEI at both endpoints. TRUE also loses to DERANGED at SHORT by more
than MEI; its LONG gap to DERANGED is inside MEI. DERANGED itself does not improve RAW.
This supports neither an aligned nor a generic-preprocessing benefit in the tested object.

## Counts, receipts, resources and engineering boundary

Exactly one detached `crto_residual_b04_c53f3bb1_01` ran on wsl_4070 at
`/home/wu/hmasd-worktrees/crto-b04-c53f3bb1`. A fresh admission at
2026-09-05T01:34:05.531211Z measured12950413312 available physical/effective bytes, above4GiB,
and was joined directly by && to the exact runner. Supervisor start/end01:34:05/01:37:07Z:
**182 machine seconds**, exit0, no retry. Observer uptime277s is not experiment duration.

| quantity | value |
| --- | ---: |
| predictor tapes / materialized examples | 128 /32256 |
| predictor updates / processed examples | 100 /12800 |
| calibration tapes / examples | 64 /16128 |
| gate updates / processed examples | 774 /24768 |
| forward rows / scored decisions / unique EVAL rows | 96 /96 /16 |
| environment transitions / common-future branch steps | 54848 /3520 |
| preparation seconds | 120.60043037099967 |
| RAW / TRUE / DERANGED training seconds | 17.373102220000874 /16.70554584999627 /17.073687174000952 |
| runner wall before publication | 171.8017914000011 |
| peak RSS bytes | 1541214208 |

All measured arm and shared times are below1200/1500s. Resources are measured; no resource
claim is made. Initial L2/RMS/Linf are18.87916908516977/.10402732933491829/.28862619400024414.
LONG displacement L2/initial-L2 is RAW.1369227563959056, TRUE.08801190138964558,
DERANGED.13797244260322725; corresponding Linf ratios are.915735779252775,
.5338464052739748,.9070316204301058. All SHORT lines are also positive and finite.

Collected summary193466 bytes, SHA256
`1e5bd64d9f93ec75d5fe27921ac5c7877c4f027b5f01e239cf691c9e0ad4716a`, under
`C:/Projects/HMASD/temp/directions/commitment_residual_triggered_options/exp/residual_cycle_endpoints_b04_20260904/attempt01_artifacts/`
with admission, runner.sh, task.log, status, start_time, exit_code and pid. Full E0 records the argv.

The draft wrapper's32.7% orchestration overage was removed before source acceptance and launch;
final250 research lines,36 runner lines,72 orchestration lines=28.8%, scope section4:none.
No accepted result-bearing implementation exceeded the engineering budget. Independent review
had no material finding. Local10 checks passed in6.13s and exact remote10 in3.30s, including
one smoke per environment and actual-sized three-representation publication with synthetic
scores labelled. The only runtime warning was the existing non-writable NumPy/PyTorch warning;
there was no exception or missing learner measurement. The real publication path completed.

## Prediction, bounded interpretation, support and contradiction

DM's BR-D/competent-RAW-LONG prediction is supported. Owner: `not taken (unattended)`;
CM and integrated owner review queries returned[] at this clean boundary.

Strongest support is the competent RAW-LONG comparator, material adverse TRUE differences at
both fixed endpoints and no alignment-control advantage. Strongest counterpoint to any broad
residual-impossibility reading is that TRUE itself improves from SHORT to LONG by.007198478370314595;
its longer-budget KEEP exact count reaches6/8, but regret still fails. Its geometry can learn,
without meeting this comparison. Only one coupled seed and a deliberately exposed selected
panel/adaptive endpoint choice are measured. No stable performance, information/function-class
value, asymptotic failure, headroom, policy/MARL, prevalence or transfer claim follows.

B01's32/256 comparator-weak result, B02/B03's separate negatives and A01's unexplained native
crash remain unchanged. B has no consumption state. This negative closes only the tested
seed0/33-and258 representation intervention, not the balanced family or direction.

## Decisions this intake produces

1. **Accept BR-D (object tier, technical).** Options(a) accept the complete independently
   recomputed negative; (b) defer this result's reading until more seeds. Recommend/select(a):
   additional seeds change scope, not this completed object's validity.
   **Owner-delegated decision (unattended,2026-09-03 instruction):(a)**.
2. **End this unchanged intervention (object tier, selection).** Options(a) retain RAW and
   drop this exact seed0 residual intervention; (b) repeat this unchanged comparison.
   Recommend/select(a): exact repetitions do not address the remaining seed-law uncertainty.
   **Owner-delegated decision (unattended,2026-09-03 instruction):(a)**. Reversible, no close
   call, no family closure/recast/C promotion/lifecycle/priority/Portfolio action.

## Next discriminator

A prospectively fixed additional-seed B comparison at the same33/258 endpoints can address
the surviving coupled-seed explanation before another budget/model change. The source map
shows that seed changes predictor initialization/permutation, common gate initialization and
TRAIN/EVAL derangement; tapes, selected rows/order and native labels stay fixed. Calibration
forecasts/packets can change with the predictor. This must be called joint learner/predictor/
derangement seed sensitivity, not isolated gate-initialization replication.

A new card must identify the seeds, legacy runner-ID provenance versus its own scientific
identity, per-invocation admission/cost/exposure and branch aggregation. Current CLI permits
onlyseed0; existing function accepts other seeds, or the CLI can be changed transparently.
The planning initial scales are seed0 history, not new-seed measurements. No successor is
frozen or launched by this intake and no Pro decision is claimed.

**OWNER_DIRECT execution boundary,2026-09-04:** Root relayed the owner's instruction,
"这轮完毕后暂停即可", after the valid-result intake was committed. B04 is complete and
CRTO stops at this clean boundary with zero live runs. The next-seed question stays pending;
no additional card, launch, retry or Pro round is authorized by the earlier continuation.
CM received the same stop instruction. This is scheduling state, not a scientific family
closure, direction lifecycle or priority change.

## Append-ready audit rows for Root

| time | direction | tier | kind | options | chosen option | reversible | provenance | evidence | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-04T18:47:09-07:00 | commitment_residual_triggered_options | object | technical | (a) accept complete BR-D; (b) wait for more seeds to read this result | (a) accept valid NO_TRUE_GAIN | yes | OWNER_DELEGATED | docs/research/portfolio/owner/inbox/2026-09-04/20260904-crto-032.json | none | |
| 2026-09-04T18:47:10-07:00 | commitment_residual_triggered_options | object | selection | (a) retain RAW, end exact seed0 residual intervention; (b) repeat unchanged | (a) drop only this unchanged intervention | yes | OWNER_DELEGATED | docs/research/portfolio/owner/inbox/2026-09-04/20260904-crto-033.json | none | |
| 2026-09-04T18:47:10-07:00 | commitment_residual_triggered_options | object | technical | Publish valid-result brief | Publish B04 Chinese brief and prediction score | yes | DM_INTAKE | docs/research/portfolio/owner/inbox/2026-09-04/20260904-crto-034.json | none | |
