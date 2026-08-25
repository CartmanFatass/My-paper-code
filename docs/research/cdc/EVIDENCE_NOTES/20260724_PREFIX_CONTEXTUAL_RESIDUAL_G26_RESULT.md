# Prefix-contextual residual expressivity G26 result

Date: 2026-07-24

## Evidence identity

The first artifact at source `96a876f2f11f437cf0566ebfd1a6d0668dc34979`
is excluded: the larger residual advanced constructor RNG before the credit
baselines, so it did not preserve G25's fast anchor. It is an operational
diagnostic failure, selected no scientific branch and consumed no iteration.

The accepted repaired evidence is:

```text
source_commit=e60a9dfd7c3e70f7dfb13bef3e0312c23615568d
run=logs/nonformal_prefix_contextual_residual_expressivity_g26_20260724_e60a9df_pm2
formal=false
iteration_consumed=false
status=COMPLETE
branch=NO_POINTWISE_PREFIX_CONTEXTUAL_FIT_G26
runtime=cpu, torch 2.7.0+cpu, one thread
```

The repair copies every G25 non-residual tensor bitwise and restores the exact
post-construction RNG state. The accepted fast-anchor utility is consequently
the same `0.6667880132`. All 36 rows, three slot orders, twelve times,
lifecycle/inactive contracts, residual-only ownership, finite updates and the
G18 information gate close; replay and anchor error are `0.0`.

## Registered evidence

```text
initial_active_action_mse=1.4311925173
final_active_action_mse=0.3414649963
final_to_initial_ratio=0.2385877457
absolute_gate=0.001
relative_gate=0.10
fast_anchor_utility=0.6667880132
final_utility=0.9281122815
gain_over_anchor=0.2613242682
final_spike_utility=0.8816298284
final_rotating_effort_share=0.8598179371
minimum_step_utility=0.6226009429
```

The first-match pointwise branch is exact. Direct anonymous set context plus
the live prefix improves the local residual's MSE and closed-loop behavior but
does not make the frozen-anchor additive family representationally sufficient
under the accepted gate.

## Scientific effect

The earlier full-actor channel-isolated G18 algorithm proved that full actor
capacity can learn the delayed source, but failed formal G17 compatibility.
G25/G26 now show that bitwise freezing that actor and relying on an additive
residual is too restrictive. The smallest new algorithm therefore returns
capacity to the full actor while protecting the immediate objective at the
gradient level: successor gradients may update only after one-way projection
out of conflict with the immediate gradient.
