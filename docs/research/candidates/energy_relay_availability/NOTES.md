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

## 2026-09-27 — B01 accepted on wsl_4070; deterministic observation

Exact source `8f638f44b1d0565ef62027d5f467a113be6a730f` was committed/published
before execution. Native launch accepted at **04:27:22 UTC**, tag
`b01_s4_refs_a01`; [launch manifest](../../../../runs/energy_relay_availability/b01_s4_refs_a01/launch-manifest.json),
[accepted status](../../../../runs/energy_relay_availability/b01_s4_refs_a01/launch-status.json)
and [actual-node admission](../../../../runs/energy_relay_availability/b01_s4_refs_a01/admission-preflight.json)
retain the command, source snapshot, node and native identities. Read-only status
at 04:28:15 UTC found both recorded processes running, no exit witness and no
identity mismatch. No result reading yet; the fixed batch is not extended.

Node refresh preserved other directions' live/dirty run files. Existing Git
auto-GC warnings (`bad tree object 9e40125...`) and noninteractive zsh prompt
warnings did not prevent the fast-forward, source publication check or admission;
no shared repository repair was attempted. Immediately before launch the node had
about 7.3 GiB available and load 13 on 20 CPUs. Actual throughput remains unknown.

Same-operation observation request:
`temp/directions/energy_relay_availability/b01-wait/request.json`, protocol `launch`,
30-second interval, 20-second probe timeout, intended 1,500-second observation
window. It invokes only the node's read-only native status on the accepted manifest's
operation reference. A checkpoint rearms this same request; it does not restart or
repeat launch. Raw scientific outputs stay in the manifest's durable node output
directory; only compact acceptance metadata is collected at this boundary.

### 2026-09-27 04:56 UTC — first native observation checkpoint

Drained generation 1 / wake `3a70f106-bba0-4cd5-9202-028b0bad373c`; the sole
pending event was `CHECKPOINT` (`ebe3f0c9d7397378618fb27c`). The same accepted
runner and supervisor remained alive with matching identities, no exit witness,
and zero observer errors. Initial registration had rejected a relative `ssh`
executable; the same request was corrected to `/usr/bin/ssh` before successful
registration. No worker launch was repeated.

Read-only progress at 04:56:29: **81/128 complete worlds, 243,000 observed complete
transitions**, no failed/unreconciled/cancelled worlds and empty stderr. Off/local
and off/central each completed 32 worlds; on/local completed 17. Summary updated
10 seconds before inspection. Node available memory was 8,543,508 KiB, load about
8 on 20 CPUs. Completed-world worker wall sum was 6,645.5 s; this is not total
batch wall or concurrent node occupancy. No scientific scores were interpreted.
Rearm the same operation for another 1,500-second observation window; preserve
the fixed 128-world endpoint, exposure and all four panels.

<a id="b01-complete-reading"></a>
## 2026-09-27 — B01 complete native reading

### Terminal reconciliation and cost

Generation 2 / wake `d046962c-db0d-41b8-af9a-7617e2ac3590` returned event
`21ee8a0747339b8b956734fb`: native process exit 0, not scientific acceptance by
itself. All pending evidence was drained; acknowledgement advanced to generation
3, with no pending events or remaining observation. Observation was then stopped.
The same accepted operation was never restarted. The fresh
[native status](../../../../runs/energy_relay_availability/b01_s4_refs_a01/status-observed.json)
at 05:25:53 UTC has consistent records, valid
[exit witness](../../../../runs/energy_relay_availability/b01_s4_refs_a01/process-exit.json),
absent runner/supervisor, and exit time 05:14:41.640504 UTC.

Read [effective config](../../../../runs/energy_relay_availability/b01_s4_refs_a01/config.json),
all [128 world rows](../../../../runs/energy_relay_availability/b01_s4_refs_a01/perworld.json),
the [full summary](../../../../runs/energy_relay_availability/b01_s4_refs_a01/summary.json)
and [artifact manifest](../../../../runs/energy_relay_availability/b01_s4_refs_a01/manifest.json).
The source is `8f638f44b1d0565ef62027d5f467a113be6a730f`. All four panels have
32 complete native H3000 truncations: **384,000 actual transitions, 0 fits,
0 optimizer updates**, no failed, cancelled, unstarted, missing, unreconciled or
orphan worlds. No early termination or extension; stdout/stderr are empty.
Effective construction confirms identical S4 mobility and the intended fault
enabled/probability differences. This is fixed-controller evaluation, not learning.

