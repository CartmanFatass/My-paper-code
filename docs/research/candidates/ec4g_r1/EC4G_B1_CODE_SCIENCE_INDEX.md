# EC4G-B1 code-science index

## Frozen treatment

- Identity: `EC4G-B1-LEAVE-RECEIPT-CONTENT-LEARNING-DISCRIMINATOR`
- Direction: `CAND-VAP-EC4G-R1@rer3-prospective-complete-v8`
- Resource forecast: `B_TOY_LIGHT`, one pool unit, CPU only, one process,
  at most 2 GiB and 60 minutes.
- Scientific boundary: this treatment tests learned raw receipt-content use and
  calibration-only gate divergence. It does not test or presume EC4G value.
  Branch 9 is explicitly a finite-panel anomaly.

## Production surfaces

- Implementation:
  `experiments/candidates/ec4g_r1/leave_receipt_content_learning_discriminator.py`
- One-shot runner:
  `scripts/run_ec4g_b1_leave_receipt_content_learning_discriminator.py`
- Focused tests:
  `tests/experiments/candidates/ec4g_r1/test_leave_receipt_content_learning_discriminator.py`
- Canonical retained result after the one authorized full:
  `docs/research/candidates/ec4g_r1/EC4G_B1_LEAVE_RECEIPT_CONTENT_LEARNING_DISCRIMINATOR_RESULT.json`

## Bound mechanics

The implementation freezes the fresh four-transition host, raw-tag and donor
construction, seven arms, eight paired outer seeds, random-access tuple RNG,
shared 32-unit GRU/A2C learner, final-checkpoint rule, post-freeze calibration,
two gate rules, forced and autonomous panels, exact activity caps, and the
nine-way first-true branch map. Treatment identity is absent from all RNG keys
and from actor/critic/optimizer/calibration construction. It enters only when
the sealed `T/C/V` inputs are consumed by the two gate rules.

The runner writes an immutable manifest, supports a zero-full technical proof,
claims the sole registered paired full exclusively, and writes either the
canonical result or a terminal first-failure receipt. The `validate` command is
retained-data-only: it does not call the environment, policy runner, learner,
trainer, optimizer, evaluator, or RNG.

## Acceptance boundary

This index records implementation intent only. Code Project Manager owns source
freeze, readiness, the unique full, publication, Git integration, and sole
technical acceptance. Explorer owns the sole scientific intake and any later
scientific choice. No retry, rescue, sweep, C, Pro, promotion, retirement, or
successor follows from this file or any result branch.

## Registered publication — 2026-08-10

The retained registered full is published mechanically from source revision
`d4b5f6b707e5de2cdaaa88edf968a7629d7abcdd`. The raw branch is
`B1_ACTIVITY_OR_EVALUATION_PANEL_INCOMPLETE`; the code result is not accepted
because the top-level activity is exact while `_metric_gates` omits the
treatment-level `registered_paired_fulls=1` when summing units. Correcting only
that omission would mechanically reach
`B1_CONTENT_OR_PHYSICAL_CALIBRATION_FAILED`; this is not an accepted or
reclassified result and makes no EC4G value/science, successor, C, or Pro
claim. The run has one full and no retry/rescue/sweep. The pure retained-data
validator is `VALID`.

```text
activity=episodes=122880|transitions=491520|batched_policy_calls=491520|active_agent_forward_rows=1105920|training=28672|calibration=28672|forced_evaluation=57344|autonomous_evaluation=8192|held_out_evaluation=65536|learner=2048|trainer=2048|optimizer=2048|table_updates=28672|checkpoints=16|registered_fulls=1|retry_rescue_sweep=0
aggregates=delta_j=-0.007578125000000359|balanced_probe_selectivity=0.0|generic_physical_effect=0.017109375000000843|q0_both_gates_p_units=1|q1_direct_p_ec4g_a_units=3|q0_RV-RS=-0.042968750000000215|q0_RV-RB=-0.031250000000000194|q0_PV-PS=0.00048828125|q0_PV-PB=-0.01123046875|q1_RV-RS=0.007812500000000111|q1_RV-RB=0.014648437500000208|q1_PV-PS=-0.00439453125|q1_PV-PB=-0.00634765625
source_readiness=.git/worktrees/ec4g_b1_source_readiness_d4b5f6b7_r2_20260810/hmasd/execution-readiness/d4b5f6b707e5de2cdaaa88edf968a7629d7abcdd/ec4g-b1-source-readiness-20260810-r3.json
operator_receipt=temp/sessions/code_project_manager/ec4g_b1_operator_receipt.json
postfull_retained_check=temp/sessions/code_project_manager/ec4g_b1_postfull_retained_checks_result.json
```

