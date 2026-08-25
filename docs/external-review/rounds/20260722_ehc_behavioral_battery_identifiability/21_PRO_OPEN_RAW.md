1. Decision and scope

Decision: BATTERY_REQUIRES_MINIMAL_CORRECTION

Scope:

The implemented battery is close to identifying the intended causal object, but the current measurement contract has one unresolved identifiability gap: it can separate event-held commitment influence on primitive logits from some trivial controls, but it does not yet fully exclude several non-semantic explanations of a positive G = U_EHC - U_DUM.

Repository facts:

The primary estimand is fixed:

G=U
EHC
	​

−U
DUM
	​


with DUM and EHC differing only by:

primitive_logits=base_logits+W
z
	​

(m⋅z)

The battery deliberately combines:

natural KEEP/RENEW support;

opportunity-count bins;

lifecycle-stratified same-state primitive-action TV under deranged marks;

exact-snapshot KEEP/RENEW continuations;

joint COMMITMENT_SUPPORTED gate.

No formal result exists yet. Aborted runs are not scientific evidence.

The required correction is not a new experiment family or a new model. It is a measurement clarification:

The battery must distinguish:

event timing + mark affects behavior

from:

event timing/mark is merely correlated with useful recurrent context

without changing G, arms, budget, or comparator.

2. Plural live conjectures
Conjecture A — Genuine event-held commitment exists

Scope:

EHC learns:

event decision
   ↓
persistent mark z
   ↓
primitive behavior distribution
   ↓
external utility

Evidence needed:

positive G;

natural KEEP/RENEW usage;

action distribution changes under mark intervention;

continuation consequences remain after conditioning.

This is the intended mechanism.

Not established by:

positive utility alone;

mark entropy;

event-head learning.

Conjecture B — Representation-only coupling

Scope:

The mark influences logits, but only as an additional latent representation.

Possible mechanism:

z
↓
logit bias
↓
different action preference

without:

z
↓
persistent behavioral process
↓
better external capability

Prediction:

action TV passes;

intervention score passes;

but KEEP/RENEW continuations do not differ causally.

Conjecture C — Timing policy is the true contributor

Scope:

The event head learns useful renewal timing, while the mark is incidental.

Mechanism:

when to renew

matters, not:

what commitment was renewed

Prediction:

renewal timing improves utility;

randomizing marks may preserve performance.

Conjecture D — Context selection artifact

Scope:

Natural KEEP/RENEW rows are not exchangeable.

Example:

RENEW happens at easier states;

KEEP happens at stable states;

counterfactual continuation inherits this bias.

Prediction:

Natural advantages disappear under stricter matched-state continuation.

3. Derivation and intervention consequences
K support

Required:

enough natural KEEP and RENEW;

complete opportunity bins:

K==1
K==2
K>=3

What it identifies:

The battery is not measuring a rare-event artifact.

What it does not identify:

That commitments are useful.

A policy can have many renewals without meaningful semantics.

Action TV under deranged commitment mark

Measurement:

Same lifecycle state, same environment, replace:

z
i
	​

→z
π(i)
	​


and measure primitive action distribution change.

What it identifies:

The commitment mark reaches primitive behavior.

What it does not identify:

That the behavior is:

useful;

persistent;

causally responsible for utility.

A random latent can produce high TV.

KEEP continuation advantage

Natural KEEP rows:

Compare:

same snapshot
same RNG
same environment
KEEP continuation
vs
RENEW continuation

What it identifies:

Whether maintaining current commitment has external consequences.

Risk:

Selection bias.

A natural KEEP row is already a policy-selected state.

RENEW continuation advantage

Natural RENEW rows:

Tests whether renewal changes future utility.

Risk:

Renewal may simply occur at states where improvement is already likely.

Joint pass

The joint gate is stronger:

Need:

support;

action TV;

KEEP advantage;

RENEW advantage;

G.

However:

A joint pass still does not automatically identify:

learned variable lifetime

because the mark may be:

arbitrary latent;

useful representation;

timing-correlated state.

Natural and held-out consequences remain necessary.

4. Concrete counterexamples
Counterexample 1 — Random nondegenerate event head

Construction:

Event head samples:

KEEP/RENEW ~ Bernoulli(p)

with sufficient entropy.

Then:

K support passes;

natural renewal exists.

Failure:

No causal commitment semantics.

Expected battery behavior:

low G;

possible misleading usage statistics.

Counterexample 2 — Context-insensitive hazard

Construction:

Renew every fixed number of primitive steps:

q = constant

No state-dependent commitment.

Possible outcome:

lifetime CV passes;

renewal distribution looks heterogeneous if noise exists.

Failure:

No learned context-sensitive commitment.

Counterexample 3 — Useful mark, arbitrary timing

Construction:

Mark determines primitive behavior:

z=0 -> useful behavior A
z=1 -> useful behavior B

but event timing is random.

Then:

action TV passes;

utility may improve.

Failure:

The battery may attribute value to event-held commitment when the mark alone is useful.

Needed distinction:

mark value
vs
renewal decision value
Counterexample 4 — Selection/support bias

Natural RENEW states:

policy chooses renew only when state is favorable

Then:

RENEW continuation > KEEP continuation

without causal renewal effect.

The exact snapshot design reduces this risk but does not automatically remove policy-selection bias.

5. Retained lemmas and smallest refuted unit
Retained lemmas

The strongest surviving claims are:

If G>0, EHC has higher external utility than DUM under the matched treatment definition.

If action TV passes, commitment marks influence primitive action distributions.

If KEEP/RENEW continuation advantages pass, event choices correlate with different future external outcomes.

If all conditions pass together, the mechanism is stronger than a pure no-op event head.

Not yet retained

Cannot claim:

learned skills;

meaningful options;

variable lifetime abstraction;

hierarchy superiority;

cooperation mechanism.

Smallest refuted unit

The smallest possible failure unit is not the entire battery.

It is:

natural counterfactual advantage
conditioned on selected KEEP/RENEW rows

because it is the most vulnerable measurement component to selection bias.

A failure there does not refute event-held commitment.

It refutes that specific continuation estimator.

6. Minimal correction or freeze

Required correction:

Add one measurement clarification:

Freeze the causal interpretation of continuation advantages

The estimand should explicitly be:

effect of forcing KEEP/RENEW from matched natural decision states

not:

difference between naturally occurring KEEP and RENEW trajectories

Minimal scientific change:

For each selected KEEP/RENEW row:

preserve snapshot;

preserve RNG;

preserve environment;

preserve lifecycle;

preserve current mark distribution;

evaluate forced alternative.

The estimand remains:

G=U
EHC
	​

−U
DUM
	​


No change to:

arms;

reward;

seeds;

budget;

thresholds.

No implementation plan is implied.

7. One scheduled research action
Action: Behavioral battery causal audit

Comparator:

Frozen EHC/DUM checkpoints only.

No retraining.

Compare:

natural KEEP continuation;

forced KEEP continuation;

natural RENEW continuation;

forced RENEW continuation.

Estimand:

Separate:

Effect
timing
	​


from:

Effect
mark
	​


and from:

Effect
representation
	​


Branches:

Outcome A

Both timing and mark effects survive.

Interpretation:

Event-held commitment explanation strengthened.

Outcome B

Only timing survives.

Interpretation:

Renewal scheduling matters more than commitment semantics.

Outcome C

Only mark effect survives.

Interpretation:

Representation useful, event timing less important.

Outcome D

Neither survives.

Interpretation:

Positive signals were selection/context artifacts.

Prohibited rescues:

changing G;

adding intrinsic reward;

adding skill labels;

changing seeds;

changing PPO;

changing comparator.

Why this does not invalidate other explanations:

It only identifies the current mechanism boundary. It does not decide whether ordinary recurrent control or another abstraction is ultimately preferable.

8. Reactivation conditions
Genuine commitment explanation reactivation

Requires:

positive G;

intervention survives;

mark changes behavior;

held-out continuation benefit.

Representation-only explanation reactivation

Requires:

action TV positive;

utility benefit exists;

continuation effects absent.

Timing explanation reactivation

Requires:

utility gain remains after mark randomization;

renewal schedule alone explains benefit.

Ordinary-MARL explanation reactivation

Requires:

A matched direct recurrent controller reaches equivalent or better held-out utility.

Variable lifetime explanation reactivation

Requires:

learned, not sampled, lifetime variation;

robustness across unseen duration distributions;

benefit beyond recurrent memory.

9. Concise Chinese user brief

当前判断：

BATTERY_REQUIRES_MINIMAL_CORRECTION

原因：

EHC behavioral battery 的方向正确，它已经比单纯看 reward gain 强很多：

有 DUM 对照；

有 action intervention；

有 KEEP/RENEW continuation；

有自然使用约束。

但目前最大风险是：

“事件保持/更新有价值” 与 “事件选择时机或状态选择偏差有价值” 仍可能混淆。

需要冻结的核心不是模型，而是证据解释：

action TV 只能证明 mark 进入行为；

KEEP/RENEW continuation 只能证明决策差异；

二者结合仍不能自动证明 learned hierarchy 或 variable lifetime。

下一步只需要一个行为因果审计：

把 timing effect、mark effect、selection bias 分开。

保持：

G 不变；

EHC/DUM 不变；

comparator 不变；

不增加新模块。

仍未确定：

是否存在真正 learned commitment；

是否只是更好的 recurrent representation；

是否真正获得 variable lifetime capability。
