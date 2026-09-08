Claim: For the selected E3 large-seed2 checkpoint, this measurement asks whether public-flag native renewal changes realized service while the learned controller continues its own internal D2 decisions.
Binding MARL structure: (b) temporal abstraction or termination; applied renewal controls each fixed agent's service lease while internal skills and recurrent state evolve on that policy's resulting observations.

# FSD_NATIVE_RENEWAL_CONTROL_A01 — science card

2026-09-07. Definition fixed for P15 engineering; **no scientific invocation released**.
Direction authority is the complete Convergence response at
`a19678fb7e0618db0c665dabe3d3cc769dc93ff5`,
`pro_packets/20260907_native_renewal_convergence/archive/RESPONSE.md`, sections 3–7;
conformity and historical evidence are in the adjacent `CONVERGENCE_INTAKE.md`.
P15 authorizes this card/spec and necessary engineering, through Root's prospective CM
comparison capture. It supplies no extra checkpoint load, sample, reset, slice or run.

## 1. Question, class and interpretation ceiling

Measure the returns of three fixed execution rules, conditional on one outcome-informed
checkpoint selection. Register this as **A/RECON: fixed-artifact native-control measurement**
under evidence-spec sections 3, 4 and 5.1. The node's “B/EXPLORE level” describes the ceiling
of its conditional observation, expressly excluding an ordinary learning B. This card does
not claim an algorithm effect or waive the nonzero learner requirement in sections 5.2,
11.4 and 11.8.6. Any subsequent learning B must run its real learner. This A has no consumption
state and is not a prerequisite for every future B (section 11.9).

The primary quantity is paired native return H−C on fresh episodes. G and H's eligible
wrong-role loss describe remaining service shortfall. This is a total closed-loop comparison:
changes in future observations, hidden state, skills and roles are part of the observation.
It does not identify a mediator-specific timing effect, synchronized D2 interruption/credit,
learned event-rule acquisition, training-seed robustness, stable superiority, transfer or UAV
validation. It requires no search, policy-class maximum or complete causal diagnosis.

The ordinary fixed-K2 policy-gap learning family stays paused. No recast, C promotion,
Portfolio lifecycle/priority change or automatic successor is selected here.

## 2. Exact evidence, source and execution bindings

| Binding | Fixed value |
| --- | --- |
| Selected training artifact | E3 `large_d2_seed2/checkpoint_final.pt`, historical launch `6d64a95a1189523e39abb184ef284a574050b748` |
| Existing local artifact | `C:/Projects/HMASD/.claude/worktrees/agent-a88287f2315bb99a0/temp/directions/flexible_skill_duration/exp/E3_20260904/large_d2_seed2/checkpoint_final.pt` |
| Existing identity record | 64,782,527 bytes; SHA256 `2f9f6c771d757db51991bab71b53687f34057dc4ddae5132b24d42afae683b89`; verified in P13 section 4, not loaded during P15 |
| Implementation input | `9fce9e70276ee7e92d29eb51a71a674e3d351621` in `C:/Projects/HMASD-worktrees/codex-fsd`, branch `codex/fsd` |
| Comparison starting revision | The complete pushed card/spec publication commit supplied with this handoff; all five arms use that same full SHA and source bytes |
| Future scientific launch revision | The accepted implementation's full committed and pushed SHA, recorded with any later named launch; not the historical training SHA or the pre-implementation input |
| Scientific execution | `.codex/hmasd-compute.toml` node `wsl_4070`, `LAPTOP-U9TDKC8A`, CPU only, 4 torch threads, float32 learned networks/actions; existing host/reward accumulation uses NumPy float64 |
| Existing remote runtime | `/home/wu/.venvs/hmasd/bin/python`, recorded Python 3.10.21 / torch 2.7.0+cu118 / NumPy 1.26.3; exact-source detached worktree under `/home/wu/hmasd-worktrees`, configured `agent-task` |
| Frozen artifact staging | Existing `scp_with_declared_sha256` route under `/home/wu/hmasd-inputs`; use the selected bytes above, with concrete path recorded at a later launch |

The scientific CPU/runtime boundary matches the selected artifact's recorded execution.
No local scientific fallback or GPU/dtype substitution is preauthorized by this card. Local
engineering fixtures use the existing scientific test interpreter and make no cross-platform
equality claim. No future actual load or batch-32 runtime has yet been verified.

Required implementation source is the named code surface in CM spec section 2 at the input
revision. P15 compared `config.py`, `config_1.py`, `hmasd/`, `envs/relay_corridor/` and the
E2/E3 runners against the historical launch: no source difference on those paths. This is
a source fact, not proof of future runtime equivalence. Checkpoint save does not contain
complete host/hidden/skill/RNG state and supports no historical or mid-episode replay claim.

## 3. Host, information, policies and reset

Use the original large Bernoulli corridor: N=6, K=2, four zones, two regions, H=400,
Delta=1, region hazards (.02, .20), `rho=0`, `c_probe=0`, coupling disabled and argmax role
decode. Keep existing deterministic entity-to-zone/region assignment, observations and
global state. Entity and slot identities coincide throughout; no join, leave, replacement,
rejoin, survivor-state rule or censoring intervention is introduced. Primitive scoring time
is t=0…399; exogenous transitions number 399 per episode. No learner discount/credit changes.

