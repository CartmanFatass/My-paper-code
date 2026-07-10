# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A multi-agent reinforcement learning research codebase studying hierarchical skill
discovery for **multi-UAV base-station networks** (UAVs serving/relaying for ground
users). Two algorithm families coexist and must be kept separate:

- **HMASD (original / baseline)** — PyTorch reimplementation of *Hierarchical
  Multi-Agent Skill Discovery* (Yang et al., 2023): team skill + individual skill +
  intrinsic discriminator reward + autoregressive coordinator. Lives in `hmasd/`.
- **HA-CTSE process-core (the ACTIVE research line)** — a standalone algorithm in
  `ha_ctse_process/`. It reuses the environments but **must not import or train
  through `hmasd.agent`, HMASD discriminators, or the HMASD training loop**
  (see `ha_ctse_process/README.md`). It has its own agent, PPO loop, and config.

Most current work happens in `ha_ctse_process/` and `memory/`. Treat `hmasd/` as a
comparison baseline, not the thing under active development.

## Architecture

**Environments** — `envs/pettingzoo/` (PettingZoo parallel API). `scenario1.py`
(independent base stations) … `scenario7_energy_aware.py`. The active target is
**Scenario 7 energy-aware, preset `S7-S1`, 6 agents**. `scenario_base.py` /
`uav_env.py` hold shared UAV physics (channel models, coverage, QoS, backhaul).

**Config layering** — `config_1.py`'s `Config` owns environment geometry, Scenario-7
presets, and reward settings. `ha_ctse_process/config.py`'s `Config` **subclasses**
it and adds the standalone algorithm hyperparameters, so HMASD env presets and
HA-CTSE algorithm knobs never mix. (`config.py` at the root is a tiny legacy stub used
only by `main.py`.)

**HA-CTSE process-core** (`ha_ctse_process/`) implements a three-timescale hierarchy:
OPT recognition substrate (`situation_substrate.py`, prototypes → `omega`/compact
`c`/`kappa`) → slow sampled team intent `Z` (`team_intent.py`) → asynchronous
individual response skills `z_i`. Intrinsic pressure comes from discriminator-style
modules (`prototype_response_discriminator.py`, `situation_transition.py`,
`skill_effect_discovery.py`, `cooperation_credit.py`, `intrinsic_rewards.py`).
`standalone_agent.py` is the agent + PPO update; `train.py` is the CLI harness;
`collectors.py` provides the rollout collectors. **Nearly every mechanism is
default-off behind a CLI/config flag** — the codebase advances by round-numbered
experiments (R12 … R22), each gated on diagnostics before its reward path is enabled.

**Runner scripts** — `scripts/`. `.ps1` = local Windows/CUDA runs; `.sh` = cloud/Linux
(often 32/64 env). Named per experiment round (e.g. `run_r21_team_intent_cloud_64env.sh`).
`dist/` holds timestamped, self-contained upload bundles for cloud runs.

## Common commands

```powershell
# HA-CTSE standalone training / smoke (primary active path)
python -m ha_ctse_process.train
python -m ha_ctse_process.smoke

# Lightweight UAV smoke profile
python -m ha_ctse_process.train --preset S7-S1 --scenario energy --n_agents 6 --num_envs 2 --collector_backend subproc --total_timesteps 16 --rollout_length 8 --skill_interval 4

# Collector backends: sync (single process) or subproc (env reset/step in workers,
# all policy/PPO/process updates stay on-policy in the main process)
python -m ha_ctse_process.train --collector_backend subproc --collector_start_method spawn

# HMASD baseline through the SAME comparison harness (fair-comparison eval metrics)
python -m ha_ctse_process.train --algorithm hmasd_original --preset S7-S1 --scenario energy --n_agents 6

# Legacy standalone HMASD trainer (Scenario 1/2 only, older path)
python main.py --mode train --scenario 1 --n_uavs 5 --n_users 50
python main.py --mode eval  --scenario 1 --model_path models/hmasd_model.pt --render
```

## Tests

The maintained suite is `tests/` (pytest). Run it with:

```powershell
python -m pytest tests/ -q
python -m pytest tests/r19_team_transition_test.py -q      # a single test file
python -m pytest tests/r19_team_transition_test.py::<name> # a single test
```

**Do not confuse these with the many `test_*.py` files at the repo root** — those are
ad-hoc diagnostic/exploration scripts and are **gitignored** (`.gitignore` excludes
`test*.py`). They are not part of the CI-style suite; the tracked tests live under
`tests/`. There is no `pytest.ini`/`conftest.py`; run from the repo root so imports
(`config_1`, `ha_ctse_process`, `hmasd`) resolve.

Dependencies for a clean run are pinned in `requirements_server.txt` (numpy, torch,
gymnasium 1.0, pettingzoo 1.24, stable-baselines3, tensorboard, networkx, …).

## Run outputs & key diagnostics

Runs write under `logs/<experiment>_<...>/`: `standalone_train.log` (readable log),
`train_updates.csv` (per-update diagnostics), `eval_metrics.csv` (checkpoint eval),
plus figures. The recurring gate metrics to watch: `coverage`, `qos`, `throughput`,
`coverage_eq1_step_frac` (the parity bar — half of eval primitive steps at
`coverage == 1.0`, not `reward_mean` spikes), `zero_throughput_ep_frac`, duration
entropy / `switch_rate`, and per-round mechanism fields (`role_gain`, `team_t_mi`,
`team_disc_acc`, `roster_ar_kl_*`). A running process is never a conclusion — read
only at pre-registered eval/gate points.

## Claude Code subagent workflow

