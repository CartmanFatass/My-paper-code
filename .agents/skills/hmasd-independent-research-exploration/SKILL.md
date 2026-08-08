---
name: hmasd-independent-research-exploration
description: Use in the user-controlled HMASD Independent Research Explorer task for bounded evidence review, an adaptive source-absorption and algorithm-inspiration campaign, or advisory validation of one mature candidate, with research outputs confined to local_research and explicit handoffs confined to the shared ignored temporary outbound path.
---

# HMASD Independent Research Exploration

## Purpose

Explore HMASD-relevant ideas without entering the formal project workflow.
Preserve the initial mission and several-live-directions discipline, but do not
make a canonical scientific decision.

The active Explorer is the `gpt-5.6-sol/ultra` research role in the current
direct user task and the only writer; no archived task ID or route registry is
required. It
uses read-only Sol-high Scouts to absorb source results, read-only Sol-max
Research Innovators to adapt and combine them, Sol-max Research Principles
Analysts for constructive RL analysis, and Sol-max Critics for later targeted
  adversarial checks. The persistent Explorer owns each review item and sends
  one ordered file-backed set of frozen question paths to the dedicated Agentify task.

Restart continuity is owned by the Explorer and specified once in
`references/parallel-research-workflow.md`; this Skill keeps the mode loop and
scientific packet requirements.

## Dispatch registered research children

Every Explorer research-child dispatch is explicit: call the registered agent
type with `fork_turns="none"` and a self-contained natural-language
assignment. The registered child types are `hmasd-research-scout`,
`hmasd-research-innovator`, `hmasd-research-principles-analyst` and
`hmasd-research-critic`.

Compile all task meaning, authority and scientific context into the assignment
and its named frozen packets. Parent conversation history is background only;
it must not supply hidden task meaning, authority, peer results or favored
answers. Assignment guidance should cover the research purpose, exact
scientific question, source and prerequisite-packet bindings, protected
assumptions and independence, exclusions, allowed local judgment and
completion meaning. This is writing guidance, not a mandatory schema, file,
validator or admission gate.

## Start safely

1. Confirm the active task has the Explorer role, registered model and current
   direct user assignment.
2. Read the Explorer role and only
   `docs/project/ALGORITHM_PRINCIPLES.md sections 1 and 3`.
3. Freeze exactly one mode, one campaign direction or evidence question, mission
   connection, authorized source boundary, exclusions and completion meaning.
   Ask the user only when a material boundary is missing.
4. For MyLib, read [references/mylib.md](references/mylib.md) and run the
   registered probe. Never write to MyLib.
5. Read [references/parallel-research-workflow.md](references/parallel-research-workflow.md)
   before dispatching children.
6. Load its Explorer-owned continuity entry. If it is absent, perform the one
   bounded owned-path scan and create it exactly as that reference specifies.
7. For algorithm inspiration, read
   [references/open-algorithm-inspiration.md](references/open-algorithm-inspiration.md).
   For a conclusion-bearing candidate validation, also read
   [references/research-methodology.md](references/research-methodology.md).

The proportional A/B/C evidence definitions live in
`docs/project/ALGORITHM_PRINCIPLES.md`; this Skill points to that source rather
than duplicating its full scientific discipline. A is read-only engineering or
runtime reconnaissance, B is a small exploratory toy algorithm experiment, and
C is conclusion-bearing, promotion/retirement or otherwise expensive work.
Treat A and B as normal research progress when their stated question and
resource boundary are clear. The strict methodology reference is C-only; it is
not a prerequisite for ordinary B iteration.

Do not preload `CURRENT_WORK.md`, active runtime/review state, implementation or
scientific ledgers during ordinary research. The project-validation phase may
inspect project material read-only as needed for reconnaissance and semantic
acceptance. During research execution, do not use Git or create project
changes. Write advisory research files with `apply_patch` under
`local_research`. An explicit mature-candidate handoff is a disposable copy
under `temp/handoffs/explorer_to_code_manager/`; it is ignored and requires no
Git operation.

Workflow design is not an Explorer mode. Report one exact requirement or defect
to the current Workflow Design Manager task through Codex-native
`send_message_to_thread`, omitting model and thinking overrides; never load the
collaborative/audit Workflow Skills, edit or accept control-plane files, or
dispatch a workflow implementer. Continue unrelated research when the defect is
dependency-local. A WDM reload receipt has `research_state_effect=none` and
cannot select, pause, resume or terminate research.

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

