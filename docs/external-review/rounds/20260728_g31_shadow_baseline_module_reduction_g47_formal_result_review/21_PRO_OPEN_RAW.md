REGISTERED_RESULT_CONFORMANCE
REGISTERED_FORMAL_BRANCH=
SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G47

scientific_acceptance=ACCEPT
scientific_iteration_cost=0

formal_source_commit=
23939a16f9a6035fda91506f6e76ff742bf23b73

aligned_implementation_commit=
fab68ae1a87578b59c1a004ac5415edf55ee7452

alignment_stage_commit=
33432c16df22e5432710a5e5b05aa34a82c5a45f

The registered branch is accepted without relabelling or expansion. The exact formal package reports:

formal=true
formal_statistical_run=false
operational_valid=true

static_certificate_pass=true
dynamic_equivalence_pass=true
D_G47=0

H=48
K_search=0
hypothetical_transitions=0

shared_real_trajectory_batches=1
episodes=8
real_transitions=384
PPO_passes_per_arm=2

reference_baseline_optimizer_steps=2
reduced_baseline_optimizer_steps=0

bootstrap_resamples=0
evaluation_optimizer_steps=0
additional_real_transitions=0

checkpoint_selection=final_only
canonical_actor_checkpoint_bytes_equal=true
pre_tanh_action_logprob_trace_equal=true
reward_roster_lifecycle_trace_equal=true

The runtime used the required C++ backend without Python fallback, completed train/evaluate/analyze with exit code zero, and bound the exact corrected ALIGNED implementation and stage.

The formal result rests on two complementary forms of evidence:

a zero-trajectory static dependency and optimizer-factorization certificate; and

a proof-sized numerical guard on one shared 8-by-48 trajectory, checking both PPO passes and obtaining exact D_G47=0.

The code-science index binds zero baseline-module and baseline-only true-state dependencies, per-parameter Adam projection, exact actor-gradient and trace equivalence, canonical checkpoint equality, and the corrected read-trapping true-state guard.

This is therefore a structural/function-matching result, not a statistical performance comparison. No confidence interval, utility margin, fresh-seed population inference, or new deployment-domain evaluation was used or is needed for the registered claim.

SCIENTIFIC_DISPOSITION
SCIENTIFIC_DISPOSITION=
PROVED_EXACT_POST_ANCHOR_SHADOW_BASELINE_APPARATUS_REMOVABILITY_G47
Exact supported proposition

In the exact accepted post-G46 RAW route, the shared two-output shadow baseline module, its baseline-only true-current-state input path, immediate and successor target-fitting losses, baseline parameters and Adam state, baseline liveness diagnostics, and baseline checkpoint/output-schema fields are structurally removable without changing the retained actor objective, actor gradients, actor/log_std parameters, retained Adam state, pre-tanh outputs, actions, token or joint log-probabilities, registered source traces, or canonical final actor checkpoint.

The proposition is bounded to the exact two-arm graph:

reference=
NATIVE6_G31_RAW_NORM_SHADOW_BASELINE

reduced=
NATIVE6_G31_RAW_NORM_NO_BASELINE_MODULE

and to:

accepted G40 common fast anchor
accepted G41 no-slow projection
accepted G46 RAW actor-credit route
source_commit=23939a16...
H=48
one shared stored 384-transition trajectory
two PPO passes per arm
per-parameter Adam factorization
final-only checkpoints

The static certificate establishes zero baseline dependencies into actor gradient, entropy, action/log-probability, checkpoint selection, evaluation, and source/lifecycle paths. The reduced graph has no baseline module, no baseline-only true-state field, and no replacement dummy or compatibility path. The dynamic guard then confirms exact retained-state equality after each PPO pass.

Accepted post-anchor route

The smallest accepted post-anchor route is now:

COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_RAW_NORM_NO_BASELINE_MODULE

Its retained actor-credit rule is:

x
t
I
	​

=r
t
	​

,x
t
S
	​

=G
t+1
	​

,

followed by:

separate per-channel centering
independent per-channel RMS scaling
literal 0.5*(g_I+g_S)
one common entropy term

The reduced route contains no:

standalone slow critic
credit-baseline module
baseline-only true-state input
baseline losses
baseline optimizer membership or Adam state
baseline liveness diagnostics
baseline checkpoint keys or output schema
DB vector, DB norm or DB shadow
Smallest retired unit

