---
name: hmasd-workflow-anomaly-routing
description: Use when an HMASD worker repeatedly cannot complete an authorized task because a provider UI, protocol, controller, workflow state, or runtime orchestration surface is malfunctioning.
---

# HMASD workflow anomaly routing

## Purpose

Route one repeated non-core failure to one recovery owner without turning the
incident into science, portfolio policy, or a larger engineering program.

Do not use this route for a science-card ambiguity, ordinary CM implementation
work, a real compute conflict, or a complete result awaiting interpretation.

## Detector report

Stop only the affected mechanical action and report:

```text
WORKFLOW_ANOMALY_REPORT
incident_id=<stable common cause>
exact_object=<affected operation or workflow>
original_outcome=<observable task result that failed>
observed_fact=<direct evidence and method>
actions_taken=<bounded actions>
actions_not_taken=<especially no resend or workaround>
remaining_unknown=<mechanical unknown>
protected_invariants=<facts that must not change>
science_impact=<why this is not scientific evidence>
```

Never return generic `BLOCKED`, infer user action from a diagnostic hint, or
pause unrelated work. Exact provider no-resend applies only to an operation
with Send/turn/identity/ambiguity evidence.

## Main routing

The active main Root owns the recovery decision. It may perform the bounded
recovery locally or reuse one task-scoped Workflow Recovery Manager for the
same common cause. Do not create serial recovery owners for downstream symptoms.

The assignment must include the original observable outcome, one safe
reproduction, protected invariants, exact context/evidence, bounded writable
surface, allowed external effects, and direct end-to-end acceptance.

For Agentify, include the frozen request/archive and current native Agentify
tool/source facts. Treat the task as MCP-controlled visible-browser work. The
normal recovery starts from the capabilities already exposed to the Operator:
visible observation, mouse/keyboard action, bounded page waiting, and
re-observation. Do not replace these with hidden DOM, ordinary-query fallback,
another provider send, or a new control-plane layer.

## Required recovery behavior

The recovery owner:

1. Restates `original_outcome` and safety invariants.
2. Reproduces once safely and identifies the smallest causal break.
3. Uses or repairs the smallest existing capability that can restore the
   outcome.
4. Runs focused regression checks and one end-to-end acceptance run.
5. Removes or marks obsolete any incident machinery superseded by the repair.
6. Returns only direct outcome evidence or a genuine external boundary.

Source edits, tests, helpers, receipts, diagnostics, and documentation are not
recovery completion. A preferred UI trace is not the outcome. If the final
visible state and safety invariants are proven, missing incidental trace data
cannot invalidate success.

Every new mechanism declares `complexity_delta=steps_removed|steps_added` and
must reduce the ordinary production path. Historical incident detail never
enters an automatically loaded Operator recipe.

## Boundaries

The recovery owner sends no provider turn and changes no science, allocation,
coordinates, leases, or Git. It does not request application lifecycle actions
as a substitute for using the current visible UI. A true boundary requires a
user credential/physical action, irreversible external risk, or explicitly
excluded external effect.

Return:

```text
WORKFLOW_RECOVERY_RESULT
status=RECOVERED|EXTERNAL_BOUNDARY
original_outcome=<named result>
outcome_evidence=<direct proof or absent>
root_cause=<causal explanation>
changed_paths=<exact paths or none>
complexity_delta=<steps removed>|<steps added>
validation=<regressions plus end-to-end acceptance>
protected_invariants=<direct checks>
remaining_unknown=<none or exact unknown>
```

The result is evidence for the invoker. It never decides scientific meaning,
portfolio allocation, production acceptance outside its scope, or thread/goal
status.
