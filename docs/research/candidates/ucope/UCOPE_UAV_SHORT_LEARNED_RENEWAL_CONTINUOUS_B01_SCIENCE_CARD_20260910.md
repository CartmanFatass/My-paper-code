Claim under test: learned short renewal improves final native return over primitive feedback after 2048 continuous training episodes on one fresh matched training instance.
Binding MARL structure: (b) temporal abstraction or termination; five partially observed, co-adapting UAVs retain their own recurrent histories during asynchronous commitments.

# UCOPE learned short renewal continuous B01 / 8701 — science card, 2026-09-10

## 1. Question, class and current authority

**UCOPE-UAV-SHORT-LEARNED-RENEWAL-CONTINUOUS-B01**, instance **8701**, selector
**renewal_short_learned_continuous_b01**, **B/EXPLORE**. Observe final learned
short-renewal **T−G primary** and **T−F secondary** on one fresh matched T/F/G
training instance. The question is whether learning the short commitment is a
useful package after this training budget. It does not demand a duration optimum,
causal localization, a tuned upper reference or a stable training-population claim.

Authority: [Portfolio decision A](../../portfolio/decisions/2026-09-10-next-five-chains.md)
and [Root's applied UCOPE assignment](../../portfolio/pro_packets/20260910_next_five_chains/EXECUTION_MAPPING.md#ucope--learned-physical-12-t-against-fixed-f-and-legal-gh),
from the full Pro response at **08e989073839fe5f0f91c6a8ad90a399bee37b6c**.
This is an object selection inside the accepted renewal family, not a third
unchanged F/G pair, a restart of P77, a new family or a C object. **Recasts: 1**.
Exactly one fresh triple is allocated through implementation, execution and intake.
No further source-acceptance gate or Pro round precedes this authorized B launch.

The [8602 intake](UCOPE_UAV_SHORT_FIXED_RENEWAL_CONTINUOUS_B01_8602_INTAKE_20260909.md)
preserves final F−G **+0.006630604939** (WITHIN), versus 8601
**+0.020735036727** (UP). Both 1024 F−G points were negative; 8602 had early
hover losses, although final F/G exceeded H on both instances. The historical
[P77 {1,4}/512 result](UCOPE_UAV_RENEWAL_FROZEN_HEAD_B01_P77_INTAKE_20260909.md)
remains contrary evidence: T−G **−0.04379734649**, T−F **−0.06808369804** and
T−H **−0.02623673365**. Its treatment, budget and fitted tensors are not reused.

## 2. Mechanism, learner and legal comparators

**T** samples physical duration **{1,2} primitive steps** at the owning UAV's
expiry from its trainable two-category duration head, conditioned on private
recurrent state and detached sampled velocity. **F** uses the same architecture,
initial head and support with the entire **2242-parameter head frozen**:
2176 seeded hidden parameters and 66 zero final parameters yield probability
one-half each initially and throughout F. **G** samples a legal velocity every
primitive step, has no duration head and holds for one step. **H** holds zero
velocity, with no learner or random action draws. T's head is trained by the
existing agent-compound PPO likelihood and native-return credit; it is not
supervised by an oracle or separately optimized for a proxy.

All three real fits retain the accepted private actor (108 inputs, 64 recurrent
state), centralized critic (136 inputs), per-primitive GRU observation, expiry
and held-velocity behavior, label0/1 likelihoods, censoring, literal d2/d4
counters and remaining/4 observation scaling. T/F map labels to physical1/2;
physical4 decisions therefore remain zero. Membership is fixed at five UAVs:
no join/leave/rejoin, replacement or survivor-state intervention occurs.

Native host: the unchanged `uav_motion_prefix_b01/environment.py` adapter and
five-UAV/50-user scenario, horizon256. Reward is the sum of the five native
`info['rewards_dict']` values, not an adapter scalar. Use raw undiscounted
Monte Carlo returns, gamma1, no bootstrap, existing detached normalized
advantages, primitive-row denominator, agent-compound clipping, entropy0,
`value_moments=None`, four full PPO epochs per two-episode rollout, chunk32 and
Adam lr0.0003 with the accepted defaults. Equal native training and optimizer
counts do not imply equal compute. T has **68553 trainable parameters**;
F/G each have **66311**. F's frozen head contributes no trainable exposure.

Environment event → owning UAV's private observation/history → velocity and
duration at own expiry → held motion and subsequent service/information →
masked native actor/critic credit, optimizer exposure and partner co-adaptation
→ native return is the measured path. T−F changes trainability and the resulting
jointly trained package; it does not isolate a pure duration effect.

G/H reuse the accepted host's observation/action/information boundaries; G has
the same training and optimizer budget. **Tuned same-information headroom is
absent**. H is a legal reference, not an upper or proof of G competence. Missing
headroom does not hold this B allocation.

## 3. Fresh initialization, state and RNG

Master **8701**, **b=870100000**. Common actor/critic initialization **b+11**;
the identical initial T/F duration head **b+12**. Create fresh copies, models,
optimizers and generator states. No fitted checkpoint, optimizer, recurrent
state, normalization state or stream from 8601, 8602 or P77 is loaded.

| Arm | Persistent training velocity/duration | Evaluation velocity/duration at checkpoint j, episode e |
| --- | --- | --- |
| T | b+41 / b+42 | b+70000+1000*j+e / b+80000+1000*j+e |
| F | b+31 / b+32 | b+30000+1000*j+e / b+40000+1000*j+e |
| G | b+21 / b+22 (duration unused) | b+50000+1000*j+e / b+60000+1000*j+e (duration unused) |
| H | none | none |

Training episode e=0..2047 resets to **b+10000+e**. Every evaluation panel and
H use the same 64 worlds **b+20000+e**, e=0..63, disjoint from training.
Each fit reuses its own environment; its constructor reset reuses the first
training seed and is counted separately. Shared worlds and initialization are
intentional; trajectories need not align. Action streams are private by arm and
checkpoint. T/F head initialization is intentionally shared, not their draws.

Each fit retains its model, critic, Adam and training generators through
**2048 episodes = 1024 two-episode rollouts × 4 Adam calls = 4096 Adam calls**.
After the updates at episodes **512/1024/2048**, use j=0/1/2 and evaluate64
episodes without learning or mutating model/critic/buffer/optimizer/normalizer
or training-generator state. Each episode clears recurrent, held and previous
action state. The next training reset follows its declared world seed. H runs
once after G's final panel, using G's environment; reuse those64 H returns for
all checkpoint contrasts. No intermediate checkpoint is selected or resumed.

[Prospective facts](UCOPE_UAV_SHORT_LEARNED_RENEWAL_CONTINUOUS_B01_PROSPECTIVE_FACTS_20260910.json)
compute declared address counts and disjointness from 8601/8602. A scoped
UCOPE master/base search found no prior8701 or synthetic9002 allocation before
this card. This is source-based arithmetic, not a global RNG census or guard.
Synthetic fixture9002 has horizon8, train6, checkpoints2/4/6 and eval2 only.

## 4. Exposure, dominant work and complete cost

One matched training instance; **3 fits × 2048 episodes × 256 ticks = 1572864
training ticks**; **3 × 1024 rollouts × 4 epochs = 12288 Adam calls**.
**(3 × 3 × 64 + 64) × 256 = 163840 evaluation ticks**. Total **1736704 native
ticks**, 6144 training episodes, 640 evaluation episodes, 6784 explicit resets
and3 constructor resets. There is no candidate search, tuning or extra native
validation. Actual algorithm work is training plus these fixed non-learning
panels; added engineering checks use the synthetic fixture and no UAV calls.

Each T/F head evaluates **6 × training renewals + 2 × evaluation renewals**:
**8110080–16220160 rows per fit** at2208 dense forward MACs each. T additionally
backpropagates through its trainable head; its incremental runtime is **unknown**.
Velocity, critic, recurrence and environment work remain in all fits. The bound
does not replace measured complete time or create a timing-probe prerequisite.

Historical 8602 F **795.986692883s** and G/H **573.656474890s** are nested in
the **1370.01s outer** invocation. T=F would give an internal-duration scenario
of **2165.629860656s** for three fits, with an unknown trainable-head increment;
this is not a complete forecast or runtime guarantee. Per-fit counts are unchanged
from the accepted continuous recipe. No cost experiment is allocated.

The allocation is **1800s per complete fit and 5400s complete study**, including
startup, all panels/H, necessary support, publication and exit. Within it choose
a **5100s internal scientific-command deadline and ≤300s supporting work**;
the5400s outer total always controls, and small admission/exit tails count inside
it. Support includes the new focused synthetic checks, required command/input
verification and automated collection/analysis, with actual durations recorded.
Authoring, review conversation, Git transport and waiting elapsed time are
reported separately when available, not substituted for machine work.
T executes first (shared startup charged there), then F, then G (H and final
publication charged there). Existing directory-test spend **12.9068072s** remains
in its300s cumulative allowance; this object does not reset it. Ordinary checks
have a prospective60s ceiling inside the support cap; a concrete overrun returns
for factual budget reconciliation without spending another scientific invocation.

Use **remote_first/hmasd-wsl-node, CPU FP32, one Torch compute/interop thread**.
Host identity is not the estimand. Publish exact source before executing in the
configured detached exact-SHA remote worktree under `agent-task`. Actual-node
canonical admission requiring physical/effective available memory≥4GiB is
joined by `&&` immediately to this one scientific command before scientific
roots, models, optimizers or RNG creation. Remote portability does not permit
an implicit device, dtype, information or budget change. No process migration.

## 5. Primary, result branches, all outcomes and predictions

For every episode, **J=sum_t sum(info['rewards_dict'].values())/256**. Retain
all64 native returns for each arm at each checkpoint plus H64 once. Publish
all six paired contrasts **T−G, T−F, F−G, T−H, F−H, G−H** with vectors, means,
episode identities and conditional evaluation SE `sample_sd(differences)/sqrt(64)`.
The fixed primary is **Delta_2048=mean_e(T_2048−G_2048)**. T−F is secondary.
Checkpoints share one training history; evaluation episodes and H are not
independent training replicates. No best point or pooled checkpoint is selected.

**MEI: absolute0.01 J**, preserving the host family's useful-effect scale so a
learned timing package is assessed on the same native quantity. No relative
gain is substituted. **Headroom absent; recasts1**.

| Complete final T/G primary | B-level reading |
| --- | --- |
| UP: Delta_2048 > +0.01 | Preliminary favorable learned-short package evidence on this fitted instance at the allocated budget. |
| WITHIN: −0.01 ≤ Delta_2048 ≤ +0.01 | No demonstrated point gain at this scale on this instance; not equivalence. |
| DOWN: Delta_2048 < −0.01 | Adverse learned-short package evidence at the final budget; earlier gains or hover comparisons do not rescue the primary. |

Apply unrounded values and report distances from both boundaries. Report the
same MEI bands descriptively for T−F and every F/G/H contrast without creating
additional primaries. Final T/G completeness governs the primary. Complete
allocation requires all three full training histories, all nine scheduled
panels and H. Missing F or H limits only its dependent comparison; no historical
control is imputed. Missing T-head instrumentation limits learned-head claims
under§11.8.7; trustworthy native differences remain reportable. A zero observed
head displacement must be reported and interpreted, not hidden or treated as a
general B launch gate. Missing optional resource telemetry is `resources_unmeasured`.

**How the result will be interpreted:** above-MEI T−G with T−F>0 and beneficial
T−H would favor considering another independent learned-short instance. T≤F
while F>G supports the fixed law on this instance and gives no evidence that
learning duration helped. A WITHIN or mixed result keeps uncertainty and may
favor ending unchanged spending. An opposite-sign result weighs against this
learned package at this budget. Every native hover loss is stated separately.
No outcome proves stable superiority/harm, pure duration causality, tuned
baseline competence, headroom, general sample efficiency or deployment value.
Every branch ends this single allocation; later work requires a new selection
and allowance at the applicable tier. No replacement seed, retry or successor.

Prospective predictions: **P(T−G_2048>0.01)=0.40**;
**P(T−F_2048>0)=0.35**; **P(T−H_2048>0)=0.60**. Historical P77 losses temper
the first two; both longer-budget F/G endpoints exceeding H weakly supports the
third while early hover losses remain contrary. Score exactly these events by
Brier loss and preserve all three. Owner prediction **not taken (unattended)**
unless an applicable response arrives before observation.

## 6. Engineering scope, acceptance and stop

**Engineering Scope Spec§4: none newly needed.** Reuse the existing duration
head, collector, PPO, group-displacement measurements, ordinary final weights,
counters and deadline. Add a narrow T/F/G mode to the existing continuous study,
CLI and mapped tests; preserve fixed8601/8602 and synthetic9001 behavior. No
new registry, guard, resume/retry, telemetry, checkpoint-selection or profiling
machinery. New source≤2000 lines and runner≤600; report the changed-source
orchestration share as a review signal.

DM owns the complete engineering batch and Git in the existing
`C:/Projects/HMASD-worktrees/dm-ucope-native-return-prep-20260906`, branch
`codex/ucope`. An optional Implementer owns the bounded code/check changes,
without Git or a scientific launch. Independent Astra/high review covers
trainable T head, frozen F, private RNG/evaluation nonmutation, primitive-time
credit, continuous optimizer state, labels/contrasts and partial/publication
behavior. Use actual changed-boundary synthetic checks and reuse accepted
unchanged reward/information/learner evidence; no mandatory native smoke.

Stop on a failed actual-node admission, cap, nonfinite learning or a concrete
defect threatening reward, information, comparison, training or the primary.
Pre-science rejection can receive an exact technical repair when no invocation
was accepted; reconcile uncertain effects on the same identity. An accepted
scientific failure has no retry/resume/replacement allowance. Preserve partial
trustworthy facts and charge breached budgets if they occur.

After acceptance DM sends `MONITOR_ADD` directly using live primary
`.codex/hmasd-monitor.toml`, records adoption pending and stops routine polling.
Root confirms adoption and forwards terminal facts; DM collects exact artifacts,
accepts engineering evidence, performs scientific intake/Chinese brief and
prepares cleanup inventory. Root owns main integration and acceptance of cleanup.

## 7. Grounding and object decision

Reuse verified local UTE retrieval in
[P82 intake§8](UCOPE_UAV_SHORT_FIXED_RENEWAL_B01_P82_INTAKE_20260909.md#8-bounded-interpretation-grounding-and-predictions)
and the current foundations temporal-abstraction/empirical sections already
read for the Portfolio decision. Fixed options and primitive clocks permit a
legal comparator; neither proves that learning a duration helps. One continuous
curve is one training history. This grounding changes the card's comparator,
clock and uncertainty interpretation, not its empirical polarity; no new
novelty or causal claim is made. Controlling evidence spec §§4,5.2,11.4,11.7–11.10.

Options: (a) execute the newly allocated learned-short T/F/G instance as above;
(b) repeat unchanged F/G; (c) defer this accepted chain. Recommend and select(a):
it observes learned versus fixed short renewal under the Portfolio allocation,
while another unchanged pair answers a different question. Budget subchoice:
(a1) reserve300s support inside5400s; (a2) expose the entire5400s internally and
account support afterward. Recommend/select(a1) to keep declared support inside
the complete allowance without a timing pilot.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a), with(a1).**
The existing Portfolio decision supplies the investment; this card freezes its
object details. Selection, predictions, owner-review status and execution facts
are retained in the [intake](UCOPE_UAV_SHORT_LEARNED_RENEWAL_CONTINUOUS_B01_8701_INTAKE_20260910.md)
and the audit row. Publishing the P2 new-card item does not wait for a reply.
