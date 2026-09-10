**Continue the existing own-expiry renewal family with the proposed learned-versus-frozen-duration comparison as its next bounded B/EXPLORE question.** Select the future design with one matched training instance of learned renewal **T**, frozen-initial-head renewal **F**, and ordinary feedback **G**, plus untuned hover **H**. Keep **T−G as the native performance primary** and **T−F as the predeclared secondary discriminator**. I narrowly prefer this to ending the sequence or adding only a fourth unchanged T/G pair: it asks whether learning the duration rule earns anything beyond the stochastic persistence already present at initialization, without replacing the legal feedback comparator.

This is **CONTINUE, not another RECAST**. The own-expiry event, duration set, task, free-information boundary and native performance question remain intact; the added control examines an alternative inside that mechanism. The previously recorded genuine recast count remains **1**, with its stated historical-coverage limitation. The opening-to-renewal RECAST is neither erased nor counted again. The older retained-policy/root-residual family remains paused, and no whole-UCOPE or Portfolio disposition follows.[^direction][^recast][^previous]

The choice below is a scientific design decision, **not a scientific invocation allocation**. It names no new master, creates no card or implementation, and releases no experiment. P74 requires full-response intake followed by a **new concrete Root command** for any subsequent application, implementation or execution. Its explicit restart supersedes the earlier soft stop, but does not replenish P72 or an earlier allowance.[^restart][^assignment]

## What the three renewal observations support

The three accepted comparisons must remain individually visible. Each used one matched training instance and 32 final evaluation episodes per T/G/H. The original native means are:

| Comparison | T | G | H |
| --- | ---: | ---: | ---: |
| P70 / 7301 | 0.18553283836801163 | 0.12985964701917668 | 0.13247830104751704 |
| P71 / 7401 | 0.1848478520611129 | 0.16018967502019155 | 0.14769953379747316 |
| P72 / 7501 | 0.16159104017261458 | 0.19253815079152012 | 0.14048393970863335 |

Their comparisons, with conditional paired-episode SE in parentheses, are:

| Comparison / original reading | T−G | T−H | G−H |
| --- | --- | --- | --- |
| P70 / **UP** | +0.055673191348834944 (0.011556059794903147) | +0.05305453732049459 (0.01182038845858344) | −0.002618654028340355 (0.011943248746505064) |
| P71 / **UP** | +0.024658177040921356 (0.011145715505143731) | +0.03714831826363973 (0.014042694092488053) | +0.012490141222718373 (0.009774298009822923) |
| P72 / **DOWN** | −0.03094711061890552 (0.010056196158593048) | +0.021107100463981232 (0.014144010759846842) | +0.052054211082886756 (0.010175312737684957) |

These are the retained measurements, not statistics recomputed by this consultation. The signed T−G episode counts are **25 positive / 7 negative**, **22 / 10**, and **10 / 22**, respectively. The permitted summaries preserve all native returns and signed vectors; no unfavorable episode, zero hover return or trained instance is discarded.[^p70][^p71][^p72]

**The strongest support for another discriminating question is the two earlier UP comparisons and positive sampled T−H in all three. The strongest contradiction is P72's loss to G while G has the largest sampled hover advantage of these three comparisons.** Its unrounded T−G lies 0.02094711061890552 below −0.01. The original DOWN remains an adverse native observation; positive T−H does not rescue it, and no unique causal diagnosis is needed to retain it.[^intake][^evidence]

The secondary three-instance mean **+0.016461419256950254** and sample SD **0.043888031476388346** remain descriptive. They arose through sequential, outcome-informed B follow-ups, include finite evaluation noise, and are neither a replacement primary nor another UP ruling. The individual cards each have one training instance; more episodes from their fixed policies do not add independent training instances. Three retained endpoints do not establish stable population superiority, harm or equivalence, nor isolate training variance from evaluation noise. The small last-digit differences between differences of arm means and means of episode differences do not replace the cards' original primaries.[^facts][^p72][^evidence]

G is a meaningful legal control, but not a demonstrated tuned optimum. P70's slightly negative G−H limits its competence claim; P71 and especially P72 provide stronger sampled feedback-versus-hover observations without proving general competence. There is still no tuned same-information upper/baseline headroom record. That absence limits the claim, not eligibility to ask the proposed B question.[^preparation][^spec]