This project has a Claude Code clone of the Codex subagent workflow (root
`AGENTS.md` + `.codex/agents/`). The main Claude Code session is the **controller**;
the project subagents live in `.claude/agents/*.md` (codebase-scout, simple-patcher,
spark-implementer, plan-implementer, plan-implementer-frontier,
implementation-reviewer-fast/-/-frontier, test-runner, exp-manager, result-analyst,
external-review-manager, long-time-memory-manager, workflow-auditor,
marl-peer-reviewer).

**MARL design cross-validation gate (mandatory):** any MARL algorithm design
decision — reward/intrinsic-reward semantics, q_A/q_D/q_d, team-intent or skill
semantics, policy/critic architecture, credit assignment, gate-criteria or
principle changes — must be peer-reviewed by an independent non-Claude model
before acceptance. Dispatch `marl-peer-reviewer` (one read-only round through the
Codex plugin, raw reply archived in `memory/LTM/external_reviews/`), then
explicitly disposition the advice (accept/reject/defer) to the user. See the
"MARL Design Cross-Validation Gate" section of `.claude/agents/README.md`.

**Before any subagent dispatch, or when the user authorizes delegation / parallel
agent work / a subagent-driven workflow, read `.claude/agents/README.md` first** and
follow it: Wave Plan + dispatch-brief gate before spawning, file-based handoffs
(templates in `.claude/agents/templates/`), the DONE / DONE_WITH_CONCERNS /
NEEDS_CONTEXT / BLOCKED status protocol, mandatory tiered implementation reviews,
the experiment-meaning communication gate, and the runtime-output contract
(`logs/<run-id>/...`, no loose root-level runtime files). Spawn subagents only when
the user asks for delegation; an authorized workflow covers its routine
exp-manager / result-analyst / long-time-memory-manager / external-review-manager
hooks. Do not edit `.codex/` or `AGENTS.md` for Claude-only workflow changes, and
keep the two workflows in deliberate sync when shared rules change.

**Controller communication contract (user directive — always in force, even
outside subagent work):**
- Proactively translate experiment state, result facts, plan transitions, and
  subagent reports into user-facing **situation, meaning, next plan,
  recommendation, core MARL impact, and remaining gates or blockers** — never
  make the user ask "what does this mean?". If the correct state is waiting,
  name exactly what is being waited on, which metrics decide the next branch,
  and what must not change while waiting.
- Before ending any turn that used subagents, report **which subagents were
  used, what they did, important results, changed files, and remaining risk**.

**Core-implementation model floor (user directive):** core algorithm and
quality-critical numerical code is never implemented by a haiku-tier agent —
controller-direct, `plan-implementer` (opus), or `plan-implementer-frontier`
(fable) only. Haiku agents handle operational scripts, packaging, docs, and
status plumbing, and escalate on contact with algorithm semantics.

**Time-cost and device rule (user directive):** before launching any experiment
or compute-bearing analysis, state its expected wall-clock time cost to the
user. Run such work on CUDA by default; never silently degrade to CPU — if the
GPU is busy with a live run, present the options with their time costs and let
the user choose.

**Cloud handoff rule (user directive):** compute-intensive tasks (long training
runs, multi-seed batches, heavy analysis) default to the user's cloud server,
not the local GPU. Protocol: (1) tell the user directly, with the time cost;
(2) write a self-contained bash runner under `scripts/` following the existing
cloud-runner conventions (64-env defaults, explicit log root, per-run status
files, seeds via env vars); (3) commit and push it to the remote so the user
can `git pull` on the server and launch; (4) record the exact launch commands
and expected artifact paths in `memory/ExpRecord.md`. The local GPU is for
smokes and small diagnostics.

**Controller handover:** this project alternates between Claude Code and Codex as
the active controller. `docs/subagents/claude-codex-handover-spec.md` is the
binding handover protocol — read it at every controller switch (incoming or
outgoing), keep the `Controller Handoff` block in `memory/CURRENT_WORK.md`
current, and follow its role-equivalence table, direction-dependent
cross-validation rule, and one-active-controller concurrency rule.

## Research memory workflow (important)

`memory/` is a **git-tracked, project-local research memory** driving the long-running
experiment program. Read it before doing algorithm/experiment work — the compact
current files, in order:

1. `memory/CURRENT_WORK.md` — current objective, next actions, active pointers.
2. `memory/ALGORITHM_PRINCIPLES.md` — the current research contract.
3. `memory/IMPLEMENTATION_PLAN.md` — staged plan ledger.
4. `memory/ExpRecord.md` — factual experiment dashboard/ledger.

Full historical records live under `memory/LTM/` (experiment/cross-validation
archives, `external_reviews/DIALOGUE_ARCHIVE.md` for raw pasted external-model
reviews). Read LTM only when the compact files point there or the user asks for
history. Legacy attention-pointer semantics (`ATTENTION_POINTER.md`,
`AGENT_ROLES.md`, `cross_validation.md`) are retired — do not recreate those files
even if a skill mentions them; the `long-task-memo` / `ltm-exp` skills should be
mapped onto the current files above. Working conventions worth respecting:

- New mechanisms land **default-off**; a reward path opens only after its diagnostic
  gate passes. Env task reward stays external — do not relabel it as intrinsic, and do
  not build intrinsic reward from raw communication indicators.
- Keep HA-CTSE and HMASD results separate; don't mix results across experiment rounds.
- Update the relevant memory files — `CURRENT_WORK.md` plus whichever of
  `IMPLEMENTATION_PLAN.md` / `ExpRecord.md` / LTM archives apply — when focus, stage,
  experiments, or external advice change (the "Completion Sync" checklist).
