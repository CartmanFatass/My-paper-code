# HMASD Project Map

One-page index. The conventions of each area live in that area's `AGENTS.md` (Codex reads them
hierarchically; Claude Code reads the one-line `CLAUDE.md` beside each, which imports it).

| Question | Where |
| --- | --- |
| Collaboration, decision ladder, unattended operation, capacity, Git under concurrent sessions | [`AGENTS.md`](../../AGENTS.md) |
| Environment, interpreters, commands | [`CLAUDE.md`](../../CLAUDE.md) |
| What research code may and may not build; core versus research tier | [`ENGINEERING_SCOPE_SPEC.md`](ENGINEERING_SCOPE_SPEC.md) |
| Candidate layout rule, directory → direction map with status, native backends | [`experiments/AGENTS.md`](../../experiments/AGENTS.md) |
| Process-core route internals, subproc rule, checkpoint owners | [`ha_ctse_process/AGENTS.md`](../../ha_ctse_process/AGENTS.md) |
| Environments and the native boundary, device caveat | [`envs/AGENTS.md`](../../envs/AGENTS.md) |
| Test layout, naming, commands, basetemp rule | [`tests/AGENTS.md`](../../tests/AGENTS.md) |
| Runner naming, interpreter rule, admission, queues | [`scripts/AGENTS.md`](../../scripts/AGENTS.md) |
| Which documentation tree is an authority; document families | [`docs/AGENTS.md`](../AGENTS.md) |
| The 22 current directions, their code and test paths, script prefixes | [`../research/RESEARCH_MAP.md`](../research/RESEARCH_MAP.md) |
| Lifecycle, priority, capacity, decisions, audit ledger | [`../research/portfolio/PORTFOLIO.md`](../research/portfolio/PORTFOLIO.md) |
| Evidence classes and the §11 calibration | [`../research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`](../research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md) |
| Parked defects that block interpretation | [`PROBLEM_CACHE.md`](PROBLEM_CACHE.md) |
| Measured throughput numbers and the rules they support | [`EFFICIENCY_PRACTICES.md`](EFFICIENCY_PRACTICES.md), [`ENGINEERING_ADDITIONS.md`](ENGINEERING_ADDITIONS.md) |
| The 14 closed or absorbed directions | [`../research/legacy/directions/README.md`](../research/legacy/directions/README.md) |

## Routes, in one screen

```
main.py → config.py (shim for config_1.Config) → hmasd.agent.HMASDAgent → envs/pettingzoo   original HMASD/UAV route
train_multiproc_config_1.py                                                                  legacy multiprocess route
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
