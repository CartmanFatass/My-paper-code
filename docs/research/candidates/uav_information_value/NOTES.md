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

At the first checkpoint (03:49 UTC read), the same native operation remained
running with consistent process identities and zero observer probe errors.
The automatic Codex wake was **not delivered**: queue exited 1 with
`direct app-server input is not allowed for unloaded spawned sub-agents (code -32600)`.
No delivery to Root is inferred. The checkpoint was consumed and the same job
rearmed as generation 2; the worker was not restarted. Under Root's explicit
continuation, this child stays active through long deterministic waits, then
drains the existing observer. This is an observation-routing limitation, not a
scientific failure or permission to substitute an operation/address.

### 2026-09-28 - B01 complete: useful BS information, partial legal-memory recovery

The same operation exited **0 at 04:25:40 UTC**; native runner/supervisor were
absent with a valid exit witness and consistent identities. Generation 2's second
checkpoint was consumed/rearmed to generation 3 without restarting the worker.
Generation 3 observed READY at 04:25:51; its automatic queue had the same native-
child delivery rejection, so this active child drained it after its long wait.
READY was consumed, generation 4 had no live job, and observation was stopped.

**Complete evidence, not a partial-panel inference.** All 192 declared worlds
completed exactly H3000 by native truncation: 576,000 transitions, 0 fits and
optimizer updates, no failed/cancelled/unreconciled/unstarted cells, partial
transitions, orphan traces, pool errors or missing resource rows. On the node the
DM verified every one of the 387 manifest-listed files by size/SHA256, loaded all
192 raw traces, and exactly recomputed each native metric sum/mean and J, finite
values, terminal flags, 3,000-step lengths, 100 replan indices and memory-use
counts. Rebuilding the full summary from collected per-world rows was exactly
equal to the stored readout. The 32 seeds are now exposed development worlds.
Intentional null first-BS times mean no legal sighting, not lost instrumentation.

Primary evidence: [summary](../../../../runs/uav_information_value/b01_sources_a01/summary.json),
[all per-world readings](../../../../runs/uav_information_value/b01_sources_a01/perworld.json),
[frozen configuration](../../../../runs/uav_information_value/b01_sources_a01/config.json),
[manifest](../../../../runs/uav_information_value/b01_sources_a01/manifest.json),
[native exit](../../../../runs/uav_information_value/b01_sources_a01/process-exit.json) and
[terminal status](../../../../runs/uav_information_value/b01_sources_a01/terminal-status.json).
The manifest SHA256 is
`6903b1a2c692929f51b8a8e5c9ab6bfd0647a76bc60d3c12c97d791aa08a90bc`.
Its 384 raw/progress entries total 70,839,779 bytes; listed scientific artifacts
total 72,334,104 bytes. No raw trace copy was downloaded to the author checkout.

Native acceptance-to-exit elapsed was 3,796.25s (63.27 minutes); measured batch
wall after imports was 3,710.70s (61.84 minutes). Four single-numeric-thread workers
used 15,106.73 CPU seconds in total and 14,777.87 summed worker-wall seconds;
parent CPU was 5.82s. Largest individual worker peak RSS was 510,292 KiB, parent
peak 481,820 KiB, not simultaneous aggregate peaks. The six programs made 19,200
ordinary plans, 3,200 each. Engineering/tests, preparation, readback and scientific
review are additional cost; no speed claim treats those costs as zero.

All values below are over the same 32 initial worlds. The return cost is the
native capped cost per step; raw cost and every tail remain in the original files.

| Program | Mean QoS/step | Mean J | Mean return cost/step | Worst battery ratio | Zero-service worlds |
| --- | ---: | ---: | ---: | ---: | ---: |
| L | .576575 | 1550.602 | .024768 | .049753 | 1 |
| U | .597252 | 1596.862 | .027392 | .058970 | 1 |
| B | .734801 | 2154.360 | .003257 | .085710 | 0 |
| F | .771381 | 2220.701 | .010484 | .064841 | 0 |
| R | .780957 | 2288.452 | .003980 | .075393 | 0 |
| H_BS | .619966 | 1691.075 | .023051 | .049753 | 1 |

The intervals are nominal paired t95 over world seeds, exploratory with no
multiplicity adjustment. Signs include ties rather than dropping them.

| Contrast | Mean delta QoS [t95] | QoS + / - / = | Mean delta J [t95] | J + / - / = |
| --- | --- | --- | --- | --- |
| U-L | +.020677 [-.019708, .061061] | 19 / 12 / 1 | +46.260 [-130.446, 222.965] | 18 / 14 / 0 |
| F-B | +.036580 [.021379, .051781] | 25 / 7 / 0 | +66.341 [-10.573, 143.254] | 22 / 10 / 0 |
| B-L | +.158226 [.097286, .219166] | 24 / 8 / 0 | +603.758 [385.308, 822.207] | 25 / 7 / 0 |
| F-U | +.174130 [.113813, .234446] | 28 / 4 / 0 | +623.839 [439.993, 807.685] | 28 / 4 / 0 |
| F-U-B+L | +.015903 [-.026943, .058750] | 19 / 13 / 0 | +20.081 [-165.237, 205.399] | 19 / 13 / 0 |
| F-L | +.194806 [.136315, .253297] | 29 / 3 / 0 | +670.098 [467.174, 873.023] | 27 / 5 / 0 |
| R-F | +.009576 [-.004573, .023724] | 19 / 13 / 0 | +67.752 [2.573, 132.930] | 20 / 12 / 0 |
| R-L | +.204382 [.146314, .262450] | 32 / 0 / 0 | +737.850 [532.831, 942.869] | 32 / 0 / 0 |
| H_BS-L | +.043391 [.004796, .081986] | 8 / 4 / 20 | +140.473 [14.795, 266.151] | 8 / 4 / 20 |

**Information and package reading.** Under this one ordinary fixed program, true
BS coordinates have a large mean service/J consequence at either user-source
setting. User truth alone has a much smaller, uncertain mean consequence at
current-legal BS; given true BS it adds service, but its J interval crosses zero.
This shifts the working explanation away from a generic missing-current-user
encoder and toward BS knowledge as an important actionable input for H1. It does
not identify the old gap's causal percentage, an optimal-information bound, or
the best use of either signal. The interaction is retained and unresolved; a
crossing interval is not proof of additivity or no complementarity. R-F's small
service mean is not equivalence, and its J mean/tails keep package behavior
scientifically relevant. R-L is the explicitly revised package contrast, not a
replication of historical H_central minus historical H_local.

