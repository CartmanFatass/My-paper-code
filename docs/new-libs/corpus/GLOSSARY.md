# Cross-corpus glossary

This glossary is a routing aid. Individual papers may use narrower definitions;
their overview and source pages control.

## CTDE

Centralized training with decentralized execution. Training may use joint state
or actions, but each deployed agent must act from its allowed local information
and received communication. CTDE does not by itself solve roster-size transfer.

## Dec-POMDP

A cooperative partially observable stochastic game in which each agent acts
from its own action-observation history. It is an information-structure model,
not a guarantee that a learned policy is scalable.

## Empirical distribution / mean action

A normalized population summary used to replace explicit dependence on all
other agents. Normalization makes input dimension independent of `N`, but can
discard extensive evidence or workload and does not imply frozen-policy
held-out-`N` robustness.

## Mean-field control (MFC)

A cooperative control problem for a representative agent coupled to a
population distribution. It differs from a mean-field game, where individually
optimizing agents interact through the population law.

## Mean-field game (MFG)

The limiting strategic problem of an individual agent interacting with a
population distribution, typically seeking an equilibrium rather than a team
optimum.

## Graphon

A measurable kernel representing the limit of a dense graph sequence. Graphon
results normally require a specified convergence mode and do not automatically
cover sparse, disconnected, or arbitrarily relabeled communication graphs.

## Markov potential game

A Markov game whose unilateral policy changes align with changes in a potential
function. Convergence results exploiting this structure do not automatically
extend to arbitrary general-sum or cooperative games lacking the potential
identity.

## Natural policy gradient

A policy-gradient update preconditioned by the policy's information geometry,
often expressed through a Fisher information matrix. Independent-agent results
depend on game structure, sampling, stepsize, and parameterization assumptions.

## Quantal response equilibrium (QRE)

An entropy-regularized equilibrium in which action probabilities respond
smoothly to expected payoffs. It is not the same object as an unregularized Nash
equilibrium.

## Variational inequality (VI)

A problem of finding a point whose operator satisfies an inequality against all
feasible directions. Monotonicity enables strong algorithms such as
extragradient or dual extrapolation; MARL game operators need not be monotone.

## Rotational learning dynamics

The antisymmetric or cycling component of multi-agent gradient interaction.
Observed cycles in a restricted bilinear construction do not establish that all
MARL optimization failure is rotational.

## Information bottleneck

An objective trading compression of a representation against information useful
for a target or task. A marginal message-entropy penalty does not by itself
measure conditional novelty, task sufficiency, or redundancy between messages.

## Mutual information

A dependence measure between random variables. Its interpretation depends on
which variables and conditioning set are used. Episode-latent/trajectory mutual
information is not a variable-duration or termination guarantee.

## Held-out `N`

Evaluation at a roster size excluded from policy fitting, normalization fitting,
hyperparameter selection, and threshold selection while using one shared frozen
parameterization. Merely running separate experiments at several `N` values is
not sufficient.

## Variable skill period `k`

One algorithm adapts when a skill/macro-action duration is externally changed or
chooses its duration/termination. Communication delay, optimizer timescale, or a
latent held for an entire fixed episode is not automatically this project axis.

## Evidence type

The epistemic status of a corpus row: formal theorem, proof technique, empirical
experiment, textbook synthesis, model definition, conceptual proposal, or
curator boundary/connection. Different types must not be silently pooled as if
they provide the same strength of support.
