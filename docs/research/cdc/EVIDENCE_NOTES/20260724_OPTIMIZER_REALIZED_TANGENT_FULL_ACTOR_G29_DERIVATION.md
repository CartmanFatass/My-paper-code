# Optimizer-realized tangent full actor G29 derivation

```text
status=DERIVATION_COMPLETE
formal=false
iteration_consumed=false
predecessor=NONFORMAL_NO_DELAYED_ACCESS_NET_DESCENT_G28
next_boundary=OPTIMIZER_REALIZED_TANGENT_FULL_ACTOR_G29_IMPLEMENTATION
```

G28 constrains the raw equal-weight gradient before Adam. Let `g_i` be the
immediate-channel actor gradient and let

```text
d = theta_before - theta_adam
```

be the actual descent displacement proposed by one Adam step using the clipped
raw equal average `0.5 * (g_i + g_s)`. Adam's moment state and coordinate-wise
preconditioner mean that
`g_i dot 0.5*(g_i+g_s) >= 0` neither implies nor is implied by
`g_i dot d >= 0`. G28 may therefore remove useful raw successor components
that Adam would transform into an admissible parameter step.

G29 removes the raw-gradient projection. It advances Adam exactly once with the
equal combined gradient and leaves both parameters and optimizer state bitwise
unchanged whenever `g_i dot d >= 0`. If the proposed displacement conflicts,
only the realized parameter displacement is moved to the closest boundary:

```text
d' = d - ((g_i dot d) / ||g_i||^2) * g_i
theta_after = theta_before - d'.
```

The dot, norm and analytical projection use float64. After actor-dtype casting,
one maximum-absolute-`g_i` coordinate walks to the first closed float lattice
point. Zero `g_i` or zero displacement is vacuously unchanged. Nonfinite input,
state, displacement or closure fails closed.

This is deliberately a new optimizer semantics: Adam's step counter and moments
record the unprojected equal combined gradient, while the actor parameters
record the projected realized displacement. The optimizer is not called twice,
rolled back or silently replaced. Its state and the projected parameters are
both checkpoint state. Critic optimization remains disjoint and unchanged.

The candidate is parameter-free and changes only which geometric object owns
the immediate-descent constraint. It retains every G17/G18 source, equal
channel normalization, full actor, exact-zero residual, budgets, gates and
first-match order. A paired bounded screen separates whether the last G28
access gap comes from its pre-Adam overconstraint or from a remaining credit or
representation limitation.
