# P20 — Refined Sample Complexity for Markov Games with Independent Linear Function Approximation

## Identity and scope

- A COLT 2024 theory paper for multi-player general-sum Markov games with independent linear function approximation, targeting sample-efficient Markov coarse correlated equilibrium (PDF pp. 1–17).

## Problem formulation

- Each agent has its own action-dependent linear feature representation in a finite-horizon Markov game; the objective is an ε-CCE without exponential joint-action dependence (PDF pp. 4–6).

## Actual contribution

- The paper refines AVLPR with stochastic pessimistic gaps, magnitude-reduced estimators, adaptive concentration, and action-dependent bonuses to recover ε^{-2} scaling without polynomial A_max dependence (PDF pp. 6–17).

## Core objects and equations

- Core objects are per-agent loss/value features, CCE gaps, stochastic gap estimates, covariance inverses, magnitude reduction, data-dependent bonuses, and a potential controlling cumulative expected gaps (PDF pp. 6–16).

## Algorithms or mechanism primitives

- Algorithm 1 is improved AVLPR; Algorithm 2 is the CCE approximation with EXP3-style policies and two bonuses; Algorithm 3 supplies value approximation (PDF pp. 7–13, 40–42).

## Assumptions and information structure

- The main theorem assumes finite horizon, general-sum Markov policies, independent linear function approximation with dimension d, and access to the specified subroutines/sampling protocol (PDF pp. 4–13).

## Theorems and guarantees

- Theorem 4.3 gives sample complexity Ṍ(m⁴ d⁵ H⁶ ε^{-2}) for an ε-CCE, polynomial in agent count m and avoiding polynomial A_max factors under Assumption 2.1 (PDF p. 13; proof pp. 40–42).

## Experiments and evaluation protocol

- No empirical benchmark is presented; evidence is theorem/proof based (PDF pp. 1–46).

## Failure boundaries and non-claims

- The guarantee is for CCE in a finite-horizon independent-linear-FA class; polynomial m dependence is not held-out-N generalization, and computational practicality is not experimentally established (PDF pp. 4–17).

## HMASD prospective connections

- Action-dependent pessimistic bonuses are prospective tools for roster-scalable uncertainty accounting in HMASD, but require a valid independent feature model and a deployable equilibrium target (PDF pp. 9–16).

## Recommended reading route

- Read the problem/assumption on pp. 4–6, improved AVLPR on pp. 6’, estimator/bonus design on pp. 9–13, and Theorem 4.3 plus proof outline on pp. 13–17.

## Source-page anchors

- Model and CCE (PDF pp. 4–6); Algorithm 1 (pp. 6’); CCE subroutine (pp. 9–13); main theorem (p. 13); proof outline (pp. 13–17); formal proof (pp. 22–42).