Keep the older opening results separate: P21's original UP, P24's WITHIN and harmful 6902 outcome, B02's DOWN with both T−H endpoints negative, B03's near-boundary DOWN, and command-conditioned opening B04's negative WITHIN point. None is pooled into the renewal primary or used as an extra randomized arm. The old numerical-locus pause and earlier finite-host findings retain their own meanings.[^direction][^recast]

## Why this comparison is preferable to the alternatives

**No successor is the strongest economical alternative.** It saves the entire new implementation, review and three-learner study. The adverse third comparison weakens the case for continued investment, and one more matched instance cannot resolve the observed variation. F might also be a poor controller, leaving an uninformative secondary advantage. The recommendation is therefore a close investment choice, not a conclusion that continued work is required by earlier positive results.

The reason to buy the added comparison is specific. All three completed studies compared learned renewal with ordinary feedback; they did not compare it with a velocity policy trained from the outset under an input-independent duration law. Keeping the initial uniform law asks whether the learned-duration package adds useful native performance beyond that simpler persistence package. It can change the next choice between retaining learned timing, considering a simpler controller, or declining further unchanged work. G remains present so that beating a weak F cannot become overall success.

A **fourth unchanged T/G pair** would be cheaper and could modestly refine the performance-variation record. It is not intrinsically forbidden. I do not select it here because it supplies no new comparison of timing learning with simple persistence, and P72 already ended the default unchanged sequence. An earlier positive mean is not a reason to continue until another positive appears. The supplied work is 286,720 native steps and 2,048 Adam calls for that alternative, versus 425,984 steps and 3,072 Adam calls for the selected design.[^preparation][^facts]

A **checkpoint-only freeze or replay** would not substitute for F trained under the frozen law. It would retain a velocity policy learned with a different duration policy and answer a different intervention question. Nor is an exact policy maximum, probability sweep, full support census or exhaustive explanation of the reversal necessary. Those would purchase stronger claims instead of the bounded native comparison being selected. This judgment follows the current proportional-burden specification, not a requirement to prove a mechanism before learning.[^spec]

The extra fitted arm is thus part of the next real learning question, not an audit prerequisite placed before another B. It remains only a package discriminator: freezing changes trainable capacity, gradient/clipping exposure and co-adaptation as well as the duration rule. Even a favorable T−F does not isolate pure timing or information causality.

## Source facts and the proposed frozen control

### What is established directly

In `policy.py::arm_copy`, the conditional duration network is **Linear(67,32) → tanh → Linear(32,2)**. Only the final layer's weights and biases are initialized to zero; the hidden layer has its ordinary private initialization. `sample` uses the owner's current recurrent feature and actual sampled command, and `joint_terms` evaluates duration likelihood only on its duration-mask rows. The current study and CLI implement the existing T/G/H routes, not F or the new three-fit study.[^policy][^study][^runner]

The source therefore supports the following deduction for finite inputs: if **the entire initialized duration head remains frozen**, its two logits stay zero and

\[
q_F(d=1\mid h,u)=q_F(d=4\mid h,u)=\tfrac12.
\]

Changing the velocity actor's recurrent feature cannot alter this output while the final weights and biases stay zero. No model initialization or probability probe was performed to establish this algebraic fact. It is not evidence of F's eventual performance.

### The selected prospective difference

**T** retains the current learned action-conditioned renewal policy. **F** uses the same renewal architecture and initially corresponding duration parameters, but freezes **all 2,242 duration-head parameters permanently**, throughout training and evaluation. Its encoder, GRU, velocity mean, log standard deviation and separate critic remain genuine learners, trained from its own trajectories at the same native-step/update budget. Freezing the whole actor, retaining only a checkpoint-time freeze, or allowing a hidden part of the duration head to update would not be this control.

The uniform law is inherited from initialization. It is not fitted to the observed d4 fractions, chosen from candidate probabilities, or replaced by deterministic four-step repetition. Equal probabilities at each eligible decision do not require an observed sample fraction of exactly one half, identical renewal schedules across arms, or a prescribed occupancy fraction. No outcome-dependent probability adjustment is permitted.

At an F renewal, the compound behavior density retains the velocity term and the fixed categorical factor. In the PPO ratio,

