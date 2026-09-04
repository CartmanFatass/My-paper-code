# P09 — Model-Free Mean-Field Reinforcement Learning: Mean-Field MDP and Mean-Field Q-Learning

## Identity and scope

- A rigorous mean-field-control treatment that lifts common-noise MFC into a mean-field MDP, relates policy classes, derives state-action Bellman equations, and adapts tabular/deep RL (PDF pp. 1–33).

## Problem formulation

- The controlled state is a probability distribution over agent states, with population-level randomized actions and common noise; the objective is infinite-horizon discounted cooperative control (PDF pp. 3–12).

## Actual contribution

- The work connects closed/open-loop MFC policies to MFMDP Markov policies, proves existence and dynamic programming results, then constructs discretized tabular and neural Q-learning approaches (PDF pp. 12–33).

## Core objects and equations

- Core objects include probability-measure states, randomized population actions, the lifted transition F-bar, value J-bar, optimal Q-bar, and Bellman operators on lower-semicontinuous functions (PDF pp. 9–20).

## Algorithms or mechanism primitives

- The tabular method discretizes the state simplex and action distributions before asynchronous Q-learning; the deep method uses actor/critic networks and replay to avoid explicit simplex discretization (PDF pp. 20–28, 43–45).

## Assumptions and information structure

- Formal results use Polish/Borel spaces, continuity/compactness and discount assumptions H1–H2; tabular convergence adds discretization and visitation/learning-rate conditions H3–H5 (PDF pp. 3–12, 21–27).

## Theorems and guarantees

- Theorems 19, 22, 27, and 30 establish DPP, policy-class relations, and the Q Bellman equation; Theorems 35–36 bound discretized Q-learning under their stated assumptions (PDF pp. 12–27).

## Experiments and evaluation protocol

- Numerical examples cover cyber security, discrete distribution planning, and swarm motion, comparing tabular or deep mean-field methods in model-specific settings (PDF pp. 28–33).

## Failure boundaries and non-claims

- This is mean-field control of a population distribution, not a theorem that a learned finite-player MARL policy works across arbitrary N; approximation from finite N is motivation, not the paper's held-out-N experiment (PDF pp. 3–5, 28–33).

## HMASD prospective connections

- The distribution state/action lifting is a prospective fixed-dimensional planner for interchangeable UAV populations, but local identities, finite-N error, churn, and observation estimation need separate treatment (PDF pp. 3–12, 18–28).

## Recommended reading route

- Use the contents on p. 1; read MFMDP/DPP on pp. 9–13, policy relations on pp. 13–17, Q-learning theory on pp. 18–27, then examples on pp. 28–33.

## Source-page anchors

- Model/common noise (PDF pp. 3–9); MFMDP and DPP (pp. 9–13); policy relations (pp. 13–17); Bellman Q and learning (pp. 18–27); examples (pp. 28–33).
