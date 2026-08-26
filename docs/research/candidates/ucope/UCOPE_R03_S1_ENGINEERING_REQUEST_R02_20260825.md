# UCOPE R03 S1 engineering request R02

Decision owner: EM-ucope

```text
document_kind=DIRECTION_ENGINEERING_REQUEST
document_revision=R02
direction_id=ucope
logical_identity=EM-ucope
generation=1
exact_object_revision=UCOPE-NEXT-VARIABLE-K-PAID-PROBE-CONTAINMENT-R01-SCIENCE-20260823-03
prior_request_sha256=9e2f2aa36a8b3c644aef1e610610577ca47c256603864d79b17c88d1d025aeba
prior_cm_work_id=4061601c1f87919adda58c074ffeed1895ddb66ced706a445fba2abbfdd11d2b
cm_disposition=S1_AUTHORITY_CONTRACT_INCOMPATIBLE
science_revision=UNCHANGED
engineering_stage=S1_ONLY
S2_release=false
question_relevant_output=NONE
empirical_authority=false
effect_refs=EMPTY_AT_HANDOFF
```

## Frozen authority and supersession

Every reference below matched its exact current bytes or revision before this
artifact was created:

| Reference | Frozen identity |
| --- | --- |
| `docs/research/portfolio/PORTFOLIO.md` | SHA-256 `922c20cf071f03a710f9e1597fda8ee826cd32bc10b89fd74331daaf7c82caaf` |
| `docs/research/portfolio/workflow/registry.json` | revision `9`, SHA-256 `95e3dd2aaf0c54b589b6f29ed51aadd0871300ba6ec528f64e12509550e03941` |
| `docs/research/candidates/ucope/DIRECTION.md` | SHA-256 `ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d` |
| `docs/research/candidates/ucope/UCOPE_R03_S1_ENGINEERING_REQUEST_20260825.md` | SHA-256 `9e2f2aa36a8b3c644aef1e610610577ca47c256603864d79b17c88d1d025aeba` |
| `docs/research/candidates/ucope/UCOPE_VARIABLE_K_PAID_PROBE_CONTAINMENT_R01_R03_S0_CM_TECHNICAL_ACCEPTANCE_PORTFOLIO_EM_INTAKE_20260824.md` | SHA-256 `f7d5522506c3bd96d84c222dc6474cc40b6f4dfbb0aed12b7be68c1bda63b7ae` |
| `docs/research/candidates/ucope/workflow/research/state.json` | revision `3`, SHA-256 `7424483068bc1349e1dc4ed8a666c636af47da1c5f63dfdff828c8b6b7ff9535` |
| `docs/research/candidates/ucope/workflow/engineering/state.json` | revision `2`, SHA-256 `64deea239649639b06e1ca0cdd09e94ae8eb1d21a6ac10812dad0f92ce27d332` |
| `temp/directions/ucope/test/s1/S1_AUTHORITY_CONTRACT_INCOMPATIBILITY.json` | SHA-256 `bbdb093122ce4d82c4e45ea2de11d26440c30fbe64290303e7a595dfed789509` |
| `scripts/hmasd_run.py` | SHA-256 `a072f8a50c825a19d91189b2330b19dc9c4198810d8453a5ae8c9057e77453d4` |
| `scripts/hmasd_state.py` | SHA-256 `8e7b6c43d8d70ae3e5769084c7e2fec19e8626404d154c68639a2f83632bd653` |

This R02 artifact supersedes the R01 request only for its authority-contract
shape. The R01 artifact remains immutable provenance. The future CM packet
issued from R02 supersedes work id
`4061601c1f87919adda58c074ffeed1895ddb66ced706a445fba2abbfdd11d2b`
only for that same contract shape. Neither supersession changes the R03
scientific object, the accepted S0-to-S1 predicates, the Pro closure, any S1
gate or resource cap, the strongest alternative, the claim ceiling, the result
firewall, or the prohibition on S2.

