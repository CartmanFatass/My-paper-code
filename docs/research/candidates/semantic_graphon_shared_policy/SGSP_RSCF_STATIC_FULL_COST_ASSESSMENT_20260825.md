# SGSP RSCF static full-cost assessment

```text
artifact_role=cm_documentary_static_full_cost_assessment
direction_id=semantic_graphon_shared_policy
logical_identity=CM-semantic_graphon_shared_policy
assessment_date=2026-08-25
scope_ref=docs/research/candidates/semantic_graphon_shared_policy/SGSP_RSCF_STATIC_FULL_COST_ASSESSMENT_HANDOFF_20260825.md#engineering-request-cm-static-full-cost-assessment
scope_sha256=99f02e729b5924ec2e9403f3cade56da266a23f7b4115fdaaaf09cfd2de29fb1
research_state_revision=4
research_state_sha256=1449770b5ad305eef8154b2dca37ec1cb770f19fc665d686ff438a8b0e287166
rscf_revision=SGSP_RG2Z_ROLE_SAMPLED_CF_R01
question_sha256=70b2ed242ca4fcee5c54c00e814d336cbccc945a45252278093e4955f98d52cf
evidence_set_sha256=6b7c08b8b459e644467a4e6fe827f098717d8049acdea0da3b6dab064c21186e
portfolio_sha256=7d5353ab63a8ead4f90f6cb565df9620f68fb605d27150e2e8315c6ec49df86a
registry_revision=9
registry_sha256=d02edd6b91c1fb103964f1f5b5a72c5f4d1fb0c0a651ba7b792bb2d1f2d685ee
direction_sha256=2fb5239b02eff2ca71421a44612ceac3539c3e0638c7fa9adeccb763e09fdb78
rscf_card_sha256=1af5b6add80af436ab7c2ecc334673f15cbddae3d18e2ac6fe7b726e8b97eaa4
cca_definition_card_sha256=1fd0a7446365f109b94ae2ec1761656b7b99c8127df3ea103388ff1ca7e38dcb
assessment_mode=symbolic_documentary_read_only
packet_status=COMPLETE_WITH_VISIBLE_STATIC_GAPS
next_owner=ROOT
next_action=PORTFOLIO_INTAKE_STATIC_FULL_COST_ASSESSMENT
```

## 1. Return boundary and conclusion

This packet is the one terminal CM return requested by the frozen handoff. It
contains feasibility, bindability, observability, risk, uncertainty, and
prospective full-cost information only. It does not select, reject, recommend,
authorize, or veto construction, and it does not alter the direction's
scientific status.

The permitted documentary evidence is sufficient to enumerate the required
semantic interfaces, logical-work counts, audit predicates, prospective work
packages, resource categories, dependency structure, and conditional cost
formulas. It is not sufficient to bind those requirements to an implementation
or to produce finite person-workday, elapsed-time, compute, memory, storage, or
opportunity-cost ranges. Every such dimension is therefore reported as
`NOT_STATICALLY_ESTIMABLE` with the missing facts below. These are visible
preparation gaps, not defects in the direction and not automatic triggers for
measurement, construction, compute, external review, or another engineering
assignment.

There is no newly discovered scientific ambiguity. The unresolved items are
implementation, observability, resource, productivity, and accounting inputs
that the request deliberately excluded. The next owner is `ROOT` for Portfolio
intake of this packet.

No source, test, build, benchmark, hardware query, technical runtime,
stochastic/scientific object, provider operation, empirical value, or lease
was accessed, created, or performed for this assessment. No worktree was
created, and no commit, push, integration, or other Git effect was performed. No
selector, coordinate, branch history, trace, digest, certificate, partial
value, or other runtime object was generated or inspected.

## 2. Evidence and estimation rules

### 2.1 Permitted evidence

The sole content authority used for the assessment is the frozen handoff bound
above, together with its current research-state identity supplied at dispatch.
The handoff's references to the direction, RSCF card, and definition-only CCA
card are identity and documentary-fact bindings; those scientific coordinates
were not opened for this assignment.

The handoff provides these logical-accounting facts:

| Symbol | Documentary fact | Status |
| --- | ---: | --- |
| $N_Q$ | 15,728,640 all-legal RSCF Q entries | Exact documentary count |
| $N_A$ | 11,010,048 new alternative continuations | Exact documentary count |
| $N_E$ | 91,471,872 total base-plus-branch-plus-evaluation environment slots | Exact documentary count |
| $N_D$ | 966,647,808 learned decisions | Exact documentary count |
| $N_B$ | 24,576 full-batch backward calls | Exact documentary count |
| $N_Q^{CCA}/N_Q$ | 48 | Exact documentary ratio |
| $N_A^{CCA}/N_A$ | 48 | Exact documentary ratio |
| $N_E^{CCA}/N_E$ | approximately 37.77 | Approximate documentary ratio; source precision is not supplied |
| $N_D^{CCA}/N_D$ | approximately 38.59 | Approximate documentary ratio; source precision is not supplied |

Counts on different rows are not assumed additive. The handoff does not give an
incidence/overlap map showing which decision, Q, environment-slot, and backward
work is already contained in another row. Resource formulas therefore keep
these drivers separate unless a future authorized accounting map proves a
non-overlapping decomposition.

### 2.2 Excluded advisory provenance

The handoff identifies `100--500` CPU core-hours and `18--30` CM workdays as
pre-CM advisory provenance only. This packet does not accept, reject, validate,
calibrate to, target, benchmark against, repeat as a substitute estimate, or
use either range as a lease, threshold, rule, recommendation, or veto. Neither
range enters any formula or conclusion below.

### 2.3 Status vocabulary

| Status | Meaning in this packet |
| --- | --- |
| `DOCUMENTED_REQUIREMENT` | The frozen handoff names the semantic obligation or exact logical fact. |
| `CONDITIONAL_STATIC_STRATEGY` | A prospective method is semantics-preserving only if every stated precondition is proved; it is not selected or authorized. |
| `NOT_STATICALLY_ESTIMABLE` | The permitted documents lack one or more facts required for a finite auditable value or implementation binding. |

`NOT_STATICALLY_ESTIMABLE` is the result for an ungrounded quantitative
dimension. An unconstrained expression, zero-to-infinity interval, or copied
advisory range is not presented as a conservative estimate.

