# UCOPE R03 S1 engineering request R05

Decision owner: EM-ucope

```text
document_kind=DIRECTION_ENGINEERING_REQUEST
document_revision=R05
direction_id=ucope
logical_identity=EM-ucope
generation=1
exact_object_revision=UCOPE-NEXT-VARIABLE-K-PAID-PROBE-CONTAINMENT-R01-SCIENCE-20260823-03
prior_request_sha256=874bee1e49837182b45a2fe3fa62c2ba0c12f1443386bd15130b296e5cad9fda
prior_cm_work_id=9df5d74039692dd54d294cdd906bd4e83e71daea7254a6a9190d729bb2def300
cm_disposition=S1_R04_BASETEMP_PARENT_MISSING
science_revision=UNCHANGED
engineering_stage=S1_ONLY
S2_release=false
question_relevant_output=NONE
empirical_authority=false
effect_refs=EMPTY_AT_HANDOFF
```

## Frozen authority and bounded conclusion

The inbound Work Packet was intaken idempotently as work id
`441d6deaf755fdf1abf93c7b7bd0e96116b682e1abb6273353c81a53990f8377`.
Before this artifact was created, its scope and every authority reference
matched the following exact bytes or revisions:

| Reference | Frozen identity |
| --- | --- |
| `.codex/runtime/work/ready/441d6deaf755fdf1abf93c7b7bd0e96116b682e1abb6273353c81a53990f8377/packet.json` | SHA-256 `32796327a55e0c8bddc4e8072d399c9bea6e39bb4bb03868ff617c48019cf27f` |
| `.codex/runtime/work/ready/9df5d74039692dd54d294cdd906bd4e83e71daea7254a6a9190d729bb2def300/packet.json` | SHA-256 `98553fb7b5ba1da52400fcedb8a09e48f7030176f4c1c2852052838300e6af1a` |
| `.codex/runtime/worktrees.json` | revision `5`, SHA-256 `c73f2e597b9d47eee42d9031775e86bcd16d961ccf774244f65aa01db41ed84c` |
| `docs/research/portfolio/PORTFOLIO.md` | SHA-256 `922c20cf071f03a710f9e1597fda8ee826cd32bc10b89fd74331daaf7c82caaf` |
| `docs/research/portfolio/workflow/registry.json` | revision `9`, SHA-256 `95e3dd2aaf0c54b589b6f29ed51aadd0871300ba6ec528f64e12509550e03941` |
| `docs/research/candidates/ucope/DIRECTION.md` | SHA-256 `ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d` |
| `docs/research/candidates/ucope/UCOPE_R03_S1_ENGINEERING_REQUEST_R03_20260825.md` | SHA-256 `1c78a75d418181c949c142220c27326958baaae914c54666d6e040f5f8b02f08` |
| `docs/research/candidates/ucope/UCOPE_R03_S1_ENGINEERING_REQUEST_R04_20260825.md` | SHA-256 `874bee1e49837182b45a2fe3fa62c2ba0c12f1443386bd15130b296e5cad9fda` |
| `docs/research/candidates/ucope/workflow/research/state.json` | revision `7`, SHA-256 `1dc04de644d20c8cf609b72d044a96245ba836fd48a89befa150d4328b91a02c` |
| `docs/research/candidates/ucope/workflow/engineering/state.json` | revision `5`, SHA-256 `173bb7efc6ea8d68d923b1fcbdd508534a59bd6275024d4219f078bff7e0184a` |
| `temp/directions/ucope/test/s1/S1_R03_RESULT_RUN_ENVIRONMENT_INCOMPATIBILITY.json` | SHA-256 `f3dea1165b939174f0cbb0301dfd40465a29ebfa533687450390d2248dc6f36f` |
| `temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260825-02/S1_R04_BASETEMP_PARENT_INCOMPATIBILITY.json` | SHA-256 `e754208383220b66e30fddcae0a8e8603e2ffff212236132f698cecfae502023` |
| `temp/runtime/receipts/wt-ucope-engineering-ucope-r03-s1-current-byte-acceptance-02.json` | SHA-256 `473c393b9c7b600681f0cae747c26721bf6802fe18c89f82b87d004ed4d841e5` |
| `scripts/hmasd_run.py` | SHA-256 `a072f8a50c825a19d91189b2330b19dc9c4198810d8453a5ae8c9057e77453d4` |
| `scripts/hmasd_state.py` | SHA-256 `8e7b6c43d8d70ae3e5769084c7e2fec19e8626404d154c68639a2f83632bd653` |
| `scripts/hmasd_work_packet.py` | SHA-256 `a3a7f7b7a62b74fba3ac335e8ffc1897cd9435bcbc41a4549fad1571d3b4d9fb` |

