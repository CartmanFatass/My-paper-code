# VQFP proof-sized variable-N physical-association gate R01 — 2026-08-29

## Material-cycle freeze

- Direction: `voronoi_quadrature_field_policy`
- Cycle: `2026-08-29.8-portfolio-vqfp-proof-gate-01`
- Object: `VQFP-PROOF-SIZED-ASSOCIATION-GATE-R01`
- Baseline: `b3915fbc59d8fe3171fd1e70f72acad9be9c2acf`
- Workflow revision: `2026-08-29.8`
- State at freeze: `WORKING`, before any object result, coefficient selection, exact enumeration, CM dispatch, or provider response

This is a fresh material cycle. It asks whether the retained VQFP analytic primitives admit a
proof-sized exact association-value discriminator before the historical VNPA R03 construction. It
does not resume, relabel, subset, or partially execute R03. R03 remains provenance and supplies only
the proved finite class `G`, exact measure and oracle lemmas, legal action law, treatment/FREE forms,
control meanings, and causal reassociation semantics.

## Question, non-goals, and decision use

Can the smallest member of the prospective finite ladder below preserve, at both held-out roster
sizes, all of these relations at the registered margins?

1. the exact integer oracle has native command and utility headroom over equal allocation;
2. one roster-independent treatment selected without held-out rows beats every frozen generic
   nonoracle control and is noninferior to a competent same-information residual FREE comparator;
3. the same selected treatment loses value when only its physical-measure association is
   half-cycle reassociated on support-matched rows.

A surviving member can justify a fresh isolated CM observation and may support `CONTINUE` toward a
broader scientific object. Failure is classified narrowly. A finite-ladder null closes the cheap
route unless the failure is a structural containment or causal impossibility that also reaches the
larger R03 question.

The cycle cannot establish arbitrary geometry or roster size, in-episode join/leave robustness,
jointly reoptimized eight-dimensional FREE noninferiority, repeated-training efficacy, 2-D or UAV
transfer, safety, deployment, physical-measure necessity, or broad MARL superiority. MGTAP supplies
only sample-split, matched-support, and fail-closed methodology; its result polarity does not enter.

## Exact finite object grammar

Use `N_train={4,8}`, `N_heldout={6,12}`, `Q=120`, `h=1/600`, and one exact decision step per row.
For every row, the physical endpoint is

```text
U(n)=sum_i m_i v_i/(v_i+n_i/600),     Z(n)=1-U(n),
```

with legal nonnegative integer `n` satisfying `sum_i n_i=120`. `LR` and the exact global marginal
oracle are exactly those proved for analytic class `G`.

The six equally weighted field rows are the registered states

```text
(beta,gamma) in {(-1/4,0),(-1/4,1/4),(0,0),(0,1/4),(1/4,0),(1/4,1/4)},
f(x)=1+beta(2x-1)+gamma(6x(1-x)-1).
```

For `alpha` in `{1/4,1/2,3/4}`, begin from uniform sites
`x_i=(2i-1)/(2N)`. At `N=4`, replace only `x_2` by `x_2+alpha/N`. At
`N in {6,8,12}`, replace `x_2` by `x_2+alpha/N` and
`x_(2+N/2)` by `x_(2+N/2)-alpha/N`. The resulting sites lie on the
`1/(384N)` grid. Their normalized cell lengths are uniform except for two half-cycle-paired high/low
pairs when `N>4`, or one pair when `N=4`; all cells lie in
`[5/(8N),11/(8N)]`, so every row belongs to proved `G`.

The prospective smallest-first ladder is fixed before results:

1. `K1={3/4}`: six field rows per roster;
2. `K2={1/2,3/4}`: twelve field rows per roster;
3. `K3={1/4,1/2,3/4}`: eighteen field rows per roster.

Each member is a complete deterministic object. Test in this order and stop at the first complete
pass. A failed smaller member is retained; it is not erased by a larger pass. This is a finite
existence search, not sampling inference or post-result population selection.

Let `C={-4,-3,-2,-1,0,1,2,3,4}` and `Theta=Phi=C^4`. For every row define

```text
d_i=m_i/v_i,  dbar=(1/N)sum_i d_i,
q_i=theta_0+theta_1 d_i+theta_2 dbar+theta_3(d_i-dbar)^2,
B_i=1+q_i^2,
w_i^T=v_i B_i,
n^T=LR(w^T).
```

Select one `theta_T` by exact maximum mean `Z` over all rows of the current ladder member at
`N={4,8}`. Ties use lexicographically increasing coefficient tuple. The same `theta_T` is then fixed
for every FREE candidate and held-out row.

FREE receives the same row information and an exhaustive matched set of exactly `|Phi|=|Theta|`
coefficient tuples. For `phi in Phi`,

