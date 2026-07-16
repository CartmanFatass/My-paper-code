# R43-NRC Controller Disposition

Date: 2026-07-16

## Verdict

`INVALID_R43_FIXED_ANCHOR_LOST`

The implementation gate M0 passed, but the registered fixed HMASD
source-continuation anchor failed. The R43-NRC treatment arm therefore has no
scientific PASS or FAIL interpretation and is neither promoted nor retired.

## Direct evidence

- Both arms completed 320,000 environment steps, 200 outer updates, 6,400
  environment-check rows, and 3,000 steps on each of the five source optimizer
  paths.
- Fixed final deterministic win/key0/key1 was `0.52/0.54/0.81`, below the
  registered `0.80/0.85/0.85` M1 floor.
- The original R41B checkpoint scored win `0.89` on the R41B reset stream and
  `0.93` on the R43 reset stream. The R43 fixed final checkpoint scored
  `0.61/0.52` on those two streams. The anchor loss is not an evaluation-stream
  artifact.
- A two-update same-seed comparison of untouched source continuation with the
  R43 fixed wrapper produced maximum parameter difference `0` for the high
  policy, low actor, low critic, team discriminator, and individual
  discriminator. The wrapper does not explain the observed drift.

## Boundary

The fixed source checkpoint is positive before continued optimization, but the
registered 320K continuation is not a stable service control under seed 43041.
The treatment's zero final win, deterministic all-RENEW behavior, and temporal
metrics are quarantined because M1 failed. No R43 rerun, seed substitution,
budget or threshold change, reward change, or successor experiment is
authorized before the external review selects one exact next causal edge.

## GPT-5.6 Pro review disposition

Source: GPT-5.6 Pro raw response, 2026-07-16,
`GPT5_6_PRO_RESPONSE_RAW.md`.

Accepted:

- confirm `INVALID_R43_FIXED_ANCHOR_LOST`;
- accept the fixed wrapper as source-equivalent without another wrapper audit;
- retain the R43 factorization, replay, clock, and gradient results as
  diagnostic-only evidence;
- select only `R44-FS-NRC`, which freezes the complete R41B source skill system
  and compares an inactive zero renewal actor with the same actor trained by a
  separate renewal-only optimizer.

R43 is not rerun and its treatment is not retired or interpreted. R44 does not
change the low policy, source coordinator, discriminators, ValueNorms,
intrinsic reward, task reward, seed, budget, clock, or registered thresholds.
