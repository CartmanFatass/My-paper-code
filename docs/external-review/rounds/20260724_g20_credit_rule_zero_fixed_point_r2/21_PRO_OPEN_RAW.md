Worked for 18m 14s
Scientific decision — G20 credit-rule repair

Stage reviewed: 3ec4a6500a26d5141715861f4b1f191ac141b6fb

Decision

Retain the exact-zero fast anchor. Retire the residual-table leave-one-out rule. Change the carrier of member-resolved credit from the correction representation R
t
​

to the member’s executed action decision.

However, the proposed full-table formula

Q
slow
​

(s
t
​

,a
t
​

)−Q
slow
​

(s
t
​

,a
t
i←a
i,t
anchor
​

​

)

is directionally correct but not scientifically acceptable verbatim for the current token-factorized actor. The canonical replacement should be a decision-history-conditioned anchor-policy action advantage, with downstream action decisions marginalized rather than held at factual values.

In one sentence:

The executed member action, relative to the frozen anchor policy’s conditional action distribution under the same decision history, should carry slow credit—not the initially zero residual value.

This is a correction of the P2 estimator, not abandonment of P2 or of exact active-set centering.

1. What the zero-fixed-point result establishes
Repository fact

The frozen design simultaneously requires:

an exactly zero residual output at delayed-phase entry;

a slow critic whose action argument is the centered residual table;

a leave-one-out counterfactual formed by zeroing one residual row;

a detached counterfactual advantage as the residual head’s only actor-gradient path;

no critic-regression gradient into the residual head.

The implementation realizes that contract: the residual output layer is zero-initialized, Q_slow consumes the residual table, and compute_counterfactual_advantage compares the factual table against the same table with one row zeroed.

At entry, both critic inputs are therefore identical for every member. The resulting advantage, normalized advantage, PPO gradient and Adam parameter change are all exactly zero. This is independently pinned in the focused test, including the fact that the residual remains unmoved after a finite delayed update.

Scientific conclusion

The smallest refuted proposition is:

A deterministic correction that starts exactly at zero can bootstrap itself using a point-ablation counterfactual that replaces one component of that same correction by zero.

That proposition is false by equivalence, independently of critic quality, optimizer, seed or budget.

The result does not refute:

exact-zero anchor initialization;

active-set centering;

action-space decomposition;

per-agent counterfactual advantages generally;

P2 as a candidate;

or member-resolved credit generally.

G19 confirms the relevant contrast: an exactly zero residual is not inherently immovable. Its shared slow-return advantage remains nonzero at the anchor, so its residual can receive a gradient even though its behavioral result was negative.

2. The revised credit quantity

Let j denote a member’s position in the policy’s action factorization at environment step t, and let

h
j,t
​

be that token’s exact decision history: state or critic information, active mask, lifecycle state, recurrent state, routing position, and the action prefix visible before token j is sampled.

Define a post-token slow action-value

Q
j
π
​

(h
j,t
​

,a
j,t
​

)=E
policy suffix
​

[G
t
slow
​

∣h
j,t
​

,a
j,t
​

],

where later action tokens are marginalized under the declared continuation policy.

Let π
0
​

be the frozen fast-anchor action policy. The anchor baseline is

b
j
0
​

(h
j,t
​

)=E
a
~
j
​

∼π
0
​

(⋅∣h
j,t
​

)
​

[Q
j
π
​

(h
j,t
​

,
a
~
j
​

)].

The member-resolved slow advantage is then

A
j,t
slow
​

=Q
j
π
​

(h
j,t
​

,a
j,t
​

)−b
j
0
​

(h
j,t
​

)
​

and it multiplies only that token’s policy likelihood ratio or score.

Inactive members receive exactly zero credit.

Why this leaves the zero anchor

At delayed-phase entry, the residual mean is exactly zero and the current policy equals the frozen anchor policy. But the actor remains stochastic: sampled actions vary around the anchor mean under the retained exploration distribution. The design explicitly retains tanh-Gaussian sampling and exploration while freezing fast parameters.

