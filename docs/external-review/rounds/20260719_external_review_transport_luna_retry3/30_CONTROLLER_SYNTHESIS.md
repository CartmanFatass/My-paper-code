# Controller Synthesis

## Archived divergent evidence

Both blind divergent stages returned `TRANSPORT_OK` from their registered
role-specific sessions. Each has `dispatch_count=1`, and both raws were archived
before this synthesis.

- Gemini read exactly its four allowlisted local files. Its response was
  byte-compared before the stage closed.
- Open Pro read the pinned Git commit, question, brief, and shared manifest in
  the registered Pro conversation. Its raw was archived and its stage closed.

## Observed transport anomalies

1. Gemini needed narrowly scoped write access to its registered conversation
   state, helper, SQLite auxiliaries, and recent-conversation index. Its visible
   response completed and archived exactly, but the CLI still reported an
   exit-time atomic-cache replacement denial.
2. The Open Luna Exchange could not receive a background route while its Codex
   task was `notLoaded`. Loading that same fixed task in Codex, without changing
   its model or external Pro conversation, made the same background-message
   call succeed.
3. The Open Exchange completed its raw and state transition but did not send a
   terminal message back to the controller. The user supplied the completed
   payload. No duplicate route was sent.

## Interpretation

The reviewer-facing transports worked, role isolation held, and both divergent
raws are valid. The controller-facing orchestration is not yet proven healthy:
task loading and terminal relay are hidden liveness dependencies, while the
Gemini exit warning shows its atomic cache update is still incomplete.

Gemini's proposed merger of controller synthesis with convergent review is
rejected because it would remove the controller's independent comparison stage.
Open Pro's proposed central ledger is largely already represented by
`05_REVIEW_STATE.json`; the missing capability is a verified terminal relay,
not another evidence ledger.

## Convergent question

Determine whether these anomalies are non-blocking after exact raw archival, or
whether a healthy reusable workflow requires one concrete repair and another
transport-only test before algorithm research may start. Do not make an
algorithm recommendation.
