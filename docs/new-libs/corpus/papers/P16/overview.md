# P16 — Trust Region Policy Optimisation in Multi-Agent Reinforcement Learning

## Identity and scope

- An ICLR 2022 cooperative-MARL paper deriving sequential trust-region policy updates and implementing HATRPO/HAPPO without requiring parameter sharing or value decomposition (PDF pp. 1–9).

## Problem formulation

- A factored joint policy in a fully cooperative Markov game is updated one agent at a time; each update conditions on earlier agents' new policies and controls KL divergence from the old policy (PDF pp. 3–6).

## Actual contribution

- The multi-agent advantage decomposition yields a lower bound on joint return, a monotonic policy-iteration scheme, and practical TRPO/PPO approximations for heterogeneous agents (PDF pp. 4–8).

## Core objects and equations

- Core objects are joint and incremental advantages A^{i_1:m}, sequential surrogate objectives L^{i_1:m}, max/expected KL penalties, and importance-ratio products for earlier updated agents (PDF pp. 4–7).

## Algorithms or mechanism primitives

- Algorithm 1 gives exact sequential multi-agent policy iteration; HATRPO enforces per-agent expected-KL constraints, while HAPPO uses clipped importance-ratio surrogates (PDF pp. 5–8, 22–24).

## Assumptions and information structure

- The exact analysis uses fully cooperative games, factored η-soft policies, centralized advantage access, and randomized update orders; practical algorithms approximate exact KL/advantage quantities from samples (PDF pp. 4–8).

## Theorems and guarantees

- Theorem 2 proves monotonic return improvement for Algorithm 1; Theorem 3 states every limit point is a Nash equilibrium when every update permutation has fixed nonzero probability (PDF pp. 6, 18–20).

## Experiments and evaluation protocol

- HATRPO/HAPPO are compared with IPPO, MAPPO, MADDPG and others on Multi-Agent MuJoCo and SMAC, with ablations on update order and parameter sharing in the appendix (PDF pp. 8’, 24–27).

## Failure boundaries and non-claims

- The exact monotonic theorem applies to ideal Algorithm 1, not automatically to neural HAPPO/HATRPO approximations; sequential update cost/order scales with roster size and no held-out-N policy test is supplied (PDF pp. 5’).

## HMASD prospective connections

- Sequential trust-region updates are a prospective way to control cross-agent interference in HMASD, but variable rosters need order-invariant/shared parameterization and cost-matched update scheduling (PDF pp. 4–8).

## Recommended reading route

- Read the parameter-sharing counterexample and advantage lemma on pp. 4–5, Theorems 2–3 on p. 6, practical surrogates on pp. 6–8, then experiments/appendix on pp. 8’ and 22–27.

## Source-page anchors

- Parameter-sharing limit (PDF p. 4); advantage decomposition/Algorithm 1 (pp. 4–5); monotonicity and equilibrium (p. 6); HATRPO/HAPPO (pp. 6–8); experiments (pp. 8’, 24–27).
