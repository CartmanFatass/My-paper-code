CODE_SCIENCE_ALIGNMENT
The target implements the core G49 treatment correctly:


both arms originate from the accepted G48 duplicated-immediate route with equal, storage-disjoint actor and log_std state and identically configured empty Adam state;


the reference executes two separately normalized immediate losses and the actual 0.5*(g_I1+g_I2) operation;


the reduced route constructs one immediate target, one normalization, one loss and one gradient;


both PPO passes require byte-equal targets, normalized rows, losses, channel gradients, entropy gradients, assigned gradients, actor state, Adam state and actor traces;


the canonical checkpoint projections are compared while the reduced route_schema declares exactly one target, normalization, loss and gradient construction.


However, the reduced artifact validator does not fully instantiate the frozen fail-closed schema requirement. It can admit hidden second-channel or duplicated-route residue encoded under an otherwise innocuous key.
FROZEN_CONTRACT_CONFORMANCE
Conforming claim-bearing paths
The actual reduced computation uses:
_single_immediate_target
_normalize_single
_single_probe
and does not invoke the accepted G48 duplicated-package builder, two-row normalization or equal-mean composition. The two-pass update materializes both plans before either optimizer step, checks actual floating-point equality, applies the reference then reduced update, and checks actor/Adam/trace equality after each pass.
The checkpoint builder also gives the two arms intentionally different route schemas while requiring their canonical actor, log_std, Adam, update-count and provenance projections to be bitwise equal.
Nonconforming artifact boundary
The frozen design requires the reduced artifact to reject:
second target fields
second normalization fields
second loss/gradient fields
duplicate-equality flags
two-channel route labels
dummy or compatibility fields
and to contain no hidden second-channel residue.
validate_reduced_schema, however, examines only mapping key names for a short list of forbidden fragments. It never examines string values or semantic contents.
In addition:


_validate_reduced_pass does not require an exact reduced-pass key set; unrecognized extra fields are accepted when their key names avoid the forbidden fragments.


validate_checkpoint_pair does not require an exact reduced-checkpoint top-level key set. It requires an exact nested route_schema, but accepts unrelated additional top-level mappings when their key names pass validate_reduced_schema.


Thus the artifact lifecycle can validate a reduced artifact that still carries a hidden duplicated-immediate route description.
CONFLICTING_BEHAVIOR_AND_COUNTEREXAMPLE
Frozen assertion
The reduced replay, update evidence and final checkpoint must genuinely remove all duplicate-channel diagnostics, route labels and compatibility residue—not merely omit a predefined set of conspicuous key names.
Concrete target-bound counterexample
Start with a valid reduced final checkpoint and add:
legacy = {
    "route": "accepted_G48_duplicated_immediate",
    "channels": ["immediate_1", "immediate_2"]
}
The resulting top-level keys are ordinary names such as legacy, route and channels. None contains:
channel_2
second_
duplicate_channel
duplicate_equality
equal_mean
average_call
compatibility
dummy
The validator does not inspect the string values accepted_G48_duplicated_immediate or immediate_2. The required nested route_schema and canonical projection remain unchanged. Consequently:
validate_reduced_schema(reduced_checkpoint) == true
validate_checkpoint_pair(checkpoint_pair) == true
despite the reduced artifact still carrying an explicit two-channel route description.
The same bypass exists in a reduced pass record: an extra innocuously named mapping containing the duplicated-route label is ignored by _validate_reduced_pass.
The focused tests reject only conspicuous forbidden key names such as channel_2_gradient, second_target and dummy_compatibility_channel; they do not exercise a forbidden route or second-channel identity stored as a value under an allowed-looking key.
This is result-changing because a malformed reduced artifact can reach reload, evaluation and the exact-removability branch while violating the claim that no hidden second channel remains.
MINIMAL_IN_CONTRACT_CORRECTION
Replace permissive reduced-schema validation with exact recursive schemas.
At minimum:


Require an exact key set for every reduced pass record.


