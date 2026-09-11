# VSP-C1 K4 B02 budget512 CM record (2026-09-06)

Implementation exists in this worktree. No result-bearing invocation was launched. No git
command was run. Hub reviews, pathspec-commits, pushes, and dispatches the operator.

## Prospective contract (restated from the frozen card and objective)

Observable: one FACTOR and one GENERIC arm, each a fresh seed-3 instance, train 512 continuous
updates on the unchanged K4 host and publish the 33-point curve (u = 0, 16, …, 512), three AUC
windows, parameter readouts, exposure counts and resource fields.

Acceptance: owned-path diff only; `experiment.py` byte-identical; B01 tests pass; new focused
tests pass; runner < 600 lines; attempt < 2,000 non-test lines; no engineering-scope §4 item;
then two complete remote arm invocations at seed 3.

Non-goals: any edit to the accepted 128-update B01 path or its seed-0/1/2 results; checkpoint
files; a two-cycle dry-run smoke; a local seed-3 training run; scientific interpretation.

Baseline / configuration / data / RNG: CPU FP32, one compute thread, in-process batch 32,
`Value(arm, seed)` and named streams as B01 (`SeedSequence([seed, tag])`, torch
`seed*1000 + tag`) at seed 3; Adam (0.9, 0.999), lr 0.01, ε 1e-8, weight decay 0, clip 5;
fixed `(32, 6, 2)` exploration draws per cycle; no loaded model. Exploration: `1 - 0.9 * update / 127`
for `update < 128` (B01 formula; at update 127 this is IEEE `1 - 0.9`), else `0.1`. Nothing
resets at 128. Evaluation greedy, deterministic, no training-stream consumption.

Protected semantics: host, pairing, support, event clocks, dtype, RNG stream assignment,
update/target/loss/clip, B01 `curve_metrics` divisor 8, B01 runner and tests. `write_read`
unchanged. In-memory θ128 copy only.

Owned paths: `budget512.py` (new), `reporting.py` (`budget512_metrics` only),
`scripts/run_vspc1_k4_factor_value_b02_budget512.py` (new), `test_budget512.py` (new), this
record. Resource bound: 2,700 s wall per complete arm invocation; physical/effective ≥ 4 GiB
admission on the executing node immediately before each runner. Output: each arm's `--out`
root `summary.json` via `write_read`. Node: remote-first `wsl_4070`, detached worktree at the
pushed sha. Stop: cap or actual technical failure; keep completed exposure; never skip
evaluation or publication; never switch seed or budget.

Engineering-scope §4 items added: **none**. `scope: none`.

## Implementation

`budget512.run` copies the B01 loop body. It imports `Value`, `state_at` consumers
(`rollout`, `evaluate`, `action_rows`), `CONTEXTS` and `STREAM_TAGS` from `experiment.py` and
does not refactor that module. Loop `for update in range(513)`: evaluate at
`range(0, 513, 16)` (33 states), snapshot after each; record detached θ128 after the
checkpoint-128 evaluation and before that cycle's rollout; break at `update == 512`. Metrics
from `budget512_metrics`: `initial_return`, `return_128`, `return_512`, `learning_gain_0_512`,
`learning_gain_128_512`, `auc_0_128` (divisor 8, first nine points), `auc_0_512` (divisor 32,
all 33), `auc_128_512` (divisor 24, points 8…32). Expected training
`{episodes: 16384, joint_steps: 98304, renewals: 32768, legal_decisions: 32768, renewals_p2: 24576, renewals_p6: 8192}`,
`optimizer_steps == 512`; evaluation
`Counter(episodes=264, joint_steps=1584, renewals=528, legal_decisions=528, renewals_p2=396, renewals_p6=132)`;
parameters 188/191. `cost_law` work string is the 512-update counts; measured seconds use
divisors 512, `optimizer_steps`, 33.

Runner shape matches B01: BLAS threads set before NumPy/Torch import; `--seed` choices `(3,)`;
launch facts; Windows `resources_unmeasured`; `write_read` of `summary.json`; exit 0 only on
`status == "complete"`.

## Tests (directly observed)

