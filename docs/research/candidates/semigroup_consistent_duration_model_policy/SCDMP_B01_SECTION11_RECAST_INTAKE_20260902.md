# SCDMP B01 — section 11 recast intake (2026-09-02)

- Direction: `semigroup_consistent_duration_model_policy`
- Study family: `SCDMP-MF-RS-MK-ORDER-VALUE-B01` (`B/EXPLORE`)
- Bound base run: `SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01`
- Bound evidence attempt: `SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01-REPLACEMENT-01-ATTEMPT-01`
- Controlling contract: `SCDMP_MF_RS_MK_ORDER_VALUE_B01_SCIENCE_CARD_20260901.md` (body unchanged;
  a dated addendum records the same demotion)
- Governing method: `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`, §11 controlling

This is the §11.6 record of the demotion ("Direction owners SHOULD record the demotion in the
direction's next intake rather than rewrite historical documents"). It changes no scientific factor
of the frozen object and produces no order-value observation.

## 1. Provenance of the decisions implemented here

- `docs/Claude_docs/reviews/FIRST_WAVE_SECTION11_COMPLIANCE_20260902.md`, Part A.4, decisions 1
  and 7; the SCDMP audit with `file:line` for every gate is Part B section 4 of the same file.
- `docs/research/portfolio/decisions/2026-09-02-first-wave-section11-recast.md`
  (`FINAL / OWNER_DIRECT / ROOT_INTEGRATED`, portfolio node `portfolio:cross_direction`).

Decision 1, verbatim from A.4:

> Recast per §11 and run now: the `PERFORMANCE_READY` receipt becomes a recorded field; telemetry is
> recorded, not gating; RUN-01-REPLACEMENT-01 runs exactly as frozen; the intake records the §11
> demotion and the §11.3 reading of the `k ∈ {7, 13}` menu

Decision 7, verbatim from A.4:

> Downgrade, not annul: a run whose resource telemetry (peak RSS, scratch, wall) is missing stays
> valid and is marked "resources unmeasured"; annulment only when the claim itself is a resource
> claim. Learner-side instrumentation failure (missing logs or checkpoints) still quarantines under
> §6.2

The portfolio record states the same rule as the closure of the clause §11.4 left undecided and of
workflow-review item R4.

## 2. What §11 demotes in this direction

Each row is quoted from the compliance note's SCDMP audit (Part B section 4) with the `file:line`
that note gives. "Card" is the working-tree
`SCDMP_MF_RS_MK_ORDER_VALUE_B01_SCIENCE_CARD_20260901.md` as committed in
`Record SCDMP working-tree state before the section 11 recast`.

| # | Demoted condition (quoted) | file:line | Now |
| --- | --- | --- | --- |
| 1 | `raise ResultExecutionDisabled("RUN-01 performance readiness receipt is required")` / `"… receipt is invalid"` | `experiments/candidates/scdmp_variable_k/multifoundation_reachable_order_value/runner.py:606-611` | recorded field `performance_assessment` in the attempt's `performance-assessment.json` and in `published-result.json`; the run proceeds. The only assessment on disk records `"performance_readiness": "REVIEW_REQUIRED"` (`temp/scdmp-b01/A-R2/assessment.json`), which is what gets recorded |
| 2 | "no scientific artifact may be created until the following order is satisfied: … 3. arm continuous process-tree peak-RSS, scratch-high-water, durable-byte and wall/resource telemetry and record a valid initial observation … 8. only then create models, optimizers, checkpoints…" | card:72, 79-81, 88 | telemetry is still armed and its initial observation still attempted; a failure to arm it is recorded as `resources_unmeasured` with its reason instead of refusing the attempt. Steps 1, 2, 4, 5, 6, 7 of that ordered list are unchanged and still binding |
| 3 | "A missing measurement invalidates the attempt just as a measured cap exceedance does." | card:530-531 | demoted to a recorded field per decision 7. A **measured** cap exceedance (peak RSS > 2 GiB, scratch > 256 MiB, durable > 256 MiB, wall > 30 min) still invalidates; a **missing** measurement does not |
| 4 | "Missing or invalid telemetry, uncertain frontier commitment, escaped partial results, … forbids resume and permanently quarantines that attempt." | card:96-99 | the "missing or invalid telemetry" clause alone no longer quarantines. Every other clause in that sentence — uncertain frontier commitment, escaped partial results, unrecoverable exact binding, regenerated stochastic coordinates, a required root/identity change — is unchanged and still quarantines |
| 5 | "failed physical/effective `4 GiB` admission or missing peak-RSS, scratch or durable telemetry" produce no scientific polarity | card:621 | split: the admission half stays a launch condition (§11.4 explicitly allows it); the telemetry half becomes a recorded field |

Rows 3–5 are the same demotion seen from three places in the card; row 1 is the only one that was
also a live code refusal. The audit classed rows 3 and 4 `UNCLEAR` because §11.4's final sentence
left the downgrade-versus-annul question open; decision 7 closes it as downgrade.

## 3. What remains a launch condition

Unchanged and still binding for this object:

- the §4 common integrity requirements, in full;
- the §5.2 requirement that the real learner, trainer, evaluator and native host run and report
  nonzero transition, optimizer-step and evaluator-call counts — card:513-514, "Scientific activity
  requires nonzero training transitions, optimizer steps and real evaluator calls";
- the mandatory resource admission — card:77-78, "perform a fresh invocation-specific memory
  admission and observe at least `4 GiB` physical and effective available memory", run immediately
  before the invocation, per `python scripts/hmasd_resource_preflight.py admit-memory --out
  <receipt.json>`;
- an exposure statement that the learner can move in its budget: SCDMP satisfies §11.4's
  exposure-line clause with the machine-generated training metrics recorded at every update and the
  nine fixed evaluator curve points per foundation, which are already required by the card. No new
  exposure gate is added and none is removed;
- the B eligibility competence counts — card:201-211, at least `24/32` per cell, `109/128` pooled,
  no more than `12/128` in one physical-failure family, every record terminal, finite and
  evaluator-valid, else stop as `FOUNDATION_COMPETENCE_NOT_ESTABLISHED`;
- the permanent zero-access quarantine of the old physical root and its descendants —
  card:616-618 and card:70-71 — which §11.4 leaves explicitly unchanged;
- the `q_by_cell` law: exactly one pre-model draw from `001110/011100/100011/110001`, sealed in the
  attempt manifest, never redrawn or selected after any model, competence, source, development,
  held-out or outcome observation — card:626-627;
- RNG-domain separation and the leakage boundary — card:641-642, no overlap among training,
  state-source, development and held-out RNG domains, no held-out tape generated or read before the
  atomic action-map freeze;
- the create-once publication law and the "published RUN-01 is immutable" guard
  (`runner.py:56`), which is untouched by this recast;
- learner-side instrumentation: missing logs, missing checkpoints, or a missing **required
  scientific** measurement still quarantines under §6.2. Only resource telemetry is downgraded.

The frozen scientific object itself does not change: seeds `1709`/`2903`, 160 updates × 12
episodes, 1,920 AdamW steps, the nine-point curves at `{0,20,…,160}`, the 128-mission competence
check, six state twins, the 18-action development sweep on eight development tapes, 16 held-out
tapes, the four admissible `q_by_cell` vectors, the ordered result branches, the workload ceilings
and the B claim ceiling.

## 4. §11.3 reading of the `k ∈ {7, 13}` duration menu

§11.3 says a treatment "does not have to be optimal, learned end to end, or invariant by
construction", and names "fixed duration menus with hazard-rate termination" as admissible
treatments and comparators; a direction "MUST NOT be parked or closed because its scheme is known
to be suboptimal".

Recorded here for this direction: the duration menu `k ∈ {7, 13}` is a legitimate suboptimal
scheme. Its target-scale error against the interruption-free reference is

```text
tau * (1 - gamma) / (1 - gamma^tau)
```

that is, `τ(1−γ)/(1−γ^τ)`, where `τ` is the segment length — the number of primitive ticks over
which the committed first action is held, i.e. the menu value `k` — and `γ` is the discount factor.
The expression is the ratio of the undiscounted segment length `τ` to the discounted length of the
same segment, `1 + γ + … + γ^{τ−1} = (1−γ^τ)/(1−γ)`. It equals `1` at `τ = 1` and at `γ = 1`, and
grows with `τ` for `γ < 1`: a longer committed hold measures its target on a scale that departs
further from the interruption-free one.

Two boundaries on that statement:

- It is recorded as the direction's §11.2 preferred theoretical product (a suboptimality/error
  bound for the scheme as implemented), not as a proved theorem and not as a C-FORMAL obligation.
  §11.2 requires only that its assumptions match the implemented scheme.
