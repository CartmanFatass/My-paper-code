---
name: hmasd-agile-research-development
description: Use when implementing, debugging, refactoring, or validating exploratory HMASD algorithm code, prototypes, runners, analyzers, or operational repairs.
---

# HMASD Agile Research Development

## Contract boundary

Read the root router, the role contract, and brief. This procedure grants no
science, formal compute, transport, or acceptance authority. External Pro owns
scientific decisions; Code Project Manager alone accepts code, directs
engineering repair and owns code-side Git integration. Research Operations
Manager owns runtime and transport. A bounded child requires an exact
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
codebase_policy=small_active_line_only
workflow_hash_validation=disabled
per_file_hash_handoff=forbidden
test_acceptance_basis=risk_and_claim_coverage
line_coverage_target=none
test_count_target=none
cpm_performance_scoring_from_tests=forbidden
formal_result_snapshot_oracle=forbidden
direction_local_test_lifetime=active_implementation_only
shared_defect_regression_promotion=plausible_recurrence_only
```

The upstream `using-superpowers` rule yields to user and `AGENTS.md`; the markers
above explicitly disable it. Never invoke or chain generic Superpowers Skills.
A user-named one may be inspected only as reference.

## Operating loop

1. **Align.** For conclusion-bearing work, require an exact Pro scientific
   disposition and its design-audit status. Before implementation Code Project Manager performs
   only a local feasibility read. It returns a concrete ambiguity,
   impossibility or counterexample to Research Operations Manager for one
   focused Pro clarification; there is no routine pre-implementation review.
   Pure operational work records why the audit is not triggered.
2. **Bound.** Use the brief and
   `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`. Code Project Manager defines code
   files, engineering choices, exclusions and completion inside the Pro-frozen
   semantics. Before implementation, write the zero-compute `H`, fixed
   `K_search`, hypothetical-transition bound and projected wall clock. Add no
   brainstorm, plan, worktree, ledger or approval when known.
3. **Probe.** Observe the smallest failing test for new behavior or plausible
   regression. For throwaway measurement/configuration, use a diagnostic.
4. **Implement.** No backward compatibility. Make the smallest active-line
   discriminator; remove replaced interfaces, adapters, migrations, fallbacks,
   state, and tests. Git history is the archive.
5. **Verify.** Proof proportional to the claim: rerun the focused check fresh.
   For result-bearing runner/analyzer integration, execution-entry, artifact,
   serialization or phase-connection changes, and code defects exposed by
   preflight, focused tests alone are insufficient. Run the two-layer
   execution-readiness procedure below. Use a broad suite only for a changed
   shared surface.
6. **Inspect and report.** Check protected semantics, RNG/replay/lifecycle,
   serialization, transfers, synchronization, packing, persistence, and serial
   evaluation. Report commands, results, limits, and files. For new or materially
   changed claim-bearing code, Code Project Manager writes the commit-bound
   critical-point index, pushes the accepted implementation and returns its
   exact commit and index to Research Operations Manager. Research Operations
   Manager routes the one comparison-only `CODE_SCIENCE_ALIGNMENT_AUDIT` before
   a formal run. The audit may identify a concrete contract mismatch but cannot
   design an algorithm, controller, solver or new evidence search.

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

## Mechanical execution readiness

Code Project Manager prepares the exact candidate-bound spec and assigns the
registered `hmasd-verifier`. Candidate-focused checks never duplicate a phase
argv or write the exercise root. The verifier uses the registered interpreter
and the Skill-owned script in two mechanical steps:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  .agents/skills/hmasd-agile-research-development/scripts/hmasd_execution_readiness.py `
  run --spec <temporary-json-spec>
```

Invoke `run` once in the ordinary candidate toolchain environment without
elevation. The outer tool timeout is explicit and equals the sum of the six
`timeout_seconds` values plus 60 seconds. The script is the only executor of the
phase argv arrays; neither Code Project Manager nor verifier pre-runs, replays or
manually invokes them. Successful `run` writes a candidate receipt inside the
exercise root and returns `HMASD_EXECUTION_READINESS_PHASES_OK`.

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  .agents/skills/hmasd-agile-research-development/scripts/hmasd_execution_readiness.py `
  finalize --spec <temporary-json-spec>
