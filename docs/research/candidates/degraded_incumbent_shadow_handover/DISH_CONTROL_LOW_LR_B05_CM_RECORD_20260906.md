# DISH B05 seed101 technical record

Implementation base: `18812ba5e62b6e1a877558f735c7bf979386be5b`.
CM branch `codex/cm-dish-b05-seed101-20260906`, worktree
`C:/Projects/HMASD-worktrees/cm-dish-b05-seed101-20260906`.
Contract: [card](DISH_CONTROL_LOW_LR_B05_SCIENCE_CARD_20260906.md) sections 2-4,6-7.

Engineering scope section 4 additions: **none**. Explicit seed/result-name arguments reuse the
existing path; no new guards, schedulers, diagnostics, retry or compatibility machinery.
B04 defaults remain seed89 and B04 name. B05 fixes seed101 and B05 result name while
SHA256 retains ASCII `DISH-CONTROL-LOW-LR-B04/seed/101`.

The seed reaches shared initialization, training reset factory and NativePersistentTrainingFlow.
The unchanged flow creates its own recurrent state, master-addressed sampler, reset factory,
trainer and policy. Native training state is new per arm; saved common initial model bytes and
recorded complete reset rows supply reference and both learners. The explicit object name
changes result identity only. All B02/B03/r06/native paths remain unchanged.

## Acceptance before execution

One focused test `tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b05/test_seed_binding.py`
exercises initializer/reset/flow arguments, shared bytes and separate state, seed101 reset rows,
all sixteen LR records, three runner summaries and synthetic paired publication. Learner and
native episode execution are substituted only inside this test; real reset construction and LR
serialization are exercised. It cannot prove actual learning counts or outcomes. Reuse B04
accepted LR persistence, corrected boundary, count-0 reference and native termination coverage
as directed by card section 7; do not rerun the historical suite.
Independent reviewer `rev_ah_dish_b05_seed` found no material defect in the actual RNG/result
identity diff and protected downstream chain. It confirmed separate mutable states, B04 defaults,
and inherited LR/replay/termination/reduction. Initial seed-only source scope: 41 added / 18 deleted non-test lines;
runners 158 and 7 lines. The subsequent minimal shared publication wall readings implement
the card's exact S/2 allocation; independent follow-up review found no material gap. Final collection uses the exact formulas
below rather than the inherited conservative `charged_wall_seconds` field and retains stdout P. No runtime acceptance asserted. Static AST parse of all five changed/new
Python implementation/test files and `git diff --check` passed. No seed101 execution yet.

## Frozen execution and cost plan

Execution node `wsl_4070`, remote detached worktree
`/home/wu/hmasd-worktrees/dish-b05-seed101-20260906`, exact integrated/pushed SHA supplied by Root.
No Windows fallback is selected. Interpreter `/home/wu/.venvs/hmasd/bin/python`;
CPU FP32 policy/float64 native, Torch/OMP/MKL/OpenBLAS one thread, `MAX_JOBS=1`;
`PYTHONPATH` equals cwd. Output relative to cwd:
`temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906` (R below).
Each command is detached via configured `agent-task`; actual node admission (>=4 GiB physical
and effective) joins its invocation with `&&`. Outer `/usr/bin/time -v` includes imports,
build/load, operation and publication; outer timeout bounds the operation. Commands, accepted
handles and final measured S will be recorded before their launches.

Logical argv, in order (PY denotes the interpreter above):

1. `PY -m pytest -q -p no:cacheprovider --basetemp temp/directions/degraded_incumbent_shadow_handover/test/b05-seed101 tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b05` (<=300s; charged in S).
2. `PY scripts/run_dish_control_low_lr_b05.py shared --seed 101 --out R/shared --admission R/shared.memory.json`.
3. `PY scripts/run_dish_control_low_lr_b05.py run --arm CONTROL --seed 101 --shared R/shared --shared-preparation-seconds S --out R/control --admission R/control.memory.json`.
4. `PY scripts/run_dish_control_low_lr_b05.py run --arm LOW_LR --seed 101 --shared R/shared --shared-preparation-seconds S --out R/low_lr --admission R/low_lr.memory.json --control-summary R/control/summary.json`.

**Per-arm cost projection:** reuse [EXPOSURE_AND_COST.json](control_low_lr_b05_20260906/EXPOSURE_AND_COST.json),
B04 same-scale measured S=15.84s, CONTROL=210.07s, LOW_LR=206.49s, fully charged 217.99/214.41s.
No new calibration. Each arm N=65536 ordinary ticks, 512 optimizer steps; native calls
2N+2E+H <=1572864. Unknown E/H and node load remain unknown. B05 projected full pair is of
order 432.40s conditionally, below 1800s/arm and 3600s total. Actual focused check, common
initializer/reference and build/load are S/2 per arm. Shared reducer/publication executes in
LOW_LR's existing timed path. Minimal direct wall readings report its duration P in the final
stdout record, after the summary/paired files are written. Final S = focused + initializer/reference
+ P; charge CONTROL wall + S/2 and LOW_LR wall - P + S/2. Before either arm, reserve 30s for P;
outer timeout <=1800 - (measured preparation + 30)/2. The inherited runner's slightly larger
internal allowance does not supersede this outer bound. The reserve is not extra runtime and
is not charged as measured work. Final acceptance checks actual P and both exact charged totals.
No budget is deducted for unmeasured contention. Invocation wall sum, study elapsed critical
path (including control-plane gaps) and aggregate CPU are reported separately.

**Post-learner path coverage:** focused synthetic paired reduction plus publication/readback
exercises the reused primary path. No historical publication replay dependency exists.

