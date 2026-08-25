1. Competing benchmark framings
Framing A — Physical-capability service roster

Definition. The physical fleet remains eight UAV assets, but a UAV belongs to the service-active roster only while it can legally contribute communication service. Temporary failure and an accepted charging/queue commitment can therefore produce service LEAVE; repair or charging completion can produce REJOIN.

A service lifecycle transition is genuine only when all of the following occur:

the UAV contributes no communication action or communication link while absent;

its service-policy row is absent rather than merely multiplied by zero after inference;

the lifecycle owner of recurrent state is explicitly frozen, restored, created, or deleted;

inactive rows generate no policy likelihood or PPO loss;

unaffected survivors preserve their states exactly.

A Boolean availability feature without these ownership consequences is only masking.

Capability probed. Correct active-set probability, lifecycle-owned recurrence, survivor continuity, and post-rejoin service recovery.

Strongest simpler reduction. A fixed eight-slot recurrent policy with the correct current availability mask, no inactive action likelihood, frozen hidden state during temporary absence, restored state at rejoin, and zero initialization for a genuinely new asset.

Principal confound. For a fixed physical fleet, that reduction may be functionally equivalent to an open-roster implementation. The benchmark must permit the conclusion that dynamic lifecycle machinery adds no task-level value.

This is the primary retained framing.

Framing B — Mission-admission or reserve roster

Definition. A temporary demand burst activates reserve UAVs or assigns selected UAVs to a surge-service cohort.

Capability probed. Dynamic recruitment and task-specific service assignment.

Strongest simpler reduction. A fixed-agent controller with an active_for_burst flag or a standby action.

Principal confound. If the environment selects which UAVs enter the burst cohort, the desired assignment has effectively been supplied. If the policy selects the cohort, “membership” may be only a renamed action.

This framing is not adopted for the burst-only source. Burst-only will keep the service roster constant. It will test rapid spatial reallocation, not dynamic membership.

Framing C — Effect-defined roster

Definition. A UAV is declared service-active when its realized communication contribution, connection count, or delivered traffic is nonzero.

Capability probed. Sparse allocation of useful service contributors.

Strongest simpler reduction. Thresholding ordinary continuous actions or connection outcomes.

Principal confound. Membership becomes a post-treatment variable derived from the behavior or outcome being evaluated. It leaks success semantics and can convert poor placement into an apparent LEAVE.

This framing is rejected as decorative.

Framing D — Anonymous lifecycle replacement

Definition. A service lifecycle, rather than a physical tensor slot, owns recurrence. Temporary absence restores the same lifecycle; terminal loss deletes it; a later service entrant receives a fresh lifecycle even when the physical fleet uses reusable storage.

Capability probed. State ownership under anonymous re-entry, cold start, and survivor-preserving roster edits.

Strongest simpler reduction. Stable physical slots with correctly implemented reset/freeze/restore semantics.

Principal confound. Stable physical-slot identity is legitimate information in a fixed fleet. Removing it only from the baseline would manufacture an open-roster advantage.

This framing is retained as a lifecycle audit, but the fixed-mask baseline is allowed stable physical slots for state routing. Slot identity itself may not be embedded as an actor feature.

Repository boundary

The current Scenario-7 environment does not yet instantiate any of these scientific roster definitions. It retains all UAVs in possible_agents; the adapter constructs fixed-size tensors from that list. The current environment treats failure or battery below the service cutoff as unavailable, but not charging itself, and its returned action mask remains all ones.

2. Exact minimal source ladder
Common service-active predicate

For the ladder, define:

A
i
svc
	​

(t)=E
i
phys
	​

(t)∧¬L
i
terminal
	​

(t)∧¬L
i
temporary
	​

(t)∧¬C
i
inactive
	​

(t)∧(b
i
	​

(t)>θ
cutoff
	​

),

where the battery term is identically true in battery-disabled sources.

An inactive service lifecycle:

emits no communication or motion-policy action;

appears in no actor active set;

produces no action log probability or actor loss;

