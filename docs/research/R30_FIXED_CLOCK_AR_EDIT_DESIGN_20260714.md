# R30 Fixed-Clock Autoregressive Skill Editing

Date: 2026-07-14

Status: accepted after GPT-5.6 Pro `MODIFY R30`; implementation is the active
core boundary. The raw review and disposition are under
`docs/external-review/gpt5_6_pro/20260714_r30_algorithm_code_review/`.

## Causal Question

Can HA-CTSE remove discrete-duration search and short-segment update bias while
retaining per-agent asynchronous lifetimes and a complete autoregressive joint
high-level decision at every global check?

```text
fixed global check clock k0
-> all-agent autoregressive KEEP/SET decisions
-> lifetime learned as KEEP survival
-> no duration shortcut or short-segment sampling advantage
```

This is upstream of the post-R29 semantic-reward question. R30 changes the
temporal controller only; it does not add a new intrinsic reward.

R30 also removes the sampled team code from the joint high action. The existing
bridge is retained only as deterministic representation:

```text
g_bar(c) = sum_q softmax(code_logits(c))[q] * code_embedding[q]
```

There is no sampled `g`, bridge action log-probability, or bridge entropy in
R30. The pre-action high state contains the global state, joint observation,
OPT compact, deterministic bridge embedding, pre-check roster, primitive-step
ages, active mask, and normalized per-environment check countdown.

## Why The Current Core Is Structurally Misaligned

The current `SkillDurationPolicy` samples independent skill and duration heads,
adds their log-probabilities, and invokes the autoregressive loop only for
expired agents. High PPO is then trained from completed variable-length
segments.

Consequences:

1. A check usually contains policy tokens for only a sparse expired subset, so
   agents that keep acting are context rather than participants in that joint
   high-level decision.
2. Short durations produce more segment samples per environment step and hence
   more high-policy updates.
3. The effective per-agent choice is `K*D`, and duration can encode skill
   identity without differentiated closed-loop behavior.

The design below restores the useful MAT-style property: one complete ordered
joint action is factorized into per-agent conditional tokens. It does not claim
MAT's theorem, and it does not reduce the number of possible joint rosters from
`K**N`; it reduces the per-agent branch set and makes sampling/training linear
over the stored agent sequence. MAT's paper and official implementation support
the autoregressive-execution / teacher-forced-training pattern:

- https://arxiv.org/abs/2205.14953
- https://github.com/PKU-MARL/Multi-Agent-Transformer

## High-Level Action

At every `k0` primitive steps, all `N` agents emit one token in a stored order:

```text
E_i(z_i_prev) = {KEEP} union {SET(z): z != z_i_prev}
```

For an active agent and `K` skills this has exactly `K` effective choices. At an
initial assignment, `KEEP` is masked and `SET(z)` may select any of the `K`
skills. `SET(current_skill)` is always masked because it duplicates `KEEP` while
resetting age.

The policy is factorized into a keep head and a switch-skill head:

```text
P(KEEP)   = p_keep
P(SET(z)) = (1 - p_keep) * pi_z(z | SWITCH), z != current
```

Executed log-probability is therefore:

```text
KEEP:   log(p_keep)
SET(z): log(1 - p_keep) + log(pi_z(z | SWITCH))
```

Masks are applied before sampling and again under teacher-forced evaluation.
The stored old log-probability must correspond to the executed mask exactly.

## Autoregressive Working Roster

The sequence is over all agents, not only agents that switch. Start with the
pre-check roster and ages. After each token, immediately apply it to a working
roster:

```text
working_skills = active_skills_before_check
working_ages   = active_ages_before_check

for i in stored_agent_order:
    token_i = policy(context, working_skills, working_ages, prefix)
    if token_i is SET(z):
        working_skills[i] = z
        working_ages[i] = 0
    # KEEP leaves both entries unchanged at the decision instant
```

Later agents see earlier applied edits and the still-active skills of agents not
yet processed. This preserves complementary roster conditioning without making
actual skill changes synchronous: every agent decides at the same check, but a
`KEEP` agent continues its existing process.

