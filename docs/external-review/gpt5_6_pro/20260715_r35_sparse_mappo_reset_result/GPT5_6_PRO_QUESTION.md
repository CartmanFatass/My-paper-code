# GPT-5.6 Pro Review Request: R35 Valid NO_ACCESS and One Non-Skill R36 Access Edge

Please inspect the exact R35 implementation and the tracked verbatim result
JSON before answering. We need:

1. an implementation-validity audit of R35;
2. a precise interpretation of `NO_ACCESS_R35_UNRESOLVED`;
3. exactly one next non-skill causal edge whose first purpose is to establish
   sparse-task access.

Do not compare performance after the registered access floor failed. Do not
rescue R35 by adding seeds, steps, thresholds, or tuning. Do not reopen the
retired R29--R34 skill-formation program.

## Current controller decision

The controller's current read is:

```text
R35 implementation_valid = true
R35 status = NO_ACCESS_R35_UNRESOLVED
```

Subject to your code audit, this is a valid registered no-access outcome, not a
MAPPO PASS, an R30 PASS, or an efficacy comparison.

A validity objection must identify a concrete defect that changes the executed
policy, initialization, reward path, optimizer exposure, evaluation
distribution, access count, or branch logic. Zero task reward by itself is not
an implementation defect.

## Why R35 was run

R29--R34 validly failed to identify, amplify, compose, or relabel a useful
persistent skill codebook. The subsequent OCSF, CBF, and TMPF proposals were
respectively rejected as:

```text
OCSF -> prohibited old-label classifier reward
CBF  -> the retired direct individual-effect policy-gradient estimand
TMPF -> no nonzero gradient path to the low actor or continuous-code generator
```

The current intrinsic skill-formation program was therefore closed. R35 was a
baseline reset, not a new paper contribution:

```text
shared neutral initialization
-> trained observation/history-only recurrent MAPPO
versus
-> trained sparse-reward R30
-> positive sparse-task access
-> only then interpret noninferiority
```

The access precondition was registered specifically because relative
noninferiority is undefined when both sparse-reward policies obtain no
collections.

## Registered R35 comparison

Both arms strictly loaded the same zero-environment-step R30 checkpoint at seed
`36031`.

### Arm A: `constant_code_mappo`

- Retains the same `n_z=4` low MLP/FiLM/RNN/action tensors and centralized
  recurrent critic tensors as R30.
- Every agent receives skill code `0` and team code `0` at every step.
- The high policy does not sample, store rows, receive gradients, or update.
- Constant conditioning makes the executed actor a function only of local
  observation and recurrent history; the unused code columns are retained for
  tensor/capacity matching.

### Arm B: `reward_pure_r30`

- Uses the same low stack.
- Uses the active fixed-clock autoregressive R30 `KEEP/SET` controller.
- The sparse external collection reward is the only policy/value reward.

Each arm used:

```text
CUDA
16 subprocess environments
rollout length = 80
environment steps = 320,000
low updates = 250
low PPO epochs = 5
recurrent sequence length = 10
sequence batch size = 64
64 stochastic final evaluation episodes, each 80 steps
paired reset seeds
```

The low actor/critic exposure is matched. R30's additional high update is the
intended treatment difference, not falsely counted as matched optimizer
exposure.

The implementation commit is `b372000`; the retry4 launch commit is `030d0cd`.
Earlier attempts failed before training because of status-file replacement or
sandbox-denied Windows process creation. Retry4 is the only scientific run and
used the unchanged registered parameters.

## Registered decision order

### M0 implementation validity

Both arms had to:

- load the same zero-step checkpoint;
- finish exactly 320,000 steps and 250 low updates;
- produce 64 final stochastic evaluation episodes;
- preserve identical low tensor shapes;
- use exact sparse collection reward;
- apply no intrinsic or environment-shaping reward.

The constant arm additionally had to produce zero high decision and update
rows.

### M1 positive access

Noninferiority could be interpreted only if both conditions held:

```text
max arm mean normalized cycle success >= 0.05
paired reset indices with >=1 collection in either arm >= 10 of 64
```

Failure gives `NO_ACCESS_R35_UNRESOLVED` and blocks all M2 interpretation.

### M2 noninferiority

