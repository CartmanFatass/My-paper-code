# UCOPE contextual paid acquisition implementation threshold

Status: `COMPLETE_STOP_FIXED_PANEL_COMPETENCE`

The sole BELIEF production command, exact production manifest, combined resource/support preflight,
and complete-only result schema are frozen and implemented. The resource-only v3 revision admitted
the existing guarded `3,600`-second projection without changing scientific or execution semantics.
The sole result completed once and validated as `STOP_FIXED_PANEL_COMPETENCE`: `0/10` seeds passed
competence. The contextual object and historical R03 are both immutable and must never be rerun.

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
  production.py
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
  test_production_command.py
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

The following was the exact exhausted production sequence. Manifest, preflight, and `run-belief`
completed once; it is retained as provenance and must not be invoked again:

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
peak `2 GiB`, at least `4,294,967,296` live available bytes and `4,294,967,296` free-disk bytes,
benchmark-derived projected scratch and durable usage of `67,108,864` bytes each under separate
`268,435,456`-byte ceilings, and an exact `3,600`-second guarded result wall ceiling.

The retained v3 receipt is
`temp/directions/ucope/exp/ucope-contextual-paid-acquisition-r01-production/preflight/production-preflight.json`.
It records `16,621,502,464` live available bytes, `659,803,439,104` free-disk bytes, both storage
projections safe, complete support minimum `361>=256`, `82` files totaling `30,057,292` bytes, and
zero optimizer updates. The completed `run-belief` invocation freshly rechecked the same live
runtime/resource gates before accepting this preflight. No further invocation is permitted.

The retained complete result is
`temp/directions/ucope/exp/ucope-contextual-paid-acquisition-r01-production/result/belief-result.json`.
It validates all ten batch-640 checkpoint records, 6,400 total optimizer updates, complete held-out
evaluation, and create-once publication. Its exact conclusion-bearing fields are:

```text
competent_seed_count=0
competence_pass=false
acquisition_all_flips=false
panel_min_signed_specificity=12190847/800000000
acquisition_pass=false
fixed_panel_disposition=STOP_FIXED_PANEL_COMPETENCE
representation_conclusion=NONE
claim_ceiling=TEN_FIXED_SEED_SLOTS_FINITE_HOST_ONLY_NO_SEED_SUPERPOPULATION
```

Every seed fails oracle-root-vector equality, `max_regret<=0.02`, and
`forced_probe_tail_agreement>=0.95`; all score choices remain unique. The positive panel minimum is
downstream diagnostic evidence only and cannot rescue competence.

## Deferred representation phase

Only after BELIEF competence and acquisition pass could a separately frozen phase compare COUNT,
unrestricted RAW, and training-time permutation-invariant RAW on identical data and matched work.
Post-hoc RAW-PERMAVG is insufficient. Any COUNT effect is finite-resource bias because RAW contains
the count. This result fails competence first, so COUNT/RAW is ineligible and no representation phase
may begin from this object.

## Stop and claim ceiling

Stop in this order on contract/oracle drift, runtime/resource refusal, support failure,
checkpoint/resume failure, incomplete evaluation, BELIEF incompetence, or failed fixed-panel
acquisition. Context leakage or context-specific parameters, held-out-K leakage, primitive-ledger
mismatch, and RNG/resume inequality are technical invalidity. Downstream values cannot rescue an
earlier branch.

A positive result supports only finite-host contextual paid acquisition by one shared policy on
held-out K. It supports no COUNT advantage, variable-N, MARL, UAV, safety, deployment, or real-world
QoS claim.

The realized terminal claim is narrower: the exact fixed-budget shared BELIEF learner was
incompetent in all ten registered seeds despite complete support. It does not establish acquisition
failure or generic BELIEF unlearnability. No added budget, seed replacement, retuning, checkpoint
selection, or rerun is permitted.

Root accepted closure of this exact object and the direction-level move from `ACTIVE/HIGH` to
`PARKED/MEDIUM`. The Portfolio snapshot remains separately Root-owned and was not edited here.
Reactivation requires a new prospectively frozen competence-first learner or representation object
with independent justification; it cannot continue this result transaction.

## Evidence

- `DIRECTION.md`
- `UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_SCIENCE_CARD_20260823.md`
- `ACQUISITION_PARK_CERT_INDEX.md`
- `experiments/candidates/ucope/variable_k_paid_probe_r01_r03/`
- `temp/directions/ucope/exp/ucope-contextual-paid-acquisition-r01-wave2-bounded-benchmark/benchmark-observation.json`
- `temp/directions/ucope/exp/ucope-contextual-paid-acquisition-r01-production/preflight/production-preflight.json`
- `UCOPE_CONTEXTUAL_PAID_ACQUISITION_R01_BELIEF_RESULT_INTAKE_20260831.md`
- `temp/directions/ucope/exp/ucope-contextual-paid-acquisition-r01-production/result/belief-result.json`

## Competence-first scout R01 threshold

The successor object is
`UCOPE-B-EXPLORE-MT-XF-BC-COMPETENCE-FIRST-SCOUT-R01`. Its independent
three-arm harness, outcome-free cold resume, exact 72-checkpoint inventory,
resource journal, two-stage publication telemetry, and terminal hash chain are
implemented. Focused non-result tests report `34 passed` (`19` runner-focused), and independent final
review is `CLEAN`.

