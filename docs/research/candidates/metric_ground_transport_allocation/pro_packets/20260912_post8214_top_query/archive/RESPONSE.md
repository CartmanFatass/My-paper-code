Select one new **TOP-versus-intact-DENSE B/EXPLORE training-pair comparison** as MGTAP's next direction-local scientific question. Replacing the mean visible-partner query with the already delivered highest-local-SINR partner's query is a concrete change in how partner information conditions user pooling. It can preserve a particular partner's learned geometry instead of averaging it with other partners, while leaving the complete raw observation and all-partner context available. That is a useful, falsifiable package question—not evidence that the strongest link is the most relevant partner or that averaging caused the earlier losses.

**This is the final direction-level scientific selection of the bounded TOP/DENSE object described below.** It extends the previous COND-only eligibility to this named query replacement, not to a general architecture search. I recommend one fresh matched training unit and the proposed new 450-second-per-complete-arm, 900-second-native, 1,200-second-complete-invoked resource envelope for the proper investment route. This response does not grant that budget, assign a master, accept an implementation or launch anything. DENSE remains the generic default. No fourth unchanged COND/DENSE pair is selected.

## 1. The decision that the next observation should inform

The next observation should determine whether this particular single-partner-conditioned actor is worth optional further development relative to the intact generic actor at the stated native task and learning exposure. It should not attempt to prove that TOP improves on mean COND, identify attention causality, or explain the sign changes in the three completed COND comparisons. Those are different questions, and the proposed two-arm design does not answer them.

The current owner continuation is explicit in the new question's §1 and adopted by TASK: MGTAP must remain advancing; finishing the 8214 allocation did not stop the direction. The earlier intake's no-successor/no-consultation language describes that ended grant. It neither supplies spendable funds nor prohibits this newly authorized consultation. Both earlier M=no decisions and the subsequent one-pair M=yes remain historical facts. The completed cleanup is also a reported historical fact, not an action repeated here. [S1, §1][S1]; [S2, §§1, 4 and 6][S2].

The selected question is appropriately B/EXPLORE. Its motivation is transparently outcome-informed, and one fresh pair would provide a new realized package comparison. No source reading, attention formula or small parameter change can establish its empirical sign beforehand. The adopted evidence standard permits this kind of specifically motivated change after mixed or adverse observations without requiring a positive pilot, tuned headroom, exact optimum or complete mechanism explanation. It does not require trying every implementable change. [S12, §§3–5.2 and 11.8–11.9][S12].

The dominant prospective work is already clear: two complete native fits, each with 512 training episodes and 32 final sampled episodes, five acting UAVs, and four recurrent PPO epochs per two-episode rollout. There is no extra candidate, trajectory, solver or evaluation-panel dimension. The resource recommendation is therefore for a small direct learning comparison, not a search or diagnostic programme. [S10, `prospective_pair`][S10].

## 2. What the accepted observations actually establish

The three COND/DENSE observations remain separate, with their original meanings:

| Matched training unit | Complete COND minus DENSE J | Conditional evaluation SE | Positive / adverse final worlds | Original reading |
| --- | ---: | ---: | ---: | --- |
| 8212 | +0.005761321371348559 | 0.00888326841451271 | 19 / 13 | Inside MEI |
| 8213 | −0.02246957345594415 | 0.004312411137154014 | 5 / 27 | Adverse |
| 8214 | +0.02447811898058116 | 0.004658159652932406 | 26 / 6 | Above MEI |

These are the accepted values in the current question, intake and direction record, not quantities recomputed by this review. I do not form a pooled primary, select 8214 as representative, or treat the evaluation worlds as additional training units. [S1, §2][S1]; [S2, §2][S2]; [S5, opening 8214/8213/8212 sections][S5].

For 8214 specifically, the reported own-arm means are 0.20802816765678933 for COND and 0.1835500486762082 for DENSE. Its conditional difference SD is 0.026350530227504637, and its reported differences range from −0.030099198498809404 to +0.07193109049112255. The six adverse worlds remain part of the positive aggregate. The E0 and intake report complete episode, rollout, private-stream, native-reward and primary checks; both branches moved, with projection displacements 0.53450608 and 0.52565241. These facts support a valid local learned-package observation, not attention identification or improvement over unmeasured initial policies. [S3, “Exposure and observations” and “Checks, cost and receipts”][S3]; [S2, §§1–2][S2].

