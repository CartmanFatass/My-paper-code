# DISH B05 seed101 result intake — 2026-09-06

**Accepted as a valid complete B/EXPLORE result.** Seed101 gives `Delta_101 = +236.25`
mean native service ticks, `D_CONTROL,101 = -16.5` and `D_LOW_LR,101 = +219.75`.
This is a second positive paired mean and, in this instance, a positive change from LOW_LR's
own initialization. It is accompanied by a -277 condition difference and 209 LOW_LR evaluation
invalid commits against CONTROL's zero. Both facts remain in the reading. No evaluation legal
transfer occurred, so RETAIN/COPY/SHADOW source value remains unestimated.

## 1. What was checked against the card

Card: `DISH_CONTROL_LOW_LR_B05_SCIENCE_CARD_20260906.md`, frozen in `18812ba5e`, integrated as
`cd317810c`. Direction choice: post-B04 PRO_FINAL at immutable
`a9718a45e0e3c1149513e0ae4289eaec1dd28a46`, complete response
`pro_packets/20260906_post_b04_convergence/archive/RESPONSE.md` (37,709 bytes,
SHA256 `042f100d5f8fe1f2dc222e73ef8eb7c23bc98855dac51bcc80b660bfc3d62511`). Full archived
text was read, then compared with the immutable Git file; only Windows checkout line endings
differed. Current owner resume superseded the historical execution stop. No specification
conflict was found in applying the question or its burden under evidence-spec §§4, 5.2,
11.4, 11.7–11.9.

CM source commits `ac55ec18f`, `83a6784b4`; Root integrated and pushed exact launch SHA
**`1d87e02194158d6bca0eaa4e7f70a1c1098bb121`**. DM inspected the actual explicit seed/object
plumbing and synthetic-primary test, plus the focused shared-cost correction. Independent
source review and its follow-up found no material gap. B04 defaults stay seed89/B04; B05
retains the B04 RNG family. No imported-module global mutation, r06/native, optimizer,
normalization, reward, information or termination change was introduced. Final source change
is 48 added / 18 deleted non-test lines; focused test 125 lines; runners remain below 600.
No engineering-scope §4 machinery was added and no §5 budget was breached.

CM's completed E0 return is `control_low_lr_b05_20260906/TECHNICAL_ACCEPTANCE.json`, committed
in `4d50bc9cf5f2f7ec2498a9ad45bd53247a7d063b`, integrated by Root as `add78a7b7`.
The adjacent three `summary.json` files, `low_lr/paired.json`, three `final_stdout.json`
files, recorded resets, five admissions, OS times and supervisor facts are the source evidence.
`DISH_CONTROL_LOW_LR_B05_CM_RECORD_20260906.md` records implementation, focused review,
exact commands and technical acceptance. `LAUNCHES.json` binds node/cwd/handles/argv.
Runtime root: `/home/wu/hmasd-worktrees/dish-b05-seed101-20260906/temp/directions/`
`degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/`; initial state and
both final checkpoints remain there. No model or experiment was re-executed during DM intake.

I checked the returned document against card §§2–7, then read the underlying summaries and
recomputed means, all paired/before-after differences and the two-seed descriptive mean.
I checked the actual seed/master/launch/source fields, corresponding reset equality across
all three controllers, count-0 reference state, all sixteen LR read-backs and finite flags,
actual exposure, twelve complete fixed-range rows, native events, terminal causes, receipts,
and the full-wall allocation from retained stdout P. These are direct artifact checks;
the source review/CM runtime observations are identified separately, not represented as a
second DM execution. Process success alone did not determine the scientific reading.

## 2. Twelve rows and the primary

Each row uses its seed101 reset and fresh native/recurrent state, speed4/slot0/block0,
GROUND-TERMINAL-LINEAR-CLEARANCE-A03, corrected renewal boundary, native float64, policy FP32,
one compute thread. All twelve rows executed all 1,200 ticks; each terminal cause is
`fixed_horizon`, with zero unstepped/zero-filled ticks. No row was removed or shortened.

| Condition | Reference | CONTROL | LOW_LR | LOW_LR - CONTROL | CONTROL - reference | LOW_LR - reference |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| TARGET_VISUAL_MASK / K8 | 96 | 178 | 591 | +413 | +82 | +495 |
| TARGET_VISUAL_MASK / K4_TO_K12 | 330 | 491 | 214 | -277 | +161 | -116 |
| TERRAIN_RELAY_MASK / K8 | 323 | 153 | 695 | +542 | -170 | +372 |
| TERRAIN_RELAY_MASK / K4_TO_K12 | 440 | 301 | 568 | +267 | -139 | +128 |
| **Mean** | **297.25** | **280.75** | **517.0** | **+236.25** | **-16.5** | **+219.75** |