Stop after one pair of sixteen updates and twelve reference/final rows, or nonfinite training,
primary-threatening failure or exhaustion of the fully charged caps. No scientific retry,
extra seed, checkpoint selection, extra evaluation or resume is authorized. CM retains launch
observation until independent monitor ACK and then collection/technical acceptance; DM owns science.

scope: none

## Runtime observations (collection in progress)

Root integrated and pushed exact launch SHA `1d87e02194158d6bca0eaa4e7f70a1c1098bb121`.
The detached remote checkout uses this SHA. Initial fetch through a non-login shell stalled
in git-remote-https; its exact preparation processes were terminated before checkout/compute,
then the configured `zsh -lic` network route fetched successfully. This is a Git access fact,
not an experiment failure or altered execution node. Login-shell gitstatus UI warnings did
not prevent successful fetch/checkout.

- `dish_b05_seed101_focused_20260906`: exit1 before test body; pytest temporary-directory
  parent absent. Admission passed. Outer1.15s, retained logs; no scientific model/episode.
- `dish_b05_seed101_focused2_20260906`: mkdir-parent ordinary launcher repair, fresh admission,
  one focused pass. Exit0, 1 passed in0.79s; outer1.07s. The cache_dir warning is the inherited
  pytest configuration with cacheprovider disabled. Total charged focused cost2.22s.
- `dish_b05_seed101_shared_20260906`: exit0, one initializer and four complete1200-tick rows;
  empty actor/snapshot/critic Welford. Outer7.11s; cumulative preparation9.33s.
  Master `cd461a1f466eb5cf40c42dc71d29e103a9dbf00f292d5673a8560069585e01c0`;
  reset phases2,3,0,1. Reference mean297.25 (rows96,330,323,440), retained independently
  of the still-unobserved paired learner comparison. No effect-based decision followed.
- `dish_b05_seed101_control_20260906`: accepted at same source; outer1780.335s ceiling
  =1800-(9.33+30)/2. Shared input is the new shared directory, not historical checkpoints.

All accepted handles dispatched directly to configured independent monitor. Shared-handle
adoption ACK received via Root; CM collected its terminal artifacts. CONTROL adoption ACK received from Root (tracking commit4202358fe); its terminal
notification remains pending. Routine polling released to the monitor. The final evidence will retain exact command strings, terminal supervisor evidence,
receipts, OS timing, and final stdout containing publication duration P.

### Exact accepted commands

`dish_b05_seed101_focused_20260906`:

```sh
/usr/local/bin/agent-task run dish_b05_seed101_focused_20260906 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/dish-b05-seed101-20260906 && export PYTHONPATH=/home/wu/hmasd-worktrees/dish-b05-seed101-20260906 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MAX_JOBS=1 && mkdir -p temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906 && /usr/bin/time -v -o temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused.time.txt /usr/bin/timeout --signal=ALRM 300s bash -lc '"'"'"'"'"'"'"'"'/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused.memory.json && /home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --basetemp temp/directions/degraded_incumbent_shadow_handover/test/b05-seed101 tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b05'"'"'"'"'"'"'"'"' > temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused.stdout.log 2> temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused.stderr.log'"'"''
```

`dish_b05_seed101_focused2_20260906`:

```sh
/usr/local/bin/agent-task run dish_b05_seed101_focused2_20260906 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/dish-b05-seed101-20260906 && export PYTHONPATH=/home/wu/hmasd-worktrees/dish-b05-seed101-20260906 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MAX_JOBS=1 && mkdir -p temp/directions/degraded_incumbent_shadow_handover/test && /usr/bin/time -v -o temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused2.time.txt /usr/bin/timeout --signal=ALRM 298.85s bash -lc '"'"'"'"'"'"'"'"'/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused2.memory.json && /home/wu/.venvs/hmasd/bin/python -m pytest -q -p no:cacheprovider --basetemp temp/directions/degraded_incumbent_shadow_handover/test/b05-seed101 tests/experiments/candidates/degraded_incumbent_shadow_handover/control_low_lr_b05'"'"'"'"'"'"'"'"' > temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused2.stdout.log 2> temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/focused2.stderr.log'"'"''
```

`dish_b05_seed101_shared_20260906`:

```sh
/usr/local/bin/agent-task run dish_b05_seed101_shared_20260906 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/dish-b05-seed101-20260906 && export PYTHONPATH=/home/wu/hmasd-worktrees/dish-b05-seed101-20260906 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MAX_JOBS=1 && /usr/bin/time -v -o temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/shared.time.txt /usr/bin/timeout --signal=ALRM 3567.78s bash -lc '"'"'"'"'"'"'"'"'/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/shared.memory.json && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_control_low_lr_b05.py shared --seed 101 --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/shared --admission temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/shared.memory.json'"'"'"'"'"'"'"'"' > temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/shared.stdout.log 2> temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/shared.stderr.log'"'"''
```

`dish_b05_seed101_control_20260906`:

```sh
/usr/local/bin/agent-task run dish_b05_seed101_control_20260906 'bash -lc '"'"'cd /home/wu/hmasd-worktrees/dish-b05-seed101-20260906 && export PYTHONPATH=/home/wu/hmasd-worktrees/dish-b05-seed101-20260906 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MAX_JOBS=1 && /usr/bin/time -v -o temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/control.time.txt /usr/bin/timeout --signal=ALRM 1780.335s bash -lc '"'"'"'"'"'"'"'"'/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/control.memory.json && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_control_low_lr_b05.py run --arm CONTROL --seed 101 --shared temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/shared --shared-preparation-seconds 9.33 --out temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/control --admission temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/control.memory.json'"'"'"'"'"'"'"'"' > temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/control.stdout.log 2> temp/directions/degraded_incumbent_shadow_handover/exp/control_low_lr_b05_20260906/control.stderr.log'"'"''
```

