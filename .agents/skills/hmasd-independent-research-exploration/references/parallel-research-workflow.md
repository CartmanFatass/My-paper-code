# Parallel independent research workflow

```text
scout_parallel_limit=4
critic_parallel_limit=2
merge_barrier=required
completion_order_priority=forbidden
single_writer=independent_research_explorer
child_depth=0
automatic_formal_workflow_promotion=forbidden
```

## Flow

1. **Intake.** Freeze the question, quick/deep mode, mission connection,
   exclusions, sources and completion condition.
2. **Integrity gate.** The Explorer alone reads MyLib integrity and records the
   live contract, counts and missing JSON IDs.
3. **Recall.** The Explorer forms a bounded candidate list from indexes without
   treating excerpts as evidence.
4. **Partition.** Split by independent research axes or non-overlapping paper
   IDs. Every candidate has one Scout owner; cross-axis comparison remains with
   the Explorer.
5. **Scout wave.** Launch 1-4 read-only Sol-high Scouts concurrently. Each gets
   one exact axis, paper set, source boundary and packet contract. One low-cost
   retry is allowed only for an operational failure with unchanged assignment.
6. **Merge barrier.** Wait for every terminal Scout packet. Reject malformed or
   scope-expanding packets. Deduplicate evidence and map conflicts; never
   privilege the packet that completed first.
7. **Critic selection.** Select only central, surprising, conflicting or
   high-consequence claims. Ordinary corroborated facts do not require a Critic.
8. **Critic wave.** Launch at most two read-only Sol-max Critics concurrently,
   each against exact claim and packet identities. Critics assess; they do not
   choose the project direction.
9. **Synthesis.** The Explorer reconciles all packets, distinguishes source
   claims from inference and writes the only durable report under
   `local_research`.
10. **Stop.** Report local completion. The user alone may initiate a separate
    formal workflow submission.

With `max_threads=8`, the maximum intended occupancy is one Explorer, four
Scouts and two Critics, leaving one slot unused. Scout and Critic waves are
sequential around the merge barrier, so normal occupancy is lower. Children
cannot spawn, write, use Git, contact persistent tasks or access active HMASD
state.