The bounded conclusion is a second command-environment interface correction,
not a new scientific judgment. The R04 command correctly moved pytest
`--basetemp` under direction-owned S1 TEST storage, but the exact parent
`temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260825-02`
did not exist in the fresh assignment. Pytest attempted
`pathlib.Path.mkdir(parents=false)` for its base directory. Three `tmp_path`
fixture setups therefore raised `FileNotFoundError: [WinError 3]`; pytest
reported `39 passed, 3 errors` in `10.99` seconds and the complete result
process lasted `12.769961` seconds. The wrapper stopped before the benchmark,
no benchmark JSON was produced, and every S1 performance gate remains
unevaluated.

The run-02 manifest is terminal revision `4`, status `FAILED`, exit code `1`,
reason `CHILD_EXIT`, with `group_quiescent=true`. Exactly one Operator prepared,
executed once, and observed terminal quiescence. Resource preflight was safe;
no cap violation was observed. Source and focused tests had zero tracked diff
before and after, no Implementer was dispatched, candidate SHA remained null,
and no commit, push, integration, registered-panel access, S2 access,
scientific or partial result, provider operation, deployment, or flight
occurred.

The exact run-02 Effect refs in its retained assignment cwd are:

```text
run_id=ucope-r03-s1-current-byte-acceptance-20260825-02
manifest_sha256=c2abf5bd17fca6688887cf87143df334697d1640c38d61e8f5b7495311d53576
preflight_sha256=2047e25ca204bc1785571e992d6922c69f9641392e5cc29e74834eb6e1cade1a
execute_preflight_sha256=f67c306d5c1d44184c99590dbe2441a6b5c43fe892a4ce17e683ef49f284b9a0
runner_spec_sha256=0f3ade9d48f87365cb2b12e6a4cfe9996631d4c3c59d3af50d6cc2754621366c
stdout_sha256=8194eeace995dad5784f86f6388a2caad12feccea74fda678fd3f7519c955ed6
stderr_sha256=fd8a4565a9f1ed05fa24eee1bedda72b781350e20df8c8341201d78ce7770500
claim_sha256=62557cd908865b7062729766f8a8d215478673e76a6aaf5efa82b32b32bfd7fd
claim_file_sha256=b4f5af4abff3f6b989103f1eb86ffa3f3081ff4e203fd656d9777afbe325e215
```

Run-01 and run-02, both claims, processes, Operators, manifests, logs,
incompatibility records, and evidence-bearing worktrees are terminal immutable
history. Neither may be replayed, resumed, resent, reused for a successor,
relabeled successful, cleaned, or deleted to simulate a fresh cwd. Root retains
both old worktrees under its normal Effect-evidence policy.

## Environment and identity correction

One minimal current-byte S1 retry remains warranted. The successor wrapper
itself creates its exact direction-owned S1 child evidence root with
`parents=True, exist_ok=True` before pytest. This removes any dependency on an
external pre-create operation while retaining the exact tests-then-benchmark
sequence and fail-closed benchmark gate.

The exact new identity is:

```text
run_id=ucope-r03-s1-current-byte-acceptance-20260826-03
assignment_id=ucope-r03-s1-current-byte-acceptance-03
operator_identity=Operator-ucope-r03-s1-current-byte-acceptance-20260826-03
expected_worktree_ref=wt-ucope-engineering-ucope-r03-s1-current-byte-acceptance-03
expected_branch=omp/ucope/engineering/ucope-r03-s1-current-byte-acceptance-03
code_sha=ee06a078c3c5ff904e00c727475c467a25ada1ff
command_sha256=e7d451cf1b1d27c6dbfd563e018986fed80b002acf0cb31e644383b1f2a847c6
parameters_sha256=f52b283f82b7d3ffa0bf8c6970725c2c6ca8675362c0b1c2e6ec5831ffacbf41
claim_sha256=6dbda9b02e194c79f39c5499e3e630203f9d8f5b502ae27d29b1a5be7a9c9b93
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
  "import subprocess,sys; from pathlib import Path; Path('temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260826-03').mkdir(parents=True, exist_ok=True); py=sys.executable; r=subprocess.run([py,'-m','pytest','-q','--basetemp','temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260826-03/pytest-basetemp','tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s0.py','tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s1.py']); r.check_returncode(); r=subprocess.run([py,'-m','experiments.candidates.ucope.variable_k_paid_probe_r01_r03.benchmark','--stage','s1','--work-root','temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260826-03/work','--output','temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260826-03/benchmark.json']); raise SystemExit(r.returncode)"
]
```

The exact parameters remain:

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

The pinned runner's one-NUL algorithm and official claim algorithm were applied
without writing, and the Python command string compiled successfully:

```text
separator_hex=00
joined_byte_length=929
command_sha256=e7d451cf1b1d27c6dbfd563e018986fed80b002acf0cb31e644383b1f2a847c6
parameters_sha256=f52b283f82b7d3ffa0bf8c6970725c2c6ca8675362c0b1c2e6ec5831ffacbf41
claim_sha256=6dbda9b02e194c79f39c5499e3e630203f9d8f5b502ae27d29b1a5be7a9c9b93
```

Relative to the future fresh native Windows assignment cwd, the exact scopes
are:

- S1 child evidence root created by the wrapper:
  `temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260826-03`;
- pytest base temporary directory:
  `temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260826-03/pytest-basetemp`;
- benchmark work root:
  `temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260826-03/work`;
- benchmark JSON:
  `temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260826-03/benchmark.json`;
- official run root:
  `temp/directions/ucope/exp/ucope-r03-s1-current-byte-acceptance-20260826-03`;
- direction claim:
  `temp/directions/ucope/.run-claims/6dbda9b02e194c79f39c5499e3e630203f9d8f5b502ae27d29b1a5be7a9c9b93.json`;
- cooperative claim lock:
  `temp/directions/ucope/.run-claims/.6dbda9b02e194c79f39c5499e3e630203f9d8f5b502ae27d29b1a5be7a9c9b93.json.lock`.

The S1 evidence root must be absent before the result command starts. Root and
CM must not externally pre-create it to repair run-02. The frozen successor
command's explicit `Path(...).mkdir(parents=True, exist_ok=True)` is the first
operation that creates it, before either pytest or benchmark is invoked.

### Fresh assignment cwd prerequisite

Root must provision a third fresh native Windows assignment cwd before the new
packet is reconciled for execution. The required assignment id, worktree ref,
branch, and code SHA are frozen above. Root records the fresh worktree and its
normal exact receipt. It must be registered, clean in tracked source/test
paths, candidate-null, at exact code SHA
`ee06a078c3c5ff904e00c727475c467a25ada1ff`, and have all new TEST/run/claim
scopes absent. CM refuses official prepare and returns the exact missing or
mismatched runtime fact if any prerequisite is absent.

Provisioning is outside this artifact and its follow-on packet. The packet does
not freeze current worktree-registry revision `5`, because legitimate Root
provisioning advances that runtime registry. It instead freezes the expected
worktree identity and requires CM to observe the new live registration and
receipt before prepare. Root must preserve both existing effect-bearing
worktrees unchanged.

## Validator-compatible engineering scope

Every engineering-state revision remains bound to:

```text
path=docs/research/candidates/ucope/DIRECTION.md
heading=Engineering request
sha256=ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d
```

Engineering `scope_ref` must not point to R01 through R05. R05 is carried by
exact content reference and the headings below as acceptance, input,
verification, and next-action authority. Engineering-state CAS remains writer
`CM-ucope` and begins from revision `5`.

