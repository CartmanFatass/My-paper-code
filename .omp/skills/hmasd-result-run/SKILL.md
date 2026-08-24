---
name: hmasd-result-run
description: Prepare and execute one observed result-bearing local command.
---

# HMASD Result Run

## Purpose

Make one exact local train, evaluate, or analyze command observable and
reproducible without turning run metadata into approval authority. One
Experiment Operator owns one command from launch through terminal return.

## Inputs

- Direction and run IDs, assignment ID, exact argv, canonical cwd, code SHA,
  parameters, output paths, and scientific activity predicate.
- Estimated duration and peak memory, frozen question/evidence SHAs, and the
  current run-manifest/revision state.
- CM's bounded assignment and any previous terminal observation.

## Bounded cycle

1. Validate the exact command, canonical paths, code identity, parameters,
   output targets, duration estimate, memory estimate, and activity predicate.
2. Run memory/resource preflight before any approval logic. Refuse an unsafe plan;
   reduce, batch, or shard it rather than asking for permission to overcommit.
3. For estimates over 7200 seconds, attempt one `hmasd-reviewer` performance
   review from frozen evidence. Record unavailability as an evidence gap, then
   return exit code `8` with a frozen decision request binding all command and
   evidence fields. Approval resumes exactly that request.
4. For estimates at or below 7200 seconds, inspect duplicate manifests and PID
   identity, dispatch exactly one Operator, and use Hub to own one
   `hmasd_run.py execute` process.
5. Observe that one process to terminal completion, write the exact manifest
   lifecycle, and return. Never start a successor or reinterpret metrics.

The cycle has one prepared manifest and at most one owned process. A decision
response or terminal observation is the only wake-up for continuation.

## State writes

- The single Operator writes the local manifest, stdout/stderr, exit code, and
  observed artifact references through the run CLI in the ignored direction
  `temp/` tree.
- The Skill records no scientific conclusion, Portfolio/EM/CM state, approval
  token, or Agentify ledger state.
- Accepted result Markdown/JSON is authored by EM through Artifact Writer.

## Returned result envelope

Return the common v1 envelope with `role: "hmasd-experiment-operator"` for the
terminal worker and payload:

```json
{
  "kind": "run",
  "run_id": "<run-id>",
  "manifest_ref": "temp/directions/<direction-id>/exp/<run-id>/manifest.json",
  "terminal_status": "COMPLETED",
  "exit_code": 0
}
```

For a long-run boundary, use `status: "BLOCKED"`, `materiality: "USER"`, and
one exact `decision_requests[]` entry. Advisor or Reviewer output is never an
approval token.

## Failure handling

Refuse invalid argv, paths, identity, duplicate ownership, unsafe memory plans,
PID mismatch, and manifest CAS conflicts. Preserve the original request and
never relaunch an unknown or partially observed process. Record the observed
terminal state and return exit code `6` for observed resource conflict, `8` for
user decision, or `1` for another directly observed failure.

## Deletion condition

Delete this Skill when an approved run helper provides exact command identity,
one-process ownership, resource refusal, user-boundary continuation, and
terminal observation with no duplicate state writer.
