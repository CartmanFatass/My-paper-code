CODE_SCIENCE_ALIGNMENT

The target implements the principal G48 treatment correctly:

both arms descend from the accepted G47 baseline-free route;

the reference materializes r_t | G_(t+1);

the null builder accepts only a rewards tensor and separately clones r_t | r_t;

each channel is separately centered and independently RMS-normalized;

credit is formed as the literal equal mean with common entropy added once;

paired trajectories are collected before the fixed reference-then-null update order;

actor optimizers are initially empty, separately owned and restricted to actor/log_std;

final formal admission remains unset pending an independent alignment result.

However, the implementation does not instantiate the frozen treatment-activation arithmetic.

The submitted design boundary was corrected by the accepted design raw so that activation measures the complete realized-successor channel package rather than unit-direction change alone. The frozen quantity is the unsquared relative vector norm:

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

with zero when both denominator norms are zero and strict activation at q_credit > 1e-6.

The target instead computes:

q
credit
target
	​

=
max(∥v
REF
	​

∥
2
2
	​

,∥v
NULL,cf
	​

∥
2
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
2
	​

	​

,

which is the square of the registered ratio. _activation_scalars constructs that squared quantity, and validate_activation_record independently reconstructs the same squared quantity before setting treatment_active.

FROZEN_CONTRACT_CONFORMANCE
Conforming surfaces

The following frozen points are represented by actual target paths:

Provenance and projection. project_g48_arms derives both arms from the accepted G47 reduced route, deep-copies them, checks actor-state equality and shared-storage absence, rejects baseline reintroduction, and verifies zero projection RNG consumption.

Target laws. The reference obtains the accepted immediate and realized-successor rows; the null accepts only rewards, creates two independent clones, and records zero realized-successor reads.

Normalization and gradient composition. Both packages are routed through separate-channel normalization. _probe forms two channel gradients, applies the literal equal mean, and adds entropy afterward. Reference group liveness is enforced without requiring both global channels individually to be live.

Pairing and exposure. Both trajectories are prepared before either update; the initial order-swap guard takes no optimizer step; production applies reference and then null, with one Adam step per pass.

Null duplicate evidence. The actual null’s two channel gradients must be bitwise equal, and both-arm normalization records are serialized and validated.

Authority closure. The runner leaves the aligned implementation and stage unset; formal execution requires later alignment plus same-source preflight and the registered token.

Nonconforming frozen point

The controlling design does not register a squared activation statistic. Squaring the relative norm changes the scientific gate:

q
target
code
	​

=(q
credit
frozen
	​

)
2
.

With the same strict threshold 1e-6, the implementation effectively requires:

q
credit
frozen
	​

>10
−3
,

rather than the registered:

q
credit
frozen
	​

>10
−6
.

The code-science index repeats the squared formula rather than accurately mapping the frozen assertion, so the index cannot cure the implementation conflict.

This is result-changing because formal conclusion evidence counts active passes under the target’s squared rule and requires at least one active pass in every formal replicate.

CONFLICTING_BEHAVIOR_AND_COUNTEREXAMPLE
Exact frozen assertion

For a finite reference credit vector v
REF
	​

 and duplicated-immediate counterfactual v
NULL,cf
	​

, activation uses:

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

>10
−6
.

This gate intentionally recognizes direction changes, magnitude-only changes and one-zero/one-nonzero credit signals.

Exact conflicting path

In _activation_scalars:

reference_norm_square = sum(reference ** 2)
null_norm_square = sum(null ** 2)
difference_sum_square = sum((reference-null) ** 2)

q_credit =
    difference_sum_square /
    max(reference_norm_square, null_norm_square)

validate_activation_record recomputes exactly that squared statistic, and build_conclusion_evidence uses its resulting treatment_active field when admitting each replicate.

Concrete target-bound counterexample

Take one valid reference pre-update pass with:

q_target = 1e-3
v_REF = [1.0005]
v_NULL,cf = [1.0]

All values are finite, both vectors are nonzero, and the only difference is a small complete-package credit-magnitude effect.

The frozen rule gives:

q
credit
frozen
	​

=
1.0005
0.0005
	​

≈4.9975×10
−4
>10
−6
,

so the pass is treatment-active.

The target computes:

q
credit
target
	​

=
1.0005
2
0.0005
2
	​

≈2.4975×10
−7
<10
−6
,

so the same pass is treatment-inactive.

If such differences are the only valid activation witnesses in one formal replicate, the frozen contract admits that replicate while the target rejects it. That can prevent formal admission or route an otherwise valid package to the invalid path.

The focused activation test checks an extreme q_credit=1 case and the both-zero case, but it contains no intermediate-ratio witness capable of detecting the squaring error.

MINIMAL_IN_CONTRACT_CORRECTION

Change only the activation arithmetic and its directly bound evidence.

In _activation_scalars, retain the serialized squared sufficient statistics, but compute:

reference_norm = sqrt(reference_norm_square)
null_norm = sqrt(null_norm_square)
difference_norm = sqrt(difference_sum_square)

denominator = max(reference_norm, null_norm)
q_credit = 0.0 if denominator == 0.0 else difference_norm / denominator

In validate_activation_record, independently reconstruct that same unsquared ratio:

expected_q_credit =
    0.0
    if max(sqrt(reference_square), sqrt(null_square)) == 0.0
    else sqrt(difference_square)
         / max(sqrt(reference_square), sqrt(null_square))

Then:

keep strict q_credit > 1e-6;

keep q_target > 1e-6;

keep direction distance descriptive only;

update the G48 code-science index to state the unsquared frozen formula;

add one focused test with a relative norm difference between 1e-6 and 1e-3, such as the concrete counterexample above, proving that it is active.

No arm, target law, gradient composition, seed, optimizer, evidence inventory, access gate, confidence procedure or first-match branch requires modification.

PROTECTED_SEMANTICS

The correction must preserve exactly:

accepted G47 source, aligned implementation, stage and formal branch
accepted G40 anchor replicates 0|1|2

reference target:
    x_I = r_t
    x_S = G_(t+1)
    G_48 = 0
    G_t = r_t + 0.99 G_(t+1)

null target:
    x_I1 = r_t
    x_I2 = r_t
    zero realized-successor actor-credit reads

normalization:
    384 team-level primitive-step rows
    separate centering
    independent population RMS
    no epsilon, filtering or active-count weighting
    one normalization before both PPO passes

credit:
    literal 0.5*(g_1+g_2)
    common entropy added once
    no norm matching
    no tunable channel coefficient

training:
    paired collection before updates
    fixed reference-then-null order
    two PPO passes
    one actor Adam step per pass
    no clipping, minibatches or reset
    final-only checkpoints

inference:
    reference-only activation evidence
    null activation-read count zero
    one active pass in every required replicate

The correction must not introduce a unit-direction gate, an altered threshold, post-Adam matching, an additional counterfactual route or another activation statistic.

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

This is an arithmetic and validation correction within the already frozen evidence boundary. It needs no additional trajectories, seeds, bootstrap draws or optimizer steps.

The existing ceilings remain unchanged:

nonformal:
    total_real_transitions<=14592
    optimizer_steps<=40
    bootstrap_resamples=250
    wall_clock<=1200 seconds

formal:
    total_real_transitions<=396288
    optimizer_steps<=1200
    bootstrap_resamples=10000
    wall_clock<=28800 seconds

Formal admission remains closed because the runner’s alignment commit and stage constants are still unset.

EXECUTABLE_BOUNDARY

The next permitted boundary is a correction-only G48 code-science alignment recheck on a new pushed target.

That recheck should answer only:

Does every source, validator, index and focused activation test now implement the frozen unsquared complete-credit-vector ratio

∥v
REF
	​

−v
NULL,cf
	​

∥
2
	​

/max(∥v
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

),

with the unchanged strict 1e-6 threshold, while every other G48 scientific and formal-authority field remains unchanged?

No nonformal or formal scientific run is authorized before that corrected target receives an independent aligned disposition.

中文简报

G48 的主要 treatment 路径基本一致：

reference = immediate + realized successor
null      = immediate + duplicated immediate

null builder 只接收 reward，两条 immediate channel 独立 materialize；两臂使用 separate centering、independent RMS、literal 0.5*(g_1+g_2)，并保持 paired collection、两次 PPO 和 final-only checkpoint。

但 activation arithmetic 与冻结合同不一致。

冻结合同是：

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

.

当前代码实际计算：

q
credit
code
	​

=
max(∥v
REF
	​

∥
2
2
	​

,∥v
NULL,cf
	​

∥
2
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
2
	​

	​

.

也就是把正确比值平方了，却仍使用 >1e-6 门槛。实际效果相当于把正确门槛从 1e-6 提高到约 1e-3。

具体反例：

q_target = 1e-3
v_REF = [1.0005]
v_NULL,cf = [1.0]

冻结规则：

q_credit ≈ 4.9975e-4 > 1e-6
→ active

当前代码：

q_credit ≈ 2.4975e-7 < 1e-6
→ inactive

这会改变每个 formal replicate 是否满足 activation gate，进而改变 formal admission 或最终 invalid 分支。

最小修正仅是：

q_credit =
sqrt(difference_sum_square)
/
max(sqrt(reference_norm_square), sqrt(null_norm_square))

同步修正 validator、index，并增加一个位于 1e-6 与 1e-3 之间的 focused witness。其余 source、target、Adam、seed、confidence、budget 和 first-match semantics 全部不变。

AUDIT_DISPOSITION=MISMATCH