Therefore:

the factual sampled action a
j,t
​

need not equal every alternative anchor action;

A
j,t
slow
​

is not identically zero unless slow value is actually action-independent;

the baseline is independent of the factual action conditional on h
j,t
​

;

hence subtracting it does not create a score-function bias;

and the exact-zero residual is no longer a structurally absorbing state.

Formally,

E[∇
θ
​

logπ
θ
​

(a
j
​

∣h
j
​

)b
j
0
​

(h
j
​

)]=0,

because b
j
0
​

does not depend on the sampled current token a
j
​

. The score-weighted factual Q term can still produce a nonzero gradient.

The executed environment action should be the critic’s causal action variable. The residual table is only one parameterization of how the action distribution is changed; it is not itself what depletes battery or produces service. In G18, the environment transition and reward are functions of requested and battery-clipped executed effort.

3. Disposition of the orchestrator’s proposed formula
Accepted principle

Rebasing from the correction table to the action decision is scientifically correct. It preserves the intended estimator class at the portfolio level:

centralized slow action-value;

member-resolved counterfactual credit;

an anchor-relative default;

external slow return;

no task-specific reward shaping;

frozen fast path.

Rejected literal form

A naive full joint-action row replacement is not the canonical PPO credit:

Q(s,a
1
​

,…,a
i
​

,…,a
N
​

)−Q(s,a
1
​

,…,a
i
0
​

,…,a
N
​

),

when every other factual row is held fixed.

The current policy exposes token log-probabilities and action-prefix state, rather than one undifferentiated parallel action probability. The G17 trajectory explicitly retains per-token log-probabilities and prefix-action sums.

Consequently, later factual actions may carry information descended from an earlier sampled action. For an earlier token, a “baseline” containing those later factual descendants need not be independent of that token. Attaching such a full-table contrast directly to its score can therefore mix:

the direct environmental effect of replacing member i;

the actor’s sequential conditioning effect;

and an action-dependent baseline.

The correct counterfactual unit is the token action under its exact pre-action history, with the suffix marginalized.

Deterministic anchor action

A deterministic reference

Q
j
π
​

(h
j
​

,a
j
​

)−Q
j
π
​

(h
j
​

,a
j
0
​

(h
j
​

))

may be retained as a lower-cost ablation, provided the downstream suffix is still marginalized consistently. It is not the preferred canonical estimator because it compares against one point rather than the frozen anchor policy’s action distribution and can be more sensitive to critic extrapolation and exploration scale.

The originally proposed full-table formula may serve as a causal diagnostic of a joint-action intervention. It should not define the principal token-level PPO advantage without a proof that the relevant action factors are conditionally parallel.

4. Should the exact-zero anchor be abandoned?

No.

Abandoning exact-zero entry would remove the algebraic fixed point, but it would do so by injecting arbitrary initial behavioral change. That would sacrifice the clean statement that the delayed phase begins exactly at the accepted fast controller.

A nonzero residual initialization would confound:

delayed-credit competence;

arbitrary symmetry breaking;

changed initial behavior;

and possibly altered G17 compatibility.

The defect is in the counterfactual argument, not in the anchor guarantee. The numerical evidence already demonstrates that the same critic becomes member-sensitive as soon as its factual and counterfactual inputs differ.

Exact-zero entry should therefore remain load-bearing.

5. Outcome mapping
Portfolio-level mapping

The previous high-level portfolio mapping remains in force:

k → k_i alone remains formally excluded as the impasse solution;

P1 remains ineligible on the current timing-credit gate;

P2 remains the active candidate, scoped to sources where the delayed-optimal change preserves the immediate aggregate;

P3 remains dormant because the centered authority has not been shown inexpressive on G18;

P4 remains the matched reduction for future P1/P3 behavioral claims.

