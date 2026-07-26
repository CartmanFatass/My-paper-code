1. REGISTERED_RESULT_CONFORMANCE

Registered branch confirmed without modification:

HISTORY_PROXY_FREE_CHECKPOINT_SUFFICIENT_G36

The formal package is operationally and evidentially closed:

formal=true, status=COMPLETE, operational_valid=true, and no operational errors;

one CPU-only execution using PyTorch 2.7.0+cpu with one thread;

no retry, resume, restart, fallback, mixed backend, or second formal run;

three replicates, configured capacities 6/8/12, 36 intervention cells, 4,608 episodes, and 221,184 real transitions;

zero training transitions and zero optimizer steps;

10,000 paired hierarchical bootstrap resamples;

exact G35 formal-artifact, CS-final-checkpoint, source, episode, donor-tape, action-stream, lifecycle, trace, preflight, and digest closure;

the correction-only code-science recheck returned AUDIT_DISPOSITION=ALIGNED;

PM independently regenerated the confidence procedure and reproduced the frozen first-match branch.

The conclusion-bearing values are:

Quantity	Formal result	Frozen requirement
Fixed utility, capacity 6	[0.947629, 0.951388, 0.956718]	LCB >=0.90
Fixed utility, capacity 8	[0.948735, 0.953464, 0.956721]	LCB >=0.90
Fixed utility, capacity 12	[0.932095, 0.945422, 0.952937]	LCB >=0.90
Random utility, capacity 6	[0.950706, 0.953849, 0.958048]	LCB >=0.90
Random utility, capacity 8	[0.949618, 0.953375, 0.956126]	LCB >=0.90
Random utility, capacity 12	[0.931118, 0.944511, 0.951948]	LCB >=0.90
Fixed stochastic pooled	[0.877366, 0.884965, 0.889512]	LCB >=0.80
Random stochastic pooled	[0.883551, 0.891270, 0.895999]	LCB >=0.80
Minimum fixed/random replicate mean	0.942637 / 0.943628	each >=0.85
Primary registered-minus-substitution delta	[-0.002479, 0.000105, 0.003575]	UCB <=0.05
Largest deterministic utility-delta UCB	0.007529	<=0.05
Largest event/segment-delta UCB	0.005266	<=0.05
Fixed/random stochastic-delta UCB	0.001926 / 0.002033	each <=0.05

Thus:

registered_source_access_valid=true
intervention_access_pass=true
intervention_access_confident_fail=false
proxy_noninferior=true
material_proxy_loss=false

The registered-minus-intervention difference is defined as:

Δ
HP
	​

=U
registered
	​

−U
donor-substituted
	​

.

Its primary interval crosses zero, but its upper endpoint is only 0.003575, and every component upper bound is at most 0.007529. The result therefore strongly excludes the frozen 0.05 material benefit for the actual bundle; it does not establish superiority in either direction.

2. SCIENTIFIC_DISPOSITION
scientific_disposition=
SUPPORTED_RETAINED_BOUNDED_ACTUAL_HISTORY_SENSOR_BUNDLE_SUBSTITUTION_G36
Exact proposition added beyond G35

G35 established that learned cross-step actor carry is not required in its fully informed P0 comparison. G36 now adds:

For the exact three formal G35 CS final checkpoints, in the registered 48-step G32 fixed-process and G34-P0 bounded-random-process family at configured capacities 6, 8, and 12, the actor’s actual normalized physical time, lifecycle age, and two actual previous-action values may be replaced by the frozen active-count-conditioned, source-valid donor-bundle generator while retaining every registered absolute-access gate and remaining noninferior to registered execution by the frozen 0.05 margin.

The substituted actor continues to receive its actual:

capability coordinates;

anonymous priority;

current load;

current target mix;

raw log1p(active_count);

active mask;

active-fraction autoregressive prefix.

The centralized critic remains unchanged and continues to receive its true current state, including true normalized physical time. Lifecycle ownership, source state, reward, checkpoint tensors, and action streams are also unchanged.

