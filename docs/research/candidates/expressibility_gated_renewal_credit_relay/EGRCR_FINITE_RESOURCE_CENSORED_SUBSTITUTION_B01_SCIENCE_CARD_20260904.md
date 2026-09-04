# EGRCR finite-resource censored-substitution B01 science card — 2026-09-04

Status: `FROZEN / B_EXPLORE / IMPLEMENTATION_REQUIRED / NO_LAUNCH_SHA`

Object ID: `EGRCR-FRCS-B01-20260904`

## Authority, class, and claim ceiling

This is the first finite-resource rung inside the B/EXPLORE family opened by the Portfolio decision
`docs/research/portfolio/decisions/2026-09-01-empirical-standard-full-direction-reaudit.md`:
structured relay critic versus a competent pair-aware critic and exact conditional-Q control on one
native allocation/utility host. It implements the surviving discriminator named by
`evidence/2026-08-29-four-successor-03-handoff.md`; it does not reopen that cycle's closed
exact-population information-necessity question.

The maximum claim is one-seed preliminary evidence about finite-data critic estimation on the
fixed four-agent censored-substitution host below. A positive result can say only that the frozen
association-factorized critic used this finite batch and update budget more effectively than the
frozen containing pair-cell critic on the recorded conditional-Q, source-gradient, allocation, and
utility measurements. It cannot establish relay information unavailable to generic conditional Q,
stable superiority, a population effect, a deployable credit rule, end-to-end variable-`k` value,
transfer, variable population, UAV relevance, safety, or a general credit claim.

## Prior observation and live question

The terminal exact-population cycle directly observed that three balanced source-to-waiter
topologies, including censored substitution, have the same population policy-score update as a
competent same-information conditional-Q/Rao--Blackwellized estimator. The strongest
counterevidence to broader closure is untested finite-sample and finite-optimization behavior.
The old EGRCR B1 also observed an expressive policy movement but exact `INTACT=GAE` native utility
and allocation over all twelve roots; its wrong-binding cut additionally broke generic cue
supervision and is not reused here.

Question: with the same sampled native trajectories, terminal external-return targets, parameter
count, initialization bytes, optimizer state, minibatches, updates, and evaluation opportunities,
does an association-aligned low-rank critic estimate the exact conditional Q and its induced source
gradient better than a competent unrestricted pair-cell critic, and does any such gain change a
real scarce waiter allocation or bounded utility at this budget?

The strongest live null is that the direct pair-cell critic is at least as data- and
optimization-efficient. Other live explanations are factorization nonconvexity, lucky lifetime-mode
counts, source-cell imbalance, initialization geometry, insufficient generic exposure, and an
implementation, RNG, numerical, target, work, or evaluator mismatch.

## Native host and environment-to-consequence trace

Each episode has four persistent physical agents on a directed ring and three native transitions.
The source identity `s` is sampled uniformly from `{0,1,2,3}`. Its two ready eligible waiters are
the clockwise relation `a=+1` and counter-clockwise relation `a=-1`; choosing one spends the sole
allocation token. The source observes `s`, both waiter identities, both public ordered edge keys,
the content sign `c in {-1,+1}`, readiness, and the remaining token. Both learned arms receive
exactly these fields. There is no hidden treatment-only edge, label, counterfactual, or future fact.

At transition 1 the selected original waiter becomes the carrier. At transition 2 the carrier mode
is sampled uniformly from `PERSIST`, `REPLACE`, and `EXPIRE`. `REPLACE` transfers the already
selected job to the unique non-source, non-selected substitute; the selected relation remains the
job's provenance while physical carrier identity changes. `EXPIRE` censors the job. At transition
3 a nonexpired carrier serves. External bounded utility is

```text
U = 1{mode != EXPIRE} * 1{a = c} in {0,1}.
```

Thus the exact action-time conditional Q is `Q*(s,c,a)=2/3` when `a=c` and zero otherwise. The
source owns the waiter choice; the selected waiter or substitute owns service. Membership is fixed,
but entity identity and carrier identity are distinct. Replacement and censoring occur after the
source action, all post-action events are present in the common trajectory, opportunity time is one
episode, optimizer exposure is the critic update count, and there is no partner adaptation or
semi-Markov discount claim.