```text
z_i=Nv_i-1,
r_i=clip[-1/2,1/2](phi_0+phi_1(d_i-dbar)+phi_2 z_i+phi_3(d_i-dbar)z_i),
w_i^F=v_i B_i(1+r_i)^2,
n^F=LR(w^F).
```

Select `phi_F` by the identical exact training mean and tie law. `phi=0` is included and reproduces
treatment exactly. This is conditional residual FREE competence, not a claim about joint
eight-dimensional reoptimization.

## Controls, reassociation, and estimands

On every identical physical row, evaluate:

- `EQ`: `n_i=Q/N`;
- `DENS`: `LR(d_i)`;
- `MASS`: `LR(m_i)`;
- `MARG0`: `LR(m_i/(600v_i+1))`;
- `ORACLE`: the exact first 120 diminishing marginal records;
- `T-P`: replace each occurrence of `v_i` in the treatment weight only by
  `lambda_i=v_(1+((i-1+N/2) mod N))`, without retraining.

`T-P` preserves sites, physical endpoint cells, `m_i`, `d_i`, `dbar`, coefficient identity, command
coordinates, and LR tie keys. The half-cycle map swaps each constructed high cell with a low cell
and preserves the complete length multiset. This is the sole treatment intervention.

For arm `p`, roster `N`, and ladder member `K`, let `J_p,N,K` be exact mean `Z` over its rows. Define

```text
H_K=min_N (J_ORACLE,N,K-J_EQ,N,K),
V_K=min_N min_b (J_T,N,K-J_b,N,K),       b in {EQ,DENS,MASS,MARG0},
F_K=min_N (J_T,N,K-J_FREE,N,K),
A_K=min_N (J_T,N,K-J_T-P,N,K).
```

The frozen margins are `delta=1/500` and `nu=1/1000`. A member survives only if

```text
H_K >= delta,  V_K >= delta,  F_K >= -nu,  A_K >= delta.
```

In addition, for each held-out roster at least `ceil(rows/4)` rows must contain an exact
`ORACLE != EQ` command witness with strict oracle utility improvement, and at least the same count
must contain `T != T-P` with strict treatment utility improvement. Exact equality or LR aliasing
does not count.

## Competing explanations and branch meanings

The strongest simple null is generic separable diminishing-return allocation: `MASS`, `DENS`,
`MARG0`, or conditional residual FREE matches or improves the treatment once work and information
are competent. Other live explanations are integer LR aliasing, geometry-only tuning, coefficient
regularization, and insufficient oracle-versus-EQ support.

Terminal scientific classifications are kept distinct:

- `NO_PROOF_SIZED_CANDIDATE`: all three ladder members complete and none passes, without a broader
  structural theorem; this closes only this cheap deterministic route.
- `GENERIC_FREE_ABSORPTION`: competent conditional residual FREE defeats noninferiority. It reaches
  the full VQFP case only if a separate exact argument covers the larger treatment/comparator class.
- `CAUSAL_REASSOCIATION_FAILURE`: the support-matched half-cycle cut does not change commands or
  value at the gate; this invalidates this gate, not physical association in arbitrary hosts.
- `SURVIVING_EXACT_CANDIDATE`: the smallest passing ladder member satisfies every relation and may
  be frozen for one isolated CM observation.
- `TECHNICAL_NONOBSERVATION`: the exact object was not validly evaluated; it supplies no science.

Absence of oracle headroom or superiority over a frozen generic control is recorded directly and
cannot be relabelled as transport or engineering failure.

## Search, consultation, resource, and stop boundary

Before any CM request, use at most three read-only local scientific routes: one construction or
counterexample route, one principles/causal audit, and one exact-mathematics check if a material
premise remains. In parallel, obtain one fresh GPT-5.6 Pro Innovator response from a new provider
conversation. No route receives another route's answer. The EM then either stops on a proved
scope-invalidating defect or writes one synthesis packet.

No RNG, bootstrap, stochastic rollout, historical R03 candidate, R03 episode, R03 operation, or R03
partial panel is permitted. No source, test, or result command is authorized by this card. If and
only if the frozen ladder remains meaning-preserving and one exact executable observation can change
`CONTINUE/NARROW/PARK`, the EM may commit this authority, transfer the writer, and create one fresh
CM task with a new isolated VQFP proof-gate source/test namespace. The exact member, command, paths,
resources, observer, branches, and claim ceiling must be frozen before that CM sees a result.

After a valid synthesis, obtain a fresh, conclusion-blind GPT-5.6 Pro Convergence response in a new
provider conversation. Transport failure changes evidence availability only. No terminal EM result
is returned while any leaf, CM, or provider operation remains live.

## Current claim ceiling

At freeze, the only claim is that a prospective, finite, result-blind discriminator has been
defined. A later positive can establish only existence of exact association value for the selected
treatment on the smallest passing deterministic ladder member under its exact coefficient sets,
controls, legal action law, and margins. A later bounded negative can close only the specified
ladder unless accompanied by a broader structural proof.
