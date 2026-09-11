Reopen only the named prospective COND/DENSE comparison for later, separately allocated B work. The material change is learned, partner-conditioned relative weighting of visible user records before their compression into a context vector. Unlike the rejected mean-to-sum substitution, that weighting can change which user relations influence the actor when visible UAV geometry changes, without changing the user count, adding information, or weakening DENSE. The supplied operation and native event-to-velocity prediction now meet the previous decision's re-entry condition.

**This is the final narrow-family choice: scientific eligibility for this exact COND/DENSE question, not general reopening of the research programme or permission to run it.** COND remains unimplemented, untested and empirically unaccepted. No card, implementation, test, master, numerical invocation or machine-time allowance is selected or frozen here. P75 remains a complete adverse REL/DENSE observation; its ended allocation, the old balanced-allocation-coordinate family PARK, historical C meanings and all Portfolio state are preserved.

## 1. What changes the decision, and what does not

The preceding Convergence decision rejected a fixed-divisor-to-sum change whose scale could be absorbed by the learned projection, and found the extra count proposal insufficiently specific. Its re-entry condition was a materially changed, source-compatible learned operation with a native event-to-velocity or credit prediction against a valid, equally informed generic comparator. It explicitly did not require a successful pilot, a diagnosis of P75, or proof that the baseline lacked the information. [S2, §§5–8][S2].

The accepted design return now supplies that missing operation. A learned summary of currently visible other-UAV relations determines the relative weights of current user embeddings; the weighted user context then enters the existing recurrent velocity actor. The native hypothesis is that this processing bias can help finite training distinguish user groups whose service consequences differ with partner geometry. It is a hypothesis about learning with the available information, not acquisition of previously unavailable information. [S1, §§3–4][S1].

The next useful observation is therefore the complete sampled native-return difference between freshly fitted COND and intact DENSE under the proposed matched exposure. It can weigh for or against replacing the existing generic package. It need not first establish how often a particular scene occurs or whether attention uniquely explains an eventual difference. The proposed work has two learned arms, one independent training-pair master, one final sampled endpoint, and no auxiliary search or H panel. Its cost and inferential limits are substantial enough to report, but the question does not require a larger design merely to become scientifically eligible. [S1, §6][S1]; [S13, §§5.2, 11.8–11.9][S13].

The strongest support for reopening is this specific computational and decision connection, not the word “attention,” source feasibility alone, or a positive historical signal. The strongest contrary evidence is that the closely related REL package already lost to the same intact generic design after actual learning. The choice is thus deliberately narrow: assess one materially different package, not repeat REL until a favorable seed appears.

## 2. P75 remains adverse, including its inside-MEI second master

The accepted P75 records report complete, technically accepted native fits and evaluation, with no primary errors. Their original result is:

| P75 master | Mean REL | Mean DENSE | Mean H, diagnostic | REL minus DENSE |
| --- | ---: | ---: | ---: | ---: |
| 8201 | 0.147553181120 | 0.192235706284 | 0.147847381964 | −0.04468252516448091 |
| 8202 | 0.165518134487 | 0.168761817933 | 0.141367171777 | −0.003243683445650989 |

The aggregate **−0.02396310430506595** remains `REL_ADVERSE` under the old object's absolute 0.01 scale. Master 8201 has all 32 episode differences adverse. Master 8202 remains inside the MEI with 14 positive and 18 negative differences; it is not a second material loss and does not replace the complete aggregate. All original REL, DENSE and H sampled returns and paired differences remain attached to that result without filtering, pooling into COND, or changed weighting. [S4, §§2–5][S4]; [S5, `aggregate.pairs`, `aggregate.primary`, `per_master`][S5].

The recorded training-pair sample SD is 0.029301685983900646. Combined conditional evaluation SE is 0.0026485358205291165; the individual conditional SEs are 0.003273643145587254 and 0.0041644001399785. These describe different levels of uncertainty. The small conditional evaluation error cannot certify a stable training-population ordering from two fitted pairs. Both branches learned; the preceding response records nonzero REL inner-map and projection movement. Nothing in these observations establishes a source defect or identifies fixed pooling as the unique cause of the loss. [S4, §§3–5][S4]; [S5, `aggregate.primary`][S5]; [S2, §2][S2].

