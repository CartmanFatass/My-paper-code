---
name: hmasd-result-run
description: Prepare, execute, observe, reconcile, or cancel one HMASD result-bearing local command without duplicate ownership.
---

# HMASD Result Run

One hmasd-experiment-operator leaf owns one exact train, evaluate, or analyze command from launch through terminal observation.

## Contract

1. Freeze direction/run/assignment IDs, argv, canonical native-host cwd, code SHA, parameters, output paths, scientific activity predicate, duration, memory estimate, and current manifest revision.
2. Run scripts/hmasd_resource_preflight.py before approval logic. Unsafe memory is reduced, batched, or sharded.
3. Above 7200 seconds, attempt one focused performance review and return an exact exit-8 user decision request. Approval resumes only the identical frozen request.
4. Check duplicate claim/manifests and process identity before launch.
5. Launch exactly one scripts/hmasd_run.py execute in one foreground Codex exec session. If the tool yields a session ID, the same Operator continues that session until terminal; no second Operator or detached shell owns it.
6. Record the exact manifest lifecycle and return terminal status/artifacts. Do not reinterpret metrics or start a successor.

Use native Windows Python and paths in this checkout. The run helper keeps legacy manifest field names for compatibility but supplies platform-specific identity values. An identity that cannot be proven is UNKNOWN/conflict and is never signaled or relaunched blindly.
