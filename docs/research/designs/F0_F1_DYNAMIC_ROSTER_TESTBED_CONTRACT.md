# F0/F1 Dynamic-Roster Testbed Contract

Status: `FROZEN_DESIGN_ONLY`

Accepted: 2026-07-17

Review verdict: `MODIFY_TESTBED_CONTRACT`

Evidence source:
`docs/external-review/rounds/20260717_f0_f1_dynamic_testbed_design/`

This document freezes a falsifiable testbed contract for deciding whether
applied-prefix conditioning adds value beyond an architecture-matched ordinary
dynamic-roster baseline. It authorizes neither implementation nor training.

## 1. Causal Objective

The final target is one shared skill-based algorithm that supports both
runtime-variable team membership and variable realized skill lifetime. This
testbed isolates one possible additional capability:

```text
natural earlier commitment
-> later common-support relative distribution
-> better roster composition
-> higher terminal external utility
```

The live hypotheses are:

- **H0 / F0 sufficiency:** active-set recurrence, exogenous opportunities,
  persistent skills and duration-correct credit are sufficient; applied-prefix
  coupling adds no task value.
- **H1 / F1 applied-prefix value:** later commitments must condition on earlier
  applied commitments to form useful team compositions.
- **H2 / skill execution failure:** a direct primitive policy can learn the
  task, but the skill-conditioned low actor cannot form and naturally use
  persistent and reactive primitives.
- **H3 / exogenous timing limitation:** skills and prefix coupling work, but
  fixed exogenous opportunities arrive too late. H3 is diagnostic only and
  does not authorize learned event timing.

## 2. Launch-Exact Environment

### 2.1 Episode Order

The horizon is `H=80`, with primitive times `t=0,...,79`. There is no early
termination or time-limit truncation. At every primitive time:

1. complete the previous primitive transition when `t>0`;
2. apply the external membership transaction at `t`;
3. create any short wave arriving at `t`;
4. form actor observations and centralized critic state;
5. process the due event frontier for F0/F1, or the full active primitive
   frontier for the direct arm;
6. execute one primitive action for every active lifecycle;
7. update persistent and short-duty state;
8. at `t=79`, pay the only external reward and terminate.

### 2.2 Membership Ledger

Routing keys identify simulator lifecycles but never enter a network.

| Time | Transaction | Active count and continuity |
| ---: | --- | --- |
| 0 | Four genuine joins | `N=4`; zero recurrent states, undefined skills, immediate opportunity, initial high action must be `SET(z)` |
| 20 | Uniformly select two of the initial four for temporary leave | `N=2`; hidden state, skill, age and remaining opportunity gap freeze |
| 40 | Those two rejoin and two new lifecycles join | `N=6`; all four arriving lifecycles receive an immediate opportunity |
| 60 | Uniformly select two active lifecycles for terminal leave | `N=4`; a removed persistent owner is cleared before action |

Completed team work never rolls back. A terminally removed lifecycle produces
no later actor rows. Direct, F0 and F1 share this boundary exactly.

### 2.3 Primitive Actions and Skills

Every active member has the same action support:

```text
0 = IDLE
1 = PERSIST
2 = SHORT
```

There are no environment-side action masks, hard roles or identity-specific
supports. F0/F1 use `K=3` latent skills and preserve
`pi_l(a_i | o_i, z_i)`. The direct arm has no skills or event controller.

### 2.4 Persistent Duty

State consists of `persistent_owner` and `persistent_units in [0,64]`.

- If the active owner executes `PERSIST`, add one unit, capped at 64.
- If no owner exists or the owner does not execute `PERSIST`, uniformly choose
  a new owner among active members executing `PERSIST`; a handoff step yields
  no unit.
- Extra non-owner `PERSIST` actions yield no work.
- Temporary or terminal leave immediately clears an owner.

The terminal persistent score is

```text
P = min(persistent_units / 64, 1).
```

This makes one long-lived commitment useful while making duplicate persistent
assignments naturally wasteful, without an auxiliary penalty.

### 2.5 Generic Short Duty

There are eight waves. At reset, the task RNG independently chooses one arrival
from each candidate set:

```text
{0}, {9,10}, {24,25}, {32,33}, {40}, {49,50}, {64,65}, {72,73}
```

Future arrivals are hidden. A wave is created after the membership transaction.
For a wave arriving with `N_w` active lifecycles, required work is
`R_w=N_w-1`; it remains active for four primitive steps.