Native acceptance-to-exit was **2,838.851 s (47.31 min)** on `wsl_4070`.
Measured parent run wall is 2,762.003 s (46.03 min); worker wall sum 10,884.779 s,
worker CPU sum 11,172.033 s (3.103 CPU hours), parent CPU 2.706 s. These sums
are not concurrent node wall. Parent peak RSS 477,340 KiB and maximum reported
single-worker lifetime peak 512,724 KiB are not a summed concurrent memory peak.
Setup, implementation, engineering review and scientific readback are additional
work; they were not instrumented as one end-to-end interval. The four-worker batch
fits the prospective 40–80 minute estimate, without claiming portable throughput.

### Native service, objective, risks and adverse worlds

Each cell below is a mean ± sample SD over 32 world seeds. Full native components,
guard/charging/waiting diagnostics, nullable fields and signed contrasts remain in
the linked files; no world is dropped from service or risk means.

| Panel | QoS/step | Native J sum | Return cost/step | Mean episode minimum battery |
| --- | --- | --- | --- | --- |
| fault off / H_local | .585768 ± .180540 | 1466.171 ± 711.863 | .043428 ± .056328 | .081563 ± .022894 |
| fault off / H_central | .760406 ± .060712 | 2212.964 ± 190.058 | .006279 ± .011070 | .098019 ± .008968 |
| fault on / H_local | .567520 ± .159622 | 1375.228 ± 681.600 | .049462 ± .046857 | .074769 ± .021599 |
| fault on / H_central | .745428 ± .069777 | 2153.645 ± 242.132 | .008679 ± .014837 | .093863 ± .009736 |

Predeclared world-level QoS contrasts, with approximate t95 intervals:

| Contrast | Mean | t95 interval | Statistical unit |
| --- | --- | --- | --- |
| on − off, H_local | −.018249 | [−.103431, +.066934] | two independent 32-world panels, Welch |
| on − off, H_central | −.014978 | [−.047674, +.017719] | two independent 32-world panels, Welch |
| central − local, off | +.174637 | [+.120395, +.228880] | 32 paired initial seeds |
| central − local, on | +.177908 | [+.132368, +.223449] | 32 paired initial seeds |
| controller-gap interaction, on − off | +.003271 | [−.066187, +.072730] | independent condition-level paired-gap samples |

J on−off is −90.942 [−439.224,+257.340] for local and −59.319
[−168.214,+49.577] for central. The central−local J gaps are +746.793
[+515.041,+978.545] off and +778.417 [+553.297,+1003.536] on. Return cost
on−off rises by .006034 [−.019875,+.031942] locally and .002400
[−.004152,+.008952] centrally. Mean minimum battery falls by .006794
[−.017917,+.004329] and .004156 [−.008834,+.000523], respectively.
Zero-cutoff and zero-depletion counts in all 128 episodes do not establish safety
or absence of return risk.

Central has higher QoS and J in 32/32 off worlds and 31/32 on worlds. Preserve the
exception: **966030**, central−local QoS −.006185 and J −15.496. Central return
cost is higher in 6/32 off and 7/32 on worlds despite its lower panel means.
The off/local world **965017 has exactly zero service**, J −552.136, return
cost/step .086924, minimum battery .057522 and 381.667 Wh charger input;
central at the same initial seed has QoS .653222 and J 1922.283. This single
failure is not removed or interpreted as proof of one search mechanism.
Its first-service time is genuinely null, so that timing contrast is marked
`not_comparable`; service itself remains zero, not missing. Other panels have no
zero-service worlds. Worst observed return cost and minimum battery coincide at
off/local 965006 (.224706, .025825), off/central 965005 (.042975, .077780),
on/local 966011 (.170438, .034713), and on/central 966012 (.070592, .065450).
The on/local minimum-QoS world is 966006 (.313839, J 110.041).

