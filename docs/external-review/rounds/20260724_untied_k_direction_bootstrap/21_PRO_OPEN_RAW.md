Worked for 12m 58s
Scientific review — 20260724_untied_k_direction_bootstrap

Snapshot reviewed: d07eda4b0987ecac3d5583c3e5814b419fb57f5e. The stage commit itself distinguishes the G17–G20 repository facts from the unestablished Project Manager inference that per-agent variable period might resolve the impasse. I therefore treat untied period as a hypothesis to adjudicate, not as an inherited conclusion.

Overall disposition: retain per-agent variable skill period as one conditional portfolio candidate, but reject it as the direct or sufficient explanation of G17–G19. Continue G20's zero-compute direction. Do not implement or run anything on the authority of this review.

1. Verdict on A
Verdict: restatement as posed; potentially useful only after a different action-and-credit factorization

The evidence does establish a temporal-credit problem:

G17 succeeded when actor credit was shortened to the task's one-step causal window; the important correction was not additional capacity but removal of unrelated future demand from the current action's advantage.

G18 established that delayed battery consequences are learnable, while also establishing that isolating the slow critic does not prevent successor-value actor gradients from changing the immediate policy.

G19 preserved the fast tensors exactly and constrained the residual gradient operationally, yet obtained no delayed improvement: the delayed source remained at 0.66667 utility with zero spike service.

But those findings do not establish that a skill's holding period is the missing variable. G17–G19 operate on a continuous recurrent actor that emits primitive actions every environment step from current observations, active-set context, per-member recurrent state and action prefixes. No high-level skill residence period is the decision variable in those experiments.

The stronger causal diagnosis is:

The impasse is primarily an action-authority and credit-factorization problem, with a temporal manifestation.

The fast requirement is largely an aggregate service mapping: current load and mix determine how much service should be produced now. The delayed battery requirement contains an agent-specific redistribution decision: two allocations can provide equal immediate service but differ in which anonymous member spends battery, thereby producing different later service. The registered G18 intervention demonstrates exactly that structure—equal first-step service, different battery state and later utility.

Moreover, one primitive action can have both an immediate effect and a delayed effect. Assigning an agent a single longer or shorter period does not separate those simultaneous causal paths. A residence time is not automatically a causal window.

The project's durable principle already requires the observation/check clock, renewal opportunity, realized segment and learning-credit window to be distinguished. Collapsing them again under a per-agent scalar k
i
​

would repeat the same conceptual error at another level.

Per-agent variable period becomes a real mechanism only under the following conditional interpretation:

The high-level agent decision is an actual semi-Markov commitment—such as a skill, role or allocation contract—with its own termination.

Immediate primitive control remains a separate fast decision.

The high-level log-probability receives event-local option credit, rather than simply inheriting a trajectory window of length k
i
​

.

Delayed consequences after the option boundary are represented through a declared bootstrap or causal estimator rather than being truncated at the holding period.

The slow decision has behavioral authority over the relevant agent-specific redistribution.

Under that interpretation, untied period is a plausible supporting component of one hierarchy. Without those changes, replacing k by k
i
​

is resegmentation, not resolution.

2. Coupling audit
Current coupling Scientific disposition Rule once periods vary
Skill reassignment time = period boundary Load-bearing, but only at the individual-decision level. Agent i's realized lifetime or termination should determine when its own skill can be renewed. The clock must be declared as primitive time, active-service opportunity, or another agent-local clock; temporary absence must not silently change its meaning. Other agents need not renew.
High-level sample closure / credit window = period boundary The closure relation is useful; the credit identity is not. Close the decision record at that decision's termination, departure, terminal censoring or forced invalidation. Estimate return over the realized segment plus a declared bootstrap. Do not assert that the skill's causal effects stop at its boundary or that all rewards inside the segment belong exclusively to it.
Recurrent chunk length = period Inherited convenience; delete the identity. Truncated recurrent training is a numerical sampling choice. Recurrent state should persist across chunk edges, with boundary indicators and masks where needed. A chunk may contain zero, one or several skill events.
Episode length divisible by period Pure convenience; delete it. Permit right-censored final segments. Freeze whether their value target bootstraps, terminates or is excluded from a duration estimand, and report the resulting exposure.

