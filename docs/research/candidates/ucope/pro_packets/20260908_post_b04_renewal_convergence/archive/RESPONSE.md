**Select the renewable own-expiry comparison, and classify the change as a direction-level RECAST from opening-only commitment to renewable commitment.** Retain exactly one new B/EXPLORE object, **UCOPE-UAV-RENEWAL-COMMITMENT-B01**, with fresh matched training-pair master **7301**, the proposed two-fit budget, and no automatic second pair. The specific reason is that the tested duration policy never chooses persistence using an evolved within-episode history: it acts only at reset. Repeated own-expiry decisions test a materially different temporal control opportunity without changing the task, free information, architecture or native-step/update budget. This is worth one bounded performance comparison, narrowly, despite the adverse history and materially greater duration-head work. It is not a finding that sparse opening exposure caused B04 or that renewal will improve return.

The completed opening-only evidence remains unchanged and receives no new unchanged allocation. The older retained-policy/root-residual numerical-locus family remains paused. This decision neither closes UCOPE nor changes its formal UAV-entry record, Portfolio lifecycle, priority or capacity. The owner resume permits this new decision; it does not replenish P61's spent allowance. The selected comparison requires its new prospective card and conforming implementation before the subsequent bounded execution; none of those operations occurs in this consultation.[^direction][^resume]

## Why this is a recast, and why it is worth one comparison

The previous Convergence explicitly selected a single opening duration and excluded every later option. Replacing that law with a duration choice at every owning UAV's expiry changes the intervention's event set, reachable commitment schedules and distribution of actor credit throughout the episode. It is therefore not merely another seed, an opening-head adjustment, a diagnostic-burden change or a renamed continuation under the old permission. **This verdict contributes one genuine Convergence RECAST to the existing direction-level account; the new object name does not reset that account.**[^previous][^agents]

Apply the standing rule in AGENTS §2 without inventing historical counts: carry forward the existing genuine Convergence-recast count and add this verdict once. The supplied record identifies the recent UAV decisions as OPEN and CONTINUE, not prior RECAST verdicts; the dated September 2 section-11 class-demotion record must not be retroactively relabelled. The scoped evidence does not establish a separate complete lifetime numerical count. If the existing recorded count makes this the second Convergence RECAST, the already-standing consequence applies: the bounded decision still executes, the DM uses the existing `second-recast` flag, and Root applies lowest sequencing among ACTIVE directions. That is application of the existing rule, not a new priority decision, lifecycle PARK or additional owner-approval gate made here.[^preparation][^agents]

### The observation being purchased

The next observation asks whether **repeated, action-conditioned commitments using current private history improve complete native team return over ordinary stepwise feedback at the stated learning budget**. It does not ask whether B04 was almost successful, whether a timer works, or whether an exact optimum exists.

The strongest reason to retain no successor is substantial: generic feedback has the higher current sampled return; B02 was adverse even against hover; P24 contained harmful treatment behavior; and neither the common-learning amendments nor command-conditioned opening B04 established a durable opening advantage. Ending the tested investment now would save all new implementation, review and training work, not merely simulator time. That option is scientifically legitimate and would not imply impossibility.

I nevertheless select the comparison because its new opportunity is concrete and source-defined. B04 already has the relevant command-conditioned head and continuously updated private recurrence, but the head is never allowed to decide again from that later history. A renewal policy can test persistence in those later contexts while G retains exactly the legal feedback that may make persistence unnecessary. This changes the performance question directly. An unchanged B04 pair would instead address repeatability of its within-band negative point. An attribution arm, counterfactual search or exact headroom calculation would purchase stronger, different claims; none is needed for the selected package comparison. The justification is the new event and bounded observation, not an expectation of a favorable sign.[^preparation][^environment][^learner][^policy]

The additional head work is not dismissed as small merely because parameters and simulator steps are unchanged. Its known forward-row count grows 64–256-fold. I retain the existing complete time caps, with incremental seconds explicitly unknown; neither a timing pilot nor an expanded cap is selected. The detailed work and refusal boundary below are part of this choice.

## What B04 and the earlier results actually establish

B04's accepted single matched training pair 7201 is **COMPLETE / WITHIN**, with the original primary and uncertainty preserved:

| B04 quantity | Mean | Conditional paired-episode SE |
| --- | ---: | ---: |
| T native J | 0.18320920071658314 | — |
| G native J | 0.18715742666070528 | — |
| H native J | 0.16333870700710337 | — |
| T−G | −0.003948225944122139 | 0.010191826216031805 |
| G−H | +0.0238187196536019 | 0.011454243503509544 |
| T−H | +0.019870493709479763 | 0.014677398371169156 |

The primary includes **18 positive and 14 negative** evaluation differences, ranging from **−0.16125563298518442 to +0.09350894263405753**. A majority of positive episodes does not reverse its negative mean. The WITHIN rule is a point-reading rule at ±0.01, not a statistical equivalence test. The independent learning unit is one matched trained pair; 32 evaluations do not estimate training-population variation. G's positive hover contrast is a narrow sampled competence observation, not tuned-generic competence or headroom. Positive T−H does not rescue negative T−G.[^intake][^facts]

Keep the history separate rather than creating another pooled result:

| Original observation | Preserved meaning |
| --- | --- |
| P21: two pairs, mean T−G +0.0152174206, UP | The earlier positive package support remains, including its limited margin and uncertainty. |
| P24: two new pairs, mean −0.0035067780, WITHIN | Opposite endpoints and harmful 6902 behavior remain; its favorable comparison against a weak generic is not universal competence evidence. |
| B02: two pairs, mean −0.026701655118179134, DOWN | Both T−H endpoints were negative; G−H was mixed. This is strong contrary package evidence, not a causal verdict about clipping. |
| B03: one pair, T−G −0.010093085146628955, DOWN | Preserve the strict near-boundary classification and both positive hover contrasts; no stable harm or entropy causality follows. |
| B04: one pair, T−G −0.003948225944122139, WITHIN | No demonstrated point gain at the selected scale/budget; its less-negative point than B03 is not an isolated conditioning gain. |

These facts are taken from the accepted B04 intake, current direction record, preparation and prior archived response. The original result files outside this manifest were not reread or their raw statistics recomputed. Different masters, objectives, fitted histories and capacity changes prevent treating this sequence as a controlled estimate of conditioning, entropy, clipping or renewal. Earlier finite-host findings remain their own evidence and do not become UAV replications.[^intake][^direction][^previous]

B04's operational evidence is also retained: **2,560** training duration samples; **73 four-step choices among 160** final openings; **40,741 versus 40,960** final T/G velocity decisions; and **40,960 recurrent observations in each arm**. The duration head's absolute movement was **0.41481131315231323**. These establish real learning, holds and continuing observations, not useful duration selection. The new decision does not convert them into a diagnosis of insufficient duration exposure.[^facts][^intake]

## Direct source facts, inference and selected new semantics

### Direct source facts

`learner.py::collect_episode` creates a fresh `HoldState` and zero private hidden state at each episode reset. It feeds the current local observation through the actor before sampling, so the opening head sees the processed reset observation—not an unprocessed zero recurrent vector. Both the duration mask and the sampler's opening argument are tied to `t == 0`. `environment.py::HoldState.decide` applies the sampled duration only at t0 and assigns one step at every later active row. During holds, the collector still runs the actor recurrence, critic and real environment step, records the native reward, and advances the timer.[^environment][^learner]

The accepted B04 policy already uses `Linear(67,32) → tanh → Linear(32,2)` on the owner's recurrent feature and detached `tanh(u)`. Its private head seed preserves common initialization, and only the final layer starts at zero. `joint_terms` evaluates that head only at true duration-mask rows. The study configuration supplies B04/7201, not a renewal selector or 7301 implementation. These are text-inspected source facts; no module was imported and no candidate was executed.[^policy][^study]

**Inference:** permitting the same head to act at later own expiries exposes it to evolved private histories and changing service/teammate conditions that the opening-only duration decision never encountered. That is a testable opportunity, not proof that the added decisions carry useful information or receive sufficient learning credit. The strongest alternative remains ordinary feedback doing the useful control itself; repeated commitments may amplify poor commands or delay adaptation to moving partners.

### The limited role of literature