### 2.4 Uncertainty method

1. Exact documentary counts and the two exact 48-fold ratios have arithmetic
   certainty relative to the frozen handoff; this is not empirical validation.
2. Ratios labeled approximately retain that qualifier. Their rounding interval
   and source precision are absent, so no conservative numeric difference range
   is derived from them.
3. Labor and resource dimensions have dominant structural/epistemic uncertainty:
   implementation inventory, reuse, hardware, service rates, topology,
   retention, staffing, and productivity are absent. A finite lower and upper
   bound cannot be justified, so the output is `NOT_STATICALLY_ESTIMABLE` rather
   than a fabricated wide interval.
4. If Root later authorizes a separate assessment with grounded inputs, the
   appropriate method is dependency-aware bottom-up interval accounting. Each
   non-overlapping work package would receive disclosed low/high bounds; totals
   would use conservative interval sums plus an explicit integration/risk
   allowance. No probabilistic independence, cancellation, or expected-value
   assumption is made here.

## 3. Static feasibility and component assessment

The requirements below are bindable as documentary predicates. Binding them to
actual fields, APIs, ownership boundaries, or observables is
`NOT_STATICALLY_ESTIMABLE` because source and runtime coordinates are outside
scope and the handoff supplies no implementation inventory.

### 3.1 Snapshot/restore

#### Documentary state/interface inventory

A prospective branch origin must preserve or bind all state categories named or
necessarily referenced by the handoff:

- the complete mutable environment state at the pretransition boundary;
- the focal and teammate current-action identities, with only the focal action
  replaceable for the counterfactual arm;
- observation, message, and recurrent-controller state needed to resume the
  closed loop;
- legal-action-distribution state or the complete inputs needed to recompute it;
- remaining common-future-tape identity and address/cursor state;
- factual-episode, role, arm-origin, slot, and horizon identity;
- immutable pre-update parameter identity, referenced without mutation across
  factual and alternative continuations; and
- optimizer/projection lifecycle identity needed to preserve the one inherited
  optimization opportunity and atomic completion rule.

This is the complete category-level inventory supportable from the handoff. A
field-level inventory, alias/ownership map, serialization boundary, hidden
mutable subsystem list, and restore order are `NOT_STATICALLY_ESTIMABLE` because
no state schema or implementation inventory is permitted or supplied.

#### Prospective work packages

| Work package | Required static contract | Dependencies | Main prospective risk | Feasibility / workdays |
| --- | --- | --- | --- | --- |
| State-boundary specification | Identify the instant immediately before the ordinary current transition and every mutable owner at that instant. | Complete field/ownership inventory | A hidden mutable owner makes restore inexact. | Interface requirement documented; implementation binding and person-workdays `NOT_STATICALLY_ESTIMABLE` (missing field/owner inventory and reuse evidence). |
| Capture contract | Preserve complete state without changing parameters, tape identity, or factual state. | State-boundary specification | Shallow copies, aliasing, asynchronous mutation, or nondeterministic external state. | `NOT_STATICALLY_ESTIMABLE` (missing representation, sizes, copy semantics, and existing facilities). |
| Restore contract | Re-establish the exact pretransition state before each arm and leave no prior-arm residue. | Capture contract; lifecycle ordering | Incomplete reset or order-dependent residue. | `NOT_STATICALLY_ESTIMABLE` (missing restore API and subsystem reset semantics). |
| Parameter-identity binding | Prove one immutable pre-update parameter identity for every arm. | Parameter ownership map | Mutation or accidental use of post-update parameters. | Predicate documented; observable binding and person-workdays `NOT_STATICALLY_ESTIMABLE`. |
| Factual-suffix/tape binding | Preserve the exact remaining common tape and factual suffix identity. | Address model; branch scheduler | Cursor drift, resampling, or arm-specific future inputs. | Predicate documented; implementation and person-workdays `NOT_STATICALLY_ESTIMABLE`. |
| Restore conformance audit | Prospectively compare all relevant identities before and after a restore without producing a runtime trace in this assignment. | All preceding contracts | An incomplete observable set can falsely certify equality. | Audit requirement documented; bindability and person-workdays `NOT_STATICALLY_ESTIMABLE`. |

The handoff does not prove that snapshot/restore is constructible on any chosen
implementation. It specifies what exactness would mean. Construction
feasibility, byte cost, copy count, latency, and labor remain
`NOT_STATICALLY_ESTIMABLE`.

### 3.2 Closed-loop branch construction

The prospective branch host must preserve this order and scope:

1. begin from the exact pretransition origin;
2. replace only the focal actor's current action for the selected legal arm;
3. retain factual teammate current actions;
4. apply the ordinary current transition;
5. from the next slot through slot 11, recompute observations, messages,
   recurrent states, and legal distributions in closed loop;
6. consume the identical remaining future tape;
7. cover every legal current action and every frozen logical entry; and
8. make branch execution order irrelevant to the resulting logical object.

| Prospective component | Static responsibility | Dependency | Risk / missing evidence | Feasibility / workdays |
| --- | --- | --- | --- | --- |
| Origin binder | Bind factual episode, public role, selected origin, slot, arm, and horizon identities. | Selector contract; snapshot boundary | Coordinate schema and actual bindable fields are absent. | `NOT_STATICALLY_ESTIMABLE` for implementation and person-workdays. |
| Focal-only intervention boundary | Change exactly the focal current action and no teammate or state input. | Legal-action interface; origin binder | A shared action container or side effect can broaden the intervention. | Predicate documented; actual diff boundary and person-workdays `NOT_STATICALLY_ESTIMABLE`. |
| Ordinary-transition adapter | Invoke the same transition law used by the factual path. | Exact restore; immutable parameters | A separate code path can change semantics. | Implementation reuse and person-workdays `NOT_STATICALLY_ESTIMABLE`. |
| Closed-loop recurrence host | Recompute every required observation, message, recurrent state, and legal distribution through the remaining horizon. | Transition adapter; complete state | Open-loop reuse or stale derived state would violate the definition. | Logical duty documented; constructibility and person-workdays `NOT_STATICALLY_ESTIMABLE`. |
| Common-tape address binder | Hold future-tape identity and addresses equal across arms. | Factual-suffix binding | Resampling, cursor drift, or worker-local variation. | Bindability and person-workdays `NOT_STATICALLY_ESTIMABLE`. |
| Complete legal-arm enumerator | Cover all legal current actions without pruning or substitution. | Legal distribution/action-set interface | Dynamic legality or incomplete enumeration can change $N_Q$. | Count obligation documented; interface and person-workdays `NOT_STATICALLY_ESTIMABLE`. |
| Order-invariant scheduler | Preserve the same logical outputs under any permitted processing order. | Restore isolation; cache key completeness | Shared mutation, reduction order, or incomplete cache keys. | Static predicate documented; safe schedule and person-workdays `NOT_STATICALLY_ESTIMABLE`. |

