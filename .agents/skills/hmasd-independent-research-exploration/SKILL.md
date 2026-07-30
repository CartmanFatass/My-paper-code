---
name: hmasd-independent-research-exploration
description: Use in the user-controlled HMASD Independent Research Explorer task for bounded literature evidence review or a user-authorized adaptive scientific-innovation campaign with Sol-high Scouts, Sol-max Innovators and targeted Sol-max Critics, while keeping every output advisory and confined to local_research outside pro_reviews.
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
under `local_research` except the independently owned `pro_reviews` subtree.

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
6. For scientific innovation, read
   [references/research-methodology.md](references/research-methodology.md)
   completely before creating the campaign record or assignments.

Do not read `CURRENT_WORK.md`, active runtime/review state, implementation or
scientific ledgers. Do not use Git or create project changes.
Write advisory files only with `apply_patch` under `local_research`, excluding
`local_research/pro_reviews`; the research session's shell is read-only.

## Choose exactly one research mode

Use **evidence review** to determine what existing sources establish. Quick
review recalls at most 12 candidates and reads structured content for at most 6
papers. Deep review freezes a larger bounded candidate set named by the intake.
Both variants launch 1-4 Sol-high Scouts with disjoint evidence axes or paper
sets, cross the merge barrier, optionally launch up to 2 Sol-max Critics for
central or conflicting claims, produce one evidence report and stop. This mode
does not create an approach-family portfolio or claim scientific innovation.

Use **scientific innovation** to run one user-authorized adaptive campaign.
Freeze its question, mission link, exclusions, scope, common scientific
objects, exact source identities and boundary, evidence baseline, maximum
cohort count, total Scout/Innovator/Critic budgets, completion condition and
stop conditions in one authorization fingerprint. Create the versioned conjecture-family registry in the
parallel-workflow reference. The first 1-4 Sol-max Innovators work independently
on materially different mechanisms or formulations. After the merge, later
cohorts may use a versioned collaboration brief and assignments with purpose
`develop`, `refine`, `combine` or `challenge`. Scouts may fill exact evidence
gaps; up to two Critics challenge high-value claims after each merge. Continue
without another user prompt only while the frozen campaign has budget and the
next cohort passes the mechanical gate. Returned packets alone supply research
evidence.

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

The probe performs mechanical integrity, catalog, JSON and PDF checks. In this
Explorer route it is invoked without `--output` and returns only stdout; the
shell never writes a receipt:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-independent-research-exploration/scripts/mylib_research_probe.py `
  --mylib-root "C:/Projects/Inst-sci/papers/MyLib" `
  --local-research-root "./local_research" status