remains available to the centralized critic only through explicitly permitted current physical state;

freezes service-policy recurrence when the absence is temporary;

deletes service-policy state when the absence is terminal.

The physical asset may continue evolving while its service lifecycle is absent. Physical state and policy lifecycle are separate ownership domains.

Ordered ladder

UAV_TEMPORARY_SERVICE_LOSS_G1 — selected first

UAV_CHARGE_ROTATION_ROSTER_G2

UAV_LOCALIZED_DEMAND_BURST_G3

UAV_COMPOSED_SERVICE_ROSTER_G4

The loss source comes first because it is the smallest source with an unambiguous, exogenous service LEAVE/REJOIN and no energy, charger, queue, or new demand-process confound. Charge comes second because physical energy evolves while the service lifecycle is absent. Burst comes third because it is a load source, not by itself a membership source. Composition comes last.

Source 1 — UAV_TEMPORARY_SERVICE_LOSS_G1
Base task

Use the unchanged S7-S1 physical environment and external reward:

physical UAVs        8
users                30
ground BS            1
episode length       500
ordinary QoS demand  1 Mbps per user
QoS target ratio     0.90
battery/charging     disabled

These are the registered S7-S1 facts.

Disturbance law

Training and IID evaluation

Exactly one recoverable temporary loss per episode.

Owner is uniform over the eight physical UAVs.

Onset:

O∼DiscreteUniform{120,…,240}.

Duration:

D∼DiscreteUniform{30,…,60}.

Owner, onset, duration, user motion, channel randomness, policy randomness, and initial physical state are mutually independent.

Held-out LATE_LONG_SINGLE

One owner, uniform over eight.

O∼DiscreteUniform{280,…,330},D∼DiscreteUniform{70,…,100}.

Held-out OVERLAPPING_DOUBLE

Two distinct owners sampled uniformly without replacement.

O
1
	​

∼DiscreteUniform{140,…,200},
O
2
	​

=O
1
	​

+δ,δ∼DiscreteUniform{10,…,20},
D
1
	​

,D
2
	​

∼
iid
DiscreteUniform{50,…,80}.

At least six UAVs therefore remain service-active.

Lifecycle and physical state

During temporary loss:

service-active membership becomes false before the affected step’s policy action;

communication links are disabled;

position is held fixed with zero velocity;

battery is absent from this source;

recurrent policy state freezes;

no action, likelihood, reward ownership, or actor row is generated for the absent lifecycle.

At rejoin:

the same lifecycle and recurrent state are restored;

the current physical observation is refreshed;

the first new action is sampled only after restoration;

no future loss duration or schedule is revealed.

A temporary detachment and a recoverable failure are merged only in this source, because both have identical zero-motion, no-service, freeze/restore consequences. A terminal loss changes the claim because there is no restoration or post-rejoin continuity. It is excluded from G1 and cannot be inferred from it.

Information contract

Both learned arms receive the same current information:

active UAV local physical and communication observations;

active-set aggregate;

current service-active count;

current service mask for the fixed-slot arm;

ordinary current user and channel information already present in S7-S1.

Neither actor receives:

future owner, onset, duration, or rejoin time;

a desired replacement UAV;

future user motion or channel state;

lifecycle key or epoch as a feature;

external reward, success, or recovery status.

The critic may read the full current physical fleet state and current service mask, including absent assets, but not the future disturbance ledger.

Source 2 — UAV_CHARGE_ROTATION_ROSTER_G2
Base task

Use the unchanged S7-S3 physics, action support, charger contention, external reward, and safety costs:

physical UAVs             8
episode length            1500
battery capacity          160 Wh
charging stations         2
simultaneous slots        1 per station
charging power            1000 W
temporary failures        disabled

S7-S2/S3 already enable batteries and two single-capacity chargers, and the environment models motion energy, return margins, capture, queueing, charging, cutoff and depletion.

Initial-energy law

Training and IID

Each episode randomly permutes across physical UAVs:

(0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90).