The exact counts show the size of the frozen logical object, not the time or
memory per continuation. Closed-loop construction feasibility and cost are
therefore `NOT_STATICALLY_ESTIMABLE` without selecting or testing a construction,
which this packet does not do.

### 3.3 Stopped-target and loss integration

The prospective integration boundary must keep all of these handoff-defined
parts intact:

- the stopped Q vector and its policy-weighted baseline;
- the stopped factual-return difference;
- equal role weighting;
- all-agent/all-slot entropy;
- the retained critic;
- one full-batch backward call per frozen opportunity;
- global clipping;
- the complete projection lifecycle; and
- every frozen checkpoint opportunity.

The prospective dependency map binds branch completion, stopped-object
assembly, role aggregation and retained terms, one full-batch differentiation
opportunity, global clipping, projection, the inherited optimizer opportunity,
and every checkpoint opportunity. It does not infer an internal order that the
handoff does not supply. This is a contract map, not an executed graph or
selected implementation.

| Prospective interface | Preservation requirement | Main risk / missing fact | Feasibility / workdays |
| --- | --- | --- | --- |
| Stopped-vector assembler | Include every legal arm on the frozen stopped horizon. | Shapes, data ownership, and assembly API are absent. | `NOT_STATICALLY_ESTIMABLE`. |
| Policy-weighted baseline interface | Use the frozen weighting without changing arm opportunity. | Policy-output interface and identity binding are unavailable. | `NOT_STATICALLY_ESTIMABLE`. |
| Factual-difference interface | Bind the exact factual counterpart and stopped-return identity. | Factual reference and stopped-return observable are unavailable. | `NOT_STATICALLY_ESTIMABLE`. |
| Equal-role aggregator | Preserve equal public-role weighting. | Role cardinality/layout and reduction implementation are absent. | `NOT_STATICALLY_ESTIMABLE`. |
| Entropy/critic retention boundary | Retain all-agent/all-slot entropy and the critic exactly as specified. | Existing loss decomposition and reuse are unavailable. | `NOT_STATICALLY_ESTIMABLE`. |
| Full-batch backward boundary | Preserve exactly 24,576 logical full-batch calls and no split optimization opportunity. | Working-set size, differentiation topology, and device path are absent. | `NOT_STATICALLY_ESTIMABLE`. |
| Global clip/projection/optimizer/checkpoint boundary | Preserve global clipping, the complete projection lifecycle, the exact inherited optimizer opportunity, and every checkpoint opportunity without inventing an unprovided order. | Optimizer ownership/state and projection/checkpoint interfaces and ordering are absent. | `NOT_STATICALLY_ESTIMABLE`. |

No target, loss tensor, differentiation graph, optimizer state, or policy output
was created or inspected. Static source binding, construction feasibility,
working-set size, and person-workdays are all `NOT_STATICALLY_ESTIMABLE`.

### 3.4 Selector, coupling, bindability, and audit matrix

“Predicate” below means a prospective documentary audit condition only. No
coordinate, trace, digest, certificate, or partial result was generated.

| Required invariant | Prospective static predicate | Documentary status | Actual bindability / observability and gap |
| --- | --- | --- | --- |
| One origin per public role and factual episode | Exactly one selected origin is associated with each required role/episode pair. | `DOCUMENTED_REQUIREMENT` | `NOT_STATICALLY_ESTIMABLE`: role/episode key schema and selection surface are absent. |
| Antithetic slot pairing | Every required paired slot obeys the frozen antithetic relation. | `DOCUMENTED_REQUIREMENT` | `NOT_STATICALLY_ESTIMABLE`: pairing map and slot observable are absent. |
| Role-local selection | A role's selected origin is derived only from its permitted role-local selection law. | `DOCUMENTED_REQUIREMENT` | `NOT_STATICALLY_ESTIMABLE`: selector inputs and ownership boundary are absent. |
| Identical arm-origin coordinates | All arms compared for one origin share identical origin identities. | `DOCUMENTED_REQUIREMENT` | `NOT_STATICALLY_ESTIMABLE`: coordinate representation and equality observable are absent. |
| Common-tape identity | Every arm uses the identical remaining-tape identity and address sequence. | `DOCUMENTED_REQUIREMENT` | `NOT_STATICALLY_ESTIMABLE`: tape/address interface is absent. |
| Branch-order identity | Permuting prospective processing order cannot change the frozen logical object. | `DOCUMENTED_REQUIREMENT` | `NOT_STATICALLY_ESTIMABLE`: mutable sharing, reduction, and scheduler semantics are absent. |
| Immutable parameters | All arms use one pre-update parameter identity. | `DOCUMENTED_REQUIREMENT` | `NOT_STATICALLY_ESTIMABLE`: parameter lifecycle and identity surface are absent. |
| Focal-only intervention | The arm differs at the current boundary only in the focal legal action. | `DOCUMENTED_REQUIREMENT` | `NOT_STATICALLY_ESTIMABLE`: action/state ownership and diff surface are absent. |
| Factual-return identity | The factual comparator is the exact stopped factual counterpart for that origin. | `DOCUMENTED_REQUIREMENT` | `NOT_STATICALLY_ESTIMABLE`: factual-reference binding is absent. |
| Closed-loop recurrence | All downstream observations, messages, recurrent states, and legal distributions are recomputed through slot 11. | `DOCUMENTED_REQUIREMENT` | `NOT_STATICALLY_ESTIMABLE`: recurrence and derived-state interfaces are absent. |
| No leakage | No alternative-arm information enters factual inputs, teammate current actions, selector inputs, or another arm. | `DOCUMENTED_REQUIREMENT` | `NOT_STATICALLY_ESTIMABLE`: information-flow/alias map is absent. |
| Exact inherited optimizer and checkpoint opportunities | Full logical work feeds the one inherited full-batch opportunity without pruning or extra updates, and every frozen checkpoint opportunity is preserved. | `DOCUMENTED_REQUIREMENT` | `NOT_STATICALLY_ESTIMABLE`: optimizer, accumulation, and checkpoint lifecycles are absent. |
| Complete logical counts | Completed accounting equals $N_Q$, $N_A$, $N_E$, $N_D$, and $N_B$ without treating overlapping categories as additive. | Exact counts documented | `NOT_STATICALLY_ESTIMABLE`: prospective counters and their binding points are absent. |
| Atomic completion before seed evaluability | No seed-level object becomes evaluable before all required logical work and audits complete atomically. | `DOCUMENTED_REQUIREMENT` | `NOT_STATICALLY_ESTIMABLE`: frontier, completion, publication, and failure-recovery lifecycle are absent. |

