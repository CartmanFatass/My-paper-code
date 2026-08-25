1. AUDIT_DISPOSITION
AUDIT_DISPOSITION=
IDENTIFIABLE_FRESH_FOLDED_SIX_COORDINATE_CS_G38_DESIGN

source_id=CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_P0
training_arms=FULL10_CS|FOLD6_CS
fresh_paired_training=true
training_graph_parameter_count_equal=true
folded_deployment_actor_coordinates=6
task_level_history_necessity_identifiable=false
native_six_coordinate_training_claim=false

A conclusion-bearing G38 comparison can be frozen, provided the actor graph is made explicitly foldable rather than treating the inherited G35 class as automatically foldable.

G37 left open the strongest practical explanation: its loss could reflect specialization of a ten-coordinate checkpoint to coherent multivariate inputs rather than useful history information. The exact G37 package closed mixed and selected fresh six-coordinate retraining rather than further factorized-donor evidence extension.

G38 therefore tests:

Whether a freshly trained no-carry actor that never receives varying lifecycle age, previous-action, or actor-time information can be converted exactly into a six-coordinate deployment actor while retaining the registered fixed/random, capacity-6/8/12 capability and remaining noninferior to a freshly trained full-information actor by 0.05.

The scientific ceiling is deliberately narrower:

A positive branch supports a freshly trained folded six-coordinate deployment actor in G38-P0.

A negative branch supports only a finite-budget advantage for access to the four varying actor fields under this graph, optimizer, source, and exposure.

Neither branch establishes global task memorylessness, individual field necessity, critic-time redundancy, G31-credit redundancy, or recurrence necessity.

The source already exposes current load and target mix, which directly support an access-level current-state policy; G35 also showed learned carry was not materially advantageous under matched fresh training.

2. EXACT_FULL10_FOLD6_GRAPH_AND_FOLDING_LAW
2.1 Actor inputs

For an active lifecycle i, partition the registered ten-coordinate observation as:

o
i,t
	​

=[x
i,t
	​

,z
i,t
	​

],

where:

x
i,t
	​

∈R
6

contains:

0:2  capability coordinates
2    anonymous presentation priority
3    current load
4    current target mix
5    log1p(active_count)

and:

z
i,t
	​

∈R
4

contains, in order:

6    normalized lifecycle age
7    normalized previous action 0
8    normalized previous action 1
9    normalized physical time

These are the exact registered G32 actor fields; the critic remains a separate six-coordinate true-current-state input.

Define:

c=(
2
1
	​

,
2
1
	​

,
2
1
	​

,
47
24
	​

).

The two training arms receive:

o
i,t
FULL
	​

=[x
i,t
	​

,z
i,t
	​

],
o
i,t
FOLD
	​

=[x
i,t
	​

,c].

The constant is written only for active rows. Inactive actor rows remain exactly zero.

For FOLD6_CS, the actor-input construction may read source coordinates 0:6, the active mask, and the current active count. It may not materialize, validate, copy, hash, or otherwise inspect the source values in coordinates 6:10 during training or evaluation.

The environment still maintains its real age and previous-action state, and the centralized critic still receives its unchanged true state. The intervention concerns actor information only.

2.2 Exact common training graph

Both arms use one common serialized ten-coordinate, no-carry training graph. The nonserialized input_mode is the sole arm treatment.

For each active member:

q
i,t
	​

=A
m
	​

o
i,t
	​

+b
m
	​

,A
m
	​

∈R
32×10
,
e
i,t
	​

=M
tail
	​

(q
i,t
	​

),

where M
tail
	​

 is the remaining shared G35 member-encoder graph and consumes no raw observation coordinate.

The active-set context is:

g
t
	​

=C
	​

	​

j∈A
t
	​

∑
	​

e
j,t
	​

,log(1+∣A
t
	​

∣)
	​

	​

.

For the registered anonymous routing order and active-fraction prefix p
i,t
	​

:

u
i,t
	​

=GRUCell([e
i,t
	​

,g
t
	​

,p
i,t
	​

],e
i,t
	​

).

The second GRU argument is the current member encoding, not stored cross-step state. Both arms are therefore CS actors and carry exactly zero learned hidden state.

The pre-tanh mean is:

μ
i,t
	​

=H([u
i,t
	​

,p
i,t
	​

])+A
r
	​

o
i,t
	​

+b
r
	​

,A
r
	​

∈R
2×10
.

The tanh-Gaussian action distribution, shared log standard deviation, anonymous routing, active-set aggregation, action prefix, action likelihood, critic, immediate baseline, successor baseline, and G31 update remain identical.

The G35 realization already exposes the common member encoder, context encoder, gated actor cell, action head, and zero-initialized current-observation readout, while its CS mode discards learned carry. Its existing gradient audit treats the member encoder and current readout as distinct trainable groups.

2.3 Complete raw-input-use inventory

The G38 graph permits exactly two actor paths from the raw ten-coordinate observation:

the affine member-input map A
m
	​

o+b
m
	​

;

the affine current readout A
r
	​

o+b
r
	​

.

No other module may directly consume o or any slice of o. In particular, raw coordinates 6:10 may not enter:

a LayerNorm or other cross-coordinate normalization;

a multiplicative gate;

a residual concatenation downstream of the first member affine;

the context encoder;

the action head independently of A
r
	​

;

the centralized critic;

the immediate or successor baseline;

routing or prefix construction.

Both arms use this exact graph. This explicit raw-input inventory prevents foldability from becoming an unexamined implementation assumption.

If a proposed realization contains any third raw-input path, or applies a non-affine transformation before the two named affine maps, it is nonconforming and must stop before training. It may not approximate the fold.

2.4 Training parameter equality

Before folding:

state_dict_key_set_FULL10 == state_dict_key_set_FOLD6
state_dict_shape_map_FULL10 == state_dict_shape_map_FOLD6
trainable_mask_FULL10 == trainable_mask_FOLD6
trainable_parameter_count_FULL10 == trainable_parameter_count_FOLD6
initial_state_bytes_FULL10 == initial_state_bytes_FOLD6

Both ten-coordinate input matrices are fully trainable in both arms. No constant-coordinate column is frozen or replaced by a dummy parameter.

The arm labels and input modes are nontrainable metadata and absent from the state dictionary.

At initialization, feeding the same clamped ten-coordinate tensor and the same action noise to both arms must produce equal:

pre_tanh_mean
action
token_log_probability
value

within 1e-7. This proves that the graph and parameters are identical before the intended input treatment is applied.

G35 already established the relevant parameter-key, shape, trainable-mask, count, and byte-identical initialization pattern for matched arms.

2.5 Live gradient path for the constant coordinates

On the forced first paired training batch, using the actual inherited fast and return-to-go objectives and before any optimizer step, require all existing G35 trainable groups to retain a finite live gradient.

Additionally, for each constant coordinate k∈{6,7,8,9}, require:

max(
	​

∇
A
m
	​

[:,k]
	​

L
fast
	​

	​

,
	​

∇
A
m
	​

[:,k]
	​

L
rtg
	​

	​

)>10
−12
,

and:

max(
	​

∇
A
r
	​

[:,k]
	​

L
fast
	​

	​

,
	​

∇
A
r
	​

[:,k]
	​

L
rtg
	​

	​

)>10
−12
.

All gradient values must be finite.

Because every component of c is nonzero, a live downstream path gives each constant column a live training path. The four columns need not be separately statistically identifiable: only their combined constant affine contribution matters for exact folding.

2.6 Exact fold

After training the final and zero FOLD6_CS checkpoints, split:

A
m
	​

=[A
m
x
	​

A
m
c
	​

],

where:

A
m
x
	​

∈R
32×6
,A
m
c
	​

∈R
32×4
.

Define the folded member-input map:

A
m
	​

=A
m
x
	​

,
b
m
	​

=b
m
	​

+A
m
c
	​

c.

Similarly split:

A
r
	​

=[A
r
x
	​

A
r
c
	​

],

and define:

A
r
	​

=A
r
x
	​

,
b
r
	​

=b
r
	​

+A
r
c
	​

c.

All remaining weights, biases, buffers, log standard deviation, context modules, GRU cell, action head, critic, and credit modules are copied unchanged.

Thus, for every active six-coordinate input x:

A
m
	​

[x,c]+b
m
	​

=
A
m
	​

x+
b
m
	​

,
A
r
	​

[x,c]+b
r
	​

=
A
r
	​

x+
b
r
	​

.

Since all later modules receive equal values, the complete actor function is preserved.

The folded deployment actor removes exactly:

4×32+4×2=136

actor weights and changes its per-member observation dimension from ten to six. The centralized critic remains unchanged.

No donor bank, donor snapshot, proxy tape, source-history reader, or internally generated four-coordinate filler remains in the folded deployment path.

2.7 Fold-equivalence gate

No optimizer step may occur after folding.

For every conclusion-bearing FOLD6_CS zero and final evaluation cell, execute the pre-fold constant-input model and folded six-input model in lockstep on the same source states and action noise while advancing only one environment trajectory.

Require:

Quantity	Equality rule
log_std and critic tensors	bitwise equal
value output	bitwise equal
active pre-tanh means	maximum absolute error <=1e-6
active deterministic/stochastic actions	maximum absolute error <=1e-6
active prefix-action sums	maximum absolute error <=1e-6
active token log probabilities	maximum absolute error <=1e-5
inactive actions and likelihoods	exact zero
reward trace	maximum absolute error <=1e-6
utility, event-window, and segment summaries	absolute error <=1e-6
roster sizes, membership edits, and lifecycle validity	exact equality

Any failure is operational invalidity. The comparison may not proceed using the pre-fold model as a substitute for the required six-coordinate deployment model.

3. PAIRED_TRAINING_AND_SEED_OWNERSHIP
3.1 Formal seed block

