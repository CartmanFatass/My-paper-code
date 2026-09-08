# FSD native-renewal learning B01 technical acceptance

P34 implementation delivered in `C:/Projects/HMASD-worktrees/codex-fsd`, branch
`codex/fsd`, from clean `e1549c8bee6777720e083255dca5777853c08feb` (complete
starting source `ebce42e23e8a86b4e8d44f840441d166828fbe54`). The P34 allocation
supplies implementation authority after the prospective card/spec preparation;
the three comparison batches were exhausted, so this is not a fourth batch.

Contract: [CM specification §§3–6](FSD_NATIVE_RENEWAL_LEARNING_B01_CM_SPEC_20260908.md)
and [card §§2–4,6–7](FSD_NATIVE_RENEWAL_LEARNING_B01_SCIENCE_CARD_20260908.md).
Only the new runner, its focused test file and this record change. Core,
configuration, host, E0/E2/E3/A01, scientific cards and historical evidence remain
at their existing source. No ENGINEERING_SCOPE_SPEC §4 machinery is added.

## Delivered source and boundaries

- [Runner](../../../../scripts/run_fsd_native_renewal_learning_b01.py): 445 lines.
  Fresh C/H learners use the existing large/D2 configuration builder, seed770203,
  CPU/four Torch threads before construction. The original sampled step_data and
  actions reach real transition storage with each adapter's float64 native reward.
  H changes only the separately copied applied mask after episode step zero.
- Terminal next state/observation are stored before adapter advancement/reset.
  Both next policy inputs use reset values. Five consumed ID blocks are recorded
  before advancement; update uses terminal done and zero terminal bootstrap.
  Actual E0 optimizer-call counts and initialization displacement, D2 row metrics
  and raw segment-length aggregates are captured after update and before clear.
- The E2 independent evaluator constructor, module/normalizer synchronization,
  lane reset and all deterministic/no-grad scoring are inside E0 `_preserve_rng`.
  Evaluator optimizer calls are separately counted. G constructs no learned agent.
- Float64 full/post arrays and H−C/G−H/G−C paired differences use the card's
  denominators and ddof1 SE. Opportunity-conditioned counts/rates include null for
  zero eligibility; native return remains independent of role diagnostics.
  Missing G limits only reference output. Missing/damaged C/H prevents a complete
  pair/reading while independently completed arm facts remain readable.
- Cooperative timing begins before heavy imports and covers setup, collection,
  updates, evaluation, paired arithmetic and publication. Every completed batch
  and update publishes partial counts with explicit denominators/status. No
  checkpoint, resume, sweep, fixture CLI, retry or launch is introduced.

## Focused checks and review

[Synthetic suite](../../../../tests/experiments/candidates/flexible_skill_duration/native_renewal_learning_b01/test_learning.py)
calls the production collector/evaluator/summary/main with fake agent/adapter
bindings and hand-computed arrays. It constructs no HMASDAgent or scientific host.
The E2 constructor/sync/reset and E0 counters/displacement/RNG helpers are exercised
with distinct fake parameter and ValueNorm state; the real config builder is
checked without a host or model. Native rewards deliberately differ with applied
masks, while stored masks/metadata and terminal/reset sentinels expose aliasing or
input mixing. Five fake update stages have unequal optimizer calls, including a
true observed zero, and later rollouts see updated fake parameters.

Final command, from the direction checkout:

```text
C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/flexible_skill_duration/test/b01-learning-final tests/experiments/candidates/flexible_skill_duration/native_renewal_learning_b01/test_learning.py
```

Final result: **18 passed**, pytest wall **3.33 s**, complete test-process wall
**4.4069052 s** measured around the process. Output is
`temp/directions/flexible_skill_duration/test/b01-learning-final-check.txt`.
The initial run was 13 passed/1 failed (pytest8.28s): the fake evaluator paired H3
with a cap40 configuration. The test now uses the existing parameter helper with
the fake horizon3; production constants did not change. The repair run passed18
in complete process4.2460821s; the final run strengthened own-reward and non-alias
coverage. All checks are within the 300s research-directory budget. Warnings are
the disabled-cache configuration warning and existing Pyparsing deprecations.

Independent source reviewer: native `fsd_integration_review`, reused for the
bounded recheck. It traced the mask/storage/D2 credit, terminal/reset,
E2 active-module/ValueNorm/RNG and E0 actual optimizer boundaries. Two material
publication findings were repaired:

1. Nonfinite initial norms or D2 metrics could enter JSON before validation and
   cause failure reporting itself to fail. They are now validated in local values
   first. Synthetic main tests retain readable incomplete output and actual
   construction/transition/update/optimizer counts for both failure cases.
2. Opening the only summary for replacement could erase the prior receipt during
   an external timeout. Publication now closes a same-directory temporary file
   before replacing `summary.json`. Interrupted/nonfinite-write tests prove that
   the prior readable completed boundary survives.

The reviewer rechecked both repairs and the added evaluator counters/comparison
fields: **no material findings remain**, no prohibited machinery. It inspected
test evidence without rerunning the suite. Source/check conformance does not
establish learning, real-run numerical stability or complete-runtime feasibility.

## Future invocation syntax and remaining execution boundary

No scientific invocation, actual model construction, checkpoint load, real
training transition, optimizer update, scientific host/evaluation episode or Pro
Send occurred in this implementation assignment. Synthetic fake method calls are
engineering checks only. No new cost probe or profile occurred.

Per-arm cost: [the prospective record](FSD_NATIVE_RENEWAL_LEARNING_B01_EXPOSURE_AND_COST_20260908.json)
retains the historical 505.86596735480975s anchor for each C/H and .27s for G.
The new segment-dependent update cost remains unmeasured; these anchors are not a
completion guarantee. Complete future caps remain C900s/H900s/G60s, summed
invocation wall1860s. Study critical path, actual summed wall and aggregate CPU
have not been observed. No arm, seed, count or cap was changed.

Post-learner publication coverage: the real new publication/pair path passed
synthetic complete-panel, missing-companion, damaged-primary, deadline and
nonfinite/interrupted-write checks. The final real evaluator/source bindings were
reviewed. Real model/runtime behavior remains untested under this assignment's
explicit no-model/no-host boundary.

The later allocation must name the output root, exact launch SHA, execution node,
fresh resource admission and existing supervisor handle. The card declares CPU
host portability and remote-first routing; no execution placement or fallback was
performed here. Intended commands, in G/C/H order, are:

```text
python scripts/run_fsd_native_renewal_learning_b01.py --policy G --seed 770203 --launch-sha <SHA> --out temp/directions/flexible_skill_duration/exp/<run>/G
python scripts/run_fsd_native_renewal_learning_b01.py --policy C --seed 770203 --launch-sha <SHA> --out temp/directions/flexible_skill_duration/exp/<run>/C
python scripts/run_fsd_native_renewal_learning_b01.py --policy H --seed 770203 --launch-sha <SHA> --out temp/directions/flexible_skill_duration/exp/<run>/H --c-summary temp/directions/flexible_skill_duration/exp/<run>/C/summary.json --g-summary temp/directions/flexible_skill_duration/exp/<run>/G/summary.json
```

Each later command requires its own complete-command OS timeout (60/900/900s)
around interpreter/import through publication, under the configured supervisor,
with no automatic retry. The cooperative timer cannot interrupt an individual
update. External observed wall is the authoritative complete cost; the JSON's
pre-publication wall is labelled accordingly. No execution is allocated here.

CM technical work ends at the reviewed scoped commit and immediate push. DM owns
scientific intake and any subsequent bounded execution decision through Root.
