# GPT-5.6 Pro Response — Lifetime Battery Contract Question

Received 2026-07-21. Archived verbatim as delivered. LaTeX markup was mangled
in transport; formulas are reconstructable from context and the numerical
values were independently reverified by the controller (see `DISPOSITION.md`).
No content is edited, reordered or summarized here.

---

Verdict
The concern is valid. Keep the primary mechanism-matched estimand
[
G=U_{\mathrm{EHC}}-U_{\mathrm{DUMMY}},
]
but revise the behavioral battery before launch. As written, it does not adequately distinguish learned, context-sensitive commitment use from stochastic event usage plus an active mark-to-logit link. That distinction matters because the project requires learned lifetime behavior under the declared clock contract, not merely varied durations, label use, or predictability.
1. Is `CV(T) >= 0.408` by construction?
Under the model stated in the concern, yes. Under the actual general learned policy class, not universally.
Let the exogenous opportunity gaps be IID:
[
\Delta\sim\operatorname{Uniform}{4,8,12}.
]
Then
[
\mu_\Delta=8,\qquad
\sigma_\Delta^2=\frac{32}{3},\qquad
\frac{\sigma_\Delta^2}{\mu_\Delta^2}=\frac16.
]
If the policy renews independently at each opportunity with constant probability (p), then
[
K\sim\operatorname{Geometric}(p),\qquad
T=\sum_{j=1}^{K}\Delta_j.
]
The compound-sum variance gives
[
CV^2(T)
1-\frac56p.
]
Consequently,
[
CV(T)\ge\sqrt{\frac16}\approx0.408248,
]
with equality at (p=1), meaning always RENEW. For (p=0.5),
[
CV(T)=\sqrt{\frac7{12}}\approx0.763763.
]
So both an always-renew policy and an untrained approximately uniform event head pass the proposed `CV(T) > 0.25` gate for reasons supplied entirely or mostly by the exogenous gap distribution.
The duration-bin gate has the same defect. Under always RENEW, (T\in{4,8,12}), so:

```text
P(T in [1,8])  = 2/3
P(T in [9,16]) = 1/3

```

Two bins exceed `0.10` without a single learned KEEP decision.
The qualification is that a real recurrent policy need not generate geometric (K). It can condition on age and prior gaps. For example, a policy that always renews after exactly three gaps has
[
CV(T)
\frac{\sqrt{3(32/3)}}{3\cdot8}
\frac{\sqrt{32}}{24}
\approx0.236,
]
so `CV(T) >= 0.408 for every possible policy` is not literally true. But the central objection remains decisive: the registered `0.25` threshold is readily passed by trivial policies because it mixes policy timing with exogenous gap variance.
2. Does the current battery discriminate learned commitment behavior?
Not sufficiently for the `COMMITMENT_SUPPORTED` versus `REPRESENTATION_ONLY` distinction.
KEEP/RENEW rates
On non-CREATE opportunities,
[
P(\mathrm{KEEP})+P(\mathrm{RENEW})=1.
]
The two gates merely constrain
[
0.10<P(\mathrm{RENEW})<0.80.
]
A uniform random head passes comfortably. These are useful support/non-collapse checks, but not evidence that the policy selects different lifetimes for causal reasons.
`CV(T)` and physical-time bins
These report realized physical duration, but that duration is a convolution of:

1. the learned KEEP/RENEW sequence; and
2. the exogenous draws from `{4,8,12}`.

They therefore cannot attribute dispersion to learned individual-lifetime control.
Logit-residual norm
The current intervention
[
\frac{\lVert W_z(z-z_{\mathrm{perm}})\rVert_2}{\sqrt3}
]
does not necessarily measure a change in action behavior.
For example, a residual proportional to
[
(c,c,c)
]
has positive norm but leaves the three-action softmax distribution exactly unchanged. Large residuals can also have little practical effect when the base logits dominate or the policy is saturated. The metric establishes parameter-path magnitude, not executable behavioral consequence.
What (G) does establish
A positive, material EHC-minus-DUMMY utility effect remains strong evidence that enabling the commitment-to-primitive link changes external performance, assuming DUMMY is otherwise identical in event computation, RNG consumption, optimizer ownership, and control flow.
But (G) alone does not show that the gain arose from learned heterogeneous commitment durations. It could arise from a useful extra low-frequency representation with arbitrary or nearly random renewal timing.
Thus the current battery can establish:

```text
event head not collapsed
+ physical spell durations are dispersed
+ mark link has nonzero parameter magnitude
+ link improves arm-level utility

```

It cannot establish:

```text
the policy learned when to KEEP and when to RENEW
+ the resulting lifetime heterogeneity is policy-generated
+ natural event decisions have beneficial consequences

```

3. Minimal replacement
The proposed move from (T) to (K) is necessary but not sufficient.
Define, for each complete uncensored commitment spell,
[
K
1+#{\text{KEEP decisions before its terminating RENEW}}.
]
Equivalently, (K) is the number of exogenous opportunity intervals contained in the spell. It is policy-determined:

```text
RENEW at first later opportunity       -> K = 1
KEEP, then RENEW                       -> K = 2
KEEP, KEEP, then RENEW                 -> K = 3
...

```

Temporary absence contributes neither a gap nor active duration. Spells censored by terminal LEAVE or episode termination are excluded from complete-spell (K) statistics and reported separately.
However, a raw `CV(K)` gate is still insufficient. A memoryless random head with (p_{\rm renew}=0.5) has
[
CV(K)=\sqrt{1-p}=\sqrt{0.5}\approx0.707,
]
so it would again look "heterogeneous." The correction must combine policy-determined lifetime support with natural consequential selection.
Replacement A — reclassify usage gates as support only
Retain KEEP and RENEW counts solely to establish estimability:

```text
at least 128 eligible natural KEEP rows
at least 128 eligible natural RENEW rows

```

or an equivalent pre-registered minimum count.
Do not use `P_KEEP` or `P_RENEW` as scientific evidence of learned commitment. Their point estimates remain diagnostic.
Replacement B — use (K), not (T), for lifetime support
Replace physical-time `CV(T)` and the physical bins with:

```text
K bins:
  K = 1
  K = 2
  K >= 3

```

Require at least two bins to have cluster-bootstrap LCB above `0.10`.
This shows that the natural policy actually realizes more than one opportunity-count lifetime. It still does not by itself prove usefulness, so it must be paired with the next gate.
Keep (T), `CV(T)`, and physical-time bins as descriptive outputs only.
Replacement C — natural event-decision consequence
At each eligible held-out non-CREATE opportunity, fork the exact simulator snapshot into two common-randomness branches:

```text
KEEP branch:
  retain current z

RENEW branch:
  apply the same pre-sampled candidate renew mark z_candidate

```

To make this defined for natural KEEP rows, generate and store a candidate renew mark at every eligible opportunity before categorical action selection. Its density enters the behavior likelihood only when RENEW is selected.
Both branches retain identical:

* future demand and membership ledger;
* future opportunity gaps;
* primitive-order tables;
* policy-action random-number tables;
* frozen final policy parameters.

Run both branches to episode termination and compute the unchanged external utility (U).
For a naturally selected KEEP row:
[
A_{\mathrm{KEEP}}
U(\mathrm{KEEP})
U(\mathrm{RENEW}(z_{\mathrm{candidate}})).
]
For a naturally selected RENEW row:
[
A_{\mathrm{RENEW}}
U(\mathrm{RENEW}(z_{\mathrm{candidate}}))
U(\mathrm{KEEP}).
]
Cluster by original sign-paired base episode, not by event row.
A defensible preregistered gate is:
[
LCB_{95}(A_{\mathrm{KEEP}})>0,
]
[
LCB_{95}(A_{\mathrm{RENEW}})>0,
]
with a material point-estimate floor such as
[
\operatorname{mean}(A_{\mathrm{KEEP}})\ge0.02,
\qquad
\operatorname{mean}(A_{\mathrm{RENEW}})\ge0.02.
]
This tests the actual claim: the natural policy uses longer and shorter commitment spells in different states, and both choices improve external consequence relative to the legal alternative.
A random nondegenerate event head can pass the support and (K)-spread checks, but should not systematically select the better counterfactual branch in both directions.
Replacement D — intervene on the action distribution, not raw logits
Replace
[
\frac{\lVert W_z(z-z_{\mathrm{perm}})\rVert_2}{\sqrt3}
]
with same-snapshot primitive-policy total variation:
[
I_{\mathrm{TV}}
\mathbb E
\left[
\frac12
\sum_a
\left|
\pi_a(a\mid o,h,z)
\pi_a(a\mid o,h,z_{\mathrm{perm}})
\right|
\right].
]
Use derangements within the same held-out lifecycle/event stratum, with observation, recurrent hidden state, action mask, active-set context, and primitive prefix held fixed.
A material gate can retain the existing numerical scale:
[
LCB_{95}(I_{\mathrm{TV}})>0.10.
]
This is invariant to softmax-common logit shifts and directly measures executable action-distribution dependence. It remains an intervention diagnostic, not standalone proof of usefulness; usefulness is supplied by (G) and the natural counterfactual event advantages.
Revised branch boundary
`COMMITMENT_SUPPORTED` should require all of:

1. External mechanism value

[
LCB_{95}(U_{\mathrm{EHC}}-U_{\mathrm{DUMMY}})>0.10.
]

2. Natural support

Both KEEP and RENEW have the registered minimum eligible counts.

3. Policy-generated lifetime realization

At least two (K) bins have LCB above `0.10`.

4. Natural consequential timing

[
LCB_{95}(A_{\mathrm{KEEP}})>0,
\qquad
LCB_{95}(A_{\mathrm{RENEW}})>0,
]
plus the frozen material point floors.

5. Executable mark dependence

[
LCB_{95}(I_{\mathrm{TV}})>0.10.
]
`REPRESENTATION_ONLY` should receive the valid pattern:

```text
G passes
but either:
  natural KEEP/RENEW counterfactual advantage fails,
  K support fails,
  or actual action-TV intervention fails

```

This means the link has external value but the registered evidence does not establish learned event-held lifetime semantics.
`ORDINARY_OR_CAPACITY_EXPLANATION_SUPPORTED` remains the branch where EHC does not materially beat the mechanism-matched DUMMY/capacity controls.
Bottom line

1. The `0.408` calculation is correct for IID gaps plus a constant-hazard geometric renewal policy, but not as a universal lower bound over all recurrent policies.
2. The existing battery does not adequately discriminate learned commitment timing. It mainly tests non-collapse, exogenously contaminated duration spread, and parameter-path magnitude.
3. Conditioning on (K) is the right first correction, but `CV(K)` alone is still passed by random policies. The minimal defensible replacement is:
   * (K)-based lifetime support;
   * action-distribution TV rather than logit norm;
   * paired natural KEEP-versus-RENEW external counterfactual advantage.

Because no result has been observed, making this correction now is a legitimate preregistration repair rather than a post-result rescue.