Freeze:

model_initialization_seed_base=10381000
training_ledger_seed_base=10382000
training_action_seed_base=10383000
evaluation_base_ledger_seed_base=10384000
evaluation_process_seed_base=10385000
evaluation_action_seed_base=10386000
initial_gradient_probe_seed_base=10387000
bootstrap_seed=10388038
nonformal_seed_offset=900000

For formal replicate r∈{0,1,2}, add r exactly once to every nonbootstrap base.

For the bounded nonformal exercise, add 900000 to every seed, including the bootstrap seed.

3.2 Shared versus arm-owned randomness

Within each replicate, both arms share:

byte-identical initial parameters;

G32 training episode identities and physical ledgers;

G34 fixed/random evaluation episode identities and process signatures;

member-owned training action-noise tensors;

member-owned evaluation action-noise tensors;

profile and event-order assignments;

bootstrap resampling indices.

Each arm owns a separate Adam optimizer state initialized from the same empty state.

No arm owns a source, process, or action-noise stream unavailable to the other arm.

The constant c is deterministic and consumes no RNG. Its construction reads no lifecycle age, previous action, physical time, event type, reward, model output, or action noise.

3.3 Training exposure

Per arm and replicate:

training_capacity=8
fast_updates=100
return_to_go_updates=100
environments_per_update=8
episode_length=48
ppo_passes=2
gamma=0.99
learning_rate=1e-3
initial_log_std=-1.0
optimizer=Adam(beta1=0.9,beta2=0.999,eps=1e-8,weight_decay=0)
minibatches=none
checkpoint_selection=final_only
episode_exclusions=none

This retains the G35 exposure that previously established common access rather than changing the finite-budget question through a smaller training contract. G35 used 100 fast updates, 100 return-to-go updates, eight environments, two PPO passes, and final-only checkpoints.

At every update:

materialize both arms’ complete trajectories from the paired source ledgers and noise;

finish collection for both arms;

update either arm only after both trajectories exist;

preserve equal fast-actor, return-to-go-actor, and critic optimizer-step counts.

G35’s paired implementation already materializes both arm trajectories before either update.

3.4 FOLD6 input independence throughout training

For every FOLD6_CS actor call in collection, replay, gradient audit, PPO, final evaluation, and zero-checkpoint evaluation:

allocate the actor tensor from source coordinates 0:6;

write c directly into active rows 6:10;

leave inactive rows zero;

never materialize source coordinates 6:10.

Required counters over the complete run are:

actual_age_read_count=0
actual_previous_action_read_count=0
actual_actor_time_read_count=0
donor_or_proxy_read_count=0

The critic remains unchanged and may read its registered true-current-state fields, including true normalized time.

4. ESTIMAND_CLAIM_CEILING_AND_GATES
4.1 Relevant policy classes

Let:

Π
10
	​


be the freshly trained no-carry policies produced by FULL10_CS, and:

Π
6,c
	​


be the policies produced by the clamped training graph and then exactly folded into six-coordinate deployment actors.

Because current load and target mix directly define an access-level action, Π
6,c
	​

 contains an access-capable policy. The source therefore cannot identify the proposition that task-level optimal control intrinsically requires the four history fields.

G38 identifies only:

empirical architectural-reduction sufficiency under the frozen budget; or

a finite-budget learning/access advantage for the varying four-field bundle.

4.2 Per-episode quantities

Retain the G34/G35 trace definitions.

For episode e:

U
e
	​

=
48
1
	​

t=0
∑
47
	​

r
e,t
	​

.

For random event times t
1
	​

,…,t
4
	​

:

E
e
	​

=
j
min
	​

4
1
	​

t=t
j
	​

∑
t
j
	​

+3
	​

r
e,t
	​

.

For the five event-delimited process segments S
j
	​

:

P
e
	​

=
j
min
	​

∣S
j
	​

∣
1
	​

t∈S
j
	​

∑
	​

r
e,t
	​

.

All summaries must be recomputed from serialized 48-step reward and actual roster-size traces.

4.3 Arm-level access

For arm a∈{FULL10,FOLD6}, define:

G
a
	​

=U
a,final,random,det
−U
a,zero,random,det
,

pooled with equal capacity weight.

ACCESS_PASS(a) requires all of the following.

Fixed process

For every capacity C∈{6,8,12}:

LCB
95
	​

(U
C
a,final,fixed,det
	​

)≥0.90.

Pooled fixed stochastic:

LCB
95
	​

(U
a,final,fixed,stoch
)≥0.80.

Minimum fixed deterministic replicate mean:

≥0.85.
Random process

For every capacity:

LCB
95
	​

(U
C
a,final,random,det
	​

)≥0.90,
LCB
95
	​

(E
C
a,final,random,det
	​

)≥0.85,
LCB
95
	​

(P
C
a,final,random,det
	​

)≥0.85,
LCB
95
	​