R05 supersedes R04 and CM work id
`9df5d74039692dd54d294cdd906bd4e83e71daea7254a6a9190d729bb2def300`
only for the successor mkdir/environment, assignment, run, command, claim,
claim paths, and Operator identity. R03/R04 and all prior packets remain
authority and provenance for the unchanged scientific contract and terminal
run-01/run-02 Effects. Their earlier supersession relationships remain intact.

## Engineering request — S1 only

After Root provisions the exact fresh assignment cwd, canonical `CM-ucope` may
perform one current-byte result-blind S1 acceptance attempt. CM first validates
all immutable refs, the new registration and receipt, exact tracked bytes, the
new command/parameters/claim tuple, absent new TEST/run/claim scopes, and the
absence of another owner. No source or test modification is authorized. The
successor only reads frozen current bytes and writes engineering state plus its
exact disposable TEST/run/claim evidence.

The exact downstream writable paths are:

- `docs/research/candidates/ucope/workflow/engineering/state.json`;
- `temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260826-03`;
- `temp/directions/ucope/exp/ucope-r03-s1-current-byte-acceptance-20260826-03`;
- `temp/directions/ucope/.run-claims/6dbda9b02e194c79f39c5499e3e630203f9d8f5b502ae27d29b1a5be7a9c9b93.json`;
- `temp/directions/ucope/.run-claims/.6dbda9b02e194c79f39c5499e3e630203f9d8f5b502ae27d29b1a5be7a9c9b93.json.lock`.

Exactly one later `hmasd-experiment-operator` owns the exact new command from
official prepare through one foreground execute and terminal observation. It
must use `scripts/hmasd_run.py`; direct or detached launch, a second Operator
or manifest, replay, and reuse of either old claim are forbidden. Resource
preflight, memory refusal, duplicate-claim checks, process identity,
descendant provenance, quiescence, terminal observation, and independently
hashed output remain mandatory. The 300-second estimate is below the
7,200-second performance-review and explicit-approval threshold.

The source-bound native host and loader; balanced PERSISTENT, REDRAW, and
SEVERED populations; all six arms; the six counter namespaces and sharing law;
paired initialization and arm-private ACTION; the `13->64->64->1` scorer and
`9->32->1` baseline; ordinary-FP32 REINFORCE, entropy, AdamW, clipping, and
deterministic reduction; exact support counters; strict 90-slot final-checkpoint
schema; and atomic batch-frontier crash/resume law remain exactly frozen.
Result-blind fixtures may cover every legal action, history, panel, and width,
but may not instantiate the registered complete population or emit a
scientific value.

The S1 stage remains `6` managed / `7` hard engineer-days, cumulative
result-blind TEST `3` managed / `6` hard CPU-hours, and `25` managed / `45`
hard minutes for the largest TEST command. Construction and TEST remain CPU-
only with GPU forbidden, at most `16` cores, `8 GiB` peak RSS, `2 GiB`
scratch, `0.75 GiB` durable evidence, and `8 GiB` aggregate read-plus-write
I/O. The complete-transaction projection must remain at most `1,800` seconds
on at most `24` CPU cores, `12` CPU-hours, `10 GiB` peak RSS, and `6 GiB`
aggregate I/O. Actual cost and remaining forecast preserve the non-replenishable
`15` managed / `18` hard total engineer-day and `6` managed / `12` hard
cumulative TEST CPU-hour envelopes.

### Acceptance criteria

`CM-ucope` may record `S1_TECHNICALLY_ACCEPTED` only when every item below holds
on the accepted current bytes:

1. Every frozen authority ref matches; Root's third fresh worktree registration
   and receipt match the expected identity; run-01/run-02 and both worktrees
   stay intact; and every new write remains inside the exact writable set.
2. The new S1 child evidence root is absent before execute, then the exact
   wrapper creates it with `parents=True, exist_ok=True` before pytest. No
   external pre-create repairs or replays run-02.
3. Native fixture-oracle equality holds for reset, root-step, probe, tail-step,
   terminal behavior, and every panel and channel intervention, with no Python
   environment fallback.
4. Integer RNG namespace, address, sharing, paired initialization, arm-private
   ACTION, stable row order, deterministic reduction, sequential/parallel
   equivalence, and crash/resume equality match the frozen law with no repeated
   optimizer step.
