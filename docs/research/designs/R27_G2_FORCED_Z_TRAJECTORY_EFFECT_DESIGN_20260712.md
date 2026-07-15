# R27-G2 Forced-z Trajectory and Effect Intervention

Status: controller-frozen design only; implementation and launch are not
authorized by this document.

Date: 2026-07-12

Controller disposition: `ACCEPTED_WITH_MODIFICATIONS_AS_DESIGN_ONLY`

## 1. Question and claim boundary

The only causal edge under test is:

```text
individual skill z_i -> persistent executable behavior
```

R27-G1 established immediate `z_i`-conditioned action-distribution
sensitivity in the frozen R25 arm0 low actor. R26-G1a did not find a passing
held-out observational behavior-window family. R27-G2 therefore asks whether
an isolated focal-agent label intervention remains behaviorally controlling
over time, rather than whether an initially different action is merely
amplified by closed-loop dynamics.

A positive R27-G2 result may support only this statement:

> In frozen R25 arm0 checkpoints, repeatedly holding one focal agent's label
> through the live recurrent executor causes label-consistent action-process
> differences for up to 40 primitive steps, relative to a matched 10-step
> pulse and exact replay controls; a separate Gate C may additionally support
> a benchmark-local focal full-observation effect.

It does not establish natural skill selection, natural duration use,
semi-Markov or asynchronous external validity, semantic usefulness,
complementary team assignment, credit assignment, reward usefulness, task
improvement, or generalization beyond the tested environment and checkpoints.
The label is actively supplied throughout a hold branch, so a pass is
conditional control under forced hold, not autonomous commitment after the
label is removed.

## 2. Upstream evidence and frozen inventory

Upstream evidence authorizing this intervention:

- R27-G1 rollout-hidden static capacity passed at all three R25 arm0
  checkpoints: mean pairwise symmetric KL `0.046344`, `0.048502`, and
  `0.052734`; standardized action-mean distance `0.285952`, `0.291377`, and
  `0.302143`; inactive separation and live parity error were zero.
- R27-G1 synthetic active-versus-sham capacity passed at all three registered
  seeds. This is architecture-capacity evidence only.
- R26-G1a's arm0 observational family failed; it remains a narrow natural-data
  negative and is not evidence that the actor lacks immediate capacity.

Registered checkpoint slots, in temporal order rather than as independent
seeds:

1. `arm0_update25`, 800,000 environment steps / update 25.
2. `arm0_update30`, 960,000 environment steps / update 30.
3. `arm0_final`, 1,000,000 environment steps / update 32.

Git manages the source revision. The executor accepts these user-provided
checkpoint slots
only by registered path, non-empty file, and loaded update/step metadata; it
does not create or validate a separate content digest.

The source contract is S7-S1, six agents, four continuous action dimensions,
four individual skill labels, `skill_interval=10`, and
`skill_lifetime_candidates=[1,2,3,4]`. The actual native individual duration
targets are therefore 10, 20, 30, and 40 primitive steps. The R25 team-intent
target is 80 primitive steps (`team_intent_k=8`). No arm2 checkpoint may enter
or rescue this audit.

## 3. External-review disposition

The raw user-supplied Claude review is
`docs/external-review/R27_G2_design_review_20260712_Claude.md`.
The exact Claude model/version was not supplied, so model provenance remains
incomplete even though the response body is complete.

Accepted:

- Raw deterministic trajectory divergence is not persistence evidence.
- A stochastic natural prefix must be recorded and then replayed exactly.
- Hold-versus-pulse, late instantaneous label-swap controllability, and
  held-out label decoding are load-bearing controls.
- There is one context per reset group, nested windows, reset-cluster
  resampling, and per-checkpoint classification with temporal agreement.
- The forced label must use the live stateful recurrent actor path.
- Replay, hidden-state, RNG, inactive-label, same-label, finite-value, and
  checkpoint-identity checks precede scientific interpretation.

Modified after repository and cost audit:

- Claude's assumed duration set `{3,7,13,24}` is not the R25 source contract.
  Gated windows end at step 40; steps 41-50 are stress diagnostics only.
