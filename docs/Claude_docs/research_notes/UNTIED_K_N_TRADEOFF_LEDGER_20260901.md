# Untying K and N in hierarchical MARL: the trade-off ledger

Definitions used below (once each):
- **Skill / option**: a temporally extended behaviour selected by a high-level policy and executed by a low-level policy for some duration. In HMASD the duration is a fixed interval k (the "skill interval"); all agents' skills start and stop together.
- **Semi-Markov decision process (SMDP)**: the decision process seen by the high level when each decision lasts a variable number of primitive steps τ; returns are discounted by γ^τ.
- **Termination function β**: the learned or rule-based decision that ends a skill early (option-critic style, "call-and-return").
- **Macro-action (MacDec-POMDP)**: a skill whose execution time varies and can end at different times for different agents (asynchronous).
- **Semigroup property** of a duration model: the k1+k2-step operator equals the k2-step operator applied after the k1-step operator, T(k1+k2) = T(k2)∘T(k1). It holds for the transition kernel of a time-homogeneous skill (behaviour independent of time-since-start) on Markov state; it does not automatically hold for a conditional-mean predictor of a nonlinear stochastic system, nor on observations under partial observability.
- **Permutation invariance / equivariance**: a team policy or value that gives the same output (invariance) or a consistently relabelled output (equivariance) when agents are reordered; the architectural property that lets one network accept any N.
- **Churn**: the roster changes mid-episode (an agent leaves or joins), as opposed to a different but fixed N per episode.

## 0. The two ties in HMASD, stated as invariants

Tie K (the common clock): every agent's skill index is re-drawn at t ≡ 0 (mod k) and held otherwise. Consequences that are invisible while the tie holds:
1. The high-level problem is a stationary SMDP with constant τ = k, so high-level targets are ordinary k-step returns discounted by γ^k.
2. The team skill Z has a clean semantics: "the joint plan for the next k steps".
3. Discriminator-based intrinsic rewards are per step, and every skill accrues the same age profile inside its segment, so any dependence of the reward on elapsed age cancels across skills.
4. Skills may be non-homogeneous inside the window (do X for 5 steps then Y) without anyone having to model it.

Tie N (the fixed roster): the joint skill assignment is an N-tuple, discriminators, critics and mixers carry N-dependent dimensions somewhere, and each agent slot has a stable identity.

Where the ties live in this repository (repo scout, file references verified by the scout):
- k = 10 by default (`config_1.py:134`; the `S7-S3` preset uses 50, `config_1.py:458`, and scenario 7 carries `scenario7_skill_interval_candidates = (10, 25, 50)` at line 459); the episode length must be a multiple of k (`config_1.py:717-719`); reassignment fires at `env_steps % k == 0`, on episode end, or on an invalid skill (`hmasd/agent.py:1897`); Z and every z_i are sampled in one coordinator call (`agent.py:1921-1929`), so the team is synchronous by construction.
- Z is one shared categorical code (n_Z = 6) and each z_i a separate per-agent categorical (n_z = 6), both independent of N (`config_1.py:132-133`). The hard N tie is the coordinator's per-agent value heads, an `nn.ModuleList` of length `config.n_agents` (`networks.py:727-729`), with no padding, masking, or identity embedding; agents are distinguished only by transformer position and head index. The team discriminator reads the global state, whose dimension follows N in the UAV environment.
- The intrinsic reward is computed every step as the discriminator log-probability of the currently held Z and z_i from single-state discriminators (`agent.py:1094-1102`, `3441-3452`; the λ-weighting at `3480-3484`); k enters only through label persistence. High-level bootstrapping already uses γ^elapsed (`hmasd/utils.py:741`, elapsed steps stored at `agent.py:2797`), so the commented-out `** k` at `agent.py:4724` is dead history. What is not discounted is the reward inside a segment: the segment reward is the plain sum Σ r_t (`agent.py:3026`).
- An opt-in horizon-window extension (HA-CTSE: `use_horizon_window`, `H_min`, `H_max`, forced termination after `H_max`; `config_1.py:239-259`; consumed at `agent.py:473`, dispatched at `1876`; keep/edit masks for agents whose duration expired at `agent.py:2010-2031`) unties the duration in multiples of k while keeping the global k boundary (`env_steps % k == 0`, `agent.py:1999`). It is off by default and no first-wave object uses it.
- The process-core route (`ha_ctse_process/`) has untied the duration and the roster, not the clock. Renewal opportunities sit on a shared interval clock (`--skill_interval`, default 10, `standalone_cli.py:43`; `steps_to_check = skill_interval`, `standalone_agent.py:163, 1724`); each renewal draws a lifetime from `(3, 7, 13, 24)` intervals, that is 30 to 240 primitive steps (`config.py:38-40`), so lifetimes differ across agents while every boundary stays on the common grid; a slower team clock (`team_intent_k = 48` intervals, 480 steps, required to exceed the longest lifetime, `config.py:92-95`); a roster of lifecycle-keyed members with JOIN / TEMPORARY_LEAVE / TERMINAL_LEAVE / REJOIN events (`variable_roster_event.py:103-107`); ragged packing in rollout and padded-plus-mask tensors only in replay; a critic with "no identity or fixed roster axis" that pools by sum plus log(1 + count) (`variable_roster_event_models.py:580, 651-653, 734-736`); and SMDP bootstrapping with γ^elapsed (`variable_roster_event.py:540`, `smdp_gae`). A temporary leave freezes the skill and its age; a rejoin forces an immediate renewal opportunity; a terminal leave discards skill and hidden state.

