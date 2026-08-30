---
name: hmasd-hypothesis-mechanisms
description: Generate or validate bounded local mechanism cards with explicit rivals, predictions, discriminators, controls, assumptions, and falsifiers when an EM requests this professional tool.
---

# HMASD Hypothesis Mechanisms

## Purpose and activation

Use this Skill only on demand for an exact direction-scoped gap supplied by its
Experiment Manager (EM). It is not a manager autoload and does not start a
research cycle, choose a family, allocate work, or change state. The tool makes
a proposed mechanism inspectable without treating it as evidence or a finding.
EM retains scientific synthesis, claim-ceiling, disposition, and lifecycle
authority.

The implementation is local, deterministic, standard-library-only, and has no
network, subprocess, provider, credential, registry, Portfolio, runtime-state,
RNG, numerical, checkpoint, or external effect. It does not retrieve or invent
evidence. An absent evidence declaration is represented explicitly as
`evidence_status: "not_reported"` with an empty `evidence_references` array.

## Frozen input

The EM-supplied draft must retain the HMASD common analytical product fields:

- assignment and gap IDs, task family, frozen claim, and
  `MATERIAL_INSIGHT | NO_MATERIAL_INSIGHT`;
- exact evidence reference IDs and locators, or explicit `not_reported`;
- assumptions and applicability boundaries;
- a falsifier or counterexample;
- uncertainty and limitations;
- consequence or decision relevance; and
- a recommendation for EM consideration, never an automatic decision.

Each proposed card is labeled by structure as a candidate and declares:

- the candidate statement, mechanism family, and process statement;
- explicit assumptions and boundary conditions;
- observable predictions with conditions, expected pattern, and uncertainty;
- at least one rival mechanism and a contrast with that rival;
- at least one discriminator linking predictions to rivals, including an
  indeterminate outcome and explicit controls;
- at least one falsifier, the assumptions under which it applies, and its
  consequence; and
- admissible packet IDs. An empty packet list is allowed and does not authorize
  information from outside the frozen packet.

Do not add scores, ranks, votes, probabilities, preferred candidates, fixed
candidate counts, novelty verdicts, evidence claims, acceptance labels, or
lifecycle recommendations. Zero or any gap-justified number of cards is valid.

## Commands

Generate content-addressed artifact and card IDs while preserving all supplied
scientific content:

```bash
python3 tools/research/hypothesis_mechanisms/mechanism_cards.py generate draft.json -o result.json
```

Validate an already generated artifact:

```bash
python3 tools/research/hypothesis_mechanisms/mechanism_cards.py validate artifact.json -o result.json
```

Use `-` as the input or output path for standard input or standard output. Both
commands return deterministic JSON. Exit code `0` means structurally valid,
`1` means completed validation with structural/internal-consistency issues, and
`2` means malformed or unreadable input. The local result envelope separates
`technical_status` from the fixed `scientific_status_effect: "NONE"` and
`lifecycle_status_effect: "NONE"` declarations.

Generation supplies only `schema_version`, `artifact_id`, and each `card_id`.
It never fills a scientific declaration, resolves a missing link, fabricates a
source, or selects a candidate. Re-running generation on identical JSON content
produces identical identifiers and bytes.

## Validation boundary

The validator checks only declarations and internal consistency:

- required fields, types, bounded identifiers, and unique IDs;
- nonempty rival, discriminator, falsifier, prediction, assumption, boundary,
  control, and uncertainty structures inside each present card;
- that every prediction names declared rivals, falsifiers, and discriminators;
- that discriminator and falsifier references resolve within the card;
- that each declared rival and falsifier is linked;
- reported-versus-not-reported evidence consistency;
- deterministic content identifiers; and
- the immutable `scientific_authority: "EM"` and no-effect declarations.

A successful validation says only that the artifact is structurally coherent.
It does not establish truth, evidential support, novelty, feasibility, safety,
scientific acceptance, rejection, ranking, or lifecycle status. A failed
validation is a technical artifact defect, not evidence against a mechanism.

## `NO_MATERIAL_INSIGHT`

`NO_MATERIAL_INSIGHT` is a successful negative-complete analytical product, not
a technical failure or scientific rejection. Its artifact records exact sources
inspected, methods attempted, why no answer-changing insight follows within the
frozen scope, and residual uncertainty. It may contain zero mechanism cards.
The validator does not change the claim, resample the task, or treat missing
material insight as evidence of absence. EM alone interprets and records the
scientific consequence and any reentry trigger.

## Upstream attribution and license

This bounded adaptation uses the object separation, rival-prediction,
falsification, control, and non-scoring validation patterns from
`K-Dense-AI/scientific-agent-skills` at immutable commit
`f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f`, specifically:

- `skills/hypothesis-generation/SKILL.md`;
- `skills/hypothesis-generation/assets/hypothesis_record_template.json`;
- `skills/hypothesis-generation/scripts/validate_hypothesis_schema.py`;
- `skills/hypothesis-generation/assets/falsification_controls_template.json`;
  and
- `skills/hypothesis-generation/scripts/check_falsification_controls.py`.

The upstream work is licensed under the MIT License:

> Copyright (c) 2025 K-Dense Inc.
>
> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions:
>
> The above copyright notice and this permission notice shall be included in all
> copies or substantial portions of the Software.
>
> THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
> IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
> FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
> AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
> LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
> OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
> SOFTWARE.
