# Decision ledger — D7.S R4 absolute focal margin

Contract: `D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md`.
Schema: `docs/project/DECISION_LEDGER_TEMPLATE.md`.

All nine entries are `PROTECTED_PRO` and were ruled externally. **None is
`PM_ENGINEERING`** — every one of them decides a registered quantity, a branch,
a comparator, or the inferential population, so routing any of them to engineering
authority would be exactly the failure the standing sweep exists to catch.

```yaml
id: R4-001
protected_object: materiality threshold -- the absolute focal margin
authority: PROTECTED_PRO
state: DECIDED
ruling: ACCEPTED
alternatives:
  - Anchor E, cutoff-equivalent 5.0 G-units, horizon-independent   [selected]
  - Anchor Q, q* * H_m, equal per-step rate                        [parked]
  - R4-B, positive pre-treatment opportunity scale                 [parked]
  - retain a global-rotation denominator under a new name          [disfavoured]
smallest_consequence: >
  Decides both clearing predicates directly. Reversing it changes which runs
  report MATERIAL on either limb, and therefore the top-level result.
evidence_paths:
  - docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md
  - docs/external-review/rounds/20260728_r4_materiality_derivation/21_PRO_OPEN_RAW.md
implementation_binding: not yet wired -- replaces compute_t_m_bootstrap's T_m gate
ruling_source: External Pro
ruling_artifact: rounds/20260728_r4_materiality_derivation/21_PRO_OPEN_RAW.md
revision: R4
depends_on: []
affects: [R4-005, R4-007, R4-008]
re_review_trigger: >
  A pre-run task-semantic argument showing one cutoff-equivalent is not a
  meaningful minimum consequence. The anchor is NOT mathematically unique and
  must not be inherited as forced.
---
id: R4-002
protected_object: optional-sampling rule -- expansion
authority: PROTECTED_PRO
state: DECIDED
ruling: ACCEPTED
alternatives:
  - no expansion                                                   [selected]
  - an R4-specific one-expansion predicate over absolute-margin points
  - inherit R3's expansion predicate                               [void: its inputs no longer exist]
smallest_consequence: >
  Decides whether the evidence population can grow after bounds are observed.
  Reversing it introduces optional stopping and a power-rescue path.
evidence_paths:
  - docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md
implementation_binding: not yet wired -- deletes expansion_allowed from the R4 path
ruling_source: External Pro
ruling_artifact: rounds/20260728_r4_contract_freeze/21_PRO_OPEN_RAW.md
revision: R4
depends_on: [R4-003]
affects: []
re_review_trigger: >
  None registered. NOTE: the Project Manager's argument for this -- that R3's
  predicate was never evaluable -- was ACCEPTED but explicitly rejected as the
  reason. The scientific reasons are a fixed confirmatory population, no
  optional-stopping correction, no power rescue, lower complexity, and the
  legitimacy of an unresolved result. Do not re-derive from the implementation
  lesson.
---
id: R4-003
protected_object: inferential population -- topology seeds
authority: PROTECTED_PRO
state: DECIDED
ruling: ACCEPTED
alternatives:
  - 20260734..20260741, untouched                                  [selected]
  - reuse 20260726..20260733 with new episode/energy/world seeds   [rejected]
  - a newly drawn seed block outside the registered set
smallest_consequence: >
  Decides what the R4 result is a statement about. Topology is the top-level
  bootstrap and inferential unit, so reusing R3 topologies would give fresh
  conditional draws from P(W|T) but not fresh draws from P_T.
evidence_paths:
  - docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md
implementation_binding: not yet wired -- replaces TOPOLOGY_SEEDS_INITIAL on the R4 path
ruling_source: External Pro
ruling_artifact: rounds/20260728_r4_contract_freeze/21_PRO_OPEN_RAW.md
revision: R4
depends_on: []
affects: [R4-002, R4-009]
re_review_trigger: >
  Repository provenance establishing that any of the eight was previously used
  for a result-bearing or design-informing source measurement. A replacement
  seed must NOT be selected silently -- the contract reopens.
---
id: R4-004
protected_object: RNG stream ownership -- population/seed namespace
authority: PROTECTED_PRO
state: DECIDED
ruling: ACCEPTED
alternatives:
  - namespace D7_S_R4_ABSOLUTE_FOCAL_MARGIN, existing hash structure  [selected]
  - reuse the R3 namespace and rely on the topology change alone      [rejected]
smallest_consequence: >
  Decides whether R4 has disjoint randomness at every conclusion-bearing layer
  or only at the topology layer. Reversing it correlates R4 episode, energy,
  user-world and continuation streams with R3's.
evidence_paths:
  - docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md
implementation_binding: not yet wired -- stream_seed's contract_id field
ruling_source: External Pro
ruling_artifact: rounds/20260728_r4_contract_freeze/21_PRO_OPEN_RAW.md
revision: R4
depends_on: [R4-003]
affects: []
re_review_trigger: Any change to stream_seed's hashed field set.
---
id: R4-005
protected_object: comparator -- the Part-A control block
authority: PROTECTED_PRO
state: DECIDED
ruling: ACCEPTED
alternatives:
  - PART_A_CONTROL, full_sync_SET vs constructive_mixed, D_A +/- 5     [selected]
  - retain the R3 calibration block with +/- 0.05*B_stable             [void: no B_m in R4]
smallest_consequence: >
  Decides branch 4. Reversing it makes a B_stable-dependent control
  conclusion-bearing again, reintroducing the denominator R4 removed.
evidence_paths:
  - docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md
implementation_binding: not yet wired -- replaces part_a_conformance's bounds
ruling_source: External Pro
ruling_artifact: rounds/20260728_r4_contract_freeze/21_PRO_OPEN_RAW.md
revision: R4
depends_on: [R4-001]
affects: [R4-008]
re_review_trigger: >
  None. The null arm and both B_m quantities are DELETED from the R4 path, not
  retained as legacy apparatus.
---
id: R4-006
protected_object: branch meaning -- branch 3's causal pair set
authority: PROTECTED_PRO
state: DECIDED
ruling: ACCEPTED
alternatives:
  - focal (KEEP, SET(z)) evaluation pairs                             [selected]
  - R3 calibration pair (constructive_mixed, null)                    [superseded, R3-specific]
  - a fractional threshold over pairs                                 [rejected]
smallest_consequence: >
  Decides what PRIMARY_G_DEGENERATE asserts. Reversing it aggregates component
  separation over the normalizer source controls, which R4 no longer has.
evidence_paths:
  - docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md
implementation_binding: exact_paired_sequence_equal over the audit-block records
ruling_source: External Pro
ruling_artifact: rounds/20260728_r4_contract_freeze/21_PRO_OPEN_RAW.md
revision: R4
depends_on: []
affects: [R4-007, R4-008]
re_review_trigger: >
  NOTE the supersession: the calibration-pair aggregation rule frozen earlier the
  same day (rounds/20260728_d7_s_autopsy_result) was R3-specific. Do not inherit
  it. Exact invariance only -- no fraction threshold, ever.
---
id: R4-007
protected_object: result semantics -- per-limb state predicates
authority: PROTECTED_PRO
state: DECIDED
ruling: ACCEPTED
alternatives:
  - four states with explicit bound predicates per limb              [selected]
  - four state names without predicates                              [the partial freeze's defect]
smallest_consequence: >
  Decides each limb's reported state, and equality at the threshold. Strict
  inequalities: equality resolves to UNRESOLVED, not MATERIAL.
evidence_paths:
  - docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md
implementation_binding: not yet wired
ruling_source: External Pro
ruling_artifact: rounds/20260728_r4_contract_freeze/21_PRO_OPEN_RAW.md
revision: R4
depends_on: [R4-001, R4-006]
affects: [R4-008]
re_review_trigger: None.
---
id: R4-008
protected_object: result precedence -- combined branch mapping
authority: PROTECTED_PRO
state: DECIDED
ruling: ACCEPTED
alternatives:
  - nine-row mapping over the two limb states, limb states always in payload  [selected]
  - the R3 branch table                                                       [insufficient: no flex-only positive]
smallest_consequence: >
  Decides the top-level result name. Reversing it can hide a valid flex positive
  under a stable-negative or generic unresolved branch -- the exact gap R3 had.
evidence_paths:
  - docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md
implementation_binding: not yet wired -- replaces decide_branch's rows 5-10
ruling_source: External Pro
ruling_artifact: rounds/20260728_r4_contract_freeze/21_PRO_OPEN_RAW.md
revision: R4
depends_on: [R4-001, R4-005, R4-006, R4-007]
affects: []
re_review_trigger: >
  The independent limb states must ALWAYS remain in the payload. A top-level name
  may never erase whether the non-material limb was affirmatively nonmaterial,
  exactly invariant, or merely unresolved.
---
id: R4-009
protected_object: data split -- no pooling with R3
authority: PROTECTED_PRO
state: DECIDED
ruling: ACCEPTED
alternatives:
  - R3 units refused by the R4 pooler; no rethresholding             [selected]
  - pool R3 and R4 topology units                                    [rejected]
smallest_consequence: >
  Decides whether the R3 artifact can become its own confirmatory result.
  Reversing it lets a rethresholded R3 dataset be reported as R4 evidence.
evidence_paths:
  - docs/research/designs/D7_S_R4_ABSOLUTE_FOCAL_MARGIN_COMPLETE.md
implementation_binding: not yet wired -- R4 freshness sentinel, conditions 2 and 5
ruling_source: External Pro
ruling_artifact: rounds/20260728_r4_contract_freeze/21_PRO_OPEN_RAW.md
revision: R4
depends_on: [R4-003]
affects: []
re_review_trigger: >
  A same-topology/new-episode run is retainable ONLY as
  R4_ORIGINAL_PANEL_CONDITIONAL_REPLICATION, never pooled or substituted.
```

## Standing sweep — current status

- No entry is routed to `PM_ENGINEERING`, so the misrouting class is empty by
  construction here.
- No `DECIDED` entry lacks a ruling artifact.
- Every entry's `implementation_binding` except `R4-006` reads **not yet wired**.
  That is the honest state: the contract is frozen and the code is not. It is
  also the reason no gate certificate exists for R4 and none may be issued until
  the realization-conformance review of the contract's §11 closes.
- **Guard closure is a premise, not a ruled fact.** It has no ledger entry
  because it is not a protected decision — but the realization gate must check it
  rather than inherit it from this session's claims.
