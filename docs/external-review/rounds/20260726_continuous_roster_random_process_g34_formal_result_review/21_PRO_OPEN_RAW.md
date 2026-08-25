1. REGISTERED_RESULT_CONFORMANCE

Registered branch confirmed without modification:

SUPPORTED_BOUNDED_RANDOM_PROCESS_TRANSPORT_G34

The formal package is operationally and evidentially closed:

schema 2, formal=true, operational_valid=true, no operational errors;

exact G32 zero/final checkpoints, independently rebound by replicate, checkpoint kind, and configured capacity;

three replicates, 60 cells, 7,680 episodes, and 368,640 real 48-step transitions;

zero G34 optimizer steps and exact before/after checkpoint identity;

every conclusion-bearing quantity recomputed from serialized 48-step reward and actual roster-size traces;

correction-only code-science recheck returned AUDIT_DISPOSITION=ALIGNED;

the registered first-match selector was independently reproduced.

The primary result clears every frozen gate with material margin:

Quantity	Formal result	Frozen requirement
Random utility, capacity 6	[0.94248, 0.94724, 0.95081]	LCB >= 0.90
Random utility, capacity 8	[0.94938, 0.95306, 0.95585]	LCB >= 0.90
Random utility, capacity 12	[0.94379, 0.94650, 0.94910]	LCB >= 0.90
Lowest event-window LCB	0.91131	>= 0.85
Lowest process-segment LCB	0.91275	>= 0.85
Worst random-minus-fixed LCB	-0.00507	>= -0.05
Final-minus-zero learned gain	[0.34837, 0.53801, 0.66985]	LCB > 0
Random stochastic pooled	[0.88315, 0.88599, 0.88932]	LCB >= 0.80
Minimum random replicate mean	0.94691	>= 0.85

The random-minus-fixed result is a noninferiority result, not evidence that random membership processes improve performance.

2. SCIENTIFIC_DISPOSITION
scientific_disposition=
SUPPORTED_RETAINED_USABLE_CONFIGURED_CAPACITY_BOUNDED_RANDOM_PROCESS_CONTINUOUS_ROSTER_G34
Exact proposition added beyond G32

G32 established configured-capacity transport: one checkpoint trained only at capacity 8 remained usable when strict-loaded at capacities 6, 8, and 12 under the fixed G32 membership schedule. G34 now adds:

In the registered 48-step continuous-service toy family, the exact G32 final checkpoints transport with zero retraining from the fixed three-event process at steps 12/24/36 to the G34-P0 family of episode-random four-event processes, while retaining deterministic access, event-local and segment-local service, stochastic stability, positive final-minus-zero gain, and lifecycle correctness at configured capacities 6, 8, and 12.

The held-out process family contains exactly one each of:

L = temporary leave
R = rejoin
J = fresh join
T = terminal leave

with:

event times in steps 5..43;

minimum separation of five steps;

no event at a multiple of four or at the trained 12/24/36 times;

orders LRJT, LJRT, or JLRT;

the registered G32 cohort magnitudes and capacity-specific active-count trajectories;

configured packing capacity fixed before each trajectory.

Strongest supported interpretation

G31, G32, and G34 together now constitute a usable continuous dynamic-roster toy test version with three supported axes:

immediate and delayed service compatibility in the registered paired toy family;

strict-loadable configured-capacity transport across 6/8/12;

zero-shot transport from the fixed G32 schedule to the bounded G34 random-process family.

The result is stronger than parameter-shape compatibility: the same trained policy retains high natural utility after event time, event factorization, event order, and active-count trajectory are changed within the registered family.

Smallest retained units

Retain the following:

Capacity-generic parameterization. Maximum configured capacity need not enter learned actor or critic tensor shapes.

Active-set representation. Active-member summation, raw log1p(active_count), and active-fraction autoregressive prefixes remain usable under the registered capacity and process shifts.

Checkpoint transport. The capacity-8-trained G32 checkpoints retain behavior at configured capacities 6, 8, and 12 without adaptation.

Lifecycle implementation semantics. Temporary state freezes and restores, fresh lifecycle state begins at zero, terminal state is deleted, and unaffected survivors remain continuous under randomized event order and timing.

Bounded process generalization. The learned policy is not confined to the exact 12/24/36 schedule or atomic R+J event.

