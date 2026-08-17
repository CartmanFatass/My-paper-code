# HMASD Project Map

This is the stable code-architecture map. It complements, rather than repeats,
[`CURRENT_WORK.md`](CURRENT_WORK.md), assignment-named scientific contracts,
and exact-commit `CODE_SCIENCE_INDEX.md` files.

| Question | Source |
| --- | --- |
| Current work routing | [`CURRENT_WORK.md`](CURRENT_WORK.md) |
| Exact scientific meaning for a named task | Its assignment-named scientific contract |
| Exact claim-to-code and test connection | The matching exact-commit `CODE_SCIENCE_INDEX.md` |
| Stable repository architecture | This map |

## Stable lineages

| Surface | Role and boundary |
| --- | --- |
| Root [`main.py`](../../main.py), root [`config.py`](../../config.py), and [`hmasd/`](../../hmasd/) | Original HMASD/UAV route. `main.py` directly imports `hmasd.agent.HMASDAgent` and the scenario-1/scenario-2 environments. Root `config.py` is a compatibility import of [`config_1.Config`](../../config_1.py). |
| [`train_multiproc_config_1.py`](../../train_multiproc_config_1.py) | Root/legacy multiprocess and baseline route, not the standalone process-core entry. |
| [`ha_ctse_process/`](../../ha_ctse_process/) | Standalone process-core platform, entered with `python -m ha_ctse_process.train`; it uses its own [`config.Config`](../../ha_ctse_process/config.py) and does not train through `hmasd.agent`. |
| [`envs/`](../../envs/) | Shared environment and source infrastructure. [`ha_ctse_process/env_factory.py`](../../ha_ctse_process/env_factory.py) selects the standalone environment. |
| [`experiments/candidates/`](../../experiments/candidates/) | Isolated proof-sized candidates. Production code has no import edge into this package. |
| [`gnn_hmasd/`](../../gnn_hmasd/) and [`manifold_hmasd/`](../../manifold_hmasd/) | Alternative lineages, not default standalone dependencies. |
| [`scripts/`](../../scripts/), [`tests/`](../../tests/), [`docs/research/designs/`](../research/designs/), [`docs/research/candidates/`](../research/candidates/), [`docs/research/cdc/`](../research/cdc/), and [`docs/external-review/`](../external-review/) | Contract- or assignment-scoped support surfaces; their presence alone does not make them part of a default route. |

## Standalone process-core route

```text
ha_ctse_process.train
  -> standalone_cli / env_factory / collectors
  -> standard train runner or eval runner
  -> StandaloneProcessAgent and focused owners
  -> segment and lifecycle state, PPO/process updates
  -> checkpoint, manifest, metrics, and plotting owners
```

[`ha_ctse_process/train.py`](../../ha_ctse_process/train.py) parses and wires
train/eval. [`standalone_train_runner.py`](../../ha_ctse_process/standalone_train_runner.py)
owns the standard training loop and dispatches specialized process-semantics and
variable-roster branches. [`standalone_eval_runner.py`](../../ha_ctse_process/standalone_eval_runner.py)
owns evaluation; [`standalone_variable_roster_runner.py`](../../ha_ctse_process/standalone_variable_roster_runner.py)
owns the variable-roster event branch.

The regular route creates environments and collectors through
[`standalone_cli.py`](../../ha_ctse_process/standalone_cli.py),
[`env_factory.py`](../../ha_ctse_process/env_factory.py), and
[`collectors.py`](../../ha_ctse_process/collectors.py). In subprocess mode,
workers perform environment `reset` and `step`; inference, rollout storage,
lifecycle handling, and PPO/process updates remain in the main process.

[`standalone_agent.py`](../../ha_ctse_process/standalone_agent.py) defines
`StandaloneProcessAgent`, composed from focused
[`standalone_models.py`](../../ha_ctse_process/standalone_models.py),
[`standalone_ar_selection.py`](../../ha_ctse_process/standalone_ar_selection.py),
[`standalone_lifecycle.py`](../../ha_ctse_process/standalone_lifecycle.py),
[`standalone_low_inference.py`](../../ha_ctse_process/standalone_low_inference.py),
[`standalone_low_update.py`](../../ha_ctse_process/standalone_low_update.py), and
[`standalone_segments.py`](../../ha_ctse_process/standalone_segments.py) owners.
The variable-roster event family has a central
[`lifecycle/core owner`](../../ha_ctse_process/variable_roster_event.py), with separate
[`types`](../../ha_ctse_process/variable_roster_event_types.py),
[`models`](../../ha_ctse_process/variable_roster_event_models.py), and
[`checkpoint`](../../ha_ctse_process/variable_roster_event_checkpoint.py) surfaces.

## Load-bearing ownership

