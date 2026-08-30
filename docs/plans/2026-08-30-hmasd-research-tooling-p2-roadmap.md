# HMASD Research Tooling P2 Roadmap

**Status:** conditional future roadmap; **not current implementation authorization**  
**Date:** 2026-08-30  
**Current authorized scope:** [`P0/P1 implementation plan`](2026-08-30-hmasd-research-workflow-p0-p1-implementation.md) only

> Nothing in this document authorizes installing a package, fetching a model or
> dataset, enabling network access, supplying a secret, running a tool, changing
> `.omp`, changing a protocol or schema, adding an agent, or executing generated
> code. Every P2 capability is optional. Promotion requires a new, explicit
> decision with its own owned paths, dependency locks, effects, resource bounds,
> acceptance evidence, and rollback plan.

## 1. Boundary and invariants

P2 begins only after the applicable P0/P1 contracts are implemented and their
acceptance evidence is durable. P2 does not revise P0/P1 and cannot be used to
hold it open. A capability that does not pass every entry gate remains external
reference material.

The following boundaries survive every possible P2 promotion:

- Root performs Portfolio. Portfolio retains allocation and lifecycle authority.
- EM retains scientific synthesis, evidence classification, discriminator
  selection, claim ceiling, and scientific disposition.
- CM retains implementation and technical-acceptance authority.
- Scouts retrieve and map evidence; Principles Analysts reason about scientific
  assumptions and implications; Implementers change code; Verifiers observe an
  exact technical fact; exactly one Experiment Operator owns one exact
  result-bearing command.
- A proof checker, solver, retrieval score, benchmark, profiler, validator,
  figure, checkpoint, or successful command is inspectable evidence, never
  scientific or Portfolio authority.
- Existing assignment worktrees, CAS/runtime registries, BrowserTransport, and
  common v1 remain. The active allocator may consume terminal facts immediately;
  P2 does not introduce an all-terminal join.
- Route count follows distinct answer-changing information gaps. No fixed leaf
  quota, agent count, round count, vote, quorum, Elo score, or scheduler is
  introduced.
- Scientific, numerical, RNG, checkpoint, bit-identity, and external-effect
  semantics may not change silently. Approximate numerical agreement is not
  byte identity, solver `UNSAT` is only relative to its encoding and theories,
  and rerunning the same code/data is not independent scientific replication.

## 2. P2 entry gates

A proposed pilot is eligible for a later authorization decision only when all
of the following are answered with inspectable evidence. An unanswered gate is
`NOT ELIGIBLE`, not permission to proceed.

