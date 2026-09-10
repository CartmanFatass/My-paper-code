**Continue the tested opening-commitment family through exactly one action-conditioned opening-duration B/EXPLORE comparison, rather than ending it now.** Select the proposed fresh matched pair, master **7201**, with the full two-fit budget below and no automatic second pair. The reason is a specific, presently untested dependency: the duration can be chosen after seeing the actual owned velocity command it will repeat. This is a sufficiently concrete performance question to justify one bounded comparison against ordinary feedback; it is not evidence that the independent duration head was defective or caused any previous loss.

This is a narrow decision. It retains one new UAV package comparison inside the existing fixed-five-UAV, opening-only family. It does not restore an unchanged B02/B03 continuation, select interruption or later options, reopen the older retained-policy/root-residual numerical-locus family, or change Portfolio lifecycle, priority, capacity or formal UAV-entry accounting. The new object is not yet implemented or observed. The existing direction record separates these families and retains the completed UAV-entry chain.[^direction][^entry]

## Why one changed comparison is worth retaining

The next observation needs to decide whether this particular action-conditioned opening package earns native return over the existing legal feedback learner at the same real training budget. It does not need to identify the unique cause of earlier failures. Ending now would save all implementation, review and training work and is a serious alternative. I narrowly prefer the one changed comparison because its new input is already available to its owner at the actual decision, its action and environmental boundaries remain unchanged, and its principal work is the existing two-fit loop rather than a search or diagnostic programme.

### The adverse history is substantive, not a rounding issue

The separate studies retain their original meanings:

| Study and independent training units | Original T−G observations | Evidence that limits the opening-package claim |
| --- | --- | --- |
| P21, two matched pairs | +0.0067140322 and +0.0237208090; equal mean +0.0152174206, **UP** | Both G−H means were positive, but the joint excess over MEI was smaller than its conditional evaluation SE. This is the strongest prior positive support, not stable superiority. |
| P24, two new matched pairs | +0.0433518665 and −0.0503654225; mean −0.0035067780, **WITHIN** | In 6901 G−H was −0.0282038164; in 6902 T−H was −0.0332644846. A positive comparison against a weak G and a materially harmful T outcome coexist. |
| B02, two matched pairs, common agent-compound clipping | −0.04726710442367869 and −0.0061362058126795795; mean −0.026701655118179134, **DOWN** | Both T−H endpoints were negative: −0.022488308354103006 and −0.024392187487712595. G−H changed sign. |
| B03, one matched pair, common explicit entropy coefficient zero | −0.010093085146628955, **DOWN** | Ordinary feedback wins the primary while both fitted learners exceed hover. The point is only 0.0000930851466 below the negative boundary. |

These are accepted-record observations, not recalculations performed by this consultation. The P21, P24, B02 and B03 intakes supply the corresponding original rules and independent-unit limits.[^entry][^p24][^b02][^b03]

B03's T/G/H means are **0.1784473239057538 / 0.18854040905238276 / 0.1409724467347594**. Its conditional paired-episode SE for T−G is **0.008506138301283968**; 17 evaluation differences are positive and 15 negative. T−H is **+0.03747487717099439**, and G−H **+0.04756796231762334**. The strict DOWN reading stays intact, but it cannot be inflated into reliable separation from −0.01 or training-population harm. Thirty-two episodes are not thirty-two trained pairs. Positive hover contrasts do not reverse the primary loss.[^facts][^b03]

The strongest argument for ending is therefore **B02's two native losses, including losses to hover, followed by a B03 loss against a G that demonstrates a positive sampled hover margin**. It is not merely the small B03 threshold crossing. The strongest argument against ending is the earlier actual positive package evidence plus the newly specified owned-command dependency. Neither guarantees that another comparison succeeds. Different objectives and masters are not pooled or treated as causal entropy/clipping experiments; the historical four-pair P21/P24 description is not new confirmation.[^b02][^p24][^preparation]