MEI remains +24 mean service ticks, before/after scale ±24. No new per-condition threshold
or tolerance was applied. Master is
`cd461a1f466eb5cf40c42dc71d29e103a9dbf00f292d5673a8560069585e01c0`, matching SHA256 ASCII
`DISH-CONTROL-LOW-LR-B04/seed/101`; actual phases are **2/3/0/1**. The initializer norm
38.261779002554604 and count-0 actor/snapshot/critic Welford reference are shared; reference
parameter norm is unchanged across each evaluation. This seed's reference is neither an
upper bound nor evidence of a tuned host baseline.

| Native companion, in the row order above | Reference | CONTROL | LOW_LR |
| --- | --- | --- | --- |
| invalid_commit | 0 / 26 / 31 / 0 | 0 / 0 / 0 / 0 | 108 / 0 / 101 / 0 |
| energy (native units) | 274178.22 / 289834.32 / 287073.04 / 267535.17 | 289103.31 / 285512.97 / 288205.51 / 287053.58 | 288085.76 / 275908.33 / 287672.07 / 225337.75 |
| legal transfers | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |

The other six hard-event classes (`buffer_clear`, `command_slew_breach`, `dual_owner`,
`dual_payload`, `separation_breach`, `token_gap`) are zero in all twelve evaluation rows.
All service is recorded before any transfer; post-transfer service is zero. These observations
do not establish safety or a zero event rate. LOW_LR energy is lower than CONTROL in each
equal-duration row (mean 269250.98 versus 287468.84); it is higher than initialization on both
K8 rows. The useful average therefore has a clear invalid-commit cost and a substantial
TARGET/K4_TO_K12 service loss. It is not dominance or harmlessness.

## 3. Card reading rule applied verbatim

The following is the frozen card §5 reading table, without an outcome-informed rewrite.

| Row | New observation | Allowed reading and next recommendation |
| --- | --- | --- |
| 1 | `Delta_101 >= +24` and the service/event/energy trade-off remains worth developing | Another instance of a useful mean increment; consider on both complete pairs whether LOW_LR remains a development candidate. Mixed rows alone do not cancel the signal. No stability, per-condition universal advantage or safety claim. |
| 2 | Row 1 plus `D_LOW_LR,101 <= -24` | Smaller loss against CONTROL, not initialization recovery; future investment must confront the better zero-update reference. |
| 3 | LOW_LR before/after inside (-24,+24), or >= +24 | Report near-initial service or positive change respectively; neither equivalence nor generally stable learning. |
| 4 | `Delta_101` inside (-24,+24), clearly negative, or a gain with a severe native trade-off | Qualify repeatability/usability beside seed 89 without denying +182.75. No automatic third seed, lower rate or longer training; continuing, ending this configuration or a new named question needs a separate decision on the complete result. |
| 5 | New CONTROL no longer below initialization, or the separation termination not repeated | The earlier loss/termination did not repeat in this instance; historical evidence stands, no zero-event-rate inference. Read the LR pair independently. |
| 6 | Still no final-evaluation legal transfer | Incumbent-only comparison; source difference remains unestimated, not disproved. |
| 7 | Input, training or primary measurement incomplete/damaged | Keep actual exposure and independently trustworthy rows; no fabricated complete pair. Report the exact dependent gap, without collateral quarantine of B04/B03. |

**Applied rows: 1, 3 (positive before/after), 5 (the non-repeated early separation termination
component only), and 6.** Row2 does not apply: LOW_LR is 219.75 above this initialization.
CONTROL is still 16.5 below its reference, so the first component of row5 is false. Its much
larger earlier mean losses did not repeat beyond the declared scale in this instance; this
does not mean equivalence or absence of learning-induced losses in individual conditions.
Row7 does not apply to the completed object. The failed initial focused setup is recorded
in §5; it did not damage the subsequent real observations.

Row1's utility clause is the DM's bounded development judgment, not an automatic claim from
the positive number: the +236.25 mean, positive before/after and lower energy in all four
CONTROL comparisons justify retaining LOW_LR for the node's next choice, while all rows finish
without separation/ownership-envelope events. The 209 invalid commits and -277 row remain
material contradictions. I do not classify them as cancelling all development value under
row4, nor call them harmless or invent an event-weighted reward. They restrict the next
question and preclude general policy or safety endorsement. No extra experiment follows
from this reading alone.

