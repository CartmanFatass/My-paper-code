# DISH-RENEWAL-BOUNDARY-A01 CM record (2026-09-05)

Worktree `C:/Projects/HMASD/.claude/worktrees/grok-dish-a01`, branch
`grok/dish-renewal-boundary-a01-20260905`, starting HEAD `f06b1b42a` of `main`.
Grok Build implemented the measurement entry; Git commit/push is the hub's
pathspec step (this session ran no git commands). Scope §4: none.

## What was added (A/D)

| Path | A | D | Role |
| --- | ---: | ---: | --- |
| `experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/renewal_boundary_a01.py` | 281 | 0 | windowed driver, row recorder, reduction |
| `scripts/run_dish_renewal_boundary_a01.py` | 134 | 0 | argparse entry, wall and peak RSS, JSON publication |
| `tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/test_renewal_boundary_a01.py` | 185 | 0 | unit checks (no native library) |
| this record | (docs) | 0 | |

Non-test source A=415, D=0, runner 134. No R06, `study.py`, or B01 helper was edited.
Call order per tick is `step_rows(..., sampler=None, deterministic=True)` then
`native.step` then `apply_native_promotion`, with one `observe()` at window start.
Native command projection is reconstructed in Python from
`rbhr_r06_production_backend.cpp:261-263` for reporting only.

## Checkpoint digest

Local file `C:/Projects/HMASD/temp/b02_transport/forecast_package/checkpoint_update16.pt`
(2,368,467 bytes). sha256
`504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66`, equal to the
card digest and `b02_20260905/forecast_package.checkpoint.sha256`. Runner refuses
a mismatch.

## Focused tests

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q tests/experiments/candidates/degraded_incumbent_shadow_handover/forecast_package_b02/test_renewal_boundary_a01.py -p no:cacheprovider --basetemp C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/test/renewal-boundary-a01-grok
```

Result: `5 passed, 1 warning in 1.80s` (repeat with `DISH_A01_CHECK_ROOT` set:
`5 passed, 1 warning in 1.63s`). The warning is pytest `cache_dir` under
`-p no:cacheprovider`. Tests cover admission predicate, row schema including
tick 0, reduction arithmetic, stub call-order (`sampler=None`,
`deterministic=True`, one `observe()` per window), and optional check-root
readback. They do not load the native library or the retained checkpoint.

## Check profile (local, not result-bearing)

Ran once after the native A03 extension built under MSVC through
`production_backend.py` (library already present; not a cold `cl.exe`).

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_dish_renewal_boundary_a01.py --checkpoint C:/Projects/HMASD/temp/b02_transport/forecast_package/checkpoint_update16.pt --checkpoint-sha256 504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66 --out C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/exp/renewal-boundary-a01-check-grok --launch-sha f06b1b42a --profile check
```

Stdout: `status COMPLETE`, `live_tick_count 4`, `wall_seconds 5.16114760003984`.
Window 1 reset phase 4 (matches card). B02 master
`ef9ec35ce27cf52e4c1d82292b22cfbe4926183ec1f29b19657280f6234814b1`. Parameter
norm before=after `39.149200792042365`. Countdown 4→3→2→1→0 across t=0..3;
no native admission in these four ticks (first K8 opportunity is t=4).
Decisive counts: native_true_policy_false 0, policy_true_native_false 0,
both_true 0, both_false 4, held_changed_ticks 0. Peak RSS on that run was
`resources_unmeasured` (untyped `GetProcessMemoryInfo` handle). The runner
now types the Win32 call; that helper was not re-run through the check
profile. Formal was not run.

## Frozen commands (hub fills LAUNCH_SHA and worktree after pathspec commit)

Node `wsl_4070`, python `/home/wu/.venvs/hmasd/bin/python`, supervisor
`/usr/local/bin/agent-task`. Checkpoint on that node (B02 CM record):
`/home/wu/hmasd-worktrees/n3-b02-20260905/temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b02_20260905/forecast_package/checkpoint_update16.pt`.
If that worktree is gone, stage the same digest under
`/home/wu/hmasd-inputs/forecast_package_b02/checkpoint_update16.pt`. Cap 120 s
wall for the whole object including native build, both profiles, reduction
and publication. Preflight on the executing node, joined by `&&`.

