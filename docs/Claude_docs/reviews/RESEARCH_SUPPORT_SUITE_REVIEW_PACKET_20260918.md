# Research support and UAV/UE visualization suite — review packet

**Date:** 2026-09-18
**Author:** Claude session (DM), Opus 5
**Under review:** commit `bafe782b7` on `main` (78 files, 45,338 insertions, 0 deletions)
**Baseline:** `ef6cb091a621bf04a734878346dbd8860a1ebe59`
**Specification:** `Research_Support_and_UAV_Visualization_Claude_Package_EN_v1_1.zip` (v1.1)
**Delivery record:** [`../deliverables/2026-09-18-research-support-and-visualization-suite.md`](../deliverables/2026-09-18-research-support-and-visualization-suite.md)

```
FORMAL_TRAINING_FITS_STARTED: 0
OPTIMIZER_UPDATES_PERFORMED:  0
HYPERPARAMETER_SEARCHES_RUN:  0
CHECKPOINTS_EXECUTED:         0
RESEARCH_DIRECTIONS_TOUCHED:  0
OWNER_PAUSE:                  untouched
```

This packet is written **for a reviewer**, not as a second delivery record. It states what was
completed, points a reviewer at the places where a defect would actually hurt, and gives a full
account of the one milestone that was not implemented. Where it repeats a number from the
delivery record, that number was measured, not estimated; every claim below names the file or
the command it rests on so it can be re-derived without trusting this document.

---

## Part 1 — Completion

### 1.1 What was built

`tools/research_support/`, 40 modules plus an operator `README.md`. It is a **reading** layer
over artifacts that already exist. It starts no research; every executing command prints its
scope first, including `optimizer updates: 0` and `formal training fits: 0`.

| Area | Module | What it is |
|---|---|---|
| Capture | `capture/` (5 files) | the Section 0.2 efficiency contract, trace store, transports, one observer per route |
| Viewer | `viewer/` (server + 4 static files) | loopback-only read-only server and the 2-D/3-D browser client |
| Capability | `plots/capability.py` | C01–C14 algorithm capability reports |
| Readers | `readers/` (3 families) | run-artifact readers |
| Model | `records.py` | the frozen shared data model everything imports |
| CLI | `cli.py` | 14 subcommands |

### 1.2 Status by deliverable

| Deliverable | Status |
|---|---|
| Live 2-D viewer, live 3-D viewer | `VERIFIED` |
| Genuinely mobile legacy UE scenario | `VERIFIED` (ground max displacement 1098.4 m in one episode) |
| Service-restoration scene | `VERIFIED` |
| Run inspector, comparison checker, config/env inspector | `VERIFIED` |
| Offline replay, event seeking, synchronised two-policy comparison | `VERIFIED` |
| Portable exports | `VERIFIED` (mp4 refuses with an actionable message; no encoder here) |
| Change-aware test recommendation, context bundles | `VERIFIED` |
| Failure bundles | `VERIFIED` as a library API — see the correction in §4 |
| Data / scenario diagnostics | `VERIFIED` |
| Efficiency contract (Section 0.2) | `VERIFIED`, measured |
| Off-path non-interference | `VERIFIED`, trajectory-identical against the pinned baseline |
| Algorithm capability reports C01–C14 | `PARTIAL` — 7 of 14 fully exercised |
| **Native runner integration (M5)** | **`NOT_IMPLEMENTED`** — Part 3 |

### 1.3 Tests

```
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest tests/tools/research_support -q
  624 passed, 2 skipped

C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest tests/envs/uav_service_restoration -q
  255 passed
```

The 2 skips are deliberate encoder-conditional cases (Pillow present → GIF-refusal case
skipped; imageio absent → MP4-success case skipped). The second run is the environment's own
pre-existing suite against the shared-core change.

### 1.4 The single shared-core change

`envs/uav_service_restoration/env.py`, **+179 / −0**: `set_capture_observer()`, a
`capture_observer` property, `capture_capabilities()`, a `_readonly` guard, four observer call
sites. `capture_observer` is `None` in the constructor and on every existing path.

Non-interference is **measured, not asserted**.
`tests/tools/research_support/test_off_path_noninterference.py` loads the pre-change `env.py`
out of git **at a pinned commit** (not `HEAD`), executes it inside the real package, and
compares a full 60-decision-step episode including the terminal transition:

- trajectory SHA-256 over observations, rewards, termination/truncation flags, info payloads
  and the episode summary, hashed over raw float bits — identical