### What the source establishes, and what it does not

In `policy.py::sample`, each active UAV first samples its velocity latent `u`. At the opening, `actor.duration(recurrent[i])` then ignores that draw. `joint_terms` recomputes the same history-only duration law. Conditional on the recurrent feature, the tested opening distribution factorizes as

\[
\pi(v,d\mid h)=\pi_v(v\mid h)\,\pi_d(d\mid h).
\]

This allows duration to depend on local history, but not on the realized noisy command selected from the velocity distribution. The source fact is direct. Calling it a bug, or diagnosing it as the cause of B02/B03, would exceed the evidence.[^policy]

The preparation intake's verified local-corpus report identifies UTE's state-and-selected-action extension policy as motivation. Its single-agent Q-learning and uncertainty-ensemble evidence is not PPO/MARL/UAV evidence. This consultation uses that recorded source finding, not a new paper retrieval, novelty search or replication. No ensemble or trajectory search is imported.[^preparation]

**My inference:** conditioning duration on the realized command could let the learner assign persistence differently to different commands under the same local state. It might instead learn nothing useful, lose useful exploration, or remain inferior to stepwise feedback. B03's logged latent standard deviation near one makes the distinction nontrivial; it does not identify harmful sampled commands. Because duration is learned only at openings, useful credit is also sparse. Those uncertainties are reasons to limit the investment to one pair, not to replace learning with a prerequisite diagnostic.

The performance observation cannot isolate the effect of conditioning from added head capacity, changed optimization, direct geometry, persistence, later learned feedback or partner co-adaptation. A third learned arm would purchase a stronger attribution question that is not selected here.

## The selected new scientific object

### Question, task and ownership

The question is: **at the existing full training budget, does an opening-duration policy conditioned on its owning UAV's just-sampled command improve complete sampled native team return over the unchanged same-information stepwise recurrent PPO learner?** Evidence class is **B/EXPLORE**. The immediate mechanism is temporal abstraction within a fixed partially observed moving team; the five shared-policy agents retain private recurrent histories and co-adapt within each fit.

Retain the selected base task: five UAVs, 50 users, uniform layout in the 1000 m area, altitude 50–150 m, the existing velocity scaling by 30, one-second primitive steps, free-space channel, no shadowing/FDMA, vectorized backend, existing local observation limits and **default native reward**. Keep the existing **256-step episode**, not a new task horizon or the original longer environment default. These are the accepted family contract as recorded in the interface intake and B03 card; no unlisted environment source was imported or inspected here.[^interface][^card]

At t0 each T UAV owns one sampled normalized command and a duration in {1,4}. A one-step duration permits a new ordinary velocity decision at t1. A four-step duration repeats the t0 command through t3 and releases at t4. Every UAV has returned to ordinary feedback by t4. There is no later duration choice, learned interruption or new stopping clock. Environment motion, channels, observations, recurrence and rewards continue at every primitive step during a hold.[^card][^learner]

The information boundary is unchanged. Each actor receives its own complete 108-component input: the existing local observation and its own command/hold history. The critic keeps its separate 136-component predecision input. Global state, diagnostic identities, other UAVs' sampled commands and future observations do not become actor inputs. The new conditioning input is the actor's own present command, not a new environmental observation or privileged signal.[^interface][^card]

### The precise treatment change

Retain the shared 108→64 encoder, GRU-64, three-dimensional Gaussian velocity head and learned log standard deviation. Replace only T's history-only duration head with **Linear(67,32) → tanh → Linear(32,2)**. Its input concatenates the 64-component recurrent feature with the three components of the actual normalized owned command **`tanh(u)`**. Zero the final layer's weights and biases so the initial duration distribution is uniform for every input. This is a selected prospective architecture, not existing accepted code.[^policy][^preparation]