In off/local, off/central, on/local, on/central order, throughput is
17.5731, 22.8122, 17.0256, 22.3628 Mbps; charger input per episode is
440.868, 448.984, 419.826, 446.710 Wh; shield-mode UAV-step share is
.430094, .384654, .424033, .378629. Mean waiting UAV-ticks are
6843.47, 5494.50, 6639.84, 5132.25; normal-mode boundary share is zero
in every world. Charging-spell one-tick shares remain high (.986827, .982844,
.980723, .975571). These diagnostics describe this fixed package and do not
identify a useful timing, charging or information intervention.

### Native failure events and descriptive windows

Off panels contain no failure events and all event means remain null. Each on
controller panel has 703 onsets, 695 timer expiries, one expiry with immediate
refault, and 694 realized failed-to-clear recoveries. There are 693 full 20/20
onset windows (10 censored across eight worlds) and 689 full recovery windows
(five censored across five worlds); all 32 worlds have complete windows. Overlap
flags occur for 545 onsets and 546 recoveries. Full 60-step post-recovery windows
number 680, with 14 censored; all 32 worlds contribute.

World-first mean onset QoS deltas are −.039152 (SD .037934) local and
−.037451 (SD .033963) central; recovery deltas are +.048092 (SD .047368)
and +.042834 (SD .035052). Full post-recovery 60-step QoS means are .581352
and .750642. These are within-episode descriptions with extensive event overlap,
moving demand and changing energy/deployment. They are not isolated causal fault
costs, time-to-recovery estimates or evidence of restoration to a no-fault
counterfactual. Events/UAVs/transitions do not add independent sample size.

The complete read gives modest negative fault-regime point differences and a
large reference-package gap in both conditions. The wide local regime interval
still includes substantial harm; neither a .03-equivalence claim nor selective
fault robustness follows. Extra current positions are part of H_central's
package; the gap cannot distinguish information sufficiency, finite search,
heuristic restrictions, energy routing or learnability. The independent
scientific recommendation and DM investment disposition follow below.

### Independent raw verification and durable evidence

The bounded Verifier `b01_raw_verification` read all 128 NPZ files in place on
`hmasd-wsl-node`, using `/home/wu/.venvs/hmasd/bin/python` (3.10.21), and confirmed
the snapshot HEAD equals the accepted SHA. Every raw SHA256 and byte count matches
the manifest, directory inventory is exact, and compact config/perworld/summary
hashes and sizes match. Recomputing native J, QoS, return cost, minimum battery,
timer-derived events and windows produced **zero mismatches**; primary paired and
Welch contrasts agree within 1e-9. Scientific metrics/rewards are finite. NaNs in
undefined targets and censored diagnostic windows remain explicit, not failures.
The DM read the complete audit output. No environment or training was rerun.

Both on controllers share exactly the same retained fault traces in each of the
32 paired seeds. Each has **28,226 / 768,000 failed UAV-steps (3.67526%)**, and
**25,048 / 96,000 team-steps with a failure (26.09167%)**, at most two at once.
Off exposure is zero. This observed same-condition trace equality does not create
an off/on counterfactual or establish equal closed-loop deployment trajectories.

The sole required raw copy is
`hmasd-wsl-node:/home/wu/projects/HMASD/runs/energy_relay_availability/b01_s4_refs_a01/raw/`:
**51,621,995 apparent / 51,908,608 allocated bytes**. The full node output is
52,502,242 apparent / 52,813,824 allocated bytes. Manifest `storage_bytes`
52,470,454 counts its scientific compact files and raw, excluding the manifest
itself and native/log metadata. Manifest SHA256 is
`e9a188dfd2c5ddba02f5aa0e547bb69a7871296b7c91ce678375e72a059d4a55`.
Local compact files are published with their raw locators; no second raw copy was
made. Integrity checks cover the retained bytes and their recorded identities,
not an independently regenerated result or universal replay equivalence.

<a id="b01-scientific-review-and-b02-selection"></a>
## 2026-09-27 — Independent scientific reading; select one ordinary response comparison

