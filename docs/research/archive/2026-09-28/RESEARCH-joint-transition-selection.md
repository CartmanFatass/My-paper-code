# Independent joint-transition question and study selection

Historical evidence only, retired on 2026-09-28 after the full independent
answer and its concrete-design continuation were read and resolved. The initial
working review is preserved from `308f3825e`; the design was reviewed at
`a354aa32c`. Earlier pending/illustrative statements below are historical, not
current experiment authority. The final decision at the end supersedes them.
Current priorities and routing remain in [RESEARCH](../../RESEARCH.md).

<a id="portfolio-review-2026-09-28-independent-joint-transition"></a>
## Portfolio review 2026-09-28 independent-joint-transition

Conversation: independent native scientific review only, no Pro consultation.
Reviewer: `/root/question_space_review`, separate context; new design DM:
`/root/dm_joint_transition`, parent Root `01a0e560-4333-7b03-8ff3-759a4add1d9a`.
Context: constitution sections 2/4/5, owner-approved attention refinement at
`858e8cff5`, current shared topics and original evidence cited in the answer.
Current source boundary: `350294379` for the review; `981e935ee` includes the
already selected persistent-service inputs. That study is not reopened here.

Decisions asked: does reduced DM activity show exhausted valuable questions,
or narrower recipes and incomplete question coverage? Which independent
UAV joint-planning question deserves design effort while current work proceeds?
Options: retain only the current study; develop an independent transition
planning comparison; or prefer another concrete question if its expected
decision value and complete cost warrant it. No topic quota or extra diagnostics
are required. Source/literature recommendations are not automatic experiment
admission, and a question's broad possibility is not a purchase justification.

### Answer

Complete final independent question-space answer, with repository link targets
made portable. This answers the question-framing choice; the executable
comparison and investment cost remain pending below.

**Retain Root's non-exhaustion diagnosis, but change the unit of convergence from active DMs to tested decisions.** The evidence has improved our ordinary comparators and rejected several specific recipes. It has not established that the remaining active directions are the uniquely valuable ones.

This was a separate-context review without inherited Root/DM conversation. The assignment disclosed Root's provisional interpretation, so it was not blinded. I reconstructed source interfaces and native summaries before reading the relevant interpretations. Current coordination was checked through `350294379`; no files, experiments, or accepted operations were changed.

The strongest evidence is:

| Evidence | Supported reading | Boundary |
|---|---|---|
| Radio placement, source `8ec998eca`: R−G QoS **+.028758**, J **+69.938**; 8 worlds, 0 fits, 72k steps, 41.79 minutes | Ordinary spatial search can improve complete service beyond stronger geometric clustering. | R also changes target support and persistence; minimum battery .088559 and three adverse reserve tails prevent uncomplicated adoption. There was no learned spatial-search arm. [Native results](../../../../runs/uav_radio_placement/b01_spatial_a01/summary.json) |
| Cooperative planning B02, source `9f72afd22`: L−P QoS **−.016488**, J **−55.389**; 1 fit, 480k steps, 3.862 hours | The fitted ranking package actively changed choices and failed against a competent ordinary planner. | Its choices were all-move or one member's ten-step hold around H1 targets. It did not learn general joint paths or spatial goals. [Protocol](https://github.com/CartmanFatass/My-paper-code/blob/350294379/docs/research/candidates/uav_cooperative_planning/NOTES.md#L304), [results](../../../../runs/uav_cooperative_planning/b02_transit_value_a01/summary.json) |
| S1 LOCAL1 B17: fresh-panel N8 differences against H6 were positive in all three blocks; N4 J differences were negative in all three | Ordinary local recurrent learning has useful competence, with consequential deployment boundaries. | These are fixed-roster Scenario 1 results, not S7 results or membership-memory evidence. [Results](../../../../runs/agent_count_generalization/s1_fresh_world_deployment_b17_final45/summary.json) |
| S1 B20: six fits, three independent training blocks; mixed-count N7 effects **−.08349 J**, **−4.399 served users/step** | The exact ordered mixing recipe did not deliver its proposed improvement. | The positive development instance remains; neither this result nor more evaluation episodes exhausts count generalization. [Results](../../../../runs/agent_count_generalization/s1_ordered_roster_confirmation_b20_aggregate_20260925/summary.json) |

