---
name: hmasd-agile-research-development
description: Use when implementing, debugging, refactoring, or validating exploratory HMASD algorithm code, prototypes, runners, analyzers, or operational repairs.
---

# HMASD Agile Research Development

## Contract boundary

Read `AGENTS.md`, the role contract, and brief. This procedure grants no science, formal compute, transport, or acceptance authority. Project Manager alone accepts or directs repair and owns direct Git integration under its role charter. A bounded child requires an exact assignment and never scopes, accepts, or commits its work.

```text
superpowers_plugin=reference_only
superpowers_execution=disabled
development_mode=agile_algorithm_research
backward_compatibility=not_required
test_scope=proof_sized
codebase_policy=small_active_line_only
workflow_hash_validation=disabled
per_file_hash_handoff=forbidden
```

The upstream `using-superpowers` rule yields to user and `AGENTS.md`; the markers
above explicitly disable it. Never invoke or chain generic Superpowers Skills.
A user-named one may be inspected only as reference.

**Maintainability is not the requirement here; reproducibility is.** These
packages are not extended — they are built, produce evidence, and are superseded
(G20 by G20R by G20R2), so extensibility, adapters and backward compatibility are
dead weight and the policy above deletes them. But a package *is* the evidence
for a claim, so it must still produce the same number from the same commit in six
months: frozen seeds, the registered interpreter and thread count, declared RNG
stream ownership, exact replay. Trade maintainability away freely; never trade
reproducibility.

## Operating loop

1. **Bound.** Use the brief. Only Project Manager acting within direct user authority may define a fallback outcome, semantics, files, exclusions, and
   completion. Add no brainstorm, plan, worktree, ledger, or approval when known.
2. **Probe.** Observe the smallest failing test for new behavior or plausible
   regression. For throwaway measurement/configuration, use a diagnostic.
3. **Implement.** No backward compatibility. Make the smallest active-line
   discriminator; remove replaced interfaces, adapters, migrations, fallbacks,
   state, and tests. Git history is the archive.
4. **Verify.** Proof proportional to the claim: rerun the focused check fresh.
   Add one bounded end-to-end exercise for material integration. Use a broad
   suite only for a changed shared surface.
5. **Inspect and report.** Check protected semantics, RNG/replay/lifecycle,
   serialization, transfers, synchronization, packing, persistence, and serial
   evaluation. Report commands, results, limits, and files.

On failure, reproduce once, locate the first violated invariant, add a regression
only for plausible recurrence, repair, and rerun. Never weaken checks or retry blindly.

## Concurrency and review

- One writer owns each file; disjoint paths may run in parallel. No global lease.
- Children do not perform Git. Project Manager integrates the exact accepted
  file set directly; no relay or completion receipt exists.
- Do not compute per-file hashes for handoff. Exact paths, the staged path set,
  and the resulting Git commit are sufficient code identity.
- Subtasks close on evidence plus one fresh PM check. At most one integrated advisory review is optional when protected semantics, cross-file integration, or material execution risk makes it useful. Additional targeted review is allowed only after a failed check or a concrete protected cross-scope anomaly; it diagnoses repair and is not another approval layer.

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
