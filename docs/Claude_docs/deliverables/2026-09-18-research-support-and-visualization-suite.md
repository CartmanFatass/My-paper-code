# Research support and UAV/UE visualization suite — delivery record

**Date:** 2026-09-18
**Specification:** `Research_Support_and_UAV_Visualization_Claude_Package_EN_v1_1.zip` (v1.1),
grounded at commit `ef6cb091a621bf04a734878346dbd8860a1ebe59`.
**Scope:** implementation of the suite, not a research result. No direction was advanced and
the owner pause was not touched.

```
FORMAL_TRAINING_FITS_STARTED: 0
OPTIMIZER_UPDATES_PERFORMED:  0
HYPERPARAMETER_SEARCHES_RUN:  0
CHECKPOINTS_EXECUTED:         0   (record-eval is implemented; no checkpoint exists here to run)
RESEARCH_DIRECTIONS_TOUCHED:  0
```

## Completion status

| Deliverable | Status | Evidence |
|---|---|---|
| Live UAV/UE/base-station viewer, 2-D | `VERIFIED` | Screens 01–03, 07; browser-driven |
| Live viewer, 3-D | `VERIFIED` | Screen 04 |
| Genuinely mobile legacy UE scenario | `VERIFIED` | Screen 07; ground max displacement 1098.4 m over one episode |
| Service-restoration scene | `VERIFIED` | Screens 01–03, 05 |
| Algorithm capability reports C01–C14 | `PARTIAL` | 7 of 14 fully implemented and directly tested; 7 thinner (see below) |
| Run inspector | `VERIFIED` | `inspect-run`, 3 readers, 40 tests |
| Comparison checker | `VERIFIED` | Screen 05; world identity verified before alignment |
| Effective-configuration / environment inspector | `VERIFIED` | `inspect-env --probe`: 29 fields promoted to `verified_runtime` |
| Offline replay | `VERIFIED` | Screens 01–07 are all replay of recorded traces |
| Event seeking | `VERIFIED` | Event timeline, `full_site_failure @120s`, recorded time not reconstructed |
| Synchronised two-policy comparison | `VERIFIED` | Screen 05, aligned by simulated time |
| Portable exports | `VERIFIED` | html 3.7 MB, png, json 5.9 MB, gif 1.5 MB; mp4 refuses with an actionable message |
| Failure bundles | `VERIFIED` | 51 tests |
| Change-aware test recommendation | `VERIFIED` | 51 tests |
| English Claude context bundles | `VERIFIED` | generated locally, nothing is sent anywhere |
| Data / scenario diagnostics | `VERIFIED` | `dataset-report`, `scenario-report`, 48 tests |
| Efficiency contract (Section 0.2) | `VERIFIED` | measured; see below |
| Off-path non-interference | `VERIFIED` | trajectory-identical against the pre-change revision |
| Native runner integration (M5) | `NOT_IMPLEMENTED` | see "Not delivered" |

**Tests:** `624 passed, 2 skipped` in `tests/tools/research_support/`
(`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest tests/tools/research_support -q`).
The 2 skips are deliberate encoder-conditional cases: Pillow is installed so the GIF-refusal
case is skipped; imageio is absent so the MP4-success case is skipped.

## Efficiency contract

`python -m tools.research_support efficiency-check --config configs/uav_service_restoration/smoke_fixture.json`

| condition | median ms/decision | p95 | max | frames | admitted/attempts |
|---|---|---|---|---|---|
| `pre_change` (env.py at `ef6cb091a`) | 37.6677 | 75.0767 | 82.8099 | 0 | 0/0 |
| `off` (what every training run does) | 36.8572 | 71.1185 | 78.1354 | 0 | 0/0 |
| `preview_no_viewer` | 37.0768 | 72.5066 | 78.0154 | **0** | **0/41** |
| `preview_with_viewer` (rate gates opened fully) | 47.6615 | 83.8258 | 95.3893 | 38 | 38/41 |
| `stalled_consumer` | 43.5324 | 80.5373 | 97.8420 | 34 | 34/41 |
| `record_eval` | 42.2266 | 87.2953 | 88.2493 | 41 | 41/41 |

```
EFFICIENCY_CONTRACT_IMPLEMENTED
OFF_PATH_VERIFIED
LOW_RATE_PREVIEW_MEASURED
ARMED_CAPTURE_NON_INTERFERING
```

`ARMED_CAPTURE_NON_INTERFERING` is the strongest of the four and the one the timings cannot
give: **every armed condition** — preview with no viewer, preview with a viewer, a stalled
consumer, and a full evaluation recording — reproduced the capture-off trajectory hash
exactly. Capture actually running, copying arrays, building frames and writing a trace
changes no scientific quantity.

Read these honestly:

- `off` measured **−2.15%** against the pre-change revision — nominally *faster*, which means
  the seam's cost is below this measurement's noise floor. This **bounds** the cost; it does
  not resolve it. The identity claim rests on the trajectory hash, not on the timing.
- `preview_with_viewer` is deliberately un-rate-limited, so +29% is the **upper bound** on
  preview cost, not the shipped behaviour. The default gates one frame per second.
- `stalled_consumer` is *cheaper* than a draining consumer, which is the point: the producer
  drops frames rather than waiting on one.
- Timings pool every repeat; frame and gate counters are the final repeat only.

## The one shared-core change

`envs/uav_service_restoration/env.py`, +179 lines, 0 deletions: `set_capture_observer()`, a
`capture_observer` property, `capture_capabilities()`, a `_readonly` guard, and four observer
call sites. `capture_observer` is `None` in the constructor and on every existing path.

`tests/tools/research_support/test_off_path_noninterference.py` (6 tests) reads the
pre-change `env.py` out of git at the pinned commit, executes it inside the real package, and
compares a **full 60-decision-step episode**, terminal transition included:

- trajectory SHA-256 over observations, rewards, termination/truncation flags, info payloads
  and the episode summary, hashed over **raw float bits** — identical
- `_evaluate_service` call count: **600 = 600** (no display-driven extra solve)
- episode boundary at step **60** on both sides — the terminal ordering is inside the compared
  trajectory, not outside it
- RNG state over all **5** named streams in `env._rngs` — identical
- attaching an observer whose gate is profile `off` also leaves the trajectory identical

`tests/tools/research_support/test_capture_seam_contract.py` (16 tests) covers the seam
contract itself: geometry time against true position, one decision index across all seams, the
documented protocol, array-mutation refusal, and the per-profile exception policy.

The pin is a commit, not `HEAD`, and the loader refuses a baseline that already contains the
seam — otherwise this test would silently become "the new code equals itself" after commit.
A companion test fails if the RNG comparison ever finds zero streams.

The legacy relay route required **no shared-core edit**: its observer reads what the adapter
already builds.

## Viewer security, verified against the running server

```
api, no token                                403  missing or invalid session token
api, wrong token                             403  missing or invalid session token
api, correct token in query                  200
api, correct token in header                 200
api, correct token, foreign Origin           403  refused Origin 'http://evil.example'
api, correct token, loopback Origin          200
plain traversal                              403  refused path outside the approved root
percent-encoded traversal                    403  refused path outside the approved root
double-encoded traversal                     403  refused path outside the approved root
backslash traversal                          403  refused path outside the approved root
POST                                         405  this viewer is read-only
DELETE                                       405  this viewer is read-only
absolute/protocol-relative URLs in page+assets  0
```

The browser confirmed the same: **7 network requests, all to `127.0.0.1:8791`, zero external.**
The token never appears in a URL the server generates and is redacted from its access log.

## Defects found and fixed during verification

Found by the test-writing pass, in code written for this suite:

1. `CaptureGate.charge()` broke the counter identity — an oversized frame counted a refusal
   without un-counting the admission, so `admitted + refusals > attempts`.
2. A clock whose origin is exactly `0.0` permanently disabled the output byte budget (`0.0`
   doubled as the "not armed" sentinel). Latent under `time.monotonic()`, live under any
   injected clock.
3. A trace whose **first** line was truncated reported status `open` instead of `incomplete`.
4. `CompositeSink.offer` let a raising child escape into the producer and skip its siblings.
5. On Windows, a viewer polling `latest.json` made 35 of 41 `os.replace` calls fail with
   `PermissionError` — atomicity held (0 partial frames) but a healthy preview looked broken
   and could have tripped the circuit breaker. Now retried with a bounded backoff and counted
   separately as `replace_contended`.
6. Percent-encoded traversal returned 404 rather than 403 (containment was never breached).
7. `export_mp4` was the only exporter that did not create its output parent.
8. The SVG favicon I had added contained `http://www.w3.org/2000/svg` — never fetched, but it
   defeats any plain "no external URL" check. Replaced with a generated PNG data URI.

Found by browser verification, in the viewer:

9. The canvas legend was painted over the scene it was explaining. Moved to the DOM.
10. Entity labels overprinted each other and were buried under markers drawn later. Now a
    deferred layer with greedy placement, halos and leader lines.
11. **A site's status label could be placed 160 px from its own marker, next to a different
    site** — it read as the wrong site's status. Placement is now clamped and a displaced
    label draws a leader back to its entity.
12. A hidden scene canvas kept showing its last painted frame beside the active one — a stale
    view with no staleness marker. (`display: block` outranked `[hidden]`.)
