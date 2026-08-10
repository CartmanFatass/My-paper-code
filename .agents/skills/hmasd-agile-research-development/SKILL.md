---
name: hmasd-agile-research-development
description: Use when implementing, debugging, refactoring, or validating exploratory HMASD algorithm code, prototypes, runners, analyzers, or operational repairs.
---

# HMASD Agile Research Development

## Contract boundary

Read the root router, the role contract, and brief. This procedure grants no
science, formal compute, transport, or acceptance authority. External Pro owns
scientific decisions. Code Project Manager alone accepts code, coordinates the
project, directs engineering repair, and owns runtime, transport and Git
integration. A bounded child requires an exact
assignment and never scopes, accepts, or commits its work.

```text
superpowers_plugin=reference_only
superpowers_execution=disabled
development_mode=agile_algorithm_research
backward_compatibility=not_required
test_scope=proof_sized
search_complexity_ceiling=O(H*K_search)
candidate_trajectory_count_ceiling=16
future_simulated_transitions_per_controller_episode<=16*H
nested_rollout_replanning=forbidden
nonformal_wall_clock_cap_minutes=20
formal_iteration_wall_clock_cap_hours=8
scalable_algorithm_target=O(N*k_neighbor)_or_O(N*logN)
codebase_policy=architecture_first_module_boundaries
workflow_hash_validation=disabled
per_file_hash_handoff=forbidden
test_acceptance_basis=risk_and_claim_coverage
line_coverage_target=none
test_count_target=none
cpm_performance_scoring_from_tests=forbidden
formal_result_snapshot_oracle=forbidden
direction_local_test_lifetime=active_implementation_only
shared_defect_regression_promotion=plausible_recurrence_only
mechanical_operation_state_owner=originating_tool_or_script
model_authored_operation_state_machine=forbidden
cpm_decision_surface=semantic_next_action_only
local_failure_default=continue_next_legal_action
research_stage=EXPLORATION|FORMALIZATION
default_research_stage=EXPLORATION
code_change_shape=coherent_module_responsibility_with_focused_evidence
successor_replaces_predecessor=same_commit_delete_code_runner_direction_test
shared_abstraction_justification=ownership_or_multiple_live_callers
versioned_scientific_filenames=forbidden_git_is_history
```

The upstream `using-superpowers` rule yields to user and `AGENTS.md`; the markers
above explicitly disable it. Never invoke or chain generic Superpowers Skills.
A user-named one may be inspected only as reference.

## Triggered transport and mechanical lanes

Formal and Explorer-to-project review transport remains a file-only handoff
through the registered `hmasd-agentify-transport` child. When a review trigger
fires, CPM freezes the questions, preserves their conversation meaning and
consumes the named result only after the child's terminal return. The Agentify
`.agents/roles/AGENTIFY_TRANSPORT_OPERATOR.md` and
`.agents/skills/hmasd-agentify-transport/SKILL.md` own the
`AGENTIFY_REVIEW_BATCH_ASSIGNMENT` contract and all page/provider/wait,
recovery and tab mechanics.

CPM owns the per-question conversation intent. Its context brief states clean
start versus one exact continuation URL, permitted concurrency versus required
independence, and whether prior memory helps or contaminates later reuse. The
transmitted question contains no local filesystem path, task history or
unrelated corpus; reviewer-facing source locators use the public remote URL.

For deterministic inspection, result extraction, handoff preparation or ticket
preparation, CPM may trigger `hmasd-cpm-mechanical`;
`.agents/roles/CPM_MECHANICAL_OPERATOR.md` and its dispatcher own the
mechanical result fields and bounded observation recovery. For an authorized
experiment, `.agents/roles/EXPERIMENT_OPERATOR.md` and
`scripts/hmasd_experiment_operator_receipt.py` own `train -> evaluate ->
analyze` and its terminal receipt. This Skill does not reproduce those lanes;
CPM remains the orchestrator, assignment author and sole technical/mechanical
acceptance owner.

## Action-bearing Explorer↔CPM interface

Use `docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md` as the single
detailed source. CPM consumes and returns action-bearing prose; it never infers
an action from a status-only token. `parked` is Explorer-local when no frozen
live successor exists, while ordinary engineering gaps go to CPM. A missing or
contradictory meaning preserves the original, asks one exact clarification and
continues unrelated work.