Retire exactly:

The post-anchor G46 RAW route requires the shadow baseline apparatus—module, true-state input, target-fitting losses, optimizer state, diagnostics, or checkpoint fields—to preserve its actor update or executable behavior.

This is a stronger conclusion than G45–G46 noninferiority: G47 establishes exact causal disconnection and function matching, not merely the absence of a material utility difference.

Smallest retained units

The following remain retained:

native-six current-state actor
no learned actor carry
accepted common fast anchor
immediate reward channel
realized-successor channel
immediate/successor decomposition
separate channel centering
independent relative channel scaling
literal equal-channel composition
common entropy
per-parameter actor Adam
active mask, active-set aggregation and action prefix

Independent relative scaling remains positively supported by G44. G47 does not weaken that result.

State-schema and deployment consequence

The reduced post-anchor final actor checkpoint may omit all baseline module, baseline optimizer, baseline true-state-input, loss, diagnostic, and output-schema fields. Its canonical retained actor and Adam projections are bitwise identical to the reference projection.

That supports a smaller checkpoint and training-state schema for the exact G47 route. It does not establish general deployment transport outside the registered source or remove every centralized object from every phase of training.

COUNTEREXAMPLES_AND_EXCLUSIONS
Post-anchor deletion is not fresh end-to-end baseline-free training

Both arms begin from the accepted common fast anchor. G47 does not retrain the native-six controller from a fresh initialization without a baseline apparatus during the anchor phase.

It therefore does not establish:

the common fast anchor can be trained baseline-free
all native-six-input training is baseline-free
a fresh baseline-free initializer reaches the same access contract

The result is exact after the registered branch start.

No individual-field redundancy result

G47 deletes one complete baseline-only true-state path because that path is causally disconnected from the accepted actor update. It does not identify which individual coordinates of any true-state vector would be redundant in a different critic or baseline.

Nor does it show that any of the six actor-visible current-state fields can be removed:

capabilities
anonymous priority
current load
current target mix
log active count
active-set/prefix information
No arbitrary-baseline theorem

The result applies to the exact shared two-output shadow baseline module and its registered optimizer ownership.

It does not establish exact removability for:

a baseline sharing a trainable trunk with the actor;

a baseline entering clipping, normalization, gradient scaling, or checkpoint selection;

a stochastic baseline consuming RNG;

a baseline used by TEAM-GAE1 or another estimator;

a critic or baseline under another optimizer;

an execution-time value function with a distinct causal role.

Such a module would violate the static factorization used by G47 rather than being covered by it.

No arbitrary history or memorylessness claim

The baseline-only true-state path is removable because the exact G47 actor objective does not read it. This does not imply:

all history fields are redundant
all tasks are Markov in the current actor observation
recurrence is universally unnecessary
task-level history necessity has been disproved

Ordinary recurrence remains retained for sources where task-relevant information is absent from the current observation. The current conjecture ledger explicitly preserves that reactivation condition.

No arbitrary-constant or filler conclusion

The reduced arm adds no constant, filler, dummy parameter, zero baseline, compatibility head, or checkpoint placeholder. Therefore G47 supplies no evidence about arbitrary constants or surrogate baseline values.

Its conclusion is deletion, not substitution.

The 384-transition guard is not a population experiment

The shared batch verifies the realized numerical kernel after the static proof. It does not provide statistical evidence across:

random initializations;

fresh training replicates;

arbitrary trajectories;

other process families;

other capacities or horizons.

The generality within the exact implementation comes from the static dependency and optimizer-factorization certificate, not from treating one batch as a representative sample.

Source, capacity and process exclusions

G47 inherits the accepted continuous-roster boundary:

H=48
configured capacities=6|8|12
capacity-8 fixed-process training lineage
G34-P0 bounded fixed/random process family
registered L/R/J/T event structure
accepted common anchors

It does not establish arbitrary configured capacity, active count, process law, repeated leave/rejoin frequency, event type, horizon, task, or optimizer.

Broader process/horizon/capacity transport remains OPEN_UNTESTED.

No new utility or superiority claim

Because the result is exact structural equivalence:

it does not establish a new utility gain;

it does not show the reduced route is statistically superior;

it does not compare full algorithms;

it does not show TEAM-GAE1 is sufficient;