- Every branch uses a fresh environment instance plus exact action replay.
  Reusing one environment object and calling `reset(seed)` is not accepted as
  exact restoration.
- The scenario RNG is a legacy NumPy `RandomState`; its canonical state is
  obtained with `get_state()`. Any adapter-side Gym Generator is recorded
  separately through `bit_generator.state`.
- Focal age and duration clocks are not reset. Stage 1 freezes high-level
  assignment calls and changes only the actor-visible focal label through an
  audit overlay. This preserves the same-label identity null and isolates the
  intended intervention.
- The two inactive labels must equal each other. They need not equal the active
  reference, because neutralizing FiLM can legitimately change the actor
  output relative to active FiLM.
- The exact full branch count is 55, not an estimated 40-52.
- Gate C has one primary endpoint, H=40. H=20 and H=50 are descriptive, which
  removes the proposed disjunctive/multiple-endpoint gate.
- The R27-G1 synthetic fitter is not a frozen behavior-decoder protocol. R27-G2
  therefore pre-registers a separate low-capacity linear decoder below.
- A pass beside an R26 observational negative is described as
  `FORCED_CAUSAL_CAPACITY_WITH_OBSERVATIONAL_NEGATIVE`, not automatically as
  observational-instrument failure. Natural policy use and observational
  sensitivity remain unresolved alternatives.
- Decision-grade compute is conservatively 12-20 cloud-CUDA hours, not
  90 minutes to 2.5 hours.

Deferred rather than accepted into Stage 1: natural asynchronous non-focal
renewal, H=100, reward activation, and actor/GRU/FiLM redesign.

## 4. Experimental unit and natural prefix

The independent unit is a reset group. Each checkpoint uses reset IDs `0..63`
and environment seeds `1..64`. There is exactly one branch context per reset:

```text
prefix_steps(reset_id) = 50  when reset_id mod 3 == 0  (22 groups)
                         150 when reset_id mod 3 == 1  (21 groups)
                         250 when reset_id mod 3 == 2  (21 groups)
```

For each reset and checkpoint:

1. Construct a fresh environment and fresh frozen policy runtime.
2. Run the natural policy stochastically to the assigned prefix time, using a
   fixed and recorded per-reset policy-sampling seed
   `prefix_policy_seed = 27100 + reset_id`. Because skill, duration, team-code,
   and low-action sampling share global Torch RNG, each reset prefix must run
   in an isolated process/job or sequentially after reseeding. A shared
   asynchronously interleaved batched agent cannot claim per-reset RNG
   independence.
3. Record every executed joint action as exact `float32`, every natural skill
   decision, every pre-action Gaussian mean/log-standard-deviation, and the
   complete branch-point evidence described in section 6.
4. Freeze one action and one local-observation standardizer per checkpoint
   using exactly the last 50 natural-prefix pre-action rows from every one of
   the 64 registered resets and all six agents. Pool the equal-size
   `64*50*6` calibration rows, compute float64 per-dimension mean and population
   standard deviation (`ddof=0`), and floor each standard deviation at `1e-3`.
   Action calibration uses `a_det=tanh(mu)`; observation calibration uses the
   full local observation. Freeze these values before any branch outcome or
   exclusion is read and reuse them for all branches, agents, pairs, and
   breadth estimators at that checkpoint. A missing or non-finite calibration
   row makes the checkpoint `INVALID`. B3's train-only feature standardization
   is separate. No pilot or post-branch outcome may tune a scale, threshold,
   feature, or window.
5. For every branch, construct another fresh environment with the same reset
   seed, replay the exact recorded joint actions without querying the policy,
   restore the recorded policy runtime, assert branch-point parity, and only
   then execute the branch.

The branch snapshot is taken after exactly the assigned number of
`env.step(...)` calls have returned and before the next
`maybe_assign_skills(...)` or `act_low(...)` call. Thus the branch observation
is the observation returned by prefix action N, and the restored low hidden
state is the state produced while choosing prefix action N.