The normal runtime path remains the existing
`runtime_capacity_pool_units=3`,
`independent_admitted_treatment_execution=parallel_first_within_capacity`, and
`runtime_admission_judgment=admit|up-class|pending_runtime_capacity` contract
in the parallel-research reference; event-driven continuation has no
clock-driven scheduler or polling.
CPM maintains its owner-local view at
`docs/project/current-work/common/explorer_project_validation.md`; the view is
not a second semantic source.

## Operating loop

1. **Align.** For conclusion-bearing work, require an exact Pro scientific
   disposition and its design-audit status. Before implementation Code Project Manager performs
   only a local feasibility read. It returns a concrete ambiguity,
   impossibility or counterexample for one focused Pro clarification; there is
   no routine pre-implementation review.
   Pure operational work records why the audit is not triggered.
2. **Bound.** Use the brief and
   `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`. Code Project Manager defines code
   files, engineering choices, exclusions and completion inside the Pro-frozen
   semantics. Before implementation, write the zero-compute `H`, fixed
   `K_search`, hypothetical-transition bound and projected wall clock. Add no
   brainstorm, plan, worktree, ledger or approval when known.
3. **Probe.** Observe the smallest failing test for new behavior or plausible
   regression. For throwaway measurement/configuration, use a diagnostic.
4. **Implement.** No backward compatibility. Make the smallest coherent module
   change; remove replaced interfaces, adapters, migrations, fallbacks, state,
   and tests. Git history is the archive. Use one stable semantic module, not a
   new generation-number copy. A successor deletes predecessor code, runner and
   direction-local test in the same change.
5. **Verify.** Proof proportional to the claim: rerun the focused check fresh.
   For result-bearing runner/analyzer integration, execution-entry, artifact,
   serialization or phase-connection changes, and code defects exposed by
   preflight, focused tests alone are insufficient. Run the two-layer
    triggered execution-readiness lane. Use a broad suite only for a changed
   shared surface.
6. **Inspect and report.** Check protected semantics, RNG/replay/lifecycle,
   serialization, transfers, synchronization, packing, persistence, and serial
   evaluation. Report commands, results, limits, and files. For new or materially
   changed claim-bearing code, Code Project Manager writes the commit-bound
   critical-point index, pushes the accepted implementation and routes the one
   comparison-only `CODE_SCIENCE_ALIGNMENT_AUDIT` through the registered
   Agentify Transport Operator before a formal run. The audit may identify a
   concrete contract mismatch but cannot
   design an algorithm, controller, solver or new evidence search.

## Active module boundary

The default active architecture is `source -> controller -> episode -> metrics
-> analysis`. Optional formalization consumes frozen core outputs and never
feeds back into the core. Runners contain configuration and wiring only. A
module has one state owner or responsibility; do not mix environment dynamics,
policy decisions, metrics and artifact I/O. Keep public interfaces minimal,
dependencies directed, and complexity isolated. Extract shared code when it
improves ownership or serves multiple live callers.

## Project cognition references

For a new persistent coding task, or when Code Project Manager clearly lacks the
project mental model, read the reusable
`.agents/skills/hmasd-writing-agent-assignments/references/project-cognition-bootstrap-prompt.md`
once alongside the normally routed documents. It is a cognitive reference, not
an authority source; never copied to each child assignment or loaded on every
round.

Use context depth deliberately rather than mechanically:

- Local tasks remain local and do not load `docs/project/PROJECT_MAP.md`.
- Coupled tasks read only the relevant project-map and
  `references/code-context-guide.md` sections, then the direct responsibility
  owner, producers, consumers and focused contract evidence.
- Load-bearing tasks read only the relevant map/context sections plus the exact
  assignment-named design, runtime boundary and claim evidence; existing
  readiness and review triggers still decide those actions.

When compiling a child assignment, use the
`hmasd-writing-agent-assignments` Skill and its optional
`.agents/skills/hmasd-writing-agent-assignments/references/assignment-brief-examples.md`
as a natural-language aid. The parent sends a shorter self-contained brief;
forked turns are background context and never replace it. The Skill and its
references are judgment aids, not schemas or admission gates, and they do not
define mandatory fields.

