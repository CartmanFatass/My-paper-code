Claim to test: a nearest-guided FLEX controller can learn lower post-churn unmet demand than the attained INDEPENDENT-NEAREST service reference under the unchanged native reward.
Binding MARL structure: agent-count change and coordination recovery; this is a proposed finite-budget service comparison, with no claim of information necessity or isolated actor credit.

# RCLE service-comparison design intake — 2026-09-10

**Recommend one new B/EXPLORE design: one fresh nearest-guided FLEX fit, 200 updates,
compared with its untrained initialization and the existing deterministic
INDEPENDENT-NEAREST reference.** Request a prospective complete cap of **300 seconds**,
including all runtime support and Monitor work. This document completes the allocated
design assignment; it is **not a frozen execution card or a numerical allocation**.
No implementation, model allocation/load, test, probe, training, native evaluation,
RNG master or scientific run root was created.

## 1. Assignment, current evidence and decision scope

Authority is the [Portfolio decision](../../portfolio/decisions/2026-09-10-rolling-successor-allocation.md),
its [complete response](../../portfolio/pro_packets/20260910_rolling_successor_allocation/archive/RESPONSE.md)
at b4d71be60f789e97bf1f4c7130bb9995fc84f387, and Root's 23:32 UTC design-only assignment
after integration 674f246a202eef1467b084fdd25e2eeb531c0b1e. The bound RCLE paragraph asks
for one implementable learned service comparison or an exact family question/no-ready
return, with zero numerical allowance. It does not transfer the old 1,500 s allocation.
RCLE remains ACTIVE/MEDIUM.

The [seed23 intake](RCLE_B03_FRESH1000_S23_RESULT_INTAKE_20260910.md) is unchanged:
Delta_U +.3033203125 and initialization gain +.3080179850, all 512 primary scenarios and
all 8 U/Y means favorable, **all 8 fragmentation means worse**, primary F increase
.015234375, reference U deficit .1162373861, and 2,045/2,048 W100 recovery scores
failure-coded 40. The three-root Delta mean .3500962999 is adaptive descriptive B;
recovered 22 is one training root. Prior failures, their costs and unknown prefixes remain.
Neither the gain nor the F reversal diagnoses a component defect.

The useful next observation is whether a real learner can improve the attained service
controller, not whether W100 again beats its nearly flat W1 control. No fourth unchanged
same 1000 root is proposed. This design changes the starting action preference inside the
same FLEX finite-budget learning package; it preserves its hierarchy, information,
native host and objective. The DM regards that as an object-tier comparator/training
design within the accepted mechanism, not a new family or a direction recast. No
Convergence disposition is invented. Numerical follow-on needs an explicit new allocation
through Root's existing route; completion of this design creates no standing slot.

## 2. One concrete learner and a competent attained comparator

Proposed name: RCLE-TBCFV-B04-NEAREST-PRIOR; one fresh training instance, proposed
master 24 in that new object domain. The domain/seed are declarations only. No old B03
checkpoint, baseline state, fitted controller, prefix or RNG root is loaded.

At each ordinary four-tick claim opportunity, agent i computes n_i, the candidate with
minimum absolute signed circular distance, using the existing public candidate feature;
ties select the lowest beacon index, matching the native reference. Define the fixed
six-action preference q_i(n_i)=.9 and q_i(j)=.02 for each other candidate. If s_theta(i,j)
is the existing FLEX pointer score, use

    pi_theta(j | legal inputs, plan) = softmax_j(s_theta(i,j) + log(q_i(j))).

Initialize the pointer's final scalar affine weight and bias to zero, so initialization
is exactly the declared stochastic .9/.02 policy. All other tensors use the existing
fresh affine initialization, including zero FLEX final update heads. This is a deliberate
new initialization, not byte-equivalence to B03. It retains 26,161 trainable FP64 scalars.
The equivalent logit offset is log(45) for the nearest candidate and zero for others.
The .9 choice is one fixed design choice: mostly local service with .1 total exploratory
mass; there is no sweep, schedule, expert trajectory generation or prior fitting.
Use one model subclass for this probability rule, copy the freshly initialized FLEX
tensors supplied by the existing initializer, then zero its pointer output and discard
the initializer's helpers. That is seven allocations: one trained model and six
untrained helpers, not seven training instances. No old fitted state is involved.

