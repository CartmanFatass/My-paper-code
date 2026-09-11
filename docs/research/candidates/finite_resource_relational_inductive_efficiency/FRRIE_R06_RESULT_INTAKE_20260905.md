# FRRIE R06 result intake — 2026-09-05

Status: `VALID_B_EXPLORE / R06_SMALL_OR_ROSTER_MIXED / N15_ONLY_ABOVE_MEI`.

## What DM checked

DM read the frozen R06 card and its prospective module-layout overlay, CM E0 Markdown,
unchanged 122,511-byte publisher JSON and terminal record at pushed
`bb65fa3322b70b9469c0732bd6c6558eb50dc1d6`. DM inspected the 22 completion flags, rule
inputs including actual initial/final LR, full checkpoint gaps, native final cells, counts,
contact/displacement, source/node/admission and original termination. Read-only subtraction
against the preserved R05 JSON supplies the dose comparison below; no new execution occurred.

CM directly observed original SystemExit(0) and complete publication, separately from
supervisor/pdb exit 0. Fixed debugger queries then stopped at module line 1 before the first
statement; q ended the session without another computation. Missing-local queries there are
expected, not learner failures. No original exception or deadline exit occurred.

## Original rule applied verbatim, in order

| branch | rule and bounded reading |
| --- | --- |
| `R06_INVALID_INCOMPLETE` | A common-integrity item fails; node admission is absent or below 4 GiB; real learner transition/update/evaluation counts or exposure are zero/missing; information/work differs; actual LR is not 0.003 for both arms throughout the unchanged no-schedule run; raw initialization is not paired; the initial tight clip does not change exactly five coordinates; optimizer moments change during projection; or required learner-side curves/counts are absent. Quarantine; no result. |
| `R06_EDGE_BELOW_UNIFORM` | The result is valid and contact-active, but e128 < 0 at either seen roster. Report direct curves and gaps; the containing comparator is not competent on that cell and the arm gap is nonidentifying. |
| `R06_FAVORABLE_BOTH` | EDGE is at least uniform on both rosters and d128 >= +0.005 at both. Preliminary one-root favorable high-LR activated-projection signal only. |
| `R06_ADVERSE_OR_MIXED` | EDGE is at least uniform on both rosters and d128 <= -0.005 at either. Bounded adverse or roster-mixed evidence for this configuration only. |
| `R06_SMALL_OR_ROSTER_MIXED` | The complete valid contact-active result reaches none of the earlier branches. Report literal signs/magnitudes; no stable effect claim. |

The invalid row is false: all common requirements, complete counts/curves and actual paired
initial/final LR [0.003] hold. Both final e values are positive. N15 exceeds +0.005 but N9
does not, so favorable-both is false; neither d is adverse. The first matching branch is
**R06_SMALL_OR_ROSTER_MIXED**. This branch does not mean both gaps are below MEI.

| update | N=9 d | N=15 d | N=9 e | N=15 e |
| --- | --- | --- | --- | --- |
| 0 | +0.000000856631 | +0.000001040776 | -0.001214709249 | +0.001417723880 |
| 32 | 0 | -0.000009918073 | +0.001460304135 | -0.001164935529 |
| 64 | +0.000481620928 | -0.000476577956 | +0.004145744381 | +0.003854064038 |
| 128 | +0.001066907914 | +0.005548293532 | +0.007199240468 | +0.014761398958 |

Exact final d: N9 `0.0010669079143553993`, N15 `0.0055482935315618875`.
Exact final e: N9 `0.0071992404681319976`, N15 `0.014761398957731823`.
All 18 native cells and 256 learner/projection rows remain in the original E0 JSON.

## Native consequence and exposure

At N15, PHY/EDGE final J is 0.046322306897491214 / 0.040774013365929326.
They make 92 / 80 successful deliveries across 256 evaluation episodes: west 47 / 46, east
45 / 34. Mean minimum basin deliveries is 0.02734375 / 0.01953125. PHY has a higher waste
fraction (0.9488863060250878 versus 0.9470775746740401), not a lower one. In the registered
return formula, the d15 contributions are +0.005078125 from deliveries, +0.000651041667
from balance and -0.000180873135 from waste. More radio actions and collisions accompany
the observed gain; these observations do not identify a particular beta coordinate's cause.