Untying either one converts these invariants into design decisions. The ledger below records what each decision buys and what it costs. Note what the repository's own history says: the base route hides the ties, the process-core route has already paid in code for variable duration (in multiples of the interval) and variable roster, and not for asynchronous boundaries, and the first-wave objects test the untyings one at a time on small hosts. The design question is therefore not "whether" but "which invariants to give back, in what order, and how to measure the price".

## 1. Untying K (skill duration)

Ways to untie, from least to most invasive:
(a) random or scheduled k at training time (robustness to duration; no new learned parts);
(b) a duration chosen by the high level from a finite set (a (z, k) decision; SCDMP's shape);
(c) event-triggered termination (goal reached, surprise, roster change);
(d) learned termination β (option-critic);
(e) fully asynchronous macro-actions across agents.

Trade-off ledger:

K-1 Commitment versus reactivity. Longer commitment means fewer high-level decisions per episode (H/k), better temporally-extended exploration and easier long-horizon credit assignment at the high level, but stale decisions when the world changes. If the relevant latent (goal, failure, roster) switches with hazard λ per step, the expected fraction of a k-step segment that is still "on the right plan" is C(k, λ) = (1/k) Σ_{t<k} (1−λ)^t; it decays roughly as 1/(kλ) once kλ ≫ 1. Toy K1(i), exact:

| k | λ=0.005 | 0.02 | 0.05 | 0.1 | 0.2 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| 5 | 0.990 | 0.961 | 0.905 | 0.819 | 0.672 |
| 9 | 0.980 | 0.924 | 0.822 | 0.681 | 0.481 |
| 13 | 0.971 | 0.888 | 0.749 | 0.574 | 0.364 |
| 20 | 0.954 | 0.831 | 0.642 | 0.439 | 0.247 |
| 40 | 0.908 | 0.693 | 0.436 | 0.246 | 0.125 |

Variable duration restores reactivity, at the price of an extra decision that has its own failure mode: termination collapse, where the termination gradient under noisy advantage estimates drives options to stop after one step, or lets one option swallow the episode (option-critic; deliberation-cost regularization is the standard repair).

K-2 Identifiability is age-confounded. HMASD's intrinsic reward is per step: log q(Z | s_t) and log q(z_i | o_{i,t}, Z) from DIAYN-style discriminators that see one state, not a window (`agent.py:1094-1102`, `3441-3452`). The confound therefore runs through elapsed age rather than window length: later states in a segment carry the skill's integrated effect (a UAV twelve steps into a skill is further along its characteristic displacement than one two steps in), so the per-step reward rises with age, and a variable-duration learner is paid more per step for staying in a skill longer. Under fixed k every skill accrues the same age profile and the effect cancels across skills; under variable k it becomes a duration bias and a moving target for the discriminator as the age distribution shifts during learning. Repairs: condition the discriminator on age (or on the elapsed fraction of the segment), subtract an age baseline from the reward, or score the discriminator only at fixed ages. Toy K1(ii) is not HMASD's estimator; it is an upper bound on how fast evidence about a skill accumulates with the length of window a discriminator could see. M skills with unit drift on a circle, noise σ, Monte Carlo (20,000 segments per cell, standard error ≤ 0.0035):

| k | M=4, σ=1 | M=4, σ=2 | M=4, σ=4 | M=8, σ=1 | M=8, σ=2 | M=8, σ=4 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.581 | 0.415 | 0.325 | 0.325 | 0.217 | 0.169 |
| 5 | 0.887 | 0.612 | 0.435 | 0.610 | 0.352 | 0.233 |
| 9 | 0.968 | 0.728 | 0.490 | 0.749 | 0.444 | 0.266 |
| 13 | 0.988 | 0.814 | 0.544 | 0.830 | 0.509 | 0.303 |
| 40 | 1.000 | 0.974 | 0.753 | 0.983 | 0.773 | 0.463 |

Chance is 0.25 and 0.125. Putting the two effects together as a per-step score J(k) = C(k, λ) · A(k) (a heuristic, not a derived objective) gives the best fixed duration k* on the grid {1, 2, 3, 5, 7, 9, 13, 20, 40}:

| skills, noise | λ=0.005 | 0.02 | 0.05 | 0.1 | 0.2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| M=4, σ=1 | 13 | 9 | 7 | 5 | 2 |
| M=4, σ=2 | 40 | 20 | 13 | 7 | 2 |
| M=8, σ=1 | 40 | 20 | 13 | 9 | 5 |
| M=8, σ=4 | 40 | 40 | 13 | 5 | 1 |

(k* = 40 is the grid edge.) What this table can and cannot say. J omits every benefit of commitment (temporally extended exploration, fewer high-level decisions per episode, deliberation cost), so it is reactivity against identifiability only and its k* is biased short; and any product of a decreasing and an increasing function has an interior argmax that moves with their rates, so the table illustrates the shape of the trade-off rather than corroborating anything. The one robust reading: no single k serves both a calm world and a volatile one, which is the toy version of the HMASD paper's own ablation ("performs poorly with too short or too long skill intervals", k = 25 on some maps and 50 on others). The effect of noise on k* is not resolved by the grid (at λ = 0.1, M = 4 the argmax runs 5, 7, 5 across σ). A fixed k is a bet on one (hazard, identifiability) pair; untying k is the decision to let the learner find that pair per context, and to pay K-2 through K-6 for the privilege.

K-3 SMDP bookkeeping and an extra non-stationarity. With variable τ the high-level target is Σ_{t<τ} γ^t r_t + γ^τ V(s'), and the high-level transition kernel depends on the termination rule. While termination is being learned, the high-level MDP moves under the high-level policy, on top of MARL's own moving-target problem (other agents' policies changing). Fixed k removes this layer entirely. The repository shows how a fixed clock hides bookkeeping. Both routes already bootstrap with γ^elapsed (`hmasd/utils.py:741`; `variable_roster_event.py:540` under `smdp_gae`), so the commented-out `** k` at `agent.py:4724` is dead history. What neither route does is discount rewards inside a segment: the segment reward is the plain sum Σ r_t (`agent.py:3026`), not Σ γ^t r_t. At fixed k that is a constant rescaling. Under variable τ it over-credits long segments by the factor τ(1−γ)/(1−γ^τ): at γ = 0.99 that is 1.12 at τ = 24 and 2.6 at τ = 240, the process-core route's longest lifetime (24 intervals of 10 steps). That is the real duration bias, and it grows with τ. It pushes toward long durations while termination collapse pushes toward short ones, so the sign of the net bias in any given learner has to be measured, not assumed.

K-4 Model and value consistency across durations (the semigroup question). Any component that answers "what happens if skill z runs for k steps" is a family indexed by k. Two ways to build it:
- composed: learn a unit-step (or unit-duration) operator and compose it k times. Consistent across horizons by construction and defined for every k, including durations never trained on; pays with compounding of the unit model's error.
- direct: learn one predictor per duration (or one predictor with k as an input). Accurate at trained durations, inconsistent across horizons (predicting 7 steps directly disagrees with predicting 3 then 4), and no principled extrapolation to unseen k.
Toy K2, normalized k-step prediction error (MSE over variance of the target), least squares, training durations {1, 3, 5, 7, 9} (T), held-out even durations (H), extrapolated durations 11 and 13 (E), 2,000 training origins:

| dynamics | model | 1 T | 2 H | 3 T | 4 H | 5 T | 8 H | 9 T | 11 E | 13 E |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| linear, stable | composed one-step | 0.026 | 0.053 | 0.080 | 0.109 | 0.140 | 0.237 | 0.270 | 0.338 | 0.412 |
| linear, stable | direct per-k (interpolate; nearest for E) | 0.026 | 0.081 | 0.080 | 0.136 | 0.139 | 0.257 | 0.269 | 1.078 | 2.305 |
| linear, stable | direct with k as input | 0.064 | 0.142 | 0.266 | 0.208 | 0.164 | 0.337 | 0.328 | 6.15 | 32.3 |
| saturating (tanh) | composed one-step (quadratic features) | 0.055 | 0.085 | 0.125 | 0.145 | 0.162 | 0.925 | 20.6 | 1.5e10 | 1.1e46 |
| saturating (tanh) | direct per-k | 0.055 | 0.108 | 0.116 | 0.150 | 0.127 | 0.184 | 0.176 | 0.985 | 2.169 |
| saturating (tanh) | direct with k as input | 0.104 | 0.179 | 0.313 | 0.229 | 0.150 | 0.252 | 0.224 | 4.82 | 23.5 |

Measured inconsistency of the direct family, ‖T(3+4) − T(4)∘T(3)‖ relative to the target norm: 0.15 to 0.20 in every setting. Readings, with the toy's limits stated. (1) In the linear case both the composed and the direct models are in-class (A^k x is linear), so the held-out gap is the interpolation rule ((A³ + A⁵)/2 ≠ A⁴), not a property of direct predictors; the extrapolation gap is real. (2) In the saturating case, composing an unbounded quadratic map produces a degree-2^k polynomial that overflows by k ≈ 9; that is misspecification blow-up, not the classic compounding-error growth (which is polynomial under a Lipschitz unit model); a bounded unit map would degrade gracefully, and composition already loses to the direct model at k = 6 (0.198 against 0.155) before it explodes. (3) Direct per-duration predictors are the most accurate at trained durations, interpolate acceptably, and never extrapolate; k as a polynomial input is the worst extrapolator of all. (4) The 14–20% inconsistency of the direct family is invisible unless measured; it is a cheap diagnostic any duration-untied design should report. Two counter-arguments a reviewer will raise, both correct: time-homogeneity is necessary but not sufficient, because Chapman–Kolmogorov composes Markov kernels (distributions), not conditional-mean point predictors, so for nonlinear stochastic dynamics a composed mean predictor is biased even with a perfect one-step model (E[f(x)] ≠ f(E[x])), and "consistent by construction" means self-consistent (INC = 0), not in agreement with the true k-step operator; and the semigroup holds on Markov state, not on observations, so under partial observability (HMASD's low level) the operator on observations is not a semigroup at all.
The semigroup property is a structural prior, and it is only correct for distribution-level or linear models of time-homogeneous skills on Markov state. A skill that behaves differently in its final steps (decelerate, hover, hand over) makes the k-step operator a genuine family, not a semigroup, and enforcing consistency then injects bias. Fixed-k hierarchies never have to decide this; untied-k hierarchies must, explicitly.

K-5 The common clock is what gives the team skill its meaning. Synchronous fixed k means one joint plan per window. Asynchronous durations turn every high-level decision into a partial re-assignment over the subset of agents whose skills just ended, while the others are mid-plan. Two consequences: the coordinator must re-assign a variable subset, which a fixed-N coordinator handles by masking (the HA-CTSE path already does this with keep/edit masks for agents whose duration expired, `agent.py:2010-2031`) and the field handles by padding, whose cost ACAC names as "misaligned asynchronous experiences and spurious correlations"; and joint-skill discriminators lose a well-defined window over which "the team did Z". The MacDec-POMDP line handles the mechanics (macro-observations, per-agent asynchronous updates), and the known price is more complex centralized training and lower sample efficiency because time steps no longer align.

K-6 Statistical cost. Variable durations spread the high-level data over duration bins, each of which must be explored; high-level returns have higher variance (variable τ); low-level policies must be competent on segments of all lengths.

K-7 Measurement cost. Competence, skill semantics, and comparisons across algorithms must be matched on the duration distribution, or a duration difference will masquerade as an algorithm difference.

## 2. Untying N (agent count)

Ways to untie: parameter sharing plus permutation-invariant or equivariant encoders (attention, sets, graphs, transformers); entity-based factorization; mean-field approximations; N-agnostic mixers (attention or hypernetwork mixers); training curricula over N; open ad hoc teamwork methods that model the current teammates as a graph.

Trade-off ledger:

N-1 Symmetry versus specialization. Exact permutation invariance is what makes any N admissible, but it also means identical agents in identical situations act identically, so they cannot fill distinct roles unless something breaks the symmetry. The three ways to break it are identity inputs (which reintroduce N-indexed structure), stochastic tie-breaking (whose coverage probability decays with N and K), or a coordinator that assigns roles. Toy N1(i), exact: probability that N exchangeable agents, each picking one of K roles uniformly, cover every role.

| K | N=K | N=K+2 | N=2K | N=3K | N=20 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 0.500 | 0.875 | 0.875 | 0.969 | 1.000 |
| 3 | 0.222 | 0.617 | 0.741 | 0.922 | 0.999 |
| 4 | 0.094 | 0.381 | 0.623 | 0.875 | 0.987 |
| 6 | 0.015 | 0.114 | 0.438 | 0.785 | 0.848 |

Without a coordinator, coverage is a coin flip even at N = 2K, and the shortfall grows with K. HMASD's coordinator is the third way, which is why it is the component that must change when N is untied.

N-2 The joint assignment does not port across N, and the team code's meaning is N-bound. In HMASD the team skill Z is a single shared code trained through q(Z | s) on the global state (`agent.py:3441`), and the joint assignment is the N-tuple (z_1, …, z_N), a space of size n_z^N that is different for every N. REVIEWER_INFERENCE: Z's semantics is whatever global-state configuration the team tends to produce at the N it was trained at, even though the code has n_Z values regardless of N. The N-portable summary of an assignment is its role composition (how many agents hold each skill; C(N+K−1, K−1) values, the quotient of n_z^N by relabelling); the equivariant matching of agents to roles carries the rest back, so the composition is not a reduction in what must be learned, it is the part the coordinator can decide invariantly of N. Toy N1(ii), K = 4 skills, joint assignments 4^N against compositions C(N+3, 3), for scale:

| N | 3 | 5 | 7 | 9 | 15 | 21 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| joint 4^N | 64 | 1,024 | 16,384 | 262,144 | 1.1e9 | 4.4e12 |
| compositions | 20 | 56 | 120 | 220 | 816 | 2,024 |

The cost is that "agent 3 does X" is no longer expressible unless identities are stable, and under churn they are not; the process-core route's lifecycle keys are exactly the device that keeps identity stable across temporary leaves.

N-3 Credit assignment and mixing. Fixed-N mixers have N-dependent input dimensions; N-agnostic mixers pool over a set, and the pooling choice (sum, mean, max) silently encodes how the team value scales with N. Counterfactual baselines need a per-agent default action, which is undefined for an agent that has left; the joint value is discontinuous at a roster change.

N-4 Input statistics shift with N even under an invariant architecture: neighbour counts, densities, contention for shared resources all change, and size generalization fails when the distribution of local structure shifts with N (Yehudai et al. 2021). Pooling and readout do not limit what can be represented (sum pooling with a rich encoder represents count and mean alike); they fix the extrapolation law: sum scales with N, mean discards it, and an explicit log N input (which the process-core critic uses, `variable_roster_event_models.py:651, 735`) is a feature never seen at held-out N that a multilayer readout extrapolates linearly (Xu et al. 2021). The question is which law matches the physics of the quantity (a total or a density). This is the specific question FRRIE's relational-bias arms ask (how far edge weights may drift from a physical prior), and it is why held-out N must be tested in both directions (FRRIE's N = 6 and 21 around training N = 9 and 15).

N-5 Churn is not "another N". A different N per episode is a distribution-shift problem; a roster change mid-episode additionally invalidates the current joint plan. A synchronous fixed-k hierarchy can only re-assign at the next boundary, so the expected reaction delay is about k/2 steps plus re-planning; whether that matters depends on the host's recovery window (VNFC's is 60 steps against a k of order 10) and on whether the low level can absorb the change from its own observation. Zero-delay coverage of a single loss (no role uncovered even before re-planning) requires redundancy N ≥ 2K in a balanced assignment; with re-planning at the next boundary the gap is transient, and the right price is coverage gap × delay. Below 2K the expected number of uncovered roles immediately after one loss is (roles with multiplicity 1)/N, which for a balanced assignment equals (2K − N)/N on K ≤ N < 2K and 0 from N = 2K on (Toy N1(iii), exact: K = 3 needs N = 6, K = 4 needs N = 8, K = 8 needs N = 16; at N = K every loss uncovers a role, at N = K+1 it uncovers one with probability (K−1)/(K+1)). This is the efficiency–robustness trade-off expressed in the skill assignment, and it is what VNFC's split objective (recovery within 60 steps and total utility, weighted 1:1) is designed to price.

