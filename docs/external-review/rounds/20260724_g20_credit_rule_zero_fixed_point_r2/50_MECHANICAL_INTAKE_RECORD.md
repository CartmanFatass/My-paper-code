# Mechanical intake record

```text
round=20260724_g20_credit_rule_zero_fixed_point_r2
stage_commit=3ec4a6500a26d5141715861f4b1f191ac141b6fb
reviewer=open_divergent
conversation_id=6a63979e-35d8-83e8-8da7-10de59a5fdeb
transport=project_manager_direct_transport
archived=2026-07-24
raw=21_PRO_OPEN_RAW.md
fence_artifact=10_FENCE.txt
reviewer_reported_stage=3ec4a6500a26d5141715861f4b1f191ac141b6fb
reviewer_reported_duration=18m14s
evidence_access=github_connector_succeeded_no_archive_upload_required
```

Transport facts only. Nothing here interprets the answer.

## Predecessor round

`20260724_g20_credit_rule_zero_fixed_point` was retired before any answer was
archived, for a Project Manager authoring defect — its question carried no
`## Evidence to read` allow-list. See that round's
`99_RETIRED_TRANSPORT_DEFECT.md`. No content from it is carried forward.

## Transport faults encountered and how they were resolved

1. **Fence fragmentation.** Earlier attempts composed the fence with the
   `computer` `type` action. A newline in that composer is Enter, which submits,
   so the fence was chopped into progressively truncated
   `CURRENT_REVIEW_ASSIGNMENT` messages. Five such fragments and one
   `Internal Server Error` remain visible above the accepted fence. None is an
   assignment and none was archived.
2. **Recovery.** The Project Manager stopped the stale generation, composed the
   complete fence as `10_FENCE.txt`, and submitted it as a single user turn using
   `shift+Return` soft line breaks. Its `instruction` field explicitly directs the
   reviewer to disregard the fragments. Exactly one fence was submitted for this
   round; none was resubmitted.
3. **Evidence access.** No diagnostic was received and no archive upload was
   needed. The reviewer read the repository through the GitHub connector,
   reporting `Stage reviewed: 3ec4a650…` and, in its trace, fetching specific
   line ranges of the screening script. The earlier hypothesis that the connector
   could not reach `untied-k` is disproved.
4. **Invalid capture, discarded.** A first archival pass wrote 794 bytes of the
   reviewer's mid-generation progress trace to the raw path and asserted byte
   equality while an active `Stop answering` control was present. That file was
   deleted unread into reconciliation and is not part of this record. The archive
   below was captured only after the stop control was gone.

## Completion evidence for the archived response

- anchored to the single complete fence, not to the page tail;
- captured after generation ended: the composer control had returned to the idle
  voice control, with no `Stop answering`, `Retry` or continue control present;
- confirmed by a second inspection more than three seconds later showing the
  same message identity and no added text;
- content addresses the question's three numbered asks rather than narrating
  progress toward them, and carries the reviewer's own stage-commit statement.

## Known fidelity limitation

The response contains rendered mathematics. Extracted page text linearizes those
expressions — subscripts, superscripts and fraction layout appear on separate
lines with residual layout characters. The archive preserves the extracted text
exactly as captured; the mathematical content is faithful but its visual layout
is not reconstructable from this file alone. The live conversation remains the
rendering of record.

No convergence turn was sent. No Git was run by any transport child.
