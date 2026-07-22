# HMASD External Review Workflow

External GPT-5.6 Pro owns scientific CDC direction. The active Controller owns
round sequencing, factual reconciliation, direct evidence intake, durable
record application, resource authorization and every Git-visible boundary. One
persistent Open-Pro Exchange owns external transport, exact raw capture and its
heartbeat. The native Codex Project Manager later owns executable algorithm realization
for an authorized implementation action; it does not reconverge the science.

## Scientific sequence

1. GPT-5.6 Pro performs CDC scientific review of the Git-visible evidence under
   `OPEN_REVIEW_PRINCIPLES.md`, preserving plural conjectures while selecting
   one scheduled research action.
2. The Controller writes factual reconciliation without changing the science,
   applies the exact durable CDC record deltas and shows the Pro user brief.
3. The Controller writes `50_DISPOSITION.md` and updates project control once.
4. If implementation is selected and separately authorized, the Controller
   dispatches the registered native Codex Project Manager with the Pro scientific direction,
   estimand, evidence and resource boundary. The Manager decides the complete
   executable algorithm and manages its code-agent task tree.

Review and direct evidence intake do not authorize code or training. Pro owns
science; Project Manager owns authorized algorithm realization; Controller owns
the workflow and resource gate. The target remains a stronger MARL algorithm,
while hierarchy, skills, variable lifetime, ordinary-MARL controls and causal
diagnostics are mechanisms or evidence, not universal prerequisites.

`docs/project/ALGORITHM_PRINCIPLES.md` is the common scientific contract and
`OPEN_REVIEW_PRINCIPLES.md` specializes the external Pro role. Direct intake
guidance lives in the Controller `hmasd-review-round` Skill.

## Direct Exchange interface

The controller prepares and pushes each immutable reviewer-visible boundary,
then resolves and sends one compact stage assignment directly to the registered
Exchange session:

```text
REVIEW_STAGE
role_skill=.agents/skills/hmasd-review-exchange/SKILL.md
reviewer_role=OPEN_DIVERGENT
round=<round-id>
stage_commit=<40-character pushed SHA>
round_path=docs/external-review/rounds/<round-id>
question=<round-relative question path>
raw=<round-relative raw path>
completion_policy=ARCHIVE_NATURAL_RESPONSE_AND_REPORT_QUALITY
```

The Exchange returns `REVIEW_STAGE_COMPLETE` or `REVIEW_STAGE_BLOCKED` directly
to the Controller through the persistent task dispatcher. After raw
verification, the Controller writes reconciliation and applies direct evidence
intake. There is no independent Intake or persistent Manager relay.

Each raw has exactly one writer: its registered Exchange. A raw becomes
immutable after that Exchange verifies natural response completion and exact
captured-text equality after rereading the file. Every naturally completed
response is preserved even when its content has gaps. The Exchange reports a
semantic quality note; the Controller decides whether the scientific contract
needs a focused Pro follow-up. A content gap is not a transport failure. An
externally accepted stage is never resubmitted.

Each Pro Exchange uses one browser lifecycle per assigned stage. At the end of
a waiting wake it finalizes the registered page with `status: "handoff"`, which
keeps the page open after automation releases it. The next wake first claims
that exact user-visible page and never creates or reloads a duplicate. It closes
the page once only after raw archival, controller callback and heartbeat
cleanup. Navigation recovery is allowed only when the registered page is absent
from both controlled and user-visible tabs.

The workflow uses no intermediate persistent session, Git handoff callback, or
review state file. The controller has no review heartbeat. Each Exchange
independently owns one 5-minute heartbeat only while its external response or
direct callback is pending, and deletes it after callback delivery is
confirmed.

## Round files

New review work lives under one round directory:

```text
rounds/YYYYMMDD_topic/
  00_REVIEW_BRIEF.md
  01_SHARED_SOURCE_MANIFEST.md
  20_PRO_OPEN_QUESTION.md
  21_PRO_OPEN_RAW.md
  30_EVIDENCE_RECONCILIATION.md
  50_DISPOSITION.md
```

Raw responses are byte-preserved and precede downstream use. Controller round
behavior lives in `.agents/skills/hmasd-review-round/SKILL.md`; registered
Exchange behavior lives in `.agents/skills/hmasd-review-exchange/SKILL.md`.
Direct scientific evidence intake lives in the Controller round Skill.
Algorithm realization and implementation behavior live with the registered
`project_manager` role. Persistent task IDs contain only the
Controller and Open-Pro Exchange in the dispatcher's `session-roles.json`;
external reviewer conversations and URLs live only in
`REVIEWER_CONVERSATIONS.json`.
