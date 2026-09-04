# Research handoff — 2026-09-03 (Claude session to Codex)

Written by the Claude reviewer session (`session_015hGLzLCuJLFFtZTboKg2bd`) at the owner's
instruction of 20:14 PDT: finish the workflow changes, write this handoff, let the two running
implementers finish and add their parts, then pause research. This file is the entry point for a
Codex session resuming the work. Sections marked *pending* are filled when the named implementer
reports.

## 1. Read in this order

1. `AGENTS.md` on branch `control-plane-revision-20260903` (not yet merged; §3 below). It carries
   the decision ladder, the blocker rule, unattended operation with the audit ledger, capacity,
   Git under concurrent sessions, and the integrity rules including the 2026-09-02 telemetry rule.
2. `docs/project/ENGINEERING_SCOPE_SPEC.md` (same branch): two tiers, the default-prohibited
   machinery list, budgets. Confirmed by the owner 2026-09-03.
3. `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` §11.
4. `docs/research/portfolio/PORTFOLIO.md` rows for the six live directions, then the intake
   record `docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` (Parts C–F) and
   `docs/Claude_docs/reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md` (Parts IX–XII) for every
   decision taken since the calibration, each with its options and provenance line.
5. The nested `AGENTS.md` files (`experiments/`, `tests/`, `scripts/`, `envs/`,
   `ha_ctse_process/`, `docs/`) on the same branch, and
   `docs/Claude_docs/plans/CODEBASE_LAYOUT_STANDARD_20260903.md` with the owner's answers in
   `docs/research/portfolio/decisions/2026-09-03-control-plane-revision.md`.

## 2. Standing owner instructions in force

- Two implementer sessions and two result-bearing runs at a time (13:33 PDT).
- Unattended delegation (13:58 PDT, `decisions/2026-09-03-unattended-delegation.md`): at every
  object-tier decision list options and a recommendation, select the recommended one, record
  `Owner-delegated decision (unattended, 2026-09-03 instruction): (x)`. Portfolio-tier decisions,
  frozen scientific meaning, and irreversible actions are excluded.
- Research is **paused** after the two running implementers finish (20:14 PDT). Do not start the
  queued objects in §4 until the owner lifts the pause.
- Pro nodes are the decider at the direction and portfolio tiers when Codex drives (owner
  clarification 18:07 and 18:12 PDT, review §9–10): Pro performs better and runs on an
  independent quota; object-tier decisions stay local for latency.

## 3. Control plane: state at handoff

Merged on `main`:
- `ac5cd664e` the owner's 09-03 09:57 edits (outsource → `spawn_agent`; transport receipt to the
  fixed return session; CM/DM effort `high`; routine implementer Luna/max) with the prompt-author
  wording aligned and four transport tests rewritten (`tests/skills`: 76 passed).
- `502896633` third-party skills to `.agents/third_party/`; empty authority directories and
  `.codex/runtime/` removed; external-review README pointer fixed.
- Records: `decisions/2026-09-03-control-plane-revision.md`, review
  `docs/Claude_docs/reviews/CODEX_CONTROL_PLANE_REVIEW_20260903.md` §1–§11, inventory
  `docs/Claude_docs/reviews/CODEBASE_INVENTORY_20260903.md`.

