# HMASD workflow capability restoration plan

Status: IMPLEMENTED / ROLLOUT PENDING — repository changes and one-time implementation QA are
complete. This document is not workflow authority and does not itself resume the paused
two-direction pilot.

## 1. Acceptance definition

This migration succeeds only when all five conditions hold together:

1. The active system remains four top-level role classes—Root, Portfolio, `EM/<direction>`, and
   `CM/<direction-or-shared>`—plus thin depth-one specialist leaves.
2. EM and CM retain the useful scientific and engineering capability previously carried by their
   specialist children; deleting an old control file never silently deletes its useful method.
3. The current native-task workflow and the current EM material-cycle design remain authoritative.
4. Semantic purity is explicit: shared semantics are global, while each skill, profile, and role sees
   only its own method and adjacent interface.
5. The design trusts Codex Desktop and the local single-user project. It adds no workflow
   authentication, SHA256 ceremony, receipt/ledger, registry, router, scheduler, retry controller,
   duplicate file confirmation, or fixed approval panel.

The old control plane is not supported or migrated. Old commits are evidence for capability
inventory only.

## 2. Layer ownership

| Layer | Owns | Must not contain |
| --- | --- | --- |
| `AGENTS.md` | universal semantic authority: exhaustive shared field/status meanings, caller matrix, non-inference rules, model/short-name policy, universal leaf/Effect/Git boundaries | role methods, Agentify UI recipe, material-cycle procedure, migration history |
| `WORKFLOW_PROTOCOL.md` | cross-task authority only: native WORK/RESULT/CONTROL, adjacent handoff meaning, liveness/join, native worktree, EM↔CM writer transfer | role milestone/cycle methods, leaf recipes, model prompts, duplicated field tables, old compatibility |
| four session `SKILL.md` files | trigger, shortest entry, own role pointer, exact authority/inputs to read | another role's fields/method, model/sandbox, full topology, UI recipe, migration explanation |
| `.agents/roles/<ROLE>.md` | one role's mission, inputs, owned judgment, method for choosing within the AGENTS-authorized leaf set, bounded recovery, and conclusion formation | caller allowlist, status enums, other roles' procedure, model/sandbox, global state tables |
| `.codex/agents/*.toml` | identity, model, effort, sandbox, own-role pointer only | copied methodology, topology/boundaries, result schema, full protocol, other role fields, transport recipe |
| explicit transport skill | trigger and navigation to the single compact mechanics reference | science/engineering judgment, copied API procedure, Portfolio consequences, local ledger, workflow identity |
| compact Agentify reference | sole strict file-backed send/observe/archive procedure | owner judgment, workflow state, duplicate skill procedure, legacy ledger/manual |
| EM/CM milestone snapshot | last material conclusion needed after compression | task identity, authentication, routing, event log, retry counter, approval gate |

`AGENTS.md` replaces the old claim that the protocol is the only authority: AGENTS owns the injected
universal semantic kernel, while the protocol is the only cross-task transport authority. All tracked
role documents must be explicitly unignored. Every profile points to exactly its own role. Every
session skill points to exactly its own top-level role. Leaves never read the full protocol.

## 3. Capability-conservation matrix

