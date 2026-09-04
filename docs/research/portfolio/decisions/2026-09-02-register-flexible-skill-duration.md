# Register `flexible_skill_duration` as an ACTIVE direction

Date: 2026-09-02

Decision: `FINAL / OWNER_DIRECT / ROOT_INTEGRATED`

## Provenance

- Portfolio node: `portfolio:cross_direction`
- Request: owner, in session `session_015hGLzLCuJLFFtZTboKg2bd` ("我希望进入正式研究层")
- Governing method: `docs/research/specs/MARL_EMPIRICAL_EVIDENCE_SPEC.md`, §11 controlling
- Direction authority: `docs/research/candidates/flexible_skill_duration/DIRECTION.md`
- Working record: `docs/Claude_docs/README.md` (plans, ADRs, reviews, experiments)

## Decision

`flexible_skill_duration` enters the Portfolio as `ACTIVE / HIGH / ROOT`. Its bounded next object
is B/EXPLORE E1 (age-conditioned discriminator at fixed `k = 10`, D0 versus D1 on UAV scenario 1,
three seeds), followed by E2 (D2 interruption cost sweep on the homogeneous relay corridor) per
`docs/Claude_docs/plans/RESEARCH_ADVANCEMENT_PLAN_20260902.md` §7.

The direction's completed objects (ADR 01, ADR 02, E0) were produced under the §11 calibration and
carry their own acceptance records; none is a C observation and none consumes anything.

## Counts after this decision

| Lifecycle | Count |
| --- | ---: |
| ACTIVE | 20 |
| PARKED | 2 |
| LEGACY | 14 |
| Total | 36 |

## Effect on other directions

None of the existing rows changes. `semigroup_consistent_duration_model_policy` and `ucope` keep
their objects; their relations to the new direction are recorded in the new `DIRECTION.md` and in
`docs/Claude_docs/plans/FLEXIBLE_SKILL_DURATION_PLAN_20260902.md` §11 (items F and G).
`variable_n_fleet_churn` remains the separate untied-`N` direction (§11.5).
