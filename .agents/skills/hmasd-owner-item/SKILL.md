---
name: hmasd-owner-item
description: Use when DM or Root records a P1/P2 owner item (new card, direction decision, material dissent, close call, second recast or Portfolio proposal), and at clean boundaries to apply owner reviews.
---

# HMASD owner items

## Maintained items and authority

Maintain P1/P2 items only. Ordinary delegated object decisions, predictions, technical
facts and result briefs belong in card/intake/audit records, without separate review items.
Keep every scientific card, prediction, result, Chinese brief and required audit record.
`item.py add` returns `skipped` without an ID or file for P3/P4; cite the card/intake
directly and do not upgrade an ordinary item to manufacture a higher priority.

Apply AGENTS §4.7 for a complete Pro-directed specification plan within delegated scope.
Read/archive the full decision, implement its exact authorized plan, and use `item.py trace`
on the relevant P1/P2 item with the actual authority, source, application record and state.
Do not fabricate owner replies, accept code solely from a rule change or broaden scope.

The owner intervenes softly through `tools/owner_console/`. The loop never waits for the owner and
never writes item JSON by hand: it calls `tools/owner_console/item.py`, which validates the item
and assigns the id. The owner's replies come back as `docs/research/portfolio/owner/reviews/<date>.md`
and as the `reviews` subcommand below. Schema and layout: `docs/research/portfolio/owner/README.md`.
Rule text: `AGENTS.md` §4.4–4.5. Controlling decision:
`docs/research/portfolio/decisions/2026-09-04-owner-intervention-surfaces.md`.

## Insertion points (write an item here, in the same step, then continue)

| Moment in the loop | kind | options | extra fields |
| --- | --- | --- | --- |
| a direction- or portfolio-tier decision is recorded | `decision` | the recorded options, recommendation and actual executed choice | explicit `--tier`, `--packet`, `--ledger-row`, `--evidence` |
| a science card is frozen | `new-card` | default `accept / reject / revise` | `--context` = the one-sentence claim and binding structure line; `--evidence` = the card |
| you overrule a critic return ending `MATERIAL_DISSENT: yes` | `critic-dissent` | your options plus the critic's position as one option | `--evidence` = the critic return and the card |
| your recommendation and its runner-up were not clearly separated | `close-call` | as `decision` | as `decision` |
| Convergence returns a second `RECAST` for the direction | `second-recast` | default `continue-low-priority / park` | `--tier direction`, `--evidence` = the Pro archive |
| Portfolio records its conforming Pro decision | `portfolio` | default `keep / refuse / amend` | `--tier portfolio`, `--direction portfolio` for cross-direction items |

For a created P1/P2 item, the audit row can cite the returned item path. A `skipped`
result has no item path; ordinary audit rows cite the card/intake directly.

```
python tools/owner_console/item.py add --direction <direction-id> --kind close-call \
  --title "<one line>" --context "<what is decided, why now, what you saw; <= 200 words>" \
  --option a "<label>" --option b "<label>" --consequence a "<effect>" --consequence b "<effect>" \
  --recommended a --auto-applied a --dm-reason "<one sentence>" \
  --packet <packet.json> --evidence <path> --ledger-row "<ledger path>#L<n>" --ledger-kind selection
```

`--direction` is the direction id from `docs/research/RESEARCH_MAP.md` (or `portfolio`); the id
prefix is derived from it. Kinds with default options need no `--option`.

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
`mark-answered`. Nothing here holds a launch (`AGENTS.md` §4.5; evidence spec §11.4).

For prospective Portfolio decisions under AGENTS §4.8, `keep` or `agree` acknowledges the
record without granting fresh authorization. `refuse` or `amend` is an asynchronous override
at the next clean boundary; preserve executed effects and do not infer a rerun or reversal.
Custom option keys retain their actual recorded meanings. Preserve historical items and replies.
Use `trace` for planned/applied/blocked state; `auto_applied` records only an executed option.
The retained packet field `changes_if_approved` describes the disposition's changes, not a new
ratification gate. Read/archive Pro and record the designated DM's conformance check before application.

## What not to do

Do not write or edit files under `owner/inbox/` or `owner/reviews/` by hand; do not create other
owner-facing surfaces; do not wait for a reply; do not treat a missing reply as a decision.
