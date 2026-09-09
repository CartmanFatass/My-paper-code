**Select the single native-cost B proposed in P68. It meets the existing re-entry condition because it specifies a genuinely different action-credit intervention, gives that intervention to the containing RAW comparator as well as both residual arms, and requires a net native-value improvement that also clears the historical RAW reference. This is a narrowly justified learning comparison, not evidence that residual alignment will succeed.**

The selected scope is one new, development-informed, fresh-from-genesis joint seed-0 package, three representations, and the two fixed 33/258-update readouts. The present decision supports re-entry for that comparison only. It neither selects an unchanged repeat nor opens an automatic seed, objective, or budget ladder. It does not freeze the implementation card, allocate compute, launch a run, or change Portfolio state.

Two interpretation corrections are necessary without changing the proposed experiment: historical RAW is competent at LONG, not at both endpoints; and improvement that fails the alignment contrasts is not, by itself, proof of a generic-preprocessing mechanism. A cost-accounting clarification is also necessary: the recorded B04 resource wall time precedes publication. These corrections are detailed below. No specification exception is needed.

## Why this now meets re-entry

The executed park was conditional on a missing scientific discriminator, not on a requirement to produce a positive result before further learning. Its re-entry condition called for a particular legal-action or credit intervention, native accounting including offsetting losses, a containing RAW null, an alignment control, and attainable value at the original 0.0025 margin. It expressly allowed comparator repair inside an experiment and a transparently different seed scope. P68 now supplies those elements. This follows the prior [Convergence intake, “Precise re-entry and limits”][intake] and the archived [response, “NEXT_DISCRIMINATOR_OR_REENTRY”][prior].

The unresolved question is whether the aligned representation becomes useful when learning credit is tied directly to the cost of legal decisions, rather than to fitting action-value scores. P68 is not another attempt to obtain the sixth correct REPLAN action through an unspecified learner modification. It fixes the objective, the information set, the representations, the updates, and the native-return contrast together. Both a favorable alignment result and a competent-RAW negative would change the assessment of this particular surviving explanation. That is sufficient decision value for one adaptive B, even though failure to clear the original margin is the more plausible forecast.

The strongest support is source-level and design-level, not empirical residual superiority. The B04 `train_path` minimizes legal-action squared error; B07 `centered_loss` subtracts separate legal means and then retains the pooled legal-element squared loss. P68 instead minimizes the probability-weighted native loss of legal actions with equal row weighting. Its comparison exposes the simplest competing explanation—ordinary objective improvement—by giving exactly the same new loss to RAW and DERANGED. [B04 source, `train_path`][b04code]; [B07 source, `centered_loss` and `train_path`][b07code]; [assessment, §§2–4][assessment].

Retaining PARK is the close runner-up. TRUE must overcome substantial observed native losses, RAW can benefit equally from the new objective, and the proposed seed and panel have already informed development. Those are substantial reasons for low expectations and a narrow investment, but they do not make this specified contrast non-discriminating. The DM’s recommendation is advice, not evidence; I select the comparison because its measurements distinguish the relevant alternatives, not because the DM recommends it. The controlling [evidence specification, §§5.2, 11.8.1–11.8.3 and 11.9][spec] permits a specifically justified change after an adverse observation and does not require positive replication or a complete causal explanation first.

## Preserve the contrary evidence

B04 remains the one competent-comparator residual negative. Its historical values are:

| Endpoint | RAW native regret | TRUE native regret | RAW minus TRUE |
| --- | ---: | ---: | ---: |
| SHORT, update 33 | 0.006581880989529963 | 0.018114012084314506 | −0.011532131094784542 |
| LONG, update 258 | 0.0037814300857039115 | 0.010915533713999911 | −0.007134103628296 |