The preparation records a 190-record real-corpus snapshot, eight lexical candidates and two substantively verified papers. Its UTE pointer—VS-0005, page 3, elements 95–96 and 144—supports action selection followed by conditional extension at option initiations. Its ACAC pointer—MARL-0449, page 1 element 382, page 2 element 388 and page 3 element 410—supports new macro-actions at each agent's own completion. Those are the preparation's verified source findings, not new paper reads by this node.[^preparation][^facts]

UTE's single-agent Q-learning, ensembles and counterfactual updates are not evidence for this PPO/MARL/UAV effect. ACAC's missing macro-observation and padding problem is not automatically present here, because this collector retains fresh primitive observations and critic rows. No ensemble, extra replay, attention, encoder replacement or new GAE is selected. The documented metadata warnings and prior identity-check provenance remain; My-lib's reported two synthetic fixtures are excluded. No novelty, comprehensive literature-coverage or knowledge-integration claim is made. The source-defined control question does not depend on treating those papers as empirical validation.

## The selected renewable-commitment B

### Fixed host and information boundary

Use the existing `make_real` path to the base MultiUAV environment and adapter: **five UAVs, 50 users, uniform 1000 m area, height range 50–150 m, velocity scale 30, one-second primitive steps, 256-step episodes**, free-space channel, vectorized backend, no shadowing or FDMA, and **the existing default native reward** (`paper_reward=False`). Retain all other stated task and observation settings; no cheaper or faster replacement host is selected. This configuration is present in the permitted wrapper and B04 card. The underlying base-environment file is not in this manifest and was not independently reinspected here.[^environment][^card]

Actors retain their **own 108-component input**: the complete existing local observation, own previous command and own remaining-hold feature. Each UAV retains its private recurrent history throughout an episode, including across every expiry; hidden state is reset only between episodes. Shared policy weights do not make those histories public. The separate critic retains its **136-component predecision input**, including the existing global state and already-established commitments. Its information and diagnostic entity IDs do not enter actors. Other agents' newly sampled commands and future observations are not new actor features.[^environment][^card][^learner]

The binding MARL structure is **temporal abstraction/termination in a partially observed, co-adapting fixed team**. All five members act within the same ongoing physical simulation. There is no membership/lifetime change, learned interruption, added observation purchase, count channel, intrinsic reward or sensing charge. Movement affects direct service as well as future observations; this remains a native control-package question, not an isolated information-price estimand.

### Own-expiry events and physical execution

At the start of primitive step t, after receiving the current observation and advancing its recurrent feature, **each T UAV with remaining hold equal to zero** samples a velocity latent u and then samples duration d in {1,4} conditioned on its current private recurrent feature and actual normalized command a=tanh(u). The duration mask equals that owner's actual renewal eligibility. A held UAV draws neither a new velocity nor a duration. One teammate's expiry does not trigger a new decision for another teammate.

Execute the newly chosen command for the active owner and the previously held command for every inactive owner, then take **one common primitive environment step**. Native reward and next observations occur normally. Decrement remaining duration once after that step. At the owner's next expiry, sample both command and duration again. A selected d=1 permits feedback at the next primitive step; d=4 holds for four steps unless the episode ends first. Actors and critic remain active on every primitive observation, including rows when the whole team is holding. There is no team decision barrier and no simulation-time jump between expiries.

This changes the three connected scientific boundaries together: eligibility in the collector, eligibility in sampling, and the timer's use of duration at every own expiry. Merely replacing a scalar opening flag with “someone is active” would not implement the selected law: it would wrongly permit duration draws for holding teammates. This is a specification of the selected behavior, not a report of a source defect or a code patch.[^environment][^learner][^policy]

The full native route is:

**own expiry amid ongoing team movement → current legal local history and owned sampled command → persistence versus earlier feedback → real positions/channels/service and later free observations → later owned decisions → complete primitive native rewards and true masked PPO learning → final complete team return.**

### Administrative horizon censoring

Retain the fixed horizon without adding post-terminal work. A renewal beginning at s selects its original d even near the boundary, but can execute only

\[
\ell=\min(d,256-s).
\]

A hold is horizon-censored exactly when s+d>256. Store and score the likelihood of the **selected duration label**, not a relabelled effective duration. At t255, d=1 and d=4 may have the same one remaining physical step; that does not authorize replacing one label by the other during density recomputation. Both receive only the remaining observed native return. There is no terminal bootstrap, reward beyond t255, carryover of command or hidden state, or decision at t256.

