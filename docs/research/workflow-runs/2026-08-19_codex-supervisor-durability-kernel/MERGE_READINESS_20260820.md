# Durability kernel v1 merge readiness

```text
prior_external_review=REVISION_REQUIRED on b520429e
final_corrective_commit=9ec92377
prompt_pin_commit=5f06bbfc
baseline=04eb640f4090993b251b204096cff26b44350b90
branch=codex-supervisor-durability-kernel-v1
live_acceptance=absent
automatic_wake_pilot_authorized=false
Stage5_authorized=false
scan_package=[]
```

This record is repository integration evidence. Merging into `aggressive`
is not live App Server, shadow, or pilot acceptance.

## Final corrective slice

`9ec92377` closes the remaining `b520429e` review defects:

1. `submit_effect(request_override=...)` materializes the final request inside
   the owned write-start `BEGIN IMMEDIATE` transaction. That transaction
   commits `request_json`, owner `SUBMITTING`, effect `WRITE_STARTED`, raw
   stdin, and `rpc_requests` before `send_prepared()`.
   `record_effect_write_start` fails closed if an ambient transaction exists.
2. Stored resume freshness compares only `raw_message_seq` values, resolving
   `thread_snapshots.last_event_seq` through `normalized_events`.
3. `WakeBatchStore.set_state` refuses generic `PREPARED → SUBMITTING`.

Independent local review of transaction ownership, raw-sequence causality, and
domain-only SUBMITTING paths returned no Critical or High finding.

## Tests

Focused:

```text
python -m pytest tests/codex_supervisor/durability/test_kernel_closures.py
  tests/codex_supervisor/durability/test_session_owner.py
  tests/codex_supervisor/durability/test_wake_cutover.py
  --basetemp=.../.tmp_durability_final2
result=64 passed
```

Pre-merge full:

```text
python -m pytest tests/codex_semantic_mvp tests/codex_context_lifecycle
  tests/codex_supervisor
  --basetemp=.../.tmp_premerge_final2
result=645 passed
interpreter=C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe
```

`scan_package() == []` before merge.
