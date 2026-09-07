# DISH B05 seed101 technical record

Implementation base: `18812ba5e62b6e1a877558f735c7bf979386be5b`.
CM branch `codex/cm-dish-b05-seed101-20260906`, worktree
`C:/Projects/HMASD-worktrees/cm-dish-b05-seed101-20260906`.
Contract: [card](DISH_CONTROL_LOW_LR_B05_SCIENCE_CARD_20260906.md) section section 2-4,6-7.

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
