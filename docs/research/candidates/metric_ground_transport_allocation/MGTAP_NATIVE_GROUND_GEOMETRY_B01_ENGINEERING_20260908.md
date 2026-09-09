# MGTAP B01 bounded CM repair — 2026-09-08

This record supersedes the earlier engineering readiness claims at `55e3adce5`.
The original assignment's REL/DENSE encoders remain unchanged. This repair adds
the fixed two-master primary, elapsed deadlines, startup numerical controls,
and reconciles shared UCOPE source to current main. No native experiment,
scientific exposure, cost probe, new arm or child delegation occurred.

CM execution task: `01a084ec-b10f-7c63-b44f-439ec6a77f3d`.
Assigning parent: `01a08204-6445-7461-badf-1150080ed87b`.
Checkout: `C:/Projects/HMASD-worktrees/dm-n5-continue-20260904`;
branch: `codex/mgtap`. This is CM implementation/testing evidence, not an
independent Reviewer report. The parent retains the independent review handoff.

## Source reconciliation and preserved semantics

Inspected main commit: `6485fe0080abafe7521ed89f3425516407303d78`.
All five files in `experiments/candidates/ucope/uav_motion_prefix_b01/`
now match that main commit. Relative to this direction's previous checkout,
only `study.py` needed reconciliation: its newer renewal-B02 route selection
is retained. The environment, policy, learner and package initializer already
matched main and the frozen `d726acf63f8db47bd2e93e43cac8bbd27529d8ad`
source pin. No legacy learner is vendored and current main is not replaced.

The adapter imports main-compatible `collect_episode`, `update`, `optimizer_for`,
`snapshot`, `exposure`, `generator`, `new_counts`, and the existing `Deadline`
and JSON publication functions. Reward summation and ordinary value arithmetic
are unchanged; optional value normalization is not enabled. Both arms retain
primitive G, no duration draw, `agent_compound`, entropy coefficient 0.01,
the same seed domains, 512 training episodes and 32 sampled 256-step endpoints.
The typed equations, parameter counts, common zero-projection initial policy,
private branch initialization and recurrent consumer are unchanged.

## Primary and failure behavior

`runner.aggregate` recomputes per-master values from retained rows and applies
`mean(Delta[8201], Delta[8202])`, with the frozen ±0.01 branches. It never
averages only the available master. Both masters' paired differences, means,
individual REL/DENSE/H values, episode indices and source limits are retained.
Opposite signs remain explicit; H remains diagnostic and is not an exclusion
criterion. Incomplete training, missing/duplicate masters, missing/duplicate or
nonfinite primary endpoints, mismatched row masters, or shortened endpoint
exposure produce `INCOMPLETE` with no aggregate mean or performance polarity.
The `--aggregate` CLI accepts exactly the two summary paths and reports unreadable
or corrupt input without converting it into a favorable subset. No statistical
model or confidence claim is added.

## Elapsed bounds and controls

The CLI captures `time.monotonic()` before package and Torch imports. Before
Torch/NumPy import, the package sets OMP, MKL, OpenBLAS, NumExpr, Accelerate and
BLIS thread environment controls to one and disables CUDA visibility. Torch
intra/inter-op threads are one, default dtype is FP32 and device is CPU.

The planned bounds are 1,800 seconds per arm and 3,600 seconds per master pair.
REL includes startup/imports and common pair construction. DENSE includes the H
reference and final publication. The pair clock never resets between arms.
The source learner's checks cover reset, primitive steps and PPO updates;
the runner also checks construction, arm transitions and publication. Exceptions
retain completed rows and live counters, including partial episode steps, and
write a summary. A publication overrun preserves completed measurements while
setting `CAP_BREACH`; a partial endpoint has no performance inference.

As in the shared source, checks are cooperative: an indivisible native step or
write may finish after its deadline. Its elapsed overrun is recorded, then no
further learning runs. Corrective serialization reports the breach. This is not
a promise to interrupt an opaque call at exactly 1,800 seconds. Process exit,
interpreter teardown and supervisor logs provide the external full-process wall;
the recorded runner wall includes imports through final publication observation.

## Prospective command, never executed here

For each master in 8201, 8202, substitute the committed launch SHA in both the
detached checkout and handle. `prospective_native_command(master, sha)` emits:

```text
ssh hmasd-wsl-node '/usr/local/bin/agent-task run mgtap-b01-8201-<EXACT_SHA> bash -lc "cd /home/wu/hmasd-worktrees/mgtap_b01_<EXACT_SHA> && /home/wu/.venvs/hmasd/bin/python scripts/hmasd_resource_preflight.py admit-memory --out /home/wu/hmasd-worktrees/mgtap_b01_<EXACT_SHA>/temp/directions/metric_ground_transport_allocation/exp/b01_8201/admission.json && /home/wu/.venvs/hmasd/bin/python scripts/run_mgtap_native_ground_geometry_b01.py --native --master 8201 --output /home/wu/hmasd-worktrees/mgtap_b01_<EXACT_SHA>/temp/directions/metric_ground_transport_allocation/exp/b01_8201 --arm-cap 1800 --pair-cap 3600"'
```

Node: `wsl_4070`, SSH `hmasd-wsl-node`; CPU FP32 even though the host has a GPU.
The 8202 command changes master, handle and output suffix only. The existing
`agent-task run` supervisor receives `bash -lc` directly. Node-local admission
and runner share one command with `&&`. Worktree setup and any later launch
remain the parent's selected execution assignment. No local fallback was chosen.

After collection, aggregate the two exact `summary.json` paths with:

```text
python scripts/run_mgtap_native_ground_geometry_b01.py --aggregate <8201_summary.json> <8202_summary.json> --output <aggregate_summary.json>
```

The per-fit cost law stays
`C_init + 131072*c_env_actor + 1024*c_update + 8192*c_eval + C_publication`.
DENSE additionally pays for 8192 H steps per master. Coefficients remain
unmeasured; 1800/3600 are planned bounds, not measured affordability. No probe
or run is selected by this repair.

## Focused acceptance evidence

Interpreter: `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`.
Command: `-m pytest -q -p no:cacheprovider --basetemp
temp/directions/metric_ground_transport_allocation/test/b01_repair_20260908
tests/experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01`.

The focused suite covers parameter matching/padding/RNG/credit, synthetic
forward-backward-publication, both-master branches including opposite effects,
missing/corrupt data and H retention, startup expiration before model construction,
partial native-shaped step counters, late publication, and a clean process proving
thread controls precede Torch import. All environment calls use SyntheticAdapter.
The first pytest invocation had six setup errors because the basetemp parent did
not exist; after creating that directory, 26 tests passed in 7.51 seconds.
One additional shortened-endpoint case was then added and checked below.
The pytest warning about disabled cache configuration is unrelated to code behavior.

No new §4 machinery: the source Deadline and publication functions are reused.
Runner remains under 600 lines, and checks remain below the five-minute budget.
Parent/Reviewer must inspect this exact repair before claiming independent review;
no self-review is represented as independent provenance.

Final changed-endpoint check: 16 passed, 4 deselected in 4.21 seconds. Combined with the prior full suite, all 27 cases are covered. git diff --check passes; the runner is 475 lines. git diff against inspected main is empty for all five shared UCOPE paths.
