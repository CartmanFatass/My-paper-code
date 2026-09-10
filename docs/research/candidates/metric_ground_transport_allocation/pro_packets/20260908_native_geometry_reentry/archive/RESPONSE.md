Continue with one bounded native comparison of a typed relation-residual actor against an equally informed, parameter-matched dense residual actor. The new candidate supplies the learned operation missing from the preceding consultation: nonlinear responses to each current geometry/SINR record share parameters across ranks within its type, are pooled, and actually enter the recurrent velocity policy. The full ordered raw-input path remains available to both actors. This is a testable processing bias, not an information acquisition, assignment-action or base-station intervention.

**The final direction decision is CONTINUE_B_NATIVE_GROUND_GEOMETRY.** The decision is formed for the single scientific comparison defined below, using primitive G mode in both arms and the common B02 per-agent PPO convention. It does not reopen the stopped balanced-allocation-coordinate family or either historical C object. It selects no implementation task, code change, invocation, compute allocation, UAV-validation entry or Portfolio action.

## 1. Smallest conclusion and decision value

The question is whether this specified allocation of actor parameters to typed local relations improves complete sampled native return relative to the same parameter budget spent on unstructured dense processing. The source supports the information-to-action and action-to-reward connections needed to ask that question. It does not establish the answer. The appropriate ceiling is **B/EXPLORE package performance on the fixed five-UAV, fifty-user native task**, with no claim of pure metric causality, optimal transport, stable superiority, equivalence, ground-base value, variable-fleet transfer, churn, warehouse/UAV delivery/sensing/relay efficacy, convergence, safety or general MARL performance.

The preceding native intake explicitly left open a local geometry-sharing actor once its operation, consumer and competent generic comparison were specified. That condition is met here at the level of a concrete performance experiment, not by asserting that geometry is absent from the baseline. The relevant MARL structure is partial observability and other-agent non-stationarity: each UAV has a restricted local view, while five co-adapting policies jointly change interference and service. Fixed team size and unchanged temporal control are conditions of this object, not varying axes. [E2, “Native geometry Convergence boundary”][E2]; [E3, “Re-entry and claim ceiling”][E3]; [E7, §§2–3][E7].

The dominant prospective work is two learned actors at two independent training-pair masters, the existing 512 complete training episodes per fit, four PPO epochs per rollout, and one final sampled evaluation. There is no geometry-by-duration factorial, kernel sweep, all-subset computation, candidate-velocity search or future-trajectory search. One pair would be a cheaper scouting observation; two are the proposed scale because the listed native evidence exhibits substantial between-fit sign changes. Neither two seeds nor a positive result is a universal B admission condition. The numerical design below defines expected scientific exposure, not permission to consume it. [E1, §§5.2, 11.8.2–11.8.3 and 11.9][E1].

## 2. Source observations and the native causal path

### Environment, ownership and information

The real constructor fixes five UAVs, fifty uniformly placed ground users, a 1000 m square, altitude limits 50–150 m, 256 one-second steps, component velocity scale 30 m/s, free-space/vectorized channels, no shadowing, no FDMA and the default reward. Native steps move UAVs; ground users are sampled at reset. Each actor owns its UAV's velocity and recurrent history. It does not choose the connection matrix or own a persistent local slot. [E9, `make_real`, `HoldState`][E9]; [E13, `reset`, `_generate_user_positions`, `step`][E13].

The actor's original 108 inputs are the 104 base components plus three last sent velocities and remaining hold divided by four. The base components are own normalized position, twenty user triples `(relative dx, relative dy, normalized SINR)`, ten other-UAV quadruples `(relative dx, relative dy, relative dz, normalized SINR)`, and time. Records are SINR-eligible, sorted by descending SINR, truncated to the slot limits and zero-padded. With five members, at most four of the ten other-UAV slots can contain actual other UAVs. The trailing field in each relation is SINR, not distance, regardless of the older dimensionality comment. [E9, `actor_features`][E9]; [E13, observation constructors and `_local_user_entries`/`_local_uav_entries`][E13].

Horizontal offsets use the 1000 m scale; other-UAV vertical offsets use the 100 m height range. This proposal retains those supplied components and does not pretend that their unweighted norm is a physical Euclidean distance. Current record geometry is meaningful without persistent IDs. A change in SINR rank does not preserve entity identity at that slot. The proposed sharing attaches to each current typed record, not to a lasting rank token.