N-6 Intrinsic-reward scale depends on N. The team-skill mutual information I(Z; s) has a ceiling that grows with the number of distinguishable joint configurations, so intrinsic reward magnitudes drift with N unless normalized per capita.

N-7 Sample and evaluation cost. Generalizing across N either multiplies training cost (curriculum over N) or leans on architecture and risks silent failure at unseen N; metrics must be per capita or explicitly total, and stated as such.

## 3. How the two untyings interact

1. Mid-episode churn (untied N) forces event-triggered termination (untied K) only when the required reaction time is shorter than about k/2 plus re-planning latency and the low level cannot absorb the roster change from its own observation. At k = 10 the mean delay is about 5 steps against VNFC's 60-step recovery window, so VNFC does not need it; a host with a 5-step window would.
2. Asynchronous durations (untied K, form (e)) force partial re-assignment, handled by masking in a fixed-N coordinator or by a set coordinator; they do not by themselves require N-agnostic machinery.
3. Both move complexity into the coordinator: it becomes a set-to-set, event-driven policy over roles and durations. The literature has each half and not the pair: the MacDec-POMDP line (Xiao, Hoffman, Amato 2019; Xiao and Amato 2022; Lyu et al. 2023) handles asynchronous macro-actions for fixed teams, and open ad hoc teamwork (GPL, Rahman et al. 2021) handles agents joining and leaving with primitive actions. Neither scout found work that does asynchronous learned skills over an open roster (UNKNOWN: absence of evidence in two searches, not a proven gap). RODE is the one skill-level result that touches both axes: a role selector at a coarser time scale reported transfer to three times the number of agents; its authors attribute the transfer to the action representations, so reading it as abstraction-buys-N-transfer is REVIEWER_INFERENCE.
4. The semigroup question and the churn question meet in the duration model: a roster change inside a segment breaks time-homogeneity, so a composed duration model is wrong across a churn event unless the roster is part of its state.

