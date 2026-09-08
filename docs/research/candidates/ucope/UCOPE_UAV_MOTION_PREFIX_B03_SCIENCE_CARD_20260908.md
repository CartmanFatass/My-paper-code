Claim under test: without an explicit entropy bonus in either learned arm, optional opening velocity commitment improves sampled complete native team return over same-information primitive-step feedback at the fixed training budget.
Binding MARL structure: (d) other-agent non-stationarity or partial observability; five local recurrent actors co-adapt through a shared reward, and the common learning amendment changes the incentive for their simultaneous stochastic exploration.

# UCOPE UAV motion prefix B03 — science card, 2026-09-08

## 1. Authority and question

Object **UCOPE-UAV-MOTION-PREFIX-B03**, **B/EXPLORE**. [P57](../../portfolio/handoffs/2026-09-08-p57-ucope-post-b02-selection.md)
at `68c7dab578d4e64d201a34028b574469bf1c598f` authorizes this specifically
selected in-family change and at most one fresh matched pair. The
[selection intake](UCOPE_UAV_MOTION_PREFIX_B03_SELECTION_INTAKE_20260908.md)
records the source-supported choice and alternatives under object-tier
delegation. The accepted family remains the optional opening commitment
versus ordinary feedback question; no new option, early termination,
environment, value-capacity or return-composition intervention is selected.

Set the **common total explicit entropy coefficient from .01 to 0.0** in
T and G. This includes the existing Gaussian velocity and T-only categorical
duration entropy terms. Sampling, trainable log standard deviation,
categorical duration probabilities and all native-return policy gradients
remain active. This tests new T against new G; it does not causally compare
entropy coefficients against B02 or claim that the old objective was defective.

## 2. Preserved host, information, action and credit

