---
name: hmasd-review-exchange
description: Use inside the registered HMASD Open-Pro Exchange session when receiving REVIEW_STAGE, an assigned Pro review question/raw path, a review heartbeat wake, a browser transport failure or approval wait, or a retry/callback for the registered OPEN_DIVERGENT external-review conversation.
---

# HMASD Open-Pro Exchange

## Entry

Accept only:

```text
$hmasd-review-exchange
REVIEW_STAGE
skill=$hmasd-review-exchange
reviewer_role=OPEN_DIVERGENT
round=<id>
stage_commit=<40-character pushed SHA>
round_path=docs/external-review/rounds/<id>
question=<round-relative 20_PRO_OPEN_QUESTION.md>
raw=<round-relative 21_PRO_OPEN_RAW.md>
completion_policy=ARCHIVE_NATURAL_RESPONSE_AND_REPORT_QUALITY
recovery_context=<optional evidence or none>
```

Read the router, role directory, this Skill,
`docs/external-review/REVIEWER_CONVERSATIONS.json`, the question and only its
listed Git-visible evidence. Require the current task to equal the registered
`open_divergent_exchange`, and require the registered external conversation,
question and raw paths to match. Reject every other reviewer role.

For every new `REVIEW_STAGE`, the brief and question must declare
`semantic_author=project_manager`,
`artifact_scope=reviewer_visible_code_side`, and
`scientific_authority=external_pro`. They must list
`docs/project/ALGORITHM_PRINCIPLES.md` and
`docs/external-review/OPEN_REVIEW_PRINCIPLES.md`. PM-authored reviewer-visible
artifacts carrying those markers are admissible; internal manager audits,
callbacks, scratch notes and work logs are forbidden.

An assignment whose freshness fence was visibly accepted before this ownership
contract changed may finish transport and raw archival only. Report it as a
superseded process; it cannot supply adoption or successor authority.

## Authority

Own only the assigned external conversation, question, raw and heartbeat. Do
not write questions, reconciliation, disposition, Git, project control, code or
experiments. Do not change models, rank routes, select a successor, dispatch
another role or use an unrelated browser conversation.

Use narrow interface and broad transport judgment. The controller supplies the
round, commit, exact PM-authored question and raw path unchanged; this Exchange chooses the in-scope browser
inspection and recovery method. Do not ask the controller for selectors, page
steps, tab commands or minor format decisions. Escalate only when the registered
conversation, pushed boundary, raw archive, route delivery, or authority itself
is unavailable.

The Exchange reads and transports the exact PM-authored files unchanged. It
does not normalize their wording or substitute a Controller-authored summary.

## Stage

Verify the pushed commit and question are remotely visible. Submit exactly one
freshness fence to the registered Pro conversation:

```text
CURRENT_REVIEW_ASSIGNMENT
repository=CartmanFatass/My-paper-code
branch=aggressive
round=<round>
stage_commit=<stage_commit>
question=<question>
instruction=Ignore earlier rounds and refs. Read only this question and its listed evidence from stage_commit.
```

Require the visible user turn to contain the current round, commit and question.
Never resubmit an accepted assignment. Keep the registered page available while
the response is pending and avoid duplicate tabs or needless reloads. Choose
the inspection and recovery method with model judgment; one failed locator or
DOM assumption is not a blocker.

## Recovery before blocked

Any browser, runtime, navigation, approval, route, archive or callback failure
starts bounded self-recovery for the same handoff. First inspect the direct tool
error and current page or delivery state. Then try safe materially distinct
methods available to this Exchange, such as reconnecting the registered runtime,
reusing an existing registered tab, opening the registered conversation after
approval, or re-resolving the live route. Before retrying assignment submission,
prove that no visible accepted freshness fence exists. Never repeat an identical
failed action without changed state and never create a duplicate assignment.

Report each attempt in commentary:

```text
RECOVERY_ATTEMPT
attempt=<positive integer>
boundary=<failed operation>
action=<diagnostic or recovery action>
outcome=<observed result>
```

`waitingOnApproval` is a live recoverable state, not a blocker. A timeout or two
failed initializations alone are not terminal while another safe in-scope
recovery remains. Emit `REVIEW_STAGE_BLOCKED` only when the registered
conversation, pushed boundary, raw archive, callback route or authority remains
unavailable after all safe in-scope recovery is exhausted.

If package validation fails, do not invite Controller rewriting. Return the
direct validation evidence with `repair_owner=project_manager`; Controller
routes it unchanged to PM, which owns the semantic repair.

When the current response stops naturally and is stable, archive it to the
assigned raw, reread it and require exact text equality. Preserve every complete
response even when content is incomplete or references the wrong evidence.
Report content limitations as `COMPLETE_WITH_GAPS`, never as transport failure.

Judge content gaps semantically. A missing label, reordered section or wording
variation is not transport failure if the response is complete and archivable.
Use `COMPLETE_WITH_GAPS` for substantive scientific or evidence omissions.
Project Manager decides whether a code-side gap needs a focused follow-up;
exact Pro text determines whether Pro left a scientific question open.
Controller only routes the resulting request.

## Heartbeat

After Pro visibly accepts the assignment, create one 5-minute heartbeat owned
by this Exchange session. Each wake explicitly invokes
`$hmasd-review-exchange` and `$hmasd-dispatch-task`, then performs one bounded
inspection. Do not sleep, poll continuously, send waiting messages or create a
second heartbeat.

Terminal success requires tool evidence for all three facts:

1. raw equals the stable completed response;
2. callback delivery returned the registered controller task;
3. this heartbeat was deleted and confirmed absent.

If callback fails, the next wake retries only the same `handoff_id`. If deletion
alone fails, retry deletion only. Release the owned page after all three facts.

## Callback

Resolve the controller live with the dispatcher route resolver, preserve all
route fields and send once:

```text
REVIEW_STAGE_COMPLETE
source_thread_id=<registered open_divergent_exchange thread ID>
skill=$hmasd-review-exchange
role=OPEN_DIVERGENT
handoff_id=<round>:OPEN_DIVERGENT:complete:<question>
round=<id>
stage_commit=<pushed SHA>
raw=<round_path>/<raw>
verification=natural_complete;exact_text_equal
quality=<COMPLETE|COMPLETE_WITH_GAPS>
quality_notes=<concise semantic observation or none>
repair_owner=<project_manager when package repair is required|none>
superseded_process=<true|false>
adoption_authority=<false|external_pro_raw_only>
```

For a genuine operational boundary send `REVIEW_STAGE_BLOCKED` with the same
`source_thread_id`, `skill`, role and round,
`handoff_id=<round>:OPEN_DIVERGENT:blocked:<question>` and the direct reason.
It also includes `recovery_attempts=<count>`, a concise attempt summary,
`recovery_exhausted=true`, and `repair_owner=project_manager` when the boundary
is package content. Do not ask the Controller for selectors, browser
commands or click sequences; request user action only when the application
itself exposes a required approval.

For the pre-contract accepted fence, set `superseded_process=true` and
`adoption_authority=false`. Every current PM-authored round sets
`superseded_process=false`; `external_pro_raw_only` means only the exact raw may
supply science and still grants no automatic code, compute or successor action.
