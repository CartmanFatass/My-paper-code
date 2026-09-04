# UCOPE root target-versus-fit R01 — remote attempt-02 evidence

- Direction: `ucope`
- Object: `UCOPE-A-RECON-THREE-WITNESS-ROOT-TARGET-VS-ROOT-FIT-AUDIT-R01`
- Evidence class: **A/RECON**
- Frozen card: `UCOPE_ROOT_TARGET_VS_ROOT_FIT_AUDIT_R01_CARD_20260904.md`
- Launch SHA: `997f49c3cbefffee88d83d7b7de750a078d1a1ca`
- Execution node: configured `wsl_4070`
- Task: `ucope_root_target_fit_r01_997f49c3_02`
- Summary status: `complete=false`, `scientific_polarity=null`
- Applied branch: **`RECONSTRUCTION_OR_BINDING_FAILURE_NO_SCIENCE`**

## 1. Bounded outcome

The remote runner bound the exact retained input, completed the declared deterministic replay and
all 24 reconstruction predicates, but eight predicates exceeded the frozen maximum absolute
tolerance `1e-12`. The card maps any such failure to
`RECONSTRUCTION_OR_BINDING_FAILURE_NO_SCIENCE`. No target-versus-fit mechanism branch exists.

This attempt therefore cannot support `ROOT_TARGET_PIPELINE_SHIFT_SUPPORTED`,
`FINITE_ROOT_FIT_RESIDUAL_SUPPORTED`, `MIXED_ROOT_CAUSE`, baseline/headroom, treatment superiority,
or a root-safe successor. Its claim ceiling is **technical attempt evidence only**.

## 2. Launch identity and copied artifacts

The source-external attempt-02 launch wrapper was 752 bytes, SHA-256
`adc7cd34d8ff533f94f2a5d2db7fcf2f234b9d4da0407ca12202b97f2e569605`, and entered the detached
worktree before running one literal remote `admit-memory && runner` sequence. The worktree was clean
at the frozen SHA. The staged summary was 1,273,684 bytes with the frozen SHA-256
`1c8b1d217fc924271da62061f7226642a3d040995aba069cabb5df9ff336b676`.

The supervisor accepted task 02 exactly once, assigned PID `16400`, and recorded terminal
`failed`, exit `6`, after about 40 seconds. No resend, local fallback, second scientific process or
node change occurred. The remote result root was copied without alteration into the local direction
runtime tree.

| copied artifact | bytes | SHA-256 |
| --- | ---: | --- |
| `resource_admission.json` | 504 | `4bdab9062efb51ed8feefc10ab9960bd2b7acdc2bd9ec18a37bbc90f8d7fbb63` |
| `summary.json` | 8,366 | `d966848ec6e7ff1361bca1b2a99910879d65af95467098ded9bdb4666f657ccd` |
| operator `task.log` | 985 | `b34e6c5643cd1741e7e3846f14ebb49b4da7729c5d28b7952d8345ce8ab7d3a5` |
| operator `runner.sh` | 1,120 | `077aeb6479df1ed6c2dd99b300c9a5f5b62b91a6d32b03c8b6c2741eb4d833c4` |

## 3. Resource admission and runtime

The admission embedded in the summary is byte-for-byte equivalent to the copied receipt.

| field | observed |
| --- | ---: |
| physical available | `12,880,388,096` bytes |
| effective available | `12,880,388,096` bytes |
| required floor | `4,294,967,296` bytes |
| physical / effective / overall pass | `true / true / true` |
| runner wall | `39.29559288 s` |
| peak RSS | `571,215,872` bytes |

The projected and actual wall are below the frozen `185.481 s` cap. Resource admission did not
cause the failure.

## 4. Exact executed work