DENSE is a valid same-information native comparator, not a damaged control. Its mean exceeds H in both P75 masters, but H is a fixed diagnostic and not a tuned controller or upper bound. The native tuned same-information headroom record remains absent. Neither that absence nor a demand to certify generic competence holds this prospective question. Conversely, the new comparison cannot claim to beat a tuned baseline merely because it retains the same parameter count and algorithm as P75 DENSE. [S2, §2][S2]; [S4, §§4–5][S4]; [S13, §11.7][S13].

The older allocation B03 evidence also stays separate: its small fixed-rate advantage contracted under equal rate selection, and its trained-toy endpoint headroom was not an estimate of UAV headroom. The historical C structural-nonidentification conclusions and the previously retained positive, within-scale and adverse UCOPE outcomes are neither rescued nor reversed by this eligibility decision. They are not additional COND training replicates. [S2, §9][S2]; [S3, historical family-boundary sections][S3].

## 3. The exact eligible computation

### Legal inputs and masks

Both arms keep the entire original 108-component actor input and each UAV's recurrent history. The current encoder extracts twenty user triples from `x[3:63]` and ten other-UAV quadruples from `x[63:103]`. These contain relative coordinates and normalized SINR, not persistent identities. Own position, time, last command and hold state remain in the full raw path. No global connection data, critic state, diagnostic indices, base-station metadata, extra feature or entity memory enters either actor. [S7, `RelationResidualEncoder.forward`, `DenseResidualEncoder.forward`][S7]; [S9, `actor_features`, `critic_features`, `local_indices`][S9].

Retain precisely the design's masks, `mU_j = [u_j[2] > 0]` and `mV_k = [v_k[3] > 0]`. The environment selects SINR-eligible records and packs their SINR as `clip((SINR+10)/50,0,1)`; the specified 3 dB eligibility threshold makes selected rows positive in that field, including a row with zero relative offset. Padding has a zero field. These masks are internal computations from legally supplied information, not a new observation channel or a use of `local_indices`. Counts nU and nV mean visible, truncated records, not total demand, served users, partner assignments or an enduring roster. There are at most twenty visible user rows and, with five UAVs and self excluded, four actual other UAVs in ten slots. [S1, §3][S1]; [S12, observation packing and `_local_user_entries`/`_local_uav_entries`][S12].

### COND

Keep all trainable blocks at their existing shapes: U is 20×3, V is 21×4, P is 64×41, all bias-free; the full raw affine path has W of shape 64×108 and b of length 64. For each current record, let

\[
e^U_j=\tanh(Uu_j),\qquad e^V_k=\tanh(Vv_k).
\]

The query is the first twenty components of the mean visible UAV embedding:

\[
q=\begin{cases}
\displaystyle\frac{1}{n_V}\sum_k m^V_k e^V_{k,0:20},&n_V>0,\\
0_{20},&n_V=0.
\end{cases}
\]

For visible users, retain the score and masked softmax

\[
s_j=\frac{(e^U_j)^\top q}{\sqrt{20}},\qquad
\alpha_j=\frac{\exp(s_j)}{\sum_{\ell:m^U_\ell=1}\exp(s_\ell)}.
\]

The contexts are exactly

\[
c_U=\begin{cases}
\displaystyle\frac{n_U}{20}\sum_{j:m^U_j=1}\alpha_j e^U_j,&n_U>0,\\
0_{20},&n_U=0,
\end{cases}
\qquad
c_V=\frac{1}{10}\sum_k m^V_k e^V_k.
\]

The pre-activation encoder is `W x + b + P concat(cU,cV)`. The existing wrapper applies tanh once, then GRU(64,64), then the unchanged three-coordinate Gaussian mean head and learned log standard deviations. All twenty-one UAV embedding components still enter cV; taking twenty for the query does not discard the last component from the existing branch. No query state is stored across steps. [S1, §3][S1]; [S7, `NativeGeometryActor.forward`][S7].

Empty user input produces zero user context without evaluating an empty softmax. With no visible other UAV, q is zero, the user weights are uniform, and the nU/20 factor recovers the old fixed-slot user mean. With one visible user, there is no relative user selection to change. These are local identities of the defined computation at matched parameters, not assertions that separately trained COND and REL policies must agree in those situations. Cancellation in a nonempty UAV query or equal user scores can also leave the weighting uniform. Their frequency and practical importance are unmeasured. [S1, §§3–4][S1].