**The strongest direct support for continued conditional-pooling exploration is 8214's first above-MEI native point. The strongest direct contradiction is the preceding unchanged 8213 adverse point.** Neither observation is TOP evidence. Together with the inside-MEI 8212 result, they leave generic DENSE adaptation, training variation and trajectory-dependent usefulness live. They do not diagnose the mean query, establish a stable ordering, or imply that the next changed actor should inherit a positive expectation.

The old REL/DENSE P75 aggregate, −0.02396310430506595, remains adverse evidence for a different package; its second master remains inside MEI. The older balanced-allocation-coordinate findings and historical C structural-nonidentification conclusions are preserved as summarized in the listed direction record and original response. They are not pooled with COND or transferred into a TOP estimate. [S5, P75 and family-boundary sections][S5]; [S6, §§1–2][S6].

DENSE remains a strong, valid comparison, not a deliberately deficient control. It receives the same ordered local information and recurrence and has the intact nonlinear branch. Its ability to use the same partner information is an alternative explanation for a small or adverse TOP contrast, not a reason that comparing finite learners is meaningless. Native tuned same-information headroom is absent. That limits competence and headroom claims; it does not create a tuning or baseline-qualification prerequisite for this B. [S1, §§2–4][S1]; [S7, `DenseResidualEncoder` and `NativeGeometryActor`][S7]; [S12, §11.7][S12].

## 3. The one selected change, precisely

### Source observations

At the specified source version, `ConditionalResidualEncoder` extracts twenty user triples from `x[3:63]` and ten partner quadruples from `x[63:103]`. It derives masks from the positive normalized-SINR components, applies the existing bias-free user and UAV maps, and forms the query from the first twenty components of the mean visible UAV embedding. Its all-partner context is separately summed and divided by ten. The complete raw affine input path is retained. `NativeGeometryActor` then applies tanh once before the existing GRU and velocity mean head. [S7, `ConditionalResidualEncoder.forward` and `NativeGeometryActor.forward`][S7].

The environment's `_local_uav_entries` selects eligible non-self partners and stably sorts them by descending actual SINR before observation normalization and clipping. The reference `_get_local_uavs_reference` also sorts the actual SINR values in descending order, retaining its existing tie order. Observation packing preserves that ordering and pads after the observed records. Consequently, when a partner is visible, delivered row 0 is the source-defined highest-local-SINR visible partner. TOP must use that row as delivered, not reconstruct an ordering from clipped SINR values or introduce a different tie rule. [S8, `_local_uav_entries`, `_get_local_uavs`, `_get_local_uavs_reference`, and observation packing][S8].

These source facts establish the row's meaning and legal availability. They do **not** establish its causal importance to service, its intended motion, which users it serves, or that it is the most relevant competitor.

### Exact TOP computation

Let the unchanged legal masks and embeddings be

\[
m^U_j=\mathbf1\{u_j[2]>0\},\qquad m^V_k=\mathbf1\{v_k[3]>0\},
\qquad e^U_j=\tanh(Uu_j),\qquad e^V_k=\tanh(Vv_k).
\]

Let nU and nV count the currently visible, truncated records. They are not global demand, served-user counts, persistent identities or a changing team membership. Retain the existing shapes U:20×3, V:21×4, P:64×41, W:64×108 and b:64, with no biases on U, V or P.

Replace **only** the query by

\[
q_{TOP}=\begin{cases}
e^V_{0,0:20},&n_V>0,\\
0_{20},&n_V=0.
\end{cases}
\]

Row 0 is valid whenever nV>0 under the inspected packing rule. Equivalently, the existing masked UAV embedding's row 0 provides the zero query when all partner slots are padding. No new learned query projection or parameter block is introduced.

Keep the existing scaled user scores, visible-user softmax and contexts:

\[
s_j=(e^U_j)^\top q_{TOP}/\sqrt{20},\qquad
\alpha_j=\frac{\exp(s_j)}{\sum_{\ell:m^U_\ell=1}\exp(s_\ell)}
\quad\text{for visible users},
\]
\[
c_U=\begin{cases}
\displaystyle\frac{n_U}{20}\sum_{j:m^U_j=1}\alpha_j e^U_j,&n_U>0,\\
0_{20},&n_U=0,
\end{cases}
\qquad
c_V=\frac1{10}\sum_k m^V_k e^V_k.
\]

The pre-activation remains W x+b+P[cU;cV], followed by the unchanged tanh, GRU(64,64), three-coordinate Gaussian mean and learned log standard deviations. All twenty-one UAV embedding components remain in cV, and every original partner row remains in the raw path. No partner is deleted from the actor's information. The current empty-user handling is retained; no undefined empty softmax is introduced. [S1, §3][S1]; [S7, encoder and wrapper definitions][S7].