The donor generator is not arbitrary noise. It constructs complete simultaneous active-roster bundles from fresh G32 fixed and G34 random ledgers, using legal lifecycle age and constructive previous-action histories, groups them only by current active count, and assigns independently selected and anonymously permuted donor rows to target active members. The donor selection is independent of the target’s actual time, age, previous actions, event identity, load/mix, reward, checkpoint output, and action noise, conditional only on the retained current mask and count.

Strongest supported deployment statement

Within that exact boundary:

An actor deployment does not need to acquire the actual four-field clock/age/action-history sensor bundle, provided the actor’s four existing input coordinates are populated by the exact frozen G36 surrogate generator.

The formal evidence closed the required stronger invariant:

actual_age_read_count=0
actual_previous_action_read_count=0
actual_actor_time_read_count=0
critic_transform_count=0
checkpoint_update_count=0

The corrected evaluator constructs a new actor tensor from source coordinates 0:6 only and writes the surrogate directly into coordinates 6:10; the actual active-row history fields are not first materialized or validated.

What this is not

This is sensor substitution, not architectural deletion. G36 does not support:

changing the trained actor from ten input coordinates to six;

deleting or zeroing the learned weights attached to coordinates 6:10;

filling those coordinates with zeros, constants, arbitrary noise, or another unreviewed distribution;

claiming that every retrained policy can omit history;

removing active masks or lifecycle state;

describing the task family as globally memoryless;

removing the critic’s true-time field.

The registered branch name must therefore be read as “free of the target’s actual history bundle under the frozen donor law,” not as “free of all history-shaped actor inputs.” The original design explicitly imposed this claim ceiling.

Smallest retired unit

Retire exactly:

In G36-P0, the exact formal G35 CS final checkpoints require the target episode’s actual, target-coherent actor bundle of true time, lifecycle age, and two previous actions for registered access, or derive a material utility benefit greater than 0.05 from that actual bundle relative to the frozen G36 donor substitute.

This includes the narrower deployment claim that those actual sensors must be acquired for these checkpoints.

It does not retire the possible need for:

the four model coordinates;

a source-supported filler distribution;

joint coherence within the surrogate bundle;

any individual field in another source or after retraining.

3. COUNTEREXAMPLES_AND_EXCLUSIONS
Strongest remaining counterexample

The strongest remaining explanation is now:

The checkpoints may be insensitive to the identity of the target history while still depending on receiving a plausible, jointly coherent, active-count-conditioned history-shaped bundle that keeps their input inside the learned source distribution.

G36’s donor preserves within-snapshot relationships among:

normalized physical time;

lifecycle ages across the active roster;

previous-action coordinates;

fresh-join and rejoin patterns;

active-count-specific roster structure.

It destroys their connection to the target episode’s history, but it does not destroy donor-internal coherence. Therefore G36 separates actual-history dependence from source-valid-surrogate dependence; it does not yet separate marginal support from joint donor coherence.

The direct source structure remains an additional simpler explanation. Current load and target mix specify an access-level constructive action, so the task never required hidden temporal information for optimal control. G35 already contained a no-carry current-state witness with minimum utility 0.94048 over the complete registered load/mix support.

Interpretation of the intervals

The primary interval is:

[−0.002479, 0.000105, 0.003575].

Because it crosses zero:

G36 does not establish that donor substitution improves performance;

G36 does not establish that actual-history execution is better;

tiny effects in either direction remain compatible with the evidence.

Its width is approximately 0.00605. Under the registered sign convention, the interval permits the donor execution to be better by roughly 0.00248, or registered execution to be better by roughly 0.00357. Both are much smaller than the frozen 0.05 materiality margin.

The component results reinforce noninferiority but do not prove exact invariance:

the largest deterministic utility-delta UCB is 0.007529;

the largest event-window or process-segment delta UCB is 0.005266;