## 4. What this project's evidence actually says today

Per direction (repo scout, quotes from the direction files):
- SCDMP unties k: the consumed FCEOV object used a fixed k = 13; the unrun B01 scout uses k ∈ {7, 13}. The one valid result is a nonpass at frozen resolution ("`TARGET_CANDIDATE_ORDER_VALUE_NOT_ESTABLISHED_AT_FROZEN_RESOLUTION`") about the value of action order, not about duration. The repository's own K-untying lineage was folded into SCDMP: lease-gated rebinding, renewal-indexed plasticity, and event-triggered budgeted renewal are all absorbed there (legacy index).
- UCOPE unties k as a paid, agent-chosen probe period: K_train = {1, 3, 5, 7, 9}, K_eval = {2, 4, 6, 8}. Valid evidence is the odd-support audit: 0/72 competent and 0/72 near-competent policies on the training durations, so the extrapolation question was never reached. The direction file itself disclaims any variable-k or variable-N conclusion.
- VNFC unties N with mid-episode loss: training support N = {3, 5}, held-out N = 7, one unannounced executor loss. The current object has no valid learner result (R01 closed on a presentation-dependent conformance defect; R02 unrun). The earlier B1 (train N ∈ {3, 5, 7}, held-out even N ∈ {4, 6}, interpolation only) recorded that "`B-REBIND` satisfies the registered project-facing variable-N value condition as an end-to-end package", while attributing most of the gain to a hand-built coverage-aware joint decoder rather than to learning.
- FRRIE unties N across episodes with a fixed roster inside each: train N = {9, 15}, held-out N = {6, 21}, both sides extrapolation. "No B01 result activity has occurred."
- RCLE unties N through churn continuity of exploration state; its previous recast closed `HARD_NO_CODE`; a fresh churn-recovery object was authorized on 2026-09-01 with no sets or results yet.
- CBSC touches neither k nor N.
- The project's own framing already joins the two untyings: the dynamic-roster testbed contract states "The final target is one shared skill-based algorithm that supports both runtime-variable team membership and variable realized skill lifetime." A hazard-based SMDP alternative to duration buckets exists as a design note and is explicitly not the implemented core.
- One vocabulary trap: "churn" means Z-boundary switching frequency in the R21 autopsy and roster loss in VNFC.

