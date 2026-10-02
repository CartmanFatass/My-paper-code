# UAV message content

Lead: native `hmasd-direction-manager` child `/root/dm_message_content`, assigned by
Root `/root` in App task `01a0e560-4333-7b03-8ff3-759a4add1d9a`.
Authoring checkout: `/home/fires/hmasd-wsl`, shared `main`.
Owned paths: this directory and matching `experiments/candidates/`,
`tests/experiments/candidates/`, `runs/`, and `temp/directions/uav_message_content/`.

## 2026-09-28 - Source reconstruction and proposed complete content comparison

**State: source-only design for Root's current cross-question selection.** No result
launch, training, policy evaluation, new implementation, accepted operation, or Pro Send
has occurred. The proposal below is not an executed result or a confirmation plan.
Root's existing independent ResearchCritic `/root/question_space_review` covers the
selection and this concrete design; no duplicate selection critic is commissioned.
The substantive unresolved dependency is that review and Root's cross-question choice,
not per-fit permission or a resource preflight for reasoning. Project pause is lifted;
PPC/FSD pause and G33 freeze remain in their existing scope. Archived CADC/C2 leads and
accepted historical operations are not resumed or inherited.

### Question and the judgment it can change

Can a finite, jointly trained local-history message encoder and decentralized motion
policy improve complete native service and net J under the existing delayed RR channel,
relative to both the current hand-coded demand aggregate and a cheap history encoding?
The intended contribution is empirical understanding and, if useful, a complete learning
package on this native UAV host. Learned communication, history summaries and delay-aware
messages are not architecture novelty claims. There is no send-timing, BS-memory,
active-sensing, energy, reward, user-motion or intention-commitment intervention.

The consequential unresolved question is whether the *content and learned response* of
a demonstrably useful finite communication process can buy additional native service.
It is different from deleting slow sends for a frozen receiver, and from the earlier
joint send-scheduling/motion learner. Task usefulness does not require proving an
information upper bound first. Conversely, a new message head or parameter movement
does not establish useful content, cooperation or a trainable package.