Prospective audit surfaces comprise invariant definitions, binding adapters,
frontier/completion accounting, fail-closed publication gating, and a
certificate contract. Their implementation, test matrix, review effort,
retention footprint, and person-workdays are `NOT_STATICALLY_ESTIMABLE` because
no observable inventory, failure model, or existing audit reuse is supplied.

### 3.5 Streaming, batching, exact cache, and sharding

Every strategy in this table is conditional. None changes, prunes, approximates,
or reweights the frozen logical schedule, and none is selected or implemented.

| Prospective strategy | Semantics-preserving preconditions | Cost sensitivity | Static result |
| --- | --- | --- | --- |
| Bounded streaming | Every logical entry is eventually processed; complete state and identity travel with it; atomic completion prevents early evaluability. | Can lower resident retained-entry memory; can increase I/O, serialization, and recomputation. | `CONDITIONAL_STATIC_STRATEGY`; batch size, memory reduction, I/O, elapsed time, and workdays `NOT_STATICALLY_ESTIMABLE`. |
| Full logical batching | Batches partition rather than prune the schedule; recurrence, horizon, factual identity, role/arm opportunity, full-batch optimizer semantics, and every checkpoint opportunity remain exact. | Trades per-worker memory against launch/coordination overhead. | `CONDITIONAL_STATIC_STRATEGY`; safe batch size and costs `NOT_STATICALLY_ESTIMABLE`. |
| Exact memoization/cache | The key includes complete state identity, remaining-tape address, recurrence state, horizon, factual identity, arm opportunity, immutable parameters, and every branch-order-sensitive input; hits are exact. | Trades CPU/accelerator work for RAM or storage and key/lookup overhead. | `CONDITIONAL_STATIC_STRATEGY`; hit rate, entry size, capacity, and benefit `NOT_STATICALLY_ESTIMABLE`. |
| Deterministic sharding | Shards are a complete disjoint partition; each has isolated mutable state; merge/accounting is order invariant and atomic. | May reduce elapsed time while multiplying live memory, scratch, host, I/O, and coordination demand. | `CONDITIONAL_STATIC_STRATEGY`; shard count and safe concurrency `NOT_STATICALLY_ESTIMABLE`. |
| Immutable sharing or copy-on-write | Shared objects are proved immutable and every mutation is isolated before write. | May reduce duplication; faulting/copy behavior can increase latency and memory. | `CONDITIONAL_STATIC_STRATEGY`; representation support and savings `NOT_STATICALLY_ESTIMABLE`. |
| Lossless serialization/compression | Round-trip preserves exact state and identities; no lossy numeric or semantic transform is allowed. | Trades CPU and latency for scratch/retained bytes. | `CONDITIONAL_STATIC_STRATEGY`; ratio, throughput, and workdays `NOT_STATICALLY_ESTIMABLE`. |
| Exact recomputation instead of retention | Recomputation uses identical immutable parameters, complete state, tape addresses, and order-invariant semantics. | Can lower retained storage while increasing host and compute time. | `CONDITIONAL_STATIC_STRATEGY`; exactness, break-even point, and costs `NOT_STATICALLY_ESTIMABLE`. |

The handoff provides no proof that any strategy is available on a prospective
implementation. In particular, logical-count reductions are forbidden; only
physical scheduling and exact representation may change.

## 4. Complete prospective labor

### 4.1 Non-overlapping work-breakdown basis

Person-workdays are separated from calendar time. Let each $W_i$ denote total
person-workdays for the named, non-overlapping package after explicitly
allocating design, implementation, focused tests, documentation, and package-
local review exactly once. End-to-end construction, system tests, final review,
packaging, and integration rows below exclude work already assigned to a
component row.

| Symbol | Prospective component | Principal dependencies | Missing facts required for a range | Person-workday range |
| --- | --- | --- | --- | --- |
| $W_{SR}$ | Snapshot/restore contract and implementation | Complete mutable-state and ownership inventory | Fields, representations, reuse, copy/restore mechanism, engineer productivity | `NOT_STATICALLY_ESTIMABLE` |
| $W_{BH}$ | Closed-loop branch host | $W_{SR}$; transition, recurrence, legality, and tape interfaces | Existing APIs, control flow, horizon representation, reuse, failure handling | `NOT_STATICALLY_ESTIMABLE` |
| $W_{TL}$ | Stopped-target/loss integration | $W_{BH}$; loss/optimizer/projection ownership | Shapes, aggregation interface, differentiation path, retained-term reuse | `NOT_STATICALLY_ESTIMABLE` |
| $W_{SC}$ | Selectors and coupling | Origin/role/slot identity model | Selector interface, pairing map, coupling representation, reuse | `NOT_STATICALLY_ESTIMABLE` |
| $W_{OA}$ | Observability and atomic audits | All semantic contracts | Observable inventory, failure model, counter bindings, publication gate | `NOT_STATICALLY_ESTIMABLE` |
| $W_{RF}$ | Runner, frontier, and certificate surfaces | $W_{OA}$; failure/recovery lifecycle | Existing orchestration, persistence, atomicity, certificate schema | `NOT_STATICALLY_ESTIMABLE` |
| $W_{BC}$ | Streaming, batching, exact cache, and sharding | Stable semantics and state-size model | Memory model, cache keys/sizes, I/O path, safe topology | `NOT_STATICALLY_ESTIMABLE` |
| $W_{CO}$ | End-to-end construction/assembly not counted above | All component implementations | Integration topology and pre-existing assembly surfaces | `NOT_STATICALLY_ESTIMABLE` |
| $W_{TE}$ | Unit, invariant, failure, integration, and full logical-count tests | Implemented observables and components | Test framework/reuse, fixture design, oracle availability, matrix size | `NOT_STATICALLY_ESTIMABLE` |
| $W_{RV}$ | Independent engineering and semantic-preservation review | Complete change and evidence packet | Review policy, reviewer count, defect/rework model | `NOT_STATICALLY_ESTIMABLE` |
| $W_{PK}$ | Packaging and operator-facing documentation | Stable runner and dependency set | Packaging target, distribution surface, documentation delta | `NOT_STATICALLY_ESTIMABLE` |
| $W_{IN}$ | Root-owned candidate verification and integration support | Accepted focused evidence and owned paths | Candidate shape, conflict state, integration procedure/rework | `NOT_STATICALLY_ESTIMABLE` |

