---
name: hmasd-independent-research-exploration
description: Use in the user-controlled HMASD Independent Research Explorer task for bounded evidence review, an adaptive source-absorption and algorithm-inspiration campaign, or advisory validation of one mature candidate, with every output confined to local_research outside pro_reviews.
---

# HMASD Independent Research Exploration

## Purpose

Explore HMASD-relevant ideas without entering the formal project workflow.
Preserve the initial mission and several-live-directions discipline, but do not
make a canonical scientific decision.

The Explorer is a persistent `gpt-5.6-sol/ultra` task and the only writer. It
uses read-only Sol-high Scouts to absorb source results, read-only Sol-max
Research Innovators to adapt and combine them, Sol-max Research Principles
Analysts for constructive RL analysis, and Sol-max Critics for later targeted
adversarial checks. All durable outputs remain
under `local_research` except the independently owned `pro_reviews` subtree.

## Start safely

1. Confirm the active task session matches the registered Explorer session.
2. Read the Explorer role and only
   `docs/project/ALGORITHM_PRINCIPLES.md sections 1 and 3`.
3. Freeze exactly one mode, one campaign direction or evidence question, mission
   connection, authorized source boundary, exclusions and completion meaning.
   Ask the user only when a material boundary is missing.
4. For MyLib, read [references/mylib.md](references/mylib.md) and run the
   registered probe. Never write to MyLib.
5. Read [references/parallel-research-workflow.md](references/parallel-research-workflow.md)
   before dispatching children.
6. For algorithm inspiration, read
   [references/open-algorithm-inspiration.md](references/open-algorithm-inspiration.md).
   For candidate validation only, also read
   [references/research-methodology.md](references/research-methodology.md).

Do not read `CURRENT_WORK.md`, active runtime/review state, implementation or
scientific ledgers. Do not use Git or create project changes.
Write advisory files only with `apply_patch` under `local_research`, excluding
`local_research/pro_reviews`; the research session's shell is read-only.

## Choose exactly one research mode

Use **evidence review** to determine what existing sources establish. Create an
exact source work roster, run every assignment, optionally use targeted
source-fidelity criticism, produce one report and stop. This mode does not
create an autonomous algorithm portfolio.

Use **algorithm inspiration campaign** for a broad direction such as variable
skill period or variable agent population. Recall and lock a versioned relevant
corpus first. Assignment count is derived from that corpus, not a fixed range;
run independent assignments at available native capacity and queue the rest.
After every `SOURCE_RESULT_PACKET` crosses the absorption barrier, the Explorer
creates one `SOURCE_ABSORPTION_BRIEF`. Innovation, constructive principles
analysis, adversarial review and portfolio update then proceed in that order.

The campaign repeats automatically while a recorded new mechanism, transfer,
combination, important correction, subdirection split or cross-direction
inspiration opportunity remains. Each cycle freezes an exact work roster before
dispatch. Keep all useful parent and child directions. Stop only at recorded
convergence, a resource boundary, an external-source expansion or work that
requires code, compute or formal adoption.

Use **candidate validation** only for a mature candidate with a precise defect,
mechanism, algorithm delta, strongest simple explanation and separating
prediction. Load the strict methodology reference and produce an advisory
validation design without executing evidence.

Never substitute an Innovator for source absorption, a Principles Analyst for
literature fidelity, or a Critic for constructive RL reasoning. A broad request
starts in algorithm inspiration rather than candidate validation.

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

Every Scout returns one `SOURCE_RESULT_PACKET` with exact assignment and source
identities, evidence locators, author claims, experimental support, mechanism
primitives, learning signal, information and temporal structure,
action/policy-space effect, failure boundaries, transferable results,
non-transferable assumptions, possible HMASD connections and cross-paper
questions. Source fact and Scout inference remain distinct.

Every campaign Innovator returns one `ALGORITHM_INSPIRATION_PACKET` with exact
source-result and parent identities, opportunity kind, target problem,
transferable primitive, transformation, mechanism, learning driver, effective
state/observation/action change, information and credit flow, temporal and
multi-agent assumptions, predicted effect, simplest alternative,
cross-direction connections, `delete|retain|add` ledger, failure boundaries,
validation needs and unresolved items.

Every selected Principles Analyst returns one `RL_PRINCIPLE_ANALYSIS_PACKET`
with candidate and source identities, RL problem formulation, effective action
space, exploration and exploitation drivers, information and credit flow,
temporal process, multi-agent strategic effect, statistical interpretation,
simple explanation, constructive refinements, cross-candidate connections,
validation requirements and unresolved principle questions. A VAE or
information-bottleneck proposal also binds its random variables, objective,
preserved/removed information, behavioral role, leakage and posterior-collapse
risks.

Every campaign Critic assignment names the terminal principles packet it
follows and returns one `CRITIC_ASSESSMENT_PACKET` with alternative
explanations, empirical risks, actionable corrections, smallest discriminator
and disposition. Inspiration criticism does not require a formal proof or
counterexample. Candidate validation may use the stronger methodology packet.

Reject a packet that substitutes index excerpts for content evidence, omits an
assigned identity, reads legacy Markdown, expands its source or opportunity,
claims project authority or collapses several retained directions into an
unassigned unique winner.

## Gate the campaign mechanically

Keep a version-3 JSON record under `local_research/` and check it with:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe `
  .agents/skills/hmasd-independent-research-exploration/scripts/research_portfolio_gate.py `
  check --record "./local_research/<record>.json" --phase <intake|absorption|cycle|convergence>
```

The checker validates mode, authorized source boundary, corpus manifest and
deltas, exact work rosters, source ownership, terminal packet coverage, ordered
absorption/innovation/principles/adversarial/portfolio barriers, parent and
subdirection identities, opportunity bindings, resource-bound reporting and
recorded convergence predicates. It emits JSON to stdout and never writes.

An opportunity uses exactly one kind:
`new_mechanism|transfer|combination|important_correction|subdirection_split|cross_direction_inspiration`.
It binds sources or parents, a material delta, expected portfolio effect,
required role and completion condition. A combination has at least two parents;
a transfer has source and target contexts; a split has a parent plus a distinct
assumption, learning driver or prediction. All independent planned assignments
may use available native capacity; the gate imposes no first-wave task count.

The checker validates the convergence record but never decides relevance,
novelty, correctness, importance or actual scientific convergence. Resource
exhaustion is `PARTIAL_CAMPAIGN_RESOURCE_BOUND`, not `CONVERGED`.

## Synthesize without promotion

After every phase barrier, the Explorer reconciles conflicts and updates one
multi-direction portfolio. Preserve source-result identities, parent and child
directions, cross-pollination edges, constructive analyses, adversarial
corrections and reactivation conditions. Generate a
`NEXT_CYCLE_OPPORTUNITY_MAP` before claiming convergence.

The final advisory report includes the campaign direction, corpus coverage,
source-result matrix, absorption brief, several retained or parked directions,
mechanism/transfer/combination/split graph, principle analyses, adversarial
findings, validation-ready candidates, residual gaps, resource disposition and
convergence basis. The Explorer cannot contact External Pro, change CDC state,
authorize compute, dispatch implementation or advance the formal workflow.
