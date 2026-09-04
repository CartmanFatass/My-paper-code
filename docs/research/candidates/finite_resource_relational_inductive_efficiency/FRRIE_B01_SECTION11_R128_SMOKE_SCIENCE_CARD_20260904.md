# FRRIE B01 section-11 R128 smoke science card — 2026-09-04

Status: `FROZEN / B_EXPLORE / IMPLEMENTATION_REQUIRED / NO_LAUNCH_SHA`

Object ID: `FRRIE-B01-SECTION11-R128-SMOKE-20260904`

## Authority and evidence class

This is the smallest B/EXPLORE rung selected by the owner in
`docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`: first determine
whether one real Slice-B learner path can complete 128 updates, then run the unchanged three-seed
B01 family. It stays inside the already selected
`FRRIE-B01-PHY-EDGE-MATCHED-CURVES-20260901` family and does not open, close, recast, or promote a
direction.

The claim ceiling is one literal seed, the fixed training rosters `N={9,15}`, the `INTACT`
intervention, and 128 updates. It can establish only that the real host/learner/comparator path ran
with the observed exposure and produced the reported curves, contact state, and competence
observation. It cannot establish a package effect, held-out roster transfer, reassociation
sensitivity, stable direction, semantic or relational mechanism, arbitrary-`N` behavior, churn,
deployment, or safety.

## Question and non-goals

Question: on one prospectively selected B01 root, can byte-paired `PHY_TRUST` and its strongest
same-information containing comparator `EDGE_FLEX` complete 128 real RSCF updates and
adaptation-free evaluations while preserving the paired estimand before tight-boundary contact?
What return curves, EDGE competence, tight-contact state, and learner exposure are directly
observed?

This rung does not implement or require the old 512-update resume chain, the 98-cell panel, held-out
`N={6,21}`, `SEMANTIC_COLUMN_ROTATE`, ordered-28 analysis, symmetric between-arm TV, parameter-
distance sidecars, a universal equality theorem, source-byte identity, full-chain telemetry, or a
production-readiness disposition. Those are optional analysis or later-rung concerns under evidence
specification §11.4 and §11.6.

## Environment-to-consequence trace

Each episode has one fixed roster for 12 native slots with public roles `WEST_SURVEYOR`,
`EAST_SURVEYOR`, and `RIDGE_RELAY`. The shared actor receives the same 22-field entity values,
public relations, legal masks, incoming recurrent state, addressed tapes, and training order in
both arms. It selects one legal native action per entity. The existing package-native host applies
the scan, uplink, half-duplex radio, collision, expiry, acknowledgement, and delivery laws. RSCF
uses the resulting factual and legal counterfactual suffix returns for one full-batch update. The
native consequence is

`J = 0.65*(D_W+D_E)/6 + 0.25*min(D_W,D_E)/3 + 0.10*(1-WASTE)`.

Membership is fixed inside every episode. Entity identity is physical entity identity rather than
slot identity; no join, leave, rejoin, replacement, censoring, semi-Markov lifetime, or partner
co-adaptation claim is present. Opportunity time is the native slot; optimizer exposure is the
update count.

## Treatment, comparator, and live alternatives

Both learned arms start from identical parameter bytes and share the architecture, `K0` chart,
observations, tapes, batches, Adam configuration, evaluation opportunities, and parameter count.
The only treatment difference is the post-Adam `beta` projection:

- `PHY_TRUST`: `beta in [-0.15,0.15]`;
- `EDGE_FLEX`: `beta in [-1.50,1.50]`.

`EDGE_FLEX` is the strongest competent same-information comparator because it strictly contains
the tight projection class. `UNIFORM_LEGAL` is a checkpoint-invariant competence reference at
`N={9,15}`, not a substitute comparator.

Live explanations are: no contact and observed-path equality; EDGE incompetence at this budget;
generic shrinkage or Adam geometry; host alignment to `K0`; evaluation noise; and an
implementation, support, leakage, RNG, numerical, or work-parity defect. One seed cannot choose
among these generally.

## Seed, budget, stop rule, and cost projection

After the mandatory memory admission and before any B01 tape, model, optimizer, or outcome is
created, create the existing five-root B01 packet prospectively. This rung uses only
`FRRIE-B01-FRESH-BLOCK-001`. The later three-seed rung uses the already generated ordered roots
`001..003` under its own card; the R128 observation cannot select or replace roots or change its
configuration.

For each learned arm:

- 128 updates;
- 64 training episodes per update in literal `(9,15)*32` order;
- one backward call and one Adam step per update;
- evaluation at updates `{0,32,64,128}`, rosters `{9,15}`, `INTACT` only, 256 episodes per cell;
- one `UNIFORM_LEGAL` 256-episode cell at each seen roster, reused across checkpoints.

The runner's existing cost law gives, per learned arm:

- training: `4,928 * 128 = 630,784` environment slots;
- evaluation: `4 * 2 * 256 * 12 = 24,576` environment slots;
- total: `655,360` environment slots and 128 optimizer steps.

The shared uniform reference adds `2 * 256 * 12 = 6,144` slots, so the one-seed invocation projects
`1,316,864` total environment slots. The retained two-arm collector observation was 9,856 slots in
11.6354654 seconds (about 847.07 slots/s), implying about 12.9 minutes of native-slot work per
learned arm and 25.9 minutes total at that observed rate. This extrapolation excludes optimizer,
evaluation, build, and I/O overhead and is a planning observation, not a gate.

