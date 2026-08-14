# HMASD External Review Workflow

Canonical authority is in `AGENTS.md` and `.agents/roles/`. This file describes
the compact artifact and transport sequence only.

## Default two-provider direction policy

Every eligible active algorithm direction receives two separate external
conversations by default:

1. **ChatGPT External Pro** for rigorous causal/mathematical scrutiny,
   comparator and shortcut adequacy, claim boundaries, result challenge, and
   convergence.
2. **External Gemini innovator** for divergent search using broad world/domain
   knowledge: mechanisms, analogies, overlooked regimes, counterexamples,
   scenario families, controls, and toy-to-UAV bridges.

Gemini never counts as or replaces ChatGPT External Pro. It supplies hypotheses,
not convergence, formal acceptance, technical acceptance, or portfolio choice.
The same-direction EM filters both answers locally; Root owns portfolio use and
CM owns technical acceptance. Freeze the two questions independently and retain
separate conversations, raw archives, and intakes. Agentify capacity may
serialize transport without merging the reviews.

## Research Operations Manager sequence

1. Research Operations Manager follows the active grant or exact clarification
   request and authors the reviewer-visible brief, allow-list and question.
2. Research Operations Manager commits and pushes that exact boundary.
3. The registered Pro transport submits the ChatGPT External Pro question once;
   the registered Gemini transport separately submits the divergent Gemini
   question once when Agentify capacity is idle.
4. Each exact natural response is archived and accompanied by its own
   provenance-bound same-direction intake. Neither archive is a substitute for
   the other and neither provider receives the other's current answer by
   default.
5. The same-direction scientific owner reconciles Gemini as innovation input
   and ChatGPT External Pro as rigorous review input. Root decides portfolio use;
   local scientific and technical authority remain unchanged.

Each provider owns only its exact question-scoped answer. The same-direction
scientific owner owns interpretation; Root owns portfolio use; Code Project
Manager owns implementation and technical acceptance. Neither review itself
authorizes code or compute.

## Transport identity

The defining rules are in `.agents/skills/hmasd-agentify-pro-transport/SKILL.md`.

## Round files

```text
rounds/YYYYMMDD_topic/
  00_REVIEW_BRIEF.md
  01_SHARED_SOURCE_MANIFEST.md
  20_PRO_OPEN_QUESTION.md
  21_PRO_OPEN_RAW.md
  50_MECHANICAL_INTAKE_RECORD.md
```

Historical files retain their original authorship markers. New rounds use
Research Operations Manager direct transport. There is no Controller, Exchange
task, dispatcher, separate persistent transport task or completion callback.
