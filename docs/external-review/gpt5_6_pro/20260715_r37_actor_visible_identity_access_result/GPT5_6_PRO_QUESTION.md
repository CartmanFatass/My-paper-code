# GPT-5.6 Pro Review Request: R37 Valid Failure And One Replacement Benchmark

Please audit the tracked implementation and exact result before answering. We
need one verdict and one replacement benchmark/access gate. Do not return a
menu or attempt to rescue R37.

## Current controller verdict

```text
R37 status = FAIL_R37_ACCESS
implementation_valid = true
```

Subject to your code audit, retire the current sparse
`alice_bob_asymmetric_cycles` environment as an algorithm-comparison gate under
the registered 80-step horizon and 320K-step ordinary-policy budget.

## Why R37 was run

R35 could not compare constant-code recurrent MAPPO with reward-pure R30 because
both matched arms had zero access. R36 then expanded coarse joint-position
coverage `3.8552x` without one collection. The R36 audit found that the actor
could see all candidate landmark positions but not which randomly initialized
button and target were active, while the centralized critic did see that
identity.

R37 isolated this upstream information edge:

```text
actor-visible current active plate/target identity
-> removal of the hidden-information bottleneck
-> robust ordinary-policy sparse access
```

This was an environment/access-instrument gate, not an algorithm contribution.

## Exact intervention and exposure

Both arms used the same 16-value actor layout, parameter count, recurrent MAPPO
actor, 19-value centralized critic, sparse collection-only reward, optimizer,
and common neutral zero-step checkpoint.

```text
actor observation = [historical 12 values,
                     active-plate slots (2),
                     active-target slots (2)]

identity_visible: final four slots = current true one-hots
identity_masked:  final four slots = constant zero
```

No clock, contact, progress, reward-derived field, future state, distance,
oracle action, skill, high policy, latent, classifier, intrinsic reward, or
shaping path was active. Only the low actor and centralized critic updated.

Each arm used seed 38031, CUDA, 16 spawn environments, rollout 80, 320,000
environment steps, 250 low updates, five PPO epochs, recurrent sequence length
10/batch 64, and 64 paired stochastic 80-step evaluations. All 640,000 actor
rows per arm passed the online identity audit with zero slot/critic error.

## Exact result and branch

M0 implementation validity passed. Both arms completed the exact exposure and
had identical shapes/parameter counts, shared initialization, sparse reward,
paired reset seeds, and no high/intrinsic updates.

```text
                                      identity_visible  identity_masked
collection episodes / 64             10                0
cycle-success mean                    0.01953125        0
mean sparse reward                    0.15625           0
zero-cycle fraction                   0.84375           1.0
mean joint-position coverage          0.035275          0.021975
```

Paired visible-minus-masked effects:

```text
collection indicator  0.15625    95% CI [0.078125, 0.25]
cycle success         0.01953125 95% CI [0.009765625, 0.03125]
sparse reward          0.15625    95% CI [0.078125, 0.25]
coverage               0.01330    95% CI [0.01175, 0.014775]
zero-cycle fraction   -0.15625    95% CI [-0.25, -0.078125]
```

The collection count floor (10/64) and paired collection CI lower bound both
passed. M2 sparse-task evidence and M3 stability passed. M1 failed only because
the visible-arm cycle-success mean was `0.01953125`, below the registered
`0.05` floor. In the result JSON,
`paired_collection_indicator_ci_lower_strict = 0` is the threshold, not the
observed CI lower endpoint.

The registered branch is unambiguous: any valid M1--M3 miss is
`FAIL_R37_ACCESS`, retires this sparse Alice--Bob gate, and requires a
replacement benchmark's observation, horizon, and ordinary-policy access floor
before more algorithm work. There is no threshold, seed, step, or budget
expansion branch.

## Reusable causal interpretation

The intervention is strong and coherent: exposing current task identity caused
nonzero collection, cycle, reward, coverage, and stability improvements, while
the capacity-matched masked arm stayed at zero access. Hidden task identity was
therefore a real benchmark bottleneck.

However, the full implication still failed. Identity repair made the task
occasionally accessible but did not establish a robust enough ordinary-policy
floor for comparing skill or temporal algorithms. M2/M3 cannot override M1.

## Replacement benchmark requirements

The next substrate must remain a general cooperative MARL mechanism test, not a
task-shaped shortcut. It should:

- use sparse external task reward with no distance/progress/contact potential;
- expose the current task state needed for decentralized execution without
  assigning either agent a role or giving oracle actions;