| Owner | Responsibility |
| --- | --- |
| Environment implementations | Transition dynamics and environment RNG. |
| [`collectors.py`](../../ha_ctse_process/collectors.py) | Transport/order plus validation and aggregation of event snapshots; the worker environment retains its own snapshot and RNG state. |
| [`standalone_agent.py`](../../ha_ctse_process/standalone_agent.py), [`standalone_models.py`](../../ha_ctse_process/standalone_models.py), and [`standalone_low_update.py`](../../ha_ctse_process/standalone_low_update.py) | Policy/action probabilities and update identity. |
| [`standalone_segments.py`](../../ha_ctse_process/standalone_segments.py) and [`standalone_lifecycle.py`](../../ha_ctse_process/standalone_lifecycle.py) | Rollout and temporal lifecycle state. |
| [`checkpoint_io.py`](../../ha_ctse_process/checkpoint_io.py) | Checkpoint payloads, loading, migration, and pruning. |
| [`standalone_manifest.py`](../../ha_ctse_process/standalone_manifest.py), [`metrics_io.py`](../../ha_ctse_process/metrics_io.py), [`standalone_metrics.py`](../../ha_ctse_process/standalone_metrics.py), and [`plotting.py`](../../ha_ctse_process/plotting.py) | Manifest, CSV I/O, metric emission, and plotting/output layers, respectively. |
| [`variable_roster_event.py`](../../ha_ctse_process/variable_roster_event.py), [`variable_roster_event_types.py`](../../ha_ctse_process/variable_roster_event_types.py), [`variable_roster_event_models.py`](../../ha_ctse_process/variable_roster_event_models.py), and [`variable_roster_event_checkpoint.py`](../../ha_ctse_process/variable_roster_event_checkpoint.py) | Event lifecycle state, active-only packing, opportunity clocks and ledgers; DTOs; policy/model definitions; and event checkpoint/restore. |

## Native boundary

[`envs/native/cpp_extension_cache.py`](../../envs/native/cpp_extension_cache.py)
owns shared source-keyed C++ extension loading and cache mechanics. Python
adapters validate arrays/results and call native kernels in
[`envs/continuous_roster/cpp_backend.py`](../../envs/continuous_roster/cpp_backend.py)
and [`envs/pettingzoo/uav_cpp_backend.py`](../../envs/pettingzoo/uav_cpp_backend.py).
Specialized continuous-roster modules demonstrate a dependency on the native
six-coordinate backend. The UAV C++ geometry backend is directly referenced by
[`tools/benchmarks/benchmark_uav_cpp_backend.py`](../../tools/benchmarks/benchmark_uav_cpp_backend.py),
not by the default standalone environment factory. Neither native backend
adapter is imported by [`ha_ctse_process/env_factory.py`](../../ha_ctse_process/env_factory.py);
the map therefore does not claim that every environment or the default
standalone route runs in C++.

## Stable dependency direction

Entry and wiring points point inward to runners, agent/collector/environment
owners, and output owners. Python adapters point to native kernels; policy code
does not point into C++. Production code does not import isolated candidates.
Runners connect boundaries; they do not own environment physics or scientific
interpretation.

## Agent context control plane

Repository-local Codex overlay for actor-scoped workflows. It is a delivery,
obligation, epoch, and reanchor ledger. runtime SQLite is noncanonical.

| Surface | Role |
| --- | --- |
| [`tools/codex_semantic_mvp/`](../../tools/codex_semantic_mvp/) | Hook/MCP overlay, actor registry, owner-local epochs, semantic commits, checkpoints, packet refs |
| [`tools/codex_context_lifecycle/`](../../tools/codex_context_lifecycle/) | Context-source registry, promotion, rollover, working-set, and retention extension |
| [`runtime/codex-semantic-mvp/`](../../runtime/codex-semantic-mvp/) | Gitignored control-plane runtime. Not canonical project memory. |
| [`tests/codex_semantic_mvp/`](../../tests/codex_semantic_mvp/) | Overlay contract tests |
| [`tests/codex_context_lifecycle/`](../../tests/codex_context_lifecycle/) | Context-lifecycle contract tests |
| [`docs/project/CONTEXT_SOURCE_REGISTRY.toml`](CONTEXT_SOURCE_REGISTRY.toml) | Role-scoped source index |
| [`docs/project/DECISIONS_INDEX.md`](DECISIONS_INDEX.md) | Shared ADR index |

PROJECT_MAP is the stable codemap. CURRENT_WORK is the current-work index.

## Repository context lifecycle

Progressive context layers, loaded only when the current actor and assignment
require them:

```text
AGENTS/roles
Skills
PROJECT_MAP
CURRENT_WORK
owner artifacts
ADR index
epochs/checkpoints
typed packets
history
```

Automatic memory and compaction summaries are retrieval hints only.

## Maintenance Protocol

The Code Project Manager owns this map's accuracy. Update it in the same code
commit when a stable lineage role, default execution shape, load-bearing state
owner, stable dependency direction, or isolated/legacy route membership
changes. Ordinary local internals and temporary experiments do not trigger an
update. A discovered discrepancy is a documentation defect corrected as a
necessary consequential change.
