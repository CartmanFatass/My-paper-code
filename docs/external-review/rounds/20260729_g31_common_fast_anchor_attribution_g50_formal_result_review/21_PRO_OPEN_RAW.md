REGISTERED_RESULT_CONFORMANCE
formal_source_commit=
b8290699f5c10c593bbc21a6666c17950fae84d3

execution_code_commit=
23af6bf7c80a4b73c09cf0423f9f539972b1b55d

alignment_stage_commit=
4df41063d077ace7e0c9212e0cbadbf56e1be4b7

formal_branch=
FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50

scientific_acceptance=ACCEPT
scientific_iteration_cost=one_already_paid
The formal train, evaluation and analysis stages all exited successfully. The package is operational_valid=true, used the required CPU C++ backend with no Python fallback, and contains three replicates, two frozen arms, 100 phase-A and 100 phase-B updates per arm, 626,688 real transitions, 2,400 optimizer steps, 72 evaluation cells, 48 episodes per cell and 10,000 bootstrap resamples. Six final-only checkpoints are present and digest-bound to the terminal manifests.
The exact treatment was:
reference=
FAST_ANCHOR_THEN_SINGLE_IMMEDIATE

null=
SINGLE_IMMEDIATE_FROM_INITIALIZATION
Both arms began from the same fresh G50 native-six initialization. During phase A, the reference used the complete historical G40 package with actor credit from normalized
rt−stopgrad⁡(bIold(ξt)),r_t-\operatorname{stopgrad}(b_I^{old}(\xi_t)),rt​−stopgrad(bIold​(ξt​)),
while the null used the G49 centered/population-RMS-normalized raw reward and retained the same two-output baseline module, reward target, MSE loss and Adam exposure only as a shadow control with zero actor reads. Both arms then deleted all phase-A-only modules and optimizer state and used the identical G49 single-immediate phase-B route with fresh Adam states.
Under the frozen first-match selector, FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50 can be selected only after operational validity, source validity and reference access are established, and only when both arms pass the complete access contract and every registered reference-minus-null primary and component UCB is at most 0.05.
The allow-listed evidence note does not expose the individual G50 confidence intervals. No numerical interval beyond the registered branch semantics is inferred or invented here.

SCIENTIFIC_DISPOSITION
SCIENTIFIC_DISPOSITION=
SUPPORTED_RETAINED_FRESH_TWO_PHASE_SINGLE_IMMEDIATE_TRAINING_SUFFICIENCY_G50
Strongest supported proposition

Under the exact G50-P0 source, three fresh paired initializations, complete interpretation-B G40 graph matching, phase-A shadow-baseline exposure, forced phase-boundary deletion and Adam reset, G49 single-immediate phase B, fixed 200-update-per-arm budget, capacity-6/8/12 evaluation family and paired whole-episode confidence plan, the phase-A common-fast-anchor actor-credit treatment is not required for access and supplies no registered advantage exceeding the 0.05 margin over the matched single-immediate-from-initialization route.

The smallest supported training route is:
FRESH_NATIVE6_INITIALIZATION
→ PHASE_A_G49_SINGLE_IMMEDIATE_ACTOR_CREDIT
  + MATCHED_SHADOW_IMMEDIATE_BASELINE_PACKAGE
→ DELETE_ALL_PHASE_A_BASELINE/CRITIC/OPTIMIZER_STATE
  + RESET_ACTOR_ADAM
→ PHASE_B_G49_SINGLE_IMMEDIATE
→ FINAL_ONLY_ACTOR_CHECKPOINT
The result establishes statistical finite-budget training sufficiency, not bytewise structural equivalence. It does not show that the two phase-A objectives produced identical actor parameters, that the common-fast-anchor treatment had exactly zero effect, or that the null was superior.
Smallest supported units
supported_actor_credit_unit=
fresh_two_phase_single_immediate_actor_credit_G50_P0

supported_access_unit=
fixed_and_bounded_random_capacity_6_8_12_access_under_G50_source