Both adverse differences exceed 0.0025 in magnitude. Historical RAW-LONG has six exact actions on each eight-row side, with side regrets 0.003754710220270765 and 0.0038081499511370583. The direct result labels that endpoint competent. Historical RAW-SHORT is explicitly not competent. A SHORT comparison can retain the inherited LONG-competence interpretation qualifier, but must be described as a short-budget result on a trajectory competent at LONG—not as superiority to a competent SHORT checkpoint. This corrects the shorthand “competent RAW endpoints” without inventing a new SHORT-competence requirement. [B04 result, `representations.RAW`, `representations.TRUE_RESIDUAL`, `contrasts` and `result_branch`][b04result].

The strongest contradiction to expecting this new experiment to succeed is the size of TRUE’s B04 deficit against that competent LONG comparator. There was also no generic-preprocessing advantage over RAW in B04. The counterweight to a broad failure inference is genuine learning: TRUE’s own SHORT-to-LONG regret improves by 0.007198478370314595. That does not rescue its comparison, but it prevents treating the representation as unable to learn. [Direction, “Residual complete-cycle endpoints B04”][direction].

B05 seeds 1 and 2 remain comparator-limited, not two additional competent residual negatives. Their later RAW side-mean regrets pass while REPLAN exact counts remain 5/8. B06 seed 2’s KEEP correction contributes 0.0009278881578830053 native gain; B07 seed 1 changes two REPLAN decisions with only 0.0000016144314865518261 net gain, and seed 2 changes no action. Exact-count competence is not a total ordering of native value. Neither the competence rule nor the two MEIs is relaxed to fit these observations. [Direction, “Joint-seed B05 result,” “RAW exposure B06,” “RAW centered loss B07” and “Balanced-family Convergence disposition”][direction]; [Convergence intake, “Bounded scientific reading”][intake].

P68 supplies no new outcome. Its arithmetic record explicitly reports zero new scientific invocations, environment/model/native/evaluator calls, and optimizer updates. The source reads and calculations motivate selection; they do not increase the empirical sample. [Arithmetic, `new_exposure` and `calculation_method`][arithmetic].

## The selected intervention and its actual claim

Retain P68’s masked expected-native-cost objective. For TRAIN row i, legal action set A_i, existing native labels y_i(a), and model outputs z_i(a), use

$$
p_i(a)=\frac{\exp z_i(a)}{\sum_{b\in A_i}\exp z_i(b)},\qquad
c_i(a)=\frac{\max_{b\in A_i}y_i(b)-y_i(a)}{0.01},\qquad
L=\frac{1}{B}\sum_i\sum_{a\in A_i}p_i(a)c_i(a).
$$

Illegal actions have zero probability. Use the specified stable legal softmax, fixed temperature 1, equal row weights, constant labels, and no gradient through the label maximum. Do not add entropy, an MSE auxiliary objective, a mixture, tuned temperatures, label clipping, or a sweep. The 0.01 normalization comes from the selected population’s existing minimum material advantage; it scales training credit and does not change native reward or the evaluation MEI. The outputs are logits, not calibrated G16 predictions. [Assessment, §3][assessment]; [B01 card, §§5–7][b01].

For one row, differentiating the stated objective gives

$$
\frac{\partial L_i}{\partial z_i(a)}
=p_i(a)\left(c_i(a)-\sum_{b\in A_i}p_i(b)c_i(b)\right).
$$

This is an algebraic implication of the proposed loss, not a result for the learner. It gives direct credit according to relative native cost: cheap and expensive wrong replacements need not receive the same update. Centered MSE instead fits centered score gaps. Equal row weighting also deliberately differs from the old pooled legal-element weighting. Thus the selected objective package is not a renamed pairwise version of B07, but a positive result would not isolate cost weighting, removal of regression, row weighting, gradient scale, clipping, or Adam as its unique cause. No additional factorization experiment is required for this bounded package comparison. [B07 source, `centered_loss`][b07code]; [assessment, §§2–3][assessment].

