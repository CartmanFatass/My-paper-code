---
name: hmasd-independent-research-pro-review
description: Use only in the registered Independent Research Pro Review Operator task for one explicit user-authorized methodology audit or one single-direction scientific audit, isolated from formal HMASD operations and archived under local_research/pro_reviews.
---

# HMASD Independent Research Pro Review

## Boundary

Operate only as the registered Independent Research Pro Review Operator. Read
the root router, `.agents/roles/INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md`, the
exact assignment and `.agents/roles/EXTERNAL_PRO.md`. Then read
`$hmasd-review-round` completely and apply its fence, attachment-identity,
single-sentinel, single-monitor, natural-completion and recovery mechanics under
this Skill's separate-conversation and local-storage boundary.

Do not load Research Operations Manager, `CURRENT_WORK.md`, formal review
rounds, runtime evidence, code, CDC state or active portfolios. This Skill
grants no science, workflow, code, compute, Git or formal-runtime authority.

## Bootstrap the isolated review

1. Confirm the active task session equals the router's
   `independent_research_review_operator_session`.
2. Use only `local_research/pro_reviews/`. The Explorer owns every other
   `local_research/` path.
3. Create or reuse exactly one Pro conversation dedicated to independent
   research. Record its exact conversation ID and URL in
   `local_research/pro_reviews/REVIEWER_CONVERSATION.json`. Never read the
   formal registry or formal conversation.
4. Require one pushed Workflow-Design-Manager commit containing the exact
   question contract. Methodology mode uses `references/20_PRO_OPEN_QUESTION.md`.
   Single-direction mode uses `references/21_DIRECTION_SCIENTIFIC_AUDIT.md`.
5. Use exactly one review mode:
   `INDEPENDENT_RESEARCH_METHODOLOGY_AUDIT` or
   `INDEPENDENT_RESEARCH_DIRECTION_AUDIT`. Both have zero scientific-iteration,
   formal-grant and project-state effect.
6. A direction assignment names one campaign record and exactly one
   `candidate_id`. Run the registered `build_direction_review_input.py build`
   command to create the direction packet. Do not read the campaign manually,
   add another candidate or attach the full portfolio.

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-independent-research-pro-review/scripts/build_direction_review_input.py build `
  --campaign <exact-local_research-campaign.json> `
  --candidate-id <exact-candidate-id> `
  --output <review-directory>/22_DIRECTION_INPUT.md
```

## Prepare one local review instance

Use a new directory:

```text
local_research/pro_reviews/<review_id>/
  20_PRO_OPEN_QUESTION.md or 21_DIRECTION_SCIENTIFIC_AUDIT.md
  22_DIRECTION_INPUT.md (direction mode only)
  21_PRO_OPEN_RAW.md
  50_MECHANICAL_INTAKE_RECORD.md
  60_METHODOLOGY_PACKET.md or 60_DIRECTION_PACKET.md
  assignment_payload.txt
  sentinel.jsonl
  monitor_assignment_receipt.json
```

Copy the committed question text exactly into the local question path. For a
direction audit, build `22_DIRECTION_INPUT.md` before rendering and verify its
reported SHA-256, campaign ID, workflow commit and sole candidate ID.
Methodology mode verifies the pushed 40-character commit and repository
allow-list with `hmasd-review-round/scripts/verify_pro_review_boundary.ps1`.
Direction mode verifies the pushed question commit plus the generated packet
receipt and attachment bytes; it never treats local research paths as a
repository allow-list. Render the exact Assignment with its registered
renderer. Preserve the complete payload bytes before browser submission.

## Transport without formal-state effects

Follow `$hmasd-review-round` with these role substitutions only:

- `registered transport owner` is this task;
- the conversation registry is the local independent registry;
- all raw, intake, payload, sentinel and receipt paths are under this review
  directory;
- no step reads, writes or resumes formal operations;
- one `hmasd-pro-response-monitor` returns locally to this task.

Do not paraphrase the question, evidence allow-list or Pro instruction. Pro may
reason for 10-30 minutes or longer. Continue bounded 45-second watches in the
same monitor; one watch expiry is `PENDING`. Never activate `Answer now`, create
a second monitor or submit a duplicate question.

Archive only after the exact user-turn identity is verified and the same
assistant message is stable in two snapshots at least three seconds apart with
inactive generation, Retry and continuation controls. Attachment-backed
identity uses the registered byte-exact validator. An unreadable or mismatched
identity is blocked, not proof of a failed send.

## Return one exact packet

The committed question declares the required response headings and fields.
After natural completion:

1. Copy the complete visible response verbatim to `21_PRO_OPEN_RAW.md` and
   reread it for exact equality.
2. Record transport facts only in `50_MECHANICAL_INTAKE_RECORD.md`.
3. Confirm every required response field is present mechanically. Do not judge,
   summarize, repair or reorder scientific content.
4. When format-complete, copy the complete response verbatim to the mode's
   `60_*_PACKET.md` path.
5. Use the registered cross-task payload helper to create one exact UTF-8
   handoff. Return a methodology packet to Workflow Design Manager. Return a
   direction packet directly to the locked Independent Research Explorer route.
   The payload contains only its path, byte count and SHA-256 plus the exact
   review and candidate identities.

If the response is format-incomplete, use the existing once-only response
contract retry only when its full mechanical predicate holds. Otherwise return
the exact terminal blocker. Never invent a missing principle or continue into
Explorer workflow mutation.

Stop after one terminal return. A direction audit neither compares the
portfolio nor chooses, schedules or opens the next direction. Another review
needs a new direct user instruction.
