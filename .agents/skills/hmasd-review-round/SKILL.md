---
name: hmasd-review-round
description: Use only by the active HMASD controller for a tracked external GPT-5.6 Pro scientific CDC decision. It creates and pushes one reviewer-visible question, dispatches the registered Open-Pro Exchange through $hmasd-dispatch-task, archives the natural response exactly, writes factual reconciliation, and sends the Pro decision to the Research Project Manager for evidence-preserving intake and operationalization.
---

# HMASD External Pro Research Round

## Scope

External GPT-5.6 Pro is the scientific decision source. It owns conjecture and
definition correction, derivation, counterexample search, retained lemmas,
portfolio meaning and selection of one scheduled research action. That action
serializes resources; it does not make other defensible explanations illegal.

The controller owns reviewer-visible Git boundaries, factual reconciliation,
adoption, durable record writes and user communication. It never operates the
browser or replaces the Pro scientific judgment. The Research Project Manager
checks provenance and executability and translates an adopted implementation
action; it does not independently reconverge the science.

Use a full plural review for competing explanations, proposed family
retirement, benchmark-identification disputes, repeated ambiguity or
full-algorithm integration. Use a focused continuation in the same registered
Pro conversation for a local scientific ambiguity or correction. Both use the
same exact evidence and raw-archive discipline.

## Round boundary

```text
docs/external-review/rounds/<round>/
  00_REVIEW_BRIEF.md
  01_SHARED_SOURCE_MANIFEST.md
  20_PRO_OPEN_QUESTION.md
  21_PRO_OPEN_RAW.md
  30_EVIDENCE_RECONCILIATION.md
  50_DISPOSITION.md
```

Before dispatch, commit and push the brief, manifest and question. Run
`scripts/verify_pro_review_boundary.ps1` with the 40-character pushed SHA and
question path. List the scientific principles and every exact Git-visible
evidence path.

The question asks Pro to return:

- plural live conjectures and their scopes;
- derived intervention, natural and held-out consequences;
- concrete counterexamples and retained lemmas;
- the smallest refuted unit in existing evidence;
- one scheduled research action chosen by information gain, cost and
  reversibility;
- evidence semantics to freeze if that action is adopted;
- reactivation conditions for unscheduled ideas;
- a concise Chinese user brief.

Pro must not equate one scheduled action with one legal successor or write an
implementation plan. If implementation is selected, it defines the scientific
object and estimand; the Manager later freezes executable architecture.

## Procedure

1. Dispatch one `REVIEW_STAGE` to `open_divergent_exchange` with explicit
   `$hmasd-dispatch-task` and `$hmasd-review-exchange` activation.
2. Accept a naturally completed raw only from that task. Preserve semantic
   quality notes separately from transport validity.
3. Write factual `30_EVIDENCE_RECONCILIATION.md` without changing Pro science.
4. Send `CDC_DECISION_INTAKE` to `research_project_manager` with the raw,
   reconciliation, CDC records and evidence.
5. Show the returned Chinese brief. Controller adoption permits one
   disposition, durable CDC updates and project-control update. A material
   scientific ambiguity returns as one focused continuation to the same Pro.

## Exchange dispatch

```text
$hmasd-dispatch-task
$hmasd-review-exchange

REVIEW_STAGE
role_skill=.agents/skills/hmasd-review-exchange/SKILL.md
reviewer_role=OPEN_DIVERGENT
round=<id>
stage_commit=<40-character pushed SHA>
round_path=docs/external-review/rounds/<id>
question=docs/external-review/rounds/<id>/20_PRO_OPEN_QUESTION.md
raw=docs/external-review/rounds/<id>/21_PRO_OPEN_RAW.md
completion_policy=ARCHIVE_NATURAL_RESPONSE_AND_REPORT_QUALITY
```

Resolve the Exchange immediately before sending, copy its live route fields
unchanged, require delivery proof and verify post-send invariance.

## Manager intake

```text
$hmasd-dispatch-task
$hmasd-project-manager

CDC_DECISION_INTAKE
role_skill=.agents/skills/hmasd-project-manager/SKILL.md
research_id=<round>:cdc-intake
inputs=<brief, raw, reconciliation, CDC records and evidence paths>
question=Preserve the Pro decision, update the durable research objects, and assess operational executability without making a new scientific choice.
```

This is read-only and creates no write lease or heartbeat.

## Recovery

There is no review state file or controller heartbeat. A naturally completed
raw with gaps remains valid transport. If a gap changes science, ask the same
Pro one focused question; if it is engineering-only, the Manager bounds it.
Never prescribe selectors, clicks or browser commands. Review and intake never
authorize implementation or compute by themselves.