it does not replace the G40 package-level credit result;

it does not establish UAV transport.

UAV G1/G2 remain source-non-identifiable, identifiable non-G33 UAV transport remains parked, and G33 remains permanently frozen.

CDC_PORTFOLIO_LEDGER_EDITS

These are exact recording instructions. They do not authorize repository mutation.

CONJECTURES.md

Replace the C-CONTINUOUS-ROSTER status paragraph with:

Markdown
- Status: supported and retained at G47 as a usable native-six-coordinate,
  no-carry, post-anchor no-slow/no-DB/no-baseline, target-only,
  literal-raw-norm, independently scaled G31-credit continuous-roster test
  version for the registered H=48, capacity-6/8/12 bounded-process family.

Insert after the existing G44 evidence:

Markdown
- Formal actor-baseline reduction evidence: G45 removes shared-baseline
  subtraction from the actual actor-credit residual and direction; G46 removes
  the remaining baseline-derived scalar credit-norm schedule. G47 then proves
  exact structural removal of the residual shadow apparatus. The static
  dependency and optimizer-factorization certificate passes, and one shared
  8x48 stored trajectory with two PPO passes per arm gives `D_G47=0`,
  bitwise-equal retained actor/Adam state, equal pre-tanh/action/log-probability
  traces and equal canonical final actor checkpoint projections.

Replace the accepted post-anchor boundary with:

Markdown
- Accepted post-anchor training boundary:
  `COMMON_NATIVE6_FAST_ANCHOR →
  NATIVE6_G31_RAW_NORM_NO_BASELINE_MODULE`.
  Retain the native-six actor, immediate and realized-successor target
  decomposition, separate centering, independent per-channel scaling,
  literal equal-channel composition and common entropy. Delete the standalone
  slow critic, all DB composition, the shared two-output baseline module,
  baseline-only true-state input, baseline target-fitting losses, baseline
  parameters/Adam state, liveness diagnostics and baseline checkpoint schema.

Append to the retired-alternatives paragraph:

Markdown
- G47 exact structural closure: the post-anchor shadow baseline apparatus is
  causally disconnected and exactly removable from the accepted G46 RAW
  route. This closes only the registered module, input, loss, optimizer and
  checkpoint apparatus after the common branch start; it does not establish
  fresh end-to-end baseline-free training or universal baseline redundancy.

Replace the strongest remaining training-explanations paragraph with:

Markdown
- Strongest remaining training explanations: the accepted route still uses
  realized-successor targeting, immediate/successor decomposition, separate
  channel centering, independent relative scaling and the common fast anchor.
  Independent relative scaling is positively retained by G44. The baseline
  apparatus is no longer a live explanation for post-anchor actor learning.

Replace the C-CREDIT status paragraph with:

Markdown
- Status: supported retained for the registered G17/G18 family and the
  shared-anchor G40-P0 branch, narrowed locally by G41--G47. The retained
  post-anchor credit unit is immediate/realized-successor decomposition,
  separate centering, independent relative scaling and literal equal-channel
  composition. The slow critic, DB composition and all baseline-module
  influence or shadow apparatus are removed from the accepted post-anchor
  route.

Append:

Markdown
- G47 update: exact graph, gradient, Adam, action, trace and canonical
  checkpoint equivalence proves the shadow baseline module structurally
  removable from the post-G46 RAW route. The next component-level question is
  whether the realized-successor channel itself adds access or material value
  over an information-matched duplicated-immediate null.
C-REC_EDIT=NONE
C-BASE_EDIT=NONE
C-BENCH_EDIT=NONE
C-COORD_EDIT=NONE
ALGORITHM_PRINCIPLES_EDIT=NONE

The current file still presents the G43 route as its main status and records G44 only as an appended update, so the accepted boundary must be consolidated rather than leaving the baseline apparatus implicitly retained.

IDEA_PORTFOLIO.md

Replace the C-CONTINUOUS-ROSTER row with:

Markdown
| C-CONTINUOUS-ROSTER | supported retained at G47: native-six no-carry,
post-anchor no-slow/no-DB/no-baseline, target-only literal-raw-norm,
independent-channel-scale G31-credit bounded-process test version | G41--G43
remove the standalone slow critic and DB composition; G44 retains independent
relative scaling; G45--G46 remove baseline-conditioned actor direction and
scalar norm; G47 proves the residual shadow baseline module, true-state input,
losses, Adam state and checkpoint schema exactly removable with `D_G47=0`. |
Retain `COMMON_NATIVE6_FAST_ANCHOR →
NATIVE6_G31_RAW_NORM_NO_BASELINE_MODULE`. Schedule realized-successor-channel
attribution next. Broader transport and identifiable non-G33 UAV remain live
or parked. |

Replace the C-CREDIT row with:

Markdown
| C-CREDIT | supported on G17/G18 and shared-anchor G40-P0; post-anchor
baseline apparatus exactly removed by G47 | The retained local unit is the
immediate/realized-successor two-channel package with separate centering,
independent relative scaling and literal equal-channel composition. G47 shows
that no slow critic, DB mechanism or baseline module is needed after the
common anchor. | Test the realized-successor channel against an exact
duplicated-immediate null. Preserve decomposition, centering, scaling,
common-anchor and source-transfer questions separately. |

Append:

## G47 formal structural result update

g47_formal_branch=
SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G47

g47_scientific_disposition=
PROVED_EXACT_POST_ANCHOR_SHADOW_BASELINE_APPARATUS_REMOVABILITY_G47

g47_scientific_route=
COMMON_NATIVE6_FAST_ANCHOR_to_NATIVE6_G31_RAW_NORM_NO_BASELINE_MODULE

g47_exact_result=
static_dependency_certificate_pass|
optimizer_factorization_pass|
D_G47_0|
canonical_actor_checkpoint_projection_bitwise_equal

g47_failed_closed=
post_anchor_shadow_baseline_module_true_state_input_loss_optimizer_and_checkpoint_necessity_G47

g47_scientific_iteration_cost=0

g47_next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48_DESIGN_ASSERTION_AUDIT

conclusion_bearing_iterations_consumed=36
iterations_remaining=1

Set the portfolio’s terminal disposition field to the disposition token declared in the next section.

The current portfolio records G44 as the latest formal iteration and G45 only as a design audit; the G47 block supersedes that stale active-route description without changing unrelated directions.

RESEARCH_DIRECTION_LEDGER.md

Supersede the stale G45 design-only row with the consolidated accepted chain:

g45_row_status=SUPPORTED_RETAINED
g45_failed_closed=
shared_true_state_baseline_subtraction_required_for_access_or_material_advantage_inside_G45_P0

g46_row_status=SUPPORTED_RETAINED
g46_failed_closed=
baseline_derived_dynamic_scalar_credit_norm_required_for_access_or_material_advantage_inside_G46_P0

Add:

## G47 formal structural result update

g47_row=
continuous-roster native-six target-only raw-norm independent-scale
post-anchor route with no baseline module

g47_row_status=SUPPORTED_RETAINED

g47_row_evidence=
docs/research/cdc/EVIDENCE_NOTES/20260728_G31_SHADOW_BASELINE_MODULE_REDUCTION_G47_FORMAL_RESULT.md
|docs/external-review/rounds/20260728_g31_shadow_baseline_module_reduction_g47_formal_result_review/21_PRO_OPEN_RAW.md

g47_row_claim_ceiling=
exact accepted post-G46 RAW implementation after the common branch start;
H48; one shared 384-transition trajectory; two PPO passes; static dependency
and per-parameter Adam factorization; no statistical, arbitrary-task,
fresh-training, UAV or universal-baseline claim

g47_scientific_route=
COMMON_NATIVE6_FAST_ANCHOR_to_NATIVE6_G31_RAW_NORM_NO_BASELINE_MODULE

g47_supported_unit=
post_anchor_baseline_free_target_only_raw_norm_actor_credit_route

g47_failed_closed=
post_anchor_shadow_baseline_module_true_state_input_target_fitting_loss_Adam_and_checkpoint_necessity_inside_G47

g47_exact_equivalence=
D_G47_0|actor_gradient_bitwise_equal|actor_Adam_bitwise_equal|
action_logprob_trace_equal|canonical_actor_checkpoint_equal

g47_scientific_iteration_cost=0
g47_conclusion_bearing_iterations_consumed=36
g47_iterations_remaining=1

g47_next_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48_DESIGN_ASSERTION_AUDIT

Add under FAILED_CLOSED:

Markdown
| G47 中 post-anchor shadow baseline module、baseline-only true-state input、
target-fitting losses、baseline optimizer state、diagnostics 与 checkpoint
schema 的结构必要性 | `FAILED_CLOSED` | 静态 dependency/Adam factorization
证书通过；一个共享 8x48 batch 上两次 PPO 后 `D_G47=0`，actor gradient、
actor/log_std、actor Adam、action/log-probability、registered traces 与
canonical final actor checkpoint 均精确相等。 | 不得写成“fresh training
不需要 baseline”“所有 baseline/critic 都无用”“所有 history input
冗余”或“其他任务/optimizer 同样可删除”。 |

Add under OPEN_UNTESTED:

Markdown
| G47 accepted baseline-free RAW route 中 realized-successor channel package
的局部必要性 | `OPEN_UNTESTED` | 保持 common anchor、native-six actor、
baseline-free graph、separate centering、independent scaling、literal equal
mean、source、paired interaction 与 Adam exposure 不变；比较
immediate-plus-realized-successor reference 与不读取 `G_(t+1)` 的
duplicated-immediate null。 | G40 supports the complete G31 package, but after
G41--G47 reductions the realized-successor channel has not yet received a
component-level comparator. Current scheduled action is G48 design audit. |

Retain without status change:

broader process/horizon/capacity;

identifiable non-G33 UAV transport;

recurrence under hidden-information sources;

C-BASE and C-COORD;

asynchronous lifetime and intrinsic reward as out of scope;

G33 as permanently frozen.

The direction ledger defines SUPPORTED_RETAINED, FAILED_CLOSED, and OPEN_UNTESTED as smallest-unit statuses and requires External-Pro authority for status changes.

PORTFOLIO_DELTA_AND_VALID_RESULT_DISPOSITION
conclusion_bearing_iterations_consumed=36
remaining_conclusion_bearing_iterations=1

G47 has scientific iteration cost zero, so the one remaining conclusion-bearing iteration is not consumed by this exact structural result. The formal brief explicitly records one remaining iteration, and the External-Pro charter requires continuation when an executable in-scope candidate remains.

An executable and decision-changing candidate remains: after removing every post-anchor baseline path, the realized-successor channel is the nearest unresolved component of the retained G31 credit package. Testing it can either:

simplify the route to an immediate-only controller; or

identify the realized-successor channel package as the core remaining finite-budget credit mechanism.

Neither terminal condition applies.

VALID_RESULT_DISPOSITION=CONTINUE

Direction	State after G47	Advancement or reactivation condition
Baseline-free post-anchor RAW route	Supported and retained	Use as the current branch-start route
Shadow baseline apparatus	Failed closed in G47	A distinct estimator with an actual baseline dependency, not G47 tuning
Independent relative channel scaling	Supported and retained	Preserve in G48
Realized-successor channel package	Live; scheduled	G48 matched successor-versus-duplicated-immediate audit
Immediate/successor decomposition	Live, unscheduled	Revisit after the successor channel’s local disposition
Separate channel centering	Live, unscheduled	Hold targets, scaling and composition fixed
Common fast anchor	Live, unscheduled	Fresh function- and exposure-matched branch-start study
Fresh end-to-end baseline-free training	Live, unscheduled	Compare fresh baseline-bearing and baseline-free anchor training
Broader process/horizon/capacity	Live, unscheduled	Change one source axis at a time
Identifiable non-G33 UAV transport	Parked	Freeze a physically feasible, load-bearing, support-valid source
Recurrence/EHC	Parked	Use a source with task-relevant information absent from current observation
C-BASE/C-COORD	Live outside this reduction	Representation-fixed access or coordination separation
Asynchronous skill lifetime/intrinsic reward	OUT_OF_SCOPE_FROZEN	Later explicit scope transition
G33 lineage	Permanently frozen	No reactivation

Scheduling G48 is an attribution choice, not a claim that the other live directions are scientifically invalid or unimportant.

CURRENT_SCHEDULED_ACTION_IF_CONTINUE
current_scheduled_action=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48_DESIGN_ASSERTION_AUDIT
Scientific rationale

The post-anchor route has now removed:

slow critic
DB angular composition
DB scalar norm
baseline-conditioned residual direction
baseline-derived scalar norm
baseline module and all baseline-only state

The nearest remaining specialized credit object is the second channel:

G
t+1
	​

,

the realized future tail.

This is more discriminating than another structural cleanup because:

G40 supports the complete G31 package against TEAM-GAE1;

G41–G47 have removed most auxiliary apparatus;

G44 positively retains independent relative scaling;

the realized-successor channel has never been compared against a no-future-target, information-matched post-anchor null.

It is cheaper and more decision-relevant than opening a new process family, fresh-anchor study, or UAV source. It can use the already registered training/evaluation family and the final remaining conclusion-bearing iteration.

EXECUTABLE_SCIENTIFIC_BOUNDARY
next_boundary=
CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48_DESIGN_ASSERTION_AUDIT

review_mode=DESIGN_ASSERTION_AUDIT
design_audit_compute=0
Exact G48 design question

Can a conclusion-bearing matched post-anchor comparison be frozen between:

NATIVE6_G31_IMMEDIATE_REALIZED_SUCCESSOR — the accepted G47 baseline-free route using immediate reward and realized-successor channels; and

NATIVE6_G31_DUPLICATED_IMMEDIATE — the identical baseline-free route in which the successor channel is replaced by a separately materialized duplicate of the immediate channel and no G_(t+1) value enters actor credit?

The only intended treatment is the complete realized-successor channel package.

Frozen source and graph

Both arms retain exactly:

accepted G40 common fast anchors, replicates 0|1|2
accepted G41 no-slow projection
accepted G47 no-baseline-module projection
native-six no-carry actor and log_std
same actor observations and active-set context
same source ledgers, episode IDs and member-owned action noise
same reward and environment lifecycle
same PPO clipping and likelihood semantics
same actor parameter inventory and Adam hyperparameters
same interaction and optimizer-step exposure
same final-only actor checkpoint schema

Training source:

G32 capacity-8 fixed process

Evaluation source:

G34-P0 fixed/random processes
configured capacities=6|8|12
H=48

Exclude:

baseline or critic reintroduction
DB composition
recurrence change
actor-information change
source or reward change
G33 or UAV promotion
Exact target laws
Reference arm
x
t
I
	​

=r
t
	​

,
x
t
S
	​

=G
t+1
	​

,

with the exact accepted realized-tail authority:

G
H
	​

=0,G
t
	​

=r
t
	​

+0.99G
t+1
	​

.

Each channel is separately centered and independently RMS-scaled once from the complete stored trajectory before both PPO passes.

The assigned actor gradient is:

d
REF
	​

=
2
1
	​

(g
I
	​

+g
S
	​

)+g
E
	​

,

where g
E
	​

 is the inherited common entropy gradient added once.

Duplicated-immediate null
x
t
I
1
	​

	​

=r
t
	​

,x
t
I
2
	​

	​

=r
t
	​

.

The two immediate rows are separately materialized but must be byte-identical after the same centering and RMS rule.

The assigned actor gradient is:

d
NULL
	​

=
2
1
	​

(g
I
1
	​

	​

+g
I
2
	​

	​

)+g
E
	​

=g
I
	​

+g
E
	​

.

The null must have:

realized_successor_read_into_actor_credit=0
realized_successor_read_into_actor_gradient_scale=0
realized_successor_read_into_checkpoint_selection=0
realized_successor_read_into_result_selection=0
successor_counterfactual_calls=0

The physical trajectory may contain rewards and terminals, but the null actor-credit path may not construct or read G_(t+1).

Treatment interpretation

No global gradient-norm matching is applied.

This is deliberate: G48 tests deletion of the complete realized-successor channel package, including its contribution to gradient direction, global credit magnitude, and subsequent Adam moments.

Accordingly, a positive result may not be interpreted as proving that future information alone is necessary; it identifies the full registered channel package.

Paired training and optimizer exposure

Freeze:

both complete paired trajectories materialized before either update
branch-start actor/log_std bytes equal
actor Adam states empty, separate and identically configured
two channel losses materialized in each arm
two PPO passes
one actor Adam step per pass
no clipping
no minibatches
no optimizer reset
no baseline parameters
final-only checkpoints

The null performs two immediate-channel backward constructions so loss-count and channel-composition exposure match the reference.

Treatment-activation gates

Using only the reference arm’s pre-update data, require:

q
target
	​

=RMS(z
S
	​

−z
I
	​

)>10
−6
,

