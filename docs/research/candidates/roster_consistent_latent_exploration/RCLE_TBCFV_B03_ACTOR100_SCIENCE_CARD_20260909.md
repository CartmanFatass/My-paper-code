Claim: On one new paired training seed of the fixed TBCFV host, increasing FLEX's claim-score weight from 1 to 100 may reduce native unserved demand after a roster change at the same learning budget.
Binding MARL structure: multi-agent credit assignment; the intervention changes the relative manager/claim score contributions while shared agents coordinate through an exogenous roster change.

# RCLE TBCFV B03 actor100 — science card

Date: 2026-09-09. Object: `RCLE-TBCFV-B03-ACTOR100`. Class: **B/EXPLORE**.
Scientific selection: complete Innovator decision `PRO_FINAL` at
`c80efaea6b0df9f22fb08bc1a5706492108836a9`,
[response](pro_packets/20260909_post_a02_innovator_recovery/archive/RESPONSE.md), §§三–六.
[Selection intake](RCLE_TBCFV_POST_A02_INNOVATOR_INTAKE_20260909.md) checks its conformance.
Root separately allocated exactly this pair in main `664afecaf36c6f436dbe870fd6c80afb11a05d75`,
`docs/research/portfolio/EXPERIMENT_TRACKING.md` §“RCLE recovery received and selected B03 allocation”.
This card is frozen under the 2026-09-03 unattended object delegation. No B03 scientific output
was observed at freeze. Pro selected scope; it did not accept implementation or launch a run.

## 1. Question, motivation and ceiling

Does the fixed W100 learning law improve final native service relative to a newly trained W1
control, holding the FLEX model, available information, seed and exposure fixed? The next
observation is the paired final U difference, with both arms' improvement from initialization
and recovery score alongside it. The coefficient 100 is an openly outcome-informed order-of-
magnitude choice after A02, not a tuned optimum, exact inverse-share calibration or unbiased
policy-gradient correction. It weights an episode's mean claim score; it does not set a
pointer-only learning rate.

A02's eight frozen graphs all had actor/pointer shares below 1% and small block-average
conditional TV; zero-baseline graphs still had shares below 1%. These motivate the test but
do not show that reweighting works. Parameter changes and some individual TV values above
0.01 contradict an account of no actor movement. Shared encoders, changing baselines,
visitation, manager allocation, event heads and noise can all mediate this whole-law effect.
No exclusive pathway or cause of B02's flat service is identified here.

Ceiling: a signal or counterexample on **one paired training replicate**, this host, fixed
FLEX and budget. No stable superiority, arbitrary-roster generalization, C1P1/FLEX package
effect, tuned-generic-baseline victory, optimum coefficient, pure pointer causal effect,
recovery-time noninferiority, UAV result or C claim. Neither a positive B nor a further A is
a qualification for a later independently justified B. No successor is allocated.

## 2. Host, information and native consequence

Reuse the unchanged definition card's §“Frozen physical host” and §“Shared maximum learned
architecture”, as instantiated by B01/B02. The host has 120 sectors, six beacons, H=64, an
exogenous membership/epoch boundary at tick24, simultaneous claims every four primitive
ticks and the unchanged six-claim support and MOVE-TO-CLAIM decoder. Each primitive tick
first applies any event, exposes the current public state, performs any claim operation,
moves current agents, then measures service. No service observation precedes the post-event
claim/movement at tick24.

Roster membership is an unordered physical-agent set, with no policy ID or persistent
slot. Expansion retains survivors and places newcomers in unoccupied sectors; contraction
uniformly selects departures and retains survivors' physical positions. Current rank is
recomputed. Event/newcomer pulses appear only at the prescribed claim clocks and carry no
future information. The selected paths contain one event, not a leave/rejoin history or
replacement study; no new rejoin memory is introduced. No N-specific head or parameter is
selected. Policy inputs remain the own physical features, current public agent/beacon set
summaries, time, N, event flags, candidate beacon features and plan latent. The latent
provides no hidden private clue beyond those public inputs.

