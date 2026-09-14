Keep the current allocation-coordinate family parked. The native source has consequential ground-user geometry, but it does not supply the old metric allocator's semantic task binding, allocation action, or additive service law. Its ground base station is not a service-reward anchor. Porting the old map to SINR-ranked slots, adding a distance feature, or weakening the generic actor would not define the requested native-value comparison.

**My final direction decision is PARK_CURRENT_ALLOCATION_COORDINATE_FAMILY.** This is a formed, reversible family-level scientific disposition, not a proof of equivalence, impossibility of geometry-aware learning, or closure of the broader direction. I do not select a native successor comparison or recast in this consultation. The concrete yield is the source-to-learner boundary below and a narrower re-entry question about an actual geometry-bound actor operation, rather than a presumed base-station or transport-allocation opportunity.

## 1. Smallest supported conclusion and decision burden

The supported conclusion is about the proposed bridge: the accepted five-UAV host is a partially observed, dynamically coupled velocity-control problem, not an instance of the registered one-quantum ground-transport allocator. That distinction does not make it an unsuitable MARL benchmark. It means that a defensible MGTAP continuation needs a new, explicit mapping from actor-available geometry to a learned velocity operation, with a competent same-information generic alternative. The present source inspection does not justify calling an unmodified allocator, an information cut, or a generic optimizer amendment that mapping. [E7, §§2–3 and 9.2][E7]; [E10, `make_real`][E10]; [E14, `step`, `_greedy_connection_assignment`, `_compute_reward`][E14].

The ceiling is **source-backed B/EXPLORE question formation on this fixed five-UAV environment and accepted recurrent PPO path**. No native MGTAP result, metric efficacy, stable superiority, equivalence, pure metric causality, ground-base value, warehouse or UAV delivery/sensing/relay efficacy, variable-fleet transfer, churn, convergence, safety, or broad MARL conclusion follows.

I am not asking for a positive preliminary result, a uniquely established mechanism, a tuned headroom certificate, persistent entity IDs, an exact optimum, or a support census before B. Nor is the absence of an already implemented MGTAP native actor itself a reason to park. The reason is the inadequacy of the specific allocation-to-native binding proposed by the available material, after considering the alternatives below. A newly specified local geometric inductive bias could be legitimate B even if suboptimal or unsuccessful. The evidence specification explicitly permits that route; its §§11.8–11.9 do not permit replacing the missing scientific comparison with a search-before-learning requirement. [E1, §§5.2, 11.3–11.4, 11.8–11.9][E1].

## 2. What the accepted source actually connects

### Environment event and ownership

`make_real` fixes five UAVs and 50 uniformly placed ground users, a 1000 m square, height limits 50–150 m, 256 one-second steps, component speed 30 m/s, free-space/vectorized channel evaluation, no shadowing, no FDMA and the default reward. Resets generate the UAV and user positions; the inspected native `step` moves UAVs, not ground users. Each of the five actors owns its UAV's command and recurrent history. It does not own a persistent local-observation slot, a pallet/sortie quantum, a semantic task queue or a connection-allocation action. [E10, `make_real`, `HoldState`][E10]; [E14, `reset`, `_generate_user_positions`, `step`][E14].

**One material correction to the caller's description is necessary:** the source is not a one-user-per-UAV assignment. `max_connections` is 10; the greedy allocator permits **at most one UAV per user and up to ten users per UAV**. The user-connected flag and each UAV's connection count enforce those constraints. Replacing this with one quantum per UAV would change the native task, not clarify it. [E14, `__init__`, `_greedy_connection_assignment`][E14].

### Actor information, critic information and slot meaning

The base observation has 104 components: normalized own position; twenty zero-padded user triples containing relative x/y and normalized SINR; ten zero-padded other-UAV quadruples containing relative x/y/z and normalized SINR; and time. With five UAVs there can be at most four actual other-UAV records, notwithstanding ten available slots. Eligibility uses the SINR threshold and records are sorted by descending SINR. The third user component is SINR, not a distance, despite the older dimensionality comment. The executing observation constructors, rather than that comment, establish its meaning. [E14, `_get_observation_vectorized`, `_get_observation_reference`, `_local_user_entries`, `_local_uav_entries`][E14].