supported_checkpoint_unit=
final_only_baseline_free_G49_actor_checkpoint_after_G50_phase_reset
The final deployed checkpoint remains the native-six, no-carry, baseline-free G49 actor. The baseline shadow exists only during phase A and is physically absent after the registered projection.
Smallest retired unit
Retire exactly:

The historical G40 baseline-conditioned common-fast-anchor actor-credit objective is necessary for access, or supplies a material finite-budget advantage over the matched single-immediate actor-credit objective, inside the exact G50-P0 two-phase/reset contract.

Also retire, within this boundary only:
common_fast_anchor_phase_A_actor_credit_as_required_curriculum_G50_P0
common_fast_anchor_phase_A_actor_credit_advantage_above_0.05_G50_P0
Retained and still-open units
The result retains rather than resolves:
phase_A shadow baseline module, loss, parameters and Adam state
immediate-target centering
population-RMS normalization
common entropy
the 100-update phase boundary
phase-A Adam disposal and fresh phase-B Adam
the registered G32/G34 source family
native-six actor information
active-set aggregation and action prefix
The fully simplified no-baseline-from-initialization route remains unproved because the G50 null deliberately retained baseline fitting and optimizer exposure as a nuisance-matched shadow control. The result therefore closes common-fast-anchor actor credit, not the shadow baseline apparatus.
The earlier G31/G40 evidence also remains valid in its own scope: G50’s null is not TEAM-GAE1, so this result does not retroactively invalidate G40’s complete-package advantage over that distinct ordinary-credit comparator.

COUNTEREXAMPLES_AND_EXCLUSIONS
The phase-A shadow baseline was not deleted
The null baseline has zero reads into actor advantage, actor gradient, action/log-probability, checkpoint selection, evaluation and result selection, but the module, immediate-target MSE, parameters and Adam exposure remain present during phase A.
Therefore G50 does not establish:
fresh baseline-free training sufficiency
phase-A baseline-module removability
phase-A baseline optimizer-state removability
arbitrary true-state baseline redundancy
The phase reset remains part of the successful treatment
Both arms discard phase-A Adam state and create fresh phase-B Adam after 100 updates. G50 does not establish equivalence to one uninterrupted 200-update single-immediate run, another reset time, or no reset.
The supported route is specifically:
100 single-immediate phase-A updates
→ reset and graph projection
→ 100 single-immediate phase-B updates
Noninferiority is not exact equality or null superiority
The selected branch establishes the registered 0.05 noninferiority condition. It does not prove:
zero parameter difference
zero utility difference
the null is statistically superior
the fast objective never changes learning
Any effect lying within the frozen margin remains compatible with the result.
No native-input or individual-coordinate result
Both arms retain the same six actor coordinates, active mask, active-set aggregation, log count and autoregressive prefix. G50 says nothing new about deleting any individual actor field.
It does not establish:
capability-field redundancy
load/mix redundancy
active-count redundancy
prefix redundancy
arbitrary current-state reduction
No universal history, baseline or recurrence theorem
G50 is a training-objective comparison on a fully observed bounded toy family. It does not establish that all history inputs, baselines, critics or recurrent states are universally unnecessary.
Ordinary recurrence remains a live simpler capability on sources where task-relevant information is absent from current observations. The current conjecture ledger explicitly preserves that reactivation condition.
No reversal of G31/G40 source-local credit evidence
G50 compares:
G40 baseline-conditioned immediate actor credit
versus
G49 centered/RMS-normalized immediate actor credit
It does not compare either route with TEAM-GAE1. G31’s paired G17/G18 result and G40’s package-level result remain supported in their registered source/comparator boundaries.
Source, capacity, horizon and deployment exclusions
The result is bounded to:
H=48
capacity-8 fixed-process training
capacity-6/8/12 fixed/random evaluation
three fresh initialization replicates
100+100 updates per arm
registered G40/G49 Adam and PPO semantics
registered phase reset
It does not establish arbitrary process laws, capacities, horizons, budgets, optimizers, tasks or initializers.
It is not a UAV result, not a real-world population statement and not a deployment superiority claim. UAV G1/G2 remain source-non-identifiable, identifiable non-G33 UAV transport remains parked, and G33 remains permanently abandoned.

