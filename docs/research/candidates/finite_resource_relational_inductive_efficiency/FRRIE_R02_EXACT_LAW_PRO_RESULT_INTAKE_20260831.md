# FRRIE R02 exact-law Pro result intake — 2026-08-31

Status: `EXTERNAL_REVIEW_ACCEPTED_WITH_REPAIRS / NO_RESULT /
NO_STANDALONE_REOPEN`

## Conclusion

The archived Pro review accepts the 916-row mean-preserving Bernoulli-IUT and supplies exact
repairs to the population, completion, and smaller-object laws. It does not change the
direction-level recommendation to close standalone FRRIE investment.

No result run occurred, and the review creates no `PHY_TRUST` or `EDGE_FLEX` polarity.

One conclusion does change materially from the local pre-review synthesis:

> An exact, finite, strictly smaller Level-A object exists at 909 rows while preserving the same
> four individual update-512 expected-numeric-mean conditions and dependence-robust IUT claim.

The 909 object is not *materially* smaller: it saves seven rows, `0.764%` of the 916-row work. The
review identifies no valid Level-A construction below 909. The interval `523..908` remains an open
minimax/worst-coupling problem.

A 720-row Level-B object is also exact and finite and reduces fixed maximum work by `21.397%`, but
it changes the scientific target to two equal-weight roster-mixture means. A mixture pass can hide
a strongly adverse individual roster, and the accepted evidence gives no independent native-utility
reason for choosing the 50/50 mixture. It is not a replacement for the four-roster object.

Neither 909 nor 720 is executable by the current repository production surface. The existing V2
code remains a 24-root R01 structure with no R02 packet, analyzer/result map, complete production
trainer/orchestrator, or result-process resource observation. Production disposition remains
`REPAIR_REQUIRED`.

## What the review accepted

The following local conclusions stand:

- fixed `L_star="FRRIE-R02-LSTAR-20260831-01"` in every execution RNG address;
- direct iid uniform-with-replacement 256-bit root rows, with duplicates retained and record IDs
  excluded from RNG;
- independent packed 1075-bit ancillary words and exact `Y=1{B<M}` Bernoulliization;
- no stochastic event/basin/role support gate for the four total contrasts;
- whole-attempt invalidity for missing, nonfinite, partial, resource-failed, or nonconforming
  execution;
- same-packet rerun from row zero after unsealing and an outcome-blind repair;
- level at most `0.05` and dependence-robust joint-power lower bound
  `0.800537003890475350` for the 916-row IUT; and
- no equality, harm, wide-superiority, semantic, or mechanism conclusion from a valid nonpass.

## Exact repairs supplied by the review

### Margins and threshold representation

The scientific margins must be exact rationals:

```text
delta_R = 1/25
delta_E = 2/25
eta     = 13/120
```

They must not be defined by the nearest binary64 values of decimal `0.04` and `0.08`. The observed
contrasts remain exact reals decoded from their final canonical binary64 bytes.

At `X=+1`, the threshold is `M=2^1075`. An implementation must therefore store `M` with 1076-bit
capacity or use an explicit positive-endpoint branch. A 1075-bit threshold container would
overflow even though the ancillary word itself has 1075 bits.

### Pre-unseal and post-unseal completion

Pre-unseal redraw is not automatically safe. Packet construction must be total over every payload
bit string. An unopened packet may be redrawn only for an independently characterized envelope
failure whose occurrence is independent of the hidden payload, or when the accepted-packet law is
separately proved to remain product-uniform. Content-sensitive malformedness would condition the
root population.

After either packet is unsealed, the local immutability rule is sound: every technical replacement
restarts the same complete root and ancillary packets from row zero; no redraw, substitution,
completed-row retention, checkpoint replacement, or partial-value salvage is allowed. Persistent
root-dependent failure leaves the object `INVALID`; it does not authorize another packet.

## Smaller exact objects

### Level A: 909 rows, same four-roster claim

At each randomized boundary, the exact rejection probability is rational. A fixed fair-bit repair
uses one independent 64-bit word per component and replaces each boundary probability by its
64-bit dyadic floor. This preserves component level, loses less than `2^-64` marginal power per
component, and lowers the joint certificate by less than `2^-62`; the joint lower bound remains
strictly above `0.80`.

