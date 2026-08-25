# Active-set-centered delayed residual G20 derivation

Date: 2026-07-24

## Accepted evidence

G19 closes two facts. First, an exact-zero additive residual and frozen fast
actor preserve the accepted G17 controller: every immediate gate passes and
fast parameter drift is exactly zero. Second, projecting one batch-global
delayed gradient against one batch-global immediate gradient yields no G18
gain. The residual moves, but spike service remains zero.

The missing degree of freedom is local anonymous redistribution. G18 does not
need a common increase in current effort; it needs more low-phase effort from
members that will charge and less from members that must remain available for
the spike. A global parameter tangent can cancel those opposing member-level
directions before the policy expresses them.

## Counterexamples

### CE-GLOBAL-ORTHOGONAL-IS-NOT-LOCAL-TANGENT

Two member corrections can have opposite effects on current reward and cancel
only when applied together. Summing their parameter gradients before one
projection may remove both. G19's 322 conflicting passes and unchanged G18
outcome demonstrate that global first-order compatibility is not sufficient
for this source.

### CE-ZERO-MEAN-LOGIT-IS-NOT-REWARD-INVARIANCE

A residual whose pre-squash means sum to zero does not prove that executed
actions sum to zero after `tanh`. Nor does an unweighted action sum preserve
G17's capacity-weighted two-channel service. The structural constraint may
expose redistribution, but it cannot replace the registered G17 behavioral
gates.

### CE-SLOT-CENTERING-WITHOUT-MASK

Centering over padding or inactive lifecycle rows makes the residual depend on
capacity and membership layout. The mean must use active rows only, inactive
residuals must remain exact zero, and slot permutations must transport the
same lifecycle correction.

## Smallest new algorithm

The new candidate is
`ACTIVE_SET_CENTERED_DELAYED_RESIDUAL_G20`.

It retains G19's two-phase schedule, trained-and-frozen fast actor, exact-zero
residual output, source-neutral observations, SGD residual optimizer,
state-only slow critic, seed structure, budgets and first-match gates. It uses
fresh fixed seed values and changes one
algorithmic mechanism: global gradient projection is removed and the residual
output is centered across the current active set before it enters the
pre-squash action mean.

For current active set `A_t`, proposal `q_i` and action coordinate `k`:

```text
r_i,k = q_i,k - (1 / |A_t|) * sum_{j in A_t} q_j,k    if i in A_t
r_i,k = 0                                             otherwise
mu_total_i = stopgrad(mu_fast_i) + r_i
```

Thus the residual has no common-mode pre-squash component. Proposals use only
the member encoding, active-set context, current lifecycle hidden state and
current observation. They do not use slot index, source identity, future state,
battery-specific code or an autoregressive prefix. The ordinary fast actor
retains the registered causal routing and prefix factorization.

## Necessary invariants

1. Zero residual exactly reproduces sampled, deterministic and teacher-replay
   anchor execution.
2. Fast actor and exploration parameters remain bitwise fixed during delayed
   training.
3. Inactive residuals/actions/likelihoods are exactly zero.
4. Each active-set residual coordinate has absolute sum at most `1e-6`; this is
   a numerical implementation bound, not a scientific result threshold.
5. Residual proposals are permutation equivariant and independent of padding
   capacity.
6. Only successor-value actor loss updates residual parameters; state-only
   critic losses reach neither actor.
7. G17 absolute compatibility remains the first scientific gate. Centering
   does not assert immediate reward invariance.

## Cheapest separating action

Add one optional step-level mean-residual hook to the generic continuous policy
and implement the active-set projection in the G20 policy. Retain G19's
one-seed budgets and thresholds with fresh seeds. Proof-sized tests cover the
seven invariants and the unchanged G17/G18 replay paths.

Passing the paired screen licenses a fresh formal executable definition.
Failure retires the exact centered residual without changing optimizer,
budget, seeds or thresholds. No formal/UAV run is scheduled and the action
costs zero conclusion-bearing iterations.

```text
next_boundary=ACTIVE_SET_CENTERED_DELAYED_RESIDUAL_G20_PROTOTYPE
formal_compute=not_scheduled
conclusion_bearing_iteration_cost=0
iterations_remaining=8
```
