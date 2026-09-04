# Codebase layout standard — alignment draft

Date: 2026-09-03. Status: draft for the owner's decisions; nothing below is applied.

Basis: `docs/Claude_docs/reviews/CODEBASE_INVENTORY_20260903.md` (facts, read-only, produced by a
Sonnet agent with three forks; every count there names its command). The control-plane draft on
branch `control-plane-revision-20260903` supplies the authority text this standard plugs into.
Items are marked [DECIDE] when the owner must choose, [ASK] when a fact only the owner has decides
the answer, and (auto) when the reviewer would apply it under the standing delegation once the
owner accepts the section.

## 0. What the inventory says, in six lines

- 4,944 tracked files; `docs/` carries 377 MiB of them, almost all multi-megabyte `RESULT.json`
  evidence; `.git` holds 716 MiB of garbage objects beside 524 MiB of real packs.
- 53 candidate implementation directories for 22 current directions: 20 are the current link
  target of `RESEARCH_MAP.md`, 33 are prior or sibling attempts, 3 of which the production
  backend still imports. Eight candidates nest attempts one level down; the rest spread attempts
  across flat siblings (`variable_n_fleet_churn`, `_b2`, `_b3`, `_b_explore`, `_bpcr_r09`, `_r02`).
- Tests use two naming conventions forced by one `.gitignore` rule (`test*.py` ignored globally,
  re-included only under `tests/experiments/**`), 48 test directories against 53 implementation
  directories, two flattened names, one empty directory, and 819 `--basetemp` directories (789 of
  them directly under `temp/`, 31 at the repository root).
- `temp/` has 1,158 top-level entries and 41 "direction" ids for 22 directions; `.tmp/` has 103.
- Worktrees live in three places (5 inside `.claude/worktrees/`, 2 as bare siblings, 11 under
  `HMASD-worktrees/`), 94 branches, 4 stashes; 4 of the 11 sibling worktrees are already merged.
- The control plane is two root files and three dot-directories; no nested `AGENTS.md` or
  `CLAUDE.md` exists; `CLAUDE.md`'s counts are stale in four places (21/22 directions, 83/99 run
  scripts, 7/10 SCDMP subs, 3/4 UCOPE subs); `PROJECT_MAP.md` is stale about the count it exists
  to report.

## 1. Principles

1. **One authority per fact, nearest to the code.** A directory's conventions live in that
   directory's `AGENTS.md`; the root `AGENTS.md` holds only repository-wide rules and a map of
   maps. `CLAUDE.md` files are one-line imports of the sibling `AGENTS.md`, so both runtimes read
   one text. (Codex merges `AGENTS.md` from the root down to the working directory, nearest wins,
   about 32 KiB combined; Claude Code reads root `CLAUDE.md` plus nested `CLAUDE.md` files on
   demand and supports `@path` imports.)
2. **Frozen paths are not moved.** Any path bound into evidence (a launch sha, a byte-addressed
   manifest, a `production_backend.py` import, a runner argv) keeps its name. The standard applies
   to new attempts; old attempts are labelled, not relocated.
3. **Visible by default.** A new file under a source or docs path is tracked unless a rule names
   it as generated. The global denylists on `*.md`, `*.txt`, `*.pdf`, `*.png`, `test*.py` go away.
4. **One scratch root, keyed by direction.** Everything unversioned lives under
   `temp/directions/<direction-id>/{exp,test}/`; nothing at the repository root, nothing loose under
   `temp/`.
5. **Two worktree homes, one naming rule.** Claude agents under `.claude/worktrees/`, everything
   else under `../HMASD-worktrees/<branch-slug>/`; branches named `<runtime>/<direction-id>/<object>-<date>`.

## 2. Target layout

