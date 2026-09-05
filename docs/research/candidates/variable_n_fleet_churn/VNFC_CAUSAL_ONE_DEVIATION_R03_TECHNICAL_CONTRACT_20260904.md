# VNFC R03 — calibration implementation contract

CM checkout: `C:/Projects/HMASD-worktrees/cm-vnfc-causal-r03-20260904`, branch
`codex/cm-vnfc-causal-r03-20260904`, based on DM disposition `1b671d1af`.
The saved checkout's unrelated changes are untouched. The frozen card and the cost-accounting
addendum control the science; this slice implements calibration and a pure exact solver only.

## Observable and acceptance

Measure the unchanged native tick and complete `grun_bcrh` cost on deterministic synthetic inputs,
plus synthetic exact-solver and serialization cost. Do not instantiate the target panel, expose
candidate endpoints, select a native action map, draw RNG, initialize a learner or create a model,
optimizer or checkpoint. A calibration is technical evidence, not CI-A/B/C or a headroom result.
The full census is not implemented by this commit.

All native source dependencies are read-only: R09 `bpcr_backend.cpp`, `bpcr_general.hpp`, checker,
and the headroom adapter. The new C++ file includes the accepted adapter unchanged. Scorer,
checker, enumeration, exact integer arithmetic, transitions and physical command law remain
the original functions; the calibration exports only timings, counts and agreement flags.
One process/one computational thread, no device or host semantics change. Build and execution
are pinned to the configured Linux `wsl_4070` node for this invocation.

Scope specification section 4 additions: **none**. In particular no new supervisor, retry,
registry, schema, source-currentness guard, manifest, telemetry service or compatibility layer.
The existing external `agent-task` is the assigned execution transport. No source edits to
dependencies, shared core, workflow configuration, DM card/intake or Portfolio.

## Source-grounded causal inventory for later census

The accepted key has not yet been implemented. Its field inventory, following the DM's written
interpretation, is:

- Exposed reset `prehistory_commands` (six physical commands); no pre-loss observations are
  fabricated. See R09 `native/bpcr_general.hpp` `ginteractive_reset` and `ginteractive_snapshot`.
- Each actual post-loss observation through epoch d: public double agent rows, zone rows,
  globals, token states/elapsed, legal masks/ETA/energy margins, with stable entity associations.
  `gobservation` at lines 52–54 emits these; line54 publicly encodes the failed-zone indicator.
- Actual BCRH input fields through d: epoch; active count; entity rank and opaque tie order;
  each agent's capability, node/route/destination, token/state/acquisition and energy;
  clearance; accrued fail/total delivered and demand; current demand/obstruction. These are
  passed by `ginteractive_bcrh` at line110 and declared in `GBcrhInput` at line9.
- Prior physical commands; native fixed token order is zone1 executor/relay, zone2
  executor/relay. Presentation row is not identity. Learner failed/intact remapping is not used.

No ABI magic/padding, full internal GS, seed/namespace/panel row, administrative zone label,
future tape, hidden state or post-action outcome enters the key. Physical rank and opaque order
are retained because this zero-learner object follows actual BCRH information, rather than the
restricted learned feature tensor. A future full census must serialize only this inventory and
independently check identical-key shared commands; this document does not claim that check ran.

## Cost and coverage recorded before calibration

One result arm has prospective upper counts: 94,128 continuations, 9,418,560 native ticks,
376,688 full BCRH calls and 738,685,168 candidate rows. A row timing includes scorer, independent
checker/enumerator, allocation and comparison. Calibration takes maximum unit time across the
six epochs and four tick cases and multiplies by a prospectively fixed factor2.

The pure exact optimizer keeps rational Pareto states, coalesces identical totals on minimum
deviations then canonical map, and separately computes scalar aggregate/zone maxima so dominance
cannot erase their tie winners. Its synthetic timing uses 16 classes with 1961 options, with
artificial rational tradeoffs, and never native outcomes. At a fixed stage, native zone return
totals lie on a 1/1200 lattice with at most9601 coordinate values (eight worlds; demand denominators
60/80/100/120). Thus three epochs and at most16 classes imply at most
`3*16*9601*1961` DP extensions. Full measured solver wall, including allocation/sorting, is
extrapolated to that count with factor2; this is conservative planning, not a worst-case runtime
theorem. Synthetic command numbers are opaque optimizer inputs, not executable native commands.

Additional overhead includes 96 eight-agent prehistory enumerations, synthetic16KiB record
allocation/grouping/serialization extrapolated to94,128 records with factor2, and a fixed60-second
setup/publication allowance. These allowances remain visible; no claim that a pilot proves full
publication speed or mathematical wall conformance. The summary separately exposes whether
native terms alone exceed2700 seconds, so a large synthetic solver extrapolation cannot obscure
the directly measured native bottleneck.

Post-learner publication obligation: no learner and no predecessor post-learner failure on this
object. The toy runner tests pure solver→projection→summary publication without a native call.
This is not full census publication coverage; that remains an open implementation item if the
calibration admits further work. The sole native calibration is not repeated in tests.

## Exact execution boundary

Commit and push these bytes, then create a detached remote worktree at that SHA under
`/home/wu/hmasd-worktrees/vnfc-causal-r03-<sha8>`. Record the resolved SHA/cwd in the launch record.
Build explicitly with `/home/wu/.venvs/hmasd/bin/python -c` importing `build_native_backend()`;
the compiler uses C++20, O2, no fast-math, no FP contraction, and a shared CPU library. The build
does not call calibration. Run the focused tests once before launch against committed bytes.

The one accepted calibration task is named `vnfc_causal_r03_calibration_20260904_01`:

```text
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
python scripts/hmasd_resource_preflight.py admit-memory --out <out-parent>/memory.json
&& timeout 60s python scripts/run_vnfc_causal_headroom.py --mode calibration
   --seed 2026090311 --launch-sha <exact-sha> --out <out-parent>/calibration
```

Here `python` is exactly `/home/wu/.venvs/hmasd/bin/python` and out-parent is
`<cwd>/temp/directions/variable_n_fleet_churn/exp/causal_r03_20260904`.
Preflight and runner are adjacent in one `agent-task` payload, and require actual-node physical
and effective available memory each>=4GiB. No duplicate launch after uncertain acceptance.
The native loader requires the prebuilt file and does not build inside calibration.
Natural completion before60 seconds yields the timing-only summary; timeout, failed admission,
native disagreement or missing summary is a technical incomplete boundary, never scientific polarity.

On acceptance send node/task/SHA/cwd/output/log/admission/bounds directly to DM and shared
`/root/tracker_tl_experiments`; release polling only after tracker adoption. If the natural
calibration finishes first, retain and collect that same task. CM retains technical collection.
If projected time>=2700s return `BLOCKED_WALL_CAP` with no census/result invocation. If below,
finish and independently review the full census before the sole result invocation.