stochastic delta UCBs are about 0.002.

These bounds exclude a registered advantage of five utility points in every conclusion-bearing dimension. They do not establish zero dependence, identical action distributions, or equality on every individual episode.

Retained units

Retain:

Current task information. Current load, target mix, capabilities, anonymous priority, active count, mask, and within-step action prefix remain part of the supported actor interface.

Active-set representation. Capacity-independent member encoding, active-member aggregation, raw log count, and prefix-normalized autoregression remain supported.

Lifecycle semantics. JOIN, temporary leave, rejoin, fresh initialization, terminal deletion, survivor continuity, likelihood ownership, and environment-maintained lifecycle state remain protected.

Bounded donor law. The exact G36 source-valid donor bank, active-count conditioning, anonymous row permutation, and surrogate tape remain part of the positive result.

Critic contract. The centralized critic and its true-time coordinate were not intervened upon.

Training provenance. The checkpoints were trained with G31 realized-future-tail credit; G36 performs no training and cannot identify that credit rule’s necessity or redundancy.

Capacity and process scope. Only H=48, configured capacities 6/8/12, G32’s fixed process, and G34-P0’s one-each-of-L/R/J/T bounded random processes are supported.

Retraining uncertainty. Whether a freshly trained six-coordinate actor can remove these coordinates architecturally remains untested.

Explicit exclusions

G36 does not establish:

safe use of constants, zeros, means, arbitrary independent noise, or another donor distribution;

that the learned weights connected to coordinates 6:10 are zero or behaviorally irrelevant;

that time, age, and previous actions are individually redundant;

that a six-input model would learn or retain access;

that all current-state policies are history independent;

arbitrary capacities, horizons, active counts, edit counts, repeated leave/rejoin cycles, or process laws;

G31-credit redundancy;

complete-algorithm superiority;

UAV transport;

asynchronous skill lifetime;

intrinsic-reward benefit.

G33 and its full-ledger/static-preposition lineage remain abandoned by direct user instruction and may not be renamed or reactivated.

4. CDC_PORTFOLIO_LEDGER_EDITS
4.1 Replace the complete C-CONTINUOUS-ROSTER block in CONJECTURES.md

The current block ends at G35 and still lists history-proxy-free robustness as unresolved. Replace it with:

Markdown
## C-CONTINUOUS-ROSTER — Continuous control under dynamic membership

- Status: supported and retained as a usable actual-history-sensor-substituted,
  configured-capacity, bounded-random-process continuous dynamic-roster test
  version for the registered 48-step capacity-6/8/12 toy family. A finite
  packing capacity is selected before each trajectory.
- Claim: a capacity-shape-independent no-carry actor trained only at capacity 8
  remains usable at configured capacities 6, 8 and 12 across the fixed G32
  process and bounded G34-P0 random process. For its exact formal G35 CS final
  checkpoints, the actor's actual true-time, lifecycle-age and previous-action
  sensor bundle may be replaced by the frozen G36 active-count-conditioned,
  source-valid donor generator.
- Retained actual actor information: capability, anonymous priority, current
  load and target mix, raw log1p(active_count), active mask and active-fraction
  autoregressive prefix.
- Retained surrogate interface: the four actor coordinates for age, two previous
  actions and time remain present and are populated by the exact G36 donor law.
  This is sensor substitution, not ten-to-six-dimensional architectural
  deletion.
- Formal immediate/delayed evidence: G31 passes the paired G17/G18 utility,
  spike-allocation, rotation, gain and fresh-seed stability gates.
- Formal configured-capacity evidence: G32 strict-loads one capacity-8-trained
  recurrent checkpoint family at capacities 6, 8 and 12 and establishes exact
  common-active padding invariance.
- Formal bounded-process evidence: G34 transports those checkpoints without
  retraining from the fixed 12/24/36 process to one each of L/R/J/T at random
  held-out times and orders.