Retain aggregate selected-d4, horizon-censored-hold and **actually suppressed decision** counts in existing summaries, separated by phase. For a completed segment, suppression is ell−1, not automatically three per selected d4. Thus d4 at t254 suppresses one remaining decision, and d4 at t255 suppresses none. Counts in an incomplete attempt describe only executed work. This requires no complete renewal-event dump; it prevents terminal truncation from fabricating exposure or credit. Selected duration versus executed duration is an administrative distinction, not learned early termination.[^preparation][^facts]

### Learner, initialization and true decision credit

Keep B04's shared 108→64 encoder, GRU-64, three-dimensional Gaussian velocity head and trainable log standard deviation; keep the **67→32→2** action-conditioned duration head. T/G totals remain **68,553 / 66,311 parameters**, with no new parameters relative to B04. T's 2,242 duration parameters are still a package difference from G; this is not a matched-capacity experiment.[^policy][^facts]

For **b=100000×7301**, preserve common actor/critic initialization b+11 and private T-head initialization b+12. Use ordinary head initialization, zeroing only its final weights and biases so initial duration probabilities are uniform for every condition. Training velocity and duration streams remain b+21 and b+22; training resets b+1000+e; final reset, velocity and duration streams b+2000+e, b+3000+e and b+4000+e. T and G start with the same common parameters, then use separate optimizers, trajectories and recurrent histories. Renewal changes T's action-draw consumption; no new cross-arm alignment, shared training trajectory or matched-outcome claim is introduced. The candidate's bounded 215-file nonreuse search is retained as bounded provenance, not a global seed census.[^card][^study][^facts]

At a true renewal for owner i, use the compound log density

\[
\ell_{i,t}=\log\pi_v(a_{i,t}\mid h_{i,t})
 +\log\pi_d(d_{i,t}\mid h_{i,t},a_{i,t}),\qquad a_{i,t}=\tanh u_{i,t}.
\]

The velocity calculation preserves the existing transformed-Gaussian Jacobian. Both behavior-density recording and PPO recomputation use the stored sampled latent and duration. The duration condition is **stored detached tanh(u)**, not the current mean, another sample or later physical displacement. Recomputed recurrent features and head parameters retain their likelihood gradients; no reparameterized gradient through a freshly generated command is added.[^policy][^learner]

Retain **agent-compound PPO clipping** in both arms. T has one velocity-plus-duration ratio on each own renewal, none on held rows. G has its ordinary velocity ratio at every step. Eligible owner surrogate terms are summed and averaged over **all primitive rollout rows**, including all-held rows. Do not divide by the number of active decisions or add a sparsity-compensation multiplier. Held observations can influence later recurrent decisions through the existing recurrent calculation; absence of a fresh held-row likelihood does not mean freezing memory during the hold.

Native credit remains

\[
r_t=\sum_i r^{\rm native}_{i,t},\qquad
R_t=\sum_{\tau=t}^{255}r_\tau.
\]

Keep gamma=1, no terminal bootstrap, the predecision critic, the existing scalar advantage normalization and detached old log probabilities/advantages. The whole primitive reward sequence is retained, so renewal does not require a new semi-Markov discount clock or a duration-only return that drops intermediate rewards. Preserve recurrent chunk length **32**, detached stored chunk-start states, **two complete episodes per rollout**, four full-rollout epochs, Adam lr **0.0003**, betas (.9,.999), epsilon 1e-8, weight decay zero, and the existing non-fused/non-foreach settings. PPO clip is **0.2**, value-loss coefficient **0.5**, and global gradient clip **0.5**. Explicit entropy coefficient remains **zero in both arms**; stochastic action selection and trainable variance continue. This is the same implemented PPO approximation and truncated recurrent training, not a new exact-gradient claim.[^learner][^card]

### The legal comparator and what this comparison cannot attribute

**G is ordinary same-information stepwise recurrent feedback**, trained afresh at the same native-step and Adam budget. Every legal velocity, including zero and repetition, remains available on every primitive step. G may exploit movement, geometry, private memory, persistence and observed partner effects itself. It is not weakened by banning movement or removing free observations. Its actual competence is assessed, not guaranteed by its name.