Engineering status is `IMPLEMENTATION_READY=YES` for a fresh A/RECON sizing
observation. The `.02` assessment was valid for its exact source and produced a
`PERFORMANCE_READY` manifest, but the first B1 attempt exposed an RSS projection
defect. Production performance status is again
`REPAIR_REQUIRED / NEEDS_FRESH_SIZING`; B1 is not launch-ready. The retained
`ucope-scout-r01-assess-20260901-01` receipt is superseded because its source
bytes and cap schema precede the final transaction repairs.

After integration commits the exact candidate package and runner bytes, create
one new result-blind sizing root:

```powershell
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' `
  scripts/run_ucope_competence_first_scout_r01.py assess-run `
  --output-root temp/directions/ucope/recon/ucope-scout-r01-assess-20260901-05
```

The fresh receipt must validate, report both 4 GiB floors, complete process-tree
RSS/CPU/I/O and separate scratch/durable high-water telemetry, retain frozen
process/thread/Torch caps, and yield `PERFORMANCE_READY`. Only then may
`create-b1-manifest` run. No valid or completed B1 scientific result exists,
and no fresh B1 is launch-ready until `.05` validates. The already launched
`b1-20260901-01` is only an unrecoverable incomplete technical attempt. Every
future run still requires its own fresh 4 GiB admission; the quarantined root
must never be resumed.

### Quarantined B1 resource refusal

`temp/directions/ucope/exp/ucope-scout-r01-b1-20260901-01` is an incomplete,
nonconsuming engineering attempt. Both prelaunch and runner admissions passed.
The core wrote all 72 outcome-free checkpoints, then failed closed before
result publication because process-tree peak RSS was `455,176,192` bytes above
the manifest cap `402,653,184` bytes. Core wall time was `122.8474525000056`
seconds; scratch/durable peaks were `10,630,135`/`10,629,120` bytes; the peak was
one process and 29 threads. No checkpoint science, evaluation, gate, or outcome
was read or interpreted during this repair.

The attempt is quarantined. It must not be resumed, salvaged, published, or
rerun, and it does not consume the scientific object. The reduced sizing path
underestimated full-load RSS because a 5/4 multiplier on its own peak did not
represent the retained three-seed populations and CPU allocator high-water
across the full arm sequence. Future projections therefore take the maximum of
the fresh A/RECON peak with 5/4 headroom and this resource-only `455,176,192`-
byte full-load floor with the same headroom, then round the cap upward to a
64 MiB quantum. For the observed envelope this yields a `576 MiB` RSS cap,
`603,979,776` bytes, while retaining the explicit 2 GiB readiness ceiling.

### Quarantined B1 publication-schema refusal

`temp/directions/ucope/exp/ucope-scout-r01-b1-20260901-02` is also an
incomplete, nonconsuming engineering attempt. Its `.03`-bound resource contract
passed, and the outcome-free journal reached all 72 checkpoint events. Result
publication then failed closed with `per-policy exact activity mismatch`; no
complete namespace or valid scientific result exists. The root is permanently
quarantined and must not be resumed, salvaged, published, rerun, or inspected
for policy/action/score/return/gate/competence/acquisition evidence.

The exact defect was a contradictory B1 activity schema introduced when the
action-dependent `sampled_evaluation_transitions` counter was correctly removed
from the A/RECON surface. `POLICY_ACTIVITY_FIELDS` inherited that reduced set,
so B1 first rejected every real per-policy row for containing the required
counter and then immediately required the same counter to be positive. The
repair adds the counter only to the B1 policy schema. A/RECON continues to
exclude it; workload, arms, seeds, clocks, checkpoints, gates, precision, RNG,
and scientific meaning are unchanged. After this source change, `.03` remains
historical readiness evidence for its exact bytes but cannot bind a new
manifest. The next allowed sizing root was `.04`; after the filesystem
telemetry repair below, only fresh `.05` may bind the next manifest.

### Quarantined B1 filesystem-observation refusal

`temp/directions/ucope/exp/ucope-scout-r01-b1-20260901-03` is a third
incomplete, nonconsuming engineering attempt. Its outcome-free resource journal
reached all 72 checkpoint events and a core terminal, but publication failed
closed at `PUBLICATION_MONITOR_FINISH`. The monitor's background thread was
walking a checkpoint directory under `.complete-staging-*` while the main
thread renamed that tree to `.complete-postvalidated-*`; the walker then raised
Windows error 3 on the old path. No visible `complete` directory exists and the
transient work root remains quarantined. It must not be resumed, salvaged,
published, rerun, or inspected for scientific content.

The repair binds the final old-tree sample, same-parent atomic rename, durable-
root retarget, and first new-tree sample under the monitor's single lock. A
background walk therefore cannot overlap the rename. Both endpoint directory
sizes are actually measured and contribute conservatively to the existing
high-water; a missing bound root raises instead of contributing a false zero.
Plain-directory and symlink rejection remain unchanged. Source/manifest,
workload, arms, seeds, updates, checkpoints, evaluation, gates, RNG, precision,
and scientific semantics are unchanged. `.04` remains historical readiness
evidence for its exact source. After Root commits this repair, the only next
sizing root is fresh `.05` above, followed by a new manifest and B1 root.
