# R35--R36 Sparse-Access Failure Review

Date: 2026-07-15

## Decision

R36 is a valid `FAIL_M1_RETIRE_R36_AEM`. Permanently retire the registered
direct 625-cell episodic joint-position bonus. Do not change its grid, count
window, formula, coefficient, budget, seed, or optimizer exposure.

## Cross-Round Evidence

| Gate | Valid mechanism evidence | Access evidence | Reusable decision |
| --- | --- | --- | --- |
| R35 constant-code MAPPO vs reward-pure R30 | Both matched arms completed 320K steps and 250 low updates with pure sparse reward | Both had 0/64 collection episodes and zero cycle success | No algorithm comparison is interpretable before access |
| R36 AEM vs constant-code MAPPO | AEM was isolated to low GAE; all 320K bonuses followed the registered formula; control exposure was zero | AEM coverage was `0.0639` vs `0.016575`, ratio `3.8552`, paired difference CI `[0.0454, 0.049175]`; both still had 0/64 collections and zero cycle success | Coarse episodic joint-position breadth is not a sufficient carrier for first sparse access |

## Failure Classification

- Instrumentation/data quality: no identified defect. M0 passed and both arms
  completed the exact registered exposure.
- Optimization/capacity: AEM produced a large, precisely measured visitation
  change, so this is not a zero-gradient or inactive-reward failure. The result
  does not establish that ordinary sparse PPO is generally incapable.
- Scientific failure: the registered carrier implication failed:

  ```text
  broader 625-cell joint visitation
  -/-> first coordinated collection
  ```

- Confounded claim boundary: one Alice--Bob seed and 320K steps do not establish
  general exploration failure, hierarchy value, cooperation, or HMASD parity.

## Environment Fact Exposed By The Failure

The Alice--Bob actor observation contains own/relative positions and offsets to
both buttons and both targets, but omits which button and target are active and
omits both task clocks. The active identities are sampled at reset; target then
toggles every 10 steps and button every 40. The centralized critic state does
contain active one-hots and clocks. A collection requires different agents to
be simultaneously within radius `0.70` of the active button and active target.

The R36 coverage grid has spatial width `8/5 = 1.6` per axis, more than twice
the contact radius. Consequently a large gain in coarse joint cells neither
implies landmark contact nor resolves the actor's hidden active-task identity.
This is a concrete candidate access-instrument problem, not evidence that the
R36 implementation was invalid.

## Closed And Open Claims

Closed:

- R35 cannot choose between constant MAPPO and R30 because access was absent.
- The exact R36 episodic joint-count reward changes visitation but does not
  create sparse access; coverage cannot override its M1 failure.
- Another count grid, RND/ICM replacement, coefficient change, or longer R36 is
  not authorized as a rescue.

Open:

- whether the current decentralized observation contract is an appropriate
  sparse-access instrument;
- whether exposing current task identity without reward shaping is necessary
  before judging exploration algorithms;
- if the observation contract is retained, which one structurally different
  non-skill mechanism targets coordinated persistent occupancy rather than
  undirected breadth.

## Single Next Decision Boundary

Before another algorithm implementation, externally audit the Alice--Bob
information/access contract. The leading controller hypothesis is an
observation-only substrate repair: expose the currently active button and
target identities to both actors while retaining collection-only reward, then
test whether matched constant-code recurrent MAPPO crosses a positive-access
floor. This would validate the environment as an algorithm test substrate, not
count as an algorithm contribution. If rejected, the review must name one
structurally different non-skill causal edge and explain why it can overcome
the observed coverage-without-access failure.