```
AGENTS.md                      repo-wide authority (control-plane draft) + map of maps
CLAUDE.md                      environment, commands, "@AGENTS.md"
main.py config.py config_1.py  original route entry points (unchanged)
train_multiproc_config_1.py    legacy route (unchanged)
hmasd/  ha_ctse_process/  envs/          production packages, each with AGENTS.md (+ one-line CLAUDE.md)
experiments/
  AGENTS.md                    candidate standard, direction-id → directory map with status
  candidates/<direction-id>/<attempt>/     new attempts nest here (existing dirs stay, labelled)
  legacy_lineages/             gnn_hmasd/, manifold_hmasd/            [DECIDE 2.1]
  launchers/ optuna/ continuous_alice_bob/  → tools/ or legacy_lineages/  [DECIDE 2.1]
scripts/
  AGENTS.md                    run_<prefix>_<object>.py rule, interpreter rule, preflight
  run_<prefix>_<object>.py     result-bearing entry points; prefix from RESEARCH_MAP's new column
  hmasd_*.py  schemas/         workflow tools
  (analysis/screen scripts → tools/analysis/)                        (auto)
tests/
  AGENTS.md                    one convention (test_*.py), mirror the source tree, basetemp rule
  <package>/…                  mirrors hmasd/, ha_ctse_process/, envs/, scripts/   (new files only)
  experiments/candidates/<direction-id>/<attempt>/   mirrors nesting exactly (no flattening)
  skills/  fixtures/
tools/                         analysis, benchmarks, diagnostics (unchanged)
docs/
  AGENTS.md                    document families, which tree is authority
  project/  research/  external-review/     authorities (unchanged)
  Claude_docs/                 session deliverables (unchanged)
  archive/                     new/, new-libs/, report/, superpowers/, benchmarks/, operations/, agents/  [DECIDE 2.2]
temp/directions/<direction-id>/{exp,test}/   the only scratch root
.codex/  .agents/              Codex runtime (tracked)
.claude/settings.json, .claude/agents/       tracked; .claude/worktrees/ ignored          [DECIDE 2.3]
```

[DECIDE 2.1] Dormant lineages and the three loose `experiments/` subtrees: (a) move
`gnn_hmasd/`, `manifold_hmasd/` to `experiments/legacy_lineages/` and `launchers/`, `optuna/`,
`continuous_alice_bob/` to `tools/experiments/` with import shims for the two scripts that reach
them; (b) leave all five where they are and label them in `experiments/AGENTS.md`. Recommended:
(b) now, (a) never unless a lineage is revived; moving dormant code buys nothing.

[DECIDE 2.2] `docs/` consolidation: (a) move `docs/new/`, `docs/new-libs/` (178 files),
`docs/report/`, `docs/superpowers/`, `docs/benchmarks/`, `docs/operations/`, `docs/agents/`, the
empty `docs/plans/` and `docs/migration/` into `docs/archive/<name>/` with a one-line index;
(b) leave them. Recommended: (a); none is an authority and none is referenced by `CLAUDE.md`'s
navigation table.

[DECIDE 2.3] `.claude/`: (a) track `.claude/settings.json` and `.claude/agents/*.md` (project
agent definitions for Claude Code, the analogue of `.codex/agents/`), keep `.claude/worktrees/`
and locks ignored; (b) keep the whole directory ignored. Recommended: (a), so Claude-side agent
definitions live in the repo like the Codex ones.

## 3. Candidate directories

Rule for new work: `experiments/candidates/<direction-id>/<attempt>/` where `<direction-id>` is
the `docs/research/candidates/` directory name and `<attempt>` is the science-card id in lower
snake case (`omrc_b01`, `bpcr_r09`, `e2_interruption_cost`). Tests mirror at
`tests/experiments/candidates/<direction-id>/<attempt>/`. Shared code of a direction lives at
`experiments/candidates/<direction-id>/` itself (as `ucope/` already does).

Existing directories: none is moved (principle 2). `experiments/AGENTS.md` carries the map:
directory → direction id → status (`current` for the 20 link targets, `prior` for superseded
attempts of a current direction, `legacy` for the 14 closed labels, `imported` for the three
prior attempts `production_backend.py` still loads). `RESEARCH_MAP.md` gains a "script prefix"
column (`cbsc`, `vnfc`, `scdmp`, `ucope`, `fsd`, …) so scripts and tests use one token per
direction. (auto once §3 is accepted)