The complete sampled distribution above drives both the native action draw and its
selected-action log probability in the loss. There is no unscored override, off-policy
teacher action, importance-weight omission or greedy evaluation substitution. The
trainable scores can oppose or reinforce the fixed offset; no action is masked.
At evaluation, use the same sampled learned policy at the final 200-update checkpoint.

Retain the B03 weight100 **whole** score-gradient law: full 64-tick native Y,
episode-mean manager score plus 100 times episode-mean claim score, one joint backward
per 64-episode block, full-vector nonzero step norm .02, then the .95/.05 per-cell
baseline update. This is not claimed to be an unbiased reformulation of a differently
weighted policy gradient or isolated actor credit. No new critic, imitation loss,
entropy reward, F penalty, clipped objective, optimizer or training distribution is added.

There are exactly three endpoint roles:

| Role | Training | Purpose |
| --- | --- | --- |
| Nearest-guided FLEX, final 200 | One real fit | Candidate service controller |
| The same model before learning | None; evaluate before the fit | Separate native learning from the supplied starting preference |
| INDEPENDENT-NEAREST | None; reuse the fixed native algorithm | Attained competent service comparator and absolute reference deficit |

The stochastic initialization is **not assumed competent** just because its preferred
action is nearest. Exploratory mistakes or the prior itself may impair service. The
deterministic reference therefore stays the primary comparator. It receives no extra
information, tuning, training or oracle optimization; the learner has a larger declared
compute bill. This study does not compare equal training efficiency or show superiority
over every legal controller. No matching tuned generic TBCFV baseline package was found
in the repository baseline surfaces; attained-reference deficit remains distinct from
upper-minus-tuned-baseline headroom, which is absent.

## 3. Information, identity, action and native consequence

Read-only source trace, at reconciled authoring 863e250b84ea9dbb1fac07f0d962a59ddead4199:

- TBCFV empirical_runner.py, _public_tensors/_batched_public_tensors and
  _draw_claims_batch: public sets, own physical features, public context, candidate
  features and current plan form the 81-field pointer input.
- TBCFV models.py, make_pointer_inputs/claim_probabilities: candidate fields 73–76
  (zero-based) already include signed distance/60 at 76. The prior uses that field only;
  no extra snapshot, transport key, future demand or private state enters the actor.
- TBCFV native/tbcfv_backend.cpp, scripted package2: INDEPENDENT-NEAREST minimizes
  circular distance, breaking exact ties by first beacon index.
- The same native file, step_one/snapshot: actions move physical agents toward the
  claimed beacon by at most 3 sectors per primitive tick; actual proximity coverage
  determines unmet demand. Y=1−sum(u_t)/64, U=sum(u_t for t24…63)/40.
  F averages normalized claim-demand shortfall at 10 post-event claim opportunities.
  F is not in Y. Tau is the first qualifying four-zero-U run, with failure coded40.

Tick 24 roster change alters the surviving population and demand, which changes the
public sets and current candidate distances. Physical-entity state survives according
to the existing FLEX rules; rank is recomputed and is not a persistent policy slot.
Departed state is removed, newcomers receive prescribed state/noise, and
ACTIVE_CONTINUATION/NEW_EPOCH remain their actual distinct event paths. No rejoin,
replacement, extra censoring, private information or persistent identity is introduced.
Plans still affect claims; all partner policies co-adapt through shared-parameter training.

The prior favors the attainable local service action. The existing public pooled
positions/demands, own rank and plan can then change which agents depart from it, with
their native travel and coverage determining whether such deviations help. This is a
testable design rationale, not evidence that it will repair undercoverage or F. Claims
and actual proximity coverage are different quantities, so improved U alone does not
establish better fragmentation. Four-tick holding and the undiscounted 64-tick return
retain their original time semantics; this design introduces no new option termination.

## 4. Independent unit, primary measurement and interpretation

Use the existing 8 training cells (6→6,10→10,6→10,10→6 crossed with the two event modes),
eight episodes each per block. One prespecified fresh fit ends at 200 updates; no held-out
checkpoint selection. All three endpoint roles use the same 8 held-out cells
(8→8,12→12,8→12,12→8 crossed with the two modes), 256 exogenous scenarios per cell.
Training and evaluation remain separate semantic purposes. Initial/final sampled
policies share declared exogenous and action-uniform coordinates where available;
the deterministic reference consumes no actor uniforms. Sharing scenarios does not
require identical policy-dependent physical trajectories.

