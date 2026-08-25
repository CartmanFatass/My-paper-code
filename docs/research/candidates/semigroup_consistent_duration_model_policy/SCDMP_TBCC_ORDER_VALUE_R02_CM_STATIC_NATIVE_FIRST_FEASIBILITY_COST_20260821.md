# SCDMP TBCC order-value revision 02 CM static native-first feasibility and cost

```text
document_kind=cm_static_technical_assessment
direction_id=semigroup_consistent_duration_model_policy
exact_object=SCDMP-TARGET-BOUND-COMPETENT-CONTROLLER-ORDER-VALUE-DEFINITION
science_revision=SCDMP-TBCC-ORDER-VALUE-SCIENCE-20260821-02
science_card_sha256=f7a6363caf4333e7afcf4cd8df8043ae3b3088a57cb42a34eaf7fa432cb38481
pro_disposition=CLOSED
em_intake=ACCEPT_CLOSED
cm_owner=CM_semigroup_consistent_duration_model_policy
assessment_scope=static_native_first_feasibility_observability_comparator_lifecycle_cost
scientific_activity_started=false
question_relevant_output=none
```

## Technical conclusion

The frozen revision is statically single-valued, observable and technically
constructible without a science-bearing change. The plant, two setup-event
maps, public/latent boundary, external-hold schedules, foundation gate,
full-mission opportunity service, treatment and four controls, duration-correct
training law, endpoint families, prerequisite-dependent atomic lifecycle and
first-true branch map each have a concrete implementation boundary.

This acceptance is definition-only. No TBCC executable host, loader, registry
entry, fixture, model, identity, coordinate, checkpoint, rollout, result or
lease exists. A future construction must start with a new task-specific C++
batched host and measured benchmark. It must not reuse the consumed SCDMP UAV
r02 host, source, controller, checkpoint, coordinate or result.

There is no current science-bearing ambiguity and no material resource-class
change. The prospective card envelope of 24--40 experienced engineer-days,
80--240 CPU core-hours, 24--72 four-worker elapsed hours, 12/20 GiB
minimum/preferred RAM, at most 10 GiB scratch and 4 GiB durable artifacts is a
credible conservative planning envelope. It is not lease readiness: the
mandatory measured end-to-end efficiency review remains unperformed and a
heavy lease must be withheld until construction and benchmarking are separately
authorized and accepted.

## Static binding and observability

### Plant, event and public-alias boundary

- The complete native state is the card's plant/command/support state with
  0.1 s ticks and a 364-tick horizon. All transition coefficients, clipping,
  cable exposures, clearance, failure precedence, safe-docking predicate and
  post-absorption mask are explicit.
- The native setup compositor must start from `p=(1,2,3,4)`, apply the exact
  `H` and `R` maps in the supplied raw middle-event order, derive only the two
  registered final assignments and keep `p`, `b_q` and `q` internal to the
  physical host. `LEVEL-RELEASE` must preserve the assignment while producing
  the exact common public first-renewal state.
- A conformance consumer can compare the two native latent assignments while
  separately requiring byte/equality-level public aliasing at first renewal.
  Production controllers receive only the frozen public vector; order-aware
  controllers receive raw setup order, while foundation and SET receive the
  unordered multiset. No public failure label, graph label or future schedule
  is needed.
- Setup slots are action-independent and contain no plant control. Therefore
  the 16 opportunity states are fresh draws from the registered aliased
  first-renewal public initialization law, instantiated under both latent
  graphs. No additional state distribution is required.

### External `k`, opportunity and direct endpoints

- Fixed `k={5,11}` and target `k={7,13}` are explicit. Each switch regime is
  balanced over switch boundaries `n=91` and `n=273`, both of which are legal
  renewal boundaries for the outgoing period. No mid-hold query or reset is
  permitted.
- The full-mission opportunity service is finite: one forced first action,
  then deterministic lexicographic foundation control through terminal on each
  of four prospectively bound tapes. Tape averaging precedes every max, and
  exact argmax sets preserve ties. The service can return only the complete
  replicate-level `Q`, `D` and `S` inputs to its atomic gate.
- The native host can expose terminal counters sufficient for
  `V,W,P,T,E,O,G,L,F` without exposing training reward as a branch input.
  Failure labels remain nonexclusive, failure dominates same-tick docking,
  and energy masks every post-absorption slot.
- Every Student-t family, threshold, strict boundary rule, route state and
  first-true branch has an explicit finite input inventory. A prerequisite
  nonpass makes later stages inapplicable rather than incomplete.

## Comparator and model feasibility

- The foundation actor/critic parameter counts `12,882/11,233` and total
  `24,115` follow directly from the declared affine layers.