The source policy used for evaluation is the temperature-one softmax of the two learned Q values.
Its native scarce-allocation observable is probability assigned to `a=c`; its native return is
measured by paired environment episodes and also enumerated exactly over all source/content/mode
cells. The nonlearned exact-Q policy uses the same temperature-one transform and is a calibrated
reference, not a native-optimal ceiling or an empirical arm.

## Frozen learners and strongest comparator

Both learned critics are FP32 PyTorch modules with exactly 32 trainable scalars. A single
counter-addressed vector drawn uniformly from `[-0.05,0.05]` supplies the same 32 initialization
bytes to both arms in their documented flat parameter order. Both use Adam with learning rate
`0.01`, betas `(0.9,0.999)`, epsilon `1e-8`, no weight decay, zero initial moments and step count,
mean squared error to the same terminal external return, the same minibatch indices, 128 optimizer
updates, and no clipping, scheduling, early stopping, arm-specific tuning, or target shaping.

1. **`ASSOCIATION_FACTOR` (treatment).** With two rank components, source-edge factors
   `U_j[s,a]`, content-edge factors `V_j[c,a]`, and biases `B[s]`, `D[c]`, `E[a]`,

   ```text
   Q_F(s,c,a) = 0.5 * (U_1[s,a] * V_1[c,a]
                       + U_2[s,a] * V_2[c,a])
                + B[s] + D[c] + E[a].
   ```

   Parameter count is `8+4+8+4+4+2+2=32`. The factorization aligns the selected ordered
   source-waiter relation with content, but receives no auxiliary loss or intermediate label.

2. **`GENERIC_PAIR` (strongest comparator).** Two independent direct tables
   `T_j[s,c,a]` predict

   ```text
   Q_G(s,c,a) = 0.5 * (T_1[s,c,a] + T_2[s,c,a]).
   ```

   Parameter count is `16+16=32`. This comparator is competent and strictly nonrestrictive on the
   finite action-time population: it can represent every possible Q table, including the exact
   factorized solution, without treatment information or target privilege.

3. **`EXACT_Q` (reference).** The closed-form `Q*` above. It has no initialization, samples,
   optimizer trajectory, or exposure and is excluded from learned-arm comparisons.

Both learned arms process two scalar components per row and the runner reports analytical
multiply/add counts, parameter bytes, Adam-state bytes, training wall time, and peak RSS. Exact
FLOP identity is not claimed: any residual arithmetic difference is a stated limit, and this rung
supports no wall-time or memory superiority claim. The comparison is matched on the quantities the
estimands consume: trajectories, external-return targets, parameters, optimizer state, example
exposures, updates, and evaluator calls.

## Seed, training budget, evaluation budget, and stop rule

The sole scientific seed is integer `2026090401`. The behavior policy is uniform over the two
eligible waiters. The environment generates 192 training episodes, 576 native transitions, and
one terminal target per episode. Source, content, action, and lifetime counts are reported exactly;
no cell is selected, discarded, resampled, or balanced after observing a return.

Each learned arm receives 128 Adam updates with minibatch size 32 from one seed-derived cyclic
permutation of the shared batch: 4,096 example exposures per arm. Evaluation uses 256 paired native
episodes per learned arm and the exact-Q reference with common source/content/mode/action uniforms,
plus deterministic enumeration of all `4 sources x 2 contents x 2 actions x 3 modes = 48` cells.
The runner reports nonzero training/evaluation environment transitions, optimizer updates, and
evaluation episodes separately.

This is one paired invocation, not a budget or hyperparameter sweep. The runner's own static work
projection per learned arm is:

```text
training_environment_transitions = 192 * 3 = 576
optimizer_example_exposures       = 128 * 32 = 4096
evaluation_environment_transitions = 256 * 3 = 768
exact_evaluation_cells             = 48
trainable_parameters               = 32
```

The non-result `project-cost` mode must emit those counts before launch and must report a
conservative projection from the runner's fixed planning law:

```text
projected_arm_seconds = 3 * (
    5
    + 0.01 * training_environment_transitions
    + 0.005 * optimizer_example_exposures
    + 0.01 * evaluation_environment_transitions
    + 0.02 * exact_evaluation_cells
)
                      = 119.64 seconds per learned arm.
```