5. Parameters, features, activations, rewards, returns, gradients, optimizer
   state, serialization metadata, and reporting reductions conform to
   `HMASD-MARL-FP32-BASELINE-V1`; no FP64, mixed, proof-grade hot path, or
   precision exception exists. The narrow result-blind FP32 sensitivity check
   remains present.
6. Support counters, checkpoint/frontier schema, atomic replacement,
   malformed-input refusal, and the result firewall are complete; no partial
   or complete R03 package crosses the activity boundary.
7. The exact argv is re-derived with one NUL byte and matches command SHA
   `e7d451cf1b1d27c6dbfd563e018986fed80b002acf0cb31e644383b1f2a847c6`,
   parameters SHA
   `f52b283f82b7d3ffa0bf8c6970725c2c6ca8675362c0b1c2e6ec5831ffacbf41`,
   and claim SHA
   `6dbda9b02e194c79f39c5499e3e630203f9d8f5b502ae27d29b1a5be7a9c9b93`.
8. Exactly one new Operator performs official prepare and one foreground
   execute from the matching fresh cwd and owns the command through terminal
   observation. Wrapper evidence stays in the exact run root and claim paths;
   child TEST evidence stays in the exact new S1 evidence root.
9. Both focused S0/S1 tests complete successfully before the result-blind
   benchmark. The benchmark establishes at least `75%` effective CPU
   concurrency, at most `30%` parallel overhead, at least `1.25x` declared
   reference throughput, and cold compile/load no greater than six minutes.
10. The complete-transaction projection and actual S1 TEST remain inside every
    frozen wall, core, CPU-hour, RSS, scratch, durable, I/O, device,
    engineer-day, and cumulative cap stated above.
11. Engineering state advances from revision `5` through expected-revision CAS
    with writer `CM-ucope`, keeps `scope_ref` bound to exact `DIRECTION.md`,
    records R03/R04/R05, both old terminal Effect refs, the new receipt, exact
    changed paths, run/verification refs, measured resources, remaining
    unknowns, and its bounded S1 disposition.

Any missing or failed item requires an S1- or Effect-scoped return naming the
failed predicate, observed refs, actual resource facts, and exact resume
condition. It is not a negative scientific result and must not be propagated
as a bare `BLOCKED` state or repaired by changing the scientific object.

### Explicit non-scope

This request does not authorize:

- replay, resume, resend, mutation, cleanup, deletion, reuse, or success
  relabeling of run-01 or run-02, either claim/process/Operator/manifest/log set,
  either incompatibility record, or either effect-bearing worktree;
- external pre-creation of the `-03` S1 child evidence root, or any attempt to
  repair run-02 after its terminal observation;
- prepare or execution before Root provisions and records the exact third fresh
  native assignment cwd, or any CM-created/switched/deleted worktree;
- source or test modification, Implementer, candidate, commit, push,
  integration, shared-core change, or Git Effect;
- any change to the R03 host, panels, arms, coordinates, periods, seeds,
  episodes, rewards, optimizer, thresholds, diagnostics, branch map, activity
  boundary, strongest alternative, claim ceiling, or result firewall;
- S2 finite evaluation, DP/RAW-PERMAVG diagnostics, attribution, complete
  output, production modules, Reviewer, Verifier, SANCheck, or S2 release;
- registered master seeds, the complete training/evaluation panel, question-
  relevant output, a scientific result or partial value, empirical identity
  or coordinate, provider operation, deployment, or flight;
- direct or detached execution, a second new Operator, a second new manifest,
  successor replay after unknown commitment, cap replenishment, or scientific-
  object substitution;
- modification of `DIRECTION.md`, R01 through R04, this immutable R05,
  research state, Portfolio, registry, external-review state, or any path
  outside the exact downstream writable set; or
- manager-task creation, provider send, deployment, flight, or any other
  external Effect.

This artifact creates no task, worktree, Operator, preflight, manifest, claim,
run, Git change, or Effect. The follow-on CM packet therefore has
`effect_refs=[]`. Root owns fresh worktree provisioning and canonical task
delivery; CM owns the later bounded engineering cycle; the unique Operator
owns only the exact new prepared command through terminal observation. S1
technical acceptance does not begin S2.
