# UAV radio-aligned spatial placement

## 2026-09-28 UTC - first source reconstruction and comparison proposal

Native DM `/root/dm_radio_placement`, assigned by Root
`01a0e560-4333-7b03-8ff3-759a4add1d9a`, owns this question and the five
`uav_radio_placement` direction directories on shared main. The owner pause is
lifted; PPC/FSD pauses and G33's frozen contract are unchanged. Current published
background was checked at `6dfbc9731e911de00d76d2b812063a741a4a0dfb`.
No accepted operation is inherited. This entry has **0 fits, 0 model queries,
0 native episodes/steps and 0 optimizer updates**. Reading/design and source
inspection have real, unmetered cost. Root's combined independent scientific
review covers this selection; no duplicate critic was requested. The proposal
below is for that review, before result execution or selection-dependent code.

### Question and inherited constraints

Does an ordinary controller that constructs spatial targets using native
end-to-end radio service add useful complete service and native objective value
over competent geometric placement? The contribution sought is empirical task
understanding and possibly an ordinary control asset, not a learning algorithm.
The working conjecture is that geometric clustering leaves usable spatial
choices because access bandwidth, association and routed backhaul are coupled.
The strongest competing explanation is that the existing geometry is already
adequate for this controller class, while transit, mobility, energy and the
model's static approximation dominate any target-score improvement.