| Gate | Evidence required before authorization | Mechanical refusal condition |
|---|---|---|
| Decision need | One current EM- or CM-owned decision that the capability could materially change; baseline method and measurable deficiency; falsifiable adoption trigger | “Useful,” “industry standard,” generic quality improvement, or agent enthusiasm without a current decision gap |
| Fit and non-duplication | Comparison against current Scout, Principles Analyst, Implementer, Verifier, and Operator methods; smallest adaptation that closes the gap | Existing role plus existing tools can produce the same artifact at acceptable cost and reliability |
| Exact scope | Exact version/commit, interfaces, owned files, inputs, outputs, effects, stop rule, and non-goals for one isolated pilot | Moving branch, floating package range, broad manager autoload, repository-wide integration, or unspecified effects |
| Dependency and version | Reproducible environment lock; Python/Lean/CUDA/native ABI matrix as applicable; transitive dependency inventory; model/data/skill revisions and hashes | Conflict with project locks, implicit project upgrade, incompatible checkpoint format, or no reproducible lock |
| License and provenance | License text for code, models, data, prompts, bundled assets, and transitive dependencies; source revision and attribution obligations; written resolution of custom or missing licenses | Custom/restrictive/unknown rights are used without explicit legal decision; provenance cannot bind an artifact to a source revision |
| Security and execution | Threat model for untrusted documents, parsers, generated content, subprocesses, native extensions, solver inputs, profiles, and artifact rendering; isolation and output validation | Direct LLM-written code execution, unsandboxed native/plugin execution, privileged access not strictly required, or artifact content can escape its boundary |
| Network and secrets | Exact hosts/endpoints, transmitted fields, retention terms, rate limits, offline alternative, egress allowlist, secret source and redaction proof | Ambient credentials, secrets in prompts/logs/artifacts, unrestricted web access, or unclear provider commitment/idempotency |
| Resource | Worst-case and observed pilot CPU, RAM, GPU/VRAM, disk, wall time, process count, and artifact size; cancellation and cleanup path | Unsafe memory plan, unbounded corpus/index/model download, unbounded solver/search, or no enforced timeout/size cap |
| Semantics | Frozen assumptions, estimand/oracle/tolerances, RNG seeds and state, solver logic/options, checkpoint compatibility, byte/hash requirements, and expected failure branches | Tool default can silently alter scientific, numerical, RNG, checkpoint, or bit-identity meaning |
| Artifact contract | Canonical, inspectable outputs with inputs/config/version/hash, stdout/stderr/exit state where relevant, and clear ownership for interpretation | Only conversational prose, a dashboard view, mutable cache, unbound score, or provider response without source locators |
| Removal | Exact files/dependencies/caches/artifacts/credentials to remove; proof that P0/P1 remains valid after removal | Pilot writes authoritative state or requires a compatibility shim to restore the baseline |

## 3. When a dedicated capability leaf is justified

Reuse a current role by default. A dedicated capability leaf is justified only
when **all** of these conditions hold:

1. a repeated, separable information gap requires a specialist method that is
   materially different from the current role’s ordinary method;
2. the method has a stable machine-checkable input/output contract and produces
   a distinctive inspectable artifact;
3. isolation, dependencies, or permissions must be narrower than the parent
   role’s normal boundary;
4. at least two accepted pilot cases show improved decision evidence against the
   frozen baseline without changing authority or protected semantics; and
5. permanent ownership is clearer with the leaf than with a bounded task issued
   to the existing role.

A leaf is **not** justified by package complexity, branding, convenience,
parallelism, prompt length, or a desire to keep a tool warm. It receives no
allocation, scientific-disposition, technical-acceptance, lifecycle, or command
ownership beyond the exact delegated task.

Default placement is:

- literature/question/source mechanisms: Research Scout, with EM interpreting;
- theorem assumptions, formal statement, and implication: Research Principles
  Analyst or a bounded theorem specialist under EM;
- dependency integration and artifact production: Implementer under CM;
- exact build, proof-check, solver, benchmark, or profile observation: Verifier
  when no result-bearing scientific command is involved;
- one frozen result-bearing command: singleton Experiment Operator;
- scientific meaning and claim effect: EM, never a tool leaf;
- technical acceptance: CM, never a tool leaf.

## 4. Candidate capability lanes

Each lane below is a candidate, not an approved package list. “Promote when” is
a falsifiable trigger for requesting a later authorization decision; it is not
self-executing approval.

### 4.1 Lean 4 and mathlib: formal theorem artifacts

**Trigger.** A material direction turns on an exact mathematical proposition;
ordinary derivation leaves a specific proof obligation open; the proposition
and assumptions can be stated without encoding the desired conclusion into the
premises; and a maintained mathlib fragment materially reduces the formalization
cost.

**Placement.** EM freezes the scientific proposition and applicability boundary.
A Research Principles Analyst may map assumptions and lemmas. A dedicated Lean
leaf is justified only after repeated formalization gaps satisfy Section 3.
CM owns any repository integration; a Verifier observes the exact pinned build.

**Dependencies and artifacts.** A pilot must pin `lean-toolchain`, the exact
mathlib revision and Lake dependency lock. Preserve `.lean` theorem/proof files,
all imported modules, the natural-language proposition-to-formal-statement map,
assumption ledger, toolchain manifest, exact build invocation, stdout/stderr,
exit status, and hashes. The artifact status is `PROVED_WITHIN_FORMAL_SCOPE`,
`COUNTEREXAMPLE_OR_TYPE_FAILURE`, or `OPEN_WITH_EXACT_OBLIGATION`—never
“scientifically true.”