Relevant published background was read at `1b5bde75830d29143b8baaa7fadcf5bf5f03fa6f`;
refresh to `e2ff834809c3cd4f80002ac6049cee93ff8faf3e` changes none of RESEARCH:
[topic 3, information structure](../../RESEARCH.md#3-marl-增加的是联合行为和信息结构),
[topic 5, C2 transport versus decision-time information](../../RESEARCH.md#5-技能和异步性是组织决策的方式其收益需要证据),
and [topic 8, information value and finite policies](../../RESEARCH.md#8-数学信息与博弈结构怎样帮助dm选择实验).
Their concrete effects here are to keep the competent RR process fixed, retrain all
receiver/motion policies, preserve a real ordinary content alternative, and read complete
J/service rather than packet freshness, entropy or representation proxies. S7's
BS/energy results motivate careful information and package distinctions but their
QoS/risk objective and movement/charging interface are not this host's objective.

### Original supporting and adverse evidence

1. CADC source `22e009c9387f2507aab6ebab4555d92e27f5070e`,
   [original card](../contention_aware_decentralized_communication/CADC_B01_CARD.md),
   [result](../contention_aware_decentralized_communication/CADC_B01_RESULT.md), and
   [training-unit summary](../contention_aware_decentralized_communication/evidence/cadc_b01_9302/RUN_SUMMARY.json):
   master 9302 LEARNED trained send and motion jointly; RR trained motion with fixed
   collision-free sends. LEARNED-RR was -0.013354921301 net J and -0.012099183996
   physical J, 10 favorable and 22 adverse final worlds. This was not a frozen-receiver
   comparison. Extra fees accompanied lower physical service; the result does not
   identify a collision, stale-content or learning-credit cause. Each arm completed
   512 train plus 32 final H256 episodes and 1,024 Adam calls; the pair cost 278,528
   team ticks, 2,048 updates and 375.34 s measured native wall in its old runtime.
2. C2 source `22ddf7b8fb9d2a02d01734939a9631866ff9a59e`,
   [complete notebook reading](../delayed_broadcast_timing/NOTES.md#2026-09-25--b01-complete-fast-only-loses-service-despite-shorter-transit-retain-rr),
   [unchanged summary](../../../../runs/delayed_broadcast_timing/c2_rr_fast_none_b01_s9302/summary.json):
   on fixed trained RR9302, RR-NONE was +0.079412983360 net J and +5.158203125
   served users/tick (31 favorable, one adverse world). FAST_ONLY-RR was
   -0.009034734047 net J and -0.615356445313 users/tick. Delivered delay fell from
   2.972 to 1 tick while valid cache age rose from 4.962 to 13.032 ticks and missing
   entries from 1.924% to 6.445%. This supports the complete RR process on one asset;
   it does not isolate payload value or compare independently trained no-comm policies.
   World 0's silence benefit and all fee reversals/losses remain contrary evidence.
   C2 cost 0 fits, 96 H256 episodes/24,576 team ticks and 133.813762369 s runner wall.
3. The [C2 final decision](../delayed_broadcast_timing/NOTES.md#2026-09-25--adopt-the-complete-advice-and-end-rr9302-timing-modifications)
   ended additional timing/threshold/payload replacement on that frozen RR9302 asset
   for lack of a worthwhile next use decision. This proposal does not reopen that
   frozen-receiver experiment. It buys fresh content/receiver learning with explicit
   ordinary comparisons and inherits the old unfavorable send-learning result.

The DM read those compact results and relevant source; it did not repeat the old raw
trajectory/checkpoint audits or reinterpret their recorded evidence as new replication.
`git diff` against CADC's frozen source found no changes in its four modules or the
reused UCOPE environment, policy and learner modules. A full new run still requires
published exact inputs and actual-node admission; old source identity is not a new
runtime-equivalence certificate.

### Actual host, information and action interface

The original `make_real` creates N5, 50 uniform **static** users, H256, a 1000 m square,
height 50-150 m, maximum component speed 30 m/s and one-second primitive steps.
It uses free-space vectorized radio, no shadowing, no paper reward, no FDMA and no
height penalty. `MultiUAVEnv.step` moves UAVs and recomputes native radio/greedy
connections; it does not move users. This is not the S7 mobile-user/energy host.
Source: [environment.py](../../../../experiments/candidates/ucope/uav_motion_prefix_b01/environment.py),
[native environment](../../../../envs/pettingzoo/uav_env.py).

The actor's 104 raw floats are own normalized xyz (3), up to 20 anonymous visible
user rows (relative xy, normalized SINR; 60), up to 10 anonymous visible teammate
rows (relative xyz, normalized SINR; 40), and normalized clock (1). Visible users
are ordered by descending SINR, not persistent ID. `min_sinr=3` makes a valid
user's normalized SINR at least .26, so `row[...,2] > 0` distinguishes padding.
No actor-visible row contains served/unserved status, the full demand map, or native
connection ownership. Diagnostics may read those truths without feeding them back.

The unchanged actor input has 171 floats: raw104, previous *executed* command3,
unused zero remaining1, and channel extras63. Extras are public GOOD/BAD one-hot2,
own physical ID5, t-mod5 one-hot5, own pending1, and five fixed-ID delivered records
of ten floats each. Each record has payload7, validity1, send_time/256, age/256.
The self record is invalid; identity and transport metadata are not charged against
the existing seven-float content budget, and are identical for all arms. Neither
undelivered messages nor another actor's GRU state enters the actor.

The existing actor is DENSE171 -> 64 plus 171 -> 16 -> 64 residual (projection
initially zero), tanh, GRU64, then a three-coordinate Gaussian motion head and tanh
execution. Private recurrent state resets to zero each episode. A training-only
critic sees normalized physical/history136 and the whole 5x63 current extras table:
451 inputs, 128/128 hidden layers. It receives no future channel draw. It is not a
fully observed in-flight-message state; its imperfect value baseline affects variance,
not the legality of the actor's information. No running input/reward normalizer is used.
Sources: [model.py](../../../../experiments/candidates/contention_aware_decentralized_communication/cadc_b01/model.py),
[collector/learner](../../../../experiments/candidates/contention_aware_decentralized_communication/cadc_b01/learner.py).

At tick t: deliver due packets; form legal inputs and update each actor's private
GRU; sample all motions and, for L's scheduled sender, content; resolve the RR request
using pre-motion information; execute motion and read native reward/service; advance
the independent channel exactly once. The channel starts GOOD/BAD equally and flips
with probability .05 per tick. A send takes one tick in GOOD, five in BAD, fixed at
send time. Only physical sender `t % 5` requests. Delivery precedes request processing,
so even a five-tick packet clears before that sender's next slot. There is exactly
one accepted request per tick, no collision and a .001 fee per tick in every arm.
Terminal in-flight messages are censored and never carried into the next episode.
Source: [channel.py](../../../../experiments/candidates/contention_aware_decentralized_communication/cadc_b01/channel.py).

Physical J is mean native team reward, `0.7 * served/50 + 0.3 * Q`, where Q averages
clipped normalized SINR over actually served connections. Net J subtracts .001 times
attempts/H. Thus all proposed net-J contrasts equal their physical-J contrasts by
the fixed fee, while absolute fees and transport counts remain reported. Native
quality, service, per-world losses and boundary/height behavior remain visible;
altitude here is not an energy or battery measure.

### Proposed B01: C, H and L, all with learned receivers and motion

This is one exploratory training block, one new fit per arm, ordered C, H, L.
All three train the full decentralized motion policy and central critic from fresh
common initialization for 512 complete H256 episodes. No old checkpoint is a scored
competitor, no receiver is frozen and no arm is chosen after seeing another's score.

| Arm | Seven floats placed in the original packet slot | Learning and interpretation |
| --- | --- | --- |
| C | Original current sender xyz, current visible-user centroid xy, zero ground-z, current count/20. | Competent historical comparator reproduced as a fresh motion/receiver fit. Six coordinates are informative; the seventh is the known constant ground height. |
| H | Current sender xyz; centroid xy of all valid visible-user rows in the sender's last up-to-five observations; normalized RMS radius about that centroid; mean visible count/20 across those observations. | Cheap deterministic current/history encoding; full receiver/motion learning. Its value is unproven, so C remains a required anchor. |
| L | Seven tanh-Gaussian latent scalars computed from the scheduled sender's current private GRU64 state. | Full learned content and receiver/motion package, using only native return. No fixed field meaning, synthetic labels or communication proxy reward. |

For H, each sender keeps a five-observation rolling collection of sufficient moments:
count n, sum of reconstructed absolute normalized user xy, and sum squared norm. Pool
valid rows from that window; `centroid=sum(xy)/n` and
`radius=sqrt(max(mean(||xy||^2)-||centroid||^2,0))/sqrt(2)`. Empty pooled sets give zero
centroid/radius. Count is total pooled n divided by `(20 * number_of_observations)`;
the beginning-of-episode window uses its actual length. Current sender xyz stays
current. These are weighted sightings, **not a count of distinct users**: a user seen
repeatedly receives repeated weight. There is no hidden-ID lookup, deduplication,
future position, global map or served-demand label. The fixed five-tick window matches
the maximum transit and RR period; it is not tuned on outcomes. It supplies persistence
and spatial spread cheaply, while the shared receiver GRU can retain earlier packets.
This is a source-motivated ordinary alternative, not a certified best hand encoding.
Its inferiority would not make L useful unless L also improves on C.

L adds `Linear(64,7)` and seven log-standard-deviation parameters (462 parameters)
after the common actor/critic initialization, with zero head weights/bias and initial
message log_std=0. A separate private RNG samples seven standard normals only for
the current RR sender; content is `tanh(mean + exp(clamp(log_std,-5,2))*noise)`.
The entire seven-dimensional code can change, rather than a bounded residual around
C/H. Initial content is deliberately uninformative, and its consequences are measured
at initialization. All arms keep exactly the same motion architecture, common initial
motion/critic tensors, raw observations, metadata, action space and reward.
The encoder can represent local history including previous commands and delivered
messages. This is equal *information access*, not equal representation or parameter count.

The message head does not condition on the same-tick sampled motion and no command is
held until delivery. Thus the design does not assert that today's intention will still
be valid one/five ticks later. Static demand can persist while UAV geometry changes;
whether the learned code selects useful persistent facts remains the conjecture.
It is not a future-trajectory predictor or a test of an intention-sharing mechanism.

### Finite learner and temporal credit

Reuse the existing four full-rollout PPO epochs per two-episode rollout: 256 rollouts,
1,024 Adam steps per fit, gamma=1 undiscounted complete-episode returns with no terminal
bootstrap, centered/scaled rollout advantages, chunk32 recurrent replay with stored
behavior hidden states detached at chunk starts. Preserve Adam lr3e-4, betas(.9,.999),
eps1e-8, no weight decay, foreach/fused false, clip ratio [.8,1.2], value coefficient .5,
entropy coefficient .01 per active Gaussian term, and global grad norm .5.

For each physical agent/tick, the PPO compound log probability is its three-dimensional
motion density, plus L's seven-dimensional tanh-corrected message density only when
that agent owns this RR send. Nonowners contribute no sampled content term. For a
send with known `t + delay >= H`, content cannot reach any later action within the
episode: still transmit/censor/charge normally, but exclude its content likelihood and
entropy from learning. This is a causal zero-effect mask, not an outcome/exposure filter.
The motion term is retained at every primitive tick, including final ticks. All episode
and world outcomes remain in the complete comparison.

The loss remains sum-agent/mean-team-row clipped PPO with the same native return
advantage as motion. Store the actual sampled pre-tanh message, old compound density,
eligibility/effect mask and delivered bytes. Received packets in recurrent replay are
the actual behavior packets, detached as observations. The sender is trained through
the likelihood-ratio term and later reward, not by differentiating through the channel
or simulator or by replacing old packets with new encodings during replay.

Concretely, for a complete behavior trajectory let `r_t` be the native net reward
after tick t's motion, `G_t=sum(r_k, k=t..255)`, and `A_t=G_t-V_old(s_t,records_t)`
before the common rollout centering/scaling. L's unclipped content score term is
`sum_t e_t * grad log p(z_t | h_sender,t) * A_t`, with
`e_t = RR_owner_eligible AND (t+delay_t < 256)`. Later native rewards in that same
trajectory, including all reward changes caused by peers' post-arrival actions,
provide credit to the stored send-time draw. The implementation uses the stated
per-agent compound PPO ratio for the motion/content factors, not this unclipped
expression as an additional loss. Only the unique eligible RR sender samples and
stores a message at a tick; other agents store mask-false placeholders and draw no
message RNG. Under this channel all such RR requests are accepted. An eventual
terminal-censored send is still sampled/stored/transmitted, with `e_t=false` for
both content density and entropy; it has no content-learning term.

This is a bounded and mathematically meaningful delayed-action credit path:
`E[grad log p(message|legal_history) * later return]` can change message generation
because arrival can change teammates' later motion and team reward. Earlier reward
terms add variance but cannot create an instantaneous content effect. PPO clipping,
function approximation, a growing receiver convention, seven noisy action dimensions,
and truncated recurrent gradients make finite learning uncertain. They are limitations
to report, not proof of inability and not a promise to add optimizers/auxiliary targets
after a disappointing result. The extra entropy term and parameters are part of the
tested package; a gain would not identify a pure semantic-content cause.

### Seeds, exposure, endpoints and decision branches

Proposed unscreened master 19431 gives `base=1,943,100,000`. Common actor/critic seed
is base+11; the separate content-head initialization address is base+12. Train worlds
use base+1000+e and channel base+6000+e, e=0..511. Private continuous training motion
and content streams use base+21/+22. No content draw consumes the motion stream.
At initialization and final, e=0..31 uses physical base+2000+e, channel base+7000+e,
motion base+3000+e and L content base+4000+e. All arms/checkpoints share those exogenous
addresses and actual reset scenes/channel sequences are checked; draws and hidden
states belong to each execution. No old CADC/C2 scored panel is reused or pooled.

Evaluate **sampled** motion in all arms and sampled content in L, matching the trained
policy; no post-result switch to mean content or deterministic motion. Initial/final
evaluation is isolated from all training RNG and optimizer state, has zero updates,
and does not select a checkpoint. Keep only the declared final endpoint. Own initial
and final service/J are both read; a change in initial advantage does not become a
causal adjustment to the endpoint contrast. The 32 worlds are nested under one
training instance per arm, not 32 training replicates.

Primary useful-package contrast: L-H net J with served users/tick and Q co-reported.
L-C is the required ordinary-anchor contrast; H-C shows whether the extra deterministic
history/spread representation itself has value. Read all per-world signed differences,
means, signs, worst losses and each arm's own learning, without a success p-value,
equivalence margin or the old CADC .01 branch transplanted as a new threshold.

- L improves mean J and service over both C and H and improves its own initialization:
  supports a conditional package-use observation and a later separately selected
  replication decision; it does not confirm content semantics or training-population use.
- H improves on C and L adds no useful complete gain: retain the ordinary package as
  the stronger conditional comparator and weaken investment in this learned recipe.
- L only beats H while H loses to C: no reuse case for L; the known comparator remains.
- J/service disagree or individual losses are substantial: retain the explicit tradeoff;
  mean J alone is not a service-improvement or tail-dominance claim.
- All complete comparisons are small/mixed, or the content pathway has little measured
  response: no established incremental use. Neither zero head movement nor changed
  messages prove an information bound; compare a targeted different prediction with
  retaining C/H or stopping. No repair is owed.
- Technical missingness: preserve actual fit/step/update frontiers and narrow valid
  facts; no complete comparison or negative learning verdict is manufactured.

Working prediction is uncertain: H may exploit static-demand persistence with lower
learning burden; L may encode task-relevant geometry/teammate context lost by a centroid,
but finite noisy temporal credit may fail. A one-seed package gain is useful exploration,
not a claim that RL messages generally beat hand coding. No outcome automatically adds
a seed, horizon, fourth arm, loss, density convention, message budget or new delay regime.

### Dominant cost and proposed implementation boundary

| Work | Per arm | Three-arm proposed batch |
| --- | ---: | ---: |
| New policy fits | 1 | 3 |
| Train episodes/team ticks | 512 / 131,072 | 1,536 / 393,216 |
| Initial and final eval episodes/team ticks | 64 / 16,384 | 192 / 49,152 |
| All complete episodes/team ticks | 576 / 147,456 | 1,728 / 442,368 |
| Primitive UAV motion samples | 737,280 | 2,211,840 |
| Two-episode rollouts/Adam calls | 256 / 1,024 | 768 / 3,072 |
| Replayed actor-row uses (5 UAVs, four epochs) | 2,621,440 | 7,864,320 |
| Accepted seven-float broadcasts, including terminal censoring | 147,456 | 442,368 |
| Planner/transition-model/radio counterfactual queries | 0 | 0 |

Each native step still performs its ordinary physical radio computation; zero extra
model queries does not mean zero simulator work. L generates 131,072 train and 16,384
eval message samples; its exact number of content-credit rows subtracts terminal-censored
messages and is reported. Actor inference during collection is 442,368 batch-of-five
calls; replay adds 3,072 chunked recurrent forwards over 1,572,864 team-row equivalents.
No candidate, subset, trajectory or world search is hidden in these counts.

Old CADC's 180.34-195.00 s/fit and C2's 133.81 s evaluation-only wall come from different
runtime/instrumentation conditions. They suggest modest native compute but are not a
fresh speed forecast. Plan sequential CPU FP32, one Torch/inter-op/BLAS thread, on
configured preferred `wsl_4070` if suitable at actual launch. A provisional 10-40 min
batch planning range allows added initialization evaluation and required readback, not
a scientific wall endpoint; exact runtime/RSS/output footprint remain unmeasured.
Past remote interpreter failures are unresolved; this is a new operation, not their
retry or proof of repair. Fresh actual-node admission chooses a suitable destination
without moving any accepted work.

Engineering is a bounded new content/collector integration plus focused tests and one
independent high-risk engineering review. Design, implementation, debugging, review,
publication, output verification and reading cost real effort; no credible measured
engineering-hours estimate exists yet. Current realized cost is 0 fits, 0 environment
steps, 0 policy/critic inferences and 0 optimizer/model-query calls, plus source/literature
reading and documentation. There is no benchmark/pilot prerequisite or automatic repeat.

**Prospective L0, not yet released for implementation:** after the same selection review,
own `experiments/candidates/uav_message_content/b01/` (including its CLI), matching
tests, this NOTES and `runs/uav_message_content/b01_s19431/`. Reuse the unchanged native
host, actor/motion and PPO helpers; add the necessary direction-owned content policy,
payload-capable transport adapter, collector and readable reducer. Do not copy a whole
learner or edit historical CADC/C2 code to retrofit this question. Any unavoidable shared
change is a narrow explicit exception with core review, not implicit direction ownership.

Checks must cover the 171/451 rights, constant original field, anonymous five-tick
moment resets, no future/served truth, exactly seven float32 packet values, delivery
before action, fixed sender/fee and terminal censorship; independent motion/content
streams; tanh density and active/terminal masks; stored-behavior replay; actual gradient
and parameter movement from a synthetic delayed team-return fixture; native reward/service
units; initialization/evaluation isolation; complete counts and adverse reductions;
admission-before-effects and partial-failure preservation. Synthetic checks use disjoint
technical seeds and are correctness tests, not a toy success gate or result pilot.
Tests own scratch under the existing pytest lifecycle. Reviewer gets actual contract,
diff and checks; DM accepts it. No result launch follows before exact-source publication
and existing native admission.

Retain compact config, source/status, all train/eval episode rows, update diagnostics,
initial/final model hashes, group movements, all three signed endpoint comparisons,
and packet/decision exposure counts. Keep initial/final checkpoints and the raw arrays
needed to reconstruct actual received content, eligibility, actions and native per-world
outcomes at one durable hashed direction location. Training storage may remain bounded
to two episodes, while compact per-episode/native measurements are streamed. Do not
replicate C2's bulky text trace or create a retention chain. Output claims and costs
remain explicit if a required diagnostic is missing.

### Primary-source bridge and novelty limits

The three local stores were checked as locating aids: `docs/new-libs/LIBRARY_INDEX.md`
contains P15 on efficient communication; Inst-sci's integrity reports 190 PDFs/190
JSONs with no missing JSON; its title index locates DACOM and related communication
work; the My-lib title index also contains communication-constrained/structured
communication work. Searches of July/external-review text did not identify an old
matching seven-float learned-content experiment; that narrow retrieval is not a novelty
audit or evidence that none exists.

The load-bearing local passage was read directly: **MARL-0006, DACOM**, structured
`/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0006.json`, pages 3-4 and 7
(PDF sibling `pdf/MARL-0006.pdf`). It has local encoders, latest-message buffers,
centralized learning and a learned waiting-time decision; its limitations include
delay-insensitive or low-communication-value tasks. The mapping here is information
compression plus delayed use. Waiting changes action timing in that paper, whereas
our fixed RR actor moves every tick and never waits; its performance does not establish
our host's gain or credit trainability.

Primary publisher/author abstracts read on 2026-09-28:
[SchedNet](https://arxiv.org/abs/1902.01554) jointly learns scheduling, encoding and
actions on scarce media; [TarMAC](https://proceedings.mlr.press/v97/das19a.html)
learns task-reward-driven messages/recipients with multi-round communication;
[CAIC](https://proceedings.mlr.press/v337/li26h.html) studies a shared queue and
trajectory-intent communication under delay. These are established related problems,
not new evidence for this proposal. This design imports neither free multiple rounds,
recipient selection, learned waiting, predictive intent targets nor a changed queue.
The abstract reading is not a full numerical or implementation audit of those papers.

### Selection return

Recommend submitting this three-fit complete native comparison to Root's existing
selection critic. It directly tests an unresolved content/receiver question with a
competent current aggregate and a cheap ordinary history alternative, at much less
simulator work than the recent S7 planner studies. Its main uncertainty is finite
joint code/receiver learning, not a proven missing message channel. The reviewer can
change the ordinary encoding, credit/package design or investment decision; none is
self-cleared here. Retaining C2's RR asset without new training is a real alternative.
Return the review and resolved choice in a later append-only entry. No scientific
result, code retirement or reclaimed-disk claim is made at this design boundary.

## 2026-09-28 - Independent selection adopted; exact B01 implementation released

Root selected the complete C/H/L study after the same independent ResearchCritic read
the committed design. The full answer and Root disposition are published at
`613c8bcfc46f8c31a88f0649ddfdfcfd4f2ed41e` in
[the current programme review](../../RESEARCH.md#portfolio-review-2026-09-28-joint-next-round-programme).
The reviewer reports **MATERIAL_DISSENT: no** and selects this finite purchase.
It independently reconstructs the native sequence and delayed likelihood-ratio credit,
accepts detached *behavior* packets during replay, and stresses that arriving at tick
255 retains a content-learning term while arriving at 256 does not. The pre-draw
central critic is a legal baseline despite incomplete in-flight state. Compound PPO,
four epochs and detached chunk-start states remain finite-learning approximations.

The reviewer accepts C/H together because H's usefulness is unproven and C remains the
competent current aggregate. Separate full receiver/motion training is essential.
It identifies the strongest unresolved objection as learning a useful seven-dimensional
code jointly with changing receivers from noisy delayed team return. Delivery, variation,
parameters or entropy alone do not establish cooperation; no positive pilot resolves
that uncertainty in advance. Its count check agrees with 3 fits, 442,368 native team
steps, 3,072 Adam calls and 7,864,320 replayed actor rows. It accepts the declared
positive, ordinary-only, mixed and technically missing outcome branches without adding
arms, fits, delay regimes, consultations or a frozen-receiver intervention.

DM disposition: adopt this reasoning and Root's selection unchanged. This resolves the
source-only selection dependency, not the empirical uncertainty. In particular,
reported policy entropy uses the inherited **pre-tanh Gaussian entropy convention**;
it is not the bounded transmitted code's differential entropy, information content or
semantic value. Engineering must name that quantity correctly and test its exact mask.

The prospective L0 above is now released as one bounded behavior change: implement the
C/H/L fixed-RR content-plus-motion comparison under the exact declared host, seeds,
information, actions, replay, horizon, learning law and evaluation. Delegate only
`experiments/candidates/uav_message_content/b01/` and mirrored tests in the shared main
checkout to the registered Implementer, with no NOTES/RESEARCH/index/commit ownership,
no result launch and no children. Reuse existing helpers rather than changing frozen
CADC/C2 or shared learner semantics. DM reviews and accepts the diff and checks, and
uses one independent engineering Reviewer for the high-risk likelihood/RNG/replay path.
The required focused tests explicitly include Gaussian-versus-transmitted entropy,
arrival255/256, conditional compound density, private stream/reset state, seven-float
payloads and replay of stored behavior packets. Technical test episodes use disjoint
seeds and are recorded separately from the selected scientific batch.

After implementation acceptance, publish exact inputs and current selected standing,
admit on the actual configured node, execute the one declared batch and keep this native
child active through same-handle observation, complete reading and publication. No
further Root acknowledgment or selection review is due for unchanged execution.
Meaning-changing findings return through the native parent. Independent interpretation
at the actual material result boundary remains distinct from this selection review.

## 2026-09-28 - B01 engineering accepted; exact inputs ready for admission

The registered Implementer produced only the direction-owned B01 package and matching
tests. DM read the full implementation against the selected contract. The independent
engineering Reviewer `/root/dm_message_content/review_content_b01` then reconstructed
the information, likelihood, replay, RNG, evaluation and admission paths and returned
**no material correctness finding**. This is an engineering acceptance, not evidence
that useful content is learnable or that a full native batch will complete.

The reviewer independently checked tanh density against `torch.distributions.Normal`
plus the direct Jacobian, the pre-tanh Gaussian entropy and terminal masks, zero
inactive content gradients, and exactly seven content-stream normal draws per accepted
L send. Its eight synthetic/control tests passed with the native test deselected.
The Implementer's initial nine-test suite had passed, including one separately seeded
technical native environment step (master 99123), not an H256 result episode or fit.
No result-bearing training, evaluation or checkpoint selection has occurred.

Three low-impact follow-ups are accepted after DM inspection: `pending_after_send`
explicitly names the post-enqueue trace while `actor_input` retains pre-send pending;
the batch records process CPU-time delta and Linux process-lifetime peak RSS; and a
new synthetic regression changes the content head after collection, forbids replay
samplers, checks every replay actor input against stored behavior observations and
checks that the current content density is still recomputed. The follow-up suite
passed **9 tests, 1 native test deselected**, adding zero native steps. Synthetic
optimizer calls are correctness-test work, not the three scientific fits. Test scratch
was removed by the existing pytest lifecycle; the reported follow-up path
`temp/directions/uav_message_content/test/content-followup-20260928-a0e560` is absent.

The reset-scene identity field hashes the actual float32 reset observation/global-state
projection. The native reset reconstructs its RNG from the named physical seed; together
these support the declared pairing. This check is not an assertion of native float64
byte identity. Saved per-tick service, Q and physical/net rewards support reconstruction
of the declared outcomes and reward identity; full connection/SINR matrices are not
retained. The code does not re-encode old messages during PPO, and no receiver is frozen.

Selected execution remains sequential C/H/L on the preferred configured `wsl_4070`
CPU interpreter, 3 fits / 442,368 team steps / 3,072 updates, with no pilot, fourth arm
or automatic retry. Its canonical checkout has existing unrelated dirty control/run
files. Preserve every existing hunk: fetch the published source, add only this new
direction's active control row under `.git/hmasd-main-writer.lock`, then use the normal
immutable snapshot launcher and fresh actual-node admission. No sparse-selection change
or whole-checkout reset/pull is required. This native child's observer identity is
`01a0e98a-2ec9-7400-aa22-ce21611bc16d`; keep the same accepted launch and observer through
complete collection and scientific reading. Exact operation metadata belongs in the
native manifest and the following notebook entry, not an invented acceptance claim.

## 2026-09-28 - B01 accepted; same-handle observation active

Inputs were published at `b2a422088a20235e760e3aaebbc74f35236a4e82` before the
result invocation. The native launcher accepted this batch at **20:32:13 UTC**;
[launch manifest](../../../../runs/uav_message_content/b01_s19431/launch-manifest.json)
is the authority for command, source snapshot, process identities and output location.
[Fresh admission](../../../../runs/uav_message_content/b01_s19431/admission-preflight.json)
reported 12,878,118,912 available/effective bytes against the 4 GiB floor while the
independent persistent-service workload was already running. No extra resource or
scientific gate was substituted for runner-side admission.

The first direct non-login remote fetch stalled; only its owned control-fetch process
group was terminated. The configured network login shell then fetched published main
successfully. Its pre-existing auto-GC missing-tree warning remains untouched; it did
not prevent this exact source snapshot or admission. Only the new direction control
row was inserted into remote canonical RESEARCH under the established writer lock,
preserving all other dirty hunks and run files. No result invocation was repeated.

`tools/hmasd_wait.py` generation 1 registered and then **adopted** the manifest's
operation using the request at
`temp/directions/uav_message_content/observe-b01-s19431.json`. The first drained
observation at 20:33:04 UTC found matching live runner/supervisor identities, consistent
records and no exit witness. Registration alone was not treated as adoption. The
controller's initial window is 1,500 seconds, with native long waits in this same
child; checkpoint rearming must retain this handle and never restart the worker.
At this entry the operation is accepted/running, not a completed fit or read result.

<a id="b01-complete-reading"></a>

## 2026-09-28 - B01 complete: own learning, no incremental content-package use

The same accepted operation exited normally at 20:43:14 UTC. Native supervisor and
runner identities are absent, the exit witness is valid, and all three arms and the
fixed reducer report COMPLETE. Full evidence is in the
[native summary](../../../../runs/uav_message_content/b01_s19431/summary.json),
[independent reconstruction](../../../../runs/uav_message_content/b01_s19431/reading.json),
[exit witness](../../../../runs/uav_message_content/b01_s19431/process-exit.json) and
[terminal status](../../../../runs/uav_message_content/b01_s19431/launch-status.json).
Summary SHA256 is `4990300afc69a1710bd5477864942223c7483cdcd69c62e4c52cfd439aa077c4`.
Source remains `b2a422088a20235e760e3aaebbc74f35236a4e82`; no accepted input was changed.

### Complete endpoints and counterexamples

| Arm | Initial net J | Final net J | Initial users/tick | Final users/tick | Final Q |
| --- | ---: | ---: | ---: | ---: | ---: |
| C | .092026527 | .193790299 | 5.310303 | 11.785156 | .099327040 |
| H | .091122761 | .184218540 | 5.251953 | 11.082031 | .100233676 |
| L | .083217925 | .173145014 | 4.815308 | 10.426270 | .093924137 |

| Final contrast | Mean net/physical J difference | Users/tick difference | Q difference | J positive/adverse | Worst J difference |
| --- | ---: | ---: | ---: | ---: | ---: |
| L-H | -.011073526 | -.655762 | -.006309539 | 13 / 19 | -.096925590 |
| L-C | -.020645285 | -1.358887 | -.005402903 | 11 / 21 | -.140907359 |
| H-C | -.009571759 | -.703125 | +.000906636 | 10 / 22 | -.058831061 |

All arms pay .001 per tick, so physical and net J contrasts are identical. L-H service
also has 13 positive/19 adverse worlds, L-C has 11/21, and H-C has 8/24. Quality and
service are not interchangeable: H's mean Q is slightly higher while its service and J
are lower. The reconstruction retains every signed vector and the original per-world
rows, not only these means.

World labels here are zero-based evaluation indices, with physical seed 1943102000+e.
L-C's worst joint loss is world 27: -.140907359 J and -9.464844 users/tick. Its largest
joint gain is world 31: +.095640496 J and +6.316406 users/tick. H-C's world 5 improves
by +.135601212 J and +8.988281 users/tick, even though L-H there loses -.094421967 J
and -6.816406 users/tick. H's largest service loss is world 26 (-4.468750 users/tick);
its worst J is world 30. L-H worlds 13 and 29 have opposite J/service signs. These
favorable cases and tradeoffs rule out a uniform-dominance description.

Each complete trained policy improves its own J and service in **all 32 worlds**.
Mean own-J gains C/H/L are +.101763773/+.093095780/+.089927089; corresponding service
gains are +6.474854/+5.830078/+5.610962 users/tick. Q improves in 31/32, 32/32 and
31/32 worlds respectively. L already began below C/H by -.008808602/-.007904836 net J
and did not close either mean deficit. This is descriptive own-learning evidence;
subtracting initialization is not a causal adjustment that isolates content.

### Exposure, verification and full cost

All 1,728 complete H256 episodes and 3,072 declared Adam calls are present: 3 fits,
1,536 training episodes / 393,216 team steps, 192 initial/final evaluation episodes /
49,152 steps, **442,368 total native calls and returned team steps**, 2,211,840 motion
samples and 7,864,320 replayed actor rows. Evaluation made zero optimizer calls.
There were zero extra planner/model-counterfactual queries. Ordinary native radio
physics still executes at every step. The earlier one-step technical test is separate.

Every arm made 147,456 accepted broadcasts with zero collisions, 145,685 deliveries
and 1,771 terminal-censored packets. L's training comprised 131,072 sampled messages,
**129,511 active send-time content-credit rows**, and 1,561 censored rows. Each of its
initial/final panels had 8,192 sampled messages, 8,087 active arrivals and 105 censored
packets. Thus the intervention was not generally prevented from arriving or entering
the learner. Arrival is an opportunity for receiver action, not proof of useful use.

All three motion/receiver and critic parameter groups had nonzero recorded gradients
on 1,024 updates; L's combined content group did too. Its final mean-weight, mean-bias
and log-standard-deviation norms were .237799481, .015407229 and .056688447, from zero;
final content log std ranged .013375644 to .032558952. These are not gradient-isolated
mechanism measurements: the combined norm includes entropy gradients, and nonzero
mean weights or variable packets do not establish task semantics. Pre-tanh Gaussian
entropy is still not transmitted-code entropy or information value.

The pure NumPy [reader](../../../../experiments/candidates/uav_message_content/read_b01.py)
reconstructed **all 192 saved evaluation trajectories**, including C/H contents from
lawful observations, L tanh samples, RR sender/arrival clocks, pre-action receiver
records and pending flags, post-send pending, terminal masks, physical/net reward,
service/Q and per-world reductions. Checkpoints and all stable retained artifacts were
hashed. Common reset projections and channel sequences matched across arms and across
each arm's initial/final panel; common initial motion/receiver and critic tensors match.
No policy, model or environment was called during this readback. The independent
scientific reader separately read all 192 remote traces with NumPy and reproduced the
endpoints and delivery counts. Neither audit generated new experimental episodes.

The first inventory also hashed `launch-status.json`; a later native status observation
legitimately changed its observation timestamp. Stable source/result hashes matched.
The retained reader explicitly excludes that refreshable status file from its stable
inventory, and the derived readback was regenerated without changing any native data.
Reset hashes certify float32 observation/global-state projections, not underlying
float64 byte identity. The documented deterministic reset and seed bindings support
pairing; no full SINR/connection matrix or semantic-information estimator was added.

Measured batch wall was **658.466101 s** (10.9744 min), self CPU delta 657.742051 s,
and Linux process-lifetime high-water RSS **536,976 KiB** (524.390625 MiB), including
the sequential arms, evaluation and writing. Arm walls C/H/L were 217.117890,
212.911188 and 228.334944 s. No engineering/review/audit-hours measurement was made.
All unique compressed raw traces, initial/final checkpoints and update streams stay
at the manifest's `wsl_4070` output path, with hashes/byte counts in the reconstruction;
no duplicate bulk copy, retention chain or tarball was created. Compact summary,
readback, source/status and outcome records are published on main.
The stable inventory has 213 artifacts / 47,850,516 logical bytes, excluding the
refreshable status and derived reader output. Collected stable files match their node
hashes; remote/local reconstruction SHA256 is
`6e1dc44b2300e9d8c7ab85f3135806530b6034a8e65f310f3fad28cb2fd4b869`.

Observer generation 1 saw the exit at 20:43:17 UTC. Its delivery was recorded as
`delivery_unknown`: App queue rejected direct input for an unloaded spawned child
with code -32600, despite the DM retaining a long active native wait. After the
900-second deterministic wait this same child drained the terminal evidence, collected
the outputs and stopped its observer; PID 1391486 is absent. No launch, Send, source
binding or observer owner was replaced. This is a delivery limitation, not lost work.

### Independent scientific reading and DM disposition

The registered ResearchCritic `/root/dm_message_content/read_content_b01` received no
DM/Root conversation inheritance. It reconstructed protocol and results before reading
the prior selection advice, then read the whole native evaluation evidence. Its full
recommendation is **retain C and stop unchanged L-recipe expansion**, with
**MATERIAL_DISSENT: no** and no technical missingness preventing the fixed endpoint
reading. I adopt that recommendation. This is an investment decision at the selected
boundary, not a claim of general learned-content inferiority.

The explanation changes at four distinct levels. The useful RR opportunity in old C2
is unchanged and was not a prediction that every replacement packet improves service.
The proposed H persistence/spread representation did not add mean complete use in this
block; C already includes trained recurrent receivers, and H adds weighted anonymous
sightings, not persistent user identities or served-demand truth. L had real delayed
credit exposure and mean-parameter updates, but semantic learnability was not measured.
At complete-package level neither replacement earned reuse over C at the frozen budget.

The strongest ordinary explanation is that the current interpretable aggregate plus
trained recurrent motion extracts more usable value at this budget. Equal rights and
seven floats do not make the finite C/H/L learners nested or equivalent: L replaces
interpretable fields with a noisy, jointly learned convention. Finite optimization and
receiver co-adaptation remain plausible alternatives to limited incremental information
opportunity; B01 separates neither. The critic's descriptive height/boundary differences
are consequences of different motion policies, not identified causes or energy evidence.
It rejects both "content cannot help" and "optimization failed, so train longer/reduce
noise" as unsupported conclusions. Packet dependence, semantic information and recurrence
over independent training instances remain open, not reasons to erase the adverse result.

No further observation is necessary for the present no-switch choice. The reviewer
notes that packet scrambling would measure this receiver's dependence/distribution
shift and would not by itself reverse the measured C preference. No targeted repair
has a supported intermediate-plus-native prediction here. No seed, epoch, mean-message
evaluation, arm or delay change is selected. This result also does not independently
replicate CADC scheduling or C2 fixed-receiver request deletion.

For a future consequential recurrence question, the critic would consider one newly
specified complete C/H/L training block, retaining this evaluation panel and all three
endpoints: another 3 fits / 442,368 steps / 3,072 updates. Repeated L losses would
strengthen the finite-recipe constraint; L beating both baselines would expose
training-instance sensitivity; mixed ordering would leave stable preference unresolved.
It explicitly does **not** recommend buying that block now. Root's later peer disposition
at `6a4386526` likewise preserves Claude's optional three-training-instances-per-arm
precision suggestion only for a future material replication/claim decision, not this
completed batch. Additional evaluation worlds would not create independent training
replication. Any such continuation needs a fresh prospective
question, seed binding, cost and actual-node admission; there is no current dependency
on an owner acknowledgment and no queued successor.

Current decision: retain the original C aggregate as the incumbent comparator; end
this stochastic L and five-tick H package's additional investment, and place the broader
content question in reserve. Keep all favorable/adverse evidence, the ordinary learning
result and the primary-source novelty limits. There is no active producer, unread
result, open Pro request or automatically selected repair. Publish this bounded reading
and directly affected shared background, then retire unused entrypoints/tests/scratch
and the disposable source snapshot while retaining the unique evidence and pure reader.

## 2026-09-28 - Published result and lifecycle retirement complete

The complete result, independent disposition and directly affected communication
background were published at `3567e73b0` before retirement. Searches of experimental,
script, test, tool and control imports found no live consumer outside this study;
both bounded helpers and the scientific reader had returned, the native worker had
exited and the observer process was absent. The ordinary CADC/C2 implementations and
all other directions' files remain untouched. The B01 runner/tests are now historical
[source at b2a422088](https://github.com/CartmanFatass/My-paper-code/tree/b2a422088a20235e760e3aaebbc74f35236a4e82/experiments/candidates/uav_message_content/b01),
not an installed active experiment. The pure readback utility remains on main.

The snapshot collector's initial preview refused the protected `/proc/660/cwd` read
with Permission denied and requested `--sudo-process-scan`. The documented read-only
privileged process probe then passed; ordinary-user collection rechecked the terminal
claim, source cleanliness, durable Git reachability and absent consumers and removed
only snapshot `b064af76c39c490da655ba4a39b3f62b`.
[Native removal record](../../../../runs/uav_message_content/b01_s19431/source-retirement.json)
reports `eligible: true` and `removed: true`. No claim, manifest, output, authoring
checkout or foreign snapshot was removed. The unrelated pre-existing node Git auto-GC
warning was not repaired or used as a reason to retain this disposable copy.

Measured allocated bytes before exact-target deletion (`du -B1 -s`), with zero bytes
remaining at each target after absence checks:

| Node | Removed target | Before bytes | After bytes |
| --- | --- | ---: | ---: |
| local | `experiments/candidates/uav_message_content/b01/` | 94,208 | 0 |
| local | `tests/experiments/candidates/uav_message_content/` | 69,632 | 0 |
| local | `temp/directions/uav_message_content/` | 20,480 | 0 |
| wsl_4070 | `.git/hmasd-launch-sources/b064af76c39c490da655ba4a39b3f62b/` | 801,361,920 | 0 |
| wsl_4070 | `temp/directions/uav_message_content/` | 24,576 | 0 |

Net reduction across these retired paths is **801,570,816 allocated bytes**. This is
target-directory space, not a claim about Git object storage or the host volume's
total free-space change. No archive or duplicate retention package was created.
All **213 stable evidence artifacts / 47,850,516 logical bytes** were rehashed again
at the original node output after cleanup and still match; the reconstruction hash
also remains unchanged. The unique raw/checkpoint/update copy, native recovery records,
published compact evidence and pure reader are intentional retained evidence, not a
cleanup blocker. No owned target or concrete cleanup refusal remains unresolved.

Remote canonical control was narrowly synchronized to the published `reserve` state
under its established writer lock, preserving the other sessions' dirty hunks. The
broader scientific question remains open, with C retained and no selected next fit,
diagnostic, producer, unread output, Pro operation or acknowledgment dependency. Return
this fully read boundary to Root for project-level allocation; do not infer permission
to run the optional replication alternative or restore an archived predecessor.

<a id="b02-preserved-content-prospective"></a>

## 2026-09-29 - B02 preserved-content continuation: prospective comparison and L0

Root assigned this question to fresh native DM `/root/dm_content_augmentation` after
the previous DM completed its result and retirement. The authoring checkout remains
shared main at `/home/fires/hmasd-wsl`; the new DM owns the same direction paths and
inherits the evidence, not the completed runtime or any operation. The owner requested
that Codex progress the two constructive questions while Claude independently selects
two others. Root is publishing the initial active standing/routing. No B02 result has
started, and this entry does not change any other direction or owner pause.

The question is whether extra private-history content, while preserving C's useful
six packet fields, improves complete native J/service beyond continued C and a
competent ordinary scalar. The contribution sought is conditional empirical/task
understanding, not an architecture novelty or confirmation claim. The original B01
summary and reconstruction were read directly along with this complete notebook.
All three old arms learned their own useful behavior; L-C was -.020645285 J and
-1.358886719 users/tick, including 11 positive/21 adverse worlds. L had 129511 train
credit rows and mean-head updates. Neither nonactivation nor co-adaptation is an
established explanation. H changed several fields, so its adverse result does not
answer this preserved-field comparison.

Published RESEARCH at `12c70a7b128ccc89b50be0357b9cb7fe150a6478`, especially
[topic 5](../../RESEARCH.md#5-技能和异步性是组织决策的方式其收益需要证据) and
[topic 8](../../RESEARCH.md#8-数学信息与博弈结构怎样帮助dm选择实验), supplies three
concrete design constraints: keep the demonstrably useful RR process; compare finite
trained packages rather than infer a nonnegative value-of-information theorem; and
treat the continuation instance as the unit, not its evaluation worlds. The full
[constructive review](../../archive/2026-09-28/RESEARCH-constructive-exploration-method.md)
(`ae35487d0`, disposition `1d65ea4ca`, retirement `6f1a850a0`) already selects preserved
six fields, blank/ordinary/learned scalar and a common retained C start. Its illustrative
three-fit count was not an allowance. This study uses three continuation seeds per
arm to observe previously unmeasured continuation variability. A focused independent
scientific follow-up covers the concrete scalar and initial-function preservation below;
it does not repeat question selection or add a positive-pilot gate.

### Bound starting point and decision interface

The actual retained checkpoint was read and hashed on `wsl_4070` on 2026-09-29:
`/home/wu/projects/HMASD/runs/uav_message_content/b01_s19431/C/final.pt`,
463293 bytes, SHA256
`456832faaa94afb22cf3faa00bb97b0f129e2f5b72b2eedbb1148523b088cdad`.
Its source is `b2a422088a20235e760e3aaebbc74f35236a4e82`; keys are actor, critic,
arm C, master19431, input_size171 and critic_size451. No Adam, RNG or recurrent state
was retained. Therefore all arms load the exact actor/critic parameters, create fresh
identical Adam states, start new independent continuation RNG streams and reset private
GRU/channel/sighting state each episode. No normalization state exists. The five shared
CADC/UCOPE dependency modules are unchanged from that source. The runner checks the
external checkpoint digest before loading; no duplicate bulk source is required.

The N5/H256/50-static-user native host, reward, 171/451 actor/critic information,
seven-float RR channel, one/five-tick send-time delay, .001 fee, sampled motion,
episode termination and four-epoch recurrent PPO law remain as specified for B01.
All arms keep C payload indices 0,1,2 (sender xyz), 3,4 (current visible centroid xy)
and 6 (current visible count/20) exactly. Only the constant centroid-z index 5 changes:

| Arm | Slot 5 | Trained parameters |
| --- | --- | --- |
| B | Zero, the continued C packet. | Full common receiver/motion and critic. |
| O | Five-observation anonymous visible-demand RMS spread, normalized to [0,1]. | Full common receiver/motion and critic. |
| L | `(1+tanh(u))/2`, one sampled scalar from the sender's private GRU64. | Same receiver/motion/critic plus 66 content-head/log-std parameters. |

For O, reconstruct normalized absolute xy from valid local rows, pool sufficient
moments over the last up-to-five observations, and send
`sqrt(2*max(E[||xy||^2]-||E[xy]||^2,0))`, clipped only for roundoff to [0,1]. Empty
history gives zero. This is weighted anonymous sightings, not distinct user identity,
unserved demand, connection ownership or future truth. Five ticks matches RR period
and maximum transit, chosen without outcome tuning. At equal centroid/count, spread
can change how useful one shared target is for coverage. The receiver must learn that
response. L has the same lawful information rights but can encode other context from
its existing private history; no forecast, intention commitment or synthetic target is
provided. Its new linear mean weights/bias and log_std start at zero. The affine-tanh
density includes its constant Jacobian; entropy remains explicitly pre-tanh Gaussian.

To preserve the starting C function, zero the incoming spare-coordinate columns in
both actor encoder paths (`126+10*s`, s=0..4) and critic first layer
(`154+63*i+10*s`, i,s=0..4), identically in B/O/L. Every such column previously
multiplied a structural zero. All other checkpoint tensors stay exact. This leaves
the architecture and future trainability unchanged while initially ignoring the new
scalar. Source algebra, synthetic sequence checks and the declared initial panels
must verify the claimed invariance; six preserved fields alone would not establish it.
This construction does not diagnose why B01 L lost. The first rollout has no true
task benefit from the new scalar; finite noisy joint learning remains an open difficulty.

Only the scheduled RR sender samples L's scalar using its private content RNG; motion
RNG consumption is unchanged. A send arriving before H contributes its one-dimensional
content log density to that sender's compound PPO term, with the original native
return advantage. Arrivals at 255 are active, arrivals at 256 are censored. Replay
uses actual behavior packets and detached chunk-start hidden states, not re-encoded
packets or differentiation through the simulator. The inherited approximation and
extra entropy/global clipping remain part of the L package, not isolated semantics.

### Predictions, exposure and reading

Prediction: equal starting policies, then learnable response to the added scalar,
followed by positive complete-task J/service differences. Read initial/final local
response by one extra actor forward at the same actual pre-step hidden state, with
only received slot-5 inputs zeroed; record bounded motion-mean RMS/max differences.
This adds no environment step and is a diagnostic of immediate input sensitivity,
not a counterfactual episode, full historical dependence or causal information value.
Its expected initial value is zero in all arms. Nonzero final response, delivery or
head movement without native improvement fails the useful-package prediction.

Freeze continuation masters **19451, 19452, 19453**, paired B/O/L within each master.
Train worlds/channel use `100000*master+1000+e` / `+6000+e`, e=0..511; continuous
motion/content streams use `+21/+22`. Head construction uses `+12` without consuming
motion or training RNG. All nine initial/final panels use the same new 32 worlds:
physical `1945002000+e`, channel `1945007000+e`, motion `1945003000+e`, content
`1945004000+e`, e=0..31. Train and evaluation states/RNG are isolated. No old B01
evaluation panel is reused and no checkpoint is selected by a score. Execute master
order then B/O/L, final endpoint after exactly 512 H256 training episodes per fit.

Read L-B, L-O and O-B complete net/physical J, served users/tick and Q, paired world
vectors and adverse extremes, plus each arm's own continuation. Report all three
continuation-seed means and differences; their shared initial C makes the estimand
conditional, not three independent C trainings. World variation is nested. A t-based
interval across three seed contrasts (df2) is descriptive and explicitly assumption
dependent, not a confirmation/p-value/equivalence result. Native host has no energy
failure metric: retain boundary/height fractions, lowest service and adverse J/service
worlds as behavioral/tail facts without calling them physical safety validation.

L exceeding both B and O in complete J/service supports a conditional learned-package
increment; O exceeding B with no L increment supports an ordinary content capability.
L beating only O while O loses to B gives no reuse case. Mixed seed signs, J/service
tradeoffs or adverse tails remain explicit. Sensitivity or own learning alone cannot
rescue the endpoint. Missing comparisons stay technical missingness. No outcome adds
seeds, epochs, an arm, deterministic evaluation or a new delay regime to this batch.

### Prospective cost and implementation scope

Nine new conditional fits: 4608 train episodes / **1179648 train steps**, 576 initial
and final eval episodes / **147456 eval steps**, **1327104 team steps total**,
**9216 Adam updates**, 23592960 replayed actor rows and 6635520 motion samples.
The local-response diagnostic adds 147456 batch-of-five actor forwards across all
initial/final panels, zero native steps/updates. No planner/suffix/model search occurs.
All arms keep their required packet/delivery/credit counts and complete sampled panel.
Inherited C separately cost one fit / 131072 train steps / 1024 updates plus 16384
eval steps. Each final policy has that common training plus its declared continuation.
The full preceding C/H/L study cost three fits / 442368 steps / 3072 updates; cumulative
direction cost after complete B02 would be 12 started fits / 1769472 steps / 12288
updates, without counting duplicated C inheritance nine times as new compute.

The original whole three-arm batch cost 658.466 s wall, 657.742 self-CPU s and
524.391 MiB lifetime RSS. Old-rate extrapolation for nine fits is **about 33 min total**,
before changed diagnostic/serialization/engineering work; it is neither 11 min per arm
nor a guaranteed new rate. Plan sequential CPU FP32, one Torch/inter-op/BLAS thread on
the retained-checkpoint node `wsl_4070`, subject to fresh actual-node admission. No
resource-pricing probe or native pilot is needed; wall/RSS are measured by the batch.
Engineering/review/publication/readback effort has no credible hours estimate yet.

L0: narrowly recover the required retired B01 collector/channel/model/study/entry
logic from the pinned source into new `experiments/candidates/uav_message_content/b02/`
and mirrored tests. Reuse unchanged CADC/UCOPE helpers; do not restore B01, copy shared
learners, alter the native host or edit shared modules. Implement exactly the three
scalar arms, common digest-bound C initialization, matched seed/exposure/replay path,
compact per-seed/per-world endpoint and diagnostic records, raw traces/update streams
and initial/final checkpoint hashes. Use admitted CLI entry `b02/run.py`; write to
`runs/uav_message_content/b02_preserved_scalar/`. Keep bulk in one durable node copy,
publish compact config/summary/source/status and an independently usable pure reader.

Correctness checks: six unchanged fields and index5; lawful spread moments/window
reset; initial sequence/function invariance; exact checkpoint state/digest; single
scalar affine density and terminal masks; detached behavior-packet replay; independent
RNG streams and no evaluation updates; count/reduction and partial failure retention;
native reward units; admission before model loading/results. Use synthetic fixtures
and tests-managed scratch, no hidden native scientific pilots. Registered Implementer
may own only B02 code/tests, no NOTES/index/commit/launch or children; the DM accepts
its diff. Independent engineering Reviewer checks numerics/RNG/replay/warm start.
Substantial implementation follows resolution of the focused scalar/initialization
review. Publish exact inputs, admit once, keep this child active through the same
operation's deterministic observation, complete reading and independent interpretation.

### Focused scientific review and adopted refinement

The registered ResearchCritic `/root/dm_content_augmentation/content_contract_review`
used `fork_turns=none`, reconstructed the original summary/frozen source, reread all
192 retained B01 trajectories on the actual node and independently verified the C
checkpoint. Its recommendation is **retain the complete B/O/L nine-fit comparison**,
with **MATERIAL_DISSENT: no**. It received the proposed contract, so this was a
separate-context contract review, not blinded selection. No policy or environment
was called during its original-evidence reconstruction.

The reviewer retains both the competent ordinary C learning and the adverse B01
replacement results, including L-C world31 +.0956405 and world27 -.1409074. It agrees
that prior H did not test O, and that changing constant-input columns in both actor
paths and critic preserves the original function only at initialization. Fresh Adam
and reset histories are appropriate to the retained checkpoint. The spread has valid
unit-square normalization and lawful anonymous inputs, but is not an optimal encoding
or unserved-demand signal. Delayed behavior-message score credit remains meaningful;
the initial scalar is ignored, and neither gradients nor sensitivity guarantee later
native value. Thus the actual design is suitable for direct complete learning without
another arm, pilot or scientific review before implementation.

Its consequential limitation is adopted: even L>B and L>O would support a learned
**package** increment, not identify private-history semantics. Immediate sensitivity
can reflect an offset or shared randomness; zero sensitivity at actual hidden states
cannot exclude an earlier message effect already carried in recurrent memory. The
diagnostic must not become a causal-information metric or exposure admission gate.

The reviewer adds a useful adoption comparison already supplied by our initial panel:
read the trained endpoint against the common uncontinued C. If L improves J/service
over B/O **and initial C**, retain a conditional useful augmentation; independently
trained C starts are a possible later purchase when generality matters. If L only
beats deteriorated B/O and stays below initial C, keep the relative continuation
observation while retaining uncontinued C for use. If O improves over B and initial C
without an L increment, keep the ordinary capability. If neither augmentation gives
complete useful benefit, retain C/B according to their measured endpoints and stop
automatic extension. Mixed seeds, opposite J/service signs and adverse tails remain
visible in every branch; none automatically buys a repair or new seed.

DM disposition: adopt this substantive recommendation and refine the reuse reading
accordingly, with no added native work or comparator arm. The question remains open
at the task/representation/finite-learning levels, but this batch has an explicit
use decision. The review verifies neither new code nor runtime; those engineering
checks, exact-source publication and fresh actual-node admission still remain.
Release the L0 above to the registered Implementer for the single preserved-content
continuation behavior. DM owns this notebook, the separate pure reader and final
acceptance; helper owns only B02 implementation/tests and performs no Git mutation.

### Engineering acceptance and source publication

The bounded Implementer returned six B02 modules and its six synthetic checks. DM
reviewed and accepted the diff; no shared scientific module or native host changed.
The separate pure reader reconstructs packets, delivery records, delayed masks,
native rewards, exact initial action/reward equality, paired endpoints and counts
from retained arrays/streams without calling a policy or environment. Its four
synthetic checks include complete B/O/L protocol traces and rejection of an altered
preserved field even after refreshing the trace digest. These are correctness
fixtures, not native scientific probes.

Registered engineering Reviewer `/root/dm_content_augmentation/review_content_b02`
independently read the checkpoint, both actor input paths, critic offsets, scalar
density, private RNG, behavior-message replay, diagnostic state handling, counts,
partial-failure frontier and admission order. It found no material engineering
issue and requested no repair. Its original seven checks passed in 5.11 s; after
the additional complete-trace fixtures its four reader checks passed in 5.42 s
(ten distinct checks across the two files). It also verified unchanged shared
CADC/UCOPE dependencies and native environment/adapter against the pinned B01
source. No native episode or new training occurred during engineering review.

DM accepts this implementation and the reviewed comparison for exact-source
publication. The actual retained checkpoint was separately hash/metadata-verified
on `wsl_4070` by the read-only source Scout; production loading rechecks those bytes.
The complete reader can only be accepted against native retained outputs after
the admitted batch finishes. No scientific completion is asserted by these tests.

### Pre-admission external-input binding correction

Published implementation `e3ea2b10a88929b428abca48f88d0e92aff5b436` was invoked once
through configured `agent-task` task `uav-content-b02-e3ea2b10a` at 2026-09-29
04:34:15 UTC. The launcher refused before claim/output/native effects: absolute
author-tree input `runs/uav_message_content/b01_s19431/C/final.pt` is not a tracked
source-snapshot file. Same-output status confirms the run directory does not exist.
This is an input-preparation refusal, not an incomplete scientific fit or accepted
operation eligible for retry. The source-only snapshot is recorded for later GC.

Correction: stage the same 463293 checkpoint bytes, SHA256
`456832faaa94afb22cf3faa00bb97b0f129e2f5b72b2eedbb1148523b088cdad`, in the node's
configured external-input root at
`/home/wu/hmasd-inputs/uav_message_content-b02-C-456832fa.pt`. Keep the canonical
B01 checkpoint unchanged, bind this staging path in the CLI, and hash the bytes again
inside the admitted runner. This changes input location only, not model state,
information rights, RNG, horizon or any scientific comparison. The 463293-byte
temporary input duplicate will be removed after reading; the original canonical
checkpoint remains the durable evidence. Publish this narrow correction before
the first admitted scientific run. No shared launcher or control contract is changed.
The pure reader verifies the durable canonical B01 checkpoint against the same hash,
records that location, and does not require the disposable staging copy to survive.
All ten synthetic checks passed together in 7.60 s after the CLI path correction.

### Accepted B02 operation and deterministic observation

The corrected exact source is `02ede8a4a75cc83e6e18d8b6619f1cfa84bc8d92`.
Independent engineering follow-up found no material issue in the input-location
correction; fixed digest, admission order, launch identity and numerical path remain
unchanged. The configured supervisor task `uav-content-b02-02ede8a4a` invoked the
launcher once; **native acceptance was 2026-09-29 04:36:49 UTC**. The supervisor's
command completion is not the scientific runner's completion.

[Native manifest](../../../../runs/uav_message_content/b02_preserved_scalar/launch-manifest.json)
binds claim `15a68a5875aea6af7216bb125efd5593469102355af49f6d8b04001f19df1514`,
source snapshot `a4c43170c0d446b3a002d8b66608660e`, supervisor PID964204 and runner
PID964205 with boot/start identities. Durable outputs are under
`wsl_4070:/home/wu/projects/HMASD/runs/uav_message_content/b02_preserved_scalar/`.
[Fresh actual-node admission](../../../../runs/uav_message_content/b02_preserved_scalar/admission-preflight.json)
measured 12967636992 available/effective bytes against the 4294967296-byte floor.

`tools/hmasd_wait.py` generation1 is registered under this native child's identity
`01a0eb55-63aa-7242-b5ec-1e16b98e58dc`, using the read-only same-claim request
`temp/directions/uav_message_content/observe-b02-preserved-scalar.json`, window1500s.
The first request omitted the required absolute `/usr/bin/ssh` executable and was
rejected before observer registration; correcting that probe does not affect the
scientific operation. Drain at 04:37:23 UTC confirmed adoption: accepted admission,
matching live runner/supervisor identities, consistent records and no exit witness.
Keep this native child active with long deterministic waits; rearm only this same
handle if the observation window ends. No additional native work is selected.

### B02 terminal collection and pure-reader correction

Generation1 reached its deterministic checkpoint while the same operation was live;
native queue delivery returned code -32600 for the spawned child. The active child
drained it, consumed event `ebe3f0c9d7397378618fb27c` and rearmed generation2 on the
same claim, without restarting work. At the later deterministic drain, generation2
reported terminal READY: native runner exit0 at **2026-09-29 05:10:02 UTC**,
consistent records and both runner/supervisor absent. The READY event
`6fd3f21f5a69a308c0b8745d` was consumed and observation stopped after collection.
Queue delivery again rejected an unloaded-child address; no reliance on a future
queue wake or migration was introduced. All nine fixed cells report COMPLETE,
1327104 native team steps and 9216 optimizer updates. Scientific reading follows;
the normal exit alone does not validate the result.

The original frozen pure reader stopped on a behavioral boundary fraction:
logged .46015625 versus reconstructed .4609375, exactly one of 1280 UAV ticks.
This was reproduced as reader arithmetic, not inferred from the error alone:
`float32(1-2**-23)` is .9999998807907104 and its distance to one is
1.1920928955078125e-7. The runner's `isclose(..., atol=1e-7, rtol=0)` correctly
excludes it. The reader's `float32_array >= 1-1e-7` rounded that threshold back to
float32 and incorrectly included it. The pure reader now evaluates absolute
boundary distances in float64, retaining the exact 1e-7 criterion. A focused
synthetic boundary regression plus four previous reader checks passed in 5.26 s.
No tolerance was widened, native data edited, model called or scientific fit added.
The new reading records its reader source-file hash; independent engineering
review of this correction precedes final acceptance of the native reconstruction.
That independent check identified the companion near-zero edge: NumPy's float32
distance comparison represents atol1e-7 as `float32(1e-7)`, slightly above decimal
1e-7. The corrected independent calculation therefore uses exact float64 distances
and the runner's represented float32 tolerance; it does not change the nominal
criterion. The regression includes that exact coordinate and its next larger
float32 neighbor, as well as both near-one cases. Original native rows stay intact.
Independent engineering follow-up verified both boundaries and adjacent representable
values, ran the five reader checks in 5.63 s, and found the remaining issue resolved.
DM accepts the reader-only repair for a second pure read of the same retained data.

<a id="b02-complete-reading"></a>
## 2026-09-28 PDT - B02 complete: positive sample means, unstable continuation ranking

The corrected pure reader from `d08e1becb33aa44d29d61ef2cacc80ecfc626110`
completed with **all_checks_passed=true**. Its source-file SHA256 is
`16a47388ff2e4872be0fb2aeb4fcd38f06970f5c3025d262a0d516782f35ba15`.
[Original summary](../../../../runs/uav_message_content/b02_preserved_scalar/summary.json)
has SHA256 `c0d747a4bf0ff47f2eef225378e4c2888ab96339786728a6c1cd93d14db993be`;
[complete reconstruction](../../../../runs/uav_message_content/b02_preserved_scalar/reading.json)
has SHA256 `53e8d186ed533f8e8d69b3379395459b0bdf81763808e43d2c5820b43e6b1889`.
Local and remote compact-file hashes agree. The source snapshot used by native
training remains the unchanged `02ede8a4a75cc83e6e18d8b6619f1cfa84bc8d92`.

The reader checked all 576 eval NPZs, all nine 576-episode streams, all nine
1024-update streams and all 18 initial/final checkpoints. It independently rebuilt
six preserved packet fields, O's sighting spread, L's affine-tanh scalar, record
delivery timing/pending state, terminal credit, action transforms, native rewards,
behavioral readings and all declared seeds/counts. Every initial action and reward
sequence is identical across all nine cells; initial scalar response is exactly
zero, and B remains zero. This supports the prospective initial-preservation claim
on the complete declared panel, not receiver invariance after learning.

All arms share the new-panel initial C endpoint: net J .181825659, physical J
.182825659, service10.956542969 users/tick and Q .098113526. Its difference from the
old B01 .193790 net J is a different evaluation panel, not checkpoint degradation.
The fee is .001/tick in every row, so physical J is net J plus .001 and paired
physical/net differences coincide. Q is the host's clipped served-link SINR quality,
not a service count or an energy measure.

| Continuation | Arm | Final net J | Users/tick | Q | J change from initial C | Service change |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 19451 | B | .236163 | 14.164185 | .129548 | +.054337 | +3.207642 |
| 19451 | O | .152227 | 8.533203 | .112539 | -.029599 | -2.423340 |
| 19451 | L | .213626 | 12.356812 | .138770 | +.031801 | +1.400269 |
| 19452 | B | .122788 | 6.503784 | .109117 | -.059038 | -4.452759 |
| 19452 | O | .241901 | 14.622070 | .127305 | +.060075 | +3.665527 |
| 19452 | L | .218227 | 12.929199 | .127394 | +.036401 | +1.972656 |
| 19453 | B | .202452 | 11.638062 | .135065 | +.020627 | +.681519 |
| 19453 | O | .172077 | 9.835083 | .117954 | -.009748 | -1.121460 |
| 19453 | L | .173410 | 8.929932 | .164636 | -.008416 | -2.026611 |

| Contrast | 19451 J / service | 19452 J / service | 19453 J / service | Mean J / service |
| --- | ---: | ---: | ---: | ---: |
| L-B | -.022537 / -1.807373 | +.095439 / +6.425415 | -.029043 / -2.708130 | +.014620 / +.636637 |
| L-O | +.061400 / +3.823608 | -.023674 / -1.692871 | +.001333 / -.905151 | +.013020 / +.408529 |
| O-B | -.083936 / -5.630981 | +.119112 / +8.118286 | -.030375 / -1.802979 | +.001600 / +.228109 |

These positive L sample means are retained as favorable exploratory evidence,
including mean L-initialC +.019929 J / +.448771 users/tick. Mixed seed signs are
not a post-hoc unanimity requirement or proof of zero effect. They do show the
uncertainty that the three conditional continuations were purchased to expose:
L-B J SD .070067 versus mean .014620, descriptive df2 t interval
[-.159436,.188676]; L-O SD .043724, interval[-.095597,.121636]. Corresponding
service intervals are [-11.867067,13.140342] and [-7.003284,7.820341]. The intervals
assume independent continuation contrasts and are not confirmation or equivalence
tests. Worlds and steps are not extra training instances. No seed's L endpoint
beats both B and O on both J and service; this is a description, not a new gate.

All signed world vectors remain in reading.json. L-B has respectively10/22,
30/2 and9/23 positive/adverse J worlds. In seed19451 world29 is +.133113 and
world13 -.122551; seed19452 world16 is +.174924 and world15 -.010325;
seed19453 world17 is +.076594 and world15 -.111086. O-B seed19452 improves J
in32/32 worlds, while O-B seed19451 loses in31/32 and reaches -.210398 onworld31.
These nested counts describe the evaluated policies, not 32 replications of training.
L-O seed19453's positive J with negative service is a real tradeoff: Q +.046682
offsets service -.905151. L's Q exceeds both B/O in all three seed means, but the
complete service objective does not inherit that sign.

### Exposure and explanation update

L received129532/129508/129526 actual training content-credit rows and each content
head had nonzero gradient norm in all1024 updates. Head displacements were
.093574/.155626/.208739 from the declared zero mean/log-std initialization.
Final local-response RMS averaged over worlds was .016332/.004699/.016487 for L,
and .002582/.003796/.005273 for O, versus exactly0 for B. L's per-world maximum
response reached .118318/.024418/.116073. O's transmitted means were
.058210/.097424/.063982; L's were .511794/.416220/.359629. Both use[0,1], but
their realized scales differ; larger response alone is not stronger information.

Thus initial functional preservation and later learned input response were observed.
The intended robust complete-task advantage is not established at this conditional
sample size, despite favorable mean differences. A blanket unactivated-message or
missing-gradient explanation is weakened directly. Local sensitivity, stochastic
offsets/shared randomness and learned private-history semantics remain distinct;
no semantic identification was obtained. Ordinary continuation itself can improve
or damage C substantially, so altered optimization/trajectory selection remains a
strong simpler explanation of the ranking. This does not identify why B01 full
replacement L lost, nor establish that extra history lacks task opportunity.

Behavioral endpoints also differ: final boundary fractions B .163/.501/.502,
O .462/.282/.431 and L .539/.184/.733; floor fractions B .746/.886/.833,
O .925/.553/.071 and L .423/.854/.534. O19453 has ceiling fraction .279 and
mean height116.631m; other final mean heights are52.393--67.738m. These preserve
behavioral risk descriptions on this no-energy host, not proof of physical safety,
cutoff avoidance or energy feasibility. All exact per-world readings remain retained.

### Measured cost and durable evidence

Nine fits consumed1179648 training +147456 evaluation =1327104 native team steps,
9216 optimizer steps,23592960 replayed actor rows and6635520 motion samples.
The diagnostic added147456 actor forwards and zero environment steps/updates.
There were4608 training episodes,288 initial and288 final eval episodes; all
evaluation optimizer counts are0. Actual batch wall time was1991.281666s
(33.188min total), self user+system CPU1989.353298s, process-lifetime peak RSS
535432KiB (522.883MiB), one intra-op/inter-op thread. This closely matches the
old-rate total estimate; it is not a per-arm timing. Engineering, both pure reads
and independent reviews are additional work, without a complete measured time sum.

Inherited C training remains one common131072-step/1024-update fit plus its old
16384 eval steps, not nine new inherited fits. Including the entire original
three-arm selection batch, cumulative direction cost is12 fits,1769472 native
steps and12288 optimizer steps,2649.747767s measured scientific wall and
2647.095349s self CPU. The pre-admission refusal added0 fits/steps/updates.

One durable native copy remains at
`wsl_4070:/home/wu/projects/HMASD/runs/uav_message_content/b02_preserved_scalar/`.
The reader inventories627 stable files totaling135657594 logical bytes, with
per-file hashes, excluding reading.json itself(667217 bytes) and mutable
launch-status.json(603 bytes). These contain the576 compressed unique traces,
all18 checkpoints and all episode/update streams. Retain all positive/adverse
outcomes and the original B01 evidence. Compact source/summary/native status and
reading are published locally; no bulk duplication or retention archive is needed.

### Independent final reading and resolved investment

Registered ResearchCritic `/root/dm_content_augmentation/read_content_b02` worked in
a separate context with no DM/Root conversation inheritance. Before reading earlier
interpretations, it independently reconstructed all576 original NPZs, all nine
episode/update streams, all18 checkpoints and the retained C identity. Native
endpoint errors were at most2.8e-16; its original `isclose` behavioral reconstruction
matched exactly. It independently verified the initial action equality and active
learning, including nonzero immediate L sensitivity on about98.88% of final ticks.
It confirms the pure-reader arithmetic issue was separate from native execution.

The review recommends preserving favorable L sample means while ending automatic
scalar-training expansion: **MATERIAL_DISSENT: no**. The intermediate prediction
succeeded; the directional sample-mean native prediction is favorable, but stable
package preference and semantic value remain unresolved. DM adopts this precision:
absence of a stable preference is not a failed sign prediction, zero-effect finding
or an invented requirement that all three seeds win. Q is averaged over connected
users; its positive sign can coexist with fewer users receiving service. All B01
constraints and positive/adverse evidence remain, without a new co-adaptation story.

Support, adoption and investment are separate. The retained C remains the uncontinued
reference; neither O nor L is promoted as a generally better training recipe. Keep
all paid final assets, especially ordinary O19452 and plain B19451, as constructive
conditional capabilities. O19452's +.060075J/+3.665527service against C is not a
failed ordinary comparator. Its advantage over B19451 is much smaller:
+.005738J/+.457886service, only13/32 current worlds with higher J. Selecting these
assets after observing B02 does not make them preselected winners on unseen worlds.

At the assigned substantive boundary, the recommended next purchase is a **new,
prospectively bound frozen-asset reuse comparison**: O19452, B19451 and uncontinued
C on one new matched32-world H256 sampled-action panel, retaining the same RR
transport and information. Estimand: reuse value of these selected paid assets,
not O-recipe superiority, independent training replication or learned semantics.
Prediction: the ordinary asset gains against C may recur, while O-B's much smaller
increment may not. Joint O improvement would support conditional O reuse; if the
simpler B supplies the benefit, use B; if neither improves C or J/service disagree,
retain C without automatically adding a panel. Actual seeds, checkpoint hashes and
fixed decision rule would be bound before any future launch, not invented here as
an active contract.

Proposed cost is0 fits/96 episodes/24576 native steps/0 updates. B02's blended rate
scales to about37s, only a rough magnitude; evaluation-only speed, preparation and
readback are unmeasured. It answers the immediate reusable-baseline question more
directly than another unchanged nine-fit learning batch (about33min at the observed
rate) or a packet-ablation diagnostic (which addresses dependence/distribution
shift, not which complete paid asset to use). More conditional fits could narrow
the current means but would still share C; independently trained C starts address
a different broader uncertainty. No diagnosed intervention currently predicts a
better learning repair. A new cross-question investment or stopping remains a
legitimate alternative if baseline reuse is not useful to Root's portfolio.

DM disposition: return this concrete proposal to Root at the assigned boundary;
**do not append it to B02 or launch it now**. B02 is completely read; the direction
returns to reserve with no active producer, unread result, retry, Pro or selected
successor. No Root approval dependency is fabricated. The broader content question
remains open, with a favorable but uncertain conditional mean and useful ordinary
assets retained. Any future re-entry starts from these recorded constraints and
an explicit new comparison, not renewed full-payload replacement or automatic repair.

### Publication and measured retirement

Complete evidence, independent disposition, reserve standing and directly affected
shared communication background were published at `99291c8e6`. Before retirement,
the native exit witness, stopped observer with no pending event, completed helpers
and absent external B02 code consumers were checked. The final critic explicitly
released both source snapshots; no accepted/native or readback process still used
them. No live source or output was moved to change ownership.

The configured snapshot collector previewed and removed, with its read-only
`--sudo-process-scan`, only these two source worktrees:

| Deleted target on wsl_4070 | Allocated bytes before | After |
| --- | ---: | ---: |
| `.git/hmasd-launch-sources/0d64575e6baa4ced93b7b02d3b368d75` (refused source-only preparation) | 801873920 | 0 |
| `.git/hmasd-launch-sources/a4c43170c0d446b3a002d8b66608660e` (terminal accepted B02 source) | 801886208 | 0 |
| `/home/wu/hmasd-inputs/uav_message_content-b02-C-456832fa.pt` (temporary input duplicate) | 466944 | 0 |
| `temp/directions/uav_message_content/` (standalone published reader copy) | 24576 | 0 |

Both source-directory and Git-worktree-registration absence were verified. Claims,
manifests, source commits and all unique evidence remain. Rehashed all627 stable
B02 files after deletion:135657594 bytes unchanged; original C's canonical hash
also unchanged. Snapshot removal neither erases the operation nor grants retry.

On author main, retired the six-file `experiments/candidates/uav_message_content/b02/`
training package and `tests/experiments/candidates/uav_message_content/b02/`, whose
exact accepted implementation remains at native source `02ede8a4a`. Removed their
generated caches, the root direction/read-test caches and the stopped observer's
`temp/directions/uav_message_content/` request. Retained the useful independent
`read_b02.py` and all five reader checks; their synthetic channel fixture now uses
the existing shared Channel directly rather than depending on retired B02 code.
All five checks passed after retirement in6.12s with bytecode/cache writes disabled;
no experimental environment or policy was invoked. No B02 imports remain in live
experiments/tests outside the retired source history.

The local selected targets plus retained test file measured229376 allocated bytes
before and8192 after: **221184 bytes reclaimed locally**. Remote selected targets
reclaimed **1604251648 bytes**. Total measured net release is **1604472832 allocated
bytes**, excluding Git object-store accounting and unrelated concurrent disk writes.
No full copy, archive or backup chain was created. One force-style scratch-removal
command was rejected by the tool before deletion; explicit non-force file removals
and empty-directory removal completed the same validated targets. There is no
remaining deletion blocker or leftover target. Required native bulk remains one
durable node copy, and the pure reader remains usable without the deleted staging
input or launcher source snapshots. No further study is selected or running.

<a id="b03-frozen-assets-prospective"></a>
## 2026-09-29 - B03 prospective: reuse four selected frozen assets on one new panel

Root has now selected a new study at the B02 return boundary: include L19452 alongside
the proposed O19452, B19451 and original uncontinued C. This is not an extension of
frozen B02, an old-handle retry or restoration of an archived lead. The same current
DM owns this newly selected question: **which already-paid complete asset is useful
on a new deployment panel under the unchanged host/channel/action mode?** One fixed
panel, no new fits, decoder changes, packet ablations or automatic second panel.

Current published RESEARCH topics5/6/8 and B02 result `99291c8e6` directly inform this
choice: initial-preservation/response evidence does not establish learned semantics;
world variation of a fixed asset differs from continuation-training variation; free
additional signals need not help a finite trained policy. B02's positive L sample
means and strong ordinary assets are preserved. L19452 is selected because its B02
endpoint has both the highest observed L J and service, not because it won an unseen
world or because the learning recipe is established. B19451 and O19452 similarly
come from observed B02 outcomes. All selection exposure is part of B03's estimand.

This adds8192 steps to the earlier three-asset proposal and avoids discarding the
favorable learned asset for lack of an algorithm-wide result. The existing independent
final ResearchCritic is assigned a focused follow-up on this addition, the actual
reuse estimand and the one decision rule below. It is not another portfolio review;
material dissent returns to Root while independent preparation continues.

### Bound assets, information and panel

Canonical inputs on `wsl_4070`, all frozen in FP32 CPU evaluation, are:

| Label | Source and canonical path relative to `/home/wu/projects/HMASD/` | SHA256 |
| --- | --- | --- |
| C | B01 `b2a422088`; `runs/uav_message_content/b01_s19431/C/final.pt` | `456832faaa94afb22cf3faa00bb97b0f129e2f5b72b2eedbb1148523b088cdad` |
| B | B02 `02ede8a4a`; `runs/uav_message_content/b02_preserved_scalar/19451/B/final.pt` | `34871c49874ec716c21438581facfaeca8a25930304a39eb26e001fb2b259da2` |
| O | B02 `02ede8a4a`; `runs/uav_message_content/b02_preserved_scalar/19452/O/final.pt` | `90760a722081dec5442aeec85c9302ae3992dcfb96f0bf919aa81389815aa684` |
| L | B02 `02ede8a4a`; `runs/uav_message_content/b02_preserved_scalar/19452/L/final.pt` | `c8df7428611608ae0c2786b6b9e395e8183d3b79b30fcdd197e4fcdc9c643f59` |

Verify actual current bytes/metadata before binding launch; stage only these exact
inputs as C.pt/B.pt/O.pt/L.pt in configured external-input root
`/home/wu/hmasd-inputs/uav_message_content-b03/`. The admitted loader verifies each
declared hash and strict actor state before native evaluation. The canonical files
stay unchanged; these necessary small staging duplicates are deleted after reading.
No optimizer/RNG/recurrent state is continued, and no new optimizer is constructed.
No warm-start zeroing is performed: each actor/content tensor is the stored endpoint
exactly, with parameter hashes checked before and after evaluation. Critic state can
remain in the verified source file without a value forward, since it never enters
sampled evaluation actions. There is no receiver or content-head adaptation.

Use exactly the native BaseCADC N5/H256/50static-user host, reward
`J_physical=.014*served_users+.3*Q`, fee.001/tick, and existing actor171-feature
interface. RR sends one seven-float packet every tick, period5, delay1/5, channel
flip.05, arrivals before action. C/B slot5 remains0; O keeps the frozen five-step
anonymous sighting spread; L samples its retained scalar head. All other payload
fields remain the original C convention. Preserve sampled motion and sampled L
content, private motion/content generators, resets of GRU/channel/sighting history,
the exact pre-action observation and packet order, and no hidden future/user-ID
information. No deterministic action-mode substitution or diagnostic intervention.

New invocation master19461; episode e=0..31 uses physical seed1946102000+e,
channel1946107000+e, motion1946103000+e and content1946104000+e. The identical tuple
is used for each frozen asset; this family is disjoint from B01 and B02. No scene or
outcome at these seeds has been inspected. Fixed asset order C,B,O,L,32episodes each.
Each episode owns fresh motion/content generators; construction RNG is isolated and
cannot shift evaluation streams. Pairing is verified by scene/channel hashes and
seed propagation, not seed labels alone. The fixed-asset world/protocol replicate is
the deployment-sampling unit; it is not an independent training replication.

### Proposed one-panel reading and cost

Prospective endpoints are per-world/per-asset mean net/physical J, users/tick, Q,
fee, transport counts and boundary/floor/ceiling fractions/mean height using the same
pre-action convention. The host has no energy budget; these behavioral descriptors
do not establish physical safety. Retain all128 complete raw trajectories and all
six signed paired asset contrasts, including world-level adverse tails.

The proposed deterministic exploratory reuse rule, subject to the focused review:
C is the default. A B/O/L candidate is eligible only if its paired mean J and mean
service differences versus C are both strictly positive. Among eligible candidates,
choose highest mean J; exact ties use greater mean service, then fixed simplicity
order C,B,O,L. Thus two assets can both improve C while trading J against service
relative to one another; report that tradeoff rather than claim Pareto dominance.
A mixed-sign candidate versus C is not eligible. If none is eligible, retain C.
This selects a provisional conditional reuse asset once, not a generally superior
training algorithm. Compute all nominal paired t95 df31 intervals as descriptive
sampling uncertainty, uncorrected/not selection-adjusted; they are not an extra
pass gate, zero-effect proof or more training seeds. No automatic new panel follows
any positive, negative or mixed outcome. L winning would support this selected
learned asset's complete use, not content semantics or recipe recurrence; an ordinary
winner remains a constructive capability rather than a failed learned comparison.

Full planned exposure:0 fits,4x32=128 episodes,32768 native team steps,163840
motion samples,8192 L content samples,32768 sends and0 optimizer updates. Only
actual deployed actor forwards are required; no ablation/extra sensitivity forward,
search, planner, teacher, suffix replay or tuning is added. One CPU intra-op/inter-op/
BLAS thread on the checkpoint node, subject to fresh actual-node admission. B02's
blended rate scales to49.2s for these steps, a rough magnitude only; evaluation-only
wall/import/build/readback and engineering are not measured yet. Record actual
batch/per-asset wall, self CPU and process-lifetime RSS; no pricing pilot is required.

Inherited selection cost remains B01+B02:12 fits,1769472 native steps,12288 updates,
2649.747767s measured scientific wall and2647.095349s self CPU, plus incompletely
measured engineering/readback. Completing B03 would yield12 cumulative fits,
1802240 native steps and12288 updates, not new training evidence. All earlier
checkpoints, positive/adverse continuations and no-causal-attribution limits remain.

L0 for implementation after review resolution: narrowly recover only the necessary
frozen policy/scalar/channel/evaluation behavior from source02ede8a4a into new
`experiments/candidates/uav_message_content/b03/` and mirrored tests. Reuse current
unchanged shared Actor/sample/environment helpers; do not resurrect the B02 trainer
or alter shared core. Explicit admitted entry `b03/run.py` binds seed19461, published
launch SHA, fixed external assets root, fixed128episodes/H256 and output
`runs/uav_message_content/b03_frozen_assets/`. Hash-load exact actor weights with
strict metadata/state validation, set frozen/eval mode, reset episode histories,
stream compact per-world rows plus compressed raw arrays, count0fits/updates and
retain partial failures without repair or missing-pair imputation. Pure reader is
DM-owned outside b03 and performs no model/environment calls.

Correctness checks use synthetic actors/checkpoints/protocol fixtures only: exact
loaded tensor preservation including formerly zeroed columns, sampled RNG law and
stream isolation, unchanged O/L payload generation and delivery order, complete
frozen-state retention, counts/paired reduction/decision-rule branches, admission
before scientific effects and partial-failure frontier. Independent engineering
review covers source identity, numerics and RNG; no hidden native test-panel probe.
The Implementer may own only b03 implementation/tests and makes no scientific choice,
NOTE/index/Git write, result launch or child delegation. DM accepts its returned diff.

### Focused review, input verification and final rule adoption

The existing separate-context final ResearchCritic reviewed only the L addition,
actual reuse estimand and proposed rule, after its original B02 reconstruction.
It recommends retaining L19452 and the complete four-asset panel:
**MATERIAL_DISSENT: no**. Marginal8192-step evaluation gives a plausible paid
learned asset a fair use comparison without rescuing a training-method claim.
The point-mean rule is an explicit provisional-use preference, not a guarantee.
Apply eligibility and ties with unrounded values. The nominal df31 intervals are
not selection-adjusted for choosing this panel's winner; a fresh panel removes
B02-outcome reuse but does not remove new winner-selection optimism.

DM adopts the rule exactly as proposed. If none qualifies, retain C without an
equivalence or general continuation-failure claim. If one qualifies, select it
provisionally with adverse worlds/uncertainty. If several qualify, prioritize J
and report any service sacrificed relative to another eligible candidate. If L
wins, this supports L19452's conditional complete use, not useful encoding or
recipe superiority. If L's J is highest but service is below C, exclude it under
the predeclared requirement; higher Q does not override that choice. A required
incomplete/invalid comparison yields no selection from a reduced set. No extra
significance gate, pilot, mandatory attribution study or automatic second panel.
The review recognizes stopping with C as the cheapest alternative; given Root's
selected reuse objective, this panel answers actual asset choice more directly
than unchanged fits or packet ablation. No material disagreement remains.

The registered source Scout independently hash-verified all four actual node files
and inspected weights-only serialized states, with no model/environment call.
Exact sizes C/B/O/L are463293/463357/463357/464366 bytes. C metadata is armC,
master19431,input171,critic451; B is armB/master19451; O/L are their named arm/
master19452. B/O/L carry the original C inherited_sha256. All actor/critic tensors
are float32. L alone adds content weight(1,64),bias1,log_std1. No optimizer/RNG/
hidden state exists. All named shared CADC/UCOPE/native-host dependencies are
unchanged from B02 source02ede8a4a. Strict endpoint loading must not call B02's
warm-start helper, which would zero learned receiver columns and reject endpoint
metadata. Only matching architecture construction plus strict full actor loading
is accepted. This resolves the bound-input facts needed by the L0; release it
to the existing registered Implementer for the narrow evaluator and tests.

### B03 implementation acceptance and staging (2026-09-29 UTC)

DM accepted the Implementer's narrow `b03/` evaluator after reading all six source
files and synthetic tests. It reuses the unchanged sampled CADC actor/channel and
native host; the only retained B02 content behavior is the selected scalar and
private five-observation history. Strict verified-byte loading preserves every
stored actor tensor, including learned scalar-input columns. A critic object is
constructed only to validate checkpoint key/shape compatibility and is never
forwarded; this small preparation cost is not native exposure. No optimizer,
diagnostic intervention, training storage or learner is restored.

The independent engineering Reviewer found two reader issues: unchecked reported
exposure counters and a direct-script import path failure. DM repaired both before
execution. `read_b03.py` now reconciles per-asset and aggregate counts against the
complete128 H256 rows, including exactly32768 actual actor forwards,8192 L content
samples and zero critic/diagnostic forwards/fits/updates. Eight corrupted-count
fixtures reject invalid readings. Direct CLI `--help` works without PYTHONPATH.
The Reviewer otherwise verified exact checkpoint loading, unchanged sampled RNG
law/delivery order, frozen state and stop-on-partial behavior. Final DM suite:
30 synthetic tests passed in14.84s; no native panel or real-checkpoint forward was
used in correctness tests. The earlier paired-interval fixture used a mistyped
hand-entered constant; its reference now uses the analytic variance88 of0..31.
The independently checked df31 t95 critical value remains2.0395134463964077.

The four declared canonical inputs were copied once to the external staging root
without replacement and all four staged SHA256 values equal the prospective table.
These are temporary byte-identical input copies, not replacement durable assets.
Exact published source and fresh actual-node admission remain required before the
single result invocation. The runner records scientific batch/per-asset wall and
self CPU/RSS; launcher preparation/import/readback time is separately observable,
not silently included in the49.2s blended-rate estimate or claimed as zero.

<a id="b03-complete-reading"></a>
## B03 complete frozen-asset panel: useful continuations, provisional B reuse (2026-09-29 UTC)

### Accepted operation, complete evidence and costs

Published scientific and reader source is
`ff15fe5df068589b15677ac3f0289fc92772548f`. The new operation is bound by
[`launch-manifest.json`](../../../../runs/uav_message_content/b03_frozen_assets/launch-manifest.json),
not the old B02 handle. Supervisor `uav-content-b03-ff15fe5d` was accepted at
06:14:17.139256UTC, and its actual exit witness records exit0 at06:14:59.284121UTC.
Actual-node preflight observed14795661312 available physical/effective bytes,
above4294967296; lead/pause/source checks passed against fresh published controls.
The remote metadata-only row-refresh command encountered a lazy Git blob fetch
without the configured network shell. DM stopped only that identified read-only
Python/Git subprocess chain; no file rewrite occurred and no scientific process
was signalled. The canonical active/lead cells already agreed with published
controls, as the admission record verifies. No failed scientific invocation or
replacement attempt was created. Existing remote Git auto-GC bad-tree warnings
were not repaired as part of this direction.

The existing owning-session observer was rearmed from stopped generation3, then
registered the new B03 job in generation5. The same claim status returned terminal
READY, exit0 and absent runner/supervisor, with no observation errors. App queue
delivery again returned -32600 for the native child; the DM stayed active, used a
60s deterministic wait and drained that same event. It was consumed into
generation6 and observation stopped. This was a new job, never a B02 rearm/retry.

The complete native contract is present:4 assets,128 H256 episodes,32768 team/native
steps,163840 motion samples,8192 L content samples,32768 actual actor forwards,
32768 broadcasts,32428 delivered and340 horizon-censored packets. There are
0 fits,0 optimizer updates,0 critic forwards and0 diagnostic actor forwards.
Every asset has8107 delivered/85 censored packets. Original checkpoint digests,
all four per-asset before/after actor tensor hashes, all32 paired physical/channel/
motion/content seed tuples, scene hashes and channel sequences match the binding.
The reader independently reconstructed every one of128 retained NPZ trajectories,
the preserved six fields and scalar, arrivals-before-action records, rewards,
service/Q, behavioral readings, counters and the complete one-panel choice.
It made zero environment, model or optimizer calls.

Durable original evidence remains on `wsl_4070` at
`/home/wu/projects/HMASD/runs/uav_message_content/b03_frozen_assets/`:
138 stable native files totaling20353306 logical bytes, including128 compressed
raw trajectories and four episode streams; `reading.json` adds188493 bytes.
Compact summary/native controls/reading are also published locally under that tag.
Original C and all nine B02 endpoints stay at their existing canonical paths.
Hashes: summary `a7508521606e915b5cf659214e595317a206cd9310e9efe6a7fb3dd6657c2e97`;
reader `6adb92d29c5bcc4186de77ebd0132498ab2ccaf9771df3c61fc48cb4ee3e6052`;
reading `97f73789a166a8bcb9245ca1c9a2ae3b785bdfffcf6ab1d863e0153aae0baf5a`.

Measured scientific batch wall41.154858s/self CPU41.293131s, process-lifetime
peak RSS382032KiB (373.078125MiB); intra-op/inter-op threads1. C/B/O/L wall
8.655316/10.092501/11.311136/11.076807s, self CPU
8.793794/9.366754/11.691696/11.421227s. Per-asset RSS values are cumulative
process-lifetime peaks, not independent simultaneous memory allocations.
The supervisor task log starts at06:13:59UTC, about18s before admission;
accepted-to-exit duration42.145s includes runner import/exit overhead outside
the scientific interval. Pure full-trajectory readback cost67.47s wall,
66.53s user+2.38s system CPU and41784KiB peak RSS, with no added native exposure.
Preparation, repeated correctness checks and independent scientific reading are
additional engineering/analysis costs, not fully measured and not zero.
Cumulative B01+B02+B03:12 fits,1802240 native team steps,12288 updates,
2690.902625s measured scientific wall and2688.388480s self CPU. The new evaluation
was inexpensive; that does not erase all inherited selection/training cost.

### Fixed-panel result and actual use decision

All values below are32-world means. The fee remains.001/tick in every asset;
B is continued C with a blank additional scalar, not a no-communication or
nonlearning controller.

| Fixed asset | Net J | Users/tick | Q | Boundary fraction | Height floor fraction | Mean height m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Original C19431 | .187527956 | 11.336425781 | .099393318 | .118969727 | .192846680 | 87.606967 |
| B19451 | .249746565 | 15.148315430 | .128900497 | .150830078 | .739160156 | 55.139982 |
| O19452 | .241001564 | 14.458862305 | .131924973 | .267822266 | .547949219 | 61.525926 |
| L19452 | .224716955 | 13.314697266 | .131037311 | .181835938 | .850805664 | 52.761903 |

| Paired difference | Mean net J [nominal t95 df31] | Mean users/tick [nominal t95 df31] | J-positive / service-positive worlds |
| --- | --- | --- | --- |
| B-C | +.062218609 [.049510389,.074926829] | +3.811889648 [2.964911428,4.658867869] | 31 / 30 |
| O-C | +.053473608 [.035303973,.071643242] | +3.122436523 [1.880297719,4.364575328] | 26 / 25 |
| L-C | +.037188999 [.023279240,.051098757] | +1.978271484 [1.063079227,2.893463742] | 27 / 24 |
| O-B | -.008745001 [-.027241688,.009751686] | -.689453125 [-1.946876271,.567970021] | 13 / 13 |
| L-B | -.025029610 [-.040111999,-.009947221] | -1.833618164 [-2.860572073,-.806664255] | 6 / 6 |
| L-O | -.016284609 [-.037244359,.004675140] | -1.144165039 [-2.555870345,.267540267] | 16 / 15 |

Under the unchanged unrounded point-mean rule, **B/O/L all qualify against C;
provisionally select B19451**. No additional significance or unanimity condition
was imposed. B has the largest J and service means here, so no service sacrifice
relative to another eligible candidate is needed. This is a complete-asset use
choice in the original deployment distribution, not confirmation that B dominates
O or is the best training recipe. O-B reverses the exposed B02 panel's small
positive ranking; its new J/service intervals both include zero. Nominal intervals
are uncorrected and not adjusted for this panel's winner selection.

Adverse outcomes remain material. B-C loses J in world30 (-.015072208) and service
in worlds20 (-.1484375) and30 (-1.6796875); its best J gain is world15 (+.127857129).
O-C has6 J-adverse and7 service-adverse worlds; world29 gives -.037591378 J and
-2.9609375 users/tick. L-C has5 J-adverse and8 service-adverse worlds, including
world2 at-.036559315 J/-2.765625 service. L still jointly beats B in six worlds
(1,12,13,14,26,30), and jointly improves C in24. Against O, L splits J16/16;
its worst J difference is-.114697019 and best+.075866812. All world-level signed
contrasts and Q/height/boundary outcomes remain in `reading.json`.

Every continued asset's Q is above C in all32 worlds. L-B mean Q is slightly
positive (+.002136814), yet native J/service are lower; Q alone is not the use
criterion. Low-altitude occupancy is prominent for B and L, especially L's.850806
floor fraction. This is a behavior descriptor in a host without energy, obstacle
or physical-safety endpoints, not a verified safety result or causal explanation.

### Explanation and provisional investment judgment

Task opportunity is real for these paid complete assets: the selected B, O and L
endpoints all retain joint mean gains over original C on new worlds. This
strengthens the constructive reuse finding, including L's useful positive example;
failure to win asset selection is not absence of a learned capability. Extra scalar
content was not necessary for the best of these four selected assets, but B03 does
not estimate the causal value of removing a scalar from O/L. B02's favorable L
recipe sample means and large continuation variability remain unchanged.

Representation and learning-method conclusions remain narrower. B03 neither
explains the old replacement loss nor isolates preservation, scalar semantics,
co-adaptation, representation opportunity or training-recipe superiority. Its32
world/protocol samples concern these four frozen policies, not new C parents or
additional continuation seeds. There is no optimizer nonactivation diagnosis:
B02's actual delayed credit and updates remain genuine, while useful encoding
increment beyond competent continued C/ordinary content is still unresolved.

DM's provisional next choice is to use B19451 as the paid reference for an actual
unchanged-host deployment need, keep O/L as durable useful alternatives, and stop
automatic panel/fitting additions in this question. Another identical panel would
mainly refine the relatively small B/O asset ranking, not the parent learning
question; another same-parent fit set would still not establish independent C
recurrence. A causal scalar ablation changes the question and is not required to
make the current practical choice. Without a named decision that needs that
precision or attribution, those costs have less marginal value than Root assigning
a distinct substantive question. No second panel, extra fit or content intervention
is selected. The final independent reading below owns any correction or dissent
before this becomes the published standing.

### Independent final reading and resolved next choice

The same separate-context ResearchCritic completed an independent reconstruction
from all128 original NPZs and four episode streams before seeing the DM's
interpretation. All raw and input hashes matched; native endpoint discrepancies
were at most2.8e-16, and independent behavioral reductions matched exactly.
Paired exogenous tuples/channel sequences and frozen actor hashes also matched.
It independently selected B19451 under the prescribed rule: B/O/L all eligible,
B highest J/service. **MATERIAL_DISSENT: no.** No review process or snapshot
consumer remains live.

Its substantive recommendation is to retain B for provisional N5/H256 static-user
sampled-action use, preserve O/L as useful conditional assets and end standalone
ranking/automatic scalar-training expansion. It specifically warns that O-B's
old-to-new sign reversal with fixed weights is deployment-panel variation
(world/channel/action randomness), not a new training outcome. Ordinary
continuation producing useful motion policies, with selection among training
outcomes, remains a simpler explanation for the practical gain. Extra learned
content is unnecessary for demonstrated B capability, without thereby refuting
content opportunity or a learning recipe. Neither an uncertain B/O population
order nor missing semantic identification mandates another experiment before
this conditional practical choice.

The Reviewer preserves all favorable and adverse evidence, including B-C's
world30 J/service loss and world20 service-only loss; O-B world9
-.109374987 J/-7.35546875 service; L-B world24 -.095084566/-7.09375;
and L-O world11 -.114697019/-7.734375. O and L have slightly higher mean Q than
B but their service losses dominate native J. Low altitude/boundary occupancy
does not establish cause or physical safety. Its recommendation retains B02's
favorable L sample means and adverse continuation instances unchanged.

DM adopts that reading. Empirical support is fixed-asset joint improvement over
C on a fresh panel; provisional adoption is B19451 for this declared use contract;
further scientific investment is **reserve, no active producer and no selected
new panel/fit**. A changed deployment condition or an explicitly important training
recurrence/semantic question would create a different decision and require its own
prospective comparison. There is no fabricated pending Root approval or automatic
recheck. Root may carry this paid B reference into compatible subsequent work or
assign a distinct substantive question. All required original C/nine continuation
checkpoints and raw positive/adverse records remain durable; only unused code,
the terminal launcher snapshot, duplicate staging and rebuildable scratch are
eligible for measured cleanup. The useful pure readers/tests remain maintained.

### B03 closure cleanup

Result/shared understanding was published at `cd5270e25`. All implementation,
engineering-review and scientific-review consumers completed; the native process
and observer are terminal/stopped. Imports and entry references identify no live
consumer of the one-shot `b03/` evaluator. Its six source files and mirrored
one-shot test are removed from current main, recoverable at `ff15fe5df`; pure
`read_b03.py`, `read_b02.py` and their focused tests remain useful and retained.

The first exact-target source-GC preview refused only the reader-created ignored
`read_b02.cpython-310.pyc`. After deleting that exact rebuildable cache, a fresh
preview passed and the supported collector removed terminal snapshot
`9e0b9c4007994e71b45abe8bee05017c`, including Git worktree registration. The four
duplicate staged C/B/O/L.pt files and their external staging directory were
deleted. Local one-shot code/test caches, pure-reader test caches and the private
`temp/directions/uav_message_content/observe-b03.json` request/directory were also
deleted. No archive, full copy, retention chain or replacement snapshot was made.

Measured allocated bytes: remote snapshot802144256 plus staging1871872 went to0,
releasing804016128 bytes. Local owned source/tests/docs/runs/scratch trees were
4513792 bytes before cleanup; the after total includes this additional compact
closure record. Combined net reduction is804208640 bytes, excluding Git object
storage and unrelated sessions' files. No concrete deletion blocker remains.
Post-cleanup hashing verified all627 B02 and138 B03 stable files against their
retained manifests and all four selected canonical checkpoint hashes; this
preserves original C and all nine B02 endpoints. Exact snapshot/staging paths are
absent. Canonical raw evidence, compact records and stopped observer/claim metadata
are intentional retained evidence, not cleanup leftovers or active work.

## 2026-09-29 - B04 prospective: dated future-motion forecasts with a competent persistence control

<a id="b04-future-motion-prospective"></a>

**Source-backed proposal for the current selection review; no implementation or result
launch.** Root assigned successor question ownership to native DM
`/root/dm_delay_intent`; routing was published at `ef2fd853c154fb3d9834a821d6363547b0a49959`.
The launch-bound lead remains `Codex DM (native child)`. The direction row is still
reserve during this selection boundary. B01-B03 are fully read/retired, with no
accepted operation or unread output inherited by this child. This entry changes no
PPC/FSD pause, G33 freeze, Milan-data hold or Claude ownership. Root is arranging one
independent selection review covering the concrete new questions. Its preliminary
warnings about a noisy current-command baseline and an expired five-step forecast
are incorporated below; the completed review and selection disposition remain to be
recorded before substantial implementation. No duplicate critic or Pro was started.

### Question, inherited evidence and actual temporal opportunity

Can a learned, fallible forecast of a sender's own future position improve complete
decentralized service beyond both geometry-only continuation and a qualified ordinary
motion forecast, under matched primitive control and a stated larger packet budget?
The intended contribution is empirical understanding and possible task usefulness,
not a novel communication algorithm, a committed-intent claim or confirmation.

Keep the [B01](#b01-complete-reading), [B02](#b02-complete-reading) and
[B03](#b03-complete-reading) readings intact. All original content arms learned useful
motion. B02's learned-scalar sample means were favorable but continuation rankings
reversed; its real credit, updates and input response do not identify semantics.
B03's B/O/L assets all jointly improved on C on fresh worlds; B19451 was provisionally
selected by the fixed rule. B is learned continued C with geometry communication, not
a no-learning/no-communication control. Its B03 gain over C was +.062219 J and
+3.811890 users/tick, while world30 lost J/service and world20 lost service. More
ordinary motion training and selection among training outcomes remain strong
explanations of the useful assets. Those facts motivate a matched continuation G
and a frozen B anchor here, rather than declaring the old scalar recipe repaired.

Read current published main at `ec20983291359d91ab59e670627363415854b6bb`, refreshed
to `ef2fd853c` without changes to the relevant background:
[topic 5](../../RESEARCH.md#5-技能和异步性是组织决策的方式其收益需要证据) preserves the useful
RR process and separates transport time from decision-time information;
[topic 8](../../RESEARCH.md#8-数学信息与博弈结构怎样帮助dm选择实验) separates a signal,
finite learned response and complete value. Concretely, keep all useful geometry,
retain primitive control in every arm, date the forecast at its send time, and buy
complete native learning/evaluation rather than infer benefit from prediction MSE.
S7 energy/BS findings do not supply this host with battery, queues or moving users.

The source-verified host is unchanged N5/50 static users/H256, map1000m,
height50-150m, component speed30m/s and dt1s. Its native physical objective is
`.014*served_users + .3*Q`; net J subtracts the identical .001 fee per team tick.
At t, due messages arrive, actors update private GRUs, all primitive commands are
sampled, the RR sender t mod5 transmits, native motion/reward occurs, then the channel
advances. A send takes1/5 ticks in GOOD/BAD. The actor has a one-step velocity head;
there is no future target, timer or commitment in this executor. Current command can
legally enter a packet after sampling, but does not assert future command persistence.
Sources: unchanged [CADC model](../../../../experiments/candidates/contention_aware_decentralized_communication/cadc_b01/model.py),
[channel](../../../../experiments/candidates/contention_aware_decentralized_communication/cadc_b01/channel.py),
[host binding](../../../../experiments/candidates/ucope/uav_motion_prefix_b01/environment.py),
and [native movement](../../../../envs/pettingzoo/uav_env.py#L265).

The conjectured decision coupling is that a receiver choosing its next motion can use
a dated estimate of where a teammate is going to provide service, in addition to that
teammate's old position and observed demand. Static users do not make those joint
trajectories static. Whether the prediction changes a useful motion choice is unknown;
no private-history bottleneck or positive headroom is assumed. Existing geometry and
the lawful current policy center may already provide enough predictive information.

### Primary bridge and why not a commitment executor

Kim/Park/Sung, ICLR2021, [Intention Sharing](https://openreview.net/pdf?id=qpsl2dR9twy),
uses learned imagined trajectories as message content. The published abstract on the
[author page](https://bitsandscraps.github.io/publication/iclr2021/) and the accessible
[original review-version PDF](https://openreview.net/references/pdf?id=k71zbVCDy)
were read: sections3/4 describe next-tick communication, modeled future observations
and actions, supervised model losses and an attention encoder; section5.3 explicitly
allows imagined/actual trajectories to differ. The published PDF endpoint currently
returns a browser challenge, so method details here are attributed to that identified
review version, not an asserted audit of the final PDF. The bridge is predictive
content, not future truth. Our direct endpoint forecaster is not an IS reproduction:
it omits imagined joint rollouts, attention and differentiable message training, and
faces RR caches plus endogenous teammate responses under one/five-tick delay.

[DACOM, arXiv2212.01619, methods](https://arxiv.org/html/2212.01619v1) makes waiting
time part of action and trades information against response delay; its TimeNet is not
an intervention in this fixed primitive-action/RR channel. Local locator:
`MARL-0006`, `/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0006.json` and
`pdf/MARL-0006.pdf`; the primary methods passage, not the catalog hint, supports this
distinction. [CAIC, PMLR337 li26h](https://proceedings.mlr.press/v337/li26h.html)
provides a related published abstract about trajectory prediction and asynchronous
messages, but also changes communication frequency under queueing congestion. Our
channel has neither learned frequency nor endogenous queueing. None of these results
is native UAV evidence or a novelty claim for the proposed study. The three local
library title/catalog searches are discovery only; a miss is not absence of prior art.

A constant-velocity hold would make truthful advertised velocity and qualified
constant-velocity prediction coincide during the hold. It would also remove primitive
feedback opportunities. A target/waypoint commitment could differ, but would require a
new executor, an explicit flexibility cost and geometry/controller controls with the
same rights and cadence. That is a larger control question, not necessary to test the
current predictive-content conjecture. Select the forecast comparison provisionally;
do not add a hold solely to make the word "intent" true. These messages promise a
forecast for a dated endpoint, not an executed future control or guaranteed position.

### Three adapted arms and the richer communication contract

All three arms start from the exact B19451 actor/critic and train the complete
receiver/motion policy. Preserve the seven original fields, including blank slot5:
sender xyz, current anonymous visible-user centroid xy, zero, and count/20. Append
three FP32 endpoint coordinates. The RR sender, delivery1/5, channel flip.05,
metadata, .001 fee, reward, termination and primitive action rights remain identical.

| Arm | Appended three floats | Extra learning |
| --- | --- | --- |
| G | Zero padding; original geometry content. | Native receiver/motion PPO and critic. |
| O | Ordinary dated endpoint from the sampled first command, then persistence of the lawful policy's central command, with native bounds. | The same native PPO and critic. |
| F | Learned residual correction of that same ordinary endpoint, from lawful send-time context. | The same native PPO/critic plus a separately trained small future-position predictor. |

Every primary arm sends10 FP32 values,40 payload bytes instead of the old28, a42.9%
increase. All have the same one-packet/tick access and delivery law. Fixed fees/delays
despite size are an explicit abstract-channel assumption, not measured free bandwidth
or a real-network cost model. G pays the same padding cost. Frozen B0 retains its
original7-float interface and is a cross-contract capability/continuation anchor,
not the primary incremental-content control. Replacing old geometry with velocities
in the frozen receiver is not proposed.

Keep each old171-feature actor path intact and append the five three-float forecast
records, giving186 total features. Add a zero-initialized bias-free15->64 projection
to the existing pre-GRU encoder output. Similarly preserve the old451-feature critic
path and add a zero-initialized75->128 projection at its first preactivation, giving
526 total features. All three adapted arms use those same10560 added parameters.
Old tensor shapes/order/values stay exact. At initialization the additions contribute
zero, preserving the B function even when O/F packet bytes differ; do not rely on
inserting zero columns into a differently shaped GEMM for bitwise invariance. All
new receiver parameters become trainable. GRU/channel state resets each episode;
there is no optimizer, RNG or normalizer state inherited from B's saved endpoint.

Canonical B input is `wsl_4070:/home/wu/projects/HMASD/runs/uav_message_content/`
`b02_preserved_scalar/19451/B/final.pt`, source `02ede8a4a`, SHA256
`34871c49874ec716c21438581facfaeca8a25930304a39eb26e001fb2b259da2`.
Its current bytes/metadata will be reverified for input binding before implementation
acceptance/launch; this proposal uses the already published identity. B includes
131072 original C plus131072 continuation training steps; each new instance adds
its own stated continuation, not an independent B training history.

### Send-time forecast, expiry and training-only labels

Write normalized own position as `p_s=(x/1000,y/1000,(z-50)/100)` and
`D=(.03,.03,.30)`. Let `u_s=tanh(sampled_pre_tanh_motion)` be the actual normalized
command passed to the environment, `m_s=tanh(motion_mean_s)` the lawful central
command, and `K_s=min(10,256-s)`. The ordinary endpoint is

`p1=clip(p_s+D*u_s,0,1)`;
`pO=clip(p1+(K_s-1)*D*m_s,0,1)`.

This reproduces repeated native clipping for the constant remaining command, given
the available own-position sensor precision. It treats the known first action
separately, including a boundary hit followed by reversal. `tanh(mean)` is the
policy's central command, not `E[tanh(Gaussian)]`. This avoids treating one fresh
noise draw as a persistent plan without pretending to predict later policy feedback.
Plain sampled-command CV is recorded cheaply as an error reference, not bought as a
weaker fourth training arm. O uses the same legal actor output/private context access
as F; the ordinary forecast is selected from source reasoning, not a score screen.

F input is the saved send-time private GRU64, own p3, sampled u3, central m3 and K/10:
74 floats, all available after sampling and before current native motion. Its
74->64(tanh)->3 MLP has4995 parameters, with output weights/bias initially zero.
Let r be its output. Form
`pF=clip(pO+2*(K-1)*D*tanh(r), lower, upper)`, where
`lower=max(0,p1-(K-1)*D)` and `upper=min(1,p1+(K-1)*D)`.
Thus F initially equals O, and every predicted endpoint respects the known component
speed/map reachable box. It still does not guarantee the path or endpoint.

The packet encodes the normalized endpoint at absolute tick `s+K_s`. A receiver
uses the original validity/send-time/age metadata and public H256 to recover the
remaining forecast lead `K_s-age`; no extra timestamp, readiness bit or future label
is supplied for free. Missing records have zero appended coordinates. Expired
forecast coordinates are zeroed while geometry stays available; expiration is
`age>=K_s`. With RR period5 and maximum delay5, the newest active cache has age<=9.
Consequently every in-horizon delivered forecast has a strictly future endpoint,
including the terminal-shortened K. This is a structural timing fact, not evidence
of accurate or useful prediction. No sender is held to its advertised endpoint.

During training only, after the complete episode has been collected, label each
eligible send with that sender's later *own observation* `y_s=p_(s+K_s)`.
Eligibility means its message arrived before H; include every eligible send without
filtering on error, service, future movement or policy response. No simulator rollout,
future channel draw, unseen user label or other agent's hidden state is queried.
The future label cannot enter current actor/critic inputs, packet construction or
evaluation adaptation. Freeze the predictor during each two-episode behavior rollout;
then take four full-data Adam updates, lr3e-4, other Adam settings as native PPO,
grad-norm cap.5, on mean squared `((pF-y)/(K*D))`, a displacement/speed-normalized
loss. Do not backpropagate into saved hidden/action/mean or the actor/critic.
All episodes and complete native rewards remain in the policy comparison.

The predictor is never native-return-trained, and there is no synthetic reward.
Motion/receiver PPO replays the actual detached behavior packets, with its original
motion likelihood, four epochs, two episodes/rollout, chunk32, gamma1, no terminal
bootstrap, lr3e-4 and unchanged clipping/entropy/value/gradient settings. Neither
current forecasts nor their targets replace old packets during replay. This is a
predictive-content package with co-adapting motion, not an exact joint-gradient or
semantic-identification claim. F's extra supervised work and parameters are priced
explicitly; G/O have the same native-data, policy-update and communication budgets
and may use all lawful context, but do not waste matching dummy predictor updates.

There is no outcome-selected readiness threshold: before its first completed update
F is exactly O, thereafter its current predictor is used, and evaluation freezes it.
Model/policy drift, noise, packet compression and receiver learning can all limit
usefulness. They are prospective limitations, not automatic repair licenses.

### Fixed exposure, predictions and result reading

Propose three continuation masters **19501,19502,19503**, paired G/O/F inside each,
512 complete H256 episodes per fit (131072 team steps), final checkpoint only.
Training physical/channel seeds are `100000*master+1000+e` / `+6000+e`, e=0..511;
motion stream `+21`, predictor construction `+12` in an isolated generator scope.
There is no content-sampling RNG. Execute master order, then G/O/F. Do not select a
checkpoint or add epochs/seeds/arms after outcomes. Any technical failure preserves
the attempted fit and missing comparison; no duplicate/restart is automatic.

Evaluate all nine final policies and exact frozen B0 on one new common32-world,
sampled-motion H256 panel, with physical/channel/motion seeds
`1950002000+e` / `1950007000+e` / `1950003000+e`, e=0..31. No scene/outcome at
these seeds has been inspected. Pair actual scene/channel/seed witnesses, not seed
names alone. B0 supplies the common uncontinued/initial-function anchor. Initial
checkpoints and zero-projection/sequence checks establish the common start; nine
duplicate initial scientific panels are not necessary. All evaluation has zero
updates and isolated state/RNG. Three continuations remain conditional on one selected
B parent, not three independent B fits or confirmation. No claim note is created.

The temporal prediction is that F improves the dated forecast beyond O particularly
where delivered records are old, and the adapted receivers learn a consequential
response that improves complete J and service. Required intermediate readings are
send count, delivered/censored count, cache-use ages and positive remaining leads;
prediction error in horizontal metres and height at the dated endpoint, both per-send
and weighted by actual cache use; and F-versus-O prediction differences on the *same*
F trajectories. Include early/late age bins1-4/5-9 and terminal-shortened horizons,
with counts and empty groups explicit. Better errors on different arm trajectories
alone do not identify a better predictor. No MSE threshold admits or rescues a run.

At each final O/F tick only, one additional actor forward starts from the actual
pre-step hidden state. For O, blank only forecast coordinates; for F, replace only
forecast coordinates by the ordinary shadow predictions computed at those same
actual F send times. Record central-motion RMS/max change, ages and receiver-use
counts. These are zero-extra-step immediate-response diagnostics, not full historical
counterfactuals, mediation estimates or proof of beneficial response. No diagnostic
result is fed to the live actor. Full native outcomes decide useful package value.

Read F-O (primary), F-G and O-G net/physical J, served users/tick, Q, each continuation
against B0, all per-seed contrasts and per-world signed vectors/extremes. Retain height
floor/ceiling, boundary occupancy and worst service; this host supplies no battery or
physical-safety endpoint. Worlds are nested deployment variation. Report the three
conditional continuation means and descriptive df2 t intervals with their assumptions;
32 worlds are not extra training replications. Mixed signs and J/service tradeoffs
are reported, not turned into an after-the-fact unanimity or equivalence rule.

Positive F-O and F-G complete J/service means support a conditional learned-package
signal. Better dated predictions plus receiver response would strengthen the proposed
explanation, without establishing that semantics caused the gain. O-G improvement
with no F increment supports an ordinary anticipation capability. Forecast/error or
response improvement without native benefit weakens this finite package's use case;
native gain without improved fidelity remains a package result with mechanism
unresolved. G/O/F losing to B0 preserves the possibility of continuation damage and
the paid B capability. No branch automatically purchases replication, a hold, a richer
model, another panel or a new delay regime. At the read boundary compare further
independent-parent work, a materially different question and stopping for what each
would change; leave the original scalar interpretations untouched.

### Prospective cost and implementation boundary

| Work | New exposure |
| --- | ---: |
| Policy continuation fits | 3 arms x3 masters =9 |
| Training episodes / team steps | 4608 /1179648 |
| Final policies plus frozen B0 evaluation | 320 episodes /81920 team steps |
| Total native team steps / motion samples | 1261568 /6307840 |
| Native PPO Adam updates / replayed actor rows | 9216 /23592960 |
| F predictors / extra supervised Adam updates | 3 /3072 |
| Eligible F training labels / four-epoch row presentations | 385536-391680 /1542144-1566720, exact channel-dependent counts retained |
| F send-time predictor forwards, train plus final eval | 417792 |
| Extra final diagnostic actor forwards, batch-of-five | 49152; zero native steps/updates |

No model branching, imagined rollout, candidate search, calibration fit or old-asset
ranking panel is included. Every study tick still has one RR send. Cumulative direction
exposure after a complete B04 would be21 fits,3063808 native steps and21504 PPO
updates, plus the3072 new predictor updates. Do not count inherited B training nine
times as newly purchased compute. Earlier B01-B03 cost2690.903s scientific wall plus
incompletely measured engineering, reading and review; it is not erased here.

B02's nine fits/1327104 native steps cost1991.282s on wsl_4070 with one CPU thread;
B03 evaluation cost41.155s and full readback another67.47s. Simple step scaling gives
about31.5min for this base workload on that old node/runtime, before the new predictor
and changed decoding/reading. This is a magnitude estimate, not a measured new rate.
Plan **local_linux**, configured CPU interpreter
`/home/fires/.venvs/hmasd-linux-cpu/bin/python`, FP32, sequential fits, one Torch,
inter-op and BLAS thread. The actual local CPU is Ryzen7 8745H. Root reports the
preferred wsl_4070 occupied by Claude's two four-thread fits, six sequential fits in
its accepted35CPUh batch; do not consume that node now. Local timing is unmeasured:
budget roughly45-90min scientific wall, plus import/build and readback, without a
pricing pilot or shortened endpoint. Use fresh actual-node admission at launch, not
as a prerequisite for this reasoning. Record measured wall/CPU/RSS and thread teams;
the old approximately523MiB RSS is only a planning reference, not a current admission.

Working engineering estimate is4-6 agent-hours total: about2-3h for direction-owned
channel/warm-start/predictor/collector work,1-2h for focused checks and independent
high-risk engineering review, and about1h for collection, pure reconstruction,
scientific reading/publication. These are estimates, not measured totals or human
labor claims. Expected durable bulk is roughly100-200MiB from comparable existing
traces plus forecast context; actual bytes/hashes will be recorded. No whole-source
backup or duplicate evidence archive is needed. Engineering expansion to a learned
world model, joint rollout planner or commitment executor returns to the scientific
choice instead of being silently added to this batch.

L0 after selection: recover only required owned B02 collector/runner pieces from
`02ede8a4a` into `experiments/candidates/uav_message_content/b04/` and mirrored tests;
reuse unchanged CADC/UCOPE helpers without copying or changing shared learners/host.
Implement the declared10-float channel, exact old-path warm start, ordinary bounded
forecast, separate supervised head/label timing, detached replay, final-only panel,
compact summary and pure reader. Entry `b04/run.py`, output
`runs/uav_message_content/b04_future_motion/`; scratch stays under the owned temp path.
Checks cover native clipping/first-action semantics, age/expiry including terminal
truncation, unchanged geometry/transport and initial function, checkpoint identity,
no future-label leakage or shared-gradient path, target indexing, actual counts,
RNG isolation and zero evaluation updates. Tests use synthetic fixtures and owned
scratch, not an undeclared native pilot. Independent engineering review is required
for this scientific-interface/replay/checkpoint change. Publish exact accepted inputs
before any result launch; retain the existing native observer lifecycle when running.

First return to Root is this complete design and its explicit richer-contract cost.
The unresolved dependency is the one focused selection review/Root cross-question
disposition; it is not a new owner permission request. No result-producing operation,
code implementation, resource claim or cleanup has been created by this entry.

### B04 prospective node/accounting correction before selection freeze

Root's source-backed allocation correction, received after publication `029b36574`:
the design-only instruction meant no node use during preparation, not exhausted
remote capacity. The current peer allocation is approximately8 CPU cores/3.1GiB on
a20-core/15.8GiB wsl_4070 node. These are Root-reported allocation facts, not this DM's
fresh admission measurement. The proposal above inferred local necessity too early.

**Replace the proposed primary node with wsl_4070**, its configured
`/home/wu/.venvs/hmasd/bin/python`, sequential FP32 fits and one Torch/inter-op/BLAS
thread. The measured same-host base-work extrapolation remains about31.5min; budget
roughly35-50min for the new scientific workload before import/build, complete reading
and publication, with actual predictor/runtime overhead still unmeasured. Root will
verify the combined allocation and publish one concrete shared CONTROL notice before
launch, preserving Claude's two accepted fits. Fresh runner-side actual-node admission
remains necessary. This is shared-resource coordination, not per-fit scientific ACK.
No launch is authorized by this correction or attempted here.

Local_linux is a fallback only if actual remote insufficiency or unsuitability is
recorded at execution. Its45-90min estimate remains an unmeasured fallback estimate,
not a fresh timing or a reason to override the owner's remote-first preference.

Accounting is **9 policy continuation fits plus3 trained predictor instances** inside
the three F attempts. Each predictor consumes that F attempt's eligible native labels
and1024 extra supervised Adam calls:3072 extra calls total, with the separate label,
row-presentation and inference counts in the cost table above. They are not three
additional native-data collection attempts, and their training is not free. Cumulative
direction work would therefore be21 policy fits plus3 newly trained predictor
instances,21504 PPO updates plus3072 predictor updates and3063808 native team steps.
The scientific arms, dates/horizons, panel, packet assumption and pending independent
selection review are unchanged.

### B04 selected disposition and implementation scope

Root selected the complete design at `029b36574` with the node/accounting correction
at `192eacd23`. The complete independent selection answer and Root disposition are
published at `eefe34dc6`,
[continuity/forecast selection](../../archive/2026-09-29/RESEARCH-continuity-forecast-selection.md#answer).
I read the whole answer. It reconstructs the prior positive and adverse evidence,
endorses G/O/F as the smallest useful complete comparison, and records
`MATERIAL_DISSENT: no`. It specifically retains the competent bounded first-sampled-
then-central-command ordinary forecast, fixed-channel TTL limits, the40-byte richer
contract, the common-parent limitation, and the possibility that F sends a useful
private-state summary rather than establishing an accuracy-mediated mechanism.
Native gains, ordinary-only gains, MSE-only improvement, mixed continuations and
adaptation damage therefore keep their distinct prospective readings. No hold
executor, extra arm, pilot or further selection review is selected.

The direction is now exploring under the unchanged launch-bound lead literal
`Codex DM (native child)`. Root owns synchronization of the canonical remote control
checkout after this row publication and the already published shared allocation:
wsl_4070, sequential one-thread Torch/inter-op/BLAS content fits alongside Claude's
two accepted four-thread fits; service can use up to4 additional one-thread workers.
Fresh actual-node admission still applies. This control synchronization is an actual
execution dependency, not a scientific approval stage. There is no accepted B04
operation yet. I own the implementation L0 above, independent engineering review,
publication, execution, full reading, proportionate independent result diagnosis and
cleanup, without an automatic retry or successor.

Root also requested bounded **evaluation-only telemetry**, with no new episodes,
objectives or adoption criterion: record50 connected-user bits after each native
step by OR over the returned `[5,50]` connection matrix. Source inspection confirms
`envs/pettingzoo/uav_env.py:318-345` already exposes this matrix in the normal step's
global info. User index means the unchanged static `user_positions` row within the
episode; record those positions once and identify the bits as post-action tick
`t+1`, aligned with that transition's reward/service reading. The wrapper's returned
info must be checked during implementation; no extra simulator/model query is allowed.
At320x256x50 uint8 entries this is4096000 uncompressed bytes. Keep this telemetry out
of actor/critic inputs, packets, predictor targets and training data, and out of B04
selection/interpretation gates. Add a focused leakage/alignment test. This preserves
a later Root question's evidence option without asserting current unfairness or
selecting a fairness study.

### B04 implementation acceptance and fixed input binding

The scoped implementation is `experiments/candidates/uav_message_content/b04/`
with mirrored synthetic tests and independent direction-root `read_b04.py`.
The registered Implementer `/root/dm_delay_intent/implement_b04` returned the
collector/channel, exact-path warm start, detached predictor/PPO updates, fixed
nine-fit driver, frozen B0 panel and raw output schema. I read the full code and
tests, corrected aggregate accounting to include B0 and kept zero diagnostic
endpoints for G. Every final trajectory retains the actual old actor/critic fields,
forecast tail, dated endpoints, commands/positions, channel records and hashes,
native outcomes and evaluation-only connection bits. The pure NumPy reader rebuilds
transport, bounds, native metrics and conditional contrasts without simulator or
policy calls; it also accounts for all update and episode streams.

Independent registered engineering Reviewer
`/root/dm_delay_intent/review_b04` read collection through replay/update/evaluation
and raw reading against this contract and B02 source `02ede8a4a`. It found no
material engineering issue after the synthetic fixture's SINR dtype was corrected
from FP32 to native FP64; production code/tolerances did not change for that fixture
failure. The review verifies preserved old tensor paths, zero tail initialization,
explicit RNG/reset semantics, post-episode labels, detached predictor gradients,
stored behavior packets, clipped dated forecasts/TTL, nonfeeding ordinary shadows,
telemetry isolation and admission before scientific effects. Its final run passed
28 tests in11.11s. My combined run passed28 in11.66s, with automatic pytest scratch
teardown. These include all four arm types' complete256-step synthetic writer-reader
checks plus a miniature nine-cell driver, not native UAV episodes or a pricing pilot.
Full native read_run across manifests, checkpoints, update logs and320 trajectories
remains to be exercised on accepted outputs. No scientific result is claimed yet.

I accept the reviewed implementation for exact-input publication and the fixed B04
launch. The latest small reader change permits later reading from the canonical B
input after the temporary staging copy is removed; its digest is unchanged. Fresh
remote read-only verification confirmed the463357-byte B19451 SHA256 above and
metadata armB/master19451/input171/critic451/inheritedC digest
`456832faaa94afb22cf3faa00bb97b0f129e2f5b72b2eedbb1148523b088cdad`.
Because a snapshot launcher cannot bind an untracked absolute input inside its
author tree, stage exactly those bytes outside the checkout at
`/home/wu/hmasd-inputs/uav_message_content-b04-B-34871c49.pt`; reverify the declared
digest inside the admitted runner. This is a temporary463357-byte input duplicate,
not a new learned checkpoint or evidence copy, and will be removed after full
reading. Canonical B19451 stays unchanged. No pre-admission failed launch was needed
to discover this already documented B02 input-binding constraint.

Root resolved the shared-control dependency at2026-09-29T10:13:31.526153Z by a
locked canonical-node fast-forward from `5c6997722` to `e9faa4ad44827a61ca44d225cef4f03296b86467`.
Fresh `_require_policy` passed this exploring direction with policy digest
`027095b84343f72c961f5a8706f902c5ff90a5265da3cfe5ac226a964e49f12b`.
Root reports the existing five dirty launch-status blobs and sparse-pattern blob
unchanged; no control/status/claim edit or accepted operation restart occurred.
Only normal fresh actual-node admission and published exact source binding remain
before execution. Resource allocation and scientific endpoints remain as selected.

### B04 accepted operation and observation

Exact inputs were published/pushed at
`7bb6d2f8eedecd7479fc4cb830467b8c6601a5ec`. The configured supervisor accepted one
invocation, and the launcher subsequently admitted the scientific child at
2026-09-29T10:34:09.788643Z. Its native identities, immutable source snapshot,
command, output and operation reference are retained in
[`launch-manifest.json`](../../../../runs/uav_message_content/b04_future_motion/launch-manifest.json).
Fresh actual-node admission measured12747161600 physical/effective available bytes,
above the4GiB floor, in
[`admission-preflight.json`](../../../../runs/uav_message_content/b04_future_motion/admission-preflight.json).
The first cell reports one Torch thread and one inter-op thread; the CLI sets the
OpenMP/OpenBLAS/MKL/NumExpr/Accelerate limits to1 before numerical imports. No GPU
training or parallel content fits were added.

Preparation had no scientific failure: an initial plain-SSH Git fetch and a
missing-object `cat-file` lazy fetch stalled in remote HTTPS without the configured
network shell. I terminated only those two identified Git request trees; their SSH
exits143/255 and zero scientific launches were retained. A subsequent bounded
writer-lock wait expired while the service direction restored its own metadata.
After that owner released the lock, `zsh -lic` fetch succeeded. Git printed a
pre-existing automatic-repack bad-tree warning; source publication/snapshot checks
and actual admission then passed. No sparse/control/status edit, accepted worker
restart or scientific retry was used to resolve preparation.

`tools/hmasd_wait.py` is armed for this same operation, owner
`01a0ec87-9c4e-7722-945e-0ad2e0e7c410`, generation1,1500-second bounded window.
The first drain observes consistent accepted/running supervisor and child identities,
zero probe errors and no terminal event. This native DM remains active through
deterministic waits and same-handle drain/rearm; registration alone is not a queue
wake or a read result. No completed scientific conclusion exists at this boundary.

At the generation1 observer checkpoint (drained11:00UTC), the same operation remains
consistent/running with no probe errors and the first six cells technically complete;
the remaining third-master cells and B0 panel are not yet all collected/read. Native
queue delivery returned `-32600` (unloaded spawned sub-agent), as anticipated; the
observer itself remained healthy. This active DM consumed that checkpoint and rearmed
the same operation as generation2, without a launch, restart, endpoint change or
partial-result interpretation. The original35-50min estimate remains adequate.

<a id="b04-complete-reading"></a>
### B04 complete reading: better fallible forecasts, no demonstrated package increment

The one accepted operation exited0 at2026-09-29T11:11:40UTC. The terminal witness
and same-handle observation agree; runner and supervisor are absent. Generation2
event `c6c705b894797619f87f7e13` was consumed, with zero probe errors. The subsequent
generation3 observer was stopped and drained with no unread events. The native
queue's unsupported-child delivery error did not restart the scientific work.
The fixed nine continuation fits, three trained predictors and frozen B0 panel are
complete. No cell was extended, replaced, selected early or retried.

I ran the published independent NumPy reader over **all320 complete H256 raw
trajectories**, manifests, checkpoint hashes and training/update streams. It reports
`all_checks_passed: true`, with zero added native steps, optimizer calls or model
calls. The checks reconstruct native movement/clipping, send-time packet geometry
and dated forecasts, fixed RR transport and RNG addresses, arrival/cache expiry,
old/new actor and critic inputs, scene/action/channel identities, user connections,
native J/service/Q and complete exposure accounting. This is an independent
numerical reconstruction, not320 independent training replications. The separate
registered scientific critic's diagnosis is recorded below.

The compact collected [summary](../../../../runs/uav_message_content/b04_future_motion/summary.json),
[full reading](../../../../runs/uav_message_content/b04_future_motion/reading.json)
and [exit witness](../../../../runs/uav_message_content/b04_future_motion/process-exit.json)
have identical local and canonical-node hashes. Respectively their SHA256 values
are `0ec4d12e9699745a8388cffe23b313d0b468b1c9f6065c2beff969da852f6e87`,
`1238939e1a4fec49ab4a9671836641551238a32441965a6b510172616ddbcfa2` and
`39f2ae94a76bee6a5026e5ab0fe79991e2007d1754b4d8a8ee4230c4168d9554`.
The one durable bulk copy is
`wsl_4070:/home/wu/projects/HMASD/runs/uav_message_content/b04_future_motion/`:
99345917 apparent bytes including directory entries,100286464 allocated bytes at
collection. All320 compressed raw files total81191722 file bytes; their individual
hashes/locators and all18 initial/final checkpoint identities are bound by the
summary, and the reader also hashes each update stream. Keep the unique raw,
checkpoints and episode/update streams. Empty stdout/stderr have the standard
empty-file SHA256; there is no hidden scientific failure log. Source and the
one-shot runner/tests remain recoverable at
`7bb6d2f8eedecd7479fc4cb830467b8c6601a5ec`.

#### Complete native outcomes

All readings below are final32-world means, with service in connected users per
tick. Native physical J equals net J plus.001 in every arm; no cost saving explains
the differences. B0 uses the original28-byte contract and is an explicit
cross-contract capability anchor, not a primary40-byte trained comparator.

| Continuation | Arm | Net J | Service | Q |
|---|---|---:|---:|---:|
|19501|G|.161905260|9.079468|.119309036|
|19501|O|.251428127|14.961914|.143204435|
|19501|F|.220705895|12.869873|.138425574|
|19502|G|.229489094|13.898682|.119691838|
|19502|O|.209828483|12.457275|.121422090|
|19502|F|.197693989|11.628662|.119642398|
|19503|G|.231786208|13.317139|.154487557|
|19503|O|.226120131|13.405518|.131476282|
|19503|F|.239545562|14.163208|.140868834|
|frozen|B0|.235095768|14.075684|.130120659|

G/O/F continuation-average net J is .207726854/.229125580/.219315149;
service is12.098429/13.608236/12.887248. The primary **F-O** net-J mean is
**-.009810431**, continuation differences
`[-.030722232,-.012134494,+.013425432]`; its descriptive df2 t95 interval is
`[-.064872340,+.045251477]`. F-O service is **-.720988**, differences
`[-2.092041,-.828613,+.757690]`, interval `[-4.268115,+2.826140]`.
Q difference is+.000944666 with both signs across continuations; interval
`[-.017607341,+.019496674]`. Mean per-world worst-tick service is lower for F
than O in all three continuations, by1.3125/.1875/.09375 users; pooled difference
-.53125, interval `[-2.216003,+1.153503]`. This last behavior reading is not a
new adoption gate.

F-G has favorable sample means, **+.011588295 J/+.788818 service**, but mixed
continuation J `+.058800635/-.031795106/+.007759354` and service
`+3.790405/-2.270020/+.846069`. Its intervals are
`[-.101238950,+.124415539]` J and `[-6.739654,+8.317291]` service. O-G also
has favorable pooled means, **+.021398726 J/+1.509806 service**, but J
`+.089522868/-.019660612/-.005666078` and service
`+5.882446/-1.441406/+.088379`; intervals
`[-.126185728,+.168983180]` and `[-8.087150,+11.106762]`. These are
three matched continuation contrasts from **one selected B parent**, with32
nested deployment worlds each, not96 independent learning replications. Wide
intervals and sign reversals do not demonstrate equivalence or impossibility;
there is no post-hoc all-seeds-positive rule.

All three arm averages fall below B0: G/O/F J differences are
`-.027368914/-.005970188/-.015780619`, service
`-1.977254/-.467448/-1.188436`. G loses both J and service in every
continuation. Its19501 deficit alone is-.073190508 J/-4.996216 users against
B0, so the positive F-G/O-G pools compete with degraded G, not a demonstrated
forecast-over-preserved-competence result. The zero-initialized added inputs kept
the initial function; they did not keep it unchanged through PPO. This does not
erase the positive O19501 endpoint (+.016332359 J/+.886230 service versus B0)
or F19503 endpoint (+.004449794 J/+.087524 service). Neither endpoint is newly
selected for deployment or confirmation from this same exposed panel.

All signed per-world differences and extrema remain in the reading, including
F-O's24/16/11 J-loss worlds and25/16/12 service-loss worlds. The worst F-O
case,19502 world23, loses **-.133423687 J/-8.277344 service**; the best,
19503 world0, gains **+.096653747/+6.226563**. F-G retains the19501 world16
gain **+.158066888/+9.445313** and19503 world12 loss
**-.100442192/-6.816406**. Favorable sample means are not discarded, and
the adverse tail is not reduced to a standard error.

Boundary/altitude behavior also changes. Mean boundary fractions for G/O/F are
.341463/.329004/.445475 versus B0 .162646; mean ceiling fractions are
.019393/.007104/.097282 versus .001514. F19501 spends.21875 at the ceiling
with mean altitude98.4668m, compared with B0's55.3449m; F19502/F19503 mean
altitudes are86.4692/57.4593m. These are retained policy differences, not
battery, collision-safety or real-flight risk measurements, and not an identified
cause of the native losses.

#### Intermediate prediction and its limit

The learned forecasts were neither expired endpoints mislabeled as future nor
unused outputs. Each final32-world cell sent8192 packets, delivered8082 before
termination and censored110. The cached future endpoint appeared in160688
receiver-record uses:64452 at ages1..4 and96236 at ages5..9, always with1..9
ticks remaining. There were178 delivered shortened-horizon sends near termination.
These equal exposure counts follow the common exogenous transport, not forecast
quality. Forecast fields expire at ageK while geometry remains; the dated endpoint
continues to be a fallible prediction, never a hold or future-truth commitment.

On **each F policy's own realized trajectories**, compare its learned endpoint
with the qualified ordinary shadow computed from exactly that same lawful
send-time state, first sampled command and subsequent central-command persistence.
Receiver-cache-weighted horizontal RMS errors in meters are:

| F continuation | Learned | Qualified ordinary shadow | Age5..9 learned / ordinary |
|---|---:|---:|---:|
|19501|67.9465|81.8201|67.6840 /81.7171|
|19502|68.8663|77.8686|68.9070 /77.7854|
|19503|65.9057|75.1994|65.5677 /74.4383|

Height RMS also falls,28.4080/33.9200/13.8026m versus ordinary
30.9381/37.4492/15.4275m. The stronger ordinary baseline matters: a
sampled-command-only persistence shadow has horizontal RMS
194.1585/205.1770/204.3453m on these same trajectories, far worse than the
selected bounded central-command predictor. This shadow is a diagnostic, not a
fourth trained arm. O's own-trajectory errors cannot be interchanged with the
same-F-trajectory comparison because the realized paths differ.

The improvements are not universal across losses or horizons. Cache-weighted
height MAE worsens for19501 and19503 (19.1563 versus18.8588m and8.3101
versus5.9576m), while19502 improves. At shortened terminal horizons,19502
height RMS worsens35.3908 versus32.5773m; terminal height MAE worsens in
all three. Horizontal RMS improves in both early and late age bins, so the
record does not isolate an older-cache-specific benefit. Initial/final training
loss summaries likewise do not justify universal convergence: first16 versus
last16 rollout means are.0211098/.0226111,.0215586/.0215100 and
.0234622/.0170519. Online target distributions change during policy learning.

With the actual pre-decision recurrent state held fixed, replacing F's forecast
fields by its ordinary shadows changes the actor central command by RMS
.0040383/.0100610/.0054207, maxima.0187616/.0308269/.0261469.
Blanking O's forecast fields gives RMS.0231282/.0193388/.0156480. These
nonzero responses and the exposure above establish that the extra content can
affect the policy, not that it improves action selection or causally mediates
reward. The saved shadows are never fed into the real rollout. Old actor
parameter displacement is23.08..30.30% of its initial norm across the nine
fits; O/F new projections and all three predictors move, while G's unused
forecast projections remain exactly zero. There is real primitive policy
learning and predictor learning, not an untrained or no-communication control.

Thus the predicted **forecast fidelity intermediate is supported**, including
under stale-but-future cache use. The proposed consequence, useful complete F
coordination beyond matched O, is **not demonstrated**. The loss in19502
world23 occurs despite its same-F horizontal RMS improving92.15 to80.22m,
as independently rederived by the critic. Better forecasts alone cannot be
credited with a native payoff, and this finite result is not a proof that
future information lacks task opportunity. Receiver co-adaptation, a service-
insensitive endpoint target and general continuation drift remain possible;
this batch does not causally identify one as the failure explanation.

Root's optional connected-user telemetry is present as4096000 uncompressed
uint8 bits: native OR over UAV assignments after each action, aligned to reward
at tick`t+1`, with stable user index bound to that episode's saved static
positions. The reader checks its shape/counts against served users. It was not
fed to actor, critic, packet, predictor training or B04 selection, and I have not
introduced fairness/coverage metrics or a new adoption criterion from it.

#### Actual and cumulative cost

The measured scientific batch used2248.564107s wall (37.476min),2248.187853
process CPU seconds and540116KiB Linux process-lifetime peak RSS, with one
Torch/inter-op/BLAS thread and no GPU. This is within the corrected35-50min
scientific estimate; it is not the unmeasured local fallback rate.

| Exposure | Actual B04 |
|---|---:|
|Policy continuation fits / trained predictor instances|9 /3|
|Training / final evaluation episodes|4608 /320|
|Explicit resets / constructors|4928 /10|
|Training / evaluation native team steps|1179648 /81920|
|Total team steps / motion samples|1261568 /6307840|
|PPO updates / replayed actor rows|9216 /23592960|
|Predictor Adam calls / eligible labels / row presentations|3072 /388560 /1554240|
|Send-time predictor forwards / diagnostic actor forwards|417792 /49152|
|Behavior actor / critic forward calls|1261568 /1261568|
|PPO actor / critic batched forward calls|9216 /9216|
|Behavior actor / critic rows|6307840 /1261568|
|PPO critic rows|4718592|
|Broadcasts / delivered / terminally censored packets|1261568 /1246500 /15068|
|Rollouts / evaluation optimizer calls|2304 /0|

The full raw reader adds84.04s wall,84.67s user+system CPU and55668KiB peak
RSS, with0 simulator/policy calls. The three documented focused test runs cost
11.66s/10.45s/11.11s wall, separate from science. Implementation, source/network
reconciliation, manual reading and independent reviews were not fully instrumented;
their cost is unknown, not zero or falsely reported as the4-6 agent-hour estimate.
The critic's selected raw checks are additional read-only support work, not fits.

Including inherited B01-B03, paid direction totals are **21 policy fits plus3
trained predictors,3063808 native team steps,21504 PPO updates plus3072
predictor updates**, and4939.467107s measured scientific wall. The separate
engineering/readback and earlier incompletely measured support remain additional.
Three continuations here do not buy independent retraining of B19451, and the
40-byte packet assumption remains42.9% wider than B0 at the original abstract
fee/delay, not zero-cost physical bandwidth.

#### Independent diagnosis and investment disposition

Registered ResearchCritic `/root/dm_delay_intent/diagnose_b04` worked in a separate
context without DM/Root conversation inheritance. Its assignment included the
prospective summaries, so the review was not blinded. It reconstructed results
before receiving my explanation. It checked the published source, manifest/exit,
configuration, counts, reader, prospective rule and consequential B01-B03 evidence;
independently hashed and reconstructed seven positive/adverse remote trajectories
and the canonical B19451 hash; and relied on the full reader for the remainder.
It made no fit, policy or simulator call. The seven traces were F/O19502 world23,
F/O19503 world0, and F/G19501 plus B0 world16. It finished all source/raw access
before allowing retirement of the unused launcher source, explicitly excluding
canonical raw/checkpoints/streams and the bound parent from that cleanup.

Its substantive recommendation is **retain B19451 for compatible provisional use
and close the exact B04 recipe, with no additional run selected**. The critic
retains the finite learned endpoint-prediction capability and the19503 native
positive, while declining the inference from prediction accuracy or immediate
input sensitivity to beneficial complete coordination. It emphasizes the adverse
F-O mean, the favorable but G-degradation-sensitive F-G mean, all adverse worlds
and altitude/boundary changes, conditional-parent intervals, the40-byte abstract
contract and incomplete support-cost measurement. The older-message-specific
story is unsupported because both age bins improve. The critic considers finite
motion optimization/co-adaptation around the competent learned parent the strongest
simpler competing explanation, not an isolated demonstrated cause. It preserves
B01 own learning, B02 favorable L sample means and reversals, and all B03 asset
gains over C. Its conclusion is not that forecasting lacks task opportunity.

The critic also compared concrete next purchases against stopping. Frozen F with
ordinary forecasts substituted throughout deployment would cost0 fits and24576
new steps across three matched panels, plus unmeasured implementation/check/read
cost. Either sign would concern dependence/co-adaptation or predictor removal for
those assets, not overturn the primary separately-trained F-versus-O comparison
or itself justify replacing B19451. No predictor-removal deployment decision is
pending, so that observation is not bought. An unchanged F/O continuation repeat
alone would cost6 policy fits,3 predictors and835584 steps before new anchors;
it refines conditional recurrence, while independent-parent evidence additionally
requires parent construction. A changed commitment/cadence/information contract
could address another question, but must grant the same addition to the competent
ordinary comparator and price its cost. None is an automatic repair selected by
this result. The critic reports **`MATERIAL_DISSENT: no`**.

I adopt that recommendation. B04's result strengthens finite forecast learnability
and weakens the expired/unexposed/entirely-ignored explanation; it does not establish
the predicted complete-package improvement. The broader substantive question remains
open, but unchanged extra epochs, seeds, head capacity or a hold executor have no
selected rationale here. I decline further investment in this exact recipe, retain
the learned and ordinary positive assets as evidence rather than retrospectively
selecting a winner, and retain B19451 for its existing compatible provisional use.
This is a read-result stop, not a technical failure, a claim of equivalence, or a
pause waiting for permission. The direction returns to reserve with no active
producer, unread result or selected successor. Root owns any future cross-question
selection; a consequential changed deployment/decision premise, rather than better
MSE alone or spare capacity, is the concrete re-entry condition.

Cleanup scope after publication is the reconciled exact B04 launcher source, the
temporary staging copy of B19451, consumed request scratch and obsolete B04
one-shot implementation/tests. A repository import/entrypoint scan found only
self-imports and the mirrored B04 tests, with no external executable consumer.
Keep direction-root `read_b04.py` and its synthetic reader tests, all required
canonical result evidence, B19451 and prior B01-B03 records. Historical code paths
in this notebook are pinned to source `7bb6d2f8eedecd7479fc4cb830467b8c6601a5ec`,
not promises that retired entrypoints remain on current main. No tar, copied
worktree or backup chain is needed. Actual deletions and allocated-byte change
will be recorded below after the maintained collector succeeds.

#### B04 retirement completed

After result publication `0f8627a95`, all scientific/reader processes were complete,
the critic had released its source/raw reads and the observer was stopped. The
maintained exact-target snapshot collector first refused an unprivileged process
scan at `/proc/660/cwd`; its supported read-only `--sudo-process-scan` retry
established eligibility. Under the normal canonical-node writer/admission locks,
`scripts/hmasd_snapshot_gc.py --snapshot db7c4d80a91442219c6da17294b8a8e1
--sudo-process-scan --apply` removed that source snapshot. The source commit remains
in published Git history, and the operation claim, manifest and exit witness remain.
This resolved the concrete process-scan limitation; no manual snapshot deletion,
permission change or shared Git repair was used.

The following exact targets are now absent; before/after allocated-byte readings
show **803610624 net bytes reclaimed** from this cleanup scope:

| Deleted target | Allocated before | After |
|---|---:|---:|
|wsl_4070 `.git/hmasd-launch-sources/db7c4d80a91442219c6da17294b8a8e1`|802963456|0|
|wsl_4070 `/home/wu/hmasd-inputs/uav_message_content-b04-B-34871c49.pt` staging duplicate|466944|0|
|local `experiments/candidates/uav_message_content/b04/`, including bytecode|118784|0|
|local `tests/experiments/candidates/uav_message_content/b04/`, including bytecode|53248|0|
|local `temp/directions/uav_message_content/`, only the consumed B04 request|8192|0|

The staging file had no `fuser` consumer; the canonical B19451 was already
independently hash-verified and remains at its original B02 path. The canonical
B04 result directory stays at100286464 allocated bytes, unchanged through cleanup.
No raw trajectory, unique checkpoint, stream or evaluation-only user telemetry was
deleted. No second bulk copy or archive was created. Git object storage and whole-
host free space are not the measured scope of the reclamation claim.

The seven one-shot source/test files were removed with explicit-path `git rm`;
their historical source is `7bb6d2f8eedecd7479fc4cb830467b8c6601a5ec`. The
retained pure reader and its independent synthetic fixtures still pass **19 tests
in2.73s** after that retirement, with pytest scratch automatically removed and no
imports of retired code. This check adds support cost only. There is no cleanup
blocker or redundant B04 scratch left in these targets. Required positive/adverse
evidence, prior records and the private consumed observer status are retained.

<a id="b05-retained-control-prospective"></a>
## 2026-09-29 - B05 prospective: bounded learning around the retained controller

Root's published selection and writer handoff are `bece6ea4b35870d9e18cfddd2bd633975faadd9b`.
The direction is active under the unchanged launch lead `Codex DM (native child)`;
the current native writer is `/root/dm_retained_control`. I read the complete Pro
answer, independent selection assessment and adopted disposition in the
[retained-control selection](../../archive/2026-09-29/RESEARCH-retained-control-selection.md).
The adequate separate-context review reports no material dissent and covers this
unchanged comparison. It is reused, not repeated for implementation. No accepted
old operation is resumed. This is exploration, not confirmation; no claim note or
independent-parent claim is introduced.

### Question, structural premise and competing explanation

Can bounded learning around useful decentralized B19451 produce a useful complete
native controller, and does ordinary dated future-motion content help within that
extension family? The intended contribution is conditional capability/use and its
empirical boundary, not a new residual architecture or a causal diagnosis of B04.
The current published [communication background](../../RESEARCH.md#5-技能和异步性是组织决策的方式其收益需要证据)
at `bece6ea4b` changes the comparison concretely: retain B19451 as an unchanged
complete-use anchor, preserve the original geometry, and distinguish restricted
learning from the incremental value of qualified ordinary forecasts. B03's joint
B/O/L gains over C, B02's favorable learned-content means and reversals, and B04's
learned forecast accuracy/positive endpoints all remain capabilities/evidence.
The B04 adverse F-O mean and degradation of every G instance remain contrary
evidence; no new name resets those costs or verdicts.

The constructive conjecture is that a fixed useful motion mapping can support
additional message-conditioned control without relearning that mapping. The
strongest ordinary rival is useful finite optimization under the old geometry
alone; M_G can succeed without crediting future content. A small mean correction
may also be ineffective at the inherited noise scale. Parameter freezing excludes
gradient changes to the base; it does not hold its closed-loop state distribution
fixed and cannot guarantee competent trajectories. The base GRU must consume real
observations and previous executed composed actions throughout.

I checked the three local literature catalogs for the two named method bridges
(no matching indexed record), then read the primary passages directly:
[RPL arXiv:1812.06298v1, section IV](https://arxiv.org/pdf/1812.06298v1)
defines an additive fixed-controller residual and zero last-layer initialization,
and warns that actor-critic learning can degrade a good initial policy;
[RESPRECT arXiv:2401.14858v1, section III-B](https://arxiv.org/html/2401.14858v1#S3.SS2)
fixes a pretrained RL policy and initializes residual critics from pretrained
weights. These support the construction, not success or novelty here. They omit
the present jointly adapting teammates, delayed private messages and endogenous
shared trajectories. No proof, toy-success or headroom pilot is bought.

### Frozen contract and decision exposure

Use unchanged native N5, 50 static uniform users, H256, free-space vectorized
radio, primitive sampled actions, fixed RR sender `t % 5`, GOOD/BAD persistence
.95 and send-time delay1/5, no loss, fee.001 per step. All arms send the same
seven geometry fields plus three FP32 values: 40 bytes rather than the original
28, a42.9% increase under unchanged abstract fee/delay. This is not free physical
bandwidth. No ACK/served-user identity, map truth, reward change, commitment,
learned predictor, additional send or altered terminal semantics is included.

Canonical parent is
`wsl_4070:/home/wu/projects/HMASD/runs/uav_message_content/b02_preserved_scalar/19451/B/final.pt`,
463357 bytes, SHA256
`34871c49874ec716c21438581facfaeca8a25930304a39eb26e001fb2b259da2`.
I rehashed those bytes on the node before this declaration. Its metadata is
B/master19451, input171/critic451, inherited C SHA256
`456832faaa94afb22cf3faa00bb97b0f129e2f5b72b2eedbb1148523b088cdad`;
source identity `02ede8a4a75cc83e6e18d8b6619f1cfa84bc8d92`. Stage only this bound
file outside the source checkout for immutable launcher input, and recheck its
digest in the admitted runner. Canonical B19451 remains the required evidence.

| Arm | Controller and payload | Training |
|---|---|---|
|B40|Frozen B19451, seven old geometry floats plus three ignored zeros|0 fits; one final32-world reference panel|
|M_G|Same frozen base plus a separate bounded mean residual; geometry plus zeros|3 conditional continuation fits|
|M_O|Same residual learner and base; geometry plus qualified dated ordinary endpoints|3 conditional continuation fits|

For M_G/M_O, `mu = mu_B + .10*tanh(g_theta)` and the actual sample is
`u = mu + sigma_B*epsilon`, executed as `tanh(u)`. The correction is in PRE-TANH
MEAN units. All base encoder/GRU/mean/log_std parameters and its fixed input
scaling stay frozen. There is no running normalizer in this source. The residual
is a separate250->64 tanh->3 MLP over the legal current186 inputs and the
frozen64-dimensional recurrent output; its last weight and bias start at zero.
Future inputs never enter the base GRU. Residual hidden initialization is shared
between M_G/M_O within a block and fresh across blocks. This is one fixed network,
not an outcome-dependent capacity choice. The inherited sigmas are approximately
`[1.16064,1.11096,1.13091]`: the bound is .086-.090 SD per coordinate and limits
the immediate same-history/noise action difference to.10, or about3m per coordinate
in one step. It places no bound on later trajectory or complete service loss.

The critic starts from the parent's451-input critic with a separate zero75->128
forecast projection, yielding526 inputs. It trains independently of the frozen
actor. Both learner arms use two complete episodes per rollout, undiscounted
terminal returns with no bootstrap, standardized team advantages, per-agent
three-coordinate composed tanh-Gaussian PPO ratios clipped[.8,1.2], chunk32
replay, four full-rollout epochs and lr3e-4 Adam(.9,.999),eps1e-8, no decay.
Residual and critic have separate optimizers and separate.5 gradient clipping;
actor loss retains the.01 inherited Gaussian-entropy term (constant at fixed
variance), critic loss is.5 mean squared return error. The critic cannot rescale
actor clipping through a shared gradient norm. This is fixed for both arms.
Replay uses detached realized packets, observations and actual entry GRU states;
it neither regenerates packets under new parameters nor creates a base-only
counterfactual trajectory. All recorded likelihoods describe the actual composed
sampled distribution, not the base distribution alone.

At each send t, M_O predicts the sender's position at `t+K`, K=min(10,H-t): apply
the actual composed sampled first command with native clipping, then persist the
current composed central command `tanh(mu)` for K-1 steps with clipping. Packet
dates and cache remaining horizon retain B04 semantics: delivery precedes action,
only delivered forecasts are read, forecast coordinates expire at ageK while
geometry remains, and no future truth is used to generate content. No forecast
commitment is enforced. B40/M_G send exactly zero tails at all times.

### Seeds, readings and prospective outcome branches

Fixed new masters are19601,19602,19603, cell order M_G then M_O within each.
For master m, construction seed100000*m+11, training scene seeds100000*m+1000+e,
channel seeds100000*m+6000+e (e=0..511), and one continuous motion RNG
100000*m+21. The two arms match all these exogenous streams and initialization.
Final-only evaluation for every cell and B40 uses32 fresh common tuples:
scene1960002000+e, channel1960007000+e, motion1960003000+e (e=0..31).
No initial scoring panel, intermediate checkpoint selection, extra panel, omitted
adverse world, fourth block or automatic retry is selected. The zero-residual
identity check is correctness work at identical inputs/history/noise, not an
additional significance panel. B40 is evaluated once after the six fixed fits.

Read complete H256 J_net and users/step together, physical J/Q/fee decomposition,
all instances and signed world differences, worst-step service, zero-service
counts and longest intervals, boundary/floor/ceiling fractions and mean altitude.
Stable user positions and post-action connected-user bits stay evaluator-only,
outside actor, critic, packet, reward and training. These behavior measures are
not energy or physical-flight safety endpoints. The raw reader reconstructs the
transport, action/composition/likelihood, native outcomes and cost counts.

Intermediate readings are base tensor identity, nonzero residual execution,
pre-tanh magnitude and fraction of coordinates with abs(correction)>=.095,
same-noise executed-action changes, and M_O response when valid forecast tails
are zeroed at the same real pre-decision state. This shadow consumes no RNG and
never enters the actual rollout. Exposure/sensitivity supports an opportunity
to affect behavior, not beneficial mediation. Record actual residual and critic
losses, gradient norms, parameter movement and separate optimizer calls.

Compute paired M_O-M_G and each extension-minus-B40 differences within each
block, then the three block means and descriptive t95 intervals with df2.
These describe conditional continuation variation on one parent and this fixed
deployment panel. Separately report paired world-level t95 df31 intervals per
fixed endpoint and the average-over-blocks deployment contrast; shared worlds
and time rows never increase training n. These intervals assume independent
draws at the respective unit and are not selection-adjusted confirmation.
No fabricated application MEI, unanimity gate or equivalence region is used.

Joint J/service gains for M_O against M_G and B40 support a conditional
forecast-assisted extension. Gains for M_G against B40 without a resolved M_O
increment credit restricted continuation. M_O>M_G with both below B40 does not
establish net usefulness. Active adverse corrections, mixed blocks or wide
uncertainty end this fixed batch and return the next investment choice to Root;
there is no radius/noise/network/training/seed scan. Broken identity, information
or likelihood yields a technically missing comparison. None of these outcomes
alone closes all future-motion or residual-learning questions.

### Prospective cost and L0

Six512x256 fits cost786432 training steps; seven32x256 final panels cost57344
evaluation steps, total843776 and4218880 motion samples. There are
1536 two-episode rollouts,6144 PPO update records,6144 actor Adam calls and6144
critic Adam calls,15728640 replayed actor rows and3145728 critic replay rows.
No predictor is trained. Count actual forward/diagnostic calls and all correctness
exposure separately. One configured wsl_4070 worker uses one Torch/inter-op/BLAS
thread, subject to fresh node admission; Claude's accepted work remains intact.
B04's2248.187853 process CPU seconds/1261568 steps implies about.418 CPUh by
linear scaling only, not a bound or wall promise. Pro's4-8 agent-hour support
estimate is unverified. Read-only preparation began about13:05UTC; meaningful
support timings will be recorded with their limits. Stop and reconsider with Root
if engineering/recovery substantially expands without corresponding value.

Inherited paid exposure before B05 remains21 policy fits plus3 predictors,
3063808 result steps,21504 PPO plus3072 predictor updates and4939.467107s
scientific wall, with additional incompletely measured engineering/readback.
A complete B05 would yield27 policy fits plus3 predictors and3907584 result
steps; inherited failed/adverse studies are not removed from that accounting.

L0 deliverable: implement exactly this composed residual policy, lawful collector,
six-fit driver, common B40 evaluator and complete compact/raw reader under
`experiments/candidates/uav_message_content/b05/` and direction-root `read_b05.py`,
mirrored tests, `runs/uav_message_content/b05_retained_control/`, and owned
`temp/directions/uav_message_content/`. Reuse existing shared native host, base
model, primitive sampler, PPO loss and dated-channel semantics; do not copy or
modify shared core. Historical B04 source is7bb6d2f8e for selective reference,
not a revived batch. I own NOTES, run/channel/collector/reader and acceptance.
A bounded Implementer owns only the composed model/PPO modules and their model
tests, with no index/commit/launch/notebook authority and no children. Independent
engineering review covers all high-risk executable changes before launch.

Checks: exact zero-residual base mapping and sampling at same history/noise;
frozen base despite active residual and critic updates; no forecast-to-base path;
composed log-density analytic agreement; lawful detached replay and correct actual
action history; clipped first-sampled/central persistence and date/expiry;
matched RNG/initialization and fixed complete counts; evaluation-only user bits;
miniature synthetic driver and full-H synthetic writer-reader. These tests are
correctness exposure, never native scientific or positive-result gates. Publish
exact accepted inputs before runner-side admission. Preserve terminal failures,
read the full output with independent material diagnosis, publish this direction's
standing/shared implications and measure exact cleanup at the result boundary.

### B05 implementation accepted, before native execution

The bounded registered Implementer
`/root/dm_retained_control/implement_composed_policy` returned the frozen composed
model, independent PPO updater and six focused tests. I read its full diff and
checks. I corrected its initial agent-average surrogate reduction to the inherited
sum-over-five-agent reduction before any result execution; the documented
per-agent density and clipping are unchanged. The accepted code reuses the
existing base network and PPO primitives rather than copying shared learners.
I implemented the lawful channel/collector, six-fit driver, B40 reference and
complete reader. The reader reuses the maintained B04 transport/native numerical
reconstruction; B05 adds composed density, bounded/executed correction, service
tails, actual checkpoint tensor identity, update streams and separated df2/df31
readings. It uses torch only to deserialize checkpoints, with no policy,
environment or optimizer calls during readback.

The integrated tests passed32 in7.37s, then32 in7.97s after reader/checkpoint
coverage and CLI repair. These are synthetic correctness checks, not native UAV
episodes or additional scientific fits. Pytest removed its invocation scratch.
Coverage includes same-history/noise zero identity; matched arm RNG and detached
actual-action inputs; active residual/critic updates with zero base movement;
three arm types' full256-step writer/reader including composed densities and
qualified clipped forecasts; a miniature six-fit/one-reference driver; and its
actual initial/final checkpoint and update-log readers. Full native `read_run`
over the224 promised trajectories, admission manifest and terminal witness has
not yet run and remains the result-collection obligation.

Independent engineering Reviewer `/root/dm_retained_control/review_b05` worked
read-only in a separate context. It found the direct reader command initially
failed before argparse because the repository root was not on sys.path. I added
the same root bootstrap used by native entrypoints; reviewer independently
verified `--help` exit0. Its final assessment is **no material finding remains**
after tracing checkpoint binding/freezing, RNG, composed sampling/density,
actual-history recurrent replay, agent-summed PPO/separate clipping, dated
forecasts, native inputs/outcomes, counts, admission ordering and partial-failure
preservation. Its full-run deserialization/manifest integration coverage is static;
it does not claim a remote native run or scientific checkpoint verification.

My remote read-only load directly verified the canonical parent metadata and
sigmas `[1.1606353521347046,1.1109598875045776,1.1309105157852173]`, in addition to
the earlier SHA256. No source contradiction was found. Source/publication controls
were refreshed before implementation; canonical remote RESEARCH still carried
the old B04 row. I reported that concrete shared-control dependency to Root and
also identified that the new published word `active` must be `exploring` for the
existing launch parser. No refused scientific invocation or replacement attempt
was used to discover either condition. These are ordinary control corrections,
not a new scientific approval requirement. The exact run tag remains
`b05_retained_control`, and no native fit has yet started.

Root completed the shared control reconciliation at published
`08b694b054ec630070261699010f9cecba224b65`: the canonical node fast-forwarded
to current main, the recognized state is `exploring`, and the exact existing
`Codex DM (native child)` lead passed the local policy parser. Root reports both
shared locks released, all five dirty status-file hashes and sparse-selection
hash unchanged, and no scientific invocation. My direct remote HEAD check agreed.
The accepted scientific source remains
`69785db45a1240046f7d1a066dbe53a3b710e7c0`; this control-only descendant does not
change its inputs. The canonical parent was staged as the single external input
`/home/wu/hmasd-inputs/uav_message_content-b05-B-34871c49.pt` and SHA256 verified;
that temporary 463357-byte duplicate will be removed after collection. Fresh
published-policy and actual-memory admission remain launch-time checks.

### B05 accepted operation and observation

The configured remote supervisor `uav-content-b05-69785db4` invoked the admission
kernel once. Native acceptance is2026-09-29T13:45:13.330252Z, claim
`36e95a98916c0da436565f42501a6af537ede4d86a1a936286083ca117798538`, with immutable
source snapshot `e6bc0c8404bc42218708e367eb8a1c37` at the accepted scientific SHA.
The retained run manifest binds supervisor PID997054 and runner PID997055 to
their Linux boot/start-tick identities. The fresh control observation was main
`d9b3708e62a71e4516102b91b4b23667ee3fec6e`; preflight measured11810435072 available
physical bytes against the4294967296-byte floor and passed. The supervisor's own
exit0 is launch delivery, not completion of the scientific child.

The same claim is observed by `tools/hmasd_wait.py`, generation1/window1500s,
using owned private state `temp/directions/uav_message_content/b05-wait` and the
read-only remote `hmasd_launch.py status` probe. First drain independently found
both native identities running, consistent records and no exit witness. I keep
this native child turn active for deterministic observation and the full reading;
registration is not an assumed future wake, and no replacement worker is allowed.
Manifest/preflight compact copies are retained under
`runs/uav_message_content/b05_retained_control/`; the canonical remote output
directory remains the sole raw/weight store while the run is live.

<a id="b05-complete-reading"></a>
### B05 complete reading: conditional continuation gain, forecast increment unresolved

The fixed operation exited0 at2026-09-29T14:14:19.746Z. Its terminal witness and
same-handle observation agree, with runner/supervisor identities absent and
consistent records. At the generation1 checkpoint the observer was rearmed for
the same claim as generation2. The terminal event
`ca122fd22b17696fa14c9369` was read, the observer was stopped, and no scientific
worker was restarted or replaced. Native queue delivery returned the known
unsupported spawned-child error `-32600`; deterministic observation and this
active child turn continued normally. The complete event is retained in
`runs/uav_message_content/b05_retained_control/observer-terminal.json`.

The accepted pure reader at source69785db45a1240046f7d1a066dbe53a3b710e7c0 read
**all224 full-H256 trajectories**, all3072 training episode records, all6144 PPO
records and all12 initial/final learned checkpoints. It reports
`all_checks_passed: true`. No reader repair, added model call, native step or
optimizer call was needed. Checks cover the canonical parent, matched initial
tensors/exogenous streams, frozen base and inherited sigmas, detached actual
history, the composed sampled density, physical movement/clipping, original
geometry, dated future fields/cache expiry, evaluator-only connected-user bits,
J/service/Q/fee, count closure and unchanged evaluation parameters. The largest
reconstructed density discrepancy is2.546e-6, within the frozen numerical check.
Initial/final base tensors are byte-identical to the canonical parent; executable
freezing/optimizer exclusion is also checked. There is no per-update archive of
base tensors, and endpoint identity is not a closed-loop competence guarantee.

The compact [summary](../../../../runs/uav_message_content/b05_retained_control/summary.json),
[full reading](../../../../runs/uav_message_content/b05_retained_control/reading.json)
and [exit witness](../../../../runs/uav_message_content/b05_retained_control/process-exit.json)
have equal local/canonical-node SHA256s, respectively
`9cd7ea9b5eb1e7fd7fdc9aaea10679ba84ea437b62182a0e2b475d8450fd3ef8`,
`3ceaa83a48591f9d8d7c4b64fe582436380d5a0eef8ac73f84f93ce879d6165c` and
`a8575e4c44391b62f1aaa8272fc7e484ad1f8a308c3e412391cf22059e954de4`.
Manifest/preflight hashes also agree across those locations. One durable raw copy
remains at `wsl_4070:/home/wu/projects/HMASD/runs/uav_message_content/b05_retained_control/`,
82194432 allocated bytes at collection. Its224 compressed traces total66776282
file bytes, including2867200 uncompressed evaluator-only user connection bits;
individual raw/checkpoint hashes and locators are bound by the summary, and stream
hashes are independently verified by the reader. All positive/adverse endpoints,
initial checkpoints and episode/update streams remain required evidence. The
canonical B19451 and prior B01-B04 raw evidence remain untouched.

#### Native outcomes and the two uncertainty scopes

All J values below are full-H256 per-step means, service is connected users per
tick, and the fee is.001 in every arm. Physical J is net J plus.001, so no fee
saving explains any contrast. All cells share the same32 evaluation worlds and
motion/channel streams. B40 is evaluated once and is not three independent fits.

| Continuation | Arm | Net J | Service | Q |
|---|---|---:|---:|---:|
|19601|M_G|.236846589|14.223511|.129058130|
|19601|M_O|.236715308|14.208984|.129298421|
|19602|M_G|.236266174|14.229248|.126855673|
|19602|M_O|.236979328|14.279419|.126891541|
|19603|M_G|.231268165|13.835083|.128590011|
|19603|M_O|.231754831|13.866821|.128731110|
|19451 frozen|B40|.228795101|13.636963|.129592068|

M_G-B40 per-block J differences are[.008051489,.007471074,.002473065],
service[.586548,.592285,.198120]. Means are **+.005998542 J / +.458984 service**.
The conditional continuation-level t95 intervals, df2, are
[-.001620096,+.013617180] J and[-.102265,+1.020234] service. These intervals
condition on this selected parent and common panel, not independent parent
training. Separately, the df31 deployment-panel intervals for the mean of these
three fixed endpoints are[+.001022296,+.010974788] J and[+.101488,+.816481]
service. Their positivity does not replace the df2 uncertainty or turn96 rows
into independent learning replications.

M_O-B40 per-block J differences are[.007920207,.008184227,.002959730],
service[.572021,.642456,.229858]. Means are+.006354721 J / +.481445 service;
df2 intervals[-.000956371,+.013665813] / [-.066825,+1.029716]. The separate
deployment intervals for the average over three fixed endpoints are
[+.001193612,+.011515831] /
[+.110879,+.852012]. Both learning arms therefore have positive observed
panel-mean gains in all three blocks, with unresolved training-level magnitude.
These positive averaged-endpoint intervals do not apply to each individual
endpoint. Only19601 has individual J/service deployment intervals strictly above
zero for both arms. Both19602 J intervals cross zero; its M_G service interval
crosses zero, while M_O service is[+.009731,+1.275181]. Both19603 endpoints cross
zero for J and service.

The prospective future-content increment M_O-M_G is much smaller:
per-block J[-.000131282,+.000713153,+.000486666],
service[-.014526,+.050171,+.031738]; mean **+.000356179 J / +.022461 service**.
Df2 intervals are[-.000729584,+.001441942] / [-.060339,+.105261]; the separate
deployment intervals also cross zero,[-.000251412,+.000963770] /
[-.022982,+.067904]. This is unresolved, not equivalence, an established content
gain or permission to add seeds after reading it.
The fixed19602 O-G contrast is a retained positive case: its separate32-world
deployment intervals are[+.000193645,+.001232661] J and[+.011120,+.089222]
service. That one endpoint-pair result is not the unresolved training-level
recipe comparison and does not select a winner after evaluation.

J decomposition preserves the tradeoff: M_G-B40 has+.006425781 from service but
-.000427239 from Q; M_O-B40 has+.006740234 from service and-.000385513 from Q.
The M_O-M_G mean divides into+.000314453 service contribution and+.000041726 Q.
The new capability signal is chiefly restricted continuation, not demonstrated
benefit of dated future content. There is no claim that this mechanism caused B04's
degradation or that these policies beat all competent ordinary planners.

#### Every adverse world and service tails

The full reading retains every raw-derived world level and paired difference,
with endpoint/world extrema and adverse-world lists for each metric. I read all
224 rows, not only the averages. J-negative worlds versus B40 are:

| Block | M_G adverse J worlds | M_O adverse J worlds |
|---|---|---|
|19601|0,4,11,12,18,19,20,26|4,11,12,18,19,22,26|
|19602|0,1,2,5,7,11,12,15,19,20,22,24,26,27|0,1,2,5,7,11,12,15,19,20,22,24,26,27|
|19603|1,2,4,6,7,10,14,19,21,23,24,26,27,31|0,2,4,6,7,10,12,14,19,21,24,26,27,31|

Service-negative lists differ and remain explicit in the reading:8/13/14 worlds
for M_G and8/13/16 for M_O. Mean gain is not worldwise dominance. The largest
M_G/M_O J losses versus B40 are-.042322806/-.043249160, both19602/world11;
the largest gains+.051784096/+.051972889 are both19602/world30. Worlds19 and26
lose J and service for every continuation, while29 and30 improve both in all six.
For M_O-M_G, J loses in19/9/15 worlds; the largest loss is-.007664551 at19603/26
and largest gain+.008296640 at19603/17. Thus the tiny mean increment is mixed
even within this one shared deployment panel.

Across32 worlds, B40 has13 zero-service ticks:2 inworld21 (longest1),11 inworld28
(longest7). M_G total zero ticks by block are7/1/10; M_O totals9/2/11. The block3
corrections introduce zero service inworld10, where B40 has none: M_G3 ticks
(longest1), M_O4 (longest2). M_O block2 retains one zero tick inworld21, where
M_G has none. World28 improves relative to B40 in every endpoint, with M_G7/1/7
and M_O9/1/7 zero ticks. This is useful aggregate tail improvement versus B40
alongside new adverse worlds, and four more pooled zero ticks for M_O than M_G.

Mean per-world minimum service is5.34375 for B40,5.25/4.96875/5.28125 for M_G
and5.21875/4.90625/5.15625 for M_O: every continuation is worse on this distinct
tail statistic. Boundary fractions are B40 .157910, M_G .152222/.138062/.156177,
M_O .152246/.137915/.153833. Floor fractions remain large: B40 .737329, M_G
.753418/.777002/.736743, M_O .752759/.777271/.747412. Mean altitude is55.3107m
for B40,54.9063/54.3664/55.3370m for M_G and54.9244/54.3587/55.0529m for M_O;
ceiling fractions remain.001245-.001465. These descriptive boundary/altitude
changes are not physical-safety evidence.

#### Exposure, useful assets and limits

All6144 PPO records contain finite actual losses and actor/critic gradients;
all6144 separate actor Adam and6144 critic Adam calls occurred. Base displacement
is exactly zero in all endpoints. Residual hidden displacement is2.968-3.200,
output displacement.283-.404, old critic displacement2.717-3.599. M_G's zero-only
forecast critic projection remains zero, while M_O's projection moves1.453-1.599.
Last16-rollout value MSEs are45.669-55.584 versus70.127-82.519 in the first16;
actor surrogate means are small, with maximum pre-clip actor gradient.074-.110
and critic maxima396.5-465.1. Separate clipping prevents the critic norm from
scaling the actor step. These facts establish learning exposure, not correctness
of a preferred causal explanation.

The first two episodes of every fit have exactly zero residual. Final correction
RMS in pre-tanh units is .034838/.081728/.032973 for M_G and
.032501/.080975/.043254 for M_O. Every final correction coordinate is nonzero;
the fraction at or above.095 is zero in training and evaluation. The mean of
worldwise maximum corrections lies.062906-.088324; no fit is diagnosed as hard
bound saturation. Same-noise normalized-action RMS changes are
.022107/.049990/.020854 for M_G and.020532/.049462/.026155 for M_O. Combined
with unchanged inherited sigmas, this is a genuinely active but restricted
fixed-noise mean-correction family, not a test of all useful control corrections.

Every M_O endpoint has160768 qualified future-cache uses on the common panel.
Valid-field removal at the same history gives central-command RMS sensitivity
.002213/.001801/.003953 (max.010521/.007087/.014515). Ordinary forecast cache-use
horizontal RMS error is81.996/82.367/81.669m, with height MAE3.750/3.211/3.908m;
dates, expiry, terminal-short targets and clipped first-sampled/central persistence
all check. Future information is delivered and the composed policy responds;
neither nonzero sensitivity nor forecast validity proves useful mediation. The
forecast increment remains unresolved despite this exposure.

The frozen B19451 and six new endpoints are retained as concrete capabilities and
evidence, not selected retrospectively as a new default winner. M_G's repeated
positive panel means strengthen the premise that bounded learning can develop a
useful inherited controller. They do not yet establish reliable improvement over
the distribution of continuations/parents, eliminate adverse worlds, or authorize
deployment replacement. Future-content usefulness remains open, with this fixed
extension offering no resolved increment. B04's measured predictor capability,
its mixed/adverse package result, and the earlier ordinary/learned positive cases
are all preserved rather than explained away.

#### Measured cost

B05 completed exactly6 policy fits,3072 training plus224 final evaluation
episodes,786432+57344=843776 native steps and4218880 motion samples. All1536
rollouts,6144 PPO records and their separate actor/critic calls occurred;
15728640 actor and3145728 critic replay rows are counted separately. There were
24576 evaluation-only shadow forward calls and no evaluation optimization.
Runner wall was1744.424536s (29.074min), worker self CPU1743.827520s (.484397h),
with one Torch/inter-op thread and lifetime peak RSS531300KiB. The CPU use is
about16% above the rough.418CPUh estimate, not a violated bound. Full reader wall
was46.66s, user47.43s plus system1.56s, peak RSS387716KiB; it added no scientific
exposure. Correctness tests and agent support remain separately scoped and not
claimed as exhaustively metered agent-hours.

Cumulative content investment is now27 policy fits plus3 predictors,
3907584 result steps,27648 PPO records plus3072 predictor updates, and
6683.891643s scientific runner wall. This carries all prior positive, adverse and
failed exposure. It does not reset cost because a new native DM owns B05.

#### Independent scientific reading and DM disposition

Registered ResearchCritic `/root/dm_retained_control/critic_b05` worked read-only
with `fork_turns=none`, without inherited DM/Root conversation. It reconstructed
the frozen protocol and evidence before reading the full Pro/selection assessment
and my interpretation. It independently read all224 raw native J/service/Q and
service tails, matched scenes/users/channel timing and realized Gaussian
innovations, checked3072 training-stream bindings, all12 checkpoints and6144
update records, and directly inspected complete action/density/forecast/cache
semantics on25 positive/adverse trajectories. Eleven relevant accepted snapshot
files matched69785db45a1240046f7d1a066dbe53a3b710e7c0 and the canonical parent
hash agreed. It found no consequential source/evidence contradiction. It did not
replay neural forwards or radio physics, nor re-audit old B03/B04 raw data.

Its substantive recommendation is to **retain the demonstrated restricted-
continuation capability and end B05 without another run**. Both extension arms
have positive observed mean J/service in all three blocks, useful evidence for
developing the retained controller but not reliable improvement across training
or parent populations. The positive df31 intervals belong to the average of three
fixed endpoints, not every endpoint: only19601 individually excludes zero in
J/service against B40 for both arms. I incorporated this factual clarification
above, while preserving the separately favorable fixed19602 M_O-M_G contrast.
The overall content comparison remains unresolved; neither its specific positive
case nor adverse19601 is erased by the pooled uncertainty.

The critic preserved native tradeoffs:19602/world11 loses.042323 J/2.660156
users for M_G and.043249/2.765625 for M_O versus B40; M_O19603/world19 loses
3.164063 users. All endpoints lower mean worst-tick service, and block3 creates
zero-service ticks inworld10. Conversely, aggregate zero counts improve and
M_G19602/world30 gains.051784 J/3.628906 users. No retrospective unanimity rule
is introduced.

Its explanation update has three parts. First, small correction-to-noise scale
does not prevent useful native changes: corrections execute and none reaches the
declared.095 saturation threshold. Nonactivation and observed hard-bound
saturation are not supported explanations. Second, **ordinary retuning is the
strongest simpler account of the shared gain**. Its post-hoc raw inspection found
19602 M_G corrections averaging approximately[-.0830,+.0826,-.0790], with each
coordinate SD about.0056. These nearly constant directional offsets are a credible
alternative to learned message coordination, not proof a constant controller would
reproduce the benefit. Third, forecast delivery and nonzero same-history sensitivity
are established, but useful mediation is not. B05 does not identify why B04 degraded:
panels, training instances and multiple learning properties differ. A persistent-
bias comparator would matter to a future state-dependent coordination claim, not
retroactively become a missing requirement for this completed package question.

The critic recommends **no additional native work in this fixed family now**.
There is no declared replacement decision that another ranking panel would settle,
and no saturation evidence specifically supporting a radius increase. It offered
one conditional future investment if concrete asset reuse becomes consequential:
prospectively select one M_G endpoint and compare it with B40 on32 fresh complete
worlds,0fits/64episodes/16384steps. Joint gains would support provisional reuse of
that one asset; losses/tradeoffs would favor B40; unresolved intervals would leave
replacement unresolved. This would be deployment testing, not training replication.
The observed12.19s B40 panel suggests tens of worker-seconds, with unpriced evaluator
preparation/readback. The critic explicitly does not recommend buying that panel
now merely to refine rankings. It reports **`MATERIAL_DISSENT: no`**, all its
read-only processes finished, and no remaining raw/source consumer.

I adopt that disposition and simpler-explanation limit. B05 strengthens the
constructive premise that bounded continuation can develop an already useful
controller, without establishing reproducible future-content advantage, a new
default endpoint, learned message coordination or freezing causality. The six
endpoints, B19451, earlier ordinary/learned capabilities and every adverse result
remain assets/evidence. No radius, noise, architecture, training length, seed,
predictor or ranking panel is selected. This fixed study is complete, and the
broader question returns to `reserve` with no active producer, unread result or
external blocker. Root owns the next investment choice under the continuing
complete-round/Pro-innovator/selection loop; the conditional reuse comparison and
simpler-bias issue are recommendations for that choice, not a waiting approval
gate or authorization for another study in this child.

At this complete boundary, retain the reusable bounded model, separate PPO
updater, dated channel/collector, their correctness tests and pure reader as
useful capability code. Retire only the ended fixed six-fit `run.py`/`study.py`
entrypoints and driver-specific test, plus the exact disposable launch snapshot,
temporary parent staging copy and consumed observer scratch. The import scan found
no external executable consumer of those driver paths. Historical implementation
and its original32-test contract remain recoverable at69785db45a1240046f7d1a066dbe53a3b710e7c0.
Canonical raw/weights/streams and the parent are excluded from deletion. The
observer's terminal event was consumed through generation3, then stopped/drained
with no pending events. Actual absence and allocated-byte change will be recorded
after the supported exact-target collector, without a backup or retention chain.

#### B05 retirement completed

The complete result was published at683f94830 and this direction's standing and
directly affected shared understanding at93956bb96. All scientific, reader and
critic processes had finished, and the observer was stopped with no pending
events before cleanup. The exact-target snapshot collector, using its supported
read-only sudo process scan, first refused because the pure reader had generated
one ignored `read_b04.cpython-310.pyc` inside the snapshot. Inspection found no
other changed/untracked/ignored file. I removed only that rebuildable bytecode and
empty cache directory; the next preview established eligibility. No experiment
source or result was changed to make this check pass.

The apply waited behind another session's canonical-node writer lock. I kept that
same cleanup handle and reported the concrete holder to Root; Root relayed that
its owner stopped only its own stalled network fetch and released the lock before
any launch. I did not interrupt or migrate that work. The original waiting
collector then removed snapshot `e6bc0c8404bc42218708e367eb8a1c37` under the
writer/admission locks. The source remains reachable in published Git, and the
claim/manifest/exit witness remain. A fresh post-cleanup status still reports
consistent exit0, valid witness and absent runner/supervisor.

The following measured cleanup scopes show **803946496 net allocated bytes
reclaimed**. Deleted targets are absent; the two partially retained directories
contain the useful components/tests, not a failed deletion.

| Scope | Allocated before | After |
|---|---:|---:|
|wsl_4070 `.git/hmasd-launch-sources/e6bc0c8404bc42218708e367eb8a1c37`, including reader bytecode|803250176|0|
|wsl_4070 `/home/wu/hmasd-inputs/uav_message_content-b05-B-34871c49.pt` duplicate|466944|0|
|local B05 implementation/test directories: delete `run.py`, `study.py`, driver-only test and bytecode; retain useful components/tests|188416|61440|
|local `experiments/candidates/uav_message_content/__pycache__`|57344|0|
|local `tests/experiments/candidates/uav_message_content/__pycache__`|24576|0|
|local consumed `temp/directions/uav_message_content/` observer/request scratch|20480|0|

The staging input had no `fuser` consumer and its SHA matched the unchanged
canonical parent before deletion. The two one-shot tracked source files were
removed with explicit-path `git rm`; the driver-specific synthetic test was
removed, and retained collector tests now use their own zero-default counters.
No core policy, likelihood, channel or collector behavior changed. The retained
component and B04/B05 reader suite passes **31 tests in7.74s**, with pytest scratch
removed. Its original32-test implementation remains at the fixed execution SHA.

The canonical B05 evidence directory remains82194432 allocated bytes, unchanged.
After all deletions, SHA256 checks passed again for all249 bound evidence files:
224 trajectories,12 initial/final checkpoints,7 episode streams and6 update streams.
The compact summary/reading and original B19451 hashes also remain unchanged.
No raw trajectory, unique endpoint, initial state, update stream or evaluator-only
user telemetry was deleted. No backup, tarball, relocated bulk or extra retention
copy was created. Git object storage and whole-host free space are outside the
reported allocated-byte scope. No selected deletion target or tool blocker remains.

The preparation-to-cleanup calendar span was approximately13:05-14:34UTC, including
the29-minute scientific worker interval and deterministic waiting. This is not a
measurement of summed agent labor; the original4-8 agent-hour suggestion remains
an unverified estimate rather than a claimed actual. There is no remaining accepted
operation, observation, pending advice, unread result or selected follow-up in this
child. Root receives the complete scientific boundary and owns the next selection.

<a id="b06-calibration-prospective"></a>
## 2026-09-29 - B06 prospective: trained constant calibration versus state-dependent correction

Root selects the corrected option B from the complete Joint Control Next Investment
advice preserved at `d7c74268f`, with the separate-context selection critic's
one prospective conditioning correction adopted: K actor Adam lr3e-3, D actor
and both critics lr3e-4. The original literal unscaled K drew material scientific
dissent; adoption resolves that objection without claiming equal optimization.
The full Pro answer and forthcoming dated selection archive are reused. No new
selection consultation or learning pilot is needed. Native lead/writer is
`/root/dm_calibration_learning`, a new DM under the same Root; the completed B05
DM and every old operation remain complete. This is exploration, not confirmation.

The question is whether developing competent retained B19451 under the same legal
delayed message contract benefits from a learned state-dependent bounded correction
beyond a seriously trained shared three-parameter calibration. A useful constant
calibration is a substantive capability too. The intended contribution is conditional
learning-package usefulness and empirical understanding, not a new architecture,
causal state-information test, forecast module or radio repair.

Current published communication background at `d7c74268f` and the complete
[B05 reading](#b05-complete-reading) change the design directly: retain B19451 and
the full geometric messages, train an ordinary constant comparator rather than
substitute a post-hoc B05 mean, and report full service tails alongside average
J/service. B01's content replacement losses, B02's favorable learned-content means
and reversals, B03's useful B/O/L assets with provisional B19451 use, and B04's
forecast capability with mixed/adverse package effects all remain inherited.
B05 M_G-B40 mean J/service +.005999/+.458984 and M_O-B40 +.006355/+.481445
support a constructive restricted-continuation conjecture; df2 intervals cross
zero and M_O-M_G is unresolved. Near-constant correction was inspected in ONE
19602 M_G endpoint, not all six. Every B05 endpoint lowered mean worldwise minimum
service; fewer aggregate zero ticks coexisted with new adverse worlds.

The competing predictions are that D learns consequential state variation and
earns complete J/service beyond K and B40, or that ordinary fixed calibration
provides most useful incremental control under this finite training recipe.
D's ability to represent constants is no finite optimization dominance guarantee.
Nonconstant output alone is not useful state dependence. Both complete policies
remain state/history dependent through the same frozen recurrent parent.

### Fixed decision contract, pairing and interpretation

Keep native N5/50 static users/H256, sampled primitive motion, frozen B19451
encoder/GRU/mean/log-variance and fixed scaling, fixed RR sender t%5, unchanged
GOOD/BAD persistence .95, delay1/5, no loss and fee.001. All arms use the same
40-byte message with the seven retained geometry values and three zero tails;
the widened abstract bandwidth retains its physical-network limitation. No new
map, telemetry, control right, predictor, reward or clock enters this comparison.
Canonical parent remains the B19451 checkpoint and digest bound in B05 above.

K has only one shared learned vector b of length3, b0=0, with d=.10*tanh(b).
D uses the retained 250->64->3 tanh MLP with zero last layer and
d=.10*tanh(g(x,h_B)). Both use u~N(mu_B+d,sigma_B^2), a=tanh(u).
The frozen base GRU consumes each arm's actual observations and previous executed
COMPOSED actions; its state is never replayed from a B40 trajectory. PPO likelihood
is the composed tanh-Gaussian density. Fixed Gaussian entropy is a constant in
the actor objective, not active regularization of executed-action entropy.

Each arm starts with fresh copies of the same parent critic tensors plus the same
zero forecast projection, identical within each pair, and fresh separate Adam
states. Two full episodes/rollout, four full-rollout PPO epochs, chunk32 replay,
undiscounted terminal returns, standardized team advantages, agent-summed PPO
clipping[.8,1.2], separate actor/critic norm clips .5 and critic loss .5*MSE are
unchanged. Only K actor lr is3e-3, from the selected one-time parameter-unit
adjustment; D actor and both critics retain3e-4. Adam(.9,.999),eps1e-8, no decay.
The illustrative unscaled constant-direction calculation d~.02979 after1024
calls is not a reachability theorem or a forecast of K failure. This correction
removes an avoidable rival explanation, not all optimization differences.

Masters19701/19702/19703 each train K then D for512 H256 episodes. Construction
seed100000*m+11, scene100000*m+1000+e, channel100000*m+6000+e, and one dedicated
continuous training motion generator100000*m+21 per fit. Different constructors
must not advance this generator. Actual innovations and scene/channel hashes
are checked, not just seed labels. Later on-policy trajectories and critics may
legitimately diverge. Final six endpoints and B40 once use32 COMMON fresh tuples
scene1970002000+e/channel1970007000+e/motion1970003000+e, e0..31. Deployment
remains sampled with common innovations. One innovation per tuple does not estimate
within-scene stochastic risk. No initial score panel, best-checkpoint selection,
extra seed, radius/variance extension or duplicate retry is included.

Read D-K, K-B40 and D-B40 full J/service per training pair, Q/fee, every endpoint's
adverse worlds, mean worldwise minimum service, zero counts and longest gaps,
correction mean/variation and executed motion, actual parameters/updates and cost.
Three continuation pairs are the learning units, conditional on one selected
parent and common evaluation panel; report descriptive df2 t95 intervals. Separate
fixed-endpoint world intervals use df31 and never create96 learning replicas.
These are exploratory and not selection-adjusted. No equivalence margin or
retrospective all-worlds-positive adoption gate is introduced.

D earning full J/service use over both K/B40 supports this finite extension package,
not causal message coordination. K benefit without a resolved D increment retains
calibration, not equivalence. D>K with both below B40 does not establish useful
development. Positive means with adverse tails remain a conditional tradeoff.
Technical missingness is not negative science. The fixed batch ends after complete
reading, followed by independent result diagnosis and a comparison of further
investment with independent questions and stopping; no rescue run is presumed.

### Prospective cost and L0

Six fits mean3072 training+224 final evaluation episodes,786432+57344=843776
native steps and4218880 motion samples. There are1536 rollouts,6144 actor and6144
critic Adam calls,15728640 actor and3145728 critic replay rows; no predictor/search.
Inherited cost is27 policy fits+3 predictors/3907584 result steps. Complete B06
would make33 policy fits+3 predictors/4751360 steps. B05's.484397 worker CPUh,
29.074min wall and about49 reader CPU-s are anchors, not this host's estimate.
Support4-8h remains conjectural. Use configured `local_linux`, one CPU/Torch/BLAS
thread with actual admission accounting for concurrent G0/radio/Claude activity.
Prospectively impose a3 CPU-hour scientific-worker resource ceiling covering
initialization, six fits, final evaluation and output. A hit preserves the prefix
as resource-incomplete and does not authorize extension or restart. Pure readback
and engineering are separately metered. No wall-based scientific stopping rule.

L0: deliver the exact K/D model and optimizers, six-fit driver, lawful zero-tail
collector and complete compact/raw reader at `experiments/candidates/uav_message_content/b06/`
and direction `read_b06.py`, mirrored tests, `runs/uav_message_content/b06_calibration/`
and owned scratch. Reuse the retained B05 model/collector/update/channel, shared
native host and existing numerical readers where semantics match. Do not modify
shared core or revive an old result driver. The bounded Implementer owns only
`b06/{__init__,model,update}.py` and mirrored `b06/test_model.py`; the DM owns driver,
collection/reader, remaining tests, NOTES and acceptance. No helper index/commit,
launch, notebook or child authority. Other sessions' writes must be preserved.

Checks cover exact zero-correction identity at common history/noise, genuinely
three-parameter shared K, bound and composed density, frozen parent despite actor
updates, identical fresh initial critics, exact optimizer learning rates/states,
actual-action recurrent history, constructor-independent continuous innovations,
lawful geometry/zero tails, output counts, synthetic writer-reader integration and
all final raw evidence. These are correctness exposure, not additional native
learning. Independent focused engineering review must resolve reachable numerical,
RNG, likelihood and output defects before exact-source publication and admission.

Root's completed selection and this DM's `exploring` route are published at
`b6d9e3b97`; I read the full focused critique and adopted disposition in
[the dated archive](../../archive/2026-09-29/RESEARCH-joint-control-next-investment.md#focused-independent-calibration-review).
Its specific objection and resolution above remain intact. I rehashed the canonical
remote parent as34871c49...59da2. The retained collector receives one optional
sampler callback, defaulting to its unchanged primitive sampler; B06 uses it to
compare every actual sampled u with an independent clone of the dedicated RNG.
This records hashes of actual-verified innovations, including continuous training
stream boundaries, without another policy/environment call or scientific sample.

### B06 implementation accepted before result exposure

The bounded registered Implementer `/root/dm_calibration_learning/implement_calibration_model`
returned only the assigned model/optimizer files and focused checks. I read and
accepted them, adapted the driver to its existing two-argument optimizer API and
corrected the synthetic previous-action fixture to indices104:107. K has exactly3
trainable actor parameters and D16259; both critics have identical parent tensors
and zero forecast projections before learning. D reuses the exact retained B05
actor and both arms reuse the inherited composed-density/recurrent PPO update.
The dedicated motion generator is unaffected by model construction.

The integrated B06/B05/retained-reader suite passed40 tests in12.34s with
`--import-mode=importlib`; test scratch was removed. It covers zero identity,
active updates/frozen bases, matched initial critics, full-H256 synthetic traces
for K/D/B40, lawful actual-action history, zero tails, composed likelihood,
actual-verified innovations, and a miniature six-fit/B40 driver with checkpoints,
update streams and complete counts. Both native CLI help entrypoints exit0.
The local staging copy `/home/fires/hmasd-inputs/uav-message-b06-B-34871c49.pt`
matches the canonical463357-byte parent digest/metadata and inherited sigmas.
No correctness test ran a native scientific episode.

Registered independent engineering Reviewer `/root/dm_calibration_learning/review_b06`
found one P2 reader defect: inherited negative-difference adverse labels reverse
the meaning of fewer zero-service ticks/shorter gaps. I repaired B06 with explicit
metric directions and neutral signed descriptive height/boundary differences;
historical B05 evidence is unchanged. Eight focused study tests passed in5.27s,
and the reviewer independently confirmed the three new regressions in1.29s.
It reports no material finding remains after checking the collector, own-history
replay, composed density, optimizers, actual RNG pairing, checkpoint/B40 binding,
counts and admission. Full production-size read_run has not run; complete native
collection and reading remain the obligation, not a conclusion from green tests.

Result inputs will be published together before admission. Current local memory
and process observations include the accepted G0 and radio workers; this one-thread
study keeps its own resource guard and must still pass fresh actual-node admission.
No accepted producer, observer or source snapshot is changed to make room.

### B06 accepted operation and observation

Exact inputs were committed and published at
`f288de6416dff6f8b73ea634995bbe163ad9b5fd`. One `local_linux` admission was accepted
at2026-09-29T20:47:04.832934Z. The
[native manifest](../../../../runs/uav_message_content/b06_calibration/launch-manifest.json)
binds claim58e472fad05fbbb67b1bd3877064f649766cf32d61c77cb8a72b622bf22e376e
and immutable snapshotad9d60efa12645809a86268a0aa464da. Fresh actual memory was
9054691328 available bytes against the4294967296-byte floor; published ownership
and source also passed. This is launch acceptance, not a completed result.

`tools/hmasd_wait.py` generation1/window1500 observes this same handle in owned
`temp/directions/uav_message_content/b06-wait`; its assigning native child UUID is
01a0eedb-12d3-7e01-ba73-98228dabc599. The initial drain confirms the recorded
supervisor/runner identities both running with consistent records and no exit
witness. I keep this child active through the full reading; a checkpoint only
rearms this observer and never restarts or replaces scientific work. Original
outputs are authored directly under `runs/uav_message_content/b06_calibration/`;
bulk raw/checkpoint/streams will remain the single durable local evidence copy.

At the generation1 checkpoint (about21:12UTC), three cells were complete and
19702/D had413/512 training episodes; no batch limit was recorded. I consumed
eventebe3f0c9d7397378618fb27c and rearmed the same claim asgeneration2/window1500.
Native queue delivery reported the known unloaded-child -32600 refusal; actual
process observation remained healthy and this child turn stayed active. No worker
restart, source change, duplicate launch or reading of partial scores occurred.

<a id="b06-owner-pause-handoff-20260929"></a>
### 2026-09-29 B06 owner pause and handoff

The owner explicitly paused this Root workflow at21:25UTC and requested a handoff.
Root published the direction pause at `c4cf7dbd2`, preserving the launch-bound Lead.
This section records interruption/reconciliation only, not a scientific reading or
a technical/scientific failure. No new experiment, evaluation, review, interpretation,
successor or cleanup is authorized. Only an explicit owner resume changes this state.

The accepted source remains `f288de6416dff6f8b73ea634995bbe163ad9b5fd`; the original
admission/observer note was published at `bda368ef2ea8109218dd96f1b8fd85015bcb1db7`.
The sole run is `/home/fires/hmasd-wsl/runs/uav_message_content/b06_calibration` on
`local_linux`/Jacob. Its original claim/operation is
`.git/hmasd-admission/58e472fad05fbbb67b1bd3877064f649766cf32d61c77cb8a72b622bf22e376e.json`,
and its immutable source is
`.git/hmasd-launch-sources/ad9d60efa12645809a86268a0aa464da`.
The managed launcher has `launch` and `status`, but no stop subcommand. After
reconciling this exact claim and the matching observed/recorded native identities,
I opened a pidfd for runner3936313, rechecked start_ticks15336778 and boot_id
16933456-3d53-469c-99a9-e7599f804ba7, and sent SIGTERM only to that runner. I did not
kill its supervisor or process group. The original supervisor3936305 (same session/
PGID3936305, start_ticks15336756) wrote the valid [native exit witness](../../../../runs/uav_message_content/b06_calibration/process-exit.json)
at2026-09-29T21:29:10.581501Z: exit_code-15, termination=signal. Subsequent same-handle
status reports `exited`, consistent records and absent runner/supervisor. This
signal was the requested owner stop, not a discovered implementation failure.

The deterministic observer in `temp/directions/uav_message_content/b06-wait` was
stopped using `tools/hmasd_wait.py stop` and drained without rearm. Generation2 is
`stopped=true`, wake_id=null and has no unconsumed event; its cached job still says
running from its last21:28:52 probe, which is stale and does not override the native
exit witness. Original observer3936495, rearm observer3988028 and local wait process
3988418 are absent. Exec waiter49862 exited0 after observing stopped=true. A fresh
process scan found no B06 producer, reader or observer. The implementation and
engineering-review helpers were already completed; both were explicitly interrupted
without new turns. No result critic was started. Nothing will wake/rearm itself.

Count-only reconciliation of persisted summaries, episode/update row identities and
file presence gives the following state. No reward/service/correction values were
read and `read_b06.py` has not run.

| Cells | Training episodes | Saved final-evaluation episodes | State |
| --- | ---: | ---: | --- |
| 19701/K,19701/D,19702/K,19702/D,19703/K | 5 x512 | 5 x32 | Cell outputs COMPLETE, unread |
| 19703/D | 512 | 9 (worlds0..8) | Training endpoint saved; evaluation interrupted |
| B40 | 0 | 0 | Not started; no directory |

All six `initial.pt` and `final.pt` files exist; all six streams contain1024 update
records. Persisted totals are3072 training episodes/786432 training native steps,
169 evaluation episodes/43264 evaluation steps,829696 native steps,1536 rollouts,
6144 actor plus6144 critic Adam calls,15728640 actor replay rows and no predictor.
The last episode boundary cannot account for in-flight evaluation world9; at most
another256 native steps may have executed without a saved trace/row. Report native
exposure as829696 persisted plus0..256 unpersisted, never as the planned843776.
Cumulative exposure is therefore33 policy fits+3 predictors and4737280 persisted
native steps plus0..256 unpersisted. The top-level batch summary is deliberately
unchanged: `INCOMPLETE`, active_cell19703/D, five returned cells, b40=null. Its
`actual` field counts only returned cells, so the separate19703/D summary is required
for this reconciliation. Empty `limits` is not proof of completion: SIGTERM bypassed
the Python finalizer. Five completed-cell resource records sum to2008.655337 CPU-s;
sixth-cell/batch final CPU accounting is absent, not zero. Acceptance to native exit
was2525.748568s wall. No reader cost exists.

Preserve the sole local evidence tree in place:207 files,60391081 logical bytes and
60796928 allocated bytes at handoff. It includes169 compressed trajectories
(46435061 bytes), twelve checkpoints (6427860 bytes), twelve streams (6717962 bytes),
and compact original summaries/config/admission/exit records. The SHA256 inventory
digest is `74d949fefdb07bed87a8eec0479002c326aaf01adb4874e6e1313a7dbe9fe15b`, computed
over all files sorted by relative path, appending UTF-8
`relative_path + NUL + decimal_size + NUL + file_sha256 + LF` to one SHA256 stream.
The original batch summary digest is
`2cf1c6884a9584e0005e62f8284582dadc43d82cf6ebb24ea70e7ed32bd88b7f`; the unfinished
19703/D summary digest is `327cde4412772d01f5bbb9ca3bff5d96d901b0f44c55c7634b33283735674458`.
Its saved final checkpoint is568164 bytes/SHA256
`140aee1b9fdbd2708fc787d788d25466bec8f46d9cbbdaaf8f099d0c1d415e13`; its episode and
update streams have hashes `1175cd06203221d98aa19a427b1f66c013b29d9aad8bf021563f204725bf79e8`
and `b440d6f54e2b668c07de44e7255cf834d13ca7e7898365cdc87d9e7565d2f10f` respectively.
All other checkpoint/stream identities remain in their original completed-cell
summaries. The staging parent `/home/fires/hmasd-inputs/uav-message-b06-B-34871c49.pt`
is463357 bytes/SHA25634871c49874ec716c21438581facfaeca8a25930304a39eb26e001fb2b259da2;
its canonical B19451 remote location above, the launch snapshot, claim, observer
request/state and all raw outputs are retained. No deletion or disk reclamation was
attempted during this pause.

Publication scope is this existing NOTES append and the unmodified compact B06
config, native launch-status/exit, batch summary and six cell summaries. New bulk
checkpoints/streams/trajectories stay local at the stated durable run path, not in
Git. Prior generation1 checkpoint narration is included. No helper has an unresolved
write; foreign dirty files belong to their owners and are untouched. Root owns the
global pause/index handoff; this DM makes no scientific standing/background change.

Resume procedure: first obtain explicit owner authorization and check the current
pause/ownership control. Reconcile the same stopped claim, exit witness and saved
evidence before choosing any further work; do not rearm the stopped observer or
restart this worker. The fixed driver rejects an existing output tree and has no
resume mode. Its remaining planned evaluation is23 worlds for19703/D and32 forB40;
all training is already spent and all trained endpoints are saved. No missing world
is authorized by this handoff. Any later evaluation-only recovery or partial-result
reading needs a prospectively stated disposition under the resumed authority, with
the interruption and extra/unpersisted exposure preserved. Do not silently splice
outputs, rerun six fits, replace the source or relax the reader's complete-batch
checks. Until then all saved scientific outputs are unread, no complete comparison
exists, and result diagnosis, publication of a scientific conclusion and cleanup
remain undone because the owner paused them.

<a id="b06-evaluation-recovery-prospective"></a>
## 2026-09-29 - B06 resumed evaluation-only recovery disposition (before scores)

The owner explicitly resumed Root with "阅读handoff 我们继续工作". Root published
the scoped pause lift and responsibility transfer at `ecd5b2583`: current parent
`01a0ef2b-a391-7693-a748-60e24be246ae`, native DM
`/root/dm_calibration_recovery`. The old child is unavailable; this transfers the
unfinished question, not an old process or a new study. The launch-bound Lead stays
`Codex DM (native child)`. At22:00UTC the original claim again reports consistent
exit-15 and absent runner/supervisor. The original207-file inventory still hashes
to74d949fe...15b, exactly the handoff inventory. No original output, observer or
accepted operation has been restarted or modified, and scientific scores remain
unread while this disposition is formed.

The proposed recovery completes only the missing original endpoint coverage:
19703/D worlds9..31 from final checkpoint140aee1b...e13, then B40 worlds0..31
from parent34871c49...9da2. This is55H256 episodes/14080native steps,0fits,0updates,
70400motion samples and two fresh environment constructors. No completed episode
is rerun. The interrupted world9 may already have executed0..256 unpersisted steps;
that possible duplicate prefix stays in total exposure. Complete saved coverage
would therefore be843776steps plus0..256unpersisted,33 cumulative policy fits plus
3predictors and4751360saved cumulative steps plus that prefix. The original
829696saved-step attempt remains interrupted rather than relabeled complete.

The current published communication background (RESEARCH section5 at ecd5b2583)
and the original B06 comparison remain applicable: state-dependent correction must
be read against the seriously trained constant K and B40, with native service tails
and the single-selected-parent limitation. The pause introduces no scientific reason
to change any comparator, sample, decision rule, checkpoint or uncertainty unit.
Ending with169/224 episodes would leave B40 entirely absent and the third D panel
selectively truncated by time; buying only55missing episodes can recover the original
question at far less cost than the six paid fits. This is a prospective recovery
choice, not a score-informed repair or a new evaluation panel.

Source tracing supports separable episodes. `b06/study.py` gives every evaluation
world its own motion generator1970003000+e, scene1970002000+e and channel1970007000+e.
The retained collector resets the native environment, constructs a fresh channel,
zeros the GRU state and previous actual action, and never calls the critic during
evaluation. `MultiUAVEnv.reset` reseeds its RandomState, resets time/agents/positions/
users/connections/SINR/transmitter mask and invalidates the physical-state caches;
the adapter forwards the reset seed. The free-space, no-shadowing host introduces
no evaluation-history RNG dependence. The same local_linux interpreter, CPU float32,
one Torch/BLAS thread and sampled policy will be retained. Construction/loading is
not training and must not consume the dedicated episode generator. The frozen
collector/model/source closure is checked against f288de641, with a synthetic
split/load/reconstruct identity test instead of buying another native episode.

An independent, outcome-blind ResearchCritic has the original prospective contract,
interruption and source to challenge this recovery choice. Its disposition will be
recorded before substantial implementation. Engineering review separately covers
checkpoint/RNG/reset/output identity. If these checks contradict separability, stop
the dependent recovery and return a bounded partial-reading choice; no native
duplicate panel or training retry is presumed.

L0 for the selected bounded implementation: add an admitted evaluation-only entry
and recovery module under `experiments/candidates/uav_message_content/b06/`, with
mirrored focused tests; preserve the original driver, collector, models and all
original run bytes. Verify the original inventory/exit/source and exact D/parent
checkpoint digests before scientific effects. Reject an existing recovery result,
changed or overlapping episode sets, changed input bindings and altered fixed
semantics. Write only `runs/uav_message_content/b06_eval_recovery/`:55 raw traces,
episode rows, fixed config, compact summary, exact input/provenance hashes and
parameter-before/after witnesses. No optimizer is constructed. Record actual counts,
wall/CPU/RSS; enforce a600CPU-second recovery-worker ceiling, with no automatic
extension/retry, separately from the original missing batch CPU accounting.

The Implementer may own this one evaluation-only behavior and its tests; the DM owns
NOTES, a separate two-source reader, acceptance, index and Git mutations. The reader
must independently validate every original and recovered trace/checkpoint/update,
explicitly identify169original+55recovery episodes and both source/exit identities,
retain original missing telemetry and extra exposure, and apply the unchanged full
panel contrasts/tail readings. It must not overwrite original summaries, fabricate
exit0 or weaken the original complete-run reader. Tests use synthetic fixtures under
pytest-managed scratch; no new native result appears before source publication and
fresh actual-node admission. Shared main contains other writers' edits; these are
preserved and commits use explicit owned paths under the shared index lock.

The outcome-blind Scientific Reviewer independently reconstructed the original
inventory, all six training/update counts, checkpoint/raw hashes and matched
exogenous witnesses. Its initial disposition is that the55-episode recovery is
scientifically defensible conditional on fresh-process episode equivalence, with
no scientific need for a duplicate native panel or new fit. The independent
Engineering Reviewer then traced the native reset/cache and actor state and found
no material semantics defect: the changing cache generation is only an identity,
and the Linear/Tanh/single-layer GRU actor has no dropout or persistent evaluation
buffer outside saved tensors and the collector-reset hidden state. Twelve frozen
source paths match f288de641. I select the bounded recovery on those findings;
the focused critic's final wording and implementation review remain to be read.
This is permission for the scoped implementation under resumed authority, not
evidence that the missing episodes have run or that the result is favorable.

The critic's complete focused disposition is now read and adopted: **retain the
exact55-episode recovery; MATERIAL_DISSENT:no**. It received no inherited DM/Root
conversation (the assignment did disclose the proposed route), reconstructed the
filtered original evidence before reading the recovery rationale, and viewed no
B06 scientific metric values. Its independent checks cover all207files, all six
final endpoints, parent/manifest/exit identities,512training and1024update rows per
fit,169contiguous saved evaluation rows/raw hashes, within-pair training witnesses,
matched evaluation RNG/scene/channel witnesses, and twelve unchanged source paths.
Its strongest remaining hazard is an unnoticed process-dependent change confounded
with missing D worlds and all B40 worlds, addressed by strict loading, frozen
dependencies, synthetic split/load identity and recovered exogenous-witness checks.
It requires a distinction between complete endpoint coverage and a completed
original operation; the separate two-source reader implements that distinction.
The600CPU-second recovery ceiling adds no replication and does not fill missing
original CPU telemetry. Original interpretation and uncertainty units remain
unchanged. No distinct Pro expertise is needed for this recovery choice. A
contradictory implementation check would stop the dependent recovery and trigger
bounded partial reading rather than an improvised replacement.

### Recovery engineering accepted before native evaluation

The registered bounded Implementer `/root/dm_calibration_recovery/implement_eval_recovery`
returned only the admitted entry, recovery module and focused tests. I read its
diff and checks and accept the implementation. It runs D9..31 from the exact saved
final tensors, then the unchanged baseline-only B40 branch; there is no optimizer
construction, learned-cell driver call or new checkpoint. Fifteen frozen dependency
files are byte-bound to f288de641. The original inventory, terminal exit, source,
checkpoint metadata/dtype/shape/finiteness and exact nonoverlapping coverage are
verified before effects, and the inventory is checked again afterward. The600CPU-s
guard checks collector boundaries and finalization; it is not OS preemption of an
individual native call.

The DM-owned separate reader retains both operation/source identities and original
interruption, validates169original+55recovery trajectories and the original six fits,
and applies the unchanged B06 contrasts. It records eight actual constructors
(six original, replacement D, B40) and the unknown0..256original prefix. It adds
only explicitly sourced in-memory interrupted-D checkpoint/stream witnesses; no
original summary, stream, checkpoint, status or exit is rewritten. The strict old
complete-run reader is unchanged.

Independent Reviewer `/root/dm_calibration_recovery/review_recovery` found a P2
reader omission of the recovered-D stream and recovery update/config artifacts.
I repaired it and added corruption regressions. Its integrated review found no
remaining material issue and independently passed34focused tests in3.64s. The
Implementer's complete B06 suite passed46tests in12.71s, including synthetic
nonzero-D uninterrupted versus reload/fresh-environment equality for every trace
array, B40 identity, no optimizer calls, input/source/coverage rejection, partial
stop preservation and admission-before-effects. Twenty reader tests separately
passed in.22s; these overlap the46, not additional scientific exposure. Scratch
was cleaned by pytest. Both CLI help paths pass. A final four-part defensive patch
(source/dtype checks, scoped output byte telemetry, final CPU check) was re-reviewed
against the prior exact digest; no new finding. Accepted recovery.py hash is
2e416fc2cf8a0ca6fc9de12f6341bee385b6eacc51ad1362922de73afddc3382.

No native episode or score reading occurred in preparation. Full native recovery
and all-evidence reading remain obligations, not implications of green tests.
Exact owned inputs are now ready for publication and fresh local_linux admission;
this preserves the original host/interpreter/device/RNG semantics rather than
moving the existing stopped operation to another node.

### Effect-free admitted input-binding failure and prospective correction

The inputs above were published at e52cda6c6ad3acc4ceabd892320691e24971857f.
The first recovery admission was accepted at22:14:09.170889UTC, claim
6652179ce25db278e9426be2bb55e906f1c6f4eb400c1b648ee0f72e1cf8e651,
snapshot1f322e8efef04d45860f130b11795047, output
`runs/uav_message_content/b06_eval_recovery/`. It exited1 at22:14:10.923894UTC
(1.753005s after acceptance). Native status has consistent records, valid exit and
absent runner/supervisor. No config, scientific summary, cell directory, checkpoint
load, policy construction, environment construction, fit, update or native step
occurred. Worker CPU was not finalized and is unknown, not zero.

The exact failure is `ValueError: original inventory mismatch` in
load_original_bindings before its checkpoint loader or evaluation. The accepted
manifest reveals why: the launcher's snapshot contract rebound the absolute
author-checkout `--original` argument into snapshot/runs, where only the tracked
compact records exist. The original207-file canonical tree still matches its
handoff digest. Source inspection of scripts/hmasd_launch.py:1507-1531 confirms
this intentional rebinding; it was our new external-evidence interface error,
not an environment/checkpoint failure or an adverse scientific observation.
No live work or uncertain scientific effect remains to reconcile.

I prospectively select one concrete interface correction at a new source and
`b06_eval_recovery_a02` output: pass fixed `--original-tag b06_calibration`, then
resolve that sibling under the already admitted canonical output's direction
directory. The launcher binds `--out` to author storage even under a snapshot;
the tag is an identity, not a source-file path. Original source/exit/inventory,
parent/D hashes and every scientific condition stay fixed. This avoids copying
bulk, alias tricks, changes to shared launcher code or an invented control-root
field in require_admission (it returns no such field). A synthetic admitted-output
binding regression and independent engineering re-review precede publication and
new admission. The first failure stays recorded; its claim is never reset/reused.
This is an explicit outcome-blind zero-effect repair, not an automatic retry or a
new seed/panel: all55original missing episodes are still missing and scores unread.
The600CPU-second ceiling and0fit/14080step bound remain unchanged.

The failed-operation observer's terminal event75d1eae8db2badf01a025f3d was read and
consumed, then observation stopped. Its known native-child queue refusal is recorded
separately from successful process observation. It will not be resumed; the old
training operation and its stopped observer also remain unchanged.

The defect was reproduced from the exact failed source snapshot: its bound original
directory contains12files, not207, and the same inventory refusal occurs with
zero checkpoint/model/environment calls. The narrow entry correction is accepted:
only recover_eval.py and its test changed; recovery.py remains2e416fc2...3382 and
all scientific collection/reader code is unchanged. Twenty-one focused tests pass
in2.64s. The added regression invokes the actual launcher's snapshot preparation
argument mapping, with only Git/publication/snapshot-creation infrastructure mocked;
it reproduces the old rebinding and proves the corrected bare tag and restored
canonical output yield the original evidence sibling after admission. Independent
Reviewer read the patch and ran that integration regression itself:1passed/.92s,
no material finding. I accept the repair and explicit new effect-free-attempt
disposition. No result values or native episodes were needed for this diagnosis.

### Corrected recovery admitted and observed

Corrected inputs and failed-attempt records were published at
77c1cd9f40bf40a2e36e4238ffd7fa5eb958b1e5. The separate
[recovery manifest](../../../../runs/uav_message_content/b06_eval_recovery_a02/launch-manifest.json)
was accepted22:19:19.331971UTC, claim1db566b592126ed7a0447f706314b303db436ef9f0ea88c584593a2cca972513,
snapshot e32e808e2d854c3886de414ba28874c7. Fresh local_linux memory was
10374225920available bytes against4294967296required. The accepted argv retains
the fixed original tag and canonical output, and the parent remains hash-bound
outside the source snapshot. This starts exactly the prospective missing55episodes,
not another fit or a restart of either stopped operation.

The new observer at owned temp/directions/uav_message_content/b06-recovery-a02-wait
is armed generation1/window1500 on this exact manifest. This native DM remains
active through terminal facts, complete reading and independent diagnosis. Both
older observers remain stopped; no old claim is rearmed or relabeled successful.

<a id="b06-complete-reading"></a>
### 2026-09-29 B06 complete endpoint reading across the interrupted and recovery operations

The corrected recovery exited0 at22:19:47.662533UTC after28.330562s from native
acceptance. Native status agrees with the exit witness and both runner4183204 and
supervisor4183203 are absent. It produced exactly the missing23 D19703 worlds9..31
and32 B40 worlds0..31:55 H256 evaluations,14080 native steps,70400 motion samples,
zero fits/optimizer calls and two replacement constructors. No earlier evaluation
was repeated. The original207 files still have inventory SHA256
74d949fefdb07bed87a8eec0479002c326aaf01adb4874e6e1313a7dbe9fe15b; its owner-stop
exit-15 and its source remain unchanged. **Endpoint coverage is complete; the
original operation remains interrupted.** The effect-free first recovery failure
above remains part of engineering cost and is not relabeled successful.

The same-handle observer delivered terminal eventcde72694a020b31b95db50eb. It was
read/consumed and stopped at generation2 with no queued event or wake. Its known
native-child queue error did not prevent deterministic observation or this active
DM's reading. The compact observer terminal is retained in the recovery output.

The pure reader ran from the exact accepted77c1cd9f4 snapshot and completed exit0:
[complete reading](../../../../runs/uav_message_content/b06_eval_recovery_a02/reading.json),
[recovery summary](../../../../runs/uav_message_content/b06_eval_recovery_a02/summary.json),
[original summary](../../../../runs/uav_message_content/b06_calibration/summary.json).
It verified all224 raw trajectories, all3072 training records and6144 update records,
all12 original initial/final checkpoints, both empty recovery update streams and
both recovery episode streams; every identity, coverage, seed/scene/channel/motion
pairing, composed-density check and count passed. There are no new reader policy,
model, optimizer or native calls. Reader source SHA256 is
32786487b0d94cb82e64aa9f1503614a14481748198826deaed2b9b49b33aee9;
its inherited full reader is0119711ea3f11074c75190f0a94d24d0306cd6ba1a38fb6b337589a4512e9174.
Original/recovery summary digests are respectively2cf1c6884a9584e0005e62f8284582dadc43d82cf6ebb24ea70e7ed32bd88b7f
and2c97ed4976ebcde2594d43f98438e81f921001943761994705ea025e5477250c.

**Full endpoint values and prospective contrasts.** All means below weight the32
worlds equally. Service is connected users per tick; J is complete native net J.
All arms have exactly.001 average fee, so physical-J contrasts equal net-J contrasts.

| Endpoint | J | Service | Q | Mean world minimum service | Zero ticks/world | Longest zero gap/world |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B40 | .214409451 | 12.696166992 | .125543711 | 4.31250 | 1.68750 | .59375 |
| K19701 | .220574991 | 13.163818359 | .124271781 | 4.43750 | 1.34375 | .81250 |
| D19701 | .222947240 | 13.390869141 | .121583573 | 4.31250 | .25000 | .15625 |
| K19702 | .217206889 | 12.914428711 | .124682956 | 4.25000 | 1.65625 | .75000 |
| D19702 | .223787295 | 13.398803711 | .124013477 | 4.53125 | .37500 | .12500 |
| K19703 | .217115603 | 12.919677734 | .124133716 | 4.46875 | 1.50000 | .50000 |
| D19703 | .220934168 | 13.185424805 | .124460736 | 4.21875 | 1.06250 | .43750 |

| Contrast | J mean [descriptive conditional df2 t95] | Service mean [conditional df2 t95] | J averaged fixed-endpoint world df31 t95 | Service averaged fixed-endpoint world df31 t95 |
| --- | --- | --- | --- | --- |
| D−K | +.004257073 [−.001054199,+.009568346] | +.325724284 [−.018952737,+.670401305] | [.000041617,.008472529] | [.028372020,.623076547] |
| K−B40 | +.003889710 [−.001007656,+.008787076] | +.303141276 [−.050833666,+.657116218] | [−.000209533,.007988953] | [.020791374,.585491178] |
| D−B40 | +.008146783 [.004504537,.011789030] | +.628865560 [.328362082,.929369038] | [.000745462,.015548105] | [.127192056,1.130539064] |

The three paired continuation means in master order19701/19702/19703 are:
D−K J+.002372249/+.006580406/+.003818565 and service+.227050781/+.484375/+.265747070;
K−B40 J+.006165540/+.002797438/+.002706152 and service+.467651367/+.218261719/+.223510742;
D−B40 J+.008537789/+.009377844/+.006524717 and service+.694702148/+.702636719/+.489257813.
Every observed joint mean is positive, but this is not a retrospective unanimity
adoption rule. The df2 intervals concern fresh continuation variability conditional
on the selected B19451 and this common panel. They do not count96 endpoint/world
rows as96 training replicates. Averaged fixed-endpoint deployment intervals are a
different estimand. D−K and D−B40 individual endpoint J/service world intervals
exclude zero only for19702; K−B40 individual intervals exclude zero for19701/19702,
not19703. Thus the positive average does not certify each endpoint. No interval is
selection-adjusted; this remains exploratory and is not confirmation.

**All adverse world identities and tails.** The reader retains signed vectors,
positive/tied/negative counts and extrema for every metric and all224 trajectories.
For the main J contrast, adverse world indices are:

| Contrast/master | Adverse J worlds |
| --- | --- |
| D−K/19701 | 0,2,4,5,6,7,8,9,15,16,19,21,23,24,27,31 |
| D−K/19702 | 2,6,7,8,9,13,15,19,22,25,31 |
| D−K/19703 | 0,2,4,10,14,16,18,21,22,23,24,29 |
| K−B40/19701 | 2,5,6,7,8,13,14,15,22,24,25,30 |
| K−B40/19702 | 2,5,6,7,8,12,13,15,16,22,25,27,28,30 |
| K−B40/19703 | 2,4,5,6,7,8,9,11,13,14,15,16,18,24,27,29,30 |
| D−B40/19701 | 2,5,6,7,8,9,15,16,19,24 |
| D−B40/19702 | 2,5,6,7,8,13,15,19,22,25,31 |
| D−B40/19703 | 2,4,5,7,8,9,14,16,18,22,23,24,27,29 |

Service-adverse worlds differ and are separately preserved: D−K has14/9/14 losses,
K−B40 has12/10/16, and D−B40 has10/11/12. D−K's worst J and service losses coincide
at19701/world15:−.029607961 J/−2.1484375 users; its greatest gains occur at19702/world10:
+.068993614/+4.84375. D−B40 at19701/world15 loses−.050991350 J/−3.53515625 users,
and at19701/world10 gains+.087161393/+5.83984375. K−B40's worst J is−.021383389 at19701/world15;
its worst service is−1.40234375 at19703/world2. Positive grand means are not dominance.

D−K, K−B40 and D−B40 mean differences in worst-tick service are respectively
−.03125/+.072916667/+.041666667; all conditional and averaged-world intervals cross zero.
D−K can lower a world's minimum by5 (19702/world22), and D−B40 by5 (19701/world15).
Mean zero-tick differences are−.9375/−.1875/−1.125; only D−B40's conditional df2
interval excludes zero, while its averaged-world interval crosses zero. D−K zero
counts worsen at19702/world29 and19703/worlds14,17, including+5ticks at19703/world17.
D−B40 zero counts worsen at19702/world29 and19703/worlds14,17,29; its greatest increase
is+4 at19703/world14, versus a30-tick reduction at19701/world26. K−B40 increases zero
counts at19701/worlds12,29;19702/worlds1,12,29;19703/worlds12,14,29, with+12ticks at19703/world29.
Mean longest-gap differences are−.447916667/+.09375/−.354166667, all intervals cross zero.
D−B40's longest gap worsens inworld29 for every master and in19703/worlds14,17;
19701/world29 has+2ticks despite its mean zero-tick reduction. K19701/world12 has an
8-tick longer gap. These are consequential package tradeoffs, not physical-safety tests.

Quality also has a tradeoff: D−K/K−B40/D−B40 mean Q differences are
−.001010222/−.001180893/−.002191115. Only K−B40's conditional interval is wholly
negative; none of the averaged-world Q intervals excludes zero. D lowers height
relative to K by.2365m on average and to B40 by.4977m; D floor occupancy is
75.91%/77.39%/76.11%, versus K75.04%/75.68%/75.78% and B4074.45%. Boundary occupancy
moves in mixed directions (D19703 exceeds both K19703 and B40). Mean paths per UAV
are7086.19/7038.57/7020.96m for D,7081.35/7053.00/7053.09m for K,7063.76m for B40.
Neither a shorter path nor a lower altitude supplies a battery/collision/safety conclusion.

**The learned interventions executed.** All39942 base-actor parameters per endpoint,
including GRU and variance, remain exactly parent-identical. The zero forecast
critic projection remains zero; old critic tensors move by norms3.08–3.71. K's
three parameters move from zero to nonzero b in all three fits, with final correction
vectors (pre-tanh mean units):
19701(−.032851357,+.035475388,−.000204057),
19702(−.016468851,+.008935112,−.033845045),
19703(−.013916681,+.048647176,−.013122307).
Raw traces verify these corrections are constant. The approximately1e-9 aggregate
standard deviations are cancellation arithmetic, not state variation. This is an
active, learned ordinary calibration comparator, not a static or untrained policy.

D hidden/output groups have16064/195 parameters and both move; hidden displacement
norms2.881/3.269/3.709 and output norms.372/.393/.385. Across all final rows, its
correction means and coordinate standard deviations are:

| Master | D mean correction (x,y,z) | D correction SD (x,y,z) | D correction RMS / K RMS | Same-noise executed-action change RMS, D / K |
| --- | --- | --- | --- | --- |
| 19701 | (−.082360,+.078409,−.011514) | (.006212,.007446,.002251) | .066219/.027915 | .042586/.017995 |
| 19702 | (−.059002,+.025838,−.084447) | (.006933,.012167,.006509) | .061953/.022335 | .035713/.012641 |
| 19703 | (+.005579,+.058983,−.015484) | (.010907,.030731,.006724) | .040111/.030180 | .025805/.019412 |

Thus D has real variation and changed actions; D19701/19702 also have large nearly
constant offsets. D produces larger corrections than K despite K's prospective10x
actor-lr adjustment. This leaves finite optimization geometry/amplitude as a serious
ordinary account of D's package difference. It does not establish useful state use,
message semantics or coordination. Both whole policies still depend on state/history
through B19451. D19703 has six final-evaluation coordinate entries at the declared
95%-of-bound threshold (fraction.000048828125); all other endpoint fractions and
all training aggregate saturation fractions are zero. No correction exceeds the.1
hard bound. Near-zero saturation does not establish adequacy of the radius/noise.

Each fit completed1024 actor and1024 critic updates with nonzero actor gradients.
K first/last16-rollout mean gradient norms remain about.0127–.0144/.0131–.0144;
D about.0229–.0277/.0405–.0468. Critic value losses decrease across first/last16-rollout
windows for every fit (initial74.27–92.33; final36.37–51.68). Fixed Gaussian entropy
stays23.17015457 as designed; it is not executed-action entropy or evidence of newly
learned stochasticity. The first two training episodes in every fit have zero
correction, and all final rows have nonzero correction. These facts rule out an
inactive/interchangeable implementation, not undertraining or all optimization accounts.

**Actual exposure and resource cost.** Combined persisted exposure is3296 resets:
3072 training plus224 final-evaluation episodes;786432+57344=843776 native team steps,
4218880 motion samples and843776 RR attempts. There are1536 rollouts,6144 actor and
6144 critic Adam calls,15728640 actor replay rows and3145728 critic replay rows,
with833905 delivered/9871 censored packets. Eight actual constructors include six
original and two recovery constructors. The original interrupted world9 may add
0..256 unpersisted native steps, which cannot be reconstructed as zero. It is not
a seventh fit or a new sampled panel. Inherited27 policy fits+3 predictors and
3907584 result steps therefore become33 policy fits+3 predictors and4751360 persisted
steps, plus that unknown original prefix. Recovery adds0fits/0predictors/14080steps.

Five completed original-cell resource records total2008.655337 CPU-s. The original
sixth-cell and batch CPU finalizers did not run; their missing values stay unknown.
Original acceptance-to-exit wall is2525.748568s, not an imputed CPU count. Recovery
adds27.833739 worker CPU-s and26.358138s worker wall after input validation (native
acceptance-to-exit28.330562s), lifetime peak264400KiB; the full reader adds55.93CPU-s,
56.03s wall and234592KiB peak. The failed first recovery adds1.753005s acceptance-to-exit
wall and unknown CPU, with zero scientific calls. Engineering/tests/reviews are
support costs without complete timing. The3CPU-hour original and600CPU-second
recovery limits were not triggered, but absent original CPU telemetry is not proof
of a measured full-batch budget total. Known finalized CPU subtotal for original
five cells+successful recovery+reader is2092.419076s; it excludes the original sixth
cell, failed attempt and support. No complete cumulative CPU-hour figure is invented.

**Working explanation after the complete read.** B06 strengthens the bounded
continuation capability beyond B05: D's complete mean J/service gains over B40 have
positive descriptive conditional intervals, while all adverse worlds remain. K's
active three-vector also has positive observed joint means in each continuation,
retaining calibration as a useful ordinary candidate. D's mean increment over K is
positive in each pair and in the averaged fixed-endpoint world intervals, but the
three-continuation interval remains unresolved. This supports a finite package
signal, not equivalence, robust recipe preference, causal state-information value,
message-content value or proof that freezing caused the gain. It neither erases
B01–B04 adverse results nor requires declaring broader learning impossible.
Independent result diagnosis and the investment disposition follow below; no new
world, fit, parent, counterfactual or architecture is implied by this reading.

### Independent diagnosis, DM response and investment boundary

Registered Scientific Reviewer `/root/dm_calibration_recovery/critic_b06_recovery`
formed its result explanation in the separate context used for the outcome-blind
recovery disposition; it received original evidence and fixed comparisons, not the
DM/Root result explanation. It independently reconstructed all224 raw hashes and
J/service/Q/fee/tail/correction values, primary intervals and exogenous witnesses;
loaded all12 learned checkpoints for equality/finiteness/movement, inspected all6144
update records and five consequential raw positive/adverse cases. It relied on the
completed reader for exhaustive physical/channel/density reconstruction and checked
B05's hash-bound reading and relevant source without duplicating its remote raw
archive. Its evidence consumers have all finished. **MATERIAL_DISSENT: no.**

The reviewer recommends closing B06 while retaining its positive conditional
capability. It distinguishes positive observed D−K means from uncertain continuation
inference, and explicitly rejects both equivalence and a causal state-dependent
coordination claim. Its strongest ordinary explanation is effective calibration
with different finite optimization. It verified that the constant mean component
accounts for99.25%/97.93%/77.18% of D correction second moment. I recomputed these
fractions as squared global coordinate means divided by their squared means plus
variances: .992471610/.979297268/.771829693. They measure correction magnitude, not
the fraction of return explained; small variable components can be consequential.
This quantitative diagnosis strengthens the competing calibration account without
pretending that D's varying component was already ablated.

The reviewer also sharpened two tail statements. D panels contain8/12/34 total zero
service ticks, versus B40's54 and K's43/53/48. D19703/world14 newly introduces four
zero ticks where B40 has none; world17 gains4.910156 users/tick yet doubles zero
ticks from4 to8. I checked both records. Unlike B05, mean world minimum service does
not deteriorate for every D endpoint. D−B40's mean J decomposes into+.008804118 from
service and−.000657335 from Q at equal fees. I checked that accounting as well.
Thus B06 strengthens useful bounded adaptation and active ordinary calibration,
while leaving message mediation, useful varying corrections, independent-parent
generalization and optimality of K unresolved. The sparse threshold exposure is not
a bound-saturation diagnosis, and all actual cost/missing telemetry above is retained.

I accept the recommendation to **end this fixed batch, retain B19451, all six B06
endpoints and their positive/adverse evidence, select no new default from this panel,
and buy no further training now**. This is closure of the tested recipe, not
rejection of the parent learning question or denial of the observed D capability.
B06 used the competent trained K comparator requested by the selection review;
its active learning and positive conditional means rule out treating it as a failed
straw comparator. D's larger useful package still merits preservation as an asset.

For Root's marginal-allocation comparison, the reviewer favors a concrete optional
zero-fit functional comparison over another six-fit block: freeze each D endpoint's
mean pre-tanh correction using this completed panel, compare all three D endpoints,
all three corresponding constant variants and B40 on fresh common tuples, with each
policy evolving on its own executed history. At32 worlds this would cost224 H256
episodes/57344native steps/0fits; recovery throughput is only a rough110CPU-second
scientific anchor, excluding engineering/reading. Constant variants preserving the
benefit would favor inexpensive calibration without asserting equivalence; a retained
D increment after matching its constant component would support further development
of varying corrections, still not message-specific causality. Failure to transfer
or continued decision uncertainty would preserve B06's positive but narrow result
and favor redirection, without automatic extra panels.

I judge this a more discriminating in-question possibility than unchanged training,
new-parent replication before a deployment decision exists, or radius/noise tuning
without evidence of their predicted bottleneck. It is **not an admission gate** for
all learning and is not selected or authorized as a new study here. A complete direct
experiment on a consequential independent question may be worth more; Root owns
that cross-question comparison. Current cost is33policy fits+3predictors and4751360
persisted steps plus0..256 unknown original steps. Closure/retention is the selected
present action; independent-parent confirmation, a fresh-panel asset decision or the
above targeted comparison each require a concrete prospective purpose. No producer
or owner decision is fabricated as an idle dependency. Current native scientific
scope is complete; Root receives the evidence and optional next-investment choice.

### Durable evidence before source/scratch retirement

Required evidence stays on configured local_linux at the two canonical paths
`/home/fires/hmasd-wsl/runs/uav_message_content/b06_calibration/` and
`/home/fires/hmasd-wsl/runs/uav_message_content/b06_eval_recovery_a02/`.
The original207-file tree is unchanged:60391081 logical bytes/60796928 allocated
file bytes, inventory74d949fe...15b. The recovery tree has72files,
16344235logical/16482304allocated file bytes and inventory
aea1337a31e958e149cb245ca5eb01137f6439b0a72351765305d2819bc9b1fa.
The inventory algorithm is the same sorted(relative-path,NUL,decimal-size,NUL,
file-SHA256,newline) concatenation used above. Recovery `reading.json` is855118bytes,
SHA2568906099bd8280c378bb9a520df3f1118eca7fc0095bfac792dd8cba3be94e4b7.
The separate failed attempt remains at `runs/uav_message_content/b06_eval_recovery/`
with7files/11329logical bytes, inventory
8b20bd9177b53a44ad794054d79b022a1425256366fdd45188ac663f19ebbc32.
Compact config/summary/readings/source/native status/observer and reader-resource
records are published; raw NPZ trajectories, training/update streams and12checkpoints
stay in these single durable evidence locations. Their per-file hashes are bound by
the saved cell summaries and complete reader. No bulk tree is copied or archived as
a cleanup condition. Useful recovery/checkpoint/reader code and focused tests stay
on main because they reconstruct this interrupted result and verify its semantics.

### Measured closure after publication

Complete result/background publication is `da3c164f59d89e415e988cf74b08582108220d57`.
At22:31UTC all three native operations again had consistent valid exit witnesses
(−15,1,0 respectively) and absent recorded runners/supervisors. All three observer
states were stopped with no wake/unconsumed event and absent daemon PIDs. Reviewer,
Implementer and Scientific Reviewer had no remaining evidence consumer or running
work. No result, review, transport or new study remains active.

After publication, exact-target `hmasd_snapshot_gc.py` preview initially refused
ordinary process inspection of own process383 (`/proc/383/cwd`, permission denied).
The tool's supported `--sudo-process-scan` read-only inspection resolved that refusal:
all three snapshots were clean, terminal, unreferenced and reachable from main.
Preview then `--apply` under the shared main writer lock removed:

| Deleted target under `.git/hmasd-launch-sources/` | Allocated bytes before | After |
| --- | ---: | ---: |
| ad9d60efa12645809a86268a0aa464da | 1650012160 | 0 |
| 1f322e8efef04d45860f130b11795047 | 1656188928 | 0 |
| e32e808e2d854c3886de414ba28874c7 | 1656233984 | 0 |

A fresh read-only process-reference scan also found no consumer for each remaining
manual target. Deleted owned `temp/directions/uav_message_content/` (53248bytes,
three stopped observers plus request scratch), and six rebuildable bytecode-cache
directories: `experiments/candidates/uav_message_content/{__pycache__,b05/__pycache__,b06/__pycache__}`
(98304/36864/65536bytes) and the matching paths under `tests/` (24576/40960/86016bytes).
The redundant local463357-byte parent staging file
`/home/fires/hmasd-inputs/uav-message-b06-B-34871c49.pt` freed466944allocated bytes.
Before deletion I rehashed the canonical parent at
`wsl_4070:/home/wu/projects/HMASD/runs/uav_message_content/b02_preserved_scalar/19451/B/final.pt`
and verified the unchanged34871c49...59da2 digest, and checked the local copy matches.
That remote canonical checkpoint remains the required parent; future reconstruction
can stage those exact bytes, rather than assuming the retired local path still exists.

All11 measured targets are absent. Net allocated bytes reclaimed from those targets
are **4963307520** (snapshot subtotal4962435072; scratch/caches/staging872448), measured
with `du -s -B1` before and absence/zero afterward. This is target disk reclamation,
not a claim of shrinking retained Git history or a global host-free-space reading.
No backup, tarball, replacement worktree or copied retention tree was made. No cleanup
blocker remains. All three admission claims/manifests/exit records remain intact;
final rehash confirms all207 original files,72 successful-recovery files and7 failed
attempt files retain the inventories recorded above. Required trajectories, streams,
checkpoints and useful reconstruction/checking code remain; unrelated writers are
untouched. B06 is read and closed, the direction is reserve/idle, and the optional
next scientific allocation belongs to Root without an automatic continuation.

<a id="b07-finite-message-design"></a>
## 2026-10-02 - B07 prospective finite-message comparison, source-only selection

**State: one bounded design for Root's cross-question choice; no new scientific
execution is selected.** Native successor `/root/dm_message_budget`, actual UUID
`01a0fd1a-8a66-7ba1-b7c3-74be96008f0a`, parent Root
`01a0ef2b-a391-7693-a748-60e24be246ae`, adopts only this direction's paths on shared
main. RESEARCH at `1ef16a5dc5b7a0f521ec189085755ddeb45ee763` records the adoption.
The B06 terminal reading/cleanup above and prior `dm_calibration_recovery` route
both explicitly say no live operation, unread advice or remaining consumer; the
current native tree contains no contrary old lead. This is succession after complete
closure, not recovery of an old run. Codex pause is lifted; Claude's pause and all
other ownership remain unchanged. No S7, typed-bank or correction-compression edit
ownership is inherited. This turn has performed source/metadata/hash/primary-passage
reads only: **0 fits, 0 model forwards, 0 static radio calls, 0 native steps, 0 new
data acquisitions**. No pricing pilot, health query, critic model call or effect is
hidden in the design.

### Question and evidence that changes this choice

The enduring question is whether a finite message can retain a useful cooperative
controller, and whether task-aware encoding adds value over competent ordinary
encoding with the same lawful information, bits and delayed transport. The proposed
contribution is **empirical understanding of a capability/communication tradeoff**,
not a new communication theorem, proven message-mediated coordination or a physical
network saving. The particular study is a lossy retrofit of an existing packet and
frozen receiver, rather than another full policy/content co-adaptation fit.

Current published RESEARCH [topic 3](../../RESEARCH.md#3-marl-增加的是联合行为和信息结构),
[topic 5](../../RESEARCH.md#5-技能和异步性是组织决策的方式其收益需要证据), and
[topic 8](../../RESEARCH.md#structural-research-background) were read at the above
revision. They change this design concretely: keep RR transport and action timing;
retain the stronger useful frozen D asset rather than discard its positive result;
give the ordinary quantizer the same paid observations, policy knowledge and tuning
panel; and require complete own-history service evaluation after any offline proxy
improvement. Neither lower reconstruction error nor a smaller code alphabet proves
closed-loop utility. Shared reward, a shared codebook and a central training loss
do not by themselves establish useful coordination.

Inherited evidence is B01-B06, including their full costs and adverse readings:
B01 C/H/L each learned, but replacement L lost to C/H; B02 retained-field L had a
positive average with seed reversals; B03 retained B19451, O19452 and L19452's new-world
gains over C and provisionally selected B19451. B04 learned forecasts improved their
own prediction errors without a resolved F-over-O native increment, and its continued
geometry controls could lose the parent capability. B05/B06 bounded continuation
retained conditional gains and active ordinary calibration, while message causality
and D-versus-K continuation superiority remained unresolved. B06's six fits, interrupted
prefix and evaluation recovery are not free or new data generated for B07.

The later [correction-compression reading](../uav_correction_compression/NOTES.md#b01-complete-reading)
is relevant read-only evidence: replacing each D by its old-panel mean lost service/J;
D19702 retained a positive conditional B40 increment on another panel, but no new
default was adopted. That is a reason to preserve its varying controller while testing
its message representation. It is not proof that its variation uses message content.
The ordinary alternative is that a small geometry codebook already preserves the
necessary distinctions, making task-aware optimization unnecessary. A second plausible
outcome is that teacher-history imitation improves while trajectory changes erase the
benefit, as proxy/native separation already occurred in this direction.

### Actual host, sender, receiver and paid data

CodeGraph/source reconstruction used the current CADC `channel.py`/`model.py` and
this direction's `b05/channel.py`, `b05/model.py`, `b05/collector.py`, and
`b06/model.py`/`collector.py`. The original N5/U50/H256 host has static anonymous
users, a 1000 m square, 50-150 m height and primitive sampled motion every tick.
The local actor receives raw104 (own xyz, up to20 anonymous visible-user relative
xy/SINR rows, up to10 anonymous visible-peer xyz/SINR rows, clock), its previous
executed command3, zero remaining1, and the common63 transport fields. These are
current GOOD/BAD, own physical ID, t-mod5, own pending bit, and fixed-sender cache
records containing payload7, validity, send tick and age. No user identity, true
served/connection status, unseen map or another agent's hidden state is actor input.

The source packet is `(sender x,y,z; visible-user centroid x,y; 0; count/20)`.
It has six variable FP32 numbers. B04-B06 appended three forecast floats; B06 D/K/B40
set all three to zero. Thus original28 B and later40 B contracts must not be conflated;
even a lossless ordinary serializer can omit their known zeros and use24 payload B.
B07's source vector is exactly fields `[0,1,2,3,4,6]`, in `[0,1]^6`; sender codec
uses this vector only. This deliberately holds the packet source interface fixed
for the retrofit question. Both methods have the same access restriction, while
the frozen receiver retains its whole legal local history. This is not an information
bound on codecs that use richer sender history or on jointly adapted controllers.

At each tick, due messages arrive before actor inference. Only `t mod5` sends;
send-time GOOD/BAD gives delay1/5, with independent .05 regime-flip probability.
The five-tick packet clears before its next slot; every tick has one accepted packet,
no collision and fee.001. All four other agents receive identical payload bytes;
self cache stays invalid. There is no central uplink, scheduler query, receiver ACK
or extra round. Terminal in-flight packets are censored. The native objective remains
`J_net=.014*mean(served_users)+.3*mean(Q)-.001`; Q conditions on actually connected
users and does not stand in for individual service continuity.

The proposed main parent/teacher is **D19702**, frozen in every arm: local canonical
`runs/uav_message_content/b06_calibration/19702/D/final.pt`,568164 B, SHA256
`1a0de628a6c324a5cd0c69f4857b37b4bc1f47c51dc80d2a9a233e7ee7f69840`.
It contains B19451's39942 actor parameters plus16259 correction parameters
(56201 FP32 actor parameters,224804 raw parameter B), the same GRU64 and variance.
Critic parameters are retained in the file but never queried or updated by B07.
The actor/GRU/correction/log-std are frozen, with episode hidden state reset to zero.
The bounded residual still receives input186 and the base recurrent output; the
extra15 forecast inputs are reconstructed zeros. Both encoder and decoder codebook
change only in the codec fit; there is **no receiver or policy adaptation**.

The full-payload B19451 reference stays available at canonical
`wsl_4070:/home/wu/projects/HMASD/runs/uav_message_content/b02_preserved_scalar/19451/B/final.pt`,
463357 B, SHA256 `34871c49874ec716c21438581facfaeca8a25930304a39eb26e001fb2b259da2`.
Its source is `02ede8a4a75cc83e6e18d8b6619f1cfa84bc8d92`; its inherited C is
`456832faaa94afb22cf3faa00bb97b0f129e2f5b72b2eedbb1148523b088cdad`.
Read-only SSH rehashed B, O19452 (`90760a722081dec5442aeec85c9302ae3992dcfb96f0bf919aa81389815aa684`)
and L19452 (`c8df7428611608ae0c2786b6b9e395e8183d3b79b30fcdd197e4fcdc9c643f59`)
to their recorded hashes. O/L are retained capabilities, not needed training inputs
or additional scored programs for this retrofit. All six local B06 K/D final bytes
were also rehashed; no weights were loaded or evaluated.

The actual proposed dataset is the **32 existing D19702 final trajectories**, under
`runs/uav_message_content/b06_calibration/19702/D/raw/final_00.npz` through
`final_31.npz`. All32 file hashes were checked against the saved summary:9061080
compressed B;65029376 uncompressed NPY member B. The ordered filename/NUL/size/NUL/
hash/newline inventory is `a0eaac8dea65434625b9a6778b7b7f147b1698de68a137b622b93a2f3fb04311`.
Summary SHA256 is `c642411146305d20716bec3f9fba510e8021adf9076876079799141b637e2211`;
full episode stream SHA256 is `a61a5b4d367ed8679066c9b580a8b5fa8cf1e8fff47d772704d89a2714fdd0f5`.
NPY headers and collector source establish actor_input `(256,5,186)`, packet `(256,10)`,
composed_mean `(256,5,3)`, sender/due/good, records, physical positions, log_std,
and connected_users `(256,50)`. Full training trajectories were **not** retained;
the512 compact training episode rows are not an offline observation bank. No attempt
to fabricate them or collect another bank is included.

Use old episode indices0-23 for fitting (6144 sends,30720 actor rows) and24-31 for
development (2048 sends,10240 actor rows). The old physical/channel/motion seed bases
are1970002000/1970007000/1970003000. These panels were already exposed in B06 and
may now supply paid development data; they are not fresh confirmation. The stored
**composed** means supply all teacher targets, so no new teacher-label acquisition,
critic/Q evaluation or rollout is required. A single32-episode frozen replay would
check those target/input bindings inside the complete purchase; that is8192 batch-of5
actor steps, not zero model work. The alternative B40 data are intact locally (32
hashed files,8573139 B), but they are not silently mixed into D's visitation dataset.

### Complete finite alphabet and transport bill

Choose **one256-symbol alphabet, fixed8-bit payload per scheduled send**, no entropy
coding or variable length. The ordinary and task-aware codecs each install a common
`256 x6` FP32 codebook (6144 B) plus six FP32 metric scales (24 B). Encoder chooses
the nearest codeword in that fixed diagonal metric; decoder looks up the same six
floats and reinstates the four known zeros for the B06 receiver. Codebook rows are
shared by all physical senders, not five free sender-specific dictionaries. Lowest
index breaks exact ties. No dictionary or embedding is transmitted with each packet.

The full modeled serialization bill is explicit, despite the simulator's abstract
link: payload8 bits + sender3 + send_tick8 + valid1 + four reserved zero bits =
**24 bits/3 B per packet**. Timestamp0-255 is unambiguous within one synchronized
H256 episode; resets discard all old packets. Age is calculated from current clock
and delivered send_tick, not a hidden additional float. Validity is stored per cache
slot, initially false; the header's valid bit is one for a received data packet.
Own ID uses3 installed bits per agent and RR rank follows the common clock. To avoid
calling the public channel and clock free bandwidth, separately count a conservative
common beacon of tick8 + current GOOD/BAD1 + seven zero padding bits =16 bits/2 B
per primitive tick. Thus the modeled team transmission ledger is **40 bits/5 B per
tick**, or1280 B/H256, under one broadcast medium. This beacon is the already-supplied
public process, not a new learned signal or a changed delay. Each data broadcast
has four logical deliveries, not four independent on-air copies; public beacon reaches
all five. A BS relay/unicast distribution network would have a different bill and is
not assumed. Clock synchronization, reset discipline and reliable broadcast are
explicit exogenous facilities; actual PHY framing/CRC/radio energy are unmodeled.

Under the same header/beacon convention, original28 B is32 B/team tick, original
40 B is44 B/team tick, and competent lossless omission of known zeros is28 B/team tick.
The honest finite-precision reduction is therefore28-to5 B versus that lossless
reference, not40-to1 B. Native fee,1/5 delays, arrival process and send opportunities
stay unchanged: **no J fee saving, faster delivery, throughput or radio-energy claim**
follows from this ledger. Report codec encode/decode CPU separately from the imposed
simulator ticks; compute latency is not smuggled into a different transport model.

One installed codec adds6168 B/device,30840 B across five devices, apart from a small
fixed serialization specification and ID/reset setup. If the codebook must be sent
from a coordinator once, charge6168 B for one reliable broadcast or30840 B for five
unicasts, explicitly outside the per-episode packet stream. Saving23 B/tick against
lossless full geometry amortizes these at269 ticks (two H256 episodes) or1341 ticks
(six episodes), respectively; this is byte accounting, not measured energy/payback.
Frozen D actor deployment additionally carries224804 parameter B per device,1,124,020 B
across five; the full568164-B checkpoint/critic need not be deployed, but cold loader
time and actual artifact bytes must be measured. The ordinary and task-aware codec
have the same installed dictionary/scale size and search/lookup form. A six-symbol
alternative would need at least3 payload bits and all this other information; it is
not selected and `log2(6)` does not price this program.

### One complete comparison and equal ordinary rights

Proposed programs on the same32 fresh complete worlds: full D19702; full B19451;
three ordinary-codebook D programs O1/O2/O3; and three task-aware-codebook D programs
L1/L2/L3. The primary contrast is paired Lr-Or; each also reports against full D and
B. Full D is the wider-message reference and full B reveals loss of the retained
correction capability; neither is mislabeled as a matched-bit comparator.

O is a competent same-data vector quantizer. For each of three independent codec
initializations19811/19812/19813, fit256-center k-means++ followed by exactly25 Lloyd
updates in each of two declared metrics: unit range coordinates, or diagonal inverse
training SD with each SD floored at.05. Empty clusters deterministically take the
largest-current-error unused training row, ties by source row index. Centroids stay
in `[0,1]^6`. The ordinary program may exploit known geometry/scales, the frozen
policy and its teacher outputs: choose between its two fitted dictionaries by the
same held-out development action-distribution loss used below, exact ties by unit
metric. Thus it is not forced to ignore planner/policy knowledge or use an obviously
weak one-bit-per-coordinate grid. Its quantizer training objective is ordinary source
distortion; that objective, rather than denial of information, is the comparator.

L starts from each corresponding fitted O dictionary and uses the same metric,
data split, dictionary dimensions and two-way development selection right. Optimize
the dictionary for exactly20 epochs over all24 fitting trajectories,4 complete
episodes per minibatch,120 Adam updates per fit (lr.001, betas.9/.999, eps1e-8,
no weight decay, norm clip1, project codeword coordinates to `[0,1]` after updates).
Forward messages are **hard nearest-codeword bytes**. Backward uses the explicitly
biased straight-through soft-distance reconstruction, temperature geometrically
annealed.25 to.025 over20 epochs. No stochastic message, Gumbel draw, entropy bonus,
new actor feature, new policy optimizer or online adaptation is added. Because the
shared dictionary also defines its Voronoi cells, the sender partition and receiver
reconstruction change together; this is task-aware learned encoding/decoding, not
only a learned post-decoder applied to an unchanged encoder. O itself is fitted, so
the claim would be task-aware fitting versus ordinary quantization, not learning
versus an untrained straw comparator.

For each stored complete trajectory, reconstruct all compressed message deliveries
causally and unroll the frozen receiver's own GRU from zero. Retain recorded private
observations and previous executed commands. With stored teacher mean mu and common
fixed sigma, minimize mean Gaussian KL `sum_d((mu_codec-mu_teacher)/sigma)^2 /2`
over all actor rows; tanh uses the same transform but native clipping/trajectory
effects are not certified by this proxy. No state-value critic is treated as a Q
function. Gradients must pass through frozen receiver inputs, including the base
actor; removing its current `no_grad` wrapper for offline input differentiation may
not change the forward function or update any receiver tensor. This is a specific
high-risk engineering check, not implementation permission in this design turn.

The offline inputs remain teacher histories. Recomputed hidden state handles the
receiver's memory of decoded packets, but the old physical observations and previous
commands do not branch with its new policy. That distribution limitation is central:
only complete native evaluation determines the closed-loop result. No success on
the offline loss is a gate before running the preselected full comparison. All12
codec fits and all eight evaluation programs are bought together or none are.

### Prediction, complete reading and investment branches

Prediction: task-aware fitting lowers development mean-action KL beyond its matched
ordinary quantizer and yields a smaller complete J/service loss to full D, on average
over the three codec initializations. An ordinary book may already preserve enough
to leave no useful L increment. Learning lower offline KL without native retention
would weaken this particular teacher-history-distillation route, not prove a message
information bound or justify automatic receiver adaptation.

New evaluation tuples are fixed prospectively as physical1981002000+e,
channel1981007000+e and motion1981003000+e, e=0..31. Sample the inherited motion
distribution; codec is deterministic. All programs execute their own observations,
commands, hidden states and message caches. Common scene/channel/innovation witnesses
must match, not just seed labels. No old panel is pooled with the fresh panel.
Codec selection uses only the eight old development episodes; no final-world tuning,
checkpoint selection, retransmission, extra bit budget or changed transport follows.

Read per-program J_net/J_physical, users/tick, Q, path/height/boundary occupancy,
worst-tick and p10 team service, zero-team-service ticks/longest run. The retained
connected-user bits permit a required **individual-service** reading: each user's
total served ticks, never-served count, mean waiting age, longest gap including both
censored edges, world worst-user values and signed same-user differences. Report
all adverse worlds and concrete longest-gap cases; aggregate J/absence of team-zero
ticks cannot certify fairness or persistent individual service. There is no energy,
collision-safety or mobile-user claim on this host.

Report three paired codec-seed effects with a descriptive df2 interval, conditional
on this selected D/data; the32-world intervals describe deployment variation of
fixed programs and do not become32 learning seeds or independent parents. The
development best-of-two selection is part of each algorithm's paid exposure. This
is exploration, not confirmation. No general equivalence/adoption claim is made from
a small mean or a nonsignificant difference. For the retention question report the
full paired loss and uncertainty rather than silently choose a post-result margin.

- O retains useful J/service with little native loss and L adds no resolved advantage:
  retain the ordinary finite-message capability; no reason for automatic task-aware
  or receiver training. A deployment with an actual bit-priced link can be separately
  proposed; this study does not certify its economics.
- L's proxy improvement is accompanied by joint native J/service improvement over O
  and useful retention versus D/B: retain that conditional task-aware capability and
  its full training/setup cost. Broader parent/data replication is a later investment,
  not an automatic continuation or a causal message-content claim.
- Both compressions substantially lose the retained D/B capability, or L only wins
  by trading worse individual service: preserve the complete tradeoff/adverses and
  end this8-bit/frozen-receiver purchase. Neither widening bits nor adapting the
  receiver is appended as a repair. Uncertain effects can justify stopping without
  being called equivalence or impossibility.
- Technical missingness preserves the actual fit/forward/native frontier and all
  partial files; it does not become a negative learning result or an automatic retry.

### Full prospective price and present recommendation before review

This resolves the previously unknown **fit count and dominant work** without running
a pricing experiment. Fixed budget is **12 codec fits:6 ordinary codebook fits plus
6 task-aware dictionary fits;0 policy/receiver/critic/predictor fits**. Ordinary fits
are real started fitting attempts and do not disappear from the fit ledger. Three
seed units each contain two metric candidates per method, then one selected endpoint.

| Work | Complete proposed purchase |
| --- | ---: |
| New data-acquisition native / static / teacher-label forwards | 0 /0 /0 |
| Existing data consumed | 32 H256 D trajectories;8192 sends;40960 actor rows |
| K-means++/Lloyd fits | 6, each6144 samples,256 centers,25 centroid updates |
| Task-aware codec fits / Adam updates | 6 /720 (20 epochs,24 complete episodes each) |
| Differentiable receiver presentations | 737280 team rows /3686400 actor rows |
| Old development scoring | 12 dictionaries x8 H256 =24576 team /122880 actor rows |
| One full saved-teacher binding replay | 8192 team /40960 actor rows |
| Fresh native evaluation | 8 programs x32 H256 =256 episodes /65536 steps |
| Native evaluation actor / motion / send counts | 327680 rows /327680 motion draws /65536 packets |
| Full new reader neural reconstruction | 65536 batch-of5 steps /327680 actor rows |
| Full new reader physical reconstruction | 65536 saved action/radio states;0 added native rollouts |
| Total new receiver forward-row presentations | 4505600, including fitted-input, dev, native and reader work |
| Value/Q/planner/counterfactual suffix calls / GPU | 0 /0 |

Book-distance accounting uses direct6-coordinate distances:6 ordinary initializations
and25 Lloyd updates plus final assignment =254803968 center comparisons; six20-epoch
task-aware fits188743680; development6291456; selected-codec native and reader work
25165824. Total **475004928 six-coordinate center comparisons**, plus reductions,
softmax and720 backward/update steps. No all-actions Q labeling or hidden simulator
branch search is required. All readback is part of the purchase; a pure reader and
the explicitly priced neural reconstruction have different costs and must be recorded.

Preferred prospective node is configured `local_linux`, CPU FP32, one Torch/inter-op/
BLAS thread, sequential fits/programs, no GPU. D19702's earlier full training+evaluation
cell cost476.206156 CPU-s,347052 KiB lifetime RSS; the local B40 final32-world cell
cost13.234506 CPU-s, and B06's complete224-trajectory reader55.93 CPU-s. These anchors
imply about106 CPU-s for the eight native panels at the old B40 rate and about64 CPU-s
for similarly scoped reader work, **before** codec costs and cold startup. They do
not benchmark the new full-unroll gradient or nearest-code search. The explicit
planning range is **0.5-2 CPUh for implementation's complete scientific chain and
roughly0.5-2.5h occupied local worker wall**, not a measured throughput or entitlement.
Full cold import/build/load, byte encoding, delivery lookup, all child lifetimes,
support/test/reviewer calls and output/hash publication must be metered separately;
unknown throughput remains an uncertainty, not zero. No pilot is purchased to narrow
this range. Planned implementation/check/review/read/publication support is **8-14
agent-hours**, itself an estimate; this design/criticism is additional support.

Existing canonical data stay one copy. Required proposed inputs are D568164 B and
B463357 B plus the9.06 MB existing raw dataset and compact binding metadata. Do not
copy the whole old direction or recovery tree. A needed local B staging copy adds
463357 B until terminal cleanup; D/data already reside here. Twelve codebooks/scales
add74016 raw B; compact fit history/selected artifacts stay below a few MB. At the
old D trace rate256 fresh traces are about72.5 MB compressed/520.2 MB uncompressed
if all old diagnostic fields were retained; the implementation should retain the
required codec/inputs/actions/user-service witnesses without promising a smaller
unmeasured file size. Plan **0.1-0.2 GiB durable new output**, about0.1 GiB temporary
data/work buffers, and roughly1.6-1.8 GB immutable source snapshot based on this
direction's retired snapshots; source remains additional to scientific data. Allow
roughly **2 GiB additional peak disk and1 GiB process RSS planning**, to be checked
at actual admission. Code review must bound per-batch tensors instead of materializing
the whole fit xepoch xcodebook graph. Snapshot/core-dump/log failures cannot silently
escape the storage accounting. These are planning figures, not measured resource
guarantees; actual node memory/disk and source bytes are checked only for a selected launch.

Inherited direction investment remains **33 policy fits+3 predictors,4751360 persisted
native steps plus0..256 interrupted steps**, with missing original B06 CPU and support
telemetry left unknown. Correction-compression's224 episodes/57344 steps and its
engineering/read costs are separate inherited evidence, not erased by choosing D.
The proposed result would add12 codec fits and65536 new native steps, not rebrand
them as zero-fit because no motion policy is trained. All failed/adverse records remain.

My present recommendation is to offer this **single complete frozen-parent codec
comparison** for selection, ahead of another from-scratch joint communication fit:
it can establish an ordinary small-message capability or identify a task-aware
increment while reusing paid targets. Stopping remains a serious alternative because
this abstract link has no measured bit-related bottleneck and full physical economics
would require a separately selected contract. The independent scientific review below
must judge whether that empirical value warrants the support cost, challenge the
ordinary comparison and the single-teacher visitation premise, and can recommend
no purchase. No implementation has started and no effect follows this draft.

### Verified primary-source bridge and limits

The concrete literature need was whether decision-sensitive message clustering has
a primary-source basis, and what information its construction actually needs. The
three local locating stores were consulted narrowly: foundations index P15 (IMAC,
message sufficiency/bandwidth); Inst-sci catalog/structured source MARL-0049; and the
My-lib title/abstract search for RGMComm/discrete-communication terms, which found no
matching entry under that conjunctive query. That miss is only query/store coverage,
not absence of prior art. No novelty claim or whole-corpus re-review is made.

I independently read **MARL-0049 RGMComm, PDF pages3-5**, cross-checked the same
structured pages at `/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0049.json`
and PDF `/home/fires/projects/Inst-sci/papers/MyLib/pdf/MARL-0049.pdf`, and verified
the [AAAI primary publication](https://ojs.aaai.org/index.php/AAAI/article/view/29680)
(Chen, Lan and Joe-Wong,2024, DOI10.1609/aaai.v38i16.29680). Their construction
clusters source observations using joint action-value vectors and visitation weights;
the matrix-game example distinguishes observations that favor the same receiving
action. The useful bridge is to preserve decision distinctions rather than insist on
uniform observation fidelity. Their Q/optimal-policy bound is **not** available from
our state-value critic, and their synchronous/current-observation analysis does not
certify this delayed recurrent continuous-control retrofit. B07 substitutes an explicitly
weaker, directly available teacher-action KL objective. That is a conjectural design
mapping, not a theorem transfer, performance guarantee or new empirical result.

### Prospective node correction before selection review returns

Root supplied the current owner's **remote-first** preference after reading the
draft. I adopt it: the proposed node is **configured `wsl_4070`**, using
`/home/wu/.venvs/hmasd-gcc-31021/bin/python`, CPU FP32 and one Torch/inter-op/BLAS
thread. This supersedes the draft's `local_linux` preference and local wall wording;
it does not change any effect count, fit horizon, asset, message or endpoint.
Stage only the local D checkpoint568164 B and its32 input traces9061080 B plus
compact bindings (9629244 B before metadata) on that node. B19451 is already
canonical there. Necessary temporary input duplication, transfers/hash checks and
cold process lifetime are paid and deleted after verified terminal collection;
no entire direction copy or local fallback operation is implied. The rough2 GiB
extra-disk plan now includes these roughly9.63 MB of input staging.

The old local CPU timings remain labeled anchors, not a remote throughput promise.
Full-GRU input backpropagation, nearest-code search, imports/builds and actual child
lifetimes are unmeasured on the chosen runtime;0.5-2 CPUh/0.5-2.5 occupied-worker h
remain explicit uncertain planning ranges, and8-14 support hours remain an estimate.
The known remote interpreter failures and mitigation history are not declared
resolved. Fresh admission would apply only after selection; no runtime health,
forward benchmark or pilot is authorized or useful merely to narrow this price.

The stored D means define a fixed paid teacher-data version; no target regeneration
is proposed. The priced one-pass teacher replay checks exact model/input/record
identity and reports numerical mean/density differences across runtimes in full.
Cross-runtime numerical identity is not assumed from a matching checkpoint digest.
Scientific selection review is asked to assess the appropriate binding/reading
contract; no failed reader, epsilon change, new teacher or source edit is preauthorized.
All native programs would execute together on the same selected runtime. No result
here has depended on an unperformed cross-runtime forward.

<a id="b07-independent-selection"></a>
### Independent scientific selection review — complete original answer

Registered `hmasd-research-critic` child
`/root/dm_message_budget/finite_message_selection_critic`, separate context with
`fork_turns=none`, returned the following complete answer on 2026-10-02 UTC. It had
the actual question, original supporting/adverse records and the concrete proposal;
the remote-first correction was supplied while it was reading. It owned no files,
launched no effects and spawned no children. The original response is preserved
below without replacing its recommendation by the DM's interpretation.

```text
**Recommendation: retain this single complete comparison for Root’s purchase decision, with the runtime-binding and interpretation clarifications below.** I favor it over another joint policy/message training attempt. It asks a different, useful question using an existing capability: whether ordinary quantization suffices, and whether task-aware fitting preserves more of that capability at the same message budget. It warrants bounded exploration, not confirmation or a communication-system deployment claim. My recommendations add no fits, native episodes, pilot or additional review.

This review used a separate context without inherited DM/Root conversation. The assignment disclosed the proposed recipe and later supplied the remote-node change; I reconstructed the original evidence before reading the full B07 proposal. I did not read the archived Oracle advice.

I independently checked:

- The channel, actor and collector sources, including RR scheduling, lawful packet construction, delayed delivery, zero forecast fields, frozen-base semantics and the state-value critic.
- D19702’s checkpoint digest; all 32 D and 32 B40 raw-file hashes; native reward/service reconstruction; common initial states, channel sequences and recorded innovation bindings. Reconstructed innovations agree within FP32 arithmetic.
- D’s complete saved actor-input bank: packets reconstruct exactly from lawful sender observations, cached records match actor inputs, previous-command inputs match each trajectory’s executed actions, and the forecast tail is zero.
- B06’s consequential contrasts, configuration, exposure and resource records; correction-compression’s native summary rows and its positive/adverse reading; the earlier B01–B05 evidence needed to preserve the lineage’s mixed outcomes.
- The prospective work and byte arithmetic, and MARL-0049’s relevant primary passage.

I did not perform model forwards, experiments or runtime health checks. I did not independently reconstruct the later correction-compression remote NPZ bank, reload checkpoint tensors, or repeat every earlier B01–B05 raw reading. Cross-runtime numerical compatibility and prospective throughput remain unverified.

The saved evidence supports preserving D as a useful conditional asset. On the original B06 panel, D19702−B40 is **+.009377844 J and +.702636719 users/tick**, with 11 service-adverse worlds. Across all three D continuations, the conditional mean gains are +.008147 J/+ .628866 service; the D−K intervals still cross zero. On correction-compression’s fresh panel, D19702−B40 remains positive, +.007748583 J/+ .529541016 service, while losing service in 18 of 32 worlds. Thus “useful controller” is supported; uniform improvement is not. The relevant primary outputs are the [B06 reading](/home/fires/hmasd-wsl/runs/uav_message_content/b06_eval_recovery_a02/reading.json) and [correction-compression summary](/home/fires/hmasd-wsl/runs/uav_correction_compression/b01_mean_deployment_a02/summary.json).

The later constant substitution matters causally, but narrowly. C19702−D19702 lost .002117960 J and .143554688 users/tick; all three tested substitutions had negative J/service intervals and failed their frozen retention rules. Small variation in a correction therefore cannot be dismissed merely because its constant component dominates its squared magnitude. This supports retaining the varying function over those particular means. It does not identify message-mediated coordination, prove every constant inferior, or resolve D versus competently trained K.

The earlier record also remains consequential: B01 learned content lost against ordinary alternatives; B02 produced positive averages with unstable continuation rankings; B03 retained useful B/O/L assets; B04 improved prediction without demonstrating its native increment; B05’s bounded continuation gained conditionally while its forecast increment remained unresolved. These observations argue against another automatic content-learning rescue. They do not already answer this frozen-controller quantization question.

**The strongest ordinary explanation is that a shared 256-center geometry quantizer already preserves the distinctions this fixed, stochastic controller needs.** The proposed ordinary comparator is competent for that question: fitted vector quantization, two reasonable metrics, matched data and initialization exposure, and selection using the same development action loss and policy knowledge. No additional baseline search is needed. A task-aware victory would concern this finite fitting package, including its extra optimization, rather than learning versus an uninformed comparator.

There is also a constructive reason to try L. Different packet errors can have different effects on the frozen receiver, so minimizing geometry distortion can spend codewords on distinctions that barely change its actions. Optimizing action loss can redistribute that error. Reconstructing deliveries and unrolling the receiver’s GRU throughout each complete recorded trajectory makes this objective more directly relevant to preservation than B04’s forecast error. It is still evaluated on one selected teacher’s old visitation distribution. Small average row loss can accumulate across **1,280 actor rows per episode**, and eight old development episodes cannot establish generalization.

The literature bridge is appropriately limited. MARL-0049 constructs communication using action-value vectors and visitation weighting; the current scalar state-value critic cannot provide those quantities. Teacher-action KL is a legitimate different objective, without inheriting RGMComm’s return guarantee. I checked the relevant passage in [MARL-0049 PDF, pages 3–5](/home/fires/projects/Inst-sci/papers/MyLib/pdf/MARL-0049.pdf), with its [structured source](/home/fires/projects/Inst-sci/papers/MyLib/json/MARL-0049.json) and [primary publication](https://ojs.aaai.org/index.php/AAAI/article/view/29680).

Two clarifications should accompany the retained design.

First, **separate immutable teacher data from execution-runtime identity**. Keep the old composed means fixed. Exact bindings should cover checkpoint/data bytes, configuration, input ordering, delivery reconstruction and frozen parameters. The priced replay on the chosen runtime should report its uncompressed D means and densities against those old labels. Nonzero cross-runtime floating-point differences should not automatically become a failed scientific comparison or trigger target regeneration.

Report the uncompressed replay loss beside codec losses as a reference discrepancy; do not subtract it as though squared errors decomposed additively. Native full D, full B and all codecs must run on the same selected runtime, so their native comparison remains well defined. A substantial old/new discrepancy would weaken the description “preserves the previously demonstrated numerical controller” and the interpretation of the imitation objective. Wrong bindings, nonfinite outputs or changed forward semantics are technical failures. None authorizes a post-result epsilon change, replacement teacher or automatic retry. This clarification uses the already-priced replay.

Second, **treat retention as a measured loss distribution, not an undeclared equivalence certificate**. The proposal explicitly declines a prospective retention margin, which is acceptable for exploration. Its answer should consequently quantify losses and uncertainty rather than announce binary preservation from nonsignificance. Likewise, one worse user or world must not become a retrospective unanimity requirement. Report the individual-service tradeoffs and keep any later adoption preference separate. Waiting-age initialization and censored-edge conventions should be fixed in the reader specification before exposure.

The smallest worthwhile complete observation is the proposed one: three paired codec initializations, both declared metric candidates, the fixed old train/development split, and the eight programs on one fresh common 32-world panel. Full D establishes compression loss; full B shows whether the retained correction capability survives. Neither replaces matched-bit O. No preliminary proxy-success gate, no-message control or additional diagnostic batch is necessary for this estimand.

The outcomes would change the following judgments:

- **O preserves useful performance and L adds no clear native increment:** retain the ordinary finite-message capability and end task-aware investment in this recipe. This would be a useful answer, without proving message irrelevance.
- **L improves development KL and joint native J/service over O, with acceptable disclosed service tradeoffs relative to D/B:** retain a conditional task-aware capability. Replication across another parent/data source becomes a testable future option, not an automatic purchase.
- **KL improves but native outcomes do not:** lower confidence in this teacher-history fitting procedure’s practical increment. Do not infer an information bound or automatically adapt the receiver.
- **Both compressed packages materially lose useful capability:** end this particular eight-bit, frozen-receiver attempt. Wider alphabets and receiver adaptation remain separate investments.
- **Effects remain uncertain or execution is incomplete:** preserve that outcome and actual exposure. Neither requires more episodes or a retry.

I found **no material arithmetic error** in the declared price. Twelve codec fits, 720 Adam updates, 65,536 fresh native steps, 4,505,600 actor-row presentations and 475,004,928 six-coordinate center comparisons reconcile. The honest modeled stream comparison is **28 versus 5 bytes/team tick**, including header and beacon, with 6,168 installed codec bytes/device. The 269-tick broadcast and 1,341-tick five-unicast setup amortizations also reconcile. These are byte accounts under declared facilities; unchanged fees and delays provide no measured transport benefit.

The remote-first delta preserves the scientific comparison. Its roughly 9.63 MB D/data staging is appropriately explicit. The 0.5–2 CPU-hour and 8–14 agent-hour estimates are planning prices, not validated bounds. Full recurrent input backpropagation, cold startup, current-runtime reliability and actual peak memory remain feasibility uncertainties. Earlier runtime failures are technical risk, not adverse evidence against compression. Historical learning, readback, staging, snapshots and support remain paid costs; zero new policy fits does not erase them.

My strongest consequential reservation is therefore **investment value**, rather than comparator validity: this host has no measured bit-related bottleneck, and one rate on one selected parent cannot establish general communication efficiency. Root should purchase it for conditional understanding of controller preservation, with the substantial support cost visible. I nevertheless favor this bounded purchase: it can produce a useful ordinary capability, a task-aware increment, or a meaningful finite failure without reopening joint policy training. It should not displace a more valuable competing project merely because its native execution is cheap.

**MATERIAL_DISSENT: no — I support the proposed complete comparison with the clarifications above, unchanged fit/native price, and no authorization for execution implied by this review.**
```

<a id="b07-selection-disposition"></a>
### DM response, fixed reading conventions and substantive return

I accept the recommendation and both clarifications. The changed judgment is that
the available paid data and a competent ordinary codebook support a coherent
frozen-controller preservation study; earlier content-learning failures do not
already answer it. No empirical compression gain has been observed. The leading
ordinary explanation remains sufficient geometric quantization; off-policy teacher
histories and one selected parent remain the principal scientific limitations.
The lack of a measured bit-priced bottleneck and the 8–14 support-hour price remain
serious allocation reservations. Root receives this as one complete candidate
purchase, not a duty to implement a favorable review. There is no material dissent
to self-clear and no separate Pro question has distinct unresolved value here.

The immutable target bank remains the old stored composed means. On the selected
remote runtime, exact identity applies to checkpoint/data hashes, input order,
configuration, packet reconstruction and unchanged frozen weights. The already
priced one-pass uncompressed D replay reports mean/density differences and its
Gaussian KL against that fixed bank alongside the O/L losses. **Do not subtract
the replay KL from codec KL**: those squared losses do not decompose additively.
Nonzero roundoff alone does not fail this comparison or regenerate teacher labels.
Changed bindings/forward semantics or nonfinite outputs do fail their dependent
claim. A substantial discrepancy remains a disclosed limitation on preservation
of the old numerical controller and on the offline objective; all eight native
programs still execute on the same runtime. No changed epsilon, new target bank,
source repair plus retry, or extra replay is authorized by a failed observation.

Fix individual-service reading before any new data: for each user and episode,
`age[-1]=0`; after tick t, `age[t]=0` if connected at t and otherwise
`age[t]=age[t-1]+1`. Mean waiting age averages these **post-tick** values over all
256 observed ticks, then reports both per-user and per-world summaries. Total
service counts true connected bits. Longest gap is the longest consecutive false
run within the 256 observations, including prefix and suffix runs; all-served is0
and never-served is256. Mark both boundary runs as censored by the observation
window; do not assert any unobserved prehistory or continuation. Preserve the
same-user mapping within each common world and report signed differences, min
served ticks and max longest gap across users. These metrics do not enter training,
codec selection or the actor's information set.

Retention remains an observed paired loss distribution with conditional codec-seed
and fixed-program world uncertainty. The earlier phrases “useful retention,”
“substantially lose” and “worse individual service” describe investment judgments,
not hidden numeric margins, equivalence tests or a rule that every user/world must
improve. Native J/service and individual-tail tradeoffs are reported together; a
single adverse user cannot be turned into a retrospective unanimity requirement.
Any future adoption preference or confirmation margin is a separate prospective
choice, not selected from this panel.

If selected, the engineering scope must enforce literal hard codeword lookup in
the learned codec's forward path, including fitting, rather than assume floating
point soft-plus-detached cancellation reproduces the transmitted codeword exactly.
Its surrogate backward is explicitly biased. Input differentiation through the
frozen recurrent base must preserve forward semantics and all weight bytes; the
new direction-local B07 adapter should not modify frozen B05/B06 contracts. Own
pending status is maintained from the sender's known send tick and send-time public
regime/deterministic delay, without an unpriced ACK. These correctness requirements
add no result-bearing pilot, metric candidate, fit, native episode or claim.

The complete proposed price is unchanged: **12 codec fits,720 Adam steps,0 policy/
receiver/critic/predictor fits,65,536 new native steps,4,505,600 actor-row presentations,
475,004,928 six-coordinate center comparisons**, full reader and individual-service
reading, with no new label acquisition. Prospective node is `wsl_4070`, CPU FP32,
one Torch/inter-op/BLAS thread;0 GPU. Planning ranges remain0.5–2 CPUh/0.5–2.5 occupied
worker hours plus8–14 support agent-hours,0.1–0.2 GiB durable output and roughly2 GiB
additional peak disk/1 GiB process RSS. These are uncertain prices, not measured
caps or proof of remote runtime health. Exact-input publication, proportionate
engineering checks/review and fresh actual-node admission apply only if purchased.

At this design boundary there is **no accepted worker, observer, Pro operation,
code implementation or generated bulk/scratch** to drain or delete. The bounded
critic has returned and is terminal. Existing canonical evidence remains in place;
no new duplicate retention was created. Actual deleted targets: none. Net disk
bytes reclaimed: **0**. There is no cleanup tool blocker. Existing source/data
links, work/byte arithmetic and the documentation diff were self-checked; no model,
physical or training check was substituted for the authorized source-only work.
Next action is Root's cross-question purchase/no-purchase choice on this exact
complete package. No result execution follows merely from review or publication.

Original advice payload is11,458 UTF-8 bytes (excluding its fence/newline), SHA256
`7fdcefcd55e8e1458c68d9930614761c3457d9c068fcffa596b8c55d35562619`.
Design/source/review support occupied roughly41 minutes of this DM's turn from
14:53 to15:34 UTC; the critic's accepted-to-return span was14m42s and overlapped it.
These are session elapsed times, not measured inference CPU or additive worker
hours. Tool/support CPU was not comprehensively metered and remains unknown.

<a id="b07-selected-contract-l0"></a>
### Root selection and L0 — 2026-10-02 UTC

After reading the complete published design and original review at `1ec302ab4`,
Root selected **one complete B07 package** through this same native child and
published the selection at `17a18bb4690af65b4352c07a4ae82145e53d9653`. It accepted
the declared remote runtime/throughput/RSS uncertainty and the support price for
conditional knowledge of ordinary message sufficiency and a task-aware increment.
This supersedes the earlier design-only restriction. There is no new teacher bank,
policy/receiver fit, no-message control, alphabet sweep or preliminary health/pilot
purchase. All fixed fits/native/reader exposure and the preceding runtime-binding/
retention clarifications remain unchanged. A real technical failure preserves
actual exposure and missingness; it grants no automatic retry, changed target/
tolerance or replacement fit. Root owns the cross-question allocation; the DM now
owns implementation through result reading, publication and measured cleanup.

**Deliverable.** Implement the finite-message retrofit as one direction-local B07
package: lawful byte codec and delayed cache; differentiable frozen D receiver;
fixed old-bank fitting/development/replay; complete native comparison; independent
full trace/model/physical/individual-service reader; compact counters/resources and
artifact identities. New entrypoints live in
`experiments/candidates/uav_message_content/b07/`; tests mirror that directory.
Use ordinary imports from retained B05/B06/CADC/host helpers where applicable,
without modifying frozen contracts or shared core. The Implementer owns these new
implementation/test paths only in `/home/fires/hmasd-wsl` on shared `main`; the DM
keeps NOTES, RESEARCH, run records, launch/collection, review and the Git index.
No helper commit, branch/index mutation, result launch, Pro or child delegation.
Other sessions own their edits; preserve them.

**Protected semantics.** D19702 and B19451 weights and declared asset hashes;
six lawful source fields `[0,1,2,3,4,6]`;256 shared rows;3-byte compressed packet
including header plus2-byte public beacon; known-zero reconstruction; no extra
uplink/ACK or sender history; arrival-before-inference and1/5-tick delayed RR;
current GOOD/BAD and send-time delay; zero self-cache; five separate3-vector motion
draws per tick; own native histories; exact selected old-data split/seeds and fresh
world tuples; all frozen parameter bytes; no critic/planner/Q calls. Full D/B use
lossless six-FP32 payload plus the same metadata/beacon bill. Actual hard bytes
travel through the delayed queue and the decoder runs on delivery, so no full
precision payload is silently supplied to a compressed receiver.

Fitting uses population SD (`ddof=0`) for the inverse-SD metric, scale
`1/max(SD,.05)`, and squared distance `sum(((x-codeword)*scale)^2)`. Initialize
each ordinary metric candidate with its named codec seed using an isolated RNG;
fix20-epoch minibatch shuffling from a separate seed `codec_seed+10000`, with the
same episode ordering for both metric candidates in each seed. Temperature is
`.25*(.025/.25)**(epoch/19)`, epoch0..19. Exact nearest ties choose lowest index;
zero-mass k-means++ fallback chooses the first as-yet-unselected source row.
These deterministic implementation details spend no new candidates or outcomes.
Task-aware hard lookup uses a soft reconstruction derivative as declared, without
turning numerical soft/hard cancellation into a different forward message. Base,
GRU, residual and log-std all permit input gradients while requiring no parameter
gradients/updates. The dataset carries teacher physical/previous-action histories;
only received values and recomputed recurrent memory change in offline fitting.

**Checks.** Focused synthetic fixtures verify byte/header boundaries, deterministic
nearest ties/empty clusters, packet delay/arrival/self-cache/age/pending/censoring,
hard forward equality and an independent surrogate backward, input gradients
through frozen base/GRU and zero frozen-parameter movement, complete recurrent
state reset, isolated initialization/shuffle/motion RNG, fixed split/fit/update/
row counters, mean-gap boundary conventions, parser and admission-before-effects,
artifact identities and strict malformed-input failure. A mocked-admission bounded
synthetic end-to-end test may cover runner/reader wiring; it is engineering work,
not a scientific health/proxy gate and must be separately counted. All generated
check files use pytest-owned `temp/` scratch. Use the configured local scientific
interpreter for these checks, with no installation. Do not add paid-data scoring,
fresh native pilots or a real fit to checks. Independent engineering review follows
the diff and actual checks, focusing on numerics, delayed causality, RNG and reading.

**Budget/stop and outputs.** The selected result package remains exactly12 codec
fits/720 Adam updates,65,536 native steps plus already-priced development, binding
replay and full reader. Entry must call `require_admission` before output creation,
checkpoint loading/model construction or other scientific effects; launch SHA must
match admission. Expose source SHA and input paths/hashes through explicit argparse;
fixed scientific dimensions are not free sweep flags. Record phase/cell progress,
started/completed fits/updates/forward rows/native calls, complete process CPU/wall/
RSS and byte ledgers, and preserve partial output on failure. No resumption that
repeats a started fit or accepted native effect is built in. A semantics or price
conflict returns to DM before dependent work. The DM accepts the diff, publishes
exact inputs, stages only declared remote inputs and admits the actual node; the
Implementer supplies code/check evidence only. Keep compact summary/reading and
failed/adverse facts; raw trajectories/dictionaries have explicit canonical paths,
sizes and SHA256 rather than bulk Git additions.

The selected scope and compact input manifest were published at
`7cc04b370cc3d60e145c8f011e87b372f512f1fc`. Manifest
`runs/uav_message_content/b07_codec_a01/input-manifest.json` is84,584 B, SHA256
`71195b30edd1b2ccf2e46098ac3371d35aa99739804ff94fce925e0ef095937e`.
It embeds original episode/seed/innovation/byte bindings without requiring remote
access to the old local provenance paths. Declared D checkpoint and32 raw files
are now staged at `wsl_4070:/home/wu/hmasd-inputs/uav_message_content/b07_codec_a01/D/`:
33 files,9,629,244 logical B/9,691,136 allocated B, all hashes read back correctly;
canonical remote B19451 also rehashed correctly. Staging cost4.738s local wall/.338s
local child CPU; remote transfer/hash CPU was not separately metered. This is input
staging, not a scientific launch or runtime-health result. The exact temporary
staging target is owned by B07 and remains a live selected input until terminal
collection; no other direction's files or sparse selection changed.

Bounded registered Implementer `/root/dm_message_budget/b07_codec_implementer`
owns only the new B07 implementation/tests under the scope above. DM retains
notebook/index/source-publication and result-operation ownership. Its assignment
permits synthetic correctness checks but no paid-data scoring or result execution.

The runner's explicit absolute-manifest interface also needs the compact published
manifest at the staging root; its84,584 bytes were copied and rehashed in1.154s
local wall. Staging now contains **34 files/9,713,828 logical B/9,789,440 allocated
tree B including directories**. This adds only declared compact metadata, not
another checkpoint/raw-data copy. Actual runtime and result exposure remain zero.

DM's initial source review caught a manifest `development`/`dev` spelling mismatch
and the need to accept the launcher-created output directory while refusing prior
scientific products. It also required ordinary dictionary displacement to use its
actual k-means++ initialization, and child CPU/RSS to be separately reported. These
are pre-execution corrections within the selected scope, not failed fits or retries;
the Implementer is adding focused synthetic coverage before independent review.

The stable Implementer return contains17 new B07 files/1,743 lines including tests
and usage. Final local synthetic command was one-thread
`/home/fires/.venvs/hmasd-linux-cpu/bin/python -m pytest -q tests/experiments/candidates/uav_message_content/b07`
with bytecode disabled and `/usr/bin/time -v`: **37 passed**, pytest4.88s;
outer6.64s wall/5.88s CPU/305,904 KiB lifetime peak RSS. Across its three invocations:
19.52s wall/17.56s CPU. These included **three synthetic ordinary fits and three
short-history learned fitting checks with360 Adam updates**, plus synthetic
collector/reader and mocked package wiring. These engineering fitting attempts are
paid separately from the12 selected real-bank codec fits; they are not extra
scientific replicates or a successful runtime/host pilot. No real input checkpoint
was loaded, no paid-bank actor scoring occurred and no actual native host ran.
Pytest removed its owned scratch. Actual child wall remains explicitly unmeasured.

The first synthetic suite independently reproduced a1-ULP centroid reconstruction
error: the original FP32 sum divided by an int64 array promotes to FP64 before
adding position and assigning FP32, whereas division by a Python integer can retain
FP32. The reader now follows the actual mixed-dtype source construction; exact
packet checks were retained. Its neural replay also reconstructs the receiver
from frozen tensors/base GRU independently of the B07 forward adapter. The named
read-only Engineering Reviewer `/root/dm_message_budget/b07_codec_engineering_review`
is inspecting this stable implementation and its checks; DM acceptance/publication
and the first result launch remain pending that review.

The independent Engineering Reviewer returned **no material finding and no repair
request** after checking the actual host/adapter consumers, hard-codeword forward
and surrogate backward, frozen input gradients/recurrent order, delayed byte queue,
pending and RNG witnesses, input/admission/failure identities, resource scopes and
the independent physical/neural/service reader. It independently reran the same
synthetic directory: **37 passed in4.86s**, outer5.72s wall/5.93s CPU/305,528 KiB
lifetime peak RSS, with pytest-owned scratch clean. Thus four total engineering
suite invocations cost25.24s wall/23.49s CPU and include **four synthetic ordinary
fits plus four short-history learned fits/480 Adam updates**. They add no real-bank
fit, scientific replicate, label acquisition or native host exposure.

DM acceptance follows reading the implementation and tests plus that independent
review. No further source change or redundant rerun is needed. Its residual limits
remain: full package wiring is mocked, fitting checks use short synthetic histories,
native-reader integration uses synthetic H256 D/B/compressed episodes, and the
actual checkpoint/data replay, full selected exposure, remote runtime and resource
estimates are not empirically exercised yet. The accepted code retains literal
byte decoding on delivery, exact frozen-parameter checks, all declared counters
and an explicitly non-resumable failure frontier. The next operation is the one
selected admitted B07 package after exact source publication; acceptance is neither
a scientific result nor an extra permission checkpoint.


<a id="b07-source-input-refusal"></a>
### B07 first source-input refusal and one corrected admission, 2026-10-02 UTC

Accepted implementation was published at `2d41535bde95c9c168fc1f63113855363c35f646`.
The remote supervisor accepted task `uav-message-b07-2d41535bd-a01` at16:22:14 UTC;
its launcher exited4 at16:22:24 UTC. Exact refusal:
`absolute author input is absent from published snapshot: /home/wu/projects/HMASD/runs/uav_message_content/b02_preserved_scalar/19451/B/final.pt`.
The launcher maps absolute inputs beneath the author root into the immutable source
snapshot, whereas this retained B checkpoint is canonical untracked bulk. This was
a source-input resolution error after snapshot creation and **before native claim,
admission, runner, model forward, codec fit, native step or reader step**. The remote
native output directory was absent; native status refused that absent handle.
Supervisor status was terminal failed/exit4, tmux inactive and recorded PID1346340
absent. Complete original wrapper/log/status/source identity and refusal frontier
are in `runs/uav_message_content/b07_codec_a01/launch-refusal.json`. Supervisor
wall was10s; launcher/remote preparation CPU was unmeasured, not zero. The original
request is retained and will not be resent or represented as a scientific result.

The remote canonical author checkout could not fast-forward because its control
files were already dirty; no shared reset/stash/checkout or repair was attempted.
Its compute configuration, launcher and source-snapshot working bytes matched the
published versions. Under its shared writer lock, only this direction's stale
reserve row was mechanically updated to its published active/native-child row;
other dirty rows and owner-pause controls were preserved. The source commit was
fetched and available. A pre-existing remote Git GC warning about another bad tree
was left untouched. None of this established scientific runtime health.

Root explicitly selected one corrected, prospectively named request for the same
scientific package after reading the refusal: stage only the identical463,357 B
B19451 checkpoint outside the author root, correct its manifest/CLI location,
publish the new exact source, reuse applicable reviews and perform targeted
path/byte/binding checks. This authority covers this identified source-input error;
it does not authorize an automatic retry after an actual effect failure, another
health/model/native probe, new labels or a changed study. D,32 paid raw trajectories,
fixed teacher bytes,12 codec fits/720 updates,65,536 native steps and the complete
reader remain unchanged. The new output tag is `b07_codec_a02`.

Before cleanup, the source-snapshot collector's explicit `--unclaimed-source`
preview and apply found exact snapshot `7ce384456e3d488986b07d1611036535` eligible,
clean, unclaimed and unconsumed, with source2d41535bd durably reachable. A read-only
privileged process scan was included. Removal of
`wsl_4070:/home/wu/projects/HMASD/.git/hmasd-launch-sources/7ce384456e3d488986b07d1611036535`
was verified both on disk and in Git worktree registration. Allocated usage fell
from1,827,467,264 to0 B: **1,827,467,264 net allocated bytes reclaimed**. The exact
record is `runs/uav_message_content/b07_codec_a01/source-cleanup.json`; there is no
cleanup blocker. Required refusal records, original manifest and live selected
inputs remain; no other snapshot or direction was touched.

B19451 now additionally resides at
`/home/wu/hmasd-inputs/uav_message_content/b07_codec_a01/B/final.pt`, with original
SHA256 `34871c49874ec716c21438581facfaeca8a25930304a39eb26e001fb2b259da2` and463,357 B
verified before and after copy. The corrected compact manifest is
`runs/uav_message_content/b07_codec_a02/input-manifest.json`,84,565 B, SHA256
`f2e50cfcbd96d35003fef37d8260379f4304eadba64e467a6cdf8f1a30f13d40`, staged as
`/home/wu/hmasd-inputs/uav_message_content/b07_codec_a01/input-manifest-a02.json`.
Only `parent_b.path` and `staged_payload_bytes` differ from the preserved original
manifest. All34 bound checkpoint/raw inputs were checked as absolute external
paths with original sizes/hashes; total10,092,601 B. No model was loaded. Complete
staging is36 files/10,261,750 logical B/10,346,496 allocated tree B including both
small request manifests. B copy/readback took.443s local call wall (.0007s measured
remote copy/hash wall); corrected-manifest transfer and all input hashes took.952s
local call wall. Remote CPU was not independently metered. Detailed identities
and targeted checks are in `runs/uav_message_content/b07_codec_a02/input-staging.json`.

No executable source or scientific premise changed, so the original independent
scientific and engineering reviews are reused without a redundant test suite.
The corrected request receives fresh actual-node admission once, after publication.
An accepted launch is not the read-result boundary; the same-handle observer must
remain active through terminal collection and full interpretation. A first actual
effect failure preserves partial counters/evidence and returns the unresolved
boundary without another automatic run.