- `_evaluate_service` call count **600 = 600** — no display-driven extra solve
- episode boundary at step **60** on both sides
- RNG state over all **5** streams in `env._rngs` — identical
- attaching an observer whose gate is profile `off` also leaves the trajectory identical

The loader **refuses a baseline that already contains the seam**, so this test cannot decay
into "the new code equals itself" now that the change is committed. A companion test fails if
the RNG comparison ever finds zero streams.

### 1.5 Measured efficiency

`python -m tools.research_support efficiency-check --config configs/uav_service_restoration/smoke_fixture.json`

| condition | median ms/decision | p95 | frames | admitted/attempts |
|---|---|---|---|---|
| `pre_change` (env.py at `ef6cb091a`) | 37.6677 | 75.0767 | 0 | 0/0 |
| `off` (what every training run does) | 36.8572 | 71.1185 | 0 | 0/0 |
| `preview_no_viewer` | 37.0768 | 72.5066 | **0** | **0/41** |
| `preview_with_viewer` (rate gates opened fully) | 47.6615 | 83.8258 | 38 | 38/41 |
| `stalled_consumer` | 43.5324 | 80.5373 | 34 | 34/41 |
| `record_eval` | 42.2266 | 87.2953 | 41 | 41/41 |

**Every armed condition reproduced the capture-off trajectory hash exactly.** Capture running,
copying arrays, building frames and writing a trace changes no scientific quantity.

Read the timings honestly: `off` measured **−2.15%** against the baseline — nominally *faster*,
i.e. the seam's cost is below this measurement's noise floor. That **bounds** the cost, it does
not resolve it. The identity claim rests on the hash, not on the timing. `preview_with_viewer`
is deliberately un-rate-limited, so +29% is an upper bound on preview cost, not the shipped
default (one frame per wall-clock second and ≥100 completed lane steps).

### 1.6 Viewer security, verified against the running server

Token missing/wrong → 403; correct token in query and in header → 200; foreign `Origin` → 403;
plain, percent-encoded, double-encoded and backslash traversal → 403 `refused path outside the
approved root`; `POST` and `DELETE` → 405 `this viewer is read-only`; absolute and
protocol-relative URLs in page and assets → **0**. The browser independently confirmed **7
requests, all to `127.0.0.1:8791`, zero external**.

### 1.7 Verification the reviewer can repeat

```powershell
# non-interference against the pinned baseline
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q `
  tests/tools/research_support/test_off_path_noninterference.py `
  tests/tools/research_support/test_capture_seam_contract.py

# the environment's own suite against the shared-core change
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m pytest -q tests/envs/uav_service_restoration

# re-measure the efficiency contract
& 'C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe' -m tools.research_support efficiency-check `
  --config configs/uav_service_restoration/smoke_fixture.json --output temp/research_support/eff-review

