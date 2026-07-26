# G33 localized-demand-burst design assertion audit brief

```text
semantic_author=project_manager
artifact_scope=reviewer_visible_scientific_boundary
scientific_authority=external_pro
repair_owner=project_manager
review_mode=DESIGN_ASSERTION_AUDIT
round=20260725_uav_localized_demand_burst_g33_design_assertion_audit
formal_compute_authority=none
```

## Purpose

Formal G31 and G32 produced a usable toy algorithm for continuous roster
control across a configured capacity fixed before each trajectory. External
Pro selected one source-identifiability audit, not another learned run, as the
next action: `UAV_LOCALIZED_DEMAND_BURST_G33_DESIGN_ASSERTION_AUDIT`.

This round asks External Pro to freeze or reject exactly one localized
temporary demand-burst source under the unchanged Scenario-7 S7-S1 physics and
external reward. The audit must establish before implementation that current
demand is sufficient for future-blind reaction, that the source requires
post-onset UAV spatial reallocation, and that a fixed pre-burst layout cannot
obtain the registered access-level result.

## Inherited binding boundary

The G32 scientific disposition already binds the following facts:

```text
base_physics=S7-S1_unchanged
physical_fleet=8
service_roster=constant_8_for_this_source
external_reward=existing_scenario7_task_reward
future_burst_ledger_visibility=forbidden
current_demand_visibility=required
desired_uav_assignment_visibility=forbidden
intrinsic_reward_change=forbidden
learned_training_in_this_action=none
```

The required controls are a future-blind constructive controller, a
ledger-blind no-reallocation controller, a full-ledger physical reachability
oracle used only for feasibility, and an information/exposure-matched ordinary
recurrent null for a possible later learned comparison.

## Current code facts that constrain the scientific choice

- S7-S1 has eight UAVs, thirty users and 500 steps. Battery, charging and
  temporary failure are disabled in this stage.
- The task utility is the mean clipped ratio of delivered per-user rate to one
  currently uniform `user_qos_rate_mbps` target. The unchanged external reward
  also retains the existing return-safety penalties and graph PBRS.
- End-to-end rate is calculated from current connections, per-UAV access
  bandwidth sharing and the current backhaul bottleneck.
- Each actor currently sees local user relative position, SINR, whether the
  user is connected to self and whether it is serviced by any UAV. There is no
  current per-user demand field and no burst ledger.
- The centralized state contains current physical user/UAV/network state but
  no burst-specific demand or future schedule.

Consequently, “per-user demand” is not an implementation-only label. External
Pro must freeze its exact physical and utility semantics: for example, whether
it changes the per-user QoS requirement, offered traffic/capacity allocation,
or another explicitly defined quantity. PM must not infer this choice from the
word “burst.” Actor and critic demand fields must then expose only the current
realized quantity needed by that definition.

## Design decision needed

External Pro must either return one fully executable, source-identifiable G33
contract or close this exact source. A valid contract must supply exact values
for the complete result-sensitive field set from the G32 disposition,
including source supports, utilities, controls, confidence construction and
first-match semantics. It must also give the explicit relevant optimal-policy
set, positive/negative witnesses and the argument that every access-level
solution performs post-onset spatial service reallocation.

The audit may not use a fixed known burst region, absolute-time prepositioning,
future or assignment leakage, or ordinary-demand sacrifice hidden outside the
guardrail. It may not change S7-S1 physics, external reward, G31/G32, the two
closed UAV sources, or the project claim into dynamic membership.

No code implementation, source diagnostic, learned training, formal compute or
conclusion-bearing iteration is part of this round.
