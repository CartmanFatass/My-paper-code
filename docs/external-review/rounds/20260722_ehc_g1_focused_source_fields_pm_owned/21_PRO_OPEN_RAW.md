1. Field-completion table

The source remains:

ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1
family = Option A clean-infrastructure temporal-duty source

G0 remains closed. No G0 task, reward, threshold, checkpoint, seed, or result is reused.

1. Physical state, transition, termination
Field	Value
1.1 lifecycle-local physical state	x_i=(g_i, age_i, remaining_i, correct_count_i, terminal_streak_i) where g_i∈{-1,+1}, age_i∈N, remaining_i∈{0,...,18}, correct_count_i∈N, terminal_streak_i∈{0,1,2}. g_i is environment-hidden after cue expiry.
1.2 JOIN/reset	Genuine JOIN initializes age=0, correct_count=0, terminal_streak=0, recurrent state reset, new duty sampled. Completed duty segment performs the same reset before the next segment.
1.3 transition	For active lifecycle i: age←age+1; remaining←remaining-1; correct_count←correct_count+1 iff primitive action equals g
i
	​

; terminal_streak←min(2,terminal_streak+1) iff current and previous active action satisfy duty, otherwise reset to 0.
1.4 correct action	correct(a_i)=1[a_i=g_i], where primitive action space is {-1,0,+1} and g
i
	​

