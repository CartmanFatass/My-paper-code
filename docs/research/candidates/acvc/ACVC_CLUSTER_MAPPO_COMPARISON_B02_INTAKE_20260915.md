# Scientific intake — ACVC_CLUSTER_MAPPO_COMPARISON_B02

DM: the Claude research hub; authoring `C:/Projects/HMASD-worktrees/codex-acvc` / `codex/acvc`.
Both granted fits are complete and technically accepted, source `2dc9631c8644464b8c4189a53344b2956c3eb3b4`.
Inputs: [full E0](ACVC_CLUSTER_MAPPO_COMPARISON_B02_RESULT_EVIDENCE_20260915.md),
[machine comparison](evidence/cluster_mappo_comparison_b02_20260915/COMPARISON.json),
[two-block accumulation](evidence/cluster_mappo_comparison_b02_20260915/TWO_BLOCK_ACCUMULATION.json),
the raw collections, the unchanged block-1 card and the two Pro decisions.

## What was checked and rule applied

Direct observation: both summaries carry object B02, master 28431, namespace 38431,
`fit_complete` true, 4,096 training episodes, 2,048 rollouts, 8,192 (C) / 8,192 + 8,192 (M)
optimizer steps, 192 / 64 evaluation episodes, empty `limits`; every episode and update row
finite with 256-step episodes; parameter displacements finite; both admissions passed; both
supervisor and native exits 0; every collected file byte-identical to its remote digest. The
wrapper's `--mode reduce` judged both fits eligible and all four contrasts complete.

The card rule (F−M > +.01 F_ABOVE_MEI; inclusive ±.01 WITHIN_MEI; < −.01 M_ABOVE_MEI) applied
verbatim to D2 = **−.03919008143501977 J** gives **M_ABOVE_MEI**. Supporting: C−M
−.08668633501269826 DOWN; F−C +.0474962535776785 UP; F−own-dwell +.031713764045473436 UP.
Accumulation with block 1 (fixed equal-block rule, df = 1): pooled F−M −.007875 J, interval
[−.406, +.390]; F−C pooled +.041 J [−.040, +.122]; F−own-dwell pooled +.022 J [−.102, +.146].

## Scientific reading and limits

Inference: the second independent training instance reverses the primary sign. What recurs
across both blocks is the within-package ordering F > C and F > own-dwell; what does not recur
is F versus the untuned recurrent M recipe. This is the response's "strong F−C alongside weak
F−M" branch: internal usefulness of the deployment transformation without a competitive
advantage over the private-information MAPPO baseline. The between-block dispersion of F−M
(block SD .044 J) is four times the within-block conditional SE (.010 J), so the 64 nested
worlds never measured the relevant uncertainty; block-to-block training variability dominates.
Two blocks cannot estimate that variability with any reliability (df = 1), and the continuation
was outcome-informed, so the interval is a working-model description only.

Boundaries: direct observation versus inference as above; scientific result (M_ABOVE_MEI on
this block, package ordering) versus engineering conformance (accepted, no defect); direction-
local advice (below) versus Portfolio action (none); historical provenance (block 1 stands
unchanged, no rescoring) versus current authority (this intake). No stable superiority, safety
or default change, equivalence, tuned headroom, transfer or K/N/component attribution follows.
The untuned status of M remains the surviving alternative in both directions: block 2's M may
be an unusually good instance as block 1's may have been a weak one.

Costs: summed native wall 4,923.13 s under heavy node contention (block 1: 3,191.66 s);
plans were not caps; no stop or retry.

## Decisions this intake produces

1. **Technical/object acceptance** — options: accept the complete bounded block / quarantine
   an integrity defect / rerun. Recommend and select acceptance; every required count, reward,
   endpoint and receipt is present. Owner-delegated decision (unattended, 2026-09-03
   instruction): accept; preserve every original. No further fit is bought.
2. **Scientific conclusion** — options: report the card-fixed block-2 M_ABOVE_MEI and the
   two-block package ordering / claim a reversal proves M superiority / pool as if the
   advantage persists. Recommend and select the bounded report: the block-1 package advantage
   did not recur; F > C and F > own-dwell recurred; F versus M is unresolved and dominated by
   training-instance variability. Owner-delegated decision (unattended): (a).
3. **Continuation** — the grant ends with this intake (zero replacements or extensions). The
   next choice is direction-tier: whether the C/M comparison family is closed as unresolved at
   this budget, recast toward a calibrated (tuned or certified-competent) M reference, or
   paused as ACTIVE-idle. Options for `em:acvc:convergence`: (A) close the family, retain the
   F > C internal-usefulness reading, ACTIVE-idle; (B) one bounded baseline-calibration design
   (tuned M reference before any further package block); (C) a third unchanged block. DM
   recommendation: (B) or (A); (C) is not recommended because two blocks already show the
   between-instance variability that a third cannot resolve at df = 2. This is a direction-tier
   question and is sent to `em:acvc:convergence` as the next DM action; nothing is decided
   locally. ACVC stays ACTIVE/MEDIUM/recasts2 in its slot.
4. **Direction/Portfolio** — no local disposition; no capacity writer held; no peer change.

Predictions: DM block-2 forecast not recorded prospectively (process gap, no post hoc entry);
owner prediction not taken; canonical reviews checked, none unapplied. Ledger row in
`docs/research/portfolio/audit/2026-09-15.md`; owner item `20260915-acvc-002` traced to this
intake. [Chinese owner brief](../../portfolio/owner/briefs/acvc/2026-09-15_cluster_mappo_comparison_b02.md).

## Preservation, boundary and revisit

Both originals (nine files each) are preserved: the non-checkpoint, non-log files are
committed under `evidence/cluster_mappo_comparison_b02_20260915/native/`, and the complete
sets including `final.pt` and `task.log` (Git-ignored) are retained in local archives listed in
`PRESERVATION.json`; the reduce output, world differences and accumulation are committed
beside them. Remote worktree
`/home/wu/hmasd-worktrees/acvc-b02-2dc9631c8` and staging `/home/wu/hmasd-inputs/acvc-mappo-b02-28431`
are reclaimed after the push (CLEANUP.json). No experiment, Pro response or transport effect
is pending for ACVC after the direction-tier question above is sent. Revisit condition: the
Convergence answer, or an owner instruction.