- The treatment scale and critic contain `641+5,505=6,146` trainable
  parameters. The FREE/SET residual contains `6,610`, giving `12,756`
  order-stage trainable parameters for each unrestricted arm.
- TREAT is implementable as a batched 18-action score tensor with
  `alpha=ReLU(g(o))`. FREE reproduces TREAT at zero residual and has feasible
  output-bias directions outside `span{1,J}`, so deployed actor-class strict
  containment is directly testable without claiming optimizer-path
  containment.
- REVERSED must share the exact final treatment foundation and adapter weights,
  alter only the compositor input `q -> 1-q`, and leave the native physical
  graph unchanged. SET must replace order by `q=0.5` and `J_SET` in actor,
  critic, old-policy, bootstrap and loss paths, and must be invariant to raw
  middle-event permutation.
- Foundation weights and normalization become immutable before opportunity or
  adapter work. TREAT/FREE/SET clone the same accepted foundation bytes. The
  one-vector-across-`k` rule is enforceable by one model/checkpoint identity
  per replicate/arm and by rejecting per-`k` parameters, optimizers or updates.
- The inverse-CDF action law, strict cumulative boundary, exact
  duration-correct return, three epoch-keyed Fisher-Yates permutations,
  quotient/remainder minibatches, gradient tie conventions, global clipping
  and persistent AdamW indices are all single-valued. They require explicit
  deterministic numeric conformance but no scientific clarification.

## Required native-first construction brief

The future construction must introduce a new component; the existing
`scdmp.uav_sp_order_value.r02.full_host` is task-specific to a consumed object
and is not compatible with this plant.

Proposed new shared identity:

```text
component=scdmp.tbcc_order_value.r02.full_host
loader_key=scdmp_tbcc_order_value_r02_full_host
host=QUAD-UAV-PALLET-GANTRY-24P5M-v1
production_backend=cpp
batch_api=true
full_reset_step_cpp=true
python_fallback=false
```

Before any production runner is written, construction must freeze and accept:

1. A task-specific C++ host with version and `sizeof` witnesses plus batched
   reset, observation-conditioned renewal/step, terminal and close calls.
   C++ owns setup maps, latent support assignment, all primitive transitions,
   failure/docking precedence, reward accumulation and terminal endpoint
   counters. Python may only materialize already frozen deterministic
   coordinates/tapes and lifecycle metadata.
2. An interactive fixed-width lane contract. Inactive/absorbed lanes remain
   masked in the same batch so late absorption cannot collapse production into
   scalar Python stepping or shift an RNG address. Candidate ABI calls reject
   malformed widths, shapes, nonfinite inputs, illegal actions, post-close use
   and cross-session handles.
3. A source/toolchain/runtime-ABI keyed candidate loader with a process-local
   warm cache, durable artifact identity and no alternate build root or Python
   fallback. The direction preflight must cross-check the shared guard receipt,
   card, source, ABI sizes and artifact identity before any master or model.
4. A fixture-only Python oracle for exact event maps, transition, absorption,
   endpoint and tape conformance. It is never a production environment or
   rollout path.
5. Batched Torch actor/critic and score computation. Python orchestration may
   form tensor batches and own sealed lifecycle/checkpoint metadata, but no
   production entry point may contain a scalar Python environment or rollout
   loop.

Natural production lane groups implied by the card are:

| Stage | Natural lane group | Required semantics |
|---|---:|---|
| foundation training | 12 per replicate/update | 3 lanes per `(k,graph)` cell; one model |
| foundation competence | 120 per replicate/regime | 60 per graph; switch cells 30 per `(graph,time)` |
| opportunity | 144 per `(replicate,k,state)` | `2 graphs x 18 actions x 4 tapes`; one foundation |
| order-stage training | 12 per replicate/arm/update | paired addresses across three arms; separate models |
| final evaluation | 120 per replicate/controller/regime | deterministic argmax; fixed complete cell |

The native host must functionally support widths 1, 8 and 32 and the natural
12/120/144 groups. Width 1 is conformance-only unless measurement shows it is
efficient. A provisional production minimum of 8 is appropriate, but the
shared registry minimum and exact worker/chunk contract must not be frozen
until the measured sweep is complete. Four outer workers with one Torch thread
each are the prospective ceiling; 1/2/4-worker equivalence and resource
measurements are mandatory.

## Mandatory end-to-end efficiency acceptance

No baseline or optimized measurement exists in this definition-only stage.
Consequently:

```text
efficiency_review=NOT_YET_EXECUTED_DEFINITION_ONLY
chain_coverage=environment|loader|batch|forward_backward|rollout|evaluation|io|resume
lease_readiness=WITHHOLD
```

