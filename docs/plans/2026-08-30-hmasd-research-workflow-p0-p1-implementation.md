# HMASD research workflow P0/P1 implementation plan

## Metadata and boundary

- **Date:** 2026-08-30
- **Status:** implementation-ready; P0 and P1 approved, research execution paused
- **Owners:** Root owns Portfolio and durable allocation/lifecycle state; EM owns direction science; CM owns engineering and technical acceptance; Git/CM integration owns candidate integration; one Experiment Operator owns one exact result-bearing command.
- **Supersession boundary:** this document supersedes only earlier P0/P1 research-workflow implementation notes that prescribe fixed leaf counts, direct Root direction-science leaves, or a single all-terminal join. It does not supersede Root Portfolio, the active allocator, assignment worktrees, registries, BrowserTransport, common v1, the exact Pro review pair, or existing scientific/numerical/RNG/checkpoint/bit-identity/external-effect contracts.
- **P2 boundary:** P2 is not authorized here. Its separate roadmap remains `docs/plans/2026-08-30-hmasd-research-tooling-p2-roadmap.md`.
- **Evidence basis:** `agent://WeeklyRegressionScout`, `agent://ResearchRoleMethodologyAnalyst`, `agent://LocalScientificSkillsScout`, `agent://ScientificPromptPatternScout`, `agent://CDCWorkflowAnalyst`, `agent://EMProfessionalToolsScout`, and `agent://CMProfessionalToolsScout`. External references below are primary links identified by those reports; source visibility is not evidence that adopting a mechanism improves scientific validity.

No implementation step in this plan resumes research. P0 changes orchestration contracts and their tests. P1 may add optional, on-demand tooling only after the provenance/license/commit/dependency gate passes.

## Confirmed regression and required correction

Session `01a04f5a-1c9f-7331-b1d9-249fb767362e` is the confirmed witness. At 2026-08-29 21:09:46 the request fixed two subagents per active direction; at 21:09:55 the assistant committed to two searches; at 21:11:45–21:12:32 Root directly spawned `hmasd-general-leaf` mathematical/enhancement work. This violated both contracts:

1. leaf count must follow independent, answer-changing information gaps, never a default of two; and
2. Root must route direction science through the direction’s EM rather than bypassing EM to scientific leaves.

P0 closes the regression mechanically in prompts, role contracts, and synthetic contract tests. It must not replace the active allocator with an all-terminal wave or create a Portfolio agent.

## Invariants that every change preserves

1. Root performs Portfolio work and retains comparison, allocation, capacity, lifecycle, and durable Portfolio writes.
2. Root sends direction-science work only to the responsible EM. Portfolio may dispatch analytical leaves only for Portfolio-owned, cross-direction information gaps; those leaves return conditional analysis, never allocation or lifecycle decisions.
3. EM alone freezes the direction object, owns scientific synthesis and claim ceiling, interprets observations, and recommends direction disposition.
4. CM alone owns implementation, technical acceptance, and engineering integration. A passing command, tool result, proof checker, validator, or code review is not scientific acceptance.
5. Exactly one Experiment Operator owns one exact result-bearing command. This is an external-effect/idempotency rule, not a staffing quota.
6. BrowserTransport remains Root-mediated and singleton. External review retains the existing common-v1 envelope and exact configured Pro pair, with its current at-most-once/idempotency rules.
7. Assignment branches/worktrees and registries remain the sources of truth. No direct writes to branches outside `omp/*`; assignment candidates integrate only into `omp/workflow` through the existing Git integration owner.
8. No fixed leaves, families, reviewers, waves, debate rounds, durations, or utilization targets. `maxConcurrency` remains a technical ceiling.
9. No direct Root direction-science leaf, vote, majority, quorum, Elo, confidence tally, numeric pseudo-VOI, new authority role, broad manager autoload, silent dependency/network activation, silent scientific/numerical/RNG/checkpoint/bit-identity change, or all-terminal join.
10. `NO_MATERIAL_INSIGHT`, negative/null scientific evidence, technical failure, and scientific rejection remain distinct states.

# P0 — orchestration and contract cutover

## P0 file map

The implementation uses only the exact paths below. The common analytical
vocabulary lives in `.omp/AGENTS.md` and the owning role Skills; P0 does not
invent a common-v1 agent file or change the existing result schema.