### Intact DENSE and parameter matching

DENSE remains

\[
\operatorname{encoder}_{DENSE}(x)=W'x+b'+Q\tanh(Dx+d),
\]

with D of shape 16×108, d of length 16 and bias-free Q of shape 64×16. It retains the full raw affine path, nonlinear processing of every original component and the same recurrent consumer. It already can use other-UAV geometry, user geometry and occupancy. No restricted input, weakened decoder, fixed-hover primary comparator or reduced recurrent history is eligible under this decision. [S7, `DenseResidualEncoder`, `NativeGeometryActor`][S7].

COND adds no learned parameters to the existing REL blocks. The inherited counts remain **2,768 branch parameters, 9,744 encoder parameters and 69,079 complete learner parameters per arm**. All downstream actor and separate critic components remain matched. These are the recorded counts supported by the unchanged block shapes, not a new model-counting execution. Equal count does not establish equal effective capacity, function class, useful computation or optimization geometry. [S1, §3][S1]; [S6, “Treatment and comparator”][S6].

Preserve the common/private initialization law: common raw encoder, GRU, velocity head, log standard deviations and critic copied from one fresh template; private fan-in initialization for the row or hidden maps; zero output projections P and Q. Both initial policies therefore reduce to the same base actor. Inner-branch learning through the policy loss occurs after the projection begins moving. That connection is specified, but actual COND movement and useful learning remain future observations. [S7, `NativeGeometryActor.__init__`, `build_pair`, `geometry_exposure`][S7].

## 4. Why this meets re-entry without establishing a mechanism result

For two visible user records, the proposed softmax implies

\[
\log\frac{\alpha_j}{\alpha_\ell}
=\frac{(e^U_j-e^U_\ell)^\top q}{\sqrt{20}}.
\]

This is a deduction from the supplied computation, not a numerical diagnostic. At fixed user rows and visible counts, changing the UAV-derived query can change the relative weighting. A constant change from division by twenty to a sum cannot reproduce that varying ratio merely by rescaling the old projection. The change is **conditioning before user aggregation**, not count-only amplification. The old full REL actor and DENSE already have nonlinear raw-input and recurrent routes through which partner geometry can affect velocity; the deduction concerns the proposed pooled branch, not a theorem that the complete baseline lacks conditional behavior. [S1, §3][S1]; [S2, §§5 and 8][S2].

The prediction concerns a UAV seeing user groups on different bearings while an observed other UAV moves toward one group's bearing. The new branch could help learning emphasize a different observed group and change primitive velocity in a way that improves joint service. It does not hard-code repulsion or know which group is actually served. Current rows do not directly reveal a partner's intended next action, assignments or unseen users. The query itself summarizes the current observation; any use of temporal evidence still depends on the unchanged recurrent actor, with no stable row-identity memory promised. [S1, §4][S1]; [S16, §§2–3][S16].

The consequential path remains:

**Own and partner motion → current local radio/geometry records and own history → UAV-conditioned relative user emphasis → primitive velocity density → clipped motion and changed distance-dependent channels/interference/SINR → capacity-limited greedy association → original primitive team reward → common PPO advantage and later learned embeddings/velocities.**

The fixed host has five UAVs and fifty ground users, a 1000 m square, 50–150 m altitude, 256 one-second steps and component velocity scaling of 30 m/s. It keeps free-space/vectorized channels, no FDMA or shadowing, at most one UAV per user and at most ten users per UAV. The action remains velocity, not a connection matrix. The reward remains 0.7 times the connected-user fraction plus 0.3 times mean connected-link SINR quality. Each agent receives one fifth of the team reward, and `team_reward` sums the original entries for learning and reporting. No base-station reward consumer or geometric surrogate is introduced. [S9, `make_real`, `team_reward`][S9]; [S12, `step`, `_greedy_connection_assignment`, `_compute_reward`][S12].

Both packages remain primitive G with sampled velocities, no duration head or renewal, ordinary critic and unchanged team PPO. With each UAV's three-coordinate log density denoted by ell_i, the likelihood ratio is `r_i = exp(ell_i,new − ell_i,old)`. The clipped surrogate is summed over agents before the primitive-row mean, without an additional division by five or per-coordinate clipping. Gamma-one returns include all primitive rewards, advantages are detached and standardized once per two-episode rollout, and four full-rollout optimizer epochs use the existing recurrent chunks. This is not a new counterfactual or individual causal-credit method. [S10, `joint_terms`][S10]; [S11, `collect_episode`, `recurrent_outputs`, `update`, `clipped_policy_loss`][S11].

