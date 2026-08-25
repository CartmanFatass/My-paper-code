# Navigation by HMASD research axis

This navigator separates source-supported ingredients from project claims that
still require direct experiments. Links open the paper overview.

## Variable roster size `N`

### Strongest theoretical anchors in this corpus

- [P14 - Mean-field controls with Q-learning for cooperative MARL](papers/P14/overview.md): one homogeneous/interchangeable population-conditioned policy and an assumption-bound finite-`N` approximation of order `N^-1/2`; this is the closest source to a shared cross-population control rule.
- [P12 - Graphon mean-field control](papers/P12/overview.md): dense nonuniform interaction limits and label/block-conditioned policy ensembles; useful when heterogeneity has stable graphon structure.
- [P22 - Accuracy of graphon particle approximations](papers/P22/overview.md): finite-time dynamics approximation, including an `O(1/N)` object under its own assumptions; it is not a learned-policy or return guarantee.
- [P21 - Large-population stochastic dynamic games](papers/P21/overview.md): foundational large-population/Nash-certainty-equivalence construction.

### Architectural and empirical ingredients

- [B01 - MARL foundations](papers/B01/overview.md): identical-policy parameter sharing and its strong-homogeneity boundary.
- [P08 - Mean-field MARL](papers/P08/overview.md): mean-action aggregation with `N`-independent input dimension; multiple fixed-size experiments are not necessarily one frozen-policy held-out-`N` test.
- [P09 - Model-free mean-field RL](papers/P09/overview.md): mean-field MDP/Q-learning interface.
- [P10 - Policy mirror ascent in MFGs](papers/P10/overview.md): independent learning with a finite-population mean-field term.
- [P24 - Non-stationary continuous mean-field games](papers/P24/overview.md): continuous population dynamics and nonstationarity, not arbitrary finite-player MARL.

### Required HMASD evidence not supplied by the literature

One shared frozen parameterization must be trained without the held-out roster,
then evaluated at the held-out `N` with matched physical time, samples, model
capacity, communication, inference work, and normalization. Within-episode
membership change requires a separate churn intervention. None of the sources
alone supplies that project result.

## Variable skill period `k`

### Nearest ingredients

- [P17 - MAVEN](papers/P17/overview.md): a shared latent mode persists for an entire episode and promotes committed exploration. This is not an externally changed or chosen skill period.
- [B03 - Dec-POMDPs](papers/B03/overview.md): formal temporal information structures, including communication considerations; a `k`-step delay is not skill duration.
- [P16 - HATRPO](papers/P16/overview.md): sequential agent updates and trust regions; update order/timescale is not a variable macro-action period.
- [P24 - Non-stationary MFG dynamics](papers/P24/overview.md): temporal population change, not option termination.

### Corpus boundary

The checked library contains no direct theorem or algorithm for one shared
policy adapting to held-out external skill periods or choosing termination. A
variable-`k` proposal must define primitive time, decision opportunities,
duration/termination action support, physical-time discounting/cost, and a
held-out-`k` protocol directly.

## Communication and information structure

- [B03 - Dec-POMDPs](papers/B03/overview.md): local histories and the exact information available to decentralized policies.
- [P15 - IMAC](papers/P15/overview.md): task-coupled communication compression through an information bottleneck and a covariance-determinant entropy upper bound.
- [P17 - MAVEN](papers/P17/overview.md): trajectory/latent mutual information for diverse coordinated exploration.
- [B01 - MARL foundations](papers/B01/overview.md): communication, parameter sharing, CTDE, and homogeneity context.

Do not infer conditional novelty, semantic duplicate rejection, or statistical
sufficiency from a marginal message-entropy penalty. Those require an explicit
conditioning set, decision target, and matched communication intervention.

## Credit, exploration, and coordinated policy learning

- [P17 - MAVEN](papers/P17/overview.md): shared latent exploration modes and trajectory mutual information.
- [P16 - HATRPO](papers/P16/overview.md): sequential multi-agent trust-region updates limiting cross-agent policy-update interference.
- [P15 - IMAC](papers/P15/overview.md): joint task objective plus communication information regularization.
- [P02](papers/P02/overview.md), [P03](papers/P03/overview.md), and [P13](papers/P13/overview.md): policy optimization under potential-game structure.

These sources provide learning primitives, not evidence that any primitive
handles roster churn or skill-duration changes.

## Learning dynamics and optimization stability

- [P04 - Recurrence, cycles, and spurious equilibria](papers/P04/overview.md): negative results in a restricted hidden bilinear zero-sum construction.
- [P05 - Dual extrapolation](papers/P05/overview.md): foundational monotone variational-inequality method.
- [P06 - Rotational MARL dynamics](papers/P06/overview.md): MARL-focused VI/lookahead/extragradient study.
- [P07 - Variance-reduced verified stochastic VI](papers/P07/overview.md): recent preprint; preserve its assumptions and provisional status.
- [P16 - HATRPO](papers/P16/overview.md): monotonic-improvement-inspired sequential trust-region machinery.

Optimization stability is a mechanism or enabling condition. It is not itself a
variable-`N`/`k` result unless the stabilized shared policy passes the matched
held-out-axis experiment.

## Planning, equilibrium, and sample complexity

- [B02 - Multiagent systems](papers/B02/overview.md): game theory, mechanisms, and multi-agent reasoning.
- [B03 - Dec-POMDPs](papers/B03/overview.md): cooperative planning with decentralized information.
- [P19 - Q-learning rates](papers/P19/overview.md): finite-time single-agent Q-learning analysis.
- [P20 - Independent linear function approximation in Markov games](papers/P20/overview.md): refined Markov-game sample complexity.
- [P25 - The power of an exploiter](papers/P25/overview.md): large-state two-player zero-sum Markov games.
- [P11 - Model-based RL for MFGs](papers/P11/overview.md): mean-field-game sample-complexity structure.

Always check the game class and information model before transferring a rate or
complexity statement into cooperative HMASD.

## UAV-transfer ingredients

The corpus supplies ingredients rather than a UAV validation result:

- population summaries and graph limits for large fleets: P08/P12/P14/P22;
- decentralized local-history constraints: B03;
- communication compression: P15;
- persistent coordinated modes: P17;
- stable multi-agent update mechanisms: P05/P06/P16; and
- continuous/nonstationary population modeling: P24.

A UAV bridge must still name the simulator, roster or skill-period intervention,
observations/actions, communication topology, matched baseline, failure mode,
and mission-level robustness or performance endpoint.
