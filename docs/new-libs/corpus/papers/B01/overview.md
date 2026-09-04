# B01 — Multi-Agent Reinforcement Learning: Foundations and Modern Approaches

Rebuilt 2026-09-02 from `docs/new-libs/papers/B01_Albrecht_MARL_Foundations_2024.pdf`
(pdfTeX build dated 2026-03-24; sha256 `4eec7be5cbabaf912846ddd295925c35d46502d92fcd9f7ba3311656fd2e9091`,
matching `metadata.json.content_fingerprint`), 395 pages, 85 chunks, 194 outline entries.
Supersedes the prior thin entry (67 chunks, 6 claims); see `_partials/b01_rebuild_qa.md`.

## Identity and scope

Albrecht, Christianos, and Schäfer's *Multi-Agent Reinforcement Learning: Foundations
and Modern Approaches* (MIT Press, 2024) is an open-access graduate textbook, based on
a 2017 IJCAI tutorial, covering MARL models, solution concepts, foundational (tabular)
algorithms, and modern deep-learning-based algorithms (Preface, p. 27-29). It ships an
accompanying PyTorch codebase (github.com/marl-book/codebase; p. 45, 334-347). The PDF
is a CC BY-NC-ND edition; using it to train AI systems requires separate written MIT
Press permission (p. 7-12). The book is organized in two parts: Part I, "Foundations of
Multi-Agent Reinforcement Learning" (Ch. 2-6, p. 46-187), and Part II, "Multi-Agent Deep
Reinforcement Learning: Algorithms and Practice" (Ch. 7-11 plus Appendix A, p. 188-369),
followed by References (p. 370-391) and an Index (p. 392-395). The authors explicitly
scope the book to Shoham, Powers, and Grenager's (2007) computational and prescriptive
MARL agendas, excluding the descriptive agenda (modeling natural/biological learning,
p. 42-44), and state they do not cover learning to communicate over noisy/unreliable
channels, learned communication protocols, or evolutionary game theory (p. 27).

## Problem formulation

MARL problems are posed as a game model (Chapter 3) plus a solution concept (Chapter 4)
(Figure 4.1, p. 91). The game-model hierarchy is normal-form game ⊂ repeated normal-form
game ⊂ stochastic game ⊂ partially observable stochastic game (POSG), each a strict
generalization, with MDPs as the single-agent special case (p. 72-89). Reward structure
is classified zero-sum, common-reward, or general-sum (p. 74). Solution concepts form a
second hierarchy — best response underlies minimax (two-agent zero-sum, p. 94-96), Nash
equilibrium (general-sum, p. 97-99), and (coarse) correlated equilibrium (p. 100-104) —
plus refinements (Pareto optimality p. 105-107, welfare/fairness p. 107-109) and an
alternative, no-regret (p. 109-112). All definitions assume finite game models (p. 90).
The book states a standing assumption of a fixed, commonly-known agent count throughout,
explicitly placing open/variable-agent-count environments outside its scope, citing only
external prior work (p. 87).

## Actual contribution