The fixed trunk currently uses one k for renewal, high-level closure, recurrent chunking and episode divisibility. The existing HA-CTSE path already samples per-agent duration targets, but its surrounding collection path still closes an environment-level high-level sample when any duration expires at a shared check boundary. That is evidence that "duration value" and "fully untied event ownership" are different abstractions.

Recurrent chunking is explicitly set to chunk_length=k, while episode validation requires divisibility by k; neither relation carries causal content.

3. Desynchronization cost

Desynchronizing agents is scientifically coherent, but it replaces a rectangular synchronized problem with a marked, ragged event process.

Event and probability ownership

A high-level record must be owned by a particular lifecycle and boundary:

(τ, i, I
τ
​

, z
i
−
​

, e
i
​

, z
i
+
​

, d
i
​

, logπ
i
​

, termination reason)

where I
τ
​

includes the active mask, current anonymous roster, teammate skills and ages, team context, and any earlier decisions in a simultaneous renewal set.

Nonrenewing agents carry their previous decisions deterministically and must contribute no new high-level log-probability. Simultaneous renewals need either an exchangeable joint distribution or a frozen anonymous autoregressive ordering. Lifecycle slot identity cannot silently become coordination information.

Value and advantage semantics

With overlapping agent segments, one team reward can be causally relevant to several active decisions. That is not automatically invalid—one reward may legitimately weight several score-function terms—but the estimator must say whether it is:

a shared team advantage;

a per-agent counterfactual or marginal advantage;

an option-level difference return;

or a factorized value-decomposition target.

Rewards must not simply be partitioned by whichever segment happens to close first. Likewise, one environment-level value at a synchronous boundary is no longer enough to define all agent-local bootstraps.

A particularly important boundary case is departure. Temporary absence, terminal departure and episode termination are not interchangeable. The skill clock may pause, continue or terminate at absence, but exactly one semantics must be frozen, and survivor recurrent state must remain owned by the surviving lifecycle.

Replay and recurrence

On-policy replay must reconstruct the probability under the exact boundary-time information set. The current HA-CTSE machinery already stores distinct termination, skill and duration log-probabilities and re-evaluates forced team codes and duration candidates; a fully asynchronous version would require the same exactness for each event rather than for a synchronized environment sample.

Primitive recurrent state should generally remain lifecycle-continuous across high-level renewals. Resetting it at every skill boundary would make period control partly a hidden-state reset controller, confounding duration with memory. Conversely, carrying high-level option state after a terminal departure would violate lifecycle ownership.

Statistical and comparator cost

Short-period agents create more decisions, entropy terms and optimizer exposure than long-period agents. Consequently:

equal environment interaction does not mean equal high-level learning opportunity;

a gain can come from more renewal samples rather than better temporal matching;

duration collapse can create a self-reinforcing update-frequency bias;

final segments introduce duration-dependent censoring;

high-level batches become dominated by frequently renewing agents unless estimands are explicitly weighted.

Both environment steps and decision/update exposure therefore have to be reported, as required by the project evidence contract.

Coordination cost

Agents conditioning on independently renewed information can hold different vintages of team context. That is acceptable only if stale context is part of the declared state. Otherwise the process becomes neither a synchronized joint policy nor a well-defined asynchronous one.

This vintage problem is the main reason not to retain a periodically sampled Z by default.

4. Team skill disposition
Primary disposition: replace periodic sampled Z with a deterministic read-time coordination context

In the primary untied-period candidate, Z should cease to be a persistent sampled team state. Preserve the useful OPT-derived information as a deterministic context

C
t
​

=f(s
t
​

, o
t
active
​

, M
t
​

, R
t
​

),

evaluated whenever an agent or simultaneous event set renews. Here M
t
​

is the active membership information and R
t
​

is the current anonymous roster of held skills and ages.