CDC_PORTFOLIO_LEDGER_EDITS
These are exact scientific recording instructions. They authorize no repository mutation.
CONJECTURES.md
Replace the C-CONTINUOUS-ROSTER status paragraph with:
Markdown- Status: supported and retained at G50 as a native-six-coordinate, no-carry,
  fresh-initialization, two-phase single-immediate actor-credit route for the
  registered H=48, capacity-6/8/12 bounded-process toy family. Phase A retains
  an information-isolated immediate-baseline shadow solely to match the
  historical G40 graph and optimizer exposure; the final phase-B actor and
  checkpoint are baseline-free.
Insert after the G48 evidence paragraph:
Markdown- G49 structural predecessor: the duplicated-immediate route collapses exactly
  to one immediate target, one normalization, one policy loss and one actor
  gradient, with equal actor/Adam/action traces and canonical final checkpoint
  projection under its proof boundary.
Add:
Markdown- Formal common-fast-anchor attribution evidence: G50 starts both arms from
  byte-identical fresh native-six initializations. The reference uses the
  complete G40 baseline-conditioned fast-anchor objective in phase A; the null
  uses the G49 centered/RMS-normalized raw-reward actor objective while
  retaining identical baseline fitting and Adam exposure as a shadow control.
  Both arms then delete all phase-A-only state, reset Adam and use the same G49
  phase-B objective. The registered formal branch is
  `FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50`: both arms pass access and
  every registered reference-minus-null UCB satisfies the frozen 0.05
  noninferiority margin.
Replace the accepted training boundary with:
Markdown- Accepted training boundary:
  `FRESH_NATIVE6_INITIALIZATION →
  PHASE_A_SINGLE_IMMEDIATE_WITH_MATCHED_SHADOW_BASELINE →
  PHASE_A_STATE_DELETION_AND_ADAM_RESET →
  PHASE_B_G49_SINGLE_IMMEDIATE`.
  Retain one immediate reward target, its centering/population-RMS
  normalization, common entropy, the registered two-phase schedule and final
  actor-only checkpoint. The historical common-fast-anchor actor-credit
  treatment is deleted from the retained route.
Append to retired alternatives:
Markdown- G50 local closure: the historical G40 baseline-conditioned phase-A actor
  credit is neither required for access nor materially advantageous over the
  matched single-immediate actor credit inside G50-P0. This does not delete the
  phase-A shadow baseline, remove normalization or entropy, establish an
  uninterrupted 200-update route, or rewrite G31/G40 evidence against TEAM_GAE1.
Replace the stale strongest-remaining-explanation text with:
Markdown- Strongest remaining training explanations: the fresh G50 route still retains
  the phase-A shadow baseline package, immediate-target centering and
  population-RMS normalization, common entropy, the 100-update phase boundary,
  Adam reset and the frozen source/optimizer budget. The nearest structural
  question is whether the phase-A shadow baseline module, fitting loss,
  parameters and Adam state can be deleted without changing the actor path.
Under C-CREDIT, append:
Markdown- G50 update: within the exact continuous-roster G50-P0 family, fresh
  single-immediate actor credit is sufficient and the historical common-fast-
  anchor actor-credit treatment has no registered >0.05 advantage. G31/G40
  package-level evidence remains supported on its distinct G17/G18 and
  TEAM_GAE1 comparator boundaries. The smallest retained G50 actor-credit
  object is one centered/RMS-normalized immediate channel; phase-A shadow
  baseline exposure remains an untested nuisance-control reduction.