Common actor/critic parameters are copied from the same initialization for T and G. For completeness, select a private initialization substream **b+12** for the added duration hidden layer, with **b=100000×7201**, using the package's ordinary Linear initialization before zeroing the final layer. This is a prospective initialization detail. It must not perturb the common b+11 initialization or either action-sampling stream. Do not zero both layers or claim an observed new-head displacement.

Sampling remains velocity first, conditional duration second, within the owning UAV. The conditioning value is the sampled normalized command, not its mean, a resampled command, observed displacement after the environment step or a counterfactual candidate. The head is evaluated only on actual opening-duration rows. No new environment or recurrent forward pass is needed for this input.

G remains the existing recurrent PPO learner with no commitment head, full current free local information, and **every legal velocity at every primitive step**, including zero or repetition. It may exploit movement, persistence and observations itself. Its own trajectories, recurrent states and optimizer are separate from T's. This is the strongest legal ordinary-feedback comparison presently specified, not a proof of neural function-class containment or globally competent control. Keep H as the same-reset, zero-velocity **untuned** reference, without training it or replacing G with it.[^policy][^study][^interface]

### True action density, hold masking and native credit

The opening density selected for T is

\[
\log\pi_v(v_i\mid h_i)+\log\pi_d(d_i\mid h_i,v_i).
\]

The velocity term retains the current tanh-transformed Gaussian density and Jacobian. During PPO recomputation, both terms refer to the **stored behavior action**: use the stored detached latent to recover its detached `tanh(u)` condition and the stored duration. Do not draw a fresh action or substitute the current velocity mean. Gradients through the duration head and its recomputed recurrent feature remain legitimate; a reparameterized gradient through a newly generated conditioning command is not this likelihood update.[^policy][^learner]

Retain **agent-compound**, not team-product, clipping. At an actual opening row, the same owner's velocity and duration log densities form one ratio. At a later ordinary decision, only the new velocity contributes. At a held row there is no fresh actor decision and no new velocity or duration credit. Sum eligible agent surrogate terms, then average over all primitive rollout rows, including all-held rows in the denominator. Do not compensate for sparsity by changing normalization or inventing held-action samples. Old log probabilities and normalized scalar advantages remain detached.[^learner][^card]

The selected causal route is therefore:

**t0 local history → owned sampled command → duration conditional on that command → actual held or stepwise physical motion → position/channel/service and subsequent free local observations → private recurrent feedback → complete native team rewards → existing agent-compound PPO learning → final sampled native service return.**

This route includes direct service consequences and partner behavior, not only information acquisition. A larger displacement, a changed local entry, nonuniform durations or a better information proxy is not an alternative endpoint. No sensor fee, intrinsic reward, count channel or assumed positive movement cost is added.

For training retain the complete undiscounted return-to-go

\[
R_t=\sum_{\tau=t}^{255} r_\tau,
\qquad r_t=\sum_i r_{i,t}^{\rm native},
\]

with gamma=1 and no terminal bootstrap. The predecision critic and scalar advantage normalization are unchanged. Retain two complete episodes per rollout, recurrent chunk length 32, four full-rollout epochs, Adam lr **0.0003**, the existing Adam settings, PPO clip **0.2**, value coefficient **0.5**, and global gradient clip **0.5**. Both arms keep **zero explicit entropy coefficient**; Gaussian/categorical sampling and trainable variance remain active. Training on the unnormalized full return-to-go and evaluating the horizon-average J are distinct existing choices, both preserved.[^learner][^card]

## One matched pair, complete primary and all-outcome interpretation

Select **master 7201**, one fresh matched training pair and two genuine fits, not one shared fitted checkpoint. The preparation reports a bounded nonreuse search in current UCOPE records; this is not a global seed-namespace proof. Keep the existing master domains: common initialization b+11, training velocity b+21, training duration b+22, training reset b+1000+e, and final reset/velocity/duration b+2000+e / b+3000+e / b+4000+e. The extra-head initialization uses the isolated substream selected above.[^facts][^study]

