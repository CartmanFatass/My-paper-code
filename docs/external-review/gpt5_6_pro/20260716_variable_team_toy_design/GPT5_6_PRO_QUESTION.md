# GPT-5.6 Pro Design Review — Genuine Variable-Team Toy Environment

Date: 2026-07-16

## Review mode

Read-only algorithm and experiment design. Do not modify the repository or run
experiments. Select one coherent design; do not offer parallel environment or
algorithm tracks.

## Decision needed

Design the smallest genuinely task-dynamic variable-team toy environment and
its first evidence-bearing learning gate for HMASD / HA-CTSE. The immediate
question is not whether a neural set encoder can accept different tensor
lengths. It is:

```text
one shared anonymous-agent policy
+ task dynamics and cooperation that truly change with active team size N
+ ordinary sparse external task reward
-> learns useful cooperative behavior across N
```

The resulting toy must also be suitable for a later, separate causal test of
variable skill duration. It must therefore contain at least two naturally
different task time scales, without assigning named roles to agents or encoding
the desired skill semantics in reward.

## Project background

### HMASD

The original HMASD path uses a fixed team size and synchronously samples a
complete autoregressive skill roster every fixed `k`. Its individual and team
discriminator terms `q_d/q_D` are environment-agnostic skill objectives, not
task-specific reward shaping. The exact source Alice-and-Bob task is a
two-agent 10x10 grid: two keys must be occupied while their corresponding goals
are reached, actions are five discrete moves, the horizon is 100, and only
completion gives shared reward `1`. The source reproduction R41B passed at
final win/key0/key1 `0.89/0.97/0.92`, but this is positive fixed-`N=2`
evidence only.

### HA-CTSE target

The UAV motivation requires both:

1. variable active team membership; and
2. variable per-agent skill lifetime.

The intended long-term control contract is a fixed global check clock,
set-equivariant active-roster representation, active-only autoregressive
KEEP/SET decisions, and membership transitions separated from the skill
renewal of surviving agents. A joiner receives initial SET; a leaver terminates
its membership segment by censoring; surviving agents keep their recurrent,
skill, age, and segment state. Learned admission or learned agent ordering is
not part of the first route.

The staged membership order remains:

```text
cross-episode variable N with stable membership
-> within-episode exogenous join/leave and censoring
-> variable skill lifetime comparison on the same dynamic-roster task
```

You may modify this order only by identifying a concrete causal confound that
cannot be removed within it.

### OPT boundary

OPT-style continuous interaction representation may later provide generic
context, but it cannot define task roles, task progress, team-size reward, or
the intrinsic objective. This review should not introduce a new OPT module.

## Evidence boundary

### R39 fixed-N toy credit failure

The earlier `two_timescale_role_free_actions` toy established factorization
capacity and directionally aligned returns, but the frozen native HMASD
GAE/PPO learner failed its registered fixed-N joint-roster gate. That exact toy
and learner route are retired without rescue.

### R49 architecture result

`PASS_R49_ORSE_ARCHITECTURE` established only that an N-independent Deep-Sets
policy can support active sizes `{1,2,3,4,6,8,12,16}`, simultaneous permutation
equivariance, dummy-padding invariance, incremental/full roster equivalence,
stored-prefix replay, active-only decoding, joiner SET, leaver censoring, and
survivor continuity. It used zero environment steps, reward reads, and
optimizer steps. It is an interface result, not learning evidence.

### R50 synthetic-bandit no-access result

R50 was not Alice-and-Bob and not an environment. It used a one-step synthetic
roster bandit whose four opaque target codes were quadrants relative to the
active-set feature mean. `N` changed only set statistics and autoregressive
sequence length.

The formal run was implementation-valid with 229,376 training cases per arm,
1,671,168 token decisions, 512 shared optimizer steps, 3,584 aggregate
specialist steps, and zero replay error. Fixed-N specialists passed macro/min
token and macro exact gates but missed N=16 exact-roster access
`0.26953 < 0.30`; the registered result is therefore
`NO_ACCESS_R50_SPECIALIST_SUBSTRATE`. The shared arm numerically passed all M2
thresholds (`0.95010` macro token accuracy, `0.71094` macro exact success,
`0.44336` N=16 exact success), but those reads are quarantined by the failed
specialist prerequisite. R50 cannot be rescued or interpreted as variable-N
task learning.

