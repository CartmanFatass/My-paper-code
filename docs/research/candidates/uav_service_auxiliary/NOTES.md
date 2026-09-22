# UAV end-to-end service auxiliary learning

## 2026-09-21 — Owner-selected independent study

The newly created independent Codex task is the sole DM for this owner-selected direction.
Record its actual task/host/checkout/branch in RESEARCH. Work, interpret and publish in this
task; after initialization do not communicate with another DM or Root. Shared Git evidence,
current research background, Pro consultation and bounded internal helpers remain available.
Owner's compute order: prefer configured remote WSL `wsl_4070`, then local computation only
with a recorded availability, resource or suitability reason. Preserve accepted handles and
use actual-node admission; four research tasks do not imply four simultaneous heavy fits.

### Question and use of consensus

With fixed k and N in Scenario7 interface v3 / reward v2 / arm C, does supervision by actual
future end-to-end service help HMASD learn coordination under access, backhaul and energy
constraints? This directly studies the service mechanism; it does not wait for S1 positives
or treat S7 as a rescue after another direction fails. G33 remains frozen.

The [background at 455837f60](https://github.com/CartmanFatass/My-paper-code/blob/455837f60127cc31fbc5d802e19dfd79d0a2bfec/docs/research/RESEARCH.md)
sections 1–3, 6 and 7 rules out using better local link/connection statistics as proof of
delivered service. Known reward does not make future joint consequences known; better MSE
does not establish a better controller. B/UCOPE's local useful signals failed to establish
stable complete return. C/VSP justify competent ordinary consequence references, not a claim
that this neural UAV auxiliary is already useful.

The [complete programme advice and decision](../../archive/2026-09-21/RESEARCH.md#portfolio-review-2026-09-21-whole-project-evidence-led-research-plan)
supports a direct S7 study and supersedes the earlier blanket S1-first recommendation.
Read it before fixing the service target. Existing S7 registration is not proof of full HMASD
integration; old arm-A scores do not transfer to v3/v2/arm C. Do not modify fault rates,
reward or frozen G33 artifacts to create an opportunity.

### First comparison

Both arms train the same small factual readout on the actor/GRU representation. The control
stops auxiliary gradients at that representation while preserving normal actor RL; the
candidate permits auxiliary gradients into the encoder/GRU. Both prediction heads are trained.
Fix one actual future end-to-end service target, window and terminal/truncation semantics
before scores. Future labels are training targets only, never current actor inputs.

Audit optimizer, clipping and RNG isolation: a supposedly detached head must not alter the
control actor through shared optimization or global clipping. Do not simultaneously introduce
planning, communication, duration learning, a new discovery objective or another DM's encoder.
Native J and actual service/risk components determine use. A common factual validation set is
needed for a comparative prediction-capability claim; own-rollout MSE alone can reflect easier
visited states. Retain a useful package result even if its proposed mechanism needs revision.

### Initial work and cost

Bind actual S7 observation/label/learner/evaluator paths and choose the minimal complete
integration that answers this question. Record the concrete missing pieces and costs.
Do not replace missing native service labels with synthetic targets or expand into a general
host migration. If integration dominates a question that has become generic representation
learning, make a reasoned scope/investment judgment under the existing scientific process.

Own this notebook, `experiments/candidates/uav_service_auxiliary/`, its tests and
`runs/uav_service_auxiliary/`. Review shared executable changes independently. Declare exact
arms, seeds, horizon, evaluation and fits with a reason before execution. Initialization
starts **0 fits**, accepts no experiment/Send and supplies no performance claim. Continue
independently to an informative native result and a supported keep/revise/stop decision;
publish reusable conclusions in the existing shared background.

## 2026-09-21 — Direct DM initialization and bounded interface work

Task `01a0c6f0-31e1-7510-bee7-4f0f8b62d821`, local host, owns this direction in
`/home/fires/.codex/worktrees/a335/hmasd-wsl`, branch `codex/uav-service-auxiliary`.
Published main `69d7d2a3d86805155ea991cf443be259602bc17e` was refreshed before registration.
No accepted operations or fits were inherited. The full programme Answer/Decision has been
read and reused for this unchanged factual-head comparison: direct S7 is warranted by its
actual service constraints, not conditional on S1 success. Background sections 1–3 and 6–7
therefore change the design concretely: choose delivered QoS rather than local SINR; retain
native J and risk alongside prediction; train both heads and evaluate on common factual
fragments. B/UCOPE forbid interpreting forecast improvement as control gain; C/VSP make
ordinary consequences a serious reference without introducing a planner into this question.

The configured remote `wsl_4070` responded as `LAPTOP-U9TDKC8A`; initial inspection showed
14 GiB available RAM, 7948 MiB free GPU and 0% GPU utilization. This is suitability evidence,
not result admission; a fresh actual-node check is required at launch. Local source reading
and correctness tests do not consume scientific fits. Bounded read-only Scout maps S7 data
and update interfaces while the DM binds the experiment. No inter-DM messages are sent.

### B01 prospective comparison and L0

Select native preset **S7-S2**, interface 3 / constrained_qos_safety_pbrs_v2 / arm C,
N=8, 30 users, fixed k=10, 1500-step episodes. S2 includes battery/charging and moving
users, without S4 faults; no fault-rate, reward, physics or observation changes. The
label is the mean of the next W=10 realized `reward_info.qos_satisfaction_ratio` values,
starting with the transition taken from the represented current observation. This is
capped actual delivered end-to-end demand, not access capacity or a synthetic label.
Only complete windows contained within an episode are supervised: true termination,
time-limit truncation and collection cutoff all censor incomplete windows; no padding,
bootstrap or cross-reset label. RL retains the native finite-episode treatment.

Two arms, `detach` and `joint`, training seed 910021, **2 planned fits**. Each fit has
4 synchronous lanes ×1500 steps ×30 rollouts =180,000 team training transitions, with
native HMASD high/low/discriminator updates after each rollout. Keep Config S7-S2 native
architecture/skills/PPO settings, no extension algorithm. Final endpoint after rollout 30;
intermediate evaluations at 0/10/20/30, 8 deterministic complete episodes each using
world seeds 920001–920008. Read raw summed and mean-per-step native reward J, delivered
QoS/throughput, return constraint, cutoff/depletion and charging. No best-checkpoint selection.
One seed is exploratory: these readings cannot establish training-population superiority.
The horizon buys 120 full energy episodes per arm and 30 native joint update stages;
it is a bounded first complete-learning comparison, not a convergence claim.

Both arms train the same hidden→64→1 factual head. After each native RL update, one
chronological auxiliary pass replays the just-collected legal observations and actual
held skill sequence from zero at episode start, with 50-step truncated BPTT chunks.
Head Adam lr=3e-4; separate representation Adam lr=3e-5 for the joint arm only, on
existing actor base encoder and GRU (FiLM constants preserved in this auxiliary pass).
MSE on complete windows, same sample exposure. Clip head and representation separately
at norm .5; head parameters never enter RL optimizer/global clipping. Detach arm blocks
only auxiliary gradients, leaving all native RL updates active. Head initialization uses
a saved/restored RNG context; auxiliary pass has no random sampling/dropout. Auxiliary
observations use the actor's legal normalization, without updating running statistics.

For prediction comparison, both endpoints replay identical initial-policy factual episodes
on held-out seeds 930001–930002, collected before learning with the shared initialized
policy, saved with arrays and digest. Observations and realized skills are conditioned
on the same factual trajectory; labels are never actor inputs. Each trained representation
is replayed from zero under its own current weights. These data are evaluation-only.
Own-rollout training MSE is only a diagnostic. Prediction: joint supervision may reduce
common-fact MSE and improve delivered service/native J; native benefit without MSE gain
retains only a package explanation. Better MSE without native benefit weakens this target's
control usefulness, with no automatic target/model sweep (programme Pro stopping advice).

Implementation L0: own `experiments/candidates/uav_service_auxiliary/b01/`, mirrored tests,
and `scripts/run_uav_service_auxiliary_b01.py`. Reuse native environment/adapter, HMASDAgent
step/store/update, and existing evaluator weight/normalizer synchronization. Add a small
standalone auxiliary replay component and native collector/evaluator; no shared core edits
are intended. Check target censoring/shift, detached actor identity, nonzero joint base/GRU
gradients, head/RNG/clipping isolation, real S7 label extraction, optimizer movement and
admission-before-effects. Independent Reviewer checks numerical/recurrent/runner semantics.
Remote WSL runs sequential fits; fresh admission before each. No scientific launch before
checks/review and committed, published exact inputs. Stop implementation expansion at a
concrete integration conflict; do not substitute a synthetic task or silently shrink exposure.

### B01 interface refinement before implementation/results

The current shared native PPO replay still uses transition `done[t]` to mask entry to row t.
The already published B-direction correctness repair `1da535e557bb1eaac30779d4596e3b2efa6426ee`
changes this to row 0=1 (stored input hidden state), later row t=`1-done[t-1]`.
Adopt that exact minimal repair and its storage→sampler→actor/critic regression for both arms;
include it in independent review. This is shared correctness work, not an auxiliary gain,
and does not change any historical frozen experiment. L0 expands only to that existing
`hmasd/agent.py` change and `tests/hmasd/test_discoverer_entry_masks.py`.

Native S2 can truly end early if all batteries exhaust. The collector must preserve terminal
next inputs before reset and allow an episode to straddle a rollout. The 120 episodes stated
above is the no-early-terminal nominal count; actual transitions remain exactly 180,000 and
actual episode count is recorded. For a straddling auxiliary rollout the stored input actor
hidden state anchors row 0, otherwise it is zero at a real reset. All subsequent resets use
the shifted done mask. This ordinary truncated replay anchor is explicit; it is not a full
current-parameter history reconstruction. Validation episodes always replay from zero.
Both termination and native finite-horizon truncation zero RL continuation as in the S7
collector; an unfinished collection boundary bootstraps the native value. This amendment
precedes every score and fit.

B01 execution binding: use remote `wsl_4070`, CUDA float32 for the learner and 4 Torch CPU
threads; keep CUDA/CPU/Python/NumPy evaluation RNG isolated and disable TF32 for this pair.
The actual remote environment reports Python 3.10.21, Torch 2.7.0+cu118, NumPy 1.26.3 and
available CUDA. The two fits use separate native admissions and run sequentially. The first
(detach) fit creates common initial-policy facts; the joint fit must read that exact retained
file with a declared SHA256, copying it into its output. No independent regeneration is
substituted. Auxiliary initialization seed is training seed +200000 for both arms. Evaluation
worlds and forecast worlds are disjoint from training seeds. The existing arm-A comparison
gate is unused; no inherited arm-A target enters this experiment's decision.

B01 endpoint clarification: primary native J is the arithmetic mean of complete per-world
**summed unmodified S7 rewards** on the eight endpoint worlds, joint minus detach. Mean
reward per executed step is a secondary scale description; no S1 reporting multiplier is
applied. Delivered QoS/throughput and risk retain their own units. No single-seed ranking
is generalized to a population. Remote preparation required the configured `zsh -lic`
network environment: an initial plain-shell fetch stalled and was terminated before any
worktree/launch effect; the configured path then fetched and created the owned isolated
`/home/wu/hmasd-worktrees/uav-service-auxiliary-a335` successfully. No scientific operation
was accepted. The canonical remote checkout/index was not edited.

### B01 component checks before native admission

The DM accepted the auxiliary component after reading its diff and independent Reviewer
review of the real actor feature path, complete-window targets, masked resets, optimizer
parameter ownership and recurrent core fix. No material first-stage finding remained.
Local focused auxiliary checks passed 5 cases; the CUDA-only case was skipped locally.
The shared storage/sampler/update entry-mask checks passed 2 cases. Tests are correctness
fixtures, not scientific fits or UAV performance evidence. The remaining review concerns
the native collector/evaluator, common-fact identity and final checkpoint/output path.

Remote checks at published component commit `7e79fc632` passed all 8 auxiliary and
storage/sampler/update tests in 3.44 seconds on `wsl_4070`, including the actual CUDA FP32
gradient/RNG isolation case. Fourteen dependency deprecation warnings did not affect the
checks. This used the owned remote worktree and configured interpreter; it accepted no
scientific fit. The native collector retains the existing post-update `clear_buffers`
behavior: the next native step reinitializes skills and recurrent state, including a lane
whose physical episode straddles that collection boundary. Auxiliary replay follows the
actual stored row-0 hidden input; it does not silently repair this shared behavior. At an
unfinished boundary, RL bootstrap uses the next state and current critic hidden state with
the held current skill. The default full-episode alignment usually avoids that boundary;
the runner records actual straddling lanes for interpretation.

The repository-wide new-runner admission source check currently fails on the existing
`scripts/run_fsd_commitment_visibility_b12.py` entry, before reaching this direction's
runner. No historical FSD source was changed. The owned B01 entry independently passed
the same admission-call AST condition and a real no-admission CLI invocation: it refused
with `missing HMASD admission` before importing scientific code or creating output.

### B01 native acceptance and preflight

The DM accepted the bounded native runner at `3e3fb068c9b20f2c263b01f2c83c51092e9172c0`
after reading the implementation and independent second-stage Reviewer review. No material
finding remains against the frozen contract. Review covered terminal next-state storage,
native bootstrap, complete-episode raw J, evaluation/normalizer isolation, common-fact
digest/initialization/seed identity, paired final checkpoints, progress/failure retention
and admission before scientific imports. The Reviewer explicitly reconciled the already
declared `clear_buffers` boundary behavior as a common baseline limitation. Focused native
checks passed 5 cases locally with 1 CUDA skip in 4.97 seconds after correcting the reviewer's
Ninja PATH. An earlier local dependency-path failure did not start a scientific fit.

The exact published native source passed all **6** focused native checks on `wsl_4070`
in 13.57 seconds. This includes the complete short collect/native-update/auxiliary/evaluate/
checkpoint path for both arms on CPU and actual CUDA; the CUDA case uses the native
256-wide architecture. Both heads update, all five native optimizers update and their
modules move; only the joint auxiliary path has representation gradients. The earlier
8 component/core checks remain unchanged. The checks do not establish 30-rollout stability;
multi-rollout straddling and injected mid-run failure persistence are not separately exercised.

The final preparation probe reports 12 GiB available host RAM, 7948 MiB free GPU memory,
0% GPU utilization and no CUDA compute process. The remote canonical tracked checkout is
clean and its current pause/state/lead for this direction matches the assignment. This is
preparation evidence; the native kernel must still perform fresh admission. Proceed with
the fixed pair sequentially, first output `runs/uav_service_auxiliary/b01_detach_910021_a01`.
No training fit has started at this entry. Bind its actual source/operation through the
runner-written manifest, then arm deterministic observation of that same handle.

### B01 detach accepted — 2026-09-21 20:01 PDT

The first planned attempt was accepted at `2026-09-22T03:01:41.983024Z` on `wsl_4070`
from published source `382643ca91cf764336f3311bc166275a5d2bbe97`, retaining the exact
snapshot. Its authoritative manifest is on `hmasd-wsl-node` at
`/home/wu/hmasd-worktrees/uav-service-auxiliary-a335/runs/uav_service_auxiliary/b01_detach_910021_a01/launch-manifest.json`;
that manifest binds the stable operation reference, output, process identities, preflight
and logs. Same-handle status at `2026-09-22T03:02:41.673817Z` reports accepted, running and
consistent identities. The supervisor command finishing successfully is not fit completion.
No scientific result has been read or accepted. The joint attempt remains unstarted.

Detached `tools/hmasd_wait.py` observation is armed for this current task, probing the
original remote output via native `status`; its private state is
`/home/fires/.local/state/hmasd-wait/01a0c6f0-31e1-7510-bee7-4f0f8b62d821`.
At completion, error or the bounded checkpoint, drain that state and reconcile this same
operation. Never launch a replacement or repeat the accepted request. After a complete
detach reading, run only the already fixed joint arm with the retained facts digest and
fresh actual-node admission. No cross-task notification or additional fit is authorized
by the observation event.

### B01 detach complete and read — 2026-09-21 22:20 PDT

The native exit witness is valid with code 0; the saved terminal observation at
`2026-09-22T05:20:32.719796Z` reports consistent records. The DM read the complete
[runner summary](../../../../runs/uav_service_auxiliary/b01_detach_910021_a01/summary.json),
configuration, learning/evaluation records and final prediction arrays. All 13 copied files
match the remote SHA256 values. Both final checkpoints load and every floating tensor is
finite. This accepts **1 completed fit**, not a comparative auxiliary result.

Actual exposure is exactly 180,000 team training transitions, 30 native/auxiliary update
stages and 120 complete training episodes. All 32 evaluation episodes are complete 1500-step
truncations on the frozen eight worlds; actual evaluation exposure is 48,000 transitions.
The two common-fact episodes contribute 3000 transitions and 23,856 valid per-agent
predictions per endpoint. There were **0** straddling rollout boundaries. All five native
modules moved from initialization; recorded optimizer steps are high=2250, low actor=67500,
low critic=67500, team discriminator=450 and individual discriminator=1800. Each auxiliary
stage has 5964 supervised team rows / 47,712 agent samples and 30 head steps; all detach
representation gradient norms are exactly zero. Runner wall time is 8318.307 seconds
(138.64 minutes), peak RSS 3,026,388 KiB, on `wsl_4070` CUDA FP32. No extra fit was started.

| Rollout | Mean complete native J | Mean QoS ratio | Mean return constraint cost | Common-fact MSE |
| --- | ---: | ---: | ---: | ---: |
| 0 | -521.691683 | 0.114334 | 0.227204 | 0.002800299 |
| 10 | -283.523015 | 0.228059 | 0.204274 | 0.007282700 |
| 20 | -555.766203 | 0.153292 | 0.257773 | 0.001460180 |
| 30 | -644.966810 | 0.152040 | 0.286961 | 0.010846485 |

Endpoint delivered throughput is 4.561212 Mbps and raw reward per step is -0.429978.
The fixed endpoint remains rollout 30; rollout 10 is not substituted as a best checkpoint.
An independent NumPy window calculation on the saved factual labels/predictions reproduces
the final MSE as 0.010846484902 (23,856 samples). The common fact identity is
`eed668d62a5ae3151463b93ee24ca292fc330ce51ca489d1fdb82a826d344a3e`;
initial full-model fingerprint is `d934e4fff0b02cb3a5987ad630793d63c43ac8ef51ae0c3b6329676b0194c851`.
Final checkpoint SHA256 values are agent
`fb83a18ce1845d2db3eb6b8837186ba2fc2ff1aefbd571eb1b827dfd934c3ba3` and auxiliary
`275f5330c86aa2afec253491d258f1acc5c55c55c6735ebfc9ea449740bb153e`.
The facts, prediction NPZ and checkpoints are retained in the original remote output and
the identical local `runs/uav_service_auxiliary/b01_detach_910021_a01/` copy; binary files
and ignored logs stay outside Git under its existing ignore policy. Runner JSON/JSONL
evidence is published.

Observed scope: charging occupancy/energy, cutoff events and depletion events are zero
throughout collected training and evaluation. The return constraint cost is active, but
this fit supplies no observed charging competition or failure-recovery evidence. Complete
J and factual forecast error are non-monotonic despite real optimizer movement. Technical
integration is established; native competence, auxiliary package advantage and training-seed
generalization remain unestablished. No horizon extension or target change follows these
scores. Current main background still supports reading complete native outcomes separately
from forecasts; the latest duration-interface clarification changes none of this fixed pair.

Proceed with the already declared second fit, joint seed 910021, the same 180k horizon and
source `382643ca91cf764336f3311bc166275a5d2bbe97`. Output is
`runs/uav_service_auxiliary/b01_joint_910021_a01`. The `--facts` input is the original remote
detach `facts.npz` above and `--facts-sha256` is its verified digest; regenerate nothing.
Fresh preparation currently shows 10 GiB available RAM and 5706 MiB free GPU memory; native
admission will recheck actual resources and current policy. No new Pro question is needed:
the programme advice already covers this unchanged, predeclared comparison.

### B01 joint input staging correction before acceptance

The first joint supervisor command at `2026-09-22T05:26:42Z` was refused before training,
exit code 4 after 15 seconds: `absolute author input is absent from published snapshot`.
It named the generated detach facts inside the author checkout, where the snapshot
argument mapper requires a published source file. The refusal occurs in path preparation
before claim/output creation or child release; same-output `status` reports that the
reference does not exist. No joint fit or accepted process was created. Its unchanged
failure log remains at `hmasd-wsl-node:/home/wu/.agent-tasks/uav-service-b01-joint-910021-a01/task.log`.

DM correction: copy the exact verified facts to the configured external input staging root,
`/home/wu/hmasd-inputs/uav_service_auxiliary/b01/facts_eed668d62a5ae3151463b93ee24ca292fc330ce51ca489d1fdb82a826d344a3e.npz`.
The staged 5,450,529 bytes have the same SHA256; the original facts/output remain intact.
Only the physical `--facts` location changes. Keep the same source, digest, arm, seed,
horizon, evaluation and unused joint output tag. This corrects a known pre-training
invocation failure; it is not a restarted accepted operation or another started fit.

### B01 joint accepted — 2026-09-21 22:29 PDT

The corrected external-input invocation was accepted at `2026-09-22T05:29:38.367056Z`
on `wsl_4070`; see its retained [native manifest](../../../../runs/uav_service_auxiliary/b01_joint_910021_a01/launch-manifest.json)
and actual-node [preflight](../../../../runs/uav_service_auxiliary/b01_joint_910021_a01/admission-preflight.json).
The source remains `382643ca91cf764336f3311bc166275a5d2bbe97`. Same-handle status at
`2026-09-22T05:30:35.022361Z` is running with consistent supervisor/runner identities.
The runner has independently verified and copied the common facts: both the full file
SHA256 and initialized-model fingerprint exactly match detach. No facts were regenerated.

The fixed pair now has **1 completed fit and 1 accepted/running fit**, plus the separately
recorded 15-second pre-training refusal. Detached observation for job
`launch-b01-joint-910021-a01` is armed in the existing current-task wait state; the completed
detach terminal event was consumed. Continue this same joint operation through completion
or a bounded checkpoint, without restart, extension or task messaging. No auxiliary package
comparison or population claim is available before the joint endpoint is read.

### B01 joint complete and paired reading — 2026-09-22 01:09 PDT

The joint operation exited with a valid code-0 witness; the terminal observation at
`2026-09-22T08:09:01.450027Z` reports consistent records. The complete
[joint summary](../../../../runs/uav_service_auxiliary/b01_joint_910021_a01/summary.json),
configuration, progress, native/auxiliary update rows, all evaluation panels, prediction
arrays and checkpoints have been read. All **13** copied files match remote SHA256 values.
Both final checkpoints load; every floating tensor is finite (agent: 694 tensors,
17,493,733 elements; auxiliary: 46 tensors, 1,159,057 elements, including optimizer state).
All summary numbers are finite and `failure` is null. This is **2 completed fits** total;
the 15-second pre-training path refusal remains separate. No fit was restarted or extended.

Both fits have exactly 180,000 training transitions, 30 native/auxiliary update stages,
120 complete training episodes, and 32 complete 1500-step evaluation episodes (48,000
evaluation transitions). Every training and evaluation episode ended by the time limit;
both have zero straddling rollout boundaries. Each auxiliary update used 5964 valid team
rows / 47,712 agent samples and 30 optimizer steps. All 30 joint representation gradient
norms are positive (range 0.122664–1.817539 before clipping), while detach is zero throughout.
All five native modules moved, with the same optimizer-step counts reported for detach.

The frozen source, facts digest and full initialization fingerprint match. The entire
initial evaluation panel, first training rollout and first native update agree exactly
between arms. Configurations differ only in the snapshot-root prefix of the unused historical
arm-A metrics path. The shared facts were collected once by detach (2 episodes / 3000
transitions); joint loaded their exact bytes, rather than creating another fact rollout.
The joint final checkpoint SHA256 values are agent
`bbab70aa8206d2fdb6ccefa6cd037ff57c3d34d9d1578b36c3c0251a9fcd4626` and auxiliary
`56332ac9b26821b0b14aab9d28f44a51e6b649535fefa9aa41614520e07105ff`.
Binary arrays/checkpoints and logs are retained remotely and in the identical local run
directory under the existing ignore policy; runner JSON/JSONL evidence is published.

| Rollout | Detach native J | Joint native J | Joint − detach J | Detach QoS | Joint QoS | Detach common-fact MSE | Joint common-fact MSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | -521.691683 | -521.691683 | 0 | 0.114334 | 0.114334 | 0.002800299 | 0.002800299 |
| 10 | -283.523015 | -232.520565 | +51.002450 | 0.228059 | 0.189085 | 0.007282700 | 0.001309411 |
| 20 | -555.766203 | -259.656648 | +296.109555 | 0.153292 | 0.256022 | 0.001460180 | 0.003928697 |
| **30 (fixed primary)** | **-644.966810** | **-485.429355** | **+159.537455** | **0.152040** | **0.190837** | **0.010846485** | **0.003328549** |

At the fixed endpoint, joint minus detach is +0.106358 raw J per step, +0.038796
QoS ratio, +1.163887 Mbps delivered throughput (4.561212 → 5.725099), and -0.034002
mean return constraint cost (0.286961 → 0.252960). The primary is the complete summed
native J above, not its per-step scale or a selected intermediate panel. Endpoint native
J is higher in 7/8 evaluation worlds, QoS in 5/8, and return constraint cost is lower in
all eight. These are within-pair world contrasts, not eight independent training effects.

| Evaluation world | Detach native J | Joint native J | Difference |
| --- | ---: | ---: | ---: |
| 920001 | -206.369922 | -92.466751 | +113.903171 |
| 920002 | -321.181965 | -329.685840 | -8.503875 |
| 920003 | -403.833723 | -265.944135 | +137.889587 |
| 920004 | -153.209866 | -64.658938 | +88.550928 |
| 920005 | -1083.444584 | -809.707165 | +273.737418 |
| 920006 | -631.022376 | -520.089850 | +110.932526 |
| 920007 | -1685.831796 | -1269.152421 | +416.679374 |
| 920008 | -674.840248 | -531.729741 | +143.110507 |

Final common-fact MSE is 69.31% lower for joint. An independent float64 direct W10
convolution of the stored factual QoS reproduces detach/joint MSE as
0.010846486932 / 0.003328549872 on 23,856 valid agent predictions each; the small
rounding difference from the runner is within numerical tolerance. Both fact episodes
favor joint (0.011182898 → 0.003452623; 0.010510076 → 0.003204477). This fixed validation
distribution is narrow: the two W10 target means are 0.171591/0.170355, standard deviations
0.008294/0.006091, and ranges [0.166667, 0.200000]/[0.166667, 0.191667]. These descriptive
statistics were read after results. They are not a new fitted comparator or a replacement
forecast endpoint. Both trained endpoints have worse common-fact MSE than initialization;
relative improvement does not establish broadly accurate service prediction.

Risk scope is limited. Neither arm has a cutoff or depletion event in training or evaluation.
Detach has no charging; joint has only five occupied UAV charging steps and 1.388889 Wh
charger input, all in training rollout 24, lane 4. All evaluation charging quantities are
zero. Thus this comparison measures active return-risk penalties and delivered service,
but supplies no convincing charging-competition or failure-recovery result. The presence
of those mechanisms in S2 is not evidence that they were materially exercised here.

Joint runner wall is 9555.825 seconds (159.26 minutes), peak RSS 3,025,168 KiB. The
pair totals 17,874.132 seconds (297.90 minutes) of runner wall, 360,000 training and
96,000 evaluation transitions, plus the single shared 3000-transition fact collection.
Observed joint/detach wall ratio is 1.149. Different concurrent node workloads mean that
ratio does not isolate the auxiliary backward-pass overhead. No extra tuning fits occurred.

### B01 working explanation and next decision — 2026-09-22

Current published background was checked at `34ee0f2544de305c28598bc140d660910f5c5090`.
Owner pause remains lifted for this direction; Claude FSD remains paused and G33 frozen.
Background sections 1, 4, 6 and 7 constrain the update: keep native outcomes separate from
prediction, retain the fixed endpoint and costs, and distinguish evaluation worlds from
training replication. The new S1 dense-encoding adverse result concerns a different
intervention/host and neither validates nor vetoes this factual S7 pair.

**Strengthened:** this exact joint auxiliary package is technically active and can coincide
with a useful native improvement under the declared S7-S2 exposure. Its J contrast is
positive at every nonzero prewritten panel; endpoint service and return-risk components
both improve. The result is more than an own-rollout MSE improvement. It gives a concrete
reason to consider retaining the package for an independent training replication.

**Weakened or bounded:** the simple account that increasingly accurate factual predictions
track better control is inadequate. At rollout 20, joint has substantially higher J but
worse common-fact MSE; at rollout 10 it has higher J but lower QoS. Both J curves deteriorate
after their early best panel, and joint's endpoint improves only +36.262328 over the common
untrained J, while detach falls -123.275127. The validation facts are low-variation initial-
policy trajectories. We have not identified preservation of backhaul support, learned
charging coordination, a unique representation mechanism, or absolute controller competence.
The currently supported positive is a finite-training package observation in one seed pair.

**Unresolved:** whether the fixed-endpoint J/service benefit recurs under a fresh training
initialization, or primarily reflects this pair's particular trajectory of learning and
degradation. More worlds for these same policies cannot resolve that training uncertainty.
Changing targets/weights/architecture or extending the horizon now would mix this question
with a new intervention. No such modification is selected.

The DM's tentative choice is **keep for one unchanged exploratory replication pair**,
rather than adopt the package as a standard or enter confirmation immediately. Recurrence
can change the investment decision: a fresh pair with a compatible native benefit would
strengthen paying for a properly fixed confirmation; an adverse/mixed pair would weaken
the reason to continue this unchanged recipe without a concrete new discriminator.
This is not an instruction to train until a favorable result. The strongest alternative
is to retain B01 as a bounded observation and end current spending, because the comparator
degrades, the absolute service level is low and the next pair costs about five runner-hours.
Direct confirmation is another option only if the evidence justifies its larger fixed cost.

The reused programme Pro advice covers the original comparison and its proxy-only stopping
branch. It does not assess this now-observed positive-but-nonmonotonic package, narrow fact
distribution, or a concrete follow-on/confirmation choice. Seek one focused consultation
under constitution section 5 before selecting that next investment. No new fit is accepted.

## Pro question 2026-09-22 b01-native-gain-next-investment

Conversation: new (Jev account; its private URL remains only in local transport state).

Question: Does the complete B01 evidence warrant one unchanged exploratory replication pair,
direct fixed confirmation, or stopping current recipe spending, and what would the smallest
worthwhile next observation actually discriminate? Critique the tentative keep decision
above; no new architecture or target is required.

Standing: Read the complete paired result and working explanation immediately above and
both runner summaries. Joint has higher fixed-endpoint native J (+159.537455), QoS
(+0.038796) and lower return constraint cost (-0.034002), with lower common-fact MSE
(0.010846485 → 0.003328549). J favors joint at all three trained panels, but both curves
decline late; rollout-20 forecast ranking opposes the return ranking. There is one training
seed pair, eight shared evaluation worlds, two narrow initial-policy factual worlds, no
evaluation charging and no cutoff/depletion events. Do not turn those worlds into training
replicates or attribute every gain to service-prediction causality. Two fits cost 297.90
runner minutes. The initial panel/first collection/first native update agree exactly, and
the final checkpoints/counts/gradient paths were verified. No candidate was tuned after B01.

Prospective option, not an accepted launch: a B02 exploratory pair of exactly **2 fits**,
new training seed **910137**, the same scientific source `382643ca91cf764336f3311bc166275a5d2bbe97`,
180k transitions per arm and fixed rollout-30 primary on worlds 920001–920008. Detach would
create the new initialization's common facts on worlds 930001–930002, joint would load those
exact bytes, and no implementation/target/horizon change would occur. Budget scale is about
five runner-hours, 360k training / 96k evaluation transitions and one 3000-transition fact
collection, plus collection/reading. This would test recurrence on the declared evaluation
panel, not establish a training-population claim. No automatic third pair is proposed.
Direct confirmation would instead require its own actual claim, fixed plan and **3–5 fresh
seeds per arm** (6–10 fits, roughly 15–25 runner-hours at B01 cost), not relabeling B01/B02.
Stopping adds zero fits. Advice may reject all new spending or recommend a more discriminating
bounded action if justified; distinguish its fit and non-fit costs.

Context (all paths marked source_sha resolve at the full question commit supplied in the
send message; the following explicit revisions retain their separate meaning):

- Governance at source_sha: `docs/project/OPERATING_CONSTITUTION.md` sections 1–5, 7–8.
  The owner authorized this independent direction to reach a supported keep/revise/stop;
  owner pause is lifted here, G33 frozen, no cross-task messages. Advice is not approval.
- Methods at source_sha: `.agents/skills/hmasd-scientific-tools/SKILL.md`, sections
  Update the working explanation, Confirm a claim, Comparators and MARL information,
  Statistics, Cost and exposure, and Pro. Exploration can be informative without a
  population claim; confirmation uses its actual prospective claim/plan and fresh seeds.
- Shared background at explicit current-main revision `34ee0f2544de305c28598bc140d660910f5c5090`:
  `docs/research/RESEARCH.md` sections 1, 4, 6 and 7. These constrain proxy/control,
  finite-learning and independent-unit interpretation; they are revisable evidence.
- Prior advice at source_sha: `docs/research/archive/2026-09-21/RESEARCH.md`, whole-project
  evidence-led plan Answer sections “分支 A”, “每次观察如何改变路线”, and Decision sections
  “固定周期的后续问题” and “UAV 场景化”. Reuse its matched-head/gradient-isolation logic;
  the material new evidence is the completed native pair and the decision above.
- Evidence at source_sha: this NOTES B01 prospective binding, both completion entries and
  the working explanation; `runs/uav_service_auxiliary/b01_detach_910021_a01/summary.json`
  and `runs/uav_service_auxiliary/b01_joint_910021_a01/summary.json`, their configurations,
  manifests and progress. Binary facts/checkpoints are retained outside Git; their verified
  identities and direct-array readings are reported above, not remotely reverified by you.
- Frozen implementation/contract at `382643ca91cf764336f3311bc166275a5d2bbe97`:
  this NOTES through preflight, `experiments/candidates/uav_service_auxiliary/b01/native.py`
  and `auxiliary.py`, and `scripts/run_uav_service_auxiliary_b01.py`. Inspect exact paths
  only where needed to assess a disputed explanation; current methods do not rewrite B01.

Constraints: no training, no experiment launch, no edits outside this question's initially
empty `### Answer` subsection in `docs/research/candidates/uav_service_auxiliary/NOTES.md`
on branch `codex/uav-service-auxiliary`. Read immutable reasoning inputs, then fetch the
latest target file/blob SHA before writing; preserve every other byte and stop on overlapping
edits. Report the actual commit on success. If GitHub writeback fails, return the **complete
answer in chat**, not only a receipt, SHA or link. This is a direction-level decision, not
an owner-triggered Portfolio selection or permission to manage other tasks.

Return: what is strengthened, weakened and still unresolved; the strongest competing
interpretation and the smallest observation that can change the choice; whether the proposed
two-fit recurrence check is worth its cost relative to stopping or confirmation; any material
change needed to its scientific reading, with a differing prediction rather than a generic
rescue. For a confirmation recommendation explain the actual claim/precision/selection issue
still needing a fixed plan. Cite sources actually read, state decision-critical gaps, and
return `MATERIAL_DISSENT: yes/no` against the tentative keep-for-one-replication choice.

### Answer

#### 结论：保留一次配方不变的探索复现，不直接确认

**建议保留恰好一对新的、科学配方不变的 B02 探索训练；不把 B01 当作标准方案的采纳证据，也不现在购买 6–10 fits 的确认。** 在题目给出的用途和成本下，我的排序是：一次有停止分支的复现优先，其次是保存 B01 后停止当前 recipe 开支，最后才是现在直接确认。这是方向级投资建议，不是预算批准、实验启动或其他任务的管理指令。[^governance][^methods]

我对 tentative keep 的**投资选择没有实质异议**，但有两项重要限定：购买的是“固定有限训练下的包级原生收益能否在另一个训练实例重现”，不是“预测准确度提高导致控制改善”的确认；而且，题面 B02 的新 seed 与冻结生产入口存在真实不兼容，必须如第六节写实处理。**“科学配方不变”不等于“现有 CLI 已能执行 910137”。**[^runner][^native]

#### 一、B01 加强了什么：一个值得复查的原生包级阳性

B01 不是只有辅助头 MSE 的阳性。在预先固定的 rollout 30，八个世界完整原生回报之均值的 joint−detach 为 **+159.537455**；QoS 为 **+0.038796**，交付吞吐为 **+1.163887 Mbps**，return constraint cost 为 **−0.034002**。三个预写的训练后面板，J 差依次为 +51.002450、+296.109555、+159.537455。终点七个世界 J 有利、五个世界 QoS 有利、八个世界返航约束成本均更低，使“本次只改善了一个预测代理量”的解释不合适。但这些是同一训练对的重复评估与分量读数，不是三个或八个独立训练阳性。[^b01][^detach][^joint]

这项增量比较也有实质性的技术支撑。两臂有相同的初始化指纹与公共事实摘要，初始面板、第一次训练采集和第一次 native update 一致；实际训练均为 180,000 transitions、30 次更新阶段，原生五个模块均移动且优化器步骤数匹配。每次辅助阶段都有 5,964 个有效团队行、47,712 个 agent 样本和 30 个辅助优化步骤；detach 的表征梯度记录为零，joint 的 30 个阶段记录均为正。配置、启动清单及 progress 首尾记录与这一暴露和输入绑定相符。故已有理由将结果作为这套 joint 辅助优化包在本次受控比较中的原生效应观察，而不是未训练对照、初始化不匹配或名义上接通的辅助支路。[^detach][^joint][^binding]

冻结设计中，两边预测头都训练，只有 joint 的辅助损失继续更新 actor base/GRU；原生 RL 在两边均保留。这个 matched-head 对照适合回答“增加这条辅助更新路径是否有用”，即使 detach 的后期表现变差也不自动使比较失效。但它没有回答“是否胜过最佳可用控制器”，也没有把任务特定监督的作用与额外表征优化、训练稳定化等作用分开。joint 每阶段还有专属表征 Adam 更新；相同环境 transitions 不是相同计算量，更不能把它写成不增加训练工作的纯信息收益。[^contract][^auxiliary][^prior]

#### 二、被削弱的解释与仍然未决的内容

**被削弱的是简单的预测—控制单调故事，而不是已经观察到的 J 差。** rollout 20 的 joint J 好得多，公共事实 MSE 却更差；rollout 10 的 joint J 更高，QoS 却更低。它们分别说明：此处公共事实误差的排序不是原生回报排序的可靠替代，J 的改善也不保证每个服务分量在每个时点同向。相反，终点的服务与返航成本同时有利，是比单看 J 更具体的支持。不能选择其中最顺的面板来重写故事，也不能将这几次排序当成一项正式的中介因果检验。[^b01][^detach][^joint]

**晚期退化使实用性仍然很弱。** 两臂在已观测的 rollout 10 面板之后都退化。共同初始化 J 为 −521.691683；终点 joint 为 −485.429355，仅提高 +36.262328，而 detach 为 −644.966810，下降 −123.275127。恒等式 `159.537455 = 36.262328 − (−123.275127)`有助于看清绝对水平，但不能把这两个数的比例解释成“多少收益由对照崩坏因果造成”。joint 终点 QoS 约 0.191，且它的返航约束成本虽然低于 detach，仍高于共同初始化的约 0.227。这里没有建立总体合格的控制器、收敛、或训练使所有重要方面优于初始化。rollout 10 的较佳回报不能替换 rollout 30 主终点。[^b01][^detach][^joint]

**公共事实 MSE 的终点相对改善不证明广泛预测能力。** joint 相对 detach 的约 69.31% 降幅发生在同一套窄初始策略轨迹上；两边终点都比共同初始化 MSE 更差。公共事实一致性排除了“用不同验证轨迹给两个端点打分”这个混淆，却没有解决这些事实是否代表训练后策略访问分布的问题。NOTES 报告的两个事实目标均值约 0.17、标准差约 0.006–0.008，是结果后的描述，不是另一个已拟合的预测基线。不能据此补写“已击败常数预测器”，也不能借它替换冻结预测终点。[^b01][^native]

23,856 个有效 agent 预测也不是 23,856 个独立证据单位：W10 窗口相互重叠，代码将同一个团队服务目标广播到各 agent；两个事实 episode 更不是两个训练复现。辅助头仅通过训练梯度影响表征，其预测值不是当前 actor 的输入。因而“策略因读取了更准确的服务预测而改善”并非此实现所识别的作用路径。[^auxiliary][^native][^methods]

**风险与场景机制的边界不能扩大。** 所有评估充电量为零，两臂训练和评估都没有 cutoff/depletion 事件；joint 只在一次训练 rollout 的一个 lane 出现五个占用 UAV 充电步。故结果涉及交付服务和实际激活的返航风险惩罚，不足以支持充电竞争协调、故障恢复、失败率降低或广义安全保证。配置中存在机制不是机制已被充分检验的证据；也没有识别出“保持了回传支持”的具体因果链。共享背景中新 S1 dense-encoding 负结果属于不同干预/宿主，不能替这对 S7 数据投赞成或否决票。[^b01][^binding][^background]

尚未解决的、直接影响下一笔投入的问题是：**这个固定终点的相对原生收益会不会随新的训练实例重现，还是主要来自 910021 这一次学习轨迹的分化与退化时机？** 更广的预测能力、独特表征机制、绝对控制能力和未被充分暴露的充电/失败机制也未解决，但不应把它们全部变成下一对训练的附加任务。

#### 三、最强竞争解释及其不同预测

最强的继续理由不是“服务预测机制已证明”，而是：**在这个固定训练预算内，额外辅助表征更新可能稳定地改善包级净结果；即使主要作用是减轻退化，它仍可能值得使用。** 与它竞争的最强停止解释是：**两条尚不成熟的学习轨迹在 B01 中恰好分叉，joint 只是较晚或较轻地退化；再付约五小时未必能得到可用、可复现的控制增益。** 二者都容许 B01 的全部结果，并不需要否认真实梯度或终点差。[^b01][^auxiliary]

它们对 B02 的分歧在于：前一种解释使“新实例的固定终点仍有可兼容的 J／服务收益”更值得期待；后一种解释容许这种收益明显缩小、消失或翻转，而公共事实 MSE 优势仍然存在。这里的预测是待观察的方向性区分，不是由一个 seed 估计出的复现概率。

还应把“可复现的稳定化收益”与“服务预测语义特有的收益”分开。**它们都可能预测 B02 为正，所以 B02 无法单独区分这二者。** 不变复现可以削弱“一次轨迹巧合”的解释，却不能凭 J 与 MSE 再次同向，就识别唯一的服务预测中介机制。当前投资的对象是包级效用，故无需先添加新的机制对照；也不能在复现阴性后自动用“其实是正则化”来救回当前 recipe 的支出。[^methods][^prior]

#### 四、最小有价值的新观察：一个新的完整匹配训练对

在题面目标下，最小能够改变投资判断的训练观察仍是 **seed 910137 的 detach/joint 各一 fit**：每臂 180k transitions，保持原生算法、辅助目标 W10、优化设置、架构、信息条件和 episode/窗口语义不变；主读数保持 rollout 30、世界 920001–920008 的完整原生 J 差。对任一训练实例 s，读数是：

`delta_s = (1/8) * sum_w [J_joint(s, w, rollout=30) - J_detach(s, w, rollout=30)]`。

其中 J 是每个完整 episode 的**未改写奖励总和**，不是每步奖励替代品，也不是挑选的最佳 checkpoint。原有 0/10/20/30 面板及 QoS、吞吐、返航成本、事件/充电暴露继续作为解释材料。初始化到终点、早期面板到终点的变化可描述训练与退化，但不成为事后新主终点。[^contract][^b01]

两 fit 而不是一 fit 有必要：只把新 joint 与 B01 的旧 detach 相比会混入训练实例差异；对旧政策增加世界、重复 seed 910021、追加预测头拟合或延长旧训练，也不回答这次新实例复现问题。这里不推荐上述额外开支。[^methods][^background]

还有两个需要写准确的范围。第一，冻结 `NativeSpec.seed` 同时进入初始化、随机数状态、head seed offset 和训练环境的 `seed + lane`；新 seed 是**新的训练实例**，不是只改变网络初始化而固定其余随机过程的隔离实验。第二，B02 应由新的 detach 初始策略在 930001–930002 采一次 facts，joint 复用这些新事实的精确字节；相同事实世界编号不代表它与 B01 是同一组轨迹。MSE 应先在各自训练对内比较，不能把两对不同初始策略事实的绝对 MSE 混合成一个共同验证分布结论。[^native]

对下一次读数，我会按下表改变投资判断；这不是新增数值门槛或审批程序，而是使“复现后会改变选择”具有实际内容。

| B02 的固定终点观察 | 对解释与后续投入的影响 |
| --- | --- |
| J 与交付服务再次呈有意义的同向改善，风险分量没有抵销该收益 | 加强包级复现理由，值得再判断是否购买独立的固定确认；不要求精确重现 +159.537455，也不要求每个世界、每个中间面板都获胜，更不自动采纳。 |
| J／服务收益重现，但公共事实 MSE 不改善或反向 | 仍加强包级效用，同时进一步削弱“该验证 MSE 改善是控制收益必要条件”的解释；不能用代理量否决原生收益。 |
| MSE 改善但固定终点 J 无益，或新对的原生收益明显反向、服务/风险混合 | 削弱继续当前不变 recipe 的理由；我的默认建议转为停止当前 recipe 开支，保留两对观察，不用早期最佳面板、调权重、延长训练或自动第三对挽救。 |
| 仅极小的 J 正差，或只重现“仍很差的控制器少退化一些”，不足以改变是否值得确认的判断 | 不把正号机械解释成下一笔确认经费的理由；保留窄的有限训练观察，停止仍然合理。 |

应并列报告 B01、B02 的各自差值和绝对表现，不能用两对均值掩盖新对的反转。即使两对都正，也只是两个训练实例的探索读数，不能把 16 个评估世界或全部 agent/时间步变成训练总体样本。反之，一次反向复现也不证明所有 seed 上都无效；它改变的是当前 recipe 的投资理由。技术无效的运行则不是科学阴性，更不在本建议中自动获得替换 fit。[^methods][^background]

#### 五、为什么这一次值得考虑，而不是直接停止或确认

B01 已花费 **297.90 runner 分钟**，这是沉没成本，不是续资理由。真正的继续理由是：此处有固定终点的原生收益，而最大未解不确定性恰是训练实例依赖；一对新的匹配训练与该不确定性直接对应。题面 B02 的新增规模是 **2 fits、约 5 runner-hours、360k training / 96k evaluation transitions，以及一次 3,000-transition 事实采集**。事实虽在两臂 summary 中都有计数，物理上只采一次，joint 是加载，不应重复计入采集暴露。复制、读取与结果整理另有非-fit 成本，不能称为零。[^b01][^native]

停止的最强理由仍成立：原生对照晚期退化、joint 绝对服务水平低、下一对也不能确认机制或总体优越性。**我仍略偏向买这一对，是因为它的正反两种结果都能改变当前投资，而不是因为一对足以“证明有效”。** 倘若无论 B02 如何都准备继续确认，或者即使兼容收益重现也绝不愿再投入，那么这次探索的决策价值就大幅减小：前者应面对一次真正固定确认的成本，后者直接停止更一致。材料没有提供科研效用、机会成本或最小值得保留增益的数值，因此我不声称计算出了最优投资概率或净收益。[^methods]

直接确认的题面规模是 **6–10 fits、约 15–25 runner-hours**。如果先 B02 再确认，从现在起合计会是 **8–12 fits、约 20–30 runner-hours**，外加非-fit 工作；不能把 B02 描述为便宜的确认替代品或免费前置步骤。它的价值在于有机会避免为不复现的 recipe 支付更大一笔固定成本，同时保留在复现后认真确认的理由。当前一次阳性且退化明显，尚不足以让我优先购买这笔较大的成本。[^b01]

这些时长是按 B01 估计的规模，不是未来运行保证。joint/detach 已观察 wall ratio 约 1.149，但并行节点负载不同，不能将其作为隔离测得的辅助反向传播开销。训练预算、评估/事实采集、实际资源和额外优化工作应各自保留，不能只报一个“同预算”标签。[^b01][^binding][^auxiliary]

#### 六、必须纠正的具体执行描述：冻结 CLI 不支持所提新 seed

这是本次精确源码阅读发现的冲突，不是我执行了试跑。在 `382643ca91cf764336f3311bc166275a5d2bbe97` 的生产脚本中，`--seed` 被限定为 `choices=(910021,)`；`main()` 调用 `run_native()` 时也没有传递 `args.seed` 或 `spec`。而冻结 `native.py` 的默认 `NativeSpec.seed` 是 910021，未传 spec 时就构造该默认 spec。[^runner][^native]

因此，**现有生产入口会拒绝 `--seed 910137`；只放宽 choices 而不把 seed 传入 NativeSpec，仍不会得到题目要的新训练实例。** 单独改输出名、清单标签或问题文字都不能产生训练复现。该问题不否定已完成、原本就使用 910021 的 B01。

底层已有显式 `NativeSpec(seed=...)` 接口，因而所需科学算法并不必变。若 DM 选择继续，最小处理应限于把新 seed 真实绑定到已有 spec 的入口/调用，并保留现有 admission 与来源身份约束；参数必须实际到达初始化、训练环境和头部 seed，且新对的两臂仍共享初始化与事实。**科学核心可沿用冻结来源，但若入口发布内容改变，实际 launch/source revision 必须如实记录，不能冒称仍由旧的完整生产入口直接执行。** 这项参数连通性与来源核对是零科学 fit 的非-fit 工作，不是换 target/架构或增加科学审批门槛；其实际人工与正确性检查成本尚未给出。[^native][^runner]

本回答不修改冻结 B01、生产代码或任何其他文件，也不绕过 admission 启动任务。已读材料没有提供另一个已经兼容 910137 的生产入口；**若“完全不变”还要求现有入口每个字节也不得变化，则题面 B02 不能由该入口按字面实现，不应发起或把旧 seed 的运行误报为新复现。** 我保留的是一次配方不变复现的投资建议，不是对当前执行描述的无条件认可。

#### 七、现在不推荐确认；将来确认仍需固定什么

若 B02 提供了足够有用的兼容原生收益，最窄且与现有比较相符的确认命题可以是：在**明确的训练 seed 抽样规则**下，同一 S7-S2 配方、180k 预算和固定评估世界面板，joint 相对 matched detach 的平均 `delta_s` 为正，或者超过事先具有决策意义的幅度。它不是“普遍更准确的预测导致更好 UAV 协调”，也不是对充电竞争/故障恢复的确认。[^methods][^contract]

届时需要在结果前固定实际采用三个还是五个 fresh seed 对、完整 seed 清单、主终点、比较对象、训练暴露、停止规则，以及什么区间精度或效应幅度足以支持该命题。**3–5 seeds/arm 是题面确认规模，不是已有功效保证。** B01 只有一个训练对，无法提供可靠的跨训练方差估计；不能拿八个世界的离散度冒充它。若结论还要求服务与风险同时满足某种条件，这些分量及组合判读也须在该确认计划中说清，不能事后挑有利指标。[^methods][^b01]

B01 与用于选路的 B02 继续作为探索证据，不能改名成为 fresh confirmation。继续使用相同八个世界，能确认的也首先是该固定面板上的跨训练命题；扩展到世界总体需另有相符的设计与成本，不是这一次咨询附赠的结论。这里是在说明未来实际命题与选择/精度问题，并未增加一个新的批准程序，也未建议现在启动确认。[^methods][^background]

#### 八、来源范围、未复核内容与最终立场

本答复实际依据：source_sha 的治理指定章节、科学方法指定章节、NOTES 的 B01 前瞻绑定/两次完成记录/working explanation/本题、两份**完整** runner summary、两份配置与启动 manifest，以及 progress 的 facts-ready/初始评估和终点段；另读了显式 `34ee0f2544de305c28598bc140d660910f5c5090` 背景第 1、4、6、7 节和指定旧咨询 Answer/Decision 段。冻结 `382643ca91cf764336f3311bc166275a5d2bbe97` 的 NOTES 到 preflight、native runner、生产入口，以及 auxiliary 的目标/信息/梯度/优化更新路径，用于核对解释和种子绑定。没有用移动分支替换科学输入；移动分支只用于写回目标的并发核对。[^governance][^methods][^background][^prior][^b01][^binding][^contract][^native][^runner][^auxiliary]

**我没有取得并重新计算仓库外 facts、预测数组和 checkpoint 的二进制校验。** “13 文件 SHA256 一致、checkpoint 可加载且浮点张量有限、float64 直接窗口重算吻合”等，是已读 NOTES 中 DM 的已报告核验，不是本次独立远程复核。progress 中间逐百步记录也没有逐行重审；完整训练更新、全部评估面板、训练 rollout 与资源曲线来自已完整读过的两份 summary。没有缺失到必须以记忆补全的核心文字来源；尚缺的新训练观察、跨 seed 方差、可执行的新 seed 入口绑定和实际确认计划，则分别限制复现、精度和执行可行性，不应假装已满足。[^b01][^detach][^joint]

最终建议是：**保留一次、恰好两 fit 的科学配方不变复现机会，先把已发现的种子入口描述写实；负向或不足以改变投资的结果应能结束当前 recipe 开支。不要直接确认，不要按预测代理量选 checkpoint，不要承诺自动第三对。**

`MATERIAL_DISSENT: no`

[^governance]: 固定治理：[OPERATING_CONSTITUTION.md，第 1–5、7–8 节](https://github.com/CartmanFatass/My-paper-code/blob/53c013bded444f72e4268bb395735a6051a49859/docs/project/OPERATING_CONSTITUTION.md)。本题给出的当前 owner 指令与独立方向权限优先于历史聊天和旧暂停说明；建议不是批准。

[^methods]: 固定方法：[hmasd-scientific-tools/SKILL.md](https://github.com/CartmanFatass/My-paper-code/blob/53c013bded444f72e4268bb395735a6051a49859/.agents/skills/hmasd-scientific-tools/SKILL.md)，Update the working explanation、Confirm a claim、Comparators and MARL information、Statistics、Cost and exposure、Pro。

[^background]: 显式背景版本：[RESEARCH.md，第 1、4、6、7 节](https://github.com/CartmanFatass/My-paper-code/blob/34ee0f2544de305c28598bc140d660910f5c5090/docs/research/RESEARCH.md)。

[^prior]: 指定旧咨询：[archive/2026-09-21/RESEARCH.md](https://github.com/CartmanFatass/My-paper-code/blob/53c013bded444f72e4268bb395735a6051a49859/docs/research/archive/2026-09-21/RESEARCH.md)，whole-project evidence-led plan 的 Answer“分支 A”“每次观察如何改变路线”，Decision“固定周期的后续问题”“UAV 场景化”。

[^b01]: 固定问题与已报告配对核验：[NOTES.md](https://github.com/CartmanFatass/My-paper-code/blob/53c013bded444f72e4268bb395735a6051a49859/docs/research/candidates/uav_service_auxiliary/NOTES.md)，B01 prospective comparison、detach complete、joint complete and paired reading、working explanation、b01-native-gain-next-investment 问题。

[^detach]: 完整 [detach summary.json](https://github.com/CartmanFatass/My-paper-code/blob/53c013bded444f72e4268bb395735a6051a49859/runs/uav_service_auxiliary/b01_detach_910021_a01/summary.json)，evaluations、updates、training_rollouts、counts、rss_curve、optimizer_steps、wall_seconds。

[^joint]: 完整 [joint summary.json](https://github.com/CartmanFatass/My-paper-code/blob/53c013bded444f72e4268bb395735a6051a49859/runs/uav_service_auxiliary/b01_joint_910021_a01/summary.json)，同上字段。

[^binding]: 固定版本两臂的 [detach config](https://github.com/CartmanFatass/My-paper-code/blob/53c013bded444f72e4268bb395735a6051a49859/runs/uav_service_auxiliary/b01_detach_910021_a01/config.json)、[joint config](https://github.com/CartmanFatass/My-paper-code/blob/53c013bded444f72e4268bb395735a6051a49859/runs/uav_service_auxiliary/b01_joint_910021_a01/config.json)、[detach launch-manifest](https://github.com/CartmanFatass/My-paper-code/blob/53c013bded444f72e4268bb395735a6051a49859/runs/uav_service_auxiliary/b01_detach_910021_a01/launch-manifest.json)、[joint launch-manifest](https://github.com/CartmanFatass/My-paper-code/blob/53c013bded444f72e4268bb395735a6051a49859/runs/uav_service_auxiliary/b01_joint_910021_a01/launch-manifest.json)，以及 [detach progress](https://github.com/CartmanFatass/My-paper-code/blob/53c013bded444f72e4268bb395735a6051a49859/runs/uav_service_auxiliary/b01_detach_910021_a01/progress.jsonl) / [joint progress](https://github.com/CartmanFatass/My-paper-code/blob/53c013bded444f72e4268bb395735a6051a49859/runs/uav_service_auxiliary/b01_joint_910021_a01/progress.jsonl) 的起始身份与终点记录。

[^contract]: 冻结 [NOTES.md 至 B01 native acceptance and preflight](https://github.com/CartmanFatass/My-paper-code/blob/382643ca91cf764336f3311bc166275a5d2bbe97/docs/research/candidates/uav_service_auxiliary/NOTES.md)：matched-head、W10、信息边界、辅助优化、共同事实、主终点和有限暴露契约。

[^auxiliary]: 冻结 [auxiliary.py](https://github.com/CartmanFatass/My-paper-code/blob/382643ca91cf764336f3311bc166275a5d2bbe97/experiments/candidates/uav_service_auxiliary/b01/auxiliary.py)：future_window_targets、AuxiliaryReplay 初始化、_inputs、_representations、update。

[^native]: 冻结 [native.py](https://github.com/CartmanFatass/My-paper-code/blob/382643ca91cf764336f3311bc166275a5d2bbe97/experiments/candidates/uav_service_auxiliary/b01/native.py)：NativeSpec、make_config、evaluation_panel、write_facts、verify_and_copy_facts、prediction_replay、run_native。

[^runner]: 冻结 [scripts/run_uav_service_auxiliary_b01.py](https://github.com/CartmanFatass/My-paper-code/blob/382643ca91cf764336f3311bc166275a5d2bbe97/scripts/run_uav_service_auxiliary_b01.py)：parse_args 的 seed choices 与 main 的 run_native 调用。对新 seed 的可行性结论来自源码阅读，未执行脚本。

## 2026-09-22 — Pro reading, adoption and B02 selection

The single consultation key is
`hmasd:9bb9395a71f2a673ecf1e24524eba4fa6b20b6bac2c77efcd307021b692d362c`.
`deliver` verified the actual answer commit `c1f7fdeef4813af4ffd023d75ef7bcf39326351e`:
only this file changed, only the previously empty Answer was filled, and the question and
all other bytes are unchanged. The DM read all 12,697 answer characters, rather than
accepting the 828-character chat receipt as the answer. The browser observer closed its
owned tab; no tab for this private conversation remains. No question was resent.

Adopt the recommendation for exactly one unchanged scientific replication pair, and its
limits. B01's positive complete native contrast gives this observation a concrete use:
it tests dependence on the particular training instance/late degradation, without claiming
to identify prediction semantics versus a more generic stabilization effect. Stronger MSE
alone would not justify continued spending. A compatible, useful J/service result can justify
considering a separately specified confirmation; a reversal, adverse service/risk tradeoff,
or a gain too small to change the investment judgment defaults to ending this recipe's
current spending. There is no automatic third exploratory pair and no confirmation selected.
Report the two seed-pair outcomes separately, including absolute levels and the fixed curves;
do not average away a reversal or select an early checkpoint. A technically invalid attempt
is separate from scientific adversity and does not automatically authorize a replacement.

The answer's consequential source claim was checked against the production entry: `--seed`
only accepts 910021 and is not passed to `run_native`, whose default NativeSpec also uses
910021. This is a real B02 execution mismatch, not a flaw in the completed B01. Amend the
earlier proposed *exact source* statement: B02 preserves all scientific modules/configuration,
but needs a newly published entrypoint revision that actually binds the selected seed.
Both B02 arms will use that same new revision. B01 remains at its original source and outputs.

The answer did not independently recheck ignored binary arrays/checkpoints; its provenance
qualification is correct. Its native contrasts, counts and code interpretation agree with
the DM's readings. The overlapping W10 windows and broadcast team labels do not constitute
23,856 independent forecast observations. Fresh `seed` changes initialization, RNG streams,
head initialization and training worlds together: B02 is a new **training instance**, not
an isolated intervention on network initialization. B02's initial-policy factual trajectories
will differ from B01 even though the held-out world numbers stay the same; forecast contrasts
remain within each pair. No scientific rejection of the advice is needed; the old exact-CLI
claim and any broader forecast/charging interpretation are explicitly bounded above.

Current published main was checked at `1bca4f7cd69d91146c9a220213927dfddf46b34a`.
The relevant native-outcome, finite-training, cost and independent-unit background remains
applicable. Other directions' new results do not change this fixed intervention. Owner pause
is lifted for this lead; G33 and Claude FSD restrictions remain. The new observation is worth
its approximately five runner-hours because both recurrence and failure to recur can change
whether a larger confirmation is worth paying for; B01's sunk cost is not the justification.

### B02 prospective binding and seed-entry L0

Choose **2 new exploratory fits**, detach then joint, training seed **910137**, outputs
`runs/uav_service_auxiliary/b02_detach_910137_a01` and
`runs/uav_service_auxiliary/b02_joint_910137_a01`. All other scientific settings remain B01:
S7-S2 v3/reward v2/arm C, N8/k10, four lanes ×1500 steps ×30 rollouts =180,000 transitions
per arm; W10 factual QoS, the same actor/head/representation optimizer and replay semantics,
CUDA FP32, four Torch CPU threads, TF32 off, and native update/exposure unchanged.
Use the same prewritten 0/10/20/30 panels on worlds 920001–920008. Primary is the paired
rollout-30 mean of complete summed raw native J, joint minus detach, with QoS/throughput,
return constraint cost, event/charging exposure and cost retained. No best checkpoint,
extension, tuning or new target is selected. These are exploration data, not confirmation.

New detach collects one new initial-policy fact file on worlds 930001–930002 before training;
new joint must load those exact bytes and match the new initialized-model fingerprint.
Do not reuse B01 facts or regenerate them for joint. Stage the accepted facts outside the
author checkout under the configured `/home/wu/hmasd-inputs` root, retaining their digest.
The comparison consumes 360k training / 96k evaluation transitions plus one 3000-transition
fact collection, estimated from B01 at about five runner-hours, with actual costs recorded.
Total planned direction cost is now **4 fits**, of which 2 are complete and these 2 unstarted.
Fresh native actual-node admission remains required on `wsl_4070` before each sequential fit.

L0 deliverable: update only `scripts/run_uav_service_auxiliary_b01.py` so its existing
admission-guarded production call can execute declared seed 910137 as well as 910021, and
actually constructs/passes `NativeSpec(seed=args.seed)`. Keep the historical seed's behavior,
all other arguments, source identity checking and admission-before-scientific-effects order.
Keep `native.py`, `auxiliary.py`, the learner/environment/evaluator, and all B01 artifacts
unchanged. Own the corresponding narrow regression in
`tests/experiments/candidates/uav_service_auxiliary/b01/test_native.py`.
Check actual spec forwarding for both allowed seeds/arms, the unchanged default scientific
fields, and the admission guard. Reuse prior unchanged native/CUDA integration evidence.
Independent Reviewer reviews this seed/result-identity change. This is zero scientific fits
of correctness work; stop for any need to change scientific semantics rather than expanding
the patch. The actual launch source will be the committed, pushed, reviewed new revision.

### B02 seed-entry accepted for execution — 2026-09-22

The DM accepted the two-file entry/test diff after independent Reviewer review. Production
now accepts only the declared seeds 910021 and 910137 and passes the selected value through
`NativeSpec(seed=args.seed)` after admission and source-SHA verification. The default spec
is unchanged for 910021. No scientific module changed from B01's frozen source. Source
inspection confirms the spec reaches RNG/model initialization, sampler, config/training
worlds, auxiliary initialization and summary identity; existing fact digest/fingerprint
checks remain intact. The final launch must record the new source revision truthfully.

Four focused launcher cases (both seeds × both arms) passed locally in 3.08 seconds;
the independent Reviewer reproduced all four in 1.82 seconds and found no material issue.
These tests stub the scientific loop and do not constitute a training/CUDA run. The
unchanged full native/CUDA integration evidence from B01 is reused; real B02 config/seed,
fingerprints, counts and final outcomes will still be read from the admitted runs.
Checks created zero scientific fits. Initial preparation reports 13,179,844 KiB available
RAM and 4864 MiB free GPU on `wsl_4070`; the actual native admission will recheck resources
and current owner/lead immediately before starting the first B02 fit.
