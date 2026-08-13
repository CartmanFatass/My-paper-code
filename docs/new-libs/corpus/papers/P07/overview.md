# P07 — Breaking the Stochasticity Barrier: An Adaptive Variance-Reduced Method for Variational Inequalities

## Identity and scope

- A February 2026 unreviewed preprint proposing VR-SDA-A for stochastic, potentially non-monotone variational inequalities; MARL appears as a motivating application rather than an evaluated MARL domain (PDF pp. 1–8).

## Problem formulation

- The target is an ε-stationary zero of an expected operator V, measured by E||V(z)||², in the presence of rotation and bounded stochastic-oracle noise (PDF pp. 1, 3–4).

## Actual contribution

- VR-SDA-A couples a STORM recursive estimator to a same-batch local-curvature acceptance test and analyzes a Lyapunov potential combining operator norm and estimator error (PDF pp. 5–6).

## Core objects and equations

- Core equations are the stochastic operator, merit M(z)=||V(z)||²/2, recursive estimator d_t, same-batch curvature inequality, and composite potential Φ_t (PDF pp. 3–6).

## Algorithms or mechanism primitives

- The method adapts step size only after checking operator change on the same batch used for the direction, aiming to prevent noise from masquerading as safe curvature (PDF p. 5; Algorithm 1 on PDF p. 11).

## Assumptions and information structure

- The analysis assumes Lipschitz V, Lipschitz Jacobian, an unbiased bounded-variance mean-square-smooth oracle, local variational stability μ>0, and a bounded region/iterates discussion (PDF pp. 4–5).

## Theorems and guarantees

- Theorem 4 states a T^{-2/3} bound on the minimum expected squared operator norm and O(ε^{-3}) oracle complexity under Assumptions 1–3 and coupled momentum/stepsize (PDF p. 6; full proof PDF p. 12).

## Experiments and evaluation protocol

- Representative results over five seeds cover a bilinear rotational system and nonconvex robust regression; the bilinear μ=0 case is explicitly outside the strict theorem and functions as a stress test (PDF pp. 6–8).

## Failure boundaries and non-claims

- The formal result needs dissipativity/local variational stability, so it does not prove convergence for pure rotation; it also provides no direct MARL benchmark, variable-N, or variable-k evidence (PDF pp. 4, 6–8).

## HMASD prospective connections

- The same-batch curvature gate is a prospective adaptive optimizer primitive for noisy HMASD saddle dynamics; it would require a MARL-specific operator, cost accounting for extra oracle calls, and matched baselines (PDF pp. 5–6).

## Recommended reading route

- Read the SVI definition and assumptions on pp. 3–5, the method and theorem on pp. 5–6, then the theorem-scope caveat and experiments on pp. 4, 6–8.

## Source-page anchors

- SVI and merit (PDF pp. 3–4); assumptions and pure-rotation boundary (p. 4); VR-SDA-A (p. 5); Theorem 4 and complexity (p. 6); experiments (pp. 6–8); proof (pp. 11–12).