\[
\rho^F_{i,t}
=\exp\!\left[
\big(\log\pi^F_{v,\mathrm{new}}(a_{i,t}\mid h_{i,t})+\log\tfrac12\big)
-\big(\log\pi^F_{v,\mathrm{old}}(a_{i,t}\mid h_{i,t})+\log\tfrac12\big)
\right],
\]

the categorical factor cancels and contributes no gradient. The freeze must prevent duration-parameter updates and duration-path gradients; it must not disable the ordinary recurrent and velocity learning paths. F's intended zero duration-head displacement is not a nonzero-learner failure. Its velocity actor and critic, rather than its fixed timer policy, provide the required real learner exposure.[^policy][^learner]

### What the literature contributes—and does not

The preparation's local-corpus record covers 190 real catalog entries and eight lexical candidates. Its verified UTE passages discuss simple repetition, include Fixed Repeat j=4, and report failures of that baseline in many tested Atari games. This motivates a simple persistence comparison and cautions against presuming its competence. The uniform 1/4-step law here comes from UCOPE initialization, **not** UTE's fixed-four algorithm or an empirical UAV result.[^preparation][^facts]

The inherited ACAC passages support own-completion decisions, while their missing-macro-observation/padding issue is not transplanted: this implementation retains fresh primitive observations and critic rows. No UTE ensemble, counterfactual update, ACAC encoder, attention or GAE is selected. The reported My-lib synthetic fixtures remain excluded, and metadata warnings and prior official-identity provenance remain as recorded. These are attributed preparation findings, not new paper retrieval, comprehensive coverage or a novelty claim by this node.[^literature]

## Event, information and native-credit boundaries

Retain the existing wrapper's **five UAVs, 50 users, uniform 1000 m area, altitude 50–150 m, velocity scale 30, one-second primitive step, 256-step horizon**, free-space channel, vectorized backend, no shadowing/FDMA and default native reward (`paper_reward=False`). The wrapper calls the actual base environment and adapter. The base step updates positions, channel/connection state and native reward, then advances one primitive step. The adapter preserves the per-agent reward dictionary but also returns an averaged scalar. The selected team reward is the **sum of the original dictionary**, not that extra average.[^environment][^base][^adapter]

Actors keep their complete **own 108-component input**, private GRU-64 history, previous command and remaining hold. The critic retains the separate **136-component predecision input** with the existing global state and established commitments. Global diagnostics, other agents' newly selected commands and future observations do not enter actors. Shared weights do not expose another UAV's private history. No new sensor, fee, roster/lifetime change, privileged information or intrinsic reward is introduced.[^basecard][^environment]

For both T and F, each owner's **own expiry** selects a new velocity followed by duration 1 or 4. T conditions duration on private recurrent history and its sampled command; F samples its uniform law. A holding teammate makes neither draw. All five actors continue processing every primitive observation, all recurrent states evolve, and the critic and native reward sequence continue. Execute one common physical step, then decrement timers. There is no simultaneous decision barrier, time jump, interruption, or hidden-state reset at an expiry. G retains every legal velocity choice at every primitive step, including repetition and zero.[^basecard][^learner][^environment]

The proposed path is **own expiry amid ongoing team movement → legal private history and owned velocity → learned or input-independent persistence → actual positions/channels/service and later free observations → masked actor/critic learning and partner co-adaptation → full native team return**. The binding structure remains temporal abstraction/termination under multi-agent partial observability. Geometry and direct service remain possible explanations; changed inputs or duration statistics are not the endpoint.

Preserve horizon censoring. A chosen label d starting at s executes only `min(d,256−s)` steps. Retain the likelihood of the selected label even when a d4 is administratively truncated. There is no step or decision at t256, bootstrap beyond the horizon, extra reward or cross-reset carryover. Counts distinguish selected d4, actual suppressed decisions and horizon-censored holds. A late d4 is not automatically three suppressed actions; only executed held steps count. No full renewal-event dump is required.[^basecard][^learner]

For T, retain one owner-compound log density `log pi_v(a|h) + log pi_d(d|h,a)` at true renewals, with the transformed-Gaussian Jacobian and duration condition derived from **the stored detached latent's tanh**. Behavior and recomputed likelihoods use the same action and mask, not a new draw, current velocity mean or later displacement. Recomputed recurrent/head gradients remain valid for T. F replaces only the learned categorical factor by the fixed law described above. Held rows have no new actor sample or likelihood; memory and later recurrent credit still continue.[^policy][^learner]

