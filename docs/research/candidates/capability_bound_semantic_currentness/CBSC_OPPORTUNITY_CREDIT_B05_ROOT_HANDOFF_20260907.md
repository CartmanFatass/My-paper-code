# CBSC B05 corrected source and prospective Root handoff

**P20 source correction accepted; no run is allocated or launched.** This replaces
P18's unresolved handoff at `2d0f95f091e0f92394bd08535fba62566e9ecb30`; that historical
gap remains in Git. Root integrates the named commits, returns them to DM for
card/code readiness, and requests the future allocation through Portfolio.
Do not execute the literals below under P20 preparation authority.

## Source, card and runtime bindings

P20 authority: `23d0f55983f31e58efe2e5ace5e228451fb2d49b`,
[bounded correction](../../portfolio/handoffs/2026-09-07-p20-cbsc-b05-source-correction.md).
[B05 card](CBSC_OPPORTUNITY_CREDIT_B05_SCIENCE_CARD_20260907.md) at
`a213567ce576ba836427b8490f183120b9de23e6` supplies seed/runtime/primary,
work/600-second caps and ordered return. Correction entry checkout was clean at
`c298c120ff843fb0b2b31f2dff789a16f52b26c1`, `codex/cbsc`,
`C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906`.

Accepted source and tests: **d2753be86c12bfa63c404ac2cac513b914371115**. Use this exact detached
source SHA, even if Root's integration has a different commit identity. The
accepted scientific reference is `a3c2a49bf7002639d43a94f460b688d50c6c42dd`;
only the explicit seed/object/runtime metadata plumbing changes. Entire `omrc_b01/`
and learner numerical methods are unchanged. Preflight source remains separately
`ec8866b3968fcb1566976ce405d7c552d4d9a5de`; direct diff of
`scripts/hmasd_resource_preflight.py` and `scripts/hmasd_platform.py` is empty.
Both are present in the accepted full source commit, so no source overlay occurs.

The same runner now accepts `--b05 --seed 21223` for either formal arm. Without
`--b05`, B04 formal 21217 and engineering 21211 retain their defaults, rejection
and object behavior. B05 has no engineering profile. `B05_OBJECT` changes only
metadata; B1_RUN remains the RNG namespace. The seed reaches host generation,
model initialization, common training uniforms, rollout uniforms and trainer ORDER
addressing unchanged. Summaries, console output, snapshots and paired summary
identify B05. B05 summaries and snapshot metadata record the lexical interpreter,
Python version and Torch version. B04 receives none of these new runtime keys.
The historical module/runner filenames and docstrings still name the reused B04
implementation; they do not override the actual B05 object/seed metadata.

Interpreter for both new arms:
`/home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python`.
P17 observed CPython 3.12.3, NumPy 1.26.3, Torch 2.7.0+cu118 and CUDA build 11.8,
with 23 pins matched. [P17 evidence](CBSC_LOCAL_ACQUISITION_P17_RESULT_EVIDENCE_20260907.md)
is the runtime observation; P20 adds no target-runtime probe or reliability claim.
CPU FP32, one scientific process and one Torch compute thread remain selected.

## Focused acceptance and independent review

Owned source: `scripts/run_cbsc_opportunity_credit_b04.py` and
`experiments/candidates/capability_bound_semantic_currentness/opportunity_credit_b04/{run.py,learner.py,snapshot.py}`.
Focused fixture: mirrored `test_b05_profile.py`. One local check invocation:

```powershell
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/capability_bound_semantic_currentness/test/b05_profile_p20 tests/experiments/candidates/capability_bound_semantic_currentness/opportunity_credit_b04/test_b05_profile.py
```

Result: **13 passed in 6.42 s**, command wall 8.0478434 s, exit 0. The warning
was an unknown `cache_dir` setting with the cache provider deliberately disabled.
Captured result is retained in the authoring checkout at
`temp/directions/capability_bound_semantic_currentness/exp/b05_source_preparation_p20_20260907/checks.txt`.
No repeat suite or old engineering invocation occurred. This charges 8.048 s
of focused local checking; it does not reset the existing directory account.

The fixtures execute actual `run_arm`, inherited train-order/minibatch selection,
tiny constructed reward targets, snapshot save/load and JSON publication/readback.
The real host, recurrent model, numerical minibatch/optimizer and policy evaluator
are replaced. They check both arms across B04 formal/engineering and B05 formal,
seed propagation, common ORDER sequence, counts, update 0/48 primary coverage,
RAW's three rule panels reused by STRUCT, all 32 paired differences, rejection
and object/runtime keys. Wrong seed/object/tape pairs are rejected. These are
boundary evidence, not measured training or native-return observations.

Independent `review_b05` reviewed source/callers and fixture coverage without
rerunning tests or using the target runtime. No material source/test findings.
It traced the unchanged downstream model/uniform/ORDER use beyond mocked entry
boundaries and confirmed no numerical `omrc_b01/` diff. Runtime-version metadata
is explicitly requested by B05 card line 107; no registry, worker, provenance
guard or new supervisor was introduced. Final handoff review is recorded below.