Matched initialization and stream definitions do not imply identical on-policy trajectories. In particular, holding changes how many velocity draws T consumes. Preserve the existing stream law rather than silently introducing new draw alignment. Both fitted policies are evaluated stochastically as before, using their final checkpoints only. There is no best-checkpoint, best-seed or duration-rule selection from evaluation.

Each learned arm receives **512 complete 256-step training episodes, 256 two-episode rollouts and 1,024 Adam calls**. After fitting, evaluate **32 complete episodes for each of T, G and H** on matched evaluation reset identities. The primary remains

\[
J_a(e)=\frac{1}{256}\sum_{t=0}^{255}\sum_i r_{a,i,t}(e),
\qquad
\Delta=\frac{1}{32}\sum_{e=0}^{31}[J_T(e)-J_G(e)].
\]

Read the original per-UAV native reward dictionary and sum it; do not substitute the adapter scalar that averages again. Report all 96 J values, all paired signs and differences, the three arm means, and T−G, T−H and G−H. For each paired contrast report `sample_sd(differences)/sqrt(32)` as **conditional evaluation SE**. There is one independent trained pair, so no training-population SD or interval is estimable. Agents, openings, rollout chunks and evaluation episodes do not add independent training units. Historical masters and finite-host results do not enter this primary.[^interface][^card][^study]

**Retain absolute MEI 0.01.** It is a task-scale investment criterion, not a significance level, headroom estimate or guarantee. The existing rationale is one percentage point on the selected native service scale; the coverage component for one continuously served additional user is 0.7/50=0.014. That component calculation does not guarantee a total-reward increment when other consequences change.[^card]

| New pair's complete observation | Reading and next recommendation |
| --- | --- |
| Δ>0.01 | Preliminary favorable package evidence on this task and fit. Consider a separately justified bounded follow-up; do not claim conditioning causality or allocate another pair automatically. |
| −0.01≤Δ≤0.01 | No demonstrated point gain at the selected scale under this budget. Prefer no unchanged continuation of this package; not stable equivalence or proof of absent information value. |
| Δ<−0.01 | Adverse native evidence for this package/task/budget. Drop its unchanged continuation from the next default choice; favorable duration or motion diagnostics do not rescue it. |

Apply the numerical boundaries without rounding and retain the distance to the boundary and conditional uncertainty. A near-boundary result must not become reliable population separation merely because it receives a categorical label. The practical contrary observation is complete native return that fails to earn the chosen margin against G, especially a negative contrast despite G's positive hover margin; that counters the investment prediction on the observed fit, not all possible conditional-duration policies.

G's competence is evaluated rather than assumed from its label. A future weak or negative G−H does not erase a trustworthy T−G measurement, but narrows any claim of improvement over competent generic control. Conversely, positive T−H never overrides a negative T−G. Hover remains untuned and no upper/tuned-generic host headroom record is created. No hover-success or significance prerequisite is added before this B.

**Every outcome ends this single allocation at intake.** Positive output is not an automatic second-pair entitlement; within-band or adverse output is not an automatic whole-family impossibility conclusion. No additional evaluation is allocated to clarify a small threshold crossing. This is outcome-informed exploration motivated by the history, not independent prospective confirmation of a conditioning mechanism.

## Dominant work, exposure and timing limits

I select the proposed full budget without enlargement:

| Work | Per learned arm | Complete selected comparison |
| --- | ---: | ---: |
| Training episodes / native team steps | 512 / 131,072 | 1,024 / 262,144 |
| Two-episode rollouts / Adam calls | 256 / 1,024 | 512 / 2,048 |
| Final evaluation | 32 episodes / 8,192 steps for each fitted policy | T/G/H: 96 episodes / 24,576 steps |
| All full episodes / native team steps | — | 1,120 / **286,720** |
| Explicit resets / constructor resets | — | 1,120 / 2, reported separately |
| Existing opening diagnostic frames | — | 1,600; no extra scientific trajectory |
| Time limits | **1,800 seconds per arm** | **3,600 seconds through full publication and exit** |

