# IC-SPL Hazard-SMDP Alternative

Status: alternative research track, not the current implemented core.

This note records a more aggressive successor to the current standalone
HA-CTSE process-core implementation. The current code in `ha_ctse_process/`
implements a discrete-lifetime process core:

```text
OPT compact c
-> compact-conditioned team code g
-> per-agent skill z and discrete duration bucket d
-> countdown-based variable segment
-> segment process reward
```

The alternative described here replaces duration buckets with a stochastic
termination process and treats skill lifetime as an emergent SMDP stopping time.

## Core Goal

Use OPT as a global interaction compressor and learn a latent-controlled
semi-Markov multi-agent process:

```text
observation/state
-> OPT compression
-> interaction latent c
-> coordination latent g
-> skill z
-> stochastic hazard termination
-> segment outcome feedback
```

This track is not HMASD plus modifications. HMASD remains only historical
motivation for periodic communication and hierarchical skill control.

## System Definition

Environment and local observations:

```text
s_t       = environment state
o_i,t     = local observation for agent i
c_t       = OPT(s_t, o_1:n,t)
```

Coordination latent:

```text
g_t ~ pi_g(g | c_t)
```

For the first hazard version, `g_t` should remain fixed for the segment that it
starts. Letting `g` vary inside a segment is a later ablation because it makes
the skill process non-stationary.

Per-agent skill:

```text
z_i,t0 ~ pi_z(z | o_i,t0, g_t0)
```

Primitive execution:

```text
a_i,t ~ pi_l(a | o_i,t, z_i)
```

The low-level actor still does not observe `c_t` or `g_t` in the core algorithm.
This preserves the skill bottleneck.

## Hazard Termination

Duration is not directly predicted as an action. A skill terminates according
to a learned Bernoulli hazard:

```text
beta_i,t = P(terminate_i at t | o_i,t, z_i, g_t0)
         = sigmoid(h_beta(o_i,t, z_i, g_t0))
```

The realized lifetime is a stopping time:

```text
T_i = inf { t > t0 : Bernoulli(beta_i,t) = 1 }
```

The induced process segment is:

```text
S_i = (o_i,t0:t1, a_i,t0:t1, r_i,t0:t1, z_i, g_t0)
```

The existing discrete lifetime set becomes a stabilizing baseline/control, not
the final temporal model.

## Process Reward

Do not revive the old HMASD single-step discriminator. The relevant object is
the segment distribution induced by `(z,g)`.

The theoretical target is a density ratio:

```text
R_process = log p_pi(S_i | z_i, g_i) - log p_ref(S_i | g_i)
```

Directly estimating this ratio is difficult because it includes environment
dynamics, low-level policy, and hazard termination. The recommended first
implementation is a variational MI surrogate:

```text
R_process ~= log q_phi(z_i | S_i, g_i) - log p(z_i | g_i)
```

This differs from HMASD's discriminator because `q_phi` consumes an entire
segment and is conditioned on coordination context. It asks whether the
executed skill changes the process distribution, not whether a single state can
reveal a label.

An outcome model can be kept to prevent task-irrelevant diversity:

```text
R_total_i =
    env_return_i
  + lambda_mi  * [log q_phi(z_i | S_i, g_i) - log p(z_i | g_i)]
  + lambda_out * log p_psi(y_i | S_i, z_i, g_i)
  - lambda_len * length_penalty
  - lambda_churn * termination_cost
```

The entropy term should not maximize `H(S | z,g)` unconditionally. The desired
pressure is:

```text
maximize I(z ; S | g) = H(S | g) - H(S | z,g)
```

Different skills should induce distinguishable process distributions, while the
same skill under the same coordination mode should remain coherent.

## Coordination Mixture

A single deterministic `g` can collapse. The alternative core treats
coordination as a discrete mixture of experts:

```text
g_t in {e_1, ..., e_K}
g_t ~ pi_g(g | c_t)
```

Collapse should be measured by intervention sensitivity, not only entropy:

```text
Delta_z(g_k, g_j) = KL(pi_z(. | o, g_k) || pi_z(. | o, g_j))
```

If `Delta_z` is near zero, `g` is being sampled but not used. A useful loss is:

```text
L_g_use = - I(g ; induced skill distribution)
```

Practical diagnostics:

- `g_usage_entropy`
- `g_mode_histogram`
- `g_to_skill_mutual_info`
- `pairwise_kl_pi_z_given_g`
- `segment_return_by_g`
- `segment_outcome_by_g`

## PPO/SMDP Training

For the first implementable hazard version, treat termination as a PPO action:

```text
log_pi_high =
    log pi_g(g | c)
  + sum_i log pi_z(z_i | o_i, g)
  + sum_{i,t in segment} log Bernoulli(term_i,t | beta_i,t)
```

This is simpler than option-critic termination gradients and matches the
current on-policy update boundary. Each segment's high-level sample is consumed
once by the policy version that generated it.

## Migration From Current Code

Stage 0: keep current discrete-lifetime core as the stable process baseline.

Stage 1: add coordination-mixture diagnostics to the current `g` path:

- `g_usage_entropy`
- `g_mode_histogram`
- `g_to_skill_mutual_info`
- pairwise intervention KL over `pi_z(. | g)`

Stage 2: upgrade the process posterior from:

```text
q(z | S)
```

to:

```text
q(z | S, g)
```

and use:

```text
log q(z | S,g) - log p(z | g)
```

Stage 3: introduce `HazardSkillPolicy` as a named variant, not a silent change
to the discrete-lifetime baseline.

Stage 4: replace duration countdown closure with hazard-closed segments:

- store per-step termination log-probabilities;
- close segment on sampled hazard termination, episode end, or rollout boundary;
- keep rollout-boundary handling on-policy;
- log termination rate and lifetime distribution.

Stage 5: only after the MI/outcome surrogate is stable, consider explicit
density-ratio process modeling.

## Falsification Metrics

This alternative should be rejected or revised if:

- `g` entropy is high but intervention KL is near zero;
- skill usage collapses to one `z`;
- hazard termination collapses to always terminate or never terminate;
- segment lengths become homogeneous despite stochastic hazard;
- process reward improves while Scenario 7 coverage/QoS/throughput do not;
- duration or termination timing alone predicts skill identity;
- update variance becomes worse than the discrete-lifetime baseline.

## Relation To Current Implementation

Current code already has:

- OPT-like compact encoder;
- discrete stochastic `g` bridge;
- low-level skill bottleneck;
- segment manager;
- segment encoder;
- process posterior-like `q(z | S)`;
- outcome prediction;
- on-policy rollout/update boundary.

Current code does not yet have:

- hazard termination;
- `q(z | S,g)`;
- explicit `p(z | g)` prior correction;
- mixture intervention-sensitivity loss;
- per-step termination log-prob PPO;
- checkpoint/eval comparison across hazard and duration variants.

Therefore this document should guide a future named variant such as
`ic_spl_hazard_smdp`, while `ha_ctse_process` remains the discrete-lifetime
process baseline until that variant is implemented and tested.