The book is a synthesis and pedagogical integration, not a single new algorithm or
theorem: it derives selected results (Bellman recursions, contraction-mapping DP
convergence, welfare-implies-Pareto, GIGA's regret bound) while attributing existence
and convergence theorems to their sources (von Neumann 1928; Nash 1950; Shapley 1953;
Hart and Mas-Colell 2000; among others; p. 94-183). Its contribution is a common notation
(p. 16-18) and a continuous route from single-agent MDPs (Ch. 2) through game models and
solution concepts (Ch. 3-4), tabular MARL algorithms (Ch. 6), deep learning/deep RL
(Ch. 7-8), deep MARL (Ch. 9), implementation practice (Ch. 10), and environments (Ch. 11).

## Core objects and equations

Core objects: MDP/stochastic-game/POSG tuples (p. 51, 76-77, 80); value/action-value
functions Vπ, Qπ and the Bellman equation (p. 55-57); expected return Ui(π) for the POSG
model, history-based and recursive forms (Eq. 4.1-4.8, p. 91-93); best response BRi
(Eq. 4.9, p. 94); minimax/Nash/(coarse) correlated equilibrium definitions (Eq.
4.10-4.24, p. 95-104); regret (Eq. 4.28-4.30, p. 110-112); the joint-action space size
|A|=|A1|·...·|An| (Eq. 5.11, p. 137); the multi-agent policy gradient theorem (Eq. 9.9,
p. 260-261); the individual-global-max (IGM) property (Eq. 9.25, p. 274); VDN's linear
and QMIX's monotonic decompositions (Eq. 9.26-9.30, 9.46-9.47, p. 275-283); weak/strong
agent-homogeneity definitions (Eq. 9.86, Definitions 14-15, p. 304). Every displayed
equation on a page carrying a numbered-equation line risks the book's one systematic
extraction defect: Σ/Π big-operator glyphs extract as ordinary Latin letters (e.g.
"P_{a'∈A}" for "Σ_{a'∈A}" on p. 226) — flagged `equation_text_unreliable` on 50 of 85
chunks (see `qa/EXTRACTION_WARNINGS.md`); prose and equation *numbers* are reliable, but
reproduced equation bodies must be checked against the source page.

## Algorithms or mechanism primitives

Tabular (Part I, Ch. 6): value iteration for stochastic games (Algorithm 6, p. 146);
joint-action learning (JAL-GT, Algorithm 7, p. 149) instantiated as minimax/Nash/
correlated Q-learning (p. 150-153); fictitious play (p. 157-159) and JAL-AM (Algorithm 8,
p. 161); Bayesian value-of-information learning (p. 163-169); IGA/WoLF-IGA/WoLF-PHC/GIGA
policy-gradient dynamics (p. 169-180); regret matching (p. 180-185). Deep (Part II):
DQN built up from deep Q-learning through target networks and replay to DDQN (Algorithms
10-12, p. 213-223); REINFORCE, A2C, PPO (Algorithms 13-16, p. 229-243); independent deep
learning (IDQN/Independent REINFORCE/IA2C, Algorithms 17-19, p. 254-258); centralized
critics and COMA-style counterfactual credit assignment (Algorithm 20, p. 263-269) and
Pareto actor-critic (p. 269-270); VDN and QMIX (Algorithms 21-22, p. 278-283) and QTRAN/
QPLEX/FACMAC/weighted-QMIX successors (p. 290-295); deep agent modeling (Algorithm 23,
p. 298; encoder-decoder representations, p. 300-302); parameter sharing (Eq. 9.87,
p. 305-306) and experience sharing (Algorithm 24, SEAC, p. 307-310); self-play MCTS and
AlphaZero (Algorithm 25, p. 313-318); population-based training via PSRO (Algorithm 26,
p. 321-323) and AlphaStar's League training (p. 326-329).

## Assumptions and information structure

The book separates training-time from execution-time information via the CTE/DTE/CTDE
taxonomy (p. 249-251), and states a critic is "centralized" if it conditions on anything
beyond the acting agent's own observation/action history, with the minimum requirement
that it see at least what the actor sees to avoid bias (Lyu et al. 2023, cited p.
262-263). The default MARL knowledge assumption is that agents know neither their own
nor other agents' reward, transition, or observation functions, unlike classical
"complete knowledge" game theory (p. 85-86). Communication is modeled as an action split
Ai=Xi×Mi, observable but, by construction, not affecting state transitions (Eq. 3.6-3.7,
p. 83-85). Weak agent homogeneity (returns invariant to relabeling agents and policies
together) and strong homogeneity (additionally, identical optimal policies across agents)
are the formal preconditions for experience sharing and parameter sharing respectively
(Eq. 9.86, Definitions 14-15, p. 304-309). Policy self-play additionally requires
symmetric roles and egocentric observations (p. 315-316).

## Theorems and guarantees

Existence: minimax solutions exist in finite two-agent zero-sum normal-form games (von
Neumann 1928/1944) and stochastic games (Shapley 1953), p. 94-95; Nash equilibria exist
in finite normal-form games (Nash 1950, p. 97) and stochastic games (Fink 1964, p. 98).
Convergence: value iteration converges via the Banach fixed-point/γ-contraction argument
(p. 146-147); Sarsa/Q-learning converge under infinite visitation plus Robbins-Monro
step sizes (p. 62-65); IGA/WoLF-IGA provably converge only for normal-form games with
exactly two agents and two actions (p. 133, 172-176); GIGA achieves no-regret with an
explicit bound (Eq. 6.52, p. 180); regret matching's average regret is bounded by κ/√z,
implying empirical-distribution (not pointwise) convergence to (coarse) correlated
equilibria (p. 182-185). Structural: any linear decomposition satisfies IGM (proved both
directions, p. 275-277); QMIX's strict-monotonicity is sufficient for IGM, with a
footnote counterexample for the non-strict case (p. 279-282); Son et al.'s QTRAN
conditions are necessary and sufficient for IGM under affine rescaling but are enforced
only asymptotically during training, not throughout (p. 290-294). Hardness: computing an
equilibrium with an added optimality/support property is NP-hard (Gilboa and Zemel 1989;
Conitzer and Sandholm 2008, p. 113); computing (ε-)Nash equilibrium is PPAD-complete
(Daskalakis, Goldberg, and Papadimitriou 2006/2009; Chen and Deng 2006, p. 115-116) — the
authors draw the explicit implication that MARL is unlikely to be a general
polynomial-time "magic bullet" for Nash computation absent exploitable structure (p. 116).

## Experiments and evaluation protocol

Nearly every algorithm family is illustrated on level-based foraging (LBF) at a fixed,
small agent count: CQL vs. IQL at N=2 (p. 128-130); JAL-AM vs. IQL/CQL at N=2, 50 runs
(p. 161-162); IA2C scaling to a 15×15 grid, N∈{2,3} (p. 257-259); VDN/QMIX/IDQN
comparisons, 5 seeds (p. 289-290); parameter-sharing ablations at N=3 (p. 305-306).
Matrix-game illustrations (Rock-Paper-Scissors, Prisoner's Dilemma, Chicken, Stag Hunt,
Climbing) recur throughout Ch. 4-6 and 9 as minimal worked examples, not statistical
studies. Large-scale results are cited from external papers, not reproduced: minimax-Q
vs. IQL on Littman's (1994) soccer game (p. 150-151); AlphaZero's match record against
Stockfish/Elmo/AlphaGo Zero (p. 319); AlphaStar reaching Grandmaster level (Vinyals et
al. 2019, p. 326-330). Chapter 10 gives the book's own evaluation methodology: learning
curves need regular-interval evaluation averaged with standard error across seeds
(p. 345); naive curves are uninformative in zero-sum games because both agents' apparent
improvement can cancel (Figure 10.2, p. 346); a thorough, equal-budget hyperparameter
search across seeds is recommended (p. 347). Chapter 11 catalogs environments and their
observability/action/reward-density properties (Figure 11.1, p. 353) without adjudicating
among them.

## Failure boundaries and non-claims

The authors name four central MARL challenges — non-stationarity, equilibrium selection,
multi-agent credit assignment, and scaling to many agents (p. 41-43, 130-138) — as open,
not solved by any algorithm in the book. VDN misrepresents monotonic-game values though
it can still reach the optimal policy greedily (p. 285-286); both VDN and QMIX fail to
reach the Climbing game's optimum (p. 288-289). COMA is reported empirically unstable/
high-variance despite an unbiased-in-expectation counterfactual baseline (p. 268-269).
Difference rewards require a default "no-op" action whose existence the authors call
"generally unclear" (p. 137).
Self-play as defined is restricted to two-agent, zero-sum, (near-)symmetric-role settings
(p. 310-316); its generalization to non-symmetric roles is a separate mechanism,
population-based training (p. 319-321), whose PSRO convergence proof assumes exact
meta-games and best-response oracles the authors say will "likely not hold in practice"
(p. 325). Every cited convergence guarantee for concurrent-learning dynamics (IGA,
WoLF-IGA) is scoped to two agents, two actions (p. 133, 175); every value-decomposition
and parameter-sharing experiment fixes agent count at 2 or 3, with no held-out- or
varying-N evaluation reported anywhere (p. 128-130, 161-162, 257-259, 283-290, 305-306).
Melting Pot's focal/background-agent protocol tests generalization to unfamiliar
co-players within a fixed task, narrower than held-out-N or held-out-k generalization
(p. 362).

## HMASD prospective connections

These are the merge team's prospective framings, not the book's own claims, and no HMASD
result is evidence for or against this book's content (see `claims.jsonl`: 7
`curator_connection` and 24 `curator_boundary` rows). Connections worth checking: the
CTDE taxonomy (p. 249-251) as the training/execution split HMASD's discriminator-
conditioned critic and decentralized skill policies occupy; the multi-agent policy
gradient theorem's centralized-critic form (Eq. 9.9, p. 260-261) and COMA's counterfactual
baseline (p. 267-268) as the closest textbook analogues to skill-conditioned credit
assignment; the IGM property (Eq. 9.25, p. 274) as the local-greedy-equals-global-greedy
consistency condition an N-agnostic skill/value mixer would need to preserve; weak/strong
homogeneity (p. 304) as the book's own formal test for whether a parameter-shared,
N-agnostic design is even valid for a given environment. Boundaries worth respecting: the
book's fixed-N assumption (p. 87) and its exclusively fixed-agent-count experiments
(p. 128-130, 257-259, 283-290) are not evidence for variable-N generalization; its narrow
(two-agent, two-action) convergence guarantees (p. 133, 175) should not be read as
scaling to general N; QTRAN's IGM property holds only asymptotically during training,
not as an enforced invariant (p. 292) — any HMASD claim of "IGM-preserving" mixing
modeled on QTRAN should preserve that distinction.

