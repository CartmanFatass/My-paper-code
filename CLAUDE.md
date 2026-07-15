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

## Controller workflow

`AGENTS.md` is the operational authority. One active controller works directly
in `C:\project\HMASD` and owns implementation, focused review, experiments, Git,
memory updates, and user communication. Create auxiliary conversations or
worktrees only when the user explicitly requests them. Independent algorithm
consultation follows the manual external-review contract in `AGENTS.md`.

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

**Controller handover:** Claude Code and Codex may alternate, but only one is
active at a time. Record the active owner in `memory/CURRENT_WORK.md`; that file
is the complete handover entry point.

## Project memory

`memory/` contains only the four canonical control files:

1. `CURRENT_WORK.md` — controller, objective, next actions, constraints, pointers.
2. `ALGORITHM_PRINCIPLES.md` — durable research contract.
3. `IMPLEMENTATION_PLAN.md` — active staged core work.
4. `ExpRecord.md` — formal experiment contracts and decisions.

Read `CURRENT_WORK.md` first and other files only for the relevant decision.
Durable designs and branch decisions live in `docs/research/`; raw consultation
evidence in `docs/external-review/`; reusable operations in `docs/operations/`;
unique legacy imports in `docs/archive/`. Runtime evidence remains under
`logs/<run-id>/`. Update the one owning file at each evidence boundary and do
not create parallel memory archives or duplicate summaries.