H remains the same-reset **untuned zero-velocity reference**, with no training and no new baseline search. Its role is to qualify generic competence and native harm, not replace the primary comparator or supply an upper/tuned-generic headroom record.

A positive T−G would support the renewable package on the observed fit. It would not isolate renewal from changed decision exposure, stochastic exploration, optimization, persistent motion or partner co-adaptation. The two arms do not estimate a direct renewal-minus-opening causal contrast; the historical B04 result is not a third randomized arm. No attribution arm is added, and those stronger claims are explicitly relinquished.

## Primary, independent unit and all-outcome interpretation

Select **one fresh matched training pair, master 7301**, with two genuine fits. Each arm trains **512 complete 256-step episodes**, **131,072 native team steps**, **256 two-episode rollouts** and **1,024 Adam calls**. Evaluate final checkpoints only, stochastically, on **32 whole matched-reset episodes for each T/G/H**. No checkpoint, seed or favorable renewal schedule is selected from evaluation.

For each evaluation episode,

\[
J_a(e)=\frac{1}{256}\sum_{t=0}^{255}\sum_i r^{\rm native}_{a,i,t}(e),
\qquad
\Delta=\frac1{32}\sum_{e=0}^{31}\big[J_T(e)-J_G(e)\big].
\]

Use the sum of the original per-UAV reward dictionary, as `team_reward` does; do not use an adapter scalar that averages that sum again. Preserve **all 96 J values**, every paired sign and difference, the three arm means and all T−G, T−H and G−H contrasts. Their SE is the sample standard deviation of the paired episode differences divided by sqrt(32), explicitly **conditional on the fitted policies**. There is one independent training pair, not two independent treatment-effect observations or 32 training replicates; no training-population SD or interval is available. No previous master, objective or finite-host result enters this primary.[^environment][^study][^card]

Retain **absolute MEI 0.01** on the existing horizon-average native team-return scale. It is the same one-percentage-point investment rationale; B04's stated coverage component 0.7/50=0.014 for one additional continuously served user is context for that scale, not guaranteed total-reward gain or measured headroom. No repository-wide threshold, significance requirement or tuned-baseline prerequisite is introduced.[^card][^spec]

| Complete new primary | Reading and next recommendation |
| --- | --- |
| Delta>+0.01 | Preliminary favorable renewable-package evidence on this task, fit and budget. Consider a separately justified bounded follow-up; no automatic second pair or stable-superiority claim. |
| −0.01≤Delta≤+0.01 | No demonstrated point gain at the selected scale/budget. Prefer no unchanged continuation of this tested package; not equivalence or proof that renewal cannot help. |
| Delta<−0.01 | Adverse native package evidence. Drop unchanged continuation from the next default choice; motion, information or duration diagnostics cannot compensate. |

Use unrounded boundaries and report proximity to the margin alongside conditional uncertainty. The contrary observation is that renewable control fails to earn the chosen native margin over legal feedback, especially if it loses while G also exceeds hover. This tests the bounded investment premise, not every policy in the renewal class.

If G−H is weak or negative, retain a trustworthy T−G observation but narrow the “over competent generic control” wording. Positive T−H never reverses a primary loss. Lack of a tuned headroom record remains an interpretive limitation, not a no-value finding. **Every sign ends this single allocation at intake.** No automatic second pair, replacement master, retry, extra H-completion/evaluation, post-result tuning or successor is selected. A/B research has no C-style consumption state; the finite authorization boundary does not become a permanent prohibition on separately justified future research.

## Complete work and honest cost boundary

The unchanged native/optimizer budget is:

| Quantity | Selected complete comparison |
| --- | ---: |
| Learned arms × independent training pairs | 2 × 1 |
| Training episodes / native team steps | 1,024 / 262,144 |
| Rollouts / Adam calls | 512 / 2,048 |
| T/G/H final evaluation episodes / team steps | 96 / 24,576 |
| Total full episodes / native team steps | **1,120 / 286,720** |
| Explicit resets / constructor resets | 1,120 / 2, kept distinct |
| Existing final T/G t0..4 diagnostic rows | 1,600 |
| Caps | **1,800 s per complete arm; 3,600 s through whole publication and exit** |