## Requested work, costs and stopping

Per arm: 384 training episodes, 48 rollouts, 768 Adam steps, 58368 training
transitions/9216 decisions, 64 evaluation executions/9728 transitions, 68096
train/evaluation transitions. Pair: 1536 Adam steps, 128 evaluations and 136192
transitions. RAW's three rules add 96 existing-tape passes/2304 action scores;
no additional worlds or trained controls. Both arms start fresh at seed 21223.

Complete cost law remains startup/admission + host generation +
48(project8/rollout8/PPO4x4) + 2(eval32/checkpoint) + RAW context or STRUCT pairing
+ publication/readback + process completion/grace. Preserve card planning
scenarios RAW 159.38 s and STRUCT 181.56 s, each below 600 s. Historical B04 RAW
53.46 s is another reference, not a measurement of this runtime. No new timing
probe is required or claimed. Requested whole caps are **600 s per arm / 1200 s
summed**; summed wall, study critical path and aggregate CPU are distinct.

Each command below starts GNU time before the timeout, task shell, admission,
imports and runner. Existing GNU timeout sends TERM at 598 s and KILL after 2 s,
matching the prior formal whole-cap arrangement. Actual outer wall and supervisor
terminal evidence decide cap conformance; a configured timeout is not proof that
observed elapsed time met 600 s. Runner's internal wall excludes outer setup and
cannot replace it. All STRUCT pair computation/publication/readback runs before
that same command exits; there is no third result-bearing invocation.

## Exact future source staging

The following are standalone **local Python control-plane literals**, for Root
only after allocation. They invoke the existing SSH alias and non-login remote
shell. Source staging uses the existing node proxy route observed in P17; it
performs no admission, package call or candidate execution. A staging failure
returns its concrete fact; it does not consume or restart a learner invocation.
Do not create another authoring branch, overwrite an existing evidence checkout,
or substitute a newer HEAD. Remote checkout identity is printed for inspection.

```python
import subprocess
subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'hmasd-wsl-node', "/usr/bin/env -u BASH_ENV -u ENV HTTP_PROXY=http://127.0.0.1:7890 HTTPS_PROXY=http://127.0.0.1:7890 /bin/bash --noprofile --norc -c 'cd /home/wu/projects/HMASD && /usr/bin/git fetch origin d2753be86c12bfa63c404ac2cac513b914371115 && /usr/bin/git -c core.autocrlf=false worktree add --detach /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907 d2753be86c12bfa63c404ac2cac513b914371115 && /usr/bin/git -C /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907 rev-parse HEAD'"], check=True)
```

## Exact future RAW invocation

Fresh cwd is `/home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907`. Fresh output parent is `/home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b05_20260907`.
The preflight writes `raw-admission.json` under that parent and immediately joins
with `&&` to RAW. It creates the receipt parent; the runner creates fresh `raw/`.
The command does not pre-create the runner's output directory.

```python
import subprocess
subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'hmasd-wsl-node', '/usr/local/bin/agent-task run cbsc-b05-raw-20260907 \'/usr/bin/time -f \'"\'"\'process_wall_seconds=%e peak_rss_kib=%M\'"\'"\' /usr/bin/timeout --signal=TERM --kill-after=2s 598s /usr/bin/env -u BASH_ENV -u ENV OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /bin/bash --noprofile --norc -c \'"\'"\'cd /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907 && /home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b05_20260907/raw-admission.json && exec /home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python scripts/run_cbsc_opportunity_credit_b04.py --b05 --arm RAW-GRU --seed 21223 --output /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b05_20260907/raw\'"\'"\'\''], check=True)
```

Root adopts `cbsc-b05-raw-20260907`, recording actual node/PID/start/command SHA,
cwd and receipt/output paths from acceptance. Existing supervisor log is
`/home/wu/.agent-tasks/cbsc-b05-raw-20260907/task.log`; GNU-time wall/RSS is in
that log. Existing supervisor `status`, `exit_code`, `start_time`, `pid` and
`runner.sh` supply lifecycle and literal evidence. Follow this same handle if
SSH acceptance is uncertain; never blindly repeat the launch.

## RAW observation and collection before STRUCT

Root owns routine observation through the current configured route
(`.codex/hmasd-monitor.toml`, `ROOT_OPERATIONS.md`). Native recipient is this same
CM `/root/dm_amx_cbsc_next/cm_cbsc_opportunity_b04`; DM is
`/root/dm_amx_cbsc_next`. At terminal notification, CM collects **all outcomes**.
Use the status/log literals below for the named accepted handle; collection is
read-only and never runs an evaluator, target import or pair calculation.

```python
import subprocess
from pathlib import Path
local = Path("C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b05_20260907_collection/raw")
local.mkdir(parents=True, exist_ok=True)
for command, filename in [("/usr/local/bin/agent-task status cbsc-b05-raw-20260907", "status.txt"), ("/usr/local/bin/agent-task logs cbsc-b05-raw-20260907 100000", "logs.txt")]:
    result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "hmasd-wsl-node", command], capture_output=True)
    (local / filename).write_bytes(result.stdout)
    (local / (filename + ".stderr")).write_bytes(result.stderr)
    print(filename, result.returncode)
for remote in ["/home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b05_20260907", "/home/wu/.agent-tasks/cbsc-b05-raw-20260907"]:
    print(subprocess.run(["scp", "-r", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "hmasd-wsl-node:" + remote, str(local)]).returncode)
```