The training expectation is over softmax actions; the reported native endpoint remains the deterministic legal argmax. Lower softmax training cost does not guarantee a better greedy EVAL action. Saturation, parameter sharing, TRAIN-to-EVAL differences, and new KEEP errors can defeat the intended effect. Consequently, logit movement, softmax probability, or training-loss reduction alone is not the requested result. The existing evaluator’s `select_printed_action` and `native_regret` provide the relevant action and consequence, preserving first-printed ties and the legal maximum-minus-selected G16 calculation. [Evaluator, `select_printed_action` and `native_regret`][evaluator].

The source-grounded trace remains: exogenous event and physical history determine the current option-owning agent slot’s history; the gate receives the shared 42-vector history and one 52-vector packet; native-cost supervision changes the legal KEEP/replacement ordering over the declared updates; the selected replacement is charged once and measured over the common 16-step four-agent future. The label branches supply training targets and evaluation consequences, not additional future information to the actor at action selection. Fixed membership, partner policies, K8, elapsed horizon 4, cost 4, and the existing source labels remain unchanged. [B01 card, §3][b01]; [assessment, §3][assessment].

RAW retains target, predictor mean, and Cholesky coordinates containing the inputs to TRUE’s deterministic transform. DERANGED retains the residual packet multiset but breaks its row alignment independently within the existing TRAIN and EVAL cells. All three receive the same objective, architecture, shared preparation, canonical example order, initialization law, Adam settings, batch size, clipping, and numerical boundary. No EVAL row enters training, predictor fitting, calibration, or new checkpoint selection. [B01 card, §5][b01]; [B04 source, `prepare`, `packet_sets` and `train_path`][b04code].

This is a finite-budget supervised native-action gate comparison in the existing four-agent host. It is not a new on-policy return experiment, a joint asynchronous-credit algorithm, an information-gain mechanism, or a function-class claim. The literature discussed in the assessment motivates action-gap-sensitive credit; I rely on the DM’s documented retrieval, not an independent paper or local-library audit here. The exact softmax-cost adaptation is a DM design inference, not a theorem imported from classification-based policy iteration or a novelty finding. [Assessment, §2][assessment].

## Native accounting and the comparator protection

At each fixed endpoint b, let R_R(b), R_T(b), and R_D(b) be the new RAW, TRUE, and DERANGED equal-side native regrets, and let R_H(b) be historical B04 RAW. Report separately

$$
\Delta_R(b)=R_R(b)-R_T(b),\quad
\Delta_D(b)=R_D(b)-R_T(b),\quad
\Delta_H(b)=R_H(b)-R_T(b).
$$

With eight rows per side, equal-side regret is the sixteen-row mean. Therefore, for every reference X separately,

$$
R_X(b)-R_T(b)=\frac{1}{16}\sum_{i=1}^{16}\left[G_i(a_{T,i,b})-G_i(a_{X,i,b})\right].
$$

Count every correction and every newly introduced loss. The original residual MEI remains 0.0025, so each qualifying contrast requires net gain greater than 0.04 over the sixteen decisions. Equality is not above the margin. The diagnostic 0.000625 corresponds to net gain 0.01 and remains descriptive; it cannot substitute for the residual criterion. [B01 card, §6][b01]; [prior response, “Native-value accounting”][prior]; [arithmetic, `native_accounting`][arithmetic].

An endpoint supplies the proposed alignment signal only when the new RAW-LONG trajectory meets the unchanged qualifier—at least six of eight exact oracle actions and mean regret at most 0.005 on each side—and all three endpoint contrasts exceed 0.0025. Historical RAW-LONG cannot supply competence on behalf of a weak new RAW trajectory. Conversely, neither new competence nor an effect above the MEI is a prelaunch requirement.

