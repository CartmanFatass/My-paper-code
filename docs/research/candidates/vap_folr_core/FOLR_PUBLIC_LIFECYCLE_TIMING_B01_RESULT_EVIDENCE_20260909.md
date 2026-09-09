# FOLR public lifecycle TIMING-B01 technical evidence

Implementation accepted; RETAIN running under confirmed Monitor adoption, pending terminal collection. EVENT and RANDOM remain unsubmitted. Allocation: card §§2–6 and intake §7 at `8fc84a01eaaf8c89197020a75879ba9dfeea0e33`, Root main `fdede5b8897e412d68d2a341a379efac69feb429`. Original CM owns implementation, execution and terminal collection. The sequence is RETAIN → EVENT → RANDOM, exactly one accepted submission each; failure ends dependent execution. No retry, replacement, top-up, cost probe or successor.

## Source and check index

All source is under `experiments/candidates/vap_folr_core/public_lifecycle_b01/` unless named otherwise. Base source `434f10cf95f16dd342cbf754382aa76155fcd2b7`.

| Path | Changed boundary |
| --- | --- |
| `model.py` | EVENT is the prior RESET law; RANDOM clears realized eligible masks before GRU |
| `collection.py` | Draw one five-slot vector per position including entry/terminal, store Boolean masks in episode replay, count actual nonterminal random resets; compute all three frozen contrasts and combined rule |
| `environment.py` | Add all-eligible true-survivor action opportunities; preserve birth/departure convention and event-bound counter |
| `scripts/run_folr_public_lifecycle_b01.py` | Fresh seeds7804/107804, isolated phase-persistent PCG64 streams207804/307804 for RANDOM,128 final evaluations, unchanged5000 episodes/4969 updates |
| `tests/experiments/candidates/vap_folr_core/public_lifecycle_b01/test_boundaries.py` | Fixed-fixture lifecycle/refill, mask draw schedule/RNG isolation, acting/online/target reuse, before-GRU state, terminal counts, branch thresholds and real runner/publication with scientific stand-ins |

Native environment, attention, mixer and learner are unchanged. Existing replay stacking automatically carries the realized mask to both actor unrolls; no learner RNG or optimizer plumbing changes. The only Scope Spec §4 addition is the aggregate eligible-survivor counter requested at science card line215 (§6). No new compatibility, guard, recovery or telemetry framework.

Focused command: configured local Python `-m pytest -q -p no:cacheprovider --basetemp temp/directions/vap_folr_core/test/timing_b01_check01 tests/experiments/candidates/vap_folr_core/public_lifecycle_b01/test_boundaries.py`. Result: **18 passed in4.97s**, enclosing check6.265178s. This includes synthetic learner/backprop and checkpoint publication plus stand-in full runner loops; no additional scientific training instance was run. Independent reviewer `/root/dm_folr_p68_reentry/cm_public_lifecycle_b01/review` inspected the complete source/test diff and returned no material finding, running no duplicate checks. Diff whitespace check passed. Production remains785 lines including108 runner lines.

Post-learner coverage: real summary publication and the runner's fixed128/no-update evaluation path exercised with stand-ins; synthetic checkpoint save retained. The unchanged native path reuses accepted B01–B03 checks. No extra smoke follows source acceptance.

Scientific-tools current main scientific-reading reference and Foundations §§2–4 plus MARL information/history passages were read; intake §3's CAMA/Sable findings were reused. Stochastic clearing changes the recurrent policy package. Reusing realized masks reconstructs its actual history; equal public inputs do not establish equal dose or isolate event-timing causality. p=.1 remains explicitly unmatched and all prior signs, including B03 reversal, remain separate.

Supporting budget: allocation-status0.7256294s + focused check6.265178s =6.9908074s measured so far of300s. Administrative source/specification reading, editing, Git and transport are outside runtime-check accounting; no cost probe. Further collection/readback time is charged here, with capacity reserved for DM intake.

Scratch exception: the first combined PowerShell test/finally-cleanup command was rejected before process creation (`blocked by policy`). Test-only execution succeeded. This invocation's `temp/directions/vap_folr_core/test/timing_b01_check01` remains; the rejected removal was not bypassed. Earlier policy-blocked scratch is untouched. This is an operational cleanup gap, not missing primary coverage.