Delete or supersede the stale paragraphs claiming that exact single-channel collapse and fresh single-immediate actor-credit training remain untested. The current file still records both as unresolved and still names the common fast anchor as the leading explanation.
C-REC_EDIT=NONE
C-BASE_EDIT=NONE
C-BENCH_EDIT=NONE
C-COORD_EDIT=NONE
ALGORITHM_PRINCIPLES_EDIT=NONE
IDEA_PORTFOLIO.md
Replace the C-CONTINUOUS-ROSTER row with:
Markdown| C-CONTINUOUS-ROSTER | supported retained at G50: native-six no-carry,
fresh-initialization, two-phase single-immediate actor-credit bounded-process
route; phase-A baseline is shadow-only and the final actor is baseline-free |
Formal G50 selects `FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50`: both arms
pass the registered access contract and the fresh single-immediate route passes
every 0.05 noninferiority gate against the complete G40 common-fast-anchor
reference. | Retain
`FRESH_NATIVE6_INITIALIZATION → SINGLE_IMMEDIATE_WITH_SHADOW_BASELINE →
RESET/DELETE → G49_SINGLE_IMMEDIATE`. Test exact phase-A shadow-baseline
module removal next. Preserve normalization, entropy, phase-reset, broader
transport and identifiable non-G33 UAV directions separately. |
Replace the C-CREDIT row with:
Markdown| C-CREDIT | G31/G40 package-level evidence remains source-local; the retained
G50 continuous-roster actor credit is one fresh normalized immediate channel |
G48 removes the realized-successor package, G49 removes the duplicate
immediate channel, and G50 removes the historical baseline-conditioned
common-fast-anchor actor-credit treatment from the smallest retained route.
G50 does not make TEAM_GAE1 sufficient and does not yet remove the phase-A
shadow baseline. | First test exact shadow-baseline deletion; then preserve
normalization, entropy, phase-reset and source/optimizer conditioning as
separate live explanations. |
Append:
## G50 formal result update

g50_formal_source_commit=
b8290699f5c10c593bbc21a6666c17950fae84d3

g50_execution_code_commit=
23af6bf7c80a4b73c09cf0423f9f539972b1b55d

g50_alignment_stage_commit=
4df41063d077ace7e0c9212e0cbadbf56e1be4b7

g50_formal_branch=
FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50

g50_scientific_disposition=
SUPPORTED_RETAINED_FRESH_TWO_PHASE_SINGLE_IMMEDIATE_TRAINING_SUFFICIENCY_G50

g50_scientific_route=
FRESH_NATIVE6_INITIALIZATION_to_PHASE_A_SINGLE_IMMEDIATE_SHADOW_BASELINE_to_RESET_to_PHASE_B_G49_SINGLE_IMMEDIATE

g50_supported_unit=
fresh_two_phase_single_immediate_actor_credit_access_and_0.05_noninferiority_G50_P0

g50_failed_closed=
common_fast_anchor_phase_A_actor_credit_necessity_or_material_advantage_G50_P0

g50_retained_open_unit=
phase_A_shadow_baseline_module_loss_parameters_and_Adam_state

g50_scientific_iteration_cost=
one_already_paid

g50_valid_result_disposition=
CONTINUE

g50_next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51_DESIGN_ASSERTION_AUDIT

continuation_grant_status=
ACTIVE

exact_remaining_numeric_balance=
UNDETERMINED_IN_ALLOW_LIST

g50_supersedes_prior_grant_terminal_marker=
true
The current portfolio still identifies G48 as the latest authority and records the prior grant as exhausted; those are stale relative to the explicit active continuation grant and the accepted G50 formal result.
RESEARCH_DIRECTION_LEDGER.md
Add:
## G50 formal result update

g50_row=
fresh native-six two-phase single-immediate actor-credit training route

g50_row_status=SUPPORTED_RETAINED

g50_row_evidence=
docs/research/cdc/EVIDENCE_NOTES/20260729_G31_COMMON_FAST_ANCHOR_ATTRIBUTION_G50_FORMAL_RESULT.md
|docs/external-review/rounds/20260729_g31_common_fast_anchor_attribution_g50_formal_result_review/21_PRO_OPEN_RAW.md

g50_row_claim_ceiling=
exact G50-P0 source; fresh matched initialization; complete interpretation-B
G40 phase-A graph; shadow-baseline-matched null; forced phase-A deletion and
Adam reset; G49 phase B; H48; capacity-6/8/12 fixed/random evaluation;
registered 100+100 update budget and 0.05 margin; no uninterrupted-training,
fully-no-baseline, arbitrary-task, UAV or universal-credit claim

