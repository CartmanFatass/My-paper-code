# B01 Section Index

## How to use this file

1. This file (`SECTION_INDEX.md`) is the entry point for every question about
   this book. Read it first; do not open chunk files speculatively.
2. Each entry below covers one outline section (chapter, x.y, or x.y.z as the
   readers judged chunk-worthy) with pages, owning chunk id(s), a summary, and
   what it defines/proves/shows.
3. To go deeper on one entry, open at most one or two of its listed chunk
   files (`papers/B01/chunks/<chunk_id>.md`) - not the whole chapter.
4. Every entry is page-anchored to the PDF (`docs/new-libs/papers/B01_...pdf`),
   not to the book's printed page numbers.
5. `equation_text_unreliable` (noted per-entry where applicable; see
   `qa/EXTRACTION_WARNINGS.md`) means large-operator glyphs (Σ, Π) extracted
   as ordinary Latin letters (e.g. "P" for Σ, "X"/"Y" for Σ/Π elsewhere) on
   pages with a numbered display equation - the prose and equation *numbers*
   are reliable, but any reproduced equation's operators must be checked
   against the source PDF page, not trusted from this index or from
   `chunks.jsonl`.
6. `hmasd: curator_connection` / `curator_boundary` rows are the merge team's
   own prospective framing, not the book's claims; `hmasd: none` means no
   connection was drawn for that entry. See `claims.jsonl` for the
   page-anchored, dedupe-checked claim inventory this index summarizes.
7. Section 9.5.5 (`Beyond Monotonic Value Decomposition`) straddles two
   readers' assigned ranges (pp. 290-294 and p. 295) and is merged into one
   entry below; two same-page section pairs (3.7/3.8 on p. 87 and 4.2/4.3 on
   p. 94) share a single owning chunk each, noted inline.
8. The book has no literal tables (confirmed by full-text scan); do not expect
   `table_text_unreliable` tags.
9. References (pp. 370-391) and the back-of-book Index (pp. 392-395) were not
   assigned to any of the seven readers and are built directly from
   `chunks.jsonl` at the end of this file - flagged as such in their entries.
10. For the four reading routes (foundations; CTDE and value decomposition;
    parameter sharing and homogeneity; evaluation practice and environments),
    see `overview.md`'s "Recommended reading route" section.

## Chapter table

| Chapter | PDF pages | Chunk range | One-line purpose | Prerequisites (as stated by the book) |
| --- | --- | --- | --- | --- |
| Front matter (Notation, Figures, Preface) | 16-29 | B01-C0004-B01-C0006 | Notation glossary, master figure list, and the book's own scope/reading-order statement. | Preface states Ch. 2/7/8 cover RL/deep-learning basics for unfamiliar readers; Ch. 3 then Ch. 9+ is the fast path for readers already familiar with RL. |
| 1 Introduction | 30-45 | B01-C0007-B01-C0010 | Frames MARL via applications and the size/knowledge/observability/rewards/objective/centralization dimensions; states the book covers the computational and prescriptive MARL agendas, not the descriptive one. | None stated as a prerequisite to Ch. 1 itself. |
| Part I: Foundations of MARL | 46-187 | B01-C0011-B01-C0042 | Single-agent RL -> game models -> solution concepts -> central/independent learning and challenges -> foundational (tabular) MARL algorithms. | Builds sequentially, Ch. 2 -> 3 -> 4 -> 5 -> 6, per Section 1.6. |
| 2 Reinforcement Learning | 48-71 | B01-C0011-B01-C0016 | Single-agent MDP foundations: value functions, Bellman equation, dynamic programming, TD learning (Sarsa/Q-learning), learning curves. | Recommended (not required) for readers unfamiliar with RL (Preface, p. 27); opens Part I (Section 1.6, p. 44). |
| 3 Games: Models of Multi-Agent Interaction | 72-89 | B01-C0017-B01-C0020 | Defines the game-model hierarchy (normal-form -> repeated -> stochastic -> POSG); models communication and knowledge assumptions; states it defines models only, not solution concepts. | Extends Ch. 2's MDP model to multiple agents (Section 1.6); readers already familiar with RL may start here and skip to Ch. 9 (Preface, p. 27). |
| 4 Solution Concepts for Games | 90-117 | B01-C0021-B01-C0026 | Builds the equilibrium hierarchy (best response -> minimax -> Nash -> (coarse) correlated), refinements (Pareto, welfare, fairness), no-regret, and PPAD-completeness of Nash computation. | Builds on Ch. 3's game models, in particular the POSG model of Section 3.4. |
| 5 MARL in Games: First Steps and Challenges | 118-143 | B01-C0027-B01-C0032 | Formalizes the MARL learning process and convergence types; introduces central/independent learning; states the four core MARL challenges (non-stationarity, equilibrium selection, credit assignment, scaling); self-play vs. mixed-play. | Builds on Ch. 4's solution concepts and Ch. 2's single-agent RL/TD background. |
| 6 MARL: Foundational Algorithms | 144-187 | B01-C0033-B01-C0042 | Four tabular MARL algorithm families: joint-action learning (value iteration, minimax/Nash/correlated Q-learning), agent modeling (fictitious play, JAL-AM, Bayesian VI), policy-based learning (IGA/WoLF-IGA/WoLF-PHC/GIGA), no-regret (regret matching). | Builds on Ch. 5 (learning process, convergence, challenges) and Ch. 4 (solution concepts); reuses Ch. 2's DP/TD machinery. |
| Part II: Multi-Agent Deep RL: Algorithms and Practice | 188-395 | B01-C0043-B01-C0085 | Deep learning and deep RL foundations, then deep MARL algorithms, implementation practice, and environments. | Section 1.6: Ch. 7 (deep learning) and Ch. 8 (deep RL) feed into Ch. 9 (deep MARL), then Ch. 10 (practice), then Ch. 11 (environments). |
| 7 Deep Learning | 190-211 | B01-C0043-B01-C0047 | Function approximation motivation; linear approximation; feedforward networks; gradient-based optimization/backprop; CNNs and RNNs. | "Explains all foundational concepts required to understand the following chapters" (p. 190); Ch. 8 and 9 build on it (p. 210). |
| 8 Deep Reinforcement Learning | 212-247 | B01-C0048-B01-C0054 | Builds deep Q-learning into DQN (target networks, replay, DDQN); policy gradient theorem through REINFORCE, actor-critic, A2C, PPO; RNN-conditioned partial observability. | "Naturally builds on the content of Chapters 2 and 7" (p. 212). |
| 9 Multi-Agent Deep Reinforcement Learning | 248-333 | B01-C0055-B01-C0072 | CTE/DTE/CTDE taxonomy; deep independent learning; multi-agent policy gradient with centralized/counterfactual critics; value decomposition (VDN/QMIX/QTRAN); neural agent modeling; parameter/experience sharing; policy self-play (AlphaZero) and population-based training (PSRO, AlphaStar). | Builds on Ch. 7 (deep learning), Ch. 8 (deep RL), and Part I's tabular MARL algorithms (esp. Sections 5.3 and 6.3), per the chapter's own opening paragraph (p. 248). |
| 10 MARL in Practice | 334-347 | B01-C0073-B01-C0075 | Walks the book's own PyTorch codebase: agent-environment interface, per-agent/shared networks, centralized critics, value decomposition, practical tips, fair result presentation. | Not stated in-range; implements algorithms defined in Ch. 8-9. |
| 11 Multi-Agent Environments | 348-365 | B01-C0076-B01-C0079 | Environment-selection criteria; the 78 structurally distinct 2x2 matrix games; seven complex environments (LBF, MPE, SMAC, RWARE, GRF, Hanabi, Overcooked); three environment collections (Melting Pot, OpenSpiel, Petting Zoo). | Builds on Ch. 3's game-model hierarchy (normal-form/stochastic/POSG). |
| A Surveys on MARL | 366-369 | B01-C0080 | Reverse-chronological (1999-2024) MARL survey reading list, application-specific surveys excluded. | None stated. |
| References | 370-391 | B01-C0081-B01-C0084 | Alphabetical bibliography of every work cited. | n/a |
| Index | 392-395 | B01-C0085 | Back-of-book alphabetical subject index. | n/a |

## Outline entries

### Front matter (cover, title page, copyright, dedication, contents)
- pages: 1-15
- chunks: B01-C0001, B01-C0002, B01-C0003
- summary: PDF pages 1-6 carry the book's cover, half-title, and published endorsement blurbs (praise quotes) from RL/MARL researchers, not book body text. PDF pages 7-12 carry the copyright/license page (MIT Press, CC-BY-NC-ND, AI-training-use restriction) and the authors' dedications. PDF pages 13-15 are the book's front-of-book table of contents, listing all part/chapter/section headings with their printed page numbers. No `structure.json` outline row covers pages 1-15 (its first entry, S001 Summary of Notation, starts at page 16, per the rebuild QA note); no reader was assigned this range either. Built directly from chunks.jsonl for this merge.
- defines: none (front matter, not exposition)
- algorithms: none
- results: none
- figures: none
- keywords: Markov decision process, Nash equilibrium, Q-learning, agent modeling, artificial intelligence, backpropagation, belief state, best response, correlated equilibrium, deep learning, equilibrium selection, game theory, gradient descent, independent learning, joint-action learning, minimax, multi-agent reinforcement learning, neural network, normal-form game, partially observable stochastic game, recurrent neural network, repeated normal-form game, self-play, stochastic game, textbook
- hmasd: none (licensing note only: p. 7-12 states a CC BY-NC-ND edition and that use to train AI systems requires separate written MIT Press permission - relevant to this corpus's own copyright/research-use boundary, not an HMASD connection)

### Summary of Notation
- pages: 16-18
- chunks: B01-C0004
- summary: Front-matter glossary of the mathematical notation used throughout the
  book: set/element/time-index/agent-index conventions, general math symbols, then
  symbol tables grouped as Game Model, Policies/Returns/Values, (Multi-Agent)
  Reinforcement Learning, Deep Learning, and (Multi-Agent) Deep Reinforcement
  Learning. Not a definitions section; each row is a symbol-to-meaning mapping rather
  than a formal definition.
- defines: notation glossary only, not formal definitions — game-model symbols I, S,
  O, A, r, T, R, Γs (p. 16-17); policy/return/value symbols Π, π, H, γ, u, V, Q (p.
  17); RL symbols L, α, ϵ, best-response set BRi (p. 17); deep learning symbols θ,
  f(x;θ), loss L(θ), batch B (p. 17); centralized information symbol z, entropy H, per-
  agent replay buffer Di (p. 18)
- algorithms: none
- results: none
- figures: none
- keywords: notation, symbols, sets, policies, value functions, discount factor,
  centralized information
- hmasd: curator_connection — the symbol z "centralized information, e.g. the state of
  the environment" (p. 18) names exactly the class of centralized-training input
  (discriminator/critic access) that any CTDE-style HMASD component depends on.

### List of Figures
- pages: 20-25
- chunks: B01-C0005
- summary: Front-matter listing of every figure caption in the book (Figures 1.1
  through 11.9) with printed page numbers, spanning the whole book, not only this
  reader's chapter range.
- defines: none
- algorithms: none
- results: none
- figures: none — this section is itself the master figure list; individual figures
  relevant to this reader's range are indexed under their owning sections below, using
  PDF-page locators (not the printed page numbers shown in this list)
- keywords: list of figures, figure captions
- hmasd: none

### Preface
- pages: 26-28
- chunks: B01-C0006
- summary: States the book's origin (based on a 2017 IJCAI tutorial by Albrecht and
  Stone), its goal (a principled introduction to MARL models, solution concepts,
  algorithmic ideas, and technical challenges, plus modern deep-learning-based
  approaches), its assumed prerequisites (undergraduate math: statistics, probability,
  linear algebra, calculus; basic programming for the accompanying codebase), and the
  recommended reading order (sequential by default; Chapters 2/7/8 for RL/deep-
  learning basics; Chapter 3 then Chapter 9 onward as a fast path for already-familiar
  readers). The authors explicitly list what the book does not cover: learning to
  communicate robustly (noisy/unreliable channels, learned protocols/languages) and
  evolutionary game theory, and state that comprehensiveness of algorithm coverage was
  not attempted given the field's growth rate.
- defines: none
- algorithms: none
- results: none
- figures: none
- keywords: preface, prerequisites, reading order, codebase, scope exclusions
- hmasd: none

### Chapter 1 — Introduction
- pages: 30-45
- chunks: B01-C0007, B01-C0008, B01-C0009, B01-C0010
- purpose: Introduces the multi-agent system concept (environment, agents, goals),
  extends the single-agent RL loop to a multi-agent training loop, works through four
  application domains (warehouse robotics, competitive games, autonomous driving,
  trading) and the "dimensions" MARL algorithms vary along (size, knowledge,
  observability, rewards, objective, centralization/communication), surveys core MARL
  challenges (non-stationarity, equilibrium selection, credit assignment, scaling),
  reviews Shoham et al.'s three MARL "agendas" (computational, prescriptive,
  descriptive) and states the book covers only the first two, then maps the book's
  two-part structure.
- prerequisites: Preface (p. 26-27) states that for readers unfamiliar with RL and deep
  learning, the basics are given in Chapters 2, 7, and 8 respectively; readers already
  familiar with RL and deep RL may read Chapter 3 and then skip to Chapter 9 onward.
  Section 1.6 (p. 44-45) states Part I's order is Ch.2 (single-agent RL) -> Ch.3 (game
  models) -> Ch.4 (solution concepts) -> Ch.5 (central/independent learning,
  challenges) -> Ch.6 (foundational algorithms); Part II's order is Ch.7 (deep
  learning) and Ch.8 (deep RL) feeding into Ch.9 (deep MARL algorithms), then Ch.10
  (implementation practice), then Ch.11 (environments). Chapter 1 itself has no stated
  prerequisite chapter.

### 1.1 Multi-Agent Systems
- pages: 31-33
- chunks: B01-C0007
- summary: Defines a multi-agent system as an environment plus multiple decision-
  making agents that interact to achieve goals, and defines the environment (state,
  dynamics, action/observation specification, possible partial observability) and
  agent (goal-directed via reward functions, uses a policy) components. Illustrates
  with the level-based foraging example (three robot agents with skill levels
  collecting items), the state representation, and the action set {up, down, left,
  right, collect, noop}, and distinguishes the "robot"/"item" object labels from the
  abstract decision-making "agent" concept.
- defines: multi-agent system (p. 32); environment (p. 31); agent (p. 32); policy (p.
  32); level-based foraging environment (p. 32)
- algorithms: none
- results: none
- figures: Figure 1.1 schematic of a multi-agent system (p. 31); Figure 1.2 level-based
  foraging task (p. 33)
- keywords: multi-agent system, environment, agent, policy, level-based foraging,
  partial observability
- hmasd: none

### 1.2 Multi-Agent Reinforcement Learning
- pages: 34-37
- chunks: B01-C0008
- summary: Defines MARL as learning optimal policies for a set of agents via a trial-
  and-error loop in which agents choose a joint action, the environment transitions,
  and each agent receives an individual reward and observation; a complete run from
  initial to terminal state is an episode. Distinguishes fully cooperative,
  competitive, and mixed scenarios using level-based foraging and chess, and argues
  MARL can decompose a large single-agent action space into smaller per-agent
  decision problems (at the cost of needing coordination) and can produce decentralized
  policies when centralized control is infeasible. Introduces the size/knowledge/
  observability/rewards/objective/centralization-communication dimensions of MARL
  algorithms with pointers to the chapters covering each (Figure 1.4).
- defines: MARL (p. 35); joint action (p. 35); episode (p. 35); centralized training
  and execution (p. 38); decentralized training and execution (p. 38); centralized
  training with decentralized execution (p. 38)
- algorithms: none
- results: worked numeric example — action-space blow-up 6^3 = 216 for centralized
  control of 3 robots vs. 6 actions per independent agent (p. 36); no theorem
- figures: Figure 1.3 schematic of MARL (p. 35); Figure 1.4 dimensions in MARL and
  relevant chapters (p. 37)
- keywords: MARL loop, joint action, episode, centralized/decentralized training and
  execution, CTDE, action-space scaling
- hmasd: curator_connection — the CTDE category named here (p. 38) is the training/
  execution regime HMASD itself uses (centralized discriminator/critic access during
  training, decentralized skill policies at execution).

### 1.3 Application Examples
- pages: 38-40
- chunks: B01-C0009
- summary: Introduces four illustrative MARL application domains — multi-robot
  warehouse management, competitive board/video games, autonomous driving, and
  automated trading — each described via its agents, observations, actions, and reward
  structure, with citations to prior work applying MARL in each domain.
- defines: none
- algorithms: none
- results: none
- figures: none
- keywords: applications, warehouse robotics, competitive games, autonomous driving,
  automated trading
- hmasd: none

### 1.3.1 Multi-Robot Warehouse Management
- pages: 38-39
- chunks: B01-C0009
- summary: Describes a hypothetical 100-robot warehouse-picking task as a MARL
  application: each robot is an independent agent observing its own location/items/
  order and possibly other agents' state, with actions for movement, picking, and
  communication; rewards may be individual (per completed order) or common/shared (any
  robot completing any order). Cites Krnjaic et al. (2024) and points to the
  simulator described in Section 11.3.4.
- defines: common (shared) reward — introduced via this example (p. 39)
- algorithms: none
- results: none
- figures: none
- keywords: multi-robot warehouse, common reward, order fulfillment
- hmasd: none

### 1.3.2 Competitive Play in Board Games and Video Games
- pages: 39
- chunks: B01-C0009
- summary: Describes MARL applied to competitive board/card games (Backgammon, Chess,
  Go, Poker) and video games; agents may observe full or partial game state, and each
  two-agent fully competitive game exhibits zero-sum reward (winner +1, loser -1).
  Cites prior MARL game-playing systems (Tesauro 1994; Silver et al. 2018; Vinyals et
  al. 2019; Bard et al. 2020; Meta FAIR Diplomacy Team et al. 2022; Perolat et al.
  2022) as external work, not results reproduced in this book.
- defines: zero-sum reward — introduced via this example (p. 39)
- algorithms: none
- results: none
- figures: none
- keywords: competitive games, zero-sum reward, self-play, board games
- hmasd: none

### 1.3.3 Autonomous Driving
- pages: 39-40
- chunks: B01-C0009
- summary: Describes urban/highway autonomous driving as a mixed-motive MARL
  application: agents have continuous or discrete driving actions, partial and noisy
  observations of other vehicles, and multi-factor rewards (large negative for
  collisions, positive for efficient driving, negative for abrupt maneuvers),
  introducing general-sum reward as agents both collaborate (avoid collisions) and
  compete (minimize own driving time).
- defines: general-sum reward — introduced via this example (p. 40)
- algorithms: none
- results: none
- figures: none
- keywords: autonomous driving, general-sum reward, mixed-motive, partial
  observability
- hmasd: none

### 1.3.4 Automated Trading in Electronic Markets
- pages: 40-41
- chunks: B01-C0009
- summary: Describes electronic-market trading agents as a mixed-motive MARL
  application in which agents buy/sell commodities, observe market/order-book
  information, and receive rewards from realized gains/losses over a trading period,
  again framed as general-sum since agents implicitly cooperate on prices while
  maximizing individual gains.
- defines: none (elaborates general-sum, already defined in 1.3.3)
- algorithms: none
- results: none
- figures: none
- keywords: automated trading, electronic markets, general-sum
- hmasd: none

### 1.4 Challenges of MARL
- pages: 41-43
- chunks: B01-C0009
- summary: Outlines four central MARL challenges to be elaborated in Chapter 5: non-
  stationarity (each agent's learning target shifts as other agents' policies change,
  producing a "moving target problem"); optimality/equilibrium selection (multiple
  equilibria may exist, with agents implicitly needing to "negotiate" which to
  converge to); multi-agent credit assignment (determining which agent's action, not
  just which past action, contributed to a shared reward, illustrated with a level-
  based-foraging example); and scaling in number of agents (joint action space can
  grow exponentially with agent count, though Section 5.4.4, outside this reader's
  range, is noted as a stated counter-example without exponential growth).
- defines: non-stationarity (p. 41); equilibrium selection (p. 41); multi-agent credit
  assignment (p. 42); scaling challenge (p. 42-43)
- algorithms: none
- results: none
- figures: none
- keywords: non-stationarity, moving target problem, equilibrium selection, credit
  assignment, scaling to many agents
- hmasd: curator_connection — the multi-agent credit-assignment problem stated here (p.
  42) is the general problem HMASD's skill-conditioned reward structure is meant to
  address; this section states the problem, not any solution.

### 1.5 Agendas of MARL
- pages: 42-44
- chunks: B01-C0009, B01-C0010
- summary: Summarizes Shoham, Powers, and Grenager's (2007) three MARL research
  agendas — computational (use MARL to compute game solutions, competing with direct
  game-theoretic methods), prescriptive (specify performance criteria a learning agent
  should satisfy, regardless of or conditioned on the class of other agents), and
  descriptive (use MARL to model how natural agents such as humans learn in a
  population) — and states the authors' own position: the book covers the
  computational and prescriptive agendas and explicitly excludes the descriptive
  agenda.
- defines: computational agenda (p. 43); prescriptive agenda (p. 43); descriptive
  agenda (p. 43)
- algorithms: none
- results: none
- figures: none
- keywords: MARL agendas, computational agenda, prescriptive agenda, descriptive
  agenda
- hmasd: curator_boundary — the book excludes the descriptive agenda (modeling
  natural/biological learning) entirely; this book is not evidence for that use case.

### 1.6 Book Contents and Structure
- pages: 44-45
- chunks: B01-C0010
- summary: Maps the book's two-part structure: Part I (Chapters 2-6) covers
  foundational single-agent RL, game models, solution concepts, and central/
  independent learning plus foundational MARL algorithms; Part II (Chapters 7-11)
  covers deep learning, deep RL, deep MARL algorithms (CTDE, value decomposition,
  parameter sharing, population-based training), practical implementation guidance,
  and multi-agent environments. States the book ships an accompanying Python codebase
  (Chapter 10 documents how algorithms map to code).
- defines: none (structural overview)
- algorithms: none
- results: none
- figures: none
- keywords: book structure, Part I, Part II, codebase
- hmasd: none

### Chapter 2 — Reinforcement Learning
- pages: 48-71 (the Part I front-matter introduction on pages 46-47 precedes it inside
  chunk B01-C0011)
