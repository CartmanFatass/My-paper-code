# External Pro open question: UAV G0 oracle-gate finite-precision arrival

```text
review_type=ORACLE_GATE_FINITE_PRECISION_ARRIVAL_CLARIFICATION
audit_mode=read_only_zero_compute_contract_clarification
compute_budget=zero
scientific_iteration_cost=zero
audit_target_source_commit=83bad9ebf489d24cb67ad30e10905cb0eb84f04a
execution_commit=9992701d814acc46d5a69d9b499b926f76a5d265
aligned_implementation_commit=c88f43de6451c40defefd7c679ba8d353c45735c
aligned_source_blob=b0baab9c47c2537217b689699d0520f158355e3d
alignment_stage_commit=499fcaac7acea4faf58268b71773459ef73bedec
failed_gate=gate_08
allowed_outputs=ARRIVAL_SEMANTICS=DEAD_ZONE_BOUND|REACHABLE_GATE_REPRESENTATION|UNREACHABLE_INVALID_REALIZATION
```

You are External GPT-5.6 Pro and the exclusive scientific authority inside
this bounded clarification. Use the connected GitHub repository connector for
`https://github.com/CartmanFatass/My-paper-code.git`, branch `aggressive`, and
read only the allow-list in `01_SHARED_SOURCE_MANIFEST.md` at the exact target
commits. Do not use a local working tree, runtime logs, unlisted files, or
compute. Do not activate Answer now. Return exactly one ASCII line and no
Chinese summary.

The first formal G0 attempt reached gate_08 but stopped before Oracle EVENT or
NO_EVENT evidence. For episode 1, both the stage/-1 and stage/+1 owner-gate
candidate pairs raised `G0RealizationError: common tracker cannot reach oracle
gate within H`. The static diagnostic checked 256 episode-candidate pairs and
137 fail exact arrival. The first counterexample had residual/action norms:

```text
episode=1|stage=-1|residual_m=9.441646398045123e-08|action_norm=3.147215377197199e-09
episode=1|stage=+1|residual_m=6.493473847513087e-08|action_norm=2.164491252898415e-09
```

The accepted G1 transducer serializes raw actions as float32; the unchanged
S7-S1 conversion maps horizontal action norm <= 1e-8 to zero velocity. Under
the current generic continuous gate coordinates, the trajectory therefore
approaches a nonzero residual fixed point instead of becoming bitwise equal.
The frozen addendum forbids caller projection/controller tolerance, coordinate
snapping, float64 action substitution, and changes to thresholds, geometry,
actions, dynamics, ownership, permutation certificates, R=273, or evidence
inventory. Do not choose among those changes.

Freeze exactly one of these executable contract rules, preserving all other
G0 fields:

1. `DEAD_ZONE_BOUND`: the registered arrival is the unchanged float32
   tracker/S7 dead-zone fixed point, with a mechanically derived finite-
   precision arrival bound and preserved bitwise evidence. State the exact
   bound and the gate identity used for `n_gate` and `latest_departure`.
2. `REACHABLE_GATE_REPRESENTATION`: gate coordinates are constructed before
   behavior on a representation reachable by the unchanged transducer. State
   the exact representation, ownership/order binding, and how bitwise gate
   equality and arrival timing are certified without changing dynamics.
3. `UNREACHABLE_INVALID_REALIZATION`: an unreachable candidate/source is a
   failed qualification/INVALID realization. State the exact artifact path,
   schema fields, and ranking/first-match behavior; Oracle behavior is not
   required for that invalid realization.

Return exactly one line in this form, with no additional text:

`ARRIVAL_SEMANTICS=DEAD_ZONE_BOUND`
`ARRIVAL_SEMANTICS=REACHABLE_GATE_REPRESENTATION`
`ARRIVAL_SEMANTICS=UNREACHABLE_INVALID_REALIZATION`

Do not redesign G0, select a result, start readiness or scientific compute, or
write code. Stop after the single bounded clarification.
