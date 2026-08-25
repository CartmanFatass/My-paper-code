# Independent Natural Policy Gradient Methods for Potential Games: Finite-Time Global Convergence with Entropy Regularization

## Identity and scope

This is arXiv:2204.05466v2, a 2022 preprint on independent entropy-regularized NPG for finite static potential games; it explicitly leaves Markov potential games to future work. (PDF pages 1-3; 11)

## Problem formulation

Agents in a finite normal-form potential game use product policies; adding each agent's Shannon entropy creates a regularized potential game whose target is a quantal response equilibrium (QRE). (PDF pages 4-5)

## Actual contribution

The paper supplies finite-time average-gap guarantees for decentralized multiplicative NPG updates, action-space-independent rates up to logarithms, sublinear dependence on agent count, and a smoothing route to approximate Nash equilibrium. (PDF pages 1-2; 6-7)

## Core objects and equations

Core objects are exact potential differences, marginalized utility, entropy-regularized utility/potential, QRE fixed point, softmax/Fisher NPG, Jeffrey and KL divergences, and QRE-gap/NE-gap. (PDF pages 3-8)

## Algorithms or mechanism primitives

Algorithm 1 initializes uniform policies and updates all agents in parallel via pi_i^{t+1}(a) proportional to pi_i^t(a)^(1-eta tau) exp(eta r_i^t(a)), using each agent's marginalized utility. (PDF page 6)

## Assumptions and information structure

The analysis assumes a finite static exact-potential game, product policies, access to marginalized utilities, uniform initialization for the corollary, positive entropy regularization, and the stated upper bound on step size. (PDF pages 4-7)

## Theorems and guarantees

Theorem 3.1 bounds the average QRE gap; Corollary 3.2 gives O(min{sqrt(N),Phi_max} Phi_max/(tau^2 epsilon^2)) iterations for an epsilon-QRE, and the smoothing argument yields a tilde-O(min{sqrt(N),Phi_max} Phi_max/epsilon^4) average NE-gap bound. (PDF page 7)

## Experiments and evaluation protocol

Synthetic experiments use N=4, |A|=20, independently sampled Beta(1/2,1/2) potential values, 10 independent runs, and comparisons between direct-parameter PG and NPG under several entropy values over 30,000 iterations. (PDF pages 10-11)

## Failure boundaries and non-claims

The general rate is sublinear, not linear, and the dimension-free statement applies to identical-interest games with bounded potential, not arbitrary potential or Markov games. (PDF pages 2; 7; 11)

Curator boundary: dependence of a complexity bound on N is not evidence that one learned policy transfers across held-out roster sizes. (PDF pages 2; 7)

## HMASD prospective connections

Curator connection (prospective): entropy smoothing and decentralized multiplicative updates are candidate coordination primitives for an HMASD static decision layer, with Markov extension and variable-roster transfer still needing separate evidence. (PDF pages 6-7; 11)

## Recommended reading route

Read the scope caveat and contributions, then the potential/QRE definitions, Algorithm 1 and Theorem 3.1/Corollary 3.2, and finally the synthetic protocol and open Markov extension. (PDF pages 1-7; 10-11)

## Source-page anchors

Scope and rates are on pages 1-2, definitions on pages 4-5, algorithm and theorem on pages 6-7, proof sketch on pages 8-10, and experiments/conclusion on pages 10-11. (PDF pages 1-11)
