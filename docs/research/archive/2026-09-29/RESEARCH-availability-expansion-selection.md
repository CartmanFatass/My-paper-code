# Availability Expansion Selection

Completed Root selection and focused independent scientific review, 2026-09-29 UTC.
This is a retired completed project review, not a new standing record or launch contract.
Current standing remains in [RESEARCH](../../RESEARCH.md#parallel-expansion-20260929);
the selected DM writes the prospective implementation and run contract in its own NOTES.
Source inspected by the advisers: `fed55fd0ef329f8fac55dfdf3faeac46158fc1d4`, with relevant G0 sources
unchanged from `007f6d88c`. Advice below was recovered from the actual native final
messages; only absolute local file-link targets were normalized to this pinned source.

## Question and Assignment

The owner asked Root to expand genuinely independent questions after rereading archived
work and both local literature libraries, and explicitly permitted an Astra-max Oracle to
share academic reasoning. The subsequent owner instruction sets a normal target of three
to four substantive Codex DMs, with a few justified reserves, never forced promising labels.
Oracle, scouts and reviewers are not DMs for this purpose.

The Oracle assignment was a read-only construction of the next useful independent question
beyond live retained-control message work and newly selected lawful local history: examine
actual member unavailability and reassignment, or propose a better alternative; reconstruct
the executable host, lawful information, competent ordinary comparator, constructive
prediction, adverse evidence, complete exposure/cost and decision implications. It was
not asked to fill a fixed number of slots. The assigned Oracle is native
`/root/oracle_question_expansion`, `gpt-6-astra` at `max`, fresh context. This is
Root's advisory reasoning mode, not a new constitutional role, review substitute or
independent direction owner.

The existing separate-context Scientific Reviewer `/root/archive_reentry_scientific_review`
then received a focused follow-up on this concrete G0 comparison. It reconstructed source
and inherited evidence before deciding whether the question and complete three-fit purchase
were worthwhile. It was not asked to repeat the whole archive census or approve a run.

## Complete Oracle Recommendation

Recommend one new DM for **joint reserve redeployment and return after a temporary UAV outage**, with a complete learned-versus-ordinary comparison. I do not recommend a second additional question beyond lawful history at this boundary. This recommendation is Root’s design reasoning, not independent scientific review.

**SOURCE FACT: usable host.** At current main `fed55fd0ef329f8fac55dfdf3faeac46158fc1d4`, the relevant G0 sources are unchanged from `007f6d88c`. [UAVSourceIdentifiabilityEnv](https://github.com/CartmanFatass/My-paper-code/blob/fed55fd0ef329f8fac55dfdf3faeac46158fc1d4/ha_ctse_process/uav_g0_environment.py#L257) instantiates actual S7-S1 dynamics: eight UAVs, 30 static users, H500, fixed 50 m altitude, battery/charging/native random failures off. One of six primary UAVs becomes unavailable at O∈180..220 for D∈80..100 steps. Absence disables motion, communication and service; return occurs at the unchanged physical position with a fresh opaque handle. Two other UAVs initially occupy reserve stages. [Source construction](https://github.com/CartmanFatass/My-paper-code/blob/fed55fd0ef329f8fac55dfdf3faeac46158fc1d4/ha_ctse_process/uav_g0_geometry.py#L608) and `current_rows`/`consume_boundary_events`/`step_dense` provide the executable interface. Use these components through a direction-owned runner; do not reopen the old proof-only G0 runner.

**Question and contribution — CONJECTURE.** Can a learned joint reserve policy preserve complete native service better than competent ordinary reassignment when moving a reserve both repairs one vacancy and changes the team’s backhaul geometry? The decision is whether to retain learned or ordinary reserve control for this explicit temporary-outage task. This is a useful control-package comparison and empirical coordination question, not an entity-memory contribution, new MARL algorithm, general churn result, or independently sourced-partner claim.

The constructive prediction is that **which reserve moves, where the second waits, and when each returns matter jointly**: immediately sending the nearest reserve to the vacated primary can sacrifice useful relay geometry or create unnecessary motion around rejoin. The competing explanation is that nearest-reserve dispatch plus an ordinary service-aware joint planner already captures the useful response.

**Recommended first-study contract — CONJECTURE, ready for focused review and DM execution.**

- All arms use the inherited controller before the first observed leave. Subsequently, the learned and primary ordinary arms jointly command both reserves at the leave/rejoin boundaries and absolute ten-step clocks, deduplicating coincident decisions. Commands persist between decisions. Other primary UAVs retain their inherited target-tracking policy; the returned primary resumes its original target. This deliberately tests the source’s complete two-reserve response, not unrestricted fleet reassignment.
- Each reserve chooses **own stage / vacated primary / inward gate / hold current position**: 16 joint categorical outputs, including both-reserve deployment, one-reserve deployment, waiting and return. “Hold” captures the position at the decision boundary. All executed motion passes through the same `actions_toward_targets` and native guard. No residual-amplitude restriction or imitation target.
- Current information is the G0 roster, service, association, registered geometry, issued assignments and public lifecycle mapping, plus observed absence age. Add the **static current user XY map** to both learned and ordinary controllers so the ordinary controller can evaluate radio service. This is an explicit centralized map addition: simulator-exact coordinates, 240 bytes for 30 float32 XY pairs before metadata, supplied once per episode. Existing current telemetry, its acquisition cost and the centralized-supervisor assumption must also be stated. No episode ID, RNG state, realized future O/D, future service or hidden source ledger enters either controller.
- Give both controllers the declared duration law. While absence continues at age a, the ordinary posterior is uniform over integers `max(80,a+1)..100`; the learner gets the same law and age. This is public event history, not private teammate information.

| Arm | Complete controller and role |
|---|---|
| **P: primary ordinary** | Exhaustively score the same 16 joint reserve commands using native S7 radio/routing/delivered-service calculations on isolated public snapshots. Forecast nominal common-tracker positions at +10/+40/+80/+120, integrate QoS with interval weights 10/30/40/40, and average active/absent predictions under the lawful return posterior. After observed return, active probability is one. Include the incumbent nearest-reserve command and both-hold; resolve score ties by incumbent, then less travel. Replan from actual state at every allowed clock. This is finite receding-horizon control, not an optimal upper. |
| **S: retained ordinary reference** | Unmodified [SameInformationController](https://github.com/CartmanFatass/My-paper-code/blob/fed55fd0ef329f8fac55dfdf3faeac46158fc1d4/ha_ctse_process/uav_g0_controllers.py#L226): nearest-reserve dispatch, gate handoff, then stage return after restored-primary participation and sufficient current service. Preserve its per-step readiness checks and report that cadence advantage. P, not S, is the matched-clock primary. |
| **L: learned package** | One central actor with 16 joint logits and a value head; normalized current geometry/service, public event age and prior assignments. A two-layer 128-unit MLP is sufficient as the proposed initial recipe; no private-memory hypothesis or new recurrent architecture. Train with the unchanged native S7 reward, using actual macro-interval reward sums. |

P’s motion forecast is explicitly approximate: sparse snapshots do not reproduce every intervening guard intervention or association change. Read its predicted-versus-realized service and requested-versus-executed movement within the complete study. The existing S2 snapshot helper is a reusable pattern, **not a drop-in G0 implementation**: G0 availability masks and source-ledger isolation require adaptation.

**Bounded exposure — DERIVATION from the proposed design.**

- Three fresh L fits, seeds **2026092911/12/13**; each 512 complete H500 episodes: **768,000 training steps**. Draw distinct training worlds from each seed’s stream, excluding the fixed evaluation IDs.
- Proposed PPO recipe: 32 collections of 16 complete episodes per fit; four epochs and four minibatches per collection, Adam 3e-4, clip .2, entropy .01, gradient cap .5, γ=1 and λ=.95 on the declared macro transitions. This gives **512 optimizer updates per fit, 1,536 total**. Save initial/final parameters and native training curves; no score-selected checkpoint.
- Final deterministic evaluation on **64 common worlds, IDs 2026093001–2026093064**, for three L instances, P and S: `5×64×500 = 160,000` steps. One common no-event reference for those worlds adds `64×500 = 32,000`; before any event all arms share the same controller, so duplicating that reference is unnecessary.
- **Total: three fits, 1,920 complete episodes, 960,000 native steps.** No initial/midpoint evaluation panels, extra seeds, predictor fits or attribution factorial are purchased.
- After the earliest possible onset, at most 33 distinct regular/event decision opportunities occur. P’s ceiling is therefore `64×33×16×4×2 = 270,336` radio/service snapshots, before eliminating identical active-state cases. These are intrinsic planner calls, not native environment rollouts or free work.

**Readers and outcome branches — CONJECTURE.** Primary contrasts are final L−P complete H500 native J and delivered QoS, with L−S retained alongside them. Read actual `last_constrained_reward_metrics["scenario7_reward"]` after each native step; **G0’s `J_event` is a different metric and must not replace native J**. Also preserve weakest-hotspot service, G0 event deficit and catastrophe streaks, absence/rejoin windows, complete pre-event and post-recovery service, guard interventions, path length, selected joint actions and all adverse worlds. Use training instance as the learning inference unit; 64 worlds refine conditional evaluation, not n=64 training replication.

- **L improves complete service/J over P and S:** retain the learned package within this source, with per-seed variation and uncertainty; no component-causal or broad churn claim.
- **P improves over S, while L fails to improve over P:** retain a useful ordinary coordination capability; end this learned recipe’s batch.
- **L only beats P, while S remains better:** insufficient for adoption; the forecast planner may be the weak link.
- **Faster response, better event-window recovery, or higher `J_event` without complete native benefit:** mixed or adverse package result, not success.
- **Similar scores:** report uncertainty and online cost differences; neither equivalence nor training amortization follows automatically.
- **No effective action diversity, guard suppression, or technically invalid endpoints:** distinguish unavailable opportunity, nonactivation and technical failure. Do not strengthen faults or enlarge the action library automatically after seeing scores.

**Costs and hardest assumptions.** Preferred runtime is `wsl_4070`, configured `/home/wu/.venvs/hmasd/bin/python`, one numeric thread and initially one worker, through current admission. G0 uses the default C++ geometry backend; a GPU is not required. Current node headroom was not measured here.

The measured S4 ordinary comparison used **5,377 worker CPU-seconds for 192,000 steps**; rescaling that mixed workload gives **7.47 CPU-hours for 960,000 steps**, merely a planning anchor. New learning, the 270k snapshot ceiling, G0 initialization, compilation and readback are additional or different. There is no measured G0 fit rate. Source construction itself performs two 8! assignment enumerations: constructing 1,536 training sources plus 64 reusable evaluation sources entails **129,024,000 assignment candidates**. Do not hide that initialization work. Engineering is conjecturally **14–28 agent-hours** for the adapter/reader, ordinary predictor, compact learner and engineering review; actual cost remains unknown.

The hardest technical issue is making a **public-snapshot radio predictor that respects G0 availability without accidentally reading its future event ledger**. The hardest scientific assumption is that this designed source leaves consequential joint reserve choices beyond S; no completed native G0 panel establishing that was found. That uncertainty can be answered by the proposed complete comparison and does not require another positive screening ladder.

A sound **alternative first purchase**, if Root judges that uncertainty more valuable than immediate learning, is P/S/common-no-event on the same 64 worlds: **zero fits, 96,000 native steps, the same 270,336 planner-query ceiling**. It directly answers whether richer ordinary joint reassignment is useful. It is a standalone ordinary-control study, not a compulsory gate that automatically authorizes L. My preference remains the three-fit package because it answers the controller-choice question directly; the ordinary planner is a substantial shared implementation cost either way.

**Inherited evidence and rejected alternatives — SOURCE FACT.** S4 B02 already made response immediate, yet mean QoS/J differences were −.01317/−29.69 with wide intervals: another “react faster” study is redundant ([complete reading](https://github.com/CartmanFatass/My-paper-code/blob/fed55fd0ef329f8fac55dfdf3faeac46158fc1d4/docs/research/candidates/energy_relay_availability/NOTES.md#L722)). N7 B01 had two actual learning pairs, both below BCRH on all four final native metrics; later B03’s missing primary must not erase these adverse results ([two-seed intake](https://github.com/CartmanFatass/My-paper-code/blob/fed55fd0ef329f8fac55dfdf3faeac46158fc1d4/docs/research/candidates/variable_n_fleet_churn/VNFC_N7_DIRECT_RETURN_B01_TWO_SEED_RESULT_INTAKE_20260905.md#L1)). Static-N B20, cap-10 duration, FOLR augmentation and FRRIE are therefore not cheap untouched replacements. Independent-partner work still lacks a deployment requirement; time-adaptive control lacks a selected real interaction-cost contract and cannot bypass FSD’s pause. Claude’s coupled-host/D1′ work and Milan dependency remain separate.

No edits, fits, evaluations, Pro calls or children were made. Historical memory was used only to locate availability ownership; current RESEARCH and source checks governed this memo.

## Complete Independent Scientific Review

**Retain The Three-Fit Study**
The question is scientifically distinct from local memory: whether joint reserve deployment and return improve complete service when replacing a missing UAV also changes backhaul geometry. G0 exposes that decision without requiring hidden identity recovery. Direct learning is justified exploratory investment; a positive zero-fit screen is not a prerequisite.

The strongest constructive prediction is that coordinated reserve placement can preserve relay support while repairing the vacancy, then avoid an unnecessarily disruptive return. The strongest alternative is that nearest-reserve S plus the native guard already captures most useful behavior, while learned coordination or approximate forecasting adds harmful movement.

Counterevidence matters. The original S4 summary confirms that removing approximately 14.38 steps of response delay produced QoS −0.01317 and J −29.69, both uncertain. N7 preserves two learned pairs below BCRH, although its intake does **not** establish field-by-field information equality. Neither result answers this joint G0 comparison; neither permits calling availability recovery untouched.

**In-Scope Corrections**
1. **Make P horizon-aware.** Truncate its quadrature at the remaining H500 horizon, including partial interval weights. Otherwise late decisions optimize service beyond the evaluated task. Explicitly give L the same public clock or remaining-horizon feature.

2. **Preserve S’s actual readiness semantics.** Its [`target_map`](https://github.com/CartmanFatass/My-paper-code/blob/fed55fd0ef329f8fac55dfdf3faeac46158fc1d4/ha_ctse_process/uav_g0_controllers.py#L315) requires consecutive native-step observations. A shadow incumbent used by P must update on P’s actual trajectory every step, while P issues commands only at its declared clocks. Calling the state machine only every ten steps can leave its reserve indefinitely at the gate.

3. **Implement the declared information equality concretely.** The public float32 user map must enter L’s features as well as P’s scorer. Association rows must align with the anonymous roster. Build P’s radio snapshots from the public contract and declared availability branch, without retaining the private event source. The S2 helper deep-copies its environment; it is a pattern, not a safe G0 implementation.

4. **Keep native reward and boundary accounting separate from learner settings.** Native S7 uses PBRS discount **0.99**, whereas learner gamma **1** defines the proposed finite-horizon learning return. Do not change the environment gamma. Retain graph-potential increments because native J is not simply QoS plus a policy-independent constant. [`step_dense`](https://github.com/CartmanFatass/My-paper-code/blob/fed55fd0ef329f8fac55dfdf3faeac46158fc1d4/ha_ctse_process/uav_g0_environment.py#L882) returns completed-step service alongside next-boundary events: consume those events once before the next decision, and do not create actor updates from the forced S prefix.

These are bounded specification and implementation corrections, not requests for extra arms or another scientific approval round.

**Reading And Cost**
The proposed outcomes change a real decision: L beating P and S on complete J/QoS supports this conditional learned package; P beating S without L beating P supports ordinary coordination; event-only gains or S remaining better reject package adoption. Three fits are three independent training units, not 192 independent learned replications. Report each fit’s paired effects on the shared worlds; uncertainty does not establish equivalence.

The arithmetic is consistent: **3 fits, 1,920 episodes, 960,000 native steps**, at most **270,336 radio snapshots**, and **129,024,000 assignment candidates** if immutable evaluation sources are reused across arms. The zero-fit alternative saves 864,000 native steps and the learner, but retains substantial predictor engineering and snapshot work. The 7.47 CPU-hour extrapolation is only an anchor; G0 construction, forecasting, training and readback remain unmeasured. That uncertainty warrants honest cost accounting, not a compulsory pilot.

I checked the decisive G0 interfaces, source-construction enumeration, native reward code, S state machine, S2 snapshot helper, original S4 summary and N7 intake. I did not execute G0, inspect N7 raw trajectories, benchmark the predictor or perform engineering acceptance.

**MATERIAL_DISSENT: no** on selecting the direct three-fit study with these corrections. Keep accepted work and existing pauses unchanged; the new DM can implement within this scope without another Root scientific review.

<a id="root-decision"></a>
## Root Decision

**Select the complete three-fit study as `uav_availability_recovery`.** The registered
new DM `/root/dm_availability_recovery`, parent
`01a0e560-4333-7b03-8ff3-759a4add1d9a`, owns the question and matching
experiment, test, notebook, run and scratch paths on shared main. Do not restore an
archived App DM, reopen the old proof-only G0 runner or erase the S4/N7 adverse evidence.

The reason is joint deployment under radio/backhaul coupling, not quicker reaction,
hidden identity memory or changing agent count. The explicit map and centralized
telemetry are added resources, not free decentralized information. P and L receive
the same map, clock and public event law; map acquisition assumptions/cost remain
visible. This first package comparison does not separately identify the map's resource
gain or a new learning algorithm.

Adopt all four independent corrections before execution:

1. P's lookahead quadrature stops at the remaining H500 horizon, including partial
   interval weights; L receives the same remaining-horizon/public clock.
2. P's shadow S state observes P's actual trajectory every native step, retaining S's
   consecutive-step readiness semantics. P still issues commands only at its fixed clocks.
3. The actual map enters L's features as well as P's scorer. Association data align to
   the anonymous roster; public predictor state carries availability without the private
   event source. The S2 deep-copy helper is not a safe drop-in.
4. Native PBRS gamma remains .99, separate from learner gamma 1. Native graph-potential
   increments remain in J. Completed-step rewards and next-boundary events are kept
   distinct, each event is consumed once, and the forced S prefix creates no actor update.

The selected scope remains three fits, 1,920 complete episodes, 960,000 native steps,
at most 270,336 planner snapshots and the stated source-construction work. The zero-fit
P/S alternative is valid but not bought as a prerequisite. The 7.47 CPU-hour scaling is
only an old-workload anchor, not a runtime cap or prediction; 14-28 engineering hours
are conjectural. Use configured remote-first execution and fresh actual-node admission,
initially one numeric-thread worker. Engineering acceptance, exact-input publication
and native readback remain DM work, without another Root scientific approval for the
same unchanged comparison.

MATERIAL_DISSENT: no after these four corrections. Outcome branches and limitations in
the full advice are adopted, including retaining ordinary coordination if P wins,
rejecting adoption if S remains better, and keeping uncertain, nonactivated and
technically missing results distinct. No automatic fault-strengthening, action-library
expansion, extra seeds or repair run follows any outcome.

At assignment this joined retained-control messages and lawful local history as the third
selected question. Before publication the message DM published its full B05 reading and
changed that direction to reserve at `93956bb96`; two new questions remain in development,
not three simultaneous admitted training jobs. Oracle continues the owner's requested
reserve search; another question is selected for value, not to count completed work as live.
Existing Claude coupled-host/D1-prime and restoration ownership, accepted
operations, Milan dependency, FSD/PPC pauses and G33 freeze are unchanged.