The separate critic receives all normalized UAV/user positions and time, plus prior command/hold entries: 136 components in total. It is assembled before current decisions. Diagnostic local indices, `entity_positions`, global connection/SINR arrays and ground-base metadata do not enter either actor. The default base at `[500,500,30]` is not an accepted default service/backhaul reward anchor and is not added to the comparison. This is ground-user geometry, not ground-base binding. [E9, `critic_features`, `local_indices`][E9]; [E11, `collect_episode`][E11]; [E13, `_get_state`, `step`, default channel/reward functions][E13]; [E14, `reset`, `step`, `get_current_state`][E14].

### Legal velocity, association and native reward

Both actors retain the three-dimensional tanh-Gaussian velocity distribution. The environment multiplies the normalized command by 30, advances one second and clips position to the stated horizontal and altitude bounds. Distinct commands need not produce distinct physical displacements at a boundary. No geometric attraction rule or projection replaces this legal action path. [E10, `sample`, `tanh_log_prob`][E10]; [E13, `step`][E13].

**The task's phrase “one-user-per-UAV association” needs a source-grounded correction.** The actual rule allows at most one UAV per user and up to ten users per UAV. `max_connections=10`, the per-UAV count and the user-connected flag establish this; the preceding native intake already recorded the correction. This answer preserves the actual source, not a one-quantum-per-UAV surrogate. [E3, “Formed decision and bounded reading”][E3]; [E13, `__init__`, `_greedy_connection_assignment`][E13].

Motion changes three-dimensional link distances, path loss, interference, SINR eligibility and the descending-SINR greedy association. The default reward is

\[
R_t=0.7\,C_t/50+0.3\,Q_t,\qquad
Q_t=\frac{\sum_{(i,j)\in\mathcal C_t}\operatorname{clip}((\mathrm{SINR}_{ij}-3)/30,0,1)}{\max(C_t,1)},
\]

where \(\mathcal C_t\) is the connected set and \(C_t\) its size. This quality normalization differs from the actor observation's clipped `(SINR+10)/50`. Each UAV receives `R_t/5`; the accepted learner recovers the native team reward by summing the original `info['rewards_dict']`. It does not train on the adapter's additional averaged scalar. [E13, `_compute_path_loss_matrix`, `_compute_uav_user_sinr_matrix`, `_update_channel_state_vectorized`, `_compute_reward`][E13]; [E14, `step`][E14]; [E9, `team_reward`][E9].

Thus the source-supported route is **reset geometry and previous joint motion → each UAV's current typed local records and own history → its learned velocity distribution → native motion, interference and association → primitive team service reward → common team-advantage PPO credit → later learned velocities**. Shared row parameters change a particular learner consumer in that route. They do not bypass the coupled physics by assuming that a shorter own link necessarily improves team reward.

## 3. One treatment and one parameter-matched generic comparator

The following is a proposed mathematical definition, not an assertion that these encoders already exist in the repository. All dimensions and counts in this section are design arithmetic; no model was instantiated to obtain them.

Let \(x\in\mathbb R^{108}\) be the unchanged actor input. Let \(u_j\in\mathbb R^3\), \(j=1,\ldots,20\), and \(v_k\in\mathbb R^4\), \(k=1,\ldots,10\), be the existing user and other-UAV rows extracted from that input, including its original padding. Both encoders return 64 features to the unchanged GRU(64,64), velocity mean head and three learned log standard deviations. Both retain a full affine raw-input path \(Wx+b\), with \(W\in\mathbb R^{64\times108}\).

### Treatment: REL, typed nonlinear pooling plus full raw residual

Define

\[
c_U(x)=\frac1{20}\sum_{j=1}^{20}\tanh(Uu_j),\quad U\in\mathbb R^{20\times3},
\]
\[
c_V(x)=\frac1{10}\sum_{k=1}^{10}\tanh(Vv_k),\quad V\in\mathbb R^{21\times4},
\]
\[
z_{\mathrm{REL}}(x)=\tanh\!\left(Wx+b+P[c_U(x);c_V(x)]\right),\quad P\in\mathbb R^{64\times41}.
\]

The two row maps and the fusion projection have **no biases**; only the common raw affine path supplies its 64 biases. Every supplied row is processed. Fixed denominators are 20 and 10, never the number of currently nonzero rows. Bias-free tanh maps make a zero-padded row contribute zero without constructing an availability mask, inferring an ID or consulting diagnostics. No row is removed from the raw path. The two type widths are fixed design choices, not selected from outcomes.

This is one-step pooling of actor-relative relations. It has no pairwise attention matrix, user-user graph, entity-memory matching, nearest-user search or geometric solver. The nonlinear transformation occurs **before** pooling; merely pooling affine row maps would lose much of the intended distinction from simple aggregate coordinate processing.

