# D7.S event-aligned source audit — re-registered contract

Status: **DRAFT_FOR_PRO_FREEZE** — authored 2026-07-26 from the ruling in
`docs/external-review/rounds/20260726_d7_s_part_b_flex_arm_and_instrument/21_PRO_OPEN_RAW.md`.
Supersedes the Part B realization of `D7_S_MAIN_SCENARIO_PERSISTENCE_NECESSITY.md`
(whose Part A structural certificate stands untouched). Nothing here is frozen
until Pro confirms; no conclusion-bearing measurement may run before that.

Ordered by Q7 of the ruling: this contract is evidence action 0. Actions 1–3
(conformance derivation, development-topology exercise, one joint audit) run
only after freeze, in that order.

## 1. Estimand — one intervention, two history classes

For mechanism `m ∈ {stable, flex}` at a qualified check history `h_m`
(section 2):

```text
V_KEEP_m(h_m) = max over legal joint continuations of
                E[ G_{H_m} | focal commitment held for exactly Delta ]
V_SET_m(h_m)  = max over z != z_i and legal joint continuations of
                E[ G_{H_m} | focal agent reassigned to z for exactly Delta ]
U*_m,src      = V_SET_m - V_KEEP_m
```

- `Delta = 10` primitive steps — the R30 commitment unit. The forced focal
  action binds for exactly one `Delta`; at `t + Delta` every constraint is
  released and **both branches receive the same best legal continuation**.
- The `max over z` is mandatory. Where the legal alternative set is finite it
  is enumerated; selection replicates choose the maximizing alternative and
  **independent evaluation replicates** estimate its return (split-sample),
  unless the continuation is exactly deterministic and analytically evaluated.
- Non-focal duties are **not** frozen in either branch: both arms optimize
  every non-focal assignment. A SET branch may coincide behaviorally with the
  mixed constructive optimum; what must be explicit is the focal decision,
  not a behavioral difference.

## 2. History classes — evaluator-certified, never role-named

Both classes are certified per-episode from realized state by the evaluator.
Role indices, reset-time slots and fixed UAV ids are prohibited as selectors.

**Stable check `h_stable`:** a supported shared check where an active
incumbent's current backhaul/service target remains locally optimal or
materially unchanged over the next `Delta`, and that incumbent holds a valid
current commitment.

**Flex check `h_flex`:** a supported shared check at an actual energy-driven
handoff opportunity: a duty is being or has just been vacated by a UAV
entering its charge-return/absence process; at least one active survivor has
a legal alternative assignment covering the vacated duty; the focal flexible
agent is selected by the evaluator from current physical state.

Both certifications require the focal agent active with a valid incumbent
commitment. At most **one pre-registered qualifying event of each type per
episode** enters the audit (else cluster all events at episode and topology
level — one rule, chosen at freeze, not per run).

## 3. Horizons — per mechanism, event-anchored

```text
H_stable = 139   from the certified stable check   (transit window, unchanged)
H_flex   = 450   from the first certified charge-handoff check
                 (charge-duration + transit mechanism window)
H = 1500         secondary whole-episode diagnostic only: verifies energy
                 binds, describes rotation-system consequences, supports
                 end-to-end G2 source controls. Never the gate.
```

If an event lacks full `H_m` remaining source support, that episode is
right-censored or ineligible under a support rule frozen here; the horizon is
never shortened post hoc.

## 4. Normalizers — per mechanism, event-aligned, treatment-independent

`B_stable`: constructive-minus-null measured on **stable-mechanism source
controls** whose windows begin at certified stable checks.
`B_flex`: same contrast on **charge-handoff source controls** whose windows
begin at certified handoff events.

Both come from a **disjoint source-control/calibration episode block** —
never from treatment-arm data, never from a reset-to-end window. The
reset-to-end whole-episode `B` remains a descriptive headroom diagnostic.

## 5. External return `G` — the registered safety score

Primary `G` is the registered G2 PBRS-free per-step safety score, summed over
the window:

```text
G_t = qos_satisfaction_ratio - 2*return_cost - 5*new_cutoff - 10*new_depletion
```

The unclipped rate ratio is retained as a **secondary mechanism-localization
metric**, reported with the safety-score components, never gated on. The
reset-state clipped saturation probe is retired as a validity test and kept
only as the historical record of the clipped proxy's retirement.

## 6. Gate — linear contrasts with interval conditions

