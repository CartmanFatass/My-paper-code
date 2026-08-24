# Isolated research candidates

This directory contains proof-sized candidate experiments that are not part of
the production HA-CTSE runtime. Each candidate owns one subdirectory containing
only its local schema, deterministic treatment, and executable evidence logic.

- Production code must not import candidate modules.
- Tests mirror the candidate path under `tests/experiments/candidates/`.
- Public science-to-code evidence lives under `docs/research/candidates/`.
- Code moves into `ha_ctse_process/` only after a separate production-integration
  task identifies a real shared consumer.
- Parked, retired, or replaced candidates are deleted as a complete family; Git
  is the archive. Compatibility wrappers and historical-code directories are
  not created.

## Code-to-science navigation

Start at the nonauthoritative
[`research-direction registry`](../../docs/HR/RESEARCH_DIRECTION_REGISTRY.toml)
for the current object, queue, owner, and exact owner evidence. The rows below
are backlinks from code to that projection. They do not make any candidate a
dependency of `ha_ctse_process/`; `docs/project/PROJECT_MAP.md` remains the sole
stable architecture map.

| Direction ID | Implementation path represented here | Boundary |
|---|---|---|
| `acvc` | `experiments/candidates/acvc` | isolated experiment |
| `commitment_residual_triggered_options` | `experiments/candidates/commitment_residual_triggered_options` | isolated experiment |
| `covariance_calibrated_information_clock` | `experiments/candidates/covariance_calibrated_information_clock` | isolated, current object unclosed |
| `degraded_incumbent_shadow_handover` | `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06` | production-capable isolated candidate, not default route |
| `dual_epoch_receipt_survival` | `experiments/candidates/dual_epoch_receipt_survival` | isolated experiment |
| `ec4g_r1` | `experiments/candidates/ec4g_r1` | isolated, B1 code not accepted |
| `eociv_lite` | `experiments/candidates/eociv_lite` | isolated experiment |
| `event_triggered_budgeted_cooperative_renewal` | `experiments/candidates/ebcr_variable_k` | isolated experiment |
| `expressibility_gated_renewal_credit_relay` | `experiments/candidates/expressibility_gated_renewal_credit_relay` | isolated experiment |
| `metric_ground_transport_allocation` | `experiments/candidates/metric_ground_transport_allocation` | isolated experiment |
| `opportunity_normalized_lease_gated_rebinding` | `experiments/candidates/opportunity_normalized_lease_gated_rebinding` | production-capable isolated candidate, not default route |
| `optimizer_entropy_exposure_boundary_relay` | `experiments/candidates/optimizer_entropy_exposure_boundary_relay` | isolated completed experiment |
| `orbit_shadow_read` | `experiments/candidates/orbit_shadow_read` | isolated certificate/experiment |
| `recct_lite` | `experiments/candidates/recct_lite` | isolated experiment |
| `renewal_indexed_score_plasticity` | `experiments/candidates/renewal_indexed_score_plasticity` | production-capable isolated candidate, unarmed |
| `roster_consistent_latent_exploration` | `experiments/candidates/roster_consistent_latent_exploration_tbcfv` | production-capable isolated candidate |
| `roster_smf` | `experiments/candidates/roster_smf` | isolated certificate |
| `scope_1s` | `experiments/candidates/scope_1s` | isolated certificate |
| `semantic_graphon_shared_policy` | `experiments/candidates/semantic_graphon_shared_policy_rscf_r01` | production-capable isolated candidate, current engineering |
| `semigroup_consistent_duration_model_policy` | `experiments/candidates/scdmp_variable_k` | production-capable isolated completed object |
| `ucope` | `experiments/candidates/ucope` | isolated completed B2; current R01 is definition-only |
| `vap_folr_core` | `experiments/candidates/folr_core` | isolated experiment |
| `variable_n_fleet_churn` | `experiments/candidates/variable_n_fleet_churn_bpcr_r09` | historical BPCR predecessor, not current PCPI implementation |
| `voronoi_quadrature_field_policy` | `experiments/candidates/vqfp_vnpa_r03` | production-capable isolated candidate |
| `vsp_02` | `experiments/candidates/vsp_02` | isolated completed experiment |
| `vsp_03` | `experiments/candidates/vsp_03` | isolated certificate |
| `vsp_04` | `experiments/candidates/vsp_04` | isolated certificate |
| `vsp_05` | `experiments/candidates/vsp_05` | isolated certificate |
| `vsp_06_mssr` | `experiments/candidates/vsp_06_mssr` | isolated certificate |
| `vsp_c1` | `experiments/candidates/vsp_c1` | isolated certificate |
