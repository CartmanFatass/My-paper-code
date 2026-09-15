# ACVC handoff — after the em:acvc:convergence decision (2026-09-15, Claude hub)

**State: ACTIVE / MEDIUM / recasts 2, lowest sequencing; one direction-tier
decision intaken (`PRO_FINAL`), zero new exposure, no live producer.** Driven by
the Claude Code research hub (owner 2026-09-15 resume; two directions, ACVC and
FSD). Authoring checkout `C:/Projects/HMASD-worktrees/codex-acvc`, branch
`codex/acvc` (1,140 commits behind `main`; a merge of `main` conflicts in Codex
control-plane files and science code, so the branch is kept as is and its
commits are cherry-picked into `main` by the hub).

## What happened this session

1. Resume intake with three options and the DM recommendation (B):
   [ACVC_POST_MAPPO_RESUME_INTAKE_20260915.md](ACVC_POST_MAPPO_RESUME_INTAKE_20260915.md).
2. Direction request `2026-09-15-acvc-cluster-mappo-comparison-b01-result-review-01`
   sent through the Claude transport (Agentify, one Send, `COMPLETE`), answered at
   `a4cb8e8b0`: **option A with k = 1**, one further unchanged C/M paired block
   (C-only fit + M fit, fresh identities, D2 = mean64(J_F − J_M), MEI .01 J,
   prospective two-block accumulation). Intake:
   [pro_packets/20260915_cluster_mappo_comparison_b01_result_review/INTAKE.md](pro_packets/20260915_cluster_mappo_comparison_b01_result_review/INTAKE.md).
   DM recommendation B overruled with reasons; recorded.
3. Engineering prepared at zero exposure: `scripts/run_acvc_cluster_mappo_comparison_b02.py`
   (identities 28431/38431 bound before any recipe import; frozen constants by
   reference) and `tests/experiments/candidates/acvc/cluster_mappo_comparison_b02/test_identity.py`
   (3 passed), commit `7bd04236d` on `codex/acvc`.

## Commits on codex/acvc not on main at writing

`7bd04236d` (block-2 wrapper + tests) and `3ae041d9e` (review corrections), both on `main`. Earlier session commits `897880496`,
`c3ce56bf2`, `f4c2475da`, `a4cb8e8b0` (Pro), `c14180e9c` are on `main`.

## Pending and blocked

- **Portfolio grant for the two new fits: granted (G)** 2026-09-15 13:19Z
  (`PRO_FINAL / OWNER_DELEGATED`,
  `docs/research/portfolio/decisions/2026-09-15-acvc-one-block-replication-grant.md`,
  packet intake in `docs/research/portfolio/pro_packets/20260915_acvc_one_block_replication_investment/INTAKE.md`).
  Launch source `codex/acvc 2dc9631c8`, remote worktree `/home/wu/hmasd-worktrees/acvc-b02-2dc9631c8`.
  C fit `acvc-mappo-c-b02-28431-2dc9631c` finished exit 0 (13:26:42Z to about 14:08Z, native
  wall 2,495.72 s, peak RSS 562,308 KiB) and is collected under
  `evidence/cluster_mappo_comparison_b02_20260915/native/C/` (`C_COLLECTION.json`); M fit
  `acvc-mappo-m-b02-28431-2dc9631c` running since 16:01:41Z (pid 3736172), expected end
  about 16:45Z. No scientific reading before M completes and the wrapper reduce runs.
  Record: `evidence/cluster_mappo_comparison_b02_20260915/EXECUTION.md`.
- ~~Remote staging of the pinned on-policy source~~ re-created 2026-09-15 13:26Z at
  `/home/wu/hmasd-inputs/acvc-mappo-b02-28431/on-policy` (digest verified,
  `evidence/cluster_mappo_comparison_b02_20260915/DEPENDENCY.json`).
- ~~Opus review of the wrapper before launch~~ done 2026-09-15 (ACCEPT_WITH_CORRECTIONS,
  applied at `3ae041d9e`: guards removed, trailing `--seed` guarded, collision span 50,000,
  `launch_b02.sh` added; the reviewer verified every seed consumer reads the rebound
  identities and that the 64 evaluation worlds are shared by C and M and disjoint from
  block 1). Remaining pre-launch items from the review: run `--mode reduce` through the
  b02 wrapper, compute the two-block pooled summary at intake by hand with provenance,
  and note that `CARD` points at the intake document.
- `DIRECTION.md` addendum for the selected object at the next clean boundary.

## Block 2 complete (2026-09-15 16:55Z)

Both granted fits finished exit 0, were collected, reduced through the b02 wrapper and
intaken: D2 = F−M −.03919 J (M_ABOVE_MEI), reversing block 1; F−C and F−own-dwell UP in
both blocks; two-block pooled F−M −.0079 J with a df = 1 interval [−.406, +.390]
([E0](ACVC_CLUSTER_MAPPO_COMPARISON_B02_RESULT_EVIDENCE_20260915.md),
[intake](ACVC_CLUSTER_MAPPO_COMPARISON_B02_INTAKE_20260915.md)). The grant is consumed.

## First resume step

Send the direction-tier question to `em:acvc:convergence` (packet under
`docs/research/candidates/acvc/pro_packets/20260915_post_block2_convergence/`): close the C/M
family with the internal-usefulness reading (A), a bounded baseline-calibration design (B), or
a third unchanged block (C); DM recommends B or A. Then verify the remote cleanup
(CLEANUP.json) and hold ACVC ACTIVE-idle until the answer. No fit is authorized.
