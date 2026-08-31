# UCOPE contextual paid acquisition implementation threshold

Status: `PRODUCTION_V2_IMPLEMENTED_NOT_READY_RESOURCE_WALL_AND_LIVE_MEMORY`

The sole BELIEF production command, exact production manifest, combined resource/support preflight,
and complete-only result schema are frozen and implemented. They are not currently schedulable:
the guarded result projection is `3,600` seconds against the current `1,800`-second ceiling, and the
fresh host preflight observed `3,514,687,488` bytes of live available RAM against the required
`4,294,967,296`. The preflight refused before support materialization, model construction, optimizer
activity, held-out evaluation, or result publication. R03 is immutable and must never be rerun.

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
vector, keep max BELIEF-DP regret `<=0.02`, and achieve forced-PROBE tail agreement `>=0.95`.
Competence literally requires each counted seed's learned action vector to equal the oracle vector.

The prospective v2 acquisition rule is an exact census of the ten preregistered slots, not a
seed-superpopulation inference. For seed `s` and context `c`, let `S_s,c=Gamma_s,c` in the sole
target cell and `S_s,c=-Gamma_s,c` in every nontarget cell. Compute exact rational
`M_s=min_c S_s,c` and `M_panel=min_s M_s` from the retained cell evidence. Acquisition requires the
unchanged competence gate, all ten exact root vectors, and strict `M_panel>0`. All ten seeds and all
80 seed/context margins remain; none may be dropped, replaced, rounded, or selected by competence.
The rule literal is `ALL_TEN_ALL_EIGHT_STRICT_POSITIVE_V1` with exact threshold `0/1`.

The former Student-t mean rule is rejected. Counter-addressed seed slots are fixed design points,
not a registered random sample, and the t statistic had no finite-sample coverage law. The exact
range is
`M_s in [-52945109/160000000, 17149681/800000000]`; a bounded mean-zero two-point law makes all ten
observations equal the positive endpoint with probability about `0.5338`, where the old zero-variance
t rule would falsely pass. This pre-result v2 recast supports only complete-panel stability and no
practical materiality floor or seed-superpopulation mean. Failure stops before COUNT/RAW.

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

The v2 CLI is exact:

```text
... describe
... check-contract --manifest PATH
... create-production-manifest --manifest PATH
... preflight-support --manifest PATH --output-root PATH       # TEST_ONLY support seam
... preflight-production --manifest PATH --output-root PATH
... validate-preflight --artifact PATH
... run-belief --manifest PATH --preflight PATH --output-root PATH
```

`run-belief` is the sole result route and accepts only manifest, accepted production preflight, and
output root—never seed, context, cost, reliability, K, threshold, arm, retry, resume, checkpoint
selection, partial-result, or COUNT/RAW overrides. It atomically resumes its fixed per-seed checkpoint
path at every batch, completes and validates all ten batch-640 checkpoints before importing or
invoking held-out evaluation, and publishes only one create-once complete v2 result. Historical
R03/B2 runtime modules are not imported; tests enforce the dependency firewall.

The literal command sequence is currently blocked at production preflight and must not be run past
that refusal:

```powershell
$python = 'C:\Users\fires\.conda\envs\hmasd-amd-cpu\python.exe'
$root = 'temp\directions\ucope\exp\ucope-contextual-paid-acquisition-r01-production'
& $python -m experiments.candidates.ucope.contextual_paid_acquisition_r01 `
  create-production-manifest --manifest "$root\manifest.json"
& $python -m experiments.candidates.ucope.contextual_paid_acquisition_r01 `
  preflight-production --manifest "$root\manifest.json" --output-root "$root\preflight"
& $python -m experiments.candidates.ucope.contextual_paid_acquisition_r01 `
  run-belief --manifest "$root\manifest.json" `
  --preflight "$root\preflight\production-preflight.json" --output-root "$root\result"
```

Current resource contract: Python 3.10, PyTorch `2.7.0+cpu`, CPU-only deterministic algorithms,
one worker, one intra-op and one inter-op thread, batch 256, checkpoint cadence one batch, estimated
peak `2 GiB`, at least `4 GiB` live available RAM and `4 GiB` free disk, and result wall ceiling
`1,800` seconds. The guarded projection is `3,600` seconds, so the command is fail-closed regardless
of a later recovery in live RAM.

A prospective resource-only revision is available for Root decision; it is not implemented or
authorized here. It would retain the identical science, data, RNG, learner, work, and command while
raising only the wall ceiling to the already guarded `3,600` seconds, with `2 GiB` peak RAM,
`256 MiB` scratch, `256 MiB` durable, one worker, intra/inter-op threads 1, batch 256, and checkpoint
cadence 1. It would still require a fresh exact preflight, absent output roots, at least `4 GiB` live
RAM and `4 GiB` free disk, and the exact production support minimum `361>=256` before any activity.

## Deferred representation phase

Only after BELIEF competence and acquisition pass may a separately frozen phase compare COUNT,
unrestricted RAW, and training-time permutation-invariant RAW on identical data and matched work.
Post-hoc RAW-PERMAVG is insufficient. Any COUNT effect is finite-resource bias because RAW contains
the count.

## Stop and claim ceiling

Stop in this order on contract/oracle drift, runtime/resource refusal, support failure,
checkpoint/resume failure, incomplete evaluation, BELIEF incompetence, or failed fixed-panel
acquisition. Context leakage or context-specific parameters, held-out-K leakage, primitive-ledger
mismatch, and RNG/resume inequality are technical invalidity. Downstream values cannot rescue an
earlier branch.

A positive result supports only finite-host contextual paid acquisition by one shared policy on
held-out K. It supports no COUNT advantage, variable-N, MARL, UAV, safety, deployment, or real-world
QoS claim.

## Evidence

- `DIRECTION.md`
- `UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_SCIENCE_CARD_20260823.md`
- `ACQUISITION_PARK_CERT_INDEX.md`
- `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/`
- `temp/directions/ucope/exp/ucope-contextual-paid-acquisition-r01-wave2-bounded-benchmark/benchmark-observation.json`