where z
I
	​

 and z
S
	​

 are the separately centered and scaled target rows.

Construct on that same reference state:

d
REF,credit
	​

=
2
1
	​

(g
I
	​

+g
S
	​

),
d
NULL,cf
	​

=
2
1
	​

(g
I
	​

+g
I
	​

).

When both are nonzero, require:

	​

∥d
REF,credit
	​

∥
2
	​

d
REF,credit
	​

	​

−
∥d
NULL,cf
	​

∥
2
	​

d
NULL,cf
	​

	​

	​

2
	​

>10
−6
.

Also require:

immediate gradient finite and live
successor gradient finite and live
every registered actor group finite in both channel rows
every actor group live in at least one reference channel

Required activation scope:

nonformal:
    at least one active pass

formal:
    at least one active pass
    in each accepted-anchor replicate 0|1|2

The actual duplicated-immediate arm supplies no activation evidence.

If the normalized successor and immediate rows are indistinguishable, or their resulting counterfactual actor directions are collinear throughout a required replicate, the package is operationally invalid rather than evidence for channel removability.

Target-behavior and access necessity

The reference arm must pass the complete inherited access contract, including the delayed event-window and process-segment gates. A reference failure has precedence over either successor-channel conclusion.

The source is identifying only when the delayed consequences measured by those gates remain accessible to the reference route.

Primary estimand

For paired final random-deterministic episodes:

Δ
succ
	​

=U
IMMEDIATE+SUCCESSOR
	​

−U
DUPLICATED IMMEDIATE
	​

.

Positive values favor the realized-successor channel package.

materiality_and_noninferiority_margin=0.05

Register the inherited component contrasts:

fixed deterministic utility, per capacity
random deterministic utility, per capacity
fixed stochastic utility, equal-capacity pooled
random stochastic utility, equal-capacity pooled
random event-window utility, per capacity
random process-segment utility, per capacity
random-minus-fixed transport, per capacity
minimum-replicate access

Use one confidence plan for every absolute and comparative quantity.

Claim ceilings

A duplicated-immediate sufficiency result may support only:

The complete realized-successor channel package is removable from the exact post-anchor G48-P0 route in favor of the registered duplicated-immediate null.

It may not establish that delayed information is universally useless or that ordinary TEAM-GAE1 is sufficient.

A reference advantage result may support only:

The realized-successor channel package supplies a source-local finite-budget access or material-utility advantage over the exact duplicated-immediate null.

It may not establish that future information alone, rather than the channel’s complete gradient and Adam consequences, is necessary.

Frozen first-match outcomes
1. INVALID_CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48

2. SOURCE_OR_REFERENCE_ACCESS_FAILURE_G48

3. DUPLICATED_IMMEDIATE_CREDIT_SUFFICIENT_G48

4. REALIZED_SUCCESSOR_CHANNEL_ADVANTAGE_G48

5. MIXED_UNDERPOWERED_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48

Exact predicates:

DUPLICATED_IMMEDIATE_CREDIT_SUFFICIENT_G48 requires both arms to pass the complete access contract and every reference-minus-null primary/component UCB to be <=0.05.

REALIZED_SUCCESSOR_CHANNEL_ADVANTAGE_G48 requires reference access and either confident null access failure or:

LCB
95
	​

(Δ
succ
	​

)>0.05

with every capacity-specific random-deterministic primary LCB strictly positive.

Every remaining operationally valid numerical pattern selects the mixed/underpowered branch.

No diagnostic may rescue or relabel an earlier branch.

Equality at an access or noninferiority boundary passes; material advantage remains strict.

Confidence and evidence inventory

Use one paired hierarchical whole-episode plan:

formal bootstrap seed=frozen before implementation
formal bootstrap resamples=10000
nonformal bootstrap resamples=250
confidence interval=95-percentile
episode exclusions=none
capacity weights=equal

Resample accepted-anchor replicate blocks, then complete episode IDs within replicate and capacity. Retain both arms and all fixed/random and deterministic/stochastic mates. Never resample agents, primitive steps, events, or channels independently.

Nonformal ceiling
replicates=1
branch_updates_per_arm=10
environments_per_update=8
PPO_passes=2

evaluation_cells=24
episodes_per_cell=6

training_transitions=7680
evaluation_transitions=6912
total_real_transitions<=14592

