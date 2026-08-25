1. Selection and source identity

Select Option A.

Freeze the independent source as:

ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1
task = ANONYMOUS_CUED_DUTY_HOLD_G1

Option A is preferable for this source because it isolates the single unresolved causal edge—whether an event-held per-member state becomes a useful persistent control variable—without simultaneously introducing multi-owner allocation or complementary-coordination requirements. Option B remains a legal later source for C-COORD; it is not rejected.

Repository-bound invariants

The following are unchanged:

G0 remains permanently closed.

Arms remain OR, DUM, and EHC.

The sole treatment remains

primitive_logits=base_logits+W
z
	​

(mz).

The primary mechanism estimand remains

G=E[U
EHC
	​

−U
DUM
	​

].

OR remains the full ordinary-recurrent comparator.

Anonymous lifecycle ownership, active masks, JOIN/temporary LEAVE/REJOIN/terminal LEAVE, survivor continuity, probability, gradient, replay, checkpoint, and first-match semantics remain protected.

The corrected K/I_TV/C_total battery is read only after source access.

All algorithmic fields not explicitly changed below—network graph, mark dimension, event and mark density, detach boundaries, PPO objectives, optimizer definitions, recurrent packing, replay, checkpoint schema, deterministic/stochastic execution rules—carry forward unchanged from the accepted EHC package. They are not locally selectable.

No G0 checkpoint, model tensor, optimizer state, episode ledger, result, or seed is reused.

2. Environment, task state, transitions, and lifecycle distribution
Per-lifecycle task state

For each opaque lifecycle κ
i
	​

, the environment owns:

status                  ACTIVE | TEMPORARILY_ABSENT | TERMINAL
membership_epoch
duty_target g_i         {-1, +1}
duty_duration d_i       active primitive steps
duty_active_age
cue_active_age
segment_match_count
terminal_match_streak
segment_id

The policy runtime separately owns its protected recurrent state, commitment mark z
i
	​

, opportunity countdown q
i
	​

, and event segment state. Routing keys and epochs never enter actor or critic inputs.

Primitive actions

The primitive action support is:

0 -> thrust -1
1 -> neutral 0
2 -> thrust +1

For an active lifecycle:

m
i,t
	​

=1[a
i,t
	​

=g
i
	​

].

Neutral is never a match because g
i
	​

∈{−1,+1}.

Primitive actions retain the existing autoregressive probability factorization and are applied simultaneously after the recorded order has been sampled.

Duty-segment transition

At genuine JOIN and after each completed duty segment:

Draw an active-time duration d
i
	​

.

Draw an independent target g
i
	​

∼Rademacher.

Reset active age, match count, and terminal streak.

Emit a target cue for exactly the first two active primitive steps:

c
i
	​

=g
i
	​

.

After those two active steps:

c
i
	​

=0.

Duration remaining, future target, future membership, future opportunity, and segment success are never actor-visible.

At each active primitive transition:

Sample and apply the primitive action.

Update m
i,t
	​

, match count, and terminal match streak.

Advance duty active age by one.

Decrement q
i
	​

 by one.

When active age reaches d
i
	​

, finalize the uncensored segment and open the next segment at the next pre-action boundary.

A completed segment is successful iff both conditions hold:

d
i
	​

∑
t
	​

m
i,t
	​

	​

≥0.75

and

terminal match streak≥2.

Equality at 0.75 counts as success.

Opportunity process

This is the only source-specific event-schedule change:

Delta_q ~ Uniform({2,4,6}) active primitive steps

It is drawn from the dedicated opportunity RNG after forced CREATE, KEEP, or RENEW.

The opportunity process is:

independent of duty target, duty duration, reward, membership owner, policy action, and physical time;

identical in train, IID evaluation, and held-out evaluation;

frozen during temporary absence;

resumed on REJOIN;

evaluated before the next primitive action when q
i
	​

=0.

Target changes do not create an opportunity. Thus the mechanism cannot solve the task through a task-triggered scheduler.

Membership lifecycle

Horizon is exactly 80 physical steps with capacity 6.

Every episode has:

initial genuine JOIN at t=0;

one temporary LEAVE;

REJOIN of that lifecycle plus one genuine new JOIN at the same boundary;

one terminal LEAVE.

Temporary LEAVE freezes:

recurrent state;

z
i
	​

;

q
i
	​

;

duty target;

duty age;

cue age;