All three learners keep the current **agent-compound PPO**: sum eligible owner surrogates, then average all primitive rollout rows, including all-held rows. Do not divide by active decisions, divide by five, add sparsity compensation, or introduce a new decision-time discount clock. Keep detached old densities and normalized scalar advantages, predecision critic rows, full native undiscounted return-to-go `R_t=sum_{tau=t}^{255} r_tau`, gamma=1 and no terminal bootstrap. Intermediate held-step rewards remain in that return.

Retain two complete episodes per rollout, recurrent chunk length 32 with stored detached chunk-start states, four full-rollout epochs, Adam lr **0.0003**, betas (.9,.999), epsilon 1e-8, zero weight decay and the existing non-fused/non-foreach settings; PPO clip **0.2**, value coefficient **0.5**, global gradient clip **0.5**, and **zero explicit entropy coefficient**. Stochastic sampling and learned velocity variance remain active. This preserves the existing implemented recurrent PPO approximation, not an exact-gradient or isolated-credit claim.[^basecard][^learner]

Common actor/critic initialization and matched reset-panel laws are retained, with separate fitted parameters, histories, optimizers and random-generator objects. The actual source creates private T/G generators with the declared matching seed domains; this does not mean independent numeric seeds or identical action-draw consumption once holds differ. Do not introduce shared action arrays, copied trajectories or new per-step draw alignment. F requires its **distinct action-stream domains**, while preserving the common initialization/reset pairing. The later authorized card must bind those domains and a fresh master before output. **No new master value or numeric stream assignment is selected here.**[^study][^preparation]

## Primary, secondary and the finite reading

For the later single matched instance, train each T/F/G actor-critic from the start for **512 complete 256-step episodes**, then evaluate only its final checkpoint stochastically on **32 whole episodes**. H is the unchanged zero-velocity policy on the same final reset panel, without training or tuning. H's evaluation is real work and is not a trained replicate.

Define

\[
J_a(e)=\frac1{256}\sum_{t=0}^{255}\sum_i r^{\mathrm{native}}_{a,i,t}(e),
\qquad
\Delta_G=\frac1{32}\sum_e[J_T(e)-J_G(e)],
\qquad
\Delta_F=\frac1{32}\sum_e[J_T(e)-J_F(e)].
\]

**Delta_G is primary. Delta_F is secondary.** Preserve all **128 native returns**, arm means, signed paired vectors and T−G, T−F, T−H, G−H and F−H. For each contrast, report `sample_sd(paired_episode_differences)/sqrt(32)` as conditional evaluation SE. One matched instance with three fitted arms is not three independent treatment-effect replicates. It supplies no training-population SD or interval. Historical masters and frozen-head initialization probabilities estimated from old data do not enter this comparison.[^facts][^card]

Retain **absolute MEI 0.01** for the primary and use the same native scale to describe the secondary difference. This is an investment scale, not a significance level, headroom estimate or equivalence margin established by a statistical test. The inherited coverage component `0.7/50=0.014` provides scale context, not a guaranteed total-reward gain.[^card]

| Complete primary | B-level reading and next recommendation |
| --- | --- |
| Delta_G > +0.01 | Preliminary favorable learned-renewal package evidence for this fit/task/budget. Use the secondary to decide whether further interest is specifically in learned timing or in persistence more generally; no automatic follow-up. |
| −0.01 ≤ Delta_G ≤ +0.01 | No demonstrated point gain at the selected scale. Prefer no unchanged extension on this observation; not stable equivalence or proof of absent value. |
| Delta_G < −0.01 | Adverse learned-renewal package evidence against legal feedback. Do not rescue it with a favorable T−F, T−H, motion statistic or duration count. |

The secondary sharpens the question without replacing it. **Delta_F > +0.01** favors the learned package over this particular frozen-initial-law package on the observed fit; **within ±0.01** shows no demonstrated secondary point residual at that scale, not equivalence; **below −0.01** favors the simpler frozen-law package relative to T. A favorable primary with no material secondary residual gives no observed reason to credit duration learning specifically. A favorable secondary with an adverse primary remains only a secondary advantage against F, not overall native improvement. If both contrasts are favorable, the bounded package evidence is stronger, but freezing-related capacity, optimization and co-adaptation differences still prevent isolated timing or information causality.