Evaluate each change by coherent module responsibility, minimal public
interfaces, directed dependencies, explicit state ownership, complexity
isolation, change locality, preserved behavior and focused evidence. Line and
file statistics are optional diagnostics only: they cannot reject work, force
arbitrary slicing or substitute for architecture review. These criteria prevent
another full `Gxx` copy without requiring artificial file splitting when one
responsibility is genuinely inseparable.

## Proof-sized test selection

Choose the smallest evidence class that exposes the changed risk; these classes
are alternatives selected by the task, not four mandatory gates:

| Changed risk | Smallest evidence | Lifetime |
|---|---|---|
| stable shared interface, schema, seed, backend or serialization contract | focused contract or durable regression | persistent while the shared surface remains |
| claim-bearing mechanism | one focused test of the `CODE_SCIENCE_INDEX.md` observable invariant | while the claim-bearing implementation remains active |
| production entry, runner phase connection or artifact lifecycle | focused evidence plus the triggered execution-readiness phases | candidate-bound receipt |
| direction-local prototype or throwaway measurement | local focused test or diagnostic | delete with the abandoned implementation |

Code Project Manager selects the evidence class, states the observable invariant
and owns acceptance. The implementer normally owns the assigned code and its
corresponding focused test together. For an ordinary risky cross-file or RNG
change that does not trigger execution readiness, verifier use remains optional.
When runner, execution-entry, serialization, phase-connection or artifact risk
triggers execution readiness, the registered verifier is the required mechanical
executor on the clean candidate commit. This is not a routine gate for ordinary
code changes and creates no second acceptance owner.

Assignments are natural-language contracts: they explain outcome, intent,
protected semantics, local judgment and completion. Suggested fields are aids
for intelligent model context, not rigid schemas or admission gates. Code
implementers run with `fork_turns=3`; code reviewers with `fork_turns=none`; the
readiness verifier with `fork_turns=1` only when the existing readiness trigger
fires. Forked turns are background context and never replace the assignment.

Select an oracle in this order when applicable: a hand-checkable exact case; a
structural invariant or metamorphic relation; a differential comparison with a
small simple reference; boundary and fail-closed behavior; then a deterministic
seeded statistical band only when no cheaper relation tests the claim. A focused
test should reject one plausible wrong implementation. Do not freeze a formal
research outcome as an implementation oracle or use test count, line coverage
or suite pass rate to score Code Project Manager performance or establish
scientific truth.

Promote a direction-local failure to a persistent regression only when the
defect can recur on a remaining shared surface. Otherwise remove its code and
test together when the direction leaves the active line; Git retains the
history. Run a broad suite only for an actually changed shared surface.

## Triggered execution-readiness lane

When result-bearing runner/analyzer integration, execution-entry, artifact,
serialization or phase-connection risk (or a preflight-exposed code defect)
triggers readiness, CPM dispatches the registered `hmasd-verifier` on the clean
candidate commit. Candidate-focused checks remain separate; `.agents/roles/VERIFIER.md`
and `.agents/skills/hmasd-agile-research-development/scripts/hmasd_execution_readiness.py`
own the ordered six phases, process
observation, candidate/exercise-root binding and Git-private receipt
finalization. The dedicated owner preserves the `formal=false`, zero-compute
boundary and distinguishes invocation failure, first causal phase failure and
finalization failure.

CPM supplies the exact commands and phase semantics, consumes the typed receipt
and alone accepts or repairs the candidate. Readiness is not a routine gate for
ordinary code changes. A timeout or technical failure is candidate evidence,
does not authorize replay or weakened checks, and consumes no scientific
iteration; recovery and any fresh candidate remain within the Verifier Role and
Code Project Manager failure-containment contracts.

## Complexity gate