I would reserve the symbol Z for a genuinely sampled team commitment. The default information object should be called C, not Z, because it has:

no holding period;

no stochastic action;

no policy log-probability;

no entropy objective;

no independent recurrent ownership;

and no classifier-based claim of team skill.

This follows the design's own distinction between recognized information and sampled commitment. The v6 description says that a deterministic recognized variable cannot acquire policy-gradient meaning merely through an identifiability reward, whereas sampled Z was intended to provide exogenous variation and atomic switching. Those are different causal objects and should not share one name.

Probability factorization

Let τ
m
​

be a high-level event time and B
m
​

the set of active agents renewing at that time. For an anonymous, frozen ordering σ
m
​

of a simultaneous event set, the primary factorization should be:

p(H)=
m
∏
​

j=1
∏
∣B
m
​

∣
​

π
θ
​

(e
σ
j
​

​

,z
σ
j
​

​

,d
σ
j
​

​

∣C
τ
m
​

​

,o
σ
j
​

,τ
m
​

​

,R
τ
m
​

−
​

,{e,z,d}
σ
<j
​

​

).

Here:

e
i
​

is the renewal/keep decision;

z
i
​

is the new individual skill when renewed;

d
i
​

is a duration or termination contract;

held decisions of i∈
/
B
m
​

contribute no new probability factor;

the roster snapshot is the one visible when the decision was sampled.

The current synchronized model samples Z first and then autoregressively samples individual skills conditioned on it and earlier individual choices. The event factorization above preserves useful autoregressive coordination while removing the unsupported requirement that every event share one sampled team action.

Intrinsic-reward consequence

Because C
t
​

is deterministic recognized information, remove the team-code entropy and q_D(Z | ·) intrinsic-reward path from this primary candidate. Predictability of C
t
​

cannot establish a learned team commitment.

An individual-skill intrinsic term may remain a live candidate only if:

it has the same mathematical input contract across environments;

it evaluates behavior or generic effects rather than duration labels alone;

it uses the active skill and the exact assignment prior;

it reads no battery identity, named rotating role, demand phase, benchmark goal or external reward;

and it is not treated as evidence of a useful skill without intervention and natural-policy transport.

The environment reward remains the sole task return. These are the existing project boundaries, not optional safeguards.

Reactivating a sampled team commitment

A sampled persistent team variable remains a separate portfolio candidate. It should be reactivated only if an intervention establishes a team-level consequence that asynchronous individual decisions or deterministic context cannot reproduce—for example, a genuinely atomic strategy switch whose staggered realization is causally harmful. It would then have its own team-event clock and factor:

q
∏
​

π
U
​

(U
q
​

∣C
η
q
​

​

)
m
∏
​

i∈B
m
​

∏
​

π
i
​

(e
i
​

,z
i
​

,d
i
​

∣C
τ
m
​

​

,U
active
​

,R
τ
m
​

​

).

That team clock must not be inherited from any individual k
i
​

.

5. Plural candidates
Candidate P1 — Event-indexed asynchronous semi-Markov skills

Causal story. Each agent renews a skill and duration at its own event. A fast executor handles current service; the high-level skill-duration decision controls persistent behavior or role. Credit is attached to the event decision using its realized segment and a declared boundary bootstrap.

Replaces or deletes. Replaces global synchronized reassignment and environment-wide high-level closure. Deletes episode_length % k == 0, period-sized recurrent chunks and periodic sampled Z in its primary form. Retains individual skill bottlenecking, active masks, lifecycle continuity and exact high-level log-probability replay.

Evidence explained. It offers a way for fast primitive decisions to retain one-step credit while a genuinely slower decision carries delayed consequences. The repository already contains per-agent duration targets and masks, showing that duration actions are representable even though fully asynchronous event ownership is not yet established.

Strongest contradiction. G17–G19 failed or succeeded without any skill-period action. In addition, an individual primitive action may simultaneously affect current service and future battery, so duration alone cannot separate its two causal paths. P1 is therefore contradicted as a timing-only explanation; it survives only as a hierarchy-plus-credit mechanism.

