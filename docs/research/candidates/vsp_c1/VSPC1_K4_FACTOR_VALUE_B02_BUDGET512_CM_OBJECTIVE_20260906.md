# CM objective: VSPC1-K4-FACTOR-VALUE-B02-BUDGET512 (2026-09-06)

Card: `VSPC1_K4_FACTOR_VALUE_B02_BUDGET512_SCIENCE_CARD_20260906.md` (frozen; read it fully).
Implementation route: Grok Build headless under `.claude/skills/hmasd-grok-cm/SKILL.md`; the
hub reviews, tests, commits by pathspec and dispatches the operator. The implementer makes no
scientific choice: every number below comes from the card.

## Objective

Add a measurement entry that trains one FACTOR arm and one GENERIC arm at seed 3 for 512
continuous updates on the unchanged K4 host and publishes the 33-point curve, the three AUC
windows, the parameter readouts, exposure counts and resource fields, without changing the
accepted 128-update B01 path or its results.

## Owned paths (create or edit only these)

- `experiments/candidates/vsp_c1/k4_factor_value_b01/budget512.py` (new): the B02 loop.
- `experiments/candidates/vsp_c1/k4_factor_value_b01/reporting.py`: add
  `budget512_metrics(curve)` beside the existing `curve_metrics` (which stays byte-identical in
  behaviour, divisor 8, nine points).
- `scripts/run_vspc1_k4_factor_value_b02_budget512.py` (new): thin runner, same shape as
  `scripts/run_vspc1_k4_factor_value_b01.py` (launch facts, resources block with
  `resources_unmeasured` on Windows, `write_read` of `summary.json`, exit 0 only on
  `status == "complete"`).
- `tests/experiments/candidates/vsp_c1/k4_factor_value_b01/test_budget512.py` (new).

Do not edit `experiment.py` (its `Value`, `state_at`, `rollout`, `evaluate`, `action_rows`,
`CONTEXTS`, `STREAM_TAGS` are imported and reused), the B01 runner, existing tests, any card
or result, or anything outside the paths above.

## Frozen behaviour of `budget512.run(arm, seed, out, launch)`

- `summary["object"] = "VSPC1-K4-FACTOR-VALUE-B02-BUDGET512"`; `seed` must be 3 (runner
  `--seed` choices `(3,)`); `torch.set_num_threads(1)`, interop 1; CPU FP32; same
  `Value(arm, seed)` construction, same stream construction (`SeedSequence([seed, tag])`,
  torch `seed*1000 + tag`), same Adam settings, same batch construction and permutation, same
  fixed `draws = exploration_rng.random((32, 6, 2))` per cycle, same target/loss/clip/update
  code as `experiment.run` (copy it; do not refactor `experiment.py`).
- Loop `for update in range(513)`: evaluate at every `update in range(0, 513, 16)` (33
  states) with the existing `evaluate(...)`, snapshot after each; break at `update == 512`.
- Exploration per cycle with zero-based `update`: `epsilon = 1 - 0.9 * update / 127` for
  `update < 128`, else `0.1`. (Cycle j = update + 1; j = 128 gives 0.1 exactly by the formula;
  j ≥ 129 uses the constant.) Nothing is reset at 128.
- Parameter readouts: `theta0_norm`; at `update == 128` (before that cycle's rollout, i.e.
  right after the checkpoint-128 evaluation) record `theta128_norm`,
  `theta0_to_128_displacement_norm`; at the end record `theta512_norm`,
  `theta0_to_512_displacement_norm`, `theta128_to_512_displacement_norm`,
  `displacement_to_initial_norm` (0→512 over ‖θ0‖). Keep a detached copy of θ128 in memory
  only; no checkpoint files.
- `metrics = budget512_metrics(curve)` returning: `initial_return`, `return_128`,
  `return_512`, `learning_gain_0_512`, `learning_gain_128_512`, `auc_0_128` (divisor 8 over
  the first nine points), `auc_0_512` (divisor 32 over all 33), `auc_128_512` (divisor 24
  over points 8…32). Trapezoid weights 0.5 at both ends of each window.
- Expected counts (defects appended exactly as in B01 when they differ): training
  `{"episodes": 16384, "joint_steps": 98304, "renewals": 32768, "legal_decisions": 32768,
  "renewals_p2": 24576, "renewals_p6": 8192}`, `optimizer_steps == 512`; evaluation
  `Counter(episodes=264, joint_steps=1584, renewals=528, legal_decisions=528,
  renewals_p2=396, renewals_p6=132)`; parameter count 188/191.
- `cost_law` with the 512-update work string and per-cycle/per-step/per-checkpoint measured
  seconds (divisors 512, `optimizer_steps`, 33).
- Everything else (checks counters, snapshot content, `status` semantics, exception path)
  as in `experiment.run`.

## Tests (`test_budget512.py`, no full training run)

1. Epsilon schedule: the function that maps `update` to ε returns the B01 values for
   `update` 0…127 (`1 - 0.9*update/127`) and 0.1 for 128…511; ε at update 127 equals 0.1.
2. `budget512_metrics` on a synthetic 33-point curve: the three windows and gains equal
   hand-computed values; `auc_0_128` equals `curve_metrics(curve[:9])["normalized_auc"]`.
3. Card arithmetic without a model: expected training/evaluation counts derived from 512
   cycles × 32 episodes and 33 × 8 evaluation episodes equal the frozen dictionaries.
4. Source parses and imports without executing the scientific path; the runner refuses seeds
   other than 3 (argparse `SystemExit`).
5. A two-cycle, two-checkpoint dry run is NOT required and must not be added as a smoke.

Run: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q
tests/experiments/candidates/vsp_c1/k4_factor_value_b01/` (existing four tests must still pass).

## Acceptance (hub)

Diff limited to the owned paths; `experiment.py` untouched (byte-identical); B01 tests pass;
new tests pass; line budget well under 600 for the runner and 2,000 total; no new
engineering-scope §4 item. Then the hub writes the CM record with the frozen remote commands
(`agent-task` on `wsl_4070`, worktree at the pushed sha, `admit-memory && python
scripts/run_vspc1_k4_factor_value_b02_budget512.py --arm FACTOR --seed 3 --out <root>/factor_s3`
then the GENERIC invocation, each under an external 2,700 s timeout) and dispatches the
operator.
