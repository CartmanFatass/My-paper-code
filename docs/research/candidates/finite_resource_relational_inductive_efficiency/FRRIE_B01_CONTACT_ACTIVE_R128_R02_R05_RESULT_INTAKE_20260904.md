# FRRIE contact-active R128 R02 R05 result intake — 2026-09-04

Status: `VALID_B_EXPLORE / R02_SMALL_OR_ROSTER_MIXED`.

Current execution overlay: the owner's 2026-09-05 instruction **“继续自动推进任务”** supersedes
the earlier pause. The conforming R06 revision was accepted for one run on 2026-09-05T09:19:47Z.
This R05 result and its interpretation remain unchanged. See
`FRRIE_R06_ACCEPTED_RUN_INTAKE_20260905.md`; the previous pause handoff remains historical.

## What DM checked

DM read the original R02 card, prospective R05 addendum, E0 Markdown, unchanged publisher JSON
and terminal CM record at pushed `2b23c7633a29b0936f5971bc58cd50941dde1f2e`. The JSON's
22 completion checks, expected/observed counts, eight estimands, exposure, work, resources
and native-cell contents were inspected against the card. CM directly collected retained
process evidence and recomputed all eight gaps from cells; DM applies the science rule below.
No new learner, test, root, RNG or result invocation was used for this intake.

The original SystemExit(0) is separately witnessed from pdb/supervisor exit 0. Expected
missing-local queries after normal program completion are not learner failures, and no second
script body ran. Technical success alone does not establish a scientific effect.

## Rule applied verbatim, in order

| branch | rule and bounded reading |
| --- | --- |
| `R02_INVALID_INCOMPLETE` | A common-integrity item fails; remote/local admission is absent or below 4 GiB; real learner transition/update/evaluation counts or exposure are zero/missing; information/work differs; raw initialization is not paired; the initial tight clip does not change exactly five coordinates; optimizer moments change during projection; or required learner-side curves/counts are absent. Quarantine; no result. |
| `R02_EDGE_BELOW_UNIFORM` | The result is valid and contact-active, but `e_128 < 0` at either seen roster. Report every direct curve and gap; the containing comparator is not competent on the affected cell, so the arm gap is nonidentifying. |
| `R02_FAVORABLE_BOTH` | EDGE is at least uniform on both rosters and `d_128 >= +0.005` at both. Preliminary one-root favorable activated-projection signal only. |
| `R02_ADVERSE_OR_MIXED` | EDGE is at least uniform on both rosters and `d_128 <= -0.005` at either. Bounded adverse or roster-mixed evidence for this configuration only. |
| `R02_SMALL_OR_ROSTER_MIXED` | The complete valid contact-active result reaches none of the earlier branches. Report literal signs/magnitudes; no stable effect claim. |

The first row is false: common integrity, fresh admission, paired initialization/information/
work, initial five-coordinate clipping, projection moment preservation and full nonzero curves
are present. Final EDGE exceeds uniform at both rosters, so row two is false. Neither the
positive-both nor adverse-either MEI condition holds. The first matching branch is therefore
**R02_SMALL_OR_ROSTER_MIXED**, also the unchanged publisher's result.

| update | N=9: PHY minus EDGE | N=15: PHY minus EDGE | N=9: EDGE minus uniform | N=15: EDGE minus uniform |
| --- | --- | --- | --- | --- |
| 0 | +0.000000856631 | +0.000001040776 | -0.001214709249 | +0.001417723880 |
| 32 | -0.000000682427 | -0.000000140211 | +0.001719594731 | +0.001222603256 |
| 64 | -0.000007822365 | +0.000062267249 | +0.000872600350 | +0.002513974044 |
| 128 | +0.000467050572 | -0.000867790232 | +0.000507024660 | +0.000484763443 |

These are rounded displays, not substituted reading inputs. The E0 Markdown and unchanged
118,913-byte JSON preserve full precision, all 18 cells and their J, deliveries, mean minimum
deliveries, waste, action and event inventories.

## Counts, contact, receipts and cost

