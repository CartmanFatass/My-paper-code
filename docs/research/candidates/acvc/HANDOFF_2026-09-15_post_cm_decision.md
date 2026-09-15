# ACVC handoff — after the em:acvc:convergence decision (2026-09-15, Claude hub)

**State: ACTIVE / MEDIUM / recasts 2, lowest sequencing; B02 granted (G2) and launched: one live
producer, handle `acvc-transfer-m-b02-28631-c006c0b24`; nothing else authorised.** Driven by
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

## Block 2 complete and family concluded (2026-09-15 17:10Z)

Both granted fits finished, were collected, reduced and intaken (D2 = F−M −.03919 J,
M_ABOVE_MEI; F−C and F−own-dwell UP in both blocks; pooled F−M −.0079 J, df = 1 interval
[−.406, +.390]). `em:acvc:convergence` answered the post-block-2 question at 17:08Z with **A**
(`PRO_FINAL`, [intake](pro_packets/20260915_post_block2_convergence/INTAKE.md)): the C/M
family is concluded at its bounded two-block claim (internal deployment-package usefulness
recurred; competitive advantage unresolved). Reporting corrections applied to the E0 and
intake. Remote worktree and staging reclaimed (CLEANUP.json); checkpoints retained locally
(PRESERVATION.json). The evidence-spec copy on `codex/acvc` was synced to main.

## M-deployment transfer object selected (2026-09-15 20:28Z)

Under the owner's 12:57 PDT scope instruction the hub derived the unlisted candidate into
[ACVC_M_DEPLOYMENT_TRANSFER_B01](ACVC_M_DEPLOYMENT_TRANSFER_B01_PROSPECTIVE_CARD_20260915.md)
and `em:acvc:convergence` selected it with corrections (**B**, `PRO_FINAL`,
[intake](pro_packets/20260915_m_deployment_transfer_convergence/INTAKE.md), response commit
`71a1ca5b7`): one fresh M fit, panels M / F(M) / own-dwell(M), T_F at .01 J, labels
28531/38531. **Launch waits for a bounded Portfolio investment decision** (one fit, about
2,600 s native plan); the L0 (runner ≤ 300 lines, wrapped evaluator, focused tests under the
card §5 and §7 acceptance groups) is engineering work that proceeds meanwhile with independent
Opus review.

## B02 granted, L0 accepted, fit launched (2026-09-15 22:35Z)

- Portfolio answered at `codex/acvc 47021a400` (22:20Z; one Send 22:13Z, COMPLETE, ARCHIVED,
  tab closed; Issue 14 comment `5688893524`): **G2**, `PRO_FINAL / OWNER_DELEGATED`
  ([decision](../../portfolio/decisions/2026-09-15-acvc-m-deployment-transfer-b02-grant.md),
  [intake](../../portfolio/pro_packets/20260915_acvc_m_deployment_transfer_b02_investment/INTAKE.md),
  ledger row 34, owner item `20260915-acvc-007`).
- L0 at `codex/acvc 6a3967065` (thin B02 entry, launch script, five binding tests); `hmasd-reviewer`
  accept, no material finding; 16 tests green on the node at the launch sha
  `c006c0b2453a44902ebfda827099823a28e136f1` (ledger row 35). On-policy re-staged at
  `/home/wu/hmasd-inputs/acvc-transfer-b02-28631/on-policy` (DEPENDENCY.json); remote worktree
  `/home/wu/hmasd-worktrees/acvc-transfer-b02-c006c0b24` (fetched by full sha).
- **Live handle `acvc-transfer-m-b02-28631-c006c0b24`**: launched 2026-09-15T22:34:13Z through hmasd-experiment-operator, remote pid 3754217, admission passed at 22:34:25Z (15,613,599,744 B physical and effective available, floor 4 GiB), running at uptime 15 s with tmux active, stderr.log 0 bytes, stdout advancing (rollout 48 after 23.06 s process wall), expected end about 22:54Z
  Record: `evidence/m_deployment_transfer_b02_20260915/EXECUTION.md`. Plan about 1,200 s, not a cap.
  Output root `<W>/temp/directions/acvc/exp/m_deployment_transfer_b02_28631`.

## First resume step (current)

Observe the handle (`agent-task status acvc-transfer-m-b02-28631-c006c0b24`; never run/stop/attach).
When finished: collect `native/` (summary.json, episodes.jsonl, updates.jsonl, admission.json,
native_time.txt, task.log as .txt) with digests as for B01, run `--mode reduce` through
`scripts/run_acvc_m_deployment_transfer_b02.py`, write WORLD_DIFFERENCES.json (never .csv), the
E0 with the card-fixed reading (T_F,2 primary; read alone first, then the two instances side by
side with their own uncertainties; no pooled verdict), intake, Chinese brief, PREDICTIONS.json
(card §3 forecasts), preservation archive under
`temp/directions/acvc/retained/m_deployment_transfer_b02_20260915/`, then reclaim the remote
worktree, staging and task record (CLEANUP.json). The object ends after this one original; a
further object is a direction-tier question for `em:acvc:convergence`. FSD-side work is unaffected.