- chunks: B01-C0011, B01-C0012, B01-C0013, B01-C0014, B01-C0015, B01-C0016
- purpose: Gives the single-agent RL foundation the rest of Part I builds on: a general
  definition of RL, the finite Markov decision process (MDP), expected discounted
  return and optimal policies, state/action value functions and the Bellman equation,
  dynamic programming (policy iteration, value iteration — requires full MDP
  knowledge), temporal-difference learning (Sarsa, Q-learning — learns from sampled
  experience), evaluation via learning curves, and the equivalence of the R(s,a,s') and
  R(s,a) reward-function conventions.
- prerequisites: Preface (p. 27) recommends Chapter 2 for readers unfamiliar with RL.
  Section 1.6 (p. 44) states Chapter 2 opens Part I and precedes Chapters 3-6, which
  build on and extend its DP/TD algorithms to game models (Ch. 3-4) and MARL (Ch.
  5-6). No chapter is stated as a prerequisite to Chapter 2 itself.

### 2.1 General Definition
- pages: 48-50
- chunks: B01-C0011, B01-C0012
- summary: Defines RL generally as algorithms that learn solutions for sequential
  decision processes via repeated interaction with an environment, unpacked into three
  questions: what is a sequential decision process (an agent choosing actions over
  time steps, receiving observations/state and a scalar reward), what is a solution
  (an optimal policy maximizing expected return), and what is learning via interaction
  (trial-and-error, balancing exploration and exploitation). Contrasts RL with
  supervised and unsupervised learning.
- defines: sequential decision process (p. 49); solution to a decision process /
  optimal policy (p. 49); exploration-exploitation dilemma (p. 50)
- algorithms: none
- results: none
- figures: Figure 2.1 definition of an RL problem (p. 49); Figure 2.2 basic RL loop for
  a single-agent system (p. 50)
- keywords: RL definition, sequential decision process, exploration-exploitation,
  supervised vs. unsupervised learning
- hmasd: none

### 2.2 Markov Decision Processes
- pages: 50-52
- chunks: B01-C0012
- summary: Gives the formal Definition 1 of a finite Markov decision process (MDP):
  states S with terminal subset S̄, actions A, reward function R, transition function
  T (with sum-to-one and initial-state-distribution normalization, Eq. 2.1-2.2), and
  describes the interaction protocol and episode. Introduces the Markov property (Eq.
  2.3), the Mars Rover MDP example (Figure 2.3), the multi-armed bandit as a T=1,
  single-state, unknown-reward special case of the MDP, and POMDPs as a generalization
  to partial observability (with a forward pointer to POSGs in Chapter 3). Marked
  equation_text_unreliable — the displayed sum/normalization equations use big-
  operator glyphs that misextracted.
- defines: Markov decision process, Definition 1 (p. 51); Markov property (p. 52);
  multi-armed bandit problem as MDP special case (p. 53); partially observable Markov
  decision process, POMDP (p. 53)
- algorithms: none
- results: worked example — Mars Rover MDP (Figure 2.3, p. 52), used throughout the
  chapter
- figures: Figure 2.3 Mars Rover MDP (p. 52)
- keywords: MDP, Markov property, multi-armed bandit, POMDP, terminal states,
  transition function
- hmasd: none

### 2.3 Expected Discounted Returns and Optimal Policies
- pages: 53-54
- chunks: B01-C0012
- summary: Defines the finite-horizon total return (Eq. 2.4) and its expectation under
  a policy (Eq. 2.5), then introduces the discount factor γ ∈ [0,1] and discounted
  return (Eq. 2.6) to guarantee finiteness in non-terminating MDPs, with a bound via
  the geometric series (Eq. 2.7). Gives two equivalent interpretations of γ
  (termination probability per step; per-step reward weighting) and introduces
  absorbing states as the device letting one discounted-return definition cover both
  terminating and non-terminating MDPs; defines the MDP solution as the optimal policy
  maximizing expected discounted return. Marked equation_text_unreliable.
- defines: discount factor γ (p. 54); discounted return, Eq. 2.6 (p. 54); absorbing
  state (p. 55)
- algorithms: none
- results: none
- figures: none
- keywords: discounted return, discount factor, absorbing states, geometric series
  bound
- hmasd: none

### 2.4 Value Functions and Bellman Equation
- pages: 55-57
- chunks: B01-C0013
- summary: Defines the state-value function Vπ(s) (Eq. 2.10-2.13) and action-value
  function Qπ(s,a) (Eq. 2.17-2.20) as expected returns under policy π, derives the
  recursive Bellman equation (Eq. 2.13, named for Richard Bellman) via the Markov
  property, and notes it forms a system of |S| linear equations solvable exactly.
  Defines optimal value functions V*/Q* (Eq. 2.21-2.22), the Bellman optimality
  equations (Eq. 2.24-2.25, non-linear from the max operator), and shows the optimal
  policy is recoverable from Q* by argmax (Eq. 2.26); deterministic optimal policies
  always exist even though multiple optimal policies may share the same value
  function. Marked equation_text_unreliable.
- defines: state-value function Vπ (p. 56); action-value function Qπ (p. 57); Bellman
  equation (p. 56); optimal value function V*/Q* (p. 57); Bellman optimality equations
  (p. 57)
- algorithms: none
- results: none
- figures: none
- keywords: value function, Bellman equation, Bellman optimality equation, optimal
  policy
- hmasd: none

### 2.5 Dynamic Programming
- pages: 58-60
- chunks: B01-C0013
- summary: Introduces dynamic programming (DP) as a family of algorithms requiring
  complete MDP knowledge to compute value functions and optimal policies, presents
  policy iteration (alternating policy evaluation and policy improvement, Eq. 2.27),
  iterative policy evaluation (Eq. 2.28) applied to the Mars Rover example, and proves
  convergence via the Banach fixed-point theorem by showing the Bellman operator is a
  γ-contraction under the max-norm (Eq. 2.29-2.37). States and uses the policy
  improvement theorem (Eq. 2.40-2.46, cited to Sutton and Barto 2018 without proof
  in-text) to argue policy iteration converges to the optimal policy. Marked
  equation_text_unreliable.
- defines: dynamic programming (p. 58); policy iteration (p. 58); iterative policy
  evaluation (p. 58); contraction mapping / γ-contraction (p. 59); bootstrapping (p.
  59)
- algorithms: none in this section's own pages (Algorithm 1, Value iteration, is
  printed on p. 61 at the top of the next chunk, though logically it concludes this
  section's material)
- results: worked example — iterative policy evaluation on the Mars Rover MDP,
  Vπ(Start)=0 for the "always right" policy, and Vπ(Start)=2.05, Vπ(Site A)=6.2,
  Vπ(Site B)=10 for a mixed policy (p. 59); stated theorem — policy improvement
  theorem, cited to Sutton and Barto (2018), used without in-text proof (p. 60)
- figures: none
- keywords: dynamic programming, policy iteration, value iteration, contraction
  mapping, Banach fixed-point theorem, policy improvement theorem
- hmasd: none

### 2.6 Temporal-Difference Learning
- pages: 61-63
- chunks: B01-C0014
- summary: Introduces temporal-difference (TD) learning as algorithms that learn value
  functions from sampled experience rather than complete MDP knowledge, via the
  general TD update rule (Eq. 2.50) with learning rate α and update target X. Presents
  Sarsa (Algorithm 2) as on-policy, target using the sampled next action (Eq.
  2.52-2.53), states its convergence conditions (infinite visitation of all state-
  action pairs; Robbins-Monro step-size conditions, Eq. 2.54) and the ϵ-greedy policy
  (Eq. 2.55) used to satisfy them. Also presents Algorithm 1 (Value iteration for
  MDPs) at the top of this chunk, concluding Section 2.5. Marked
  equation_text_unreliable.
- defines: temporal-difference learning (p. 62); ϵ-greedy policy (p. 63)
- algorithms: Algorithm 1 Value iteration for MDPs (p. 61); Algorithm 2 Sarsa for MDPs
  with ϵ-greedy policies (p. 63)
- results: Sarsa convergence to Qπ under two stated conditions (visitation +
  Robbins-Monro step-size schedule), no in-text proof (p. 62)
- figures: none
- keywords: temporal-difference learning, Sarsa, value iteration, epsilon-greedy,
  Robbins-Monro conditions
- hmasd: none

### 2.6 Temporal-Difference Learning (Q-learning, cont.)
- pages: 64-65
- chunks: B01-C0015
- summary: Continues Section 2.6: presents Q-learning (Algorithm 3) as an off-policy TD
  method whose target uses the max over next-state action values (Eq. 2.56-2.58), and
  states Q-learning converges to π* under the same visitation/step-size conditions as
  Sarsa without requiring the behavior policy to approach π* — the on-policy/off-
  policy distinction the book flags for elaboration in Chapter 8. Marked
  equation_text_unreliable.
- defines: on-policy vs. off-policy TD algorithm (p. 65)
- algorithms: Algorithm 3 Q-learning for MDPs with ϵ-greedy policies (p. 64)
- results: Q-learning convergence to π* under the same conditions as Sarsa, no in-text
  proof (p. 65)
- figures: none
- keywords: Q-learning, off-policy, on-policy, convergence
- hmasd: none

### 2.7 Evaluation with Learning Curves
- pages: 65-68
- chunks: B01-C0015
- summary: Describes the standard learning-curve methodology — plotting evaluation
  return (return of the greedy policy extracted after T learning time steps) against
  cumulative environment time steps (not episode count, to avoid skewing comparisons
  when algorithms complete episodes at different rates), averaged over independent
  training runs with shaded standard deviation. Applies this to Sarsa vs. Q-learning on
  the Mars Rover MDP (100 training runs x 100 evaluation episodes each), showing both
  converge to the same optimal policy with near-identical curves, while learning-rate
  and exploration-rate choices materially affect Q-learning's speed. Also discusses
  undiscounted returns and secondary metrics (win rate, episode length) for
  interpretability, while cautioning that the evaluated policy was trained for the
  discounted objective, not these metrics, and that different discount factors can
  yield different optimal policies for the same MDP.
- defines: evaluation return (p. 65); learning curve (p. 65)
- algorithms: none
- results: empirical figure — Sarsa vs. Q-learning learning curves on Mars Rover MDP,
  γ=0.95, averaged over 100 training runs x 100 evaluation episodes (Figure 2.4, p.
  66); both converge to the optimal policy V*(Start)=4.1; learning-rate/exploration-
  rate sensitivity shown in Fig. 2.4(c)-(d) (p. 66); γ=0.5 yields a different optimal
  policy, V*(Start)=0, than γ=0.95's V*(Start)=4.1, for the identical Mars Rover MDP
  (p. 68)
- figures: Figure 2.4 Sarsa/Q-learning learning curves and episode lengths on Mars
  Rover (p. 66)
- keywords: learning curves, evaluation return, discounted vs. undiscounted return,
  hyperparameter sensitivity
- hmasd: none

### 2.8 Equivalence of R(s,a,s') and R(s,a)
- pages: 68-69
- chunks: B01-C0015, B01-C0016
- summary: Shows the two common reward-function conventions, R(s,a,s') and R(s,a), are
  formally equivalent (any MDP under one can be transformed into an MDP under the
  other with identical expected returns for any policy), derives the transformation
  via R(s,a) = Σ_s' T(s'|s,a)R(s,a,s') (Eq. 2.63), and states the book's choice to use
  R(s,a,s') throughout for two pedagogical reasons: it is more intuitive for
  specifying example MDPs with differing per-transition rewards, and it visually
  matches TD update targets in the Bellman equations. Notes most original MARL
  literature (Chapter 6) uses R(s,a). Marked equation_text_unreliable.
- defines: reward-function equivalence R(s,a,s') <-> R(s,a) (p. 69)
- algorithms: none
- results: none
- figures: none
- keywords: reward function, R(s,a,s') vs. R(s,a), notational equivalence
- hmasd: none

### 2.9 Summary
- pages: 69-71
- chunks: B01-C0016
- summary: Recaps the chapter's core concepts — MDP as the standard environment model,
  an RL problem as decision-process-model plus learning objective, the Markov property
  enabling recursive Bellman value functions, dynamic programming (full-knowledge)
  versus temporal-difference learning (sampled-experience) as the two algorithm
  families covered, and learning curves as the standard evaluation tool — then
  previews how Chapters 3-6 extend these single-agent concepts to games and MARL.
- defines: none (recap of prior definitions)
- algorithms: none
- results: none
- figures: none
- keywords: chapter summary, MDP, Bellman equation, dynamic programming, temporal-
  difference learning
- hmasd: none

### Chapter 3 — Games: Models of Multi-Agent Interaction
- pages: 72-89
- chunks: B01-C0017, B01-C0018, B01-C0019, B01-C0020
- purpose: Defines the hierarchy of formal game models used throughout the book:
  normal-form games, repeated normal-form games, stochastic games, and partially
  observable stochastic games (POSGs), each generalizing the previous (POSG ⊃
  stochastic game ⊃ repeated normal-form game ⊃ MDP as the single-agent case). Covers
  zero-sum/common-reward/general-sum reward classification, belief states and
  filtering under partial observability, modeling communication as an action that does
  not affect the state, knowledge assumptions (complete vs. incomplete information
  games), and closes with an RL-to-game-theory terminology dictionary. States
  explicitly that this chapter defines interaction models only, not solution concepts
  (deferred to Chapter 4).
- prerequisites: Preface (p. 27) states readers already familiar with RL and deep RL
  may read Chapter 3 and then skip straight to Chapter 9 onward — i.e., Chapter 3 is
  positioned as not requiring Chapters 2 or 4-8 on that fast path. Section 1.6 (p. 44)
  places Chapter 3 immediately after Chapter 2 within Part I, extending the MDP model
  to multiple agents; Chapter 4 (solution concepts) is stated to build on Chapter 3's
  game models.

## Section entries

### 3.1 Normal-Form Games
- pages: 72-75
- chunks: B01-C0017
- summary: Introduces the game-model hierarchy (Figure 3.1: POSG ⊃ stochastic game ⊃
  repeated normal-form game ⊃ MDP as agent-count/state-count special cases) and gives
  Definition 2 of the normal-form (strategic-form) game: a finite agent set I, per-
  agent finite action set Ai, and reward function Ri: A→R. Describes the single-shot
  interaction protocol and classifies normal-form games as zero-sum (Σ Ri(a)=0),
  common-reward (Ri=Rj for all i,j), or general-sum (no restriction), illustrated by
  Rock-Paper-Scissors, a Coordination Game, and Prisoner's Dilemma (Figure 3.2). Notes
  two-agent normal-form games are called matrix games and points to Section 11.2's
  listing of all 78 structurally distinct strictly-ordinal 2x2 normal-form games.
  Marked equation_text_unreliable.
- defines: normal-form game, Definition 2 (p. 73); zero-sum game (p. 74); common-
  reward game (p. 74); general-sum game (p. 74); matrix game (p. 74)
- algorithms: none
- results: none
- figures: Figure 3.1 hierarchy of game models (p. 73); Figure 3.2 three example matrix
  games — Rock-Paper-Scissors, Coordination Game, Prisoner's Dilemma (p. 75)
- keywords: normal-form game, matrix game, zero-sum, common-reward, general-sum,
  Prisoner's Dilemma
- hmasd: none

### 3.2 Repeated Normal-Form Games
- pages: 75-76
- chunks: B01-C0017
- summary: Extends the normal-form game to T time steps of repeated play, conditioning
  each agent's policy on the joint-action history ht. Notes finite and infinite
  repetition are not equivalent (finite repetition creates "end-game" effects),
  relates the infinite-repetition termination probability to the RL discount factor
  (1-γ), and introduces Tit-for-Tat for repeated Prisoner's Dilemma as an example of a
  history-conditioned policy. Defines "non-repeated" (T=1) versus "repeated" (T>1) as
  the book's terminology going forward.
- defines: repeated normal-form game (p. 76); Tit-for-Tat policy (p. 76); non-repeated
  vs. repeated normal-form game terminology (p. 76)
- algorithms: none
- results: none
- figures: none
- keywords: repeated games, joint-action history, Tit-for-Tat, end-game effects,
  discount factor as termination probability
- hmasd: none

### 3.3 Stochastic Games
- pages: 76-78
- chunks: B01-C0017
- summary: Gives Definition 3 of the stochastic game (Shapley 1953): adds a finite
  state set S (with terminals S̄) to the normal-form game, with per-agent reward
  functions Ri: S×A×S→R and transition function T satisfying normalization equations
  (3.1-3.2). Describes the interaction protocol (state-action history ht, full
  observability of state and joint action by all agents), states the Markov property
  (Eq. 3.3), and notes stochastic games are also called Markov games. Illustrates with
  a stochastic-game formulation of level-based foraging; notes stochastic games include
  repeated normal-form games (single state) and MDPs (single agent) as special cases.
  Marked equation_text_unreliable.
- defines: stochastic game, Definition 3 (p. 76-77); Markov game (synonym) (p. 77)
- algorithms: none
- results: none
- figures: none
- keywords: stochastic game, Markov game, full observability, state-action history
- hmasd: curator_connection — the stochastic-game definition's full observability of
  state and joint action by all agents (p. 77) is the assumption HMASD's centralized-
  training components rely on, and that partial observability (Section 3.4) relaxes.

### 3.4 Partially Observable Stochastic Games
- pages: 78-82
- chunks: B01-C0018
- summary: Gives Definition 4 of the partially observable stochastic game (POSG)
  (Hansen, Bernstein, and Zilberstein 2004): a stochastic game plus, for each agent, a
  finite observation set Oi and observation function Oi: A×S×Oi→[0,1] (Eq. 3.4).
  Describes the interaction protocol (agents act on observation histories hti rather
  than states), notes POSGs with common reward are known as Decentralized POMDPs
  (Dec-POMDPs), and that POSGs include stochastic games (oti=(st,at-1)) and POMDPs
  (single agent) as special cases. Enumerates example observability structures the
  observation function can encode: unobserved other-agent actions, limited view
  regions (illustrated with partially observable level-based foraging, Figure 3.4),
  sensor noise, and lossy/limited-range communication. Marked
  equation_text_unreliable.
- defines: partially observable stochastic game / POSG, Definition 4 (p. 80);
  Decentralized POMDP / Dec-POMDP (p. 80-81); observation function (p. 80)
- algorithms: none
- results: none
- figures: Figure 3.3 normal-form games as the building block of stochastic games and
  POSGs, shown as directed cyclic graphs (p. 79); Figure 3.4 level-based foraging with
  partial observability / local vision fields (p. 82)
- keywords: POSG, Dec-POMDP, observation function, partial observability, limited view
  region, communication modeling
- hmasd: curator_connection — the POSG's per-agent observation function (p. 80) and
  limited-view-region example (p. 82) are the formal object an N-agnostic or roster-
  varying HMASD variant's observation design must specify; this section defines the
  model, not any variable-N guarantee.

### 3.4.1 Belief States and Filtering
- pages: 82-83
- chunks: B01-C0018, B01-C0019
- summary: Defines the belief state bti as a probability distribution over possible
  environment states given an agent's observation history, gives the Bayesian belief-
  update equation (Eq. 3.5) for the single-agent (POMDP) case, and notes the belief
  state is a sufficient statistic for optimal action selection. States exact belief
  tracking is intractable (exponential in state-variable count) in general, that
  multi-agent belief updating is significantly more complex since it requires modeling
  other agents' observation functions and policies, and that MARL typically assumes
  agents lack the knowledge (S, T, Oi) required for exact filtering — motivating
  recurrent neural networks (Section 7.5.2) as the practical approximate-filtering
  mechanism used later in the book. Marked equation_text_unreliable.
- defines: belief state (p. 83); (belief state) filtering (p. 83); sufficient
  statistic (p. 83)
- algorithms: none
- results: none
- figures: none
- keywords: belief state, filtering, Bayesian update, sufficient statistic, recurrent
  neural networks
- hmasd: none

### 3.5 Modeling Communication
- pages: 83-85
- chunks: B01-C0019
- summary: Shows how stochastic games and POSGs can represent inter-agent
  communication without a dedicated primitive: each agent's action space is split into
  environment and communication components, Ai = Xi × Mi (Eq. 3.6), communication
  actions are observed by other agents but by definition do not affect the state
  transition function (Eq. 3.7), and in a POSG, noisy/lossy/range-limited
  communication can be modeled via the observation function (e.g., additive Gaussian
  noise, or setting a message to ∅ if out of range or lost). Notes agents are assumed
  not to know the meaning of communication actions a priori and must learn to
  interpret them, citing the emergent-communication literature (Foerster et al. 2016;
  Sukhbaatar, Szlam, and Fergus 2016; Wang, He, et al. 2020; Guo et al. 2022) as prior
  work, not results of this book.
- defines: communication action (p. 84); message loss / noisy communication modeling
  (p. 85)
- algorithms: none
- results: none
- figures: none
- keywords: communication modeling, message passing, emergent communication, noisy/
  lossy channels
- hmasd: none

### 3.6 Knowledge Assumptions in Games
- pages: 85-87
- chunks: B01-C0019, B01-C0020
- summary: Distinguishes "complete knowledge games" (all agents know all game
  components: action spaces, reward functions, transition/observation functions) from
  the standard MARL assumption the book states is closer to "incomplete information
  games" — agents typically know neither their own nor others' reward functions, nor
  the transition/observation functions, and instead learn from experienced
  transitions. Introduces the simulator abstraction T̂ (Eq. 3.8) as the realistic
  middle ground many MARL settings use. Raises symmetric/asymmetric knowledge and
  common-knowledge questions as generally lesser-studied in MARL, with exceptions in
  zero-sum/common-reward algorithm design (pointing to Chapters 6 and 9). States the
  standard assumption that the number of agents is fixed and commonly known, noting
  open multi-agent environments (agents entering/leaving) as outside this book's
  scope, citing Jiang et al. (2020), Rahman et al. (2021), and Rahman, Carlucho, et al.
  (2023).
- defines: complete knowledge game (p. 86); incomplete information game (p. 86);
  simulator model T̂ (p. 86)
- algorithms: none
- results: none
- figures: none
- keywords: knowledge assumptions, complete vs. incomplete information, common
  knowledge, fixed agent count, open multi-agent systems
- hmasd: curator_boundary — the book states fixed and commonly-known agent count is
  its standard assumption throughout (p. 87) and that dynamically entering/leaving
  agents ("open" multi-agent environments) are outside its scope, citing only external
  prior work; nothing in this book's own algorithms is evidence for variable-N
  generalization.

### 3.7 Dictionary: Reinforcement Learning ↔ Game Theory
- pages: 87
- chunks: B01-C0020
- summary: Gives a terminology dictionary (Figure 3.5) mapping RL terms used in the
  book to their game-theory equivalents: environment/game, agent/player, reward/
  payoff-utility, policy/strategy, deterministic-X/pure-X, probabilistic-X/mixed-X,
  and joint-X/X-profile.
- defines: none (terminology mapping, not new concepts)
- algorithms: none
- results: none
- figures: Figure 3.5 synonymous terms in RL and game theory (p. 88)
- keywords: terminology, RL/game-theory dictionary, strategy vs. policy
- hmasd: none

### 3.8 Summary
- pages: 87-89
- chunks: B01-C0020
- summary: Recaps the chapter's game-model hierarchy (normal-form → repeated normal-
  form → stochastic game → POSG, each a generalization), the zero-sum/common-reward/
  general-sum reward classification, communication modeling via observable-but-state-
  inert actions, and the standard MARL assumption of incomplete knowledge of game
  components. States that Chapter 4 will introduce solution concepts as learning
  objectives for these game models.
- defines: none (recap)
- algorithms: none
- results: none
- figures: none
- keywords: chapter summary, game hierarchy, reward classification
- hmasd: none

### 4 Solution Concepts for Games (chapter-level intro)
- pages: 90–91
- chunks: B01-C0021
- summary: Frames a MARL problem as game model + solution concept (Figure 4.1). States
  that a solution is a joint policy π = (π1,...,πn) satisfying properties expressed in
  terms of agents' expected returns Ui(π) and the relations between agents' returns. Says
  the chapter will build a hierarchy from minimax through Nash to correlated equilibrium,
  plus refinements (Pareto, welfare/fairness) and alternatives (no-regret), then discuss
  computational complexity. Notes all definitions assume finite game models.
- defines: none (definitions begin in 4.1)
- algorithms: none
- results: none
- figures: Figure 4.1 MARL problem = game model + solution concept (p. 91)
- keywords: solution concept, joint policy, game model, MARL problem definition
- hmasd: curator_connection: the game-model/solution-concept split is the same decomposition HMASD papers implicitly use when they fix a POSG-like environment and add a skill-discovery objective as an additional solution criterion

### 4.1 Joint Policy and Expected Return
- pages: 91–93
- chunks: B01-C0021
- summary: Gives a universal definition of expected return Ui(π) that applies to all
  game models from Chapter 3, stated for the POSG model. Provides two equivalent
  definitions: a history-based sum over full histories weighted by their probability
  under π (Equations 4.1–4.4), and a recursive Bellman-style definition via value
  functions Vπ_i and Qπ_i (Equations 4.6–4.8). Assumes discounted returns and absorbing
  states to unify finite- and infinite-horizon cases.
- defines: expected return Ui(π), history-based form (p. 92, Eq. 4.1–4.4); joint-action
  probability under independent policies (p. 92, Eq. 4.5); recursive value functions
  Vπ_i, Qπ_i (p. 93, Eq. 4.6–4.7); expected return from initial state (p. 93, Eq. 4.8)
- algorithms: none
- results: none — this section is exposition/definition, not a stated theorem. Some
  equations (4.1–4.8) sit on pages flagged `equation_text_unreliable`; big-operator
  glyphs (Σ, Π) in the extracted text should not be trusted as printed.
- figures: none
- keywords: expected return, POSG, history-based return, Bellman recursion, value function, discounted return, absorbing state
- hmasd: none

### 4.2 Best Response
- pages: 94
- chunks: B01-C0022
- summary: Defines the best-response operator BRi(π−i), the set of policies for agent i
  that maximize Ui against a fixed policy π−i for the other agents. Notes best responses
  need not be unique. States that best-response operators underlie both the compact
  definitions of solution concepts in this chapter and iterative solution methods
  (fictitious play, joint-action learning with agent modeling, covered in Chapter 6).
- defines: best response BRi(π−i) (p. 94, Eq. 4.9)
- algorithms: none
- results: none
- figures: none
- keywords: best response, best-response operator
- hmasd: none

### 4.3 Minimax
- pages: 94–96
- chunks: B01-C0022
- summary: Defines minimax as the solution concept for two-agent zero-sum games. States
  that every finite two-agent zero-sum normal-form game has a minimax solution (von
  Neumann 1928; von Neumann and Morgenstern 1944), that finite-horizon and
  discounted-infinite-horizon two-agent zero-sum stochastic games also have minimax
  solutions (Shapley 1953), and that all minimax solutions yield the same unique value
  for each agent. Shows a minimax solution is equivalent to mutual best response
  (πi ∈ BRi(πj), πj ∈ BRj(πi)) and works the Rock-Paper-Scissors example, where the
  unique minimax solution is uniform-random play with value 0 to both agents.
- defines: minimax solution (p. 95, Definition 5, Eq. 4.10–4.11); maxmin/minmax policy and value (p. 95); minimax value of the game (p. 95)
- algorithms: none
- results: existence of minimax solutions in finite two-agent zero-sum normal-form
  games (von Neumann 1928/1944) and finite/discounted-infinite two-agent zero-sum
  stochastic games (Shapley 1953) — stated theorems, no proof given in text (p. 94–95)
- figures: none (references Figure 3.2(a) Rock-Paper-Scissors matrix from Chapter 3, outside range)
- keywords: minimax, zero-sum game, maxmin, minmax, Rock-Paper-Scissors, game value
- hmasd: none

### 4.3.1 Minimax Solution via Linear Programming
- pages: 96
- chunks: B01-C0022
- summary: Gives the linear program that computes a two-agent zero-sum minimax solution:
  one LP per agent, each minimizing the opponent's guaranteed expected return subject to
  probability-simplex constraints on the agent's own action distribution. Notes LPs are
  solvable via simplex (worst-case exponential, often fast in practice) or interior-point
  methods (provably polynomial time).
- defines: minimax LP (p. 96, Eq. 4.12–4.15)
- algorithms: minimax-via-LP construction (unnumbered; formal linear program, p. 96)
- results: none
- figures: none
- keywords: linear programming, minimax LP, simplex algorithm, interior-point method
- hmasd: none

### 4.4 Nash Equilibrium
- pages: 97–99
- chunks: B01-C0022
- summary: Extends mutual best response to general-sum games with n ≥ 2 agents. States
  Nash's existence theorem for finite normal-form games (Nash 1950) and that, in
  two-agent zero-sum games, minimax solutions and Nash equilibria coincide. Distinguishes
  deterministic ("pure") from probabilistic ("mixed") equilibria and notes some games
  (e.g., Rock-Paper-Scissors) have only mixed equilibria. Discusses that a game may have
  multiple Nash equilibria with different expected returns (coordination game, Chicken,
  Stag Hunt), raising the equilibrium-selection question addressed later in Section
  5.4.2. States "folk theorems": under sufficiently far-sighted agents (discount γ near
  1), any feasible and enforceable expected-return vector can be realized by an
  equilibrium, where enforceable means each agent's return is at least its minmax value
  (Eq. 4.17). Gives a best-response-based procedure to check whether a joint policy is a
  Nash equilibrium.
- defines: Nash equilibrium (p. 97, Definition 6, Eq. 4.16); pure/mixed equilibrium
  terminology (p. 98); n-agent minmax value (p. 98, Eq. 4.17)
- algorithms: procedure for checking Nash equilibrium via per-agent best-response
  recomputation (unnumbered, p. 99); notes π′_i computable via LP for non-repeated
  normal-form games (Albrecht and Ramamoorthy 2012), or single-agent RL for sequential
  games
- results: existence of Nash equilibrium in finite normal-form games (Nash 1950, p. 97);
  existence of Nash equilibrium in stochastic games (Fink 1964; Filar and Vrieze 2012,
  p. 98); folk theorems on feasible/enforceable expected returns (informal statement,
  no proof, p. 98–99) — text on these pages is flagged `equation_text_unreliable`
- figures: none (references Prisoner's Dilemma / coordination / Rock-Paper-Scissors
  matrix games from Figure 3.2, outside range)
- keywords: Nash equilibrium, pure equilibrium, mixed equilibrium, folk theorem, minmax value, equilibrium selection (forward reference)
- hmasd: curator_connection: the multiplicity-of-equilibria discussion here is the source of the "equilibrium selection" challenge that HMASD-style skill discovery must implicitly resolve by biasing toward one joint behavior mode

### 4.5 ε-Nash Equilibrium
- pages: 99–100
- chunks: B01-C0022, B01-C0023
- summary: Relaxes strict Nash equilibrium to allow deviation gains up to ε > 0, to
  address that exact equilibria may require irrational-valued probabilities (Nash 1950)
  and that exact equilibria can be too costly to compute. Gives an explicit
  counterexample (Figure 4.2) showing an ε-Nash equilibrium can be arbitrarily far in
  expected-return space from the unique Nash equilibrium of a game, so ε-Nash should not
  be read as a return-approximation of Nash equilibrium. Gives a check procedure
  analogous to Section 4.4's.
- defines: ε-Nash equilibrium (p. 99, Definition 7, Eq. 4.18)
- algorithms: none
- results: none (the Figure 4.2 example is a worked counterexample, not a stated
  theorem)
- figures: Figure 4.2 matrix game showing an ε-Nash equilibrium (B,D), ε=1, far from the
  real Nash equilibrium (A,C) (p. 100)
- keywords: epsilon-Nash equilibrium, approximate equilibrium, irrational probabilities
- hmasd: none

### 4.6 (Coarse) Correlated Equilibrium
- pages: 100–103
- chunks: B01-C0023
- summary: Generalizes Nash equilibrium by allowing correlated (not necessarily
  independent) agent policies via a joint recommendation policy πc conditioned on
  private signals. States that correlated equilibria contain Nash equilibria as the
  special case where πc factors into independent policies. Works the Chicken game
  example, showing a correlated equilibrium (5,5) can Pareto-dominate the best symmetric
  Nash equilibrium (≈4.66, 4.66) reachable independently. Defines the more general coarse
  correlated equilibrium by restricting deviations to unconditional (constant-action)
  modifiers, and notes correlated equilibria are a special case of coarse correlated
  equilibria. Surveys extensions to sequential-move games (private signals as actions vs.
  policies; revealed vs. hidden outcomes; deviation-handling choices) without adopting one.
- defines: correlated equilibrium (p. 101, Definition 8, Eq. 4.19); ε-correlated
  equilibrium (p. 101, informal, by subtracting ε in Eq. 4.19); coarse correlated
  equilibrium (p. 102, Moulin and Vial 1978, informal via restricted action modifiers)
- algorithms: none (LP construction deferred to 4.6.1)
- results: correlated equilibria ⊇ Nash equilibria, with Nash equilibrium as the
  independent-factorization special case (Osborne and Rubinstein 1994, p. 101) —
  stated, not proved in text
- figures: Figure 4.3 Chicken matrix game (p. 102)
- keywords: correlated equilibrium, coarse correlated equilibrium, action recommendation, Chicken game, private signal
- hmasd: curator_connection: central learning (Section 5.3.1) is explicitly named by the authors as producing a correlated joint policy, which is the game-theoretic solution class that any centralized-training component of HMASD-style architectures is implicitly targeting

### 4.6.1 Correlated Equilibrium via Linear Programming
- pages: 103–104
- chunks: B01-C0023
- summary: Gives the LP that computes a correlated equilibrium in a non-repeated
  normal-form game by maximizing social welfare subject to no-unilateral-deviation
  constraints over joint actions; a variant with weaker constraints computes a coarse
  correlated equilibrium instead. Notes this LP's variable/constraint counts (k^n for the
  simplex constraint, nk² for the CE deviation constraints, nk for the CCE deviation
  constraints) grow with the number of joint actions, unlike the two per-agent minimax
  LPs of Section 4.3.1.
- defines: correlated-equilibrium LP (p. 103, Eq. 4.20–4.23); coarse correlated
  equilibrium LP (p. 104, Eq. 4.24)
- algorithms: correlated-equilibrium-via-LP and coarse-correlated-equilibrium-via-LP
  constructions (unnumbered, p. 103–104)
- results: none
- figures: none
- keywords: linear programming, correlated equilibrium LP, joint-action variables, constraint growth
- hmasd: curator_connection: the explicit note that LP size grows in the number of joint actions (k^n) is the same combinatorial pressure the book later calls "scaling to many agents" (Section 5.4.4), directly relevant to HMASD's variable-N framing

### 4.7 Conceptual Limitations of Equilibrium Solutions
- pages: 104–105
- chunks: B01-C0023, B01-C0024
- summary: The authors list three conceptual limitations of equilibrium solutions
  (beyond the practical ε-Nash issues of Section 4.5): sub-optimality (an equilibrium's
  best-response property does not imply maximal returns, illustrated by Prisoner's
  Dilemma and the Chicken correlated-equilibrium example), non-uniqueness (multiple
  equilibria can yield different returns, which the authors name the "equilibrium
  selection" problem, further discussed in Section 5.4.2), and incompleteness (an
  equilibrium for sequential-move games does not prescribe behavior off the
  equilibrium path; the authors point to subgame-perfect and trembling-hand-perfect
  equilibrium as game-theoretic refinements addressing this, which the book does not
  itself develop further).
- defines: off-equilibrium path (p. 105, via Pr(ĥ|π)=0)
- algorithms: none
- results: none
- figures: none
- keywords: sub-optimality, non-uniqueness, incompleteness, equilibrium selection, subgame perfect equilibrium, trembling-hand perfect equilibrium
- hmasd: curator_connection: "equilibrium selection" is named here as a conceptual limitation and is one of the four MARL challenges the book returns to formally in Section 5.4.2 — a core obstacle any HMASD-style multi-agent skill-discovery method must contend with when multiple joint skill assignments are equally locally optimal

### 4.8 Pareto Optimality
- pages: 105–107
- chunks: B01-C0024
- summary: Introduces Pareto domination and Pareto optimality as a refinement to narrow
  the (possibly infinite) space of equilibrium solutions. States every game has at least
  one Pareto-optimal joint policy, and that in common-reward games all Pareto-optimal
  joint policies achieve the same, maximal, expected return. Illustrates the Pareto
  frontier of the Chicken game with a discretized 30x30 joint-policy sweep (900 joint
  policies) and connects it to a folk theorem: for infinitely repeated games under average
  reward, any expected joint return at or above the agents' minmax value is realizable by
  an equilibrium. Notes Pareto optimality alone is a weak solution concept — all
  zero-sum-game joint policies are trivially Pareto-optimal, and Pareto-optimal
  general-sum outcomes can still be highly unequal.
- defines: Pareto domination, Pareto optimality (p. 105, Definition 9, Eq. 4.25)
- algorithms: none
- results: existence of at least one Pareto-optimal joint policy in every game (p. 106,
  stated, no proof); folk theorem connecting Pareto frontier to realizable equilibria via
  minmax value under average reward (p. 107, stated, no proof)
- figures: Figure 4.4 feasible joint rewards and Pareto frontier in the Chicken game,
  900 discretized joint policies (p. 106)
- keywords: Pareto optimality, Pareto domination, Pareto frontier, minmax value, average reward, folk theorem
- hmasd: none

### 4.9 Social Welfare and Fairness
- pages: 107–109
- chunks: B01-C0024, B01-C0025
- summary: Defines welfare as the sum of agents' expected returns and fairness as their
  product (Nash social welfare), each inducing a corresponding optimality notion. Shows
  welfare-optimality implies Pareto-optimality (proof given) but not conversely, and that
  fairness-optimality neither implies nor is implied by Pareto-optimality. Notes welfare
  and fairness add no useful discriminating power in common-reward games (maximized
  exactly when each agent's return is maximized) or in two-agent zero-sum games (all
  minimax solutions tie on both). Illustrates fairness-optimality in the Battle of the
  Sexes game (Figure 4.5), where the two deterministic joint policies are the unique
  joint policies that are both Pareto- and fairness-optimal. Footnote flags the simple
  fairness definition's failure mode when any agent's return is zero or negative.
- defines: welfare, welfare optimality (p. 108, Definition 10, Eq. 4.26); fairness
  (Nash social welfare), fairness optimality (p. 108, Definition 11, Eq. 4.27)
- algorithms: none
- results: welfare optimality ⟹ Pareto optimality (p. 109, proof given by
  contradiction); Pareto optimality does not imply welfare optimality; fairness
  optimality and Pareto optimality are logically independent (p. 109, stated)
- figures: Figure 4.5 Battle of the Sexes game and its fairness-optimal outcomes (p. 109)
- keywords: social welfare, Nash social welfare, fairness, Battle of the Sexes, welfare optimality, fairness optimality
- hmasd: none

### 4.10 No-Regret
- pages: 109–112
- chunks: B01-C0025, B01-C0026
- summary: Introduces regret-based solution concepts, contrasting them with the
  best-response-based concepts of earlier sections: no-regret evaluates a sequence of
  policies across episodes rather than a single joint policy, framed by the authors as
  an instance of the "prescriptive agenda" (Section 1.5) concerned with learning-time
  performance. Defines regret as the gap between an agent's realized return and the best
  return it could have gotten from a fixed alternative action/policy against the
  observed history of opponent play, and no-regret as average regret going to 0 in the
  episode limit. Works a 10-episode Prisoner's Dilemma example (Figure 4.6) computing
  agent 1's regret. States the key conceptual limitation: regret assumes other agents'
  actions/policies stay fixed retrospectively, which is violated whenever opponents also
  adapt, so regret does not capture true counterfactuals; consequently minimizing regret
  need not maximize returns (illustrated again via Prisoner's Dilemma, where the unique
  no-regret joint policy is mutual defection). Distinguishes external (unconditional) from
  internal (conditional) regret and states their equilibrium-convergence connections.
- defines: regret for actions (p. 110, Eq. 4.28); no-regret (p. 110, Definition 12,
  Eq. 4.29); ε-no-regret (p. 110, informal); regret for policies, generalizing to
  stochastic games/POSGs (p. 111, Eq. 4.30); external (unconditional) vs. internal
  (conditional) regret (p. 112)
- algorithms: none
- results: in 2-agent zero-sum normal-form games, no-external-regret play's empirical
  action distribution converges to the set of minimax solutions; in general-sum
  normal-form games, no-external-regret converges to the set of coarse correlated
  equilibria and no-internal-regret converges to the set of correlated equilibria (Hart
  and Mas-Colell 2000; Young 2004) — stated, no proof (p. 112)
- figures: Figure 4.6 ten episodes of Prisoner's Dilemma used to compute agent 1's
  regret (p. 111)
- keywords: no-regret, external regret, internal regret, conditional regret, regret matching (forward reference), counterfactual
- hmasd: curator_connection: no-regret's explicit framing as a learning-time (prescriptive) criterion, distinct from a converged-solution criterion, matches how HMASD-adjacent work typically evaluates online skill-discovery performance rather than only the final skill set

### 4.11 The Complexity of Computing Equilibria
- pages: 112–113
- chunks: B01-C0026
- summary: Poses the question of whether equilibria can be computed in time polynomial
  in the size of the game, situating the discussion in algorithmic game theory. Notes
  P/NP are a poor fit since games always have at least one equilibrium (a "total search
  problem"), whereas computing an equilibrium with extra properties (Pareto optimal, a
  minimum per-agent return, a minimum social welfare, or fixed action-support
  constraints) is a genuine decision problem and each such variant is NP-hard (Gilboa
  and Zemel 1989; Conitzer and Sandholm 2008). States that minimax (Section 4.3.1) and
  correlated equilibrium (Section 4.6.1) are both polynomial-time computable via LP, but
  Nash equilibrium computation ("NASH") cannot be posed as an LP because of the
  independence assumption between agent policies, and is introduced as a PPAD-complete
  total search problem (detailed in 4.11.1–4.11.2).
- defines: total search problem (p. 113); NASH as the standard name for the Nash
  equilibrium computation problem in general-sum non-repeated normal-form games (p. 113)
- algorithms: none
- results: computing equilibria satisfying Pareto optimality, a minimum per-agent
  return, a minimum social welfare, or action-support constraints is NP-hard (Gilboa and
  Zemel 1989; Conitzer and Sandholm 2008, p. 113) — stated, no proof
- figures: none
- keywords: computational complexity, algorithmic game theory, P, NP, PPAD, total search problem, NASH
- hmasd: none

### 4.11.1 PPAD Complexity Class
- pages: 113–115
- chunks: B01-C0026
- summary: Defines PPAD ("polynomial parity argument for directed graphs") via its
  canonical complete problem END-OF-LINE: given implicit Parent/Child circuit functions
  on a directed graph of bit-string nodes with in/out-degree ≤ 1, and a source node, find
  another source or a sink node. Explains the "parity argument" (every source has a
  matching sink) guarantees a solution exists, but following the path from Parent/Child
  alone can require exponential time in the worst case. Notes P=PPAD? is open, PPAD
  contains longstanding hard problems (Brouwer fixed points, Arrow-Debreu market
  equilibria), and PPAD-hardness has been shown under cryptographic assumptions.
- defines: PPAD (p. 113); END-OF-LINE (p. 114, Definition 13); source node, sink node
  (p. 114–115); problem reduction (p. 113, footnote 16)
- algorithms: none
- results: PPAD-hardness under cryptographic assumptions (Bitansky, Paneth, and Rosen
  2015; Garg, Pandey, and Srinivasan 2016; Choudhuri et al. 2019) — cited, not proved in
  text (p. 115); no known polynomial-time algorithm exists for END-OF-LINE (p. 115,
  stated as an open/negative empirical fact of the research literature)
- figures: Figure 4.7 illustration of an END-OF-LINE instance's paths/cycles and a
  source node (p. 114)
- keywords: PPAD, END-OF-LINE, source node, sink node, parity argument, Brouwer fixed point, Arrow-Debreu equilibrium
- hmasd: none

### 4.11.2 Computing ε-Nash Equilibrium Is PPAD-Complete
- pages: 115–117
- chunks: B01-C0026
- summary: States that NASH (Nash equilibrium computation in general-sum non-repeated
  normal-form games) is PPAD-complete: first proven for 3+ agents (Daskalakis, Goldberg,
  and Papadimitriou 2006, 2009), then for exactly 2 agents (Chen and Deng 2006), with the
  approximate ε-Nash version proven PPAD-complete for certain ε bounds and the exact
  (ε=0) version PPAD-complete for the 2-agent case. Draws out the implication for MARL:
  since no known efficient algorithms solve PPAD-complete problems, MARL is unlikely to
  be a general "magic bullet" for computing Nash equilibria in polynomial time absent
  exploitable game structure; the field's progress has largely come from identifying and
  exploiting such structure. A footnote adds that approximating an actual Nash
  equilibrium within a fixed policy-space distance (rather than an ε-Nash equilibrium) is
  even harder — complete for a distinct class, FIXP (Etessami and Yannakakis 2010), for
  3+-agent general-sum normal-form games.
- defines: none (uses PPAD/NASH from 4.11 and 4.11.1)
- algorithms: none
- results: NASH is PPAD-complete for 3+ agents (Daskalakis, Goldberg, and Papadimitriou
  2006, 2009) and for 2 agents (Chen and Deng 2006) — stated theorem, no proof given in
  text (p. 115–116); approximating an actual Nash equilibrium within a fixed distance is
  FIXP-complete for 3+-agent general-sum normal-form games (Etessami and Yannakakis
  2010, p. 116, footnote 18, stated, no proof)
- figures: none
- keywords: PPAD-completeness, NASH, epsilon-Nash equilibrium, FIXP, approximate equilibrium hardness
- hmasd: curator_connection: the book's own stated implication — that no efficient general-purpose Nash-equilibrium algorithm is likely to exist without exploiting game structure — is a caution against reading any MARL/HMASD result as scaling generically; gains must be attributed to structure the method exploits, not to the algorithm class alone

### 4.12 Summary
- pages: 116–117
- chunks: B01-C0026
- summary: Recaps the chapter's solution-concept hierarchy (best response underlying
  minimax, Nash, and coarse/correlated equilibrium), notes equilibria need not be unique
  or return-maximizing, recaps the refinement concepts (Pareto optimality, welfare,
  fairness) and the alternative no-regret concept, and recaps the PPAD-completeness
  result and its implication that efficient general MARL algorithms for learning Nash
  equilibria likely do not exist. Transitions to Chapter 5's treatment of learning
  processes and challenges, and Chapter 6's algorithm families.
- defines: none
- algorithms: none
- results: none (summary of prior results)
- figures: none
- keywords: solution concept summary, equilibrium hierarchy, PPAD-completeness recap
- hmasd: none

### 5 Multi-Agent Reinforcement Learning in Games: First Steps and Challenges (chapter-level intro)
- pages: 118–119
- chunks: B01-C0027
- summary: Introduces reinforcement learning (repeated episodes of action, observation,
  reward) as the book's principal method for computing the solution concepts of Chapter
  4. Previews the chapter structure: a general learning framework and convergence types;
  the two basic single-agent reductions, central learning and independent learning; the
  four core MARL challenges (non-stationarity, equilibrium selection, multi-agent credit
  assignment, scaling to many agents); and self-play/mixed-play as two modes by which
  agents may or may not share a learning algorithm.
- defines: episode (p. 118, informal, reused from Chapter 2 terminology)
- algorithms: none
- results: none
- figures: Figure 5.1 elements of a general learning process in MARL (p. 119)
- keywords: reinforcement learning, episode, MARL challenges preview, self-play, mixed-play
- hmasd: none

### 5.1 General Learning Process
- pages: 119–121
- chunks: B01-C0027
- summary: Formalizes the MARL learning process: a game model (from Chapter 3); data
  Dz consisting of z histories from episodes; a learning algorithm L mapping (Dz, πz) to
  an updated joint policy πz+1; and a learning goal π* satisfying a chosen solution
  concept. Discusses nuances: policy conditioning depends on the game model (unconditioned
  in non-repeated normal-form games; on action histories in repeated normal-form games;
  on state-action histories in stochastic games; on own-observation histories in POSGs,
  possibly windowed); Dz may carry more information than the policies are conditioned on
  (e.g., centralized-training-with-decentralized-execution regimes, forward reference to
  Section 9.1); and L may itself decompose into per-agent algorithms Li using shared or
  agent-private data.
- defines: data set Dz (p. 119, Eq. 5.1); learning algorithm update rule (p. 120,
  Eq. 5.2); learning goal π* (p. 120, informal)
- algorithms: none
- results: none
- figures: none (Figure 5.1 introduced under the chapter intro, p. 119)
- keywords: learning process, learning algorithm, data set, policy conditioning, centralized training decentralized execution (forward reference)
- hmasd: curator_connection: the explicit statement that a learning algorithm may see more information (Dz) than the policies it produces are conditioned on is the book's own definition of the CTDE pattern HMASD-style hierarchical training relies on

### 5.2 Convergence Types
- pages: 121–123
- chunks: B01-C0027, B01-C0028
- summary: Defines the book's main theoretical convergence criterion — pointwise
  convergence of the joint policy πz to a solution π* as z→∞ (Eq. 5.3) — and three weaker
  criteria used when an algorithm cannot achieve pointwise convergence: convergence of
  expected return (Eq. 5.4), convergence of the empirical (time-averaged) joint-action
  distribution to a solution (Eq. 5.5–5.6), convergence of the empirical distribution to
  a set of solutions within any ε (Eq. 5.7), and convergence of average return across
  episodes (Eq. 5.8). States pointwise convergence (Eq. 5.3) implies all the weaker
  types, but none of the convergence types bound the returns of any single finite-z
  policy — in practice, algorithms are often instead monitored via learning curves of
  Ui(πz), which do not by themselves establish any relation to π*.
- defines: pointwise convergence to a solution (p. 121, Eq. 5.3); convergence of
  expected return (p. 121, Eq. 5.4); convergence of empirical distribution / averaged
  joint policy (p. 121–122, Eq. 5.5–5.6); convergence of empirical distribution to a set
  of solutions (p. 122, Eq. 5.7); convergence of average return (p. 122, Eq. 5.8)
- algorithms: none
- results: pointwise convergence (Eq. 5.3) implies expected-return, empirical-distribution, and average-return convergence (p. 123, stated, informal argument) — page flagged `equation_text_unreliable`
- figures: none
- keywords: convergence types, pointwise convergence, empirical distribution, average return, learning curve
- hmasd: none

### 5.3 Single-Agent RL Reductions
- pages: 123–129
- chunks: B01-C0028, B01-C0029
- summary: Introduces the two most basic ways to apply single-agent RL to a multi-agent
  problem: central learning, which learns one policy over the joint-action space, and
  independent learning, which applies single-agent RL separately per agent. Notes named
  algorithms that fail pointwise convergence but achieve weaker convergence types:
  fictitious play (empirical-distribution convergence, Fudenberg and Levine 1998),
  infinitesimal gradient ascent (average-return convergence, Singh, Kearns, and Mansour
  2000), and regret-matching (empirical-distribution-to-a-set convergence, Hart and
  Mas-Colell 2000) — all forward references to Chapter 6.
- defines: none (section-level intro; definitions appear in 5.3.1/5.3.2)
- algorithms: none (CQL and IQL detailed in the subsections)
- results: fictitious play's empirical action distribution converges to a Nash
  equilibrium (Eq. 5.5) in certain cases (Fudenberg and Levine 1998, p. 123); IGA's
  average rewards converge to those of a Nash equilibrium (Eq. 5.8) in non-repeated
  normal-form games (Singh, Kearns, and Mansour 2000, p. 123); regret-matching's
  empirical distributions converge to the set of (coarse) correlated equilibria
  (Eq. 5.7) in normal-form games (Hart and Mas-Colell 2000, p. 123) — all stated, no
  proof, forward references to Chapter 6 algorithms
- figures: none
- keywords: single-agent RL reduction, central learning, independent learning, fictitious play, infinitesimal gradient ascent, regret matching
- hmasd: none

### 5.3.1 Central Learning
- pages: 124–126
- chunks: B01-C0028
- summary: Central learning trains one policy πc over the full joint-action space
  A = A1×...×An, taking all agents' local observations and outputting a joint action —
  reducing the problem to single-agent RL, shown concretely as Central Q-learning (CQL,
  Algorithm 4). States that in common-reward games, using r = ri as the scalar reward
  and an optimal single-agent RL algorithm guarantees πc is Pareto-optimal (no policy
  gives any agent a higher return) and hence also a correlated equilibrium (no agent
  benefits from unilateral deviation); in zero-sum/general-sum games, no single scalar
  reward transformation is known to guarantee an equilibrium solution. Lists central
  learning's limitations: joint-action space grows exponentially in the number of agents
  (216 actions for 3 agents × 6 actions each in level-based foraging); and centralized
  execution may be physically/organizationally infeasible. Notes that in fully observable
  stochastic games an optimal deterministic central policy can always be decomposed into
  per-agent policies (Eq. 5.9, since MDPs admit deterministic optimal policies), but this
  decomposition breaks under partial observability (POSGs), motivating independent
  learning (5.3.2).
- defines: central policy πc; scalar-reward transformation for common-reward games
  (p. 124); central-policy decomposition into per-agent policies (p. 126, Eq. 5.9)
- algorithms: Algorithm 4 Central Q-learning (CQL) for stochastic games (p. 125) —
  information requirement: observes full state s, maintains Q(s,a) over the full joint
  action space
- results: with a common-reward scalarization and an optimal single-agent RL algorithm,
  central learning's learned πc is guaranteed Pareto-optimal and a correlated
  equilibrium in common-reward stochastic games (p. 124, argued, not a numbered theorem)
- figures: none
- keywords: central learning, Central Q-learning, CQL, joint-action space, reward scalarization, correlated equilibrium, exponential action growth
- hmasd: curator_connection: central learning's guarantee is scoped to common-reward games and requires an optimal single-agent solver over the full joint-action space — a scalability wall the book itself names (p. 124), directly bearing on any HMASD component that centralizes over N agents

### 5.3.2 Independent Learning
- pages: 126–128
- chunks: B01-C0028
- summary: Independent learning (IL) has each agent i learn its own policy from only its
  own local history of observations/actions/rewards, ignoring other agents, shown
  concretely as Independent Q-learning (IQL, Algorithm 5). States IL avoids central
  learning's exponential joint-action-space growth and needs no reward scalarization, but
  is vulnerable to non-stationarity from concurrent multi-agent learning: from agent i's
  perspective the other agents' changing policies become part of a formally
  non-stationary transition function Ti (Eq. 5.10). Surveys idealized-dynamics analyses,
  centering on Wunder, Littman, and Babes (2010), who study infinitesimal-step-size
  (α→0) IQL with ε-greedy exploration in 2-agent, 2-action general-sum normal-form games,
  classifying games into six subclasses by equilibrium structure and reporting whether
  IQL is predicted to converge (Figure 5.2); notably, class 3b (containing Prisoner's
  Dilemma) can show chaotic non-convergent behavior whose average reward exceeds the
  unique Nash equilibrium's. Notes independent learning remains a strong empirical
  baseline, citing Papoudakis et al. (2021) for competitiveness with more sophisticated
  MARL methods.
- defines: independent learning (p. 126); non-stationary per-agent transition function
  Ti (p. 126, Eq. 5.10)
- algorithms: Algorithm 5 Independent Q-learning (IQL) for stochastic games (p. 127) —
  information requirement: each agent observes only its own state/reward/action, no
  information about other agents
- results: idealized infinitesimal-step IQL convergence predictions across six 2-agent,
  2-action normal-form game subclasses (Wunder, Littman, and Babes 2010, p. 127–128,
  Figure 5.2) — theoretical/idealized-model result, page flagged `equation_text_unreliable`; independent learning is empirically competitive with more sophisticated MARL algorithms (Papoudakis et al. 2021, p. 127, cited empirical claim, not reproduced in this book)
- figures: Figure 5.2 IQL convergence table across six general-sum 2-agent, 2-action
  normal-form game subclasses (p. 128)
- keywords: independent learning, Independent Q-learning, IQL, non-stationarity, infinitesimal gradient dynamics, Prisoner's Dilemma chaos
- hmasd: curator_connection: Equation 5.10's formal statement of how other agents' changing policies enter agent i's transition function is the cleanest textbook definition of the non-stationarity problem that any HMASD skill-discovery agent trained concurrently with others must confront

### 5.3.3 Example: Level-Based Foraging
- pages: 128–130
- chunks: B01-C0028, B01-C0029, B01-C0030
- summary: Compares CQL and IQL empirically on a fixed 2-agent, 11x11-grid level-based
  foraging instance (Figure 5.3): both agents level 1, one item level 1 (collectible
  solo), one item level 2 (requires both agents), fixed start positions, γ=0.99, episodes
  cap at 50 steps, constant learning rate α=0.01, ε linearly decayed 1→0.05 over 80,000
  training steps, CQL's scalar reward is the summed individual rewards. Reports (Figure
  5.4, averaged over 50 independent training runs) that IQL learns faster early on
  because each IQL agent explores only 6 actions per state versus CQL's 36 (6²) joint
  actions, though both algorithms eventually converge to the same optimal joint policy
  (solved in 13 time steps).
- defines: none
- algorithms: none (uses Algorithm 4 CQL and Algorithm 5 IQL from 5.3.1/5.3.2)
- results: worked comparison of CQL vs. IQL on a single fixed 2-agent level-based
  foraging instance, 50 training runs (p. 129–130) — this is the authors' own
  demonstration, not a cited external study; both algorithms converge to the same
  13-step optimal joint policy, with IQL converging faster early due to its smaller
  per-state action space
- figures: Figure 5.3 the level-based foraging task instance, 11x11 grid, 2 agents
  (level 1 each), 2 items (levels 1 and 2) (p. 129); Figure 5.4 CQL vs. IQL average
  discounted evaluation returns over training, 50 runs, γ=0.99 (p. 130)
- keywords: level-based foraging, CQL vs IQL comparison, joint-action space size, sample efficiency, evaluation returns
- hmasd: none

### 5.4 Challenges of MARL (section intro)
- pages: 130–131
- chunks: B01-C0030
- summary: States that MARL algorithms (including CQL and IQL) inherit single-agent RL
  challenges — unknown dynamics, exploration-exploitation, bootstrapping
  non-stationarity, temporal credit assignment — and additionally face conceptual and
  algorithmic challenges specific to learning in a system of multiple concurrently
  learning agents. Names the four challenges the section will develop in turn:
  non-stationarity (5.4.1), equilibrium selection (5.4.2), multi-agent credit assignment
  (5.4.3), and scaling to many agents (5.4.4).
- defines: none
- algorithms: none
- results: none
- figures: none
- keywords: MARL challenges overview, non-stationarity, equilibrium selection, credit assignment, scaling
- hmasd: none

### 5.4.1 Non-Stationarity
- pages: 131–133
- chunks: B01-C0030
- summary: Defines stationarity for a stochastic process {Xt} (distribution of Xt+τ
  independent of τ) and shows that in single-agent RL, the state process is stationary
  under a fixed policy but non-stationary once learning updates the policy over time
  (the "moving target problem" for value estimation, e.g. Sarsa's bootstrapped target).
  In MARL, this is exacerbated: all agents update concurrently, so from agent i's
  perspective the other agents' changing policies (already formalized as Ti in Eq. 5.10,
  Section 5.3.2) make the environment appear non-Markovian, since it now depends on
  interaction history rather than just the current state. States that this breaks the
  usual stochastic-approximation convergence conditions for TD learning, and that all
  known MARL convergence results are restricted to narrow settings — specifically, IGA
  (Section 6.4.1) and WoLF-IGA (Section 6.4.3) provably converge (Eq. 5.8 and Eq. 5.3
  respectively) but only for normal-form games with exactly two agents and two actions.
  Illustrates non-stationarity's cyclic dynamics via two WoLF-PHC agents in Rock-Paper-
  Scissors converging toward the uniform Nash equilibrium (Figure 5.5).
- defines: stationary stochastic process (p. 131); non-stationarity / moving target
  problem (p. 132–133)
- algorithms: none (WoLF-PHC used only as illustration; algorithm detailed in Section
  6.4.4, outside range)
- results: IGA (Section 6.4.1) provably converges to the average reward of a Nash
  equilibrium (Eq. 5.8), and WoLF-IGA (Section 6.4.3) provably converges to a Nash
  equilibrium (Eq. 5.3) — both explicitly scoped by the authors to normal-form games
  with exactly two agents and two actions (p. 133, stated, proofs not given, forward
  references to Chapter 6)
- figures: Figure 5.5 two WoLF-PHC agents' evolving policies in non-repeated
  Rock-Paper-Scissors, converging toward the uniform-random Nash equilibrium (p. 132)
- keywords: non-stationarity, moving target problem, stochastic approximation, IGA, WoLF-IGA, WoLF-PHC, stationary process
- hmasd: curator_connection: the book's own scoping of its only cited convergence guarantees (IGA, WoLF-IGA) to two agents and two actions is exactly the kind of narrow-N result the corpus's `curator_boundary` fidelity rule warns against treating as evidence for variable- or large-N settings

### 5.4.2 Equilibrium Selection
- pages: 133–135
- chunks: B01-C0030
- summary: Revisits the multiple-equilibria problem from Section 4.7 using the Chicken
  game (three equilibria, returns (7,2), (2,7), ≈(4.66,4.66)) and introduces the Stag
  Hunt game (Figure 5.6b), where (S,S) is the Pareto-optimal, higher-reward but
  higher-risk "reward-dominant" equilibrium and (H,H) is the lower-reward,
  lower-risk "risk-dominant" equilibrium (each agent guarantees at least 2 by choosing
  H). Argues that algorithms such as IQL, uncertain about others' actions early in
  training, are prone to converging on the risk-dominant equilibrium via a
  self-reinforcing feedback loop. Surveys mitigation approaches: refining the solution
  space with Pareto optimality/welfare/fairness (Section 4.9); exploiting game
  structure (e.g., minimax Q-learning's benefit from unique zero-sum equilibrium values,
  Section 6.2.1; the Pareto actor-critic algorithm's use of common knowledge of the
  reward-dominant equilibrium in no-conflict games, Chapter 9); agent modeling (Section
  6.3) to predict others' actions; and inter-agent communication, which the authors note
  brings its own challenges (unverifiable or non-binding messages, and possible genuine
  preference conflicts over which equilibrium to select).
- defines: reward-dominant equilibrium, risk-dominant equilibrium (p. 134, informal, via
  Stag Hunt example)
- algorithms: none (minimax Q-learning, Pareto actor-critic, agent modeling are forward
  references)
- results: none (worked examples, not stated theorems)
- figures: Figure 5.6 Chicken and Stag Hunt matrix games (p. 134)
- keywords: equilibrium selection, Stag Hunt, reward-dominant equilibrium, risk-dominant equilibrium, agent modeling, communication
- hmasd: curator_connection: the risk-dominant convergence failure mode under independent learning is a direct analogue of the joint-skill-assignment coordination problem HMASD-style methods must avoid when multiple agents discover skills concurrently without communication

### 5.4.3 Multi-Agent Credit Assignment
- pages: 135–137
- chunks: B01-C0030, B01-C0031
- summary: Distinguishes temporal credit assignment (which past actions of one agent
  contributed to a reward) from multi-agent credit assignment (which agent(s)' actions
  contributed). Uses a three-robot level-based foraging example (Figure 5.7) where a
  shared +1 collect reward is given after two of three agents jointly collect an item;
  the authors argue disentangling which agent's action mattered requires understanding
  world dynamics (levels, positions, the collect action's success condition) that a
  learner observing only actions/states/reward cannot easily infer. States the problem
  is not specific to common-reward settings — even with per-agent differentiated
  rewards, an agent must still work out whether another agent's action contributed to
  its own reward. Notes multi-agent and temporal credit assignment compound over time.
  Argues joint-action value functions (as used in central learning) can disentangle
  contributions where independent per-agent action values cannot, illustrated via a
  Rock-Paper-Scissors example contrasting Q(s,a1) (which averages away the opponent's
  action) with Q1(s,a1,a2) (which represents it). Surveys two lines of remedy: difference
  rewards (Wolpert and Tumer 2002; Tumer and Agogino 2007), which counterfactually swap
  in a default/no-op action for one agent, noting the authors' caveat that a sensible
  default action may not always exist; and learned value-decomposition methods (Rashid
  et al. 2018; Sunehag et al. 2018; Son et al. 2019; Zhou, Liu, et al. 2020), detailed
  later in Chapter 9.
- defines: temporal credit assignment, multi-agent credit assignment (p. 135); joint-
  action value function Q1(s,a1,a2) (p. 137, informal, contrasted with per-agent Q(s,a1))
- algorithms: none (difference rewards and value-decomposition methods are named but not
  given as algorithms in this range)
- results: none (worked examples)
- figures: Figure 5.7 three-robot level-based foraging illustrating multi-agent credit
  assignment (p. 136)
- keywords: credit assignment, multi-agent credit assignment, temporal credit assignment, joint-action value function, difference rewards, value decomposition
- hmasd: curator_connection: the stated limitation of difference rewards ("generally unclear whether such a default action exists") is a direct boundary condition on any HMASD component that would try to attribute skill-level contributions to reward via a counterfactual no-op baseline

### 5.4.4 Scaling to Many Agents
- pages: 137–138
- chunks: B01-C0031
- summary: States the joint-action space grows as |A| = |A1|·…·|An| (Eq. 5.11),
  illustrated by level-based foraging growing from 216 joint actions at 3 agents to
  7,776 at 5 agents, with state space |S| also growing if per-agent features (e.g.
  positions) are part of the state. Notes joint-action-value algorithms (central
  Q-learning, joint-action learning) suffer growth in both representation size and
  sample requirements, while algorithms without joint-action values (independent
  learning) are still affected because more agents increase non-stationarity (each
  additional agent is another moving part) and worsen multi-agent credit assignment
  (each additional agent is another potential reward cause). Adds an explicit
  counter-example: joint-action-space growth is not universal — factoring a fixed global
  action vector (e.g., a 1,000-variable power plant, k^1,000 total actions) across n
  agents keeps the total number of joint actions constant (k^1,000) regardless of n, even
  as each agent's individual action space shrinks. Notes the exponential-growth challenge
  is not unique to MARL — it also affects single-agent reductions (central learning) and
  model-based multi-agent planning (Oliehoek and Amato 2016) — and that Part II of the
  book addresses scalability via deep learning techniques.
- defines: joint-action space size |A| (p. 137, Eq. 5.11)
- algorithms: none
- results: none
- figures: none
- keywords: scaling to many agents, joint-action space growth, action factoring, non-stationarity scaling, credit assignment scaling
- hmasd: curator_connection: the power-plant factoring counter-example is the book's own statement that "more agents" need not mean "more total actions" when the decomposition is by a fixed global action vector — directly relevant to how HMASD's variable-N claims should be scoped (growth is a property of the chosen decomposition, not of agent count per se)

### 5.5 What Algorithms Do Agents Use? (section intro)
- pages: 138–139
- chunks: B01-C0031
- summary: Notes that once independent learning allows each agent its own algorithm, two
  basic modes of operation follow: self-play, where all agents use the same learning
  algorithm (detailed in 5.5.1), and mixed-play, where agents use different learning
  algorithms (detailed in 5.5.2).
- defines: none
- algorithms: none
- results: none
- figures: none
- keywords: self-play, mixed-play, algorithm heterogeneity
- hmasd: none

### 5.5.1 Self-Play
- pages: 139–140
- chunks: B01-C0031
- summary: Distinguishes two senses of "self-play" the authors use: (1) algorithm
  self-play — all agents use the same learning algorithm (the assumption underlying
  essentially every MARL algorithm in the book, and the standard assumption in the
  game-theoretic "interactive learning" literature, which studies convergence to
  equilibria under a shared learning rule), used as a simplifying assumption because
  non-stationarity is worsened when agents use different learning approaches; and (2)
  policy self-play — a single agent's policy is trained directly against copies of
  itself (originating in zero-sum sequential games, e.g. TD-Gammon (Tesauro 1994), later
  combined with deep RL for champion-level play (Silver et al. 2017, 2018; Berner et al.
  2019), and extended by population-based training against a distribution of past/other
  policies (Lanctot et al. 2017; Jaderberg et al. 2019; Vinyals et al. 2019), detailed
  later in Sections 9.8–9.9). States policy self-play implies algorithm self-play, can
  learn faster by pooling all agents' experience into one policy, but requires
  symmetrical agent roles and egocentric observations; algorithm self-play has no such
  restriction and permits agents with different actions, observations, and rewards.
- defines: algorithm self-play, policy self-play (p. 139–140, informal, the authors'
  own terminology to disambiguate the two senses of "self-play")
- algorithms: none (TD-Gammon, AlphaGo/AlphaZero-class and OpenAI Five-class systems,
  and population-based training are named examples/forward references, not detailed
  here)
- results: none
- figures: none
- keywords: self-play, algorithm self-play, policy self-play, population-based training, TD-Gammon
- hmasd: none

### 5.5.2 Mixed-Play
- pages: 140–141
- chunks: B01-C0031, B01-C0032
- summary: Defines mixed-play as agents using different learning algorithms, giving
  trading markets (agents built by different organizations) and ad hoc teamwork (Stone
  et al. 2010; Mirsky et al. 2022 — collaborating with previously unknown agents) as
  motivating examples. Reports that Albrecht and Ramamoorthy (2012) empirically compared
  Nash-Q (Section 6.2), JAL-AM (Section 6.3.2), WoLF-PHC (Section 6.4.4), and a
  regret-matching variant (Section 6.5) across many normal-form games under several
  solution-concept-based metrics from Chapter 4, concluding there was no clear overall
  winner, each algorithm having relative strengths and weaknesses in mixed-play. Contrasts
  this with Papoudakis et al. (2021), which benchmarks deep-learning-based MARL algorithms
  (Chapter 9) only for algorithm self-play in common-reward games, and notes the authors'
  observation that no comparable benchmark yet exists for deep MARL algorithms in
  mixed-play settings.
- defines: mixed-play (p. 140, informal)
- algorithms: none (Nash-Q, JAL-AM, WoLF-PHC, regret matching are forward references to
  Chapter 6)
- results: no algorithm was a clear overall winner across many normal-form games in a
  mixed-play empirical comparison of Nash-Q, JAL-AM, WoLF-PHC, and regret matching
  (Albrecht and Ramamoorthy 2012, p. 140) — cited empirical study, not reproduced in
  this book
- figures: none
- keywords: mixed-play, ad hoc teamwork, algorithm comparison, Nash-Q, JAL-AM, WoLF-PHC, regret matching
- hmasd: curator_connection: the book's explicit gap — no benchmark yet exists for deep MARL algorithms in mixed-play settings — bounds any claim that HMASD-style methods, evaluated only in algorithm self-play, would behave the same way against heterogeneous learners

### 5.6 Summary
- pages: 141–143
- chunks: B01-C0032
- summary: Recaps the chapter: MARL learns joint policies satisfying a solution concept
  from episodic history data; several convergence criteria exist, from strict pointwise
  convergence to weaker empirical-distribution and average-return criteria; central and
  independent learning are the two basic single-agent RL reductions; non-stationarity
  (the "moving target problem," arising because other agents' policies change and break
  the Markov assumption) and equilibrium selection are named as key challenges, alongside
  multi-agent credit assignment and scaling to many agents (exponential joint-action-space
  growth); and algorithm self-play, policy self-play, and mixed-play are named as the
  book's basic modes for how agents relate to one another's learning algorithms.
  Transitions to Chapter 6's families of MARL algorithms that explicitly model
  multi-agent interaction to address one or more of these challenges. Notes (page
  118-141 range, just before the summary proper) that some algorithms extend the
  algorithm-self-play agenda toward best-responding to stationary opponents (Bowling and
  Veloso 2002; Banerjee and Peng 2004; Conitzer and Sandholm 2007) or toward "targeted
  optimality and safety" — achieving best-response returns against an assumed opponent
  class and at least a maxmin ("security") return otherwise (Powers and Shoham 2004,
  2005; Vu, Powers, and Shoham 2006; Chakraborty and Stone 2014).
- defines: targeted optimality and safety, security (maxmin) return (p. 141, informal)
- algorithms: none
- results: none (chapter recap)
- figures: none
- keywords: chapter summary, moving target problem, targeted optimality and safety, security return
- hmasd: none

### Chapter 6 — Multi-Agent Reinforcement Learning: Foundational Algorithms
- pages: 144–187
- chunks: B01-C0033–B01-C0042
- purpose: Building on Chapter 5's basic central-learning and independent-learning reductions of MARL to single-agent RL, this chapter introduces four families of foundational MARL algorithms that explicitly model or exploit the multi-agent structure of the interaction: joint-action learning (temporal-difference learning combined with game-theoretic solution concepts), agent modeling (learning explicit predictive models of other agents and best-responding to them), policy-based learning (direct gradient-ascent optimization of policy parameters), and no-regret learning (regret matching). All algorithms in this chapter are presented for normal-form games and stochastic games under full observability of states and actions; Part II of the book extends to deep-learning-based algorithms for the more general POSG model.
- prerequisites: not in my range (the preface, pp. 26–29, and Section 1.6 Book Contents and Structure, pp. 44–45, which the brief identifies as stating chapter dependencies, are both outside chunks B01-C0033–B01-C0042). Chapter 6 itself explicitly builds on Chapter 5 (general learning process, convergence types, central/independent learning, MARL challenges) and Chapter 4 (solution concepts: minimax, Nash equilibrium, correlated equilibrium, no-regret, best response), and reuses dynamic programming and TD-learning machinery from Chapter 2.

### 6.1 Dynamic Programming for Games: Value Iteration
- pages: 145–147
- chunks: B01-C0033, B01-C0034
- summary: Presents Shapley's (1953) value iteration procedure for zero-sum, two-agent stochastic games,
  analogous to MDP value iteration (Section 2.5). Each sweep builds, for every state, a matrix of one-step
  lookahead returns per agent and joint action, forms a non-repeated normal-form game from these matrices,
  and updates each agent's state value using the game's minimax value. The authors show the update operator
  is a γ-contraction mapping, so by the Banach fixed-point theorem repeated application converges to the
  unique optimal value functions V*_i, whose corresponding policies are stationary (state-conditioned only).
  In the single-agent case the algorithm reduces exactly to MDP value iteration.
- defines: γ-contraction mapping (p. 147); Banach fixed-point theorem application to Eq. 6.4 (p. 147)
- algorithms: Algorithm 6 Value iteration for stochastic games (p. 146)
- results: convergence of value iteration to the unique fixed point V*_i via the contraction-mapping/Banach
  argument (p. 147, proof sketch, cites Shapley 1953); reduction to MDP value iteration in the single-agent
  case (p. 147); equation_text_unreliable applies to Eqs. 6.1–6.8 on pp. 146–147 (Σ/Π-type operators may be
  misrendered)
- figures: none
- keywords: value iteration, stochastic games, Shapley 1953, minimax value, contraction mapping, Banach
  fixed-point theorem
- hmasd: curator_connection: value iteration's per-state minimax solve is a fixed two-agent, fixed-roster
  planning primitive; it offers no direct treatment of variable N but is useful background for any
  model-based/planning component that must construct a per-state local game.

### 6.2 Temporal-Difference Learning for Games: Joint-Action Learning
- pages: 147–155
- chunks: B01-C0034, B01-C0035
- summary: Motivates joint-action learning (JAL) as a response to the shortcomings of independent Q-learning
  (non-stationarity, credit assignment) and central Q-learning (reward scalarization). JAL-GT algorithms
  learn joint-action value functions Qj(s,a) for every agent, treat them as a per-state normal-form game Γs,
  and solve Γs with a game-theoretic solution concept to select actions and compute TD targets (Algorithm 7).
  The section covers three named instantiations (minimax, Nash, and correlated Q-learning) and closes by
  proving, via the NoSDE-game construction, that state-conditioned joint-action values can be structurally
  insufficient to recover a stochastic game's equilibrium policy.
- defines: joint-action Q-value Qπ_i(s,a) (Eq. 6.9, p. 148); per-state normal-form game Γs (Eq. 6.10, p. 148)
- algorithms: Algorithm 7 Joint-action learning with game theory (JAL-GT) (p. 149)
- results: soccer-game empirical comparison of minimax Q-learning vs. independent Q-learning (Figure 6.2,
  p. 151, reproduced from Littman 1994); NoSDE theorem on insufficiency of Q-values for equilibrium recovery
  (p. 154–155, detailed under 6.2.4)
- figures: Figure 6.1 grid-world soccer game (p. 151); Figure 6.2 win-rate/episode-length results table
  (p. 151); Figure 6.3 NoSDE game (p. 155)
- keywords: joint-action learning, JAL-GT, minimax Q-learning, Nash Q-learning, correlated Q-learning,
  equilibrium selection, temporal-difference learning
- hmasd: curator_connection: JAL-GT's requirement that the learning agent observe the joint action and every
  agent's reward each step, and maintain a Qj table per agent, is an explicit N-dependent information/
  communication assumption relevant to what "centralized training" must supply as N varies.

### 6.2.1 Minimax Q-Learning
- pages: 150–151
- chunks: B01-C0034
- summary: Minimax Q-learning (Littman 1994) instantiates JAL-GT by solving each state's normal-form game Γs
  via a minimax solution (linear programming, Section 4.3.1); it applies to two-agent zero-sum stochastic
  games and is the TD analogue of the value iteration algorithm of Section 6.1. The book reports Littman's
  simplified soccer-game experiment comparing minimax Q-learning to independent Q-learning against random,
  hand-built, and optimal (worst-case) opponents.
- defines: none (reuses the minimax solution concept from Section 4.3)
- algorithms: Minimax Q-learning (p. 150), an instance of Algorithm 7 (p. 149)
- results: minimax Q-learning "is guaranteed to learn the unique minimax value of the stochastic game under
  the assumption that all combinations of states and joint actions are tried infinitely often, as well as
  the usual conditions on learning rates" (p. 150, cites Littman and Szepesvári 1996, stated theorem without
  proof); soccer-game results (Figure 6.2, p. 151): minimax Q-learning wins 53.7% vs. the hand-built opponent
  (near the theoretical 50%) and 37.5% vs. the optimal opponent, while independent Q-learning wins 76.3% vs.
  the hand-built opponent (exploiting its weaknesses) but 0% vs. the optimal opponent (any deterministic
  policy is exploitable)
- figures: Figure 6.1 (p. 151); Figure 6.2 (p. 151)
- keywords: minimax Q-learning, Littman 1994, zero-sum stochastic games, soccer game, worst-case robustness
- hmasd: none

### 6.2.2 Nash Q-Learning
- pages: 152
- chunks: B01-C0034
- summary: Nash Q-learning (Hu and Wellman 2003) instantiates JAL-GT by solving Γs for a Nash equilibrium and
  applies to general-sum stochastic games with any finite number of agents. Convergence to a Nash equilibrium
  is guaranteed only under highly restrictive structural conditions on every normal-form game the algorithm
  encounters, in addition to the usual infinite-exploration and learning-rate conditions. The authors note
  these conditions are unlikely to hold in practice and illustrate, via Prisoner's Dilemma, that global
  optimality is strictly stronger than Pareto optimality.
- defines: global optimum joint policy (p. 152); saddle point joint policy (p. 152)
- algorithms: Nash Q-learning (p. 152), an instance of Algorithm 7 (p. 149)
- results: Nash Q-learning convergence to a Nash equilibrium requires (in addition to infinite exploration
  and standard learning-rate conditions) that every encountered normal-form game Γs consistently has either
  (a) a global optimum or (b) a saddle point (p. 152, stated theorem without proof); the authors state this
  is "highly restrictive" and "unlikely to exist... let alone in all of the encountered games" (p. 152)
- figures: none
- keywords: Nash Q-learning, Hu and Wellman 2003, global optimum, saddle point, restrictive convergence
  assumptions
- hmasd: curator_boundary: the stated Nash Q-learning convergence guarantee is conditioned on every
  per-state game encountered during learning satisfying the global-optimum-or-saddle-point property; this is
  not evidence that Nash Q-learning converges in general N-agent stochastic games lacking that structure.

### 6.2.3 Correlated Q-Learning
- pages: 153
- chunks: B01-C0035
- summary: Correlated Q-learning (Greenwald and Hall 2003) instantiates JAL-GT by solving Γs for a
  correlated equilibrium, which spans a wider (and potentially higher-return) solution space than Nash
  equilibrium and can be computed via linear rather than quadratic programming. Because a correlated
  equilibrium may not factor into independent per-agent policies, Algorithm 7's action-selection step is
  modified so the agent samples a joint action from the equilibrium and takes only its own component. The
  authors state that, in general, no formal convergence conditions are known for this algorithm.
- defines: none (reuses correlated equilibrium and its selection mechanisms from Section 4.6, applied via
  Greenwald and Hall 2003)
- algorithms: Correlated Q-learning (p. 153), a modified instance of Algorithm 7 (p. 149)
- results: none — the text explicitly states "no formal conditions are known under which correlated
  Q-learning converges to a correlated equilibrium of the stochastic game" (p. 153)
- figures: none
- keywords: correlated Q-learning, Greenwald and Hall 2003, correlated equilibrium, linear programming,
  equilibrium selection
- hmasd: none

### 6.2.4 Limitations of Joint-Action Learning
- pages: 153–155
- chunks: B01-C0035
- summary: Shows a structural limitation shared by all JAL-GT algorithms: because Qj(s,a) is conditioned
  only on state, any derived equilibrium is stationary, and in "turn-taking" stochastic games (only one
  agent has more than one available action in any given state) any equilibrium concept reduces to a
  max-operator over Qi. The authors present the NoSDE ("No Stationary Deterministic Equilibrium") example
  game (Zinkevich, Greenwald, and Littman 2005) and its accompanying theorem, showing two NoSDE games can
  share identical equilibrium Q-values while their unique equilibrium policies give different expected
  returns to some agent.
- defines: stationary equilibrium (p. 153); NoSDE games (p. 154)
- algorithms: none
- results: Theorem (Zinkevich, Greenwald, and Littman 2005), Eq. 6.12 (p. 154): for any NoSDE game Γ with a
  unique equilibrium π*, there exists another NoSDE game Γ̃ (differing only in reward functions) with unique
  equilibrium π̃* ≠ π*, such that Qπ*,Γ_i = Qπ̃*,Γ̃_i for all agents i, yet Vπ*,Γ_i ≠ Vπ̃*,Γ̃_i for some agent i —
  cited/stated without an in-text proof; equation_text_unreliable applies to Eq. 6.12 and surrounding text
  on p. 154–155
- figures: Figure 6.3 NoSDE game (p. 155)
- keywords: NoSDE games, stationary equilibrium, joint-action value insufficiency, Zinkevich Greenwald
  Littman 2005, turn-taking stochastic games
- hmasd: curator_boundary: this result bounds what state-conditioned joint-action value functions can
  recover in principle, demonstrated via a specific small (two-state, two-agent, deterministic-transition)
  counterexample; it is an existence/possibility result, not a general claim that all JAL-GT-style algorithms
  fail on all games, and it says nothing about behavior as N grows.

### 6.3 Agent Modeling
- pages: 156–168
- chunks: B01-C0036, B01-C0037, B01-C0038
- summary: Introduces agent modeling (opponent modeling) as an alternative to JAL-GT's normative
  game-theoretic assumptions: instead of assuming worst-case or equilibrium play, a learning agent builds an
  explicit predictive model of another agent's behavior from observations and computes a best response to
  it. Covers the dominant approach, policy reconstruction, framed as a supervised-learning problem over
  observed (state, action) pairs of the modeled agent, and formalizes best-response selection with respect
  to a set of learned models (Eq. 6.13).
- defines: agent model / opponent modeling (p. 156); policy reconstruction (p. 156); best response to agent
  models πi ∈ BRi(π̂−i) (Eq. 6.13, p. 157)
- algorithms: none at this level (see 6.3.1–6.3.3)
- results: none
- figures: Figure 6.4 general agent model diagram (observations → prediction) (p. 157)
- keywords: agent modeling, opponent modeling, policy reconstruction, best response
- hmasd: curator_connection: the "observations → prediction" agent-model schema (Figure 6.4) is a
  plain-language analogue of what an agent-conditioned skill or teammate-intent representation must supply
  as N varies.

### 6.3.1 Fictitious Play
- pages: 157–159
- chunks: B01-C0036
- summary: Presents fictitious play (Brown 1951; Robinson 1951), one of the earliest agent-modeling
  algorithms, defined for non-repeated normal-form games. Each agent models the others as stationary
  distributions given by the empirical frequency of their past actions (Eq. 6.14) and selects a myopic,
  deterministic best-response action (not policy) against these models (Eq. 6.15). Because the chosen action
  is deterministic, fictitious play cannot itself represent randomized equilibrium policies, but its
  empirical action distribution can converge to one; the book states four convergence properties and
  illustrates them on Rock-Paper-Scissors.
- defines: fictitious-play empirical agent model (Eq. 6.14, p. 157); myopic best-response action selection
  (Eq. 6.15, p. 158)
- algorithms: Fictitious play (p. 157), not numbered as "Algorithm N"
- results: four convergence properties stated for fictitious play (p. 159, cited to Fudenberg and Levine
  1998, not proved in text): (1) if agents' actions converge, the converged actions form a Nash equilibrium;
  (2) if actions ever form a Nash equilibrium, they remain there in all subsequent episodes; (3) if the
  empirical action distributions converge, they converge to a Nash equilibrium; (4) empirical distributions
  are known to converge in several game classes, including two-agent zero-sum games with finite action sets
  (Robinson 1951); worked Rock-Paper-Scissors example converging to the unique uniform-random Nash
  equilibrium (Figures 6.5, 6.6, pp. 158–159)
- figures: Figure 6.5 empirical action-distribution evolution on Rock-Paper-Scissors (p. 158); Figure 6.6
  first ten episodes, joint actions/models/action values (p. 159)
- keywords: fictitious play, Brown 1951, Robinson 1951, empirical distribution, myopic best response,
  Rock-Paper-Scissors
- hmasd: none

### 6.3.2 Joint-Action Learning with Agent Modeling
- pages: 160–162
- chunks: B01-C0036, B01-C0037
- summary: Extends fictitious play to stochastic games as JAL-AM (Algorithm 8). Agent models are now
  state-conditioned empirical distributions (Eq. 6.16) rather than stationary ones; the algorithm combines
  joint-action values Qi with these models to compute a best-response action value AVi (Eq. 6.17) and select
  best-response actions, deriving TD targets from AVi. Unlike JAL-GT, JAL-AM does not require observing other
  agents' rewards and maintains only its own Qi. The book reports an empirical comparison to independent
  Q-learning (IQL) and central Q-learning (CQL) on the level-based foraging task, averaged over fifty runs.
- defines: state-conditioned agent model π̂j(aj|s) (Eq. 6.16, p. 160); best-response action value AVi(s,ai)
  (Eq. 6.17, p. 161)
- algorithms: Algorithm 8 Joint-action learning with agent modeling (JAL-AM) (p. 161)
- results: informal convergence statement — if the true policy πj is fixed or converges and is state-only
  conditioned, then in the limit of observing every (s,aj) pair infinitely often, π̂j converges to πj (p. 161,
  not proved in text); empirical comparison (Figure 6.7, p. 162, fifty independent training runs,
  level-based foraging from Figure 5.3): JAL-AM converges to the optimal joint policy after about 500,000
  training steps vs. about 600,000 for IQL, with lower variance in evaluation returns than both IQL and CQL
- figures: Figure 6.7 JAL-AM vs. CQL vs. IQL learning curves, level-based foraging (p. 162)
- keywords: JAL-AM, agent modeling, best-response action value, level-based foraging, variance reduction
- hmasd: curator_connection: JAL-AM's information requirement (own Qi plus per-agent state-conditioned
  models, no observation of other agents' rewards) is a lighter-weight centralized-training assumption than
  JAL-GT and is directly relevant to what information a routine/curator must supply as N scales.

### 6.3.3 Bayesian Learning and Value of Information
- pages: 163–169
- chunks: B01-C0037, B01-C0038, B01-C0039
- summary: Extends agent modeling to maintain an explicit belief (probability distribution) over a space of
  candidate models for each other agent, updated by a Bayesian posterior (Eq. 6.18) rather than committing to
  a single point model. Defines the value of information (VI), a recursive best-response criterion
  (Eqs. 6.19–6.20) that trades off exploiting current beliefs against exploring actions that reveal
  information about other agents' true models, illustrated with a repeated Prisoner's Dilemma example using
  two candidate opponent models (Coop, Grim). Connects the approach to "rational learning" in game theory and
  states its convergence result together with the "absolute continuity" condition it requires, and a case
  where that condition is violated.
- defines: belief over agent models Pr(π̂j | h) (p. 165–166); Bayesian belief update (Eq. 6.18, p. 166);
  Dirichlet-distribution belief representation with pseudocounts (p. 166–167); value of information
  VIi(ai|h) (Eq. 6.19, p. 167); recursive action-value Qi(h,a) with VI in place of the max-operator's Qi
  (Eq. 6.20, p. 167); absolute continuity assumption (p. 169)
- algorithms: none numbered; VI-based best-response action selection at_i ∈ arg max_ai VIi(ai|h) (p. 168)
- results: worked Prisoner's Dilemma example values VI1(C) = −9, VI1(D) = −13.5 in the initial time step
  (Eq. 6.21, p. 168), and VIi(C) = −1, VIi(D) = 0 in the final time step (Eq. 6.22, p. 168), yielding
  mutual cooperation followed by defection in the last step (an "end-game effect," cross-referenced to
  Section 3.2); rational-learning convergence result (Kalai and Lehrer 1993, cited, not proved in text): under
  strict assumptions including "absolute continuity," agents' predictions of future play converge to the true
  distribution of play and their policies converge to a Nash equilibrium (p. 168); the authors show absolute
  continuity can be violated by a skewed prior (0.8 Coop / 0.2 Grim), producing initial mutual defection not
  predicted by either candidate model (p. 169); equation_text_unreliable applies to Eqs. 6.19–6.20 (p. 167)
- figures: Figure 6.8 Prisoner's Dilemma payoff matrix and Coop/Grim finite-state models (p. 164); Figure 6.9
  value-of-information illustration (p. 165); Figure 6.10 Dirichlet belief evolution over episodes,
  Rock-Paper-Scissors (p. 166)
- keywords: Bayesian learning, type-based reasoning, value of information, Dirichlet distribution, rational
  learning, absolute continuity, Prisoner's Dilemma
- hmasd: curator_connection: the VI recursion's explicit trade-off between exploiting current beliefs and
  exploring to reduce uncertainty about a co-agent's latent model is conceptually close to what a skill or
  intent-discovery module must do when the population of co-agents is not fixed, though the book's worked
  construction uses a fixed, small (two-model), known candidate space.

### 6.4 Policy-Based Learning
- pages: 169–179
- chunks: B01-C0039, B01-C0040
- summary: Introduces the third algorithm family, which directly parameterizes and optimizes agents'
  policies via gradient ascent rather than deriving them from learned values. The authors motivate this by
  the limitations of the value-based families already covered: JAL-GT's Q-values can be insufficient to
  recover an equilibrium (Section 6.2.4), and best-response-action methods (fictitious play, JAL-AM) cannot
  represent randomized equilibrium policies (Section 6.3). Policy-based methods can directly represent and
  learn probabilistic (mixed-strategy) equilibria.
- defines: none at this level (see 6.4.1–6.4.5)
- algorithms: none at this level
- results: none
- figures: none
- keywords: policy-based learning, gradient ascent, probabilistic equilibria
- hmasd: none

### 6.4.1 Gradient Ascent in Expected Reward
- pages: 169–171
- chunks: B01-C0039
- summary: Derives basic gradient-ascent policy learning for two-agent, two-action general-sum normal-form
  games. Each agent's policy reduces to a single probability parameter (α or β); expected reward Ui(α,β) is
  written in closed form (Eqs. 6.25–6.28), and each agent updates its own parameter along the partial
  derivative of its own expected reward (Eqs. 6.29–6.32), with gradients projected back onto the unit square
  at its boundary. The authors flag the strong knowledge assumption this implies: each agent must know its
  own reward matrix and the other agent's policy in the current episode.
- defines: two-agent, two-action policy parameterization πi=(α,1−α), πj=(β,1−β) (Eq. 6.24, p. 170); expected
  rewards Ui(α,β), Uj(α,β) (Eqs. 6.25–6.26, p. 170); gradient-ascent update rule (Eqs. 6.29–6.32, p. 171)
- algorithms: gradient-ascent learning in expected reward (p. 170), unnamed/not "Algorithm N" numbered
- results: none (definitional section)
- figures: none
- keywords: gradient ascent, expected reward, normal-form games, reward-matrix knowledge assumption
- hmasd: curator_boundary: this method assumes each agent knows its own reward matrix exactly and observes
  the other agent's current policy each episode; it is not evidence for learning under partial observability,
  unknown reward structure, or unknown/varying opponent identity.

### 6.4.2 Learning Dynamics of Infinitesimal Gradient Ascent
- pages: 171–174
- chunks: B01-C0039
- summary: Analyzes the κ→0 limit of the gradient-ascent rule (infinitesimal gradient ascent, IGA) as a
  continuous-time affine dynamical system (Eq. 6.33) with a closed-form center point (Eq. 6.34). Classifies
  the joint-policy trajectory into three types by the eigenvalues of the system matrix F (non-invertible,
  purely real, purely imaginary), each tied to which game classes (common-reward, zero-sum, general-sum) can
  produce it, and states convergence properties culminating in a characterization of when convergence occurs.
- defines: infinitesimal gradient ascent (IGA) (p. 172); center (zero-gradient) point (α*,β*) (Eq. 6.34,
  p. 172)
- algorithms: Infinitesimal Gradient Ascent (IGA) (p. 172), unnumbered
- results: three trajectory types classified by the eigenvalues of F (p. 172–173, Singh, Kearns, and Mansour
  2000), each linked to which game classes can/cannot produce it (e.g., purely imaginary eigenvalues, giving
  ellipse trajectories, cannot occur in common-reward games); three stated properties of the learning
  dynamics (p. 173–174, cited without full in-text proof): (α,β) need not converge in all cases; if it does
  not converge, the average rewards received converge to the expected rewards of some Nash equilibrium (the
  convergence type of Eq. 5.8, Section 5.2); if (α,β) does converge, the converged joint policy is a Nash
  equilibrium; the result is also stated to extend to finite step sizes κ_k = 1/k^(2/3) if appropriately
  reduced (Singh, Kearns, and Mansour 2000); equation_text_unreliable applies to this chunk
- figures: Figure 6.11 three IGA trajectory types by eigenvalue class (p. 173)
- keywords: infinitesimal gradient ascent, IGA, dynamical systems, eigenvalues, Nash-equilibrium
  convergence, average-reward convergence
- hmasd: none

### 6.4.3 Win or Learn Fast
- pages: 173–176
- chunks: B01-C0039, B01-C0040
- summary: Notes that IGA's average-reward convergence (Section 6.4.2) is a weak guarantee since it permits
  arbitrarily low instantaneous reward compensated later, and does not require the actual joint policy to
  converge pointwise. Introduces WoLF-IGA (Bowling and Veloso 2002), which varies each agent's step size
  between lmin (when "winning," i.e., doing at least as well as an equilibrium policy) and lmax (when
  "losing"): the WoLF ("win or learn fast") principle is to adapt quickly when losing and slowly when
  winning. States that this variable-rate scheme provably converges to a Nash equilibrium in the two-agent,
  two-action, general-sum case.
- defines: win or learn fast (WoLF) principle (p. 174); variable learning-rate rule (Eqs. 6.37–6.38, p. 174);
  WoLF-IGA update (Eqs. 6.35–6.36, p. 174)
- algorithms: WoLF-IGA (p. 174), unnumbered extension of IGA
- results: WoLF-IGA "is guaranteed to converge to a Nash equilibrium in general-sum games with two agents
  and two actions" (p. 175, stated theorem without proof, Bowling and Veloso 2002); in the previously
  problematic purely-imaginary-eigenvalue case, WoLF-IGA trajectories become piecewise elliptical across the
  four quadrants around the unique center point and spiral inward, tightening each quadrant by a factor of
  sqrt(lmin/lmax) < 1 (p. 175–176); equation_text_unreliable applies to these pages
- figures: Figure 6.12 WoLF-IGA spiral trajectory to the Nash-equilibrium center point (p. 175)
- keywords: WoLF, win or learn fast, WoLF-IGA, variable learning rate, Nash-equilibrium convergence,
  Bowling and Veloso 2002
- hmasd: none

### 6.4.4 Win or Learn Fast with Policy Hill Climbing
- pages: 176–178
- chunks: B01-C0040
- summary: Presents WoLF-PHC (Bowling and Veloso 2002, Algorithm 9), which generalizes the WoLF principle to
  general-sum stochastic games with any finite number of agents and actions, and removes the requirement of
  knowing reward functions or other agents' policies. The algorithm learns standard action values Q(s,ai) and
  updates a policy πi toward the current greedy policy at a WoLF-varying rate, using an empirically averaged
  own-policy π̄i in place of the (unknown) Nash equilibrium policy used by WoLF-IGA's winning/losing test.
  Convergence is illustrated only empirically, on Rock-Paper-Scissors; no formal convergence theorem for
  WoLF-PHC itself is stated in this section.
- defines: average policy π̄i (Eq. 6.42, p. 177); WoLF-PHC policy-update term Δ(s,ai) (Eqs. 6.44–6.46,
  p. 176)
- algorithms: Algorithm 9 Win or learn fast with policy hill climbing (WoLF-PHC) (p. 177)
- results: informal justification that the averaged policy π̄i "replaces" the unknown Nash equilibrium
  policy, by analogy to fictitious play's average-distribution convergence property (p. 176, not a formal
  theorem); empirical demonstration on non-repeated Rock-Paper-Scissors (Figure 6.13, p. 178): agents'
  policies co-adapt and converge smoothly (circular trajectories) to the uniform-random Nash equilibrium,
  contrasted with fictitious play's triangular trajectories (Figure 6.5); equation_text_unreliable applies to
  these pages
