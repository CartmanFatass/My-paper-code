---
name: hmasd-workflow-anomaly-routing
description: Route an HMASD EM/CM non-core workflow anomaly to a Terra-high Workflow Recovery Manager. Use whenever a direction's science or technical work is impeded by provider transport, Agentify/UI observability, protocol/controller behavior, cross-file workflow state, runtime orchestration, or repeated unchanged-science recovery—not by a missing scientific definition or direction-local implementation defect.
---

# HMASD workflow anomaly routing

Apply this routing before treating a non-core anomaly as an EM/CM retry, a
scientific result, a portfolio signal, or a user boundary.

## Trigger

Trigger on any one of these facts:

- strict provider preflight, identity, native-DOM, controller, tab/ledger, or
  exact-one transport cannot establish its required mechanical fact;
- a protocol, workflow, cross-file state, runtime-control, or observability
  defect needs diagnosis beyond the direction's frozen scientific object;
- the same unchanged-science anomaly recurs, produces no new evidence, or
  would otherwise invite Root/EM/CM to retry, poll, or improvise a workaround;
- an EM or CM detects a non-core code/transport/process anomaly that it cannot
  resolve inside its ordinary scientific or implementation assignment.

Do not trigger for an ordinary science-card ambiguity (return it to the EM), a
direction-local source/runner implementation issue owned by the CM, a real
compute-lease conflict, or a complete result requiring portfolio judgment.

## Required report from EM or CM

Stop only the affected mechanical action. Preserve all frozen science and send
Root one `WORKFLOW_ANOMALY_REPORT` directly; do not report only to a sibling.

```text
WORKFLOW_ANOMALY_REPORT
direction_id=<exact direction>
exact_object=<card/run/transport operation>
observed_fact=<direct fact and observation method>
actions_taken=<bounded actions>
actions_not_taken=<especially no resend/no workaround>
remaining_unknown=<mechanical unknown>
causal_hypotheses=<transport/workflow hypotheses only>
science_impact=<why this is not science evidence or a direction stop>
recovery_scope=<smallest non-core scope>
applies_to=<exact operation, tab, runner, lease, or source surface only>
does_not_imply=<explicitly name direction/science/portfolio actions not fenced>
continuation_owner=<EM, CM, same recovery, or Root and its next authorized work>
root_decision_class=<none|bounded recovery|lease/resource|science change|portfolio>
```

Never label this `BLOCKED`, a portfolio pause, a consumed attempt, or a user
request. Preserve exact provider no-resend after a committed or ambiguous turn.
No-resend fences that exact operation identity only. It does not ban a later
distinct EM-authored provider turn, direction-local repair, CM work, or the
scientific investment unless a separately authorized owner says so.

## Root routing

On receipt, Root must register one task-scoped
`hmasd-workflow-recovery-manager` (Terra-high) before any fresh direction
retry, unless the report is plainly an ordinary CM source/runner fix. Give the
manager the exact object, evidence boundary, permitted source/runtime/UI
diagnosis, validation target, and forbidden science/provider actions.

Every recovery follows this required sequence before returning a conclusion:

1. **Locate governing context.** Read the exact role, `AGENTS.md` route,
   applicable skill/instructions, original assignment, owner handoffs, exact
   incident artifact, and the current task's authority boundary.
2. **Reconstruct and reproduce.** State the smallest safe reproduction from
   direct facts. Use a non-destructive observation or fixture first; do not
   infer root cause from labels, memory, or a sibling's summary.
3. **Explore the causal surface.** Inspect the relevant source, runtime state,
   configuration, interface/tool semantics, and their boundary with the
   observed failure. Identify alternatives, not just the first plausible fault.
4. **Freeze a repair plan.** Name the defect hypothesis, exact files/surfaces,
   reversible repair, tests that distinguish it from alternatives, and actions
   that remain forbidden. Return to Root first only if that plan would expand
   authority or alter science.
