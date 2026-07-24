# Return-to-go direction-balanced G31 derivation

```text
status=DERIVATION_COMPLETE
formal=false
iteration_consumed=false
predecessor=NO_DELAYED_ACCESS_DIRECTION_BALANCED_G30
next_boundary=RETURN_TO_GO_DIRECTION_BALANCED_G31_IMPLEMENTATION
```

Formal G30 proves that equal global channel directions preserve G17 and learn
broad G18 utility, gain and rotating effort. Its only registered failure is
fresh-seed spike access. G27--G30 all retain the same one-step successor target
`gamma * V(s_(t+1))`; they differ only in actor-gradient/update geometry. The
nearest distinct question is therefore target estimation rather than another
projection rule.

For a completed trajectory define the detached realized future tail

```text
F_t = sum_(k=t+1)^(T-1) gamma^(k-t) r_k
F_(T-1) = 0
A_immediate,t = r_t - b_immediate(s_t)
A_successor,t = F_t - b_successor(s_t).
```

The slow critic still fits the full discounted return including `r_t`; the
successor baseline fits `F_t`. G30's exact global unit-direction half-sum,
ordinary Adam, gradient clip and phase ownership are unchanged. The rule reads
only the environment-neutral reward stream after rollout. It does not add a
future observation, spike flag, battery field, event label or inference-time
input.

Three counterexamples bound the claim:

1. `CE-ONE-STEP-CRITIC-SEED`: a learned `V(s_(t+1))` can propagate the sparse
   spike with seed-dependent error even when broad utility is high; a realized
   tail removes that bootstrap estimator from the actor target.
2. `CE-LONG-GAE-EXOGENOUS-NOISE`: the earlier G17 long-trace experiment learned
   a near-constant policy because later independently resampled demand was
   assigned to current actions. Monte-Carlo tails may amplify the same noise;
   G30 geometry is not proof against Adam or sampling variance.
3. `CE-INACTIVE-ROW-TEAM-TAIL`: a member active at `t` can receive later team
   reward accrued while it is inactive. Exact current active masks prevent a
   fictitious action but do not by themselves prove individual causal credit.

The candidate is worth exactly one bounded paired screen because the precise
combination is untested, parameter-free and environment-neutral. It must retain
G17 compatibility, G18 access/mechanism, exact lifecycle/replay and the frozen
first-match order. Any non-promising valid branch retires G31 without seed,
budget, threshold, coefficient or source rescue.