The work is `2×512×256 + 3×32×256`, with no candidate-action search, trajectory enumeration, ensemble, replay, headroom census or extra common-learning sweep. Native team steps are not multiplied by five and relabeled as independent samples. H's evaluation is real additional work, not a free baseline.[^facts][^study]

There are only **512 opening team decisions, or 2,560 owned duration samples, in T's training**. These share a fit and do not create a large independent evidence base. Full-episode credit and the unchanged primitive-row denominator may make duration learning difficult; no new exposure threshold or training extension is selected to guarantee its success.

The recorded prospective head arithmetic replaces 130 parameters with 2,242, adding **2,112 relative to the old T**. New T totals **68,553 parameters**; G remains **66,311**. The added capacity belongs to the tested package. The named opening-head forward work is **15,680 rows**: 2,560 sampling, 2,560 stored-density evaluations, 10,240 four-epoch recomputations, and 160+160 final sampling/density rows. At 2,208 dense multiply-adds per row this is **34,621,440 forward multiply-adds** for the new head, not an observed time or the entire learning workload. Backward, activation and Adam work are additional. Do not evaluate the head on every masked primitive row and then call that expansion part of the selected design.[^facts]

The per-arm law remains initialization plus **131,072 environment/actor steps + 1,024 updates + 8,192 final-policy steps + publication**, with G also carrying **8,192 hover steps**. T carries startup/common initialization, and G carries the final hover/publication segment under the existing accounting. The conditional-head initialization, forward, backward and optimizer increments must be accounted for inside those same caps, not charged to a separate unbounded phase.

B03's observed **143.6449222 s T**, **139.3128413 s G including hover**, and **283.51 s whole invocation** are a useful same-loop reference. They are not a measured forecast for the new head. Incremental seconds, aggregate CPU work for the proposed run and total agent/engineering effort remain unknown; multiply-add counts do not determine them. No affordability guarantee or measured speedup is asserted. If a concrete projection or execution breaches the selected cap, return the exact fact and reconsider the question/work rather than raising the cap, parallelizing to obscure total work or adding a pilot automatically.[^facts][^b03]

Retain CPU FP32, one Torch thread and the portable remote-first route, using accepted committed/pushed source for the subsequent detached invocation. Require fresh actual-node physical and effective available memory of at least **4 GiB** immediately before its scientific work. Node identity is not the performance estimand. This response launches nothing and creates no environment, actor, critic or optimizer.[^card][^agents]

Historical learner exposure remains distinct: B03 ran two real fits with 131,072 train steps and 1,024 Adam calls each at lr0.0003, total relative displacement T **0.558120601386** / G **0.538479842605**, and T duration absolute displacement **0.138774350286**. Those measurements establish prior learning, not new-head trainability or sufficient optimization. The future run reports its own actual counts, parameter-group movement, initialization norms and applicable displacement ratios; zero-initialized groups require meaningful absolute movement rather than an epsilon-normalized ratio presented as evidence. Consultation exposure is **zero new models, training pairs, environment episodes, native steps, optimizer steps, evaluation episodes, replay calls, profiling calls and scientific invocations**.[^facts][^b03]

## Verification and the next boundary

Select only the proposed **one affected-directory suite, at most 300 seconds**, and existing independent review of actual-command conditional density, held-action credit and the native primary. Verification should establish the new opening dependency and matching behavior/recomputed probabilities for the same stored action, preserve true masks and common initialization streams, and protect reward/information/primary boundaries. It need not diagnose every historical result or certify optimality. Existing unchanged paths and checks are reused. No separate smoke, profiling, scientific pilot, replay, full-array publication or additional learned arm is selected.[^preparation][^spec]

