# RCLE TBCFV A02 frozen score allocation — result intake

**Valid complete A/RECON.** All four logical configurations have very low sampled actor-score
contribution and pointer allocation in both frozen blocks. Both final snapshots have small mean
conditional probability change on the fixed-input library. The same-graph baseline change alters
direction as well as magnitude, while the low relative actor/pointer allocation persists. These
are measurements on seed 18's saved states, not an algorithm improvement or a unique explanation
of B02's flat service. This selected spend ends; no successor is selected or launched here.

Date: 2026-09-06 PDT. Object `RCLE-TBCFV-A02-FROZEN-SCORE-ALLOCATION`; outcome-informed A after
B02. Authority: complete post-B02 Innovator **PRO_FINAL**, immutable response commit `6c0d1ca55`,
[archive](pro_packets/20260906_post_b02_innovator/archive/RESPONSE.md) §§三–六; current owner resume
and [frozen card](RCLE_TBCFV_A02_FROZEN_SCORE_ALLOCATION_SCIENCE_CARD_20260906.md) §§1–7.
Source accepted from `24c2808fecad4a8fe053875628983e7067e2d060`, integrated by Root at `855963f8e`.
Exact integrated launch SHA: `abcc3766c2b2d9908c9391b0827d9f2a39f8d641`.
Pushed E0/primary-data/receipt archive commit: `2fba6345d8847a51015ce6ced3534efd7d902f4f`;
no source change followed the launch.

## 1. What was checked and the resulting evidence ceiling

DM inspected the actual [summary](a02_frozen_score_allocation_20260906/summary.json), calculated
the configuration/block comparisons over its recorded values, and checked the
[E0 evidence](RCLE_TBCFV_A02_RESULT_EVIDENCE_20260906.md),
[complete primary tables](a02_frozen_score_allocation_20260906/PRIMARY_TABLES.md),
[artifact readback](a02_frozen_score_allocation_20260906/artifact_readback.json), admission,
whole-process time and terminal log against card §§2–6. The earlier source acceptance checked
the actual joint/M/A loss path, shared encoders and event heads, fixed-input re-encoding, stopped
sampling/advantage, RNG specialization and partial-output accounting; it did not confer result
validity in advance. The [CM record](RCLE_TBCFV_A02_CM_RECORD_20260906.md) retains the focused
checks and independent review. Publication issues raised during review were repaired before
launch; no material finding remained. DM did not repeat the CM's execution or model readback.

| Binding quantity | Observed against the frozen allowance |
| --- | --- |
| Models and graphs | 4 single-constructed models; all 4 configurations × 2 blocks |
| Result interactions | 512 episodes, 32,768 environment ticks; exactly 8 episodes per cell/block/configuration |
| Derivatives | 32 attempted and 32 completed; no operation left in flight |
| Learning | 0 optimizer steps, 0 baseline updates, 0 new training instances |
| Fixed-input library | 256 unique points, 16 per cell/block; scenarios 0/1, ticks 0/24/28/60, first and last active member |
| Conditional probabilities | Three `[256,6]` FP64 arrays, 768 finite nonnegative vectors |
| Numerical identity | All 8 additivity checks passed; maximum residual `7.624346369010137e-17` |
| Projection coverage | All 30 named tensors / 5 disjoint groups; maximum squared-norm discrepancy `2.220446049250313e-16` |

The concrete probe identifiers in the summary match seed 18, labels 19001/19002 and purpose
`post-b02-frozen-probe`; arm names do not choose substreams. The two probe blocks are sampled
measurement units on the same training seed. Configurations, cells, episodes and tensors are not
independent training replicates. No training-seed uncertainty or significance claim is produced.
Technical fixtures remain separate: 16 non-card episodes and 17 derivative attempts / 16 completed,
including one deliberately interrupted synthetic call. Readback added zero forwards, derivatives
or episodes.

