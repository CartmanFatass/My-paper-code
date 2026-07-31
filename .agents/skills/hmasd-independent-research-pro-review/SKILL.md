---
name: hmasd-independent-research-pro-review
description: Use only in the registered Independent Research Pro Review Operator task for one explicit user-authorized methodology audit or one reusable ordered batch of single-direction scientific audits, isolated from formal HMASD operations and archived under local_research/pro_reviews.
---

# HMASD Independent Research Pro Review

## Boundary

Operate only as the registered Independent Research Pro Review Operator. Read
the root router, `.agents/roles/INDEPENDENT_RESEARCH_REVIEW_OPERATOR.md`, the
exact methodology assignment or ordered direction-audit batch and
`.agents/roles/EXTERNAL_PRO.md`. Then read `$hmasd-review-round` completely and
apply its immutable backend fork. A browser selection uses its fence,
attachment-identity, single-sentinel, single-monitor, natural-completion and
recovery mechanics. An Agentify selection uses only its request/receipt and
exact-archive branch. Both remain under this Skill's separate-conversation and
local-storage boundary.

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
   `INDEPENDENT_RESEARCH_DIRECTION_AUDIT`. Both have no scientific-iteration,
   formal-grant or project-state effect.
6. A direction batch names one campaign record, one question-contract commit
   and one explicit ordered list of unique `candidate_id` values. One user
   instruction authorizes that immutable list; it does not authorize another
   campaign or dynamically discovered candidate. Create one immutable batch
   manifest with the registered builder. Do not read the campaign manually.

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-independent-research-pro-review/scripts/build_direction_review_input.py batch-plan `
  --campaign <exact-local_research-campaign.json> `
  --question-contract-commit <exact-40-character-commit> `
  --candidate-id <first-id> --candidate-id <next-id> `
  --output <batch-directory>/BATCH_MANIFEST.json
```

Before starting or resuming any item, run `batch-next`. Only `NEXT` permits a
new Pro submission. `ACTIVE` continues the same item, `BLOCKED` stops the batch,
and `COMPLETE` ends it. Never infer progress from task memory or completion
order.

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-independent-research-pro-review/scripts/build_direction_review_input.py batch-next `
  --manifest <batch-directory>/BATCH_MANIFEST.json
```

7. For the sole `NEXT` candidate, run the registered
   `build_direction_review_input.py build` command to create its direction
   packet. Do not add another candidate or attach the batch manifest or full
   portfolio to the Pro turn.

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-independent-research-pro-review/scripts/build_direction_review_input.py build `
  --campaign <exact-local_research-campaign.json> `
  --candidate-id <exact-candidate-id> `
  --batch-manifest <batch-directory>/BATCH_MANIFEST.json `
  --output <review-directory>/22_DIRECTION_INPUT.md
```

## Prepare one local review instance

Methodology mode uses one review directory. Direction-batch mode uses one batch
directory and deterministic item subdirectories:

```text
local_research/pro_reviews/<review_id>/
  20_PRO_OPEN_QUESTION.md or 21_DIRECTION_SCIENTIFIC_AUDIT.md
  22_DIRECTION_INPUT.md (direction mode only)
  21_PRO_OPEN_RAW.md
  50_MECHANICAL_INTAKE_RECORD.md
  60_METHODOLOGY_PACKET.md or 60_DIRECTION_PACKET.md
  assignment_payload.txt
  TRANSPORT_BACKEND.json
  sentinel.jsonl (browser only)
  monitor_assignment_receipt.json (browser only)
  agentify_request.json and agentify_receipt.json (Agentify only)

local_research/pro_reviews/<batch_id>/
  BATCH_MANIFEST.json
  item_001/
    21_DIRECTION_SCIENTIFIC_AUDIT.md
    22_DIRECTION_INPUT.md
    21_PRO_OPEN_RAW.md
    50_MECHANICAL_INTAKE_RECORD.md
    60_DIRECTION_PACKET.md
    70_EXPLORER_HANDOFF.json
    90_TERMINAL_BLOCKER.json (only on a terminal blocker)
    assignment_payload.txt
    TRANSPORT_BACKEND.json
    sentinel.jsonl (browser only)
    monitor_assignment_receipt.json (browser only)
    agentify_request.json and agentify_receipt.json (Agentify only)
```

