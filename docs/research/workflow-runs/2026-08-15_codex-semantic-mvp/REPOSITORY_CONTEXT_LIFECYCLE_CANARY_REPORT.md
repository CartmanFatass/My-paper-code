# Repository Context Lifecycle Canary Report

Synthetic multi-actor rollover and memory-nonauthority canaries for the
repository-owned context lifecycle. Live Codex compact/resume tabs were not
operated in this batch.

```text
baseline_commit=1df15d13dd3b8e2d779508148c07c43033af18ad
implementation_surface=tools/codex_context_lifecycle + schema v3 overlay
test_command=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest tests/codex_semantic_mvp tests/codex_context_lifecycle -q
test_count=277 passed in 96.21s
```

## Canaries

| Canary | Evidence | Result |
| --- | --- | --- |
| Portfolio / Root / EM / CM rollover carry rules | `tests/codex_context_lifecycle/test_rollover.py` | passed |
| Released EM does not auto-rehydrate | `test_working_set.py::test_released_em_does_not_auto_rehydrate` | passed |
| Five-epoch working set excludes closed epochs | `test_working_set.py::test_five_epoch_actor_capsule_stays_current` | passed |
| Memory/summary cannot mutate | `test_memory_nonauthority.py` | passed |
| End-to-end EM propose/reject/apply/rollover/GC | `test_end_to_end_lifecycle.py` | passed |

## Counts from the synthetic end-to-end path

```text
lost obligations = 0
cross-owner leakage = 0
unapproved promotion = 0
silent epoch advance = 0
automatic memory state effects = 0
closed-epoch capsule entries = 0
physical deletions = 0
```

## Known limitation

Live Portfolio/Root/EM/CM compact-then-rollover canaries remain outstanding.
They do not change the synthetic contract. Automatic rehydration stays limited
to Portfolio and Operational Root session-root identity.