| Path | Exact planned change |
|---|---|
| `.omp/AGENTS.md` | Add the common information-gap dispatch rule, neutral packet, analytic return schema, anti-quorum rule, and `NO_MATERIAL_INSIGHT` semantics. State that these rules add no authority role or registry. |
| `.omp/skills/hmasd-root-control/SKILL.md` | Prohibit direct Root direction-science leaves; require meaning-complete EM work; define Portfolio analytical leaves and active, non-all-terminal synthesis. |
| `.omp/skills/hmasd-em-direction-cycle/SKILL.md` | Define first-wave blindness, route/reentry predicates, theorem/concept/counterexample/evidence/family tasks, EM synthesis, negative-complete handling, and conditional CM/Innovator concurrency. |
| `.omp/skills/hmasd-cm-engineering-cycle/SKILL.md` | Remove “exactly one implementer” and “one specialist wave” as general cardinality rules; allow only disjoint writer boundaries; keep exactly one Operator per command. Separate mapping, implementation, review, verification, and observation returns. |
| `.omp/skills/hmasd-scientific-external-review/SKILL.md` | Align scientific finding/no-finding output with the common analytic schema without changing BrowserTransport, common v1, exact Pro pair, preflight, receipt, or at-most-once semantics. |
| `.omp/skills/hmasd-result-run/SKILL.md` | Clarify exact-command singleton ownership and direct-observation output; prohibit scientific interpretation or outcome-improving reruns. |
| `.omp/agents/hmasd-em.md` | Mirror EM-only direction authority, family dispatch, synthesis barrier, negative-complete status, and observation/interpretation separation. |
| `.omp/agents/hmasd-cm.md` | Mirror conditional multi-writer rules, frozen interfaces, one candidate before review/verification, and one Operator per exact command. |
| `.omp/agents/hmasd-research-scout.md` | Require source-bounded evidence packets, dated search boundary, locators, contradiction, and bounded non-detection language. |
| `.omp/agents/hmasd-research-principles-analyst.md` | Require theorem/concept assumptions, exact implications, alternatives, and claim-boundary output; prohibit manager decisions. |
| `.omp/agents/hmasd-research-innovator.md` | Require a distinct mechanism-level family or concrete counterexample/instantiation; permit honest `NO_MATERIAL_INSIGHT`; prohibit novelty theater and sibling anchoring. |
| `.omp/agents/hmasd-research-critic.md` | Add scientific issue schema, reviewed scope, counterexample/alternative, claim-ceiling effect, and no-approval semantics. |
| `.omp/agents/hmasd-reviewer.md` | Keep code review technical; add exact path/symbol, contract/invariant, trigger, causal failure, evidence, repair/check, and reviewed scope. Do not import scientific novelty/causal-validity criteria. |
| `docs/project/HMASD_OMP_CONTROL_PLANE_PROTOCOL.md` | Document Root→EM routing, Portfolio analytical leaves, active allocation, scientific/code review separation, and negative-complete semantics. |
| `.omp/skills/hmasd-portfolio-control/` | Remove the empty Portfolio skill scaffold and any stale publication/reference to it. Do not replace it with a Portfolio agent or skill; Root remains Portfolio. An empty untracked directory naturally disappears. |
| `tests/hmasd_portfolio_logic_contract_test.py` | Extend current topology/Root assertions with Root→EM-only direction dispatch, Portfolio analytical leaf limits, active non-all-terminal behavior, common-v1/BrowserTransport/Pro-pair preservation, and empty Portfolio-skill removal. |
| `tests/hmasd_topology_contract_test.py` | Verify the empty Portfolio skill is gone, Root still owns Portfolio, and only accepted on-demand P1 Skills enter the published inventory. |
| `tests/hmasd_research_workflow_contract_test.py` | Add focused contract cases for neutral blind packets, gap-driven count, output schema, family tasks, review separation, CM writer boundaries, conditional concurrency, and negative-complete behavior. |
| `tests/hmasd_research_workflow_synthetic_smoke_test.py` | Add a synthetic OMP scenario described below. It must exercise semantic state transitions in fixtures/harness objects and must not inspect or assume CLI command availability. |

All paths above either exist now or are the two explicitly named new test
files. The clean cutover creates no alias, deprecated compatibility path, or
second protocol convention.

## P0.1 Common information-gap dispatch

A manager dispatches an analytical leaf if and only if all are true:

- the unanswered item can change a manager-owned decision: Root’s Portfolio rationale, EM’s discriminator/claim ceiling, or CM’s technical acceptance;
- the gap is separable from manager synthesis and the leaf has a method, source, code-map, or tool advantage;
- the return is inspectable: a proof step, construction, counterexample, source packet, dependency map, diff finding, or direct observation;
- scope, protected semantics/effects, positive/negative/null/ambiguous/failure branches, stop condition, and reentry are frozen; and
- accepted evidence does not already answer the question.

The neutral input packet contains the manager-owned variable, frozen question/claim/contract, authoritative definitions and hashed references, separated facts/evidence/inferences/speculation/contradictions, the exact gap and assigned lens, outcome branches, non-goals, ownership/effects, required output, stop, and reentry. It contains no favored answer, desired PASS, sibling conclusion, vote tally, or allocation preference.

The common analytical output is:

- question answered and `MATERIAL_INSIGHT` or `NO_MATERIAL_INSIGHT`;
- concrete product and exact source/artifact/observation references;
- assumptions and applicability boundary;
- verified facts, external evidence, inference, speculation, and contradiction kept distinct;
- surviving alternatives and the conditional effect on the manager-owned variable;
- limitations, next discriminator, exact residual gap, `DONE_REASON`, and reentry trigger.

