# HMASD External Review Workflow

External GPT-5.6 Pro owns scientific CDC decisions. The active controller owns
round sequencing, factual reconciliation, adoption and every Git-visible
boundary. One persistent Open-Pro Exchange owns external transport, exact raw
capture and its heartbeat. The Research Project Manager preserves the Pro
decision, maintains the research records and checks operational executability;
it does not independently reconverge the science.

## Scientific sequence

1. GPT-5.6 Pro performs CDC scientific review of the Git-visible evidence under
   `OPEN_REVIEW_PRINCIPLES.md`, preserving plural conjectures while selecting
   one scheduled research action.
2. The controller writes factual reconciliation without changing the science.
3. The Research Project Manager performs `CDC_DECISION_INTAKE`: it projects the
   Pro decision onto durable records and checks operational feasibility.
4. The controller shows the resulting user brief, adopts or rejects the action,
   writes `50_DISPOSITION.md` and updates project control once.

Review does not authorize code or training. Pro owns science; the Manager owns
evidence-preserving operationalization. The target remains a stronger MARL
algorithm, while hierarchy, skills, variable lifetime, ordinary-MARL controls
and causal diagnostics are mechanisms or evidence, not universal prerequisites.

`docs/project/ALGORITHM_PRINCIPLES.md` is the common scientific contract and
`OPEN_REVIEW_PRINCIPLES.md` specializes the external Pro role. Operational
intake guidance lives only in the Research Project Manager Skill.

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
to the controller through the task dispatcher. After raw verification, the
controller writes reconciliation and sends one `CDC_DECISION_INTAKE` to the
Research Project Manager. The manager owns no heartbeat and returns
`CDC_DECISION_BRIEF` or `RESEARCH_MANAGER_BLOCKED`.

Each raw has exactly one writer: its registered Exchange. A raw becomes
immutable after that Exchange verifies natural response completion and exact
captured-text equality after rereading the file. Every naturally completed
response is preserved even when its content has gaps. The Exchange reports a
semantic quality note; the controller and Research Project Manager decide
whether the scientific contract is sufficient or needs a focused follow-up. A
content gap is not a transport failure. An externally accepted stage is never
resubmitted.

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
Scientific intake and implementation behavior live in
`.agents/skills/hmasd-project-manager/SKILL.md`.
Codex task IDs and role bindings live only in the dispatcher's
`session-roles.json`; external reviewer conversations and URLs live only in
`REVIEWER_CONVERSATIONS.json`.
