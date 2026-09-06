# DISH-RENEWAL-BOUNDARY-A02-CORRECTION CM record (2026-09-06)

Worktree `C:/Projects/HMASD/.claude/worktrees/grok-dish-a02`, branch
`grok/dish-a02-correction-20260906`, starting HEAD `1952f7b35` of `main`.
Grok Build implemented the ordinary-renew overlay and A02 measurement entry;
Git commit/push is the hub's pathspec step (this session ran no git commands
that change state). Scope §4: none.

## What changed (A/D)

| Path | A | D | Role |
| --- | ---: | ---: | --- |
| `experiments/candidates/degraded_incumbent_shadow_handover_rbhr_r06/production_backend.py` | 20 | 37 | ordinary `NativeBatch` observation overlay |
| `experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/renewal_boundary_a02.py` | 209 | 0 | windowed driver, row recorder, reduction |
| `scripts/run_dish_renewal_boundary_a02.py` | 134 | 0 | argparse entry, wall and peak RSS, JSON publication |
| `tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/test_renewal_boundary_a02.py` | 247 | 0 | unit checks (no native library) |
| this record | (docs) | 0 | |

Non-test source A=363, D=37, runner 134. `production_recurrent_trainer.py` was
not edited: `step_rows` still reads `observation["renew"]` at line 311; fragment
fields `renew` / `prepare_mask` / `commit_mask` still copy that key at lines
506–508.

## Independent review rework (2026-09-06)

Opus reviewer accepted the wrapper (`production_backend.py`) and returned four
findings. This pass does not edit `production_backend.py`. Scope §4: none.

| Path | lines now | this-pass A | this-pass D | Role |
| --- | ---: | ---: | ---: | --- |
| `forecast_package_b02/renewal_boundary_a02.py` | 227 | 18 | 0 | native-out counters; A01 hard-event fields |
| `scripts/run_dish_renewal_boundary_a02.py` | 170 | 36 | 0 | primary acceptance line in summary/stdout/log |
| `test_renewal_boundary_a02.py` | 303 | 68 | 12 | trainer `_fragments` call; mismatch row; schema |
| this record | 279 | 100 | 0 | findings 1–4, consumer map, check counters |

### Finding 1 (fixed)

`native_admission` and `policy_renew` both test the same pre-step `countdown == 0`,
so the countdown disagreement counters were structurally zero. `reduce_rows` now
also compares `row["renew_completed"]` (native `out.renew` for the completed
step) with `row["policy_renew"]` and publishes:

- `native_out_renew_equals_policy_renew`
- `native_out_true_policy_false`
- `policy_true_native_out_false`

The runner's acceptance line uses that native-out comparison as the primary
agreement measure. Countdown-based `matched_renewals` /
`native_true_policy_false` / `policy_true_native_false` remain as a secondary
consistency check, labelled as such in `summary.json`.
`test_reduce_rows_four_tick_handwritten_counts` now includes handwritten rows
where `renew_completed` and `policy_renew` differ and asserts both mismatch
counters increment.

### Finding 2 (recorded only; no code change)

`rollout()` consumer not named in the first consumer map.

- `production_preactivity.py:108,132-134` builds `renew` / `prepare_mask` /
  `commit_mask` fragments from `batch.rollout(rows)["renew"]` and pairs index
  `t` with `rows[t]`. With the overlay, those fixture fragments move: reviewer
  measured 2048 of 4096 entries change on `TestProtocolNativeBatch(32)` with
  `_rollout_rows(32,128)`; total true count unchanged at 1024. That changes
  fixture PPO losses and `native_fragment_binding.sha256` published by
  `production_p1.py:41,50` and the E2B acceptance runner. Bound: test-only
  fixture. No test asserts those constants. No B01, B02 or A02 science path
  is affected.
- `tools/experiments/run_dish_rbhr_r06_e2b_acceptance.py:66-70,92` records
  `source_sha256` of `production_backend.py`, so the archived r06 E2B
  technical acceptance no longer describes current bytes (bookkeeping for
  the hub).

### Finding 3 (fixed)