Candidate P2 — Active-set functional decomposition of fast common mode and slow redistribution

Causal story. Decompose the joint action change into:

a common or aggregate component responsible for immediate service; and

an anonymous active-set-centered component that reallocates effort among members while preserving the immediate aggregate target.

Slow credit acts on the second component. Fast credit acts on the first.

Replaces or deletes. Replaces G19's parameter-space gradient projection with a functional or action-space authority decomposition. It can retain the accepted fast controller and does not require skill labels, variable periods or sampled team state.

Evidence explained. G18's decisive counterfactual is a redistribution: equal current service but different agent battery expenditure and later service. G19 proved that a residual can move while the anchor remains bitwise fixed and its projected gradient satisfies the registered dot-product condition, yet this did not produce delayed access. That is consistent with protecting parameters without exposing the relevant functional redistribution direction.

Strongest contradiction. Not every delayed task is a zero-sum redistribution problem. Some delayed actions legitimately require changing total effort or another fast aggregate. An overly strict centering operator could remove the actual causal action. P2 is therefore a candidate for the registered G18 mechanism, not yet a general solution.

Candidate P3 — Separate slow allocation authority over a fast executor

Causal story. The slow policy does not add a small primitive-action residual. Instead, it controls an explicit agent-level allocation variable—role, priority, quota, active skill or another generic commitment—that determines who should bear current load. The fast executor controls how to satisfy the current service target under that allocation.

Periods may be fixed or variable; untied periods are optional rather than defining.

Replaces or deletes. Replaces G19's additive residual and its requirement that slow behavior be expressed as a perturbation of the same primitive action mean. Retains a fast service executor but changes the probability factorization and action authority. Deletes the assumption that preserving a fast parameter gradient is equivalent to preserving the scientifically relevant fast behavior.

Evidence explained. G18's delayed decision is naturally about which members expend effort before a roster event. G19's residual had feature access and trainable movement but no delayed result. A slow allocation action could make the redistribution an explicit decision rather than asking shared primitive parameters to discover it implicitly.

Strongest contradiction. The G18 observations already expose battery, rotation status and time, so an ordinary recurrent actor has enough information in principle. A supplied role variable may merely rename those observations, and a skill label conditioned on the known rotating flag would not establish learned skill semantics. P3 must beat the direct recurrent reduction and show behavioral actionability under intervention.

Candidate P4 — Flat recurrent controller with per-agent causal credit

Causal story. Remove skills, durations and team latent state. Emit primitive actions every step from the same anonymous active-set information and per-lifecycle recurrent state, but use an agent-sensitive delayed-credit estimator that distinguishes which member's action produced the future consequence.

Replaces or deletes. Deletes the hierarchy entirely. Retains active-set aggregation, masks, recurrent lifecycle continuity, exact policy replay and the external reward. It changes credit factorization rather than adding temporal abstraction.

Evidence explained. It explains the entire line as a credit-geometry problem: G17 requires immediate credit; G18 requires delayed, agent-sensitive credit; G19 fails because preserving the fast map does not make the delayed redistribution direction identifiable or controllable.

Strongest contradiction. A flat controller can change its decision every primitive step and may fail to form stable commitments, resist churn or transport to environments where heterogeneous long-lived duties—not only delayed primitive effects—are causally necessary. A positive P1 result on held-out temporal heterogeneity could refute P4's sufficiency.

These candidates do not reopen exact TD(0), raw-sum, channel-normalized, actor/critic-isolated credit or the G19 fast anchor. P2 changes the functional action subspace; P3 changes slow action authority; P4 removes the hierarchy; P1 changes high-level event ownership and return semantics. The closed implementations remain closed.

6. Matched reduction

The strongest information-matched reduction is P4: the flat recurrent causal-credit controller.

It should receive exactly the information that the asynchronous hierarchy receives:

the same state and local observations;

the same active mask and anonymous active-set context;

the same lifecycle recurrent continuity;

