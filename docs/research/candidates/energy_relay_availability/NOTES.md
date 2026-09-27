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

<a id="b02-complete-reading"></a>
## 2026-09-27 — B02 complete native reading

### Terminal evidence, fixed exposure and actual cost

The accepted operation ended at **06:20:29.397770 UTC**, with a valid native
exit0 witness, absent recorded runner/supervisor identities and no consistency
mismatch. The terminal observation was read at generation5 and acknowledged with
its returned wake/event identities into generation6; both recorded jobs are
terminal, and no worker was restarted. No Pro operation is pending. The earlier
attempt to register B02 observation was refused because the completed B01 observer
was stopped; the supported empty-state rearm and new-job registration resolved
only that observer state. The accepted B02 scientific operation was unchanged.

Read the [effective configuration](../../../../runs/energy_relay_availability/b02_event_replan_a01/config.json),
[all 64 world rows](../../../../runs/energy_relay_availability/b02_event_replan_a01/perworld.json),
[summary and all 32 paired differences](../../../../runs/energy_relay_availability/b02_event_replan_a01/summary.json),
[manifest](../../../../runs/energy_relay_availability/b02_event_replan_a01/manifest.json),
[terminal native status](../../../../runs/energy_relay_availability/b02_event_replan_a01/status-terminal.json)
and [exit witness](../../../../runs/energy_relay_availability/b02_event_replan_a01/process-exit.json).
They report all 64 declared episodes completed at H3000, all horizon-truncated,
**192,000 transitions, 0 fits and 0 optimizer updates**. There are no failed,
missing, cancelled, unstarted, unreconciled, partial or orphan jobs. The actual
S4/8-UAV/30-user/fault/shield/controller settings match the prospective record.
Technical exit and compact completeness are distinct from the raw verification
and scientific reading recorded below.

Exact source is `b4c7b153775222414375da4fda27b25e3c5363a8`. Runner wall was
**1,326.454021 s (22.11 min)**; native acceptance-to-exit was **1,371.400651 s
(22.86 min)**. Four workers used one numeric thread each. Worker wall summed to
5,209.240705 s and worker CPU to 5,377.172848 s (1.494 CPU h); parent CPU was
0.772327 s. Parent peak RSS was 479,076 KiB; maximum single-worker peak was 518,940
KiB. These peaks are not a simultaneous node total. Engineering, publication and
readback wall were not comprehensively instrumented and are additional, not zero.

### Complete service, objective and risk

World seed is the paired unit (32 fresh pairs). Values below are mean ± sample SD;
the event-minus-clock intervals are the declared approximate t31 95% intervals.
No training population, multiplicity-adjusted confirmation, equivalence or general
method-superiority claim follows from this fixed-policy development comparison.

| Native reading | clock30 | availability_event | Paired event−clock mean [t95] |
| --- | ---: | ---: | ---: |
| QoS/step | .598010520 ± .136700250 | .584838284 ± .139887399 | −.013172237 [−.048950941,+.022606468] |
| Native J sum | 1551.667587 ± 611.248976 | 1521.982069 ± 625.067712 | −29.685518 [−203.914273,+144.543236] |
| Native J/step | .517222529 ± .203749659 | .507327356 ± .208355904 | −.009895173 [−.067971424,+.048181079] |
| Raw return cost/step | .035387605 ± .044560369 | .033756090 ± .044996646 | −.001631515 [−.018296289,+.015033259] |
| Capped return cost/step | .035298304 ± .044362191 | .033659524 ± .044764063 | −.001638780 [−.018292991,+.015015431] |
| Episode minimum battery ratio | .081385552 ± .019008495 | .081943829 ± .019634056 | +.000558277 [−.005678671,+.006795225] |
| End-to-end throughput Mbps/step | 17.940315611 ± 4.101007513 | 17.545148514 ± 4.196621971 | −.395167097 [−1.468528232,+.678194038] |
| Charger input Wh | 454.887153 ± 65.464895 | 466.232639 ± 72.740282 | +11.345486 [−3.704709,+26.395682] |

All64 worlds have nonzero service and zero cutoff/depletion events. This is not
an absence-of-risk or indefinite-operation guarantee. Event improves QoS in 14/32
pairs and J in 17/32; raw return cost increases in 16/32, and minimum battery is
lower in 15/32. Every world remains in the result, without outlier removal.

- **969013**, strongest QoS/J benefit: QoS .362669200→.728957135
  (difference +.366287935), J 378.684696→2063.692172 (+1685.007477).
- **969028**, strongest QoS/J harm: QoS .603779415→.365800734
  (−.237978681), J 1763.145128→332.428508 (−1430.716620), raw return
  cost/step increases .119484807 and minimum battery falls .043690823.