```

Invoke `finalize` once only after the phase-success token. Give this
zero-compute command a short explicit timeout and narrow exact-command
elevation. It reruns no phase, validates the candidate receipt against the
current clean commit, exact spec, phase argv/status and expected artifacts, and
writes only the Git-private receipt. The result-bearing `run` is never elevated,
so its compiler, native-extension cache and candidate environment do not change
between focused evidence and readiness execution.

The temporary JSON spec binds one candidate commit, exact accepted paths,
`formal=false`, `scientific_iteration_cost=zero`, one independent proof-sized
exercise root, expected artifacts and argv arrays for these ordered phases:

```text
interface_smoke -> bounded_exercise -> artifact_validation -> artifact_reload -> evaluate_entry -> analyze_entry
```

`interface_smoke` instantiates the production configuration and calls the same
entry method, argument shapes and return schema used by the production runner.
Calling a lower-level projection method directly is not a substitute. The
remaining phases exercise the real proof-sized entry, canonical validator,
artifact reload and minimal real evaluate/analyze entries to completion. They
never use a formal authorization token, formal budget or scientific threshold
disposition.

The script executes argv arrays without a shell, fails at the first unsuccessful
phase and checks the expected artifacts. It exposes the successful Git-private
receipt only after `finalize` revalidates all six phases on the exact clean
candidate commit. The receipt is mechanical evidence, is not Git-tracked and is
not another acceptance owner. The verifier returns the receipt or distinguishes
a pre-phase invocation failure, the first causal phase failure, and a
zero-compute finalization failure without repair.
Code Project Manager classifies that evidence, owns any reassignment or repair,
and alone accepts the candidate.
For a deterministic post-acceptance defect with plausible recurrence, add one
proof-sized regression before rerunning the procedure.

A readiness phase timeout is candidate evidence, not authority to replay the
same proof root or relax its timeout. A new or revised workflow contract chooses
a semantics-preserving technical optimization under the unchanged phase timeout
or an evidence-backed timeout revision. That contract may also define a bounded
operational retry budget for one unchanged clean candidate. Every attempt still
requires one exact spec, one fresh absent root, one wrapper run, the same ordered
six phases and a full commit-bound receipt. Any code or validator defect produces
a new clean pushed candidate; only a transient environment, launcher, path or
operating-system failure may consume an explicitly defined retry budget. A
timeout, technical failure or finalization failure consumes zero scientific
iterations, produces no scientific disposition and leaves its root terminal.
Nothing automatically increases a timeout or switches the selected response.

The project `Stop` hook is a last-message guard only. It runs no validation
command. In the fixed Code Project Manager task, a `CODE_ACCEPTED` return with
`execution_readiness=passed` must name a matching successful receipt; an
untriggered return must state its bounded reason. Other roles, ordinary turns
and blocked returns are no-ops.

An execution-readiness operational failure before `CODE_ACCEPTED` remains in
the Code Project Manager verification loop and never routes to Research
Operations Manager as a partial code handoff. After code acceptance, classify
every runtime terminal event before continuing. A purely operational failure
returns control to Research Operations Manager for automatic `retry`, `resume` or `restart` inside the
unchanged authorized scientific boundary, without per-attempt reauthorization
or a fixed attempt count. Preserve the estimator, source, seed law, budgets,
thresholds, backend constraints and branch semantics; never weaken checks or
use recovery to select among scientific outcomes. Operational recovery uses
zero scientific iterations and creates no scientific disposition. A valid
scientific result is archived and routed to External Pro. An external hard
technical impossibility is terminal only after applicable automatic recovery
cannot make progress. Add a regression only for plausible recurrence of a code
defect.

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
- Children do not perform Git. Code Project Manager integrates the exact accepted
  file set directly; no relay or completion receipt exists.
- Do not compute per-file hashes for handoff. Exact paths, the staged path set,
  and the resulting Git commit are sufficient code identity.
- Subtasks close on evidence plus one fresh Code Project Manager check. The required Pro
  code-science audit occurs once after Code Project Manager implementation acceptance; it is a
  contract diff and owns scientific alignment, not code acceptance or
  implementation design. Additional
  code review is allowed only after a failed check or concrete engineering
  anomaly; it diagnoses repair and is not another approval layer.

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

Research Operations Manager applies the terminal-event routing below. Inside
the active authorized nine-valid-iteration grant, do not stop for user
input, a permission prompt, a scientific result or protected-science ambiguity.
Archive every valid success, failure, mixed or
underpowered result and return it to External Pro. Pro maintains multiple live
or parked directions when evidence supports them. Pro returns
`COMPLETE_BALANCE_EXHAUSTED` when all nine valid iterations are consumed;
otherwise it returns `CLOSE_NO_EXECUTABLE_CANDIDATE` only when the full preserved
portfolio has no executable in-scope candidate, or `CONTINUE` with one current
resource-consuming action. That scheduling boundary provides attribution and
does not establish scientific uniqueness. Research Operations Manager executes
only the designated `CONTINUE` action and never reorders or compresses the
portfolio. While balance
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
