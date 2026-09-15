**End the present fixed1e-4/512 exposure exploration, retain the optional COND implementation and its evidence, and select no immediate numerical extension.** The completed longer-training comparison did not produce a useful realized relative advantage at its prescribed final endpoint, and the within-path observation did not reveal growth in COND's advantage that would strengthen the particular late-exposure opportunity. Read alongside the preserved favorable and adverse history, this gives further unchanged512 sampling a weaker current development case than reversible non-extension. This is a marginal-value decision under uncertainty, not a finding that another pair is information-free or that COND cannot work. [Current intake, accepted result and decisions][S1]; [result, endpoint table][S2]; [card, question and decision value][S9].

**The final512 result remains a valid INSIDE_MEI B/EXPLORE observation: COND−DENSE = −0.005375013231600323 J. I found no material source-and-record defect requiring reclassification, recomputation or another experiment to preserve it.** It is not equivalence, an adverse card outcome, or stable DENSE superiority. The strongest alternative is one fresh matched pair at the same fixed rate and512 training endpoint, preferably with final512-only evaluation when recurrence of that endpoint is the question. That is a credible, bounded research option; it loses here on judged incremental development value, not on admissibility, a seed quota or a requirement for a favorable pilot. [S2, card rule][S2]; [analysis, primary and checks][S4]; [TASK, requested alternatives][TASK].

This decision is final only for the bound exposure-family question. It does not PARK or CLOSE MGTAP, change its scientific CONTINUE, priority or occupied slot, promote COND over the generic DENSE default, grant resources, or initiate another consultation. The explicit owner resume is recognized; the historical operational pause is not a stopping reason. Whole-direction maintenance, investment or lifecycle remains a separate Portfolio question. [DIRECTION, current result and historical-pause sections][S8]; [AGENTS, §§2–4 and §5 autonomy][S18].

## 1. What this completed object measured

For training endpoint h in {256,512}, the evaluated quantity is the original native reward:

\[
J_{a,h,e}=\frac{1}{256}\sum_{t=0}^{255}\sum_{i=1}^{5}r_{a,h,e,i,t},\qquad
\Delta_h=\frac{1}{32}\sum_{e=0}^{31}\left(J_{\mathrm{COND},h,e}-J_{\mathrm{DENSE},h,e}\right).
\]

The episode horizon stays H256;512 is the number of training episodes, not a longer evaluation horizon or a changed reward denominator. The card selected final512 before the run. The intermediate256 observation and its derived change cannot replace that primary. [Card, question and protected path][S9]; [protocol.py, constants and `primary`][S11].

| Training endpoint and role | COND mean J | DENSE mean J | Ordered COND−DENSE | Conditional paired-world SE | Positive / negative worlds |
| --- | ---: | ---: | ---: | ---: | ---: |
| 256, descriptive | 0.09595785820780596 | 0.08758757884879717 | +0.008370279359008794 | 0.0014115631565087363 | 26 / 6 |
| 512, sole primary | 0.1277920207332075 | 0.1331670339648078 | −0.005375013231600323 | 0.004649366246290445 | 15 / 17 |

These are supplied observations from the complete native summary, result and analysis, not numerical reductions executed by this review. Both endpoint estimates lie inside the declared inclusive [−0.01,+0.01] band. Only a final contrast strictly above +0.01 or below −0.01 receives the corresponding above-MEI or adverse branch. A negative point inside the band remains negative and inside; it is neither a treatment failure classification nor evidence that the two procedures are equivalent. [S2, rule and table][S2]; [RUN_SUMMARY, `primary`][S3]; [ANALYSIS, `panel_summary`][S4].

I read all64 endpoint/world rows in PAIRED_SCORES.csv. Final512 includes both substantial favorable and adverse values, for example +0.02795315808174384 at zero-based episode19 and −0.0682568281201714 at episode25. They remain in the same complete primary. The15 favorable worlds cannot be promoted into15 successful training instances or a discovered target subgroup; the17 unfavorable worlds cannot be counted as17 failed fits. Nor does a small mean imply small differences in every world. [PAIRED_SCORES.csv, both complete panels][S5].

