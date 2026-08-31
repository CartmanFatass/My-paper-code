# FRRIE implementation threshold

Status: `RESULT_BLIND_SCAFFOLD_COMPLETE_PRODUCTION_CHAIN_MISSING`

The first object is fixed-roster per episode with adaptation-free held-out-size evaluation. It does
not exercise join, leave, rejoin, replacement, or within-episode churn and cannot support those
claims.

## Single learned host

Use a fresh FRRIE-owned `RIDGEGATE-2Z/RSCF` object. No historical SGSP seed, checkpoint,
update-154 state, result, threshold, or run-control state transfers.

Exactly two learned arms exist:

- `PHY_TRUST`: projects the relational residual `beta` to `[-0.15, 0.15]`;
- `EDGE_FLEX`: projects the same residual to `[-1.50, 1.50]`.

`UNIFORM_LEGAL` is evaluation-only. Both learned arms use the same 35,513-parameter actor/critic and

\[
\omega_{ab}(n)=K^0_{ab}(n)\exp(\beta_{ab,0}+\beta_{ab,1}v(n)).
\]

Only the projection box differs. Inclusion is literal and `beta=0.60` is the strict-capacity
witness. Both arms receive the same 22-field entity observations, public physical/role relations,
messages, masks, recurrent history, and tapes. Entity/slot identity, arm label, hidden/future
outcomes, reward decomposition, and result-derived features are forbidden.

## Work, cells, and endpoint

Freeze bit-identical initialization, minibatch order, potential outcomes, 512 updates, 64 episodes
per update split over train `N={9,15}`, one backward/Adam step per update, checkpoint opportunities,
and 256 evaluations per cell. Each seed block is one inferential unit. Use at most 24 fresh blocks.

Evaluate adaptation-free at held-out `N={6,21}` and under symmetric
`SEMANTIC_COLUMN_ROTATE` while simulator physics, observations, reward, and tapes stay fixed. The
native endpoint is

\[
J=0.65(D_W+D_E)/6+0.25\min(D_W,D_E)/3+0.10(1-\mathrm{WASTE}).
\]

Primary fixed-work estimand is the minimum held-out `PHY_TRUST - EDGE_FLEX` native-return contrast at
update 512. Any work-to-threshold claim requires prospectively frozen checkpoints and thresholds;
missing values invalidate the manifest.

Match environment slots, learned decisions, backward calls, parameter bytes, FLOPs, workers,
threads, native width, dtype, checkpoint I/O, and evaluation opportunities. CPU/native FP32 and
float64 reductions are fixed; no GPU or network. Fresh resource preflight is required before result
activity.

## Output-disconnected controls

- FRRIE-owned CCIC arity-three typed-wedge compiler fixture;
- exact `Fraction` EGRCR pair-aware conditional-Q/Rao--Blackwell equality fixture;
- immutable intact/reassociated raw-value rows whose opposite labels force balanced accuracy `1/2`;
- FRRIE-owned VQFP LR, `MARG0`, marginal-heap, utility, MASS/MASS-P, and half-cycle-reassociation
  fixtures.

No FRRIE file imports historical VQFP packages or native libraries. Historical coefficients,
partial panels, retained operations, and result polarity do not enter fixtures.

## New implementation surface

```text
experiments/candidates/finite_resource_relational_inductive_efficiency/
  contracts/core.py
  contracts/ccic_control.py
  contracts/egrcr_control.py
  contracts/vqfp_controls.py
  controls/raw_value.py
  rng.py
  host.py
  arms.py
  checkpoint.py
  runner.py
  analysis.py
  lifecycle.py
  fixtures/*.json
  cli.py
  __main__.py

tests/experiments/candidates/finite_resource_relational_inductive_efficiency/
  test_contract_and_containment.py
  test_native_host_and_endpoint.py
  test_pair_work_and_rng.py
  test_checkpoint_resume.py
  test_controls.py
  test_analysis_and_lifecycle.py
  test_dependency_firewall.py
```

Key API includes manifest validation, native host admission, factual/shadow trajectories,
bit-identical pair initialization, parity audit, paired update receipts, deterministic checkpoint
serialize/restore, typed-wedge and Rao--Blackwell controls, marginal heap, raw-value control,
sealed-seed execution, and complete-panel analysis.

Schemas are `FRRIE_MANIFEST_V1`, `FRRIE_CHECKPOINT_V1`,
`FRRIE_SEALED_SEED_PACKET_V1`, `FRRIE_COMPLETE_PANEL_RESULT_V1`, and `FRRIE_TERMINAL_V1`. The
manifest binds host/source identities, arms, cells, dtype/native width, workers/threads, updates,
checkpoints, fresh roots, competence/threshold specs, work parity, fixture identities, and resource
ceilings.

## CLI and non-result acceptance

```text
python -m experiments.candidates.finite_resource_relational_inductive_efficiency describe
python -m experiments.candidates.finite_resource_relational_inductive_efficiency check --manifest PATH --output PATH
python -m experiments.candidates.finite_resource_relational_inductive_efficiency run --manifest PATH --output-root PATH [--resume]
```

Only `describe` and focused tests are pre-implementation checks; the result command is not
authorized here. No defaults for seeds, thresholds, checkpoints, or resources. Invalid contract,
missing native backend, failed preflight, resume mismatch, and technical failure use distinct
nonzero exits and expose no partial scientific values.

Tests cover literal containment, native identity/shapes/endpoint/no Python fallback, bitwise pair
initialization, exact logical-work parity, arm-independent addressed RNG, checkpoint/resume identity,
all analytic controls, evaluation noninterference, complete-only analysis, atomic fresh roots, AST
dependency firewall, and a tiny explicit `TEST_ONLY` chain.

## Acceptance and stop law

Generic competence precedes treatment interpretation. A positive requires prospectively frozen
simultaneous lower bounds on held-out direct return, held-out-minus-seen interaction, worst-basin
delivery, treatment cut loss, legal-action TV, and differential cut attenuation. Exact numeric
margins are manifest fields and cannot default from historical SGSP.

Structural, RNG, information/work, resource, or partial-panel failure is invalid. Generic
incompetence or endpoint-support failure is nonidentification. Practical equality, generic
superiority, same-host compiler absorption, or cut-insensitive gain closes the tested mechanism.
Mixed intervals remain unresolved. No replacement seed, second budget, altered threshold, or
post-result rescue is permitted.

The maximum claim is finite-budget relational inductive bias on the frozen fixed-roster and
held-out-size cells only.

## Evidence

- `DIRECTION.md`
- `docs/research/candidates/semantic_graphon_shared_policy/DIRECTION.md`
- `docs/research/candidates/covariance_calibrated_information_clock/DIRECTION.md`
- `docs/research/candidates/expressibility_gated_renewal_credit_relay/DIRECTION.md`
- `docs/research/candidates/voronoi_quadrature_field_policy/DIRECTION.md`