| Legacy capability source | Category | Current owner | Preserved capability | Rejected legacy architecture |
| --- | --- | --- | --- | --- |
| Root recovery method | CURRENT_MANAGER | Root | original outcome, protected invariants, safe reproduction, causal break, one hypothesis-driven repair, focused regression, end-to-end acceptance | persistent recovery manager, incident registry, heartbeat, local routing |
| externally researched Portfolio method | CURRENT_MANAGER | Portfolio | quality floor before allocation; qualitative comparison of route difference, shared assumptions, decision value, cost/time/stage, reversibility, option value and independent validation; anti-homogenization check | Elo, scalar score, fabricated success probability, vote, persistent hypothesis graph |
| Independent Explorer scientific method | CURRENT_MANAGER | EM and current EM cycle | question/estimand, construct-first research, mechanisms, evidence synthesis, claim ceiling, discriminator, result interpretation | old L1 identity, Operational Root bridge, cross-root artifacts, Gemini, old packets |
| Research Innovator capability | THIN_LEAF | `ri` | distinct mechanism family; adapt/combine/develop/refine/split/dependency challenge; source-to-target assumptions; delete/retain/add; causal chain; prediction/falsifier/retirement | direction selection, durable authoring, fixed panel or acceptance |
| Research Principles capability | THIN_LEAF | `rp` | stochastic game, information sets, identity ownership, semi-Markov clocks, effective action space, information/credit flow, optimizer exposure, exploration driver, passive-noise and co-adaptation checks | mandatory quorum, packet gate, final claim judgment |
| Research Scout capability | THIN_LEAF | `rs` | primary-source and PDF fidelity, facts versus inference, provenance, conflict, uncertainty, one bounded recheck | scientific disposition or open-ended search |
| Research Critic capability | THIN_LEAF | `rc` | strongest null/counterexample, passive noise, capacity, optimizer exposure, partner co-adaptation, causal alternatives and discriminator | veto, acceptance, mandatory duplicate review |
| Pro transport capability | THIN_LEAF | EM-authored prompt + `pt` | one fresh Innovator and one independent Convergence per material cycle, GitHub connector access, science-only review, objection disposition | provider as owner, code review, Gemini fallback, old resend/ledger/closure authority |
| Code Project Manager engineering method | CURRENT_MANAGER | CM | engineering contract, mapping, implementation selection, integration, focused verification, failure classification, runtime interpretation, Git closure | old L1 manager, lease/router/readiness state machine |
| Code/Project Scout capability | THIN_LEAF | `cs` | files/symbols/callers/consumers/state owner/shapes/tests/shared boundaries and project fact map | separate generic project-scout manager or acceptance |
| semantic Implementer capability | THIN_LEAF | `im` | probability/gradient/replay/recurrent/RNG/checkpoint/result semantics; production chain; native batching; equivalence seams | Git, experiments, scientific/technical acceptance, L2 children |
| routine Implementer capability | THIN_LEAF | `rt` | behavior-preserving repair/refactor; loader/cache, packed state, bounded worker, focused tests, reversible changes | material architecture/science decisions, Git, L2 children |
| Reviewer capability | THIN_LEAF | `rv` | independent material-risk findings, normal-path likelihood/effect/repair cost/residual risk, one bounded reread | approval layer, fixed review chain |
| Verifier capability | THIN_LEAF | `vf` | one proof-sized runtime/equivalence observation with exact proof root and no duplicate launch | tracked edits, acceptance, generic readiness phase |
| Experiment Operator capability | THIN_LEAF | `op` | one exact command, same process handle, terminal witness | retry, repair, implementation, scientific interpretation |
| engineering transport capability | THIN_LEAF | `et` | exact engineering question send/observe/archive fidelity | technical acceptance or provider-driven routing |
| mechanical/artifact/general helper capability | THIN_LEAF | `gl` | bounded download, organization, conversion, fixture, literal extraction, exact manager-approved mechanical write | dedicated mechanical planes, artifact ownership, model roster expansion |
| old task/control function | NATIVE_REPLACEMENT | Codex Desktop native plane | visible task ID/history/status/create/send/read/wait/worktree/archive | Clerk, envelope, digest, receipt, local task DB, registry, scheduler, compatibility |

Algorithm, RNG, checkpoint, result, run-manifest, and scientific reproducibility tests are not old
control-plane capability and remain untouched.

### 3.1 External agentic-science research retained

The attached external-research synthesis is a capability source, not merely background. Its
scientific mechanisms are acceptance requirements for this migration. Later user decisions replace
its obsolete operational proposals (manager-only implementation, saved permanent direction
projects, and the old roster), but do not delete the research method.

| External source / finding | Retained mechanism | Current owner and observable behavior | Explicitly not copied |
| --- | --- | --- | --- |
| OpenAI CDC prompt | preserve genuinely different approach families; keep early routes independent; reopen a blocked route only for a genuinely new mechanism; require a concrete lemma, construction, or counterexample | EM freezes a neutral common scope, chooses bounded independent approaches by information gap, withholds the current favorite before the synthesis barrier, and records whether each route produced a materially distinct mechanism or `NO_MATERIAL_INSIGHT` | 64-agent scale, fixed runtime, fixed leaf count, answer voting |
| Google AI Co-Scientist | generation → evidence → reflection → comparison → evolution | EM compares candidate mechanisms against evidence and evolves only a surviving mechanism; Portfolio receives the changed uncertainty and next decision, not a popularity score | Elo, tournament ranking, persistent hypothesis graph, LLM consensus as authority |
| Robin | hypothesis proposes an experiment; observation creates the next mechanism question or experiment | necessary EM→CM→EM observation loops occur before `SYNTHESIS_READY`; EM interprets each observation and may refine the next discriminator within the frozen bounds | Convergence before executable evidence; CM as a post-research implementation service |
| Co-STORM | actively search for unused evidence and questions not yet asked | EM/`rs` names the missing evidence or unasked question that could change the conclusion; synthesis explicitly checks whether an outlier or unused source changes the claim ceiling | adding generic experts, open-ended browsing, mandatory panel |
| POPPER | discriminator-first hypothesis testing | scope freeze states competing explanations, their differing predictions, the observation that separates them, and the outcome-to-claim/Portfolio map before CM work | treating command success, test success, or experiment completion as scientific acceptance |
| multi-agent-debate evidence | independent routes are useful only as coverage and robustness probes | EM may commission bounded heterogeneous routes, preserves a material outlier, and synthesizes without vote; same-model/source agreement is labelled coverage rather than independent evidence | persistent debate, fixed rounds/personas, agreement threshold, majority verdict |
| self-critique evidence | external feedback and executable observation outrank unaided self-correction | EM grounds revisions in primary evidence, CM observations, Pro review, or a named counterexample; `rc` is a bounded adversarial probe, not proof by introspection | recursive self-critique loop or self-declared correction as acceptance evidence |
| public research-allocation practice | apply a scientific quality floor, then allocate qualitatively across distinct risks and options | Portfolio first checks question/evidence/discriminator/failure-identifiability/claim ceiling, then compares complementarity, shared risk, action-changing value, cost/time/stage, reversibility, stop rule and option value | universal numeric score, fabricated probability, lifecycle mutation by a leaf |
| AI-assisted-science breadth finding | guard against narrowing toward data-rich or mutually dependent routes | Portfolio explicitly checks shared assumptions, common data/code/measurement dependencies, missing independent validation, and premature route homogenization before changing capacity | diversity theatre based on names or number of agents |