- contain genuinely different short and long cooperative task timescales so a
  later fixed/shared versus per-agent-lifetime comparison is meaningful;
- be small enough for rapid local CUDA iteration;
- give an ordinary recurrent MAPPO policy a predeclared, reproducible positive
  access floor before any R30 or skill comparison;
- separate a random-policy sanity bound from the trained ordinary-policy floor;
- define one horizon and budget in advance, with no rescue branch after result.

Repository candidates exist, but you must choose exactly one route rather than
returning alternatives:

1. audit and, only if necessary, minimally regularize the historical 200-step
   continuous Alice--Bob environment;
2. specify one new minimal two-agent/two-timescale sparse benchmark; or
3. use S7-S1 with a deliberately bounded ordinary-policy access/calibration
   gate if no fast local environment can be scientifically valid.

The controller has not accepted any of these yet.

## Requested decision

1. Audit R37 environment construction, capacity-matched observation switch,
   common checkpoint, recurrent actor/critic data flow, per-step identity audit,
   sparse reward, paired evaluation/bootstrap, result analyzer, and branch
   order. Return either `VALID_FAIL_R37_ACCESS` or identify one concrete
   estimand-changing implementation defect.
2. If valid, state exactly what the coherent visible-minus-masked effects prove
   and what the failed cycle floor prevents us from claiming.
3. Decide whether the current 80-step asymmetric-cycle Alice--Bob gate must be
   retired exactly as registered. Do not reinterpret M2/M3 as an overall PASS.
4. Select exactly one replacement benchmark/access route. Specify its complete
   environment contract: task dynamics and two timescales, decentralized actor
   observation, centralized critic state, horizon, sparse reward, terminal and
   reset semantics, and information forbidden to the actor.
5. Specify the complete minimum access gate: ordinary policy and random/sham
   comparator, shared initialization, model/update exposure, seed, environments,
   steps, optimizer updates, stochastic evaluation, metrics, thresholds,
   bootstrap/nulls, validity checks, mutually exclusive branches, and one next
   action per branch.
6. State which existing repository files can be reused and the smallest new or
   modified file boundary. The access gate must run before any algorithm
   implementation and may establish only benchmark viability.

## Prohibited next routes

Do not propose:

- rerunning or rescuing R37 by changing its horizon, contact radius, world
  geometry, threshold, budget, seed, PPO settings, or adding identity variants;
- treating the passed collection CI, M2, or M3 as permission to ignore M1;
- distance/progress/contact shaping, potential rewards, curriculum,
  demonstrations, scripted/oracle actions, privileged role labels, or future
  state in the actor;
- a new skill, option, subgoal, latent, codebook, classifier, `q_d/q_D`, team
  reward, intrinsic reward, scheduler, hazard, duration head, roster scorer, or
  algorithm mechanism before the replacement access floor passes;
- R29--R36, OCSF, CBF, TMPF, IFEPG, IRSC, BHMD, AEM, RND, or ICM rescue;
- a seed/step/threshold/optimizer sweep or parallel route;
- an efficacy, cooperation, hierarchy, decoupled-lifetime, HMASD, S7, or
  paper-level claim from this access gate.

Return one decisive audited route only.

## Repository files to inspect

- `memory/LTM/R35_R37_SPARSE_ACCESS_FAILURE_REVIEW_20260715.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/CURRENT_WORK.md`
- `memory/IMPLEMENTATION_PLAN.md`
- `memory/ExpRecord.md`
- `docs/external-review/gpt5_6_pro/20260715_r36_aem_access_result/DISPOSITION.md`
- `envs/pettingzoo/alice_bob_asymmetric_cycles.py`
- `envs/pettingzoo/continuous_alice_bob.py`
- `config_continuous_alice_bob.py`
- `ha_ctse_process/config_alice_bob_sparse_mappo.py`
- `ha_ctse_process/config_alice_bob_identity_masked.py`
- `ha_ctse_process/config_alice_bob_identity_visible.py`
- `ha_ctse_process/standalone_agent.py`
- `ha_ctse_process/train.py`
- `ha_ctse_process/plotting.py`
- `scripts/run_r37_actor_visible_identity_access_local.ps1`
- `scripts/analyze_r37_actor_visible_identity_access.py`
- `logs/r37_actor_visible_identity_access_320k_20260715_090205/result/r37_actor_visible_identity_access.json`