- figures: Figure 6.13 WoLF-PHC policy trajectories on Rock-Paper-Scissors (p. 178)
- keywords: WoLF-PHC, policy hill climbing, Bowling and Veloso 2002, average policy, stochastic games
- hmasd: curator_connection: WoLF-PHC's use of an empirically averaged own-policy as a model-free stand-in
  for an unknown equilibrium policy is a training-rate heuristic the book itself presents without a formal
  convergence proof, relevant to any credit/opponent-agnostic training-rate design choice.

### 6.4.5 Generalized Infinitesimal Gradient Ascent
- pages: 178–180
- chunks: B01-C0040, B01-C0041
- summary: Generalizes IGA to normal-form games with more than two agents and actions, called GIGA
  (Zinkevich 2003). GIGA updates a policy via an unconstrained gradient in the actual (realized) reward
  against the other agent's most recently observed action, then projects the result back onto the simplex of
  valid probability distributions (Eqs. 6.50–6.51). Unlike IGA, GIGA does not require knowledge of the other
  agents' policies, only their past actions. The authors state GIGA achieves no-regret (hence so does IGA),
  and that its empirical action distribution converges to a coarse correlated equilibrium.
- defines: expected reward against an observed opponent action Ui(πi,aj) (Eq. 6.47, p. 178); GIGA update
  rule with projection operator P(x) (Eqs. 6.50–6.51, p. 179)