The native chain held fixed is: roster event → current physical entities and survivor state
→ common public summaries and own features → FLEX plan update plus six-way claim sampling
→ actual complete-episode score-gradient training → movement and normalized unmet demand.
The claim opportunity clock is every four primitive ticks; the learner uses complete
64-tick undiscounted returns. No semi-Markov discount or opportunity-time reward replaces
that return. Shared-policy partner co-adaptation is endogenous to each arm's training.

## 3. Arms and exact learning change

Exactly two independently trained instances of the **same FLEX-REKEY package**, reporting
labels `W1` and `W100`. Both allocate the same maximum 26,161 scalar model, from the same
Xavier/zero-bias initialization; the final layers of both FLEX event heads start at zero
and remain trainable. No seed18 final state is loaded or warm-started. Both arms copy the
common initial tensors. Any extra untrained initialization-helper allocations are counted
separately from the two training instances.

For a complete 64-episode balanced block, let s_M,e be the existing mean of the manager
log-density scores actually used in episode e and s_A,e its existing mean of claim
log-probabilities. Preserve the separate episode means and the existing averaging law.

`L_lambda = -(1/64) sum_e stop(Y_e - b_cell(e)) * (s_M,e + lambda * s_A,e)`

W1 uses lambda=1; W100 uses lambda=100. With `g = grad_theta L_lambda`, apply
`theta <- theta - 0.02*g/||g||_2` if g is nonzero, otherwise no parameter update. One complete
block performs one joint backward and one full-vector step call. The 400 planned step
calls do not imply 400 nonzero steps. Preserve measured raw norm, applied delta norm and
separate zero/nonzero counts.

After the parameter step, each arm independently updates its eight initially zero cell
baselines as `b_c <- 0.95*b_c + 0.05*mean(Y_e in cell c)`. This still occurs if g is zero.
Return, baseline, stochastic samples and old-epoch samples keep the original stop-gradient
semantics. Keep the derivative through the **current deterministic FLEX event heads** to
the claim score; do not detach that entire output. Optimize the unchanged complete-return
`Y = 1 - sum_(t=0..63)(u_t)/64`, not the post-event-only U.

No changed reward, entropy, Adam/momentum, auxiliary loss, return normalization, clipping,
adaptive balancing, per-group update or extra backward. The historical B01/B02 functions,
cards, seed meanings and results keep their original laws. Implement the real weighted
loss in the new object's path; writing a configuration label alone is insufficient.

## 4. Seed, pairing, training and final panels

One fresh paired seed **19**. Root key is SHA256 of ASCII
`RCLE-TBCFV-B03-ACTOR100/seed/19`:
`4b17629c25d71afceed93bbe657c0b5799d468d1f5673d90a7ceee644ec474c5`.
Use the existing derivation with identity `RCLE-TBCFV-B03-ACTOR100` and block index 0.
Training and evaluation keep distinct purpose domains. In every stochastic semantic
coordinate both arms' **true package value is FLEX**. W1/W100, lambda and execution order
must never enter random addresses. Pair initialization, exogenous scenarios and the
manager/actor streams allowed by the original semantics; each arm still samples its own
policy and may diverge in actions, states, baselines and returns. Matching cell/index means
matching the declared scenario, not forcing equal trajectories.

Each arm trains 200 complete updates × 64 episodes (eight episodes in each cell):
`6→6, 10→10, 6→10, 10→6` × `ACTIVE_CONTINUATION, NEW_EPOCH`.
Keep all 200 block summaries and per-cell Y/U/tau curves, not only 25-update display points.
Evaluate update200 only, with no intermediate checkpoint selection or added evaluation.