Scientific Reviewer `b01_scientific_reading` used the dedicated ResearchCritic role
with `fork_turns="none"`. It reconstructed the prospective contract, original
outputs and source before reading the expansion review or DM investment discussion;
it also read the on-panel fault fields, independently of the full integrity audit.
The complete returned answer has been read. **MATERIAL_DISSENT: no**; there is no
unresolved owner-resolution item. Its substantive diagnosis and recommendation:

- Ordinary feedback/planning preserves substantial service under limited,
  automatically recovering outages; 26% of team time nevertheless has a fault.
  Broad legal-information/search, finite layout planning and energy deployment
  can account for much of the remaining variation. The approximately .18
  central-reference advantage also exists in the public S2 reference comparison
  (about .17709); stage/world/adaptation differences prevent interpreting that
  resemblance as an identified mobility effect.
- Similar event losses, regime point differences and unchanged reference gap
  weaken a demonstrated *selectively local* fault bottleneck. Wide intervals,
  risk changes, zero-service 965017 and adverse 966030 remain consequential.
  Availability recovery can restore topology without proving planning adaptation;
  charging can coincide with legal recovery. B01 does not identify information
  limits, a legal-search defect, learning difficulty, churn or an optimal value.
- A concrete rival survives: the 30-step assignment clock may delay reassignment
  for up to 29 decisions, comparable with native 20–60-step outages. Immediate
  response may help, or cause unnecessary travel/churn when a brief outage soon
  ends. B01 contains no intervention that distinguishes these outcomes.
- Recommend one fresh, paired, **local-only** comparison under native fault-on:
  preserve the ordinary 30-step schedule versus add a replan at observed legal
  availability changes while keeping scheduled replans. Count extra calls and
  compute. This tests complete utility of the response rule, including additional
  legal spatial refresh; it does not isolate availability causality.
- Do not purchase stronger faults, new fits or another unpaired sensitivity panel.
  Broad legal search has possible larger upside but no identified repair in B01;
  DM1's independent learning instances and DM3's imitation study answer distinct
  current questions. Their completion is neither a dependency nor an excuse to
  duplicate their work. End B01, keep its original sensitivity answer imprecise,
  and continue the same parent question with the narrow practical comparison.

**DM adoption.** Adopt that revised comparison, with the prospective contract
below. This changes the actionable question from estimating regime sensitivity
to the net value of one legal response rule. It preserves all B01 exposure and
adverse evidence rather than extending its 128-world batch. Current main
`0fbc5aa7010cbacbafdb91bd45569f622e02921b` was refreshed at this decision boundary;
RESEARCH sections 2/3/7/8 and the current S7 plan rule out interpreting this as
learning or taking another lead's question. The independent review is adequate
for this decision; another Pro pass offers no distinct unresolved expertise or
disagreement to purchase now.

An illustrative post-result precision calculation using observed local variances
would require about 248 worlds **per regime** for a normal-approximation .03
half-width: 496 local-only episodes, 1.488M transitions, about 178 runner minutes
at B01's rate. This is neither a threshold nor a guarantee nor a selected study.
A two-arm intervention can answer a more actionable question at lower evaluation
cost. A positive result is not owed; faster reassignment without complete utility
will not be promoted, and a negative/uncertain result will not trigger sweeps.

<a id="b02-prospective"></a>
## 2026-09-27 — B02 prospective availability-triggered ordinary replanning (L0)

### Question, prediction and fixed exposure

Does reacting to observed legal availability changes improve complete S4 service
and native J enough to retain an ordinary comparator change? Both arms are the
B01 pooled-legal-observation H1 planner and production shield, under **native
fault-on only**, with identical mobility, energy, reward, H1 parameters, legal
inputs and continuous action law. There is no privileged-coordinate arm or actor,
critic, optimizer, training schedule, normalization or checkpoint selection.

- `clock30`: original availability-aware H_local, regular replans at decision
  indices 0,30,60,... .
- `availability_event`: the same schedule, plus a replan when the current legal
  eight-UAV `available` vector differs from the previous decision's vector.
  Simultaneous changes cause one replan; coincidence with a scheduled replan
  causes one call. Extra calls never move the regular clock. Initial reset has
  the scheduled replan only. Shield-mode changes alone are not a new trigger.
