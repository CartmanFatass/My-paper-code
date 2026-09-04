# Research handoff — 2026-09-03 (Claude session to Codex)

Written by the Claude reviewer session (`session_015hGLzLCuJLFFtZTboKg2bd`) at the owner's
instruction of 20:14 PDT: finish the workflow changes, write this handoff, let the two running
implementers finish and add their parts, then pause research. This file is the entry point for a
Codex session resuming the work. Sections marked *pending* are filled when the named implementer
reports.

> **Current-status overlay (owner, 2026-09-04).** The owner lifted the handoff pause and directed
> automatic research to resume. The repository now has no fixed research-concurrency cap, Direction
> Managers run at `gpt-5.6-sol` / `max`, and every Pro handoff creates an on-demand Transport
> operator whose single receipt returns to its creator `source_thread_id`. Root `AGENTS.md`,
> `PORTFOLIO.md`, and `decisions/2026-09-04-dm-max-and-unbounded-research-capacity.md` are the current
> control plane. Statements below about the old pause, two-direction cap, deleted Claude heartbeat,
> or fixed receipt routing describe the historical handoff state only.

## 1. Read in this order

1. `AGENTS.md` on `main` (merged 2026-09-03 20:26 PDT as `824b499aa`; §3 below). It carries
   the decision ladder, the blocker rule, unattended operation with the audit ledger, capacity,
   Git under concurrent sessions, and the integrity rules including the 2026-09-02 telemetry rule.
2. `docs/project/ENGINEERING_SCOPE_SPEC.md`: two tiers, the default-prohibited
   machinery list, budgets. Confirmed by the owner 2026-09-03.
3. `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md` §11.
4. `docs/research/portfolio/PORTFOLIO.md` rows for the six live directions, then the intake
   record `docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md` (Parts C–F) and
   `docs/Claude_docs/reviews/ADR_01_02_ADVERSARIAL_REVIEW_20260902.md` (Parts IX–XII) for every
   decision taken since the calibration, each with its options and provenance line.
5. The nested `AGENTS.md` files (`experiments/`, `tests/`, `scripts/`, `envs/`,
   `ha_ctse_process/`, `docs/`), and
   `docs/Claude_docs/plans/CODEBASE_LAYOUT_STANDARD_20260903.md` with the owner's answers in
   `docs/research/portfolio/decisions/2026-09-03-control-plane-revision.md`.

## 2. Standing owner instructions at the handoff

- Historical capacity at the handoff: two implementer sessions and two result-bearing runs at a
  time (13:33 PDT). Superseded by the 2026-09-04 unbounded-capacity decision cited above.
- Unattended delegation (13:58 PDT, `decisions/2026-09-03-unattended-delegation.md`): at every
  object-tier decision list options and a recommendation, select the recommended one, record
  `Owner-delegated decision (unattended, 2026-09-03 instruction): (x)`. Portfolio-tier decisions,
  frozen scientific meaning, and irreversible actions are excluded.
- Historical pause: research was to pause after the two running implementers finished (20:14 PDT).
  The owner lifted this pause on 2026-09-04; the queued objects in §4 may now advance subject to the
  current decision ladder and resource admission.
- Direction Pro nodes decide direction-tier questions. The persistent Portfolio Pro node produces
  a Portfolio proposal, and the owner ratifies it before any Portfolio action takes effect.
  Object-tier decisions stay local for latency and follow the unattended delegation.

## 3. Control plane: state at handoff

Merged on `main`:
- `ac5cd664e` the owner's 09-03 09:57 edits (outsource → `spawn_agent`; transport receipt to the
  then-current return session; CM/DM effort `high`; routine implementer Luna/max) with the
  prompt-author wording aligned and four transport tests rewritten (`tests/skills`: 76 passed).
  The routing and DM-effort portions are superseded by the current-status overlay above.
- `502896633` third-party skills to `.agents/third_party/`; empty authority directories and
  `.codex/runtime/` removed; external-review README pointer fixed.
- Records: `decisions/2026-09-03-control-plane-revision.md`, review
  `docs/Claude_docs/reviews/CODEX_CONTROL_PLANE_REVIEW_20260903.md` §1–§11, inventory
  `docs/Claude_docs/reviews/CODEBASE_INVENTORY_20260903.md`.