`actor_features` appends three last sent normalized velocity components and remaining hold divided by four, giving 108 inputs. A change of rank does not mean the same slot still denotes the same user. Conversely, anonymous ranked records still contain valid current geometry: persistent IDs are not necessary for every possible geometric actor. A proposed local metric must bind to each current record, not silently to a lasting rank identity. Physical distances would also have to respect the source's different horizontal and vertical normalizations rather than treating every normalized coordinate as the same unit. [E10, `actor_features`, `own_positions`][E10]; [E14, observation constructors][E14].

The separate critic receives the normalized 116-component global state—five UAV positions, fifty user positions and time—plus twenty prior command/hold entries, for 136 inputs. It is assembled before current decisions. `local_indices`, full connection/SINR diagnostics and `entity_positions` are not actor inputs. Giving those to a geometry treatment while leaving the generic actor local would be an information advantage, not a metric-learning result. [E10, `critic_features`, `local_indices`][E10]; [E12, `collect_episode`][E12]; [E15, `reset`, `step`][E15].

### Legal action and physical consequence

The policy samples a three-coordinate tanh-Gaussian velocity. The environment scales each component by 30 m/s, advances one second and clips the resulting position to the stated boundaries. Consequently, a changed pre-tanh mean or sampled command is not automatically a changed physical displacement at a saturated boundary. The source contains a real action-to-service path, but movement magnitude alone is not its value criterion. [E11, `sample`, `tanh_log_prob`][E11]; [E14, `step`][E14].

The opening-hold semantics remain part of the host: T chooses duration one or four only at time zero; a four-step command is sent through time three, with feedback resuming at time four. G can select a legal velocity every primitive step, including repeating a command or hovering. Observation, recurrent-state advancement and reward collection continue during a hold. None of those distinctions is selected as an MGTAP treatment here. [E8, §§2–3][E8]; [E10, `HoldState`][E10]; [E12, `collect_episode`][E12].

After motion, the source recomputes UAV–user and UAV–UAV channels, then connections. Free-space path loss depends on physical three-dimensional distance. With FDMA disabled, a UAV's received signal is compared with noise and power from other UAVs. The connection routine sorts eligible UAV–user pairs by SINR and applies the capacity constraints. The learned action is still velocity; it is not the connection matrix that this routine produces. A shorter own link can have a different team consequence from its isolated-link consequence because positions also affect interference, eligibility and the eventual served set. [E14, `_uav_user_geometry`, `_compute_path_loss_matrix`, `_compute_uav_user_sinr_matrix`, `_update_channel_state_vectorized`, `_greedy_connection_assignment`][E14].

### Native team reward and PPO consumer

Writing C for the number of connected users, the accepted default reward is

\[
R_t=0.7\,C_t/50+0.3\,Q_t,
\qquad
Q_t=\frac{\sum_{(i,j)\,\mathrm{connected}}\operatorname{clip}((\mathrm{SINR}_{ij}-3)/30,0,1)}{\max(C_t,1)}.
\]

This reward-quality normalization is different from the observation's clipped `(SINR+10)/50`. The base environment distributes `R_t/5` to each UAV. The adapter also returns an averaged scalar, but the accepted learner deliberately obtains the native team reward by summing the original `info['rewards_dict']`. A new comparison must preserve that accessor, not introduce another division by five or substitute a geometric surrogate. [E14, `_compute_reward`, `step`][E14]; [E15, `step`][E15]; [E10, `team_reward`][E10]; [E12, `collect_episode`][E12].

