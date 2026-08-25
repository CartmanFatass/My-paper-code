# Controller disposition: correction 1 still revives direct IFEPG

Date: 2026-07-15

Source model: GPT-5.6 Pro. The raw correction response is
`RESPONSE_CORRECTION_1_RAW.md`.

## Decision

- Retraction of R35-OCSF: **ACCEPT**.
- Remaining bottleneck may be the latent object itself: **ACCEPT AS AN OPEN
  HYPOTHESIS**.
- Proposed R35-CBF: **REJECT**. No implementation or compute is authorized.

## Decisive rejection reason

R35-CBF defines the same between-latent persistent trajectory separation and
same-latent replica noise used by R32, then applies that effect as a
score-function policy gradient:

```text
D(c,z,z') = ||psi(tau_z) - psi(tau_z')||^2
N(c,z)    = ||psi(tau_z^1) - psi(tau_z^2)||^2
A_CBF     = D - mean(D)
L_CBF     = -E[log pi(a|o,z) * A_CBF]
```

This is direct individual-effect policy-gradient optimization. Calling the
slots "random latent assignments" rather than "existing skills" does not
change the optimized causal object, the K=4 intervention, the low actor input,
or the score-function gradient. R32 already established that this family makes
only a small forced shift and does not create a materially stronger codebook;
its effect, update-count, parameter-scope, label, and capacity variants were
permanently retired. The correction request explicitly prohibited the retired
individual-effect score and direct IFEPG.

## Additional gate defects

- If the sham relabels `z` only after collecting actions under another `z`, its
  policy likelihood is not the behavior likelihood. If it shuffles before
  execution, uniformly random symmetric slots make the distribution a slot
  permutation rather than a disrupted mechanism comparator.
- Forty auxiliary updates, fifteen PPO-style epochs, and `40*32*10` window
  steps do not define when fresh on-policy data is collected; repeated policy
  updates on stale intervention windows violate the policy-version boundary.
- The written `E[D]/(E[N]+epsilon)` objective is not the implemented gradient:
  `A_CBF` contains no `N` term, so within-slot consistency is not optimized and
  stochastic trajectory variance can increase the numerator.
- `P(z -> same process)` has no registered estimator and risks reintroducing a
  prototype or classifier metric.
- The route jumps directly to an effect-driven policy update even though the
  requested first gate was reward-off/gradient-off evidence followed by a
  source-anchored causal intervention.

## Next boundary

The final tracked correction is `GPT5_6_PRO_CORRECTION_2.md`. It requires either
one genuinely different replacement for the discrete skill object or an
explicit decision that no justified post-R34 skill-formation route remains.
Renaming R32 again is not an acceptable answer.
