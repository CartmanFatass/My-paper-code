1. Decision and exact source contract

Decision: Select Option A — clean-infrastructure temporal-duty source

Source family:

ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1

Selected scientific object:

Test whether an event-held per-member commitment state can preserve a causally required multi-step duty under anonymous dynamic membership when the useful future behavior cannot be recovered by physical-time scheduling, primitive reaction, or current observable shortcuts.

This selection does not reuse G0. G0 remains closed as NO_ACCESS_THIS_BENCHMARK; it is not modified, renamed, or rescued.

The source preserves:

OR/DUM/EHC;

matched DUM/EHC capacity and exposure;

EHC-only treatment:

primitive_logits=base_logits+W
z
	​

(mz)

primary estimand:

G=U
EHC
	​

−U
DUM
	​


anonymous lifecycle semantics;

first-match operational validity → source identification → access → mechanism interpretation order.

1.1 State, action, transition, exogenous events, episode, lifecycle
Environment state

Each lifecycle i owns:

s
i
	​

=(x
i
	​

,g
i
	​

,τ
i
	​

,a
i
	​

,h
i
	​

)

where:

x
i
	​

: physical local state;

g
i
	​

: hidden duty requirement;

τ
i
	​

: active duty age;

a
i
	​

: accumulated duty performance;

h
i
	​

: policy recurrent state.

The environment owns:

membership status;

lifecycle epoch;

active mask;

temporary absence state;

terminal state.

The policy never receives identity.

Primitive action

Existing primitive action space remains:

a_i ∈ {-1,0,+1}

interpreted as local control.

The commitment does not directly execute actions. It only enters through:

π(a
i
	​

∣o
i
	​

,h
i
	​

,z
i
	​

)

via:

base_logits+W
z
	​

(mz)
Duty transition

At a genuine JOIN or completed duty segment:

Environment samples a hidden duty mode:

g
i
	​

∈{−1,+1}

Environment samples heterogeneous active duration:

T
i
	​

∈{6,10,14,18}

A short observation cue reveals the duty requirement.

After the cue expires:

g
i
	​

 remains hidden;

future duration remains hidden;

future membership remains hidden.

The lifecycle succeeds only if:

T
i
	​

correct active actions
	​

≥0.75

and:

final two active steps satisfy the duty

The task therefore requires maintaining information across a window, not merely reacting at the decision point.

Exogenous events

Events:

JOIN;

temporary LEAVE;

REJOIN;

terminal LEAVE.

Temporary LEAVE freezes:

recurrent state;

commitment state;

segment clock;

duty state.

REJOIN restores them.

Terminal LEAVE closes the lifecycle.

This preserves anonymous lifecycle ownership rather than fixed identity slots.

Why commitment is load-bearing

A primitive-reactive counterexample:

After the cue disappears, two worlds are observationally identical:

g
i
	​

=+1

and

g
i
	​

=−1

but require opposite actions.

Therefore any controller without retained memory has:

P(correct)=0.5

after cue removal.

A retained commitment can store:

z
i
	​

≈g
i
	​


and continue correct behavior.

This creates a causal dependency:

online cue
    ↓
held commitment
    ↓
future primitive action
    ↓
duty completion

The task is not solved by calendar prepositioning because:

cue time is randomized;

duty mode is independent;

duration is independent;

membership shocks are independent.

2. Plural conjectures and scopes
C-EHC — event-held commitment is load-bearing

Scope:

The mark z is a useful persistent state variable.

Expected evidence:

EHC improves over DUM;

intervention changes primitive behavior;

natural KEEP/RENEW consequences exist;

benefit transports to held-out duty distributions.

Strong contradiction:

Matched ordinary recurrence achieves identical held-out performance.

C-REC — ordinary recurrence is sufficient

Scope:

A recurrent primitive controller can store the same information internally.

Expected evidence:

OR matches EHC under information/capacity matching.

Strong contradiction:

EHC provides gains only after recurrent capacity is controlled.

C-BASE — shared base policy is the bottleneck

Scope:

The G0 failure came from common representation or policy capacity.

Expected evidence:

A stronger matched base accesses the source without changing the commitment mechanism.

Strong contradiction:

EHC succeeds with the same base under the new source.

C-BENCH — task design determines identifiability

Scope:

The previous benchmark failed because commitment was not causally required.

Expected evidence:

The new task separates:

persistent state;

timing;

recurrence;

primitive reaction.

Strong contradiction:

A simpler controller solves the same source.

These remain plural. No source definition selects a successor. The review principles require retaining structurally distinct explanations rather than converting one evidence action into a single route.

3. Derived consequences
Intervention consequence

If EHC is causal:

Deranging:

z
i
	​

→z
j
	​


while holding:

observation;

environment;

primitive RNG;

fixed should change action distributions.

Required:

I
TV
	​

>0

under the frozen battery.

Natural-policy consequence

The policy should naturally:

KEEP useful commitments;

RENEW when duty changes;

preserve commitments across temporary absence.