[DECIDE 3.1] The three empty or near-empty directories (`scdmp_variable_k/native_fusion_r01/`,
0 tracked files; `tests/experiments/candidates/finite_semantic_boundary_support/`, 0 tracked
files; `scripts/dashboard/`): delete. Recommended: yes.

## 4. Tests

- One convention for new files: `test_<subject>.py`, in a directory mirroring the source path.
  Existing `*_test.py` files are not renamed; pytest collects both patterns.
- `pytest.ini` at the root [DECIDE 4.1]: `testpaths = tests`, `python_files = test_*.py *_test.py`,
  `cache_dir = temp/pytest_cache`, no `addopts` that changes behaviour. Recommended: yes, minimal.
- `--basetemp` is always `temp/directions/<direction-id>/test/<run-tag>` for evidence-bearing
  runs; the flat `temp/pytest-<slug>` form is retired. `tests/AGENTS.md` carries the exact
  command lines that `CLAUDE.md` has today.
- `.gitignore` drops the global `test*.py` rule (principle 3), which removes the reason for the
  two conventions.
- Stale `tests/__pycache__` entries and the 47 ignored `__pycache__` directories are deleted
  (auto; regenerated on the next run).

## 5. Scripts

- `scripts/run_<prefix>_<object>.py` for result-bearing entry points only, prefix from the new
  `RESEARCH_MAP.md` column. Analysis and screening scripts (13 loose files: `analyze_*`,
  `screen_*`, `collect_good_states`, `rollout_and_collect`, `train_vae`, `uav_g0_artifact_io`,
  `orbit_owner_freeze_evidence`, `codex_cost_role_weekly`) move to `tools/analysis/` with their
  tests [DECIDE 5.1]; recommended: yes, none is bound into evidence by absolute path (verify each
  with `git grep` before the move).
- No absolute interpreter or user-profile paths in scripts. The eight matches (five to the main
  conda env, one to a stray Python 3.11, two to `C:\Users\wu\...\SB3`) are replaced by
  `sys.executable` or an `HMASD_PYTHON` environment variable with the documented default; the two
  `wu`/`SB3` PowerShell launchers and the Python 3.11 reference are stale [ASK 5.2: is
  `run_ucope_structural_competence_certificate.py`'s frozen Python 3.11 path part of a frozen
  contract, or an accident?].

## 6. Scratch, worktrees, branches, git hygiene

- Scratch: `temp/directions/<direction-id>/{exp,test}/` only. One-time cleanup [DECIDE 6.1]:
  delete the 789 `temp/pytest*` entries, the 31 root `.tmp_pytest_*`/`.pytest_tmp*` directories,
  `.tmp/` (103 task dirs, 2026-08-26 → 09-01), `.codex_tmp_pytest_audit_liveness/`, `.scratch/`,
  the loose `*_admit_memory.json` receipts at `temp/` top level, the four non-direction buckets
  under `temp/directions/` (`control-plane`, `path-normalization`, `workflow`,
  `workflow-codex-migration`) and the `crto` duplicate, and `config.toml.backup_20260903_131348.toml`.
  Recommended: yes, all; none is cited by a tracked document (to be verified by `git grep` of each
  name before deletion, with a list of any hits returned to the owner instead of deleted).
- Worktrees [DECIDE 6.2]: remove the four merged sibling worktrees and their branches
  (`expressibility_gated_renewal_credit_relay`, `opportunity_normalized_lease_gated_rebinding`,
  `ucope-engineering-s2c1`, `ucope-v3`) and the two merged `.claude/worktrees/agent-*` ones;
  list the seven unmerged sibling worktrees from 2026-08-24 → 08-28 (`omp/*`, `codex/*`, the
  detached `HMASD-vnfc-debug-98c96af0`) with their branch tips for the owner to keep or drop.
  Recommended: remove merged now; unmerged are the owner's.
- Branches: `<runtime>/<direction-id>/<object>-<date>` for new branches (`claude/flexible_skill_duration/e2-20260903`,
  `codex/ucope/three-witness-hinge-20260904`); the 94 existing branches are pruned to those with
  a worktree or an unmerged tip newer than 2026-08-28 [DECIDE 6.3]; recommended: yes, after a
  tag `archive/branches-20260903` that keeps every tip reachable.
