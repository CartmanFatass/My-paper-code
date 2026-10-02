# Sparse-window relay toy: readings (2026-10-02)

Instrument check for `docs/Claude_docs/environment_design/SPARSE_WINDOW_RELAY_SCENARIO_DESIGN_20261002.md`.
Standard-library Python 3.11 in the Claude cloud container, every draw seeded; `swr_toy.py` reproduces
every number here. Not an HMASD result: the learners are tabular REINFORCE analogs with tabular
discriminators, not the project's PPO, Transformer coordinator or learned low-level skills. No project
host, node, direction or fit was touched.

**Setup.** 11 × 11 grid, base station at the centre, four corner sites served only through a relay chain
(link range 2, access range 1 or 2, at most 3 UAV hops), six UAVs, decisions every 10 ticks, 120-tick
episodes, five 20-tick windows (sites 0, 1, 2, 3, 0), a window pays +1 after 5 consecutive served ticks
(maximum 5 per episode); decoy variant adds +.002 per UAV-tick within one cell of the base station
(maximum 1.44 per episode). Learned arms: `flat` (one target policy per UAV, conditioned on the open
site), `flat_count` (count bonus .1/√n on the coarse 3 × 3 team configuration), `hier_nodisc` (team skill
Z → per-UAV skill z_i → shared target policy, no intrinsic reward), `hier_disc` (the same plus
discriminator rewards λ_D log q(Z | configuration) + λ_d mean_i log q(z_i | region_i, Z) at the project's
defaults λ_D = .05, λ_d = .02), `hier_disc_x4` (λ_D = .2, λ_d = .08). REINFORCE, learning rate .05,
per-decision baseline; 5,000 episodes per instance, seeds 1–5, two rungs (access range 1 = the needle, one
two-UAV chain per corner; access range 2 = wider). Readings are the final 500 training episodes.
Wall time 739 s and 737 s for the two rungs, run in parallel on two of four cores.

## 1. References (zero learning, 2,000 episodes each)

| rung | reference | windows / episode | episodes with any window |
| --- | --- | ---: | ---: |
| needle (access 1) | random targets | .020 | .019 |
| needle | sticky random (hold w.p. .9) | .005 | .005 |
| needle | stay at base station | .000 | .000 |
| needle | region_random (all UAVs inside one random 3 × 3 region) | .043 | .043 |
| needle | ordinary_window (knows schedule and chain cells) | **5.000** | 1.000 |
| wider (access 2) | random targets | .131 | .125 |
| wider | sticky random | .033 | .032 |
| wider | stay at base station | .000 | .000 |
| wider | region_random | .081 | .080 |
| wider | ordinary_window | **5.000** | 1.000 |

With the decoy, `stay` earns 1.44 and `sticky random` .84 of dense reward with zero windows: the decoy is
real. `region_random` doubles the needle hit rate over uniform targets, which is the concentration lever
the discriminator reward is supposed to pull.

## 2. Learners, pure sparse reward (decoy 0)

| rung | arm | windows / episode (mean ± SE over 5 seeds) | seeds ≥ 1 window | first 250-episode bin with seed-mean ≥ 1.0 | distinct coarse configurations visited |
| --- | --- | ---: | ---: | ---: | ---: |
| needle | flat | .016 ± .002 | 0/5 | never | 2,890 |
| needle | flat_count | .017 ± .000 | 0/5 | never | 2,893 |
| needle | hier_nodisc | .020 ± .004 | 0/5 | never | 2,889 |
| needle | hier_disc | .022 ± .004 | 0/5 | never | 2,885 |
| needle | hier_disc_x4 | .033 ± .006 | 0/5 | never | 2,857 |
| wider | flat | 1.781 ± .167 | 5/5 | 18 (episodes 4,251–4,500) | 2,888 |
| wider | flat_count | 1.995 ± .082 | 5/5 | 17 (4,001–4,250) | 2,891 |
| wider | hier_nodisc | 1.225 ± .307 | 3/5 | 19 (4,501–4,750) | 2,864 |
| wider | hier_disc | 1.577 ± .238 | 4/5 | 18 (4,251–4,500) | 2,850 |
| wider | **hier_disc_x4** | **2.048 ± .029** | **5/5** | **14 (3,251–3,500)** | 2,800 |

Per-seed final windows at the wider rung: flat 1.21 / 2.08 / 1.95 / 1.60 / 2.07; flat_count 1.73 / 2.12 /
2.12 / 2.13 / 1.87; hier_nodisc 0.29 / 1.64 / 1.51 / 0.74 / 1.95; hier_disc 1.66 / 0.71 / 2.01 / 1.49 / 2.01;
hier_disc_x4 2.16 / 2.05 / 2.02 / 2.00 / 2.02.

Seed-mean learning curves at the wider rung (windows per episode per 250-episode bin):

- flat: .15 .14 .15 .14 .16 .15 .18 .18 .22 .21 .20 .23 .25 .28 .30 .39 .56 1.06 1.57 1.99
- flat_count: .15 .15 .15 .14 .18 .16 .18 .18 .21 .20 .22 .23 .24 .30 .34 .50 1.02 1.49 1.89 2.10
- hier_nodisc: .13 .14 .14 .15 .16 .16 .16 .18 .17 .19 .19 .23 .23 .26 .26 .38 .60 .80 1.10 1.36
- hier_disc: .13 .14 .15 .14 .14 .16 .18 .17 .17 .18 .20 .23 .30 .40 .57 .85 .98 1.15 1.42 1.73
- hier_disc_x4: .12 .14 .14 .17 .16 .18 .16 .16 .20 .21 .24 .44 .94 1.37 1.72 1.97 2.02 2.02 2.05 2.05

