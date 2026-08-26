# UCOPE R03 S1 engineering request R06

Decision owner: EM-ucope

```text
document_kind=DIRECTION_ENGINEERING_REQUEST
document_revision=R06
direction_id=ucope
logical_identity=EM-ucope
generation=1
exact_object_revision=UCOPE-NEXT-VARIABLE-K-PAID-PROBE-CONTAINMENT-R01-SCIENCE-20260823-03
prior_request_sha256=653d2caf0f9d0c1388568cbdfdae9945e3d0b7ea0cb38002eaa458a2f57a484d
prior_cm_work_id=73e6f89253430c5f643d980ebe1d229f8cae71dab6a1045a697927d5bb5b31e3
cm_disposition=S1_R05_WINDOWS_PENDING_PATH_TOO_LONG
science_revision=UNCHANGED
engineering_stage=S1_ONLY
S2_release=false
question_relevant_output=NONE
empirical_authority=false
effect_refs=EMPTY_AT_HANDOFF
```

## Frozen authority and bounded conclusion

The inbound Work Packet was intaken idempotently as work id
`0570471c78522ceaa902d41ea6e1b88d810716d765c0f8d9cca6aa7cd0c285e2`.
Before this artifact was created, its scope and every authority reference
matched the following exact bytes or revisions:

| Reference | Frozen identity |
| --- | --- |
| `.codex/runtime/work/ready/0570471c78522ceaa902d41ea6e1b88d810716d765c0f8d9cca6aa7cd0c285e2/packet.json` | SHA-256 `fa496d0269d204981cbdf924b1b257e3768897867d08be90a211b1ba08e9229c` |
| `.codex/runtime/work/ready/73e6f89253430c5f643d980ebe1d229f8cae71dab6a1045a697927d5bb5b31e3/packet.json` | SHA-256 `38e3bc9439ea6bf805e700369e5adb18dfe8b8f13774ef20609c6ef73b17a9cf` |
| `.codex/runtime/worktrees.json` | revision `7`, SHA-256 `85910acd0263539065776edf5329e14f35413f7c8f7ba63d73e0050768a87ace` |
| `docs/research/portfolio/PORTFOLIO.md` | SHA-256 `922c20cf071f03a710f9e1597fda8ee826cd32bc10b89fd74331daaf7c82caaf` |
| `docs/research/portfolio/workflow/registry.json` | revision `9`, SHA-256 `95e3dd2aaf0c54b589b6f29ed51aadd0871300ba6ec528f64e12509550e03941` |
| `docs/research/candidates/ucope/DIRECTION.md` | SHA-256 `ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d` |
| `docs/research/candidates/ucope/UCOPE_R03_S1_ENGINEERING_REQUEST_R03_20260825.md` | SHA-256 `1c78a75d418181c949c142220c27326958baaae914c54666d6e040f5f8b02f08` |
| `docs/research/candidates/ucope/UCOPE_R03_S1_ENGINEERING_REQUEST_R04_20260825.md` | SHA-256 `874bee1e49837182b45a2fe3fa62c2ba0c12f1443386bd15130b296e5cad9fda` |
| `docs/research/candidates/ucope/UCOPE_R03_S1_ENGINEERING_REQUEST_R05_20260826.md` | SHA-256 `653d2caf0f9d0c1388568cbdfdae9945e3d0b7ea0cb38002eaa458a2f57a484d` |
| `docs/research/candidates/ucope/workflow/research/state.json` | revision `8`, SHA-256 `004490bff2d31b1b4e407137b8710b5e26ff30629cfffce158c4fb19c1ccc1a4` |
| `docs/research/candidates/ucope/workflow/engineering/state.json` | revision `6`, SHA-256 `cddfdac499e4f0e33c21abfb6300385190e37a347ff7114b33e3608b0bf92245` |
| `temp/directions/ucope/test/s1/S1_R03_RESULT_RUN_ENVIRONMENT_INCOMPATIBILITY.json` | SHA-256 `f3dea1165b939174f0cbb0301dfd40465a29ebfa533687450390d2248dc6f36f` |
| `temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260825-02/S1_R04_BASETEMP_PARENT_INCOMPATIBILITY.json` | SHA-256 `e754208383220b66e30fddcae0a8e8603e2ffff212236132f698cecfae502023` |
| `temp/directions/ucope/test/s1/ucope-r03-s1-current-byte-acceptance-20260826-03/S1_R05_WINDOWS_PENDING_PATH_LENGTH_INCOMPATIBILITY.json` | SHA-256 `124861fa6d05e2937b14d01fdea09fa8752484de6fe8e0dee62fdb2fa1ee2df8` |
| `temp/runtime/receipts/wt-ucope-engineering-ucope-r03-s1-current-byte-acceptance-03.json` | SHA-256 `b983a12767d087c6f49ebf7c8991eb0ce75cd3b3037c81ca61bc96af64fa1d52` |
| `scripts/hmasd_run.py` | SHA-256 `a072f8a50c825a19d91189b2330b19dc9c4198810d8453a5ae8c9057e77453d4` |
| `scripts/hmasd_state.py` | SHA-256 `8e7b6c43d8d70ae3e5769084c7e2fec19e8626404d154c68639a2f83632bd653` |
| `scripts/hmasd_work_packet.py` | SHA-256 `a3a7f7b7a62b74fba3ac335e8ffc1897cd9435bcbc41a4549fad1571d3b4d9fb` |

