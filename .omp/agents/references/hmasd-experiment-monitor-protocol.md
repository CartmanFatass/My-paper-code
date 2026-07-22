# HMASD Rebuildable OMP Monitor Protocol

## Assignment

One Monitor task observes one authorized run. The assignment provides a valid
manifest containing the stable run ID, named persistent `hub` process, absolute
run root and authoritative status path, registered progress sources and allowed
fields, deadline, exact task name `monitor-<run-id>` and terminal idempotency
fields.

The Monitor is a non-isolated low-cost OMP background job. It is never a
persistent role and has no heartbeat, session route or controller callback. Its
terminal value is delivered through automatic task result delivery and retained
through `agent://` output and `history://` transcript.

## Bounded observation

Inspect authoritative status first. A terminal authoritative state takes
precedence over process existence, counters, nominal duration or ETA. For a
nonterminal state, inspect the named `hub` process and the smallest registered
progress evidence. Use bounded `hub` waits and log reads rather than continuous
polling, sleeps or broad scans.

Running progress remains inside the Monitor job unless Main explicitly asks.
Completed training counters with nonterminal status mean finalization is
pending, not failure. Missing or malformed evidence is actionable only after
bounded read-only diagnosis inside the registered run root.

## Terminal result

At terminal state, actionable operational error or deadline, return:

```text
run=<run-id>
state=<terminal state>
phase=<phase or unavailable>
status=<absolute authoritative status path>
payload=<result path, direct-error path, or none>
reason=<one actionable line or none>
idempotency_key=<run-id>:<terminal-state>:<status-updated-at>
```

Never launch, restart, repair, extend or scientifically interpret the run.
Never mutate source, project control, experiment evidence or the manifest.

## Reconstruction

A root OMP restart does not stop a persistent `hub` run. On recovery, the
Controller reads the manifest and authoritative status, checks `hub` process
state and current task roster, and creates `monitor-<run-id>` only when no
matching task exists and its terminal idempotency key has not already been
accepted. A nonterminal replacement resumes bounded observation; if status is
already terminal, a bounded replacement returns that retained payload
immediately.

A missing process with nonterminal status is an actionable operational error,
not permission to restart. A replacement Monitor uses the same manifest and
returns the same terminal idempotency key. The Controller accepts one terminal
result per key. No heartbeat, persistent monitor session or route resolver is
created.
