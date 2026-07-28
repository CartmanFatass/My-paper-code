CODE_SCIENCE_ALIGNMENT
The target implements most of the frozen G47 reduction correctly: it creates a genuinely baseline-free reduced module, projects the retained actor and Adam state, preserves the target-only independently normalized actor objective, compares the two PPO updates bitwise, and uses distinct checkpoint schemas.
It does not, however, instantiate the complete structural deletion frozen by the design. The baseline-only true-current-state input remains on the reduced arm’s executable actor path. The design required the reduced path not to consume that view even when it remains physically present in the shared trajectory.

FROZEN_CONTRACT_CONFORMANCE
Conforming portions
The implementation correctly:


derives both arms from the accepted G46 RAW route;


deep-copies the actor and log_std without shared storage or projection RNG;


removes credit_baselines, baseline parameters, baseline optimizer state, and baseline checkpoint schema from G47NoBaselineProjection;


projects the retained actor Adam state by parameter name;


preserves the target-only immediate and realized-successor credit law, separate centering, independent RMS scaling, literal 0.5*(g_I+g_S), and common entropy;


verifies bitwise actor-gradient, actor-state, actor-Adam, pre-tanh, action, and log-probability equality over the bounded two-pass guard;


rejects baseline keys in the reduced checkpoint and compares canonical actor projections.


Nonconforming portion
The frozen treatment deletes the baseline-only true-state input path, not merely the baseline module and output fields. The reduced actor path still dereferences and forwards that input.
actor_only_replay executes:
critic_state=trajectory.critic_states[time]
for G47NoBaselineProjection, despite the reduced model having no baseline module.
The common actor_trace path likewise reads and forwards trajectory.critic_states[time] for either arm, including the reduced arm.
Thus the reduced callable boundary remains dependent on the presence and readability of the baseline-only true-state field.

CONFLICTING_BEHAVIOR_AND_COUNTEREXAMPLE
Exact frozen assertion
The reduced route must remove:
credit-baseline module
baseline-only true-state input consumer
baseline forward/loss/backward path
baseline optimizer and checkpoint state
and must remain valid when the baseline-only true-state view is unavailable. The accepted design explicitly states that the reduced path must not consume this view even if the shared source record still contains it.
Exact conflicting path
Both reduced replay and reduced trace evaluation index trajectory.critic_states and pass the resulting tensor into g41.retained_actor_step. This leaves a baseline-only input read in the actor/log-probability and evaluation paths.
The static certificate cannot detect this conflict:


its forbidden-read filter checks only names containing credit_baselines, baseline_values, or baseline_loss;


it does not treat critic_states or the baseline-only true-state field as forbidden;


several dependency counts, including the baseline-to-action and baseline-to-evaluation counts, are serialized as literal zero values rather than reconstructed from the complete nested call graph.


Concrete target-bound counterexample
Construct the otherwise valid shared G46 trajectory with unchanged actor observations, actions, rewards, masks, ledgers, and realized-successor targets, but replace its baseline-only critic_states view with a read-trapping accessor.
Under the frozen G47 reduced contract:
NATIVE6_G31_RAW_NORM_NO_BASELINE_MODULE
must still execute, because no retained actor computation is allowed to consume that field.
At the target commit, actor_only_replay and actor_trace attempt to index the trapped field before producing actor outputs. The reduced route therefore fails even though every actor-relevant input is unchanged. Meanwhile, the current static certificate can continue reporting zero baseline-to-action/evaluation paths because critic_states is absent from its forbidden-read vocabulary.
The focused projection test verifies removal of baseline module attributes and checks the already-produced zero-valued certificate, but it does not make the baseline-only true-state view inaccessible.
This admits a conclusion-bearing SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G47 result without actually deleting the frozen baseline-only input dependency.

MINIMAL_IN_CONTRACT_CORRECTION
Make only the following correction:


Introduce or route through a G47 actor-only forward function whose callable interface has no critic_state argument and whose implementation reads only:


actor observations;


active mask and prefix state;


actor hidden state;


teacher action or action noise.




Update actor_only_replay so it never indexes trajectory.critic_states.