match count and streak.

REJOIN restores those values and increments the epoch. If q
i
	​

=0, its opportunity is handled before its next primitive action.

Terminal LEAVE censors the open duty segment, closes policy state under the existing terminal contract, and deletes lifecycle state after finalization. Episode end also right-censors open segments. Censored segments do not enter the completion denominator.

Unrelated active survivors remain continuous. These semantics preserve the project requirement that variable membership exercise actual within-episode JOIN/LEAVE/REJOIN rather than fixed-count masking.

3. Actor observations, critic observations, reward, utility, and normalization
Actor observation

Each active lifecycle receives exactly eight analytically normalized fields:

Index	Field
0	local cue value c
i
	​

∈{−1,0,+1}
1	local cue-present flag
2	local new-duty-segment flag
3	genuine-JOIN flag
4	REJOIN flag
5	log(1+N
t
	​

)/log7
6	active fraction whose cue is currently present
7	active fraction at a JOIN or REJOIN boundary

The actor does not receive:

physical time;

current target after the cue;

duty duration or remaining duration;

duty age;

match count or streak;

previous primitive action;

primitive-action run length;

previous reward;

lifecycle key or epoch;

future membership or opportunity;

task success or progress;

z
i
	​

 through ordinary observation channels.

For EHC, z
i
	​

 reaches primitive behavior only through the protected W
z
	​

(mz) treatment. DUM has the same event state and capacity with m=0.

The actor uses fixed analytic feature scaling only; there is no running observation normalizer.

Critic observation

The centralized critic is identical across all arms and does not read z. It receives active-only tokens containing:

current g
i
	​

;

normalized duty age;

normalized remaining duty steps;

cue age and cue-present flag;

current segment match fraction;

capped terminal streak;

JOIN and REJOIN flags.

Global critic fields contain:

t/80;

normalized active count;

cumulative tracking numerator and denominator;

cumulative completion numerator and denominator;

current structural membership-event indicators.

The critic does not receive future targets, future durations, future membership events, future opportunity times, policy RNG, routing identity, or post-action state.

External reward and terminal utility

Let:

R
e
	​

 be the total number of active lifecycle rows in episode e;

M
e
	​

 be the number of uncensored duty segments ending in episode e;

X
e
	​

 be the total number of matching active rows;

Y
e
	​

 be the number of successful uncensored segments.

Ledger construction requires M
e
	​

>0.

Define:

A
e
	​

=
R
e
	​

X
e
	​

	​

,B
e
	​

=
M
e
	​

Y
e
	​

	​

,

and terminal utility:

U
e
	​

=0.75A
e
	​

+0.25B
e
	​

.

Thus U
e
	​

∈[0,1].

The environment gives the exact dense decomposition:

r
t
	​

=0.75
R
e
	​

∑
i∈A
t
	​

	​

m
i,t
	​

	​

+0.25
M
e
	​

#{successful uncensored segments ending at t}
	​

.

Therefore:

t=0
∑
79
	​

r
t
	​

=U
e
	​

.

This is the external task return itself, not intrinsic reward and not an auxiliary shaping term. There are no additional bonuses, penalties, novelty terms, lifetime payments, switch costs, or task-specific intrinsic inputs. Access failures may not be concealed through intrinsic customization.

4. Train and held-out distributions, and why persistence is load-bearing
Episode pairing

Training and evaluation use sign-paired base ledgers.

Episodes 2b and 2b+1 share:

membership events;

lifecycle-key permutation;

duty durations;

opportunity ledgers;

autoregressive orders;

primitive random uniforms.

Every duty sign in the odd episode is the exact negation of its mate.

Training IDs are 0..3999, arranged as 2,000 base pairs. Each collection of 16 episodes contains eight complete pairs.

Every evaluation cell uses IDs 0..255, giving 128 complete base pairs.

Distribution table
Field	Train and IID evaluation	Held-out evaluation
Initial active count	exactly balanced between N
0
	​

=3,4	exactly balanced between N
0
	​

=2,5
Temporary LEAVE time	uniform integer 14..20	uniform integer 8..14
REJOIN/new-JOIN delay	uniform integer 14..18 after LEAVE	uniform integer 20..26 after LEAVE
Terminal-LEAVE delay	uniform integer 20..26 after REJOIN	uniform integer 24..30 after REJOIN
Roster trace	3→2→4→3 or 4→3→5→4	2→1→3→2 or 5→4→6→5
Duty duration	uniform over {6,10,14} active steps	uniform over {8,12,16} active steps
Duty target	independent Rademacher	independent Rademacher
Cue duration	two active steps	two active steps
Opportunity gap	uniform {2,4,6}	uniform {2,4,6}

