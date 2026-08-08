# UCOPE acquisition park certificate: code-science index

Candidate: `CAND-VSP-07-UCOPE@adversarial-parked-v7`

Treatment: archival deterministic `UCOPE-ACQ-PARK-CERT`

Status: executable park evidence only. It certifies the exact algebra of the
2026-08-05 external adversarial review that parked the forced-balanced
acquisition route (terminal `PARK_SCIENTIFICALLY`). It establishes no task
return, no acquisition value, no transfer, no retirement, no joint
exploration, and nothing beyond the registered complementary-hazard
fixed-window family. The module performs no training, no rollout, no
sampling, no RNG use and no floating arithmetic.

## Frozen contract

The registered family constants are read off the externally accepted
`UCOPE-COUNT-STATE-D1` (`experiments/candidates/ucope/exact_enumerator.py`)
and bound by test: hazards 9/10 aligned / 1/10 misaligned, prior 1/2,
per-trial horizon `H=3`, durations `d_S=1`, `d_L=2`, per-trial coverage
reset, block-persistent `Theta`. The certificate operates on the pooled
evidence statistic `Z` (posterior odds `9^Z`); pooling admissibility (cells
share one `Theta`-conditional hazard) is a D1 family fact
(`HazardTable.probability` takes no cell argument), not a claim this
certificate re-certifies.

Registered policies over `4+T` trials, `T in {0,1,2,3,4}`:

- `pi_CAL`: forced `S,S,L,L`, then `T` trials of the count-informed rule
  (`S` iff `Z >= 0`; the score tie sits at posterior odds `7/17`, which the
  helper derives from the family's own score algebra and verifies is not a
  reachable power of the likelihood ratio over the scanned range).
- `pi_PASSIVE`: forced `S,S,S,S`, retaining outcomes, then the same rule.
- `pi_GREEDY`: the rule on all `4+T` trials from cold start.
- `pi_CB`: always `S`, never reading the ledger.

## Certified statements

1. **Action-equivalent signals.** `Pr(evidence toward S | Theta)` is the
   same for both actions (`9/10` under `Theta=S`, `1/10` under `Theta=L`),
   so period choice never changes the information kernel. This is a
   consequence of the complementary hazards `9/10 + 1/10 = 1` and is
   disclosed as family-specific (a non-complementary perturbation breaks it
   in a dedicated negative test).
2. **Posterior-law coupling.** The joint `(Theta, Z_4)` law after the
   `SSLL`, `SSSS` and `GREEDY` prefixes is identical (exact dict equality
   over support `Z in {-4,-2,0,2,4}`, mass exactly 1).
3. **Dominance identities.** `V_CAL - V_PASSIVE = -1` and
   `V_CAL - V_GREEDY = -9107/5000` for every registered `T`.
4. **No horizon rescue.** `G_T = CumRegret_T(B0) - E[CumRegret_T(B4)] <=
   CumRegret_T(B0) <= 156978910907/250000000000 < 1` for EVERY `T`,
   because per-trial regret is certified nonnegative pointwise (so
   `CumRegret_T` is nondecreasing in `T`) and the bound is the exact
   occupancy regret of the first 12 decision trials plus a rational Markov
   tail from `E[3^(-Z_t) | Theta=S] = (3/5)^t` and its mirror (thresholds
   `(3/5)^t/3` under `Theta=S`, `(3/5)^t` under `Theta=L`). Hence
   `N_T = G_T - 1 < 0` universally: no decision horizon repays the forced
   prefix cost. The occupancy path and the value-DP path are certified to
   agree exactly at `t0=12`, and the bound is certified to dominate every
   enumerated prefix horizon. The non-registered constant `5/8` is only
   sandwiched between the exact `T=12` regret and the rigorous bound; the
   certificate's all-`T` ceiling is `156978910907/250000000000`, and `5/8`
   is NOT certified as an upper bound.

The `CAL-CB` table is retained ONLY under its corrected name
`total forced-prefix count-adaptive commitment value versus count-blind S`:
negative at `T=1,2`, positive at `T=3` (`11651/1000000`) and `T=4`
(`1791887/5000000`). The `T=3` sign crossing is a count-adaptive-versus-
count-blind commitment result, not an acquisition threshold.

Corrected boundaries replace the falsified pairwise-zero claims: under
homogeneous hazards `1/2` and under coherent independent per-trial redraw,
`V_CAL = 3+T` while `V_PASSIVE = V_GREEDY = V_CB = 4+T` and `G_T = 0` (both
branches fully computed). The severance identity
`V_CAL(T) - V_CAL_severed(T) = G_T` is computed with the severed cold tail
going through the independent full-tree path, so the identity is not a
syntactic cancellation; it certifies that the prefix-law kernel and the
value DP agree.

All arithmetic is `fractions.Fraction`. A leaf-complete full-tree
enumeration (`2^(5+T)` leaves including `Theta`, mass exactly 1) reproduces
the CAL/PASSIVE/GREEDY dynamic-program values exactly (Fraction equality)
under the primary family; `v_cb` is structurally `4+T` and is pinned by
test rather than tree-checked.

## Traceability

