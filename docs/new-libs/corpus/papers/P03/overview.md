# P03 — Independent Policy Gradient for Large-Scale Markov Potential Games: Sharper Rates, Function Approximation, and Game-Agnostic Convergence

## Identity and scope

- A theoretical and computational study of independent policy-gradient updates for Markov potential games, with a cooperative special case, linear value-function approximation, and a separate game-agnostic optimistic update (PDF pp. 1–9).

## Problem formulation

- Players observe the state and update individual policies in discounted Markov potential/cooperative games; performance is average Nash regret and approximate Nash equilibrium under distribution-mismatch coefficients (PDF pp. 3–6).

## Actual contribution

- The paper removes explicit state-cardinality dependence from key iteration bounds, gives a sample-based linear-function-approximation analysis, and proves one optimistic scheme converges in both cooperative and zero-sum cases under its respective assumptions (PDF pp. 5–9).

## Core objects and equations

- Key objects are averaged action values, projected per-state policy updates, the Markov potential, Nash regret, mismatch coefficients, and linear features for each player's averaged Q-function (PDF pp. 3–8).

## Algorithms or mechanism primitives

- Algorithm 1 is exact independent projected policy ascent; Algorithm 2 estimates averaged Q-values from geometrically stopped rollouts and regression; Algorithm 3 couples optimistic actor steps to a smoothed critic (PDF pp. 5–8, 14–15).

## Assumptions and information structure

- Guarantees require MPG or identical-reward structure, discounted dynamics, specified mismatch bounds and stepsizes; the function-approximation result assumes each player's averaged Q is linear in a known local feature map with bounded statistical error (PDF pp. 3–8).

## Theorems and guarantees

- Theorems 1–4 give Nash-regret and iteration/sample bounds, including O(1/ε⁵) sample complexity for the stated sample-based case; Theorem 5 gives asymptotic last-iterate convergence for the two-player cooperative optimistic scheme (PDF pp. 5–9).

## Experiments and evaluation protocol

- Small computational studies test state-space/distribution-mismatch effects and the game-agnostic dynamics; extended plots and setup details are in the appendix (PDF pp. 9, 49–54).

## Failure boundaries and non-claims

- 'Large-scale' means favorable dependence on state size and polynomial rather than exponential dependence on player count; it does not show a single learned policy transferred across held-out N (PDF pp. 1, 5–8).

## HMASD prospective connections

- Prospectively, the per-agent projected update and mismatch-aware analysis are optimization baselines for scalable HMASD, but variable-roster transfer would need a shared representation and explicit cross-N protocol absent here (PDF pp. 5–8).

## Recommended reading route

- Read the definitions on pp. 3–4, Algorithm 1/Theorems 1–2 on pp. 5–6, the function-approximation assumptions and Theorems 3–4 on pp. 6–8, then the game-agnostic result on pp. 8–9.

## Source-page anchors

- Model and regret (PDF pp. 3–4); exact IPG (pp. 5–6); function approximation (pp. 6–8); game-agnostic convergence (pp. 8–9); proofs and extra experiments (pp. 16–54).