In addition to returned observation/state/info equality, replay must match a
canonical typed environment snapshot by direct structured comparison. Starting
from the adapter and underlying environment, the snapshot recursively traverses
nested `__dict__` objects and records type-qualified attribute paths plus all
Python scalar, NumPy scalar/array, list/tuple, set, and dictionary values, with
cycle detection.
Only callables, modules/classes, Gym space objects, renderer/plot handles, and
RNG objects are excluded by type; RNG states are captured and compared directly.
This type-based rule is fixed, and implementation review must reject ad hoc
field omission.

The prefix is stochastic to remain close to the R27-G1 collection
distribution. Branch execution is deterministic to make identity nulls exact.

## 5. Stage 1 intervention and exact branch matrix

Stage 1 is the only gated design. After the branch point, do not call
`maybe_assign_skills` or any other high-level assignment/renewal method. Team
code, all non-focal skills, clocks, and non-neural assignment state remain
frozen at their matched branch-point values. Low actor and critic hidden states
are restored identically once at each branch start and then evolve statefully
exactly once per primitive step; they are never reset or frozen within a
branch.

The only treatment is an audit-only focal label overlay at the input to the
live low actor. It must not call the legacy zero-hidden
`_low_actor_forced_skill_outputs` path and must not use the old all-agent R24
forced audit.

The current repository has no unified hook with these semantics. Any later
implementation must add one strict-source single-step audit hook that:

- copies the recorded skill roster, overrides only the focal actor-visible
  row, and never mutates `active_skills` or clocks;
- supports neutral FiLM (`gamma=1`, `beta=0`) on the focal actor row only;
- runs the actor recurrent transition exactly once and returns pre-tanh mean,
  log-standard-deviation, deterministic action, log probability, and new actor
  hidden state from that same transition;
- runs the source critic transition exactly once, returns value/new critic
  hidden, and advances both runtime hidden arrays exactly as live `act_low`
  would. The registered strict-HMASD critic is team-code/state conditioned and
  is not part of the focal-label treatment;
- uses the identical hook with no override for the reference branch. Existing
  `act_low` parity is checked on a duplicate restored snapshot, never by
  calling both paths successively on one live hidden state;
- fails closed for any policy class, action distribution, team-conditioning,
  tensor shape, or checkpoint contract outside the registered R25 source.

Each reset has exactly 55 branches, each with one 50-step rollout:

| Family | Count | Definition |
| --- | ---: | --- |
| Unforced reference | 1 | Recorded roster and team code, no label overlay, no renewal |
| Hold | 24 | Six focal agents x four labels; hold the focal label for all 50 steps |
| Pulse | 18 | Six focal agents x each of the three non-natural labels; force for steps 1-10, then restore that focal agent's branch-point natural label for steps 11-50 |
| Inactive-label identity | 12 | Six focal agents x two labels `((z_ref+1) mod 4, (z_ref+2) mod 4)` with neutral FiLM `gamma=1, beta=0`; labels must be bitwise identical to each other |

For every focal agent, the hold branch whose label equals the recorded natural
label must be bitwise identical to the single unforced reference. These six
comparisons are the same-label live-path null. The two inactive branches are
compared to each other, not to the active reference.

At every step of the unforced reference, hold, and pulse branches, before
executing the action, enumerate all four focal labels diagnostically at that
branch's exact current focal observation and supplied recurrent hidden state.
Record Gaussian means, log-standard-deviations, deterministic actions, output
hidden states, and active/neutral-FiLM outputs. The distribution and new hidden
for the branch's executed label must match the live single-step hook within the
registered parity tolerance. Diagnostic enumeration must use copies and must
not mutate runtime state or consume RNG. Inactive branches enumerate the four
labels with focal-row neutral FiLM and must remain label-invariant.

Nested read windows from the one 50-step rollout are:

```text
W_early = steps 1-10
W_mid   = steps 11-20
W_late  = steps 31-40
H40     = primary effect endpoint
H20     = descriptive intermediate endpoint
H50     = descriptive forced-hold stress endpoint only
```

H50 exceeds every configured individual duration and cannot gate a native
semi-Markov persistence claim.

## 6. Restoration and validity battery

For every branch, deep-copy a new working runtime from one immutable canonical
snapshot. The exact required attribute names are:

```text
active_skills
active_duration_indices
duration_remaining
skill_age
has_active_skill
active_team_codes
team_intent_remaining
team_intent_age
low_actor_hxs
low_critic_hxs
_last_low_context
segments
situation_debouncer
per_agent_situation_debouncer
situation_hazard_guard
_last_situation_state
_last_agent_situation_state
_team_transition_open
_team_transition_closed
_team_transition_env_steps
_team_intent_boundary_count
_team_intent_boundary_trunc_fracs
_team_intent_boundary_trunc_by_duration
_team_intent_dwell_checks
_team_intent_age_check_samples
_situation_diag_events
_agent_situation_diag_events
_situation_hazard_forced_renewals
_situation_hazard_events
```

A missing registered attribute or a newly discovered behavior-affecting
runtime attribute blocks implementation review until the immutable inventory
is explicitly revised. A runtime copy modified by one branch is never reused
as another branch's source.

The current high-level skill-duration selector and team bridge are
feed-forward; the neural recurrent state is in the low actor/critic. The
non-neural roster, clocks, segment, situation, and team-transition state still
must be restored because they can alter live rollout behavior or evidence.

Before each branch:

- local observations, global state, termination flags, and the required info
  fields equal the recorded branch-point values exactly;
- scenario `RandomState.get_state()` and adapter Generator state equal the
  recorded states;
- all restored runtime arrays/objects equal their canonical snapshots;
- the checkpoint path is the registered non-empty file, loaded update and step
  metadata match the registered slot, and cloned full module `state_dict`
  values (parameters plus buffers) plus ValueNorm values compare equal;
- action order, shape, dtype, and finite-value checks pass.

During and after each branch:

- the executed focal label is asserted every step;
- live-versus-diagnostic mean, log-standard-deviation, and next-hidden parity
  pass for the executed label;
- deterministic branch execution consumes no Python, NumPy, CPU-Torch, or
  CUDA-Torch global RNG state;
- scenario and adapter RNG states are recorded after every environment step and
  must compare equal across each matched reference/hold/pulse contrast through
  H40. This detects action-dependent random-draw-count divergence;
- full module and ValueNorm states remain directly equal to their cloned
  before-run snapshots;
- no value, action, hidden state, observation, or metric is non-finite;
- no branch crosses an episode boundary or contains an exogenous focal-agent
  failure.

Any replay mismatch, same-label mismatch, inactive-label leakage,
live/diagnostic mismatch, unexpected RNG consumption, checkpoint mutation,
CPU fallback, or non-finite evidence makes the whole checkpoint `INVALID`.
Episode boundary or exogenous failure may exclude a reset group only when the
event is recorded and the support floors below still pass.

CUDA identity checks require `torch.use_deterministic_algorithms(True)`,
cuDNN deterministic mode with benchmarking disabled, the runner's required
`CUBLAS_WORKSPACE_CONFIG=:4096:8` before CUDA initialization, TF32 disabled,
and identical inference batching/order for identity pairs. Same-natural-label and
paired inactive actor/action/environment arrays are required to be bitwise
identical under that contract. Independently implemented live-versus-
diagnostic actor quantities use the inherited R27 parity tolerance `1e-6`;
inactive metric leakage uses `1e-8`. An unsupported deterministic kernel is an
operational failure/`INVALID`, not permission to fall back to CPU or relax the
threshold after seeing data.

## 7. Metrics

Define the exact deterministic continuous action supplied to the environment
as `a_det = tanh(mu)`, where `mu` is the frozen actor's pre-tanh Gaussian mean.
Gate A and the SKL component of B1 retain pre-tanh distribution quantities as
conditional-capacity diagnostics. The load-bearing B1 action distance, B2
trajectory distance, and B3 decoder use `a_det`; a pre-tanh difference cannot
pass executable behavior when tanh saturation removes it.

All standardized `a_det` distances use the single checkpoint-level action
standardizer frozen from the exact calibration population in section 4.

### A. Immediate branch-point replication

At the exact branch-point reference state, enumerate all four labels with
active and neutral FiLM and reproduce the R27-G1 quantities:

- mean pairwise symmetric KL;
- mean pairwise Euclidean norm of action-mean differences divided by the
  first distribution's action standard deviation;