Card §3 per-tick events were dropped. `make_row` now records `hard_events` and
`hard_event_increments` exactly as A01 (`a01.HARD_EVENTS`). Both keys are in
`ROW_KEYS` and the row-schema assertions.

### Finding 4 (fixed)

`test_collector_fragment_fields_follow_corrected_renew` no longer builds
fragments locally. It calls `NativePersistentTrainingFlow._fragments` (the
function that contains lines 506–508) with a two-tick corrected flag sequence
padded to the trainer's 128×32 schema, then asserts `renew` /
`prepare_mask` / `commit_mask` equal that sequence. The `step_rows` gating
half of the test is unchanged.

### Consumer map (`observation["renew"]` under dish trees)

| Site | Role | Bound |
| --- | --- | --- |
| `production_recurrent_trainer.py:311` `step_rows` | card-named ordinary consumer | science path; code unchanged |
| `production_recurrent_trainer.py:506-508` `_fragments` | card-named collector fields | science path; code unchanged |
| `production_preactivity.py:108,132-134` via `NativeBatch.rollout` | test-only fixture fragments | fixture PPO / `native_fragment_binding.sha256`; 2048/4096 entries move, total 1024 unchanged |
| `production_p1.py:41,50` | publishes that fixture binding | test-only |
| `run_dish_rbhr_r06_e2b_acceptance.py:66-70,92` | `source_sha256` of wrapper | archived E2B acceptance no longer describes current bytes |
| `renewal_boundary_a01.py` / `renewal_boundary_a02.py` | measurement of the consumed flag | A01/A02 observation |
| `production_training_engine.py` `data["renew"]` | fragment tensor, not wrapper observation | downstream of `_fragments` |

`B01PreparedBatch.observe` / `_decode_step_outputs` / clone paths still use
raw `out.renew` (reviewer-accepted).

### Exact lines in `production_backend.py`

- Added `_ordinary_decision_observation` at lines 312–320. It copies the decoder
  `renew` to `renew_completed` and sets `renew` to `[countdown == 0]`.
- `NativeBatch.observe` (559–565): decode `_outputs`, read per-lane
  `_states.countdown` (no native call, no advance), overlay.
- `NativeBatch.reset_selected` still returns `self.observe()` (586).
- `NativeBatch.step` (716–725): after `step_batch`, `return self.observe()`
  instead of copying `_outputs` (the previous 33-line dict).
- `NativeBatch.rollout` (741–776): same output dict as before, then overlay
  from actor feature 42 because `_states` holds only the post-rollout lane.
  `_decode_step_outputs`, `complete_b01_tick`, ctypes structures, native
  source, and `B01PreparedBatch.observe` (526–531, still `_decode_step_outputs`)
  were not edited.

The other class whose `observe` sat near line 515 is `B01PreparedBatch`
(now 526). It is not the ordinary class.

Inherited side effect: `complete_b01_tick` (643) returns `self.observe()`
and therefore receives the overlay. B01 policy decisions consume
`B01PreparedBatch.observe()` / `_decode_step_outputs` (unchanged). Clone
observations at `clone_b01_prepared_batches` line 694 still use
`_decode_step_outputs`.

## Reviewer questions

1. Is the ordinary `NativeBatch` the only class changed? (`B01PreparedBatch.observe`
   still decodes raw `renew`.)
2. Does `reset_selected` for a phase-zero lane expose `renew = 1`? (Stubbed
   native reset writes `countdown = phase` and leaves `out.renew = 0`; observe
   overlay reports 1. Native `reset_one` matches that: `s.countdown = x.phase`,
   `out.renew` stays 0.)
3. Does any other consumer of `observation["renew"]` under
   `experiments/candidates/degraded_incumbent_shadow_handover*/` now change
   meaning unintentionally? See the consumer map in this record (Finding 2
   adds the `rollout()` fixture path).
4. Is the inherited `complete_b01_tick` → `observe()` overlay acceptable, or
   must post-B01-complete `renew` stay the completed-transition flag?