All four evaluation panels share the same seed19 held-out scenarios, indexed by cell/index:
`8→8, 12→12, 8→12, 12→8` × both conditions, exactly 256 episodes per cell.
Panels are W1-final, W100-final, one **shared initialization FLEX** panel and one unchanged
INDEPENDENT-NEAREST panel. The W1 complete invocation owns the initialization panel once.
Neither its level nor the reference determines whether the paid training proceeds.
Reference behavior: every agent selects its current nearest beacon, ties to the smaller
index, no latent or training; its unavailable Y stays null with the reason. It is an
achievable simple level, not an upper or trained control. Old seed18 W1-like results cannot
replace the new W1 control.

## 5. Primary measurement, uncertainty and interpretation

Per assigned episode, `U = sum_(t=24..63)(u_t)/40` and Y retain their native definitions.
Tau is the first h in 0..36 for which four consecutive unmet-demand values from tick24+h
are zero, otherwise 40. It is a bounded score with a failure code, not uncensored recovery
time. `40U` is cumulative normalized unmet demand, not raw service units or agent-ticks.

**Primary:** on ACTIVE_CONTINUATION paths 8→12 and 12→8,
`Delta_U = (mean_256(U_W1-U_W100)_8to12 + mean_256(U_W1-U_W100)_12to8)/2`.
Positive favors W100. Pair by actual cell/index and publish both arm levels, each path
difference and the equal-weight primary; keep every assigned scenario, failure and interval.
Do not substitute a favorable cell or the eight-cell mean.

Companions: each arm's `G_U = U_init-U_final` on the same two equally weighted paths,
40U, tau and fraction tau=40; all eight cells' U/tau/Y/F and the declared eight-cell
secondary mean. NEW_EPOCH is not a pure identity-erasure intervention.

Use existing NumPy or equivalent arithmetic on retained paired-scenario d=U_W1-U_W100.
Per path, report sample `SE = sd(d, ddof=1)/sqrt(256)`. The primary's SE is
`sqrt(SE_1^2+SE_2^2)/2` only if the actual cell-domain draws are independent; if they share
an exogenous sampling unit, retain covariance/group that actual unit. Same index names
alone imply no cross-path pairing. An optional approximate 95% interval is conditional
scenario Monte Carlo uncertainty for this pair of fitted policies. One paired training
seed supplies no estimate of training-population variance; episodes, ticks, agents,
checkpoints and cells are not independent training seeds. No bootstrap or new model call
is needed for this summary.

**MEI: absolute U=0.05** for Delta_U and G_U, equivalent to two normalized unmet-demand
ticks in the 40-tick window. The physical scale is easier to interpret than a percentage
and distinguishes the small historical B02 G_U≈0.002. Tau=4 ticks describes one claim
period of reverse tradeoff; it is not another noninferiority gate, and tau need not leave40.

**Headroom:** no identified upper-minus-tuned-generic `H_A1` record exists for this host.
B02's reference U≈0.282 versus learned≈0.707 (gap≈0.425) is a diagnostic gap, not H_A1.
Reuse the host's unchanged public information, action and reference set; no matching tuned
generic baseline result is claimed. A headroom or baseline-tuning study is not bought here.

How the result will be interpreted: a positive difference above the MEI motivates considering
one independently trained pair, with native tradeoffs visible. A smaller positive difference
is a local signal whose value depends on G_U and cost. An adverse difference is a useful
counterexample and may also merit a specifically selected replication. Relative benefit
without G_U>0 can mean less degradation. The following overlapping descriptive branches
control intake; they are not a C test or automatic successor allocation.

