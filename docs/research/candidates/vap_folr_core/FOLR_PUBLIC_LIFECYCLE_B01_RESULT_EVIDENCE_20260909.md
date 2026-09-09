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

RETAIN accepted at supervisor start epoch1788972342 (2026-09-09T16:45:42Z), PID3061064, tmux `agent_folr-public-lifecycle-b01-retain-20260909`. Destination admission at16:45:42.395319Z passed both physical/effective floors, each15,635,152,896 available bytes, threshold4,294,967,296. At first observation status running/exit null. At26.392907447s, the run reported episode200/update169. These are progress facts, not final performance or a new launch projection.

Staging initially used non-login remote Git and hung in network access; a configured `zsh -lic` fetch succeeded. The two precisely identified non-scientific Git requests were terminated, their SSH sessions ended, then the detached worktree was created and exact HEAD/source diff verified. No scientific process or admission occurred during this repair. Network-shell gitstatus/zle startup warnings did not prevent successful fetch/staging. Remote main's unrelated bundle files were untouched.

RETAIN terminated exit0 at2026-09-09T16:58:33Z. External complete elapsed770.69s, user757.39s/system13.30s, peak RSS656364KiB. Runner pre-publication wall729.723850s and RSS642380KiB have narrower boundaries; external metrics control the complete cap. The difference is retained without an unmeasured attribution. Full counts5000 episodes/100000 training ticks/4969 optimizer steps/32 evaluations/640 evaluation ticks; mean native return2.104375. Training events births20925/departures7417/opportunities45511/resets0; evaluation138/40/304/0.

Collected final.pt, summary.json, process.time, task.log and admission receipt into the same relative local output paths. Direct primary/count readback passed; local/remote checkpoint SHA256 `a95b46fd26afddff80fb4838d475db2077902c2f4deed92aaeedb156ddc4851e` and summary `48e11763ad98cd9c173bd8f0150eb5e47b48866e8ad4a8f7f563af1455e61c6d` agree. This is post-collection artifact verification, not runtime provenance machinery.

Before RESET: the now-complete RETAIN path supplies a770.69s per-arm point estimate for the identical4969-update workload. RESET adds boolean incoming carry masking, with unchanged model dimensions and invocation counts; its actual time remains to be measured under its original1800s cap. This is a same-workload planning estimate, not a guaranteed upper bound or altered cap. No scientific outcome changes the fixed second-arm allocation.
