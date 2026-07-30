# UAV G0 behavioral replay contract clarification

Answer only the frozen contract question below. Do not redesign G0, change
geometry, metrics, confidence rules, controls, episode counts, or protected
fields. Use the GitHub connector and only the allow-listed paths in the shared
manifest. Return one exact disposition token and the complete ASCII addendum
required by that token.

## Exact implementation diagnosis

The G0 code assignment required a registered, shared, immutable safety ledger.
The oracle candidate trace was generated before behavioral service rows and
could not read future service. In the real test, the selected candidate was
`stage/+1`; event onset was step 191 and rejoin was step 272. The ledger and
independent primitive reload completed successfully. The first semantic
difference between the sealed candidate trace and the later behavioral replay
was:

`/steps/280/guarded_executed_action/data_hex`

The traces matched through step 279. At step 280 the pre-behavior candidate
kept the reserve at the gate because it could not know future service. The
behavioral controller had observed service-conditioned `RETURN_READY` and
returned the reserve to staging. Thus the frozen safety addendum's requirement
of byte-identical proposed action, guarded action, and physical state at every
step cannot hold simultaneously with the no-future-service information rule
and the required `RETURN_READY` behavior.

This is a contract conflict, not a test timeout or a code-path ambiguity.
The Code PM must not choose a scientific interpretation. No source commit,
formal run, nonformal run, bootstrap, or iteration result exists for this
attempt; the five implementation paths remain uncommitted and preserved.

## Required decision

Choose exactly one policy, preserving every previously frozen G0 field and
claim boundary:

1. `G0_REPLAY_CONTRACT_DISPOSITION=CONTINGENT_SAFETY_POLICY`
   Define the registered oracle object as a contingent policy over the
   allowed current-information state. State exactly which pre-behavior safety
   facts are sealed, how the policy is evaluated after service-conditioned
   `RETURN_READY`, and which invariant—not literal action/state identity—is
   compared during replay. State why this does not leak future service into
   candidate ranking.

2. `G0_REPLAY_CONTRACT_DISPOSITION=POST_RETURN_READY_REPLAY_RULE`
   Retain a realized pre-behavior trace, but define the exact post-
   `RETURN_READY` replay comparison and the first step at which a target may
   change. State which guard inputs, actions and physical state fields remain
   required byte-identical before and after that boundary. Do not weaken
   safety, ownership, permutation or pairing certificates.

3. `G0_REPLAY_CONTRACT_DISPOSITION=INVALID_REALIZATION_REQUIRED`
   Freeze that this realization is invalid whenever the required pre-behavior
   trace and the service-conditioned behavioral replay cannot satisfy their
   exact comparison. State that no `INFEASIBLE`, `ORACLE_ONLY`, `UNDERPOWERED`
   or `IDENTIFIED` result is admissible in that case.

If none of the three policies can be made exact without violating the frozen
information boundary, choose `INVALID_REALIZATION_REQUIRED`.

## Required response format

Return one ASCII-only response with these headings, in this order:

`G0_REPLAY_CONTRACT_DISPOSITION`
`G0_REPLAY_CONTRACT_OBJECT`
`G0_REPLAY_CONTRACT_INFORMATION_BOUNDARY`
`G0_REPLAY_CONTRACT_COMPARISON_RULE`
`G0_REPLAY_CONTRACT_FAILURE_SEMANTICS`
`G0_REPLAY_CONTRACT_PROTECTED_FIELDS`

The first heading must contain exactly one of the three tokens above. Include
the exact post-`RETURN_READY` step rule or the exact invalidity rule required
by the selected token. Do not return an implementation commit, a compute
authorization, or a learned/formal result.
