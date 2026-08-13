# P11 — Model-Based RL for Mean-Field Games is not Statistically Harder than Single-Agent RL

## Identity and scope

- An ICML 2024 model-based theory paper defining Partial Model-Based Eluder Dimension (P-MBED) and a bridge-policy model-elimination algorithm for learning MFG Nash equilibria (PDF pp. 1–9).

## Problem formulation

- The learner knows a model class and samples finite-horizon mean-field dynamics; strategic exploration must identify a Nash policy without exploring the entire state-action-density space (PDF pp. 3–6).

## Actual contribution

- P-MBED measures the induced single-agent model complexity, MEBP alternates model elimination with bridge-policy exploration, and extensions cover multi-type MFGs; the paper also separates MFG from harder MFC (PDF pp. 4–9).

## Core objects and equations

- Key objects are model classes, policy-conditioned distances, local alignment, P-MBED, central-model neighborhoods, policy-aware MDPs, and bridge policies approximating a fixed point of the central-model map (PDF pp. 4–8).

## Algorithms or mechanism primitives

- Algorithm 1 performs Model Elimination via Bridge Policy; Algorithms 2–3 eliminate policy-conditioned models and construct a bridge PAM/policy; the practical appendix replaces exhaustive operations with heuristics (PDF pp. 6–8, 54–55).

## Assumptions and information structure

- Results assume realizability, Lipschitz mean-field transitions/rewards, a model class and sampling oracle, and access to costly optimization/NE subroutines; the main theorem algorithm can be computationally exponential (PDF pp. 3–9).

## Theorems and guarantees

- Theorems 4.1/4.5 and F.7 give sample complexity polynomial in P-MBED and accuracy; Theorem F.9 supplies an exponential MFC lower-bound instance; Theorem 5.2 extends to multi-type MFGs (PDF pp. 5–9, 32–45).

## Experiments and evaluation protocol

- Only the heuristic computational variant is evaluated, with details deferred to Appendix J; this empirical result does not validate the intractable theorem algorithm end to end (PDF pp. 9, 54–55).

## Failure boundaries and non-claims

- 'Not statistically harder' is conditional on the model-based assumptions and P-MBED construction; it is not a claim of computational ease, arbitrary finite-player MARL, or frozen-policy cross-N robustness (PDF pp. 5–9).

## HMASD prospective connections

- P-MBED and bridge-policy exploration are prospective tools for choosing informative fleet-distribution probes, but HMASD would need a concrete model class, tractable oracle, finite-N bridge, and UAV observables (PDF pp. 4–8).

## Recommended reading route

- Read P-MBED on pp. 4–5, MEBP and the MFG/MFC contrast on pp. 5–8, the multi-type extension on pp. 8–9, then formal bounds and lower bound in pp. 26–45.

## Source-page anchors

- P-MBED (PDF pp. 4–5); main algorithm (pp. 5–8); MFC separation (p. 6); multi-type result (pp. 8–9); formal proofs (pp. 26–45); heuristic experiment (pp. 54–55).
