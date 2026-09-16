---
name: hmasd-owner-item
description: Mechanically publish required confirmation-result or lifecycle/Portfolio owner items and apply real owner reviews at clean boundaries; not routine pilot records.
---

# HMASD owner items

## Trigger, input and normal publication

Input is an already determined lifecycle/Portfolio decision or confirmatory result with
options, recommendation, actual executed choice, evidence and provenance. This skill
publishes it; it does not choose which research to run or create a review requirement.
Pilots have no automatic owner item/brief. Ordinary technical facts and predictions stay
in card/summary/intake. Audit only selection decisions with real alternatives. Maintain
P1/P2 only; item.py skipped returns no ID/file and never justifies upgrading the item.

Use tools/owner_console/item.py, never hand-edit inbox/reviews. For a decision use add
with --direction, --kind decision (or portfolio), --tier, --title, --context,
--option/--consequence for each option, --recommended, --auto-applied only if executed,
--dm-reason, --packet, --evidence and --ledger-row when a selection row exists.
Existing kinds new-card, critic-dissent, close-call and second-recast remain usable
inside required confirmation/lifecycle reporting, not an independent every-event trigger.
Do not manufacture a selection row for a technical fact. See item.py --help for fields;
owner/README.md describes the existing packet schema only, not broader triggers.

For confirmation results provide the Chinese brief under
`docs/research/portfolio/owner/briefs/<direction>/<date>_<object>.md`, under 600 characters,
with 问题, 机制与比较器, 结果一句话, 预测核对, 排除了什么, 下一步与需要你做的.
Keep technical SHA/fields in English intake. Score actual predictions or mark not taken.
For an authorized scoped specification plan archive the full source and use item.py trace
on an applicable existing item with actual authority, source, application record/state.
No fabricated reply, new code acceptance or run authority follows.

## Decision packet (required for P1/P2 review)

`item.py add` refuses a `portfolio`, `second-recast`, `critic-dissent`, `close-call` or
`new-card` item, and any direction- or portfolio-tier item, without `--packet <file.json>` and a
non-empty `consequence` on every option. The owner cannot rule on a one-line context; the console
shows such an item as "上下文不足" and the owner's reply `needs-context` sends it back. Write the
packet in Chinese, from the material you already have (the Pro response's relevant
conclusions and evidence, the intake, or the card). Pro prose needs no named sections:

```json
{
  "question": "一句话：要所有者决定什么",
  "changes_if_approved": [
    {"target": "PORTFOLIO.md · semigroup_consistent_duration_model_policy", "from": "无 second-recast 标记", "to": "second-recast，最低争用排序，仍 ACTIVE/HIGH"}
  ],
  "if_refused": "拒绝后循环怎么走，什么保持不变",
  "evidence_for": [
    {"path": "<repo path>", "quote": "≤2 句原文", "why": "为什么它支持推荐项"}
  ],
  "evidence_against": [
    {"path": "<repo path>", "quote": "≤2 句原文", "why": "为什么要谨慎"}
  ],
  "uncertainty": ["未决点或复审触发条件，每条一句"],
  "cost": {"compute": "…", "owner_time": "…", "reversibility": "reversible | costly | irreversible", "waits_on_this": "等待此决定的事，或 nothing"},
  "verdict_text": "裁决原文（Pro 的 OWNER_RATIFICATION_TEXT 或 DM 的建议段），逐字",
  "source": "<path of the Pro response, intake or card>"
}
```

Required: `question`, `changes_if_approved` (at least one entry, or one string `"none"`),
`if_refused`, `evidence_for` (each with `path` and `quote`), `cost.reversibility`.

## Read point (every clean boundary)

```
python tools/owner_console/item.py reviews          # all unapplied owner instructions, regardless of age
python tools/owner_console/item.py reviews --json
python tools/owner_console/item.py mark-answered <id> [<id> ...]
```

Apply each `instruction` that differs from what already ran (an override of a delegated decision
takes effect at this boundary; a `reject` or `revise` on a card is applied before its next launch;
a `prediction` reply is scored at intake; legacy `ratify` retains its original meaning), cite
the review line in the ledger, then `mark-answered`. `agree` needs no action beyond
`mark-answered`. Nothing here holds a launch (publishing is not approval).

For prospective Portfolio decisions under standing owner delegation, `keep` or `agree` acknowledges the
record without granting fresh authorization. `refuse` or `amend` is an asynchronous override
at the next clean boundary; preserve executed effects and do not infer a rerun or reversal.
Custom option keys retain their actual recorded meanings. Preserve historical items and replies.
Use `trace` for planned/applied/blocked state; `auto_applied` records only an executed option.
The retained packet field `changes_if_approved` describes the disposition's changes, not a new
ratification gate. Read/archive Pro and record the author parent's conformance check (the designated author DM) before application.

## What not to do

Do not write or edit files under `owner/inbox/` or `owner/reviews/` by hand; do not create other
owner-facing surfaces; do not wait for a reply; do not treat a missing reply as a decision.

Return the actual item path/ID or skipped, brief and evidence links, applied review and unresolved gap. Missing publication facts do not authorize a scientific substitute.