### Comparator: DENSE, unstructured nonlinear processing plus the same raw residual

Define

\[
z_{\mathrm{DENSE}}(x)=\tanh\!\left(W'x+b'+Q\tanh(Dx+d)\right),
\]

with \(D\in\mathbb R^{16\times108}\), \(d\in\mathbb R^{16}\), and \(Q\in\mathbb R^{64\times16}\), with no output bias on \(Q\). This comparator sees every original component in both its raw path and its additional generic dense path. It is not a masked, geometry-blind, fixed-hover or reduced-action comparator. Both packages preserve the original dense G actor as a representable special case by setting the additional output projection to zero. No smaller information set or removal of rank information is used to make REL look favorable.

| Parameter block | REL | DENSE |
| --- | ---: | ---: |
| Full 108→64 raw affine path | 6,976 | 6,976 |
| Typed row maps / generic hidden affine | 3×20 + 4×21 = 144 | (108+1)×16 = 1,744 |
| Context projection to 64 | 41×64 = 2,624 | 16×64 = 1,024 |
| Additional branch subtotal | **2,768** | **2,768** |
| Complete encoder subtotal | **9,744** | **9,744** |

The unchanged GRU, velocity head, log standard deviations and separate critic have matching dimensions and parameter counts. Relative to the source's 66,311-parameter complete G learner, each proposed learner has **69,079 parameters**. These are parameter-count matches, not a theorem of equal hypothesis classes, equal statistical capacity, equal useful computation or identical training trajectories. There are no extra output-disconnected parameters added solely for counting. The inherited constant hold input in primitive G is present in both packages. [E7, §9, original G parameter count][E7]; [E10, `Actor`, `Critic`][E10].

For paired initialization, copy the same original raw encoder, GRU, velocity head, log standard deviations and critic into both packages. Initialize \(P\) and \(Q\) to zero, so the initial policies equal the same original G policy, rather than giving either arm an initial behavior advantage. Initialize \(U,V,D\) from nondegenerate, zero-mean fan-in-scaled uniform distributions, with each weight's bounds \(\pm1/\sqrt{\mathrm{fan\_in}}\); initialize \(d=0\). Use a private initialization stream separate from action sampling. All parameters remain trainable. At initialization, inner-branch gradients may be zero until the output projection moves; that is a consequence of the common residual initialization, not a claim that every parameter must move on the first update.

The comparator is credible and unweakened by construction, but **its empirical competence is not certified by a parameter count**. The listed native results contain G fits below hover and no tuned native headroom record. The resulting primary can establish only performance relative to the actually fitted DENSE package; stronger wording about a competent tuned controller must be supported by the observed baseline evidence. No separate competence-only experiment or global tuning certificate is a prerequisite to this B comparison.

## 4. Why this is consequential binding, and what it does not identify

REL binds together a current row's relative geometry and SINR in one learned response, and uses a distinct shared map for ground-user versus other-UAV relations. A learning update arising at one user rank changes the same map used at other user ranks and future times. The resulting pooled context enters the recurrent state, velocity mean and action-density gradient. DENSE instead allocates its equally numerous branch parameters to unrestricted combinations of the whole ordered observation. This is a concrete difference in learned processing, not a renamed coordinate or extra scalar distance.

For the pooled branch, moving a complete row within its type does not change the mathematical sum. The full actor is **not** claimed to be permutation-invariant: the raw residual intentionally retains the original ordered slots, and the environment's eligibility/truncation still matters. A swap of only coordinate fields while keeping SINR attached to another user would corrupt the source record and is not the proposed intervention. Anonymous current rows are sufficient for this operation; persistent IDs are neither assumed nor added.

The differentiating prediction is that sharing nonlinear responses to similarly situated current relations can use finite training exposure more effectively than learning their contribution separately through an unstructured dense encoder. That is a plausible hypothesis, not an observed improvement. Own altitude, position, time and last command can still affect how the context is used through the full residual and recurrent consumer. Neither relation pooling nor the raw path reconstructs unobserved users or the exact interference field.

**The strongest live alternative** is that any apparent benefit is generic typed sharing, occupancy/SINR processing or regularization, rather than a specifically spatial advantage. The dense residual may already learn the useful function; pooling may dilute rare but decisive records, discard useful rank distinctions in its branch, or encourage a harmful response to locally attractive links under coupled interference. REL may also learn to ignore its context. Equal Adam settings do not eliminate architecture-dependent optimization effects.

