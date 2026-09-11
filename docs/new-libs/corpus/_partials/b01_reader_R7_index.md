# B01 reader R7 index — Chapters 10, 11, Appendix A (PDF pages 334-369)

## Chapter 10: Multi-Agent Deep Reinforcement Learning in Practice
- pages: 334-347
- chunks: B01-C0073, B01-C0074, B01-C0075
- purpose: Walks through implementing MARL algorithms in the book's own PyTorch codebase (github.com/marl-book/codebase): the agent-environment interface, building per-agent neural networks (independent and parameter-shared), centralized critics, value decomposition (VDN/QMIX), assorted practical implementation tips, and how to present experimental results fairly given MARL's sensitivity to seeds/hyperparameters and non-scalar solution concepts.
- prerequisites: not in my range (the preface and Section 1.6, which state chapter dependencies, are outside PDF pages 334-369)

## Chapter 11: Multi-Agent Environments
- pages: 348-365
- chunks: B01-C0076, B01-C0077, B01-C0078, B01-C0079
- purpose: Surveys benchmark environments built on the game models of Chapter 3 (normal-form games, stochastic games, POSGs): a complete taxonomy of the 78 structurally distinct strictly-ordinal 2x2 matrix games, seven complex individual environments, and three environment collections. The authors state this selection illustrates game models and gives readers a starting point for experimentation; it is explicitly not comprehensive.
- prerequisites: not in my range (states it builds on Chapter 3's game-model hierarchy, which is outside PDF pages 334-369)

## Appendix A: Surveys on Multi-Agent Reinforcement Learning
- pages: 366-369
- chunks: B01-C0080
- purpose: A reverse-chronological reading list (1999-2024) of MARL survey articles, presented to complement the book's own coverage; the authors state they omit surveys specific to particular application domains.
- prerequisites: not in my range

---

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
