# G0 oracle safety/information clarification

Answer only the frozen contract question below. Do not redesign G0, change
geometry, metrics, confidence rules, controls, episode counts, or protected
fields. Use the GitHub connector and only the allow-listed paths in the shared
manifest. Return the required ASCII token and the exact addendum required by
that token.

## Frozen conflict

The accepted G0 addendum requires the oracle to generate and rank exactly two
reserve candidates before behavioral rows, under the unchanged S7-S1 physics,
action support, safety and collision rules. Candidate ranking is by violation
count, certified gate-arrival time, event-window target error, path length and
stage coordinates, with O(H*K_search), K_search=2, and no nested rollout.

The same addendum also forbids the oracle candidate generator from reading,
instantiating, consuming, inspecting or ranking by future channel or service
randomness. The exact G1 source at source_commit has a real backhaul safety
guard reached by the environment step path; that guard depends on current
connections, routing_paths and link capacity. If the guard is used during
candidate generation, it can change violation count, arrival time, tracking
error and path length, but it introduces channel/routing information into the
oracle candidate behavior. If it is omitted, the candidate is not certified
under unchanged S7-S1 safety.

## Required decision

Choose exactly one policy, preserving the original G0 claim scope and all
protected fields:

1. `G0_ORACLE_SAFETY_INFORMATION_DISPOSITION=REGISTERED_LEDGER_ALLOWED`
   Freeze an explicitly shared, pre-registered channel/routing ledger for both
   candidates, state exactly what fields are visible and how it is independent
   of future behavioral service rows, and retain real safety evaluation.

2. `G0_ORACLE_SAFETY_INFORMATION_DISPOSITION=CHANNEL_INDEPENDENT_KERNEL`
   Freeze a channel-independent safety kernel used before candidate ranking,
   state its exact inputs and proof that it is equivalent to the registered
   S7-S1 safety guard for all candidate-relevant states, and state what the
   runtime guard does after ranking.

3. `G0_ORACLE_SAFETY_INFORMATION_DISPOSITION=IDENTITY_GUARD_PROOF`
   Freeze the exact proof obligation that the real guard is the identity for
   both candidate trajectories over all relevant states, including the
   connections/routing/capacity fields and failure semantics.

4. `G0_ORACLE_SAFETY_INFORMATION_DISPOSITION=INVALID_REALIZATION_REQUIRED`
   Freeze that the source is `INVALID_UAV_G0_REALIZATION` whenever the
   required pre-behavior oracle safety certificate cannot be established, and
   state that no INFEASIBLE, ORACLE_ONLY, UNDERPOWERED or IDENTIFIED result is
   admissible in that case.

## Required response format

Return one ASCII-only response with these exact headings, in order:

`G0_ORACLE_SAFETY_INFORMATION_DISPOSITION`
`G0_ORACLE_SAFETY_INFORMATION_VISIBLE_FIELDS`
`G0_ORACLE_SAFETY_INFORMATION_CERTIFICATE`
`G0_ORACLE_SAFETY_INFORMATION_FAILURE_SEMANTICS`
`G0_ORACLE_SAFETY_INFORMATION_COMPLEXITY`
`G0_ORACLE_SAFETY_INFORMATION_PROTECTED_FIELDS`

The first heading must contain exactly one of the four tokens above. If the
chosen policy cannot be made exact from the allow-listed source, return
`G0_ORACLE_SAFETY_INFORMATION_DISPOSITION=INVALID_REALIZATION_REQUIRED`.
Do not return an implementation commit, a compute authorization, or a learned
result.
