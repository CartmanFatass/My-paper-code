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