- It is **not** applied to the B01 endpoint. The frozen endpoint is
  `U = 1{safe dock} · (1 − dock_tick/364)`, an undiscounted full-mission utility, so no factor of
  this form enters any B01 number. The expression is a direction-level statement about what the
  fixed menu costs relative to an interruption-free reference, and belongs to the duration-model
  question, not to this run's arithmetic.

## 5. Relation to `flexible_skill_duration`

`docs/research/candidates/flexible_skill_duration/DIRECTION.md`, "Relations to other directions"
(line 47), states:

> `semigroup_consistent_duration_model_policy` (SCDMP): recast toward scheme D6 (a duration model
> whose value is sharing `Q(s, z, k)` across `k`); its `(z, k)` menu is comparator D8 here (plan
> §11 F). SCDMP's own objects continue independently.

So the `(z, k)` menu SCDMP holds fixed is that direction's comparator D8, and the D6 recast is
noted there, not here. Nothing in that relation gates, blocks or redirects SCDMP: `SCDMP-MF-RS-MK-
ORDER-VALUE-B01` continues independently under its own science card. Per §11.5 the untied-`k` and
untied-`N` programmes remain separate directions; this intake opens no joint object.

## 6. What this intake does not do

It records no order-value observation, changes no seed, tape, state, action map, endpoint,
comparator, budget or branch, and consumes no scientific object. It establishes no algorithm
performance, stability, promotion, retirement, lifecycle, transfer, safety or general-MARL claim.
The previous attempt `SCDMP-MF-RS-MK-ORDER-VALUE-B01-RUN-01` remains permanently quarantined under
zero access, and this recast does not resume, salvage, reopen or reinterpret it.
