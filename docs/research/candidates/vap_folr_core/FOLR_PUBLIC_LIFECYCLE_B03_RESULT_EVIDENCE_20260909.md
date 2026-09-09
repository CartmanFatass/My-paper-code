# FOLR B03 execution evidence

**Pending collection, not a completed technical result.** Frozen allocation/card/intake at0653b30ed35b4b007cd70a1e310ec8eadacf2cba; exact unchanged scientific source434f10cf95f16dd342cbf754382aa76155fcd2b7. Original CM `/root/dm_folr_p68_reentry/cm_public_lifecycle_b01` retains terminal collection/technical acceptance; original DM owns scientific intake.

New detached cwd `/home/wu/hmasd-worktrees/folr-public-lifecycle-b03-434f10cf` on `hmasd-wsl-node`, interpreter `/home/wu/.venvs/hmasd/bin/python`, CPU FP32, Torch compute/interop1. Fresh seeds7803/107803; no earlier state/data/checkpoint reused. Per-arm projections from card§4: RETAIN769.265s/RESET750.000s; hard1800s each/3600s pair. Reuse unchanged semantic review, B02 seed-route and final publication coverage; no tests/smoke rerun. Staged HEAD/source/preflight presence check0.4876519s plus1.6414286s prior support =2.1290805s of60s; ordinary staging/monitor dispatch is control-plane work.

Exact RETAIN command submitted under `/usr/local/bin/agent-task run folr-public-lifecycle-b03-retain-20260909`:

```sh
cd /home/wu/hmasd-worktrees/folr-public-lifecycle-b03-434f10cf && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vap_folr_core/exp/public_lifecycle_b03_seed7803_retain_memory.json && mkdir -p temp/directions/vap_folr_core/exp/public_lifecycle_b03_seed7803_retain && /usr/bin/time -v -o temp/directions/vap_folr_core/exp/public_lifecycle_b03_seed7803_retain/process.time /usr/bin/timeout --signal=TERM --kill-after=5s 1800s /home/wu/.venvs/hmasd/bin/python scripts/run_folr_public_lifecycle_b01.py --arm RETAIN --seed 7803 --evaluation-seed 107803 --launch-sha 434f10cf95f16dd342cbf754382aa76155fcd2b7 --out temp/directions/vap_folr_core/exp/public_lifecycle_b03_seed7803_retain
```

Supervisor accepted submission and returned tmux `agent_folr-public-lifecycle-b03-retain-20260909`, log `/home/wu/.agent-tasks/folr-public-lifecycle-b03-retain-20260909/task.log`. This confirms submission, not memory admission or scientific completion. One of two allowed submissions consumed; RESET remains unsubmitted until original-CM terminal collection/acceptance of RETAIN. No retry, third arm, extra evaluation or successor.

## Shared Monitor handoff

Read live primary `C:/Projects/HMASD/docs/project/EXPERIMENT_MONITOR.md` and `.codex/hmasd-monitor.toml`, with Root address calibration4f216bc9e. Direct MONITOR_ADD delivered successfully via app tool to configured task `01a087e5-2044-7301-abb6-7a1709a98197`, with exact node/handle/source/cwd/output/receipt paths and original CM/DM plus Root `01a07249-b095-7821-8ce2-e9c32ba85267`. Tool returned destination threadId, isError=false. Monitor instructed to read goal state and continue its active set or create a nonempty goal without invented budget, and notify Root directly of adoption/terminal facts.

**Dispatch accepted; adoption pending confirmation.** CM performed no remote status polling after dispatch and does not poll Monitor's task. Resource receipt and terminal facts await Monitor notification and Root's native resumption of the original CM. This handoff does not complete the two-arm batch or transfer technical acceptance. Root handles any observation-dispatch/adoption loss against the same accepted handle, never a duplicate launch.

On resumption collect summary.json/all32 final returns, final.pt, process.time, memory receipt and task.log under the same local relative B03 output root. Preserve both scoped supervisor records and this new execution worktree until Root's later explicit closeout trigger. Shared authoring checkout and policy-blocked earlier scratch remain untouched.