- algorithms: Generalized Infinitesimal Gradient Ascent (GIGA) (p. 179), unnumbered
- results: Zinkevich (2003) result (cited, not proved in text): with step size κ_k = 1/√k, GIGA achieves
  no-regret as k→∞; explicit regret bound Regret^k_i ≤ [√k + (√k−1)/2]·|Ai|·r²max (Eq. 6.52, p. 180); the
  average regret therefore →0 as k→∞, satisfying the no-regret criterion of Definition 12 (Section 4.10);
  the no-regret property is further stated to imply the empirical action distribution converges to a coarse
  correlated equilibrium (p. 180); all results stated to extend to n>2 agents by replacing j with −i (p. 180);
  equation_text_unreliable applies to pp. 179–180
- figures: none
- keywords: GIGA, generalized infinitesimal gradient ascent, no-regret, Zinkevich 2003, coarse correlated
  equilibrium, projection operator
- hmasd: none

### 6.5 No-Regret Learning
- pages: 180–182
- chunks: B01-C0041
- summary: Introduces regret matching (Hart and Mas-Colell 2000) as a family of no-regret learners that
  associate regrets with not having chosen particular actions in past episodes and assign action
  probabilities proportional to positive average regret. States that regret matching's empirical action
  distributions converge to the set of (coarse) correlated equilibria of normal-form games.