`NO_MATERIAL_INSIGHT` is a successful terminal analytical return meaning no answer-changing result within the frozen scope. It is not `FAILED`, approval, negative evidence, evidence of absence, or scientific rejection. It records what was tried and the residual gap. The same family/input is reopened only after a new mechanism, source, observation, premise, or corrected defect.

**Observable acceptance:** a contract fixture with zero gaps dispatches zero leaves; one gap dispatches one fitting leaf; three separable gaps may dispatch three leaves; duplicate gaps do not increase count. Every accepted return contains the common fields. A `NO_MATERIAL_INSIGHT` return closes its assignment without changing a claim or silently resampling it.

## P0.2 Root and Portfolio

### Direction routing

Root constructs meaning-complete `WORK` for the active direction and sends it to that direction’s EM. Root must not send theorem, concept, mechanism, counterexample, evidence-retrieval, implementation, or enhancement work directly to a generic/research leaf. EM chooses whether any direction leaf is warranted.

**Observable acceptance:** the synthetic witness modeled on session `01a04f5a...` requests “two subagents per direction.” Root rejects the numeric instruction as a scientific quota, creates one EM assignment per selected direction, and creates no direct direction leaf. EM then dispatches only the distinct gaps present in its frozen packet.

### Portfolio analytical leaves

Root may dispatch a Portfolio leaf only for one of these cross-direction analytical gaps:

- **shared-assumption audit:** dependency, affected directions/layer, necessity, common-mode failure path, and independent discriminator;
- **complement/substitute analysis:** `COMPLEMENT | SUBSTITUTE | ORTHOGONAL | CONDITIONAL | UNKNOWN`, mechanism, conditions, evidence, and sequencing implication, distinguishing scientific value, information value, engineering reuse, and common risk;
- **option value:** branch opened/preserved/closed, reversible enabling action, exercise/abandon/expiry trigger, information gained, irreversibility, dependencies, and bounded cost/time, with no invented probability or rank;
- **cross-direction risk:** mechanism, exposed directions, propagation, trigger, blast radius, relatively independent check, and reversible mitigation/tradeoff.

Portfolio leaves return conditional relationships only. They do not rank directions, allocate resources, change lifecycle, write direction state, or adjudicate science. Root synthesizes cited mechanisms and dependencies, not counts.

### Active allocation, not an all-terminal join

Root may act on an unrelated direction as soon as its decision evidence is sufficient. It waits only for a live specialist whose result is a dependency of the contemplated action. An unresolved relationship terminates as explicit `UNKNOWN` with a reentry trigger; it does not hold every direction at a global barrier.

**Observable acceptance:** in a synthetic three-direction state, A can advance while an A-dependent shared-risk leaf is complete even though an unrelated B analysis remains live; an A action that depends on a live A/B substitute analysis is withheld; no “all terminal” predicate appears in the transition.

## P0.3 EM direction work

### First-wave blindness

When more than one genuinely different scientific family is needed, early leaves receive the same neutral freeze and different mechanism-level lenses. They do not receive the favored route or sibling conclusions until each has returned a substantive artifact or `NO_MATERIAL_INSIGHT`. Authoritative constraints and known invalidating evidence are never hidden. After the barrier, EM may cross-pollinate exact artifacts and gaps.

**Observable acceptance:** serialized early assignment bytes contain no favored-family or sibling-result field; later critique assignments cite the frozen claim and admissible returned packet IDs. Paraphrases of one mechanism fail the semantic-diversity fixture.

### EM task families

EM invokes none, one, or several families according to unresolved gaps:

1. **Theorem derivation** — exact proposition, definitions, quantified assumptions, named-result hypothesis mapping, lemma/dependency chain, boundary cases, circularity check, and `PROVED_WITHIN_SCOPE | CONDITIONAL | REFUTED | OPEN`; a reduction must show why the new obligation is strictly simpler or remain blocked at the exact missing lemma.
2. **Concept/prototype validation** — mechanism→behavior→capability chain, distinction from baseline, minimal instantiation, comparator, positive/negative/null/ambiguous predictions, identifiability limits, and falsifier. Executable validation becomes a durable EM request routed through Root to CM.
3. **Counterexample/adversarial search** — frozen target claim, minimal witness or boundary case, violated implication/assumption, attacked layer, damage scope, surviving corrected claim, and next discriminator. The leaf never silently rewrites the target.
4. **Evidence retrieval** — source ID, exact URL/DOI/version/date, locator, excerpt, support/challenge, applicability, search boundary, and unresolved evidence. “Not located within the documented search boundary” never becomes “no prior work exists.”
5. **Genuinely different family generation** — mechanism/reduction/comparator/invariant/measurement/failure-mode family, concrete product, predictions, assumptions, common-failure links, and refutation condition. Persona or wording changes are not distinct families.

