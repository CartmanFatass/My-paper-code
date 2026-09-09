# E01 technical record

Allocation: science card §0, scientific definition §§2–6. Authoring checkout
`C:/Projects/HMASD-worktrees/codex-acvc`, branch `codex/acvc`, starting revision
`7199ddc1a9173cd45c5734bb3991fbebf27d8428`, initially clean.

Implemented the fixed-only six-panel runner, dwell collector/stream support and separate-base
paired reduction. Binding and shared native host remain byte-unchanged. Engineering scope §4:
none. Independent reviewer `review_acvc_link_loss` found no remaining material issue after
explicit zero-learning exposure and completed-episode intervention scope were added.

Acceptance: `python -m pytest -q --basetemp <owned temp>/pytest
tests/experiments/candidates/acvc/native_link_loss_b01/test_fixed_reuse.py` passed one check
in 2.08 s. Whole command 4.3434695 s, conservatively charged **4.35 s** support. Synthetic
command/feedback, streams, reduction and full publication checked; no native pilot, no fit.
Invocation scratch was removed. No unchanged broad suite was repeated.

Cost projection reused from frozen card: C 10.526871886 s per panel, F 12.841401330 s,
dwell same unmeasured proxy; six-panel complete process 91.171740593 s, with support
121.171740593 s nominal. Serial critical path equals summed invocation wall; aggregate CPU
will be recorded from external process timing. Native CPU FP32, intra/inter-op threads 1.

Execution binding: node `wsl_4070`, supervisor `/usr/local/bin/agent-task`, task name
`acvc-fixed-retrace-reuse-e01-20260909`; detached source worktree
`/home/wu/hmasd-worktrees/acvc-fixed-retrace-reuse-e01-20260909` at this source commit.
Output relative to worktree: `temp/directions/acvc/exp/fixed_retrace_reuse_e01_20260909`.
Admission receipt: `temp/directions/acvc/e01_admission.json`.
Checkpoint evidence staged at `/home/wu/hmasd-inputs/acvc/fixed_retrace_reuse_e01_20260909/`
as `base8201.pt` and `base8202.pt`; remote SHA256 matches both frozen feasibility values.

Exact runner argv: `/home/wu/.venvs/hmasd/bin/python scripts/run_acvc_fixed_retrace_reuse_e01.py
--seed 8911 --checkpoint-8201 /home/wu/hmasd-inputs/acvc/fixed_retrace_reuse_e01_20260909/base8201.pt
--checkpoint-8202 /home/wu/hmasd-inputs/acvc/fixed_retrace_reuse_e01_20260909/base8202.pt
--output temp/directions/acvc/exp/fixed_retrace_reuse_e01_20260909 --launch-sha <this source SHA>
--execution-seconds 140`. Fresh destination `admit-memory` is joined by `&&` before this
command. External `/usr/bin/time` measures actual exit and aggregate CPU; `timeout
--signal=TERM --kill-after=5 145` bounds the execution to 150 s, including termination.
The internal 140 s limit reserves publication time. Full 30 s support reserve remains inside
180 s complete cap; 25.65 s remains for collection/readback. No retry or extra panel.

After accepted launch, dispatch MONITOR_ADD to the endpoint read from live
`C:/Projects/HMASD/.codex/hmasd-monitor.toml`. CM returns pending collection with adoption
state; Root resumes the original CM on terminal. No parallel status polling follows dispatch.
