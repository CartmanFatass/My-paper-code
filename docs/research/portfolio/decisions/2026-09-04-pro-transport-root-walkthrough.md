# Owner-directed 6 Pro transport and skill repair

Date: 2026-09-04
Provenance: OWNER_DIRECT (transport, model, skill repair); no Portfolio lifecycle action
State: both replies archived; revised route-expansion proposal available for owner review

## Owner instructions and scope

The owner requested 6 Pro, then a new conversation and Root's personal execution:

> 请开启新的conversation 不要让其再重复投递了 老的conversation没有新模型 以及我建议是你完成一遍流程 这个操作员的模型比较dumb

The owner then clarified that demonstrating successful Send was sufficient before
repairing the skills; the subsequent wait/archive/research procedure stays unchanged.
After the first response, the owner sent a follow-up directly in the same Pro chat:

> 出于提高效率和相同族互相增益的需求 我们可以放宽要求 不需要只收敛到两条线各一个 这个只是用来分类的 请给我更多的路线

Two parent lines therefore classify research. They impose neither a one-route-per-line
limit nor a two-route investment budget. The owner asked to review the expanded reply
before proceeding. The earlier two-investment PARK list was **not applied**.
The 19 ACTIVE / 3 PARKED source lifecycle snapshot and execution pause remain intact.

## Observed transport

- Request 01: one confirmed old-model Send. Its returned capture begins with pinned
  ref `dfd9c5dbd512c463a79a21d1bd50e1dccf45d28d` and answers an earlier policy
  question, rather than this packet at `b35eadf954a0bc56f3291f3b3d2b9ece0748e4a9`.
  Capture SHA-256: `4f44f206bd1971f76f6b4b843918fd385e63c89b1e0db509f187be81034e0ba2`.
  Preserve it as mismatched transport evidence; it is not a consolidation decision.
  The precise UI cause was not reproduced, so no cause is asserted from the text alone.
- Request 02: operator reported zero accepted provider sends and stopped all future
  actions after Root's takeover instruction. Its rejected-before-acceptance stop
  dispatch was retried exactly; no provider request was retried.
- Root request: `2026-09-04-two-line-consolidation-portfolio-03-root-6pro`.
  New provider conversation: `6a9b2be3-3b34-83e8-9864-59783c44768e`.
  Observed selection: closed `6 Pro`, checked `Latest`, effort `Pro, 5 of 5.`.
  One exact `PROMPT_BODY.md` upload, provider filename `PROMPT_BODY(20260904-203624).md`;
  body SHA-256 `5e494c995cf024ab50235f2263014ea2bcd11c37de2bb2dcf8e870e3da06b835`.
  Exactly one Send. The transient `/c/WEB:...` settled to the concrete conversation
  UUID on the next observation; no second click occurred.
- Bound user message `08ce14e6-e61a-4dc7-8750-949eafdbd5c9`; paired assistant message
  `3654c1e9-6f0f-4fa9-9bc6-f94b87e3b1b8`. Natural completion showed `Worked for 11m 43s`,
  response actions, and no active generation control. Browser Copy response yielded
  28,604 characters / 42,418 UTF-8 bytes. The exact tool-returned clipboard text was
  archived without retyping or normalization; request ID/ref and text boundaries match.
  Response SHA-256: `e2bcd81c9dc99d69748c7994f73f20abb98400798eb108858ecbd5fcaf3a0940`.
- Root's request heartbeat `root-6-pro-consolidation-review` was retired to PAUSED
  after archive verification. No self-receipt was sent because caller equals parent.
- Owner follow-up: user message `edbf0ee1-b41e-4d55-86ab-b17285712824` in the same
  conversation, paired assistant `2eb86432-2e04-41ab-9416-c45e451de8e7`. Root performed
  zero Send actions for it. The owner pasted its complete reply; the original 21,325
  bytes are archived as `OWNER_FOLLOWUP_02_RESPONSE.md`, SHA-256
  `4a7a68fe7608e860829094487aa210c92cc8ec035667d66e9b3895c37f6f7e4c`.
  The browser confirms the paired message and no active generation. Its separate
  wake `owner-6-pro-route-expansion` is PAUSED; the tab stays open for owner participation.

Canonical initial packet, response and facts are in
`docs/external-review/2026-09-04-two-line-consolidation-6pro/`.
The response remains exact evidence even though its recommendation is now under revision.
The revised [two-category, six-family, nine-route proposal](2026-09-04-two-line-nine-route-proposal.md)
supersedes the initial two-investment recommendation without rewriting the first response.

## Skill changes and verification

Prompt Author propagates the configured provider requirement separately from the
Codex executor, adds request/ref response identity, and supports owner-directed
`CALLER_DIRECT` without singleton dispatch. Both author and Transport accept explicit
owner conversation replacement without inventing contamination. Binding preserves
the old record, uses a distinct request ID, and idempotently adopts the one observed
successful Send. The observed `6 Pro / Latest / Pro` tuple is supported; an old model,
unqualified `Latest`, or non-Pro mode is refused before Send.

Transport uses the available CUA methods, preserves exact input through filename
normalization, observes transient client URLs without resending, and captures the
assistant paired with the current user message. Owner stop/takeover and direct
owner follow-ups are recorded without automatic corrections or repeat delivery.
Portfolio instructions distinguish classification, complementary subdirections,
investment and execution capacity. Ordinary singleton dispatch and subsequent
wait/archive/decision authority remain unchanged.

Verification: 105 focused tests passed across Prompt Author, Transport and conversation
binding (Python 3.11.9; final run 1.50 s test wall). The three edited skills passed `quick_validate.py`.
The test runner emitted the existing `cache_dir` warning when its cache plugin was
disabled. These are control-plane checks; no experiment, learner, admission, or
scientific root was created.

Scope: none.
