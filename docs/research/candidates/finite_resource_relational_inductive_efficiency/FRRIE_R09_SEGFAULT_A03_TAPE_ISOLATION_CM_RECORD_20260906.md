# FRRIE R09 tape-isolation A03 CM record — 2026-09-06

Worktree `C:/Projects/HMASD/.claude/worktrees/grok-frrie-a03`, branch
`grok/frrie-a03-tape-isolation-20260906`, starting HEAD
`df8e1e775652ce9299fab1268a0619b893480450` of `main`. Grok Build implemented
the probe; Git commit/push is the hub's pathspec step. Scope §4: none.

## What was added

| Path | lines | Role |
| --- | ---: | --- |
| `experiments/candidates/finite_resource_relational_inductive_efficiency/tape_isolation_a03.py` | 219 | T0 training replica, lazy T1 evaluation, digest, `run_arm` |
| `scripts/run_frrie_r09_tape_isolation_a03.py` | 45 | argparse entry; `--arm {T0,T1}` |
| `tests/experiments/candidates/finite_resource_relational_inductive_efficiency/test_tape_isolation_a03.py` | 59 | torch-absence subprocess, 64-tape field equality, digest |
| this record | (docs) | identity check, local T0 wall, frozen commands |

Non-test source A=264, D=0, runner 45. No R09 path was edited. `training_inputs_no_torch`
hard-codes `ROSTERS = (9, 15)` from `b01_contact_r02/semantics.py:27` and does not
import `orchestration`, `policy`, `semantics`, `b01_contact_r02`, or `torch`.
T1 lazily imports `b01_contact_r02.tapes` (production import graph, torch present
at work start). T2 is T1 under module-mode pdb; the module does not trace.

## Byte identity of exercised modules

Command (PowerShell; brace expansion expanded to explicit paths):

```
git diff 43eec21e9584c83e5e8d940402d7e4570b454e59 HEAD --stat -- experiments/candidates/finite_resource_relational_inductive_efficiency/tapes.py experiments/candidates/finite_resource_relational_inductive_efficiency/rng.py experiments/candidates/finite_resource_relational_inductive_efficiency/contracts/core.py experiments/candidates/finite_resource_relational_inductive_efficiency/orchestration.py experiments/candidates/finite_resource_relational_inductive_efficiency/policy.py experiments/candidates/finite_resource_relational_inductive_efficiency/b01_contact_r02/tapes.py experiments/candidates/finite_resource_relational_inductive_efficiency/b01_contact_r02/semantics.py
```

Output: empty (no lines). The seven paths are byte-identical to
`43eec21e9584c83e5e8d940402d7e4570b454e59` at HEAD `df8e1e775`. The probe can
run from this sha; a detached 43eec21e worktree is not required.

## Focused test (local)

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/experiments/candidates/finite_resource_relational_inductive_efficiency/test_tape_isolation_a03.py -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/finite_resource_relational_inductive_efficiency/test/tape-isolation-a03-grok
```

Result: `1 passed, 1 warning in 27.54s`. The warning is pytest `cache_dir` under
`-p no:cacheprovider`. The test (a) builds update-1 training inputs in a
subprocess whose stdout is `False` for `'torch' in sys.modules`, (b) equals
`production_training_inputs` on all 64 tapes field by field, (c) `tape_digest`
is stable and matches the production tapes.

Runner `--help` lists `--arm {T0,T1}`, `--repeat`, `--updates`, `--eval-episodes`,
`--out`, `--launch-sha`, `--admission-receipt`.

## Torch-absence check (local)

Import of the new module:

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -c "from experiments.candidates.finite_resource_relational_inductive_efficiency.tape_isolation_a03 import training_inputs_no_torch, run_arm, tape_digest; import sys; print(repr('torch' in sys.modules)); print([m for m in sys.modules if 'torch' in m or 'b01_contact_r02' in m or 'orchestration' in m or 'policy' in m])"
```

```
False
[]
```

After `training_inputs_no_torch(...)` (64 tapes):

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -c "import sys; from experiments.candidates.finite_resource_relational_inductive_efficiency.tape_isolation_a03 import training_inputs_no_torch; tapes = training_inputs_no_torch(bytes.fromhex('00'*31+'01'), 'FRRIE-B09-CONTACT-BLOCK-003', 1); print('torch' in sys.modules); print(len(tapes))"
```

```
False
64
```

Parent `__init__.py` imports only `contracts.core`. No torch-importing module
had to be restructured.

## Local T0 timing (one repetition, `--updates 1`)

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m scripts.run_frrie_r09_tape_isolation_a03 --arm T0 --repeat 1 --updates 1 --out C:/Projects/HMASD/temp/directions/finite_resource_relational_inductive_efficiency/exp/tape-isolation-a03-t0-local --launch-sha df8e1e775652ce9299fab1268a0619b893480450 --admission-receipt C:/Projects/HMASD/temp/directions/finite_resource_relational_inductive_efficiency/exp/tape-isolation-a03-t0-local/admission.json
```

`summary.json` phase `training_update_1`: wall **6.888891300011892 s**,
`tape_count` 64, array `nbytes` **571392**, digest
`0f0fb392c59dcfdbaa475ae8becca03323751d0a849ee6f39c9a8c9d68057b5f`
(production root `…0003`, label `FRRIE-B09-CONTACT-BLOCK-003`).
`torch_present_at_work_start` false, `torch_in_sys_modules` false,
`trace_active` false, `peak_rss_bytes` null (not Linux). Publication path
`summary.json` was written.