g50_scientific_route=
FRESH_NATIVE6_INITIALIZATION_to_SINGLE_IMMEDIATE_SHADOW_BASELINE_to_RESET_to_G49_SINGLE_IMMEDIATE

g50_supported_unit=
fresh_two_phase_single_immediate_actor_credit_sufficiency_inside_G50_P0

g50_failed_closed=
historical_G40_common_fast_anchor_actor_credit_required_for_access_or_material_advantage_inside_G50_P0

g50_formal_branch=
FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50

g50_formal_inventory=
replicates3|arms2|phase_A_updates100|phase_B_updates100|H48|
transitions626688|optimizer_steps2400|cells72|episodes_per_cell48|
bootstrap10000|final_only_checkpoints6

g50_next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51_DESIGN_ASSERTION_AUDIT
Add under FAILED_CLOSED:
Markdown| G50-P0 中 historical G40 common-fast-anchor phase-A actor credit 对 access
的必要性或相对 fresh single-immediate actor credit 的 >0.05 material
advantage | `FAILED_CLOSED` | Exact matched fresh-initialization G50 formal
package selects `FRESH_SINGLE_IMMEDIATE_TRAINING_SUFFICIENT_G50`; both arms
pass access and every registered reference-minus-null UCB is <=0.05. |
不得写成“G40/G31 在其他 source/comparator 上无效”“baseline module 已删除”
“一个连续 200-update run 已充分”或“所有任务只需即时 reward”。 |
Replace the stale fresh-training row with two smallest units:
Markdown| Fresh two-phase single-immediate actor-credit training with matched phase-A
shadow baseline and forced Adam reset | `SUPPORTED_RETAINED` | G50 formal
branch establishes access and 0.05 noninferiority against the complete G40
common-fast-anchor reference. | Bound to the exact G50-P0 source, reset,
shadow-control and budget; no fully-no-baseline or uninterrupted-run claim. |

| G50 phase-A shadow baseline module, fitting loss, parameters and Adam state
exact structural deletion | `OPEN_UNTESTED` | The null actor never reads the
baseline, but G50 deliberately retains baseline fitting and optimizer exposure
as a matched nuisance control. | Seek a zero-trajectory dependency/optimizer
factorization proof and, only if needed, one shared 8x48 numerical-kernel
witness. |
Preserve without status change:
immediate centering and population-RMS normalization
common entropy
phase-reset and optimizer-conditioning explanations
broader process/horizon/capacity
identifiable non-G33 UAV transport
recurrence under hidden-information sources
C-BASE and C-COORD
asynchronous skill lifetime and intrinsic reward as OUT_OF_SCOPE_FROZEN
G33 as permanently abandoned
The ledger requires changing only the smallest supported or refuted unit; it must not convert this local G50 result into a universal temporal-credit or deployment conclusion.

PORTFOLIO_DELTA_AND_VALID_RESULT_DISPOSITION
VALID_RESULT_DISPOSITION=CONTINUE
The allow-listed review package identifies an active unattended continuation grant and records the G50 conclusion-bearing cost as already paid. It does not expose an exact remaining integer, so none is fabricated. Because an executable, in-scope and cheaper structural candidate remains, neither terminal disposition applies.
DirectionState after G50Advancement or reactivation conditionFresh two-phase single-immediate actor-credit routeSupported and retainedReuse only inside the G50 source/reset/budget boundaryHistorical common-fast-anchor actor creditFailed closed locallyA distinct source or comparator, not more G50 seeds or budgetPhase-A shadow baseline moduleLive; scheduledExact dependency/optimizer-factorization reductionImmediate centering and population-RMS normalizationLive, unscheduledHold fresh route, shadow status, entropy, reset and optimizer fixedCommon entropyLive, unscheduledMatched entropy-only attribution on the accepted minimal routePhase boundary and Adam resetLive, unscheduledCompare against an exposure-matched uninterrupted optimizer routeBroader process/horizon/capacityLive, unscheduledChange one source axis at a time after the minimal training graph is settledIdentifiable non-G33 UAV transportParkedPhysically feasible, load-bearing, support-valid sourceOrdinary recurrence/EHCParkedSource with relevant information absent from current observationsC-BASE/C-COORDLive outside this reductionRepresentation-fixed access or coordination comparisonAsynchronous skill lifetime/intrinsic rewardOUT_OF_SCOPE_FROZENExplicit later scope transitionG33 lineagePermanently abandonedNo reactivation
Scheduling the baseline reduction is an attribution choice, not a claim that normalization, entropy, reset, transport or other retained directions are scientifically inferior. The project principles require one action at a time while preserving unscheduled ideas as live or parked.

