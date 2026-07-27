AUDIT_DISPOSITION=MISMATCH

Frozen assertion: treatment activation must be reconstructed entirely from the DBNORM reference arm’s pre-update state:

q=
max(m
DB
	​

,
2
1
	​

∥g
I
	​

+g
S
	​

∥
2
	​

)
	​

m
DB
	​

−
2
1
	​

∥g
I
	​

+g
S
	​

∥
2
	​

	​

	​

.

Every reference-arm pass must serialize its own db_norm, raw_sum_norm, and equal_mean_norm; the null arm may not supply evidence for this gate.

Conflicting behavior: _prepare_passes forms dbnorm from the DBNORM arm’s gradients but forms mean from the independently evolving MEAN arm’s gradients, then passes those two cross-arm objects to treatment_schedule_record. That function computes q from the DBNORM arm’s registered_gradient_norm and the MEAN arm’s applied_gradient_norm. After the first update, the two policies and trajectories may differ, so this quantity conflates scalar-schedule treatment with downstream arm-state divergence. It can falsely activate the treatment when the two scalar laws coincide on the reference state, or conceal activation when they differ there.

The focused positive test exercises only the first paired update, where the branch states and channel gradients are still bitwise equal, so cross-arm and reference-arm q coincide; it does not expose the later-update bypass before conclusion evidence is accepted.

Smallest in-contract correction: retain the actual MEAN arm update unchanged, but construct a separate reference-arm equal-mean counterfactual 0.5*(g_I+g_S) from the DBNORM arm’s own pre-update channel gradients solely for treatment_schedule_record and conclusion activation. Serialize and reconstruct q only from the DBNORM arm’s db_norm, reference raw-sum norm, and reference equal-mean norm. Add a focused guard that deliberately changes only the MEAN arm’s gradients after branch divergence and proves that reference-arm q and its activation decision remain unchanged; also prove that a reference-arm q≤10
−6
 cannot pass merely because the MEAN arm’s norm differs. No arm formula, source, optimizer, threshold, evidence volume, confidence procedure, or first-match branch needs to change.