Temporary-LEAVE and terminal-LEAVE owners are sampled uniformly from their legal active sets using the task-ledger stream. The new JOIN always receives a new opaque lifecycle.

Why prepositioning cannot solve the source

Before a new duty cue, the next target is independent of:

physical time;

roster state;

previous target;

prior action;

previous mark;

membership owner;

opportunity history.

Consequently, preselecting +1 or −1 before the cue has expected match probability 0.5.

The actor has no physical-time field, no duration field, and no future-shock signal. The membership schedule therefore cannot serve as a target calendar.

Why a one-step primitive-reactive policy is insufficient

After the two cue steps, the current actor observation contains no focal target information, no previous action, and no physical proxy for the target. Other members’ targets are independent.

For any no-history policy—even one using the full current active set and primitive autoregressive prefix—the sign-paired expected match after cue expiry is at most 0.5.

For the shortest duration d=6:

A
memoryless
	​

≤
d
2+
2
1
	​

(d−2)
	​

=
3
2
	​

.

At most one member of a sign pair can satisfy the terminal two-step and 75% completion requirements under the same post-cue no-history behavior, so:

B
memoryless
	​

≤
2
1
	​

.

Therefore:

U
memoryless
	​

≤0.75⋅
3
2
	​

+0.25⋅
2
1
	​

=0.625.

Longer durations make this bound stricter.

A one-bit persistent controller that stores the cue and emits its sign at every active step achieves:

A=B=U=1.

Thus persistence is externally load-bearing, while the task does not prejudge whether the useful persistent state should live in ordinary recurrence or the EHC mark.

5. Absolute access and source-identifiability floors

All source checks precede access. Access precedes G and the behavioral battery.