13. The comparison opened with the right pane on its **last** frame while the left sat at its
    first, under a banner claiming the panes were synchronised by simulated time.
14. The "policy-visible" inspector listed simulator-truth rows under that heading. Truth-sourced
    rows now sit under an explicit "simulator truth — not read from the observation view" block.
15. The 1200 px-wide identity strip forced a horizontal scrollbar on every layout below that
    width. Verified clean at 1920, 1440, 1024 and 700 px.
16. The client could only ever load the first served trace. Added trace pickers.
17. `[hidden]` was overridden by an explicit `display` value in two places — a hidden scene
    canvas kept painting its last frame beside the live one, and a hidden panel kept its space
    so the capability report was pushed 1800 px off the bottom of the page. One global rule now
    makes `[hidden]` authoritative.
18. The capability report was a link to a file whose relative `figures/…` references could not
    resolve through a query-string route, so every figure would have 404'd. Reports are now
    served under `/report/<token>/<label>/<path>`, which carries the token into each
    subresource by construction, and the report renders inline in the viewer (14 figures, none
    broken) under its own tighter policy: `script-src 'none'`, framed only by this viewer.
19. **Two viewer processes could bind the same port and both answer.** `ThreadingHTTPServer`
    sets `SO_REUSEADDR`, which on Windows lets a second server hijack a live port — so an
    operator could restart the viewer and silently keep reading the *old* server's traces.
    Binding a busy port now fails.

## Independent review of the shared-core change

An independent reviewer was given the diff and a fixed acceptance contract (A–H). It returned
**MATERIAL_DISSENT: YES** on the first version. Its findings were real; all of them are fixed,
and each now has a regression test in
`tests/tools/research_support/test_capture_seam_contract.py` (16 tests).

| | Claim | First verdict | Now |
|---|---|---|---|
| A | Off-path identity | ESTABLISHED | ESTABLISHED, and the rollout now reaches the terminal step |
| B | No recomputation for display | ESTABLISHED | ESTABLISHED |
| C | Capture-time correctness | **VIOLATED** | fixed and measured |
| D | Aliasing / copy obligation | ASSERTED-BUT-UNPROVEN | enforced at runtime |
| E | Terminal ordering | ESTABLISHED but untested | tested |
| F | Exception policy | wrong for a live preview | split by profile |
| G | No privileged leakage into the policy | ESTABLISHED | ESTABLISHED |
| H | Checkpoint / state compatibility | ESTABLISHED | ESTABLISHED |

What was wrong, and what changed:

1. **The displayed geometry was stamped with a time it did not hold at.** Under the default
   midpoint quadrature the solve uses the geometry at the *middle* of its substep, but the
   seam passed `time_s=sub_start` and the consumer mapped that straight to
   `geometry_time_s`. Every emitted frame mislabelled UAV positions by `max_speed * h / 2`
   — 10 m on this preset. The seam now passes `window_start_s` and `geometry_time_s` as two
   separate values, computed in `env.py` because only that method knows the quadrature rule.
   Verified: with a constant full-speed action, `geometry_time_s = 10.5` and the shown
   `x = 1110.0` is exactly the position at *t* = 10.5.
2. **`decision_step` meant two different things.** `on_decision_complete` read
   `self._step_index` *after* it had been incremented, so one frame took its geometry from
   interval *k* and its label from *k+1*. All three seams now use one index captured before
   the increment.
3. **The documented observer protocol was wrong.** It called five members unconditionally
   while describing four of them as "all optional" and omitting `on_episode_reset` entirely;
   an observer written to that docstring raised `AttributeError` inside `reset()`.
4. **An observer could silently change a reward.** The arrays handed over are read back by
   the environment — one of them *becomes* `self._positions_m`. The copy obligation was a
   docstring. They are now read-only for the duration of the call, restored afterwards even
   if the observer raises, so a mutating observer fails loudly.
5. **A display defect could end a scientific run.** Now split by profile: a `live_preview`
   defect disarms the capture, records the reason and opens the circuit while the run
   continues; a `record_eval` defect still raises, because there the recording *is* the
   deliverable.
6. **`capture_substeps` claimed a resolution it never produced.** It was labelled
   `every_substep_of_an_admitted_interval` while emitting one frame per interval. The labels
   are now `first_substep_…` and `last_substep_of_an_admitted_decision_interval`, which is
   what the flag actually selects; a frame carries interval totals that do not exist until
   the interval ends, so a per-substep frame is not assemblable.

The reviewer also showed that the off-path test could pass while comparing nothing (a missing
git history became a skip) and that its `episode_boundaries` assertion was vacuous because the
rollout stopped at 40 of 60 decision steps. Both are fixed: the rollout runs to the horizon,
and a skip is refused whenever git is actually available.

