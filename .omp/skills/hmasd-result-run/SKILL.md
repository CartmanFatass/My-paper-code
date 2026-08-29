---
name: hmasd-result-run
description: Prepare and execute one observed result-bearing local command.
---

# HMASD Result Run

## Purpose

Make one exact local train, evaluate, or analyze command observable and
reproducible without turning run metadata, terminal success, or metrics into
approval or scientific authority. Exactly one Experiment Operator owns exactly
one command from launch through its terminal witness. No CM, Reviewer,
Verifier, or second Operator shares that command ownership.

## Inputs

Before dispatch, CM supplies:

- direction, cycle, run, and assignment IDs;
- shell-free exact argv and canonical cwd;
- exact code/baseline, config, data, RNG, parameter, and environment
  identities;
- canonical input and output paths plus every filesystem, process, network, and
  result Effect;
- duration, peak-memory, worker/thread/device and other resource bounds;
- scientific activity predicate, completion checks, and stop condition;
- frozen question/evidence/engineering-contract refs; and
- current manifest revision plus any previous terminal-witness ref.

The Operator may execute only these frozen bytes. Missing, contradictory,
noncanonical, unsafe, or changed fields return a refusal before launch. A
convenient shell wrapper, different seed, reduced comparator, alternate output
root, or relaxed stop condition is a different command and requires a new CM
contract; it is not local recovery.

## Bounded cycle

1. Validate exact argv, canonical paths, code and input identity, Effects,
   output targets, resource bounds, activity predicate, completion checks, and
   stop condition. Bind them to one prepared `runner-spec.json` and manifest
   identity.
2. Run `scripts/hmasd_resource_preflight.py` before any approval logic. Refuse
   unsafe memory or resource plans mechanically; reduce, batch, or shard them
   through a replacement CM contract rather than asking permission to
   overcommit.
3. For an estimated duration over 7200 seconds, attempt one
   `hmasd-reviewer` performance-reasonableness review from the frozen evidence.
   Reviewer unavailability is an evidence gap, not approval. Return exit code
   `8` with one user decision request that binds the exact command, evidence,
   resources, Effects, and stop condition. Approval resumes only those same
   bytes.
4. At or below 7200 seconds, or after approval of the exact long-run request,
   inspect duplicate manifests and live PID/process identity, then dispatch
   exactly one `hmasd-experiment-operator`. That Operator uses Hub to own one
   `scripts/hmasd_run.py execute` process.
5. Observe the same process until a terminal fact. Publish one immutable
   `scripts/hmasd_operator_result.py` witness containing the run ID, manifest,
   stdout/stderr paths, terminal status, exit code, and observation timestamp.
   Reconcile the manifest terminal lifecycle and return those exact refs.

The bounded cycle has one prepared manifest, one Operator, one process, and one
terminal witness. A user response to the frozen decision request or an
observation of that exact process is the only continuation. Never poll through
a successor assignment, relaunch an unknown or partially observed process, or
reinterpret metrics.

## State writes

- The single Experiment Operator writes `manifest.json`, `runner-spec.json`,
  stdout/stderr, exit-code data, produced artifact refs, and its immutable
  terminal witness in the ignored
  `temp/directions/<direction-id>/exp/<run-id>/` tree through the run and
  terminal-witness CLIs.
- CM coordinates but does not execute the process or write its manifest.
  Reviewer and Verifier observe their separately frozen questions and never
  acquire command ownership.
- This Skill records no scientific conclusion, acceptance token,
  Portfolio/EM/CM state, lifecycle action, provider ledger, or Agentify state.
  Accepted scientific result Markdown/JSON remains EM-authored through the
  Artifact Writer.
- Process exit zero and terminal `SUCCEEDED` mean only that the frozen command
  completed as observed. They do not establish scientific acceptance.

## Returned result envelope

Return the common v1 envelope with `role: "hmasd-experiment-operator"` for the
terminal worker. Include the terminal-witness path in `artifact_refs` and use:

```json
{
  "kind": "run",
  "run_id": "<run-id>",
  "manifest_ref": "temp/directions/<direction-id>/exp/<run-id>/manifest.json",
  "terminal_status": "SUCCEEDED",
  "exit_code": 0
}
```

For a long-run boundary, use `status: "BLOCKED"`, `materiality: "USER"`, and
one exact `decision_requests[]` entry. Advisor or Reviewer output is never an
approval token. On any terminal status, return observed paths and limitations
without a scientific interpretation.

## Failure handling

Refuse invalid or mutable argv, noncanonical paths, identity mismatch, duplicate
ownership, unsafe resources, unbounded workers, undeclared Effects, PID
mismatch, manifest CAS conflict, or a conflicting terminal witness. Preserve
the original request and inspect the exact manifest/process before classifying
an unknown outcome. Never start a successor for a partially observed command.

Record the observed terminal state and return exit code `6` for an observed
resource conflict, `8` for the user decision boundary, or `1` for another
directly observed failure. If terminal observation is lost, retain the same run
identity and exact re-observation condition; do not manufacture an exit code or
claim completion.

## Deletion condition

Delete this Skill when an approved run helper enforces the same frozen command,
canonical paths, one-process ownership, resource refusal, exact long-run
decision boundary, immutable terminal witness, and no duplicate state writer.