EM preserves outliers and counterexamples, checks unused evidence and unasked answer-changing questions, requests the smallest executable discriminator from CM, and sets the claim ceiling. Route exhaustion preserves the exact gap; leaf failure does not imply mechanism failure.

### Negative-complete status

A scientifically adverse, null, or bounded negative observation can satisfy the frozen material and complete the EM cycle. EM records the strongest supported negative/null statement, assumptions, limits, alternatives, and Portfolio-facing implication. A technical failure yields no scientific update. `NO_MATERIAL_INSIGHT` yields no claim delta. These statuses remain separately queryable in the existing direction/result record; no new lifecycle authority or status registry is added.

**Observable acceptance:** fixtures distinguish (a) valid negative observation → scientific `COMPLETE` with adverse disposition, (b) successful analysis with no delta → `NO_MATERIAL_INSIGHT`, and (c) command/tool failure → technical failure and no scientific disposition.

### Conditional CM/Innovator concurrency

EM may request a non-writing Innovator route while CM evaluates or implements a frozen executable discriminator only when:

- both consume the same immutable scientific freeze;
- the Innovator cannot change the interface, test oracle, input identity, or command owned by CM;
- paths, semantic boundaries, effects, and outputs are disjoint; and
- EM declares how the two results rejoin.

If the Innovator can alter the discriminator or CM contract, EM resolves that scientific branch before CM starts or issues a new versioned request after CM stops. The Innovator never writes the CM candidate.

**Observable acceptance:** a fixture permits concurrent alternative-mechanism analysis plus a frozen read-only feasibility check, but rejects concurrent mutation of the tested hypothesis/interface.

## P0.4 Scientific review versus code review

| Boundary | Scientific review | Code review |
|---|---|---|
| Owner/role | Research Critic and, where authorized, the existing exact Pro convergence pair; EM dispositions | `hmasd-reviewer`; CM dispositions |
| Object | Frozen claim, definitions, comparator/estimand, causal/proof logic, evidence, alternatives, claim ceiling | Frozen base/diff, engineering contract, interfaces, protected invariants, focused evidence |
| Method | Broken assumptions, counterevidence, confounds, circularity, metric gaming, overreach, simpler explanations, falsifiers | Design/functionality, callers, edge cases, concurrency, complexity, tests, numerical/RNG/checkpoint/resource/effect semantics, maintainability |
| Return | attacked claim/link, evidence/counterexample, epistemic label, material claim effect, surviving alternative, discriminator, reviewed scope/limit | exact path/symbol/line, violated contract/invariant, trigger and causal failure, technical impact, evidence, minimal repair/check, reviewed scope |
| Authority excluded | no code acceptance, allocation, lifecycle, external send, or result command | no scientific validity, novelty, causal interpretation, allocation, lifecycle, edit, or command execution |

A no-finding result is `NO_MATERIAL_INSIGHT` within reviewed scope, never approval. Existing external-review transport remains frozen: Root-mediated BrowserTransport, common v1, exact Pro pair, exact target, stable idempotency key/fingerprint, known commitment state, and no resend after unknown commitment.

**Observable acceptance:** tests reject a scientific critic that returns code approval, reject a code reviewer that returns scientific acceptance, and accept each review only with its object-specific schema and owner disposition.

## P0.5 CM decomposition and writer ownership

CM dispatches only unresolved technical gaps:

- Project Scout for layout/build/path/pattern facts;
- Code Scout for definitions, callers, interfaces, state/lifetime, and verification seams;
- `hmasd-implementer` for observable or protected semantics;
- `hmasd-implementer-terra` only for demonstrably behavior-preserving local refactors, stopping before a semantic boundary;
- `hmasd-reviewer` only after CM freezes one integrated candidate where independent inspection can change acceptance;
- `hmasd-verifier` for one exact runtime/equivalence/environment fact; and
- exactly one `hmasd-experiment-operator` for the one exact result-bearing command.

Multiple writers are permitted only when both path ownership and semantic/interface ownership are disjoint and the shared interfaces are frozen. Different files are insufficient if they implement one live boundary. No two writers edit the same live boundary, and CM alone integrates returned deltas. Review and verification start after integration, not against sibling partial candidates. Missing Reviewer/Verifier/Advisor output is an evidence gap, not approval or rejection.

**Observable acceptance:** fixtures accept two writers on independent modules with a frozen interface, reject writers on different files that jointly mutate one protocol, and preserve exactly one Operator for an exact command while allowing any number of separable non-effect gaps.

## P0.6 Empty Portfolio skill cleanup

Remove `.omp/skills/hmasd-portfolio-control/` if it is empty and remove stale index/config/test references that publish it. Do not add a placeholder file to retain the directory. `.omp/AGENTS.md`, Root control, the human protocol, and topology tests must say Root performs Portfolio directly.

