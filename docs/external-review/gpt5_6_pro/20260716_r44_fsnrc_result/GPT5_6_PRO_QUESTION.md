# GPT-5.6 Pro Review — R44 Valid Frozen-Source Timing Failure

Review the repository state at the exact commit supplied in the handoff prompt.
This is a read-only scientific and implementation review. Do not edit files,
launch experiments, or substitute a neighboring commit.

## Question

R44-FS-NRC tested whether a separate per-agent renewal factor can learn useful
timing while the complete successful R41B skill system remains frozen. It used
two mechanism-matched arms: an inactive zero renewal actor and the same actor
trained with the registered next-check renewal credit. Both renewal critics
were trained; no source policy, critic, discriminator, optimizer, ValueNorm,
reward, or intrinsic-reward parameter was updated.

The run completed:

```text
status: VALID_FAIL_R44_FSNRC

M0 implementation and frozen source: PASS
M1 frozen service anchor:             PASS
M2 service safety:                    PASS
M3 temporal decoupling:               FAIL

control final win/key0/key1:   0.93 / 1.00 / 0.93
treatment final win/key0/key1: 0.93 / 1.00 / 0.93
treatment-minus-control win CI: [0, 0]

treatment actor relative drift:          0.353245
treatment actor nonzero-gradient steps:  3000 / 3000
control actor drift/nonzero steps:        0 / 0
source module/optimizer/ValueNorm drift:  0 in both arms
replay and conditional-ratio error:       0

control/treatment discordance:          0 / 0
control/treatment full-sync RENEW:       1.0 / 1.0
control/treatment min KEEP/RENEW share:  0 / 0
zero and final deterministic outcomes:  exactly equal across arms
zero and final high/low action traces:  exactly equal across arms
```

The first analyzer pass incorrectly required each critic to have a nonzero
gradient on all 3,000 factor steps. The registered contract required finite
critic gradients and at least one nonzero exposure. Control and treatment had
3,000 and 2,992 nonzero-gradient steps, respectively, and all 3,000 checks were
finite. The condition was corrected to `critic_nonzero_steps > 0`; only the
analyzer was rerun. No training, threshold, artifact, or metric changed.

The controller disposition is to treat this as a valid scientific failure and
permanently retire frozen-source `K=50` timing-only renewal with this
next-check credit. We need a review of that boundary and exactly one
structurally different causal edge. A successor must explain why it is not a
hidden retune of R42, R43, or R44 and must preserve environment-agnostic
intrinsic reward.

## Repository files to inspect

Read all of the following before answering:

- `AGENTS.md`
- `memory/CURRENT_WORK.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/IMPLEMENTATION_PLAN.md` (R41B--R44 boundary)
- `memory/ExpRecord.md` (R41B--R44 contracts and decisions)
- `docs/external-review/gpt5_6_pro/20260716_r44_fsnrc_result/r44_frozen_source_nrc_compact.json`
- `docs/external-review/gpt5_6_pro/20260716_r44_fsnrc_result/DISPOSITION.md`
- `scripts/r44_frozen_source_nrc.py`
- `scripts/run_r44_frozen_source_nrc_arm.py`
- `scripts/analyze_r44_frozen_source_nrc.py`
- `scripts/run_r44_frozen_source_nrc_local.ps1`
- `docs/external-review/gpt5_6_pro/20260716_r43_nrc_result/GPT5_6_PRO_RESPONSE_RAW.md`
- `docs/external-review/gpt5_6_pro/20260716_r43_nrc_result/DISPOSITION.md`
- `docs/external-review/gpt5_6_pro/20260716_r43_nrc_result/r43_native_renewal.json`
- `docs/external-review/gpt5_6_pro/20260716_r43_nrc_result/fixed_source_two_update_parity.json`
- `docs/external-review/gpt5_6_pro/20260716_r42_irr_result/r42_irr_native_roster_residual.json`
- `docs/external-review/gpt5_6_pro/20260716_r42_irr_result/fixed_refresh_seed_result.json`
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/r41b_hmasd_alice_bob_full_source.json`
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/seed1_result.json`
- `docs/external-review/gpt5_6_pro/20260716_r41b_source_access_result/FINAL_DISPOSITION.md`
- `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/runner/shared/alice_and_bob_runner.py`
- `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/algorithms/mat/algorithm/ma_transformer.py`
- `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/algorithms/mat/mat_trainer.py`

The compact R44 JSON was generated mechanically from the authoritative local
result. It preserves the registered contract, gates, paired statistics,
per-arm arguments, installation/freeze evidence, optimizer and gradient
telemetry, clock metrics, outcomes, renewal events, and exact trace-equality
booleans. It omits only the large raw per-step action arrays; it contains no
hashes or manually recomputed scientific metrics.

## Requested decision

Return one integrated answer containing:

1. **Validity verdict.** Confirm or reject `VALID_FAIL_R44_FSNRC`. Audit the
   analyzer correction against the registered M0 contract and name any
   concrete implementation, factorization, likelihood, credit, clock, reset,
   freeze, checkpoint, evaluation, or analyzer defect that changes the branch.
2. **Reusable causal conclusion.** State exactly what the combination of
   preserved service, strong treatment-actor drift, nonzero gradients, and
   identical deterministic behavior establishes. Separate actor connectivity,
   estimator informativeness, stochastic policy movement, deterministic
   transport, and task service.
3. **Retirement boundary.** Confirm, narrow, or reject permanent retirement of
   frozen-source `K=50` timing-only renewal with the registered next-check
   credit. Identify what remains untested; do not generalize this result to all
   asynchronous skill learning.
4. **Exactly one next causal edge.** Select one structurally different,
   falsifiable route. It must name the failed edge it repairs and explain why it
   is not a learning-rate, entropy, temperature, budget, seed, threshold,
   evaluator, or stochastic-action rescue of R44.
5. **Exact algorithm contract.** Specify the policy factorization, time and
   reset semantics, information boundary, credit estimand, updated and frozen
   parameters, optimizer/checkpoint migration boundary, intrinsic-reward
   boundary, and mechanism-matched comparator for the selected route.
6. **Minimum Alice--Bob abandonment gate.** Give exact arms, seed policy,
   environment count, environment steps, optimizer exposures, evaluation mode
   and episode count, M0 checks, scientific metrics and thresholds, and
   mutually exclusive PASS/FAIL/INVALID branches. Use the smallest evidence
   boundary that can falsify the new causal edge.
7. **Evidence and claim boundary.** State what R41B, R42, invalid R43, and valid
   R44 jointly establish and what they do not establish about skill semantics,
   cooperation, sparse exploration, S7 transfer, open rosters, and variable
   team membership.
8. **Prohibitions and strongest objection.** Do not rescue R42--R44 through
   extra seeds, more steps, new thresholds, entropy/temperature changes, reward
   shaping, environment-specific intrinsic reward, task fields, duration
   categories, S7 promotion, open-roster promotion, or variable-`N` work. Give
   the strongest objection to the selected route and whether it changes the
   verdict.

Choose one next route and one abandonment gate, not a menu or parallel plan.
Do not equate entropy, actor parameter drift, stochastic distribution movement,
renewal frequency, or action-space size with useful temporal abstraction,
skill semantics, cooperation, or task improvement.