- defines: no-regret learner (p. 180, invoking Section 4.10's Definition 12); regret matching (p. 180)
- algorithms: none at this level (see 6.5.1, 6.5.2)
- results: none
- figures: none
- keywords: no-regret learning, regret matching, Hart and Mas-Colell 2000/2001, coarse correlated
  equilibrium
- hmasd: none

### 6.5.1 Unconditional and Conditional Regret Matching
- pages: 180–182
- chunks: B01-C0041
- summary: Defines the two regret-matching variants analyzed later. Unconditional regret matching sets
  action probabilities proportional to the positive part of average unconditional regret accumulated over
  all past episodes (Eqs. 6.53–6.55). Conditional regret matching instead conditions the regret on episodes
  in which the agent chose a specific reference action (Eqs. 6.56–6.58), with a bias parameter η lower-
  bounded to guarantee valid probabilities. Both variants are illustrated on Prisoner's Dilemma, where the
  dominant-action structure makes them behaviorally identical (deterministic defection after the first
  episode).
- defines: unconditional regret Regret^z_i(ai) (Eq. 6.53, p. 181); average unconditional regret (Eq. 6.54,
  p. 181); unconditional regret-matching policy update (Eq. 6.55, p. 181); conditional regret
  Regret^z_i(a'i,ai) (Eq. 6.56, p. 181); average conditional regret (Eq. 6.57, p. 181); conditional
  regret-matching policy update (Eq. 6.58, p. 182), requiring η > 2·max_a|Ri(a)|·(|Ai|−1)
- algorithms: Unconditional regret matching (p. 181); Conditional regret matching (p. 181), both unnumbered
- results: worked example on Prisoner's Dilemma (p. 182): since defection is a dominant action, the
  unconditional regret for cooperation is never positive, so both regret-matching variants assign probability
  1 to defect in every episode after the first; equation_text_unreliable applies to these pages
- figures: none
- keywords: unconditional regret matching, conditional regret matching, Hart and Mas-Colell 2000, Prisoner's
  Dilemma, dominant action
- hmasd: none

### 6.5.2 Convergence of Regret Matching
- pages: 182–185
- chunks: B01-C0041, B01-C0042
- summary: States and derives the convergence results for regret matching: both variants' average regrets
  are bounded by κ/√z (Hart and Mas-Colell 2000, attributed to Blackwell's Approachability Theorem 1956),
  a bound that requires no assumption about other agents' behavior. The authors derive that this implies
  convergence of the empirical joint-action distribution to a correlated equilibrium (conditional variant) or
  coarse correlated equilibrium (unconditional variant) — explicitly not pointwise convergence of the
  policies themselves, contrasted directly against the stronger convergence type of Equation 5.3.
  Illustrates unconditional regret matching on Rock-Paper-Scissors: the actual policies show no convergent
  behavior over 10,000 episodes, yet the empirical distribution converges steadily to the game's unique Nash
  equilibrium.
- defines: none new (builds on the regret definitions from 6.5.1)
- algorithms: none
- results: regret bound κ·(1/√z) for both regret-matching variants, independent of other agents' behavior
  (p. 182, Hart and Mas-Colell 2000; Approachability Theorem, Blackwell 1956); derivation (Eqs. 6.59–6.64,
  pp. 182–183, equation_text_unreliable) showing conditional regret matching's empirical joint-action
  distribution satisfies the correlated-equilibrium defining inequality (Eq. 4.19) as z→∞, hence converges to
  the set of correlated equilibria (the unconditional variant analogously converges to coarse correlated
  equilibria); the text explicitly notes this is not pointwise convergence of π^z_i as per Eq. 5.3 (p. 183);
  empirical demonstration on Rock-Paper-Scissors (Figures 6.14, 6.15, pp. 183–185): actual policies show no
  convergent trajectory over 10,000 episodes while empirical distributions converge to the uniform-random
  Nash equilibrium, and average regrets decay toward the zero line with persistent oscillation caused by
  mutual adaptation
- figures: Figure 6.14 RPS policy vs. empirical-distribution trajectories (p. 183–184); Figure 6.15 average
  unconditional regret over 10,000 episodes (p. 185)
- keywords: convergence of regret matching, correlated equilibrium, coarse correlated equilibrium,
  Approachability Theorem, Blackwell 1956, empirical-distribution convergence
- hmasd: curator_boundary: regret matching's proven convergence is of the empirical joint-action
  distribution to a (coarse) correlated equilibrium set, not of the agents' actual policies to a single
  equilibrium — a materially weaker guarantee than WoLF-PHC's pointwise-convergence claim, and the two should
  not be conflated when citing "convergence" for either family.

### 6.6 Summary
- pages: 185–187
- chunks: B01-C0042
- summary: Chapter-closing recap of the four algorithm families covered — value iteration for stochastic
  games; joint-action learning via minimax/Nash/correlated Q-learning; agent modeling via fictitious play,
  JAL-AM, and Bayesian/value-of-information methods; policy-based learning via the IGA family
  (IGA/WoLF-IGA/WoLF-PHC/GIGA); and no-regret learning via unconditional/conditional regret matching — each
  restated with its convergence type. Explicitly notes that regret matching achieves zero regret and
  empirical-distribution convergence to (coarse) correlated equilibria. Closes Part I of the book; Part II
  introduces deep-learning-based MARL algorithms building on these foundations.
- defines: none
- algorithms: none (recap only)
- results: none (recap of results already indexed under 6.1–6.5)
- figures: none
- keywords: chapter summary, joint-action learning, agent modeling, policy-based learning, no-regret
  learning, Part I conclusion
- hmasd: none

### Chapter 7 — Deep Learning
- pages: 190–211 (Part II introduction precedes at pp. 188–189, within chunk B01-C0043)
- chunks: B01-C0043 – B01-C0047
- purpose: Introduces deep learning as a general function-approximation framework to motivate its use in RL/MARL: why tabular representations fail to generalize and scale (7.1), linear function approximation as a first, feature-limited fix (7.2), feedforward neural networks and their building blocks (7.3), gradient-based optimization — loss functions, gradient-descent variants, and backpropagation (7.4) — and specialized architectures for spatial (CNN) and sequential (RNN) inputs (7.5).
- prerequisites: not in my range (preface pp. 26–29 and Section 1.6 "Book Contents and Structure," pp. 44–45, are outside this reader's chunk range). Within range, the chapter states it "explains all foundational concepts required to understand the following chapters" (p. 190) and that Chapters 8 and 9 build on it (p. 210).

### 7.1 Function Approximation for Reinforcement Learning
- pages: 190–191
- chunks: B01-C0043
- summary: Motivates function approximation as a remedy for two limitations of tabular value functions: the table grows with the number of state-action pairs (infeasible for tasks like Go, ~10^170 states), and tabular updates are isolated per visited state, so an agent must directly encounter a state to learn its value. A maze example (Figure 7.1) illustrates that function approximation lets an agent generalize value estimates to unvisited but "similar" states.
- defines: function approximation motivation via generalization (p. 191); tabular value function limitations (p. 190)
- algorithms: none
- results: none (Figure 7.1 is an illustrative example, not a formal or empirical result)
- figures: Figure 7.1 maze environment illustrating generalization (p. 191)
- keywords: function approximation, generalization, tabular value functions, state space size
- hmasd: none

### 7.2 Linear Function Approximation
- pages: 192
- chunks: B01-C0043
- summary: Defines function approximation formally as learning f(x;θ) to approximate a target function f*(x) (Eq. 7.1), then introduces linear value-function approximation V̂(s;θ)=θᵀx(s) (Eq. 7.2) over a predetermined state-feature vector x(s). States linear approximation's benefit is simplicity and generalization, but its accuracy is constrained by the quality of hand-selected features, which is difficult for high-dimensional inputs such as images.
- defines: function approximation (Eq. 7.1, p. 192); linear state-value function (Eq. 7.2, p. 192); state feature vector x(s) (p. 192)
- algorithms: none
- results: none
- figures: none
- keywords: linear function approximation, state features, parameterized function
- hmasd: none

### 7.3 Feedforward Neural Networks
- pages: 193–197
- chunks: B01-C0044
- summary: Introduces feedforward neural networks (MLPs) as compositions of sequential layers (Eq. 7.4), each built from neural units computing a weighted sum plus bias followed by a non-linear activation (Eq. 7.5, Section 7.3.1). Summarizes common activation functions — ReLU, leaky ReLU, ELU, tanh, sigmoid (Figures 7.4/7.5, Section 7.3.2) — and states the universal approximation theorem (citing Cybenko 1989; Hornik, Stinchcombe, and White 1989; Hornik 1991; Leshno et al. 1993): a feedforward network with as few as one hidden layer can approximate any continuous function on a closed, bounded domain given sufficient hidden units, though deeper networks can generalize better at an equivalent parameter count (citing Goodfellow, Bengio, and Courville 2016). Section 7.3.3 gives the vectorized per-layer computation (Eq. 7.6).
- defines: feedforward neural network / MLP (Eq. 7.4, p. 194); neural unit (Eq. 7.5, p. 196); activation functions ReLU, leaky ReLU, ELU, tanh, sigmoid (Figure 7.4, p. 196); layer computation (Eq. 7.6, p. 197); depth and width (p. 195)
- algorithms: none
- results: universal approximation theorem, stated without proof, citing Cybenko 1989; Hornik, Stinchcombe, and White 1989; Hornik 1991; Leshno et al. 1993 (p. 195)
- figures: Figure 7.2 three-layer feedforward network (p. 194); Figure 7.3 single neural unit (p. 195); Figure 7.4 activation function table (p. 196); Figure 7.5 activation function plots (p. 197)
- keywords: feedforward neural network, MLP, neural unit, activation function, ReLU, universal approximation theorem
- hmasd: none

### 7.4 Gradient-Based Optimization
- pages: 198–203
- chunks: B01-C0045
- summary: Presents the neural-network training loop (Figure 7.6: sample batch, forward pass, compute loss, backpropagate, gradient-descent update) and its three components — loss function, gradient-based optimizer, backpropagation. Defines loss minimization (Eq. 7.7), an MSE loss for supervised value regression (Eq. 7.8), and a TD bootstrapped loss (Eq. 7.9). Defines the gradient (Eq. 7.10) and vanilla/stochastic/mini-batch gradient descent (Eqs. 7.11–7.13), with a worked comparison (Figure 7.7a) of their stability and per-update compute cost on a toy polynomial-fitting task, plus a second worked comparison (Figure 7.7b) showing momentum accelerates convergence but can overshoot, with Nesterov momentum more stable; states the Adam optimizer "has emerged as a common choice" among adaptive-learning-rate methods (p. 203). Introduces backpropagation (Section 7.4.3, heading at p. 203) as the chain-rule-based technique for computing all-parameter gradients — its worked chain-rule explanation (Eq. 7.14) is extracted on p. 204 (see report: outline/chunk-boundary anomaly).
- defines: loss function / optimization objective (Eq. 7.7, p. 199); MSE regression loss (Eq. 7.8, p. 199); TD bootstrapped loss for value functions (Eq. 7.9, p. 200); gradient (Eq. 7.10, p. 200); vanilla/batch gradient descent (Eq. 7.11, p. 200); stochastic gradient descent (Eq. 7.12, p. 201); mini-batch gradient descent (Eq. 7.13, p. 201); momentum (p. 203); backpropagation (named, p. 203; chain-rule mechanics on p. 204)
- algorithms: vanilla, stochastic, and mini-batch gradient descent (Eqs. 7.11–7.13, p. 200–201); gradient descent with momentum / Nesterov momentum (p. 203)
- results: worked example comparing vanilla/SGD/mini-batch gradient descent on a polynomial-fitting task, reporting per-update compute time (1.07ms vanilla vs. 0.30ms SGD vs. 0.32ms mini-batch B=32) (Figure 7.7a, p. 201–202); worked example on momentum vs. no momentum (Figure 7.7b, p. 203)
- figures: Figure 7.6 training loop (p. 198); Figure 7.7 gradient-descent batch and momentum comparisons (p. 202)
- keywords: loss function, gradient descent, stochastic gradient descent, mini-batch, momentum, Adam, backpropagation
- hmasd: none

### 7.5 Convolutional and Recurrent Neural Networks
- pages: 204–208
- chunks: B01-C0046
- summary: Gives the chain rule (Eq. 7.14) underlying backpropagation, then explains why feedforward networks are ill-suited to images (huge parameter counts — e.g., >6M parameters for a 128×128 RGB image with 128 first-layer units — and no encoding of spatial relationships) and introduces convolutional neural networks (CNNs), which slide shared-parameter filters over the input (Eq. 7.15, Figure 7.8) to cut parameter counts (a 16-filter 5×5 CNN uses 1,216 parameters for the same image) and exploit local spatial structure, plus pooling for dimensionality reduction and robustness to small local translations. Section 7.5.2 introduces recurrent neural networks (RNNs), which process sequences by maintaining a hidden state h_t = f(x_t, h_{t-1};θ) (Eq. 7.16, Figure 7.9); notes RNNs suffer vanishing/exploding gradients over long sequences and that LSTMs and GRUs are the most common architectures used to mitigate this (named on p. 209, in chunk B01-C0047).
- defines: chain rule for backpropagation (Eq. 7.14, p. 204); convolution operation / filter / kernel / receptive field / stride / padding (Eq. 7.15, p. 206); pooling / max-pooling (p. 207); recurrent neural network hidden state (Eq. 7.16, p. 208)
- algorithms: convolutional neural network (Section 7.5.1, p. 205–207); recurrent neural network (Section 7.5.2, p. 207–208)
- results: worked parameter-count comparison: feedforward network on a 128×128×3 image ≈ 6.29M first-layer parameters vs. a 16-filter 5×5 CNN ≈ 1,216 parameters (p. 205–207)
- figures: Figure 7.8 CNN kernel/pooling illustration (p. 206); Figure 7.9 RNN hidden-state computation (p. 208)
- keywords: convolutional neural network, CNN, filter, kernel, pooling, recurrent neural network, RNN, hidden state, vanishing gradients, LSTM, GRU
- hmasd: none

### 7.6 Summary
- pages: 209–211
- chunks: B01-C0047
- summary: Recaps the chapter: function approximation is necessary because tabular methods cannot generalize or scale; feedforward networks stack linear-transformation-plus-activation layers; parameters are trained via gradient-based optimization of a differentiable loss using backpropagation; CNNs share kernel parameters across spatial locations and use pooling; RNNs maintain a hidden state to compactly summarize input sequences, with LSTMs and GRUs as the dominant variants (named here, p. 209). States Chapter 8 introduces deep RL algorithms and Chapter 9 extends them to MARL.
- defines: LSTM, GRU (named, p. 209)
- algorithms: none
- results: none
- figures: none
- keywords: deep learning summary, feedforward networks, CNN, RNN, backpropagation, LSTM, GRU
- hmasd: none

### Chapter 8 — Deep Reinforcement Learning
- pages: 212–247
- chunks: B01-C0048 – B01-C0054
- purpose: Bridges Chapter 2 (tabular RL) and Chapter 7 (deep learning) before Chapter 9 extends these ideas to multi-agent settings. Builds deep value-function approximation up piece by piece into DQN (8.1: moving target problem, breaking correlations via replay, target networks, DDQN, and further extensions), covers policy gradient algorithms (8.2: policy gradient theorem, REINFORCE, actor-critic, A2C, PPO, and parallel/concurrent training), and gives practical guidance on handling partial observability via RNN-conditioned histories (8.3).
- prerequisites: stated in range — "It naturally builds on the content of Chapters 2 and 7" (p. 212).

### 8.1 Deep Value Function Approximation
- pages: 212–222
- chunks: B01-C0048, B01-C0049
- summary: Section-level introduction stating the chapter builds on Chapters 2 and 7, formalizes the environment as a fully observable MDP (partial observability deferred to 8.3), and builds up deep Q-learning piece by piece into the DQN algorithm, addressing the moving target problem and correlated samples along the way.
- defines: none beyond subsections
- algorithms: Deep Q-learning (Algorithm 10, p. 215); Deep Q-learning with target networks (Algorithm 11, p. 218); DQN (Algorithm 12, p. 220)
- results: none at this level (see subsections)
- figures: Figure 8.1 action-value network architecture (p. 214)
- keywords: deep value function approximation, DQN, fully observable MDP
- hmasd: none

### 8.1.1 Deep Q-Learning—What Can Go Wrong?
- pages: 213–215
- chunks: B01-C0048
- summary: Extends tabular Q-learning (Eq. 8.1) to a neural network Q(s,a;θ) that outputs one value per discrete action per forward pass (Figure 8.1). Defines the squared-error loss (Eq. 8.2) against a bootstrapped target (Eq. 8.3, zero for terminal next states) and gives pseudocode (Algorithm 10). States the resulting "deep Q-learning" suffers from two issues: the moving target problem (exacerbated by function approximation) and correlation of consecutive training samples, and notes gradients must be stopped from flowing through the bootstrapped target term.
- defines: deep Q-learning loss (Eq. 8.2, p. 214); target value y_t with terminal-state handling (Eq. 8.3, p. 214)
- algorithms: Algorithm 10 Deep Q-learning (p. 215)
- results: none (stated failure modes, not formal/empirical results)
- figures: Figure 8.1 action-value network architecture (p. 214)
- keywords: deep Q-learning, action-value network, target value, gradient stopping
- hmasd: none

### 8.1.2 Moving Target Problem
- pages: 216
- chunks: B01-C0048
- summary: Explains that the moving target problem (non-stationarity, previously introduced in Section 5.4.1) worsens under function approximation because updating one state's value estimate can change estimates for all other states via generalization. Names the "deadly triad" (off-policy learning + function approximation + bootstrapped targets; citing Sutton and Barto 2018; van Hasselt et al. 2018) as the source of potential divergence, walks through why all three components together are necessary for the described divergence mechanism, and introduces the target network fix (Eq. 8.4, periodically copied parameters θ⁻), continued as Algorithm 11.
- defines: moving target problem (p. 216); deadly triad (p. 216–217); target network (Eq. 8.4, p. 217)
- algorithms: Algorithm 11 Deep Q-learning with target networks (p. 218, spans into B01-C0049)
- results: none (explanatory mechanism, not an empirical/formal result)
- figures: none
- keywords: moving target problem, deadly triad, non-stationarity, target network
- hmasd: none

### 8.1.3 Breaking Correlations
- pages: 217–219
- chunks: B01-C0048, B01-C0049
- summary: Argues RL data violates the i.i.d. assumption of standard ML training in two ways (temporal correlation of transitions; a policy-dependent, shifting sampling distribution), illustrated by a spaceship-landing example (Figure 8.2) of catastrophic forgetting under highly correlated experience. Introduces the replay buffer D (fixed-capacity FIFO), sampled as mini-batches B~U(D), which breaks correlations and improves gradient stability/sample reuse; states a replay buffer can only be used for off-policy algorithms.
- defines: i.i.d. assumption and its violation in RL (p. 218–219); catastrophic forgetting (p. 219); replay buffer (p. 219)
- algorithms: none named yet in this subsection (feeds into DQN, Algorithm 12, p. 220)
- results: none (conceptual argument and illustrative example, Figure 8.2)
- figures: Figure 8.2 spaceship correlated-experience illustration (p. 219)
- keywords: i.i.d. assumption, correlated samples, catastrophic forgetting, replay buffer
- hmasd: none

### 8.1.4 Putting It All Together: Deep Q-Networks
- pages: 220–221
- chunks: B01-C0049
- summary: Assembles target networks and a replay buffer into the DQN algorithm (Mnih et al. 2015; Algorithm 12, loss Eq. 8.5 with targets from Eq. 8.4). Reports an ablation in a simplified single-agent 8×8 level-based-foraging item-collection task (Figure 8.3): plain deep Q-learning is slow and unstable; adding a target network alone gives no notable improvement; adding a replay buffer alone is noisy across runs; only the combined DQN achieves stable, near-optimal convergence.
- defines: DQN loss (Eq. 8.5, p. 220)
- algorithms: Algorithm 12 Deep Q-networks (DQN) (p. 220)
- results: ablation experiment comparing deep Q-learning, +target network, +replay buffer, and full DQN in single-agent level-based foraging, 100,000 steps, 5 seeds, γ=0.99, α=3e-4, batch size 512, buffer capacity 10,000, target update every 100 steps (Figure 8.3, p. 221–222)
- figures: Figure 8.3 environment and learning curves (p. 221)
- keywords: DQN, ablation, level-based foraging, learning curves, replay buffer, target network
- hmasd: none

### 8.1.5 Beyond Deep Q-Networks
- pages: 222
- chunks: B01-C0049 (continues into B01-C0050, p. 223)
- summary: States DQN still overestimates action values because the target uses a max over the main network's own noisy estimates; presents double DQN (DDQN, van Hasselt, Guez, and Silver 2016), which decouples greedy action selection (main network) from value evaluation (target network) (Eq. 8.6), as a simple, commonly reused fix. Briefly lists further DQN extensions cited from the literature — prioritized replay (Schaul et al. 2016), noisy networks (Fortunato et al. 2018), dueling networks (Wang et al. 2016), distributional RL (Bellemare, Dabney, and Munos 2017) — combined into Rainbow (Hessel et al. 2018), reported by that cited paper to outperform DQN across Atari games.
- defines: overestimation bias (p. 223); DDQN target (Eq. 8.6, p. 223)
- algorithms: DDQN (p. 223); Rainbow (combination, cited, p. 223)
- results: Rainbow "shown to exhibit significantly higher performance than DQN across Atari games" — a result attributed to Hessel et al. 2018, not reproduced in this book (p. 223)
- figures: none
- keywords: overestimation, DDQN, prioritized replay, noisy networks, dueling networks, distributional RL, Rainbow
- hmasd: none

### 8.2 Policy Gradient Algorithms
- pages: 223–243
- chunks: B01-C0050, B01-C0051, B01-C0052, B01-C0053
- summary: Section-level introduction to directly parameterizing a policy π(·;ϕ) rather than deriving actions from a value function, motivating the family of "policy gradient algorithms" that follow gradients of the policy parameters computed via the policy gradient theorem.
- defines: policy gradient algorithm (p. 224)
- algorithms: REINFORCE (Algorithm 13); A2C (Algorithm 14); PPO (Algorithm 15); A2C with synchronous environments (Algorithm 16)
- results: none at this level (see subsections)
- figures: none at this level
- keywords: policy gradient, actor-critic
- hmasd: none

### 8.2.1 Advantages of Learning a Policy
- pages: 224–225
- chunks: B01-C0050
- summary: Gives two stated advantages of learning a policy directly: (1) a parameterized probabilistic policy can represent arbitrary action distributions, unlike an ε-greedy policy derived from a value function, which the authors illustrate cannot represent the uniform-mixed Nash/minimax equilibrium of Rock-Paper-Scissors except at ε=1 (Figure 8.4); (2) parameterized policies extend to continuous action spaces, which the value-based architecture of Section 8.1 (one output per discrete action) cannot represent. Defines the softmax policy over action preferences l(s,a;ϕ) (Eq. 8.7). States the book restricts its policy-gradient treatment to discrete action spaces.
- defines: softmax policy (Eq. 8.7, p. 226); Boltzmann/UCB alternative exploration policies for value-based RL (footnote, p. 224–225)
- algorithms: none
- results: worked example: ε-greedy cannot represent the Rock-Paper-Scissors Nash/minimax uniform-mixed equilibrium for ε<1 (p. 225–226)
- figures: Figure 8.4 ε-greedy vs. probabilistic policy flexibility (p. 225)
- keywords: policy representation, softmax policy, continuous actions, Rock-Paper-Scissors equilibrium
- hmasd: none

### 8.2.2 Policy Gradient Theorem
- pages: 226–228
- chunks: B01-C0050
- summary: States the policy gradient theorem (citing Sutton and Barto 2018) giving ∇_ϕJ(ϕ) ∝ Σ_s Pr(s|π) Σ_a Q^π(s,a) ∇_ϕπ(a|s;ϕ) (Eq. 8.8), defines the on-policy state distribution Pr(s|π) via the discounted state-occupancy quantity ρ(s|π), and rewrites the theorem as an expectation over states and actions sampled from the current policy, culminating in ∇_ϕJ(ϕ) = E_π[Q^π(s,a)∇_ϕ log π(a|s;ϕ)] (Eq. 8.13). States this restricts optimization to on-policy data generated by the current policy π itself, so a replay buffer (Section 8.1.3) cannot be used to train a policy-gradient algorithm under this theorem, and that DQN-style algorithms do not satisfy this on-policy requirement since they target the optimal value function via the Bellman optimality equation instead.
- defines: policy gradient theorem statement (Eq. 8.8, p. 226); on-policy state distribution Pr(s|π) and occupancy ρ(s|π) (p. 227); log-derivative form of the policy gradient (Eq. 8.13, p. 227)
- algorithms: none
- results: policy gradient theorem, stated without proof, citing Sutton and Barto 2018 (p. 226–227); chunk carries equation_text_unreliable — the summation/product big-operator glyphs (Σ, Π) in Eq. 8.8 and the ρ(s|π) derivation extract as ordinary letters, so the equation forms should be re-verified against the source page rather than trusted from extracted text
- figures: none
- keywords: policy gradient theorem, on-policy state distribution, log-derivative trick
- hmasd: none

### 8.2.3 REINFORCE: Monte Carlo Policy Gradient
- pages: 229–230
- chunks: B01-C0051
- summary: Instantiates the policy gradient theorem with Monte Carlo return estimates to derive the REINFORCE loss (Williams 1992) over an episodic history (Eqs. 8.15–8.16, Algorithm 13). States Monte Carlo returns give high-variance gradients and unstable training because returns depend on the full episode. Derives (Eqs. 8.17–8.27) that subtracting any state-only baseline b(s) leaves the expected gradient unchanged, since the baseline term integrates to zero over the action distribution, and gives a state-value function V(s;θ) trained by MSE against episodic returns (Eq. 8.28) as a common baseline, yielding the baselined REINFORCE loss (Eq. 8.29).
- defines: REINFORCE loss (Eqs. 8.15–8.16, p. 229); baseline (Eq. 8.17, p. 230); state-value baseline loss (Eq. 8.28, p. 231); baselined REINFORCE loss (Eq. 8.29, p. 231)
- algorithms: Algorithm 13 REINFORCE (p. 230)
- results: proof sketch that baseline subtraction preserves the expected policy gradient in expectation (Eqs. 8.17–8.27, p. 230–231)
- figures: none
- keywords: REINFORCE, Monte Carlo policy gradient, baseline, variance reduction
- hmasd: none

### 8.2.4 Actor-Critic Algorithms
- pages: 231–232
- chunks: B01-C0051
- summary: Introduces actor-critic algorithms, which jointly train a policy (actor) and value function (critic), using the critic to bootstrap return estimates (Eqs. 8.30–8.32) instead of full Monte Carlo returns. States two benefits versus REINFORCE — per-step updates instead of waiting for episode end, and lower-variance estimates — at the cost of bias from an imperfect critic. Introduces N-step returns (Eq. 8.33) as a tunable interpolation between one-step bootstrapping (low variance, high bias) and full Monte Carlo returns (N=T; unbiased, high variance), with an empirical measurement of this trade-off (Figure 8.5) using a critic trained by A2C (N=5) in the single-agent level-based-foraging task.
- defines: bootstrapped return estimate (Eqs. 8.30–8.32, p. 231–232); N-step return estimate (Eq. 8.33, p. 232)
- algorithms: none named yet (actor-critic family generically)
- results: empirical measurement of variance (increasing with N) and bias (decreasing with N) of N-step return estimates, N∈{1,...,10} plus Monte Carlo, from a critic trained with A2C N=5 for 100,000 steps, evaluated on 10,000 episodes (Figure 8.5, p. 233)
- figures: Figure 8.5 bias/variance of N-step returns (p. 233)
- keywords: actor-critic, bootstrapping, N-step returns, bias-variance tradeoff
- hmasd: none

### 8.2.5 A2C: Advantage Actor-Critic
- pages: 233–235
- chunks: B01-C0051, B01-C0052
- summary: Defines the advantage Adv^π(s,a) = Q^π(s,a) − V^π(s) (Eq. 8.34) and its bootstrapped one-step estimate (Eqs. 8.35–8.36), gives the A2C actor loss weighted by the advantage (Eq. 8.38) and critic MSE loss against a bootstrapped target (Eqs. 8.39–8.40), and provides pseudocode (Algorithm 14), explicitly labeled "Simplified A2C" because the original A2C/A3C (Mnih et al. 2016) also uses multi-step returns, parallelization, and entropy regularization. Defines entropy regularization (Eq. 8.41) as an added actor-loss term that discourages premature convergence to a near-deterministic policy.
- defines: advantage function (Eq. 8.34, p. 234–235); advantage bootstrapped estimate (Eq. 8.36, p. 235); A2C actor loss (Eq. 8.38, p. 235); A2C critic loss (Eq. 8.40, p. 235); entropy regularization (Eq. 8.41, p. 236)
- algorithms: Algorithm 14 Simplified advantage actor-critic (A2C) (p. 235); original A2C/A3C referenced (Mnih et al. 2016, p. 234)
- results: none (definitional section)
- figures: none
- keywords: A2C, advantage function, entropy regularization
- hmasd: none

### 8.2.6 PPO: Proximal Policy Optimization
- pages: 236–237
- chunks: B01-C0052
- summary: Introduces trust regions to bound how much a single gradient step may change the policy, contrasting TRPO (Schulman et al. 2015) — which enforces this via a constrained optimization problem or penalty term the book calls "computationally expensive" — with PPO (Schulman et al. 2017, clipped variant), which computes an importance-sampling ratio ρ(s,a)=π(a|s;ϕ)/π_β(a|s) (Eq. 8.42) between the policy being trained and the behavior policy that generated the data, and clips it in the actor loss (Eq. 8.43, Algorithm 15) to permit multiple gradient epochs (N_e) over the same batch — something standard on-policy policy-gradient methods cannot do. States the book covers only the clipped-surrogate PPO variant, not the alternative KL-penalty PPO variant also proposed by Schulman et al. (2017).
- defines: trust region (p. 236); importance sampling weight ρ(s,a) (Eq. 8.42, p. 237); PPO clipped surrogate actor loss (Eq. 8.43, p. 238)
- algorithms: Algorithm 15 Simplified proximal policy optimization (PPO) (p. 237); TRPO referenced (Schulman et al. 2015, p. 236)
- results: none (definitional/comparative section)
- figures: none
- keywords: PPO, TRPO, trust region, importance sampling, clipped objective
- hmasd: none

### 8.2.7 Policy Gradient Algorithms in Practice
- pages: 238
- chunks: B01-C0052
- summary: Reports an empirical comparison of REINFORCE, A2C, and PPO in the single-agent level-based-foraging task (Figure 8.6): REINFORCE solves the task in most runs but with high variance throughout training (attributed to high-variance Monte Carlo returns, per Figure 8.5); A2C and PPO with N-step returns reach optimal performance across all runs within 60,000 steps; PPO learns slightly faster than A2C, attributed to reusing each batch across multiple update epochs.
- defines: none
- algorithms: none new
- results: empirical comparison of REINFORCE, A2C, PPO learning curves, 100,000 steps, 5 seeds, small (2×32-unit) networks, γ=0.99; REINFORCE α=1e-3 no baseline, A2C/PPO α=3e-4 N=5, PPO ε=0.2, N_e=4 epochs (Figure 8.6, p. 239)
- figures: Figure 8.6 REINFORCE/A2C/PPO learning curves (p. 239)
- keywords: REINFORCE, A2C, PPO, comparison, level-based foraging
- hmasd: none

### 8.2.8 Concurrent Training of Policies
- pages: 239–243
- chunks: B01-C0052, B01-C0053
- summary: Since on-policy policy gradient algorithms cannot use a replay buffer, this section introduces two parallelization schemes to obtain larger, less-correlated batches: synchronous data collection (Figure 8.7, Algorithm 16), which runs K environment instances in lockstep threads with the agent waiting each step for all of them, and asynchronous training (Figure 8.9), which gives each thread its own agent copy and environment, updating a shared central network whenever any thread computes gradients. Reports an experiment (Figure 8.8) varying K∈{1,4,16,64} synchronous environments in a 12×12 two-item level-based-foraging task trained for five minutes: smaller K is comparably sample-efficient per time step but less stable (K=1 fails to converge to optimal), larger K is more wall-clock efficient but with diminishing returns as thread idle time grows. States synchronous collection suits multi-core CPUs while asynchronous training suits distributed/accelerator setups, and both assume parallel environment instances are available (not true for, e.g., a single physical robot).
- defines: synchronous data collection (p. 240–241); asynchronous training (p. 243–244)
- algorithms: Algorithm 16 Simplified A2C with synchronous environments (p. 241)
- results: sample-efficiency vs. wall-clock-efficiency experiment for K∈{1,4,16,64} synchronous A2C environments in a 12×12 two-item level-based-foraging task, five-minute training budget, γ=0.99, α=1e-3, N=10 (Figure 8.8, p. 242)
- figures: Figure 8.7 synchronous data collection diagram (p. 240); Figure 8.8 K-ablation learning curves (p. 242); Figure 8.9 asynchronous training diagram (p. 243)
- keywords: synchronous data collection, asynchronous training, parallelization, wall-clock efficiency
- hmasd: none

### 8.3 Observations, States, and Histories in Practice
- pages: 244
- chunks: B01-C0053 (continues into B01-C0054, p. 245)
- summary: Addresses that the chapter's algorithms were formalized for full state observability, but real tasks are often partially observable, requiring conditioning on the episodic history h_t=(o_0,...,o_t). States naive concatenation grows the input dimensionality without bound and that zero-padding to a maximum length is high-dimensional, sparse, and inapplicable to potentially-infinite episodes. Recommends processing the history with a recurrent neural network (Section 7.5.2) instead, one observation at a time, citing GRUs and LSTMs as the RNN variants commonly used in deep RL (Hausknecht and Stone 2015; Rashid et al. 2018; Jaderberg et al. 2019; Morad et al. 2023).
- defines: episodic history h_t (p. 244); why naive history concatenation/zero-padding fails (p. 245)
- algorithms: RNN-conditioned value/policy networks for partial observability (p. 245)
- results: none
- figures: none
- keywords: partial observability, history conditioning, recurrent neural network, GRU, LSTM
- hmasd: communication — the book's only fix for partial observability in this range is a single-agent RNN summarizing an agent's own observation history; a claim about a component needing agent history should cite this page, not Chapter 9's multi-agent extensions (outside this reader's range)

### 8.4 Summary
- pages: 245–247
- chunks: B01-C0054
- summary: Recaps Chapter 8: function approximation lets one update change many states' value estimates (a double-edged sword); the moving target problem is addressed by target networks; correlated samples are addressed by a replay buffer; DQN combines both into a foundational off-policy deep value-based algorithm; the policy gradient theorem underlies REINFORCE (Monte Carlo, high variance, can use a baseline), actor-critic methods (bootstrapped, biased but lower-variance), A2C (adds the advantage function), and PPO (adds a clipped importance-sampling surrogate over TRPO's trust region for more stable, sample-efficient, multi-epoch updates); concurrent training (synchronous or asynchronous) parallelizes data collection/optimization for on-policy algorithms that cannot use a replay buffer. States Chapter 9 extends these algorithms to multi-agent RL.
- defines: none (recap only)
- algorithms: none new (recaps DQN, REINFORCE, A2C, PPO)
- results: none
- figures: none
- keywords: deep RL summary, DQN, REINFORCE, actor-critic, A2C, PPO
- hmasd: none

### Chapter 9 — Multi-Agent Deep Reinforcement Learning
- pages: 248–333
- chunks: B01-C0055–B01-C0072
- purpose: extends the deep-learning tools of Chapter 7 and the single-agent deep-RL algorithms of Chapter 8 to MARL. Opens by classifying MARL training/execution paradigms (fully centralized, fully decentralized, CTDE), then covers deep independent learning, multi-agent policy-gradient methods with centralized critics (including counterfactual and equilibrium-selection variants), and value-decomposition methods for common-reward games (VDN, QMIX, QTRAN and successors). Later parts of the chapter (out of this range) cover agent modeling with neural networks, parameter/experience sharing, self-play, and population-based training. R6 adds, citing the chapter's own Section 9.10 summary: the chapter presents deep-learning-based MARL algorithms built on the training/execution paradigms of centralized training and execution, decentralized training and execution, and CTDE. It covers independent learning, multi-agent policy gradient with centralized critics, value decomposition for common-reward credit assignment, neural agent modeling of other agents' policies, parameter/experience sharing for homogeneous-agent environments, and policy self-play / population-based training culminating in AlphaZero and AlphaStar.
- prerequisites: not directly available (preface and Section 1.6 are outside my range). However, the chapter's own opening paragraph (p. 248, chunk B01-C0055) states it builds on Chapter 7 "Deep Learning", Chapter 8 "Deep Reinforcement Learning", and the tabular MARL algorithms of Part I (Chapters 2–6, especially central/independent learning in Section 5.3 and agent modeling in Section 6.3). R6 (pages 295-333) separately notes: not in my range (stated in the preface and Section 1.6, which are outside chunks B01-C0064–B01-C0072)

### 9.1 Training and Execution Modes
- pages: 249–251
- chunks: B01-C0055
- summary: Classifies MARL algorithms along two axes — what information training may use (decentralized vs. centralized) and what information policies may use at execution (decentralized vs. centralized). Defines and contrasts three regimes: centralized training and execution (CTE), decentralized training and execution (DTE), and centralized training with decentralized execution (CTDE). The authors state CTDE is common in deep MARL because it lets a critic use privileged joint information during training while the deployed policy stays local.
- defines: centralized training and execution (CTE) (p. 249); decentralized training and execution (DTE) (p. 250); centralized training with decentralized execution (CTDE) (p. 251)
- algorithms: none
- results: none
- figures: none
- keywords: CTE, DTE, CTDE, training paradigm, execution paradigm, central learning, independent learning, privileged information
- hmasd: curator_connection — the paradigm distinction (what info training may use vs. what info the deployed policy may use) is the same axis HMASD's own centralized-training skill discriminator vs. decentralized low-level policy sits on.

### 9.2 Notation for Multi-Agent Deep Reinforcement Learning
- pages: 251–252
- chunks: B01-C0055, B01-C0056
- summary: Fixes chapter-wide notation: π(·;ϕi), V(·;θi), Q(·;θi) for agent i's policy/value/action-value networks; hi^t for agent i's local observation history, h^t for the joint-observation history, and the state st, with st ≈ h^t under partial observability. Notes that although RNNs let networks be written as conditioned only on the latest observation, the chapter will always write the explicit history dependence.
- defines: local observation history h_i^t (p. 252); joint-observation history h^t (p. 252); state-approximated-by-joint-history convention s^t ≈ h^t (p. 252)
- algorithms: none
- results: none
- figures: none
- keywords: notation, observation history, joint history, partial observability, recurrent conditioning
- hmasd: none

### 9.3 Independent Learning
- pages: 252–258
- chunks: B01-C0056, B01-C0057
- summary: Introduces deep independent learning, in which each agent treats the others as part of a (non-stationary) environment and applies single-agent deep RL locally. Covers independent value-based learning (IDQN) and independent policy-gradient methods (REINFORCE, A2C, PPO), the specific problem replay buffers create under non-stationary co-learners, and mitigations (smaller buffers, importance-sampling reweighting, hysteretic/lenient learning). Closes with an experiment (Section 9.3.3) showing IA2C scaling to a 15×15-grid level-based-foraging task with up to ~5×10^9 states.
- defines: independent learning (p. 252, restated from Section 5.3.2); hysteretic Q-learning (p. 255); leniency (p. 255)
- algorithms: Algorithm 17 Independent deep Q-networks (IDQN) (p. 254); Algorithm 18 Independent REINFORCE (p. 256); Algorithm 19 Independent A2C with synchronous environments (IA2C) (p. 258)
- results: Figure 9.1 IA2C learning curves in 15×15 level-based foraging, 2-agent/2-item and 3-agent/3-item tasks (p. 259, described in Section 9.3.3 text on pp. 257–258)
- figures: Figure 9.1 IA2C learning curves (p. 259)
- keywords: IDQN, independent REINFORCE, IA2C, replay buffer non-stationarity, hysteretic learning, leniency, level-based foraging, scalability
- hmasd: curator_connection — the documented replay-buffer staleness problem (old off-policy transitions become misleading as co-agents' policies change) is directly relevant to any HMASD component that reuses stored rollouts across changing skill/agent counts.

### 9.4 Multi-Agent Policy Gradient Algorithms
- pages: 259–270
- chunks: B01-C0058, B01-C0059, B01-C0060
- summary: Derives a multi-agent policy gradient theorem and shows how CTDE lets the critic (but not the actor) use centralized information to counter non-stationarity. Covers centralized state-value critics, centralized action-value critics, counterfactual/difference-reward-based credit assignment (COMA), and an equilibrium-selection variant (Pareto actor-critic) for no-conflict games.
- defines: multi-agent policy gradient theorem (p. 260–261, Eq. 9.9); centralized critic (p. 261); difference rewards (p. 267, Eq. 9.14); aristocrat utility (p. 267, Eq. 9.15); no-conflict game (p. 268, Eq. 9.17)
- algorithms: Algorithm 20 Centralized A2C with synchronous environments (p. 263)
- results: Figure 9.3 speaker-listener training curves showing centralized-critic A2C beats IA2C (p. 264–265); Figure 9.6 Pareto-AC vs. centralized A2C on Climbing and penalized level-based foraging (p. 271); COMA reported to empirically suffer high baseline variance and inconsistent value estimates (p. 268–269, citing Kuba et al. 2021, Vasilev et al. 2021, Papoudakis et al. 2021) — chunk B01-C0059 carries `equation_text_unreliable`, so the Eq. 9.16 counterfactual-baseline statement should be checked against the source page for exact operator glyphs
- figures: Figure 9.2 centralized critic architecture (p. 262); Figure 9.3 speaker-listener game and curves (p. 264–265); Figure 9.4 centralized action-value critic architecture (p. 266); Figure 9.5 Stag Hunt and Climbing matrix games (p. 269); Figure 9.6 Pareto-AC vs. centralized A2C curves (p. 271)
- keywords: multi-agent policy gradient theorem, centralized critic, centralized action-value critic, COMA, counterfactual baseline, difference rewards, aristocrat utility, Pareto actor-critic, equilibrium selection, no-conflict games
- hmasd: curator_connection — the centralized-critic/decentralized-actor split and the counterfactual-baseline credit-assignment mechanism (COMA) are the closest textbook analogue to HMASD's own credit-assignment intuition; the book's stated caveat that added centralized information can raise policy-gradient variance without improving convergence guarantees (Section 9.4.2, p. 262–263, citing Lyu et al. 2023) is a boundary condition worth checking against HMASD's discriminator-conditioned critics.

### 9.4.1 Multi-Agent Policy Gradient Theorem
- pages: 260–261
- chunks: B01-C0058
- summary: States the single-agent policy gradient theorem (Eq. 9.7–9.8) and extends it to MARL (Eq. 9.9) as an expectation, for agent i, over full-history distributions and all agents' joint policies, of the centralized action-value function times the log-gradient of agent i's own policy. Notes independent REINFORCE/A2C (Section 9.3.2) are special cases using only single-agent, non-centralized value estimates.
- defines: multi-agent policy gradient theorem (p. 260–261, Eq. 9.9)
- algorithms: none
- results: none (theorem stated without proof in this chunk; equation_text_unreliable flagged on this chunk, so operator glyphs in Eq. 9.7–9.9 should be checked against the source page)
- figures: none
- keywords: policy gradient theorem, multi-agent policy gradient, CTDE derivation
- hmasd: none

### 9.4.2 Centralized Critics
- pages: 261–265
- chunks: B01-C0058, B01-C0059
- summary: Defines a critic as "centralized" if conditioned on any information beyond the individual agent's own observation/action history, and shows how a centralized value loss (Eq. 9.10) and centralized A2C (Algorithm 20) are built. Reports Lyu et al. (2023)'s analysis that the critic must at minimum condition on the actor's own observation history to avoid bias, that additional centralized information zt can raise policy-gradient variance without improving convergence guarantees in theory, but that in practice (per Lowe et al. 2017; Papoudakis et al. 2021) such information can still help escape local optima. Demonstrates the effect empirically on the speaker-listener game.
- defines: centralized critic (p. 261, Eq. 9.10)
- algorithms: Algorithm 20 Centralized A2C with synchronous environments (p. 263)
- results: Figure 9.3(b) — centralized-critic A2C converges to higher returns than IA2C on the speaker-listener game (p. 264–265); theoretical bias/variance analysis attributed to Lyu et al. (2023) reported without proof in this chunk (p. 262–263; chunk flagged equation_text_unreliable)
- figures: Figure 9.2 centralized critic architecture (p. 262); Figure 9.3 speaker-listener game and training curves (p. 264–265)
- keywords: centralized critic, information conditioning, bias-variance tradeoff, speaker-listener game, partial observability
- hmasd: curator_connection — the stated minimum-information requirement (critic must see at least what the actor sees) is a concrete design constraint for any HMASD skill-discriminator-conditioned critic.

### 9.4.3 Centralized Action-Value Critics
- pages: 265–266
- chunks: B01-C0059
- summary: Extends centralized critics to action-value form Q(hi, z, a; θi), conditioned on all agents' actions as well as local history and centralized information (Eq. 9.11–9.13). Explains why DQN-style bootstrapped off-policy training with a replay buffer is not used: the multi-agent policy gradient theorem needs the expected return under the *current* joint policy, which off-policy replay data does not represent. Describes the architecture that avoids exponential output size by taking other agents' actions a_{-i} as additional inputs and producing one output per action of agent i.
- defines: centralized action-value critic (p. 265, Eq. 9.11); on-policy requirement for centralized action-value critics (p. 265–266)
- algorithms: none
- results: none (chunk flagged equation_text_unreliable for Eq. 9.11–9.13)
- figures: Figure 9.4 centralized action-value critic architecture (p. 266)
- keywords: centralized action-value critic, on-policy training, joint-action space, Sarsa-style target
- hmasd: none

### 9.4.4 Counterfactual Action-Value Estimation
- pages: 266–269
- chunks: B01-C0059
- summary: Introduces difference rewards and the aristocrat utility as counterfactual credit-assignment devices, then presents COMA (Foerster, Farquhar, et al. 2018), which uses a centralized action-value critic to compute a counterfactual baseline (Eq. 9.16) that marginalizes out agent i's own action while holding other agents' actions fixed; this baseline is stated to leave the policy gradient unchanged in expectation. The authors report that despite this motivation, COMA empirically suffers high baseline variance (Kuba et al. 2021), inconsistent value estimates (Vasilev et al. 2021), and resulting unstable/poor training (Papoudakis et al. 2021).
- defines: difference rewards (p. 267, Eq. 9.14); aristocrat utility (p. 267, Eq. 9.15); counterfactual baseline / COMA (p. 267–268, Eq. 9.16)
- algorithms: COMA (Counterfactual multi-agent policy gradient) (p. 267–268, no numbered algorithm box in this range)
- results: COMA reported empirically unstable/high-variance despite unbiased-in-expectation baseline (p. 268–269); chunk flagged equation_text_unreliable for Eq. 9.14–9.16
- figures: none
- keywords: difference rewards, aristocrat utility, COMA, counterfactual baseline, multi-agent credit assignment
- hmasd: curator_connection — difference rewards / counterfactual baselines are the standard textbook framing of "individual contribution to shared reward," directly comparable to any credit-assignment signal HMASD derives from its skill/agent decomposition; the noted COMA instability is a documented limit worth citing before assuming counterfactual credit signals are automatically well-behaved.

### 9.4.5 Equilibrium Selection with Centralized Action-Value Critics
- pages: 268–270
- chunks: B01-C0059
- summary: Defines no-conflict games (Eq. 9.17, all agents share the same most-preferred joint policy) and uses the Stag Hunt as a worked example of risk-dominant equilibrium selection under policy-gradient learning. Presents Pareto actor-critic (Pareto-AC; Christianos, Papoudakis, and Albrecht 2023), which trains agent i assuming other agents follow a best-response set π+_{-i} that maximizes agent i's return (Eq. 9.18–9.21), steering learning toward the Pareto-optimal rather than risk-dominant equilibrium. Notes the mechanism requires an argmax over other agents' joint actions, which the authors state scales poorly with agent count and remains an unresolved tractability problem for Pareto-AC.
- defines: no-conflict game (p. 268, Eq. 9.17); Pareto actor-critic objective (p. 269–270, Eq. 9.18–9.21)
- algorithms: Pareto actor-critic (Pareto-AC) (p. 269–270, no numbered algorithm box in this range)
- results: none in this sub-section (empirical curves reported under Section 9.5's opening text, Figure 9.6, p. 271)
- figures: Figure 9.5 Stag Hunt and Climbing matrix games (p. 269)
- keywords: no-conflict games, Stag Hunt, equilibrium selection, risk dominance, Pareto actor-critic, Pareto optimality
- hmasd: none

### 9.5 Value Decomposition in Common-Reward Games
- pages: 271–294 (continues past page 294 into R6's range — Section 9.5.5 text is unfinished at the end of this range, see below)
- chunks: B01-C0060, B01-C0061, B01-C0062, B01-C0063
- summary: Motivates factoring a centralized action-value function into per-agent utility functions to avoid the intractability of a full joint-action critic while still enabling decentralized, efficient greedy action selection. Traces the idea to coordination graphs (Guestrin et al.) and formalizes the individual-global-max (IGM) property as the correctness condition for such a decomposition. Presents linear decomposition (VDN) and monotonic decomposition (QMIX) as sufficient-condition instantiations with proofs, evaluates both empirically on matrix games and level-based foraging, and closes (Section 9.5.5) by presenting Son et al.'s necessary-and-sufficient IGM conditions underlying QTRAN plus brief mentions of weighted QMIX and a duplex (value+advantage) decomposition.
- defines: individual-global-max (IGM) property (p. 274, Eq. 9.25); linear value decomposition / VDN (p. 275, Eq. 9.26–9.30); monotonic value decomposition / QMIX (p. 278–279, Eq. 9.46–9.47); QTRAN's necessary-and-sufficient IGM conditions (p. 290–291, Eq. 9.67–9.69)
- algorithms: Algorithm 21 Value decomposition networks (VDN) (p. 278); Algorithm 22 QMIX (p. 283); QTRAN (p. 290–292, no numbered algorithm box in this range)
- results: proof that any linear decomposition satisfies IGM (p. 275–277); proof that QMIX's monotonicity condition is sufficient for IGM, plus a footnote counterexample showing non-strict monotonicity breaks the "⇐" direction (p. 279–282); Climbing-game failure of both VDN (converges to (C,C), +5) and QMIX (converges to (C,B), +6) against the optimal (A,A), +11 (p. 288–289, Figure 9.15); level-based foraging comparison where QMIX > VDN > IDQN in return, speed, and variance across 5 seeds (p. 289–290, Figure 9.16); QTRAN's learned decomposition recovers optimal policies in the linear, monotonic, and Climbing games but only asymptotically satisfies its own IGM conditions during training (p. 292–294). All of these chunks (B01-C0060 through B01-C0063) are flagged `equation_text_unreliable`; big-operator glyphs (Σ, Π, ∀, ∃) in the reproduced equations should be checked against the source pages before being trusted verbatim.
- figures: Figure 9.7 coordination graph (p. 273); Figure 9.8 VDN/QMIX network architectures (p. 279); Figure 9.9 value-decomposition visualization format (p. 284); Figure 9.10 linear matrix game decompositions (p. 285); Figure 9.11 monotonic matrix game decompositions (p. 286); Figure 9.12 QMIX mixing-function visualization (p. 286); Figure 9.13 two-step common-reward stochastic game (p. 287); Figure 9.14 VDN/QMIX on the two-step game (p. 287); Figure 9.15 Climbing game decompositions (p. 288); Figure 9.16 level-based foraging environment and IDQN/VDN/QMIX learning curves (p. 289); Figure 9.17–9.19 QTRAN decompositions on the linear, monotonic, and Climbing games (p. 293–294)
- keywords: value decomposition, IGM, VDN, QMIX, QTRAN, coordination graph, monotonic mixing, hypernetwork, weighted QMIX, duplex decomposition, common-reward games
- hmasd: curator_connection — the IGM property is exactly the "local-greedy-equals-global-greedy" consistency condition that any N-agnostic HMASD skill/action mixer would need to preserve as agent count N varies; see individual sub-section entries below for the precise page-anchored statements.

### 9.5.1 Individual-Global-Max Property
- pages: 273–275
- chunks: B01-C0060
- summary: Formally defines the IGM property (Eq. 9.25): a decomposition of the centralized action-value function into per-agent utilities is IGM-consistent iff, for all full histories, a joint action is greedy for the centralized Q exactly when each component action is greedy for its agent's own utility. States two implications — decentralized greedy execution matches the centralized greedy joint action, and the greedy joint action needed for a training target can be computed cheaply per-agent — and notes IGM-satisfying decompositions may not exist for some environments, particularly under partial observability where individual utilities cannot discriminate joint histories with different true values.
- defines: individual-global-max (IGM) property (p. 274, Eq. 9.25); greedy-action sets A*(h,z;θ) and A*_i(hi;θi) (p. 273–274, Eq. 9.23–9.24)
- algorithms: none
- results: none (definitional section; chunk flagged equation_text_unreliable)
- figures: none
- keywords: IGM property, decentralized greedy action, coordination graph, consistency
- hmasd: curator_connection — see 9.5 top-level entry; this is the precise formal statement (Eq. 9.25) an N-agnostic HMASD mixer would need to satisfy.

### 9.5.2 Linear Value Decomposition
- pages: 275–277
- chunks: B01-C0060, B01-C0061
- summary: Defines VDN's linear decomposition — the sum of per-agent utilities equals the common reward, so the centralized Q is exactly the sum of per-agent utility functions (Eq. 9.26–9.30) — and gives a full two-direction proof that any linear decomposition satisfies IGM. Presents VDN's loss (Eq. 9.43) trained over a shared replay buffer across all agents and gives its pseudocode.
- defines: linear value decomposition / VDN (p. 275, Eq. 9.26–9.30)
- algorithms: Algorithm 21 Value decomposition networks (VDN) (p. 278)
- results: theorem — any linear decomposition satisfies the IGM property, proved in both directions (p. 275–277); chunk flagged equation_text_unreliable, so the proof's operator glyphs should be checked against source pages
- figures: none in this sub-section (Figure 9.8 VDN/QMIX architecture appears at p. 279, in 9.5.3)
- keywords: VDN, linear decomposition, IGM proof, shared replay buffer, common reward
- hmasd: none beyond the general IGM connection noted at the 9.5 level.

### 9.5.3 Monotonic Value Decomposition
- pages: 278–283
- chunks: B01-C0061, B01-C0062
- summary: Introduces QMIX's monotonic decomposition, requiring the derivative of the centralized Q with respect to each agent's utility to be strictly positive (Eq. 9.46), and proves this is sufficient for IGM. A footnote gives the non-strict (≥0) version used in the original QMIX paper (Rashid et al. 2018) and an explicit two-agent counterexample showing the "⇐" direction of IGM fails without strict positivity. Describes the mixing network fmix and hypernetwork fhyper architecture (Eq. 9.47) that enforces positive mixing weights via an absolute-value activation, and gives QMIX's loss (Eq. 9.63) and pseudocode. States that VDN's class of representable decompositions is a strict subset of QMIX's (any linear decomposition is monotonic; Eq. 9.64 gives a monotonic-but-non-linear example with positive per-agent weights αi(h)).
- defines: monotonic value decomposition / QMIX (p. 278–279, Eq. 9.46–9.47); mixing network fmix and hypernetwork fhyper (p. 279–282)
- algorithms: Algorithm 22 QMIX (p. 283)
- results: theorem — QMIX's (strict) monotonicity condition is sufficient for IGM, proved in both directions (p. 279–281); footnote counterexample shows non-strict monotonicity breaks the "⇐" direction (p. 280–281, Eq. 9.59–9.62); VDN's representable class ⊂ QMIX's representable class (p. 282–283, Eq. 9.64); reported that QMIX "has been shown to outperform VDN and many other value-based MARL algorithms" citing Rashid et al. 2018 and Papoudakis et al. 2021, with the authors flagging that several original-QMIX implementation details (parameter sharing, agent-ID one-hot, RNN utilities, last-action input, episodic replay buffer) may materially affect this result and are not specific to QMIX itself (p. 283). Chunk flagged equation_text_unreliable.
- figures: Figure 9.8 VDN/QMIX network architectures (p. 279)
- keywords: QMIX, monotonicity, mixing network, hypernetwork, IGM sufficiency, strict vs. non-strict monotonicity, parameter sharing
- hmasd: curator_connection — Eq. 9.46 (strict positive partial derivative) is the exact algebraic property a monotonic HMASD skill/value mixer must preserve; the strict-vs-non-strict counterexample (footnote 9, p. 280–281) is a concrete pitfall to check if an HMASD mixer only enforces non-negative weights.

### 9.5.4 Value Decomposition in Practice
- pages: 283–290
- chunks: B01-C0062, B01-C0063
- summary: Empirically compares VDN and QMIX on a linearly decomposable matrix game, a monotonic-but-non-linear matrix game, a two-step common-reward stochastic game combining both, the Climbing game (no simple linear/monotonic structure), and a shared-reward level-based foraging environment. Reports that VDN cannot represent the monotonic game's true values (Figure 9.11) though it can still reach the optimal *policy* there; that VDN systematically underestimates the harder branch of the two-step game and thus mis-selects between sub-games (Figure 9.13–9.14); that both VDN and QMIX fail to reach the optimal joint action in the Climbing game (Figure 9.15); and that QMIX outperforms VDN and IDQN on level-based foraging in return, speed, and variance across 5 seeds (Figure 9.16). All experiments use fixed 2- or 3-agent settings; no held-out or varying agent-count evaluation is reported.
- defines: none new (uses the Figure 9.9 tabular format to display learned decompositions, p. 284)
- algorithms: none new (evaluates VDN/Algorithm 21 and QMIX/Algorithm 22)
- results: VDN fails on the monotonic-game value estimates but still reaches the optimal policy greedily (p. 285–286); VDN underestimates the harder two-step sub-game and picks the worse branch (a1=A, reward +9 instead of +10) (p. 287–288); both VDN and QMIX fail to reach the Climbing game's optimum (+11), converging to (C,C)/+5 and (C,B)/+6 respectively (p. 288–289); QMIX > VDN > IDQN on level-based foraging return/speed/variance, 5 seeds, 2M environment steps (p. 289–290). Chunk flagged equation_text_unreliable (affects numeric-table readability only in a few places; the reported payoff/decomposition numbers themselves are plain numerals, not big-operator equations).
- figures: Figure 9.9 visualization format (p. 284); Figure 9.10 linear game decompositions (p. 285); Figure 9.11 monotonic game decompositions (p. 286); Figure 9.12 QMIX mixing-function visualization (p. 286); Figure 9.13 two-step stochastic game (p. 287); Figure 9.14 VDN/QMIX on the two-step game (p. 287); Figure 9.15 Climbing game decompositions (p. 288); Figure 9.16 level-based foraging environment and learning curves (p. 289)
- keywords: VDN limitations, QMIX limitations, Climbing game, two-step stochastic game, level-based foraging, empirical comparison, matrix games
- hmasd: curator_boundary — every experiment in this sub-section fixes the agent count (2 or 3); this is not evidence that a linear or monotonic decomposition (or its IGM guarantee) continues to hold as N varies, which is directly relevant to any variable-N HMASD claim built on VDN/QMIX-style mixing.

### 9.5.5 Beyond Monotonic Value Decomposition
- pages: 290-295 (merged from R5's body, pp. 290-294, and R6's closing paragraph, p. 295 — section straddles the R5/R6 reader split)
- chunks: B01-C0063, B01-C0064
- summary: Presents Son et al. (2019)'s necessary-and-sufficient conditions for IGM (Eq. 9.67–9.69), combining a linear sum of per-agent utilities, an unrestricted centralized Q(h,z,a;θq), and a correction utility V(h,z;θv); shows the conditions are necessary under affine rescaling of individual utilities (Eq. 9.70). Defines QTRAN, which optimizes soft regularization losses (Eq. 9.72, 9.74) toward these conditions rather than enforcing them exactly, so the authors state the IGM property "is only satisfied asymptotically and not throughout the entire training process." Reports QTRAN recovering the optimal policy in the linear, monotonic, and Climbing matrix games (where VDN/QMIX failed), but notes QTRAN's unrestricted centralized Q becomes intractable to train as agent/action count grows. Closes (as this range ends) by introducing weighted QMIX (Rashid et al. 2020, an unconstrained auxiliary mixing network for a weighted value loss) and beginning to introduce Wang et al. (2021)'s duplex decomposition (Eq. 9.78, value+advantage form) — this last item's explanation is incomplete at page 294. R6's continuation (p. 295): The closing paragraph (only part in this range) notes that QPLEX's
  advantage-based IGM decomposition (Eq. 9.79) can be upheld throughout training, and
  that FACMAC extends the value-decomposition idea to multi-agent policy gradient by
  training a decomposed centralized critic (not necessarily monotonic, since the IGM
  property is not required when parameterized policies handle decentralized execution).
- defines: QTRAN's necessary-and-sufficient IGM conditions (p. 290–291, Eq. 9.67–9.69); weighted QMIX (p. 294, named but not equation-defined in this range); duplex decomposition (p. 294, Eq. 9.78, definition incomplete — continues in R6); advantage-based IGM decomposition, Q(hi,ai) = V(hi) + A(hi,ai) (p. 295)
- algorithms: QTRAN (p. 290–292, no numbered algorithm box); QPLEX (p. 295, name only, uses multi-head attention mixing of advantage
  functions — Vaswani et al. 2017); FACMAC (p. 295, decomposed centralized critic +
  individual policy networks, non-monotonic mixing allowed)
- results: theorem — Son et al.'s conditions are necessary and sufficient for IGM under affine rescaling (p. 290–291, stated, proof not reproduced in this chunk); QTRAN recovers optimal policies on the linear, monotonic, and Climbing games where VDN/QMIX did not (p. 292–294, Figures 9.17–9.19); QTRAN's own IGM guarantee holds only asymptotically during training, not throughout (p. 292); QTRAN's centralized Q becomes intractable for large agent/action counts (p. 294). Chunk flagged equation_text_unreliable.
- figures: Figure 9.17 QTRAN on the linear game (p. 293); Figure 9.18 QTRAN on the monotonic game (p. 293); Figure 9.19 QTRAN on the Climbing game (p. 294)
- keywords: QTRAN, necessary and sufficient IGM conditions, soft regularization, weighted QMIX, duplex decomposition, affine transformation; QPLEX, advantage decomposition, IGM, FACMAC, centralized critic decomposition
- hmasd: curator_boundary — QTRAN's own text states its IGM property is not enforced during training, only approached asymptotically through regularization losses; any HMASD claim of "IGM-preserving" decomposition modeled on QTRAN should distinguish the trained-network guarantee from the formal necessary-and-sufficient condition.

### 9.6 Agent Modeling with Neural Networks
- pages: 295–302
- chunks: B01-C0064, B01-C0065
- summary: The authors motivate agent modeling by observing that independent learning,
  multi-agent policy gradient, and value decomposition algorithms only consider other
  agents' actions indirectly, through training data or centralized critics conditioned
  on joint actions. Agent modeling lets an agent explicitly learn models of other
  agents' policies with neural networks so it can generalize to unseen states (unlike
  the tabular empirical-distribution models of Section 6.3). Two approaches are given:
  policy reconstruction via deep joint-action learning (9.6.1), and learning compact
  representations of other agents' policies via encoder-decoder architectures (9.6.2).
- defines: agent model notation π̂i_j parameterized by ϕi_j, a neural network mapping
  agent i's observation history to a predicted action distribution for agent j (p. 296)
- algorithms: Deep joint-action learning, Algorithm 23 (p. 298)
- results: Figure 9.20 learning curve, IDQN vs. JAL-AM exact vs. JAL-AM sampled K=10 in
  level-based foraging (p. 299); Figure 9.22 learning curve, centralized A2C with/without
  representation-based agent modeling (p. 302). extraction_warnings:
  equation_text_unreliable applies to both chunks (Eq. 9.79–9.85 big-operator glyphs).
- figures: Figure 9.20 level-based foraging environment + learning curve (p. 299);
  Figure 9.21 encoder-decoder agent-model architecture (p. 300); Figure 9.22 level-based
  foraging environment + learning curve for representation-based agent modeling (p. 302)
- keywords: agent modeling, joint-action learning, deep agent models, cross-entropy loss,
  encoder-decoder, theory of mind, recursive reasoning, opponent shaping
- hmasd: none

### 9.6.1 Joint-Action Learning with Deep Agent Models
- pages: 296–299
- chunks: B01-C0064
- summary: Extends tabular joint-action learning (Section 6.3.2) to partially observable
  environments with neural-network agent models π̂i_j. Each agent i trains agent models
  of every other agent j by minimizing cross-entropy loss (Eq. 9.80) against j's true
  observed actions, and trains a centralized action-value function Q(hi, ⟨ai,a−i⟩; θi)
  (Eq. 9.81) whose target uses the greedy action of agent i weighted by the product of
  other agents' predicted action probabilities (Eq. 9.82–9.83). Because exact
  computation of the target requires summing over all joint actions of other agents
  (intractable for many agents/large action spaces), the authors give a sampling
  approximation using K sampled joint actions from the agent models (Eq. 9.84). The
  authors compare exact vs. sampled (K=10) JAL-AM against IDQN on a two-agent
  level-based foraging environment: IDQN fails to reliably learn cooperative item
  collection, JAL-AM succeeds, and the sampled variant learns faster and more reliably
  than the exact variant (attributed to prioritizing common-action value estimates and
  added exploratory noise).
- defines: agent model loss L(ϕi_j) (Eq. 9.80, p. 297); centralized action-value loss
  L(θi) (Eq. 9.81, p. 297); target action value AV(hi,ai;θi) exact (Eq. 9.82–9.83, p.
  297) and K-sample approximation (Eq. 9.84, p. 298)
- algorithms: Algorithm 23 Deep joint-action learning (p. 298)
- results: Figure 9.20 learning curve — IDQN vs. JAL-AM (exact) vs. JAL-AM (sampled
  K=10) on level-based foraging, 2M env steps, 5 seeds, results reported as mean ±
  std of evaluation returns (p. 299). equation_text_unreliable noted for this chunk.
- figures: Figure 9.20 (p. 299)
- keywords: JAL-AM, agent models, cross-entropy loss, centralized action-value function,
  sampling approximation, level-based foraging
- hmasd: none

### 9.6.2 Learning Representations of Agent Policies
- pages: 300–302
- chunks: B01-C0065
- summary: Motivates learning compact representations of other agents' policies rather
  than reconstructing them directly, because other agents' policies may be unavailable
  at execution time, too complex (e.g., full neural-net parameters) to condition on, and
  non-stationary. An encoder network f^e maps agent i's observation history to a
  representation m^t_i; a decoder network f^d, trained jointly with the encoder via a
  cross-entropy reconstruction loss over all other agents' true actions (Eq. 9.85),
  reconstructs the other agents' action probabilities from m^t_i. The representation is
  used only to condition the agent's policy/value functions at execution time (decoder
  discarded); the method is stated to be agnostic to the underlying MARL algorithm
  (illustrated by extending centralized A2C). The authors report a level-based foraging
  experiment (Fig. 9.22) in which agent modeling speeds convergence and yields higher,
  lower-variance converged returns than plain centralized A2C. The authors also note
  related encoder-decoder agent-modeling work in the different setting of a single
  learning agent interacting with fixed, non-learning other agents (Rabinowitz et al.
  2018; Papoudakis, Christianos, and Albrecht 2021; Zintgraf et al. 2021), which
  additionally predicts observations/"mental state" of other agents.
- defines: encoder-decoder representation loss L(ψe_i, ψd_i) (Eq. 9.85, p. 301)
- algorithms: none (mechanism, not a numbered algorithm)
- results: Figure 9.22 learning curve, centralized A2C vs. centralized A2C + agent
  modeling on level-based foraging, 16M env steps across 8 synchronous environments, 5
  seeds (p. 302). equation_text_unreliable noted for this chunk.
- figures: Figure 9.21 encoder-decoder architecture (p. 300, appears at top of chunk,
  described on p. 300); Figure 9.22 environment + learning curve (p. 302)
- keywords: representation learning, encoder-decoder, policy representation, gradient
  stopping, mental-state prediction, theory of mind
- hmasd: none

### 9.7 Environments with Homogeneous Agents
- pages: 303–309
- chunks: B01-C0066, B01-C0067
- summary: Motivated by the parameter-space blowup of independent per-agent networks
  (e.g., IDQN) as agent count n grows, the authors formalize two notions of agent
  homogeneity. An environment has **weakly homogeneous agents** (Definition 14, Eq.
  9.86, p. 304) if, for any joint policy and any permutation σ of agent identities, each
  agent's expected return under the permuted assignment equals the original agent's
  return under the corresponding permuted joint policy — i.e., policies can be
  relabeled/swapped across agents without changing the induced returns. An environment
  has **strongly homogeneous agents** (Definition 15, p. 304) if it is weakly
  homogeneous and additionally the optimal joint policy consists of identical individual
  policies for all agents. The authors stress that weak homogeneity does not imply
  agents should behave identically (Figure 9.23a: two agents that must split across two
  landmarks are weakly but not strongly homogeneous — the optimal joint policy requires
  differentiated behavior). Section 9.7.1 covers parameter sharing (exploits strong
  homogeneity) and Section 9.7.2 covers experience sharing (exploits weak homogeneity,
  a strictly weaker assumption).
- defines: weakly homogeneous agents, Definition 14 / Eq. 9.86 (p. 304); strongly
  homogeneous agents, Definition 15 (p. 304)
- algorithms: none at this level (see 9.7.1, 9.7.2)
- results: none at this level (see subsections)
- figures: Figure 9.23 weakly vs. strongly homogeneous multi-agent navigation
  environments (p. 305)
- keywords: homogeneous agents, weak homogeneity, strong homogeneity, agent
  permutation, identical optimal policies, scalability
- hmasd: curator_connection: Definitions 14–15 are the book's formal test for whether an
  N-agnostic/parameter-shared policy is even a valid design choice for a given
  environment — a fixed but relabelable agent set is assumed throughout, not a variable
  agent count.

### 9.7.1 Parameter Sharing
- pages: 305–306
- chunks: B01-C0066
- summary: Parameter sharing sets all agents' network parameters equal,
  θ_shared = θ1 = ... = θn and/or ϕ_shared = ϕ1 = ... = ϕn (Eq. 9.87, p. 305), which the
  authors state directly instantiates the strongly-homogeneous-agents assumption
  (Definition 15) by constraining the joint policy to identical individual policies.
  Stated benefits: parameter count stays constant as agent count n grows (vs. linear
  growth without sharing), and shared parameters are updated from the pooled experience
  of all agents (more diverse/larger training data). Stated caveat: strong homogeneity
  is a strong, hard-to-verify assumption, and weakly-but-not-strongly-homogeneous
  environments (e.g., Fig. 9.23a) will not benefit and may fail to learn the required
  differentiated policies under the sharing constraint. The authors describe augmenting
  the observation with an agent index ī (giving observation ō^t_i) as a theoretical way
  to let shared parameters still express distinct per-agent behaviors, but state that in
  practice this may not suffice because network representational capacity may be
  insufficient to encode several distinct strategies from an index alone, citing
  Christianos et al. (2021) on the limitations of parameter sharing (with and without
  an agent-index observation). The authors report an empirical comparison of four
  independent-A2C variants (full parameter sharing, critic-only sharing, actor-only
  sharing, no sharing) on a 6×6 level-based foraging environment with two level-1 agents
  and one level-2 item: sharing speeds convergence (fewer time steps) but does not
  necessarily raise final converged returns, since all four variants reach similar
  policies in this example.
- defines: parameter sharing, Eq. 9.87 (p. 305); agent-index-augmented observation ō^t_i
  (p. 307)
- algorithms: none named (parameter-shared independent A2C used as the experimental
  vehicle, not a new algorithm)
- results: Figure 9.24 learning curves, four parameter-sharing configurations of
  independent A2C on level-based foraging (p. 306). equation_text_unreliable noted for
  this chunk.
- figures: Figure 9.24 (p. 306)
- keywords: parameter sharing, strongly homogeneous agents, agent index, scalability,
  independent A2C, Christianos et al. 2021
- hmasd: curator_connection: the parameter-count-independent-of-n property is exactly
  the scaling property an N-agnostic policy design wants, but the authors' own caveat —
  that strong homogeneity is a strong, hard-to-verify assumption, and that an agent
  index alone may not give a shared network enough capacity to differentiate behavior —
  is a direct boundary condition on how far a parameter-shared design can be pushed
  toward heterogeneous or variable-role rosters.

### 9.7.2 Experience Sharing
- pages: 307–309
- chunks: B01-C0066, B01-C0067
- summary: Experience sharing trains a separate parameter set per agent but pools the
  generated trajectories, relaxing the strongly-homogeneous-agents assumption to weak
  homogeneity. For off-policy algorithms (e.g., IDQN), this is implemented by replacing
  each agent's individual replay buffer with a single shared buffer D_shared (Algorithm
  24, p. 309); the authors note that merely sharing the buffer without also increasing
  the number of training samples drawn per step will not change learning versus
  individual buffers, since the buffer only becomes useful once more (and more recent)
  samples are actually drawn from it. For on-policy algorithms, shared experience
  actor-critic (SEAC) (Christianos, Schäfer, and Albrecht 2020) corrects for the
  off-policy nature of other agents' trajectories via importance sampling (Eq. 9.88,
  extending independent A2C's loss to Eq. 9.89 with weighting hyperparameter λ: λ=1
  weights others' experience equally to one's own, λ=0 collapses to no sharing). Stated
  trade-off vs. parameter sharing: experience sharing is more computationally expensive
  per environment step (larger batches, per-agent parameter counts that scale with n)
  but does not assume the optimal joint policy is composed of identical individual
  policies, and the authors cite Christianos, Schäfer, and Albrecht (2020) that
  agent-specific networks with experience sharing can reach higher converged returns
  than parameter sharing when the strongly-homogeneous assumption doesn't hold. Stated
  additional benefit: experience sharing gives agents a more uniform learning
  progression (weaker agents catch up faster by learning from stronger agents'
  trajectories), which the authors argue improves opportunities to practice
  coordination-requiring actions.
- defines: shared replay buffer D_shared (p. 307–308); SEAC loss with importance-
  sampling correction, Eq. 9.88–9.89 (p. 309)
- algorithms: Algorithm 24 Deep Q-networks with shared experience replay (p. 309); SEAC
  (Shared Experience Actor-Critic), named but not given a separate numbered box —
  described as independent A2C (Algorithm 19) using Eq. 9.89 (p. 309–310)
- results: none (this subsection is conceptual/algorithmic; no dedicated experiment
  figure). equation_text_unreliable noted for both chunks.
- figures: none
- keywords: experience sharing, shared replay buffer, SEAC, importance sampling,
  off-policy correction, weakly homogeneous agents, sample efficiency
- hmasd: curator_connection: experience sharing is the book's explicit alternative to
  parameter sharing when the roster is only weakly (not strongly) homogeneous —
  relevant as a design point between full parameter tying and fully independent agents
  for any HMASD variant that relaxes the identical-policy assumption while N is still
  fixed within an episode.

### 9.8 Policy Self-Play in Zero-Sum Games
- pages: 310–318
- chunks: B01-C0068, B01-C0069
- summary: Introduces two-agent, fully observable, turn-taking zero-sum board games
  (chess, shogi, backgammon, Go) as characterized by sparse terminal-only reward, large
  action spaces, and long horizons, making full game-tree search infeasible. Reviews
  alpha-beta minimax search and its reliance on specialized, game-specific evaluation
  functions, then introduces Monte Carlo tree search (MCTS) as a sampling-based
  alternative that does not require a hand-built evaluation function. States that
  MCTS + policy self-play + deep learning achieved "super-human" performance in chess,
  shogi, and Go (Silver et al. 2016/2017/2018; Schrittwieser et al. 2020), and walks
  through AlphaZero as the worked example.
- defines: none new at this level (see 9.8.1–9.8.3)
- algorithms: MCTS for MDPs, Algorithm 25 (p. 313); AlphaZero (p. 317–318, see 9.8.3)
- results: none at this level
- figures: Figure 9.25 tree expansion and backpropagation in MCTS (p. 314)
- keywords: zero-sum games, sparse reward, alpha-beta search, Monte Carlo tree search,
  policy self-play, AlphaZero
- hmasd: none

### 9.8.1 Monte Carlo Tree Search
- pages: 312–314
- chunks: B01-C0068
- summary: Gives the general MCTS algorithm for MDPs (Algorithm 25, p. 313): for each
  encountered state, run k simulations that expand a search tree of visited
  state-action counts N and action-value estimates Q, using ExploreAction (e.g.,
  ϵ-greedy or UCB, Eq. 9.90) to select actions during simulation, InitializeNode to
  expand new leaf nodes using an evaluation function f(ŝ_l) (heuristic if domain
  knowledge is available, or uniform random rollout otherwise), and Update to
  backpropagate the leaf evaluation u through visited nodes via the incremental average
  update (Eq. 9.91, valid under the assumption of a terminating MDP with zero reward
  until termination and an undiscounted return objective). After k simulations,
  BestAction(st) selects the actual action to execute (most-tried or highest-value).
  The authors note UCB's finite-sample error bounds are established (Kocsis and
  Szepesvári 2006) and that MCTS grows one persistent tree across the whole episode/run
  rather than rebuilding per state.