Split or dispatch actor_trace so the reduced-arm trace uses the actor-only function and never indexes or forwards critic_states. The reference arm may retain its baseline-only true-state path.


Extend the static certificate with an independently reconstructed predicate such as:


baseline_true_state_read_into_reduced_actor_gradient=0
baseline_true_state_read_into_reduced_action_or_logprob=0
baseline_true_state_read_into_reduced_evaluation=0
critic_states and any equivalent baseline-only input accessor must be included in the forbidden dependency analysis; these counts must not be literal constants.


Add one focused guard in which the reduced path receives a read-trapping baseline-only true-state view. Reduced replay, trace, update, checkpoint construction, and reload must remain valid and bitwise equal to the reference actor projection, while the reference baseline path may still access its own ordinary true-state input.


No change is required to the actor objective, source, optimizer, parameter inventory, PPO exposure, checkpoint projection, exact-equivalence definition, evidence ceiling, or ordered branches.

PROTECTED_SEMANTICS
The correction must preserve exactly:
accepted G46 provenance
accepted G40 anchor authority
reference baseline module and fitting exposure
reduced absence of all baseline parameters and optimizer state
target-only r_t and G_(t+1) residuals
separate channel centering
independent per-channel RMS normalization
literal 0.5*(g_I+g_S)
common entropy once
two persistent PPO passes
per-parameter Adam projection and ordering
same stored 8×48 trajectory
D_G47 exact-bitwise semantics
canonical actor-checkpoint projection
final-only checkpoint inventory
C++ backend requirement
formal-admission closure
The correction may not add a dummy true-state tensor, constant filler, compatibility baseline interface, replacement critic, learned scale, or altered actor forward contract.

EVIDENCE_AND_COMPLEXITY
audit_compute=0
formal_compute_started=false
nonformal_compute_started=false
K_search=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
The correction needs no new scientific evidence volume.
The existing ceiling remains sufficient:
static dependency and optimizer-factorization proof first

optional bounded guard:
    one accepted branch start
    one shared 8×48 stored batch
    real_transitions<=384
    PPO_passes=2 per arm
    bootstrap_resamples=0
    formal_statistical_run=false
    wall_clock<=1200 seconds
The read-trapping true-state guard is a focused contract check inside that existing boundary, not a new experiment or conclusion-bearing run.

EXECUTABLE_BOUNDARY
The exact next permitted boundary is a correction-only G47 code-science alignment recheck at a new pushed implementation commit.
That recheck should answer only:

Has the reduced actor/replay/trace path stopped accepting, indexing, forwarding, validating, or otherwise consuming the baseline-only true-current-state view, and does the static certificate now reconstruct that absence while every other frozen G47 field remains unchanged?

Formal and nonformal proof execution remain closed until that corrected target receives an independent aligned disposition and the existing admission requirements are satisfied.

中文简报
G47 的主要删除已经实现：reduced arm 确实没有 baseline module、baseline 参数、baseline Adam state 或 baseline checkpoint keys，actor 与 Adam 的两次 PPO 更新也做到了逐字节一致。
但冻结合同还要求删除 baseline-only true-state input path。当前代码在 reduced arm 中仍然执行：
trajectory.critic_states[time]
并把它传给 retained_actor_step。actor_only_replay 与 actor_trace 都存在这条路径。当前静态证书又没有把 critic_states 识别为禁止读取项，并将若干依赖计数直接写成零，因此这一残留输入依赖仍可通过证书和最终分支。
具体反例是：保持所有 actor-facing 数据不变，只把 baseline-only critic_states 替换成“读取即报错”的 sentinel。按冻结合同，no-baseline arm 应完全不受影响；当前 target 会在 replay/trace 阶段读取它并失败。
最小修正是：
为 reduced arm 使用完全不接收 critic_state 的 actor-only forward；
actor_only_replay 与 reduced actor_trace 不再索引 critic_states；
静态证书新增并真实重建 true-state read count；
加入一个 read-trapping sentinel 聚焦守卫。
其余 source、credit、Adam、PPO、384-transition 上限、checkpoint 与 branch semantics 全部保持不变。
AUDIT_DISPOSITION=MISMATCH