```text
T_stable = U*_stable,src + 0.10 * B_stable
T_flex   = U*_flex,src   - 0.10 * B_flex

stable limb clears  iff  UCB95(T_stable) < 0  and  LCB95(B_stable) > 0
flex limb clears    iff  LCB95(T_flex)   > 0  and  LCB95(B_flex)   > 0
```

No ratio gates, no point-only gates. Ratios may be reported descriptively
where the corresponding `B_m` interval excludes zero. Prospective only: the
ep64 record is not relabeled.

Uncertainty is a **hierarchical bootstrap**: resample topologies first, then
episodes/qualifying events within each selected topology. The gate reads the
topology-population contrasts; per-topology margins are mandatory diagnostics.

## 7. Arms and controls

| Arm | Meaning |
|---|---|
| `constructive_mixed` | holds stable assignments while renewing flexible ones — the design's constructive controller, correctly realized |
| `null` | no renewal |
| `full_sync_SET` | reassigns every duty at each check — **conformance diagnostic only** |
| `KEEP_m` / `SET_m` | the focal one-`Delta` interventions of section 1, per mechanism |

CRN and fresh-environment-per-arm are retained: every arm starts from an
identical pre-intervention history, topology, energy assignment, user-motion
stream and random state, and the complete pre-intervention state is
**checked, not assumed**. Topology is pinned per instance by the mechanism
that actually works in this repository: construction, then
`reset(seed=topology_seed)`, then explicit `_init_ground_bs()` and
`_init_charging_stations()` — construction-time draws alone are NOT
seed-determined (defect 4a). The conformance derivation (evidence action 1)
must prove seed-to-coordinates determinism under this mechanism.

## 8. Result branches — all reachable or explicitly owned

| Branch | Fires when | Consequence |
|---|---|---|
| `PERSISTENCE_NECESSARY_SOURCE` | both limbs clear | D7.3 proceeds |
| `MATERIAL_STABLE_PERSISTENCE_IDENTIFIED` | stable clears, flex does not | partial: one commitment class has material value; no heterogeneous-urgency claim; D8 stays blocked |
| `SOURCE_NECESSITY_UNRESOLVED` | anything else | stays unresolved; no automatic budget expansion without a pre-frozen expansion rule |
| `PART_A_CONTRADICTION` | `full_sync_SET` matches the mixed constructive optimum | reopens the Part A structural ruling; invalidates downstream reads until resolved |

`ZERO_COST_ROLE_EXCHANGE_SOURCE` is no longer an advertised executable
branch: Part A owns that certificate, and its failure mode surfaces as
`PART_A_CONTRADICTION` through the conformance arm.

## 9. Topology population — the paper-level scope

- at least **8 fresh topology seeds**, excluding `20260725` (development
  topology — instrument-contaminated, reserved for the proof-sized exercise
  with no scientific reading);
- 8 audit episodes per topology, equal topology weighting;
- a disjoint calibration block per topology for `B_stable`/`B_flex`;
- actual BS/charging-station coordinates (or their hash) recorded in every
  result artifact, not merely the seed;
- standing provenance rule (repository-wide): any Scenario-7 result reused as
  a causal comparator or paper-level premise must establish shared topology
  or scope its claim to its realized/unknown topology; audited on reuse.
  This section records the rule's origin; its standing home is `AGENTS.md`
  (*Result interpretation*), which the reuse path actually reads.

## 10. Pre-freeze check (AGENTS.md), answered against this draft

1. *Signals at entry:* evaluation-only; no learning signal exists. The gate
   quantities are estimated from returns; nothing is trivially zero because
   KEEP and SET branches genuinely differ at any certified history where a
   legal alternative exists — certification (section 2) guarantees one.
2. *Gradient paths:* none — no trainable parameters.
3. *Trivially satisfied invariants:* `set_flex ≡ constructive` is abolished
   by construction — both limbs use the same explicit focal intervention;
   arm-identity is proven in the conformance derivation (evidence action 1),
   which must show the five arms pairwise distinct on a witness history.
4. *Branches firing non-scientifically:* `SOURCE_NECESSITY_UNRESOLVED` on
   zero qualifying events is a support failure, not a margin reading — the
   result artifact must report qualifying-event counts per topology so an
   empty support set is visible as such.
5. *Initialization/credit cancellation:* not applicable; no credit rule.

## 11. What this contract does not authorize

Implementation, compute, or any change to Part A, D0's estimand hierarchy,
or closed results. After Pro freezes this contract: evidence action 1 is a
zero-compute derivation; action 2 is a proof-sized exercise on `20260725`;
action 3 is the single joint audit, which requires its own compute gate and
prelaunch note under standing authority.
