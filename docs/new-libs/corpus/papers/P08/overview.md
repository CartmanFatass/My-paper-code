# P08 — Mean Field Multi-Agent Reinforcement Learning

## Identity and scope

- An ICML 2018 paper introducing practical mean-field Q-learning (MF-Q) and actor-critic (MF-AC) for large populations by replacing joint neighbor actions with an average effect (PDF pp. 1–8).

## Problem formulation

- Each homogeneous agent interacts with an empirical distribution/mean action of its neighborhood, reducing a many-body stochastic game to an agent-versus-mean-field interaction (PDF pp. 2–4).

## Actual contribution

- The paper derives mean-field Q and actor-critic updates, gives a convergence argument under strong stage-game assumptions, and demonstrates scaling to hundreds or thousands of agents in selected tasks (PDF pp. 3–8).

## Core objects and equations

- Core objects are the mean-field action, local Q(s,a,ā), Boltzmann/actor policy, mean-field Bellman operator, and a Nash-Q comparison used in the convergence proof (PDF pp. 3–5).

## Algorithms or mechanism primitives

- MF-Q averages neighbor actions before TD learning; MF-AC uses a centralized/shared mean-field critic with decentralized actors (PDF pp. 3–4; pseudocode referenced on PDF p. 4).

## Assumptions and information structure

- The proof uses infinite visitation, GLIE, bounded reward, and a strong assumption that each stage-game Nash equilibrium is globally optimal or a saddle point; empirical methods assume meaningful neighbor averaging (PDF pp. 4–5).

## Theorems and guarantees

- The convergence section argues the MF-Q operator is contractive and Q converges to Nash Q under Assumptions 1–3; this guarantee is tied to the stated homogeneous/stage-game structure (PDF pp. 4–5).

## Experiments and evaluation protocol

- Experiments cover Gaussian Squeeze at N=100, 500, 1000; a 20×20 Ising model; and a 64-vs-64 battle, with additional battle sizes 8, 144, and 256 reported qualitatively (PDF pp. 6–8).

## Failure boundaries and non-claims

- Mean aggregation assumes the average sufficiently summarizes interaction; separate experiments at several N do not show one frozen policy tested at held-out N (PDF pp. 3–8).

## HMASD prospective connections

- The mean-neighbor interface is a prospective variable-roster primitive for local UAV interactions, but it needs an explicit invariance map, held-out-N evaluation, and tests against multimodal neighbor effects (PDF pp. 3–8).

## Recommended reading route

- Read the approximation on pp. 2–4, the proof assumptions on pp. 4–5, then Gaussian Squeeze, Ising, and battle protocols on pp. 6–8.

## Source-page anchors

- Model reduction (PDF pp. 2–3); MF-Q/MF-AC (pp. 3–4); convergence assumptions (pp. 4–5); N=100/500/1000 and other experiments (pp. 6–8).