```

Use `search`, `locate`, `validate-pdf` and `smoke` subcommands as routed in the
reference. `--output` is forbidden in this route; durable advisory output is
written only by the Explorer through `apply_patch`.

## Require mode-specific packets

Each Scout returns one `SCOUT_EVIDENCE_PACKET` with:

- assignment ID and non-overlapping research axis;
- evidence rows restricted to the assignment's exact source-identity,
  JSON/PDF type and absolute-path bindings;
- search terms, candidates, exclusions and coverage limit;
- evidence rows containing claim, claim kind, paper ID, title, absolute
  JSON/PDF path, locator and confidence;
- supporting, conflicting and boundary evidence;
- testable hypotheses and unresolved facts;
- source-grounded mechanism primitives, transfer boundaries and cross-source
  questions when the assignment belongs to an innovation campaign.

Each scientific-innovation child returns one `RESEARCH_DIRECTION_PACKET` with:

- assignment, campaign, cohort, approach-family, conjecture/version, parent and
  exact-claim identities;
- assignment purpose and exact input collaboration-brief identity when later
  than the independent first cohort;
- scientific game and information objects, membership process, identity/state
  ownership, temporal clocks when relevant and strategic policy dependence;
- core mechanism, mathematical defect, assumptions and a derivation or
  construction;
- mission link and novelty delta relative to the frozen evidence baseline;
- evidence dependencies and their verification state;
- at least one concrete lemma, construction, equation, counterexample or
  falsifiable prediction;
- intervention/comparator regimes, primary estimand, sampling hierarchy,
  identification assumptions and uncertainty requirements;
- strongest simple null, equivalence analysis, negative controls, a
  `delete|retain|add` replacement ledger and unique discriminating observation;
- strongest internal counterexample, alternate explanation, failure/retirement
  bounds, missing lemma/interface, proposed conjecture patch and unresolved
  items, without executing evidence.

An elegant reduction with an equally hard missing lemma is `blocked`, not
nearly complete. Contradiction, terminology weakening and an exact unresolved
gap are valid results. Never assume an affirmative result exists or suppress a
counterexample.

Each selected Critic returns one `CRITIC_ASSESSMENT_PACKET` with:

- its exact expected Critic-assignment identity and terminal status;
- campaign/cohort, exact target family, conjecture/version, claim and source
  packet identities assessed;
- evidence identity and fidelity audit;
- strongest counterexample and alternate explanation;
- one supported, weakened, contradicted or unresolved disposition;
- exact corrections with immutable correction ID, existing target record/field, kind,
  exact text, basis and disposition impact;
- smallest discriminating observation or experiment, without executing it.

Every selected Critic is first recorded as an expected assignment with exact
source packets and a target-specific adversarial checklist. Its packet or
terminal operational failure must close the Critic merge barrier, and the
assignment consumes the frozen Critic budget in either case.
Record a selected Critic that fails as `operational_failure`, or
`partial_operational_failure` when another selected Critic returns a packet;
`not_selected` means no Critic assignment existed.

The Critic assignment also contains a target-specific adversarial checklist.
In evidence review it tests source semantics and fidelity. In scientific
innovation it applies the methodology principles: object validity, membership
nonstationarity, identity, clocks, strategic dependence, estimand, sampling,
identification, strongest simple null, hidden equivalence, module admission,
counterexamples, discriminator validity, correction propagation and
complexity.

Reject a packet that substitutes index excerpts for content evidence, omits
source identity, reads legacy Markdown, exceeds its axis or claims project
authority. A metadata-derived claim must also name its field provenance,
evidence locator, extraction method, confidence and verification state; absent
provenance reduces the field to recall-only guidance.

## Gate the scientific portfolio mechanically

For scientific innovation, keep a version-2 JSON campaign record under
`local_research/` and check it with:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-independent-research-exploration/scripts/research_portfolio_gate.py `
  check --record "./local_research/<record>.json" --phase <intake|merge|next-cohort|synthesis>
```

The checker validates the complete frozen campaign authorization fingerprint,
including an explicit allowed-source set, total-budget accounting, required
nested methodology fields, conjecture
lineage, first-cohort independence, expected Critic assignments, later
collaboration-brief and originating-admission binding, merge completion, exact
Critic-correction outcomes, planned-assignment coherence and next-cohort
admission, including canonical prospective conjecture versions and exact parent
coverage, with each refinement bound to its own immediate predecessor. It emits JSON to stdout
and never writes.
For a completed cohort, the same check uses only conjectures visible before that
cohort, so a post-hoc current or future registry entry cannot repair invalid
lineage or become a parent retroactively.
It does not decide whether a mechanism is new, correct, causal, important or
ready for compute.

After a cohort merge, another cohort is eligible only when all prior expected
assignments are terminal, the campaign has sufficient remaining role budget, a
disposition-changing target and genuine mechanism/invariant/construction/
correction/combination/refinement are named, and an exact stop condition is
recorded. A deterministic fingerprint binds the admission to the original
campaign authorization, terminal identity sets, prior disposition snapshot and
full planned assignment semantics. No per-cohort user
confirmation is required inside that frozen campaign. A blocked family cannot
reopen for a rephrased gap, generic search or new citation alone. Mechanical
eligibility never dispatches a child; maximum cohorts and total budgets prevent
an unbounded loop.

## Synthesize without promotion

After all packets cross the final merge barrier, reconcile conflicts and write
one local report. In evidence review, deduplicate by paper ID and claim. In
scientific innovation, preserve every versioned conjecture-family disposition,
every cohort's disposition snapshot, cross-pollination edge and exact Critic
correction. Mark each correction `applied`, `unresolved` or `conflicting`;
`applied` is reserved for a versioned conjecture successor whose target field
equals the correction text exactly and whose parents include the corrected
conjecture. Include:

- question and mission connection;
- mode, retrieval terms, coverage and exclusions;
- evidence matrix and fidelity level;
- supporting and conflicting findings;
- Explorer inferences separated from paper claims;
- several live or parked hypotheses with reactivation conditions;
- blocked and contradicted families with exact reopen conditions;
- conjecture version map, parent-child lineage, collaboration briefs and
  combined-family records;
- smallest discriminating next observations or experiments;
- limitations and unresolved questions.

Stop after the advisory report. The Explorer cannot contact External Pro,
change CDC state, authorize compute, dispatch implementation or advance the
formal workflow. The user may later choose to submit a result separately.
