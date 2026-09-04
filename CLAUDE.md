# CLAUDE.md

Guidance for Claude Code in this repository. The collaboration and authority rules are in
`AGENTS.md` (runtime-neutral; Appendix B is the Claude Code part) and are imported here:

@AGENTS.md

Directory conventions live next to the code, one `AGENTS.md` per top-level area, each imported by
a one-line `CLAUDE.md` beside it: `experiments/`, `ha_ctse_process/`, `envs/`, `tests/`,
`scripts/`, `docs/`. `docs/project/PROJECT_MAP.md` is the one-page index of those files. What
research code may and may not build is `docs/project/ENGINEERING_SCOPE_SPEC.md`.

## What this repository is

Two systems share one directory: a PyTorch MARL research codebase (HMASD, Yang et al. 2023, on
multi-UAV base-station scenarios, plus later lineages and 22 current research directions with 53
implementation directories under `experiments/candidates/`), and a research workflow and evidence
layer (`AGENTS.md`, `.agents/skills/`, `.codex/agents/*.toml`, `scripts/hmasd_*.py`,
`docs/research/`) that governs how scientific objects are frozen, run and recorded. Most day-to-day
work follows the second system's conventions even when the edit lands in the first.

## Environment

The project runs on a conda environment that is **not** the `python` on PATH (a bare system
Python 3.11 without torch). Use the explicit interpreter:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe        # main env: Python 3.10, torch 2.7.0+cpu, pytest 9
C:/Users/fires/.conda/envs/hmasd-science-tools/python.exe  # isolated analysis env (Python 3.11, no torch)
```

The second environment is declared in `configs/scientific-capabilities-v1.toml`
(`python scripts/hmasd_science_capabilities.py list|show|doctor`). Never install into either
environment to satisfy an analysis need; report the capability as unavailable and let the owner
decide. Neither environment has CUDA.

## Commands

```powershell
# tests (pytest.ini sets testpaths and both file patterns; see tests/AGENTS.md)
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/experiments/candidates/ucope/
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/hmasd_run_test.py::test_name
# evidence-bearing test runs isolate their temp dir under the direction's scratch root
... -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/<direction-id>/test/<run-tag>

# original HMASD/UAV route
python main.py --mode train --scenario 1 --n_uavs 5 --n_users 50
python main.py --mode eval  --scenario 2 --model_path models/hmasd_model.pt --render

# standalone process-core route
python -m ha_ctse_process.train
python -m ha_ctse_process.smoke

# mandatory resource admission, immediately before every result-bearing run, resume or queue element
python scripts/hmasd_resource_preflight.py admit-memory --out <receipt.json>
```

There is no lint, format or type-check tooling, no dashboard for research code, and no C++ build
step (native extensions compile through PyTorch's JIT loader on first use). Do not add any of
them. The one owner-side exception is `tools/owner_console/` (owner decision 2026-09-04): a
standard-library local page that reads and writes only the owner surfaces under
`docs/research/portfolio/owner/`; the research loop never depends on it.

## Working rules specific to this repository

- Scientific integrity, quarantine of incomplete attempts, the telemetry rule, diagnosis by
  reproduction and the post-learner rule: `AGENTS.md` §8.
- Git under concurrent sessions (worktree per implementer, stage by path, commit by pathspec,
  never `git add -A` / stash / reset): `AGENTS.md` §6. Commits end with the trailers the runtime
  supplies plus `scope: none` or `scope: <item> per <card line>` (scope spec §7).
- Scratch belongs under `temp/directions/<direction-id>/{exp,test}/`; nothing at the repository
  root, nothing loose under `temp/`.
- Line endings: `.gitattributes` pins `eol=lf` on byte-addressed authorities (`docs/research/portfolio/`,
  every `DIRECTION.md`, `.codex/`, `.agents/`, `AGENTS.md`, `scripts/hmasd_*.py`, named fixture
  sets, the two VNFC science cards). Do not normalise them by hand.
- Workflow-layer edits are made directly by the current agent; `$hmasd-workflow-outsource` only
  when the owner names it.
- `CONCEPT_MAP.md` and `LEARNING_LOG.md` (now under `docs/personal/`) are the owner's learning
  notes, not project authorities.