- Formal current-state reduction evidence: G35 freshly trains matched REC and CS
  arms. Both access; pooled REC-minus-CS CI95 is
  [-0.0173505, -0.0081213, 0.0007130], and every capacity-specific UCB is at
  most 0.0054082 against the 0.05 margin.
- Formal actual-history substitution evidence: G36 freezes the exact G35 CS
  finals and replaces actor time, age and two previous-action fields with an
  independent source-valid donor bundle. Fixed/random capacity-6/8/12 utility,
  stochastic, event-window, process-segment, transport and replicate-stability
  gates all pass. The primary registered-minus-substitution CI95 is
  [-0.0024790, 0.0001048, 0.0035749]; the largest conclusion-bearing component
  UCB is 0.0075287 against the 0.05 margin.
- Retired alternatives: within the registered family, usable deployment does
  not require capacity-shaped learned parameters, capacity-specific retraining,
  checkpoint adapters, the exact fixed 12/24/36 schedule, atomic R+J, learned
  per-lifecycle actor carry, or acquisition of the target episode's actual
  time/age/previous-action sensor bundle for the exact G35 CS checkpoints.
- Lifecycle boundary: active masks, likelihood ownership, environment lifecycle
  state, fresh initialization, temporary leave/rejoin, terminal deletion and
  survivor continuity remain part of the runtime contract.
- Scope: H=48; configured capacity is fixed within a trajectory and belongs to
  6/8/12; G34-P0 contains one each of L/R/J/T and three legal event orders; G36
  uses the exact frozen donor distribution. This is not arbitrary process or
  arbitrary filler robustness.
- Strongest remaining explanation: the checkpoints may need only a plausible
  active-count-conditioned history-shaped nuisance bundle. G36 removes target
  history but preserves donor-internal time/age/action coherence.
- Critic and credit boundary: the critic retains true time, and all checkpoints
  retain G31 training provenance. G36 performs no training and supplies no
  credit-comparator evidence.
- UAV boundary: temporary-service-loss G1 and charge-rotation G2 remain source
  non-identifiable. G33 and all derivatives remain abandoned by user
  instruction.
- Exclusions: arbitrary capacity/process/horizon, donor-law invariance,
  architectural coordinate deletion, globally memoryless control, UAV
  usability, asynchronous skill lifetime, intrinsic-reward advantage,
  complete-algorithm superiority and G31-credit redundancy remain unsupported.
4.2 Replace the complete C-REC block in CONJECTURES.md

The current entry closes learned carry but still treats the actual history fields as retained unresolved inputs. Replace it with:

Markdown
## C-REC — Ordinary recurrence is sufficient

- Status: selected as a sufficient capability in the exact G1/G2 memory
  sources, while learned actor carry is rejected as load-bearing in G35-P0 and
  target-coherent actor history sensors are replaceable for the exact G35 CS
  checkpoints under the frozen G36 donor law.
- Memory-source claim: a matched recurrent MARL controller can represent useful
  persistence without explicit event-held commitment when task-relevant
  information is absent from the current observation.
- Continuous-roster carry result: G35 compares parameter-identical REC and CS
  arms under identical current information, G31 credit, source, interactions
  and optimizer exposure. Both access; every REC-minus-CS UCB is at most
  0.0054082 against the 0.05 margin.
- Continuous-roster sensor result: G36 replaces the exact CS checkpoints'
  actual time, age and previous-action bundle with a target-history-independent,
  source-valid donor bundle. All access gates pass and the primary
  registered-minus-substitution UCB is 0.0035749.
- Smallest retired units: learned cross-step actor carry is not required or
  materially advantageous in G35-P0; the target episode's actual coherent
  history bundle is not required or materially advantageous for those exact
  CS checkpoints under G36-P0.
- Retained distinction: G36 preserves four history-shaped model coordinates, a
  source-valid donor generator, active masks, lifecycle ownership and the
  centralized critic. It does not establish that the task or all policy classes
  are memoryless.
