Claim tested: On the declared two-role service toy, factorized action values may improve bounded-budget native-return learning over the named fully conditioned Q learner.
Binding structure: (b) temporal abstraction or termination; an exogenous period determines when a focal service action can change and which native rewards enter its renewal transition.

# VSPC1-K4-FACTOR-VALUE-B01 science card

Date: 2026-09-05. Evidence class: **B/EXPLORE**. Status: scientifically selected, implementation and runtime result pending. This is the first card of a new bounded learning comparison within the accepted VSP-C1 K4 agenda. A/B has no consumption state.

Selection: complete [Innovator response](pro_innovator_20260905/archive/RESPONSE.md), sections 1–7, taken in by the [DM intake](VSPC1_K4_NATIVE_RETURN_INNOVATOR_INTAKE_20260905.md). The Pro design is recorded as `PRO_FINAL`; the concrete card and next engineering assignment use ordinary object-tier unattended delegation. Current evidence spec §§11.8–11.9 controls burden. No C claim or freeze is selected.

## 1. Question, population and claim ceiling

Does explicit factorized cross-period action-value parameterization improve the selected learner's native return or learning curve against a fully conditioned generic Q network at the same information, environment exposure and optimizer-update budget? Harmful sharing or optimization cost is an equally reportable outcome.

The world has two fixed roles, one learned focal controller and one fixed partner program. The partner's plan is public and does not adapt. The resulting task reduces to fully observed, single-controller, finite-horizon control; it is a small duration-value parameterization diagnostic, not evidence of strategic MARL, partner co-adaptation or hidden-state inference. No membership change, entity replacement, slot identity, join/leave/rejoin or survivor-state issue occurs. “Identity” below means the focal held service mode, never an entity identifier.

An episode has six scored joint primitive steps, `t = 0,...,5`. The external context is `x = (p, tau, c)` with period `p in {2,6}`, partner switch tick `tau in {2,4}`, mirrored channel `c in {0,1}`. These eight contexts have equal population weight `1/8`. All are in training and evaluation; both focal actions are legal throughout. There is no held-out fourth corner, unseen duration or held-out partner claim.

The maximum positive reading is an initial, seed-specific native-return or learning-curve improvement of this parameterization against this named learner on the eight selected contexts and this finite budget. Stable superiority, semantic identity necessity, low-rank necessity, transfer, universal negative transfer, UAV benefit and deployment safety are outside the claim.

## 2. Environment, information and native consequence

- At reset, both arms observe the same public `p, tau, c` and clock. The fixed partner actually acts `b_t = c` for `t < tau`, otherwise `b_t = 1-c`.
- The focal chooses service mode `i in {0,1}` at legal boundaries `t = 0,p,2p,... < 6`, before that tick's reward. It holds that action until the next legal boundary or episode end.
- Reward is `r_t = 1[a_t == b_t]`, and the native episode return is `R = sum_t r_t / 6` in `[0,1]`. Service depends on both actually executed actions.
- At a decision boundary, the common state is `s = (2*c-1, tau-3, t/6, ell_t)`. At `t=0`, `ell_t=0` means no previous partner action; otherwise `ell_t=2*b_(t-1)-1`. Mode and period use ordinary two-entry one-hot codes.
- The action/credit path is public partner plan → partner's current channel action → focal service held until its next renewal → joint service reward → actual segment reward and bootstrap → Q update and subsequent focal choice.
- Both periods divide six. Every held segment is complete; terminal continuation is zero. Period is exogenous, not learned. There is no low-level actor, termination learner, artificial observation, teacher label or optimal-action target.

The analytical reference chooses the best action over the **current held segment** only:
`a*(t) = argmax_a sum_(u=t)^(min(t+p,6)-1) 1[a == b_u]`, breaking ties at action 0. For either `tau`, the optimum is 1 at `p=2` and `2/3` at `p=6`, giving uniform free-policy return `5/6`. This is a consequence of the declared host, not an executed reference or measured headroom. The forced-initial-action mean with optimal continuation would be `2/3`; it is a different estimand and is not run.

