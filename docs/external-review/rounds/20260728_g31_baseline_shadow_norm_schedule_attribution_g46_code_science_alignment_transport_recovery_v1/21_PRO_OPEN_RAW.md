Corrected q_norm

Let m
B
	​

 and m
raw
	​

 be the registered global L
2
	​

 norms of the baseline-conditioned counterfactual credit gradient and the literal raw equal-mean credit gradient, respectively. Both must be finite and nonnegative.

q
norm
	​

=
⎩
⎨
⎧
	​

INVALID,
0,
0,
1,
INVALID,
max(m
B
	​

,m
raw
	​

)
∣m
B
	​

−m
raw
	​

∣
	​

,
	​

m
B
	​

 or m
raw
	​

 is nonfinite or negative,
m
B
	​

=0, m
raw
	​

=0,
m
B
	​

=m
raw
	​

>0,
m
B
	​

=0, m
raw
	​

>0,
m
B
	​

>0, m
raw
	​

=0,
m
B
	​

>0, m
raw
	​

>0, m
B
	​


=m
raw
	​

.
	​


The m_B>0, m_raw=0 case is invalid before either optimizer step because the reference arm’s norm-matched direction is undefined. This preserves the frozen zero/cancellation semantics.

A valid pass is treatment-active if and only if

q
norm
	​

>10
−6
.

Equality at 10
−6
 is inactive. Invalid cases cannot supply activation evidence.

Unit-direction equality

When both assigned credit gradients are nonzero:

Flatten them in the frozen actor-plus-log_std parameter order.

Convert both flattened vectors to float64.

Compute, without denominator epsilon,

u
REF
	​

=
∥v
REF
	​

∥
2
	​

v
REF
	​

	​

,u
RAW
	​

=
∥v
RAW
	​

∥
2
	​

v
RAW
	​

	​

.

Require the inclusive Euclidean rule

∥u
REF
	​

−u
RAW
	​

∥
2
	​

≤10
−6
.

Any nonfinite norm or normalized coordinate, or a distance greater than 10
−6
, routes to:

INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_ATTRIBUTION_G46

When either assigned gradient is zero, this direction rule is not evaluated; the frozen zero/cancellation cases govern the pass. This closes the previously unspecified result-sensitive tolerance.

smallest_next_boundary=CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_ATTRIBUTION_G46_CODE_SCIENCE_ALIGNMENT_AUDIT

This clarification authorizes no implementation or compute.

G46_CONTRACT_FROZEN