- Reactivation condition: an identified source with task-relevant sequential
  information absent from current observations, followed by a matched material
  recurrent advantage. More seeds, budget or threshold changes on G35/G36-P0
  are not reactivation evidence.
4.3 Add this bullet to C-CREDIT
Markdown
- G36 update: G36 freezes the G35 CS final checkpoints and performs zero
  optimization. Actual-history sensor substitution therefore adds no evidence
  about whether G31 realized-future-tail credit was necessary for learning the
  checkpoints or can be replaced. C-CREDIT remains supported only by its
  registered paired G17/G18 evidence.

No other conjecture block changes.

4.4 Replace the affected rows in IDEA_PORTFOLIO.md

The current portfolio and terminal block still point to G36 as unresolved. Replace the three affected rows with:

Markdown
| C-CONTINUOUS-ROSTER | supported retained: bounded actual-history-sensor-substituted configured-capacity random-process continuous-roster test version | G31 closes the paired immediate/delayed toy contract; G32 adds capacity-6/8/12 transport; G34 adds bounded random-process transport; G35 removes learned actor carry; G36 shows that the exact G35 CS finals retain all registered access and noninferiority gates when actual actor time, age and previous actions are replaced by the frozen source-valid donor generator. | Next action: separate dependence on the G36 donor's joint time/age/action coherence from dependence on marginal in-support filler values. Architectural deletion, arbitrary filler robustness, UAV transport and G31-credit necessity remain open. |
| C-REC | sufficient in exact memory sources; learned carry and actual target-history acquisition closed as load-bearing in G35/G36-P0 | G35 closes a >0.05 REC advantage. G36 primary registered-minus-substitution CI95 is [-0.0024790, 0.0001048, 0.0035749], and the largest component UCB is 0.0075287. | Reactivate recurrence only on an identified source containing task-relevant information absent from current observations. G36 does not support global memorylessness or deletion of the four model coordinates. |
| C-CREDIT | supported on paired toys; necessity unresolved outside them | G36 performs zero optimization on checkpoints trained with G31 credit and therefore isolates only execution-time actor inputs. | Reactivate only through a representation-, information- and exposure-matched credit-only comparison. |

Replace the terminal block with:

completed_action=CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_FORMAL_ITERATION_27
source_family=CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_P0
formal_disposition=HISTORY_PROXY_FREE_CHECKPOINT_SUFFICIENT_G36
scientific_disposition=SUPPORTED_RETAINED_BOUNDED_ACTUAL_HISTORY_SENSOR_BUNDLE_SUBSTITUTION_G36
next_action=CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_DESIGN_ASSERTION_AUDIT
authorization_status=active_twenty_iteration_toy_first_uav_promotion_chain
conclusion_bearing_iterations_consumed=27
iterations_remaining=10

Replace the final continuous-roster paragraph with:

Markdown
Formal G32 supports capacity-6/8/12 strict-load and padding invariance. Formal
G34 transports the checkpoints from the fixed 12/24/36 process to the bounded
four-event random-process family. Formal G35 freshly compares matched REC and
CS arms and closes learned actor carry as required or materially advantageous
inside P0. Formal G36 then freezes the exact G35 CS final checkpoints and
selects `HISTORY_PROXY_FREE_CHECKPOINT_SUFFICIENT_G36`: actual actor time,
lifecycle age and previous actions can be replaced by the frozen independent
source-valid donor bundle while all fixed/random capacity-6/8/12 access gates
pass. The primary registered-minus-substitution CI95 is
[-0.0024790, 0.0001048, 0.0035749], and every component UCB is below 0.00753
against the 0.05 margin. This closes acquisition of the target's actual coherent
history bundle, but retains the four model coordinates, donor-law coherence,
critic true time and G31 training provenance. The next scientific action is
`CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_DESIGN_ASSERTION_AUDIT`.
4.5 Update RESEARCH_DIRECTION_LEDGER.md

Replace the supported continuous-roster row with:

Markdown
| 连续动态 roster 的跨容量、随机过程、current-state 与实际历史传感替代 | `SUPPORTED_RETAINED` | G31/G32/G34/G35/G36 在已登记 48-step toy family 中形成可用测试版：capacity-8 训练模型可在配置容量 6/8/12 与固定/有界随机 roster process 上保持 access；G35 关闭 learned actor carry；G36 进一步表明，对 exact G35 CS final checkpoints，actor 的真实 time、age 与 previous-action bundle 可由冻结的 active-count-conditioned source-valid donor generator 替代，全部绝对门槛与 0.05 noninferiority 门槛通过。 | 不能推出十维到六维的结构删除、任意常数/噪声替代、donor-law 不变性、全局 memoryless、任意容量/过程/horizon、UAV transport、G31 credit 冗余或技能生命周期。 | [G35 正式结果](EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_REACTIVE_REDUCTION_G35_FORMAL_RESULT.md)；[G36 正式结果](EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_FORMAL_RESULT.md)；[第 27 轮报告](../../report/ITERATION_27.md) |

Add under 已失败并关闭的精确方向:

Markdown
| G36-P0 中目标真实/一致 history bundle 对 exact G35 CS checkpoint access 或 >0.05 material benefit 的必要性 | `FAILED_CLOSED` | 替换真实 time、lifecycle age 与两个 previous actions 后，fixed/random capacity-6/8/12 的全部 access 门槛通过；primary registered-minus-substitution CI95 为 [-0.0024790, 0.0001048, 0.0035749]，最大 component UCB 为 0.0075287。目标 episode 的真实 coherent bundle 在该精确边界内不是 load-bearing。 | “四个模型坐标可以删除”“任意 filler 都安全”“所有任务都无记忆”“critic 或 lifecycle state 不需要”。 | [G36 正式结果](EVIDENCE_NOTES/20260726_CONTINUOUS_ROSTER_HISTORY_PROXY_FREE_CS_G36_FORMAL_RESULT.md)；[第 27 轮报告](../../report/ITERATION_27.md) |

Replace the current open history-proxy row with:

Markdown
| G36 donor bundle 的 joint coherence 是否 load-bearing | `OPEN_UNTESTED` | 在保持每个 history-proxy 坐标的 active-count-conditioned empirical marginal 与合法 support 时，破坏 time/age/previous-action 的跨坐标、跨成员 joint coherence，exact G35 CS checkpoints 是否仍保持 access 与 0.05 noninferiority。 | G36 只证明目标真实 history 可被一个内部 coherent 的 source-valid donor snapshot 替代；尚未证明任意 marginally in-support surrogate 已足够。 |

Replace the UAV-transport row with:

Markdown
| G36 简化 continuous-roster controller 向非 G33、可识别 UAV source 的 transport | `OPEN_UNTESTED` | 在物理可行、目标行为 load-bearing 且 source-identifiable 的非 G33 UAV source 上，current-state representation、bounded-process transport、实际历史传感替代与 G31 credit 是否保持可用。 | UAV G1/G2 在 learned training 前因 source 不可识别关闭；G33 被用户放弃；尚无可判别的 UAV transport 结果。 |

Replace longitudinal summary item 5 with:

Markdown
5. G32 支持 capacity-6/8/12 strict-load，G34 支持固定过程到有界随机
   roster process 的零训练 transport，G35 关闭 learned actor hidden carry。
   G36 进一步以零训练证明 exact G35 CS final checkpoints 不需要目标 episode
   的真实 time/age/previous-action bundle：冻结的 source-valid donor generator
   已足以保持全部 access 与 0.05 noninferiority 门槛。该结果仍保留四个模型
   坐标、donor 内部 joint coherence、critic true time、lifecycle state 与 G31
   credit；下一边界检查 donor coherence 是否只是维持输入分布的非必要外壳。