The complete labor identity is

$$
W_{total}=W_{SR}+W_{BH}+W_{TL}+W_{SC}+W_{OA}+W_{RF}+W_{BC}+W_{CO}+W_{TE}+W_{RV}+W_{PK}+W_{IN}+W_{risk},
$$

where $W_{risk}$ is an explicit, non-duplicative allowance for realized risks
not already included in a package. Neither a component interval nor a grounded
risk allowance exists in the permitted evidence, so $W_{total}$ is
`NOT_STATICALLY_ESTIMABLE`.

### 4.2 Staffing, sequencing, reuse, and risk assumptions

- **Staffing:** No role count, skill mix, availability, productivity, or hours-
  per-workday convention is supplied. Staffing, person-workday normalization,
  and calendar conversion are `NOT_STATICALLY_ESTIMABLE`.
- **Sequencing:** The documentary dependency spine is state/identity contract;
  snapshot/restore and selector/coupling binding; branch host; stopped/loss
  integration; observability/atomic lifecycle; runner/frontier/certificate;
  batching/cache; assembly; tests; review; packaging; Root integration.
  Cross-cutting audit design can be specified alongside components, but no
  implementation concurrency is declared safe.
- **Reuse:** No existing component is assumed reusable because source access is
  forbidden. Reuse fraction is `NOT_STATICALLY_ESTIMABLE`, including whether a
  nominally similar factual runner, snapshot facility, loss path, or cache has
  the required exact semantics.
- **Dependencies:** Actual APIs, owners, language boundaries, third-party
  constraints, packaging targets, and reviewer availability are absent.
- **Risk allowance:** Principal risks are hidden mutable state, incomplete
  restore, parameter/tape drift, focal-intervention leakage, stale recurrence,
  dynamic legality mismatch, incomplete cache identity, branch-order effects,
  premature evaluability, full-batch working-set pressure, and integration
  rework. Probability and workday impact distributions are not supplied;
  $W_{risk}$ is `NOT_STATICALLY_ESTIMABLE`.
- **Uncertainty:** A numerical three-point or probabilistic labor model would be
  unsupported. The packet reports structural gaps instead of assigning
  confidence percentages.

## 5. Compute, host resources, and elapsed time

### 5.1 Resource accounting categories

For a future authorized plan, let prospective phase $j$ use $C_j$ provisioned
CPU cores, $G_j$ provisioned accelerator devices, $M_j$ provisioned hosts, and
elapsed duration $T_j$ hours. The separate provisioned allocation identities
are

$$
H_{CPU,prov}=\sum_j C_jT_j,\qquad
H_{ACCEL,prov}=\sum_j G_jT_j,\qquad
H_{HOST}=\sum_j M_jT_j.
$$

If utilization $u_j$ were independently bound, busy CPU or accelerator hours
would instead integrate provisioned capacity times utilization. Busy and
provisioned accounting must be labeled separately, and heterogeneous CPU,
accelerator, or host classes must remain class-labeled rather than silently
aggregated. Utilization cannot merge CPU core-hours, accelerator-hours, or
host-hours. No $C_j$, $G_j$, $M_j$, $T_j$, $u_j$, service-rate, or accounting-
basis value is grounded here.

| Required input/category | Frozen support | Static assessment |
| --- | --- | --- |
| CPU hardware class | None | `NOT_STATICALLY_ESTIMABLE`; instruction set, core performance, memory bandwidth, and topology are missing. |
| Accelerator class and usefulness | None | `NOT_STATICALLY_ESTIMABLE`; no accelerator path, kernel coverage, precision contract, or transfer model is supplied. |
| Device count | None | `NOT_STATICALLY_ESTIMABLE`. |
| Host class/count | None | `NOT_STATICALLY_ESTIMABLE`. |
| Process/thread/worker model | None | `NOT_STATICALLY_ESTIMABLE`; isolation and shared-state safety are also unbound. |
| CPU utilization | None | `NOT_STATICALLY_ESTIMABLE`. |
| Accelerator utilization | None | `NOT_STATICALLY_ESTIMABLE`. |
| Per-slot, per-decision, per-Q, and per-backward service demands | Logical counts only | `NOT_STATICALLY_ESTIMABLE`; operation overlap and time/energy per primitive are missing. |
| CPU core-hours | Formula only | `NOT_STATICALLY_ESTIMABLE`. |
| Accelerator-hours | Formula only | `NOT_STATICALLY_ESTIMABLE`; this does not imply zero or require an accelerator. |
| Total host-hours | Formula only | `NOT_STATICALLY_ESTIMABLE`. |

The exact logical counts can be used as separate sensitivity drivers. For
example, a hypothetical environment-slot service demand scales with $N_E$, and
a hypothetical full-batch-call service demand scales with $N_B$. They cannot be
summed into a full cost until a non-overlap incidence map and per-unit service
demands are supplied. No throughput, timing, or benchmark value was imported or
created.

### 5.2 Safe concurrency conditions and sensitivities

