# UCOPE R03 S1 engineering request R04

Decision owner: EM-ucope

```text
document_kind=DIRECTION_ENGINEERING_REQUEST
document_revision=R04
direction_id=ucope
logical_identity=EM-ucope
generation=1
exact_object_revision=UCOPE-NEXT-VARIABLE-K-PAID-PROBE-CONTAINMENT-R01-SCIENCE-20260823-03
prior_request_sha256=1c78a75d418181c949c142220c27326958baaae914c54666d6e040f5f8b02f08
prior_cm_work_id=4f45a59c022da0db66eed52d357c932dea1a5742757a065531ed86a9861cc032
cm_disposition=S1_R03_RESULT_RUN_ENVIRONMENT_INCOMPATIBLE
science_revision=UNCHANGED
engineering_stage=S1_ONLY
S2_release=false
question_relevant_output=NONE
empirical_authority=false
effect_refs=EMPTY_AT_HANDOFF
```

## Frozen authority and bounded conclusion

The inbound work packet was intaken idempotently as work id
`7aea010bbd9bab9c889c50d67557c8c7bcf8c54e8ffd3e2b205547503b0e13aa`.
Before this artifact was created, its scope and every authority reference
matched the following exact bytes or revisions:

| Reference | Frozen identity |
| --- | --- |
| `.codex/runtime/work/ready/7aea010bbd9bab9c889c50d67557c8c7bcf8c54e8ffd3e2b205547503b0e13aa/packet.json` | SHA-256 `c924f16a785e2a4523f15c7b5752036264c57b9a646ad62fb99be54f60c94ba8` |
| `.codex/runtime/work/ready/4f45a59c022da0db66eed52d357c932dea1a5742757a065531ed86a9861cc032/packet.json` | SHA-256 `6fccad870716ee40701d767c4d38774f4c8b4f8e3279bebd478dc839e1bf0e18` |
| `.codex/runtime/worktrees.json` | revision `3`, SHA-256 `bbac944cbce04bc528c9a2f1fbbcece922c6691f369f1176f4460620ba18dee8` |
| `docs/research/portfolio/PORTFOLIO.md` | SHA-256 `922c20cf071f03a710f9e1597fda8ee826cd32bc10b89fd74331daaf7c82caaf` |
| `docs/research/portfolio/workflow/registry.json` | revision `9`, SHA-256 `95e3dd2aaf0c54b589b6f29ed51aadd0871300ba6ec528f64e12509550e03941` |
| `docs/research/candidates/ucope/DIRECTION.md` | SHA-256 `ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d` |
| `docs/research/candidates/ucope/UCOPE_R03_S1_ENGINEERING_REQUEST_R03_20260825.md` | SHA-256 `1c78a75d418181c949c142220c27326958baaae914c54666d6e040f5f8b02f08` |
| `docs/research/candidates/ucope/workflow/research/state.json` | revision `6`, SHA-256 `24a330e1caeb91bfe0cf6ed0ce44f15787c9db2e51bfc8b83c6f34cfdd750805` |
| `docs/research/candidates/ucope/workflow/engineering/state.json` | revision `4`, SHA-256 `850a1b4ea0966f3da3a4944e92236866f2e1ecac16be27e34b93cadfaf12f342` |
| `temp/directions/ucope/test/s1/S1_R03_RESULT_RUN_ENVIRONMENT_INCOMPATIBILITY.json` | SHA-256 `f3dea1165b939174f0cbb0301dfd40465a29ebfa533687450390d2248dc6f36f` |
| `temp/runtime/receipts/wt-ucope-engineering-ucope-r03-s1-current-byte-acceptance.json` | SHA-256 `a16a8447cc426d8586dd8836c82e3e138a5bffa623abd3619e3d95ed414a9454` |
| `scripts/hmasd_run.py` | SHA-256 `a072f8a50c825a19d91189b2330b19dc9c4198810d8453a5ae8c9057e77453d4` |
| `scripts/hmasd_state.py` | SHA-256 `8e7b6c43d8d70ae3e5769084c7e2fec19e8626404d154c68639a2f83632bd653` |
| `scripts/hmasd_work_packet.py` | SHA-256 `a3a7f7b7a62b74fba3ac335e8ffc1897cd9435bcbc41a4549fad1571d3b4d9fb` |