DENSE remains W′x+b′+Q tanh(Dx+d), with D:16×108, d:16 and bias-free Q:64×16, followed by the same recurrent/action consumer. The recorded branch/encoder/complete-learner counts remain **2,768 / 9,744 / 69,079 per arm**, since TOP changes a reduction/selection computation and no parameter shapes. This is a source-based reuse of the existing count record, not a new model construction or parameter-count execution. Equal counts are not equal useful capacity, computation, optimization or hypothesis classes. [S7, `DenseResidualEncoder` and `make_encoder`][S7]; [S6, §3][S6].

### Why this is not a renamed mean or constant scale

For two visible users, a deduction from the defined softmax gives

\[
\log(\alpha_j/\alpha_\ell)=(e^U_j-e^U_\ell)^\top q/\sqrt{20}.
\]

At matched parameters and a fixed local observation, the TOP-versus-mean change in these log odds is therefore

\[
\frac{(e^U_j-e^U_\ell)^\top
\left(e^V_{0,0:20}-\frac1{n_V}\sum_k m^V_k e^V_{k,0:20}\right)}{\sqrt{20}}.
\]

This can change relative user emphasis, rather than only a fixed context amplitude. It is a short algebraic reading of the proposed computation, not a numerical diagnostic or proof that TOP has a larger policy class. The computation may also change query magnitude, attention sharpness and gradient routing; those are part of the package, not isolated geometry effects.

There are important limiting cases. With zero or one visible partner, TOP and mean-query pooling coincide at the same parameters. With no users the user context is zero; with one user its softmax weight is one, so changing the query cannot change that user context. Multiple partners and multiple distinguishable user embeddings are thus necessary for the immediate user-pooling difference, but not sufficient for a useful action difference. Query cancellation, equal scores or a downstream policy that ignores the residual can remove the practical effect. These identities do not imply that independently trained TOP and COND policies agree later. No event-frequency census or retained-trajectory replay is selected to quantify the cases. [S7, supplied computation][S7]; [S6, §§3–4][S6].

## 4. Native consequence and the strongest challenge to the hypothesis

The proposed event is a UAV observing user groups at different bearings while the highest-local-SINR visible partner's relative geometry changes toward one group. The hypothesis is that using that partner's embedding directly can make a useful conditional velocity response easier to learn than a query averaging several partners. A response might redirect this UAV toward another observed group, or preserve useful service rather than following a diluted context. Neither redirection nor approach is hard-coded; native return decides which behavior is useful. [S1, §3][S1].

The full trace is: **own and partner motion → source-ranked local geometry/SINR records and this UAV's private history → TOP-conditioned relative user weights → primitive velocity distribution → native clipped motion, channel/interference/SINR changes and capacity-limited association → original team service reward → ordinary team-advantage PPO updates → later learned velocities.**

The host remains five UAVs and fifty users, 256 one-second steps, a 1000 m square, 50–150 m altitude and the existing 30 m/s component velocity scale. Membership, primitive decisions, free-space/vectorized dynamics, observation restrictions and recurrence are unchanged. The actor does not select connections. The association remains at most one UAV per user and up to ten users per UAV. The default reward remains 0.7 times the connected-user fraction plus 0.3 times mean connected-link SINR quality; J uses the original sum of per-agent rewards rather than an additionally averaged adapter scalar. [S4, §2][S4]; [S6, §4][S6]; [S8, `_compute_reward`][S8].

The query itself uses a current row, not a partner velocity or intention. Apparent relative motion may reflect this UAV's own motion, and a change in row 0 can be a rank switch rather than continued observation of the same partner. The unchanged private GRU can use history, but neither an RNN nor a highest-link label guarantees sufficient state or entity tracking. This is why no persistent identity, communication, global assignment, counterfactual credit or new observation is inferred. [S15, §§2–3][S15]; [S8, ordering and packing][S8].

**The strongest structural contradiction is that radio prominence need not identify the partner that matters most to user service.** A weaker-link partner may dominate contention near an important user group. Mean pooling may contain useful distributed context that TOP discards from the query. Near-tied partners may exchange the first rank and cause abrupt query changes; raw input already reorders, but this new use of row 0 can amplify the effect. Selecting one partner can reduce cancellation, yet also sharpen a wrong response or encourage co-adapting UAVs to choose the same alternative. All-partner raw/context access mitigates information loss but does not guarantee that finite learning compensates for the bias.