**Observable acceptance:** topology discovery contains no Portfolio agent or Portfolio skill; Root still exposes the complete Portfolio decision frame and active allocator.

## P0.7 Synthetic OMP smoke

The smoke is semantic and hermetic; it does not discover, invoke, or assert availability of any CLI command. Use the repository’s existing contract-fixture style or a minimal in-memory assignment/event fixture.

Scenario:

1. Root holds two active directions, preserved registries/worktrees, capacity, and a user instruction requesting two leaves per direction.
2. Root ignores the fixed scientific count, emits one meaning-complete EM work item per selected direction, and emits no direct research/general leaf.
3. EM-A identifies three gaps: theorem implication, primary-source evidence, and executable discriminator. It creates two mutually blind analytical assignments and a durable CM request; count follows gaps and fitting methods rather than “two.”
4. One analytical route returns `NO_MATERIAL_INSIGHT`; the other returns a concrete counterexample packet. EM narrows the claim and does not retry the no-insight route.
5. CM freezes an interface, permits two genuinely disjoint writers, integrates one candidate, performs technical review, and assigns the exact result command to one Operator.
6. The Operator returns exact input identity, direct observation, exit status, and artifact references. CM checks technical conformance; EM alone records a bounded negative scientific completion.
7. Root advances direction A without waiting for unrelated direction B work. BrowserTransport/common-v1/Pro-pair fields and assignment worktree/registry identities remain unchanged.

Smoke acceptance is the observed event/state trace: no direct Root science leaf, no quota-derived count, blind initial packets, common analytic schema, no-insight terminality, disjoint writers, singleton command owner, technical/scientific separation, negative completion, active non-all-terminal allocation, and preservation of protected identities.

# P1 — gated on-demand research tooling

P1 starts only after P0 is merged and its focused contracts pass. P1 does not autoload tools into Root, EM, or CM and does not resume research. Each wrapper is invoked only by the accountable manager for an exact gap and returns artifacts/observations under the common schema.

## P1.1 Mandatory provenance, license, commit, dependency, and effects gate

For every adopted upstream component, record in `docs/research-tooling/provenance.yml`:

- upstream repository and exact file/subtree;
- immutable commit SHA and upstream release/tag when available;
- local copied/adapted file hashes and modification notice;
- upstream license, file-level exceptions, attribution/NOTICE obligation, and transitive dependency license result;
- maintainer/release risk and last-reviewed date;
- Python/runtime/platform compatibility and a locked dependency set;
- network endpoints, request fields, secrets boundary, rate limits, data retention, and failure behavior;
- deterministic inputs, seed/solver/options/precision/tolerance/version fields, outputs, hashes, and artifact paths;
- owner, scientific-authority exclusion, stop/reentry, and uninstall/rollback procedure.

The gate fails closed if the license is absent/incompatible, the source is pinned only to mutable `main`, copied assets lack provenance, transitive dependencies are unresolved, project pins would be silently upgraded, network/secret behavior is not explicit, or protected numerical/RNG/checkpoint/bit-identity semantics would change. Failure leaves the tool external and preserves P0 behavior.

P1 uses these exact isolated support paths:

- `requirements_research_tools.txt` — fully resolved optional pins and hashes
  for the supported interpreter/platform; it is never included by default
  runtime requirements;
- `tools/research/` — adapted deterministic scripts and thin wrappers;
- `tests/research_tools/` — fixture-only contract tests with network disabled by
  default; and
- `docs/research-tooling/provenance.yml` and
  `docs/research-tooling/NOTICE` — machine-readable provenance and required
  attribution.

Each accepted wrapper updates `tests/hmasd_topology_contract_test.py` in the
same change so the published Skill inventory cannot drift from the reviewed
capability set. No P1 dependency changes `requirements_server.txt`,
`requirements_sb3.txt`, or the default environment.

**Observable acceptance:** a fixture with a missing commit, license, transitive license, or network declaration refuses activation; an accepted fixture resolves immutable source and local hashes, exact optional lock, no default autoload, and reproducible offline help/validation behavior.

## P1.2 Minimal wrapper paths and contracts

### Paper lookup

- **Paths:** `.omp/skills/hmasd-paper-lookup/SKILL.md`, `tools/research/paper_lookup/`, `tests/research_tools/test_paper_lookup_contract.py`.
- **Source:** K-Dense `paper-lookup`, pinned after gate: <https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/paper-lookup>.
- **Contract:** EM or Research Scout supplies a bounded query, approved endpoints, date/page limits, and external-data classification. Return source ID, DOI/version, endpoint parameters, access date, locator/excerpt, pagination/count reconciliation, support/challenge/limits, and errors including HTTP-200 error payloads. No synthesis, novelty verdict, or evidence-of-absence claim.
- **Acceptance:** recorded fixture responses produce deterministic packets; pagination and false-success payloads are surfaced; live network is absent from default tests and never activated silently.

### K-Dense hypothesis-generation and peer-review mechanisms