Held-out LOW_ENERGY

Random permutation of:

(0.45,0.50,0.55,0.60,0.65,0.70,0.75,0.80).

Held-out SYNCHRONIZED_PRESSURE

Random permutation of:

(0.55,0.55,0.60,0.60,0.65,0.65,0.70,0.70).

Charging-station geometry follows the existing randomized service-anchored distribution. Station count, capacity, physical energy model, return thresholds and safety reward are unchanged.

Charge lifecycle

A UAV remains service-active during ordinary return transit. It enters service LEAVE at the first step on which either:

its dock request is active and it is within the charging capture radius, including queueing for a full station; or

its battery reaches the existing service-cutoff threshold.

While service-inactive:

the common deterministic docking/hold/charge physical mechanism applies identically to all learned arms;

position, battery, queue wait and charge state continue evolving;

service-policy recurrence freezes;

communication links and service actions are disabled.

A temporarily absent charge lifecycle rejoins automatically at the first post-charge step satisfying:

b
i
	​

≥0.80,

provided it is not failed or terminally depleted. Its recurrent state is restored.

A UAV depleted outside charging capture is a terminal service loss. A depleted UAV already captured or charging remains a temporary absence because physical recharge remains possible.

Observability

Actors may read only current:

battery ratio and return margin;

relative charging-station positions;

station occupancy and queue length;

dock request and current service-active status;

current communication and physical observations.

They may not read future energy use, charger arrivals, queue ordering, completion time, future station demand or a prescribed charging rotation.

The critic may read the full current battery, queue, charging and inactive physical states, but no future schedule.

Held-out claim

The source tests transport to lower-energy and more synchronized charger pressure, not changes to battery physics, station capacity, safety reward or charger count.

Source 3 — UAV_LOCALIZED_DEMAND_BURST_G3
Scientific classification

This source has a constant service roster of eight. It is retained because the user requested localized rapid coverage, but it cannot independently support a dynamic-membership claim.

Burst law

Training and IID

Exactly one burst.

Onset:

O∼DiscreteUniform{140,…,260}.

Duration:

D∼DiscreteUniform{40,…,80}.

Select one user uniformly as spatial center.

The affected set is that user and its seven nearest users: exactly eight users.

Demand multiplier:

M∈{1.5,2.0},P(M=1.5)=P(M=2.0)=0.5.

Held-out EARLY_LONG

Onset uniform 60..120;

duration uniform 90..120;

ten nearest users affected;

multiplier exactly 2.25.

Held-out REMOTE_STRONG

Center is uniform among users in the farthest spatial quartile from the ground BS;

onset uniform 180..260;

duration uniform 70..110;

ten nearest users affected;

multiplier exactly 2.50.

The current target rate for affected user u is:

q
u
	​

(t)=M⋅1 Mbps

during the burst and 1 Mbps otherwise.

Information

Actors receive current affected-user demand values through the same local user-observation channel used for positions and channel state. The critic may receive the full current demand vector. Neither receives:

future onset, duration, multiplier or center;

the desired UAV-to-user assignment;

a burst-success flag or future user trajectory.

Membership

All eight UAVs remain service-active. Repositioning is an ordinary action decision. Calling a UAV “joined to the burst” would be decorative and is prohibited.

Source 4 — UAV_COMPOSED_SERVICE_ROSTER_G4

Composition is eligible only after all three isolated sources are source-identifiable and access-positive.

The composed source independently samples:

one localized burst;

the charge-rotation process;

one recoverable temporary loss;

then conditions the ledger on at least 30 physical steps of overlap between the burst and at least one service absence. Held-out composition uses the stronger held-out burst, lower-energy profile, and overlapping two-loss profile.

Composition cannot rescue an inaccessible or non-identifiable isolated source.

Promotion additionally requires at least one of the two genuine membership sources—temporary loss or charging—to remain unresolved in favor of dynamic lifecycle ownership or to support it. If both support fixed-mask sufficiency, stop the dynamic-advantage ladder before composition. A composed robustness benchmark may still be useful operationally, but it would not be a justified dynamic-roster algorithm test.