The Q4 scope also remains unchanged. The registered G18 delayed direction is centered, but there exists a common-mode-reduction class in which centering deletes the necessary action.

Screen-level mapping

The repaired G20 screen must be re-registered before any run. The existing mapping does not survive unchanged.

The old screen was frozen around a different critic action, different factual/counterfactual pair, and different actor-credit estimand. Credit is protected semantics, and the project contract requires probability and credit authority plus conclusion-bearing metrics to be frozen before observing a result.

The existing numerical performance thresholds may be reused because the source, compatibility claim and delayed-mechanism claim have not changed. But their scientific interpretation must be rebound to the repaired estimator.

A fresh mapping must distinguish at least four cases:

Observation Smallest scientific update
Chain-rule baseline invalid, zero-entry gradient still structurally zero, replay inconsistent, or action critic cannot identify action dependence Invalid or non-identified estimator; no P2 update
Estimator identified, but G17 compatibility fails This anchor-policy action-credit realization is incompatible with the accepted fast controller
G17 retained, but G18 delayed access or rotating-member mechanism fails This revised P2 realization is insufficient on the registered G18 source; do not retire centering or all counterfactual credit
G17 retained and G18 access plus mechanism pass Support only for the revised anchor-relative action-credit realization on the Q4-scoped source

The current branch sequence assumes that operational validity includes a residual output that has moved away from zero. Under the frozen rule that condition is deterministically impossible, so the current screen would classify an estimator-definition failure as behavioral no-access.

Re-registration need not imply a conclusion-bearing iteration or a new portfolio candidate number. It is nevertheless mandatory before the result can be interpreted.

6. Structural generalization

The Project Manager’s proposed generalization is correct after narrowing its quantifier.

Exact theorem

Let c
θ
​

(x) be a deterministic correction satisfying

c
θ
0
​

​

(x)=0

for every input at the anchor. Suppose member credit is

A
i
​

(c)=F(c)−F(c
i←0
),

and suppose:

the factual correction and ablated correction are evaluated at the same state;

the actor receives gradient only through a detached A
i
​

-weighted score or likelihood ratio;

the critic loss is detached from the correction actor;

and there is no independent stochastic, finite-difference or derivative probe.

Then

A
i
​

(c
θ
0
​

​

)=F(0)−F(0)=0

for every member, and θ
0
​

is an absorbing actor-update point.

This is independent of the form or quality of F.

What the theorem does not cover

It does not establish that every “counterfactual over a correction” is inert. The following can leave zero:

a counterfactual over sampled actions generated around a zero correction mean;

a correction with nonzero stochastic support at zero mean;

a finite-difference probe F(+ϵe
i
​

)−F(−ϵe
i
​

);

a directional derivative ∂F/∂c
i
​

∣
c=0
​

;

or a shared realized-return advantage such as G19’s.

The retired family is therefore:

Exact-zero deterministic correction + factual-versus-zero-ablation contrast over that correction + no independent probe.

It is not the entire per-agent counterfactual estimator class.

7. Does the theorem bind P1 and P3?
P1 — asynchronous semi-Markov skills

Not generally. Conditionally yes.

P1 is bound only if it is realized as:

an exactly zero additive skill or action correction over a frozen anchor;

whose member credit is obtained by zeroing that same correction;

with no option-return, action counterfactual, stochastic skill choice or derivative path.

A native semi-Markov policy whose skill action is sampled and credited by an option return or an anchor-policy action advantage does not satisfy the theorem’s premises. P1 therefore remains ineligible on the existing timing gate, but it is not additionally retired by this zero-fixed-point result. Its independent heterogeneous-tempo gate remains open.

P3 — separate slow allocation authority

Not generally. Conditionally yes.

P3 is not bound when the slow allocation is itself a sampled action—priority, quota, role or allocation—and credit compares its realized decision against a default or anchor distribution. Such a slow action has nontrivial support at entry even if its parameters are initialized to reproduce the anchor in expectation.