- **Paths:** `.omp/skills/hmasd-hypothesis-mechanisms/SKILL.md`, `tools/research/hypothesis_mechanisms/`, `tests/research_tools/test_hypothesis_mechanisms_contract.py`.
- **Sources:** pinned K-Dense hypothesis-generation and peer-review skills: <https://github.com/K-Dense-AI/scientific-agent-skills/blob/f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f/skills/hypothesis-generation/SKILL.md> and <https://github.com/K-Dense-AI/scientific-agent-skills/blob/f6fcafeb1cc8c82eca0160a18bc41c38427b8e0f/skills/peer-review/SKILL.md>.
- **Contract:** local deterministic templates/validators only. Candidate records contain rival family, assumptions, boundary, observable, prediction/uncertainty, falsifier, rival contrast, indeterminate outcome, controls, and admissible packet IDs. Peer-review issues contain location, observation, evidence/criterion, impact, requested action, reviewed scope, and EM-owned disposition. Validators check declarations/internal consistency, never truth or approval.
- **Acceptance:** zero or variable candidates are valid; no scoring/ranking/fixed count; missing evidence is “not reported”; a validator pass cannot change scientific status.

### Experimental design scripts

- **Paths:** `.omp/skills/hmasd-experimental-design-tools/SKILL.md`, `tools/research/experimental_design/`, `tests/research_tools/test_experimental_design_contract.py`.
- **Source:** pinned K-Dense scripts: <https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/experimental-design>.
- **Contract:** EM freezes unit, randomization level, blocking/stratification/factor design, seed, sample structure, balance checks, outcome branches, and schedule hash; CM may generate/validate the schedule and execute only that frozen artifact. Any schedule/seed change is a new scientific protocol version.
- **Acceptance:** identical frozen inputs reproduce the schedule/hash; invalid randomization level or missing seed fails; no pseudoreplication or balance claim is inferred from script success.

### Scientific-writing validators

- **Paths:** `.omp/skills/hmasd-scientific-writing-validation/SKILL.md`, `tools/research/scientific_writing/`, `tests/research_tools/test_scientific_writing_contract.py`.
- **Source:** pinned K-Dense scripts: <https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/scientific-writing>.
- **Contract:** offline source manifest, claims table, claim-source consistency, references, authorship/reporting declarations, and artifact hashes. A pass means only that the declared structure is internally consistent; it does not verify sources, truth, reporting completeness, or publication readiness.
- **Acceptance:** unsupported claim IDs and missing locators fail; fixtures work offline; no figure-generation or external-provider requirement is introduced.

### SymPy and Z3

- **Paths:** `.omp/skills/hmasd-symbolic-counterexample-tools/SKILL.md`, `tools/research/symbolic/`, `tests/research_tools/test_symbolic_tools_contract.py`.
- **Primary sources:** SymPy <https://github.com/sympy/sympy> (BSD) and Z3 <https://github.com/Z3Prover/z3> (MIT), each pinned to reviewed releases rather than moving branches.
- **SymPy contract:** freeze domains, symbol assumptions, exact expression/script, precision, simplification options, versions, expected residual checks, and an independent numerical or analytic cross-check. CAS output is a derivation aid, not proof.
- **Z3 contract:** freeze SMT-LIB2/Python encoding, logic/theory, assumptions, options, solver seed, timeout, solver version, input hash, model/unsat/unknown output, and encoding audit. A SAT model is a concrete witness for the encoded claim; UNSAT is only relative to the frozen encoding/theory.
- **Acceptance:** artifacts reconstruct exact inputs and versions; unknown/timeout remains explicit; no solver/CAS output directly changes EM disposition; alternate solver use occurs only when solver diversity answers a declared gap.

### Hypothesis property tests and NumPy/SciPy numerical contracts

- **Paths:** `.omp/skills/hmasd-scientific-compute-contracts/SKILL.md`, `tools/research/scientific_compute/`, `tests/research_tools/test_scientific_compute_contract.py`.
- **Primary sources:** Hypothesis <https://hypothesis.readthedocs.io/en/latest/>, NumPy testing <https://numpy.org/doc/stable/reference/testing.html>, and SciPy <https://docs.scipy.org/doc/scipy/reference/>; exact repositories/releases/licenses must pass the gate.
- **Hypothesis contract:** freeze property, generator domain/filters, examples, seed/replay artifact, health/shrink settings, version, and minimal counterexample. Property testing is bounded falsification, not theorem proof; a pass means no counterexample in the recorded run.
- **NumPy/SciPy contract:** freeze dtype/device, shapes, units, NaN/Inf/signed-zero policy, ordering, algorithm/version, RNG object/state, tolerances with domain justification, statistical assumptions, and oracle. Tolerance checks and exact bit identity are separate: exact identity uses canonical bytes/hashes, never `allclose`. Numerical warnings, convergence failure, nondeterminism, and ill-conditioning remain explicit.
- **Acceptance:** plausible boundary generators can shrink to retained counterexamples; tolerance tests reject unjustified defaults; bit-identity fixtures use byte/hash equality; dependency activation cannot alter existing numerical or RNG behavior silently.