The latest positive COND point supplies no resolution of that contradiction. The preceding adverse point and earlier REL losses were not localized to query cancellation. A favorable TOP result would still admit generic optimization, altered query scale, parameter sharing and trajectory variation as explanations. DENSE can learn the relevant response using its existing ordered nonlinear input and recurrence. [S1, §§2–5][S1]; [S2, §2][S2]; [S16, package-versus-mechanism discussion][S16].

The listed literature material is explanatory only. The question reports a refreshed CAMA source-page reading, and the older design return reports CAMA/MARC passages. Those methods differ, including CAMA's action-prediction/communication machinery. I did not access their unlisted local papers or independently verify those reports, and they supply no TOP effectiveness or novelty evidence. The decision rests on the inspected native operation and a bounded test of its consequence. [S1, §5][S1]; [S11, §7][S11].

## 5. Why the runner-up loses

The serious runner-up is to reject TOP for now and take a bounded source/design refinement of partner relevance instead of spending on a TOP fit. Its strongest argument is sound: highest SINR is an untested selection heuristic, and three mixed COND observations do not make it the demonstrated best next intervention. I do not claim otherwise.

It loses here because the concrete uncertainty left by this proposal is its finite-learning native value, not an unresolved input entitlement, query definition or measurement consumer. The operation, empty cases, intact comparator, action/reward path and limited work are specified. Another source-only description cannot establish which query produces better trained native behavior. A direct two-arm B is the smallest empirical comparison of the proposed optional package against the standing generic choice; requiring a relevance certificate or a cancellation diagnosis first would answer a stronger, different question.

This is a modest, revisable question-selection judgment, not a theorem that TOP has greater expected research value than every alternative. The operation is specific enough to risk one bounded observation, while the intact DENSE comparison and all-outcome interpretation make that risk informative. No broad menu, stronger-class prerequisite or fourth unchanged COND pair is substituted. The owner's continuation instruction rules out treating grant closure as a direction stop; it does not itself establish TOP's scientific merit. [S1, §§1 and 6][S1]; [S12, §§11.8–11.9][S12].

Omitting mean COND is deliberate. The question is optional TOP-package usefulness versus DENSE, not whether choosing row 0 is better than averaging. A third mean-COND arm would add another full fit to answer that additional question. It is not selected. Omitting it relinquishes contemporaneous TOP-minus-COND comparison and causal query attribution, not the meaning of a trustworthy TOP-minus-DENSE result.

## 6. The bounded scientific object and its inference

Use **one unscreened fresh matched training master**, still unassigned, with two fresh on-policy learners: TOP and intact DENSE. Retain the existing common/private generation law. Common raw encoder, GRU, velocity head, log standard deviations and critic start from the same fresh template; private row/hidden initialization uses the existing separate stream, and both residual output projections begin at zero. The initial policies coincide algebraically, but the branch's useful learning is not known in advance. Preserve initialization draw order when adding TOP; do not construct and discard extra candidate encoders. [S7, `make_encoder` and `NativeGeometryActor`][S7]; [S9, `build_cond_pair`][S9].

Retain the inherited seed-domain law with b=100000s: common template b+11 and private branch b+12; construction b+1000, training resets b+1000+e, separate per-arm advancing velocity generators initialized at b+21; final resets b+2000+e and private per-arm evaluation velocity generators b+3000+e. Existing unused-duration stream conventions remain unchanged; no duration decisions are added. Pair exogenous inputs, not trajectories or optimizer histories. No old checkpoint, state, seed screen, intermediate checkpoint selection or fourth unchanged pair enters the comparison. [S4, §2][S4]; [S6, §3][S6]; [S9, factory][S9].

Keep CPU FP32/thread1 and the accepted primitive recurrent PPO settings: gamma one, standardized detached team advantage, agent-compound velocity density and ratio clipping at [0.8,1.2], entropy coefficient 0.01, ordinary critic, four full-rollout epochs and 32-step recurrent chunks. Retain Adam 3e-4 with the inherited betas/epsilon, no weight decay or scheduler, value coefficient 0.5 and global gradient clipping 0.5. No auxiliary loss, duration, mean-action evaluation or counterfactual credit change is selected. These are inherited documented learner conditions, not a claim that this review executed or newly audited an unlisted learner file. [S4, §§2–3][S4]; [S6, §§4 and 6][S6].

The proposed primary is

