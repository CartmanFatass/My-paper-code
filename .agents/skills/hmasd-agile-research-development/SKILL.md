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

## Mechanical execution readiness

Use the registered interpreter and the Skill-owned script:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  .agents/skills/hmasd-agile-research-development/scripts/hmasd_execution_readiness.py `
  run --spec <temporary-json-spec>
```

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
phase, checks the expected artifacts and writes a successful Git-private receipt
only when all six phases pass on the exact clean candidate commit. The receipt
is mechanical evidence, is not Git-tracked and is not another acceptance owner.
For a deterministic post-acceptance defect with plausible recurrence, add one
proof-sized regression before rerunning the procedure.

The project `Stop` hook is a last-message guard only. It runs no validation
command. In the fixed Code Project Manager task, a `CODE_ACCEPTED` return with
`execution_readiness=passed` must name a matching successful receipt; an
untriggered return must state its bounded reason. Other roles, ordinary turns
and blocked returns are no-ops.

Classify every terminal event before continuing. A purely operational failure
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
