# B01 reader R6 index (chunks B01-C0064–B01-C0072, PDF pages 295–333)

## Chapter 9: Multi-Agent Deep Reinforcement Learning (second half)
- full chapter pages: 248–333; chunk range covering the whole chapter is not in this
  reader's assignment — R6 covers only chunks B01-C0064–B01-C0072 (pdf pages 295–333),
  i.e., the back half of the chapter starting partway through 9.5.5
- purpose (as the chapter's own summary, Section 9.10, states it): the chapter presents
  deep-learning-based MARL algorithms built on the training/execution paradigms of
  centralized training and execution, decentralized training and execution, and CTDE.
  It covers independent learning, multi-agent policy gradient with centralized critics,
  value decomposition for common-reward credit assignment, neural agent modeling of
  other agents' policies, parameter/experience sharing for homogeneous-agent
  environments, and policy self-play / population-based training culminating in
  AlphaZero and AlphaStar.
- prerequisites: not in my range (stated in the preface and Section 1.6, which are
  outside chunks B01-C0064–B01-C0072)

---

### 9.5.5 Beyond Monotonic Value Decomposition (tail only — begins in R5)
- pages: 295 (section body spans pdf pages 290–294, which is in R5's range; only the
  closing paragraph on p. 295 falls in my range)
- chunks: B01-C0064
- summary: The closing paragraph (only part in this range) notes that QPLEX's
  advantage-based IGM decomposition (Eq. 9.79) can be upheld throughout training, and
  that FACMAC extends the value-decomposition idea to multi-agent policy gradient by
  training a decomposed centralized critic (not necessarily monotonic, since the IGM
  property is not required when parameterized policies handle decentralized execution).
- defines: advantage-based IGM decomposition, Q(hi,ai) = V(hi) + A(hi,ai) (p. 295)
- algorithms: QPLEX (p. 295, name only, uses multi-head attention mixing of advantage
  functions — Vaswani et al. 2017); FACMAC (p. 295, decomposed centralized critic +
  individual policy networks, non-monotonic mixing allowed)
- results: none
- figures: none
- keywords: QPLEX, advantage decomposition, IGM, FACMAC, centralized critic decomposition
- hmasd: none

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