At N9, PHY/EDGE J is 0.02694512805901468 / 0.02587822014465928, with 50 / 48 successful
deliveries. The d9 components are +0.000846354167 delivery, +0.000325520833 balance and
-0.000104967086 waste. Thus native consequences exist at both rosters, while only N15
passes the predeclared effect threshold.

The original raw paired root/model and initial five clips [2,4,11,12,16] remain. PHY
contacts in 125/128 later updates, with 437 coordinate events over 14 distinct coordinates;
EDGE has no contact. Cumulative tight displacement is 0.30848179012537, maximum overshoot
0.008026394993066788 including initialization; every projection preserves optimizer moments.

Final Linf displacement from raw initialization is PHY 0.21827195584774017 and EDGE
0.2057093381881714, respectively 4.36544 and 4.11419 times the 0.05 initial half-range.
Nominal exposure is the declared 128 × 0.003 = 0.384, normalized 7.68. Both actual per-arm
initial/final group LRs are 0.003 under the unchanged no-schedule optimizer.

R05's same-root low-LR anchor had 50 contact updates and Linf displacement only about 0.52
and 0.53 initial half-ranges. The higher dose therefore exercised substantially more actual
movement/contact. At update 128, R06 minus R05 changes d by +0.0005998573421190229 at N9
and +0.006416083763663958 at N15; e increases by +0.00669221580804636 and
+0.014276635514882709. Checkpoint-0 gaps and shared uniform means are identical. This is an
outcome-informed same-root dose description, not independent replication or a pooled estimator.

## Counts, receipts and cost

| quantity | retained observation |
| --- | --- |
| source / task | `72b1bd001f7aff4d383f7cbec296bed2edf675dd` / `frrie_b01_contact_r06_72b1bd00` |
| node | `wsl_4070`, CPython 3.10, CPU FP32, Torch thread 1, native width 32 |
| start / end | 2026-09-05T09:19:47Z / 09:34:42Z |
| fresh admission | 09:19:47.084784Z, physical/effective each 12,939,055,104 bytes |
| per-arm updates / Adam / backward | 128 / 128 / 128 |
| per-arm factual episodes / transitions / training slots | 8,192 / 98,304 / 630,784 |
| per-arm learned evaluation episodes / slots | 2,048 / 24,576 |
| all evaluation | 18 cells, 4,608 episodes, 55,296 transitions |
| total native slots | 1,316,864 |
| completion | all 22 flags true; 256 sequential learner rows and eight checkpoint-state summaries |
| supervisor / runner wall | 895 / 843.355730929994 seconds |
| attributed PHY / EDGE wall | 148.04153741498885 / 147.02805976910167 seconds; shared work is additional |
| peak RSS | 614,965,248 bytes; `resources_unmeasured` for scratch high-water only |

All cells contain action/event inventories, 256 episodes and 3,072 transitions. Evaluation
preserves model bytes and uses common tapes nine times per roster. Both four-hour per-arm and
eight-hour total caps hold. The accepted source remains unchanged; only the fresh native build
directory is untracked remotely. Final source scope is 23/79 = 29.11%; no new source, test,
publication wrapper or guard was added during collection. Earlier rejected candidates remain
historical breaches, not properties of the accepted revision.

R05 plus R06 form an observed two-valid-B remote window: 1,742.007364 runner seconds total,
871.003682 per valid result; 1,832 supervisor seconds total, 916 per result. This is not a
lifetime total and is not pooled with A01, engineering checks, earlier failures or the Windows
window. Actual full publication succeeded; formal-sized publication-test coverage remains open.
Host headroom remains absent: uniform is a minimum reference, not a tuned generic baseline or
feasible upper-policy record. Original logs/receipt/summary remain at paths in the CM record.

## Bounded reading and prediction score

Strongest support is actual increased learner exposure plus a positive native d15 above MEI
against a containing same-information comparator that is well above its minimum uniform
reference on this root. Strongest contradiction to an across-roster material advantage is
the N9 sub-MEI gap; the N15 threshold margin is only about 0.000548 on one literal root and
one prospectively selected endpoint. Earlier checkpoints do not show a stable positive gap.

