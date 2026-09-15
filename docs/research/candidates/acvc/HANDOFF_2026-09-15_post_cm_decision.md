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

- **Portfolio grant for the two new fits** (about 3,400 s planned native; C
  1,800 s, M 1,600 s). **Requested and sent** 2026-09-15 13:10Z: packet
  `docs/research/portfolio/pro_packets/20260915_acvc_one_block_replication_investment/`
  (task `84ba08ad0`, bound handoff `5846a1dab`, request id
  `2026-09-15-acvc-one-block-replication-investment-01`, key
  `portfolio:cross_direction`, conversation `6a9c109e-b264-83e8-a78b-f9ea1b767b7b`,
  Issue #14, response path `.../archive/RESPONSE.md` on `codex/acvc`). One Send
  (operation `25b6008b-940a-4be2-95c9-2b072719163b`, user message
  `768efae5-…`); the registry blocker was cleared by the owner-approved
  reconciliation at 05:43 PDT. Phase 2 (observe, archive, registry, tab close)
  runs when the response lands on GitHub; intake follows.
- Remote staging of the pinned on-policy source (sha `de66d7a4b`, archive
  sha256 `0f151fea…`) must be re-created before an M fit; the previous copy was
  reclaimed (DEPENDENCY.json / STAGING.json in the B01 evidence folder record
  the exact procedure).
- ~~Opus review of the wrapper before launch~~ done 2026-09-15 (ACCEPT_WITH_CORRECTIONS,
  applied at `3ae041d9e`: guards removed, trailing `--seed` guarded, collision span 50,000,
  `launch_b02.sh` added; the reviewer verified every seed consumer reads the rebound
  identities and that the 64 evaluation worlds are shared by C and M and disjoint from
  block 1). Remaining pre-launch items from the review: run `--mode reduce` through the
  b02 wrapper, compute the two-block pooled summary at intake by hand with provenance,
  and note that `CARD` points at the intake document.
- `DIRECTION.md` addendum for the selected object at the next clean boundary.

## First resume step

Check the GitHub readback for the grant response (`codex/acvc` head, the response
path above, Issue #14 comments). When present: transport phase 2, then intake
(`PRO_FINAL / OWNER_DELEGATED`, decision record, ledger row, P1 portfolio item
trace). On a grant: re-create the on-policy staging (sha `de66d7a4b`, archive
sha256 `0f151fea…`, DEPENDENCY.json / STAGING.json procedure), launch C then M
through `hmasd-experiment-operator` with `launch_b02.sh`-form commands
(`--seed 28431`), collect, reduce with `--mode reduce` through the b02 wrapper,
intake with the fixed two-block accumulation rule and the pooled summary by hand
with provenance. On a refusal: record it, `DIRECTION.md` addendum, ACVC
ACTIVE-idle with the missing fact named.