The within-path arm-mean increases are +0.03183416252540154 J for COND and +0.045579455116010636 J for DENSE. The reported gap change is −0.013745292590609116 J. Thus COND did not lose absolute mean return between these checkpoints; DENSE's mean improved more on this realized comparison. These are mean changes, not improvement in every individual world. The fact that the gap change is numerically more negative than −0.01 does not make the object COND_ADVERSE: that threshold was assigned to final512, not to this secondary quantity. [Result, within-path changes][S2]; [protocol.py, secondary fields][S11].

## 2. The executed learning and measurement dependencies

### The changed endpoint is implemented without restarting learning

At actual launch source90f835e10357fbbf465cc5d500a93f1e2d4ab226, the159-line new runner constructs one matched pair at master8254 and trains COND then DENSE. Within each `native_fit`, it constructs the actor/critic's optimizer once and creates one advancing training-velocity generator before the rollout loop. It performs256 two-episode rollouts, with the inherited recurrent update after each rollout. At completed training episodes256 and512 it evaluates and saves a checkpoint; it does not recreate the optimizer or restart the training generator at256. No old checkpoint is loaded and no selector is invoked. [study.py, `native_fit` and `run_study`][S10].

The new source uses two distinct environment objects per arm, one for training and one for evaluation. Evaluation constructs private generators at its specified addresses instead of drawing from `train_velocity`; the update call is outside the evaluation loop and consumes the training episodes. The intermediate scores are emitted to records, not fed into a rate choice, an early-stop condition or the learner's update. These producer/consumer facts support the intended uninterrupted learning comparison more directly than a COMPLETE label. [study.py, environment construction, `episode` and rollout loop][S10].

The checkpoint audit reports active Adam step values512 at the256 checkpoint and1024 at512 for each arm. Total displacement from the initial parameters progresses from2.986039161682129 to4.302816867828369 for COND and from3.2927403450012207 to3.9585959911346436 for DENSE. Together with the source's optimizer lifetime, recorded updates and the independent changed-path review, these facts support real continued learning. A step counter alone would not prove optimizer-state continuity, and displacement neither proves convergence nor identifies which component caused the return. [ANALYSIS, `checkpoint_facts`][S4]; [RUN_SUMMARY, fit endpoint exposure][S3]; [ENGINEERING, checks and technical acceptance][S7].

### Native meaning and information fairness remain bounded

The protected task is five UAVs, fifty uniform users, free-space/no shadowing and H256, with the original sum-five-reward/256 J. Both actors receive legal raw108 local information and retain private GRU64 histories; privileged critic information remains training-only. The primitive action is sampled velocity. COND retains mean visible-partner conditioning and masked-partner context; DENSE retains intact raw/nonlinear processing. Recurrent PPO uses agent-compound ratios, chunk32, two episodes per rollout, four epochs, entropy0.01 and joint actor/critic clipping0.5. Adam is fixed at1e-4 for both, with its other stated settings unchanged; execution is CPU FP32/thread1. [Card, protected path][S9]; [RUN_SUMMARY, configuration][S3]; [new runner, inherited call sites][S10].

The visible factory creates separate actors from the new seed's templates and deep-copies the common critic for each arm. The new fit creates its own optimizer, environments and generators. The source and engineering record support the intended ownership; I did not reopen the unlisted inner actor/template or shared environment/learner implementations. The independent engineering account reports inspecting actual forward behavior and state/RNG handling. This is a scoped source-and-record judgment, not a new certification of every imported function. [conditional_pooling.py, `build_cond_pair`][S13]; [reused helper imports and `_optimizer`][S12]; [ENGINEERING, independent review coverage][S7].

The relevant mechanism trace is unchanged: evolving user/UAV state supplies each UAV's legal visible-entity information; COND or DENSE processing and private recurrence shape primitive velocity actions; those joint actions affect native team reward and recurrent PPO learning. Equal legal information does not imply that the two finite learners reach equal performance. Conversely, an RNN, team reward and nonzero parameter movement do not prove sufficient state, partner-intention identification or individual causal credit. These distinctions limit attribution without invalidating the measured whole-procedure contrast. [Card, trace][S9]; [FOUNDATIONS, §§2–4 and6][S16].

### Pairing and complete-panel publication are coherent

Master8254 was selected prospectively as the next unscreened integer. With b=100000×8254, training uses reset b+1000+e, persistent velocity b+21 and duration b+4000+e. Evaluation uses reset b+2000+e and fresh private velocity/duration generators at b+3000+e and b+5000+e. The two endpoints deliberately reuse those evaluation address labels. Reusing numeric addresses is common-input pairing, not shared mutable RNG state or identical endogenous trajectories. It also does not supply two independent evaluation panels across checkpoints. [Card, randomization][S9]; [protocol.py, `randomization`][S11].