**Risks and evidence.** The adoption case must measure formalization effort,
checker reproducibility in a clean isolated environment, reviewability of the
statement translation, and value to the EM decision. Risks include a vacuous or
mis-translated theorem, hidden classical/nonconstructive assumptions, dependency
churn, large builds, and confusing type-checking with empirical validity.

**Promote when.** At least two representative, nontrivial obligations reproduce
from the lock and an independent statement review finds the formal claim matches
the frozen scientific claim. Remove by deleting the isolated toolchain/cache and
pilot-owned proof artifacts; the unresolved obligation reverts to EM’s prior
claim ceiling.

Primary sources: [Lean 4](https://github.com/leanprover/lean4),
[mathlib4](https://github.com/leanprover-community/mathlib4).

### 4.2 cvc5: conditional solver diversity

**Trigger.** A frozen SMT-LIB2 claim already has a primary solver result, and an
independent cvc5 encoding/run could change whether EM treats the result as a
credible bounded falsifier or encoding-sensitive observation. Solver diversity
is not adopted merely to duplicate a passing result.

**Placement.** Principles Analyst maps the claim and assumptions; Implementer
produces the bounded encoding under CM; Verifier observes a non-scientific solver
check, while an Experiment Operator owns it if it is the exact result-bearing
command. EM interprets disagreement.

**Dependencies and artifacts.** Pin the cvc5 release/binary hash or build
revision, SMT logic, options, seeds, timeout, resource limits, and platform.
Preserve canonical SMT-LIB2, an encoding-to-claim map, stdout/stderr, exit state,
model/proof/unsat-core artifacts when supported, and a semantic diff from the
primary solver encoding.

**Risks and evidence.** `SAT` provides a model relative to the encoding;
`UNSAT` does not establish a scientific claim. Divergence can arise from theory,
option, timeout, or encoding differences. The pilot must include known-SAT,
known-UNSAT, malformed, unsupported, timeout, and cross-solver-disagreement
cases.

**Promote when.** Solver diversity detects at least one material encoding/tool
assumption missed by the baseline, or demonstrates a repeatable reduction in an
existing decision uncertainty worth its maintenance cost. Otherwise remove the
binary/environment and retain only the pilot record.

Primary source: [cvc5 repository and BSD-3-Clause license](https://github.com/cvc5/cvc5).

### 4.3 PaperQA2: bounded literature evidence packets

**Trigger.** A Research Scout must repeatedly search a bounded scientific corpus
where contextual chunk summaries, reranking, metadata/retraction awareness, or
contradiction retrieval measurably improves primary-source recall or locator
quality over the current source workflow.

**Placement.** Research Scout owns retrieval only. EM owns source appraisal,
claim-to-source synthesis, and insufficiency. No PaperQA agent or answer becomes
a literature-review authority, and no new leaf is needed unless Section 3 is met.

**Dependencies and artifacts.** Pin the exact PaperQA2 commit/release, Python and
embedding/reranker/model versions, prompt revision, document parser, corpus
manifest, chunking settings, index hash, query log, cost/endpoint configuration,
and offline/hosted boundary. Preserve source IDs, DOI/version, page/section or
other locators, verbatim excerpts, contextual summaries, scores, supports/
challenges/limits, search boundary, and an explicit `INSUFFICIENT_EVIDENCE`
state. Every synthesized claim must point back to an original source artifact.

**Risks and evidence.** PaperQA’s move to CalVer and removal of broad
backward-compatibility guarantees requires commit-level freezing. Other risks are
prompt injection in documents, retraction/metadata errors, copyright and local
full-text handling, external embedding leakage, stale indices, model drift, and
plausible unsupported answers. A pilot uses a frozen gold corpus with answerable,
unanswerable, contradictory, retracted, duplicate-version, and adversarial-text
queries; it measures source recall, locator correctness, unsupported-claim rate,
and resource/cost bounds.

**Promote when.** It beats the frozen Scout baseline on the declared evidence
metrics without introducing unsupported claims or violating data/network gates.
Index, cache, documents, models, and credentials must be independently removable.

Primary sources: [PaperQA2 pinned prompts](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/src/paperqa/prompts.py),
[README and compatibility notice](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/README.md),
[Apache-2.0 license](https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/LICENSE).

### 4.4 STORM/Co-STORM: question coverage and unused-evidence checks

**Trigger.** An EM material has a demonstrated coverage failure: answer-changing
questions remain unasked, relevant evidence is repeatedly unused, or materially
different source perspectives are missing after the ordinary Scout route.

**Placement.** Adapt only the perspective-guided question generation, retrieval
transcript, question-to-evidence map, outline, unused-evidence check, and dynamic
concept-map ideas. Research Scout retrieves; Principles Analyst identifies
assumptions/questions; EM decides what matters. Do not import STORM/Co-STORM’s
moderator, simulated experts, turn manager, article generator, or collaboration
model as authority.

**Dependencies and artifacts.** A pilot should prefer prompt/schema adaptation
without installing the system. If later code reuse is proposed, freeze the exact
repository revision, DSPy/provider/retriever versions, endpoint and data policy.
Artifacts are the initial question set, perspective/source basis, retrieval
transcript, question-evidence matrix, unused evidence, newly surfaced question,
concept-map/outline diff, citations, and unanswered gaps—not an auto-written
article.

**Risks and evidence.** Risks include performative question volume, duplicated
perspectives, citation laundering, source contamination, conversational
anchoring, provider costs, and mistaking polished coverage for correctness. The
pilot compares answer-changing coverage and evidence use on frozen materials;
it may not use number of questions, turns, agents, or article length as success.

**Promote when.** The mechanism repeatedly surfaces a previously missed,
material question or source that changes an EM discriminator or claim ceiling,
with acceptable false-positive and resource burden. Removal is deletion of the
pilot prompt/schema/artifacts and any isolated index; EM’s existing gap-driven
route remains sufficient.

Primary sources: [STORM/Co-STORM repository](https://github.com/stanford-oval/storm),
[Co-STORM paper](https://arxiv.org/html/2408.15232).

### 4.5 Expanded statistical analysis and scientific visualization

**Trigger.** A frozen experiment requires a named diagnostic, effect size,
confidence/credible interval, power/sensitivity analysis, or truthful accessible
figure audit that current project code cannot produce reproducibly. Analysis
must be pre-specified enough to avoid post-hoc method shopping.

**Placement.** EM freezes estimand, assumptions, comparisons, multiplicity,
tolerances, and interpretive boundary. CM assigns an Implementer to produce the
analysis/figure artifacts. A Verifier checks exact artifact conformance; the
Operator owns the result-bearing command. EM alone interprets scientific
meaning.

**Dependencies and artifacts.** Freeze the exact applicable subset of NumPy,
SciPy, pandas, statsmodels, and plotting/export dependencies; optional Bayesian
packages require a separate resource/RNG gate. Preserve data/input hashes,
analysis plan, environment lock, assumption diagnostics, warnings, missing-data
policy, effect estimates and intervals, multiplicity treatment, seeds/chains
when applicable, machine-readable tables, plotting source, underlying plotted
data, palette/contrast and metadata audit, export settings, and hashes. Exact
identity claims require bytes/hashes; tolerance-aware checks are separate.

**Risks and evidence.** Risks include an outdated decision tree, violated model
assumptions, p-hacking, hidden data filtering, unstable stochastic inference,
misleading axes/aggregation, inaccessible colors, browser/Kaleido complexity,
and figures that imply unsupported causality. A pilot uses frozen synthetic and
known-result fixtures plus one representative project artifact, and verifies
failure/warning behavior as well as nominal output.

**Promote when.** A named recurring analysis or figure contract gains measurable
correctness/reproducibility/auditability over the baseline and the dependency
cost is justified. Prefer adapting deterministic validators/scripts over loading
a broad skill into a manager. Remove the isolated dependencies and generated
artifacts without changing the frozen experiment or P0/P1 authority.

Primary sources: [K-Dense statistical-analysis skill at a pinned revision](https://github.com/K-Dense-AI/scientific-agent-skills/blob/f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f/skills/statistical-analysis/SKILL.md),
[K-Dense scientific-visualization skill at a pinned revision](https://github.com/K-Dense-AI/scientific-agent-skills/blob/f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f/skills/scientific-visualization/SKILL.md),
[NumPy testing guidance](https://numpy.org/doc/stable/reference/testing.html).

### 4.6 pytest-benchmark: controlled performance evidence

**Trigger.** CM has an observable performance contract or a suspected regression
whose decision cannot be made from existing timing evidence, and the workload
can be isolated from result-bearing scientific interpretation.

**Placement.** Implementer adds the smallest benchmark harness only in a later
authorized change. Verifier observes a focused technical benchmark. If the exact
command produces a scientific result rather than engineering performance
evidence, it belongs to the singleton Operator instead.

**Dependencies and artifacts.** Pin pytest-benchmark and Python/project versions;
freeze hardware/OS/CPU governor/contention context, warmup, calibration, rounds,
input hashes, and comparison baseline. Preserve JSON export, raw samples and
summary statistics, environment manifest, exact command, exit state, and noise
notes.

**Risks and evidence.** Automatic calibration is not immunity to noisy hosts,
JIT/cache effects, benchmark gaming, multiple comparison, or nonrepresentative
microbenchmarks. A pilot must detect a planted representative regression and
remain within a declared false-alarm band over repeated isolated observations.

**Promote when.** It reliably changes a real CM acceptance decision with bounded
noise and maintenance cost. Remove the plugin, pilot benchmark, and output; do
not preserve a brittle threshold without evidence.

Primary source: [pytest-benchmark documentation](https://pytest-benchmark.readthedocs.io/en/latest/).

### 4.7 py-spy: conditional runtime diagnosis

**Trigger.** A Python workload has a material runtime bottleneck that ordinary
instrumentation cannot localize without changing behavior, and sampling can be
performed without elevated access or secret exposure.

**Placement.** CM directs the diagnostic. A Verifier may observe a bounded
profile of a non-result run; the Operator owns profiling if attached to the one
exact result-bearing command. The profile cannot accept a performance change.

**Dependencies and artifacts.** Pin the py-spy binary/release and hash; freeze
sampling rate, duration, target identity, platform, permissions, and output
format. Preserve exact invocation, process identity without secrets, exit state,
SVG/speedscope artifact, version manifest, redaction record, and interpretation
notes linked to code symbols.

**Risks and evidence.** ptrace/process-memory access may require privileges and
can expose sensitive locals, paths, or command lines; sampling can miss short
phases and native/async stacks may be incomplete. Refuse a pilot that needs root
or broad process visibility. Validate on a bounded nonsecret workload with a
known bottleneck and quantify overhead.

**Promote when.** It identifies a material actionable bottleneck missed by the
baseline while meeting privilege, redaction, and overhead bounds. Removal
includes binary, profiles, temporary permissions, and caches.

Primary source: [py-spy repository](https://github.com/benfred/py-spy).

### 4.8 DVC: conditional local provenance only

**Trigger.** Adoptability may be evaluated only when Git/CAS manifests and
current runtime registries cannot represent a concrete recurring data/metric/
parameter lineage need without material manual error. Dataset size alone is not
a trigger.

**Placement.** CM owns technical provenance integration; EM identifies which
scientific identities and parameters must be preserved; Portfolio consumes only
terminal evidence and never DVC state as authority. DVC is not a scheduler,
workflow database, lifecycle registry, or experiment adjudicator.

**Dependencies and artifacts.** A proposal must name the exact DVC release,
Git interaction, cache location, `.dvc`/pipeline/metrics objects, remote backend
if any, credential flow, lock behavior, garbage-collection boundary, and
relationship to existing CAS/runtime registries. Preserve an exportable lineage
manifest independent of the DVC cache.

**Risks and evidence.** DVC experiment refs are local and not pushed by default.
Risks include duplicate sources of truth, opaque cache retention, destructive
cleanup, remote credentials, surprise uploads, Git-ref complexity, and altered
checkpoint/data identity. Pilot offline and local-only unless a separate network
and secret authorization explicitly permits one exact remote.

**Promote when.** A representative lineage reconstruction and removal drill show
a material reduction in provenance error versus the existing manifest/CAS route,
with no authority duplication and no loss after cache removal. Otherwise DVC
remains rejected by default.

Primary source: [DVC experiment management documentation](https://dvc.org/doc/user-guide/experiment-management).

### 4.9 Version-frozen NetworkX, Stable-Baselines3, PyG, and PufferLib skills

**Trigger.** A direction has an authorized implementation task using one of these
libraries, and a version-matched skill demonstrably prevents a current API,
RNG, environment, batching, device, native-extension, or checkpoint error. A
reference guide is not itself a reason to add a skill.

**Placement.** Keep these as CM/Implementer references by default, not manager
autoloads and not scientific leaves. Verifier/Operator roles remain unchanged.
A dedicated leaf would require repeated distinctive artifact contracts under
Section 3, not merely domain terminology.

**Version gates.** Freeze the skill file hash and the exact runtime stack it
describes. The audited skills currently do not match all project snapshots:
NetworkX guidance targets a newer 3.x surface than the observed 3.2.1 lock; SB3
guidance targets 2.8 while the snapshot used 2.6.0; PyG guidance targets 2.7.x
and PyTorch 2.6+ while the snapshot used PyG 2.6.1 and PyTorch 2.7.0+cu118;
PufferLib 3.x and 4.x have incompatible API/native-stack assumptions. A pilot
must either adapt the skill to the existing project lock or use a wholly
isolated environment. It may not silently upgrade the project.

**Artifacts and risks.** Require API/version compatibility matrix, environment
and wrapper contract, seeds/RNG state, graph/data split and batching identity,
device/native ABI/CUDA details, evaluation configuration, serialized checkpoint
and replay-buffer/optimizer state as applicable, resume-vs-restart
classification, output hashes, and failure cases. Risks include graph-label
leakage, nondeterministic GPU operations, vectorized-environment semantics,
unsaved replay buffers, checkpoint incompatibility, native build/plugin supply
chain, and misleading library metrics.

**Promote when.** On representative frozen tasks, the version-matched reference
prevents a plausible material defect and passes clean removal/reproduction with
no semantic drift. Otherwise retain official versioned documentation externally.

Primary sources: [NetworkX](https://networkx.org/),
[Stable-Baselines3](https://stable-baselines3.readthedocs.io/),
[PyTorch Geometric](https://pytorch-geometric.readthedocs.io/),
[PufferLib](https://github.com/PufferAI/PufferLib), and the
[pinned K-Dense skill collection](https://github.com/K-Dense-AI/scientific-agent-skills/tree/f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f).

### 4.10 Agent Laboratory: checkpoint-pattern adaptation

**Trigger.** A multi-stage EM→CM material repeatedly loses an inspectable phase
boundary—literature evidence, frozen experiment plan, terminal observation, or
report input—and a checkpoint artifact would make reentry safer than relying on
conversation history.

**Placement.** Adapt phase-specific prompt/checkpoint patterns into existing
EM/CM artifacts. Do not import the professor/postdoc dialogue, autonomous phase
scheduler, step pressure, scoring, fixed roles, or “good plan” consensus.

**Dependencies and artifacts.** Prefer a schema/prompt adaptation with no Agent
Laboratory runtime dependency. Bind checkpoints to phase, admissible evidence
packet IDs, input hashes, frozen decision, unresolved gaps, exact command/result
witness where applicable, carried fields, expiry rule, and resume preconditions.
Conversation truncation is not a scientific memory policy.

**Risks and evidence.** Risks are stale conclusions reentering as facts,
checkpoint proliferation, implicit state-machine authority, premature consensus,
and resume across incompatible code/data. Pilot a forced interruption and
resume on a bounded material, checking that negative evidence and unresolved
gaps survive while expired prose does not.

**Promote when.** The checkpoint prevents a demonstrated reentry error without
becoming a new registry, scheduler, approval gate, or authority source. Removal
must leave the ordinary durable EM/CM packet sufficient.

Primary sources: [Agent Laboratory pinned implementation](https://github.com/SamuelSchmidgall/AgentLaboratory/blob/d9017d90e329112d2a80b7712f37ee9094d2cd27/agents.py),
[MIT license](https://github.com/SamuelSchmidgall/AgentLaboratory/blob/d9017d90e329112d2a80b7712f37ee9094d2cd27/LICENSE).

### 4.11 AI Scientist: artifact ideas only; runtime and licensed text rejected

**Trigger.** Only an HMASD-owned artifact contract—not source code or prompt
copying—may be considered when a current experiment lacks an inspectable run
directory, frozen idea/input record, plot source, result summary, or review issue
record.

**Placement.** CM defines technical artifact conformance; Implementer produces
artifacts; Verifier checks them; the singleton Operator alone executes an exact
authorized result command; EM interprets results and scientific review. There is
no autonomous scientist role.

**Candidate ideas.** Independently designed HMASD artifacts may include a frozen
experiment description, input/config manifest, per-run code snapshot or commit
identity, machine-readable final-result summary, notes tied to run IDs, plotting
source and data, manuscript template inputs, and structured review issues. They
must use HMASD names and contracts derived from project needs, not copied prompt
text.

**Hard rejection.** AI Scientist v1/v2 use a custom Source Code License with
restrictions, including machine-generation disclosure obligations for scientific
manuscripts. No code, prompt text, template, or derivative is adopted without an
explicit legal decision. Its documented execution of LLM-written code presents
web/process risks. Direct or autonomous LLM code execution, autonomous
experiment scheduling, self-declared novelty, model review as authority, and
unrestricted web access are rejected even if legal review later permits some
source use.

**Promote when.** A clean-room, project-owned artifact shape measurably improves
traceability in an isolated non-autonomous pilot and legal review confirms it
does not copy protected material. This can promote only the specific artifact
contract, never the AI Scientist runtime. Removal deletes the pilot schema and
artifacts without affecting result identity or authority.

Primary sources: [AI Scientist execution warning and artifact layout](https://github.com/SakanaAI/AI-Scientist/blob/1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb/README.md),
[experiment execution source](https://github.com/SakanaAI/AI-Scientist/blob/1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb/ai_scientist/perform_experiments.py),
[custom license](https://github.com/SakanaAI/AI-Scientist/blob/1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb/LICENSE).

## 5. Isolated pilot protocol

A later authorization may approve exactly one pilot lane at a time unless it
explicitly demonstrates that two lanes are inseparable. The pilot record must:

1. freeze one decision need, baseline, hypothesis for improvement, falsifier,
   success/failure thresholds, non-goals, and authority owner;
2. name exact versions, canonical paths, environment, input identities,
   permissions, egress, secrets, resource ceilings, timeout, and stop condition;
3. use a disposable isolated environment and pilot-owned paths; do not alter
   authoritative P0/P1 state, common interfaces, project dependency locks, or
   existing checkpoints;
4. include positive, negative, null/insufficient, malformed/adversarial, timeout,
   resource-exhaustion, and version-mismatch cases appropriate to the lane;
5. compare against the frozen current-role baseline using decision-relevant
   evidence, not output volume, model preference, agreement, or polish;
6. produce a manifest binding input, version/config, exact operation, direct
   observations, exit state, artifacts and hashes, limitations, and the
   responsible EM/CM interpretation;
7. perform a removal drill: revoke temporary secrets/permissions, remove the
   environment/cache/index/model/pilot outputs, and show the baseline path still
   functions conceptually without a shim or new authority source; and
8. end as `PROMOTION_CANDIDATE`, `REJECTED`, or `INCONCLUSIVE_WITH_REENTRY`.
   The pilot may not promote itself.

No retry may be used to improve an unfavorable scientific outcome. A retry is a
new authorized observation only when the prior attempt failed technically and
the exact idempotency/RNG/checkpoint semantics permit it.

## 6. Promotion into a later authorized phase

Promotion requires a new user-approved implementation plan. That plan must name
one bounded capability and include:

- the satisfied Section 2 gate evidence and pilot manifest;
- exact repository files/symbols and owned paths to change, every caller or
  consumer to migrate, and a clean cutover with no alias/shim path;
- exact dependencies, locks, licenses/attributions, model/data rights, SBOM or
  equivalent inventory, and supported version matrix;
- exact network/secret/resource policy and canonical destructive/removal targets;
- protected scientific/numerical/RNG/checkpoint/bit-identity/external-effect
  semantics and explicit failure branches;
- artifact schema and provenance, responsible producing role, and the EM/CM/
  Portfolio authority that consumes but is not replaced by it;
- project-specific focused verification: representative success plus adverse,
  timeout/resource, incompatibility, and rollback/removal cases;
- a measurable advantage over the baseline on at least two representative cases,
  unless one safety-critical case alone establishes necessity;
- maintenance owner, upgrade/revalidation trigger, expiry criterion, and a
  complete removal plan.

Authorization is capability-specific and version-specific. Success for one lane
cannot authorize another, and promotion of an artifact schema does not authorize
a runtime, provider, model, remote, or dedicated leaf.

## 7. Rejected defaults

The following remain rejected unless a future user decision explicitly changes
the relevant boundary after new evidence. This roadmap itself does not do so:

- **`research-lookup`**: no default adoption; its external routing, API keys,
  query transmission, installer warnings, and overlap with Scout/paper lookup
  require a separate security/data-boundary case.
- **Monolithic `literature-review`**: no bundled multi-database orchestration,
  mandatory AI figures, PDF toolchain, synthesis, and external services; adopt
  only a smallest proven mechanism.
- **Autonomous scheduler or workflow service**: no Agent Laboratory/AI Scientist
  scheduler, supervisor, workflow database, or new authority role.
- **Direct LLM code execution**: no execution of model-written code, shell,
  plugins, or arbitrary generated programs.
- **Fixed agents or rounds**: no minimum/target leaf count, debate roster, turn
  count, wave, or all-terminal join.
- **Votes, quorum, rankings, or Elo**: disagreement is resolved by evidence and
  discriminators, not aggregation of model opinions.
- **Tool authority**: no proof checker, solver, retriever, benchmark, profiler,
  checkpoint, validator, Reviewer, Verifier, or Provider accepts science,
  technical integration, allocation, or lifecycle.
- **DVC by default**: existing Git/CAS/runtime provenance remains the baseline;
  DVC needs the specific lineage trigger and local-removal proof in Section 4.8.
- **Broad manager autoloads**: no large scientific skill bundle or domain library
  is loaded into Root, EM, CM, or Portfolio by default; use bounded tasks and
  exact version-matched references.
- **Autonomous manuscript/review production**: generated reports, citation
  scores, novelty claims, and model reviews are drafts/evidence artifacts only,
  never publication-ready findings or dispositions.

These rejections preserve optionality: a later decision may evaluate a narrow,
version-frozen mechanism, but cannot cite “P2 roadmap” as authorization to
install, run, connect, transmit, schedule, or delegate anything.
