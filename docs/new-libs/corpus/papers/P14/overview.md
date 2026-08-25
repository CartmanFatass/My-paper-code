# P14 — Mean-Field Controls with Q-learning for Cooperative MARL: Convergence and Complexity Analysis

## Identity and scope

- A SIAM journal paper building MFC-K-Q, a kernel-based Q-learning method for mean-field control, and connecting it to interchangeable cooperative MARL (PDF pp. 1–27).

## Problem formulation

- N identical, indistinguishable agents share a cooperative objective; the mean-field lift uses a population distribution as state and a distribution of local state-action controls as action (PDF pp. 3–9).

## Actual contribution

- The paper derives a DPP for an integrated Q function, constructs kernel/discretized MFC Q-learning, proves linear fixed-point convergence and covering bounds, and supplies O(N^{-1/2}) MARL approximation (PDF pp. 6–23).

## Core objects and equations

- Core objects are the population state μ, lifted action h, deterministic population transition Φ, integrated Q, Bellman operator, ε-net C_ε, and kernel interpolant Γ_K (PDF pp. 4–14).

## Algorithms or mechanism primitives

- Algorithm 4.1 samples neighborhoods of an ε-net, estimates reward/dynamics, and iterates an approximate Bellman operator with kernel regression (PDF pp. 9–10).

## Assumptions and information structure

- Guarantees require finite state/action sets, interchangeability, Lipschitz rewards/transitions/policies, contraction, kernel locality, reachability/covering, and common access to the population state/action representation (PDF pp. 4–16).

## Theorems and guarantees

- Theorem 5.5 gives an O(ε) approximation bound and linear convergence to the approximate fixed point; Theorem 5.6 bounds covering time; Theorem 6.3 gives O(N^{-1/2}) finite-agent value approximation (PDF pp. 12–17).

## Experiments and evaluation protocol

- Network traffic congestion experiments compare MFC-K-Q with MARL baselines over varying N and report gains especially beyond roughly 50 agents in the tested setting (PDF pp. 23–26).

## Failure boundaries and non-claims

- The N-independent learning complexity belongs to the mean-field problem under interchangeability; combined with O(N^{-1/2}) approximation it is not a generic finite-MARL or frozen-policy cross-N theorem (PDF pp. 14–23).

## HMASD prospective connections

- MFC-K-Q provides a population-state planning template for homogeneous UAV fleets; practical use needs continuous observations/actions, population estimation, churn handling, and a cross-N policy protocol (PDF pp. 3–23).

## Recommended reading route

- Read the lifted MFC model on pp. 3–6, integrated-Q DPP on pp. 6–9, Algorithm 4.1 and Theorems 5.5–5.6 on pp. 9–16, then finite-N bridge and experiments on pp. 16–26.

## Source-page anchors

- MFC lift (PDF pp. 3–6); Q DPP (pp. 6–9); algorithm (pp. 9–10); convergence/complexity (pp. 10–16); O(N^{-1/2}) bridge (pp. 16–23); experiments (pp. 23–26).
