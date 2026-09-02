# Toy hosts and the UAV environment: design advice

Vocabulary: a **host** is the project's word for an environment built to isolate one mechanism; an **oracle** is a reference controller whose return defines the competence ceiling; **common random numbers (CRN)** means giving each entity its own random stream so two arms see the same noise and their difference is low-variance; **C-TRANSFER** is the evidence class for held-out transfer to a declared simulator distribution.

## 1. What exists (inventory, read-only)

The UAV family (`envs/`, 23,816 Python lines, 705 C++): one engine (`MultiUAVEnv`, path-loss models, greedy max-SINR association) and seven scenarios. Scenarios 1 and 2 are wired to `main.py`; 3 is orphaned (tests and benchmarks only); 4 to 7 (forced relay, belief map, progressive, energy-aware) are reached only through the process-core factory. N is fixed per scenario (5, 5, 20, 12, 12, 6, 8). Actions are continuous 3-D velocity (4-D in scenario 7). Per-agent observations are padded neighbour lists (`max_observed_users × 3 + max_observed_uavs × 4 + …`, about 104 numbers). Rewards come in at least seven variants (coverage/SINR, paper throughput minus power, load-balance with repulsion, awareness, handover, progressive demand-aware, constrained QoS with dual-ascent safety cost and potential-based shaping). RNG is a legacy `RandomState`; 3GPP line-of-sight draws and cluster mobility are stochastic. Lifecycle, routing, reward, observation and RNG are Python-owned; C++ covers only geometry and radio kernels (100× faster on the kernel, 2–3× on the full step because Python still sequences everything else). Scenario 7 already contains churn-like events: temporary UAV failures, battery depletion, charging contention.

Two reusable variable-N toys already exist in the process-core route: the G32 continuous roster (member capacity {6, 8, 12}, join/leave at fixed times 12/24/36, horizon 48, 2-D continuous actions, service-matching reward, a constructive exact oracle, per-member CRN streams, a six-coordinate native hot path) and the F0/F1 dynamic roster testbed (horizon 80, up to 6 lifecycles, 3 discrete actions, terminal-only reward, frozen ledger seeds). Three unit-test probes (value, policy, discriminator) also exist.

The first-wave hosts were each built from scratch:

| Host | Direction | Horizon / decisions | N | Actions | Oracle / gate | Code (Py + C++) |
| --- | --- | --- | --- | --- | --- | --- |
| RIDGEGATE-2Z/RSCF | FRRIE | 12 steps | multiples of 3; train {9, 15}, eval {6, 9, 15, 21} | 6 discrete, role-masked | delivery/balance/waste in [0, 1] | 22,102 + 777 |
| BPCR two-zone | VNFC | 6 decisions | train {3, 5}, held-out 7, one unannounced loss | 4 handoff tokens | none declared beyond fixed controllers | 3,695 + 378 (r09); 4,699 (r02) |
| QUAD-UAV-PALLET-GANTRY-24P5M-v1 | SCDMP | 364 ticks, k = 13 | fixed quad | 18-action catalogue | competent foundation gate, matched tapes | 49,213 + 1,099 across 7 sub-implementations, plus a half-built second host (TRI-UAV-SLING-CORRIDOR-36M-v1) |
| eight-context finite host | UCOPE | root + tail, k as probe period | single agent | probe / commit, k ∈ odd or even | exact oracle root vector, strict positive margin over 80 cells | 27,192 + 588 across 4 sub-implementations |
| 128-world enumeration | CBSC | exhaustive | 2 receivers | codec choices | exact protocol value 5/8 | 28,752 |

Design-principle quotes the project already holds: "A toy environment must expose the target capability rather than merely make the current mechanism easy to pass" (`ALGORITHM_PRINCIPLES.md:237`); a controlled host "establishes only controlled identifiability or learnability, not value in a natural production distribution" (same file, 189–191); the F0/F1 contract: "testbed isolates one possible additional capability".

## 2. Diagnosis

D1. One host per direction, none shared. About 135,000 lines of host and harness code for five directions against 24,000 for the entire UAV family. Every host carries its own N semantics (multiples of 3; two zones; one quad; eight contexts; two receivers), its own RNG law, its own oracle, its own validators and its own native kernel. Nothing transfers between hosts: not oracles, not competence certificates, not the untying questions. The K and N questions are being asked in five incompatible coordinate systems.

