# Energy relay availability

## 2026-09-27 — B01 prospective S4 task and ordinary-reference study

Direct DM: `Codex DM (independent session)`, task
`01a0e0f9-ae03-75b2-80b3-c7a2f9adf190`, authoring shared main at
`/home/fires/hmasd-wsl`. Direction ownership is `energy_relay_availability`.
Owner authorized this new direction and five concurrent result-bearing tracks; actual
node admission may allow fewer. No App messages, other direction takeover, or new fit.

### Evidence and question

What service loss and recovery remain for ordinary legal-information control under
native S7 faster moving demand and temporary UAV failures? The first observation fixes
S4 mobility and compares its native failure regime enabled versus disabled, using a
competent ordinary pooled-legal-observation planner and a labelled extra-information
reference. This is fixed-policy exploration, not a learning claim or confirmation.

Relevant published background at `eda9fae045607dc6e59133fb1bab8f1569744e08`:
[RESEARCH sections 1–3, 7–8](../../RESEARCH.md#研究背景与共享认识) distinguish native
service from proxies, pooled legal information from independent local actors, and
information/reference gaps from optimal values. These distinctions fix the controllers
and prevent calling the central reference an achievable upper bound. The
[public report](../../../inbox/2026-09-27-energy-relay-benchmark-report-and-directions-for-codex.md)
and [benchmark c04 reading](../energy_relay_benchmark/NOTES.md#stage-1-c04-804k-transitions-rollout-134-evaluated-b02_s1_eval_c04_a01-operation-f77befe2--first-checkpoint-of-the-resumed-process)
show S2 H_local/H_central QoS about .597/.774, but c04 learner .406/.404 is still
improving. These are motivation and exposed prior evidence, not S4 comparators or a
learning plateau. Prior S7 service/risk repairs and technical failures keep their
original scope; no old operation is resumed here.

The [complete independent expansion review and Root adoption](../../archive/2026-09-27/RESEARCH-four-dm-expansion.md#four-dm-expansion-review)
cover this question/comparator/investment with `MATERIAL_DISSENT: no`. Adopt its
128-episode first observation and all restrictions: eight permanent entity slots;
availability adaptation shared by all references; no strict matched-mobility claim;
no automatic stronger faults, sweep or fit. No additional Pro pass offers a distinct
decision benefit at this unchanged selection. A material reading/continuation choice
will receive independent scientific review on the new evidence.

### Fixed comparison and exposure

- Four panels: `fault_off/H_local`, `fault_off/H_central`, `fault_on/H_local`,
  `fault_on/H_central`. 32 worlds per panel; full native episodes capped at 3,000
  transitions, retaining native early termination/truncation. 128 episodes, at most
  384,000 team environment transitions, **0 fits and 0 optimizer updates**.
- Fixed S7-S4 mobility: RPGM, user speed 8 m/s, cluster migration speed 10 m/s,
  cluster pauses 0–3 and user pauses 0–2. Eight UAVs, 30 users, one BS, two
  capacity-one charging stations, 160 Wh battery, normal native reward and guard.
  Failure-on retains native .001 eligible-UAV-step probability, 20–60 step durations,
  minimum six nonfailed UAVs. Failure-off disables only failure generation; effective
  runtime configuration must verify this despite environment preset normalization.
- Fault-off seeds **965001–965032**; fault-on seeds **966001–966032**. Each
  controller uses the same seed list within a condition. Disjoint condition panels
  are predeclared independent samples; **on-minus-off is an unpaired regime contrast**.
  Within-condition controller contrasts use the common initial seed as paired unit,
  not a claim that closed-loop physical or observation trajectories stay equal.
  Faults and mobility share environment RNG; no counterfactual trajectory replay.
- `H_local` uses pooled eight legal observations, including globally present legal
  energy records, radius-gated users, observed/cached BS and station-ring fallback.
  It is one centralized planner over those observations, not eight local actors.
  `H_central` additionally uses ground-truth user/BS coordinates every replan;
  its result is an extra-information reference, not a fair same-information baseline
  or mathematical upper bound. Both use the already selected H1 parameterization:
  six service/two relay target capacity, 100 m altitude, 30 m/s cruise, 30-step
  replanning, 300 m assignment hysteresis, production shield enter 0 / exit .05.
- Both references pass `shield_mode OR NOT legal_available` to the existing target
  assignment at each scheduled replan. Replanning remains every 30 transitions, so
  a changed availability may wait up to 29 decisions for reassignment. Motion,
  shield, action guard, rewards and charging rules remain native. This common
  reference adaptation is not a method-benefit arm. No parameters are tuned on B01.
- Worlds 957001–957032 and all contents of
  `runs/energy_relay_benchmark/b02_holdout_refs_a01` remain sealed: no reading,
  listing, tests, training or design use. The new panels are exploratory development
  exposure and can never later be called untouched confirmation worlds.

### Readings and differing outcomes

Retain each world's native J (sum and per actual step), QoS (sum and per actual
step), throughput, all native reward/risk metric components, minimum battery,
cutoff/depletion, charging/waiting/guard/shield counts, native length and terminal
type. Failed or incomplete worlds remain explicit and do not become zeros or vanish
from denominators. A batch with technical failures is incomplete; no automatic retry.

Record pre/post native failure timers/flags and legal availability/charging separately.
Failure onset at transition t affects that transition's returned QoS. Boolean
failed-to-clear recovery is not proof of usable service availability: charging or
battery cutoff may remain. Preserve timer expiry plus immediate refault explicitly;
do not silently lose a new event because pre/post failed flags both remain true.

For each onset and realized failed-to-clear recovery, record mean QoS on `[t-20,t)`
and `[t,t+20)` and post-minus-pre. Primary event-window deltas require both full
20-transition windows; retain incomplete counts and actual observed lengths without
padding. Also retain the post-recovery `[t,t+60)` mean and its full-window indicator.
Count overlapping events and retain them rather than imply isolated event causality.
Summarize complete-event deltas first within each world, then across event-bearing
worlds; report number of events, complete windows, worlds, no-event worlds and
censored worlds. These are descriptive within-episode service changes, not causal
failure effects, and events/UAVs are not additional independent sample size.

For full-episode results report all four panel means/SDs, signed on-minus-off regime
contrasts (Welch standard errors and approximate t95 intervals), central-minus-local
seed-paired contrasts within each condition (t95), and the difference between those
two controller contrasts (independent conditions). The inference unit is the world
seed under each fixed controller program, not a training seed, event or transition.
No multiplicity-adjusted confirmation or equivalence verdict. The .03 absolute QoS
scale from the prior benchmark is a practical reading aid, not a data-dependent
decision threshold or an equivalence region.

If H_local largely retains service and risk behavior, priority for another mechanism
under this exact native fault regime weakens. If both references lose service, this
establishes a current program/task cost, not impossibility of recovery. A larger
local-reference loss motivates considering information, finite search and control
program limitations as distinct explanations; the central difference alone does
not identify any one. A negligible, imprecise or heterogeneous comparison is reported
as such. Any next experiment requires a new prospective reason; occupying a slot is
not one.

### Cost, implementation scope and checks (L0)

Preferred node `wsl_4070`, configured Python/supervisor; initially 4 spawned CPU
workers × 1 Torch/BLAS/OpenMP thread each, subject to fresh actual-node admission.
No neural model or GPU allocation. Prior 8-worker reference rates suggest 20–40 min;
4 workers plus simultaneous studies may take roughly 40–80 min or longer. S4,
observer, cold import/build, serialization and contention overhead remain unmeasured.
Record actual wall and CPU time, runner/worker RSS scope, steps, and storage bytes.
Engineering/readback cost is part of this study. No outcome-based extension.

Deliverable: direction-local admitted `run_b01.py`, thin S4 config/reference adapter,
event recorder/readout and fixed batch runner under
`experiments/candidates/energy_relay_availability/`, with focused tests under its
matching tests directory. Reuse the existing native environment, production shield,
heuristic and `evaluate_world(..., observer=...)`; do not edit shared evaluator,
training, heuristic or environment code. Keep a single required compressed raw copy
per world at the declared node output, compact config/per-world/summary/manifest in
Git with hashes and byte locators for raw. Do not copy the host or full observations.

Checks cover effective fault-off/on normalization and fixed mobility, legal-available
assignment for both references, shield identity, timer expiry/refault and event
window/censoring denominators, no-event/early-ended/failed worlds, fixed 128-job plan,
sealed-world rejection, missing admission, and complete count/readout integrity.
Tests use synthetic sequences and short engineering fixtures (nonpanel seeds,
injected events); never scientific development or holdout panels. Independent
engineering review is required before the published-input native launch.
Helpers may own only assigned implementation/tests, never NOTES/shared Git mutations;
one writer per path. Scientific runs stop at this declared batch's completion or
terminal technical failure. No worker restarts or blind resends on lost observation.

### Source reconstruction before implementation

Two bounded read-only scouts reconstructed the existing code; no scientific worlds
were run. S4's profile overrides the base config at environment construction:
`envs/pettingzoo/relay/energy_aware.py:55–62,310–315`. Therefore fault-off must pass
`uav_failure_enabled=False, uav_failure_probability=0.0` as constructor kwargs,
which are applied after the profile. Check `raw_env.failure_enabled` and actual
probability, not only the configuration object's values. The default S4 constructor
remains the on arm. The wrapper can directly reuse `UAVEnergyAwareRelayEnv` and
`ParallelToArrayAdapter`; no shared repair is needed.

The native failure update decrements timers before sampling new failures, ahead of
the transition's mobility/action/service. A timer of 1 can expire then reset in that
same transition. The observer will hold a read-only reference to the raw environment,
copy its timers at attach (after reset) and each post-step callback, and record
onset (`post_timer > max(pre_timer-1,0)`), expiry (`pre_timer == 1`), immediate
refault (`pre_timer == 1 AND post_timer > 0`), and realized recovery
(`pre_failed AND NOT post_failed`). Only legal `available` reaches the controller;
raw timers and fault flags are diagnostic observations and never controller inputs.
This uses the already published observer seam, not a new shared trajectory interface.

The native `available` bit is exactly nonfailed and, when batteries are enabled,
battery above the service-cutoff threshold (`energy_aware.py:2152–2167,2250`).
Charging alone does **not** clear that bit. Charging is recorded separately and
the original shield-mode exclusion is preserved; no additional charging mask is
introduced. In the event discussion above, ongoing charging can constrain motion
or deployment but is not itself a false legal-available bit. A recovered fault may
still coincide with a battery cutoff, another fault, or unfavorable deployment.

## 2026-09-27 — B01 engineering accepted; exact inputs prepared for native launch

The bounded Implementer returned six direction-owned modules and one focused test
file; DM read the implementation and accepted the final behavior. Shared environment,
heuristic, shield, evaluator and other directions are unchanged. The independent
Engineering Reviewer (`b01_engineering_review`, separate context) reports **no
material finding remains** on the final executable content. Its substantive findings
and disposition are preserved here:

- Native launcher metadata already occupies the output directory: allow that directory
  while refusing any pre-existing scientific artifacts.
- Nullable phase/event diagnostics must not abort a valid world: retain defined/missing
  counts and label incomplete diagnostic contrasts `not_comparable`.
- Stop new submissions at the first failed/unreconciled world, cancel only unstarted
  work and drain accepted work. Use spawned `ProcessPoolExecutor`, without worker
  replacement or retry. Retain orphan files as hashed, explicitly unreconciled data.
- In incomplete execution, separate completed transitions from observed partial
  transitions, report a known lower bound and leave the actual total unknown.

All were repaired. Event rows, window lengths, missing/censoring indicators and
60-step post-recovery readings are stored in the same per-world NPZ as native
traces. The common reference mask is only shield mode plus legal unavailability;
the charging distinction is checked explicitly. Final runner SHA256:
`1864761c26a6ae5d1485360920ca020735247a94751b20f0e0a272b5c54082b1`.

Final DM check on the configured local scientific Python: **9 passed in 5.67 s**,
using pytest-managed scratch. Besides synthetic protocol/statistical/failure tests,
short seed 42/43 fixtures exercised effective S4 construction, native event timing,
the full worker's event-array serialization and reward/hash readback, and missing
admission. No development/holdout panel was evaluated. Earlier implementer/reviewer
checks were 8 passed (6.03/4.97 s); compileall also passed. Only dependency
deprecation warnings appeared. An actual OS process crash was not induced; that
failure path is checked by synthetic scheduling and source review. Setup failures
before scheduling retain the initial incomplete summary and native stderr rather
than a structured setup-error field; this does not create a scientific result.

Actual engineering/testing effort is nonzero; reading and implementation wall time
was not instrumented end-to-end. The prospective publication was `dee7ae639` and
the following source publication/launch times bound the subsequent preparation
interval. The initial read-only destination probe showed 20 CPUs, load about 1 and
13.1 GiB available; it is not launch admission. Keep the declared 4×1 CPU topology
and 40–80 minute provisional range, with contention and cold setup uncertainty.