The foundations matter to this judgment in three concrete ways. Partial observation plus a GRU does not certify sufficient state, so the query is not treated as partner intent. Shared return and a centralized critic do not establish correct individual causal credit, so no credit-identification claim is made. Representability is distinct from finite learning, so DENSE's access to the same information does not make a processing comparison meaningless, while COND's explicit structure does not demonstrate an advantage. [S16, §§2–4 and 6][S16]; [S17, comparison and mechanism sections][S17].

## 5. The strongest contradiction and the zero-work alternative

**Retaining PARK is the serious runner-up.** It requires no new scientific exposure, preserves a complete adverse observation, and avoids spending on an untested interaction that might merely add optimization difficulty. P75 did not localize its loss to independent typed pooling. COND keeps a mean UAV query that can erase distinctions, and its learned dot products do not have an intrinsic “less contested” interpretation. It may favor an already attractive user group, overlook a crucial record, or induce several shared-policy UAVs to choose the same alternative. DENSE can learn the useful response as well or better. [S4, §§4–5][S4]; [S1, §§3–4 and 7][S1].

The nonuniform-weighting opportunity also disappears when no other UAV or only one user is visible, and it can be weak even with multiple records. No event frequency, useful-attention trace or tuned headroom is established. A low-confidence inside-MEI prediction in the design return is not positive evidence and is not converted into a favorable prior result. [S1, §§3, 6–7][S1].

Nevertheless, PARK loses for this exact eligibility question because the new proposal supplies more than another easy scale adjustment: it specifies what is conditioned on what, where that interaction occurs before compression, its empty/sparse behavior, a plausible native velocity consequence, and a full-information generic comparison that could disconfirm its usefulness. The single-pair primary asks directly whether that package earns a useful realized native difference. No additional structural axis or search needs to be opened to obtain that observation. This is a sufficient reason to make the named question eligible, not a rule that every implementable architecture should be tried.

The previous PARK was appropriate to the adverse REL result and the insufficient sum/count proposal it assessed. Its re-entry condition is now met by a materially different hypothesis, not waived because the family has been idle. P75 remains contrary evidence and an ended object. No unchanged repeat, general architecture sweep or alternative recast is selected. The uncertainty about the benefit is exactly why the claim remains exploratory rather than a prediction of successful re-entry. [S2, §§6–8][S2]; [S13, §§11.8.2 and 11.9][S13].

## 6. Adequacy and limits of the proposed one-pair B

The accepted proposal is adequate as a minimal **B/EXPLORE scouting comparison**, with its exact master still unassigned. It uses one fresh COND fit and one fresh DENSE fit, separate arm optimizers and on-policy histories, the existing common initialization/reset and private RNG-domain convention, and no old checkpoint reuse. Pairing source randomness does not mean trajectories remain identical after policies differ. Neither agents nor episodes are independent training replicates. [S1, §6][S1]; [S7, `build_pair`][S7]; [S17, “随机性有层级”][S17].

The proposed exposure retains the following recorded scale, not a new allocation:

| Quantity | Per learned fit | One COND/DENSE pair |
| --- | ---: | ---: |
| Training episodes, each 256 steps | 512 | 1,024 |
| Native training team steps | 131,072 | 262,144 |
| Two-episode rollouts | 256 | 512 |
| Adam calls, four per rollout | 1,024 | 2,048 |
| Final sampled evaluation episodes | 32 | 64 |
| Native final evaluation steps | 8,192 | 16,384 |
| Total native team steps | 139,264 | **278,528** |

There is one final checkpoint per arm, not an intermediate or selected endpoint; no rate, width, seed or checkpoint search. Optional H is omitted, relinquishing a contemporaneous hover comparison. Historical H is not reused as though evaluated against the new fitted policies. The primary does not need H to compare two valid learned packages, but its absence prevents new hover-relative competence wording. [S1, §6][S1]; [S2, §7][S2].

