# FSD E4 census — actual-node cost projection

Recorded 2026-09-05 after the three calibrations and before any formal census invocation.
Card: `FSD_E4_CENSUS_SCIENCE_CARD_20260905.md`, frozen005643177. Class A/RECON technical
cost measurement within the same selected object; no final scientific reference return read.
CM record `FSD_E4_CENSUS_CM_TECHNICAL_RECORD_20260905.md` at f1a9f9aa4 contains exact commands,
source review and the reproduced test-directory failure followed by13 passing tests.

Exact source for every calibration and the prospective formal invocation:
`bc3eaeecf5f97e630a886028db0053ba2d08d56f`. Actual node wsl_4070, host hmasd-wsl-node,
Python `/home/wu/.venvs/hmasd/bin/python`, detached checkout
`/home/wu/hmasd-worktrees/fsd-e4-census-bc3eaeecf`. The same `bash -lc` shell/default thread
environment is retained; no OMP/MKL/OPENBLAS/NUMEXPR variable was set in that shell inspection,
and no settings were changed. No cross-host timing inference is made.

## Measured cost law applied before the sweep

Per-law projection remains exactly `P=2*(T_cold_law + 36*max(T_six_DP_samples))`.
The six samples cover switching, oracle fixed k1/k40, and open offset0 k1/k40/never-renew.
Each is an existing H400 DP at the frozen law and parameters. Cold law time triggers the lazy
mean, variance and hazard calculation; lognormal finite calibration is included. DP timing
is computation time of each call, and the cold-law timer starts after imports/CLI parsing.
Projection is an empirical heuristic with prospective factor2, not a bound on every path.

| Law | Cold law s | Largest DP sample s | Projected full law s | Frozen full-law cap s | Decision |
| --- | ---: | ---: | ---: | ---: | --- |
| deterministic | 0.00004823099880013615 | 0.021496598987141624 | 1.5478515890717972 | 300 | launch unchanged law |
| geometric | 0.000025706991436891258 | 0.011186856994754635 | 0.8055051176052075 | 300 | launch unchanged law |
| rounded-lognormal | 0.09033990699390415 | 0.03813238699513022 | 2.926211677637184 | 300 | launch unchanged law |

| Full-H DP sample | deterministic s | geometric s | rounded-lognormal s |
| --- | ---: | ---: | ---: |
| switching | 0.021496598987141624 | 0.011186856994754635 | 0.03813238699513022 |
| oracle k1 | 0.008622936002211645 | 0.011005887005012482 | 0.0355905089963926 |
| oracle k40 | 0.008700391001184471 | 0.010526275000302121 | 0.035097982006845996 |
| open offset0 k1 | 0.008711065995157696 | 0.010593373008305207 | 0.036248035001335666 |
| open offset0 k40 | 0.00867162000213284 | 0.010848990001250058 | 0.035739229002501816 |
| open offset0 never-renew | 0.008446173000265844 | 0.010553870000876486 | 0.03521465300582349 |

Every projection is below its own cap. The full-law structural work remains36 DPs and96
candidate values; three laws total108 DPs/288 candidates. No budget, source, law, grid, initial
phase or scientific branch changed in response to timing. Six DP arrays per law were computed
only for calibration; they are not a substitute for the complete reference census.

## Actual admission, completion and timing windows

Each row is a separate accepted detached task, with fresh adjacent memory admission and120s
timeout. All three exited0 and published status COMPLETE, non-toy H400 with zero learner counts.

| Law | Task | Receipt captured UTC | Physical = effective available bytes | Module wall before output s | External process wall s | Peak RSS KiB |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| deterministic | fsd_e4_cal_deterministic_bc3eaeecf_01 | 2026-09-05T16:35:02.778854Z | 15419650048 | 0.13272366298770066 | 0.15 | 35076 |
| geometric | fsd_e4_cal_geometric_bc3eaeecf_01 | 2026-09-05T16:35:37.933620Z | 15417974784 | 0.16190573100175243 | 0.18 | 35192 |
| rounded-lognormal | fsd_e4_cal_lognormal_bc3eaeecf_01 | 2026-09-05T16:36:07.298025Z | 15421640704 | 0.390393566005514 | 0.41 | 46996 |

All available-memory readings exceed4294967296 bytes, with physical/effective floor flags true.
The module timing starts before NumPy import and ends before publication, excluding interpreter
startup and output. External process wall includes interpreter startup and output and has only
0.01s display resolution. The runner prints output timing separately. Its JSON marks peak RSS
unmeasured internally; existing external process_time.txt does measure RSS, so do not rewrite
that raw JSON flag. None of these timings includes shell/SSH/agent scheduling latency.
Calibration process wall sum is0.74s at displayed resolution; it is consumed technical work,
whereas projected formal time is not consumed compute. Full scientific invocation wall remains
unmeasured at this boundary.

Raw summary copies: `e4_census_20260905/calibration_deterministic.json`,
`calibration_geometric.json`, `calibration_lognormal.json`. Full hazard tables and lognormal
finite moments are retained there. The private-moment calculation reports mean
19.999999999999996, variance687.3086223944757, support cap98296 and floating mass1.0/residual0.0;
the card's no-infinite-support-exactness limitation applies. These are calibration facts, not
final census return observations.

Original remote root for each law is
`<checkout>/temp/directions/flexible_skill_duration/exp/e4_census_20260905/calibration_<law>/`.
Each retains `summary.json`, `receipt.json`, `process_time.txt`; supervisor log is
`/home/wu/.agent-tasks/<task>/task.log`. CM copied these unchanged into the matching relative
root of `C:/Projects/HMASD-worktrees/cm-fsd-e4-census-20260905`. No artifact was moved/deleted.

## Decisions this technical intake produces

Object tier: (a) execute the unchanged three-law census under the measured below-cap projections;
(b) stop despite complete below-cap calibration; (c) alter grid/budget or start a learner.
Recommend/select (a), **Owner-delegated decision (unattended, 2026-09-05 instruction): (a)**,
OWNER_DELEGATED. The chosen per-law invocation cap stays300s, with a new actual-node receipt
immediately before each run. No reply is required; current owner review CLI reports no unapplied
instruction. This closes the missing cost fact, not the scientific question. Next discriminator
is still the complete reference census, and the slice ends at its intake without a successor.