The coefficients are prospective planning weights, not observed performance, and factor three is
the fixed implementation/host-load allowance. The fixed machine-time cap is 600 wall seconds per
learned arm.
Because both arms run sequentially in one process, the invocation cap is 1,200 wall seconds. A cap
stop is an incomplete technical attempt and is not interpreted or resumed. A valid attempt runs
both learned arms in fixed order `GENERIC_PAIR`, then `ASSOCIATION_FACTOR`, without inspecting the
first arm's result; there is no result-sensitive early stop.

## Exposure line

Before launch, `project-cost` must machine-generate and the result must repeat:

```text
updates=128; adam_lr=0.01; nominal_lr_exposure=1.28;
init_half_range=0.05; nominal_exposure_over_init_half_range=25.6
```

This is an optimizer opportunity scale, not a coordinate-displacement bound. The result reports
per arm the actual `L_inf(theta_128-theta_0)/0.05`, `L2` displacement, nonzero changed-coordinate
count, and first/last loss. Zero parameter movement refuses the scientific result.

## Required observables and estimands

The single `summary.json` reports the launch SHA and argv; exact configuration; flat initial and
final parameter summaries; source/content/action/mode counts; transition, episode, example,
update, and evaluation counts; target and prediction ranges; nonfinite counts; wall time and peak
RSS when measured; parameter/optimizer/work accounting; and the machine-generated cost and exposure
lines. Missing resource telemetry leaves an otherwise valid run marked `resources_unmeasured`.

For each learned arm, report over the 16 action-time cells:

- RMSE and maximum absolute error against `Q*`;
- exact action-ranking competence, `C_Q`, the number of the eight source/content contexts whose
  greedy action is `a=c` (shared deterministic tie rule);
- the eight-component uniform-policy source-gradient vector, one component per `(s,c)` logit,
  `g[s,c]=0.25*(Q(s,c,+1)-Q(s,c,-1))`, plus its L2 error and cosine to the corresponding exact-Q
  vector;
- mean probability allocated to `a=c`, exact expected bounded utility, paired sampled bounded
  utility, and their per-source/content values.

The primary estimation differences are
`Delta_Q = RMSE_GENERIC - RMSE_FACTOR` and
`Delta_g = grad_error_GENERIC - grad_error_FACTOR`. The primary native difference is
`Delta_U = exact_utility_FACTOR - exact_utility_GENERIC`; sampled utility is supporting evidence.
The exact-Q reference supplies scale but never counts as a learned-arm win.

## Frozen result rule

Apply the first matching branch after both learned arms and the reference are complete:

| Branch | Rule and bounded reading |
| --- | --- |
| `FRCS-INVALID-INCOMPLETE` | A common-integrity item fails; mandatory fresh admission is absent or below 4 GiB; learned-arm inputs, targets, initial bytes, optimizer/update/example/evaluator counts, or required measurements differ or are missing; a parameter vector does not move; or a required count is zero. Quarantine; no scientific observation. |
| `FRCS-E-GENERIC-UNDEREXPOSED` | `C_Q_GENERIC < 8`. The containing comparator did not reach action-ranking competence at this budget. Report both curves, but make no treatment-efficacy claim; the next object may increase common exposure. |
| `FRCS-A-FACTORIZED-ENDPOINT-GAIN` | `Delta_Q>0`, `Delta_g>0`, and `Delta_U>0`. On this seed the factorized critic improved both exact estimation readings and native expected utility over a competent generic comparator. This supports only a three-seed replication of the unchanged rung. |
| `FRCS-B-ESTIMATION-ONLY` | `Delta_Q>0` and `Delta_g>0`, but `Delta_U<=0`. Factorization improved the two estimation readings without changing native utility in the predicted direction. Any successor must target the decision boundary, not claim algorithm value. |
| `FRCS-C-GENERIC-MATCHES-OR-BEATS` | `RMSE_GENERIC<=RMSE_FACTOR`, `grad_error_GENERIC<=grad_error_FACTOR`, and `exact_utility_GENERIC>=exact_utility_FACTOR`. The competent direct critic matches or beats the factorized arm on all primary readings at this rung. This closes only this architecture/budget/seed unit. |
| `FRCS-D-MIXED` | Every other complete combination. Preserve the exact discordance; no clean efficiency polarity is inferred. |