For each lifecycle and current wave, store a `short_streak` in `{0,1,2}` and a
binary `contributed` flag.

- An active, not-yet-contributing member executing `SHORT` increments its
  streak.
- `IDLE` or `PERSIST` resets the streak.
- Reaching streak two creates one work unit and marks that lifecycle as having
  contributed once to the wave.
- Leave or wave expiry clears the streak; unfinished work expires permanently.

The score is

```text
S = total_completed_short_work / total_required_short_work.
```

Under the frozen roster schedule, the denominator is
`3+3+1+1+5+5+3+3 = 24`. The optimal anonymous composition is one persistent
owner plus `N_t-1` short workers.

### 2.6 Reward

The shared external reward is terminal only:

```text
r_t = 0                    for t < 79
r_79 = U = 0.5 * (P + S)
```

`P`, `S`, owner handoffs, wave progress and completed work are diagnostics, not
intermediate rewards, intrinsic rewards, potential terms or bonuses. Intrinsic
reward remains environment-agnostic and may not consume any task field.

### 2.7 Anonymous Observation

Each active lifecycle receives the following 15-dimensional primitive
observation:

| Index | Field | Normalization |
| ---: | --- | --- |
| 0 | primitive time | `t/80` |
| 1 | active count | `log(1+N_t)/log(7)` |
| 2 | persistent units | `units/64` |
| 3 | owner exists | binary |
| 4 | wave active | binary |
| 5 | wave steps remaining | `remaining/4` |
| 6 | wave work remaining | `remaining_work/max(R_w,1)` |
| 7 | arrived-wave completion fraction | completed/required-arrived; zero when none |
| 8 | self is persistent owner | binary |
| 9 | self short streak | `streak/2` |
| 10 | self contributed to current wave | binary |
| 11 | cumulative active execution time | `active_steps/80` |
| 12--14 | previous primitive action | three-way one-hot |

Temporary leave freezes previous action and cumulative active time; rejoin
restores them. Genuine join initializes previous action as `IDLE`. Fields 0--7
are common within the active set.

Forbidden actor inputs include lifecycle key, epoch, member index, future
membership or wave schedule, tie-break outcome, assigned role, future
opportunity, reward, return and success labels.

The event high token remains
`[o_i, emb(z_i), log(1+tau_i), join, rejoin]`. The low actor receives only the
15-dimensional observation and its skill.

### 2.8 Centralized Critic

Each active-member critic token uses the same 15-dimensional observation. F0
and F1 may additionally use current skill, skill age, join/rejoin flag, owner
high hidden state and boundary kind from the existing runtime. The global
critic vector is the eight common observation fields.

The critic may not read future ledgers, routing keys, epochs, future waves,
sampled action/order or external return.

### 2.9 Independent RNG Ledgers

Master seeds are frozen:

```text
direct model initialization   57056
paired F0/F1 initialization  57057
training task ledger         67057
event opportunity/order      77057
policy action sampling       87057
evaluation ledger            97057
bootstrap                   107057
```

Episode `e`, stream `s` uses
`PCG64(SeedSequence([master,e,s]))`.

Task-ledger streams:

```text
0  t=20 temporary-leave selection
1  t=60 terminal-leave selection
2  wave-arrival choices
3  persistent-owner tie breaks
4  active presentation permutations
5  direct primitive-frontier orders
```

Event-ledger streams:

```text
0  per-member opportunity gaps
1  F0/F1 frontier permutations
```

Training uses ledger IDs `0..3999`. Evaluation uses IDs `0..255` under the
independent evaluation master. F0/F1 share corresponding external ledgers and
action-uniform streams. Treatment-induced trajectory divergence is part of the
causal effect and is not repaired away.

## 3. Evidence Order and Frozen Exposure

The three stages are one serialized causal chain, not independent toy routes.

### Stage A: No-Learning Carrier

Use all 256 evaluation ledgers and perform no optimization.

The constructive routing-only controller maintains an owner, assigns all
eligible non-owners to active short work and otherwise idles. It must satisfy:

```text
mean(P) >= 0.95
mean(S) >= 0.95
mean(U) >= 0.95
```

Uniform independent primitive actions must satisfy:

```text
Pr(U > 0) >= 0.20
mean(U) < 0.55
```

Failure retires this exact testbed without any learning run.

### Stage B: Direct Primitive-AR Access

The direct instrument is a shared per-lifecycle recurrent actor with active-only
sum/count context, centralized active-set critic, a uniformly sampled recorded
frontier order each primitive step and earlier-action counts available to later
tokens. It contains no skill, `KEEP/SET`, event opportunity or high policy.