A later construction acceptance must produce one result-blind packet containing
all of the following before coordinates or a heavy lease:

- process-cold build/load, first warm-cache load and repeated process-local
  loader calls, with exact source/build/artifact/ABI identity;
- oracle-versus-native reset/renew/terminal equality and native steady
  transitions/second at widths 1, 8, 12, 32, 120 and 144 where applicable;
- batched policy forward and foundation/order-stage forward-backward/optimizer
  throughput at the natural widths, including active-lane masking;
- one complete foundation-update, competence-cell, opportunity-state,
  order-update and final-evaluation-cell benchmark, then a registered-work
  full-panel projection;
- 1/2/4-worker CPU utilization, peak RSS and deterministic equivalence;
- checkpoint generation/commit throughput, competence/opportunity atomic
  publication, cold resume scan and same-coordinate frontier recovery;
- scratch/durable bytes and write amplification for 24 foundation, 72 adapter
  and 96 total checkpoints; and
- baseline fixture-oracle versus optimized native outputs, RNG address/order,
  endpoint counts, checkpoint identities and complete-stage counts.

The dominant bottleneck is not yet measured. Prospective risks are the
15,829,632 policy-query ceiling and 129,024 AdamW steps rather than the simple
primitive plant arithmetic. If the measured chain projects above the accepted
24--72 hour four-worker wall envelope because of loader re-entry, scalar
Python rollout, undersized policy batches or checkpoint write amplification,
the engineering conclusion is `REPAIR_REQUIRED`; no heavy lease is requested.

Rollback nodes are the candidate ABI/source, shared registry declaration,
process-local cache, accepted batch widths, 1/2/4-worker choice, opportunity
chunk size and checkpoint/I/O chunking. Rollback always fails closed to an
earlier accepted native configuration; it never enables a Python production
fallback or changes coordinates, RNG order, rows, horizon, treatment or
observable.

## Workload and full prospective cost

The registered ceilings are arithmetically consistent when the two switch
times are included:

| Stage | Episodes/rollouts | Primitive slots | Maximum policy queries | AdamW steps | Checkpoints |
|---|---:|---:|---:|---:|---:|
| foundation training | 46,080 | 16,773,120 | 2,465,280 | 46,080 | 24 |
| foundation competence | 17,280 | 6,289,920 | 768,960 | 0 | 0 |
| opportunity | 110,592 | 40,255,488 | 4,313,088 | 0 | 0 |
| order-stage training | 82,944 | 30,191,616 | 4,437,504 | 82,944 | 72 |
| final evaluation | 86,400 | 31,449,600 | 3,844,800 | 0 | 0 |
| **complete conditional ceiling** | **343,296** | **124,959,744** | **15,829,632** | **129,024** | **96** |

For each evaluation controller/replicate, fixed query counts are
`73,34,52,28`; a switch at `n=91` uses 34 queries and the same direction at
`n=273` uses 46, so each balanced switch regime averages 40. The six-regime
sum is therefore 267 queries per controller/replicate cell, matching the card's
ceiling. No dummy or post-absorption query is required.

Independent prospective cost acceptance:

```text
engineering=24--40 experienced engineer-days
cpu=80--240 core-hours including native construction benchmarks and the conditional full panel
four_worker_wall=24--72 elapsed hours after construction, subject to measured gate
ram=12 GiB minimum; 20 GiB preferred
scratch=10 GiB maximum
durable=4 GiB maximum
gpu=not required
```

This remains the same resource class as the EM planning envelope. Early
prerequisite nonpass can reduce realized work but cannot be used to weaken the
construction, benchmark, atomicity or maximum-resource plan.

## Shared-registry and next-authority request

A new shared component is required. No TBCC or
`QUAD-UAV-PALLET-GANTRY-24P5M-v1` entry currently exists in
`envs.native.production_backend`.

Operational Root should request the shared backend CM only after Portfolio
authorizes construction. That request should reserve
`scdmp.tbcc_order_value.r02.full_host` and require candidate-local native host,
ABI, malformed-input, width-sweep and result-blind benchmark evidence before
shared registration. The shared loader must call only the candidate-local
source-keyed loader; it must not call a coordinate, activity, lease or
production helper. Registration supplies no science, identity, activity or
lease authority.

Current local fence: preserve the Pro-closed card and consumed r02 artifacts;
do not create source, registry changes, build, fixture, benchmark, identity,
coordinate, model, checkpoint, rollout, result or lease. The next decision is
Portfolio construction investment or no current construction; this CM makes no
portfolio recommendation.