G's and F's hover comparisons qualify their observed competence; neither is presumed successful before training. A weak control narrows dependent wording without erasing a trustworthy difference. All opposing episodes and any proximity to the unrounded MEI boundaries remain visible. The question does not require statistical significance, every sign positive, tuned headroom or a complete mechanism explanation.[^spec]

**Every outcome of any later allocation implementing this design ends at all-outcome intake.** There is no automatic second instance, replacement master, retry, additional H/evaluation, tuning sweep or successor. One favorable secondary cannot extend the allocation, and one adverse comparison does not by itself close UCOPE. A/B has no C-style consumption state; this is a bounded future authorization design, not a permanent prohibition on separately justified research.

## Work and cost: the added learner is not free

Adopt the proposed envelope for a later card, without allocating it now:

| Algorithm work | Future design envelope |
| --- | ---: |
| Independent matched training instances | 1 |
| Fitted actor/critic arms | 3: T, F, G |
| Training episodes / native steps per fitted arm | 512 / 131,072 |
| Two-episode rollouts / Adam calls per fitted arm | 256 / 1,024 |
| Total rollouts / Adam calls | 768 / **3,072** |
| Final evaluations | 32 each T/F/G/H; **128** total |
| Full explicit episodes/resets | **1,664** |
| Total native steps | **425,984** |
| Complete-arm / complete-study limits | **1,800 s / 3,600 s** |

The native expression is **3×512×256 + 4×32×256**. Relative to an unchanged pair, this is **1.5× training**, **4/3× evaluation**, and **1.4857142857142858× native steps**, before differences in head-backward work. The zero-successor alternative costs no new scientific work. These are supplied configuration calculations, not executions or timing forecasts.[^facts]

T and F each retain 68,553 total parameters and G 66,311: **203,417 total**, **201,175 trainable**, and **2,242 intentionally frozen**. There are three real actor-critic learners, not an extra untrained entire policy presented as a trained comparator. Actual parameter-group norms and displacement would distinguish F's permanent freeze from T's learned head and from the three evolving actor/critic packages.

For each renewal head, the supplied forward-route bound is

`6 × training own expiries + 2 × final own expiries`,

or **1,003,520–4,014,080 rows**. Both heads together give **2,007,040–8,028,160 rows**, corresponding to **4,431,544,320–17,726,177,280 dense forward multiply-adds** on the recorded route. F can reuse that forward route but receives no head update. Activation, categorical sampling, environment/recurrent computation, backward and Adam work must be distinguished; the fixed head's absence of updates does not make its controller or simulation free. These are bounds over actual possible expiry counts, not policy enumeration, and are not whole-wall multipliers.[^facts]

There is no candidate-action or trajectory search, ensemble, nested controller evaluation, probability tuning, best-checkpoint selection, cost pilot or scientific validation invocation. The extra learning and final evaluation of F—not an exact diagnostic—is the additional algorithm work being considered.

Measured references remain separated by their actual boundaries:

| Accepted renewal comparison | T arm wall, s | G arm wall including H, s | Whole invocation wall, s |
| --- | ---: | ---: | ---: |
| P70 | 160.45789840299403 | 135.36679288500454 | 304.85 |
| P71 | 158.1893359690439 | 138.41656891599996 | 306.04 |
| P72 | 204.3931929190294 | 172.94761272502365 | 390.73 |

The three complete invocation walls sum to **1,001.62 s**, or **333.8733333333334 s per valid matched comparison** in that recorded three-result window. Each such result included two learner fits; the denominator is not an individual actor-critic fit. Engineering, older opening regimes, aggregate CPU and session-wide elapsed time are excluded. The slower P72 timing is not assigned to an unmeasured mechanism.[^p70][^p71][^p72]

For each future fitted arm, retain the cost law **initialization + 131,072 native/recurrent training steps + 1,024 updates + 8,192 final-policy steps + publication**, with the head-dependent work for T/F and **8,192 additional H steps charged in G's segment**. Common startup and final publication are inside the full study accounting. The entire three-arm study must fit **3,600 s through publication and exit**; three separate 1,800-second allowances do not create a 5,400-second study budget. There is no new unbounded F phase.