Cost law: wall scales with 64 training tapes per update, plus `2 * eval_episodes`
evaluation tapes on T1, times repetitions. Projection from this local T0
sample (same per-tape cost, cap 300 s/arm): T0 full (2 updates × 3 reps)
≈ 41.3 s; T1 (512 eval + 128 training tapes × 3 reps) ≈ 206.7 s. Both under
300 s. A02 on `wsl_4070` finished 512 eval tapes plus a partial training
update in 33 s, so the remote T1 wall may be lower than this local linear
projection. T2 is T1 plus pdb; same cap.

## Frozen `wsl_4070` commands

Node `wsl_4070`, python `/home/wu/.venvs/hmasd/bin/python`, supervisor
`/usr/local/bin/agent-task`. Hub replaces `WT` (absolute detached worktree at
`LAUNCH_SHA`) and `LAUNCH_SHA`. Each arm is its own `agent-task`, unique
output root, fresh admission joined by `&&`, one compute thread, `-X faulthandler`.
Not launched here.

T2 stdin file (operator creates; not a repo path):
`WT/temp/directions/finite_resource_relational_inductive_efficiency/exp/r09_tape_isolation_a03_t2/pdb_stdin.txt`
with eight `q` lines so a postmortem prompt does not block.

T0:

```
/usr/local/bin/agent-task run frrie_r09_tape_isolation_a03_t0_LAUNCH_SHA 'cd WT && mkdir -p temp/directions/finite_resource_relational_inductive_efficiency/technical temp/directions/finite_resource_relational_inductive_efficiency/exp/r09_tape_isolation_a03_t0 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out WT/temp/directions/finite_resource_relational_inductive_efficiency/technical/r09_tape_isolation_a03_t0_admission.json && timeout --signal=TERM --kill-after=5s 300s /home/wu/.venvs/hmasd/bin/python -X faulthandler -m scripts.run_frrie_r09_tape_isolation_a03 --arm T0 --repeat 3 --updates 2 --eval-episodes 256 --out WT/temp/directions/finite_resource_relational_inductive_efficiency/exp/r09_tape_isolation_a03_t0 --launch-sha LAUNCH_SHA --admission-receipt WT/temp/directions/finite_resource_relational_inductive_efficiency/technical/r09_tape_isolation_a03_t0_admission.json'
```

T1:

```
/usr/local/bin/agent-task run frrie_r09_tape_isolation_a03_t1_LAUNCH_SHA 'cd WT && mkdir -p temp/directions/finite_resource_relational_inductive_efficiency/technical temp/directions/finite_resource_relational_inductive_efficiency/exp/r09_tape_isolation_a03_t1 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out WT/temp/directions/finite_resource_relational_inductive_efficiency/technical/r09_tape_isolation_a03_t1_admission.json && timeout --signal=TERM --kill-after=5s 300s /home/wu/.venvs/hmasd/bin/python -X faulthandler -m scripts.run_frrie_r09_tape_isolation_a03 --arm T1 --repeat 3 --updates 2 --eval-episodes 256 --out WT/temp/directions/finite_resource_relational_inductive_efficiency/exp/r09_tape_isolation_a03_t1 --launch-sha LAUNCH_SHA --admission-receipt WT/temp/directions/finite_resource_relational_inductive_efficiency/technical/r09_tape_isolation_a03_t1_admission.json'
```

T2 (T1 under `pdb -c continue`):

```
/usr/local/bin/agent-task run frrie_r09_tape_isolation_a03_t2_LAUNCH_SHA 'cd WT && mkdir -p temp/directions/finite_resource_relational_inductive_efficiency/technical temp/directions/finite_resource_relational_inductive_efficiency/exp/r09_tape_isolation_a03_t2 && printf "q\nq\nq\nq\nq\nq\nq\nq\n" > temp/directions/finite_resource_relational_inductive_efficiency/exp/r09_tape_isolation_a03_t2/pdb_stdin.txt && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out WT/temp/directions/finite_resource_relational_inductive_efficiency/technical/r09_tape_isolation_a03_t2_admission.json && timeout --signal=TERM --kill-after=5s 300s /home/wu/.venvs/hmasd/bin/python -X faulthandler -m pdb -c continue -m scripts.run_frrie_r09_tape_isolation_a03 --arm T1 --repeat 3 --updates 2 --eval-episodes 256 --out WT/temp/directions/finite_resource_relational_inductive_efficiency/exp/r09_tape_isolation_a03_t2 --launch-sha LAUNCH_SHA --admission-receipt WT/temp/directions/finite_resource_relational_inductive_efficiency/technical/r09_tape_isolation_a03_t2_admission.json < temp/directions/finite_resource_relational_inductive_efficiency/exp/r09_tape_isolation_a03_t2/pdb_stdin.txt'
```

## Not verified

T1/T2 were not run (local T0 timing only). Peak RSS is `None` on Windows; Linux
`resource.getrusage` was not exercised. The exception-and-re-raise path was not
hit. 512-episode evaluation wall is projected, not measured. Torch-present-at-T1
start is by import graph, not an executed T1 process. Remote admission, faulthandler,
and pdb stdin were not launched.

scope: none