3. Estimands and matched reductions
Common QoS quantity

The existing environment computes:

ρ
t
	​

=
N
users
	​

1
	​

u
∑
	​

clip(
q
u
	​

(t)
R
u
	​

(t)
	​

,0,1),

reported as qos_satisfaction_ratio. The current reward uses that task utility together with the existing return-risk, cutoff, depletion and graph-PBRS terms.

No source changes Scenario-7 safety physics or converts a diagnostic metric into intrinsic reward.

Event and recovery score

For an episode, let W be the union of disturbance/service-absence intervals and let R be the union of the first 60 physical steps following each recoverable rejoin or burst end. Overlap is counted once.

Define normalized target deficit:

d
t
	​

=
0.90
max(0,0.90−ρ
t
	​

)
	​

.

Define:

J
event
	​

=1−
∣W∪R∣
1
	​

t∈W∪R
∑
	​

d
t
	​

,

and ordinary-service retention:

Q
ordinary
	​

=
∣
W∪R
ˉ
∣
1
	​

t∈
/
W∪R
∑
	​

ρ
t
	​

.

For recoverable membership sources, define post-rejoin continuity:

J
rejoin
	​

=1−
∣R∣
1
	​

t∈R
∑
	​

d
t
	​

.

Recovery latency—the first time after rejoin at which five consecutive steps satisfy ρ
t
	​

≥0.90—is reported as a descriptive diagnostic. It does not add another branch gate because J
rejoin
	​

 already measures recovery-area loss.

Source-specific minimal metrics
Source	Conclusion-bearing quantities
Temporary loss	J_event, J_rejoin, Q_ordinary
Charging	J_event, J_rejoin, Q_ordinary, depletion/cutoff episode fraction and return-constraint safety
Burst	J_event, Q_ordinary; no lifecycle estimand
Composition	Same quantities as its constituent membership and burst sources
Learned arms
FIXED_MASK_REC

The strongest ordinary reduction:

fixed eight physical slots;

shared per-UAV parameters;

current service-availability mask;

exactly the same local information, active-set sum, log1p(active_count) coordinate and active-fraction autoregressive prefix as the open-roster arm;

no inactive action or actor loss;

hidden state frozen/restored for temporary absence;

hidden state deleted for terminal loss and zeroed for a genuinely new asset;

stable physical slots permitted for state routing but not embedded as actor features.

PREFIX_NORMALIZED_OPEN_ROSTER

The accepted G8 functional pattern:

actor processes service-active lifecycle rows only;

active-set sum;

log1p(active_count);

active-fraction action prefix;

lifecycle-owned recurrent state;

parameter shape independent of roster capacity.

The accepted synthetic evidence supports that algorithm only in its registered synthetic family and does not establish UAV advantage.

Matching requirements

The two learned arms must have:

identical actor-visible information;

identical critic-visible current information;

identical primitive action support;

exact trainable parameter count;

identical episode ledgers and disturbance realizations;

equal environment interactions;

equal actor and critic optimizer steps;

identical PPO, reward and checkpoint-selection rules;

paired initialization and evaluation randomness.

Only roster representation and lifecycle-state ownership may differ.

Constructive controls

Each source contains:

a constructive feasibility controller, allowed to read the complete disturbance ledger and current physical state, but receiving no training and serving only as a feasibility certificate;

a no-reallocation control, which preserves the pre-disturbance service layout or action target.

These controls are not learned comparators.

For source identification:

mean(J
constructive
	​

)≥0.90

and

LCB
95
	​

(J
constructive
	​

−J
no-reallocation
	​

)>0.10.

The first establishes reachability; the second establishes that the disturbance actually makes adaptation load-bearing.

Dynamic-lifecycle estimands

For the selected first source:

G
svc
	​

=E[J
open
	​

−J
mask
	​

],
G
rejoin
	​

=E[J
rejoin,open
	​

−J
rejoin,mask
	​

],
G
ordinary
	​

