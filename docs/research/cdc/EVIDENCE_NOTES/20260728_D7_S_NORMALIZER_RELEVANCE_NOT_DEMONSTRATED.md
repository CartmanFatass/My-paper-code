# Normalizer relevance is not demonstrated

> **CORRECTION, 2026-07-28, by External Pro's ruling on this very note.**
>
> This note was originally titled *"The normalizer is not weak — it is unrelated
> to the effect it was scaling"* and the body below still argues that. **That
> claim is not established and must not be quoted.** The association intervals
> encompass strong negative *and* positive relationships and the
> leave-one-topology-out estimates are unstable. The supported statement is
> `GLOBAL_ROTATION_NORMALIZER_RELEVANCE_NOT_DEMONSTRATED` — *relevance not
> demonstrated*, never *unrelated*. N5 moves the portfolio by prioritising
> focal-compatible scale design; it does not independently retire a comparator.
>
> Two further rows below are superseded. **The N1 row is discarded outright** —
> the classifier concatenated the stable and flex per-topology vectors and
> evaluated the combined vector against the stable-only interval and stable-only
> leave-one-out points, mixing two horizons and two causal classes. **N4
> "material" was overstated** — only `B_stable` has a nonzero adjusted ratio, and
> the accurate statement is *limited topology contribution for `B_stable`;
> topology-dominant variation not established for any quantity*. The
> stratify-or-expand recommendation is **not selected**.
>
> The sentinel result, the four standalone distributions in Section A, and the
> R4 decision are unaffected. The corrected run is `logs/d7s_autopsy_2/`.
>
> The body is preserved unedited below, because a claim the reviewer corrected is
> appended to, not erased.

First execution of the artifact-only normalizer-identifiability autopsy, the
action External Pro converged after D7.S audit run 2 returned
`PRIMARY_G_DEGENERATE`.

```text
script    = scripts/d7s_normalizer_autopsy.py
input     = logs/d7s_audit_2_30289161086/pooled/d7_s_event_aligned.json
            sha256 b087e67cfb799000...
output    = logs/d7s_autopsy_1/
bootstrap = iters 10000, seed 2026072601, quick_dev_run False
new data  = none. Zero environment compute.
```

## The sentinel passed, which is what makes the rest readable

All six fail-closed conditions held: artifact hash, contract id and procedure
version, the exact seed set `20260726`–`20260733`, `smoke=False`, the four
`topology_units` collections, and **exact reproduction of all six registered R3
bounds**.

That last one matters more than it looks. The Project Manager had reproduced
those bounds by hand to better than 1e-12 while writing the round question; Pro
required that check become an executable precondition rather than remain an
assertion made once. It is now the gate the analysis cannot start without.

## Section A — the standalone distributions

| artifact-derived | point | 5th pct | 95th pct | min | max | +/−/0 |
|---|---|---|---|---|---|---|
| `B_stable` | +0.180139 | −0.077367 | +0.416071 | −0.495793 | +0.534832 | 5/1/2 |
| `B_flex` | +4.288854 | −8.648833 | +14.102587 | −17.147505 | +19.027850 | 6/2/0 |
| `U*_stable` | +1.254074 | −2.203652 | +7.186347 | −5.205364 | +14.042137 | 4/4/0 |
| `U*_flex` | −4.122402 | −13.827640 | +3.371472 | −30.069646 | +7.395372 | 3/5/0 |

**Internal consistency, worth stating because it is free evidence:** the 5th
percentiles of the two `B_m` intervals are `−0.077367` and `−8.648833` — exactly
the one-sided LCBs the run recorded. The two-sided presentation is the same
bootstrap distribution R3 took its bounds from, not a re-derivation.

## The finding: N5

| Explanation | Verdict |
|---|---|
| N1 signed-normalizer failure | compatible (moderate) |
| N2 opposite source direction | not resolved |
| N3 component cancellation | `UNDISCRIMINATED_FROM_STORED_ARTIFACT` |
| N4 topology heterogeneity | material |
| **N5 comparator-scale mismatch** | **raised** |
| Selection instability | moderate |

**N5 is raised on an essentially absent association.** Per-topology paired
`(B_m, U*_m)`:

```text
stable   pearson +0.038   rank -0.180
flex     pearson +0.022   rank -0.333
```

`B_m` measures the benefit of *global proactive rotation versus none*. `U*_m`
measures a *focal one-Δ reassignment under reoptimized continuation*. Pro named
these as different interventions when it added N5; the measured association is
what that looks like empirically. The normalizer is not a weak version of the
effect — across topologies it carries close to no information about it, and what
little rank association exists points the wrong way.

That reframes the whole failure. `PRIMARY_G_DEGENERATE` reads as "the estimator
could not resolve." The autopsy says the denominator was arguably never the right
denominator, which is a design fault rather than a power fault — and it is
consistent with §9 having independently forbidden expansion.

## The rest, without inflation

- **N4 material, not dominant.** `max R_topology = 0.1221` — nonzero, well under
  0.5. Between-topology variation is real but does not swamp within-topology
  uncertainty. Per Pro's Modification 5 this **cannot** establish reproducible
  regimes with eight observed topologies and no permitted expansion, and no
  partition here is anything but exploratory.
- **N1 compatible, moderate tier.** `B_m` crosses zero and most topology-level
  `U*_m` share a sign, but the pooled `U*_m` interval still includes zero. The
  hierarchy was frozen before the output was looked at.
- **N2 not resolved.** Neither `U*` resolves in the direction N2 requires, so the
  source proposition is not shown to point the opposite way either.
- **N3 undiscriminated**, with the sentence Pro required: *primary-`G` component
  cancellation remains compatible with every scalar pattern observed in this
  autopsy.* It is not scored false, absent or lowered.
- **Selection instability moderate.** 39% (stable) and 37% (flex) of events have
  a leading candidate below 0.60 selection frequency. This qualifies why `U*`
  intervals are broad; it was not used to drop events or reselect candidates.

No explanation was forced to win. The script names no R4 scale and retires no
carrier — that disposition is Pro's at the next boundary.

## What this does not say

It does not validate the R3 execution path. Every number above is conditional on
that path being correct, and the back-half mutation sweep established the test
suite would not have detected several ways it could be wrong — including a halved
`g_total`. The autopsy inherits that conditional scope exactly as Pro said it
would, and cannot repair it: the component series that would allow independent
reconstruction were never persisted.