A missing output tree after failure is recorded; it does not prevent collection
of supervisor evidence. SSH/scp failure is uncertain collection, not a terminal
scientific result. Reconcile the same handle/files without new candidate work.
Check actual successful terminal, full wall <=600, adjacent admission pass,
summary B05/seed21223/source SHA/runtime prefix/version/CPU FP32/thread1,
48 rollouts/768 Adam/384 train/64 eval and 121349 parameters. Inspect update0/48,
32 endpoint identities, signed returns/rule comparisons, recorded action counts,
loss/credit rows, parameter movement and both snapshots' recorded readback.
Internal snapshot/readback evidence plus collected files is reused; no extra
runtime import or learner replay is a collection prerequisite.

A concrete primary/seed/runtime/information/reward/training/count/pairing defect,
failed admission or cap breach stops the dependent STRUCT. Optional resource
telemetry absence alone does not stop it. RAW's return, rank or sign **never**
selects STRUCT. If integrity permits and both arms were allocated, Root issues
exactly the next literal without a new scientific selection.

## Exact future STRUCT invocation

STRUCT has its own fresh `struct-admission.json`, fresh `struct/` and the exact
new RAW `summary.json`. It never uses old B04 RAW.

```python
import subprocess
subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'hmasd-wsl-node', '/usr/local/bin/agent-task run cbsc-b05-struct-20260907 \'/usr/bin/time -f \'"\'"\'process_wall_seconds=%e peak_rss_kib=%M\'"\'"\' /usr/bin/timeout --signal=TERM --kill-after=2s 598s /usr/bin/env -u BASH_ENV -u ENV OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 /bin/bash --noprofile --norc -c \'"\'"\'cd /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907 && /home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b05_20260907/struct-admission.json && exec /home/wu/.venvs/hmasd-cbsc-system312-local-acquisition-p16-20260907/bin/python scripts/run_cbsc_opportunity_credit_b04.py --b05 --arm STRUCT-CURRENTNESS-GRU --seed 21223 --output /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b05_20260907/struct --raw-result /home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b05_20260907/raw/summary.json\'"\'"\'\''], check=True)
```

Root adopts `cbsc-b05-struct-20260907` with the same bound source/runtime/cwd.
Its supervisor records/log are
`/home/wu/.agent-tasks/cbsc-b05-struct-20260907/`. At terminal, CM collects:

```python
import subprocess
from pathlib import Path
local = Path("C:/Projects/HMASD-worktrees/dm-cbsc-next-20260906/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b05_20260907_collection/struct")
local.mkdir(parents=True, exist_ok=True)
for command, filename in [("/usr/local/bin/agent-task status cbsc-b05-struct-20260907", "status.txt"), ("/usr/local/bin/agent-task logs cbsc-b05-struct-20260907 100000", "logs.txt")]:
    result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "hmasd-wsl-node", command], capture_output=True)
    (local / filename).write_bytes(result.stdout)
    (local / (filename + ".stderr")).write_bytes(result.stderr)
    print(filename, result.returncode)
for remote in ["/home/wu/hmasd-worktrees/cbsc-opportunity-credit-b05-20260907/temp/directions/capability_bound_semantic_currentness/exp/opportunity_credit_b05_20260907", "/home/wu/.agent-tasks/cbsc-b05-struct-20260907"]:
    print(subprocess.run(["scp", "-r", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "hmasd-wsl-node:" + remote, str(local)]).returncode)
```

Apply the same per-arm checks. `struct/paired_summary.json` must be published
and read back by the STRUCT invocation, identify B05/21223/update48 with both
accepted launch SHAs, contain all 32 signed differences and shared context,
and preserve the matched initialization/tape/order/action-uniform identities.
Read the already published JSON and retain both absolute returns/checkpoints;
do not generate a missing pair after the cap or replace missing values with zero.
CM returns all-outcome evidence to DM for prediction/MEI/card intake; Root
integrates named artifacts. No retry, extra seed, acquisition, engineering smoke,
old budget reset or historical-cause series follows.

## Final review and remaining boundary

Independent `review_b05` completed handoff review with no material findings.
It checked exact source/preflight/runtime bindings, separate admissions/outputs,
new RAW pairing input, full-command deadline coverage and all-outcome collection.
CM's stdlib AST/shlex check parsed all five Python blocks and both nested launch
payloads, confirming source SHA, 598+2 bounds, adjacent admission/runner and the
STRUCT-only RAW-result argument. Its record is beside `checks.txt` as
`literal_checks.json`. No prospective source staging/launch/observation/collection
literal above was executed in P20.
The future learner's actual reliability, return, resource peaks and complete wall
remain unobserved. Source acceptance is technical conformance, not science or an
execution allocation. Writer returns to DM after the handoff commit/push.
