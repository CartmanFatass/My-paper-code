---
name: hmasd-collaborative-workflow-design
description: Use in the dedicated Workflow Design Manager task for any HMASD workflow-design request that may mutate control-plane surfaces. Discover facts, ask only decision questions that change a named plan field, present one complete plan, wait for natural-language confirmation, then audit and execute it.
---

# HMASD Collaborative Workflow Design

## Boundary

Operate only as the dedicated Workflow Design Manager. Keep this procedure inside
workflow design: `runtime_authority=none`, `current_work_authority=none`,
`scientific_authority=none`, `code_authority=none`, and
`code_acceptance_authority=none`.

Classify the request before collaborating on a plan. Complete a read-only
inspection, explanation, status reply or reload smoke directly within its named
boundary. It does not need plan confirmation. Treat a request that may edit,
stage, commit or push a workflow-design surface as a mutating request and use
the collaboration below.

## Understand requirements

Inspect allowed control-plane files for discoverable facts before asking the
user. If the request already fixes the requirements understanding, goal and
non-goals, exact paths, intended changes, verification and risks, take the
zero-question path and present the plan directly.

Otherwise ask a question only when its answer changes at least one named plan
field. Name that field, ask one question at a time, and include a recommended
answer with its practical effect. Decisions belong to the user; repository facts
do not. Challenge an ambiguous term or use a concrete failure example only when
it can change the plan.

Do not edit, stage, commit, push, dispatch or create an artifact while
requirements are still being understood. Stop asking when every plan field is
specific enough for the user to judge the complete proposed change.

## Present one plan

Present one compact but explicit plan with these information groups:

- **Requirements understanding:** restate the requested behavior and relevant
  decisions; this replaces a separate requirements-confirmation round.
- **Goal and non-goals:** name the desired workflow behavior and excluded work.
- **Exact paths:** list every path expected to change.
- **Intended changes:** state the material change in each path, including affected
  Skills, roles and route names instead of compressing them into a slogan.
- **Verification and risks:** name focused checks, Git integration, protected
  dirty paths and any workflow-step cost audit triggered by the plan.

Keep the plan detailed enough for the user to see its actual scope without
creating a separate design document. If the user corrects it, continue the
conversation and present the complete revised plan. Perform no mutation until
the user confirms the complete plan in natural language. Confirmation of one
answer is not confirmation of the plan, and no fixed token or status phrase is
required.

## Execute the confirmed plan

After confirmation, use `$hmasd-workflow-change-audit` for impact classification,
mutation, structural and focused checks, stale-reference searches, exact staging,
commit, push and any required reload smoke. The confirmed plan authorizes those
operations only for its stated intent, authority, path set and acceptance method.

Resolve mechanical details inside the confirmed goal, owned paths and acceptance
method without another prompt. Pause and present a revised complete plan before
continuing when execution would change the goal, expand an authority boundary,
add a path, add or expand a workflow step, change the acceptance method, or add
an external effect not described in the confirmed plan.

Do not create a handoff, runtime record, review round, experiment or child merely
to manage this collaboration. Do not enter the active research loop. Before plan
confirmation, return only the next decision question or the complete plan; after
execution, return the accepted commits, exact paths and focused verification
evidence.