The bounded conclusion is environment-only. The one R03 command reached a
terminal `FAILED` manifest at revision `4`, exit code `1`, reason `CHILD_EXIT`,
with `group_quiescent=true`. Exactly one Operator prepared it, executed it
once, and observed terminal quiescence. Pytest reported `39 passed` and three
fixture-setup errors in `13.80` seconds. All three errors were
`PermissionError: [WinError 5]` while `tmp_path` attempted to enumerate
`C:/Users/fires/AppData/Local/Temp/pytest-of-fires`. The benchmark did not
launch and no benchmark JSON was produced. No registered master seed, complete
panel, S2 path, scientific value, partial scientific value, source/test change,
candidate, commit, push, integration, provider operation, deployment, or flight
occurred. No implementation gap or negative scientific result follows from
this failure, and no S1 acceptance predicate has yet been established.

The old Effect remains immutable in the old assignment cwd. Its exact refs are:

```text
run_id=ucope-r03-s1-current-byte-acceptance-20260825-01
manifest_sha256=4801b1f81cd665b610fb3480701c92a7a5a8882efee342759ef05793e04c7098
preflight_sha256=ad35f2479b6ab1291afab393c4ca46eefb443768637ef7142614202dc3cafc9a
stdout_sha256=656abd54052cfe4a9acbb51687f5ffca14328552bca0f992dd090910e1dc2646
stderr_sha256=0a063b61a0712627fc269abe30fffe37b72c8aef20d817477fdc31055fd6d705
claim_sha256=5410a4060ce1e625044056e263d0cc2c09a2c5fa5a6a1a8593db28f244c78607
claim_file_sha256=920d0a6ef81d6879c0cffb7dcb0f8e4566ec7f6c9713f1e6a4ce29b9dcab7400
```

That run, claim, process, Operator identity, and command are terminal. They
must never be replayed, resumed, resent, reused for a successor, relabeled
successful, or deleted to make a cwd appear clean. The old registered worktree
and its ignored run evidence must remain intact until Root applies its normal
evidence-retention policy.

## Environment and identity correction

S1 acceptance remains worth one minimal current-byte retry. The successor uses
an exact pytest `--basetemp` below its direction-owned S1 TEST evidence root,
so fixture setup does not depend on the inaccessible system pytest root. Tests
still precede the benchmark, and a failing test prevents benchmark launch.

The exact new identity is:

```text
run_id=ucope-r03-s1-current-byte-acceptance-20260825-02
assignment_id=ucope-r03-s1-current-byte-acceptance-02
operator_identity=Operator-ucope-r03-s1-current-byte-acceptance-20260825-02
expected_worktree_ref=wt-ucope-engineering-ucope-r03-s1-current-byte-acceptance-02
expected_branch=omp/ucope/engineering/ucope-r03-s1-current-byte-acceptance-02
code_sha=ee06a078c3c5ff904e00c727475c467a25ada1ff
command_sha256=43d7ffdc24a66adf104ea24f5b18f5969191138b9da57626869eca0641e41e58
parameters_sha256=f52b283f82b7d3ffa0bf8c6970725c2c6ca8675362c0b1c2e6ec5831ffacbf41
claim_sha256=62557cd908865b7062729766f8a8d215478673e76a6aaf5efa82b32b32bfd7fd
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
  "import subprocess,sys; py=sys.executable; r=subprocess.run([py,'-m','pytest','-q','--basetemp','temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260825-02/pytest-basetemp','tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s0.py','tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s1.py']); r.check_returncode(); r=subprocess.run([py,'-m','experiments.candidates.ucope.variable_k_paid_probe_r01_r03.benchmark','--stage','s1','--work-root','temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260825-02/work','--output','temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260825-02/benchmark.json']); raise SystemExit(r.returncode)"
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

The pinned runner's single-NUL algorithm was applied without writing:

```text
SHA256(bytes([0]).join(os.fsencode(part) for part in argv))
separator_hex=00
joined_byte_length=780
command_sha256=43d7ffdc24a66adf104ea24f5b18f5969191138b9da57626869eca0641e41e58
parameters_sha256=f52b283f82b7d3ffa0bf8c6970725c2c6ca8675362c0b1c2e6ec5831ffacbf41
claim_sha256=62557cd908865b7062729766f8a8d215478673e76a6aaf5efa82b32b32bfd7fd
```

Relative to the future fresh native Windows assignment cwd, the exact scopes
are:

- S1 child evidence root:
  `temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260825-02`;
- pytest base temporary directory:
  `temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260825-02/pytest-basetemp`;
- benchmark work root:
  `temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260825-02/work`;
- benchmark JSON:
  `temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260825-02/benchmark.json`;
- official run root:
  `temp/directions/ucope/exp/ucope-r03-s1-current-byte-acceptance-20260825-02`;
- direction claim:
  `temp/directions/ucope/.run-claims/62557cd908865b7062729766f8a8d215478673e76a6aaf5efa82b32b32bfd7fd.json`;
- cooperative claim lock:
  `temp/directions/ucope/.run-claims/.62557cd908865b7062729766f8a8d215478673e76a6aaf5efa82b32b32bfd7fd.json.lock`.

### Fresh assignment cwd prerequisite

Root must provision a fresh native Windows assignment cwd before it delivers
the successor for execution. The required assignment id, worktree ref, branch,
and code SHA are frozen above. Root records the fresh worktree in the runtime
registry and produces its normal exact receipt. The fresh cwd must be registered,
clean in tracked source/test paths, candidate-null, and at exact code SHA
`ee06a078c3c5ff904e00c727475c467a25ada1ff`. CM must refuse prepare and return
the exact missing or mismatched runtime fact if this prerequisite is absent.

Provisioning is intentionally outside this artifact and its follow-on packet.
The packet does not freeze worktree-registry revision `3` as a future
run-validity predicate because legitimate Root provisioning advances that
runtime registry. Instead it freezes the expected worktree identity and makes
the fresh Root receipt and live registration mandatory observations before
prepare. Root must not repurpose, clean, delete, or reuse the old effect-bearing
worktree to satisfy this prerequisite.

## Validator-compatible engineering scope

Every engineering-state revision remains bound to:

```text
path=docs/research/candidates/ucope/DIRECTION.md
heading=Engineering request
sha256=ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d
```

Engineering `scope_ref` must not point to R01, R02, R03, or R04. This R04
artifact is carried by exact content reference and the headings below as
acceptance, input, verification, and next-action authority. Engineering-state
CAS remains writer `CM-ucope` and begins from revision `4`.

R04 supersedes R03 and work id
`4f45a59c022da0db66eed52d357c932dea1a5742757a065531ed86a9861cc032`
only for the successor environment, run, command, claim, claim paths, and
fresh-cwd prerequisite. R03 and the old CM packet remain authority and
provenance for the unchanged scientific contract and the terminal old Effect.
All earlier R03 supersession relationships remain intact.

## Engineering request — S1 only

After Root provisions the exact fresh assignment cwd, canonical `CM-ucope` may
perform one current-byte result-blind S1 acceptance attempt. CM first validates
all immutable refs, the fresh registration and receipt, exact tracked bytes,
the new command/parameters/claim tuple, the empty new run and claim scopes, and
the absence of another owner. No source or test modification is authorized:
the successor only reads the frozen current bytes and writes engineering state
plus its exact disposable TEST/run/claim evidence paths.

The exact downstream writable paths are:

- `docs/research/candidates/ucope/workflow/engineering/state.json`;
- `temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260825-02`;
- `temp/directions/ucope/exp/ucope-r03-s1-current-byte-acceptance-20260825-02`;
- `temp/directions/ucope/.run-claims/62557cd908865b7062729766f8a8d215478673e76a6aaf5efa82b32b32bfd7fd.json`;
- `temp/directions/ucope/.run-claims/.62557cd908865b7062729766f8a8d215478673e76a6aaf5efa82b32b32bfd7fd.json.lock`.

Exactly one later `hmasd-experiment-operator` owns the exact new command from
official prepare through one foreground execute and terminal observation. It
must use `scripts/hmasd_run.py`; direct or detached launch, a second Operator
or manifest, replay, and reuse of the old claim are forbidden. Resource
preflight, memory refusal, duplicate-claim checks, process identity,
quiescence, terminal observation, and independently hashed output remain
mandatory. The 300-second estimate is below the 7,200-second performance-review
and explicit-approval threshold.

The source-bound native host and loader; balanced PERSISTENT, REDRAW, and
SEVERED populations; all six arms; the six counter namespaces and sharing law;
paired initialization and arm-private ACTION; the `13->64->64->1` scorer and
`9->32->1` baseline; ordinary-FP32 REINFORCE, entropy, AdamW, clipping, and
deterministic reduction; exact support counters; strict 90-slot final-checkpoint
schema; and atomic batch-frontier crash/resume law remain exactly as frozen in
R03. Result-blind fixtures may cover every legal action, history, panel, and
width but may not instantiate the registered complete population or emit a
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

1. Every frozen authority ref matches, Root's fresh worktree registration and
   receipt match the exact expected identity, the old worktree and Effect stay
   intact, and every new write stays inside the exact downstream writable set.
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
   precision exception exists. The narrow result-blind FP32 sensitivity check
   remains present.
5. Support counters, checkpoint/frontier schema, atomic replacement,
   malformed-input refusal, and the result firewall are complete; no partial
   or complete R03 package crosses the activity boundary.
6. The exact argv is re-derived with one NUL byte and matches command SHA
   `43d7ffdc24a66adf104ea24f5b18f5969191138b9da57626869eca0641e41e58`,
   parameters SHA
   `f52b283f82b7d3ffa0bf8c6970725c2c6ca8675362c0b1c2e6ec5831ffacbf41`,
   and claim SHA
   `62557cd908865b7062729766f8a8d215478673e76a6aaf5efa82b32b32bfd7fd`.
7. Exactly one new Operator performs official prepare and one foreground
   execute from the matching fresh cwd and owns the command through terminal
   observation. Wrapper evidence stays in the exact new run root and claim
   paths; child TEST evidence, including pytest `--basetemp`, stays in the
   exact new S1 evidence root.
8. Both focused S0/S1 tests complete successfully before the result-blind
   benchmark. The benchmark establishes at least `75%` effective CPU
   concurrency, at most `30%` parallel overhead, at least `1.25x` declared
   reference throughput, and cold compile/load no greater than six minutes.
9. The conservative complete-transaction projection and actual S1 TEST remain
   inside every frozen wall, core, CPU-hour, RSS, scratch, durable, I/O, device,
   engineer-day, and cumulative cap stated above.
10. Engineering state advances from revision `4` through expected-revision CAS
    with writer `CM-ucope`, keeps `scope_ref` bound to exact `DIRECTION.md`,
    records R03, R04, the old terminal Effect refs, the fresh worktree receipt,
    exact changed paths, new run and verification refs, measured resources,
    remaining unknowns, and its bounded S1 disposition.

Any missing or failed item requires an S1- or Effect-scoped return naming the
failed predicate, observed refs, actual resource facts, and exact resume
condition. It is not a negative scientific result and must not be propagated
as a bare `BLOCKED` state or repaired by changing the scientific object.

### Explicit non-scope

This request does not authorize:

- replay, resume, deletion, reuse, mutation, or success relabeling of run
  `ucope-r03-s1-current-byte-acceptance-20260825-01`, its claim, process,
  Operator, manifest, logs, evidence, or worktree;
- prepare or execution before Root provisions and records the exact fresh
  native assignment cwd, or any CM-created/switched/deleted worktree;
- any source or test modification, Implementer, candidate, commit, push,
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
- modification of `DIRECTION.md`, R01, R02, R03, this immutable R04, research
  state, Portfolio, registry, external-review state, or any path outside the
  exact downstream writable set; or
- manager-task creation, provider send, deployment, flight, or any other
  external Effect.

This artifact itself creates no task, worktree, Operator, preflight, manifest,
claim, run, Git change, or Effect. The follow-on CM packet therefore has
`effect_refs=[]`. Root owns fresh worktree provisioning and canonical task
delivery; CM owns the later bounded engineering cycle; the unique Operator
owns only the exact new prepared command through terminal observation. S1
technical acceptance does not begin S2.