The named source currently implements the independent head and declares only the existing study masters. It is evidence for a small modification, **not acceptance of that modification**. The prospective card and complete CM specification must carry the selected head, fresh master, current zero-entropy agent-compound objective, full counts and stopping conditions. The existing route then proceeds through the same DM/CM, affected-path review, accepted-source binding, the selected bounded execution and all-outcome intake. It needs no routine second Portfolio implementation vote. The consultation itself does not perform those steps or expand its two authorized delivery writes.[^policy][^study][^route]

Stop at the selected counts/caps, failed actual-node admission, nonfinite learning, or a concrete defect threatening reward, information access, action density, training, comparison or primary measurement. Preserve partial observations, completed endpoints and actual overruns. No retry, replacement master, second pair, extra H-completion run or post-result tuning is allocated. A damaged primary cannot support its dependent comparison; an independently trustworthy narrower observation remains reportable. Missing optional telemetry or information diagnostics limits the corresponding claim rather than automatically erasing an intact native comparison. Preserve the earlier smoke overrun and zero-exposure command failures at their original meanings; this decision does not repair or reclassify them.[^spec][^b02][^card]

This is an ordinary B under evidence-spec §§4,5.2,11.4,11.7–11.9. No exact headroom, universal positive signal, all-positive seeds, causal explanation or search-before-learning is required. Pro is resolving the actual assigned family choice, not creating a generic B launch gate. No engineering-scope §4 machinery is needed. Ordinary 2,000-line source, 600-line runner and applicable test/resource budgets remain; 30% orchestration is a review signal, not a new automatic refusal or a revived general100 application. No specification exception is requested.[^spec][^scope]

**The final decision is one bounded continuation, with ordinary feedback as the primary comparator and complete native return as the deciding observation.** The strongest remaining uncertainty is whether this sparse opening dependency changes useful learned behavior at all, or simply adds capacity while feedback still wins. At intake the allocation ends regardless of sign. No stable superiority/harm, conditioning/entropy/clipping causality, pure-information value, tuned headroom, transfer, C promotion or whole-UCOPE disposition follows.

## Evidence access and provenance

All **17 listed evidence paths** were accessed through the connected GitHub connector at **`f3ac3991ff30a603adc111cead2e3bd38f6783ca`**. The references below name the actual paths and relevant sections/functions read. Large files were read in the question-relevant ranges; this was not a repository-wide review. No listed path was unavailable.

The task itself was read at its separate fixed task commit. Delivery-branch and Issue11 reads are delivery checks, not new scientific evidence. The listed Issue snapshot contains the earlier interface request and delivery, not a post-B03 decision; its old preparation wording does not override the present accepted records.[^snapshot]

No unlisted scientific file, raw runtime array, local clone, moving-branch scientific source or external literature was substituted. No code, statistical recomputation, import, test, experiment or profiling was executed. Literature and prior independent verification are attributed to their accepted preparation/intake records; they are not claimed as repeated work by this node.

