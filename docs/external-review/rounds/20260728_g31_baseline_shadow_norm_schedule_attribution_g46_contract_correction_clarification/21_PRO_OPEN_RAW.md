Corrected q_norm

Let m
B
	​

 and m
raw
	​

 be the finite, nonnegative float64 global L
2
	​

 norms of the credit-bearing gradients before common entropy is added, using the frozen actor-plus-log_std parameter order.

q
norm
	​

=
⎩
⎨
⎧
	​

undefined and INVALID,
0,
0,
1,
undefined and INVALID,
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


The m_B>0, m_raw=0 case is invalid because the reference arm’s norm-matched direction is undefined; it cannot supply activation evidence. This preserves the previously frozen zero and cancellation semantics.

A valid pass is treatment-active if and only if

q
norm
	​

>10
−6
.

Equality at 10
−6
 is inactive. Thus:

m_B=m_raw=0       → valid, inactive
m_B=m_raw>0       → valid, inactive
m_B=0,m_raw>0     → valid, active because q_norm=1
m_B>0,m_raw=0     → INVALID
positive unequal  → active only when |m_B-m_raw|/max(m_B,m_raw) > 1e-6

This corrects the inverted ratio in the prior question and closes its positive-equality zero denominator.

Unit-direction equality rule

When both assigned credit gradients are nonzero:

Flatten v_REF and v_RAW in the frozen actor-plus-log_std parameter order.

Cast both flattened vectors to float64.

Form

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

Require the inclusive rule

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
	​


with no epsilon added to either denominator.

A distance greater than 10
−6
, or any nonfinite norm or normalized coordinate, routes to:

INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_ATTRIBUTION_G46

If one or both assigned gradients are zero, this direction rule is not evaluated; the frozen zero/cancellation table above governs the pass. This supplies the single numeric metric, comparison operator, and tolerance that the prior contract left unspecified.

smallest_next_boundary=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_SCHEDULE_ATTRIBUTION_G46_CODE_SCIENCE_ALIGNMENT_AUDIT

That boundary becomes applicable only after Code Project Manager independently realizes and technically accepts an exact pushed G46 implementation; this clarification authorizes neither implementation nor compute.

G46_CONTRACT_FROZEN
