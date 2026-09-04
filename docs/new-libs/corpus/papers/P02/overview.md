# Independent Natural Policy Gradient Always Converges in Markov Potential Games

## Identity and scope

This local file is arXiv:2110.10614v1 (2021), corresponding to an AISTATS 2022 paper on independent natural policy gradient in discounted Markov potential games. (PDF pages 1-3)

## Problem formulation

Each agent maximizes its discounted value under a product policy; an MPG has a state-dependent potential whose unilateral policy differences match that agent's value differences, and the target is a Nash-equilibrium joint policy. (PDF pages 4-7)

## Actual contribution

The paper connects independent NPG to natural ascent on the common potential and argues last-iterate convergence under a sufficiently small fixed step size, supplemented by tabular congestion-game comparisons against independent policy gradient. (PDF pages 3; 8-17)

## Core objects and equations

Key objects are discounted occupancy, value/Q/advantage functions, MPG potential, mismatch coefficient, Fisher matrix, softmax policy, and the multiplicative-weights form of the NPG update. (PDF pages 4-10)

## Algorithms or mechanism primitives

Independent NPG updates each agent's logits using its expected advantage; after changing variables to policy probabilities, the update is multiplicative weights with per-state normalization. (PDF page 8)

## Assumptions and information structure

The formal setting is finite and tabular with rewards in [0,1], product policies, discounted return, oracle expected advantages, interior softmax initialization, and a step size below the stated bound; Lemma 3.6 additionally invokes isolated fixed points. (PDF pages 4-11)

## Theorems and guarantees

Theorem 3.1 states pointwise last-iterate convergence to equilibrium policies for step size eta below (1-gamma)^3 divided by the stated n/action/mismatch constant; Lemmas 3.2-3.6 establish potential ascent, fixed-point convergence, and the equilibrium step. (PDF pages 8-11)

## Experiments and evaluation protocol

The distancing game uses 8 agents, 4 facilities, 2 states, learning rate 0.0001, and 10 runs; the stochastic congestion game uses a six-vertex layered graph and primarily 4 agents, with 10-run L1-distance-to-final-policy plots. The paper also reports INPG traces for 8 agents. (PDF pages 12-18)

## Failure boundaries and non-claims

The guarantee is specific to MPGs and oracle/tabular advantages; the authors list finite-time rates, sampled advantage estimation, function approximation, and TRPO convergence as future work. (PDF page 17)

Curator boundary: experiments at 4 and 8 agents are separate fixed-N runs and do not demonstrate one frozen policy generalizing across roster size. (PDF pages 14-18)

## HMASD prospective connections

Curator connection (prospective): the potential-as-Lyapunov proof suggests a diagnostic for decentralized UAV coordination when the modeled task can justify an MPG structure; the MPG equality must be checked rather than assumed. (PDF pages 4-11)

## Recommended reading route

Read the formal MPG and NPG definitions, then Theorem 3.1 with Lemmas 3.2-3.6, and finally the two experiment protocols and limitations. (PDF pages 4-17)

## Source-page anchors

The informal result is on PDF page 3, definitions on pages 4-8, formal convergence on pages 8-11, experiments on pages 12-18, and appendix proofs on pages 20-24. (PDF pages 3-24)