## P1.3 Explicit exclusions

- Keep broad `literature-review`, `scientific-critical-thinking`, NetworkX, PyG, SB3, PufferLib, research-lookup, DVC, benchmarking, profiling, and additional proof assistants external unless a later exact gap and separate authorization justify them.
- `review-required/research-lookup` is not adopted because its external data/security boundary and dependency warnings are unresolved.
- CDC prompt/proof and `cdc-lean` are method evidence, not copyable runtime components absent reuse licenses.
- AI Scientist prompt text is not copied because the pinned repositories use a custom restricted license; only independently expressed safeguards are adopted.
- No tool gets manager authority, automatic network access, secret access, implicit retries, result averaging, or default agent autoload.

# Evidence-to-change map

| Evidence/system | Primary link | Concrete HMASD change | Rejected transfer |
|---|---|---|---|
| OpenAI CDC | <https://cdn.openai.com/pdf/04d1d1e4-bc75-476a-97cf-49055cd98d31/cdc_prompt.pdf> | EM mechanism-level families, first-wave blindness, exact blocked obligation/reentry, concrete lemma/construction/counterexample outputs, object-specific audit | fixed scale, fixed duration, affirmative prior, monolithic Root science, approach quota |
| PaperQA2 | <https://github.com/Future-House/paper-qa/blob/57e89f7223b0960d5ee5ea048c69e3c47e088572/src/paperqa/prompts.py> | neutral source packets before synthesis, current admissible evidence IDs, explicit insufficiency/no-answer boundary | retrieval or citation presence as authority; mutable-release copying |
| STORM/Co-STORM | <https://arxiv.org/html/2408.15232> | EM checks unused evidence and unasked answer-changing questions; Portfolio may request bounded cross-direction gaps | mandatory multi-agent conversation or moderator authority |
| POPPER | <https://cs.stanford.edu/people/jure/pubs/auto-hypothesis-validation-icml25.pdf> | separate scientific implication/design, execution observation, and EM interpretation; explicit branches and stop | generic statistical validity or automated scientific acceptance |
| K-Dense scientific skills | <https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills> | rival families, falsifiers, indeterminate outcomes, non-scoring validators, bounded paper lookup/design/writing tools | forced counts, truth-by-validator, broad autoload, silent dependencies |
| Agent Laboratory | <https://github.com/SamuelSchmidgall/AgentLaboratory/blob/d9017d90e329112d2a80b7712f37ee9094d2cd27/agents.py> | explicit admissible-memory/expiry fields and inspectable command/artifact contracts | time-pressure prompts, consensus closure, prestige/novelty theater, monolithic adoption |
| Debate evidence | <https://proceedings.mlr.press/v235/smit24a.html> | anti-quorum rule; conflicts require discriminators and counterexamples rather than votes | mandatory debate, majority, agreement-as-confidence |
| AI Scientist safeguards | <https://github.com/SakanaAI/AI-Scientist/blob/1de1dbc1f4ee2c5f61e9c94348d55eb51d7fa2eb/ai_scientist/perform_experiments.py> | exact command/input/output/artifact/stop contract, explicit timeout/error, scientific interpretation kept separate | restricted prompt copying, self-declared convergence, absence-as-novelty, outcome-improving reruns |
| Professional theorem/symbolic tools | <https://github.com/openai/cdc-lean>, <https://github.com/sympy/sympy>, <https://github.com/Z3Prover/z3> | pinned theorem artifacts where justified; SymPy derivation checks; Z3 witnesses/encoding-relative UNSAT | checker/CAS/solver as science; unlicensed CDC source copying |
| Professional code/science tools | <https://hypothesis.readthedocs.io/en/latest/>, <https://numpy.org/doc/stable/reference/testing.html>, <https://docs.scipy.org/doc/scipy/reference/> | property-based falsification, minimal counterexamples, explicit numerical oracle/tolerances, exact-byte identity boundary | finite testing as proof, `allclose` as bit identity, silent RNG/numerical changes |
| Reproducibility distinction | <https://www.nationalacademies.org/read/25303/chapter/3> | successful rerun is technical evidence; replication and scientific correctness remain separate | reproduced output as automatic acceptance |
| Code-review practice | <https://google.github.io/eng-practices/review/reviewer/looking-for.html> | technical review covers design, behavior, edges, concurrency, complexity, tests, and context | reviewer approval authority or scientific rubric |

# Clean cutover and ownership order