Standing position from the first-wave review of 2026-09-01: no valid learner result on either untying exists yet. UCOPE's odd-train/even-eval duration split is the right test for K-4 but never reached the question because no learner became competent on the training durations (source audit: optimizer exposure about an order of magnitude short). FRRIE's two-sided held-out N is the right test for N-4 and has not run. VNFC's churn objects have not produced a valid learner result (B1 gains were explained by hand-injected structure; R01 closed on a near-tie witness; R02 unrun). SCDMP's valid `.3` signal is about the value of action order at one state, with the duration untying (k ∈ {7, 13}) designed but unrun.

## 5. Design guidance that follows

1. Untie K in stages and stop at the least invasive stage the science needs: random-k training for robustness; event-triggered termination only where the required reaction time is shorter than about k/2 plus re-planning and the low level cannot compensate; learned β last and only with a deliberation cost.
2. Discount inside segments (Σ γ^t r_t) before any duration is untied. Enforce semigroup consistency only for distribution-level or linear models of time-homogeneous skills on Markov state; otherwise index models by (k, elapsed time), measure the inconsistency INC = ||T(k1+k2) − T(k2)∘T(k1)|| and report it, and give up extrapolation in k honestly.
3. Condition discriminators on age or subtract an age baseline from the intrinsic reward; normalize the team-level term per capita.
4. Choose pooling and readout for the extrapolation law the physics implies (sum for totals, mean for densities), treat any explicit N or log N input as a feature that extrapolates linearly, and test held-out N on both sides.
5. Represent the team-level decision as a role composition plus an equivariant assignment; whether the shared code Z survives untied N is an empirical question (its N-bound semantics is inference), so test it rather than retire it.
6. Price robustness explicitly: redundancy N ≥ 2K for single-loss coverage, or a measured coverage gap; keep efficiency and robustness as separate metrics as VNFC does.
7. Order of evidence: competence on the training support first (durations or rosters), then the held-out split. A split test on an incompetent learner is uninformative (UCOPE).

