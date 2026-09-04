# Navigation by theorem and evidence type

Use this file when the epistemic status of a statement matters more than its
topic. The per-paper claim index retains theorem labels, assumptions, empirical
protocols, and boundaries with PDF-page anchors.

## Textbooks, model definitions, and broad synthesis

- [B01 - MARL foundations](papers/B01/overview.md): modern synthesis plus illustrative experiments; inspect its stated scope and homogeneity caveats.
- [B02 - Multiagent systems foundations](papers/B02/overview.md): broad game-theoretic, algorithmic, and logical treatment.
- [B03 - Dec-POMDPs](papers/B03/overview.md): formal decentralized planning model and algorithms.
- [P01 - What is the multi-agent learning question?](papers/P01/overview.md): conceptual taxonomy and evaluation discipline.

## Formal positive convergence, approximation, or complexity results

- [P02](papers/P02/overview.md): last-iterate convergence of independent natural policy gradient under Markov-potential-game assumptions.
- [P03](papers/P03/overview.md): independent policy-gradient analysis for large-player Markov potential games.
- [P05](papers/P05/overview.md): dual extrapolation under variational-inequality structure.
- [P09](papers/P09/overview.md): model-free mean-field reinforcement-learning analysis.
- [P10](papers/P10/overview.md): policy mirror ascent in mean-field games with a finite-population term.
- [P11](papers/P11/overview.md): model-based mean-field-game sample complexity.
- [P12](papers/P12/overview.md): graphon mean-field-control approximation and near-optimality under dense-graph convergence.
- [P13](papers/P13/overview.md): entropy-regularized natural policy gradient and quantal-response equilibrium.
- [P14](papers/P14/overview.md): `O(N^-1/2)` cooperative-MARL/MFC approximation and `N`-independent MFC learning complexity under explicit assumptions.
- [P19](papers/P19/overview.md): finite-time tabular Q-learning rates.
- [P20](papers/P20/overview.md): refined sample complexity with independent linear function approximation in Markov games.
- [P21](papers/P21/overview.md): large-population stochastic-game/Nash-certainty-equivalence formulation.
- [P22](papers/P22/overview.md): graphon approximation for uncontrolled interacting particles; do not relabel the bound as a policy guarantee.
- [P25](papers/P25/overview.md): exploiter-based guarantees in large-state two-player zero-sum Markov games.

## Formal negative results or concrete failure constructions

- [P04 - Recurrence, cycles, and spurious equilibria](papers/P04/overview.md): rigorous failure behavior for a restricted hidden bilinear zero-sum class.

The restriction is part of the result. It is not a theorem that every
nonconvex-nonconcave MARL problem cycles.

## Method papers with empirical support

- [P06 - Rotational learning dynamics in MARL](papers/P06/overview.md)
- [P08 - Mean-field MARL](papers/P08/overview.md)
- [P12 - Graphon MFC](papers/P12/overview.md) also includes computational examples; keep them separate from its theorems.
- [P15 - Information-bottleneck communication](papers/P15/overview.md)
- [P16 - HATRPO](papers/P16/overview.md)
- [P17 - MAVEN](papers/P17/overview.md)
- [P24 - DEDA-FP for non-stationary continuous MFGs](papers/P24/overview.md)

For cross-`N` use, check whether one frozen policy was actually trained without
and then evaluated at the target roster. Multiple fixed-size experiments alone
do not establish that protocol.

## Recent preprints requiring extra caution

- [P06](papers/P06/overview.md): 2025 arXiv/workshop-stage rotational-MARL work.
- [P07](papers/P07/overview.md): 2026 arXiv v1 stochastic VI method; theorem assumptions and peer-review status must remain visible.
- [P24](papers/P24/overview.md): 2025 NeurIPS/arXiv continuous-MFG work; preserve its actual game class.

Recency is neither a defect nor validation. Avoid converting a new theorem under
narrow assumptions into established general MARL practice.

## Conceptual or position-paper evidence

- [P18 - Optimal transport and MARL](papers/P18/overview.md): proposes a synergy and research agenda; it does not supply decisive empirical or theorem-level validation of an OT-based MARL algorithm.

## How to use the claim index

Filter [`claim_index.jsonl`](claim_index.jsonl) by:

- `claim_kind=source_claim` for an author theorem/method/empirical statement;
- `claim_kind=source_scope` for the actual model or evaluation population;
- `claim_kind=curator_boundary` for a precisely bounded non-inference; and
- `evidence_type` to separate theorem, proof, experiment, definition,
  synthesis, or conceptual proposal.

Retain `conditions`, `limits`, theorem/proposition label, and `pdf_pages` in any
downstream LLM synthesis.
