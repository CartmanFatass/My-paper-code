# Reconciliation — R4 is derivable, and my design-defect claim was wrong

Ruling: `21_PRO_OPEN_RAW.md`, stage commit `21455362`.

## The decision

**SELECT ANCHOR E; R4-A IS DERIVABLE; RETAIN S7-S3 CONDITIONALLY.**

`delta_stable = delta_flex = 5.0` G-units — the cutoff-equivalent absolute focal
margin. R4-Q and R4-B are **parked**, not rejected: Q reactivates only if an
external `q*` is supplied independently of R3, B if a sign-fixed
focal-commensurate scale is derived without treatment returns.

## Where I was wrong — both corrections, stated first

**1. My claimed R3 design defect does not exist.** I asserted that R3's ratio
estimand and its frozen linear realization diverge once `B` can be non-positive,
and offered it as a defect in the registered design. Pro:

> The frozen files do not independently register an unconditional ratio gate that
> may be interpreted when `B_m <= 0`.

The contract freezes the **linear** gate together with the separate
`LCB95(B_m) > 0` requirement, and that requirement *is* what keeps the linear
form inside the domain where it equals the ratio. My `B = -1` case lies **outside
the registered interpretation domain** — such a run fails the `B_m` gate and
terminates before the linear contrast is ever interpreted.

So the counterexample correctly shows *why positivity is necessary*. It does not
show R3 ever applied the gate outside its domain. **No additional R3 retraction
is required**; the previous result semantics and portfolio update stand.

**2. I reversed the sign in my own worked example.** `U*_stable = V_SET − V_KEEP`,
so `U*_stable = −3` means SET is three G-units **worse** than KEEP — which is
precisely why it points toward *stable persistence*. My question said "SET is 3
G-units BETTER than KEEP." The arithmetic conclusion (−3 does not clear a −5
margin) was right; the prose explaining its sign was backwards.

**3. A precision point I must keep straight.** The artifact's `B_m` **point**
estimates were positive (`+0.180`, `+4.289`); only their lower bounds were
non-positive, and some individual topologies were negative. The correct reading
is *a positive population normalizer was not established* — never *the population
normalizer was proved negative*.

## Why the fork resolved to Anchor E

The proposition is about the **total task consequence of one renewal decision**,
not its average effect per primitive step. A service cutoff is a discrete task
consequence, and its external value does not become one quarter as important
because the flex process must be observed four times as long.

So the unequal per-step bars I flagged as a concern — 3.60% of `H_stable` versus
0.91% of `H_flex` — are **not an unfairness**. They are the expected consequence
of evaluating cumulative task value over different causal windows. Choosing an
equal per-step bar would have defined a *different proposition*: that the renewal
decision must produce the same average effect rate over its whole downstream
window. That is not the registered source-necessity proposition.

"Cutoff-equivalent" does **not** mean the result must be carried by an observed
cutoff. Five G-units may arise from any registered combination of QoS, capped
return-cost, cutoff and depletion differences — the frozen objective already
declared those exchange rates. Five is chosen because it is the smallest nonzero
coefficient attached to a *discrete, window-local, task-semantic* event, where
QoS and return cost are rate-like and their one-step interpretation depends on
the simulation clock.

Pro is explicit that the anchor is **not mathematically unique**, only
non-post-hoc, externally interpretable, and fixed by pre-existing task semantics —
which is sufficient for the requested derivation.

## Branch 3 under R4

**Retained, but bound solely to exact focal-arm component invariance.** With no
normalizer in the gate, branch 3's normalizer limb is gone; the ruling gives an
R4 pair set, a per-limb aggregation, a global predicate, and the distinction
between a *missing* audit and *exact invariance*. One of my §6 guesses was
wrong: **"calibration disappears" is false if branch 4 remains** — Part-A must be
rederived at the five-unit equivalence, so calibration stays on the path.

## The scheduled action

**Freeze the full R4 contract around the five-unit absolute focal margin**,
including:

1. focal-arm component-invariance branch 3;
2. the five-unit Part-A equivalence test;
3. symmetric per-limb result semantics;
4. a **fresh evidence population** — mandatory;
5. an R4-specific expansion or no-expansion rule.

*"No implementation or environment compute is authorized by this review. D7.3 and
D8 remain blocked pending a valid R4 result."*

The R3 expansion rule **cannot carry forward**, and flex-only positive evidence
must be preserved by symmetric per-limb semantics.

## What R3 may and may not be cited for

Citable: the executed matched scalar observations; the topology and event-support
record; the artifact-derived `B_m` and `U*_m` distributions; failure to establish
a positive `B_m` lower bound on either limb; retirement of the signed
global-rotation normalizer as the R3 materiality scale; and the design risk that
the comparator is not demonstrated relevant to the focal effect.

**Not** citable for: an R4 five-unit result obtained by rethresholding the old
data; persistence necessity or its absence; flexible-renewal necessity; an
identified negative `B_m`; an identified ratio inversion; primary-`G` component
cancellation; or any natural-policy or algorithmic claim about R30 or D8.

The rethresholding prohibition is the one to keep in front of me: the R3 artifact
motivates the R4 design and **cannot become its confirmatory result.**
