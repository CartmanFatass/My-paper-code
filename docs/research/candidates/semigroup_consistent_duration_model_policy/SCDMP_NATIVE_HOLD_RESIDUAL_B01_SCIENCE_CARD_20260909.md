Claim: A two-ended residual penalty on actual opening hold segments can improve the final sampled native return of the complete MC actor–critic within the declared single-pair learning budget.
Binding MARL structure: (b) temporal abstraction or termination.

# SCDMP-NATIVE-HOLD-RESIDUAL-B01 — B/EXPLORE

## 1. Selection and question

Selected by the complete [P58 response](pro_packets/20260908_held_residual_context_repair/archive/RESPONSE.md), immutable commit `ac1d97f5920fe2dfc88698681d389af0b907dbfe`, lines 64–119. The [DM intake](pro_packets/20260908_held_residual_context_repair/CONVERGENCE_INTAKE_20260909.md) applies the substantive second recast. P56/P58's standing continuation and Root's 2026-09-09 native confirmation allocate this **one matched pair, master8201**. Recovery authorization itself allocates no science. No empirical outcome exists at publication.

Question: does this fixed residual-MC package improve complete native return against the intact same-information MLP-MC learner enough to merit further local investigation? Ceiling: a single-pair package effect on this recipe, final checkpoint and sampled evaluation. No stable superiority, unique hold/semigroup attribution, novel residual-gradient method, expected-Bellman guarantee, sufficient-Markov or deterministic-transition assumption, TD/gate superiority, transfer, safety, deployment, C promotion or automatic UAV-entry conclusion. Old D6 source/countdown-search family PARK remains intact. No extra seed, retry, pilot, weight search or automatic successor.

## 2. Native event, ownership and information

Reuse the original five-UAV, 50 uniform-user, 256-primitive-step native motion/channel/service task and reward/terminal laws. Five fixed ordered entities retain slots for the episode; no roster changes, replacement, join/rejoin or new termination scheme. Preserve source reset and constructor behavior. Duration d1/d4 is selected only at t0; stored nonzero remaining hold can occur at t1–3, with primitive feedback resumed at t4. Unheld agents still act and all actor GRUs update on every primitive observation while a teammate holds.

Critic input remains the 136-dimensional normalized global state and five ordered prior-command/remaining-hold blocks. It excludes actor hidden histories and newly chosen current action/duration. Each arm has the identical complete 136→128→128→1 tanh MLP critic and recurrent duration actor: **66,441 parameters**. No extra parameter, gate, head, privileged actor input, synthetic transition or model successor.

Native reward and stored pre-action state → two-ended critic residual plus full MC anchor → existing joint actor/critic gradient clipping and later rollout baseline → rollout-normalized detached advantages and compound PPO → later sampled local actions → complete native return. There is no direct differentiable residual-to-actor path. Joint clipping can immediately alter actor gradient scale; later critic changes can alter future advantages. These indirect paths are part of the selected package.

Sources: [P56 source intake §§2–4](SCDMP_NATIVE_RETURN_COMPOSITION_P56_SOURCE_INTAKE_20260908.md), [source facts](SCDMP_NATIVE_RETURN_COMPOSITION_P56_SOURCE_FACTS_20260908.json), accepted UCOPE `6374063408208ba67b8cb7c69ebc0babb0f00259`, and VSPC1 recipe `65c89368ab0fc7402fb0e24254447629e829a12d`. Missing `experiments/candidates/ucope/uav_motion_prefix_b01/environment.py` in the main-derived input tree is a CM dependency restoration from that exact accepted UCOPE source, preserving the interface; it is not authority to substitute a host.

## 3. Sole treatment and comparator

**MLP-MC:** original `policy_loss + 0.5*L_MC - 0.01*mean_entropy`.

**RESIDUAL-MC:** `policy_loss + 0.5*(L_MC + 1.0*L_seg) - 0.01*mean_entropy`.

