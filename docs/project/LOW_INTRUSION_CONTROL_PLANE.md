# Low-Intrusion Control Plane

Semantic drift is inevitable.  The control objective is drift containment at
promotion/authority boundaries.  Normal turns and auto-compaction receive zero
control-plane prompts.  Subagent feedback is evidence, not a parent command.
Supervisor owns liveness, not semantic interpretation.

## Normal-operation budget

| Event | Prompts | Forced turns | Shared semantic mutation |
|---|---:|---:|---:|
| Ordinary turn/tool call/assistant Stop/child start/ordinary return | 0 | 0 | 0 |
| Native auto-compaction | 0 | 0 | 0 |
| Bootstrap, material incident, explicit status, cross-owner packet | one bounded receipt | 0 | owner-controlled |

Behavioral `Stop`, `PreToolUse`, `SubagentStart`, `SubagentStop`, `SessionStart`,
`PreCompact`, and `PostCompact` Hooks are not part of the active path. Native
auto-compaction remains the sole automatic compaction mechanism.

## Artifact spine

`PROJECT_MAP.md` is the sole stable codemap. `CURRENT_WORK.md` is a pointer
index. Active requirements live in `PROJECT_REQUIREMENTS.toml`; assignments and
results are human-readable, file-backed artifacts. A result is scope-local
evidence until its owner explicitly intakes or promotes it.

Nontrivial code assignments name exact files or bounded discovery roots, exact
symbols, a `PROJECT_MAP` route, architecture role, state owner, inputs, direct
consumer, and non-target surfaces. Abstract labels such as “pipeline” or
“backend” do not establish scope.

## Incident scope

`E0` is observation, `E1` an exact-operation incident, `E2` assignment recovery,
`E3` a domain-owner decision, `E4` a cross-owner decision, and `E5` a concrete
user-authority requirement. E1/E2 do not reach the user by default. No exact
operation may automatically become a Root/session incident, direction
disposition, Portfolio decision, or user request. Generic `blocked` wording is
an unscoped claim without an impact envelope.

## Execution boundary

Result-bearing execution uses a registered semantics-preserving C++ backend and
parallel route where available. Every launch records a current CPU/memory
preflight and the CM-selected run-specific width. There is no project-wide
worker default/cap and no fixed portfolio direction cap. Serial/Python routes
are debug/reference only. Runtime claims use measured or transparently
extrapolated samples; implausible toy runtimes route to CM as implementation
anomalies, not scientific stops.

The explicit supervisor is invoked by an operator through start/status/stop
commands. It reports only bounded READY, INCIDENT, STATUS, and STOPPED receipts;
heartbeats and unchanged health remain external.