P3 is bound if it is implemented as an exactly zero deterministic additive allocation correction and credited by ablating that correction to zero.

Thus the theorem should be checked as an architectural lint rule before P1 or P3 realization, but it is not a scientific objection to either candidate as a class.

8. Retained alternatives
C1 — Anchor-policy conditional action advantage — preferred

The executed action is compared with the frozen anchor action distribution under the same token history. It retains exact anchor behavior, PPO-style score credit, member resolution and environment neutrality.

Strongest risk: the conditional action critic may not be sufficiently identified, especially for long-delayed consequences. A critic-identification failure must not be misreported as a failure of centered authority.

C2 — Slow-Q tangent projected into the centered action subspace — parked

Use the local action derivative of a slow critic at the anchor and project it onto the active-set-centered tangent:

g
t
​

=P
center
​

∇
a
​

Q
slow
​

(s
t
​

,a
t
0
​

).

This is nonzero at an exactly zero residual whenever the critic has a nonzero centered directional derivative.

Strongest risk: critic derivatives can be much less identified than critic values and may exploit unsupported local geometry. This would be a distinct deterministic-gradient estimator requiring its own mapping.

C3 — Stochastic centered correction probe — parked, not preferred

Maintain a zero correction mean but inject centered stochastic correction perturbations, then compute the counterfactual over the realized nonzero correction.

Strongest risk: sampled behavior no longer exactly matches the fast anchor. Any result could be explained by increased exploration or altered action variance rather than member-resolved credit.

Nonzero deterministic residual initialization is weaker than C3 and should remain excluded unless the exact-anchor requirement is deliberately abandoned in a separately registered proposition.

9. Next evidence action

Before any behavioral screen, freeze one revised G20 estimator note that establishes:

the exact action variable carrying credit—executed action, not residual representation;

the exact token decision history;

whether the anchor reference is an expectation under π
0
​

or a deterministic anchor action;

how downstream token actions are marginalized;

the policy whose continuation defines Q
j
π
​

;

critic inputs, return horizon and detach boundaries;

analytical baseline independence from the factual token;

non-inertness at exact-zero residual under an action-sensitive reference Q;

a critic-identification branch distinct from behavioral no-access;

the revised smallest-supported and smallest-refuted propositions.

The old G20 run must remain withheld. This review authorizes neither implementation nor nonformal or formal compute.

中文简报

**裁决：**保留“快速策略完全不变、延迟 residual 从严格零开始”的 anchor 设计；废弃的是“对零 residual 表做 leave-one-out”这一条 credit rule。

新的成员级信用应由实际执行的成员动作承载。更严格地说，应比较：

当前成员在其真实决策历史下采样的动作价值，减去冻结 fast-anchor 策略在同一决策历史下的动作价值期望。

不能直接采用“把完整联合动作表中的第 i 行替换成 anchor 动作、其余行保持事实值”的朴素版本，因为当前动作策略存在 token/prefix 因子化；后续动作可能依赖前面成员的动作，这会让所谓 baseline 间接依赖正在被训练的动作。正确版本必须在成员动作处做条件反事实，并对后续动作进行一致的边缘化。

原有 G20 的高层组合关系仍然成立：P2 继续，P1 仍未因当前 gate 获得实现资格，P3 仍处于 dormant，Q4 的适用范围不变。但新的 G20 screen 必须重新注册结果解释。旧阈值可以复用，旧科学映射不能原封不动继承，尤其必须把“action critic 未识别”与“P2 行为机制失败”分开。

这个零固定点定理只约束以下结构：

确定性 correction 从严格零开始，并通过“事实 correction 与把同一 correction 置零”的差值获得唯一 actor credit。

它不自动约束基于实际动作、随机决策、有限差分、critic 导数或 option return 的 P1/P3 实现。

本回复不授权实现，也不授权任何计算。
