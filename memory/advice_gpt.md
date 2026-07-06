> Agreed. **The HMASD current-env baseline will no longer be treated as a blocking item.** You already have enough HMASD environment readings to support the current design progression; the marginal value of spending more GPU on this is low. What really needs to be done now is to convert the negative results of R21 into **R23 design specifications**.
>
> I suggest the current main line be:
>
> > **R23: Actionable Team Intent**
> > Not "recover sampled `Z`", but "first let sampled `Z` change the joint assignment `ξ`, then let the team discriminator reward future joint behavior".
>
> The R21 autopsy has already pinned down the root cause: the team-disc data contract is aligned, the chance accuracy is real no-signal; the forced-Z KL at both random-init and final is approximately `0.002`, proving `Z` never had actionability; `K_team=48≈episode` also degraded the two-clock experiment into roughly one Z commitment per episode. The R22 ELBO note has already concluded this as load-bearing: `I(Z; ξ | c, ω)` must be introduced, and any `q_D(Z|·)` reward must be gated by a forced-Z assignment KL floor.
>
> ---
>
> # R23 Design: Actionability First
>
> ## 0. Core Principles
>
> The wrong order of R21 was:
>
> ```text
> sample Z
> → train q_D(Z | s_next)
> → hope Z becomes meaningful
> ```
>
> The correct order for R23 is:
>
> ```text
> sample Z
> → force/verify Z changes joint assignment ξ
> → verify ξ changes behavior/effect
> → only then enable q_D(Z | future effect)
> ```
>
> Where:
>
> ```text
> c, ω = OPT recognition context
> Z    = sampled slow team intent
> ξ    = joint assignment structure
>        includes skill logits/probs, duration logits/probs, edit probs,
>        edited subset, roster-conditioned AR assignment
> z_i  = individual skill
> a_i  = low-level action
> ```
>
> OPT remains merely the interaction context. In the OPT paper, it decomposes entity interactions into sparse/diverse prototypes and then recombines them with aggregation weights `ω` into a compact interaction pattern; this supports using `c, ω` as a recognition substrate, not a team option.
>
> `Z` works in HMASD because it sits at the front of the high-level autoregressive chain, and subsequent `z_i` depend on `Z` and the skills of previous agents; meanwhile, `q_D(Z|s)` and `q_d(z_i|o_i,Z)` generate intrinsic reward for the discoverer. R23 must retain this **causal order**, not simply feed the sampled label back.
>
> ---
>
> # PR-1: Two-clock ELBO / R23 objective note
>
> Write the theoretical design first, not the training code. The goal is to turn R23 into a reviewable objective, not another mechanism stack.
>
> ## 1. PGM Variables
>
> ```text
> c_t, ω_t  = OPT recognition substrate
> 
> Z_m       = slow sampled team intent
> 
> ξ_m       = joint assignment / response structure
>             ξ_m includes:
>               edited subset E_m
>               AR order
>               skill assignment distribution π_z
>               duration / edit distribution
>               roster-conditioned assignment pattern
> 
> z_{i,r}   = agent i's active individual skill at renewal r
> 
> a_{i,t}   = low-level primitive action
> 
> O_t       = optimality variable from environment reward
> ```
>
> ## 2. Factorization
>
> ```text
> p(τ, Z, ξ, z, a)
> =
> p(env)
> ∏_m π_Z(Z_m | c_m, ω_m)
> ∏_m π_ξ(ξ_m | Z_m, c_m, ω_m)
> ∏_{i,r} π_z(z_{i,r} | ξ_m, Z_m, c_r, ω_r, o_{i,r}, roster_r)
> ∏_{i,t} π_l(a_{i,t} | o_{i,t}, z_{i,active(t)})
> ```
>
> The key is the explicit inclusion of `ξ`. What R21 lacked was not `q_D`, but this intermediate causal chain:
>
> ```text
> Z -> ξ
> ```
>
> ## 3. Candidate Objective Terms
>
> The R23 objective should at least review these terms:
>
> ```text
> J =
>   E[ external return ]
> 
> + λ_A * I(Z ; ξ | c, ω)
> 
> + λ_D * I(Z ; future_joint_effect | c, ω)
>         gated by actionability
> 
> + λ_d * Σ_i I(z_i ; local_effect_i | Z, ξ, c, ω)
> 
> + entropy constraints:
>     H(Z | c,ω)
>     H(ξ | Z,c,ω)
>     H(z_i | ξ,Z,c,ω)
>     H(duration/edit)
>     H(action)
> ```
>
> The most critical of these is:
>
> ```text
> I(Z ; ξ | c,ω)
> ```
>
> It is the load-bearing term of R23.
>
> `q_D(Z|future)` can only follow, because R21 has already demonstrated: if behavior does not depend on `Z`, the team discriminator can only read chance.
>
> ---
>
> # R23 Mechanism Design
>
> ## 1. Static Architecture Capacity Gate
>
> Don't train first. Just test whether the architecture has the capacity for `Z` to influence the assignment.
>
> ### Test
>
> Fix a batch:
>
> ```text
> same c, ω, obs, roster, ages
> force Z = 0..5
> measure:
>   π_z
>   π_duration
>   π_edit
>   joint assignment ξ
> ```
>
> ### Metrics
>
> ```text
> forced_Z_skill_KL_mean
> forced_Z_skill_TV_mean
> forced_Z_duration_KL_mean
> forced_Z_edit_KL_mean
> forced_Z_joint_assignment_distance
> ```
>
> ### Gate
>
> The decorative band of R21 was:
>
> ```text
> forced_Z_skill_KL ≈ 0.002
> ```
>
> The R23 capacity gate can initially be set as:
>
> ```text
> PASS:
>   forced_Z_skill_KL_mean >= 0.02
>   or at least 10x R21 random-init band
> 
> and:
>   effect visible in at least one of skill / duration / edit heads
> 
> FAIL:
>   forced_Z KL still ~0.002
> ```
>
> This gate is **random-init / static**.
> If it fails at random init, the problem is not the objective, but the architecture's connection gain being too weak.
>
> ## 2. Architecture Correction
>
> If the gate fails, first fix the high-level assignment path, don't add losses.
>
> Suggestion:
>
> ```text
> A. Z as true AR first-token
>    Don't just use a weak team_vector side input.
>    The skill decoder / AR assignment takes the Z embedding as the first token.
> 
> B. Z-FiLM on assignment heads
>    Add Z-conditioned FiLM or affine modulation to skill / duration / edit heads.
> 
> C. Direct residual logit path
>    logits_z_i += W_Z e_Z
>    logits_duration_i += U_Z e_Z
>    logits_edit_i += V_Z e_Z
>    But keep coefficients/initialization small to avoid full domination by Z from the start.
> 
> D. Do not alter low-level actor input.
>    The low level remains:
>      a_i ~ π_l(a_i | o_i, z_i)
> 
> E. Match S-base path as much as possible.
>    Don't drastically replace the assignment path like R21 did when introducing team-intent.
>    Otherwise, task regression will be confounded by policy-path issues.
> ```
>
> Only enter objective training when the static forced-Z KL is clearly above the decorative band.
>
> ---
>
> # 3. Actionability Objective
>
> ## 3.1 Soft Decision-Level Usage Loss
>
> The first version can use a differentiable MI starter:
>
> ```text
> L_action =
>   - λ_skill * I(Z ; π_z decisions | c,ω)
>   - λ_dur   * I(Z ; π_duration decisions | c,ω)
>   - λ_edit  * I(Z ; π_edit decisions | c,ω)
> ```
>
> Estimate by enumerating `Z`:
>
> ```text
> I_Z_skill =
>   H(mean_Z π_z(. | c,ω,Z))
>   - mean_Z H(π_z(. | c,ω,Z))
> ```
>
> Similarly:
>
> ```text
> I_Z_duration
> I_Z_edit
> ```
>
> This is not the final intrinsic reward, just a way to give `Z` actionability first. It should be:
>
> ```text
> small coef
> warmup only
> anneal after forced_Z_KL passes floor
> high-level only
> no communication fields
> no low-level actor input change
> ```
>
> ## 3.2 Assignment Residual Discriminator
>
> A form closer to the ELBO:
>
> ```text
> R_action =
>     log q_A(Z | ξ, c,ω)
>   - log q_prior(Z | c,ω)
> ```
>
> Here `ξ` can include:
>
> ```text
> soft skill assignment distribution
> duration distribution
> edit distribution
> executed skill pattern
> edited subset
> roster-conditioned AR context
> ```
>
> Usage:
>
> ```text
> First, use it as a reward-off diagnostic.
> Then a small high-level auxiliary reward/loss.
> ```
>
> The success criterion is not high `q_A` accuracy, but:
>
> ```text
> forced_Z_assignment_KL increases
> ξ changes with Z
> task health does not collapse
> ```
>
> ---
>
> # 4. Team Discriminator Gate
>
> Only turn on the team discriminator after actionability is passed.
>
> ```text
> R_team =
>     log q_D(Z | future_joint_effect, c,ω)
>   - log q_prior(Z | c,ω)
> ```
>
> Gate:
>
> ```text
> forced_Z_assignment_KL >= floor
> and
> q_A_residual_gain > 0
> ```
>
> Otherwise:
>
> ```text
> team_disc_reward = 0
> ```
>
> This is a hard rule. R21 proved that ungated `q_D` is decorative.
>
> ---
>
> # 5. Individual Skill Term
>
> R23 should not focus only on team intent. It must retain the individual discoverer pressure, but conditional on `Z` and `ξ`:
>
> ```text
> R_ind_i =
>     log q_d(z_i | local_effect_i, Z, ξ, c,ω)
>   - log q_prior(z_i | Z, ξ, c,ω)
> ```
>
> This corresponds to HMASD's `q_d(z_i | o_i, Z)`, but in a process/effect version. In the HMASD paper, the individual discriminator is explicitly conditioned on the team skill `Z`; this is its key difference from pure individual skill discovery.
>
> First version: keep reward-off for probing:
>
> ```text
> does z_i produce local effect beyond Z/ξ/context prior?
> ```
>
> Don't add low-level reward at the beginning.
>
> ---
>
> # K / Duration Design
>
> The first version of R23 must avoid R21's `K≈episode` confound.
>
> ## Choice 1: Short duration + short K, for testing actionability
>
> Recommended:
>
> ```text
> episode ≈ 50 high-level checks
> K_team = 8
> duration candidates = {1, 2, 3, 4}
> ```
>
> This results in:
>
> ```text
> K_team ≈ 2 * max_duration
> ~6 Z periods per episode
> team discriminator has within-episode variation
> long-duration truncation is no longer approximately tautological
> ```
>
> This is not a decoupled-lifetime thesis conclusion. It is merely a test for the R23 actionability mechanism. This must be stated clearly:
>
> ```text
> Choice-1 tests whether actionable Z can be learned.
> It does not prove full asynchronous long-lifetime contribution.
> ```
>
> ## Choice 2: True parent-child decoupling, deferred
>
> Do this later:
>
> ```text
> Z boundary does not force termination of active z_i
> old z_i may continue under birth_Z until natural expiry
> new renewals dock to current Z
> ```
>
> This is the complete two-clock parent-child lifetime. But it's complex; don't implement it yet. R23 must first prove that `Z` is actionable.
>
> ---
>
> # Experiment Matrix
>
> ## Stage R23-0: Static Capacity Gate
>
> ```text
> No training.
> Random-init and S-base checkpoint.
> Force Z=0..5.
> Measure assignment KL/TV/distance.
> ```
>
> Only proceed to R23 training if this passes.
>
> ## Stage R23-1: Actionability-Only
>
> ```text
> Architecture-capacity-fixed
> + L_action or R_action
> - no q_D reward
> - no communication reward
> - short K / short duration Choice-1
> ```
>
> Goal:
>
> ```text
> Does Z start controlling ξ?
> ```
>
> Metrics:
>
> ```text
> forced_Z_assignment_KL ↑
> forced_Z_duration_KL ↑ or edit_KL ↑
> q_A_residual_gain > 0
> Z_usage_entropy healthy
> task metrics not catastrophic
> ```
>
> Failure:
>
> ```text
> forced_Z_KL unchanged:
>   objective too weak or architecture still weak
> 
> forced_Z_KL ↑ but task collapse:
>   actionability creates arbitrary churn; reduce/anneal coefficient
> ```
>
> ## Stage R23-2: Team-Disc Probe
>
> ```text
> + q_D diagnostic only
> team_disc_reward = off
> ```
>
> Goal:
>
> ```text
> Now that Z changes ξ, can the future state/effect recover Z?
> ```
>
> Metrics:
>
> ```text
> team_disc_acc > chance but not leak-saturating
> team_disc_residual_gain > 0
> team_disc_prior_entropy healthy
> ```
>
> Failure:
>
> ```text
> forced_Z_KL > 0 but team_disc chance:
>   ξ changes but low-level/joint behavior hasn't changed enough
> ```
>
> ## Stage R23-3: Team-Disc Reward
>
> ```text
> + q_D reward
> coef small, e.g., 0.02 or 0.05
> gated by forced_Z_KL floor
> ```
>
> Goal:
>
> ```text
> Recover HMASD-style team exploration pressure.
> ```
>
> Metrics:
>
> ```text
> reward / coverage / QoS / throughput ↑
> zero_throughput ↓
> coverage_eq1_step_frac ↑
> reward variance ↓
> forced_Z_KL stays nonzero
> team_disc_residual stays positive
> ```
>
> ## Stage R23-4: Individual q_d Process Term
>
> ```text
> + q_d(z_i | local_effect_i, Z, ξ, c,ω)
> - prior-corrected
> - shortcut-controlled
> ```
>
> Goal:
>
> ```text
> Let individual skills differentiate under actionable team intent.
> ```
>
> ---
>
> # What NOT to Do Now
>
> Explicitly stop:
>
> ```text
> HMASD current-env rerun
> R21 seed2
> R21 sweep
> R19 sweep
> R12 hazard / DADS
> target kappa*
> g-revival
> entropy auto-temperature implementation
> new topology-role reward
> ```
>
> Regarding HMASD: you've already stated that the existing tests are sufficient, so don't waste more time. Only add one sanity/appendix run for the final paper, not as a current blocking item.
>
> ---
>
> # Next Design Prompt for Claude
>
> You can directly send this:
>
> ```text
> We accept the R21 autopsy. Do not run more HMASD baselines, R21 seeds, or R21 sweeps.
> 
> The next design is R23: Actionable Team Intent.
> 
> Core correction:
> R21 sampled Z failed because Z was never actionable. Forced-Z KL was ~0.002 at random init and final. Team-disc labels were aligned, so chance q_D was genuine no-signal. Therefore q_D(Z|future) cannot be used to make Z meaningful; Z must first change joint assignment ξ.
> 
> Task 1: Draft PR-1 R22/R23 design note.
> Variables:
>   c, omega = OPT recognition context
>   Z = slow sampled team intent
>   xi = joint assignment / roster / skill-duration-edit structure
>   z_i = individual skill
>   a_i = primitive action
> 
> Main objective questions:
>   Is I(Z; xi | c, omega) required?
>   When is q_D(Z | future effect, c,omega) legal?
>   How does q_d(z_i | local effect, Z, xi, c,omega) enter?
>   Which entropy terms are derived constraints vs stabilizers?
> 
> Task 2: Specify R23 static architecture capacity gate.
> No training.
> Force Z=0..5 on a fixed batch and measure:
>   forced_Z_skill_KL / TV
>   forced_Z_duration_KL / TV
>   forced_Z_edit_KL / TV
>   forced_Z_joint_assignment_distance
> PASS if forced_Z_skill_KL >= 0.02 or at least 10x the R21 decorative band.
> FAIL means architecture, not objective.
> 
> Task 3: Propose architecture changes if gate fails:
>   Z as true AR first token;
>   Z-FiLM on skill/duration/edit heads;
>   direct small residual Z logit path;
>   preserve low-level actor input a_i ~ pi_l(o_i,z_i);
>   avoid replacing S-base selection path unnecessarily.
> 
> Task 4: Specify R23 actionability objective.
> Option A:
>   differentiable I(Z; skill/duration/edit decisions | c,omega) by enumerating Z.
> Option B:
>   residual q_A:
>     log q_A(Z | xi,c,omega) - log q_prior(Z | c,omega).
> Use small warmup coefficient and anneal after actionability passes.
> No communication-specific reward.
> 
> Task 5: Specify q_D gate.
> q_D(Z|future) reward is forbidden until:
>   forced_Z_assignment_KL >= floor
>   and q_A_residual_gain > 0.
> Then q_D can be tested probe-off first, reward-on later.
> 
> Task 6: Specify Choice-1 timing for clean mechanism test:
>   K_team=8 high-level checks
>   duration candidates {1,2,3,4}
> This tests actionability, not full decoupled-lifetime thesis.
> Do not implement true parent-child lifetime yet.
> 
> Do not modify algorithm code yet unless writing a diagnostic-only capacity-gate script.
> No new training runs.
> ```
>
> ---
>
> # Final Sentence
>
> What needs to be done next is not to continue proving HMASD, nor to continue fixing R21, but to design the **R23 actionability-first objective**:
>
> ```text
> Z must first control ξ.
> ξ must then control joint behavior.
> Only then can q_D recover Z and provide HMASD-style team exploration pressure.
> ```
>
> The value of R21's failure lies here: it tells us that **the team discriminator is not an initiator, but an amplifier**. If the `Z -> ξ` chain is not established first, even the strongest `q_D` can only read chance.