## 4. Independent seeds, predictions and bounded scientific update

| Paired training seed | Reference mean | CONTROL mean | LOW_LR mean | Paired difference | CONTROL before/after | LOW_LR before/after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 89 (B04) | 393.75 | 154.0 | 336.75 | +182.75 | -239.75 | -57.0 |
| 101 (B05) | 297.25 | 280.75 | 517.0 | +236.25 | -16.5 | +219.75 |

The equal-weight two-seed difference is **+209.5**, descriptive only. `RUN_SCORES.csv` selects
one final four-condition mean per actual training run; the scientific-tools `summarize_runs.py`
output `RUN_SUMMARY.json` preserves both paired differences. Initial references are kept
outside that tool's training-run table. Four conditions are not four training seeds; B03's
package pair is not an LR replicate. No condition bootstrap, population interval or stable
superiority claim is made from these two outcome-informed exploratory pairs.

DM prediction `D_CONTROL,101 <= -24` **missed** (-16.5). The positive sign/mixed-row portion
of the Delta prediction held, but its inside/near-band magnitude prediction **missed**
(+236.25); a broad mixed-sign prediction is not credit for predicting that mean. The competing
useful-mean observation occurred with the native costs above. Owner prediction: **not taken**;
primary-checkout `item.py reviews --json` returned `[]` at this intake boundary.

Strongest support: the new seed repeats a useful mean LR difference with actual treatment,
learning and complete native evaluation, and LOW_LR now improves its own initialization.
This positive difference exists without any early evaluation termination. Thus the new
instance's gain is not solely an artifact of the earlier CONTROL tick-684 termination;
this does not decompose or explain that old row's +668.

Strongest contradiction: TARGET/K4_TO_K12 loses 277 versus CONTROL and 116 versus its
reference, while both K8 LOW_LR rows make many invalid commits. The absolute learning and
event/energy relations differ between the two seeds. No final evaluation transfers legally.
Surviving alternatives are seed/condition-specific motion, recurrent/normalization/parameter
interactions, auxiliaries and training-data shifts; smaller parameter displacement alone
does not identify the cause. The LR hyperparameter also scales AdamW's existing decay.
Training CONTROL's three legal transfers show ordinary transfer can occur on the training
path; they are not matched RETAIN/COPY/SHADOW comparisons and do not estimate source value.

Question-driven literature check for the stronger-than-predicted gain and next-question
selection: My-lib's existing CLI coverage reports only two `synthetic-core` fixture papers
(coverage date 2026-07-26), explicitly excluded from scientific evidence. Inst-sci's actual
formal `llm-index/catalog.v2.jsonl` contains 190 records. Bounded title/algorithm searches for
the canonical PPO/implementation/reproducibility titles returned no match; broader exact
PPO/MAPPO, learning-rate, normalization and hyperparameter searches returned candidate metadata
from other methods/settings, not a verified explanation of this AdamW/recurrent CONTROL
comparison. No source passage or literature-based mechanism claim is asserted from those
index matches. This coverage gap neither changes validity nor establishes novelty; the
next-question recommendation rests on the direct DISH record, with no claim of a literature-
established normalization cause or general low-rate theorem.

## 5. Counts, receipts, cost and implementation deviations

| Training quantity | CONTROL | LOW_LR |
| --- | ---: | ---: |
| ordinary transitions / completed updates / optimizer steps | 65536 / 16 / 512 | 65536 / 16 / 512 |
| next-label steps / next-mask count | 65536 / 65504 | 65536 / 65504 |
| eligible E / delay 2E | 17208 / 34416 | 18957 / 37914 |
| native training calls, lower–upper (`2N+2E+H`) | 165488–509648 | 168986–548126 |
| parameter L2 displacement / relative to initial norm | 8.425011 / 0.220194 | 1.956013 / 0.051122 |
| training service / legal transfers | 29580 / 3 | 29166 / 0 |
| training invalid commits | 1915 | 2074 |