=E[Q
ordinary,open
	​

−Q
ordinary,mask
	​

].

Evidence for dynamic lifecycle ownership requires:

LCB
95
	​

(G
svc
	​

)>0.03,
LCB
95
	​

(G
rejoin
	​

)>0.02,

and

LCB
95
	​

(G
ordinary
	​

)≥−0.02.

The first two margins are strict; the ordinary-service noninferiority boundary passes at equality.

Evidence supporting the fixed-agent reduction

The fixed-agent reduction is supported for the source if it establishes access and:

UCB
95
	​

(G
svc
	​

)≤0.03

and

UCB
95
	​

(G
rejoin
	​

)≤0.02.

A dynamic implementation pass, slot-invariance test, or anonymous-key audit alone cannot override that result.

4. Access, gates and mutually exclusive outcomes
Access score

For arm a and evaluation cell c, define:

A
a,c
	​

=min(
0.80
J
a,c
	​

	​

,
0.90
Q
ordinary,a,c
	​

	​

).

The arm-level access statistic is the worst registered evaluation cell:

A
a
	​

=
c
min
	​

A
a,c
	​

.

Access is established when:

LCB
95
	​

(
a
max
	​

A
a
	​

)≥1.

Equality passes.

No access is established when:

UCB
95
	​

(
a
max
	​

A
a
	​

)<1.

The result is underpowered when the interval crosses 1.

Source-identifiability gates for the first source

Before reading learned access:

exact disturbance-law reproduction;

owner, onset and duration support;

no future-ledger leakage;

no inactive action or likelihood;

exact temporary hidden freeze and rejoin restore;

exact survivor continuity;

action and parameter matching;

constructive mean J≥0.90;

constructive-minus-no-reallocation LCB >0.10;

all recovery windows fully observed;

both held-out cells represented independently.

First-match result system
Priority	Result	Exact condition	Smallest scientific update
1	INVALID_UAV_TEMP_LOSS_G1	Any reward, probability, mask, lifecycle, RNG, replay, count, checkpoint, comparator-matching or provenance invariant fails	No scientific update. Repair only the defect under the frozen source.
2	SOURCE_NON_IDENTIFIABLE_UAV_TEMP_LOSS_G1	Any source law, feasibility, load-bearing, support or leakage predicate fails	Close this source definition. Infer neither access nor roster value.
3	NO_ACCESS_UAV_TEMP_LOSS_G1	Source valid and UCB(max
a
	​

A
a
	​

)<1	Close only this source–learner pair. Do not infer dynamic or mask superiority.
4	UNDERPOWERED_ACCESS_UAV_TEMP_LOSS_G1	Source valid and the access interval crosses 1	Close under the frozen budget. No extra seed or update rescue.
5	USABLE_MASK_SUFFICIENT_UAV_TEMP_LOSS_G1	Fixed-mask arm accesses; UCB(G_svc)<=0.03; UCB(G_rejoin)<=0.02	Support the correctly masked fixed-agent recurrent reduction for recoverable temporary loss. Do not generalize to charging, terminal loss or composition.
6	DYNAMIC_LIFECYCLE_SUPPORTED_UAV_TEMP_LOSS_G1	Open-roster accesses; both strict gain margins pass; ordinary-service noninferiority passes	Support a UAV-local dynamic lifecycle advantage for recoverable temporary loss only.
7	MIXED_ANOMALOUS_UAV_TEMP_LOSS_G1	Every other valid access-positive pattern	Preserve both explanations; close the source without threshold, budget or stratum rescue.

Branches stop at the first match.

Promotion rule

Invalid: repair only.

Non-identifiable, no-access or underpowered: close G1; charge and burst remain legal independent sources, but no composition is permitted.

Mask sufficient: proceed to charge because energy evolution may make fixed masking less sufficient; retain burst as a load source.

Dynamic lifecycle supported: proceed to charge to test whether the advantage survives physical state evolution during service absence.

