# P25 — The Power of Exploiter: Provable Multi-Agent RL in Large State Spaces

## Identity and scope

- An ICML 2022 theory paper for finite-horizon two-player zero-sum Markov games with general function approximation, introducing an exploiter and multi-agent Bellman-Eluder dimension (PDF pp. 1’).

## Problem formulation

- A max-player learns a Nash policy through self-play against a deliberately selected best-response exploiter, while confidence sets over function classes encode uncertainty (PDF pp. 3‗).

## Actual contribution

- GOLF_WITH_EXPLOITER separates optimistic main-player planning from exploiter computation and proves sample efficiency for low multi-agent BE dimension, including linear, kernel, and rich-observation examples (PDF pp. 5’).

## Core objects and equations

- Core objects are Q/value function classes F/G, realizability and completeness, Nash Bellman residuals, Q/V-type BE dimension, confidence sets, main-player optimism, and exploiter best response (PDF pp. 3‘).

## Algorithms or mechanism primitives

- Algorithm 1 performs optimistic planning, computes an exploiter, collects trajectories or stepwise exploratory samples, and filters a confidence set; Algorithm 2 fits the exploiter response (PDF pp. 5‗).

## Assumptions and information structure

- Theory assumes two-player zero-sum finite-horizon games, approximate realizability/completeness, access to function-class optimization, and finite classes or bounded covering numbers (PDF pp. 3‘).

## Theorems and guarantees

- Theorem 4.4 gives O(√K) regret in low BE dimension; Corollary 4.5 gives Ṍ(H² dim_BE/ε²) sample scaling up to class/error terms; Theorem 4.8 handles adversarial opponents with a weaker objective (PDF pp. 7‘).

## Experiments and evaluation protocol

- No empirical benchmark is presented; evidence is theorem/proof based (PDF pp. 1‒9).

## Failure boundaries and non-claims

- The results are not for cooperative or general-sum N-agent MARL, and the authors state the algorithm is sample-efficient but computationally inefficient (PDF pp. 2, 6’).

## HMASD prospective connections

- The exploiter is a prospective adversarial curriculum primitive for finding weaknesses in an HMASD controller, but the zero-sum two-player theory does not transfer directly to cooperative UAV teams (PDF pp. 5‘).

## Recommended reading route

- Read assumptions and BE definitions on pp. 3‖, Algorithm 1 and exploiter construction on pp. 5‗, guarantees on pp. 7‘, and function-class examples on pp. 8’.

## Source-page anchors

- Problem/function classes (PDF pp. 3―); Algorithm 1 (pp. 5‖); BE dimension and guarantees (pp. 6‘); examples/boundaries (pp. 8’); proofs (pp. 15‒9).