Keep CPU FP32/thread1 and the inherited primitive learner settings: Adam 3e-4, betas 0.9/0.999, epsilon 1e-8, no weight decay or scheduler; value coefficient 0.5, entropy coefficient 0.01, global gradient clip 0.5; ordinary unnormalized critic, no GAE or terminal bootstrap; 32-step truncated recurrent gradients from collected chunk-start states. Optional duration, renewal, mean-action and value-normalization paths in the shared source are not part of this question. [S6, “Fixed mode, learner and exposure”][S6]; [S8, `run_pair`][S8]; [S10–S11, sampled policy and update consumers][S11].

For the complete paired final episodes, retain

\[
J_{a,e}=\frac{1}{256}\sum_{t=0}^{255}\sum_{i=1}^{5}r_{a,i,t},\qquad
 d_e=J_{COND,e}-J_{DENSE,e},\qquad
\Delta=\frac{1}{32}\sum_{e=0}^{31}d_e.
\]

Report every own-arm return and difference, the mean and the conditional evaluation SE, using the existing paired-difference sample SD divided by the square root of the episode count. Reporting retains the source's original native-reward accumulation; training keeps its FP32 representation. One matched training pair cannot estimate training-seed population uncertainty. More episode resampling cannot repair that limitation. P75 is historical motivation, not extra observations in this estimand. [S1, §6][S1]; [S8, `_primary`][S8]; [S11, `collect_episode`][S11]; [S17, randomness and comparison sections][S17].

The proposed absolute **MEI 0.01 in native time-average team reward** has a host-specific rationale: one additionally connected user throughout an episode contributes 0.014 through the coverage term before changes in quality. It is not a guaranteed attainable improvement, tuned headroom, or the old allocation AUC quantity. I retain this proposed scale and the following interpretation, without freezing a new card. [S1, §6][S1]; [S12, `_compute_reward`][S12].

| Complete future observation | Bounded interpretation and subsequent choice |
| --- | --- |
| Delta > 0.01 | Realized COND-package advantage at this exposure. Consider separately selected, bounded independent repeatability work if the observation and complete cost warrant it; no automatic successor. |
| −0.01 ≤ Delta ≤ 0.01 | No demonstrated gain above the chosen scale. Preserve the actual sign, retain DENSE as the available generic choice, and end that proposed allocation without inferring equivalence. |
| Delta < −0.01 | Adverse evidence for this exact COND package. Recommend against unchanged continuation based on favorable attention or motion appearances; no broad geometry impossibility follows. |
| Primary incomplete or damaged | No paired performance polarity. Preserve independently trustworthy own-arm facts and the exact dependent gap; no automatic retry or replacement master. |

A later single-pair result would not identify attention, geometry, occupancy, parameter sharing or credit as the unique cause, and would not establish COND's superiority to old REL fits. Omitting an attention/binding intervention relinquishes those stronger causal claims; omitting H relinquishes the contemporaneous reference; neither omission invalidates the narrowly stated sampled COND-minus-DENSE primary. No event census, causal panel, exact upper or baseline-qualification study is added as a prerequisite. [S13, §§11.8.1–11.8.7][S13].

## 7. Dominant work, unknown costs and executable readiness

Zero further work has zero new training and evaluation exposure. The proposed alternative has two full learned fits and the counts above. Five actor histories, native radio/association work and four optimizer passes are intrinsic multiplicative costs, not administrative checks. The existing record gives **3,317,760 logical actor-row evaluations per fit** across collection, final evaluation and PPO reprocessing. COND's masks, query formation, twenty-dimensional scores, softmax and weighted reduction act on those rows, including the backward path during PPO, not merely during final evaluation. [S1, §6][S1]; [S2, §7][S2]; [S11, recurrent and update consumers][S11].

The old row maps and projection remain. The new computation uses a single pooled UAV query and a vector of user scores. It requires no user-by-UAV pair table, joint-action enumeration, future-trajectory branching, best-of-many controller, solver or width search. Those absences constrain the design's work; they do not make its remaining operations free or prove a runtime advantage. [S1, §§3 and 6][S1].

The known complete per-arm law remains

\[
C_a=C_{init,a}+131072\,c_{env+actor,a}+1024\,c_{update,a}
+8192\,c_{eval,a}+C_{publication,a}.
\]