Before outcomes, set external episode master seed **770103**, ordered episode IDs **0…31**,
one batch of 32 lanes per policy. This is a newly declared object tape; the targeted prior
FSD records/runners contain no use of this master seed. It is not new training independence.
Use constructor RNG seed 2 for each C/H process and existing deterministic controller calls.
Each policy owns its own host, controller/plan and future observations. The common keys pair
exogenous events, not endogenous trajectories. No seed/episode filtering is permitted.

| Policy | Actual action and information |
| --- | --- |
| C | Independently load the selected checkpoint; run intact deterministic D2. Pass emitted continuous actions and `step_data['d2_sampled_mask']` to the existing adapter. |
| H | Independently load the same checkpoint. At t=0 use its normal forced-reset D2 renewal. At t>0 replace only the mask actually passed to the host by the current public `change_flag[:, region_of_agent]`. Preserve the original internal mask, skills, ages, recurrence and emitted role actions. Feed back H's own next observation/state. |
| G | Existing `GreedyOnPublicState`, with its own host and reset plan, using only public cue/flag and identities. Convert its emitted roles to argmax-equivalent two-coordinate actions for the same adapter. Its native roles bypass the learned actor. Preserve its default t=0 no-renew convention. |

C/H retain the checkpoint configuration; only `num_envs=32` changes for evaluation storage.
In particular n_Z=6 team tokens, n_z/action_dim=2, recurrence and all D2 settings remain
unchanged. Preserve `use_obsnorm=false`, `use_statenorm=false`, `use_valuenorm=true` and restore
both enabled coordinator/discoverer ValueNorm mean/var/count without evaluation updates.
Restore needed active network fields; no random remainder or default enabled statistic may
be presented as the selected policy. No optimizer state/resume restoration is required.

Use existing `train(False)`, `clear_buffers()` and `reset_env_state(lane)` for every C/H lane.
Start with both observation and global state returned by that policy's fresh adapter reset,
zero env_steps and false dones. Thereafter carry normal state/recurrence until H=400; no extra
reset when H changes the applied mask. G resets its plan once at its fresh episode start.

The source chain is event → fixed regional entity lease invalidation → public observation
and internal D2/actor decision → actual RENEW/KEEP and current emitted role → scoring-time
service → that policy's subsequent state. RENEW changes lease/held-role/age for later scoring;
host reward tests the current emitted role, not held_role. It does not reset regional dwell
age. Role-correct/freshness labels are read only for measurement, never injected as new inputs.

## 4. Primary observables and reading rule

For each policy p and episode e, retain all 32 `R_full[p,e] = sum(t=0…399) r[p,e,t]/400`
and `R_post[p,e] = sum(t=1…399) r[p,e,t]/399`. Report each paired full and post H−C and G−H
vector, its mean and sample standard error `std(ddof=1)/sqrt(32)`. The independent unit is
the exogenous episode conditional on the selected checkpoint. Do not compare H against the
old nonpaired C mean or treat agent steps as replicates.

Using this step's returned `renew_mask`, `lease_fresh` and `role_correct`, define eligible
`KEEP & fresh` and wrong-role `KEEP & fresh & !correct`. Report H's full/post per-episode
opportunity counts, wrong-role counts and reward-unit loss; the required post loss is
`Delta * wrong_post / (399*N)`. The conditional wrong-role rate is `wrong/eligible`, or
JSON null when eligible=0. Record per-episode internal versus applied renewal counts for
C/H and actual renewal counts for G, full/post. These counters identify the intervention;
no full action/logit/hidden tape is required. All raw episode outcomes, including losses, stay.

**Minimum effect of interest:** .01 absolute mean native reward, a descriptive scale of one
percentage point of service at Delta=1. It exceeds the known single-reset full-return scale
Delta/H=.0025. It is not a pass test, equivalence margin, competence criterion, significance
threshold or E3-rule change. Report smaller effects and uncertainty without rounding them away.
G's initial service advantage is separated by the post-reset denominator, without a fourth arm.

Apply the following selected response-section-6 reading rule without an automatic successor:

| Complete trustworthy observation | Bounded reading and recommendation |
| --- | --- |
| H improves C, approaches G post-reset, and eligible wrong-role loss is small | This fixed controller can realize service on those altered trajectories. Retain native renewal as a concrete candidate for a separately specified bounded follow-up. |
| H improves C but retains G−H and wrong-role service loss | Report local gain and remaining service shortfall separately; withdraw a timing-only explanation of complete competence. Do not assign the residual to a unique mediator. |
| H is unchanged or worse | This selected actuator substitution supplies no reason for continued timing-only investment in this instance; the unselected learning family stays paused. Other checkpoints, independent B questions and the direction are not closed. |
| Resolution is limited or episode signs differ | Preserve the finite information and end at this bound. Do not equate nonsignificance with equality or add samples to obtain a sign. |

