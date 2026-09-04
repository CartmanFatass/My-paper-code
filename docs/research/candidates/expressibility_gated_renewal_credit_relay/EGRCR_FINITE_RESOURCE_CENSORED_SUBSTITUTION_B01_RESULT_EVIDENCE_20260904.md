# EGRCR finite-resource censored-substitution B01 result evidence — 2026-09-04

Object: `EGRCR-FRCS-B01-20260904`

Evidence class: `B/EXPLORE`

Result branch: `FRCS-D-MIXED`

Launch SHA: `3c9124396430e88c619e91831cd7f8e14a08fa75`

Scientific seed: `2026090401`

## E0 result

The single paired invocation is complete and valid. The competent unrestricted pair-cell critic
estimated exact conditional Q and the corresponding source gradient more accurately than the
association-factorized critic, but the factorized critic produced a larger temperature-one action
gap and therefore higher exactly enumerated expected utility. Both learned critics ranked the
correct relation in all eight source/content contexts, and their paired sampled utility was equal.
This is the card's mixed branch and supplies no clean finite-resource factorization polarity.

This is a direct one-seed observation on the frozen four-agent host. It is not a stable comparison,
an information-necessity result, or evidence for a deployable relay.

## Launch, admission, and terminal observation

The prelaunch focused suite passed on the integrated launch bytes:

```text
16 passed, 1 existing cache_dir warning in 11.14 s
```

The runner's non-result static projection emitted `119.64` seconds per learned arm, below the
`600`-second per-arm cap, and emitted the frozen exposure line. Immediately before the result
invocation, `scripts/hmasd_resource_preflight.py admit-memory` recorded:

| Quantity | Observation |
| --- | ---: |
| available physical memory | `9,288,708,096` bytes |
| effective available memory | `9,288,708,096` bytes |
| required floor | `4,294,967,296` bytes |
| physical/effective pass | `true / true` |

The run was launched hidden and detached as PID `28440`. It terminated, wrote exactly one
`summary.json`, printed `FRCS-D-MIXED`, and left an empty stderr log. The detached process handle was
not retained, so an external exit code is unavailable. The complete result, terminal process
observation, empty stderr, and runner-integrity surface are direct evidence; the missing external
exit code is not repaired or inferred.

Runtime artifacts:

- `temp/directions/expressibility_gated_renewal_credit_relay/exp/frcs_b01_20260904/summary.json`
- `temp/directions/expressibility_gated_renewal_credit_relay/exp/frcs_b01_20260904_admission.json`
- `temp/directions/expressibility_gated_renewal_credit_relay/exp/frcs_b01_20260904.stdout.log`
- `temp/directions/expressibility_gated_renewal_credit_relay/exp/frcs_b01_20260904.stderr.log`

## Integrity, work, and exposure

The summary records `scientific_contract_exact=true`, `technical_execution_complete=true`,
`complete_and_valid=true`, nonzero required counts, both parameter vectors moved, no nonfinite
target/loss/prediction/parameter, and all wall caps respected.

| Count | Observation |
| --- | ---: |
| shared training episodes / native transitions | `192 / 576` |
| optimizer updates per learned arm | `128` |
| example exposures per learned arm | `4,096` |
| total optimizer updates / exposures | `256 / 8,192` |
| evaluation episodes / transitions per arm or reference | `256 / 768` |
| total evaluation transitions | `2,304` |
| exact evaluation cells per arm or reference | `48` |
| trainable parameters per learned arm | `32` |

The sampled training population was shared exactly: source counts `(52,41,47,52)`, content counts
`(+1=99,-1=93)`, action counts `(+1=88,-1=104)`, and mode counts
`PERSIST=68, REPLACE=70, EXPIRE=54`. Both arms used identical terminal returns, minibatch indices,
FP32, the same flat 32-scalar initialization bytes, zero Adam moments and step, and the frozen arm
order `GENERIC_PAIR` then `ASSOCIATION_FACTOR`. The two layouts were different as declared; tensor
shape identity was never claimed. Actual Adam state bytes matched at `260` per arm.

The machine-generated exposure line was:

```text
updates=128; adam_lr=0.01; nominal_lr_exposure=1.28;
init_half_range=0.05; nominal_exposure_over_init_half_range=25.6
```