The learning path is Linear(108,64)/tanh/GRU-64 followed by the velocity head, with shared weights but separate UAV histories; the separate critic is 136→128→128→1. For B02, `agent_compound` retains each active UAV's velocity log density, together with its time-zero duration density when applicable, in one ratio. `clipped_policy_loss` clips each such ratio, sums active-agent terms, and averages primitive rows without dividing by five or the active count. All-held rows retain recurrent, critic and reward contributions. Return-to-go uses every primitive reward with gamma one and no bootstrap; detached advantages are normalized once per 512-step rollout; gradients are truncated in 32-step chunks; four full-rollout epochs produce four joint actor/critic Adam calls. [E8, §3][E8]; [E11, `Actor`, `Critic`, `joint_terms`][E11]; [E12, `returns_to_go`, `clipped_policy_loss`, `recurrent_outputs`, `update`][E12]; [E13, `Config`, `run_pair`][E13].

Thus the complete relevant chain is **UAV motion → distance-dependent channels and coupled service → each owning actor's current local records and memory → its legal velocity density → actual primitive team reward and common PPO advantage → subsequent learned velocities and native service**. A surviving geometry proposal must specify where its learned operation changes this chain; the existing chain alone is not evidence for that proposal.

### The base-station non-binding

The base station defaults to `[500,500,30]` and appears in metadata/diagnostic positions. It is absent from the actor features and the inspected global state, and the accepted default channel/connection/reward path does not use it as a service or backhaul endpoint. This rules out interpreting the constant as an already present native ground-base value opportunity. It does not mean the area center is unknowable from normalized coordinates, nor that ground-user geometry is absent. A center-distance feature would be a deterministic coordinate construction, not evidence of base-station service binding. [E14, `__init__`, `_get_state`, `step`, default channel and reward functions][E14]; [E10, feature constructors][E10]; [E15, `get_current_state`][E15].

## 3. Historical evidence retained, including the strongest contradiction

MGTAP B03 remains a valid same-panel, three-seed exploratory rate comparison. Its fresh rate-0.1 contrast is +0.008410135905, but equal four-rate selection leaves only +0.000655478018 in normalized AUC. FREE's own selection gain is +0.200872633192; selected FREE exceeds rate-0.1 METRIC by +0.192462497287. The selected seed contrasts include −0.000671047635 between two positive values. Both arms select the grid edge, rate 3.0. These observations support generic finite-optimization sensitivity on the old toy, not equivalence, a native UAV result or a theorem against metric representations. [E5, “Direct measurements and ordered rule”][E5]; [E6, “Rule applied verbatim and direct result”][E6].

The old oracle-minus-selected-FREE endpoint gap, 0.040598777488, is neither the AUC estimand nor a transferable amount of UAV headroom. B02's positive below-MEI observation, B03's small residual, grid-edge uncertainty and same-panel selection remain visible. Both historical C objects keep their terminal structural-nonidentification meanings; neither is reopened or retrospectively supplied with efficacy data. [E2, current B03/B02 and historical boundary sections][E2]; [E3, “Bounded scientific reading”][E3]; [E6, “Headroom, resources and technical limits”][E6].

The native UCOPE evidence is also mixed, not a metric result. P24's two fresh T−G means are +0.0433518665 and −0.0503654225, averaging −0.0035067780. In the positive pair, G−hover is −0.0282038164; in the negative pair, T−hover is −0.0332644846. The four-pair outcome-informed descriptive mean is +0.0058553213, while P21 keeps its original UP reading. Larger opening displacement occurs with both native signs. Changed local inputs, more movement or a positive opening reward contribution therefore cannot rescue the complete-return loss or establish geometric information value. [E9, §§2–4][E9].

**The strongest contradiction to parking is substantial:** physical user geometry is genuinely reward-relevant and already legally observable, the recurrent actor can in principle benefit from a better geometric inductive bias, and historical native return varies enough that a useful effect is not excluded. Rank anonymity and interference do not prohibit a local set-based actor. Nor does B03 settle the behavior of a different state-dependent representation on this host. These facts prevent any direction-wide impossibility conclusion. They do not, by themselves, choose which geometry operation and competent generic comparison should replace the stopped allocator.

The live alternatives are ordinary contextual function approximation from the existing relative positions and SINR, geometry-aligned parameter sharing that has not yet been specified as a native comparison, recurrent/policy optimization effects, and co-adapting interference/connection dynamics. I do not identify one as the unique native cause. Comparator competence and tuned native headroom remain unestablished in the listed results; they limit claims but do not erase trustworthy comparisons or impose a separate competence-only experiment. [E8, §§5–6][E8]; [E9, §§2–4 and 7][E9].