- **969003** also loses .235113280 QoS/step and 779.966125 J.
  **969008** loses 737.764525 J with raw return cost/step +.111765171.
- **969025** has lower QoS (−.083527940) but higher J (+514.084535),
  because raw return cost/step falls .127444724; battery minimum rises .050710277.
  Thus native service and penalized objective cannot be interchanged.
- Lowest event QoS is 969001 at .298927583; lowest event J is 969029 at 233.213135.
  Both arms' lowest battery occurs at 969029: .038681366→.035483446. The largest
  event raw return cost is 969008 at .141146055/step. All other tails are retained
  in the original per-world output.

The mean J difference decomposes as cumulative QoS −39.516710, capped return-cost
penalty improvement +9.832678 and graph-potential difference −.001487. Therefore
the adverse mean J is not evidence of an increased *mean* return penalty. Its
uncertainty and heterogeneous service/risk tradeoffs remain explicit. Boundary
share in normal mode is zero for both; shield-mode share is .422544271→.432377604,
guard-blocked actions 1877.59→2054.06, waiting ticks 6317.03→6423.66, and first
service step 43.75 in both. Charging input/counts rise slightly, with uncertain
paired changes; one-tick charging spell share is .977724→.977202. These diagnostic
means do not identify a causal explanation of the complete service difference.

### Activation, response censoring and fault windows

Both arms execute 100 regular plans/world. Event adds a mean 43.46875 plans
(range 26–60), producing 143.46875 total versus 100. There are 1,435 observed legal
availability-change decisions per arm; event has 1,391 extra plans and 44 changes
coincident with regular replans. Extra calls preserve the original regular clock.
Mean planning CPU is .283341871→.372360946 s/world (difference +.089019075,
t95 [.071781608,.106256542]); planning wall is .274653486→.360564714 s/world.
The measured extra planning cost is small relative to full episode execution;
it is not evidence of an online service deadline or the cause of the score loss.

World-first mean lag from **observed change** to the next executed plan falls
**14.384705877→0** decisions. Clock has 1,418 completed responses and 17
right-censored responses across 13 worlds; event completes all 1,435. No world
lacks response events, and neither arm has a change solely in the final returned
observation. Clock lag is conditional on a subsequent plan and is not a value
assigned to its censored changes. Zero lag refers to the first available decision
after the native transition, not anticipation of a fault inside that transition.

Each arm has 730 native onsets,719 expiries/recoveries and0 immediate refaults;
11 failures remain at the horizon. All32 pairs have equal recorded fault-trace
hashes. This is an observed diagnostic, not an assumption of identical closed-loop
physical trajectories. Complete pre20/post20 windows number 717 onset and 715
recovery;13 onset windows across 12 worlds and 4 recovery windows across 4 worlds
are censored. Recovery post60 has 707 complete and 12 censored windows. Overlap
counts are 565 onset and 566 recovery events. All32 worlds contribute complete
events; event counts are not independent scientific samples.

World-first onset QoS post−pre is −.041527047 for clock and−.037626995 for event
(descriptive difference +.003900052). Recovery post−pre is +.050376731 versus
+.045976417 (−.004400314), and full recovery-post60 QoS is .620681439 versus
.595379432 (−.025302007). The windows overlap and contain topology recovery and
different deployment histories. They neither identify isolated fault/recovery
effects nor replace the complete native endpoints.

### Independent raw verification and retained evidence

The bounded Verifier `b01_raw_verification` checked B02 on `hmasd-wsl-node` with
the configured Python 3.10.21. DM read its full report, audit script and JSON.
The exact source snapshot HEAD matches the launch SHA. Every one of 64 compressed
raw files matches manifest SHA256 and bytes, with exact inventory and no extra,
missing, incomplete, partial or orphan file. Locally collected config/perworld/
summary also match the declared remote manifest. Raw scientific metric/reward
arrays are finite, the native reward equation reconciles, and reconstructed
native metrics, timer events/windows, decisions/counters and every response
lag/censor flag agree. All comparable paired statistics agree with an independent
SciPy t31 calculation (zero mismatches). The complete original paired output
and all positive/adverse worlds remain preserved.

Array-by-array paired timer comparison confirms 32/32 equal fault traces. Per arm,
**28,345/768,000 failed UAV-steps (3.690755%)** and **25,336/96,000 team steps
with a failure (26.391667%)**, maximum two simultaneous failed UAVs. Nonfinite
values occur only in undefined target coordinates and undefined/censored event
window diagnostics, including onset post60 which is undefined by construction.
These were retained, not converted to zero or removed from scientific sample size.