The changed forward/backward coefficients, activation memory, candidate wall/CPU use and complete support costs are unmeasured. Added acceptance, staging, monitoring and collection effort remain separate and unknown. Shared initialization and pair publication must be accounted for once rather than hidden by an average; actual command accounting includes the necessary initialization, admission, learning, final evaluation and closed-file readout. No fresh profiling or timing probe is required or allocated here. [S1, §6][S1]; [S13, §11.9][S13].

P75's pair-command walls were 353.71 and 368.12 seconds, with 0.81 seconds for aggregation: 722.64 seconds in that native-plus-aggregate process window. Its 899.395664691925-second critical path also includes observation, collection and inter-invocation gaps. These are neither aggregate CPU work nor isolated DENSE measurements. They provide historical context, not a COND forecast or release of the old 1,800/3,600-second limits. No new machine-time cap is assigned. [S5, timing fields][S5]; [S4, §6][S4].

There is also an explicit implementation boundary. Current `geometry.py` contains REL and DENSE, not COND. Its exact row slices and recurrent insertion support the proposed replacement computation. Current `runner.py` binds REL/DENSE/H, masters 8201/8202 and a two-master aggregate; changing an output label cannot make it a one-pair COND study. Later separately allocated work would need its own correct operation and dependent comparison/readout while preserving the historical command and evidence. This is an identified readiness gap, not an instruction to implement it now. [S7, actor kinds and `build_pair`][S7]; [S8, `run_pair`, `_primary`, `aggregate`][S8].

The eventual ordinary acceptance need concerns the changed pooling behavior, input/parameter preservation, loss connection and dependent primary publication. Zero-initialized projections, empty masked inputs and the unchanged single tanh placement are relevant local checks; they do not require native event diagnostics or an exact support study. No new framework or Engineering Scope §4 machinery is needed. The present consultation permits none of those checks or implementations to be executed. [S14, §§4–5 and 7.1][S14]; [S13, §§11.4, 11.8.6–11.9][S13].

## 8. Family effects, Portfolio effects and remaining uncertainty

**Family effects.** Only the exact source/design return §§3–4 COND/DENSE question becomes scientifically eligible for later separately allocated B work at the assessed one-pair primary-only scale. This is not an open-ended native actor search and does not resume P75, authorize an unchanged REL repeat, or alter the prior result. The old balanced-allocation-coordinate family remains PARKed; historical C conclusions and recast count remain unchanged. No card is frozen and no master, implementation or invocation is selected.

**Direction lifecycle and Portfolio effects.** None. The broad direction remains ACTIVE/MEDIUM, with capacity, priority, investment, fusion, formal UAV-entry and other Portfolio records unchanged. The original-node decision does not create a new blanket delegation or an additional approval layer. The source-return author's recommendation is evidence considered here, not the authority for this final choice. [S3, current scientific boundaries][S3]; [S15, §§1–4][S15].

The unresolved scientific questions are whether relevant partner-conditioned opportunities occur often enough to matter under the original sampled task, whether the learned summary uses them beneficially, whether DENSE learns the behavior better, and whether any realized margin repeats across training. None has been answered by this source review. The absence of those answers is not converted into a mandatory preliminary measurement. The explicit one-pair native comparison is eligible to obtain the first package-level observation, while its benefit, complete runtime and support cost remain unknown.

Actual new numerical exposure in this consultation is zero: no scientific imports, model construction, checkpoint load, environment, simulation, test, training, evaluation, replay, diagnostic or cost probe was performed. The historical zero-exposure statement in the design return describes its authoring boundary; this consultation's scoped response publication is a separate administrative action. Retrieval and publication effort are not claimed free.

## 9. Actual access and fixed-source references

All eighteen listed paths were accessed through the connected GitHub connector at their own specified versions. S1, S3 and S7–S17 were read at `e4666a5c1aecc9a4d84cad4c724970e5392cfc25`; S4–S6 at `d9723c7bdd91d44a97cc34365891c42b2a41772e`; S2 at its immutable delivery commit `251bffbc4bb58cce3f10f8622a1a615fd8e48acb`; and S18 at `55ff973fc8b6cb4947b263a7f4581dbaa15e626d`. The task itself was read at `da4bb56d3a7e45fbafe490853ec2a069ce0057f2`. No moving branch was used as scientific evidence, and no listed critical or explanatory source was inaccessible.

