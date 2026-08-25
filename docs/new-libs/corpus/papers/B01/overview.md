# B01 — Multi-Agent Reinforcement Learning: Foundations and Modern Approaches

## Identity and scope

- A broad textbook joining reinforcement learning, game-theoretic models, foundational MARL algorithms, deep MARL, implementation practice, and environments (PDF pp. 10–15, 30–365).
- The PDF identifies a CC BY-NC-ND edition and separately states that use to train AI systems requires written MIT Press permission (PDF p. 7).

## Problem formulation

- MARL is organized around stochastic and partially observable stochastic games, joint policies, information assumptions, and solution concepts rather than a single universal objective (PDF pp. 72–117).

## Actual contribution

- The book supplies a common notation and a continuous route from MDP/RL fundamentals through game solutions, classical learning dynamics, deep CTDE methods, and experimental practice (PDF pp. 16–18, 48–365).

## Core objects and equations

- Core objects include value and action-value functions, Bellman equations, best responses, minimax/Nash/correlated equilibria, regret, policy-gradient identities, centralized critics, and value factorizations (PDF pp. 48–117, 144–187, 212–333).

## Algorithms or mechanism primitives

- The algorithm route covers value iteration and joint-action Q-learning, fictitious play, gradient and regret dynamics, DQN/PPO/actor-critic, independent learners, COMA-style counterfactual credit, VDN/QMIX, self-play, and PSRO (PDF pp. 144–187, 212–333).

## Assumptions and information structure

- The treatment explicitly separates centralized/decentralized training and execution, observable state versus local history, agent homogeneity, parameter sharing, and access to joint actions or centralized information (PDF pp. 72–88, 248–305).

## Theorems and guarantees

- This is a synthesis textbook: it derives selected Bellman, equilibrium, regret, and policy-gradient results while attributing guarantees to their source settings; it is not one new end-to-end MARL theorem (PDF pp. 90–117, 144–187, 212–333).

## Experiments and evaluation protocol

- Evaluation guidance covers learning curves, uncertainty across runs, hyperparameter search, and environment selection; environment chapters summarize matrix games, LBF, MPE, SMAC, RWARE, football, Hanabi, Overcooked, and suites (PDF pp. 65–69, 334–365).

## Failure boundaries and non-claims

- The book names non-stationarity, equilibrium selection, multi-agent credit assignment, and scaling to many agents as distinct challenges; parameter sharing or testing several roster sizes is not presented as a general held-out-N guarantee (PDF pp. 131–141, 305–333).

## HMASD prospective connections

- Prospective use: ground HMASD terminology, observation/action information structure, CTDE interfaces, credit baselines, and variable-roster implementation choices; these are curator connections, not evidence for an HMASD result (PDF pp. 248–347).

## Recommended reading route

- Start with Chapters 1 and 5 for agendas and failure modes, Chapter 3–4 for formal game language, Chapter 9 for modern MARL mechanisms, then Chapter 10 for implementation/evaluation (PDF pp. 30–45, 72–143, 248–347).

## Source-page anchors

- Contents and notation (PDF pp. 10–18); stochastic games and knowledge assumptions (pp. 72–89); MARL challenges (pp. 118–143); modern deep MARL (pp. 248–333); practice and environments (pp. 334–365).