The dominant native expression remains **2×512×256 + 3×32×256**. H costs a real additional 8,192 native steps and is charged in G's segment. Team steps are not five independent samples. There is no extra environment or recurrent forward step, nested candidate action, trajectory enumeration, policy search, solver, ensemble, checkpoint replay or validation experiment.[^facts][^study]

The duration work, however, is substantially different:

| T duration work | Recorded prospective bounds |
| --- | ---: |
| Owned training renewals | 163,840–655,360 |
| Owned final-evaluation renewals | 10,240–40,960 |
| Head-forward rows, sample + behavior density + four PPO epochs, then final sample + density | **1,003,520–4,014,080** |
| Multiplier relative to B04's named head rows | **64–256** |
| Dense forward multiply-adds at 2,208 per row | **2,215,772,160–8,863,088,640** |

These supplied calculations bound 64–256 renewals per UAV episode; they are not a policy enumeration or prediction of learned durations. Categorical sampling, activations, backward passes and optimizer work are additional. T velocity samples occur only at actual renewals; G's train-plus-final owned velocity samples remain **696,320**. Actual eligibility counts, selected/censored holds and suppression must be reported, not filled with a preferred bound.[^facts]

The per-arm cost law is initialization plus **131,072 native/recurrent steps + 1,024 updates + 8,192 learned-policy evaluation steps + publication**. Add G's 8,192 hover steps and T's renewal-dependent sampling/head/density/backward work. T carries startup/common initialization; G carries hover and final publication under the existing full-chain accounting. No new head-work phase sits outside the cap.

B04's measured **137.6704245 s T**, **139.2941963 s G including hover**, and **277.51 s whole invocation** are same-loop references only. The head multiplier is not a whole-invocation multiplier, and equal native steps are not equal computational cost. Incremental renewal seconds, new aggregate CPU and total engineering effort are unknown. The operation bounds and existing loop make one capped trial a concrete proposal; they do not certify affordability. No speedup, timing guarantee or new cost measurement is asserted.[^facts][^intake]

Keep the proposed **portable remote-first CPU FP32, one-Torch-thread** route and both caps without enlargement. A concrete over-cap projection refuses launch under this allocation; a runtime overrun is retained as an overrun, including late indivisible publication. A cost refusal returns the question and necessary work for reconsideration—it does not trigger a timing pilot, faster substitute host, parallel workaround, cap increase or hidden additional phase. Unknown coefficients alone are not a new mandatory profiling experiment or generic launch gate.[^spec][^agents]

Historical exposure is separate: B04 T/G each ran **131,072 training team steps and 1,024 Adam calls** at lr0.0003, with total relative movement **0.5401094749093319 / 0.5930201245151642**. Its duration-head absolute movement was **0.41481131315231323**. Those past facts do not establish the new event's trainability. The future comparison reports its own counts, parameter-group initial/final norms and displacement; a zero-initial final layer uses meaningful absolute movement and an undefined relative ratio rather than an epsilon-divided “effect.” No minimum favorable head movement is imposed.[^facts]

## Verification, execution boundary and remaining uncertainty

The selected added validation is **one affected-directory focused suite, at most 300 seconds**, and the existing independent review of own-expiry eligibility, behavior/recomputed conditional density, held-row credit, horizon censoring and native-primary output. Reuse unchanged checks. The changed behavior needs heterogeneous expiry cases, all-held rows and terminal truncation to be represented within that focused work; no full renewal-event dump, extra scientific trajectory, separate smoke, warm-up, profiling or replay is selected. Omitting a full event trace relinquishes a full trajectory-by-trajectory mechanism audit, not the trustworthy sampled-return comparison.[^preparation][^spec]

No engineering-scope §4 subsystem is needed. Keep ordinary **2,000 new source-line / 600 runner-line** limits and the stated test budget. The 30% orchestration measure is a review signal, not an automatic refusal or revived general100 application. Do not delete required action/reward/primary coverage or compress code to meet a denominator. A concrete verification-budget or semantic gap is returned with its actual affected dependency, not converted into negative renewal science.[^scope][^spec]

The same DM now has a selected scientific scope and budget to carry into the new card and complete CM specification. The **same CM owns the cohesive implementation, independent review, accepted-source binding, staging, bounded execution, observation, collection and technical-acceptance batch** under the current Root ownership. One actual observer is identified for an accepted handle and reported to Root; no standing observer, new scheduler, per-command relay chain or independent Portfolio session is created. Root integrates, and the DM intakes every outcome. The newer owner resume supersedes dated global-pause sentences; it does not reopen spent B04 work.[^operations][^resume]

