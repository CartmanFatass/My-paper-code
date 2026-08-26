---
name: hmasd-slice-interface
description: Use when an HMASD Root, Portfolio, EM, or CM task receives an exact Work Packet or returns its bounded slice.
---

# HMASD Slice Interface

This is the sole normal cross-session receiver interface. Read
`docs/project/WORKFLOW_PROTOCOL.md` only for shared contract detail.

1. Accept one exact packet locator and `work_id`. Run `return-read` first. An
   existing matching return is the idempotent no-op: report its facts and do
   not redo the slice or derive another packet.
2. If no return exists, validate the exact packet and fresh cited refs; do only
   its frozen objective, non-goals, owned paths, authority writes, and Effects.
   Resolve each path Windows-safely to canonical casefolded repository form
   before comparison or writing. A precise contract defect is returned to the
   program; normal work never wakes Clerk.
3. Write the machine-valid `agent_result` with `assignment_id=work_id`, exact
   structured evidence/state refs, and explicit scoped failure when applicable.
   For `REQUEST_*`, build the complete canonical draft first; the typed result
   binds only `next_action.input_refs=[draft.work_id]`. Do not select a next
   owner in free text.
4. Call `return-publish` with a fresh receiver observation. Only after that
   command succeeds may the session send a natural-language summary. A repeated
   identical publish is safe; a different return is a conflict.

CM keeps ordinary review, same-scope repair, tests, verification, and candidate
preparation inside this one slice. Leaves return only to their owner. Do not
create coordination state or dispatch.
