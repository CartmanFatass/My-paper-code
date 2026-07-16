# R48-SBRS-G0 Controller Disposition

Date: 2026-07-16

## Verdict

`VALID_FAIL_R48_SBRS`

The registered local CUDA gate is implementation-valid, but resetting only the
focal low-actor recurrent hidden state at a forced nonincumbent skill SET did
not materially reduce same-skill stochastic variability or produce the
required reset-versus-carry causal-SNR gain.

## Direct evidence

- M0 passed every registered check: 64 exact source contexts, 384 branches per
  arm, 768 complete branches, 30,720 forced steps, zero early resets, exact
  snapshot restoration, exact matched arm starts and Gaussian innovation tape,
  exact focal-hidden intervention, exact parameter/normalizer freeze, zero
  optimizer steps, no task/reward evidence field, finite statistics, and target
  support `47/48/50/47`.
- H10 reset rho was `1.19670`, but its lower 95% bound was `0.98468`. The
  reset/carry rho-ratio lower bound was `1.11816`, below `1.25`, and the
  within-ratio upper bound was `1.01877`, not below `0.80`. Only the
  between-ratio preservation gate passed.
- H40-late reset rho and all four target-conditional rhos exceeded one, and the
  between-ratio lower bound was `1.00776`. However, the reset/carry rho-ratio
  lower bound was only `1.00223`, and the within-ratio upper bound was
  `1.00874`. Reset therefore preserved process differences but did not lower
  same-skill stochastic variability.

## Binding conclusion

The registered recurrent-contamination explanation is rejected. Permanently
retire SET-time focal zero-reset, the shared-parameter skill-boundary-reset
line, and this raw-trajectory between/within gate. Under the registered branch,
fixed-`N` skill/lifetime algorithm exploration stops without additional seed,
context, budget, threshold, model, reward, environment, or best-checkpoint
rescue. Open-roster or variable-`N` work, if separately justified, cannot
inherit a claim that the fixed-`N` skill mechanism or skill semantics work.
