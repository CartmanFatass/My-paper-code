# R30 Alice--Bob Result And Reward Boundary

## Historical Run Contract

- run: `r30_alice_bob_paired_64k_20260714_163908`
- implementation commit:
  `cbf504729ac4e14f8195bd0c7714e73f9e667474`
- arms: adaptive R30 `KEEP/SET` versus matched shared-`k` forced refresh
- seed: `30031`
- exposure: `64,000` environment transitions per arm, `16` environments,
  `50` PPO updates, CUDA
- fixed check clock: `k0=10`
- final evaluation: `40` deterministic episodes, `80` steps each
- machine status: `COMPLETE`, `implementation_valid=true`

This is one paired mechanism screen, not a multi-seed efficacy experiment,
S7 evidence, or HMASD parity result.

## Three Reward Objects That Must Not Be Conflated

### 1. Historical environment reward

The completed run used:

```text
r_env = collection_event + 0.20 * (Phi(s_next) - Phi(s))
```

`Phi` was the negative normalized minimum distance under the two role-free
assignments of agents to the active button and target. This is task-specific
environment reward shaping. It was shared by both agents and entered both low
and R30 high returns.

Consequently, describing the historical run as simply `reward-pure` was
imprecise. The correct label is:

```text
R30 controller reward-pure; Alice--Bob environment shaped
```

### 2. Sparse external reward at the review-target commit

The active environment now uses:

```text
r_task = 1
  only when different agents jointly occupy the active button and target
  for the first successful collection in the current short window;
r_task = 0 otherwise.
```

The former potential function and progress coefficient have been removed from
the active environment. The compatibility metric
`alice_bob_progress_reward` remains identically zero so evidence can show that
shaping was absent.

### 3. Current algorithmic intrinsic reward

For each low-level primitive transition, the transition discriminator predicts
the active individual skill:

```text
q_phi(z_i | o_i,t, a_i,t, delta_o_i,t, r_env,t)
```

The reward removes the stronger of a learned skill prior and a context-only
shortcut based on segment-start observation, agent identity, and clock phase:

```text
delta_i,t = log q_phi(z_i | transition)
            - max(log p_phi(z_i), log q_ctx(z_i | context))

r_sem_i,t = clip(0.02 * ReLU(delta_i,t), 0, 0.05)
```

The score is detached from the discriminator update and added only to the
primitive low-level PPO reward. R30 high `KEEP/SET` PPO receives environment
reward only. This signal encourages locally identifiable skill-conditioned
transitions; it is not a state-novelty, coverage, or task-discovery bonus.

## Result

Implementation and temporal-use evidence:

- exact PPO replay maximum log-probability error was below `5e-7` in both arms;
- adaptive full-synchronization SET rate was `0.168956`, versus `1.0` by
  construction in shared-`k`;
- adaptive produced `125` skill spells longer than `4*k0`, versus `0` in the
  shared control;
- adaptive switch-time skill entropy/minimum share were
  `0.997598 / 0.216007`.

Task evidence:

- both arms: `cycle_success_rate=0`, `targets_completed=0`,
  `target_contact=0`, and `joint_coordination=0`;
- adaptive/shared mean evaluation rewards were
  `-0.0254259 / -0.00333633` under the historical shaped environment;
- adaptive button occupancy was `0.04375`; shared was `0`.

Skill evidence:

- transition discriminator accuracy was adaptive/shared
  `0.356070 / 0.298407`;
- context accuracy was `0.261118 / 0.281550`;
- late residual-MI mean was `-0.007931 / -0.031478`;
- positive-residual fraction was `0.475391 / 0.396094`;
- mean applied intrinsic reward was approximately
  `0.000714 / 0.000458`.

Behavior-alignment evidence is too sparse for a strong conclusion: the late
behavior table has only four adaptive rows and one shared-control row. The
observed adaptive button `KEEP=0.75`, target `SET=0`, and cycle match `0` cannot
establish semantic alignment.

## Allowed Interpretation

- R30 fixed-clock edit/replay wiring passed this screen.
- Adaptive R30 used lifetime freedom and did not collapse to forced refresh.
- The current transition intrinsic was active but did not establish natural
  context-residual skill differentiation or cooperative behavior here.
- The current combination failed to access the task within this short screen.

## Prohibited Interpretation

- This was not a sparse-reward exploration experiment because its environment
  reward was shaped.
- Shaped progress cannot be attributed to the algorithmic intrinsic reward.
- Both arms used the same intrinsic reward, so their pair does not estimate the
  intrinsic reward's causal effect.
- Zero task success does not by itself prove R30, variable lifetime, or
  intrinsic exploration is ineffective.
- Skill entropy, classifier accuracy, or the few observed KEEP/SET rows do not
  prove persistent skill semantics.
- The result cannot be compared with original HMASD efficacy and does not
  authorize a longer run or seed expansion by itself.