5. For `rollout`, is actor feature 42 the correct per-tick current countdown
   (native writes it after the countdown update, cpp:494–495)?

## Checkpoint digest

Local file `C:/Projects/HMASD/temp/b02_transport/forecast_package/checkpoint_update16.pt`
(2,368,467 bytes). sha256
`504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66`, equal to the
card digest. Runner refuses a mismatch.

## Focused tests

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/test/renewal-boundary-a02-grok2 tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/test_renewal_boundary_a02.py tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/test_renewal_boundary_a01.py
```

After the review rework: `11 passed, 1 warning in 1.96s` (6 A02 + 5 A01).
`test_package.py` cannot collect on Windows (`ModuleNotFoundError: No module
named 'resource'` from `scripts/run_dish_forecast_package_b02.py:4`); not
stubbed.

A02 names (unchanged functions; two bodies extended):
`test_ordinary_observe_reports_current_countdown_permission`,
`test_reset_phase_zero_exposes_renew_one_phase_four_exposes_zero`,
`test_repeated_observe_does_not_advance_tick_or_countdown`,
`test_collector_fragment_fields_follow_corrected_renew` (now calls
`NativePersistentTrainingFlow._fragments`),
`test_reduce_rows_four_tick_handwritten_counts` (native-out mismatch row;
`hard_events` / `hard_event_increments` in schema),
`test_source_parses`. One `BatchedRecurrentPolicy` (`checkpoint_bytes=None`)
construction, 0 backward. They do not load the native library or run the
real windows.

## Check profile (local, not result-bearing)

Native A03 library already present; not a cold `cl.exe`.

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_dish_renewal_boundary_a02.py --checkpoint C:/Projects/HMASD/temp/b02_transport/forecast_package/checkpoint_update16.pt --checkpoint-sha256 504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66 --out C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/exp/renewal-boundary-a02-check-grok --launch-sha 1952f7b35bce656b778b00db2c466ec3574b46e8 --profile check
```

First implementation check (pre-review): wall `0.08637129998533055`,
peak RSS `195788800`.

