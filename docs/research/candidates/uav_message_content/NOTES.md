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
