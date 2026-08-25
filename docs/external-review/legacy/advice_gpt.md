> response:
>
> I will classify the R23 result as:1 I agree with your current assessment and will solidify it as the new **R23 interim conclusion**:
>
> > **R23-0 is real progress: `Z -> ξ` static/architectural actionability has been fixed.
> > But R23 is not yet successful: the half-chain `ξ -> joint behavior/effect -> q_D` remains broken.**
>
> This is much better than R21. The R21 autopsy already proved that at that time `forced-Z KL` was approximately `0.002` at both random-init and final, meaning it was never actionable; R23 now raises the KL to `0.04–0.08`, showing that `Z` can indeed influence the assignment distribution. However, the core chain from R22 is:
>
> ```text
> Z -> ξ -> joint behavior / future effect -> q_D can recover Z
> ```
>
> R23 currently only passes the first segment. R22 had already set `I(Z; ξ | c,ω)` as load-bearing, and required that `q_D(Z|·)` reward must be gated behind a forced-Z assignment KL floor; now the gate mechanics are correct, but `q_D` cannot read downstream behavioral signals.
>
> ---
>
> # Current Status Determination
>
> ```text
> R23-0 architecture capacity: PASS
> R23-1 g-info objective: FAIL / null
> R23-2 q_D team discriminator: FAIL
> R23-3 q_D gate mechanics: PASS, but reward signal ~0
> Task parity: untouched
> ```
>
> I will write this result as:
>
> > **Blocker moved from "Z cannot move ξ" to "ξ does not yet induce recoverable joint behavior."**
>
> This sentence is important because it prevents us from mistakenly re-fixing the R21 problem. The issue now is not simply to make `Z` more "able to move the assignment"; rather, we must ask:
>
> ```text
> What ξ did Z change?
> Is this ξ actually executed?
> Does the executed z_i change low-level behavior?
> Does joint behavior leave a recoverable team signature at the appropriate time scale?
> ```
>
> ---
>
> # What NOT to Do Now
>
> I agree with stopping the following items:
>
> ```text
> Do not perform g-info coef sweep
> Do not enable q_D reward
> Do not run 960k long runs
> Do not open new kappa*/hazard/DADS branches
> Do not turn communication metrics into intrinsic reward
> Do not re-treat HMASD baseline as the current blocker
> ```
>
> Regarding HMASD: since you already have sufficient environment tests, I agree to stop treating the HMASD current-env rerun as a current blocking item. It can serve as a paper/appendix sanity check later and should not occupy the current research loop. The current implementation plan still uses S7-S1 parity with HMASD as a benchmark gate, but this does not mean each round of mechanism design must first repeat HMASD.
>
> ---
>
> # Next Step 1: First Perform g-info Gradient Audit
>
> You have already confirmed at the curve level:
>
> ```text
> architecture KL stable from first update
> g-info flat
> team_disc always chance
> ```
>
> Therefore, the shortest path now is not coefficient tuning, but confirming whether the g-info objective can actually move parameters.
>
> ## Questions the Gradient Audit Must Answer
>
> ```text
> Does g-info loss have gradients flowing into:
>   Z embedding
>   skill assignment head
>   duration head
>   edit head
>   shared high encoder
> ```
>
> Suggested tracking:
>
> ```text
> grad_norm_ginfo_to_Z_embedding
> grad_norm_ginfo_to_skill_head
> grad_norm_ginfo_to_duration_head
> grad_norm_ginfo_to_edit_head
> grad_norm_ginfo_to_high_encoder
> 
> ratio_ginfo_grad_to_ppo_grad_skill
> ratio_ginfo_grad_to_ppo_grad_duration
> ratio_ginfo_grad_to_ppo_grad_edit
> 
> ginfo_loss_raw
> ginfo_loss_scaled
> ppo_policy_loss
> entropy_loss
> ```
>
> ## Interpretation Rules
>
> ```text
> grad ≈ 0:
>   Implementation / detach / enumeration path broken.
>   Fix wiring first, do not do coef sweep.
> 
> grad non-zero but 100x~1000x smaller than PPO:
>   Scale issue.
>   Can consider increasing coef or rescaling loss, but only with gradient evidence.
> 
> grad normal but MI doesn't move:
>   Current g-info form is unsuitable.
>   Switch to Option-B q_A residual.
> 
> grad normal and MI rises but task collapses:
>   Actionability objective creates arbitrary churn.
>   Needs annealing / debiased usefulness / stronger constraints.
> ```
>
> This audit should be a short script / single batch backward pass, no long training required.
>
> ---
>
> # Next Step 2: Main Candidate Switches to Option-B `q_A` Residual
>
> I agree with your "accept but modify": `q_A` is a new module that needs authorization and must undergo duplicate-count audit in PR-1. However, algorithmically, it aligns better with R22's core term:
>
> ```text
> I(Z ; ξ | c,ω)
> ```
>
> The current g-info is a distribution-level usage regularizer; `q_A` more directly asks:
>
> ```text
> Given the current OPT context c,ω,
> does the joint assignment ξ contain additional information that can recover Z?
> ```
>
> This is precisely the breaking point of R21/R23.
>
> ---
>
> ## q_A Residual Definition
>
> Define:
>
> ```text
> ξ = joint assignment / roster / duration-edit structure
> ```
>
> The first version of `ξ` should include two sets of information:
>
> ```text
> soft ξ:
>   skill logits/probs for all agents
>   duration logits/probs
>   edit probabilities
> 
> executed ξ:
>   sampled z_i ids
>   sampled duration ids
>   edit mask
>   active roster summary
>   agent mask / age buckets
> ```
>
> Training:
>
> ```text
> q_A_full(Z | ξ, c,ω)
> q_A_prior(Z | c,ω)
> ```
>
> Residual:
>
> ```text
> R_A =
>     log q_A_full(Z | ξ, c,ω)
>   - log q_A_prior(Z | c,ω)
> ```
>
> First reward-off:
>
> ```text
> q_A_full_acc
> q_A_prior_acc
> q_A_residual_gain
> q_A_full_minus_prior
> q_A_best_shortcut_name
> ```
>
> Then small-coefficient reward/auxiliary:
>
> ```text
> R_action = clip(R_A, -1, 1)
> ```
>
> Placement:
>
> ```text
> high-level assignment path only
> not low-level reward
> not environment reward
> not communication-specific reward
> ```
>
> ## Hard Gate for q_A
>
> ```text
> PASS:
>   q_A_full beats q_A_prior by stable margin
>   q_A_residual_gain > 0
>   forced_Z_assignment_KL remains non-decorative
>   Z usage does not collapse
> 
> FAIL:
>   q_A_full ≈ q_A_prior
>   or q_A only reads duration/edit shortcut
>   or q_A raises KL but causes task/entropy collapse
> ```
>
> If q_A reward is effective, it indicates:
>
> ```text
> Z -> ξ
> ```
>
> Has moved from "architecture capacity" to "learnable objective."
>
> ---
>
> # Next Step 3: q_D Effect Target / Timescale Audit
>
> The current `team_disc_acc≈chance` should not be directly interpreted as "q_D is useless." More precisely:
>
> ```text
> The current q_D target / timescale cannot see the Z-induced joint effect.
> ```
>
> In HMASD, `q_D(Z|s)` reads global state after fixed-k synchronous skill execution; under HA-CTSE's two-clock/async structure, the effect of `Z` may not manifest in a single `s_next` step. HMASD's team discriminator was originally designed to reward team access to differentiable global states, while the individual discriminator conditions on `Z`; this mechanism is inherently synchronous under fixed-k. HA-CTSE needs to re-identify the observation window for team effects.
>
> Suggest comparing four types of targets, all reward-off:
>
> ```text
> Target A:
>   q_D(Z | s_next)
> 
> Target B:
>   q_D(Z | joint_action_summary over H)
> 
> Target C:
>   q_D(Z | joint_effect_window over H)
> 
> Target D:
>   q_D(Z | ΔOPT compact / Δω over H)
> ```
>
> H:
>
> ```text
> H ∈ {10, 20, 50}
> ```
>
> `Δω` is particularly worth trying because OPT's aggregation weights are reconstruction weights for interaction prototypes. OPT obtains compact interaction patterns through sparse prototypes + learnable aggregation weights; if `Z` truly changes team interaction mode, `Δω` / prototype-response trajectory may be more sensitive than raw `s_next`.
>
> ## Criteria for q_D Target Audit
>
> ```text
> PASS:
>   Some target's q_D_acc > chance
>   And residual beats context / prior / duration shortcuts
>   And it's not instant leak saturation
> 
> FAIL:
>   All targets are chance
>   -> ξ changes logits but not executed joint behavior,
>      or low-level z_i behavior still not differentiated.
> ```
>
> Note: Even if a target passes, it is only a probe. Do not immediately enable reward.
>
> ---
>
> # Next Round Mechanism Matrix: 320k is Sufficient, Not 960k
>
> I suggest the next round only runs the mechanism matrix, not a task-parity long run.
>
> ## Arm 0: Arch-only Control
>
> ```text
> R23 architecture fix
> z_assignment_residual_gain=0.5
> no g-info objective
> no q_A reward
> q_D reward off
> ```
>
> Purpose:
>
> ```text
> Confirm architecture KL is stable,
> Serve as baseline for q_A / q_D target audit.
> ```
>
> ## Arm 1: g-info Gradient Audit / Maybe No Training
>
> ```text
> single-batch backward audit
> or very short smoke
> ```
>
> Purpose:
>
> ```text
> Determine whether current g-info failure is wiring / scale / form failure.
> ```
>
> If the gradient audit is sufficient, Arm 1 may not need training.
>
> ## Arm 2: q_A Probe Reward-off
>
> ```text
> arch + q_A heads
> reward off
> ```
>
> Purpose:
>
> ```text
> Can Z be prior-corrected recovered from ξ?
> ```
>
> ## Arm 3: q_A Reward Small
>
> ```text
> arch + q_A residual reward/aux
> q_D reward off
> coef = 0.02 or 0.05
> warmup
> clip
> ```
>
> Purpose:
>
> ```text
> Can actionability be learned/stabilized, not just rely on static architecture KL?
> ```
>
> ## Arm 4: q_D Target Audit
>
> ```text
> best q_A checkpoint or arch-only checkpoint
> compare s_next / joint_action / joint_effect / Δω
> H={10,20,50}
> reward off
> ```
>
> Purpose:
>
> ```text
> Find the recoverable observation space and timescale for ξ -> joint effect.
> ```
>
> Only when Arm 4 passes, consider:
>
> ```text
> q_D reward-on
> ```
>
> ---
>
> # What PR-1 Should Write: Not Generic ELBO, But Duplicate-Count Audit
>
> You said "q_A is a new module, must undergo duplicate-count audit in PR-1," and this is very correct.
>
> PR-1 should now clearly define three types of terms:
>
> ```text
> 1. Actionability:
>    I(Z ; ξ | c,ω)
> 
> 2. Team-effect:
>    I(Z ; future_joint_effect | c,ω)
> 
> 3. Individual process:
>    I(z_i ; local_effect_i | Z,ξ,c,ω)
> ```
>
> Then answer:
>
> ```text
> Do q_A and q_D double-count?
> ```
>
> My current answer:
>
> ```text
> They do not double-count, provided the division of labor is clear:
> 
> q_A:
>   Does Z change high-level assignment ξ?
>   This is upstream actionability.
> 
> q_D:
>   Does Z, through ξ, change future joint behavior/effect?
>   This is downstream behavioral signature.
> 
> q_d:
>   Does individual z_i, under Z/ξ context, induce local process effect?
> ```
>
> If `q_D` directly reads `ξ` or assignment labels, it double-counts with `q_A`.
> If `q_D` only reads future behavior/effect/window/Δω, its division of labor differs from `q_A`.
>
> Therefore, PR-1 should state clearly:
>
> ```text
> q_A may read ξ.
> q_D must not read ξ as a label shortcut if used as a team-effect discriminator.
> q_D can condition on context c,ω, but must recover Z from future effect.
> ```
>
> The R22 note has already written "team discriminator downstream-useless until behavior depends on Z" as a hard conclusion, so q_A must come before q_D.
>
> ---
>
> # Should Principles Be Updated Now?
>
> I agree not to make major changes to the principles for now. A single 320k seed is insufficient to rewrite the contract with q_A as the main line. However, an interim ledger should be kept:
>
> ```text
> R23 interim:
>   architecture capacity PASS
>   g-info objective FAIL/null
>   q_D effect signature FAIL
>   next: g-info gradient audit + q_A residual probe + q_D effect target audit
> ```
>
> This means:
>
> ```text
> ExpRecord / ATTENTION_POINTER / cross_validation updates are sufficient.
> ALGORITHM_PRINCIPLES remain largely unchanged for now.
> ```
>
> Wait until the q_A probe or q_D target audit yields results before modifying principles.
>
> ---
>
> # Next Instruction for Claude / Codex
>
> Can be sent directly as:
>
> ```text
> Accepted: R23 is mixed. Architecture capacity passed, but g-info and q_D failed.
> 
> Do not run coefficient sweeps or long runs.
> 
> Next tasks:
> 
> 1. Plot only decision-critical curves:
>    - forced_Z_skill_KL / z_assignment_itv
>    - g_info_mi_skill/duration/edit
>    - g_info_loss raw and scaled
>    - team_disc_acc / residual / prior_entropy
>    - coverage_eq1 / coverage / zero_throughput
> 
> 2. Run g-info gradient audit:
>    measure grad_norm from g-info loss to:
>      Z embedding
>      skill head
>      duration head
>      edit head
>      shared high encoder
>    compare to PPO grad norms.
>    Decide: wiring vs scale vs objective-form failure.
> 
> 3. Draft Option-B q_A residual module spec:
>    q_A_full(Z | ξ,c,ω) - q_A_prior(Z | c,ω)
>    ξ includes soft and executed assignment structure.
>    Probe reward-off first.
>    Reward/aux only if q_A_residual_gain > 0.
> 
> 4. Draft q_D target/timescale audit:
>    compare q_D(Z | s_next),
>            q_D(Z | joint_action_summary_H),
>            q_D(Z | joint_effect_window_H),
>            q_D(Z | Δω_H)
>    for H={10,20,50}, reward-off only.
> 
> 5. Prepare 320k mechanism matrix:
>    Arm0 arch-only
>    Arm1 q_A probe
>    Arm2 q_A reward small
>    Arm3 q_D target audit
>    No q_D reward-on unless q_D target residual passes.
> 
> Do not modify algorithm principles yet except recording interim result.
> Do not use communication metrics as intrinsic reward.
> ```
>
> ---
>
> # Final Judgment
>
> The research path for R23 is now clear:
>
> ```text
> R21 failure:
>   Z could not move ξ.
> 
> R23-0 fixed:
>   Z can move ξ.
> 
> Current failure:
>   ξ does not yet become recoverable joint behavior.
> 
> Next required mechanism:
>   q_A to make Z→ξ learnable and stable;
>   q_D target audit to find whether ξ→joint effect exists and at what timescale.
> ```
>
> So my recommendation is:
>
> > **First perform the g-info gradient audit; then switch the main line to `q_A` residual actionability; simultaneously reward-off audit q_D's effect target and timescale. Do not treat q_D as the initiator anymore; it can only serve as an amplifier once `Z -> ξ -> behavior` is established.**
>
> > **R23-0 resolves the R21 issue of "Z being completely inactionable", but R23 has not yet solved the "whether Z-induced assignments become recoverable joint behavior" problem.**
> > The current blocker has shifted from `Z -> ξ` to `ξ -> joint effect`, while the `g-info / MI objective` itself has not yet provided meaningful learning pressure.
>
> This is not an R21-style total mechanism failure. R23 shows real progress: `z_assignment_residual_gain=0.5` raised the forced-Z KL from R21's decorative band of `~0.002` to `0.04–0.08`, demonstrating the architecture's capacity gate has been passed. The R21 autopsy explicitly noted that `Z` only had about `0.002` KL in both random-init and final states, meaning it was "never actionable"; R23 has fixed this part.
>
> But what R22's ELBO truly requires is the chain:
>
> ```text
> Z -> ξ -> joint behavior / future effect -> q_D can recover Z
> ```
>
> Only the first segment is currently proven:
>
> ```text
> Z -> ξ
> ```
>
> The latter two segments still fail. R22 had already upgraded `I(Z; ξ | c,ω)` to load-bearing status and explicitly stated that `q_D(Z|·)` reward must be gated behind a forced-Z assignment KL floor; R23 results show the gate mechanism is correct, but the downstream `q_D` still lacks an amplifiable signal.
>
> ---
>
> ## My Suggested Next Step: Diagnostic Plots + Gradient Audit First, Then Decide on Strong Objective
>
> Claude asked whether you want to draw raw MI/disc curves or draft a stronger objective. My suggestion is:
>
> ```text
> Draw curves first, but only the decision-critical few;
> Simultaneously perform gradient audit of the g-info/actionability objective;
> Then prioritize designing Option-B q_A residual, rather than simply sweeping the coef from 0.02 upward.
> ```
>
> The reason is that the current `objective-ON` MI is actually lower than `objective-OFF`:
>
> ```text
> ON:  0.012
> OFF: 0.024
> ```
>
> This is not the typical "coef slightly too small" phenomenon; it looks more like:
>
> ```text
> 1. The objective scale is too small;
> 2. The objective sign / implementation path might be weak;
> 3. The loss is not effectively entering the assignment head;
> 4. Entropy / PPO loss is drowning it out;
> 5. This MI objective itself is unsuitable for the current logits/ξ representation.
> ```
>
> So don't start with a large coefficient sweep first. Confirm whether it's actually backpropagating.
>
> ---
>
> # 1. Immediate Plots to Draw: Only 6 Lines, Don't Overwhelm Decisions
>
> Ask Claude/Codex to pull raw curves, but only these:
>
> ```text
> 1. forced_Z_skill_KL / z_assignment_itv
> 2. g_info_mi_skill / duration / edit
> 3. g_info_loss_raw and coef-scaled loss
> 4. team_disc_acc
> 5. team_disc_residual / team_disc_prior_entropy
> 6. task coverage_eq1_step_frac / coverage / zero_throughput
> ```
>
> The purpose is not to beautify the report, but to confirm three facts:
>
> ```text
> A. Does architecture-induced KL exist and stabilize from early training;
> B. Is the g-info objective completely flat;
> C. Is team_disc always at chance, or was it briefly above chance then disappeared.
> ```
>
> If `team_disc_acc` is at chance throughout and prior entropy is pinned at ln6, don't enable `q_D` reward. The R21 autopsy already proved the data contract is fine; the chance reading is a genuine no-signal, not a label bug.
>
> ---
>
> # 2. Gradient Audit is Mandatory: Is R23-1's Failure Due to Scale or Wiring
>
> The current `g-info loss ≈ -2e-4` is too small. The next question to ask:
>
> ```text
> Does this loss actually produce gradients for Z embedding / assignment heads?
> ```
>
> Have Codex run a small backward audit, no need for a long training run.
>
> Record:
>
> ```text
> grad_norm_g_info_to_Z_embedding
> grad_norm_g_info_to_skill_head
> grad_norm_g_info_to_duration_head
> grad_norm_g_info_to_edit_head
> grad_norm_g_info_to_shared_high_encoder
> ratio_g_info_grad_to_ppo_grad
> ratio_g_info_loss_to_policy_loss
> ```
>
> Explanation:
>
> ```text
> grad ≈ 0:
>   There's a problem with the objective wiring / detach / enumeration path.
>   Fix the implementation first, don't sweep coef.
> 
> grad non-zero but 1000x smaller than PPO:
>   Scale issue. Consider coef or redefine loss.
> 
> grad non-zero and not small, but MI doesn't move:
>   The objective form is unsuitable, or is canceled out by entropy / PPO / clipping.
>   Switch to Option-B q_A residual.
> ```
>
> This audit is more valuable than directly adjusting `coef=0.05/0.1`.
>
> ---
>
> # 3. Not Recommended to Continue Using Current g-info as Primary Actionability Objective
>
> The problem with the current g-info is: it only requires information differences in decision distributions under different `Z`s, but it doesn't guarantee that executed `ξ` forms stable, learnable joint assignment codes. It's more like a smooth usage regularizer.
>
> R23 now needs a harder objective:
>
> ```text
> Z should be recoverable from executed joint assignment ξ,
> beyond context prior.
> ```
>
> That is, from R22:
>
> ```text
> I(Z ; ξ | c,ω)
> ```
>
> So I suggest the next main objective should be **Option-B residual q_A**.
>
> ---
>
> # 4. Option-B q_A Residual: Next Version of Actionability Objective
>
> Definition:
>
> ```text
> ξ = joint assignment structure
> ```
>
> The first version of `ξ` shouldn't be too complex; I suggest including:
>
> ```text
> executed skill ids z_1:n
> duration ids / remaining bucket
> edit mask
> possibly soft skill logits/probs
> agent mask / roster summary
> ```
>
> Train two heads:
>
> ```text
> q_A_full(Z | ξ, c,ω)
> q_A_prior(Z | c,ω)
> ```
>
> Residual:
>
> ```text
> R_A =
>     log q_A_full(Z | ξ, c,ω)
>   - log q_A_prior(Z | c,ω)
> ```
>
> This directly corresponds to R22's cross-layer actionability term `I(Z; ξ | c,ω)`.
>
> ## Phase 1: Reward-off q_A Probe
>
> First, don't enable reward, just look at:
>
> ```text
> q_A_full_acc
> q_A_prior_acc
> q_A_residual_gain
> q_A_full_minus_prior
> q_A_full_minus_duration
> q_A_best_shortcut_name
> ```
>
> Expectation:
>
> ```text
> Since R23-0's forced-Z KL has already passed,
> q_A should be able to recover Z from ξ.
> ```
>
> If even q_A fails, it means that although the KL metric is high, the executed ξ information is still too weak / too noisy / hasn't been discretized into stable joint patterns.
>
> ## Phase 2: q_A Reward / Auxiliary
>
> Only after the q_A probe passes, inject with small coefficient:
>
> ```text
> R_action = clip(R_A, [-1, 1])
> ```
>
> Placement:
>
> ```text
> high-level assignment reward / auxiliary
> not low-level reward
> not environment reward
> ```
>
> Initial suggestions:
>
> ```text
> coef = 0.02 or 0.05
> warmup = 20k
> clip = 1.0
> prior-corrected
> reward ratio logging
> q_D reward still off
> ```
>
> The success criterion is not that the task immediately improves, but:
>
> ```text
> forced_Z_assignment_KL ↑ or stays robust
> q_A_residual_gain ↑
> Z_usage_entropy not collapsed
> task health not catastrophically worse
> ```
>
> ---
>
> # 5. Don't Tune q_D Coef Now; Change Effect Target / Timescale
>
> The failure of R23-2 indicates:
>
> ```text
> ξ moves with Z,
> but future state/effect currently does not carry a recoverable Z signature.
> ```
>
> There could be three reasons for this.
>
> ## Reason A: ξ Changes Only at Logits Level; Executed Skills Don't Form Stable Differences
>
> Check:
>
> ```text
> Z -> executed ξ q_A
> ```
>
> If q_A full can't beat prior, it means forced-Z KL is a distributional difference, but the sampled executed assignments are unstable.
>
> ## Reason B: Executed ξ Doesn't Change Low-level Behavior
>
> Check:
>
> ```text
> force Z
> sample ξ
> run low-level for H={10,20,50}
> measure action / trajectory / process spread
> ```
>
> If assignments change but low-level actions/effects don't, the problem is:
>
> ```text
> z_i -> low-level behavior
> ```
>
> This goes back to discoverer capacity / individual skill semantics. The current principles also emphasize that the low-level actor should maintain `a_i ~ π_l(o_i,z_i)`, and whether a skill truly induces sustained process is a core judgment.
>
> ## Reason C: Behavior Changes, But q_D Target Too Weak / Timescale Too Short
>
> R21/R23's `q_D(Z | s_next)` might be too close to HMASD's single-step form, and in your two-clock / async structure, `Z`'s influence might require a longer window to manifest.
>
> Recommend reward-off comparison of four team-disc targets:
>
> ```text
> q_D(Z | s_next)
> q_D(Z | joint_action_summary over H)
> q_D(Z | joint_effect_window over H)
> q_D(Z | ΔOPT compact / Δω over H)
> ```
>
> Where H could be:
>
> ```text
> H = 10, 20, 50 primitive steps
> ```
>
> Don't immediately turn any of them into a reward. First check which target has residual signal.
>
> In the OPT paper, `ω` is the aggregation weights of interaction prototypes, and through CD/CMI it yields sparse/diverse and more stable interaction patterns; if state-level `s_next` can't read `Z`, but `Δω` or joint effect window can, it means the team discriminator's effect space should switch from raw state to interaction-process space.
>
> ---
>
> # 6. Don't Run Full Task Long-run for R23's Next Round; Run Small Mechanism Matrix
>
> I suggest the next round only do 320k mechanism readings, not 960k parity readings.
>
> ## Arm 0: Architecture Control
>
> ```text
> R23-arch-only
> z_assignment_residual_gain=0.5
> no g-info
> no q_A reward
> q_D probe only or off
> ```
>
> This is the current known-pass baseline.
>
> ## Arm 1: q_A Probe
>
> ```text
> R23-arch + q_A_probe
> reward off
> ```
>
> Judgment:
>
> ```text
> Can Z be recovered from ξ beyond c,ω prior?
> ```
>
> ## Arm 2: q_A Reward
>
> ```text
> R23-arch + q_A_reward_coef002/005
> q_D reward off
> ```
>
> Judgment:
>
> ```text
> Does actionability learning increase / stabilize Z->ξ?
> ```
>
> ## Arm 3: Team-disc Target Audit
>
> ```text
> best of Arm 1/2
> q_D reward off
> compare s_next / joint_action / joint_effect / Δω targets
> ```
>
> Only when Arm 3 shows non-chance residual, then allow:
>
> ```text
> q_D reward-on
> ```
>
> This follows R22's rule: `q_D` is an amplifier, not a starter.
>
> ---
>
> # 7. What Not to Do Now
>
> Don't do:
>
> ```text
> 1. Directly sweep g-info coef from 0.02 to 0.1/0.2.
> 2. Directly enable q_D reward, hoping it saves itself.
> 3. R23 960k long run.
> 4. New target-kappa / hazard / R12 DADS branch.
> 5. Use coverage/backhaul/recovery as intrinsic reward.
> ```
>
> The current implementation plan and principles repeatedly state: communication metrics are S7-S1 diagnostics and evaluation, not default intrinsic rewards.
>
> ---
>
> # 8. Regarding Whether to Update Principles
>
> Claude said "a single 320k seed isn't enough to rewrite the contract," and I half agree.
>
> No need for major principle changes, but should record an **R23 interim result** in memory / ExpRecord:
>
> ```text
> R23-0 architecture capacity: PASS
> R23-1 g-info objective: FAIL/null
> R23-2 q_D: FAIL
> Current blocker: ξ does not map to recoverable joint effect.
> Next candidate: q_A residual actionability and q_D target/timescale audit.
> ```
>
> This isn't a final theoretical correction, but it's a prerequisite for the next experiment.
>
> ---
>
> # 9. Direct Reply to Claude/Codex
>
> You can reply:
>
> ```text
> First pull raw curves, but only decision curves:
> forced_Z_KL / z_assignment_itv, g_info MI/loss, team_disc_acc/residual/prior entropy,
> and task coverage/zero-throughput.
> 
> Then don't directly do g-info coef sweep.
> Please do g-info gradient audit first:
> Does it have gradients entering Z embedding and skill/duration/edit heads?
> If not, fix wiring; if gradients are orders of magnitude smaller, record scale; if gradients are effective but MI doesn't move, switch to Option-B.
> 
> Next version objective uses Option-B q_A residual:
> R_A = log q_A(Z | ξ,c,ω) - log q_prior(Z | c,ω)
> First reward-off probe, then small-coefficient high-level reward.
> q_D remains reward-off, and do effect target/timescale audit:
> s_next vs joint_action_summary vs joint_effect_window vs Δω over H={10,20,50}.
> 
> Don't start long runs, don't q_D reward-on, don't new branches.
> ```
>
> ---
>
> ## Final Judgment
>
> R23 is real progress, but not success.
>
> It has advanced the problem from:
>
> ```text
> Z can't move assignments
> ```
>
> To:
>
> ```text
> Z can move assignments, but assignments haven't become recoverable team behavior.
> ```
>
> The core of the next step is not "stronger team discriminator", but filling the middle layer:
>
> ```text
> Learnable actionability objective for Z -> ξ
> Timescale-aware probe for ξ -> behavior/effect
> ```
>
> Once both segments pass, `q_D(Z|future)` will then qualify as an HMASD-style team exploration reward.