| Complete observation | Reading and possible recommendation |
| --- | --- |
| Delta_U≥0.05 without a same-scale reverse native tradeoff | W100 service signal on this seed/budget; consider a separately selected fresh pair, without stable or causal claims. |
| 0<Delta_U<0.05 | Small local positive signal; judge another named comparison using path outcomes, G_U and actual cost. |
| Delta_U=0 or -0.05<Delta_U<0 | No positive W100 signal; retain the exact zero/adverse value and Monte Carlo ambiguity. |
| Delta_U≤-0.05 or a material service/recovery loss | Counterexample to this fixed weight at this budget; a justified independent replication may test recurrence. |
| abs(Delta_U)<0.05 and either arm G_U≥0.05 | Native learning without a same-scale law advantage; name the improving arm. |
| abs(Delta_U)<0.05, both G_U small and tau saturated | No useful benefit shown by this 200-update comparison; end this spend and return to object selection. |
| Favorable primary with W100 G_U≤0 | Report relative benefit and absolute deterioration together; do not call it improvement from initialization. |
| Opposite paths, U/tau tradeoff or intervals crossing interest scales | Mixed/undecided; retain all paths and companions, with U=0.05/tau=4 as descriptive scales. |
| Damaged training, information or primary readout | Report the actual failure and counts; only independent narrower facts survive. No algorithmic polarity. |

No requirement that every path or future seed improve. Gradient/probability motion without
native benefit is not performance success. No row proves equivalence, that zero baseline
is better, or that RCLE should close.

**Predictions before execution:** DM and Pro both predict, with low confidence,
`0<Delta_U<0.05`, with tau40 still common. The strongest competitor is Delta_U≤0 from
amplified noise or displaced useful manager/encoder credit. A valid Delta_U≤0 refutes the
positive forecast; Delta_U≥0.05 supports its sign but refutes its small magnitude. Preserve
uncertainty crossing those scales. Owner prediction: **not taken (unattended)** unless an
actual reply arrives. A02's two failed DM predictions stay failed; Pro's previous
manager-dominant/small-change forecast remains supported.

## 6. Exposure, complete cost and stops

[Machine-generated plan](RCLE_TBCFV_B03_ACTOR100_EXPOSURE_PLAN_20260909.json) rechecks the
existing configuration arithmetic and seed-key hash, without constructing models or states.

| Work | Episodes | Primitive ticks | Backward / joint-step calls |
| --- | ---: | ---: | ---: |
| Two arms × 200 × 64 training | 25,600 | 1,638,400 | 400 |
| Two final eight-cell panels | 4,096 | 262,144 | 0 |
| Shared initialization FLEX panel | 2,048 | 131,072 | 0 |
| Scripted reference panel | 2,048 | 131,072 | 0 |
| Total | 33,792 | 2,162,688 | 400 |

Parameter path budget per arm is at most 200×0.02=4, about0.19 of the historical
initial norm≈21.2. This is a motion opportunity, not net displacement or a capability
target. Measure seed19's actual initial norm inside the charged invocation. Scientific
model/episode/backward/update exposure at freeze is zero; technical fixtures are reported
separately and their runtime is charged to the whole object.

Dominant work is two arms × one seed × 200 blocks × 64 episodes, plus four fixed 2,048-episode
panels. Each claim scores six legal candidates; no joint-action enumeration, trajectory
tree, beam/best-of-many policy search, solver search or coefficient grid. A zero-baseline
pair would have the same 33,792 episodes/400 backward calls; the unselected package×weight
factorial would require63,488 episodes/800 calls. These are counts, not timing ratios.

Planning references only: B02 whole learned invocations71.47/71.23s, reference2.62s and
whole chain152.622s. Its first C1P1 call included init; its second FLEX call did not.
Those are not B03 timings or standalone panel times. New-law and necessary startup/check
costs remain unknown; no separate calibration experiment is requested.

Hard limits: **600s per complete learned invocation; 1,500s cumulative execution wall
for the entire object**. Count startup/build, initialization, training, final evaluation
and publication in the relevant complete invocation. W1 owns shared init once. Charge
actual necessary preparation, focused check, reference, merging and final publication
once within the whole-object sum; no cap resets across scripts. Report study elapsed
critical path separately from the sum of complete logical invocation walls. No historical
budget balance, automatic extension, retry, added arm, coefficient or seed is available.