For a proposed worker count $k$ to be statically memory- and resource-safe, an
authorized future plan would have to prove at least

$$
kr_{worker}+r_{shared}+r_{margin}\le r_{host},
$$

$$
kv_{worker}+v_{shared}+v_{margin}\le v_{available},
$$

$$
ks_{worker}+s_{shared}+s_{margin}\le s_{scratch},
$$

and show that aggregate I/O demand, file/socket/process limits, worker isolation,
common-tape identity, branch-order invariance, cache exactness, atomic frontier
completion, and host/device topology all remain within explicit safe bounds.
Here $r$, $v$, and $s$ denote RAM, VRAM, and scratch requirements/capacities;
none has a supplied numeric value.

| Prospective concurrency case | Sensitivity | Safe level | Elapsed-time range |
| --- | --- | --- | --- |
| One CPU worker | Avoids inter-worker sharing but still requires one complete bounded working set and sufficient scratch/I/O. | `NOT_STATICALLY_ESTIMABLE`; even $k=1$ lacks a footprint and host capacity bound. | `NOT_STATICALLY_ESTIMABLE`; service demands and host class are missing. |
| Multiple CPU workers on one host | Ideal parallel work may fall with $k$; RAM, scratch, process count, synchronization, and I/O pressure rise with $k$. | `NOT_STATICALLY_ESTIMABLE`; isolation, footprint, bandwidth, and process limits are missing. | `NOT_STATICALLY_ESTIMABLE`. |
| Multiple workers sharing accelerator device(s) | Potential device throughput competes with VRAM, transfers, launch overhead, and deterministic/full-batch constraints. | `NOT_STATICALLY_ESTIMABLE`; accelerator path, VRAM footprint, device count, and precision semantics are missing. | `NOT_STATICALLY_ESTIMABLE`. |
| Multiple hosts with deterministic shards | Potential elapsed reduction trades against duplicated shared state, retained identity, network/I/O, merge, and atomic completion costs. | `NOT_STATICALLY_ESTIMABLE`; shardability, network, host homogeneity, and merge semantics are missing. | `NOT_STATICALLY_ESTIMABLE`. |

There is therefore no statically supportable numeric concurrency case in the
permitted evidence. No concurrency level is proposed, tested, or sent for
approval. A future prospective plan must first choose batching or sharding that
satisfies finite RAM/VRAM/scratch bounds; an unsafe plan must be reduced rather
than escalated.

A generic elapsed-time sensitivity may be written as

$$
T_{elapsed}(k)=T_{serial}+T_{parallel}(k)+T_{IO}(k)+T_{sync}(k)+T_{recompute}(k),
$$

but none of these terms is grounded. Calendar time is also not derivable from
person-workdays because staffing and dependency availability are absent. Every
elapsed/calendar range is `NOT_STATICALLY_ESTIMABLE`.

## 6. Memory and storage

Logical entries need not all be resident simultaneously, but every one must be
processed. Streaming and exact caching therefore change only the prospective
physical footprint and traffic, never the logical counts or semantics.

| Prospective phase | Per-worker RAM constituents | Per-worker VRAM constituents | Static peak result |
| --- | --- | --- | --- |
| Snapshot/restore | Live mutable state, capture/restore copy or journal, immutable-identity metadata, remaining-tape address state | Device-resident state/parameters only if an exact accelerator path exists | RAM and VRAM separately `NOT_STATICALLY_ESTIMABLE`: field shapes, dtypes, representations, copy policy, and device placement are absent. |
| Closed-loop continuations | Restored state, observation/message/recurrent/legal working set, arm batch, transition buffers | Device working set only if applicable | Per-worker and total RAM/VRAM `NOT_STATICALLY_ESTIMABLE`. |
| Stopped integration/backward | Complete stopped-vector working set, retained terms, aggregation and prospective differentiation buffers | Parameters, activations, gradients, and optimizer/projection working set only if applicable | Per-worker and total RAM/VRAM `NOT_STATICALLY_ESTIMABLE`; full-batch topology and shapes are absent. |
| Audit/frontier/certificate | Counters, identity bindings, atomic frontier state, prospective audit evidence buffers | None assumed; any device use is unbound | RAM/VRAM `NOT_STATICALLY_ESTIMABLE`. |
| Exact cache/batching | Batch state, exact keys/payloads, cache index, serialization buffers | Device cache/batch only if selected | RAM/VRAM `NOT_STATICALLY_ESTIMABLE`; entry size, capacity, hit rate, and batch size are absent. |
| Tests/packaging/integration | Fixture and process working sets, package artifacts | No device assumption | RAM/VRAM `NOT_STATICALLY_ESTIMABLE`. |

For phase $p$ and $k$ co-resident workers, conditional footprints are
$R_p(k)=kr_{worker,p}+r_{shared,p}+r_{margin,p}$ for RAM and the analogous
class-labeled sum $V_{p,d}(k)$ for each accelerator device $d$. Peak RAM and
peak VRAM are the maxima over the phases that a future schedule proves
co-resident, reported per worker, per host/device, and in contemporaneous
aggregate. Every term is unbound; these formulas are not ranges.

| Storage dimension | Required accounting basis | Static result and missing facts |
| --- | --- | --- |
| Peak scratch/transient | Snapshots/journals, branch batches, exact-cache spill, temporary frontier/audit buffers, serialization duplication, test/package temporaries | `NOT_STATICALLY_ESTIMABLE`: object sizes, batch/cache policy, worker count, duplication, and cleanup lifecycle are absent. |
| Retained storage | Only separately authorized retained package, audit, frontier, and certificate surfaces under an explicit retention policy | `NOT_STATICALLY_ESTIMABLE`: retention set, format, duration, replication, and lifecycle are absent. |
| Serialization duplication | Source object plus serialized/staged copies, including failure-safe atomic-write overhead | `NOT_STATICALLY_ESTIMABLE`: serializer and atomicity strategy are absent. |
| Compression | Lossless only, with exact round-trip identity | `NOT_STATICALLY_ESTIMABLE`: compressibility, ratio, CPU cost, and format are absent. |
| Cache storage | Exact key plus complete exact payload and index, with no semantic aliasing | `NOT_STATICALLY_ESTIMABLE`: key/payload sizes, capacity, eviction, and hit rate are absent. |
| Frontier/certificate storage | Atomic completion/accounting metadata sufficient for the named audits | `NOT_STATICALLY_ESTIMABLE`: schema, granularity, retention, and replication are absent. |