Frozen training contract:

```text
num_envs                 16
horizon / rollout        80 / 80
outer updates            250
environment transitions  320,000
PPO passes per update    4
optimizer steps          1,000
optimizer                Adam
learning rate            3e-4
gamma / GAE lambda       0.99 / 0.95
policy / value clip      0.20 / 0.20
value coefficient        0.50
entropy coefficient      0.01
global gradient clip     0.50
max recurrent chunk      20
advantage normalization  per collected update
```

Each PPO pass consumes the full valid recurrent batch from that update; there
is no replay across updates and no extra minibatch split. Evaluate exact update
0 and update 250 with 256 deterministic and 256 stochastic episodes on matched
evaluation ledgers; never select a best checkpoint.

Direct access requires all of:

```text
mean(U_direct_final_det)   >= 0.70
mean(P_direct_final_det)   >= 0.65
mean(S_direct_final_det)   >= 0.65
mean(U_direct_final_stoch) >= 0.60
LCB95(mean(U_final_det - U_zero_det)) > 0.15
```

The confidence bound uses 10,000 paired-episode bootstrap resamples. Failure
retires the testbed and prohibits Stage C.

### Stage C: Paired F0/F1

Only after direct access passes, run each arm with:

```text
num_envs                 16
horizon / rollout        80 / 80
outer updates            250
environment transitions  320,000
PPO passes per update    4
high optimizer steps     1,000
low optimizer steps      1,000
latent skills            3
```

All other PPO settings equal Stage B. The high optimizer covers commitment
policy and event critic; the low optimizer covers low actor and low critic.
F0/F1 have byte-equal initialization, identical state keys, ledgers, event
opportunities, orders, batches, optimizer counts and zero/final evaluation.
Only the selector differs:

```text
F0 -> initial commitment summary
F1 -> applied working commitment summary
```

Evaluate both arms at zero and final with 256 deterministic and 256 stochastic
episodes. Paired F0/F1 contrasts use 10,000 episode-paired bootstrap resamples
with seed `107057`.

## 4. Attribution Reads

### 4.1 Forced-Skill Execution Audit

At each final checkpoint, select 128 natural non-`t=0` snapshots balanced by
roster phase. For each snapshot and each of three skills, force only the focal
skill for 12 primitive steps with two independent action replicas. Forced data
is audit-only and cannot train a scorer or policy.

For each skill, use process signature
`[PERSIST occupancy, SHORT occupancy, delta persistent units / 12,
delta short work / max(R_w,1)]`. Let `B` be median between-skill distance,
`W` median within-skill cross-replica distance and `rho=B/(W+1e-8)`.

An arm has executable naturally used skills only if:

```text
LCB95(rho) > 1
persistent-like skill != reactive-like skill
both corresponding action-occupancy margins > 0.15
each skill occupies >= 10% of natural active primitive steps
```

### 4.2 F0 Task Sufficiency

F0 task access requires:

```text
mean(U_F0_final_det) >= 0.60
mean(P_F0_final_det) >= 0.55
mean(S_F0_final_det) >= 0.55
LCB95(mean(U_F0_final_det - U_F0_zero_det)) > 0.10
```

### 4.3 H1 Natural Applied-Prefix Evidence

Use only natural on-policy F1 event rows with `t>0`, frontier size at least two
and token position after the first. Working-prefix and initial-prefix reads
must have identical legal support, observation, incumbent, pre-hidden state,
critic source and parameters. Do not resample actions; exclude forced,
synthetic and episode-start all-join rows.

For the later token, compare `p_work` against `p_init` on their common support.
H1 requires all of:

```text
eligible natural rows >= 1,024
LCB95(mean(TV(p_work, p_init))) > 0.02
max F0 TV <= 1e-6
LCB95(mean(directional_composition_shift)) > 0.02
LCB95(mean(U_F1_det - U_F0_det)) > 0.03
mean(U_F1_final_det) >= 0.60
mean(P_F1_final_det) >= 0.55
mean(S_F1_final_det) >= 0.55
F1 executable-skill read = true
```

The directional shift increases persistent-like commitment probability when
the applied roster has none and decreases duplicate probability once it has at
least one. Prefix gradients, synthetic controls or TV alone do not support H1.

### 4.4 Conditional Timing Read