A one-seed result never establishes stability. Only branch A authorizes preparation of the exact
same three-seed replication as an object-tier next rung. Branches B--E require a written intake
before any changed budget, architecture, or target. No branch changes direction lifecycle or
Portfolio investment.

## Predictions on record

- **DM prediction:** `FRCS-C-GENERIC-MATCHES-OR-BEATS`. The generic table is convex in its
  parameters and directly represents every cell, while the treatment introduces a nonconvex
  product without additional targets. I expect it to reach `C_Q=8` and match or beat the
  factorized arm on Q error, source-gradient error, and native utility at 128 updates.
- **Owner prediction:** `not taken (unattended)`.

## Protected semantics, engineering scope, and CM return

Protected scientific and engineering semantics are: the four-agent ring and entity identities;
the selected-relation versus replacement-carrier distinction; the uniform `PERSIST/REPLACE/EXPIRE`
law; the external utility and exact Q; common RNG coordinates and arm order; FP32; flat
initialization bytes; model equations and parameter count; shared external-return targets;
minibatch indices; Adam semantics; counts; softmax evaluator; deterministic tie rule; output only
under the named scratch root; and no side effect outside it. Technical success cannot establish any
result branch or mechanism value.

This object needs none of `docs/project/ENGINEERING_SCOPE_SPEC.md` section 4. It adds no distributed
execution, worker pool, scheduler, queue, checkpoint/resume/recovery, retry, lease, lock, heartbeat,
liveness probe, tamper evidence, byte manifest, provenance/currentness guard, incident tree,
schema validator, registry, plugin/configuration framework, compatibility shim, or telemetry beyond
wall time and peak RSS.

CM owns only:

- `experiments/candidates/expressibility_gated_renewal_credit_relay/finite_resource_censored_substitution_b01/`;
- `scripts/run_egrcr_frcs_b01.py`; and
- `tests/experiments/candidates/expressibility_gated_renewal_credit_relay/finite_resource_censored_substitution_b01/`.

The attempt stays below 2,000 new research-code lines, the runner below 600 lines, and orchestration
below 30 percent. Tests are one under-60-second end-to-end toy smoke and focused result-rule/model/
count tests, run once after editing and once immediately before launch. CM returns the exact changed
paths, test command/result, `project-cost` output, protected-semantic audit, and a commit pushed from
its independent worktree. It does not run the scientific seed. If the frozen object cannot be
implemented inside these limits without changing meaning, CM returns the exact blocker.

After CM acceptance, DM integrates the implementation, records a launch SHA, runs
`python scripts/hmasd_resource_preflight.py admit-memory --out <receipt>` immediately before the
single result invocation and before it creates trajectories, models, optimizer, or result roots,
then starts the invocation detached under
`temp/directions/expressibility_gated_renewal_credit_relay/exp/frcs_b01_20260904/`.

## Object-tier decision

Options considered before implementation:

- (a) run this one-seed, 128-update finite-resource rung on the censored-substitution host;
- (b) begin with three seeds and a budget curve before establishing that either learned route is
  competent and decision-sensitive; or
- (c) reopen the exact-population relay/noncollinearity search already closed by the terminal
  three-family audit.

Recommendation: **(a)**. It is the smallest reversible observation that directly reaches the
Portfolio-authorized unknown while preserving the exact-population null and keeping any
three-seed investment conditional on an observed finite-resource signal.

**Owner-delegated decision (unattended, 2026-09-03 instruction): (a).** This is object-tier wording
inside an already opened B family. It changes no frozen prior result, direction lifecycle,
Portfolio priority, fusion boundary, or investment decision.

## Non-goals

Do not repair or rerun historical EGRCR B1/T3, use the old wrong-binding cut, hide an edge or
post-action event from the generic comparator, add auxiliary labels, change the external target,
tune an arm after seeing results, introduce a budget sweep, add held-out rosters or variable
membership, modify core code, or infer association-specific information value from a finite-resource
architecture comparison.