The primary comparison therefore tests the whole proposed representation package. There is no trained CUT/inert factorial in this object. Omitting it relinquishes pure metric-specific attribution, not the right to report a trustworthy native performance difference. A worse CUT model or a local gradient statistic would not replace REL versus DENSE. Requiring exhaustive causal localization or an exact policy-class equivalence proof before this performance experiment would exceed the current evidence burden. [E1, §§11.8.1, 11.8.4–11.8.6 and 11.9][E1]; [E4, re-entry and competent-FREE discussion][E4].

## 5. Fixed primitive mode and common learning exposure

**Both arms use primitive G mode:** no duration head, no learned opening hold and no renewal. Each of the five actors observes, advances its recurrent history and chooses a fresh legal velocity at each primitive step. Repeating a command and hovering remain legal. Last sent velocity stays in the input; remaining hold is zero at decision time in this mode. No third learned arm is used to test duration.

Use B02's `agent_compound` ratio grouping, entropy coefficient **0.01**, and the ordinary critic without value normalization. At this input revision the listed source also contains optional renewal, conditioned-duration, entropy-zero and value-moment paths. Their presence does not change this object's definition: `renewal=False`, no duration head and no value moments. The existing T/G runner is evidence for the host and workload, not an already implemented REL/DENSE comparison or a command to execute it. [E7, §§2–3][E7]; [E9, `HoldState`][E9]; [E10, `joint_terms`][E10]; [E11, `collect_episode`, `update`][E11]; [E12, `Config`, `run_pair`][E12].

For each active agent, sum the three velocity-coordinate log densities before exponentiating its old/new ratio. Clip that agent ratio to [0.8,1.2], multiply by the unchanged scalar team advantage, sum the five agent terms, then average primitive rows. There is no additional division by five and no per-coordinate clipping. Retain the source's entropy calculation and action-density conventions rather than substituting a new action objective.

Return-to-go includes every primitive native reward, with gamma one and no GAE or terminal bootstrap. Normalize detached advantages once per two-episode, 512-step rollout. Preserve 32-step truncated recurrent gradients using collected chunk initial states, four full-rollout epochs and one joint actor/critic Adam call per epoch. Both arms use learning rate 3e-4, betas 0.9/0.999, epsilon 1e-8, no weight decay or scheduler, value coefficient 0.5 and global gradient clipping 0.5. These common settings are not the geometry treatment. [E7, §3][E7]; [E11, `returns_to_go`, `clipped_policy_loss`, `recurrent_outputs`, `optimizer_for`, `update`][E11].

### Independent units, matching and expected counts

The proposed scientific comparison uses two fresh paired masters, **8201 and 8202**, one REL fit and one DENSE fit per master. These values differ from the masters named in the inspected study source; no repository-wide uniqueness or reservation is claimed. With \(b=100000s\), use the source's domain layout: original common initialization at \(b+11\), private branch initialization at \(b+12\), separate per-arm training velocity generators initialized at \(b+21\), training resets \(b+1000+e\), evaluation resets \(b+2000+e\), and private per-arm evaluation velocity generators at \(b+3000+e\). There is no duration draw. Initial common parameters and reset inputs are paired; trajectories, optimizer states and recurrent histories remain separate and on-policy. Independent masters, not agents or episodes, are the training replicates. [E7, §4][E7]; [E10, `templates`, `generator`][E10]; [E12, seed domains and collection loops][E12].

Use one fixed architecture/configuration per arm, no rate or width sweep, and no selection of the better seed or checkpoint. Both prospective pairs belong to the comparison irrespective of the first sign; this does not allocate a retry, replacement seed or extra run. The exposure is:

| Work unit | Per learned fit | Two masters, four learned fits |
| --- | ---: | ---: |
| Complete training episodes, 256 steps each | 512 | 2,048 |
| Native training team steps | 131,072 | 524,288 |
| Two-episode rollouts | 256 | 1,024 |
| Actual Adam calls, four per rollout | 1,024 | 4,096 |
| Final sampled learned-policy evaluation episodes | 32 | 128 |
| Learned-policy evaluation team steps | 8,192 | 32,768 |

Retain the existing fixed-zero-velocity H reference on the same 32 evaluation resets per master: 64 additional episodes and 16,384 team steps overall, with no learner or tuning. H is a diagnostic reference, **not a second primary comparator**. Thus the whole expected comparison comprises 2,240 complete episodes, 192 final evaluation episodes and **573,440 team steps**. There are no intermediate checkpoint evaluations. Existing on-policy training episode/rollout records provide the learning history without pretending that they are repeated final-policy measurements. These totals follow from the listed source's counts and the proposed two-arm design; they are not observations of a new execution. [E7, §§4 and 7][E7]; [E12, `run_pair`][E12].

