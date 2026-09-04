# experiments/ — research candidates

Research-tier code (`docs/project/ENGINEERING_SCOPE_SPEC.md` §2): runnable now, readable later,
disposable when its scientific object closes. No compatibility obligation between attempts. Core
packages (`hmasd/`, `ha_ctse_process/`, `envs/`) must not import from here; the three imports that
`envs/native/production_backend.py` still makes are recorded defects, not precedent.

## Layout rule for new work

```
experiments/candidates/<direction-id>/<attempt>/     code of one scientific object
tests/experiments/candidates/<direction-id>/<attempt>/   its tests, mirroring exactly (never flattened)
scripts/run_<prefix>_<attempt>.py                    its runner (prefix column in docs/research/RESEARCH_MAP.md)
temp/directions/<direction-id>/exp/<attempt>_<run>/  its output (ignored)
```

`<direction-id>` is the directory name under `docs/research/candidates/`. `<attempt>` is the
science-card id in lower snake case (`omrc_b01`, `bpcr_r09`, `e2_interruption_cost`). Code shared
by a direction's attempts lives at `experiments/candidates/<direction-id>/` itself (`ucope/` is
the example). Existing directories are never moved: their paths are bound into launch shas,
runner argv and evidence documents.

What an attempt must contain, and what it must not, is in the scope spec §3–§5: one runner with
`argparse` and a seed, one `summary.json` per run, the resource-admission receipt, one smoke test
under 60 s plus rule tests; no orchestration, guards, receipts, witnesses, resume machinery,
schema validators, registries or telemetry beyond wall time and peak RSS unless a card line names
the need. Budgets: 2,000 new lines per attempt, 600 per runner, orchestration under 30% of a diff.

Native backends: a candidate that needs C++ ships its own `native_backend.py`/`native_loader.py`
(most do) or reuses `envs/native/cpp_extension_cache.py`; the first run compiles through the
PyTorch JIT loader, keyed by a source hash, so the first test touching it is slow. Check the
direction's contract before switching device: CPU is sometimes scientifically invalid, not merely
slower (`docs/project/PROBLEM_CACHE.md` P1b).

Execution placement inherits the repository's `.codex/hmasd-compute.toml` remote-first policy.
The card fixes host/device portability before launch; a Windows-only native backend, a device-bound
numerical contract, or a different RNG/device semantic is a real pin, not a reason to silently
change the experiment. Portable committed attempts use an exact-sha remote worktree and the
destination node's fresh admission; existing live local attempts are never moved or duplicated.

## Directory map (2026-09-03)

Status: `current` = the directory `RESEARCH_MAP.md` links for a live direction; `prior` = a
superseded attempt of a live direction (kept, not maintained); `legacy` = code of one of the 14
closed or absorbed labels (`docs/research/legacy/directions/README.md`); `imported` = a prior or
legacy directory that `production_backend.py` still loads; `dormant` = not a candidate.