Mixed: independent charge and burst sources remain legal, but no composition is permitted.

Composition requires:

all three isolated sources to be source-identifiable and access-positive;

burst reallocation access;

at least one genuine membership source not to have resolved confidently in favor of mask sufficiency.

A failed source is never rescued by changing its name, distribution, metric, threshold, budget, seed, reward or observation. This follows the project’s smallest-unit result semantics.

5. Protected versus implementation-only choices
Choice	Classification	Frozen value or bounded PM freedom
Physical fleet versus service-active roster	scientific_value	Eight physical assets; source-specific active predicate above
Temporary-loss onset, duration, owner and held-out shifts	scientific_value	Exact laws in Section 2
Burst location, size, duration and magnitude	scientific_value	Exact laws in Section 2
Initial-energy distributions and charging rejoin threshold	scientific_value	Exact multisets and 0.80 threshold
Temporary/terminal lifecycle distinction	scientific_value	Temporary freeze/restore; terminal delete; G1 excludes terminal loss
Inactive physical evolution	scientific_value	Loss: zero-motion hold; charge: battery/position/queue continue
Actor and critic information	scientific_value	Current information only; no future disturbance or desired assignment
Existing Scenario-7 physics and reward	scientific_value	Unchanged within each selected preset
QoS, event, recovery and guardrail formulas	scientific_value	Exact formulas above
Access and comparative margins	scientific_value	Exact boundaries above
Learned comparators and matching	scientific_value	Fixed-mask recurrent versus prefix-normalized open roster
Constructive and no-reallocation controls	scientific_value	Feasibility controls only, never learned comparators
Trainable parameter count	scientific_value	Exact equality across learned arms
Environment and optimizer exposure	scientific_value	Exact equality; scheduled action freezes totals below
Confidence procedure	scientific_value	95% hierarchical paired bootstrap, 10,000 resamples
File names and class layout	implementation_only	Any small active-line organization implementing the frozen source
Ragged tensor versus compact indexed storage	implementation_only	May vary if policy inputs, masks, probabilities and lifecycle semantics are exactly equivalent
Padding capacity	implementation_only	Any value at least eight; padding must be policy-inert
Telemetry and JSON layout	implementation_only	Must expose all registered predicates and terminal branch, format otherwise free
Checkpoint serialization layout	implementation_only	Format free; exact state/RNG/lifecycle continuation remains mandatory
Seed integers	implementation_only	PM chooses fresh disjoint namespaces; same paired seeds across arms, no train/evaluation reuse
Parallel worker topology	implementation_only	Must preserve exact exposure, RNG ownership and CPU/one-thread contract
Constructive-controller software method	implementation_only	May use deterministic planning or scripted layout search, but must obey unchanged physics and meet the frozen feasibility predicates
Proof-sized test organization	implementation_only	Smallest checks covering source law, masks, lifecycle continuity, matching and metric arithmetic

Exact seed integers, schemas and telemetry are not scientific because changing them within those bounds does not change the distribution, information, estimand, confidence procedure or branch.

6. One scheduled evidence action
Source and purpose
UAV_TEMPORARY_SERVICE_LOSS_G1

Purpose: Determine whether explicit active-lifecycle ownership improves recoverable temporary-loss service and post-rejoin continuity beyond the strongest correctly masked fixed-agent recurrent controller.

This is the smallest source because it creates a genuine service LEAVE/REJOIN while leaving energy, charging, queueing and demand processes unchanged.

Protected source contract

S7-S1 physics, eight physical UAVs, thirty users, 500 steps and existing external reward.

One recoverable temporary loss during train/IID.

Held-out late-long single loss and overlapping double loss.

Service-active rows only for open roster.

Correct active masks and no inactive likelihood for fixed slots.

Freeze/restore of the affected lifecycle and continuity of all survivors.

Current-only actor/critic information; no future event schedule.

No terminal-loss, charging, burst or composition claim.

Arms

FIXED_MASK_REC

PREFIX_NORMALIZED_OPEN_ROSTER