## 4. Options and why the runner-up is not selected

**Selected: retain the reversible family boundary and return the source yield.** Four superficially attractive transfers fail to specify the requested comparison:

| Candidate transfer | What the source permits | Why it does not supply the claimed MGTAP bridge |
| --- | --- | --- |
| Ground-base distance or backhaul cost | A constant base position exists in diagnostics. | There is no accepted reward/backhaul consumer. Adding one changes the host; adding only its distance establishes no base-bound service mechanism. |
| Distance feature or physical-unit renaming | Current relative user geometry is already available to both actors. | A new feature may affect learning, but naming redundant information is not the requested consequential metric-binding operation. Information equality must not be replaced with a weaker generic input. |
| Old fixed task-neighborhood map on local ranks | The actor has fixed-size ranked slots. | Slot numbers are not the old semantic task tokens; the native action has three velocity coordinates, not eight role–task score channels or a task-coupling decoder. A rank transposition is not the old value-preserving task-binding intervention. |
| Nearest-user/shortest-ground assignment | Physical distance affects the channel. | Service also depends on other UAVs, thresholds, capacities and native greedy association. Replacing that path with additive assignment or a synthetic adapter changes the question. A nearest-user controller could be tested as a heuristic, but is not automatically a metric-coordinate learner comparison. |

These are source-based incompatibilities of particular transfers, not a requirement that a new heuristic be optimal. The registered B1 itself explicitly excludes connectivity thresholds, interference, complementarity and dynamic routing from its additive UAV bridge and calls for a new object where they matter. That warning remains pertinent; its old formal admission gates and warehouse sequence are not imported as prerequisites for a new ordinary B. [E7, §§2.2–2.6, 3 and 9.2][E7]; [E1, §§11.1–11.4 and 11.8–11.9][E1].

**Runner-up: a new state-local geometry-sharing actor against an uncut, fully informed generic actor.** For example, tying a learned response to current physical user bearings, or sharing learned responses across nearby current records, would be more substantive than attaching another distance. Such a method could alter the velocity mean and its PPO gradient without changing reward or buying information. It is not ruled out by this decision.

It is not selected because the candidate label still leaves the scientific contrast unresolved: which coefficients are shared, which operation consumes the metric, how the full generic action map is retained, and whether an apparent difference is introduced by information loss, a restricted decoder, added capacity, or an ordinary change of optimizer geometry. The native source specifies none of that new comparison, and I do not replace those choices with an arbitrary kernel, rank rotation or extra head simply to manufacture a successor. This is a judgment against selecting an underspecified or weakly motivated bridge now, not a demand to disentangle every cause before evaluating a clearly specified package. Exact policy-class equality is not a prerequisite for a future B; relevant capacity differences merely have to be disclosed and the comparator remain credible.

A recast that adds base-station service, changes association physics, gives actors global positions, or replaces velocity control by an allocator loses more decisively: it would change the fixed host/information/action contract. Changing PPO clipping, opening duration or movement magnitude also does not answer this MGTAP question; the accepted B02 grouping and opening rules stay fixed. No alternative in this section is an implementation or execution selection.

## 5. Precise re-entry condition and the observation it would serve

Re-entry is satisfied by **one specified, source-compatible geometry-bound learning comparison**, not by a positive result in advance. It must identify a learned actor operation whose dependence on current, legally observed physical geometry predicts a consequential velocity or credit change relative to a competent generic map, while keeping the full local information, native action/reward, fixed membership, channel/association law, recurrent history and common B02 credit convention intact. Ground here may be ground-user geometry; it need not mean a base station. A new persistent-ID or global-diagnostic input is not an acceptable shortcut.

The deciding observation would be sampled complete native return after actual matched learning, with the whole legal action-to-reward path intact. A geometric alignment score, a worse CUT actor, a larger displacement or a changed rank list is not a substitute. The generic comparator must receive the same original local records and history, preserve unrestricted legal velocity choice, and receive equal optimization and model-selection exposure. The old toy's rate-3 FREE remains relevant to the old toy only; transferring that SGD rate to the native Adam learner would not establish native competence. [E3, “Apply the re-entry boundary”][E3]; [E4, comparator and exposure sections][E4]; [E8, §§2–5][E8].