**F's runtime and the changed backward cost are unmeasured.** The existing timings make the comparison concrete, not guaranteed affordable. A concrete over-cap projection or execution overrun returns the necessary question/work for reconsideration. It does not authorize a pilot, higher cap, faster replacement host, native rewrite or hidden preceding A. Unknown coefficients alone do not require a new profiling experiment.[^facts][^spec]

The later execution boundary remains remote-first **CPU FP32, one Torch thread**, exact accepted committed inputs and fresh actual-node physical and effective memory admission of at least **4 GiB**. No admission, model creation or scientific invocation is performed for this consultation. Optional unmeasured aggregate CPU/resource quantities limit their corresponding claims rather than erasing an intact native comparison.[^agents][^operations]

## Verification and the next authorized boundary

The subsequent bounded engineering work needs one affected semantic/primary-output suite within the existing **300 s** allowance, with independent review of the high-impact freeze and action-credit change. Reuse unchanged checks. The relevant observation is that the entire F duration head remains fixed and uniform while its velocity actor/critic train; stored-action densities, own-expiry masks, horizon censoring, native reward scale and all declared primary/secondary outputs remain correct. No full event dump, repeated launch-boundary smoke, checkpoint-only scientific replay, profiler or new validation service is necessary.[^scope][^spec]

The current source supports a precise modification, not an already accepted F implementation. Its T/G/H loop and output assembly cannot simply be described as the completed three-fit comparison. A later concrete command must carry the selected treatment/comparator meaning, fresh binding, complete cost envelope and proportionate acceptance into the existing DM/CM route. It must preserve old selectors, cards and result meanings rather than rewriting B03 into this new comparison.[^study][^runner]

Stop any later allocated attempt at its actual counts/caps, failed admission, nonfinite learning, or a concrete reward, information, action-density, training, comparison or primary defect. Preserve executed counts, partial outcomes and independently trustworthy narrower facts; a damaged comparison cannot support its dependent claim. Missing optional diagnostics do not automatically annul an intact native result. Partial delivery or technical failure supplies no implicit retry or completion run.[^spec][^agents]

No engineering-scope §4 machinery or specification exception is selected. The ordinary **2,000-source-line / 600-runner-line** and focused-test limits remain. Thirty percent orchestration is a review signal, not a new automatic failure or revived general100 application. The scientific choice adds no approval system or generic Pro-before-B gate.[^scope][^spec]

Root receives this complete decision for the existing intake; the original DM retains scientific ownership. **Implementation and execution await Root's subsequent concrete bounded command**, as P74 explicitly requires. The current request does not restore an old execution route, select a numeric master, create a card, or contact another Portfolio session. The existing recast account remains one; adding this comparator does not change the accepted expiry event or establish a second recast. No lifecycle, priority, capacity, formal UAV-entry or C-promotion action is made.[^assignment][^recast][^agents]

The remaining uncertainty is substantive: whether the native value lies in learning duration rather than merely allowing persistence, whether either renewal package can beat useful ordinary feedback on the next fit, and whether any such difference is repeatable. This one comparison can supply a bounded new observation; it cannot resolve stable performance or isolated causality. **The selected next question is the T/F/G/H comparison, not an unchanged fourth pair, and not a diagnosis that must succeed before another experiment.**

## Actual access and exposure

All **28 listed evidence paths** were accessed at **3828ed463d5899ac374929a5119c909ebb6e20a7** through the connected GitHub connector. The footnotes identify each path and the sections/functions actually used. Large documents were read in relevant ranges, not as a repository-wide or lifetime-history audit. One read of the renewal B03 card encountered a transient server disconnect; the identical fixed-path read succeeded on retry. No required evidence path remains unavailable.

The fixed TASK was read at its separate task commit. Branch and Issue reads are delivery checks, not moving scientific inputs. The pinned Issue snapshot contains the three previous deliveries and older preparation wording; it is not a decision on this round. No unlisted source, external paper, local clone or runtime checkpoint was substituted.[^discussion][^collaboration]