No change is warranted to ALGORITHM_PRINCIPLES.md. G36 is a bounded local simplification and sensor-substitution result, not a new cross-experiment law. The durable principles already require narrow interpretation and replacement before accumulation.

5. ONE_NEXT_ACTION
CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_DESIGN_ASSERTION_AUDIT
Scientific distinction

G36 has closed dependence on the target’s actual history. It has not closed dependence on the surrogate’s internal joint coherence.

The next question is:

source-valid joint donor snapshot
               versus
active-count-conditioned marginally supported but factorized surrogate

The selected G37 audit should test whether the exact checkpoints need time, age, and previous-action values to form a mutually coherent lifecycle-like tuple, or whether those four coordinates merely need individually plausible values.

Why this is the cheapest discriminating action

It is cheaper than the alternatives because it:

requires zero training and can reuse the exact G35 checkpoints and G36 registered evidence;

changes only the surrogate joint distribution, not the source, policy, critic, checkpoint, reward, or action stream;

directly attacks G36’s strongest remaining counterexample;

can establish whether the donor-bank machinery is scientifically load-bearing or merely an input-distribution convenience.

It is more discriminating than:

six-coordinate retraining, which simultaneously changes architecture, parameterization, initialization, and optimization;

a G31-credit comparison, which changes training rather than the unresolved execution-time input question;

capacity or process expansion, which would broaden transport without determining whether donor coherence is needed;

another UAV source, which is more expensive and remains exposed to the source-identifiability failures already observed in UAV G1/G2;

constants or zeros, whose failure would be confounded by concentration on a special, potentially out-of-support input point.

A G37 pass would permit a simpler marginal surrogate generator. A confident failure would retain source-valid donor coherence as load-bearing for these checkpoints and close this simplification slice without retraining rescue.

6. EXECUTABLE_SCIENTIFIC_BOUNDARY

A new design audit is required because G37 introduces a new intervention distribution and a new null. The one exact audit question is:

Can a conclusion-bearing zero-training comparison be frozen for the exact formal G35 CS final checkpoints in which the accepted G36 joint-donor execution is compared with an active-count-conditioned factorized donor execution that preserves each of the four history-proxy coordinates’ empirical donor marginal and legal support, but destroys within-row, cross-coordinate, and across-roster joint coherence by drawing the age, previous-action-0, previous-action-1, and time columns from independently selected G36 donor snapshots and independently permuting each column across active rows?

The audit must determine whether that factorized surrogate retains every G36 fixed/random, deterministic/stochastic, capacity-6/8/12, event-window, process-segment, transport, and replicate-stability gate and remains noninferior to the G36 joint-donor execution by a frozen 0.05 margin.

Inherited non-negotiable boundary
training=none
checkpoints=exact_formal_G35_CS_final_only
reference_execution=exact_formal_G36_joint_donor
H=48
capacities=6|8|12
sources=unchanged_G32_fixed_and_G34_P0_random
actor_actual_fields_0_to_6=unchanged
active_mask_and_prefix=unchanged
critic=unchanged
reward=unchanged
action_streams=paired
episode_ids=complete_inherited_support
G33_reactivation=forbidden

The primary estimand to be frozen by the design audit is directionally:

Δ
coh
	​

=U
joint donor
	​

−U
factorized donor
	​

,

where a positive value favors donor coherence.

The audit must provide exact mutually exclusive branches for:

INVALID_CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37
SOURCE_OR_G36_REFERENCE_FAILURE_G37
FACTORIZED_HISTORY_PROXY_SUFFICIENT_G37
JOINT_DONOR_COHERENCE_LOAD_BEARING_G37
MIXED_UNDERPOWERED_HISTORY_PROXY_COHERENCE_G37

The positive claim ceiling is only:

The exact checkpoints do not require the G36 donor’s joint coherence under the frozen factorized marginal law.

A negative result may establish only checkpoint dependence on donor coherence or distributional consistency; it may not establish task-level history necessity.

Complexity boundary
design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)