Non-results must remain separate. Transit handoff was declined before execution, with substantial proposed model-rollout cost. Roster-memory reconstruction found ordinary public event/assignment state, not the hypothesized private persistent information. Diagnostics A02 ended incomplete with no checkpoint and 126k new recorded transitions; it is not a failed test of the masking intervention's benefit. [Handoff cost](https://github.com/CartmanFatass/My-paper-code/blob/350294379/docs/research/candidates/uav_transit_handoff/NOTES.md#L327), [roster sources](https://github.com/CartmanFatass/My-paper-code/blob/350294379/docs/research/candidates/uav_roster_memory/NOTES.md#L89), [A02 output](../../../../runs/energy_relay_diagnostics/b02_shield_surrogate_a02/ordinary/summary.json).

Thus ordinary competence, failed finite learning, and restrictive question framing all contribute to the present picture. None alone explains it. Existing free-action SET learning also prevents claiming that spatial control has never been attempted. What is missing is a convincing comparison between **learned joint trajectory construction and competent ordinary spatial/temporal planning**.

My strongest recommended independent question is:

**Given a common radio-aware destination generator, can experience improve coordinated movement between destinations beyond an ordinary trajectory planner, under the unchanged native service objective and execution rules?**

The decision object is the team's intervening motion: which members move together, which stage their movement, and which use intermediate waypoints while others continue serving. The native guard checks individual proposals against existing dependent paths before applying the resulting joint positions. Consequently, a high-scoring destination layout does not certify a useful transition. This is an implemented coupling, **not evidence that guard obstruction is the dominant current loss**. [Guard and transition source](https://github.com/CartmanFatass/My-paper-code/blob/350294379/envs/pettingzoo/relay/routed_core.py#L3294).

This question differs materially from:

- B02's single-member hold library: it permits coordinated, nontrivial intermediate motion.
- The declined handoff design: it is not triggered by a returning member or limited to visiting its vacated position.
- Persistent-service round3: it does not choose return, station dwell, or redeployment commitments.
- Claude's recorded relational-goal proposal: it holds the destination-generation rule common and tests **how to get there**, rather than how a learned coordinator constructs destinations. Numerical future targets can diverge after trajectories diverge; “common generator” must not be misrepresented as identical future target traces.