# the exact shared-core diff, alone
git diff ef6cb091a..bafe782b7 -- envs/uav_service_restoration/env.py
```

---

## Part 2 — Where a reviewer should look first

Ranked by how much a defect there would cost, not by how much code it is.

1. **`envs/uav_service_restoration/env.py` — the four seams.** The only file in this commit
   that a training or evaluation run executes. Everything else is opt-in tooling that nothing
   in the repo calls yet. The specific things worth re-deriving: that `decision_index` is
   captured **before** `_step_index` advances and reused by all seams; that
   `geometry_offset_s` is `0.5 * h` under midpoint and `0.0` otherwise; that
   `on_decision_complete` runs before `self.agents = []`; that `_readonly` restores
   writability in a `finally`.
2. **`capture/profiles.py::CaptureGate.admit()` — the gate ordering.** The contract is
   profile → lane → completed-step gate → *one* clock read → circuit → wall → viewer lease →
   session → byte budget, with every gate evaluated before any array copy. A reordering here
   would silently reintroduce per-step cost on the training path without failing any
   functional test.
3. **`capture/service_restoration.py` — the `_absorb` policy.** A `live_preview` defect
   disarms capture and opens the circuit; a `record_eval` defect raises. Getting this
   backwards either kills a run for a drawing bug or silently truncates a requested
   recording.
4. **`records.py::Measured` / `Validity`.** Every "missing evidence is not zero" claim in the
   suite reduces to this type. If a consumer coerces an `unknown` to `0.0` anywhere, the
   guarantee is gone.
5. **`viewer/server.py` — containment and the two CSPs.** The report route
   `/report/<token>/<label>/<path>` carries the token into subresources by construction; the
   report frame runs under `script-src 'none'`.
6. **`plots/capability.py`** is the largest file (4,630 lines) and the *least* risky: it draws
   charts and holds no invariant that a run depends on.

The one thing I would most like challenged: **claim A rests on a hash, and the timing
evidence is weaker than the hash.** If a reviewer thinks a trajectory hash over observations,
rewards, flags, info payloads and the summary can miss a semantic change on this env, that is
the finding worth having.

---

## Part 3 — M5, native runner integration: why it was not implemented

### 3.1 What M5 asked for

`Plan_EN_v1_1.md:923`:

> Instrument actual original/process-core interfaces, selected-lane subprocess capture, skill
> and update metrics, terminal/snapshot handling. Acceptance: native route contract tests; no
> duplicate forward/solver calls; checkpoint eval if available; missing artifacts reported.

The load-bearing words are **actual** (the real training runners) and **subprocess** (the
multi-lane worker route).

### 3.2 It lands on a different surface than everything else in this commit

The suite's live route drives `envs/uav_service_restoration/env.py` plus a legacy mobile relay
demo adapter. Training does **not** use that environment. `ha_ctse_process/env_factory.py:18`:

```python
from envs.pettingzoo.relay.forced_relay import UAVForcedRelayEnv
```

and of the 113 modules under `ha_ctse_process/`, **zero** reference
`uav_service_restoration`.

So M5 requires new observation boundaries in:

| File | What M5 needs there |
|---|---|
| `envs/pettingzoo/relay/forced_relay.py` | a second set of seams — the environment training actually runs |
| `ha_ctse_process/collectors.py` | lane selection and frame extraction in `SyncEnvCollector`, `SubprocEnvCollector`, `_worker` |
| `hmasd/agent.py` | skill-assignment and update metrics — the most protected learner in the repo |
| `ha_ctse_process/env_factory.py` and its callers | thread the opt-in flag through |

That is three to four shared-core files, two of them training-main-line, against the **one**
file this commit touches and got reviewed.

### 3.3 A concrete conflict: the training snapshot pickles the whole instance dict

This is the hardest blocker and it is confirmed by reading, not inferred.
`ha_ctse_process/collectors.py:108-120`:

```python
class _TrainingStatePickler(pickle.Pickler):
    """Bypass constructor-only EzPickle reductions for live environment state."""
    def reducer_override(self, obj):
        if isinstance(obj, EzPickle):
            state = dict(obj.__dict__)
            # Pygame render handles are process-local presentation resources,
            # not training state, and cannot be serialized.
            for key in ("screen", "viewer", "game_font"):
                if key in state:
                    state[key] = None
            return (_rebuild_exact_ezpickle, (type(obj), state))