The one canonical raw copy remains at
`hmasd-wsl-node:/home/wu/projects/HMASD/runs/energy_relay_availability/b02_event_replan_a01/raw/`:
**26,901,933 apparent bytes /27,025,408 allocated bytes**. The complete native
output root is 27,372,075 apparent/27,516,928 allocated bytes. The manifest's
27,353,550-byte total covers raw plus its three declared compact files; it does
not include the manifest itself or additional native metadata. Manifest SHA256:
`4a5ab7e0416e8f051df73e44712a3b1756b1d6a023c5a17d45a7ee36715e4880`.
Config SHA256 `d79bb8146b5e8a69fbf4bc51be215ef6bcebef2444cad70b28a176d6404079cb`,
perworld `5123bb6c778fd68f93209b8c9bb577ad4f00d8a5acca8292bdd127950fa462ef`,
summary `2b3002322e35a32821bed6604766ce3b59207d35b18e95294eb72a90a5edb987`.
Hashes establish consistency of retained bytes with their colocated manifest and
the collected compact evidence, not independently signed provenance or universal
replay identity. No raw file was copied locally, and no sealed holdout was read.

<a id="b02-independent-review-and-decision"></a>
## 2026-09-27 — Independent scientific review; retain clock30 and end current timing investment

Scientific Reviewer `b02_scientific_reading` used the dedicated ResearchCritic role
with `fork_turns="none"`, without DM/Root conversation or a proposed B02
interpretation. It reconstructed the frozen comparison, source and original
outputs before reading earlier explanations/advice and current project ownership.
It additionally read eight canonical raw trajectories in four selected positive/
adverse pairs. The independent full raw audit subsequently supplied integrity and
arithmetic verification. DM read the entire returned answer. **MATERIAL_DISSENT:
no**; the reviewer recommends retaining clock30 and ending this event-rule
investment, with no further result-bearing S4 study at this boundary.

The substantive review and DM disposition are:

1. **Adopt the distinction between activation and native usefulness.** The
   intermediate prediction passed: fixed regular calls plus extra event calls
   removed the observed planning lag. The native-improvement prediction was not
   supported: both primary mean differences have the opposite sign, with
   uncertainty allowing benefit and harm. Median J difference is +8.275 while
   median QoS difference is −.016692. Neither wins, medians nor mean sign alone
   establishes a stable population ranking. No equivalence or proof of harm is
   claimed. Local windows do not show a consistent hidden recovery success.
2. **Adopt ordinary deployment sensitivity as a working explanation, not an
   identified component defect.** Clock30 already combines periodic planning,
   continuously executed motion/shield feedback and automatic fault recovery.
   Replanning changes information refresh and trajectories as well as assignment
   timing, under limited but real fault exposure. Spatial visibility, assignment,
   geometry and energy feedback can yield large outcomes in either direction.
   This fits the mixed complete outcomes better than a demonstrated dominant
   response-delay bottleneck. It does not prove churn, optimal timing or a repair.
3. **Preserve the selected-tail reading and its selection limits.** The reviewer
   found zero service during the final 1,000 steps of clock30 on 969013 while event
   continued serving; 969028 showed the reverse. These segments coincided with
   all UAVs in shield mode and no finite H1 targets. That is association in chosen
   tails, not evidence that shield mode alone caused the loss. On969008 event had
   more service in each of the first three 500-step blocks before later costs and
   service losses reversed the early advantage. On969019 event travelled less
   overall but lost service, so a universal extra-travel explanation is inadequate.
   These post-result observations create no new independent sample or selected
   tail-repair experiment.
4. **Adopt the cost reading.** Added planning wall is only about .086 s/world;
   this simulator does not turn that measured CPU time into an observed service
   deadline. The negative mean J arises from the service/risk decomposition above,
   not a compute charge or new cutoff penalty. Shorter aggregate event-worker
   wall does not establish an end-to-end speedup. All scientific and supporting
   costs remain recorded separately.
5. **Adopt no new experiment at this boundary.** The completed 32-pair batch was
   the smallest selected complete observation for the adoption decision. Shorter
   lag with higher complete service/J and acceptable risk could have justified
   retaining the rule; the observed shorter-lag/absent-established-gain branch
   supports declining it. Another unchanged panel mainly purchases precision
   without a presently specified use decision requiring it. A clock sweep,
   onset-only/recovery-only variant, stronger faults or tail-specific changes
   would be new exploratory investments, not completion of B02; none is selected.