The references answer different questions. New RAW asks whether the aligned representation helps beyond the containing representation under the same cost objective. New DERANGED asks whether alignment matters beyond the retained residual-shaped packet distribution. Historical RAW prevents a positive being manufactured by damaging RAW with the new objective. These controls are adequate for the narrow conditional representation question. They do not establish universal causal specificity or independent performance. Keep historical and new contrasts separate; do not create an EVAL-selected best-of-two or row-wise oracle baseline. No historical learner replay is needed for this declared fixed-reference comparison. [Assessment, §4][assessment]; [evidence specification, §§11.8.1, 11.8.5–11.8.6][spec].

The original margin is arithmetically attainable against the seed-0 historical floor, but demanding:

| Endpoint | Historical RAW regret | New TRUE must be below, to clear that floor | Required recovery from historical TRUE |
| --- | ---: | ---: | ---: |
| SHORT | 0.006581880989529963 | approximately 0.004081880989529963 | greater than 0.014032131094784543 |
| LONG | 0.0037814300857039115 | approximately 0.0012814300857039115 | greater than 0.009634103628296 |

The ceilings in the middle column are deductions by subtracting 0.0025, not new measurements. They are necessary, not sufficient: new RAW and DERANGED may impose tighter comparisons. [Arithmetic, `historical_endpoint_regrets` and `TRUE_mean_recovery_needed_to_clear_fixed_RAW`][arithmetic].

The difficulty is not merely an exact-count threshold. Historical TRUE-LONG selects the costly TRANSIT-L action on `0/EVALUATION/K8/850/156/0` and `1/EVALUATION/K8/858/156/0`, with native regrets 0.05438343183122113 and 0.054714365493479994. P68’s arithmetic adds the third large correction on `5/EVALUATION/K8/833/60/0`; correcting all three without any new error would recover only 0.009277347274383108 in mean regret, still below the recovery needed to clear historical RAW-LONG by 0.0025. These exposed rows illustrate required net value; they must not become targeted TRAIN examples or an extra evaluation subset. [B04 result, `representations.TRUE_RESIDUAL.LONG.rows`][b04result]; [arithmetic, `three_largest_LONG_error_corrections` and `three_error_mean_recovery`][arithmetic].

A reference regret at or below 0.0025 makes a strictly larger improvement impossible against that reference, because treatment regret is nonnegative. This retains the old seed-1 LONG limit and applies to any new RAW or DERANGED endpoint that becomes sufficiently good. Such an outcome may be useful comparator learning; it is not residual impossibility or a reason to retune the margin. Zero label-oracle regret remains privileged arithmetic, not an accessible policy or a tuned headroom package. [Intake, “Bounded scientific reading”][intake]; [assessment, §4][assessment].

## Reading the observation without overstating it

Use the new P68 comparison meaning; do not automatically reuse B04’s branch implementation, whose `score_summary` calls the older B01 rule and contains no historical-RAW contrast. Preserve B04’s recorded branch unchanged. The necessary new output is the separate endpoint contrasts and competence-qualified reading, not an amendment to a completed rule. [B04 source, `score_summary`][b04code].

| Observation | Bounded interpretation and next action |
| --- | --- |
| New RAW-LONG is competent and all three contrasts exceed 0.0025 at an endpoint | Report an aligned native-value signal at that named endpoint on this reused seed and exposed panel. A bounded independent-seed follow-up may be recommended through ordinary authority; none is automatically launched or promoted to C. |
| The same inequalities hold at both endpoints | Report persistence over these two observed budgets only. This is not independent replication, convergence, or an asymptotic representation advantage. |
| A qualifying SHORT signal disappears at LONG as RAW improves | Preserve the short-budget signal and describe the budget dependence. Do not label the exact historical short-only branch satisfied unless its additional predicates actually hold. |
| TRUE improves over its historical value but fails one or more RAW/derangement comparisons | Report the native improvement and the failed contrasts. There is no identified aligned advantage. Generic objective or preprocessing benefit is a possible explanation, not automatically established by this pattern. |
| Competence changes or gains lie within the diagnostic margin | Report the comparator or action fact, without a material residual-value claim. Changes between 0.000625 and 0.0025 also remain below the original residual MEI. |
| Competent RAW but no qualifying aligned signal, or material native cost | Retain the narrow package result and all signed gains/losses. This does not establish equivalence, family exhaustion, or residual unlearnability. No automatic repair follows. |
| New RAW-LONG is weak | Preserve trustworthy native comparisons as diagnostics, but assign no competent-comparator residual polarity. Do not replace it with historical competence or silently add another seed or budget. |

