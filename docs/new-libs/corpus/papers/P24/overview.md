# P24 — Solving Continuous Mean Field Games: Deep Reinforcement Learning for Non-Stationary Dynamics

## Identity and scope

- A NeurIPS 2025 paper introducing Density-Enhanced Deep-Average Fictitious Play (DEDA-FP) for non-stationary continuous-state/action mean-field games (PDF pp. 1–10).

## Problem formulation

- A representative agent optimizes against a time-indexed population distribution while its policy must be consistent with the induced distribution flow; exploitability measures equilibrium deviation (PDF pp. 3–5).

## Actual contribution

- DEDA-FP combines deep best responses, supervised average-policy representation, and a time-conditioned normalizing flow for population density and sampling, with an error-propagation analysis (PDF pp. 4–7).

## Core objects and equations

- Core objects are policy-induced flows μ^π, best response, exploitability, fictitious-play averages, neural average policy, conditional density model, and three approximation errors (PDF pp. 3–7).

## Algorithms or mechanism primitives

- Each iteration trains SAC/PPO as an approximate best response, supervises a network to represent the average policy, and fits a conditional normalizing flow to the evolving population density (PDF pp. 5‖, 16‑9).

## Assumptions and information structure

- Theorem 1 assumes Lipschitz objective/mean-field maps and controlled best-response, supervised-policy, and density-model errors; deep-network training itself is not fully characterized (PDF pp. 6‗, 14‑6).

## Theorems and guarantees

- Theorem 1 bounds true exploitability at iteration k by accumulated best-response, supervised-learning, and normalizing-flow errors under Assumptions 1–2 (PDF p. 7; proof pp. 14‑6).

## Experiments and evaluation protocol

- Four independent runs report approximate exploitability for Beach Bar, LQ, and four-rooms tasks; SAC is used for the first two, PPO for four rooms, and an RTX 4090 for each experiment (PDF pp. 7‑0).

## Failure boundaries and non-claims

- The authors note incomplete theory for deep training, approximate/environment-dependent exploitability, and no extensions yet to multi-population, graphon, or common-noise MFGs; this is not arbitrary finite-player MARL (PDF p. 10).

## HMASD prospective connections

- Time-conditioned density models and explicit best-response/policy/density error channels are prospective primitives for non-stationary fleet planning, but finite-N, churn, and UAV transfer need separate validation (PDF pp. 5‑0).

## Recommended reading route

- Read the MFG/exploitability definitions on pp. 3―, DEDA-FP on pp. 5‖, Theorem 1 and experiments on pp. 7‑0, then implementation/proof appendices on pp. 14‑9.

## Source-page anchors

- MFG model (PDF pp. 3—); DEDA-FP (pp. 5‖); error theorem (p. 7); experiments (pp. 7‑0); limitations (p. 10); proof/implementation (pp. 14‑9).