## 6. Literature anchors, labelled

Labels: DIRECT = verbatim from the paper text (local per-paper JSON in `C:/Projects/Inst-sci/papers/MyLib/json/<ID>.json`, or fetched by the web scout); PARAPHRASE = a scout's reading; CURATOR = curator paraphrase in `docs/new-libs` (its chunk files are absent on disk, so nothing there can be quoted); REVIEWER_INFERENCE = mine; UNKNOWN = not verifiable.

Local library, duration (DIRECT unless marked):
- MARL-0553, HMASD, NeurIPS 2023: "k ∈ N+ is the number of timesteps between two consecutive skill assignments and is called skill interval" (p. 5); "HMASD performs poorly with too short or too long skill intervals, which demonstrates that an appropriate number of timesteps is necessary" (p. 16). The Dec-POMDP tuple fixes N (PARAPHRASE).
- MARL-0449, ACAC, ICML 2025: "Macro-actions—sequences of actions executed as single decisions—facilitate longterm planning but introduce asynchrony, complicating Centralized Training with Decentralized Execution" and "Existing CTDE methods use padding to handle asynchrony, risking misaligned asynchronous experiences and spurious correlations" (p. 1). Per-agent learned termination β over history.
- MARL-0543, VO-MASD, IJCAI 2025: "Each skill z ∈ Ωz, after being selected, will be executed for H time steps – a predefined subtask duration" (p. 2); the subgroup size varies, the duration does not.
- MARL-0011, HAVEN, AAAI 2023: "the high-level advantage function can give low-level policies the temporal abstraction of next k steps" (p. 3), fixed k.
- VS-0001, DCSL, ICLR 2025 (single-agent): "fixed skill lengths fail to reflect the varying durations of real-world behaviors" (p. 1); "trade-off between skill granularity and learning efficiency" (p. 22). VS-0005, UTE, AAAI 2024 (single-agent): the SMDP option tuple ⟨I, π, β⟩ (p. 3).
- B03 (Oliehoek and Amato, Dec-POMDPs) and P17 (MAVEN) carry CURATOR notes that their k is a communication delay or an action count, not an adaptive skill period.

