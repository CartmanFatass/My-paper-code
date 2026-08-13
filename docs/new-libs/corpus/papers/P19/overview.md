# Learning Rates for Q-learning

## Identity and scope

This JMLR 2003 article gives finite-time convergence-rate bounds for tabular single-agent Q-learning under polynomial versus linear learning-rate schedules; it is not a MARL theorem. (PDF pages 1-4)

## Problem formulation

The model is a finite discounted MDP with bounded nonnegative reward and discount gamma; the paper treats synchronous parallel sampling and asynchronous one-state-action updates with covering time L. (PDF pages 2-4)

## Actual contribution

The central result separates schedules alpha_t=1/t^omega for omega in (1/2,1) from alpha_t=1/t: polynomial schedules have polynomial dependence on 1/(1-gamma), whereas the linear schedule has exponential dependence, with a matching constructed lower bound. (PDF pages 1-6; 24)

## Core objects and equations

Core objects are Q*, the Bellman contraction, learning rate alpha_t, parallel sampling, covering time L, discount-derived beta=(1-gamma)/2, stochastic-approximation noise, and sup-norm error. (PDF pages 2-10)

## Algorithms or mechanism primitives

The same tabular Q update is analyzed under synchronous and asynchronous sampling; the schedule exponent omega controls the bias/noise contraction tradeoff. (PDF page 4)

## Assumptions and information structure

Results assume finite states/actions, bounded rewards, gamma<1, specified initialization, appropriate stochastic noise, and either ideal parallel sampling or an exploration sequence with finite covering time; high-probability bounds include epsilon and delta. (PDF pages 2-5; 8-10)

## Theorems and guarantees

Theorems 2-5 give high-probability upper bounds for synchronous/asynchronous polynomial and linear schedules; Theorem 6 supplies a deterministic one-state MDP requiring order (1/epsilon)^(1/(1-gamma)) steps for the linear schedule, with the construction proved in Lemma 39. (PDF pages 5-6; 24)

## Experiments and evaluation protocol

Experiments use random and line MDPs with two actions per state, including 100-state runs for 10^8 asynchronous steps and 10-state runs for 10^7 steps, plus the one-state lower-bound MDP; plots vary omega, gamma, and step budget. No repeated-seed uncertainty intervals are reported. (PDF pages 6-8)

## Failure boundaries and non-claims

The bounds concern tabular single-agent discounted MDPs and do not establish convergence under multi-agent non-stationarity, function approximation, replay, or policy-gradient updates. (PDF pages 1-4)

The JMLR article has no DOI; a DOI sometimes associated with this title belongs to the earlier COLT version, not this local file. (PDF pages 1; 25)

## HMASD prospective connections

Curator connection (prospective): use the schedule/discount interaction as a control when comparing MARL optimizers—especially near gamma=1—but do not transplant the single-agent bound without restoring its contraction and sampling assumptions. (PDF pages 4-6)

## Recommended reading route

Read the schedule contrast and model, then Theorems 2-6, inspect the experiment regimes, and use Section 10 for the lower-bound mechanism. (PDF pages 1-8; 24)

## Source-page anchors

Model and update are on pages 2-4, main bounds on pages 4-6, experiments on pages 6-8, proof machinery on pages 8-23, and lower bound on page 24. (PDF pages 2-24)
