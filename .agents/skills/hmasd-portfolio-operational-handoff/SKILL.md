---
name: hmasd-portfolio-operational-handoff
description: Use when an HMASD Portfolio-owned EM or Operational-Root-owned CM reaches a stage milestone, needs cross-root evidence or authority, receives an owner decision, or risks leaving the shared reconciliation stale.
---

# HMASD Portfolio–Operational handoff

Durable anchor:

`docs/research/workflow-runs/2026-08-11_five-round-research-team/PORTFOLIO_OPERATIONAL_RECONCILIATION_20260814.md`

## Default owner split

Portfolio normally owns EM; the Operational lane normally owns CM. This split
reduces context and preserves provenance; it is not a permission boundary on
the active main Root. Main may create either role or perform either bounded lane
locally, while preserving separate EM-science and CM-technical artifacts.

| Owner | Creates/manages | Own anchor fields |
|---|---|---|
| Dedicated Portfolio session | EM, direction science, Pro/Gemini science, interpretation, allocation | EM/science/portfolio |
| Operational Root | CM, code/runtime, Operator, lease, Git/publication | CM/engineering/lease/application |

Delegated children do not contact across Root trees. When sessions are actually
separate, Roots relay exact owner artifacts;
EM science is not a CM command and CM facts are not science decisions.

## Prospective default path

1. Portfolio creates/reuses `EM_<direction>`. EM writes its meaning-complete
   object and returns the science milestone to Portfolio.
2. Portfolio requests engineering with `PORTFOLIO_EM_TO_ROOT_CM_REQUEST`.
3. In the default split, Operational Root creates/reuses `CM_<direction>`, preserving the exact
   EM paths and semantics. CM returns its milestone to Operational Root.
4. Operational Root records CM/stage/lease facts and sends
   `ROOT_CM_TO_PORTFOLIO_RETURN` with exact CM-authored paths.
5. Portfolio gives that return to its EM for scientific intake. Portfolio then
   sends any object-specific construction/empirical or allocation decision to
   Operational Root for application.

Main may collapse these routing steps locally or directly dispatch both roles;
it need not relay to a second Root for permission it already holds. In that
case the same object/revision, protected semantics, science/technical evidence
separation, claim ceiling, lease boundary, and acceptance standards still
apply. Only use the cross-session packet contracts when a real cross-session
handoff occurs.

```text
PORTFOLIO_EM_TO_ROOT_CM_REQUEST
direction_id=<exact direction>
exact_object_revision=<exact object and revision>
em_owner=<portfolio child task>
science_artifacts=<exact owner-authored paths>
pro_disposition_and_em_intake=<paths or not-yet-required>
technical_question=<bindability|observability|cost|construction|result>
protected_semantics=<treatment/comparator/observable/activity/claim boundary>
allowed_engineering=<bounded scope>
compute_class=<none|light probe|later Root lease required>
return_boundary=<exact CM milestone>
does_not_authorize=<explicit exclusions>
```

```text
ROOT_CM_TO_PORTFOLIO_RETURN
direction_id=<exact direction>
exact_object_revision=<exact object and revision>
cm_owner=<operational-root child task>
technical_artifacts=<exact owner-authored paths>
observed_engineering_fact=<plain causal fact>
science_bearing_ambiguity=<none or exact EM question>
question_relevant_output=<none or accepted output locator>
prospective_cost=<engineering/compute/wall/memory/storage facts>
local_fence=<exact operation only>
direction_continuation=<work that remains live>
portfolio_question=<none or exact decision requested>
```

These contracts are not statuses. Exclude runtime/PID/tab/
receipt streams. Distinguish observed fact, local fence, continuing work and
the owner decision needed.

## Grandfathered work already in motion

All in-flight work continues unchanged to its current exact milestone under its
existing owners. Do not cancel, restart, reparent, resend, rebind coordinates or
pause a run, definition, provider turn, repair or acceptance to install the
split. At that boundary, Operational Root sends the old EM's exact artifacts to
Portfolio and does not follow up that EM again. Portfolio creates any later EM;
Operational Root may reuse the CM. Exact scopes are in
`PORTFOLIO_EM_OPERATIONAL_CM_OWNERSHIP_AMENDMENT_20260821.md`.

## Anchor and delivery

Each separated Root updates its default-owned fields at the milestone; main may
update any in-scope fields while explicitly acting as their semantic owner.
A completed object is never left as awaiting or pending. Give every cross-root
packet a unique marker. Before sending, read the target's latest compact turns;
if the marker exists, do not duplicate it. After one send, re-read the target.
Record `DELIVERED_VISIBLE_TARGET` only when visible and
`ACKNOWLEDGED_BY_<OWNER>` only after an explicit response. A transport timeout
is `SUBMISSION_UNCERTAIN`, never a science or stage decision.

In the default split, Operational Root applies explicit Portfolio actions and
acknowledges the installed CM/stage/lease envelope. Main may instead create a
lease/CM/EM or perform Git integration when within the user's scope, but it must
name the semantic role and preserve all object-specific safety boundaries.
Missing code is CM-semantic work; missing science is EM-semantic work; neither
fact pauses the other domain.