Low movement and nonactivation no longer explain this particular high-dose run. Generic
shrinkage/projected-Adam geometry, common K0 alignment, roster dependence, episode-path
variation and root-specific co-adaptation survive. This does not identify relation-specificity,
held-out transfer, arbitrary N, membership change or a seed-population effect. Claim ceiling
remains B/EXPLORE, one literal root, actual Linux CPU surface, INTACT, seen N={9,15}.

Prediction score is **mixed, not an unqualified match**. The recorded branch
`R06_SMALL_OR_ROSTER_MIXED` and its EDGE-at-least-uniform condition matched. But the same
prediction explicitly said **“A material gap or wide-below-uniform directly contradicts this
prediction”**. N15's above-MEI gap triggers that material-gap falsifier, so that substantive
component is contradicted. Higher expected movement/contact was observed. Owner prediction
is `not taken (unattended)`; current DM/integration reviews and audit owner columns contain
no overriding instruction or prediction reply.

## Decisions this intake produces

### Valid result and honest reading

Options: (a) accept the original mixed-roster branch, explicitly preserve N15 above-MEI and
score the prediction's contradictory component; (b) report both gaps as small and a wholly
matched prediction; (c) promote this one-root signal to stable superiority or C evidence.

Recommendation and selection: **(a)**, object tier, kind `technical`, owner flag `none`.
Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**, `OWNER_DELEGATED`.
No B consumption state exists and no failure is reclassified from this success.

### Next object inside the accepted family

Options: (a) a second prespecified literal-root B check of the N15 signal at unchanged high
LR/work/boxes, with full N9 reporting; (b) tune LR or shrinkage further on the observed root;
(c) add relation intervention before checking root sensitivity; (d) pool R05/R06 as independent
seeds or reopen the old stopped B01 panel.

Recommendation and selection: **(a)**. Root sensitivity is the immediate live explanation for
a barely above-MEI N15 gap; another dose change would leave it unresolved. N15 is transparently
selected as the new object's primary question after R06, while N9 remains fully reported.
Neither the R06 endpoint/rule nor old B01's three-root stop is rewritten. Old slots 004/005
remain unopened. The new card uses author-fixed literal seed 2 with no root/outcome filtering
and makes no claim that two fixed roots identify a random-root population.

Object tier, kind `selection`, owner flag `none`.
Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**, `OWNER_DELEGATED`.
The new `FRRIE_R07_SECOND_ROOT_SCIENCE_CARD_20260905.md` prospectively handles zero initial
contact, later contact or no contact without resampling. It changes no family, lifecycle,
priority or recast count. CM may implement only after the new card's complete contract is frozen.

## Owner surfaces and append-ready audit

A Chinese brief and CLI-created validity, brief, selection and new-card items accompany this
intake. Root appends the rows below under `frrie-r06-intake-r07-selection` in the 2026-09-05
ledger. Existing ladder prediction provenance remains; no new owner reply is imputed.

| time | direction | tier | kind | options | chosen option | reversible | provenance | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-05T03:11:09-07:00 | finite_resource_relational_inductive_efficiency | object | technical | (a) accept original branch and mixed prediction score; (b) call both gaps small and prediction wholly matched; (c) stable/C promotion | (a) VALID B/EXPLORE R06_SMALL_OR_ROSTER_MIXED, only N15 above MEI, substantive prediction component contradicted | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-05/20260905-frrie-005.json` | none | |
| 2026-09-05T03:11:09-07:00 | finite_resource_relational_inductive_efficiency | object | technical | reading-agreed; reading-disputed | publish R06 Chinese brief; no owner reading imputed | yes | VALID_RESULT_INTAKE | `docs/research/portfolio/owner/inbox/2026-09-05/20260905-frrie-006.json` | none | |
| 2026-09-05T03:11:10-07:00 | finite_resource_relational_inductive_efficiency | object | selection | (a) second literal root, unchanged dose/work, N15 primary and full N9; (b) tune observed-root dose; (c) relation intervention before root check; (d) pool nonindependent R05/R06 or reopen stopped panel | (a) new R07 seed-2 literal-root B object, no filtering or historical rule rewrite | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-05/20260905-frrie-007.json` | none | |
| 2026-09-05T03:11:11-07:00 | finite_resource_relational_inductive_efficiency | object | technical | accept; reject; revise | freeze R07 card; accept recommended, no owner choice imputed | yes | CARD_RECORDED | `docs/research/portfolio/owner/inbox/2026-09-05/20260905-frrie-008.json` | none | |
