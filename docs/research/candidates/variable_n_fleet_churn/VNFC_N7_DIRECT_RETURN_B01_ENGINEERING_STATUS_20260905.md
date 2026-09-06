# B01 source acceptance and first focused-check boundary

Source `33e08f440c2117dcfd9457d825f42fef7b38ccd7` implements the frozen B01 comparison.
Independent review found no unresolved material source defect after the cost-accounting and
same-batch presentation-check repairs. New production538 lines, runner37, tests45; scope:none.
Existing R01/R02/R09/native dynamics are unchanged. Draft PR: https://github.com/CartmanFatass/My-paper-code/pull/2 .

The necessary real training/evaluation/output check has **not completed**. Its first invocation
failed during initialization before learner training or evaluation. This gives no B result,
no learner-cost estimate and no formal2700s readiness conclusion.

## Actual first invocation

Exact command, non-target inputs, node and source are frozen in
`VNFC_N7_DIRECT_RETURN_B01_ENGINEERING_CONTRACT_20260905.md`.
Task `vnfc_b01_check_33e08f440_20260905_01`, configured `wsl_4070`, detached cwd
`/home/wu/hmasd-worktrees/vnfc_b01_check_33e08f440`, terminal exit1.
Admission at2026-09-05T23:09:59Z passed with15,423,397,888 available physical and effective bytes.
The runner imported, built and loaded `output/b01_native.so`, then failed in
`learning.initialize` -> unchanged R01 `_SeedRNG.normal_array` -> `hmac.new`:
`AttributeError: 'HMAC' object has no attribute 'digest_size'` in Python3.10 stdlib `hmac.py:68`.
No native reset/rollout or PPO update had occurred. Output pytest was not reached.

External complete failed-chain measurement:3.90s wall,2.90user+.38system=3.28 CPU seconds;
`time` maximum RSS381,308KiB is its observed maximum, not simultaneous summed process memory.
These are failed preparation costs only. Full per-arm collection/update/evaluation, BCRH and
publication remain unmeasured; unknown values are not replaced with zero.

## Bounded failure localization

Read-only source inspection found no HMAC/hashlib monkeypatch or mutation. The native adapter
had only built/loaded the library and assigned ctypes signatures; no native state function had
run at the failing boundary. A small diagnostic sequence on the exact committed remote checkout
used literal non-target HMAC input `B01-non-target-diagnostic`: four calls with stdlib alone,
four after importing committed `learning`, and10,000 after also loading this invocation's actual
`b01_native.so`. All passed. No new build, rollout or target input was involved.

The smallest failing-step reproduction then used the same committed `learning.initialize`
with seed2026090591, namespace `B01-ENGINEERING-CHECK`, the existing library and one Torch/BLAS
thread. Task `vnfc_b01_initialize_diagnostic_20260905_01` had a30s timeout and fresh admission
at23:12:57Z (15,422,214,144 available physical/effective bytes). It completed both model/optimizer
initializations, exit0, supervisor elapsed6s. No worlds, actions, evaluation or optimizer steps
were run. The original failure is therefore **unreproduced**, not classified as an established
node defect or source defect. No source-supported repair has been identified.

Exact reproduction computation after fresh admission:

```sh
timeout 30s env OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 /home/wu/.venvs/hmasd/bin/python -c 'import ctypes,torch; from experiments.candidates.variable_n_fleet_churn_n7_direct_b01 import learning; torch.set_num_threads(1); torch.set_num_interop_threads(1); library=ctypes.CDLL("temp/directions/variable_n_fleet_churn/b01_check_20260905_01/output/b01_native.so"); models,optimizers=learning.initialize(2026090591,"B01-ENGINEERING-CHECK"); print("non_target_initialize_completed", sorted(models))'
```

Retained evidence under `evidence/b01_check_20260905_01/`: `check.log`, `memory.json`,
`whole_time.txt`, `initialize_diagnostic.log`. Remote original output/library and supervisor
directories remain in place. CM notified the shared tracker of both accepted handles and their
terminal state; no live B01 process remains.

## Current boundary

The card/handoff forbids automatic retries. CM returned this exact same-source, unreproduced
initialization failure to DM/Root for object-tier selection rather than relaunch the whole check.
No scientific seed, arm, checkpoint selection or source was changed. Formal B01 and E01 were
not run. A selected unchanged non-target retry would use a new output/task directory and fresh
node admission; it would still need actual learner/output success and complete cost evidence.