- reset-cluster active-minus-inactive symmetric-KL interval.

### B1. Sustained conditional controllability

On every hold branch, calculate per-step mean pairwise symmetric KL and
standardized pairwise `a_det` distance from the instantaneous four-label
enumeration at that hold-induced observation and hidden state. Aggregate
within `W_early`, `W_mid`, and `W_late`. Reference- and pulse-state
enumerations are required supporting evidence but do not gate B1.

```text
rho = SKL_late / max(SKL_early, 1e-8)
```

This metric proves that the live recurrent actor remains label-controllable on
late states induced by forced holds. It does not alone prove a persistent
behavior.

### B2. Hold-versus-pulse late behavior

For every matched non-natural target label, compare the hold and pulse focal
deterministic action sequences to the unforced reference over `W_late`.

Use the frozen checkpoint-level `a_det` standardizer. At each step use the
root-mean-square
standardized difference across action dimensions, then average over the
window:

```text
D_hold  = distance(hold_z, reference; W_late)
D_pulse = distance(pulse_z, reference; W_late)
Delta_B = D_hold - D_pulse
R_B     = D_hold / max(D_pulse, 1e-6)
```

Raw hold/reference or pulse/reference divergence is descriptive. `Delta_B`
and `R_B` are load-bearing because their predictions differ between a
continuously controlling label and an amplified first-interval nudge.

### B3. Held-out label consistency

Each hold branch yields one fixed 12-dimensional `W_late` executed-behavior
feature vector for the focal agent. For each of four action dimensions,
concatenate:

1. mean `a_det`;
2. temporal standard deviation of `a_det`;
3. least-squares temporal slope of `a_det`.

Fit one four-class linear decoder per focal agent. Agent identity, observation,
state, team code, hidden state, instantaneous swap statistics, and branch
metadata are not inputs.

The split is fixed by reset ID:

```text
test       = 0..11   (4/4/4 prefix strata)
validation = 12..23  (4/4/4 prefix strata)
train      = 24..63  (14/13/13 prefix strata)
```

For each agent, fit `Linear(12, 4)` after feature standardization learned on
train only (standard-deviation floor `1e-6`). Use full-batch cross-entropy,
Adam with learning rate `3e-3` and weight decay `1e-4`, at most 1,000 optimizer
steps, validation every 5 steps, patience 20 validations, minimum validation
loss improvement `1e-4`, and fit seed `27022`. Restore the best validation
state and evaluate test exactly once.

A fake-label control applies an independent deterministic permutation of the
four labels within every `(reset, agent)` group, seed `27023`, preserving
balance but destroying a consistent cross-reset mapping. It uses the identical
fit and stopping contract.

Aggregate held-out accuracy and macro-F1 pool the six per-agent decoders'
predictions with equal weight for every `(test reset, agent, label)` row. Let
`T` be the retained fixed-split test-reset set after permitted exclusions,
where `n_T >= 9` and every prefix stratum contributes at least three resets.
The aggregate uses `24*n_T` predictions, each agent uses `4*n_T`, and the
accuracy interval resamples only the `n_T` held-out reset groups without
refitting the decoder.

### C. Benchmark-local focal full-observation effect

At H40, standardize the full focal local-observation vector using the frozen
checkpoint-level observation standardizer, and use
root-mean-square distance to the unforced reference:

```text
E_hold  = local_effect_distance(hold_z, reference; H40)
E_pulse = local_effect_distance(pulse_z, reference; H40)
Delta_C = E_hold - E_pulse
R_C     = E_hold / max(E_pulse, 1e-6)
```

The full Scenario-7 observation is used without selecting fields.
It contains communication-derived components, so no communication subfield may
be selected, gated, or headlined, and this diagnostic can never become an
intrinsic reward source. This is benchmark-local effect evidence, not a
task-generic MARL effect representation. Global-state distance, non-focal
joint-action response, H20, H50, and effect decoding are descriptive only.

## 8. Pre-registered gates and statistics

Pilot outcomes cannot alter these rules.

