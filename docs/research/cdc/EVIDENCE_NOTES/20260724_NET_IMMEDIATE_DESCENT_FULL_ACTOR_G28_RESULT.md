# G28 net-immediate-descent full-actor bounded result

```text
status=COMPLETE
formal=false
iteration_consumed=false
accepted_source_commit=0ac8fa605b4ee82b96600220c8e960b174e4b843
accepted_run=logs/nonformal_net_immediate_descent_full_actor_g28_20260724_0ac8fa6_pm2
branch=NONFORMAL_NO_DELAYED_ACCESS_NET_DESCENT_G28
iterations_remaining=8
```

## Evidence closure

The repaired CPU one-thread artifact completed its run, artifact check and
mechanical analysis with exit code zero. Replay and applied-gradient identity
errors are exact zero, lifecycle and optimizer ownership pass, and the minimum
combined immediate-gradient dot is `1.5619988e-11`. The first attempt at source
`74fe15cd8725c97459f8c8d2a8347a89d8181eca` produced no result because its
single float-lattice correction could not close one high-dimensional update.
That attempt is an operational reproducer only and consumes no iteration.

## Registered result

G17 remains compatible: final IID/held-out utility is
`0.9600854/0.9517933`, effort/mix correlation is
`0.9903934/0.9963926`, and all mapping, minimum-episode and gain gates pass.

G18 improves sharply over G27. Utility moves from the fast anchor `0.5833333`
to `0.9632779`, gain is `0.3799446`, rotating effort share is `0.8696263`, and
minimum-step utility is `0.5712655`. However spike utility is `0.8898338`,
below the frozen `0.90` access floor. The registered first-match branch is
therefore `NONFORMAL_NO_DELAYED_ACCESS_NET_DESCENT_G28`. Utility, gain and
mechanism diagnostics cannot relabel that branch.

## Scientific disposition

Allowing successor conflict cancelled by the immediate channel is materially
better than G27's strict successor tangent, while the raw-gradient half-space
still narrowly blocks registered delayed access. G28 is closed without tuning
its threshold, budget, seed, optimizer or result gate and without UAV or formal
promotion.

The nearest untested distinction is between the raw combined gradient and the
actual Adam parameter displacement. Adam preconditioning and momentum mean the
G28 raw-gradient dot does not define the realized update direction. The next
bounded candidate keeps equal credit channels but protects immediate descent
only on the realized actor displacement.
