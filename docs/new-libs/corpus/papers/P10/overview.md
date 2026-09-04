# P10 — Policy Mirror Ascent for Efficient and Independent Learning in Mean Field Games

## Identity and scope

- An ICML 2023 theory paper showing policy mirror ascent can learn a regularized mean-field-game equilibrium from a single finite-N trajectory without a population generative model (PDF pp. 1–9).

## Problem formulation

- N symmetric agents generate an empirical population state while each follows a Markov policy; the target is a regularized MFG Nash equilibrium under contractive population/policy operators (PDF pp. 3–6).

## Actual contribution

- The paper constructs a contractive PMA operator, analyzes conditional TD under evolving population samples, and derives centralized and independent finite-sample guarantees with an O(N^{-1/2}) mean-field term (PDF pp. 4–9).

## Core objects and equations

- Core objects are population update Γ_pop, Q/policy improvement maps, regularizer h, the PMA fixed-point operator Γ_η, conditional TD operator, and empirical-population deviation (PDF pp. 3–8).

## Algorithms or mechanism primitives

- Algorithm 1 performs conditional TD while waiting for population mixing; Algorithms 2–3 alternate value estimation with simultaneous PMA updates in centralized or independent forms (PDF pp. 7–9, 29–32).

## Assumptions and information structure

- Results require finite state/action spaces, strong concavity/regularization, contractivity, persistence of excitation, mixing, Lipschitz population dynamics, and policies bounded away from zero (PDF pp. 3–8, 23–32).

## Theorems and guarantees

- Theorem 4.2 controls CTD error with O(N^{-1/2}) population bias; Theorems 4.3 and 4.5 give centralized and independent sample guarantees, with the centralized rate O(ε^{-2} log²(1/ε)) up to approximation terms (PDF pp. 7–9).

## Experiments and evaluation protocol

- The paper is primarily theoretical and does not present a task benchmark section; evidence is theorem/proof based (PDF pp. 1–9, 12–33).

## Failure boundaries and non-claims

- The O(N^{-1/2}) term is a finite-population approximation under symmetry/mixing and is not evidence that one frozen learned policy generalizes to held-out N or churn (PDF pp. 7–9).

## HMASD prospective connections

- The single-trajectory, independent update is a strong candidate ingredient for variable-roster learning, but HMASD would need explicit shared parameterization and cross-N deployment tests (PDF pp. 6–9).

## Recommended reading route

- Read the MFG/PMA operators on pp. 3–6, CTD and Theorem 4.2 on pp. 7–8, centralized/independent theorems on pp. 8–9, then explicit constants in pp. 23–32.

## Source-page anchors

- MFG model (PDF pp. 3–4); PMA contraction (pp. 4–6); conditional TD (pp. 6–8); centralized/independent guarantees (pp. 8–9); proofs (pp. 23–33).
