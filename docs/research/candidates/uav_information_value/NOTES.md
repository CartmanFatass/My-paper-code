# UAV actionable information value

## 2026-09-28 - Initial evidence reconstruction and proposed complete comparison

Native DM child `/root/dm_information_value`, assigned by Root task
`01a0e560-4333-7b03-8ff3-759a4add1d9a`, authoring shared `main` at
`/home/fires/hmasd-wsl`. Owned direction: `uav_information_value`. This first
assignment is reasoning and design only: **0 fits, 0 new environment transitions,
0 evaluations, 0 result-bearing diagnostics, and no implementation or launch**.
Existing compact results and code were read; no accepted historical operation or
archived DM was resumed. Root owns the initial index registration and the initial
independent, context-isolated scientific review of the three assigned questions.
The proposal below is a concrete recommendation for that review and task boundary,
not an accepted execution contract. No duplicate critic or Pro request was made.

### Question and changed explanation

What part of the native UAV ordinary central/local service difference comes from
the position information supplied to an otherwise common decision rule, and how
much can a competent ordinary controller recover from lawful observation history?
The intended contribution is empirical understanding of actionable information on
this host. An algorithmic novelty or a learned encoder is not required.

The original approximately .18 QoS difference is a useful phenomenon, but it is
not an identified information deficit. In addition to seeing more positions,
`H_central` and `H_local` construct their point sets differently; ordering enters
k-means initialization, while missing users or a missing BS change the local
planner's target generation and search. The source inspection also identifies a
specific lawful memory opportunity: a stationary BS can be forgotten by the
environment's replacement cache and by the current planner. For moving users,
memory has a different scope: short-term prediction from repeated anonymous
positions is possible, but unobserved users and newly sampled waypoints are not
made observable by retaining history. These are code-supported distinctions,
**not measurements of how often each matters or of recoverable service**.