G31 provenance. The transporting checkpoint was trained with G31’s realized-future-tail and direction-balanced update. G34 preserves its usability but does not independently establish that credit rule as causally necessary.

Smallest retired alternative

Retire this exact explanation:

Within the G34-P0 source family, the G32 checkpoint is usable only because membership changes occur at steps 12/24/36 with an atomic R+J middle event.

The random source changes the event count from three to four, separates R and J, moves every event away from the trained event times and load-block boundaries, and changes their legal ordering. Performance remains essentially noninferior to the paired fixed reference.

Do not broaden that retirement to arbitrary schedule or process invariance.

3. COUNTEREXAMPLES_AND_EXCLUSIONS
Strongest remaining counterexample

The strongest remaining explanation is:

The policy may primarily be a true-time-conditioned, current-demand mapper with active-set scaling, rather than a controller whose success requires lifecycle recurrence or G31’s delayed-credit mechanism.

Current load and target mix are actor-visible and directly define the constructive action. G32’s formal mapping correlations exceed 0.9898, with MAEs below 0.0166. G34 proves that this mapping survives bounded random membership processes; it does not prove that recurrent state or realized-future-tail credit is responsible for that survival.

Time-rotation annotation: LOAD_BEARING

The capacity-8 time-rotation diagnostic produced:

utility CI95                 [0.89172, 0.89494, 0.89729]
rotated-minus-primary CI95  [-0.05962, -0.05808, -0.05675]
classification               LOAD_BEARING

Both upper bounds confidently miss the frozen utility/noninferiority boundaries. Therefore:

The exact G32 checkpoint behavior on G34-P0 depends materially on receiving the correct normalized absolute-time coordinate.

It does not establish:

that the policy memorizes 12/24/36—the G34 events never occur at those times;

that absolute time is universally required by the task;

that another policy could not learn the same source without time;

that time is the mechanism responsible for process transport;

that recurrence or G31 credit is unnecessary.

Rotating a trained input is an intervention on one checkpoint, not a matched time-free learning comparison. The primary G34 branch remains unchanged because true time is part of the frozen registered interface.

Reactive-ablation annotation: UNDERPOWERED

The capacity-8 reactive ablation produced:

utility CI95                 [0.84610, 0.88636, 0.91385]
reactive-minus-primary CI95 [-0.10782, -0.06660, -0.04201]
classification               UNDERPOWERED

Its interval crosses both the 0.90 access boundary and the -0.05 noninferiority boundary. It therefore establishes neither:

current-state sufficiency, nor

recurrent/history-state necessity.

Moreover, the intervention simultaneously zeroes recurrent hidden state, lifecycle age, and both previous-action fields. Even a confident loss would identify dependence on the combined history-bearing channel, not the unique necessity of a GRU or lifecycle-owned learned recurrence. A separately trained, information-matched current-state null is needed for that claim.

Explicit exclusions

G34 does not establish:

arbitrary membership-process laws;

repeated leave/rejoin cycles;

arbitrary event counts or edit types;

arbitrary cohort magnitudes or active counts;

horizons other than 48;

capacities outside 6, 8, and 12;

capacity changes during an active trajectory;

time-free robustness;

recurrence necessity;

G31-credit necessity;

superiority over a matched complete MARL controller;

UAV transport;

asynchronous skill lifetime;

environment-agnostic intrinsic-reward value.

G33 and its full-ledger/static-preposition lineage remain abandoned by direct user instruction and may not be renamed or reactivated.

4. CDC_PORTFOLIO_LEDGER_EDITS
4.1 Replace the complete C-CONTINUOUS-ROSTER block in CONJECTURES.md

The current block still ends at G32 and lists process-law variation as an unresolved counterexample. Replace it with:

Markdown
## C-CONTINUOUS-ROSTER — Continuous control under dynamic membership

- Status: supported and retained as a usable configured-capacity,
  bounded-random-process continuous dynamic-roster algorithm test version for
  the registered 48-step capacity-6/8/12 toy family. A finite packing capacity
  is selected before each trajectory.
- Claim: a G31 realized-future-tail and direction-balanced recurrent policy
  whose learned parameter shapes exclude maximum capacity can use one
  capacity-8-trained checkpoint at configured capacities 6, 8 and 12 while
  retaining within-episode temporary leave, rejoin, fresh join and terminal
  leave across both the fixed G32 process and the bounded held-out G34-P0
  random-process family.