The C1P1 and FLEX final-state SHA256 values match card §2, respectively
`3c277fee5ec01adbdd259bc809126bd6eaaa85affbe7b716425d2da14895d13e` and
`66d23ae708edbf6ab02003400bdd961451b81dc6f68b6c0e55118b1478e490f0`.
Theta0 was reconstructed by the registered seed/initialization law, not loaded or retrained:
norm `21.205717682888878` versus recorded `21.205717682888885`.
Both final baselines were reconstructed from their own 200 ordered full-precision per-cell curve
rows. This implements the predeclared path, with the disclosed `math.fsum/len` versus original
FP64 `torch.mean` reduction-order limitation; it does not recover the missing buffer bits. No
zero-baseline fallback was needed and no substituted zero gradient is labelled original.

Raw library SHA256 `13e480994acc47e5183aa174a1a3ace81e166ae4e46a72a50a3227408864fb61`
matches the retained remote and local 586,817-byte file. Stored-vector readback gives maximum
simplex error `3.3306690738754696e-16` and maximum entropy/TV summary difference
`4.440892098500626e-16`. These are engineering/measurement checks, not evidence of mechanism value.
No required measurement is quarantined; optional resources are measured. Evidence spec
§§4, 5.1 and controlling 11.8–11.9 support the frozen A ceiling without imposing a training,
full-replay or exhaustive-causal requirement. B01/B02 retain their historical validity.

## 2. Frozen reading rule applied verbatim

From card §5:

> Define `r_A = norm(g_A)/(norm(g_M)+norm(g_A))` and `r_P = norm(pointer_projection(g))/norm(g)` under the original baseline. A snapshot is described as **very low sampled actor-score contribution and pointer allocation** only if **both blocks** simultaneously satisfy r_A<=0.01 and r_P<=0.01. This is not "actor has no effect".

> Report the weaker manager-dominant reading r_A<0.5 separately on every block; retain cancellation, shared encoder and head projections. Each block's mean TV<=0.01 permits **small average conditional probability change on this input library**, with all cells and maxima shown. Block/state conflicts remain heterogeneous; no convenient aggregate replaces them. Zero-baseline changes have no new success threshold.

| Observation | Reading and recommendation | Limit |
| --- | --- | --- |
| Low actor / low pointer allocation on both blocks and small TV | Raise joint gradient allocation or pointer conditional sensitivity as motivation for a next named change; lower a blind global step increase. | Not no gradient throughout training; not proof that reweighting improves U. |
| Original versus zero baseline changes direction, cancellation or actor projection, not only scale | The baseline's finite-sample role merits a separate test; retain a reason for a future explicit baseline B. | Frozen zero-baseline gradients are not zero-baseline training; no B is auto-executed. |
| Actor allocation is not low, or conditional probabilities clearly moved while service stays flat | Reject the simple claim-distribution-unresponsive explanation; retain credit assignment, noise and coordination learning. | No host unlearnability or unbounded search conclusion. |
| Blocks conflict or no strong reading emerges | Publish the unresolved result and end this A. | No extra samples until a convenient reading; unresolved does not forbid an ordinary B. |
| File identity, numerical graph or resource problems damage a measurement | Stop and label only the dependent measurement; retain independently trustworthy readings. | No retroactive B01/B02 quarantine without concrete dependency evidence; no automatic retry. |

> These are overlapping descriptive readings, not winner selection. **Every branch ends the A and returns the measurements for next-object selection.** No conditional successor is hidden in the card. A/B have no consumption state; ending this spend is its explicit budget boundary.

**Applied: rows 1 and 2.** Every configuration meets the strong allocation marker in both blocks;
all eight graphs also meet the weaker `r_A<0.5` description. The baseline direction effect supports
row 2 separately. The branch-3 forecast that actor allocation would be substantial is not supported;
the nonzero distribution and parameter movement below constrain any stronger "unresponsive" claim.
No extra blocks are bought and no row supplies a hidden learner successor.

## 3. Direct observations and bounded interpretation

### Actual loss-path allocation