| quantity | checked observation |
| --- | --- |
| literal root | `2e6dfa0a297cf52627a4fdb48c775c5649a4dfbed0195b980d2550605389d807`, seed 1 / `FRRIE-B02-CONTACT-BLOCK-001` |
| task / launch SHA | `frrie_b01_contact_r02_5e6d47f0_05` / `5e6d47f0cc05dfdf345bfe7f3f8661d1ffcf7ecc` |
| actual node | `wsl_4070`, Linux Python 3.10, CPU FP32, one Torch thread, native width 32 |
| start / end | `2026-09-05T00:53:58Z` / `2026-09-05T01:09:35Z` |
| fresh admission | `00:53:58.408321Z`; physical and effective each 12,670,226,432 bytes |
| paired updates; per-arm backward / Adam | 128; 128 / 128 |
| per-arm factual episodes / transitions / training native slots | 8,192 / 98,304 / 630,784 |
| per-arm learned evaluation episodes / slots | 2,048 / 24,576 |
| full evaluation including uniform | 18 cells, 4,608 episodes, 55,296 slots |
| full invocation native slots | 1,316,864 |
| completion checks | 22 of 22 true |
| supervisor / runner wall | 937 / 898.6516333679974 seconds |
| directly attributed PHY / EDGE wall | 160.1987184420359 / 159.29206010704365 seconds; shared work is additional |
| peak RSS | 615,534,592 bytes |

Each cell has 256 episodes and 3,072 transitions; action totals equal N times transitions.
Shared evaluation tapes have nine uses per roster. Full model preservation during evaluation
and native/replay checks remain enabled; both 128-row learner curves are complete.

Raw paired initialization agrees. Tight projection changes exactly `[2,4,11,12,16]` before
checkpoint 0; wide initialization is identity. Tight projection subsequently contacts in
50/128 updates with 99 coordinate-clipping events, separate from the initial five changes.
Maximum overshoot is 0.008026394993066788; cumulative tight displacement including initialization
is 0.028062518686056137. Wide contact is absent. Every projection preserves optimizer moments.

Machine-generated exposure:
`updates=128; adam_lr=0.0003; nominal_lr_exposure=0.0384; init_half_range=0.05; nominal_exposure_over_init_half_range=0.768; tight_box_half_width=0.04; initial_projection_changed_coordinates=5`.

Final parameter Linf displacement from raw initialization is 0.02603882923722267 for PHY and
0.026373978704214096 for EDGE, about 0.52 and 0.53 times the initial half-range. Nominal
exposure is not an observed displacement bound. Contact and movement alone are not mechanism value.

Both four-hour per-arm and eight-hour total caps were met. Source diff is zero, no tests were
repeated for R05 and no scope-budget breach is observed. Exception telemetry used the existing
declared debugger input. Per-cell RSS/wall and scratch were not separately measured; this is
not a resource claim. The full publisher output, fresh 504-byte receipt and six supervisor files
remain at the accepted remote paths and CM's ignored `technical/r05-collection/`, listed in
the terminal CM record. Later status uptime is not execution wall.

R05 adds one valid remote B result costing 937 supervisor / 898.651633 runner seconds. A01's
927 / 902.249676 seconds remain separate A/RECON cost. Neither is pooled with the earlier
four-result Windows window or called a lifetime average. RIDGEGATE-2Z headroom still lacks a
feasible upper policy and tuned same-information generic baseline; uniform is minimal competence.

## Bounded scientific reading and predictions

Direct observation: this root develops small opposite-sign native-return differences under
initial and repeated tight contact. The original no-contact explanation no longer accounts for
this particular result. Both absolute differences are below the declared 0.005 MEI.

Strongest support is the complete paired learner/evaluator evidence with a containing arm,
matched information/work, repeated contact and a native consequence. Strongest contradiction
to a meaningful tight-box advantage at this budget is that both gaps are below MEI and have
opposite signs after activation. This does not establish equivalence or absence of smaller
effects. EDGE's small positive margins satisfy the original minimal rule, not a tuned-baseline claim.

Surviving alternatives are limited effective learning at 128 low-LR updates, common K0 dominance,
generic shrinkage/Adam geometry, one-root variation and roster-dependent effects. Claim ceiling
is B/EXPLORE on the actual Linux CPU surface, one literal root, INTACT, seen N={9,15}; no
relation specificity, held-out transfer, arbitrary N, membership-change, seed-population or
stable-superiority claim follows.

DM predicted `R02_SMALL_OR_ROSTER_MIXED`, conditional on EDGE at least uniform at both rosters:
**matched**, including the condition. Owner prediction: `not taken (unattended)`. Current
integration and DM owner reviews returned `[]`; today's only review was already answered,
yesterday's file is absent, and no direction-specific audit override or prediction reply exists.

R04 and attempt02 causes remain separate and unresolved. Successful completion does not
reproduce a failure, diagnose cause or prove repair. A01 retains its A class. Real publication
completed, but formal-sized end-to-end publication test coverage remains an open engineering
item, without becoming another B launch condition.

## Decisions this intake produces

### Validity and reading