\[
J_{a,e}=\frac1{256}\sum_{t=0}^{255}\sum_{i=1}^{5}r_{a,i,t},\qquad
 d_e=J_{TOP,e}-J_{DENSE,e},\qquad
 \Delta=\frac1{32}\sum_{e=0}^{31}d_e.
\]

Use all 32 ordered, complete sampled final episodes per arm, with every own-arm return and paired difference retained. The existing reducer's statistical operation—paired-difference sample SD divided by sqrt(32)—is sufficient for conditional evaluation SE. A correctly bound TOP readout must not publish the old COND label or silently average an available subset. No new statistical framework or result recomputation is performed here. [S9, `primary`][S9].

There is **one matched training unit**, not 32 training replicates, five independent learners per arm or 2,048 independent observations. Its conditional SE cannot estimate training-seed population uncertainty. The prior three COND observations are not extra TOP units; no historical pooling, synthetic replication or stable-superiority inference is selected. The foundational distinction between representability and finite learning justifies retaining DENSE intact; the distinction between episode and training randomness fixes this claim ceiling. [S15, §§4 and 6][S15]; [S16, randomness hierarchy][S16].

Retain absolute MEI **0.01 J**, with the host-specific scale that an additional continuously connected user contributes 0.014 to the coverage term before quality changes. This is a useful comparative scale, not measured headroom, a service guarantee, a universal investment threshold or the old allocation AUC quantity. [S4, §4][S4]; [S8, default reward][S8].

| Future complete primary | Meaning and subsequent recommendation |
| --- | --- |
| Delta > +0.01 | A local TOP-package development signal at this exposure. Consider separately selected bounded repeatability work if the complete observation and cost warrant it; do not change the generic default or authorize a successor automatically. |
| −0.01 ≤ Delta ≤ +0.01 | No demonstrated gain beyond the chosen scale. Preserve the actual sign and adverse worlds; not equivalence. End that numerical allocation without an unchanged automatic continuation; MGTAP's next direction step remains distinct. |
| Delta < −0.01 | Adverse evidence for this exact TOP package. Recommend against carrying it forward unchanged on the strength of favorable weights or motion appearances; no broad geometry failure or lifecycle PARK follows. |
| Primary incomplete or damaged | No paired performance polarity. Retain independently trustworthy own-arm facts, actual exposure and the exact dependent gap; no automatic retry, replacement master or recovered budget. |

DENSE remains generic in all branches until a proper later decision changes it. No H panel is selected, so there is no new hover-relative comparison or competence claim. No causal/attention panel is selected, so even a positive primary cannot identify strongest-partner relevance or attention/geometry/credit causality. The ceiling is the realized native TOP/DENSE package outcome on this fixed host, not training-population superiority, equivalence, optimal transport, scaling, churn, transfer, deployment or formal UAV validation.

## 7. Work and the recommended fresh resource envelope

The supplied machine-generated exposure record gives the following prospective work; none has been executed in this consultation:

| Work unit | Per learned arm | One TOP/DENSE pair |
| --- | ---: | ---: |
| Complete training episodes, 256 steps each | 512 | 1,024 |
| Native training team ticks | 131,072 | 262,144 |
| Two-episode rollouts | 256 | 512 |
| Adam calls, four epochs per rollout | 1,024 | 2,048 |
| Final sampled episodes, 256 steps each | 32 | 64 |
| Native final evaluation ticks | 8,192 | 16,384 |
| All complete episodes | 544 | 1,088 |
| All native team ticks | 139,264 | 278,528 |
| Logical actor-row opportunities including recurrent reprocessing | 3,317,760 | 6,635,520 |

The per-arm actor-row figure is the inherited record; the pair count is explicitly supplied in EXPOSURE.json. These are logical opportunities, not measured useful attention events or wall-time units. Native radio/association work, five recurrent actor streams and four PPO passes are intrinsic algorithm work, not free validation. TOP still evaluates the existing user/UAV maps, masks, user dot scores, softmax, context projection and recurrent consumer. Selecting delivered row 0 adds no user-by-partner table, policy search, solver call, trajectory branch or independent panel. It also does not prove a speedup: the all-partner context remains, and changed forward/backward rates are unmeasured. [S10, counts][S10]; [S1, §4][S1]; [S6, §7][S6].

The complete per-arm law remains

\[
C_a=C_{init,a}+131072\,c_{env+actor,a}+1024\,c_{update,a}
+8192\,c_{eval,a}+C_{checkpoint/publication/exit,a}.
\]