- `824b499aa` merge of `control-plane-revision-20260903` (owner instruction 20:22 PDT; the
  worktree `.claude/worktrees/control-plane-20260903` can be removed): `4ca97fd61` runtime-neutral
  `AGENTS.md`; DM absorbs EM; CM performance gate → two recorded lines; seven definitions retired
  (`em`, `research-innovator`, `research-principles-analyst`, `research-scout`,
  `workflow-designer`, `design-reviewer`, `general-leaf`); `config.toml` at nine registrations;
  portfolio skill parks on a blocker; prompt author names the DM as the `em` caller.
  `9bcc5ce5d` `ENGINEERING_SCOPE_SPEC.md`; nested `AGENTS.md` × 6 with one-line `CLAUDE.md`
  imports; root `CLAUDE.md` thinned; `PROJECT_MAP.md` one-page index; `RESEARCH_MAP.md`
  script-prefix column; `pytest.ini`; scope self-check in CM, implementers, reviewer, critic, DM
  and the outsource template; `scope:` commit trailer rule; `.gitignore` rewrite (visible by
  default; run output anchored at the root). `656bdffea` keeps
  `max_concurrent_threads_per_session = 40`: at the handoff the two-direction cap was a Root/DM
  policy rather than a thread limit. That research cap is now superseded; the runtime thread limit
  remains an implementation constraint because a DM → CM → implementer chain needs several
  threads.
- `f368aedb5` recorded the then-current two-number capacity line in `PORTFOLIO.md`, with pointers to
  the scope spec and audit ledger. The capacity line is now `UNBOUNDED` at the repository-policy
  layer. `docs/research/portfolio/audit/` is created on the first delegated decision.
- Housekeeping (Opus agent, reported 21:04 PDT): `fd0cb36e6` seven analysis scripts →
  `tools/analysis/` (six left in `scripts/` because a frozen document or a candidate cites them
  by path; 55 tests pass); `a1ce91797` user-profile interpreter paths removed from six scripts
  (the UCOPE certificate runner's `FROZEN_PYTHON_EXECUTABLE` and the VNFC R02 runner are kept
  because a test and a byte manifest pin them). Not committed: three empty directories and 46
  `__pycache__` removed; scratch reduced (`temp/` top level 1,158 → 912; `.scratch/`,
  `.pytest_cache/`, the four non-direction `temp/directions/` buckets, the backup toml removed;
  `temp/directions/crto/` kept because two CRTO evidence documents cite it); 22 root
  `.tmp_pytest_b1_*`, `.pytest_tmp`, and 20 `.tmp/cm_scdmp_*`/`vnfc_*` entries are locked by
  ACLs set by confinement tests and need an elevated shell; six merged worktrees removed (two
  untracked, superseded files discarded from `ucope-engineering-s2c1`); 30 branches deleted
  after tag `archive/branches-20260903` (pushed; every deleted tip reachable from it), 18 local
  branches remain; nine unmerged sibling worktrees under `C:/Projects/HMASD-worktrees/` and
  `C:/Projects/HMASD-app-server-availability-runtime` are listed in the agent report for the
  owner. `git gc --prune=now` was not run.
- Personal notes (`CONCEPT_MAP.md`, `LEARNING_LOG.md`, the 2026-08-26 tutoring summary) moved
  to `docs/personal/` (ignored).

## 4. Research: state per direction

