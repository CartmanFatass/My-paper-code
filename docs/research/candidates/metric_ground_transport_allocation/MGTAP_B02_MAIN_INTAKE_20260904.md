# MGTAP B02 main panel — DM intake and safe round boundary

Date: 2026-09-04. Direction: `metric_ground_transport_allocation`; route N5.
DM: `/root/dm_amx_n5_allocation`. Class: **B/EXPLORE**.
Result: **`B02_INSIDE_MEI`**, a positive observed curve difference below this
object's declared effect of interest. This is not practical equivalence.

Card: `MGTAP_B02_CURVES_SCIENCE_CARD_20260904.md` at `22ae3de13`.
Main release and measured projection: `MGTAP_B02_PILOT_INTAKE_20260904.md` at
`9145a4c3a`. Source launch SHA: `f3595bfe3e90024f3b31eb8a82910304b90543d3`.
CM result: `MGTAP_B02_MAIN_RESULT_EVIDENCE_20260904.md`; exact aggregate:
`MGTAP_B02_MAIN_SUMMARY_20260904.json`, accepted at CM commit `c8d6cb618`.

## What I checked

I checked the CM's technical acceptance against the card, all three collected
main summaries and admissions, the 17-point aggregate and paired seed results,
the raw-array/count recomputation reported by CM, and the numerical branch rule.
The declared CPU float64/one-thread configuration, 60 parameters, zero start,
same-information METRIC/INTACT and equal-class FREE/INTACT, SGD 0.1 without
momentum or weight decay, fixed seed set and evaluation grid all match. The
new source used B02-specific RNG phases and never called the old C runner or
stationarity selection. No source, arm, budget or threshold changed after pilot.

All six fits have 256 updates and 17 evaluation points, with 16 tapes per
pair/load episode/N. Each fit has 24,576 training allocation transitions,
147,456 training agent steps, 13,056 evaluation episodes, 26,112 evaluation
decisions and 156,672 evaluation agent steps. Full main totals are:

| Quantity | Actual, matching card |
| --- | ---: |
| Paired training seeds / arm fits | 3 / 6 |
| Optimizer updates | 1,536 |
| Training allocation transitions | 147,456 |
| Training autoregressive agent steps | 884,736 |
| Evaluation two-epoch episodes | 78,336 |
| Evaluation allocation decisions | 156,672 |
| Evaluation autoregressive agent steps | 940,032 |

CM recomputed all N/load curve means from finite retained episode arrays within
absolute 1e-15, checked all learner trace lengths and finite parameter/gradient
measurements, and verified equal initial episode outputs and read-only oracle
reuse. Tests and this conformance check establish implementation fidelity; the
following observed native returns establish the B result. The pilot seed is
excluded from all main statistics, and tapes are not extra training replicates.

## Rule applied verbatim and observed result

The card defines `d_s=A_METRIC,s-A_FREE,s`, where each A is normalized trapezoid
AUC over the complete update grid 0,16,...,256, and `D=mean_s(d_s)`. Its rule is:

1. `B02_METRIC_CURVE_SIGNAL` iff `D >= 0.01` and at least two d_s are positive.
2. `B02_FREE_CURVE_SIGNAL` iff `D <= -0.01` and at least two d_s are negative.
3. `B02_INSIDE_MEI` iff `abs(D) < 0.01`.
4. `B02_MIXED_SEEDS` otherwise.

| Seed | METRIC AUC | FREE AUC | Paired difference |
| --- | ---: | ---: | ---: |
| 203 | 0.409158579508464 | 0.401116858588325 | +0.008041720920139 |
| 211 | 0.406846957736545 | 0.399160342746311 | +0.007686614990234 |
| 223 | 0.408928510877821 | 0.399466790093316 | +0.009461720784505 |

`D=+0.008396685564959483`; sample SD 0.000939281677409837; range
[0.007686614990234375, 0.009461720784505134]. All three differences are positive.
Branch 1 fails because D is below 0.01; branch 2 fails; branch 3 is true.
The positive sign does not replace the AUC threshold with a sign-count rule.
The three-seed observation does not establish statistical equivalence or an
upper confidence bound below the MEI.

Mean paired differences at updates 16, 64 and 256 were respectively
0.002807617187500, 0.008355938946759 and 0.007262731481481. Mean return at 256
was 0.491427951388889 (METRIC) and 0.484165219907407 (FREE). The full curves
and N/load breakdowns are retained; the visualization is
[`MGTAP_B02_CURVES_20260904.png`](MGTAP_B02_CURVES_20260904.png), drawn read-only
from those three main summaries. Its band is the observed seed range, not a
confidence interval; its horizontal MEI reference applies to AUC.

The same-population oracle is 0.66875. Its endpoint gaps are 0.177322048611111
(METRIC) and 0.184584780092593 (FREE). These are valid untuned finite-budget
diagnostics at trained N=4/8, not the missing tuned headroom record at N=6/12.
Mean curve motion from 224 to 256 is +0.009705041956019 and +0.012535264756944;
that is a descriptive learning observation, never the retired C stationarity gate.

## Runtime, cost and engineering boundary

