# Controller-Direct External Review Design

## Decision

Retire the persistent `open_divergent_exchange` Codex task and make the active
Controller the sole mechanical transport owner for the registered external
GPT-5.6 Pro conversation. This removes cross-task browser custody, callback and
heartbeat delivery while preserving the existing semantic firewall:

- Project Manager is the sole semantic author and repair owner for every
  reviewer-visible code-side package.
- External Pro is the sole scientific decision authority.
- Controller owns only provenance checks, Git visibility, browser transport,
  exact raw archival, heartbeat lifecycle, mechanical intake and routing.

The retired Exchange task and Skill are not retained as a fallback. Git history
is the archive.

## Direct transport state machine

```text
PM_PACKAGE_READY
  -> CONTROLLER_MECHANICAL_VALIDATE
  -> INSPECT_REGISTERED_CONVERSATION
  -> RESUME_ACCEPTED_FENCE | SUBMIT_ONCE
  -> WAIT_WITH_CONTROLLER_HEARTBEAT
  -> ARCHIVE_EXACT_RAW
  -> CONTROLLER_MECHANICAL_INTAKE
  -> DELETE_CONTROLLER_HEARTBEAT
  -> RETURN_EXACT_RAW_TO_PM
```

The Controller inspects the registered conversation before submission. A
visible fence for the same round, commit and question is resumed and never
resubmitted. A stable natural response is archived exactly even when its
scientific content is incomplete. Project Manager alone decides whether its
code-side work requires a focused follow-up and authors that package.

## Failure and recovery contract

A browser/runtime/navigation/archive failure remains an active handoff while a
safe materially distinct recovery exists. The Controller records each attempt,
reconnects the registered runtime or conversation, checks for an accepted fence
before any submission retry, and never guesses from a stale tab. `BLOCKED` is
terminal only after recovery is exhausted and reports the remaining cause,
attempts, duplicate-submission risk and exact resume condition.

Late callbacks and writes from the retired Exchange task have no authority.
They cannot overwrite a Controller-owned raw or start a successor.

## Runtime migration

1. Delete the Exchange-owned heartbeat if present.
2. Archive and unpin the Exchange task.
3. Move heartbeat rendering under `$hmasd-review-round`.
4. Remove the Exchange role, route and Skill in one tracked boundary.
5. Inspect the existing focused G1 conversation and resume an already accepted
   fence instead of creating a duplicate.

## Non-goals

This topology change does not modify scientific evidence, benchmark semantics,
algorithm code, formal-compute authority, iteration accounting or the current
PM-authored G1 question package.