A successful forced intervention without natural usage is insufficient.

Skill semantics require:

intervention-sensitive executable behavior;

persistent effects;

transport beyond forced branches;

natural policy use.

Held-out consequence

The commitment should survive:

unseen duty durations;

unseen membership schedules;

unseen roster patterns.

Otherwise it may only memorize source statistics.

Why decorative commitment is excluded

Counterexample:

A random event head:

sample z

can produce:

nonzero action TV;

diverse lifetimes.

But it cannot produce:

causal duty completion;

held-out transport.

Therefore:

z diversity ≠ useful commitment
4. Counterexamples and retained lemmas
Ordinary-MARL reduction

Strongest reduction:

capacity-matched recurrent primitive controller

Requirements:

same actor-visible information;

same lifecycle state;

same training exposure;

same optimizer exposure.

It is the correct null because ordinary recurrence may encode persistence internally.

Shortcut counterexample: timing

If duty changes followed a predictable clock:

time→duty

then a scheduler solves the task without commitment.

Prevented by:

random cue timing;

random duration;

independent membership shocks.

Shortcut counterexample: observable hidden target leakage

If actor receives g
i
	​

 after the cue:

observation -> action

then no retention is needed.

Prevented by removing post-cue duty identity.

Shortcut counterexample: supplied executor

A manually assigned primitive controller proving completion would not establish EHC.

Only learned:

z→action

counts.

Retained G0 lemmas

Retain:

Access must precede mechanism interpretation.

OR remains mandatory comparator.

A no-access result only closes its benchmark pair.

Lifecycle semantics require anonymous membership and survivor continuity.

Diagnostic behavior does not equal learned skill.

G0 did not establish that EHC is false. It established only that the frozen source was inaccessible.

5. Estimands and mutually exclusive outcomes
Access estimand
U
a
	​

=E[U∣a]

Absolute access floor:

LCB
95
	​

(
a
max
	​

U
a
	​

)≥0.80

Equality passes.

If:

UCB
95
	​

<0.80

then:

NO_ACCESS_THIS_G1_SOURCE

Only this source closes.

Mechanism estimand

Primary:

G=U
EHC
	​

−U
DUM
	​


Pass:

LCB
95
	​

(G)>0.10

Fail:

UCB
95
	​

(G)≤0.10
Battery interpretation

After access only:

Support

Enough natural:

KEEP;

RENEW.

Lifetime

K-bin:

K=1,K=2,K≥3

with sufficient heterogeneous support.

Intervention
I
TV
	​


must pass.

Natural consequence

Both:

C
KEEP
	​


and:

C
RENEW
	​


must pass.

First-match outcomes
Branch	Meaning
INVALID	operational defect only
NON_IDENTIFIABLE	source definition invalid
NO_ACCESS	this source inaccessible
UNDERPOWERED	insufficient certainty
COMMITMENT_SUPPORTED	EHC link supported locally
REPRESENTATION_ONLY	mark affects representation without useful behavior
ORDINARY_EXPLANATION	EHC adds no value over matched null
MIXED	unresolved
6. One scheduled evidence action and reactivation conditions
Scheduled action

Define the bounded G1 source contract above.

This is:

not compute authorization;

not implementation approval;

not a unique successor.

It only freezes the scientific object.

Why this action

It separates:

C-EHC;

C-REC;

C-BASE;

C-BENCH.

The previous G0 could not because access failed before mechanism interpretation. Lower-precedence diagnostics cannot repair that.

Reactivation conditions
C-EHC

Reactivated by:

access-positive source;

positive G;

intervention;

natural transport;

held-out benefit.

C-REC

Reactivated by:

EHC and matched recurrence perform equivalently.

C-BASE

Reactivated by:

A stronger matched base succeeds without changing the mechanism.

C-BENCH

Reactivated by:

A new source again fails to separate:

persistence;

recurrence;

timing.

7. Concise Chinese user brief

本轮冻结的是一个独立 G1 科学源，不是 G0 修复。

选择：

Option A

原因：

它只改变任务，使“持续保存一个成员特定承诺”成为真正必要能力，同时复用匿名 membership/lifecycle 基础设施，避免一次引入多成员协同、通信和分配问题。

核心设计：

cue 短暂暴露 duty；

cue 消失后 target 隐藏；

成员必须在多个 active step 内保持正确行为；

membership shock 会改变 duty 持续过程；

普通无记忆 reactive policy 存在严格性能上界；

persistent commitment 可以突破该上界。

保持：

OR/DUM/EHC；

primitive_logits=base+W
z
	​

(mz)；

G=U
EHC
	​

−U
DUM
	​

；

anonymous lifecycle；

K / I
TV
	​

 / C
total
	​

 battery。

仍未解决：

EHC 是否优于 ordinary recurrence；

commitment 是否真正形成 variable lifetime；

是否存在更简单的 recurrent reduction。

本回复只冻结科学对象，不授权实现、不授权正式计算、不修改 G0。