On branch `control-plane-revision-20260903` (worktree `.claude/worktrees/control-plane-20260903`,
pushed, **awaiting the owner's review and merge**):
- `4ca97fd61` runtime-neutral `AGENTS.md`; DM absorbs EM; CM performance gate → two recorded
  lines; seven definitions retired (`em`, `research-innovator`, `research-principles-analyst`,
  `research-scout`, `workflow-designer`, `design-reviewer`, `general-leaf`); `config.toml` at nine
  registrations and `max_concurrent_threads_per_session = 2`; portfolio skill parks on a blocker;
  prompt author names the DM as the `em` caller.
- `9bcc5ce5d` `ENGINEERING_SCOPE_SPEC.md`; nested `AGENTS.md` × 6 with one-line `CLAUDE.md`
  imports; root `CLAUDE.md` thinned to environment and commands; `PROJECT_MAP.md` one-page index;
  `RESEARCH_MAP.md` script-prefix column; `pytest.ini`; scope self-check in CM, implementers,
  reviewer, critic, DM and the outsource template; `scope:` commit trailer rule.
- `.gitignore` rewrite (visible by default; run output anchored at the root) — *see §6 for the
  pending pieces*.

After merge, the following are owed on `main`: `PORTFOLIO.md` capacity line replaced by the two
numbers (`AGENTS.md` §5); `docs/research/portfolio/audit/` created on first delegated decision;
`.codex/config.toml` re-checked against the Codex version in use.

Housekeeping delegated to an Opus agent on `main` at 20:05 PDT (report *pending*): empty
directories, 13 analysis scripts → `tools/analysis/`, eight absolute interpreter paths replaced,
scratch cleanup (789 `temp/pytest*`, 31 root basetemp dirs, `.tmp/`, non-direction buckets,
backup toml), merged worktrees removed, branch prune after tag `archive/branches-20260903`.
`git gc --prune=now` is still to be run at a quiet moment (716 MiB of garbage objects).

## 4. Research: state per direction

| Direction | State at handoff | Next (held by the pause) |
| --- | --- | --- |
| flexible_skill_duration | E2 interruption-cost sweep running on branch `worktree-agent-a88287f2315bb99a0` (launch sha `92243f413`, result doc commits through `9b0b10a3a`); 15-run plan after the `k = 1` arm was dropped (XII.6), re-projected 10.3 h (XII.7); 6 of 15 evidence-bearing summaries at 03:07Z; *pending* the implementer's final result document and the reviewer's Part XIII intake | E2 result → intake → merge branch → decide E2b/E3 (cost projection rule from XII.7 applies) |
| capability_bound_semantic_currentness | B1 attempts r01–r05 all refused by orchestration guards or, for r05, a memory-admission floor crossed at the replay phase (E.6–E.12); guard repairs `2e5bc4695`, `09acf0539`, `0b629eff4`, `4679e8dc8`; the implementer is on the E.8 item 3 engineering follow-up (end-to-end profile covering the formal publication path, preflight message fix, incident path budget) — *pending* its commit sha and test line | r06 at the repaired sha when a run slot is free (E.11 decision (b)); the object is unconsumed |
| ucope | paid-acquisition B object answered PA-B (D.24); chain paused by the owner (D.25) | three-witness hinge object (card first) |
| variable_n_fleet_churn | R02 consumed: `INSTABILITY/HETEROGENEITY`, BCRH not beaten (F.5) | controller-headroom A/RECON object (card first, F.6) |
| semigroup_consistent_duration_model_policy | B01 line stopped with the base run and the graded diagnostic (C.6); k-split survival is an E4 design input for FSD | D6 recast, no object yet |
| finite_resource_relational_inductive_efficiency | §11 recast not yet executed (three untracked `b01/` files and their tests exist in the working tree, unreviewed) | one-seed 128-update smoke on the Slice-B trainer, then three seeds |

Owner items still open (not delegated): the replay-phase admission semantics (E.12 item 2: a
bounded wait-and-retry before a phase's admissions would change "immediately before each
invocation"); a Git LFS or size rule for tracked `RESULT.json` evidence (377 MiB).

## 5. Runtime facts a resuming session needs

- Interpreter `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`; preflight before every
  result-bearing run; `--basetemp` under `temp/directions/<id>/test/`.
- Git: several sessions commit to `main`; stage by path, commit by pathspec, never `git add -A`,
  stash or reset; push immediately; on this host push outside the Codex sandbox.
- Machine: 29.8 GiB RAM; two E2 runs take about 2.5 GB each; the 4 GiB floor is crossed when a
  third result-bearing process joins them (E.11).
- Heartbeat cron in the Claude session (`23,53 * * * *`, job `bb7c8b33`) resumes agents killed by
  rate limits; it is deleted when the pause begins.
- E2 monitor: `bw9qgennf` reports each completed run; study root
  `.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E2_20260903/`.

## 6. Pending at the time of writing

- Opus housekeeping agent report (§3).
- `.gitignore` commit on the branch; `docs/` consolidation into `docs/archive/` (`new/`,
  `new-libs/` including its 96 untracked corpus files, `report/`, `superpowers/`, `benchmarks/`,
  `operations/`, `agents/`, empty `plans/`, `migration/`); `logs/` → `docs/archive/logs/`; personal
  notes → `docs/personal/` (ignored); `.claude/settings.json` and `.claude/agents/` tracked when
  they exist.
- CBSC implementer report → §4 row and E.13.
- E2 completion → result document, Part XIII intake, merge → §4 row.
