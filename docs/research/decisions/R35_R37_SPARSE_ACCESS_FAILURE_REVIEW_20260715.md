# R35--R37 Sparse-Access Failure Review

Date: 2026-07-15

## Decision

R37 is a valid `FAIL_R37_ACCESS`. Retire the current sparse
`alice_bob_asymmetric_cycles` environment as an algorithm-comparison gate under
the registered 80-step horizon and 320K-step ordinary-policy budget. Do not
rescue it by changing its threshold, horizon, contact geometry, budget, seed,
optimizer exposure, or observation menu.

R37 does not show that current-task identity is ineffective. It shows that the
identity repair is a strong causal access carrier but still does not establish
the registered robust cycle-success floor.

## Cross-Round Evidence

| Gate | Valid mechanism evidence | Access evidence | Reusable decision |
| --- | --- | --- | --- |
| R35 constant-code MAPPO vs reward-pure R30 | Both matched arms completed 320K steps and 250 low updates from one neutral initialization | Both had 0/64 collection episodes and zero cycle success | No hierarchy comparison is interpretable without a positive ordinary-policy access floor |
| R36 AEM vs constant-code MAPPO | The direct 625-cell novelty reward was isolated to low GAE and expanded coverage `3.8552x` | Both arms still had 0/64 collections and zero cycle success | Undirected coarse state breadth is not a sufficient carrier for first coordinated access |
| R37 visible vs masked current-task identity | Both capacity-matched arms used one common 16-input zero-step checkpoint; all 1.28M actor-slot audits had zero error; no high or intrinsic path was active | Visible identity produced 10/64 collection/cycle episodes, reward `0.15625`, cycle mean `0.01953125`, and coverage `0.035275`; masked identity produced zero access and coverage `0.021975` | Hidden task identity was a real bottleneck, but repairing it did not clear the registered robust cycle floor `0.05` |

The paired visible-minus-masked effects were all directionally coherent:

```text
collection indicator  0.15625    95% CI [0.078125, 0.25]
cycle success         0.01953125 95% CI [0.009765625, 0.03125]
sparse reward          0.15625    95% CI [0.078125, 0.25]
coverage               0.01330    95% CI [0.01175, 0.014775]
zero-cycle fraction   -0.15625    95% CI [-0.25, -0.078125]
```

The registered collection count floor of 10/64 and the paired collection CI
both passed. M2 sparse-task evidence and M3 stability passed. M1 failed only
because treatment cycle success was `0.01953125`, below `0.05`. The JSON field
`paired_collection_indicator_ci_lower_strict = 0` is the required threshold,
not the observed CI lower endpoint.

## Failure Classification

- Instrumentation/data quality: no identified defect. M0 passed; both arms had
  identical capacity, initialization, critic information, reward, update
  exposure, and paired evaluation seeds. The visible slots matched the active
  one-hots and the masked slots remained zero at every audited actor step.
- Optimization/capacity: the visible arm learned nonzero sparse access and
  completed ten cycles, so this is not a zero-gradient or inaccessible-task
  result. The registered ordinary-policy floor nevertheless remained too weak
  for algorithm comparison.
- Scientific failure: the full registered implication failed:

  ```text
  current-task identity visible
  -> positive first access
  -/-> robust cycle success >= 0.05
  ```

- Claim boundary: the result identifies an environment information defect and
  its partial repair. It is not an algorithm, hierarchy, cooperation, HMASD,
  S7, or paper-level result.

## Baseline Matrix For The Replacement Decision

| Candidate substrate | Current evidence | Blocking issue before algorithm work |
| --- | --- | --- |
| Current 80-step asymmetric-cycle Alice--Bob | Valid causal identity effect, but cycle mean only `0.01953125` | Retired by its registered valid-FAIL branch; no threshold/budget/environment rescue |
| Historical continuous Alice--Bob | Existing 200-step two-button/two-diamond sparse environment with visible fixed object semantics | No current matched ordinary-policy access floor; old observation/reward/runtime contract requires audit before reuse |
| S7-S1 | Standing HMASD reference reaches high coverage by roughly 0.8M steps | Scientifically relevant but materially slower; a fast access/calibration boundary and matched ordinary baseline are not yet specified |

## Closed And Open Claims

Closed:

- Hidden randomly initialized active identities caused a large, measurable
  access loss in the current Alice--Bob environment.
- Coarse state breadth without task identity was insufficient.
- Current identity alone was necessary and useful but insufficient for the
  registered robust cycle floor at this exact horizon and budget.
- R35--R37 may not be rescued by retuning, more seeds/steps, lower thresholds,
  reward shaping, or another algorithm module.

Open:

- which single replacement benchmark retains sparse cooperative reward and
  genuinely different short/long task timescales while giving ordinary
  recurrent MAPPO a predeclared positive access floor;
- its exact decentralized observation, centralized critic state, horizon,
  reward, random-policy sanity bound, ordinary-policy budget, and abandonment
  rule;
- whether an existing repository environment is suitable or one new minimal
  benchmark is required.

## Single Next Decision Boundary

Before more R30 or skill-mechanism work, externally audit R37 and select exactly
one replacement benchmark/access gate. That gate must validate the substrate
with an ordinary non-hierarchical policy before any algorithm comparison. It
must not modify or rerun R37, add shaping/curriculum/oracle supervision, or
smuggle an algorithm contribution into the environment repair.