## Recommended reading route

(a) **Foundations**: Ch. 1 (p. 30-45) → Ch. 2 (p. 48-71) → Ch. 3 (p. 72-89) → Ch. 4
(p. 90-117) → Ch. 5 (p. 118-143). (b) **CTDE and value decomposition**: Section 9.1
(p. 249-251) → 9.4.1-9.4.2 (p. 260-265) → 9.4.4 (p. 266-269, COMA) → 9.5.1 (p. 273-275,
IGM) → 9.5.2-9.5.3 (p. 275-283, VDN/QMIX) → 9.5.5 (p. 290-295, QTRAN and successors).
(c) **Parameter sharing and homogeneity**: Section 9.3 (p. 252-258, independent learning
baseline) → 9.7 (p. 303-309, weak/strong homogeneity, parameter/experience sharing) →
10.2 (p. 336-339, PyTorch implementation). (d) **Evaluation practice and environments**:
Section 2.7 (p. 64-68, learning curves) → 10.6 (p. 345-347, fair comparison practice) →
Ch. 11 (p. 348-365, environment catalog). Readers already familiar with single-agent RL
may skip Ch. 2 and go Ch. 3 → Ch. 9 onward per the Preface's own stated fast path (p. 27).

## Source-page anchors

Front matter, notation, licensing: p. 1-29. Part I (foundations): p. 46-187 — RL
recap p. 48-71; game models p. 72-89; solution concepts p. 90-117; learning process and
challenges p. 118-143; foundational algorithms p. 144-187. Part II (deep MARL): p.
188-369 — deep learning p. 190-211; deep RL p. 212-247; deep MARL p. 248-333 (CTDE
p. 249-251; independent learning p. 252-258; policy gradient/COMA p. 259-270; value
decomposition p. 271-295; agent modeling p. 295-302; homogeneity/sharing p. 303-309;
self-play/population-based training p. 310-329; chapter summary p. 330-333);
implementation practice p. 334-347; environments p. 348-365; surveys p. 366-369.
References p. 370-391; Index p. 392-395. For the full outline-ordered, chunk-anchored
breakdown of every section (including the seven-reader entries this overview summarizes
and the References/Index entries built directly from `chunks.jsonl`), see
`SECTION_INDEX.md`.
