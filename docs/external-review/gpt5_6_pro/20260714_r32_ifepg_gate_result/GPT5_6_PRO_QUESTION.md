# GPT-5.6 Pro Review Request: Route After R32-IFEPG FAIL

Please inspect the repository implementation and the tracked result JSON before
answering. We need a validity audit and exactly one structurally different R33
causal edge, not a menu of algorithms.

## Research chain

- **R29 actor density ratio:** natural skill-conditioned action separation
  existed, but its online endpoint reward did not preserve the R26 signal and
  failed score/task-safety gates. The online R29 family was retired.
- **R31 natural-window CFEI:** natural effects were classifiable
  (`G_nat=0.487866`), but the direct forced-skill between/within median ratio was
  `0.889613`, CI `[0.763227, 1.078315]`. This exposed association without causal
  persistent skill effects, so R31 was retired.
- **R32 IFEPG:** randomized fixed-window interventions directly optimized
  effect separation, with gradients restricted to the low actor skill-FiLM.
  The registered paired mechanism gate is now complete and returned
  `FAIL_M1_RETIRE_R32_IFEPG`.

R30 remains the controller substrate: fixed `k0` checks, asynchronous
`KEEP/SET(other_skill)` lifetimes, no learned duration action, and sparse
collection-only Alice--Bob reward. The result makes no task-efficacy,
cooperation, HMASD-parity, or transfer claim.

## Frozen R32 mechanism and gate

Both arms started from the same frozen adaptive-R30 checkpoint and natural
context bank. For each context, the focal agent was forced to each of four
skills for `W=10`, with two independent stochastic replicas per skill. For each
skill pair, R32 used

`U(z,z') = <E_z^1 - E_z'^1, E_z^2 - E_z'^2>`

and the signed context score `S_c = mean_pair(U) / 8`. A leave-one-context
standardized advantage drove one PPO-clipped focal likelihood update. The real
arm updated only `low.actor_film.parameters()`; the probe arm performed the
same data collection without optimization. There was no posterior/scorer,
intrinsic reward, task-reward objective, critic/value/GAE loss, entropy bonus,
high-policy update, or update to actor base/RNN/action head/log-std.

Registered budget: paired seed `32031`; 256 source contexts and 128 heldout
contexts; 20 auxiliary updates; 32 contexts/update; four skills; two replicas;
one epoch; PPO clip `0.10`; grad clip `0.5`; 51,200 training shadow steps per
arm; 10,240 heldout common-random-number steps per arm; and 64 paired stochastic
natural episodes (5,120 steps per arm).

## Result

**M0 implementation validity: PASS.** Every registered check passed: exact
context/replica/update/evaluation counts, paired initial parameters and context
schedule, replayed-versus-stored log-probability tolerance, zero probe drift,
finite nontrivial real FiLM drift, zero non-FiLM gradient/drift, and no
critic/high/posterior/environment-reward update.

**M1 heldout causal separation: FAIL.** The real median ratio was `1.015540`,
CI `[0.877865, 1.207808]`, against the registered requirement `>=1.50` with CI
lower bound `>1`. The paired real-minus-probe median gain was positive but only
`0.028746`, CI `[0.024775, 0.033320]`, against the material-gain threshold
`>=0.40`. Real pooled skill ratios were `{0: 0.658951, 1: 0.998809,
2: 1.374737, 3: 2.150302}`; the contract required every skill to exceed one.

**M2 noise-pathology gate: FAIL.** The between-effect real/probe ratio was
`1.029965` rather than `>=1.50`, although its paired raw-gain CI was positive
`[0.003052, 0.003576]`. The within-effect ratio was `0.998550` and therefore
respected the `<=1.25` noise ceiling. The update produced a small detectable
change, not the precommitted magnitude of causal separation.

**M3 natural transport: FAIL; R30 safety: PASS.** Natural joint-position union
coverage was `553/546`, ratio `1.012821` rather than `>=1.10`; paired-reset
coverage-gain CI `[-0.000125, 0.000725]` crossed zero. Both arms passed the R30
safety floors (`full_sync_SET=0.158482`, switch entropy `0.995952`, minimum
long/short spell share `0.110169`).

## Hard disposition constraints

Do not rescue R32 by changing its learning rate, window, replica count, update
count, effect vector, estimator threshold, seed count, or FiLM capacity. Do not
restart, expand, or integrate direct IFEPG into the normal trainer. If the
result is valid, direct individual-effect IFEPG is permanently retired. If you
find it invalid, identify one concrete implementation/estimator defect that
invalidates M0; speculative underpowering or hyperparameter arguments do not
reopen the route.

## Requested decision

1. Audit whether `FAIL_M1_RETIRE_R32_IFEPG` is a valid scientific failure under
   the registered implementation and estimator. Separate a concrete M0 defect
   from an algorithmic failure.
2. If valid, state the reusable causal lesson from the positive-but-tiny M1/M2
   change and retire direct IFEPG without a rerun.
3. Select **exactly one** structurally different R33 causal edge. Explicitly
   decide whether the project should move from maximizing each skill's
   individual fixed-window effect to learning **team complementarity** (joint
   effects or role-free division of labor), rather than continuing to optimize
   individual effect magnitude. Do not offer parallel alternatives.
4. Specify one implementable R33 algorithm: mathematical objective and
   estimator; intervention/randomization semantics; policy inputs; exact
   gradient recipients, detach boundaries, and frozen modules; interaction
   with R30 `KEEP/SET`; and what remains diagnostic-only.
5. Give the smallest Alice--Bob **abandonment gate** that can permanently
   falsify R33. Precommit comparator arms, source/heldout construction,
   stochastic execution, numerical metrics and thresholds, compute budget, M0
   validity checks, and exact PASS/FAIL branches. There must be no
   `UNDERPOWERED` or post-result retuning branch.
6. Name the exact files to add or modify, keeping R33 outside normal training
   until its mechanism gate passes.

## Repository files to read

- `docs/external-review/gpt5_6_pro/20260714_r31_cfei_gate_result/RESPONSE_RAW.md`
- `docs/external-review/gpt5_6_pro/20260714_r31_cfei_gate_result/DISPOSITION.md`
- `ha_ctse_process/r32_interventional_effect_pg.py`
- `ha_ctse_process/standalone_agent.py`
- `scripts/r32_ifepg_gate.py`
- `logs/r32_ifepg_paired_gate_20260714_193304/result/r32_ifepg_pair.json`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/LTM/R29_R31_EFFECT_REWARD_FAILURE_REVIEW_20260714.md`

Please return one decisive route with a falsifiable causal edge and a complete
minimal gate contract. Do not claim sparse-task improvement from this gate.