HMASD tests Pro-proposed ideas; it does not implement unlimited solvers. Search
introduced only for evidence must be at most `O(H*K_search)` with fixed
`K_search<=16` and no more than `16*H` hypothetical transitions per controller
episode. Nested remaining-horizon rollout at every real step, recursive rollout
inside a candidate rollout, tree/beam/MCTS search and horizon-growing candidate
sets are forbidden regardless of C++ speed or parallel hardware. A nonformal
exercise is capped at 20 minutes and a formal iteration at eight cumulative
hours. Exceeding the bound returns `NON_EXECUTABLE_EVIDENCE_DESIGN` to Code Project Manager, which
first chooses a cheaper technical realization of the same frozen scientific
predicate. Pro is asked only when the predicate itself cannot survive the
bound, and is never asked to design a solver. No conclusion-bearing iteration
is consumed.

Do not confuse evidence-search complexity with simulator physics. C++ and
batching remain preferred for a valid fixed-small-N exact reference. A
deployment algorithm claimed to scale with dynamic agent count must target
`O(N*k_neighbor)`, `k_neighbor<=16`, or `O(N*logN)` rather than add a dense
pairwise path. Any sparse or approximate physical model is a new scientific
choice and requires its own design audit.

Router, role, Skill, native-profile, registry and active workflow-contract
changes belong to Workflow Design Manager under `hmasd-workflow-change-audit`. This
Skill remains Code Project Manager's implementation loop for any separately assigned source-code
slice.

## Concurrency and review

- One writer owns each file; disjoint paths may run in parallel. No global lease.
- Explorer-origin result-bearing treatments use the three-unit capacity,
  admission, barrier and resource contract defined only by
  `.agents/skills/hmasd-independent-research-exploration/references/parallel-research-workflow.md`.
  CPM is the operational owner and makes a stateless per-admission judgment of
  `admit`, `up-class` or `pending_runtime_capacity`; this Skill adds no second
  capacity procedure. Capacity deferral applies only to a not-yet-started
  treatment and never creates `BLOCKED`. The scientific A/B/C evidence level is
  independent of runtime class; CPM never infers class or barrier from science
  or `local_research/`.
- Once Explorer has selected and frozen independent direction treatments and CPM
  has admitted isolated tickets/worktrees within the three-unit pool, the normal
  execution path remains
  `independent_admitted_treatment_execution=parallel_first_within_capacity`.
  Serialization exceptions, heavy-pool exclusivity and event-driven Explorer
  continuation are defined by the parallel-research workflow reference. CPM
  treatment dispatch is constrained only by an exact scientific/dependency
  predecessor, capacity/admission, a formal or actually observed resource
  conflict, or a same mutable-path/object conflict. Read-only Explorer science
  lanes remain independent of CPM pool/admission by default; only an exact
  question depending on an unreturned CPM result creates a direction-local
  science barrier. All non-experiment work that does not contend for the
  observed bottleneck continues; one command contending for that same actual
  resource may be delayed without `BLOCKED`.
- Concurrent-treatment identity, isolated roots, shared-mutable-state rejection,
  failure containment and one-acceptance-per-result remain required as defined by
  the parallel-research workflow reference; this Skill does not duplicate those
  resource and barrier mechanics.
- Before a result-bearing full starts, CPM may issue at most one engineering
  recovery that preserves all scientific literals. A light treatment is one-full,
  no sweep and no implicit retry. Once the full starts, CPM returns its terminal
  outcome without silently replaying it; any later full is a newly authorized
  treatment decision rather than operational recovery.
- Isolated worktrees use `scripts/hmasd_workspace_ticket.py provision`. Code
  Project Manager supplies the main checkout, exact base commit, assignment and
  allowed paths; the command creates both the worktree beneath
  `C:/worktrees/HMASD` and its Git-private ticket. Raw external `git worktree`,
  `subst` and path-alias setup are forbidden. The child resolves the ticket
  before editing, and Code Project Manager verifies it after return. Never
  transcribe, infer or repair an absolute worktree path in prose.
- Registered provision uses command-local `core.longpaths=true` without changing
  repository or global Git configuration. A workflow-frozen replacement
  assignment may name one earlier unticketed partial assignment with
  `--recover-partial-assignment`. An already-clean state with no ticket,
  destination or Git registration is an idempotent `PARTIAL_WORKSPACE_CLEANED`;
  otherwise the script removes only the exact registered state, verifies its
  absence, then provisions the new assignment. It fails closed on an existing
  ticket, an unregistered destination, a redirected path, identity mismatch or
  incomplete cleanup. Callers never run raw `worktree remove` or `worktree
  prune`, manually delete the path, or reuse the retired assignment.
