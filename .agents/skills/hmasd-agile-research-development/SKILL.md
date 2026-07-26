---
name: hmasd-agile-research-development
description: Use when implementing, debugging, refactoring, or validating exploratory HMASD algorithm code, prototypes, runners, analyzers, or operational repairs.
---

# HMASD Agile Research Development

## Contract boundary

Read the root router, the role contract, and brief. This procedure grants no
science, formal compute, transport, or acceptance authority. External Pro owns
scientific decisions; Project Manager alone accepts code, directs engineering
repair and owns direct Git integration. A bounded child requires an exact
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
   disposition and its design-audit status. Before implementation PM performs
   only a local feasibility read. It returns a concrete ambiguity,
   impossibility or counterexample through the dedicated External Review
   Operator as one focused clarification; there is no routine pre-implementation
   Pro review. Pure operational work records why the audit is not triggered.
2. **Bound.** Use the brief and
   `docs/project/EVIDENCE_COMPLEXITY_POLICY.md`. Project Manager defines code
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
   Add one bounded end-to-end exercise for material integration. Use a broad
   suite only for a changed shared surface.
6. **Inspect and report.** Check protected semantics, RNG/replay/lifecycle,
   serialization, transfers, synchronization, packing, persistence, and serial
   evaluation. Report commands, results, limits, and files. For new or materially
   changed claim-bearing code, PM writes the commit-bound critical-point index,
   pushes the accepted implementation, and sends its exact identity to Workflow
   Manager. Project Manager routes the one existing comparison-only
   `CODE_SCIENCE_ALIGNMENT_AUDIT` after implementation acceptance and before a
   formal run. The audit may identify a concrete contract mismatch but cannot
   design an algorithm, controller, solver or new evidence search.

On failure, locate the first violated invariant and distinguish scientific
failure from a purely operational failure. Within the unchanged user-authorized
scientific boundary, PM may arrange low-cost retry, resume or restart without
per-attempt reauthorization or a fixed attempt count. Preserve the estimator,
source, seed law, budgets, thresholds, backend constraints and branch semantics;
never weaken checks, retry blindly or use recovery to select among scientific
outcomes. Operational recovery costs zero scientific iterations and produces no
scientific disposition or abandonment. Add a regression only for plausible
recurrence of a code defect.

## Complexity gate

HMASD tests Pro-proposed ideas; it does not implement unlimited solvers. Search
introduced only for evidence must be at most `O(H*K_search)` with fixed
`K_search<=16` and no more than `16*H` hypothetical transitions per controller
episode. Nested remaining-horizon rollout at every real step, recursive rollout
inside a candidate rollout, tree/beam/MCTS search and horizon-growing candidate
sets are forbidden regardless of C++ speed or parallel hardware. A nonformal
exercise is capped at 20 minutes and a formal iteration at eight cumulative
hours. Exceeding the bound returns `NON_EXECUTABLE_EVIDENCE_DESIGN` to PM, which
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
Skill remains PM's implementation loop for any separately assigned source-code
slice.

## Concurrency and review

- One writer owns each file; disjoint paths may run in parallel. No global lease.
- Isolated worktrees use `scripts/hmasd_workspace_ticket.py`: PM creates one
  ticket from the actual Git worktree and base commit, the child resolves that
  ticket before editing, and PM verifies it after return. Never transcribe,
  infer or repair an absolute worktree path in prose.
- Children do not perform Git. Project Manager integrates the exact accepted
  file set directly; no relay or completion receipt exists.
- Do not compute per-file hashes for handoff. Exact paths, the staged path set,
  and the resulting Git commit are sufficient code identity.
- Subtasks close on evidence plus one fresh PM code check. The required Pro
  code-science audit occurs once after PM implementation acceptance; it is a
  contract diff and owns scientific alignment, not code acceptance or
  implementation design. Additional
  code review is allowed only after a failed check or concrete engineering
  anomaly; it diagnoses repair and is not another approval layer.

## Quick reference

| Change | Smallest sufficient evidence |
|---|---|
| helper or schema | one focused check |
| bug or invariant repair | reproduction, regression if durable, focused rerun |
| runner/analyzer integration | focused suite plus one bounded exercise |
| protected cross-file path | frozen contract, focused evidence, optional one review |

## Stop only for a real boundary

Stop for protected-science ambiguity, missing formal authority, same-file
collision, or exhausted recovery—not in-brief engineering.

## Common mistakes

| Mistake | Correction |
|---|---|
| preserve compatibility “just in case” | delete the superseded path |
| equate quality with coverage or a full suite | test the actual claim |
| follow a generic Skill's worktree/review/commit ritual | use this procedure only |
| turn file hashes into a handoff or approval gate | use exact paths and Git identity |
| ask again inside an active grant | continue to a real stop boundary |
| optimize an asymptotically forbidden evidence search | return it to Pro for a bounded discriminator |