**Legal retention has native value but no universal improvement.** L and H_BS
first legally see a BS in the same 15 worlds; 17 never see one. Three sighted
worlds never require retention at a replan, leaving 12 active worlds and 761
memory-used replans. H_BS has zero known-BS omission plans, versus L's mean
27.09375, but it changes later visibility and deployment as well. All 20 inactive
worlds tie exactly on QoS/J. Among the 12 active worlds eight improve both and
four lose both. This is a legal-history recovery result, not a learned memory
result; conditioning on activation does not create a new randomized estimand.
No signal was invented for never-seen BSs. Mean legal user supply in L is 20.838
of the 30 true users at replans, while full-source programs receive all 30;
these cross-program coverage diagnostics are also trajectory-dependent.

The four memory-loss worlds are all preserved: 28100106 (-.026879 QoS/-83.522 J),
28100109 (-.010899/-30.958), 28100118 (-.009548/-23.529), and 28100119
(-.079119/-239.574). Best memory gain is 28100122 (+.329043/+1318.098).
Mean memory return-cost change is -.001717 [-.005351, .001917]: seven decreases,
five increases, twenty ties. World 28100101 gains .287287 service yet raises
return cost .010799 and lowers minimum battery .006660. Thus an overall positive
mean is not uniformly safer service. L/H_BS's worst battery remains .049753 in
28100107 and maximum mean return cost .118735. All six arms have zero cutoff and
depletion events, which does not erase these return risks or prove physical safety.

The never-seen world 28100126 remains zero-service for L, U and H_BS. B/F/R yield
.665413/.662419/.678173 there; their respective J values are 1961.007/1487.436/
2002.081, so even similar service masks a substantial risk/objective difference.
For F-B, 28100120 gains .012628 service but loses 508.092 J while return cost
rises .090995. For U-L, 28100113 loses .285854 service and 1185.661 J. Every
other loss and every risk minimum remains available, unfiltered, in the linked
per-world records and by-seed contrasts. None is selected for an automatic repair.

Initial DM investment reading: retain H_BS as a stronger ordinary legal-memory
comparator, not as a guaranteed deployed improvement. This complete empirical
study does not require a neural module to count as useful understanding. Do not
append anonymous-user tracking, another panel or a generic encoder to B01. Lawful
BS acquisition or belief from public station priors is a consequential remaining
question, but current RESEARCH assigns active sensing with ordinary memory/priors
to another native DM; return that implication to Root rather than duplicate it.
An independent context-isolated ResearchCritic is reading the complete original
record before the final route disposition. Published controller/canonicalization,
readout helpers and `batch.effective_config` have live active-sensing consumers
and therefore remain maintained; no peer file or accepted source is changed.

### 2026-09-28 - Independent result reading and bounded next question

The context-isolated registered ResearchCritic `read_b01` reconstructed the
published source, original benchmark/SET and availability evidence, configuration,
native completion record and all per-world results before reading the prior
selection advice or the DM's proposed disposition. It independently recomputed
all 36 contrast means/SDs for QoS, J/step, return cost and minimum battery from the
192 rows (maximum summary difference below 6e-17) and verified local artifact
hashes. It did not repeat the DM's remote NPZ audit. Its reported J deltas were
normalized per step; the preceding table uses total native J, exactly 3,000 times
those deltas. Review conclusion: **MATERIAL_DISSENT: no** on conditional publication,
retaining H_BS as an ordinary comparator and ending B01, with no new investment
automatically authorized.

The review strengthens the BS-anchor reading but keeps ordinary controller
competence as the strongest unresolved alternative. H1 was selected centrally,
not optimized as a legal-information policy, and its missing-BS branch removes
relay targets. Supplying a BS coordinate changes a consequential program choice;
the comparison establishes usefulness for this program, not the best possible
use of legal information. F-L remaining large means package ordering alone does
not explain this panel's mean R-L service difference, but absent historical
H_local prevents estimating canonicalization's effect on that controller or a
causal fraction of the old gap. The interaction cannot establish that users help
only with true BS, and R-F remains relevant, particularly for J.

One additional descriptive reading was independently checked by the DM: in the
12 memory-active worlds, B and H_BS differ by at most 3.908e-6 in QoS/step and
3.902e-6 in J/step. On the 17 never-seen H_BS trajectories, mean B-H_BS is
.219475 QoS/step and .294013 J/step. These are post-policy groups, not separately
randomized effects or attainable acquisition bounds. They do not authorize
selecting those 17 worlds for another evaluation. All four memory-active losses
remain losses. Eliminating omissions was an implementation implication; improved
complete service received qualified empirical support, not universal confirmation.
No moving-user memory, anonymous association or learned representation was tested.

The older adverse evidence remains applicable. SET's .437/.438 development
endpoint was one resumed lineage with privileged inputs, so its ordinary-control
shortfall cannot diagnose missing information or inability to learn memory.
Availability B02's zero-lag intervention had QoS delta -.01317
[-.04895, .02261]; a generic faster-refresh repair has weak motivation. B01's
32 worlds are fixed-program evaluation units, not independent learning runs.

**Scope correction to the preceding preliminary next-action paragraph:** the
other active-sensing study's [selected contract](../uav_active_sensing/NOTES.md#policy-family-and-exact-implementation-choices)
requires a known legal BS and 6-29 current users before scouting, and explicitly
excludes initial BS discovery. Thus it does not currently answer the 17
never-seen cases. No peer experiment or ownership was changed by this finding.

The critic's strongest feasible next comparison is a fixed ordinary BS estimate
from already legal station coordinates against H_BS, rather than a generic user
tracker or encoder. The source generator places station 0 around
`.7 * BS + .3 * initial_user_mean` and station 1 around `initial_user_mean`.
Therefore `(station0 - .3 * station1) / .7` is a concrete noisy estimate, not
exact reconstruction: independent per-axis jitter up to 960 m, clipping and
minimum-separation rejection matter. Even the unclipped coordinate-wise error
bound is 1,782.86 m; projection is not posterior calibration. A prospective
ordinary fallback could freeze a projected estimate at reset, keep inferred
coordinates distinct from observed memory, and give genuine legal sightings
priority, with no actor access to hidden truth or initial true user mean.