- Formal immediate/delayed evidence: G31 passes the paired G17/G18 utility,
  spike-allocation, rotation, gain and fresh-seed stability gates.
- Formal configured-capacity evidence: G32 strict-loads the same capacity-8
  final checkpoints at capacities 6, 8 and 12 with zero evaluation optimizer
  steps. Utility LCBs are 0.95025, 0.93757 and 0.94832; the held-out gain LCB is
  0.36581, the minimum held-out replicate is 0.94284 and held-out stochastic
  mean is 0.87591.
- Formal bounded-process evidence: G34 evaluates those exact checkpoints with
  zero optimizer steps on one each of L/R/J/T, random event times in steps
  5--43, minimum five-step separation, no event at a four-step demand boundary,
  and orders LRJT/LJRT/JLRT. Capacity-6/8/12 deterministic utility LCBs are
  0.94248/0.94938/0.94379; minimum event-window and process-segment LCBs are
  0.91131 and 0.91275; the worst random-minus-fixed LCB is -0.00507 against the
  -0.05 noninferiority margin; learned-gain LCB is 0.34837; pooled stochastic
  LCB is 0.88315.
- Exact padding lemma: under the registered cap8/cap12 common-active process,
  observations, values, deterministic actions, rewards, hidden state and
  lifecycle transitions are exactly equal and added inactive rows remain zero.
- Retired alternatives: within the registered family, usable deployment at a
  new configured capacity does not require capacity-shaped learned parameters,
  retraining, checkpoint adapters, tensor slicing or key remapping; and usable
  behavior does not require the exact fixed 12/24/36 schedule or atomic R+J
  event of G32.
- Scope: horizon is 48; configured capacity is fixed within a trajectory and is
  one of 6/8/12; G34 covers exactly one each of L/R/J/T, the registered cohort
  magnitudes and three registered legal event orders. It is not an arbitrary
  process-law result.
- Strongest simpler explanation: current load and target mix directly determine
  the required action, and the exact checkpoint also depends materially on the
  correct absolute-time coordinate. Bounded process transport may therefore be
  largely reactive rather than recurrence- or delayed-credit-dependent.
- Diagnostic boundary: G34 time rotation is LOAD_BEARING for the exact
  checkpoint, while the reactive ablation is UNDERPOWERED. Neither diagnostic
  selects recurrence or G31-credit necessity.
- Code-only boundary: live in-trajectory tensor-width rebinding remains a
  packing/state-migration issue unless future protected scope removes the
  pre-trajectory capacity bound.
- UAV boundary: temporary-service-loss G1 and charge-rotation G2 remain source
  non-identifiable. G33 and its derivatives are abandoned by user instruction.
- Exclusions: arbitrary capacity, arbitrary or repeated membership processes,
  random horizon, time-free robustness, UAV usability, asynchronous skill
  lifetime, intrinsic-reward advantage, comparative superiority and causal
  necessity of either recurrence or G31 credit remain unsupported.
4.2 Add this bullet to C-REC

The current entry establishes ordinary recurrence in the earlier exact memory sources but says nothing about the G34 diagnostic. Add:

Markdown
- Continuous-roster update: G34 does not select recurrence necessity. The
  zero-history reactive ablation is UNDERPOWERED, while rotation of the true
  time coordinate is LOAD_BEARING for the exact checkpoint. A freshly trained,
  information-, capacity-, credit- and exposure-matched current-state
  feedforward null is required to distinguish learned recurrent-state value
  from direct current-state mapping.
4.3 Add this bullet to C-CREDIT

The current entry ends by treating UAV transport as the remaining discriminator. G34 is a zero-training transport result, not a credit comparison. Add:

Markdown
- G34 update: a checkpoint trained with G31 credit transports to the bounded
  G34-P0 process family, but G34 performs zero optimization and contains no
  matched credit comparator. It therefore adds checkpoint-usability evidence,
  not causal evidence that realized-future-tail credit is necessary. C-CREDIT
  remains supported only inside the registered G17/G18 paired toy family.
4.4 Replace affected rows in IDEA_PORTFOLIO.md

