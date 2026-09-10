Claim under test: fixed stochastic own-expiry renewal improves sampled native team return over legal stepwise feedback when both velocity actors and critics train from the start.
Binding MARL structure: (b) temporal abstraction or termination; five partially observed, co-adapting UAVs hold asynchronous one- or four-step commitments while retaining private recurrent histories.

# UCOPE UAV fixed renewal B01 — science card, 2026-09-09

## 1. Authority, question and ceiling

Object **UCOPE-UAV-FIXED-RENEWAL-B01**, selector **renewal_fixed_b01**,
**B/EXPLORE**, one matched training instance **7701**. Root's **P78 allocation
of 2026-09-09** adopts the object-tier arm removal recommended in
[P77 intake §9](UCOPE_UAV_RENEWAL_FROZEN_HEAD_B01_P77_INTAKE_20260909.md#9-decisions-this-completed-intake-produces).
It authorizes one fresh F/G/H comparison inside the accepted own-expiry family,
following [P74's CONTINUE intake](UCOPE_POST_RENEWAL_B03_CONVERGENCE_INTAKE_20260909.md).
It is neither a direction recast nor retrospective replacement of P77's primary.
Recasts remain **1**. Earlier allowances, outcomes and result rules remain intact.

The observation asks whether the fixed initial stochastic renewal package F
earns native return over legal ordinary feedback G on a new fit. **F−G is primary**;
retain F−H and G−H independently. P77's displayed F mean exceeded G's, while
learned T lost to G, F and H. That observed ordering motivates this prospective
question; no new P77 test or favorable retrospective primary is asserted.
No stable superiority, equivalence, isolated duration-learning or timing effect,
information causality, transfer, deployment, C or Portfolio conclusion follows.

## 2. Preserved host and fixed renewal package

Inherit [P77 card §2](UCOPE_UAV_RENEWAL_FROZEN_HEAD_B01_SCIENCE_CARD_20260909.md#2-preserved-host-and-changed-frozen-comparator)
and accepted source **002ba439773c72cfdf042a2e31d221cf512a3a3d**: five UAVs,
50 users, 256 primitive steps, unchanged native wrapper/base/adapter, private
actor input108/GRU64 and critic predecision input136. Primitive observations
and recurrence remain free while held; own expiry triggers real action
selection, held actions are suppressed, selected labels are horizon-censored,
and recurrent state resets only at episode boundaries. Membership is fixed.

F retains its entire initialized **67→32→2, 2242-parameter** duration head,
permanently frozen before training. Both final-layer weights and bias start
at zero, so finite-input logits stay zero and probabilities stay **one half /
one half**. Actual sampled fractions can vary. F's velocity actor and critic
learn from the start. This is the original fixed initial law, with no fitted
duration probabilities or checkpoint-frozen trained policy.

F selects duration1 or4 at each own expiry, conditioned on the stored detached
command, through the accepted compound-density path. The fixed categorical
factor cancels in the PPO ratio and provides no head update or duration-path
gradient. Ordinary velocity, recurrent and critic gradients remain. G keeps
every legal stepwise velocity action, and H is untuned zero velocity. The
observation, information, action limits and reward are unchanged.

Preserve gamma1/full native returns, agent-compound clipping, all-primitive-row
loss denominator, zero entropy, Adam/lr0.0003, global gradient clipping,
truncated recurrence and final-checkpoint evaluation. Shared optional VSPC1
value moments stay **None**; UCOPE's scalar critic targets stay unnormalized.
F has68553 total/66311 trainable parameters; G has66311 trainable parameters.
Only F's2242 duration parameters are intentionally fixed. Policy exposure,
clipping and partner co-adaptation differ, limiting mechanism attribution.

Path: **own expiry amid team movement → owner's current legal history and
command → fixed-law persistence → geometry/service and later free observations
→ masked actor/critic exposure and partner co-adaptation → native team return**.
No join/leave/rejoin, replacement, interrupted hold or new discount clock arises.
Reuse the verified UTE/ACAC retrieval in
[P74 preparation §3](UCOPE_POST_RENEWAL_B03_P74_PREPARATION_INTAKE_20260909.md);
the fixed-law alternative now motivates arm removal, not an imported algorithm
or additional diagnostic prerequisite.

## 3. Fresh RNG and real learner exposure

Master **7701**, b=**770100000**. Common actor/critic initialization b+11;
F's initial duration head b+12. G's separate training velocity/duration
generator objects use b+21/b+22; F's use **b+31/b+32**. Common training
resets are b+1000+e, e0..511. Common F/G/H final resets are b+2000+e, e0..31.
G's private final velocity/duration generators use b+3000+e/b+4000+e; F's
use **b+5000+e/b+6000+e**. H has no action draws. Preserve actual private
stream consumption; do not align per-step draws or share action arrays.
A scoped preparation search found no prior master/base/selector/object match
in current UCOPE docs and mapped source/tests; this is not a global RNG census.

Train F/G separately for **512 complete episodes,131072 native steps,
256 two-episode rollouts and1024 Adam calls each**, four epochs per rollout.
Evaluate each final checkpoint stochastically for32 complete episodes, plus32 H
episodes. No new final panel selects checkpoints, seeds or configurations.
One matched instance is the independent training unit; two fits, UAVs, updates
and evaluation episodes are not independent treatment-effect replicates.

Machine-generated prospective exposure from
[configuration arithmetic](UCOPE_UAV_FIXED_RENEWAL_B01_P78_PROSPECTIVE_FACTS_20260909.json):
`matched_training_instances=1; fitted_arms=2; native_steps=286720;
optimizer_steps=2048; final_eval_episodes=96; lr=0.0003; F_parameters=68553;
G_parameters=66311; F_frozen_duration_parameters=2242; trainable_parameters=132622`.
Retain per-group initial/final norms and displacement for both fitted arms,
including F's two head layers. Its intended head displacement is zero; actor
and critic provide real learner exposure. Relative movement from a zero initial
norm is undefined. No favorable movement threshold follows. Preparation exposure=0.

## 4. Work, cost and node

`2*512*256+3*32*256=286720` native steps; `2*256*4=2048` Adam calls;
512 rollouts,1120 explicit resets,2 constructor resets,96 final evaluations.
Reuse the existing1600 first-five-step diagnostic rows. Versus P77 this is
2/3 of training,3/4 of evaluation and0.6730769230769231 of native steps.
There is no candidate/trajectory/probability/checkpoint search or T fit/evaluation.

F head work is `6*training_renewals+2*final_renewals` forward rows:
1003520–4014080 rows,2215772160–8863088640 dense forward multiply-adds,
plus activation, sampling, environment/recurrent, backward and optimizer work.
Count bounds do not imply wall multipliers. G has696320 velocity selections.

Per fitted arm cost law: **initialization +131072 training steps +1024 updates
+8192 final-policy steps +publication**, plus F head work; G also carries8192 H
steps. Execute serially **F,G**, charge common startup to F and H/final
publication to G. Caps remain **1800s per complete arm and3600s for the whole
invocation through publication/exit**, including all required phases.
P77 measured F170.78452501102583s and G including H146.30148461798672s;
its three-fit outer wall was501.69s. New two-fit outer wall is unmeasured.
These references and lower known work do not guarantee new timing. No known
count projects over cap; a concrete over-cap issue returns the necessary work
without pilot, increased cap, cost probe or hidden phase.

Added verification is one affected suite≤300s and independent semantic review.
Use configured **remote_first**, `hmasd-wsl-node`, exact committed/pushed source,
detached exact-SHA worktree and `agent-task`, **CPU FP32/one Torch thread**.
Host identity is not the estimand. Immediately before the sole scientific
invocation, canonical actual-node admission must show physical and effective
availability≥4GiB, joined to the exact runner with `&&` before scientific roots,
RNG, models or optimizers. CM is sole observer/collector.

## 5. Primary, MEI, predictions and reading

`J_a(e)=sum_t sum(info['rewards_dict'].values())/256`, retaining native reward
dictionary units. **Delta_G=mean(F−G)** on32 paired final resets is primary.
Publish all96 J values, three arm means and signed F−G/F−H/G−H vectors.
Conditional evaluation SE is `sample_sd(paired_episode_differences)/sqrt(32)`,
conditional on these fitted policies. Training-population uncertainty is unavailable
at n=1. **MEI: absolute0.01**, retaining the native scale used for the accepted
family so this arm removal does not change the worthwhile effect threshold;
coverage0.7/50=0.014 is context, not a promised effect or significance level.
**Tuned same-information headroom is absent**. Reuse G/H because observation,
action, information and budget match; report both hover contrasts independently.

| Complete primary | B-level reading and next recommendation |
| --- | --- |
| UP: Delta_G > +0.01 | Preliminary favorable fixed-renewal package evidence for this fit/task/budget; recommend a separately allocated small independent-fit follow-up if investment continues. |
| WITHIN: −0.01 ≤ Delta_G ≤ +0.01 | No demonstrated point gain at the selected scale; recommend no unchanged extension on this observation, without claiming equivalence or absent value. |
| DOWN: Delta_G < −0.01 | Adverse fixed-renewal package evidence against legal feedback; recommend dropping an unchanged continuation, without rescuing it through hover or prior means. |

Use unrounded boundaries and report distance and conditional uncertainty.
F−H/G−H cannot rescue primary polarity or establish general comparator competence.
How the result will be interpreted: above-MEI supports bounded package interest;
inside-MEI limits the observed point improvement; opposite sign retains a native
counterexample. None identifies learned-duration benefit because the duration
law is fixed. Every outcome ends P78 at full intake.

Prospective predictions: **Delta_G>+0.01 probability0.55** and **F−H>0
probability0.65**. P77's displayed means motivate modest fixed-persistence
interest, while one F fit and the renewal family's sign reversals keep confidence
limited. These are outcome-informed exploratory judgments for the fresh fit,
not calibrated posteriors or retroactive P77 predictions. Owner: **not taken
(unattended)**.

## 6. Engineering scope and stop

Engineering scope §4: **none**. Reuse existing learner, publication, checkpoint
and infrastructure paths. Source≤2000 new lines, runner≤600 lines and focused
affected checks≤300s. Stop on allocated caps, refused admission, nonfinite
learning, or concrete reward/information/action-density/training/comparison/
primary defects. Retain executed counts and partial independently trustworthy
facts. Optional missing resources are `resources_unmeasured`; defects limit
their dependent claim. No scientific retry/resume/replacement, second instance,
extra P77 or P78 evaluation/H, tuning, probe, pilot, successor or Pro Send is allocated.

## 7. Complete CM handoff and acceptance

Same checkout `C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`,
branch `codex/ucope`; [P78 intake §2](UCOPE_UAV_FIXED_RENEWAL_B01_P78_INTAKE_20260909.md#2-five-item-cm-assignment)
gives the five-item full-batch assignment. Preserve every older selector/result.
New real7701/card section5 and fixture9001/section7 identities propagate through
CLI/config/RNG, renewal credit/entropy, F/G arm selection, counts and primary.

Reuse meaningful frozen-head/action-credit coverage and independently review
the changed arm/primary/budget boundaries. Focused checks verify no T fit or
evaluation, entire F head fixed/uniform with no head gradient/update while
velocity/recurrent/critic learning remains real, private stream addresses,
F−G/F−H/G−H completeness and first-arm F/last-arm G complete caps. No native
pilot or repeated smoke follows. CM owns implementation, semantic review
acceptance, focused checks, commit/push, wrapper/staging, one accepted detached
submission, sole observation/collection and technical return. No additional
source-permission phase is inserted. DM inspects accepted artifacts and intakes
science; Root owns main integration. Return actual scientific-meaning or budget
conflicts before dependent execution while continuing independent in-scope work.

## 8. Observed P78 completion — 2026-09-09

One7701 invocation at sourcec7c139c512b2dc598a00ff5746b1f89b1aaf8a46 completed
all286720 steps/2048Adam/96 final evaluations in334.19s with no cap breach.
[E0 evidence](UCOPE_UAV_FIXED_RENEWAL_B01_P78_RESULT_EVIDENCE_20260909.md) and
[DM intake §§7–10](UCOPE_UAV_FIXED_RENEWAL_B01_P78_INTAKE_20260909.md#7-dm-scientific-intake-against-the-card)
accept **valid UP**: F−G+0.026550516654013076, conditional SE0.011109495362659165;
F−H+0.030122962641204728, G−H+0.0035724459871916527. F's head stayed fixed
while actor/critic learning was real. All96 outcomes and15 adverse F−G episodes
are retained. The one-fit package ceiling and absence of tuned headroom remain.

Both forecast events occurred; mean Brier loss0.1625, owner prediction not taken.
P78 ends at the all-outcome stop. Intake recommends one separately allocated
new F/G/H training instance, creating no new card/master/run or Pro Send.
Original§§1–7 and all earlier result meanings remain unchanged; recasts remain1.