H remains unmeasured with `0 <= H <= 20E`. The other six training hard-event classes are zero
in both arms. Every curve retains finite loss/gradient flags and both actual parameter-group
rates, `[3e-4,3e-4]` or `[3e-5,3e-5]`, at all sixteen updates. Finite mean-gradient ranges
are 19.15–297.75 and 28.37–2015.33; their size is not a nonfinite fault or a parameter-step
measurement. There are 131072 ordinary transitions, 32 update rounds and 1024 optimizer
steps across the pair, plus four reference and eight final episodes, all 14400 actual ticks.
The four reference rows have zero learner/label exposure. No intermediate checkpoint,
additional seed, efficacy stopping, changed reset or bad-row rerun occurred.

Five adjacent node admissions (`focused`, `focused2`, `shared`, `control`, `low_lr`) all pass
physical and effective 4GiB floors; measured availability spans 15,656,681,472–15,667,519,488
bytes. Node is `wsl_4070`; each admission immediately precedes its invocation in the detached
command. Initial focused invocation exited1 before the test body because the pytest basetemp
parent was absent. The ordinary directory repair, same source and fresh admission yielded
one passing focused test. Preserve the first 1.15s plus repaired 1.07s; no real initializer,
learner or evaluation ran in the failed invocation. Shared, CONTROL and LOW_LR each exited0.
The monitor's adopted handles and terminal notifications were collected; no routine polling
was duplicated by DM, and no run was relaunched to transfer observation.

| Full OS invocation wall | Seconds |
| --- | ---: |
| first focused setup failure | 1.15 |
| repaired focused check | 1.07 |
| common initializer/reference | 7.11 |
| CONTROL | 210.63 |
| LOW_LR, including paired reduction/publication | 212.86 |
| **Sum** | **432.82** |

Final stdout gives shared paired reduction/publication `P=0.001856654998846352s`.
`S=1.15+1.07+7.11+P=9.331856654998846s`; exact charged CONTROL is `Cwall+S/2`
= **215.2959283274994s**, LOW_LR is `Lwall-P+S/2` = **217.52407167250058s**.
Both are within 1800s and total432.82s is within3600s; the reserved 30s is not billed as
observed work. These values use outer OS wall and retained stdout P, not prepublication wall,
the old conservative runner charge or late-collected supervisor `uptime_seconds`.
Aggregate CPU is444.01s; study elapsed critical path is2663s, including inter-invocation
monitor/control-plane gaps. These are different quantities. No code/test/runtime cap breach.
Scratch remains unmeasured (`resources_unmeasured`); OS per-process RSS maxima are retained,
not summed across processes. These missing optional resources do not invalidate service.

## 6. Decisions this intake produces

1. **Object tier, validity.** Options: (a) accept the complete B05 result while retaining the
   failed focused setup and all costs; (b) quarantine a damaged training/primary dependency.
   Recommend/select(a): the required real training, primary and companion measurements are
   trustworthy and complete. Owner-delegated decision (unattended, 2026-09-03 instruction): (a).
   This is B evidence and has no consumption state.
2. **Object tier, reading.** Options: (a) rows1/3/5-termination/6 as the bounded reading above,
   with invalid commits and the negative condition explicit; (b) regard the native trade-off
   as cancelling development value under row4; (c) treat two positive means as stable or
   universal superiority. Recommend/select(a) for the stated native evidence and exploratory
   scope; (c) is unsupported. Owner-delegated decision (unattended, 2026-09-03 instruction): (a).
   No outcome or adverse event was discarded. Owner flags: no overruled material critic,
   no recast or Portfolio decision; native utility restrictions remain prominent.
3. **Direction tier, next named question.** Options: (a) return the complete two-pair/native
   record to the same Convergence node to select the next bounded question or narrow stop;
   (b) automatically buy a third LR seed, lower rate or longer training; (c) locally close or
   recast the direction. Recommend/select referral(a); dispatch is recorded in the follow-up
   packet, and no direction decision exists yet.
   Two positive means do not themselves justify more of the same comparison. No new experiment
   is authorized or launched by this intake. Portfolio remains Root's surface.

Owner brief: `docs/research/portfolio/owner/briefs/degraded_incumbent_shadow_handover/`
`2026-09-06_B05-seed101-result.md`. Audit: `docs/research/portfolio/audit/2026-09-06.md`.
Current owner19:50 rulings in `HANDOFF_20260906_CLAUDE.md` §5 are applied as existing authority:
the next Convergence request can bind the reconciled conversation, the formerly unattributed
chat turns were owner input, and ordinary P3/P4 console items stay skipped. No reply is invented
and no owner wait is imposed. Next discriminator is the node's class-correct, cost-bounded
choice on the remaining ordinary-application/source question and measured native trade-offs.

scope: none