[^preparation]: [`docs/research/candidates/ucope/UCOPE_POST_B03_CONVERGENCE_PREPARATION_INTAKE_20260908.md`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/docs/research/candidates/ucope/UCOPE_POST_B03_CONVERGENCE_PREPARATION_INTAKE_20260908.md), §§2–5: separate history, sampled-action dependency, recorded UTE source finding, candidate and work; §6 remains the prior pending recommendation.
[^facts]: [`docs/research/candidates/ucope/UCOPE_POST_B03_CONVERGENCE_FACTS_20260908.json`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/docs/research/candidates/ucope/UCOPE_POST_B03_CONVERGENCE_FACTS_20260908.json), `recorded_B03`, `consultation_exposure`, `proposed_B04`, `no_successor_option` and `local_library_query`. Prospective counts are recorded calculations, not executions.
[^direction]: [`docs/research/candidates/ucope/DIRECTION.md`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/docs/research/candidates/ucope/DIRECTION.md), Authority, Scientific question, Current scientific position—B03 and Prior scientific position—B02; read lines 1–200.
[^b03]: [`docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B03_P57_INTAKE_20260908.md`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B03_P57_INTAKE_20260908.md), §§1–6, especially §§2–3 and 5–6: exact DOWN, conditional uncertainty, native path and exhausted allocation.
[^b02]: [`docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B02_P47_INTAKE_20260908.md`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B02_P47_INTAKE_20260908.md), §§2–3 and preserved resource/stop record in §§4–6; read lines 1–210.
[^p24]: [`docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B01_P24_INTAKE_20260907.md`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B01_P24_INTAKE_20260907.md), §§2–3; read lines 1–132. The four-pair description is historical, not used as this object's primary.
[^entry]: [`docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B01_INTAKE_20260907.md`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B01_INTAKE_20260907.md), §2 and §5's actual-entry chain; relevant movement/credit interpretation in §3; read lines 1–190.
[^interface]: [`docs/research/candidates/ucope/UCOPE_UAV_INTERFACE_CONVERGENCE_INTAKE_20260907.md`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/docs/research/candidates/ucope/UCOPE_UAV_INTERFACE_CONVERGENCE_INTAKE_20260907.md), §1 decision and §§3–4: host, free-information/comparator boundary and native reward sum.
[^card]: [`docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B03_SCIENCE_CARD_20260908.md`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B03_SCIENCE_CARD_20260908.md), §§2–6: preserved host/learning, master domains, primary, MEI and full-chain caps; later result append is historical.
[^policy]: [`experiments/candidates/ucope/uav_motion_prefix_b01/policy.py`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/experiments/candidates/ucope/uav_motion_prefix_b01/policy.py), `Actor`, `templates`, `arm_copy`, `tanh_log_prob`, `sample`, `joint_terms` and exposure helpers; source read as text only.
[^learner]: [`experiments/candidates/ucope/uav_motion_prefix_b01/learner.py`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/experiments/candidates/ucope/uav_motion_prefix_b01/learner.py), `collect_episode`, `returns_to_go`, `clipped_policy_loss`, `recurrent_outputs`, `optimizer_for` and `update`; no invocation.
[^study]: [`experiments/candidates/ucope/uav_motion_prefix_b01/study.py`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/experiments/candidates/ucope/uav_motion_prefix_b01/study.py), `Config`, `declared_masters`, endpoint arithmetic and `run_pair`'s training/evaluation/timing loop; read lines 1–430.
[^route]: [`docs/research/portfolio/handoffs/2026-09-08-p61-ucope-post-b03-direction-choice.md`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/docs/research/portfolio/handoffs/2026-09-08-p61-ucope-post-b03-direction-choice.md), Target/deliverable, Scientific bounds, Return route and Budget/stop.
[^spec]: [`docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md), §§4,5.2,11.4,11.7–11.9; read lines 1–125 and 330–590. These are the current proportional-burden and failure-dependency rules.
[^scope]: [`docs/project/ENGINEERING_SCOPE_SPEC.md`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/docs/project/ENGINEERING_SCOPE_SPEC.md), §§4–5 and immediately preceding focused-check language; read lines 36–125.
[^agents]: [`AGENTS.md`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/AGENTS.md), focused reading, §2 decision ladder, §4 delegation and §§5–7 execution/Git/resource boundaries; read lines 1–185 and 223–450. These do not enlarge this consultation's authorized delivery scope.
[^snapshot]: [`docs/research/candidates/ucope/pro_packets/20260908_post_b03_convergence/archive/ISSUE_INPUT_SNAPSHOT.json`](https://github.com/CartmanFatass/My-paper-code/blob/f3ac3991ff30a603adc111cead2e3bd38f6783ca/docs/research/candidates/ucope/pro_packets/20260908_post_b03_convergence/archive/ISSUE_INPUT_SNAPSHOT.json), earlier Issue11 body and prior interface-delivery comment; discussion provenance only.