- defines: UCB action selection for MCTS, Eq. 9.90 (p. 313); backpropagation update Eq.
  9.91 (p. 314, footnote: assumes undiscounted return)
- algorithms: Algorithm 25 Monte Carlo tree search for MDPs (p. 313)
- results: none (mechanism description, no dedicated experiment)
- figures: Figure 9.25 (p. 314)
- keywords: MCTS, UCB, simulation, rollout, backpropagation, evaluation function
- hmasd: none

### 9.8.2 Self-Play MCTS
- pages: 315–316
- chunks: B01-C0068, B01-C0069
- summary: States the core requirement for policy self-play: the agents must have
  symmetrical roles and egocentric observations, so that a single trained policy can be
  used to act for every agent, from that agent's own perspective. In zero-sum board
  games this holds because agents are direct opponents with (generally) the same action
  set. An observation is called egocentric if its content is expressed relative to the
  acting agent. For chess, the authors give a worked state-transformation example: state
  s = (i, x, y) with i the acting agent's index, x that agent's own piece locations, y
  the opponent's; to reuse agent 1's policy π1 to act for agent 2, the state is
  transformed via ψ(s) = (1, y, x), which geometrically corresponds to a 180° board
  rotation with piece colors swapped (Figure 9.26). Under this transformation, MCTS
  (Algorithm 25) is adapted so that all tree operations are always performed as if it
  were agent 1's turn (Eq. 9.92), with leaf evaluations sign-flipped when acting for the
  non-anchor agent. The authors note self-play can be extended to train the policy
  against a maintained set Π of past policy versions (not just the current policy),
  serving a role analogous to the experience replay buffer in reducing overfitting to
  a single opponent; this generalization is developed further in Section 9.9. A footnote
  states self-play works even when roles are not perfectly symmetric (e.g., chess's
  first-move advantage for white) as long as egocentric observations and a shared action
  set can be defined and there exist generalizable strategy characteristics across
  roles.
