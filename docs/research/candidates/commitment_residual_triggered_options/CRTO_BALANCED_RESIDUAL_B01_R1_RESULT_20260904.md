# CRTO balanced-residual B01-R1 result evidence

Date: `2026-09-04`

Object: `CRTO-B-EXPLORE-BALANCED-RESIDUAL-R01-R1`

Evidence class: `B/EXPLORE`

Status: `VALID_COMPLETE_B_EXPLORE`

Frozen first-matching branch: `BR-E — COMPARATOR_WEAK`

Claim ceiling: one learner initialization on the exact outcome-informed 48-row TRAIN and 16-row
EVAL population frozen in
`CRTO_BALANCED_RESIDUAL_B01_R1_SCIENCE_CARD_20260904.md`. This result is a learnability diagnostic;
it cannot support a competent-comparator residual effect.

## Invocation and artifacts

The accepted implementation was committed and pushed before launch at
`e0b55beebc567a90701ee9fb28c8aebdd7e3921e`. The final focused prelaunch suite passed `9` tests in
`7.19` seconds. The implementation added no item from engineering-scope specification §4; its
scope line is `scope: none`.

One result-bearing invocation was started as detached process `23380` after the fresh memory
admission. It terminated without a retry, resume, replacement row, alternate seed, or second
result invocation. The process exit code was not retained across the detached Windows process
handle. Direct terminal evidence is instead the terminated process, one complete final summary,
and a complete stdout JSON carrying the same object and launch SHA. The result root contains only
`summary.json`.

- summary:
  `temp/directions/commitment_residual_triggered_options/exp/balanced_residual_b01_r1_20260904/summary.json`
- summary bytes: `174002`
- summary SHA-256: `32549E0AA5C20DF7BD83F6E89DFB4073170BE45C266917E2100EB13550CB7843`
- admission:
  `temp/directions/commitment_residual_triggered_options/exp/balanced_residual_b01_r1_20260904_admission.json`
- stdout:
  `temp/directions/commitment_residual_triggered_options/exp/balanced_residual_b01_r1_20260904.stdout.log`
- stderr:
  `temp/directions/commitment_residual_triggered_options/exp/balanced_residual_b01_r1_20260904.stderr.log`

The exact runner arguments recorded by the summary select seed `0`, the admission above, and that
single output root. The summary reports `toy=false`, the exact launch SHA, and an empty
`validity_issues` list.

## Admission, resource, and cost observations

The receipt was assessed at `2026-09-04T11:37:53.511630Z`; the runner accepted it at an age of
`16.244214` seconds. Both physical and effective available memory were `9504276480` bytes and
passed the mandatory 4 GiB floor.

The prospective runner law gave `336.70048016922266` seconds per representation, below the
`900`-second per-path cap. Direct measured wall times were:

| quantity | seconds |
| --- | ---: |
| RAW training plus evaluation | 42.2828106 |
| TRUE_RESIDUAL training plus evaluation | 62.5834969 |
| CALIBRATED_DERANGEMENT training plus evaluation | 33.7267008 |
| complete invocation | 434.7066687 |

Every measured path and the complete invocation remained within the frozen `900`/`2700` second
caps. Peak RSS was unavailable, so the valid result is marked `resources_unmeasured` under the
owner telemetry rule. Stderr contains one pre-existing PyTorch warning about a read-only NumPy
view in predictor packet forecasting; it contains no exception and no learner measurement is
missing.

## Population, RNG, and work checks

The result directly reconstructed all `64` selected source rows from namespace `2026083192`,
source split coordinate `EVALUATION`, K8 slots `0..7`, and episode range `832..895`. It read no old
result JSON and did not read or instantiate confirmation namespace `2026083001`.

All `48` TRAIN and `16` EVAL rows reproduced their frozen event, onset, cost `4.0`, elapsed horizon
`4`, K8 regime, and inclusive side margin. There were no missing or replacement rows. The TRAIN
and EVAL derangements contained `48` and `16` donor assignments respectively, with zero fixed
points.

The predictor used `128` tapes from new namespace `2026090401`, produced `32256` examples, and
received exactly `100` updates and `12800` processed examples. Calibration used the disjoint
canonical `64` tapes, produced `16128` examples, and pooled K4 and K8. Direct work counts were:

```text
environment transitions                 54,848
common-future branch steps                3,520
gate updates per representation             256
processed examples per representation     8,192
evaluation rows per representation             32
```

All three gate trajectories began from the same recorded FP32 parameter scale:

```text
initial L2   = 18.87916908516977
initial RMS  = 0.10402732933491829
initial Linf = 0.28862619400024414
```

The actual exposure lines were finite and nonzero:

| path | checkpoint | updates | examples | nominal exposure | displacement L2 / initial L2 | displacement Linf / initial Linf |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| RAW | SHORT | 32 | 1024 | 0.032 | 0.0455486375 | 0.0937514004 |
| RAW | LONG | 256 | 8192 | 0.256 | 0.1359536930 | 0.9058249799 |
| TRUE_RESIDUAL | SHORT | 32 | 1024 | 0.032 | 0.0473793752 | 0.0943589251 |
| TRUE_RESIDUAL | LONG | 256 | 8192 | 0.256 | 0.1007137230 | 0.7404136303 |
| CALIBRATED_DERANGEMENT | SHORT | 32 | 1024 | 0.032 | 0.0512738258 | 0.0845651145 |
| CALIBRATED_DERANGEMENT | LONG | 256 | 8192 | 0.256 | 0.1080224632 | 0.8215297049 |

These are engineering and exposure observations, not evidence of mechanism value by themselves.

## Direct scientific observations

Every cell contains the prospectively required eight KEEP and eight REPLAN evaluation rows.

| path | budget | KEEP exact | KEEP mean regret | REPLAN exact | REPLAN mean regret | equal-side regret |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| RAW | SHORT | 1/8 | 0.0131637620 | 8/8 | 0 | 0.0065818810 |
| RAW | LONG | 8/8 | 0 | 4/8 | 0.0066464624 | 0.0033232312 |
| TRUE_RESIDUAL | SHORT | 5/8 | 0.0125263776 | 4/8 | 0.0175732694 | 0.0150498235 |
| TRUE_RESIDUAL | LONG | 6/8 | 0.0033848302 | 5/8 | 0.0150578212 | 0.0092213257 |
| CALIBRATED_DERANGEMENT | SHORT | 3/8 | 0.0161717034 | 7/8 | 0.0014148518 | 0.0087932776 |
| CALIBRATED_DERANGEMENT | LONG | 3/8 | 0.0126890059 | 5/8 | 0.0074856695 | 0.0100873377 |

The frozen equal-side contrasts were:

| budget | `d_RT = RAW - TRUE` | `d_DT = DERANGED - TRUE` | `d_RD = RAW - DERANGED` |
| --- | ---: | ---: | ---: |
| SHORT | -0.0084679425 | -0.0062565459 | -0.0022113966 |
| LONG | -0.0058980945 | 0.0008660120 | -0.0067641065 |

The relevant frozen rule is:

> `BR-E — COMPARATOR_WEAK`: RAW-LONG fails either material-side competence condition.

RAW-LONG passed the KEEP condition with `8/8` exact and zero mean regret. It failed the REPLAN
condition in both ways: `4/8` exact is below the required `6/8`, and mean regret
`0.0066464624` is above `0.005`. Every earlier branch requires a competent RAW-LONG comparator.
With no validity issue, the first matching branch is therefore exactly
`BR-E — COMPARATOR_WEAK`.

## Bounded reading

Directly, the same-information RAW path had lower equal-side regret than TRUE_RESIDUAL at both
observed budgets, and no aligned TRUE advantage appeared in this literal run. Scientifically, the
registered BR-E rule prevents turning those signs into a residual-mechanism result because the
RAW-LONG comparator did not meet its two-sided competence definition.

The valid conclusion is narrower: this one initialization and selected finite panel are a
learnability diagnostic with no competent-comparator residual claim. The observation contradicts
the DM's `BR-A` prediction for the literal object, but it does not distinguish residual geometry
from an unstable RAW checkpoint, cyclic-order phase, insufficient comparator budget or
architecture, predictor/calibration error, one-initialization variation, or the outcome-informed
population.

A B result has no consumption state. This result does not estimate natural K8 prevalence, reopen
the consumed support objects, read the untouched confirmation namespace, establish information
gain or function-class value, identify a stable effect, test policy return or variable populations,
or support warehouse, UAV, safety, deployment, or general MARL claims.

## Separate current-source reproduction flag

Before implementation, the DM and CM independently executed the fully described lower-domain tape
from the archived 2026-08-31 Pro response over current source. Both obtained boundary `t=60`, agent
`0`, previous `TRANSIT_L`, target energy about `0.25`, legal actions `{KEEP, RETURN}`, denominator
`257`, and `A=-0.0003712691571040594`. This does not reproduce the archive's previous `RETURN`,
three-action legal set, or `A≈-0.0307511126`. It is not part of B01 and supplied no result polarity;
it only demotes that archived construction from a locally reproduced support fact to unresolved
historical external provenance.

## Next discriminator

The cheapest next discriminator is a separate RAW-only A/RECON trace on the same exact population,
initialization, order, and batch size, with every checkpoint `252..264` declared before the run.
Because batch `32` over `48` TRAIN rows has a three-update order phase, this bracket directly tests
whether the observed SHORT-to-LONG side flip and update-256 competence failure are checkpoint-phase
facts. Its claim ceiling is comparator-path measurement only. A new three-path B object should not
be frozen until that trace distinguishes a transient phase from genuine RAW budget/model
incompetence.