(U
C
a,final,random,det
	​

−U
C
a,final,fixed,det
	​

)≥−0.05.

Pooled random stochastic:

LCB
95
	​

(U
a,final,random,stoch
)≥0.80.

Minimum random deterministic replicate mean:

≥0.85.

Learned gain:

LCB
95
	​

(G
a
	​

)>0.

Equality passes at every non-strict floor. Learned gain remains strict.

Operational access additionally requires:

source-law validity;

live-gradient audit;

exact paired exposure;

finite updates;

replay error <=1e-6;

zero carried hidden state;

exact lifecycle ownership;

zero evaluation optimizer steps;

final-only checkpoint selection;

FOLD6 fold-equivalence closure.

4.4 Confident access failure

ACCESS_CONFIDENT_FAIL(a) holds if any corresponding:

deterministic, stochastic, event-window, or segment UCB is below its floor;

process-transport UCB is below -0.05;

learned-gain UCB is at or below zero;

registered minimum replicate mean is below 0.85.

Every other nonpassing pattern is access-underpowered.

4.5 Primary information estimand

For capacity C, paired replicate r, and paired random deterministic episode e:

Δ
info,C,r,e
	​

=U
C,r,e
FULL10,final,random,det
	​

−U
C,r,e
FOLD6,final,random,det
	​

.

The pooled primary estimand is:

Δ
info
	​

=
3
1
	​

C∈{6,8,12}
∑
	​

E
r,e
	​

[Δ
info,C,r,e
	​

]
	​


Positive values favor access to the four varying fields.

Freeze:

δ
info
	​

=0.05.
4.6 Six-coordinate noninferiority

Define analogous FULL10 − FOLD6 paired differences for:

fixed deterministic utility, per capacity;

random deterministic utility, per capacity;

fixed stochastic utility, equal-capacity pooled;

random stochastic utility, equal-capacity pooled;

random event-window utility, per capacity;

random process-segment utility, per capacity.

SIX_COORDINATE_NONINFERIOR requires:

UCB
95
	​

(Δ
info
	​

)≤0.05,

and every registered component UCB above is also at most 0.05.

Equality at 0.05 passes.

4.7 Six-coordinate reduction claim

SIX_COORDINATE_ARCHITECTURAL_REDUCTION_SUFFICIENT_G38 requires:

ACCESS_PASS(FOLD6)=true
SIX_COORDINATE_NONINFERIOR=true
FOLD_EQUIVALENCE_PASS=true

A pass supports:

A freshly trained constant-input graph can be converted into the exact folded six-coordinate actor and retain the registered capability within G38-P0.

It does not establish:

that a natively six-coordinate, lower-parameter graph has identical optimization behavior;

that all tasks are memoryless;

that the critic can drop true time;

that any one of the four removed fields is individually redundant;

that constants other than c are equivalent;

transport outside H=48, capacities 6/8/12, or the G32/G34 process family.

4.8 Full-information finite-budget advantage

Define:

MATERIAL_INFO_ADVANTAGE⟺LCB
95
	​

(Δ
info
	​

)>0.05

and, for every capacity:

LCB
95
	​

(Δ
info,C
	​

)>0.

FULL_INFORMATION_FINITE_BUDGET_ADVANTAGE_G38 requires:

ACCESS_PASS(FULL10)=true
and either:
    ACCESS_CONFIDENT_FAIL(FOLD6)=true
or:
    MATERIAL_INFO_ADVANTAGE=true

The result must report which subpredicate fired.

This branch supports only that varying access to the four-field bundle provides a finite-budget capability or material utility advantage under G38-P0. It cannot establish task-level necessity. It also cannot distinguish useful semantic history from optimization conditioning supplied by varying inputs.

4.9 Non-rescuing diagnostics

Report, but do not branch on:

norms of trained weights on the four removable columns;

the size of the folded bias adjustment;

per-coordinate gradient norms after the initial audit;

training curves;

action-distribution displacement;

performance stratified by event type, order, active count, or capacity beyond registered gates;

comparison with historical G35/G36/G37 checkpoints.

No diagnostic may rescue or relabel a primary branch.

5. PAIRING_CONFIDENCE_AND_EVIDENCE
5.1 Source validation without redundant model cells

The G32/G34 source family is unchanged. G38 therefore introduces no new constructive model cell.

SOURCE_VALID requires:

exact G32 capacity-8 fixed training law;

exact G34-P0 fixed/random capacity-6/8/12 evaluation law;

valid nonempty active rosters and lifecycle transitions;

unique registered process signatures;

the registered constructive load/mix action yielding exact source access for every generated ledger;

no source, reward, observation, critic, or process-law change.

The constructive identity may be verified directly from the source equations and generated ledgers; it contributes no additional environment trajectory to the conclusion-bearing inventory.

The registered G34 process uses one each of L/R/J/T, held-out event times, three legal orders, and paired fixed/random base ledgers.

5.2 Evaluation-cell inventory

For each arm, replicate, and capacity, evaluate exactly:

ZERO_RANDOM_DET
FINAL_FIXED_DET
FINAL_FIXED_STOCH
FINAL_RANDOM_DET
FINAL_RANDOM_STOCH

Thus:

arms=2
cells_per_arm_capacity=5
cells_per_replicate=30
formal_replicates=3
formal_total_cells=90
evaluation_episodes_per_cell=128

For FOLD6_CS, the zero and final cells are run through the folded six-coordinate model. The corresponding pre-fold constant-input model is evaluated in lockstep only for the fold-equivalence gate and does not create a second environment trajectory or another scientific cell.

5.3 Formal training and evaluation inventory

Training transitions:

2×3×200×8×48=460,800.

Evaluation transitions:

3×30×128×48=552,960.

Total real transitions:

1,013,760
	​


Formal optimizer steps:

2×3(100×2+2×100×2)=3,600.

This is smaller than the G35 ceiling because the unchanged constructive source is validated directly rather than rerun as three extra model cells per replicate.

5.4 Paired unit

The conclusion-bearing paired unit is:

(replicate, capacity, process, action_mode, episode_id)

The paired training unit is:

(replicate, update, environment_slot, episode_id)

Within each unit, preserve both arms, zero/final checkpoints, fixed/random mates, deterministic/stochastic mates, source ledger, and action noise.

5.5 Confidence construction

Freeze:

paired_training_replicates=3
capacities=6|8|12
evaluation_episodes_per_cell=128
bootstrap_resamples=10000
bootstrap_seed=10388038
confidence_interval=95_percent_percentile
episode_exclusions=none

Generate one plan and reuse it for every absolute and paired estimand:

resample the three paired training-replicate blocks with replacement;

within each selected replicate and capacity, resample all 128 whole episode IDs;

retain all arm, checkpoint, process, and action-mode rows belonging to the episode;

never independently resample members, time steps, events, arms, fixed/random mates, zero/final mates, or pre/post-fold paths.

Pooled quantities weight capacities 6, 8, and 12 equally.

6. WITNESSES_AND_IDENTIFIABILITY
6.1 Exact fold witness

For arbitrary trained matrices and any active six-coordinate input x:

A[x,c]+b=A
x
	​

x+(b+A
c
	​

c).

Applying this identity to both permitted raw-input affines gives equal member-encoder preactivations and equal current-readout outputs. Since all later modules and the critic are unchanged, the complete policy distribution and value are equal up to the frozen floating-point tolerance.

A raw-input LayerNorm, multiplicative interaction, attention score, or unenumerated skip path is a graph/fold failure witness and reaches operational invalidity before training.

6.2 Six-coordinate access witness

Set the current readout to ignore every coordinate except current load and target mix and produce:

a
(0)
=tanh(2L−1),a
(1)
=tanh(2M−1).

This policy uses only retained coordinates 3 and 4. Its registered minimum utility over the complete load/mix support is approximately 0.94048, above the 0.90 access floor.

Therefore FOLD6 cannot fail because the six-coordinate class lacks an access-capable policy.

6.3 Source/common-access failure witness

If the source constructive identity is invalid, or both freshly trained arms confidently fail the common access predicates, the package cannot distinguish information value from general source or training failure.

Example:

FULL10 random utility UCB < 0.90
FOLD6 random utility UCB < 0.90

for the same capacity.

6.4 Six-coordinate sufficiency witness

For example:

ACCESS_PASS(FOLD6)=true
Delta_info CI95=[-0.01,0.01,0.03]
all component UCBs<=0.05
fold equivalence passes

This selects the six-coordinate reduction branch even if FULL10 is numerically slightly higher.

6.5 Full-information advantage witness

For example:

ACCESS_PASS(FULL10)=true
Delta_info CI95=[0.06,0.07,0.08]
each capacity-specific random-deterministic LCB>0

This supports a material finite-budget advantage for varying history fields.

A second valid witness is:

ACCESS_PASS(FULL10)=true
ACCESS_CONFIDENT_FAIL(FOLD6)=true

which establishes an access-level finite-budget advantage even if the pooled difference is not precisely above 0.05.

6.6 Mixed witness

Examples:

ACCESS_PASS(FOLD6)=true
Delta_info CI95=[0.03,0.07]

or:

FOLD6 capacity-12 deterministic utility CI95 crosses 0.90
FULL10 accesses
Delta_info does not have LCB>0.05

Neither establishes noninferiority nor a material full-information advantage.

6.7 Identifiability ceiling

The FOLD6 training graph contains redundant constant columns and biases. A FULL10 advantage may therefore reflect:

useful varying information;

improved optimization conditioning;

reduced collinearity relative to the constant-input arm;

finite-budget sensitivity.

It may not be called task-level history necessity.

Conversely, a FOLD6 pass supports a six-coordinate deployment actor after exact folding. It does not prove that a natively six-coordinate, lower-parameter actor would train identically without the overparameterized constant-coordinate training graph.

