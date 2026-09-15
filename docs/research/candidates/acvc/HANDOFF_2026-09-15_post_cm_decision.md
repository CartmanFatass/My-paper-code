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

`7bd04236d` (block-2 wrapper + tests). Earlier session commits `897880496`,
`c3ce56bf2`, `f4c2475da`, `a4cb8e8b0` (Pro), `c14180e9c` are on `main`.

## Pending and blocked

- **Portfolio grant for the two new fits** (about 3,400 s planned native; C
  1,800 s, M 1,600 s). Not yet requested: the shared Portfolio binding
  `portfolio:cross_direction` rests at `DIRECTION_VERIFIED` for the FSD request
  because the Codex-side `archive_delivered_claude_request.py` fails with
  `KeyError: 'direction_id'` on records that carry only `direction_ids` (same
  for `em:acvc:convergence`). The hub does not edit Codex scripts or the shared
  registry without owner approval. **Owner decision needed:** approve a manual
  registry reconciliation (or a script fix by Codex Root) so the next Portfolio
  Send can be bound.
- Remote staging of the pinned on-policy source (sha `de66d7a4b`, archive
  sha256 `0f151fea…`) must be re-created before an M fit; the previous copy was
  reclaimed (DEPENDENCY.json / STAGING.json in the B01 evidence folder record
  the exact procedure).
- Opus review of the wrapper before launch (RNG identity binding).
- `DIRECTION.md` addendum for the selected object at the next clean boundary.

## First resume step

Once the Portfolio key is unblocked: author the one-block investment request
(REQUEST.json under `docs/research/portfolio/pro_packets/20260915_acvc_one_block_replication_investment/`,
issue #14 or #22 as the delivery issue, references: the direction INTAKE.md,
RESPONSE.md, B01 E0/intake), render/bind/dispatch; on a grant, stage on-policy,
Opus-review the wrapper, launch C then M through `hmasd-experiment-operator`
with `launch.sh`-equivalent commands (`--seed 28431`), collect, reduce with
`--mode reduce`, intake with the fixed accumulation rule.