## 3. Treatment and competent comparator

| Arm | Parameterization | Trainable parameters |
| --- | --- | ---: |
| `FACTOR` | `[s, onehot(i)]`, dimension 6 → 16 tanh units → `u(s,i)` of dimension 4; learned period embedding `v(p)` with shape 2×4; `Q = u dot v` | 188 |
| `GENERIC` | `[s, onehot(i), onehot(p)]`, dimension 8 → 19 tanh units → unrestricted scalar Q | 191 |

Both selectors are period-aware and have the same public information and legal actions. Dense layers use CPU FP32 Xavier-uniform initialization with gain 1 and zero biases; the period embedding uses independent mean-zero normal entries with standard deviation `0.5`. No pretrained parameters are used. Different model shapes have distinct named initialization streams. Parameter counts were computed, not measured from an instantiated learner.

This is the selected competent general learning comparator, not an assertion that it is the strongest possible tuned learner. Both networks share hidden features. Four embedding coordinates with only two period columns create no binding rank-four bottleneck. Capacity, initialization, bilinear optimization, label coding and segment credit remain alternatives to any claimed sharing mechanism. A same-information analytic controller is a stronger nonlearning alternative; a fully conditioned tabular Q learner is a possible later discriminator, not a third arm now.

The existing baseline set cannot be reused as an accepted learner: the old VSP-C1 audit has zero learning and no native-return host; inspected relay/probe hosts do not implement this partner-dependent service question. New disposable research code implements the selected host and two networks. The approved scientific-tools adapter reference was read; this tiny Q comparison needs no PPO/framework rewrite, PettingZoo migration, new MARL library installation or live runtime upgrade.

## 4. Training, RNG and numerical semantics

Seed 0 only. Each of 128 rollout/update cycles contains 32 real episodes: 16 per period and four per `(p,tau,c)` context. Each context therefore receives 512 training episodes. Context ordering and exploration randomness are paired by episode and primitive boundary across arms; each arm executes its own actions and resulting trajectories. Neither arm's observed outcome selects the other's data. Use separate named initialization streams and an evaluation stream that does not advance training randomness. Record the actual seed/stream assignments; do not impose cross-host bit equality or identical parameter bytes on different shapes.

In cycle `j=1,...,128`, epsilon-greedy exploration has `epsilon_j = 1 - 0.9*(j-1)/127`; exploratory actions are uniform, greedy ties choose action 0. Choices occur only at legal boundaries. No action condition is masked. Actual identity/period/partner/context action counts are recorded; do not force equal realized counts or replace an adverse trajectory to fill a cell.

Each actual held segment supplies `(s,i,p,g,s_next,done)` with `g = sum_segment r_t / 6`. At the end of a complete rollout cycle, use pre-update parameters and detached targets

`y = g + (1-done) * max_(i_next) Q_theta_old(s_next,i_next,p)`.

The terminal term is zero, `gamma=1`. Do not add period discounting or divide segment reward by segment length again. Targets are formed before the cycle's one update; no hidden target-training pass is added.

Each cycle makes **one** full-batch Adam step, learning rate `0.01`, betas `(0.9,0.999)`, epsilon `1e-8`, weight decay zero, global gradient norm clip 5. There is no replay, extra epoch, hyperparameter sweep or auxiliary loss. There are 48 short-period and 16 long-period renewal rows per cycle. The loss is episode-weighted:

`L = (1/32) * sum_episode [(1/m_episode) * sum_segment (Q-y)^2]`, with `m_episode = 6/p_episode`.

Thus each period contributes half the loss weight, while short-period renewal counts and bootstrap depth remain three times larger. Preserve and report that difference rather than treating rows as equal population mass.

## 5. Evaluation and reading rule

