# MGTAP B03 — scalar-rate control DM intake

Date: 2026-09-04 (owner timezone). DM `/root/dm_amx_n5_continue`.
Class **B/EXPLORE**. Valid result **B03_SELECTED_INSIDE_MEI**.
The grid-selected residual is +0.0006554780183014955, inside absolute MEI 0.01.
This supports scalar-rate absorption as a live explanation for B02's fixed-rate
separation; it is not equivalence or a direction-wide negative.

## What I checked

I read the complete CM E0 result and technical evidence against the B03 card,
the committed aggregate and three collected raw seed summaries, all admission
receipts, and the retained learner trace paths. I independently recomputed AUCs,
global actor-rate selection, all three selected contrasts, H and the ordered
branch from the raw seed curves. They exactly match CM's published values.
I also checked that all three runtime configurations match, inspected the
recorded source/RNG/numerical contract and the native population, and read CM's
raw-array/count/displacement conformance evidence. The largest observed complete
parameter path across the 24 fits is 36.43800279995542; the carded finite SGD
path budgets and real nonzero learner motion are separately recorded.

Card and selection were pushed at `da765da0a`; launch source is
`19531d07023637a0940fd9c6cfa51005d13fe0a7`, unchanged through execution.
CM result commit is `32c1e3323b05cde6d69f6971beecc35e2bf2387c`.
References: `MGTAP_B03_STEPSIZE_SCIENCE_CARD_20260904.md`,
`MGTAP_B03_SELECTION_INTAKE_20260904.md`,
`MGTAP_B03_TECHNICAL_EVIDENCE_20260904.md`,
`MGTAP_B03_MAIN_RESULT_EVIDENCE_20260904.md`, and
`MGTAP_B03_MAIN_SUMMARY_20260904.json`.

Both actors have 60 zero-initialized float64 CPU parameters and one thread,
unchanged information/action class, decoder, REINFORCE loss, entropy, gradient
clipping, sampler and no momentum/weight decay. Only the four named scalar rates
vary. Seeds 307/311/313 are fresh relative to B02. Training/evaluation address
laws are unchanged at those new seeds, paired across actors/rates; evaluation
is disjoint from training. No old C runner, stationarity gate or evidence is reused
as an efficacy observation. The old numerical and B02 source files are unchanged.

All 24 fits contain 256 finite learner rows and all 17 parameter/evaluation
arrays. CM reports exact recomputation of all mean/N/load curves from retained
episode returns, finite parameters/gradients/displacements, equal zero initial
arrays, and agreement of checkpoint norms with distance traces and summed path.
These are engineering conformance observations, distinct from native-return value.

| Quantity | Actual, matching card |
| --- | ---: |
| Training seeds / actor-rate fits | 3 / 24 |
| Optimizer updates | 6,144 |
| Training allocation transitions | 589,824 |
| Training autoregressive agent steps | 3,538,944 |
| Evaluation two-epoch episodes | 313,344 |
| Evaluation allocation decisions | 626,688 |
| Evaluation autoregressive agent steps | 3,760,128 |

Each actor has exactly four configurations times three seeds of selection
exposure. Selection and reading share the same B panel. The three seeds are the
training replicates; evaluation tapes, rates and checkpoints are not extra seeds.

## Rule applied verbatim and direct result

The card chooses one rate for each actor by mean normalized trapezoid AUC over
0,16,...,256, with exact ties going to the smaller rate. The selected paired
contrasts are d_s and their mean is D. Its ordered rule is:

1. `B03_METRIC_RESIDUAL_SIGNAL` iff `D >= 0.01` and at least two d_s are positive.
2. `B03_FREE_SELECTED_SIGNAL` iff `D <= -0.01` and at least two d_s are negative.
3. `B03_SELECTED_INSIDE_MEI` iff `abs(D) < 0.01`.
4. `B03_MIXED_SEEDS` otherwise.

| Rate | METRIC mean AUC | FREE mean AUC | Paired mean difference |
| --- | ---: | ---: | ---: |
| 0.1 | 0.406183906837746 | 0.397773770932798 | +0.008410135904948 |
| 0.3 | 0.493172765661169 | 0.488168645788122 | +0.005004119873047 |
| 1.0 | 0.562689576325593 | 0.561284100567853 | +0.001405475757740 |
| 3.0 | 0.599301882143374 | 0.598646404125072 | +0.000655478018302 |

