# ACVC_MATCHED_PACKAGE_COMPARISON_B01 — E0 result evidence

## Bound object, source and rule

B/EXPLORE, one fresh prospectively paired block MASTER 28731 / evaluation namespace 38731: exactly
one C fit and one M fit of the unchanged recipes, six sole-final 64-world panels on the common
final worlds, fixed by `em:acvc:convergence` (A with corrections, `PRO_FINAL`,
[card](ACVC_MATCHED_PACKAGE_COMPARISON_B01_PROSPECTIVE_CARD_20260915.md),
[intake](pro_packets/20260915_matched_package_card_convergence/INTAKE.md)) and funded by
`portfolio:cross_direction` (G3,
[decision](../../portfolio/decisions/2026-09-15-acvc-direction-investment-lifecycle.md)). Thin
entry `scripts/run_acvc_matched_package_comparison_b01.py` binding the identities and plans before
any recipe import on both routes (independent review accepted; ledger row 40); exact launch source
`841e5c35b1b9c0fe56f852f62f5235ae345b3227` (`codex/acvc`); pinned on-policy `de66d7a4b` re-staged
for the M arm ([DEPENDENCY.json](evidence/matched_package_comparison_b01_20260916/DEPENDENCY.json)).

Primary reading rule applied verbatim to the unrounded mean of `p_e = J_e(F(C)) − J_e(F(M))` over
the 64 declared worlds: `P > +.01` F_C_ABOVE_MEI; `−.01 ≤ P ≤ +.01` WITHIN_MEI; `P < −.01`
F_M_ABOVE_MEI; missing or invalid operand INCOMPLETE. J is the complete native team episode sum
divided by 256. Both fits and all six panels are complete. The unrounded primary is

**P = −.014962985109475921 J → F_M_ABOVE_MEI**

(conditional SE .010960 J over the 64 matched worlds; 24 worlds favour F(C), 40 favour F(M), 0
zero; extrema −.214268 and +.207615 J). No interval, significance or seed-SD gate replaces the
rule.

## Absolute scores and every declared contrast

| Panel (64 worlds) | Mean J | Mean episode sum S |
|---|---:|---:|
| C | .3022370425065718 | 77.37268288168238 |
| F(C) | .34777234159887255 | 89.02971944931137 |
| own-dwell(C) | .32340093491498223 | 82.79063933823545 |
| M | .35811853199940724 | 91.67834419184825 |
| F(M) | .36273532670834846 | 92.8602436373372 |
| own-dwell(M) | .36440145048790296 | 93.28677132490316 |

| Contrast (left − right) | Mean delta J | Sample SD J | Conditional SE J | Favorable / adverse / zero | Min J | Max J | Frozen reading |
|---|---:|---:|---:|---:|---:|---:|---|
| **P = F(C) − F(M)** (sole primary) | **−.014962985109475921** | .087680 | .010960 | 24 / 40 / 0 | −.214268 | +.207615 | **F_M_ABOVE_MEI** |
| C − M | −.05588148949283544 | .086174 | .010772 | 17 / 47 / 0 | −.252013 | +.154608 | DOWN |
| F(C) − C | +.045535299092300766 | .071110 | .008889 | 49 / 15 / 0 | −.191725 | +.184562 | UP |
| F(M) − M | +.00461679470894125 | .031291 | .003911 | 38 / 26 / 0 | −.150385 | +.086080 | WITHIN_MEI |
| F(C) − own-dwell(C) | +.024371407 | .081708 | .010214 | 45 / 19 / 0 | −.264991 | +.204292 | UP |
| F(M) − own-dwell(M) | −.001666124 | .034107 | .004263 | 31 / 33 / 0 | −.159947 | +.102006 | WITHIN_MEI |
| own-dwell(C) − own-dwell(M) | −.041000516 | .101481 | .012685 | 21 / 43 / 0 | −.272243 | +.163773 | DOWN |