constructive feasibility controller, evaluation only

no-reallocation control, evaluation only

The two learned arms start from paired initialization and have equal trainable parameters, data, environment interactions and optimizer steps.

Formal exposure

Per learned arm and paired replicate:

paired replicates             3
parallel environments         16
episode / rollout length      500
updates                       200
environment transitions       1,600,000
PPO passes per update         4

Only the final registered checkpoint is conclusion-bearing; no best-checkpoint selection.

Evaluation per arm and replicate:

NO_DISTURBANCE

IID_SINGLE

LATE_LONG_SINGLE

OVERLAPPING_DOUBLE

Each is evaluated deterministically and stochastically with 128 episodes per cell.

Uncertainty uses 10,000 hierarchical paired-bootstrap resamples: replicate first, then whole paired episode IDs, preserving all arms and disturbance branches.

Primary estimands

A
a
	​

: worst-cell access statistic;

G
svc
	​

;

G
rejoin
	​

;

G
ordinary
	​

.

Access and first-match semantics

Use the exact seven-branch first-match system in Section 4. No lower-precedence gain is read before source validity and access.

Held-out claim boundary

A positive result supports only:

recoverable temporary communication-service loss in an eight-asset S7-S1-like fleet, including one unseen late/long loss profile and one unseen overlapping two-loss profile.

It does not support:

charging rotation;

terminal asset loss;

demand bursts;

composed disturbances;

learned variable skill lifetime;

sample-efficiency superiority;

arbitrary fleet size;

generic UAV deployment advantage.

Minimum completion evidence

A valid terminal source must contain:

exact disturbance and episode counts;

paired arm initialization and exposure;

exact inactive-row exclusion;

hidden freeze/restore and survivor continuity;

no-future-leakage audit;

action, parameter and optimizer matching;

constructive and no-reallocation controls;

deterministic and stochastic final evaluation;

registered bootstrap intervals;

exactly one first-match terminal result.

This recommendation consumes zero conclusion-bearing iterations until a valid formal result exists and does not authorize implementation or compute.

7. Concise Chinese user brief

首个建议源是：

UAV_TEMPORARY_SERVICE_LOSS_G1

选择它的原因是：临时失联能够最干净地制造真正的服务 LEAVE/REJOIN，而不同时引入电池、充电站、排队或新的需求过程。

这里必须区分两个集合：

物理机队：整个 episode 中始终存在的 8 架 UAV 资产；

服务活跃 roster：当前能够并被允许产生通信服务动作的 lifecycle。

失联 UAV 仍是物理资产，但失联期间：

不产生服务动作；

不进入 actor active set；

不产生 action likelihood；

recurrent state 冻结；

归队后恢复同一个 lifecycle。

最强普通解释不是一个故意做弱的 mask baseline，而是：

固定 8 个物理槽位、正确 availability mask、inactive row 无策略损失、临时离场 hidden 冻结并恢复的共享 recurrent MARL。

首轮只有当 open-roster 相对这个强基线同时改善扰动期服务和归队后连续性，且不损害普通时段 QoS，才能支持 dynamic lifecycle。若固定 mask 方法达到 access，且 open-roster 的增益上界不超过冻结 margin，则应接受“普通 fixed-agent recurrence + 正确 masks 已足够”。

其余扰动仍保留在梯子中：

充电轮换：测试服务 lifecycle 缺席期间，位置、电量、排队和充电仍继续演化；

局部需求 burst：测试快速覆盖重分配，但 roster 保持固定，不能单独证明动态 membership；

组合源：只有三个独立源均可识别且可访问后才允许进入，不能用来救援任何失败的独立源。

第一轮可以证明或反驳的，只是：

在 S7-S1 类固定物理机队上，recoverable temporary service loss 是否需要显式 dynamic lifecycle ownership，而不是正确实现的固定-agent mask。

它不能证明充电、burst、terminal loss、组合鲁棒性、任意规模或 learned skill lifetime。本审阅不授权代码、实验、计算、Git 或 successor。