For this native reward, the natural candidate estimand is the mean paired difference in

\[
J=\frac{1}{256}\sum_{t=0}^{255}\sum_{i=1}^{5}r_{i,t},
\]

using complete sampled episodes, followed by separate reporting of independent training-pair results. An absolute MEI of 0.01 in this J scale has a source-supported prospective rationale: the coverage component of one additionally served user throughout an episode is 0.7/50 = 0.014, before any quality-term change. That is a scale comparison, not a guarantee or measured headroom. It is not the old allocation AUC margin transplanted without a unit change. A later selected object would state whether it adopts this value; no new card or budget is fixed here. [E8, §5][E8].

The relevant future readings are straightforward. A positive complete-return difference at the chosen scale could justify bounded follow-up of that fitted package; an inside-scale outcome would not establish equivalence; an adverse native difference would count against that package even with favorable local diagnostics. A generic fit below hover would limit a claim against competent control without invalidating the observed treatment–generic difference. A damaged reward or primary measurement would limit its dependent claim, not become a scientific negative. One trustworthy comparison can motivate one or two independent follow-up seeds; there is no run-until-all-positive rule. These are re-entry interpretation requirements, not a selected successor's frozen branch map. [E1, §§11.8.2–11.8.7][E1]; [E8, §§5–6][E8].

No trained CUT/inert factorial is required for that performance question. A future binding control could supplement the intact-versus-generic primary, but should preserve the original information and actual entity/record associations. Omitting such a causal panel relinquishes pure metric-specific attribution; it does not prevent reporting package performance. A focused check of the changed actor operation, actor-input boundary and native primary is sufficient verification in principle. No exact controller search, trajectory enumeration, support census or fresh cost experiment is prescribed.

## 6. Work and cost implications, without allocating a study

**New model construction, scientific imports, native calls, optimizer steps, evaluation episodes and result-bearing cost probes in this consultation: zero.** No arms, training masters, runtime cap or execution route are newly allocated.

For scale, the accepted source already supplies a credible direct-learning unit: one fit has 512 complete 256-step training episodes, 131,072 team steps, 256 two-episode rollouts and 1,024 Adam calls, followed by one final-checkpoint evaluation of 32 episodes, or 8,192 steps. Two such learned fits and one shared 32-episode hover reference would be 286,720 team steps and 2,048 Adam calls for one matched training instance. That last total is arithmetic from the source counts, not a measured new comparison. Repeating at two independent masters gives the source's 573,440 steps, 4,096 Adam calls and 192 evaluation episodes. A geometry-by-T/G-by-many-kernels sweep is not needed merely because those dimensions exist; a future question should isolate one host regime and one primary comparison where sufficient. [E8, §§4 and 7][E8]; [E13, `Config`, `run_pair`][E13].

Native work already includes the 5×50 UAV–user channel array, UAV–UAV channels, interference accumulation, sorting up to 250 eligible link entries, local observation ordering and recurrent collection. Each optimizer call reprocesses the 512-row rollout, using the five agent terms and 32-step recurrent chunks. These are algorithm/environment costs, not an added verification panel. The B02 source records 2,621,440 agent-ratio terms per fit; this does not mean a fivefold increase in whole-run cost. There is no existing joint-action or future-trajectory search in this loop. Adding all candidate velocities, all user subsets or repeated counterfactual controllers would create additional work that needs its own scientific purpose, not just a claim that it is bounded. [E8, §7][E8]; [E12, `recurrent_outputs`, `update`][E12]; [E14, channel and connection functions][E14].

The source's applicable per-fit coefficient form is

\[
C_a=C_{\mathrm{init},a}+131072\,c_{\mathrm{env+actor},a}
 +1024\,c_{\mathrm{update},a}+8192\,c_{\mathrm{eval},a}
 +C_{\mathrm{publication},a},
\]

