# Five-direction execution parallelism

Date: 2026-09-04

Provenance: `OWNER_DIRECT`

## Decision

Root maintains a target working set of five concurrently advancing top-level research-direction
DM chains. This is an execution-parallelism target, not a requirement that the Portfolio contain
five `ACTIVE` directions. All currently lifecycle-`ACTIVE` directions remain admitted unless a
separate Portfolio-tier decision changes their lifecycle.

This clarification supersedes the literal "all ACTIVE directions continue in parallel" wording in
`2026-09-04-owner-intervention-surfaces.md` while preserving its intended lifecycle rule: sequencing
never becomes a disposition. An admitted direction outside the current working set is queued, not
`PARKED`, deprioritized, fused, absorbed, or closed.

Count only top-level direction/DM chains toward five. Root, Transport, CM, implementer, reviewer,
critic, verifier, operator, and detached experiment processes do not consume additional direction
slots. The existing removal of repository-level fixed limits on nested implementer sessions and
result-bearing runs remains in force inside the working set, subject to actual runtime resources,
path/dependency ownership, per-arm cost law, and the fresh per-invocation 4 GiB admission.

## Initial working set

The initial five chains are:

1. `finite_resource_relational_inductive_efficiency` — live high-priority B01 algorithm evidence;
2. `flexible_skill_duration` — live high-priority E3 discriminator on the remote node;
3. `capability_bound_semantic_currentness` — high-priority production-conformance closure;
4. `ucope` — high-priority, portable clean-boundary three-witness/headroom discriminator; and
5. `variable_n_fleet_churn` — high-priority R02/Convergence boundary with a decision-relevant next
   object.

The roster records current execution, not a permanent reservation or lifecycle judgment.

## Refill and rotation

- At each clean boundary Root reads owner reviews and reconciles completed or blocked chains.
- A chain yields its slot when it completes its current boundary, reaches a terminal Direction- or
  Portfolio-tier blocker, or cannot advance a named dependency while another direction can.
- Root fills a vacancy with the most promising runnable `ACTIVE` direction, comparing decision
  relevance, the lowest sufficient evidence class, honest claim ceiling, expected information
  gain, cost and reversibility, current dependencies, and contrary evidence.
- A temporary overlap above five is allowed to drain; live agents and accepted experiments are not
  interrupted merely to restore the target. Root does not refill until the count returns to five.
- A shortage below five is reported only when fewer than five admitted directions are genuinely
  runnable after safe in-scope alternatives are exhausted.

## Fusion boundary

Five is not a convergence target. Similar naming, host, mechanism family, or reusable baseline
assets is insufficient for fusion. Root raises a concrete on-demand Portfolio fusion or absorption
question only after showing that the directions' question, comparator, estimand, and next object
are materially the same. The persistent Portfolio Pro proposal and owner ratification path remains
required for such a lifecycle action.

This decision changes no frozen object, claim ceiling, result polarity, provider-conversation
binding, remote-first placement rule, or lifecycle row in `PORTFOLIO.md`.
