# Scientific intake — ACVC_M_DEPLOYMENT_TRANSFER_B01

DM: the Claude research hub; authoring `C:/Projects/HMASD-worktrees/codex-acvc` / `codex/acvc`.
The one granted fit is complete and technically accepted, source
`a741758a11e6c9d9888cbc852095544f3df4e04f`. Inputs:
[full E0](ACVC_M_DEPLOYMENT_TRANSFER_B01_RESULT_EVIDENCE_20260915.md),
[machine reduce](evidence/m_deployment_transfer_b01_20260915/reduce/summary.json),
[world differences](evidence/m_deployment_transfer_b01_20260915/WORLD_DIFFERENCES.json), the raw
collection, the [card](ACVC_M_DEPLOYMENT_TRANSFER_B01_PROSPECTIVE_CARD_20260915.md) as corrected
by `em:acvc:convergence`, and the Portfolio grant.

## What was checked and rule applied

Direct observation: the summary carries object ACVC_M_DEPLOYMENT_TRANSFER_B01, master 28531,
namespace 38531, launch sha a741758a1, upstream de66d7a4b, `status` complete, `fit_complete`
true, 4,096 training episodes, 2,048 rollouts, 8,192 + 8,192 optimizer steps, one checkpoint
loaded three times, 192 evaluation episodes, five constructors, empty `limits`; all 4,288
episode rows have 256 steps and finite fields; all 2,048 update rows are finite; parameter
displacements finite; admission passed (15.6 GB available); supervisor and native exits 0;
stderr empty; every collected file byte-identical to its remote digest. The runner's
`--mode reduce` judged the fit eligible and all three contrasts complete.

The card rule (T_F > +.01 TRANSFERS; inclusive ±.01 WITHIN_MEI; < −.01 ADVERSE) applied
verbatim to the unrounded **T_F = +.018338005502877976 J** gives **TRANSFERS** (53/64 worlds
favorable, conditional SE .0055 J). Supporting: T_D = +.009069800680064894 J WITHIN_MEI (50/64
favorable); paired U = F(M) − own-dwell(M) = +.00926820482281308 J WITHIN_MEI (48/64 favorable,
conditional SE .0055 J). Counters: 6,752 retraces on 6,752 opportunities (F(M)), 5,110 holds
on 5,110 opportunities (own-dwell(M)), every substitution distinguishable. No accumulation with
blocks 1 or 2.

## Scientific reading and limits

> **Correction 2026-09-15 (`em:acvc:convergence` result review, `PRO_FINAL`,
> [intake](pro_packets/20260915_m_deployment_transfer_result_review/INTAKE.md)).** The paragraphs below overstate in three places and the E0 and
> `DIRECTION.md` carry the corrected wording: U contrasts two complete deployment packages
> (unequal realised schedules, diverging downstream states), not a retrace-specific
> remainder, and does not identify "what transfers most clearly"; T_D about half of T_F
> describes three means, not a mediation; the .044 J block dispersion of F(C)−M is not the
> variability of T_F, whose between-fit variation is unmeasured rather than inherited. The
> recorded primary, counts and decisions are unchanged.

Inference: on this one fresh instance of the conventional private recurrent proposer, the
fixed retrace law adds an MEI-sized increment, and roughly half of that increment is shared
with the simpler zero-command law on the same predicate; the retrace-specific remainder over
holding still (U) is inside the MEI band. The transformation therefore "transfers" in the card's
sense (its value is not tied to the C proposer that was trained beside it), but what transfers
most clearly is the intervention at link-loss opportunities, with the direction of the
retrace command adding a within-band amount on top. The C side showed a larger F−C
(+.047/+.035 J) and F−own-dwell (+.032/+.012 J); those are different proposers and instances,
reported beside, never matched or pooled.

The strongest surviving alternative is instance variability: blocks 1 and 2 put the
between-instance SD of the C-side F−M at .044 J against a within-block SE of .010 J, and T_F
here (+.018 J) is of that order. One instance cannot separate a real transfer from a favorable
draw; §11.8 names one or two independent training seeds as the default follow-up for a real
bounded improvement, and no seed must be positive.