Rework check (same checkpoint, new out
`.../exp/renewal-boundary-a02-check-grok2`):

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_dish_renewal_boundary_a02.py --checkpoint C:/Projects/HMASD/temp/b02_transport/forecast_package/checkpoint_update16.pt --checkpoint-sha256 504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66 --out C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/exp/renewal-boundary-a02-check-grok2 --launch-sha 1952f7b35bce656b778b00db2c466ec3574b46e8 --profile check
```

Stdout: `status COMPLETE`, `live_tick_count 4`,
`wall_seconds 0.10556320002069697`, `peak_rss_bytes 196190208`.
Window 1 reset phase 4. B02 master
`ef9ec35ce27cf52e4c1d82292b22cfbe4926183ec1f29b19657280f6234814b1`. Parameter
norm before=after `39.149200792042365`. Countdown 4→3→2→1 across t=0..3;
`policy_renew` false, `native_admission` false, `renew_completed` false on all
four ticks; `hard_events` / `hard_event_increments` all zero; first K8
opportunity is t=4.

Primary (native `out.renew` vs `policy_renew`):
`native_out_renew_equals_policy_renew` 4,
`native_out_true_policy_false` 0, `policy_true_native_out_false` 0.

Secondary countdown consistency: `matched_renewals` 0,
`matched_non_renewals` 4, `native_true_policy_false` 0,
`policy_true_native_false` 0. Admissions 0, `held_changed_ticks` 0.
Formal was not run.

## Frozen commands (hub fills LAUNCH_SHA and worktree after pathspec commit)

Node `wsl_4070`, python `/home/wu/.venvs/hmasd/bin/python`, supervisor
`/usr/local/bin/agent-task`. Checkpoint on that node (B02 CM record):
`/home/wu/hmasd-worktrees/n3-b02-20260905/temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b02_20260905/forecast_package/checkpoint_update16.pt`.
If that worktree is gone, stage the same digest under
`/home/wu/hmasd-inputs/forecast_package_b02/checkpoint_update16.pt`. Cap 120 s
wall for the whole object including native build, both profiles, reduction
and publication. Preflight on the executing node, joined by `&&`. External
`timeout` 120 s.

Check (`WT` = remote worktree at LAUNCH_SHA):

```
/usr/local/bin/agent-task run dish_a02_check_20260906 'bash -lc '"'"'cd WT && export PYTHONPATH=WT OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/renewal_boundary_a02_check.memory.json && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_renewal_boundary_a02.py --checkpoint /home/wu/hmasd-worktrees/n3-b02-20260905/temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b02_20260905/forecast_package/checkpoint_update16.pt --checkpoint-sha256 504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66 --out temp/directions/degraded_incumbent_shadow_handover/exp/renewal_boundary_a02_check --launch-sha LAUNCH_SHA --profile check'"'"''
```

Formal (same node, not launched here):

```
/usr/local/bin/agent-task run dish_a02_formal_20260906 'bash -lc '"'"'cd WT && export PYTHONPATH=WT OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/renewal_boundary_a02_formal.memory.json && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_renewal_boundary_a02.py --checkpoint /home/wu/hmasd-worktrees/n3-b02-20260905/temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b02_20260905/forecast_package/checkpoint_update16.pt --checkpoint-sha256 504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66 --out temp/directions/degraded_incumbent_shadow_handover/exp/renewal_boundary_a02_formal --launch-sha LAUNCH_SHA --profile formal'"'"''
```

Local fallback (Windows, A03 native builds under MSVC; only if remote refuses
and no remote process was accepted). Interpreter
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`. Check:

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/hmasd_resource_preflight.py admit-memory --out C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/exp/renewal_boundary_a02_check.memory.json && C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_dish_renewal_boundary_a02.py --checkpoint C:/Projects/HMASD/temp/b02_transport/forecast_package/checkpoint_update16.pt --checkpoint-sha256 504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66 --out C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/exp/renewal_boundary_a02_check --launch-sha LAUNCH_SHA --profile check
```

Formal local fallback replaces `--profile check` / `_check` paths with
`formal`. Do not treat the already-run Grok check directory as the frozen
formal output.

## Cost projection against 120 s

Law: `build/import/load + one focused regression + checkpoint + 2 x (policy + reset) + <= 64 x (forward + native step) + publication`
with W=4 (check) or 64 (formal), C=1 or 2. Cap 120 s for the whole object.

Reused A01/B02 measured terms: focused profile+admission 6.83 s (compile mixed
with five tests; compile not isolated); A01 local check 5.161 s cold / 0.065 s
warm; A01 formal warm 0.090 s; FORECAST_PACKAGE complete arm 298.60 s for
65536 training transitions plus 4800 evaluation ticks.

This session: A02+A01 unit tests 1.71 s then 1.96 s after the review rework;
`test_package.py` not collected on Windows (`resource` missing; not stubbed);
local check 0.086 s then 0.106 s (library already present, 4 ticks).

Pessimistic eval attribution: 64/4800 × 298.60 s = 3.981 s for 64 ordinary
steps if the entire package arm wall were eval.

Conservative composition without double-counting: 6.83 s compile upper +
12.07 s focused tests + 0.086 s measured check + 60 remaining ticks ×
298.60/4800 = 3.73 s + one extra policy construction bounded by another ~5 s
load ≈ 28 s, below 120 s. No arm is over cap. Formal was not launched.

## Post-learner path

Not applicable: zero training, zero optimizer, no learner publication path.

## Stop conditions and residual engineering notes

No stop. Per-lane current countdown is already on `NativeBatch._states`
(`_State.countdown`); no native export was added. Checkpoint digest matched.
`production_recurrent_trainer.py` and `production_backend.py` unchanged in
this rework. Projection is under 120 s. The 4-tick check has no admission
ticks by construction (first K8 opportunity is t=4), so it cannot yet show
incorporation; it does show primary native-out agreement 4/4 and countdown
4→1 with `policy_renew` false. Finding 2 is recorded only: the `rollout()`
fixture consumer and the archived E2B `source_sha256` bookkeeping.