Primary Delta_ref is the equal-weight mean of U_reference−U_final on
ACTIVE_CONTINUATION8→12 and12→8; positive favors the learned controller. Also report
the two path levels and contrasts, G_U=U_initial−U_final, signed remaining reference
gap U_final−U_reference,40U, and every 8-cell U/F/tau level and contrast. Retain the
tau 40 fraction. Learned initial/final Y is reported; the historical scripted endpoint
wrapper has no Y field, so reference Y stays unavailable rather than reconstructed from
post-event U. Optimization nevertheless uses the unchanged full 64-tick native objective.

The independent learning unit is the complete fresh training instance, n1. Scenario
uncertainty is conditional on that fitted controller and the fixed reference, using
the declared matched paths. No training-population interval follows from 2,048 scenarios;
prior B03 roots are historical context, not matched controls or additional B04 seeds.
Preserve all outcomes and completed training blocks. This proposal was informed by
the observed B03 results, and makes no confirmatory or transfer claim.

**Reuse the existing absolute U interest scale .05**, equivalent to two normalized
unmet-demand ticks over40; it is this design's descriptive service scale, not a new
repository-wide threshold or a reinterpretation of seed23. There is no F MEI, F/U
exchange rate, aggregate utility or F nonharm rule. The old tau 4 descriptive scale
does not convert failure-coded 40 into uncensored recovery time.

Proposed reading, to be fixed with any later card:

| Observation | Bounded reading and recommendation |
| --- | --- |
| Delta_ref≥.05 and G_U>0 | Above-interest local service improvement over the attained reference with native learning; retain the size of G_U, both paths and every F/recovery consequence. Consider one independent follow-up only through a later allocation. |
| 0<Delta_ref<.05 | Small reference improvement; retain exact size, initialization gain and cost. No stable superiority claim. |
| Delta_ref≤0 and G_U>0 | Learning may improve the supplied stochastic prior, but the attained reference deficit remains; do not call this competent-reference superiority or automatically extend training. |
| G_U≤0, whatever the reference contrast | No positive learning-from-initialization claim; report any supplied-prior benefit separately. |
| Opposed primary paths or worsened F/recovery | Mixed native consequences, reported alongside intact service facts. No post-hoc scalar tradeoff or unqualified nonharm. |
| Reward/information/training/primary defect | No dependent performance polarity; preserve any independently trustworthy facts and actual exposure. |

Inside the .05 scale, a small benefit may still be real and useful, but no automatic
extension follows. An opposite sign is a negative for this fixed candidate/budget.
F loss is not erased by service improvement, and does not erase trustworthy U learning.
One finite result cannot establish a general solution to roster recovery or explain the
old coefficient effect. Failure to beat the reference is not a prerequisite failure
that requires a preceding diagnostic/search object.

## 5. Prospective work, cost and engineering boundary

Counts below were calculated with Python AST/literal arithmetic from the existing
B01 cost_law, TBCFV config/inference constants and this proposal; no experiment code
was imported. The native environment and learner were never executed.

| Work | Proposed count |
| --- | ---: |
| Fresh trained arms × independent seeds × update blocks | 1×1×200 |
| Training episodes:200×8 cells×8 | 12,800 |
| Training primitive ticks:12,800×64 | 819,200 |
| Endpoint episodes:3 roles×8 cells×256 | 6,144 |
| Endpoint primitive ticks | 393,216 |
| Complete scientific episodes / primitive ticks | 18,944 /1,212,416 |
| Backward/update calls; two 32-episode rollout batches per block | 200; 400 batches |
| Joint claim opportunities, training/evaluation | 204,800 /98,304 |
| Neural policy agent-claim decisions, training plus initial/final panels | 2,293,760 |
| Six neural candidate scores per agent decision | 13,762,560 |
| Scientific model allocations: existing initializer 6 plus new subclass 1 | 7 total: 1 fit plus 6 untrained helpers |

The equal-cell training populations average 8 and held-out populations 10; those fixed
counts, not an independent-agent assumption, determine the agent-decision totals.
The existing 16 claim opportunities per episode and lifecycle manager/event calls remain.
The prior adds one six-way nearest comparison and six constant logit additions per
neural agent decision, not another neural forward, fitted advisor, rollout, solver,
candidate policy or future trajectory. No6^N joint-action search is proposed.