Require an exact top-level key set for the reduced final checkpoint.


Retain the existing exact equality requirement for the nested reduced route_schema.


Require exact key sets for nested reduced target and gradient-evidence mappings, rather than accepting arbitrary extra metadata.


Where any free-form string value remains permitted, reject duplicated-immediate, second-channel, equal-mean, dummy and compatibility identities in both keys and values.


Add one focused guard using an innocuous key whose value names accepted_G48_duplicated_immediate and immediate_2; both update-evidence and checkpoint reload validation must fail.


No source, target, normalization, gradient, entropy, Adam, trajectory, checkpoint projection, branch order or evidence-volume field needs modification.
PROTECTED_SEMANTICS
The correction must preserve:
accepted G48 provenance and formal branch
reference=NATIVE6_G31_DUPLICATED_IMMEDIATE
reduced=NATIVE6_G31_SINGLE_IMMEDIATE

single target x_I=r_t
accepted float64 centering and population-RMS order
exact-zero scale law
one single-channel loss and gradient
reference literal 0.5*(g_I1+g_I2)
common entropy added once

two PPO passes
one Adam step per pass
lr=1e-3
betas=(0.9,0.999)
eps=1e-8
weight_decay=0
amsgrad=false
no clipping, minibatches or reset

one shared 8×48 stored trajectory
D_SC exact equality
canonical actor/log_std/Adam checkpoint projection
final-only checkpoint selection
C++ backend and formal-admission closure
The correction may not add a placeholder second channel, compatibility tensor, changed route label, replacement normalization, altered optimizer or new scientific result gate.
EVIDENCE_AND_COMPLEXITY
audit_compute=0
formal_compute_started=false
nonformal_compute_started=false

H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
The existing proof ceiling remains unchanged:
one accepted branch start
one shared 8×48 trajectory
384 real transitions
two PPO passes per arm
two actor optimizer steps per arm
zero bootstrap
formal_statistical_run=false
wall_clock<=1200 seconds
The required correction is an artifact-schema closure and focused tamper guard. It introduces no new scientific evidence volume or experiment.
EXECUTABLE_BOUNDARY
The next permitted boundary is a correction-only G49 code-science alignment recheck on a new pushed target.
That recheck should answer only:

Do reduced pass records and reduced final checkpoints now enforce exact recursive schemas that reject all extra second-channel, duplicated-route, equal-mean, dummy and compatibility residue—including residue encoded in values under innocuous keys—while every computational, optimizer, equality, provenance and authority field remains unchanged?

Formal and nonformal scientific execution remain closed until that corrected target receives an independent aligned disposition.
中文简报
G49 的核心计算路径已经实现了：
reference:
    两个相同 immediate channel
    两次 normalization / loss / backward
    0.5*(g_I1+g_I2)

reduced:
    一个 immediate channel
    一次 normalization / loss / backward
    直接使用 g_I
两次 PPO pass 都检查了 gradient、entropy、actor、Adam 和 trace 的逐字节相等。
但 reduced artifact 的 fail-closed schema 仍不完整。当前 validator 只扫描 key 名称，不扫描 value，也不要求 reduced pass/checkpoint 使用精确完整的 key 集合。
因此可以在 reduced checkpoint 中加入：
legacy = {
    "route": "accepted_G48_duplicated_immediate",
    "channels": ["immediate_1", "immediate_2"]
}
这些 key 名不包含当前禁止片段，value 又不会被检查；原有 route_schema 与 canonical actor projection 不变，所以 checkpoint pair 仍可通过。这样 artifact 明明保留了 duplicated-immediate route 信息，却仍能进入 exact-collapse 分支。
最小修正是对 reduced pass、checkpoint 及其嵌套结构使用精确递归 schema，并对仍允许的字符串同时检查 key 和 value；加入一个 innocuous-key/forbidden-value 的聚焦 tamper guard。其余科学合同全部保持不变。
AUDIT_DISPOSITION=MISMATCH