with the existing G accounting also carrying 8,192 hover steps and pair publication. A geometry module would add collection/evaluation and recurrent-update work where it is actually consumed. Its precise missing cost facts are the defined operation and its incremental per-row forward/backward cost on the accepted CPU FP32 path, plus any extra retained state—not an uncomputed oracle or an obligation to launch a profiling experiment. The number of states, affinity entries or attention pairs should be stated once that operation exists. [E13, `run_pair` cost projection][E13].

P24's observed 564.93 seconds for four fits and their evaluations is context, not a guarantee for a new module. The old allocation panel's 36.314234316 seconds, sixty-parameter displacement bounds and float64 SGD timing cannot be assigned to this native learner. Likewise, the UCOPE 1,800-second arm and 3,600-second pair caps are historical/prospective UCOPE limits, not a new MGTAP allocation. Unknown incremental cost is not zero and does not establish that a small new B would be unaffordable. Nothing in this decision changes host, dtype or device for transport convenience. [E9, §5][E9]; [E5, resource section][E5]; [E8, §7][E8].

## 7. Residual uncertainty and effects

The main residual uncertainty is empirical: a carefully specified state-dependent geometric actor may outperform, match or harm a strong same-information generic actor on this task. Source inspection cannot decide that performance ordering. The fixed-five-UAV scope, SINR-based partial observability, nonpersistent ranked slots, capacity-limited association and dynamic interference remain part of any such result's meaning. No tuned native headroom record exists in the listed evidence, and the historical G fits do not establish across-pair competence. These are limitations to carry forward, not additional B admission gates.

**Direction effects.** The stopped balanced-allocation-coordinate family remains parked reversibly. Its positive, null, small and adverse observations and both historical C meanings are preserved. This answer supplies a concrete negative source yield for the naive base/slot/additive-allocation bridge and a narrower native-actor re-entry condition. It does not declare that all possible geometric methods are exhausted, increase a recast count, select another learner object or claim native MGTAP success.

**Portfolio effects.** None. No lifecycle, priority, fusion, registration, cross-direction investment, implementation task, scientific invocation or UAV-validation entry is selected or counted. UCOPE's existing results and separate scientific decisions are not consumed or changed by this consultation.

## 8. Actual evidence access

All fifteen listed scientific paths below were accessed through the connected GitHub connector at **6374063408208ba67b8cb7c69ebc0babb0f00259**. References E1–E15 resolve to that full immutable source commit. Inspection covered the stated sections/functions; this is not a claim to have run source, read unlisted raw arrays, followed embedded links, or validated historical tests. No listed-file access gap was encountered.