Copy the committed question text exactly into the local question path. For a
direction audit, build `22_DIRECTION_INPUT.md` before rendering and verify its
reported SHA-256, campaign ID, workflow commit and sole candidate ID.
Methodology mode verifies the pushed 40-character commit and repository
allow-list with `hmasd-review-round/scripts/verify_pro_review_boundary.ps1`.
Direction mode verifies the pushed question commit plus the immutable batch
manifest and generated packet receipt; it never treats local research paths as a
repository allow-list. The campaign's recorded
`workflow_commit` and the later question-contract commit are distinct identities
and are verified against their own surfaces. Render the exact Assignment with
its registered renderer. Preserve the complete payload bytes before browser
submission.

## Transport without formal-state effects

Follow `$hmasd-review-round` with these role substitutions only. Before the
first send, freeze exactly one backend for the item. The default remains the
browser path; if Agentify is selected, activate
`$hmasd-agentify-pro-transport` and route the complete item through its
request, verify and archive commands. Do not initialize a browser sentinel or
monitor for an Agentify item, and never submit the same item through both
backends. The Agentify receipt must bind the exact prompt hash, stable key,
runtime conversation/model, `sendCount=1`, exact message IDs, two stable
snapshots separated by at least three seconds, response hash and
`clickedControls=[]`; the validator derives that no prohibited control was
activated. An incomplete or conflicting receipt is a blocker without another
send.

When Agentify is selected, the validated request/receipt pair and exact raw
archive return directly to **Return one exact packet** below for normal
mechanical intake. Do not execute the browser substitutions, watches, retry or
sentinel/monitor rules in between.

When browser is selected, follow these role substitutions only:

- `registered transport owner` is this task;
- the conversation registry is the local independent registry;
- all raw, intake, payload and receipt paths are under this review directory;
- browser-only sentinel paths are also under this directory;
- no step reads, writes or resumes formal operations;
- one browser-only `hmasd-pro-response-monitor` returns locally to this task.

Do not paraphrase the question, evidence allow-list or Pro instruction. In a
browser turn, Pro may reason for 10-30 minutes or longer. Continue bounded
45-second watches in the same monitor; one watch expiry is `PENDING`. Never
activate `Answer now`, create a second monitor or submit a duplicate question.

At most one batch item may own an active Pro turn. A browser item may own one
sentinel/monitor pair; an Agentify item may own one ledger operation. A later
item cannot start until the current item has exact natural completion, exact
archive and a `ROUTE_SENT` handoff receipt bound to the direction packet's byte
count and SHA-256. A scientific disposition of `VALIDATION_READY`,
`REVISION_REQUIRED`, `PARK` or `UNRESOLVED` completes that item and does not stop
the batch. An identity, transport, format or archival blocker creates the exact
`90_TERMINAL_BLOCKER.json`, stops the batch and forbids skipping ahead.

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
6. For a direction item, record the successful route mechanically in
   `70_EXPLORER_HANDOFF.json` with `candidate_id`, `route_status=ROUTE_SENT`,
   `packet_bytes` and `packet_sha256`. Run `batch-next` again. `NEXT` continues
   the same authorized batch without another user prompt; `COMPLETE` terminates
   it.

If a browser response is format-incomplete, use the existing once-only response
contract retry only when its full mechanical predicate holds. Agentify does not
use that browser retry path. Otherwise return the exact terminal blocker. Never
invent a missing principle or continue into Explorer workflow mutation.

Stop after one terminal methodology return, one completed ordered batch, or one
batch blocker. Each Pro turn remains a single-direction audit and never compares
the portfolio. The immutable manifest, not the Operator or Explorer, selects
the next item. A new batch, campaign or candidate outside that manifest needs a
new direct user instruction.
