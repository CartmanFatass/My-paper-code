# B01 reader R5 index — Chapter 9 (first half): pages 248–294

## Chapter 9 Multi-Agent Deep Reinforcement Learning
- pages: 248–333 (chapter total per structure.json); this partial covers only 248–294
- chunks in this range: B01-C0055 through B01-C0063 (chapter continues past my range in further chunks covering 9.6–9.10, pages 295–333)
- purpose: extends the deep-learning tools of Chapter 7 and the single-agent deep-RL algorithms of Chapter 8 to MARL. Opens by classifying MARL training/execution paradigms (fully centralized, fully decentralized, CTDE), then covers deep independent learning, multi-agent policy-gradient methods with centralized critics (including counterfactual and equilibrium-selection variants), and value-decomposition methods for common-reward games (VDN, QMIX, QTRAN and successors). Later parts of the chapter (out of this range) cover agent modeling with neural networks, parameter/experience sharing, self-play, and population-based training.
- prerequisites: not directly available (preface and Section 1.6 are outside my range). However, the chapter's own opening paragraph (p. 248, chunk B01-C0055) states it builds on Chapter 7 "Deep Learning", Chapter 8 "Deep Reinforcement Learning", and the tabular MARL algorithms of Part I (Chapters 2–6, especially central/independent learning in Section 5.3 and agent modeling in Section 6.3).

---

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
- pages: 290–294 (text continues past page 294 — the discussion of Wang et al.'s duplex decomposition, Eq. 9.78, is cut off mid-explanation at the end of chunk B01-C0063; continues in R6)
- chunks: B01-C0063
- summary: Presents Son et al. (2019)'s necessary-and-sufficient conditions for IGM (Eq. 9.67–9.69), combining a linear sum of per-agent utilities, an unrestricted centralized Q(h,z,a;θq), and a correction utility V(h,z;θv); shows the conditions are necessary under affine rescaling of individual utilities (Eq. 9.70). Defines QTRAN, which optimizes soft regularization losses (Eq. 9.72, 9.74) toward these conditions rather than enforcing them exactly, so the authors state the IGM property "is only satisfied asymptotically and not throughout the entire training process." Reports QTRAN recovering the optimal policy in the linear, monotonic, and Climbing matrix games (where VDN/QMIX failed), but notes QTRAN's unrestricted centralized Q becomes intractable to train as agent/action count grows. Closes (as this range ends) by introducing weighted QMIX (Rashid et al. 2020, an unconstrained auxiliary mixing network for a weighted value loss) and beginning to introduce Wang et al. (2021)'s duplex decomposition (Eq. 9.78, value+advantage form) — this last item's explanation is incomplete at page 294.
- defines: QTRAN's necessary-and-sufficient IGM conditions (p. 290–291, Eq. 9.67–9.69); weighted QMIX (p. 294, named but not equation-defined in this range); duplex decomposition (p. 294, Eq. 9.78, definition incomplete — continues in R6)
- algorithms: QTRAN (p. 290–292, no numbered algorithm box)
- results: theorem — Son et al.'s conditions are necessary and sufficient for IGM under affine rescaling (p. 290–291, stated, proof not reproduced in this chunk); QTRAN recovers optimal policies on the linear, monotonic, and Climbing games where VDN/QMIX did not (p. 292–294, Figures 9.17–9.19); QTRAN's own IGM guarantee holds only asymptotically during training, not throughout (p. 292); QTRAN's centralized Q becomes intractable for large agent/action counts (p. 294). Chunk flagged equation_text_unreliable.
- figures: Figure 9.17 QTRAN on the linear game (p. 293); Figure 9.18 QTRAN on the monotonic game (p. 293); Figure 9.19 QTRAN on the Climbing game (p. 294)
- keywords: QTRAN, necessary and sufficient IGM conditions, soft regularization, weighted QMIX, duplex decomposition, affine transformation
- hmasd: curator_boundary — QTRAN's own text states its IGM property is not enforced during training, only approached asymptotically through regularization losses; any HMASD claim of "IGM-preserving" decomposition modeled on QTRAN should distinguish the trained-network guarantee from the formal necessary-and-sufficient condition.
