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

`docs/HR/RESEARCH_DIRECTION_DASHBOARD.md` is the human-readable Portfolio
status projection, with queue semantics in
`docs/HR/RESEARCH_QUEUE_SCHEMA.md`. It does not replace owner artifacts or the
shared reconciliation anchor. Portfolio updates it in the same active turn as
any primary-queue, scientific-disposition, owner, next-event or revisit change;
Operational Root contributes exact engineering/activity facts through the
normal handoff. Mechanical coverage must equal the set of
`docs/research/candidates/` directories exactly once. Missing materially
invested custody is visible as `ORPHAN_RECOVERY`; a preliminary unowned concept
is `TRIAGE_UNOWNED`. Aggregate counts and generic stop words never satisfy this
obligation.

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

## Implementation delegation boundary

Within a CM-owned direction or named shared-component engineering stage:

```text
implementation_role=architecture|orchestration|integration|diagnostic|technical_acceptance
primary_source_implementer=registered_implementer
mandatory_implementation_delegation=substantial|production_capable|novel|native|exact_arithmetic|science_conformance_critical
mandatory_implementation_delegate=exactly_one_registered_implementer
cm_local_source_edit_authority=small_bounded_low_risk_integration_or_diagnostic_only
implementation_threshold_basis=semantic_and_risk_scope_not_line_count
threshold_crossing_handoff=next_atomic_consistent_boundary|preserve_existing_edits_and_evidence|freeze_remaining_task|handoff_existing_candidate
semantics_critical_implementer=hmasd_implementer_sol_high
routine_reversible_implementer=hmasd_implementer_terra_high
semantics_critical_review=exactly_one_independent_hmasd_reviewer_after_coherent_candidate
review_acceptance=advisory_reviewer|cm_final_technical_acceptance
routine_low_risk_review=not_automatic
verifier_route=optional_proof_sized_distinct_risk_only
```

CM owns architecture, integration, diagnosis, file semantics, and final
technical acceptance; it is not the primary source implementer. Every
substantial, production-capable, novel, native, exact-arithmetic, or
science-conformance-critical source implementation is frozen and delegated to
exactly one registered Implementer. Authority, RNG, exact-arithmetic,
science-conformance, probability, gradient, replay, recurrent-state,
checkpoint, and result-meaning semantics use `hmasd-implementer`/Sol-high.
`hmasd-implementer-terra`/Terra-high is retained only for routine, reversible
engineering with frozen semantics.

CM-local source edits are limited to small, bounded, low-risk integration or
diagnostic work. The threshold is semantic and risk scope, not line count. If
local work discovers or crosses a mandatory-delegation category, CM stops at
the next atomic consistent boundary, preserves existing edits and evidence,
freezes the remaining task, and hands the existing candidate to the
Implementer. It never reverts or restarts work merely to delegate it.

After a coherent semantics-critical candidate exists, exactly one independent
Reviewer examines the named material risk. Review is advisory and CM retains
technical acceptance. Routine low-risk work has no automatic Reviewer, no
routine Verifier, and no automatic re-review; Verifier is optional only for a
proof-sized distinct risk.

## Execution boundary

Result-bearing execution uses a registered semantics-preserving C++ backend and
parallel route where available. Every launch records a current CPU/memory
preflight and the CM-selected run-specific width. There is no project-wide
worker default/cap and no fixed portfolio direction cap. Serial/Python routes
are debug/reference only. Runtime claims use measured or transparently
extrapolated samples; implausible toy runtimes route to CM as implementation
anomalies, not scientific stops.

Within a CM-owned engineering scope, actual train, evaluate, or analyze
execution and every leased or question-relevant command are Operator-only
execution. CM is the orchestration and technical-intake owner: it freezes the
exact command, manifest, preflight, scientific-activity criterion, and output
paths, then dispatches exactly one `hmasd-experiment-operator` for that command.
The Operator alone launches once, owns and awaits the foreground process
handle, records terminal facts, and returns. CM remains responsive and acts on
the execution only after the child returns terminal evidence; CM launch
authority and foreground process-handle ownership for actual execution are
none.

For a command expected to outlast an ordinary active Codex turn, CM returns the
complete run-ready packet and the current Operational Root dispatches exactly
one Operator, then ends normally. The return path is an external Codex App
thread heartbeat targeting that same current Operational Root. HMASD defaults
to estimate-driven scheduling: estimate the minutes from arming through the
next observable terminal or decision boundary, including prelaunch delay, and
select `clamp(ceil(estimate), 15, 60)` minutes. Use 30 minutes only when no
credible estimate exists. Before launch, confirm that the heartbeat targets
the current Operational Root, binds the exact watched object and receipt paths,
is ACTIVE, and has the selected 15--60-minute schedule. If any cannot be
established, return exact
`CONTROL_PLANE_CAPABILITY_BOUNDARY` with `launched=false`; do not launch. Every scheduled turn performs exactly one bounded check of the exact
native child or one point-in-time check of its named durable terminal receipt.
A nonterminal check may re-estimate and update the cadence inside 15--60
minutes, then ends normally with the heartbeat ACTIVE. A terminal check
collects the ordinary Operator-to-CM native return through Root. Coverage stays
ACTIVE through CM intake and required owner reconciliation/relay and pauses
only after the complete chain. `no active Operator` alone is not a pause
condition while a terminal receipt or decision handoff is unreconciled. Any
unrelated Root turn arriving during coverage must preserve or complete the
exact watch before pausing it.

