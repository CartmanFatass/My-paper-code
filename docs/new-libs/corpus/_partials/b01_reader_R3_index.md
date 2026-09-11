# B01 Reader R3 index — Chapter 6, Multi-Agent Reinforcement Learning: Foundational Algorithms

## Chapter 6: Multi-Agent Reinforcement Learning: Foundational Algorithms
- pages: 144–187
- chunks: B01-C0033–B01-C0042
- purpose: Building on Chapter 5's basic central-learning and independent-learning reductions of MARL to
  single-agent RL, this chapter introduces four families of foundational MARL algorithms that explicitly
  model or exploit the multi-agent structure of the interaction: joint-action learning (temporal-difference
  learning combined with game-theoretic solution concepts), agent modeling (learning explicit predictive
  models of other agents and best-responding to them), policy-based learning (direct gradient-ascent
  optimization of policy parameters), and no-regret learning (regret matching). All algorithms in this
  chapter are presented for normal-form games and stochastic games under full observability of states and
  actions; Part II of the book extends to deep-learning-based algorithms for the more general POSG model.
- prerequisites: not in my range (the preface, pp. 26–29, and Section 1.6 Book Contents and Structure,
  pp. 44–45, which the brief identifies as stating chapter dependencies, are both outside chunks
  B01-C0033–B01-C0042). Chapter 6 itself explicitly builds on Chapter 5 (general learning process,
  convergence types, central/independent learning, MARL challenges) and Chapter 4 (solution concepts:
  minimax, Nash equilibrium, correlated equilibrium, no-regret, best response), and reuses dynamic
  programming and TD-learning machinery from Chapter 2.

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