## User requirements

The new design must satisfy all of these:

1. **N must change the task, not only the tensor.** Workload, feasible
   coordination, allocation, or interaction dynamics must change with the
   active team size. Adding idle agents, duplicating the same two-person task,
   padding slots, or changing the number of classification tokens is
   insufficient.
2. **Two natural time scales.** The same task must create persistent and
   short-lived responsibilities so that a later variable-lifetime algorithm
   has a falsifiable reason to prefer long and short skills. The first
   variable-N gate may keep `k` fixed; it must not claim a lifetime result.
3. **Role-free homogeneous agents.** Any active agent can perform any task.
   No agent ID, slot embedding, Alice/Bob identity, fixed role label, or
   identity-specific skill block may enter the actor. A centralized critic may
   read the active global state.
4. **Sparse native external reward.** Training may use shared task completion
   reward defined by the environment. It may not use distance/progress
   potentials, role rewards, task-stage bonuses, team-size reward, join reward,
   survival reward, KEEP reward, or membership reward. Subtask events may be
   logged as diagnostics but not added to policy return.
5. **Environment-agnostic intrinsic only.** The first ordinary-policy access
   read should use no intrinsic reward. A later HMASD arm may preserve the
   original environment-agnostic `q_d/q_D` objective unchanged; no task field,
   goal identity, contact, phase, success predicate, distance, external reward,
   `N`, join, or leave event may be converted into intrinsic reward.
6. **Fast local iteration.** Use a small network and parallel local toy
   execution, preferably 16 environments and no more than 320K transitions per
   arm for the first gate. If that cannot yield a defensible access floor,
   change the task geometry/horizon before proposing a larger budget; do not
   hide no-access with reward shaping.
7. **One evidence-bearing gate.** Do not create another architecture-only or
   thirty-check workstream. The first controlled run must include the minimum
   implementation validity needed to trust the result and must directly test
   task-level variable-N learning.
8. **Matched exposure and within-N interpretation.** Report environment
   transitions and optimizer updates. Do not infer improvement by comparing
   raw reward at different N values. Treatment/control comparisons and safety
   reads must be made within each N, then aggregated by a declared weighting.
9. **No environment tailored to the desired answer.** The task should expose
   a generic scalable cooperation problem, not reward the exact HA-CTSE
   mechanism or hard-code its intended skill meanings.
10. **Toy first.** Do not send the next experiment to S7/UAV. S7 remains a
    later transfer target after this local toy gate works.
11. **Bounded variable-N computation.** The controller must not enumerate the
    `K^N` joint roster or introduce a mandatory dense `N x N` interaction
    tensor. State the sampling, replay, memory, and update complexity in N and
    K; prefer active-only autoregressive `O(NK)` behavior with pooled or other
    justified set statistics.

## Non-binding candidate family

A scalable anonymous multi-key/multi-goal grid derived from the source
Alice-and-Bob logic is one candidate, not a decision. For example, an active
key or station may require persistent occupancy while short-lived goals/jobs
appear elsewhere; the amount or arrangement of work changes with N, and any
agent may occupy or collect. This could expose long and short natural duties
without named roles.

Audit this candidate aggressively. Reject or modify it if it merely decomposes
into independent two-agent copies, gives surplus agents no meaningful effect,
leaks role semantics, makes larger teams trivially easier, or cannot support a
clean within-N comparator. You may select another task family, but output only
one final environment.

## Repository files to inspect

Read all of these before deciding:

1. `memory/CURRENT_WORK.md`
2. `memory/ALGORITHM_PRINCIPLES.md`, especially the baseline hierarchy,
   promotion ladder, intrinsic-reward boundary, and skill-before-async rule