The retained research loop is therefore:

`Portfolio decision uncertainty → EM falsifiable question and neutral scope → independent bounded
approaches plus Pro INNOVATOR → discriminator selection → zero or more necessary EM→CM→EM
observation loops → evidence-grounded synthesis → independent Pro CONVERGENCE → EM objection
disposition → Portfolio reinvestment decision`.

There is no fixed local-leaf quota. EM chooses route families from actual independent information
gaps, prevents early favored-answer leakage across those routes, and uses a synthesis barrier before
comparison. A purely mathematical/static/evidence-interpretation cycle may omit CM only when EM
states why no executable observation is needed or available and sets the corresponding claim
ceiling. Multiple observation loops are allowed only inside the frozen round/resource/stop bounds;
a changed scientific object terminates the current cycle and requires a new one.

Research provenance: [OpenAI CDC prompt](https://cdn.openai.com/pdf/04d1d1e4-bc75-476a-97cf-49055cd98d31/cdc_prompt.pdf),
[Google AI Co-Scientist](https://www.nature.com/articles/s41586-026-10644-y),
[Robin](https://www.nature.com/articles/s41586-026-10652-y),
[Co-STORM](https://arxiv.org/abs/2408.15232),
[POPPER](https://cs.stanford.edu/people/jure/pubs/auto-hypothesis-validation-icml25.pdf),
[multi-agent debate: ICML](https://proceedings.mlr.press/v235/smit24a.html) and
[ACL](https://aclanthology.org/2024.acl-long.331/),
[LLM self-correction review](https://aclanthology.org/2024.tacl-1.78/),
[DARPA Heilmeier](https://www.darpa.mil/about/heilmeier-catechism),
[NSF merit review](https://www.nsf.gov/funding/merit-review),
[UKRI decision process](https://www.ukri.org/apply-for-funding/how-we-make-decisions/), and the
[AI-assisted-science breadth study](https://www.nature.com/articles/s41586-025-09922-y).

### 3.2 Exhaustive legacy source disposition

This inventory is the deletion audit against Git tree `832d68dc`. Every profile under
`.codex/agents/`, every role under `.agents/roles/`, every top-level skill under `.agents/skills/`,
the Agentify manual, and every workflow/control test family named in §3.3 must have one explicit
disposition and acceptance owner. Implementation repeats `git ls-tree -r --name-only 832d68dc` for
those exact roots and fails the migration audit if any source is unclassified. An unlisted old file
cannot become active by implication.

Only four disposition classes are valid: `CURRENT_MANAGER`, `THIN_LEAF`, `NATIVE_REPLACEMENT`, and
`RETIRE`. A retired identity may have a method conserved separately by a current manager; this does
not reactivate the identity.

| Exact legacy source | Disposition | Current owner / acceptance |
| --- | --- | --- |
| `hmasd-code-project-manager` identity and profile | RETIRE | no intermediate manager identity |
| Code Project Manager engineering method | CURRENT_MANAGER | top-level CM role; engineering pressure test |
| `hmasd-independent-research-explorer` identity and profile | RETIRE | no intermediate manager identity |
| Independent Explorer scientific method | CURRENT_MANAGER | top-level EM role and material-cycle pressure test |
| `hmasd-workflow-recovery-manager` identity/profile | RETIRE | no recovery manager or persistent incident plane |
| bounded recovery method | CURRENT_MANAGER | Root and affected current manager; one causal repair scenario |
| `hmasd-code-scout`, `hmasd-project-scout` | THIN_LEAF | `cs` for code surface; `gl` only for literal bounded inventory |
| `hmasd-implementer`, `hmasd-implementer-terra` | THIN_LEAF | `im`, `rt`; owned-path and no-Git tests |
| `hmasd-research-innovator`, `hmasd-research-principles-analyst` | THIN_LEAF | `ri`, `rp`; mechanism/principles pressure tests |
| `hmasd-research-scout`, `hmasd-research-critic` | THIN_LEAF | `rs`, `rc`; provenance/adversarial pressure tests |
| `hmasd-reviewer`, `hmasd-verifier`, `hmasd-experiment-operator` | THIN_LEAF | `rv`, `vf`, `op`; sandbox and bounded-effect tests |
| `hmasd-cpm-agentify-transport`, `hmasd-explorer-agentify-transport` | THIN_LEAF | `et`, `pt`; strict operation fidelity tests |
| `hmasd-cpm-mechanical`, `hmasd-explorer-mechanical`, `hmasd-luna-medium`, `hmasd-luna-xhigh` | THIN_LEAF | one `gl`; exact-output and no-owner-judgment tests |
| old `hmasd-luna-max` profile identity | RETIRE | no persistent Luna-max leaf/profile; simplicity QA is one native one-off invocation |
| `hmasd-research-artifact-writer` identity | RETIRE | no durable-writer leaf |
| durable scientific/engineering authorship method | CURRENT_MANAGER | EM/CM author durable content; `gl` may apply only exact manager-approved mechanical bytes |
| `hmasd-external-gemini-transport`, `hmasd-external-gemini` | RETIRE | no provider fallback; divergent capacity lives in `ri` and Pro Innovator |
| old `hmasd-agentify-transport` implementation/manual | RETIRE | replaced, not made compatible |
| current explicit Agentify navigation skill/reference | THIN_LEAF | `pt`/`et` use the single current strict mechanics reference |
| `docs/project/AGENTIFY_TRANSPORT_INSTRUCTIONS.md` legacy manual | RETIRE | only exact prompt ownership, strict one-send, non-sending observation, provider-visible input equality, natural-completion and full-response checks are rewritten into the compact current reference |
| `hmasd-independent-research-exploration` skill identity | RETIRE | no discoverable duplicate skill |
| its research method | CURRENT_MANAGER | EM role methods plus the external-research requirements in §3.1 |
| `hmasd-independent-research-pro-review` skill identity | RETIRE | no provider authority or separate manager skill |
| Innovator/Convergence scientific method | CURRENT_MANAGER | EM owns prompt, evidence packet and disposition; `pt` only transports |
| `hmasd-explorer-project-validation` | NATIVE_REPLACEMENT | meaning-complete EM→CM→EM WORK/RESULT |
| `hmasd-portfolio-operational-handoff` | NATIVE_REPLACEMENT | direct Portfolio→EM→CM requester chain |
| `hmasd-workflow-anomaly-routing` identity/router | RETIRE | affected action stops locally; no router |
| bounded anomaly recovery method | CURRENT_MANAGER | affected current role owns one local recovery/return decision |
| `hmasd-agile-research-development` identity | RETIRE | no duplicate session skill |
| valid native/performance/evidence method from it | CURRENT_MANAGER | EM/CM own-role method and focused tests |
| old Agentify ledger restore/result-path guard scripts | RETIRE | strict tool evidence + owner exact archive path; no local threat-model guard |
| Clerk, local task plane, envelope, registry, receipt, scheduler, dashboard, compatibility profiles/scripts/tests | RETIRE | Codex Desktop native plane and current structural negative tests |

Old algorithm/candidate tests, RNG/checkpoint/bit identity, run manifests, results, and scientific
checksums are KEEP and are outside this control-file retirement table.

### 3.3 Legacy role-document and test-family audit

The same four dispositions apply to the old role documents. The useful text is migrated by method,
not by preserving a second active role identity.

| Exact legacy role documents | Disposition | Current owner / evidence |
| --- | --- | --- |
| `ROOT.md` | CURRENT_MANAGER | current `ROOT.md`; recovery/shared-core pressure tests |
| `CODE_PROJECT_MANAGER.md` | CURRENT_MANAGER | current `CM.md`; engineering capability scenarios |
| `INDEPENDENT_RESEARCH_EXPLORER.md` | CURRENT_MANAGER | current `EM.md`; §3.1 research-loop scenarios |
| `CODE_SCOUT.md`, `PROJECT_SCOUT.md` | THIN_LEAF | current `CM_SCOUT.md`; unfamiliar-surface map scenario |
| `IMPLEMENTER.md` | THIN_LEAF | current `IMPLEMENTER.md` and `ROUTINE_IMPLEMENTER.md`; semantic-versus-routine selection scenarios |
| `RESEARCH_INNOVATOR.md`, `RESEARCH_PRINCIPLES_ANALYST.md`, `RESEARCH_SCOUT.md`, `RESEARCH_CRITIC.md` | THIN_LEAF | same-named current thin roles; route/evidence/principles/adversarial scenarios |
| `REVIEWER.md`, `VERIFIER.md`, `EXPERIMENT_OPERATOR.md` | THIN_LEAF | same-named current thin roles; bounded-effect and no-acceptance scenarios |
| `EXPLORER_AGENTIFY_TRANSPORT_OPERATOR.md`, `CPM_AGENTIFY_TRANSPORT_OPERATOR.md` | THIN_LEAF | `PRO_TRANSPORT.md`, `ENGINEERING_TRANSPORT.md`; exact-prompt/send-once scenarios |
| `EXPLORER_MECHANICAL_OPERATOR.md`, `CPM_MECHANICAL_OPERATOR.md` | THIN_LEAF | `GENERAL_LEAF.md`; bounded chore/no-owner-judgment scenarios |
| `LUNA_TASK_OPERATOR.md` identity | RETIRE | bounded chore method is already in `GENERAL_LEAF.md`; the Luna-max simplicity review is a native one-off QA invocation, not an active role |
| `RESEARCH_ARTIFACT_WRITER.md` | RETIRE | durable authorship is retained by EM; exact-byte mechanical application only through `gl` |
| `WORKFLOW_RECOVERY_MANAGER.md` | RETIRE | bounded method retained by the affected current manager; no identity/profile |
| `EXTERNAL_GEMINI_TRANSPORT_OPERATOR.md`, `EXTERNAL_PRO.md` as provider/manager identities | RETIRE | Gemini absent; Pro is external evidence reached only through owner-authored prompt plus `pt` |

Legacy control tests are evidence sources, not compatibility targets. Each family is either replaced
by a current structural/behavioral assertion or retired with the architecture it tested:

| Legacy test family | Disposition | Current evidence |
| --- | --- | --- |
| `codex_context_lifecycle/**`, `codex_semantic_mvp/**`, `codex_supervisor/**`, `hmasd_control_plane/**` | RETIRE | native task history plus negative tests proving no local plane, registry, router, receipt, scheduler or supervisor |
| `hmasd_agentify_complete_ledger_restore_test.py`, `hmasd_agentify_result_path_guard_test.py` | RETIRE | strict tool operation evidence, exact owner archive path, and trusted-local threat model; no HMASD ledger/security ceremony |
| `hmasd_cpm_mechanical*`, `hmasd_explorer_mechanical*`, `hmasd_remaining_child_context_test.py`, `hmasd_cpm_specialized_child_context_test.py` | THIN_LEAF | current caller/reference graph plus `gl/im/rt` assignment and semantic-purity pressure tests |
| `hmasd_direction_scoped_owner_contract_test.py`, `hmasd_l1_stage_pair_contract_test.py`, `hmasd_two_level_agent_topology_test.py`, `hmasd_hook_topology_test.py` | RETIRE | current depth-one native topology and caller-matrix structural tests; no L1/L2 compatibility or hooks |
| `hmasd_execution_readiness_test.py`, `hmasd_model_routing_test.py`, `hmasd_workspace_boundary_guard_test.py` | NATIVE_REPLACEMENT | current native task/worktree, exact model/profile, owned-path and one-writer-phase tests |
| `hmasd_agent_profile_benchmark_contract_test.ps1` | RETIRE | benchmark identities/profiles are retired; current exact profile/model/sandbox/reference graph has its own contract |
| `hmasd_code_project_manager_contract_test.ps1` | CURRENT_MANAGER | current CM engineering-method and capability pressure tests |
| `hmasd_experiment_operator*` | THIN_LEAF | exact-command/same-process/terminal-witness tests for `op` |
| `hmasd_independent_research_exploration_test.py`, `hmasd_research_delivery_scenarios_test.py`, `hmasd_research_portfolio_gate_test.py`, `hmasd_research_workflow_contract_test.ps1` | CURRENT_MANAGER | Portfolio/EM research-method scenarios derived from §3.1, without old packets or identities |
| `hmasd_root_exact_temp_cleanup_test.py`, `hmasd_root_managed_worktree_test.py` | NATIVE_REPLACEMENT | exact bounded cleanup and Codex native worktree tests; no permanent direction-project registry |
| `hmasd_workflow_recovery_manager_contract_test.py` | CURRENT_MANAGER | one affected-manager causal-repair scenario; no recovery-manager profile |

## 4. Final roster ownership

The implemented top-level roles, exact leaf roster, aliases, caller matrix, model/effort settings,
and exhaustive result namespaces are defined only in `AGENTS.md`; this non-authoritative migration
record deliberately does not reproduce them. The capability disposition in §3 records why every
manager and thin leaf exists.

The design decision is manager-retained judgment plus capability-driven leaves: EM retains science,
CM retains engineering acceptance and integration, Portfolio retains investment/lifecycle, and Root
retains user/shared-core control. No leaf quorum or automatic review chain exists. A nontrivial
behavior-bearing code change uses the semantic implementer even when the textual diff is small;
manager-direct edits are limited to behavior-neutral local changes. Cross-family calls and leaf
subdelegation remain prohibited by the single global caller matrix.

## 5. Meaning-first assignment and return

Every leaf assignment is a self-contained natural-language task model: intended outcome, why it
matters, concrete objects and relations, protected semantics, owned paths/Effects, local judgment,
completion evidence, and stop condition. IDs, paths, commits, fields, and commands are factual
anchors after meaning. Forked turns are background only.

Every role returns its conclusion and direct consequence before its compact owned field tail. A
field is a namespace, not a substitute for judgment. Parent alone maps a leaf observation into its
own decision. No status in one namespace can be inferred into another.

## 6. Research-side methods retained

### 6.1 EM-local material cycle

The current material cycle remains, but its detailed procedure belongs only to the EM role rather
than the global protocol:

1. EM freezes the scientific object, estimand, non-goals, current claim ceiling, strongest null and
   competing explanations, their differing predictions, the proposed discriminator, each possible
   outcome's effect on the claim and Portfolio decision, baseline/config/data/RNG boundaries,
   maximum observation rounds or resource bound, early stop, and scope-invalidation condition; it
   then opens `SCOPE_FROZEN`.
2. EM gives every early route the same neutral grounding while withholding its favored answer. It
   selects bounded, genuinely different approach families from the actual information gaps—for
   example mechanism-, counterexample-, comparator-, measurement-, or principles-first—and may use
   `ri`, `rp`, `rs`, or its own direct analysis. Routes do not see one another before the synthesis
   barrier and may explicitly return `NO_MATERIAL_INSIGHT`.
3. EM writes the full natural-language Pro Innovator prompt from that neutral scope. A fresh `pt`
   performs exactly one strict Innovator operation while independent local work may run.
4. EM compares mechanisms, preserves a material outlier, checks for unused evidence and unasked
   questions, and chooses the smallest answer-changing discriminator. Same-model/source agreement
   is coverage, not independent evidence.
5. If executable evidence is needed, EM sends a meaning-complete native WORK to CM. CM returns the
   direct observation, artifacts, technical scope and limitations without scientific acceptance;
   EM interprets the outcome against the competing predictions. A bounded next observation may be
   requested only when it follows from that result and remains inside the frozen round/resource/stop
   bounds. A changed scientific object ends the cycle instead of silently rewriting its scope.
6. Only after all necessary CM observations and EM interpretations—or an explicit static/theoretical
   sufficiency reason with a finite claim ceiling—EM writes `SYNTHESIS_READY`. It authors a separate
   Convergence prompt from the current evidence packet without the Innovator transcript, and a fresh
   `pt` sends it once.
7. EM dispositions each Convergence objection against evidence, optionally uses `rc` for one named
   unresolved material issue, writes `REVIEW_RESOLVED`, then `HANDOFF_READY` and returns Portfolio.

Milestone snapshots remain milestone-only anti-compression memory. They do not authenticate,
release a task, route a message, or record every event.

The preceding procedure is written only to `EM.md`. The EM sees Portfolio's adjacent WORK input and
must return the required decision-impact interface, but it does not read or reproduce Portfolio's
internal allocation method.

### 6.2 Portfolio-local allocation method

Portfolio consumes that return as a change in decision uncertainty. It first applies the scientific
quality floor (clear question, traceable evidence, action-changing discriminator, identifiable
negative result, bounded claim), then compares shared assumptions and dependencies,
complementarity/substitution, expected decision change, cost/time/stage, reversibility, stop rule,
option value and availability of a relatively independent validation route. It does not collapse
these judgments into Elo, a universal score, a vote or a fabricated success probability.

This paragraph is written only to `PORTFOLIO.md`. Portfolio receives EM's adjacent RESULT but does
not read or reproduce EM's material-cycle procedure.

For `FUSE`, Portfolio first creates a new scientific synthesis question, states why the source
directions are complementary rather than merely similar, and gives every source direction its own
explicit lifecycle disposition; any shared-core engineering need is a separate Root WORK. It does
not merge source code or silently collapse source authorities. For `SPINOFF`, Portfolio first
registers the new direction and its scientific boundary, then creates a new current-protocol EM task;
it does not insert the new question into an existing direction's authority. These methods live only
in `PORTFOLIO.md` and receive focused behavior scenarios.

## 7. Minimal strict Agentify boundary

EM or CM writes the complete cohesive natural-language prompt to the exact frozen file. The prompt
contains the scientific/engineering question and only necessary GitHub remote, reachable commit,
repository-relative refs, context, requested analysis, and limits. Repository code is evidence for
the research mechanism, not a request for general code review.

The transport leaf does not compose, summarize, append, truncate, or rewrite the prompt. Its role
invokes one explicit transport skill; that skill navigates to the one compact mechanics reference,
which calls the strict file-backed
`agentify_review_query` once with `promptPath`. Tool-required idempotency/stable keys or content hash
remain tool-local call parameters; they are not written into HMASD workflow authority, state, or a
new ledger. Ordinary `agentify_query` is not the review send path.

After the send-capable call, only the same operation is observed through non-sending strict observe
or `verifyExisting` behavior. `AGENTS.md` is the sole human-readable owner of the exhaustive
transport states and their cross-namespace consequences; this plan does not restate that glossary.
A provider-visible input mismatch remains a terminal fact for that operation and supplies no
scientific, engineering, Portfolio, lifecycle, or cancellation conclusion.

An unknown or sent owner-frozen request cannot be made fresh by changing WORK, leaf, label, key,
conversation, task, or cycle. Another send requires strict zero-send proof or a materially different
owner-authored question. Native history and the prompt provide this continuity; no local ledger or
workflow identity is added.

The strict tool's own immutable operation key, stable binding, prompt SHA, provider-visible turn,
model evidence, natural-completion evidence, and operation observation are the source of fidelity
facts. They remain inside that tool call/result and are not copied into HMASD authority or a local
ledger. The archive path must be the exact direction/assignment path supplied by the owner; under
the trusted local threat model HMASD does not restore a separate symlink/reparse/result-path security
guard. No local prompt SHA ceremony, receipt, ledger, retry counter, duplicate file confirmation,
fixed tab recipe, or giant legacy manual is restored.

## 8. State, Git, and native task boundaries

- Keep one EM and one CM current milestone snapshot with timestamp/revision for compression recovery.
  `hmasd_state.py` and schemas validate owned fields and impossible semantic transitions only; they
  never block native routing or act as task admission, authentication, approval, attempt ledger, or
  event database. This bounded transition validation is retained because the user requires both
  milestone memory and exhaustive status meaning.
- Add `SENT_INPUT_MISMATCH` consistently to global meanings, EM state schema, transitions, unresolved
  operation handling, and tests.
- Keep Root on the primary `main` checkout. Portfolio/EM/CM tasks use Codex native
  `environment: worktree` from the saved HMASD project; no direction project, local mapping, or
  permanent sibling registry is required.
- Preserve the one-direction one-writer phase and exact Git fast-forward handoff. Git commit identity
  is version control, not session authentication.
- Verifier may write only the assignment proof root under `temp/`; implementers may write only exact
  owned paths. Leaves never commit/push.

## 9. Files to change

1. Public/current authority: `AGENTS.md`, `docs/project/WORKFLOW_PROTOCOL.md`, and the stale native
   worktree wording in `docs/research/portfolio/PORTFOLIO.md`.
2. Role layer: track `.agents/roles/*.md`; complete all manager/specialist methods without copying
   global topology or another role's fields.
3. Skills: first run the RED pressure scenarios below, then reduce the four session skills to trigger
   + own role pointer + exact reading route; add one explicit-only `hmasd-agentify-transport` skill
   that only navigates to one compact mechanics reference, following `superpowers:writing-skills`.
4. Profiles/config: retain current nine, add `ri/rp/im/rt`, make every profile a thin own-role
   pointer, and give Verifier bounded workspace write.
5. State: update `hmasd_state.py`, research schema, and focused transition tests, including terminal
   mismatch versus unresolved sent states.
6. Active project guidance: repair stale/dead references in algorithm/efficiency/project-map docs
   only where they affect current role capability. Do not rewrite historical evidence or scientific
   checksums.
7. Tests: replace fragile wording markers with structural ownership, reference graph, forbidden
   cross-role references, state behavior, sandbox, strict-send, and native-worktree assertions.
   Bind CM capability to resource/memory preflight, native C++ batching, FP32/MARL sanity, exact run
   manifest/checkpoint/result semantics, question-relevant-output failure classification, and one
   hypothesis-driven unchanged-science repair.

Before editing any skill, preserve the observed RED evidence from the contaminated pilot and run at
least these five pressure scenarios without the restored skill/method:

1. transport composes or truncates an EM prompt instead of sending exact bytes;
2. transport chooses ordinary `agentify_query` instead of strict review;
3. an unknown/sent operation is rationalized into another send;
4. a leaf actively reads the full protocol or another role document, copies unrelated topology or
   procedure into its task/return, or emits another owner's field;
5. CM retains a nontrivial implementation and loses integration attention instead of using the
   correct implementer.

For each scenario, first run a no-guidance baseline and preserve the exact output and any verbatim
rationalization that demonstrates the failure. After adding the minimum skill/role guidance, run at
least five fresh-context repetitions of the same scenario. Record a compact scenario table containing
baseline failure, added guidance, expected behavior, repetitions, observed behavior, rationalization
or red flag, and disposition. A GREEN assertion must inspect behavior and the absence of forbidden
rationalization, not merely the presence of preferred wording. Then remove duplicated instructions,
rerun the full scenario set after that refactor, and add at least five fresh micro-tests for obvious
bypass wording. This follows `superpowers:writing-skills` as instruction TDD; the evidence is one-time
migration QA, not a runtime approval layer or permanent log database.

The read-only historical replay against `b4762febd12b62748d35e2b1a1dffdfb8d776180` did not fabricate
five failures. Exact prompt fidelity was RED and had direct contaminated-pilot evidence: the
provider-visible request contained a shell-result wrapper and mojibake rather than the owner text.
Mandatory material-cycle Innovator was also RED: the old EM protocol described it as optional and
the transport said only `at most once`, so either layer could legally skip it. Convergence was
mandatory except for the user-waived exact unsent operation or a transport terminal exception.
Ordinary
`agentify_query` was the old contract rather than an accidental violation, so moving to strict
review is a target design upgrade that closes the fidelity defect. Unknown/sent no-resend and leaf
namespace isolation were already present and were retained. Manager-direct CM
implementation was also the then-current design; restoring thin implementers is the later
user-authorized capacity correction, not a retroactive claim that the old instructions contradicted
themselves.

### 9.1 Research-method behavior acceptance

The external-research mechanisms in §3.1 receive behavior checks rather than keyword-only tests:

| Mechanism | Required observable scenario |
| --- | --- |
| CDC route independence | two bounded early approaches receive the same neutral scope but neither the favored route nor the other's output; synthesis distinguishes their causal families, and a blocked route is reopened only by a named new mechanism |
| concrete constructive progress | a route must return a concrete lemma/construction/counterexample/prediction or `NO_MATERIAL_INSIGHT`; a catalogue of fashionable modules cannot satisfy the assignment |
| generation/evidence/reflection/comparison/evolution | EM compares at least two live explanations against evidence, retires or narrows one, and evolves only the supported survivor without Elo, vote or persistent hypothesis graph |
| unused evidence/unasked question | EM or `rs` identifies one previously unused source or unasked answer-changing question and records whether it changes the discriminator or claim ceiling |
| discriminator-first | competing predictions and outcome-to-claim/Portfolio map exist before any CM WORK; command/test success alone cannot produce scientific acceptance |
| experiment-feedback loop | at least one real pilot direction completes an executable discriminator through EM→CM→EM before `SYNTHESIS_READY`; a negative or ambiguous direct observation causes an explicit EM claim/next-question revision and an explicit Portfolio reinvestment consequence |
| debate/self-critique limits | same-model/source agreement is labelled search coverage, a material outlier is preserved through synthesis, and any claim correction cites external evidence, executable observation, Pro objection or concrete counterexample |
| Portfolio quality/allocation | Portfolio applies the quality floor before qualitative comparison of complementarity, shared risk, action-changing value, cost/time/stage, reversibility, stop rule, option value and independent validation; no universal score/probability/vote appears |
| anti-homogenization | a comparison with shared data/code/measurement assumptions identifies the dependence and retains or seeks a relatively independent validation route rather than counting renamed agents/directions as diversity |
| FUSE/SPINOFF | FUSE creates a new synthesis question plus per-source lifecycle dispositions and routes shared-core work to Root; SPINOFF registers a new bounded direction before creating its EM |

A unit or prompt test may establish local instruction behavior, but the real two-direction pilot is
the acceptance test for the observation-feedback and Portfolio reinvestment row. Both pilot
directions may not bypass CM as “static”; at least one must exercise that full loop. The other may be
static/theoretical only with a written sufficiency reason and bounded claim ceiling.

## 10. Review and rollout

This plan must converge under three independent reviews before implementation:

- functional completeness against the capability matrix;
- simplicity under the trusted local Codex Desktop threat model, performed by a one-off
  `gpt-5.6-luna` / `max` reviewer;
- semantic purity of AGENTS/protocol/skill/profile/role ownership.

After implementation, the same three reviews run again against actual files and tests. Blocking
findings are fixed and the relevant review repeats until all three are clear. This two-stage review
is a one-time migration QA process explicitly required by the user, not a permanent workflow gate,
role authority, or general approval panel. Reviewers may advise; the Root dispositions findings
against user authority and records rejected findings with reasons. The Luna-max reviewer is a
one-off review invocation, not a fourteenth active profile, role, or persistent state.

Only then:

1. run all current workflow/config/state/run contracts and focused leaf pressure tests;
2. audit the paused contaminated pilot without treating invalid transport as science or lifecycle;
3. close that pilot through the existing requester chain without inventing cancellation;
4. start a fresh two-direction pilot using new current-protocol tasks and exact native worktrees;
5. require at least one pilot direction to complete a real discriminator through EM→CM→EM with a
   negative or ambiguous observation that visibly revises the EM claim/next question and Portfolio
   reinvestment judgment; the second may omit CM only under the explicit static-evidence rule;
6. restore four-direction mode only after both directions finish their valid complete cycles and
   Portfolio audits the round and all §9.1 acceptance rows clean.

## 11. Implementation QA record

This is a compact one-time migration record, not a runtime gate or event log.

- Backup: all pre-change active control files, plus the retired host-compat script/test, are under
  `C:/Projects/workflow backup/HMASD-control-pre-capability-restoration-20260828` and are not active
  discovery input.
- Legacy disposition: read-only `git ls-tree -r --name-only 832d68dc` found 23 profiles, 23 role
  documents, nine top-level skills, and one Agentify manual (56 core sources). Every source and every
  workflow/control test family named in §3.3 has an explicit disposition; none is unclassified.
  This audit does not create a compatibility test or runtime dependency on the old tree.
- Instruction baseline: exact owner-prompt fidelity and mandatory material-cycle Innovator were
  RED; the other scenarios were classified as retained capability or deliberate target-design
  changes as explained above.
- Instruction GREEN: five independent fresh-context Reviewer repetitions each rejected prompt
  rewriting/truncation, ordinary-query substitution, relabelled resend, cross-role field/method
  leakage, and CM direct handling of a nontrivial RNG/checkpoint/recurrent edit. Intermediate
  rationalization findings were fixed and the affected reviewer reran to `NO_FINDINGS`.
- Semantic-purity pressure: a separate fresh-context review found and then cleared duplicate
  `COMPLETE` prose, over-broad adjacent-section routing, and ambiguous EM leaf-null wording.
- Post-implementation reviews: functional completeness `NO_FINDINGS`; trusted-local simplicity by
  one-off `gpt-5.6-luna`/`max` `NO_FINDINGS`; semantic purity `NO_FINDINGS`.
- OAI-backed liveness review: an independent Reviewer read the official Subagents and Long-running
  work documentation, found terminal snapshots that could coexist with unresolved provider/process
  Effects plus a schema-only WAITING reentry gap, and verified the repaired validator/schema/role
  contracts as `NO_FINDINGS`. Terminal snapshots are now absorbing except for a native-history
  successor entering a fresh research cycle or engineering scope; no task ID, ledger, scheduler,
  heartbeat, or retry controller was added.
- Verification: five current skills pass the official quick validator; focused
  workflow/config/role/state contracts pass 86 tests; the expanded current `hmasd_*` plus Codex
  config suite passes 159 tests with two expected skips; `git diff --check` reports no whitespace
  errors.

The remaining acceptance evidence is rollout evidence, not repository implementation: audit and
close the contaminated paused pilot without scientific/lifecycle inference, run a fresh valid
two-direction round including one real negative or ambiguous EM→CM→EM observation loop, and only
then authorize four-direction mode.
