# Dual Extrapolation and Its Applications to Solving Variational Inequalities and Related Problems

## Identity and scope

This is the August 2003 CORE working paper underlying the later 2007 Mathematical Programming article; its pagination and typesetting differ from the journal version. (PDF pages 1-3)

## Problem formulation

Given a continuous monotone operator g on a closed convex set Q, the target is a variational-inequality solution, measured through a restricted merit function built from a strongly convex prox function and Bregman distance. (PDF pages 4-8)

## Actual contribution

The paper introduces a one-level, norm-adjustable dual extrapolation update and derives optimal-order oracle complexities for Lipschitz monotone and bounded-variation operators, with applications to nonsmooth minimization, saddle points, and matrix games. (PDF pages 1-3; 8-20)

## Core objects and equations

Core objects are weak/strong variational inequalities (2.1)-(2.2), strongly convex prox d, conjugate d*_Q, Bregman distance omega, restricted merit f_D, dual model s, prox map, and averaged iterates. (PDF pages 4-9)

## Algorithms or mechanism primitives

Each dual extrapolation step evaluates two prox-like points and updates one accumulated dual linear model; step-size/prox scaling changes between Lipschitz and bounded-variation regimes. (PDF pages 6-11)

## Assumptions and information structure

Guarantees require monotonicity, continuity, a closed convex feasible set, a differentiable strongly convex prox on the relevant image, and either a known Lipschitz constant or a bounded-variation constant; saddle-point results add convex-concave smoothness/scaling conditions. (PDF pages 4-16)

## Theorems and guarantees

Theorem 2 gives f_D of the averaged iterate at most LD/[sigma(k+1)] and O(1/epsilon) iterations for Lipschitz operators; Theorem 3 gives O(1/sqrt(k)) merit and O(1/epsilon^2) iterations for bounded variation; Theorem 6 specializes an O(1/(k+1)) saddle-gap bound to bilinear matrix games. (PDF pages 9-11; 19-20)

## Experiments and evaluation protocol

There are no numerical experiments. Evidence is a chain of lemmas, complexity bounds, and explicit algorithm specialization to convex-concave and bilinear problems. (PDF pages 4-21)

## Failure boundaries and non-claims

These guarantees are for monotone variational inequalities and convex-concave saddle structure; they do not imply convergence in nonmonotone or generic nonconvex MARL games. (PDF pages 2-4; 12-20)

## HMASD prospective connections

Curator connection (prospective): dual extrapolation is a candidate optimization primitive when an HMASD learning subproblem can be justified as a monotone VI; monotonicity and oracle access are discriminator assumptions, not defaults. (PDF pages 4-11)

## Recommended reading route

Read the VI/prox setup and Lemma 5/Theorem 1, then the two algorithmic schemes and rates; use the saddle-point and matrix-game sections for implementation geometry. (PDF pages 4-11; 12-20)

## Source-page anchors

VI and Bregman definitions are on pages 4-6, the extrapolation inequality on page 8, rates on pages 9-11, saddle-point scaling on pages 12-16, and matrix-game algorithm/rate on pages 16-20. (PDF pages 4-20)
