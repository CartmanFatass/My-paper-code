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
decide. Neither local environment has CUDA.

Result-bearing and compute-intensive execution is **remote-first** (owner, 2026-09-04;
`AGENTS.md` §5). The execution node is declared in `.codex/hmasd-compute.toml` (`wsl_4070`,
SSH alias `hmasd-wsl-node`, repo `/home/wu/projects/HMASD`, worktrees under
`/home/wu/hmasd-worktrees`, interpreter `/home/wu/.venvs/hmasd/bin/python`, supervisor
`/usr/local/bin/agent-task`; network-touching commands run inside `zsh -lic`). Its sparse
checkout omits `docs/`; add a committed evidence path to the sparse surface before a run reads
it. The control plane (editing, review, Git, transport) stays on this Windows checkout.

## Commands

```powershell
# tests (pytest.ini sets testpaths and both file patterns; see tests/AGENTS.md)
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/experiments/candidates/ucope/
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/hmasd_run_test.py::test_name
# evidence-bearing test runs isolate their temp dir under the direction's scratch root
... -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/<direction-id>/test/<run-tag>

# original HMASD/UAV route
python experiments/launchers/main.py --mode train --scenario 1 --n_uavs 5 --n_users 50
python experiments/launchers/main.py --mode eval  --scenario 2 --model_path models/hmasd_model.pt --render

# standalone process-core route
python -m ha_ctse_process.train
python -m ha_ctse_process.smoke

# mandatory resource admission, immediately before every result-bearing run, resume or queue element
python scripts/hmasd_resource_preflight.py admit-memory --out <receipt.json>

# remote route: admission and runner are one supervised command on the executing node (AGENTS.md §7)
ssh hmasd-wsl-node "zsh -lic 'cd /home/wu/hmasd-worktrees/<wt> && git fetch && git worktree add ... <launch-sha>'"
ssh hmasd-wsl-node "bash -lc '/usr/local/bin/agent-task run <handle> -- /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out <receipt> && /home/wu/.venvs/hmasd/bin/python scripts/run_<prefix>_<object>.py ...'"
ssh hmasd-wsl-node "/usr/local/bin/agent-task status <handle>"   # observation; never run/stop/attach
```

Only `hmasd-experiment-operator` issues launch commands; the hub never launches in its own
process. Test scratch: every pytest invocation supplies `-p no:cacheprovider --basetemp
temp/directions/<direction-id>/test/<run-tag>` (or `temp/tests/<run-tag>` outside a direction)
and the creator removes that directory when done (`tests/AGENTS.md`, OWNER_DIRECT 2026-09-08).

