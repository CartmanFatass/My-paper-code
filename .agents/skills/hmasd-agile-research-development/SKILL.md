---
name: hmasd-agile-research-development
description: Use when implementing, debugging, refactoring, or validating exploratory HMASD algorithm code, prototypes, runners, analyzers, or operational repairs.
---

# HMASD Agile Research Development

## Contract boundary

Read the root router, the role contract, and exact Root/CPM assignment brief. This procedure grants no
science, formal compute, transport, or acceptance authority. External Pro owns
scientific decisions. Code Project Manager alone accepts code, coordinates one
exact `direction:<id>|shared:<component>` scope, directs engineering repair,
and makes scope-local technical and runtime judgments. Each scope atom matches
`[a-z0-9][a-z0-9._-]{0,63}`; empty values, path separators, extra colons,
whitespace and `..` are invalid. Root owns agent lifecycle, cross-owner relay, physical
canonical writes, managed-worktree lifecycle and Git mechanics. Costly runtime
requires an explicit user task routed through Root. A bounded child requires an
exact assignment and never scopes, accepts, or commits its work.

This Skill is action-triggered context, not CPM default startup context: load it
only for an assignment-named implementation, debugging, refactoring or
validation action. For such an action, apply the Root-managed tracked-write
worktree contract in
`docs/session-workspaces/code_project_manager/README.md` before writing tracked
paths or mixed tracked/ignored output; read-only, ignored-only and
temporary-only work is exempt. One writable L1 assignment uses one Root-managed
worktree. Parallel L2 tracked writers with the same frozen base and
exact disjoint paths share that worktree; Root waits for them and creates one
slice candidate from their union. Different CPM assignments use independent
worktrees and integration uses a separate worktree. This physical resource is
not identity, authority or runtime authorization. L2 children never
create/manage worktrees or use raw child worktree commands.

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
replacement_replaces_predecessor=same_commit_delete_code_runner_direction_test
shared_abstraction_justification=ownership_or_multiple_live_callers
versioned_scientific_filenames=forbidden_git_is_history
```

## Orchestrator-first delegation path

Code Project Manager first decomposes the request, chooses the architecture and
technical approach, maps dependencies and concurrency, and writes a
self-contained natural-language assignment. A coherent nontrivial
implementation-plus-focused-test package defaults to one registered
implementer: routine frozen engineering goes to
`hmasd-implementer-terra`, while protected algorithm, numerical or training
semantics go to `hmasd-implementer`. Use the registered code scout for interface
mapping, `hmasd-cpm-mechanical` for deterministic fact organization, the
Experiment Operator for an authorized experiment, one scope-local advisory
Reviewer after the same CPM combines its L2 outputs into one coherent
scope-local candidate, and the Verifier only when the existing scope-local
execution-readiness trigger fires. The Reviewer never performs a
cross-direction or union review.

The single simple fallback is direct execution of a cheap reversible singleton
when delegation would add more coordination than the bounded work. CPM also
acts directly for owner-exclusive architecture, scope-local integration,
acceptance or Git decisions. There is no microdelegation threshold, rigid assignment schema,
passive relay path or completion-token acceptance; assignments remain
natural-language contracts and CPM checks action-bearing conclusions and
concrete postconditions.

Disjoint code-scope assignments use the parallel-first path. While a child or
experiment is outstanding, CPM continues independent mapping, review,
integration, assignment and acceptance work. CPM waits in a bounded fashion
only when every remaining safe action depends on that result. Same-file writer
exclusion and existing `fork_turns` contracts remain required; children never
accept, stage, commit, push, change science, authorize costly runtime or update
canonical CPM state. Root may dispatch multiple CPM L1 instances with caller
action `fork_turns=1` and self-contained assignments; each scoped CPM may fan
out registered L2 leaves within depth 2 and performs final technical acceptance
for its exact slice. Root may mechanically integrate accepted candidates in a
separate Root-managed integration worktree and run union Tests/Static, but that
Root union PASS is mechanical evidence only and creates no technical-semantic
acceptance. Root
must not resolve or rewrite physical or test-exposed semantic conflicts; they
return to the owning direction CPM(s), or to a temporary named
`shared:<component>` CPM for a shared dependency. No extra union Reviewer is
created and no integration-group scope exists. This path adds no scheduler, queue, registry, quota,
reservation, retry mechanism or runtime ledger, uses no time-triggered wake-up
loop, and changes no science or runtime state.

A direction CM may read a frozen shared dependency but never edit it. Any
shared-component edit requires a separate temporary exact
`shared:<component>` CM; `shared:all` is never valid.

The upstream `using-superpowers` rule yields to user and `AGENTS.md`; the markers
above explicitly disable it. Never invoke or chain generic Superpowers Skills.
A user-named one may be inspected only as reference.

## CM recovery, Operator, and formal-review lanes

CM owns the whole engineering producer path: code, runner, adapters, package
and dependency installation, interpreter/backend selection, isolated
environment setup, tests, technical acceptance, pre-full recovery and
Operator dispatch. `CM-ready` is an action-bearing handoff sufficient for CM
to build missing engineering objects. `run-ready` is not a gate, token, or
machine state: it is true only after CM technically accepts the exact command,
configuration, seeds, budget, source/revision, dependencies/environment,
isolated run/evidence/checkpoint/result roots, and active authorization.

Before a result-bearing full begins, a preflight/import/runner/package/
environment failure returns to CM as evidence. CM automatically repairs,
re-verifies, and selects a legal `fresh|retry|resume|restart` run while the
frozen scientific question, comparator, estimand, and evidence class remain
unchanged. Changed source always means fresh identity and isolated roots. The
Operator receives only an exact run-ready assignment, performs one ordered
`train -> evaluate -> analyze` sequence, and returns mechanical `COMPLETE` or
`ERROR`; it never installs, repairs, changes source/configuration, or chooses
recovery. Once a result-bearing full begins, CM returns terminal evidence and
does not silently replay it.

Formal `CODE_SCIENCE_ALIGNMENT_AUDIT` remains a CPM-owned comparison audit
through the parent-specific `hmasd-cpm-agentify-transport` child. It is not an
Explorer-origin final review. The transport child owns page/provider/wait and
receipt mechanics; an `ERROR` remains review-local and does not replace CM's
engineering recovery path. The legacy audit name means scientific-contract
alignment at one published revision, never code correctness, test review,
debugging, style, dependency or runtime acceptance.

For deterministic inspection, result extraction, handoff preparation or state
rendering, CPM may trigger `hmasd-cpm-mechanical`. This Skill does not duplicate
its mechanical contract. CM remains assignment author and sole technical and
mechanical acceptance owner. `.agents/roles/CPM_MECHANICAL_OPERATOR.md` owns
the mechanical result fields and bounded observation recovery.

Overnight authorization is supplied by the natural-language assignment. Within
that assignment CM may perform dependency/environment setup, focused tests,
named long compute, bounded recovery and Operator dispatch without a repeated
permission prompt. Shared environment/Conda/ABI/backend mutation, untracked or
artifact overwrite/delete, long/formal compute, and process-kill effects need
local effect evidence (`action`, `target`, `reason`, `before`, `result`,
`rollback`, `commit-or-receipt`), not an admission or retry mechanism.

## Action-triggered references and action-bearing Explorer↔CPM interface

Load the execution-readiness Role and helper only when its existing
execution-entry, artifact-lifecycle, serialization or phase-connection trigger
fires. Load the Explorer↔CPM contract and project maps/views only when the
assignment names an Explorer handoff or a coupled or load-bearing project task.
These references remain outside default startup.

Use `docs/project/EXPLORER_PROJECT_VALIDATION_WORKFLOW.md` as the single
detailed source. CPM consumes and returns action-bearing prose; it never infers
an action from a status-only token. `parked` is Explorer-local when no frozen
live replacement exists, while ordinary engineering gaps go to CPM. A missing or
contradictory meaning preserves the original, asks one exact clarification and
continues unrelated work.

The canonical file-backed Explorer-to-CM transport consumer is
`temp/handoffs/explorer_to_code_manager/`. It carries the named action-bearing
handoff into CM; it is not a reverse-intake queue, a status-token substitute,
or a source of scientific authority.

For any runtime-bearing action, Root mechanically observes actual live
processes, CPU, memory and concrete resource conflicts. CPM consumes those
observations for scope-local technical/runtime judgment. The active runtime
contract is `runtime_unit_accounting=none`, `runtime_pool=none`,
`runtime_class_quota=none`, `runtime_reservation=none`, and
`runtime_admission_ledger=none`; this Skill adds no monitoring or stateful
runtime control mechanism. High-cost runtime requires an
explicit user task routed through Root. Path, worktree and code parallelism do
not authorize costly runtime, and `max_threads=20` is an agent-concurrency
ceiling only. No runtime or costly execution is authorized by this Skill alone.
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
   brainstorm, ledger or approval when known.
3. **Probe.** Observe the smallest failing test for new behavior or plausible
   regression. For throwaway measurement/configuration, use a diagnostic.
4. **Implement.** No backward compatibility. Make the smallest coherent module
   change; remove replaced interfaces, adapters, migrations, fallbacks, state,
   and tests. Git history is the archive. Use one stable semantic module, not a
   new generation-number copy. A replacement deletes predecessor code, runner and
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
    changed claim-bearing code, Code Project Manager prepares the commit-bound
    critical-point index and returns a candidate-ready proposal to Root. Only
    when separately authorized does Root create one local candidate commit;
    CPM then dispatches the Verifier for the same candidate, performs final
    technical acceptance and routes the one comparison-only
    `CODE_SCIENCE_ALIGNMENT_AUDIT` through the CPM Agentify transport when
    required. The audit may identify a
   concrete contract mismatch but cannot
   design an algorithm, controller, solver or new evidence search. Its question
   uses only the GitHub repository, branch `aggressive`, and relevant
   repository-relative paths; contains no local absolute path, raw/blob URL,
   commit hash, checksum, byte count or receipt field; and asks for scientific
   alignment rather than file verification.

## Active module boundary

The default active architecture is `source -> controller -> episode -> metrics
-> analysis`. Optional formalization consumes frozen core outputs and never
feeds back into the core. Runners contain configuration and wiring only. A
module has one state owner or responsibility; do not mix environment dynamics,
policy decisions, metrics and artifact I/O. Keep public interfaces minimal,
dependencies directed, and complexity isolated. Extract shared code when it
improves ownership or serves multiple live callers.

## Action-triggered project cognition

For a new task-scoped coding assignment, read only the directly relevant
project map, owner, producer, consumer and focused test surfaces. Do not load a
generic workflow or assignment-writing corpus.

Use context depth deliberately rather than mechanically:

- Local tasks remain local and do not load `docs/project/PROJECT_MAP.md`.
- Coupled tasks read only the relevant project-map and
  `references/code-context-guide.md` sections, then the direct responsibility
  owner, producers, consumers and focused contract evidence.
- Load-bearing tasks read only the relevant map/context sections plus the exact
  assignment-named design, runtime boundary and claim evidence; existing
  readiness and review triggers still decide those actions.

When compiling a child assignment, send a short self-contained brief with the
outcome, exact scope, allowed action and completion evidence. Forked turns are
background context and never replace the brief.

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
implementers, code reviewers and the readiness verifier use the default
`fork_turns=1`. Forked turns are background context and never replace the
assignment.

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

Router, role, Skill, native-profile and registry changes belong directly to
Root. This Skill remains Code Project Manager's implementation loop for any
separately assigned source-code slice.

## Concurrency and review

- One writable L1 assignment owns one Root-managed worktree. Disjoint tracked
  L2 writers under that L1 share its common frozen base and exact path boundary;
  L2 children have no Git, helper or worktree-lifecycle authority. Root waits
  for the L2 children and creates one CPM slice candidate from their union.
- Different CPM L1 assignments use independent Root-managed worktrees, and
  Root integrates accepted slices in a separate worktree. If an independent
  candidate or lifecycle is needed, Root creates a new writable L1 assignment;
  no L2 receives an independent worktree.
- Root may dispatch multiple CPM L1 instances by unique
  `direction:<id>|shared:<component>` scope with caller action `fork_turns=1`
  and a self-contained assignment. Each scope CPM may fan out registered L2
  leaves within depth 2 and technically accepts its exact slice. Root may
  mechanically integrate accepted candidates in a separate Root-managed
  worktree and run union Tests/Static, but that Root union PASS is mechanical
  evidence only and creates no technical-semantic acceptance. Root must not resolve or rewrite
  conflicts; physical or test-exposed semantic conflicts return to the owning
  direction CPM(s), or to a temporary named `shared:<component>` CPM for a
  shared dependency. No extra union Reviewer or integration-group scope is
  created.
- A direction CM may read a frozen shared dependency but never edit it. Any
  shared-component edit requires a separate temporary exact
  `shared:<component>` CM; `shared:all` is never valid.
- Root mechanically observes live processes, CPU, memory and concrete resource
  conflicts. CPM uses those observations for scope-local technical/runtime
  judgment. Path, worktree and code parallelism never authorize costly runtime;
  `max_threads=20` is an agent-concurrency ceiling only. High-cost runtime
  requires an explicit user task routed through Root.
- Children do not perform Git or acceptance. Focused checks and execution
  readiness remain conditional on the existing triggers; no scheduler, queue,
  registry, quota, reservation, retry mechanism or runtime ledger is added.
- Before a result-bearing full starts, CPM may issue at most one engineering
  recovery that preserves all scientific literals. A light treatment is one-full,
  no sweep and no implicit retry. Once the full starts, CPM returns its terminal
  outcome without silently replaying it; any later full is a newly authorized
  treatment decision rather than operational recovery.
- Each concurrent treatment has an exact assignment, candidate-specific source
  freeze, accepted candidate revision, run/evidence/checkpoint/result roots,
  seed/RNG namespace, temporary session paths and technical-acceptance record.
  These are semantic candidate bindings, not Git or worktree identity
  requirements; when the assignment may write tracked paths, the Root-managed
  worktree is provisioned under the separate contract above. Assignment-owned
  paths remain the write boundary.
- Children do not perform Git or acceptance. Explicit CPM readiness dispatch
  yields a candidate-ready proposal to Root. Only when separately authorized,
  Root creates one local candidate commit; CPM dispatches the same-candidate
  Verifier check and performs final technical acceptance, after which Root may
  integrate the accepted paths. No legacy integration-subcommand, Hook Stop or
  current-Git-execution promise is part of this Skill.
- Do not compute per-file hashes for handoff. Exact paths and the resulting Git
  revision, when Root separately creates one, are sufficient code identity.
- Subtasks close on evidence plus one fresh Code Project Manager check. After
  the same CPM combines its L2 outputs into one coherent scope-local candidate,
  one independent advisory reviewer by default examines the complete candidate
  for that exact scope. Parallel reviewers are allowed only for genuinely
  independent questions within that scope. Never review once per implementer,
  perform a cross-direction or union review, or create an automatic re-review
  loop. The required Pro scientific-contract alignment audit occurs
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

## Scoped blocker boundary

Ordinary engineering absence and an Operator `ERROR` never stop the research
chain. CM first exhausts applicable repair, verification, and legal
`fresh|retry|resume|restart` recovery, then uses Root relay for a legal owner
action where needed. Only then may it report a scoped branch blocker, with one
concrete non-executable fact: every implementation changes frozen science; EM
has different scientific options that evidence cannot decide; continuing
changes comparator, estimand, or evidence class; a real code-science conflict
exists; or no legal owner can choose the next action. The report pauses only
that branch. No `SESSION_BLOCKED`, receipt-exhaustion conclusion, or ordinary
engineering parking is created; independent work continues.

## Common mistakes

| Mistake | Correction |
|---|---|
| preserve compatibility “just in case” | delete the superseded path |
| equate quality with coverage or a full suite | test the actual claim |
| follow a generic Skill's Git/review/commit ritual | use this procedure only |
| turn file hashes into a handoff or approval gate | use exact paths and Git identity |
| ask again inside an active overnight assignment | complete CM-owned setup, recovery, and named execution with effect evidence |
| pause after an unfavorable result | archive it and follow the Pro continuation or terminal disposition |
| propose external authority while an in-scope route exists | defer it and continue the in-scope route |
| optimize an asymptotically forbidden evidence search | return it to Pro for a bounded discriminator |