6. **Retain the broader question without manufacturing a dependency or successor.**
   Legal spatial history/search and energy-aware assignment remain possible
   questions, but B01/B02 do not currently select their intervention. B01's
   roughly .175/.178 central-reference gaps survive as package differences with
   different information rights, not attainable legal headroom or a learning
   bottleneck. Current [shared understanding](../../RESEARCH.md#研究背景与共享认识)
   and [research allocation](../../RESEARCH.md#current-research-plan), refreshed
   from published `f8263e426`, separate native complete utility from local repair
   diagnostics. DM1 already owns ordinary-learning replication and DM3 owns
   demonstration/closed-loop learning. Duplicating those studies in S4 is not
   justified by this result. Their completion is not a prerequisite for this
   decision, and an available runtime slot is not a reason to invent work.

The working judgment is therefore **weakened** for shortening the existing
availability-response delay as the next default service improvement, **strengthened**
for assessing immediate replanning by complete outcomes, and **retained** for
substantial ordinary legal-control service with consequential trajectory/risk
variation. Better legal information use, different objectives and learning remain
unresolved. B02 says nothing about representation capacity, finite learnability,
decentralized coordination, genuine membership change or general UAV safety.

DM adopts the recommendation in full: **retain clock30 as the ordinary comparator;
end current S4 fault-clock investment; select 0 further fits, 0 new episodes and
0 experimental implementation.** B01/B02 together used 192 complete episodes,
576,000 transitions and 0 fits/updates. This closes the tested approach and releases
its current runtime investment, not the scientific parent question. The direct
DM retains responsibility for that explanation; there is no queued B03, external
producer to await, automatic re-entry or owner permission request. A materially
new feasible comparison would need its own reason, discriminating prediction,
cost and scientific review rather than being implied by these uncertain scores.

One adequate independent scientific review covers this ordinary consequential
decision. The reviewer identifies no distinct expertise/framing/disagreement that
an additional Pro pass would resolve now; DM agrees. No Pro question was sent,
and neither model agreement nor this publication supplies empirical replication.

The useful implementation and checks were already published before execution.
[Frozen B02 source](https://github.com/CartmanFatass/My-paper-code/tree/b4c7b153775222414375da4fda27b25e3c5363a8/experiments/candidates/energy_relay_availability)
and [its focused tests](https://github.com/CartmanFatass/My-paper-code/tree/b4c7b153775222414375da4fda27b25e3c5363a8/tests/experiments/candidates/energy_relay_availability)
remain recoverable beside the separately pinned B01 source. Preserve the compact
readings and the unique raw evidence supporting the retained findings; retire
unused current-tree implementation and disposable scratch after checking consumers.


### Completed publication-boundary cleanup

Both bounded helpers finished reading, no scientific process remains, and native
observation generation6 had no pending events or running jobs before its stop.
No Pro delivery or other direction imports/entrypoints consume this direction's
implementation. Source/test consumers were checked across experiments, tests,
scripts, configs and runtime configuration; notebook source links are pinned to
published B01/B02 commits. Shared H1/environment/evaluator assets are untouched.

The maintained remote snapshot collector preview passed. Its first wrapped apply
refused with `snapshot is referenced by pid 782789 cmdline`; allocation remained
796,823,552 bytes and nothing was deleted. That invocation's measurement wrapper
itself included the full snapshot path in its command text. The recorded PID was
subsequently absent (read-only ps returned no process). A fresh direct preview and
apply under the node's shared Git writer lock rechecked all references, terminal
identities, clean source, canonical output and durable source reachability, then
removed exactly `f45c7e38c26b4a5ba135deadde2bea51`. The documented
`--sudo-process-scan` supplied only the read-only process scan. No check was
bypassed, source edited or worker restarted; the existing zsh prompt warnings
remained separate from the collector's successful exit.

Remote source allocation: **796,823,552 → 0 bytes**, directory absence verified.
All64 canonical raw files and the unchanged manifest hash were checked afterward.
Local exact owned targets were then removed, including12 unused tracked source/
test files, their bytecode caches and the completed launch/wait/audit scratch:

| Removed local target | Allocated bytes before | After |
| --- | ---: | ---: |
| `experiments/candidates/energy_relay_availability` | 180,224 | 0 |
| `tests/experiments/candidates/energy_relay_availability` | 106,496 | 0 |
| `temp/directions/energy_relay_availability` | 69,632 | 0 |

All three paths are absent. Local release is **356,352 bytes**; combined
identified-target net release across both hosts is **797,179,904 bytes
(760.250 MiB)**. This measures the deleted targets, separately from
shared Git object storage and unrelated concurrent host writes. No tarball,
backup, duplicate raw copy or retention package was created.

Actual retained material is the compact positive/adverse results and native
operation records in main, published source/test history, one canonical B01 raw
copy and one canonical B02 raw copy at their recorded node locations. Those raw
copies support the retained event, complete-outcome and tail readings. Native
claims/manifests remain for status and duplicate prevention. No unused owned
source, scratch, snapshot, active observer, cleanup blocker or selected follow-up
remains. Shared research standing is archived for this ended investment while
preserving the question, lead and bounded unresolved explanations.

## 2026-09-27 — B03 prospective target-energy allocation (L0)

### Question, evidence and decision value

Under the same legal pooled observations, target-generation rule and clock30,
does one target-related energy allocation rule improve H_local's complete S4
service, native J and energy-risk outcomes relative to the original distance /
300 m hysteresis assignment? This is a fixed-policy, zero-fit comparison. It
tests one ordinary planning choice; it does not test a learned policy or explain
the separate S2 learning gap.

The current published [shared understanding](../../RESEARCH.md#研究背景与共享认识),
refreshed at main `96e6a8422`, separates legal-control package differences from
an attainable upper bound, and requires full native outcomes beside planning
proxies. The [current plan](../../RESEARCH.md#current-research-plan) and the
[independent review and Root adoption](../../archive/2026-09-27/RESEARCH-two-successors.md#two-successors-review)
select this exact B03 question and exposure. B01 retained a wide fault-regime
interval and a substantial H_central−H_local package gap; B02 removed observed
replanning lag (14.38→0) but did not establish QoS/J improvement and had 14
positive versus 18 negative QoS worlds. Those studies retain their scope and
adverse worlds. The new observation changes only the allocation cost: whether
legal battery plus an explicit target→service→station energy estimate adds
useful information to the ordinary planner. Current return margin alone cannot
answer that question because it describes return from the current position.

The earlier independent ResearchCritic review already recommended this exact
comparison, its limits and its cost. Root accepted it at `2905e4f9e`; the current
plan still matches that decision. Its evidence and premises have not changed in a
way that calls for another scientific-review or Pro round. Engineering review
remains separately required for the new assignment implementation.

### Fixed arms, energy rule and conditions

- `distance_hysteresis`: frozen B02 `clock30` H_local assignment, using the same
  legal pooled user/BS/station observations, H1 target-generation code, 30-step
  clock and original Euclidean-distance / 300 m continuation hysteresis.
- `energy_fraction`: the same planner, target generator, legal information,
  available-UAV mask, movement actions, production shield and 30-step clock. The
  only decision change is the cost matrix used by the existing target assignment
  (including its existing station-1 search-ring fallback). At any identical
  decision observation, the ordered relay/service/search targets are unchanged.
  Subsequent target sets may naturally differ when the closed-loop states differ.
- For each available UAV `i` and generated target `j`, decode legal current xyz,
  battery fraction and valid station xyz. Target xyz uses H1's unchanged 100 m
  command altitude. Use the S4 propulsion function
  `P(vxy,vz) = P0*(1+3*vxy^2/Utip^2) + Pi*sqrt(max(0,sqrt(1+vxy^4/(4*v0^4))-vxy^2/(2*v0^2))) + k3*vxy^3 + 15*abs(vz)`
  with the native constants `P0=79.86 W`, `Pi=88.63 W`, `Utip=120 m/s`,
  `v0=4.03 m/s`, `k3=0.5*0.6*1.225*0.05*0.503`, and one-second steps.
  Predict nominal outbound energy using H1's command law in one-second steps:
  each step uses `vxy=min(remaining_xy,30)` and
  `vz=sign(dz)*min(remaining_z,5)`, subtracts those distances, and sums
  `P(vxy,vz)/3600 Wh` until both components reach zero. A dimension that has
  already reached its target contributes zero speed while the other continues.
  Add one full
  clock-period service load, `Eservice=30*P(0,0)/3600 Wh`, assuming 30 seconds
  of level hover at the target after arrival. Estimate target→station energy for
  each legally valid known station `s` by the native return-margin convention:
  `Ereturn_s=(distance_3d(target,s)/3)*P(3,0)/3600 Wh`; use the least such
  estimate. This reflects a 3 m/s limp-home estimate, not a guaranteed path.
- Let `Mij=Eout+Eservice+min_s(Ereturn_s)`. Let `Bi=max(0,160*battery_fraction_i
  - 0.10*160) Wh`, using the fixed S4 capacity and reserve. Minimize
  `Mij/max(Bi,1e-6)` over the same one-to-one assignment. Preserve the former
  hysteresis scale by subtracting the continuation bonus
  `E300/max(Bi,1e-6)`, where `E300=10*P(30,0)/3600 Wh`, from the cost of
  the nearest generated target matching that UAV's previous target. Keep the
  existing solver and tie behavior. Record each assigned mission estimate,
  budget, predicted reserve slack, chosen station and cost; do not apply a hard
  feasibility filter.
- This is one frozen heuristic, not a future-energy guarantee: it assumes one
  full 30-second hover after reaching the target, fixed H1 travel speeds, the
  native simplified return estimate, and a reachable station without queueing.
  It ignores changing demand, intervening replans, shield/guard changes to the
  path and station competition. The production shield and charging contracts
  remain untouched. No future or hidden user positions enter the controller.

Both arms use native S4 with eight fixed slots, 30 users, native fault
probability/duration/minimum-active contract, identical target generation,
clock30, production shield and charger rules. Do not drop or replace any target,
change the fault policy, return threshold, information rights, assignment solver,
replan period or mobility. Fresh predeclared development worlds are seeds
`970001–970032`, shared across both arms: 32 pairs, 64 full H3000 episodes,
192,000 planned team transitions, 0 fits and 0 optimizer updates. These are not
confirmation worlds. Pairing is by the same initialized world seed; before
claiming matched stochastic paths, compare initial-state hashes, per-step legal
user-xy traces, native failure-timer traces and the environment RNG-state stream.
Report exact match counts and digests. UAV paths may differ as a treatment result;
do not call them common trajectories. If exogenous traces diverge, preserve the
initial-world pairing but state that the later random streams were not identical.

### Readings and outcome branches

For every world retain native J, QoS, throughput, all native reward/risk
components, raw/capped return cost, minimum battery, return-margin distribution,
low-battery/cutoff/depletion counts, charging, waiting, guard and shield exposure,
episode length/terminal type, complete raw traces and per-plan assignment
diagnostics. Summarize both arm distributions and all 32 seed-paired differences
with means, SDs, SEs and approximate t31 95% intervals for complete J, QoS and
the recorded risk measures. Keep every positive and adverse world. Predicted
energy fraction/slack and assignment changes are mechanism diagnostics; their
improvement alone is not a native-use result. No equivalence or safety claim is
planned.

If QoS and native J improve together without a material deterioration in
return-cost, low-battery, cutoff/depletion or adverse-world outcomes, the rule
may be retained as a conditional H_local/S4 ordinary-planning improvement. If
risk improves while service/J worsens, report a cost trade. If predicted reserve
slack improves without complete native improvement, the target-energy model did
not establish use for this rule. If effects are small, mixed or imprecise, say
that without claiming equivalence. In every branch, stop this exact rule after
the declared comparison; do not auto-sweep coefficients, remove hard worlds or
raise fault intensity. The result cannot directly explain S2 learning behavior.

### Cost and engineering scope (L0)

Preferred node `wsl_4070`, four spawned CPU workers × one numeric thread each,
subject to fresh actual-node admission. Plan for 30–60 minutes of native
execution; B01/B02 rates inform this estimate but do not guarantee it. Record
actual acceptance-to-exit, runner wall/CPU, per-worker wall/CPU/RSS and output
bytes; implementation, tests, review, publication, contention and readback are
additional actual costs.

Deliverables, all direction-owned: recover the pinned B02 baseline adapter and
its focused regression inputs as needed; add a B03 energy-cost/controller
adapter, immutable 64-job runner, paired readout, admission-guarded entrypoint,
and focused tests under the matching candidate/test paths. The runner records
source identity, effective S4 configuration, both native arms, all planned and
completed jobs, full paired diagnostics and one compressed raw trace per world.
Do not change shared environment, H1, shield, evaluator or other direction code.

Focused checks cover the exact propulsion arithmetic against the S4 native
function, target→station selection and battery normalization, energy hysteresis,
unchanged H1 target generation and 30-step clock, no RNG use by the controller,
paired reset/user/fault/RNG fingerprints, immutable seeds and output paths,
missing-admission refusal before output creation, and complete adverse-inclusive
paired summaries. Use pytest-owned scratch and nonpanel engineering seeds; no
test evaluates a declared development world. Independent Engineering Reviewer
will inspect cost units, legal-information boundaries, assignment semantics,
RNG/path pairing and failure/partial-output handling before DM acceptance and
publication.

### Engineering implementation and prelaunch review (2026-09-27)

Restored the B02 clock30 distance baseline adapter and its focused regression inputs from
the pinned B02 source. Added the B03 legal energy-cost adapter, immutable 64-cell runner,
per-world paired readout, and runner-side admission entrypoint under this direction's
candidate directory. Each assigned target record retains the modeled outbound, 30-second
hover and return Wh, usable battery above reserve, predicted slack, chosen legal station,
raw cost fraction and post-hysteresis assignment cost. Compressed raw output holds one
trace per completed world; failed worlds retain the partial observer and decision records
when available.

The configured Linux scientific Python ran
`tests/experiments/candidates/energy_relay_availability/test_b03.py` together with the
restored `test_b02.py`: **12 passed** in 8.23 s on the final focused run. The engineering environments used only
nonpanel seeds 42 and 43; the B03 runner path exercised two five-step smoke episodes at
seed 43. Checks cover native propulsion equality, legal station selection, budget
normalization, unchanged target generation and clock30, no environment-RNG consumption by
the assignment call, identical reset/user/failure/RNG fingerprints for the short paired
world, admission refusal before output creation, and complete adverse-inclusive synthetic
paired summaries. No declared B03 development seed or H3000 study episode was run during
engineering checks.

The independent Engineering Reviewer found one P2 in the first readout: arm-level panels
omitted SEs and t95 intervals. Added per-arm SE, df and Student-t 95% intervals, including
nullable uncertainty when fewer than two values are available; the Reviewer confirmed that
this resolved the finding and reported no remaining material issue in the assigned
engineering surfaces. Added a direct check that the launcher binds `--out` to the exact
tag path. Full H3000 behavior and the admitted four-worker execution were unobserved at
implementation/review sign-off.

### Native B03 launch accepted (2026-09-27)

The declared 64-world, zero-fit B03 comparison was accepted once under operation
`5932941d6d03e635fc7b78cb956891cf20fe370a4f20149a45e8a4e2591ec4f7`. The
[native manifest](../../../../runs/energy_relay_availability/b03_energy_assignment_a01/launch-manifest.json),
[admission preflight](../../../../runs/energy_relay_availability/b03_energy_assignment_a01/admission-preflight.json)
and [initial launch status](../../../../runs/energy_relay_availability/b03_energy_assignment_a01/launch-status.json)
retain the exact source, command, node, output, supervisor and runner identities. The
fresh actual-node preflight measured 15,414,423,552 available physical/effective bytes
against the 4,294,967,296-byte floor and passed.

At 10:02:55 UTC, native status found consistent accepted records, matching live runner
and supervisor identities, and no process-exit witness. The outer supervisor handle
`era-b03-energy-assignment-a01` had exited zero after submitting the launcher; that is
not the experiment's exit. No scientific outcome has been read or interpreted. Compact
acceptance metadata has been copied into the canonical `runs/` tag directory; the live
runner's evolving outputs remain on `wsl_4070` until terminal collection.

### 2026-09-27 — complete native B03 reading

#### Terminal reconciliation, integrity and cost

Drained generation 1 / wake `92e68f18-f260-4da4-924f-4da5c21a8cce`, event
`15f405d37df42f6cd9b8d598`. The `READY` event recorded accepted, internally
consistent records; a valid process-exit witness with code 0; and absent runner and
supervisor. The same-key operation was never restarted; status says
`explicit_retry_available: false`. A fresh native status at 10:23:39 UTC agreed.
After rearming generation 2, the drain had no pending events; the observer was
stopped with `work_unchanged: true`.

The runner summary is `complete`: **64/64 H3000 episodes**, 32 per arm, 192,000
actual transitions, 0 fits, 0 optimizer updates, and no failed, cancelled, missing,
unstarted, unreconciled, partial or orphan jobs. All episodes truncated at 3,000
steps; neither arm had zero-service worlds, service cutoffs or depletion events.
These zero counts are observations, not a safety or equivalence claim.

Copied the complete 74-file remote run directory into the canonical local tag
directory and matched every copied file hash to the remote source. All 64 raw NPZ
files also match their per-world manifest byte counts and SHA256 values. The raw
files total 137,304,566 bytes; the run manifest reports 137,926,213 total storage
bytes. The local [summary](../../../../runs/energy_relay_availability/b03_energy_assignment_a01/summary.json),
[per-world table](../../../../runs/energy_relay_availability/b03_energy_assignment_a01/perworld.json),
[manifest](../../../../runs/energy_relay_availability/b03_energy_assignment_a01/manifest.json),
[config](../../../../runs/energy_relay_availability/b03_energy_assignment_a01/config.json),
[final observed native status](../../../../runs/energy_relay_availability/b03_energy_assignment_a01/operation-status-observed.json)
and all raw traces retain the evidence. The independent ResearchCritic also
recomputed the native metrics and paired summaries from all raw files; no material
integrity contradiction was found.

Accepted 09:59:19.983 UTC; process exit was 10:16:49.509 UTC, **17.49 minutes
acceptance-to-exit** on `wsl_4070`. Runner parent wall was 1,005.568 s; parent CPU
1.152 s / peak RSS 477,024 KiB. Worker totals were 4,068.411 CPU-seconds and
3,908.388 wall-seconds, with maximum reported single-worker peak RSS 530,852 KiB.
Worker timers stop before NPZ compression and hashing, so they undercount full
worker process cost; batch elapsed includes that work. Engineering, review,
transfer and scientific readback are additional and not combined into one end-to-end
measure. The four workers each used one configured numeric thread.

#### Frozen native outcomes

All intervals below are approximate paired Student-t intervals with 31 degrees of
freedom. The unit is one same-initialized-world seed pair, not an independent
training seed. There is no multiplicity adjustment and this development batch is
not confirmation.

| Outcome | Distance / hysteresis mean | Energy-fraction mean | Energy − distance, mean [t31 95% interval] |
| --- | ---: | ---: | ---: |
| QoS per step | 0.58029 | 0.55367 | −0.02662 [−0.05886, +0.00562] |
| Native J sum | 1,431.49 | 1,223.37 | −208.12 [−403.86, −12.37] |
| Raw return-cost sum | 139.77 | 207.92 | +68.15 [+5.11, +131.19] |
| Capped return-cost sum | 139.41 | 203.54 | +64.13 [+4.49, +123.77] |
| Episode minimum battery ratio | 0.07570 | 0.06769 | −0.00801 [−0.01480, −0.00122] |
| UAV steps below fixed 10% reserve | 9.73% | 12.88% | +3.15 pp [−0.20, +6.50] |
| UAV steps with negative return margin | 10.72% | 13.88% | +3.16 pp [−0.21, +6.54] |
| UAV steps below dynamic return threshold | 50.79% | 50.55% | −0.24 pp [−0.61, +0.13] |

QoS is lower on 20/32 worlds and higher on 12/32; native J is lower on 22/32 and
higher on 10/32. Both improve in 9 worlds, both decline in 19, and four split.
Capped return cost rises in 22/32 pairs; minimum battery ratio falls in 24/32.
Seed 970005 preserves a large joint service/J loss: QoS/step 0.68980→0.36046 and
J sum 2,030.73→275.17. Seed 970020 preserves a severe low-energy tail: raw
return-cost sum 47.69→722.11, minimum battery ratio 0.08508→0.03023, and steps
below fixed reserve 0.42%→30.76%. The favorable seed 970012 also remains: QoS/step
0.33272→0.49335, J sum 193.85→1,393.92 and raw return-cost sum
388.03→27.99. All 32 pairs remain in the per-world output.

The mean native-J loss is consistent with lower QoS plus higher capped return cost
(approximately −79.86 J from service and −128.26 J from return penalties per
world, with about +0.001 from shaping). This is not a demonstrated risk-for-service
trade: the energy arm does not improve service or J on average, and its return-cost
and minimum-battery outcomes worsen.

#### Pairing and prediction diagnostics

Initial-state, user-position, failure-trace and environment RNG-stream hashes agree
in **32/32 pairs**. The independent reviewer also compared all retained user-position
snapshots and failure timer arrays directly. UAV paths differ as an effect of the
assignment and are not claimed as common trajectories. Pairing supports this fixed
controller/world comparison, not a learning or training-seed claim.

The energy arm logged 3,755 assignment records and 14,100 assigned missions; 2,120
selected missions (15.04%) had negative model-predicted reserve slack. It executed
100 scheduled clock30 replans per world, as did the baseline. The distance arm does
not compute these energy records: its zero mission/slack fields are structural
placeholders, so no comparative slack improvement or model calibration is shown.
The energy arm also averages 487 more waiting UAV-steps and 24.44 Wh less charger
input per world. Those are downstream observations, not a causal diagnosis of why
the complete outcomes changed. The modeled continuous outbound/service/return
cost omits actual replanning, shield interventions and station queueing; its
misalignment with closed-loop outcomes is plausible but not identified here.

#### Independent review and DM disposition

The separate-context Scientific Reviewer independently read the frozen question,
source and raw outputs before receiving the DM's interpretation. It recommends
stopping this exact `energy_fraction` rule, retaining `distance_hysteresis` as the
ordinary S4 comparator, and selecting no confirmation, coefficient sweep or
additional batch. The predeclared retention branch required joint QoS/J improvement
without material energy-risk deterioration; the cost-trade branch required risk
improvement alongside service/J loss. Neither describes these results. The DM adopts
that conclusion. `MATERIAL_DISSENT: no` on the result and stopping this rule.

The strongest plausible explanation is that distance plus continuation already
provides useful spatial allocation and the proposed normalized mission estimate is
not sufficiently aligned with the full closed-loop task. The lower charging input
and higher waiting are compatible with that interpretation, but do not identify a
queueing or energy-model cause. B03 does not establish that battery information or
energy-aware allocation generally lacks value, does not establish safety, and does
not explain S2 learning. The frozen rule is **NOT_VIABLE_CLOSE**; the broader
ordinary joint-allocation question remains with this DM, with no current successor
selected. Any continuation must offer a distinct pre-result prediction and reason
to spend the next evaluation; this result does not authorize a rescue sweep or an
additional run.