The CM revision-2 disposition is a direction-scoped engineering-authority
incompatibility. It is not a scientific result, partial result, empirical
observation, implementation defect, or reason to change the selected object.
CM recorded no source or test change, no Operator, no run manifest, no result
command, no question-relevant output, and no Effect.

## Authority-shape correction

### Unique result-blind Operator and official run scope

One later result-blind technical command is authorized for S1 acceptance under
the following frozen identity:

```text
run_id=ucope-r03-s1-current-byte-acceptance-20260825-01
assignment_id=ucope-r03-s1-current-byte-acceptance
operator_identity=Operator-ucope-r03-s1-current-byte-acceptance-20260825-01
code_sha=ee06a078c3c5ff904e00c727475c467a25ada1ff
command_sha256=b968adea6fa5f73fcb24f925306ec8fcef82430af0325d098a98e25f39809f84
parameters_sha256=f52b283f82b7d3ffa0bf8c6970725c2c6ca8675362c0b1c2e6ec5831ffacbf41
claim_sha256=348a15a4137cd4c18e9b29fad78af53e17092e9525f45b644f7cece90fe895e4
estimated_wall_seconds=300
estimated_peak_memory_gib=2.0
workers=8
threads_per_worker=1
estimated_duration_above_7200_seconds=false
scientific_activity_predicate=false|NONREGISTERED_TEST_ONLY|NO_S2|NO_SCIENTIFIC_VALUE
```

The exact argv is:

```json
[
  "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
  "-c",
  "import subprocess,sys; py=sys.executable; r=subprocess.run([py,'-m','pytest','-q','tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s0.py','tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s1.py']); r.check_returncode(); r=subprocess.run([py,'-m','experiments.candidates.ucope.variable_k_paid_probe_r01_r03.benchmark','--stage','s1','--work-root','temp/directions/ucope/test/s1/work','--output','temp/directions/ucope/test/s1/benchmark.json']); raise SystemExit(r.returncode)"
]
```

The exact parameters are:

```json
{
  "gpu": false,
  "max_workers": 8,
  "namespace": "TEST_ONLY_UCOPE_R01_R03_S1",
  "registered_master_seeds": false,
  "request": "SEMANTIC_CORE_TEST",
  "threads_per_worker": 1
}
```

Exactly one `hmasd-experiment-operator` owns this exact command from official
prepare through foreground execute and terminal observation. It must use
`scripts/hmasd_run.py`; direct child launch, detached launch, a second
Operator, replay after unknown commitment, or a second manifest is forbidden.
The normal resource preflight remains mandatory. The 300-second estimate is
below the 7,200-second performance-review and explicit-approval threshold, but
it does not waive memory refusal, duplicate-claim checks, process identity, or
terminal observation.

Before prepare, Root must provide or reuse one canonical native Windows
assignment cwd whose Git branch begins `omp/` and whose HEAD is the exact
`code_sha` above. CM and the Operator freeze that absolute cwd as runtime
provenance. The earlier unlaunched observation of `C:/Projects/HMASD` on
`main` is not a launch authority and must not be passed to official prepare.
This artifact does not itself create, switch, commit, push, or integrate a
worktree. If a conforming cwd is absent, CM returns that exact runtime
prerequisite to Root before prepare and performs no run effect.

Relative to the conforming cwd, the official run output root is exactly:

`temp/directions/ucope/exp/ucope-r03-s1-current-byte-acceptance-20260825-01`

The official manifest, preflight, execute-preflight, runner specification,
stdout, stderr, checkpoints, metrics, artifacts, and run-local lock files stay
inside that root. The exact direction claim and its cooperative lock are:

- `temp/directions/ucope/.run-claims/348a15a4137cd4c18e9b29fad78af53e17092e9525f45b644f7cece90fe895e4.json`;
- `temp/directions/ucope/.run-claims/.348a15a4137cd4c18e9b29fad78af53e17092e9525f45b644f7cece90fe895e4.json.lock`.