In primitive G, each learned fit has 655,360 training agent velocity decisions/recurrent observations and 40,960 final-evaluation agent decisions, with zero duration decisions. PPO reprocessing is additional optimizer exposure, not additional native environment interaction. Future ordinary exposure reporting should distinguish encoder, recurrent and critic movement; zero-initialized projections use absolute displacement rather than a ratio to zero. The old sixty-parameter SGD path bounds cannot be transferred to Adam or used to predict motion of the new branch.

## 6. Native estimand, MEI and branch-to-action readings

For every complete sampled episode use the original native rewards:

\[
J_{a,s,e}=\frac1{256}\sum_{t=0}^{255}\sum_{i=1}^{5}r_{i,t},\qquad
\Delta_s=\frac1{32}\sum_{e=0}^{31}(J_{\mathrm{REL},s,e}-J_{\mathrm{DENSE},s,e}),\qquad
\Delta=\frac{\Delta_{8201}+\Delta_{8202}}2.
\]

Use the source's float/float64 accumulation for reporting, while preserving the learner's FP32 reward representation. Sample the final policies; do not replace sampling by a greedy mean policy or reuse historical T/G endpoints as new observations. Report all REL/DENSE/H episode values, both pair means, adverse episodes and training records. Conditional evaluation SE for each pair is the sample SD of its 32 paired differences divided by \(\sqrt{32}\); combine those SEs as \(\sqrt{SE_1^2+SE_2^2}/2\). Report training-pair sample SD separately. Two fitted pairs give little information about training-population uncertainty; evaluation episodes, recurrent chunks and bootstrap resamples cannot manufacture more independent fits. [E7, §§4–5][E7]; [E12, `difference_stats`, `primary_from_rows`, `aggregate`][E12].

For this proposed comparison adopt **absolute MEI 0.01 in complete time-average native team reward**. The native scale rationale is that one additionally connected user throughout an episode contributes 0.7/50 = 0.014 through coverage before any quality-term change. This is a useful scale for deciding whether the added relation operation merits further study, not a service guarantee or measured recoverable headroom. It is not the old allocation AUC margin treated as the same estimand. [E7, §5][E7].

| Prospective reading | Scientific interpretation and subsequent recommendation |
| --- | --- |
| \(\Delta>0.01\) | Preliminary advantage of the REL fitted package at this task and exposure. Retain both seed results and baseline qualifications; recommend a bounded independent follow-up appropriate to the uncertainty, not automatic C promotion or pure-geometry attribution. |
| \(-0.01\le\Delta\le0.01\) | No aggregate gain at the proposed scale under this exposure. Not equivalence. Inspect the already retained seed differences and baseline performance to decide whether this particular sharing operation merits a specifically justified change; no automatic expansion of unchanged seeds. |
| \(\Delta<-0.01\) | Adverse native evidence for this REL package, favoring DENSE in this comparison. Recommend against carrying this unchanged module forward solely on a favorable local statistic; do not close all geometry-aware learning. |

Opposite per-seed effects remain explicit even when the aggregate is inside the MEI. A DENSE fit below H limits claims against demonstrated competent generic control but does not erase a trustworthy REL-minus-DENSE observation. H is neither an upper bound nor a tuned generic policy. Missing or corrupted primary measurements limit their dependent performance inference; an engineering failure is not a scientific negative, and independently trustworthy narrower facts remain reportable. These readings create no new approval or launch layer. [E1, §§11.8.2–11.8.7][E1].

## 7. Contrary evidence, options and why parking now loses

The historical allocation evidence remains a warning against favorable comparisons to poorly chosen generic settings. B03's fresh low-rate AUC advantage was +0.008410135905, but symmetric four-rate selection left +0.000655478018, including one negative seed, while FREE's own gain was +0.200872633192. Both winners were at rate 3.0, the grid edge, selected and compared on three exploratory seeds. Its 0.040598777488 oracle-minus-FREE endpoint gap is neither the AUC estimand nor transferable UAV headroom. B02/B03 remain valid bounded observations; both old C objects remain terminal structural nonidentifications. [E2, accepted B03/B02 sections][E2]; [E4, “Bounded scientific reading”][E4]; [E5, comparison definition][E5]; [E6, “Direct measurements and ordered rule”][E6].

The new input revision also contains adverse B02 native evidence that cannot be omitted:

