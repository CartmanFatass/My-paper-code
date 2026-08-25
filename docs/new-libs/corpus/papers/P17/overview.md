# MAVEN: Multi-Agent Variational Exploration

## Identity and scope

This NeurIPS 2019 paper studies exploration failures induced by monotonic value factorization under centralized training with decentralized execution and proposes MAVEN, a latent-variable extension of QMIX. (PDF pages 1-4)

## Problem formulation

The cooperative task is a Dec-POMDP; decentralized argmax requires an individual-global-max consistency condition, while QMIX enforces it through a monotonic mixing network that cannot represent nonmonotonic joint Q-functions. (PDF pages 2-4)

## Actual contribution

The paper gives counterexample families where visitation plus QMIX's representation class yields suboptimal policies, then adds an episode-persistent shared latent mode, a hierarchical latent policy, and a variational mutual-information objective for committed exploration. (PDF pages 3-6)

## Core objects and equations

Core objects are monotonic value decomposition, nonmonotonic Q-functions, latent z sampled from the initial state, z-conditioned utilities/mixer, Q-learning loss, episode return, mutual information I(trajectory;z), and its variational lower bound. (PDF pages 2-6)

## Algorithms or mechanism primitives

Algorithm 1 alternates episode rollouts under a sampled z with updates to the hypernetwork, feature and mixing networks, variational posterior, and latent policy; z is sampled once per episode and used during decentralized action selection. (PDF pages 5-6)

## Assumptions and information structure

Training is centralized and execution decentralized; agents act on local histories, while training may use global state. The theorem family concerns constructed n-player k-action matrix games, and MAVEN's latent is shared and episode-persistent. (PDF pages 2-6)

## Theorems and guarantees

Theorem 1 constructs uniform-visitation matrix games where QMIX learns a suboptimal policy; Theorem 2 gives a probability bound for the analogous epsilon-greedy setting. These are failure guarantees for a family, not a convergence guarantee for MAVEN. (PDF pages 3-4)

## Experiments and evaluation protocol

The m=10 matrix game reports 100,000 training steps over 20 random initializations; SMAC evaluation pauses every 100,000 steps for 32 greedy episodes and reports median win rate with interquartile shading. Maps include corridor, 6h_vs_8z, 2s3z, 2-corridors with a gate change at 5 million steps, and zealot_cave; ablations vary latent policy and MI loss. (PDF pages 6-8)

## Failure boundaries and non-claims

MAVEN has empirical support but no theorem that its variational objective finds globally diverse or optimal behaviors; a poor variational posterior creates a lower-bound gap. (PDF pages 5-6; 9)

Curator boundary: z persists for a fixed episode. This is not an adaptive or externally variable skill period k; the k in the matrix-game theorem denotes action count. (PDF pages 2-6)

## HMASD prospective connections

Curator connection (prospective): episode-persistent latent coordination and mutual-information diversity are plausible starting ingredients for variable-duration skills, but HMASD must add explicit termination/duration control and evaluate changed k. (PDF pages 4-6)

Curator connection (prospective): the 2-corridors intervention is a useful pattern for testing coordinated recovery after a known environment change, not evidence of variable roster robustness. (PDF page 7)

## Recommended reading route

Read the CTDE/QMIX setup and counterexample theorems, then Figure 2/Algorithm 1 and the MI bound, then the experiment protocol and ablations. (PDF pages 2-8)

## Source-page anchors

Representation and Theorems 1-2 are on pages 2-4, MAVEN and Algorithm 1 on pages 4-6, experiments/ablations on pages 6-8, and limitations/future work on page 9. (PDF pages 2-9)