Published background was checked at `27551e616e874a1cbc9dc380e3d358c5ed2d097b`
(`HEAD == origin/main` after fetch). [RESEARCH sections 2, 3, 6 and 8](../../RESEARCH.md#研究背景与共享认识)
change the proposed comparison in concrete ways: use pooled legal observations as
the deployment contract; keep a competent ordinary joint planner; compare native
closed-loop outcomes; do not equate a privileged reference with an optimal upper
bound; and retain feedback-induced state changes in the estimand. Section 6's
failed immediate-replanning prediction argues against substituting another clock
repair for this information question. Section 2's finite-model results concern a
different fixed small host, latent-parameter particles and decision sampler. They
do not establish a UAV information effect or justify reopening that closed route.
Likewise, transport/payload studies with pending messages do not map to the present
pooled controller's free observation input: this study does not invent a message
latency, bandwidth constraint or hidden model to make learning necessary.

### Original supporting and adverse evidence

- Benchmark B01, source `e1fdbe72f53a1597c34c1d32c89ac6700251dca0`, selected H1
  centrally on eight development worlds from H1/H2/H3. Its fixed S2 comparison
  reports `H_central=.7740241283`, `H_local=.5969387490`, difference
  `+.1770853793` QoS/step. Native J is `2281.8874` versus `1628.4463`.
  `H_local` inherited the central selection; it was not independently optimized
  under equal local development. The earlier Pro/reviewer correction already
  rejected the causal labels "information gap" and "learning gap".
  [B01 reading](../energy_relay_benchmark/b01_ref_a02_readings.json),
  [original result and interpretation](../energy_relay_benchmark/NOTES.md#2026-09-26--b01-result-read-by-the-pre-registered-branches-operation-02f762d2-tag-b01_ref_a02).
- Stage 1's final SET instance reaches `.437/.438` development QoS and remains
  below both ordinary references. SET has held central state plus pooled
  observations, so its shortfall is not evidence that legal history cannot work.
  Its resumed training lineage and the subsequently exposed 957001-957032 panel
  are retained as development knowledge, not fresh replication or an untouched
  evaluation set for this direction.
  [Stage 1 result and independent corrections](../energy_relay_benchmark/NOTES.md#2026-09-27--stage-1-result-one-set-development-fit-at-fixed-exposure-read-by-the-pre-registered-readings-b02_s1_set_a01--b02_s1_set_a01r-final-model-c06-957001957032-read-once).
- Availability B01, source `8f638f44b1d0565ef62027d5f467a113be6a730f`, preserves
  the gap on S4: central-minus-local QoS is `+.1746372` without failures and
  `+.1779084` with native failures; respective paired t95 intervals are
  `[+.1203946,+.2288798]` and `[+.1323680,+.2234489]`. The gap interaction
  `.0032712 [-.0661874,+.0727299]` does not establish equivalence across regimes.
  Off/local world 965017 has zero complete service; on world 966030 slightly
  favors local. This is a program comparison, not an information upper bound.
  [Original summary](../../../../runs/energy_relay_availability/b01_s4_refs_a01/summary.json),
  [full reading and adverse worlds](../energy_relay_availability/NOTES.md#2026-09-27--b01-complete-native-reading).
- Availability B02, source `b4c7b153775222414375da4fda27b25e3c5363a8`, actually
  removed observed availability-to-replan waiting (14.38 to zero decisions), but
  complete QoS changed by `-.0131722 [-.0489509,+.0226065]` and J by
  `-29.6855 [-203.9143,+144.5432]`. Extra spatial refresh and zero planning
  delay did not establish a mean service gain. This weakens a generic stale-clock
  story without refuting history or useful sensing.
  [Original summary](../../../../runs/energy_relay_availability/b02_event_replan_a01/summary.json),
  [activation, losses and disposition](../energy_relay_availability/NOTES.md#2026-09-27--b02-complete-native-reading).

### Actual information and decision contract

The following is reconstructed from code at the published revision above, with
load-bearing implementations linked here:
[planner](https://github.com/CartmanFatass/My-paper-code/blob/27551e616e874a1cbc9dc380e3d358c5ed2d097b/experiments/candidates/energy_relay_benchmark/b01/heuristic.py),
[observation decoder](https://github.com/CartmanFatass/My-paper-code/blob/27551e616e874a1cbc9dc380e3d358c5ed2d097b/experiments/candidates/energy_relay_benchmark/b01/observation.py),
[controller/evaluator](https://github.com/CartmanFatass/My-paper-code/blob/27551e616e874a1cbc9dc380e3d358c5ed2d097b/experiments/candidates/energy_relay_benchmark/b01/evaluation.py),
[local sensing](https://github.com/CartmanFatass/My-paper-code/blob/27551e616e874a1cbc9dc380e3d358c5ed2d097b/envs/pettingzoo/relay/local_view.py),
[mobility, observations and BS cache](https://github.com/CartmanFatass/My-paper-code/blob/27551e616e874a1cbc9dc380e3d358c5ed2d097b/envs/pettingzoo/relay/routed_core.py),
[energy suffix and station prior](https://github.com/CartmanFatass/My-paper-code/blob/27551e616e874a1cbc9dc380e3d358c5ed2d097b/envs/pettingzoo/relay/energy_aware.py).

| Fact | What is legally available | What history can and cannot recover |
| --- | --- | --- |
| Current users | Up to all 30 users within each UAV's 1500 m 3-D radius; anonymous distance-sorted slots, relative xy, link/service fields. Pooling all eight observations is the existing local-reference contract. | Repeated detections can support association and velocity estimation. There are no true user IDs, velocities, cluster assignments or future targets in these slots. A slot index is not a persistent identity. |
| Observed absence | With 30 slots for 30 users there is no capacity truncation of this host's in-range user list. Empty areas inside the union of current sensing footprints supply negative evidence, subject to the existing zero-record sentinel and geometric dedup approximation. | Absence outside that union is unknown. Do not delete an unseen user merely because it is not in the current union, or treat an unmatched extrapolation as an identified entity. |
| BS position | Current radius-gated BS slots or the shared cache; one BS is static during a world. The cache is replaced at synchronization by what some UAV currently sees, and is reset between worlds. | A previously observed BS can be retained exactly up to observation precision. A never-observed BS remains unknown; station geometry gives a prior, not its exact coordinate. |
| UAV and station state | The energy suffix supplies all eight UAV positions, batteries, availability, return/dock state and station records without radius gating. Own observations also expose current backhaul/load. | These current facts are already lawful. Do not hide them, relabel them as a belief-learning target, or give a candidate new access. |
| Initial demand geography | Station 1 is sampled around the initial mean user position, with up to 960 m component-wise jitter plus clipping/separation rules; station 0 is near `.7*BS + .3*initial_user_mean`. | These are useful public priors already exploited by H_local's 1000 m station-1 search ring. They do not reveal each user, exact current mean, or later migration. |
| User motion and future uncertainty | S2 uses RPGM with user speed at most 3 m/s, hidden piecewise velocity, random new targets and pauses; cluster centers also move. | A short observed trajectory can estimate ongoing motion and bounds displacement by `3*age` m. It cannot identify a newly sampled target before informative feedback, and cluster membership may change. |
| Planner representation | H1 uses six service centroids and two relay targets, relay-first priority, Hungarian distance assignment with 300 m prior-target hysteresis, 30-step replanning, 100 m altitude and 30 m/s cruise. | This is stateful even without a measurement memory. Local input is deduplicated within .5 m and sorted by xy; central input retains environment user order, initially grouped by cluster. `linspace` index seeding makes this difference decision-relevant in principle. |

`H_central` reads only true current user/BS xy at replans. It does not plan from
true user velocity, future demand, future failures or a solved optimal policy.
The common native shield and guard remain part of every controller package. Users,
relays, routing and return trajectories interact: a motion that reveals demand can
also break backhaul or consume battery. Counting newly seen users alone cannot
establish useful information-seeking behavior.

### Recommended first complete comparison

Recommend **one zero-fit S2/H3000 ordinary-control study**, with a common H1 planner
and four crossed position-source conditions, one original-reference bridge and
one lawful-history candidate. S2 is the original .177-gap host; it avoids adding
a fault/mobility factor merely because S4 is available. The original native S2
reward, dynamics, sensing radius, observations, communication convention, actions,
shield and guard remain unchanged. There is no learned decoder, learned value
ranker, selected new sensor or modified fault process. Claude's pre-first-shield
learned relational decoder is outside this study.

| Arm | User point input at 30-step replans | BS input | Role |
| --- | --- | --- | --- |
| `L = V00` | Current pooled legal detections | Current legal observed/cached record | Matched ordinary deployment baseline, preserving H_local behavior |
| `U = V10` | True current user xy | Current legal observed/cached record | Isolate the user-position source change under the same planner |
| `B = V01` | Current pooled legal detections | True BS xy | Isolate the BS-position source change under the same planner |
| `F = V11` | True current user xy | True BS xy | Joint privileged source reference under the same planner |
| `R` | Original central array input and original preprocessing | True BS xy | Reproduce the old H_central package on this fresh panel |
| `H` | Current detections plus bounded ordinary history estimates | Last legally observed BS, retained within the world | Test attainable ordinary history recovery under the L information rights |

For L/U/B/F/H the planner receives the same anonymous point-set interface and
applies one explicit deduplication/sorting rule before identical k-means,
target generation, fallback search, matching and primitive control. No signal
label selects a different search or assignment algorithm. L's existing sorted,
deduplicated inputs and inherited H1 behavior must be retained; supplied equal
point sets and BS inputs must produce equal plans regardless of arm label. The
common rule keeps the original .5 m geometric merge convention and xy ordering;
true-xy arms have no user identity, index order, velocity or cluster metadata.
The estimand is the effect of the **position source**, including its coordinate
fidelity, not a separate estimate of pure visibility loss. R minus F measures the
specific original preprocessing/representation difference, not every conceivable
planner improvement. If implementing the common path changes L's semantics, that
is a design deviation to fix or explicitly redesign before a result launch.

H uses no additional observations or communication. It may assimilate the
already delivered legal observations at every primitive step, while acting on
the same 30-step replanning clock. Its ordinary starting proposal is gated
minimum-distance association of anonymous detections, clamped finite-difference
velocity estimates, and constant-velocity extrapolation for at most one replan
interval (30 steps, hence at most 90 m S2 travel). Current detections have priority;
at most 30 point hypotheses are passed downstream. Track IDs are internal
bookkeeping, never simulator user IDs. Negative observations and ambiguous
associations must be handled explicitly; a stale point cannot silently become an
extra known user. BS retention clears at reset. The exact association/retirement
semantics require an L0 and engineering review before implementation acceptance;
these unresolved choices are a real engineering cost of the six-arm proposal.
This is a practical ordinary-estimator package, not an optimal Bayesian filter or
a claim that full legal history has been exhausted. No hyperparameter sweep is
selected. A history loss would not refute all history-based control.

Use **32 fresh paired initial world seeds across all six fixed programs**:
192 native complete episodes, at most **576,000 team transitions**, **0 fits and
0 optimizer updates**. Fix the actual seed list and all code before execution;
this design-only return reserves no launch and exposes no new world. All prior
benchmark/availability panels and their reported adverse worlds are development
knowledge. There is no selection of the best arm/checkpoint/seed after this panel,
no automatic extension, and no confirmation claim. Pair by actual initial seed;
do not assume the subsequent RNG or closed-loop trajectories remain identical.

### Estimands, predictions and limits

The primary readings are all four conditional position-source contrasts:
`V10-V00`, `V11-V01`, `V01-V00`, `V11-V10`, plus the interaction
`I = V11-V10-V01+V00`. Report QoS/step and native J for each, with world-level
paired uncertainty and every adverse world. `R-F` reads the representation bridge;
`H-L` reads lawful recovery. The identity
`R-L = (R-F) + (F-L)` is a decomposition of these fixed programs' closed-loop
outcomes. It does not identify nonnegative information/learning gaps between
optimal policy classes. The interaction prevents assigning a unique additive
percentage of the old gap to users versus BS.

Keep native return-cost components, minimum battery, cutoff/depletion,
zero-service worlds, first service, total service and throughput, and full episode
length/termination. Useful intermediate records are the number of current versus
estimated user points, estimate ages, known-BS omissions, fallback-search use and
executed targets. An evaluator-only record may identify actual observation
coverage and geometric estimation errors, but true identities/positions must
never flow back into H or L. These are supporting descriptive readings; lower
position error or less fallback is not itself a native benefit. Do not fit an
information-gain surrogate or run counterfactual suffixes in this batch.

Working prediction, not an established fact: the canonical full-source arm retains
a positive service advantage over L, with user/BS contributions potentially
complementary; H reduces known-BS omissions and the loss of recently observed
demand, and may recover some complete service. The stronger ordinary alternative
is that a substantial part of the old gap comes from k-means initialization and
search behavior, or that recent-history retention is not the missing actionable
quantity. Fixed heuristics can be hurt by extra information, so no nonnegativity
claim is imposed on these contrasts.

- If R-F accounts for much of the observed R-L difference, prioritize the
  ordinary representation explanation; a new neural memory would have weak
  support from this phenomenon.
- If user-source gains remain with either BS condition while BS-source gains
  are small, focus the explanation on observed demand geometry under this rule.
  If BS dominates, exact static memory or discovery is the simpler candidate.
  A large interaction instead points to joint access/backhaul information use.
- If H improves complete service/J with acceptable measured risk, retain it as
  conditional ordinary recovery; the BS/user crossed effects describe where
  privilege helped, but do not causally split H's two memory components.
- If privilege helps but H does not, the current estimator/recovery route is
  unresolved or adverse. Do not automatically purchase tracker tuning, an RNN,
  another clock repair or a learned decoder. Compare the remaining information
  type with the cost of a direct complete alternative before another study.
- If the contrasts are imprecise, mixed or technically incomplete, report that
  result. It would not establish zero information value or close the parent
  question by itself. A complete but uninformative study can still justify
  declining further investment at its observed cost.

Information-seeking actions are a possible later comparison, not another active
idea here. They would have to trade sensing visits against service, backhaul and
energy using the same legal priors; no new observation radius or reward bonus is
needed. This six-arm study does not measure their value. In particular, a
history failure for never-seen demand cannot establish that exploration is useful,
and a privileged gain is not an achievable exploration upper bound.

### Cost, uncertainty and boundary return

Availability B01's 128 H3000 episodes took 46.03 runner minutes / 47.31 accepted
operation minutes and 3.10 worker CPU hours on `wsl_4070` with four workers. Scaling
only for a planning estimate gives roughly 70 minutes / 4.65 CPU hours for 192
episodes before extra tracking/readout; budget **about 70-120 wall minutes**, with
contention and S2 throughput explicitly unmeasured. Prefer that configured node;
fresh admission belongs to a later actual launch. Engineering/review/readback
cost is additional and likely dominates this study's intellectual uncertainty.
The main risks are anonymous-track ambiguity, false retained points, numeric
preprocessing drift, and attributing closed-loop information effects to optimal
VoI. Compact per-world readings and one required raw copy would be sufficient;
no bulk copies or new record type are proposed.

Compared with another neural fit, this study directly tests the interpretation of
an already consequential ordinary gap at zero training cost and preserves the
joint motion/backhaul decision. Compared with a two-arm true/local repetition,
the crossed source conditions separate two qualitatively different unknowns and
the reference bridge tests a concrete package confound. Compared with an exhaustive
planner/memory search, it is one fixed complete comparison and can return a
negative or uninformative answer. A narrower five-arm version omitting H would
answer attribution but defer lawful recovery; that is a legitimate cost reduction
if the independent review judges the currently unresolved tracker design too
speculative, not a mandatory diagnostic gate before any future method.

Current recommendation: retain the assigned information question and put this
bounded ordinary comparison to Root's commissioned scientific review. Do not yet
claim an information bottleneck, fund a new encoder, or interpret the old .18 gap
as achievable recovery. The first assigned reasoning boundary ends with this
design. Root owns synthesis and the next task choice; a later in-scope execution
assignment will carry the resolved comparison, code/review, published inputs and
native admission. No worker, observer, accepted handle, fit or run output exists
for this new direction, and no cleanup target or reclaimed disk space is claimed.

## 2026-09-28 - Independent scientific challenge adopted: static memory first

Root relayed the provisional recommendation of its already commissioned,
context-isolated Scientific Reviewer: the six-arm comparison is a useful complete
observation, but its first lawful-history arm should permanently retain a BS
coordinate once legally seen and omit anonymous user tracking. Root will retain
the completed review in the existing project record. This is the same initial
review, not an additional consultation, new permission requirement or run approval.

**Adopted. This entry supersedes H's moving-user tracker and the associated H
predictions in the initial proposal.** The effective six arms for the design
return are L/U/B/F/R as above and **H_BS**: current pooled legal user points exactly
as in L; BS position taken from the current legal record when present, otherwise
from the last BS position legally seen in this world. Assimilate observations
already delivered at each primitive step; clear memory before every reset; act on
the unchanged 30-step H1 replan clock. There is one static BS, so no identity
association, motion estimate or learned parameter is required. Station records
remain available to every arm. H_BS never infers a never-seen BS from privileged
state, random seeds or station coordinates.

This is a substantive improvement to the first comparison. The code demonstrates
replacement of an observed static fact, whereas the value and reliability of
moving anonymous-user history remain conjectures. The originally proposed tracker
would add up to **96,000 primitive-step association/update cycles** in its 32 H3000
episodes, plus deterministic gates, ambiguous crossing/tie handling, births,
expiry, negative-observation handling, duplicate prevention and checks that no
simulator identity leaked into the estimates. Those are real implementation,
review, CPU and interpretation costs even with zero fits; none has been measured
or incurred. A static-coordinate memory requires none of that machinery. The
dominant remaining work is a common planner/input adapter, information-isolation
checks, native six-arm runner/readout and review. No exact implementation wall
time is claimed before that bounded code task exists.

The ordinary recovery contrast is now **H_BS-L**. B-L supplies true BS information
even before any legal sighting; H_BS-L can recover only loss after a legal sighting.
Report first legal BS sighting, plans where the legal slot is absent despite an
earlier sighting, retained-coordinate use and complete native consequences. If
memory is never used, that is nonactivation of this specific route on the sampled
closed-loop trajectories, not a negative finding about useful active memory.
Working prediction: H_BS eliminates known-BS omissions at replans and improves
complete service only if those omissions matter to this H1 deployment. The first
clause is an implementation consequence; the second remains a scientific
prediction. A favorable memory score alone does not establish its effect on user
search, and unchanged/worse service would weaken this memory mechanism's practical
value without refuting the user-information opportunity.

All crossed-source effects and their interaction remain **total consequences of
fixed policy programs**. Different positions, sensing footprints, routing and
energy use after the intervention are part of the outcome; they are not removed
by matching initial seeds. The crossed comparison identifies neither a common
state's one-step causal value nor an optimal information bound. H_BS and B may
reach different states even after each knows its own world's BS, so B-H_BS cannot
be interpreted as a time-local cost of the initial unknown interval.

The cost remains one fixed proposal: **6 programs x 32 fresh initial seeds x up to
3000 transitions = 192 episodes / at most 576,000 team steps; 0 fits and 0 updates**.
The 70-120 minute node-wall estimate remains conservative and unmeasured; tracker
cost is removed, not transferred to a later mandatory study. The question about
moving-demand history or active sensing stays open in the reasoning above, with
no selected follow-on. The final recommendation is this six-arm static-memory
version, subject to Root's synthesis of the completed initial review. The current
assignment still ends at design publication, with no result execution or code.

## 2026-09-28 - B01 selected for implementation and execution; L0

Root's subsequent native assignment selects the final static-BS six-arm design and
the completed independent scientific review, which is being preserved at
`docs/research/archive/2026-09-28/RESEARCH-native-dm-question-review.md`. The review
retains this question and the complete comparison. This is the next assignment,
not a launch under the earlier reasoning-only scope. No additional scientific
review is required for the unchanged selection. The current RESEARCH entry is
`exploring`, exact lead `Codex DM (native child)`; the owner pause remains lifted.

Freeze B01 as **L, U, B, F, R, H_BS**, all on fresh initial seeds
**28100101-28100132**, S7-S2/H3000: 192 complete episodes, at most 576,000 team
transitions, 0 fits/optimizer updates. These seeds were absent from the inspected
candidate sources and the new direction notebooks; no outcome on them has been
observed. All are exploratory development exposure once run. No tuning, extra
panel, extension, changed physical process or automatic retry is included.
Start with four CPU workers and one numeric thread each on `wsl_4070`, subject
to actual-node admission. Expected operation wall remains 70-120 minutes; record
actual cost. Native terminal failure stops new submissions, retains running-cell
collection and partial/failed records, and does not authorize a replacement.

L0 deliverable: an admitted `experiments/candidates/uav_information_value/run_b01.py`
with a direction-local controller adapter, fixed runner and readout. Reuse the
original `evaluate_world`, `make_eval_config`, production feedback and H1 motion/
assignment implementations. No shared evaluator, environment, heuristic or peer
direction edit. The current-user/full-user and legal-BS/true-BS replacements must
all enter one anonymous canonical point-set planner, while R uses the unchanged
original central controller. L must agree with the original local controller for
the same legal observations and controller state. Preserve original replan timing,
normal/mode handling, H1 parameters, reward, terminal rules and guard. H_BS retains
only actually delivered legal BS coordinates, updates between replans, and clears
at reset. L and H_BS never hold or read a raw-environment reference or central state.

One bounded Implementer owns only `controllers.py` and its matching
`test_controllers.py`: implement and verify these six controller information
contracts. The DM owns NOTES, batch/CLI/readout/observer code and their tests, all
Git mutations, launches and scientific reading. Both work on shared main and
preserve other writers; no helper writes shared files, commits, launches or spawns.

Checks: synthetic equal-input/canonical ordering, original-L/R parity, BS memory
between replans/reset/no-sighting, legal-source isolation, assignment/fallback
parity, effective native S2 configuration, fixed six-by-32 plan, true seed binding,
missing admission, finite metric serialization, exact world pairing/interaction
signs, and incomplete/failed/orphan handling. Small nonpanel native fixtures may
verify controller/evaluator wiring and RNG parity; they are engineering checks,
not selected research outcomes. Independent engineering review covers the actual
diff, information flow, evaluator identity, RNG and failure/persistence contract
before publication and launch.

Persist each complete native world row and every J/service/risk tail, compact
configuration/summary/source/status and hashes in Git; retain one raw trace copy
at the configured node. Record BS exposure/retention, current versus supplied
user counts and search/target behavior without feeding evaluator truth to legal
arms. Contrasts are the four conditional source changes, factorial interaction,
F-L, R-F, R-L and H_BS-L, computed by matched initial world seed; nominal paired
t95 intervals are exploratory and not multiplicity-adjusted. Partial batches
remain incomplete and never obtain a fabricated full-panel result.

### 2026-09-28 - Engineering counterexample resolves the local-identity conflict

Before any panel exposure or accepted launch, independent engineering Reviewer
`/root/dm_information_value/review_b01` found that the two intended input
invariants cannot both hold universally. Original `pooled_users` merges in
observation order and then sorts; the proposed full-source adapter sorted before
merging. For exactly the same unmerged decoded x coordinates
`[1000.4000068, 1000, 1000.8000135]` at y=1000, original legal pooling keeps one
point, while sort-then-merge keeps two and changes targets. The earlier equal-input
test accidentally hid this by premerging truth. This is a genuine representation
confound, not dismissed as a rare geometry.

Root resolves the conflict in favor of the already selected common canonical
preprocessing: **L/U/B/F/H_BS all sort the raw xy hits first, then greedily merge
within 0.5m; R remains exactly the original central controller.** Legal-source
arms begin with decoded present user slots, not original `pooled_users` output.
This also selects a potentially different float reconstruction among duplicate
observations. Universal exact identity of L with historical H_local is expressly
withdrawn. Original planner parity remains required when the supplied canonical
point sets coincide; native observer-off/on parity remains a correctness check.
The unmerged near-neighbor-chain counterexample becomes a regression test across
all five source adapters, with a legal-hit permutation check. No seed, arm, panel,
native physical rule, reward, shield, planner action rule or fit is added.

The four source contrasts and interaction still compare information sources under
one fixed preprocessing/planning program. F-L is the full-source consequence under
that program. **R-L is now explicitly original-central package versus canonical-
legal package**, not an exact recreation or a pure-information decomposition of
the old central/local gap. R-F remains the original-central/canonical-full bridge;
the historical local package is contextual evidence, not an extra measured arm.
H_BS-L tests legal static memory under the same canonical legal program. Root
adopts this correction without another scientific selection round because it
implements the selected common-preprocessing estimand; no launch has yet occurred.

The initial engineering pass otherwise found no material issue in admission/SHA
ordering, original evaluator/shield, seed binding, matched readout, failure stop,
partial/orphan retention and hashes. It ran 26 focused tests, all passing in
16.91s, but the counterexample still required correction. Its residual limits
were short native seed-17/H31 coverage, stubbed single-worker failure, and no abrupt
spawned-child death or destination-node execution check. These limits are retained.

### 2026-09-28 - Implementation accepted; exact inputs ready to publish

The DM read and accepts the bounded Implementer's controller/test work, with the
common-preprocessing correction above made by the DM after ownership returned.
The independent engineering Reviewer re-read that correction and independently
reran seven controller checks in memory, including the unmerged chain, equal
sources, permutation, leakage/reset and original-R checks: **no material finding
remains under the revised contract**. The DM's full configured scientific-Python
command covering this direction and original H1 tests passed **27 tests in
19.97s**, with 14 pre-existing dependency deprecation warnings. The corrected
native fixture verifies all six observer-off/on paths and the exact R anchor;
original-L parity applies only where preprocessing yields the same points.

Four test-suite invocations (including the Reviewer's first pass) executed twelve
31-step native correctness episodes each on nonpanel seed 17: 1,488 engineering
transitions, no fits or outcome-based method selection. Synthetic worker failures
and the 192-row synthetic persistence check execute no native transitions. None
of seeds 28100101-28100132 has been exposed. Abrupt spawned-worker death and the
destination-node runtime remain coverage limits, not fictitious test successes.
Failure accounting retains progress lower bounds and incomplete/orphan records;
missing results never receive zero surrogates or complete-panel contrasts.

Configured destination remains `wsl_4070`, four workers/one numerical thread.
The node's canonical checkout has unrelated dirty evidence and older control
prose; preserve all of it and its sparse selection. Fetch published source,
synchronize only this direction's published admission row under the node's short
writer lock, and let native admission check live resources. Root explicitly
accepted that narrow local control synchronization. The new global removal of
the fixed Codex track-count ceiling changes neither this study nor actual-node
resource admission. No result launch or retry has been made at this entry.

### 2026-09-28 - B01 accepted; same-handle observation armed

Exact published inputs: `ee9c6c8aca0ee13e3d7a02416ff4acf85766f274`.
The fixed B01 operation was accepted at 03:22:24 UTC through the configured
`wsl_4070` supervisor and native launch kernel. Its authoritative identity is the
[launch manifest](../../../../runs/uav_information_value/b01_sources_a01/launch-manifest.json),
with [fresh actual-node admission](../../../../runs/uav_information_value/b01_sources_a01/admission-preflight.json):
14,879,690,752 available physical/effective bytes against the 4,294,967,296 floor.
The initial native status and first detached observation agree: accepted, native
supervisor and runner running, no exit witness, no identity mismatch. This is
**active collection, not a read scientific result**; no extra arm or retry exists.

`tools/hmasd_wait.py` owns same-handle observation for this child runtime at
`/home/fires/.local/state/hmasd-wait/01a0e5da-116b-72f3-b158-476344637e06`,
generation 1, job `b01_sources_a01`, 1,500-second checkpoint window. Its first
drain adopted the accepted handle with zero probe errors; no wake was pending.
On a checkpoint rearm that same job without restarting the worker. On terminal
return, collect the declared complete or incomplete record, verify hashes/counts,
then interpret and publish. All raw scientific evidence remains on the configured
node during collection; only compact admission records have been copied here.

Node preparation left unrelated dirty source/evidence and sparse selection intact.
An initial non-login Git fetch was terminated after stalling; the configured
`zsh -lic` network path fetched successfully before launch. Its automatic-GC
warning about old bad tree `9e40125ee3e24973b69754649226d18847b45862` remains
unrepaired; current input and native snapshot preparation succeeded. A first
two-context-line control patch was refused with no change, then applied using
explicit zero-context allowance; only this published direction row was added.
These were prelaunch preparation events, not failed scientific episodes.
