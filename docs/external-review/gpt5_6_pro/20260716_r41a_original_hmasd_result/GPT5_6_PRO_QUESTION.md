# GPT-5.6 Pro Review — R41A Original HMASD Alice–Bob Result

Date: 2026-07-16

## Review boundary

This is automated consultation round 1 of at most 3 sequential rounds. Review
the repository state at the exact commit named in the handoff prompt. Do not
answer from prior conversation memory alone.

The project needs a fixed-`N`, fixed-`k` learned HMASD anchor before it can test
the native categorical R30 `KEEP/SET` temporal decoupling on the same task and
checkpoint. Variable team membership is a later orthogonal axis; it must not be
introduced while the fixed-`N` anchor is unresolved. Intrinsic reward must
remain environment-agnostic and may not consume task identities, goals,
contacts, phases, distances, success predicates, or external reward.

R35–R40 closed the custom/public substrate-search loop. The accepted next edge
was therefore to execute the original HMASD source and its own Alice–Bob task,
not another custom toy and not HA-CTSE-specific shaping.

## Experiment and result

R41A freshly extracted tracked `ref/hmasd.tar` and executed the copied original
source without porting it into the current trainer. It preserved the original
environment, reward, `k=50`, `n_Z=2`, `n_z=4`, network settings, PPO epochs,
optimizer coefficients, and deterministic evaluator.

The resource-bounded pilot used:

- seed 1;
- CUDA;
- 16 rollout environments;
- 100-step episodes;
- 937 outer updates;
- 1,499,200 environment steps;
- 14,055 optimizer steps for each of high policy, low actor, low critic,
  `q_D`, and `q_d`;
- exact zero-step and exact-final evaluation on the same 100 deterministic
  reset streams.

This preserves the original number of outer/optimizer updates but uses half the
32-env batch and half the approximately 3M environment transitions of the
full source configuration. It is intentionally not a full reproduction.

The registered result is:

```text
status = NO_ACCESS_R41A_HMASD_ALICE_BOB_LOCAL_PILOT
implementation_valid = true
M0 = PASS
high replay error = 0.0
low replay error = 0.0
global replay error = 0.0
M1 = FAIL: exact-final win rate 0.0 < 0.50
M2 = FAIL: final-minus-zero 0.0, 95% CI [0.0, 0.0]
```

All five optimizer paths completed exactly 14,055 nonzero finite-gradient
steps. The learning trace contains 188 logged training points and 38
intermediate deterministic evaluations:

- training win rate peaked at only `0.0125`;
- training key0/key1 rates peaked at `0.4875` / `0.15`, but their means were
  `0.03856` / `0.02473`;
- intermediate deterministic win rate was always `0`;
- intermediate deterministic key0/key1 maxima were `0.09` / `0.01`;
- every evaluation from update 700 through 925 had win/key0/key1 all `0`;
- exact zero-step and exact-final win rates were both `0`.

The registered branch says this valid single-seed reduced-batch pilot cannot
retire the paper-task route or authorize R30. Its next action is to review the
original-source learning trace.

## Repository files to inspect

Read all of the following before deciding:

1. `memory/ALGORITHM_PRINCIPLES.md`
2. `memory/IMPLEMENTATION_PLAN.md` — R41A section
3. `memory/ExpRecord.md` — `EXP-20260716-r41a-hmasd-alice-bob-local-pilot`
4. `docs/research/decisions/R35_R40_SUBSTRATE_FAILURE_REVIEW_20260715.md`
5. `scripts/run_r41_official_hmasd_seed.py`
6. `scripts/run_r41_official_hmasd_local.ps1`
7. `scripts/analyze_r41_official_hmasd_anchor.py`
8. `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/r41a_hmasd_alice_bob_local_pilot.json`
9. `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/seed1_result.json`
10. `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/R41A_TRACE_SUMMARY.json`
11. `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/R41A_SEED1_TRAINING_TRACE_RAW.txt`
12. Every copied source file under
    `docs/external-review/gpt5_6_pro/20260716_r41a_original_hmasd_result/original_source/`,
    especially the Alice–Bob environment, train entry, runner, MAT high policy,
    recurrent MAPPO low policy, discriminator, and three buffers.

The copied source files are review-only evidence from the fresh extraction.
The experiment itself executed the fresh tree under the run root.

## Requested decision

Produce one explicit verdict and one unique next causal edge.

### 1. Validity and learning-trace audit

Decide whether `NO_ACCESS_R41A_HMASD_ALICE_BOB_LOCAL_PILOT` is a valid result
for this reduced-batch contract. Look for a concrete defect in the wrapper,
arguments, source update path, reward flow, recurrent likelihood, evaluator,
checkpoint, environment, or exposure accounting that could change the result.

- If such a defect exists, return `INVALID_R41A_<specific defect>` and specify
  the minimal external-wrapper/source-contract repair that permits one unchanged
  rerun. Do not call ordinary stochastic failure or weak learning a defect.
- Otherwise return `VALID_NO_ACCESS_R41A` and state precisely what the trace
  rules out and what it does not rule out.

### 2. Unique next action

If R41A is valid, choose exactly one next action rather than parallel options:

- an exact original 32-env, approximately 3M-step source reproduction for one
  access seed before any multi-seed expansion;
- the already contemplated full five-seed reproduction;
- or a different evidence-bearing action only if the inspected source/result
  proves why another full source run would be scientifically uninformative.

Specify the exact environment count, seeds, environment steps, outer updates,
optimizer exposure, evaluator, success/abandonment gate, and what happens on
PASS versus NO_ACCESS. Equal optimizer-update count alone must not be treated
as equivalent to the original 32-env sample/batch contract.

### 3. Algorithm boundary after the anchor

State whether a positive exact source anchor would authorize the next native
categorical R30 `KEEP/SET` temporal gate on the same environment/checkpoint,
and define the minimum mechanism-matched comparator. Do not authorize R30,
open-roster/variable-`N`, a new team latent, or a new intrinsic reward before
the prerequisite evidence you identify actually passes.

### 4. Prohibited rescue

Do not repair this outcome by changing intrinsic reward, adding shaping,
changing the environment, selecting a favorable checkpoint, increasing model
size, retuning learning rates/entropy coefficients, relaxing thresholds, or
returning to any R29–R40 retired route. Do not propose multiple simultaneous
research branches.

End with:

1. the exact verdict token;
2. reusable causal conclusions;
3. the single next experiment or implementation edge;
4. its minimal abandonment gate;
5. explicit prohibited changes.