| Native historical pair | T−G | G−H | T−H |
| --- | ---: | ---: | ---: |
| P24, 6901 | +0.0433518665 | −0.0282038164 | +0.0151480500 |
| P24, 6902 | −0.0503654225 | +0.0171009380 | −0.0332644846 |
| B02/P47, 7001 | −0.0472671044 | +0.0247787961 | −0.0224883084 |
| B02/P47, 7002 | −0.0061362058 | −0.0182559817 | −0.0243921875 |

P24's two-pair mean was −0.0035067780, WITHIN, while the earlier four-pair outcome-informed description was +0.0058553213 and P21 retained its original UP reading. At this pin, B02/P47's primary is **−0.026701655118179134, DOWN**; both T−G and both T−H signs are negative. G−H changes sign. The larger opening displacement in harmful fits did not compensate for complete native losses. These are different historical fitted packages, not new REL/DENSE data and not a causal verdict against per-agent clipping. The ended P47 execution route is not resumed here. [E8, §§2–5][E8]; [E7, §10][E7].

**The strongest contradiction to continuing** is therefore both structural and empirical: relation pooling may suppress decisive local structure under interference, and the available native learner has produced unstable or weak generic performance. Equal parameter counts and a plausible processing bias cannot promise that either fitted actor will use its information well. More broadly, a benefit could be SINR/occupancy sharing rather than spatial binding. These limits constrain the eventual wording, not the admissibility of an explicit B performance comparison.

**Runner-up: retain parking until a stronger mechanism or comparator result exists.** That was justified when the proposal was an old rank-map/base-distance transfer without a native actor operation. It loses now because the request supplies the operation and this answer closes its consumer, full-information residual, parameter match, primitive mode and native primary. Requiring a positive precursor, exact metric theorem, globally tuned headroom or unique causal explanation at this point would defer the direct observation that can decide the question. The empirical specification allows a specifically justified changed B package after adverse evidence. [E1, §§11.3, 11.8 and 11.9][E1]; [E3, re-entry condition][E3].

A recast adding ground-base reward, global actor positions, new association actions, renewal or a synthetic allocation law is not selected. It changes more than the supplied question requires. The proposed typed processing comparison is the narrow re-entry, with the original balanced allocator remaining parked and no assertion that its old equal-class metric mechanism has transferred intact.

## 8. Work, unknown cost and proportionate verification

The native environment still computes the 5×50 UAV–user link field, UAV–UAV geometry, interference and a greedy ordering over up to 250 link entries. These are existing environment costs, not policy search. Each optimizer call processes 512 primitive rows with five agent terms and the unchanged recurrent chunks. [E11, `recurrent_outputs`, `update`][E11]; [E13, vectorized channel and association functions][E13].

The proposed branches add different computation despite identical parameter counts. Per logical actor-input row, REL uses twenty 3→20 maps, ten 4→21 maps and a 41→64 projection: **4,664 matrix-weight products**, excluding biases, pooling, activations and the common raw/recurrent work. DENSE uses 108→16→64: **2,752 matrix-weight products**. REL also evaluates 610 inner tanh components per actor row, versus 16 for DENSE. These are arithmetic work descriptions, not measured FLOPs or elapsed-time ratios. Typed batching does not make their cost zero.

A learned fit has \(5(131072+8192)+1024\times512\times5=3,317,760\) logical actor-row evaluations across collection, final evaluation and optimizer reprocessing. REL applies thirty typed row maps at each such row. There is no all-pair relation graph, joint-action \(a^5\) enumeration, trajectory branching, best-of-many rollout or repeated counterfactual controller. A future implementation may batch the stated work but must not change the scientific comparison to justify a speed claim.

The applicable source-derived per-arm law remains

\[
C_a=C_{\mathrm{init},a}+131072\,c_{\mathrm{env+actor},a}
+1024\,c_{\mathrm{update},a}+8192\,c_{\mathrm{eval},a}
+C_{\mathrm{publication},a}.
\]

A single shared H reference adds 8,192 environment steps per master, charged once with the pair's publication rather than counted as a learned fit. The new coefficients must include branch forward work during collection/evaluation and forward/backward work during each PPO epoch. Their incremental elapsed time, activation memory and total RSS are **unmeasured**. Parameter equality supplies neither those coefficients nor an affordability certificate. No cost probe, warm-up, profiler, exact solver or fresh calibration experiment is requested by this consultation. [E12, `run_pair` cost projection][E12]; [E1, §11.9][E1].