| Reference and exact repository path | Inspected material used here |
| --- | --- |
| [E1 — `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`][E1] | Evidence classes, integrity, lifecycle meanings and complete §§11.4, 11.8–11.9. |
| [E2 — `docs/research/candidates/metric_ground_transport_allocation/DIRECTION.md`][E2] | Lines 1–280: latest family boundary, B03/B02 observations and historical structural limits. |
| [E3 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_B03_CONVERGENCE_INTAKE_20260904.md`][E3] | Complete intake; parking, re-entry, evidence and authority separation. |
| [E4 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_B03_STEPSIZE_SCIENCE_CARD_20260904.md`][E4] | Complete card; comparator, information, MEI, exposure and cost. |
| [E5 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_B03_MAIN_RESULT_EVIDENCE_20260904.md`][E5] | Complete result document; all selected signs, rates, counts and resources. |
| [E6 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_B03_MAIN_INTAKE_20260904.md`][E6] | Complete intake; independent reported recomputation and competing interpretations. |
| [E7 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_B1_SCIENCE_CARD.md`][E7] | Lines 1–520 and 900–end: original treatment/comparator, process, decision boundaries and §9 UAV exclusions. |
| [E8 — `docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B02_SCIENCE_CARD_20260908.md`][E8] | Complete card; fixed host, per-agent PPO, native primary, counts and cost limits. |
| [E9 — `docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B01_P24_INTAKE_20260907.md`][E9] | §§1–7 and the retrieved §8 continuation: all-outcome native interpretation and common credit-amendment rationale. |
| [E10 — `experiments/candidates/ucope/uav_motion_prefix_b01/environment.py`][E10] | Complete file; real constructor, feature boundaries, reward accessor and hold state. Synthetic fixture was read as code only, not used as evidence of native behavior. |
| [E11 — `experiments/candidates/ucope/uav_motion_prefix_b01/policy.py`][E11] | Complete file; actor/critic, owned action density, masking and exposure functions. |
| [E12 — `experiments/candidates/ucope/uav_motion_prefix_b01/learner.py`][E12] | Complete file; actual information/reward consumer, recurrent collection and PPO updates. |
| [E13 — `experiments/candidates/ucope/uav_motion_prefix_b01/study.py`][E13] | Complete file; B02 configuration, T/G/H counts, evaluation, cost projection and publication boundaries. |
| [E14 — `envs/pettingzoo/uav_env.py`][E14] | Lines 1–1510: constructor, reset, motion, actor/state observations, channels, interference, greedy association and default reward; rendering tail not needed. |
| [E15 — `envs/pettingzoo/env_adapter.py`][E15] | Lines 1–480: constructor, reset, array/dictionary conversion, native reward/info forwarding and diagnostic-state separation. |

The [fixed task][TASK] was read at its own specified revision, separately from the scientific source commit. The delivery branch was inspected only to preserve its ancestry and existing paths, not as moving scientific evidence.

The explicitly listed [issue #5][ISSUE] body and all eight pre-delivery comments were accessed; the pre-delivery discussion was rechecked during the 2026-09-08 17:34–17:37 UTC review window. Its body concerns VSP-C1 rather than MGTAP. In particular, [the latest native hold-value delivery comment][DISCUSSION] describes a different direction's response; it is not a MGTAP geometry decision or authorization. No linked VSP-C1 file was followed and no cross-direction result was pooled. The other seven visible comments likewise concern VSP-C1 rounds. There was no matching MGTAP native-geometry delivery in that pre-delivery view. The issue's different title is not an access blocker because it is the outlet explicitly designated by this task.

[E1]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[E2]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/docs/research/candidates/metric_ground_transport_allocation/DIRECTION.md
[E3]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/docs/research/candidates/metric_ground_transport_allocation/MGTAP_B03_CONVERGENCE_INTAKE_20260904.md
[E4]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/docs/research/candidates/metric_ground_transport_allocation/MGTAP_B03_STEPSIZE_SCIENCE_CARD_20260904.md
[E5]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/docs/research/candidates/metric_ground_transport_allocation/MGTAP_B03_MAIN_RESULT_EVIDENCE_20260904.md
[E6]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/docs/research/candidates/metric_ground_transport_allocation/MGTAP_B03_MAIN_INTAKE_20260904.md
[E7]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/docs/research/candidates/metric_ground_transport_allocation/MGTAP_B1_SCIENCE_CARD.md
[E8]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B02_SCIENCE_CARD_20260908.md
[E9]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B01_P24_INTAKE_20260907.md
[E10]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/experiments/candidates/ucope/uav_motion_prefix_b01/environment.py
[E11]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/experiments/candidates/ucope/uav_motion_prefix_b01/policy.py
[E12]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/experiments/candidates/ucope/uav_motion_prefix_b01/learner.py
[E13]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/experiments/candidates/ucope/uav_motion_prefix_b01/study.py
[E14]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/envs/pettingzoo/uav_env.py
[E15]: https://github.com/CartmanFatass/My-paper-code/blob/6374063408208ba67b8cb7c69ebc0babb0f00259/envs/pettingzoo/env_adapter.py
[TASK]: https://github.com/CartmanFatass/My-paper-code/blob/2dee7f41fd2ac4c5b27d3186f04a4d7e7f044a24/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260908_native_geometry_convergence/TASK.md
[ISSUE]: https://github.com/CartmanFatass/My-paper-code/issues/5
[DISCUSSION]: https://github.com/CartmanFatass/My-paper-code/issues/5#issuecomment-5588799828