At updates `0,16,32,48,64,80,96,112,128`, execute one greedy, no-learning episode for each of the eight exogenous contexts in the same real host. Every evaluation uses free legal policy choices. The evaluation rule and checkpoint schedule are fixed; there is no best-checkpoint selection or tuning on evaluation.

- `J_arm(u) = mean_x R_arm(u;x)` at each declared update.
- Primary endpoint: `Delta J = J_FACTOR(128) - J_GENERIC(128)`.
- Prespecified curve summary: normalized trapezoidal AUC over updates 0–128,
  `AUC_arm = [0.5*J(0) + J(16) + ... + J(112) + 0.5*J(128)] / 8`.
  Report both AUCs and `Delta AUC = AUC_FACTOR - AUC_GENERIC`.
- Report initialization return, per-arm learning gain `J(128)-J(0)`, every curve point, and period/partner strata from those same eight episodes. Initialization advantage alone is not faster learning.
- The descriptive minimum effect of interest is absolute `1/12`, half a service step per six-step episode on average. It helps describe magnitude; it is not a minimum positive threshold for bounded follow-up.

The rule below is applied to the complete observations, including opposite signs between endpoint and AUC, and never only to the more favorable metric:

| Observation | B reading and recommended next decision |
| --- | --- |
| Missing updates, mismatched information, wrong reward/target or damaged primary evaluation makes the dependent comparison untrustworthy | Name that implementation/measurement dependency; report independently trustworthy narrower facts. It supplies no mechanism-negative or candidate-winning comparison. Repair the concrete dependency before its next invocation; unrelated historical failures need not be solved. |
| Trustworthy final-return or prespecified curve improvement for FACTOR, with both actual learners and evaluators complete | A local investment signal. Recommend the same comparison on independent training seeds 1 and 2 under a newly recorded bounded object-tier decision. Preserve a contradictory endpoint/AUC, initialization advantage and all adverse strata in the wording; do not claim stable superiority. An improvement below `1/12` can qualify. |
| Both arms reach the same analytical optimum early and have no useful curve difference | This host/budget lacks further discrimination. Do not append an identical exhaustive A or purposeless repeat B; do not close K4. |
| GENERIC is better without a credible FACTOR advantage in the other prespecified measurement | Local contrary evidence for this factorized parameterization at this budget. Inspect existing initialization, learning curves and action strata, especially conflicting first-action preferences, before attributing the cause. No new diagnostic or learner arm is automatically added. |
| Both valid learners improve little, or the remaining observations are inconclusive | Still a valid finite-budget exploration. A concrete new B may be proposed from these observations; positivity is not a universal follow-up prerequisite. |

Above the MEI, a credible FACTOR advantage is a larger local signal for bounded replication. Inside it, report the observed sign and small size and consider the same limited follow-up if worthwhile. An opposite sign weakens this parameterization's conjecture at this budget and is preserved. Initialization, optimization and representation remain live explanations; the rule does not turn them into prerequisites for seeing whether the real comparison has value.

No statistical interval over training-seed performance can be estimated from one seed. The eight contexts and nine repeated checkpoints are not independent training seeds. All observations and failures remain on record; no run-until-positive policy is selected.

## 6. Predictions and headroom

DM prediction: the generic network is likely to catch up quickly on this tiny public-plan task; FACTOR may differ early but is not predicted to win reliably. The main alternatives are an early factorization benefit, a factorization optimization/interference cost, and no useful discrimination once both learners solve the task. For `tau=4`, first-action preferences across periods agree; for `tau=2`, they conflict. Existing evaluation strata can describe that contrast without identifying a unique mechanism.

Owner prediction: **not taken (unattended)**. Score any subsequent actual owner prediction at intake without inventing a reply.