5. **Repair and validate.** Within the assigned authority, implement the
   smallest repair, run focused regression and live/non-destructive validation,
   and verify the original reproduction no longer occurs. Preserve unrelated
   workspace edits.
6. **Return one consolidated result.** Report context read, reproduction,
   alternatives, repair/plan, tests, residual risk, and the smallest next
   authority/action. A recovery is not complete merely because an agent has
   inspected a page or observed one status field.

Use this generic dispatch block:

```text
WORKFLOW_RECOVERY_ASSIGNMENT
incident_id=<stable common-cause id>
exact_object=<affected workflow surface>
governing_context=<roles, instructions, skills, handoffs, original assignment>
incident_artifacts=<exact paths/records>
reproduction_boundary=<safe observation or fixture>
causal_surface=<source/runtime/config/tool interfaces to inspect>
authorized_repair_and_validation=<bounded source/runtime/UI work and tests>
forbidden_actions=<science/allocation/provider/compute/Git or other exclusions>
completion=<consolidated context→reproduction→exploration→plan→repair→test report>
```

For an Agentify/provider anomaly, Root's recovery dispatch must additionally
require the manager to read before acting: the exact frozen request and every
incident archive; the complete `hmasd-agentify-transport` skill; the complete
canonical `AGENTIFY_TRANSPORT_INSTRUCTIONS.md`; and the current relevant
Agentify source/runtime surfaces for MCP strict review, provider picker,
tab/URL binding, and durable ledger behavior. State explicitly that the work is
an MCP-controlled browser task: inspect the native Agentify registry and live
provider DOM through the approved Agentify MCP primitives, reconcile that
evidence with loaded source/runtime, and never substitute generic browser
assumptions, hidden DOM, ordinary query, or a non-MCP send route. The recovery
return includes the context read and the exact source/runtime surfaces used.

Use this required dispatch block for that class of recovery:

```text
AGENTIFY_WORKFLOW_RECOVERY_ASSIGNMENT
incident_id=<stable common-cause id>
direction_id=<exact direction>
exact_object=<strict operation or workflow surface>
frozen_request_and_archives=<absolute exact paths>
context_required=<complete transport skill; complete manual; MCP tool semantics;
                  current strict-review/picker/tab/ledger source and runtime>
observed_fact=<pre-send/committed facts only>
allowed_validation=<native MCP tab/registry/DOM inspection; focused offline or
                    non-sending live validation; bounded repair if authorized>
forbidden=<provider prompt/send/bootstrap/ordinary fallback; science/card/claim/
           coordinate/lease/compute/Git changes>
completion=<one consolidated recovery result with context read, source/runtime
            reconciliation, validation, residual risk and exact next action>
```

Keep one root cause and every directly induced workflow consequence in that
same recovery-manager task. Reuse it with a follow-up assignment until its
consolidated recovery result; do not spawn a second recovery manager for a
production-tab variant, later preflight, or other downstream manifestation of
the same anomaly. Create a new recovery task only when direct evidence shows a
different root cause and a disjoint repair scope.

The recovery manager may repair and validate the workflow surface. It must not
alter treatments, comparators, claims, thresholds, coordinates, allocation, or
Git; it sends no provider turn unless Root gives a later explicit, separate
authorization after recovery.

## Semantic return fence

Every recovery conclusion names: `applies_to`, `does_not_imply`,
`continuation_owner`, and `root_decision_class`. `AUTHORITY_BOUNDARY` means
only that the named recovery action requires an outside authorization; it is
never a direction pause. For a provider operation with uncertain commitment,
state whether the exact operation is no-resend, then separately state the
remaining scientific-stage work and the smallest authority needed for any
distinct future turn. Never substitute a child-local transport limitation for
a Root workflow decision.

## Recovery return

Return directly to Root with observed fact, exact object, actions taken and not
taken, validation performed, remaining unknown, causal hypotheses, and the
smallest next authority/action. Root reports a completed recovery or a genuine
external boundary to the main session, relays only a decision-level scientific
milestone to portfolio, and never relays routine workflow mechanics.
