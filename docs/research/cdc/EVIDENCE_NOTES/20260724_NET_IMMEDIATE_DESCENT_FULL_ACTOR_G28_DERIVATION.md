# Net-immediate-descent full actor G28 derivation

```text
status=DERIVATION_COMPLETE
formal=false
iteration_consumed=false
predecessor=NONFORMAL_NO_DELAYED_ACCESS_TANGENT_FULL_ACTOR_G27
next_boundary=NET_IMMEDIATE_DESCENT_FULL_ACTOR_G28_PROTOTYPE
```

Let `g_i` and `g_s` be the independently normalized immediate and successor
actor gradients. G27 imposed `g_i dot g_s' >= 0` before applying
`g = 0.5 * (g_i + g_s')`. This is stronger than the actual first-order
compatibility condition. Under gradient descent, the immediate loss is locally
non-increasing whenever

```text
g_i dot g >= 0
<=> ||g_i||^2 + g_i dot g_s' >= 0.
```

G28 therefore keeps `g_s` unchanged when
`g_i dot g_s >= -||g_i||^2`. Otherwise it uses the closest Euclidean successor
gradient on the boundary:

```text
g_s' = g_s + ((-||g_i||^2 - g_i dot g_s) / ||g_i||^2) * g_i
g = 0.5 * (g_i + g_s').
```

When `g_i` is zero, `g_s` is unchanged. Dot products, norms and the final
closed-half-space check use the accepted G27 float64 plus minimum representable
lattice realization. No coefficient, learned gate or new tuning parameter is
introduced.

This one-axis change separates two explanations left by G18/G27: useful delayed
learning may require controlled instantaneous conflict, or the dual-source
problem may require a different representation/credit mechanism entirely.
The exact G17-first/G18-second screen can distinguish them without formal or
UAV compute.
