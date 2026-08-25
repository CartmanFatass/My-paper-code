# Poincare Recurrence, Cycles and Spurious Equilibria in Gradient-Descent-Ascent for Non-Convex Non-Concave Zero-Sum Games

## Identity and scope

This NeurIPS 2019 paper analyzes gradient-descent-ascent in a restricted but expressive family of hidden bilinear non-convex/non-concave zero-sum games motivated by indirect parameter competition in GANs. (PDF pages 1-3)

## Problem formulation

Players choose parameters passed through smooth nonlinear maps F and G, while payoffs are bilinear in their outputs; the paper studies continuous and discrete GDA rather than generic MARL policies. (PDF pages 2-5)

## Actual contribution

The analysis constructs conservation laws and reductions showing periodic or Poincare-recurrent motion for safe initializations, plus positive-measure attraction to spurious non-minmax fixed points for other constructions. (PDF pages 3; 5-8)

## Core objects and equations

Core objects are hidden bilinear payoff r(theta,phi)=F(theta)^T U G(phi), continuous/discrete GDA flows, attainable-value sets, safe initializations, invariant H, and volume-preserving transformed flows. (PDF pages 2; 5-8)

## Algorithms or mechanism primitives

The paper is chiefly a failure-mode analysis: trajectory reparameterization, invariant construction, Poincare-Bendixson/recurrence arguments, and time averaging are the reusable analytical primitives. (PDF pages 5-8)

## Assumptions and information structure

Periodicity results require a 2x2 hidden bilinear zero-sum game with an interior mixed Nash equilibrium and safe initialization; higher-dimensional recurrence further assumes separable coordinate maps and, for Theorem 7, sigmoid or related one-to-one maps. (PDF pages 5-8)

## Theorems and guarantees

Theorems 2-4 give an invariant, periodic orbits, and convergence of time-averaged outputs/payoffs in the two-strategy case; Theorems 6-7 give recurrence results; Theorems 8 and 10 construct spurious equilibria; Theorem 9 gives nondecreasing energy in discrete time. (PDF pages 6-8)

## Experiments and evaluation protocol

There is no benchmark experiment or statistical protocol. Figure 1 visualizes trajectories consistent with Theorem 7; the main evidence is formal analysis and constructed examples. (PDF page 3)

## Failure boundaries and non-claims

The results do not cover every non-convex/non-concave game, every GAN architecture, or general-sum MARL; they are bounded to hidden bilinear zero-sum structure and stated initialization/map conditions. (PDF pages 2-8)

## HMASD prospective connections

Curator connection (prospective): monitor cycling, conserved quantities, and initialization-dependent spurious stationarity when an HMASD optimizer has a locally adversarial or rotational component; this paper alone does not validate a repair. (PDF pages 3; 6-8)

## Recommended reading route

Read the hidden-bilinear definition and results overview, then the safe-initialization reduction and Theorems 2-4, followed by recurrence and spurious/discrete-time results. (PDF pages 2-3; 5-8)

## Source-page anchors

Model equation (2) is on PDF page 2; two-strategy GDA and safe initialization on pages 5-6; higher-dimensional recurrence and negative results on pages 7-8. (PDF pages 2-8)
