# Finite native-radio placement: exploratory scope

## Claim and evidence

In the fixed S7-S2/H3000 central-information comparison, one finite native-radio
spatial-search package R improved complete mean service relative to original
H1 and a stronger eight-start geometric solver G. This is evidence of
conditional ordinary spatial-package headroom, not a claim about a pure
objective formula, global optimization, a learned representation or safety.

Source: `8ec998ecac68f93697ab31c65d5732ab337f4203`; fixed eight worlds
36092801-36092808, three programs, 24 complete episodes/72,000 native steps,
0 fits. Same central user/BS snapshots every 30 steps, legal team geometry and
energy, movement caps, F and native guard. R changes objective, finite search
and target support together. Returned/charging UAVs still communicate above
the native cutoff. See [prospective design and complete reading](NOTES.md)
and [retained summary](../../../../runs/uav_radio_placement/b01_spatial_a01/summary.json).

Primary R-G: QoS +.028758 [.009323,.048194], J +69.938482 [3.052642,136.824323].
R-H: QoS +.027374 [.002805,.051944], J +61.645574 [-10.641620,133.932767].
G-H mean QoS -.001384/J -8.292909 with wide intervals. Intervals are
descriptive paired t7, conditional on these worlds and deterministic programs.

## Adverse evidence and limits

R loses J to G in 36092801 despite higher service; it loses service and J to H
in 36092806. Its minimum battery reaches .088559, and <=10% reserve exposure
reaches 6.870833% of UAV-steps in 36092805. Three R worlds have appreciable
reserve/negative-margin tails despite lower total movement and consumption.
Zero cutoff/depletion in this panel is not a safety or equivalence guarantee.

The full H/G/R batch uses 59,988 queries and 1.3765 measured worker-CPU hours,
with R per-world worker CPU 68.7% higher than G. Compute is not priced by native J. Independent
artifact reading verifies raw hashes, all metric arithmetic, user-path pairing
and saved search decisions; full RNG states were not retained offline.

This does not establish that remaining service loss is mainly outside geometry,
that improving clustering SSE is useless, or that radio scoring caused the
package gain in isolation. Static scoring omits transit, future users, energy
dynamics and live association history. The result is not a default replacement
recommendation for H, and it selects no confirmation or automatic repair run.
Independent scientific review and DM disposition retain R as a conditional
asset, keep H as the default anchor and end the current recipe's investment.
The complete recommendation, adverse reading and unselected Root-level
comparison suggestion are recorded append-only in NOTES. No confirmation is
selected.