The child command's result-blind TEST work and benchmark remain exactly under
`temp/directions/ucope/test/s1`. The official `exp` wrapper evidence and the
TEST evidence are two authorized disposable scopes with different purposes;
neither is durable scientific authority. No registered seed, registered
complete panel, question-relevant output, partial value, or R03 result may be
materialized.

### Validator-compatible engineering scope

Every engineering-state revision remains bound to the existing validator-
compatible decision reference:

```text
path=docs/research/candidates/ucope/DIRECTION.md
heading=Engineering request
sha256=ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d
```

The engineering `scope_ref` must not point to either immutable request
artifact. This R02 artifact is instead carried by exact content reference and
the headings below in CM input, verification, acceptance, and next-action
refs. The engineering-state CAS remains writer `CM-ucope`, begins from
revision `2`, and preserves the `scope_ref.path` required by
`scripts/hmasd_state.py`.

## Engineering request — S1 only

Root may deliver one new immutable packet to canonical `CM-ucope`. CM first
inspects the current bytes, makes only necessary repairs inside the exact owned
paths, and either accepts every S1 predicate or returns the exact failed
predicate and resume condition.

The exact downstream owned paths are:

- `docs/research/candidates/ucope/workflow/engineering/state.json`;
- `experiments/candidates/ucope/variable_k_paid_probe_r01_r03`;
- `tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s0.py`;
- `tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s1.py`;
- `temp/directions/ucope/test/s1`;
- `temp/directions/ucope/exp/ucope-r03-s1-current-byte-acceptance-20260825-01`;
- `temp/directions/ucope/.run-claims/348a15a4137cd4c18e9b29fad78af53e17092e9525f45b644f7cece90fe895e4.json`;
- `temp/directions/ucope/.run-claims/.348a15a4137cd4c18e9b29fad78af53e17092e9525f45b644f7cece90fe895e4.json.lock`.

Within that scope, complete or verify only the source-bound native host and
loader; balanced PERSISTENT, REDRAW, and SEVERED populations; all six arms; the
six frozen counter namespaces and sharing law; paired initialization and
arm-private ACTION; the `13->64->64->1` scorer and `9->32->1` baseline; the
ordinary-FP32 REINFORCE, entropy, AdamW, clipping, and deterministic reduction
law; exact support counters; the strict 90-slot final-checkpoint schema; and
atomic batch-frontier crash/resume without a repeated optimizer step.
Result-blind fixtures may cover every legal action, history, panel, and width,
but may not instantiate the registered complete population or emit a
scientific value.

The S1 stage remains `6` managed / `7` hard engineer-days, cumulative
result-blind TEST `3` managed / `6` hard CPU-hours, and `25` managed / `45`
hard minutes for the largest TEST command. Construction and TEST remain
CPU-only with GPU forbidden, at most `16` cores, `8 GiB` peak RSS, `2 GiB`
scratch, `0.75 GiB` durable evidence, and `8 GiB` aggregate read-plus-write
I/O. Actual cost and remaining forecast must preserve the non-replenishable
`15` managed / `18` hard total engineer-day and `6` managed / `12` hard
cumulative TEST CPU-hour envelopes.

The already-selected sole Sol-high `hmasd-implementer` may be reused under CM
ownership if a necessary in-scope repair is established. A second Implementer
or substitute capability is outside this request. Reviewer remains prohibited
until one coherent S2 candidate exists, and no Verifier is authorized.

### Acceptance criteria

`CM-ucope` may record `S1_TECHNICALLY_ACCEPTED` only when all of the following
hold on the accepted current bytes:

1. Every frozen authority reference matches before material engineering work,
   and every changed or generated material path remains inside the exact owned
   set.
2. Native fixture-oracle equality holds for reset, root-step, probe, tail-step,
   terminal behavior, and every panel and channel intervention, with no Python
   environment fallback.
