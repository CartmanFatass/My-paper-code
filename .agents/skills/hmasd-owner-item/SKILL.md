---
name: hmasd-owner-item
description: Use whenever a DM or Root makes something the owner should see (a delegated object-tier decision, a frozen card, a ladder's first card, a valid-result brief, an overruled critic, a second recast, a Portfolio recommendation) and at every clean boundary to read and apply the owner's review instructions.
---

# HMASD owner items

The owner intervenes softly through `tools/owner_console/`. The loop never waits for the owner and
never writes item JSON by hand: it calls `tools/owner_console/item.py`, which validates the item
and assigns the id. The owner's replies come back as `docs/research/portfolio/owner/reviews/<date>.md`
and as the `reviews` subcommand below. Schema and layout: `docs/research/portfolio/owner/README.md`.
Rule text: `AGENTS.md` §4.4–4.5. Controlling decision:
`docs/research/portfolio/decisions/2026-09-04-owner-intervention-surfaces.md`.

## Insertion points (write an item here, in the same step, then continue)

| Moment in the loop | kind | options | extra fields |
| --- | --- | --- | --- |
| an object-tier decision is recorded in the audit ledger (`AGENTS.md` §4.1, §4.4) | `decision` | the ledger row's options, same keys; `--recommended` and `--auto-applied` = the executed one | `--ledger-row`, `--ledger-kind technical\|selection`, `--evidence` = the intake or card |
| a science card is frozen | `new-card` | default `accept / reject / revise` | `--context` = the one-sentence claim and binding structure line; `--evidence` = the card |
| a ladder's first card is frozen | `prediction` | the competing mechanisms as options | `--dm-reason` = your own prediction; `--evidence` = the card |
| a valid result is taken in and its Chinese brief written | `brief` | default `reading-agreed / reading-disputed` | `--brief` = the brief path; `--evidence` = the intake |
| you overrule a critic return ending `MATERIAL_DISSENT: yes` | `critic-dissent` | your options plus the critic's position as one option | `--evidence` = the critic return and the card |
| your recommendation and its runner-up were not clearly separated | `close-call` | as `decision` | as `decision` |
| Convergence returns a second `RECAST` for the direction | `second-recast` | default `continue-low-priority / park` | `--tier direction`, `--evidence` = the Pro archive |
| Root records a Portfolio proposal, or a DM returns a direction recommendation to Root | `portfolio` | default `ratify / refuse / amend` | `--tier portfolio`, `--direction portfolio` for cross-direction items |

The audit ledger row's evidence path names the item file the command prints.

```
python tools/owner_console/item.py add --direction <direction-id> --kind decision \
  --title "<one line>" --context "<what is decided, why now, what you saw; <= 200 words>" \
  --option a "<label>" --option b "<label>" [--consequence a "<one line>"] \
  --recommended a --auto-applied a --dm-reason "<one sentence>" \
  --evidence <path> [--evidence <path>] --ledger-row "<ledger path>#L<n>" --ledger-kind selection
```

`--direction` is the direction id from `docs/research/RESEARCH_MAP.md` (or `portfolio`); the id
prefix is derived from it. Kinds with default options need no `--option`.

## Decision packet (required for anything the owner must rule on)

`item.py add` refuses a `portfolio`, `second-recast`, `critic-dissent`, `close-call` or
`new-card` item, and any direction- or portfolio-tier item, without `--packet <file.json>` and a
non-empty `consequence` on every option. The owner cannot rule on a one-line context; the console
shows such an item as "上下文不足" and the owner's reply `needs-context` sends it back. Write the
packet in Chinese, from the material you already have (the Pro response's PORTFOLIO_EFFECTS,
RATIFICATION_CHANGES, EVIDENCE and UNCERTAINTY sections; the intake; the card):

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
`if_refused`, `evidence_for` (each with `path` and `quote`), `cost.reversibility`. A `decision` of
object tier needs no packet; its `context` paragraph and the intake link are enough because the
owner is reviewing, not ruling.

## Read point (every clean boundary)

```
python tools/owner_console/item.py reviews          # unapplied owner instructions, last 2 days
python tools/owner_console/item.py reviews --json
python tools/owner_console/item.py mark-answered <id> [<id> ...]
```

Apply each `instruction` that differs from what already ran (an override of a delegated decision
takes effect at this boundary; a `reject` or `revise` on a card is applied before its next launch;
a `prediction` reply is scored at intake; `ratify` is the owner's Portfolio ratification), cite
the review line in the ledger, then `mark-answered`. `agree` needs no action beyond
`mark-answered`. Nothing here holds a launch (`AGENTS.md` §4.5; evidence spec §11.4).

## What not to do

Do not write or edit files under `owner/inbox/` or `owner/reviews/` by hand; do not create other
owner-facing surfaces; do not wait for a reply; do not treat a missing reply as a decision.