Both endpoints must remain visible. A SHORT success does not erase a LONG loss; a LONG success does not erase a SHORT loss. Opposite signs require an explicitly mixed-budget reading, not selection of the favorable checkpoint. Failure to meet the conjunction is absence of the specified alignment signal, not proof of no effect whatsoever. There is no training-seed uncertainty estimate from this one reused seed, and the 96 scored decisions are repeated observations of sixteen identities, not 96 independent samples. [Assessment, §§3–4][assessment]; [evidence specification, §§11.8.2–11.8.4][spec].

An incomplete or corrupted primary measurement cannot support its dependent comparison. Independently trustworthy narrower observations remain reportable under the current dependency-based failure rule; no scientific negative follows from a transport, resource, or implementation failure. This prospective reading does not relabel any quarantined historical attempt. [Evidence specification, §4 and §11.8.7][spec].

## Scope, exposure, and proportional work

Select the proposed reused joint seed 0 and no others, with the unchanged common initialization law and one uninterrupted 258-update trajectory per representation, observed at 33 and 258. Preserve CPU FP32, one compute thread, Adam learning rate 0.001, betas 0.9/0.999, epsilon 1e-8, zero weight decay, batch 32, clip 1, canonical order, predictor fitting and calibration, and the existing fixed selected population. This is a new objective scope chosen after B04, not an independent seed or a repair of the two weak joint packages. It does not isolate gate initialization from predictor fitting or derangement. [Assessment, §3][assessment]; [B04 source, `prepare`, `packet_sets`, `train_path`][b04code].

The dominant algorithm work is preparation of the existing histories and targets, followed by three real gate-training paths. The supplied counts are:

| Work factor | Proposed amount |
| --- | ---: |
| Gate trajectories | 3 representations × 1 reused joint seed |
| Gate optimization | 3 × 258 = 774 Adam updates |
| Gate processed examples | 3 × 258 × 32 = 24,768 |
| Per-arm SHORT exposure | 33 updates; 1,056 examples; 22 visits per TRAIN row; nominal learning-rate exposure 0.033 |
| Per-arm LONG exposure | 258 updates; 8,256 examples; 172 visits per TRAIN row; nominal learning-rate exposure 0.258 |
| Shared predictor optimization | 100 updates × 128 = 12,800 processed examples |
| Gate evaluation | 3 × 2 × 16 = 96 decisions; 16 distinct EVAL identities |
| Softmax-cost arithmetic upper | 198,144 action terms across gate training |
| Shared host planning upper | 73,728 primitive team steps |

The host upper comprises 128 × 256 predictor steps, 64 × 256 calibration steps, 64 × 256 selected scans, and at most 64 × 8 × 16 native-label branch steps. The latter is one legal-action fan-out with a fixed continuation, not eight-way branching at every future step, a joint-action search over four agents, or a policy search prerequisite. B04 actually recorded 54,848 environment transitions and 3,520 branch steps. These are historical observations, not promised new counts. [Arithmetic, `proposed_work` and `historical_work_counts`][arithmetic]; [B01 card, §9][b01]; [B04 result, `work_counts`][b04result].

