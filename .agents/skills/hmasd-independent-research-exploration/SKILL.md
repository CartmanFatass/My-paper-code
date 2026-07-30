---
name: hmasd-independent-research-exploration
description: Use in the user-controlled HMASD Independent Research Explorer task for either bounded literature evidence review with Sol-high Scouts or genuine scientific-innovation exploration with Sol-max Research Innovators, followed by targeted read-only Critics, while keeping every output advisory and confined to local_research.
---

# HMASD Independent Research Exploration

## Purpose

Explore HMASD-relevant ideas without entering the formal project workflow.
Preserve the initial mission and the several-live-conjectures discipline in
`docs/project/ALGORITHM_PRINCIPLES.md sections 1 and 3`, but do not make a
canonical scientific decision.

The Explorer is a persistent `gpt-5.6-sol/ultra` task and the only writer. It
uses read-only Sol-high Scouts to establish what existing sources say,
read-only Sol-max Research Innovators to develop genuinely new mechanisms, and
Sol-max Critics for high-value adversarial checks. All durable outputs remain
under `local_research`.

## Start safely

1. Confirm the active task session matches the registered Explorer session.
2. Read the Explorer role and only sections 1 and 3 of the algorithm principles.
3. Freeze exactly one mode, the question, mission connection, named sources,
   exclusions, completion condition and target-specific semantic traps. Ask the
   user only when one of those fields is materially missing.
4. For MyLib, read [references/mylib.md](references/mylib.md) and run the
   registered probe. Never write to MyLib.
5. Read [references/parallel-research-workflow.md](references/parallel-research-workflow.md)
   before dispatching children.

Do not read `CURRENT_WORK.md`, active runtime/review state, implementation or
scientific ledgers. Do not use Git or create project changes.
Write advisory files only with `apply_patch` under `local_research`; the
research session's shell is read-only.

## Choose exactly one research mode

Use **evidence review** to determine what existing sources establish. Quick
review recalls at most 12 candidates and reads structured content for at most 6
papers. Deep review freezes a larger bounded candidate set named by the intake.
Both variants launch 1-4 Sol-high Scouts with disjoint evidence axes or paper
sets, cross the merge barrier, optionally launch up to 2 Sol-max Critics for
central or conflicting claims, produce one evidence report and stop. This mode
does not create an approach-family portfolio or claim scientific innovation.

Use **scientific innovation** to develop new mechanisms, derivations,
constructions, counterexamples or falsifiable hypotheses from a frozen evidence
baseline. Create the approach-family registry in the parallel-workflow
reference, then launch 1-4 Sol-max Research Innovators on materially different
mechanisms or formulations. Shared baseline sources are allowed. Withhold the
favored family unless an assignment explicitly challenges it. Wait for all
assignments to end with a terminal packet or structured terminal operational
failure before cross-pollination or up to 2 Sol-max Critic assignments. Only
returned packets supply research evidence. Default to synthesis and stop after
the initial wave.

Never substitute an Innovator for routine library recall, or a Scout for
mechanism-level scientific innovation. A combined user request runs the two
modes as separately bounded phases and uses the evidence-review report as the
frozen innovation baseline.

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

## Require mode-specific packets

Each evidence-review Scout returns one `SCOUT_EVIDENCE_PACKET` with:

- assignment ID and non-overlapping research axis;
- evidence rows restricted to the assignment's exact source-identity,
  JSON/PDF type and absolute-path bindings;
- search terms, candidates, exclusions and coverage limit;
- evidence rows containing claim, claim kind, paper ID, title, absolute
  JSON/PDF path, locator and confidence;
- supporting, conflicting and boundary evidence;
- testable hypotheses and unresolved facts.

Each scientific-innovation child returns one `RESEARCH_DIRECTION_PACKET` with:

- assignment, approach-family and exact-claim identities;
- core mechanism, assumptions and a derivation or construction;
- mission link and novelty delta relative to the frozen evidence baseline;
- evidence dependencies and their verification state;
- at least one concrete lemma, construction, equation, counterexample or
  falsifiable prediction;
- strongest internal counterexample, alternate explanation and failure bounds;
- missing lemma or interface and one smallest discriminating observation or
  experiment, without executing it.

An elegant reduction with an equally hard missing lemma is `blocked`, not
nearly complete. Contradiction, terminology weakening and an exact unresolved
gap are valid results. Never assume an affirmative result exists or suppress a
counterexample.

Each selected Critic returns one `CRITIC_ASSESSMENT_PACKET` with:

- terminal status;
- exact claim and packet identities assessed;
- evidence identity and fidelity audit;
- strongest counterexample and alternate explanation;
- supported, weakened, contradicted and unresolved dispositions;
- smallest discriminating observation or experiment, without executing it.

The Critic assignment also contains a target-specific adversarial checklist.
In evidence review it tests source semantics and fidelity. In scientific
innovation it additionally tests hidden equivalence to a known family,
circularity, a missing lemma of unchanged difficulty, failure boundaries and
whether the proposed discriminator separates the alternatives.

Reject a packet that substitutes index excerpts for content evidence, omits
source identity, reads legacy Markdown, exceeds its axis or claims project
authority. A metadata-derived claim must also name its field provenance,
evidence locator, extraction method, confidence and verification state; absent
provenance reduces the field to recall-only guidance.

## Gate the scientific portfolio mechanically

For scientific innovation, keep a JSON portfolio record under
`local_research/` and check it with:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-independent-research-exploration/scripts/research_portfolio_gate.py `
  check --record "./local_research/<record>.json" --phase <intake|merge|additional-wave|synthesis>
```

The checker validates identities, required packet fields, independence
shielding, merge completion, critic-correction propagation and additional-wave
admission structure. It emits JSON to stdout and never writes. It does not
decide whether a mechanism is scientifically new or valid.

After the initial scientific-innovation wave, an additional wave is eligible
only when all prior assignments are terminal by packet or structured
operational-failure record, a disposition-changing target and new
mechanism/invariant/construction are named, budgets and a stop condition are
recorded, and the user separately confirms that exact wave. The admission
records prior and next wave IDs, exact terminal assignment and packet sets, and
a deterministic fingerprint of the frozen target, novelty, budgets and stop
condition; the confirmation is bound to that fingerprint. This is an internal
consistency check, not a substitute for the actual user confirmation. A
blocked family cannot reopen for a rephrased gap, generic search or new citation
alone. Mechanical eligibility never dispatches a child. No autonomous loop,
minimum duration or fixed large-agent target exists.

## Synthesize without promotion

After all packets cross the merge barrier, reconcile conflicts and write one
local report. In evidence review, deduplicate by paper ID and claim. In
scientific innovation, preserve every approach-family disposition and propagate
each exact Critic correction into the corresponding claim. Include:

- question and mission connection;
- mode, retrieval terms, coverage and exclusions;
- evidence matrix and fidelity level;
- supporting and conflicting findings;
- Explorer inferences separated from paper claims;
- several live or parked hypotheses with reactivation conditions;
- blocked and contradicted families with exact reopen conditions;
- smallest discriminating next observations or experiments;
- limitations and unresolved questions.

Stop after the advisory report. The Explorer cannot contact External Pro,
change CDC state, authorize compute, dispatch implementation or advance the
formal workflow. The user may later choose to submit a result separately.
