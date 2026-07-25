# Retired: Project Manager authoring defect, no scientific content changed

```text
round=20260724_g20_credit_rule_zero_fixed_point
status=RETIRED_BEFORE_ANY_ARCHIVED_ANSWER
superseded_by=20260724_g20_credit_rule_zero_fixed_point_r2
retired=2026-07-24
fault_owner=project_manager
fault_class=transport_authoring_not_scientific
raw_archived=false
iteration_consumed=false
compute_spent=zero
```

## What was wrong

The question authored for this round carried no `## Evidence to read` section.
The evidence paths were placed in `01_SHARED_SOURCE_MANIFEST.md`, a separate
file that the freshness fence does not name and the reviewer therefore never
reads.

Two consequences followed, both mechanical:

1. The reviewer read a question at `stage_commit` with no pointer to any
   evidence path, and asked for file contents. Under the skill that response is
   an evidence-access transport diagnostic, not an answer.
2. `build_review_evidence_archive.ps1` refused to run for the documented
   recovery, with `Question has no exact evidence allow-list`. The builder parses
   the question for a literal `## Evidence to read` heading followed by
   `` - `path` `` items; nothing else is an allow-list.

## What compounded it

The exchanger correctly stopped and escalated when the reviewer asked for
content instead of reading the repository. The Project Manager answered by
instructing it to submit the question body verbatim, splitting across messages
if needed. That instruction was wrong and contradicted the transport contract —
`SKILL.md` line 116: *"the question carries exact paths, not file contents."*
The correct response to that diagnostic was evidence-access recovery through the
archive builder.

The exchanger had read `SKILL.md` and `EXTERNAL_PRO.md` and had the recovery
procedure loaded; it did not fail to trigger the skill. It followed a Project
Manager instruction that overrode it.

## Why the round could not be repaired in place

The freshness fence was accepted at
`stage_commit=0e85694febaed501aa4bc94f8dddc73a1cc23f7a` and binds the round
identity including that commit and question path. Adding the allow-list changes
the question, and an accepted fence is never resubmitted. Reusing this round id
with a second fence at a different commit would create exactly the ambiguity the
single-fence rule exists to prevent, so the round is retired and reopened under
a new id instead.

## What carried forward unchanged

The scientific content of the question — the derivation, the numerical
confirmation, what the finding retires, the proposed repair marked as unadopted
inference, and the three asks. Only the allow-list placement changed.

No answer was archived from this round. Nothing here is scientific evidence, and
the conversation turns it produced are superseded by the `_r2` fence.