The protocol checks evaluation object, master, LR, endpoint and randomization bindings, then separately passes each endpoint's rows to the accepted reducer. That reducer rejects unknown arms, duplicate/invalid episode indices, nonfinite scores and incomplete H256 observations, and requires all32 episodes per arm. It constructs ordered differences and their mean. The new runner checks completed counts and both endpoint records, retains fit limits, and reports partial failures separately. The actual summary has two complete fits, all four complete endpoint panels, empty partial_fits/limits and no current failure. [protocol.py, `primary`][S11]; [conditional_pooling.py, `primary`][S13]; [study.py, completion/publication][S10]; [RUN_SUMMARY, final fields][S3].

Actual totals are1152 episode rows,512 rollout rows,1024 training episodes,128 evaluation episodes,294912 team ticks and2048 Adam calls. They match the supplied completed-record analysis, not only an embedded planning block. The engineering account reports12 DM synthetic checks and an independent synthetic counterexample, with no material finding; these checks support wiring, not independent native efficacy. [Result, execution and technical evidence][S2]; [ANALYSIS, counts and checks][S4]; [ENGINEERING, acceptance][S7].

No primary-changing dependency gap is apparent in this chain. The DM's data-only intake did inspect four retained checkpoint payloads to check metadata and Adam state, as well as raw rows; this was not new fitting or policy evaluation. I read its findings, the full readable score table and the listed source, but did not deserialize those checkpoints or independently repeat the raw audit. The distinction matters: repeated reduction or checkpoint inspection is not another empirical replication. [S1, what was checked][S1]; [S4, checkpoint facts and check scope][S4].

## 3. What the evidence changes—and does not identify

The new512 comparison is a different exposure condition, not a retry of8253 or a third independent final256 result. The previous review's preference against immediate unchanged256 sampling did not prohibit a specifically justified new B. The card gave a concrete reason to examine512: the rate had been selected at256, and its later behavior was unobserved. The owner resume permits treating that new question on its merits rather than importing the historical pause or stopping preference as an answer. [Card, selection rationale][S9]; [prior review, §4][S14]; [DIRECTION, current result][S8].

The strongest local update is that **extending this newly fitted path to512 improved both arm means but did not expose a useful relative COND advantage**. The relative point moved from small-positive to small-negative, both inside the local scale. That weakens the immediate case for developing this late recipe on the strength of the observed path; it does not demonstrate that longer training usually favors DENSE, that1e-4 was wrongly selected, or that COND lacks useful outcomes. The DM's final-inside prediction and its expectation of no useful growth in the relative advantage were met here, but no calibrated probability or forecast accuracy is estimated. [S1, scientific-reading application and prediction][S1]; [S2, endpoint results][S2].

There is one training pair. The two checkpoints are dependent states of that pair, and the32 evaluation addresses are reused across endpoints. At either endpoint, sample-SD of paired-world differences divided by sqrt(32) reports conditional evaluation uncertainty for those fitted policies. It omits variation from fresh fitting and from the earlier configuration-selection process. The analysis correctly leaves training-run SD null; that is unestimated uncertainty, not zero variance. [Reducer, conditional_se][S13]; [ANALYSIS, training_run_sd][S4]; [04_EMPIRICAL, randomness hierarchy][S17].

The same-address design makes the within-path changes interpretable as matched descriptive observations, but does not isolate a causal dose mechanism. It also means that the two endpoint SEs must not be combined as though the endpoint estimates were independent. Their covariance is relevant to uncertainty in the change, and no change-SE or across-training dose inference is supplied here. No new calculation is needed for the declared descriptive report. Neither two points nor comparison with historical256 runs establishes a general learning curve or sample-efficiency advantage. [Card, limits][S9]; [protocol.py, secondary changes][S11]; [FOUNDATIONS, §6][S16].

The retained signed history constrains interpretation without creating a pooled test:

| Evidence role | Retained meaning |
| --- | --- |
| Selection8251 | Both arms selected1e-4 by their own validation return; slow validation favored DENSE. This is selection-used evidence, not an independent favorable recurrence. |
| Selected-programme holdout8252,1e-4/256 | +0.023704897713093642 J, a valid useful local positive. |
| Fixed recurrence8253,1e-4/256 | −0.025924927546066238 J, a valid adverse local realization; it did not reproduce8252's favorable sign. |
| New late-exposure8254,1e-4/512 | −0.005375013231600323 J, inside MEI; its own256 checkpoint is descriptive and dependent. |
| Earlier3e-4 early256 | 8241 +0.015128847632690413 and8242 −0.05684388886006531 J remain separate. |
| Earlier equal512 mean-COND | 8212 +0.005761321371348559,8213 −0.02246957345594415 and8214 +0.02447811898058116 J retain their own readings. |
| Other procedures | TOP8221 −0.0684509798102144 and unequal COND512/DENSE7688231 −0.02933437223896382 J concern different comparisons; REL and old C/coordinate-family conclusions remain unchanged. |

The older exact values are read through the listed complete prior review, not through a new retrieval or reanalysis of their original arrays. They are not additional fixed1e-4/512 training replicates. The new near-zero point cannot be called recovery from8253 by added training:8253 and8254 have different fitted policies and final worlds. Conversely,8253 cannot stand in for a second512 failure. The earlier positive8252 and8214 remain genuine contrary evidence to broad failure. [Prior review, §§1 and3][S14]; [DIRECTION, current and immediately preceding sections][S8]; [current intake, retained history][S1].

The whole series is adaptive: earlier results informed selection, recurrence and the later exposure question, while8254's own master/endpoints were fixed before output. This supports a local exploratory interpretation, not retrospective confirmation of a fixed multi-seed design. Native setting sensitivity observed under8251 is not a causal explanation of old losses, and these later fits add no untuned same-holdout comparator or upper reference. Lower-grid-edge selection, tuned headroom and mechanism attribution remain unresolved; their absence is not a B admission condition. [S14, scientific update and selection limits][S14]; [S9, inference boundary][S9]; [empirical specification, §§11.7–11.10][S15].

## 4. Why end this exposure family rather than buy one more pair?

### The strongest continuation case is real

The best numerical alternative is a genuinely fresh matched COND/DENSE pair fixed at1e-4, each trained through512 and assessed on its sole32 final worlds, retaining every sign. It would ask whether another learning realization changes how much active development the512 optional recipe merits. It would not need to establish stable ordering, find the optimal rate, explain a mechanism or begin from a positive512 pilot. Only one final512 training pair has been observed, so the new observation would add information that the256 checkpoint and old256 pairs cannot provide. [Current intake, decisions and final paragraph][S1]; [specification, §§11.8.2–11.8.3][S15].

The favorable8252 result and earlier native positives make useful COND outcomes plausible. The current final512 point is inside the chosen scale with nonzero conditional uncertainty, not an exclusion of benefit. The implementation is exercised, and the complete two-endpoint run actually cost360.00s native wall. Thus an honest bounded repeat has a concrete feasibility basis. It must not be dismissed as intrinsically chasing a sign merely because it follows an inconclusive point. [S1, strongest support and alternative][S1]; [S2, actual wall][S2].

A useful positive second512 observation could reasonably strengthen a bounded commitment to that recipe; an adverse observation could weaken it; an inside-scale result could leave the present low-priority development judgment intact. Those are meaningful differences in information, even though no single outcome would settle population performance. The existing maintenance choice is real: no outside customer or entirely new mechanism is needed to make it a scientific question.

### The narrower reason that alternative loses now

I nevertheless choose non-extension. The marginal allocation being judged is another recipe-development experiment, not preservation of the optional implementation. Preservation and the DENSE default are already compatible with stopping numerical work on this family. We therefore need not purchase another draw simply to avoid discarding the idea or its favorable evidence.

The particular new reason for testing512 was that later learning might make the fixed low-rate recipe worth developing beyond what the mixed256 record supported. Its completed path now supplies both the late endpoint and the local early-to-late comparison. Neither adds a useful relative improvement, while generic DENSE also learns and improves. This does not refute a population late-benefit hypothesis; it reduces the immediate empirical support for committing further work to this specific exposure recipe. The strongest known positive remains a differently commissioned256 realization, not a demonstrated late-exposure opportunity. [Card, decision value][S9]; [result, arm and relative changes][S2].

