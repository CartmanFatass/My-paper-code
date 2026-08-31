# UCOPE contextual paid acquisition implementation threshold

Status: `ISOLATED_IMPLEMENTATION_AND_TEST_ONLY_PREFLIGHT_COMPLETE`

No production result command is scientifically frozen or implemented. R03 is immutable and must
never be rerun.

## Scientific object

Test whether one shared policy uses observable linkage, reliability, and primitive probe cost to
probe only where information repays its cost. Phase 1 supports only contextual net acquisition;
COUNT-versus-RAW attribution is deferred.

Use the uniform eight-cell population:

```text
link        {LINKED, SEVERED}
reliability {13/20, 17/20}
probe cost  {9/100, 14/100}
```

Retain horizon 12, six marks, train periods `{1,3,5,7,9}`, held-out periods `{2,4,6,8}`, and the R03
tail law. The shared policy observes linkage, reliability, time cost, and energy cost, never regime,
future randomness, reward, seed, or arm/context label.

Primitive accounting keeps probe service, time, and energy separate. LINKED displays marks from the
tail regime; SEVERED displays an independent prior-regime history while actual marks still own probe
service. Probing has negative direct value in every context.

## Exact BELIEF gate

Freeze

\[
\Gamma(link,p,C;K)=1\{link=LINKED\}I_p(K)+1/25-C.
\]

Exactly one context, `LINKED × p=17/20 × C=9/100`, must uniquely choose PROBE on both train and
held-out period sets; every other context uniquely chooses IMMEDIATE. On held-out K, LINKED BELIEF
chooses periods by observed count while SEVERED chooses the same immediate optimum. Missing
uniqueness, changed sign, or nonnegative direct probe value stops before learning.

## Support-first exposure

Use ten new counter-keyed seed slots, distinct from R03. For every seed and context, materialize the
immutable dataset before constructing a model:

```text
20,480 episodes
10,240 PROBE
2,048 immediate COMMIT(k) for each training k
2,048 tail COMMIT(k) for each training k conditional on PROBE
```

Require exact context/regime balance and at least 256 displayed visits for each count `0..6`. The
indexed behavior schedule is independent of context, marks, and rewards. Preflight binds manifest,
tape, dataset, and support-counter identities; performs zero optimizer updates; and emits no values,
contrasts, or acquisition conclusion. Failure stops without resampling, appending, dropping seeds,
or changing floors.

## Shared BELIEF learner

Each seed owns one checkpoint with shared root and tail scorers; no context indexes parameters,
optimizer, normalization, replica, or checkpoint. Use fixed-behavior fitted Q with FP32
`9→64→64→1` scorers, fixed Glorot initialization, one deterministic pass, batch 256, AdamW `3e-4`,
fixed betas/epsilon/weight decay, and gradient clip 1. Tail targets are unshaped tail returns; PROBE
root targets use realized primitive probe ledger plus `max_k Q_tail`; immediate targets use unshaped
return. No validation selection, early stop, retry, sweep, rescue, or held-out-even-K optimizer
exposure.

Complete held-out enumeration requires at least 9/10 seeds to reproduce the eight-cell action
vector, keep max BELIEF-DP regret `<=0.02`, and achieve forced-PROBE tail agreement `>=0.95`. After
competence, acquisition requires every retained seed to execute the exact root flip and a strictly
positive one-sided confidence bound on signed specificity. Failure stops before COUNT/RAW.

## Isolated implementation surface

```text
experiments/candidates/ucope/contextual_paid_acquisition_r01/
  contract.py
  schema.py
  rng.py
  oracle.py
  host.py
  support.py
  model.py
  training.py
  checkpoint.py
  evaluation.py
  analysis.py
  artifact.py
  cli.py
  __main__.py

tests/experiments/candidates/ucope/contextual_paid_acquisition_r01/
  test_contract_and_oracle.py
  test_primitive_ledger_and_severance.py
  test_support_preflight.py
  test_shared_policy_and_targets.py
  test_heldout_k_firewall.py
  test_checkpoint_resume.py
  test_analysis_and_schema.py
  test_cli_and_dependency_firewall.py
```

Schemas cover contract, exact BELIEF-flip certificate, support certificate, checkpoint, and complete
BELIEF result. APIs validate the contract, construct the flip certificate, build/materialize the
fixed behavior plan, validate support, train one seed, evaluate held-out cells, validate competence,
and atomically publish a complete result.

Current CLI is non-result only:

```text
... describe
... check-contract --manifest PATH
... preflight-support --manifest PATH --output-root PATH
... validate-preflight --artifact PATH
```

A later result command may accept only manifest, accepted preflight, and output root—never seed,
context, cost, reliability, K, threshold, arm, retry, or partial-result overrides. Historical R03/B2
runtime modules are not imported; tests enforce the dependency firewall.

## Deferred representation phase

Only after BELIEF competence and acquisition pass may a separately frozen phase compare COUNT,
unrestricted RAW, and training-time permutation-invariant RAW on identical data and matched work.
Post-hoc RAW-PERMAVG is insufficient. Any COUNT effect is finite-resource bias because RAW contains
the count.

## Stop and claim ceiling

Stop on contract drift, absent/nonunique flip, nonnegative direct probe value, support failure,
context leakage or context-specific parameters, held-out-K leakage, primitive-ledger mismatch,
RNG/resume failure, resource-preflight failure, BELIEF incompetence, or nonpositive acquisition
bound.

A positive result supports only finite-host contextual paid acquisition by one shared policy on
held-out K. It supports no COUNT advantage, variable-N, MARL, UAV, safety, deployment, or real-world
QoS claim.

## Evidence

- `DIRECTION.md`
- `UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_SCIENCE_CARD_20260823.md`
- `ACQUISITION_PARK_CERT_INDEX.md`
- `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/`