A direction review or bounded methodology audit inside the active
user-authorized Explorer grant is external advisory input and needs no
per-review user or WDM confirmation. Load
`hmasd-independent-research-pro-review`, then Explorer freezes each exact
assignment, review mode and standalone `RAW_QUESTION`. Write one minimal batch
file containing provider and the ordered paths of all currently eligible frozen
questions, then send its path in one `AGENTIFY_REVIEW_BATCH_REQUEST` to the
dedicated Agentify task. Continue unrelated research while it runs. On
`AGENTIFY_REVIEW_BATCH_RESULT`, archive each raw response under its review item
and reconcile it; an item error affects only that review. Pro/Gemini labels and all local metadata
stay outside the transmitted question. Page, adapter and recovery details
remain inside the Agentify task.

Before sending, check once that the raw question contains no local filesystem
path, task history or unrelated corpus. Use a public remote GitHub URL when the
reviewer needs a source locator. Do not turn this checklist into a script,
fingerprint or approval gate.

Use `PRO_CONSTRUCTIVE_MATHEMATICAL_REVIEW` first. Preserve its exact packet and
explicitly apply, reject or park every correction in a new advisory version.
Only that version may support a separate
`PRO_ADVERSARIAL_SCIENTIFIC_REVIEW` assignment. The adversarial turn challenges
confounds, leakage, capacity, recurrence, co-adaptation, alternative
explanations, controls and residual uncertainty; it is not a closure-only
check. Never compare candidates or turn either review into project adoption.

An `ERROR` affects only that review; Explorer continues unrelated research and
may resend the unchanged question path without modifying research files.

Use **candidate validation** only for a mature candidate with a precise defect,
mechanism, algorithm delta, strongest simple explanation and separating
prediction. Classify the requested work as A, B or C using the stable principles
before deciding what evidence is proportionate. Once a candidate is implementable,
has a differentiating prediction and a matched comparator, and no unresolved
contradiction changes the question, B normally means preparing a direct
implementation/experiment handoff rather than ending at theory-only design.
Load the strict methodology reference only for C or an explicitly requested
conclusion-bearing audit; an A/B design may proceed to its named treatment
without a Pro review on every iteration.

Additional fixture, census, enumerator, certificate or byte-stability work must
name the unresolved result-relevant scientific question it answers. These
engineering/evidence objects are not a default substitute for an algorithm
implementation or experiment. A B experiment must use the real toy
environment, policy, learner, trainer and evaluation runner and produce nonzero
transitions, updates or evaluations; tests and truth tables alone do not qualify.

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
convergence basis. The Explorer contacts External Pro only through the dedicated
Agentify task procedure above; it cannot change CDC state, authorize compute,
dispatch implementation or advance the formal workflow.

## Project-validation handoff (advisory only)

When one or more mature candidates are ready for project intake, load
`hmasd-explorer-project-validation`. Write self-contained semantic briefs under
`temp/handoffs/explorer_to_code_manager/`; an optional manifest lists
their public paths in the intended order. Each brief carries one candidate, but
its format is not an admission gate and its order is not queue state or ranking.
The brief names the selected treatment defined by the stable validation workflow
and gives one clear instruction naming implementation, instance binding,
experiment, pause, abandon or exact review as applicable. That instruction
authorizes CPM to execute the named treatment without separate permission fields.
If an object is missing, the brief states what is known and Explorer answers any
scientific choice CPM cannot determine; CPM owns constructing or binding the
engineering object. Missing objects are collaboration topics, not task states.

CPM reads the shared temporary brief, applies engineering judgment and may perform
bounded safe read-only reconnaissance. It returns an understandable summary
and exact evidence through its reverse temporary directory. After CPM technical
acceptance and push, ordinary B may continue as advisory iteration without Pro.
Only for the named C/direction-change/material-ambiguity/final-alignment/
conclusion trigger does Explorer freeze one `CODE_SCIENCE_ALIGNMENT_AUDIT`
using the returned exact commit and public GitHub locators, submit it through
the dedicated Agentify task, and archive and intake the answer. External Pro
owns final scientific-semantic acceptance when invoked; Explorer does not
substitute its own judgment.
Explorer does not ask
CPM to read `local_research/` and does not reinterpret prior mechanical BLOCKED
receipts as candidate evidence. The explicit instruction authorizes CPM to
execute the named treatment; External Pro remains the final scientific-semantic
acceptance owner.
