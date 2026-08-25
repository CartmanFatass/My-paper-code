# GPT-5.6 Pro Review Request: R36 Valid Failure And The Alice--Bob Access Instrument

Please inspect the tracked R36 result and implementation before answering. We
need one audited verdict and one decisive next boundary. Do not return a menu.

## Current controller verdict

```text
R36 status = FAIL_M1_RETIRE_R36_AEM
implementation_valid = true
```

Subject to your code audit, permanently retire the exact R36 direct 625-cell
episodic joint-position bonus. Do not rescue it by changing grid resolution,
count horizon, bonus formula/scale, network, steps, seed, PPO exposure, or gate.

## Why R36 was run

R35 compared trained observation/history-only constant-code recurrent MAPPO
with trained reward-pure R30 from one neutral zero-step initialization. Both
valid 320K arms had zero final-evaluation collections, so R35 ended as
`NO_ACCESS_R35_UNRESOLVED` and no hierarchy comparison was interpretable.

R36 isolated one access-first non-skill edge:

```text
task-generic episodic joint-position novelty
-> broader reachable-state visitation
-> first sparse collection access
```

Both R36 arms used the same constant-code recurrent MAPPO actor and centralized
critic. The treatment added one detached shared collector bonus to low GAE:

```text
cell = direct arithmetic 5 x 5 x 5 x 5 joint-position index
b_t = 1 / (80 * sqrt(preincrement_episode_count(cell) + 1))
r_low_t = r_sparse_t + b_t
```

Counts were per vector environment and reset only at episode boundaries. The
bonus used only both agents' normalized positions. It was not an actor/critic
input. Evaluation used pure collection-only reward.

Each arm used seed 37031, CUDA, 16 spawn environments, rollout 80, 320,000
steps, 250 low updates, five PPO epochs, recurrent sequence length 10/batch 64,
and 64 paired stochastic 80-step evaluation episodes.

## Exact result

M0 passed without an invalid reason:

```text
both arms: 320,000 steps, 250 low updates, 64 evaluations
treatment AEM applied steps: 320,000
treatment formula max error: 0
treatment forbidden-field reads: 0
control AEM exposure: 0
both sparse evaluation reward exact: true
```

M1 access failed:

```text
treatment cycle-success mean = 0.0                  floor 0.05
treatment collection episodes = 0/64                floor 10/64
paired collection-indicator mean and CI = 0 [0, 0] floor 0.10, lower > 0
```

The registered visitation carrier changed strongly but did not transport:

```text
AEM mean 625-cell joint coverage = 0.063900
control mean coverage            = 0.016575
ratio                            = 3.855204
paired difference                = 0.047325
95% CI                           = [0.045400, 0.049175]

both arms cycle success          = 0
both arms collection episodes    = 0
both arms zero-cycle fraction    = 1.0
```

Thus R36 is not a weak-mechanism result: the registered reward substantially
changed natural visitation. Its causal carrier implication failed.

## Alice--Bob information contract that now requires audit

The two-agent world is size 8. Each active landmark has contact radius 0.70.
A collection occurs only when different agents simultaneously occupy the
active button and active target. The target changes every 10 steps and the
button every 40 steps.

The decentralized actor observation includes:

- own position;
- relative position of the other agent;
- offsets to both candidate buttons;
- offsets to both candidate targets.

It deliberately excludes:

- which button is active;
- which target is active;
- the short and long task clocks;
- contacts, collection state, and reward progress.

The initial active button and target are sampled randomly. The centralized
critic state, unlike the actor observation, contains active one-hots and both
clocks. Before the first reward, the actor cannot infer the initially sampled
active identities from its observation history. Also, one R36 grid bin is
`8/5 = 1.6` wide per axis, so coarse cell coverage does not imply contact within
radius 0.70.

This does not invalidate R36. It raises a more upstream question: is the
current Alice--Bob observation contract a valid sparse-access instrument for
deciding algorithms, or are we repeatedly testing exploration behind a hidden
task-identity bottleneck?

## Leading controller hypothesis

The leading next boundary is not another intrinsic reward. It is an
observation-only substrate audit:

```text
actor-visible current active button/target identity
+ unchanged collection-only sparse reward
-> positive access under constant-code recurrent MAPPO
-> only then resume algorithm comparisons
```

This would be an environment/instrument repair, not an algorithm contribution.
No distance/progress/contact reward, potential, curriculum, demonstrations, or
oracle action would be added. R30 would remain diagnostic-only until the
substrate has positive access.

## Requested decision

1. Audit R36 sampling, reward injection, per-environment reset, low-GAE-only
   path, control isolation, pure sparse evaluation, access metrics, coverage
   metric, bootstrap, and branch order. Return either
   `VALID_FAIL_M1_RETIRE_R36_AEM` or identify one concrete estimand-changing
   implementation defect.
2. If valid, state precisely what the `3.855x coverage / zero access` result
   establishes and cannot establish. Coverage must not override M1.
3. Audit the Alice--Bob information structure. Decide whether hidden randomly
   initialized active identities make this an unsuitable or needlessly
   pathological access gate for decentralized actors.
4. Accept, modify, or reject the leading observation-only substrate repair.
   Return exactly one next route:
   - preferably one minimal environment/access-instrument gate; or
   - if the benchmark cannot support a meaningful task-generic access floor,
     retire this sparse Alice--Bob gate and specify the minimum observation,
     horizon, and random/ordinary-policy access-floor contract for one
     replacement benchmark; or
   - if you reject that diagnosis, one structurally different task-generic
     non-skill causal edge that directly addresses coordinated persistent
     occupancy rather than undirected state breadth.
5. Specify the selected route completely: exact observation/information
   boundary, actor/critic inputs, reward and gradient paths, updated/frozen
   modules, comparator, initialization, seed, steps, updates, evaluation,
   metrics, thresholds, validity checks, mutually exclusive result branches,
   and one authorized next action per branch.
6. A substrate-repair PASS may establish only that Alice--Bob is access-viable
   under the repaired observation contract. It must not be called an algorithm
   improvement or paper result.

## Prohibited next routes

Do not propose:

- another R36 grid/count/scale/horizon/budget/seed variant;
- RND, ICM, or a learned novelty model as a cosmetic replacement for the same
  undirected state-breadth edge without explaining a new causal carrier;
- task distance/progress/contact reward, potential shaping, demonstrations,
  curriculum, oracle actions, or privileged actor inputs beyond the explicitly
  audited current-task identity;
- a new skill, option, subgoal, latent codebook, trajectory label, roster
  scorer, classifier, `q_d/q_D`, team reward, or communication reward;
- R29--R34, OCSF, CBF, TMPF, duration/hazard/scheduler, or other retired route;
- a seed, step, threshold, coefficient, or optimizer sweep;
- an efficacy, cooperation, hierarchy, HMASD, S7, or paper-level claim.

Return one decisive audited route only.

## Repository files to inspect

- `memory/LTM/R35_R36_SPARSE_ACCESS_FAILURE_REVIEW_20260715.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/CURRENT_WORK.md`
- `memory/ExpRecord.md`
- `envs/pettingzoo/alice_bob_asymmetric_cycles.py`
- `ha_ctse_process/config_alice_bob_sparse_mappo.py`
- `ha_ctse_process/config_alice_bob_aem.py`
- `ha_ctse_process/train.py`
- `scripts/run_r36_aem_access_local.ps1`
- `scripts/analyze_r36_aem_access.py`
- `logs/r36_aem_access_320k_20260715_034611/result/r36_aem_access.json`