| Directory | Direction id | Status |
| --- | --- | --- |
| `acvc` | acvc | current |
| `capability_bound_semantic_currentness` (+ `omrc_b01/`, `online/`) | capability_bound_semantic_currentness | current |
| `capability_bound_semantic_currentness_learnability_r01` | capability_bound_semantic_currentness | current |
| `commitment_residual_triggered_options` | commitment_residual_triggered_options | prior |
| `commitment_residual_triggered_options_common_history_gate_r01` | commitment_residual_triggered_options | current |
| `covariance_calibrated_information_clock` | (legacy label) | legacy |
| `degraded_incumbent_shadow_handover_rbhr_r05` | degraded_incumbent_shadow_handover | prior |
| `degraded_incumbent_shadow_handover_rbhr_r06` | degraded_incumbent_shadow_handover | current |
| `dual_epoch_receipt_survival` | (legacy label) | legacy |
| `ebcr_variable_k` | event_triggered_budgeted_cooperative_renewal (legacy) | legacy |
| `ec4g_r1` | ec4g_r1 | current |
| `eociv_lite` | eociv_lite | current |
| `expressibility_gated_renewal_credit_relay` | expressibility_gated_renewal_credit_relay | current |
| `finite_resource_relational_inductive_efficiency` (+ `b01/`, `contracts/`, `controls/`, `native/`) | finite_resource_relational_inductive_efficiency | current |
| `finite_semantic_boundary_support` | (legacy label) | legacy |
| `folr_core` | vap_folr_core | current |
| `metric_ground_transport_allocation` | metric_ground_transport_allocation | current |
| `opportunity_normalized_lease_gated_rebinding` (+ `b2/`, `b3/`, `headland90/`, `tbvuus_r03/`) | (legacy label) | legacy, imported (`headland90`, `tbvuus_r03`) |
| `optimizer_entropy_exposure_boundary_relay` | (legacy label) | legacy |
| `orbit_owner_match` | orbit_shadow_read | prior |
| `orbit_shadow_read` | orbit_shadow_read | current |
| `recct_lite` | recct_lite | current |
| `renewal_indexed_score_plasticity` (+ `event_conditioned_bayes_r01/`) | (legacy label) | legacy, imported |
| `roster_consistent_latent_exploration`, `_b2`, `_cpc`, `_pcpv` | roster_consistent_latent_exploration | prior |
| `roster_consistent_latent_exploration_tbcfv` | roster_consistent_latent_exploration | current, imported |
| `roster_smf` | (legacy label) | legacy |
| `scdmp_variable_k/foundation_conditioned_event_order_value` | semigroup_consistent_duration_model_policy | current |
| `scdmp_variable_k/{b2_relation_specificity, b3_stability_first, graded_order_value_diagnostic_r01, multifoundation_reachable_order_value, support_representation_factorial, target_bound_order_to_value}` | semigroup_consistent_duration_model_policy | prior |
| `scdmp_variable_k/{target_bound_competent_controller_order_value, uav_suspended_payload_order_value}` | semigroup_consistent_duration_model_policy | prior, imported |
| `scope_1s` | scope_1s | current |
| `semantic_graphon_shared_policy`, `_r06`, `_rg2z_r03`, `_rscf_gate_a` | (legacy label) | legacy |
| `semantic_graphon_shared_policy_rscf_r01` | (legacy label) | legacy, imported |
| `ucope/contextual_paid_acquisition_r01` (+ shared modules at `ucope/`) | ucope | current |
| `ucope/{competence_first_scout_r01, conditioning_discriminator_r01}` | ucope | prior |
| `ucope/variable_k_paid_probe_r01_r03` | ucope | prior, imported |
| `variable_n_fleet_churn`, `_b2`, `_b3`, `_b_explore`, `_r02` | variable_n_fleet_churn | prior (`_r02` is the 2026-09-03 R02 runner host) |
| `variable_n_fleet_churn_bpcr_r09` | variable_n_fleet_churn | current, imported |
| `voronoi_quadrature_field_policy`, `_r05_measurement`, `vqfp_frrie_action_codec` | (legacy label) | legacy |
| `vqfp_vnpa_r03` | (legacy label) | legacy, imported |
| `vsp_02`, `vsp_03`, `vsp_c1` | vsp_02, vsp_03, vsp_c1 | current |
| `vsp_04`, `vsp_05`, `vsp_06_mssr` | (legacy labels) | legacy |
| `continuous_alice_bob/`, `launchers/`, `optuna/` (not under `candidates/`) | — | dormant |
| `../gnn_hmasd/`, `../manifold_hmasd/` | — | dormant lineages, reachable only from `tools/analysis/rollout_and_collect.py` and `train_vae.py` |

The duration direction `flexible_skill_duration` has no candidate directory: its D2 lives on
the base route (`hmasd/agent.py`) and its host under `envs/relay_corridor/`.

Update this table when `RESEARCH_MAP.md` changes a direction's primary implementation, when an
attempt is added, or when a `production_backend.py` import is removed.