Another endpoint-only pair would refine that uncertainty and could change the decision. I judge the incremental developmental payoff insufficient at this boundary, rather than treating all possible information as something that must be collected. A favorable new point would deserve consideration on its magnitude and context, not an automatic continuation; an unfavorable point would likewise not make the family universally false. The present choice accepts the possibility of missing a useful future realization in exchange for not extending a weakly supported recipe exploration by default. This is a reversible practical judgment, not a computed negative value of information or a significance rule.

That reasoning must not be shortened to “the primary was small, so stop.” The current result alone does not impose stopping, and mixed history alone does not make replication useless. The decision rests on this particular late-exposure motivation, the completed relative and absolute observations, the preserved contrary history, and the option to retain the code without further immediate experimentation. Unknown support totals qualify the cost picture but are not the decisive reason; neither the lifted owner pause nor completed cleanup enters the scientific rationale. [S1, development options][S1]; [specification, §§11.8–11.9][S15].

The DM is therefore right to distinguish further identical draws from a justified next question, but its inability to identify a specific implementation change is not itself a reason to deny a performance repeat. Nor is a new targeted-use advantage or measured structural defect required. The strongest repeat already is a legitimate question about the512 recipe. My disagreement with that option is its present marginal priority, not a judgment that it fails a scientific qualification test. This preserves the substantive qualification in the previous complete review rather than turning its stopping preference into a permanent prohibition. [Current intake, decision2][S1]; [prior review, §4][S14].

### Why the other alternatives are not substitutes

A fixed256 pair is cheaper but answers a different endpoint. More evaluation of8254's existing512 checkpoint would refine conditional policy performance, not add a learning realization. Repeating an eight-fit selector asks about selecting configurations again; the original selector chose on256, so silently treating it as a512 repeat would also change the protocol. A lower-rate grid or architecture change could be worthwhile for a separately reasoned question, but neither follows automatically from this point or the old grid boundary. Choosing favorable worlds after seeing their signs would not establish a targeted-use advantage. [TASK, alternatives and counts][TASK]; [S9, selection history and limits][S9]; [S14, alternative comparisons][S14].

No numerical alternative is selected. This closes the current exposure exploration without declaring it impossible or permanently barring the same design. A materially different valuation of the existing recipe-maintenance choice, relevant new evidence, or a concrete development consequence of another signed endpoint could justify revisiting it. Revisit need not await positive data, a new architecture or full diagnosis; it does need an actual reason to change this allocation judgment rather than an automatic search for a favorable majority. No new approval form, seed quota or compulsory consultation is created.

## 5. Compare the strongest alternative using its smallest sufficient work

The decision above considers a final512-only fresh pair, not an inflated repeat that makes the intermediate checkpoint mandatory. The completed object needed both observations for its selected within-path question. A new endpoint-recurrence question need not buy that secondary information again. Omitting it would relinquish the new path's256-to512 description, not its final512 comparison, provided evaluation remains nonintrusive as in the accepted design. This would be a prospectively defined new object, not alteration of8254's completed contract. [Card, exposure and protected path][S9]; [TASK, final-only alternative][TASK].

| Work | Completed8254 / hypothetical same two-endpoint repeat | Hypothetical fresh final512-only pair | Earlier fixed256 reference |
| --- | ---: | ---: | ---: |
| Fits | 2 | 2 | 2 |
| Total training episodes | 1,024 | 1,024 | 512 |
| Total evaluation episodes | 128 | 64 | 64 |
| Team ticks | 294,912 | 278,528 | 147,456 |
| Adam calls | 2,048 | 2,048 | 1,024 |
| Actor collection/evaluation/replay row uses | 6,717,440 | 6,635,520 | 3,358,720 |

Completed counts are source-reported actual execution facts; the alternatives are supplied prospective arithmetic, not new work or a promised runtime. The extra256 observation costs16,384 team ticks across both arms. Per arm, the endpoint-only work is initialization,131,072 training ticks,1,024 recurrent PPO/Adam calls,8,192 final ticks and the necessary final checkpoint/publication work. Five agent histories and four replay epochs are intrinsic learning work; there is no candidate, joint-action, trajectory, controller or solver search. Proportionate changed-path verification is separate support work, not another required empirical panel. [RUN_SUMMARY, fits/counts][S3]; [protocol.py, `planned_exposure`][S11]; [TASK, alternative counts][TASK].

The original eight-fit programme is not simply “four times this512 study.” It has four times as many fits as a two-fit pair, but its per-fit exposure and selection purpose differ. Counts must follow the actual selected protocol; there is no reason to substitute it for the endpoint question here. [Prior review, §§4–5][S14]; [current card, alternatives][S9].