Conditionally, if object class $a$ has live count $n_a(t)$, serialized bytes
$b_a$, duplication factor $d_a$, and exact lossless compression factor $c_a$,
then scratch bytes have the form
$S_{scratch}=\max_t[\sum_a n_a(t)b_ad_a/c_a+S_{staging}(t)]$.
Retained bytes use the same class-labeled sum over only the explicitly retained
set, with retention duration accounted separately. All counts, bytes, factors,
staging, sets, and durations are unbound, so both numeric results are
`NOT_STATICALLY_ESTIMABLE`.

Peak scratch is not combined with retained storage, and RAM is not combined with
VRAM. No telemetry, file, or data object was created to measure any category.
Aggregate peaks require contemporaneous co-residency; per-phase or per-host
maxima are not added unless a future schedule proves they coincide. No numeric
allocator, fragmentation, failure-staging, or safety margin is grounded.

## 7. Opportunity cost and definition-only CCA comparison

### 7.1 Opportunity-cost basis

A complete prospective opportunity-cost ledger would keep these dimensions
separate:

| Dimension | Conditional accounting formula | Static result |
| --- | --- | --- |
| Engineering labor | $W_{total}$ person-workdays multiplied by disclosed role-specific capacity or cost, plus identified displaced work | `NOT_STATICALLY_ESTIMABLE`: labor range, staffing cost, capacity, and displaced Portfolio work are absent. |
| CPU capacity | Class-labeled provisioned $H_{CPU,prov}$ or separately labeled busy CPU core-hours multiplied by a disclosed non-bundled shadow price or rate | `NOT_STATICALLY_ESTIMABLE`: accounting basis, core-hours, class, and rate are absent. |
| Accelerator capacity | Class-labeled provisioned $H_{ACCEL,prov}$ or separately labeled busy device-hours multiplied by a disclosed non-bundled shadow price or rate | `NOT_STATICALLY_ESTIMABLE`: path, accounting basis, hours, device class, scarcity, and rate are absent. |
| Host occupancy | $H_{HOST}$ multiplied by host-specific occupancy cost | `NOT_STATICALLY_ESTIMABLE`: host-hours, class, and rate are absent. |
| RAM/VRAM capacity | Class-labeled byte-time or an explicitly bundled host/device occupancy basis | `NOT_STATICALLY_ESTIMABLE`: byte footprints, holding intervals, scarcity, and rates are absent. |
| Scratch and retained storage | Each class's byte-time under separate transient and retention horizons | `NOT_STATICALLY_ESTIMABLE`: bytes, classes, durations, and rates are absent. |
| Calendar displacement | Elapsed critical-path time multiplied by an explicit Portfolio delay/shadow-cost rule | `NOT_STATICALLY_ESTIMABLE`: elapsed range and Portfolio valuation rule are absent. |
| Risk/rework | Probability-weighted or conservative interval impact under a disclosed non-overlapping risk model | `NOT_STATICALLY_ESTIMABLE`: probabilities, impacts, and model are absent. |

No monetary, lease, scheduling-priority, or displaced-direction value is
inferred. A future scalar ledger must also choose either bundled host/device
rates or non-overlapping component rates; it must not double count CPU,
accelerator, RAM, VRAM, or storage already included in a bundled rate.

### 7.2 Like-for-like CCA logical accounting

The common basis is definition-only logical work as recorded by the handoff. It
is not an implementation, runtime, or resource comparison. Signed differences
use $\Delta=RSCF-CCA$, so a negative number means fewer RSCF logical units on
that row.

| Dimension | RSCF | Definition-only CCA on the same logical basis | Signed difference $\Delta$ | Comparability |
| --- | ---: | ---: | ---: | --- |
| All-legal Q entries | 15,728,640 | 754,974,720, derived as $48N_Q$ | -739,246,080, derived as $-47N_Q$ | Exact documentary ratio and arithmetic |
| New alternative continuations | 11,010,048 | 528,482,304, derived as $48N_A$ | -517,472,256, derived as $-47N_A$ | Exact documentary ratio and arithmetic |
| Total environment slots | 91,471,872 | Exact count `NOT_STATICALLY_ESTIMABLE`; only an approximately 37.77-fold ratio is supplied | Numeric difference `NOT_STATICALLY_ESTIMABLE` because ratio precision/rounding is absent | Approximate ratio only |
| Learned decisions | 966,647,808 | Exact count `NOT_STATICALLY_ESTIMABLE`; only an approximately 38.59-fold ratio is supplied | Numeric difference `NOT_STATICALLY_ESTIMABLE` because ratio precision/rounding is absent | Approximate ratio only |
| Full-batch backward calls | 24,576 | `NOT_STATICALLY_ESTIMABLE`; no CCA count/ratio is supplied | `NOT_STATICALLY_ESTIMABLE` | Non-comparable from permitted evidence |
| Person-workdays | `NOT_STATICALLY_ESTIMABLE` | `NOT_STATICALLY_ESTIMABLE` | `NOT_STATICALLY_ESTIMABLE` | No common implementation/reuse/productivity model |
| Elapsed/calendar time | `NOT_STATICALLY_ESTIMABLE` | `NOT_STATICALLY_ESTIMABLE` | `NOT_STATICALLY_ESTIMABLE` | No safe concurrency or service-rate model |
| CPU core-hours | `NOT_STATICALLY_ESTIMABLE` | `NOT_STATICALLY_ESTIMABLE` | `NOT_STATICALLY_ESTIMABLE` | No common hardware/incidence/service-demand model |
| Accelerator-hours | `NOT_STATICALLY_ESTIMABLE` | `NOT_STATICALLY_ESTIMABLE` | `NOT_STATICALLY_ESTIMABLE` | Neither accelerator path is bound |
| Host-hours | `NOT_STATICALLY_ESTIMABLE` | `NOT_STATICALLY_ESTIMABLE` | `NOT_STATICALLY_ESTIMABLE` | No common host topology |
| Peak RAM / peak VRAM | Each separately `NOT_STATICALLY_ESTIMABLE` | Each separately `NOT_STATICALLY_ESTIMABLE` | `NOT_STATICALLY_ESTIMABLE` | No common representation, batch, or device model |
| Peak scratch / retained storage | Each separately `NOT_STATICALLY_ESTIMABLE` | Each separately `NOT_STATICALLY_ESTIMABLE` | `NOT_STATICALLY_ESTIMABLE` | No common serialization/cache/retention model |
| Opportunity cost | `NOT_STATICALLY_ESTIMABLE` | `NOT_STATICALLY_ESTIMABLE` | `NOT_STATICALLY_ESTIMABLE` | No labor/resource/shadow-price basis |

