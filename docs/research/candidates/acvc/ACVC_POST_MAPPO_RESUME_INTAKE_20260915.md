# ACVC resume intake after the C/M comparison — 2026-09-15

**Owner resume applied.** The owner instructed the Claude Code research hub on
2026-09-15 to run the research loop for two directions from the recorded handoffs.
This intake resumes ACVC from
[ACVC_OWNER_PAUSE_AFTER_MAPPO_HANDOFF_20260914.md](ACVC_OWNER_PAUSE_AFTER_MAPPO_HANDOFF_20260914.md)
at its complete safe boundary. Nothing in the completed object is re-scored. The
hub acts as this direction's DM under `CLAUDE.md` (research hub) and AGENTS §1
(DM implements directly; CM/Implementer suspended). Scientific lifecycle remains
**CONTINUE / MEDIUM / recasts 2**, lowest sequencing priority, one occupied slot.

## What the completed object established

`ACVC_CLUSTER_MAPPO_COMPARISON_B01` (B/EXPLORE, one prospectively paired training
block, MASTER 28331 / EVAL 38331) on the private-information cluster host
(`make_cluster`, five UAVs / fifty users, H256, J = S/256):

| Panel | Mean J | Contrast | Value J | Card reading |
| --- | ---: | --- | ---: | --- |
| C | .3224744244 | C − M | −.0113099002 | DOWN |
| F | .3572239743 | **F − M (primary)** | **+.0234396496** | **F_ABOVE_MEI** (MEI .01 J) |
| own-dwell | .3450025971 | F − C | +.0347495498 | UP |
| M | .3337843247 | F − own-dwell | +.0122213772 | UP |

Retained limits, verbatim from the intake: one training block; F − M adverse in
22/64 matched worlds with worst −.2115133 J; conditional world SE .0104028 J
(within-block, not a training-variation estimate); different targets, losses,
ValueNorm, critic and optimizer arrangements between C/F and M remain
complete-method alternatives; no tuned same-information headroom exists. Native
walls C 1670.62 s and M 1521.04 s; 2,162,688 native team ticks, 24,576
optimizer steps, zero retries. Independent post-collection review found no
material defect. Nothing here is stable superiority.

## New fact since the pause

The hub's cross-direction review
([FOUR_DIRECTION_PROGRESS_REVIEW_20260915.md](../../../Claude_docs/reviews/FOUR_DIRECTION_PROGRESS_REVIEW_20260915.md))
and the completed FSD factorial
([FSD_INTERRUPTION_BATCH_B01_RESULT_EVIDENCE_20260915.md](../flexible_skill_duration/FSD_INTERRUPTION_BATCH_B01_RESULT_EVIDENCE_20260915.md))
supply the first same-repository measurement of *between-training-block*
variation of a within-block paired contrast: on the Scenario 1 host with a
5-rollout early recipe, two blocks gave a paired-contrast training SD of
.0785526 J (SI1280) and .0929470 J (SI128), and arm-level block-to-block
differences of .06–.09 J. That host, recipe and package differ from ACVC's
cluster host; the number is an indication of scale, not ACVC's variance.
Its consequence is arithmetical: if ACVC's block-to-block SD of F − M is of
the same order (.05–.08 J), one further block cannot resolve a +.023 J effect
(two blocks: SE ≈ .035–.057 J), and resolving it to ±.01 J would need tens of
blocks at about 3,200 s native per block. The direction's own intake already
names "training-block variability versus a broader package advantage" as the
next uncertainty.

## Options the DM weighed

- **(A) Replication series.** k additional independent unchanged paired blocks
  (C, F, own-dwell, M at 4096/H256, sole-final 64-world panels), prospectively
  pooled with the completed block under a declared rule. Cost about 3,200 s
  native per block plus support. It answers the stated uncertainty only if the
  true block SD is small (≲ .02 J); under the FSD-scale alternative it buys a
  wide interval around a small effect. The 2026-09-14 reviewer preferred one more
  reference fit before the pause; that preference predates the variance fact.
- **(B) Budget-scaling probe.** One fresh paired block of F and M only (C
  optional) at three times the training exposure of B01, with the identical
  64-world sole-final panel evaluated at 1×, 2× and 3× of the budget, evaluator
  state separate from training RNG. Question: does F − M grow, hold or vanish as
  training continues? Its reading is a *sign and scale* observation from one
  block, not a variance estimate; its decision value is that a package effect
  which does not grow past the early endpoint is not worth further replication
  spend, whereas an effect that reaches the .05 J scale at 3× makes (A)
  worthwhile at that budget. Ordinary plan about 5,000 s (F) and 4,500 s (M)
  native, two fits, plus two interim panels each; exact counts are computed from
  the runner before any launch. This is an outcome-informed new object under
  its honest label.
- **(C) No new experiment.** Record F_ABOVE_MEI at one block as the family's
  terminal evidence, keep ACVC ACTIVE-idle at lowest sequencing, and let the
  next Portfolio investment question decide whether a tuned-baseline
  calibration is funded. Zero cost; leaves the direction's package question
  unresolved and the two recasts exhausted.

**DM recommendation: (B).** It is the cheapest observation that changes the
decision between continuing and closing the C/M family, and it does so before
any replication money is spent on an effect whose scale may be below the
host's training variation. (A) is not recommended at this evidence; (C) is the
correct fallback if the node judges one block at three times the budget not
worth about 10,000 s native.

This is a direction-tier question (open/close of the C/M object family, next
object after a completed B under two exhausted recasts). It is posed to
`em:acvc:convergence`; no local selection is made and no Portfolio lifecycle,
priority or capacity change is proposed. Consultation exposure: zero fits,
models, loads, environment steps, optimizer steps, tests or profiling.

## Decisions this intake produces

1. Object technical: resume from the recorded boundary; no re-scoring, no repair
   rerun of the unwired auxiliary counters (they remain `unmeasured`). Applied.
2. Direction question: publish the option set above to the direction's Pro
   node with (B) recommended; park dependent work at this clean boundary; take
   the archived answer in as `PRO_FINAL`. Independent authorized work: none in
   ACVC until the answer; the hub drives FSD meanwhile.

Owner reviews at this boundary: none unapplied. Owner prediction: not taken
(unattended). Ledger: `docs/research/portfolio/audit/2026-09-15.md`.
