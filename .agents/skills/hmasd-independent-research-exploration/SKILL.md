---
name: hmasd-independent-research-exploration
description: Use in the user-controlled HMASD Independent Research Explorer task to investigate research directions, papers, counterexamples, or testable hypotheses with parallel read-only Scouts and Critics while keeping all outputs advisory and confined to local_research.
---

# HMASD Independent Research Exploration

## Purpose

Explore HMASD-relevant ideas without entering the formal project workflow.
Preserve the initial mission and the several-live-conjectures discipline in
`docs/project/ALGORITHM_PRINCIPLES.md sections 1 and 3`, but do not make a
canonical scientific decision.

The Explorer is a persistent `gpt-5.6-sol/ultra` task and the only writer. It
may launch read-only Sol-high Scouts for breadth and Sol-max Critics for
high-value challenges. All durable outputs remain under `local_research`.

## Start safely

1. Confirm the active task session matches the registered Explorer session.
2. Read the Explorer role and only sections 1 and 3 of the algorithm principles.
3. Restate the question, mission connection, mode, exclusions and completion
   condition. Ask the user only when one of those fields is materially missing.
4. For MyLib, read [references/mylib.md](references/mylib.md) and run the
   registered probe. Never write to MyLib.
5. Read [references/parallel-research-workflow.md](references/parallel-research-workflow.md)
   before dispatching children.

Do not read `CURRENT_WORK.md`, active runtime/review state, implementation or
scientific ledgers. Do not use Git or create project changes.
Write advisory files only with `apply_patch` under `local_research`; the
research session's shell is read-only.

## Choose the research mode

Use **quick exploration** for route finding. Recall at most 12 candidates,
read structured content for at most 6 papers, launch 1-4 disjoint Scouts, and
use a Critic only for a central or conflicting claim.

Use **deep evidence review** when the user requests a decision-quality research
map. Freeze a bounded candidate set, inspect structured evidence and required
PDF fidelity boundaries, launch up to 4 Scouts, then up to 2 Critics after the
merge barrier. State uncovered literature and unresolved ambiguity explicitly.

## Use MyLib evidence correctly

Read live `metadata/integrity.json` first; never hard-code corpus counts or
missing IDs. Require its `metadata_v2.status=validated`, then use the exact
registered sequence: `llm-index/catalog.v2.jsonl` for lightweight recall,
`metadata/v2/papers.v2.jsonl` for the selected records, and
`metadata/v2/schema.v2.json` plus `quality-report.v2.json` for interpretation.
For every candidate inspect `quality.grade`, `quality.warnings` and
`provenance.field_evidence` before opening content. Never use the retired
`catalog.jsonl` or a Metadata v2 staging file from `papers/temp`.

Metadata v2 algorithm, setting, benchmark, contribution and related research
facets are Luna analyses grounded in the title or abstract. They improve recall
but do not verify full-text details. Empty arrays and `unspecified` remain
unknown; never fill them from domain knowledge. Method details, equations,
experimental values and limitations must return to the candidate JSON by page
and element, with PDF verification when required.

`structured JSON is the formal LLM content layer`. Record its absolute path and
page/element/bbox locator for claims derived from it. `PDF is required for original verification, formula/figure/table semantics, or missing JSON`.
Use assets only with their JSON coordinates. `legacy Markdown is excluded`:
never search or cite `papers/temp/acquisition/legacy-markdown-*`.

For a record whose structured JSON is missing, the exact official abstract and
its `evidence_url` may guide recall only when the full metadata marks it
`abstract_only`. Any method-detail claim still requires the original PDF.

The probe performs mechanical integrity, catalog, JSON and PDF checks:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-independent-research-exploration/scripts/mylib_research_probe.py `
  --mylib-root "C:/Projects/Inst-sci/papers/MyLib" `
  --local-research-root "./local_research" status
```

Use `search`, `locate`, `validate-pdf` and `smoke` subcommands as routed in the
reference. The script may write a receipt only when `--output` resolves under
`local_research`.

## Require evidence packets

Each Scout returns one `SCOUT_EVIDENCE_PACKET` with:

- assignment ID and non-overlapping research axis;
- search terms, candidates, exclusions and coverage limit;
- evidence rows containing claim, claim kind, paper ID, title, absolute
  JSON/PDF path, locator and confidence;
- supporting, conflicting and boundary evidence;
- testable hypotheses and unresolved facts.

Each selected Critic returns one `CRITIC_ASSESSMENT_PACKET` with:

- exact claim and packet identities assessed;
- evidence identity and fidelity audit;
- strongest counterexample and alternate explanation;
- supported, weakened, contradicted and unresolved dispositions;
- smallest discriminating observation or experiment, without executing it.

Reject a packet that substitutes index excerpts for content evidence, omits
source identity, reads legacy Markdown, exceeds its axis or claims project
authority. A metadata-derived claim must also name its field provenance,
evidence locator, extraction method, confidence and verification state; absent
provenance reduces the field to recall-only guidance.

## Synthesize without promotion

After all packets cross the merge barrier, deduplicate evidence by paper ID and
claim, reconcile conflicts and write one local report. Include:

- question and mission connection;
- mode, retrieval terms, coverage and exclusions;
- evidence matrix and fidelity level;
- supporting and conflicting findings;
- Explorer inferences separated from paper claims;
- several live or parked hypotheses with reactivation conditions;
- smallest discriminating next observations or experiments;
- limitations and unresolved questions.

Stop after the advisory report. The Explorer cannot contact External Pro,
change CDC state, authorize compute, dispatch implementation or advance the
formal workflow. The user may later choose to submit a result separately.