The bounded conclusion is a native Windows path-budget correction, not an
implementation or scientific revision. Run-03 successfully created its short-
lived TEST parent and pytest base, then completed 41 focused tests. The sole
failure was
`test_s1_atomic_frontier_cold_resume_and_90_slot_schema` during the atomic S1
frontier save. Its parent directory existed at 212 characters and its unchanged
final checkpoint target was 251 characters. The unchanged PID-qualified atomic
pending filename expanded the absolute path to 265 characters, and the Windows
host returned `FileNotFoundError: [WinError 2]` while opening it.

Run-03's benchmark did not launch; no benchmark JSON or S1 performance gate was
produced. No source/test diff, Implementer, candidate, commit, push,
integration, registered-panel access, S2 access, scientific or partial result,
provider operation, deployment, or flight occurred. Resource preflight was
safe and no cap violation was observed. One initial control prepare with
unsupported estimate field names was refused before any manifest, preflight,
claim, child root, or commitment. Thereafter exactly one Operator completed one
successful prepare, one execute, and terminal observation. The manifest is
revision `4`, status `FAILED`, exit code `1`, reason `CHILD_EXIT`, with
`group_quiescent=true`.

The exact run-03 Effect refs in its retained assignment cwd are:

```text
run_id=ucope-r03-s1-current-byte-acceptance-20260826-03
manifest_sha256=9f3dfee1a6ba48139c76f242cc6be66ec2b69e3a906e0387d14cd01ed7543168
preflight_sha256=0b9a96a02d0ebf7b32d321ef72971809882262d500ca894eb2a0aba1eb9ce4f8
execute_preflight_sha256=196afcc4535d68e9f09a8235ada0f5fd33702525c8f976109e88ce18703e390a
runner_spec_sha256=435c4e235e0cb45469ebdff45f86d066fa04ce361044427fabcc6983fbdc5d27
stdout_sha256=b02c9337be6d88c264325d5a526d331ac8e3a4669f91f5810b54185522528fd3
stderr_sha256=974e70346bd6644cb90b4a7c098f54ab49cd01d3765cf6ed6f3f326099381953
claim_sha256=6dbda9b02e194c79f39c5499e3e630203f9d8f5b502ae27d29b1a5be7a9c9b93
claim_file_sha256=1ca9916a3612433e874c218ecf779fa742de5676162ff133686fd8424eee5cd6
```

Runs 01 through 03, all claims, processes, Operators, manifests, logs,
incompatibility records, and evidence-bearing worktrees are terminal immutable
history. None may be replayed, resumed, resent, reused for a successor,
relabeled successful, cleaned, or deleted to simulate a fresh cwd.