A two-arm RAW/TRUE run would be smaller but would relinquish the requested distinction from the deranged packet control. The third arm directly serves that question. A new historical-MSE replay, exact capacity study, complete support census, policy search, or fresh cost calibration adds no necessary discrimination here. The requested two readouts preserve short/long information within the same training trajectories rather than doubling training. This is a proportionate direct learning comparison, not a proposal to accelerate an unnecessary search. [Evidence specification, §§11.8.6 and 11.9][spec].

Historical B04 initial L2/RMS/Linf scales are 18.87916908516977 / 0.10402732933491829 / 0.28862619400024414. Its LONG displacement-to-initial L2 ratios are 0.1369227563959056, 0.08801190138964558, and 0.13797244260322725 for RAW, TRUE, and DERANGED; the corresponding Linf ratios are 0.915735779252775, 0.5338464052739748, and 0.9070316204301058. These anchors show historical finite movement. New-objective movement is unmeasured and must be reported in the actual run; it is not inferred from nominal exposure or required to match the old trajectory. [Arithmetic, `historical_exposure`][arithmetic].

### Cost anchors, not a runtime guarantee

P68 uses measured B04 wsl_4070 stages in

$$
\widehat T_j=3(S+258t_j+E_j+Q),\qquad
\widehat T_{shared}=3\left(S+\sum_j(258t_j+E_j)+Q\right).
$$

The recorded preparation S is 120.60043037099967 seconds. The per-update times t_j are approximately 0.06733760550, 0.06475017771, and 0.06617708207 seconds; the two-readout forward times E_j are approximately 0.014060345, 0.011793982, and 0.012702049 seconds; total scoring Q is 0.00270985699899029 seconds. Preparation is the dominant measured historical stage. [B04 result, `cost_law.measured_*`][b04result]; [arithmetic, `cost_projection`][arithmetic].

| Projection from those historical stages | Seconds |
| --- | ---: |
| RAW arm | 413.97090837899304 |
| TRUE arm | 411.96144017999904 |
| DERANGED arm | 413.06858835300955 |
| One shared invocation | 515.3820955440096 |

Do not sum the arm projections: they each include shared preparation. These figures are P68 arithmetic using the measured B04 stages, not B04’s older Windows-based `project_cost` forecast, and not a measured speedup or new-objective runtime. The factor three is the retained planning allowance, not a universal bound. New expected-cost objective overhead, setup/check/publication overhead, and current node load remain unmeasured. [Arithmetic, `cost_projection`][arithmetic]; [B04 source, `project_cost` and `run_experiment`][b04code].

The historical resource record is 171.8017914000011 seconds and peak RSS 1,541,214,208 bytes. Although the assessment calls the wall value complete, source inspection shows it is stored before `raw.publish_summary`; it is a pre-publication runner measurement, not independently verified end-to-end wall time. Publication remains an unknown component of the next invocation. This clarification changes no recorded number or scientific result. [B04 result, `resources`][b04result]; [B04 source, end of `run_experiment`][b04code].

Retain the proposed planning caps of 1,200 seconds per arm with attributable preparation/training/evaluation/publication and 1,500 seconds for the shared invocation, subject to ordinary allocation. The historical B04 arm monitor is training-plus-evaluation, so merely reusing its numeric cap is not evidence that the broader proposed accounting is already implemented. That is a bounded execution-definition issue for the new card, not a new experiment or approval layer. Actual execution uses the current remote-first route and fresh actual-node resource admission; neither an allocation nor current-node availability is established here. No automatic retry, replacement seed, resume, or larger budget is selected. [Assessment, §5][assessment]; [B04 source, `check_wall`][b04code].

The smallest useful added verification is the focused check of the changed masked loss, legal-action output, and three-contrast result reading, including its historical reference. It serves actual training and primary-comparison correctness. It is not another scientific arm, repeated smoke prerequisite, profiling experiment, framework migration, bit-equality programme, or complete mechanism audit. Only the current §11.4 launch conditions apply. [Evidence specification, §§11.4, 11.8.5–11.8.8 and 11.9][spec].

