# UAV localized-demand-burst G33-P0 source witness

```text
document_kind=pm_executable_contract_extraction
scientific_authority=external_pro
code_acceptance_owner=project_manager
candidate=UAV_LOCALIZED_DEMAND_BURST_G33_P0
design_disposition=UNRESOLVED_UAV_BURST_G33_DESIGN
next_boundary=UAV_LOCALIZED_DEMAND_BURST_G33_SOURCE_WITNESS_AND_STATIC_UPPER_BOUND_AUDIT
learned_models=0
optimizer_steps=0
backend=cpu
torch_threads=1
conclusion_bearing_iteration_cost=1_only_if_a_valid_source_witness_result_is_produced
```

Scientific authority for every field below is the exact raw at
`docs/external-review/rounds/20260725_uav_localized_demand_burst_g33_design_assertion_audit/21_PRO_OPEN_RAW.md`.
This document makes its code boundary concise; it does not reinterpret it.

## Source

- Preserve S7-S1: 8 physical and service-active UAVs, 30 users, one ground BS,
  500 steps, ordinary demand 1 Mbps, target ratio 0.90, existing radio,
  routing, movement, reward coefficients and terminal graph PBRS.
- Battery, charging and temporary failure remain disabled. P0 makes no dynamic
  membership claim.
- Delivered traffic is `min(raw end-to-end capacity, current offered demand)`.
  Per-user satisfaction is `clip(capacity / current demand, 0, 1)`. The same
  current demand vector normalizes task utility and graph potential. Demand
  changes no raw capacity, connection, routing or physical transition.

## Episode ledger

The disturbed profiles are exact:

| Profile | Onset | Duration | Center/cohort | Multiplier |
|---|---:|---:|---|---:|
| `IID_BURST` | uniform integer 140..260 | uniform integer 40..80 | uniform center; center plus 7 nearest | equiprobable 1.5 or 2.0 |
| `EARLY_LONG` | uniform integer 60..120 | uniform integer 90..120 | uniform center; center plus 9 nearest | 2.25 |
| `REMOTE_STRONG` | uniform integer 180..260 | uniform integer 70..110 | uniform center among farthest 8 from nearest BS; center plus 9 nearest | 2.50 |

`NO_BURST` remains 1.0 throughout. Distances are horizontal and measured at
the pre-action onset boundary. User-index tie breaking is exact; the cohort is
frozen until burst end. The burst is active on `[O,O+D)`, ordinary demand
returns before the action at `O+D`, recovery is `[O+D,O+D+60)`, and all windows
finish before step 500.

Burst, ordinary user motion, initial physical state, channel, action and
counterfactual randomness own independent episode-addressed namespaces.
Controls share the complete episode ledger and exogenous trajectory.

## Information contract

Each visible local user row contains current relative position, normalized
SINR, connected-to-self, serviced-by-any, normalized current demand and a
visibility flag. Demand normalization is `clip((q/q0 - 1)/1.5, 0, 1)`.
Rows use anonymous current physical-content order and padded rows are zero.

The centralized critic contains the unchanged current physical state plus the
current demand paired with each user row. Explicit physical time is absent from
both actor and critic. Neither receives a future onset/end, remaining duration,
future multiplier/cohort/position/channel, center identity, centroid, target
assignment, role label, progress metric, reward input or stable identity.

Every affected user must be collectively visible at onset. Violation fails the
source-information contract.

## Controls

The exact six controls are:

1. `FULL_LEDGER_REACHABILITY_ORACLE`
2. `CURRENT_ONLY_ADAPTIVE_CONSTRUCTIVE`
3. `NO_REALLOCATION`
4. `MOTION_SUPPRESSED_CONTINUATION`
5. `STATIC_FULL_LEDGER_PREPOSITION`
6. `NO_BURST_CONTROL`

All use the Pro-frozen shared layout library and legal continuous movement.
Constructive and no-reallocation actions are identical before onset.
Motion suppression replaces only UAV movement components by zero from onset
through recovery while preserving recurrent state and every exogenous draw.

The exact layout score, future-ledger objective, static preposition procedure
and N1 certificate interface are pending the focused
`IMPLEMENTATION_ALIGNMENT_CLARIFICATION`. Until that raw completes, code may
realize the source environment and structural probes but may not implement a
result-bearing controller or source analyzer.

## Estimands and evidence unit

For burst `B=[O,O+D)`, recovery `R=[O+D,O+D+60)` and ordinary
`N=[0,O) union [O+D+60,500)`, compute the exact affected, unaffected and team
service traces from the raw. The deficit-normalized window score is:

`J(X,r) = 1 - mean(max(0, 0.90-r_t) / 0.90 for t in X)`.

The cell access score is the minimum of burst and recovery `J/0.80` plus
unaffected and ordinary service divided by 0.90. Equality passes. Source gates
are evaluated separately for every disturbed profile:

- full-ledger and current-only access: CI95 lower bound at least 1;
- no-reallocation and motion-suppressed access: CI95 upper bound below 1;
- constructive minus each negative control burst-J: CI95 lower bound above
  0.10;
- paired no-burst ordinary access: CI95 lower bound at least 1;
- a confidently accessing full-ledger static control rejects P0.

The formal evidence unit is three replicate namespaces and 128 paired episode
IDs per profile per replicate. Hierarchical bootstrap uses 10,000 resamples:
resample replicates, then whole episode IDs inside each selected replicate,
retaining every paired control and counterfactual row. Users, time rows and
branches are never resampled independently.

## Source-witness outcomes

- `SOURCE_WITNESS_REJECTS_P0_G33`: a confident structural/source failure or a
  confident static counterexample; close P0 without rescue.
- `SOURCE_WITNESS_SUPPORTS_N1_G33`: all gates pass and a complete declared
  static-policy upper-bound certificate passes.
- `SOURCE_WITNESS_SUPPORTS_ONLY_N2_G33`: all policy-specific source gates pass
  but universal static coverage is unavailable; return to Pro for explicit
  claim narrowing.
- `SOURCE_WITNESS_UNDERPOWERED_G33`: a required interval crosses its boundary;
  close the frozen witness without automatically adding evidence.

Exact first-match predicates remain pending only for the focused control
clarification. No learned runner is eligible before a valid source witness and
the subsequent Pro disposition.

## Implementation-only choices

File names, array layout, vectorization, telemetry, serialization, fresh
integer seed values, batch partitioning, CPU process topology and proof-sized
test organization are PM-owned provided the exact evidence object is unchanged.
No compatibility reader, alternate source profile or rescue parameter is kept.