## Result review intaken and B02 investment question sent (2026-09-15 22:10Z)

- `em:acvc:convergence` answered the result review at `codex/acvc 1fb3d9e14` (21:57Z; one
  Send at 21:46Z, receipt COMPLETE, registry ARCHIVED, tab closed; facts under
  `temp/sessions/hmasd-chatgpt-pro-transport/archive/acvc/2026-09-15-acvc-m-deployment-transfer-result-review-01/`).
  **B, `PRO_FINAL`**: one further independently initialised M fit,
  [ACVC_M_DEPLOYMENT_TRANSFER_B02](ACVC_M_DEPLOYMENT_TRANSFER_B02_PROSPECTIVE_CARD_20260915.md)
  (MASTER 28631 / namespace 38631, same three panels, T_F,2 primary, per-instance display
  beside B01, no pooled verdict, end after one). Intake
  [pro_packets/20260915_m_deployment_transfer_result_review/INTAKE.md](pro_packets/20260915_m_deployment_transfer_result_review/INTAKE.md);
  ledger row 33; owner item `20260915-acvc-006`. B01's E0, intake and `DIRECTION.md` carry
  the node's three narrative corrections (U a complete package contrast; T_F variability not
  inherited from the .044 J block dispersion; M score ordering descriptive only). Commit
  `74d49807b` (main `6d00be0e8`).
- The one-fit B02 investment question is with `portfolio:cross_direction`: packet
  `docs/research/portfolio/pro_packets/20260915_acvc_m_deployment_transfer_b02_investment/`
  (request `2026-09-15-acvc-m-deployment-transfer-b02-investment-01`, TASK `92c5957c7`, bound
  HANDOFF `4ebfad9df`, references at `74d49807b` / main `3580587ac`, conversation
  `6a9c109e-b264-83e8-a78b-f9ea1b767b7b`). Transport: one Send at 22:13:13Z (first call errored review_user_message_not_observed_after_click with persisted sendAttempted=true; the identical verifyExisting observation confirmed the single send, user message 721f8b05-4e0f-4a28-a556-d778056ebfc6, operation 5b50fcbb-a76b-4427-b9b4-02bb6fd65252), matched labels Latest / Pro, tab fee2561b-aa1e-43aa-905d-44dc1a80dd76 open for phase 2, prompt sha256 9ca41561260fdaa363fe5018dad2fe6fd13a7ced3fc4527d980c23fe5b1d9728; the registry binding's history lists the one-block replication round as its last request (the transfer-investment round has an archive folder but no history row), state ARCHIVED before this send.
- No producer, no launch. Engineering that may proceed meanwhile at zero exposure: the B02
  binding change (new identities bound before any recipe import, delegating to the B01 runner,
  wrapped evaluator and reducer at `a741758a1`) with one focused binding test and independent
  review of the changed behaviour.

## First resume step as written at 22:10Z (superseded 22:35Z by the section above)

Wait for the archived Portfolio answer to the B02 investment request (GitHub readback of the
response path above at a fresh `codex/acvc` head; then transport phase 2: COMPLETE receipt,
archive, `bind_conversation.py --direction-id portfolio --direction-ids-json '["acvc"]'`,
registry to ARCHIVED, tab close). Intake it as `PRO_FINAL / OWNER_DELEGATED` with a decision
record under `docs/research/portfolio/decisions/` and a P1 `portfolio` owner item. If G2:
implement the B02 binding change and focused test, independent review, technical acceptance,
fresh admission and launch through `hmasd-experiment-operator` only (plan about 1,200 s). If N:
ACVC is ACTIVE-idle with the selected successor on record. No launch before a conforming grant
and technical acceptance. FSD-side work is unaffected.

## Transfer fit complete and intaken: TRANSFERS on one instance (2026-09-15 21:45Z)

- Handle `acvc-transfer-m-b01-28531-a741758a` finished exit 0/0 at about 21:26Z (native wall
  985.12 s, peak RSS 585,028 KiB; the node was idle, the 2,500 s projection came from a contended
  block-2 wall). Every count as granted; digests byte-identical; collection, reduce, world
  differences, prediction scores and preservation under
  `evidence/m_deployment_transfer_b01_20260915/` (retained archive with `final.pt` and logs at
  `C:/Projects/HMASD-worktrees/codex-acvc/temp/directions/acvc/retained/m_deployment_transfer_b01_20260915/M_original.tar.gz`).
- Reading: T_F +.018338 J **TRANSFERS** (53/64), T_D +.00907 WITHIN_MEI, U +.00927 WITHIN_MEI;
  [E0](ACVC_M_DEPLOYMENT_TRANSFER_B01_RESULT_EVIDENCE_20260915.md),
  [intake](ACVC_M_DEPLOYMENT_TRANSFER_B01_INTAKE_20260915.md), ledger row 32,
  [brief](../../portfolio/owner/briefs/acvc/2026-09-15_ACVC_M_DEPLOYMENT_TRANSFER_B01.md).