## Limits and direction effect

The question is eligible for this one B without a positive pilot, independent-seed pass, exact upper, full causal explanation, or tuned headroom. Requiring those before re-entry would conflict with the current specification and with the prior re-entry condition itself. Knowledge-integration v3 supplies no launch gate. No exception to the specification is proposed or implied. Historical stricter conditions and completed result meanings remain historical; they do not silently become new universal prerequisites. [Evidence specification, §§11.4 and 11.8–11.9][spec]; [assessment, §1][assessment].

The selected-panel ceiling remains adaptive B/EXPLORE on 64 outcome-informed members—48 TRAIN and sixteen repeatedly exposed EVAL identities—fixed four-agent K8/elapsed-4/cost-4 histories, and one reused joint seed. “No EVAL training” means no use of those rows in fitting this new run; it does not erase the earlier outcome-informed panel, seed, loss, or endpoint selection. Neither a positive nor a negative here estimates independent-population performance, training-seed variability, stable superiority/equivalence, natural prevalence, information/function-class value, full-policy return, variable K/N, general MARL/UAV value, transfer, safety, or resource efficiency.

The old natural-support family stays closed. The B04 negative, B05 comparator limitation, B06 native gain, B07 offsetting changes, both MEIs, absent tuned headroom, and unresolved A01 crash keep their meanings. Later successful paths do not explain A01. This decision neither depends on diagnosing that unrelated historical crash nor asserts that a concrete defect threatening the new primary comparison could be ignored. [Direction, B04–B07 and “Balanced-family Convergence disposition”][direction]; [intake, “Precise re-entry and limits”][intake]; [evidence specification, §11.8.7][spec].

The direction decision is therefore to permit bounded re-entry by selecting this specified native-cost comparison, with the interpretation and timing clarifications above. It is not a general reopening for arbitrary repairs and not a recast. A conforming new card can proceed through ordinary authority. Root retains allocation and integration; no lifecycle, priority, capacity, scheduling, source, or scientific-state mutation is performed by this consultation. The next scientific evidence is the actual three-arm native-action comparison, not another search or permission layer.

## Evidence access and provenance

All eleven listed scientific paths were accessed through the connected GitHub connector at source version `c9690db8ef340ac8201043183a864454f08c0431`. The links below pin that version. Read scope was the relevant sections/functions and result fields, not a claim to have audited every JSON row or imported dependency. No repository code, learner, evaluator, cost probe, or local clone was executed. No unlisted literature, local-library source, or repository implementation was substituted for the manifest.

| Source actually read | Reading used |
| --- | --- |
| [docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md][spec] | §§3–5.2 and §11, especially 11.4, 11.8 and 11.9. |
| [docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_P68_REENTRY_ASSESSMENT_20260908.md][assessment] | Complete bounded assessment, including proposed objective, controls, prediction and cost discussion. |
| [docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_P68_ARITHMETIC_20260908.json][arithmetic] | Complete arithmetic record; no independent execution of its calculation. |
| [docs/research/candidates/commitment_residual_triggered_options/DIRECTION.md][direction] | B04–B07 evidence and executed balanced-family convergence disposition, with adjacent earlier diagnostic context. |
| [docs/research/candidates/commitment_residual_triggered_options/CRTO_BALANCED_FAMILY_CONVERGENCE_INTAKE_20260905.md][intake] | Complete intake, especially bounded reading and precise re-entry. |
| [docs/research/candidates/commitment_residual_triggered_options/pro/2026-09-05-crto-balanced-family-convergence-01/RESPONSE.md][prior] | Strongest contradiction and re-entry sections; adjacent alternatives, scope and cost passages resolving inherited restrictions. |
| [docs/research/candidates/commitment_residual_triggered_options/CRTO_RESIDUAL_CYCLE_ENDPOINTS_B04_RESULT_20260904.json][b04result] | Selected native-action rows, RAW and TRUE endpoint summaries, DERANGED-LONG summary, contrasts, exposure, work, measured stages and resources. |
| [experiments/candidates/commitment_residual_triggered_options/residual_cycle_endpoints_b04/experiment.py][b04code] | Preparation, packet construction, training, scoring, cost and wall-accounting source. |
| [experiments/candidates/commitment_residual_triggered_options/raw_centered_loss_b07/experiment.py][b07code] | Centered loss and its matched training/comparison source. |
| [experiments/candidates/commitment_residual_triggered_options_common_history_gate_r01/evaluation.py][evaluator] | Legal printed-order action selection and native regret; neighboring text was not used to replace the selected-panel evaluator. |
| [docs/research/candidates/commitment_residual_triggered_options/CRTO_BALANCED_RESIDUAL_B01_R1_SCIENCE_CARD_20260904.md][b01] | §§3, 5–7 and 9, with adjacent predictor/calibration definitions; no new population-table search. |