## Mechanical Windows path-budget proof

The frozen source constructs the S1 final target as:

```text
Path(work_root).resolve() / "ucope_r01_r03_s1_frontier.TEST_ONLY.pt"
```

The frozen atomic writer constructs its pending sibling as:

```text
target.with_name(f".{target.name}.{os.getpid()}.pending")
```

Neither expression, filename, test, nor checkpoint implementation changes in
R06. The installed pytest `tmp_path` fixture sanitizes the test node name,
truncates it to 30 characters, and requests a numbered directory. The observed
focused S1 directory is exactly
`test_s1_atomic_frontier_cold_r0`.

Counting ASCII Windows path characters excluding the terminating NUL with
`PureWindowsPath` exactly reproduces run-03:

```text
old_parent_length=212
old_final_target_length=251
old_pending_pid=2584
old_pending_length=265
```

This equality validates the counting convention against the actual failure.
The R06 proof uses the exact future native cwd
`C:\Projects\HMASD-worktrees\ucope-engineering-s1r6`, exact TEST root
`temp\directions\ucope\test\s1\r6`, pytest base `p`, benchmark work root `w`,
and benchmark output `b.json`. PID allowance is the 20 decimal digits of the
unsigned 64-bit maximum `18446744073709551615`, which is conservative for the
active Windows host.

The worst focused S1 path is:

```text
cwd=C:\Projects\HMASD-worktrees\ucope-engineering-s1r6
cwd_length=50
parent=C:\Projects\HMASD-worktrees\ucope-engineering-s1r6\temp\directions\ucope\test\s1\r6\p\test_s1_atomic_frontier_cold_r0
parent_length=117
final_target=C:\Projects\HMASD-worktrees\ucope-engineering-s1r6\temp\directions\ucope\test\s1\r6\p\test_s1_atomic_frontier_cold_r0\ucope_r01_r03_s1_frontier.TEST_ONLY.pt
final_target_length=156
worst_pending=C:\Projects\HMASD-worktrees\ucope-engineering-s1r6\temp\directions\ucope\test\s1\r6\p\test_s1_atomic_frontier_cold_r0\.ucope_r01_r03_s1_frontier.TEST_ONLY.pt.18446744073709551615.pending
worst_pending_length=186
hard_validation_limit=240
headroom=54
proof_pass=true
```

All frozen atomic candidates were enumerated under the same 20-digit PID
allowance:

| Candidate | Absolute length |
| --- | ---: |
| focused S1 frontier pending | `186` |
| focused S0 coupon/checkpoint pending | `177` |
| benchmark S1 coupon pending | `161` |
| benchmark S1 I/O frontier pending | `143` |
| benchmark JSON pending | `120` |

The focused S1 pending path is therefore the mechanical worst case and remains
`54` characters below the required maximum of `240`. Before prepare, CM must
recompute this table from the live canonical cwd and exact R06 argv. Any cwd
mismatch or computed maximum above `240` is a no-write scoped return; CM must
not prepare, pre-create result scopes, or substitute another path.

## Short environment and identity correction

One minimal current-byte S1 retry remains warranted with the proven short path
budget. The exact new identity is:

```text
run_id=ucope-s1-r6
assignment_id=s1r6
operator_identity=Operator-ucope-s1-r6
expected_worktree_ref=wt-ucope-engineering-s1r6
expected_branch=omp/ucope/engineering/s1r6
expected_native_cwd=C:\Projects\HMASD-worktrees\ucope-engineering-s1r6
code_sha=ee06a078c3c5ff904e00c727475c467a25ada1ff
command_sha256=5e44006edcb32c51232e6f8a699ef7f21d9d186a9d8a053bfea6030f3d34fb97
parameters_sha256=f52b283f82b7d3ffa0bf8c6970725c2c6ca8675362c0b1c2e6ec5831ffacbf41
claim_sha256=0adc316e593a168f3fd35dc3465db120e4b117f922942044d38b12c490f4afd4
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
  "import subprocess,sys; from pathlib import Path; Path('temp/directions/ucope/test/s1/r6').mkdir(parents=True, exist_ok=True); py=sys.executable; r=subprocess.run([py,'-m','pytest','-q','--basetemp','temp/directions/ucope/test/s1/r6/p','tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s0.py','tests/experiments/candidates/ucope/test_variable_k_paid_probe_r01_r03_s1.py']); r.check_returncode(); r=subprocess.run([py,'-m','experiments.candidates.ucope.variable_k_paid_probe_r01_r03.benchmark','--stage','s1','--work-root','temp/directions/ucope/test/s1/r6/w','--output','temp/directions/ucope/test/s1/r6/b.json']); raise SystemExit(r.returncode)"
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
joined_byte_length=720
command_sha256=5e44006edcb32c51232e6f8a699ef7f21d9d186a9d8a053bfea6030f3d34fb97
parameters_sha256=f52b283f82b7d3ffa0bf8c6970725c2c6ca8675362c0b1c2e6ec5831ffacbf41
claim_sha256=0adc316e593a168f3fd35dc3465db120e4b117f922942044d38b12c490f4afd4
```

Relative to the future fresh cwd, the exact writable runtime scopes are:

- S1 child evidence root created by the wrapper:
  `temp/directions/ucope/test/s1/r6`;
- pytest base temporary directory:
  `temp/directions/ucope/test/s1/r6/p`;
- benchmark work root:
  `temp/directions/ucope/test/s1/r6/w`;
- benchmark JSON:
  `temp/directions/ucope/test/s1/r6/b.json`;
- official run root: `temp/directions/ucope/exp/ucope-s1-r6`;
- direction claim:
  `temp/directions/ucope/.run-claims/0adc316e593a168f3fd35dc3465db120e4b117f922942044d38b12c490f4afd4.json`;
- cooperative claim lock:
  `temp/directions/ucope/.run-claims/.0adc316e593a168f3fd35dc3465db120e4b117f922942044d38b12c490f4afd4.json.lock`.

The S1 evidence root must be absent before execute. Root and CM must not
externally pre-create it; the frozen command's explicit
`Path(...).mkdir(parents=True, exist_ok=True)` creates it before pytest.

### Fresh short assignment cwd prerequisite

Root must provision the exact fresh native Windows assignment `s1r6` before
the new packet is reconciled for execution. It must register worktree ref
`wt-ucope-engineering-s1r6`, branch `omp/ucope/engineering/s1r6`, canonical cwd
`C:\Projects\HMASD-worktrees\ucope-engineering-s1r6`, and produce receipt
`temp/runtime/receipts/wt-ucope-engineering-s1r6.json`. The worktree must be at
code SHA `ee06a078c3c5ff904e00c727475c467a25ada1ff`, clean in tracked
source/tests, candidate-null, and have all R06 TEST/run/claim scopes absent.

Provisioning is outside this artifact and its follow-on packet. The packet does
not freeze worktree-registry revision `7`, because legitimate Root provisioning
advances it. CM observes the future live registration and receipt, then repeats
the exact path-budget proof before prepare. Root preserves all three existing
effect-bearing worktrees unchanged.

## Validator-compatible engineering scope

Every engineering-state revision remains bound to:

```text
path=docs/research/candidates/ucope/DIRECTION.md
heading=Engineering request
sha256=ad2751f64021596e6831fbc051f46f0f5450f815c458771dc9d1f71ac068f22d
```

Engineering `scope_ref` must not point to R01 through R06. R06 is carried by
exact content reference and the headings below as acceptance, input,
verification, and next-action authority. Engineering-state CAS remains writer
`CM-ucope` and begins from revision `6`.

R06 supersedes R05 and CM work id
`73e6f89253430c5f643d980ebe1d229f8cae71dab6a1045a697927d5bb5b31e3`
only for assignment/run/TEST path budget and the derived command, claim, claim
paths, and Operator identity. R03 through R05 and all prior packets remain
authority and provenance for unchanged science and terminal runs 01 through
03. Earlier supersession relationships remain intact.

## Engineering request — S1 only