The first implementation uses one canonical agent order and stores it with the
transition. Order randomization is not part of R30.

The integer pre-check roster, ages, active mask, order, and executed tokens are
the replay truth. Training rebuilds the working roster token by token; a cached
float prefix is not an authoritative action record.

## Fixed-Clock High PPO

Variable skill segments remain useful low-level process records, but they are
no longer high-policy samples. A separate high-check buffer owns the PPO data.

For high row `tau`:

```text
R_tau = sum_{r=0}^{L_tau-1} gamma**r * r_env[tau*k0+r]
Gamma_tau = gamma**L_tau
```

`L_tau=k0` normally and may be shorter at an episode terminal or PPO update
boundary. High GAE is computed along each environment's ordered high-row
sequence. The high critic predicts exactly one pre-action scalar
`V_H(x_tau, steps_to_check/k0)`. It is independent of the autoregressive prefix,
tokens, edit decisions, and process segments. One resulting row advantage
`A_tau` is shared by the `N` stored edit tokens on a real decision row.

Each environment owns `steps_to_check`; an interleaved collector index is never
the clock. Episode reset sets it to zero, performs the initial all-skill
assignment with `KEEP` invalid, then resets it to `k0`. Primitive steps
accumulate discounted raw scalar environment reward, increment active ages, and
decrement the clock.

At a PPO update boundary, the open row is closed with
`policy_truncated=True` and bootstrapped from the old high critic. The active
skills, ages, clock, environment state, and low recurrent state remain live.
The next rollout opens an actor-invalid critic-only continuation row until the
next real check. This continuation contributes reward and value learning but no
actor tokens or log-probabilities. Update truncation bootstraps the value target
while breaking the GAE trace:

```text
delta_tau = R_tau + Gamma_tau*(1-terminal_tau)*V_next - V_tau
A_tau = delta_tau + Gamma_tau*lambda*(1-terminal_tau)
        *(1-policy_truncated_tau)*A_next
```

Training uses the stored action sequence and prefixes as teacher forcing:

```text
rho_tau_i = exp(new_logp_tau_i - old_logp_tau_i)
L_policy  = mean_over_checks_and_agents(PPO_clip(rho_tau_i, A_tau))
```

The agent dimension is averaged, not summed, so changing `N` does not silently
multiply the gradient scale. This is a practical MAT-style PPO surrogate, not
the exact conditional-advantage construction required for a monotonic theorem.

Each executed token has one ratio. In particular, `SET(z)` uses the combined
log-probability `log(1-p_keep)+log pi_z(z|SWITCH)` and is clipped once; its keep
and skill factors are never clipped separately. Initial assignment has no keep
gradient because `KEEP` is invalid.

Required transition shapes are:

```text
state              [B, state_dim]
joint_obs          [B, N, obs_dim]
prev_skills        [B, N]
prev_active        [B, N]
prev_ages          [B, N]
steps_to_check     [B]
decision_mask      [B]
agent_order        [B, N]
token_kind         [B, N]
set_skill          [B, N]
token_valid        [B, N]
old_token_logp     [B, N]
old_value          [B]
old_next_value     [B]
block_reward       [B]
block_len          [B]
terminal           [B]
policy_truncated   [B]
```

The buffer is independent of `Segment`. `KEEP` leaves the active process
segment open; `SET` closes and opens it; episode terminal closes it. A PPO
update may cut process diagnostics for version hygiene, but segments never
produce high rewards, advantages, or policy samples.

The low-level actor remains exactly `pi_l(a_i | o_i, z_i)`; neither the edit
token nor the global context bypasses the skill bottleneck.

## Learning Long Lifetimes Without A Length Reward

Lifetime is the survival run of `KEEP` decisions. Long-horizon task benefit is
credited through check-sequence GAE rather than a duration label chosen at the
segment start.

R30 removes every competing structural bias:

- every agent supplies one high token per check, independent of lifetime;
- no duration head, duration candidate set, or duration entropy floor;
- no `KEEP/SWITCH` entropy bonus;
- no edit penalty, switch penalty, forced `H_max`, or positive lifetime reward;
- no sweep of the keep initialization.

The keep-head bias is derived once from the retired duration distribution:

```text
p_keep_init = 1 - 1 / mean(duration_blocks)
```

For the active `{1,2,3,4}`-block source, `p_keep_init=0.6`, preserving the old
initial mean of 2.5 blocks while allowing unbounded survival up to the episode
horizon. This makes long skills learnable when they improve delayed return; it
does not guarantee that every task should or will select long lifetimes.

## Preserving Skill Supply And Semantic Differentiation

The temporal decision and skill identity remain separate. Only the conditional
switch-skill distribution receives a skill-coverage entropy term:

```text
L_skill_entropy = -lambda_z * stopgrad(p_switch)
                  * H(pi_z(. | SWITCH, stopgrad(shared_features)))
```

For this regularizer only, detaching both the weight and the shared feature
input confines its gradient to the switch-skill branch. It therefore cannot pay
the keep head, directly or through the shared trunk, to switch more often. PPO
gradients from executed switch actions still train the complete shared path. The
entropy term supplies alternative skill labels when a switch is chosen but is
not itself evidence of behavioral semantics.

The HMASD-like semantic path remains:

```text
balanced switch-skill supply
-> skill-conditioned low-level bottleneck
-> fixed-window realized-effect differentiation
```

Any later semantic target must use a fixed `W=k0` window, be blind to duration,
age, agent ID, communication-specific fields, and task reward, and enter low
GAE only. It must not enter the high `KEEP/SET` return; otherwise longer
lifetimes could earn more intrinsic reward merely by surviving. The exact
effect target remains the separate post-R29 causal question and is not invented
inside R30.

## Implementation Boundary

One coherent implementation changes:

1. add an explicit `r30_fixed_clock_ar_edit` mode with
   `keep_head + switch_skill_head`; keep the duration controller only as a
   frozen comparator;
2. run all-agent autoregressive editing every `k0` steps using the applied
   working roster;
3. make the bridge deterministic expected context and add a prefix-independent
   scalar `HighCheckValue`;
4. add a fixed-check high buffer, per-environment countdown, continuation rows,
   and check-sequence GAE/PPO path;
5. decouple process-segment renewal from high sampling: `KEEP` continues the
   segment, `SET` closes/opens it, and update/episode boundaries still flush it;
6. retire duration entropy, duration penalties, and duration-dependent metrics
   from the active mode;
7. migrate compatible low actor/critic/ValueNorm, compact/OPT/bridge
   representation, shared high actor trunk, and compatible skill head through a
   versioned loader. Reinitialize the keep head, high critic, high ValueNorm,
   high optimizer, clocks, and buffers; never silently load them with
   `strict=False`.

Legacy duration code may remain loadable only as the frozen comparator. It is
not an active tuning branch.

## First Evidence-Bearing Run

After implementation, use one reward-pure, mechanism-matched short comparison
between the frozen discrete-duration controller and fixed-clock editing. Use
seed `30031`, 16 environments, CUDA, and approximately 320K environment
transitions per arm. Keep the low policy, source checkpoint, optimizer-update
exposure, and evaluation identical. Choose a rollout boundary that exercises a
non-check-aligned update continuation. The read needs only four facts:

1. exactly `N` high tokens are produced per real check, replay log-probability
   max error is at most `1e-5`, and continuation rows have zero actor tokens;
2. over late eligible skill spells,
   `min(P(T>4*k0), P(T<=4*k0)) >= 0.05`;
3. full-synchronous `SET` rate is at most `0.50`, conditional switch-skill
   entropy divided by `log(K)` is at least `0.80`, and every skill's switch
   share is at least `0.05`;
4. relative task-reward degradation is at most `0.10` and absolute worsening
   in zero-service-step fraction is at most `0.10`.

No semantic reward, team mechanism, duration sweep, or long-run claim is mixed
into this gate.