I recommend selecting this question for concrete DM design effort. I do **not** recommend declaring neural neighborhood selection itself the contribution. With eight UAVs there are only 28 pairs; ordinary pair enumeration, geometry-aware ordering, or adaptive search may be sufficient. A recent primary MAPF reevaluation found strong ordinary selection methods and no clear advantage from the evaluated learned methods under unified comparisons. That strengthens the comparator requirement here; its grid collision constraints and delay objective do not transfer to wireless service. [Tan et al., methods and findings](https://arxiv.org/html/2407.09451v2).

The primary comparison should give learned **L** and ordinary **O** the same information, destination generator, trajectory support, clock, executor, and model access. O should use a competent ordinary trajectory search, including direct motion and staged alternatives. Retain **R** and exact central **TransitHold P** as complete-program references on the same new worlds: existing separate panels cannot rank R and P. P's different clock remains explicit. Lawful `P_BS`, which uses current legal users plus BS observation/memory/station inference, is a different information condition and cannot silently substitute for central P.

A concrete costing envelope is one exploratory fit over 64 H3000 episodes, then L/O/R/P on 16 common fresh worlds: **1 fit, 128 episodes, 384k native steps**. This is a design scale, not an accepted protocol or proof of adequate learning exposure. For illustration, R destination search plus eight trajectory candidates scored at three positions per 30-step boundary would imply approximately **1.44 million maximum static snapshot calls**, including the references. Historical R timings suggest roughly **11–12 worker-CPU hours for native evolution and scoring**, before new learning, initialization, verification, and readback. This is a sensitivity estimate, not a wall-time quotation or upper bound.

The consequential feasibility gaps are the actual trajectory library, optimizer exposure, and lawful scoring model. Fresh-association snapshots do not expose hidden live routing history or guarantee native execution. Full model rollouts could make the proposed cost substantially larger. These details should be resolved in the concrete design, without a mandatory positive pilot. Candidate aliases, shield overrides, and actual displacement should be recorded inside the complete study.

The contrasting outcomes would change real choices:

- **L improves complete QoS and J over O and both retained references, with acceptable reported tails and cost:** retain a conditional learned trajectory-planning candidate; independent training replication becomes a possible next investment.
- **O improves over R/P but L adds nothing:** ordinary transition planning answers the practical question; stop the learning addition.
- **Both lose despite materially different executed trajectories:** stop this trajectory package. Do not automatically prescribe a different network, horizon, or sensing model.
- **Choices rarely execute or collapse to identical trajectories:** the comparison had limited decision exposure; it has not tested the intended trajectory capability. A repair still requires its own value/cost reason.
- **Only proxy scores, blocked-action counts, or early service improve:** no complete-use success. Risk conflicts and technical failures remain visible.

This preserves a worthwhile learning question without promising that learning is necessary. It also avoids turning every negative result into another battery, sensing, or optimizer repair. User-motion prediction remains plausible, but B01 supplied current user sources and BS memory, not user-track memory; it has not yet supplied a stronger investment argument than the trajectory question above.

**MATERIAL_DISSENT: no.** Root's stated non-exhaustion diagnosis is supported. The recommended correction is substantive allocation toward a distinct joint-transition comparison, while preserving round3 and Claude's accepted work. Neither reduced DM count nor the cited failures supports claiming convergence to the uniquely valuable research directions.

### Decision

Root, 2026-09-28: adopt the diagnosis and select `uav_joint_transition` for a
concrete comparison design. A fresh registered DM `/root/dm_joint_transition`
has the source evidence, adverse results and specific question; it may challenge,
simplify or decline the proposed approach. The existing critic retains this
independent context for the resulting specification, not another parallel pass.
The sample arms/exposure/query count are not frozen inputs and no result run is
selected by them alone. The ordinary comparator, executable intermediate motion,
model rights and full cost must support the actual investment choice.

This is independent of the already selected persistent-service study and the
peer's B05. Root will communicate the concrete scope through the established
peer channel while preserving each lead's decisions. This working review remains
current until the concrete design/cost and investment disposition are resolved;
do not archive it as an accepted experiment or require owner approval again.

### Concrete design review

The following is the complete final answer from the same independent critic
after reading the proposed executable comparison at `a354aa32c`. Link targets
are source-pinned or rebased; no dissent is omitted.

**Recommendation: revise O's forecast, then select the bounded comparison. Do not launch the `a354aa32c` design unchanged.** The question merits this purchase; the objection concerns the ordinary comparator, not the number of evaluation worlds or the absence of preliminary positive evidence.

This continues the same independent selection review. I read the complete design and checked its consequential dependencies against current source. The inspected R, P, feedback, guard and energy files are unchanged from the R launch revision. No joint-transition implementation exists yet, so this is scientific selection review, not engineering acceptance.

The design makes a substantive change from the failed B02 ranking study. It exposes simultaneous multi-member staging and intermediate motion, retains the actual R destination generator, and trains directly on complete native rewards. The four-way factored policy can represent coordinated deterministic choices even though sampling is conditionally independent. Its initial non-D exposure is explicitly substantial, while deterministic initialization equals R. These are reasonable exploratory choices, not evidence of sufficient learning exposure.

The principal source-supported objection is [O's frozen treatment of F/unavailable members](https://github.com/CartmanFatass/My-paper-code/blob/a354aa32c/docs/research/candidates/uav_joint_transition/NOTES.md#L147). That approximation is more consequential here than in R's static destination score:

- The production feedback rule commands station-directed movement from lawful positions, margins and station observations. Inside the docking radius, the native energy executor supplies docking motion. These members are not generally stationary. [Feedback](https://github.com/CartmanFatass/My-paper-code/blob/a354aa32c/experiments/candidates/energy_relay_benchmark/b01/feedback.py#L117), [native execution](https://github.com/CartmanFatass/My-paper-code/blob/a354aa32c/envs/pettingzoo/relay/energy_aware.py#L1617).
- Station-directed dock/return actions have a guard exemption. Missing live routing history therefore does not justify treating all currently returning members as immobile. [Guard exemption](https://github.com/CartmanFatass/My-paper-code/blob/a354aa32c/envs/pettingzoo/relay/energy_aware.py#L2169).
- “Unavailable” includes battery below the service cutoff; positive-battery members can still execute limp-home motion. Charging also changes battery through capacity and battery/wait/index allocation. [Availability](https://github.com/CartmanFatass/My-paper-code/blob/a354aa32c/envs/pettingzoo/relay/energy_aware.py#L2152), [charging](https://github.com/CartmanFatass/My-paper-code/blob/a354aa32c/envs/pettingzoo/relay/energy_aware.py#L1842).
- These are not merely hypothetical states: R's original panel spent **28.84% of UAV-steps in F**. That is not the fraction of decision windows affected, but it rules out assuming negligible exposure. [Native summary](../../../../runs/uav_radio_placement/b01_spatial_a01/summary.json).

O evaluates other members' paths against that frozen radio geometry and a worst-member return-deficit score. Errors in the forced members' predicted locations and batteries can therefore alter rankings among otherwise identical eligible-member choices. The current record does not establish their direction or magnitude. It does establish that the forecast discards useful, already-permitted controller information.

**The correction I recommend is to propagate the known control composition in the inexpensive predictor.** Project currently mandated F/limp-home/docking motion and propulsion depletion from lawful observations; account for the declared phase cancellation when a modeled branch enters F. Supply the corresponding shared prediction features to L. State explicitly whatever inexpensive charging/release approximation remains. Do not call that forecast exact: future users, hidden association/guard history and any approximated charging interaction remain limitations.

This does **not** require a live simulator copy, exact future routing, exhaustive counterfactual rollouts, or an additional diagnostic experiment. If incorporating known forced motion makes the implementation materially larger than this bounded study, the preferable alternatives are a consistently narrowed opportunity definition for both L/O or declining this implementation. An expanding charging-model project would undermine the selected independent question.

The remaining comparison is defensible:

- **O's finite search:** two coordinate sweeps plus D/W pair search is a credible ordinary attempt. Its pair pass does not test jointly beneficial detours that are individually adverse. Preserve that limitation; I do not require exhaustive pair-detour enumeration or all `4^8` choices before exploration.
- **R/P references:** retaining both on the same new worlds prevents success against a poor new O alone from earning a practical-use recommendation. P remains exact central TransitHold at its own clock; lawful `P_BS` is not interchangeable.
- **Common R:** preserving its carried targets independently of intermediate waypoints is correct. Initial-L=R must include identical ordering of R generation and feedback evaluation: the existing evaluator passes previous modes to the controller before applying current feedback. This belongs in the already-planned engineering check. [Evaluator order](https://github.com/CartmanFatass/My-paper-code/blob/a354aa32c/experiments/candidates/energy_relay_benchmark/b01/evaluation.py#L432).
- **Learning and exposure:** 6,400 macro decisions and 256 PPO minibatch updates could be informative or insufficient. Full nominal action support is not full executed exposure. The planned alias, interruption, action and displacement readings can distinguish those cases without a pilot.
- **Eight evaluation worlds:** acceptable for this conditional exploratory purchase. They offer limited precision and tail coverage, not independent training replication, safety evidence or confirmation.

The proposed arithmetic is internally consistent: **one fit, 96 episodes, 288k native steps**, at most **1.312 million static radio queries**, and **7.68 million individual kinematic/power-step equivalents**. The original **10–14 worker-CPU-hour** estimate is a sensitivity calculation, not a measured price; revised forecast work must update it. Initialization, learning, engineering, readback and actual node occupancy remain additional or incompletely measured. Removing L's transition queries does not make deployment cheap because every L episode still executes R's destination search.

I judge that cost worth one complete comparison after the comparator correction. It purchases a meaningful test of experience-guided joint motion against two established assets and a matched ordinary planner. An ordinary-only prerequisite would postpone the actual learning question without resolving whether experience helps. Additional fits or worlds are not required now.

The outcome decisions should remain:

| Outcome | Scientific and investment consequence |
|---|---|
| L improves complete J/service over corrected O, R and P without a concerning new observed tail | Retain a conditional useful trajectory package; consider independent training replication separately. No attribution to guard correction or long-horizon reasoning follows. |
| O improves over R/P while L adds nothing | Retain the ordinary path asset if its complete cost/risk warrants use; stop this learning addition. |
| L beats O but fails against R or P | Do not promote it as the useful controller; ordinary-comparator weakness or program tradeoffs remain relevant. |
| Both lose with materially executed alternatives | End this package's investment. No automatic horizon, waypoint, architecture or seed repair. |
| Mostly aliases, overrides or deterministic D | Limited decision exposure/nonactivation, not demonstrated adverse intervention or general unlearnability. A repair is not owed. |
| Technical incompleteness | Preserve missing evidence and actual cost; no scientific sign or automatic replacement. |

Root can resolve this by adopting the forecast correction and letting the DM freeze its exact approximation and updated cost within the same study. This does not require another selection ceremony or alteration of persistent-service or Claude's accepted work.

**MATERIAL_DISSENT: yes.** I object to purchasing the unchanged `a354aa32c` comparison as learning beyond competent ordinary trajectory planning, because its forecast freezes consequential motion already determined by lawful common control. I support the bounded purchase after that specific correction, with the remaining approximation and cost limits preserved.

### Final Root decision

Root, 2026-09-28: adopt the material objection and select the corrected finite
study. The DM accepted it and appended the exact forecast and L0 to
[NOTES](../../candidates/uav_joint_transition/NOTES.md#2026-09-28-utc---adopted-forecast-correction-and-selected-b01-l0)
before executable implementation. This resolves the scientific specification
objection; it is not engineering acceptance or evidence of a successful fit.

The forecast now propagates thirty nominal joint ticks: proposal and current F,
native zero-battery/limp-home/docking motion, clipped nominal displacement and
native power, public capacity with battery/wait/ID allocation, capped charge,
modeled margin and next-tick F release. Intermediate modes cancel on modeled
entry. It preserves prior-F -> R generation -> current-feedback ordering.
Decoded lawful current waits and public parameters are sufficient for that
bounded arithmetic; no live simulator or hidden routing is copied.

Prediction remains conditioned on nominal unguarded positions. It omits
intermediate radio/guard/user-motion updates and uses only the original three
fresh-association service snapshots. These are substantive limitations, not an
exact native forecast or diagnosed error magnitude. L receives conditional
all-D and single-member-alternative joint prediction features. They must not
be assembled as independent battery trajectories when allocation couples them.

The selected data scope remains **one fit, 64 H3000 training worlds, L/O/R/P
on eight new common worlds, 96 episodes/288k native steps and 256 planned
updates**, with the final checkpoint and no automatic additions. The unchanged
static-radio bound is 1,312,000. The correction replaces the independent-path
cost with **9,864,000 candidate-team prediction ticks / 78,912,000 UAV-tick
equivalents**, before forecast reuse. The earlier 10-14 worker-CPU-hour
whole-batch estimate is withdrawn. Historical R and extra-radio scales remain
approximately 7.11 and 1.60 worker-CPU hours; new joint prediction, engineering,
learning and readback require actual measurement. Unknown cost is not zero.

This added arithmetic is justified because it retains a meaningful ordinary
comparator within the chosen motion question; it does not select a new charging
model project. If it grows into a new simulator or materially different
comparison, the DM returns that specific scope/cost issue. Proportionate
engineering checks may provide predictor timing before admission; no
result-bearing pilot, positive-exposure screen or extra selection pass is owed.

The full original dissent and non-exhaustion diagnosis above are preserved.
R/P remain complete-program references; an L win only against O is insufficient.
One fit, eight worlds, common R search cost, finite local ordinary search and
the forecast approximation bound every interpretation. No guarantee of
coordination novelty, safety, learning necessity or sustainable service follows.

The fresh DM owns the selected study through implementation, required
engineering review, exact-input publication, true-node admission, deterministic
same-handle observation, complete independent result reading, publication and
evidence-preserving cleanup. Root owns cross-question integration. Existing
persistent-service and Claude B05 accepted work remain unchanged. The owner
requested genuine parallel questions, not a fixed number of active DMs.
