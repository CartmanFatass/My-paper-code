# Independent scientific review request: dynamic-roster UAV robustness and paper thesis

## Review authority and operating boundary

You are acting as an independent senior academic reviewer for a multi-agent reinforcement learning and UAV-systems research program. The user explicitly requests a critical scientific review, not encouragement or implementation assistance.

This is a design-and-evidence review only:

- Do not run experiments, write code, modify repositories, or infer that an unperformed UAV experiment succeeded.
- Do not reinterpret a mechanical runtime result beyond the stated registered conclusion.
- Distinguish clearly among: demonstrated result, technically validated mechanism, plausible hypothesis, proposed experiment, and unsupported claim.
- You may recommend rejection, narrowing, redesign, or a different paper thesis if the evidence warrants it.
- Use current primary academic literature for novelty positioning. Give direct paper links or DOIs, distinguish peer-reviewed work from preprints, and do not invent citations.
- Respond primarily in Chinese. Keep equations, method names, branch tokens, and standard academic terminology in English where useful.

## Decision to be reviewed

The original research narrative is:

> Develop a roster-native multi-agent controller for UAV teams whose number and membership can change during an episode because of planned charging or maintenance rotation, unexpected temporary or permanent failure, replacement, and rejoin. The controller should preserve mission service without retraining for every team size or relying on fixed identity slots, and should provide a systematic, falsifiable robustness story rather than only average performance on one benchmark.

The user wants to know whether the present algorithmic evidence can credibly grow into a publishable paper around that narrative, what the narrowest defensible thesis should be, and exactly which experiments are necessary to support it.

This is not a request to rubber-stamp the phrase “system robustness.” Determine whether that phrase is scientifically justified, how it must be operationalized, and what claim ceiling should remain if only simulation evidence is obtained.

## Intended problem setting

The target setting is decentralized execution by a UAV team with within-episode membership changes. Candidate event families include:

1. Planned charging or maintenance rotation: one or more UAVs leave service predictably, later return, and other UAVs must maintain coverage or service.
2. Unexpected temporary failure: abrupt dropout followed by recovery or rejoin.
3. Permanent failure or replacement: an agent disappears and may be replaced by a newly initialized member.
4. Count shock: multiple departures or arrivals over a short interval.
5. Repeated leave/rejoin: the controller must not confuse stale state, identity, or ownership across lifecycle changes.
6. Held-out roster processes: test event timing, order, duration, severity, and team sizes not seen during training.

The desired semantics are stronger than changing a fixed value of N between episodes. Membership changes must occur during the same episode and must exercise anonymous membership, active masks, join/leave/rejoin transitions, state ownership, and continuity of surviving agents. Fixed identity slots must not be the sole carrier of cooperation.

The intended operational objective is continued mission service under registered roster perturbations. Candidate UAV tasks may involve communication coverage, service allocation, sensing, relay, or demand response, but the reviewer should specify the smallest physically credible and scientifically identifiable task instead of assuming that every UAV narrative is suitable.

## Current algorithmic idea

The current candidate family is a shared, roster-native, continuous-action policy developed in a toy dynamic-roster environment under centralized training and decentralized execution semantics.

The retained actor is intentionally small:

- native six-coordinate current-state actor;
- shared parameters across agents;
- active-set and autoregressive-prefix context;
- no learned actor hidden-state carry in the accepted boundary;
- no actor reads of lifecycle age, previous action, or actor time;
- no fixed per-agent identity slot as the sole coordination mechanism;
- member-owned action-noise streams and explicit source/lifecycle ledgers;
- deterministic paired evaluation under fixed and bounded-random roster processes.

The current working hypothesis is that roster semantics, current observable state, active-set aggregation, and state ownership may be more load-bearing than a complicated credit-assignment apparatus. A sequence of matched formal reductions therefore removed unnecessary training machinery while preserving the registered toy-domain access contract.

The intended computational class remains scalable: deployment should target approximately O(N k_neighbor) or O(N log N), not rely on dense pairwise O(N^2) operations as the final general claim. A small exact O(N^2) simulator may still be used as a reference implementation.

## Registered toy-domain evidence before the recent reductions

The research program has already established the following narrow results in registered toy families:

- A discrete dynamic-roster recurrent-policy chain exercised high-frequency churn, several count ranges, random roster processes, atomic replacement, count shock, and fresh seeds. It did not establish UAV applicability.
- A continuous-service dynamic-roster controller demonstrated usable control with membership lifecycle state, active-set aggregation, and a direct demand path. It did not establish physical UAV transport.
- A G31 delayed-credit route retained immediate-task access and delayed spike/rotation/stability gates in paired toy sources. It did not establish general delayed-credit superiority or UAV transport.
- The G31/G32/G34/G35/G39 chain produced the current native-six current-state controller in a registered H=48 toy family. Training at capacity 8 transferred to fixed and bounded-random roster processes evaluated at capacities 6, 8, and 12. The actor did not need learned carry, age, previous action, actor time, donor/filler columns, or constant over-parameterization inside those frozen boundaries.
- These results do not establish arbitrary team size, arbitrary process law, horizon other than 48, general memorylessness, or UAV-system robustness.

