# A Concise Introduction to Decentralized POMDPs

## Identity and scope

This author preprint is a compact book-length treatment of decentralized partially observable Markov decision processes, with finite- and infinite-horizon planning, complexity, factored structure, macro-actions, communication, and reinforcement learning. (PDF pages 1-7; 8-123)

## Problem formulation

A Dec-POMDP models a cooperative team with a shared reward, stochastic state transitions and observations, and policies conditioned on each agent's local action-observation history; centralized planning must produce decentralized executable policies. (PDF pages 18-39)

## Actual contribution

The book unifies formal definitions, policy and belief representations, worst-case complexity, exact and approximate planning methods, finite-state controllers, factored models, and communication variants into a navigable reference. (PDF pages 18-123)

## Core objects and equations

Core objects are joint policies over private histories, plan-time sufficient statistics and multiagent beliefs, policy trees and decision rules, finite-state controllers, value functions for fixed joint policies, and coordination graphs for factored rewards and transitions. (PDF pages 40-61; 74-105)

## Algorithms or mechanism primitives

The algorithmic route covers dynamic programming, multi-agent A* and heuristic search, conversion to non-observable MDPs, bounded and memory-bounded DP, finite-state-controller policy iteration/optimization, factored max-sum methods, macro-actions, and communication-aware planning. (PDF pages 48-121)

## Assumptions and information structure

The standard model assumes no extra communication beyond what actions, states, and observations encode; later sections distinguish implicit from explicit communication and analyze instantaneous, delayed, costly, and local communication models. (PDF pages 22-39; 107-120)

## Theorems and guarantees

Theorem 1 states that finding an optimal finite-horizon Dec-POMDP solution for at least two agents is NEXP-complete, and the text notes the same worst-case hardness for epsilon-approximation; Theorem 2 gives piecewise-linear convexity of the plan-time optimal value representation. (PDF pages 46-47; 55-56)

## Experiments and evaluation protocol

Evidence is textbook synthesis, formal complexity, algorithm derivations, and benchmark-domain examples such as Dec-Tiger, recycling, box pushing, networks, and sensors; it is not one controlled cross-algorithm empirical study. (PDF pages 24-39; 48-121)

## Failure boundaries and non-claims

Worst-case NEXP complexity is a statement about finite-horizon planning instances, not a claim that every practical instance requires the worst-case time; approximations and structural restrictions remain central. (PDF pages 46-73; 96-105)

Curator boundary: the section on k-step delayed communication fixes an information delay parameter; it is not a variable learned skill duration and cannot be cited as adaptive HMASD skill period k. (PDF pages 114-116)

## HMASD prospective connections

Curator connection (prospective): Dec-POMDP local-history policies and plan-time sufficient statistics provide a precise information model for decentralized UAV teams. (PDF pages 18-47)

Curator connection (prospective): macro-actions and explicit communication are useful ingredients for skill abstraction and bandwidth-aware coordination, but an HMASD variable-k treatment must add duration adaptation or termination rather than inherit a fixed delay/macro duration. (PDF pages 106-120)

## Recommended reading route

Read the model definition and finite-horizon policy representation first, then complexity and exact planning, then infinite-horizon controllers; finish with factored models, macro-actions, and communication according to the target system. (PDF pages 18-61; 74-121)

## Source-page anchors

Definition 2/10 and the information structure are in Chapter 2; complexity is in section 3.5; exact and approximate planning occupy Chapters 4-5; macro-actions and communication are in sections 8.2-8.3. (PDF pages 18-47; 48-73; 106-120)
