# Final GPT-5.6 Pro correction: R35-CBF is direct IFEPG

The first correction correctly retracted R35-OCSF, but its replacement
R35-CBF again violates the retired-route boundary. Do not implement or defend
R35-CBF.

## Exact contradiction

R35-CBF defines between-slot trajectory distance `D`, same-slot replica noise
`N`, and then updates the low actor with:

```text
L_CBF = -E[log pi(a|o,z) * A_CBF(D,N)]
```

That is the R32 direct individual-effect score-function gradient. Replacing the
phrase "existing skill" with "random latent assignment" does not change:

- the K=4 slot intervention;
- the low-policy conditioning variable;
- the between/within persistent-effect estimand;
- the focal action log-likelihood gradient;
- the attempt to create semantics by directly maximizing that effect.

For this project, any update in which an individual `do(z)` trajectory
effect/distance/separation supplies `A` in `sum log pi(a|o,z)*A` is part of the
retired R32 family, whether described as reward, value, auxiliary policy
gradient, controllability, or formation. Random slot assignment, a fixed
embedding, and removal of the classifier do not create an exception.

R32 already found a valid but immaterial causal shift and permanently retired
direct IFEPG, including changes to parameter scope, effect representation,
update count, window, replica, label treatment, and capacity. The original R34
question and correction 1 both explicitly prohibited this route.

The proposed shuffled-slot null is also not valid. Post-collection relabeling
uses a behavior likelihood for the wrong conditioned policy; pre-execution
relabeling under uniformly sampled symmetric slots is only a permutation of the
same mechanism. The proposed update count/epoch/window totals do not define
fresh on-policy collection after the actor changes.

The stated mathematics is internally inconsistent as well: the registered
ratio uses `D/(N+epsilon)`, but `A_CBF=D-mean(D)` contains no gradient from `N`.
It therefore optimizes neither the written ratio nor within-slot consistency.

Controller disposition:

```text
R35-OCSF: REJECTED old-label classifier reward
R35-CBF:  REJECTED direct IFEPG revival
NO R35 IMPLEMENTATION OR COMPUTE AUTHORIZED
```

## Final requested decision

Do not offer a third renamed classifier, effect-gradient, cluster/distillation,
or selector objective. Choose exactly one of these scientifically honest
outcomes:

1. **REPLACE THE DISCRETE SKILL OBJECT.** Specify one new executable policy
   object whose formation objective is not supervised recovery of any skill or
   cluster label, not a reward/advantage/gradient derived from pairwise
   between-skill trajectory effect, not post-hoc trajectory clustering or
   cloning, and not high-roster fitting, team-latent revival, task shaping, or
   scheduling mechanics.
2. **ABANDON THE CURRENT SKILL-FORMATION PROGRAM.** State that the present
   evidence does not authorize another intrinsic mechanism and identify one
   simpler non-skill algorithmic baseline/direction that should replace it.

Select one, not both. If choosing replacement, the old K=4 numerical slots must
not silently survive under a new name unless you prove why that interface is a
necessary property rather than a historical convenience.

## Requirements if choosing a replacement object

- State the new causal edge and why R29--R34 do not already test it.
- Give its mathematical training objective and show explicitly that no
  `q(label|trajectory)`, `log q` intrinsic term, pairwise skill-effect advantage,
  centroid/prototype label, or roster score appears in the policy gradient.
- Define tensor/recurrent flow, policy inputs, gradient recipients, detach
  boundaries, frozen modules, and whether R30 KEEP/SET is removed, adapted, or
  retained.
- Give the smallest Alice--Bob gate with a frozen-source anchor and one
  mechanism-matched control. Evaluation may use heldout `do(intervention)`
  persistent effects, but the training objective must not optimize that same
  registered evaluation score.
- Start at the lowest promotion level justified by evidence. Do not jump to
  normal reward-on PPO.
- Register exact independent per-arm on-policy exposure, optimizer calls,
  CRN, bootstrap unit, metrics, material thresholds, M0 checks, and mutually
  exclusive PASS/FAIL/INVALID branches.
- No tuning, UNDERPOWERED, threshold revision, or automatic seed expansion.

## Requirements if abandoning the program

- State the reusable negative conclusion precisely without claiming that all
  hierarchical MARL is impossible.
- Name exactly one replacement baseline/direction and the smallest decision
  gate that would justify pursuing it.
- Explain what happens to R30 KEEP/SET and the decoupled-lifetime hypothesis.

## Requested answer structure

1. `SECOND CORRECTION ACCEPTED` or one estimand-level proof that CBF is not
   direct IFEPG.
2. Exact permanent disposition of R35-CBF.
3. Exactly one choice: replacement object or program abandonment.
4. Complete algorithm and one source-anchored gate for that choice.
5. Supported and prohibited claims.

## Repository files to inspect

- `docs/external-review/gpt5_6_pro/20260715_r34_bhmd_gate_result/GPT5_6_PRO_QUESTION.md`
- `docs/external-review/gpt5_6_pro/20260715_r34_bhmd_gate_result/RESPONSE_RAW.md`
- `docs/external-review/gpt5_6_pro/20260715_r34_bhmd_gate_result/GPT5_6_PRO_CORRECTION_1.md`
- `docs/external-review/gpt5_6_pro/20260715_r34_bhmd_gate_result/RESPONSE_CORRECTION_1_RAW.md`
- `docs/external-review/gpt5_6_pro/20260715_r34_bhmd_gate_result/DISPOSITION_CORRECTION_1.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/CURRENT_WORK.md`
- `memory/LTM/R29_R33_EFFECT_COMPOSITION_FAILURE_REVIEW_20260714.md`

Read the complete chain before answering. Return one route only.
