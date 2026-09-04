# Recommended reading paths

These routes are ordered for comprehension, not prestige. Each link opens a
corpus overview; follow its page anchors to source chunks and PDFs.

## 1. MARL and decentralized decision foundations

1. [P01 - What question is multi-agent learning answering?](papers/P01/overview.md)
2. [B01 - MARL foundations and modern approaches](papers/B01/overview.md)
3. [B02 - Algorithmic, game-theoretic, and logical foundations](papers/B02/overview.md)
4. [B03 - Dec-POMDP information structure](papers/B03/overview.md)

Use this route to distinguish learning in a multi-agent environment, learning
equilibria, cooperative planning under local information, and centralized
training/decentralized execution. Do not assume a fixed-agent formalism covers
entry, exit, or held-out rosters.

## 2. Large populations, mean field, and variable `N`

1. [P21 - Large-population stochastic dynamic games](papers/P21/overview.md)
2. [P08 - Mean-field MARL](papers/P08/overview.md)
3. [P09 - Model-free mean-field reinforcement learning](papers/P09/overview.md)
4. [P14 - Cooperative MARL/mean-field-control approximation and Q-learning](papers/P14/overview.md)
5. [P10 - Independent policy mirror ascent in mean-field games](papers/P10/overview.md)
6. [P12 - Graphon mean-field control for nonuniform dense interactions](papers/P12/overview.md)
7. [P22 - Accuracy of graphon particle approximations](papers/P22/overview.md)
8. [P24 - Non-stationary continuous mean-field games](papers/P24/overview.md)

Read P14 for the strongest homogeneous cooperative finite-`N` approximation in
this library. Read P12 for structured dense heterogeneity. Read P22 to see why
an `O(1/N)` particle-system statement cannot replace an MFC policy theorem.
Every HMASD use still needs direct frozen-policy held-out-`N` evaluation.

## 3. Communication, information, and coordinated exploration

1. [B03 - Local histories and decentralized information](papers/B03/overview.md)
2. [P15 - Information-bottleneck communication](papers/P15/overview.md)
3. [P17 - Episode-persistent latent exploration modes](papers/P17/overview.md)
4. [P16 - Sequential multi-agent trust-region updates](papers/P16/overview.md)

P15 supports a bandwidth/usefulness tradeoff but not semantic deduplication or
conditional information sufficiency. P17 addresses committed exploratory modes,
not externally changed skill duration.

## 4. Potential games and independent policy optimization

1. [B02 - Game-theoretic foundation](papers/B02/overview.md)
2. [P02 - Independent natural policy gradient in Markov potential games](papers/P02/overview.md)
3. [P03 - Independent policy gradient for large-scale Markov potential games](papers/P03/overview.md)
4. [P13 - Entropy-regularized natural policy gradient and QRE](papers/P13/overview.md)

The structural potential-game assumptions are essential. “Independent” here
does not mean the theorem applies to arbitrary general-sum MARL, and
“large-scale” does not mean one learned policy transports across `N`.

## 5. Rotational dynamics and variational inequalities

1. [P04 - Cycles and spurious equilibria in hidden bilinear games](papers/P04/overview.md)
2. [P05 - Dual extrapolation for variational inequalities](papers/P05/overview.md)
3. [P06 - Rotational learning dynamics in MARL](papers/P06/overview.md)
4. [P07 - Stochastic variance-reduced/verified VI method](papers/P07/overview.md)

Separate classical monotone-VI guarantees from later MARL adaptations. P07 is
a recent preprint and should not be treated as settled general MARL doctrine.

## 6. Sample complexity and function approximation

1. [P19 - Finite-time Q-learning rates](papers/P19/overview.md)
2. [P25 - The exploiter approach in large-state Markov games](papers/P25/overview.md)
3. [P20 - Independent linear function approximation in Markov games](papers/P20/overview.md)
4. [P11 - Model-based learning in mean-field games](papers/P11/overview.md)

Check whether each result concerns single-agent MDPs, two-player zero-sum games,
general Markov games, or mean-field games before transferring its sample-
complexity language.

## 7. Optimal transport as a prospective MARL ingredient

1. [P18 - Optimal transport and MARL position paper](papers/P18/overview.md)
2. [P12 - Graphon population structure](papers/P12/overview.md)
3. [P24 - Continuous non-stationary mean-field dynamics](papers/P24/overview.md)

P18 is primarily conceptual. Use it to generate testable mechanisms or metrics,
not as evidence that Wasserstein objectives improve a MARL policy.

## 8. Fast route for an HMASD variable-axis proposal

1. [B01](papers/B01/overview.md) for shared-policy and homogeneity boundaries.
2. [B03](papers/B03/overview.md) for deployable information structure.
3. [P14](papers/P14/overview.md) for homogeneous variable-population theory.
4. [P12](papers/P12/overview.md) for structured nonuniform populations.
5. [P15](papers/P15/overview.md) for communication compression boundaries.
6. [P17](papers/P17/overview.md) for the nearest but non-equivalent temporal-
   commitment mechanism.

Then consult [`NAV_BY_HMASD_AXIS.md`](NAV_BY_HMASD_AXIS.md) and require a direct
held-out axis experiment rather than treating any of these sources as the
missing project result.