Headroom record: old `VSPC1_IDENTITY_PERIOD_HEADROOM_A01` validly found the registered production host and both headroom terms unavailable. That remains missing, not zero. The new toy has a declared analytic reference `5/6` but no executed generic baseline or measured/tuned gap. The real generic learning arm supplies an early baseline observation; missing tuned headroom does not hold this B.

## 7. Computed exposure and complete work

The [machine-generated design counts](VSPC1_K4_FACTOR_VALUE_B01_DESIGN_COUNTS_20260905.json) were produced with Python arithmetic from the selected configuration, without constructing a model, RNG or environment. This preparation has zero new scientific executions. Its future counts are not observed exposure.

| Quantity | Per arm, seed 0 | Two arms |
| --- | ---: | ---: |
| Training episodes | 4,096 | 8,192 |
| Training joint primitive steps | 24,576 | 49,152 |
| Training renewal transitions | 8,192 | 16,384 |
| Actual optimizer steps planned | 128 | 256 |
| Evaluation episodes | 72 | 144 |
| Evaluation joint primitive steps | 432 | 864 |
| Evaluation legal action choices | 144 | 288 |
| Complete training + evaluation joint primitive steps | 25,008 | 50,016 |

Per arm the training renewal counts are 6,144 at `p=2` and 2,048 at `p=6`. Joint primitive steps are six-step task interactions, not independent agent samples. The two arms share exogenous seeds but remain one paired training-seed comparison. Each arm has 8,336 training-plus-evaluation legal decisions. Scoring the two legal actions for Q maximization is intrinsic to the learner, not trajectory or policy search. There is no nested candidate-policy census, trajectory branching, model selection, extra controller rollout or hidden future seed in these numbers.

Machine-generated prospective exposure line: `FACTOR/GENERIC = 188/191 trainable parameters; each = 8,192 reward-bearing transitions, 128 unfrozen Adam updates at lr 0.01; nominal sum(lr)=1.28; sqrt(E||theta_0||^2)=4.138510931/3.627569332 under the stated initialization`. This is a positive optimization budget with a specified initialization scale. The nominal schedule sum is neither realized movement nor an Adam displacement bound. At actual execution report `||theta_0||`, `||theta_128-theta_0||`, their ratio and the nonzero observed training/update/evaluation counts from each learner. There is no invented minimum displacement-ratio gate and no reuse of the preparation file's zero actual exposure as the learner's evidence.

The complete per-arm cost law is
`C_init + C_rollout(24,576 joint steps; 8,192 renewals) + C_update(128 full batches of 64 renewal rows) + C_eval(432 joint steps; 144 decisions) + C_check_and_publish`.
Each two-action scorer is a small dense network with 188 or 191 parameters. Actual unit times, full wall seconds, peak RSS and development cost are unmeasured. Counts, in-process batching and native tensor kernels do not establish a speedup or guarantee affordability. No separate calibration A, benchmark or search is needed to estimate a quantity the real bounded invocation will directly measure.

Not selected: 40-episode zero-learner A (240 joint steps), 16-episode forced-initial-action evaluation per policy (96 joint steps), or eight-episode actual analytic-reference evaluation (48 joint steps). No separate reference or upper-census obligation is inherited from them.

## 8. Resource bound, stop and portability

The object cap is **2,700 seconds per complete arm/seed invocation**, including imports/initialization, training, all nine evaluations, necessary checks and publication. This is the selected B cap, not merely an interpretation of the runtime investigation threshold. Run the two arm invocations serially; their maximum sum of invocation wall budgets is 5,400 seconds, not a guarantee of elapsed study time. Charge real one-time shared preparation once, name its scope and do not move a required stage outside invocation accounting.

Prospective execution is host-portable between the configured nodes, with CPU FP32, one scientific process, one compute thread, in-process batch 32 and the protected RNG/comparison semantics above. CPU is fixed for this comparison; changing to GPU is not a routing substitution. Default route is remote-first `wsl_4070`, exact committed source in a detached worktree, configured interpreter and existing `agent-task`. No existing process is migrated. Local fallback is possible only under the repository's prospectively portable/no-accepted-remote-process/fresh-local-admission rule. No cross-host bit-equivalence claim is made.