Both actor-global selections are **3.0**, the upper grid edge. For seeds
307/311/313, selected d_s are +0.0009539286295572325,
-0.000671047634548616 and +0.0016835530598958703. D is
**+0.0006554780183014955**, sample SD 0.0012053384101939199.
Rule 1 fails because D<0.01; rule 2 fails; rule 3 is true. Mixed seed signs do
not override the earlier inside-MEI branch. This is no upper confidence bound
below MEI and no equivalence statement.

Selection gains relative to 0.1 are +0.19311797530562788 for METRIC and
+0.20087263319227425 for FREE. The scalar-rate bridge
`H=FREE_selected-METRIC_0.1` is **+0.19246249728732637**; its three values
are +0.19408111572265624, +0.19906217787000874 and +0.18424419826931415.
Selected N-specific mean contrasts are +0.0005547417534721433 at N=4 and
+0.0007562142831308109 at N=8, so a large opposing size effect is not hidden
by the aggregate on these two trained sizes. All N/load curves remain available.

The B03 rate-0.1 anchor reproduces the small positive pattern on fresh seeds,
close to B02's +0.008396685564959483. The much larger within-actor rate gains,
positive H on all three seeds and shrinking cross-actor contrast jointly support
generic scalar-step-size sensitivity. That is a bounded inference from the
observed native returns, not a proof that scalar rate is the only mechanism.

The read-only figure [`MGTAP_B03_STEPSIZE_20260904.png`](MGTAP_B03_STEPSIZE_20260904.png)
shows all rates, selected/fixed-rate curves and paired contrasts. Dots/bands are
observed seeds/ranges, not confidence intervals. The MEI reference is on AUC.

## Headroom, resources and technical limits

The same-population oracle is 0.66875. AUC-selected FREE has endpoint mean
0.6281512225115741, leaving **0.040598777488426**; seed gaps are
0.0423475477430556, 0.03816189236111123 and 0.04128689236111116.
This is a now-available grid-tuned trained-N=4/8 diagnostic with full curves,
equal information and explicit same-panel selection. It is not a globally tuned
or held-out N=6/12 headroom record. Those historical missing quantities remain
missing. Existing unrelated host baseline packages do not match this information,
action or work surface; the accepted B03 configuration/summary is reusable here.

One remote task `mgtap_b03_main_307_311_313_19531d07` ran on `wsl_4070`, SSH
`hmasd-wsl-node`, exact detached cwd `/home/wu/hmasd-worktrees/mgtap_b03_20260904`.
Each of the three adjacent `admit-memory && runner` invocations passed both
4-GiB floors. Available physical/effective bytes were 12,995,407,872,
12,981,219,328 and 12,978,884,608 at respectively 23:58:13.108355Z,
23:58:26.675779Z and 23:58:41.591328Z on 2026-09-04.
The exact argv, output roots and receipts are in the result/summary.

Runner wall is **36.31423431600706 seconds** for one complete 24-fit B panel,
with no new pilot or failed scientific attempt. Shared setup is 0.0375011720
seconds; maximum RSS 483,786,752 bytes. Each fit is under 20 seconds, each
three-seed configuration is under 60, and the object is under 540. The supervisor
log reports 41 seconds; a later status uptime is an observation delay and is not
substituted for execution time. Cost currency is 36.314234316 seconds per this
valid comparison, not divided by 24 to call each configuration a separate result.
Including prior B02 pilot/main, the explicitly observed B02–B03 runner window
totals 45.25377291200857 seconds over two main comparisons; it is not lifetime cost.

The tracker accepted the same handle directly, notified this DM of exit 0,
and received terminal ACK. CM collected all raw roots at the same relative paths
in `C:/Projects/HMASD-worktrees/cm-n5-b03-20260904`; supervisor witnesses are
under its `.../exp/mgtap_b03_supervisor`. No running process, repeated launch,
quarantine, source repair after launch or missing learner measurement remains.
Resources are measured. Ordinary-shell Git preparation stalls occurred before
scientific acceptance and supply no scientific polarity.

Scope section 4 additions are none. CM/reviewer report 272 new source lines,
173 runner lines and 127 test lines. Orchestration is 110/399 = 27.57% of the
literal whole research diff; source-only is 89/272 = 32.72% and remains disclosed.
The spec explicitly excludes tests for the source-line cap, not for its diff
denominator. No tests/numerical duplication were added to dilute that ratio.
Under that stated accounting no section-5 budget is breached; a future owner
denominator clarification would be recorded as an engineering accounting change,
not a retroactive sign of algorithm value. Seven remote focused checks and the
actual complete summary/publication path passed; no open publication coverage
item remains. Technical conformance and native-return interpretation are separate.

## Prediction check and observation that bounds the result

