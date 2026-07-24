# Direction-balanced full actor G30 derivation

```text
status=DERIVATION_COMPLETE
formal=false
iteration_consumed=false
predecessor=NONFORMAL_NO_DELAYED_ACCESS_REALIZED_TANGENT_G29
next_boundary=DIRECTION_BALANCED_FULL_ACTOR_G30_IMPLEMENTATION
```

G28 nearly accesses both sources but its closest-half-space projection preserves
raw channel magnitudes. G29 constrains the Adam-transformed step and suppresses
G18 much more strongly. The remaining bounded discriminator asks whether raw
gradient *scale*, rather than directional conflict, causes the paired source
instability.

For nonzero global actor-gradient norms define

```text
u_i = g_i / ||g_i||
u_s = g_s / ||g_s||
h = 0.5 * (u_i + u_s).
```

Then

```text
g_i dot h = 0.5 * ||g_i|| * (1 + u_i dot u_s) >= 0
```

by Cauchy--Schwarz. The complete successor direction is retained and neither
channel's raw magnitude dominates. Exact zero branches are explicit and use no
epsilon: both zero gives zero; one nonzero channel contributes exactly half its
unit direction. Exact opposite directions give exact mathematical zero.

Norms and diagnostic dots use float64; the actor tensor uses its registered
dtype and the unchanged `-1e-7` runtime bound. No lattice repair or projection
may rotate the direction-balanced result. Ordinary Adam receives `h`, advances
once, and its moments plus parameters define a new checkpoint identity that
cannot resume G28/G29.

No global rescale is introduced. The existing gradient clip at `0.5` provides
the only magnitude cap; matching a raw norm would reintroduce an arbitrary
scale choice. G30 changes only actor-gradient composition and uses the same
paired screen to distinguish direction balance from another credit or
representation failure.