| Configuration | Block | r_A original | r_P original | r_A<0.5 |
| --- | ---: | ---: | ---: | --- |
| C1P1-init | 19001 | 0.00934238849 | 0.00941476692 | yes |
| C1P1-init | 19002 | 0.00755212707 | 0.00756448282 | yes |
| FLEX-init | 19001 | 0.00934447557 | 0.00941476673 | yes |
| FLEX-init | 19002 | 0.00755675075 | 0.00756448255 | yes |
| C1P1-final | 19001 | 0.00758724535 | 0.00760733249 | yes |
| C1P1-final | 19002 | 0.00671868818 | 0.00673617113 | yes |
| FLEX-final | 19001 | 0.00760950255 | 0.00761280071 | yes |
| FLEX-final | 19002 | 0.00641083238 | 0.00641687601 | yes |

The manager/actor norm cosine is near zero (about −0.0094 to −0.0004), with cancellation ratio
about 0.9907–0.9936. Thus large cancellation **between these two aggregate loss terms** does not
explain the small joint norm in these samples. Internal sample cancellation, gradient noise,
inter-agent conflict and their historical training effects remain unmeasured. Both loss paths
reach shared encoders; the pointer receives the actor contribution. C1P1 event heads are absent
from the graph. FLEX's initially zero-valued final head layers receive nonzero actor gradients,
while connected hidden-head gradients can be numerically zero. Equal initial forward policies
therefore do not imply identical backward graphs or dead FLEX learning paths.

The observed `r_P` means a hypothetical full-vector normalized step of 0.02 would allocate less
than 0.0002 in pointer L2 displacement on these graphs. No such step was taken. This does not
measure allocation throughout B02, show that pointer parameters alone control service, or prove
that loss reweighting would provide a useful update direction.

### Same-graph baseline counterfactual

| Final state | Block | Original / zero joint norm | cos(original, zero) | r_A with zero baseline | r_P with zero baseline |
| --- | ---: | ---: | ---: | ---: | ---: |
| C1P1 | 19001 | 0.0988989568 | 0.811611093 | 0.00716168128 | 0.00719182815 |
| C1P1 | 19002 | 0.0453089754 | -0.189325433 | 0.00544843096 | 0.00544132722 |
| FLEX | 19001 | 0.0989116764 | 0.811568586 | 0.00729228793 | 0.00731180205 |
| FLEX | 19002 | 0.0463483646 | -0.244324980 | 0.00539244596 | 0.00537463535 |

Zero baselines enlarge the raw joint norm roughly 10–22 fold but do more than rescale it: the
original/zero directions have cosine about +0.812 on block 19001 and negative cosine on 19002.
That block difference is retained. Actor/pointer relative shares remain below 1% under zero
baseline, often smaller than under the original baseline. A baseline change is therefore a
candidate for a distinct finite-sample-direction question, not an observed repair of allocation.
All 64 original cell rows retain Y mean/SD and advantage mean/RMS/SD. Within each cell,
constant-baseline centering preserves the measured return SD; the result does not support
"baseline near the mean erased the return variation." Neither block estimates expected
gradient variance or the return of zero-baseline training. The reconstructed-buffer precision
qualification remains attached to every original-baseline comparison.

### Net parameter movement and conditional probability change

Direct tensor differences give `norm(C1P1-final − init)=0.472889394`,
`norm(FLEX-final − init)=0.472943899`, and
**`norm(FLEX-final − C1P1-final)=0.00234143919`**. The last value is measured from tensors,
not by subtracting the first two norms. Both final/init pointer differences are about 0.0157;
FLEX common/agent heads move by 0.000279551 / 0.000327731. The full disjoint-group and per-tensor
records are retained. Net displacement does not identify the sequence or utility of training
updates.

| Block | C1P1-final/init mean TV | Maximum | FLEX-final/init mean TV | Maximum | FLEX-final/C1P1-final mean TV | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 19001 | 0.00535123840 | 0.0103800609 | 0.00534134180 | 0.0103474469 | 0.0000172250 | 0.0000348292 |
| 19002 | 0.00544612839 | 0.0106404335 | 0.00543670243 | 0.0106135669 | 0.0000164805 | 0.0000363949 |