The actual8254 full-command measurement is360.00s wall,561,596KiB peak RSS (548.43359375MiB), exit0. COND189.38205022900365s and DENSE168.54817102500238s are fit-body measurements; the357.95038999198005s pre-summary study body is another nested scope. None is added on top of the whole command or substituted for it. The earlier fixed256 command's178.86s is a measured alternative-endpoint reference, not an equal-budget comparison or part of8254's own bill. [Result, execution][S2]; [RUN_SUMMARY, body and timing_scope][S3]; [prior review, §5][S14].

The roughly6–10-minute future wall estimate remains UNMEASURED. The endpoint-only pair has fewer evaluation ticks, but there is no measured whole-command timing for that new variant and no warranted speedup factor. Git/staging, source/check/review, observation recovery, collection/audit/intake/archive, maintenance and provider work lie outside the native timer; full support/lifetime/provider and aggregate CPU totals remain UNKNOWN. Native affordability is evidence in favor of the alternative, not a guarantee that complete future work is cheap, and unknown totals are not a budget-breach or stopping finding. No cost pilot or lifetime census is needed for this choice. [S1, cost limits][S1]; [specification, §§11.8.1 and11.9][S15].

Actual admission passed the physical/effective4GiB requirement with15,587,618,816 available bytes. The cgroup fields were unavailable rather than measured zeros. Any later invocation would require fresh actual-node admission and existing resource authority; inherited watchdogs remain ordinary operational plans, not new grants or time-based scientific endpoints. This decision allocates zero new fits, ticks or Adam calls. [ENGINEERING, actual launch][S7]; [card, resource boundary][S9].

## 6. Material reporting limits and the smallest corrections

No correction to the original primary, card branch or completed-exposure record is required by the listed evidence. The minimal reporting qualifications concern interpretation, not additional experiments:

| Source and affected claim | Smallest adequate interpretation |
| --- | --- |
| Card “Question, decision value and limits”; intake “Decisions this intake produces” | “No useful late advantage was observed on8254” does not mean that inside-MEI prohibits another B. Non-extension is the present development-value choice, not a small-primary veto. |
| Result endpoint table; protocol secondary changes | Both arm means improved on one continuing path; the relative change is descriptive. Do not apply the final-MEI rule to that change, combine endpoint SEs as independent, or claim a causal dose effect or general sample efficiency. |
| RUN_SUMMARY/ANALYSIS independent-unit fields | One training pair remains one pair. The64 endpoint/world rows reuse32 address labels and dependent checkpoints; null training SD is unestimated, not zero. |
| COLLECTION/ENGINEERING Monitor account | Native finish is23:30:56Z; exact terminal-observation UTC is unknown. Preserve the overwritten-adoption/reused-finish-time defect without using it as evidence against the native primary. |
| Current DIRECTION and AGENTS boundaries | Ending this exposure family does not restore the lifted operational pause or apply whole-direction PARK/CLOSE, priority or slot changes. |

These distinctions are largely already explicit; they identify what must survive the final intake rather than alleging that the DM made every overclaim listed. The one substantive decision correction is that a review request is no longer the next answer to the same unresolved family question: this complete response chooses non-extension. It does not require another round merely to ratify that choice. [S1–S2][S1]; [S6–S7][S6]; [AGENTS, §§2–4][S18].

The collection reports all14 remote originals, including four checkpoints, plus the local Monitor in a15-member archive. Its3,334,990-byte identity and SHA256 a4aa0713a72396e12c593ae92996850d7e4bcda5a600f2ab9c611bc48f33e935, remote/local matches and archive/Git-blob readbacks are source-reported preservation facts, not independent causal proof. The same records report successful removal of the exact completed remote checkout, with disk and registration absent, while supervisor/local originals and shared authoring remain. The older E0's pending-cleanup sentence describes its creation boundary; the collection and engineering completion entries supply the later cleanup fact. [COLLECTION][S6]; [ENGINEERING, preservation and cleanup][S7]; [result, deviations][S2].

The rejected combined local check/deletion command and retained test scratch are preserved without a workaround. Monitor initially returned nonterminal facts prematurely, and its final metadata overwrote the original adoption and reused program-finish time. The native records, checkpoints and complete-command timer are separately reported intact. These operational limitations constrain their own claims; neither successful publication nor a flawed monitor timestamp changes the algorithm's signed result. [S2, preservation and deviations][S2]; [S6, monitor_limit][S6]; [S7, checks and transfer][S7].