The relevant [RESEARCH topics 1, 3, 6 and 8](../../RESEARCH.md#研究背景与共享认识)
require the complete native objective and service/risk components, a competent
same-information comparator, explicit model cost and retention of adverse
worlds. Their concrete effects here are the H competence anchor, full H3000
evaluation through recharge, and refusal to infer usable headroom from a
hypothetical layout score. Small Hungarian/identity differences do not certify
the spatial targets; the availability/planning results prevent treating better
static service or zero cutoff as a safe complete improvement.

Sources read for this proposal:

| Evidence | Consequence for the comparison |
| --- | --- |
| Benchmark B01 `b01_ref_a02`, source `e1fdbe72f`; [original reading](../energy_relay_benchmark/NOTES.md#2026-09-26--b01-result-read-by-the-pre-registered-branches-operation-02f762d2-tag-b01_ref_a02) | H1 was selected against H2/H3 on eight development worlds: J 2248.1 versus 2196.9/2167.0. On the 32-world main panel H1 has QoS .7740 and J 2281.9. Retain this demonstrated ordinary controller rather than substitute an untested geometric optimizer as the only comparator. |
| Benchmark `b03_stake_a01`, source `5e8da3d94`; original summary/panels and the [subsequent correction](../energy_relay_benchmark/NOTES.md#2026-09-27--independent-challenge-of-the-stage-2-0-entry-and-the-two-arguments-hmasd-research-critic-separate-context-read-only-on-the-working-tree-material_dissent-yes-on-eleven-statements-my-first-hand-verification-disposition-d-credit-argument-withdrawn-to-revision-next-step-redefined) | Hungarian minus identity is +.006827 QoS and +57.808 J, not a layout-quality bound. Identity travels 186 versus 136 km and has more subsequent energy cost; its global-index rule also leaves different targets empty. Nearest loses .324 QoS with severe co-location/absorbing-stack behavior; it does not identify the isolated value of de-duplication. |
| Availability [B04 complete reading](../energy_relay_availability/NOTES.md#2026-09-27--complete-native-b04-reading), `025350669`; [B05 complete reading and review](../energy_relay_availability/NOTES.md#2026-09-27--complete-native-b05-reading), `754d5d34d` | Ordinary motion timing can help. B05's +.016071 QoS/+35.808 J mean advantage coexists with world 28092823's J -260.945 and 16.279% reserve exposure. Static scores, strict floating-point ties, energy omissions and full risk must remain separate. Do not reuse the rule that disables all planning whenever one member enters F. |
| Cooperative planning [B02 complete reading and disposition](../uav_cooperative_planning/NOTES.md#2026-09-27--complete-native-b02-reading), `9f72afd22` | One active learned value package lost .016488 QoS/55.389 J to its ordinary planner and selected hold in 4575/4582 active windows. World 29102732 has minimum battery .076676 and reserve exposure 14.733%. This limits that learning recipe, not spatial opportunity; do not rerun its residual. |
| Benchmark's new [reasoning entry 2](../energy_relay_benchmark/NOTES.md), published `6dfbc9731` | Claude adopted Pro's objections to geometry-insensitivity and chain-feasibility claims; its selected saved-SET geometry-response probe is a distinct learning/representation question. Its new observations are not assumed and its code/records remain owned by Claude. |

### Native meaning of the spatial score

In `routed_core.py`, channel calculation feeds access association and UAV/base
connections, then widest-path routing. `energy_aware.py`'s
`_calculate_end_to_end_user_rates` divides each member's access bandwidth among
its associated users, limits that member's delivered access by its recorded
route bottleneck, and takes the maximum delivered rate across members for each
user. Native QoS is mean clipped delivered demand. This is not the graph
potential's relaxed-capacity proxy and not a newly imposed multicommodity flow
model: this path does not subtract downstream traffic from shared edge capacity.

`_communication_unavailable_mask` is failed or battery at/below the native
service cutoff. Returning and charging members continue to participate above
that cutoff. F mode does not remove a member from the radio graph. Native reward
also uses the team's worst return-energy deficit, cutoff/depletion events and
potential shaping; none can be replaced by geometric target score.

Current H1 computes six k-means service centers, places two relay targets at
one-third/two-thirds of BS-to-center-mean, prioritizes relays then largest
clusters, and assigns the available prefix with Hungarian distance and 300 m
continuation hysteresis. Its central user/BS positions are privileged relative
to the radius-gated local observations. All new arms receive that same central
snapshot; this study does not estimate the value of information.

### Smallest recommended complete comparison

Use native S7-S2, eight UAVs, thirty moving users, production charging capacity
and allocator, H3000, unmodified native reward/termination/guard/energy physics.
Evaluate **eight new common initialized worlds under H, G and R**, 24 complete
episodes, at most 72,000 native team steps, zero fits/updates. Seeds are fixed
in the accepted implementation declaration before any execution and exposure
checked against current records. No preliminary result panel is proposed.

All arms plan at t=0,30,...,2970, receive identical current central user/BS xy
and legal own/team energy/position information, and use the same capped xyz
go-to primitive (30 m/s horizontal, 5 m/s vertical), native guard and per-step
production F (entry 0, exit .05). Current F members remain under F. A new entry
between planning clocks still overrides the spatial proposal. R may optimize
all other members even while some return or charge. The generalized xyz executor
must reproduce the original H1 actions when targets have H1's 100 m altitude.

**H, established geometry:** unchanged H1 central target construction,
Hungarian assignment and hysteresis at its original 30-step clock. No radio
search affects its actions.

**G, stronger geometric solve:** the same six-center/two-relay construction,
assignment, 100 m height and execution, but use eight deterministic k-means
initializations. Include H's exact initialization; the other seven use
farthest-first centers with first-user indices evenly spaced across the 30
current users. Each Lloyd run uses the existing 30-iteration/empty-center/stop
semantics. Select the lowest final sum of squared user-to-center distances;
earliest listed candidate breaks exact ties. This improves the declared
geometric criterion, not necessarily service. H protects the comparison if
the new G is weaker as a complete controller. There is no tuning on the panel.

**R, radio-aligned layout search:** reconstruct a separate model object from
the fixed public S2 configuration. Supply only this clock's allowed user/BS,
own-position and battery fields, with fresh association. Never deepcopy the
live environment's hidden association/RNG/future motion into the planner.
Initialize from the four complete per-member layouts H, G, carried R targets
and current positions (duplicates may be skipped deterministically). F members
have their current observed xyz in every candidate; their radio availability
still follows battery/failure, not F. For a carried target unavailable at the
previous clock, use current xyz. Score all movable members at their proposed
target positions, without teleporting the actual environment.

The scalar is the native static mean clipped QoS, with native access
association, MCS, interference and widest-path routing. Select a layout, then
make two deterministic member-by-member pattern-search sweeps. Every movable
member tests +/-x, +/-y, +/-z around its current candidate target. Horizontal
steps are 500 then 125 m; vertical steps are 50 then 25 m. Clip candidates to
native map/height limits. The member order starts at clock_index modulo eight;
later evaluations include earlier accepted positions. There is no fixed
relay/service identity, one-donor restriction, one-event limit or prohibition
on choosing a coincident target when the actual service score favors it.

Use float64 scoring. A QoS increase must exceed 1e-10. Within that fixed
tolerance, prefer shorter total three-dimensional proposed travel, with a
1e-6 m distance tolerance and existing-candidate-first tie order. These fixed
numerics avoid crediting sub-ulp arithmetic as deliberate service search;
they are part of the prospective package, not a repair of B05. Record actual
score gaps, ties, position changes and query counts. Stop after the two sweeps;
there is no convergence guarantee, global optimum or oracle claim.

This is a finite local ordinary optimizer with geometric initializations.
R-G changes search/objective/target support as a package; it is not an isolated
causal effect of replacing one formula. G-H describes improved geometric
solving and R-H tests added usefulness over the established controller. An
equal-query alternate-objective optimizer would answer a narrower attribution
question but is not necessary to determine complete usefulness first.

### What is deliberately approximate and what remains native

The model evaluates stationary layouts with current users, current batteries
and fresh association. It omits travel-time service, association history,
movement-dependent consumption, guard reactions, future user motion and future
charging competition. Returning/charging members are included at their current
position, not their hypothetical arrival. This is an explicitly limited
deployment objective, not a calibrated rollout or an attainable upper bound.
The complete evaluation retains all of those native consequences. A static
score improvement that is erased by them is a useful adverse outcome for this
specific method, not permission to silently add a forecast or energy repair.

This differs from sibling `uav_energy_coordination`: that question compares
simultaneous versus sequential selection from a broad service/return/charging
goal library under a 600-step analytical itinerary. Here the intervention is
spatial position construction and a static radio objective, with the existing
F controller handling energy. Both have joint geometry; neither owns that
whole question family. If a defensible R design needs the sibling's itinerary
search, propose a merge to Root before implementation rather than recreate it
or freeze real couplings to manufacture a residual. Reuse only published
shared/native helpers; do not import another writer's uncommitted work.

### Readings, predictions and outcome branches

Primary contrast is R-G, with R-H and G-H reported alongside every per-world
outcome. The targeted prediction is both higher same-snapshot static service
and higher complete mean QoS/native J; optimizer score alone cannot satisfy it.
At each program's own states retain static H/G/R candidate scores where already
computed. H/G get one additional diagnostic score for their selected targets.
These endogenous states are not a shared counterfactual rollout or causal
decomposition. Fixed clock thirds describe deployment/sustained operation
without different-length first-return windows.

Read complete QoS, delivered traffic, native J/decomposition, native worst-member
return-cost sums, minimum battery, at/below 10% reserve, cutoff/depletion,
zero-service steps/longest service gaps, input/consumed energy, actual xy/xyz
distance, F/charging fractions, guard blocks, target changes and planner
CPU/wall/query counts. Preserve every adverse world and score/native conflict.
Paired means and descriptive t7 intervals are conditional on these eight
worlds/programs, not training replication, equivalence or tail safety.

- R improves complete QoS/J relative to both G and H with acceptable observed
  risk: finite spatial optimization has conditional usable value. This does
  not establish general optimality, pure objective causality or learning need.
- G improves over H and R adds little: geometric solving is a sufficient
  simpler explanation within this comparison. A small difference does not
  establish equivalence or exhaust all radio placement methods.
- R improves static service but loses native QoS/J or creates severe risk:
  this static-layout package has not earned use; preserve the mismatch and
  stop this recipe's automatic expansion. Transit/model/energy mechanisms
  remain alternatives, not diagnosed causes or automatic repair assignments.
- Neither optimizer improves useful native outcomes: the selected searches
  have failed to demonstrate usable layout improvement. Do not conclude that
  H is globally sufficient or that all remaining losses lie outside geometry.
- Technical failure/missing worlds stay incomplete; do not impute zero,
  splice an old comparator or automatically retry.

### Complete prospective cost and next boundary

Eight worlds x three arms x H3000 = 24 episodes / <=72,000 native steps.
Each arm has at most 100 real planning clocks. R makes at most
`4 + 2*8*6 = 100` radio queries per clock, or **80,000** total. H/G each add
one selected-layout diagnostic query per clock, **1,600** combined. G and R
each perform at most eight 30-iteration k-means solves per clock; H performs
one, so at most **13,600** k-means solves or **408,000** Lloyd iterations before
early stopping/deduplication. Assignment and per-candidate distance/tie
calculations are additional. There is no inner native episode or hidden fit.

For scale only, B04's H evaluation CPU was 160.66 s per H3000 world, suggesting
about 1.07 worker-hours for 24 episodes before optimizer cost. The sibling's
historical B02 panel difference corresponds to about .016 worker-seconds per
service snapshot, implying about .36 worker-hours for 81,600 snapshots.
These are confounded historical extrapolations, not measured pure-service
rates or a promise of total wall time. Construction, geometry search, complete
model/RNG instrumentation, CPU contention, import/build, engineering review,
scientific reading, publication and raw retention are additional; no exact
total is asserted. Prefer wsl_4070 per current compute policy, with fresh
admission immediately before a selected published launch; use local only for
a recorded node-suitability/unavailability reason.

Next: Root's already assigned combined ResearchCritic receives this original
evidence and proposed comparison. Resolve any material question/comparator
objection before result work. While that decision is pending, finish read-only
native-contract mapping and the exact bounded engineering scope. If selected,
implement within the owned paths, verify information isolation/unchanged H,
obtain independent engineering review, publish exact inputs and run the one
complete native batch. No extra arm, panel, fit or rescue is pre-authorized by
a favorable proxy or an uninformative result.

## 2026-09-28 UTC - independent recommendation adopted and B01 L0

Root returned the combined independent Scientific Reviewer's recommendation
through native communication after reviewing the native radio/routing source
and this notebook: **proceed with the direct complete H/G/R comparison**.
Root adopted it at shared-control commit `59a77f2c8`, retaining eight new worlds,
three H3000 programs, <=72k steps, zero fits and <=81,600 radio queries. The
substantive qualification is adopted: R-G is a target/search/movable-support
package comparison, not the causal effect of one objective formula. This is
the recommendation communicated by the assigning Root, not a claim that this
DM has read a separate full review transcript. No material dissent was passed
back as unresolved; the assigned implementation can proceed without waiting
for another science round or per-run acknowledgment.

The source Scout independently mapped the S2 path and returned the fixed
1 Mbps/user demand, soft-handover history semantics, cache rebuild order,
communication cutoff rule and existing B04 isolation tests. Its source-only
return is factual assistance, not the scientific review above. A separate
fixed-config model object will use B04's native snapshot scorer; it is never
the live environment passed to that scorer. There is no new shared-core edit.

### Fixed execution and owned implementation

Batch B01 uses seeds **36092801-36092808**, subject to the exact source-record
exposure scan before publishing the executable input. Arms are H, G, R in
that declared order; each gets all eight seeds. H3000, clock30, production F,
two R sweeps and the proposed numerical rules are unchanged. Worker count is
two, one numeric thread each; all scientific computation remains CPU even if
the chosen node has a GPU. Node preference is wsl_4070. Expected source entry:
`experiments/candidates/uav_radio_placement/run_b01.py`; output tag
`runs/uav_radio_placement/b01_spatial_a01/`. Neither changing a tag nor a
technical failure authorizes a duplicate attempt.

L0 deliverable: the finite ordinary placement controller, admission-guarded
fixed batch, complete native output and independently reproducible reading.
Owned implementation is `experiments/candidates/uav_radio_placement/b01/` and
the direction entrypoint; tests mirror that directory. DM owns NOTES, runner,
readout/collection and all Git publication. A bounded Implementer may own only
`b01/placement.py` and `tests/.../b01/test_placement.py`; it has no index,
shared-file, notebook, launch or child-agent permission. Other sessions are
concurrently editing main and their changes are preserved.

The controller API is `PlacementController(arm, env, model_env)`, compatible
with the existing `evaluate_world` propose/reset/targets_xy contract; the model
environment is separately constructed from `make_eval_config` with fixed seed
0. It exposes `decision_records` and per-member xyz targets. The H/G candidate
constructors in R use the same previous selected R target history for the
existing Hungarian hysteresis, with independent temporary objects; they do
not advance any baseline controller or global RNG. At each sweep's member,
the six directions originate from the incumbent target at that member's
start, and all six are compared before accepting the winner. A clock has at
most 100 queries. Non-finite target entries are filled by current xyz only for
scoring; actual H action behavior is retained. Native cutoff/unavailability
and F remain distinct. Candidate altitude is clipped to fixed native bounds.

Per-world raw keeps every existing native metric/trace, all 3001 exogenous
user frames and their RNG/initial-state digests, pre/post physical positions,
proposed/submitted actions, actual velocity, and per-clock selected xyz,
candidate score/distance/identity, acceptance and query/cost records. Compact
outputs keep config/source identity, complete per-world results, all pairwise
signed effects and uncertainty, score/native conflicts and resource totals;
bulk NPZ lives in one durable node location with size/hash metadata.

Checks: original H proposals and shielded short native trajectory versus
unchanged H1; geometric best-of-eight criterion and fixed count/empty-cluster
semantics; bounded six-direction search/tie/clipping including F and cutoff;
model live-state/RNG isolation and native score parity with B04; charging radio
availability; short paired H/G/R native evaluation with exact clocks and
exogenous matching; failed/missing/duplicate outputs never read as complete;
admission before environment construction; raw-derived native arithmetic and
all hashes at collection. Native fixtures and short regressions are engineering
checks on separate declared test seeds, not the eight result worlds. Engineering
review covers this high-risk executable path independently before publication
and result launch. Stop at this one fixed batch's complete reading, or a
preserved technical failure needing a fresh scientific decision.

### Engineering preparation and cost correction

The full [combined scientific review and Root disposition](../../archive/2026-09-28/RESEARCH-expanded-native-dm-review.md)
were subsequently published at `ee5799a2c`. The F section supports H/G/R,
retains full native service/J/risk and computation, and states no material
dissent against the selected comparison. Its static-package and no-automatic-
repair boundaries are the boundaries adopted here.

The Implementer returned the two owned placement files with eight focused
checks passing. DM read the full implementation and accepts the intended
controller behavior for integration/review. One accounting correction is
required before execution: R constructs H separately from G's eight starts,
so it performs nine k-means solves per clock, not eight. The implementation is
simpler than sharing mutable assignment construction; retain it and record
**14,400 solves / at most 432,000 Lloyd iterations** across the batch instead
of the earlier 13,600/408,000 estimate. Actual iteration counts for original H
are not instrumented and stay unmeasured. This adds no radio queries, episodes,
fits, arms or search sweeps. All proposal seeds were searched in current
docs/runs/experiment source; only this direction's prospective declaration
matched, with no earlier exposure found.

### Engineering acceptance before publication

DM accepted the implementation after the registered independent engineering
Reviewer `/root/dm_radio_placement/placement_engineering_review` read the fixed
contract and all owned code in a separate context. It found one P2: caught
worker failures could retain planning queries in a partial artifact but omit
them from cost totals. This is fixed with invocation-started/completed counters,
successful-record conservation and an explicit lower-bound/unmeasured-cost
qualification for incomplete batches. An injected first native-step exception
retains the already spent query and zero native steps. The Reviewer statically
rechecked the correction and reported no remaining material issue. This is
engineering acceptance, not scientific evidence or a launch witness.

Final local command, with the configured toolchain PATH, passes **14 tests in
11.89 s**. Coverage includes 31-step H/G/R paired raw records, a 35-step exact
original-H1 native trajectory, separate-model/live RNG isolation, best-of-eight
geometry, F/radio cutoff distinctions, search order/ties/clipping, admission
before science, full offline metric/reward/hash/search-choice reconstruction,
missing/duplicate worlds and artifact corruption refusal. The independent
Reviewer earlier reran the then-current 13 tests: 13 passed in 12.90 s. No
complete H3000 engineering run was added; late native charging/F transitions
therefore remain a coverage limit, not a fabricated validation result.

The first full DM command failed one model test because its shell omitted the
configured venv PATH, making `ninja` unavailable. The remaining 12 tests passed;
the configured PATH resolved the failure without source/toolchain modification.
The four recorded full DM test invocations took 14.20, 12.19, 12.24 and 11.89 s,
plus the Reviewer's 12.90 s. Each exercised 163 short native steps on engineering
seeds 976801/976802: **815 native engineering steps** over these five invocations,
separate from the 72k result-step ceiling. The injected test seed 976803 failed
before its first native step. Earlier eight controller tests and the small
non-native test subset add engineering costs; design, implementation and review
human/model wall/compute were not comprehensively metered. Nothing is counted
as a fit. The final source diff check is clean.

The selected execution uses two single-threaded workers on `wsl_4070`, subject
to actual native admission, output `runs/uav_radio_placement/b01_spatial_a01`.
Exact source publication precedes launch. Native-child observation follows the
published `f2c53785f` correction: arm the detached same-handle observer, keep
this native turn active through long deterministic waits and drain/rearm. A
queue registration is not proof of automatic child resumption. No changed
operation, duplicate launch, alternate App target or per-run Root ACK is used.

### Pre-launch node selection correction

Exact inputs were published at `28c036f2b0e2785fee77bf3b6f22e48964d5f1bf`.
The preferred remote node accepted SSH, but its GitHub TLS path was unavailable:
the first `git fetch` made no progress for approximately two minutes and only
that synchronization's exact processes were terminated; a second bounded fetch
exited 124 at 45 seconds, and an independent HTTPS request timed out at its
10-second connection limit. No launcher was called on that node, no scientific
claim exists there for this batch, and no result world was exposed. Its dirty
canonical index/outputs were not edited; a transferred but unapplied policy-row
patch is disposable scratch, not a policy override.

Select configured **local_linux** for this CPU-only batch under the previously
declared unavailable-node alternative. A preparatory read found approximately
10 GiB available memory, 16 logical CPUs and no local scientific worker. The
configured local interpreter/toolchain passed the engineering checks above.
All three arms remain on this one node with two workers/one numeric thread;
no arm, seed, search, native semantics or cost ceiling changes. Current published
policy and actual memory are still checked freshly by the native launcher.
This is an operational placement choice, not a retry of accepted scientific work.

### B01 accepted operation and observation

The fixed input snapshot was natively accepted. The original
[launch manifest](../../../../runs/uav_radio_placement/b01_spatial_a01/launch-manifest.json)
is the authority for source, node, command, native process identities and
same-operation reference. Its [resource preflight](../../../../runs/uav_radio_placement/b01_spatial_a01/admission-preflight.json)
passed with 11,171,889,152 effective available bytes against the 4 GiB floor.
No remote scientific attempt preceded it.

`tools/hmasd_wait.py` was armed on that original status handle for this native
child. The first generation-1 drain confirmed accepted, consistent records and
both runner/supervisor running; no terminal witness yet. The observer owner
remains this child, with long deterministic waits and checkpoint drain/rearm.
This is technical acceptance only. Full artifact collection, arithmetic and
choice reconstruction, adverse-inclusive interpretation and publication remain.

## 2026-09-28 UTC - B01 complete native reading

The original operation exited zero with a valid
[native witness](../../../../runs/uav_radio_placement/b01_spatial_a01/process-exit.json).
The same observer retained both its generation-1 checkpoint and READY event;
the child drained both, consumed them by generation-2 rearm, then stopped
observation because no job remained running. Its attempted App queue delivery
reported `-32600` for an unloaded spawned child; that did not lose the native
operation, change the handle or trigger a retry. Technical acceptance and
terminal evidence are distinct from the complete reading below.

All **24/24 episodes reached H3000**, giving **72,000 native team steps**, zero
partial/missing/duplicate worlds, zero fits/optimizer updates and **59,988
completed native-radio model invocations**. All eight initial-state/user-path/
RNG-stream digests matched across H/G/R. The independent
[artifact reader output](../../../../runs/uav_radio_placement/b01_spatial_a01/reading.json)
verified 27 artifacts, all 24 raw files, every native metric sum and mean, every
saved search choice/tie/F-fixed candidate and all full exogenous user paths.
The largest native reward arithmetic error was 2.220446049250313e-16. Full RNG
states were not retained, so those digests are runner evidence, not a second
offline reconstruction of the RNG stream. The error log is empty.

### Complete outcomes and adverse worlds

Panel means, with minimum battery being the minimum over the whole panel:

| Program | QoS/step | Native J | Return cost sum | Min battery | <=10% UAV-step share | Team xy km/episode | Consumed Wh/episode |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| H | .781669 | 2311.756747 | 1.337836 | .100411 | 0% | 129.121 | 1344.437 |
| G | .780285 | 2303.463838 | 3.409083 | .095769 | .520313% | 135.780 | 1356.990 |
| R | .809043 | 2373.402321 | 11.576521 | .088559 | 2.060938% | 99.006 | 1296.313 |

Primary R-G: QoS **+.028758** [+.009323,+.048194], 8/8 positive; native J
**+69.938482** [+3.052642,+136.824323], 7/8 positive. Secondary R-H: QoS
**+.027374** [+.002805,+.051944], 7/8 positive; J **+61.645574**
[-10.641620,+133.932767], 7/8 positive. G-H: QoS **-.001384**
[-.026418,+.023650], 5 wins/3 losses; J **-8.292909** [-83.594425,+67.008608],
4 wins/4 losses. Brackets are descriptive paired t7 intervals over the eight
worlds; there is no training replication, equivalence or tail guarantee.

Every signed primary and anchor outcome is retained here and in
[per-world outputs](../../../../runs/uav_radio_placement/b01_spatial_a01/perworld.json):

| Seed | R-G QoS | R-G J | R-H QoS | R-H J | R minimum battery | R <=10% share |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 36092801 | +.012941 | -2.074787 | +.020783 | +6.204292 | .090474 | 5.708333% |
| 36092802 | +.061206 | +183.852253 | +.058599 | +176.068249 | .101381 | 0% |
| 36092803 | +.020417 | +33.858757 | +.072891 | +187.495776 | .093190 | 3.908333% |
| 36092804 | +.000505 | +2.693504 | +.000784 | +2.496381 | .101083 | 0% |
| 36092805 | +.034327 | +28.384245 | +.034782 | +29.680830 | .088559 | 6.870833% |
| 36092806 | +.038787 | +114.618775 | -.015450 | -50.537545 | .100400 | 0% |
| 36092807 | +.003820 | +11.345689 | +.010524 | +31.802489 | .100246 | 0% |
| 36092808 | +.058063 | +186.829423 | +.036083 | +109.954118 | .100559 | 0% |

R-G return-cost difference is +8.167438 [-4.088248,+20.423124]; R-H is
+10.238685 [-2.366556,+22.843926]. Mean episode minimum battery is lower
under R than H by .005130 [-.009303,-.000957]. Reserve exposure is materially
present even though its paired mean interval crosses zero. In 36092801 the
extra service is outweighed by +20.449964 return cost versus G, producing the
J loss. In 36092805 R's cost is 38.421501 versus H 1.088626/G 1.123670, and
the panel's worst battery/reserve outcome occurs. R also worsens the low tail
in 36092803. Conversely, R removes G's 1.770833% reserve exposure in 36092808;
this favorable world is not discarded. All 24 episodes have zero native
cutoff/depletion events and zero decoded cutoff share; none of this establishes
safety. G's large losses in 36092806 (J -165.156320 versus H) and 36092808
(-76.875306) remain part of its near-zero mean, not ignorable optimizer noise.

The additional energy cost already enters native J at coefficient two; query
CPU is **not** priced by that reward. Native J has not been reconstructed from
the planner score. Delivered mean traffic is H/G/R 23.450069/23.408555/24.271303
Mbps. Graph-potential sums are approximately -30.575 in all arms. R's total
consumption is lower than both references despite its worse low-battery tail:
less aggregate energy/path is not a risk-sufficiency argument.

### Intermediate readings, scope and actual cost

Within R's own decision states, selected static QoS exceeds its H/G initial
candidate score by .065397/.062072 on average; strict >1e-10 gains occur in
55.75/48.75 of 100 clocks per world. Selected-score means on each program's
own states are H .882722, G .857919, R .944857. These are endogenous static
snapshots with fresh association, not paired executed counterfactuals or a
causal mediation decomposition.

Fixed first/middle/last-third QoS is H [.801129,.845517,.698360], G
[.827261,.842274,.671321], R [.828202,.905178,.693751]. R's largest mean
service increment is in the middle third; the last-third R-H mean is negative.
Mean F-mode UAV-step fractions are H .337745/G .341620/R .288406, and charging
UAV-steps are 1288.375/1356.625/1113.5 per episode. Mean guard blocks are
885.125/919.625/1024.25; negative-margin shares are .317708%/1.211979%/2.833854%.
Mean zero-service steps and longest zero-service gaps are 9.875/9.875/10.000.
No post-hoc threshold, return-window alignment or difficult-world deletion is
used to select a preferred comparison.

Retained endpoint changes provide a descriptive motion-accounting check, not
a mechanism claim: between the 99 adjacent clocks, count a member changed if
both xyz endpoints are finite and differ by >1e-6 m, or finite/absent status
changes. H/G/R average 568.375/570.000/299.000 changed member endpoints and
97.625/96.625/59.750 changed clocks per episode. R's F endpoints are current
positions whereas H/G use absent targets, so this count is not a matched
target-switching estimand. The actual path is the common physical measure:
R-G xy distance -36.774 km/episode [-47.085,-26.462], R-H -30.115 km
[-44.905,-15.324]; full xyz means are 130.125/136.866/99.207 km.

The accepted-to-exit duration was **41.79 min**, including startup; runner
wall was 2503.359 s (41.72 min). Summed worker CPU was 4955.342 s (**1.3765 h**),
summed worker wall 4985.377 s, and maximum worker peak RSS 483,884 KiB. Mean
per-episode worker CPU H/G/R was 155.907/172.496/291.014 s; R costs 68.7%
more than G and 86.7% more than H on this node. Mean planning CPU alone was
1.463/2.226/108.752 s, including H/G diagnostic queries. Total queries are
H 800, G 800, R 58,388, below the 81,600 limit because F members are not
searched. Exactly 14,400 k-means solves occurred; full actual Lloyd iteration
counts remain unmeasured as declared. The 815 short native engineering steps,
failed local tool-path invocation, failed remote source synchronization and
unmetered design/review/reading/publication effort are additional, not zero-cost
because the study has no fit.

One necessary raw copy remains at
`/home/fires/hmasd-wsl/runs/uav_radio_placement/b01_spatial_a01/raw/` on configured
`local_linux`: 24 NPZ files, **50,482,280 content bytes** (50,524,160 allocated).
Their byte counts/digests are in the compact
[manifest](../../../../runs/uav_radio_placement/b01_spatial_a01/manifest.json).
Git receives compact config, all per-world/aggregate readings, native identities
and the verification, not these bulk arrays. Nothing has been spliced from old
comparators or rerun. This complete mixed result now receives focused independent
scientific review before the final direction/claim disposition.

### Independent scientific reading and DM disposition

Registered ResearchCritic `/root/dm_radio_placement/placement_result_critic`
worked in a separate context without DM/Root conversation inheritance. Its
task/navigation context included summaries, so it explicitly does not claim
blinding. It first reconstructed the new original results, independently read
all 24 NPZ files and exactly reproduced all 48 QoS/J scalars, then compared
the prospective branches, original contrary evidence and the newly published
`uav_energy_coordination` B01. It ran no environment or new experiment.

Its recommendation is **revise: retain R as a conditional ordinary-control
asset, keep H as the current default reference, stop automatic expansion of
this recipe**. `MATERIAL_DISSENT: no`. The static-and-complete mean direction
prediction is realized, but the acceptable-risk use condition is not supported.
There was no predeclared numerical safety threshold; neither Reviewer nor DM
invents one after seeing the result. Service, throughput and J are related
readings, not three independent successes. The R-H J interval crossing zero
and all signed adverse worlds remain visible.

The Reviewer sharpened the tail interpretation with retained raw observations.
R worlds 36092801/03/05 spend 1370/938/1649 UAV-steps at/below .10, beginning
at transitions 2784/2849/2742, and each has seven members still below .10 in
the final transition. DM reproduced those counts exactly. All three R final
observations have queue [0,6] and occupancy [0,1]. The corresponding H queues
also have six members, yet no reserve crossing; queue presence alone is not
an explanation. The fixed final-thousand R-H service mean is -.004610,
negative in five worlds. No extended episode is needed to preserve this
already observed un-recovered endpoint risk; the experiment makes no claim
about the unobserved continuation.

Total consumption/path savings also do not imply better remaining stored
energy. Mean charger input is H 357.881944 versus R 309.305556 Wh, so input
minus consumption is -986.554882 versus -987.007264 Wh. Native input is actual
charge delivered, clipped at available capacity (`energy_aware.py:1805-1816`);
the subtraction is an energy-balance reading, not identification of why the
individual deficits arise. Native return cost takes the worst member, so
lower team consumption and a deeper local risk tail are compatible.

The Reviewer counted R's 800 selected layouts: pattern 371, carried_R 340,
current 59, H 30 (G zero). This supports actual finite search and leaves
ordinary target stability/holding as a simple contributor alongside radio
alignment and expanded spatial support. It does not identify a pure objective,
predictive-model or cooperation mechanism. Original H geometry is not the
endpoint of achieved mean service in this panel; G's near-zero mean does not
establish equivalence, exhaust clustering improvements or localize all remaining
loss away from geometry. Existing B04/B05 conditional gains and adverse tails,
B03 assignment caveats and the one-fit B02 negative remain intact.

DM adopts these recommendations in full. Keep the bounded exploratory
[claim card](CLAIM_finite_radio_placement.md), exact executable comparison,
complete positive/adverse raw evidence and H as the default anchor. **End B01
investment and set this direction to reserve at the assigned return boundary.**
There is no active worker, unread output, selected fit, automatic replication,
forecaster, charging repair, local-sensing conversion or search-budget expansion.
The broader allocation of future questions belongs to Root, not to an invented
approval dependency or recurring check in this direction.

One distinct unselected opportunity goes back to Root: if the project needs
to choose its next ordinary comparator, compare frozen I and R on the same
new worlds. The Reviewer's minimal proposal is eight new worlds, I/R keeping
their own 60/30-step clocks, 16 H3000 episodes/48k steps/0 fits; roughly 1.11
worker-hours and 222k radio calls are historical extrapolations, not a new
admitted budget. It is a full-program comparison, not pure time-model causality,
and should be merged/selected against the already proposed I/P question by
Root. Different existing world panels cannot rank I above R. No such study is
selected or run here; retaining these results with no further run is also a
valid current outcome.

### Retention and measured cleanup

All native processes are absent and observation is stopped. The 24 required
raw files remain in the one location above; reusable tested implementation and
checks remain, with compact readings and adverse evidence published. No copy,
archive or backup chain was made for cleanup.

Deleted exact disposable targets: this direction's `temp/directions/` subtree
(the unapplied published-row patch and stopped-observer request), its two
implementation `__pycache__` directories and test `__pycache__`, plus remote
`/tmp/uav_radio_placement-admission-28c036f2b.patch`. Local allocated usage went
from 126,976 bytes to zero; the remote patch from 4,096 bytes to absent, with
absence verified. **Net reclaimed: 131,072 allocated bytes.**

Source-snapshot reclamation is separately blocked, not completed. The exact
launcher snapshot `5d429c7d3527454993ff7eca765b0226` retains **1,604,083,712
allocated bytes**. The supported GC preview first refused inspection of
`/proc/383/cwd`; its documented elevated read-only scan then refused because
process 2019 changed during reference inspection. A read-only `ps` shows that
process is a defunct zsh. The DM did not modify the shared collector, kill an
unowned process or force-remove the snapshot. This is a concrete tool blocker
for Root's shared-control ownership, not an incomplete scientific result or
permission to retry the experiment.

### Exact source-snapshot cleanup completed (2026-09-28 06:42 UTC)

Root's bounded follow-up authorized only the remaining snapshot cleanup after
published shared repair `311247eb629f5dbe05c2e6fd59df4cee867c1b02`. The DM read
the repair and reused Root's independent engineering review: the scanner may
clear a zombie only after confirming the same start identity, state Z and
exactly the leader task; surviving or unreadable tasks still refuse cleanup.
The reported shared-tool checks were 40 full-suite and nine independent focused
passes. No new scientific comparison, environment episode or fit was selected
or executed for this follow-up.

Fresh supported preview, with `--snapshot 5d429c7d3527454993ff7eca765b0226
--sudo-process-scan`, returned eligible. This rescanned the actual current
processes rather than assuming the old PID 2019 state. It verified the exact
claim `658077535eececf3833726c0a34f21a1febd1fee76bc7c8109e02cb547dd8ed0`,
valid terminal records, source SHA `8ec998ecac68f93697ab31c65d5732ab337f4203`,
clean snapshot and durable `refs/heads/main` reachability. The subsequent
supported `--apply` for this same ID repeated those checks under its admission
lock and returned `removed: true` (exit 0); the short main writer lock also
serialized its Git worktree mutation. The elevated option was only the
supported read-only process scan. No process was killed or refusal bypassed.

Deleted exact path:
`/home/fires/hmasd-wsl/.git/hmasd-launch-sources/5d429c7d3527454993ff7eca765b0226`.
Immediately before deletion, `du -s -B1` measured **1,604,083,712 allocated
bytes**; afterward the path is absent and its Git worktree registration is gone.
All 12 other launch-snapshot registrations present before this operation remain
unchanged. **This follow-up reclaimed 1,604,083,712 allocated bytes; cumulative
direction cleanup reclaimed 1,604,214,784 bytes**, including the previously
recorded 131,072 bytes. The earlier refusal above is preserved as historical
evidence and is now resolved for this exact target, not generalized to others.

The one required raw location remains untouched at **50,524,160 allocated
bytes**. Post-deletion SHA-256 verification against the published manifest
passed for all 24 raw NPZ files and all three listed compact result artifacts
(27/27). No raw evidence, operation record, other snapshot, reusable code or
test was deleted, and no backup copy was created. Scientific readings, the
conditional R claim and the reserve standing are unchanged. Cleanup has no
remaining blocker or selected follow-on action in this direction.