Immediately before **each actual arm invocation**, the actual execution node must pass `scripts/hmasd_resource_preflight.py admit-memory`, physical and effective available memory both at least 4 GiB. The existing remote supervisor runs admission and the exact runner joined by `&&`; the card is not a receipt. Source must be committed and pushed before execution. Exact launch SHA, command, actual node, interpreter, output root and receipt are recorded at CM launch, not invented here.

At the invocation wall cap, stop that invocation and report actual completed exposure and trustworthy outputs. Do not drop a stratum, omit publication, shorten a hidden stage or automatically continue at another SHA to obtain a positive result. A concrete technical failure is reported immediately; cause attribution needs direct evidence. No parameter, seed or arm rescue is preauthorized by a failure. Future bounded choices use their actual intake and ordinary delegation.

## 9. CM objective, owned surfaces and technical acceptance

Implement exactly this real host, two policies, renewal learner, trainer, fixed evaluator and readable primary result in one disposable attempt. Proposed ownership:

- `experiments/candidates/vsp_c1/k4_factor_value_b01/`
- `scripts/run_vspc1_k4_factor_value_b01.py`, a thin argparse runner with arm and seed arguments
- `tests/experiments/candidates/vsp_c1/` for one focused profile of changed behavior and primary output
- Runtime roots below `temp/directions/vsp_c1/exp/`, one arm invocation per distinct output root

Core, old VSP-C1 audits, old SCDMP D6 code/results and other directions are outside the change. Existing files belong to concurrent workers; do not revert them. CM owns exact implementation decomposition, independent review, direct runtime observation and technical acceptance; DM owns scientific intake.

Engineering scope §4: **needs none of the default-prohibited machinery**. Use ordinary in-process tensor batching and the existing external supervisor/admission tooling. A list of two serial commands suffices. Do not add a queue service, worker pool, checkpoint/resume platform, provenance guard, schema registry, historic replay tree or repeated smoke. No VNFC four-thread exception is imported.

Protect reward, observation access, legal hold boundaries, population and loss weights, initialization/RNG pairing, dtype/device/thread/batch semantics, detached bootstrap, actual update count, fixed evaluation/checkpoint schedule, all adverse observations and primary output. There is no frozen checkpoint file format because checkpoint/recovery orchestration is not needed; the nine evaluations refer to update states within the actual run.

Use one focused verification of actual changed dependencies: held actions, partner switch timing, six-step native reward, terminal bootstrap, population/loss weighting, equal information and primary-result write/read. Inspect actual budgeted trajectories and outputs, adding no environment smoke or learner updates just to repeat these observations. Small direct checks of the implementation and result-reading rule do not become another experiment. Reuse valid existing checks if relevant; there is no full historical publication dependency. Required source limits remain 2,000 new non-test lines per attempt, 600 runner lines and five minutes of research-directory tests; orchestration share is a review signal, not an automatic refusal. Report a concrete excess or missing primary dependency rather than adding machinery to certify it.

Each run's `summary.json` contains the actual launch context, per-checkpoint/context returns, actual action and transition/update/evaluation counts, learner norm/movement measurements, primary aggregate, wall/RSS status and any primary dependency defect. Compact summaries sufficient to inspect the selected measurements are enough; no full tensor/trajectory dump is required. Missing optional resource telemetry means `resources_unmeasured` unless the claim depends on it; missing primary learner/evaluation facts limit the dependent comparison. Tests passing and a process exiting do not establish mechanism value.

Once a real detached process is accepted, CM/DM hands the existing process handle, node, launch SHA, cwd, run root, logs/exit witness, cap and this DM's canonical name to the shared tracker published in Portfolio. Tracking is observation coverage and never a launch gate. No process or resource admission exists at this card boundary.