The available native timing context is 564.93 seconds for P24 and 577.94 seconds for B02/P47, each across four learned fits and their associated measurements. The latter also retained nonzero real parameter displacement and its historical 80.578-second synthetic smoke against a 60-second engineering bound. These source-reported facts are not timing guarantees for REL/DENSE or reasons to reproduce the old breach. The old allocation panel's 36.314234316 seconds and float64 SGD movement/cost law do not apply here. No new wall-time cap, device allocation or execution route is chosen; the scientific numerical path remains the specified CPU FP32 learner. [E7, §§9–10][E7]; [E8, §5][E8]; [E6, resource section][E6].

For an eventual implementation, retain the original reward, information, action-density and primary-output checks and add one focused check of the changed encoder path. Ordinary parameter counting and automatic differentiation can establish that the stated trainable branch is connected to the velocity loss; the check must account for its deliberately zero initial output projection. Fixed-count pooling, row grouping and zero padding are directly inspectable without a native diagnostic experiment. No exact support census, all-history replay, cross-platform bit test or all-positive-seeds gate is added. Optional local-index tracing and trained binding ablations are not part of the proposed performance work; their omission relinquishes identity-specific and pure causal claims, not complete native-return measurement. [E1, §§11.4, 11.8.5–11.8.7][E1].

## 9. Residual uncertainty and authority effects

No native result for REL or DENSE exists in the inspected evidence or was generated here. The effect sign, magnitude, repeatability, empirical generic competence, tuned headroom and incremental runtime remain unknown. The proposed pair equalizes information, declared parameter budget and training/selection exposure, but not hypothesis classes or processing cost. Its result would concern a typed nonlinear representation package under fixed-five-UAV partial observability and dynamic association/interference, not metric-specific causation or deployment performance.

**Direction effects.** This answer forms a source-backed native-actor re-entry question, with exactly one REL/DENSE comparison. The balanced-allocation-coordinate family stays parked, and its positive, inside-MEI, adverse and historical C evidence is preserved. The preceding native parking decision remains correct for the underspecified bridge it evaluated; the new explicit operation is the material change. No recast count is changed and no existing scientific source/state is edited.

**Portfolio effects.** None. No lifecycle, priority, fusion, registration, investment, implementation assignment, scientific invocation or UAV-validation entry is selected or counted. The prospective dimensions and exposures above specify the scientific question only. Actual model construction, scientific imports, tests, training, evaluation, simulation and result-bearing cost work performed in this consultation are all zero.

## 10. Actual source access

All fourteen listed scientific paths were read through the connected GitHub connector at **d726acf63f8db47bd2e93e43cac8bbd27529d8ad**. Inline references below resolve to that immutable evidence revision. The task was read separately at its specified task commit. No moving delivery-branch content was substituted for scientific evidence, no embedded unlisted file link was followed, and no source code or historical test was executed.

| Reference and exact repository path | Material actually inspected and used |
| --- | --- |
| [E1 — `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`][E1] | Complete specification, including §§11.4, 11.8 and 11.9, via segmented reads. |
| [E2 — `docs/research/candidates/metric_ground_transport_allocation/DIRECTION.md`][E2] | Lines 1–220: latest native boundary, B03/B02 observations and historical interpretation limits. |
| [E3 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GEOMETRY_CONVERGENCE_INTAKE_20260908.md`][E3] | Complete preceding native intake and its precise re-entry condition. |
| [E4 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_B03_CONVERGENCE_INTAKE_20260904.md`][E4] | Complete prior family decision, comparator requirement and preserved C meanings. |
| [E5 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_B03_STEPSIZE_SCIENCE_CARD_20260904.md`][E5] | Complete historical comparison, exposure, MEI and cost definition. |
| [E6 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_B03_MAIN_RESULT_EVIDENCE_20260904.md`][E6] | Complete result document, all selected signs and resource observations. |
| [E7 — `docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B02_SCIENCE_CARD_20260908.md`][E7] | Complete current card, including §10's P47 adverse completion, not just its prospective definition. |
| [E8 — `docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B01_P24_INTAKE_20260907.md`][E8] | Lines 1–230: §§1–6 and the beginning of §7; native outcomes, diagnostics, limitations and costs. |
| [E9 — `experiments/candidates/ucope/uav_motion_prefix_b01/environment.py`][E9] | Complete file: real constructor, feature/reward boundaries, hold state; synthetic fixture not used as native evidence. |
| [E10 — `experiments/candidates/ucope/uav_motion_prefix_b01/policy.py`][E10] | Complete file: actor/critic, optional heads, sampling, densities and exposure. |
| [E11 — `experiments/candidates/ucope/uav_motion_prefix_b01/learner.py`][E11] | Complete file: collection, source options, team reward, recurrent consumer and PPO updates. |
| [E12 — `experiments/candidates/ucope/uav_motion_prefix_b01/study.py`][E12] | Complete file via segmented reads: configuration, seeds, counts, cost law and publication. |
| [E13 — `envs/pettingzoo/uav_env.py`][E13] | Lines 1–620, 755–1030 and 1390–1510: native setup, motion, observations, vectorized geometry/interference/association and reward. |
| [E14 — `envs/pettingzoo/env_adapter.py`][E14] | Lines 1–480: array conversion, reset/step, reward forwarding and diagnostic separation. |