Why200 rather than inheriting1000: the new question begins near the attained action
rule and tests whether real learning improves it. A first 200-update observation can
answer that bounded question. At 1000 the same single-fit/three-panel design would use
70,144 episodes and five times the gradient/training work, with no current evidence
requiring that larger initial investment. The negative ceiling at 200 stays explicit;
neither automatic continuation nor a mandatory diagnostic is added.

Existing timing analogues on wsl_4070 CPU FP64/thread1 are [S20](RCLE_B03_S20_RESULT_EVIDENCE_20260909.md)
W1 with initialization/final panels 89.83 s, W100 with final panel 80.62 s, and reference 2.85 s;
the earlier recovered W100 was 70.95 s. These are old complete invocations, not a measured
timing for the proposed action law. The new offset/initialization, future build and
support costs remain unmeasured; no exact speed forecast is supplied.

**Request, not allocation: 150 s complete learned invocation +10 s complete reference
invocation +140 s all additional runtime support =300 s total.** The learned invocation
includes admission/initialization, initial evaluation,200-block learning, final
evaluation/checkpoint and its publication. The 140 s covers any needed native build,
staging, focused contract checks, review execution, Monitor observation, collection,
analysis, final publication, evidence preservation and cleanup; do not exclude Monitor
or charge a phase twice. Agent authoring/review effort is unmeasured and is not called
runtime wall. Sum of invocation wall, study critical path and aggregate CPU remain
distinct; no parallelism saving or automatic retry is assumed. A cap is not a measured
cost or evidence of feasibility.

Future L0, if this design receives an explicit implementation/execution allocation:

1. Deliver a thin B04 study wrapper/model-local claim-probability override and initial/
   final/reference publication, preserving the above complete comparison.
2. Own the existing codex/rcle checkout; proposed new surfaces are
   experiments/candidates/roster_consistent_latent_exploration_tbcfv_b04/study.py,
   one scripts/rcle_b04_nearest_prior entry and one focused direction test. Reuse the
   B03 weighted update and existing native host. Existing core/frozen studies remain
   read-only unless a concrete dependent change is separately named.
3. Preserve the legal 81-field inputs, six claims, FLEX entity lifetime, native Y/U/F/tau,
   FP64 CPU/thread1 and semantic RNG consumers. Serialize the changed model's explicit
   prior/initialization settings with its ordinary output so evaluation uses the same
   law; do not add a generic factory or new provenance guard.
4. Focused acceptance must falsify nearest/tie computation, .9/.02 initialization,
   identical action/score probability, gradient flow through the used probability, and
   final checkpoint/evaluation publication. Changed action/score semantics warrant
   independent high-risk review under engineering §7.3. No check is executed in this
   design assignment; later checks stay within the proposed support bill. Use synthetic
   tensor fixtures for the changed probability/checkpoint contract and the actual
   allocated result for native publication; no additional environment episode or
   policy rollout is proposed as validation. Technical fixture allocations/calls are
   separate from the scientific table and remain unmeasured within the 140 s support bill.
5. Remote-first after exact source publication and fresh destination-adjacent memory
   admission. Respect the 150/10/140 components and 300 s total; stop at the fixed endpoint
   or actual failure/cap. No extra seed, panel, retry, tuning, profiler or continuation
   is included. Standard source/runner/test scope budgets still apply.

Engineering §4: **this design needs no added listed machinery**. Existing learner
checkpoints and the owner's detached supervisor/Monitor route are reused, not rebuilt.
No source or test diff exists to accept today.

## 6. Scientific reading and verified literature effect

Reused evidence-spec §§11.4,11.7–11.10 and FOUNDATIONS §§3–6 plus
02_MARL/04_EMPIRICAL at main 674f246a2 (unchanged explanatory passages). The concrete
assumption is that a deterministic function of the already legal candidate-distance
feature adds an inductive preference, not execution information. The source trace above
supports that assumption. Representation of a useful behavior and finite-budget learning
remain different; neither a prior nor shared parameters establishes native competence.
Conditional scenarios cannot substitute for an independent training unit.

Question-driven library search asked whether using an imperfect attained rule as an
overridable action preference is a reasonable learned comparator, and what cautions
it introduces. My-lib's supported coverage command reports only 2 papers/2 mechanisms
in synthetic-core, explicitly synthetic fixtures; those were excluded. Real download
directories were visible but not verified as a real searchable collection. No synthetic
hit or unavailable integration is treated as scientific evidence.