∈{−1,+1}.
1.5 bounds/failure	Duration support is {6,10,14,18}. Invalid action is impossible because policy support is fixed. Terminal LEAVE closes incomplete duties as censored; censored segments do not count as successful completion.
1.6 interaction	Members are task-dynamics independent. The joint transition factorizes: (P(x_{t+1}
2. Actor and critic information contract
Field	Value
2.1 actor observation	Ordered actor fields: (cue_value, cue_present, new_segment, join_flag, rejoin_flag, normalized_active_count). Domains are binary except cue value {-1,0,+1} and normalized count [0,1]. No target, duration, remaining time, reward, success, progress, identity, lifecycle key, or future membership.
2.2 critic observation	Critic may access task-state fields unavailable to actor: current duty progress, remaining duty fraction, completion statistics, active-count statistics, membership-event flags. Critic never provides these fields to actor.
2.3 cue	At duty start, cue reveals g
i
	​

 for exactly two active primitive transitions. After expiry, cue becomes zero and target remains hidden.
2.4 history/clocks	Actor recurrent state is legal memory. JOIN resets recurrent state. Temporary LEAVE freezes recurrent state and commitment state. REJOIN restores them. Physical, opportunity, event, and segment clocks remain distinct.
2.5 anonymity/leakage	Lifecycle IDs, epochs, roles, named agents, future duty duration, future membership, reward, success, and progress are prohibited from actor inputs.
2.6 OR/DUM/EHC matching	OR, DUM, EHC receive identical information. Only EHC receives the commitment-to-logit path: base_logits + W_z(m*z).
3. External reward and utility
Field	Value
3.1 transition reward	Dense external reward equals current active-duty correctness contribution plus terminal completion contribution. No intrinsic reward is added.
3.2 utility	U=0.75A+0.25B, where A is total correct active actions divided by active action opportunities and B is completed duty segments divided by eligible segments. U∈[0,1].
3.3 aggregation	Late JOIN contributes only after activation. Temporary absence contributes neither active correctness nor segment progress. REJOIN resumes the same lifecycle. Terminal LEAVE closes the lifecycle.
3.4 penalties	No additional penalties. Missing/censored segments do not receive completion credit. Invalid actions are impossible under the fixed action space.
3.5 intrinsic boundary	No task field, duty target, success predicate, progress, identity, or external reward enters any environment-agnostic intrinsic signal.
4. Training and held-out distributions
Field	Value
4.1 horizon/roster	Horizon 80 primitive steps. Initial roster distribution: balanced over registered anonymous roster sizes. Episodes are sign-paired across arms.
4.2 duty sampling	At JOIN and completed duty boundaries: g
i
	​

∼Bernoulli(0.5) mapped to {-1,+1}. Duration distribution: uniform over {6,10,14,18}.
4.3 cue sampling	Cue start occurs only at duty start. Cue duration is exactly two active steps. Cue time, target, duration, opportunity process, and membership events are independent.
4.4 membership process	Anonymous JOIN, temporary LEAVE, REJOIN, terminal LEAVE. Temporary absence freezes lifecycle state. REJOIN restores lifecycle state.
4.5 training distribution	Training uses the declared duty-duration support and membership process; no future schedule information is exposed.
4.6 held-out distribution	Held-out evaluation changes roster patterns, membership timing, and duty-duration realizations while preserving the causal dependency that hidden post-cue information must be retained.
5. G1 identifiability and battery mapping
Field	Value
5.1 additional source predicates	Required before access: (1) persistent-oracle reachability; (2) primitive-reactive/no-retention ceiling; (3) reward identity consistency; (4) duty-duration and lifecycle support.
5.2 intervention inventories	KEEP/RENEW rows must come from natural policy decisions only. Selection strata remain outcome-blind. Frozen battery thresholds remain unchanged.
5.3 held-out admission	Held-out transport may only be claimed after access passes and the unchanged battery passes.
5.4 intervention states	I_TV uses same-state paired primitive-action distributions under commitment intervention. C_total_KEEP and C_total_RENEW use terminal utility differences from paired continuation branches.
5.5 mapping	K-bin support tests realized commitment durations; I_TV tests executable mark influence; C-total tests natural consequence. None alone proves variable lifetime.
6. Exposure, uncertainty, seeds, RNG
Field	Value
6.1 training exposure	Five paired replicates. Per arm: 16 environments, horizon 80, 250 updates, 320k transitions, 1000 base optimizer steps; DUM/EHC additionally train event parameters with matched exposure.
6.2 evaluation	Evaluate final registered checkpoint only. Four cells: IID deterministic, IID stochastic, held-out deterministic, held-out stochastic. 256 episodes per cell per replicate/arm.
6.3 confidence	95% percentile hierarchical bootstrap, resampling replicate triples then paired episode IDs. Underpowered access remains separate from confident no-access.
6.4 seeds	New G1 source requires new explicit integer seeds for initialization, task generation, membership, duty, opportunity, event, mark, primitive action, evaluation, audit, bootstrap. These are source-owned constants, not inherited from G0.
6.5 RNG ownership	Separate namespaces for task, membership, opportunity, event, mark, primitive action, evaluation, and bootstrap. Common-random-number pairing applies only where the estimand requires it. Cross-arm leakage and train/evaluation RNG reuse are prohibited.
2. Frozen-content conformance

Confirmed:

G0 remains NO_ACCESS_THIS_BENCHMARK; no rescue or reinterpretation.

OR/DUM/EHC preserved.

EHC-only causal treatment preserved:

primitive_logits=base_logits+W
z
	​

(mz)

Primary estimand preserved:

G=U
EHC
	​

−U
DUM
	​


Anonymous membership/lifecycle semantics preserved.

Physical/event/opportunity/segment clocks remain distinct.

Access precedes mechanism interpretation.

Existing K-bin, I_TV, C_total_KEEP, C_total_RENEW battery semantics remain unchanged.

No G0 value is imported as a default source contract.

3. Derived intervention, natural, and held-out consequences
Intervention consequence

If EHC is meaningful:

z→primitive behavior

must survive same-state intervention.

Passing I_TV only proves executable influence, not useful skill.

Natural consequence

A valid commitment mechanism requires:

KEEP when current commitment remains useful;

RENEW when future duty requires replacement;

persistence across hidden intervals.

A forced mark that never appears naturally is insufficient.

Held-out consequence

The commitment must transport across:

unseen durations;

unseen membership patterns;

unseen timing realizations.

A calendar or observable shortcut must fail.

4. Plural conjectures, counterexamples, retained lemmas
C-EHC

Claim:

Event-held commitment creates useful persistent behavior.

Evidence required:

positive G;

executable mark influence;

natural KEEP/RENEW consequences;

held-out transport.

C-REC

Claim:

Ordinary recurrence stores equivalent information.

Strong reduction:

Information-matched recurrent primitive controller.

Contradiction:

EHC wins under matched information and capacity.

C-BASE

Claim:

Shared base representation is insufficient.

Contradiction:

A stronger matched base succeeds without changing the causal treatment.

C-BENCH

Claim:

The benchmark determines identifiability.

Contradiction:

A source with the same mechanism but different causal structure repeatedly separates the hypotheses.

Strongest shortcut counterexamples

Timing shortcut

If duty follows a known clock:

time→action

commitment is unnecessary.

Observable-target shortcut

If target remains visible:

observation→action

no memory is needed.

Supplied executor shortcut

A hand-coded duty controller does not prove learned commitment.

Retained G0 lemmas

Valid no-access closes only the benchmark-comparator pair.

Operational validity and scientific validity are separate.

Forced behavior is not natural skill evidence.

Ordinary recurrence remains the mandatory reduction.

Integration requires natural use, intervention sensitivity, external value, and held-out transport.

5. Estimands and mutually exclusive outcomes
Access
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

passes access.

UCB
95
	​

(
a
max
	​

U
a
	​

)<0.80

means:

NO_ACCESS_THIS_G1_SOURCE
Mechanism

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

Link-null:

UCB
95
	​

(G)≤0.10
Branches
Branch	Smallest update
INVALID	Implementation/evidence validity only
SOURCE_NON_IDENTIFIABLE	Source definition invalid
NO_ACCESS	This G1 source inaccessible only
UNDERPOWERED	Evidence insufficient under frozen budget
COMMITMENT_SUPPORTED	EHC link supported in this source
REPRESENTATION_ONLY	Mark affects representation but not useful commitment
ORDINARY_EXPLANATION	EHC adds no value over matched recurrence
MIXED	Preserve unresolved explanations

No branch automatically integrates a mechanism.

6. One scheduled evidence action and reactivation conditions
Scheduled evidence object

The bounded evidence object is:

ACCESS_POSITIVE_MECHANISM_MATCHED_EHC_G1

with the frozen source contract above.

It is a scientific definition only.

It does not authorize:

implementation;

compute;

monitoring;

integration.

Reactivation conditions
C-EHC

Requires:

access;

positive G;

executable mark influence;

natural KEEP/RENEW consequences;

held-out benefit.

C-REC

Requires:

Matched recurrence achieves the same capability.

C-BASE

Requires:

A stronger base policy accesses the source.

C-BENCH

Requires:

The source fails to distinguish persistence from simpler explanations.

7. 中文简报

本轮完成的是 G1 source contract 的字段冻结，不是实现授权。

核心保持：

G0 永久关闭；

OR/DUM/EHC 不变；

G=U
EHC
	​

−U
DUM
	​

 不变；

K-bin、I
TV
	​

、C
total
	​

 battery 不变。

补全内容包括：

精确任务动力学；

actor/critic 信息边界；

外部 reward 与 utility；

train/held-out 分布；

access 与 identifiability 判断；

exposure、bootstrap、RNG 规则。

目标是让两个合理实现必须得到同一个科学对象。

仍未证明：

EHC 一定优于 ordinary recurrence；

learned commitment 一定形成 variable lifetime；

hierarchy 一定必要。

本回复不授权：

写代码；

启动实验；

分配计算；

集成算法。

它只冻结后续证据对象。