I recommend the author's **new** envelope for the proper Portfolio route: TOP at most 450 seconds per complete arm, DENSE at most 450 seconds, the complete native pair at most 900 seconds, and complete future invoked work at most 1,200 seconds. The 300-second support amount is a planning reference within that proposal, not a scientific-validity cutoff or a statement that support has been measured. No portion of the completed 8214 grant is transferred. [S1, §4][S1].

Preserve the prospective shared-cost convention: TOP first receives admission/startup and common construction through its own final panel; DENSE receives the remaining native comparison, reduction, closed publication and outer exit remainder. Charge shared work once and retain an unattributed tail rather than using it to reduce an arm's cost. Added checks/review, staging, monitoring, collection, integration and scoped retention/cleanup are support work, separate from the intrinsic learner work. Provider/authoring and idle calendar time are separately described; unknown portions are not zero.

The latest unchanged pair's **361.85-second** native wall is planning evidence, with reported arm charges **198.38539502117783** and **163.4646049788222** seconds. The latter includes **5.85604484882208** seconds of outer remainder. Peak RSS was 560,596 KiB, while aggregate CPU was unmeasured. These are observed COND/DENSE quantities, not a TOP runtime or activation-memory forecast. The accepted support account did not establish a complete 300/1,200-second certificate or a breach; that limitation does not erase its independently accepted performance observation. [S3, cost section][S3]; [S2, §3][S2].

The proposed envelope is reasonable to put forward because it retains an observed complete native workload and adds no new search or panel dimension. That is not an affordability certificate: TOP rates, activation memory, complete support and provider costs remain unknown. I do not require a timing probe, reconstruct the entire old support history, or silently relax any later allocated cap. A concrete infeasibility discovered during separately allocated preparation should return with the affected work and consequence; the question and necessary evidence can be reconsidered rather than silently truncating training or hiding cost. [S12, §11.9][S12].

## 8. Readiness, proportional acceptance and authority effects

TOP is absent from the inspected source. `make_encoder` currently recognizes REL, COND and DENSE; `build_cond_pair` and `primary` are bound to COND/DENSE. A new TOP object requires the actual query operation and correct new identity/factory/readout, preserving the accepted historical implementations and results. Relabeling a completed COND run is not an implementation. The current source establishes a feasible insertion point, not tested TOP behavior. [S7][S7]; [S9][S9].

For later bounded implementation, the relevant focused acceptance is the changed query and its dependent primary: delivered-row selection and empty masks, unchanged all-partner/raw paths and parameter shapes, common/private initialization, loss connection after the zero projection moves, and correctly ordered TOP/DENSE native-score publication. Existing PyTorch/autograd can check the local connection without a native event census; the existing statistics reducer supplies the final conditional summary. The actual high-risk numerical/RNG/recurrent diff receives the already required independent review under Engineering Scope §7.3. This creates no extra approval service, duplicate numerical smoke, historical replay or mechanism-validation gate. Engineering Scope §4 machinery needed: none. No implementation or test is performed or commissioned as an external action by this response. [S13, §§4–5, 7.1 and 7.3][S13]; [S12, §§11.4 and 11.8.6–11.10][S12].

**Direction effects.** The next selected scientific object is exactly one fresh TOP/DENSE B pair with the operation and limits above. This is an explicit extension beyond the original COND-only eligibility, not a silent interpretation of that earlier decision. The old balanced-allocation-coordinate family stays parked; the historical native-family boundary is changed only to admit this named TOP question. P75, each COND pair, historical C meanings and recast count remain unchanged. No broad family search, C promotion or fourth unchanged pair is opened. MGTAP remains advancing under the current owner instruction.

**Portfolio and execution effects.** Lifecycle, priority, capacity, investment and formal UAV-entry records do not change here. The new work/resource need is ready for Root's proper Portfolio route and the designated DM's existing intake/preparation process; it is not a fresh grant or launch receipt. No additional owner-ratification gate is invented. The old M allocation remains closed, and no historical control endpoint is adopted as a live dispatch route. DENSE remains the generic default. [S1, §§1 and 6][S1]; [S14, §§1–4][S14].

Actual scientific invocations, models, checkpoint loads, environment constructions, training/evaluation steps, optimizer calls, fixtures, simulations and profiling in this consultation are all zero. Source inspection and the scoped response delivery are administrative work, not free activity and not empirical evidence of TOP performance. The remaining uncertainty concerns which partner matters, how often TOP differs usefully, learning variability, the intact generic response and complete future costs. The selected direct native comparison can supply one package observation; it cannot resolve all of those uncertainties or authorize an automatic successor.