| quantity | observed |
| --- | ---: |
| replayed environment episodes / transitions | `983,040 / 4,915,200` |
| reconstructed root blocks | `6` |
| live target arrays / exact roots / exact policy evaluations | `12 / 12 / 12` |
| MSE-tail / MSE-root / live-distance checks | `6 / 6 / 12` |
| new seed, draw or independent-sample identities | `0 / 0 / 0` |
| learner rows / optimizer constructions / optimizer steps / parameter updates | `0 / 0 / 0 / 0` |
| fresh sampled evaluation episodes | `0` |

The counts meet the amended A/RECON reconstruction contract. They do not override a failed
reconstruction predicate.

## 5. Predicate inventory

CM independently reapplied `error <= 1e-12`, with no relative tolerance, to every recorded check.
Stored and recomputed pass flags agree in all 24 cases.

| predicate family | pass | fail |
| --- | ---: | ---: |
| `MSE_EXACT_TAIL` | 6 | 0 |
| `MSE_EXACT_ROOT` | 3 | 3 |
| `LIVE_ROOT_DISTANCE` | 7 | 5 |
| **total** | **16** | **8** |

The eight failures are:

| seed / fold | predicate | arm | absolute error |
| --- | --- | --- | ---: |
| 00 / 0 | `MSE_EXACT_ROOT` | reference | `1.0168532682541809e-12` |
| 00 / 0 | `LIVE_ROOT_DISTANCE` | dose-matched | `1.0919043447188415e-12` |
| 00 / 0 | `LIVE_ROOT_DISTANCE` | three-witness | `1.0579315201653117e-12` |
| 01 / 0 | `LIVE_ROOT_DISTANCE` | dose-matched | `1.1838308111578044e-12` |
| 01 / 0 | `LIVE_ROOT_DISTANCE` | three-witness | `1.1188827642172328e-12` |
| 01 / 1 | `MSE_EXACT_ROOT` | reference | `1.021627227260069e-12` |
| 01 / 1 | `LIVE_ROOT_DISTANCE` | dose-matched | `1.0790257576331896e-12` |
| 02 / 0 | `MSE_EXACT_ROOT` | reference | `1.010413974711355e-12` |

The smallest failure is `1.010413974711355e-12`; the largest is
`1.1838308111578044e-12`.

## 6. Frozen rule applied verbatim

The retained-input byte and digest binding passed. The next card condition requires all 24
numerical predicates to pass. Eight do not, so the first applicable branch is exactly:

```text
RECONSTRUCTION_OR_BINDING_FAILURE_NO_SCIENCE
```

The three mechanism branches are not evaluated from the unpublished policy payload, and the
summary correctly omits complete `policies`.

## 7. Direct observation and inference boundary

Direct observation: exact source, retained input, declared counts and remote execution produced
solver-derived reconstruction values that exceed the values retained from the earlier node by more
than the frozen tolerance in eight places.

Inference only: a NumPy/LAPACK/backend difference is the leading explanation. It is not identified
by these artifacts because they do not bind the LAPACK driver or compare byte-identical
`design64`/target arrays through both node solvers. FP32 target arithmetic, BLAS reduction order or
another dependency boundary remain live alternatives. No scientific mechanism polarity follows
from any of them.

## 8. Predictions and validity

The DM predicted `ROOT_TARGET_PIPELINE_SHIFT_SUPPORTED`; the owner prediction was
`not taken (unattended)`. Neither prediction is adjudicated because the reconstruction prerequisite
failed.

Attempt 02 is a complete record of an **invalid scientific attempt** and a valid technical failure
artifact. It is quarantined rather than salvaged, interpreted or rerun. The A/RECON question remains
unresolved.

## 9. Evidence paths

- Runtime root:
  `temp/directions/ucope/exp/root_target_vs_root_fit_audit_r01_20260904/`
- Copied task facts:
  `temp/directions/ucope/exp/root_target_vs_root_fit_audit_r01_20260904_operator_attempt02/`
- Remote worktree:
  `/home/wu/hmasd-worktrees/ucope_root_target_fit_r01_997f49c3_02`
- Remote task facts:
  `/home/wu/.agent-tasks/ucope_root_target_fit_r01_997f49c3_02/`
