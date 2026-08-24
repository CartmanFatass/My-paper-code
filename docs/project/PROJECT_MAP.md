# HMASD Project Map / Codemap

This is the stable code-architecture map. It describes executable code and
dependency direction only. It is not a task router, permission system, lease
registry, or current-work ledger.

| Question | Source |
| --- | --- |
| Stable repository architecture | This file |
| Research directions, current scientific position, and directories | [`../research/RESEARCH_MAP.md`](../research/RESEARCH_MAP.md) |
| Exact scientific meaning | The direction's files under [`../research/candidates/`](../research/candidates/) |
| Candidate implementations | [`../../experiments/candidates/`](../../experiments/candidates/) |
| Candidate test source | [`../../tests/experiments/candidates/`](../../tests/experiments/candidates/) |
| Per-direction implementation, test, and scratch mapping | [`../research/RESEARCH_MAP.md#code-tests-and-generated-output`](../research/RESEARCH_MAP.md#code-tests-and-generated-output) |
| Standalone process-core usage | [`../../ha_ctse_process/README.md`](../../ha_ctse_process/README.md) |
| Local temporary files and worktree layout | [`../../temp/README.md`](../../temp/README.md) |

## Research-direction codemap standard

The stable research-direction key is the directory name under
`docs/research/candidates/`. That same key joins the four surfaces below; it is
a navigation convention, not workflow state.

| Surface | Canonical location | Contents |
| --- | --- | --- |
| Durable research artifacts | `docs/research/candidates/<direction-id>/` | Science definitions, accepted manifests, result summaries, dispositions, and code-science indexes. |
| Candidate implementation | `experiments/candidates/<implementation>/` | Versioned implementation source. The exact primary implementation name is recorded per direction in `RESEARCH_MAP.md`. |
| Candidate tests | `tests/experiments/candidates/<implementation>/` | Versioned test source for the primary or retained implementation. |
| Local experiment output | `temp/directions/<direction-id>/exp/` | Ignored runs, checkpoints, profiles, captured output, and rebuildable generated manifests. |
| Local test output | `temp/directions/<direction-id>/test/` | Ignored pytest bases, fixtures, test databases, and compiler probes. |

`RESEARCH_MAP.md` is the per-direction inventory: it records all 33 direction
keys and their current primary implementation and test paths. `AGENTS.md`
defines how agents must create and use the local directories. `temp/README.md`
defines cleanup and worktree layout. Do not duplicate the 33-row inventory in
another document.

## Stable lineages

| Surface | Role and boundary |
| --- | --- |
| [`main.py`](../../main.py), [`config.py`](../../config.py), and [`hmasd/`](../../hmasd/) | Original HMASD/UAV route. `main.py` imports `hmasd.agent.HMASDAgent`; root `config.py` is a compatibility import of `config_1.Config`. |
| [`train_multiproc_config_1.py`](../../train_multiproc_config_1.py) | Legacy multiprocess and baseline route. |
| [`ha_ctse_process/`](../../ha_ctse_process/) | Standalone process-core platform, entered with `python -m ha_ctse_process.train`. It owns a separate configuration and training route. |
| [`envs/`](../../envs/) | Shared environment and native-backend infrastructure. |
| [`experiments/candidates/`](../../experiments/candidates/) | Isolated research candidates. Their presence does not promote them into a default production route. |
| [`gnn_hmasd/`](../../gnn_hmasd/) and [`manifold_hmasd/`](../../manifold_hmasd/) | Alternative algorithm lineages. |
| [`tests/`](../../tests/) and [`tools/`](../../tools/) | Product tests, benchmarks, and development utilities. |
| [`docs/research/`](../research/) and [`docs/external-review/`](../external-review/) | Scientific definitions, evidence, and external-review archives. These documents are not executable control state. |

## Original HMASD route

```text
main.py
  -> config.py / config_1.py
  -> hmasd.agent.HMASDAgent
  -> hmasd networks, replay, coordination, and update logic
  -> envs/pettingzoo UAV environments
```

This is the repository's original implementation and compatibility surface.
It remains separate from the standalone process-core route.

## Standalone process-core route

```text
ha_ctse_process.train
  -> standalone_cli / env_factory / collectors
  -> standalone_train_runner or standalone_eval_runner
  -> StandaloneProcessAgent and focused state owners
  -> rollout, lifecycle, PPO/process updates
  -> checkpoints, manifests, metrics, and plots
```

[`train.py`](../../ha_ctse_process/train.py) parses and wires train/eval.
[`standalone_train_runner.py`](../../ha_ctse_process/standalone_train_runner.py)
owns the standard training loop, while
[`standalone_eval_runner.py`](../../ha_ctse_process/standalone_eval_runner.py)
owns evaluation. Variable-roster execution is handled by
[`standalone_variable_roster_runner.py`](../../ha_ctse_process/standalone_variable_roster_runner.py).

Environment creation and collection flow through
[`standalone_cli.py`](../../ha_ctse_process/standalone_cli.py),
[`env_factory.py`](../../ha_ctse_process/env_factory.py), and
[`collectors.py`](../../ha_ctse_process/collectors.py). The agent is composed
from `standalone_agent.py`, `standalone_models.py`,
`standalone_ar_selection.py`, `standalone_lifecycle.py`,
`standalone_low_inference.py`, `standalone_low_update.py`, and
`standalone_segments.py`.

## Load-bearing ownership

| Surface | Responsibility |
| --- | --- |
| Environment implementations | Transition dynamics and environment RNG. |
| [`collectors.py`](../../ha_ctse_process/collectors.py) | Worker transport, ordering, validation, and snapshot aggregation. |
| Agent/model/update modules | Policy probabilities, recurrent state, optimization, and update identity. |
| Segment/lifecycle modules | Rollout and temporal lifecycle state. |
| [`checkpoint_io.py`](../../ha_ctse_process/checkpoint_io.py) | Checkpoint payloads, loading, migration, and pruning. |
| Manifest/metrics/plotting modules | Output identity, metric I/O, reporting, and visualization. |
| Variable-roster event modules | Event state, active-only packing, opportunity clocks, policy definitions, and restore. |

## Native boundary

[`envs/native/cpp_extension_cache.py`](../../envs/native/cpp_extension_cache.py)
owns source-keyed C++ extension loading. Python adapters validate inputs and
call native kernels, including
[`envs/continuous_roster/cpp_backend.py`](../../envs/continuous_roster/cpp_backend.py)
and [`envs/pettingzoo/uav_cpp_backend.py`](../../envs/pettingzoo/uav_cpp_backend.py).
The map does not claim that every environment or default route is native.

## Dependency direction

Entries wire runners; runners depend on agents, collectors, environments, and
output owners. Python adapters may call native kernels. Production routes do
not import isolated candidates. Research documents describe meaning but do not
control execution.

## Optional Codex collaboration layer

The `main` branch may include `AGENTS.md` and `.codex/agents/*.toml` for native
Codex delegation. Those files select collaborators only; they do not sit in
the application import graph. The `codex/control-plane-free-20260824` branch
omits that layer while keeping the same product and research tree.

Update this map when a stable executable route, dependency direction, or the
codemap layout contract changes. Update `RESEARCH_MAP.md` when an individual
direction changes its primary implementation or test mapping. Ordinary runs,
task status, reviews, and temporary work do not belong here.
