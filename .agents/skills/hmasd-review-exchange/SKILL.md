---
name: hmasd-review-exchange
description: Use only inside the registered persistent HMASD Open-Pro Exchange session for one controller-assigned blind divergent review. It owns the registered Pro browser conversation, exact raw capture, semantic quality note, one 5-minute heartbeat while pending, and one direct callback to the controller; it never performs convergence, implementation, Git, experiment or project management.
---

# HMASD Open-Pro Exchange

## Entry

Accept only:

```text
$hmasd-dispatch-task
$hmasd-review-exchange

REVIEW_STAGE
role_skill=.agents/skills/hmasd-review-exchange/SKILL.md
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

The question must list `docs/project/ALGORITHM_PRINCIPLES.md` and
`docs/external-review/OPEN_REVIEW_PRINCIPLES.md` and must not list internal
manager references.

## Authority

Own only the assigned external conversation, question, raw and heartbeat. Do
not write questions, reconciliation, disposition, Git, project control, code or
experiments. Do not change models, rank routes, select a successor, dispatch
another role or use an unrelated browser conversation.

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

When the current response stops naturally and is stable, archive it to the
assigned raw, reread it and require exact text equality. Preserve every complete
response even when content is incomplete or references the wrong evidence.
Report content limitations as `COMPLETE_WITH_GAPS`, never as transport failure.

## Heartbeat

After Pro visibly accepts the assignment, create one 5-minute heartbeat owned
by this Exchange session. Each wake explicitly reloads both Skills and performs
one bounded inspection. Do not sleep, poll continuously, send waiting messages
or create a second heartbeat.

Terminal success requires tool evidence for all three facts:

1. raw equals the stable completed response;
2. callback delivery returned the registered controller task;
3. this heartbeat was deleted and confirmed absent.

If callback fails, the next wake retries only the same `handoff_id`. If deletion
alone fails, retry deletion only. Release the owned page after all three facts.

## Callback

Resolve the controller live through `$hmasd-dispatch-task`, preserve all route
fields and send once:

```text
$hmasd-dispatch-task

REVIEW_STAGE_COMPLETE
role=OPEN_DIVERGENT
handoff_id=<round>:OPEN_DIVERGENT:complete:<question>
round=<id>
stage_commit=<pushed SHA>
raw=<round_path>/<raw>
verification=natural_complete;exact_text_equal
quality=<COMPLETE|COMPLETE_WITH_GAPS>
quality_notes=<concise semantic observation or none>
```

For a genuine operational boundary send `REVIEW_STAGE_BLOCKED` with the same
role, stable handoff, round and direct reason. Diagnose and attempt reasonable
in-scope recovery before blocking; do not ask the controller for selectors,
browser commands or click sequences.