The suggested complete comparison is **32 fresh paired S2/H3000 worlds, 64
episodes, 192,000 transitions, zero fits**, unchanged planner/action rules, shield
and native service/J/risk. The fixed B01 rate suggests roughly 20-25 node minutes
before contention and overhead, with engineering/review/readback additional.
There is no prerequisite accuracy study or repeated factorial panel. A complete
J/service improvement with acceptable observed risk would strengthen ordinary
legal inference as the next baseline; better estimates or sightings without
native benefit would weaken this particular use. A loss rejects the tested
fallback package, not all inference or acquisition. An imprecise result need not
buy a larger panel. No numerical risk acceptance criterion, source, new seed set
or run is declared here: this is a recommendation for Root's next task choice.

DM disposition: accept this diagnosis and recommendation. **End B01 with its
complete conditional empirical result, retain the ordinary H_BS comparator and
do not append another arm, panel, fit or rescue.** The broad actionable-information
question remains open, especially initial BS inference/acquisition and better
ordinary use of legal inputs. Return that concrete next comparison to Root for
cross-question allocation; there is no active producer, hidden approval gate or
recurring check. The direction is idle/reserve until a concrete next assignment.

### 2026-09-28 - Durable evidence and measured retirement

After terminal reconciliation and full readback, moved the sole raw/progress
directory from the shared sparse checkout to the durable configured-node path
`wsl_4070:/home/wu/hmasd-artifacts/uav_information_value/b01_sources_a01/raw/`.
The original manifest remains unchanged: resolve its `raw/...` entries relative
to `/home/wu/hmasd-artifacts/uav_information_value/b01_sources_a01/`, rather than
the old run root. All 384 entries were rechecked there against original bytes and
SHA256, totaling 70,839,779 file bytes (72,024,064 allocated); the old raw path is
absent and no second raw copy exists. This move preserves the unique scientific
evidence outside sparse-checkout cleanup, and is **not** space reclamation.
Compact original configuration, per-world/summary/manifest and native statuses
are published under the original `runs/` path. The node's original zero-byte
stdout/stderr and acceptance/exit/control records remain with the operation.

The exact-target snapshot collector first refused its ordinary process scan
because `/proc/660/cwd` was unreadable. Its supported `--sudo-process-scan`
preview then verified terminal identities, no process references, clean snapshot
and durable Git reachability through `refs/remotes/origin/HEAD`. Applying the
collector to only `c2ee6692766a4a6fae25b99d93203cec` removed that accepted snapshot.
Its allocated size fell from 799,076,352 bytes to zero; actual path absence was
checked. The older remote Git GC bad-tree warning recorded at preparation was
not repaired; it did not block this collector, and no snapshot target remains.

Local consumer inspection found active-sensing imports of `controllers`,
`readout` and `batch.effective_config`, including tests. These useful published
source modules and their tests remain; no blanket implementation deletion was
attempted. With the deterministic observer stopped and the critic returned,
removed only these generated/rebuildable owned paths and verified absence:

- `experiments/candidates/uav_information_value/__pycache__/`: 40,960 to 0 bytes.
- `tests/experiments/candidates/uav_information_value/__pycache__/`: 45,056 to 0.
- `temp/directions/uav_information_value/` (used node-control patch and observer
  request): 12,288 to 0.

Net allocated space reclaimed across the exact remote/local deleted targets is
**799,174,656 bytes**: 799,076,352 remote and 98,304 local. This is working-tree
allocation reduction, not a claim about Git object-store or filesystem capacity.
No required evidence was discarded, no backup package was made, and no cleanup
tool blocker or accepted operation remains for B01.

### 2026-09-28 - B02 selected: lawful station-prior BS fallback

Root selected the preceding independent review's concrete next question after
B01's complete publication (`65d6c5165`): can an ordinary estimate from already
legal station coordinates recover useful complete native service/J beyond H_BS
before a genuine BS sighting? B01 remains closed and immutable. Reuse the
context-isolated result review above, whose fixed ordinary comparison and
32-fresh-pair recommendation directly cover this selection; no duplicate
scientific gate or prerequisite coordinate-accuracy study is added.