## Frozen execution plan

Route: configured `hmasd-wsl-node`, `/home/wu/.venvs/hmasd/bin/python`, CPU FP32, Torch compute/interop1, new detached exact-source worktree. Fresh destination admission immediately precedes each arm. Full command uses `/usr/bin/time -v` around `/usr/bin/timeout --signal=TERM --kill-after=5s 1800s` and the existing runner.1800s includes startup, learning,128 evaluations and publication; total triple cap5400s. No local fallback.

Per-arm complete-path projections reused from card §5: RETAIN778.701s, EVENT765.647s, RANDOM772.174s (unmeasured midpoint proxy with unknown mask overhead), sum2316.522s. Training work is4969×32×21×5×2 replay actor rows per arm, plus backward/mixing and5128×21×5 acting rows; RANDOM alone538440 private uniform draws. All three planned arms fit their individual1800s caps. Projection is not observed conformance. Complete external wall, aggregate OS CPU and study critical path remain distinct and will be reported after collection.

The original CM directly registers each accepted handle with live-main shared Monitor `01a087e5-2044-7301-abb6-7a1709a98197`, Root destination `01a07249-b095-7821-8ce2-e9c32ba85267`. Dispatch acceptance is not adoption. Root confirms adoption and resumes this same CM at terminal for collection and the next already allocated arm. No parallel status polling after dispatch. Preserve exact handles and roots until explicit closeout.

## RETAIN accepted, pending collection

Source/check/E0 commit `74d023d7d55453da8a5d5dccebd518e4ffdb65c8` was pushed before execution. A non-login-shell Git fetch stalled and was stopped before any worktree or scientific submission; the configured `zsh -lic` network shell then fetched successfully and staged a new detached exact-source checkout. The staged source was clean and source/preflight/interpreter presence readback passed in0.6174942s. DM's independent source/E0 readback took0.6924301s. Cumulative measured support is **8.3007317s of300s** before collection, leaving291.6992683s; Git/staging transport is separate control-plane work.

Accepted handle `folr-public-lifecycle-timing-b01-retain-20260909`, tmux `agent_folr-public-lifecycle-timing-b01-retain-20260909`, log `/home/wu/.agent-tasks/folr-public-lifecycle-timing-b01-retain-20260909/task.log`. Exact supervisor command:

```sh
cd /home/wu/hmasd-worktrees/folr-public-lifecycle-timing-b01-74d023d7 && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out temp/directions/vap_folr_core/exp/public_lifecycle_timing_b01_seed7804_retain_memory.json && mkdir -p temp/directions/vap_folr_core/exp/public_lifecycle_timing_b01_seed7804_retain && /usr/bin/time -v -o temp/directions/vap_folr_core/exp/public_lifecycle_timing_b01_seed7804_retain/process.time /usr/bin/timeout --signal=TERM --kill-after=5s 1800s /home/wu/.venvs/hmasd/bin/python scripts/run_folr_public_lifecycle_b01.py --arm RETAIN --seed 7804 --evaluation-seed 107804 --launch-sha 74d023d7d55453da8a5d5dccebd518e4ffdb65c8 --out temp/directions/vap_folr_core/exp/public_lifecycle_timing_b01_seed7804_retain
```

Direct MONITOR_ADD via app tool to the live configured task returned destination threadId and `isError=false`, carrying the exact handle/source/cwd/root/receipt and original CM/DM/Root. **Dispatch accepted, adoption not yet confirmed.** No remote scientific status polling followed. Acceptance of submission does not establish memory admission, resource conformance or scientific result. Root resumes original CM for terminal collection of summary/all128 returns, checkpoint, process.time, receipt and log; only then does the next already allocated arm proceed. Preserve new execution/supervisor roots for later explicit closeout. Technical acceptance of the complete triple remains pending.

Root subsequently confirmed actual Monitor adoption at2026-09-09T22:40:57.9647914Z: running, exit null, tmux true, PID3075634, uptime36s, new active Monitor goal. Observation transfer is complete. Root independently accepted source/review and integrated74d023d7d as main `fd034727b`. Original CM returns pending terminal collection; EVENT and RANDOM remain the already allocated next steps, not submitted early.
