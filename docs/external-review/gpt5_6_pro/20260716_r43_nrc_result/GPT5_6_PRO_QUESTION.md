# GPT-5.6 Pro Review — R43 Invalid Fixed-Anchor Boundary

Review the repository state at the exact commit supplied in the handoff prompt.
This is a read-only scientific and implementation review. Do not edit files,
launch experiments, or use a neighboring commit as substitute evidence.

## Question

R43-NRC was the accepted reset-censored, source-global-clock implementation of
true per-agent renewal. The paired run completed, and M0 passed, but the fixed
HMASD continuation lost the registered R41B service anchor:

```text
status: INVALID_R43_FIXED_ANCHOR_LOST
fixed final win/key0/key1: 0.52 / 0.54 / 0.81
registered floors:        0.80 / 0.85 / 0.85
treatment final win:      0.00  (quarantined; not scientific evidence)
```

The failure was localized with two bounded diagnostics:

```text
R41B source checkpoint, seed-1 evaluation stream:      win 0.89
R41B source checkpoint, seed-43041 evaluation stream:  win 0.93
R43 fixed final, seed-1 evaluation stream:              win 0.61
R43 fixed final, seed-43041 evaluation stream:          win 0.52

untouched source continuation vs R43 fixed wrapper,
same checkpoint/seed and two updates:
global max parameter difference across all five trained modules = 0
```

Thus the new evaluation stream is not the carrier, and the fixed wrapper is
source-exact at the directly compared boundary. Continued optimization of the
solved R41B checkpoint is itself unstable in this registered continuation,
despite R42's seed-42041 fixed continuation ending at win 0.98.

We need one decision that preserves negative-result discipline without using a
fragile continued-training control to make every temporal mechanism test
uninterpretable.

## Repository files to inspect

Read all of the following before answering:

- `AGENTS.md`
- `memory/CURRENT_WORK.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/IMPLEMENTATION_PLAN.md` (R41B--R43 boundary)
- `memory/ExpRecord.md` (R41B--R43 contracts and decisions)
- `docs/external-review/gpt5_6_pro/20260716_r43_nrc_result/r43_native_renewal.json`
- `docs/external-review/gpt5_6_pro/20260716_r43_nrc_result/fixed_refresh_seed_result.json`
- `docs/external-review/gpt5_6_pro/20260716_r43_nrc_result/r43_nrc_seed_result.json`
- `docs/external-review/gpt5_6_pro/20260716_r43_nrc_result/fixed_anchor_cross_eval.json`
- `docs/external-review/gpt5_6_pro/20260716_r43_nrc_result/fixed_source_two_update_parity.json`
- `docs/external-review/gpt5_6_pro/20260716_r43_nrc_result/DISPOSITION.md`
- `scripts/r43_native_renewal.py`
- `scripts/run_r43_native_renewal_arm.py`
- `scripts/analyze_r43_native_renewal.py`
- `scripts/run_r43_native_renewal_local.ps1`
- `docs/external-review/gpt5_6_pro/20260716_r42_irr_result/r42_irr_native_roster_residual.json`
- `docs/external-review/gpt5_6_pro/20260716_r42_irr_result/fixed_refresh_seed_result.json`
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/r41b_hmasd_alice_bob_full_source.json`
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/seed1_result.json`
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/FINAL_DISPOSITION.md`
- `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/runner/shared/alice_and_bob_runner.py`
- `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/algorithms/mat/algorithm/ma_transformer.py`
- `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/algorithms/mat/mat_trainer.py`

## Requested decision

Return one integrated answer containing:

1. **Validity verdict.** Confirm or reject `INVALID_R43_FIXED_ANCHOR_LOST`.
   Identify any concrete implementation, replay, clock, reset, checkpoint,
   optimizer, evaluation, or analyzer defect that changes the branch. Do not
   call an unfavorable seed outcome an implementation defect.
2. **Fixed-path equivalence verdict.** Decide whether the code plus zero
   two-update parameter difference is sufficient to treat the R43 fixed wrapper
   as the original HMASD continuation. If it is insufficient, name exactly one
   smallest decisive diagnostic; do not request a menu of audits.
3. **Reusable conclusion.** Separate what is established about source
   checkpoint access, source-continuation stability, the R43 wrapper, and the
   NRC treatment from what remains unidentifiable. The treatment must not be
   retired from an invalid fixed anchor.
4. **One next causal edge.** Select exactly one falsifiable route. It may repair
   the comparator/continuation boundary or retire this checkpoint-continuation
   testing design, but it must not return parallel alternatives.
5. **Exact comparator and update contract.** State which checkpoint and
   modules are frozen or updated, how treatment and control remain
   mechanism-matched, how pre-existing service is protected, and which metric
   owns the scientific comparison. Explain why the choice does not merely
   select the favorable R42 seed or make a frozen-vs-trained comparison.
6. **Minimum abandonment gate.** Give the smallest local Alice--Bob run or
   diagnostic required for the selected edge, with arms, seed policy, env
   count, environment steps, optimizer exposures, evaluation episodes, M0 and
   scientific thresholds, and mutually exclusive PASS/FAIL/INVALID branches.
7. **Treatment disposition.** State whether any R43 treatment evidence is
   reusable as diagnostic-only information and explicitly prohibit scientific
   claims from its zero-win or renewal statistics under the failed M1 anchor.
8. **Prohibitions and strongest objection.** No seed substitution, threshold
   weakening, extra budget, extra seeds, reward shaping, environment-specific
   intrinsic signal, task field, duration-category action, R42 rescue, S7, or
   variable-`N` promotion may be used to rescue this run. Give the strongest
   objection to the selected next edge and whether it changes the verdict.

The answer must choose one next causal edge and one minimum evidence boundary.
Do not equate label entropy, deterministic renewal frequency, or a larger
action space with useful temporal abstraction, skill semantics, or cooperation.