The explicitly listed [issue #5][ISSUE] body and its nine visible pre-delivery comments were accessed. The discussion was rechecked around **22:50 PDT on September 8, 2026**. Its body and most comments concern VSP-C1, not this scientific question. The existing [MGTAP native-geometry comment][PREVIOUS] links the preceding parking response, not this re-entry round. It was preserved rather than treated as a matching delivery. No listed scientific path or required discussion was inaccessible. Discussion timestamps and delivery state are mutable observations, not commit-pinned experimental evidence.

[E1]: https://github.com/CartmanFatass/My-paper-code/blob/d726acf63f8db47bd2e93e43cac8bbd27529d8ad/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[E2]: https://github.com/CartmanFatass/My-paper-code/blob/d726acf63f8db47bd2e93e43cac8bbd27529d8ad/docs/research/candidates/metric_ground_transport_allocation/DIRECTION.md
[E3]: https://github.com/CartmanFatass/My-paper-code/blob/d726acf63f8db47bd2e93e43cac8bbd27529d8ad/docs/research/candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GEOMETRY_CONVERGENCE_INTAKE_20260908.md
[E4]: https://github.com/CartmanFatass/My-paper-code/blob/d726acf63f8db47bd2e93e43cac8bbd27529d8ad/docs/research/candidates/metric_ground_transport_allocation/MGTAP_B03_CONVERGENCE_INTAKE_20260904.md
[E5]: https://github.com/CartmanFatass/My-paper-code/blob/d726acf63f8db47bd2e93e43cac8bbd27529d8ad/docs/research/candidates/metric_ground_transport_allocation/MGTAP_B03_STEPSIZE_SCIENCE_CARD_20260904.md
[E6]: https://github.com/CartmanFatass/My-paper-code/blob/d726acf63f8db47bd2e93e43cac8bbd27529d8ad/docs/research/candidates/metric_ground_transport_allocation/MGTAP_B03_MAIN_RESULT_EVIDENCE_20260904.md
[E7]: https://github.com/CartmanFatass/My-paper-code/blob/d726acf63f8db47bd2e93e43cac8bbd27529d8ad/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B02_SCIENCE_CARD_20260908.md
[E8]: https://github.com/CartmanFatass/My-paper-code/blob/d726acf63f8db47bd2e93e43cac8bbd27529d8ad/docs/research/candidates/ucope/UCOPE_UAV_MOTION_PREFIX_B01_P24_INTAKE_20260907.md
[E9]: https://github.com/CartmanFatass/My-paper-code/blob/d726acf63f8db47bd2e93e43cac8bbd27529d8ad/experiments/candidates/ucope/uav_motion_prefix_b01/environment.py
[E10]: https://github.com/CartmanFatass/My-paper-code/blob/d726acf63f8db47bd2e93e43cac8bbd27529d8ad/experiments/candidates/ucope/uav_motion_prefix_b01/policy.py
[E11]: https://github.com/CartmanFatass/My-paper-code/blob/d726acf63f8db47bd2e93e43cac8bbd27529d8ad/experiments/candidates/ucope/uav_motion_prefix_b01/learner.py
[E12]: https://github.com/CartmanFatass/My-paper-code/blob/d726acf63f8db47bd2e93e43cac8bbd27529d8ad/experiments/candidates/ucope/uav_motion_prefix_b01/study.py
[E13]: https://github.com/CartmanFatass/My-paper-code/blob/d726acf63f8db47bd2e93e43cac8bbd27529d8ad/envs/pettingzoo/uav_env.py
[E14]: https://github.com/CartmanFatass/My-paper-code/blob/d726acf63f8db47bd2e93e43cac8bbd27529d8ad/envs/pettingzoo/env_adapter.py
[ISSUE]: https://github.com/CartmanFatass/My-paper-code/issues/5
[PREVIOUS]: https://github.com/CartmanFatass/My-paper-code/issues/5#issuecomment-5589322235
