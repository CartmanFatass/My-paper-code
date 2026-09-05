# B01 reader R4 index — Chapters 7–8 (PDF pages 188–247)

## Chapter 7 — Deep Learning
- pages: 190–211 (Part II introduction precedes at pp. 188–189, within chunk B01-C0043)
- chunks: B01-C0043 – B01-C0047
- purpose: Introduces deep learning as a general function-approximation framework to motivate its use in RL/MARL: why tabular representations fail to generalize and scale (7.1), linear function approximation as a first, feature-limited fix (7.2), feedforward neural networks and their building blocks (7.3), gradient-based optimization — loss functions, gradient-descent variants, and backpropagation (7.4) — and specialized architectures for spatial (CNN) and sequential (RNN) inputs (7.5).
- prerequisites: not in my range (preface pp. 26–29 and Section 1.6 "Book Contents and Structure," pp. 44–45, are outside this reader's chunk range). Within range, the chapter states it "explains all foundational concepts required to understand the following chapters" (p. 190) and that Chapters 8 and 9 build on it (p. 210).

## Chapter 8 — Deep Reinforcement Learning
- pages: 212–247
- chunks: B01-C0048 – B01-C0054
- purpose: Bridges Chapter 2 (tabular RL) and Chapter 7 (deep learning) before Chapter 9 extends these ideas to multi-agent settings. Builds deep value-function approximation up piece by piece into DQN (8.1: moving target problem, breaking correlations via replay, target networks, DDQN, and further extensions), covers policy gradient algorithms (8.2: policy gradient theorem, REINFORCE, actor-critic, A2C, PPO, and parallel/concurrent training), and gives practical guidance on handling partial observability via RNN-conditioned histories (8.3).
- prerequisites: stated in range — "It naturally builds on the content of Chapters 2 and 7" (p. 212).

---

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
