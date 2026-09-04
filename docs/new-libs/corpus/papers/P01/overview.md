# If Multi-Agent Learning Is the Answer, What Is the Question?

## Identity and scope

This 2006 author preprint of the 2007 Artificial Intelligence article is a conceptual critique and taxonomy of multi-agent learning, not a new learning algorithm. (PDF pages 1-3)

## Problem formulation

The discussion is grounded in stochastic/Markov games, while repeatedly asking which agent objective, opponent class, self-play condition, payoff criterion, or equilibrium property a learning rule is meant to satisfy. (PDF pages 3-7; 11-16)

## Actual contribution

The authors separate five agendas often conflated under MAL: computational, descriptive, normative, prescriptive cooperative, and prescriptive non-cooperative, each with a different success criterion. (PDF pages 14-16)

## Core objects and equations

The formal objects are stochastic games, repeated games, policies over histories, equilibrium and payoff criteria, regret, safety, consistency, opponent models, and teaching effects. (PDF pages 3-13)

## Algorithms or mechanism primitives

Representative families include model-based best response, model-free/Q-learning variants, fictitious and rational learning, and regret minimization; they are examples used to expose differing goals rather than one recommended universal method. (PDF pages 7-13)

## Assumptions and information structure

Results surveyed depend on restrictions such as self-play, two agents, zero-sum or common-payoff structure, stationary opponents, infinite exploration, learning-rate conditions, or strong belief-model assumptions. (PDF pages 11-13)

## Theorems and guarantees

The paper contributes no new convergence theorem; it compares types of claims such as equilibrium convergence, opponent-model accuracy, payoff thresholds, safety, and no-regret guarantees and argues that their evaluation criteria must be explicit. (PDF pages 11-16)

## Experiments and evaluation protocol

There is no empirical evaluation. Game examples, including Stackelberg interaction and Rock-Paper-Scissors tournaments, illustrate why equilibrium play and actual achieved reward can answer different questions. (PDF pages 5-7)

## Failure boundaries and non-claims

The literature sample is intentionally partial and not a ranking; the article warns against treating convergence to a stage-game equilibrium as automatically the right performance yardstick. (PDF pages 3; 11-16)

## HMASD prospective connections

Curator connection (prospective): use the five-agenda taxonomy as an experiment-design checklist—state whether a variable-N or variable-k algorithm is being used to compute, explain, coordinate, or maximize reward, and match metrics accordingly. (PDF pages 14-16)

## Recommended reading route

Read the punch line and formal setting, then the three result types and their critique, and finish with the five agendas and summary. (PDF pages 1-3; 11-16)

## Source-page anchors

The stochastic-game setup begins on PDF page 3; representative MAL families on pages 7-11; evaluation claims and questions on pages 11-13; the five-agenda taxonomy on pages 14-16. (PDF pages 3-16)