3. `memory/ExpRecord.md`, especially R39, R41B, R48, R49, and R50
4. `docs/research/decisions/R39_NATIVE_TOY_CREDIT_FAILURE_REVIEW_20260715.md`
5. `docs/research/decisions/R35_R40_SUBSTRATE_FAILURE_REVIEW_20260715.md`
6. `docs/external-review/gpt5_6_pro/20260715_open_roster_variable_team_review/DISPOSITION.md`
7. `docs/external-review/gpt5_6_pro/20260715_open_roster_variable_team_review/GPT5_6_PRO_FOLLOWUP_RESPONSE_RAW.md`
8. `envs/pettingzoo/continuous_alice_bob.py`
9. `envs/pettingzoo/alice_bob_asymmetric_cycles.py`
10. `ha_ctse_process/config_alice_bob_asymmetric.py`
11. `ha_ctse_process/r30_fixed_clock.py`
12. `scripts/r49_orse.py`
13. `scripts/run_r50_vnsl_gate.py`
14. `docs/external-review/gpt5_6_pro/20260716_variable_team_toy_design/r50_vnsl.json`

The tracked R50 JSON is copied from runtime root
`logs/r50_vnsl_20260716_195649/result/r50_vnsl.json`. The original HMASD source
archive is `ref/hmasd.tar`; the exact source Alice-and-Bob environment is
summarized above so archive extraction is not required for this decision.

## Requested decision

Return one verdict:

```text
ACCEPT_VARIABLE_TEAM_TOY_REQUIREMENTS
MODIFY_VARIABLE_TEAM_TOY_REQUIREMENTS
REJECT_VARIABLE_TEAM_TOY_ROUTE
```

Then provide exactly one coherent route and answer all of the following:

1. Select exactly one toy environment. State whether it is an Alice-and-Bob
   generalization or a different task, and explain why it is not merely N-way
   padding or replicated two-agent work.
2. Specify the complete Markov game: team-size distribution, map/entities,
   observation and centralized state, action space, transition rules, native
   external reward, termination, episode horizon, reset distribution, and
   computational scale.
3. Explain precisely how changing N changes optimal coordination and how the
   task contains persistent and short-lived natural responsibilities without
   assigning roles.
4. Define the first cross-episode variable-N learning gate. Select train and
   evaluation N values, one shared-policy treatment, one mechanism-matched
   comparator, model scale, environments, rollout, updates/transitions, seed,
   evaluation episodes, metrics, aggregation across N, thresholds, and
   expected wall clock. Prefer a single paired run under 320K transitions per
   arm.
5. Include an ordinary-policy access condition that distinguishes an
   inaccessible environment from a variable-N algorithm failure, but fold it
   into the same controlled run rather than creating a preliminary audit
   project.
6. State the probability, information, credit, recurrent-state, mask,
   membership, checkpoint, optimizer-exposure, and computational-complexity
   contracts. Explicitly say which contracts are exercised now and which are
   deferred to within-episode join/leave.
7. Define minimal implementation validity, PASS, environment-NO_ACCESS,
   shared-variable-N-FAIL, and INVALID branches. Give the only next action
   authorized by each branch and one abandonment condition that prevents
   budget/threshold/seed/model rescue.
8. State what a PASS would and would not establish. It must not establish
   variable skill lifetime, intrinsic-reward efficacy, UAV transfer, or paper
   novelty.
9. If the proposed sparse reward cannot support fast ordinary-policy access,
   solve that through task size, geometry, horizon, reset distribution, or a
   better generic task. Do not add shaping or an intrinsic signal.

## Prohibited routes

- R50 rerun, threshold change, extra updates/seeds, larger R50 model, or reinterpretation
- existing asymmetric-cycle Alice-and-Bob unchanged
- S7/UAV-first experiment
- environment-specific intrinsic reward or reward shaping
- task/role labels in the actor or skill objective
- fixed agent identity, learned agent order, or slot-specific policy blocks
- learned admission/membership in the first gate
- within-episode join/leave before cross-episode variable N works
- variable-lifetime efficacy claim in the first gate
- revival of retired R29--R48 mechanisms
- parallel environment proposals or open-ended hyperparameter sweeps