- defines: egocentric observation (p. 315); self-play state transformation ψ(s) for
  chess (p. 315–316); self-play simulation process, Eq. 9.92 (p. 316)
- algorithms: none newly numbered (modification of Algorithm 25)
- results: none
- figures: Figure 9.26 state transformation in chess — 180° board rotation with piece
  colors swapped (p. 316)
- keywords: policy self-play, egocentric observation, symmetric roles, state
  transformation, opponent pool
- hmasd: curator_boundary: self-play as described here is defined only for two-agent,
  zero-sum, (near-)symmetric-role, fixed-N settings with a single shared policy acted
  from an egocentric viewpoint; the text does not establish self-play for general-sum
  or variable-agent-count games (that generalization is deferred explicitly to Section
  9.9, Population-Based Training).

### 9.8.3 Self-Play MCTS with Deep Neural Networks: AlphaZero
- pages: 317–318
- chunks: B01-C0069
- summary: AlphaZero is self-play MCTS against the current policy, augmented with a
  deep convolutional network f(s;θ) = (u, p) (Eq. 9.93, p. 317) that jointly predicts
  the expected game outcome u (targeting z ∈ {+1,−1,0}) and an action-selection
  probability vector p (targeting the MCTS visit-count distribution). Trained end to
  end from randomly initialized parameters via SGD on the combined loss
  L(θ) = (z−u)² − πᵀlog p + c‖θ‖² (Eq. 9.94, p. 318) over self-play data
  D = {(s_t, π_t, z_T)}. p is used to bias MCTS's action-selection formula (Eq. 9.95,
  p. 318), a PUCT-style variant of UCB), and after simulations, actions are chosen
  proportional to root visit counts (training/exploration) or greedily (evaluation).
  The authors note that the full implementation includes additional engineering details
  (network architecture, exploration-rate schedule, exploration noise, action masking)
  referred to the original paper.
- defines: AlphaZero network f(s;θ) → (u,p), Eq. 9.93 (p. 317); AlphaZero loss, Eq. 9.94
  (p. 318); PUCT-style action selection, Eq. 9.95 (p. 318)
- algorithms: AlphaZero (Silver et al. 2018) (p. 317–318)
- results: none in this subsection (match results reported in Section 9.9's opening,
  Figure 9.27, p. 319 — see next entry)
- figures: none in this subsection
- keywords: AlphaZero, self-play, convolutional network, policy-value network, PUCT
- hmasd: none

### 9.9 Population-Based Training
- pages: 319–329
- chunks: B01-C0070, B01-C0071
- summary: Opens by reporting AlphaZero's match results (Figure 9.27, p. 319): against
  Stockfish (chess), Elmo (shogi), and AlphaGo Zero (Go, trained for three days),
  AlphaZero (playing white) won 29.0/84.2/68.9 percent, drew 70.6/2.2/0 percent (no
  draws reported for Go), and lost 0.4/13.6/31.1 percent respectively; each instance
  used k=800 MCTS simulations per state and trained for nine hours/44M games (chess),
  twelve hours/24M games (shogi), thirteen days/140M games (Go), using no game-specific
  heuristic evaluation despite evaluating far fewer states per second than the
  specialized opponents. The authors then pose the generalization question: self-play
  (Section 9.8) required symmetric two-agent zero-sum games — can this be extended to
  general-sum games with two or more agents with non-symmetric roles? Population-based
  training answers yes by maintaining a separate policy population Π^k_i per agent i,
  evolved over generations k via three repeated steps: initialize populations,
  evaluate current policies against the other populations (e.g., by expected return or
  Elo), and modify populations (parameter perturbation, copying better performers, or
  training new policies against a distribution over other populations). The section
  then develops policy space response oracles (PSRO) as the general instantiation
  (9.9.1), a convergence analysis of PSRO to Nash equilibrium under idealized
  assumptions (9.9.2), and AlphaStar as a large-scale applied instance (9.9.3).
- defines: policy population Π^k_i and generation index k (p. 320); population-based
  training's three-step loop — initialize/evaluate/modify (p. 320)
- algorithms: Policy space response oracles, PSRO, Algorithm 26 (p. 322, see 9.9.1)
- results: Figure 9.27 AlphaZero match results vs. Stockfish/Elmo/AlphaGo Zero (p. 319)
- figures: Figure 9.27 (p. 319); Figure 9.28 PSRO steps for a two-agent game (p. 323,
  see 9.9.1); Figure 9.29 PSRO trace on Rock-Paper-Scissors (p. 326, see 9.9.2)
- keywords: population-based training, self-play generalization, general-sum games,
  policy population, generations, PSRO
- hmasd: curator_connection: population-based training is the book's answer to
  extending self-play beyond the fixed-two-symmetric-agent case to non-symmetric roles
  — directly relevant to any HMASD design question about training multiple
  differentiated skill/role policies against each other rather than assuming
  interchangeability.

### 9.9.1 Policy Space Response Oracles
- pages: 321–323
- chunks: B01-C0070
- summary: PSRO (Lanctot et al. 2017), built on the double oracle algorithm (McMahan,
  Gordon, and Blum 2003) and empirical game-theoretic analysis (Wellman 2006), is a
  population-based training family for general-sum games with full or partial
  observability and two or more agents (any POSG or other Chapter 3 game model). Each
  generation k, PSRO (Algorithm 26, p. 322) constructs a meta-game M^k — a finite
  normal-form game whose per-agent action set is that agent's current population Π^k_i
  and whose payoffs are the empirically estimated expected returns of the underlying
  game G for each joint-policy combination — then uses a "meta-solver" (e.g., Nash
  equilibrium, or any Chapter 4 solution concept; the original PSRO enforces a lower
  probability bound ϵ on each population member to avoid overfitting) to compute
  distributions δ^k_i over each population, then uses an "oracle" (typically an
  approximate best-response computed via single-agent RL against sampled opponents,
  Eq. 9.96) to generate a new policy π'_i added to each population (Eq. 9.97). The
  authors note the basic method is computationally expensive (meta-game construction
  scales with the joint-policy space size, Nash solving has exponential complexity —
  Section 4.11 — and RL best-response computation can be costly) and cite a line of
  scalability improvements (Balduzzi et al. 2019; McAleer et al. 2020; Muller et al.
  2020; Smith, Anthony, and Wellman 2021).
- defines: meta-game M^k (p. 321); best-response oracle objective, Eq. 9.96 (p. 322);
  population update rule, Eq. 9.97 (p. 323)
- algorithms: Algorithm 26 Policy space response oracles (PSRO) (p. 322)
- results: none (conceptual/algorithmic; empirical trace given in 9.9.2)
- figures: Figure 9.28 PSRO steps for a two-agent game — construct meta-game, solve
  meta-game, add new policies via oracle (p. 323)
- keywords: PSRO, meta-game, double oracle, meta-solver, best-response oracle,
  empirical game-theoretic analysis
- hmasd: none

