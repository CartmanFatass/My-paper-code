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

