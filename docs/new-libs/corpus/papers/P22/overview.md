# P22 — Accuracy of the Graphon Mean Field Approximation for Interacting Particle Systems

## Identity and scope

- A probability/queueing paper quantifying graphon mean-field approximation error for dense weighted interacting particle systems; it is not an RL or control-policy paper (PDF pp. 1–18).

## Problem formulation

- N finite-state particles interact through a weighted graph G^N with Markovian transition rates; a graphon-driven deterministic integro-differential system approximates expected particle states (PDF pp. 3–9).

## Actual contribution

- The main error separates a finite-size 1/N term from the L2 operator distance between the finite graph and limiting graphon, then specializes deterministic and random graph sampling (PDF pp. 7–10).

## Core objects and equations

- Core objects are binary particle-state fields X^{G_N}, graphon G, drift F^G, deterministic trajectory x^G, L2/operator graphon norm, and graph discretization/sampling distance (PDF pp. 3–9).

## Algorithms or mechanism primitives

- There is no learned policy; the method constructs and numerically solves a deterministic graphon mean-field ODE for comparison with stochastic systems (PDF pp. 8–14).

## Assumptions and information structure

- Theorem 1 assumes finite particle state space, piecewise-Lipschitz graphon and transition rates, dense interactions, matched finite/limit rates, and fixed finite time (PDF pp. 8’).

## Theorems and guarantees

- Theorem 1 bounds L2 bias by C_A/N + C_B|||G^N-G|||; deterministic weighted discretization yields O(1/N), while random sampling gives O(sqrt(log N/N)) with high probability (PDF pp. 9–10).

## Experiments and evaluation protocol

- Load-balancing and heterogeneous bike-sharing simulations compare finite-system sample means with graphon trajectories; bike-sharing plots average 7,500 simulations per system size (PDF pp. 10–14).

## Failure boundaries and non-claims

- The O(1/N) rate is for weighted interacting-particle bias with deterministic graph discretization, not graphon MFC/MARL value, learned-policy optimality, or held-out-N generalization (PDF pp. 8–10).

## HMASD prospective connections

- The decomposition can prospectively separate finite-roster error from graph approximation error in a UAV interaction model, but control, learning, and policy robustness would need new analysis (PDF pp. 8–10).

## Recommended reading route

- Read the particle model on pp. 3–5, graphon distance on pp. 6–7, assumptions/Theorem 1 on pp. 8‑0, then the two numerical systems on pp. 10‑4.

## Source-page anchors

- Particle system (PDF pp. 3–5); graphons/distances (pp. 6–7); main error and corollaries (pp. 8‑0); load balancing/bike sharing (pp. 10‑4); proof (pp. 15‑8).