Estimator contract, with `r` = reset, `i` = focal agent, `z` = executed hold
label, and `p` = one of six unordered diagnostic label pairs:

- A: average each active/neutral-FiLM pair metric over `p`, then over the six
  focal agents, producing one paired active/inactive value per reset. The
  checkpoint estimate is the arithmetic mean over valid resets.
- B1: for each hold `(r,i,z)` and window, average instantaneous-swap SKL and
  standardized pairwise `a_det` distance over the 10 steps and six `p`. Then
  average over the four hold labels and six agents to obtain
  `SKL_early_r`, `SKL_late_r`, and `X_late_r`; define
  `rho_r = SKL_late_r / max(SKL_early_r, 1e-8)`. Checkpoint SKL/distance are
  arithmetic means over resets and checkpoint rho is the median over resets.
  The neutral-FiLM counterpart is evaluated at the identical hold states and
  hidden copies with the same hierarchy, yielding one paired active-minus-
  inactive late-SKL value per reset.
  Agent breadth fixes `i` before averaging `z,p,step`; pair breadth fixes `p`
  before averaging `i,z,step`.
- B2: each reset has 18 matched non-natural `(i,z)` contrasts. Define
  `H_r = mean(D_hold)`, `Delta_B_r = mean(D_hold-D_pulse)`, and
  `R_B_r = median(D_hold/max(D_pulse,1e-6))` over those 18 contrasts.
  Checkpoint `H` and `Delta_B` are arithmetic means over resets; checkpoint
  `R_B` is the median over resets. Agent breadth fixes `i`; pair breadth uses
  only contrasts whose natural/target labels form `p`, then aggregates
  eligible agents inside each reset.
- B3: each retained held-out reset has exactly 24 equal-weight predictions
  (six agents x four labels). `Acc_r` is its correct fraction. Checkpoint
  accuracy is the arithmetic mean over the `n_T` retained test resets;
  macro-F1 is recomputed from the pooled `24*n_T` predictions. Bootstrap
  resamples those `n_T` test reset IDs, keeps the fitted decoders fixed, and
  recomputes accuracy and pooled macro-F1 with sampled-reset multiplicity.
  Per-agent accuracy uses that agent's `4*n_T` predictions.
- C: use the same 18 matched contrasts as B2 at H40. Define
  `Delta_C_r = mean(E_hold-E_pulse)` and
  `R_C_r = median(E_hold/max(E_pulse,1e-6))`; checkpoint Delta is the mean and
  checkpoint ratio is the median over resets. Agent/pair breadth follows B2.

No primitive step, branch, agent, or label row is an independent bootstrap
unit. Use 10,000 reset-ID bootstrap resamples and two-sided percentile 95%
intervals; every lower bound is the 2.5th percentile. Fixed seeds are `27031`
for A, `27041` for B1, `27051` for B2, `27061` for B3, and `27071` for C.
Checkpoints are classified separately and never pooled as seeds.

Gate A passes only when all are true:

- branch-point mean pairwise symmetric KL is at least `0.02` nats;
- branch-point standardized action-mean distance is at least `0.20`;
- the active-minus-inactive symmetric-KL 95% lower bound is above zero;
- all validity checks pass.

Gate B1 passes only when all are true:

- `SKL_late >= 0.02` nats;
- late natural-prefix-standardized pairwise `a_det` distance is at least
  `0.20`;
- the late active-minus-inactive symmetric-KL lower bound is above zero;
- median reset-level `rho >= 0.50`;
- at least four of six focal agents and at least three of six unordered skill
  pairs separately meet all four preceding B1 conditions under their fixed
  agent/pair estimator.

Gate B2 passes only when all are true:

- checkpoint mean `D_hold >= 0.20` in natural-prefix-standardized executed-
  action units;
- the reset-cluster 95% lower bound of `Delta_B` is above zero;
- median matched `R_B >= 1.50`;
- at least four of six focal agents and at least three of six unordered skill
  pairs each have mean `D_hold >= 0.20`, a positive `Delta_B` lower bound, and
  median `R_B >= 1.50` under their fixed estimator.

Gate B3 passes only when all are true:

- aggregate held-out accuracy and macro-F1 are each at least `0.40`;
- the test-reset-cluster accuracy lower bound is above chance `0.25`;
- at least four of six per-agent decoders have test accuracy at least `0.40`;
- fake-label held-out accuracy is at most `0.35`;
- train-minus-test accuracy is at most `0.20` for every gated decoder.

Gate B, persistent executable behavior under forced hold, passes only when B1,
B2, and B3 all pass.

Gate C passes only when all are true at H40:

- the reset-cluster lower bound of `Delta_C` is above zero;
- median matched `R_C >= 1.50`;
- at least four of six focal agents and at least three of six unordered skill
  pairs each have a positive `Delta_C` lower bound and median `R_C >= 1.50`
  under their fixed estimator.

There is no `H20 OR H50` or metric-disjunction route to Gate C.

Support is adequate only when:

- at least 48 of 64 reset groups remain valid per checkpoint;
- each prefix stratum retains at least 14 reset groups;
- every hold agent-label cell retains at least 40 reset groups;
- each gated unordered-pair contrast occurs in at least 40 distinct reset
  groups; multiple agents inside one reset do not increase independent
  support;
- B3 retains at least 32 train, 9 validation, and 9 test reset groups, with
  per-prefix-stratum floors of 10/10/10 inside train and 3/3/3 inside each of
  validation and test.

Failure of a support floor is `UNDERPOWERED`, not `FAIL`. A pilot cannot be
pooled into decision-grade support.

## 9. Decision rules

Checkpoint-level precedence:

1. A validity-battery failure is `INVALID`.
2. A support-floor failure is `UNDERPOWERED`.
3. A first Gate-A failure is `INVALID_SUSPECT` because it conflicts with
   R27-G1 and authorizes one instrumentation audit/repetition with unchanged
   thresholds. If a fully valid repetition still fails, classify
   `NO_BRANCHPOINT_STATIC_REPLICATION` (`FAIL`) rather than rerunning until it
   passes.
4. A+B+C is `PERSISTENT_BEHAVIOR_AND_EFFECT` (`PASS`).
5. A+B with C failing is `PERSISTENT_ACTION_NO_EFFECT` (`PASS` for the current
   behavior edge, but no reward authorization).
6. C passing while B is incomplete is `EFFECT_WITHOUT_PERSISTENT_ACTION`
   (`MIXED`).
7. B1+B2 passing with B3 failing is `INCONSISTENT_LABEL_MODES` (`MIXED`).
8. B1 passing with B2 failing is
   `STATIC_CONTROL_WITHOUT_HOLD_ADVANTAGE` (`MIXED`).
9. `TRANSIENT_ACTION_NUDGE` (`FAIL`) requires A passing, all of B1/B2/B3/C
   failing, median `rho < 0.50`, `Delta_B` lower bound at most zero,
   `R_B < 1.50`, held-out accuracy and macro-F1 each at most `0.35` with the
   accuracy lower bound at most chance `0.25`, and C failing. This label is not
   inferred merely from an aggregate gate failure.
10. If B1/B2/B3/C all fail after A passes but the exact transient pattern in
    item 9 is absent, classify `NO_PERSISTENT_SEPARATION` (`FAIL`).
11. Any remaining pattern with at least one but not all of B1/B2/B3 passing is
    `MIXED_OTHER`.

Family-level temporal decision:

- Any checkpoint `INVALID` or unresolved `INVALID_SUSPECT` makes the family
  `INVALID` pending the one permitted unchanged-contract repair cycle.
- With no invalid checkpoint, any checkpoint `UNDERPOWERED` makes the family
  `UNDERPOWERED`. The two-of-three rule cannot silently discard a registered
  checkpoint for validity or support reasons.
- `PASS_BEHAVIOR_EFFECT` requires B and C at at least two of three
  checkpoints.
- `PASS_BEHAVIOR_NO_STABLE_EFFECT` requires B at at least two of three
  checkpoints but B+C at fewer than two.
- `FAIL_BEHAVIOR_FAMILY` requires any combination of
  `TRANSIENT_ACTION_NUDGE`, `NO_PERSISTENT_SEPARATION`, or
  `NO_BRANCHPOINT_STATIC_REPLICATION` at at least two checkpoints.