D2. Horizons too short for temporal abstraction. Horizon 12 (FRRIE), 6 decisions (VNFC), a two-stage root-and-tail decision (UCOPE): these are contextual bandits or one-shot assignment problems. They are fine for exact oracles and identifiability, and useless for any duration claim, because a skill segment of k = 13 does not fit even once. Only the GANTRY host (364 ticks, 28 segments) can carry a K-untying result.

D3. Margins below learner resolution, with exactness gates. UCOPE's margins are 0.02–0.05 and its gate is the minimum of 80 signed margins strictly above zero; SCDMP's `.3` inference demanded a distribution-free bound over the full support. Exact oracles are the right way to define competence; exact gates on sub-resolution margins are the way to guarantee failure. No host declares the learner resolution it expects (return standard error at the evaluation budget, optimizer displacement budget) or makes its margin a parameter.

D4. Structure leaks from host into learner. VNFC's B1 gain came from a hand-built coverage-aware joint decoder; FRRIE's arms differ by a projection box on 18 parameters chosen to match the host's physics. When the host and the learner package are designed together by the same hands, the control that detects hand-injected structure (a structure-blind arm; a reassociation cut) must be part of the host contract, not an afterthought.

D5. The UAV family is a transfer target being used as if it were a discovery host. It is slow at the full step, its N is frozen per scenario, its observation encoding pads to a maximum neighbour count (the N tie lives here), and its reward sprawl (seven variants) makes any cross-scenario claim confounded by the reward definition. It is, however, the only host with realistic churn events, mobility and energy, which is exactly what a C-TRANSFER claim needs.

D6. Native ports at the wrong layer. Kernels are 100× faster in C++ and full steps only 2–3×, because the Python orchestration is the bottleneck; meanwhile SCDMP's candidate-local full C++ host cost a thousand lines of C++ and tens of thousands of Python. The production policy (Python reference is a test-and-debug oracle only; fallback forbidden) is the right policy for C claims and an expensive one for B exploration.

## 3. Principles for a toy host (the ones that would have changed this wave)

P1. One mechanism, one scalar knob, one curve. The host exposes one capability and a difficulty parameter that can be swept (margin m, hazard λ, churn rate ρ, agent count N, duration k). The result of a B object is then a threshold on a curve, not a bit. A bit at one setting is what turned 562/562 positive tapes into a nonpass.

P2. Three reference policies, always: an exact or near-exact oracle (ceiling), a cheap heuristic (floor), and a structure-blind control that receives the same inputs with the mechanism removed (reassociation, derangement, permutation). Competence is measured against the ceiling; effect against the control; the floor tells you whether the host is trivial.

P3. Margin above resolution, declared. Compute the learner's resolution before freezing: return standard error at the evaluation budget (σ/√episodes), the optimizer displacement budget (learning rate × steps against the initialization scale), and the discriminator's identifiability at the window length. Set the host margin to at least three times the largest of them, and make the margin a parameter so the ladder {large, medium, small} can be run.

P4. Horizon in units of k, hazard as a parameter. Any host meant to carry a duration result needs at least ten segments at the largest k, a latent that changes with a controllable hazard λ (so the commitment-versus-reactivity trade-off is measurable), and a time-homogeneity flag for skills (so semigroup-consistent models can be tested when they should hold and falsified when they should not).