- The grant is consumed. Next: the direction-tier result review to `em:acvc:convergence`
  (options A/B/C/D in the intake, DM recommends B: one further independent M instance, which
  would need a Portfolio investment question). Remote worktree and staging reclaimed after the
  push (CLEANUP.json in the evidence folder).

## First resume step as written at 21:45Z (superseded 22:10Z by the section above)

If the result-review request to `em:acvc:convergence` has been sent (see the packet folder
`pro_packets/20260915_m_deployment_transfer_result_review/` and the transport registry), wait for
the archived response and intake it (`PRO_FINAL`); a Portfolio investment question follows only if
the node selects a new fit. If it has not been sent, author it from the intake's continuation
section. No launch is authorized. FSD-side work is unaffected.

## Portfolio grant G, L0 reviewed, fit launched (2026-09-15 21:09Z)

- `portfolio:cross_direction` granted the one fit at 20:51Z (`PRO_FINAL / OWNER_DELEGATED`,
  [decision](../../portfolio/decisions/2026-09-15-acvc-m-deployment-transfer-grant.md),
  [intake](../../portfolio/pro_packets/20260915_acvc_m_deployment_transfer_investment/INTAKE.md),
  ledger row 30, owner item `20260915-acvc-005`). Transport: one Send, receipt COMPLETE,
  registry ARCHIVED, tab closed (facts under
  `temp/sessions/hmasd-chatgpt-pro-transport/archive/portfolio/2026-09-15-acvc-m-deployment-transfer-investment-01/`).
- L0 committed at `codex/acvc fb7f859d9` (main `95c2290a0`); independent `hmasd-reviewer`
  accepted after fixes; corrections at `a741758a1` (main `deb0eb357`), eleven tests green;
  ledger row 31 (technical acceptance).
- On-policy re-staged at `/home/wu/hmasd-inputs/acvc-transfer-b01-28531/on-policy`
  (`evidence/m_deployment_transfer_b01_20260915/DEPENDENCY.json`); remote worktree
  `/home/wu/hmasd-worktrees/acvc-transfer-b01-a741758a1` (fetched by sha: the node's stale
  remote-tracking ref `origin/codex/acvc/next-object-20260904` blocks fetching the branch ref).
- **Live handle `acvc-transfer-m-b01-28531-a741758a`** (pid 3745266, launched 21:09:14Z,
  admission passed at 15,621,808,128 B, expected end about 21:52Z), output root
  `<worktree>/temp/directions/acvc/exp/m_deployment_transfer_b01_28531`;
  [EXECUTION.md](evidence/m_deployment_transfer_b01_20260915/EXECUTION.md) has the cost
  projection and command form.

## First resume step as written at launch (superseded 21:45Z by the section above)

Check `agent-task status acvc-transfer-m-b01-28531-a741758a`. When finished with exit 0:
collect `summary.json`, `episodes.jsonl`, `updates.jsonl`, `admission.json`, `native_time.txt`,
`stdout.log`, `stderr.log`, `final.pt` (retain locally, preserve digests) into
`evidence/m_deployment_transfer_b01_20260915/native/`, run
`scripts/run_acvc_m_deployment_transfer_b01.py --mode reduce --m-summary <summary.json> --output <dir>`,
write the E0 with T_F / T_D / U and the counters, score the hub predictions (T_F .40/.30/.30,
T_D .30/.35/.35), intake, Chinese brief, ledger row, then reclaim the remote worktree and
staging with a CLEANUP.json and send the result review to `em:acvc:convergence`. A non-zero
exit or an incomplete panel is quarantined and reported; no retry is authorized.

## State at the previous boundary (20:28Z): ACTIVE, transfer object selected, no producer

Pending: the Portfolio investment question (to author and send on `portfolio:cross_direction`)
and the L0 implementation. No live handle, no unresolved transport effect. Reopening condition (Pro):
new compatible evidence or a concrete changed use that makes the comparative choice
consequential, for example a decision to develop the fixed transformation on an M-trained
proposer (Pro's best unlisted candidate: one fresh M fit with M / F(M) / own-dwell(M) panels).
Lifecycle ACTIVE/MEDIUM/recasts2 and the occupied slot are unchanged; only a Portfolio or owner
disposition changes them.

## First resume step

Read this handoff, `DIRECTION.md` (top section), the corrected card (§7) and the transfer
intake. (1) If the Portfolio investment question has not been sent, author it
(`docs/research/portfolio/pro_packets/20260915_acvc_m_deployment_transfer_investment/`, one
fit, references at a main commit) and send it through `hmasd-pro-transport`. (2) Implement
the L0 on `codex/acvc` (`scripts/run_acvc_m_deployment_transfer_b01.py`,
`experiments/candidates/acvc/m_deployment_transfer_b01/wrapped_eval.py`, focused tests), get
independent Opus review, record the per-fit cost projection. (3) Launch only after a
conforming Portfolio decision and technical acceptance, via `hmasd-experiment-operator` on
the WSL node with fresh admission. Nothing to launch before that.
