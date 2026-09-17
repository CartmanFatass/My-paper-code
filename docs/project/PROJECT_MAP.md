# HMASD Project Map

One-page index. The conventions of each area live in that area's `AGENTS.md` (read the nearest file explicitly before edits; Claude Code also has one-line imports).

| Question | Where |
| --- | --- |
| Current governance and owner pause rules | [OPERATING_CONSTITUTION.md](OPERATING_CONSTITUTION.md) |
| Current directions, lead runtime, pause and next steps | [RESEARCH.md](../research/RESEARCH.md) |
| Control-plane sources and operating guide | [map](CONTROL_PLANE_MAP.md), [guidance](CONTROL_PLANE_GUIDANCE.md) |
| Documentation layout and historical evidence | [docs index](../README.md) |
| Scientific and engineering methods | [science](../../.agents/skills/hmasd-scientific-tools/SKILL.md), [engineering](../../.agents/skills/hmasd-research-engineering/SKILL.md) |
| Environment, interpreters and node defaults | [CLAUDE.md](../../CLAUDE.md), [compute configuration](../../.codex/hmasd-compute.toml) |
| Research code layout | [experiments/AGENTS.md](../../experiments/AGENTS.md) |
| Core internals and environment boundaries | [process core](../../ha_ctse_process/AGENTS.md), [environments](../../envs/AGENTS.md) |
| Test commands and automatic scratch cleanup | [tests/AGENTS.md](../../tests/AGENTS.md) |
| Runner conventions | [scripts/AGENTS.md](../../scripts/AGENTS.md) |
| Historical direction/code catalogue | [RESEARCH_MAP.md](../research/RESEARCH_MAP.md) |
| Previously parked defects, to recheck against the current task | [PROBLEM_CACHE.md](PROBLEM_CACHE.md) |

## Routes, in one screen

```
experiments/launchers/main.py → configs/config.py (shim for configs.config_1.Config) → hmasd.agent.HMASDAgent → envs/pettingzoo   original HMASD/UAV route
experiments/launchers/train_multiproc_config_1.py                                             legacy multiprocess route
python -m ha_ctse_process.train → standalone_cli / env_factory / collectors → runners → agent  process-core route (own config)
experiments/candidates/<direction-id>/<attempt>/ + scripts/run_<prefix>_<attempt>.py           research candidates
gnn_hmasd/, manifold_hmasd/                                                                  dormant lineages
```

Dependency direction: entries wire runners; runners depend on agents, collectors, environments
and output owners; adapters may call native kernels. Core packages (`hmasd/`, `ha_ctse_process/`,
`envs/`) do not depend on research candidates, with the recorded exception of
`envs/native/production_backend.py`'s lazy imports (see `envs/AGENTS.md`). Research documents
describe meaning; they never control execution.

Update this index when a nested `AGENTS.md` is added or removed. Update `RESEARCH_MAP.md` when a
direction changes its primary implementation or test path.

## Control-plane source map

The constitution is the sole governance text. Six shared task skills under `.agents/skills/`
carry current methods; native roles supply bounded assistance, with Claude copies generated
by `tools/publish_claude_control.py`. See the [control map](CONTROL_PLANE_MAP.md) for the actual
source chain. Retired specifications and old operating records are in
[archive/project/](../archive/project/); their historical language is not current instruction.