Boundaries: direct observation versus inference as above; scientific result (TRANSFERS on this
instance; U within band) versus engineering conformance (accepted, no defect; the fit ran in
985 s on an idle node against a 2,500 s projection scaled from a contended block-2 wall);
direction-local advice (below) versus Portfolio action (none); historical provenance (the
two-block C/M claim stands unchanged) versus current authority (this intake). No stable
superiority, discardable C, F(C) versus F(M), tuned headroom, equivalence, mechanism, default
change or C promotion follows.

Costs: native wall 985.12 s, CPU 983.51 s, peak RSS 585,028 KiB; plan not a cap; no stop or
retry.

## Decisions this intake produces

1. **Technical/object acceptance** — options: accept the complete bounded fit / quarantine an
   integrity defect / rerun. Recommend and select acceptance; every required count, reward,
   endpoint, counter and receipt is present. Owner-delegated decision (unattended, 2026-09-03
   instruction): accept; preserve the original. No further fit is bought.
2. **Scientific conclusion** — options: report the card-fixed TRANSFERS with T_D and U within
   the band / claim the transformation is established as portable / read U as showing the
   retrace direction adds nothing. Recommend and select the bounded report (a): one-instance
   transfer of the fixed law to M, with the retrace-specific part unresolved beyond the MEI.
   Owner-delegated decision (unattended): (a).
3. **Continuation** — the grant ends with this intake (zero replacements or extensions). The
   next choice is direction-tier: the card's TRANSFERS branch "motivates a development question
   'M plus the fixed transformation' and makes a later F(C) versus F(M) comparison worth asking",
   and the family was concluded by the node on 2026-09-15 with this object as its reopening
   candidate. Options for `em:acvc:convergence`: (A) record the transfer observation and keep the
   family concluded, ACTIVE-idle, naming the fact that would reopen it; (B) one further
   independent M instance with the same three panels (labels fresh, the §11.8 default follow-up;
   a Portfolio investment question would precede it, since G bought exactly one fit); (C) a
   matched F(C) versus F(M) comparison as the next object (new card, a C fit and an M fit with
   panels on common worlds); (D) a development object training M through the fixed law
   (the M-side analogue of FIXED_F_TRAINING_USE). DM recommendation: (B): it is the cheapest
   discriminator of instance variability, which is the alternative that blocks 1 and 2 showed to
   be real for this family, and (C) or (D) are premature before it. This is a direction-tier
   question and is sent to `em:acvc:convergence`; until its answer ACVC stays
   ACTIVE/MEDIUM/recasts2 in its slot, ACTIVE-idle with no producer.
4. **Direction/Portfolio** — no local disposition; no capacity writer held; no peer change.

Predictions: DM card forecast T_F TRANSFERS .40 / WITHIN .30 / ADVERSE .30 realized TRANSFERS
(Brier .54, modal category occurred); T_D UP .30 / WITHIN .35 / DOWN .35 realized WITHIN_MEI
(Brier .635). Owner prediction not taken; canonical reviews checked ("no unapplied owner
instructions"). Ledger row 32 in `docs/research/portfolio/audit/2026-09-15.md`; the grant's
owner item `20260915-acvc-005` is the accepted surface; no separate ordinary-result item.
[Chinese owner brief](../../portfolio/owner/briefs/acvc/2026-09-15_ACVC_M_DEPLOYMENT_TRANSFER_B01.md).

## Preservation, boundary and revisit

The original nine-file set is preserved: the non-checkpoint, non-log files and the task log are
committed under `evidence/m_deployment_transfer_b01_20260915/`, and the complete set including
`final.pt`, `stdout.log` and `stderr.log` is retained in the local archive listed in
`PRESERVATION.json`; the reduce output, world differences and prediction scores are committed
beside them. Remote worktree `/home/wu/hmasd-worktrees/acvc-transfer-b01-a741758a1` and staging
`/home/wu/hmasd-inputs/acvc-transfer-b01-28531` are reclaimed after the push (CLEANUP.json). No
experiment or transport effect is pending for ACVC other than the direction-tier question above.
Revisit condition: the Convergence answer, or an owner instruction.
