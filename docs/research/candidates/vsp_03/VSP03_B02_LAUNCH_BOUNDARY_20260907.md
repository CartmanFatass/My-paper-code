# VSP03 B02 selected launch boundary

This records the sole P09 invocation, not an accepted process. Root substitutes only
the accepted committed/pushed source SHA in the detached cwd below and uses the existing
configured `agent-task` supervisor. No source staging before commit, extra test episode,
second invocation, or local fallback is selected.

- Node: `wsl_4070` (`ssh hmasd-wsl-node`); CPU float32, one compute thread.
- Interpreter: `/home/wu/.venvs/hmasd/bin/python`.
- Cwd: `/home/wu/hmasd-worktrees/vsp03-b02-p09-<accepted-source-sha>` detached at that SHA.
- Output: `/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p09_20260907`.
- Adjacent receipt: `/home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p09_20260907_admission.json`.
- Handle proposed for the one supervisor dispatch: `vsp03-b02-p09-20260907`.
- Hard stop:120 seconds covering the complete command below, terminating the foreground
  shell/process group with SIGKILL at the bound; no grace interval or retry. Internal
  monotonic checks provide ordinary partial error publication where time remains.

The supervisor executes this logical shell command from the exact detached cwd. Its
standard stdout/stderr and terminal status are retained by the existing supervisor.
The shell body in `VSP03_B02_COMMAND` is also recorded in `summary.json`; the complete
outer timeout command, cwd and admitted SHA are recorded in technical collection.

```bash
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
export VSP03_B02_COMMAND='VSP03_B02_STARTED=$(/home/wu/.venvs/hmasd/bin/python -c "import time; print(time.perf_counter())")
/home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p09_20260907_admission.json && exec /home/wu/.venvs/hmasd/bin/python scripts/run_vsp03_b02.py --seed 4 --out /home/wu/projects/HMASD/temp/directions/vsp_03/exp/b02_seed4_p09_20260907 --started-monotonic "$VSP03_B02_STARTED" --node wsl_4070'
/usr/bin/timeout --signal=KILL 120s bash -c "$VSP03_B02_COMMAND"
```

Admission and exact runner are adjacent through `&&`, on the execution node. The outer
timeout begins before the timestamp helper; the internal timestamp begins before
admission and does not reset per arm. No model or RNG world is constructed by timestamp
or preflight. The existing supervisor's terminal elapsed/exit establishes the outer
boundary; `runner_exit_ready` and the summary's readback line are narrower observations.
A summary marked complete without terminal conformance is not a complete120-second result.

After an accepted supervisor handle, CM sends that same handle/cwd/SHA/log/receipt/output
to Root's current observation route and retains collection ownership. Uncertain acceptance
is resolved against the same handle; never dispatch a duplicate. No live tree is copied
until terminal collection. A route failure returns its exact gap without running locally.