The direct-source observations, supplied machine arithmetic, and documented historical results above are distinguished from the gradient/threshold deductions and the investment judgment. Library coverage and paper passages are reported only through the assessment’s attributed DM verification. No unavailable access prevents this direction decision.

[spec]: https://github.com/CartmanFatass/My-paper-code/blob/c9690db8ef340ac8201043183a864454f08c0431/docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md
[assessment]: https://github.com/CartmanFatass/My-paper-code/blob/c9690db8ef340ac8201043183a864454f08c0431/docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_P68_REENTRY_ASSESSMENT_20260908.md
[arithmetic]: https://github.com/CartmanFatass/My-paper-code/blob/c9690db8ef340ac8201043183a864454f08c0431/docs/research/candidates/commitment_residual_triggered_options/CRTO_NATIVE_COST_P68_ARITHMETIC_20260908.json
[direction]: https://github.com/CartmanFatass/My-paper-code/blob/c9690db8ef340ac8201043183a864454f08c0431/docs/research/candidates/commitment_residual_triggered_options/DIRECTION.md
[intake]: https://github.com/CartmanFatass/My-paper-code/blob/c9690db8ef340ac8201043183a864454f08c0431/docs/research/candidates/commitment_residual_triggered_options/CRTO_BALANCED_FAMILY_CONVERGENCE_INTAKE_20260905.md
[prior]: https://github.com/CartmanFatass/My-paper-code/blob/c9690db8ef340ac8201043183a864454f08c0431/docs/research/candidates/commitment_residual_triggered_options/pro/2026-09-05-crto-balanced-family-convergence-01/RESPONSE.md
[b04result]: https://github.com/CartmanFatass/My-paper-code/blob/c9690db8ef340ac8201043183a864454f08c0431/docs/research/candidates/commitment_residual_triggered_options/CRTO_RESIDUAL_CYCLE_ENDPOINTS_B04_RESULT_20260904.json
[b04code]: https://github.com/CartmanFatass/My-paper-code/blob/c9690db8ef340ac8201043183a864454f08c0431/experiments/candidates/commitment_residual_triggered_options/residual_cycle_endpoints_b04/experiment.py
[b07code]: https://github.com/CartmanFatass/My-paper-code/blob/c9690db8ef340ac8201043183a864454f08c0431/experiments/candidates/commitment_residual_triggered_options/raw_centered_loss_b07/experiment.py
[evaluator]: https://github.com/CartmanFatass/My-paper-code/blob/c9690db8ef340ac8201043183a864454f08c0431/experiments/candidates/commitment_residual_triggered_options_common_history_gate_r01/evaluation.py
[b01]: https://github.com/CartmanFatass/My-paper-code/blob/c9690db8ef340ac8201043183a864454f08c0431/docs/research/candidates/commitment_residual_triggered_options/CRTO_BALANCED_RESIDUAL_B01_R1_SCIENCE_CARD_20260904.md