DM predicted `B03_SELECTED_INSIDE_MEI`, with H>=0 and rate gains larger than
the fixed-rate coordinate separation. All are observed. The owner's prediction
is **not taken (unattended)**: existing ladder prediction item
`20260904-mgtap-006` has no reply. The current DM and integration owner-review
surfaces returned no pending instruction; today's review contains only an already
answered Portfolio agree, and yesterday's review file is absent. The earlier
drain instruction was superseded by the owner's explicit current research resume.

Strongest support: the fixed-rate separation reappears at fresh seeds, native
learning improves substantially for both actors under scalar rate changes, and
selected FREE surpasses METRIC 0.1 on every seed with matched per-fit work.
Strongest contradiction to a distinctive material metric benefit here: the
selected residual is far inside MEI and includes a negative seed, while the
generic FREE improvement is two orders of magnitude larger than that residual.
Strongest caveat: both selected rates are upper-edge winners, selected/read on
three development seeds. Anisotropic conditioning, clipping and implicit
regularization remain live; no ground-binding intervention identifies a pure
metric cause. No trained/held-out population transfer or partner co-adaptation
was measured, and no direction-wide exclusion follows.

## Decisions this intake produces

### 1. Accept the card-matched B observation — object tier

Options: (a) accept `B03_SELECTED_INSIDE_MEI` with scalar-rate sensitivity,
grid-edge and same-panel caveats; (b) call this equivalence or broad metric failure;
(c) treat the fresh positive 0.1 anchor as a material metric win. Recommendation
and selection: **(a)**. It applies the unchanged reading rule and retains both
the positive fixed-rate observation and the strong competent-comparator caution.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
Tier object, kind technical, provenance `OWNER_DELEGATED`, reversible, owner
flag none. A valid B result has no C consumption state. The scope denominator
is transparent; no unrequested machinery is accepted as the price of a result.

### 2. Choose the future of this coordinate family — direction tier, escalated

Options for Convergence: (a) park the present allocation-coordinate family until
a discriminator can name native value beyond the competent tuned FREE null;
(b) continue with one specified same-information B discriminator that keeps
tuned FREE as a comparator; (c) recast the question around a different explicit
multi-agent structure. DM recommendation: **(a)**, a reversible family boundary,
not a claim that the direction is scientifically impossible or a Portfolio change.

The same-information FREE comparator already absorbs the putative fixed-rate
advantage. Widening the scalar grid by default or comparing only against a bad
binding permutation could spend work without establishing native value over that
null. The remaining oracle gap and grid edge are reasons for uncertainty, not
reasons to erase this valid result. A concrete alternative from Convergence may
still justify one more B object at the same ceiling.

No direction decision is taken locally. Submit an `em_convergence` packet on
`em:metric_ground_transport_allocation:convergence`, with exposure and costs;
hold new learner selection at this clean boundary while its archived decision
forms. No C freeze, family closure, recast, lifecycle or priority change occurs
in this intake. Root can drive another admitted direction while the packet is
pending. The smallest next scientific discriminator must defeat or otherwise
change a competent same-information action/native return, not merely a statistic.

Owner-facing recommendation (Chinese): 建议暂缓当前配置坐标家族，直到能明确说明相对已调参通用策略的原生收益问题；这不是方向整体不可能的结论。

## Append-ready audit rows for Root

The shared audit is Root-owned. Exact owner item paths and rows are appended
after `item.py` assigns IDs, under the intended anchor `n5-b03-main-intake`.

Current origin/main MGTAP inbox ended at 013 before insertion. The Chinese
valid-result brief is `../../portfolio/owner/briefs/metric_ground_transport_allocation/2026-09-04_b03_main.md`
and is 347 characters, with the six required headings.

| time | direction | tier | kind | options | chosen option | reversible | provenance label | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-04T17:11:07-07:00 | metric_ground_transport_allocation | object | technical | (a) accept bounded B03 reading; (b) equivalence/broad failure; (c) fixed-rate win | (a) B03_SELECTED_INSIDE_MEI with scalar-rate, grid-edge and same-panel limits | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-mgtap-014.json` | none | |
| 2026-09-04T17:11:07-07:00 | metric_ground_transport_allocation | object | technical | reading-agreed; reading-disputed | valid-result brief recorded; owner prediction not taken | yes | DM_INTAKE | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-mgtap-015.json` | none | |
| 2026-09-04T17:11:08-07:00 | metric_ground_transport_allocation | direction | selection | (a) park current coordinate family; (b) one specified B discriminator with tuned FREE; (c) recast | no direction selection; (a) recommended for em_convergence | yes | DM_RECOMMENDATION_PENDING_PRO | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-mgtap-016.json` | none | |
