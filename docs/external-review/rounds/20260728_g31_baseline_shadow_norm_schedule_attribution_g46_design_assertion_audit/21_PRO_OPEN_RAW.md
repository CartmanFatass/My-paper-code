INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_BASELINE_SHADOW_NORM_ATTRIBUTION_G46

design_frozen=false
next_boundary=NONE_UNTIL_G46_CONTRACT_CORRECTION

Contradictory contract field — treatment activation. The question defines

q
norm
	​

=
∣m
B
	​

−m
raw
	​

∣
max(m
B
	​

,m
raw
	​

)
	​


except when both norms are zero, and then requires q_norm > 1e-6. For nonnegative unequal norms this ratio is always at least 1, so an arbitrarily small schedule difference automatically counts as active. When m
B
	​

=m
raw
	​

>0, it divides by zero rather than classifying the treatment as inactive. The gate therefore cannot distinguish a real scalar intervention from numerical near-equality and is inconsistent with its stated purpose.

Missing contract field — direction-equivalence tolerance. The question requires the two nonzero assigned gradients to have matching unit directions under “one frozen proof tolerance,” but supplies neither an exact numerical tolerance nor an explicit inherited tolerance identifier. That leaves a result-sensitive acceptance gate selectable during implementation.

The smallest in-contract correction is to freeze

q
norm
	​

=
⎩
⎨
⎧
	​

0,
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

=m
raw
	​

=0,
max(m
B
	​

,m
raw
	​

)>0,
	​


retain the strict q_norm > 1e-6 activation rule, and bind an exact unit-direction equality tolerance—or exact bitwise equality—before implementation. This changes no arm, source, estimand, margin, branch order, or evidence volume. Threshold arithmetic and zero denominators must be closed before a design freeze.