This was registered but is not scientifically reachable after M1 failed. With

```text
D = constant_code_mappo - reward_pure_r30
```

the margins were cycle success `-0.10`, normalized joint-position coverage
`-0.05`, and zero-cycle fraction `+0.10`.

## Exact terminal result

The single tracked result reports:

```text
implementation_valid = true
status = NO_ACCESS_R35_UNRESOLVED
```

M0 evidence:

```text
                                constant MAPPO       reward-pure R30
train steps                    320,000              320,000
low updates                    250                  250
final eval episodes            64                   64
high decision/update rows      0 / 0                32,000 / 32,000
intrinsic reward fields nonzero none                 none
sparse evaluation reward exact true                 true
valid                           true                 true
```

M1 evidence:

```text
max arm cycle-success mean = 0.0                 required >= 0.05
paired indices with collection in either arm = 0 required >= 10
```

Arm summaries:

```text
constant_code_mappo:
  cycle_success_mean = 0.0
  episodes_with_collection = 0
  joint_position_coverage_mean = 0.015
  zero_cycle_fraction = 1.0

reward_pure_r30:
  cycle_success_mean = 0.0
  episodes_with_collection = 0
  joint_position_coverage_mean = 0.013625
  zero_cycle_fraction = 1.0
```

The paired descriptive differences were:

```text
cycle success:
  mean = 0.0
  95% CI = [0.0, 0.0]

joint-position coverage:
  mean = +0.001375
  95% CI = [+0.000550, +0.002200]

zero-cycle fraction:
  mean = 0.0
  95% CI = [0.0, 0.0]
```

Because M1 failed, the small positive coverage difference is descriptive only.
It cannot establish MAPPO noninferiority, exploration success, or a hierarchy
effect.

The result records final-evaluation collection access. It does not by itself
prove that no sparse reward was ever encountered during training unless the
underlying training evidence establishes that separately. Do not silently
strengthen the claim.

## Frozen interpretation boundary

If M0 is valid, the strongest supported statement is:

```text
shared neutral initialization
+ matched 320K low-policy optimization
+ one sparse Alice--Bob seed
-> neither constant-code recurrent MAPPO nor reward-pure R30 crossed the
   predeclared final-evaluation access floor
-/-> no valid noninferiority or inferiority comparison
-/-> no conclusion about the general value of hierarchy
-/-> no HMASD, S7, cooperation, or paper-efficacy conclusion
```

`NO_ACCESS` does not authorize:

- declaring recurrent MAPPO the replacement baseline;
- declaring R30 superior or inferior;
- treating identical zero cycle success as equivalence;
- using the coverage interval as a performance PASS;
- increasing the R35 seed count or budget;
- lowering the access threshold;
- restarting from the trained R30 checkpoint;
- reintroducing a skill objective to "fix" access.

The R29--R34 retirements and closure of the current skill-formation program
remain in force independently of R35.

## Required next research boundary

If R35 is valid, select exactly one R36 causal edge outside skill formation. It
should directly address the unresolved upstream bottleneck:

```text
one task-generic non-skill exploration or credit mechanism
-> materially higher probability of first sparse-task access
-> only after access, ordinary task optimization can be interpreted
```

You may refine this edge if needed, but the proposal must remain non-skill and
access-first. It must not merely compare constant MAPPO and R30 again.

The constant-code recurrent MAPPO stack may be used as an architecture-matched
control substrate, but R35 did not establish it as superior to or noninferior
to R30. State explicitly whether R30 becomes a frozen reference/diagnostic,
remains unresolved, or has another narrowly defined role.

If the proposed R36 mechanism uses an auxiliary objective or intrinsic signal,
it must be:

- task-generic and non-skill;
- independent of button, target, contact, phase, reward progress, human roles,
  communication fields, or an oracle assignment;
- mathematically separated from sparse external reward;
- specified with exact information inputs, gradient recipients, detach
  boundaries, update timing, normalization, and scale;
- structurally different from every retired skill-label/effect objective.

Do not disguise task shaping, a new latent codebook, options, subgoals,
trajectory labels, or roster semantics as a non-skill access mechanism.

## Retired and prohibited routes

Do not select or restore:

- R29 action-density/action-information reward or prior/window/scale variants;
- R31 CFEI, old-label posterior, or another classifier for numerical skills;
- R32 direct IFEPG as reward, advantage, value target, or wider-gradient form;
- R33 intervention-scored roster complementarity, pair scorer, team latent,
  `q_D`, or team reward;
- R34 clustering, hindsight mode labels, behavior distillation, or relabeling;
- OCSF, CBF, TMPF, or another discrete/continuous latent advertised as a skill;
- duration selection, hazard, queue, service priority, scheduler, atomic commit,
  or other IMOD execution mechanics as the learning contribution;
- task-distance/progress shaping, button/target/contact reward, communication
  intrinsic reward, or human role supervision;
- a trained-versus-frozen comparator;
- an R35 seed/budget/threshold rescue or automatic expansion.

Do not claim that these prohibitions prove all hierarchy or temporal
abstraction impossible. They close the tested skill-formation program only.

## Requested decision

1. Audit the R35 constant-code execution path, R30 execution path, shared
   zero-step initialization, low/high optimizer exposure, sparse reward path,
   stochastic paired evaluation, access calculation, bootstrap, and branch
   ordering.
2. Return either:
   - `VALID_NO_ACCESS_R35_UNRESOLVED`; or
   - `INVALID_R35_IMPLEMENTATION`, naming one concrete estimand-changing defect
     and the smallest repair. A zero-access outcome is not itself a defect.
3. If valid, state exactly what the result establishes and what it cannot
   establish. Explicitly reject performance and hierarchy comparison after M1.
4. Preserve the R29--R34 retirements and the closure of the current intrinsic
   skill-formation program. Do not rerun or expand R35.
5. Select exactly one non-skill, access-first R36 causal edge. Give one
   implementable algorithm, not a menu or family.
6. Specify its complete semantics:
   - mathematical objective/estimator;
   - actor and critic information;
   - recurrent-state and rollout flow;
   - gradients and detach boundaries;
   - reward decomposition;
   - updated and frozen modules;
   - interaction, if any, with the R30 fixed-clock controller.
7. Give the smallest mechanism-matched Alice--Bob abandonment gate:
   - one trained treatment and one trained matched control;
   - shared neutral initialization;
   - identical low architecture, environment steps, updates, optimizer
     exposure, seed, evaluation, and bootstrap protocol;
   - exact positive-access metrics and material thresholds;
   - secondary coverage/stability metrics that cannot override access;
   - M0 validity and mutually exclusive PASS, FAIL, INVALID, and crash branches;
   - one authorized next action per branch;
   - no `UNDERPOWERED`, tuning, threshold revision, or automatic seed/budget
     expansion.
8. State the narrow claim a PASS would support and the reusable negative
   conclusion a valid FAIL would establish. Do not claim task efficacy,
   cooperation, HMASD parity, S7 transfer, or a paper contribution from the
   Alice--Bob access gate.

Return one decisive route only.

## Repository files to inspect

- `docs/external-review/gpt5_6_pro/20260715_r34_bhmd_gate_result/RESPONSE_CORRECTION_3_RAW.md`
- `docs/external-review/gpt5_6_pro/20260715_r34_bhmd_gate_result/DISPOSITION_CORRECTION_3.md`
- `memory/LTM/R29_R33_EFFECT_COMPOSITION_FAILURE_REVIEW_20260714.md`
- `memory/ALGORITHM_PRINCIPLES.md`
- `memory/CURRENT_WORK.md`
- `memory/ExpRecord.md`
- `ha_ctse_process/config_alice_bob_sparse_mappo.py`
- `ha_ctse_process/config_alice_bob_asymmetric.py`
- `ha_ctse_process/standalone_agent.py`
- `ha_ctse_process/train.py`
- `ha_ctse_process/plotting.py`
- `envs/pettingzoo/alice_bob_asymmetric_cycles.py`
- `scripts/run_r35_sparse_mappo_reset_local.ps1`
- `scripts/analyze_r35_sparse_mappo_reset.py`
- `logs/r35_sparse_mappo_reset_320k_20260715_013000_retry4/result/r35_sparse_mappo_reset.json`

Read the implementation and result, then return one audited verdict, one
bounded causal conclusion, and one complete falsifiable non-skill R36
abandonment gate.
