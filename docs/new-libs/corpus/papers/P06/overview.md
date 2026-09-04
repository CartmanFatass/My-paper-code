# P06 — Addressing Rotational Learning Dynamics in Multi-Agent Reinforcement Learning

## Identity and scope

- A 2025 preprint reframing centralized-critic actor-critic MARL as a variational-inequality problem and testing lookahead/extragradient modifications (PDF pp. 1–8).

## Problem formulation

- The paper attributes part of MARL instability to rotational components in the joint gradient/operator field, where ordinary descent-style optimizers can cycle or diverge (PDF pp. 1–5).

## Actual contribution

- It proposes reusable VI wrappers for existing MARL actor-critic updates, emphasizing LA-MARL and optional extragradient, then measures policy distance to equilibrium and coordination outcomes (PDF pp. 4–8).

## Core objects and equations

- The central object is the stacked multi-agent operator built from actor and critic gradients; nested lookahead periodically interpolates fast and slow parameter copies, while extragradient evaluates a predictive point (PDF pp. 3–6, 15–23).

## Algorithms or mechanism primitives

- Algorithms 1–3 specify nested lookahead and VI-MARL variants; appendices instantiate LA-MADDPG, LA-MATD3, and related pseudocode (PDF pp. 4–6, 16–23).

## Assumptions and information structure

- The main MARL study uses CTDE with centralized critics and separate actors; conclusions depend on optimizer integration, buffer/update choices, and environment-specific equilibrium metrics (PDF pp. 2–6, 17–24).

## Theorems and guarantees

- The work motivates VI methods from known optimization results but does not prove a new general convergence theorem for the deep MARL systems evaluated (PDF pp. 2–6, 8).

## Experiments and evaluation protocol

- It evaluates RPS and matching pennies plus MPE predator-prey and physical deception; reported plots use five training seeds, and the MPE equilibrium table uses 100 evaluation environments (PDF pp. 6–8, 24–30).

## Failure boundaries and non-claims

- Rewards can hide non-equilibrium behavior, and the paper's empirical gains do not establish convergence for arbitrary non-monotone games, variable N, or deployment-time churn (PDF pp. 7–8).

## HMASD prospective connections

- LA/EG wrappers are prospective optimizer interventions for diagnosing rotational failure in HMASD without changing policy semantics; a matched gradient-descent control and operator-norm diagnostics would be needed (PDF pp. 4–8).

## Recommended reading route

- Read the operator motivation on pp. 1–5, the proposed methods on pp. 5–6, the equilibrium-aware evaluations on pp. 6–8, then implementation details on pp. 20–30.

## Source-page anchors

- Rotational motivation (PDF pp. 1–2); operator construction (pp. 3–5); LA/EG integration (pp. 5–6); results (pp. 6–8); detailed algorithms/results (pp. 20–30).
