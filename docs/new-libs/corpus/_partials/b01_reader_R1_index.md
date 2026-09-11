# B01 reader R1 index partial

Range: B01-C0004 through B01-C0020 (PDF pages 16-89): Summary of Notation, List of
Figures, Preface, Chapter 1 Introduction, Chapter 2 Reinforcement Learning, Chapter 3
Games: Models of Multi-Agent Interaction.

## Chapter-level headers

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
