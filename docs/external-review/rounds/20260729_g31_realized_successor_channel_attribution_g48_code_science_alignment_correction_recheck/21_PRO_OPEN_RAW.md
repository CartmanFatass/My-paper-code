CODE_SCIENCE_ALIGNMENT

The repaired target closes the single archived G48 mismatch. _activation_scalars now derives the Euclidean norms from the serialized squared sufficient statistics and computes the frozen unsquared ratio:

q
credit
	​

=
max(∥v
REF
	​

∥
2
	​

,∥v
NULL,cf
	​

∥
2
	​

)
∥v
REF
	​

−v
NULL,cf
	​

∥
2
	​

	​

,

with a zero denominator yielding 0.0. Treatment activation remains the conjunction of strict q_target > 1e-6 and strict q_credit > 1e-6; unit-direction distance remains descriptive only.

The correction is confined to the previously identified arithmetic and its bound evidence. No target-bound scientific ambiguity remains.

FROZEN_CONTRACT_CONFORMANCE
Corrected arithmetic

The implementation now computes:

reference_norm  = sqrt(reference_norm_square)
null_norm       = sqrt(null_norm_square)
difference_norm = sqrt(difference_sum_square)

denominator = max(reference_norm, null_norm)
q_credit = 0.0 if denominator == 0.0
           else difference_norm / denominator

This is exactly the registered complete-credit-vector ratio, not its square.

Independent validator reconstruction

validate_activation_record independently reconstructs all three norms from the serialized squared fields, recomputes the unsquared ratio, recomputes the strict activation Boolean, and requires exact agreement with the stored q_target, q_credit, norm fields and treatment_active. Negative, nonfinite, malformed or stale evidence fails validation.

Intermediate-ratio witness

The focused guard uses the prior counterexample scale:

v_REF     = [1.0005]
v_NULL,cf = [1.0]
q_target  = 1e-3

It verifies that:

1e-6 < q_credit < 1e-3
treatment_active=true

and separately rewrites the record with the old squared statistic and confirms that validation rejects it. The same test retains strict equality-at-threshold inactivity, both-zero inactivity and nonfinite rejection.

Index and authority binding

The code-science index now states the unsquared formula, identifies the intermediate-ratio guard, rejects the squared gate as the excluded alternate mechanism, and keeps formal admission pending an exact independent alignment target/stage, fresh same-source preflight and authorization token.

CONFLICTING_BEHAVIOR_AND_COUNTEREXAMPLE

No concrete target-bound counterexample remains within the correction scope.

The prior counterexample no longer conflicts with the implementation: its unsquared relative difference is now recorded as active, while the old squared value is explicitly rejected by the validator.

The repaired source also preserves reference-only activation authority: the counterfactual is constructed from the reference immediate gradient, the actual null contributes zero activation evidence, and direction distance is not a conclusion gate.

MINIMAL_IN_CONTRACT_CORRECTION
additional_correction_required=NONE

The archived smallest correction has been implemented in all three claim-bearing surfaces:

source arithmetic
validator reconstruction
focused intermediate-ratio test

The index now maps those surfaces to the frozen unsquared assertion.

PROTECTED_SEMANTICS

The repaired target preserves the protected G48 contract:

reference arm=
NATIVE6_G31_IMMEDIATE_REALIZED_SUCCESSOR

null arm=
NATIVE6_G31_DUPLICATED_IMMEDIATE

reference target=r_t | G_(t+1)
null target=r_t | r_t
null successor reads=0

normalization=
separate centering
independent population RMS
384 team-level primitive-step rows

credit=
literal 0.5*(g_1+g_2)
common entropy added once
no norm matching
no learned channel coefficient

pairing=
both trajectories before either update
fixed reference-then-null update order

optimizer=
two PPO passes
one actor Adam step per pass
no clipping, minibatching or reset

artifacts=
final-only checkpoints
paired confidence and frozen first-match semantics

The current index retains the same G47 provenance, two registered arms, target/null routes, normalization, gradient composition, pairing, checkpoint, runtime, confidence and authority rows; only the squared activation defect is marked as repaired.

The source continues to construct the reference from immediate plus realized-successor credit and the null from two separately allocated reward-only clones with zero recorded successor reads.

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

The registered evidence inventories remain unchanged:

nonformal:
    14,592 real transitions
    40 optimizer steps
    24 evaluation cells
    250 bootstrap resamples

formal:
    396,288 real transitions
    1,200 optimizer steps
    72 evaluation cells
    10,000 bootstrap resamples

No new arm, source, seed block, threshold, confidence rule, artifact route or runtime path was introduced by the correction.

EXECUTABLE_BOUNDARY

The corrected G48 implementation is scientifically conformant to the frozen activation contract.

Formal entry remains governed by the existing fail-closed boundary:

exact ALIGNED implementation target and archived alignment stage
+
fresh same-source valid nonformal preflight
+
exact G48 formal authorization token

The index still records the alignment target/stage as pending this independent correction recheck and records both nonformal and formal compute as not started. This disposition itself authorizes no implementation, Git operation, preflight or formal execution.

中文简报

本轮只复核前次唯一 mismatch：q_credit 被错误平方。

修复后的代码现在计算：

q
credit
	​

=
max(∥v
REF
	​

∥
2
	​

,∥v
NULL,cf
	​

∥
2
	​

)
∥v
REF
	​

−v
NULL,cf
	​

∥
2
	​

	​

,

分母为零时取零，并继续使用严格的：

q_target > 1e-6
q_credit > 1e-6

validator 会从平方充分统计量中独立重建同一个未平方比值，并拒绝旧平方值、过期 treatment_active、非有限值或不一致记录。

聚焦测试覆盖了前次反例：

v_REF=[1.0005]
v_NULL,cf=[1.0]

其正确比值位于 1e-6 与 1e-3 之间，修复后被判定为 active；改写成旧平方统计量后会被 validator 拒绝。

其余 reference/null target、successor 零读取、normalization、equal-mean credit、entropy、paired update、Adam exposure、seed、confidence、first-match、预算和 formal authority 均保持冻结状态。正式入口仍需本轮独立对齐归档、fresh same-source preflight 与精确 token；本回复不授权计算。

AUDIT_DISPOSITION=ALIGNED