There is no lint, format or type-check tooling, no dashboard for research code, and no C++ build
step (native extensions compile through PyTorch's JIT loader on first use). Do not add any of
them. The one owner-side exception is `tools/owner_console/` (owner decision 2026-09-04): a
standard-library local page that reads and writes only the owner surfaces under
`docs/research/portfolio/owner/`; the research loop never depends on it.

## Working rules specific to this repository

- Scientific integrity, quarantine of incomplete attempts, the telemetry rule, diagnosis by
  reproduction and the post-learner rule: `AGENTS.md` §8.
- Git under concurrent sessions (reuse the direction checkout, stage by path, commit by pathspec,
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
moved here from `AGENTS.md` Appendices B and C on 2026-09-06 and **resynchronised with the
Codex control plane on 2026-09-15** (owner instruction of that date): the dated `OWNER_DIRECT`
blocks in `AGENTS.md` (2026-09-10 DM absorbs CM; 2026-09-12 CM/Implementer suspension and
rolling chains; 2026-09-13 DM autonomy; 2026-09-14 two-axis calibration, evidence spec §11.11)
bind Claude sessions exactly as they bind Codex. Where a Claude file below is silent, the Codex
role file or skill it was ported from applies.

### Claude Code session rules (formerly AGENTS.md Appendix B)

- `CLAUDE.md` at the repository root carries the environment, commands, architecture, and
  repo-specific working rules; it is tracked. `.claude/settings.json` denies edits to the Codex
  control plane.
- Deliverables of a Claude session (reviews, plans, experiment designs and results outside the
  research authority tree) live under `docs/Claude_docs/<category>/`, indexed by its README.
  Research authority records (cards, intakes, `DIRECTION.md`, decisions, handoffs, ledger,
  owner items, briefs) live in their `docs/research/` locations exactly as for Codex.
- The Fable session is the **research hub**: Root and Direction Manager at once for the directions
  it drives (owner, 2026-09-05). Its procedure is `.claude/skills/hmasd-research-hub/SKILL.md`. It
  keeps every scientific judgment (cards, L0 specifications, intake, decisions, owner items,
  briefs, `DIRECTION.md`, Portfolio rows, integration) and, under the 2026-09-12 suspension of
  CM and Implementer assignments, **implements code directly** with the L0 five facts of
  `docs/project/ENGINEERING_SCOPE_SPEC.md` §7.1 and independent `hmasd-reviewer` review for
  high-risk diffs (§7.3). It delegates bounded methods to the subagents in `.claude/agents/`,
  ported from `.codex/agents/*.toml`: Opus for independent judgment (`hmasd-reviewer`,
  `hmasd-research-critic`), Sonnet for scouting, launch, observation and mechanical work
  (`hmasd-cm-scout`, `hmasd-verifier`, `hmasd-experiment-operator`, `hmasd-experiment-tracker`,
  `hmasd-clerk`, `hmasd-research-scout`, `hmasd-pro-transport`). `hmasd-cm` and
  `hmasd-routine-implementer` are retained for recovery of accepted work and receive no new
  assignment until the owner lifts the suspension. Subagents cannot spawn subagents, so the hub
  dispatches every specialist itself; there is no sibling messaging, so the tracker is the
  bounded Claude counterpart of the DM-owned native Monitor in
  `docs/project/EXPERIMENT_MONITOR.md`, invoked by the hub per window, and the hub retains
  collection, technical acceptance and intake.
- Capacity in a Claude session is **two concurrently advancing directions** (owner, 2026-09-03,
  reaffirmed 2026-09-05 and 2026-09-15; the Claude five-hour usage window is the reason). The
  three-chain working set in `AGENTS.md` §5 is the Codex loop's target and does not apply here.
  Lifecycle, priority, occupied slots and budgets are unchanged by which loop drives a
  direction; a Claude session drives existing occupied slots and never authors a vacancy
  replacement.
- The hub and every editing agent reuse the direction's designated checkout and branch under
  `AGENTS.md` §6 (one authoring worktree per direction, created on demand); no automatic
  per-agent isolation. The hub integrates accepted commits into `main` by cherry-pick, pushes
  immediately after every commit, and retires finished temporary branches. Commits end with the
  `Co-Authored-By` and `Claude-Session` trailers the runtime supplies plus the `scope:` line.
- Pro transport in Claude Code goes through Agentify Desktop (`C:/Projects/agentify-desktop`) and
  the same scoped GitHub delivery (`docs/project/GITHUB_RESEARCH_COLLABORATION.md`), packet
  renderer, registry, provider policy (`.codex/hmasd-transport.toml`) and conversation bindings
  the Codex Transport uses; procedure in `.claude/skills/hmasd-pro-transport/SKILL.md`. The
  non-scientific smoke passed on 2026-09-05, so scientific dispatch through
  `hmasd-pro-transport` is enabled. The hub is the author DM: it dispatches direction-tier
  questions to `em:<direction>:convergence` / `:innovator` and Portfolio-tier questions to
  `portfolio:cross_direction`, and takes complete archived responses in as `PRO_FINAL` (or
  `PRO_FINAL / OWNER_DELEGATED` for Portfolio under `AGENTS.md` §4.8) after checking them
  against current owner instructions and specifications. Transport readiness follows the
  actual ChatGPT login state and one-Send reconciliation (OWNER_DIRECT 2026-09-11), never which
  session opened a browser surface. Whenever transport is unavailable, record the actual
  missing scientific review fact and pause only the dependent scope; transport failure never
  parks a direction.
- Handoffs: per direction `docs/research/candidates/<direction>/HANDOFF_<date>_<slug>.md`; root
  `docs/research/portfolio/handoffs/<date>-<slug>.md`. Write both before a session's usage
  window closes.

### Grok Build route (formerly AGENTS.md Appendix C)

- Grok Build (xAI CLI) is a third agent runtime under section 1 (owner decisions 2026-09-05
  22:40 and 22:57 PDT). It receives working methods only. Its **CM mode** (`grok-4.6` high, one
  direction's code implementation) is an "equivalent code-implementation role" and is
  **suspended with CM/Implementer under OWNER_DIRECT 2026-09-12**; no new Grok CM assignment
  starts until the owner lifts that suspension. Its **clerk mode** (`grok-4.5` medium, owner
  2026-09-06) continues: every mechanical control-plane task whose content the hub has fixed in
  advance (ledger rows, owner items through `item.py`, evidence copies, packet auxiliary files,
  splices of hub-written text, render/bind, named checks, cherry-pick sequences). Grok never
  launches result-bearing runs, never operates Pro transport, and never makes a scientific
  judgment.
- Invocation is headless and fenced (`.claude/skills/hmasd-grok-cm/SKILL.md`): the direction's
  existing worktree, an explicit tool allowlist, no subagents, no web, deny rules on every shared
  or governance path, no git commands. Its output is a diff for the hub to review and commit by
  pathspec with an `Implemented-By: grok-build` trailer. Accepted Grok work is recorded as a
  `technical` ledger row.
- Grok reads `AGENTS.md`, `CLAUDE.md`, `.claude/agents/` and `.claude/skills/` itself; those
  files bind it as they bind every runtime. No Grok-specific authority, label or gate exists.