Its remaining caveat stands and is reproduced here: the efficiency timings **bound** the
off-path cost rather than resolving it, since `off` measured nominally faster than
`pre_change`. The evidence for claim A is the exact trajectory hash, not the timing.

## Independent scientific defect, reported not fixed

`docs/Claude_docs/findings/2026-09-18-forced-relay-downlink-sinr-and-dead-backhaul-adjacency.md`.

In `UAVForcedRelayEnv`, for the same UAV at the same position with the same recorded path loss
(~100 dB) and a **stronger** transmitter (BS 30 dBm vs UAV 23 dBm), the two directions differ
by ~146 dB:

```
base_path_loss   (dB)  [ 99.07 100.96 101.07 100.51 102.32  99.01]
uav_to_base_sinr (dB)  [ 17.90  16.01  15.89  16.45  14.64  17.96]
base_to_uav_sinr (dB)  [-128.60 -130.49 -130.60 -130.04 -131.85 -128.54]
```

Consequences: `uav_bs_connections` is identically `False`; the observation feature at
`forced_relay.py:3090` is a dead constant `0.0`; hop-map routing can never seed its first BFS
layer; and `_find_widest_path_to_ground_bs` uses only the uplink, so routes exist while
adjacency says none. **Not fixed under a visualization patch.** The viewer reports both
criteria with per-edge labels and counts the disagreement rather than picking one
(`backhaul_route_edges_without_sinr_adjacency: 6` on the recorded trace).

Four more defects in existing code were found while reading it, confirmed directly, and are
recorded in `docs/Claude_docs/findings/2026-09-18-defects-observed-while-reading-existing-code.md`
— also **not** fixed here. The most consequential: a prepared dataset's arrays are hashed but
its `metadata.json` and `splits.json` are not, so `is_real_activity_data` and the
train/validation/test date lists can be edited after preparation with every integrity check
still passing.

The environment's own existing suite was run against the shared-core change:
`255 passed` in `tests/envs/uav_service_restoration/`.

## Not delivered

- **M5, native runner integration.** An opt-in capture flag threaded through the
  `ha_ctse_process` collectors with subprocess-lane capture was not implemented. The
  transport supports it (`SharedViewerLease`, `BoundedQueueSink` with `cancel_join_thread`)
  but no collector calls it and no cross-process test exercises it.
- **C01, C08–C13 are thinner than C02–C07 and C14.** They render correctly on labelled
  records but are exercised against synthetic inputs, because this checkout contains no
  training runs to read. C10 draws recorded sweep levels only; C11 marks a labelled hole and
  refuses any speedup claim when wall time is absent; C13's condition table is text only.
- **Section 7.2's "click at time *t* links to the trace time"** in the figure contract. No
  trace-time vocabulary exists in the chart inputs yet.
- **`record-eval`'s full success path is unverified.** There is no trained process-core
  checkpoint in this checkout, so "loads → acts → frames written" has never executed.
  Everything up to and including the loader boundary runs against real payloads.
- **One boundary caveat:** the repo's own agent constructor (`StandaloneProcessAgent.__init__`)
  allocates `torch.optim.Adam` unconditionally. `record-eval` constructs no optimizer, applies
  no update, and runs under `torch.no_grad()` with `.eval()`; its manifest records
  `optimizer_updates: 0`, `optimizer_objects_constructed_here: 0` and states the constructor's
  behaviour rather than hiding it. Avoiding the allocation would mean bypassing the repo's
  declared constructor — a scientific choice not taken here.
- **No real prepared dataset exists in this checkout**, so `dataset-report`'s prepared-cache
  path is verified only against a cache built by the repo's own writer from the committed
  fixture sample. Large-cache truncation branches are implemented but unexercised.

## Screenshots

`docs/Claude_docs/deliverables/research_support_screens/`

| file | what it shows |
|---|---|
| `01-restored-service-2d.png` | all nine aggregate demand points served through the relay chain, `site_east` still down |
| `02-site-outage-unserved-demand.png` | sim 130 s: three cells unserved, `unmet_mbit_interval` spiking at the recorded failure |
| `03-policy-visible-unknowns.png` | reset frame in policy-visible mode: hatched "unknown demand (not zero)", `radio ? / core ?` |
| `04-3d-inspection-display-frozen.png` | 3-D view with `DISPLAY FROZEN — producer continues` |
| `05-two-policy-comparison-same-world.png` | relay vs static at the same simulated time, same verified world |
| `06-capability-report-with-named-holes.png` | the capability report rendered in the viewer, naming its ten missing panels and refusing to rank or attribute cause |
| `07-legacy-mobile-ues-with-trails.png` | legacy relay route: 24 individual mobile UEs, aggregate-demand layer correctly greyed as `not recorded` |