Interpretation around the MEI is descriptive: an above-.01 gain is a material local candidate;
an inside-scale gain is still reported with its actual magnitude and uncertainty; an opposite
sign weighs against this instance. “Approaches G” requires the actual post gap and wrong-role
loss, not a nonsignificant comparison. DM applies the narrative with the rule; the runner
reports quantities and never emits a scientific promotion/closure decision.

Tuned same-information generic renewal-host headroom is **absent**. Existing E3 public
reference .890275 and selected old C mean .455985311 are historical quantities, not new H
gain or tuned baseline headroom. G reuses the matching host/information/action reference,
while bypassing actor computation. Strongest learning support remains small seed2 competent
+.033291585 and E2 duration control; contradiction remains six competent medium/large losses,
including selected large seed2 −.108895874, and E4's public-null explanation. Actor quality,
recurrence, changed trajectories, team interference and prior optimizer exposure remain alternatives.

## 5. Work, exposure, cap and termination

Python arithmetic only, from the fixed P15 design:

| Work | Quantity |
| --- | ---: |
| Policies × episodes × scoring horizon | 3 × 32 × 400 = 38,400 environment scoring steps |
| Episodes / agent-step observations | 96 / 230,400 |
| Per-policy scoring steps / exogenous transitions | 12,800 / 12,768 |
| C/H controller environment steps / batched `agent.step` | 25,600 / 800 |
| Maximum C/H coordinator batches / fixed decodes per relevant pass | 1,598 / 6 |
| G batched acts / independent C/H model constructions and loads | 400 / 2 and 2 |
| New training starts, training transitions, optimizer.step | 0, 0, 0 |
| Complete policy wall cap / summed invocation wall cap | 180 s / 540 s |

Prospective order is G, C, H: three separate complete policy processes, one batch each,
run as a plain ordered list. H reads completed G/C outputs and publishes the paired panel
inside its own cap. Each 180 s includes interpreter/import/setup, policy construction/load,
normalizers, host reset, evaluation, necessary reading checks and publication. Existing agent
construction may create optimizer objects; zero updates is not zero initialization cost.
Complete process wall is distinguished from study elapsed and its three-process sum.

Known historical linear anchors per learned arm are 8.79968751346875 s from
563.180000862/2048×32, and 14.72 s from .46×32. Neither prices standalone loading,
batch-32 operation, G or publication. Those costs stay unknown; no separate cost probe,
profiling run or claim that this is cheaper than a minimal real B is added.

Any later authorized invocation uses fresh on-node memory admission immediately before it,
joined by `&&` to the exact runner in the configured detached `agent-task`. Require physical
and effective available memory ≥4 GiB. The later operator uses the existing external process
wall limit as well as the runner's deadline, including startup/publication. Admission and
artifact staging are not scientific initialization and do not themselves authorize execution.

End at the complete panel and intake, or the first cap/dependent failure. No automatic retry,
weight substitution, extra sample/reset, partial recombination, parallel replacement or cap
extension. Record actual completed counts and any cap breach. A concrete defect in required
loading, state, information, reward or paired output limits its dependent comparison;
independently trustworthy other observations remain reportable. Missing optional RSS is
`resources_unmeasured`, not missing native return. A new source SHA would be a new launch.

**Engineering scope section 4: needs none.** Reuse the project's existing detached execution,
memory admission and frozen-input staging; add no new orchestration, runtime provenance gate,
resume service, schema system or telemetry beyond wall/peak RSS. Scientific counters above
measure the question. Source ≤2,000 new lines, runner ≤600, focused tests ≤300 s, with ordinary
independent scientific-risk review after comparison. CM spec section 5 fixes the single
bounded engineering fixture and original checks; no selected checkpoint is loaded in them.

Current P15 exposure: **0 scientific invocations; 0 actual model constructions/loads;
0 training starts/transitions; 0 optimizer steps; 0 evaluation episodes.** Historical selected
checkpoint exposure is 128,000 training transitions and recorded update counts
4350/9000/9000/300/1200, retained as outcome-informed selection history.

## 6. Predictions and recorded decision

DM prediction before this measurement: H−C is positive but H retains post-reset G−H and
eligible wrong-role loss; confidence is low because public timing can also change skill and
recurrent trajectories adversely. This is a prediction, not evidence. Owner prediction:
**not taken (unattended)**; score any later actual prediction reply at result intake.

Object-tier options: (a) freeze this selected, conditional A measurement and its CM spec;
(b) defer the card without new evidence; (c) broaden to training or alter the selected design.
Recommend (a): it makes the existing decision implementable at its stated ceiling. Option (c)
is outside P15. **Owner-delegated decision (unattended, 2026-09-03 instruction): (a).**
The A wording, new episode keys, G→C→H execution order and output layout operationalize the
accepted observation without selecting another family or changing its reading rule.

Next authorized action is Root's comparison capture of the complete committed task/spec/source,
then bounded implementation and normal review. This card is not a launch command. The next
empirical discriminator remains the native C/H/G panel after a separately named release.