Normal stop is completion of the allocated updates, all four panels and publication.
Finite poor returns, zero advantages, tau40, zero gradients or a poor first arm are not
outcome-dependent early stops. Stop affected work for actual time/resource limits,
nonfinite numbers or a concrete reward/information/event/RNG/training/readout defect.
If W1 cannot form the pair, do not blindly spend W100 merely to fill an arm. Keep actual
completed work; partial execution is not complete. Missing init invalidates G_U but not
otherwise trustworthy final Delta_U; missing reference need not invalidate that comparison.
Missing planned panels still makes the whole object incomplete. Optional resource telemetry
absence is `resources_unmeasured`, not automatic scientific invalidation; mandatory admission
and complete-cost bounds remain binding. No automatic rerun follows a defect.

## 7. Engineering scope and execution route

**Engineering scope §4 needs: none.** Reuse ordinary existing model/native execution,
serialization and required external task supervision. Add no scheduler, heartbeat,
checkpoint/retry service, registry, validation framework, provenance gate, full-parameter
telemetry or A02 decomposition. New non-test source≤2,000 lines, runner≤600, and research
test wall≤300s; orchestration30% is a review signal, not a gate or padding target.

One focused verification covers the actual weighted loss, lambda1 control limit,
step-before-baseline order/stop gradients, FLEX semantic RNG labels and primary-output
sign/pairing. Independent semantic review is required for the changed learning and
comparison boundary. Reuse unchanged host checks; no whole-history replay or additional
result panel. Technical test exposure and actual check wall are reported separately.

Portable scientific execution remains **remote-first wsl_4070, CPU FP64, one compute
thread**, exact committed/pushed source in a detached execution worktree under the existing
agent-task supervisor. No device/precision/thread/node change or local fallback is allocated.
Every actual invocation immediately runs the same-node `admit-memory` preflight and runner
in one command joined by `&&`; both physical and effective available memory must be≥4GiB.
Source/cwd and staged command are checked as existing ROOT_OPERATIONS requires, without a
new conformance framework. The assigned CM owns observation through collection and technical
acceptance, with explicit handover if needed under EXPERIMENT_MONITOR. No old heartbeat
adoption condition is imported.

## 8. CM assignment and records

Deliverable: implement, independently review, publish and execute this one exact pair,
then collect native rows/checkpoints/curves, complete-cost/admission receipts and an E0
technical result. CM retains its execution and observation ownership through acceptance.

Designated shared authoring checkout: `C:/Projects/HMASD-worktrees/dm-rcle-a02-20260906`,
branch `codex/rcle`. Owned implementation surfaces: a narrow new
`experiments/candidates/roster_consistent_latent_exploration_tbcfv_b03/`,
`scripts/run_rcle_tbcfv_b03.py` and a necessary fixed launch wrapper, mirrored focused
tests, this direction's B03 CM/result records and
`temp/directions/roster_consistent_latent_exploration/exp/` runtime artifacts. DM owns this
card, intake, DIRECTION, owner items and audit. Serialize the shared index. Root integrates.

Reuse code entry points `roster_consistent_latent_exploration_tbcfv/models.py`
(`averaged_episode_score`, `exact_advantage_loss`), `_tbcfv_b02/study.py`
(`fixed_norm_sgd_step`, block update, training, init/final/reference helpers), and the
existing native episode/RNG helpers. Preserve old object functions/results; B03 owns its
weighted-loss and W1/W100 publication changes. Implementation-relevant source pointers
are the response §三 and this card §§2–5, not an instruction to reread history or literature.

Acceptance: §§2–7 above and evidence spec §§4,5.2,11.4,11.8.6–11.8.7; real learning and
all assigned output counts, primary pairing/sign, finite measured native endpoints,
focused check, independent review and complete-cost receipts. State actual deviations and
dependency limits. Budget/stop: §6 exactly, no other result invocation or automatic successor.
CM sends an accepted-handle update to DM for Root tracking, without parallel polling.

At final technical return, DM performs scientific intake, scores the recorded predictions,
publishes the Chinese result brief and object decisions, and returns any direction-tier
next-object question to its proper node. No C consumption state exists for this B.