Read H3 only when direct access, F1 skills, natural prefix TV and directional
composition pass, but the F1-minus-F0 utility gain fails. A short wave is
timing-feasible at arrival when at least `R_w` active members already carry the
reactive-like skill or have a recorded opportunity by `t_w+2`. Also record
steps to restore a persistent-like commitment after owner loss.

Conditional H3 support requires:

```text
>= 25% of uncompleted work is timing-infeasible
LCB95(feasible-wave completion - infeasible-wave completion) > 0
```

This result cannot authorize learned timing.

## 5. Correctness Boundary

Before interpreting a scientific branch, M0 must establish the exact frozen
state machine and ledger counts, absence of identity/future/reward leakage,
active-only support, finite updates, exact exposure and optimizer counts,
sampling/replay probability agreement, strict schema-3 save/resume, matched
F0/F1 initialization and parameter graph, and selector-only reduction. F0's
common-support TV must be at most `1e-6`. Any concrete M0 defect produces
`INVALID_IMPLEMENTATION`; only that defect may be repaired without changing
the contract.

## 6. Mutually Exclusive Outcomes

Interpret outcomes in this priority order:

| Branch | Trigger | Disposition |
| --- | --- | --- |
| `INVALID_IMPLEMENTATION` | Any environment, ledger, replay, resume or F0-reduction M0 failure | Fix only the concrete defect; no scientific update |
| `RETIRE_TESTBED_CARRIER` | Stage A fails | Permanently retire this exact testbed |
| `RETIRE_TESTBED_NO_DIRECT_ACCESS` | Stage B fails | Permanently retire this exact testbed; H0--H3 unidentified |
| `SUPPORT_H1_ON_TESTBED` | Skills, natural TV, direction and F1 task gain all pass | H1 rises; stop for a separate integration decision |
| `SUPPORT_H0_STOP_AT_F0` | F0 task sufficiency passes but full H1 does not | H0 rises; retire H1 and stop at F0 |
| `SUPPORT_H2_SKILL_LIMIT` | Direct passes; both task arms and both skill-execution reads fail | Record skill bottleneck and stop without adding a module |
| `CONDITIONAL_H3_TIMING_LIMIT` | Skills and prefix direction pass, task gain fails, timing split passes | Record conditional timing limit; one cross-round interpretation only |
| `VALID_MIXED_UNCATEGORIZED` | Valid result fits no branch above | Stop without forced attribution or a successor toy |

All continuous reads remain reportable once Stage C runs, but downstream
descriptions cannot override an upstream failed prerequisite.

## 7. F0/F1 Isolation and Ordinary-MARL Objection

F0/F1 must share the environment, membership and task ledgers, opportunity
gaps, frontier order, active presentation, lifecycle store, network graph,
parameter count and initialization, critic, low actor, supports and masks,
optimizers, value normalization, event return/GAE, checkpoint schema and
exposure. They share the same data-generation contract, not necessarily the
same realized trajectories.

H1 evidence cannot come from episode-start symmetry, synthetic parameters,
forced trajectories, support-mask changes, common-logit shifts, post-sampling
repair or routing identity.

F0 already includes dynamic membership, survivor continuity, per-member
opportunities, variable realized lifetime, skill-conditioned recurrent low
control, active-set critic, exact event probabilities and duration-aware
credit. Therefore F1 cannot claim variable `N`, asynchronous lifetime, ragged
replay, resume, skill persistence or active-set representation as its
contribution. Its sole possible new contribution is useful natural
applied-prefix coupling that transports to external utility.

## 8. Replacement and Stop Ledger

Retain the schema-3 event runtime, typed membership transactions,
survivor/rejoin continuity, active-only sum/count reference, uniform external
event order, exact selector, duration-correct event credit, existing low actor,
task-blind intrinsic boundary and terminal task objective.

Delete or keep retired the exact R51--R54 contracts, R55 route and unexecuted
substrate, `SHORT_A/SHORT_B`, fixed-`N` specialists as a universal prerequisite,
identity/hard roles, graph/attention/slots/critical residuals, team latent or
new discriminator, learned ordering, learned event time and all task-specific
intrinsic or shaping.

No failure automatically creates another toy, module or rescue. H1 success is
testbed evidence only and still requires a separate integration disposition.

## 9. Authorization Boundary

This design migration is authorized and complete. The following remain
explicitly unauthorized:

- environment or adapter implementation;
- direct primitive-AR implementation;
- event-mode training integration;
- any experiment launch;
- F1 promotion or UAV integration.

A future controller must obtain a separate authorization before adding code or
executing any stage of this contract.