| Direction | State at handoff | Next recorded at handoff |
| --- | --- | --- |
| flexible_skill_duration | E2 interruption-cost sweep running detached on branch `worktree-agent-a88287f2315bb99a0` (launch sha `92243f413`; branch tip `8329f4e4a`, pushed, declares the study's two §4 items: the two-slot launch queue with a JSON state file and the `wait_for_pids` liveness probe, both instruction-named). 15-run plan after the `k = 1` arm was dropped (XII.6), re-projected 10.3 h (XII.7). **Sweep complete: 15 of 15** summaries at 07:24Z (last run `d2_c2p0` seed 2); no run failed; the queue has exited. Seed-1 D0 ordering so far matches the exact references; `d0_k5` across-seed range 3.1e-5 against `d0_k40`'s 0.086. The implementer was stopped by the session limit at 21:04 PDT; queue state and per-run summaries are in the study root (§5). Result document and Part XIII intake **not written** | Codex: when 15 summaries exist, write the E2 result document from the study root in the E0 format (rule from the E2 card applied verbatim; the §5 return test with `s` from the D2 arm's own across-seed range), intake it, merge the branch, then decide E2b/E3 (per-arm cost projection rule, `AGENTS.md` §5) |
| capability_bound_semantic_currentness | B1 attempts r01–r05 all refused by orchestration guards or, for r05, a memory-admission floor crossed at the replay phase (E.6–E.12); guard repairs `2e5bc4695`, `09acf0539`, `0b629eff4`, `4679e8dc8`. E.8 item 3 follow-up committed as `81dfbd72e` (E.13): four more formal-path defects repaired with ten pinning tests, preflight refusal reasons surfaced, offline coverage of the whole publication path; `84 passed, 1 deselected`. Unfinished: the unified end-to-end profile is red at `test_b1_metrics_production.py:699`; incident-root path budget drafted only; **defect 8** (durable cap 512 MiB versus a 685 MiB formal artifact) held for the owner with three options and a recommendation in E.13. Working tree clean for CBSC paths | Owner decision on defect 8 → unified profile green (short `--basetemp`) → `b1_scout_r06` at that sha, detached, short incident root (E.11 decision (b)). Do not launch r06 before the cap decision; it would stop after ~40 min of replay. The object is unconsumed |
| ucope | paid-acquisition B object answered PA-B (D.24); chain paused by the owner (D.25) | three-witness hinge object (card first) |
| variable_n_fleet_churn | R02 consumed: `INSTABILITY/HETEROGENEITY`, BCRH not beaten (F.5) | controller-headroom A/RECON object (card first, F.6) |
| semigroup_consistent_duration_model_policy | B01 line stopped with the base run and the graded diagnostic (C.6); k-split survival is an E4 design input for FSD | D6 recast, no object yet |
| finite_resource_relational_inductive_efficiency | §11 recast not yet executed (three untracked `b01/` files and their tests exist in the working tree, unreviewed) | one-seed 128-update smoke on the Slice-B trainer, then three seeds |

Owner items still open (not delegated): CBSC defect 8, the durable artifact cap (E.13; the
reviewer recommends publishing a `summary.json` and dropping the raw dump below the cap); the
replay-phase admission semantics (E.12 item 2: a bounded wait-and-retry before a phase's
admissions would change "immediately before each invocation"); a Git LFS or size rule for tracked
`RESULT.json` evidence (377 MiB).

## 5. Runtime facts a resuming session needs

- Interpreter `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`; preflight before every
  result-bearing run; `--basetemp` under `temp/directions/<id>/test/`.
- Git: several sessions commit to `main`; stage by path, commit by pathspec, never `git add -A`,
  stash or reset; push immediately; on this host push outside the Codex sandbox.
- Machine: 29.8 GiB RAM; two E2 runs take about 2.5 GB each; the 4 GiB floor is crossed when a
  third result-bearing process joins them (E.11).
- The Claude session's heartbeat cron (`23,53 * * * *`, job `bb7c8b33`) was deleted when the pause
  began. It is superseded by the active Codex heartbeat `hmasd-research-loop`, which resumes the
  creator Root task every 30 minutes.
- E2 monitor: `bw9qgennf` reports each completed run; study root
  `.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E2_20260903/`.

## 6. Open at the historical pause (2026-09-03 23:58 PDT)

- E2 sweep complete (15 of 15, 07:24Z) → result document, Part XIII intake, merge → §4 row. Not started.
- Layout standard items not yet applied (owner-approved, `decisions/2026-09-03-control-plane-revision.md`):
  `docs/` consolidation into `docs/archive/` (`new/`, `new-libs/` including its 96 untracked corpus
  files, `report/`, `superpowers/`, `benchmarks/`, `operations/`, `agents/`, empty `plans/`,
  `migration/`); `logs/` → `docs/archive/logs/`; `.claude/settings.json` and `.claude/agents/`
  tracked when they exist; `git gc --prune=now`; the ACL-locked scratch entries (§3) from an
  elevated shell.
- Untracked owner work left uncommitted on purpose: FRRIE `b01/{b4_induction_pilot,training_runner,training_shards}.py`
  with their three tests, modified FRRIE `b01/{checkpoint,trainer}.py` and `test_checkpoint.py`,
  and `tests/skills/hmasd_workflow_outsource_test.py`.
- `.codex/config.toml` re-check against the Codex version in use.