The same Root task's goal auto-continuation is paused or absent throughout the
covered wait. Rapid goal continuations are not scheduler-liveness evidence and
must not compete with or substitute for the external heartbeat. If this
condition cannot be established before a long Operator dispatch, fail closed
with `launched=false`.

`ACTIVE + target + schedule` proves configuration, not scheduler liveness.
After any App/session, target or heartbeat-configuration change, one real
same-thread scheduled canary must fire before a long Operator launch. Synthetic
process or terminal-receipt tests do not satisfy this boundary.

Use the same estimate-driven heartbeat for an active or unknown-duration long
effect expected to outlast an ordinary turn. A known future time gate with no
active CM, Operator, foreground command, or admitted activity instead uses one
exact scheduled same-task return at the boundary and no intermediate polling
turns. A file-backed `PRESTART` lease is a dormant future authorization record,
not a current Goal blocker, process, worker, resource reservation, or session
hold.

Every no-immediate-action handoff has one explicit continuity class:

```text
CURRENT_WORK=one exact active owner and current action
DORMANT_SCHEDULED_CONTINUATION=no active worker expected|one exact scheduled owner|one next event
IDLE_COMPLETE=no unfinished obligation|no scheduled owner required
UNOWNED_STALL=unfinished obligation|no active worker|no valid scheduled owner
```

Only `UNOWNED_STALL` is a workflow anomaly. Never keep or create a placeholder
subagent merely to make a session look active. Every quiescent return exposes
`continuity_state`, `active_worker`, `continuity_owner`, and `next_event`.

Goal mode covers finite actionable tranches, not indefinite continuity. Do not
create a Goal whose only remaining completion condition is elapsed time or an
external event. Once the future continuation has a durable owner, Goal mode is
paused, cleared, or absent until the event becomes actionable. A legacy blocked
Goal is only a local rapid-retry circuit breaker and never project/workflow
status. The other Root does not mirror it. If the product surface cannot pause
or clear it, report `GOAL_HEARTBEAT_INTERLOCK_REQUIRED` once; do not consume
repeated Goal turns or create a dummy worker.

The heartbeat is an external scheduled turn trigger, not event-driven wake.
`workflow_await_event`, global events, native-child signals, subagents, and
receipts can release or assist only a wait inside an already-active turn; they
never schedule, retry, restart, or wake an ended Codex task. A content-free
signal is followed by the ordinary native return through collaboration. The
Operator exclusively owns the one foreground handle and named durable terminal
receipt; neither a heartbeat nor later receipt reconciliation may relaunch or
duplicate the command. Signals, receipts, and heartbeat observations are
execution facts only and never scientific conclusions, interpretation,
acceptance, or disposition.

A bounded non-experiment preflight, probe, or rehearsal is defined by its side
effects and preserved invariants rather than a closed command-name list. A
non-exhaustive example list includes environment, PATH/native toolchain/FFI,
launcher/interpreter/backend, serialization, fresh-root, CPU/memory/resource,
and compilation/import/ABI/help/test-only checks. It cannot begin train,
evaluate, or analyze work; consume a lease; or create or advance
question-relevant outputs or frontiers. Crossing any of those boundaries makes
the command actual execution and requires the Operator route. An ordinary
bounded tool call may wait only for its own short non-experiment command. Root
and CM child waiting uses collaboration or event surfaces. Root and CM must
never hide an aggregate indefinite polling loop inside one `functions.exec`
call, including `while (true)` repeatedly calling `tools.write_stdin`.
Long-Operator completion detection likewise forbids CPU, file, frontier,
partial-value, `functions.exec`, `write_stdin`, and hidden-loop polling. The one
scheduled point-in-time check may inspect only the exact native child or the
named durable terminal receipt.

This is a static contract and regression boundary, not a behavioral hook. The
repository cannot intercept a live `functions.exec` payload without a platform
hook. It likewise cannot intercept a live CM `apply_patch` or other
source-writing payload without a platform hook. The low-intrusion policy above
disables behavioral hooks.

The explicit supervisor is invoked by an operator through start/status/stop
commands. It reports only bounded READY, INCIDENT, STATUS, and STOPPED receipts;
heartbeats and unchanged health remain external.