- A fault is realized inside transition t; the candidate can first react using
  the returned legal observation at decision t+1, not before. Raw timers and
  fault flags remain observer-only and never feed the planner. Recovery changes
  are treated symmetrically; same-step expiry/refault with unchanged availability
  does not trigger. All extra planning reads the same legally available spatial
  observation fields. Its extra refresh and computation belong to the package.
- Fresh paired worlds **969001–969032**, both arms per seed, full native H3000:
  **64 episodes, at most 192,000 actual transitions, 0 fits/optimizer updates**.
  No B01 world reuse. The selected seeds do not occur in current public S7 direction
  declarations checked before selection. Sealed 957001–957032 and the protected
  holdout remain forbidden. This is new exploratory exposure, not confirmation.
- Fixed endpoint is all 64 planned worlds or terminal technical failure. No
  outcome-based extension, reordering, replacement, retry, tuning, stronger faults
  or learning. Use common initial seeds as paired units; verify and report actual
  fault-trace agreement without assuming identical closed-loop physical histories.

Intermediate prediction: shorter observed-availability-change to executed-plan
delay, specifically zero additional decision lag for the event rule versus up to
29 for clock30. Native conjecture: less stale assignment increases mean complete
QoS and J. Competing prediction: immediate redistribution produces churn/travel
or risk that offsets short-lived service recovery, leaving complete utility flat
or worse. Faster planning alone is not success.

### Native readout and outcome implications

Primary readings are paired event−clock complete native J and QoS, with all32
world values, mean/SD/SE and approximate t31 95% intervals; retain every loss and
zero-service world. Read return constraint cost (raw and capped), cutoff/depletion,
minimum battery, throughput, charging/waiting/guard/shield, episode length and
terminal type beside them. No multiplicity-adjusted confirmation or equivalence
claim. Null diagnostics retain their denominators. Technical incompleteness stays
incomplete and is not an adverse effect.

Record per-decision legal availability change, regular/extra/executed replan
flags, targets, plan-call count and measured planning CPU/wall. For every observed
change record lag to the next executed plan, marking changes without a subsequent
decision/plan as right-censored rather than assigning zero; aggregate world-first.
Retain the B01 native timer/event arrays and pre20/post20/recovery60 diagnostic
windows, including censoring and overlap. Any last-transition change without a
following decision is explicitly beyond the response opportunity. Targets/plan
counts check that the intervention actually activates; they are not new native
performance endpoints or independent samples.

Higher complete QoS and J with acceptable recorded risk and adverse-world behavior
can justify retaining this ordinary rule as an exploratory comparator improvement,
without a learning or isolated timing mechanism claim. Shorter lag/local recovery
without complete gain does not justify promotion. Increased return cost or lower
complete utility favors clock30. Small, heterogeneous or imprecise results are
reported as such and end this clock intervention's current investment unless a
specific new scientific decision warrants further work; they do not establish
equivalence or settle the broader mobile-demand service question.

### Implementation, cost and checks

Preferred node remains `wsl_4070`, initially four spawned workers with one numeric
thread each, subject to fresh actual-node admission. B01's rate projects about
23 runner minutes; budget expectation is **25–50 minutes** with added planning,
setup and contention, not a scientific stopping rule. At most roughly two extra
availability-change opportunities per outage; record actual extra calls, worker
CPU, wall/RSS and storage. Engineering and readback cost is additional and actual.
Preserve one canonical compressed raw copy per world and compact Git readings.

Implementer owns only direction-local B02 modules/entrypoint and matching tests;
minimal extraction or a default-preserving worker callback in the B01 scheduler
is allowed if needed for reuse. Keep B01 behavior and inputs unchanged at its
pinned source; do not edit shared environment, H1 planner, shield or evaluator.
No NOTES/shared-index/Git mutation, launch, scientific choice or child delegation
belongs to the Implementer. Use existing failure stop/drain/cancel and partial/orphan
accounting semantics; admission precedes scientific imports and output creation.