"Favorable" counts worlds where the left operand is higher. The rowwise identity
`p_e = [F(C)−C]_e + [C−M]_e − [F(M)−M]_e` holds with maximum absolute residual 2.8e-17 J
(arithmetic on matched rows, not attribution). Every uncertainty is computed from its own paired
vector. [reduce/summary.json](evidence/matched_package_comparison_b01_20260916/reduce/summary.json)
(the thin entry's `--mode reduce` over the two collected summaries, with input provenance) and
[WORLD_DIFFERENCES.json](evidence/matched_package_comparison_b01_20260916/WORLD_DIFFERENCES.json)
retain every absolute score and every matched difference. These are conditional world summaries
for the two attained fitted policies on one block; six panels are not six training samples.

Intervention counters (existing meanings; `apply` is 0 by construction because the mask is the
choice; the unwrapped panels have no `Binding` on their path, so their zero counters are bypassed
instrumentation, not absent opportunities):

| Panel | Opportunities (share of 81,920 agent-ticks) | Retraces | Dwells | Distinguishable |
|---|---:|---:|---:|---:|
| F(C) | 6,395 (7.81 %) | 6,395 | 0 | 6,395 |
| own-dwell(C) | 4,629 (5.65 %) | 0 | 4,629 | 4,629 |
| F(M) | 4,569 (5.58 %) | 4,569 | 0 | 4,569 |
| own-dwell(M) | 3,602 (4.40 %) | 0 | 3,602 | 3,602 |

Each wrapped panel counts its own history; the counts are not a matched intervention dose.

## Display beside the concluded families (labelled context, no pooling)

| Object | Contrast | Value J | Reading | Identities |
|---|---|---:|---|---|
| **This block** | F(C) − F(M) | −.014963 | F_M_ABOVE_MEI | 28731 / 38731 |
| C/M block 1 | F(C) − M | +.023440 | F_ABOVE_MEI | 28331 / 38331 |
| C/M block 2 | F(C) − M | −.039190 | M_ABOVE_MEI | 28431 / 38431 |
| Transfer B01 | F(M) − M | +.018338 | TRANSFERS | 28531 / 38531 |
| Transfer B02 | F(M) − M | +.002859 | WITHIN_MEI | 28631 / 38631 |
| This block (support) | F(M) − M | +.004617 | WITHIN_MEI | 28731 / 38731 |
| This block (support) | F(C) − M (not a declared support; derivable as C−M + F(C)−C) | −.010346 | (context only) | 28731 / 38731 |

Distinct contrasts, identities, exposures and labels; nothing is appended to D1/D2 or T_F,1/T_F,2,
no worlds are pooled across objects, no training-population mean, best instance, or new
recurrence/transfer claim is reported.

## Actual exposure, implementation and measurement limits

Each fit: 4,096 H256 training episodes, 2,048 rollouts, 8,192 PPO minibatches, 1,048,576 native
training team ticks; C 8,192 joint Adam steps; M 8,192 actor + 8,192 critic Adam steps; each arm one
final snapshot loaded three times, 192 evaluation episodes (49,152 ticks). Totals: 2 fits,
**2,195,456 scored team ticks** (exactly the G3 inclusive ceiling), 24,576 optimizer steps, 2
snapshots, 6 panel loads, **9 environment constructors** (C 1 + 3, M 2 + 3, as corrected by the
node). Every episode row (4,288 per arm) has 256 steps, finite S and J, true termination, the bound
identities, training resets `100000·28731 + 1000 + e` and, in every panel, exactly the common
addresses `100000·38731 + 2000 + e`, e = 0..63. Update rows (C 8,192; M 2,048 as in block 2) are
finite; parameter displacements finite (C actor 6.438 / critic 15.169; M actor 9.165 / critic
9.108 / head 1.827). Training J rose from .089 to .235 (C) and from .112 to .348 (M) between the
first and last 256 training episodes. No retry, tuning, midpoint, pilot or extra panel occurred;
both originals were included regardless of the first result (the C original finished first and
was not read before the M original finished). Inherited placeholder fields remain unmeasured, not
zero behaviour (§11.8.7); the primary does not depend on them. Both summaries carry the common
object and their fitted-arm identity; `eligible_fits` C and M true.

Checks before launch: eight focused synthetic tests plus the B02, B01-transfer and block-2 binding
suites (27 passed on the node at the launch sha); independent `hmasd-reviewer` accept at
`dadba46f9` with three MINOR resolved at `841e5c35b`; protected bytes untouched.

## Complete native cost and preservation

| Original | Handle | PID | Native wall s | User + system CPU s | Peak RSS KiB | Exit |
|---|---|---:|---:|---:|---:|---|
| C (fit + C / F / dwell panels) | acvc-matched-c-b01-28731-841e5c35b | 3762157 | 1,161.65 | 1,157.22 + 2.21 | 552,644 | 0/0 |
| M (fit + M / F(M) / dwell(M) panels) | acvc-matched-m-b01-28731-841e5c35b | 3764685 | 1,065.69 | 1,064.17 + 0.92 | 596,148 | 0/0 |

Summed native wall 2,227.34 s against the 3,800 s summed plan (C 0.45 of its 2,600 s plan, M 0.89
of its 1,200 s plan). The two originals overlapped on the otherwise idle node (C launched 03:13:34Z,
M 03:16:25Z, both single-thread), with process walls to the summary 1,135.50 s (C: training
1,096.75 s, about 1.05 ms per training tick; panels 11.7 / 13.5 / 13.5 s) and 1,042.07 s (M:
training 1,004.03 s, about 0.96 ms per tick; panels 11.5 / 13.2 / 13.3 s). These are two whole
invocations that happened to overlap; no concurrent-pair speedup or slowdown is claimed. Both
admissions passed 4 GiB (C 15,610,613,760 B; M 15,299,493,888 B available). Support, provider and
lifetime costs remain UNKNOWN.

Both nine-file sets were collected with per-file sha256 equal to the remote listings
([COLLECTION.json](evidence/matched_package_comparison_b01_20260916/COLLECTION.json)); the seven
non-checkpoint, non-log files per arm are committed under
[evidence/…/native/{C,M}/](evidence/matched_package_comparison_b01_20260916/native/); `final.pt`
and the logs are excluded from Git by `.gitignore` and retained with the full sets in
`C:/Projects/HMASD-worktrees/codex-acvc/temp/directions/acvc/retained/matched_package_comparison_b01_20260916/{C,M}_original.tar.gz`
([PRESERVATION.json](evidence/matched_package_comparison_b01_20260916/PRESERVATION.json)). Launch
and terminal facts: [EXECUTION.md](evidence/matched_package_comparison_b01_20260916/EXECUTION.md);
remote reclamation: [CLEANUP.json](evidence/matched_package_comparison_b01_20260916/CLEANUP.json).

## Bounded reading and predictions

On this matched block the conventional-proposer package F(M) attains an MEI-sized advantage over
the coordinator-side package F(C): P = −.0150 J with 40/64 worlds adverse to F(C) and conditional
SE .011 J. Under the fixed mapping this favours further development of F(M) relative to F(C) on
this observed block. Arithmetic context, not attribution: C alone trails M by .056 J; the fixed
transformation adds +.046 J to C (UP, 49/64) but only +.005 J to M (within the band, 38/64); the
package gap is smaller than the proposer gap because F helps C much more than M. The M-side
wrapper adds nothing MEI-sized on this block: F(M) − M and F(M) − own-dwell(M) are both inside the
band (dwell(M) is .0017 J above F(M)), so unwrapped M or dwell(M) is a reportable competing
development option without substituting its contrast for P. These measurements do not identify a
unique source of the advantage; within-band does not mean zero. Evidence for the attained
finite-learning packages on one block, not stable superiority, a training-population mean, a
discardable C or M, tuned headroom, equivalence, a K/N/retrace/memory mechanism, C promotion, a
default or safety change, or a transfer/recurrence claim. The concluded C/M two-block claim and
both transfer readings keep their labels; this is a third M-side F(M) − M observation (+.005 J,
within band) displayed per instance beside +.018 and +.003 J.

Predictions ([PREDICTIONS.json](evidence/matched_package_comparison_b01_20260916/PREDICTIONS.json),
recorded before launch, rationale qualified by the node): P forecast F_C_ABOVE .20 / WITHIN .15 /
F_M_ABOVE .65 → realized F_M_ABOVE_MEI, multiclass Brier .185, modal forecast occurred; supports
C−M (.15/.15/.70 → DOWN, Brier .135), F(C)−C (.80/.15/.05 → UP, .065), F(M)−M (.40/.45/.15 →
WITHIN_MEI, .485); completeness forecast .90 → complete. Owner prediction not taken (unattended);
the canonical review inbox was empty at intake. No calibration claim.