The principal formal evaluation class used three initialization replicates, paired episode identities and action noise, capacities 6/8/12, fixed/random and deterministic/stochastic cells, 48 episodes per formal cell, final-only checkpoints, and paired hierarchical whole-episode bootstrap confidence intervals. Equality and first-match gates were predeclared rather than chosen after observing outcomes.

## Recent mechanism-reduction evidence

The following results are registered only for the exact toy-domain and post-anchor boundaries stated here:

### G46: baseline-derived scalar credit-norm schedule

- Formal branch: `RAW_NO_BASELINE_SHADOW_NORM_SUFFICIENT_G46`.
- Both the shadow-norm reference and literal raw-norm arm passed access.
- The primary shadow-minus-raw CI95 was approximately `[-0.000423, 0.002109, 0.006698]`, with all registered capacity contrasts within the 0.05 noninferiority margin.
- Narrow implication: the baseline-derived scalar credit-norm schedule was not load-bearing in that exact post-anchor actor-credit path.
- Not established: structural baseline deletion, UAV robustness, or general credit equivalence.

### G47: shadow baseline-module deletion

- Registered branch: `SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G47`.
- A static graph/optimizer factorization certificate and one proof-sized shared 8x48 trajectory showed `D_G47=0`, including actor/log_std, Adam, action/log-probability, reward/roster/lifecycle trace, and canonical retained-checkpoint equality.
- Narrow implication: the matched shadow baseline module could be structurally removed from that accepted raw-norm route.
- This was exact functional evidence, not a new statistical UAV result.

### G48: realized-successor channel attribution

- Formal branch: `DUPLICATED_IMMEDIATE_CREDIT_SUFFICIENT_G48`.
- Both arms passed access; the primary reference-minus-null CI95 was approximately `[-0.009930, -0.003130, 0.000650]`.
- The realized-successor channel did not show a material registered advantage over a duplicated-immediate comparator in the frozen post-G47 route.
- Narrow implication: the complete realized-successor package was not required for the registered toy-domain access result.

### G49: duplicate immediate-channel collapse

- Registered branch: `DUPLICATED_IMMEDIATE_SINGLE_CHANNEL_EXACTLY_COLLAPSIBLE_G49`.
- Static and proof-sized numerical evidence established exact collapse with `D_SC=0` for the canonical actor/log_std/Adam/action/log-probability/final-checkpoint projection.
- Narrow implication: the duplicate equal-mean immediate package collapsed exactly to one normalized immediate channel in the frozen route.

### G50: common-fast-anchor attribution

- G50 asks whether the historical G40 common-fast-anchor training phase is still load-bearing before the common G49 single-immediate phase-B route.
- The result-bearing implementation has undergone code-science correction work, but no G50 nonformal or formal scientific result is supplied to this review.
- Do not assume whether fresh single-immediate training or the historical fast anchor wins. Treat anchor necessity as unresolved.

Taken together, G46–G49 support a much smaller post-anchor actor-credit route in the registered toy environment: no baseline module and one normalized immediate channel. They do not themselves demonstrate UAV transfer or generic robustness.

## Existing UAV evidence and the central gap

Two earlier UAV-oriented sources did not reach learned-policy comparison:

1. `UAV temporary service loss G1`: the constructive controller did not cross the absolute feasibility gate and was worse than a no-reallocation comparator. The workflow closed before learned training.
2. `UAV charge rotation G2`: proactive rotation was behaviorally load-bearing relative to no rotation, but the constructive controller still remained far below the absolute feasibility floor. Learned training did not begin.

Therefore those studies do not reject the algorithm family, but they provide no positive UAV transport evidence. At present there is no active, source-identifiable UAV task proving that the target service level is physically reachable and that roster adaptation is the causal requirement.

The current open scientific question is whether the native-six roster controller—and its simplified G49 route—transports to a physically feasible UAV source involving planned rotations and unexpected failures.

## Research needs

The user wants a paper-level program, not another long chain of toy-only ablations. The review should determine the minimum credible evidence for each of the following:

- source identifiability and physical feasibility before learned training;
- genuine within-episode membership change rather than episode-level N variation;
- planned rotation, abrupt failure, count shock, and rejoin;
- generalization to held-out roster laws, severities, timings, and team sizes;
- absolute mission access and tail-risk robustness, not only mean return;
- comparison with strong variable-agent and robustness baselines;
- separation of representation effects, training curriculum effects, and increased parameter or optimizer exposure;
- computational scalability and real-time feasibility;
- reproducible paired statistical inference and predeclared failure conditions;
- a defensible claim ceiling for simulation-only, hardware-in-the-loop, and real-fleet evidence.

Do not assume that every item above must appear in one paper. Identify the smallest coherent publishable package and then describe optional evidence that would materially strengthen it.

## Candidate hypotheses to audit, not accept automatically

### H1 — roster-native transport

A shared active-set policy with explicit membership/state-ownership semantics can retain absolute service access under within-episode join/leave/rejoin processes and under team sizes or event schedules not seen in training.

### H2 — unified planned and unplanned roster handling

Planned charging rotation and abrupt failures can share one roster/lifecycle interface; they may differ in observability and anticipation but need not require distinct policy architectures.

### H3 — representation dominates credit complexity in this problem family

The G46–G49 reductions suggest that robustness may arise primarily from roster representation, observable current state, active-set context, and source pairing rather than baseline-conditioned or realized-successor actor credit. This remains a toy-bound inference until UAV transport is tested.

### H4 — current-state control may be enough within a registered observability contract

The native-six actor may retain performance without recurrent carry when current observations expose sufficient demand, active-set, and lifecycle information. This must not be generalized to partial observability or arbitrary UAV failures without direct evidence.

### H5 — common-fast-anchor necessity is an optimization-path question

If G50 later finds that the common fast anchor is necessary, it may be framed as a finite-budget curriculum or optimization-path contribution. If fresh G49 training is sufficient, the final method becomes simpler. Neither outcome is available yet.

### H6 — systematic robustness requires a matrix, not one average score

A defensible robustness claim likely requires multiple roster-event families, severity levels, held-out processes, service-floor and recovery metrics, and tail-risk confidence—not merely improved average utility on one source.

### H7 — source feasibility is logically prior to algorithm comparison

An oracle or constructive feasibility controller must demonstrate that the UAV task can meet absolute service floors and that the event genuinely requires reallocation. Failure of all controllers on an infeasible source is not evidence against the algorithm.

For each hypothesis, classify it as currently supported, partially supported, plausible but untested, poorly posed, or contradicted. State the smallest falsifying experiment.

## Candidate paper contribution structure to assess

One possible two-layer paper is:

1. **Algorithmic contribution:** a roster-native shared decentralized policy with anonymous active-set semantics, explicit member lifecycle/state ownership, no fixed identity slot dependency, and a minimal current-state single-immediate training route.
2. **Evaluation contribution:** an identifiable UAV robustness protocol separating planned rotation, unexpected dropout, count shock, replacement, and rejoin, with held-out team sizes/processes and tail-aware service metrics.

Potential central claim:

> Under a registered class of UAV service tasks and roster perturbations, a roster-native shared policy preserves service across within-episode membership changes without retraining per team size or relying on fixed identity slots.

Audit whether this claim is novel, measurable, and supportable. Rewrite it if needed. Do not broaden it to arbitrary UAV systems, arbitrary failures, safety certification, or universal robustness.

## Reviewer tasks

### 1. Paper-readiness judgment

Determine which statement is most accurate:

- the present evidence already supports a publishable mechanism paper but not a UAV robustness paper;
- a minimal additional UAV validation package could support the original narrative;
- the narrative requires a substantial redesign or a different core scientific question;
- the evidence is too fragmented for a coherent paper even after one additional validation stage.

Explain why and give a narrow claim ceiling.

### 2. Novelty and literature positioning

Compare the proposed contribution against recent primary literature on:

- variable-number or variable-population MARL;
- open/ad-hoc teams and teammate adaptation;
- graph, attention, set, mean-field, or permutation-equivariant multi-agent policies;
- fault-tolerant and robust MARL;
- communication dropout and agent failure;
- UAV charging rotation, coverage/service continuity, and fleet resilience.

Identify what is already known, what combination may still be novel, and the most dangerous novelty collision. Supply direct links/DOIs for the most relevant primary papers and distinguish accepted papers from preprints.

### 3. Minimum identifiable UAV benchmark

Specify the smallest UAV task that can support the claim. Include:

- state, observation, action, reward, and service definitions;
- motion/energy/charging/communication constraints necessary for credibility;
- event generator for planned rotation and unexpected failure;
- membership and rejoin semantics;
- oracle or constructive feasibility checks;
- no-reallocation and no-failure controls;
- exact source-identifiability tests that must pass before learning;
- what can remain abstracted without invalidating the paper.

