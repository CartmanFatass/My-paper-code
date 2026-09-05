# B01 Reader R2 Index — Chapters 4–5 (PDF pages 90–143)

Reader: R2. Range: chunks B01-C0021 through B01-C0032, PDF pages 90–143, covering
Chapter 4 "Solution Concepts for Games" and Chapter 5 "Multi-Agent Reinforcement
Learning in Games: First Steps and Challenges."

## Chapter 4: Solution Concepts for Games
- pages: 90–117
- chunks: B01-C0021–B01-C0026
- purpose: Defines what counts as a "solution" to a game. Gives a universal definition
  of expected return Ui(π) for the POSG model (history-based and recursive/Bellman
  forms), then builds a hierarchy of equilibrium solution concepts — best response,
  minimax, Nash equilibrium, ε-Nash equilibrium, (coarse) correlated equilibrium —
  followed by refinement/alternative concepts (Pareto optimality, social welfare and
  fairness, no-regret), and closes with the computational complexity (PPAD-completeness)
  of computing Nash equilibria. States that all definitions assume finite game models
  (finite state/action/observation spaces, finite number of agents).
- prerequisites: not in my range (the book states dependencies in the preface and
  Section 1.6, which are outside chunks B01-C0021–B01-C0032; within-range text says the
  chapter's definitions build on the game models of Chapter 3, in particular the POSG
  model of Section 3.4).

## Chapter 5: Multi-Agent Reinforcement Learning in Games: First Steps and Challenges
- pages: 118–143
- chunks: B01-C0027–B01-C0032
- purpose: Introduces reinforcement learning as the computational method for finding the
  solution concepts of Chapter 4. Defines a general MARL learning process and several
  types of convergence (pointwise to a solution, and weaker forms: expected return,
  empirical distribution, empirical distribution to a set, average return). Introduces
  two baseline single-agent RL reductions — central learning (Central Q-learning) and
  independent learning (Independent Q-learning) — compared empirically on a level-based
  foraging task. States and illustrates the four core MARL challenges: non-stationarity,
  equilibrium selection, multi-agent credit assignment, and scaling to many agents.
  Closes with self-play vs. mixed-play as two modes of algorithm use among agents.
- prerequisites: not in my range (within-range text explicitly builds on Chapter 4's
  solution concepts and Chapter 2's single-agent RL/TD-learning background).

---

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