The current C-CONTINUOUS row and terminal block still point to G32 and abandoned G33. Replace the three affected rows with:

Markdown
| C-CONTINUOUS-ROSTER | supported retained: usable configured-capacity bounded-random-process continuous-roster test version | Formal G31 closes the paired immediate/delayed toy contract; G32 adds strict-loadable capacity-6/8/12 transport and exact padding invariance; G34 adds zero-shot transport to the registered random four-event process with strong utility, event-window, segment, gain and stochastic gates. | Next action: a matched reactive/current-state reduction design audit. Arbitrary processes, horizons, time-free robustness, UAV transport and causal necessity of recurrence or G31 credit remain open. |
| C-REC | selected for exact G1/G2; unresolved for the G34 continuous-roster source | G34 primary transport passes, but its reactive ablation is UNDERPOWERED and cannot establish either current-state sufficiency or recurrent-state necessity. | Compare freshly trained recurrent and current-state/feedforward policies under identical information, G31 credit, capacity, interactions and optimizer exposure. |
| C-CREDIT | supported on paired toys; necessity unresolved outside them | Formal G31 establishes usability on G17/G18. G34 transports a G31-trained checkpoint with zero additional optimization, so it supplies no matched evidence that the credit rule is causally necessary for process transport. | Reactivate only through a representation-fixed, information- and exposure-matched credit-only comparison; do not infer necessity from G34. |

Replace the terminal block with:

completed_action=CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_FORMAL_ITERATION_25
source_family=CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_P0
formal_disposition=SUPPORTED_BOUNDED_RANDOM_PROCESS_TRANSPORT_G34
scientific_disposition=SUPPORTED_RETAINED_USABLE_CONFIGURED_CAPACITY_BOUNDED_RANDOM_PROCESS_CONTINUOUS_ROSTER_G34
next_action=CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_DESIGN_ASSERTION_AUDIT
authorization_status=active_twenty_iteration_toy_first_uav_promotion_chain
conclusion_bearing_iterations_consumed=25
iterations_remaining=12

Replace the final G32/G33 paragraph with:

Markdown
Formal G32 supports one capacity-8-trained checkpoint at configured capacities
6, 8 and 12 with exact common-active padding invariance and zero evaluation
optimizer steps. After the user abandoned G33 without a scientific result,
formal G34 froze the G32 checkpoints and established zero-shot transport from
the fixed 12/24/36 process to the registered four-event random-process family.
G34 retires dependence on that exact fixed schedule inside P0, but its
time-rotation diagnostic is LOAD_BEARING and its reactive ablation is
UNDERPOWERED. It therefore does not establish recurrence or G31-credit
necessity. The next scientific action is
`CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_DESIGN_ASSERTION_AUDIT`.
4.5 Update RESEARCH_DIRECTION_LEDGER.md

Replace the existing configured-capacity row with:

Markdown
| 连续动态 roster 的跨配置容量与有界随机过程复用 | `SUPPORTED_RETAINED` | G31/G32/G34 在已登记 48-step continuous-service toy family 中形成可用测试版：同一 capacity-8 训练 checkpoint 可无适配 strict-load 到配置容量 6/8/12，并在固定 G32 process 与 G34-P0 的四事件随机时间/顺序 process 上保持高 utility、event-window、segment、stochastic 与 learned-gain 表现。容量须在 trajectory 前选定。 | 不能推出 live tensor-width rebinding、capacity 6/8/12 外的规模、任意/重复 membership process、随机 horizon、time-free robustness、UAV transport、技能生命周期、内在奖励增益、比较优势、recurrence 或 G31 credit 的独立必要性。 | [G32 正式结果](EVIDENCE_NOTES/20260725_RUNTIME_CAPACITY_INVARIANT_CONTINUOUS_ROSTER_G32_FORMAL_RESULT.md)；[G34 正式结果](EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_RANDOM_PROCESS_G34_FORMAL_RESULT.md)；[第 25 轮报告](../../report/ITERATION_25.md) |

Replace the current UAV-transport open row with:

Markdown
| G31/G32/G34 向非 G33、可识别 UAV source 的 transport | `OPEN_UNTESTED` | 在物理可行、目标行为 load-bearing 且 source-identifiable 的非 G33 UAV source 上，已支持的 continuous-roster representation、bounded-process transport 与 realized-future-tail checkpoint 是否保持可用。 | UAV temporary-loss G1 与 charge-rotation G2 均在 learned training 前因 source 不可识别关闭；G33 由用户直接放弃且禁止复活；尚无可判别的 UAV transport 结果。 |

Replace the broad process/horizon row with:

Markdown
| 超出已登记边界的 active count、membership process 与 horizon | `OPEN_UNTESTED` | 已支持表示在 N>80、configured capacity 6/8/12 之外、重复 leave/rejoin、不同 event count/type、任意过程律与 horizon≠48 时的边界。 | G34 只覆盖一个 each-of-L/R/J/T、三种顺序、五步最小间隔和 H=48 的有界 process family。 |

Add this row under the frozen directions:

Markdown
| UAV localized-demand-burst G33 及其 full-ledger/static-preposition 衍生线 | `OUT_OF_SCOPE_FROZEN` | 用户直接放弃并禁止重命名或复活该 lineage。 | 这是范围决定，不是 source 或算法的科学失败；不得由后续 G34 结果改写。 |

Replace longitudinal summary item 5 with:

Markdown
5. G32 正式支持同一 capacity-8 训练 checkpoint 在配置容量 6/8/12 间
   strict-load 复用；G34 进一步以零训练证明该 checkpoint 从固定
   12/24/36 process 迁移到已登记四事件随机时间/顺序 family。固定日程依赖
   在该 P0 范围内关闭，但 true-time rotation 为 LOAD_BEARING，reactive
   ablation 为 UNDERPOWERED，因此 recurrence 与 G31 credit 的必要性仍未
   识别。下一科研边界是 matched current-state reduction 的 G35 design audit。

No change is warranted to ALGORITHM_PRINCIPLES.md: G34 is a bounded local result and does not add a new cross-experiment scientific rule.

5. ONE_NEXT_ACTION
CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_DESIGN_ASSERTION_AUDIT
Scientific distinction

The next question is not whether G34 transports—it does. The remaining decision-relevant ambiguity is:

lifecycle-owned learned recurrence
versus
a strong true-time-conditioned current-state controller

The existing reactive intervention cannot decide this because it is underpowered and simultaneously removes several history-bearing inputs from a policy trained to use them.

Why this is the cheapest discriminating action

A matched reduction design audit is cheaper and more informative than the alternatives:

Cheaper than another UAV source: it reuses the already identified G32/G34 source rather than risking a third source-identifiability failure.

Cheaper than horizon/capacity expansion: it changes one mechanism edge rather than broadening several deployment axes while attribution remains unresolved.

More discriminating than another frozen-state intervention: a freshly trained current-state null can adapt to the absence of recurrent hidden state; zeroing a trained recurrent model remains an out-of-distribution perturbation.

Cleaner than a credit comparison: holding G31 credit fixed isolates recurrence first. A simultaneous credit change would confound representation and optimization.

Decision-changing: a successful matched current-state null would reduce the accepted algorithm to a simpler controller; a material recurrent advantage would support carrying lifecycle-owned neural state into later promotion work.

The action is a zero-compute design audit, not an implementation or experiment.

6. EXECUTABLE_SCIENTIFIC_BOUNDARY
next_boundary=
CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_DESIGN_ASSERTION_AUDIT
One exact audit question

Can a conclusion-bearing matched comparison be frozen in which fresh paired recurrent and current-state/feedforward policies are trained on the unchanged G32 capacity-8 training source and evaluated on the unchanged G34-P0 fixed/random capacity-6/8/12 cells, with identical actor-visible current fields, centralized critic information, active-set aggregation, autoregressive prefix, action distribution, G31 credit rule, parameter count, environment interactions, optimizer exposure, initialization pairing and final-checkpoint rule—while the only causal difference is whether the actor carries a learned recurrent hidden state across primitive steps and lifecycle boundaries?

Non-negotiable inherited boundary
H=48
train_source=unchanged_G32_capacity8_fixed_process
heldout_source=unchanged_G34_P0_capacity6_8_12
reward=unchanged
true_time_field=retained_in_both_arms
lifecycle_age_and_previous_actions=retained_in_both_arms
credit=identical_G31_realized_future_tail
new_reward_or_intrinsic=forbidden
uav_scope=excluded
g33_reactivation=forbidden