```

It serialises the **entire instance `__dict__`**, nulling exactly three known presentation
handles. Therefore:

- With capture **armed**, an observer holding a `multiprocessing.Queue` or an `mmap` sits in
  that dict and is not picklable, so `_snapshot_training_env` raises
  `RuntimeError("environment does not support exact protocol-5 training-state snapshot")`.
  Mid-run snapshotting fails **precisely when an operator is watching** — the only situation
  M5 exists for.
- If the observer were made picklable instead, a resumed worker would restore a dead copy of
  a live transport into a new process: a browser-facing handle inside a scientific snapshot,
  which boundary 10 of the execution prompt forbids outright.

Two precisions, so this is not overstated:

- **Profile `off` is unaffected.** The attribute is `None` and pickles cleanly.
- **Existing checkpoints do not break.** `payload_sha256` is validated for self-consistency
  within one snapshot (`collectors.py:172`), and `_env_spec()` (`:79`) covers only the ABI —
  dimensions, action-space type, `n_uavs`. An added attribute changes neither check.

The correct fix is to extend that exclusion list — which means **editing
`ha_ctse_process/collectors.py` itself**, the collector module, paired with a test that the
snapshot round-trip is byte-unchanged with capture off *and* still succeeds with capture
armed. That is a design task, not a flag. The comment already in that function is the
precedent: this repo has already learned that live presentation handles are not training
state, and a capture observer is the same class of object.

### 3.4 Part of M5's acceptance evidence can only be obtained from a real fit

M5 wants skill and update metrics and matched timing on the real direct and subprocess routes
(`Plan:124`).

- Skill and update metrics need the learner in the loop performing optimizer steps. **That is
  a fit.**
- Matched median/p95 regression on the real route needs a representative training workload.

Boundary 1 of the execution prompt is "default formal training budget is zero fits; do not
resume paused research", and `docs/research/RESEARCH.md` records the owner pause. The
non-interference evidence I *did* produce is measured because that route can be exercised
legitimately without a fit. The collector route cannot reach the same standard of evidence
today.

I could have written the code and left it unexercised. That would have shipped instrumentation
**claiming** non-interference on the training path with no measurement behind it — exactly
what boundaries 5 and 8 and "never report a blocked feature as complete" prohibit. Reporting
`NOT_IMPLEMENTED` is the honest option; shipping it unmeasured is the dangerous one.

### 3.5 It requires independent review, and this session's review data shows why

Boundary 2 permits narrow opt-in telemetry in shared collectors **with focused tests and
required independent review**. That review happened for the one env seam and returned
`MATERIAL_DISSENT: YES`, with six material findings in 179 lines of single-process code:

| | Finding |
|---|---|
| 1 | geometry stamped with the window start under midpoint quadrature — every frame mislabelled UAV positions by `max_speed * h / 2` (10 m on this preset) |
| 2 | `decision_step` read after the increment — geometry from interval *k*, label from *k+1* |
| 3 | documented protocol said "all optional" while calling five members unconditionally, and omitted `on_episode_reset` |
| 4 | the observer could mutate arrays the environment reads back — one of them *becomes* `self._positions_m` |
| 5 | a blanket raise was wrong for `live_preview`: a drawing defect could end a scientific run |
| 6 | `capture_substeps` claimed a resolution it never produced |

All six are fixed and pinned by `test_capture_seam_contract.py` (16 tests). The reviewer also
showed the off-path test could pass having compared nothing (a missing git history became a
skip) and that its `episode_boundaries` assertion was vacuous at 40 of 60 steps; both fixed.

Six real findings per 179 lines, on the **easy** surface. The collector version adds lane
identity, queue backpressure, worker teardown ordering, per-lane RNG and terminal-before-reset
capture — with no measurement available to catch a mistake. That is not something to land at
the end of a session.

### 3.6 A secondary fact: it would have zero users today

An already-running uninstrumented process can **never** be displayed — M5 only affects future
runs launched with the flag, and research is paused, so there are none. The specification
itself requires the documentation to say this (`Plan:953`, point 3); `README.md` does. This did
not decide the outcome, but it decided the ordering: the parts that read existing artifacts
were worth shipping first, and they shipped.

### 3.7 What already exists, so the remainder is bounded

The transport was designed for the cross-process case, not retrofitted for it:

| Piece | Location | Why it is the cross-process design |
|---|---|---|
| `MappedViewerLease` | `capture/transport.py:378` | a pre-armed `mmap`'d 8-byte double, so a worker reads the lease with no socket, file scan or RPC |
| `BoundedQueueSink` | `:242`, `cancel_join_thread` at `:307` | a stalled viewer cannot deadlock collection or block worker exit |
| lane gate | `capture/profiles.py`, `GateVerdict.LANE_NOT_SELECTED` | already the second check in `admit(lane_id, completed_steps)`, before any clock read |
| config boundary | `CaptureConfig` docstring | "choosing a camera, a viewer FPS or a lane must not change a training contract hash or a checkpoint schema" |

**What is missing is the caller.** No collector calls any of it, and there is no cross-process
test.

### 3.8 The cheapest honest next step, if this is wanted

Drive `SubprocEnvCollector` with random actions — zero optimizer steps, therefore **not a
fit** — and verify only: lane identities do not cross, the queue stays bounded, a slow
consumer cannot deadlock or block teardown, and the snapshot-exclusion design of §3.3 holds
(byte-unchanged with capture off, successful with capture armed).

That is a genuine partial M5 and it does not need the pause lifted. It still requires editing
`ha_ctse_process/collectors.py` and an independent review, which is why it was out of scope
for a visualization commit and was not slipped in before pushing. Skill/update metrics and
real-route timing wait for the owner.

---

## Part 4 — Other gaps, stated as gaps

- **Correction to the commit message.** `bafe782b7`'s body lists `failure-bundle` among
  `cli.py`'s subcommands. It is not one. `cli.py` exposes **14** subcommands (`demo`, `serve`,
  `replay`, `inspect-env`, `inspect-run`, `compare`, `report`, `record-eval`,
  `efficiency-check`, `export`, `dataset-report`, `scenario-report`, `recommend-tests`,
  `context-bundle`); `failure_bundle.write_failure_bundle()` (`failure_bundle.py:751`) is a
  **library API with no CLI entry point and no caller anywhere in the repository outside its
  tests**. It is deliberately importable from inside a failing process rather than driven from
  outside, but the consequence is that nothing currently produces a failure bundle
  automatically — its 51 tests exercise the writer, not an integration. I noticed this while
  writing this packet; the commit message is wrong and this line is the correction.
- **C01, C08–C13 are thinner than C02–C07 and C14.** They render correctly on labelled records
  but are exercised against synthetic inputs, because this checkout contains no training runs
  to read. C10 draws recorded sweep levels only; C11 marks a labelled hole and refuses any
  speedup claim when wall time is absent; C13's condition table is text only.
- **Section 7.2's "click at time *t* links to the trace time"** is not implemented. No
  trace-time vocabulary exists in the chart inputs yet.
- **`record-eval`'s full success path is unverified.** No trained process-core checkpoint
  exists here, so "loads → acts → frames written" has never executed. Everything up to and
  including the loader boundary runs against real payloads.
- **No real prepared dataset exists here**, so `dataset-report`'s prepared-cache path is
  verified only against a cache built by the repo's own writer from the committed fixture
  sample. Large-cache truncation branches are implemented but unexercised.
- **One boundary caveat, disclosed rather than hidden:** the repo's own
  `StandaloneProcessAgent.__init__` allocates `torch.optim.Adam` unconditionally.
  `record-eval` constructs no optimizer, applies no update, and runs under `torch.no_grad()`
  with `.eval()`; its manifest records `optimizer_updates: 0` and
  `optimizer_objects_constructed_here: 0` and states the constructor's behaviour. Avoiding the
  allocation would mean bypassing the repo's declared constructor — a scientific choice I did
  not take unilaterally.

---

## Part 5 — Pre-existing defects: reported, not fixed

Fixing a scientific defect under a visualization patch would hide it, so none was touched.

- [`../findings/2026-09-18-forced-relay-downlink-sinr-and-dead-backhaul-adjacency.md`](../findings/2026-09-18-forced-relay-downlink-sinr-and-dead-backhaul-adjacency.md)
  — in `UAVForcedRelayEnv`, the same UAV at the same position with the same recorded path loss
  and a *stronger* transmitter differs by ~146 dB between directions;
  `uav_bs_connections` is identically `False`, the observation feature at `forced_relay.py:3090`
  is a dead constant `0.0`, and hop-map routing can never seed its first BFS layer. The viewer
  reports both criteria with per-edge labels and **counts the disagreement** rather than
  picking one (`backhaul_route_edges_without_sinr_adjacency: 6` on the recorded trace).
- [`../findings/2026-09-18-defects-observed-while-reading-existing-code.md`](../findings/2026-09-18-defects-observed-while-reading-existing-code.md)
  — four directly confirmed, four relayed and explicitly unverified. The most consequential:
  a prepared dataset's arrays are hashed but its `metadata.json` and `splits.json` are not, so
  `is_real_activity_data` and the train/validation/test date lists can be edited after
  preparation with every integrity check still passing.

---

## Part 6 — Judgement calls I made without asking

Listed so a reviewer can overturn any of them.

1. **Committed and pushed to `main` directly.** AGENTS.md permits Claude integration only with
   no acting Root. Checked before committing: `main` level with `origin/main` (0 ahead, 0
   behind, re-fetched immediately before the push), no `.git/index.lock`, and all 34 other
   worktrees on `codex/*` branches or detached HEADs — none on `main`.
2. **Reported M5 rather than implementing it unmeasured.** Part 3.
3. **Reported pre-existing defects rather than fixing them.** Part 5.
4. **Kept the repo's optimizer-allocating constructor** instead of bypassing it for
   `record-eval`. Part 4.
5. **Did not fill any unknown policy-visible field from simulator truth**, which is why the
   inspector has a visibly empty "unknown demand (not zero)" layer rather than a complete-looking
   one (screenshot 03).
6. **Wrote this packet in English**, matching every other document under `docs/Claude_docs/`
   and the reviewer agents' working language.

---

## Verdict offered, not claimed

What I believe the evidence supports: the suite is usable now for reading existing artifacts
and recorded traces; the one shared-core change is non-interfering on the tested route by exact
trajectory identity, not by argument; and M5 is genuinely blocked rather than merely unfinished
— its acceptance evidence requires a fit, and its implementation requires editing the collector
module and the learner.

What the evidence does **not** support, and I am not claiming: that the seam's cost is
resolved (it is bounded, §1.5); that `record-eval` works end to end (§4); that seven of the
fourteen capability reports have been exercised on real runs (§4); or that any statement in
Part 5's second list has been verified by me.