| Fixed source | Material actually read and used |
| --- | --- |
| [S1 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_CONDITIONAL_POOLING_SOURCE_DESIGN_RETURN_20260910.md`][S1] | §§2–7, with earlier completion/exposure context: exact operation, event, comparator, counts, interpretation and readiness limits. |
| [S2 — `docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260909_post_b01_convergence/archive/RESPONSE.md`][S2] | Opening decision and §§1–9: prior PARK, scaling distinction, re-entry condition, work and historical counterevidence. |
| [S3 — `docs/research/candidates/metric_ground_transport_allocation/DIRECTION.md`][S3] | Opening P75, post-B01, native re-entry and coordinate-family boundaries through line 215. |
| [S4 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_P75_INTAKE_20260909.md`][S4] | Complete intake: accepted outcomes, comparator, exposure, costs and ended object. |
| [S5 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_P75_TECHNICAL_RESULT.json`][S5] | Complete file, including both masters' REL/DENSE/H arrays, all paired differences, aggregate, counts and timings. No recomputation or raw checkpoint inspection. |
| [S6 — `docs/research/candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_SCIENCE_CARD_20260908.md`][S6] | Native boundary, original actor formulas, learner, exposure, primary, MEI and cost/check sections through line 230. |
| [S7 — `experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/geometry.py`][S7] | Complete file: old encoders, wrapper, initialization and exposure. |
| [S8 — `experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/runner.py`][S8] | Lines 1–460, including old arm/master binding, `_primary`, `run_pair` and `aggregate`. |
| [S9 — `experiments/candidates/ucope/uav_motion_prefix_b01/environment.py`][S9] | `make_real`, actor/critic feature construction, reward accessor, diagnostic separation and hold state. |
| [S10 — `experiments/candidates/ucope/uav_motion_prefix_b01/policy.py`][S10] | Actor/critic, initialization, sampling and `joint_terms`; optional paths distinguished from the proposed primitive mode. |
| [S11 — `experiments/candidates/ucope/uav_motion_prefix_b01/learner.py`][S11] | Collection, native reward, recurrent reprocessing, likelihood reduction and update consumer. |
| [S12 — `envs/pettingzoo/uav_env.py`][S12] | Observation/SINR packing and eligibility, interference, greedy association and default reward at lines 290–462, 565–610, 900–1000 and 1421–1490. |
| [S13 — `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`][S13] | Adopted §§3–5.2, 11.4 and 11.7–11.10. Other objects' exceptions do not apply to COND. |
| [S14 — `docs/project/ENGINEERING_SCOPE_SPEC.md`][S14] | Adopted §§4–5 and 7.1; no machinery, implementation or testing commissioned. |
| [S15 — `AGENTS.md`][S15] | Adopted decision-tier/finality/delegation sections 1–4 and shared-branch publication section 6. |
| [S16 — `docs/rl-marl-foundations-20260907/FOUNDATIONS.md`][S16] | §§2–4 and 6: information/history, joint credit, finite learning and evidence limits, applied in §§4 and 6 above. |
| [S17 — `docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md`][S17] | Comparison units, randomness hierarchy, package versus mechanism, and return/cost interpretation. |
| [S18 — `docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260910_conditional_pooling_reentry/ISSUE_SNAPSHOT.json`][S18] | Recorded observation time and the three MGTAP historical delivery comments; unrelated VSP-C1 material is not scientific evidence here. |

The live [issue #5][ISSUE] body and its thirteen pre-delivery comments were accessed, with discussion rechecked around **19:12 PDT on September 10, 2026** (02:12 UTC on September 11). The snapshot separately records **2026-09-11T01:50:06.1012925Z**; that is the author's earlier observation, not this review's timestamp. The three MGTAP comments locate the [native audit][H1], [REL/DENSE re-entry][H2] and [post-P75 PARK][H3]. None is a delivery for this conditional-pooling round. The mixed issue's other-direction content supplies no MGTAP scientific authority. No unlisted linked file or literature source was followed; the design return's literature findings were read as secondary context, not independently verified papers or evidence of COND efficacy. Delivery-branch HEAD and target checks served only scoped publication and did not change the scientific evidence pins.

[S1]: https://github.com/CartmanFatass/My-paper-code/blob/e4666a5c1aecc9a4d84cad4c724970e5392cfc25/docs/research/candidates/metric_ground_transport_allocation/MGTAP_CONDITIONAL_POOLING_SOURCE_DESIGN_RETURN_20260910.md
[S2]: https://github.com/CartmanFatass/My-paper-code/blob/251bffbc4bb58cce3f10f8622a1a615fd8e48acb/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260909_post_b01_convergence/archive/RESPONSE.md
[S3]: https://github.com/CartmanFatass/My-paper-code/blob/e4666a5c1aecc9a4d84cad4c724970e5392cfc25/docs/research/candidates/metric_ground_transport_allocation/DIRECTION.md
[S4]: https://github.com/CartmanFatass/My-paper-code/blob/d9723c7bdd91d44a97cc34365891c42b2a41772e/docs/research/candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_P75_INTAKE_20260909.md
[S5]: https://github.com/CartmanFatass/My-paper-code/blob/d9723c7bdd91d44a97cc34365891c42b2a41772e/docs/research/candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_P75_TECHNICAL_RESULT.json
[S6]: https://github.com/CartmanFatass/My-paper-code/blob/d9723c7bdd91d44a97cc34365891c42b2a41772e/docs/research/candidates/metric_ground_transport_allocation/MGTAP_NATIVE_GROUND_GEOMETRY_B01_SCIENCE_CARD_20260908.md
[S7]: https://github.com/CartmanFatass/My-paper-code/blob/e4666a5c1aecc9a4d84cad4c724970e5392cfc25/experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/geometry.py
[S8]: https://github.com/CartmanFatass/My-paper-code/blob/e4666a5c1aecc9a4d84cad4c724970e5392cfc25/experiments/candidates/metric_ground_transport_allocation/mgtap_native_ground_geometry_b01/runner.py
[S9]: https://github.com/CartmanFatass/My-paper-code/blob/e4666a5c1aecc9a4d84cad4c724970e5392cfc25/experiments/candidates/ucope/uav_motion_prefix_b01/environment.py
[S10]: https://github.com/CartmanFatass/My-paper-code/blob/e4666a5c1aecc9a4d84cad4c724970e5392cfc25/experiments/candidates/ucope/uav_motion_prefix_b01/policy.py
[S11]: https://github.com/CartmanFatass/My-paper-code/blob/e4666a5c1aecc9a4d84cad4c724970e5392cfc25/experiments/candidates/ucope/uav_motion_prefix_b01/learner.py
[S12]: https://github.com/CartmanFatass/My-paper-code/blob/e4666a5c1aecc9a4d84cad4c724970e5392cfc25/envs/pettingzoo/uav_env.py
[S13]: https://github.com/CartmanFatass/My-paper-code/blob/e4666a5c1aecc9a4d84cad4c724970e5392cfc25/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[S14]: https://github.com/CartmanFatass/My-paper-code/blob/e4666a5c1aecc9a4d84cad4c724970e5392cfc25/docs/project/ENGINEERING_SCOPE_SPEC.md
[S15]: https://github.com/CartmanFatass/My-paper-code/blob/e4666a5c1aecc9a4d84cad4c724970e5392cfc25/AGENTS.md
[S16]: https://github.com/CartmanFatass/My-paper-code/blob/e4666a5c1aecc9a4d84cad4c724970e5392cfc25/docs/rl-marl-foundations-20260907/FOUNDATIONS.md
[S17]: https://github.com/CartmanFatass/My-paper-code/blob/e4666a5c1aecc9a4d84cad4c724970e5392cfc25/docs/rl-marl-foundations-20260907/topic-notes/04_EMPIRICAL.md
[S18]: https://github.com/CartmanFatass/My-paper-code/blob/55ff973fc8b6cb4947b263a7f4581dbaa15e626d/docs/research/candidates/metric_ground_transport_allocation/pro_packets/20260910_conditional_pooling_reentry/ISSUE_SNAPSHOT.json
[ISSUE]: https://github.com/CartmanFatass/My-paper-code/issues/5
[H1]: https://github.com/CartmanFatass/My-paper-code/issues/5#issuecomment-5589322235
[H2]: https://github.com/CartmanFatass/My-paper-code/issues/5#issuecomment-5596561607
[H3]: https://github.com/CartmanFatass/My-paper-code/issues/5#issuecomment-5599484438
