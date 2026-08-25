# HMASD MCP Post-V1.1 Extension Plan

```text
document_kind=non-operative-extension-roadmap
baseline=HMASD-MCP-CONTROL-PLANE-V1.1-20260820
automatic_authority=none
automatic_wake_pilot_authorized=false
scheduler_serve=false
stage5_authorized=false
agents_sdk_authorized=false
```

This roadmap is deliberately separate from V1.1 acceptance. No section below
starts automatically, changes scientific work, or grants provider, production,
portfolio, lease or Git authority.

## Extension A — wake after a Codex task has ended

Goal: let one external typed event wake one ended Codex task without using a
long MCP wait.

Prerequisites:

- independent live acceptance of the Codex supervisor;
- explicit user authorization for an automatic-wake pilot;
- every wake mutation remains behind `AppServerSessionOwner.submit_effect`;
- `WRITE_STARTED+` remains permanently no-resend for the same effect identity;
- a reversible, harmless, single-task/single-event pilot is frozen first.

MCP supplies state and evidence only. App Server or Automation owns event
subscription and one idempotent wake. This phase adds neither automatic retry
nor a research scheduler.

## Extension B — periodic Doctor and notification

Goal: detect control-plane regression without a resident repair daemon.

A Codex Automation may periodically invoke the read-only Doctor and notify only
for a new ERROR incident, abnormal stale-instance growth or a newly unreadable
source. Incident IDs deduplicate notifications. The automation must not
reconcile, restart, clean, retry, wake scientific work or infer a direction
pause. Snapshots remain under runtime and never become canonical research
state.

This requires a separate automation authorization and configuration review.

## Extension C — persistent Streamable HTTP MCP

Trigger: instance evidence must first demonstrate a real STDIO leak, lock
contention or unacceptable startup cost. A visually large instance count is
not sufficient.

If triggered, observability may move to a local or controlled Streamable HTTP
service with stable instance identity, authentication and health checks.
During migration, STDIO and HTTP outputs must be schema- and value-equivalent.
Orchestrator actor/owner/authority checks remain server-side.

## Extension D — MCP resources, subscriptions and read-only console

Goal: improve browsing and diagnosis without expanding mutation authority.

Candidate capabilities:

- expose schemas, bounded snapshots and incident evidence references as MCP
  resources;
- subscribe to incident and long-effect terminal changes;
- render a local read-only workflow/incident/instance/long-effect console.

The console must not display provider text or scientific result values. Repair
continues through explicit reconcile/recovery operations, never through the
console.

## Extension E — role-shaped MCP tool surfaces

Goal: show Root, EM, CM and Recovery only the tools normally needed for their
roles.

Server-side actor/owner/authority validation remains authoritative; hiding a
tool is never the ACL. Introduce profiles in audit mode first, compare observed
use and denials, then request separate authority before enforcement. Existing
Root/Portfolio/EM/CM semantic ownership does not change.

## Extension F — Stage 5 or Agents SDK

This is the last possible phase and requires a new user-approved design. It may
be considered only after V1.1 and a separately authorized wake pilot have been
stable long enough for Doctor/incident evidence to demonstrate a concrete need
that Root + L1 pairs + file-backed long effects cannot meet.

Any proposal must define cancellation, human takeover, cost, durability,
partial-write recovery, authority isolation and rollback. V1.1 does not imply
Stage 5, Agents SDK, autonomous portfolio work or scientific retry.

## Required iteration loop for every extension

```text
native incident ID
-> minimal reproduction
-> smallest repair or feature
-> focused offline tests
-> harmless bounded live canary
-> independent acceptance record
-> explicit rollout authority
```

Failure at one stage returns to diagnosis. It does not create scientific
failure, direction pause, portfolio disposition, automatic retry or authority
for the next extension.