The machine-time cap is four wall-hours per learned arm; because the arms are interleaved in one
invocation, the invocation stops at eight wall-hours. A cap stop is a technical incomplete attempt,
has no scientific polarity, and is not resumed or salvaged. There is no result-sensitive early
stop: a valid rung reaches update 128.

## Exposure line

The runner must machine-generate this line before launch and repeat it in `summary.json`:

`updates=128; adam_lr=0.0003; nominal_lr_exposure=0.0384; init_half_range=0.05; nominal_exposure_over_init_half_range=0.768`

Initialization is uniform on the representable values in `[-0.05,0.05]`. The nominal quantity is
an exposure scale, not a mathematical coordinate-displacement bound. The result also reports the
observed `L_inf(theta_128-theta_0)/0.05`, first tight-contact update, and cumulative tight-projection
displacement.

## Observables, estimands, and result rule

Report each checkpoint and arm separately: `J`, `D_W`, `D_E`, `min(D_W,D_E)`, `WASTE`, action and
native-event counts, transitions, episodes, backward calls, Adam steps, evaluation episodes, first
tight-contact update, changed-coordinate inventory, maximum overshoot, cumulative projection
displacement, pre-contact full model/optimizer equality, wall time, and peak RSS. Missing resource
telemetry leaves an otherwise valid run marked `resources_unmeasured`; missing learner counts,
curves, or required checkpoints is an incomplete attempt.

For each checkpoint and seen roster, report the literal-seed descriptive quantities

- `d_u(N) = J_PHY,int(N) - J_EDGE,int(N)`;
- `e_u(N) = J_EDGE,int(N) - J_UNIFORM,int(N)`.

Apply exactly one branch after the complete invocation:

| Branch | Rule and bounded reading |
| --- | --- |
| `R128_INVALID_INCOMPLETE` | A §4 integrity item fails; mandatory admission is absent/below 4 GiB; real learner transition/update/evaluation counts are zero or missing; the exposure line is absent; paired information/work differs; an arm differs before contact; or required learner-side measurements are absent. Quarantine; no scientific observation. |
| `R128_VALID_NO_CONTACT` | The complete valid rung has no FP32-changing tight projection through update 128. Report the curves and observed-path equality only where full parameter/optimizer equality is directly observed. |
| `R128_VALID_CONTACT` | The complete valid rung has at least one FP32-changing tight projection. Report contact, exposure, curves, EDGE competence, and any weak, adverse, or mixed arm differences literally without treating one seed as polarity. |

Every valid branch advances to preparation of the unchanged three-seed B01 rung. Only an invalid or
technical attempt returns to CM for an outcome-blind repair at a new launch sha. The R128 values do
not authorize a configuration, seed, or comparator change before that three-seed rung.

## Predictions on record

- DM prediction: `R128_VALID_NO_CONTACT`. `beta` starts within `[-0.05,0.05]`; reaching the tight
  wall requires at least 0.10 coordinate movement from the most extreme allowed initialization,
  while nominal 128-step learning-rate exposure is 0.0384. I expect full paired equality through
  update 128 and therefore no arm-return difference on the literal path.
- Owner prediction: `not taken (unattended)`.

## Engineering-scope declaration and CM boundary

This object needs none of `docs/project/ENGINEERING_SCOPE_SPEC.md` §4. In particular, it does not
need distributed execution, a worker pool, checkpoint/resume/recovery orchestration, retries,
leases, supervisors, tamper matrices, byte manifests, source-currentness gates, create-once
publication, incident trees, schema frameworks, registries, or telemetry beyond wall time and peak
RSS.

CM owns a fresh implementation using clean committed FRRIE APIs. The intended owned paths are one
new runner `scripts/run_frrie_b01_r128_smoke.py` and one mirrored test
`tests/experiments/candidates/finite_resource_relational_inductive_efficiency/b01/test_r128_smoke.py`;
an additional small object-local helper is permitted only if the runner cannot remain under 600
lines. Total new research code remains under 2,000 lines, orchestration under 30%, and the test set
is one under-60-second toy end-to-end smoke plus branch/count tests. The runner uses `argparse`, an
explicit production seed-packet path, an output directory, the existing fixed configuration, and
writes one `summary.json` containing the launch sha, exposure line, direct counts, and rule inputs.

The owner-dirty main-checkout files named in the accompanying intake are excluded from CM
ownership. CM must not copy or edit them. If clean committed APIs cannot execute the 128-update loop
without changing treatment, comparator, RNG, numerical, checkpoint, or side-effect semantics, CM
returns the exact missing API as a technical blocker. Technical success establishes only a
launchable implementation; it cannot establish mechanism value or any branch above.

After CM acceptance, DM commits the card and implementation before launch, records that launch sha
and the declared source paths, runs `scripts/hmasd_resource_preflight.py admit-memory` immediately
before the result invocation, and starts the invocation detached under
`temp/directions/finite_resource_relational_inductive_efficiency/exp/`. The runner does not inspect
Git cleanliness, compare HEAD identity, or refuse unrelated workspace changes; those are not B
launch conditions.