After Root provisions the exact short assignment cwd, canonical `CM-ucope` may
perform one current-byte result-blind S1 acceptance attempt. CM first validates
all immutable refs, the live registration and receipt, exact tracked bytes, the
new command/parameters/claim tuple, absent R06 scopes, the mechanical path
budget, and the absence of another owner. No source, test, or checkpoint
implementation modification is authorized.

The exact downstream writable paths are:

- `docs/research/candidates/ucope/workflow/engineering/state.json`;
- `temp/directions/ucope/test/s1/r6`;
- `temp/directions/ucope/exp/ucope-s1-r6`;
- `temp/directions/ucope/.run-claims/0adc316e593a168f3fd35dc3465db120e4b117f922942044d38b12c490f4afd4.json`;
- `temp/directions/ucope/.run-claims/.0adc316e593a168f3fd35dc3465db120e4b117f922942044d38b12c490f4afd4.json.lock`.

Exactly one later `hmasd-experiment-operator` owns the exact new command from
official prepare through one foreground execute and terminal observation. It
must use `scripts/hmasd_run.py`; direct/detached launch, a second Operator or
manifest, replay, and reuse of any old claim are forbidden. Resource preflight,
memory refusal, duplicate-claim checks, process and descendant identity,
quiescence, terminal observation, and independently hashed output remain
mandatory. The 300-second estimate is below the 7,200-second review/approval
threshold.

The source-bound native host and loader; balanced PERSISTENT, REDRAW, and
SEVERED populations; all six arms; six counter namespaces and sharing law;
paired initialization and arm-private ACTION; `13->64->64->1` scorer and
`9->32->1` baseline; ordinary-FP32 REINFORCE, entropy, AdamW, clipping, and
deterministic reduction; exact support counters; strict 90-slot final-checkpoint
schema; and unchanged atomic batch-frontier crash/resume law remain frozen.
Result-blind fixtures may cover every legal action, history, panel, and width,
but may not instantiate the registered complete population or emit a
scientific value.

The S1 stage remains `6` managed / `7` hard engineer-days, cumulative
result-blind TEST `3` managed / `6` hard CPU-hours, and `25` managed / `45`
hard minutes for the largest TEST command. Construction and TEST remain CPU-
only with GPU forbidden, at most `16` cores, `8 GiB` peak RSS, `2 GiB`
scratch, `0.75 GiB` durable evidence, and `8 GiB` aggregate read-plus-write
I/O. The complete-transaction projection remains at most `1,800` seconds on at
most `24` CPU cores, `12` CPU-hours, `10 GiB` peak RSS, and `6 GiB` aggregate
I/O. Actual cost and forecast preserve the non-replenishable `15` managed / `18`
hard total engineer-day and `6` managed / `12` hard cumulative TEST CPU-hour
envelopes.

### Acceptance criteria

`CM-ucope` may record `S1_TECHNICALLY_ACCEPTED` only when every item below holds:

1. Every frozen ref matches; Root's short worktree registration, cwd, branch,
   code SHA, and receipt match exactly; runs 01 through 03 and all three old
   worktrees stay intact; and every new write remains in the exact writable set.
2. Before prepare, the live-cwd path proof reproduces parent `117`, final target
   `156`, worst 20-digit-PID pending `186`, maximum `240`, and headroom `54`;
   every enumerated atomic candidate is no longer than `240`. Any mismatch is a
   no-write scoped return.
3. The R06 TEST root is absent through prepare, then the exact wrapper creates
   it with `parents=True, exist_ok=True` before pytest. No external pre-create
   or old-run replay is used.
4. Native fixture-oracle equality holds for reset, root-step, probe, tail-step,
   terminal behavior, and every panel/channel intervention without fallback.
5. Integer RNG namespaces, addresses, sharing, paired initialization,
   arm-private ACTION, stable row order, deterministic reduction,
   sequential/parallel equivalence, and crash/resume equality match the frozen
   law with no repeated optimizer step.