the same membership-change and age information, where those are legitimate observations;

the same external reward;

the same action factorization and action support;

the same environment interaction exposure;

matched or explicitly reported optimizer-update exposure.

It must not receive skill labels, chosen durations or a supplied "rotating role." It may receive generic event information already available to the hierarchical policy.

The relevant reduction question is:

Can the direct recurrent controller, with the same information and an agent-sensitive delayed-credit estimator, preserve the G17 immediate mapping and learn the G18 delayed redistribution without any skill period?

If yes, fixed period should stay for this capability claim. A variable-period result would then be explained by changed credit, extra renewal decisions, additional optimizer exposure or extra capacity—not by temporal abstraction.

If both P1 and P4 access the training source, the distinguishing evidence is held-out transport to genuinely heterogeneous temporal duties and intervention-sensitive persistence, not skill usage, duration entropy or classifier accuracy. The project contract explicitly requires the matched direct recurrent null and rejects weak skill evidence.

7. Separating evidence
Single observation that would most move confidence

The strongest future observation is a positive, held-out period-specific interaction on a source with anonymous membership changes and causally heterogeneous duties:

I
period
​

=[U
untied
​

−U
fixed
​

]
heterogeneous tempo
​

−[U
untied
​

−U
fixed
​

]
homogeneous tempo
​

.

All period arms must use the same event-credit semantics. The flat recurrent reduction must receive the same information and credit.

Confidence in untied period would rise materially only if all of the following form one registered observation:

the immediate-service compatibility gate passes first;

I
period
​

is positively separated from zero;

the improvement appears on held-out tempo and membership trajectories;

it survives anonymous slot permutations;

the information-matched flat recurrent controller does not reproduce it;

intervention shows that the learned duration changes persistent executable behavior under natural policy use.

If untied and fixed periods are equivalent once credit is corrected, or if the flat reduction matches untied period, confidence should move sharply against period as the explanatory mechanism.

Evidence semantics to freeze beforehand

Freeze:

the source causal graph and constructive-access controls;

homogeneous versus heterogeneous tempo generation;

observations and all future-event announcements;

anonymous membership, join/leave/rejoin and survivor-state semantics;

the meaning of primitive, observation/check, renewal, segment and credit clocks;

whether temporary absence advances, pauses or terminates an agent lifetime;

event probability factorization and simultaneous-event ordering;

conditioning snapshots used for policy replay;

segment closure, post-boundary bootstrap and terminal censoring;

external and intrinsic reward definitions;

action support and active-mask rules;

actor, critic and recurrent information;

environment-step and optimizer/event exposure;

fixed-period and flat-controller comparator capacity;

seed provenance, held-out trajectories and slot permutations;

first-match result precedence;

conclusion-bearing metrics and confidence procedure.

These are precisely the classes of semantics the project requires to be frozen before observing a conclusion-bearing result.

Smallest refuted unit
Candidate Smallest proposition refuted by a valid negative
P1 async semi-Markov skills "Heterogeneous per-agent holding times add causal value beyond event-local credit and the matched flat recurrent controller." Absence of the registered period interaction refutes this proposition, not all temporal abstraction.
P2 active-set functional decomposition "The delayed-control direction for the registered source lies in the proposed anonymous redistribution subspace while the immediate direction lies in the retained fast subspace." Failure to distinguish the constructive and equal-service counterfactual pair refutes this decomposition.
P3 slow allocation authority "A separate slow allocation decision is behaviorally actionable and can change delayed outcomes without rewriting the fast executor." An intervention that changes the slow variable but not executed allocation refutes its actionability.
P4 flat recurrent reduction "Temporal abstraction is unnecessary once information and causal credit are matched." If P4 accesses the source but cannot produce persistent, held-out heterogeneous-tempo behavior that P1 produces naturally, this sufficiency claim is refuted.
8. Relation to G20

Continue G20. Do not drop it in favor of untied period.

