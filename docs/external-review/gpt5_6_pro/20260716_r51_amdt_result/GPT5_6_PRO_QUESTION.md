# GPT-5.6 Pro Review — R51-AMDT No-Access and the Next Variable-N Task

## Review boundary

Review the launch-exact `R51-AMDT-G0` result at the tracked repository
boundary. This is a result-validity and environment-design failure review.
Do not rescue R51 by changing its budget, PPO epochs, seed, model width,
thresholds, dynamics, horizon, reset distribution, or reward and rerunning it.

The scientific objective remains narrow:

```text
genuine N-scaled cooperative task dynamics
+ stable cross-episode N in {2,3,4,5,6}
+ one anonymous shared ordinary policy
+ task-native external reward
-> learnable behavior across team sizes
```

The project still forbids environment-specific intrinsic reward. No skill
latent, KEEP/SET, variable lifetime, S7, or UAV claim is active.

## Registered R51 result

The authoritative result is:

```text
status = NO_ACCESS_R51_AMDT_SPECIALISTS
implementation_valid = true
M0 = true
M1 specialist access = false
M2 shared variable-N = false and quarantined
```

Exact exposure and probability evidence:

```text
balanced cycles                         125
N-specific batches/arm                 625
transitions/arm                        320,000
transitions/N/arm                       64,000
agent-token decisions/arm            1,280,000
shared optimizer steps                  625
specialist optimizer steps/model        125
specialist aggregate steps              625
PPO epochs                                1
sample/replay max error                    0
prefix replay max error                    0
masked probability mass max                0
all M0 checks                           true
```

All five exact-final specialist success rates were zero:

| N | specialist final success | final-minus-zero CI | four block means |
| -: | -----------------------: | ------------------: | ---------------- |
| 2 | 0 | `[0,0,0]` | `[0,0,0,0]` |
| 3 | 0 | `[0,0,0]` | `[0,0,0,0]` |
| 4 | 0 | `[0,0,0]` | `[0,0,0,0]` |
| 5 | 0 | `[0,0,0]` | `[0,0,0,0]` |
| 6 | 0 | `[0,0,0]` | `[0,0,0,0]` |

The complete training CSV has 625 rows. Neither shared nor specialist arms
ever produced a nonzero terminal-success batch. Thus the on-policy buffer had
no positive external reward sample during the whole registered run.

Exact-final diagnostics provide localization but are not reward terms:

- specialist station-failure rate was `1.0` for every N;
- N=2 completed all jobs but still always lost its station;
- N=3 and N=4 completed no jobs and always missed their deadlines;
- N=5 and N=6 sometimes completed jobs, but still always failed a station;
- duplicate-assignment fractions were high (`0.50` to `0.71875`);
- shared numerical results are quarantined by M1 and may not support a
  cross-N conclusion.

## Controller interpretation to audit

The current interpretation is:

```text
valid implementation
+ zero successful specialist training episodes
+ zero specialist final success at every N
-> exact AMDT full-conjunction terminal reward has no ordinary-policy access
   under its frozen dynamics/horizon/reset contract
-> R51 cannot test shared variable-N learning
```

The likely carrier failure is the conjunction of persistent station survival
and all short-job completion: random/on-policy trajectories never reach the
only positive terminal outcome, so PPO receives no task-return carrier. This
is an inference, not a registered causal conclusion. Check whether any concrete
environment, observation, transition, recurrent replay, PPO-credit, or
evaluation defect instead invalidates the run. Name an exact defect if and
only if it changes the registered estimand or terminal branch.

## Repository files to inspect

Read these files completely before deciding:

1. `docs/external-review/gpt5_6_pro/20260716_r51_amdt_result/GPT5_6_PRO_QUESTION.md`
2. `docs/external-review/gpt5_6_pro/20260716_r51_amdt_result/R51_AMDT_RESULT.json`
3. `docs/external-review/gpt5_6_pro/20260716_r51_amdt_result/R51_AMDT_TRAIN_UPDATES.csv`
4. `ha_ctse_process/r51_amdt.py`
5. `scripts/run_r51_amdt_gate.py`
6. `scripts/run_r51_amdt_local.ps1`
7. `memory/ExpRecord.md`, especially `EXP-20260716-r51-amdt-g0`
8. `memory/ALGORITHM_PRINCIPLES.md`, especially the external-reward versus
   environment-agnostic intrinsic boundary
9. `docs/external-review/gpt5_6_pro/20260716_variable_team_toy_design/GPT5_6_PRO_RESPONSE_RAW.md`
10. `docs/external-review/gpt5_6_pro/20260716_variable_team_toy_design/GPT5_6_PRO_LAUNCH_CLARIFICATION_RESPONSE_RAW.md`
11. `docs/external-review/gpt5_6_pro/20260716_variable_team_toy_design/FINAL_DISPOSITION.md`

## Requested decision

Return one explicit validity verdict:

```text
CONFIRM_NO_ACCESS_R51_AMDT_SPECIALISTS
INVALID_R51_AMDT_WIRING_<exact defect>
```

If the result is valid, accept the registered retirement of the exact R51
environment contract. Then select exactly one new falsifiable route, tentatively
named `R52`, for a genuinely task-dynamic variable-N toy that satisfies all of
the following:

1. task workload and cooperative resource constraints genuinely scale with N;
2. N is stable within an episode and varies across episodes;
3. agents are anonymous and use the same small N-independent set/pointer policy;
4. local specialists can receive a task-native learning carrier without
   intermediate shaping or environment-specific intrinsic reward;
5. the external task reward may be sparse in time, but its exact semantics must
   be defended as the task objective rather than a handcrafted algorithm aid;
6. a fixed-N specialist ordinary-access prerequisite isolates environment
   no-access before shared-variable-N interpretation;
7. the task remains small enough for one local 16-env CUDA gate;
8. no Alice-and-Bob replication, one-step synthetic bandit, skill, KEEP/SET,
   variable lifetime, membership change, S7, or UAV transfer is introduced.

Specify one launch-exact minimum gate: environment transitions, observation,
centralized state, action semantics, external reward, model (or justified reuse
of the R51 model), PPO credit, paired comparator, seeds, budgets, exact
optimizer exposure, evaluation, M0 validity checks, specialist access M1,
shared cross-N M2, mutually exclusive terminal branches, and no-rescue rules.

The central design question is whether a terminal-only graded task objective
(for example, normalized fulfilled workload subject to a nontrivial
cooperation constraint) is the correct task-native carrier, or whether a
different Markov game is needed. Decide one; do not offer parallel routes or a
parameter sweep.

Also state the strongest objection to the selected route and whether it changes
your recommendation.
