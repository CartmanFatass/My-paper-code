# HA-CTSE Process-Core Standalone

This directory is the standalone implementation of the new HA-CTSE
process-core algorithm.

It may reuse environment and scenario infrastructure from the repo, but it must
not import or train through `hmasd.agent`, HMASD discriminators, or the HMASD
training loop.

Main entry points:

```powershell
python -m ha_ctse_process.train
python -m ha_ctse_process.smoke
```

Collector modes:

```powershell
python -m ha_ctse_process.train --collector_backend sync
python -m ha_ctse_process.train --collector_backend subproc --collector_start_method spawn
```

The `subproc` collector only runs environment `reset/step` in worker processes.
Policy inference, rollout storage, segment closure, PPO updates, and process
updates stay in the main process.  This keeps the algorithm on-policy and avoids
worker-side replay.

Recommended lightweight UAV smoke profile:

```powershell
python -m ha_ctse_process.train --preset S7-S1 --scenario energy --n_agents 6 --num_envs 2 --collector_backend subproc --total_timesteps 16 --rollout_length 8 --skill_interval 4
```

Default algorithm config:

```text
ha_ctse_process.config.Config
```

The default config inherits environment presets from `config_1.Config`, but
owns the standalone algorithm hyperparameters locally so HMASD and process-core
experiments are not mixed.