All 32 coordinates moved in both arms. Observed maximum-coordinate displacement over initialization
half-range was `16.4382767677` for `GENERIC_PAIR` and `15.1227581501` for
`ASSOCIATION_FACTOR`.

Peak RSS was unavailable, so the valid run is marked `resources_unmeasured` under the owner telemetry
rule. Total measured invocation wall time was `3.2284484` seconds. Complete arm-work wall time was
`3.0557292` seconds for `GENERIC_PAIR` and `0.1560825` seconds for
`ASSOCIATION_FACTOR`, both below cap. These timings do not support a compute-efficiency claim:
the frozen analytical forward work differed (`4,112/4,112` multiplies/adds for generic versus
`12,336/16,448` for factor), and backward/optimizer arithmetic was not claimed.

## Primary observations

| Observable | `GENERIC_PAIR` | `ASSOCIATION_FACTOR` | Exact-Q reference |
| --- | ---: | ---: | ---: |
| exact action-ranking competence `C_Q` | `8/8` | `8/8` | `8/8` |
| Q RMSE | `0.0527587559` | `0.0962653460` | `0` |
| maximum absolute Q error | `0.1460960706` | `0.2827973564` | `0` |
| source-gradient L2 error | `0.0523571133` | `0.0982021395` | `0` |
| source-gradient cosine to exact | `0.9945215316` | `0.9923031656` | `1` |
| mean probability on matching relation | `0.6644999725` | `0.6825671204` | `0.6607563688` |
| enumerated expected bounded utility | `0.4429999817` | `0.4550447470` | `0.4405042458` |
| paired sampled bounded utility | `0.484375` | `0.484375` | `0.48046875` |
| first / last training loss | `0.2890386581 / 0.1275905520` | `0.2979082465 / 0.1294161528` | not learned |

The card's signed primary differences were observed exactly as:

```text
Delta_Q = RMSE_GENERIC - RMSE_FACTOR             = -0.04350659008150653
Delta_g = grad_error_GENERIC - grad_error_FACTOR = -0.04584502615935601
Delta_U = utility_FACTOR - utility_GENERIC       = +0.012044765264439206
```

Thus the generic comparator is competent and wins both registered estimation readings, while the
factorized arm wins the smooth temperature-one expected-utility reading. Both greedy rankings are
perfect and the finite paired sampled utility is tied.

The exact-Q arm is a temperature-one calibrated reference, not a native-optimal ceiling. Learned
predictions can exceed its expected utility by inflating the action-value gap; that is not evidence
that their Q estimate is more exact.

## Frozen rule applied verbatim

The earlier branches do not match:

- `FRCS-E-GENERIC-UNDEREXPOSED` is false because `C_Q_GENERIC=8`;
- `FRCS-A-FACTORIZED-ENDPOINT-GAIN` and `FRCS-B-ESTIMATION-ONLY` are false because both
  `Delta_Q` and `Delta_g` are negative; and
- `FRCS-C-GENERIC-MATCHES-OR-BEATS` is false because `Delta_U` is positive.

The first matching card branch is:

> `FRCS-D-MIXED` — Every other complete combination. Preserve the exact discordance; no clean
> efficiency polarity is inferred.

## Deviations and anomalies

- No scientific configuration, target, seed, arm, update, count, stop rule, or result rule changed.
- The replacement carrier was clarified before tests and result as the opposite-ring non-waiter
  `(s+2) mod 4`; the unselected eligible waiter never substitutes.
- Peak RSS and detached external exit code are unavailable. Peak RSS is covered by the telemetry
  rule; neither missing field removes learner-side measurements or changes the estimand.
- The two model equations have equal parameter and optimizer-state counts but unequal analytical
  forward arithmetic. This was declared prospectively and prevents a compute-efficiency reading.
- Training cell counts are seed-realized rather than exactly balanced, shared by both arms, and
  reported rather than repaired.

## Bounded result

On this seed, host, batch, initialization, and 128-update budget, the association-factorized critic
did not improve exact conditional-Q or source-gradient estimation over the competent pair-cell
critic. It produced a more decisive temperature-one policy and a `0.0120448` expected-utility gain,
but that movement coexisted with larger Q and gradient errors, identical `8/8` greedy competence,
and identical sampled utility. The result therefore supports neither clean factorization efficiency
nor clean factorization failure on native utility. It is a valid mixed B observation.