The Inst-sci formal catalog.v2.jsonl was searched for residual/prior/advisor/imitation
mechanisms. It yielded real guidance candidates, including MARL-0576 and MARL-0224;
metadata alone was not used as a method result. For MARL-0576, Liu et al.,
[Integrating Suboptimal Human Knowledge with Hierarchical Reinforcement Learning for
Large-Scale Multiagent Systems, NeurIPS 2024](https://papers.neurips.cc/paper_files/paper/2024/hash/ba29e3f830d039c3f1fa0b4dfcf19c54-Abstract-Conference.html),
the official page confirmed identity. The metadata record has official-title match,
quality grade A/no warnings, but its semantic tags are abstract-grounded. I therefore
read C:/Projects/Inst-sci/papers/MyLib/json/MARL-0576.json, §2.3 p3 (element 149),
§3.1 p4 (175,193–194), and §3.2 p5 (210,212,215,217); PDF identity
c836d3fa16d1c2d627500f58cfd6bc9ad1c728486fe080c40aa38c79d19068ce.

Those passages describe observation-legal guidance and warn that imperfect advice can
hinder learning; their integration lets agents depart from it. That changes this design
by retaining all six actions, native-return training and the untrained-prior comparator.
The paper's fuzzy-rule/hypernetwork/graph method and SMAC evidence do not validate this
fixed logit prior, select .9, explain seed23, or supply a novelty claim. The proposed
small offset is the DM's inference for this existing host; it is not an implementation
or claimed reproduction of hhk-MARL. No literature acquisition or framework migration
was commissioned.

## 7. Decisions this design intake produces

**Object-tier design selection.** Options: (a) the one 200-update nearest-guided FLEX
comparison above; (b) another unchanged same 1000 pair; (c) invent a new F/U reward or
first fit/tune a baseline; (d) return no ready candidate. Recommend/select(a) **as the
design output only**. It places a real learner against the attained service controller
with an explicit learning-from-initialization measurement, at one training unit and
known bounded work. The existing public distance feature makes it concrete without
unpriced demonstrations, new information or a causal diagnosis. Its strongest
counterargument is that the .1 exploration mass and normalized whole-law learning may
harm an already useful local controller or learn nothing within 200 updates. The study
would report that outcome directly. This is a falsifiable proposal, not competence
already established.

Owner-delegated decision (unattended,2026-09-03 instruction): **(a), publish this
design/recommendation and end the assigned zero-numerical work.** The 300 s proposal is
not approved or consumed. No card is frozen, so this ordinary object design is recorded
in the intake/audit rather than a new owner-console card item. The existing Portfolio
owner item 20260910-root-004 carries the allocated design assignment.

**Direction/Portfolio boundary.** No family/lifecycle/priority change or new Pro request
is made. Return the concrete design and its separate allocation need to Root. A later
specification that changes objective or opens another family would require the proper
direction question; that is not the current proposal.

**Claim ceiling/support/contradiction.** Current empirical support remains B03's local
service learning. Its strongest contradiction remains reference/recovery deficits and
all-cell seed23 F harm. New evidence is read-only source/literature reasoning and design
arithmetic, not a new scientific performance result. The next discriminator, if selected
and allocated, is final 200 versus both initialization and deterministic nearest, with
all native consequences retained.

**Exposure and boundary receipt.** New scientific episodes 0; primitive ticks 0; training
instances 0; model allocations/loads 0; backward/update calls 0; native/controller calls 0;
tests/probes 0; implementation lines 0. Existing S23/H_A1/history retain their own counts
and meanings. Owner prediction: not taken (unattended); no new result is available to
score. Live-main owner reviews were empty; no applicable nonempty owner instruction was
found. No valid-result Chinese brief is due for a design-only return.

Shared authoring started clean at fce30af098aec7e6b75c4cbddf61da2af5c50a28. Merge
863e250b84ea9dbb1fac07f0d962a59ddead4199 brought main 674f246a2 inputs into codex/rcle;
the only audit conflict was resolved to main after verifying it already contained every
RCLE row. No unique row was discarded. Source/history/other directions were preserved.
Only this direction design, its next-discriminator pointer and its audit row are newly
authored. Root owns main integration and any subsequent allocation.