This distinction separates G38 from G37’s post-training joint-distribution intervention.

7. FIRST_MATCH_TRUTH_TABLE

Define:

OPERATIONAL_VALID
Exact graph inventory, parameter matching, no-history-read path, live gradients, finite updates, replay, lifecycle, checkpoints, fold conversion, fold-equivalence, traces, RNG, inventory, and authority invariants pass.

SOURCE_VALID
Exact G32/G34 source laws, constructive identity, process support, denominators, and lifecycle predicates pass.

FULL_ACCESS_PASS, FOLD_ACCESS_PASS
Section 4.3.

FULL_ACCESS_CONFIDENT_FAIL, FOLD_ACCESS_CONFIDENT_FAIL
Section 4.4.

SIX_COORDINATE_NONINFERIOR
Section 4.6.

MATERIAL_INFO_ADVANTAGE
Section 4.8.

Priority	Terminal branch	Exact predicate	Smallest scientific update
1	INVALID_CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38	OPERATIONAL_VALID=false	No scientific update. Repair only the exact operational defect under the unchanged contract. Non-affine or incomplete folding belongs here and cannot be approximated.
2	SOURCE_OR_COMMON_ACCESS_FAILURE_G38	Operationally valid and either SOURCE_VALID=false, or both FULL_ACCESS_CONFIDENT_FAIL=true and FOLD_ACCESS_CONFIDENT_FAIL=true	Close this exact source/comparator package without selecting information value or six-coordinate sufficiency.
3	SIX_COORDINATE_ARCHITECTURAL_REDUCTION_SUFFICIENT_G38	Source valid, FOLD_ACCESS_PASS=true, SIX_COORDINATE_NONINFERIOR=true, and fold equivalence passes	Support the exact fresh-trained folded six-coordinate deployment actor in G38-P0. Do not infer native-six-input training equivalence or global history redundancy.
4	FULL_INFORMATION_FINITE_BUDGET_ADVANTAGE_G38	Source valid, FULL_ACCESS_PASS=true, and either FOLD_ACCESS_CONFIDENT_FAIL=true or MATERIAL_INFO_ADVANTAGE=true	Support a finite-budget capability or material utility advantage for varying actor history fields. Report which subpredicate fired. Do not claim task-level necessity.
5	MIXED_UNDERPOWERED_SIX_COORDINATE_G38	Every remaining valid pattern	Preserve both explanations and close G38-P0 without seed, budget, constant, margin, architecture, source, or evidence-volume rescue.

Branch evaluation stops at the first match.

Equality semantics:

absolute access-floor equality             = pass
random-minus-fixed LCB = -0.05             = pass
learned-gain LCB > 0                        = strict
UCB(FULL10-FOLD6) = 0.05                    = noninferior pass
LCB(primary FULL10-FOLD6) > 0.05            = material-advantage pass
fold error = stated tolerance               = fold-equivalence pass

No descriptive diagnostic may rescue or relabel an earlier branch.

8. EVIDENCE_COMPLEXITY_AND_AUTHORITY
8.1 Search complexity
design_audit_compute=0
H=48
K_search=0
hypothetical_trajectory_count=0
hypothetical_transitions=0
nested_rollout=false
replanning=false
per_episode_complexity=O(H)

No candidate search, rollout oracle, tree, beam, or simulated counterfactual is present.

This is within the user-authorized hard boundary of fixed K_search, at most 16H hypothetical transitions, a 20-minute nonformal cap, and an eight-hour formal cap.

8.2 Bounded nonformal preflight

Freeze:

replicates=1
arms=2
fast_updates_per_arm=10
return_to_go_updates_per_arm=10
environments_per_update=8
ppo_passes=2
evaluation_cells=30
evaluation_episodes_per_cell=8
bootstrap_resamples=250

Training transitions:

2×20×8×48=15,360.

Evaluation transitions:

30×8×48=11,520.

Total:

26,880
	​


Optimizer steps:

2(10×2+2×10×2)=120.

The nonformal package must validate:

exact graph-input inventory;

byte-identical paired initialization;

live gradients for every registered group and each constant column;

no-read constant-input construction;

paired collection before updates;

exact exposure;

zero/final checkpoint closure;

zero hidden carry;

fold conversion and lockstep equivalence;

exact 30-cell inventory;

source and trace validity;

branch witnesses and equality semantics.

The complete nonformal train/evaluate/analyze package must finish within 1,200 seconds.

8.3 Formal inventory
formal_replicates=3
formal_training_transitions=460800
formal_evaluation_cells=90
formal_evaluation_episodes=11520
formal_evaluation_transitions=552960
formal_total_real_transitions=1013760
formal_optimizer_steps=3600
bootstrap_resamples=10000

This is below the inherited ceilings of 1,069,056 real transitions and 3,600 optimizer steps.

8.4 Formal wall-clock projection

The preflight records separately:

T_train_nf
T_evaluate_nf
T_analyze_nf

Freeze:

T
projected,formal
	​

=1.25(30T
train,nf
	​

+48T
evaluate,nf
	​

+40T
analyze,nf
	​

).

Formal work is admissible only if:

T
projected,formal
	​

≤28,800 seconds.

The nonformal total must also be at most 1,200 seconds.

A bound failure returns:

NON_EXECUTABLE_EVIDENCE_DESIGN

and consumes no scientific iteration.

8.5 Authority sequence

Before formal training:

PM technically accepts one exact implementation of this contract.

The implementation and a commit-bound code-science index are pushed.

External Pro returns ALIGNED from the G38 code-science alignment audit.

One exact same-source-commit bounded nonformal preflight validates all three artifacts and the formal projection.

The formal runner requires:

CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_FORMAL_AUTHORIZATION_V1

Formal artifacts bind the aligned source commit and the preflight training, evaluation, and analysis digests.

This response supplies no implementation or compute authority.

9. CODE_SCIENCE_MAPPING
Scientific field	Existing surface or minimal G38 symbol	Binding correspondence
Common no-carry policy	G35MatchedStateCarryPolicy with carry_mode=CS	Preserve context, routing, GRU, action head, distribution, critic, and zero carried state.
Explicit foldable actor graph	G38FoldableMatchedCSPolicy	Expose exactly two raw-observation affine entries: member_input: Linear(10,32) and current_readout: Linear(10,2); no other raw-input path.
FULL10 actor input	build_g38_full10_actor_input	Use exact active source coordinates 0:10; inactive rows zero.
FOLD6 training input	build_g38_constant_actor_input	Read only source 0:6; write c into active 6:10; inactive rows zero; all actual-history-read counters remain zero.
Paired initialization	G35 make_paired_models pattern plus G38 arm metadata	Exact keys, shapes, trainable masks, parameter counts, and initial bytes.
Gradient audit	G35 g35_initial_gradient_audit plus g38_constant_column_gradient_audit	Use actual objectives; every common group and every removable input column has a finite live path before an optimizer step.
Exact folding	fold_g38_constant_actor_checkpoint	Apply the two frozen bias transformations, remove 136 actor weights, preserve all other tensors, and bind the folded checkpoint to its pre-fold source digest.
Fold verification	verify_g38_fold_equivalence	Lockstep pre-fold/folded forward calls and one environment trajectory under the frozen tolerances.
Paired training	G35 paired-training runner surface	Collect both trajectories before updating either arm; preserve fresh seeds, source, action noise, optimizer, and exposure.
Training source	G32 fixed capacity-8 source	Exact profiles, reward, lifecycle semantics, and episode/member-owned streams.
Evaluation source	G35/G34 process-ledger surface	Exact fixed/random capacity-6/8/12 laws, episode identities, event support, and action-noise pairing.
Trace metrics	G34/G35 trace-recomputation surface	Recompute utility, event-window, segment, transport, gain, and roster validity from 48-step traces.
Confidence	g38_bootstrap_plan	One paired replicate/whole-episode plan with seed 10388038, reused across every registered quantity.
First-match result	select_g38_result_branch	Exact priority and inclusive/strict comparisons in Section 7.
Preflight and authority	G35 preflight pattern plus G38 inventory	Bind 26,880 nonformal and 1,013,760 formal transitions, 3,600 optimizer steps, three stage times, digests, source commit, and dedicated token.
Scientific and frozen

raw-input-use inventory;

common training graph;

constant vector and active-row semantics;

no-history-read rule;

fold equations and tolerances;

seed block;

training/evaluation exposure;

source and cell inventory;

access and gain gates;

primary estimand and 0.05 margin;

confidence unit;

first-match order;

transition and wall-clock bounds.

Implementation-only

file and class names beyond the minimal symbols;

tensor storage;

vectorization;

serialization layout;

batching;

telemetry organization;

deterministic kernel choice, provided fold tolerances pass;

proof-sized test-file organization.

Scientifically nonconforming realizations include:

freezing or deleting the four input columns during training;

giving the two arms different widths or dummy parameters;

reading actual FOLD6 history values before clamping;

applying c to inactive rows;

leaving a donor or filler generator in the folded deployment actor;

folding only the current readout but not the member-input affine;

retaining an unenumerated raw-observation path;

approximating a nonlinear input path;

evaluating the pre-fold constant model instead of the folded six-coordinate model;

changing the critic, credit, source, action distribution, exposure, or checkpoint rule.

10. ONE_NEXT_BOUNDARY
next_boundary=
CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_CODE_SCIENCE_ALIGNMENT_AUDIT

That boundary becomes eligible only after PM has technically accepted one exact pushed realization.

Its sole scientific question is:

Does the accepted implementation instantiate the exact two-affine-entry matched training graph, active-only constant-input treatment, byte-identical paired initialization, live removable-column gradients, paired G32/G34 training and evaluation exposure, exact two-bias fold, true six-coordinate folded checkpoint, lockstep fold equivalence, registered access and FULL10−FOLD6 estimands, whole-episode confidence plan, smaller 90-cell formal inventory, and frozen first-match semantics without creating another information, capacity, optimization, checkpoint, or evidence route?