Local library, agent count (DIRECT unless marked):
- MARL-0561, NeurIPS 2023: "risk of overfitting to the training set, which may lead to catastrophic performance when facing dramatically varying team compositions during execution" (p. 1); zero-shot across compositions.
- MARL-0104, ADAPT, AAAI 2026: "mainstream MARL architectures assume fixed-size observation and action spaces—each neural network is hard-wired to accept a preset number of input features ... and emit a predetermined number of actions" (p. 1).
- MARL-0509, TEM, IJCAI 2023: targeted communication "is not scalable when the number of agents varies" (p. 1). MARL-0075, GTDE, AAAI 2025: "new agents can only be linked to existing agents during training and cannot be linked to each other" (p. 7), so no joining after training.
- MARL-0471, ICML 2025: "The number of agents can be an effective curriculum variable" (p. 1). MARL-0637, SUBSAMPLE-MFQ, NeurIPS 2025: "The choice of k reveals a fundamental trade-off between the size of the Q-table and the optimality" (p. 2), where that k is an agent-subsample size. MARL-0438, major-minor mean field, ICML 2024: the strict mean-field assumption "is too inflexible in practice" (p. 1).
- Mean-field and graphon cluster in `docs/new-libs` (P08–P24, B01, P16), CURATOR: N-independent mean-field complexity "must not be read as generic held-out-N policy robustness" (P14-CL006); a shared-parameter policy can be exponentially worse than the unrestricted optimum as N grows (P16-CL001).

Local library, multi-step models (DIRECT): MARL-0016, MAG, AAAI 2023: in multi-step rollouts of per-agent models "local prediction errors can be propagated ... eventually give rise to considerably large global errors" (p. 1), the multi-agent face of the compounding cost in K-4.

Zero local hits, either library: ROMA, RODE, ODIS, HSD, DIAYN as indexed papers; the SMDP formalism inside a MARL paper; ad hoc teamwork or open systems by name; in-episode churn; permutation invariance by name; successor features, γ-models, jumpy models, or any composition property; and any single paper that treats duration and agent count together.

External (web scout), duration:
- Options as SMDP actions with multi-step backups: Sutton, Precup, Singh, Artificial Intelligence 1999 (PARAPHRASE).
- Termination collapse in end-to-end option learning, options shrinking to one step or one option swallowing the episode; the deliberation-cost repair: Bacon, Harb, Precup AAAI 2017; Harb et al. AAAI 2018 (PARAPHRASE, with follow-up documentation of the collapse in arXiv:2011.02565 and arXiv:2010.02756).
- HMASD's own duration sensitivity: Yang et al. NeurIPS 2023, Appendix D, "HMASD performs poorly with too short or too long skill intervals"; k = 25 on two SMAC maps and 50 on two others; no experiment trains at one k and tests at another (PARAPHRASE of the ablation; the quoted clause is DIRECT per the scout).
- Asynchronous macro-actions: Xiao, Hoffman, Amato CoRL 2019; Xiao and Amato NeurIPS 2022; Xiao et al. IJRR 2025 (PARAPHRASE: asynchrony avoids idling on the slowest teammate and matches robot execution, and breaks synchronous policy-gradient machinery). Lyu et al. IROS 2023, DIRECT: "multi-robot option executions are often asynchronous" while centralized methods "always select new options at the same time".
- Multi-agent option discovery: Chakravorty et al. AAMAS 2020 (centralized option evaluation, decentralized intra-option control); Chen et al. 2022/2023 (joint-space covering options, exponential in N, Kronecker approximation); Steleac, Sridharan, Abel 2025/2026, DIRECT: existing methods "often sacrifice coordination by producing loosely coupled or fully independent behaviours"; VO-MASD (IJCAI 2025) and NBDI (2025) learn variable-length or novelty-terminated skills (PARAPHRASE).
- Roles at a coarser time scale: RODE (Wang et al. ICLR 2021), role selector at lower temporal resolution, reported transfer to three times the agents (PARAPHRASE); ROMA (ICML 2020), per-step continuous roles, the opposite end of the commitment axis (PARAPHRASE).
- Temporally-extended ε-greedy (Dabney, Ostrovski, Barreto 2020): the single-agent ancestor of the persistence-versus-reactivity trade (PARAPHRASE).