### 9.9.2 Convergence of PSRO
- pages: 324–325
- chunks: B01-C0070, B01-C0071
- summary: Gives a proof sketch (not a formally numbered theorem) that PSRO with an
  exact Nash meta-solver and exact best-response oracle converges, and that if it
  converges the result is a Nash equilibrium of the underlying game G. Argument: for a
  finite game G (finite agents/actions/states/observations, terminating in finite
  time), fixing other agents' policies via π−i ∼ δ^k_−i reduces G to a finite MDP
  (stochastic game case) or finite POMDP (POSG case), each of which is known (Chapter
  2) to admit a deterministic optimal policy, and any needed stochastic policy can be
  recovered as a probabilistic mixture via δ^k_i; hence there is always a deterministic
  best response, and since G is finite there is a finite enumerable set of deterministic
  best-response policies, so PSRO must eventually add all of them or terminate earlier,
  guaranteeing convergence; and by the definition of Nash equilibrium, a fixed point
  (oracle's selected best response already in the population) is exactly a Nash
  equilibrium. Two worked non-repeated matrix-game traces illustrate this: Rock-Paper-
  Scissors (Figure 9.29, p. 326) converges only after enumerating all three deterministic
  actions in both populations, reaching the unique uniform-randomization Nash
  equilibrium at generation k=5; Prisoner's Dilemma converges in one generation because
  "defect" is already a best response to itself. The authors explicitly flag that the
  convergence argument assumes exact meta-games (Ri = Ui, i.e., infinite-episode payoff
  estimates) and exact best responses, neither of which holds in practice (meta-games
  are estimated from finitely many sampled episodes; best responses are RL-trained and
  may not converge or may hit local optima), though a cited bound (Tuyls et al. 2020)
  exists on sample counts needed for an estimated-meta-game Nash equilibrium to be an
  approximate Nash equilibrium of the exact meta-game.
- defines: none new (uses PSRO objects from 9.9.1)
- algorithms: none new
- results: proof sketch for PSRO convergence to Nash equilibrium under exact
  meta-solver/oracle assumptions (p. 325); worked traces, Figure 9.29 Rock-Paper-
  Scissors (p. 326) and Prisoner's Dilemma (p. 326, in-text, no figure).
  equation_text_unreliable noted for the C0071 chunk.
- figures: Figure 9.29 PSRO trace on non-repeated Rock-Paper-Scissors over 5 generations
  (p. 326)
- keywords: PSRO convergence, Nash equilibrium, finite game, deterministic best
  response, Rock-Paper-Scissors, Prisoner's Dilemma
- hmasd: curator_boundary: the stated convergence guarantee holds only under exact
  meta-games and exact best-response oracles in a finite game; the authors themselves
  state this will "likely not hold in practice," so PSRO's convergence result is not
  evidence that a sampled/approximate implementation converges to Nash equilibrium.

### 9.9.3 Grandmaster Level in StarCraft II: AlphaStar
- pages: 326–329
- chunks: B01-C0071
- summary: StarCraft II is introduced as sharing all the difficulties of Section 9.8's
  games (large action space, long horizon) plus partial observability (players see only
  what their units see) and three asymmetric races (Terran, Protoss, Zerg) with
  different units/strategies. AlphaStar (Vinyals et al. 2019) was, in 2019, the first
  agent to reach Grandmaster level in the full game, ranked above 99.8 percent of
  officially ranked human players. Per-race, AlphaStar trains a policy
  π(a^t_i | h^t_i, z; θ_i) conditioned on observation-action history and a
  human-data-derived strategy statistic z; observations include a minimap-like overview
  and visible unit lists with attributes; actions specify type, unit, target, and
  timing; reward is +1/−1/0 at game end only, undiscounted. Action-timing constraints
  (max 22 non-duplicate actions per 5-second window) were imposed to keep the match
  against humans fair. The action representation yields roughly 10^26 possible actions
  per step, motivating supervised pretraining on human replay data (each match yielding
  a strategy statistic z) before RL fine-tuning based on A2C, with a penalty for
  deviating from the supervised policy. The population-based mechanism used is "League
  training," which follows a PSRO-like structure: a single league Π^k per race holds
  three agent types — main agents, main exploiter agents, league exploiter agents —
  distinguished by their opponent-sampling distribution, when their policy snapshots
  are frozen into the league, and when/whether their parameters are periodically reset
  to the supervised-pretraining initialization. Opponent sampling uses prioritized
  fictitious self-play (PFSP), δ^k_i(πi) ∝ f(Pr[π'_i wins against πi]) (Eq. 9.98, p.
  328), with two weighting functions: f_hard(x) = (1−x)^p (default; focuses on the
  hardest opponents) and f_var(x) = x(1−x) (focuses on similarly-matched opponents).
  Detailed per-type training mixtures and reset/addition rules are given (main agents:
  35% self-play / 50% PFSP over all past league policies / 15% PFSP over past main
  exploiters, frozen into the league every 2×10^9 steps, never reset; main exploiters:
  trained mostly against main agents, added to league on defeating all three main
  agents ≥70% of matches or after 4×10^9 steps, then reset; league exploiters: trained
  against the whole league, added on defeating the whole league ≥70% of matches or
  after 2×10^9 steps, reset with probability 0.25). Final evaluation used a 971,000-
  match anonymized human replay dataset (top-22-percent Match Making Rating players)
  for pretraining and 44 days of League training on 32 third-generation TPUs; the
  authors report that omitting human-data pretraining causes AlphaStar's performance to
  degrade substantially because the search space becomes too hard to explore from
  scratch, and that supervised-only initial policies already ranked above 84 percent of
  human players before any League RL training.
- defines: PFSP opponent-sampling distribution, Eq. 9.98 (p. 328); f_hard, f_var
  weighting functions (p. 328–329)
- algorithms: AlphaStar / League training (p. 327–329), a population-based training
  variant structurally similar to PSRO
- results: AlphaStar reached Grandmaster level, above 99.8 percent of officially ranked
  human players across all three races (p. 330, opening of 9.10's predecessor
  paragraph, pdf page 330 — carried into this entry since it directly reports the
  9.9.3 experiment's outcome); supervised-only (no RL) initial policies ranked above 84
  percent of human players (p. 330); performance "degrades very substantially" without
  human-data pretraining (p. 330, authors' summary of Vinyals et al. 2019, not a
  reproduced number)
- figures: none dedicated to 9.9.3 in this chunk (StarCraft II screenshots, if any, are
  not present in the extracted text)
- keywords: AlphaStar, League training, PFSP, StarCraft II, main agent, exploiter agent,
  human replay pretraining, partial observability
- hmasd: none

### 9.10 Summary
- pages: 330–333
- chunks: B01-C0072
- summary: The authors' own chapter recap, organized as a bulleted list: (1) the
  centralized-training-and-execution / decentralized-training-and-execution / CTDE
  taxonomy, with "centralized information" defined as anything shared across agents
  beyond an agent's own observation (parameters, gradients, observations, actions,
  etc.); (2) independent learning as agents applying single-agent RL independently,
  sometimes competitive with more complex methods despite simplicity, compatible with
  fully decentralized training and execution; (3) multi-agent policy gradient methods
  that learn centralized critics V(h^t_i, z^t; θ_i) or Q(h^t_i, z^t, a^t; θ_i)
  conditioned on centralized information/joint action; (4) value decomposition for
  common-reward multi-agent credit assignment, factorizing joint action-value functions
  into simpler per-agent-group terms — VDN sums individual Q-values,
  Q(s,⟨a1,a2,a3,...⟩) ≈ Q(a1)+Q(a2)+Q(a3)+..., QMIX uses a monotonic linear combination;
  (5) agent modeling — reconstructing other agents' policies directly, or learning
  compact representations of them via neural networks, either way to condition one's
  own policy/value function and adapt to others; (6) parameter and experience sharing,
  motivated by environments where the optimal joint policy is composed of (near-)
  identical individual policies π*_1 = π*_2 = π*_3 = ...; parameter sharing ties
  parameters across agents (faster gradient descent, smaller search space), experience
  sharing pools trajectories for a more diverse training batch while training
  independent parameters; (7) policy self-play (AlphaZero, using MCTS in each state,
  reaching champion-level play in chess/shogi/Go) for two-agent zero-sum games; (8)
  population-based training generalizing self-play to general-sum, two-or-more-agent,
  full-or-partial-observability games via evolved policy populations — PSRO builds
  per-generation meta-games and uses game-theoretic solution concepts (e.g., Nash
  equilibrium) plus a best-response oracle; AlphaStar operates like PSRO (with
  modifications) and reached Grandmaster level in StarCraft II. Closing sentence frames
  the chapter as addressing partial observability, non-stationarity, multi-agent credit
  assignment, and equilibrium selection, and previews that the next chapter moves from
  theory to implementation practice.
- defines: none new (recap of prior definitions)
- algorithms: none new (recap: VDN, QMIX, AlphaZero, PSRO, AlphaStar)
- results: none new
- figures: none
- keywords: chapter summary, CTDE, independent learning, centralized critics, value
  decomposition, agent modeling, parameter sharing, experience sharing, self-play,
  population-based training
- hmasd: curator_connection: the authors' own framing — "environments where the optimal
  joint policy is composed of (near-)identical individual policies" as the condition
  under which parameter sharing helps — is the exact assumption a curator connection to
  HMASD's shared-policy, N-agnostic design should cite and must not extend beyond
  without independent evidence.

### Chapter 10 — Multi-Agent Deep Reinforcement Learning in Practice
- pages: 334-347
- chunks: B01-C0073, B01-C0074, B01-C0075
- purpose: Walks through implementing MARL algorithms in the book's own PyTorch codebase (github.com/marl-book/codebase): the agent-environment interface, building per-agent neural networks (independent and parameter-shared), centralized critics, value decomposition (VDN/QMIX), assorted practical implementation tips, and how to present experimental results fairly given MARL's sensitivity to seeds/hyperparameters and non-scalar solution concepts.
- prerequisites: not in my range (the preface and Section 1.6, which state chapter dependencies, are outside PDF pages 334-369)

### 10.1 The Agent-Environment Interface
- pages: 334-335
- chunks: B01-C0073
- summary: Describes the interface the book's codebase uses to interact with environments: a `reset()` function that initializes the environment and returns initial observations, and a `step()` function that advances one time step given a joint action and returns next observations, rewards, and a termination flag. The authors state MARL has no single unified environment interface across frameworks (unlike single-agent RL's Gym convention), though a Gym-style interface with minor modification supports many multi-agent environments; observation/action spaces are represented as per-agent tuples.
- defines: agent-environment interface via reset()/step() (p. 335); observation space and action space as per-agent tuples (p. 335)
- algorithms: none
- results: none
- figures: none
- keywords: Gym interface, reset, step, observation space, action space, POSG modeling
- hmasd: none

### 10.2 MARL Neural Networks in PyTorch
- pages: 336-339
- chunks: B01-C0073
- summary: Shows how to build per-agent fully connected networks in the book's codebase: `MultiAgentFCNetwork`, which creates one independent MLP per agent (two 64-unit ReLU hidden layers by default) and runs their forward passes in parallel via `torch.jit.fork`/`torch.jit.wait`; and (10.2.1) `MultiAgentFCNetwork_SharedParameters`, a single shared network usable when all agents' input/output sizes match. Section 10.2.2 instantiates these networks concretely for IDQN (Algorithm 17) with a 5-dimensional observation and 3 discrete actions per agent for two agents.
- defines: MultiAgentFCNetwork, an independent per-agent MLP module (p. 337); MultiAgentFCNetwork_SharedParameters, a shared-network variant (p. 338)
- algorithms: IDQN (Algorithm 17, referenced, not restated) (p. 339)
- results: none
- figures: Figure 10.1 the resulting MultiAgentFCNetwork architecture for IDQN with two agents, observation size 5, three actions (p. 339)
- keywords: PyTorch, torch.jit.fork, parameter sharing, IDQN, ReLU, hidden layers, MultiAgentFCNetwork
- hmasd: none

### 10.3 Centralized Value Functions
- pages: 340
- chunks: B01-C0074
- summary: Describes centralizing a value function or policy on "external" information (per Section 9.4.2) instead of only the acting agent's own observation. Concretely, the state-conditioned actor-critic critic is built by concatenating all agents' observations into a single centralized-critic input, while the actor (policy) remains conditioned only on the individual agent's own observation, preserving the CTDE paradigm.
- defines: centralized (state-conditioned) critic via observation concatenation (p. 341)
- algorithms: state-conditioned actor-critic (referenced from Section 9.4.2, not restated) (p. 341)
- results: none
- figures: none
- keywords: CTDE, centralized critic, observation concatenation, actor-critic
- hmasd: none

### 10.4 Value Decomposition
- pages: 341
- chunks: B01-C0074
- summary: Walks through implementing value decomposition for common-reward environments. VDN is implemented by stacking each agent's next-state Q-values, selecting each agent's best next action, and summing the per-agent Q-values of those actions to form the joint-return target; the text notes more complex methods such as QMIX replace this plain summation with a non-linear, monotonicity-constrained mixing function.
- defines: none (implements definitions introduced in Sections 9.5.2-9.5.3)
- algorithms: VDN, implemented via summed per-agent target Q-values (p. 341); QMIX, referenced as a non-linear/monotonic replacement for the sum (p. 341)
- results: none
- figures: none
- keywords: value decomposition, VDN, QMIX, common reward, target network, monotonicity constraint
- hmasd: none

### 10.5 Practical Tips for MARL Algorithms
- pages: 342-344
- chunks: B01-C0074
- summary: Gives three practical implementation tips. (10.5.1) Choosing between stacking a small window of recent observations, using a recurrent network (LSTM/GRU), or using only the current observation, as a practical compromise against the theoretically sound but not neural-network-friendly full-history-conditioned policy; recurrent nets are closest to theoretically sound but suffer vanishing gradients in practice. (10.5.2) Standardizing rewards or returns (zero mean, unit standard deviation) improves neural-network approximation but the authors give a worked example (a one-state, two-action MDP with only negative rewards) showing standardization can flip the effective sign/goal structure of the reward without changing the ranked action preference, so it should be applied with care. (10.5.3) Using a single shared optimizer over all agents' trainable parameters (summing per-agent losses before one backward/step call) instead of one optimizer per agent, for speed.
- defines: reward/return standardization (pp. 343-344); centralized single-optimizer training (p. 344)
- algorithms: none
- results: worked example: standardizing an all-negative-reward one-state, two-action MDP inverts the apparent sign of the second action's reward while leaving the agents' action preference unchanged (p. 344)
- figures: none
- keywords: recurrent network, LSTM, GRU, observation stacking, vanishing gradient, reward standardization, single shared optimizer
- hmasd: curator_connection: the stacking-vs-recurrent-vs-none decision in 10.5.1 is the same effective-history-length choice an untied-k skill duration would force a designer to revisit if the relevant window is not fixed in advance.

### 10.6 Presentation of Experimental Results
- pages: 345-347
- chunks: B01-C0075
- summary: States that comparing algorithms is harder in MARL than single-agent RL for two reasons: sensitivity to hyperparameters/seeds, and solution concepts that are not one-dimensional. (10.6.1) Learning curves require an evaluation procedure run at regular training intervals plus averaging/standard-error across seeds; the authors show (Figure 10.2) that naive learning curves are uninformative in zero-sum games because both agents' apparent improvement can cancel out, and propose fixes (a fixed heuristic/pretrained opponent, or an expanding pool of past-checkpoint opponents as in AlphaStar) plus condensing curves to a single max or average statistic. (10.6.2) The authors recommend a thorough, parallelizable grid-style hyperparameter search across seeds, since a comparison is unfair if one algorithm received a larger search budget; they suggest starting near known-sensible values and prioritizing exploration-related hyperparameters such as the entropy coefficient.
- defines: none
- algorithms: none
- results: Figure 10.2(b) empirical example: independent-A2C learning curves in a two-agent zero-sum game are not informative and cannot demonstrate whether agents are learning (p. 346)
- figures: Figure 10.2 example learning curves, single-agent vs. zero-sum two-agent (independent A2C) (p. 346)
- keywords: learning curves, evaluation returns, standard error, zero-sum games, self-play pool, hyperparameter search, grid search, seeds, entropy coefficient
- hmasd: none

### Chapter 11 — Multi-Agent Environments
- pages: 348-365
- chunks: B01-C0076, B01-C0077, B01-C0078, B01-C0079
- purpose: Surveys benchmark environments built on the game models of Chapter 3 (normal-form games, stochastic games, POSGs): a complete taxonomy of the 78 structurally distinct strictly-ordinal 2x2 matrix games, seven complex individual environments, and three environment collections. The authors state this selection illustrates game models and gives readers a starting point for experimentation; it is explicitly not comprehensive.
- prerequisites: not in my range (states it builds on Chapter 3's game-model hierarchy, which is outside PDF pages 334-369)

### 11.1 Criteria for Choosing Environments
- pages: 348
- chunks: B01-C0076
- summary: Lists criteria for selecting MARL environments. Normal-form games are useful for testing convergence to specific solution concepts because exact solutions (e.g., minimax/correlated-equilibrium linear programs, Sections 4.3.1/4.6.1) are computable and comparable to what an algorithm learns, and small games support manual inspection. Stochastic-game/POSG environments instead test scaling in agent count, partial observability, and sparse rewards, but usually lack a tractable exact solution (though a learned joint policy can be tested for equilibrium per Section 4.4). The authors also note that different environments require different agent skills (e.g., when/whom to cooperate with in LBF, what information to share in some MPE tasks, how to position within a team in SMAC/GRF), so an algorithm may learn some skills but not others.
- defines: none
- algorithms: none
- results: none
- figures: none
- keywords: environment selection criteria, solution concepts, minimax equilibrium, correlated equilibrium, partial observability, sparse rewards, scalability, agent skills
- hmasd: none

### 11.2 Structurally Distinct 2x2 Matrix Games
- pages: 349-351
- chunks: B01-C0076, B01-C0077
- summary: Presents a complete listing of all 78 structurally distinct, strictly ordinal 2x2 normal-form games (two agents, two actions each) based on the taxonomy of Rapoport and Guyer (1966), downloadable via the book's matrix-games codebase. "Structurally distinct" means no game can be produced from another by row/column/agent-relabeling transformations; "strictly ordinal" means each agent ranks the four outcomes 1-4 with no ties. Games are split into no-conflict games (agents share the same most-preferred outcome) and conflict games (agents disagree on it), and include ordinal variants of games discussed earlier in the book, such as Prisoner's Dilemma, Chicken, and Stag Hunt. Each entry's reward pair is underlined where it constitutes a deterministic (pure) Nash equilibrium; some games have none.
- defines: structurally distinct, strictly ordinal 2x2 game (p. 350); no-conflict game (p. 350); conflict game (p. 351)
- algorithms: none
- results: full enumerated listing of 78 games (21 no-conflict, 57 conflict) with pure-Nash-equilibrium outcomes underlined (pp. 350-357, spanning into chunk B01-C0077)
- figures: none
- keywords: 2x2 matrix games, Rapoport and Guyer taxonomy, ordinal games, no-conflict games, conflict games, pure Nash equilibrium, Prisoner's Dilemma, Chicken, Stag Hunt
- hmasd: none

### 11.3 Complex Environments
- pages: 352-360
- chunks: B01-C0077, B01-C0078
- summary: Introduces a hand-picked selection of complex (stochastic-game/POSG) multi-agent environments that have seen significant adoption in MARL research (the authors state many more exist that are not covered), summarized by observability, observation/action type, and reward density in Figure 11.1. Defines "task" as a specific parameter setting of an environment (e.g., grid size, number of agents, number of items).
- defines: task, a specific parameter setting of an environment (p. 353)
- algorithms: none
- results: none
- figures: Figure 11.1 summary table of environment properties for LBF, MPE, SMAC, RWARE, GRF, Hanabi, Overcooked, Melting Pot, OpenSpiel, Petting Zoo (p. 353)
- keywords: complex environments, task, observability, observation/action type, reward density
- hmasd: none

### 11.3.1 Level-Based Foraging
- pages: 353-354
- chunks: B01-C0077
- summary: Level-based foraging (LBF; Albrecht and Ramamoorthy 2013) places n agents in a fully observable grid-world where agents and items each have a numerical skill level; a discrete action space {up, down, left, right, collect, noop} lets agents navigate and collect items. A group of adjacent agents can collect an item if they all select collect and the sum of their levels meets or exceeds the item's level, so higher-level items require cooperation among a subset of agents. Reward is per-agent, given by Equation 11.1, normalized by the item's level relative to all items and the agent's level relative to the contributing group. A task is specified by grid size, number of agents/items, and level assignment (random per episode); "forced cooperation" tasks assign item levels so that every item requires all agents to cooperate. The authors note many LBF tasks mix competitive (individually collectible items) and cooperative (higher-level items) objectives. Agent count is a task-configuration parameter (fixed within an episode/task), not stated as varying mid-episode.
- defines: level-based foraging (LBF) task (p. 353); LBF per-agent reward function, Equation 11.1 (p. 354); forced cooperation (p. 354)
- algorithms: none
- results: Equation 11.1, per-agent normalized collection reward (p. 354) — chunk B01-C0077 carries an `equation_text_unreliable` warning, so the summation glyphs in this equation should not be trusted as extracted; consult the source page.
- figures: Figure 11.2 two LBF tasks in an 8x8 grid with 3 agents and 5 items: (a) random levels, (b) forced cooperation (p. 354)
- keywords: level-based foraging, LBF, grid-world, forced cooperation, mixed objectives, item collection, fully observable
- hmasd: curator_connection: LBF's "number of agents" is a per-task configuration constant (not varied within a run), which is exactly the fixed-N-per-task pattern the project's variable-N work must not mistake for held-out-N generalization evidence.

### 11.3.2 Multi-Agent Particle Environment
- pages: 355-355
- chunks: B01-C0077
- summary: The multi-agent particle environment (MPE; Mordatch and Abbeel 2018, task set from Lowe et al. 2017) contains 2D navigation tasks focused on coordination, spanning competitive, cooperative, and common-reward tasks with both full and partial observability. Agents observe high-level features (velocity, relative positions to landmarks/other agents) and can act via discrete cardinal-direction movement or continuous velocity control. Named tasks include predator-prey (a team of predators chases an escaping prey), coordinated navigation (three agents cover three landmarks while avoiding collisions), and speaker-listener (a listener must reach a landmark it cannot itself perceive, guided by a speaker's binary communication actions). Bettini et al. (2022) extend MPE as the GPU-simulatable vectorized multi-agent simulator (VMAS). Agent count and observability vary by task rather than being fixed environment-wide.
- defines: multi-agent particle environment (MPE) (p. 355); VMAS, vectorized GPU-simulated extension of MPE (p. 356)
- algorithms: none
- results: none
- figures: Figure 11.3 three MPE tasks: (a) predator-prey, (b) coordinated navigation (3 agents, 3 landmarks), (c) speaker-listener (p. 355)
- keywords: multi-agent particle environment, MPE, predator-prey, coordinated navigation, speaker-listener, VMAS, continuous control, communication
- hmasd: curator_connection: the speaker-listener task's binary communication channel is a concrete communication-axis benchmark a communication-augmented HMASD variant could be evaluated against.

### 11.3.3 StarCraft Multi-Agent Challenge
- pages: 356-356
- chunks: B01-C0077
- summary: SMAC (Samvelyan et al. 2019) has a team of agents (one agent per unit) fight, under a dense common (cooperative) reward based on damage dealt and units defeated plus a large win bonus, against a team controlled by a fixed built-in AI. Tasks vary in unit number/type and map; SMAC includes symmetric tasks (both teams the same units) and asymmetric tasks (different compositions). All SMAC tasks are partially observable: agents see health/shield status of themselves and nearby units within a radius. The authors state the common reward makes credit assignment (Section 5.4.3) especially prominent, since actions have long-term consequences that are hard to disentangle under a shared reward, making value decomposition (Section 9.5) particularly suited to SMAC. Each SMAC task fixes unit starting locations, which the authors say can cause agents to overfit to the specific configuration (e.g., learning a fixed acting order); SMACv2 (Ellis et al. 2023) randomizes unit types and starting locations across episodes to force more generalizable policies. SMAClite (Michalski, Christianos, and Albrecht 2023) reimplements SMAC's mechanics without the StarCraft II game for reproducibility and lower compute cost; the authors report agents trained on SMAClite transfer to SMAC with some performance degradation.
- defines: SMAC symmetric vs. asymmetric task (p. 356); SMACv2 (p. 356); SMAClite (p. 356)
- algorithms: none
- results: cited empirical finding: SMAClite-trained agents transfer to SMAC tasks with some performance degradation, i.e., SMAC is accurately but not perfectly modeled by SMAClite (Michalski, Christianos, and Albrecht 2023, cited, not reproduced) (p. 356)
- figures: Figure 11.4 symmetric (3 marines vs. 3 marines) and asymmetric SMAC tasks (p. 357)
- keywords: StarCraft Multi-Agent Challenge, SMAC, SMACv2, SMAClite, common reward, credit assignment, value decomposition, partial observability
- hmasd: curator_connection: SMAC's per-task fixed unit count with cooperative-play-against-fixed-AI is a fixed-N cooperative benchmark; its documented overfitting-to-fixed-start-locations failure mode is a boundary case for any claim that a fixed-roster algorithm generalizes.

### 11.3.4 Multi-Robot Warehouse
- pages: 357-357
- chunks: B01-C0077, B01-C0078
- summary: In RWARE (Christianos, Schäfer, and Albrecht 2020; Papoudakis et al. 2021), agents control robots in a grid-world warehouse that must find, collect, and deliver shelves with requested items; tasks vary in warehouse layout and number of agents (Figure 11.5). Agents observe shelves/agents within a configurable observation range (partial observability) and act via rotate-left/right, move-forward, stay, or pick-up/drop-off. Agents receive individual (not shared) positive rewards only for successfully delivering a requested shelf; each delivery triggers a new random shelf request. The authors state the main challenge is very sparse rewards, since delivery requires long, specific action sequences, which makes parameter/experience sharing (Section 9.7) particularly effective, as demonstrated by Christianos, Schäfer, and Albrecht (2020).
- defines: multi-robot warehouse (RWARE) task (p. 357)
- algorithms: none
- results: cited empirical finding: parameter/experience sharing is particularly well suited to RWARE's sparse-reward setting (Christianos, Schäfer, and Albrecht 2020, cited, not reproduced) (p. 358)
- figures: Figure 11.5 three RWARE tasks by size and agent count: tiny/2 agents, small/2 agents, medium/4 agents (p. 358)
- keywords: multi-robot warehouse, RWARE, sparse rewards, individual reward, observation range, parameter sharing, experience sharing
- hmasd: none

### 11.3.5 Google Research Football
- pages: 358-358
- chunks: B01-C0078
- summary: GRF (Kurach et al. 2020) is a physics-based 3D football simulation supporting either two agents (one per team) or per-player multi-agent control of a cooperating team against a fixed built-in AI, up to the full 11-vs-11 game, plus a set of progressively harder reference scenarios (e.g., defending/scoring with fewer players). Agents choose among 16 discrete actions (movement, passing, shooting, dribbling, sprinting, defensive actions). Two reward functions are offered (goal-only +1/-1, or additionally shaped for ball possession/forward progress), and three observation modes (raw pixels, a compressed global map, or a 115-value feature vector). Song et al. (2023) propose a unified evaluation setting across GRF variants. The authors state GRF suits both cooperative multi-agent evaluation and two-team competitive self-play.
- defines: Google Research Football (GRF) task family (p. 358)
- algorithms: none
- results: none
- figures: Figure 11.6 two GRF tasks: 3 vs. 1 with keeper, and full 11 vs. 11 (p. 359)
- keywords: Google Research Football, GRF, reward shaping, pixel observations, feature vector observations, competitive self-play, cooperative team play
- hmasd: none

### 11.3.6 Hanabi
- pages: 359-359
- chunks: B01-C0078
- summary: Hanabi is a fully cooperative, turn-based card game for two to five players; each player sees every other player's cards but not their own. On a turn, a player gives a hint (revealing rank/color of a chosen player's matching cards, consuming one of a shared pool of eight information tokens), plays a card (advancing or, if illegal, costing one of three shared lives), or discards a card (regaining an information token and drawing a new card). The team scores by building same-color, increasing-rank stacks; the episode ends on three lost lives, all five stacks completed, or the deck exhausted plus a final round; score ranges 0-25. Bard et al. (2020) proposed Hanabi as a challenge because agents must adopt conventions to extend their limited hint-based communication with implicit signaling, making it relevant to cooperative self-play, ad hoc teamwork (Mirsky et al. 2022, cited), and acting/communicating under imperfect information.
- defines: Hanabi game rules (hints, plays, discards, information tokens, lives, scoring) (pp. 359-360)
- algorithms: none
- results: none
- figures: none
- keywords: Hanabi, cooperative card game, partial observability, implicit communication, conventions, ad hoc teamwork, imperfect information
- hmasd: curator_connection: Hanabi's implicit-convention requirement under a strict information channel (hint tokens) is a communication-axis benchmark distinct from the free-form continuous channels used elsewhere in the chapter.

### 11.3.7 Overcooked
- pages: 360-360
- chunks: B01-C0078, B01-C0079
- summary: Overcooked-style environments put players in control of chefs on a top-down grid kitchen who must cooperate to prepare and deliver dishes by moving, picking up ingredients, and interacting with tools (chopping boards, pans, pots, plates). The authors describe two implementations: Cooking Zoo (Rother, Weisswange, and Peters 2023, building on Wang, Wu, et al. 2020), which supports customizable agent count, level layouts, recipes, rewards, and observation spaces, making it well suited to studying generalization to new tasks; and Carroll et al.'s (2019) Overcooked environment, similar in observation/action space but limited to a fixed small set of recipes and five map layouts with less customization, whose advantage is a publicly available human-gameplay dataset for evaluation or training.
- defines: Cooking Zoo (p. 361); Carroll et al. Overcooked environment (p. 361)
- algorithms: none
- results: none
- figures: Figure 11.7 illustration of the Cooking Zoo environment (p. 361)
- keywords: Overcooked, Cooking Zoo, cooperative cooking, customizable tasks, human gameplay dataset, generalization
- hmasd: none

### 11.4 Environment Collections
- pages: 361-365
- chunks: B01-C0079
- summary: Introduces environment collections that bundle many structurally different games behind one unified agent-environment interface (in contrast to earlier environments, whose tasks share transition/observation structure), typically also providing analysis tooling, environment-creation tools, and MARL algorithm implementations.
- defines: environment collection (p. 362)
- algorithms: none
- results: none
- figures: none
- keywords: environment collections, unified interface
- hmasd: none

### 11.4.1 Melting Pot
- pages: 362-362
- chunks: B01-C0079
- summary: Melting Pot (Leibo et al. 2021) is a collection of over fifty multi-agent tasks built on DeepMind Lab2D, targeting two kinds of generalization: across tasks (a diverse set with different agent counts, objectives, and dynamics) and across co-players (per task, a diverse pool of pretrained agent policies). During training a "focal population" is trained on a task; during evaluation the focal population faces varying co-players, sampling some agents from the trained focal population and some "background agents" from pretrained policies, so evaluation tests zero-shot generalization to unfamiliar co-player behavior. Tasks range across zero-sum competitive, fully cooperative common-reward, and mixed-objective games; observability is partial (an 88x88 RGB partial image); the action space is discrete, always including six movement actions (forward/backward, strafe left/right, turn left/right) plus task-specific extras. Agent count varies by task, and the paired-population evaluation protocol means co-player identity, not agent count, is what varies at evaluation time.
- defines: Melting Pot (p. 362); focal population and background agents (p. 362)
- algorithms: none
- results: none
- figures: Figure 11.8 four Melting Pot tasks: Collaborative Cooking, Clean-up (7 agents, apple-collection social dilemma), Chemistry, Territory (p. 362)
- keywords: Melting Pot, generalization, focal population, background agents, zero-shot generalization, social dilemma, DeepMind Lab2D
- hmasd: curator_connection: Melting Pot's focal-vs-background-agent evaluation protocol tests robustness to varying co-player identity within a fixed task, a narrower claim than held-out-N or held-out-k generalization and useful as a boundary example of what "generalization" does and does not mean here.

### 11.4.2 OpenSpiel
- pages: 363-363
- chunks: B01-C0079
- summary: OpenSpiel (Lanctot et al. 2019) is a collection of environments and MARL/planning-search algorithms (e.g., MCTS, Section 9.8.1) focused on turn-based ("extensive-form") games, though its interface also supports simultaneous-move games matching this book's game models. It includes classical turn-based games such as Backgammon, Bridge, Chess, Go, Poker, and Hanabi (Section 11.3.6). Environments mix full and partial observability, and all specify discrete actions, observations, and states. The authors note many OpenSpiel games require long interaction sequences before any reward is received.
- defines: OpenSpiel (p. 363)
- algorithms: none
- results: none
- figures: none
- keywords: OpenSpiel, extensive-form games, turn-based games, MCTS, discrete state/action, sparse terminal reward
- hmasd: none

### 11.4.3 Petting Zoo
- pages: 363-365
- chunks: B01-C0079
- summary: Petting Zoo (Terry et al. 2021) is a MARL research library bundling a large number of multi-agent environments: Atari Learning Environment-based multi-agent games, classic games (Connect Four, Go, Texas Hold'em), continuous control tasks, and an integration of the multi-agent particle environment (Section 11.3.2). It spans full and partial observability, discrete and continuous actions, and dense and sparse rewards, all under one unified interface, plus tools to customize the interface and integrate training with various MARL frameworks.
- defines: Petting Zoo (p. 364)
- algorithms: none
- results: none
- figures: Figure 11.9 three Petting Zoo environments: Pong (2 agents), Multiwalker (3 agents, bipedal robots carrying a shared package), Pistonball (piston-controlling agents moving a ball) (p. 363)
- keywords: Petting Zoo, Atari multi-agent, continuous control, unified interface, Pong, Multiwalker, Pistonball
- hmasd: none

### A Surveys on Multi-Agent Reinforcement Learning
- pages: 366-369
- chunks: B01-C0080
- summary: A reverse-chronological bibliography of MARL survey articles, from Sen and Weiss (1999) — which the authors describe as the first survey of the field to their knowledge — through Zhu, Dastani, and Wang (2024) on communication in deep MARL. The authors state the list is meant to complement the book by pointing to algorithms not covered here, and that they have omitted surveys specific to particular MARL application domains.
- defines: none
- algorithms: none
- results: none
- figures: none
- keywords: MARL surveys, bibliography, reading list
- hmasd: none

### References
- pages: 370-391
- chunks: B01-C0081, B01-C0082, B01-C0083, B01-C0084
- summary: Alphabetically-ordered (by first author surname) bibliography of every work cited in the book, split across four page-contiguous chunks: PDF pages 370-375 list bibliography entries (References), alphabetically ordered by first author surname, spanning entries from Arora, Raman, Ofer Dekel, and Ambuj Tewari to Forges, Francoise. PDF pages 376-381 list bibliography entries (References), alphabetically ordered by first author surname, spanning entries from Fukushima, Kunihiko, and Sei Miyake to Mihatsch, Oliver, and Ralph Neuneier. PDF pages 382-387 list bibliography entries (References), alphabetically ordered by first author surname, spanning entries from Mordatch, Igor, and Pieter Abbeel to Leibo, Csaba Szepesvári, and Thore Graepel. PDF pages 388-391 list bibliography entries (References), alphabetically ordered by first author surname, spanning entries from Vasilev, Bozhidar, Tarun Gupta, Bei Peng, and Shimon Whiteson to Zinkevich, Martin. Not assigned to any of the seven readers (R1-R7 cover pages 16-369); built directly from chunks.jsonl for this merge, not from a reader partial.
- defines: none (bibliography, not exposition)
- algorithms: none
- results: none
- figures: none
- keywords: Bayesian learning, Dec-POMDP, Markov decision process, Nash Q-learning, Nash equilibrium, Q-learning, artificial intelligence, autonomous driving, best response, correlated equilibrium, credit assignment, dynamic programming, fairness, fictitious play, gradient ascent, gradient descent, independent learning, machine learning, minimax, multi-agent reinforcement learning, no-regret, normal-form game, partially observable stochastic game, policy gradient, self-play, social welfare, stochastic game, zero-sum
- hmasd: none (a reference list is not itself a claim or connection; individual cited works are attributed inline elsewhere in this index and in claims.jsonl)

### Index
- pages: 392-395
- chunks: B01-C0085
- summary: PDF pages 392-395 are the book's back-of-book alphabetical subject index, mapping terms to their printed page numbers. Reading order across the two-column layout was visually QA'd (see b01_rebuild_qa.md) and confirmed alphabetically monotone across the column boundary. Not assigned to any of the seven readers (R1-R7 cover pages 16-369); built directly from chunks.jsonl for this merge, not from a reader partial.
- defines: none (back-of-book subject index, not exposition)
- algorithms: none
- results: none
- figures: none
- keywords: Markov decision process, stochastic game, normal-form game, repeated normal-form game, partially observable stochastic game, Dec-POMDP, belief state, Nash equilibrium, correlated equilibrium, coarse correlated equilibrium
- hmasd: none