## 7. Actual source access and decision boundary

All18 manifest paths were accessed through the connected GitHub connector at their declared full revisions, with the current fixed TASK read separately. No listed decision-critical textual or explanatory source remained inaccessible. The following table identifies complete-file reads or the relevant section ranges actually used; the reference definitions give exact repository paths and commits.

| Reference | Actual access |
| --- | --- |
| [S1 — late-exposure intake][S1] | Complete at d0affb5f9bd8c4dbdef2290bed3db22a2456d0ed. |
| [S2 — late-exposure result][S2] | Complete E0, endpoint table, rule, work and deviation account at that evidence revision. |
| [S3 — RUN_SUMMARY.json][S3] | Complete two-fit/endpoints/counts/movement, both panels, all ordered differences, status and timing at that revision. |
| [S4 — ANALYSIS.json][S4] | Complete panels, sign summaries, checkpoint Adam facts, counts and check scope at that revision. |
| [S5 — PAIRED_SCORES.csv][S5] | Entire64 endpoint/world rows at that revision. |
| [S6 — COLLECTION.json][S6] | Complete14-original inventory, archive/readback, terminal, cleanup and Monitor-limit account at that revision. |
| [S7 — ENGINEERING.md][S7] | Complete implementation/independent-review/acceptance, source/admission/launch, preservation and limitation record at that revision. |
| [S8 — DIRECTION.md][S8] | Lines1–160 at that revision, especially current8254 result and immediately preceding8253/CONTINUE/history boundaries; no recursive linked-source loading. |
| [S9 — late-exposure card][S9] | Complete prospective card at actual launch source90f835e10357fbbf465cc5d500a93f1e2d4ab226. |
| [S10 — late-exposure study.py][S10] | Complete159-line runner at that launch source; inspected, not executed. |
| [S11 — late-exposure protocol.py][S11] | Complete address, counts, panel binding and primary/secondary code at that source; not executed. |
| [S12 — reused selection-study helpers][S12] | Lines1–181 at that source: imports, optimizer/deadline/publication, existing fit/state/failure/count helpers; old selector not run. |
| [S13 — conditional_pooling.py][S13] | Complete factory, ordered-world reducer and publication helper at that source; not executed. |
| [S14 — preceding8253 review][S14] | Complete181-line response at494dbefe004bfa4b52017dc2ba903f4eff30204c, including its genuine fresh-pair alternative, stopping qualifications and access limits. |
| [S15 — empirical specification][S15] | Common integrity§4 and applicable§§11.4,11.7–11.10 at90f835e10357fbbf465cc5d500a93f1e2d4ab226; no other-object exception applied. |
| [S16 — FOUNDATIONS.md][S16] | §§2–4 and6 at that source, applied to legal histories, joint learning, finite optimization and uncertainty. |
| [S17 — 04_EMPIRICAL.md][S17] | Complete short note at that source, applied to comparison objects, randomization hierarchy and attribution. |
| [S18 — AGENTS.md][S18] | §§2–4 and the2026-09-13 autonomy passage in§5 at that source, read with the TASK's explicit later owner resume. |

I did not fetch the binary archive, raw episode/rollout JSONL, checkpoint payloads, the unlisted analysis script, independent-review transcript, standalone final-run descriptive file, deeper shared actor/environment/learner code or external papers. The DM's full raw/checkpoint checks and the independent engineer's broader inspection remain attributed reports. No numerical reanalysis, source/test execution, checkpoint loading, model/RNG/environment construction, fitting, evaluation or profiling was performed here. This is an inspection limit, not a failed binary retrieval or an assertion that retained bytes are absent. The unrelated older attached allocation-toy task does not govern this review.

Branch HEAD/ancestry/target and issue18 reads serve publication reconciliation only, not moving scientific evidence. The issue's historical post8231 body does not replace this fixed task. The result supports its one-path B ceiling; the final decision ends the particular fixed1e-4/512 exposure exploration with no immediate numerical extension and preserves optional assets and every signed observation. Any later whole-direction maintenance, investment, priority or PARK question is distinct and belongs to Portfolio; none is initiated or answered by this delivery. [Current TASK][TASK]; [AGENTS, §§2–4 and autonomy][S18].

