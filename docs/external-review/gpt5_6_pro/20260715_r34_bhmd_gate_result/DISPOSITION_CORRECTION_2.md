# Controller disposition: TMPF has no skill-formation gradient

Date: 2026-07-15

Source model: GPT-5.6 Pro. The raw response is
`RESPONSE_CORRECTION_2_RAW.md`.

## Decision

- Retraction of R35-CBF as direct IFEPG: **ACCEPT**.
- Replacing the historical K=4 object rather than renaming its slots: **ACCEPT
  AS A STRUCTURAL HYPOTHESIS**.
- R35-TMPF as specified: **REJECT / INVALID ALGORITHM CONTRACT**. It cannot be
  implemented or launched without inventing a missing training mechanism.

## Decisive gradient defect

The proposed formation loss is only a world-model likelihood:

```text
L_wm(theta) = -log p_theta(o[t+1:t+W] | o[t:t+W-1], a[t:t+W-1], u)
```

Collected observations, actions, and sampled `u` are data. With the required
detach from the environment trajectory:

```text
grad_actor L_wm = 0
grad_u_policy L_wm = 0
```

The response simultaneously says that the world model does not update the
policy, that the only policy objective is sparse environment-reward PPO, and
that `actor_film(u)` is updated by formation. Those statements cannot all hold.
No objective or gradient is given for the mentioned `latent encoder e_phi(o)`,
and it is not connected to the random-walk `u` definition.

Backpropagating through stored action inputs would not repair this contract: it
would require an explicit model-based actor objective, behavior-policy and
model-bias treatment, and a differentiable definition of what the actor is
optimizing. It would also contradict the response's claim that policy gradient
comes only from environment PPO.

## Controller and gate defects

- A frozen discrete R30 `SET(z)` head cannot emit a continuous `u`. Randomly
  keeping, perturbing, or resampling `u` is an external scheduler, not the
  frozen high controller or learned temporal abstraction.
- The adaptive-R30 discrete checkpoint cannot initialize a different
  continuous-FiLM input without an explicit migration and a capacity-matched
  inactive continuous adapter.
- Original discrete R30 is neither a capacity-matched control nor an unchanged
  source anchor for the larger continuous policy.
- The proposal gives no policy-training exposure beyond 32 source episodes,
  even though M3 assumes reward-PPO learning. Its on-policy steps, optimizer
  calls, and per-arm version boundaries are absent.
- Continuous-latent sampling distribution, scale, pair distance, interpolation
  metric, `Var(tau(u+delta))`, bootstrap unit, CIs, and material source-relative
  gates are undefined. Arbitrary latent scale can manufacture B/W separation.
- A world model can ignore `u` because actions already explain transitions; a
  lower prediction loss is not evidence of an executable primitive.

## Next boundary

The structural replacement hypothesis is not rejected, but TMPF supplies no
formation mechanism. `GPT5_6_PRO_CORRECTION_3.md` therefore requires the
scientifically honest program-abandonment branch and one non-skill replacement
direction. No R35 compute is authorized before that final decision is valid.