Reuse [B02 card §§2–4](UCOPE_UAV_MOTION_PREFIX_B02_SCIENCE_CARD_20260908.md#2-unchanged-host-ownership-and-information)
at the completed source `6374063408208ba67b8cb7c69ebc0babb0f00259`, with
only §1's coefficient and §4's fresh single master changed. The fixed host
is five UAVs /50 users /256 one-second steps, unchanged base reward,
physics, adapter, observation limits and legal velocity bounds. There is
no sensing fee, privileged actor feature, membership change or replacement.

T chooses velocity and duration1 or4 once at t0. A four-step choice holds
the command through t3 and releases at t4; observations, recurrence and
reward continue during the hold. No later option is opened. G may choose
any legal velocity every primitive step, including repeat or zero. Actors
receive their own108 components; the separate common critic receives the
same predecision136 components. Diagnostic/global state does not enter actors.

Both arms retain **agent-compound clipping**, summed over eligible agent
actions before averaging all primitive rows, including all-held rows in
the denominator. Velocity and opening duration stay grouped within their
owner. Old log probabilities and normalized scalar advantages are detached.
Architecture, common initialization, private histories/RNG, FP32 CPU,
gamma1 native returns-to-go, four full-rollout PPO epochs, Adam lr3e-4,
clip.2, value coefficient.5 and global gradient clip.5 remain unchanged.
The complete update is now `loss = policy_loss + .5*value_loss` in both arms.
Existing entropy values may still be reported as descriptive measurements;
they supply no bonus to this B03 loss.

The path remains command → position/channel/service → owning actor's local
observation and recurrent history → legal owned action/hold → scalar native
team return → PPO credit → fitted service. Removing a common bonus changes
the learning incentive along this path, not the observation/action interface.

## 3. Why this bounded change

Source `policy.py::joint_terms` rewards unsquashed normal entropy, independent
of the action mean; `learner.py::update` subtracts .01 times that entropy.
For G with all five agents active, the bonus alone contributes −.05 to
the loss derivative of each interior log-std coordinate before gradient
clipping. Existing B02 G logs rise from21.2840748 to22.0004864 /22.2533092.
Source-based arithmetic implies geometric mean latent standard deviations
about1.049 /1.067 at those last logged pre-update epochs, versus initial1.
These modest increases do not establish the bonus's causal role in the losses.

The motivation is to let native policy credit determine exploration scale
without a persistent explicit entropy reward. The verified ADER source
shows why exploration needs can differ among co-adapting agents, while
also protecting against exploration collapse. It does not endorse zero
bonus universally or establish this UAV result; [selection §2](UCOPE_UAV_MOTION_PREFIX_B03_SELECTION_INTAKE_20260908.md#2-source-and-literature-that-change-the-choice)
records its actual pages, real-corpus coverage and contrary evidence.

Strongest current contradiction: B02 T−G −0.0472671044 /−0.0061362058,
mean−0.0267016551; both T−H negative and G−H mixed. Historical P21 UP,
P24 WITHIN and6902 harm stay separate. The strongest alternative is that
ordinary feedback benefits equally or more, or that removing the bonus
reduces useful exploration. Initial broad stochastic actions remain, so
this amendment may have little effect. Geometry, persistence, optimization
and information remain unseparated. No extra seed or diagnostic resolves
those alternatives in advance.

## 4. Independent unit, fresh master and work

One fresh matched training-pair master: **7101**. The bounded current
UCOPE record/source search found no exact7101 match before this card;
[computed preparation facts](UCOPE_UAV_MOTION_PREFIX_B03_PREPARATION_FACTS_20260908.json)
retain its actual coverage. This is not a universal seed-namespace claim.

With b=710100000, use initialization b+11, training velocity b+21,
training duration b+22, training reset b+1000+e (e0..511), final T/G/H
reset b+2000+e (e0..31), private final velocity b+3000+e and final duration
b+4000+e. T/G begin with equal common parameters and reset inputs, then
use separate optimizers, recurrent histories and on-policy trajectories.

Each fit uses512 complete training episodes /131072 team steps /256
two-episode rollouts /1024 actual Adam calls. Evaluate final checkpoints
only,32 sampled whole episodes per T/G/H. H uses zero velocity without
training or tuning, on the same reset seeds through G's environment.
Independent training **n=1 matched pair**; episodes and agents add no
training units. No second-pair aggregate or endpoint sample SD is defined.

Dominant work: `2*512*256 + 3*32*256 = 286720` native team steps,
`2*256*4 = 2048` Adam calls,1120 complete episodes,96 final episodes and
1600 existing diagnostic frames. There is no nested candidate search,
additional forward path, extra evaluation, replay or cost probe.

## 5. Native primary, MEI, predictions and interpretation

For each final whole episode use the original base native reward sum:
`J=sum_t sum(info['rewards_dict'].values())/256`. Primary
`Delta=mean_e(J_T,e-J_G,e)` over the32 paired episodes of7101. Report all
T/G/H values, signed differences, mean T−G, G−H and T−H, and the conditional
paired-episode SE `sample_sd(differences)/sqrt(32)`. Training-population
uncertainty cannot be estimated from this one fitted pair. Do not pool B02,
P21/P24 or finite-host outcomes into this primary.

**MEI: absolute0.01 in complete time-average native team reward.** Retain
the task's prior one-percentage-point scale rationale; the coverage term
for one continuously served additional user is.7/50=.014. This is not a
measured headroom value or a QoS guarantee.

| Reading | Fixed rule and bounded interpretation |
| --- | --- |
| UP | Delta>.01: preliminary advantage of this fitted package under the declared task/budget; competence and information wording require their own evidence. |
| WITHIN | -.01<=Delta<=.01: no gain at the selected scale under this budget; not stable equivalence. |
| DOWN | Delta<-.01: adverse native evidence for this task/prefix/learner budget; local movement or information changes do not compensate. |

There is **no tuned same-information headroom record** on this host. Reuse
the original H reference because task, information and budget match; H is
neither a tuned generic controller nor an upper. Mixed/weak G−H limits
competence wording while leaving trustworthy T−G reportable.

Predictions before output: **WITHIN, probability.55**; **G−H positive,
probability.55**. Owner prediction: not taken (unattended). Score both
against the one allocated outcome. Neither creates a launch condition.

Above MEI would support considering a separately allocated bounded follow-up
of this package. Inside the band would favor another question-selection
decision before more unchanged training. Opposite sign would favor dropping
this tested combination from the next default choice. None proves entropy
causality, pure information value, stable superiority/harm, transfer,
deployment, C promotion or a family disposition. P57 ends after this intake.

## 6. Resource budget, engineering scope and stop

Caps: **1800s per complete learned arm;3600s for the full pair through
publication and exit**. T includes startup/common initialization; G includes
H and publication. Existing B02 complete-arm references are approximately
138.26s for T and137.54s for G. The cost law is unchanged; scalar bonus
removal adds no dominant work. These references are projections, not timing
guarantees. No diagnostic timing experiment is needed.

Use the existing remote-first CPU FP32 /one-Torch-thread route; host/device
is not itself the estimand. Commit/push accepted source before a detached
exact-SHA invocation. Require fresh actual-node physical/effective memory
admission >=4GiB immediately before scientific work. Root owns launch and
routine observation; the same CM collects and technically accepts; DM
retains all-outcome interpretation. No source/currentness change follows
from doc-only commits.

Stop at fixed counts/cap, nonfinite learning or a concrete defect affecting
reward, information, comparison, training or primary measurement. Preserve
partial facts and cap breaches. No retry, replacement seed, second pair,
extra evaluation/H-completion run, tuning sweep or automatic cap increase
is allocated. Missing telemetry limits its dependent claim under§11.8.7;
no stronger generic-competence or causal prerequisite holds this B.

Engineering scope §4: **none**. Use the existing learner, metadata and output
paths. Ordinary budgets remain source≤2000 lines and runner≤600 lines.
Acceptance uses one focused directory suite≤300s and independent review of
the changed learning objective. No separate runner smoke, profile or new
diagnostic invocation is part of this small scalar/identity amendment;
existing tensor/synthetic test boundaries may be used inside the suite.
The B02 smoke80.578s/60s breach remains historical under P48 and is neither
repeated nor retroactively reclassified. CM comparison's three batches are
complete; no fourth arm set is enrolled.

Preparation adds zero model, simulator, learner, evaluator, replay or
diagnostic invocations. The machine-generated exposure line in preparation
facts declares the real1024-Adam/lr3e-4 per-fit budget and reuses B02's
observed nonzero movement; actual7101 exposure must be reported at intake.
The [complete CM specification](UCOPE_UAV_MOTION_PREFIX_B03_CODE_SPEC_20260908.md)
owns implementation and its original focused acceptance.

## 7. Accepted source and exact P57 route — 2026-09-08

Sections1–6 were frozen at `f5230ca30537e7baa7db71ee2ba437a17efe807b`
before implementation or B03 output and remain unchanged. Accepted source:
**`70900ac7e7aa3a85b4f4ad6a2a8031ccb346fd44`**, tree
`13634a339b2d6e323238a46feac29f443d022b8e`.
The [CM technical record](UCOPE_UAV_MOTION_PREFIX_B03_TECHNICAL_ACCEPTANCE_20260908.md)
and [DM acceptance](UCOPE_UAV_MOTION_PREFIX_B03_SELECTION_INTAKE_20260908.md#6-implementation-intake-and-source-binding--2026-09-08)
record61 focused test passes, whole check wall2.30s and independent review
with no material finding. These are engineering facts, not a UAV result.

The [exact Root handoff](UCOPE_UAV_MOTION_PREFIX_B03_P57_ROOT_HANDOFF_20260908.md)
binds one7101 invocation to the existing exact-SHA detached remote checkout.
Root retains staging/current-state reconciliation, fresh actual-node memory
admission, launch and observation. CM retains terminal collection, and DM
all-outcome intake. No scientific invocation is accepted by this binding;
there is no second pair, aggregate, retry or additional evaluation route.

## 8. Observed P57 completion — 2026-09-08

The one allocated7101 pair is **COMPLETE / DOWN** at the accepted source.
T−G is−0.010093085146628955, conditional evaluation SE0.008506138301283968,
just0.0000930851466 below−0.01. G−H is+0.04756796231762334 and T−H
+0.03747487717099439. All96 final outcomes are retained; n=1 supplies no
training-population uncertainty. The frozen§5 rule is unchanged and is
not rounded into WITHIN or promoted to stable harm/entropy causality.

Actual work is286720 team steps/2048 Adam/96 final episodes,283.51s whole
wall, within all declared caps, with fresh admission and complete finite
artifacts. The WITHIN prediction misses and positive G−H prediction hits
(1/2); owner prediction not taken. See [E0](UCOPE_UAV_MOTION_PREFIX_B03_P57_RESULT_EVIDENCE_20260908.md),
[computed summary](UCOPE_UAV_MOTION_PREFIX_B03_P57_RESULT_SUMMARY_20260908.json),
[scientific intake](UCOPE_UAV_MOTION_PREFIX_B03_P57_INTAKE_20260908.md) and
[Chinese brief](../../portfolio/owner/briefs/ucope/2026-09-08_UCOPE_UAV_MOTION_PREFIX_B03_P57.md).
The unchanged B03 recipe is not automatically continued; P57 is complete
and exhausted. No second pair, retry, aggregate, extra evaluation, new
object, family disposition or formal UAV-entry change follows.