Current published background at `c669878d1`, [RESEARCH section 2](../../RESEARCH.md#2-部分可观测性要求处理信息不要求每次都重新训练),
changes the comparator to ordinary H_BS, not forgetting L: BS-source usefulness
was large under H1 while memory had four adverse active worlds and 17 never-seen
worlds. Sections 6/8 keep this a fixed-program, initial-world comparison, not an
optimal information decomposition, new learning evidence or a pure mediator
effect. The strongest simpler explanation for an advantage is that H1's
missing-BS branch omits relays despite available station-layout information.
The contrary prediction is that noisy inferred anchors misplace relays, displace
service/search or add return risk enough to cancel any service gain. Native
shield, moving users, shared stations and team assignment remain coupled.

Two frozen programs only: `H_BS`, exactly the published ordinary legal-user and
once-legally-seen BS controller; and `P_BS`, that same controller with a station
prior while no BS has ever legally been seen. On the first decision after reset,
decode station IDs 0 and 1 from their existing globally legal energy records,
using the first valid observer for each. Form
`b_hat = clip((station0_xy - .3 * station1_xy) / .7, 0, 8000)` coordinate-wise.
Freeze this one estimate for the episode; no fitting, tuning, subsequent station
re-estimation, confidence calibration or hidden-state correction. If either
station has no valid finite reset record, no estimate is created and ordinary
H_BS applies. Missing station records in synthetic tests do not change the actual
two-station S2 contract.

Inferred coordinates and observed memory remain distinct. A genuine legal BS
sighting at any primitive step updates observed memory and takes permanent
priority over the estimate, including when the BS later becomes absent. Replan
remains every 30 calls, with exactly the common sort-then-merge users, H1 target
generation, six service/two relay slots, Hungarian assignment, hysteresis,
speed/altitude and ordinary search fallback. The controller accepts no raw env,
never reads state/true BS/true initial user mean/RNG, and never fabricates a legal
sighting or rewrites an observation. The source relation remains noisy due to
960 m jitter, clipping and rejection; this is neither exact recovery nor a
calibrated belief.

Fixed fresh panel: **seeds 28100201-28100232**, every seed run once with H_BS and
once with P_BS, **64 full S2/H3000 episodes, at most 192,000 native transitions,
zero fits/updates**. None is selected from B01's 17-world subgroup. Output tag
`b02_station_prior_a01`. No old panel, auxiliary truth arm, early stopping on
scores, panel extension or automatic retry. A native early termination is retained
at its actual length; an exception or incomplete cell prevents a complete paired
claim and creates no substitute episode. Source SHA will be pinned by the native
manifest after focused tests and engineering review, before exposure.

Primary reading is paired total native J; QoS/step is its service consequence,
not independent corroboration. Retain all native metric sums/means, sign counts,
paired nominal t95 intervals and every adverse world; intervals are exploratory,
not multiplicity-adjusted or confirmation. Positive mean J and QoS with a J
interval wholly above zero supports this fixed fallback's conditional usefulness;
an interval crossing zero leaves the mean benefit unresolved, not equivalent.
More sightings or changed planning without complete J/service improvement does
not support utility. A loss rejects this package, not all lawful inference or
active acquisition. No result automatically buys a wider panel or learner.

**Prospective practical risk reading.** Use the unchanged native reserve ratio
.10, not a tuned new threshold. Preserve native cutoff/depletion counts, capped
and raw return-cost tails, exact native per-UAV battery traces, time at/below
reserve and final reserve counts. Do not recommend default replacement if P_BS
adds cutoff/depletion events or leaves more UAVs at/below reserve at H3000 in any
paired world. Higher mean return cost or a worse panel battery minimum is also
an explicit risk tradeoff, never erased by positive mean J. Conditional service
value may survive such a tradeoff, but it is not risk dominance or a deployed
safety guarantee. All individual J/service losses are reported whether or not
those risk conditions trigger. Zero events cannot establish safety or sustainable
cycling beyond this horizon.

The candidate predicts that inferred BS coordinates are used at pre-sighting
replans and thereby enable the ordinary relay branch where legal users suffice;
the empirical prediction is a positive complete J/service difference. Prior-used
plan counts and true legal first-sighting times diagnose activation; later
sightings, user visibility and policy trajectories are endogenous consequences,
not a separately randomized information mechanism. No coordinate-error result
is required or used to select the recipe. The other active-sensing contract
requires a known legal BS and does not cover this initial-inference intervention.

Compute: configured `wsl_4070`, scientific Python
`/home/wu/.venvs/hmasd/bin/python`, four worker processes with one numerical
thread each, subject to fresh actual-node native admission. B01 rate scaling
suggests 20-25 node minutes and about 1.4 summed worker CPU hours before contention;
engineering, review, readback and storage add real cost. Retain compact originals
in Git and one hashed native trace copy outside the shared sparse checkout at
completion. No new dependency installation or device/precision switch is selected.

L0: add only `experiments/candidates/uav_information_value/b02/`, the direction's
`run_b02.py`, and matching `tests/.../uav_information_value/b02/`; do not change
B01 source/outputs or active-sensing consumers. Reuse published native evaluator,
H_BS/PointSetHeuristic, effective S2 checks and bounded execution utilities.
The bounded Implementer owns the B02 prior-controller module and its tests only;
DM owns runner/readout/entrypoint, notebook and publication. Checks cover lawful
station ID decoding, projection, reset freezing, observed-sighting priority and
retention, no observation/state/environment leakage, H_BS off-path parity, common
planner inputs, risk accounting, fixed-panel/failure serialization and a short
nonpanel native observer-off/on fixture. No correctness test may expose these 32
result seeds. Independent engineering review is required for the final executable
contract. Publish exact inputs, launch once, keep this child active through
same-handle deterministic waiting, collect/read the complete record, obtain the
required independent result diagnosis and publish the disposition before return.

### 2026-09-28 - B02 engineering acceptance before exposure

The bounded Implementer delivered only the prior-controller module and its
constructed-observation checks. The DM read and accepts that work: it subclasses
H_BS state, reuses the unchanged PointSetHeuristic, copies no privileged source
and adds no alternate assignment/action rule. DM-owned runner, paired readout and
admitted entrypoint keep all B01 source and artifacts untouched. The risk observer
copies exact native batteries after each transition; those values never enter
either controller. Returned native arrays remain preserved even if downstream
reading fails, and incomplete panels suppress paired/practical-risk claims.

The DM's focused suite passed **19 checks in 8.55s**. The independent registered
engineering Reviewer read all six new files and the prospective contract, then
independently passed the same **19 checks in 8.28s**: **no material finding**.
Both runs reported the same 14 existing dependency deprecation warnings. Each
executed four 31-step seed-17 native observer-off/on fixtures, so B02 engineering
exposure is **248 native transitions, zero fits**. Implementer checks were
constructed observations only; mocked persistence/failure tests created no native
transitions. The declared 32 fresh result worlds remain unexposed. Review limits
are no full-H3000 execution, destination-node runtime check or abrupt spawned-
worker-death reproduction; failure serialization uses a single-worker thread
substitute. These are coverage limits, not invented extra launch gates.

Root supplied cross-question context from E's distinct 16-world panel: ten worlds
had no legally known BS at any macro decision and all four intervention traces
matched H there, with six activated. That is not B01's denominator, a separately
randomized subgroup or permission to select worlds. It reinforces the scope
distinction only. B02's already selected fresh full panel, estimator, cost and
stopping contract are unchanged and require no E result gate.

### 2026-09-28 - B02 accepted and observed on its native handle

Exact published inputs are `d6151ff5155d8bf3f3289bba727ee5148f6b76a6`.
The single fixed B02 operation was accepted at **06:37:28 UTC**, with its original
[native launch manifest](../../../../runs/uav_information_value/b02_station_prior_a01/launch-manifest.json)
and [fresh actual-node admission](../../../../runs/uav_information_value/b02_station_prior_a01/admission-preflight.json)
collected here. Available physical/effective memory was 14,881,013,760 bytes
against the 4,294,967,296 floor. The configured supervisor's launch command
finished exit 0 after 19 seconds; that is not the experiment exit. The first
deterministic observation at 06:43:33 UTC reports the native runner/supervisor
running with matching identities, accepted admission, no exit witness and zero
observer errors. No B02 result has been read at this entry.

The node's dirty canonical RESEARCH prose remains unchanged: its relevant lifted
pause, exploring state and exact `Codex DM (native child)` lead match published
controls. Source fetch through configured `zsh -lic` succeeded; the previously
recorded old bad-tree automatic-GC warning remains and was not repaired. No
sparse selection, unrelated evidence or source was reset or merged.

Observation remains owned by this native child at
`/home/fires/.local/state/hmasd-wait/01a0e5da-116b-72f3-b158-476344637e06`.
The first new request was refused for a relative `ssh` executable; it was
corrected to `/usr/bin/ssh`. A second arm was refused because the old B01 observer
state was stopped. Draining that state showed no pending wake/event and only the
already completed B01; rearming generation 4 to 5 cleared observation stop, then
adding B02 established **generation 6**, job `b02_station_prior_a01`, window
1,500 seconds. These were observer-setup corrections, not launches, worker
restarts, result failures or a resumed B01. Its completed job remains completed.

The accepted native handle is unchanged. This child stays active through long
deterministic waits, drains the existing observer at terminal/checkpoint, rearms
only that observation when needed, and will collect/read all declared outcomes.
The earlier native-child automatic wake rejection is not assumed fixed or routed
to Root. No replacement operation, panel extension or extra arm is authorized.

### 2026-09-28 - B02 complete: useful lawful prior with a reserve counterexample

The original operation exited **0 at 06:56:04 UTC**. Same-handle observation
reported READY at 06:56:24 UTC, matching the valid native exit witness and absent
runner/supervisor identities, with no consistency mismatch or probe error.
The detached queue attempted delivery to this child but returned code -32600:
`direct app-server input is not allowed for unloaded spawned sub-agents`.
The child remained active, completed its long deterministic wait and drained the
same handle; no completion callback was presumed delivered. READY event
`c4dde6f323ddc40125787a0a`, wake `31df8dd3-ac3a-4e30-a70e-1a9a4d97c073`, was
consumed from generation 6 to 7; observation was stopped and a final drain showed
no pending event/wake. No restart, replacement, retry or additional panel occurred.
The first compact scp used unsupported brace expansion and found no file; explicit
source paths then collected the originals. That collection error caused no result
execution or missing scientific evidence.

All **64 declared episodes / 32 paired fresh worlds** completed at native H3000
truncation: **192,000 native transitions, zero fits, zero optimizer updates**.
There are no failed, cancelled, unreconciled, missing, unstarted or orphan cells,
and no partial transitions. [Configuration](../../../../runs/uav_information_value/b02_station_prior_a01/config.json),
[all per-world readings](../../../../runs/uav_information_value/b02_station_prior_a01/perworld.json),
[complete summary](../../../../runs/uav_information_value/b02_station_prior_a01/summary.json),
[manifest](../../../../runs/uav_information_value/b02_station_prior_a01/manifest.json)
and [terminal status](../../../../runs/uav_information_value/b02_station_prior_a01/terminal-status.json)
retain exact source `d6151ff5155d8bf3f3289bba727ee5148f6b76a6`.

Full readback verified every **131 manifest entries**, including 64 NPZ and 64
progress records. All 64 NPZ loaded with `allow_pickle=False`; native reward,
metrics, positions and exact batteries were finite, with no early terminal and
only final truncation. Rebuilding `world_row`, mechanism/position readings and
exact battery readings yielded **4,864 exact per-world field matches**. Declared
seed/arm/order, 100 replans at 0:30:2970, prior formula from recorded legal
station coordinates, no prior after legal BS knowledge, canonical user equality,
activation counts and final progress were also checked. The complete summary
rebuild matched every reader-produced field exactly. Compact local file hashes
match the original manifest. No new environment transition was used for readback.

| Endpoint | H_BS mean | P_BS mean | P_BS - H_BS, nominal paired t95 |
| --- | ---: | ---: | ---: |
| Total native J | 1662.263697 | 2060.435659 | +398.171962 [172.534665, 623.809258] |
| QoS/step | .616873 | .703389 | +.086515 [.030571, .142459] |
| Capped return cost/step | .026306 | .003204 | -.023102 [-.037168, -.009037] |
| Raw return cost/step | .026434 | .003204 | -.023230 [-.037419, -.009041] |
| UAV-step fraction at/below .10 reserve | .062617 | .012512 | -.050105 [-.078333, -.021878] |
| Final UAV count at/below reserve | 3.531250 | 1.437500 | -2.093750 [-3.431397, -.756103] |
| Mean episode minimum battery | .086956 | .098743 | +.011788 [.005609, .017966] |

The predeclared conditional-usefulness prediction succeeds: mean J and QoS are
positive and the J interval is wholly above zero. J and QoS each improve in
**17 worlds, worsen in 3, and tie in 12**. Intervals are exploratory over initial
worlds, not independent training replications, confirmation or multiplicity-
adjusted inference. Service is part of native J; its improvement is not independent
corroboration, and the native objective also benefits from lower return costs.
All native metrics, tails and phase/charging readings remain in the originals.
H_BS's two zero-service worlds, 28100203/28100226, attain .596549/.580654 QoS under
P_BS without ever legally seeing BS. This is a concrete complete-use result, not
a coordinate-accuracy result or a selected zero-service population.

Every J/service loss is retained (J below is total, not per step):

| Seed | Delta QoS/step | Delta total J | Delta return cost/step |
| --- | ---: | ---: | ---: |
| 28100217 | -.022772 | -70.479000 | +.000364 |
| 28100223 | -.001219 | -1.790923 | -.000307 |
| 28100231 | -.041743 | -125.688814 | +.000077 |

**Do not recommend default replacement.** The prospective risk rule is triggered
by **28100224**: P_BS gains .083353 QoS/step and 87.318994 total J but final
reserve count rises **0 to 7**, reserve exposure **12 to 2,631 UAV-steps**,
episode minimum battery falls **.096840 to .082321**, and return cost/step rises
**.000809 to .027933**. The independent critic inspected the exact native arrays:
seven UAVs stay below .10 throughout the last 300 transitions, with final ratios
about .08232-.08399; H_BS has none below reserve in that window. This is sustained
exposure, not a rounding artifact. Better mean risk does not cancel a prospectively
declared adverse-world rule. Zero cutoff/depletion events in both arms establish
neither safety nor sustainable cycling after H3000.

The panel-wide minimum battery improves .044310 to .082321, and the maximum
world-mean capped/raw return costs improve .143354/.145746 to .027933/.027933.
Nevertheless reserve exposure and episode minima worsen in 28100217/224/230;
final minimum battery worsens in 28100217/224/229/230; return cost worsens in
28100217/224/230/231 (abbreviated suffixes retain the 28100 prefix). Thus the
conditional performance gain is not paired risk dominance. All these tails,
including a positive-J risk counterexample, constrain future use.

The prior enters planner inputs in **25 worlds / 1,067 replans**. Only **20 worlds
/ 1,001 replans** combine inferred input with relay targets; these are the 20
worlds with different native outcomes. Seven worlds already see BS at reset.
In five others (28100207/208/214/220/227), prior-used replans have no legal users
and no relay targets, followed by legal BS acquisition before a consequential
relay decision. All native arrays, including targets, are exactly equal in the
12 tied worlds. Input supplied is therefore distinct from decision activation.
P_BS has ten never-seen worlds versus H_BS's seventeen, but first-sighting times
are deliberately not paired after dropping non-occurrences. These sets and later
observations are policy consequences, not separately randomized mediators. Seed
28100231 acquires BS at step 70 rather than 1804 and still loses J and service.

The result strengthens the ordinary-information explanation: an untuned lawful
function of already public station coordinates can improve complete service/J
beyond remembering genuine sightings, without extra sensing, fitting or learned
memory. It weakens a claim that those additions are required for this increment.
It does **not** isolate algebraic coordinate content from supplying an anchor that
enables H1's otherwise absent relay branch. The noisy generator relation is not
exact reconstruction or a calibrated posterior; coordinate accuracy, optimal
information value and learned recoverability remain unmeasured. Nor can B02's
fresh panel be subtracted from B01's central references to claim a remaining gap
or a percentage of the historical central/local gap recovered. Endogenous user
visibility, shield/charging trajectories and later sightings are included in the
fixed-program consequence, not controlled mechanisms.

Actual cost is **1,076.713 runner seconds (17.945 min)**, **1,115.536 accepted-
operation seconds (18.592 min)** and **4,304.283 summed worker CPU seconds
(1.196 h)** with four single-thread workers. Maximum reported worker peak RSS is
510,564 KiB (498.598 MiB); parent peak is 479,344 KiB. Individual peaks are not a
simultaneous node peak. All worker resource records are present. The separately
declared engineering exposure remains 248 transitions / zero fits; preparation,
review and readback time is not fully measured and is not zero cost.

### 2026-09-28 - B02 independent reading and disposition

The registered ResearchCritic `/root/dm_information_value/read_b01` reconstructed
the original 64 rows and fixed rule before receiving the DM disposition. This is
the same context-isolated reviewer used for B01, retaining that review but no
inherited DM/Root conversation. It independently checked compact artifact hashes,
ten paired summaries and seven decision-relevant remote NPZs, including the
reserve counterexample and input-used ties. It did not duplicate the DM's full
64-trace reconstruction. No second selection review or Pro round was added.

Its substantive recommendation is **retain P_BS as a useful conditional ordinary
comparator, enforce the default-replacement block, and stop B02 without extension
or post-hoc safety repair**. The mean-benefit prediction succeeded while practical
adoption did not. The critic emphasizes the three adverse service/J worlds, the
sustained seed-224 reserve exposure, and the distinction between input use and
decision activation. Its descriptive check finds that the two zero-service
rescues contribute about 43% of the aggregate service increment; the other thirty
worlds still average positive differences. That post-hoc description changes
neither the full-panel estimand nor the declared decision rule.

The strongest surviving explanation is ordinary relay-branch competence. More
legal BS sightings cannot establish the mediator, especially with seed-231's
earlier-sighting loss. The result does not identify a cause of reserve failure
that selects a targeted repair. A positive mean does not itself justify another
panel, fit, confirmation, threshold or learner. **MATERIAL_DISSENT: no.** The DM
accepts this reading and the stop at the assigned substantive boundary.

A genuinely different contingent question is whether the station transformation
adds useful decision content beyond a simpler lawful anchor with identical
pre-sighting relay activation and genuine-observation precedence, for example
station 0 itself. P_BS superiority would support incremental transformation value;
the simpler rule's superiority would favor ordinary simplification; imprecision
would leave attribution unresolved. This is worth selecting only if attribution
or comparator choice would change a substantive next investment. It is not a
prerequisite to the B02 result or an automatic repair. Two arms on 32 fresh worlds
would cost roughly 18-25 node minutes plus engineering/readback; adding H_BS costs
half again and is necessary if the decision is default replacement against H_BS,
rather than the two anchors' conditional ranking. No such comparison, fit,
anonymous tracker, active-sensing takeover or wider panel is selected here.

Disposition: end this fixed B02 investment, retain its positive and adverse
evidence and reusable ordinary controller, and return this belief update to Root
for cross-question allocation. The broader actionable-information question is
not exhausted; no active operation, uncollected result or external dependency is
being called an idle wait. Re-entry requires a newly selected distinct comparison
whose interpretation would change use or explanation, not an unchanged-score
check. RESEARCH section 2 will reflect this stronger legal comparator and its
reserve limitation rather than continuing to call initial inference untested.

Cleanup scope: keep the unchanged reusable `b02/controller.py`, its lawfulness
tests, and `b02/readout.py`. The finished 32-world launcher/worker are not reusable
assets or current consumers: retire `run_b02.py` and `b02/batch.py`, and retain the
three constructed reader tests from `test_batch.py` as `test_readout.py` while
retiring its finished-run wiring tests. No controller/readout semantics change;
the accepted executable remains pinned at the input SHA above. Check retained
constructed tests without new native episodes, check imports/active consumers,
retain the single hashed raw evidence copy outside the shared checkout, reclaim
the exact completed launcher snapshot with its native collector, and measure
deleted targets and net allocated bytes. Do not modify B01 records or source.

### 2026-09-28 - B02 durable evidence and completed cleanup

After the critic returned, moved only B02's required raw directory to its single
durable location:
`wsl_4070:/home/wu/hmasd-artifacts/uav_information_value/b02_station_prior_a01/raw/`.
It contains **128 files / 35,545,197 file bytes / 35,946,496 allocated bytes**.
Every byte count and SHA-256 was checked against the original manifest both
before and after the move; the old shared-checkout raw directory is absent.
Moving retained evidence reclaimed **0 bytes**. The original manifest is unchanged,
SHA-256 `63d375d1de5ad16f5b4c1824efb67f2d509842885c936aa930fe702f49d8a47a`.
For its `raw/...` entries use this durable raw root; compact configuration,
per-world, summary and native operation records remain at their recorded run path
and are published in Git. No full tree, archive package or backup copy was made.

The reusable prior controller and paired/risk reader are unchanged. The completed
launcher/worker and their obsolete wiring tests were retired after a consumer
search found no remaining executable imports of them. Three existing constructed
reader tests were retained separately, alongside ten controller tests: **13 passed
in 3.17s**, with the same 14 dependency warnings and **zero new native transitions**.
The full accepted 19-check executable and frozen run entry remain recoverable at
[the input SHA](https://github.com/CartmanFatass/My-paper-code/tree/d6151ff5155d8bf3f3289bba727ee5148f6b76a6/experiments/candidates/uav_information_value).
Existing B01 code and active-sensing imports were left unchanged.

The exact native snapshot
`/home/wu/projects/HMASD/.git/hmasd-launch-sources/f71f3891bc9d4406a604484c4c226c73`
was reclaimed using `scripts/hmasd_snapshot_gc.py`. Its first preview refused
generated ignored caches created by the DM's import-based readback; inspected
status showed only 14 `__pycache__` directories containing `.pyc` files. Removing
those generated files reclaimed 1,146,880 bytes. Ordinary process inspection then
refused `/proc/660/cwd`; the collector's supported read-only `--sudo-process-scan`
verified eligibility, and exact-target apply removed the remaining 800,120,832
bytes. The snapshot is absent, with its accepted claim/output/manifest and durable
main source ref preserved. These are cleanup-tool refusals subsequently resolved,
not failed scientific execution or an outstanding blocker.

Measured cleanup targets (allocated bytes before to after):

| Target | Before | After |
| --- | ---: | ---: |
| Exact remote snapshot, including generated caches | 801267712 | 0 |
| Local direction `__pycache__/` | 40960 | 0 |
| Local direction `b02/__pycache__/` | 32768 | 0 |
| Local tests `b02/__pycache__/` | 45056 | 0 |
| `temp/directions/uav_information_value/` (observer request only) | 8192 | 0 |
| Retired `b02/batch.py` + `run_b02.py` + `b02/test_batch.py`, net of retained `test_readout.py` | 32768 | 4096 |

All deleted targets were checked absent. Net allocated reduction across these
cleanup targets is **801,423,360 bytes** (801,267,712 remote; 155,648 local,
including the replacement reader-test file). This is working-tree allocation,
not Git-object-store reclamation or a whole-host free-space claim. The unique
required raw evidence remains; no accepted worker, active observer, pending
review, redundant raw copy or concrete cleanup blocker remains for B02.

## 2026-09-28 - B03 prospective: geometric prior versus an ordinary relay anchor

New native DM `/root/dm_information_round2`, parent Root
`01a0e560-4333-7b03-8ff3-759a4add1d9a`, continues this question on shared main.
The owner explicitly starts the next round; the predecessor's B01/B02 are fully
read and closed, with no inherited live operation or pending advice. Root selects
the substantive question and owns the common isolated selection review
`/root/round2_question_review`. The design below was sent through native parent
communication before substantial implementation. It is prospective, pending that
applicable review, not a launch or a second selection-review request.

**Question and use.** Does B02's algebraic station prior supply useful decision
content beyond the simplest lawful anchor enabling the same pre-sighting relay
branch, and which ordinary comparator should subsequent information/learning
work use? The intended contribution is empirical understanding and a defensible
ordinary reference. Neither algorithmic novelty nor re-proving B02's whole-
package benefit is the target. B02's positive complete result, its three J/service
loss worlds and its sustained seed-28100224 reserve counterexample remain facts.
No favorable new average can erase the earlier default-replacement restriction.

Relevant published background was refreshed at
`2abfda5c048883483a27149c645701cbf79daf37`, with HEAD and origin/main matching.
[RESEARCH section 2](../../RESEARCH.md#2-部分可观测性要求处理信息不要求每次都重新训练)
requires a stronger ordinary comparator than forgetting an observed BS and warns
that an inferred coordinate also enabled H1's relay branch. Sections 6/8 require
complete native consequences and distinguish fixed-program information use from
optimal information value, finite learning, or a pure mediator. These judgments
lead directly to a matched anchor comparison with H_BS on the same fresh panel.
The parent question stays open even if this particular construction is not useful.

**Source premises and the ordinary alternative.** The existing generator
`envs/pettingzoo/relay/energy_aware.py` places station 0 near
`.70 * BS + .30 * initial_user_mean` and station 1 near initial user mean, with
component jitter up to 960m, clipping and separation rejection. Consequently
station 0 itself is a lawful, cheap BS-side anchor. The algebraic construction
removes an idealized demand contribution but amplifies station noise and does
not estimate a calibrated posterior. Either anchor may put the ordinary relay
targets in a useful region. Existing H_park2 is a useful whole fixed-waypoint
reference, but changes the motion/target program and does not control this same
H1 branch; its historical score is not evidence against the matched station-0
choice. No anchor is optimized or selected from exposed worlds.

The actual interface is the unchanged PointSetHeuristic: canonical current legal
users form up to six service centroids; a nonempty centroid set plus a supplied
BS/anchor generates two relay targets, ahead of service targets. Non-shielded UAV
capacity limits assignment, and Hungarian distance assignment retains 300m
hysteresis. Plans persist 30 primitive calls; each step then passes through the
same production return shield, energy handling and backhaul guard. Thus input
supply, relay generation/assignment, proposed command, submitted command and
realized movement are distinct. Truth assimilation does not add an interrupt.

**Fixed comparison proposed for selection.** The three programs are:

| Arm | Before a genuine BS sighting | After a genuine BS sighting |
| --- | --- | --- |
| H_BS | No BS input; existing ordinary fallback | Existing current/remembered legal BS |
| P_BS | Unchanged B02 reset-frozen `clip((s0-.3*s1)/.7,0,8000)` | Current/remembered legal BS permanently supersedes inference |
| S0_BS | Reset-frozen first valid legal station-0 xy | Identical permanent genuine-sighting priority |

S0_BS decodes station ID 0 through the existing legal energy records, takes the
first valid observer and requires finite coordinates. If unavailable at reset it
stays H_BS; no later estimate is introduced. P_BS retains its existing two-record
requirement. The actual S2 host supplies both stations. Every arm assimilates
genuine BS sightings at each primitive step and uses the latest remembered truth
at the next shared replan. Inference is never inserted into observations, counted
as a sighting or stored as observed memory. The same real observation supplied to
all three programs has the same priority; each program's later observations may
differ because its trajectory differs. Canonical users, replan cadence, service/
relay slots, assignment, speed/altitude, search, guard, reward, shield, native
termination and observation rights are unchanged. There is no critic, learner,
normalizer, optimizer, extra communication or fitted parameter.

Freeze **28100301-28100332**, all three programs once on every seed, S2/H3000:
**96 complete episodes, at most 288,000 native transitions, 9,600 ordinary replans,
zero fits and optimizer updates**. These seeds are fresh, not a selected subgroup
of either earlier panel. Tag `b03_anchor_content_a01`. Native early termination
is retained at its actual length; a failed or missing cell prevents a complete
paired conclusion and is not replaced. No outcome-dependent stopping, extra
arms, panel extension, threshold tuning, learning or automatic retry.

Primary estimand is paired total J for **P_BS-S0_BS** over the full initial-world
panel. QoS/step is its service consequence, not independent corroboration.
P_BS-H_BS and S0_BS-H_BS on this same panel determine the ordinary reference's
conditional use. Report all native metrics, per-world differences, signs/ties,
nominal paired t95 intervals and adverse worlds. These are exploratory world-
level intervals without multiplicity adjustment, not independent training runs.
Later activation/sighting groups are descriptive, never a selected estimand.

Positive mean J and QoS with the primary J interval wholly above zero supports
incremental geometric-construction value, conditional on the program and risk.
If S0_BS is useful against H_BS (positive J/QoS means and J interval above zero)
but P_BS's increment is unresolved, S0_BS may be the pragmatic simpler conditional
reference; this is a choice under uncertainty, not equivalence or a claim that
geometry is useless. The opposite signed primary result favors the simpler
anchor directly. A primary gain without either anchor's established complete use
against H_BS does not justify default adoption. Unresolved/adverse anchors retain
H_BS and end this batch without an automatic larger panel. Intermediate changes
without J/service benefit do not establish utility. Every outcome changes either
comparator choice or the stated uncertainty/investment, not B02's original result.

**Risk/use rule.** Keep B02's native .10 reserve threshold and exact post-step
battery arrays, cutoff/depletion, capped/raw return-cost tails, reserve UAV-steps,
final reserve counts and episode/final battery minima. For each anchor versus
H_BS, any paired world with added cutoff/depletion or more final UAVs at/below
reserve blocks default replacement. Higher mean return cost or a worse panel
battery minimum is an explicit tradeoff. Apply the same descriptive comparisons
between the two anchors; positive means never erase their adverse worlds. P_BS's
already observed B02 replacement block persists even if B03 has no new blocker.
Conditional reference value is distinct from risk dominance, operational safety
or sustainable cycling after H3000; zero events prove none of those.

**Cost and L0.** Prefer configured wsl_4070 and its existing scientific interpreter,
four independent workers with one numerical thread each, subject to fresh actual
node admission with Claude B05 and any other real work present. B02's measured
rate scales to about 27-40 node minutes and 1.8 worker CPU-hours before contention;
engineering, publication, review and readback add real cost. No GPU/dependency or
sparse-checkout change is required. Compact config/per-world/summary/native
records go to Git, with one hashed required trace copy in durable direction/tag
storage at closure.

Implementation is confined to new `b03/` modules and `run_b03.py` beneath this
direction, plus matching tests. Reuse frozen B01/B02 controller and native reader
assets unchanged; the sensing DM may import them independently. Deliver the
single fixed comparison above with native admission, bounded failure-preserving
execution, exact panel identity and declared reading. The read-only observer must
retain supplied anchor/source, generated/assigned relay counts, controller proposal,
shield-submitted commands, exact native pre/post movement and exact batteries,
without affecting controller/RNG/environment behavior. Keep genuine observations
and inferred input distinct, including sightings between replans.

Checks use constructed observations and a short nonpanel native observer-off/on
fixture: station-ID selection, reset freezing, memory/true-sighting priority,
missing-record fallback, no raw-state leakage, existing P/H parity, branch and
assignment conditions, action/movement distinction, risk counts, fixed-panel and
failure serialization, and admission before scientific effects. No test exposes
the declared 32 result seeds. Independent engineering review covers the final
executable change; completed applicable selection advice will be recorded here.
After one published/admitted run, retain this native child through deterministic
same-handle observation, collect/read the full evidence, obtain independent
scientific result diagnosis, publish standing/shared understanding and perform
scoped measured cleanup. No new claim note is needed for this exploratory
fixed-program comparison.

### 2026-09-28 - Selection correction: simplicity does not resolve uncertainty

The common independent critic supports the three-arm experiment but raises a
material objection to the proposed inconclusive-result disposition. P_BS's
algebraic overhead is negligible, so a wide P_BS-S0_BS interval cannot favor S0_BS
mainly on simplicity: meaningful P benefit or a risk difference may remain
unresolved. Root adopts that correction and the DM implements it. **This
supersedes the preceding pragmatic-simplicity branch:** if uncertainty remains
decision-wide, retain P_BS and S0_BS as unresolved conditional alternatives and
keep H_BS as the default. A future conditional reference is selected only from
the complete J/service/risk observations and real tradeoffs, not a crossing-zero
test or trivial arithmetic savings. There is no equivalence claim, new numerical
threshold, pilot, extra world or post-score repair. The original P_BS reserve
counterexample and default-replacement block remain in force. Full selection
advice is returning through Root and will be preserved in this notebook.

The bounded Implementer owns only the new B03 executable modules/entrypoint and
matching B03 tests for this one frozen three-program behavior. The DM owns this
notebook, RESEARCH, acceptance, launch and collection. Both work in the existing
shared main checkout; the Implementer has no Git-index/commit, shared-file, B01/
B02-edit or launch permission and spawns no children. The selection correction
changes interpretation, not the prescribed executable panel.