Subsequent execution uses exact accepted committed/pushed inputs and fresh **actual-node physical and effective available memory of at least 4 GiB** immediately before scientific work. Stop at the selected counts/caps, failed admission, nonfinite learning or a concrete defect affecting reward, information, density, training, comparison or primary measurement. Preserve executed counts, completed endpoints and failures. A damaged primary cannot support its dependent performance claim; an independently trustworthy narrower fact remains reportable. Missing optional telemetry or a diagnostic does not automatically erase an intact native comparison, nor does partial success authorize the unallocated completion run.[^agents][^spec]

The main uncertainties remain whether renewal learns useful persistence from evolved histories, whether that benefit survives its loss of feedback, whether generic control already captures the opportunity, and whether the added head work fits the cap. No result here resolves them. No stable superiority/harm/equivalence, isolated renewal/conditioning/clipping/entropy causality, pure-information or sensing-fee value, tuned headroom, transfer, deployment or C promotion follows. The older numerical-locus pause and all prior adverse results retain their original meaning.

**This consultation has zero new models, training pairs, environment episodes, native steps, optimizer steps, evaluation episodes, replay calls, profiling calls and scientific invocations.** It forms the scoped recast and selects one future real comparison; it does not implement, accept or run it. No governance file, scientific state, prior response or main-branch file is changed by this delivery.

## Evidence access and provenance

All **15 allowed evidence paths** were accessed through the connected GitHub connector at **5ac3469a85109a82af8c66670865150f320dd85d**. The footnotes identify the actual paths and sections/functions used. Large files were read in question-relevant ranges; no full-history or repository-wide review is claimed. The task was read at its separate fixed task commit; branch/Issue reads concern delivery only. No listed source was unavailable.

No unlisted source, moving-branch scientific input, local clone, external paper, runtime array or historical citation tree was substituted. Recorded statistics, cost arithmetic and literature checks are attributed to the permitted preparation/intake records rather than claimed as repeated analysis. No code, model import, environment initialization, test or experiment was executed.