P5. N is free, roles are separate, churn is a process. No divisibility constraints on N; the number of roles K is its own parameter; churn is an event process with its own rate (leave, rejoin, terminal loss, with the process-core route's lifecycle keys), not a scripted single loss at a fixed time. Coverage redundancy N/K is then a swept quantity, and the 2K threshold from the combinatorics becomes a testable prediction.

P6. CRN per entity, matched tapes, frozen ledgers. G32 and SCDMP already do this; make it the family default. Paired comparisons at sub-1% effect sizes are impossible without it.

P7. Speed budget before native. A B host must run at roughly 10^4 steps per second per core in vectorized Python (numpy over episodes) before anyone writes C++. Native kernels are a C-claim investment.

P8. One family, many points. Build one parametric toy family and express each direction as a point in its parameter space, so that oracles, competence certificates, evaluators, and the exposure card are shared.

## 4. A concrete family: the relay corridor

One host, parameters: N agents, K roles, Z zones or contexts, horizon H, skill interval k (or a duration set), hazard λ (probability per step that the latent demand pattern switches), churn rate ρ (per-step probability of a temporary leave, with rejoin and terminal-loss sub-rates), probe cost c and probe information value v (a paid observation of the latent), margin m (the scale of the reward difference between the oracle plan and the best structure-blind plan), and a time-homogeneity flag for skills. Observations are ragged sets of entities (no padding at the host boundary; the learner pads). Rewards are per-step task returns in [0, 1] plus declared costs. RNG: per-entity streams keyed by (master seed, episode, entity id). Reference policies: oracle (has the latent), heuristic (greedy on public state), structure-blind (same as the learner with the mechanism cut). Evaluation: matched tapes, held-out N and k on both sides of the training support.

Where the five directions sit in it: FRRIE is (K = 3, λ = 0, ρ = 0, N swept both sides); VNFC is (Z = 2, ρ > 0 with one terminal loss, N swept); SCDMP is (k swept, λ > 0, order structure in the action catalogue); UCOPE is (c > 0, v as the margin, k as the probe period); CBSC is (nuisance coordinates as Z contexts). Building this once at P7 speed costs less than any one of the existing hosts and makes every first-wave result comparable.

## 5. The UAV environment

U1. Decide its role and write it down: it is the C-TRANSFER target, not a B host. Every mechanism claim is discovered on the family in section 4 and must survive in scenario 7 (energy-aware, temporary failures, charging contention), which is the closest thing the project has to a deployment distribution.

U2. Untie N at the observation boundary. Replace `max_observed_*` padded lists with entity sets and let the learner do the packing (the process-core route's ragged CSR packing already does this). Fixed N per scenario becomes a roster schedule: scenario 7's temporary failures are already churn; expose their rate as a parameter.

U3. One canonical task reward per scenario. Keep the seven variants as named ablations, but a transfer claim names one task reward and treats shaping (potential-based terms, dual-ascent costs) as part of the algorithm under test, not of the host.

U4. One entry point. Retire the direct `main.py` construction (it bypasses the array adapter) and the orphaned scenario 3; the process-core factory is the entry for everything.

U5. Do not port it to C++ now. The full-step speedup ceiling is 2–3× while Python owns lifecycle and RNG; the investment would be the SCDMP story again. Vectorize across environments in numpy, batch the lifecycle, and accept few seeds at C-TRANSFER.

U6. Determinism for paired evaluation. Per-UAV and per-cluster RNG streams (as in G32) instead of a single `RandomState`, so that two arms can be evaluated on the same mobility and line-of-sight draws.

U7. Duration hooks. The `episode_length % k == 0` constraint and the synchronous reassignment mask are the fixed-k tie; when the family result says which untying to keep, the HA-CTSE horizon window that already exists in the base route is the place to receive it.

## 6. What to write next (your design, my attack)

An architecture decision record for the relay corridor family, one page: the parameter list above with ranges, the three reference policies with their expected returns at three margins, the resolution arithmetic for the learner you intend to run first, the invariants (ragged sets at the boundary, CRN per entity, no divisibility on N, ten segments at the largest k), and the tests-as-specs that would falsify each invariant. I will review it as a hostile senior engineer before anyone writes code.


## 7. Addendum, 2026-09-02: hosts follow the research order

The owner's calibration (spec §11) puts a rung below the toy hosts discussed above. Each direction now starts from an inspiration model that needs no host at all: a drifting bandit with a commitment length for the duration direction, a variable-budget combinatorial bandit for the roster direction; both are a few dozen lines of numpy and already exist in the toy study attached to Part 1. The single-agent bridge (a moving-goal grid with age-conditioned option termination; a variable-size set-input regression with sum versus mean pooling) is the first thing that needs a host, and it should be a self-contained script, not a member of the relay-corridor family. The relay corridor is the first multi-agent host and the first place a B run happens; the UAV environment remains the C-TRANSFER target. The ADR invitation in section 6 stands, but it is now the third artefact in the sequence, after the bandit and the bridge have produced their one-sentence predictions.