|claim_id|frozen_assertion|code_path::symbol|observable_invariant|focused_test|
|---|---|---|---|---|
|UCOPE-PARK-01|action-equivalent signals|`acquisition_park_certificate.py::HazardFamily.evidence_up`|`lemma1_action_equivalent_signals`|`test_posterior_law_coupling_makes_prefix_actions_informationally_equal`|
|UCOPE-PARK-02|posterior-law coupling|`::prefix_belief_law`|`lemma2_posterior_law_coupling`|`test_posterior_law_coupling_makes_prefix_actions_informationally_equal`|
|UCOPE-PARK-03|passive dominance -1|`::v_cal, ::v_passive`|`lemma3_passive_dominance`|`test_dominance_identities_hold_for_every_registered_horizon`|
|UCOPE-PARK-04|greedy dominance -9107/5000|`::v_greedy`|`lemma3_greedy_dominance`|`test_dominance_identities_hold_for_every_registered_horizon`|
|UCOPE-PARK-05|no horizon rescue|`::no_horizon_rescue_bound, ::cumulative_regret`|`lemma4_no_horizon_rescue`, `lemma4_regret_nonnegative_pointwise`, `lemma4_partial_regret_paths_agree`, `lemma4_bound_dominates_prefix_horizons`|`test_regret_machinery_is_pinned_exactly_and_nonnegative`|
|UCOPE-PARK-06|exact policy tables|`::run_certificate`|`exact_cal_table`, `exact_cb_table`, `exact_greedy_anchor`|`test_exact_policy_value_tables_match_review_algebra`|
|UCOPE-PARK-07|commitment naming and signs|`::CertificateResult.to_bytes`|`commitment_signs`|`test_commitment_contrast_signs_and_threshold_are_exact`|
|UCOPE-PARK-08|information tables G/N|`::gross_information_value`|`exact_information_table`|`test_gross_and_net_information_values_are_exact_and_never_recover_cost`|
|UCOPE-PARK-09|corrected boundaries|`::v_cal(HOMOGENEOUS/reset_belief), ::v_cal_severed`|`homogeneous_boundary_corrected`, `independent_redraw_boundary_corrected`, `severance_boundary_ties_g`|`test_corrected_boundaries_replace_the_false_pairwise_zero_claims`|
|UCOPE-PARK-10|full-tree cross-check|`::full_tree_value`|`full_tree_cross_check`|`test_full_tree_enumeration_cross_checks_the_dynamic_program`|
|UCOPE-PARK-11|tie unreachable, sign rule total|`::_reachable_tie_is_absent, ::rule_action`|`tie_unreachable`, `greedy_rule_is_sign_rule`|`test_greedy_rule_is_total_sign_rule_with_unreachable_tie`, `test_tie_helper_actually_detects_a_forced_tie`|
|UCOPE-PARK-12|D1 numeric arbitration|`::v_cal, ::gross_information_value`|(cross-artifact)|`test_certificate_reproduces_the_externally_accepted_d1_numbers`|
|UCOPE-PARK-13|byte-stable park terminal|`::CertificateResult.to_bytes`|`no_identity_fields`|`test_canonical_output_is_byte_stable_compact_and_park_terminal`|

## Bounded execution

```text
python experiments/candidates/ucope/acquisition_park_certificate.py  (single process, deterministic, seconds)
python -m pytest tests/experiments/candidates/ucope/ -q
...........................                                              [100%]
27 passed in 11.01s
```

No environment step, rollout, training, optimizer update or reward estimate
is executed anywhere in this treatment.

## FULL_RAW_JSON

```json
{"binding":"ucope.acquisition_park_certificate.v1","commitment_value_vs_count_blind_S":[{"CAL_minus_CB":"-1","T":0,"V_CAL":"3","V_CB":"4"},{"CAL_minus_CB":"-13429/20000","T":1,"V_CAL":"86571/20000","V_CB":"5"},{"CAL_minus_CB":"-165861/500000","T":2,"V_CAL":"2834139/500000","V_CB":"6"},{"CAL_minus_CB":"11651/1000000","T":3,"V_CAL":"7011651/1000000","V_CB":"7"},{"CAL_minus_CB":"1791887/5000000","T":4,"V_CAL":"41791887/5000000","V_CB":"8"}],"greedy":[{"T":0,"V_GREEDY":"24107/5000"},{"T":1,"V_GREEDY":"122999/20000"},{"T":2,"V_GREEDY":"3744839/500000"},{"T":3,"V_GREEDY":"8833051/1000000"},{"T":4,"V_GREEDY":"50898887/5000000"}],"information":[{"G":"0","N":"-1","T":0},{"G":"6571/20000","N":"-13429/20000","T":1},{"G":"219139/500000","N":"-280861/500000","T":2},{"G":"506651/1000000","N":"-493349/1000000","T":3},{"G":"2684887/5000000","N":"-2315113/5000000","T":4}],"invariants":{"ceiling_containment":true,"commitment_signs":true,"decision_phase_learning_table":true,"exact_cal_table":true,"exact_cb_table":true,"exact_greedy_anchor":true,"exact_information_table":true,"full_tree_cross_check":true,"greedy_rule_is_sign_rule":true,"homogeneous_boundary_corrected":true,"independent_redraw_boundary_corrected":true,"lemma1_action_equivalent_signals":true,"lemma2_posterior_law_coupling":true,"lemma3_greedy_dominance":true,"lemma3_passive_dominance":true,"lemma4_bound_dominates_prefix_horizons":true,"lemma4_no_horizon_rescue":true,"lemma4_partial_regret_paths_agree":true,"lemma4_regret_decomposition":true,"lemma4_regret_nonnegative_pointwise":true,"no_identity_fields":true,"severance_boundary_ties_g":true,"tie_unreachable":true},"no_rescue_bound":"156978910907/250000000000","terminal":"PARK_CONFIRMED_FORCED_BALANCED_ACQUISITION_ROUTE"}
```

RAW_OUTPUT_BINDING: `ucope.acquisition_park_certificate.v1`
