# CLAUDE.md

Guidance for Claude Code in this repository. The collaboration and authority rules are in
`AGENTS.md` (the Codex control plane, imported read-only; the Claude Code part is the section
"Claude control plane and the Codex control plane" below):

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

## Claude control plane and the Codex control plane (owner, 2026-09-06 09:56 PDT)

`AGENTS.md`, `.agents/skills/**` (including the scripts inside them such as `render_packet.py`
and `bind_conversation.py`) and `.codex/**` are the Codex control plane: they shape Codex's
behaviour and Pro's prompts. Claude sessions read and execute them but **never edit them**;
any change needs the owner's explicit approval, named per file. Claude's own rules live only in
this file and under `.claude/`. Downstream mechanical state (the shared transport registry and
archive under `temp/sessions/hmasd-chatgpt-pro-transport/`, `scripts/hmasd_*.py`) may be shared
by both loops, and is likewise modified only with the owner's approval. The sections below were
moved here from `AGENTS.md` Appendices B and C on 2026-09-06 (the appendices were restored to
their Codex-era text); their content is unchanged.

### Claude Code session rules (formerly AGENTS.md Appendix B)

- `CLAUDE.md` at the repository root carries the environment, commands, architecture, and
  repo-specific working rules; it is tracked.
- Deliverables of a Claude session (reviews, plans, experiment designs and results outside the
  research authority tree) live under `docs/Claude_docs/<category>/`, indexed by its README.
- The Fable session is the **research hub**: Root and Direction Manager at once for the directions
  it drives (owner, 2026-09-05). Its procedure is `.claude/skills/hmasd-research-hub/SKILL.md`. It
  keeps every scientific judgment (cards, objectives, intake, decisions, owner items, briefs,
  `DIRECTION.md`, Portfolio, integration) and delegates everything else to the subagents defined in
  `.claude/agents/`, ported from `.codex/agents/*.toml`: Opus for code and independent judgment
  (`hmasd-cm`, `hmasd-reviewer`, `hmasd-research-critic`), Sonnet for scouting and mechanical work
  (`hmasd-cm-scout`, `hmasd-routine-implementer`, `hmasd-verifier`, `hmasd-experiment-operator`,
  `hmasd-experiment-tracker`, `hmasd-clerk`, `hmasd-research-scout`, `hmasd-pro-transport`).
  Subagents cannot spawn subagents, so the hub dispatches every specialist itself; there is no
  sibling messaging, so the tracker is a bounded observer the hub invokes, not a standing agent.
- Capacity in a Claude session is **two concurrently advancing directions** (owner, 2026-09-03,
  reaffirmed 2026-09-05; the Claude quota is separate from Codex's). The five-chain working set in
  §2 and §5 is the Codex loop's target and does not apply here. Lifecycle and priority are
  unchanged by which loop drives a direction.
- Implementer subagents run in worktrees under `.claude/worktrees/` (`isolation: worktree`); the
  hub integrates into `main` by cherry-pick. Commits end with the `Co-Authored-By` and
  `Claude-Session` trailers the runtime supplies.
- Pro transport in Claude Code goes through Agentify Desktop (`C:/Projects/agentify-desktop`) and
  the same scoped GitHub delivery, packet renderer, registry and conversation bindings the Codex
  Transport uses; procedure in `.claude/skills/hmasd-pro-transport/SKILL.md`. It is enabled for
  unattended scientific dispatch only after one recorded non-scientific smoke has passed. Until
  then, and whenever transport is unavailable, direction- and Portfolio-tier questions are put to
  the owner through the owner surfaces; in the owner's absence the direction parks (§3) and
  object-tier decisions follow §4.

### Grok Build route (formerly AGENTS.md Appendix C)

- Grok Build (xAI CLI, `grok-4.6` at effort `high`) is a third agent runtime under section 1
  (owner decisions 2026-09-05 22:40 and 22:57 PDT). It receives working methods only: one
  direction's CM implementation when two directions advance in a Claude session, read-only code
  maps, second independent reviews, and (owner 2026-09-06, `grok-4.5`) every mechanical
  control-plane task whose content the hub has fixed in advance (ledger rows, owner items through
  `item.py`, evidence copies, packet auxiliary files, splices of hub-written text, render/bind). It never launches result-bearing runs, never operates Pro
  transport, and never makes a scientific judgment.
- Invocation is headless and fenced (`.claude/skills/hmasd-grok-cm/SKILL.md`): its own git
  worktree, an explicit tool allowlist, no subagents, no web, deny rules on every shared or
  governance path, no git commands. Its output is a diff for the hub to review, test and commit
  by pathspec with an `Implemented-By: grok-build` trailer; a diff touching a protected surface
  also goes to `hmasd-reviewer`. Accepted Grok work is recorded as a `technical` ledger row.
- Grok reads `AGENTS.md`, `CLAUDE.md`, `.claude/agents/` and `.claude/skills/` itself; those
  files bind it as they bind every runtime. No Grok-specific authority, label or gate exists.
