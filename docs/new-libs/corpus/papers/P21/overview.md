# Large Population Stochastic Dynamic Games: Closed-Loop McKean-Vlasov Systems and the Nash Certainty Equivalence Principle

## Identity and scope

This 2006 journal article is a foundational large-population stochastic-game treatment using closed-loop McKean-Vlasov systems and the Nash certainty equivalence principle for multi-class weakly coupled agents. (PDF pages 1-3)

## Problem formulation

n controlled diffusions are weakly coupled through empirical averages in dynamics and cost; agents know their own state/dynamic class and limiting population statistics, and seek decentralized feedback controls. (PDF pages 4-7)

## Actual contribution

The NCE methodology decomposes the game into an HJB optimal-control problem for a representative agent and a closed-loop McKean-Vlasov equation, tied by a fixed-point consistency condition between assumed and induced measure flows. (PDF pages 3; 7-22)

## Core objects and equations

Core objects are multi-class empirical distributions, measure flows, HJB value functions, best-response map, measure-flow inducing map, McKean-Vlasov dynamics, Wasserstein/Vasershtein metric, composite gain, and epsilon-Nash deviation cost. (PDF pages 7-24)

## Algorithms or mechanism primitives

The reusable synthesis primitive is solve HJB under a candidate population measure, apply the resulting class-dependent Lipschitz feedback in the McKean-Vlasov system, and seek a fixed point where induced and assumed measures agree. (PDF pages 9-22)

## Assumptions and information structure

H0 fixes convergence of class proportions; H1-H6 impose compact controls, bounded/Lipschitz dynamics and cost, smoothness, a unique regular best response, regular measure flows, and Lipschitz feedback. The NCE fixed point additionally uses a composite-gain condition. (PDF pages 7; 10-22)

## Theorems and guarantees

Theorem 5 gives a unique bounded classical HJB solution under H1-H4; Theorem 6 gives a unique consistent McKean-Vlasov pair under H1-H6; Theorem 10 gives NCE existence/uniqueness when c1c2<1; Theorem 12 gives O(n^-1/2+epsilon_n) decoupling; Theorem 13 and Corollary 14 give asymptotic epsilon-Nash conclusions under their stated strategy/model restrictions. (PDF pages 13; 16; 22; 24-29)

## Experiments and evaluation protocol

There is no numerical experiment. Evidence consists of stochastic-control existence proofs, fixed-point arguments, propagation/decoupling estimates, and asymptotic equilibrium analysis. (PDF pages 10-29)

## Failure boundaries and non-claims

The variable population is an asymptotic model with weak coupling and regularity/gain assumptions, not a learned-policy held-out-N benchmark; Theorem 13 initially restricts deviations to decentralized feedback, while Corollary 14 broadens the strategy space only for additional decomposable structure. (PDF pages 23-29)

## HMASD prospective connections

Curator connection (prospective): the empirical-measure interface and O(n^-1/2+epsilon_n) error form a principled variable-N abstraction for homogeneous/multi-class UAV teams when weak coupling and exchangeability are credible. (PDF pages 7; 24-29)

Curator connection (prospective): use the NCE fixed point as a model-based comparator or design prior, not as evidence that a neural MARL policy generalizes across N. (PDF pages 9-22)

## Recommended reading route

Read the NCE decomposition and population assumption, then H1-H6 and Theorems 5/6/10, and finish with Theorems 12-13 and Corollary 14 for finite-population meaning. (PDF pages 3; 7-29)

## Source-page anchors

Finite game and NCE construction are on pages 4-9, assumptions on pages 10-14, McKean-Vlasov/fixed-point results on pages 14-22, and finite-n epsilon-Nash analysis on pages 23-29. (PDF pages 4-29)