### 4. Frozen experiment matrix

Propose the smallest conclusion-bearing matrix, separating mandatory from strengthening experiments. Address:

- training team size(s) and held-out evaluation sizes;
- planned versus unplanned event families;
- dropout duration, multiplicity, timing, and severity;
- replacement and rejoin;
- in-distribution versus held-out process laws;
- one versus two UAV tasks or simulator variants;
- simulation-only versus hardware-in-the-loop requirements;
- whether G50 must finish before UAV validation or may run in parallel conceptually.

Avoid an unbounded benchmark wishlist. Prioritize experiments that change the paper decision.

### 5. Baselines and ablations

Specify the minimum fair baselines, likely including appropriate members of these classes:

- fixed-N shared policy with masking/padding;
- recurrent shared MARL;
- attention/set/graph variable-agent policy;
- a published variable-number method such as a k-nearest or comparable approach;
- domain-randomization or dropout-trained robustness baseline;
- no-reallocation lower bound;
- oracle or no-failure upper bound.

For each baseline, state what alternate explanation it excludes. Define the smallest mechanism ablations needed to connect G46–G49 to UAV behavior without repeating every historical toy experiment.

### 6. Robustness metrics and statistics

Define measurable robustness rather than using the word generically. Consider:

- absolute mission/service utility;
- event-window minimum service;
- recovery time and recovery area-under-curve;
- catastrophic service-loss probability;
- worst-decile, CVaR, or another tail-risk measure;
- post-rejoin recovery quality;
- transport gaps between fixed and random roster laws;
- performance across unseen team sizes and event severities;
- inference latency, memory, and scaling with N.

Recommend a paired statistical protocol, independent training-seed strategy, confidence method, effect-size/margin choices, and power analysis approach. Do not prescribe a seed count merely by convention; explain how it should be justified.

### 7. Falsification and stop rules

List concrete outcomes that would:

- invalidate the UAV source;
- falsify roster-native transport;
- show that fixed masking is sufficient;
- show that recurrence or attention is load-bearing;
- show that robustness comes only from training randomization or extra capacity;
- restrict the claim to one team size/process;
- force retreat to a mechanism-only paper.

### 8. Paper architecture

Recommend:

- one precise title;
- a one-sentence thesis;
- three to five contribution bullets;
- a section outline;
- which G31–G49 results belong in the main paper, appendix, or should be omitted;
- whether G50 should be presented as a core contribution, a curriculum ablation, or unresolved future work depending on its eventual outcome;
- an appropriate venue tier/category, without overpromising acceptance.

### 9. Prioritized research plan

Return a decision-ordered plan. The first step should remove the largest scientific uncertainty. For each step state:

- decision changed by the result;
- required evidence;
- success and failure boundary;
- whether it consumes a conclusion-bearing scientific iteration;
- what later work becomes unnecessary if it fails.

## Required response contract

Use every heading exactly once and in this order:

1. `REVIEW_DISPOSITION=` followed by exactly one of:
   - `MECHANISM_PAPER_READY_UAV_VALIDATION_REQUIRED`
   - `MINIMAL_UAV_PACKAGE_CAN_SUPPORT_ORIGINAL_NARRATIVE`
   - `SUBSTANTIAL_REDESIGN_REQUIRED`
   - `PAPER_THESIS_NOT_YET_COHERENT`
2. `EXECUTIVE_JUDGMENT`
3. `PUBLISHABLE_THESIS_AND_CLAIM_CEILING`
4. `CURRENT_EVIDENCE_AUDIT`
5. `HYPOTHESIS_AUDIT`
6. `NOVELTY_AND_PRIMARY_LITERATURE`
7. `MINIMUM_IDENTIFIABLE_UAV_BENCHMARK`
8. `MANDATORY_EXPERIMENT_MATRIX`
9. `OPTIONAL_STRENGTHENING_EXPERIMENTS`
10. `BASELINES_AND_ALTERNATE_EXPLANATIONS`
11. `ROBUSTNESS_METRICS_AND_STATISTICS`
12. `FALSIFIERS_AND_STOP_RULES`
13. `PAPER_TITLE_CONTRIBUTIONS_AND_OUTLINE`
14. `PRIORITIZED_NEXT_ACTIONS`
15. `UNRESOLVED_SCIENTIFIC_QUESTIONS`

At the end, include exactly these five machine-readable lines once each:

```text
paper_now=YES|NO|MECHANISM_ONLY
uav_validation_minimum=<one concise sentence>
system_robustness_claim_now=SUPPORTED|NOT_SUPPORTED|TOO_BROAD
recommended_next_boundary=<one concise identifier>
review_complete=true
```

Do not include implementation code or claim that any proposed experiment has been run.
