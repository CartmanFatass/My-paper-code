# UCOPE R03 S1 engineering request R03

Decision owner: EM-ucope

```text
document_kind=DIRECTION_ENGINEERING_REQUEST
document_revision=R03
direction_id=ucope
logical_identity=EM-ucope
generation=1
exact_object_revision=UCOPE-NEXT-VARIABLE-K-PAID-PROBE-CONTAINMENT-R01-SCIENCE-20260823-03
prior_request_sha256=a51937a96ff9f00d37d7068195da6b19d37f3efcf3c4cf01b894596064b20937
prior_cm_work_id=5fadc1c99698939e0f9b55668d7e1d9f0d1f59285087f2ba1eb1f7485eafc0de
cm_disposition=S1_R02_COMMAND_IDENTITY_INCOMPATIBLE
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
| `docs/research/portfolio/workflow/registry.json` | revision `9` |
| `docs/research/candidates/ucope/DIRECTION.md` | SHA-256 `ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d` |
| `docs/research/candidates/ucope/UCOPE_R03_S1_ENGINEERING_REQUEST_R02_20260825.md` | SHA-256 `a51937a96ff9f00d37d7068195da6b19d37f3efcf3c4cf01b894596064b20937` |
| `docs/research/candidates/ucope/workflow/research/state.json` | revision `5`, SHA-256 `cd283e21f9b1882d7836fcc90d3fe6f8fd58c7accdc68e1131cbbc4578dc92f1` |
| `docs/research/candidates/ucope/workflow/engineering/state.json` | revision `3`, SHA-256 `7cf6f34350a0745d4f179b4511d950354ebf7354847c688ca6ab4910a1c8dd11` |
| `.codex/runtime/worktrees.json` | revision `3` |
| `temp/runtime/receipts/wt-ucope-engineering-ucope-r03-s1-current-byte-acceptance.json` | SHA-256 `a16a8447cc426d8586dd8836c82e3e138a5bffa623abd3619e3d95ed414a9454` |
| `temp/directions/ucope/test/s1/S1_R02_COMMAND_IDENTITY_INCOMPATIBILITY.json` | SHA-256 `1fd78bfe87b188f3c086e4562cc81c75e98098c6dbf91728a0fc3e0b86d63355` |
| `scripts/hmasd_run.py` | SHA-256 `a072f8a50c825a19d91189b2330b19dc9c4198810d8453a5ae8c9057e77453d4` |
| `scripts/hmasd_state.py` | SHA-256 `8e7b6c43d8d70ae3e5769084c7e2fec19e8626404d154c68639a2f83632bd653` |

This R03 artifact supersedes R02 only for the command digest, claim digest,
and their two claim paths. It also supersedes only the contrary mechanical
statement recorded in research-state revision 5. R02 and revision 5 remain
immutable provenance. The future CM packet issued from R03 supersedes work id
`5fadc1c99698939e0f9b55668d7e1d9f0d1f59285087f2ba1eb1f7485eafc0de`
only for the same command/claim contract shape. The earlier shape supersession
of work id
`4061601c1f87919adda58c074ffeed1895ddb66ced706a445fba2abbfdd11d2b`
remains intact.

No scientific or engineering acceptance predicate changes. The R03 object,
accepted S0-to-S1 predicates, Pro closure, S1-only boundary, parameters,
resource caps, strongest alternative, claim ceiling, result firewall, and S2
prohibition are unchanged. The CM revision-3 return is a prepare-prerequisite
identity correction, not a scientific result, partial result, implementation
defect, or negative finding.

## Mechanical command and claim reconciliation

The exact R02 JSON argv was parsed as an array of three strings. The pinned
runner computes the command identity as:

```text
SHA256(bytes([0]).join(os.fsencode(part) for part in argv))
```

The separator is exactly one NUL byte, hexadecimal `00`. The joined byte length
is `572`. Independent no-write evaluation yields:

```text
command_sha256=dd580636e12aaf248532ad8704429a3fe097a710089af499eebfbdbd0687fb1c
parameters_sha256=f52b283f82b7d3ffa0bf8c6970725c2c6ca8675362c0b1c2e6ec5831ffacbf41
claim_sha256=5410a4060ce1e625044056e263d0cc2c09a2c5fa5a6a1a8593db28f244c78607
```

The R02 command value
`b968adea6fa5f73fcb24f925306ec8fcef82430af0325d098a98e25f39809f84`
was produced by joining with the two ASCII bytes backslash-zero rather than a
single NUL byte. Its derived claim
`348a15a4137cd4c18e9b29fad78af53e17092e9525f45b644f7cece90fe895e4`
and both R02 claim paths are therefore not official identities. They must not
be used by prepare, execute, engineering state, or the follow-on packet.

CM stopped before official prepare. It created no preflight, manifest, claim,
Operator, child, benchmark, scientific output, or Effect. The registered
assignment worktree
`wt-ucope-engineering-ucope-r03-s1-current-byte-acceptance` is singly
registered, `PROVISIONED`, clean, on branch
`omp/ucope/engineering/ucope-r03-s1-current-byte-acceptance`, at exact HEAD
`ee06a078c3c5ff904e00c727475c467a25ada1ff`, with candidate SHA `null` and no
source or focused-test difference.

## Authority-shape correction

### Unique result-blind Operator and official run scope

One later result-blind technical command is authorized for S1 acceptance under
the following corrected, single-valued identity:

```text
run_id=ucope-r03-s1-current-byte-acceptance-20260825-01
assignment_id=ucope-r03-s1-current-byte-acceptance
operator_identity=Operator-ucope-r03-s1-current-byte-acceptance-20260825-01
worktree_ref=wt-ucope-engineering-ucope-r03-s1-current-byte-acceptance
code_sha=ee06a078c3c5ff904e00c727475c467a25ada1ff
command_sha256=dd580636e12aaf248532ad8704429a3fe097a710089af499eebfbdbd0687fb1c
parameters_sha256=f52b283f82b7d3ffa0bf8c6970725c2c6ca8675362c0b1c2e6ec5831ffacbf41
claim_sha256=5410a4060ce1e625044056e263d0cc2c09a2c5fa5a6a1a8593db28f244c78607
estimated_wall_seconds=300
estimated_peak_memory_gib=2.0
workers=8
threads_per_worker=1
estimated_duration_above_7200_seconds=false
scientific_activity_predicate=false|NONREGISTERED_TEST_ONLY|NO_S2|NO_SCIENTIFIC_VALUE
```

The exact argv is unchanged from R02:

```json
[
  "C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe",
  "-c",
  "import subprocess,sys; py=sys.executable; r=subprocess.run([py,'-m','pytest','-q','tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s0.py','tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s1.py']); r.check_returncode(); r=subprocess.run([py,'-m','experiments.candidates.ucope.variable_k_paid_probe_r01_r03.benchmark','--stage','s1','--work-root','temp/directions/ucope/test/s1/work','--output','temp/directions/ucope/test/s1/benchmark.json']); raise SystemExit(r.returncode)"
]
```

The exact parameters are unchanged:

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
prepare through one foreground execute and terminal observation. It must use
`scripts/hmasd_run.py`; direct or detached child launch, a second Operator or
manifest, replay after unknown commitment, or a successor command is
forbidden. Resource preflight, memory refusal, duplicate-claim checks, process
identity, quiescence, and terminal observation remain mandatory. The
300-second estimate is below the 7,200-second performance-review and explicit-
approval threshold.

At prepare, Root's exact registered worktree supplies the canonical native
Windows cwd. Its branch, HEAD, registration, cleanliness, receipt, and
candidate-null facts must still match. CM and the Operator freeze the observed
absolute cwd only as runtime provenance; this artifact does not copy it into a
durable path or create, switch, commit, push, integrate, or delete a worktree.

Relative to that cwd, the official run output root remains exactly:

`temp/directions/ucope/exp/ucope-r03-s1-current-byte-acceptance-20260825-01`

The corrected direction claim and cooperative lock are exactly:

- `temp/directions/ucope/.run-claims/5410a4060ce1e625044056e263d0cc2c09a2c5fa5a6a1a8593db28f244c78607.json`;
- `temp/directions/ucope/.run-claims/.5410a4060ce1e625044056e263d0cc2c09a2c5fa5a6a1a8593db28f244c78607.json.lock`.

The official manifest, preflight, execute-preflight, runner specification,
stdout, stderr, checkpoints, metrics, artifacts, and run-local locks stay in
the run root. Child TEST work and benchmark output stay under
`temp/directions/ucope/test/s1`. Both scopes are disposable, result-blind
technical evidence and are not durable scientific authority.

### Validator-compatible engineering scope

Every engineering-state revision remains bound to:

```text
path=docs/research/candidates/ucope/DIRECTION.md
heading=Engineering request
sha256=ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d
```

Engineering `scope_ref` must not point to R01, R02, or R03. This R03 artifact
is carried by exact content reference and the headings below in CM input,
verification, acceptance, and next-action refs. Engineering-state CAS remains
writer `CM-ucope`, begins from revision `3`, and preserves the validator-
required `scope_ref.path`.

## Engineering request — S1 only

Root may deliver one new immutable packet to canonical `CM-ucope`. CM first
revalidates R03, the registered clean worktree, current source/test equality,
and the corrected command/claim tuple. It makes only necessary repairs inside
the exact owned paths, then either accepts every S1 predicate or returns the
exact failed predicate and resume condition.

The exact downstream owned paths are:

- `docs/research/candidates/ucope/workflow/engineering/state.json`;
- `experiments/candidates/ucope/variable_k_paid_probe_r01_r03`;
- `tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s0.py`;
- `tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s1.py`;
- `temp/directions/ucope/test/s1`;
- `temp/directions/ucope/exp/ucope-r03-s1-current-byte-acceptance-20260825-01`;
- `temp/directions/ucope/.run-claims/5410a4060ce1e625044056e263d0cc2c09a2c5fa5a6a1a8593db28f244c78607.json`;
- `temp/directions/ucope/.run-claims/.5410a4060ce1e625044056e263d0cc2c09a2c5fa5a6a1a8593db28f244c78607.json.lock`.

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
hard minutes for the largest TEST command. Construction and TEST remain CPU-
only with GPU forbidden, at most `16` cores, `8 GiB` peak RSS, `2 GiB`
scratch, `0.75 GiB` durable evidence, and `8 GiB` aggregate read-plus-write
I/O. Actual cost and remaining forecast must preserve the non-replenishable
`15` managed / `18` hard total engineer-day and `6` managed / `12` hard
cumulative TEST CPU-hour envelopes.

The already-selected sole Sol-high `hmasd-implementer` may be reused only if a
necessary in-scope repair is established. A second Implementer or substitute
capability is outside this request. Reviewer remains prohibited until one
coherent S2 candidate exists, and no Verifier is authorized.

### Acceptance criteria

`CM-ucope` may record `S1_TECHNICALLY_ACCEPTED` only when all of the following
hold on the accepted current bytes:

1. Every frozen authority reference matches before material engineering work,
   and every changed or generated material path stays inside the exact owned
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
6. The exact argv is re-derived with one NUL byte and matches command SHA
   `dd580636e12aaf248532ad8704429a3fe097a710089af499eebfbdbd0687fb1c`,
   parameters SHA
   `f52b283f82b7d3ffa0bf8c6970725c2c6ca8675362c0b1c2e6ec5831ffacbf41`,
   and claim SHA
   `5410a4060ce1e625044056e263d0cc2c09a2c5fa5a6a1a8593db28f244c78607`.
7. Exactly one Operator performs official prepare and one foreground execute
   from the matching registered worktree and owns the command through terminal
   observation. Wrapper evidence stays in the exact run root and corrected
   claim paths; child TEST evidence stays in `temp/directions/ucope/test/s1`.
8. Focused S0/S1 tests and the benchmark establish at least `75%` effective CPU
   concurrency, at most `30%` parallel overhead, at least `1.25x` declared
   reference throughput, and cold compile/load no greater than six minutes.
9. The conservative complete-transaction projection remains no greater than
   `1,800` seconds on at most 24 CPU cores, `12` CPU-hours, `10 GiB` peak RSS,
   and `6 GiB` aggregate I/O, while actual S1 TEST remains inside the stricter
   16-core/8-GiB construction envelope. All stage and cumulative engineer-day,
   CPU-hour, wall, RSS, scratch, durable, I/O, and device caps remain satisfied.
10. Engineering state advances from revision `3` through expected-revision CAS
    with writer `CM-ucope`, keeps `scope_ref` bound to the exact `DIRECTION.md`
    reference, records R03 in input/verification/acceptance refs, and reports
    exact changed paths, run and verification refs, measured costs/resources,
    remaining unknowns, and the bounded S1 disposition.

Any missing or failed item requires an S1-scoped incompatibility return naming
the failed predicate, observed refs, actual cost/resource facts, and exact
resume condition. It is not a negative scientific result and must not be
reported as a bare `BLOCKED` state or repaired by changing the scientific
object.

### Explicit non-scope

This request does not authorize:

- use of the superseded `b968adea...` command identity,
  `348a15a4...` claim identity, or either R02 claim path;
- any change to the R03 host, panels, arms, coordinates, periods, seeds,
  episodes, rewards, optimizer, thresholds, diagnostics, branch map, activity
  boundary, strongest alternative, claim ceiling, or result firewall;
- S2 finite evaluation, DP/RAW-PERMAVG diagnostics, attribution, complete
  output, production modules, Reviewer, SANCheck, or S2 release;
- registered master seeds, the complete training/evaluation panel, question-
  relevant output, a scientific result or partial value, empirical identity
  or coordinate, provider operation, deployment, or flight;
- direct or detached execution, a second Operator, a second manifest, replay
  after unknown commitment, a second Implementer, a Verifier, cap
  replenishment, or substitution of another scientific object;
- CM or Operator creation, switching, commit, push, integration, or deletion
  of the registered worktree; Root alone owns runtime worktree facts;
- modification of `DIRECTION.md`, R01, R02, this immutable R03, research state,
  Portfolio, registry, external-review state, shared core, or any material path
  outside the exact downstream owned set; or
- any Git, provider, deployment, flight, or other external Effect.

This artifact creates no task, Operator, preflight, manifest, claim, run,
worktree, or effect. The follow-on CM packet has `effect_refs=[]` because no
run or external Effect exists at publication. Root owns canonical task and
worktree orchestration; CM owns the later bounded engineering cycle; the
single Operator owns only the exact prepared command through terminal
observation. S1 acceptance does not begin S2.