3. Integer RNG namespace, address, sharing, paired initialization, arm-private
   ACTION, stable row order, deterministic reduction, sequential/parallel
   equivalence, and crash/resume equality match the frozen law with no repeated
   optimizer step.
4. Parameters, features, activations, rewards, returns, gradients, optimizer
   state, serialization metadata, and reporting reductions conform to
   `HMASD-MARL-FP32-BASELINE-V1`; no FP64, mixed, proof-grade hot path, or
   precision exception exists. One narrow result-blind FP32 sensitivity check
   is included.
5. Support counters, checkpoint/frontier schema, atomic replacement,
   malformed-input refusal, and the result firewall are complete; no partial
   or complete R03 package crosses the activity boundary.
6. Exactly one Operator prepares and executes the exact result-blind command
   through `scripts/hmasd_run.py` from a conforming native `omp/` cwd at the
   frozen code SHA. The manifest reaches a terminal state under the same
   Operator; official wrapper evidence stays in the exact `exp` root and claim
   paths, while child TEST evidence stays in `temp/directions/ucope/test/s1`.
7. The focused S0/S1 tests and benchmark re-establish at least `75%` effective
   CPU concurrency, at most `30%` parallel overhead, at least `1.25x` declared
   reference throughput, and cold compile/load no greater than six minutes.
8. The conservative complete-transaction projection remains no greater than
   `1,800` seconds on at most 24 CPU cores, `12` CPU-hours, `10 GiB` peak RSS,
   and `6 GiB` aggregate I/O, while actual S1 TEST remains inside the stricter
   16-core/8-GiB construction envelope.
9. Actual S1 engineering, TEST CPU/wall, RSS, scratch, durable, aggregate I/O,
   and device facts remain within every stage and total cap, and the remaining
   forecast preserves the total `18`-day hard ceiling.
10. The final engineering-state write uses expected-revision CAS with writer
    `CM-ucope`, keeps `scope_ref` bound to the exact `DIRECTION.md` reference,
    records R02 as input/verification/acceptance authority, and reports exact
    changed paths, run and verification refs, measured cost/resource facts,
    remaining unknowns, and the bounded S1 disposition.

Any missing or failed item requires an S1-scoped incompatibility return naming
the failed predicate, observed refs, actual cost/resource facts, and exact
resume condition. It is not a negative scientific result and must not be
reported as a bare `BLOCKED` state or repaired by changing the scientific
object.

### Explicit non-scope

This request does not authorize:

- any change to the R03 host, panels, arms, coordinates, periods, seeds,
  episodes, rewards, optimizer, thresholds, diagnostics, branch map, activity
  boundary, strongest alternative, claim ceiling, or result firewall;
- S2 finite evaluation, DP/RAW-PERMAVG diagnostics, attribution, complete
  output, production modules, Reviewer, SANCheck, or S2 release;
- registered master seeds, the complete training/evaluation panel,
  question-relevant output, a scientific result or partial value, empirical
  identity or coordinate, provider operation, deployment, or flight;
- direct or detached execution, a second Operator, a second manifest, replay
  after unknown commitment, a second Implementer, a Verifier, cap
  replenishment, or substitution of another scientific object;
- CM or Operator creation, switching, commit, push, integration, or deletion
  of a worktree; Root alone supplies or reuses the runtime cwd;
- modification of `DIRECTION.md`, the R01 request, this immutable R02 request,
  Portfolio, registry, external-review state, shared core, or any material path
  outside the exact downstream owned set; or
- any Git, provider, deployment, flight, or other external Effect.

This artifact creates no task, Operator, manifest, lease, claim, worktree, or
run. The follow-on CM packet has `effect_refs=[]` because no run or external
effect exists at publication. Root owns canonical task/worktree orchestration;
CM owns the later bounded engineering cycle; the single Operator owns only the
exact prepared command through terminal observation. S1 acceptance does not
begin S2.