- `git gc --prune=now` to clear the 716 MiB of garbage objects [DECIDE 6.4]; recommended: yes
  (safe; it removes only unreferenced temporary objects). The 377 MiB of tracked `RESULT.json`
  is out of scope here and only flagged: a later decision on Git LFS or on a size cap for
  evidence files.

## 7. `.gitignore` rewrite

Replace the 252-line denylist-plus-allowlist with about 40 lines: generated artifacts
(`__pycache__/`, `*.py[cod]`, `*.pt`, `*.pkl`, `*.npy`, `*.npz`, `*.sqlite3`, `*.tfevents.*`),
tool caches, `models/`, `results/`, `logs*/` (with the 24 tracked files force-kept or moved to
`docs/archive/logs/` [ASK 7.1]), `runtime/`, `temp/` (except `temp/README.md`), `.tmp*`,
`.claude/worktrees/`, `.claude/*.lock`, `.remember/`, root personal notes by name. No global
`*.md`, `*.txt`, `*.pdf`, `*.png`, `test*.py`. Personal root files (`CONCEPT_MAP.md`,
`LEARNING_LOG.md`, `SESSION_SUMMARY_*.md`) move to `docs/personal/` (ignored as a directory)
[ASK 7.2: keep them out of Git, or track them?]. `.gitattributes` is unchanged. (auto after the
owner accepts, applied on the control-plane branch with `git status` before/after compared to
prove nothing tracked becomes untracked and nothing unwanted becomes tracked.)

## 8. Layered `AGENTS.md`

| File | Content (moved from) | Size target |
| --- | --- | --- |
| `AGENTS.md` (root) | authority text of the control-plane draft + a ten-line map of maps | ≤ 12 KiB |
| `CLAUDE.md` (root) | environment, interpreters, commands, `@AGENTS.md`; the architecture and research-layout sections leave | ≤ 8 KiB |
| `experiments/AGENTS.md` | candidate standard (§3), directory → direction map with status, native-backend rule, the `production_backend.py` import list | ≤ 8 KiB |
| `ha_ctse_process/AGENTS.md` | process-core internals and the subproc rule (from `CLAUDE.md` and `PROJECT_MAP.md`) | ≤ 6 KiB |
| `envs/AGENTS.md` | native boundary, the two C++ sources, `cpp_extension_cache`, device caveat (P1b) | ≤ 4 KiB |
| `tests/AGENTS.md` | §4 verbatim with the exact commands | ≤ 4 KiB |
| `scripts/AGENTS.md` | §5, preflight, `hmasd_run.py` when frozen | ≤ 4 KiB |
| `docs/AGENTS.md` | which tree is authority, document families, Claude_docs convention, evidence-file size flag | ≤ 4 KiB |
| each of the above directories: `CLAUDE.md` | one line, `@AGENTS.md` | — |
| `docs/project/PROJECT_MAP.md` | reduced to a one-page index of the nested files, with the stale count fixed | ≤ 3 KiB |

`RESEARCH_MAP.md`, `PORTFOLIO.md`, the evidence spec and `DIRECTION.md` files are unchanged.
[DECIDE 8.1] adopt this split; recommended: yes. [DECIDE 8.2] who writes the nested files:
(a) Claude drafts all eight on the control-plane branch for one review; (b) one Codex
`$hmasd-workflow-outsource` contract per file. Recommended: (a).

## 9. Order of application

1. Owner decisions on §2–§8 (one question set).
2. On branch `control-plane-revision-20260903`: nested `AGENTS.md`/`CLAUDE.md` files, `.gitignore`
   rewrite, `pytest.ini`, `RESEARCH_MAP.md` column, `PROJECT_MAP.md` reduction, `CLAUDE.md`
   thinning. One review, one merge.
3. On `main`, each as its own commit with the verification named: `tools/analysis/` moves,
   empty-directory deletions, interpreter-path replacements.
4. Local hygiene (nothing in Git): scratch cleanup, worktree removal, branch prune after the
   archive tag, `git gc`.
5. Only then: new attempts follow §3–§5. No existing attempt is touched.
