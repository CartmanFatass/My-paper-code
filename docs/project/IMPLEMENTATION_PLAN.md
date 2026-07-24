# G19 fast-policy-anchored delayed-residual implementation plan

> Use `$hmasd-agile-research-development`. Generic Superpowers execution,
> compatibility work, workflow hashes and review stacks are disabled.

```text
last_formal=ACTOR_CRITIC_ISOLATED_CHANNEL_CREDIT_G18
last_formal_result=NO_G17_COMPATIBILITY_CRITIC_ISOLATED_G18
active_source=DELAYED_BATTERY_ROSTER_G18
source_gate=PASS_DELAYED_BATTERY_ROSTER_INFORMATION_GATE_G18
active_implementation=FAST_POLICY_ANCHORED_DELAYED_RESIDUAL_G19_DERIVATION
backend=cpu
torch=2.7.0+cpu
torch_threads=1
formal_iteration=19_complete
iterations_remaining=8
formal_compute=not_scheduled_for_g19
algebra_status=ZERO_COMPUTE_DERIVATION_REQUIRED
screen_contract=docs/research/designs/ACTOR_CRITIC_ISOLATED_CHANNEL_CREDIT_G18.md
```

## Accepted active line

1. The exact TD(0), raw-sum, channel-normalized and actor/critic-isolated G18
   candidates are closed without retry or tuning. They remain only as frozen
   evidence and focused regression surfaces.
2. Formal G18 proves that the delayed battery source is learnable: every
   delayed-access, mechanism and replicate-stability threshold passed. It also
   proves that a shared actor update does not reliably preserve the accepted
   G17 immediate controller across fresh seeds.
3. G17 remains the accepted fast immediate-service algorithm. G18 does not
   relabel or weaken that result and does not advance to UAV.
4. The next derivation must isolate one new algorithmic degree of freedom: an
   explicit fast-policy anchor plus a zero-initialized delayed residual whose
   optimization cannot overwrite the fast path. It must remain environment
   neutral and may not read battery, demand phase or lifecycle role directly.
5. No G19 implementation or compute is scheduled until the derivation freezes
   the smallest separating invariant and proof-sized acceptance boundary.