## 9. Actual source access and limits

All seventeen manifest paths were accessed through the connected GitHub connector at their individually specified commits. The task itself was read at `7edd25cdcc81a604ae25a3309fd2371664e971e5`. Source/design, result, historical decision and current method versions were kept separate. The references below resolve to the exact path and effective full SHA; section and function citations above identify the material used.

| Reference and exact repository path | Access used |
| --- | --- |
| [S1 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_POST8214_DIRECTION_QUESTION_20260912.md`][S1] | Complete §§1–6 at aae355b2a7485a53a58e0b9d996496bbe172eb77. |
| [S2 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_CONDITIONAL_POOLING_B01_8214_INTAKE_20260912.md`][S2] | Complete intake, including §§1–4 and completed cleanup §6, at 6561056ed6f2f51d57801d315af2ca8749cee6d2. |
| [S3 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_CONDITIONAL_POOLING_B01_8214_RESULT_20260912.md`][S3] | Complete E0 at a12fb206aeac848ccf5f7dc585e9a35afeef0f03. |
| [S4 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_CONDITIONAL_POOLING_B01_8214_SCIENCE_CARD_20260912.md`][S4] | Inherited comparison, generation, exposure and primary in §§2–4, with authority context, at 10ea737f0f9210ee2c126ad1e095734f21d4fcbc. |
| [S5 — `docs/research/candidates/metric_ground_transport_allocation/DIRECTION.md`][S5] | Opening 205 lines: accepted 8214/8213/8212, COND eligibility, P75 and prior family summaries, at a12fb206aeac848ccf5f7dc585e9a35afeef0f03. |
| [S6 — `docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260910_conditional_pooling_reentry/archive/RESPONSE.md`][S6] | Opening and §§1–7 at its original delivery commit 319c51a5fdc411eaaf1a47557d032f23ed269265. |
| [S7 — `experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/geometry.py`][S7] | Named encoders, factory and actor initialization/recurrent insertion at 10ea737f0f9210ee2c126ad1e095734f21d4fcbc; no import or execution. |
| [S8 — `envs/pettingzoo/uav_env.py`][S8] | Lines 375–510, 565–667 and 1421–1487: packing, actual-SINR ordering/ties and default reward, at 10ea737f0f9210ee2c126ad1e095734f21d4fcbc. |
| [S9 — `experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/conditional_pooling.py`][S9] | `build_cond_pair`, `primary` and their supplied reading boundary at 10ea737f0f9210ee2c126ad1e095734f21d4fcbc. |
| [S10 — `docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260912_post8214_top_query/EXPOSURE.json`][S10] | Complete zero-exposure and prospective-count record at aae355b2a7485a53a58e0b9d996496bbe172eb77; not recomputed. |
| [S11 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_CONDITIONAL_POOLING_SOURCE_DESIGN_RETURN_20260910.md`][S11] | §7's reported literature access and limits at e4666a5c1aecc9a4d84cad4c724970e5392cfc25. |
| [S12 — `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`][S12] | Adopted §§3–5.2, 11.4 and 11.7–11.10 at 6c2cde9453d503c519372d3a946a99413a81ec8b; unrelated object exceptions not applied. |
| [S13 — `docs/project/ENGINEERING_SCOPE_SPEC.md`][S13] | Adopted §§4–5, 7.1 and 7.3 at 6c2cde9453d503c519372d3a946a99413a81ec8b. |
| [S14 — `AGENTS.md`][S14] | Adopted §§1–4 and shared-branch §6 at 6c2cde9453d503c519372d3a946a99413a81ec8b. |
| [S15 — `docs/rl-marl-foundations-20260907/FOUNDATIONS.md`][S15] | §§2–4 and 6 at 6c2cde9453d503c519372d3a946a99413a81ec8b; information, joint-credit and finite-learning limits applied above. |
| [S16 — `docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md`][S16] | Comparison, randomness, attribution and return/cost passages at 6c2cde9453d503c519372d3a946a99413a81ec8b. |
| [S17 — `docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260912_post8214_top_query/ISSUE_SNAPSHOT.json`][S17] | Complete scoped snapshot at 94d202b754ae23c48cbe547cce9c7b902b6e870e. |

The live [issue #18][ISSUE] body was read, and its comments were rechecked at approximately **13:35 PDT on September 12, 2026 (20:35 UTC)**; there were no pre-delivery comments or matching delivery to reuse. The pinned snapshot separately records the author's observation at **2026-09-12T20:23:15.137277+00:00**, not this review's time. Issue #5 remains only historical provenance within the permitted documents; it was not newly retrieved for this task.

No listed critical or explanatory path was inaccessible. The permitted E0/intake report retention and validation of all raw outcomes, but their linked raw CSVs, archives, checkpoint files and collection records are outside this manifest and were not independently opened or replayed. This review preserves their reported acceptance and all summarized adverse outcomes without claiming a new raw-data audit. No unlisted repository dependency, local library file, web mirror, moving scientific source or numerical execution was used. Delivery-branch HEAD/target/ancestry reads serve only the authorized publication, not scientific evidence substitution.

[S1]: https://github.com/CartmanFatass/My-paper-code/blob/aae355b2a7485a53a58e0b9d996496bbe172eb77/docs/research/candidates/metric_ground_transport_allocation/MGTAP_POST8214_DIRECTION_QUESTION_20260912.md
[S2]: https://github.com/CartmanFatass/My-paper-code/blob/6561056ed6f2f51d57801d315af2ca8749cee6d2/docs/research/candidates/metric_ground_transport_allocation/MGTAP_CONDITIONAL_POOLING_B01_8214_INTAKE_20260912.md
[S3]: https://github.com/CartmanFatass/My-paper-code/blob/a12fb206aeac848ccf5f7dc585e9a35afeef0f03/docs/research/candidates/metric_ground_transport_allocation/MGTAP_CONDITIONAL_POOLING_B01_8214_RESULT_20260912.md
[S4]: https://github.com/CartmanFatass/My-paper-code/blob/10ea737f0f9210ee2c126ad1e095734f21d4fcbc/docs/research/candidates/metric_ground_transport_allocation/MGTAP_CONDITIONAL_POOLING_B01_8214_SCIENCE_CARD_20260912.md
[S5]: https://github.com/CartmanFatass/My-paper-code/blob/a12fb206aeac848ccf5f7dc585e9a35afeef0f03/docs/research/candidates/metric_ground_transport_allocation/DIRECTION.md
[S6]: https://github.com/CartmanFatass/My-paper-code/blob/319c51a5fdc411eaaf1a47557d032f23ed269265/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260910_conditional_pooling_reentry/archive/RESPONSE.md
[S7]: https://github.com/CartmanFatass/My-paper-code/blob/10ea737f0f9210ee2c126ad1e095734f21d4fcbc/experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/geometry.py
[S8]: https://github.com/CartmanFatass/My-paper-code/blob/10ea737f0f9210ee2c126ad1e095734f21d4fcbc/envs/pettingzoo/uav_env.py
[S9]: https://github.com/CartmanFatass/My-paper-code/blob/10ea737f0f9210ee2c126ad1e095734f21d4fcbc/experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/conditional_pooling.py
[S10]: https://github.com/CartmanFatass/My-paper-code/blob/aae355b2a7485a53a58e0b9d996496bbe172eb77/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260912_post8214_top_query/EXPOSURE.json
[S11]: https://github.com/CartmanFatass/My-paper-code/blob/e4666a5c1aecc9a4d84cad4c724970e5392cfc25/docs/research/candidates/metric_ground_transport_allocation/MGTAP_CONDITIONAL_POOLING_SOURCE_DESIGN_RETURN_20260910.md
[S12]: https://github.com/CartmanFatass/My-paper-code/blob/6c2cde9453d503c519372d3a946a99413a81ec8b/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[S13]: https://github.com/CartmanFatass/My-paper-code/blob/6c2cde9453d503c519372d3a946a99413a81ec8b/docs/project/ENGINEERING_SCOPE_SPEC.md
[S14]: https://github.com/CartmanFatass/My-paper-code/blob/6c2cde9453d503c519372d3a946a99413a81ec8b/AGENTS.md
[S15]: https://github.com/CartmanFatass/My-paper-code/blob/6c2cde9453d503c519372d3a946a99413a81ec8b/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[S16]: https://github.com/CartmanFatass/My-paper-code/blob/6c2cde9453d503c519372d3a946a99413a81ec8b/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
[S17]: https://github.com/CartmanFatass/My-paper-code/blob/94d202b754ae23c48cbe547cce9c7b902b6e870e/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260912_post8214_top_query/ISSUE_SNAPSHOT.json
[ISSUE]: https://github.com/CartmanFatass/My-paper-code/issues/18
