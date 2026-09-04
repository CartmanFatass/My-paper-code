# Isolated research candidates

This directory contains proof-sized candidate experiments that are not part of
the production HA-CTSE runtime. Each candidate owns one subdirectory containing
only its local schema, deterministic treatment, and executable evidence logic.

- Production code must not import candidate modules.
- Tests mirror the candidate path under `tests/experiments/candidates/`.
- Current science-to-code evidence lives under `docs/research/candidates/`; structurally closed or
  absorbed direction evidence lives under `docs/research/legacy/directions/`.
- Code moves into `ha_ctse_process/` only after a separate production-integration
  task identifies a real shared consumer.
- Historical candidate code may remain versioned for reproduction and accepted controls. Its
  presence does not reactivate a legacy direction or authorize result activity.

## Code-to-science navigation

Start at the current [`research map`](../../docs/research/RESEARCH_MAP.md) and
[`Portfolio`](../../docs/research/portfolio/PORTFOLIO.md). The rows below are code-to-science
backlinks only. They do not make any candidate a dependency of `ha_ctse_process/`;
`docs/project/PROJECT_MAP.md` remains the stable architecture map.

| Direction ID | Implementation path represented here | Boundary |
|---|---|---|
| `acvc` | `experiments/candidates/acvc` | isolated experiment |
| `commitment_residual_triggered_options` | `experiments/candidates/commitment_residual_triggered_options` | isolated experiment |
| `covariance_calibrated_information_clock` | `experiments/candidates/covariance_calibrated_information_clock` | legacy FRRIE control; standalone closed |
| `degraded_incumbent_shadow_handover` | `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06` | production-capable isolated candidate, not default route |
| `dual_epoch_receipt_survival` | `experiments/candidates/dual_epoch_receipt_survival` | legacy CBSC control; standalone absorbed |
| `ec4g_r1` | `experiments/candidates/ec4g_r1` | isolated, B1 code not accepted |
| `eociv_lite` | `experiments/candidates/eociv_lite` | isolated experiment |
| `event_triggered_budgeted_cooperative_renewal` | `experiments/candidates/ebcr_variable_k` | legacy SCDMP branch; no standalone activity |
| `expressibility_gated_renewal_credit_relay` | `experiments/candidates/expressibility_gated_renewal_credit_relay` | isolated experiment |
| `metric_ground_transport_allocation` | `experiments/candidates/metric_ground_transport_allocation` | isolated experiment |
| `opportunity_normalized_lease_gated_rebinding` | `experiments/candidates/opportunity_normalized_lease_gated_rebinding` | legacy SCDMP control; standalone closed |
| `optimizer_entropy_exposure_boundary_relay` | `experiments/candidates/optimizer_entropy_exposure_boundary_relay` | legacy optimizer-history control; standalone absorbed |
| `orbit_shadow_read` | `experiments/candidates/orbit_shadow_read` | isolated certificate/experiment |
| `recct_lite` | `experiments/candidates/recct_lite` | isolated experiment |
| `renewal_indexed_score_plasticity` | `experiments/candidates/renewal_indexed_score_plasticity` | legacy SCDMP branch; standalone absorbed |
| `roster_consistent_latent_exploration` | `experiments/candidates/roster_consistent_latent_exploration_tbcfv` | production-capable isolated candidate |
| `roster_smf` | `experiments/candidates/roster_smf` | legacy FRRIE exact-census control |
| `scope_1s` | `experiments/candidates/scope_1s` | isolated certificate |
| `semantic_graphon_shared_policy` | `experiments/candidates/semantic_graphon_shared_policy_rscf_r01` | legacy FRRIE treatment ancestry |
| `semigroup_consistent_duration_model_policy` | `experiments/candidates/scdmp_variable_k` | production-capable isolated completed object |
| `ucope` | `experiments/candidates/ucope` | isolated completed B2; current R01 is definition-only |
| `vap_folr_core` | `experiments/candidates/folr_core` | isolated experiment |
| `variable_n_fleet_churn` | `experiments/candidates/variable_n_fleet_churn_bpcr_r09` | historical BPCR predecessor, not current PCPI implementation |
| `voronoi_quadrature_field_policy` | `experiments/candidates/vqfp_vnpa_r03` | legacy FRRIE control; current ABI structurally closed |
| `vsp_02` | `experiments/candidates/vsp_02` | isolated completed experiment |
| `vsp_03` | `experiments/candidates/vsp_03` | isolated certificate |
| `vsp_04` | `experiments/candidates/vsp_04` | legacy CBSC diagnostic |
| `vsp_05` | `experiments/candidates/vsp_05` | legacy DISH FSM/veto control |
| `vsp_06_mssr` | `experiments/candidates/vsp_06_mssr` | legacy RCLE partner-memory branch |
| `vsp_c1` | `experiments/candidates/vsp_c1` | isolated certificate |