The 909-row main ancillary stream has `3,908,700` scientific bits. Its canonical byte container has
four fixed zero terminal padding bits after the complete global stream, with no per-word padding.
Four additional independent 64-bit words implement the boundary decisions.

The exact maximum work is:

```text
environment slots:          4,631,740,416
conventional static FLOPs:  3,599,251,364,772,864
```

This is a valid finite Level-A object, but the seven-row saving does not meet the registered
material-cost standard.

### Level B: 720 rows, changed mixture claim

The preferred exact mixture law averages the two final binary64 contrasts as exact dyadics before
Bernoulliization. Each of the two mixture components needs one 1076-bit ancillary word per row;
its threshold needs 1077-bit capacity or endpoint handling. The two randomized boundaries can use
independent 64-bit dyadic floors and retain joint power strictly above `0.80`.

Its maximum work is:

```text
environment slots:          3,668,705,280
conventional static FLOPs:  2,850,892,170,117,120
```

A positive result selects `PHY_TRUST` only for an independently accepted 50/50 mixture of
`N={6,21}` direct utility and a 50/50 mixture of `N={9,15}` competence. It establishes no
individual-roster condition. Without an external native-utility premise for that mixture, it is a
different mathematical object without current Portfolio decision relevance.
It is not registered as a successor.

### Level C: staged and sequential objects

Competence-first staging preserves level but does not reduce maximum successful-branch work. At
the registered alternative, the two competence tests proceed to the direct stage with probability
at least about `0.903554`, so no uniform material expected saving follows.

The capped-2048 SPRT can use exact rational likelihood-ratio comparisons and has valid component
and global level. Its reported power, ASN, and robust `E[max_j T_j]` values still lack an exact
finite recursion certificate. Even if accepted, the robust expected maximum is about `920.95`,
above 916, and the maximum is 2048. It is not a smaller whole-panel object.

## Universal structural proposition

The literal pre-training first native action is universally identical across the two arms because
their initialization, state, observations, and action tapes are identical before learning. This
proves only one common transition and has no decision value.

The closure-relevant proposition must instead cover every update through 512 and every
claim-relevant evaluation transition. A sufficient certificate proves universal projection
noncontact and inductively preserves complete parameter, optimizer, policy, action, recurrent, and
native-state equality through the full return. Equality of only the first update-512 evaluation
action is still insufficient to prove equal returns.

## Direction and resource impact

The external review is prospective mathematics, not implementation or runtime evidence. It adds
no production throughput, wall-time, RSS, scratch, durable-I/O, serialization, concurrency, or
completion observation. The 909 and 720 objects remain non-executable in the current production
tree.

The standalone closure recommendation therefore remains:

- close investment in 916 and 909 because the same-claim saving is not material;
- treat 720 as a different, unaccepted utility object and do not register it as a successor;
- do not use the capped SPRT as a whole-panel discount;
- transfer no FRRIE polarity to a structural successor; and
- permit reentry only for a materially lower-cost same-meaning Level-A construction or a sound
  all-update/all-transition universal complete-return equality certificate.

The cheapest new scientific discriminator is a finite minimax/worst-coupling calculation over a
prospectively chosen material row ceiling below 909. A certified power at least `0.80` would create
a materially smaller Level-A candidate; a matching upper bound below `0.80` would close that row
range. No result experiment is needed for this discriminator.

## Evidence boundary

New input:

- `temp/sessions/hmasd-chatgpt-pro-transport/archive/finite_resource_relational_inductive_efficiency/portfolio-frrie-r02-exact-law-20260831-01/RESPONSE.md`

Compared against:

- `FRRIE_R02_EXACT_LAW_AND_SMALLER_OBJECT_SYNTHESIS_20260831.md`
- `FRRIE_R02_RESOURCE_DISCRIMINATOR_20260831.md`
- `FRRIE_R02_DIRECTION_CONVERGENCE_20260831.md`

Where these documents conflict on exact margins, pre-unseal redraw, finite 909 boundary
randomization, or the closure-relevant universal proposition, this intake is the current
direction-local interpretation.
