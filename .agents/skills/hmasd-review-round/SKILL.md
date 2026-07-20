---
name: hmasd-review-round
description: Use only by the active HMASD controller for one complete tracked external-review round or one focused follow-up to an already accepted Convergent disposition. It prepares and pushes reviewer-visible boundaries, dispatches only the required registered reviewer-exchange sessions through the task router, validates immutable raw callbacks, writes the accepted disposition, and never operates an external reviewer itself.
---

# HMASD External Review Round

## Scope

This is a controller workflow, not a persistent-session role. Use it for either
a complete tracked round whose unresolved scientific question requires two
blind divergent reviews followed by one convergent review, or the narrowly
defined focused Convergent follow-up below. Do not use it for an ordinary
prompt, one returned answer, routine result interpretation, literature
discussion, or a disposition that is already code-ready.

The controller also reads:

1. `../hmasd-task-router/SKILL.md`;
2. `../hmasd-task-router/references/session-roles.json`;
3. this Skill;
4. `docs/external-review/REVIEWER_CONVERSATIONS.json`;
5. the named round directory and its explicitly listed evidence.

The controller owns round files, Git-visible boundaries, direct Exchange
dispatch, callback acceptance, and the final project-state update. It never
controls a reviewer browser or Antigravity; each Exchange session owns its
transport, raw and heartbeat.

## Reviewer Principle Binding

Use role-specific Git-visible scientific contracts rather than copying generic
review prose into every round:

- both `10_GEMINI_DIVERGENT_QUESTION.md` and
  `20_PRO_OPEN_QUESTION.md` must list
  `docs/project/ALGORITHM_PRINCIPLES.md` and
  `docs/external-review/OPEN_REVIEW_PRINCIPLES.md` in their evidence inputs;
- `40_PRO_CONVERGENT_QUESTION.md` must list
  `docs/project/ALGORITHM_PRINCIPLES.md` and
  `docs/external-review/CONVERGENT_REVIEW_PRINCIPLES.md`.

Open questions request a plural portfolio and must not select one successor.
The convergent question requests evidence validation, weighted synthesis, one
next evidence source or stop, and preservation of valuable unselected ideas.
Keep round-specific facts, required output fields, and evidence paths in the
question; keep durable role behavior only in the corresponding principle file.
Never give an open reviewer the convergent principle file or a convergent
reviewer the open principle file as an instruction source.

## Round Boundary

For one round require:

```text
round=<id>
evidence_commit=<40-character pushed SHA>
round_path=docs/external-review/rounds/<id>
```

The initial boundary contains `00_REVIEW_BRIEF.md`, the shared and local source
manifests, and the two divergent questions. Before any dispatch, verify the
commit, assigned question, base algorithm principles, and matching role
principle file are present on `My-paper-code/aggressive`.
The controller may stage, commit and push only the current round paths needed by
the next stage.

## Direct Exchange Procedure

1. dispatch Gemini and Open-Pro blind divergent stages directly and
   independently to `gemini_divergent_exchange` and
   `open_divergent_exchange`;
2. accept each raw only from its registered Exchange callback and verify the
   required sections plus exact-text-equality claim;
3. write `30_EVIDENCE_RECONCILIATION.md` as a factual reconciliation without
   ranking routes, then write `40_PRO_CONVERGENT_QUESTION.md` under the
   convergent principle contract;
4. commit and push that round boundary;
5. dispatch the convergent stage directly to `convergent_exchange`;
6. after its verified raw returns, write `50_DISPOSITION.md`, commit and push
   it, then update the owning project-control boundary once.

Every dispatch is exactly:

```text
REVIEW_STAGE
role_skill=.agents/skills/hmasd-review-exchange/SKILL.md
reviewer_role=<GEMINI_DIVERGENT|OPEN_DIVERGENT|CONVERGENT>
round=<id>
stage_commit=<40-character pushed SHA>
round_path=<round_path>
question=<round-relative question path>
raw=<round-relative raw path>
```

Resolve only the matching registered Exchange immediately before each send and
copy its live `hostId`, `threadId`, `model`, and `thinking` unchanged. Delivery
requires the send tool to return that same Exchange task ID. Never route through
another persistent session.

Gemini and Open Pro may run concurrently because their sessions, source views,
raws and heartbeats are disjoint. Convergent starts only after both verified
divergent raws, factual reconciliation and its question are in one pushed
commit.

## Focused Convergent Follow-up

Use exactly one focused follow-up when an accepted Convergent disposition has
already frozen the scientific source and portfolio but omitted scientific
values that the Code Implementation Manager is forbidden to choose, such as
task dynamics, information contracts, model, budget, seeds, absolute floors or
material margins.

For this case:

1. create a new tracked follow-up directory containing only
   `00_REVIEW_BRIEF.md` and `40_PRO_CONVERGENT_QUESTION.md` before dispatch;
2. bind the question to the accepted disposition, its Convergent raw,
   `ALGORITHM_PRINCIPLES.md`, and `CONVERGENT_REVIEW_PRINCIPLES.md`;
3. ask only for the missing code-ready contract and allow an explicit stop if
   no defensible contract can be frozen;
4. commit, push and verify the question boundary, then dispatch only the
   registered `convergent_exchange` with the ordinary `REVIEW_STAGE` schema;
5. archive `41_PRO_CONVERGENT_RAW.md`, adopt one focused disposition, and then
   update project control once.

Do not create divergent questions, dispatch Gemini or Open Pro, reconsider the
selected source, reweight the portfolio, or count this clarification as a new
evidence-bearing research iteration. This is a completion of the prior
scientific contract, not a new full external-review round.

## Callback and Recovery

Accept only `REVIEW_STAGE_COMPLETE` or `REVIEW_STAGE_BLOCKED` from the Exchange
task registered for the declared reviewer role. Require matching native
`source_thread_id`, stable `handoff_id`, round, question/raw assignment, and the
role Skill terminal schema. A duplicate callback with the same handoff is
idempotent.

There is no review state machine and no controller heartbeat. Derive progress
from immutable round artifacts plus callbacks. If a raw already exists, send
the same stage to its owning Exchange for one completion/equality verification;
never resubmit the external question from the controller. A blocked Exchange is
a terminal operational blocker for the round unless the user explicitly repairs
or replaces that registered Exchange.

External review recommends scientific action but never grants code or
experiment authority. The controller operationalizes only the accepted
`50_DISPOSITION.md` within current user authority.