- All other checkpoint disagreement is `MIXED_TEMPORAL_INSTABILITY`.

The two-of-three rule is the family gate. A stronger abandonment trigger is
separate: if all three checkpoints are valid and adequately powered and all
three fail B1+B2+B3+C, after no more than one genuine instrumentation-fix
rerun, stop adding diagnostics to rescue this frozen checkpoint family. Record
that the current architecture+objective did not produce temporally extended
behavior under this maximally favorable forced-hold test and perform the
required cross-round failure review. Abandoning the representation itself
would require a subsequent redesigned training line to fail the same frozen
protocol; it is not an automatic R27-G2 action.

## 10. Compute, staging, and artifact boundary

Per checkpoint, the 22/21/21 prefix allocation contains 9,500 natural-prefix
environment steps. One initial prefix collection plus 55 fresh replay/branch
runs costs exactly:

```text
9,500 + 55 * (9,500 replay steps + 64 * 50 branch steps)
= 708,000 environment steps per checkpoint
= 2,124,000 environment steps for three checkpoints
```

Diagnostic four-label forwards on every active branch and decoder optimization
are additional but do not add environment steps. Based on observed R27-G1
throughput, fresh replay, and the expanded diagnostic-forward load, register
12-20 hours on cloud CUDA for decision-grade Stage 1. CUDA is mandatory; there
is no silent CPU fallback.

If separately authorized after implementation review, a final-checkpoint-only
eight-reset pilot may execute at most the same 55-branch matrix (under 90,000
environment steps). It is wiring/parity/artifact/timing evidence only. It is
expected to cost roughly 30-60 minutes only if a safe flattened 64-job queue is
achieved; an eight-worker reset-sharded topology may cost about 3-5 hours.
All pilot scientific metrics are quarantined and cannot tune or contribute to
the decision-grade result.

Future outputs belong under a timestamped
`logs/r27_g2_forced_z_trajectory_effect_<timestamp>/` root. A later authorized
implementation must write a self-contained cloud Bash runner under `scripts/`
and record exact commands, environment count, resets, checkpoints, device,
branch count, and artifacts in `memory/ExpRecord.md` before launch.

## 11. Only authorized next action by outcome

- `PASS_BEHAVIOR_EFFECT`: permits only separate design/review of a task-generic
  reward target and, if that target has its own valid nulls, a promotion-ladder
  level-3 small clipped test against a mechanism-matched HA-CTSE control. Gate
  C's full Scenario-7 observation and communication fields cannot be that
  reward target. This outcome does not authorize a reward test or activation
  by itself.
- `PASS_BEHAVIOR_NO_STABLE_EFFECT`: no reward. Review why forced action control
  does not reach the benchmark-local focal effect before any training change.
- `MIXED_*`: complete the failure review and choose one unresolved causal edge;
  no new module, reward, sweep, or long run.
- `FAIL_*`: preserve the negative constraint and complete the cross-round
  R26/R27 failure matrix before any actor/objective change.
- `UNDERPOWERED`: increase support only; do not change thresholds, metrics,
  windows, or mechanism.
- `INVALID`: repair the identified instrument defect and repeat the same gate,
  with at most one genuine invalid-fix cycle before escalation.
- crash: preserve logs, repair the operational cause, and rerun the unchanged
  contract; a crash has no scientific interpretation.

Stage 2 natural asynchronous non-focal renewal is conditional and ungated. It
may be designed only after a Stage-1 Gate-B family pass. It cannot enter the
Stage-1 verdict or retroactively rescue a failure.

## 12. Core-MARL and change boundary

This design is reward-off and checkpoint-frozen. It changes no reward, actor,
critic, FiLM/GRU architecture, optimizer, loss, advantage, training collector,
environment dynamics, credit assignment, team intent, or latent-skill
semantics. `memory/ALGORITHM_PRINCIPLES.md` needs no change at this boundary.

Implementation, pilot, decision-grade launch, reward design, and algorithm
changes each require a later explicit authorization. Until then the open gate
remains `individual skill z_i -> persistent executable behavior`.