CURRENT_SCHEDULED_ACTION_IF_CONTINUE
current_scheduled_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51_DESIGN_ASSERTION_AUDIT

review_mode=
DESIGN_ASSERTION_AUDIT

design_compute=0
scientific_iteration_cost_at_design=0
Exact next question
Can an exact structural comparison be frozen between:
reference=
G50_FRESH_SINGLE_IMMEDIATE_WITH_PHASE_A_SHADOW_BASELINE

reduced=
G50_FRESH_SINGLE_IMMEDIATE_WITHOUT_PHASE_A_BASELINE_MODULE
where both arms retain exactly:
same fresh native-six actor/log_std initialization
same G49 single-immediate actor credit in phase A
same immediate centering and population-RMS normalization
same common entropy
same source ledgers, action noise and environment trajectories
same PPO passes and actor optimizer exposure
same phase boundary and fresh phase-B Adam
same G49 single-immediate phase B
same final-only actor checkpoint contract
and the only treatment is deletion from initialization of:
credit_baselines module and true-state input consumer
immediate-baseline target and MSE loss
baseline parameters and gradients
baseline Adam slots and optimizer membership
baseline liveness/diagnostic records
baseline checkpoint and artifact fields
Structural estimand
Define DG51D_{G51}DG51​ as the maximum exact difference across:
actor/log_std assigned gradients
actor parameter bytes
actor Adam step/exp_avg/exp_avg_sq bytes
pre-tanh means
actions and token/joint log-probabilities
reward/roster/lifecycle traces
phase-boundary projected actor bytes
phase-B actor/Adam trajectories
canonical final actor checkpoint projection
The exact-removability branch requires:
DG51=0.D_{G51}=0.DG51​=0.
Frozen first-match outcomes
1. INVALID_G50_PHASE_A_SHADOW_BASELINE_MODULE_REDUCTION_G51

2. UNREGISTERED_PHASE_A_SHADOW_BASELINE_COUPLING_G51

3. PHASE_A_SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G51

4. NUMERICALLY_UNRESOLVED_PHASE_A_SHADOW_BASELINE_REDUCTION_G51
A positive result may support only exact removal of the registered G50 phase-A shadow baseline apparatus. It may not establish arbitrary baseline redundancy, removal of immediate normalization or entropy, uninterrupted-training sufficiency, UAV transport or universal memorylessness.
Smallest evidence ceiling
First seek a zero-trajectory static dependency and per-parameter Adam-factorization proof. If the actual Adam kernel requires a numerical witness, freeze at most:
one accepted G50 fresh initialization
one shared 8-episode × 48-step stored phase-A batch
real_transitions<=384

PPO_passes_per_arm=2
actor_optimizer_steps_per_arm=2
total_optimizer_steps<=4

bootstrap_resamples=0
formal_statistical_run=false

H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
wall_clock<=1200_seconds
The same stored trajectory must feed both paths; duplicated environment interaction is unnecessary.
Implementation-only degrees of freedom are file names, tensor layout, vectorization, serialization and proof-test organization. The deletion boundary, actor-gradient equality, Adam factorization, phase reset, artifact projection and claim ceiling are scientific fields.
This disposition authorizes no implementation, Git operation, nonformal run or formal run.