The exact logical reductions do not imply the same reduction in labor, elapsed
time, compute, memory, storage, or opportunity cost; fixed costs, unit costs,
physical schedules, and implementations are all unbound. The handoff supplies
no materiality metric or uncertainty rule. This packet therefore emits no
`MATERIALLY_BELOW`, pass/fail, investment, construction-selection, or veto
label.

## 8. Assumption and gap register

| ID | Disclosed assumption or absent input | Consequence |
| --- | --- | --- |
| A1 | The handoff is the sole content authority; referenced scientific and implementation coordinates remain unopened. | Identity-bound documentary facts are usable; field/API/scientific reinterpretation is forbidden. |
| A2 | Exact counts are accepted exactly as documentary facts; approximate ratios retain unknown precision. | Exact arithmetic is limited to the 48-fold rows; no fabricated interval for approximate rows. |
| A3 | Counts on different rows may overlap computationally. | They are sensitivity axes, not an additive compute total. |
| A4 | No implementation, state schema, API, language, dependency, reuse, or test surface is supplied. | Construction bindability and all component workday ranges are `NOT_STATICALLY_ESTIMABLE`. |
| A5 | No hardware, process/thread/worker, utilization, service-rate, or device-path facts are supplied. | CPU, accelerator, host, elapsed, and safe-concurrency ranges are `NOT_STATICALLY_ESTIMABLE`. |
| A6 | No shape, dtype, representation, batch, cache, serialization, compression, retention, or frontier schema is supplied. | RAM, VRAM, scratch, and retained storage ranges are `NOT_STATICALLY_ESTIMABLE`. |
| A7 | No staffing, productivity, availability, review policy, packaging target, or risk distribution is supplied. | Labor, calendar, and risk allowances are `NOT_STATICALLY_ESTIMABLE`. |
| A8 | No price, scarcity, displaced-work, or Portfolio delay-value rule is supplied. | Opportunity cost is `NOT_STATICALLY_ESTIMABLE`. |
| A9 | Any future physical strategy must preserve all logical work, complete state, recurrence, coupling, loss/optimizer lifecycle, checkpoint opportunity, and audits. | Streaming, batching, caching, sharing, compression, recomputation, and sharding remain conditional and cannot justify scientific reduction. |
| A10 | No construction or empirical activity follows automatically. | Visible gaps return to Root; they do not start a successor assignment. |

## 9. Acceptance traceability

| Handoff requirement | Packet coverage | Terminal finding |
| --- | --- | --- |
| 1. Snapshot/restore feasibility and cost | Section 3.1; labor Section 4; resources Sections 5--6 | Category-level contract inventoried; field binding, constructibility, labor, and resources `NOT_STATICALLY_ESTIMABLE`. |
| 2. Closed-loop branch feasibility and cost | Section 3.2 | Full focal-only, factual-teammate, ordinary-transition, recomputation, horizon, common-tape, and legal-coverage duties preserved; implementation/cost `NOT_STATICALLY_ESTIMABLE`. |
| 3. Stopped-target/loss integration | Section 3.3 | Every named retained term and lifecycle mapped; implementation/cost `NOT_STATICALLY_ESTIMABLE`. |
| 4. Selector/coupling/audits | Section 3.4 | Every named invariant has a prospective predicate and explicit observability gap. |
| 5. Streaming/batching/exact cache | Section 3.5 | Only conditional semantics-preserving strategies; no logical-work change or selection. |
| 6. Complete prospective labor | Section 4 | Every named component has a separate workday variable, dependencies, risks, and exact missing facts; all finite ranges `NOT_STATICALLY_ESTIMABLE`. |
| 7. Compute and host resources | Section 5.1 | CPU core-hours, accelerator-hours, and host-hours remain separate; hardware/topology/utilization and ranges `NOT_STATICALLY_ESTIMABLE`. |
| 8. Elapsed time and safe concurrency | Section 5.2 | Safety inequalities and sensitivities disclosed; no numeric case, including one worker, is grounded; all elapsed ranges `NOT_STATICALLY_ESTIMABLE`. |
| 9. Memory and storage | Section 6 | RAM/VRAM, per-worker/total, scratch/retained, serialization/duplication/compression/cache/frontier assumptions separated; all ranges `NOT_STATICALLY_ESTIMABLE`. |
| 10. Opportunity cost and CCA comparison | Section 7 | Common logical basis, exact ratios/arithmetic, non-comparable dimensions, opportunity-cost formulas, and missing facts disclosed; no materiality or selection label. |

The packet binds every required authority hash in its header; independently
excludes both advisory planning ranges; keeps labor, elapsed time, CPU,
accelerator, host, RAM, VRAM, scratch, retained storage, and opportunity cost
separate; preserves all frozen logical and semantic requirements; and produces
no empirical or scientific artifact.

## 10. Durable disposition

`packet_status=COMPLETE_WITH_VISIBLE_STATIC_GAPS` means the requested assessment
is complete under its documentary/read-only boundary, not that any estimate or
construction is accepted. Root/Portfolio receives this packet for a separate
intake decision. No construction proposal, source or test access, measurement,
compute, provider review, lease, successor engineering assignment, or
scientific transition follows automatically.

```text
next_action.owner=ROOT
next_action.kind=PORTFOLIO_INTAKE_STATIC_FULL_COST_ASSESSMENT
scientific_ambiguity_found=false
construction_selected=false
construction_recommended=false
construction_authorized=false
compute_authorized=false
source_or_test_effect=false
runtime_or_scientific_effect=false
provider_operation_created=false
```
