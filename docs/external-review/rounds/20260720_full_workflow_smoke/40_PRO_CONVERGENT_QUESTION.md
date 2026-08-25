# Convergent-Pro Full Workflow Smoke

You are the registered convergent GPT-5.6 Pro reviewer. Evaluate only whether
the current external-review transport completed its real Gemini and Open-Pro
stages and whether the recorded repairs are internally coherent. Do not review
or recommend an algorithm or experiment.

## Repository files to inspect

- `docs/external-review/rounds/20260720_full_workflow_smoke/00_REVIEW_BRIEF.md`
- `docs/external-review/rounds/20260720_full_workflow_smoke/10_GEMINI_DIVERGENT_QUESTION.md`
- `docs/external-review/rounds/20260720_full_workflow_smoke/11_GEMINI_DIVERGENT_RAW.md`
- `docs/external-review/rounds/20260720_full_workflow_smoke/20_PRO_OPEN_QUESTION.md`
- `docs/external-review/rounds/20260720_full_workflow_smoke/21_PRO_OPEN_RAW.md`
- `docs/external-review/rounds/20260720_full_workflow_smoke/30_EVIDENCE_RECONCILIATION.md`
- `.agents/skills/hmasd-review-exchange/SKILL.md`
- `scripts/invoke_gemini_reviewer.ps1`
- `scripts/start_gemini_reviewer_live.ps1`

## Requested decision

Return concise Markdown with exactly these headings:

## VERDICT

Choose exactly one:

- `PASS_FULL_WORKFLOW_SMOKE`
- `FAIL_FULL_WORKFLOW_SMOKE`

## VERIFIED_TRANSPORTS

State separately whether Gemini, Open Pro, direct callbacks, raw archival, and
role isolation are supported by the supplied evidence.

## REPAIR_ASSESSMENT

State whether the Gemini permission, deferred-Pro waiting, and pinned-question
validation repairs address the observed blockers without changing scientific
scope.

## REMAINING_OPERATIONAL_RISK

Name at most two concrete transport risks, or state `NONE_BLOCKING`.

## NEXT_ACTION

If PASS, state whether the workflow may be used for the next tracked scientific
round. If FAIL, name only the minimum transport repair and retest.

Do not make an algorithm, implementation, or experiment recommendation.