Contrasts at the wider rung (differences of seed means; SE from the two independent seed sets):

| contrast | windows / episode | SE | reading |
| --- | ---: | ---: | --- |
| hier_disc_x4 − hier_nodisc | +.82 | .31 | the discriminator reward is what makes the hierarchy work (5/5 vs 3/5 seeds) |
| hier_disc_x4 − flat | +.27 | .17 | earlier activation and lower seed variance; level difference unresolved |
| hier_disc_x4 − flat_count | +.05 | .09 | same final level; the count bonus gets there about 750 episodes later |
| hier_disc − flat | −.20 | .29 | unresolved; the project's default weights give no visible benefit here |
| hier_disc − hier_nodisc | +.35 | .39 | unresolved |

## 3. Learners with the decoy (+.002 per UAV-tick next to the base station)

| rung | arm | windows / episode | seeds ≥ 1 window | all-episode mean total reward (windows + decoy) |
| --- | --- | ---: | ---: | ---: |
| needle | flat | .016 ± .002 | 0/5 | .207 ± .000 |
| needle | flat_count | .021 ± .003 | 0/5 | .206 ± .001 |
| needle | hier_nodisc | .023 ± .003 | 0/5 | .225 ± .001 |
| needle | hier_disc | .020 ± .001 | 0/5 | .224 ± .001 |
| needle | hier_disc_x4 | .020 ± .005 | 0/5 | .296 ± .021 (its last bin reaches .66: decoy capture, no windows) |
| wider | flat | 1.783 ± .154 | 5/5 | .616 ± .037 |
| wider | flat_count | 1.498 ± .261 | 4/5 | .579 ± .055 |
| wider | hier_nodisc | 1.493 ± .200 | 4/5 | .613 ± .048 |
| wider | hier_disc | 1.249 ± .333 | 2/5 | .631 ± .116 |
| wider | hier_disc_x4 | 2.068 ± .136 | 5/5 | 1.139 ± .130 |

At the needle rung the shared target policy of the hierarchy arms learns the decoy (camp next to the base
station) while flat does not learn even that in 5,000 episodes; at the wider rung the decoy lowers the
default-weight hierarchy and the count-bonus arm (2/5 and 4/5 seeds) and leaves flat and the ×4 arm where
they were. Seed variance is large; this is a direction, not an established effect.

## 4. Per-site diagnostic (recording-only field added after the main run; dynamics and random draws unchanged)

Re-running single instances with the added `final_site_windows` field reproduces the main run exactly
(final windows 2.08, 2.16, 0.29, 1.732 and the same first rewarded episodes). Windows per episode by site
in the final 500 episodes, wider rung, no decoy:

| instance | site 0 (two windows) | site 1 | site 2 | site 3 |
| --- | ---: | ---: | ---: | ---: |
| flat, seed 2 | 1.88 | .09 | .07 | .04 |
| hier_disc_x4, seed 1 | 1.97 | .17 | .01 | .01 |
| flat_count, seed 1 | 1.54 | .06 | .07 | .05 |
| hier_nodisc, seed 1 | .16 | .03 | .02 | .08 |

The plateau near two windows is site 0, the site whose chain pays twice per episode. Every activated
instance learned that one chain; the three other needles stay at the random rate. What the exposure
bought is the first mission, not the schedule.

## 5. What this changes

- **Changed:** "the discriminator reward is an exploration device" is now supported in the abstraction,
  but only when its weight is large relative to the sparse reward: at the project's default weights the
  hierarchy is no better than flat, and without discriminators the hierarchy is the worst and least
  reliable arm. A real-host comparison must carry a stronger-weight HMASD arm (design §2, arm 1b) or it
  tests the wrong thing.
- **Changed:** sparsity must be calibrated before buying fits. A 2% hit rate under random targets is
  unlearnable by every analog at 5,000 episodes; a 13% hit rate is learnable by every arm. The real
  scenario's zero-fit floors now carry a 5–20% window-hit band for the random slot program (design §4).
- **Unchanged:** the count-based bonus reaches the same final level as the best discriminator arm, later.
  The mechanism's claim at this rung is earlier activation and lower seed variance, not a unique
  capability; the real-host arms keep the count-bonus control for that reason.
- **Unchanged:** the ordinary scheduler that knows the schedule sits at the ceiling of 5 on both rungs; no
  learned arm approaches it, and the activated learners stop at the first mission. A learning curve
  (10k, 20k episodes) on the toy would show whether the remaining three needles are found with more
  exposure; it was not run.
- **Uninformative outcomes and cost:** the needle rung is uninformative about arm differences (all at the
  floor) and cost about 12 minutes of CPython; the decoy comparisons are too variable at five seeds to
  rank arms. Total cost of the study: about 25 minutes of CPython on this container, zero node resources.

## 6. Limits

No radio physics, continuous control, PPO, advantage estimation, Transformer coordinator or learned
low-level skills; intrinsic rewards are computed once per decision on the end-of-segment configuration
rather than per tick; discriminators are exact tabular conditionals rather than trained networks; the
schedule is fixed across episodes. Five seeds per arm give descriptive, not confirmatory, intervals. The
toy says which design choices on the real host would make the comparison informative; it does not
predict the real host's outcome.
