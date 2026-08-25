# R47-NSOPM-G0 Controller Disposition

Date: 2026-07-16

## Verdict

`VALID_FAIL_R47_NSOPM`

The registered local CUDA gate is implementation-valid. The frozen natural
process estimator found stable half-fit structure and passed the nuisance
shortcut audit, but it did not establish four temporal-null-significant modes
or lag-5 heldout coherence. Forced skills also failed the registered support,
assigned-mode, and between/within causal-SNR requirements.

## Direct evidence

- M0 passed: 512 complete natural `[10,7]` windows, 64 matched contexts,
  512 forced branches, 20,480 forced steps, zero early resets, exact snapshot
  restoration, exact parameter freeze, zero optimizer steps, and no reward
  field in evidence. The three singleton-covariance fields were exactly zero.
- The primary and both half estimators each retained 14 nontrivial modes.
  Half-to-primary matches were `0.9568--0.9933`; aligned A/B stability was
  `0.8759--0.9610`. The maximum nuisance test R2 was `-0.0713`, so these two
  parts of M1 passed.
- Only eigen-rank 0 exceeded its rank-matched temporal-null q95. Ranks 1--3
  were `0.24214/0.21097/0.18614` versus null q95
  `0.26078/0.22241/0.19868`. Lag-1 coherence difference had lower bound
  `0.00433`, but lag-5 had lower bound `-0.04475`. M1 therefore failed.
- H10 complete-context support was `46/64=0.71875`, below `0.80`; H40-late
  support was `53/64=0.828125`. H10 assigned-mode contrast was `0.00194` with
  lower bound `-0.000652`; H40-late was positive pooled, but skill 0 was
  `-0.01542`. Between/within causal-SNR means were only `0.0343` and `0.1992`,
  both far below the registered lower-bound requirement `>1`. M2 failed.
- The intersection persistence ratio was `3.696`, but persistence alone cannot
  override failed support, temporal-null, assigned-mode, or causal-SNR gates.

## Binding conclusion

The source has repeatable low-dimensional natural dynamics, but under the
registered representation most of that structure is not stronger than the
within-window temporal null, and frozen numeric skill labels do not reliably
occupy the corresponding spectral ranks with between-skill variation greater
than stochastic replica variation. The exact 7-D view, initial-centering,
35-D quadratic map, lags `{1,5}`, whitened Gram estimator, four spectral-rank
identities, candidate score, and reward-on pair are retired without rescue.
No reward-on experiment is authorized by this result.

## GPT-5.6 Pro disposition

- Source: GPT-5.6 Pro, 2026-07-16.
- Raw response: `GPT5_6_PRO_RESPONSE_RAW.md`.
- Disposition: **accept** `CONFIRM VALID_FAIL_R47_NSOPM`, the no-rescue
  retirement of the exact R47 line, and the single selected successor
  `R48-SBRS-G0`.
- Boundary: R48 changes only the focal low-actor recurrent hidden state at a
  forced nonincumbent skill SET. It adds no reward, classifier, mode estimator,
  scorer, optimizer, model capacity, task field, or R47 rescue. A valid R48
  failure permanently stops fixed-`N` skill/lifetime algorithm exploration.