L_MC averages original complete-episode reward-to-go MSE over all 512 rollout rows, gamma=1, without terminal bootstrap. For each actual episode and t in {1,2,3}, include one team scalar pair (t,4) iff any agent's stored remaining hold at t is nonzero. Do not duplicate by held-agent count, connect episodes, select by reward or reselect under updated policies. R_t:4=sum(r_t,…,r_3), excluding r_4. V_4 uses that episode's stored input before its new t4 action.

L_seg is mean `(V_t - R_t:4 - V_4)^2` over actual eligible pairs; zero with no pairs. Both values come from the current epoch's complete-batch critic output and both retain gradients. Rewards, masks and MC targets remain recorded non-differentiable data. Reusing those outputs needs no extra model forward, separate backward or optimizer call; indexing, scalar arithmetic and gradient contributions remain actual added work.

On recorded reward paths, G_t=R_t:4+G_4, so the residual is e_t−e_4. Substituting G_4 duplicates MC; stop-gradient V_4 selects different semi-gradient TD. The selected sampled residual gradient is nonredundant but adds no label/information. Keep original MC and actor terms. Advantages use collection-time values and full MC returns, are normalized/detached once per rollout and remain fixed through four epochs. Preserve `agent_compound` PPO and likelihood/mask semantics.

Sparse support does not imply a weak penalty: L_seg averages actual pair count while L_MC averages 512 rows. The two episodes supply at most six pairs. No minimum support gate or forced hold. The arms' on-policy support and trajectories may diverge.

## 4. Learner, RNG and evaluation

Each arm: 512 complete training episodes, two per 512-row rollout, 256 rollouts, four epochs each, **1,024 actual Adam calls**. Preserve chunk32, lr3e-4, PPO clip0.2, joint gradient clip0.5, original optimizer, CPU FP32 single-thread. No intermediate evaluation/checkpoint selection, extra replay or training stream.

Source seed base b=100000×8201=820100000. Preserve initialization b+11, training action/duration b+21/b+22, training resets from b+1000, final resets from b+2000, final action/duration domains from b+3000/b+4000, including each domain's original episode indexing and constructor effects. Match initialization and exogenous reset/RNG recipes using private per-arm generator objects; do not share consumable mutable generators.

Evaluate only each final **sampled** policy on 32 matched reset episodes; evaluate original H on those same resets as an attained reference, not a learner or upper. Preserve master8101 history/weights without using them as this object's models or extra evaluation arms. No greedy selection, TD/gated/non-hold/forced-duration arm or additional learner.

## 5. Observable, prediction and reading rule

J is complete native team reward divided by 256. Primary Δ is mean of 32 paired differences δ_e=J_RESIDUAL,e−J_MLP,e. Report every episode row, both learner J−H, negative-episode counts, actual hold/pair exposure, training summaries, counts and complete costs. Conditional evaluation SE may use sample SD(δ)/sqrt(32); it conditions on these trained policies and evaluation sampling, not training-seed population uncertainty. **n=1 training pair, not n=32.**

MEI: **absolute 0.01** native time-average team reward. Source scale 0.7/50=0.014 for one continuously served user's coverage contribution motivates its size, without guaranteeing one more user served. Tuned same-information upper-minus-baseline headroom remains absent; H is attained. No qualifying headroom run. The source MLP recipe matches observation, action, information and budget; historical outcomes are context, not new-loss samples.

Working DM prediction: **WITHIN, probability 0.65**. Owner prediction: **not taken (unattended)**. Unscored until empirical intake.

| Complete trustworthy observation | Reading and recommendation |
| --- | --- |
| Δ>0.01 | One package-level native signal may justify considering an independent training pair after full intake. No stable superiority or automatic additional seed. |
| −0.01≤Δ≤0.01 | WITHIN, including both boundaries: no selected-scale improvement reason to repeat the unchanged penalty. Not statistical equivalence; a small positive Δ or lower residual is not success. |
| Δ<−0.01 | This instance favors intact MC. Preserve the loss; no automatic retuning, seed change, added budget or alternative arm. Does not close SCDMP or all residual methods. |
| Primary dependency incomplete | No complete-budget package judgment dependent on missing facts. Preserve independently trustworthy rows/counts/errors. Missing H limits H-dependent claims only if the learner comparison is independently complete. |