External (web scout), agent count:
- Entity-token transformers: UPDeT (ICLR 2021); TransfQMix (AAMAS 2023) with a transformer mixer; MAT (NeurIPS 2022) sequence decoding that imposes an agent order (PARAPHRASE).
- Sub-group randomization: REFIL (ICML 2021), with the scout's note that it "performs poorly in unseen tasks", so size randomization in-distribution is not out-of-distribution transfer (PARAPHRASE).
- Curricula over N: DyAN / From Few to More (AAAI 2020), EPC (ICLR 2020) (PARAPHRASE).
- Permutation-invariant critic scaling to 30× more agents than trained on, between episodes not within one: PIC (CoRL 2019) (PARAPHRASE).
- Mean-field MARL (ICML 2018), DIRECT: interactions "approximated by those between a single agent and the average effect from the overall population".
- Open teams with mid-episode arrival and departure: GPL (Rahman et al. ICML 2021; JMLR 2023), the clearest hit on churn; Mirsky et al. 2022 survey framing open teamwork as largely unsolved (PARAPHRASE). Tang, Xu, Wang 2022 on agents joining or leaving training, mid-episode scope UNKNOWN.

External (web scout), multi-horizon models:
- γ-models (Janner et al. NeurIPS 2020): the explicit "tradeoff between training-time and testing-time compounding errors" (PARAPHRASE of the paper's framing); TDMs (Pong et al. ICLR 2018) horizon-indexed values; MTS3 (Shaj et al. NeurIPS 2023) multi-time-scale state space; Skipper (Zhao et al. ICLR 2024); Any-step Dynamics Model (Lin et al. 2024), horizon-conditioned and trained over a k range, extrapolation UNKNOWN; Farebrother et al. 2026, DIRECT: "a novel consistency objective that aligns predictions across timescales", the closest published relative of the semigroup requirement.

Gaps, labelled UNKNOWN (absence of evidence across one local and one web search): no skill-discovery paper found trains on one duration set and evaluates on another, so UCOPE's odd/even split may be new; mid-episode churn with learned skills appears unpublished; asynchronous termination is handled only for fixed rosters.

## 7. Predict-then-verify prompts for the reader

Q1. A skill decelerates during its last two steps. Does the k-step operator of that skill satisfy T(7) = T(4)∘T(3)? Commit to an answer, then read K-4.
Q2. Five agents, three roles, a shared exchangeable policy with no coordinator, each agent picks a role uniformly. Probability that all three roles are covered? Commit, then read Toy N1(i).
Q3. Fixed synchronous k = 13. An agent fails at a uniformly random time inside a segment. Expected number of steps before the team can re-plan? Commit, then read N-5.


## 8. Addendum, 2026-09-02: two parallel directions, and the theory ceiling

The owner has since fixed two things this memo left open.

First, the two untyings are two parallel research directions, not one joint algorithm. Section 3 stays as an analysis of how they would interact; it is not a design target. Each direction holds the other quantity fixed as a stated parameter: the duration direction fixes N, the roster direction fixes k and reports sensitivity to it wherever its cost bound contains k (the ≈ k/2 re-planning delay in N-5). This is now `MARL_EMPIRICAL_EVIDENCE_SPEC.md` §11.5.

Second, the theory ceiling. Nothing in K-2, K-4, or N-1 is to be proved; the semigroup property, age-conditioned identifiability, and permutation equivariance are design heuristics that say what to try. The theoretical product per direction is a suboptimality bound for the scheme as implemented. Both bounds are already in this memo in pieces:

- Duration direction, implemented scheme: a fixed duration menu (for instance the process-core lifetimes 3, 7, 13, 24 intervals) with an optional constant-hazard early termination, chosen by one discrete head. Bound: the within-segment valuation bias factor τ(1−γ)/(1−γ^τ) (K-3, 1.12 at τ = 24 and 2.6 at τ = 240 for γ = 0.99) plus the commitment cost C(k, λ) against k* (K-1, Toy K1). The sum bounds the menu scheme's gap to the optimal duration policy under time-homogeneous drift.
- Roster direction, implemented scheme: sum-plus-log-count pooling in the shared value head and boundary-deferred re-planning, no event-triggered termination. Bound: expected uncovered fraction (2K−N)/N under exchangeable sampling (Toy N1, zero for N ≥ 2K) plus expected delay ≈ k/2 times the uncovered-period gap (N-5). Both terms are directly measurable in the same run that tests the scheme.

The rule that survives: a bound's assumptions must match the implemented scheme. A bound for a learned optimal terminator or a fully equivariant coordinator says nothing about the menu or pooling scheme actually run.

The research order per direction, replacing the guidance in section 5 where they conflict: an inspiration model (drifting bandit with commitment for k; variable-budget combinatorial bandit for N), a single-agent bridge (age-conditioned option termination on a moving-goal grid; variable-size set input with sum versus mean pooling), then one-to-three-seed B runs on the existing route with one change at a time. Train-k / test-k′ and train-N / test-N′ splits, oracle-retuned baselines, and stated failure boundaries are what a repeatable B signal gets promoted into, not what it must pass to start.
