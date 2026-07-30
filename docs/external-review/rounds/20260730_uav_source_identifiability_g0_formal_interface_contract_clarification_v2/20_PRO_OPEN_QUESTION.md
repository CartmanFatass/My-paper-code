# External Pro open question: complete UAV G0 formal interface contract v2

```text
review_type=FORMAL_INTERFACE_CONTRACT_CLARIFICATION_V2
audit_mode=zero_compute_code_facing_contract_only
compute_budget=zero
scientific_iteration_cost=zero
source_commit=83bad9ebf489d24cb67ad30e10905cb0eb84f04a
accepted_g0_source_commit=9239e3ec8a3d5b0ac3ba078f5598c19bde3c6d43
readiness_execution_commit=3bd7b1c050030d4e2176f3492f4cc4296e0908bb
prior_interface_round=20260730_uav_source_identifiability_g0_formal_interface_clarification
prior_interface_disposition=G0_FORMAL_INTERFACE=HOLD
code_science_alignment_correction_recheck_stage_commit=58d67c7245877e3e6ef98a2898dfa5e1d26c80e4
code_science_alignment_correction_recheck_disposition=ALIGNED
formal_admission=G0_FORMAL_ADMISSION=PROCEED
formal_compute_started=false
allowed_outputs=G0_FORMAL_INTERFACE=FROZEN|G0_FORMAL_INTERFACE=HOLD
```

You are External GPT-5.6 Pro and the exclusive scientific authority inside
this bounded clarification. Use the connected GitHub repository connector for
`https://github.com/CartmanFatass/My-paper-code.git`, branch `aggressive`.
Read only the allow-list in `01_SHARED_SOURCE_MANIFEST.md` at the exact
`source_commit`. Do not use a local working tree, runtime logs, CURRENT_WORK,
workflow files, or compute. Do not activate Answer now and do not provide a
Chinese summary.

The prior response returned `G0_FORMAL_INTERFACE=HOLD` and named only the two
alignment identity fields. Those fields are now explicitly frozen above. This
v2 question asks for the complete code-facing contract required to implement
the already admitted G0 study. Do not infer or invent science; copy only
mechanically frozen values from the allow-listed contract and source.

If the contract is complete, return ASCII-only text beginning exactly with
`G0_FORMAL_INTERFACE=FROZEN` and then one-line key/value records for every
field below, followed by one ordered first-failure/admission predicate block:

- `formal_authorization_token` and its exact role (identity gate only; never
  user authorization);
- runner identity and exact `train`, `evaluate`, and `analyze` command shapes;
- fresh same-source nonformal-preflight and formal-root identity rules;
- exact source, accepted/aligned source, execution and alignment-stage
  identities;
- accepted-anchor/provenance inputs and immutable source requirements;
- CPU backend, Python-fallback prohibition, CPU budget/process workers, worker
  start method, deterministic merge and OMP/MKL/OPENBLAS/NUMEXPR/Torch thread
  controls;
- formal episode IDs, controls, cells, H, K_search, real simulator steps,
  bootstrap resamples, and learning/optimizer/checkpoint status;
- complete terminal artifact inventory with schema/version fields;
- ordered admission gates, first-failure stop, fresh-root rule, and the
  formal=false same-source preflight boundary.

The response must also state whether any field remains unfrozen. If any
result-sensitive field cannot be frozen without scientific invention, return
`G0_FORMAL_INTERFACE=HOLD` and list only those exact missing fields. Do not
propose compute, redesign, a new control, threshold, estimator, geometry,
ownership rule, or successor action.