Each block's 128-point mean meets the registered small-change description. Some point maxima
exceed 0.01: the distributions are not unchanged. All eight cells in each block and snapshot
entropies remain in the complete tables; no favourable cell selection replaces them. Because
both raw external input and the C1P1-init latent z are fixed and each snapshot re-encodes them,
this identifies average conditional encoder/pointer change on that library. It excludes
manager/FLEX-head changes to the latent and final-policy visitation. It cannot establish full
policy insensitivity or a causal service effect.

**Strongest support:** both independently drawn probe blocks show the low allocation marker in
all four configurations, accompanied by small final/init mean TV. **Strongest contradiction to
an overbroad explanation:** pointer/encoder weights and probabilities moved, some point TVs
exceed 0.01, and FLEX head gradients are nonzero. Small relative allocation is a plausible reason
to change the next learner comparison; it is not a complete causal diagnosis. Native B02 service
remains the historical near-flat result; this A contributes no new native learning gain or loss.

### Literature grounding that changes this reading

The question-driven local-library retrieval was used to bound two interpretations, not to add
another launch condition. My-lib's tracked index had only the two synthetic fixture entries and
no local-page rows; these supplied no scientific coverage. The Inst-sci formal catalog had 190
rows and substantive verified coverage in `MARL-0622`, HyperMARL (NeurIPS 2025), with title identity
verified and retained PDF SHA256
`87578f637d6cffd315ef0870798624153dc4c49055a192fe3c8c8938a7e81ed6`.
Its source `C:/Projects/Inst-sci/papers/MyLib/json/MARL-0622.json`, pp. 4–7 (§§3.2, 4.3) and
Appendix F.2, treats inter-agent gradient factorization/conflict and measures gradient variance
alongside performance. That is a different decomposition from this manager/actor loss split.
It specifically restrains the claim here: these two blocks do not identify inter-agent conflict
or variance reduction, and no HyperMARL architecture or novelty claim is adopted.