Node `wsl_4070`, SSH `hmasd-wsl-node`; exact detached cwd
`/home/wu/hmasd-worktrees/mgtap_b02_20260904`. The one accepted main task was
`mgtap_b02_main_203_211_223_f3595bfe`, PID 103077, terminal `finished`, exit 0
at `2026-09-04T22:47:40Z`.
Its supervisor directory is
`/home/wu/.agent-tasks/mgtap_b02_main_203_211_223_f3595bfe/`, containing
`task.log` and `exit_code`. The task executes only the three fixed commands in
sequence; each has its own adjacent `admit-memory && runner` invocation.
Outputs are cwd plus
`temp/directions/metric_ground_transport_allocation/exp/mgtap_b02_main_<seed>`.
The same roots are collected in `C:/Projects/HMASD-worktrees/cm-n5-b02-20260904`;
the read-only aggregate is `mgtap_b02_main_aggregate/summary.json` there.

| Seed | Physical/effective available bytes at admission | Runner wall seconds |
| --- | ---: | ---: |
| 203 | 15,429,967,872 / 15,429,967,872 | 2.9970070070 |
| 211 | 15,435,071,488 / 15,435,071,488 | 2.5733781990 |
| 223 | 15,433,801,728 / 15,433,801,728 | 2.6023936020 |

Admissions were at `22:47:29.631981Z`, `22:47:33.676492Z` and
`22:47:37.250912Z`, respectively; each receipt is `admission.json` in its
named seed root. All admissions pass 4 GiB. The main runner wall is **8.1727788080 seconds**;
including the named pilot it is **8.9395385960 seconds**. Supervisor wall is
**11 seconds main / 13 seconds including pilot**, a different measurement.
The roughly 19 seconds between launch acceptance and CM's first terminal
observation is not substituted for supervisor runtime. Shared setup over pilot
and all main invocations totals 0.0954760750 seconds, below 60. Maximum main
peak RSS is 482,988,032 bytes. Every arm/seed stayed below 100 seconds; both
three-seed arm totals and the entire object stayed below their declared caps.

Cost denominator: one completed three-seed main comparison. Report 8.1727788080
seconds per that valid comparison, or 8.9395385960 seconds including its accepted
development pilot; do not count the pilot as an extra main replicate. This is
the complete B02 window on this node/device, not the direction's lifetime cost.
Fixed METRIC-first order and lazy optimizer startup prevent a causal compute-
efficiency reading of the per-arm wall difference.

The tracker received both accepted handles directly; each terminal event was
acknowledged and CM collected the evidence. There is no running task, duplicate
invocation, retry, quarantine, source repair or missing learner measurement in
B02. Resources are measured. Scope section 4 additions: none. The reviewed
375 research lines, 167 runner lines and approximately 28% orchestration fit
the engineering budgets; no section-5 breach. The actual main run exercised the
full grid, oracle-input CLI and final aggregation/publication path. No open
post-learner publication-coverage issue remains for this object.

## Prediction check and observation that bounds the result

The DM prediction `B02_INSIDE_MEI` was borne out. The owner prediction is
**not taken (unattended)**. The final review read on both the DM and Root
integration owner surfaces returned no pending instruction or prediction reply.
This agreement does not upgrade the evidence class.

Strongest support: all three paired seeds favor METRIC across AUC, both arms
learn substantially, and the difference appears in native reward under equal
information, action class and update exposure. Strongest contradiction to a
material-advantage claim: the observed aggregate stays below the declared MEI,
with only three seeds and one fixed optimizer configuration. The full curves
remain changing; there is no tuned containing-control result.

The surviving explanation is generic coordinate conditioning/effective step
size and implicit finite-SGD regularization. Zero explicit weight decay removes
one deliberate regularizer but does not isolate ground metric causality. This
toy is centralized, balanced and trained at both measured N; it contains no
churn, hidden-role inference, partner adaptation, duration decision or UAV host.
The coupled allocation/team-credit trace is real, but its necessity is untested.
No retrospective reinterpretation of the two old C nonidentifications occurs.

## Decisions this intake produces

### 1. Accept the full-panel B reading — object tier

Options: (a) accept `B02_INSIDE_MEI` with the positive observed seed differences
and explicit conditioning alternative; (b) call a positive sign a material
METRIC win; (c) claim equivalence or metric-family failure. Recommendation:
**(a)**. Only (a) applies the card's rule without discarding contrary detail or
claiming more than three exploratory seeds can establish.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
Provenance `OWNER_DELEGATED`; reversible; kind `technical`; owner flag `none`.
This is a valid B observation, with no C consumption state and no direction-tier
or Portfolio disposition.

### 2. End this round at the completed intake — owner-direct boundary

Options: (a) retain the complete B02 evidence and stop after clean commit/push;
(b) immediately choose another budget/arm or start another round. Recommendation
and executed option: **(a)**, applying the owner's safe drain relayed by Root.
Provenance `OWNER_DIRECT`; reversible. No next object/card is selected, no Pro
round is opened, and no priority or lifecycle changes.

The next scientific discriminator, if the owner later resumes research, is a
same-information step-size/conditioning control within the existing finite-budget
learning question. It is a candidate for later object-tier selection, not a new
frozen card or current launch. Recovery starts by reading this intake and the
current owner instructions, not by rerunning B02 or reviving either old C.

Recovery Git state: DM worktree `C:/Projects/HMASD-worktrees/dm-n5-allocation-20260904`,
branch `codex/dm-n5-allocation-20260904`; CM worktree
`C:/Projects/HMASD-worktrees/cm-n5-b02-20260904`, branch
`codex/cm-n5-b02-20260904`. CM commits are `f3595bfe3 -> cb86c6419 -> c8d6cb618`
after the card base `22ae3de13`; DM commits separately hold the card, pilot intake
and this final intake/figure/owner record. Both branches are pushed for Root's
explicit integration. Source remains pinned to f3595bfe3 for historical replay;
there is no remaining B02 process or queued launch to resume.