optimizer_steps<=40
wall_clock<=1200_seconds
Formal ceiling
replicates=3
branch_updates_per_arm=100
environments_per_update=8
PPO_passes=2

evaluation_cells=72
episodes_per_cell=48

training_transitions=230400
evaluation_transitions=165888
total_real_transitions<=396288

optimizer_steps<=1200
wall_clock<=28800_seconds

This reuses the inherited three-replicate G46-sized conclusion-bearing inventory; it preserves exact process/profile balance and stays within the project’s 20-minute nonformal and eight-hour formal limits.

Complexity
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)
Implementation-only degrees of freedom

Implementation-only:

file and class names
tensor-storage layout
vectorization and batching
serialization format
telemetry organization
proof-test file placement
launch-fixed worker count within deterministic resource bounds

Scientifically frozen:

source and provenance
two target laws
zero successor reads in the null
separate centering and independent scaling
literal equal-channel composition
optimizer and exposure
activation gates
estimands and thresholds
confidence unit
first-match order
evidence ceilings
claim ceilings

This disposition authorizes no implementation, nonformal run, formal run, Git operation, or browser transport.

中文简报
G47正式分支=
SHADOW_BASELINE_MODULE_EXACTLY_REMOVABLE_G47

科学裁决=
PROVED_EXACT_POST_ANCHOR_SHADOW_BASELINE_APPARATUS_REMOVABILITY_G47

G47科学迭代成本=0
已消耗结论性轮次=36
剩余结论性轮次=1
G47 最强结论

G47 不是统计 noninferiority，而是 exact structural proof。

它比较：

reference:
    保留 shadow baseline module、true-state input、loss、Adam 和 checkpoint fields

reduced:
    完全删除以上 baseline apparatus

正式结果同时满足：

static dependency certificate pass
optimizer factorization pass
D_G47=0
actor gradient bitwise equal
actor/log_std bitwise equal
actor Adam bitwise equal
pre-tanh/action/logprob equal
reward/roster/lifecycle trace equal
canonical final actor checkpoint equal

证据边界是：

H=48
一个共享 8×48 trajectory
384 real transitions
每臂 2 个 PPO passes
final-only checkpoints
无 bootstrap
无 statistical run

因此，exact post-G46 RAW route 可以删除：

shared two-output baseline module
baseline-only true-state input
baseline target-fitting losses
baseline parameters and Adam state
baseline diagnostics
baseline checkpoint/output schema
当前最小 route
COMMON_NATIVE6_FAST_ANCHOR
→ NATIVE6_G31_RAW_NORM_NO_BASELINE_MODULE

继续保留：

immediate target
realized-successor target
两通道 decomposition
separate centering
independent scaling
literal 0.5 equal mean
common entropy
不能误写为
fresh end-to-end training 不需要 baseline
所有 baseline 或 critic 都无用
六个 actor 字段可以逐个删除
所有历史输入都冗余
所有任务都 memoryless
其他 process/capacity/horizon 同样成立
UAV transport 已建立
reduced route 统计上更优

G47 是 post-anchor、exact implementation-specific structural reduction。

Portfolio 裁决

仍有一个结论性迭代，而且存在一个可执行、能改变算法结论的候选，因此：

VALID_RESULT_DISPOSITION=CONTINUE

其他方向继续保留：

broader process/horizon/capacity=live
fresh baseline-free anchor training=live
recurrence/EHC=parked behind hidden-information source
non-G33 UAV transport=parked behind identifiable source
skill lifetime/intrinsic reward=OUT_OF_SCOPE_FROZEN
G33=permanently frozen
当前调度动作
CONTINUOUS_ROSTER_NATIVE_SIX_G31_REALIZED_SUCCESSOR_CHANNEL_ATTRIBUTION_G48_DESIGN_ASSERTION_AUDIT

G48 将比较：

reference:
    immediate + realized-successor

null:
    immediate + duplicated immediate
    对 G_(t+1) 完全零读取

两臂继续使用：

baseline-free native-six graph
separate centering
independent RMS
literal 0.5 equal mean
相同 source、trajectory、Adam exposure 和 final-only checkpoints

G48 检验的是完整 realized-successor channel package，而不是把结果过度解释成“未来信息本身”的纯理论必要性。

本裁决不授权实现、Git、nonformal 或 formal compute。