Options: (a) accept the complete B result under its first-match rule; (b) infer stable
equivalence, superiority or repaired root cause; (c) reject it because EDGE is only slightly
above uniform instead of applying the card's stated minimal condition.

Recommendation and selection: **(a)**, preserving prospective class and bounded observation.
Object tier, kind `technical`, owner flag `none`.
Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**, `OWNER_DELEGATED`.

### Next discriminator

Options: (a) a new B rung with shared Adam LR 0.003 at the same 128-update work and literal
root; (b) extend low-LR training to 512 updates; (c) repeat this dose on another root;
(d) further shrink the box while leaving the weak-learning regime unchanged.

Recommendation and selection: **(a)**. It raises nominal exposure tenfold while holding
interaction count, training-address prefix, evaluation opportunity and per-arm work fixed.
The runner's cost law is unchanged. Option (b) is useful later but increases training work
fourfold and changes the training-information prefix; (c) describes root variation without
testing the current exposure explanation; (d) changes shrinkage while leaving that explanation
unaddressed. Thus (a) is the clearest immediate discriminator per unit work, not an optimal-LR claim.

The new card is `FRRIE_B01_CONTACT_ACTIVE_R128_LR003_R06_SCIENCE_CARD_20260904.md`. This is
an explicitly outcome-informed B adaptation inside the accepted B01 projection/optimizer family.
R05 stays immutable; its common-root low-LR values are a descriptive anchor, not an independent
replicate or pooled confirmatory panel. There is no family opening, C promotion, direction
disposition, priority or lifecycle action.

Object tier, kind `selection`, owner flag `none`.
Owner-delegated decision (unattended, 2026-09-03 instruction): **(a)**, `OWNER_DELEGATED`.
CM implements only the literal LR/identity variant and checks actual optimizer settings and
publication before one fresh admitted detached invocation. No R06 ran before this decision.
Tracker owns subsequent observation, CM technical acceptance and DM scientific intake.

## Owner surfaces and append-ready audit rows

A Chinese brief and CLI-created technical, brief, selection and new-card items accompany this
intake. The existing B ladder already has its prediction item; this rung's prediction is on
its card. Root appends the rows below under `frrie-r05-intake-r06-selection` in the shared
2026-09-04 audit ledger and integrates Portfolio. Times and IDs come from the CLI receipts.

| time | direction | tier | kind | options | chosen option | reversible | provenance | evidence path | owner flag | owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-04T18:35:15-07:00 | finite_resource_relational_inductive_efficiency | object | technical | (a) original-rule bounded B result; (b) infer equivalence, superiority or repair; (c) impose a stronger comparator gate | (a) VALID B/EXPLORE R02_SMALL_OR_ROSTER_MIXED | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-frrie-023.json` | none | |
| 2026-09-04T18:35:16-07:00 | finite_resource_relational_inductive_efficiency | object | technical | reading-agreed; reading-disputed | publish R05 Chinese brief; no owner reading imputed | yes | VALID_RESULT_INTAKE | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-frrie-024.json` | none | |
| 2026-09-04T18:35:18-07:00 | finite_resource_relational_inductive_efficiency | object | selection | (a) shared LR 0.003 at fixed R128 work/root; (b) low-LR 512 updates; (c) same dose another root; (d) smaller box | (a) new R06 B dose discriminator within accepted family | yes | OWNER_DELEGATED — Owner-delegated decision (unattended, 2026-09-03 instruction): (a) | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-frrie-025.json` | none | |
| 2026-09-04T18:35:19-07:00 | finite_resource_relational_inductive_efficiency | object | technical | accept; reject; revise | freeze R06 card; accept recommended, no owner choice imputed | yes | CARD_RECORDED | `docs/research/portfolio/owner/inbox/2026-09-04/20260904-frrie-026.json` | none | |

## Evidence

- `FRRIE_B01_CONTACT_ACTIVE_R128_R02_SCIENCE_CARD_20260904.md`
- `FRRIE_B01_CONTACT_ACTIVE_R128_R02_R05_EXECUTION_ADDENDUM_20260904.md`
- `FRRIE_B01_CONTACT_ACTIVE_R128_R02_R05_RESULT_EVIDENCE_20260904.md` and adjacent JSON
- `FRRIE_B01_CONTACT_ACTIVE_R128_R02_R05_CM_RECORD_20260904.md`
- `FRRIE_R04_RECONSTRUCTION_A01_INTAKE_20260904.md`
- `FRRIE_B01_CONTACT_ACTIVE_R128_LR003_R06_SCIENCE_CARD_20260904.md`
