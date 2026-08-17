# Codex Actor Compaction Topology Probe Report

This report records only directly observed probe capabilities. It does not
claim unobserved Codex identity fields, automatic L1/leaf rehydration, or any
scientific, technical, or portfolio disposition.

## Observation method

- Synthetic unit tests in `tests/codex_semantic_mvp/test_topology_probe.py`
  exercise redaction and capability summarization.
- SHADOW templates now register `PreCompact` and `PostCompact` as observational
  handlers. ACTIVE remains the four lifecycle events only.
- Live eight-canary Codex execution was not completed in this implementation
  batch. Therefore no live actor-identity field set is claimed.

## Codex surface

| Field | Observed value |
|---|---|
| Codex version | unobserved in this batch |
| Desktop/CLI surface | unobserved in this batch |

## Events observed by actor kind

| Actor kind | Events observed live |
|---|---|
| Portfolio session root | unobserved |
| Operational Root | unobserved |
| EM | unobserved |
| CM | unobserved |
| Leaf | unobserved |

## Fields present by event

No live hook payloads were captured. Synthetic records may contain only:

```text
timestamp
event
source
session_id
turn_id
agent_id
agent_type
canonical_path
parent_agent_id
parent_canonical_path
payload_key_names
```

Transcript paths, last-assistant prose, tool input, and environment secrets
are excluded from probe records.

## Fields absent

Until a live SHADOW capture exists, treat every actor-identity field as
absent for automatic-rehydration decisions.

## Automatic rehydration supported by actor kind

| Actor kind | Automatic rehydration |
|---|---|
| PORTFOLIO | unproven; do not enable from this report |
| OPERATIONAL_ROOT | unproven; do not enable from this report |
| EM | no |
| CM | no |
| LEAF | no |

## Fallback required by actor kind

| Actor kind | Fallback |
|---|---|
| PORTFOLIO | explicit MCP checkpoint / `context_checkpoint_current` |
| OPERATIONAL_ROOT | explicit MCP checkpoint / `context_checkpoint_current` |
| EM | no automatic compaction rehydration |
| CM | no automatic compaction rehydration |
| LEAF | no automatic compaction rehydration |

## Narrow PreToolUse matcher result

`narrow_pretool_matcher_verified` remains `false`. ACTIVE must not install an
all-tools or unmatched `PreToolUse` handler.

## Frozen capability ceiling for later tasks

Later tasks may not assume automatic EM, CM, or leaf compaction rehydration.
They also may not treat Portfolio or Operational Root automatic rehydration as
proven until a live SHADOW capture shows reliable session-root identity.