G20 is currently better aligned with the actual separating structure in the evidence. G18's constructive distinction is anonymous member redistribution under equal immediate service, and G19's parameter-space protection did not expose delayed access. G20 asks whether an active-set-centered residual can make those per-step redistribution directions explicit.

Its scientific role should be broadened slightly:

determine whether the registered constructive-minus-counterfactual action difference belongs to an anonymous centered subspace;

determine whether that subspace preserves the G17 aggregate service direction;

determine whether shared scalar actor credit contains enough information to orient that subspace;

identify a counterexample in which centering deletes a required delayed common-mode action.

If successful, G20 should be absorbed as a credit/action-authority component, usable by P1, P3 or P4. It would not prove variable periods.

If unsuccessful, retire only the active-set-centered residual proposition. Do not infer that every per-agent or counterfactual credit factorization is false.

9. One scheduled evidence action and reactivation conditions
Recommended scheduled action

Complete one zero-compute timing–credit identifiability derivation using the frozen G18 first-action intervention pair.

The derivation should compare, at the level of scientific estimands rather than implementation:

fixed synchronous segmentation with shared team advantage;

per-agent untied segmentation with the same shared advantage;

an agent-sensitive or active-set-centered redistribution advantage.

The central proposition to derive or disprove is:

Does changing only the boundary schedule alter the information available to distinguish the constructive rotating-member allocation from the equal-immediate-service counterfactual?

If the answer is no, then k→k
i
​

alone is formally excluded as a solution to this impasse. If the answer is yes, the derivation must identify the exact probability or return term that changes and why the matched fixed-period or flat controller cannot express it.

This is the cheapest, most reversible evidence action and directly decides whether untied period is mechanistic or merely a new segmentation of the same insufficient actor signal. It also completes rather than interrupts the active G20 line.

Reactivation conditions

P1 / untied period: eligible for an implementation proposal only after the derivation identifies a decision-local information or credit difference attributable to asynchronous event ownership, or after a frozen heterogeneous-tempo source yields the positive period-specific interaction above.

P2 / G20 implementation: eligible only if the derivation shows that the registered delayed direction lies in the centered subspace and that the required fast common mode remains representable.

P3 / separate slow allocation: reactivate if a representation argument shows that the delayed allocation cannot be expressed by the centered residual or matched flat controller without changing the fast mapping.

P4 / flat recurrent null: remains mandatory whenever P1 or P3 advances to behavioral evidence.

Sampled persistent team commitment: reactivate only after an intervention demonstrates a necessary atomic team consequence, natural-policy actionability and failure of deterministic read-time context plus individual event decisions.

This recommendation authorizes neither implementation nor nonformal or formal compute.

10. 中文用户简报

决定："每个智能体使用可变技能周期"被保留为一个有条件候选，但它不是 G17–G19 冲突的直接解释。按当前表述，它只是把"信用窗口不匹配"重新表述为"周期不匹配"。现有证据更指向动作权限与信用因子化：即时目标主要需要保持团队总服务方向，延迟目标需要识别"由哪个匿名成员承担当前消耗"的重分配方向。

已排除：

只把全局 k 改成 k_i；

直接令"技能持有期 = 信用因果窗"；

继续把技能周期、RNN chunk 长度和 episode 整除约束绑在一起；

默认保留一个周期性、持久化、随机采样的团队技能 Z；

重新调参、换种子或改名恢复已经关闭的 G18/G19 候选。

保留的开放候选：

带个体事件信用的异步半马尔可夫技能；

G20 的 active-set 匿名重分配方向；

"慢速成员分配/角色权限 + 快速即时执行器"；

信息匹配的扁平循环控制器作为最强 reduction。

团队信息默认应改为在每个个体边界即时计算的确定性上下文；只有在干预证明确实需要原子化团队承诺时，才重新引入具有独立时钟的随机团队变量。

**建议的下一项证据动作：**只完成零计算的"时钟 × 信用可识别性"推导，判断改变边界本身能否区分 G18 中即时服务相同、但未来后果不同的两种成员分配。

本回复不授权任何实现，也不授权任何非正式或正式计算。

Sources