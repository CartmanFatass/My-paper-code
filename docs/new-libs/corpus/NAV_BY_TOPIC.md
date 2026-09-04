# Navigation by topic

This is the broadest human-facing map. Use the linked overview for orientation,
then follow its claim/chunk links for source-page evidence.

## MARL problem formulations and evaluation discipline

- [P01 - If multi-agent learning is the answer, what is the question?](papers/P01/overview.md): distinguishes several learning agendas and asks what should count as success.
- [B01 - MARL: Foundations and Modern Approaches](papers/B01/overview.md): broad modern treatment of cooperative/competitive learning, CTDE, parameter sharing, communication, and evaluation.
- [B02 - Multiagent Systems](papers/B02/overview.md): algorithmic, game-theoretic, and logical foundations.
- [B03 - Dec-POMDPs](papers/B03/overview.md): formal cooperative planning under decentralized observations and local histories.

## Cooperative learning and value decomposition

- [P17 - MAVEN](papers/P17/overview.md): representation-induced exploration failure, episode-persistent latent modes, and trajectory-latent mutual information.
- [P16 - HATRPO](papers/P16/overview.md): sequential multi-agent policy updates with trust-region constraints.
- [P15 - IMAC](papers/P15/overview.md): learned communication compression tied to task value.
- [B01](papers/B01/overview.md): broader value-decomposition, actor-critic, CTDE, and communication context.

## Large populations and mean-field approximation

- [P21 - Large-population stochastic dynamic games](papers/P21/overview.md): foundational large-population limit and Nash-certainty-equivalence ideas.
- [P08 - Mean-field MARL](papers/P08/overview.md): representative-agent/mean-action approximation for practical many-agent learning.
- [P09 - Model-free mean-field RL](papers/P09/overview.md): mean-field MDP and Q-learning formulation.
- [P10 - Policy mirror ascent in MFGs](papers/P10/overview.md): independent single-trajectory mean-field-game learning.
- [P11 - Model-based RL for MFGs](papers/P11/overview.md): model-based sample complexity in mean-field games.
- [P14 - Mean-field control Q-learning for cooperative MARL](papers/P14/overview.md): finite cooperative-MARL/MFC bridge and `N`-independent learning complexity under interchangeability.
- [P24 - Non-stationary continuous MFGs](papers/P24/overview.md): deep RL for continuous, time-varying population dynamics.

## Graphons and nonuniform population interaction

- [P12 - Graphon mean-field control](papers/P12/overview.md): dense nonuniform interaction limits, label/block policy ensembles, and finite-agent approximation.
- [P22 - Accuracy of graphon mean-field approximation](papers/P22/overview.md): finite-time expected particle-dynamics approximation, not a learned control result.
- [P24](papers/P24/overview.md): continuous/nonstationary mean-field dynamics, useful as a contrasting population model.

## Potential games and equilibrium-oriented policy optimization

- [P02 - Independent natural policy gradient in Markov potential games](papers/P02/overview.md): last-iterate convergence under MPG structure.
- [P03 - Independent policy gradient for large-scale MPGs](papers/P03/overview.md): many-player policy-gradient analysis and function approximation.
- [P13 - Entropy-regularized NPG and QRE](papers/P13/overview.md): regularized potential games and smooth equilibrium concepts.
- [B02](papers/B02/overview.md): equilibrium and game-theoretic prerequisites.

## Cycles, rotational dynamics, and variational inequalities

- [P04 - Recurrence, cycles, and spurious equilibria](papers/P04/overview.md): concrete negative phenomena in a restricted hidden bilinear zero-sum class.
- [P05 - Dual extrapolation](papers/P05/overview.md): classical method for monotone variational inequalities.
- [P06 - Rotational learning dynamics in MARL](papers/P06/overview.md): VI/lookahead/extragradient methods targeted at MARL rotation.
- [P07 - Breaking the stochasticity barrier](papers/P07/overview.md): variance-reduced and verified stochastic VI proposal; recent-preprint boundaries apply.

## Communication, bandwidth, and information

- [P15 - Information-bottleneck communication](papers/P15/overview.md): message entropy/bandwidth versus task usefulness, learned encoding and scheduling.
- [B03 - Decentralized information structure](papers/B03/overview.md): what each executing agent can condition on.
- [P17 - Latent/trajectory mutual information](papers/P17/overview.md): committed exploration rather than message sufficiency.
- [B01](papers/B01/overview.md): broader communication methods and parameter-sharing context.

## Exploration and temporal commitment

- [P17 - MAVEN](papers/P17/overview.md): temporally extended exploration through an episode-level latent.
- [P01](papers/P01/overview.md): evaluation questions that help distinguish adaptation, equilibrium learning, and coordination.
- [P16](papers/P16/overview.md): policy-update coordination; not a temporal-abstraction algorithm.

The library has no direct variable-skill-period theorem. An episode-fixed latent,
communication delay, or optimizer timescale must not be relabeled as adaptive
skill duration.

## Sample complexity and large state spaces

- [P19 - Learning rates for Q-learning](papers/P19/overview.md): finite-time tabular single-agent analysis.
- [P20 - Markov games with independent linear function approximation](papers/P20/overview.md): refined sample complexity for the stated Markov-game setting.
- [P25 - The power of an exploiter](papers/P25/overview.md): provable learning in large-state two-player zero-sum Markov games.
- [P11 - Model-based MFG learning](papers/P11/overview.md): statistical complexity in a mean-field-game model class.
- [P14](papers/P14/overview.md): MFC learning complexity and finite cooperative-MARL approximation under explicit assumptions.

## Optimal transport and geometric population ideas

- [P18 - Optimal transport and MARL](papers/P18/overview.md): conceptual synergy and proposed uses of Wasserstein geometry; treat as an agenda, not validation.
- [P12 - Graphon MFC](papers/P12/overview.md): population geometry through a graph limit.
- [P24 - Continuous MFGs](papers/P24/overview.md): continuous population distributions and nonstationarity.

## Variable `N` and roster robustness

Start with [B01](papers/B01/overview.md), [P08](papers/P08/overview.md),
[P14](papers/P14/overview.md), and [P12](papers/P12/overview.md), then read
[the HMASD-axis navigator](NAV_BY_HMASD_AXIS.md). These sources motivate shared
or population-conditioned policies, but direct held-out-`N` and in-episode churn
tests remain necessary.

## Variable skill period `k`

The nearest sources are [P17](papers/P17/overview.md) for persistent coordinated
modes and [B03](papers/B03/overview.md) for temporal information constraints.
Neither establishes the project axis. A new treatment must define duration or
termination, physical-time matching, and held-out `k` itself.