It is a read-only conformance diff. It may not alter the constant, graph, source, fold, tolerance, seed, margin, evidence volume, confidence unit, or branch order.

This disposition authorizes no implementation, Git operation, nonformal exercise, formal training, monitoring, or successor child.

11. 中文简报

本轮裁决是：

IDENTIFIABLE_FRESH_FOLDED_SIX_COORDINATE_CS_G38_DESIGN

G38 可以形成有效比较，但不能简单假设现有十维模型“天然可折叠”。本轮将 actor 图明确限制为：原始十维 observation 只进入两个仿射入口。

1. member encoder 的第一层 Linear(10,32)
2. current readout 的 Linear(10,2)

其他 context、GRU、action head、critic 和 credit 模块不得再次直接读取原始 observation。

两个训练 arm

FULL10_CS 使用真实十维 actor 输入：

capability(2)
priority
load
target mix
log active count
age
previous action(2)
time

FOLD6_CS 只读取前六维，并在 active row 内部写入冻结常量：

c=(1/2,1/2,1/2,24/47)

inactive row 仍为全零。

两个 arm 在训练期间：

使用同一十维图；

参数 key、shape、trainable mask、参数量完全相同；

初始参数 byte-identical；

都不携带 learned hidden；

使用相同 critic、G31 credit、source、action noise、transition 和 optimizer exposure；

唯一区别是四个字段是真实变化值还是冻结常量。

FOLD6_CS 在整个训练与评价期间都不得读取真实 age、previous action 或 actor time。

精确 folding

训练完成后，将两个仿射矩阵拆成前六列与后四列：

W=[W
x
	​

,W
c
	​

].

然后：

W
fold
	​

=W
x
	​

,b
fold
	​

=b+W
c
	​

c.

该变换分别应用于：

Linear(10,32)；

Linear(10,2)。

最终删除：

4×32+4×2=136

个 actor weights，得到真正只消费六个 per-member actor coordinates 的部署模型。部署中不保留 donor、proxy tape 或内部四维 filler。

需要强调：

G38 若通过，支持的是“经过十维常量参数化训练并精确折叠后的六维部署 actor”，而不是“原生低参数六维模型必然同样容易训练”。

训练与证据规模

正式训练继续使用已验证能够形成 common access 的 G35 预算：

3 paired replicates
2 arms
100 fast updates
100 return-to-go updates
8 envs/update
2 PPO passes

正式评价不再重复 unchanged constructive cells，只保留每个 arm/capacity 的五个必要 cell：

ZERO_RANDOM_DET
FINAL_FIXED_DET
FINAL_FIXED_STOCH
FINAL_RANDOM_DET
FINAL_RANDOM_STOCH

正式总量：

training transitions   460800
evaluation transitions 552960
total transitions      1013760
optimizer steps        3600
evaluation cells       90

小于此前上限 1,069,056。

主估计量
Δ
info
	​

=U
FULL10
	​

−U
FOLD6
	​

.

margin 固定为：

0.05.

若 FOLD6 达到全部 fixed/random、deterministic/stochastic、event-window、segment、transport、learned-gain 与稳定性门槛，并且所有 FULL10−FOLD6 UCB 均不超过 0.05，结果是：

SIX_COORDINATE_ARCHITECTURAL_REDUCTION_SUFFICIENT_G38

若 FULL10 达到 access，且 FOLD6 confident fail，或者 pooled 差值 LCB 严格大于 0.05 且每个 capacity 的差值方向均为正，结果是：

FULL_INFORMATION_FINITE_BUDGET_ADVANTAGE_G38

即使 FULL10 胜出，也只能说明四个变化字段在该预算和图下提供有限预算优势，不能写成任务理论上必须历史信息。

完整正式分支为：

INVALID_CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38
SOURCE_OR_COMMON_ACCESS_FAILURE_G38
SIX_COORDINATE_ARCHITECTURAL_REDUCTION_SUFFICIENT_G38
FULL_INFORMATION_FINITE_BUDGET_ADVANTAGE_G38
MIXED_UNDERPOWERED_SIX_COORDINATE_G38
当前研究位置
阶段	结论
G32	支持 capacity 6/8/12
G34	支持有界随机 roster process
G35	learned actor carry 不 load-bearing
G36	真实 history sensors 可由 coherent donor 替代
G37	完整 factorization 有方向性损失，但 mixed
G38	冻结 fresh training 后的真正六维 actor 检验
剩余正式迭代	9

下一边界是：

CONTINUOUS_ROSTER_SIX_COORDINATE_CS_G38_CODE_SCIENCE_ALIGNMENT_AUDIT

G33 及其衍生线继续保持用户放弃、禁止复活。本裁决不授权代码、Git、非正式或正式计算。