- Children do not perform Git or acceptance. Code Project Manager reads the
  file-backed terminal mechanical receipt/result and, after acceptance,
  integrates the exact accepted file set directly with ticket
  `finalize-integrate`; this local receipt is evidence only and never delegates
  acceptance.
- Do not compute per-file hashes for handoff. Exact paths, the staged path set,
  and the resulting Git commit are sufficient code identity.
- Subtasks close on evidence plus one fresh Code Project Manager check. After
  Code Project Manager integrates a coherent group of implementer changes, one
  independent reviewer by default examines the complete integrated diff. Parallel
  reviewers are allowed only for genuinely independent review questions, and
  each may read the whole diff. Never review once per implementer and do not
  create an automatic re-review loop. The required Pro code-science audit occurs
  once after Code Project Manager implementation acceptance; it is a contract
  diff and owns scientific alignment, not code acceptance or implementation
  design. Verifier dispatch remains conditional on the existing readiness
  trigger.

## Quick reference

| Change | Smallest sufficient evidence |
|---|---|
| helper or schema | one focused check |
| bug or invariant repair | reproduction, regression if durable, focused rerun |
| runner interface or projection wiring | focused check plus production-entry interface smoke |
| result-bearing runner/analyzer or artifact lifecycle | focused evidence plus all six execution-readiness phases |
| preflight-exposed code repair | reproduction, durable regression and all six execution-readiness phases |
| protected cross-file path | frozen contract, focused evidence, optional one review |

## Stop only for a real boundary

```text
valid_result_dispositions=CONTINUE|CLOSE_NO_EXECUTABLE_CANDIDATE|COMPLETE_BALANCE_EXHAUSTED
valid_result_disposition_precedence=balance_exhausted_then_no_executable_candidate_then_continue
scheduled_action_presence=CONTINUE_only
missing_scheduled_action_clarification=remaining_balance_and_possible_candidate_only
operational_recovery=automatic_within_unchanged_authorized_boundary
operational_recovery_scientific_iteration_cost=zero
early_termination_boundary=unrecoverable_external_technical_impossibility_only
```

Code Project Manager consumes tool-owned terminal evidence. Inside
the active authorized nine-valid-iteration grant, do not stop for user
input, a permission prompt, a scientific result or protected-science ambiguity.
Archive every valid success, failure, mixed or
underpowered result and return it to External Pro. Pro maintains multiple live
or parked directions when evidence supports them. Pro returns
`COMPLETE_BALANCE_EXHAUSTED` when all nine valid iterations are consumed;
otherwise it returns `CLOSE_NO_EXECUTABLE_CANDIDATE` only when the full preserved
portfolio has no executable in-scope candidate, or `CONTINUE` with one current
resource-consuming action per formal nine-valid-iteration turn (one new action
per turn). That formal nine-valid-iteration/one-new-action-per-turn lane's
scheduling boundary provides attribution and does not establish scientific
uniqueness; it is never an ordinary A/B global serial lock. Code Project
Manager executes only the designated `CONTINUE` action and never reorders or
compresses the portfolio. While balance
remains, an absent or ambiguous action with a possible in-scope candidate causes
automatic focused Pro clarification. Terminate earlier only for an unrecoverable
external technical impossibility after applicable automatic recovery cannot
make progress, and report it as a technical blocker rather than a permission
question.

## Common mistakes

| Mistake | Correction |
|---|---|
| preserve compatibility “just in case” | delete the superseded path |
| equate quality with coverage or a full suite | test the actual claim |
| follow a generic Skill's worktree/review/commit ritual | use this procedure only |
| turn file hashes into a handoff or approval gate | use exact paths and Git identity |
| ask again inside an active grant | continue unattended to Pro adjudication, balance exhaustion or terminal closure |
| pause after an unfavorable result | archive it and follow the Pro continuation or terminal disposition |
| propose external authority while an in-scope route exists | defer it and continue the in-scope route |
| optimize an asymptotically forbidden evidence search | return it to Pro for a bounded discriminator |