For the remaining baseline question, primary
[Greensmith, Bartlett and Baxter (JMLR 2004)](https://jmlr.org/papers/v5/greensmith04a.html),
pp. 1472–1473 and §3.5, explains baselines as control variates and why an average-reward baseline
need not minimise variance. Its average-reward GPOMDP setting does not establish the expectation
of RCLE's normalized update `g/norm(g)`. This evidence changes the intake language: lower raw norm
is not loss of information, and a same-graph direction difference is not a beneficial training
effect. No additional retrieval report, implementation change or validation spend follows.

## 4. Predictions scored without changing their targets

| Prediction on record | Outcome |
| --- | --- |
| Pro: at least one final snapshot has r_A<0.5 in both blocks with small conditional pointer change | Supported; both finals meet both descriptions. The stronger 1% marker was observed but was not required by this forecast. |
| Retained DM: branch 3, r_A between 0.1 and 0.5, and fixed-input TV above 0.01 on at least one block | Refuted on both parts: every r_A is below 0.01 and both final/init block means are below 0.01. Point maxima above 0.01 do not rescue the block-mean forecast. |
| Owner | Not taken (unattended); no prediction reply exists at this intake boundary. |

## 5. Receipts, cost and conformance

The sole detached `agent-task` handle `rcle-a02-20260906` ran on configured `wsl_4070`,
CPU FP64 / one compute thread, cwd `/home/wu/hmasd-worktrees/rcle-a02-abcc376`.
It started `2026-09-07T03:41:36Z` and ended `03:41:43Z` (September 6 20:41:36–20:41:43 PDT),
exit 0 / `COMPLETE`. Result root is that cwd's
`temp/directions/roster_consistent_latent_exploration/exp/tbcfv_a02_20260906`.
The existing independent monitor received the accepted handle directly; Root forwarded the
adoption ACK and CM released routine polling, then completed terminal collection. There was no
second accepted handle, result retry, node switch or replacement block. Prior Git/partial-clone
fetch stalls were preparation transport facts, not scientific attempts or result polarity.

[Memory admission](a02_frozen_score_allocation_20260906/memory.json) at
`2026-09-07T03:41:36.420464Z` records physical/effective availability both
15,257,608,192 bytes (14.2097549438 GiB), exceeding the same-node 4 GiB floor. It immediately
preceded the runner through `&&`. [GNU time](a02_frozen_score_allocation_20260906/complete.time)
measures **7.02 s whole-process wall**, including startup/loading and final writes;
5.75 user + 0.28 system = **6.03 CPU-s** at its actual descendant accounting scope;
**602,980,352 bytes peak RSS**. The summary's 5.927895314 s excludes its final write and is
not substituted for whole-process wall. The accepted supporting-check debit 12.7002317 s gives
**19.7202317 s charged against 300 s**, with the result inside its reserved external 287 s /
internal 285 s bounds. Result critical path equals this sole process wall. Unisolated cold-build
cost is included if incurred, not separately estimated; Git/SSH preparation and artifact collection
are outside result-machine wall. Collection/readback generated no additional model exposure.

The CM returned 410 added / 1 deleted non-test source lines, a 64-line runner and 135 test lines;
no engineering-scope §4 machinery was added and no §5 line or wall budget was breached. Checks
and independent review support technical conformance; scientific acceptance follows the measured
card observables above. Headroom remains B02's reference U about 0.282 versus learned U about
0.707 on the active paths, gap about 0.425. It is not an upper-versus-tuned-baseline H_A1 record,
and no new baseline training was purchased. A has no algorithm-effect MEI; its 1%/0.01 scales
retain their descriptive meaning. No C object is consumed and A/B have no consumption state.

## 6. Decisions this intake produces

**Object tier — validity and bounded reading.** Options: (a) accept the complete A measurements
at the stated ceiling with the baseline precision qualification; (b) quarantine a dependent
measurement for a concrete defect; (c) treat the measurements as a causal training result.
Recommendation and selection: **(a)**. Counts, identities, graph/coverage checks and published
values support the declared measurement; no concrete defect supports (b), and (c) exceeds the card.
**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**

**Object tier — stop and return.** Options: (a) end the selected A spend, retain every block and
return the observations for next-object selection; (b) buy extra probe blocks; (c) launch an
unfrozen baseline/allocation learner now. Recommendation and selection: **(a)**, required by
card §5 and the Root assignment. **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
This is a clean execution boundary, not a direction-family closure, recast, park or Portfolio action.

Direction-local next-discriminator advice, **not a selected successor**: compare one explicitly
named score-allocation learner change with the unchanged same-information training law in a
bounded real B. Its next observation should be sampled native service return. A baseline-law B
remains a separate candidate because the finite-sample direction changes, but this A supplies no
evidence that removing the baseline repairs allocation or improves return. Choosing the exact
law, seed/exposure and comparator belongs to the next authorized decision/card. No second A,
complete diagnosis, global step increase, host qualification or capability prerequisite is
imposed before an ordinary B.

## 7. Owner surface and clean boundary

Primary-checkout `item.py reviews --json` returned `[]` at intake; relevant RCLE/Portfolio audit
owner columns were empty. No unapplied override or prediction reply required handling. Historical
18:11-stop text remains provenance; the current owner resume authorized this completed object.
Existing new-card item `20260906-rcle-003` is traced through `item.py` to this actual application;
its original `#L92` link belongs to the pre-integration freeze branch (`25d6aff6a`), while the
integrated freeze/source-acceptance rows at launch SHA are L94/L95. This intake branch appends
validity and stop decisions at audit L96/L97, with the current evidence links. No owner reply is fabricated and no new
approval is awaited. Result/decision item commands obey the current P3/P4 retirement behaviour;
the Chinese brief is retained at
`docs/research/portfolio/owner/briefs/roster_consistent_latent_exploration/2026-09-06_RCLE_TBCFV_A02.md`.

Owner flags: `none`. The failed DM prediction, single-seed ceiling, nonzero movement and baseline
reconstruction limit are prominent evidence, not hidden as a successful test result. No material
critic dissent was overruled, no close-call selection or new recast occurred, and no direction or
Portfolio disposition is enacted. Root owns integration and subsequent sequencing.

scope: none