[^preparation]: [docs/research/candidates/ucope/UCOPE_POST_B04_RENEWAL_P67_PREPARATION_INTAKE_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/5ac3469a85109a82af8c66670865150f320dd85d/docs/research/candidates/ucope/UCOPE_POST_B04_RENEWAL_P67_PREPARATION_INTAKE_20260908.md), §§1–6: owner resume, untested event, source/literature limits, proposal, work and pending direction recommendation.
[^facts]: [docs/research/candidates/ucope/UCOPE_POST_B04_RENEWAL_P67_FACTS_20260908.json](https://github.com/CartmanFatass/My-paper-code/blob/5ac3469a85109a82af8c66670865150f320dd85d/docs/research/candidates/ucope/UCOPE_POST_B04_RENEWAL_P67_FACTS_20260908.json), `recorded_B04`, `source_observation`, `consultation_exposure`, `proposed_renewal_B` and `local_library_query`: accepted observations and supplied prospective work bounds, not new executions.
[^intake]: [docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B04_P61_INTAKE_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/5ac3469a85109a82af8c66670865150f320dd85d/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B04_P61_INTAKE_20260908.md), §§2–6: original WITHIN rule, every sign, native path/exposure, resource limits and exhausted P61; dated pause is historical.
[^card]: [docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B04_SCIENCE_CARD_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/5ac3469a85109a82af8c66670865150f320dd85d/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B04_SCIENCE_CARD_20260908.md), §§2–6: host, opening-only semantics, architecture, RNG, credit, estimator, MEI and caps. Those frozen B04 semantics are not amended by this new object.
[^direction]: [docs/research/candidates/ucope/DIRECTION.md](https://github.com/CartmanFatass/My-paper-code/blob/5ac3469a85109a82af8c66670865150f320dd85d/docs/research/candidates/ucope/DIRECTION.md), Authority, Scientific question and Current scientific position—B04; relevant ranges 1–180. Earlier numerical-locus PARK and actual UAV-entry record remain separate.
[^previous]: [docs/research/candidates/ucope/pro_packets/20260908_post_b03_convergence/archive/RESPONSE.md](https://github.com/CartmanFatass/My-paper-code/blob/5ac3469a85109a82af8c66670865150f320dd85d/docs/research/candidates/ucope/pro_packets/20260908_post_b03_convergence/archive/RESPONSE.md), opening verdict and The selected new scientific object / Question, task and ownership; read lines 1–95. Prior response remains the completed opening-only decision, originally delivered at 475f4452177a98e20fb4c0aedf31a89aee4d8912.
[^environment]: [experiments/candidates/ucope/uav_motion_prefix_b01/environment.py](https://github.com/CartmanFatass/My-paper-code/blob/5ac3469a85109a82af8c66670865150f320dd85d/experiments/candidates/ucope/uav_motion_prefix_b01/environment.py), `make_real`, `actor_features`, `critic_features`, `team_reward` and `HoldState`. Read as source text only; no base-environment invocation or unlisted dependency read.
[^learner]: [experiments/candidates/ucope/uav_motion_prefix_b01/learner.py](https://github.com/CartmanFatass/My-paper-code/blob/5ac3469a85109a82af8c66670865150f320dd85d/experiments/candidates/ucope/uav_motion_prefix_b01/learner.py), `collect_episode`, `returns_to_go`, `clipped_policy_loss`, `recurrent_outputs`, `optimizer_for` and `update`: actual opening mask, primitive recurrence/reward and current PPO path.
[^policy]: [experiments/candidates/ucope/uav_motion_prefix_b01/policy.py](https://github.com/CartmanFatass/My-paper-code/blob/5ac3469a85109a82af8c66670865150f320dd85d/experiments/candidates/ucope/uav_motion_prefix_b01/policy.py), `Actor`, `templates`, `arm_copy`, `sample`, `tanh_log_prob`, `joint_terms` and exposure groups: accepted conditional head, private initialization and stored-action likelihood.
[^study]: [experiments/candidates/ucope/uav_motion_prefix_b01/study.py](https://github.com/CartmanFatass/My-paper-code/blob/5ac3469a85109a82af8c66670865150f320dd85d/experiments/candidates/ucope/uav_motion_prefix_b01/study.py), `Config`, `declared_masters`, `primary_from_rows` and `run_pair`; relevant ranges 1–115 and 190–430. Existing B04 route and loop are not an implemented renewal selector.
[^spec]: [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md](https://github.com/CartmanFatass/My-paper-code/blob/5ac3469a85109a82af8c66670865150f320dd85d/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md), §§4,5.2,11.4,11.7–11.9; relevant ranges 44–113 and 360–600. Claim-proportionate exploration, independence, failure dependency and question/work selection control this decision.
[^scope]: [docs/project/ENGINEERING_SCOPE_SPEC.md](https://github.com/CartmanFatass/My-paper-code/blob/5ac3469a85109a82af8c66670865150f320dd85d/docs/project/ENGINEERING_SCOPE_SPEC.md), §§4–5 and adjoining focused-check language; read lines 36–112. No new prohibited subsystem, automatic ratio gate or exception application is selected.
[^agents]: [AGENTS.md](https://github.com/CartmanFatass/My-paper-code/blob/5ac3469a85109a82af8c66670865150f320dd85d/AGENTS.md), §§1–2 and 4–7, including §2 Investment fields' recast rule; read relevant text within lines 1–447. Root owns Portfolio/execution; scientific and delivery permissions remain distinct.
[^operations]: [docs/project/ROOT_OPERATIONS.md](https://github.com/CartmanFatass/My-paper-code/blob/5ac3469a85109a82af8c66670865150f320dd85d/docs/project/ROOT_OPERATIONS.md), Complete deliverables and their owners, Exact execution inputs and Current records and integration: cohesive CM batch, one observer and Root integration; dated pause wording is superseded only by the owner resume.
[^resume]: [docs/research/portfolio/handoffs/2026-09-08-research-resume.md](https://github.com/CartmanFatass/My-paper-code/blob/5ac3469a85109a82af8c66670865150f320dd85d/docs/research/portfolio/handoffs/2026-09-08-research-resume.md), owner-resume paragraph, P67 UCOPE row and common execution boundary. Other directions in that handoff supply no scientific input to this decision.