The strong current-state null must retain all current information, including true normalized time, lifecycle age, previous actions, load, target mix, capabilities, active count, and action prefix. Otherwise a recurrent advantage could be manufactured through information removal.

Fresh paired training of both arms is required. Existing G32 checkpoints may be reported as historical references but cannot serve as the causal recurrent comparator after the architecture changes.

Decisions the design audit must freeze

The design audit must return one exact contract specifying:

the feedforward/current-state actor graph and exact parameter-matching rule;

recurrent and current-state training exposure;

fresh paired seed blocks;

absolute source-access gates for both arms;

primary estimand

Δ
rec
	​

=U
recurrent
	​

−U
current-state
	​

;

a frozen materiality or noninferiority margin;

deterministic/stochastic and event-window/segment requirements;

hierarchical whole-episode confidence construction;

final-checkpoint-only selection;

mutually exclusive branches for:

operational invalidity;

source or common access failure;

current-state reduction sufficiency;

recurrent-state advantage;

mixed/underpowered evidence.

It must also contain a positive representational witness showing that the current-state null can express the registered constructive load/mix mapping. Otherwise null failure would not identify recurrence.

Complexity boundary
design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_bound=0
nested_rollout=false
replanning=false

Any later bounded realization must remain within:

nonformal_wall_clock<=20_minutes
formal_train_evaluate_analyze_wall_clock<=8_hours

File names, tensor storage, vectorization, serialization, telemetry layout, and proof-sized test organization are implementation-only. The null architecture, parameter matching, observations, credit, exposure, estimand, margin, seeds, confidence unit, and first-match order are scientific and may not be selected locally by PM. The design-audit requirement follows because this action creates a new comparator, architecture distinction, estimand, and result branches.

7. 中文简报

G34 的正式分支应原样接受：

SUPPORTED_BOUNDED_RANDOM_PROCESS_TRANSPORT_G34

它在 G32 之上新增的最强结论是：

只在 capacity 8 和固定 12/24/36 roster 日程上训练的同一组 checkpoint，不需要重训，就能在 capacity 6、8、12 上迁移到已登记的四事件随机 process：每个 episode 各有一次 leave、rejoin、fresh join 和 terminal leave，事件时间与顺序均未在训练中出现。

三种 capacity 的 deterministic utility 下界都高于 0.94 左右，event-window 和 process-segment 下界都高于 0.91，相对固定日程的最差下界只有 -0.00507，远高于 -0.05 的 noninferiority 边界。因此，在这个精确 P0 family 内，可以关闭：

checkpoint 只有依赖固定 12/24/36 时间表和 atomic R+J 才能工作。

但不能写成“任意 process 都能泛化”。当前只覆盖：

H=48；

capacity 6/8/12；

每类事件一次；

三种顺序；

事件间隔至少五步；

没有重复 leave/rejoin；

trajectory 开始前固定 packing capacity。

两个诊断必须单独解释：

TIME_ROTATED=LOAD_BEARING：当前 checkpoint 明确依赖正确的 absolute time 输入；这不等于它记忆固定 membership 事件，也不证明所有策略都需要时间。

REACTIVE_ABLATION=UNDERPOWERED：当前证据既不能证明 current-state mapping 已足够，也不能证明 recurrence 必要。该 ablation 同时删除 hidden、age 和 previous action，因此不是干净的 recurrence comparator。

最强剩余简单解释是：

该策略主要是一个使用 current load、target mix、active-set 信息和真实时间的直接映射器；recurrence 与 G31 credit 未必是 transport 的必要原因。

下一项科研动作选择：

CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_DESIGN_ASSERTION_AUDIT

它将先冻结一个真正匹配的 current-state/feedforward 强对照：

两个 arm 都重新配对训练；

observation、critic、active-set、action prefix、参数量、G31 credit、环境交互和 optimizer exposure 相同；

只删除 learned recurrent hidden state；

true time、age 和 previous actions仍对两个 arm 可见。

这样才能回答 recurrence 是否真的增加能力，而不是继续对已训练 recurrent checkpoint 做破坏性 ablation。

G33 及其衍生线继续保持用户放弃、禁止复活。本裁决不授权代码、Git、实验或计算。