How the result will be interpreted: above MEI suggests a bounded performance lead worth discussing, inside it offers no clear reason to repeat this treatment, and an opposite-sign effect beyond MEI favors complete MC here. Residual fit, predictor accuracy or movement cannot compensate native loss. If either arm is below H, report that beside Δ and narrow useful-control language; two sub-H learners do not establish useful duration control with positive Δ. All-zero eligible-pair exposure is valid to report but does not exercise nonzero penalty efficacy. Do not redraw duration or relaunch to obtain support.

## 6. Exposure, cost and execution bound

[Machine card facts](SCDMP_NATIVE_HOLD_RESIDUAL_B01_CARD_FACTS_20260909.json): 2×512×256 training plus 3×32×256 evaluation = **286,720 native team steps**, **2,048 Adam calls**, **96 final evaluation episodes**. No nested action/candidate/trajectory search or solver. At most 1,536 eligible rows/arm and 6,144 treatment scalar residual terms across epochs. Added validation is §7's focused coverage, with no scientific qualification or cost experiment.

Per arm: `131072*c_collection + 1024*c_update + 8192*c_eval + complete overhead`; second arm also carries 8,192 H steps and paired publication. Treatment c_update includes residual work. The source complete-pair wall **308.63 s** is a planning anchor, not a bound. Incremental wall/CPU is unmeasured. No profiling/calibration invocation.

Caps: **1,800 s per arm; 3,600 s complete pair**, covering admission-adjacent startup, imports, initialization, training, final evaluation, necessary checks, publication/readback and exit. Assign H/pair output to second arm; no clock reset across stages or borrowed second-arm cap hiding first-arm excess. A cap or primary-dependency failure stops this execution and preserves available facts. No automatic retry, slice, changed coefficient, seed or successor.

Route: configured `remote_first`, `wsl_4070`, exact committed accepted source in a detached worktree under `/home/wu/hmasd-worktrees`, `/home/wu/.venvs/hmasd/bin/python`, CPU FP32 single-thread. This package pins the host/device route; no local/device substitution is allocated. CM binds launch SHA/command/root and observes the accepted `agent-task` handle through collection under current EXPERIMENT_MONITOR. Fresh node-local `hmasd_resource_preflight.py admit-memory` and exact runner are one supervisor command joined by `&&`, both physical and effective availability ≥4 GiB immediately before invocation. No scientific root/model/RNG initialization before admission.

Source exposure: same-recipe MLP parameters=66,441; actual Adam=1,024; total displacement/initial-L2=0.4681669210; critic=0.7238134732. Zero-initialized duration relative displacement is undefined; absolute=0.1582330167. These support that the recipe can move, not that the new penalty has moved or improved anything. Report actual later exposure without universal per-group movement gates. Card preparation has zero models, steps, training/optimizer/evaluation/replay/profiling or result-bearing invocations, recorded in card facts.

## 7. Engineering acceptance and stop

Engineering scope specification §4: **needs none**. Ordinary cumulative limits: 2,000 new non-test research source lines, 600 runner lines, five minutes focused tests per research directory excluding runner smoke. Orchestration share is a review signal, not scientific validity. No new retry/recovery service, byte guard, schema validator, framework or telemetry gate.

CM owns the complete technical batch: minimal scoped implementation and exact accepted environment restoration, focused checks plus independent affected-learning-path review, accepted-source commit/push, one detached admitted execution, observation, full collection and technical acceptance. Check both endpoint gradients, same-episode index/reward interval, mask/no-pair, full MC/actor/fixed-advantage semantics, primary aggregation and private paired RNG. Reuse unchanged native-interface evidence; do not repeat the entire native suite/history or demand actor bit equality after joint clipping's input norm changes.

Return concrete scope/meaning conflicts to DM with independent completed work. Missing resource telemetry is `resources_unmeasured`; learner/primary failures limit dependent claims under §11.8.7. E0 result evidence preserves the verbatim rule, actual counts, primary/H rows, receipts and deviations. Exit success is not scientific effect. DM takes scientific intake; Root integrates and owns cross-direction sequencing. No successor inherits this budget.