Command:

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/vsp_c1/test/b02-budget512-grok tests/experiments/candidates/vsp_c1/k4_factor_value_b01/
```

Result (verbatim summary): `9 passed, 1 warning in 1.72s` (exit 0). Four existing B01 tests
and five new B02 tests. The warning is the pre-existing pytest `cache_dir` config option under
`-p no:cacheprovider`; not introduced by this change.

What the tests establish: ε schedule vs the B01 formula on 0…127 and constant 0.1 on 128…511;
three AUC windows and gains on a synthetic 33-point curve, with `auc_0_128` equal to
`curve_metrics(curve[:9])["normalized_auc"]`; frozen count dictionaries from 512×32 and 33×8
arithmetic; source parse plus import without calling `run`; runner argparse `SystemExit` for
seeds 0, 1, 2 and 4. What they cannot: a 512-update training trajectory, remote wall/RSS, or
seed-3 numerical values.

## Per-arm cost law (conditional linear scenario; not a measurement)

Runner cost law after a complete invocation (result-blind):

- work: `init + rollout(98304 joint ticks,32768 renewals) + 512 updates(64 rows) + eval(1584 joint ticks) + checks/publication`
- `measured_rollout_seconds_per_cycle` = rollout wall / 512
- `measured_update_seconds_per_step` = update wall / `optimizer_steps`
- `measured_evaluation_seconds_per_checkpoint` = evaluation wall / 33

Planning projection uses only accepted B01 measured phase times and complete external walls
from `VSPC1_K4_FACTOR_VALUE_B01_CM_TECHNICAL_RECORD_20260905.md` and the archived B01
`summary.json` cost_law fields. It is labelled a **conditional linear scenario**: same
batch32/H6/CPU-FP32/one-thread path, 4× the 128-update work in the training loop, 33/9
evaluation checkpoints, unmeasured init/import/I/O/start/exit/contention/node state.

B01 seed-0 complete external invocation walls: FACTOR 1.76 s, GENERIC 3.95 s. Card §4
4× linear of those walls: **7.04 s FACTOR, 15.8 s GENERIC** per arm. Across all six B01
complete walls (1.76, 2.76, 2.77, 2.86, 2.90, 3.95; sum 17.00 s) the same 4× scenario is
7.04–15.8 s.

B01 `cost_law` unit times, phase-linear with init unscaled:
`init + 512 × (rollout_per_cycle + update_per_step) + 33 × eval_per_checkpoint`:

| B01 source | init s | rollout/cycle s | update/step s | eval/checkpoint s | phase-linear s | 4× complete wall s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| FACTOR seed 0 | 0.502342 | 0.000899838 | 0.001145068 | 0.001204288 | 1.589 | 7.04 |
| GENERIC seed 0 | 0.542603 | 0.000946730 | 0.014140148 | 0.000943265 | 8.298 | 15.8 |
| FACTOR seed 1 | 0.787141 | 0.001448007 | 0.001580509 | 0.001540894 | 2.389 | 11.08 |
| GENERIC seed 1 | 0.776462 | 0.001375214 | 0.001584128 | 0.001484529 | 2.341 | 11.04 |
| FACTOR seed 2 | 0.817603 | 0.001400648 | 0.001644005 | 0.001945818 | 2.441 | 11.60 |
| GENERIC seed 2 | 0.799039 | 0.001477171 | 0.001675194 | 0.001445948 | 2.461 | 11.44 |

GENERIC seed 0 update unit time is an outlier relative to the other five B01 invocations;
it is retained as the upper reference of the card's 7.04–15.8 s scenario. Phase-linear
figures omit import/git/publication overhead present in complete walls. Neither column is
a bound.

Against the **2,700 s per-arm cap**: 15.8 s is 0.6% of the cap. No arm is over-cap under
this scenario. Cap sum 5,400 s is not an estimate. Actual B02 walls remain unmeasured until
the operator invocations complete.

## Frozen remote commands (`wsl_4070`)

Placeholders: `WT` = detached worktree at the pushed `LAUNCH_SHA` under
`/home/wu/hmasd-worktrees`. Interpreter `/home/wu/.venvs/hmasd/bin/python`. Supervisor
`/usr/local/bin/agent-task`. Serial order: FACTOR seed 3, then GENERIC seed 3. Fresh
actual-node `admit-memory` immediately before each runner, joined with `&&`. External
2,700 s timeout covers import, init, training, 33 evaluations, checks, publication
readback and exit. Required publication stays inside the timeout. No automatic
continuation.

Logical command (FACTOR, then the same with `GENERIC` and its root):

```bash
cd <WT> && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out <WT>/temp/directions/vsp_c1/exp/k4_b02_factor_seed3_<LAUNCH_SHA>_01/admission.json && /usr/bin/time -v -o <WT>/temp/directions/vsp_c1/exp/k4_b02_factor_seed3_<LAUNCH_SHA>_01/invocation.time timeout --signal=TERM 2700s /home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_k4_factor_value_b02_budget512.py --arm FACTOR --seed 3 --out <WT>/temp/directions/vsp_c1/exp/k4_b02_factor_seed3_<LAUNCH_SHA>_01
```

```bash
cd <WT> && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out <WT>/temp/directions/vsp_c1/exp/k4_b02_generic_seed3_<LAUNCH_SHA>_01/admission.json && /usr/bin/time -v -o <WT>/temp/directions/vsp_c1/exp/k4_b02_generic_seed3_<LAUNCH_SHA>_01/invocation.time timeout --signal=TERM 2700s /home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_k4_factor_value_b02_budget512.py --arm GENERIC --seed 3 --out <WT>/temp/directions/vsp_c1/exp/k4_b02_generic_seed3_<LAUNCH_SHA>_01
```

Supervisor wrappers (existing `agent-task`; task names follow the B01 pattern):

```bash
/usr/local/bin/agent-task run vspc1_b02_factor_s3_<LAUNCH_SHA>_01 'cd <WT> && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out <WT>/temp/directions/vsp_c1/exp/k4_b02_factor_seed3_<LAUNCH_SHA>_01/admission.json && /usr/bin/time -v -o <WT>/temp/directions/vsp_c1/exp/k4_b02_factor_seed3_<LAUNCH_SHA>_01/invocation.time timeout --signal=TERM 2700s /home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_k4_factor_value_b02_budget512.py --arm FACTOR --seed 3 --out <WT>/temp/directions/vsp_c1/exp/k4_b02_factor_seed3_<LAUNCH_SHA>_01'
```

```bash
/usr/local/bin/agent-task run vspc1_b02_generic_s3_<LAUNCH_SHA>_01 'cd <WT> && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out <WT>/temp/directions/vsp_c1/exp/k4_b02_generic_seed3_<LAUNCH_SHA>_01/admission.json && /usr/bin/time -v -o <WT>/temp/directions/vsp_c1/exp/k4_b02_generic_seed3_<LAUNCH_SHA>_01/invocation.time timeout --signal=TERM 2700s /home/wu/.venvs/hmasd/bin/python scripts/run_vspc1_k4_factor_value_b02_budget512.py --arm GENERIC --seed 3 --out <WT>/temp/directions/vsp_c1/exp/k4_b02_generic_seed3_<LAUNCH_SHA>_01'
```

Post-learner path: primary JSON write/read is inside each invocation (`write_read` of
`summary.json`, reused unchanged). No alternative publication path is selected.

## Files and line counts (this worktree)

| Path | Role | Lines |
| --- | --- | ---: |
| `experiments/candidates/vsp_c1/k4_factor_value_b01/budget512.py` | new loop | 127 |
| `experiments/candidates/vsp_c1/k4_factor_value_b01/reporting.py` | add `budget512_metrics` only | 42 (was 25) |
| `scripts/run_vspc1_k4_factor_value_b02_budget512.py` | new runner | 66 |
| `tests/experiments/candidates/vsp_c1/k4_factor_value_b01/test_budget512.py` | new tests | 92 |
| this record | CM record | (documentation) |

Non-test addition ≈ 127 + 17 + 66 = 210 lines. Runner 66. Both under budget.
`experiment.py`: 248 lines, SHA-256
`7e3092e40cbbf639b057b0a5135acb04a7cde25111092fce34ab3bf97d296358`. This session did not
write that file.

## Limitations and remaining technical risk

- No 512-update training was executed. Seed-3 numbers, actual walls, RSS and cost_law unit
  times are unknown.
- First-128 identity with B01 is by copied source and the same ε formula, not by a seed-3
  B01 comparator (seed 3 was never a B01 seed).
- IEEE: `epsilon_at(127)` is `1 - 0.9` (B01), not the binary literal `0.1`. Cycles 129…512
  use the constant `0.1`.
- Remote `wsl_4070` admission, checkout and supervisor behaviour were not exercised here.
- Independent reviewer is not requested for a shared-core/RNG/checkpoint surface: the loop
  is direction-local and copied. Hub intake review of the Grok diff remains required. No
  verifier is needed for the focused tests; runtime facts wait on the operator.

Passing checks establish conformance of the added entry, not scientific truth.