A later realization may read the exact G36 joint-donor baseline rather than rerun it. The maximum admissible new formal inventory is:

replicates=3
capacities=3
new_factorized_cells_per_capacity=4
episodes_per_cell=128
real_transitions<=221184
optimizer_steps=0
bootstrap_resamples=10000

The complete nonformal package must finish within 20 minutes, and the formal evaluate/analyze boundary must be projected to and capped at eight hours. A violation is NON_EXECUTABLE_EVIDENCE_DESIGN, not a scientific result.

Scientific and result-sensitive fields include:

the exact factorization and permutation law;

seed ownership;

reference-artifact binding;

paired unit;

0.05 margin;

access gates;

confidence construction;

evidence volume;

first-match order.

File names, storage layout, vectorization, donor caching, serialization, telemetry, batching, and proof-sized test organization remain implementation-only.

This disposition authorizes no implementation, Git action, nonformal/formal evaluation, monitoring, or successor child.

7. 中文简报

本轮正式结果必须原样接受：

HISTORY_PROXY_FREE_CHECKPOINT_SUFFICIENT_G36

科学裁决是：

SUPPORTED_RETAINED_BOUNDED_ACTUAL_HISTORY_SENSOR_BUNDLE_SUBSTITUTION_G36
G36 新证明了什么

G35 已证明 learned hidden carry 不需要。G36 进一步证明：

对 exact G35 CS final checkpoints，在 H=48、capacity 6/8/12、G32 fixed 与 G34 bounded-random process 中，actor 不需要读取目标 episode 的真实 time、lifecycle age 和 previous actions。把这四个真实字段替换成独立的、source-valid donor bundle 后，全部 access 门槛仍通过，且相对注册执行的损失 UCB 远低于 0.05。

主差值为：

registered - donor-substituted
CI95 = [-0.002479, 0.000105, 0.003575]

区间跨过零，所以不能说 donor 更好，也不能说真实 history 更好。但它排除了真实 bundle 带来超过 0.003575 的 pooled 优势；最大 component UCB 也只有 0.007529。

最小关闭单元

现在可以关闭：

对这些 exact checkpoints，目标 episode 的真实且一致的 time/age/previous-action bundle 是 access 必需条件，或能带来超过 0.05 的 material benefit。

但不能写成：

模型可以从 10 维删成 6 维；

四个输入权重没有作用；

任意零值、常数或噪声都安全；

task 全局无记忆；

critic true time、active mask 或 lifecycle state 可以删除；

所有重新训练的策略都不需要历史。

G36 的正结论仍依赖一个内部 coherent 的 source-valid donor snapshot。它删除的是目标真实历史，不是所有 history-shaped 输入。

当前进度位置
阶段	已支持结论
G32	checkpoint 跨配置容量 6/8/12
G34	固定 roster 日程到有界随机 process
G35	learned actor carry 不再 load-bearing
G36	目标真实 time/age/previous-action sensors 可由冻结 donor 替代
剩余正式迭代	10
唯一下一动作
CONTINUOUS_ROSTER_HISTORY_PROXY_COHERENCE_G37_DESIGN_ASSERTION_AUDIT

它只检查：

G36 是否真正只需要四个字段各自处于合理 marginal support，还是仍需要 donor 内部 time、age 和 previous actions 的 joint coherence。

G37 应使用 factorized donor：四个坐标分别从独立 donor snapshots 抽取并独立置换，保留每个坐标的合法 marginal，但破坏跨坐标、跨成员的一致 lifecycle 结构。

这是比重新训练六维模型、比较 credit、扩 capacity/process 或再次设计 UAV source 更便宜、更干净的证据。设计审计本身零计算；后续若获准实现，仍必须满足：

H=48
K_search=0
hypothetical transitions=0
new formal transitions<=221184
optimizer steps=0
nonformal<=20 minutes
formal<=8 hours

G33 及其衍生线继续保持用户放弃、禁止复活。本裁决不授权代码或计算。