Structural and information-identifiability checks
Check	Frozen estimand and boundary
Full-information persistent oracle	Every IID and held-out control episode must have U=1 within absolute tolerance 10
−12
. Any lower value fails source identifiability.
History-free ceiling	Exact sign-paired no-history upper bound must be ≤0.625. Equality passes; any value >0.625 fails.
Reward identity	(\left
Roster profile balance	Every 256-episode evaluation cell has exactly 64 base pairs for each registered N
0
	​

 value.
Duration coverage	In each IID and held-out ledger profile, every registered duration has segment proportion ≥0.25. Equality passes.
Within-roster temporal heterogeneity	Every held-out base ledger has at least 16 physical steps with two active lifecycles whose remaining active durations differ by at least four.
Leave-spanning duty	Every held-out base ledger contains at least one duty segment that begins before temporary LEAVE and continues after REJOIN.
Segment support	Every held-out base ledger has at least six uncensored segment endings from at least three lifecycle instances.
Opportunity exposure	Across five held-out stochastic replicates: at least 1,000 non-CREATE opportunities and at least 250 lifecycles with at least two such opportunities. Equality passes.
Natural-action support	At least 128 eligible natural KEEP and 128 eligible natural RENEW rows in total, and at least 16 of each in every replicate. Equality passes.

Failure of any row produces source non-identifiability before access or mechanism interpretation.

Absolute access estimand

For arm a, define:

U
a
access
	​

=E[U
a
	​

∣held-out stochastic profile].

Use the registered hierarchical bootstrap described below.

The new absolute access floor is:

U
min
	​

=0.80.

This is a source-specific value. It is not inherited from or compared with the closed G0 0.78 floor.

Boundaries:

Confident no access

a
max
	​

UCB
95
	​

(U
a
access
	​

)<0.80.

Access underpowered

a
max
	​

LCB
95
	​

(U
a
access
	​

)<0.80≤
a
max
	​

UCB
95
	​

(U
a
access
	​

).

Access established

a
max
	​

LCB
95
	​

(U
a
access
	​

)≥0.80.

Equality at 0.80 establishes access.

The floor lies materially above the exact no-history ceiling 0.625 and below the persistent oracle value 1.

6. Formal budget, cells, bootstrap, seeds, and battery carry-forward
Training budget

For each of five paired replicates r=0..4 and each arm:

parallel environments       16
physical horizon            80
outer updates               250
training episodes           4,000
environment transitions     320,000
base optimizer steps        1,000
event optimizer steps       OR=0, DUM=1,000, EHC=1,000

Total formal training exposure is:

4,800,000 environment transitions
15 arm-replicate training cells

Every arm in a paired replicate completes collection on the same episode IDs before any arm updates.

The backend is the registered CPU interpreter, torch threads 1, width 16, with no fallback, mixed backend, or cross-backend resume. CPU is a resource condition rather than a treatment.

Policy evaluation

For every replicate and arm, evaluate only the final registered checkpoint in four cells:

IID deterministic;

IID stochastic;

held-out deterministic;

held-out stochastic.

Each cell has 256 episodes.

Thus:

5 replicates × 3 arms × 4 profiles = 60 policy cells
60 × 256 = 15,360 policy evaluation episodes

Additionally, for each replicate’s held-out ledger set, evaluate:

one full-information persistent-oracle control cell;

one exact history-free/null control cell.

That adds 10 control cells and 2,560 control episodes or exact solves. These controls do not train or enter G.

Hierarchical bootstrap

Use exactly 10,000 percentile bootstrap repetitions.

For each bootstrap repetition:

Resample the five paired replicate triples.

Within each selected replicate, resample the 128 base IDs.

Retain both sign mates.

Retain all OR/DUM/EHC arms, deterministic/stochastic profiles, lifecycle rows, opportunity rows, and CRN counterfactual branches belonging to that base ID.

No agent, event, segment, censored row, or forced continuation is independently resampled.

Seeds

For replicate r, add 1000*r to every replicate-specific seed:

Stream	Base seed
model/addition initialization	158058
training task ledger	168058
training AR order	178058
training primitive action	188058
training opportunity	190058
training event action	192058
training mark	194058
IID evaluation task	198058
held-out evaluation task	199058
evaluation AR order	179058
evaluation primitive action	189058
evaluation opportunity	191058
evaluation event action	193058
evaluation mark	195058

Fixed analysis seeds:

derangement/audit seed = 206058
bootstrap seed         = 208058

Each task-ledger master uses immutable stream IDs:

0 lifecycle-key permutation and owner selection
1 membership-event timing
2 duty durations
3 target signs

The odd sign mate is generated by deterministic negation, not another random stream.

Carry-forward of mechanism thresholds

After access, the existing mechanism thresholds carry forward unchanged:

Primary:

LCB
95
	​

(G)>0.10.

Confident link-null:

UCB
95
	​

(G)≤0.10.

Support:
at least 128 eligible natural KEEP and 128 eligible natural RENEW rows.

Lifetime realization:
at least two of K=1, K=2, K>=3 have

LCB
95
	​

(proportion)>0.10.

Executable mark dependence:

LCB
95
	​

(I
TV
	​

)>0.10.

Natural consequential KEEP:

LCB
95
	​

(C
total,KEEP
	​

)>0

and

mean(C
total,KEEP
	​

)≥0.02.

Natural consequential RENEW:

LCB
95
	​

(C
total,RENEW
	​

)>0

and

mean(C
total,RENEW
	​

)≥0.02.

C_timing and C_mark remain decomposition diagnostics without branch thresholds. Point-floor shortfall with a positive interval is underpowered, not confident failure. The confident C_total failure dual remains an upper bound at or below zero. These semantics were already reconciled and may not be reopened locally.

The only source-specific threshold changes are:

new structural and information-identifiability floors;

new access floor 0.80;

new per-replicate natural-action support quota of 16 per action stratum.

The G, K, I_TV, and C_total scientific thresholds are unchanged.

The secondary complete-algorithm estimand

V=E[U
EHC
	​

−U
OR
	​

]

is reported after access but has no G1 branch threshold.

7. Mutually exclusive first-match truth table
Priority	Result	Exact condition	Smallest scientific update
1	INVALID_OPERATIONAL_G1	Any protected environment, probability, gradient, RNG, replay, lifecycle, mask, counter, checkpoint, reference, backend, or finite-value invariant fails	No scientific update. Repair only the failed operational path under the identical source.
2	SOURCE_NON_IDENTIFIABLE_G1	Any structural oracle, history-free ceiling, reward identity, roster, duration, heterogeneity, segment, opportunity, or natural-support floor fails	Close this source definition. Do not infer access or EHC mechanism value.
3	NO_ACCESS_THIS_G1_SOURCE	All preceding checks pass and max
a
	​

UCB
95
	​

(U
a
access
	​

)<0.80	Close only this G1 benchmark–comparator pair. Preserve recurrence, base-policy, credit, benchmark, EHC, link-null, and coordination conjectures.
4	UNDERPOWERED_ACCESS_G1	max
a
	​

LCB
95
	​

<0.80≤max
a
	​

UCB
95
	​

	Close under the frozen budget. Do not add seeds or updates. Mechanism remains unidentified.
5	COMMITMENT_SUPPORTED_G1	Access established; LCB(G)>0.10; K, I
TV
	​

, and both complete C
total
	​

 gates pass	Support the EHC mechanism-to-behavior-to-held-out-value link in this source only. Integration remains a separate decision.
6	REPRESENTATION_ONLY_G1	Access established; LCB(G)>0.10; at least one required interval condition confidently fails, including UCB(I
TV
	​

)≤0.10, insufficient possible K-bin passes, or either UCB(C
total
	​

)≤0	Reject the variable-lifetime behavioral interpretation for this EHC link in this source. A representation or optimization effect may remain.
7	ORDINARY_OR_CAPACITY_EXPLANATION_SUPPORTED_G1	Access established and UCB(G)≤0.10	Retire the load-bearing EHC link within this accessible matched source. Ordinary recurrence, stronger base-policy, credit, and coordination explanations remain legally distinct.
8	MIXED_UNDERPOWERED_G1	Every remaining valid numerical pattern, including point-floor shortfall without confident interval failure	Close this source unresolved. No threshold, budget, seed, or stratum rescue.

Branch evaluation stops at the first match.

Neither the structural persistent oracle nor the memoryless gap constitutes learned hierarchy, natural commitment, or variable-lifetime evidence. They establish only that the source is reachable and that persistent information is externally useful.

8. Prohibited rescues and concise Chinese user brief
Prohibited rescues

For this G1 source, do not change after observation:

task state or transition order;

cue length;

duty success definition;

train/IID/held-out roster, event-time, target, duration, or opportunity distributions;

actor or critic observations;

external reward or terminal utility;

normalization;

access floor or identifiability floors;

G or any battery threshold;

budget, replicate count, evaluation count, bootstrap unit, seed, or stream ownership;

OR/DUM/EHC architecture, capacity matching, W
z
	​

(mz), base PPO, event objective, critic, or ordinary comparator;

final-checkpoint rule;

CPU backend or thread count.

Do not:

reuse a G0 checkpoint or result;

add best-checkpoint selection;

add intrinsic reward or task shaping;

add identity, roles, task progress, success fields, previous reward, or future information;

add a duration action, learned hazard, terminate action, graph, team latent, communication module, posterior, or new credit estimator;

treat a source oracle, memoryless gap, K support, mark TV, or forced continuation alone as learned skill or variable-lifetime evidence;

rename and rerun a valid negative.

These prohibitions follow the durable rules that access failure is not repaired by customized intrinsic reward, valid negatives are not rescued by tuning, and integration requires natural use, intervention-sensitive sequential behavior, external value, and resistance to simpler explanations.

中文简报

本轮选择 Option A，冻结一个新的独立任务：

ANONYMOUS_CUED_DUTY_HOLD_G1

每个成员会在不可预测的时刻收到只持续两个 active step 的 ±1 duty cue，随后必须在 6–16 个 active step 的异质 duty 中持续执行正确动作。目标、剩余时长、上一步动作和 reward 都不进入 actor observation；临时离场冻结 duty、hidden、mark 和 opportunity clock，归队后继续。

这个任务的关键识别性质是：

完整 persistent oracle 的 U=1；

无历史 primitive-reactive policy 的严格上界为 U≤0.625；

新的 access floor 固定为 0.80；

因此任务确实需要持久信息，但不预设它必须来自 EHC，而不是普通 recurrence。

OR/DUM/EHC、W_z(m*z)、主 estimand G、匿名 lifecycle、first-match 顺序和完整行为电池全部保留。G、K、I_TV、C_total_KEEP、C_total_RENEW 的阈值不变。新 source 使用五个 paired replicates、每臂 320K transitions、60 个 policy evaluation cells 和全新的冻结 seeds。

这只是完整的科学 source contract：不授权代码、测试或正式计算，也不复活或修改已经关闭的 G0。
