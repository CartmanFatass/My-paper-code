# D7.S R4 — the formal result: `PART_A_CONTRADICTION`

The first valid fresh-population R4 measurement. Every gate upstream passed; the
Part-A control is what stopped it.

```text
run          30403322062, tag d7s-audit-3, instrument a00612ad
population   TOPOLOGY_SEEDS_R4 = 20260734..41, 8 shards x 1 topology
wall clock   2h08m (22:06:31Z -> 00:14:58Z), all eight shards success
branch       PART_A_CONTRADICTION
limb_states  {stable: AFFIRMATIVE_NONMATERIAL, flex: UNRESOLVED}
```

## The sentinel passed, so the rest is readable

```text
exact_seed_list                            True
no_r3_overlap                              True
identifies_r4_contract_and_namespace       True
per_topology_block_identities              True
registered_episode_counts                  True
every_topology_accounted_for_exactly_once  True
```

Every shard independently carried `r4_population_namespace =
D7_S_R4_ABSOLUTE_FOCAL_MARGIN`, ran the registered 8/8 episode volume, and
recorded zero hash failures. The identity is earned by every contributing
process, not asserted once at the end.

## The result

```text
part_a.verdict              PART_A_CONTRADICTION
part_a.d_a_point            0.4839380477047651
part_a.lower_contrast_lcb   4.318957155049049      LCB95(D_A + 5) > 0
part_a.lower_contrast_ucb   6.685962861943237
part_a.upper_contrast_lcb   3.314037138056763      LCB95(5 - D_A) > 0

support.ok                  True
conformance.ok              True
  invalidated_pairs_count   0
  topology_hash_ok          True
  arm_distinct_ok           True

primary_g.degenerate                      False
primary_g.component_invariance_evaluated  True
primary_g.components_invariant_stable     False
primary_g.components_invariant_flex       False
```

**This is a positive equivalence finding, not a failure to resolve.** Both
one-sided bounds clear zero comfortably, so the bootstrap established
`|D_A| < 5` on both sides at 95%. The arms are equivalent *within the
registered margin*, and that is a measurement, not an absence of one.

Per-topology `D_A` means straddle zero:

```text
20260734  n=6  mean=-1.2609    20260738  n=8  mean=+2.6829
20260735  n=7  mean=+0.6096    20260739  n=7  mean=-1.9098
20260736  n=7  mean=-0.1806    20260740  n=8  mean=+0.1581
20260737  n=7  mean=+3.0277    20260741  n=8  mean=+0.7446
```

Within-topology spread is wide (individual contributions from −7.9 to +11.5),
so the tight pooled interval comes from topology-level cancellation, not from
small within-topology variance.

## What it means, stated as the contract states it

`PART_A_CONTRADICTION` fires when the two arms are **equivalent**. The name
reads backwards until the reasoning is visible: if the source were necessary,
the full-sync arm should *differ* from constructive-mixed. It does not. So the
focal result cannot be read as source necessity, and §7 puts this above the
combined result in the precedence — it masks whatever the limbs said.

What it masked, recorded because §6 requires the limb states to survive the
branch name: `(AFFIRMATIVE_NONMATERIAL, UNRESOLVED)` — which maps to
`NO_MATERIAL_STABLE_PERSISTENCE_IDENTIFIED`. **That mapping is not this run's
result.** It is recorded so the mask is auditable, and it is exactly the
information R3 lost by letting a top-level branch name erase the per-limb states.

## The dev topology predicted this, and that is the uncomfortable part

Step E, on development topology 20260725 alone, measured `D_A ≈ 0.46` and noted
it "contradicts legitimately" — at the time this was an obstacle to the
exercise, worked around by steering `D_A` to a separated value so the nine
combined results could be reached at all.

The full eight-topology population now returns `0.484`. The dev topology was not
an outlier: **the source-control contrast is systematically near zero at this
margin**, and the step-E note recorded the signal without recognising it as one.

Whether that is a property of the estimand, of the `MATERIALITY_MARGIN = 5.0`
anchor, or of the S7-S3 carrier is a scientific question and is not the Project
Manager's to answer. It goes to Pro as the third touchpoint.

## Provenance

Artifact at `logs/d7s_r4_30403322062/pooled/d7_s_event_aligned.json`; the eight
shard artifacts beside it under `shards/`. Numbers above are transcribed here
because `logs/` is untracked and `git add -f` is forbidden.

## Independent re-derivation of the Part-A numbers

The reviews of this instrument all stubbed the environment, so before this run
nothing had checked its numerics against real data. Closed here, by an
implementation reading only the artifact and sharing no code with the audit
module.

```text
point estimate       0.4839380477047651   reproduces BIT FOR BIT, diff 0.0e+00
naive unit-pooled    0.550812             differs -- so topology weighting is
                                          genuinely applied, not merely claimed
my bootstrap, 3 seeds  LCB95  -0.6382 / -0.6734 / -0.6452
                       UCB95  +1.7020 / +1.6563 / +1.6574
reported (inverted)    LCB95  -0.6810     UCB95  +1.6860
```

The bit-exact point estimate is the sharper of the two checks because it is
deterministic. The naive unit-pooled mean is what the code would have produced
had it pooled events instead of weighting topologies; it differs, so this is a
discriminating check rather than a tautology.

Interval differences are Monte-Carlo noise at `BOOTSTRAP_ITERS = 10000`. The
equivalence holds under every re-derivation, a factor of ~3 inside the margin.

`D_A` 95% interval, inverted from the registered contrasts: **[-0.681, +1.686]**,
point **+0.484**, against a margin of **+/-5**.

## The masked limb states, re-derived the same way

The limb states are masked by the branch but are disclosed to Pro, so a wrong
value there is a wrong disclosure. Re-derived by the same independent path:

```text
u_star_stable_point  -1.0919725533508093   BIT FOR BIT, diff 0.0e+00
u_star_flex_point    -0.1643991783956942   BIT FOR BIT, diff 0.0e+00
units per topology   [5, 6, 6, 5, 6, 7, 8, 6]   identical on both limbs,
                     which is expected -- the two lists are appended in lockstep
```

Re-applying the MIRRORED resolvers from first principles, not by calling them:

```text
stable  MATERIAL iff UCB95 < -5   -> +1.3401 < -5 ?  False
        AFFIRMATIVE_NONMATERIAL iff LCB95 > -5 -> -3.1781 > -5 ?  True
        => AFFIRMATIVE_NONMATERIAL
flex    MATERIAL iff LCB95 > +5   -> -8.1859 > +5 ?  False
        AFFIRMATIVE_NONMATERIAL iff UCB95 < +5 -> +7.4558 < +5 ?  False
        => UNRESOLVED
```

Both match the artifact. The mirror is the science and not a convention, and it
is the exact asymmetry an earlier exercise got wrong by using one `U*` table for
both limbs -- so re-deriving it rather than trusting it is the point.

**Every numeric claim in the result submission is now independently verified**:
the Part-A point and interval, both `U*` points, and the limb states.