6. Parameters, activations, rewards, returns, gradients, optimizer state,
   serialization metadata, and reporting reductions conform to
   `HMASD-MARL-FP32-BASELINE-V1`; no FP64, mixed, proof-grade hot path, or
   precision exception exists. The narrow result-blind sensitivity check stays.
7. Support counters, 90-slot checkpoint/frontier schema, unchanged atomic
   replacement, malformed-input refusal, and result firewall are complete; no
   partial or complete R03 package crosses the activity boundary.
8. The exact argv compiles, is re-derived with one NUL byte, and matches command
   SHA `5e44006edcb32c51232e6f8a699ef7f21d9d186a9d8a053bfea6030f3d34fb97`,
   parameters SHA
   `f52b283f82b7d3ffa0bf8c6970725c2c6ca8675362c0b1c2e6ec5831ffacbf41`,
   and claim SHA
   `0adc316e593a168f3fd35dc3465db120e4b117f922942044d38b12c490f4afd4`.
9. Exactly one new Operator performs official prepare and one foreground execute
   from the matching short cwd and owns the command through terminal
   observation. Evidence stays in the exact run/claim/TEST scopes.
10. Both focused S0/S1 tests complete successfully before the result-blind
    benchmark. The benchmark establishes at least `75%` effective CPU
    concurrency, at most `30%` parallel overhead, at least `1.25x` declared
    reference throughput, and cold compile/load no greater than six minutes.
11. The complete-transaction projection and actual TEST remain inside every
    frozen wall, core, CPU-hour, RSS, scratch, durable, I/O, device,
    engineer-day, and cumulative cap stated above.
12. Engineering state advances from revision `6` through expected-revision CAS
    with writer `CM-ucope`, keeps `scope_ref` bound to exact `DIRECTION.md`, and
    records R03 through R06, all three old terminal Effects, short receipt,
    path-budget proof, exact changed/run/verification refs, resources, unknowns,
    and bounded disposition.

Any missing or failed item requires an S1- or Effect-scoped return naming the
failed predicate, observed refs, actual resources, and exact resume condition.
It is not a negative scientific result and must not be propagated as bare
`BLOCKED` or repaired by changing the scientific object.

### Explicit non-scope

This request does not authorize:

- replay, resume, resend, mutation, cleanup, deletion, reuse, or success
  relabeling of runs 01 through 03, any old claim/process/Operator/manifest/log,
  any incompatibility record, or any old worktree;
- modification or renaming of either atomic checkpoint function, the final
  filename `ucope_r01_r03_s1_frontier.TEST_ONLY.pt`, the pending filename law,
  checkpoint schema, atomic replacement, source, or focused tests;
- prepare when the live canonical cwd differs from the exact short cwd or any
  worst-case pending path exceeds `240` characters;
- external pre-creation of the R06 TEST root, or CM-created/switched/deleted
  worktrees;
- Implementer, candidate, commit, push, integration, shared-core change, or
  Git Effect;
- any change to the R03 host, panels, arms, coordinates, periods, seeds,
  episodes, rewards, optimizer, thresholds, diagnostics, branch map, activity
  boundary, strongest alternative, claim ceiling, or result firewall;
- S2 finite evaluation, DP/RAW-PERMAVG diagnostics, attribution, complete
  output, production modules, Reviewer, Verifier, SANCheck, or S2 release;
- registered master seeds, complete panel, question-relevant output,
  scientific/partial value, empirical identity, provider, deployment, or flight;
- direct/detached execution, second new Operator/manifest, successor replay
  after unknown commitment, cap replenishment, or object substitution;
- modification of `DIRECTION.md`, R01 through R05, this immutable R06,
  research state, Portfolio, registry, external-review state, or any path
  outside the exact writable set; or
- manager-task creation or any external Effect.

This artifact creates no task, worktree, Operator, preflight, manifest, claim,
run, Git change, or Effect. The follow-on CM packet therefore has
`effect_refs=[]`. Root owns fresh short-worktree provisioning and canonical task
delivery; CM owns the later bounded engineering cycle; the unique Operator owns
only the exact new prepared command through terminal observation. S1 technical
acceptance does not begin S2.