Check (`WT` = remote worktree at LAUNCH_SHA):

```
/usr/local/bin/agent-task run dish_a01_check_20260905 'bash -lc '"'"'cd WT && export PYTHONPATH=WT OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/renewal_boundary_a01_check.memory.json && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_renewal_boundary_a01.py --checkpoint /home/wu/hmasd-worktrees/n3-b02-20260905/temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b02_20260905/forecast_package/checkpoint_update16.pt --checkpoint-sha256 504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66 --out temp/directions/degraded_incumbent_shadow_handover/exp/renewal_boundary_a01_check --launch-sha LAUNCH_SHA --profile check'"'"''
```

Formal (same node, not launched here):

```
/usr/local/bin/agent-task run dish_a01_formal_20260905 'bash -lc '"'"'cd WT && export PYTHONPATH=WT OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/degraded_incumbent_shadow_handover/exp/renewal_boundary_a01_formal.memory.json && /home/wu/.venvs/hmasd/bin/python scripts/run_dish_renewal_boundary_a01.py --checkpoint /home/wu/hmasd-worktrees/n3-b02-20260905/temp/directions/degraded_incumbent_shadow_handover/exp/forecast_package_b02_20260905/forecast_package/checkpoint_update16.pt --checkpoint-sha256 504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66 --out temp/directions/degraded_incumbent_shadow_handover/exp/renewal_boundary_a01_formal --launch-sha LAUNCH_SHA --profile formal'"'"''
```

Local fallback (Windows, A03 native builds under MSVC; only if remote refuses
and no remote process was accepted). Interpreter
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`. Check:

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/hmasd_resource_preflight.py admit-memory --out C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/exp/renewal_boundary_a01_check.memory.json && C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_dish_renewal_boundary_a01.py --checkpoint C:/Projects/HMASD/temp/b02_transport/forecast_package/checkpoint_update16.pt --checkpoint-sha256 504329d6ee0c001f827be67bf101d3850d2787a3011a7fb43137d3d3f162dc66 --out C:/Projects/HMASD/temp/directions/degraded_incumbent_shadow_handover/exp/renewal_boundary_a01_check --launch-sha LAUNCH_SHA --profile check
```

Formal local fallback replaces `--profile check` / `_check` paths with
`formal`. Do not treat the already-run Grok check directory as the frozen
formal output.

## Cost projection against 120 s

Law: `1 A03 native build + C checkpoint loads + C resets + W native steps + W recurrent forwards + reduction/publication`
with W=4 (check) or 64 (formal), C=1 or 2. Cap 120 s for the whole object.

Reused B02 measured terms (`DISH_FORECAST_PACKAGE_B02_CM_RECORD_20260905.md` /
result evidence): focused profile+admission 6.83 s (compile mixed with five
tests; compile not isolated); FORECAST_PACKAGE complete arm 298.60 s for
65536 training transitions plus 4800 evaluation ticks.

Pessimistic eval attribution (not a measured tick time): 64/4800 × 298.60 s
= 3.981 s for 64 ordinary steps if the entire package arm wall were eval.
Measured this session: local check 5.161 s (checkpoint load, A03 library
already present, 4 ticks, reduction, publication).

Unknown isolated: cold A03 compile on `wsl_4070`, checkpoint-load-only wall,
per-tick wall on the evaluation path.

Conservative composition without double-counting: 6.83 s compile upper +
5.16 s measured check + 60 remaining ticks × 298.60/4800 = 3.73 s + one extra
policy construction bounded by another ~5 s load ≈ 21 s, below 120 s. No arm
is over cap. Formal was not launched.

## Post-learner path

Not applicable: zero training, zero optimizer, no learner publication path.

## Stop conditions and residual engineering notes

No stop. Checkpoint digest matched. Measurement did not require R06 or
`study.py` edits. Reset phase on window 1 was 4 as expected. Projection is
under 120 s. Check-profile RSS was unmeasured on the one local run; the
typed Win32 helper is in the runner for subsequent invocations. First native
admission on K8/phase 4 is t=4, so the 4-tick check has no admission ticks
by construction.