1. **Contract writer:** update `.omp/AGENTS.md` common dispatch/output/anti-quorum rules first; preserve common v1 and effect contracts.
2. **Root writer:** update Root control and human protocol; remove direct direction-leaf language; add Portfolio analytical leaves and active dependency-aware synthesis.
3. **EM writer:** update EM skill/agent and research leaf agents with family contracts, blindness, output/reentry, review, negative completion, and conditional CM concurrency.
4. **CM writer:** update CM skill/agent, reviewer, and result-run contracts; replace general fixed cardinality with disjoint writer boundaries while preserving singleton Operator ownership.
5. **External-review writer:** align finding output only; do not alter BrowserTransport, common v1, exact Pro pair, idempotency, preflight, receipts, or commitment rules.
6. **Topology cleanup writer:** remove the empty Portfolio skill publication/scaffold, without adding a Portfolio role.
7. **Test writer:** update existing contract tests, add research workflow contracts, then add the semantic synthetic smoke. Tests inspect canonical contracts and state/event behavior, not CLI availability or source-text trivia alone.
8. **CM integration owner:** integrate each disjoint assignment candidate into `omp/workflow`, resolve only frozen interfaces, and run focused P0 verification once after integration. Root/CM records the evidence; assignment writers do not commit/push to non-owned branches.
9. **P1 gate owner:** after P0 acceptance, land provenance/license/dependency infrastructure before any wrapper. Each wrapper is a separate disjoint assignment and remains inactive until its own gate fixture passes.

No two writers may concurrently edit one listed file or one shared semantic/interface boundary. Disjoint files alone do not establish safe concurrency. Worktrees and assignment registries remain canonical; Root does not write direction state, and leaves do not integrate candidates.

# Verification claims, owners, and evidence

| Claim | Verification owner | Required evidence |
|---|---|---|
| Root never bypasses EM for direction science and does not honor fixed leaf quotas | P0 test owner; CM accepts | focused Root contract assertions plus the session-`01a04f5a...` synthetic regression trace |
| Portfolio leaves are analytical, conditional, and non-authoritative | P0 test owner; Root checks protocol | one fixture per shared-assumption, complement/substitute, option-value, and cross-risk schema, including `UNKNOWN` |
| Active allocator does not wait for all terminal work | P0 test owner | dependency-aware transition trace showing unrelated progress and dependent withholding |
| Blind routes are neutral and semantically distinct | EM contract/test owner | serialized packet comparison and semantic-family fixture; no favored/sibling field before barrier |
| Every analytical return is inspectable, including `NO_MATERIAL_INSIGHT` | common contract/test owner | schema cases for material/no-material/failure and reentry rules |
| EM family tasks and negative completion preserve scientific authority | EM contract/test owner | theorem, concept, counterexample, evidence, family, adverse/null, and technical-failure fixtures |
| Scientific and code review remain distinct | EM and CM test owners | object-specific finding schemas and rejected cross-authority returns |
| Parallel writers are disjoint; one exact command has one Operator | CM contract/test owner | accepted independent-boundary case, rejected shared-boundary case, singleton command-owner trace |
| Portfolio skill remains absent while Root retains Portfolio | topology test owner | canonical topology/skill discovery and complete Root decision-frame assertions |
| BrowserTransport, common v1, exact Pro pair, registries, worktrees, and external-effect semantics are unchanged | integration owner | before/after canonical identity and contract assertions in existing focused tests |
| P1 tools are optional, pinned, licensed, inspectable, and non-authoritative | each wrapper owner; CM accepts technical gate; EM accepts only later evidence use | provenance record, immutable hashes, optional lock, offline fixtures, explicit network/effect contract, artifact reconstruction, and authority-negative tests |
| Scientific/numerical/RNG/checkpoint/bit identity is not silently changed | CM and verifier | explicit oracle/seed/version/tolerance/hash fixtures; no default dependency activation |

These are prospective verification requirements, not claims that tests or tools were run while writing this plan.

# Stop and rollback

Stop the P0 assignment and return it for replacement if the frozen authority split, protected transports/common-v1/Pro pair, worktree/registry model, or listed ownership scope materially changes. Stop an individual writer at an unexpected shared boundary rather than broadening its assignment.

Rollback is a clean candidate reversion through the CM/Git integration owner:

- revert the unaccepted assignment candidate from `omp/workflow` rather than editing unrelated work;
- restore the last canonical P0 contract set as a unit if Root/EM/CM/common schema versions cannot agree;
- preserve durable Portfolio/direction records, worktrees, registries, receipts, commitment state, and result artifacts;
- never resend an external operation with unknown commitment and never rerun a result command to improve an outcome;
- for P1, remove the optional wrapper and lock/provenance entry together, disable its on-demand publication, and retain already-produced provenance/artifacts as historical evidence;
- a P1 gate failure rolls back only that wrapper and cannot weaken P0 orchestration.

P0 is complete only when every P0 observable acceptance above passes in the integrated focused contracts and semantic smoke. P1 is complete only when each adopted wrapper independently passes the gate and its contract tests. P2 remains entirely governed by `docs/plans/2026-08-30-hmasd-research-tooling-p2-roadmap.md`.
