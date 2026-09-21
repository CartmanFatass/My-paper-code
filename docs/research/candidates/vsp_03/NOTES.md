# VSP-03 research notebook

## 2026-09-21 — independent DM adoption and opportunity-rule comparison

Owner explicitly reopened this direction with B and C and authorized research execution.
This task is the direct DM for `vsp_03`, not a Root or a child DM. Native task
`01a0c347-9e60-77f1-b503-46ed4f80b314`, host `local`, authoring checkout
`/home/fires/.codex/worktrees/e481/hmasd-wsl`, branch `codex/vsp03-opportunity-rule`.
No inherited live experiment or uncertain send was assigned. No App message, reporting
loop or acknowledgement to another task is authorized. The owner-selected shared
activation is being published separately; until native canonical registration is present,
this task continues reading, design and implementation but launches no result-bearing run.

Adopted the current constitution, the direction-manager developer-instructions body,
`hmasd-scientific-tools` and `hmasd-research-engineering`. Actual session settings are
the runtime's settings. Fits record cost, with no allowance or old running window.
Historical records retain their original meaning and are not rewritten.

### Evidence adopted and present judgment

Read the complete Portfolio Pro Answer and Decision at
[`b6093d211fa33a81d05d490ffa5bc920f43605eb`](https://github.com/CartmanFatass/My-paper-code/blob/b6093d211fa33a81d05d490ffa5bc920f43605eb/docs/research/RESEARCH.md#portfolio-review-2026-09-21-closed-direction-research-value),
the direction record at `e130c1cdabae114ab98948f28f437167847e9a9e`, the B06/B07
result evidence and the actual B02/B06 source. B06 final-512 G−R0 is
`.02599609375 / .0145068359375 / .0096875` (mean `.016730143229166668`);
B07 final is `.0115673828125` with 128→512 `−.0016064453125`. The positive
endpoint observations survive. Stable strong superiority, monotonic training improvement,
UAV benefit and a special decentralized-MARL mechanism are not established. The old
initialization and shorter-training adverse evidence remains contrary evidence.

Reuse the complete Pro advice for this decision: fixed 512-update ordinary G versus a
competent transparent opportunity rule O, retaining R0/R; evaluate complete team J and
cost components; accept a useful ordinary rule as an answer. This advice covers the
question, comparator and development comparison, but not a future confirmation plan.
The owner's simultaneous activation supersedes the review's old pending-selection prose.

Verified interface: two public targets, 40 transitions, alternating two-tick clocks through
t32, each target's clock every four ticks. SUBMIT is legal even when not ready and commits
eight ticks whether successful or not. Success requires presence after all eight service
transitions. Native per-job units are `200*success −10*attempt −waiting_ticks`, team
J is their sum /400. Fourteen actor features contain current time, own and partner
presence/age/armed/expired/ready, partner pending, clock parity and next partner clock.
No future random tape is a policy input. The armed/expired/ready latches affect R0/R,
not the physical service success law. A t26 submission removes the partner's t28 and
t32 opportunities. Blocking is an observed scheduling event, not by itself a causal error.

Working hypothesis: much of G's gain over readiness can be represented by a finite-horizon
public opportunity calculation. Own survival and waiting trade against the value of the
partner's delayed or removed next/last opportunity. Strongest simpler explanation is a
good single-job timing rule without a material shared-slot correction. The discriminating
comparison therefore includes a same-model single-job diagnostic. A reduction in last-clock
blocking without J improvement does not count as a successful mechanism explanation.

### L0 — fitted public opportunity rule and B08 runner (before code)

Deliverable: one new disposable `experiments/candidates/vsp_03/opportunity_b08/`
module, `scripts/run_vsp03_opportunity_b08.py`, and mirrored focused tests. Preserve all
historical code, especially B02 rollout and B06's G model/objective/Adam/512 updates.
No FSD, B or C code/notebook/run edits. DM owns this notebook and the runner; an optional
Implementer may own only the new opportunity model/planner and its tests. An independent
Reviewer checks scientific semantics, observation rights, numerical recursion and admission
before launch. No helper launches experiments or edits this notebook.

Planned O: fit an explicit two-parameter age-dependent transition family from the **same
eligible 14-feature observations produced by G's training**, grouped by episode and mapped
back to physical target identity. Presence departure hazard `1/(age+c)` and absent return
probability `p` are estimated, not read from environment constants; declare the age-Markov,
independent-target family as O's structural modeling assumption. Consecutive observations
separated by delta ticks contribute their multi-step endpoint likelihood; no latent
intermediate transition, future draw, evaluation observation or service outcome is supplied
to this fit. G and O have the same raw observation/reward access; the algorithms consume
that data differently. This is not an equal-compute comparison or a claim that model
structure is free. O's fitting/planning work and structural assumption are reported.

O solves the finite-horizon WAIT/SUBMIT recursion for full remaining team units under that
fitted model. At a free eligible clock, WAIT moves two ticks if both jobs are pending;
SUBMIT costs 10, earns 200 times eight-step survival, and blocks the partner until its
clock t+10 (if any), regardless of success. One-pending-job WAIT advances four ticks.
All intervening pending-job waiting and horizon non-submission costs are included.
Readiness is not an action mask. `O_self` uses the same fitted survival/model but chooses
from the single-job recursion, ignoring partner opportunity loss; it is an attribution
diagnostic, not a competent primary baseline. `O_known` uses the actual transition
parameters solely as an explicitly extra-model-knowledge diagnostic, never the primary.

Checks: literal service-survival cases; independent recursion on late-horizon cases,
including failed submission occupancy and final clocks; observation-to-identity mapping;
no future/evaluation leakage; native units and per-job components; unchanged G update
exposure; fail-closed admission and SHA identity; runner output/count/readback coverage.
Synthetic test fixtures do not provide scientific scores or tune the study.

Initial cost design (not yet a launch declaration): three fresh independent blocks,
G 512 updates ×128 complete episodes per block; three G fits and three fitted-law O fits.
R0/R/O_self/O_known require no optimizer training. No hyperparameter or checkpoint search.
Fix actual seeds, evaluation panels, likelihood optimizer and exact work counts after the
implementation is reviewable, before any result. Development interpretation only; a later
confirmation would need its own claim note, fresh seeds and Pro criticism of the actual plan.
First concrete next step: implement the model likelihood and two-job recursion while the
DM builds the admitted runner around the unchanged G learner and reads shared registration.

### Independent scientific criticism and DM response (before outcomes)

Internal ResearchCritic `comparison_critic` returned material dissent on attribution, not on
the comparison or the endpoint likelihood. I accept it. B07's positive G−R0 accompanies
identical final-clock blocking `.0185546875`, more attempts `.12890625/team`, more failed
attempts `.1123046875/team`, and less waiting `2.595703125 ticks`; B06 block10801 also
improves while last-clock blocking increases. These published component facts keep own
deadline/readiness relaxation as a strong alternative to partner protection.

Clarification to the initial L0: `O_self` is **coupled versus isolated-job planning**, not
an intervention that deletes only partner utility. Its WAIT assumes the next own clock
in four ticks remains free; joint planning includes the possibility that the partner
submits two ticks later and delays one's own opportunity. O−O_self therefore measures
the value of including reciprocal scheduling interaction within this model, not a pure
partner-loss mediator and not an explanation of G's learned representation.

Add a pre-result intermediate prediction without extra rollouts: in every paired O/O_self
evaluation world, record the first action disagreement while histories and public inputs
are still identical; retain time, both target states and both possible disagreement
directions. Predict activation only while both jobs are pending, with positive complete-world
O−O_self as the native counterpart. Zero activation or activation without J gain weakens
the usefulness of coupling here. A strong O_self with little O increment is a useful simple
own-timing answer. No post-treatment selection of saved opportunities; retain all worlds.

The critic found no inherent adaptive-sampling defect: the next eligible observation time
is determined by the preceding observed state/action and slot schedule, not future target
draws. Each add_batch handles its own episode IDs (which restart at zero); absent-at-submit
success is explicitly `p*(c−1)/(c+6)` because the first service transition can be a return.
O's known model family remains a declared structural resource, not equal computation or
a model-free comparison. This internal critique supplements the reused Pro advice.

### B08 prospective declaration — fixed before the first result

Shared registration is now published at `main@d07c96f049282c3b2a7114268e7fd112a8b82f9b`;
the live canonical checkout agrees that vsp_03 is exploring and its lead is
`Codex DM (independent session)`. Its actual task, checkout and branch match this task.
The author branch merged that publication without editing other directions. This removes
the initial control dependency; execution still uses fresh native admission.

This is one development batch, **not confirmation**. Three new independent paired blocks
are seeds **21801, 21802, 21803**. Per block: one ordinary G fit at exactly 512 updates,
128 complete H40 episodes/update, unchanged B06 architecture, FP32 actor/critic, Adam
lr .001/betas(.9,.999)/eps1e-8, one backward/update, inherited entropy law. No restart,
early stopping, checkpoint selection or historical fit replay. G uses the same train100
world and action-address laws at fresh seeds. One O model fit then uses every consecutive
eligible public observation endpoint from that G fit, pooling the two identical target
laws after restoring identity; no extra environment collection. The declared MLE starts
at c6/p.4, L-BFGS-B bounds c[1.01,30], p[.01,.99], maxiter200, ftol1e-12, gtol1e-7.
The fixed age-Markov family is a stated structural resource. No candidate-family or
hyperparameter selection. Nonconvergence is a technical failure, not an O score.

**Six planned fits**: three G training attempts and three O transition-model fits.
The O_self rule reuses its block's fit. O_known uses true c4/p.5 and has zero new fits,
explicitly with additional model knowledge; it is not the primary comparator. R0/R also
have zero fits. On each block's fresh split200 4,096 paired complete worlds, evaluate
seven fixed panels: G greedy, G stochastic (secondary mode), O, R0, R, O_self and O_known.
No parameter updates from evaluation. All final panels share exogenous worlds and phase;
no old evaluation seed or score selected the new blocks. Three blocks, not episodes or
seven panels, are the independent inference units.

Work: **196,608 unique training episodes /7,864,320 team ticks**, **86,016 evaluation
episodes /3,440,640 team ticks**, total **282,624 episodes /11,304,960 team ticks /
22,609,920 target transitions**. G performs 1,536 Adam/backward calls. O likelihood
iterations/function calls, eligible rows, planner time and total actual wall are measured
separately. Reusing G observations is not additional native collection. Each planner solves
17 two-job 42×42 state tables and 17 single-job 42-state tables; fitted and known models
are both costed, with no rollout search. There are no development selection fits hidden
outside these six. Code checks used deterministic synthetic cases and mocked orchestration.

Primary contrast is fixed-final **G−O** in complete team J. Also retain O−R0, G−R0,
G−R, O−O_self, O_known−O and stochastic−greedy G, absolute J, successes, attempts,
failed attempts, non-submissions, waiting, expiry-at-own-clock events, and next/final-clock
blocking. First O/O_self divergences and both directions are reported without filtering
worlds. Conditional episode uncertainty remains separate from across-block variation.
Report all three block contrasts, their mean/SD and a descriptive t95 interval with df2;
normal independent block contrasts are an assumption, and n3 limits precision.

Interpretation: O absorbing the observed G−R0 gain favors the transparent rule; it does
not identify what G learned. Positive O−O_self with activation supports coupled planning
in this host; weak coupling with a strong O_self supports simpler own timing. Positive
G−O would motivate a specific residual analysis, not moving to update128 or adding seeds.
Mixed/small effects remain uncertain. The old .02 J scale is context, not a post-hoc gate
or equivalence region. No same-batch expansion after scores. A further question needs a
new prospective rationale; confirmation needs a fresh claim and Pro pass.

Node: configured `local_linux`, scientific Python, CPU one thread (also BLAS/OpenMP1),
one detached process with sequential blocks. No universal fit-rate or wall promise;
historical nine-second G alone excludes new collection/fitting/planning/publication costs.
Native admission will verify actual memory, published SHA, current lead/pause and duplicate
identity. Source SHA and operation manifest will be linked after exact-input publication.
All failed or incomplete outputs remain. The scientific endpoint has no wall-time stop.

Prelaunch engineering acceptance: Implementer returned only the assigned model/planner
and tests; DM read and accepted them. Independent `b08_reviewer` found no material executable
defect after tracing physical service, t+10 continuation, likelihood, identities, learner,
panels, publication and admission. Its one metadata wording correction for O_self was
applied. DM focused suite: 14 passed in 1.26 s; independent suite: 14 passed in 1.42 s.
These are synthetic correctness/orchestration checks, not fresh scientific scores or
an empirical 512-update identity replay. No result was read before this declaration.

### B08 complete read — transparent coupled scheduling retains more team value

The single accepted operation at source `4fb5a62363f863811d453facf8a14b21df2eff09`
finished exit0. Recoverable native identity, exact command, cwd, preflight and process exit:
[`launch-manifest.json`](../../../../runs/vsp_03/opportunity_b08_21801_21803/launch-manifest.json).
Full [summary](../../../../runs/vsp_03/opportunity_b08_21801_21803/summary.json), block curves,
G512 weights, fitted endpoint counts, planner tables, per-world/per-job results, decisions,
exogenous tapes and first disagreements are retained under that run root. No retries or
same-batch extension. Native work exactly matches the declaration: six completed fits,
282,624 complete episodes, 11,304,960 team ticks, 22,609,920 target transitions, 1,536
G optimizer calls, 1,178,356 gradient rows and 650,527 evaluation decision rows. Each G
actor moved (L2 displacement 5.42 or more on the first block; full per-block values saved).
Training mean J rises from about .268–.271 in updates1–32 to .364–.370 in updates481–512.
These curves describe training, without checkpoint selection or a monotonicity claim.

| Contrast, fixed final512 | 21801 | 21802 | 21803 | Mean |
| --- | ---: | ---: | ---: | ---: |
| G−O (primary) | -.023081055 | -.022924805 | -.020360107 | -.022121989 |
| O−R0 | +.035040283 | +.034486084 | +.031058350 | +.033528239 |
| G−R0 | +.011959229 | +.011561279 | +.010698242 | +.011406250 |
| G−R | +.011120605 | +.011693115 | +.010699463 | +.011171061 |
| O−O_self | +.020233154 | +.018049316 | +.008978271 | +.015753581 |
| O_known−O | -.000651855 | 0 | 0 | -.000217285 |
| G stochastic−greedy | -.001739502 | +.000192871 | -.002719727 | -.001422119 |

The descriptive n3 t95 interval for O−G is `[.018326642,.025917336]`; for O−O_self it
is `[.000927441,.030579721]`. These are development readings with three independent
training/data blocks, not confirmation, equivalence or a universal rank. Fitted (c,p) are
`(4.001403,.497072) / (3.987742,.501447) / (4.011515,.498266)`. All MLEs converged in
8–9 iterations (33–45 function evaluations), without using evaluation rows. O_known has
extra true-law knowledge; its finite-panel non-positive difference is not evidence that
the fitted model beats the known-law expected optimum. Known-law initial expected J is
.3863777695; the three observed known-law means .39704/.39421/.39436 lie 1.40–1.92
conditional world SE above it, which is preserved rather than substituted for expectation.

**Native tradeoffs and the failed strong intermediate prediction.** O−G increases successful
jobs by `.0724284/team`, attempts by `.0488281`, waiting by `5.1486003 ticks`, and
expiry-at-clock events by `.4608561`; failed attempts decrease `.0236003` on average
(the third block increases). Final-clock blocking goes from G's
`.0185547/.0107422/.0212402` to zero under O. Thus the initial idea of less missed
opportunity **without greater waiting/expiry cost** fails; full J nevertheless increases
because the task trades these components. Versus R0, O also has more failed attempts
(`+.0724284/team`) and waiting (`+3.9243164`), offset by more success (`+.0950521`).
No proxy improvement is substituted for team utility.

O−O_self has `.0113932` more success, `.0713704` more attempts, `.0599772` more failed
attempts, `4.7364909` fewer waiting ticks and `.3070475` fewer expiry events per team.
O_self leaves `.0778809/.0683594/.0678711` jobs unsubmitted, exactly its last-clock
blocking rate; O submits both jobs in every observed world and has no last-clock blocking.
The native gain is not a claim that all cost components improve.

First O/O_self action disagreements occur in **1893/1872/1848 of4096 worlds**, all at
t6–22 and all **O SUBMIT / O_self WAIT**; none are the reverse. About half of these
disagreements occur at t6 with the actor still present at age6 while the partner has
left/reentered or is younger. This strengthens a more specific explanation: coupled
planning sometimes commits a good current service *earlier* than isolated own timing,
leaving room for the other job later. It is not simply waiting to let the partner go
first, and it does not identify what G's network learned. The primary observation is
still whole-world J over all worlds, not the favorable divergent subset.

**Working update.** Ordinary G's gain over readiness is strengthened by three fresh blocks.
A stronger fitted transparent scheduler absorbs that gain and adds about .022 J in this
development batch. The value of coupled scheduling relative to the declared isolated-job
rule is strengthened, with remaining small-sample uncertainty. The stronger no-cost-trade
story is weakened. Model-family misspecification, decentralized information, adapting
teammates, changed clocks/horizons, and UAV deployment are untouched. Do not repair G merely
to preserve a neural advantage; keep O as the current development choice.

Scientific-process wall was **35.276 s**, CPU **34.829 s**, peak process RSS
**425,426,944 bytes**. G fit walls including endpoint collection were 8.509/8.660/8.462 s;
MLE walls .0071/.0053/.0067 s; planner-pair walls .0020/.0014/.0016 s. These small
compute costs exclude implementation, tests, launch preparation, collection and reasoning.
Fresh available physical/effective memory was 11,592,208,384 bytes; cgroup telemetry was
unavailable, not zero. Post-result readback verified **66 artifact digests and all86,016
native evaluation rows**, recomputed contrasts with math.fsum, and reconciled every curve
update/gradient count and endpoint-count total. An inefficient initial read-only checker
was interrupted and replaced by one that decompresses each array once; no learner/evaluator
was restarted and no scientific output changed. The completed readback took .794 s.

**Next decision.** A fixed fresh confirmation of O versus G can determine whether this
specific public-host package comparison is reproducible after development, while keeping
O_self secondary and retaining the tradeoff explanation. Proposed five new blocks,
unchanged 512-update G and O estimator, ten fits, no new architecture or score-dependent
rule choice. Seek Pro criticism of the actual claim/plan before this confirmation; continue
its bounded implementation and publication while advice is pending. This is not closing
VSP-03 or an automatic request for more seeds in B08.

### L0 B09 implementation — prepared while scientific criticism is pending

Owned changes: `experiments/candidates/vsp_03/opportunity_b09/study.py`,
`scripts/run_vsp03_opportunity_b09.py` and mirrored tests. Reuse B08's published
`train_and_evaluate` without changing any fit, observation, planner or panel code.
Only the five fixed fresh seeds, confirmation object identity and across-block df4
O−G reading change. Root output must preserve every block/technical failure and actual
fit counts. Tests use mocked blocks and literal statistics, not scientific fits; guard
tests verify direct CLI refuses before creating output. Reviewer checks the new entry
and aggregation. DM owns implementation and acceptance. Do not launch B09 until the
complete Pro answer is read and the DM has recorded its scientific choice; implementation
is independent preparation and creates no confirmation outcome.

Engineering acceptance: DM implemented the small B09 entry/aggregation and confirmed the
B08 scientific files are byte-unchanged. Independent Reviewer found no material finding:
five-block identity/order/completion, O−G sign, df4 interval and .02 context match the claim;
failure paths retain actual fits and do not retry. Five focused checks passed in1.57 s
(independent run1.25 s). Root failure accounting was source-inspected rather than exercised
by a new injected-failure test; inherited per-block partial publication was already tested.

## Pro question 2026-09-21 fitted-opportunity-confirmation

Conversation: new Jev direction consultation; private account/conversation details stay
only in the local transport operation. No App cross-task message is involved.

Question: Does the concrete B09 claim/confirmation plan below make a useful, defensible
next observation after B08, and what is the strongest material objection to its estimator,
comparison or explanation? Criticize the **actual plan**, not an unspecified future batch.
The decision is whether to run this fixed confirmation unchanged, amend it before any
outcome, or use a smaller materially discriminating alternative. Pro advises; the DM owns
the choice. No positive neural increment is owed, and an ordinary useful rule is a result.

Owner explicitly selected and reopened VSP-03 with independent direct ownership and no
time/fit allowance; current pause is lifted and registration is active. The task is the
real shared WAIT/SUBMIT eight-tick-slot H40 object, not Claude's label END. No FSD/B/C work
or cross-task communication is requested. Existing complete Portfolio advice was reused
for B08; this new call is specifically constitution5's pre-confirmation decision point.

Standing: the preceding complete B08 reading retains all positive and adverse evidence.
G−R0 remained positive on all three fresh blocks (mean+.01140625), while O−G was
+.023081055/+.022924805/+.020360107 (mean+.022121989). Coupled O−isolated O_self was
+.020233154/+.018049316/+.008978271. O estimated transition parameters from the same
eligible public history that G generated, without latent transitions/evaluation feedback.
The assumed reciprocal-age Markov family and independent targets are a structural resource;
true parameters appear only in extra-knowledge O_known. Tests and independent review found
no material executable defect. This is not a general proof of a fair optimal policy.

The naive explanatory prediction did not fully survive: O waits more than G and has more
expiry events, although team success and J increase. First O/O_self differences are all
earlier O submissions, not yielding. O_self omits reciprocal interference as well as partner
utility, so its gap is the value of coupled planning within this model, not a pure externality
mediator or what G learned. Strongest alternative is ordinary own survival/deadline timing;
the coupled increment is positive here but has only three development blocks.

Actual proposed claim and fixed reading: `docs/research/candidates/vsp_03/CLAIM_fitted_opportunity_b09.md`.
Five fresh blocks21901–21905; unchanged G512/O estimator; primary O−G; df4 t95 lower>0
for narrow superiority, old .02 scale reported without redefining it; secondary O_self
and other retained panels remain descriptive. Ten fits,18,841,600 team ticks,2,560 G Adam
calls plus five MLEs/planning and publication. No score-dependent expansion. If the simpler
rule is reproducibly useful, preserve it and its conditions instead of rescuing G. Please
assess whether this claim is worth confirming or whether the sharper remaining scientific
observation is different; no compulsory new architecture, host or candidate count.

Context (all unqualified paths resolve at source_sha supplied in the send):
- Governance: `docs/project/OPERATING_CONSTITUTION.md`, sections1–5,7–8; current owner
  authorization above supersedes historical pauses, allowances and old window language.
- Methods: `.agents/skills/hmasd-scientific-tools/SKILL.md`, Update the working explanation,
  Confirm a claim, Comparators, Statistics, Cost and exposure; engineering skill Checks and
  review/Execution for the code and proposed reuse.
- Evidence: this notebook's adoption, pre-result L0/critic correction, full declaration and
  B08 read; `runs/vsp_03/opportunity_b08_21801_21803/summary.json` and each block's raw
  per-world G/O/O_self rows, paired differences and first-disagreement records. Source input
  SHA was `4fb5a62363f863811d453facf8a14b21df2eff09`; results first published at
  `294982aa1302ab3f4eff5d6c471d2e91145eb3c7`. Complete relevant code is
  `experiments/candidates/vsp_03/opportunity_b08/opportunity.py` and `study.py`, inherited
  `vsp03_b02/b02.py` physics and `vsp03_b01/b01.py` objective. The B09 execution wrapper
  will reuse these frozen fit/evaluation functions with only new fixed seeds/aggregation.
- Prior advice: complete Answer/Decision of the Portfolio review at
  `b6093d211fa33a81d05d490ffa5bc920f43605eb:docs/research/RESEARCH.md`, VSP-03 sections;
  historical B06/B07 retain their original results and are not pooled with B08/B09.

Return: assess the actual claim, units, pairing, model/data rights, prewritten rule and
cost. State what B08 strengthens/weakens/leaves untouched, especially whether earlier
commitment is a more defensible explanation than late yielding. Give the strongest
alternative and smallest useful discriminator; if revising, predict intermediate and
complete native effects and cost. No new empirical result or new idea is required.
Include MATERIAL_DISSENT yes/no and cite sources actually read; disclose consequential
unread sources. Do not turn Pro into an approval or new proof gate.

Write only into this question's initially empty `### Answer` subsection on branch
`codex/vsp03-opportunity-rule`, target `docs/research/candidates/vsp_03/NOTES.md`.
Read pinned source inputs; fetch the latest target blob before writing and use its actual
SHA. Preserve the question and every other byte. Stop on overlapping edits. No experiments,
other file changes or extra messages. Report the actual answer commit; if GitHub writeback
fails, give the complete answer in chat, not just a receipt or link.

### Answer
