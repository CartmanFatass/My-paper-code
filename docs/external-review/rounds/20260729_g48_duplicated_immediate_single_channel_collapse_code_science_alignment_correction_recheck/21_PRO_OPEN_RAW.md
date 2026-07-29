CODE_SCIENCE_ALIGNMENT
The repaired target 9edddc845d88191bbfbd6c2ec779551edbbcb78a closes the exact artifact-schema mismatch recorded against the superseded target. The repair is confined to reduced-artifact schema enforcement and its focused tamper evidence; the G49 computational treatment remains the accepted duplicated-immediate reference versus the genuinely single-immediate reduced route.
The repaired source now defines exact key inventories for:
single-channel normalization records
gradient rows
single-channel gradient-evidence records
reduced pass records
reduced final checkpoints
The corresponding validators require exact set equality rather than accepting arbitrary additional metadata.
The repaired recursive residue detector now examines both mapping keys and string values. It normalizes case and separators and rejects second-channel, duplicated-immediate, equal-mean, averaging, dummy and compatibility identities, while allowing only the exact registered provenance values in their protected fields.
FROZEN_CONTRACT_CONFORMANCE
Exact reduced schemas
The reduced pass must have exactly _REDUCED_PASS_KEYS; its target must have exactly _SINGLE_NORMALIZATION_KEYS; its gradient evidence must have exactly _SINGLE_GRADIENT_EVIDENCE_KEYS; every gradient row must have exactly _GRADIENT_ROW_KEYS.
The reduced checkpoint must have exactly _REDUCED_CHECKPOINT_KEYS, and its nested route_schema must equal exactly:
target_law=x_I=r_t
normalization_instances=1
channel_losses=1
gradient_constructions=1
entropy_addition_count=1
No additional reduced-checkpoint field can pass merely because its key looks innocuous.
Key-and-value residue rejection
The validator recursively inspects nested mappings, sequences and string values. The prior hidden values:
accepted_G48_duplicated_immediate
immediate_2
are now recognized as forbidden residue even when stored beneath ordinary-looking keys such as legacy, route or channels.
Prior counterexample closure
The focused source test directly submits the prior innocuous-key/value payload and requires rejection. It separately injects that payload into a reduced final checkpoint and a reduced pass record, and also verifies rejection of extra nested gradient-evidence fields. Valid reduced records and checkpoints continue to validate.
The runner-level guard performs an actual artifact-reload check: it writes the hidden duplicated-route payload into the serialized reduced checkpoint, updates the file digest, and still requires training-artifact validation to fail at checkpoint reload.
Protected computation
The repair preserves the claim-bearing computation:
reference credit = 0.5*(g_I1+g_I2)
reduced credit   = g_I
common entropy   = added exactly once in both routes
Every pass still requires byte equality of the two reference losses and gradients, the single loss and gradient, the actual reference average, entropy gradients and final assigned actor gradients.
The post-pass checks continue to bind actor/log_std bytes, Adam counters and moments, action and log-probability traces, and disjoint optimizer storage.
The final checkpoint comparison remains a canonical actor/log_std/Adam/provenance projection comparison, while the full reference and reduced route schemas intentionally differ.
CONFLICTING_BEHAVIOR_AND_COUNTEREXAMPLE
No conflicting behavior remains within the correction-only scope.
The exact prior counterexample can no longer pass through either conclusion-bearing route:
reduced pass validation
reduced checkpoint validation
serialized checkpoint reload validation
It is blocked independently by exact outer key sets and by recursive inspection of the forbidden string values. The valid single-channel artifacts remain accepted, so the repair does not close the route vacuously.
MINIMAL_IN_CONTRACT_CORRECTION
additional_correction_required=NONE
The repaired target implements every element of the previously specified smallest correction:
exact reduced-pass key set
exact reduced-checkpoint key set
exact nested target and gradient-evidence key sets
exact reduced route_schema
recursive forbidden-key and forbidden-value rejection
focused innocuous-key/value update-evidence guard
focused serialized-checkpoint reload guard
No source, target law, normalization, gradient, entropy, optimizer, trajectory, checkpoint projection, result branch or evidence-volume change is required.
PROTECTED_SEMANTICS
The following remain unchanged:
accepted G48 formal source and branch
reference=NATIVE6_G31_DUPLICATED_IMMEDIATE
reduced=NATIVE6_G31_SINGLE_IMMEDIATE

single target x_I=r_t
accepted float64 centering and population-RMS reduction
exact-zero scale maps to zero

reference literal 0.5*(g_I1+g_I2)
reduced literal g_I
common entropy added once

two PPO passes
one Adam step per pass
lr=1e-3
betas=(0.9,0.999)
eps=1e-8
weight_decay=0
amsgrad=false
no clipping, minibatches or optimizer reset

one shared 8×48 stored trajectory
384 real transitions
exact actor/Adam/action-trace equality
D_SC=0 requirement
canonical final checkpoint projection
final-only checkpoint selection
C++ backend requirement
The current index records the repair exclusively as recursive schema closure and retains the original proof inventory, exact-equivalence branches, claim ceiling and formal-authority boundary.
EVIDENCE_AND_COMPLEXITY
audit_compute=0
formal_compute_started=false
nonformal_compute_started=false

accepted_branch_starts=1
shared_real_trajectory_batches=1
episodes=8
H=48
real_transitions=384

PPO_passes_per_arm=2
actor_optimizer_steps_per_arm=2
bootstrap_resamples=0
formal_statistical_run=false

K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
wall_clock_cap_seconds=1200
The correction adds no scientific arm, trajectory, seed, optimizer step, bootstrap draw or result branch. It only strengthens artifact validation and focused tamper evidence.
EXECUTABLE_BOUNDARY
Formal entry remains fail-closed. The runner still has no bound implementation commit or alignment-stage identity, so formal admission cannot proceed before this independent disposition is mechanically archived and a fresh same-source preflight satisfies the existing authorization contract.
This disposition authorizes no implementation, Git operation, proof execution, nonformal run or formal run.
中文简报
本轮只复核前次唯一 mismatch：reduced artifact 能否把 duplicated-immediate 信息藏在普通 key 下的字符串 value 中。
修复后：
reduced pass 顶层 key 必须完全一致
reduced checkpoint 顶层 key 必须完全一致
target / gradient evidence / gradient row 的嵌套 key 必须完全一致
route_schema 必须精确等于单通道 schema
validator 现在递归检查 key 和 string value，因此此前的反例：
legacy = {
    "route": "accepted_G48_duplicated_immediate",
    "channels": ["immediate_1", "immediate_2"]
}
在以下路径都会失败：
reduced pass validation
reduced checkpoint validation
serialized checkpoint reload validation
同时，合法的 single-immediate pass、checkpoint 和 reload 仍然通过。
G49 的计算合同没有变化：reference 仍执行两个 immediate loss 与实际 0.5*(g_I1+g_I2)；reduced 仍只执行一个 immediate loss 并使用 g_I；entropy、两次 PPO、Adam、共享 384-transition trajectory、D_SC=0 和 canonical checkpoint equality 全部保持冻结。
正式入口仍关闭；本回复不授权任何计算。
AUDIT_DISPOSITION=ALIGNED
