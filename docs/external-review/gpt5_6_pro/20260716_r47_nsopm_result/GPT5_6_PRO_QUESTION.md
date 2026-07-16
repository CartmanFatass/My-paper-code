# GPT-5.6 Pro Review — R47-NSOPM-G0 Result and Next Causal Edge

## Review mode

Read-only scientific and implementation review. Do not modify the repository,
run experiments, propose parallel routes, or rescue a failed branch through
window, lag, mode count, encoder, kernel, seed, data, model, threshold,
post-hoc alignment, task field, action likelihood, reward, or environment
changes.

## Claim under review

The launch-exact R47-NSOPM-G0 gate completed as `VALID_FAIL_R47_NSOPM`.
M0 passed. M1 failed because only spectral rank 0 exceeded its matched temporal
null and lag-5 heldout coherence did not have a positive lower bound. M2 failed
because H10 support was below 0.80, H10 assigned-mode contrast crossed zero,
H40 skill 0 contrast was negative, and both between/within causal-SNR lower
bounds were far below 1. The controller therefore retired the exact registered
view, feature map, spectral ranks, score, and reward-on pair without launching
reward-on training.

## Repository files to inspect

Read all of these before deciding:

1. `memory/ALGORITHM_PRINCIPLES.md`
2. `memory/CURRENT_WORK.md`
3. `memory/IMPLEMENTATION_PLAN.md`
4. `memory/ExpRecord.md` — the R47 dashboard row and detailed contract
5. `scripts/r47_nsopm.py`
6. `scripts/run_r47_nsopm_gate.py`
7. `scripts/analyze_r47_nsopm.py`
8. `scripts/run_r47_nsopm_local.ps1`
9. `docs/external-review/gpt5_6_pro/20260716_r46_hmrv_result/GPT5_6_PRO_RESPONSE_RAW.md`
10. `docs/external-review/gpt5_6_pro/20260716_r46_hmrv_result/GPT5_6_PRO_R47_CONTRACT_CLARIFICATION_RESPONSE_RAW.md`
11. `docs/external-review/gpt5_6_pro/20260716_r47_nsopm_result/r47_nsopm.json`
12. `docs/external-review/gpt5_6_pro/20260716_r47_nsopm_result/DISPOSITION.md`

The formal run root is `logs/r47_nsopm_20260716_172711`; the copied JSON above
is the tracked authoritative scientific result. Pre-launch implementation
commit is `078845b`.

## Requested decision

Return exactly one coherent disposition:

1. Audit whether the implementation and analyzer preserve the accepted R47
   seven-dimensional view, natural staggered schedule, split-specific
   normalization, 35-D map, pooled-lag whitening, temporal null, half-fit
   alignment, coherence, nuisance regression, forced snapshot/CRN boundary,
   support rule, assigned-mode contrast, causal-SNR, bootstrap, M0--M2, and
   terminal branch contracts. If not, identify one concrete result-changing
   M0 defect and label the run invalid.
2. Otherwise explicitly confirm or reject `VALID_FAIL_R47_NSOPM` and the
   no-rescue retirement of the exact view, spectral basis, score, and reward-on
   pair.
3. State the reusable causal conclusion separating natural low-dimensional
   repeatability, temporal-null significance, long-lag coherence, natural
   support, skill-conditioned mode occupancy, and stochastic execution noise.
4. Decide whether fixed-N skill/lifetime exploration should stop. If one next
   edge remains justified, select exactly one structurally different,
   falsifiable fixed-N route, with no environment-specific intrinsic reward,
   and give its smallest numeric abandonment gate with explicit
   PASS/VALID-FAIL/INVALID branches. It must not be a disguised R47 rescue and
   must precede open-roster or variable-N work. If no justified edge remains,
   state that as the single disposition.
5. List all permanently closed branches and prohibit threshold, seed, budget,
   model, reward, or environment rescue.