[S1]: https://github.com/CartmanFatass/My-paper-code/blob/d0affb5f9bd8c4dbdef2290bed3db22a2456d0ed/docs/research/candidates/metric_ground_transport_allocation/MGTAP_LATE_EXPOSURE_B01_INTAKE_20260914.md
[S2]: https://github.com/CartmanFatass/My-paper-code/blob/d0affb5f9bd8c4dbdef2290bed3db22a2456d0ed/docs/research/candidates/metric_ground_transport_allocation/MGTAP_LATE_EXPOSURE_B01_RESULT_20260914.md
[S3]: https://github.com/CartmanFatass/My-paper-code/blob/d0affb5f9bd8c4dbdef2290bed3db22a2456d0ed/docs/research/candidates/metric_ground_transport_allocation/late_exposure_b01_8254/RUN_SUMMARY.json
[S4]: https://github.com/CartmanFatass/My-paper-code/blob/d0affb5f9bd8c4dbdef2290bed3db22a2456d0ed/docs/research/candidates/metric_ground_transport_allocation/late_exposure_b01_8254/ANALYSIS.json
[S5]: https://github.com/CartmanFatass/My-paper-code/blob/d0affb5f9bd8c4dbdef2290bed3db22a2456d0ed/docs/research/candidates/metric_ground_transport_allocation/late_exposure_b01_8254/PAIRED_SCORES.csv
[S6]: https://github.com/CartmanFatass/My-paper-code/blob/d0affb5f9bd8c4dbdef2290bed3db22a2456d0ed/docs/research/candidates/metric_ground_transport_allocation/late_exposure_b01_8254/COLLECTION.json
[S7]: https://github.com/CartmanFatass/My-paper-code/blob/d0affb5f9bd8c4dbdef2290bed3db22a2456d0ed/docs/research/candidates/metric_ground_transport_allocation/late_exposure_b01_8254/ENGINEERING.md
[S8]: https://github.com/CartmanFatass/My-paper-code/blob/d0affb5f9bd8c4dbdef2290bed3db22a2456d0ed/docs/research/candidates/metric_ground_transport_allocation/DIRECTION.md
[S9]: https://github.com/CartmanFatass/My-paper-code/blob/90f835e10357fbbf465cc5d500a93f1e2d4ab226/docs/research/candidates/metric_ground_transport_allocation/MGTAP_LATE_EXPOSURE_B01_SCIENCE_CARD_20260914.md
[S10]: https://github.com/CartmanFatass/My-paper-code/blob/90f835e10357fbbf465cc5d500a93f1e2d4ab226/experiments/candidates/metric_ground_transport_allocation/mgtap_late_exposure_b01/study.py
[S11]: https://github.com/CartmanFatass/My-paper-code/blob/90f835e10357fbbf465cc5d500a93f1e2d4ab226/experiments/candidates/metric_ground_transport_allocation/mgtap_late_exposure_b01/protocol.py
[S12]: https://github.com/CartmanFatass/My-paper-code/blob/90f835e10357fbbf465cc5d500a93f1e2d4ab226/experiments/candidates/metric_ground_transport_allocation/mgtap_lr_selection_b01/study.py
[S13]: https://github.com/CartmanFatass/My-paper-code/blob/90f835e10357fbbf465cc5d500a93f1e2d4ab226/experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/conditional_pooling.py
[S14]: https://github.com/CartmanFatass/My-paper-code/blob/494dbefe004bfa4b52017dc2ba903f4eff30204c/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260914_fixed_lr_results_review/archive/RESPONSE.md
[S15]: https://github.com/CartmanFatass/My-paper-code/blob/90f835e10357fbbf465cc5d500a93f1e2d4ab226/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[S16]: https://github.com/CartmanFatass/My-paper-code/blob/90f835e10357fbbf465cc5d500a93f1e2d4ab226/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[S17]: https://github.com/CartmanFatass/My-paper-code/blob/90f835e10357fbbf465cc5d500a93f1e2d4ab226/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
[S18]: https://github.com/CartmanFatass/My-paper-code/blob/90f835e10357fbbf465cc5d500a93f1e2d4ab226/AGENTS.md
[TASK]: https://github.com/CartmanFatass/My-paper-code/blob/36eec84748c1eea656d31de009d626899be62e46/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260914_late512_results_review/TASK.md
