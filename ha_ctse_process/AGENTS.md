# ha_ctse_process/ — the standalone process-core route

Core tier (`docs/project/ENGINEERING_SCOPE_SPEC.md` §2, §6). Entered with
`python -m ha_ctse_process.train` (and `.smoke`); owns its own configuration
(`ha_ctse_process/config.py`, which inherits environment presets from `config_1.Config` but owns the
algorithm settings). It must not import `hmasd.agent`, the HMASD discriminators, or the HMASD
training loop; importing generic layer helpers from `hmasd/r_mappo_utils.py` is allowed and done.

About 110 files. Skeleton:

```
train.py  → standalone_cli.py → env_factory.py → collectors.py
          → standalone_train_runner.py | standalone_eval_runner.py
          → standalone_variable_roster_runner.py, event_process_runner.py   (variable roster)
agent: standalone_agent.py (327 KB; pulls ~17 modules: intrinsic_rewards, team_intent, situation_*, process_posterior, g_info_objective, …)
       standalone_models.py, standalone_ar_selection.py, standalone_lifecycle.py,
       standalone_low_inference.py, standalone_low_update.py, standalone_segments.py
edges: standalone_metrics.py, standalone_manifest.py, standalone_contracts.py,
       standalone_event_support.py, infrastructure_profiling.py, plotting.py
```

Rules that carry scientific meaning:

- The `subproc` collector runs only environment `reset/step` in workers; inference, rollout
  storage, segment closure and PPO/process updates stay in the main process. That is what keeps
  the algorithm on-policy. Do not move update work into workers.
- Checkpointing has two owners: `checkpoint_io.py` on the standard route;
  `variable_roster_event_checkpoint.py` for event and variable-roster payloads, called directly by
  `event_process_runner.py` and `standalone_variable_roster_runner.py`. Changing either format is
  a semantic change and needs the owner's name on it.
- Research-flavoured modules have accumulated inside this package
  (`continuous_roster_native_six_g31_*`, `uav_source_identifiability_g0.py`,
  `uav_charge_rotation_g2.py`, `r24_qd_dataset.py`, `r30_fixed_clock.py`, …). They are frozen as
  they are; new research code goes under `experiments/candidates/`, never here.

Usage and collector modes: `ha_ctse_process/README.md`.