Consultation exposure is **zero new models, environment steps, Adam calls, evaluation episodes, diagnostic/replay calls, selected masters and scientific invocation allocation**. Historical exposure is the three accepted matched renewal comparisons: **860,160 native steps, 6,144 Adam calls and 288 final evaluations**. Their real parameter/head movement establishes learning, not useful timing; for example P72's duration-head displacement is 1.044926404953003 alongside its adverse primary. No training, source import, model/environment initialization, statistical recomputation, test, profiling or paper retrieval was executed here. Recorded calculations and previous verification are attributed to their supplied sources, not claimed as repeated work.[^facts][^p72]

[^preparation]: [docs/research/candidates/ucope/UCOPE_POST_RENEWAL_B03_P74_PREPARATION_INTAKE_20260909.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/candidates/ucope/UCOPE_POST_RENEWAL_B03_P74_PREPARATION_INTAKE_20260909.md), §§1–5, especially §§2–4: separate observations, source deduction, literature limits, alternatives and proposed work. Read lines 1–240; its recommendation was not a prior direction verdict.
[^facts]: [docs/research/candidates/ucope/UCOPE_POST_RENEWAL_B03_P74_FACTS_20260909.json](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/candidates/ucope/UCOPE_POST_RENEWAL_B03_P74_FACTS_20260909.json), full file: independent_fit_results, three_fit_secondary, measured_regime_costs, prospective alternatives, source reading, local literature and zero exposure.
[^restart]: [docs/research/candidates/ucope/UCOPE_RESTART_HANDOFF_20260909.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/candidates/ucope/UCOPE_RESTART_HANDOFF_20260909.md), Current result and claim boundary; Consumed budget and held next step. Its soft-stop wording is historical after the explicit P74 restart.
[^intake]: [docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B03_P72_INTAKE_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B03_P72_INTAKE_20260908.md), §§8–11 read completely; earlier technical portions inspected without repeating their checks. Original DOWN, independent unit, preserved signs and exhausted allocation.
[^evidence]: [docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B03_P72_RESULT_EVIDENCE_20260909.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B03_P72_RESULT_EVIDENCE_20260909.md), E0.1–E0.6: original rule, primary integrity, all contrasts, actual counts/resources and interpretation.
[^p70]: [docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B01_P70_RESULT_SUMMARY_20260908.json](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B01_P70_RESULT_SUMMARY_20260908.json), lines 1–540: native arrays, contrasts, prediction record, counts, exposure and resource measurements.
[^p71]: [docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B02_P71_RESULT_SUMMARY_20260908.json](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B02_P71_RESULT_SUMMARY_20260908.json), lines 1–555: native arrays, contrasts, prediction record, phase counts, exposure and costs.
[^p72]: [docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B03_P72_RESULT_SUMMARY_20260909.json](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B03_P72_RESULT_SUMMARY_20260909.json), full file: all native returns and contrasts, secondary description, predictions, counts/exposure, configuration and actual resources.
[^card]: [docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B03_SCIENCE_CARD_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B03_SCIENCE_CARD_20260908.md), §§1–7, especially §§3–5: original one-instance budget, private stream/reset law, native primary, MEI and original all-outcome reading.
[^basecard]: [docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B01_SCIENCE_CARD_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/candidates/ucope/UCOPE_UAV_RENEWAL_COMMITMENT_B01_SCIENCE_CARD_20260908.md), §§2–3, read lines 20–133: fixed host, owner eligibility, primitive observations, horizon censoring, conditional density and learning settings.
[^direction]: [docs/research/candidates/ucope/DIRECTION.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/candidates/ucope/DIRECTION.md), Authority, Scientific question and current renewal position, lines 1–180. Earlier families and original outcomes remain distinct.
[^recast]: [docs/research/candidates/ucope/UCOPE_POST_B04_RENEWAL_CONVERGENCE_INTAKE_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/candidates/ucope/UCOPE_POST_B04_RENEWAL_CONVERGENCE_INTAKE_20260908.md), §§1–3 and §4 Recast account; lines 1–130 and 145–180. The maintained account records one genuine recast with limited historical coverage.
[^previous]: [docs/research/candidates/ucope/pro_packets/20260908_post_b04_renewal_convergence/archive/RESPONSE.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/candidates/ucope/pro_packets/20260908_post_b04_renewal_convergence/archive/RESPONSE.md), opening verdict and Why this is a recast, lines 1–30. This prior decision changed the event boundary; its completed allowance is not reused here.
[^literature]: [docs/research/candidates/ucope/UCOPE_POST_B04_RENEWAL_P67_PREPARATION_INTAKE_20260908.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/candidates/ucope/UCOPE_POST_B04_RENEWAL_P67_PREPARATION_INTAKE_20260908.md), §3, lines 100–145: inherited UTE/ACAC passages, primitive-observation distinction and metadata/coverage limits; not new paper verification.
[^policy]: [experiments/candidates/ucope/uav_motion_prefix_b01/policy.py](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/experiments/candidates/ucope/uav_motion_prefix_b01/policy.py), Actor, templates, arm_copy, sample, joint_terms and exposure groups; full text read, no execution.
[^learner]: [experiments/candidates/ucope/uav_motion_prefix_b01/learner.py](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/experiments/candidates/ucope/uav_motion_prefix_b01/learner.py), collect_episode, returns_to_go, clipped_policy_loss, recurrent_outputs, optimizer_for and update; full text read as scientific evidence.
[^environment]: [experiments/candidates/ucope/uav_motion_prefix_b01/environment.py](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/experiments/candidates/ucope/uav_motion_prefix_b01/environment.py), make_real, actor_features, critic_features, team_reward and HoldState; lines 1–90.
[^study]: [experiments/candidates/ucope/uav_motion_prefix_b01/study.py](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/experiments/candidates/ucope/uav_motion_prefix_b01/study.py), Config, declared_masters, primary_from_rows and run_pair; lines 1–150 and 210–470. Existing private generator/reset domains, counts, two-fit loop and publication boundary.
[^runner]: [scripts/run_ucope_uav_motion_prefix_b01.py](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/scripts/run_ucope_uav_motion_prefix_b01.py), complete 54-line CLI and invocation mapping; read only, not a launch command.
[^base]: [envs/pettingzoo/uav_env.py](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/envs/pettingzoo/uav_env.py), constructor/action dimensions and reset/step/state, lines 1–200 and 210–395: velocity scaling, one primitive step and per-UAV reward division. No uninspected subclass or whole-environment verification is claimed.
[^adapter]: [envs/pettingzoo/env_adapter.py](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/envs/pettingzoo/env_adapter.py), ParallelToArrayAdapter constructor/reset/step, lines 1–320: observations, state/next_state, original rewards_dict and additional scalar average.
[^spec]: [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md), §§4,5.2,11.4,11.7–11.9; lines 55–117 and 369–610. Question-proportionate exploration, independence, work, verification and failure dependency.
[^scope]: [docs/project/ENGINEERING_SCOPE_SPEC.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/project/ENGINEERING_SCOPE_SPEC.md), §§4–5, lines 45–115: ordinary source/runner/test limits and prohibited unrequested machinery.
[^agents]: [AGENTS.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/AGENTS.md), §§1–2 and 4–7, read within lines 1–433: Root/DM authority, recast rule, bounded delegation, shared branch and resource requirements.
[^operations]: [docs/project/ROOT_OPERATIONS.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/project/ROOT_OPERATIONS.md), Complete deliverables and their owners, Exact execution inputs and Current records. These roles do not expand P74's question-only allocation.
[^assignment]: [docs/research/portfolio/handoffs/2026-09-09-research-resume-p74.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/portfolio/handoffs/2026-09-09-research-resume-p74.md), owner restart, UCOPE row and common return boundary: preparation/full-response intake now, subsequent implementation/invocation by a new concrete Root command. Other directions supply no scientific input here.
[^collaboration]: [docs/project/GITHUB_RESEARCH_COLLABORATION.md](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/project/GITHUB_RESEARCH_COLLABORATION.md), Task and delivery scope, Normal sequence and Partial success and uncertainty: only the scoped new response/comment, with fresh actual-state verification.
[^discussion]: [docs/research/candidates/ucope/pro_packets/20260909_post_renewal_b03_convergence/ISSUE_DISCUSSION_SNAPSHOT.json](https://github.com/CartmanFatass/My-paper-code/blob/3828ed463d5899ac374929a5119c909ebb6e20a7/docs/research/candidates/ucope/pro_packets/20260909_post_renewal_b03_convergence/ISSUE_DISCUSSION_SNAPSHOT.json), full fixed pre-P74 discussion snapshot; historical delivery provenance only.
