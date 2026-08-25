# External Pro open question: UAV G0 formal execution interface

```text
review_type=FORMAL_INTERFACE_CONTRACT_CLARIFICATION
audit_mode=zero_compute_code_facing_contract_only
compute_budget=zero
scientific_iteration_cost=zero
source_commit=9239e3ec8a3d5b0ac3ba078f5598c19bde3c6d43
readiness_execution_commit=3bd7b1c050030d4e2176f3492f4cc4296e0908bb
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

The corrected G0 study has already received `G0_FORMAL_ADMISSION=PROCEED`.
Code Project Manager reports that the accepted runner is still proof-only and
fail-closed: it has no frozen formal authorization token, same-source
nonformal-preflight binding, formal train/evaluate/analyze interface, formal
artifact schema, or formal admission predicates. This question asks for one
complete, code-facing contract that makes the already-admitted study
executable without changing its science.

Return an ASCII-only contract. Start with exactly one of:

`G0_FORMAL_INTERFACE=FROZEN`
`G0_FORMAL_INTERFACE=HOLD`

If `FROZEN`, include all fields below as explicit single-line key/value
records, followed by one ASCII first-failure/admission predicate block:

- `formal_authorization_token` and its exact role (identity gate only; never
  user authorization);
- `runner` and exact `train`, `evaluate`, and `analyze` command shapes;
- fresh same-source `nonformal_preflight_root` and `formal_root` identity rules;
- exact source, aligned-source, execution and alignment-stage identities;
- accepted-anchor/provenance inputs and immutable source requirements;
- CPU backend, fallback prohibition, process/worker count, start method and
  OMP/MKL/OPENBLAS/NUMEXPR/Torch thread controls;
- formal counts: episode IDs, controls, cells, H, K_search, real simulator
  steps, bootstrap resamples and any optimizer/learning/checkpoint status;
- complete terminal artifact inventory and schema/version fields;
- ordered admission gates, first-failure stop semantics, fresh-root rule and
  formal=false preflight boundary.

Every result-sensitive field must be frozen from the allow-listed contract.
Do not invent a new scientific control, threshold, estimator, geometry,
ownership rule or result criterion. Do not claim that readiness evidence is a
scientific result. If any required code-facing field cannot be frozen without
scientific invention, return `G0_FORMAL_INTERFACE=HOLD` and name only those
missing fields. Do not propose compute, redesign, or a successor action.