Checks cover clock30 identity against B01 on short nonpanel engineering fixtures,
observed availability changes and regular-clock preservation, coincident triggers,
reset/refault/last-step censoring, no trigger from charging/shield alone, legal-only
information, meaningful native worker serialization, paired units/nullable metrics,
fixed64/sealed-seed/admission guards and no replacement after terminal failure.
Use synthetic masks and nonpanel seeds; no development result worlds in tests.
Independent Engineering Reviewer will check timing/information/RNG/trace/failure
safety before DM acceptance, exact input publication and native launch.

### B01 boundary cleanup and publication

After the complete raw audit, local and remote config/perworld/summary/manifest
SHA256 values were compared directly and match. Native workers were absent, all
observer events consumed, generation3 stopped, and no helper retained a source
snapshot consumer. The maintained exact-target snapshot collector first refused
the unprivileged read-only scan of `/proc/660/cwd`; its documented
`--sudo-process-scan` performed only that read-only scan via existing passwordless
sudo. Preview then passed all source/claim/output/ref/process checks. Apply was
serialized under the node's shared Git writer lock and rechecked its own admission
lock. No source or output bypass, backup or duplicate retention package was used.

Deleted the B01 source snapshot
`/home/wu/projects/HMASD/.git/hmasd-launch-sources/7c9d27a9439e412e9c7973eb599d07ba`:
**796,528,640 → 0 allocated bytes**, absence verified. Retained the terminal
claim, native manifest/status/exit witness and the unique canonical output.
The [frozen B01 source](https://github.com/CartmanFatass/My-paper-code/tree/8f638f44b1d0565ef62027d5f467a113be6a730f/experiments/candidates/energy_relay_availability)
is reachable from published main. Local completed audit/request scratch
`temp/directions/energy_relay_availability/{b01-verification,b01-wait}` and
redundant `launch-command.stdout`, `launch-command.stderr`, empty local stdout
and stderr were deleted: another **49,152 → 0 allocated bytes**, all exact targets
absent. Total target allocation released is **796,577,792 bytes** across the
two hosts, separately from Git object storage and unrelated host disk activity.

Actual retained material: compact run evidence/NOTES in main, one ~51.62 MB raw
copy at the node locator above, and source/tests needed by the selected B02
continuation. No cleanup blocker or B01 worker/observer remains. This cleanup
finishes B01's accepted operation; it does not stop or restart B02 preparation.

## 2026-09-27 — B02 implementation and independent engineering acceptance

The Implementer returned the direction-owned `b02_controller.py`, `b02_runner.py`,
`b02_readout.py`, `run_b02.py` and `test_b02.py`. The sole existing executable
change is an optional top-level worker callback in the B01 bounded scheduler;
its default resolves to the original worker at call time. DM read all new code,
the scheduler diff and the checks. No shared environment, heuristic, shield or
evaluator was edited. The B01 frozen source and completed evidence remain intact.

Independent Engineering Reviewer `b01_engineering_review` reports **no material
finding remains; acceptable for DM acceptance**. It verified legal-only triggers,
one-decision response timing, fixed regular clock, simultaneous/coincident/reset
semantics, charging/shield distinctions, terminal censoring, native trace and
fault-hash retention, no new RNG consumption, paired readout, admission ordering
and stop/drain/partial/orphan accounting. Implementer checks were **16 passed in
8.13 s**; reviewer independently obtained **16 passed in 8.12 s**, with short
nonpanel 42/43 native identity/worker serialization fixtures and normal scratch
cleanup. Compile and whitespace checks passed. No scientific worlds were run.
No extra unchanged test round was required for acceptance.

Accepted SHA256 values: B02 controller
`f86681175f86866f06f915bfe375e1c4a751fd57bebb81f2ea7d30b4bfc42752`,
B02 runner `2275830fa6a6e90ff111ea4821b6ba89e5394c23396556badee3a2ebbaa0a7c2`,
readout `ddb9511e0a1f20fb6b2b4ebb3c5f41ac8775b99ea625cdd15ab0f84b77238189`,
entrypoint `4903b36cd033dd187fd21ee8f7dfbbee720f1d787ee2fda973423caf8c1a44fe`,
shared direction scheduler module
`a6fffd611d86750d7b66f98318064764762bd2dcfadb0baa8dcfc839cb252431`.
Actual H3000 execution and an OS worker crash were not engineering-tested;
setup failures before scheduling retain the initial incomplete summary and native
stderr rather than a structured setup-error field. These are reported limits,
not scientific acceptance or a retry authorization.

A read-only preparation check found the remote canonical main still at B01's
source. Fetch succeeded, but fast-forward refused because another direction's
live `runs/energy_relay_benchmark/b02_s1_set_a01r/summary.json` would be overwritten.
That file and the canonical branch/index were preserved, with no stash/reset or
foreign-output staging. The maintained launch method permits unrelated prose to
differ while the operative pause/direction/state/lead agree. Direct parsing
confirmed the canonical and fetched published operative controls match and the
compute configuration is unchanged. New execution will use the exact newly
published source snapshot, with fresh published-control and actual-node resource
checks by native admission; no stale-policy bypass is introduced. The known Git
auto-GC warning and zsh prompt diagnostics remain outside this direction's repair
scope. Use configured `agent-task` to invoke the native launcher; its outer command
completion is distinct from the scientific operation's native acceptance/exit.

### Correction before any B02 launch

The immediately preceding paragraph prematurely said that direct remote parsing
had confirmed operative-control equality. That read-only SSH call instead timed
out after 25 seconds before returning its comparison. The source-code reading
establishes which fields admission checks, but it does **not** establish the
current node observation. Treat that comparison as unverified until a completed
read below. No B02 scientific launch or supervisor run has been submitted. The
published implementation `c2258557ef2b7f076820850659f8e837e7e31e06` and its tests
remain valid; this correction changes no exposure or protocol.

The subsequent completed read through the configured `zsh -lic` network shell
returned exit0: both canonical and fetched published controls are `Owner pause:
lifted`, direction `energy_relay_availability`, state `exploring`, lead
`Codex DM (independent session)`; compute bytes also match. Plain SSH probes had
timed out without usable control evidence (25 s and 35 s). The successful network
shell read and the existing fetch auto-GC warnings are recorded separately; no
scientific worker was started by these probes. Use that configured shell for
published Git reads and the single upcoming native launch invocation. Native
admission still rechecks the live published head and actual-node resources.

## 2026-09-27 — B02 accepted on wsl_4070; same-handle observation

Exact source `b4c7b153775222414375da4fda27b25e3c5363a8` was published and fetched
before the single configured-supervisor invocation. Native launch accepted at
**05:57:37.997119 UTC**, tag `b02_event_replan_a01`. The outer `agent-task`
invocation `era-b02-event-a01` finished with exit0 after submitting the launcher;
that outer completion is not the experiment's completion. The separate native
runner and supervisor were both observed running with matching identities and
consistent records. No exit witness exists yet, and no scientific result has
been read or accepted.

The [launch manifest](../../../../runs/energy_relay_availability/b02_event_replan_a01/launch-manifest.json),
[native launch status](../../../../runs/energy_relay_availability/b02_event_replan_a01/launch-status.json),
[observed running status](../../../../runs/energy_relay_availability/b02_event_replan_a01/status-observed.json)
and [actual-node preflight](../../../../runs/energy_relay_availability/b02_event_replan_a01/admission-preflight.json)
retain the exact source, argv, output, operation reference, source snapshot and
native identities. Fresh admission measured 9,930,584,064 available bytes against
the 4,294,967,296-byte floor, passed with no failure reasons, and verified the
published control head at the source SHA. The unrelated dirty canonical result
was preserved; no fast-forward, stash/reset or policy substitution was needed.

Deterministic observation request:
`temp/directions/energy_relay_availability/b02-wait/request.json`, job
`launch-b02-event-replan-a01`, protocol `launch`, interval30 s, timeout20 s,
intended window1500 s. It reads only the accepted native operation's status via
absolute `/usr/bin/ssh`; checkpoints rearm that same handle. The 64-world endpoint,
192k maximum transitions and zero-fit protocol remain fixed. Terminal failure
will retain incomplete evidence without an automatic replacement or retry.
