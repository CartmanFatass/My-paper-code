# FOLR public lifecycle B01 execution evidence

Source SHA: `387a40f3f1c15ba0ddc4c59d9245ff2b47bc2358`, committed and pushed. [Technical acceptance](FOLR_PUBLIC_LIFECYCLE_B01_ENGINEERING_RESULT_20260909.md). Sole observer: `/root/dm_folr_p68_reentry/cm_public_lifecycle_b01`; DM `/root/dm_folr_p68_reentry` owns intake. Sending handle facts to DM/Root does not transfer observation.

Node `hmasd-wsl-node` (`wsl_4070`, LAPTOP-U9TDKC8A), CPU FP32, interpreter `/home/wu/.venvs/hmasd/bin/python`. Detached cwd `/home/wu/hmasd-worktrees/folr-public-lifecycle-b01-387a40f3`. One environment/process per arm, Torch compute/interop1; no hardware-dependent estimand and no allocated local fallback. Frozen training seed7801 and final evaluation seed107801.

Exact command for RETAIN, submitted to `/usr/local/bin/agent-task run folr-public-lifecycle-b01-retain-20260909`:

```sh
cd /home/wu/hmasd-worktrees/folr-public-lifecycle-b01-387a40f3 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vap_folr_core/exp/public_lifecycle_b01_20260909_retain_memory.json && mkdir -p temp/directions/vap_folr_core/exp/public_lifecycle_b01_20260909_retain && /usr/bin/time -v -o temp/directions/vap_folr_core/exp/public_lifecycle_b01_20260909_retain/process.time /usr/bin/timeout --signal=TERM --kill-after=5s 1800s /home/wu/.venvs/hmasd/bin/python scripts/run_folr_public_lifecycle_b01.py --arm RETAIN --seed 7801 --launch-sha 387a40f3f1c15ba0ddc4c59d9245ff2b47bc2358 --out temp/directions/vap_folr_core/exp/public_lifecycle_b01_20260909_retain
```

RESET has the identical command replacing `retain` with `reset` in handle/paths and `--arm RETAIN` with `--arm RESET`; SHA, seed, interpreter, cwd and1800s bound are unchanged. It is submitted only after intact RETAIN completion/collection. Each command has fresh destination admission; no rejected-admission fallback, scientific retry or successor. The original wall projection is unknown for each arm; dominant cost and fixed counts remain in card§5. External time captures the complete Python invocation (startup through final publication), while runner `wall_seconds` starts at its first Python statement and is sampled immediately before JSON writing. GNU timeout failure reporting may use up to5s kill grace; that cannot yield an accepted over-cap scientific result.

## Observation and collection

Staging/acceptance and terminal facts pending. No scientific process was accepted when this record was first frozen. Exact supervisor status/logs, admission receipt, summary, final checkpoint and external process.time are retained under the named run root upon collection. Scientific comparison requires both intact final summaries and their complete32 native returns. A partial/error summary labels counts as completed episodes/updates only; interrupted prefixes are unmeasured, not zero.
