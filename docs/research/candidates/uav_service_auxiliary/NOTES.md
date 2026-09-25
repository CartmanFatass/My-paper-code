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

### B02 pre-training control-reference correction

Supervisor `uav-service-b02-detach-910137-a01` was refused before training at
`2026-09-22T09:01:21Z`, code 4 after 16 seconds: `canonical control checkout has not fetched
the published control head; sync it before launch`. Native same-output status reports that
the reference does not exist. This policy check precedes snapshot/claim/output creation
and child release; no B02 fit or worker was accepted. Preserve the supervisor log.
Refresh only the canonical repository's published main reference, without moving its
checkout or any live process. Then use the same published scientific inputs
`30401722b14c208bf5330ab66e967c94b3df8a36`, seed, arm, horizon and unused output tag.
This is a resolved pre-training control-data refusal, not a restarted training attempt.

### B02 detach accepted — 2026-09-22 02:02 PDT

After fetching the canonical control reference to `1bca4f7cd69d91146c9a220213927dfddf46b34a`,
supervisor `uav-service-b02-detach-910137-synced-a01` completed native admission at
`2026-09-22T09:02:54.446158Z`. This is the first accepted B02 fit. It uses the published,
reviewed source `30401722b14c208bf5330ab66e967c94b3df8a36` in the retained source snapshot
`/home/wu/projects/HMASD/.git/hmasd-launch-sources/7ff125f86a384427b106b03b822686a5`.
The author checkout and all B01 outputs remain intact. The real runner config records
`spec.seed=active.seed=910137`, with the prewritten 30 × 4 × 1500 training exposure,
evaluation/fact worlds and native S7 settings. No additional scientific setting changed.

The accepted output is `runs/uav_service_auxiliary/b02_detach_910137_a01` under the remote
owned root `/home/wu/hmasd-worktrees/uav-service-auxiliary-a335`. Its operation reference is
`/home/wu/projects/HMASD/.git/hmasd-admission/18814e12d341f265ea6f61e01c1d76caacf84bdb123dec64d2ba2ef736f30c95.json`.
Supervisor PID/session 173846 has start ticks 43144873; runner PID 173847 in that session
has start ticks 43144876; both belong to boot `bb732fcb-1a33-4659-a786-331110ae41d3`.
The `09:08:13.563580Z` native observation found both identities running, consistent records,
and no exit witness. Actual-node admission measured 13,626,494,976 available physical bytes,
passed the 4 GiB floor, and observed current main/lead before release. Local copies retain
the launcher manifest, preflight, status and runner config. Acceptance is not completion
or scientific acceptance; collect the full outputs before reading an effect.

Cost is now **4 planned fits: 3 accepted, of which 2 complete and 1 running; 1 unstarted**.
The earlier 15-second B01 path refusal and 16-second B02 control-reference refusal are
separate pre-training support costs, not additional fits. B02 joint remains unstarted and
must use this same source plus the new detach fact bytes/digest and initialized-model
fingerprint, after detach completion and fresh native admission. Observe the retained
operation through `hmasd_wait`; a checkpoint neither repeats launch nor expands the plan.

### B02 detach complete and original joint remains — 2026-09-22 03:59 PDT

The retained detach operation exited with a valid code-0 witness at
`2026-09-22T10:59:19.735903Z`; native observation at `10:59:31.749705Z` reported consistent
records and absent completed processes. The DM read the complete result fields, all four
evaluation panels/worlds, all 30 training/update rows and resource curve, and retained all
13 original output files locally. Every copied file matches its remote SHA256. The runner
summary is COMPLETE with no failure: 180,000 training transitions, 30 updates, 120 complete
1500-step training episodes, 32 complete evaluation episodes / 48,000 transitions, and one
3000-transition factual collection. All episodes end at the time limit; there are zero
straddling collector boundaries. Source remains `30401722b14c208bf5330ab66e967c94b3df8a36`,
seed 910137, CUDA FP32, four Torch threads and the prewritten scientific configuration.

All native update scalars are finite and every learner module moved. Optimizer steps are
high 2250, low actor/critic 67500 each, team discriminator 450 and individual discriminator
1800. Each auxiliary pass has 5964 valid team rows / 47,712 agent samples and 30 optimizer
steps. The auxiliary representation gradient is exactly zero in all 30 detach passes;
head gradient norms range from 0.1086981371 to 3.0616805553 before clipping. Both final
checkpoints load, and all stored floating tensors are finite. Every native evaluation
aggregate was independently recomputed from the eight complete world rows.

| Rollout | Mean complete raw native J | QoS / step | Throughput Mbps | Return constraint cost / step | Common-fact MSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0 | -570.8365503404 | 0.1087515285 | 3.2625458559 | 0.2407932113 | 0.02035683773 |
| 10 | -342.0843405034 | 0.1789423854 | 5.3682715616 | 0.1991881923 | 0.00868157874 |
| 20 | -27.3218782269 | 0.1812576436 | 5.4377293077 | 0.0955760265 | 0.07037506257 |
| **30 (fixed endpoint)** | **-670.3937326855** | **0.1402308206** | **4.2069246167** | **0.2894672194** | **0.00415097860** |

The fixed endpoint is 99.557182345 worse than initialization in J, despite higher QoS and
lower initial-policy factual MSE. From rollout 20 to 30, J falls by 643.071854459 as return
constraint cost rises. This strengthens the working concern about late finite-training
degradation and keeps forecast error separate from policy utility. It does not identify
an auxiliary effect: this is only B02's detach arm. Do not select the earlier endpoint,
change the horizon or compare B02 MSE directly with B01's different factual trajectories.
The already declared joint fit is still needed for this pair's discriminating observation.

There are zero cutoff or depletion events in all training and evaluation. Training rollout
12, lane 4 has exactly one occupied-UAV charging time step and 0.2777777778 Wh charger input;
all other training charging quantities and every evaluation charging quantity are zero.
Record this small exposure rather than inheriting B01 detach's all-zero training statement.
It does not establish charging competition or a recovery benefit. No shared background
revision beyond the existing non-monotonicity/exposure caveat is supported by this single arm.

The new facts are 4,572,909 bytes with SHA256
`7d3120283c569b45290621f0c3a4934ad885e98c3859da004242c6f06ac6d359` and initial-model fingerprint
`dec0015986e35ff11d21bbf0d56558d1c0605f61597479576418ba2f070c6b3f`.
An independent float64 direct W10 calculation from the saved QoS/done arrays gives final
MSE **0.00415097850735455**, matching the runner, with 23,856 valid agent predictions.
The two episodes' target means are 0.169971687 and 0.167087670, standard deviations
0.008518633 and 0.001445556; this remains a narrow initial-policy factual distribution.
Overlapping windows and repeated team labels are not independent experimental units.
Final checkpoint SHA256 values are agent
`0931183e971aeaf0c2406e4969b5fb30d469174b0ffbc7efc2cb2578de49ae24` and auxiliary
`4bc51a9ae8d42503242bd8a8d12fadf3f2a9a09b1bef6b839ac5ecbe9927370e`.

Actual runner wall is **6982.896684170 seconds / 116.381611403 minutes**, peak RSS
3,024,640 KiB. Direction cost is now **3 complete fits, 1 declared unstarted fit**,
414.28 runner minutes for the completed fits, plus the separately recorded 15/16-second
pre-training refusals. Verification/staging creates no scientific fits.

Continue only the original B02 joint fit, seed 910137, source
`30401722b14c208bf5330ab66e967c94b3df8a36`, output `runs/uav_service_auxiliary/b02_joint_910137_a01`.
The exact new fact bytes have been staged and rehashed at
`/home/wu/hmasd-inputs/uav_service_auxiliary/b02/facts_7d3120283c569b45290621f0c3a4934ad885e98c3859da004242c6f06ac6d359.npz`.
The joint runner must match this digest and initial-model fingerprint; generate no replacement
facts. Current published main was read at `2f7aac82eb8371c527b50a5e8fecb0134ee19486` and the
remote canonical reference refreshed: owner pause remains lifted for this lead, G33 frozen,
and Claude FSD paused. Preparation reports 14,503,952 KiB available RAM and 7948 MiB free GPU;
native admission rechecks actual-node resources and policy before release. The completed
Pro advice still applies to this unchanged pair; no new question or automatic extra fit.

### B02 joint accepted — 2026-09-22 04:07 PDT

Supervisor `uav-service-b02-joint-910137-a01` completed native admission at
`2026-09-22T11:07:32.438157Z` on `wsl_4070`, without a new refusal or retry. The retained
[manifest](../../../../runs/uav_service_auxiliary/b02_joint_910137_a01/launch-manifest.json)
binds the original source `30401722b14c208bf5330ab66e967c94b3df8a36`, seed 910137 and exact
staged facts. Its operation reference is
`/home/wu/projects/HMASD/.git/hmasd-admission/6f9d9d249716c8bfc644954d3b3990c8b064d62646b209b451bbb2f7a0025e65.json`;
the snapshot is `/home/wu/projects/HMASD/.git/hmasd-launch-sources/fda709fc31804eea99a8c60ba7f19cc7`.
The `11:08:11.463672Z` status reports consistent, running supervisor/runner identities
(PIDs 192886/192887, start ticks 43869112/43869115, boot
`bb732fcb-1a33-4659-a786-331110ae41d3`) and no exit witness. The actual admission passed
with 14,821,879,808 available physical bytes and current control head `2f7aac82e`.

The runner has independently verified the exact common-fact digest
`7d3120283c569b45290621f0c3a4934ad885e98c3859da004242c6f06ac6d359` and initialized-model
fingerprint `dec0015986e35ff11d21bbf0d56558d1c0605f61597479576418ba2f070c6b3f` against detach.
The two actual configs match apart from their inactive baseline file's snapshot prefix;
both actual seed fields are 910137. Joint loads the two factual episodes, with no extra
fact collection. Summary is still INCOMPLETE with no failure; no pair effect is read yet.

All **4 planned fits are now accepted: 3 complete and 1 running**, with no unstarted fit
or further batch selected. Observe this same joint operation through completion or the next
bounded checkpoint; the completed detach event is consumed. Then verify the full joint
outputs and read the fixed pair under the already recorded Pro-informed stopping rule.

## B02 complete comparison and bounded keep decision — 2026-09-22

### Completion and paired technical reading

The original joint operation exited with a valid code-0 witness at
`2026-09-22T12:42:24.670614Z`; native observation at `12:42:43.556488Z` found consistent
records and absent completed supervisor/runner identities. This is the same accepted source
`30401722b14c208bf5330ab66e967c94b3df8a36`, seed 910137, output
`runs/uav_service_auxiliary/b02_joint_910137_a01`. No worker was restarted or replaced.
The DM collected and read all result fields, all four evaluation panels and their world rows,
all 30 training/update rows and the resource curve, and checked the complete progress stream.
All 13 copied files match their remote sizes and SHA256 values. The original binary arrays,
checkpoints and logs remain locally and under the owned remote output root
`/home/wu/hmasd-worktrees/uav-service-auxiliary-a335/runs/uav_service_auxiliary/`;
the runner-written text evidence is published with this notebook.

Joint is COMPLETE with no failure: 180,000 training transitions, 30 rollouts, 120 complete
training episodes, 32 evaluation episodes / 48,000 transitions, and two loaded factual
episodes / 3000 transitions. All training and evaluation episodes reach the 1500-step time
limit, with no straddling collector boundary. Progress contains one facts-ready event, four
evaluations, 450 collection checkpoints and 30 rollout completions. Actual config remains
CUDA FP32, four Torch threads and the prewritten scientific recipe. Native optimizer steps
are 2250 high, 67500 low actor and critic each, 450 team discriminator and 1800 individual
discriminator; every native learner module moved and every recorded update scalar is finite.
Each auxiliary pass uses 5964 valid team rows / 47,712 agent samples and 30 optimizer steps.
Joint representation gradient norms are positive in all 30 passes, ranging from
0.063767396 to 1.410942435 before clipping; head norms range from 0.090973467 to 1.478754044.
Detach's auxiliary representation gradient remains exactly zero in every pass.

Rechecking the completed pair confirms identical factual bytes/digest and initialized-model
fingerprint, identical full initial evaluation, first training rollout and first native
update. Both actual seed fields are 910137. Configs match except the inactive baseline
file's source-snapshot prefix. The facts digest is
`7d3120283c569b45290621f0c3a4934ad885e98c3859da004242c6f06ac6d359`; the initial-model digest is
`dec0015986e35ff11d21bbf0d56558d1c0605f61597479576418ba2f070c6b3f`.
All native aggregates were independently recomputed from the eight complete world rows.

The final agent checkpoint SHA256 is
`3c00b9ca8218f6f97718800e0f2f2885f4b66ba9c6076e9712aa267f9c4aa052`;
the auxiliary checkpoint SHA256 is
`9ad6134ec05189ba12a56bf3518040f79ca30d2f25eba88c3d518f1dcad3c336`.
Both load on CPU; all floating tensors are finite (agent: 694 tensors / 17,493,733 floating
elements; auxiliary: 46 tensors / 1,159,057 floating elements). Auxiliary state binds joint,
head seed 1110137, W10, chunk 50, head/representation rates 3e-4/3e-5, clipping 0.5 and 30
updates. All saved numeric fact/prediction arrays are finite. An independent float64 direct
window calculation from QoS/done reproduces the validity masks and gives final joint MSE
**0.009332327272**, agreeing with the runner's **0.009332324897** within float32 rounding.
There are 1491 complete windows per factual episode, 23,856 valid agent predictions total;
the largest saved-target error is 2.84e-8. These overlapping windows and broadcast labels
remain dependent observations, not additional training instances.

### Fixed endpoint, curves and adverse evidence

Each J is the mean of eight complete episodes' raw native reward sums. The endpoint remains
rollout 30; neither the earlier detach peak nor a more favorable MSE checkpoint is selected.

| Rollout | Detach J | Joint J | Joint minus detach J | Detach QoS / step | Joint QoS / step | Detach common-fact MSE | Joint common-fact MSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | -570.8365503404 | -570.8365503404 | 0 | 0.1087515285 | 0.1087515285 | 0.02035683773 | 0.02035683773 |
| 10 | -342.0843405034 | -277.0730725246 | +65.0112679788 | 0.1789423854 | 0.2029723136 | 0.00868157874 | 0.00820370019 |
| 20 | -27.3218782269 | -104.7549392818 | -77.4330610550 | 0.1812576436 | 0.2830555427 | 0.07037506257 | 0.00979407692 |
| **30** | **-670.3937326855** | **-266.8824267825** | **+403.5113059030** | **0.1402308206** | **0.2202640597** | **0.00415097860** | **0.00933232490** |

Final delivered throughput is 4.206924617 versus 6.607921790 Mbps, a joint gain of
**2.400997174 Mbps**. Return constraint cost per step is 0.2894672194 versus 0.1948619397,
a joint reduction of **0.0946052796**; mean minimum-battery ratio is 0.5728576350 versus
0.5780243491. Thus the endpoint J difference accompanies higher delivered service and lower
observed return constraint cost, rather than a favorable prediction proxy alone.

| Evaluation world | Joint minus detach J | QoS / step difference | Return constraint cost / step difference |
| --- | ---: | ---: | ---: |
| 920001 | +46.146236719 | -0.092282601 | -0.060960267 |
| 920002 | +39.916691856 | -0.032470975 | -0.029181480 |
| 920003 | +849.218326021 | +0.219417977 | -0.174079406 |
| 920004 | +596.044348317 | +0.118705188 | -0.139566701 |
| 920005 | +391.838223506 | +0.193322941 | -0.034530289 |
| 920006 | +1058.367460196 | +0.147924395 | -0.279473022 |
| 920007 | +310.823522984 | +0.139632211 | -0.033554494 |
| 920008 | -64.264362376 | -0.053983224 | -0.005496578 |

Seven of eight worlds improve in J, five in QoS and all eight in return constraint cost.
World 920008 is adverse in J and three worlds lose QoS; these remain in the result. The
worlds describe this pair's evaluation distribution and are not eight training replicates.
At rollout 20 joint has **worse J and higher return cost despite better QoS and much lower
factual MSE**. At rollout 30 it has better J but **2.248223 times detach's factual MSE**
(124.8223% higher). These opposing orderings directly limit this proxy's use for selecting
the better controller. They do not prove that all useful predictive information is irrelevant.

Both policies again deteriorate late: rollout 20 to 30 J changes are -643.071854459 for
detach and -162.127487501 for joint. Relative to initialization, joint improves by
303.954123558 whereas detach declines by 99.557182345. The latter decomposition is descriptive,
not a causal allocation of the gain to control degradation versus candidate learning. Joint's
final QoS remains only 0.220264 and its return constraint cost is nonzero; this is no
convergence or satisfactory-controller claim. All B02 joint training and evaluation charging,
cutoff and depletion quantities are zero. Detach retains its one occupied-UAV charging time
step in training; every B01/B02 evaluation has zero charging, cutoff and depletion events.
The retained comparison therefore does not test a charging-competition or failure-recovery
benefit merely because the host implements those mechanisms.

### Cumulative explanation, Pro reuse and DM choice

The prior explanation is the [B01 paired reading](#b01-joint-complete-and-paired-reading--2026-09-22-0109-pdt)
and [Pro-informed B02 selection](#2026-09-22--pro-reading-adoption-and-b02-selection).
The two training-pair outcomes are retained separately:

| Training instance | Detach final J | Joint final J | J difference | QoS / step difference | Return cost / step difference | Within-pair joint / detach factual MSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| B01, 910021 | -644.966810001 | -485.429355351 | +159.537454650 | +0.038796228 | -0.034001587 | 0.306878 (lower) |
| B02, 910137 | -670.393732685 | -266.882426783 | +403.511305903 | +0.080033239 | -0.094605280 | 2.248223 (higher) |

**Strengthened:** the fixed auxiliary representation-update package's native benefit is
observed in a second training instance, with service and return cost supporting both final
J contrasts. This weakens an explanation confined to B01's particular instance. The positive
second result changes the disposition from a one-pair provisional candidate to a retained
two-pair exploratory package; an adverse or unhelpful recurrence would have ended this recipe
under the recorded rule. It does not establish a population mean or a stable ranking.

**Weakened:** improvement of this common initial-policy factual MSE is necessary for the
observed fixed-endpoint native gain. B02 is an explicit contrary observation. Revise the
mechanism language accordingly; do not reject a useful native contrast because this proxy
went the other way. The facts differ across B01/B02 and are narrow within both pairs, so
their absolute errors cannot be pooled as if evaluated on a shared validation distribution.

**Still unresolved:** task-specific predictive supervision versus more generic auxiliary
representation optimization/stabilization. Both interpretations could predict positive B02
native recurrence; this comparison does not identify their relative contribution. Extra
representation Adam work remains part of the package. Late degradation, the low absolute
service levels, fixed reused evaluation worlds, two training instances and absent evaluation
charging/fault exposure continue to restrict the use. No time-series correlation or MSE
ordering is presented as a mediation test.

The complete delivered Pro answer at `c1f7fdeef4813af4ffd023d75ef7bcf39326351e` already
specified both of the realized branches: useful J/service recurrence with compatible risk,
and recurrence with **worse** common-fact MSE. Its conditional advice is still materially
applicable to this unchanged scientific comparison: retain package evidence, weaken the
proxy explanation, and decide confirmation separately. Adopt that reading; no material
dissent, new question, broadened claim or resend is needed. This reuses the full repository
answer previously read and verified, not the short chat receipt. Its general confirmation
discussion is not an approval or criticism of a concrete future confirmation plan.

**Decision: keep the bounded package result; revise the mechanism interpretation.** The
owner-selected assignment to reach an informative native result and a supported
keep/revise/stop decision is complete. Preserve `exploring` scope, with **0 running and
0 queued fits**, and no open Pro or uncollected accepted operation. This is a retained
research candidate, not adoption as the default algorithm or entry into confirmation.
The original B02 recurrence question has been answered; an automatic third pair would add
another selected exploration without supplying a fixed population decision. No change to
target, weight, horizon or checkpoint rule is selected from these outcomes.

The useful future distinction is whether the same fixed package retains a practically useful
native benefit across fresh training instances and fresh final evaluation worlds, versus a
gain concentrated in the development instances/panel. That could justify a separate fixed
confirmation if a population claim becomes the intended use. It is **not selected now**:
the current request can retain a finite-learning package without making that larger claim,
and low absolute service plus late decline still limit immediate adoption. Confirmation would
cost 6–10 fresh fits for 3–5 paired training instances, with actual seeds, task/evaluation
population, practical use, fixed endpoint, uncertainty and reading rule written in a CLAIM
and critiqued by Pro before execution. Neither the number nor a wall-time extrapolation is
a power guarantee. B01/B02 would remain development evidence, not relabeled confirmation.
This is a bounded investment choice, not a proof that confirmation or other supervision
methods have no value, and no further fit is owed by the unused possibilities.

Current published main was checked at `a48ef628a40ed1200c42140dd2d6e42c8979faa9`.
Its native-outcome, finite-learning and independent-unit background determines this reading:
keep the native/service contrast despite the adverse proxy and preserve the training unit.
Update shared topic 6 from its one-pair observation to recurrence with reversed MSE ordering,
keeping late decline and actual exposure limits. Other directions' findings and controls are
unchanged; owner pause remains lifted for this lead, Claude FSD remains paused and G33 frozen.

### Final cost and observation state

B02 joint runner wall is **5689.557749510 seconds / 94.825962492 minutes**, peak RSS
3,034,952 KiB. B02's two fits total **12,672.454433680 seconds / 211.207573895 minutes**.
All **4 planned fits are complete**, with no failed training attempt: **30,546.586701393
runner seconds / 509.109778357 minutes (8.485163 hours)** on `wsl_4070`, 720,000 training
transitions and 192,000 evaluation transitions. Physical factual collection totals 6000
transitions, once per pair; each joint arm merely loads its pair's bytes. B01's 15-second
and B02's 16-second pre-training refusals remain separate support costs. Preparation,
collection, verification and publication time is additional and was not comprehensively
metered; runner-wall sum is neither end-to-end task time nor measured exclusive node occupancy.
Observed joint/detach wall ordering reverses between pairs under different concurrent load,
so it does not identify intrinsic auxiliary compute overhead or a speed advantage.

Terminal observation `c616b9a44bca892fba642f98` was consumed using generation 28 and wake
`442aab7d-8284-44da-9c18-3b6b70935125`. Rearm returned generation 29; readback has no pending
events or active observations. All four launches are terminal, and the only Pro operation
was already delivered, read and its owned tab closed. No worker restart, repeat Send,
cross-task message or new operation follows from this completion event.

## 2026-09-22 — Direct DM continuation and plan-1 source reading

Owner has now started literature-plan item 1 and assigned this same direction to direct DM
task `01a0c9af-d5cd-7d70-b5e8-9db2c598ad4e`, checkout
`/home/fires/.codex/worktrees/d319/hmasd-wsl`, branch
`codex/uav-service-predictive-control`. The published registration is
`e46deae6aae14dd54180bfabd982fd00840a14de`; this checkout was fast-forwarded to it.
The prior DM's notebook, four fits, frozen sources and conclusions remain intact. The
launch-bound lead is still `Codex DM (independent session)`. Claude FSD remains paused and
G33 remains frozen. Initialization is complete; no continuing Root permission or App
communication is involved.

Read-only native status checks at `2026-09-22T15:18:46Z` reconciled all four original
operation references: consistent records, valid exit-code-0 witnesses and absent finished
runner/supervisor identities. The old checkout is clean and was not written. Its one Pro
operation remains `COMPLETE` with `send_effect=sent`, and its full delivered answer at
`c1f7fdeef4813af4ffd023d75ef7bcf39326351e` was reread. No old launch or Send was repeated.

The new DM also independently recomputed all four saved endpoint prediction errors from
the retained local arrays using direct float64 W10 sums. Episode-equal MSE is
0.010846486932 / 0.003328549872 for B01 detach/joint, and
0.004150978507 / 0.009332327272 for B02 detach/joint. Every episode has 1491 valid windows;
validity matches saved masks exactly and the largest target difference is 2.981e-8.
The within-pair factual SHA256 values match the original records. These are verification
of existing observations, **0 new fits**, not additional replication. B02 initial-policy
fact target standard deviations are only 0.008519 and 0.001446; this narrow diagnostic
distribution does not support treating its MSE as controller quality.

The working explanation remains the [complete B02 reading](#b02-complete-comparison-and-bounded-keep-decision--2026-09-22):
two useful native package contrasts, an explicitly contrary proxy ordering, late decline,
low absolute service and no evaluation charging/cutoff/depletion exposure. What is new is
the selected question: does the service package retain useful control value against a
specified ordinary auxiliary representation-learning package, on fresh training instances
and fresh final worlds? The earlier Pro answer covered unchanged recurrence and proxy
reversal, but did not assess this new comparator. Constitution section 5 therefore calls
for one focused consultation before adopting the successor design.

Current main's [shared background topics 2, 4 and 6](https://github.com/CartmanFatass/My-paper-code/blob/e46deae6aae14dd54180bfabd982fd00840a14de/docs/research/RESEARCH.md)
changes the design concretely: future facts remain training labels; primary readings stay
native J/service/risk; a common endpoint-policy factual panel supplements the narrow
initial-policy panel; training blocks remain the repetition unit; S/G differences cannot
identify service semantics alone. The new S1 raw/clip deployment observation in topic 3
does not transfer as an S7 correction: S7's energy wrapper already transforms actions.

Relevant primary passages were checked against the local source JSON, with official
bibliographic pages verified: [Ni et al., ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/666c1861d709bd84e20b6e0e02a2c223-Abstract-Conference.html),
Algorithm 1 / section 4.3 and section 5.3, supports an ordinary one-step action-conditioned
self-prediction comparator. Its clean MiniGrid results favor observation prediction over
self-prediction, and its detached-target rank degrades in deep recurrent experiments;
stop-gradient is not a general anti-collapse guarantee. [SPR, ICLR 2021 v4](https://arxiv.org/abs/2007.05929v4),
section 2.2, Table 2 and Appendix D, supports normalization/target stop-gradient as concrete
design choices and retaining full auxiliary compute cost, not a UAV benefit prediction.
[MA2CL, IJCAI 2023](https://www.ijcai.org/proceedings/2023/470), sections 4.2–4.3 and conclusion,
already uses auxiliary gradients on the actor encoder; moving a loss there is not itself
a new mechanism. Local evidence records are `DMOD-C517F96832` E4/E7,
`DMOD-F328FA237A` E1/E4/E6 and `MARL-0502` E2/E3/E7 under
`/mnt/c/Projects/Inst-sci/papers/MyLib/llm-index/readings/`; primary JSON files are under
the same library's `json/`. The three synthesis revisions from DMX-C02 to MFX-C03 are
design context, not new empirical evidence or support for a compulsory fixed readout.
These analogies omit endogenous teammate learning, shared team labels and policy-induced
changes in trajectories; the native comparison is needed for those effects.

A bounded source Scout and direct DM inspection identified an action distinction relevant
to the proposed G arm. At frozen source `30401722b14c208bf5330ab66e967c94b3df8a36`, the runner
stores the raw four-dimensional actor command and submits it to `env.step`. The S7 energy
wrapper clips it, interprets docking and may override movement before sending a derived
three-dimensional action to the base environment. Proposed G should therefore condition
on the **actual submitted actor command**, not claim to observe the final physical action.
This keeps the policy's action variable and avoids adding hidden execution-state inputs or
changing the environment. The prediction head's inputs remain training-only.

W10 uses the consequences of rows t through t+9, with terminal/truncated transitions
allowed only at the last member of a full window. The shared W10-valid starts already
exclude `done[t]` and guarantee that observation t+1 exists, so G can use that same subset
without crossing a reset. Chronological auxiliary replay uses the stored sequence-entry
hidden state, masks `1-done[t-1]`, held skills through detached FiLM and chunk length 50.
The actual old runs have no straddling collector boundaries. No new full-episode recurrent
algorithm or new physical action mapping is selected by this continuation.

## Pro question 2026-09-22 b03-service-versus-generic-control

Conversation: reuse the direction's completed Jev conversation from local operation
`hmasd:9bb9395a71f2a673ecf1e24524eba4fa6b20b6bac2c77efcd307021b692d362c`.
Its private address stays only in local transport state.

Question: Under the complete B01/B02 evidence, is the following six-fit D/S/G comparison
the smallest worthwhile next investment to distinguish a useful W10 service-training
package from an ordinary auxiliary-learning explanation? Recommend a concrete first
comparison and reading rule, especially whether the proposed generic target is a competent
reference, which scale/collapse diagnostics actually protect that reading, and which
outcomes should end this recipe's spending. This is a package/use decision, not a request
to prove service-semantic mediation or invent another module.

Standing: the preceding continuation entry and B02 complete comparison are the current
explanation. B01/B02 final joint-minus-detach J is +159.537455/+403.511306, QoS is
+0.038796/+0.080033, return cost is -0.034002/-0.094605; B02 common-fact MSE ratio is 2.248223.
Both pairs decline late, both use the same eight evaluation worlds, and risk mechanisms
have no charging/cutoff/depletion evaluation exposure. No prediction is an actor input.
The strongest simpler account is extra representation optimization/stabilization; another
is development-instance/world dependence. Two positive training pairs do not resolve them.

Proposed comparison, subject to this advice and the DM's subsequent explicit adoption:

- D: both service and generic heads train on detached actor features; native learning stays.
- S: only W10 service loss updates actor base/GRU; the generic head is a detached shadow.
- G: only one-step normalized latent-prediction loss updates base/GRU; the service head is
  a detached shadow. All arms contain both heads and have the same training data rights.
- Service head: hidden -> 64 -> 1, unchanged W10 team QoS target. Generic head:
  `(h_t, submitted raw actor command a_t)` -> 64 -> hidden, predicting stop-gradient
  `h_(t+1)` with squared distance between unit-normalized vectors, epsilon 1e-8. Target
  features are computed without gradients once at the start of each auxiliary pass and
  held fixed for that pass; they are refreshed next pass, not permanently frozen. No EMA,
  projection, teacher, prediction input, communication or planning is added by default.
- Both heads update each chunk; only the designated loss reaches the representation.
  Preserve S's existing head initialization with RNG-isolated generic initialization;
  test D/S native behavior against the old recipe when the added head is shadow-only.
  Keep native update then one auxiliary pass, chunk50, separate head/representation Adam
  rates 3e-4/3e-5 and separate norm clips .5. Same rates are not the same gradient effect.
  No evaluation-dependent loss tuning or hidden generic warm-start is proposed.
- Preserve S7-S2 interface v3/reward v2/arm C, N8/k10, local actor information, critic,
  Gaussian/PPO likelihood and existing S7 action execution. Proposed command conditioning
  explicitly differs from conditioning on the post-energy-wrapper physical motion.
  Auxiliary replay uses original observation normalization with no statistic updates,
  sequence-entry hidden state, shifted done masks and held skill conditioning. G uses
  exactly S's complete W10 start rows, so its next row never crosses an episode boundary.

The S/G contrast changes time span, scalar versus latent target and loss geometry as well
as service semantics. Even a favorable S/G result establishes only this specified package
contrast. A collapsed G cannot establish service-specific necessity or defeat all generic
auxiliary learning. Ni et al.'s clean-observation OP results and detached-target rank decline
are adverse context for casually labeling this G a strong comparator. Please choose whether
to retain this bounded G or substitute one clearly specified ordinary target **before** any
fit, with the information/cost reason; do not suggest an automatic target sweep.

Prospective cost and units: D/S/G × two fresh training blocks = **6 fits**, each
4 lanes × 1500 steps × 30 rollouts = 180k, total **1.08M training transitions** on
configured `wsl_4070`, CUDA FP32, four Torch threads. Existing four fits remain development
evidence. Candidate training seeds are 912211 and 912347 (each also binds its lane seeds
and model RNG). A bounded search of published direction notes, designs, scripts, candidate
code and runner configs found no use of these or the proposed factual/final-world seeds;
final implementation will bind actual values through config and launch. There are no new
fits started or queued, and this question does not grant an automatic confirmation.

Preserve rollout 0/10/20/30 development curves on worlds 920001–920008. At rollout30 only,
evaluate all six fits on fresh final worlds 936001–936032, shared across arms and blocks.
That is nominal **576k native evaluation steps**, with actual termination counts reported.
Each block samples two common initial-policy factual episodes (932201/932202 and
932211/932212 respectively), then each endpoint policy supplies four episodes on the block's
common factual worlds (933201–933204 and 933211–933214). After the three fits in a block,
all three heads replay the same union of endpoint trajectories from reset; factual data
never updates any learner. Physical factual collection totals **42k steps**, plus replay.
Native training/evaluation/factual worlds are disjoint; endpoint facts are diagnostic data,
not the final native world panel. Episodes are weighted equally for the primary W10 MSE,
and neither overlapping windows nor agents inflate the training repetition count.

Primary readings: per training block, final-world mean raw episode-return differences
S-D, G-D and S-G at rollout30; retain every world, curve and absolute level. Report QoS,
delivered throughput, return-constraint cost, minimum battery and actual charging/cutoff/
depletion exposure beside J. Primary intermediate reading is endpoint-common-fact W10 QoS
MSE, with the initial-policy panel separately named. It is not a necessary-benefit gate.
Two blocks are exploratory; no population ranking, equivalence or confirmation claim.

Record per-pass target/feature/prediction norms, per-dimension variance and effective rank,
actual auxiliary head/representation gradients and parameter displacement, loss/counts and
full costs. The plan also proposes same-parameter-point RL/auxiliary gradient cosine and
post-auxiliary policy KL. These require additional loss replay/instrumentation: advise
whether they alter this first package decision or should be deferred until a separately
chosen gradient-location question. No scalar diagnostic may become an outcome-selected
replacement endpoint. Numerical failure is technical failure; target collapse is an adverse
comparator observation, not service-semantic evidence or a license to replace fits mid-batch.

Proposed investment reading: two fresh blocks with useful positive S-D native contrasts,
service support and compatible observed risk retain the bounded S package. Consistent S-G
increment would retain only a contrast to that exact G. If both useful packages are hard
to distinguish, prefer actual simpler/cheaper use without an equivalence claim. Proxy-only
improvement, final-world reversal or continued poor absolute service should weaken further
investment, not trigger an early-checkpoint rescue or extra fit. G failure cannot rescue S
when S-D has no useful native increment. Please challenge these branches and state what
observation would change your recommendation. Four-fit GRU-only follow-up and eight-fit
confirmation are unselected options, not part of this batch or an entitlement.

The historical 509.11 runner minutes for four fits gives only a rough original-recipe
scale (~127 minutes/fit); expanded final evaluation, generic forward/backward, endpoint
facts and replay add work of unknown duration. No exclusive-node speed claim is available.
Implementation/verification are non-fit work; fitting any additional probe would count and
require a separate prospective choice. No mandatory toy pass or exhaustive search is proposed.

Context (paths marked source_sha use the full question commit supplied in the message):

- Current owner instruction: activate literature-plan item 1 as this direction's independent
  direct DM, continue through meaningful execution/readout/publication; initialization is
  complete. No App cross-task communication. Research is authorized here; Claude/G33 remain
  restricted. `docs/project/OPERATING_CONSTITUTION.md` sections 1–5, 7–8 at source_sha gives
  governance, fit-cost and bounded inference; Pro advises and adds no approval gate.
- Method at source_sha: `.agents/skills/hmasd-scientific-tools/SKILL.md`, Update the working
  explanation / Simple-model and literature bridges / Comparators and MARL information /
  Statistics / Cost and exposure / Pro. Engineering's Checks and review applies only to
  actual successor implementation, not a new science prerequisite.
- Shared evidence: `docs/research/RESEARCH.md` topics 2/3/4/6 and the owned Active row at
  `e46deae6aae14dd54180bfabd982fd00840a14de`; original proposed design is
  `docs/research/designs/LITERATURE_RESEARCH_PLAN_20260922.md#plan-1` at
  `fe6e990cb161af5483d12da624e0184e75db3ffd`. The draft is a starting point, not a frozen run.
- Direction evidence at source_sha: this notebook's B01 paired reading, B02 complete
  comparison and continuation above; complete `summary.json` and `config.json` under
  `runs/uav_service_auxiliary/b01_detach_910021_a01/`, `b01_joint_910021_a01/`,
  `b02_detach_910137_a01/`, `b02_joint_910137_a01/`. The earlier full Pro answer is this
  notebook's `Pro question 2026-09-22 b01-native-gain-next-investment / Answer` at
  `c1f7fdeef4813af4ffd023d75ef7bcf39326351e`; its B02 branches retain their original scope.
- Frozen code is separately at `30401722b14c208bf5330ab66e967c94b3df8a36`:
  `experiments/candidates/uav_service_auxiliary/b01/auxiliary.py` (`future_window_targets`,
  `recurrent_entry_masks`, `_representations`, `update`), `native.py` (`NativeSpec`,
  `_episode`, `write_facts`, `prediction_replay`, `run_native`), and
  `scripts/run_uav_service_auxiliary_b01.py`; action mapping is
  `envs/pettingzoo/relay/energy_aware.py` (`step`, `_prepare_energy_actions`,
  `_movement_velocity_from_action`). These files need not exist on the new main-based
  question branch; inspect the named frozen revision. Old B01/B02 entrypoints stay intact.
- Primary passages and official links are in the preceding source-reading entry. The
  local library files are not accessible through GitHub; do not claim to have read them.
  Use the linked primary publications where needed and distinguish their actual results
  from our native adaptation. No novelty claim or whole-library review is requested.

Constraints: no training, no edits outside the empty `### Answer` subsection of this
question on branch `codex/uav-service-predictive-control`. Read the pinned question for
reasoning; fetch the latest target file for writing and use its actual blob SHA. Preserve
all other bytes; stop on overlapping edits. On successful write report the actual commit;
on write failure return the complete answer in chat, not merely a SHA, status or link.

Return: a focused Chinese answer separating observed facts, changed/unchanged judgments
and new conjectures; the strongest reason to decline or materially simplify this batch;
the smallest executable informative comparison you favor, its fit/non-fit costs, comparator
limits and result branches. State which requested source could not be read and the actual
consequence, without turning missing optional material into an approval process. Include
`MATERIAL_DISSENT: yes/no`. The DM owns the final choice and will record adoption or dissent.

### Answer

Saved from chat, 2026-09-22. Same accepted request; delivery verification returned
NOT_DELIVERED and the target branch still had an empty Answer. The complete collected
text below is preserved verbatim (including rendered-math/citation text), SHA-256
`d3773aed24c457f1360f59e106784b4df3fc8d69a462685ffb201fc38bccbffc` before the file newline.

GitHub 读取成功，但本轮可调用接口没有仓库文件写入动作，因此未写回；实际 Answer commit：无。 最后读取的目标 blob 为 da8386d0a6ae11f73f78f9c13a24d139689e5eb7，指定 Answer 仍为空，其后已有另一节记录；本轮没有修改仓库。

完整答复 Markdown 副本（含固定版本来源）

B03：服务辅助训练与普通辅助学习的下一项比较

MATERIAL_DISSENT: yes。 异议针对拟议 G 的首选目标，以及把梯度余弦／策略 KL 纳入本轮的必要性；不是反对继续研究服务训练包，也不是要求先完成一种新的确认。

我的建议是：保留 D/S/G × 两个新训练块的六-fit 探索，但在任何 fit 之前，把 G 替换为“一步、以实际提交命令为条件的下一合法观测预测”；保留共同终点事实面板与新的最终评价世界；不做本轮 RL/auxiliary 梯度余弦和 post-auxiliary KL 的额外回放。 六 fits 不是数学上的最小实验，而是针对本题同时需要的“新条件下仍优于 D”和“相对一个明确普通方法的差异”，我愿意购买的最小完整批次。该建议不选择后续四-fit GRU-only 或八-fit 确认。题面的六-fit 方案与这些后续选项仍是待 DM 选择的设计，不是已经接受的运行。

hmasd-pro-question-usa-b03-serv… +1

一、B02 改变了什么，没有改变什么

已完成比较的固定终点可以压缩为下表。J 是完整 episode 的未改写原生奖励总和，差值均为 joint−detach；MSE 比值是在各自训练块的共同初始策略事实集内计算，不能把两个事实集当成同一分布。

固定 rollout 30 的读数	B01	B02
原生 J 差	+159.537455	+403.511306
QoS 比例差	+0.038796	+0.080033
返航约束成本差	−0.034002	−0.094605
共同事实 MSE，joint/detach	约 0.307	约 2.248
joint 的绝对 J	−485.429355	−266.882427
joint 的绝对 QoS	0.190837	0.220264

加强的是这套辅助优化包存在可复查原生用途的理由。 两个真正重新训练的块都得到终点 J、服务和返航成本同向的有利差异，不能再把全部正面信息描述为一次初始状态偶然性或纯代理改善。B02 joint 相对自身共同初始化的 J 还提高约 303.954，而不是只有“比一个退化对照差得少”。与此同时，两块仍共用旧八世界，历史曝光并未变成新世界上的外推验证。

削弱的是“该共同事实 MSE 的改善是控制增益的可靠解释或必要条件”。 B02 终点直接给出相反排序；B02 rollout 20 的 J 差又是 −77.433061，而终点转为正。这不是稳定的逐面板统治，更不是 MSE 与回报之间已被识别的因果关系。当前只能说该窄分布、该训练中 readout 的误差不足以承担控制质量的代理；不能扩大为“所有服务预测都无关”。

最强的继续解释是：额外表征优化在给定训练预算内产生有用的稳定化或表示偏置，服务标签可能是实现它的一种办法。最强的停止解释是：我们仍在付费比较低服务水平、晚期退化的学习配方；新增 G 若容易退化，六 fits 最后可能既不能给出可用控制器，也不能排除普通辅助学习解释。两块旧正例、没有训练后的预测输入、以及没有评价充电／cutoff／depletion 暴露，都不能消除这项机会成本。这里的两个解释是对已有事实的竞争性解释，不是已经确诊的机制。

hmasd-pro-question-usa-b03-serv…

我仍建议一次改进后的比较，是因为它现在增加了两项有区别的信息：同期 D/S/G 的新训练对照，以及与旧开发世界分开的最终世界。不是因为已经支付四 fits 必须继续，也不是把“还未证伪”当成投入理由。

二、为什么不把当前 normalized latent G 当作首选强参照

拟议损失的一个问题可以直接用反例说明。设所有合法历史都被编码成同一个非零向量 c，预测器也总输出 c，则

	​

∥p(h
t
	​

,a
t
	​

)∥
2
	​

p(h
t
	​

,a
t
	​

)
	​

−sg(
∥h
t+1
	​

∥
2
	​

h
t+1
	​

	​

)
	​

2
2
	​

=0.

特征范数非零、归一化向量范数为一，损失却可以在没有区分历史的表征上达到零。按 pass 固定目标和 stop-gradient 改变优化路径，不从目标集合中排除这个解。这只是对拟议辅助目标的反例，不是断言联合 RL 必然走向塌缩，也不是否认该方法可能有效。

实际文献使这个风险值得在设计前处理。Ni 等的 Algorithm 1／§4.3 提供普通动作条件自预测的先例，但其反塌缩理论有特殊简化条件；§5.3 的深循环实验中，detached target 的秩并未普遍保持，干净 MiniGrid 中观测预测也有更有利的结果。因此我不会把“用了 stop-gradient”当作当前 GRU 对照已经合格的证据，更不会把该论文算法与本项目的 actor-RL＋独立辅助 Adam 当成完全相同的实现。
ICLR 会议记录
+1

SPR 的归一化、目标网络及相关消融应作为完整方法条件来读：Table 2 中的未归一化 quadratic 变体表现很差，并不推出删除投影、数据增强等条件后的一步单位向量预测自动可靠。Appendix D 也说明辅助方法必须计完整训练与评价时间。MA2CL 则已把辅助表征学习作用于 actor encoder；这里不能把梯度进入 actor 当成新机制。两篇论文都不替当前 G 或 S 提供 UAV 成绩。
arXiv
+2
arXiv
+2

我选择替换 G，而不是给它增加 EMA、投影、防塌缩正则和目标搜索。 本轮所需的是认真定义的普通方法比较，不是建立完整的自监督算法平台。换成环境给出的下一合法观测，至少使给定事实轨迹上的目标不随编码器一起收缩；它仍可能难学、关注无关维度或损害控制，必须接受这些反面结果。

三、我建议实际采用的 D/S/G

D、S 的作用保持题面不变，只替换 generic head／target；下文把替换后的普通臂仍记为 G。环境保持 S7-S2、interface v3／reward v2／arm C、N=8／k=10，高低层及判别器继续原生学习，不叠加时长、通信或规划改动。

hmasd-pro-question-usa-b03-serv…

臂	服务头	普通观测预测头	辅助梯度进入 base/GRU
D	训练，输入表示 detach	训练，输入表示 detach	无；原生 RL 正常进行
S	训练，允许表征梯度	训练，但作为 detached shadow	只有 W10 服务损失
G	训练，但作为 detached shadow	训练，允许表征梯度	只有一步观测预测损失
固定一个可执行的普通目标和尺度定义

令 x
t
	​

 为原 actor 合法观测路径中的数值向量，使用原有归一化语义但不更新统计；a
t
	​

 为该 agent 当时实际提交给环境的四维原始命令。G 的头采用

p
ψ
	​

(h
t
	​

,a
t
	​

):(d
h
	​

+4)→64
ReLU
	​

d
o
	​

,

预测下一观测，数值目标按下文的尺度变换定义。a
t
	​

 使用存下来的常数命令，不以当前策略重采样，也不通过该输入向 action head 反传。当前配置 d
h
	​

=256,d
o
	​

=365；不加入全局真值、其他 agent 的隐藏动作、真实 padding 身份或实际物理执行后的状态作为额外输入。观测预测头只在训练／诊断中使用，不改变执行 actor。

为了避免“预测下一观测”留下一个未定义的量纲问题，我建议以下固定、只作用于 G 的目标坐标变换。在每个块首次共同训练 rollout 上，使用 W10 有效起点对应的下一观测，计算每坐标均值 μ
j
	​

 和

s
j
	​

=max(1,
mean(x
t+1,j
2
	​

)
	​

),u
t+1,j
	​

=
s
j
	​

x
t+1,j
	​

−μ
j
	​

	​

.

三臂复用同一份 μ,s 的精确值；它们在本块余下训练中不更新。计算来自本来就要采集的首个训练 rollout，不来自 initial-fact、endpoint-fact 或 final worlds，也不增加环境采集或拟合一个新 probe。保存其来源与数值，先验证三臂在首次辅助更新前的采集一致。actor 自身的输入、归一化状态及 S 的 W10 目标均不受这个变换影响。

此定义保留已在原生观测构造中具有合理单位的坐标，同时不把首个 rollout 几乎恒定的维度除以极小样本标准差而放大。它不是最优缩放定理，也不声称把各维对控制的价值变成相同；它只是一个事先确定、可核查、无测试回流的普通构造。本轮不根据回报或 G 的误差再更换这套尺度。

损失明确为对有效 agent-row 及观测坐标取平均；下式的 V 指当前 chunk 的有效起点，pass 报表另外按有效样本数加权：

L
G
	​

=
∣V∣N
1
	​

(t,e)∈V
∑
	​

i
∑
	​

d
o
	​

1
	​

j=1
∑
d
o
	​

	​

[p
ψ
	​

(h
t,e,i
	​

,a
t,e,i
	​

)
j
	​

−u
t+1,e,i,j
	​

]
2
.

零填充位置仍是原有观测数字的一部分，不额外用环境真值选择监督维度。保留服务头的原 MSE 定义、两头各自 Adam 3×10
−4
、激活表征 Adam 3×10
−5
、各自 norm clip .5、每个有效 chunk 一步；上述 L
G
	​

 的系数固定为 1。相同学习率、相同裁剪上限和系数 1 不代表相同梯度作用或相同计算量，它们是这个指定包的组成部分，不是“纯服务语义”控制。

这个替换解决一项歧义，不认证全部能力

OP 的目标在同一轨迹上固定，编码器不能靠把自身下一潜表示也变成常量来消除目标变化。它还省去每 pass 额外构造整段 latent target 的必要性；输出维度则由 256 增至 365，实际成本仍要测，不能据此宣布更快。

其局限同样具体。S7 的局部用户／邻机槽按距离排序，下一槽位可能换实体；下一观测还包含队友行动与执行包装器共同造成的变化。一阶坐标 MSE 可以学到条件均值，却不保证保留对任务最重要的信息。合法数值观测也不等于没有噪声或无关信息，因此 Ni 等的干净 MiniGrid 结果仅是选普通参照的依据之一，不是迁移保证。
ICLR 会议记录

G 是第一次接受原生检验的、有限配置的普通参照，不是经过穷尽调优的 generic 上界。 S 已有四 fits 的开发历史，G 没有同等原生选择历史；公开这项不对称，不用新六 fits 把旧曝光清零，也不为“补齐公平”自动增加搜索。S−G 仍同时改变时域、标签维数、命令条件化和损失几何；有利结果只支持这套 S 相对这套 G，不能识别服务语义的独立中介作用。

hmasd-pro-question-usa-b03-serv…

四、真正保护读数的实现约束

命令与物理动作的区别必须保留。 冻结 runner 把四维 actor 命令提交给环境；energy wrapper 先裁剪、解释 docking／limp-home 等分支，再向基底环境传递派生三维动作。因此 G 预测的是“提交这条命令之后的合法观测后果”，不是一个已经观察到最终物理运动的完备动力学模型。不要为了让 G 容易预测而改执行映射，或偷渡包装器内部状态。

时间配对必须按真正的轨迹，而不是按张量方便。 S 的 W10 起点要求 t…t+8 无 done，t+9 可为终止／截断；G 用完全相同的起点和 t+1 观测。chunk 末行的下一观测可以在下一个 chunk，不应每隔 50 行额外丢一条、补零或跳过；真实 reset 不能跨越。继续采用 stored entry hidden、移位 done mask、已执行技能的 detached FiLM，以及原来的 50-step TBPTT。训练中分块参数更新后的隐藏状态沿用与从 reset 的固定参数评价是不同语义，不暗中给某一臂“修成”新的全历史算法。

shadow-only 不应改变 D/S 的原生训练。 两头分别拥有优化器和裁剪，generic 初始化不推进原随机流；新增统计不得改变原 normalizer、模块模式、GRU 状态或采样。需要核对的是实际参数／RNG／动作及首个原生更新，而不是只看“没有把它的 loss 加进去”。S 的服务更新顺序与有效曝光保持原样。已有辅助实现的参数所有权和随机性隔离提供了可复用的基础，而不是新增头自动无影响的保证。

还存在两项具体交付缺口。旧生产入口已正确把 910137 传入 NativeSpec，不能继续沿用上轮“B02 seed 未传入”的旧诊断；但它并不支持 B03 的 D/S/G、新种子和新面板，应由独立 successor 入口绑定，旧入口保持冻结。旧事实文件的 writer 保存 observations、skills、dones、qos，没有保存 raw command；若要在新的共同事实面板上评价 G，必须在新 writer 里同时保存当时命令，不能从旧 facts 或下一状态反推出一个“已执行命令”。

五、诊断：保留有解释力的低成本量，删去一轮额外梯度研究

我保留三类读数，但不把任何一类当成替换 J 的评分系统。

优化路径与尺度。 每 pass 报实际有效团队行／agent-row、两头与表征的步数、未缩放损失和实际使用损失；在原有 backward 中汇总每个头、base、GRU 的裁剪前范数、裁剪比例与实际参数移动。区分 RL 移动和本次辅助更新前后的移动；已有“自初始化总位移”不能独自回答辅助分支实际改变了多少。只需适当聚合和复用已有张量，不再回放一份 RL loss 来取得这些量。D 的辅助表征移动应为零，S/G 的 designated 路径应被实际检查。

退化与目标难度。 训练 pass 中的目标／预测／h 范数和逐维方差可直接统计；有效秩不必在每 pass 对全部 47,712 agent-row 做完整谱分解。建议只在 0/10/20/30 已有的共同初始事实回放中，固定选择至多 512 个跨 episode、时间、agent 的合法行，报告中心化协方差的总方差和有效秩，并保留分 agent／片段方差。用固定索引而非额外随机采样；各次使用同一事实索引，避免访问分布变了却归因为表示变好。

若以协方差特征值 λ
j
	​

 定义 p
j
	​

=λ
j
	​

/∑
j
	​

λ
j
	​

，报告

exp(−
j
∑
	​

p
j
	​

logp
j
	​

),

同时保留总方差 ∑
j
	​

λ
j
	​

；总方差为零时明确记退化，不加 epsilon 后报告一个虚假的高秩。低总方差／低秩是退化线索，高秩却不是任务能力证书；不同技能或身份的均值差也可能抬高 pooled rank。使用 OP 后没有需要监测的 learned target encoder，重点转为实际观测目标变化、预测变化和演员表征变化。

共同事实上的简单参照。 G 的观测 MSE 旁保留固定的 persistence 预测“下一观测仍为当前观测”，以及来自训练首段的坐标均值预测；两者使用同一尺度、同一有效行，无额外优化、无额外环境步。W10 服务 MSE 也可附训练数据均值这一无状态参照，但不使用测试 episode 自己的均值当作已训练模型。简单参照帮助识别“只是接近一个常量”或“下一步本来就几乎不变”；不要求它们先给出阳性才能执行学习比较，也不以其失败自动启动更大的头。新增头前向、统计与回放的时间照实计入。

本轮推迟 RL/auxiliary 梯度余弦和 post-auxiliary policy KL。 梯度余弦需在同一参数点、同一合法历史和明确损失定义上计算；原始梯度夹角还不是两个 Adam 实际步的夹角。KL 则衡量所选观测分布上的策略变化，不说明变化是否提高完整回报。当前没有一种预写余弦或 KL 结果会取代新世界上的 S−D/G−D/S−G，或直接决定应该采用哪一包，因此额外 loss replay 的信息价值不足。这不是永久禁用：只有以后选中的梯度位置／干扰问题会据此作不同选择时，才重新为它计成本。

这些诊断建议是在题面允许删减的 instrumentation 范围内作取舍，不是新添的一组科学准入关卡。

hmasd-pro-question-usa-b03-serv…

六、最终评价与共同事实面板怎样读

保留拟议训练种子 912211、912347；旧 920001–920008 世界只承担 0/10/20/30 的开发曲线。最终主读数保持 rollout 30 的 936001–936032，不根据前一个 fit、某个开发 checkpoint 或初步 final 排名改变后续臂、目标、权重和训练量。新增固定批次不能因为改名 B03 就继承一次自动确认。

hmasd-pro-question-usa-b03-serv…

对块 b，先形成

Δ
b
S−D
	​

=
32
1
	​

w
∑
	​

[J
b,S,w
	​

(30)−J
b,D,w
	​

(30)],

同样计算 G−D 与 S−G，分别报告两个块和每个世界。三个差值满足

Δ(S−G)=Δ(S−D)−Δ(G−D),

不是三个独立证据来源。32 个世界嵌套在每个训练实例中，两个块共用世界也不会产生 64 次训练复制。可以描述条件世界分布与尾部，但不能用世界 bootstrap 的窄区间宣称训练总体精度充分。两个新块仍是探索；原四 fits 留在开发证据中，不拼成事后“六 seed 确认”。这与指定科学方法中关于独立训练单位和选择曝光的要求一致。

共同终点事实集每块有 D/S/G 各四条轨迹、合计十二个 episode。三套 endpoint 的表示与服务头都从 reset 回放全部相同事实，保持 episode 等权，先在 episode 内平均合法时间与 agent 的误差，再平均 episode。初始策略的两条事实单列，不能混成一个看起来更好的总体 MSE。保留采集来源 D/S/G 的分层描述，不能只读各自最容易的轨迹。

hmasd-pro-question-usa-b03-serv…

这测量的是由本次三个 endpoint 共同生成的经验混合分布，不是独立于这些策略的全任务分布。共同测试输入解决了“每臂在不同测试轨迹打分”的混淆，却没有让各自 head 的训练数据变相同，也没有把 MSE 变成纯表示能力测量。新面板能检查“旧初始事实太窄”这一解释，但不能证明唯一中介，不能为未执行动作提供反事实标签。若短 episode 完全没有合法 W10 窗口，应报告缺失及分母；原生回报仍保留，不把 MSE 缺失填零或静默剔除整项运行。

另有两个容易误读的指标。第一，当前恒定每用户 1 Mbps、30 用户的交付定义下，吞吐量是 QoS 的固定倍数；二者是不同单位的表达，不是两份独立正证据。第二，旧 evaluator 对每步 battery_min_ratio 求和后再除长度，所得是“时间平均的机群最低电量”，不是整回合 min
t
	​

min
i
	​

battery。B03 若要报告后者，应新增一个纯统计 min 累积器，同时保留旧指标名称与历史意义，不改环境或 reward。零充电／cutoff／depletion 仍只表示未观察到相应事件，不能升级为充电竞争解决或安全保证。

七、成本和最强的简化选择

沿用题面的 wsl_4070、CUDA FP32、四 Torch 线程与实际节点准入；每 fit 仍为四 lanes、1500 步、30 rollouts。本建议保留的原生数据量如下；计算的是名义完整长度，真实终止另报。

hmasd-pro-question-usa-b03-serv…

工作	数量与成本意义
六个完整训练 fit	6×180,000＝1,080,000 团队训练 transitions
开发曲线＋新最终世界	6×(4×8＋32)×1500＝576,000 原生评价 transitions
初始事实＋endpoint 事实	2×2×1500＋2×3×4×1500＝42,000 事实采集 transitions
合计原生交互	1,698,000；不把回放行数加成环境步
非 fit 工作	successor 实现与正确性检查、固定尺度统计、事实回放、指标归约、保存／读回；辅助训练计入所属 fit 的完整工作

旧四 fits 的 509.11 runner 分钟只是原配方的历史锚点。新最终面板、第二头、OP 输出、事实采集及回放改变成本，不能按旧均值给出本批完成承诺；更不能用不同并发负载下的 wall 比值识别纯算法开销。OP 去掉 latent-target 回放是一项结构差别，不是已经测出的时间收益。

hmasd-pro-question-usa-b03-serv…

最强的简化是停下，保存 B01/B02，而不是删除 D 后仍声称回答同一个问题。 只做 S/G 两臂×两块会省两 fits，但新世界上“两种辅助都损害原生方法”的情况无法被同期 D 识别；拿旧块 D 填这个位置会混入训练实例。只做一个 D/S/G 块确实可以作为更便宜的探索，但它只给新对照的一次实现／轨迹观察。既然当前决定已把“是否值得保留一套训练包”而非“G 能否接通”放在中心，我选择两块；不以此设定项目通用 seed 下限。

这笔投入不应服务于一条没有出口的归因链。共同事实、简单尺度与退化诊断足以承接当前包级问题；不用先训练 probe、证明 toy 阳性、优化到所有代理获胜，或者补齐四种未来消融。

八、预先承诺哪些结果结束投入

下表是我建议在 prospective entry 中采用的投资分支，不是显著性检验、全类别判决或自动下一批授权。判定始终先读新的固定终点和实际任务分量，不从最有利世界、最佳 checkpoint 或某个损失反选答案。

新批次结果	可保留的判断及停止边界
两块 S−D 都有值得保留的原生增量，服务支持且观察到的风险不抵销；相对正常工作的 G 也有一致增量	保留这套 S 和对这套 G 的有限包级证据。是否需要确认取决于一个实际待采用主张；不能转成服务语义必要性或自动开始 GRU-only。
G−D 有用，S/G 在现有数据下没有足够决策差别	对实际训练成本、监督取得成本和用途作选择；停止为“服务标签必需”继续支付复杂化成本。G 不因名为 generic 就自动更便宜；未分清不等于等价。
S−D 有用，但 G 数值正常却退化／没有学到有变化的目标	保留 S 对 D 的边界，承认普通对照问题未被充分解决；本批不换 G、不补 fit，不以 G 的失败证明所有 generic 无效。另一个对照只有新的具体理由才值得再买。
S−D 没有有用原生增量，只有 MSE 好看；或旧世界正例不能在新最终世界维持	结束当前 S 配方的性能投入，G 比它更差也不能救回。保留旧正结果及新反例，不选早期 checkpoint、不延长 horizon、不换目标续跑。
两块相互冲突，或相对差仍伴随不足以支持当前用途的绝对服务水平	记录未决，并默认不启动第三块／确认／新模块。停止是下一项信息不值成本，不是已经证明零效果。

“有用”不能偷换成任何一个正小数。 这里没有材料给出适用于当前用途的已验证最小收益、风险容忍区间或部署合格线，我不从旧效果大小倒推出一个人为阈值，也不把历史配置中的 QoS gate 偷渡进 B03。应公开差值、绝对水平和完整成本；在这次探索中，两个正号最多是保留候选的条件之一，不是自动采纳证书。若当前用途只有“证明唯一的服务语义机制”，则本比较从一开始就不够，应不买；若用途是筛选下一套值得采用的有限训练包，上述范围是足够具体的。

数值异常、错误目标移位或泄漏是技术问题，保留失败尝试与成本，不能填成科学负效果；数值正常但预测／表征退化则是该配方的不利观察。两者都不允许在批次里更换实现后把新 cell 当原来的固定比较。以后真要确认，需要实际 CLAIM、选定主对照、选择曝光、任务总体、终点、实用差异与不确定性方法，以及现行方法要求的全新独立训练种子；本轮两个块及三个差值不替代那份计划。

九、来源范围与最终判断

本答复依据 bf065e83a29880773168b111e0c66349f4359855 的问题、B01/B02 记录、治理／方法及指定 summary/config；共享背景按 e46deae6aae14dd54180bfabd982fd00840a14de，原 plan-1 按 fe6e990cb161af5483d12da624e0184e75db3ffd，旧 Pro Answer 按 c1f7fdeef4813af4ffd023d75ef7bcf39326351e，实际代码按 30401722b14c208bf5330ab66e967c94b3df8a36。B01 的完整 summary/config 在本对话前一轮已经阅读全文，本轮核对指定提交的 blob 相同；B02 的完整 summary/config 及当前 notebook 相关段落已读取。没有用移动分支代替科学输入。

本地文献库 JSON、readings 记录和仓库外 NPZ／checkpoint 本轮没有取得；四个误差的 float64 复算属于已读 continuation 中 DM 的核验，不是我的新数组复验。Ni、SPR、MA2CL 使用实际出版物文本；Ni 相关算法／秩页面及 SPR 方法页有图像核读，部分 SPR 表页和 MA2CL 页面的截图失败，因此没有把未目检表格的精确数值作为决策论据，也没有做全库或穷尽新颖性审计。尚缺 B03 successor 的实现、实际对照能力和新增完整成本，这限制“已经能运行／已经有用”的断言，不妨碍上述事前选题；没有增加等待外部审批的要求。DM 复算及本地来源的范围在附件中也有明确区分。

hmasd-pro-question-usa-b03-serv… +1

最终选择：改 G 为有固定尺度的一步合法观测预测，保留同期 D 和两块六-fit 结构，以新世界原生 J／服务／风险作使用判断，以共同终点事实作解释；删去当前不能改变包级选择的梯度余弦与 KL 工作。 B01/B02 使继续一次有理由，但没有让服务预测中介成立。新批次没有有用增量，或只能靠弱 G、旧世界和早期 checkpoint 保住故事，就结束这一配方的投入。

## 2026-09-22 — Same-operation observation correction and bounded L0

The question above was sent once under key
`hmasd:89adf42eea46a3380a9f9bac76cf9fec1c4fda626d6a8da2205de6d41cf61f75`,
source `bf065e83a29880773168b111e0c66349f4359855`, effort `6 Pro`; the exact attachment was
seen. The first deterministic observation incorrectly classified the 58-character opening
acknowledgment as COMPLETE. Delivery inspection returned NOT_DELIVERED, with no answer
commit. Reopening the same conversation read-only showed active source-retrieval/search
progress after that acknowledgment, despite the absence of the composer's stop button.
Thus the recorded short text is not the requested answer; scientific consultation remains
pending. The original request is accepted and will not be repeated or replaced.

L0 for the necessary observation repair: change only `tools/pro_transport/jev_send.py`
completion recognition and its focused `tests/skills/test_jev_transport.py` regressions.
Require completion controls in the bound assistant turn, rather than infer completion
from stable text plus absence of a global stop control. Preserve exact prompt/attachment
matching, operation key, single-send guard, conversation binding, connector authorization,
bounded observation, private URL policy and owned-tab closure. Test a stable opening
acknowledgment during tool work, a later true final answer, and isolation from earlier or
later turns' final controls; run the existing transport checks and obtain independent
engineering review. This is 0 fits and no new Pro Send. A new observation may target the
same accepted operation after the erroneous event is consumed; it cannot restart Pro.
The Pro-owned Answer subsection remains empty and untouched by this entry.

The DM's focused suite passed 30 tests in 0.78 seconds; independent Reviewer reran it,
30 passed in 0.72 seconds, with no material finding. A live read-only DOM check identified
the prior completed assistant's feedback control while the current operation had no
collectable final answer and continued reporting research progress. The DM accepts this
bounded repair; raw page/operation details remain private. There is still no scientific
answer or adopted six-fit batch at this boundary.

## 2026-09-22 — Complete Pro reading and B03 decision

The same accepted Pro request completed with 11,355 characters; the whole answer above
has been read. The connector reported no write capability, and independent delivery
inspection found no Answer commit. The DM saved the complete chat text in the assigned
subsection, preserving the question and all surrounding bytes, in `7ee03d86a`.
The first 58-character acknowledgment remains an observation error, not a consultation.
No question was resent and no other App task was contacted.

**Adopt the material dissent.** Replace the proposed normalized latent G with one-step
action-conditioned prediction of the next legal actor observation, with a fixed training-only
coordinate transform. A constant nonzero representation and the same constant prediction
give zero normalized latent loss; stop-gradient does not remove that solution. This is an
analytical counterexample, not evidence that joint RL necessarily collapses. The previously
verified Ni et al. Algorithm 1 / sections 4.3 and 5.3 support ordinary predictive comparators
and caution against a universal detached-target rank claim; the clean-observation result is
an analogy, not UAV evidence. SPR and MA2CL retain their actual method conditions and do not
make actor-encoder auxiliary gradients new. No new literature-derived performance claim is
made. OP instead has a fixed observed target on a given trajectory, but sorted entity slots,
teammate actions, irrelevant coordinates and partial observability remain real limitations.

The source audit and direct source reading verified submitted raw four-dimensional commands,
the existing wrapper's separate physical action mapping, W10 censoring, shifted entry masks,
detached FiLM and the lack of commands in old fact files. Direct inspection also verified
that the historical battery metric is a time average of fleet minima, and delivered traffic
is 30 times QoS under the current 30-user, constant 1-Mbps demand. Add an episode minimum
statistic without changing the historical field; do not count throughput as independent
support. The current learner/environment/config diff from frozen `30401722b` changes only
wording and an equivalent first-dimension shape check in the existing recurrent mask code.
The successor uses the current shared path consistently for all arms; old entries stay frozen.

The DM chooses the six-fit package comparison below. B01/B02 strengthen the case for one
new-world comparison of a potentially useful training package; B02 weakens the proposed
MSE-mediated explanation. Neither establishes service-label necessity. The strongest
alternative is to stop now because of low absolute service and late decline. I choose to
pay for contemporaneous D/S/G and new final worlds because they distinguish renewed package
value, an ordinary auxiliary alternative, and failure to retain the historical increment.
Removing D would lose the distinction between two useful packages and two harmful ones.
Two blocks are exploratory recurrence, not a new general seed minimum or confirmation.

Current published background was checked at `5da954a9de1a0f11a2c4f8a689c076abf8fd91b8`
([RESEARCH](https://github.com/CartmanFatass/My-paper-code/blob/5da954a9de1a0f11a2c4f8a689c076abf8fd91b8/docs/research/RESEARCH.md)).
Topics 2, 4 and 6 concretely keep future facts out of actor inputs, require a real ordinary
package comparison, separate proxy error from native consequences and keep the training
instance as the replication unit. The newer S1 action-law/capacity results do not justify
changing S7's existing wrapper. Pause remains lifted for this direction; Claude FSD and G33
retain their separate restrictions. No new general shared-background conclusion is owed
before these new observations exist.

Adopt low-cost gradient/parameter-movement, variance and fixed-fact rank diagnostics, along
with persistence and first-training-rollout mean references. Defer RL/auxiliary gradient
cosine and post-auxiliary KL: no prespecified value would change this package choice, and
they require extra replay. This is a scope decision, not a promise to add them later.
No four-fit GRU-only experiment, eight-fit confirmation, extra probe training or target sweep
is selected. This consultation covers the choice and its stated result branches; routine
implementation, review, execution and collection need no second consultation.

## 2026-09-22 — B03 prospective comparison and L0

**Question and fixed arms.** In S7-S2 interface v3 / reward v2 / arm C, N8/k10, does the
W10 service-supervised representation package retain useful native benefit against D and
one specified ordinary observation-prediction package? D trains two detached heads; S
updates actor base/GRU only from service MSE with a detached generic shadow; G updates
base/GRU only from observation MSE with a detached service shadow. High/low learners and
discriminator continue their unchanged native updates. Heads are never actor inputs.
S versus G changes target semantics, horizon, dimension, command conditioning and loss
geometry together; even a favorable outcome supports only these packages.

Service head is the frozen hidden→64/ReLU→1 with its original isolated seed offset
200000. Generic head is (hidden+4)→64/ReLU→obs_dim, with isolated seed offset 300000.
Native dimensions remain hidden=256, obs=365, action=4. Stored raw commands are constant
head inputs; no action-head gradient or resampling is allowed. No privileged physical
motion, entity identity or padding-truth input is added. At the first common training
rollout only, take next observations at W10-valid starts from the existing actor observation
normalization path with `update=False`. Compute in float64, over valid time/lane/agent rows,
`mu[j] = mean(x_next[j])`, `scale[j] = max(1, sqrt(mean(x_next[j]**2)))`, and thereafter use
`u_next=(x_next-mu)/scale`. This explicit RMS definition fixes the rendered equation in
the chat extraction. Save exact values and their source fingerprint. S/G import D's
values and verify their own first rollout produces the same inputs and statistics before
the first auxiliary update; do not derive statistics from any evaluation/fact worlds.
The first-rollout mean W10 target also supplies the optional constant service reference.

G uses exactly the W10-valid starts and next input at t+1, including cross-chunk pairs.
The target loss averages all 365 coordinates and valid agent rows; coefficient is 1.
Keep native update then one chronological auxiliary pass, 50-step TBPTT, collector entry
hidden, mask row 0=1 and later rows=1-done[t-1], and held-skill FiLM with its output detached.
Each head has independent Adam 3e-4 / clip .5; the one active representation optimizer is
Adam 3e-5 / combined base+GRU clip .5. Step the service head first, then generic head;
use detached pre-update features for the inactive head. S's service/representation update
must reproduce the original joint path on the same inputs. D has no auxiliary representation
optimizer. Identical rates/clips are not a claim of equal effective gradients or compute.
The transform, losses, horizon and target are not retuned after scores.

**Fixed exposure.** D/S/G × training seeds 912211 and 912347 = **6 planned fits**, each
4 lanes × 1500 steps × 30 rollouts = 180,000 team transitions; **1,080,000 training** total.
Lane seeds are block seed+[0,1,2,3]. Execute D/S/G for the first block, then D/S/G for the
second; serialize fits unless actual node evidence supports a safe equivalent schedule.
Use configured `wsl_4070` first, CUDA FP32, TF32 off, four Torch threads. Native admission
must verify fresh actual-node memory and the stable lead `Codex DM (independent session)`.
No new fit has started at this entry. The old four fits remain development exposure;
G has no equivalent tuning history, and this asymmetry remains disclosed.

Development worlds 920001–920008 run at rollouts 0/10/20/30. New final worlds
936001–936032 run only at rollout 30, in every arm/block: **576,000 nominal evaluation
transitions** total. D collects each block's two common initial-policy fact episodes:
932201/932202 or 932211/932212; S/G reuse those exact files. Each final policy collects four
fact episodes on 933201–933204 or 933211–933214. Thus **42,000 physical fact transitions**,
and **1,698,000 nominal native interactions** overall, with actual early terminations counted.
Facts now include the submitted raw commands. After a block finishes, all three checkpoint
pairs replay its same 12 endpoint episodes; initial-policy facts stay separate. These are
zero-update diagnostics, with no new environment interaction or probe fits. Episode-weighted
MSE averages valid time/agent/coordinate error within each episode before averaging episodes;
missing W10 windows stay explicitly missing, not zero. Preserve source-arm strata and all
per-world values. A common endpoint mixture is not the complete task distribution.

**Readings and investment branches.** Primary contrasts are each block's rollout-30
final-world means S−D, G−D and S−G in complete raw native episode J; also retain absolute J,
QoS, return cost, delivered traffic, episode minimum and time-mean fleet-minimum battery,
charging/cutoff/depletion exposure and all development curves. S−G=(S−D)−(G−D), not a third
independent experiment. The two training blocks are the units; 32 shared worlds do not
become 64 training replications. No population ranking, equivalence or safety claim.
Endpoint-common-fact service/OP MSE is explanatory, never a gate substituting for J.

- Useful S−D in both blocks, supported by service without offsetting observed risk, may
  retain this S package. A consistent increment against a functioning G retains only that
  bounded comparison, not a service-semantic mediator or automatic confirmation.
- If G is useful and the data give no actionable S/G difference, choose by actual cost/use;
  stop paying to establish service labels as necessary. Unresolved is not equivalent.
- A numerically valid but degenerate G is adverse evidence about this specified G; it
  cannot rescue S, prove all generic methods weak or authorize replacing a cell mid-batch.
- Proxy-only improvement, loss of S−D on new final worlds, conflicting blocks or still
  inadequate absolute service weakens further investment and defaults to no third block,
  early-checkpoint rescue, longer horizon or new module. Stop the present recipe when its
  next information is not worth its cost; that is not proof of a zero effect.

There is no validated deployment threshold or minimum useful return in the supplied task,
so no post-hoc threshold is inferred from old effects. Read magnitudes, components and full
cost together; two positive signs alone are insufficient. Technical defects retain their
failed attempt and cost and quarantine only dependent claims. No automatic retry is selected.
Old 509.11 runner minutes is a historical anchor, not a completion-time promise. Measure
preparation, native collection/update, auxiliary work, evaluation, facts/replay, publication,
fit/batch wall, CPU and process-scoped peak RSS; shared-node timing is not an intrinsic
speed comparison. Non-fit implementation/checks and zero-update replay are reported separately.

**L0 deliverable and ownership.** Restore exact B01 auxiliary/native/entry/tests from frozen
`30401722b14c208bf5330ab66e967c94b3df8a36` as unchanged reusable dependencies and off-path
references. Add `experiments/candidates/uav_service_auxiliary/b03/auxiliary.py`, `native.py`,
`facts.py` as needed, `scripts/run_uav_service_auxiliary_b03.py`, a bounded endpoint replay
entry if needed, and focused mirrored B03 tests. No shared learner/environment/reward edits.
The new production entry binds the fixed seeds/panels and calls `require_admission` before
scientific effects. Results go to runner-written `runs/uav_service_auxiliary/<b03-tag>/`,
including both heads/optimizers/scale in checkpoints and measured counts/movement.

One bounded Implementer owns only B03 auxiliary replay and its focused auxiliary tests;
the DM owns restored references, native collection/evaluation/facts, entrypoints, integration
tests, this notebook, Git index/publication and acceptance. The helper chooses no science,
launches no results and does not write shared files. API: `B03AuxiliaryReplay(actor, arm,
initialization_seed=..., generic_initialization_seed=..., observation_dim=..., action_dim=4)`;
`calibrate(..., normalized_observations=...)` / exact load/export of fixed scale;
`update(actor, observations, skills, dones, qos, *, actions, initial_hidden,
normalized_observations)`; deterministic `predict_all` returning service, observation and
feature tensors; complete checkpoint save/load. Reuse the frozen input/mask/FiLM machinery.

Per pass record weighted loss and counts, head/representation step counts, pre-clip norms,
clip fractions, actual auxiliary movement separately for base/GRU and heads, and target/
prediction/feature norm/variance summaries. The DM records native movement separately.
Fixed initial facts at 0/10/20/30 provide at most 512 deterministic cross-episode/time/agent
valid rows for centered covariance effective rank plus total variance; zero variance is
explicit degeneration. Preserve per-agent/episode-segment variation so pooled rank is not
mistaken for within-history information. Use same transformed rows for OP persistence and
training-mean references. Diagnostics preserve RNG, modes, normalizers and learner state.

Checks trace real storage→W10/next-row pairing→recurrent input→loss→designated parameter
update, cross-chunk and reset cases, D/S off-path identity against frozen replay, isolated
head RNG, shared first collection/native update/scale, no gradients to FiLM/action head,
checkpoint round trip and deterministic no-update replay. A small native integration test
uses pytest-owned scratch and shortened synthetic/checking exposure, never result evidence.
Independent high-risk engineering review covers the actual integrated diff and checks before
publication/admitted execution. Stop dependent work on a real target/RNG/leakage/input
identity/resource conflict, preserve evidence and resolve locally; no repeated owner approval.

## 2026-09-22 — B03 implementation acceptance and node verification

The DM accepted the Implementer's bounded auxiliary diff and the integrated native/factual
paths. D/S service replay is checked against the frozen B01 path; both head initializations
preserve the native RNG. Three-arm real-S7 engineering checks verify identical first
collection, first native update and calibration, then separate native/auxiliary movement,
checkpoint readback and common endpoint replay with zero new updates. Initial G predictions
are saved before training; D's first-training-rollout scale is later applied to those saved
predictions, without rerunning an updated actor as if it were the initial one.

Independent Reviewer identified one concrete replay-boundary defect: hash-valid shortened
engineering endpoints could be accepted as production endpoints. It is repaired by binding
the production specification, training SHA, device/threads, actual evaluation panels/counts
and source policy identity; the production CLI exposes no short-spec override. A regression
now refuses the very engineering roots used by the positive integration test. No material
review finding remains. The review independently ran 15 auxiliary/facts checks; frozen B01
reference files remain byte-identical to `30401722b`.

Local CPU verification passes 24 B03 checks with the CUDA case skipped. The separate frozen
B01 auxiliary check passed five tests with one CUDA skip. Earlier engineering-only failures
were a legitimate inactive configuration infinity sentinel rejected by strict JSON, the
test command missing the documented Ninja PATH, and a regression expecting the old ordering
of two rejection checks. These were reproduced and corrected before result execution;
runtime scientific configuration did not change. This is 0 result fits, not a learning result.
The selected production-shape, four-lane CUDA integration check will run on the configured
node from committed source before the first fit. Its short horizon remains engineering-only.

The configured `wsl_4070` CUDA check at source
`2524168eacab801590a4eb43f63865220b8a609e` passed (1 selected integration test, 20.62 s).
It exercised all three arms with native 256-wide hidden state, 365 observations, four
collection lanes, first-update identity, both checkpoint loaders, fixed-source rejection
and common endpoint replay. It used a 12-step checking horizon and one Torch thread;
the selected result fits remain 1500-step rollouts, 30 rollouts and four Torch threads.
No claim is inferred from its scores. Remote source staging initially stalled outside
the node's configured network shell; only those two owned Git staging process groups were
terminated after PID/command verification, then staging completed through the configured
`zsh -lic` route. There was no accepted result worker or Pro request restart.

The DM accepts the implementation and selects the first fixed cell, D / 912211, at source
`2524168eacab801590a4eb43f63865220b8a609e`. Source is published and the retained node checkout
is `/home/wu/hmasd-worktrees/usa-b03-2524168ea`. Native admission still precedes the actual
start. The later S/G cells will import the first D run's hash-verified initial facts and
training-only calibration after its completed artifact has been read; no score changes
the remaining cells or creates an extra fit.

## 2026-09-22 — B03 D pre-training failure and bounded environment repair

The first D / 912211 attempt was admitted at source `2524168ea`; its native
[manifest](../../../../runs/uav_service_auxiliary/b03_d_912211_a01/launch-manifest.json),
[summary](../../../../runs/uav_service_auxiliary/b03_d_912211_a01/summary.json) and
[exit witness](../../../../runs/uav_service_auxiliary/b03_d_912211_a01/process-exit.json)
are preserved. Both native processes are absent and the valid exit witness is code 1.
The failure occurred on the first fact-environment reset, before any environment step or
optimizer update: all scientific counters are zero; runner wall 1.5122 s, CPU user/system
2.1820/0.2614 s, process peak RSS 849104 KiB. This is one accepted **pre-training attempt**,
0 B03 started training fits, not a scientific negative or a completed D cell. All remote
logs remain at the manifest's paths; nothing is overwritten or relaunched under this handle.

The complete traceback ends in `RuntimeError: Ninja is required to load C++ extensions`.
The CUDA test had explicitly included the scientific venv's bin in PATH; the configured
remote runner prefix omitted it. This explains a difference between test and admitted
execution, rather than a CUDA or scientific-target failure. Verify the diagnosis using the
actual node's kernel-created child environment, with both the old and repaired prefix.

L0 for this bounded shared correctness repair: add the existing configured remote scientific
interpreter's bin directory to `nodes.wsl_4070.path_prefix` in `.codex/hmasd-compute.toml`,
retaining the other entries. Add a focused launcher regression for configured venv tools
and an actual-node Ninja-visibility reproduction; obtain independent executable-config
review. No installation, compiler/source/backend, device, dtype, seeds, loss, horizon or
existing process changes. Publish this shared repair normally and fast-forward the clean
tracked canonical control files so new admission actually reads it. Preserve all unrelated
untracked evidence and other processes. The original stopped attempt stays stopped.

If the reproduction confirms the repair, the DM selects a fresh D / 912211 attempt a02
at the corrected published source and a new output root, with the same scientific exposure.
This is an explicit response to the recorded pre-training defect, not an automatic retry
or new scientific batch. The six-cell design and all reading branches remain fixed.

Independent review found no remaining material defect in the bounded PATH repair. The
reviewer's focused local run passed 7 checks with the actual-node case skipped. On the
configured node, committed source `73be55261b9f5e8f8fe26fdec6558b87ad088fcb` passed all
8 selected launcher checks in 3.60 s. The actual child-environment reproduction finds no
Ninja under the prior prefix, reproduces the recorded PyTorch error, and resolves
`/home/wu/.venvs/hmasd/bin/ninja` with the repaired prefix. This confirms the dependency
visibility diagnosis. No packages or compiler settings were changed.

The scientific implementation and both B03 entrypoints are byte-identical to `2524168ea`.
The DM accepts the repair and selects D / 912211 / a02 at full source
`73be55261b9f5e8f8fe26fdec6558b87ad088fcb`; all six fixed cells will use that same source.
The retained source checkout is `/home/wu/hmasd-worktrees/usa-b03-73be55261`. New execution
depends on publication and canonical adoption of the reviewed configuration, fresh native
resource admission, and a new output root. At this decision there remain 0 B03 started
training fits and one failed pre-training attempt; no native scientific result is inferred
from the repair checks.

## 2026-09-22 — B03 repaired D attempt admitted

The reviewed configuration and retained failure evidence were published to main at
`df79a252025402da65ca8bf7759750d070aabd0e`; canonical control was fast-forwarded with its
tracked files clean and unrelated untracked evidence preserved. The partial clone needed
a missing blob during this update: the first plain-shell merge stalled in its network
helper. After verifying its exact parent chain, only that owned helper was terminated;
the merge returned code 128 with the canonical tracked state still clean. The same update
then completed through the configured network shell. No experiment process was involved.

The selected D / 912211 / a02 attempt is now natively admitted. Its
[manifest](../../../../runs/uav_service_auxiliary/b03_d_912211_a02/launch-manifest.json)
preserves the exact source, command, operation reference and process identities. The native
status at 2026-09-22 17:12:08 UTC reports accepted admission, both matching processes running,
no exit witness and consistent records. Fresh node evidence before admission showed
12.52 GB available host memory and 7948 MiB free GPU memory; the kernel's own immediate
[preflight](../../../../runs/uav_service_auxiliary/b03_d_912211_a02/admission-preflight.json)
remains the admission evidence.

The first copied runner summary is still its initial INCOMPLETE snapshot: failure null,
all persisted counters zero, no updates and empty stderr. It does not certify completion
of initial facts or commencement of training. Preserve that distinction from the earlier
terminal pre-training failure. Subsequent observations use the returned operation reference;
no other cell has started, and no scientific conclusion or additional fit is selected.

## 2026-09-22 — B03 D first training checkpoint

The bounded observer checkpoint at 17:38 UTC retains the same admitted a02 operation:
both native identities are running, the records agree, and no exit witness is present.
The copied runner summary has SHA256
`87d0dde9d49844c2f6ecdc3a07e4d38d6ef2f6e274ea6858bd16831072ec4b39`.
Its config digest matches the retained config and all 10,800 floating-point values are
finite. Failure is null and stderr remains empty. This is an in-progress observation,
not endpoint or artifact acceptance.

The summary records 35,600 training team transitions, including part of the sixth
collection, and 5 completed native/auxiliary updates out of the fixed 30. Initial
development evaluation accounts for 8 worlds / 12,000 transitions and initial facts for
2 episodes / 3,000 transitions. The last completed-rollout resource row records cumulative
wall 1515.47 s and RSS 3,047,892 KiB. Actual cost is now **1 started B03 training fit**;
the separate a01 pre-training failure remains recorded. The other five cells have not begun.

All five completed updates move the native learners; D's auxiliary representation optimizer
steps and base/GRU movement remain exactly zero, while both detached heads update. Service
varies strongly across training collections: rollouts 1, 2 and 4 have nonzero delivery,
rollout 3 has only a small amount, and rollout 5 has zero QoS in all four lanes. The earlier
task commentary incorrectly generalized rollout 5's zero to all five and was corrected
after reading every rollout. These changing training worlds are not the final-world panel
and do not establish a final trend or any D/S/G comparison. Technical execution is supported;
the bounded service-use hypothesis remains untested by the incomplete comparison. Continue
the accepted operation and the fixed horizon without a restart, new fit or score-based change.

## 2026-09-22 — B03 D second training checkpoint

The 18:07 UTC observer checkpoint reports the same two matching native processes running,
consistent records and no exit witness. No newer owner pause or change to this direction's
assignment is present in refreshed main. The copied summary SHA256 is
`909a343d3ec17acc64d0ec9dcbddce2f60e94811a6ef0fb3214727c789fe940b`:
76,000 training transitions including partial collection 13, 12 completed updates, 16
development episodes / 24,000 evaluation transitions, and the same 2 initial fact episodes /
3,000 physical fact transitions. Config digest still matches, all 25,720 floating values
are finite, failure is null and stderr is empty. The last resource row records cumulative
wall 3357.41 s and RSS 3,085,844 KiB. Cost remains one started B03 fit plus the separate
pre-training failure; there is no new launch.

The prescribed rollout-10 development panel has mean raw J -418.874856, QoS .195961 and
return cost .233338, versus initialization -508.082488 / .132604 / .231689 on the same
eight world seeds. This is a within-instance intermediate observation with low absolute
service and mixed per-world changes, not a D/S/G comparison, final panel or checkpoint
selection. Training collections 6–12 also vary substantially. D's auxiliary representation
steps and base/GRU movement remain zero in every new completed update.

On the same two initial-policy fact episodes, the rollout-10 service MSE is .0193532
against its training-mean reference .0101168. Observation MSE is .0149235, training-mean
MSE .00858561 and persistence MSE .00000103515. These adverse predictive diagnostics are
retained: they concern D's detached heads on initial facts, not a trained G arm or common
endpoint mixture. Feature variance is 13.1790 and effective rank 7.4114 on the fixed 512 rows,
with nonzero per-agent and episode-segment variation; this alone establishes no control use.
No final worlds or final checkpoint are available. Continue the same accepted run and fixed
reading without revising the recipe, choosing an early model or adding a fit.

## 2026-09-22 — B03 D third training checkpoint

The 18:35 UTC checkpoint retains the same running a02 identities, consistent records and
no exit witness. Refreshed main leaves this direction active with the same lead and no
new owner pause. Snapshot SHA256
`a7ff7aa2850b339791754b91db7a6b1c93b192df906fe01c0bec60654d09949c`
records 119,600 training transitions, including partial collection 20, and 19 completed
updates. Evaluation remains the two completed development panels at 0 and 10: 24,000
transitions, plus the unchanged 3,000 physical initial-fact transitions. All 40,371 floating
values are finite; the config digest, initialization, initial-fact digest, calibration and
first-rollout bindings match the prior snapshot. Failure is null and stderr is empty.

Completed training collections 13–19 retain varying raw return and service, with D's
auxiliary representation steps and base/GRU movement still zero. No additional evaluation
panel or final result is yet available. The last resource row records cumulative wall
4933.74 s and RSS 3,085,844 KiB. Cost remains one started B03 fit and the separately retained
pre-training failure. Continue observing this accepted operation at the fixed exposure;
the incomplete comparison supports no new package or predictive-mechanism conclusion.

## 2026-09-22 — B03 D fourth training checkpoint

At the 19:02 UTC observer checkpoint the same a02 native identities remain running, with
consistent records and no exit witness. Current published control still authorizes this
direction and introduces no new pause. Snapshot SHA256
`78c81d4a9a782b4a3f6ac79331524c00bcddf065478dfcbdd6fa248be1b036ec`
records 150,400 training transitions including partial collection 26, 25 completed updates,
24 development episodes / 36,000 evaluation transitions, and the same 3,000 initial-fact
transitions. All 53,198 floating values are finite; config, initialization, facts, calibration
and first-rollout bindings remain unchanged. Failure is null and stderr is empty. The last
resource row records cumulative wall 6686.17 s and RSS 3,092,180 KiB. There is still one
started B03 fit, separate from the recorded a01 pre-training failure.

The prescribed rollout-20 development panel has mean raw J -110.657820, QoS .204738,
return cost .135173 and mean episode-minimum battery .371384. Its eight worlds remain
mixed, with one zero-service world; no charging, cutoff or depletion events are observed.
The new completed training collections 20–25 also have no such events, and D's auxiliary
representation steps and base/GRU movement remain zero.

On the unchanged initial facts, service MSE is .110199, while observation MSE is .0102530;
their training-mean references remain .0101168 and .00858561, and observation persistence
MSE remains .00000103515. These predictive diagnostics remain adverse despite the higher
mean development return than at rollout 10; they are not final-world or S/G evidence.
Fixed-row feature variance is 25.8736 and effective rank 7.6482, without a zero-variance
degeneration flag. Retain all observations and continue the accepted operation through its
fixed training and final evaluation. No early checkpoint is selected and no new fit is added.

## 2026-09-22 — B03 D training horizon reached, final evaluation pending

The 19:29 UTC checkpoint still reports both matching a02 processes running, consistent
records and no exit witness. No newer owner pause or assignment change applies. Snapshot
SHA256 `3edf3edfd0f048a4060ae50ebd339f51c7f3071535c16fd42f00872bcf909094`
records the full 180,000 training transitions and 30 completed updates. All four development
panels are complete: 32 episodes / 48,000 evaluation transitions; physical facts remain
the two initial episodes / 3,000 transitions. Final-world evaluation, endpoint facts and
final checkpoint acceptance are still pending. The summary remains INCOMPLETE with failure
null and empty stderr. All 63,932 floating values are finite; earlier completed records and
fixed initialization/config/facts/calibration bindings remain unchanged. The final training
resource row records cumulative wall 7852.55 s and RSS 3,092,180 KiB; it is not total fit cost.

Rollout-30 development mean J is -204.652697, QoS .187162 and return cost .157697.
The mean is below rollout 20 on the same eight seeds, with four worlds improving and four
worsening. This late development decrease is retained; rollout 20 is not substituted for
the fixed endpoint. On initial facts, service MSE is .0116812 and observation MSE .00972033,
still above their fixed training-mean references. Thus the service readout improved since
rollout 20 while mean development return fell; these different-panel measurements are not
a causal mechanism analysis. Fixed-row variance/rank are 28.9133 / 8.8947. D's auxiliary
representation updates remain zero across all 30 passes, and the newly read training and
development records contain no charging, cutoff or depletion events. Continue the same
operation through the pending final-world/fact collection; no later cell is launched yet.

## 2026-09-22 — B03 D complete acceptance and fixed S continuation

The D / 912211 / a02 operation has a valid exit-0 witness; at 19:55:55 UTC both recorded
native identities are absent and the operation records are consistent. The DM has now read
the complete [runner summary](../../../../runs/uav_service_auxiliary/b03_d_912211_a02/summary.json),
all 32 final-world rows, development panels, training/progress records, facts and saved
checkpoints. Summary SHA256 is
`824e706fddd4d9b1f53a80463d8033db9135449c7154a2cec10ded54156ac672`.
All 18 files, totaling 237,191,695 bytes, were copied from the original node and matched
its per-file sizes and SHA256 digests. The large NPZ/PT files remain recoverable in both
the local run directory and `/home/wu/hmasd-worktrees/usa-b03-73be55261/runs/uav_service_auxiliary/b03_d_912211_a02`;
they are not replaced by this prose or added to Git against the repository ignore rules.

Artifact acceptance is separate from process exit. The production-contract readback passed
the frozen source, full production spec, CUDA/four-thread binding, panel identities and
lengths, artifact hashes, fixed calibration, fact metadata/shapes/masks and final policy
fingerprint. Every reported evaluation aggregate was independently recomputed from its
world rows. Saved arrays at 0/10/20/30 independently reproduced the episode-equal service,
observation, persistence and training-mean losses in float64 within the declared float32
rounding tolerance. Both final checkpoints loaded and matched the native optimizer counts,
30 auxiliary passes, 900 updates for each detached head and zero auxiliary representation
updates. This readback performed zero environment steps or optimizer updates.

The completed fit contains exactly 180,000 training team transitions / 30 rollouts / 120
episodes, 96,000 evaluation transitions / 64 episodes, and 9,000 physical fact transitions /
6 episodes (two initial and four endpoint). Initial-fact diagnostics replayed 95,424 valid
agent rows across four checkpoints. Native high-level/actor/critic/team-discriminator/
individual-discriminator optimizer counts are 2,250 / 67,500 / 67,500 / 450 / 1,800, with
nonzero displacement for all native learners. D's auxiliary base/GRU movement is zero on
every pass. No missing final artifacts, runner failure or stderr was found.

The prescribed final 32-world panel at rollout 30 has mean raw J **-96.648955**, QoS
**.219808215**, throughput **6.594246465**, return cost **.137800407**, and mean true
episode-minimum fleet battery **.367119027**. The legacy time-average minimum battery is
.568477819 and is not substituted for the episode minimum. All worlds last 1,500 steps
and truncate. One has zero service; raw J ranges from -1570.825 to 488.390. Charging,
cutoff, depletion and charger-input exposure remain zero. These observations retain the
low-absolute-service, heterogeneity and event-exposure limitations.

The fixed development J curve at 0/10/20/30 is -508.082488 / -418.874856 / -110.657820 /
-204.652697. Its late decrease remains part of the reading; no rollout-20 selection is
made. The final and development panels have different world seeds, so their difference
does not measure a learning improvement. The separate four endpoint-fact worlds have
mean J 48.311094 and QoS .149470470; their facts await the prespecified common D/S/G
mixture after this block completes. They are not extra final-world observations.

On the unchanged initial facts, final service MSE is .0116812224 versus training-mean
.0101167676; observation MSE is .00972032691 versus training-mean .00858561420 and
persistence .00000103514643. Fixed-row feature variance/effective rank are 28.9133 / 8.8947.
The adverse reference comparisons and the earlier disagreement between service MSE and
development J remain contrary evidence. They do not yet evaluate a trained G package or
the common endpoint mixture and cannot identify a predictive mechanism.

Actual D runner cost is **9,828.798293 s / 163.813305 min**, CPU user/system
9,405.779616 / 443.096927 s, and peak RSS 3,092,180 KiB. Stage wall seconds are collection
4,094.20379, native update 2,266.60051, auxiliary update 20.53472, evaluation 2,835.34253,
physical facts 274.13449, fact replay 11.59253, preparation 1.36821 and checkpoint .20688.
This is scoped runner cost under the observed node conditions, not an intrinsic speed claim.
Actual B03 cost at this decision is one completed fit plus the separately retained zero-step
pre-training failure; five fixed fits remain unstarted.

Refreshed published control still lists the same active direction and lead with owner pause
lifted. The technical completeness judgment strengthens; the service-versus-generic package
hypothesis remains untouched by a D-only result, while low absolute service and late
variation remain adverse context. The next discriminating observation is the already
selected S / 912211 / a01 cell at the same 180k horizon, source
`73be55261b9f5e8f8fe26fdec6558b87ad088fcb`, device and panels. S activates service gradients
into the base/GRU while its generic head stays detached. It imports the exact D initial
facts (`8d049f00c9f16367f481e9dabe47c21068d84c8125ba2653e51795cd7ca2f5e5`)
and calibration (`b5b7e03fdc253592f673fc9a0b4d640305a9bd1d7a8ccbca35904d1105012523`)
from that retained run. Initialization, first collection and first native update must match
before auxiliary divergence. A higher final S-minus-D raw J would support this bounded
service-use package contrast, subject to the fixed G contrast and second training block;
an adverse or mixed contrast weakens that reading. No extra fit, horizon change, early
checkpoint, retuning or new Pro Send is selected. Launch remains subject to native admission.

## 2026-09-22 — B03 fixed S cell admitted

The preceding complete D reading and prospective S continuation were committed and pushed
as `792c764e8` before launch. S / 912211 / a01 was natively accepted at 20:07:06 UTC from
the unchanged frozen source `73be55261b9f5e8f8fe26fdec6558b87ad088fcb`. Its
[manifest](../../../../runs/uav_service_auxiliary/b03_s_912211_a01/launch-manifest.json)
binds the exact D facts/calibration hashes and retains the new operation and process handles.
Fresh published control was `9ba1b112316aed0b5ea7323cd5a44de2386650ec`; canonical pause/state/
lead agreed. Native memory preflight passed with 14,762,332,160 available physical bytes.
The preceding GPU probe reported 7,948 MiB free. The native status at 20:07:22 UTC reports
both matching identities running, consistent records and no exit witness.

The first copied [summary](../../../../runs/uav_service_auxiliary/b03_s_912211_a01/summary.json),
SHA256 `8c26595fd00cabac5b23fa9de55c54731b5f59af71421972130db0ec2ecad8ac`, is INCOMPLETE
with failure null and empty stderr. It records the same initialization fingerprint as D,
the exact initial-fact digest, two reused episodes / 3,000 reused transitions, and zero
physical fact generation, training transitions, updates or completed evaluation panels.
Config binds the fixed calibration digest. This early snapshot supports correct initial
input reuse; first-collection and first-native-update equality remain to be observed.
It does not yet establish commencement of a second training fit or any S result.

The completed D observation was consumed with its exact generation, wake and event IDs;
the new native S operation is registered with the deterministic detached observer for
completion, error or a bounded checkpoint. No accepted worker or Pro question was repeated.
One B03 fit is complete, S is admitted and active, four later cells remain unstarted, and
the separate zero-step a01 D failure remains retained. Continue the fixed S operation;
the incomplete package comparison still selects no additional fit or altered recipe.

## 2026-09-22 — B03 S first training checkpoint

The 20:32 UTC observer checkpoint retains the same admitted S / 912211 / a01 operation:
both native identities match and are running, the records agree, and no exit witness is
present. Refreshed published control retains this direction and lead with no new pause.
The copied summary SHA256 is
`e5aa531c7bc0a650f04fcb6e11bab3249b81eeb7187933a5eff43924a4dab183`.
Its 14,928 floating values are finite; config and calibration digests match, failure is
null and stderr is empty. It records 48,000 training transitions / 32 completed collection
episodes, including the eighth collection, with seven completed native/auxiliary updates
of the fixed 30. Evaluation still consists only of the initialization panel: eight worlds /
12,000 transitions. Two D fact episodes / 3,000 transitions are reused with zero new physical
fact generation, and the initial diagnostic replay covers 23,856 valid agent rows.

The matched-start check is now observed, not merely required. Initialization, first-rollout
collection digest `8d78cbcc8f830680e01ce0d3ff889144971ac6c72e8b6f87e2d5bd2826068915`,
first-native-update digest `a194c21bf4bc51e954f7d5b015d35220f3ecb208d49f9fce82745f3362ac4043`
and all first native optimizer counts exactly match D. The complete initial development
panel, first training collection, first native loss record and native parameter displacement
record also match D exactly. Calibration is byte-identical to D, and the initial prediction
array digest is the same. Thus the observed separation begins with the prescribed auxiliary
intervention, without an earlier sampled-history or native-update mismatch.

Every completed S auxiliary pass records 30 representation optimizer steps and nonzero
base/GRU movement, alongside 30 steps for each head; every native learner also moves.
Training service remains heterogeneous: collection 3 has almost no service, collection 5
has zero service in all four lanes, and collection 6 combines poor service with high return
cost in several lanes. All seven completed collections have zero charging, cutoff,
depletion and charger-input exposure. These changing training trajectories are not a
fixed-panel efficacy comparison. No trained development panel, final worlds or endpoint
facts are yet available; the scientific package judgment remains open.

The last completed-update resource row records cumulative wall 1,472.56 s and peak RSS
3,052,116 KiB; this is an intermediate observation, not total fit cost. Actual B03 cost is
now two started training fits, of which D is complete and S remains running, plus the
separate zero-step pre-training failure. Four later fixed cells remain unstarted. The
technical matched-start and active-gradient judgments are strengthened; no endpoint
service advantage is established. Continue this accepted S operation at the fixed horizon
and rearm its observation without a restart, new fit, recipe change or new Pro question.

## 2026-09-22 — B03 S second training checkpoint

The 20:59 UTC native observation retains the same matching S processes running, consistent
records and no exit witness. Refreshed published control still permits this direction under
the same lead; no newer owner pause applies. The copied summary SHA256 is
`8fff77d889e60d5863fb9d1dbdf3b1aa3ce9b1e454ed572bbfd089f65ddfe2d7`.
It records 102,800 training transitions including part of collection 18, 17 completed
updates, 68 training episodes, and two development panels / 16 episodes / 24,000 evaluation
transitions. Physical facts remain zero with the same two D episodes / 3,000 transitions
reused; initial-fact diagnostic replay totals 47,712 valid agent rows. All 36,127 floating
values are finite, prior completed rows and input bindings are unchanged, and progress is
an exact append-only extension. Failure is null and stderr is empty.

The prescribed rollout-10 development panel has mean raw J **99.099574**, QoS **.295123097**,
return cost **.110023676**, and mean episode-minimum fleet battery **.365480650**. All eight
worlds run 1,500 steps and truncate, with zero new optimizer updates during evaluation.
Recomputing every aggregate from the world rows reproduces the saved values. Against D at
the same rollout and on the same world seeds, S-minus-D is **+517.974430 J**, **+.099162156
QoS**, **-.123314326 return cost**, and +.005902641 episode-minimum battery. Seven world J
contrasts are positive; world 920006 is adverse at -682.344841. This is favorable intermediate
development evidence for the S package in this training block, with retained contrary-world
evidence. It is not the prespecified final-world contrast, an independent-seed replication,
or a reason to select an early checkpoint.

On the same initial facts, the runner reports service MSE **.021099299**, versus D
.019353231 (S/D **1.090221**) and the fixed training-mean reference .010116768. Observation
MSE is .015224734 versus D .014923470, fixed mean .008585614 and persistence .000001035146.
The two-episode weighting was independently checked. Thus this favorable early control
contrast is not accompanied by lower initial-fact predictive error; it weakens a simple
explanation that requires improved error on that panel. It does not identify causation or
address trained G and the common endpoint mixture. Fixed-row feature variance/effective
rank are 12.007839 / 7.836655, with no zero-variance flag.

All new completed auxiliary passes retain 30 representation steps with nonzero base/GRU
movement and both head updates; every native learner moves. Training collections remain
heterogeneous, including all-zero QoS in collections 10, 13 and 14. The new training and
development records still have zero charging, cutoff, depletion and charger-input exposure.
The last completed-update resource row records cumulative wall 3,231.93 s and peak RSS
3,057,372 KiB, not final fit cost. Cost remains two started B03 fits (D complete, S running),
four later cells unstarted and the separate zero-step D failure. Preserve both the favorable
development contrast and adverse prediction diagnostics, continue the fixed S horizon and
rearm the same operation. No additional fit, recipe change, early selection or Pro Send is
selected from this intermediate reading.

## 2026-09-22 — B03 S third training checkpoint

The 21:27 UTC observation retains the same admitted S / 912211 / a01 processes running,
matching native identities, consistent records and no exit witness. Refreshed main retains
the direction, lead and lifted pause. Summary SHA256
`a644c212df9b88f64367d972bf9d3fd1654bceb8e48bb4b556b2067df9fa9686`
records 159,600 training transitions including part of collection 27, 26 completed updates
and 104 completed training episodes. Three development panels account for 24 episodes /
36,000 evaluation transitions. Physical fact generation remains zero; two initial D
episodes / 3,000 transitions are reused, with 71,568 valid agent rows replayed across the
three diagnostics. All 55,233 floating values are finite, prior completed records and
input bindings are unchanged, progress extends the previous file exactly, failure is null
and stderr is empty. This remains an incomplete fit.

At the prescribed rollout-20 development panel, mean J is **-53.352798**, QoS **.248211446**,
return cost **.137342195**, and mean episode-minimum fleet battery **.378754210**. All
eight worlds truncate at 1,500 steps with zero evaluation updates; all aggregates were
recomputed from their world rows. S-minus-D at the same rollout/worlds is **+57.305022 J**,
**+.043473605 QoS**, **+.002169274 return cost** and +.007369723 episode-minimum battery.
Only three of eight world J contrasts are positive, with the other five adverse; the range
is -1331.644750 to +1666.680142. One S world has zero service. The average J advantage has
therefore narrowed considerably from +517.974430 at rollout 10, and its per-world pattern
is less favorable. S's own mean J falls by 152.452372 from rollout 10, with four worlds
improving and four worsening. This weakens an interpretation of a stable early S advantage;
it neither establishes a final effect nor permits substituting rollout 10 for the endpoint.

The same initial-fact diagnostic now reports service MSE **.035502055**, compared with
D .110198947 (S/D .322163287), and observation MSE **.009836454**, compared with D
.010253014. Both remain above their fixed training-mean references .010116768 and
.008585614; observation persistence remains .000001035146. Episode-equal scoring and
the common fact identity were checked. Although S's relative service error is now lower
than D's, S's own error has increased since rollout 10 while its development return fell.
The changing relative error ranking does not establish a predictive mechanism. Fixed-row
feature variance/effective rank are 22.040431 / 7.462769, without a zero-variance flag.
Trained G, the final-world panel and the common endpoint mixture are still absent.

All new completed passes retain active service representation updates and movement in
both base and GRU, both head updates, and nonzero native learner movement. Training service
is still heterogeneous, including zero QoS in every lane of collection 24. Newly read
training and development records retain zero charging, cutoff, depletion and charger-input
exposure. The last completed-update resource row records cumulative wall 4,814.23 s and
peak RSS 3,057,972 KiB, not final fit cost. Cost remains two started B03 fits (D complete,
S running), four later cells unstarted and the separate zero-step D failure. Continue the
same fixed S operation through its remaining training and final evaluation, preserving the
weaker intermediate contrast and contrary worlds. Rearm observation; no extra fit, early
checkpoint selection, recipe adjustment or Pro Send is selected.

## 2026-09-22 — B03 S training horizon reached, final evaluation pending

The 21:54 UTC observation still reports both matching S / 912211 / a01 native identities
running, consistent records and no exit witness. Refreshed main preserves this direction's
assignment and contains no newer owner pause. Snapshot SHA256
`bcba7510241a87132da247283daee7a835cab42454bee80eba48a55ada2a81d0`
records the complete 180,000 training transitions / 30 updates / 120 episodes. All four
development panels are complete, totaling 32 episodes / 48,000 evaluation transitions.
The same two D initial-fact episodes / 3,000 transitions were reused, with zero new physical
facts and 95,424 valid agent rows replayed over four diagnostic checkpoints. Final-world
evaluation, endpoint facts, saved final checkpoints and artifact acceptance remain pending.
The runner summary is INCOMPLETE, failure is null and stderr is empty. All 63,874 floating
values are finite; prior completed records, config and input bindings are unchanged, and
progress extends the previous file exactly.

The fixed rollout-30 development panel has mean J **192.471241**, QoS **.362226250**,
return cost **.112110638** and mean episode-minimum fleet battery **.402181969**. Its eight
worlds truncate at 1,500 steps with no evaluation updates; all aggregates were recomputed.
At this same rollout/world panel, S-minus-D is **+397.123937 J**, **+.175064046 QoS**,
**-.045586275 return cost**, and +.039967295 episode-minimum battery. Six world J contrasts
are positive; worlds 920006 and 920007 remain adverse at -1038.728208 and -177.777920.
S's mean J recovers by 245.824038 from rollout 20, with four worlds improving and four
worsening. The full trained development J curve at 10/20/30 is 99.099574 / -53.352798 /
192.471241. This strengthens the favorable development reading relative to the preceding
checkpoint while retaining its nonmonotonic trajectory and adverse worlds. It does not
replace the prespecified, different final-world panel or establish a replicated effect.

On the unchanged initial facts, final service MSE is **.016626176**, versus D .011681222
(S/D **1.423325035**) and the fixed training-mean reference .010116768. Observation MSE
is .010383823 versus D .009720327, fixed mean .008585614 and persistence .000001035146.
Episode-equal weighting and common fact identity were checked. Thus the favorable final
development contrast again occurs with worse predictive error than D on these initial
facts. Preserve this disagreement and the change of relative error ranking across training;
neither error ranking identifies the control mechanism. Fixed-row feature variance/effective
rank are 33.779040 / 8.153838, with nonzero agent/segment variation and no degeneration flag.
Trained G and the common endpoint mixture remain unobserved.

All 30 auxiliary passes retain service representation updates; the four newly read passes
have nonzero base/GRU and native learner movement with both heads updating. New training
and development records still contain zero charging, cutoff, depletion or charger-input
exposure; collection 27 has zero QoS in all lanes. The final training resource row records
wall 5,399.38 s and peak RSS 3,057,972 KiB; the subsequent rollout-30 completion event after
development evaluation is at 5,683.46 s. Neither is total fit cost. Two B03 training fits
have started and reached their training horizon, but only D has complete artifact acceptance;
S's accepted operation continues and four later cells remain unstarted. Retain the separate
zero-step D failure. Continue this same operation through the remaining final evaluation
and collection, and rearm observation. No new cell, extra fit, early checkpoint, recipe
change or Pro Send is selected at this incomplete-result boundary.

## 2026-09-22 — B03 S complete acceptance and fixed G continuation

S / 912211 / a01 has a valid exit-0 witness. At 22:02:15 UTC both retained native process
identities are absent and the operation records are consistent. The DM has read the complete
[runner summary](../../../../runs/uav_service_auxiliary/b03_s_912211_a01/summary.json), all
32 final-world rows, development and training records, endpoint facts and saved diagnostics.
Summary SHA256 is `2c4e71ff76110a2d002645ecf7e1896c0a34ac210df7807afc2882dd05420265`.
All 18 files, totaling 241,916,276 bytes, were copied from the original node and verified
against its per-file sizes and SHA256 digests. NPZ/PT artifacts remain in the local run
directory and `/home/wu/hmasd-worktrees/usa-b03-73be55261/runs/uav_service_auxiliary/b03_s_912211_a01`;
they are retained rather than added against the repository ignore rules. Endpoint-fact,
agent-checkpoint and auxiliary-checkpoint digests are, respectively,
`414bc314340034d46eff5784870d4ba8f5cf141543980431365d9d9e2f34f4fc`,
`6008ac0a50cc383108ccf5fc3ec97c93c4f0f48eaf9b674c6ea90bfa57cd0024` and
`bd652a6ea1d373bee2bbf9948913f271ce5e5a5e024b3a1455718b22b35fe5aa`.

Artifact acceptance is separate from the successful process exit. Production-contract
verification passed the exact source/spec, CUDA/four-thread binding, all panel seeds and
lengths, input/output hashes, fact metadata/shapes/masks and fixed calibration. All reported
evaluation aggregates were independently recomputed from world rows. The four saved initial-
fact arrays independently reproduce episode-equal service, observation, persistence and
training-mean errors in float64 within the declared float32 rounding tolerance; their
features are finite and reproduce reported total variance. CPU checkpoint readback matches
final policy fingerprint `4b68c84f26df1f0add0af57a9e3836ff3529ed8eb6c7281d4a055f6f7ff7d33e`,
native optimizer counts, 30 auxiliary passes and 900 updates each for the representation,
service-head and generic-head optimizers. Calibration is exactly D's. Readback used zero
environment steps and optimizer updates. The loader's empty discriminator-buffer warning
is the expected checkpoint contract and does not change the saved learner weights/counts.

The completed fit contains 180,000 training team transitions / 30 updates / 120 episodes,
96,000 evaluation transitions / 64 episodes and 6,000 new physical fact transitions / four
endpoint episodes. It reuses D's two initial episodes / 3,000 transitions without collecting
them again; four initial diagnostics total 95,424 valid agent rows. Native high-level/actor/
critic/team-discriminator/individual-discriminator optimizer counts are 2,250 / 67,500 /
67,500 / 450 / 1,800, with positive displacement for every native learner. Each auxiliary
pass records service-driven base/GRU movement and both heads updating; there are no
straddling rows. Initialization, first collection and first native update remain exactly
matched to D before auxiliary divergence. Failure is null and stderr is empty.

The prescribed final 32-world panel has mean raw J **-72.063548**, QoS **.275530183**,
throughput **8.265905489**, return cost **.157240885**, and mean true episode-minimum fleet
battery **.375991055**. The legacy time-average fleet minimum is .577749999 and remains
separate. All worlds truncate at 1,500 steps with zero evaluation updates. Two worlds,
936017 and 936029, have zero service; charging, cutoff, depletion and charger-input exposure
are zero throughout this final panel and the newly read endpoint-fact panel.

At the same fixed endpoint/worlds, **S-minus-D J is +24.585407**, QoS **+.055721967**, return
cost **+.019440479** (worse), and true episode-minimum battery +.008872027. Sixteen paired
world J differences are positive and sixteen negative; median is +16.277653, with range
-1401.438827 on 936017 to +2025.595496 on 936011. This retains a small positive descriptive
mean control contrast accompanied by higher service and higher return cost, with substantial
opposing worlds. It weakens the large/robust benefit suggested by the final development
contrast (+397.123937), while preserving that observed development result and its adverse
worlds. The development and final panels use different world seeds; this is not a measured
post-training decline. Absolute raw J remains negative and service remains limited. Thirty-
two worlds are one training-block comparison, not 32 training replications, and balanced
world signs do not establish equivalence or a zero effect.

The unchanged initial facts give final service MSE **.016626176** versus D .011681222
(S/D **1.423325035**) and fixed training-mean .010116768; observation MSE is .010383823
versus D .009720327, fixed mean .008585614 and persistence .000001035146. Fixed-row feature
variance/effective rank are 33.779040 / 8.153838 with no zero-variance flag. These adverse
prediction comparisons and the changing error/control ranking across development remain
contrary evidence to a simple initial-fact-error explanation. They do not measure the
common endpoint mixture or identify prediction semantics. The four separate endpoint-fact
worlds have mean J 149.129266, QoS .323020472, return cost .106778749 and true episode-minimum
battery .428230636. They are inputs to the planned common mixture, not additional final
worlds. That zero-update mixture comparison still awaits G's endpoint facts/checkpoints.

Actual S runner cost is **6,876.480299 s / 114.608005 min**, CPU user/system
6,573.656131 / 319.944001 s and peak RSS 3,057,972 KiB. Stage wall seconds are collection
2,997.277638, native update 1,554.107031, auxiliary update 30.986586, evaluation 2,137.988860,
physical facts 143.584298, fact replay 10.133203, preparation .954058 and checkpoint .144171.
D plus S cost **16,705.278592 s / 278.421310 runner min**, apart from the retained zero-step
D pre-training failure (1.512166 s). These scoped shared-node measurements do not establish
an intrinsic method speed difference. Two of the six planned B03 fits are now fully accepted;
four fixed cells remain unstarted at this entry, and the old four development fits remain
separate historical cost.

Refreshed published main `6f82e921fec608556008982066e99ded85f7b8aa` preserves this direction,
lead and lifted pause. RESEARCH background section 6 requires retaining the distinction
between fixed world panels and training units, full service/risk components and prediction
proxies. It therefore supports the bounded reading above; the directly affected shared
paragraph will retain this weaker new contrast alongside the old two pairs. Technical
completeness and matched-start/active-gradient execution are strengthened. A large or
robust S benefit is weakened; the generic-package comparison and second-block behavior are
still unresolved. There is no current claim that S is worth retaining after the batch.

The next useful observation remains the already selected **G / 912211 / a01**, with the
same source `73be55261b9f5e8f8fe26fdec6558b87ad088fcb`, 180k training horizon, device, four
threads, development/final panels and endpoint-fact protocol. G activates next-legal-
observation gradients into base/GRU while its service head stays detached. It imports D's
exact initial facts (`8d049f00c9f16367f481e9dabe47c21068d84c8125ba2653e51795cd7ca2f5e5`)
and calibration (`b5b7e03fdc253592f673fc9a0b4d640305a9bd1d7a8ccbca35904d1105012523`), with
initialization, first collection and first native update required to match D before the
auxiliary intervention. A useful G-minus-D with no actionable S increment weakens the
reason to pay for this service-specific package; a functioning G below S preserves only
the specified package difference, subject to its small S-minus-D magnitude, components
and second-block evidence. An adverse/degenerate G cannot rescue S or establish service
semantics. The unchanged batch has two training blocks; no third block, new module, horizon
extension, retuning, early-checkpoint rescue or Pro Send is selected. Prospective output is
`runs/uav_service_auxiliary/b03_g_912211_a01`; launch remains subject to native admission.

## 2026-09-22 — B03 fixed G cell admitted

The preceding complete S reading and prospective G continuation were committed and pushed
as `37b268d6a` before launch. G / 912211 / a01 was natively accepted at 22:13:44 UTC from
the unchanged source `73be55261b9f5e8f8fe26fdec6558b87ad088fcb`. Its
[manifest](../../../../runs/uav_service_auxiliary/b03_g_912211_a01/launch-manifest.json)
binds the exact D initial facts and calibration, with operation claim
`6bc2067e6dab42e3168f02aa8f31314d211c06fed0b2dfdf40eaef3b2753a8f5`.
Fresh published control was `6f82e921fec608556008982066e99ded85f7b8aa`; canonical pause,
state and lead agreed. Native memory preflight passed with 13,699,764,224 available physical
bytes. The preceding GPU probe reported 7,948 MiB free. Supervisor/runner identities
263986/263987, session 263986, are retained in the manifest. Native status and the subsequent
22:14:56 UTC observer both report matching processes running, consistent records and no
exit witness.

The first copied [summary](../../../../runs/uav_service_auxiliary/b03_g_912211_a01/summary.json),
SHA256 `b7d369799532a905c10a3d0c8d59e971099e6b26d428949aee1e7acd5ead772a`, is INCOMPLETE
with failure null and empty stderr. Full native config/spec and initialization match D;
the exact two initial episodes / 3,000 transitions are reused and config binds D's fixed
calibration digest. This snapshot contains zero training transitions, updates, completed
evaluation panels or new physical facts. First collection/native-update equality and active
generic-gradient execution remain to be observed. Admission and a running process alone
do not establish a third started training fit or any generic-package result.

The completed S wake was consumed with generation 17 and its exact wake/event IDs. The G
operation is now adopted by the read-only detached observer at generation 19, with zero
probe errors and no pending event; it will return on completion, error or a bounded
checkpoint. No worker restart, Pro Send or cross-task message was made. Two B03 fits are
fully accepted, G is admitted and active, three later fixed cells remain unstarted, and the
separate zero-step D failure is retained. Continue this accepted G operation without a
recipe change; its complete final panel and the block's common endpoint replay remain the
next useful observations under the existing six-fit design.

## 2026-09-22 — B03 G first training checkpoint

The 22:38 UTC observer checkpoint retains the same admitted G / 912211 / a01 operation,
with matching native identities running, consistent records and no exit witness. Refreshed
published main `d4ab3a15bb66adb1b1ef2882a6c2ac4485560b7b` preserves this direction/lead and
the lifted pause. Copied summary SHA256 is
`e25e087b9684b2c6923822afe2928bb1bf8d946dcbcac6dc1b7ea577bc91a9ba`.
It contains 46,000 training transitions, including part of collection 8, seven complete
native/auxiliary updates and 28 completed training episodes. Evaluation remains the initial
eight-world panel / 12,000 transitions. Two exact D initial-fact episodes / 3,000 transitions
are reused, with zero new physical facts and 23,856 valid agent rows in the initial replay.
All 14,928 floating values are finite; failure is null, stderr is empty and config/input
hashes agree. Progress and stdout were read and preserved; no final artifact is expected yet.

The matched-start requirement is now observed for G as well as S. The entire initial
development panel and common-fact diagnostic, first training collection, first native loss
record and native parameter displacement are exactly equal to D. Initialization and first-
native optimizer counts match; collection digest
`8d78cbcc8f830680e01ce0d3ff889144971ac6c72e8b6f87e2d5bd2826068915` and native-update digest
`a194c21bf4bc51e954f7d5b015d35220f3ecb208d49f9fce82745f3362ac4043` are unchanged. Calibration
is byte-identical to D. Remote facts and initial saved prediction-array hashes also match
the already verified D artifacts. Thus all three arms share the observed pre-intervention
start; subsequent trajectory differences follow the prescribed auxiliary intervention.

Each of the seven G auxiliary passes records 30 representation steps, positive movement in
both base and GRU, and 30 updates with positive movement for each head. Every native learner
also moves. All passes have 5,964 valid team starts / 47,712 agent samples. Representation
gradients are finite and below the clip threshold; feature variance remains nonzero in
all 256 coordinates. Collection-feature RMS falls from .917629 to .632778, while total
variance varies from 9.680287 to 7.466999 across changing trajectories. These are training
diagnostics, not a common-fact comparison or evidence of either useful or degenerate G.

Training service remains heterogeneous: collections 3 and 5 have zero QoS in every lane,
and collection 6 includes two zero-service lanes with return costs above .80. All completed
collections truncate at 1,500 steps and have zero charging, cutoff, depletion and charger-
input exposure. Preserve these adverse observations; sampled training histories do not
replace the fixed-panel G-minus-D and S-minus-G contrasts. No trained G development panel,
final-world result or endpoint mixture is yet available. The technical matched-start and
active-generic-gradient judgments strengthen, while the scientific package judgment and
the preceding weak/mixed S-minus-D reading remain unchanged.

The last completed-update resource row records cumulative wall 1,506.666418 s and peak RSS
3,039,560 KiB, not final fit cost. Actual B03 cost now includes three started training fits:
D/S complete and G running; three later fixed cells remain unstarted, with the separate
zero-step D failure retained. The exact checkpoint wake/event was consumed and observation
rearmed at generation 20 for this same operation. Continue the fixed horizon and await the
prespecified trained panels; no restart, extra fit, retuning, early selection or Pro Send
is selected from this intermediate evidence.

## 2026-09-22 — B03 G second training checkpoint

The 23:05 UTC observer retains the same matching G / 912211 / a01 processes running,
consistent operation records and no exit witness. Refreshed main
`345e9d94e3795b7f63d4a5dd202f731144eed8c2` retains this direction/lead and no newer pause.
Copied summary SHA256 is
`5b207f468a2f236ddb193b359541c6be89ad503556cb8159af758ad5d56c9c0e`.
It records 90,000 training transitions / 60 collected episodes, including completed
collection 15, with 14 fully recorded native/auxiliary updates. Two development panels
contain 16 episodes / 24,000 evaluation transitions. The same two D fact episodes / 3,000
transitions are reused, with zero new physical facts and 47,712 valid agent rows replayed
across the two diagnostics. All 29,848 floating values are finite; failure is null and
stderr empty. Prior completed records and input bindings are unchanged; all 118 new
progress events were read, and collection counts/timing and append-only extension agree.

The rollout-10 development panel has mean raw J **67.229066**, QoS **.235510191**, return
cost **.090781179**, throughput 7.065305719 and mean true episode-minimum fleet battery
**.384303886**. All eight worlds truncate at 1,500 steps with zero evaluation updates;
all aggregates were independently recomputed. World 920007 has zero service, and all
charging, cutoff, depletion and charger-input exposure remains zero.

Against D on these same rollout/world seeds, **G-minus-D J is +486.103922**, QoS
**+.039549249**, return cost **-.142556823**, and true episode-minimum battery +.024725877.
Seven world J differences are positive; 920006 is adverse at -705.490339. This is favorable
intermediate control evidence for the specified observation-prediction package, with
substantial return-cost improvement and a smaller service increase. At the same panel,
**S-minus-G J is +31.870508**, QoS **+.059612907**, return cost **+.019242497** (worse), and
true episode-minimum battery -.018823235. Four world contrasts favor S and four favor G;
their median is -33.522659, ranging from -689.297023 on 920007 to +936.028851 on 920005.
Thus both auxiliary packages show development benefit over D at this checkpoint, while
S/G have mixed world outcomes and a service/cost tradeoff. This strengthens G as a useful
observed comparator and weakens a preference for S based only on its large early S-minus-D
development mean. It establishes neither equivalence nor a semantic mechanism. This
eight-world development comparison cannot replace the unobserved fixed final G panel,
second training block or the already weaker/mixed final S-minus-D result.

On the unchanged initial facts, G's rollout-10 service MSE is **.004631897**, versus D
.019353231 and S .021099299; its service head is a detached shadow. It is also below the
fixed service-mean reference .010116768 in aggregate, but episode 932201 is adverse to its
own mean reference (.008181163 versus .007212412), whereas 932202 improves (.001082631
versus .013021124). G observation MSE is **.013599499**, below D .014923470 and S
.015224734 but above fixed mean .008585614 and persistence .000001035146. Episode-equal
scoring was checked from both episode rows; the saved array digest matches the original
node. Fixed-row feature variance/effective rank are 13.084203 / 6.878838, with nonzero
agent/segment variation and no degeneration flag. Lower common-initial-fact error is
compatible with a useful G package here, but the actor histories and trained heads differ;
these diagnostics do not identify the source of its control gain or yet cover the common
endpoint mixture. Lower service-readout error alone is not a reason to select G either.

All seven new completed passes retain 30 representation steps, positive base/GRU movement,
both head updates and positive movement of every native learner. Training remains
heterogeneous, with zero QoS in all four lanes of collection 10 and several other
zero-service lanes. Newly read training records still have no charging/cutoff/depletion/
charger-input exposure. The last completed-update resource row records cumulative wall
3,041.095180 s and peak RSS 3,078,076 KiB; these are intermediate costs. Three B03 fits
have started (D/S complete, G running), with three later fixed cells unstarted and the
separate zero-step D failure retained. The checkpoint was consumed using its exact
generation/wake/event and observation rearmed at generation 21. Continue the same fixed
G operation; no extra fit, early selection, recipe change or new Pro question is selected.

## 2026-09-22 — B03 G third training checkpoint

The 23:33 UTC observer retains matching G / 912211 / a01 identities running, consistent
records and no exit witness. Refreshed main `0f692f8cfff0dbd25b6ffae70683366fa89e9c8c`
preserves this direction/lead and the lifted pause. Copied summary SHA256 is
`6cc76f321250c41c96b3b5e5afc6cd72048d6c2330a5ee61f785945f26e4c517`.
It records 143,600 training transitions, including part of collection 24, 23 complete
updates and 92 completed training episodes. Three development panels total 24 episodes /
36,000 evaluation transitions. The exact two D initial episodes / 3,000 transitions are
reused, with zero new physical facts and 71,568 valid agent rows replayed across three
diagnostics. All 48,954 floating values are finite; failure is null and stderr empty.
Prior completed records and input bindings are unchanged. All 144 new progress events
were read, with monotonic timing, consistent collection counts and append-only extension.

At rollout 20, G's prescribed development mean raw J is **-75.744959**, QoS **.249717513**,
return cost **.145632532**, throughput 7.491525390 and true episode-minimum fleet battery
**.366664266**. All eight worlds truncate at 1,500 steps with zero evaluation updates;
all reported aggregates were independently recomputed. Each world has nonzero service,
but charging, cutoff, depletion and charger-input exposure remains zero.

At this same rollout/world panel, **G-minus-D J is +34.912861**, QoS **+.044979672**, return
cost **+.010459611** (worse), and true episode-minimum battery -.004720220. Three world J
differences are positive and five negative; median is -190.534761, range -1353.909090 on
920006 to +1385.786795 on 920008. The mean gap has narrowed sharply from +486.103922 at
rollout 10, with both G's own decline and D's improvement contributing. G's own J drops
142.974025 on the same development worlds: two improve and six worsen. Its QoS rises
.014207322, while return cost rises .054851353 and true episode-minimum battery falls
.017639620. Thus more delivered service does not prevent a worse complete return here;
the earlier favorable generic-package reading is weakened by this later comparison.

**S-minus-G J is +22.392161** at rollout 20, with QoS -.001506067, return cost -.008290337
and true episode-minimum battery +.012089944. Six world J differences favor S and two
favor G; median is +54.794257, and 920007 is notably adverse to S at -679.723691. Preserve
this modest mean advantage and differing service/risk components without treating the
worlds as training replications. Neither this development result nor the earlier one
replaces G's unobserved final 32-world endpoint or the second training block. There is
still no completed three-arm package comparison or basis for early-checkpoint selection.

On unchanged initial facts, G observation MSE improves from .013599499 to **.009703034**,
below D .010253014 and S .009836454 at rollout 20, but still above fixed mean .008585614
and persistence .000001035146. Meanwhile its detached service-readout MSE worsens from
.004631897 to **.197741939**, above D .110198947, S .035502055 and service-mean .010116768.
Both fact episodes are now adverse to their service-mean references (.223737172 versus
.007212412, and .171746706 versus .013021124). Episode-equal scoring was checked and the
saved array digest matches the node. Fixed-row feature variance/effective rank are
15.935531 / 8.395262, with nonzero agent/segment variation and no degeneration flag.
The declining observation error alongside declining native J is contrary evidence to
using that proxy as a control-benefit criterion; the earlier low service-readout error
also fails to persist. These observations do not identify a mediator or establish that
the generic package is technically degenerate. The common endpoint mixture remains absent.

All nine new complete passes retain active observation-driven representation steps and
positive movement in base/GRU and every native learner, with both heads updating.
Training remains heterogeneous; collection 22 has zero QoS in every lane. Newly read
training records retain zero charging/cutoff/depletion/charger-input exposure. The last
completed-update resource row records cumulative wall 4,795.805478 s and peak RSS
3,079,224 KiB, not total fit cost. Cost remains three started B03 fits (D/S complete,
G running), three later fixed cells unstarted and the separate zero-step D failure.
Consume this checkpoint and rearm the same operation at generation 22. Continue the
fixed G horizon and retain the adverse trajectory; no restart, additional fit, retuning,
early checkpoint or Pro Send is selected.

## 2026-09-22 — B03 G training horizon reached; final evaluation pending

The 00:01 UTC September 23 observer retains the same matching G / 912211 / a01 processes
running, consistent records and no exit witness. Refreshed main
`9ff4925d56f5361aeb28ac5574acdb1f71a2c169` preserves this direction/lead and no newer pause.
Copied summary SHA256 is
`451ab9c5ae4599e77b780f88e0b728615e98137082e161d9a13d528054ed2b26`.
Training has reached its fixed **180,000 transitions / 30 updates / 120 episodes**. The
four development panels contain 32 episodes / 48,000 evaluation transitions; the final
32-world panel, endpoint facts, checkpoints and final resource totals remain pending.
The two D initial episodes / 3,000 transitions are still reused, with zero new physical
facts and 95,424 valid agent rows replayed across four diagnostics. Status is INCOMPLETE,
failure null and stderr empty. All 63,874 floating values are finite. Input hashes and
previous completed records are unchanged. All 99 new progress events and seven completed
training passes were read, with consistent counts and monotonic timing. Training-horizon
completion does not constitute completion or scientific acceptance of this fit.

The rollout-30 development mean raw J is **10.885286**, QoS **.234182821**, return cost
**.109122334**, throughput 7.025484617 and true episode-minimum fleet battery **.374662911**.
All eight worlds truncate at 1,500 steps with zero evaluation updates; aggregates were
independently recomputed. World 920002 has zero service. Charging, cutoff, depletion and
charger-input exposure remains zero throughout this panel.

On the same rollout/world panel, **G-minus-D J is +215.537983**, QoS **+.047020617**, return
cost **-.048574578** and true episode-minimum battery +.012448236. Seven world J differences
favor G and one favors D; median is +106.474426, with the adverse 920002 difference
-53.615460. **S-minus-G J is +181.585954**, QoS **+.128043429**, return cost **+.002988303**
(worse) and true episode-minimum battery +.027519059. Six worlds favor S and two favor G;
median is +119.687440, with adverse differences -1136.047197 on 920006 and -296.355944 on
920007. This restores a favorable development G-minus-D comparison after its narrower
rollout-20 gap, and the S-minus-G development mean grows. Preserve the adverse worlds and
S's service/cost tradeoff; neither contrast supplies the missing final G endpoint.

G's own J recovers **86.630245** from rollout 20, while QoS falls .015534692, return cost
falls .036510198 and true episode-minimum battery rises .007998644. Five worlds improve
and three worsen, including large declines on 920001, 920002 and 920008. Its trained
development trajectory is **67.229066 / -75.744959 / 10.885286** at rollouts 10/20/30:
the late recovery remains below rollout 10. This strengthens evidence that return-cost
changes matter to the whole objective, while weakening any smooth or monotonic benefit
reading. The weak/mixed final S-minus-D result remains unchanged. No early selection,
training-population conclusion, equivalence or semantic-mediator claim follows.

On the unchanged initial facts, the detached service-readout MSE recovers from .197741939
to **.005864226**, below D .011681222, S .016626176 and service-mean .010116768 in aggregate.
Episode 932201 remains adverse to its own mean reference (.008517807 versus .007212412),
whereas 932202 improves (.003210645 versus .013021124). Observation MSE worsens from
.009703034 to **.010363129**, above D .009720327, just below S .010383823, and above fixed
mean .008585614 and persistence .000001035146. Both fact episodes remain adverse to their
observation-mean references. Episode-equal scores were checked from both rows; original-node
array SHA256 `b7e17f3e182a0bf583953366963d6016b7d58adefd32fa347ff9ba8b5e80f4e1`
matches the summary. Fixed-row feature variance/effective rank are 23.165562 / 8.740836,
with nonzero per-agent and segment variation and no degeneration flag. G again has the
lowest service-readout error while S has higher development return; observation error
worsens while G return recovers. These changing rankings further weaken either proxy
as a control-benefit criterion. They do not identify a mechanism or replace the still
absent common endpoint mixture.

All seven new updates retain 30 representation steps and 30 steps for each head, positive
base/GRU and head movement, and positive movement of every native learner; each has 5,964
valid team starts / 47,712 agent samples. Training remains heterogeneous: collection 29
has QoS at most .0058 in every lane, and collection 30 includes two zero-service lanes.
All newly completed collections truncate at 1,500 steps with no charging/cutoff/depletion/
charger-input exposure. The last training resource row records cumulative wall
5,986.629868 s and peak RSS 3,079,224 KiB; the rollout-30 completion event after development
evaluation/replay is at 6,282.249290 s. Neither is final fit cost. Three B03 training fits
have started: D/S accepted, G final evaluation pending; three later fixed cells remain
unstarted, and the separate zero-step D failure is retained. Consumed the exact
generation-22 wake/event and rearmed the same accepted G operation at generation 23.
Await the fixed final panel and full artifact readback; no new cell, worker restart,
retuning or Pro Send is selected at this checkpoint.

## 2026-09-22 — B03 G complete acceptance and fixed common-endpoint replay

The 00:21 UTC September 23 READY event has a valid exit-zero witness for the original
G / 912211 / a01 operation, absent original processes and consistent native records.
Fetched main `f82f7265b0724c88627cf63d7a4849f3735c6c32` retains the lifted pause and this
direction/lead; concurrent changes concern other owned entries. All 18 files / 243,910,798
bytes were copied from the original node and individually checked against its SHA256s.
The final summary is `54c16736a8101dab32aa53f66858d6e8e0cb601f9f1c8a812cd681486ceeefde`.
An initial local inspection preceded completion of that copy and found the not-yet-copied
checkpoint; after transfer completed, full verification passed. This was a local readback
ordering error, with no missing remote asset, worker failure or repeated scientific action.

Accept the completed G fit after reading all final-world and endpoint-fact rows and
independently recomputing their aggregates. The fixed production specification, source,
CUDA/four-thread contract, artifact digests and panels pass the production verifier.
Counts are **180,000 train / 30 updates / 120 training episodes; 96,000 evaluation
transitions / 64 episodes; 6,000 physical endpoint-fact transitions / four episodes**,
with two exact D initial episodes / 3,000 transitions reused and 95,424 diagnostic agent
rows replayed. All 64,606 reported floating values are finite, failure is null and stderr
empty. Earlier training/panel/resource records are unchanged. D/G initialization,
rollout-zero panel/diagnostics, first collection and first native update match exactly.
Every native learner and both auxiliary heads move; all 30 passes move base/GRU with the
fixed valid rows. Native optimizer steps are high 2,250, actor/critic 67,500 each, team
discriminator 450 and individual discriminator 1,800. Both heads and the active generic
representation optimizer each have 900 actual steps, including every saved optimizer state.

Final checkpoint SHA256s are agent
`869e5ed10e4b81d39bbf449a2b7f00e1bb6c1a7f2e59b65085fa8f1658e19643` and auxiliary
`318e09baa0244d2fe0bdb70f045844cc742ddfb8672d5f65f3483f03097b4321`.
CPU readback restores the exact policy fingerprint
`26a75bafb67af6c9d290198167b8c65d987790d1b0fc91261e80c21eba3039e5`, all native steps,
both heads and the unchanged D calibration. Initial/endpoint fact metadata, seeds, shapes,
finite arrays, single final done and policy/source identity were checked. All four saved
initial-fact prediction archives were independently rescored using direct float64 W10
windows and next-observation arithmetic, including episode weighting and feature spectrum;
maximum score difference from the runner is 2.943e-9, consistent with its float32 labels.
This readback added zero environment transitions and optimizer updates. Binary assets
remain hash-bound on the original node and locally, under their existing ignored paths.

On the final 32 worlds, G mean raw J is **21.247479**, QoS **.260098279**, return cost
**.118462317**, delivered throughput 7.802948369, true episode-minimum fleet battery
**.364596667**, and historical time-mean fleet-minimum battery .568461935. Every world
truncates at 1,500 steps; world 936017 has zero service. Charging, cutoff, depletion and
charger input remain zero. Throughput is still 30 times QoS, not independent evidence.

| Final-world contrast, block 912211 | Mean raw J | QoS | Return cost | True episode-minimum battery | World J signs |
| --- | ---: | ---: | ---: | ---: | --- |
| S minus D | +24.585407 | +.055721967 | +.019440479 | +.008872027 | 16 positive / 16 negative |
| G minus D | **+117.896434** | **+.040290063** | **-.019338089** | -.002522361 | 23 positive / 9 negative |
| S minus G | **-93.311027** | +.015431904 | **+.038778568** | +.011394388 | 11 positive / 21 negative |

G-minus-D median world difference is +237.193285, range -748.364249 on 936023 to
+593.193739 on 936025. S-minus-G median is -252.778236, range -852.253597 on 936029 to
+1678.882294 on 936011. Preserve all adverse worlds and the components: G improves both
mean service and return cost over D, but has a slightly lower minimum-battery mean; S
delivers somewhat more service than G with more return cost and lower complete J. G's
own negative-J worlds include 936011 (-1224.111838) and 936032 (-1381.145755), so a
positive aggregate does not establish adequate absolute service or broad reliability.

This strengthens the specified ordinary G package as a functioning and descriptively
useful comparator in this block. It weakens preferring S from the development panels:
rollout-30 S-minus-G is +181.585954 on development worlds but -93.311027 on final worlds.
These are different world panels at the same policy endpoint, not additional training
or proof of temporal regression. The earlier large S-versus-detach effects do not recur
at their previous scale in this contemporaneous final comparison. Current shared
background at the fetched revision already distinguishes service/cost tradeoffs and
prediction error from control usefulness; G now supplies the previously missing ordinary
comparison. The stronger working reading is that a useful auxiliary package need not
use service labels, while this block supplies no reason to claim service-label necessity.
The three contrasts still represent one training block, with no stable ranking,
equivalence, semantic isolation, deployment or population claim.

Initial-fact diagnostics retain the preceding entry's nonmonotonic error/rank histories;
G's final service MSE .005864226 and observation MSE .010363129 are conditional on the
two initial-policy episodes. The separate G endpoint-fact panel has J **380.235814**, QoS
.263084385, zero return cost and true episode-minimum battery .416531424; all four worlds
truncate at 1,500 with no charging/cutoff/depletion/input events. Endpoint-facts SHA256 is
`e6961f5618801336fe26f8f4700090326fe6d8305eb420195d0392c423674439`.
These favorable fact-collection worlds do not replace the final native panel. They now
complete the frozen 12-episode D/S/G common-endpoint mixture needed to test whether the
initial-fact readout ranking persists across the three policies' factual distributions.
Either ranking is explanatory only and cannot override native J.

G runner wall is **7,657.884149 s / 127.631402 min**, CPU user/system
7,326.130296 / 349.930746 s, and process peak RSS 3,079,224 KiB (2.936577 GiB). Stage walls
are preparation .936549, collection 3,330.298521, native update 1,778.102620, auxiliary
35.441563, evaluation 2,339.069361, facts 160.269204, replay 11.480051 and checkpoint
.189750 seconds. Three accepted B03 fits total **24,363.162741 s / 406.052712 runner min**,
540,000 train, 288,000 evaluation and 21,000 physical fact transitions. The zero-step D
failure's 1.512166 s remains separate. Shared-node elapsed times are not intrinsic speed
comparisons. Three second-block cells remain unstarted.

**Selected next action within the frozen plan:** run the reviewed zero-update endpoint
replay at unchanged source `73be55261b9f5e8f8fe26fdec6558b87ad088fcb`, CUDA/four threads,
output `runs/uav_service_auxiliary/b03_endpoint_replay_912211_a01`. Bind D/S/G summaries to
`824e706fddd4d9b1f53a80463d8033db9135449c7154a2cec10ded54156ac672`,
`2c4e71ff76110a2d002645ecf7e1896c0a34ac210df7807afc2882dd05420265`, and the G digest above,
respectively, at the three accepted original-node run paths. Each endpoint replays all
12 factual episodes, retaining episode-equal aggregation and source-arm strata:
**zero new fits, optimizer updates and environment transitions**; expected 429,408 valid
agent rows across all nine policy/source combinations. Do not modify training, heads,
normalization, seeds or calibration. Existing Pro advice explicitly covers this diagnostic
and the bounded second-block recurrence question, so no repeat consultation is selected.
The second block remains useful for distinguishing recurrence of G's descriptive benefit
and the S/G service-cost tradeoff from a block-specific ranking; the common replay is
read first and does not authorize an extra fit or a changed recipe. The exact completed-G
wake/event was consumed at generation 24, with no remaining accepted training process.

## 2026-09-22 — B03 fixed common-endpoint replay admitted

The exact replay inputs and completed-G reading were committed/pushed in `407da2464`
before the single new invocation. Native admission accepted the fixed replay at 00:29 UTC
September 23 against main `f82f7265b0724c88627cf63d7a4849f3735c6c32`; source remained clean
and the output did not previously exist. The runner and supervisor identities match and
records are consistent. The authoritative handle and exact input digests are in the
[native manifest](../../../../runs/uav_service_auxiliary/b03_endpoint_replay_912211_a01/launch-manifest.json).
The first copied snapshot is INCOMPLETE with D/S replay sections recorded, 286,272 agent
rows, no failure and zero new fits, optimizer updates or environment transitions. The
three stderr messages report absent discriminator replay buffers on checkpoint loading;
these fixed-policy loaders create empty buffers and perform no discriminator learning.
They do not change the restored policy identities or constitute a resumed training fit.
Automatic observation is registered against this exact native claim. Read and verify the
whole three-arm result after completion; second-block training remains unstarted.

## 2026-09-22 — B03 common-endpoint replay accepted and second block retained

The same replay operation completed with a valid exit-zero witness at 00:30 UTC September
23. All 17 files / 668,781,720 bytes were recovered and checked against original-node
SHA256s. Summary digest is
`615ab6fffce72457f7784e0fc5574c7f2424e5056b2b1d1e2e23f688aaeef5cc`.
Read all nine source strata and 36 policy/episode scores. Status is COMPLETE, failure null,
and all 1,881 reported floating values are finite. The three restored policy fingerprints
match their accepted training endpoints before/after replay, and all input summary,
calibration and factual-policy identities match. There are exactly **429,408 valid agent
rows, zero new fits, zero optimizer updates and zero environment transitions**.

The nine saved prediction archives were independently rescored with direct float64 W10
windows, legal next-observation coordinates and episode-equal reductions. All 36 scores,
nine stratum means and three mixture means agree within maximum absolute error 4.014e-9;
the small discrepancy is consistent with float32 runner labels. Saved seeds/QoS/dones
match the source facts, and each source's normalized factual inputs match across all
three readouts. Each episode has 1,491 valid starts / 11,928 agent rows; no episode is
missing. The 512-row feature samples, selection indices, variance and effective rank
were independently checked. This readback adds no training or environment interaction.
The D/S sections are unchanged from the first snapshot. Accept the completed diagnostic;
its source strata and binary-array identities remain in the runner-written summary.

| Factual source | D service MSE | S service MSE | G service MSE | D observation MSE | S observation MSE | G observation MSE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| D endpoint, four episodes | .010311016 | .017367963 | .021386320 | .019620017 | .022893773 | .020707128 |
| S endpoint, four episodes | .039695826 | .028320992 | .081293670 | .034882359 | .029610588 | .033069611 |
| G endpoint, four episodes | .013669773 | .017019269 | .051454015 | .021906366 | .020292745 | .025529430 |
| Equal 12-episode mixture | **.021225538** | **.020902741** | **.051378002** | **.025469580** | **.024265702** | **.026435390** |

The common service-mean reference has mixture MSE .047533042; the observation-mean and
persistence references are .024824760 and .000146870. S is slightly below the observation
mean in aggregate; D/G are above it, and all three are far above persistence. G's lowest
initial-fact service error does not generalize to this endpoint mixture: its service
MSE is now highest in every source stratum, 2.420575 times D in the mixture and above
the fixed service-mean reference overall. G is worse than that mean on its own source
stratum and D's, though below it on the S-source stratum. This is a specific failure of
the earlier initial-fact error ranking, not evidence that G failed to train or collapsed.
All feature summaries retain nonzero variation: effective ranks span 6.785709–20.296357
across readout/source pairs, with no degeneration flag.

S's mixture service MSE is only .000322797 below D (ratio .984792), and this average
conceals worse errors in **11 of 12** common episodes. Its single favorable episode is
the S-source 933204 trajectory: S MSE .052268160 versus D .109546312, a difference
-.057278152 that outweighs the other eleven increases. S is worse than D in both D- and
G-source stratum means. Retain this concentration rather than treating a slightly lower
mixture average as a broad predictive advantage or equivalence. S has lower observation
MSE than D in nine episodes and lower service/observation MSE than G in ten/nine episodes,
respectively, yet the final native panel favors G in aggregate. The package with the
highest native mean also has the highest mixture error for both readouts. This further
weakens forecasting accuracy or service-readout accuracy as a selection/mediation rule
under these fixed conditions. The study does not identify which learning effect produced
the native benefit; neither the mixed factual distribution nor the readouts are the full
control task, and no new gradient intervention was made.

Replay runner wall is **54.365640 s / .906094 min**, CPU user/system 51.115133 / 14.982371 s,
and process peak RSS 1,503,000 KiB (1.433372 GiB). Accepted first-block training plus this
separate diagnostic totals **406.958806 runner min**; the earlier zero-step failure,
implementation, transfers/publication and readback remain outside that sum. Three fits
are complete, with no fourth fit yet started at this decision. The exact generation-25
READY wake/event was consumed and observation advanced to generation 26.

**Continue the already fixed second block.** Refreshed main
`1a153dc5d61a094841a6fea05fa56eb0251b6825` retains this lead and lifted pause, and the
one-training-block and proxy-versus-native limits recorded in the G acceptance entry.
Its newly published S1 pooling-versus-MLP cost/service loss reinforces measuring ordinary
packages rather than assuming their benefit; it does not alter this frozen S7 comparator
or negate the observed G-minus-D result under different conditions.
The strongest stop argument is S's small mixed final increment, unfavorable S-minus-G,
low absolute service and unstable proxy ranking. I retain the prespecified second block
because recurrence now distinguishes a functioning ordinary auxiliary alternative from
a block-specific favorable ranking, and can change the bounded package-retention judgment.
The working expectation is positive G-minus-D native J with higher service/lower return
cost, and no favorable S-minus-G complete-return increment. A favorable S-minus-D and
S-minus-G with acceptable observed components in block two would instead make the blocks
conflict; loss of both auxiliary increments would weaken even the ordinary-package
benefit. Neither outcome authorizes averaging away adverse evidence or adding a third
block. These are comparisons at the existing fixed endpoint, not new numerical acceptance
thresholds. The common-fact reading supplies no semantic-mediator claim and changes none
of the six-fit design's conditions or investment branches. Prior complete Pro advice
covers this planned recurrence and remains applicable; no repeat Send is selected.

Execute the remaining **D/S/G at training seed 912347**, in that order, three fixed fits
of 180,000 training transitions each: 540,000 train, 288,000 nominal evaluation and 21,000
physical fact transitions for this block. Retain source
`73be55261b9f5e8f8fe26fdec6558b87ad088fcb`, wsl_4070 CUDA FP32/TF32-off/four threads, the
30-update horizon and all prior losses, optimizers, gradients, panels and no-early-selection
rules. D first creates initial facts on 932211/932212 and the training-only calibration;
S/G must reuse those exact block-two inputs. Endpoint-fact seeds are 933211–933214; the
development and final worlds remain as fixed in the original plan. The next output is
`runs/uav_service_auxiliary/b03_d_912347_a01`, absent on the node at this reading. Commit
and push this decision before its single native launch. No new module, tuned target,
extended horizon, replacement G, additional block or confirmation is selected.

## 2026-09-22 — B03 second-block D admitted

The complete common-fact reading and fixed second-block decision were committed/pushed
in `9395b11c1` before one new D / 912347 / a01 invocation. The first immediate status
probe preceded manifest creation; the original supervisor log and then native status
reconciled that same invocation without another launch. Native admission accepted it at
00:38 UTC September 23 against main `1a153dc5d61a094841a6fea05fa56eb0251b6825`, with fresh
physical/effective available memory 13,268,672,512 bytes above the configured 4-GiB floor.
The scientific runner and supervisor have matching live identities, no exit witness and
consistent records. Exact source, command, identities and operation reference are retained
in the [native manifest](../../../../runs/uav_service_auxiliary/b03_d_912347_a01/launch-manifest.json).

The copied first summary SHA256 is
`5a4ab92583550a5af75f188da00a3e97648a53be9385d2e832905ce359cdebfc`.
It is INCOMPLETE with all reported training/evaluation/fact counters zero, failure null
and empty stderr; no trained second-block result is inferred. Config SHA256
`b3d8c34afd6e46173202acbdaf8bd7c9499b56bd7de77e770bb3c5d951090793`
matches the exact production specification for seed 912347, including the shifted initial
and endpoint-fact seeds and unchanged development/final panels. Automatic observation is
registered against this accepted native claim. Four of six planned fits are now launched:
three first-block fits accepted and second-block D running; S/G remain unstarted. Keep
the fixed horizon and read D's calibration/initialization evidence before binding S/G.

## 2026-09-22 — B03 second-block D first training checkpoint

The 01:03 UTC September 23 observer retains the same matching D / 912347 / a01 identities
running, consistent records and no exit witness. Refreshed main
`a7d16ff220231dff37b413ab4b746c6b552d3073` preserves this direction/lead, lifted pause and
owned shared-background entry. Copied summary SHA256 is
`01b2248a339e45547351adfca5c82baf4d0a64d903dde8747e3c6152ea75dc79`.
The snapshot records **43,600 training transitions, seven completed native/auxiliary
updates and 28 completed training episodes**, including part of collection eight.
Only the rollout-zero development panel is present: eight episodes / 12,000 evaluation
transitions. D collected the two prescribed initial-policy fact episodes / 3,000 physical
transitions, with 23,856 valid agent rows replayed. Status remains INCOMPLETE, failure null
and stderr empty. All 15,717 floating values in the summary and calibration are finite.
Read all 118 progress events and seven complete training passes; collection counts,
update/episode totals and monotonic timing agree. No trained development panel, final
evaluation or second-block auxiliary comparison is available yet.

Block-two initialization fingerprint is
`10cdc004027e2ee04c4aa3c5bc7f0e2938df00bb1bc52d346c2886f21a9aa720`.
The exact new initial-facts digest is
`163d34ce6dc14e2cf6273c503ec8e086589b39908c19632af30c1b3bb3a727ae`, with seeds 932211/932212
and the matching initial policy. Calibration digest is
`0c49d91203e9e6d18a38d5650207873a7eeb91b536f582a35fea9ee312591ebb`.
Its scientific binding matches the summary's first-rollout record, including collection
`ee1d01c195f9197226e4b41d360c0a38957c8b4a61af16ff7622b0dfc93e7eb7` and first native update
`4ee61c8f3ecb466faca8609273f17b007bfd9258b4dac57e43774bbbbe711c8f`.
The training-only coordinates use 5,964 valid team starts / 47,712 agent rows, 365 finite
means and scales (all scales equal one here); fixed service-target mean is .043316392.
First native optimizer steps are high 75, actor/critic 2,250 each, team discriminator 15
and individual discriminator 60. Future S/G must match these block-two inputs; first-block
facts or calibration are not interchangeable with them.

The initial development mean raw J is **-431.411727**, QoS **.121938558**, return cost
**.200757110**, throughput 3.658156747 and true episode-minimum fleet battery **.347762066**.
Worlds 920002 and 920007 have zero service. The initial factual panel has J **-800.611213**,
QoS .087434656 and return cost .306928046; episode 932212 has zero service and J
-1645.974128. All ten evaluation/fact episodes truncate at 1,500 steps, with zero optimizer
updates and no charging, cutoff, depletion or charger input. Aggregates were independently
recomputed from the complete world rows. These establish this block's untrained starting
conditions, not a learned package effect or a comparison with first-block trained policies.

On those two initial facts, the untrained service/observation MSEs are **.141869610 /
.074281531**, versus fixed service-mean .009677077, observation-mean .006262023 and
persistence .000001321245. Both episode rows are adverse to their respective mean
references. Episode-equal reduction and metadata were checked; original-node saved-array
digest `894ec96a001412e9b0f5b846ac523f9f8f6494d070628ac0bb7bf64e00dee2be` matches the report.
Reported fixed-row feature variance/effective rank are 80.812081 / 1.970603, with nonzero
per-agent variation and no degeneration flag. The saved initial heads are untrained;
these values are a reference for later panels, not evidence of failed trained prediction.
Full binary readback and independent saved-array rescoring remain part of D completion.

Every native learner moves in all seven complete updates. Each detached head receives
30 steps per pass with positive parameter movement; auxiliary representation steps and
base/GRU movement remain exactly zero, as required for D. All passes retain the fixed
5,964/47,712 valid-row counts. Training service is sparse: collections **2 and 3 have zero
QoS in all four lanes**, with further zero-service lanes throughout the seven collections.
All completed training episodes truncate at 1,500; charging/cutoff/depletion/input exposure
remains zero. These adverse training observations are retained without changing horizon
or treating them as a final negative package comparison. The technical detached-control
judgment strengthens; first-block package readings and the planned recurrence question
are unchanged until trained second-block comparisons exist.

The last completed-update resource row records cumulative wall **1,554.436201 s** and
peak RSS **3,049,804 KiB**, not final fit cost. Four planned fits are launched, three
first-block fits accepted and second-block D running; second-block S/G remain unstarted.
Consumed the exact generation-27 checkpoint wake/event and rearmed the same operation
at generation 28. Continue its fixed horizon; no restart, new cell, retuning or Pro Send
is selected from this checkpoint.

## 2026-09-22 — B03 second-block D development-ten checkpoint

The September 23 01:32 UTC checkpoint and 01:34 UTC direct status read retain the
original D / 912347 / a01 runner/supervisor identities, consistent records and no exit
witness. Refreshed main `0fed22d9758227f6545d0e4e78ba78fdc7cc82eb` preserves the lifted
pause, this direction/lead and its fixed B03 work. Copied summary SHA256 is
`5e57b3d96d9cbfc3dc4561e124a83e8773f45342a654a77a3f124f26da57e04c`.
It records **90,000 training transitions, 14 completed updates and 60 completed
episodes**: collection 15 is finished, but its update is not in this snapshot.
Status remains INCOMPLETE, failure null and stderr empty. Development panels zero/ten
total 16 episodes / 24,000 evaluation transitions; the same two initial facts account
for 3,000 physical transitions and two readouts total 47,712 replayed agent rows.
All previously read completed records, initial facts, calibration and bindings are
unchanged. All 30,637 floating values in summary/calibration are finite. Read the
seven added complete training records and all 124 new progress events; the complete
242-event stream has 225 ordered collection events, 14 completed updates, two
development panels and one facts-ready event, with consistent counters and timing.

At development ten, raw J is **-140.462028**, QoS **.272550455**, return cost
**.178651344**, throughput **8.176513664** and true episode-minimum fleet battery
**.376546503**; the legacy time-mean battery metric is .582383639. Relative to the
same eight initial development worlds, J changes **+290.949700**, QoS +.150611897,
cost -.022105766 and true minimum battery +.028784438. Seven worlds improve J, while
920006 worsens by -53.899417 to -946.613718 with QoS .012933333. World 920007 still
has zero service and J -1399.717170; 920003/920005 also remain negative. All eight
episodes truncate at 1,500 with zero optimizer updates and zero charging, cutoff,
depletion or charger input. Recomputed all aggregate means from the complete world
rows. This strengthens the narrow observation that the native detached control is
learning on these development worlds; it is neither final performance nor an
auxiliary-package effect.

On the unchanged initial facts, service/observation MSE falls from .141869610 /
.074281531 to **.012557119 / .007977503**, but both remain above their fixed mean
references **.009677077 / .006262023**; observation persistence is .000001321245.
The service head is worse than its mean reference on 932211 (.023563154 vs .017477845)
and better on the zero-service episode 932212 (.001551084 vs .001876310). Observation
errors are worse than the mean reference on both episodes. Episode-equal reductions,
zero-update metadata and exact fact/calibration bindings pass. Original-node array
digest `1ed847f8754dfbce23989710d879c4ffdc5139a8e39ade6da1064541cecf08e2` matches the
reported development-ten readout; initial facts and zero-panel array digests also
remain unchanged. Full binary readback/rescoring remains part of completion. Reported
fixed-row feature variance/effective rank are **10.531186 / 6.076676**, with nonzero
per-agent and quarter-episode variation and no degeneration flag. Lower errors than
untrained heads do not establish useful auxiliary gradients or rescue a package claim.

All native learners move in each new update. Both detached heads take 30 steps per
pass; auxiliary representation steps, base/GRU gradients and parameter movement stay
exactly zero, and valid-row counts remain 5,964 team / 47,712 agent. Collections
8/9/10 each have three zero-service lanes; 11/12/14 each have two, and 13 has one.
Every completed episode truncates at 1,500 with zero charging/cutoff/depletion/input.
The two earlier all-zero-service collections remain adverse evidence. Head losses,
gradient/clipping diagnostics, target/prediction moments and feature variation are
finite; they do not alter the prescribed treatment. The last completed resource row
reports cumulative wall **3,099.253619 s**, peak RSS **3,054,988 KiB**; collection 15
ends at wall 3,215.024734 s. These are partial costs, not final fit timing.

First-block package judgments remain unchanged pending the fixed second-block
comparisons. The next prescribed observation is the development-twenty curve and
ultimately final D followed by S/G and common endpoint replay; no early checkpoint is
selected as the endpoint. Four planned fits are launched, three accepted and D2
running; S2/G2 remain unstarted. Consumed the exact generation-28 wake/event and
rearmed the same accepted process at **generation 29**. Continue the existing fixed
horizon without a restart, new fit, changed recipe or Pro Send.

## 2026-09-22 — B03 second-block D development-twenty checkpoint

The September 23 02:00 UTC observer reports the original D / 912347 / a01 runner and
supervisor identities running, no exit witness, consistent records and zero observation
errors. Refreshed main `aecf372347b6779d75d63f1c0e36bc279d3e6e14` leaves the constitution,
compute binding, owned notebook, lifted pause and direction/lead/plan unchanged.
Copied summary SHA256 is
`4116c17c1fc59940407a4fd26e7436b137d4a1f390eb5ae7de624303bc3e9afb`.
It has **132,000 training transitions, 21 completed updates and 88 completed episodes**;
collection 22 is complete, but its update is not recorded in this snapshot. Three
development panels total 24 episodes / 36,000 evaluation transitions. Initial facts
remain two episodes / 3,000 physical transitions; three readouts total 71,568 agent
rows. Status is INCOMPLETE, failure null and stderr empty. All previously read completed
records and frozen bindings are unchanged. All 45,557 summary/calibration floating
values are finite. Read all seven new complete training records and the 113 added
progress events; the 355-event stream has 330 ordered collection events, 21 completed
updates, three development panels and one facts-ready event. Counter and timing checks
pass. This is still a partial fit, not completion acceptance.

Development-twenty J is **315.088688**, QoS **.320492508**, return cost **.050470046**,
throughput **9.614775248**, and true episode-minimum fleet battery **.379834331**;
legacy time-mean battery is .584219799. Relative to development ten, changes are
J **+455.550716**, QoS +.047942053, cost -.128181298 and true minimum battery +.003287827.
Six worlds improve J and two worsen: 920001 changes **-991.304303** to **-270.442162**,
and 920002 changes **-240.151424** to 328.136951. World 920006 remains negative
(-156.261562), though it improves; all eight worlds now have nonzero service.
The largest favorable change is 920007, +1840.439862 to 440.722692. Every episode
truncates at 1,500 with zero optimizer updates and no charging, cutoff, depletion or
charger input. All reported aggregate means and per-step conversions were independently
recomputed. The development learning curve now improves at both scheduled intervals,
but heterogeneous world outcomes remain adverse evidence; no early endpoint is selected.

On the same initial-policy facts, service MSE is **.008551292**, below development
ten's .012557119 and the fixed training-mean reference .009677077. This mean hides
opposite episode results: 932211 has error .005158248 versus reference .017477845,
while zero-service episode 932212 has error **.011944336** versus reference .001876310
and has worsened from development ten's .001551084. Observation MSE increases from
.007977503 to **.010040269**, above both the constant mean .006262023 and persistence
.000001321245; each episode remains worse than its mean reference. Episode-equal
reductions, zero-update metadata and exact fact/calibration bindings pass. The original
node's saved development-twenty array digest
`8fd687fddc2330213f32ca585273c49b3180a11f459ae5924c8bd6c578e6cb91` matches the report;
facts and both earlier array digests remain unchanged. Full binary readback/rescoring
remains a completion check. Reported fixed-row feature variance/effective rank are
46.058879 / 4.592022, with positive per-agent and quarter-episode variation and no
degeneration flag. Native development improvement alongside worse observation readout
retains the proxy/control separation; neither head error identifies an auxiliary effect.

All native parameter groups move in updates 15–21. Both heads receive 30 steps per
pass, while D's auxiliary representation steps, base/GRU gradients and displacement
remain exactly zero. Valid rows stay 5,964 team / 47,712 agent; native diagnostics,
head gradients, target/prediction moments and feature variance are finite. Training
collections 15/16/18/19 each have one zero-service lane, 17/20 each have two, and 21
has none. All completed episodes truncate with zero charging/cutoff/depletion/input.
Earlier all-zero-service collections and negative worlds remain in the cumulative
record. The last complete resource row is wall **4,823.398056 s**, peak RSS
**3,089,316 KiB**; collection 22 ends at wall 4,956.633947 s. These are partial costs.

The technical detached-control judgment remains supported, and this block's native
development learning is clearer. First-block package judgments and the S/G recurrence
question remain untouched until their fixed trained comparisons exist. Continue D to
the prescribed final evaluation, then use its fully accepted block-two inputs for S/G
and common endpoint replay. Four planned fits are launched, three accepted and D2
running; S2/G2 remain unstarted. Consumed the exact generation-29 wake/event and
rearmed the original accepted process at **generation 30**, without restarting or
changing any fit, horizon, recipe or Pro operation.

## 2026-09-22 — B03 second-block D collection-horizon checkpoint

The September 23 02:27 UTC observer retains the original D / 912347 / a01 process
identities running, with consistent records, no exit witness and zero observation
errors. Refreshed main remains `aecf372347b6779d75d63f1c0e36bc279d3e6e14`, with the
lifted pause and owned direction/lead/plan unchanged. Copied summary SHA256 is
`2b4dc38e8bfa61a6fe78ebb7901af4f4c48c14a6bea492eb4516214b92df19c0`.
The snapshot contains all **180,000 training transitions / 120 completed episodes**,
but only **29/30 completed updates**; collection 30 is finished and its update is not
yet recorded. Status remains INCOMPLETE, failure null and stderr empty. There are no
new evaluation/readout panels: zero/ten/twenty still total 24 episodes / 36,000
evaluation transitions, with two initial fact episodes / 3,000 physical transitions
and 71,568 replayed agent rows. Final evaluation, endpoint facts and saved final
checkpoints are still pending; collected transitions alone do not complete a fit.

All previously read completed records, three panels and frozen input bindings remain
unchanged. The original-node initial facts and three prediction-array digests still
match the summary. All 62,301 summary/calibration floating values are finite. Read the
eight new complete training records and 128 added progress events; the full 483-event
stream contains 450 ordered collection events, 29 completed updates, three development
panels and one facts-ready event. Counts and monotonic timing agree. Every native
learner moves in updates 22–29; both heads take 30 steps per pass with positive movement.
D auxiliary representation steps, base/GRU gradients and displacement remain zero,
and supervised rows remain 5,964 team / 47,712 agent. Native loss/entropy diagnostics,
head losses/gradient clipping, target/prediction moments and feature variance are finite.
All newly completed training episodes truncate at 1,500 with no charging, cutoff,
depletion or charger input.

Later training remains adverse and variable despite the favorable development-twenty
mean. Collections 22–24 have service in all four lanes, but 25–28 each contain one
zero-service lane, and 29 contains two. The second lane has zero service throughout
25–29, including J **-1955.770503**, **-1967.363737** and **-2099.788898** at 25, 27 and
28. Collection 29 has negative J in all four lanes:
**-1255.078660 / -771.954156 / -266.166816 / -725.877331**. Its two positive-service
lanes have QoS .110009359 / .139933115 and return cost .138900185 / .307194082.
These observations preserve the limitation that service alone need not yield useful
whole return. They are training episodes, not a new final-world panel or evidence for
choosing an earlier checkpoint. No second-block S/G comparison exists yet; the prior
package judgments and recurrence question remain unchanged.

Last completed-update resource wall is **6,310.124606 s**, peak RSS **3,089,316 KiB**;
the final collection event is at wall **6,424.044425 s**. These are partial fit costs.
Continue the accepted final update, scheduled development/final evaluations, endpoint
facts and checkpoint writing, then perform full completion verification before S2.
Four planned fits are launched, three accepted and D2 running; S2/G2 remain unstarted.
Consumed the exact generation-30 checkpoint wake/event and rearmed the same process
at **generation 31**. No restart, additional fit, retuning, shortened horizon or Pro
Send is selected from this checkpoint.

## 2026-09-22 — B03 second-block D complete acceptance and fixed S continuation

D / 912347 / a01 completed at September 23 02:55 UTC. Direct native status confirms
exit zero with a valid witness for the original identities, both processes absent and
consistent admission/manifest/source records. Refreshed main remains
`aecf372347b6779d75d63f1c0e36bc279d3e6e14`, with this direction and lifted pause intact.
Accepted source remains `73be55261b9f5e8f8fe26fdec6558b87ad088fcb`. Collected all
**18 artifacts / 236,271,241 bytes** and matched original-node SHA256s locally.
The final summary is
`729f8f1991a3bdd79fcc46b09083645da46e800f633590ac566328fbd016b99f`, status COMPLETE,
failure null, stderr empty. Full production-spec verification passes for D / 912347,
CUDA / four threads and the exact frozen source. This acceptance follows reading the
complete evidence and checkpoint verification, not the process exit alone.

Exposure is exactly **180,000 train / 30 updates / 120 training episodes**, plus
**96,000 evaluation transitions / 64 episodes** and **9,000 physical fact transitions /
six episodes**. The four initial-fact readouts total 95,424 valid agent rows. All
485 progress events and final counters agree; previously read complete records remain
unchanged. Every native group moves, with optimizer steps high 2,250, actor/critic
67,500 each, team discriminator 450 and individual discriminator 1,800. Both heads
have 900 steps; D has zero auxiliary representation steps, gradients and base/GRU
movement throughout all 30 passes. Native displacement from initialization is positive
for all groups. No straddling rollout boundary occurs in this fixed episode-length run.

All 65,395 summary/calibration floating values are finite. Verified raw initial and
endpoint fact arrays, seeds, shapes, terminal rows, policy/source metadata and QoS
aggregates. Independently rescored every saved initial-fact prediction array at
0/10/20/30 in float64, including W10 service labels, observation targets, both mean
references and persistence; maximum discrepancy is **6.969093e-9**. All four saved
feature samples reproduce their variance/effective rank. CPU readback restores the
exact final native policy and auxiliary states; all **726 tensors** are finite and
every native optimizer parameter state has the prescribed step count. Both head
optimizer states have 900 steps, representation optimizer is absent, and calibration
matches. The loader's expected missing discriminator-buffer notice does not resume
training; verification performs no new environment interaction or optimizer update.

Final **32-world raw J is +12.170880**, QoS **.233777638**, return cost **.108376770**,
throughput **7.013329151**, and true episode-minimum fleet battery **.385216308**;
legacy time-mean battery is .578743130. Eighteen worlds have positive J and fourteen
negative J. Zero-service worlds are **936011, 936013, 936018 and 936029**. The worst
J is **-1181.533226** at 936024; 936011 is -1151.501629 and 936015 -936.116143. The
best is +864.618263 at 936032. All 32 episodes truncate at 1,500 with zero optimizer
updates and no charging, cutoff, depletion or charger input. Recomputed the complete
world aggregates; these worlds describe this one trained policy, not 32 training
replications. No second-block S/G effect can yet be inferred from this D baseline.

Development J at 0/10/20/30 is **-431.411727 / -140.462028 / +315.088688 / -41.598834**.
The final interval loses **356.687523 J** despite QoS increasing .002339640: return
cost rises **.120143486** to .170613532. True minimum battery rises .013381815, showing
that these summaries alone do not identify a unique cost mechanism. All final
development worlds have nonzero service, but four have negative J. The endpoint is
kept at the prescribed 30 updates; the stronger development-twenty checkpoint is
not selected retrospectively. Late negative training episodes, including the final
pass's zero-service second lane, remain part of the adverse record.

On unchanged initial facts, final service/observation MSE is **.007275837 / .007002230**.
Service error is below its mean reference .009677077 on average, but not in both episodes:
932211 is .007182121 versus .017477845, while zero-service 932212 is **.007369553**
versus .001876310. Observation error exceeds its mean reference .006262023 and
persistence .000001321245; both episodes remain worse than their mean reference.
Service error improves from development twenty while native development J falls;
both heads' errors also improve over that last interval. Reported final feature
variance/effective rank is 46.801954 / 6.958434, nondegenerate. Thus this block adds
another concrete limit on using prediction error to select control performance; it
does not identify mediation or the effect of auxiliary representation gradients.

The four prescribed endpoint fact worlds 933211–933214 have mean J **273.823643**,
QoS .193849117, cost .001346911 and true minimum battery .400286356. All four truncate,
with zero updates/events. Their different performance from the 32-world panel is
retained as panel dependence, not extra test replication. Exact accepted bindings are:

- Initial facts: `163d34ce6dc14e2cf6273c503ec8e086589b39908c19632af30c1b3bb3a727ae`.
- Calibration: `0c49d91203e9e6d18a38d5650207873a7eeb91b536f582a35fea9ee312591ebb`.
- Endpoint facts: `6b34d62e05d084d9ddab5fd3ba165323d18e8ce92d996e39e81360fe52be11d2`.
- Final native checkpoint: `ed65f3d70c440c681eba46a46dd2626f94aa451c142e5733c19fb402ba0a6827`.
- Final auxiliary checkpoint: `2cf95d69509479037f094e02010ecb26fe520c26f30c15f15c7525cff9ef366a`.
- Final policy fingerprint: `9b95af7625a969e9988a910586cbf0baa4889c79d90cd62a69f89b1a1b3b4122`.

Runner wall is **8,195.780130 s / 136.596335 min**, CPU user/system
7,851.973719 / 362.907227 s and peak RSS **3,089,316 KiB / 2.946201 GiB**. Stage walls
are collection 3,464.383987 s, native update 1,906.751907 s, auxiliary 15.749694 s,
evaluation 2,502.896957 s, facts 197.021879 s, replay 11.023819 s, preparation .977825 s
and checkpoint .137347 s. Four accepted B03 fits total **542.649048 runner min**;
the first-block zero-update endpoint replay's .906094 min and the earlier zero-step
technical failure remain separately scoped. Shared-node wall timing is not intrinsic
algorithm speed.

The current shared B03 reading remains: first-block G has the larger descriptive
native gain, S has a service/cost tradeoff, and common-fact errors do not justify a
semantic or mediation claim. D2 strengthens the validity of the second baseline and
retains late cost deterioration as contrary evidence. It cannot strengthen or weaken
the within-block auxiliary comparison before S/G exist. Continue the **already fixed
fifth fit, S / 912347 / a01**, followed by the fixed G cell; no new fit is added and
the original recurrence prediction remains unchanged. A higher/lower D baseline is
not a reason to select or cancel the matching arms.

Prospective S uses the unchanged source, 180k train / 30 updates, four lanes, CUDA FP32
and four threads; all native learners continue, W10 service gradients enter actor
base/GRU and the observation head stays detached. Reuse the exact D2 initial facts
and calibration above from
`/home/wu/hmasd-worktrees/usa-b03-73be55261/runs/uav_service_auxiliary/b03_d_912347_a01/`.
First collection/native update/initialization must match the recorded D2 bindings.
S output is `runs/uav_service_auxiliary/b03_s_912347_a01`, supervisor
`usa-b03-s-912347-a01`; evaluation panels, endpoint facts, coefficients, seeds and
learning rates remain frozen. Commit/push this decision and D evidence before its
single native admission. No extension, retuning, third block, confirmation batch or
new Pro Send is authorized by this result. Consumed the exact generation-31 checkpoint
and rearmed observation at generation 32 to reconcile the completed original process.
The resulting READY event was read against the complete verified result and consumed
at generation 33; the D2 operation remains finished, with no worker restart.

## 2026-09-22 — S2 pre-admission invocation refusal and correction

The prospective D acceptance/S binding was published at `48f15461b` before submission.
At September 23 03:06:51 UTC, supervisor `usa-b03-s-912347-a01` ended with exit 4 and
the exact message `hmasd launch refused: runner entry is outside the source checkout`.
The DM incorrectly put the configured Python executable after the launcher's `--`,
where the native interface requires the tracked runner script as its first argument.
The configured interpreter belongs before `scripts/hmasd_launch.py`; admission selects
it for the child. The rejection occurs in request probing before claim creation.
Direct reconciliation confirms the intended S output does not exist and the claim
store contains no operation for that output. No S worker, environment, update, fit or
scientific artifact was created. The failed supervisor log remains at
`/home/wu/.agent-tasks/usa-b03-s-912347-a01/task.log`; it is not restarted.

After reading the actual interface and the accepted first-block S manifest, explicitly
correct the invocation to `-- scripts/run_uav_service_auxiliary_b03.py` followed by the
same frozen S arguments. Keep the still-unused output `b03_s_912347_a01` and all
source/seed/facts/calibration/exposure bindings unchanged. Use a distinct submission
supervisor `usa-b03-s-912347-a01-admit02`, preserving the rejected submission. Commit
and push this correction before submitting that one valid request. This fixes the
pre-admission command, not a scientific retry or a change to the six-fit design.

## 2026-09-22 — B03 second-block S admitted

The corrected invocation was published at `8be5fbb28` and submitted once through
`usa-b03-s-912347-a01-admit02`. Native admission accepted **S / 912347 / a01** at
September 23 **03:10:12 UTC**, on source `73be55261b9f5e8f8fe26fdec6558b87ad088fcb`.
The original submission supervisor returned after admission; the independent native
supervisor/runner are **301706 / 301707**, session 301706, start ticks
49514020 / 49514023, on the same recorded boot. Admission observed published control
`de99a36ac9846bc5b2bf3bc1f82fe0f033aa84db`. Actual-node available/effective memory was
**14,767,763,456 bytes**, above the configured 4 GiB floor, with no failure reason.
Native claim is
`/home/wu/projects/HMASD/.git/hmasd-admission/b73b0ca2f8b86b1628bfdf9794dbf60255a1e054dc79ceb58b867310db6481ae.json`;
the runner-written manifest is in `runs/uav_service_auxiliary/b03_s_912347_a01/`.

Copied initial summary SHA256 is
`e8b0350526d99070e46eadc663291298933b66d4202d77c2a14e73cd316ceede` and config SHA256
`c42fd346acaf1ba4b0adb9bec3bb9ab677674ebae1eedd22fc142ba041ba3be1`. The snapshot is
INCOMPLETE with zero training/evaluation updates or transitions, failure null and
stderr empty. Its production spec matches D2 exactly; initialization fingerprint and
reused facts digest match D2, with exactly two reused episodes / 3,000 reused
transitions and zero new fact interaction. The command binds D2's exact calibration.
The first collection/native-update provenance check remains to be observed after it
occurs; these startup facts are not scientific acceptance of S.

Registered observation and read its first adopted facts at **generation 34**: the
original native identities are running, records consistent, exit witness absent,
observation errors zero and no pending event. Five of the six planned fits have now
started: four complete/accepted, S2 running and G2 unstarted. Continue the fixed S
horizon and complete verification before G2; the initial refused supervisor remains
a separate zero-fit pre-admission event, with no worker restarted or recipe changed.

## 2026-09-22 — B03 second-block S first checkpoint and matching verification

Read generation-34 CHECKPOINT `f8e17485f2be5ce2fdeefdb6` from wake
`ae703955-f3ec-4df9-835a-dd0d420c96ef`. Published main remains `e8c7b0de8` with
the same active DM and no applicable owner pause. Native observation at September 23
03:35:15 UTC identifies the original supervisor/runner **301706 / 301707** with
matching boot/start ticks, consistent records, no exit witness and zero observer errors.
Copied runner bytes were checked against their remote SHA256 digests; the existing
progress prefix and config are unchanged. The read summary SHA256 is
`e4e47d443fe7fb0b231f0788796c1d99cad0b5e221782166001a879041cb7368`.

The snapshot is INCOMPLETE, failure null and stderr empty, with **48,000 training
transitions / 8 native updates / 32 episodes**. It contains only development panel 0
(8 worlds / 12,000 evaluation transitions), 23,856 initial-fact replay agent rows,
two reused initial-fact episodes / 3,000 reused transitions and zero new fact
interaction. Initialization, first collection, first native-update fingerprint and
first native optimizer-step counts exactly match D2. The newly written calibration
bytes hash to D2's `0c49d91203e9e6d18a38d5650207873a7eeb91b536f582a35fea9ee312591ebb`;
the full panel-0 evaluation/readout object also matches D2 exactly. This verifies the
previously pending matching checks before auxiliary divergence.

All **17,752 floating values** in the summary and calibration are finite. All five
native parameter groups move on each of the eight updates. Each auxiliary pass uses
5,964 valid team rows / 47,712 agent samples and 30 steps for each head and the active
representation optimizer: **240 steps each** so far. Both base and GRU auxiliary
gradient maxima and parameter movements are positive on every pass. Service training
losses span .000530119–.011422066 and finish this snapshot at .007529681; detached
observation-head losses span .017087991–.034260658 and finish at .023481358. These are
changing training distributions, not a common-fact improvement claim. Feature total
variance spans 6.775868–12.209136. Wall at completed rollout 8 is **1,595.701921 s /
26.595032 min**, peak RSS **3,049,384 KiB / 2.908119 GiB**. Stage timing and all
per-lane readings remain in the runner summary.

Retain the adverse early training: **24/32 episodes have zero QoS and 29/32 have
negative J**; rollouts 2 and 3 have zero service on all lanes, and the second lane
has zero service throughout all eight rollouts. Worst training J is −2,329.142893
at rollout 4's fourth lane. All episodes truncate at 1,500 and have zero charging,
cutoff, depletion or charger input. The only native development panel is still the
matched initial panel (J −431.411727); no trained development or final comparison
has yet been read. The new evidence strengthens matching and active-gradient
correctness, while preserving low-service training as contrary evidence. It does
not resolve second-block S−D or S−G utility. Continue the frozen 30-update horizon,
then complete acceptance and the already planned G cell; no early selection or
additional fit. Consumed the exact event and rearmed the same native operation at
**generation 35**, 1,500-second window, without restarting a worker or sending Pro.

## 2026-09-22 — B03 second-block S development-10 checkpoint

Read generation-35 CHECKPOINT `939bead1e29bdb84dacc2a49`, wake
`ecb41684-a78b-4fda-bda6-75c8505e451f`. Refreshed main is `46d3560c5`; its changes
since the last publication do not alter the constitution, RESEARCH or this notebook,
so pause, lead and fixed scope remain unchanged. Native observation at September 23
04:02:04 UTC still matches supervisor/runner **301706 / 301707**, with consistent
records, no exit witness and zero errors. Copied summary SHA256 is
`bed086aa5c42edabdb8d9892e6fd7ffdf8a269762ee67139e419e4f7f0a115ee`.
Remote/local byte hashes agree; all earlier updates, training rows, evaluations and
RSS entries remain exact prefixes, and config/calibration/provenance are unchanged.

The snapshot is INCOMPLETE with failure null and empty stderr: **16/30 native
updates, 64 completed training episodes**, plus collection of rollout 17 through
step 1,400 (**101,600 total training transitions**, of which 96,000 belong to the
completed updates). Evaluations total 16 episodes / 24,000 transitions at panels
0 and 10, initial-fact readout rows 47,712, and new fact interaction remains zero.
All **34,765 summary/calibration floats** are finite. All five native parameter
groups and both active auxiliary representation components move on every new
update; heads and representation have **480 optimizer steps each** through 16
passes, with unchanged 5,964 team / 47,712 agent samples per pass. Progress counts
and wall ordering check consistently. Completed-rollout wall is 3,114.967005 s;
latest collection wall **3,202.386811 s / 53.373114 min**, peak RSS
**3,092,032 KiB / 2.948792 GiB**. These are ongoing, not final, costs.

Development panel 10 has mean **J +117.651753**, QoS **.270265866**, cost
**.091502155**, throughput 8.107975968 and true episode-minimum battery **.366952601**.
Recomputed world averages match the runner aggregate. Against D2 at the same panel,
S−D is **J +258.113781**, QoS **−.002284590**, cost **−.087149189** and true minimum
battery **−.009593902**: the higher J accompanies lower cost and slightly lower
service/battery. Four paired worlds improve J and four worsen it. All eight worlds
have service, seven have positive J, and adverse world **920007 remains −1,415.596917**
with cost .605834415. All truncate at 1,500 with zero updates, charging, cutoff,
depletion and charger input. This is a development panel, not the fixed final panel.

Initial-common-fact service/observation MSE at 10 is **.009623920 / .008401050**;
relative to D2 it is −.002933199 / +.000423547. The service mixture is only slightly
below the training-mean reference .009677077: nonzero-service episode 932211 has
error .018254840 versus reference .017477845, while zero-service episode 932212
has .000992999 versus .001876310. Observation error remains above its .006262023
training-mean reference. Feature total variance / effective rank is **9.108592 /
5.645159**, nondegenerate. Per-episode/agent/quarter variation and the prediction
array digest are retained; complete raw-array rescoring remains part of terminal
acceptance. These readouts do not establish mediation or service-target necessity.

The new eight training rollouts contain **20/32 zero-service and 27/32 negative-J
episodes**, bringing cumulative counts to **44/64 and 56/64**. Rollout 9 has zero
service on all lanes; the second lane first gains service at rollout 13, then loses
it again at 14–16. All training event counts remain zero. Preserve these readings
alongside the favorable development mean. The result supports an intermediate
cost-related S−D gain and active learning, while final utility and recurrence remain
unresolved. Continue the fixed horizon and then G2 and common endpoint replay;
no endpoint selection, extra fit or new Pro question. Consumed the exact event and
rearmed the original operation at **generation 36**, 1,500-second window.

## 2026-09-22 — B03 second-block S development-20 reversal retained

Read generation-36 CHECKPOINT `eb28f47572a1031bf1235b26`, wake
`afd775a4-c709-424e-9ea3-d21704ad4e5a`. Refreshed main `1ccec7d64` contains another
direction's result/background revision; this direction's entry, notebook, lead and
pause remain unchanged. Native observation at September 23 04:28:52 UTC still
matches original supervisor/runner **301706 / 301707**, with consistent records,
no exit witness and zero errors. Copied summary SHA256 is
`b147ad44d29bc82613866bfd4592b7f29145ed096110f2a67676b8e779465ace`.
Remote/local bytes match, prior completed rows and panels are exact prefixes, and
config, calibration and first-rollout bindings remain unchanged.

The snapshot remains INCOMPLETE, failure null, stderr empty: **25/30 native
updates / 150,000 transitions in completed update rows**, plus all 6,000 transitions
collected for rollout 26. Thus collector counts are **156,000 transitions / 104
episodes**, while 100 episodes have completed update/readout rows. Panels 0/10/20
account for 24 evaluation episodes / 36,000 transitions, with 71,568 initial-fact
readout agent rows and zero new fact interaction. All **53,871 summary/calibration
floats** are finite. Each new update moves all five native groups, both heads and
the active base/GRU; each pass retains 5,964 team / 47,712 agent samples and 30 steps
per auxiliary optimizer, **750 steps each** through update 25. Progress count/order
checks pass. Completed-update wall is 4,695.405332 s; latest collection wall
**4,788.609767 s / 79.810163 min**, peak RSS **3,092,032 KiB / 2.948792 GiB**.

Development panel 20 has mean **J +93.329853**, QoS **.359506441**, cost
**.143891593**, throughput 10.785193220 and true episode-minimum battery **.398685664**.
All world averages independently recompute. Relative to D2 at 20, **S−D J is
−221.758835, with all eight paired world differences negative** (range −484.385192
to −3.076897). QoS is **+.039013932**, cost **+.093421547** and true minimum battery
**+.018851334**. The earlier development-10 mean advantage +258.113781 therefore
does not persist to 20. Within S, 10→20 J falls 24.321900 while QoS rises .089240575
and cost rises .052389438. Six worlds have positive J, all have service, but worlds
920001 and 920006 remain **−530.031340 / −604.620496**. All eight truncate at 1,500
with zero optimizer updates, charging, cutoff, depletion and charger input.

Initial-common-fact service/observation MSE is **.017281207 / .013726571** at 20:
both increase from 10 (+.007657288 / +.005325520) and exceed D2 at 20
(+.008729916 / +.003686301). The service-head reading is heterogeneous: episode
932211 error .004699575 is below its training-mean reference .017477845, but
zero-service episode 932212 error **.029862839** is far above its .001876310
reference. Both observation episodes exceed their training-mean references. Feature
total variance / effective rank **26.021919 / 4.859084** remains nondegenerate;
per-agent and quarter variation is preserved with the raw prediction-array digest.
Terminal acceptance still requires raw-array rescoring. Jointly worsening these
readouts and J at this interval does not establish a causal mediation mechanism.

New rollouts 17–25 have **17/36 zero-service and 22/36 negative-J episodes**;
cumulative completed-update readings are **61/100 and 78/100**. Worst training J
is **−2,413.736784**, rollout 23's third lane. Intermittent service gains coexist
with high costs; all training event counts remain zero. These adverse rows are
retained. Development-20 weakens the interim favorable net-use reading and again
separates higher service from higher complete native return. It does not determine
the predeclared final panel or justify early selection. Continue the same fixed
30-update endpoint, then complete S acceptance and the fixed G/replay operations.
No added fit, retuning or Pro Send. Consumed the exact event and rearmed the same
operation at **generation 37**, 1,500-second window.

## 2026-09-22 — B03 second-block S training horizon reached, final panel pending

Read generation-37 CHECKPOINT `786a030f14e41e804ce67cb6`, wake
`f90a4b68-7256-4996-9ee2-317a2ab6a01d`. Refreshed main `54306eeb3` changes another
direction's standing/plan; this direction, its lead, scope and applicable pause are
unchanged. Native observation at September 23 04:55:34 UTC still identifies the
original supervisor/runner **301706 / 301707**, with matching process identities,
consistent records, no exit witness and zero errors. Copied summary SHA256 is
`b1ff936d9b91ba8da16c421221a8f1fb44ff439c65f54e17898b42d0d09d1b21`.
Byte hashes match the node, all prior completed evidence remains unchanged, and
config/calibration/first-update provenance still matches its accepted bindings.

The **30-update / 180,000-transition / 120-episode training horizon is reached**.
The run remains INCOMPLETE, failure null, stderr empty: only four development
panels (32 episodes / 48,000 transitions) are in this snapshot, with 95,424
initial-fact readout agent rows and zero new fact interaction. The distinct final
32-world panel, endpoint facts and saved final checkpoints have not yet been
reported. All **64,605 summary/calibration floats** are finite. The final five
updates move every native parameter group and both auxiliary representation
components; runner records sum to **900 steps for each head and representation**.
Checkpoint optimizer-state readback remains part of complete acceptance. The last
completed rollout event, after development-30, is at **5,696.117708 s / 94.935295
min**. The RSS sample for rollout 30 was taken earlier, at 5,410.082121 s, and peak
RSS remains **3,092,032 KiB / 2.948792 GiB**. These do not include the unfinished
final evaluation/facts stages and are not full-fit cost.

Development panel 30 has mean **J +423.756952**, QoS **.381303084**, cost
**.044612212**, throughput 11.439092535 and true episode-minimum battery **.399113047**.
World averages independently recompute. **S−D J is +465.355787**, with seven paired
wins and one loss (world 920001, −3.323136); QoS is +.058470936, cost −.126001319
and true minimum battery +.005896901. World 920006 still has absolute **J −276.830662**;
all eight have nonzero service and truncate at 1,500 with zero optimizer updates,
charging, cutoff, depletion and charger input. The S−D development means at 10/20/30
are **+258.113781 / −221.758835 / +465.355787**. Preserve this changing sign and
the all-world losses at 20 alongside the late gain. Within S, 20→30 J rises
330.427099, QoS rises .021796644 and cost falls .099279381. The final 32-world
panel is still required to read the predeclared native endpoint.

Initial-common-fact service MSE instead rises to **.079407301**, +.062126093 from
20 and **10.913837 times D2** at 30. The two episode errors .068084437 / .090730165
both exceed their training-mean references .017477845 / .001876310. Observation
MSE is **.009724954**, down .004001617 from 20 but 1.388837 times D2 and above the
.006262023 mean reference. Feature total variance / effective rank is **52.672727 /
4.477290**, nondegenerate; all per-agent/quarter variation and array bindings are
retained. Raw-array rescoring remains pending complete collection. The larger
development return alongside worse service prediction is contrary to using this
initial-fact MSE as a net-use or mediation surrogate.

Final training rollouts 26–30 contain **13/20 zero-service and 17/20 negative-J
episodes**; whole-training counts are **74/120 and 95/120**. Rollout 29 has zero
service and negative J on all four lanes. Worst training J is **−2,477.709912** at
rollout 26's fourth lane. Rollout 30 recovers service on all lanes, yet its fourth
lane remains −984.011902. All training event counts are zero. These trajectories
are retained rather than replaced by the favorable development endpoint. The late
panel supports a bounded development gain, while the fixed final-panel comparison,
full S acceptance and second-block G comparison remain unresolved. Continue only
the original operation's final evaluation/facts/checkpoint work. Consumed the exact
event and rearmed the same handle at **generation 38**, 1,500-second window; no
worker restart, early acceptance, new fit or Pro Send.

## 2026-09-22 — B03 second-block S complete acceptance and fixed G continuation

Read generation-38 READY event `8f6d9a8fd9ff5ad19e46b06f`, wake
`c90612f7-a7a0-49b6-a0dd-e971166089f4`. The original S/912347/a01 runner exited
at September 23 **05:03:59 UTC**, exit 0, with a valid native witness and consistent
manifest/claim. Current published main `54306eeb3` retains this DM's active scope
and no applicable pause. Collected **18 files / 240,761,037 bytes** from the original
node and independently matched every local byte digest to the remote inventory.
The complete summary is
`a158a6d1a59c87456d1ac3e4b39c97372f039897f9420f36da99411b82a7499e`.
Original node outputs and local ignored NPZ/PT artifacts remain recoverable under
the same run path; JSON records and this reading are published on the direction
branch. The run is COMPLETE, failure null and stderr empty. All previously read
updates, curves, development panels and first-update bindings are unchanged.

Production `verify_run` passes for S, seed 912347, frozen source
`73be55261b9f5e8f8fe26fdec6558b87ad088fcb`, CUDA/four threads and the exact planned
specification. Counts are **180k training / 30 updates / 120 training episodes;
96k evaluation / 64 episodes; 6k new endpoint-fact transitions / four episodes**,
plus two exactly reused D2 initial-fact episodes / 3k transitions, and 95,424
readout agent rows. Initial policy, first collection, first native update, facts
and calibration all match D2. All 65,337 summary/calibration floats and **756
checkpoint tensors** are finite. Every native group moves on all 30 updates.
CPU checkpoint readback restores the exact final policy and all native optimizer
states: high 2,250; actor/critic 67,500 each; team/individual discriminator
450/1,800, across 91/15/14/24/29 states respectively. Both heads and the active
representation restore **900 steps**, across 4/4/10 states, with 30 passes and
exact calibration. The expected empty discriminator-buffer load notice has no
learning effect. Verification adds no environment transitions or updates.

Both raw factual archives pass schema, metadata, world/arm/policy, shape, finite
value and terminal-row checks. Independently recomputed float64 W10 service,
next-observation, persistence and mean-reference errors match all four saved
readout arrays and both episodes; maximum absolute difference is
**6.969092358755091e-9**. Sampled feature variance/rank is also independently
reproduced at all checkpoints. A first local scoring invocation addressed the
calibration wrapper as if `mu` were top-level; correcting it to the existing nested
`calibration` schema allowed the remaining checks to pass, without any runner,
artifact, fit or recipe change. This is now complete acceptance, beyond exit status.

The fixed 32-world final panel gives **S J −4.654721**, QoS **.218006503**, cost
**.106157679**, throughput **6.540195077**, true episode-minimum battery **.371236728**
and legacy time-average minimum-battery .572268619. Against D2:

| Final paired reading | S−D |
| --- | ---: |
| Native J | **−16.825601** |
| QoS per step | **−.015771136** |
| Return-constraint cost per step | **−.002219091** |
| Throughput Mbps per step | −.473134073 |
| True episode-minimum battery | **−.013979580** |

World J differences have **19 wins / 13 losses**, median +82.112249, range
**−2,286.526742 (936017) to +1,466.156753 (936011)**. Preserve the negative mean
alongside the positive median/win count; the large adverse tail is part of the
predeclared reading. S has 12/32 absolute negative-J worlds and zero service at
**936017, 936018 and 936029**. Worst absolute J is −1,815.514824 at 936017; other
large negatives include 936023 −1,130.430289 and 936024 −929.453651. All final
worlds truncate at 1,500 with zero optimizer updates, charging, cutoff, depletion
and charger input. The 32 worlds are not 32 training replications.

The favorable development-30 **S−D +465.355787** reverses on the fixed final
world panel to **−16.825601** at the same checkpoint. This is panel dependence,
separate from the temporal development signs +258.113781 / −221.758835 /
+465.355787 at 10/20/30. Preserve all of them. Final initial-fact service MSE
**.079407301** is 10.913837 times D2 and rises while development J improves late;
observation MSE **.009724954** is 1.388837 times D2. The full previous entry's
per-episode errors, low-service training and feature variation remain contrary
evidence; MSE does not rescue, mediate or substitute for the native endpoint.

Endpoint-fact worlds 933211–933214 give S mean **J −747.679640**, QoS .171197352,
cost .330353305 and true minimum battery .370174272. Their J values are
−345.236409 / −1,851.582688 / +683.747077 / −1,477.646543; the second and fourth
have zero service. All truncate at 1,500 with zero updates/events. This distinct
factual panel is retained for the fixed common-endpoint replay, not treated as
another training replication or a substitute native endpoint. Accepted bindings:

- Endpoint facts: `01f00a24f11d4712073f365775f6e572413f7cde398f8a63c54873bad01e89fa`.
- Native checkpoint: `17b810f6eac207b72a33c182ead1c608dc242404947921661af8132069a06a22`.
- Auxiliary checkpoint: `8c19bdb50e308751d441f58bf05653853dc650b382b200fa7f0307e3081157a4`.
- Final policy: `a84ac106d635eb097c3e3db4c6ca84ce9891e82537bba76910e8d6121b6280f8`.

Full runner wall is **6,823.945966 s / 113.732433 min**, CPU user/system
6,520.891811 / 319.537209 s, peak RSS **3,092,032 KiB / 2.948792 GiB**. Stage walls
are collection 2,897.743849 s, native update 1,518.977201 s, auxiliary 29.537788 s,
evaluation 2,104.180874 s, facts 115.900990 s, replay 10.215752 s, preparation
.971034 s and checkpoint .163581 s. Five accepted B03 fits total **656.381481
runner min**, with the first-block zero-update replay .906094 min separately;
technical pre-admission/pre-training failures retain their separate scopes.
Shared-node wall time does not establish intrinsic algorithm speed.

This second S−D endpoint **does not reproduce the first block's +24.585407**;
service and battery differences also change direction. It weakens a stable gain
claim for the current service-gradient package, without establishing equivalence,
population harm or a general impossibility for service supervision. Native utility,
the initial-fact predictor and the generic comparison remain distinct questions.
Keep the original prediction and complete the **already fixed sixth fit G / 912347 /
a01**, then the second-block common endpoint replay. Whether G's first-block native
gain recurs remains a discriminating observation; neither this negative mean nor
the favorable development score changes that prospective comparison. Existing
complete Pro advice covers these branches; no new Send, added fit, third block,
retuning, extended horizon or confirmation is implied.

Prospective G retains the same source, 180k train / 30 updates, native learners,
CUDA FP32/four threads, panels, seeds and learning rates. One-step next legal
observation gradients enter base/GRU; the service head remains a trained detached
shadow. Bind D2 initial facts
`163d34ce6dc14e2cf6273c503ec8e086589b39908c19632af30c1b3bb3a727ae` and calibration
`0c49d91203e9e6d18a38d5650207873a7eeb91b536f582a35fea9ee312591ebb` from
`/home/wu/hmasd-worktrees/usa-b03-73be55261/runs/uav_service_auxiliary/b03_d_912347_a01/`.
Require matching initialization/first collection/native update. Output is
`runs/uav_service_auxiliary/b03_g_912347_a01`, submission supervisor
`usa-b03-g-912347-a01`. The native invocation uses the tracked script first after
`--`, with the configured interpreter only before `scripts/hmasd_launch.py`.
Commit/push this accepted evidence and binding before one native submission.
Consumed the exact S READY event at **generation 39**; no active S producer remains.
The shared source is an authoring worktree with retained outputs and the planned
G consumer, not a disposable per-operation snapshot to reclaim.

## 2026-09-22 — B03 second-block G admitted

After publishing the S acceptance and prospective G binding in `ade57de66`,
submitted the original sixth fit once. Native admission accepted G/912347/a01 at
September 23 **05:13:30 UTC**; the [runner manifest](../../../../runs/uav_service_auxiliary/b03_g_912347_a01/launch-manifest.json)
retains the command, source, node, process identities and operation reference.
The actual-node preflight passed with **14,995,603,456 available/effective bytes**
against the 4 GiB floor, no failure reasons. Publication refresh to `e8fd213ba`
changes another direction's standing only; this scope and pause remain unchanged.

Collected and byte-verified the eight small startup files, including empty stdout
and stderr. The startup summary digest is
`9cd1325ad262eac8ccaa1f8013c569d9b324daa77241ad0b99c0e321fc15c1ac`;
config is `6eb46367b0877be2a67459bab3fcc21d4595eef5238701b11c8ddf69f362e738`.
The initial policy and reused facts exactly match D2; the config and command bind
its declared calibration. Configuration comparison differs from D2 only in arm
and the two declared reference digests. The captured summary is INCOMPLETE,
failure null, with zero completed training/updates/evaluation and two reused fact
episodes / 3,000 transitions; it is a startup snapshot, not a current progress
estimate. First collection, first native update and realized calibration matching
remain pending their recorded outputs.

Registered the accepted native status handle, then drained **generation 40** and
actually adopted its observation: runner and supervisor identities match, both
running, records consistent, zero observation errors, no pending events and no
stop request. This is **6/6 fixed fits started, five fully accepted and G2 running**.
Keep the accepted handle and frozen endpoint; next read G's checkpoints and full
result, then the already planned zero-update common endpoint replay. Admission
and observation do not accept the scientific result. This continuation added no
fit beyond the fixed six and made no worker restart, Pro Send or App message.

## 2026-09-22 — B03 second-block G first nine updates and matched first rollout

Read generation-40 checkpoint `1fc6ce4f6dfb12cca663a588`, wake
`c69e9457-c958-4c3d-8d0e-bfd111424710`. The original runner and supervisor remain
running with matching native identities, consistent records and zero observation
errors. Refreshed main `2a23a738e`: this direction's authorization, owner pause,
launch controls and relevant shared B03 understanding are unchanged. Collected
and byte-verified nine small files from the accepted operation; immutable config,
manifest and preflight match the startup snapshot. Summary digest is
`1c063a57785b3e4fb0262b36301c27341406fb6d56031f3451ee5480c5cfcd1e`.

The first-rollout checks now exactly match D2: initialization and facts retain
their declared digests; collection is
`ee1d01c195f9197226e4b41d360c0a38957c8b4a61af16ff7622b0dfc93e7eb7`, first native
update is `4ee61c8f3ecb466faca8609273f17b007bfd9258b4dac57e43774bbbbe711c8f`,
and the realized calibration file is byte-identical at
`0c49d91203e9e6d18a38d5650207873a7eeb91b536f582a35fea9ee312591ebb`. All first native
optimizer step counts match. The entire initial evaluation/readout record equals
D2, including every world, factual episode, feature statistic and array digest.
It is the same baseline observation, not new evidence for G's training benefit.

The snapshot is INCOMPLETE, failure null, stderr empty. It contains **nine completed
updates / 54k updated training transitions**, with the tenth collection already
finished: total **60k collected transitions / 40 episodes**; four episodes await
their reported training/update row. Evaluation remains only the initial eight
worlds / 12k transitions; reused initial facts are 3k, new facts zero, readout rows
23,856. All **19,845 summary/calibration floats** are finite. Every native parameter
group moves at all nine updates, and both auxiliary heads and the active base/GRU
move. Each pass uses 5,964 team / 47,712 agent rows; each head and the representation
report **270 optimizer steps** so far. Final saved-state readback remains pending.

Read all 36 reported training episodes: **28 have zero service and 32 negative J**.
Rollouts 2, 3 and 9 have zero service in all four lanes; the worst reported J is
**−2,257.271887** at rollout 4's fourth lane. All terminate by the fixed 1,500-step
truncation, with zero charging, cutoff, depletion and charger input. Preserve these
adverse trajectories alongside finite losses and learner movement. No trained
development panel is present yet, so this checkpoint establishes operation and
matching, without revising the unobserved final G comparison.

The latest completed-update sample is **1,484.785164 s / 24.746419 min**, peak RSS
**3,049,704 KiB / 2.908424 GiB**; the later collection-10 event is at
**1,576.881969 s / 26.281366 min**. These are partial scopes, not full-fit cost.
Consumed the exact checkpoint and rearmed the same accepted handle at
**generation 41**, 1,500-second window. Continue the frozen run and panels; no
restart, extra fit, new Pro Send or App message.

## 2026-09-22 — B03 second-block G nineteen updates and development-10 reading

Read generation-41 checkpoint `9193efb48124ad3412f0a3d8`, wake
`c59b3591-b9fe-424a-be9a-687aeff5c60e`. Original native identities remain running
and consistent, with zero observer errors. Main `3d4e4e1d4` preserves this scope,
pause, launch controls and relevant B03 understanding. Collected and byte-verified
nine small files. Earlier updates, training rows, RSS, evaluation-0 and all
first-rollout bindings are unchanged. The new summary digest is
`2eb73e429886b86a97574de5cdc0113403c703e7f70f7915a0241fa2373640b8`.

The run remains INCOMPLETE, failure null, stderr empty: **19 completed updates /
114k updated training transitions / 76 completed training episodes**; collection
20 is at step 1,300, bringing collected transitions to **119,200**. Two development
panels give 16 episodes / 24k evaluation transitions and 47,712 readout agent rows;
initial facts remain exactly reused, with zero new factual interaction. All
**41,044 summary/calibration floats** are finite. Every native group and both
auxiliary representation components move on updates 10–19; both heads and the
representation now report **570 optimizer steps each**, retaining the fixed
5,964 team / 47,712 agent samples per pass. Saved-state verification remains due
at complete collection.

Read all eight development-10 worlds and independently recomputed their means.
G has **J −67.602729**, QoS **.227257460**, cost **.131611822** and true minimum
battery **.382148866**. Four worlds have negative J; 920007 has zero service and
920006 is worst at −942.792941. All truncate at 1,500, with zero optimizer updates,
charging, cutoff, depletion and charger input. At this development checkpoint:

| Paired development reading | G−D | G−S |
| --- | ---: | ---: |
| Native J mean | **+72.859299** | **−185.254482** |
| QoS per step | −.045292996 | −.043008406 |
| Return-constraint cost per step | −.047039522 | +.040109668 |
| True episode-minimum battery | +.005602362 | +.015196264 |
| World J wins / losses | 3 / 5 | 4 / 4 |
| Median world J difference | −143.065153 | −10.893864 |

G−D's positive mean includes the +1,126.424636 difference at 920007 despite that
world's zero absolute G service. Retain five paired losses and lower mean service
beside the lower cost. Relative to S, both service and cost are unfavorable at
this checkpoint. These are development-panel readings, not final comparison or
independent training replications; they do not establish the prospectively sought
final G service increase.

Initial-common-fact service MSE is **.007244093**, observation MSE **.006763699**:
respectively .576891/.847847 times D and .752718/.805102 times S. Both service
episodes beat their training-mean references; the observation mean remains above
the .006262023 reference, with one episode on each side. Sampled feature variance /
effective rank is **6.439162 / 5.870591**, nondegenerate, with per-agent and quarter
variation retained. The saved array digest is
`8442e66bfa41cc58bfa864588d56be00855de7f1f4eb318355ec5e33901e7c00`;
independent raw-array rescoring remains pending complete collection. G has lower
prediction errors than S but lower development J, preserving the distinction
between this readout and control use.

New training rollouts 10–19 contain **24/40 zero-service and 32/40 negative-J
episodes**; cumulative counts are **52/76 and 64/76**. Worst new J is −1,974.254544
at rollout 10's first lane; all training episodes truncate and all event counts
remain zero. The latest completed-update resource sample is **3,177.502144 s /
52.958369 min**, peak RSS **3,092,120 KiB / 2.948875 GiB**; the later partial
collection event is at **3,258.822754 s / 54.313713 min**, not full-fit cost.
The mixed early panel and adverse training remain visible while the predeclared
final comparison is unresolved. Consumed the exact event and rearmed the same
handle at **generation 42**, 1,500-second window; no restart, added fit, Pro Send
or App message.

## 2026-09-22 — B03 second-block G twenty-eight updates and adverse development-20

Read generation-42 checkpoint `443b24fda2bb4fd8073b4adc`, wake
`9d19548a-cc98-4d64-9bee-36f2d15fa904`. The original native runner/supervisor remain
running with matching identities, consistent records and zero observation errors.
Main `5e18c6c05` retains this scope, pause, launch controls and relevant B03 shared
understanding. Nine small files were collected and byte-verified; immutable inputs,
all earlier update/training/RSS rows, development 0/10 and first-rollout checks are
unchanged. Current summary digest:
`90db2cbf544107e6cfa557e30d0a344d52cf18f65bef323ec80ad3d184b06267`.

Snapshot status is INCOMPLETE, failure null, stderr empty. There are **28 completed
updates / 168k updated training transitions / 112 reported training episodes**;
collection 29 is complete, making **174k collected transitions / 116 episodes**,
with its update/training row still pending. Development panels 0/10/20 total 24
episodes / 36k evaluation transitions and 71,568 readout agent rows; initial facts
remain reused, new factual interaction zero. All **60,150 summary/calibration
floats** are finite. All native parameter groups and both auxiliary representation
components move on updates 20–28; each head and the representation report **840
optimizer steps**, with the fixed complete-window sample counts. Saved checkpoint
readback and raw-array rescoring remain part of final acceptance.

Read all eight development-20 worlds and independently recomputed their means.
G has **J −225.908988**, QoS **.215550640**, cost **.178596503**, true episode-minimum
battery **.377867383**. Five worlds have negative J; 920007 again has zero service,
and 920006 is worst at −877.781177. All truncate at 1,500, with zero optimizer
updates, charging, cutoff, depletion and charger input. Paired readings:

| Development-20 reading | G−D | G−S |
| --- | ---: | ---: |
| Native J mean | **−540.997677** | **−319.238841** |
| QoS per step | −.104941868 | −.143955800 |
| Return-constraint cost per step | +.128126457 | +.034704910 |
| True episode-minimum battery | −.001966948 | −.020818281 |
| World J wins / losses | 1 / 7 | 3 / 5 |
| Median world J difference | −563.287582 | −382.917958 |

Only 920002 beats D in J; the largest G−D loss is −1,436.848916 at 920005. The
earlier development-10 G−D +72.859299 has changed sign. Within G, 10→20 J falls
**158.306260**, QoS falls .011706819 and cost rises .046984680. Service and cost
are both adverse against D and S at 20. This weakens any reading of the early
positive development mean as stable progress, while leaving the predeclared
final 32-world endpoint unobserved and unchanged.

Initial-fact service MSE is **.007639823** and observation MSE **.013191826**;
both rose from 10. Relative to D the ratios are .893412 / 1.313892; relative to S
they are .442089 / .961043. Thus lower service error, and both lower errors against
S, coexist with lower development J. The service mean is below its .009677077
reference but one episode is worse; both observation episodes exceed their mean
references. Feature total variance / effective rank is **36.179148 / 4.034095**,
nondegenerate; all per-agent/quarter variation is retained. Saved readout digest:
`1f506f6abd776fa28fd3a6321c1b50a5153bb9cbbad49f319359d95f1c104f38`.
These summary readings neither identify mediation nor replace final raw verification.

New training rollouts 20–28 have **12/36 zero-service and 24/36 negative-J episodes**;
cumulative counts are **64/112 and 88/112**. The new overall worst J is
**−2,436.929221** at rollout 26's fourth lane. All reported episodes truncate and
all event counts remain zero. Retain the lower zero-service fraction in this slice
alongside the persistent negative returns and large adverse tail. Latest completed
update wall is **4,760.693076 s / 79.344885 min**, peak RSS **3,092,120 KiB /
2.948875 GiB**; collection 29 later records **4,847.227897 s / 80.787132 min**.
These are partial scopes. Continue the same frozen operation through update 30,
the remaining panels and endpoint artifacts. Consumed the exact checkpoint and
rearmed at **generation 43**, 1,500-second window; no worker restart, extra fit,
new Pro Send or App message.

## 2026-09-23 — B03 second-block G training complete, final panel still pending

Read generation-43 checkpoint `61e11e3b8c0c6427d68ffab4`, wake
`e67f6e07-2fc0-4225-a151-166109a95ae2`. Both original native identities remain
running, records consistent, observation errors zero; no exit witness is present.
Main `e6bbd3162` leaves this authorization, pause, launch controls and relevant B03
background unchanged. Collected and byte-verified nine small files. All prior
updates, training/RSS rows, development 0/10/20 and fixed bindings remain unchanged.
The new summary digest is
`c8bc01d8295d77e7a7808712fde482e9e7be9959ad89abeb980763f1368d45bb`.

Training has reached **180k transitions / 30 updates / 120 episodes**, but the run
is still INCOMPLETE, failure null, stderr empty. Only the four development panels
are recorded: 32 episodes / 48k evaluation transitions, 95,424 readout agent rows,
zero new factual interaction. The final 32-world panel, four endpoint-fact
episodes and final checkpoint readback remain pending. All **64,605 summary and
calibration floats** are finite. Every native group and both auxiliary
representation components move on the last two updates; all three auxiliary
optimizers report **900 steps**. These logged counts do not substitute for saved
optimizer-state verification.

Development-30 gives **G J −566.691439**, QoS **.203386603**, cost **.286423774**,
throughput 6.101598099 and true minimum battery **.370541902**. All eight worlds
have nonzero service, but seven have negative J; worst is 920007 at −1,702.580350.
All truncate at 1,500, with zero optimizer updates and physical event counts.
World means independently recompute. Paired development readings are:

| Development-30 reading | G−D | G−S |
| --- | ---: | ---: |
| Native J mean | **−525.092605** | **−990.448392** |
| QoS per step | −.119445545 | −.177916481 |
| Return-constraint cost per step | +.115810243 | +.241811562 |
| True episode-minimum battery | −.022674243 | −.028571144 |
| World J wins / losses | 1 / 7 | 1 / 7 |
| Median world J difference | −489.498875 | −878.706288 |

The sole paired win against either arm is 920006, whose absolute G J remains
−60.744601. G−D development means at 10/20/30 are +72.859299 / −540.997677 /
−525.092605. Within G, 20→30 J falls **340.782451**, service falls .012164037 and
cost rises .107827272. Preserve this late decline and the unfavorable comparisons;
the fixed final world panel is still a distinct outstanding reading.

Initial-fact service MSE falls to **.005350291**, observation MSE to **.006838820**,
while development J deteriorates. Their ratios to D are .735351 / .976663 and to
S .067378 / .703224; lower errors coexist with lower development utility against
both. The service mean beats its reference while episode 932212 does not;
observation mean still exceeds .006262023, with episode 932211 worse and 932212
better than their references. Feature variance / effective rank is **34.703107 /
4.903232**, nondegenerate; per-agent/quarter variation is retained. Readout array
digest is `139a80b7cedb9a6d674b4b5caa73611d0ac2fb54dc8db9f562d278d3e5bd0634`.
Raw-array rescoring remains pending full collection; proxy improvement cannot
rescue this adverse development result or select a replacement checkpoint.

Rollout 29 has zero service and negative J on all four lanes. Rollout 30 has
three positive-J lanes, while its second lane has zero service and J −488.952212.
Whole-training counts are **69/120 zero-service and 93/120 negative-J episodes**,
with the previous −2,436.929221 tail retained. All episodes truncate and all
charging, cutoff, depletion and charger-input counts remain zero. The last RSS
sample is at **5,041.502147 s / 84.025036 min**, peak **3,092,120 KiB / 2.948875 GiB**;
the post-development-30 rollout-complete event is **5,312.082158 s / 88.534703 min**.
Neither includes the unfinished final stages. Continue only the original accepted
operation; consume the exact event and rearm the same handle at **generation 44**,
1,500-second window. No restart, extra fit, new Pro Send or App message.

## 2026-09-23 — B03 second-block G accepted and fixed common replay bound

Read generation-44 READY event `61a9bead68ddfb9fc2a50087`, wake
`1b88dc11-8716-4e5c-9db3-1c35d41d69f9`. The original G2 operation exited at
07:06:12.528 UTC with exit 0 and a valid native exit witness; both original
processes are absent, records consistent and observation errors zero. This is
execution evidence; acceptance below follows full reading and independent checks.
Current main `e6bbd3162` preserves owner authorization, the lifted pause, this
lead and the fixed B03 inputs. The only new main changes concern another direction.

Collected all **18 files / 242,896,468 bytes** and matched every remote/local
SHA-256. COMPLETE, no failure, empty stderr. All previously read curves,
development panels and initial/first-update bindings remain byte-for-byte equal
to the prior committed record. Production-contract verification passes source
`73be55261b9f5e8f8fe26fdec6558b87ad088fcb`, CUDA/four threads, full horizon and
all prescribed seeds/panels/counts. Final summary digest is
`0b3ac1f4542f70e87c533cc35b23a5746a71969611efad297175180284939771`.
The runner records **180k training / 30 updates / 120 episodes**, **96k evaluation /
64 episodes**, **6k new endpoint-fact transitions / four episodes**, 3k reused
initial facts and 95,424 initial-fact readout agent rows.

Read all 32 final-world and four endpoint-fact rows and independently recomputed
their means. Raw initial/endpoint facts pass schema, metadata, source policy,
seed, shape, finite-value and terminal-row checks. All four saved initial-fact
readouts were independently rescored from raw QoS/observations with float64 W10
convolution and the frozen calibration: **60 comparisons, maximum absolute error
6.969092358755091e-9**. Feature variance and effective rank independently agree
via centered feature SVD, with the exact saved deterministic sample indices.
Recursive finite checks cover **66,131 floats across summary, calibration and
checkpoint metadata**, plus **756 checkpoint tensors**.

CPU checkpoint readback restores the exact native policy and all optimizer states:
high 2,250 (91 states), actor/critic 67,500 (15/14 states), team 450 (24 states)
and individual 1,800 (29 states). Each state's step count was checked. The paired
auxiliary checkpoint round trip preserves all tensors/metadata, calibration,
arm/seeds/options and 30 passes; service/generic/representation optimizers each
have 900 steps (4/4/10 states). The expected empty discriminator-buffer restoration
warning changes no endpoint. Readback/rescoring performs no fit, update or
environment step, and its temporary scratch was cleaned.

Final-world G means are **J −12.775041**, QoS **.288711442**, return-constraint
cost **.144193623**, throughput **8.661343270**, true episode-minimum battery
**.364769562** and time-mean fleet-minimum battery **.572557755**. Throughput is
30 times QoS, not an independent service outcome. There are 13 negative-J worlds;
936006/936011 have zero service. The worst J is **−2,069.917857 at 936011**,
followed by −1,826.319457 at 936001 and −1,288.952785 at 936028. All 32 episodes
truncate at 1,500, with zero optimizer updates and charging/cutoff/depletion/input
events. Zero observed events does not establish safety.

| Final-world contrast, block 912347 | S−D | G−D | S−G |
| --- | ---: | ---: | ---: |
| Native J mean | **−16.825601** | **−24.945921** | **+8.120320** |
| QoS per step | −.015771136 | +.054933804 | −.070704940 |
| Return-constraint cost per step | −.002219091 | +.035816853 | −.038035944 |
| True episode-minimum battery | −.013979580 | −.020446746 | +.006467166 |
| World J wins / losses | 19 / 13 | 16 / 16 | 13 / 19 |
| Median world J difference | +82.112249 | +3.542617 | −195.819963 |

G−D ranges from **−1,526.941091 at 936028** to **+1,572.768888 at 936015**.
G−S has 19 wins and a positive median despite a negative mean: its tail at
936011 is **−2,384.572980**, while its largest gain is +1,909.853462 at 936017.
Retain these distributions alongside the small mean differences; they do not
establish equivalence, population harm or a stable global arm ranking. The full
rows remain in the runner summary rather than being replaced by aggregate signs.

G−D final J **−24.945921** contrasts with first-block **+117.896434**. Its service
increase recurs, but the first block's cost decrease changes to a cost increase,
and true minimum battery is worse in both blocks. S−D likewise changes from
**+24.585407 to −16.825601**; S−G changes from **−93.311027 to +8.120320**.
Neither package reproduces positive mean native use across the two training
blocks. G−D development-30 is −525.092605 and S−G +990.448392: final differences
have the same signs but very different magnitudes. S−D development/final signs
remain opposite. Development or earlier-checkpoint selection cannot rescue the
fixed primary endpoints.

G's final initial-fact service/observation MSE is **.005350291 / .006838820**,
lower than both other arms while final J is lower. The service/observation ratios
to D are .735351 / .976663 and to S .067378 / .703224. Both errors improved
20→30 while G development J deteriorated. Final feature variance/rank
**34.703107 / 4.903232** is nondegenerate, so this is not explained by complete
representation collapse. Per-episode reference failures and per-agent/quarter
variation from the preceding entry remain. These facts weaken use of this
readout error as a net-use surrogate, without identifying a causal mediator.

G endpoint-fact episode J on 933211–933214 is **+394.471161 / −927.086294 /
−485.439555 / −816.090327**, mean **−458.536254**, QoS **.321274863**, cost
**.308682312**, true minimum battery **.381855289**. All four have service and
three have negative J; all truncate at 1,500 with no updates/events. This
separate fact panel supplies the fixed replay, not replacement primary endpoints
or more independent training instances.

G2 wall is **6,759.441941 s / 112.657366 min**; CPU user/system
**6,471.842483 / 304.703137 s**, peak RSS **3,092,120 KiB / 2.948875 GiB**.
Measured stages (s): preparation .896366, collection 2,727.864268, native updates
1,384.104354, auxiliary 28.768075, evaluation 2,234.680189, fact collection
167.077522, factual replay 10.734324 and checkpoint .189979. All six completed
fits total **769.038846 runner minutes**, **1.08M train + 576k evaluation + 42k
physical facts = 1.698M interactions**. First-block zero-update common replay
adds .906094 min separately; earlier pre-training technical failure/refusal
remains separately recorded. Shared-node timing is not intrinsic speed.

Accepted artifact bindings: endpoint facts
`1d144985cd6091e3fdfe601b549a8b657c0b6e4706476dc2b916f47a7268df52`, native
checkpoint `d1209d366390935dd352afb777f46eae87b26c654ce7de9bb487b1bf177c5bb2`,
auxiliary checkpoint `452c8eb994f8d3230b6320bf95965622262fd09e7f8de9ee56527ecd500bad3b`,
final policy `4ac43face8939651e8e1765aa46c4665afbb6358872754f3e203512ce1f76fc3`.
All underlying files are retained at the same relative run path below local
authoring root `/home/fires/.codex/worktrees/d319/hmasd-wsl` and node source root
`/home/wu/hmasd-worktrees/usa-b03-73be55261`; large NPZ/PT remain outside Git.
[Runner summary](../../../../runs/uav_service_auxiliary/b03_g_912347_a01/summary.json),
[native manifest](../../../../runs/uav_service_auxiliary/b03_g_912347_a01/launch-manifest.json),
[exit witness](../../../../runs/uav_service_auxiliary/b03_g_912347_a01/process-exit.json).
Consumed the exact READY event and rearmed at **generation 45**; no producer is
running. There is no new fit or Pro Send.

**Fixed second-block common replay.** Complete the already prospective diagnostic
before the bounded batch decision. Use unchanged source `73be55261b9f5e8f8fe26fdec6558b87ad088fcb`,
`scripts/replay_uav_service_auxiliary_b03.py`, seed 912347, CUDA/four threads,
output `runs/uav_service_auxiliary/b03_endpoint_replay_912347_a01` and supervisor
`usa-b03-replay-912347-a01`. Preflight found no output or existing claim. Bind
the accepted inputs under that node source root:

| Arm | Run root under runs/uav_service_auxiliary | Full summary SHA-256 |
| --- | --- | --- |
| D | b03_d_912347_a01 | `729f8f1991a3bdd79fcc46b09083645da46e800f633590ac566328fbd016b99f` |
| S | b03_s_912347_a01 | `a158a6d1a59c87456d1ac3e4b39c97372f039897f9420f36da99411b82a7499e` |
| G | b03_g_912347_a01 | `0b3ac1f4542f70e87c533cc35b23a5746a71969611efad297175180284939771` |

All three local/remote summary hashes match. The production guard verifies full
run contracts and checkpoint/fact identities again. Three frozen checkpoint pairs
read the same 12 endpoint episodes (D/S/G × four), retaining source strata and
episode-weighted errors: **429,408 agent rows, zero new fits, optimizer updates
or environment transitions**. Initial-fact readouts stay separate. Read and
independently rescore all nine arrays and 36 episode readings; report replay cost
separately. Publish this binding before one native submission and observe its
actual handle. Existing complete Pro advice and the prospective decision branches
cover conflicting blocks and proxy-only improvement: absent a new reason, no
third block, retuning, longer horizon, new module or confirmation follows.

## 2026-09-23 — B03 second common replay accepted and current recipe closed

**Execution and acceptance.** The single prospective replay was admitted at
07:20:07.568 UTC against current main `e6bbd3162`, with fresh actual-node
available memory **13,613,752,320 bytes** above the 4-GiB floor. Native supervisor
335562/start 50974790 and runner 335563/start 50974793 share boot
`bb732fcb-1a33-4659-a786-331110ae41d3`; generation 46 observed both exact
identities running before their recorded exit. READY event
`5a574215d31b0139697a18d1`, wake `c58e1f32-6320-4ba5-8d76-917f2d6eaaf6`,
reports exit 0 at **07:20:57.097 UTC**, valid witness, absent processes, consistent
records and zero observation errors. The native operation reference is
`/home/wu/projects/HMASD/.git/hmasd-admission/7fbb38ab067a7dfd849e3c2a5d3547e10f9a72089fb9a5ece6649da21c8afa26.json`.

All **17 files / 667,535,492 bytes** were collected and remote/local SHA-256
verified. Summary digest
`759040d88d208bce346a6fc5a39b5007642ac092d1f4c83ea29fc9a728541edc` is COMPLETE,
failure null; stdout empty. Stderr contains exactly the three expected empty
discriminator-buffer restoration warnings. The exact three summary, checkpoint,
fact, policy, calibration and source bindings agree with the prospective entry;
all input checkpoint bytes remain unchanged. Three native policy fingerprints
and optimizer counts are preserved by the runner's before/after checks.

Read all **36 episode readings**, nine source strata and three aggregates,
including service and next-observation errors, references, feature rank/variance
and per-agent/quarter variation. All **1,881 summary floats** are finite.
Independently recomputed the nine saved arrays from raw endpoint QoS/observations,
using float64 W10 convolution and the frozen training-only calibration:
**240 score comparisons, maximum absolute error 1.1110843967099271e-8**.
Independent SVD matches all feature variance/rank readings, maximum absolute
difference **2.842170943040401e-14**. Each episode contributes 1,491 valid team
rows / 11,928 agent rows; every stratum has four episodes, with no missing windows.
The complete replay is **429,408 agent rows, zero new fits, optimizer updates or
environment transitions**. Array finiteness, exact raw/normalized observations,
QoS/dones/seeds, sample indices, episode equality and source-policy fingerprints
all pass. No replacement evaluator or checkpoint selection was used.

**Common endpoint mixture.** Lower error is preferable within this fixed table;
columns are the frozen model/readout pair, with each source arm contributing four
equally weighted episodes.

| Error / fact source | D endpoint | S endpoint | G endpoint |
| --- | ---: | ---: | ---: |
| Service MSE, D facts | .017224449 | .052353028 | .018394062 |
| Service MSE, S facts | .045119271 | .041393413 | .037777164 |
| Service MSE, G facts | .046676456 | .038835860 | .049224319 |
| **Service MSE, 12-episode mixture** | **.036340059** | **.044194100** | **.035131848** |
| Observation MSE, D facts | .012672498 | .014412639 | .013797628 |
| Observation MSE, S facts | .014526623 | .014969824 | .014013515 |
| Observation MSE, G facts | .035319984 | .034589217 | .030984909 |
| **Observation MSE, 12-episode mixture** | **.020839702** | **.021323893** | **.019598684** |

G has the lowest mixture means for both errors while having the lowest final
native J. Its service advantage against D is only **.001208210**, with lower
error on **4/12** episodes and higher error on eight; the source-stratum advantage
occurs only on S-generated facts. Its observation advantage against D is
.001241017, with five lower-error episodes and seven higher-error episodes.
G beats S on observation MSE in all 12 episodes, yet its final J is lower by
8.120320. S−D mixture errors increase by **.007854042 service / .000484192
observation**; service improves on five episodes and worsens on seven. The lower
S service error on its own and G-generated strata coexists with its much higher
error on D-generated facts. Do not hide this heterogeneity behind aggregate rank.

The shared service constant-reference MSE is **.073205737**; D/S/G beat it on
9/8/8 of 12 episodes, respectively, although all three means are lower. Shared
observation training-mean MSE is **.028018791** and persistence MSE **.000370816**.
Each arm beats the training-mean reference on 11/12 episodes; all 36 model/episode
readings are worse than persistence. These are factual forecasting references,
not alternative control policies. Feature total variance spans **27.382411 to
56.585244** and effective rank **9.887964 to 20.713971**, all nondegenerate;
the full per-agent and quarter readings remain available. This rules out an
exact constant-feature explanation on these saved samples, not weak or irrelevant
features elsewhere. A jointly trained feature/readout pair and its factual
distribution are measured together; there was no new probe fit to identify
intrinsic representation quality or causal mediation.

First-block G had the highest native J and the highest two mixture errors;
second-block G has the lowest native J and the lowest two mixture errors.
Together with the within-run development reversals and initial-fact readings,
this strengthens the warning that these measured prediction errors cannot be
used to select a useful controller. Different blocks have different facts and
training-derived calibration, so the raw error magnitudes are not a common
cross-block difficulty scale. Neither mixture represents the full task
distribution; its 12 episodes are not 12 independent trained policies.

Replay2 wall **47.220724 s / .787012 min**, CPU user/system **45.525196 /
16.654195 s**, peak RSS **1,373,932 KiB / 1.310284 GiB**. Both common replays
total **101.586364 s / 1.693106 min**, separate from **769.038846 runner minutes
for six fits**. The combined runner scopes sum to **770.731952 min**, excluding
implementation, verification, transfer/publication and the separately retained
pre-training technical failure. This is accumulated measured process wall, not
elapsed project time or an intrinsic per-arm speed estimate. Six fits retain
**1.08M train / 576k evaluation / 42k physical fact interactions**; common replay
adds no interactions. All arrays remain recoverable under this relative replay
path on both the local authoring root and `/home/wu/hmasd-worktrees/usa-b03-73be55261`.
[Full replay summary](../../../../runs/uav_service_auxiliary/b03_endpoint_replay_912347_a01/summary.json),
[manifest](../../../../runs/uav_service_auxiliary/b03_endpoint_replay_912347_a01/launch-manifest.json),
[exit](../../../../runs/uav_service_auxiliary/b03_endpoint_replay_912347_a01/process-exit.json).

**Whole-batch interpretation and decision.** All six fixed training cells and
both fixed common replays are now accepted. Primary final-world readings are:

| Training block | D J | S J | G J | S−D | G−D | S−G |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 912211 | −96.648955 | −72.063548 | +21.247479 | **+24.585407** | **+117.896434** | **−93.311027** |
| 912347 | +12.170880 | −4.654721 | −12.775041 | **−16.825601** | **−24.945921** | **+8.120320** |

The two training blocks are the replication units. The 32 common final worlds,
development worlds, overlapping windows and shared S−G contrast add no training
replications. No combined mean or formal population interval is used to obscure
the sign reversals. Low absolute returns, large negative world tails and the
recorded service/return-cost tradeoffs remain part of the reading; there is no
validated deployment threshold from which to declare acceptable absolute use.
The older four-fit B01/B02 development exposure and unequal tuning history of
the new G comparator remain disclosed in the prospective comparison.

- **Opportunity remains open.** S7's incomplete service and return constraints
  still permit useful control improvement in principle. Historical B01/B02 and
  B03 block1 positive observations remain valid bounded evidence. They do not
  demonstrate that another unmodified batch is worthwhile.
- **Representation and learning readings are narrower.** Auxiliary gradients
  reached the declared base/GRU and both readouts learned finite, varying outputs;
  complete feature collapse is not the explanation in saved facts. Lower factual
  error was neither necessary for the observed historical gain nor sufficient
  to secure the new final gain. A service-semantic mediator, a universal target
  ranking and a generic representation-information claim remain unidentified.
- **Net-use retention is weakened for both current packages.** S−D benefit does
  not recur, and G−D benefit also reverses. G's service increase recurs, but its
  first-block constraint-cost improvement does not; minimum battery is worse
  in both. S−G is itself sign-unstable. No arm is promoted to a stable winner,
  and no small mean difference is called equivalence or population harm.

The complete Pro answer and its adopted prospective branches already cover
conflicting blocks, proxy-only improvement and loss of final benefit. I therefore
**close the current B03 recipe and choose no further investment in an unchanged
S/G package**. No third block, coefficient/head/target sweep, longer horizon,
early-checkpoint rescue, additional panel or confirmation batch is selected.
The authorized comparison resolved why the earlier positive package reading
should not be promoted, but did not identify a new actionable repair worth an
additional batch. A future reopening would require a genuinely new recorded
reason and prospective discrimination; a new candidate is not owed. This closes
the recipe, not the broader scientific possibility or the owner's direction
assignment. Keep the direction/lead routing unchanged, with no selected next batch.

Consumed the exact replay READY event and rearmed at **generation 47**. All
accepted operations are terminal and read; no remaining observation, worker,
pending Pro answer, duplicate Send or App message is required. Publish the own
standing, directly affected shared understanding and the completed plan to main,
retiring the superseded in-flight index text in the same publication. Retain the
shared source worktree and all accepted artifacts; only the temporary publication
checkout is eligible for normal cleanup after publication and dependency checks.

## 2026-09-23 — B04 prospective direct service and return-risk learning

**Decision and reason.** The owner's adopted three-DM plan and scientific autonomy
in current main (`9f53da649`) continue this DM's responsibility for service benefit
and risk control. I read the current constitution, role, scientific/engineering
methods, relevant shared background, and the complete project Pro Answer and
Decision in `archive/2026-09-23/RESEARCH-scientific-management-adopted.md`.
The 9,550-character answer has SHA256
`3831d54162f944c23aacc2c437aca1ea558696661db008cc6b716dd84ebe82ff`.
Its direct risk-learning proposal applies here; its incorrect S7 numbers do not.
The six original summaries independently reproduce the two B03 sign reversals
already recorded above. B03 remains closed; its service gains and adverse costs
are retained. This is a new training-objective comparison, not another auxiliary
head, a same-objective critic repair, or a third B03 replication block.

The working explanation is that learning can improve service while failing to
price actions leading to return infeasibility sufficiently under finite PPO
training. A stronger true risk signal may reduce those trajectories enough to
improve the original reward. The strongest simple contrary explanation is that
the existing penalty already expresses the appropriate tradeoff: strengthening
it sacrifices more service than it saves in cost, or does not change useful
actions. Prediction error is untouched by this experiment and is no selection
criterion. Both lower risk with worse original J and no risk reduction are useful
adverse outcomes; neither justifies automatic coefficient search.

**Fixed comparison (exploratory, one matched training pair).** New ordinary native
HMASD `N` and risk-reweighted `R`, seed **914021** in both, four native training
lanes initialized with 914021–914024. S7-S2 / arm C, N=8, 30 users, k=10,
1500-step rollouts/episodes, 30 complete updates = **180,000 team transitions per
fit**, **1.44M agent rows per fit**. Native hidden sizes, PPO epochs, learning
rates, discriminators, entropy and normalizers remain those of `make_config`.
Both arms have ordinary complete high/low learning and no B01/B03 auxiliary
heads or extra representation pass. CUDA FP32, TF32 off, four torch CPU threads
on configured `wsl_4070`, subject to fresh actual-node admission. Run N then R
without using N's performance to alter R. A technical failure is reconciled and
repaired, not scored as negative science or blindly repeated.

The environment remains unchanged. Source trace establishes
`r_native = QoS - 2*c_return - 5*new_cutoffs - 10*new_depletions + graph_PBRS`,
where `c_return = min(max_i(max(0,-return_margin_i)) / .05, 1)` is the actual
post-transition return constraint cost. The energy environment broadcasts this
same reward to eight agents; the adapter averages identical entries, so there
is **no further division by N**. Select a single fixed doubling of the existing
coefficient, on its native units, before any new outcome: `r_train(N)=r_native`,
`r_train(R)=r_native-2*c_return`. Coefficient 4 is a deliberately material test
of underweighted risk, not an estimate of an optimum or a claim that doubling
is universally preferable. Cutoff, depletion, PBRS, cost cap and physics stay
unchanged. Actual native metrics and J are always recorded separately.

Only the scalar reward handed to `store_transition_batch` changes. Its native
low-level `lambda_e=1` component enters the stored reward, GAE and clipped PPO
actor loss. The same scalar accumulates in the existing high-level skill
interval return and high-level GAE. Thus this changes **both hierarchy levels'
return targets and actor advantages**, with native critics learning the new
targets; it does not isolate low-actor credit or criticize a single critic.
No cost number is merely added as a detached constant to the actor loss, no
future cost is supplied as an actor input, and the real costs are available only
after their transitions. Reward info and evaluation config keep their original
meaning. A controlled real storage/sampler/update regression must establish
that nonconstant cost changes advantages and actor updates, while zero extra
weight preserves native behavior.

**Readings and exposure fixed now.** Development worlds **937001–937008** at
updates **0,10,20,30**; fresh final worlds **938001–938032**, once at update 30.
No checkpoint selection, early success stop, final-world tuning or substitution
of old D. All panels use deterministic native policy execution, original
coefficient 2, preserved training RNG and no new optimizer updates. Each fit
has up to **96,000 evaluation transitions / 64 episodes**; actual shorter native
terminations are counted. Planned total: **2 fits / 360k train / 192k eval**,
552k team interactions at full horizons. No fact collection or replay fit.
Report measured wall, CPU, RSS scope and artifact storage; compare elapsed costs
under shared-node load without claiming an intrinsic speed difference.

Primary reading is paired final-world **R−N original raw native J**. Also read
QoS, delivered service, true return cost, cutoff/depletion counts, charging,
per-world episode minimum battery and its lower tail; preserve every world's
delta, loss count, negative-tail magnitude and actual episode length. Read the
development trajectory as context, not a way to replace the final endpoint.
Positive J with lower cost and no material service collapse strengthens this
specific finite-training opportunity; lower cost with negative J is a failed
net-use tradeoff, and positive J with worse cost does not validate the risk
explanation. Mixed worlds remain mixed. One trained policy per arm cannot
support a population ranking; 32 worlds are paired environments, not 32 fits.
After full acceptance update the cumulative explanation and choose the next
useful action using these outcomes and alternatives. No automatic extension,
coefficient sweep or confirmation is selected by this entry, and completing it
does not itself end this DM's scientific responsibility.

**L0 implementation scope.** Own only new
`experiments/candidates/uav_service_auxiliary/b04/`,
`scripts/run_uav_service_auxiliary_b04.py`, mirrored candidate tests, and this
notebook. Reuse unchanged B01 native setup/initialization/optimizer helpers;
do not change shared learner, environment, B01/B03 frozen code or old outputs.
Provide a fixed N/R admission-guarded CLI, complete native collector/update loop
and original-reward evaluator. Keep scalar reward and cost records, first-rollout
physical collection digest plus stored reward/advantage audit, per-update five
learner displacement and optimizer counts, full raw metric/command trajectories
for independent rescoring, final native checkpoint and artifact hashes.
Preserve terminal next observations before reset, recurrent entry masks and
native sampler/bootstrap semantics. Tests cover reward units/sign/cap failures,
real reward→buffer→GAE→actor update sensitivity, matched pre-update collection,
original-reward zero-update evaluation and RNG isolation, production spec and
admission-before-science. Test-only short CPU/CUDA paths are engineering checks,
not result fits. An independent registered Reviewer reads the complete diff and
checks before DM acceptance. Commit/push exact source before native launch;
arm the accepted operation and end the turn. Failure to retain required evidence
quarantines only its dependent claim; do not invent scientific acceptance from
exit zero. Publish owned standing/plan at the completed preparation/launch
boundary, preserving current main's other directions and controls.

**Implementation acceptance before any fit.** The new B04 files implement the
fixed comparison; shared and frozen scientific code is unchanged. Local focused
CPU suite: **7 passed / 1 CUDA skip, 13.72 s** on the final reviewed reset repair.
The controlled 40-step correctness fixture independently reproduces the expected
low GAE difference and four high interval reward differences, and verifies changed
actual skill-head gradients and low-actor updates. Its synthetic costs are a test
fixture, not native outcome evidence. The real short S7 path checks zero-cost
N/R identity, all five learners, raw rescoring, checkpoint digests, true minimum
battery, zero-update RNG isolation and refusal without admission.

Independent registered Reviewer found and I repaired a terminal-array alias:
the discriminator retains views while production normalizers are off, so the
collector must reset into separate arrays. The regression checks actual stored
terminal state/observation rows after reset and before update. Reviewer re-read
the repair and reported **no outstanding material findings**, after separately
running the native recurrent storage/sampler/update mask regressions (**2 passed,
2.14 s**). Its review is code/engineering acceptance, not scientific acceptance.
An unchanged native limitation remains: strict high-level storage drops an
incomplete k-interval at early termination; this comparison retains that common
behavior and does not claim to repair it. Production 1500-step truncations align
with k=10; raw terminations and partial-path evidence remain recorded.

An additional repository-wide admission-source check fails on the pre-existing
`scripts/run_fsd_commitment_visibility_b12.py`, unchanged from HEAD, because its
AST has no direct `require_admission` call. B04's own guarded entry, SHA mismatch
and no-admission/no-output tests pass. This unrelated FSD script was not changed
or resumed. Initial B04 self-check failures (two wrong metric key spellings and
a 12-step test's unclosed high interval) were fixed before acceptance; fixtures
now use complete k intervals. No scientific fit has yet run.

Fresh remote resource observation during preparation: 13,522 MiB available host
memory and 5,764 MiB free GPU memory on configured wsl_4070; this is a feasibility
observation, not the final launch admission or a resource reservation. The next
step is the same published-source CUDA correctness path on the actual node,
then native admission of N. R remains the fixed second fit, selected irrespective
of N's performance. No repeat Pro Send, task creation or App message is needed.

## 2026-09-23 — B04 N admitted after native CUDA checks

Fixed scientific source **`914fc484368cc6c41af211b169c45b02e4a10425`** is committed
and published. The exact checkout on the configured 4070 node passed the entire
B04 suite: **8 passed in 14.71 s**, including CPU and four-lane/full-hidden-size
CUDA end-to-end checks. No source change followed these checks. The full native
N fit is now **accepted and running**; this is a process fact, not a scientific
result. [Native manifest](../../../../runs/uav_service_auxiliary/b04_n_914021_a01/launch-manifest.json),
[actual-node preflight](../../../../runs/uav_service_auxiliary/b04_n_914021_a01/admission-preflight.json),
[observed native state](../../../../runs/uav_service_auxiliary/b04_n_914021_a01/launch-status.json).
The returned supervisor and child identities both match the live processes;
the manifest supplies the immutable source, exact command, operation and paths.

Detached observation is armed on that same operation, generation **48**, with
a 1500-second bounded window. Initial drain adopted the live native handle;
there are no unconsumed old events or pending Pro deliveries. Retain this worker
and its source. On a checkpoint, read the evidence and rearm the same operation;
on completion, verify the entire output and unchanged evaluation target before
accepting a scientific result. R is already fixed as the second fit and awaits
N's collection/resource release, not a positive performance gate. No further
scientific action is selected in this launch turn.

## 2026-09-23 — B04 N fully accepted; fixed R remains the next fit

**Acceptance.** The original N operation ended with a valid native exit witness,
exit 0, matching recorded identities and a consistent admission record. This is
the same accepted operation, not a restarted fit. I collected all **46 files /
113,794,543 bytes** and verified their SHA256 values against the actual node
before replacing the local initial status snapshot with the final status.
The complete checkpoint, first-rollout audit and all raw trajectories remain
under `runs/uav_service_auxiliary/b04_n_914021_a01/` in this authoring checkout
and at the manifest's original remote output. They are retained even where Git
ignores binary/log artifacts. No remote cleanup occurred.

[Full runner summary](../../../../runs/uav_service_auxiliary/b04_n_914021_a01/summary.json),
[fixed configuration](../../../../runs/uav_service_auxiliary/b04_n_914021_a01/config.json),
[exit witness](../../../../runs/uav_service_auxiliary/b04_n_914021_a01/process-exit.json),
[final observed status](../../../../runs/uav_service_auxiliary/b04_n_914021_a01/launch-status.json).
Summary SHA256 is `ab814a3e1d1861bcc8413c15c828dd39ed25c55106b1a71a6dc76a267f7bff78`.

Independent read-only arithmetic over every stored trajectory reproduced all
30 training-rollout lane returns/metric sums and every field and aggregate in
all 64 evaluation worlds. Original reward was rescored from QoS, actual cost,
event counts and graph PBRS, with maximum per-step discrepancy
`4.440892098500626e-16`; native cost cap, coefficient 2 and N training-reward
identity also matched. All **37 runner-recorded artifact hashes**, configuration
hash, numeric arrays, action bounds, seeds, lengths and terminal flags passed.
There were **180,000 train / 1,440,000 agent rows / 30 updates / 120 episodes**,
and **96,000 evaluation transitions / 64 episodes / zero evaluation updates**.
Every episode truncated at 1500, with no early terminations or rollout-boundary
straddling; stderr is empty.

The first-rollout audit matches the saved physical trace and the actual stored
reward, including the unchanged native discriminator components. Independent
float64 GAE recurrences reproduced the stored FP32 low advantages/returns
(maximum errors `2.195e-6 / 3.933e-6`) and high team/agent advantages and returns
(maximum error across these arrays `1.024e-4`, within `atol=5e-5, rtol=3e-6`
for the accumulated FP32 computation). High interval rewards agree within
`9.537e-7`; all 600 valid high rows have ten-step intervals and the correct final
termination masks. This checks the recorded native path, not a new fit.

All five learners moved at every update. Final optimizer steps are high **2250**,
low actor/critic **67,500 each**, team discriminator **450**, individual
discriminator **1800**; every initialized optimizer tensor has the corresponding
step, both in the summary and loaded checkpoint. Parameter L2 movement from
initialization is respectively **12.590971 / 35.897559 / 31.338790 / 3.048546 /
7.853115**. The checkpoint's 91/15/14/24/29 parameter tensors independently
reproduce final policy hash
`3fee4d9c751aac8dd3c0b5d84839624da63ca22a93f05f744647b1dc8f111408`,
also shared by development update 30 and the final panel. The two registered
positional-encoding buffers are included in the whole-checkpoint hash and finite
checks, but not the parameter-only fingerprint.

**Complete N reading, before its fixed comparator.** QoS and cost below are
per-step means; battery is each world's actual episode minimum, not its average.

| Panel | Native J | QoS | Return cost | Mean episode battery minimum | P10 episode battery minimum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Development 0 | -233.327251 | .098629 | .123193 | .353016 | .326800 |
| Development 10 | +163.285048 | .270542 | .076369 | .371356 | .347821 |
| Development 20 | -1.408604 | .213444 | .103004 | .381249 | .347300 |
| Development 30 | +50.842834 | .252992 | .105077 | .366580 | .341325 |
| Fresh final 32 worlds | **-496.301830** | **.158025** | **.239923** | **.353111** | **.325910** |

Final throughput is **4.740758 Mbps/step**; mean per-episode QoS sum, cost sum and
PBRS sum are **237.037886 / 359.884904 / -13.569907**, reproducing the original J.
All 32 world records are preserved in the summary and independently rescored.
**20/32 J values are negative**, with range **[-1537.378126, +431.154043]** and
P10 **-1392.587969**. Six worlds have zero QoS (938004/11/17/25/30/32); the worst
J and lowest battery minimum **.311067401** both occur in 938032. No charging,
charger input, cutoff or depletion event occurs anywhere in training or any
evaluation panel. This does not test charging recovery or catastrophe reduction.

On the same eight development worlds, update 30 versus initialization has
J **+284.170084**, QoS **+.154363** and cost **-.018117**. This is useful ordinary
learning in that panel, with a non-monotone training trajectory. It does not
justify replacing the fixed endpoint with update 10. The final 32 worlds are
a different sample evaluated with the same update-30 policy; their lower mean
is not additional training deterioration. N alone neither supports nor refutes
the fixed R risk-weighting hypothesis. The paired final comparison, negative
tails and service-risk tradeoff remain unresolved. Shared research judgments
are unchanged at this incomplete-pair boundary.

**Cost and continuation.** One completed fit, **276,000 total team interactions**,
**134.635283 runner minutes**; user/system CPU **7723.455233 / 364.479707 s**.
Collection/update/evaluation wall seconds are **3570.328844 / 1932.932596 /
2201.584883**. Runner-process high-water RSS is **2,986,896 KiB (2.848526 GiB)**;
this is not a simultaneous machine peak or an intrinsic-speed comparison.
The full local run occupies **113,796,311 bytes** after adding the final status.
Read-only verification added zero environment interactions and zero optimizer
updates. Current published main still lifts the owner pause and preserves this
direction/lead; FSD and G33 remain untouched.

Proceed with the already-fixed **R**, same scientific source
`914fc484368cc6c41af211b169c45b02e4a10425`, seed, horizons and evaluation worlds.
The only intervention remains the extra `2 * actual return_constraint_cost` in
training; original evaluation coefficient remains 2. N's observations caused no
coefficient, endpoint, seed or exposure change. R is the second originally
selected fit, not an extension, confirmation or response to a positive N gate.

## 2026-09-23 — B04 fixed R admitted on the same source

The preselected R fit is **natively accepted and running** on the configured
4070, with fresh actual-node available memory **13,679,423,488 bytes** against
the 4 GiB floor. Its supervisor and scientific child identities match and the
operation record is consistent. [Manifest](../../../../runs/uav_service_auxiliary/b04_r_914021_a01/launch-manifest.json),
[admission preflight](../../../../runs/uav_service_auxiliary/b04_r_914021_a01/admission-preflight.json),
[observed state](../../../../runs/uav_service_auxiliary/b04_r_914021_a01/launch-status.json).
The supervisor's successful launch-command exit is not the scientific child's
completion; no R outcome has been accepted.

The written active config and complete spec exactly match N; the arm selector
and extra training coefficient are the intended changes. Training/evaluation
coefficients are **4/2**. The original N operation was collected and accepted
before R's single launch. R's initial summary is still the pre-evaluation
skeleton; the runner publishes initialization/collection fingerprints with its
first progress write, so those matched-initialization checks remain pending.
There is no evidence of an initialization mismatch or a runner failure.

Retain this accepted operation and arm the assigning task's deterministic
observer with the same native status reference. At its next checkpoint read
the newly written fingerprints and progress; at completion collect and verify
the entire R output, then read the fixed paired final worlds and contrary
tails. No restart, new Pro question, new fit or cross-App message is selected
by this completion/launch boundary.


## 2026-09-23 — B04 complete: native final gain with contrary development worlds

**Full R acceptance.** The original accepted R operation completed with a valid
exit-0 witness and consistent native identities. All **46 files / 113,325,077
bytes** matched the actual node byte for byte before refreshing the local final
status. The complete raw trajectories, first-rollout audit and checkpoint remain
in this authoring checkout and the manifest's original remote output; no remote
cleanup occurred. [R summary](../../../../runs/uav_service_auxiliary/b04_r_914021_a01/summary.json),
[config](../../../../runs/uav_service_auxiliary/b04_r_914021_a01/config.json),
[exit witness](../../../../runs/uav_service_auxiliary/b04_r_914021_a01/process-exit.json),
[final observed status](../../../../runs/uav_service_auxiliary/b04_r_914021_a01/launch-status.json).
Summary SHA256: `78cf9a11fa5895d305165e1f43d4bfc3eff11bd324c333aedf23ae7ed842654e`.
Checkpoint SHA256: `d84a99de66b9c65aefde9908545f3956575e53ae94eec9c476adcc8609e26a0d`.
Binary/log artifacts remain recoverable at those locations even where Git ignores them.

The independent read-only audit reproduced every reported return and metric from
all **30 raw training rollouts / 64 evaluation worlds**, checked all **37**
runner artifact hashes plus configuration hash, and reconstructed original reward
from QoS, true return cost, cutoff/depletion counts and graph PBRS. Maximum reward
error is `4.441e-16`; R training reward equals original reward minus twice actual
cost. Training/evaluation cost coefficients remain **4/2**. All numeric arrays,
action bounds, seeds, terminal flags and checkpoint tensors passed. R performed
**180,000 training transitions / 1,440,000 agent rows / 30 updates / 120 episodes**,
and **96,000 evaluation transitions / 64 episodes / zero new evaluation updates**.
Every episode truncated at 1500; no early terminations or straddling occurred.
Stderr is empty; all 30 training/update rows and development/final panels were read.

First-rollout independent float64 recurrences reproduce the stored FP32 low
advantages/returns (maximum errors `4.152e-6 / 7.690e-6`) and both high advantage/
return paths (largest error `2.029e-4`, within the unchanged combined tolerance
`atol=5e-5, rtol=3e-6`). High interval rewards agree within `1.908e-6`. Five native
learners moved at every update; final steps are high **2250**, low actor/critic
**67,500 each**, team discriminator **450**, individual discriminator **1800**.
Every initialized optimizer tensor agrees in the summary and checkpoint.
Initialization-to-final L2 movement is respectively **12.187382 / 35.940557 /
32.300515 / 3.045758 / 7.996300**. Parameter-only fingerprint
`f93a494a789a498b9f15cb274587a04b532df64e2cd65e51b45a0acbce5afe2e`
was independently reconstructed from all 91/15/14/24/29 parameter tensors and
matches both update-30 development and final evaluation. Registered positional
buffers are covered separately by the checkpoint digest and finite check.

**Actual matching and activation.** Complete active config and spec are identical
across N/R; arm and extra coefficient are the intended changes. Initialization
hash `1dfde4b46e1e7a9006cd4a920e3d23f9fefc9c95fdf6cd1a95d9c3bf6f6cf9d6`,
first physical-collection hash
`8e3a0e084544dbc62e400ee964aa7dc4354b06a3937a73cc99a1bd1ce726fdf2`,
and the entire initial evaluation match. Every first-rollout physical metric,
action and end flag matches exactly. Only the recorded training reward changes
in that trace. First-audit low advantages differ by up to **33.613453**, high
advantages by **141.979340**, while pre-update values and native discriminator
components match. First updated policy hashes differ (N `d6887856…`, R `313ccfb8…`).
This resolves the launch-time pending fingerprint check and establishes an active
training intervention. It does not identify which subsequent learning path caused
service gains or isolate actor from critic or high from low effects.

**All prespecified panels.** J is original raw native episode return; QoS and
cost are per-step means. The development eight worlds are reused across updates;
final 32 worlds are a separate sample with the same update-30 policy. No checkpoint
or endpoint was changed after observing results.

| Panel | N J | R J | R−N J | R−N QoS | R−N cost | R−N mean episode minimum battery | J wins/losses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Development 0 | -233.327251 | -233.327251 | +0.000000 | +0.000000000 | +0.000000000 | +0.000000000 | 0/0 |
| Development 10 | +163.285048 | +49.494269 | -113.790779 | -0.042389671 | +0.016954686 | -0.008140019 | 2/6 |
| Development 20 | -1.408604 | -290.908498 | -289.499894 | -0.044626136 | +0.074181672 | +0.006197752 | 2/6 |
| Development 30 | +50.842834 | -167.590619 | -218.433452 | -0.091920514 | +0.027256861 | +0.009926936 | 2/6 |
| Final 32 | -496.301830 | +53.091698 | +549.393528 | +0.108482684 | -0.129009370 | +0.035802733 | 22/10 |

At the fixed final endpoint, N/R mean QoS is **.158025257 / .266507941**,
throughput **4.740758 / 7.995238 Mbps per step**, and true capped cost
**.239923270 / .110913900**. The raw uncapped cost also falls, from **.482361201**
to **.205172231** per step. The native J difference **+549.393528** decomposes
arithmetically into **+162.724026 QoS sum**, **+387.028110 from −2×cost sum**,
and **−.358607 PBRS**. This accounting is not a causal percentage or a separately
recoverable mechanism. Both service and risk contribute on these final worlds.

There are **22 positive / 10 negative** paired J differences, median **+460.498960**,
range **[−899.031058, +2074.949527]**. Negative differences sum to **−4581.104563**;
positive differences sum to **+22161.697451**. QoS rises in 22 worlds, falls in 9,
and ties in one; cost falls in 21, rises in 9, and ties in two. Actual episode
minimum battery rises in 31/32 worlds, but this does not guarantee lower return
constraint cost: distance-to-return and the worst-agent risk also matter.

| Final measure | N | R |
| --- | ---: | ---: |
| Negative raw J worlds | 20/32 | 12/32 |
| P10 raw J | −1392.587969 | −745.607733 |
| Worst raw J | −1537.378126 | −1246.010918 |
| Best raw J | +431.154043 | +731.790480 |
| Mean episode minimum battery | .353111020 | .388913752 |
| P10 episode minimum battery | .325910225 | .347596453 |
| Worst episode minimum battery | .311067401 | .319874564 |
| Zero-QoS worlds | 6/32 | 6/32 |

R still has low absolute mean QoS and substantial adverse tails. Its zero-service
worlds are **938004/06/07/08/14/21**; only 938004 overlaps N's six zero-service
worlds. Thus recovering N's bad worlds can coexist with new failures. World
938021 loses **899.031058 J**, with less QoS and higher cost; 938013 loses
**797.043242 J** despite slightly more QoS and higher minimum battery, because
cost rises. R's worst absolute world 938006 has zero QoS and J **−1246.010918**.
The only lower minimum battery is 938018 (**−.000378834**), even though J improves.
These exceptions remain beside the favorable mean and lower-tail summaries.

**Every final-world paired reading.** All N/R lengths are **1500, truncated**.
Delta throughput is exactly 30 times delta QoS on these fixed demands. Both arms
have zero evaluation charging/charger input/cutoff/depletion in every world.
PBRS and every other raw component remain in the linked complete summaries and
were independently recomputed; the displayed J includes them.

| World | N J | R J | R−N J | R−N QoS/step | R−N cost/step | R−N episode minimum battery |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 938001 | -876.165009 | +274.525449 | +1150.690458 | +0.332404623 | -0.217653536 | +0.071341870 |
| 938002 | +304.295543 | -400.063028 | -704.358572 | +0.027211124 | +0.247950310 | +0.020721208 |
| 938003 | -336.553081 | -549.451758 | -212.898677 | -0.181150777 | -0.018600239 | +0.007245420 |
| 938004 | -1035.744855 | -813.956597 | +221.788258 | +0.000000000 | -0.073778246 | +0.034394596 |
| 938005 | -1394.507223 | -84.942980 | +1309.564243 | +0.194664174 | -0.339755077 | +0.066704315 |
| 938006 | -499.094901 | -1246.010918 | -746.916017 | -0.257748759 | +0.119987829 | +0.011130776 |
| 938007 | +94.403898 | -415.928741 | -510.332639 | -0.302476983 | +0.018782515 | +0.028881709 |
| 938008 | -1484.760602 | -312.253843 | +1172.506759 | -0.120105395 | -0.451287927 | +0.051837829 |
| 938009 | -784.334361 | +320.814966 | +1105.149327 | +0.210441876 | -0.263436803 | +0.037979171 |
| 938010 | +345.871096 | +91.462012 | -254.409084 | -0.171148622 | -0.000085152 | +0.000895267 |
| 938011 | -624.503496 | +421.948265 | +1046.451761 | +0.294237543 | -0.201693629 | +0.038261794 |
| 938012 | +76.060876 | +624.150371 | +548.089495 | +0.219715130 | -0.073609544 | +0.071003829 |
| 938013 | +283.359371 | -513.683871 | -797.043242 | +0.003164532 | +0.267001037 | +0.046760727 |
| 938014 | -155.605685 | -236.029556 | -80.423871 | -0.107733333 | -0.025982966 | +0.006326100 |
| 938015 | -1290.896840 | +343.503162 | +1634.400002 | +0.359996418 | -0.365281045 | +0.048208121 |
| 938016 | -914.169805 | +88.896768 | +1003.066573 | +0.046585258 | -0.311431355 | +0.034390374 |
| 938017 | -266.916911 | -79.831974 | +187.084937 | +0.261717860 | +0.068864971 | +0.047301113 |
| 938018 | -603.156456 | +464.708829 | +1067.865285 | +0.298999531 | -0.206214741 | -0.000378834 |
| 938019 | +101.090234 | +731.790480 | +630.700246 | +0.302625358 | -0.059287460 | +0.050635132 |
| 938020 | -891.134440 | +595.173738 | +1486.308178 | +0.234732926 | -0.378556573 | +0.060806526 |
| 938021 | +131.628216 | -767.402841 | -899.031058 | -0.097151555 | +0.251027992 | +0.028107587 |
| 938022 | +431.154043 | +492.485199 | +61.331156 | +0.074257258 | +0.016204577 | +0.018225158 |
| 938023 | -1252.867887 | +599.631291 | +1852.499178 | +0.299453158 | -0.468080700 | +0.077772057 |
| 938024 | -483.329470 | -841.076947 | -357.747477 | -0.073460877 | +0.083028542 | +0.002783265 |
| 938025 | -1198.684186 | +414.467193 | +1613.151379 | +0.287144697 | -0.393902538 | +0.003290648 |
| 938026 | +337.549766 | +319.605839 | -17.943927 | -0.069035448 | -0.028675451 | +0.007890095 |
| 938027 | +185.714621 | +558.623046 | +372.908425 | +0.250069707 | +0.000000000 | +0.061051208 |
| 938028 | -1375.314685 | +144.834265 | +1520.148950 | +0.237151291 | -0.388531455 | +0.053592060 |
| 938029 | +316.524526 | +514.356281 | +197.831755 | +0.133129515 | +0.000000000 | +0.069959398 |
| 938030 | -1506.037629 | +381.857851 | +1887.895480 | +0.263481608 | -0.497305144 | +0.037875348 |
| 938031 | +21.844910 | +39.160986 | +17.316076 | +0.152781846 | +0.069755094 | +0.026365502 |
| 938032 | -1537.378126 | +537.571401 | +2074.949527 | +0.367492195 | -0.507753122 | +0.024328071 |

**Contrary development evidence.** The same final policies on development worlds
instead have **R−N J −218.433452**, QoS **−.091920514** and cost **+.027256861**,
with **6/8 J losses**. P10 episode minimum battery is also slightly lower for R
(**.338897015 versus .341325436**) despite its higher mean minimum. World 937003
loses **951.891591 J** while QoS and minimum battery rise, with cost **+.357820225**.
World 937007 gains **352.316155 J** by reducing cost but loses **.334601897 QoS**.
Development updates 10 and 20 also favor N on mean J, QoS and cost; this is not an
isolated late comparison. R's own same-world J gain from initialization to 30 is
**+65.736632**, compared with N's **+284.170084**. That is useful learning in this
panel, without a monotone improvement curve or an R advantage. Initial policies
were not evaluated on the final panel, so no final-panel own-learning increment
is asserted. The opposite final/development comparison cannot be called another
training change: the policy hashes at update 30 are identical across the panels
within each arm. Nor does this finite sample identify a systematic distribution
shift, evaluation overfitting or failure mechanism.

**Event exposure.** R training contains one actual charging UAV-step, rollout 25,
zero-based step 936 / lane 1, with **.277777778 Wh** charger input; N training has
none. Both have zero cutoff/depletion throughout all training and evaluation,
and all evaluation has zero charging. Preserve this small training exposure;
it cannot support charging recovery, competition or catastrophe-reduction claims.

**Working update and next decision.** The frozen prediction of lower cost,
non-collapsed service and higher original J is realized on the primary final
panel. This strengthens the bounded possibility that direct weighting of real
risk can turn finite native learning into net service benefit, without an MSE
head. It weakens a categorical claim that stronger risk weighting can only buy
safety by sacrificing service. It does **not** establish that the original risk
coefficient is generally too small or that coefficient 4 is a better default.
Development performance contradicts uniform risk reduction and uniform net use;
world losses and one trained pair prevent a stable training-method ranking.
Policy/value scaling, both hierarchy levels and subsequent state visitation
change together. Their independent roles remain unresolved. The old B03 sign
reversals and failed proxy ordering stay intact; this is not a rescued auxiliary
result, proof of optimality or a physical UAV safety result.

Current published main `b512311aff062034799414338bf69f1043a710d6`, shared topics
3 and 6, was read at this decision. Its independent-training-unit warning makes
recurrence a distinct question from estimating the use of these fixed policies
on more worlds. Its B11/B12 target-training reversal is another reason not to
promote a large single-pair endpoint automatically; that S1 evidence does not
falsify this S7 intervention. Its B02 low-discriminator deletion result keeps
native mixed RL a competent working reference, not a component-necessity proof.
These uses favor preserving ordinary N and testing the actual risk intervention
before proposing another architecture or reviving the old auxiliary head.

The earlier complete project Pro advice supports the direct-risk premise, but
contains no decision about this newly observed strong final gain plus contrary
development panel. Before choosing renewed learning investment, ask one focused
follow-up below: another independent N/R pair on fixed exposed worlds versus a
zero-fit wider-world evaluation of the existing pair. The answer can reverse my
provisional preference for a fresh learning pair. No new fit, coefficient sweep,
confirmation or replay is selected yet; B04 is complete, and the scientific
responsibility continues through this concrete choice.

**Cost and observation closure.** R is **152.041147 runner min**, user/system CPU
**8712.419316 / 421.226692 s**, collection/update/evaluation wall
**3988.163467 / 2303.179677 / 2308.520845 s**, peak runner RSS
**2,989,520 KiB (2.851028 GiB)**. After final status refresh its local size is
**113,326,845 bytes**. N/R together are **2 fits / 360k training / 2.88M agent rows /
192k evaluation / 552k total team interactions**, sum runner **286.676430 min**,
sum user/system **16435.874549 / 785.706399 s**. Stage evaluation alone totals
**75.168429 min**; it is material non-fit work. These walls reflect actual shared
node conditions, not an intrinsic speed comparison; RSS is per-run high-water,
not a sum or simultaneous machine peak. Admission of N to exit of R spans
**303.797771 min**, including the between-fit collection interval.
Independent rescoring and checkpoint verification added zero interactions and
updates. The READY evidence was consumed with generation 60 and its exact wake/
event IDs; generation **61** retains no active B04 experiment. There is no old
Pro delivery awaiting collection and no duplicate launch or cross-App message.


## Pro question 2026-09-23 b04-risk-gain-next-discriminator

Conversation: reuse the direction's completed Jev conversation from local
operation `hmasd:89adf42eea46a3380a9f9bac76cf9fec1c4fda626d6a8da2205de6d41cf61f75`;
its private URL stays only in local operation state.

**Question and decision.** After an active, fully verified S7 risk-weighting
intervention yields a large positive original-J difference on its fixed final
worlds but negative differences on every post-initial development panel, what
single next observation is worth buying for service-and-risk learning? My
provisional preference is one new independent matched N/R training pair, with
unchanged coefficient, budget and both existing evaluation panels. The strongest
alternative is zero-fit evaluation of the two existing final policies on a
predeclared wider fresh-world panel. Please choose between these or give a
concrete stronger alternative/end-investment reason, rather than an automatic
sequence of all studies. The scientific choice is renewed investment and its
estimand, not whether the completed run was technically accepted.

**Standing and actual evidence.** The immediately preceding complete B04 entry
contains independent verification, all final-world differences, adverse cases,
learning curves and measured costs. Original S7 reward is
`QoS - 2*c_return - 5*new_cutoffs - 10*new_depletions + graph_PBRS`;
`c_return=min(max_i(max(0,-return_margin_i))/.05,1)`. Ordinary complete native
HMASD N uses it directly; R changes only the scalar supplied to native storage to
`r_native - 2*c_return`, affecting both high/low returns, GAE, actors and critics.
Native mixed discriminator rewards, entropy, information, physics and action
bounds stay matched. Both evaluate original coefficient 2. There is no auxiliary
head. Seed914021, four lanes, 180k team transitions per arm, 30 full updates;
actual initialization, first physical collection and initial evaluation match.
The intervention changes both levels' advantages and the first actual update.

Fixed update-30 final worlds938001–938032 give N/R J **−496.301830/+53.091698**,
R−N **+549.393528**, QoS **+.108482684**, capped cost **−.129009370** per step,
22 positive/10 negative J differences, median **+460.498960**, worst relative loss
**−899.031058**. Final mean/P10 episode minimum battery improve; R still has
12/32 negative-J worlds, six zero-service worlds and worst absolute J−1246.010918.
Update-30 development worlds937001–937008 instead give **−218.433452 J**,
**−.091920514 QoS**, **+.027256861 cost**, 6/8 losses and a slightly worse P10
battery. Development differences at updates10/20 are **−113.790779/−289.499894 J**.
The final/development panels share the exact final policy within each arm, so
that reversal is not additional training. There are no evaluation charging,
cutoff or depletion events; one charging UAV-step occurs in R training only.
One trained pair is not 32 training replicates; the world samples do not prove
systematic distribution shift or locate an optimization defect.

Earlier B03 auxiliary S/D and G/D signs reversed over two training blocks, with
both blocks evaluated on the same final worlds. Their exact raw-J differences
are **+24.585407/−16.825601** and **+117.896434/−24.945921** respectively. The
project-level prior Pro answer misquoted their units/numbers; its following
Decision and our original summaries correct them. Do not reuse those wrong
numbers. B03 remains closed; lower common MSE did not order control usefulness.
The complete project advice's direct-risk proposal motivated B04, but it did
not address this new panel-sensitive positive result or select the next batch.
No follow-up is needed merely to repeat routine implementation/verification.

**Two feasible candidate investments, not selected or launched.**

- Fresh-learning recurrence: two new native fits at the same 180k horizon and
  coefficients N=2/R=4, a prospective fresh seed such as914173 with four lanes,
  identical initialization within pair, identical matched native conditions.
  Keep B04's two panels fixed to avoid changing both training instance and
  worlds; call them already exposed development evidence, not new held-out
  confirmation. Same0/10/20/30 schedule gives **2 fits / 360k train / 192k eval /
  552k total team interactions**, 2.88M train agent rows. Predeclare which joint
  J/service/risk pattern would retain or lower investment and preserve each
  panel and adverse world separately. This tests recurrence conditional on these
  worlds, not a stable population effect from n=2. B04 cost was286.676430 sum
  runner min; future shared-node wall is unknown. Small parameter plumbing and
  a focused check may be needed, not a new model or a coefficient search.
- Fixed-policy world sensitivity: both frozen B04 final checkpoints, a predeclared
  fresh64-world panel (e.g.939001–939064), 1500-step native evaluation, original
  coefficient2, deterministic actions and zero updates: **0 fits / 192k eval**.
  Report all paired J/QoS/cost/minimum-battery values and adverse tails. This can
  refine the use judgment for these two policies but cannot add training
  recurrence or identify why their training diverged. B04's192k evaluation cost
  alone was75.168429 min; zero fits is not zero cost. A narrow checkpoint evaluator
  would need identity/RNG/reproduction checks and engineering review if changed.

No extra head, critic decomposition, coefficient sweep, training extension,
checkpoint selection, automatic third block or confirmation is proposed. A
same-objective separate-cost critic is an unselected alternative with a weaker
current activation/bottleneck rationale. There is no obligation to invent a new
architecture or rescue a positive number. Pro may recommend a better targeted
choice only with distinct predicted intermediate/native consequences and honest
implementation, fit and non-fit costs.

**Context and source precedence.** This question and the immediately preceding
B04 result are at `source_sha` (the immutable commit supplied in the message).
Read these concrete sources; the small current-main set below has an explicit
revision because the experimental branch does not overwrite current governance.

- Current governance: `docs/project/OPERATING_CONSTITUTION.md` §§1–5,7–8 at
  `b512311aff062034799414338bf69f1043a710d6`. Owner pause is lifted; current owner
  scientific-autonomy/three-DM delegation lets this DM choose and continue useful
  work. FSD remains owner-paused and G33 frozen. No cross-App messages.
- Current methods: `.agents/skills/hmasd-scientific-tools/SKILL.md`, “Update the
  working explanation”, “Comparators and MARL information”, “Statistics”, “Cost
  and exposure”, “Pro”, at that same current-main revision. No mandatory new
  architecture, pilot success, exact-head repeat test, or per-fit permission.
- Shared scientific background: `docs/research/RESEARCH.md`, topics3 and6 and
  DM3 current plan at that revision. Relevant contrasts are DM1 B11/B12 target
  training reversal and DM2 B02 removal of low discriminator reward; they constrain
  inference/default promotion, not the S7 result itself. The owned DM3 row there
  predates R completion; the `source_sha` result above supplies the newer facts.
- Prior advice: `docs/research/archive/2026-09-23/RESEARCH-scientific-management-adopted.md`,
  full Answer and Decision at that current-main revision, especially the direct
  risk-learning proposal and correction to S7 numbers. Its decision scope is
  distinguished from this new follow-up; do not require another owner approval.
- Frozen scientific source: `914fc484368cc6c41af211b169c45b02e4a10425`, this notebook's
  “B04 prospective direct service and return-risk learning” and
  `experiments/candidates/uav_service_auxiliary/b04/native.py`, `evaluation.py`,
  `scripts/run_uav_service_auxiliary_b04.py` only where a disputed contract needs
  code. Current methods do not revise the original seed, endpoint or outputs.
- Primary runner evidence at `source_sha`: both
  `runs/uav_service_auxiliary/b04_n_914021_a01/summary.json` and
  `runs/uav_service_auxiliary/b04_r_914021_a01/summary.json`, plus config, progress,
  exit/status. Read their final worlds, all development aggregates, actual counts
  and intervention fingerprints. The DM's raw NPZ/checkpoint byte audit is reported
  above; these binaries are retained locally/on the node and are not necessarily
  available through GitHub. Do not claim to have independently byte-verified them.
- This notebook's prior “B03 second common replay accepted and current recipe
  closed” for inherited adverse evidence, at `source_sha`; no recursive archive
  preload or literature survey is needed. If a new literature premise changes
  the decision, use a primary passage and separate its result from analogy.

**Return.** Give a direct choice with what it can change, the strongest reason
against it, and what observations would change your recommendation. Separate
observed facts, strengthened/weakened/untouched judgments and newly suggested
explanations; address the large final gain, negative development panels, adverse
worlds and actual costs together. If selecting a new study, give a narrow fixed
comparison and prospective outcome branches, with units of inference and
exposure. A failed intermediate prediction is not a reason to keep varying
architecture or coefficients. Return `MATERIAL_DISSENT: yes/no` with substantive
reason and cite consequential sources actually read; name any decision-critical
unread gap. No fixed candidate count or mandatory extra investigation.

**Write scope.** Do not train or launch anything. Write only into the empty
`### Answer` immediately below this unique question on branch
`codex/uav-service-predictive-control`, file
`docs/research/candidates/uav_service_auxiliary/NOTES.md`. Read the question at
`source_sha`, fetch the latest target file/blob SHA before writing, preserve every
other byte and stop on overlapping edits. Report the actual write commit. If
writeback is unavailable, return the complete answer in chat rather than a
receipt, link or SHA. Advice is not approval and does not lift a pause. The
scientific decision remains this DM's under existing owner authorization.

### Answer

Saved from chat, complete original answer. Same accepted question key:
`hmasd:9c663dfbd9d85af2ad743a57b23ff3bc2d7e48878eff62bd5252c071b8ece5c5`,
source `5c6af88f406b0b97d7f988f8d5cb9351d6afb893`. The deterministic observer
collected 8,650 characters, body SHA256
`79fd8810c1a5715ad21bc63da9f32b521e6629dbc4e2b6c0d003865dddc01152`.
The saved file adds one final newline, SHA256
`cd4d5b158dc322ff390f02aa62aaff8002274540b6f2c50f321a250fdd28554c`.
`deliver` verified **NOT_DELIVERED**, no write commits; the hash beginning
`f1b909f5` in the reply is described as a target blob and is not a delivery
commit. The branch and empty target subsection remain unchanged. I read the
entire answer below before taking back the subsection. Citation placeholders
and the extracted display-math line breaks are preserved; no question was resent.

~~~text
GitHub 读取可用，但本轮可调用接口未提供文件写入动作，因此未写回；实际 Answer commit：无。 最后读取的目标 blob 为 f1b909f5f0d6ed5dfa28aa8b05935c2a89600708，指定问题下的 ### Answer 仍为空。本轮没有修改仓库，也没有启动实验。以下是完整答复。

B04 下一笔投入：选择一次新的匹配训练对，保留两个面板的分歧

MATERIAL_DISSENT: no。

我支持一次新的、恰好两 fit 的 N/R 匹配训练比较：保持训练系数 N=2、R=4，保持每臂 180k transitions、固定 update-30 终点和两套既有评价世界。此次不同时选择旧策略的 64 新世界评价，不启动确认，也不增加系数搜索或新模块。

支持这一选择的实质理由是：当前要决定的是风险重加权作为有限训练配方是否值得继续投入，而不是仅在已经训练好的两个 checkpoint 中挑选一个。新的训练对能增加一个独立学习实例，检查原生收益及其面板敏感性是否重现；扩大旧策略的评价世界数，虽然有价值且较便宜，却不增加这项学习重复。这个选择不把 B04 的大正差视为已确认优势，也不把开发面板的持续负差降格为可以忽略的噪声。

一、先把 B04 的正面结果和反面结果放在同一读法下

下面保留各预定训练后面板的原始对比。J 是原生完整 episode 奖励总和的世界均值，不是 R 自己的重加权训练回报；QoS 和成本差是每步均值，均按 R−N 计算。

hmasd-pro-question-usa-b04-next…

面板	原生 J 差	QoS 差	封顶返航成本差	J 胜／负世界数
开发 update 10	−113.790779	−0.042389671	+0.016954686	2／6
开发 update 20	−289.499894	−0.044626136	+0.074181672	2／6
开发 update 30	−218.433452	−0.091920514	+0.027256861	2／6
固定最终 32 世界，update 30	+549.393528	+0.108482684	−0.129009370	22／10

最终面板是一个值得认真复查的原生阳性，不是只有风险代理量变好。 N/R 的 QoS 为 0.158025257／0.266507941，封顶成本为 0.239923270／0.110913900，未封顶成本也从 0.482361201 降到 0.205172231。J 差的算术分解是服务项约 +162.724026、原生的 −2×成本项约 +387.028110、PBRS 约 −0.358607。因此，这些世界上的收益同时得到服务和风险分量支持；不能说它只是换了评价权重才显得更好，也不能把上述分解变成机制贡献百分比。

hmasd-pro-question-usa-b04-next…

它也不是只靠一个最有利世界抬高均值：32 个差值中有 22 个为正，中位数为 +460.498960。但尾部并未消失。R 仍有 12 个负 J 世界、六个零服务世界；两臂的零服务集合只有一个世界重合。世界 938021 的相对损失达 −899.031058，938013 在 QoS 和最低电量稍有提高时仍损失 −797.043242，因为返航成本上升。恢复 N 的某些坏世界与产生新的坏结果可以同时发生。 这些异常不能被均值、P10 或最低电量的总体改善覆盖。

hmasd-pro-question-usa-b04-next…

开发面板则是对“普遍降低风险并改善服务”的直接反证。 三个训练后面板不只 J 较差，QoS 也较低、返航成本也较高。update-30 开发和最终评价使用各臂同一个终点策略，summary 中的策略指纹对此相符，所以两面板反号不是 R 又训练了一段时间所致。另一方面，这三个开发读数复用了同一组八世界，也不是三个独立训练阴性，更不能仅凭这次有限样本把反号命名为系统性分布迁移、评价过拟合或某个优化缺陷。

hmasd-pro-question-usa-b04-next…

还要保留一个绝对学习水平的边界：开发世界上，R 从初始化到终点的 J 提高约 +65.736632，N 提高约 +284.170084；这说明 R 在该面板发生了有用学习，却没有建立相对 N 的优势。最终面板没有初始化评价，不能拿开发初始化与最终终点相减，声称 R 在最终世界上的自身学习增量。 所有评价又都没有充电、cutoff 或 depletion 事件；一次训练中的充电 UAV-step 不支持充电竞争、恢复能力或灾难率下降的结论。

hmasd-pro-question-usa-b04-next…

二、工作解释应当怎样更新

被加强的是一个有限训练机会：直接加强真实风险在训练目标中的权重，能够在一次完整训练比较的预定最终面板上，同时改善原生服务、真实成本和原生 J。 初始化、首轮物理采集和初始评价相符，首轮两层 advantages 及首次更新发生差异，两个运行都有完整原生优化器更新。因此，“修改没有真正进入学习”“只是评价重计分”已不适合作为当前结果的解释。原始数组及 checkpoint 的逐字节核验仍归属于 DM 的已报告审计；我本次核对的是源码、配置、summary、进度及退出／状态记录。

hmasd-pro-question-usa-b04-next…

被削弱的是两种过强说法。 第一，“加强风险惩罚只能通过牺牲服务来获益”不符合最终面板；第二，“系数 4 会普遍减少风险并提高净收益”不符合开发面板和不利世界。合适的更新不是在两个说法中选一个，而是承认：这个干预有真实但条件敏感的有限训练用途，其跨训练可重复性仍未知。

未被识别的是收益的独立机制。 R 修改的是进入原生存储的奖励标量，从而同时改变高低层 return、GAE、actor advantages 和 critic targets；后续访问状态也随之变化。它不是同目标下只修复一个 critic，也不是把风险梯度单独加到低层 actor 的隔离实验。奖励与价值尺度、有限优化过程和访问轨迹的作用尚未分离。因此，“原系数一般过小”“风险表征更正确”“某一层信用分配被修好”都仍属于新猜想，而不是 B04 已经给出的诊断。

继承证据要在这里真正约束投入，而不是只作引用。B03 的正确原始 J 差是 S−D +24.585407／−16.825601、G−D +117.896434／−24.945921；它说明同一最终面板上的辅助包差异也会随训练块反转，且共同 MSE 不提供可靠控制排序。项目级旧 Answer 的错误数字不能复用，后续 Decision 的纠正和本方向原记录才是依据。B04 没有辅助头，不能把当前阳性记成 B03 的挽救。

指定当前背景中的 DM1 B11/B12 目标训练反转，进一步支持“不因一个大终点就提升为默认”；DM2 删除低层判别器奖励后的不利结果，则支持继续保留完整 native mixed RL 作为本次工作参照，而非未经依据地再删一个组件。这两项 S1 证据既不否定 S7 的阳性，也不识别 S7 的收益来源。它们对当前设计的具体影响是：保留 N，先重复真正发生的风险干预，不同时改变结构或内在奖励。

三、为什么下一笔钱买新的训练对，而不是先买更多旧策略世界

两种候选分别补充不同的不确定性。

冻结策略的新 64 世界评价，考察的是：给定 seed 914021 已经产生的这两个终点策略，它们在另一组世界上的相对用途怎样？ 新的 N/R 训练对则考察：换一个完整训练实例，在相同两组世界上，这套训练干预还能产生怎样的 J／服务／风险差异？

当前已经有两个事实：旧策略对世界条件敏感；这套学习干预只有一个训练对。增加旧策略世界数可以更清楚地描述前者，但不会增加后者。鉴于本题要决定的是后续学习投入，我愿意为第二个训练实例支付更高成本。它能让“训练实例变化”和“评价面板变化”形成一个小而有用的交叉比较，而不是每次同时换训练种子和世界、最后无法判断哪里发生了变化。

其不同预测可以写得具体：

可重复的风险训练用途预期：新实例在固定最终面板仍呈现较低真实成本、未塌缩的服务和较高原生 J；不要求精确重现 +549.393528。

B04 特定学习轨迹的有利分化容许：新实例虽然再次确认干预进入 advantages 和更新，最终的服务／风险增量却消失或反转。

较稳定但有范围的面板依赖预期：新实例又出现最终面板有利、开发面板不利。这样的重复会使“差异只属于 B04 这一次训练偶合”较难维持，却仍不给出一般用途，更没有自动识别一个可部署的世界分类规则。

这些是供下一观察区分的工作假说，不是已经估计出来的发生概率。重复相同正负格局也不证明两组 seed 编号代表某种已知任务亚群；尤其不能根据已经看过的世界成绩，事后构造“这个世界用 N、那个世界用 R”的选择器并计作当前方法的收益。

最强的反对理由与成本

反对我这一选择的最强理由，是当前最显眼的问题确实来自世界敏感性，而冻结评价以更低成本就能直接扩大其观察范围。 R 的绝对服务还低，旧终点尚有严重坏世界；再花一对完整训练的成本，可能只增加另一对同样不成熟、同样难泛化的策略。两套已暴露面板上的第二次阳性仍不是总体确认。这个反对理由成立，不能靠“科研就应该多 seed”回避。

两项候选的名义工作量如下。历史时间仅用作成本尺度，不是未来共享节点的运行保证。

hmasd-pro-question-usa-b04-next… +1

下一项候选	新训练 fits	训练团队 transitions	评价团队 transitions	历史成本参照
一对新的 N/R 完整训练	2	360,000	192,000	B04 两 fits 合计 286.676430 runner 分钟
旧 N/R 终点策略 × 64 新世界	0	0	192,000	B04 的 192k 评价阶段合计 75.168429 分钟

新训练方案另有 2.88M 训练 agent rows，总计 552k 团队交互。冻结方案也需要 checkpoint 加载、身份和 RNG／复现核对，以及必要的窄 evaluator 实现；“零 fit”不等于零工程或零计算。B04 的 runner wall 总和、303.797771 分钟的批次经过时间、CPU 时间和每个进程的 RSS 高水位属于不同口径，不能相互替代或把 RSS 相加当作机器峰值。

hmasd-pro-question-usa-b04-next…

我仍选择新训练对，是因为其成功和失败都能改变这套学习配方的投入理由。 若实际用途改为“只决定这两个旧 checkpoint 中哪个更值得使用”，我会转而选择冻结 64 世界评价；若无论下一对如何都准备继续调系数，或即使复现也绝不考虑保留任何用途，那么这一对也没有足够决策价值，直接停止当前配方开支更一致。材料没有提供效用函数或机会成本的数值，因而这里是有理由的投资判断，不是计算出的最优预算分配。

本建议没有选择“训练复现之后自动加 64 世界，再自动确认”。两种研究不是免费的前后置步骤，只选择当前这一项。

四、我建议固定的下一项比较
科学条件与执行绑定

使用题面候选 914173 作为拟定的新训练 seed，N/R 各从头训练一次；四 lanes、1500-step rollout／episode、30 次完整更新，每臂 180k 团队 transitions。仍采用 S7-S2、interface v3／reward v2／arm C、8 UAV、30 用户、固定 k=10，保留原生网络、PPO、判别器奖励、熵、信息权限、归一化、循环 reset 和 S7 实际动作执行。CUDA FP32、TF32 关闭、四 Torch 线程及实际节点准入沿既有方式处理。914173 在此是拟采用值，本次没有声称已核验其全部历史使用情况；实际输入绑定应明确记录这一点，而不是仅更换输出目录名称。

hmasd-pro-question-usa-b04-next…

保持唯一目标干预：

r
train,N
	​

=r
native
	​

,r
train,R
	​

=r
native
	​

−2c
return
	​

.

环境和两臂评价始终使用原生系数 2；不改变成本的 0.05 尺度、封顶 1、cutoff／depletion 惩罚或 PBRS。训练时是 2 对 4，评价时是 2 对 2。这里的原生标量不再除以 UAV 数量，也不拿两臂各自不同目标的训练回报直接排名。

有一处执行描述必须写实：冻结 B04 CLI 的 --seed 只接受 914021；production_spec() 也会拒绝其他 seed，并返回原 B04 默认 spec。因此新 seed 不能由冻结入口原样执行，单改 CLI 的 choices 也不够。需要一个窄的后继参数绑定，使选定 seed 真正进入 spec 和 run_native，保留准入、来源身份及其他科学设置；记录实际发布的新来源版本，不改写旧 B04 入口和结果。这个边界来自源码阅读，不是已完成 B04 的缺陷，也不是新增科学审批。

两臂应复用匹配的初始化和外生随机设计，并通过已有初始化、首轮物理采集和首次更新记录核对。新的 seed 同时改变模型初始化、随机流及训练世界，是一个新训练实例，不是单独隔离“初始化”的实验。保留现有审计足以核查干预是否生效；不为此次复现额外引入辅助头、梯度夹角调查或全新的 critic 诊断工程。

面板、估计对象与读数

保留 937001–937008 在 update 0／10／20／30 的开发面板；保留 938001–938032 在 update 30 的终点面板。这两组世界现在都属于已暴露的开发证据，“final”只是继承的面板和终点名称，不能再次称为未查看的确认集。不查看旧面板上的中途分数来修改 R、缩短／延长训练，或追加世界。

对训练块 b 和面板 p，分别报告

Δ
b,p
J
	​

=
∣W
p
	​

∣
1
	​

w∈W
p
	​

∑
	​

[J(π
b,R
30
	​

,w)−J(π
b,N
30
	​

,w)],

并在相同世界上分别报告 QoS 和真实成本差。终点 32 世界的原生 J 差保留为主读数；开发八世界的终点差和整条曲线保留为范围约束，不合并成一个事后选择权重的总分。 配对依据是实际共同设计和世界，不是 seed 字符串相同。原有科学方法明确区分了独立训练单位、嵌套评价和选择曝光。

这会形成四个不能互相遮蔽的终点格子：

训练块	开发八世界	既定终点 32 世界
B04，914021	−218.433452	+549.393528
新训练块，拟 914173	单独报告	单独报告，保留主终点

即使第二行全正，也只是两个训练实例的探索；不能把 32／40 个世界、评价 episode、四个 checkpoint 或数百万 agent rows 当作更多训练重复。即使对世界差值计算条件于策略的误差区间，也不能把其精度冒充跨训练总体精度。

每个面板继续并列报告绝对 J、服务、封顶及未封顶成本、实际 episode 最低电量及其下尾、充电／cutoff／depletion 曝光，保留全部世界和实际长度。最低电量不能代替返航成本；固定需求下吞吐量与 QoS 的倍数关系也不能被算作两份独立证据。真实早终的完整回报按实际 episode 计入，不填补到 1500、不因其不利而剔除；每步尺度只作补充。冻结 evaluator 已明确累计原生回报、记录真正 episode minimum battery，并保持零评价更新。

五、什么结果改变下一步选择

下表是我建议事前采用的投入分支，不是总体显著性检验或机械的“正号通过”规则。

新训练对的预定终点观察	对解释和投入的改变
32 世界再次有值得保留的 J 增量、较低成本和兼容服务；开发面板也不再给出实质相反结果	加强风险重加权的有限训练复现理由，弱化“仅 B04 学习轨迹巧合”的解释。保留候选，但不把系数 4 设为默认，不自动确认。
32 世界的服务／风险净收益重现，但开发面板仍明显不利	保留“在这些世界上可重复”的窄观察，同时加强面板敏感性。不把重复了正面格子理解成普遍用途。 不能据此选择一个未识别的世界条件规则；若所需用途是通用默认方案，本轮仍不足以支持继续按该用途投入。
32 世界的原生收益消失、反转，或小到不足以改变保留价值；只有开发面板或早期 checkpoint 有利	显著降低当前固定系数 4 配方的投入理由，默认结束它的继续训练开支。不能用旧 B04 大正差、两块均值、另一面板或第三对训练掩盖新块主读数。
成本降低但原生 J 变差，或 J 提高却没有风险改善／伴随不可接受的服务损失	前者是未兑现净用途，后者未兑现直接风险解释。保留实际得到的分量权衡，不改称原假说成功，也不自动扫系数、换 critic 或恢复辅助头。

这里尤其要区分两件事：保留一个研究观察，与选择再花一笔钱，不是同一个决定。 “最终正、开发负”的重复可以产生可复用认识，却仍不足以支持通用控制器使用。R 当前低绝对 QoS、零服务世界及严重相对损失，意味着下一对即使平均正，也必须读它究竟改善了什么、留下多大损害；不能把任何一个正小数当作确认经费或部署资格。材料未给出与实际用途相符的最小有用差异和尾部容忍线，我不会从 +549.393528 倒推一个门槛，或偷用历史配置中的 gate 代替这次探索的用途判断。

相反，新块反向也不证明所有风险重加权都无效；它改变的是继续这一固定配方的理由。技术错误导致的无效读数必须单列，保留尝试和成本，不能算科学阴性；同一语义下的工程修复由 DM 按现有责任处理，不能借修复悄悄更换 seed、系数或终点。失败的中间预测不是反复更换模块直到阳性的理由。

本次没有选中确认。将来只有出现值得主张的实际用途，才需要在真实 CLAIM 中固定候选、主要对照、选择曝光、训练和世界总体、主终点、实用差异及小样本不确定性方法，并依现行方法采用全新独立训练种子。B04 和这里建议的新训练对都留作探索；它们不会因累计数量增加而自动变成确认。结束一个配方也不等于解除 DM 的方向责任，但本答复不据此安排另一个自动后继研究。

六、来源范围和信息缺口

本次读取的科学输入按附件绑定：问题、完整 B04 结果及指定 B03 收尾记录使用 5c6af88f406b0b97d7f988f8d5cb9351d6afb893；治理、科学方法、共享背景主题 3／6、DM3 计划以及项目级完整 Answer／Decision 使用 b512311aff062034799414338bf69f1043a710d6；B04 前瞻合同及有关执行、奖励和评价路径使用冻结来源 914fc484368cc6c41af211b169c45b02e4a10425。背景的 DM3 状态早于 R 完成，未用它覆盖较新的 B04 结果。移动分支只用于最后核对写回目标，不替代这些输入。

两份 primary summary 的最终世界、全部开发聚合、实际计数和干预／策略指纹，以及两份配置、退出和最终状态记录已读取；progress 核对了可见采集记录和终点段，没有把整个原始轨迹审计重新执行一遍。仓库外 NPZ、checkpoint 和真实节点文件的逐字节一致性、GAE 的 float64 复算等，均是已读 NOTES 中 DM 报告的核验，不是我的独立二进制复核。GitHub 的 COMPLETE、exit-0 和一致状态记录支持其已完成的文本证据，但不使我取得未读取的数组。

hmasd-pro-question-usa-b04-next…

没有缺失到需要以记忆补写的决策核心文字来源。真正未满足的内容是：新的训练观察、可支持总体判断的跨训练精度、未暴露世界上的更广用途、以及新 seed 的实际后继入口和运行成本。它们分别限制复现、主张范围与执行，不是把已经可作的方向级选择推回另一个审批流程。

最终建议保持不变：只选择一次新的匹配 N/R 训练对，固定系数与两个已暴露面板，购买跨训练实例的判别信息；保留大最终收益和持续开发劣势的全部张力。若新观察不能增加值得使用的服务—风险证据，就结束当前配方的追加投入，不用更大世界面板、更多 seed 或新模块自动接续。

MATERIAL_DISSENT: no——同意“先买一次新学习实例”的选择，不同意将其理解为默认采纳、总体确认，或已经排除了面板依赖。

~~~

## 2026-09-23 — B04 advice adopted; B05 fixed independent training recurrence

**Decision and actual update.** I adopt the complete Pro recommendation for
exactly **one new N/R training pair**, and its adverse-outcome branches. The
current question is whether the finite-learning intervention is worth retaining;
another 64 worlds for the old checkpoints cannot add a training instance. This
justifies the greater cost of learning, not an entitlement to a second positive
number. I do not select the alternative old-policy wider-world study. Advice
adds no empirical replication, establishes no mechanism and grants no permission;
the owner already delegated this scientific choice. Current main
`36db756f30dfe0452207457a881d16e9095cec7b` retains the pause lift, this lead and
three-DM autonomy; FSD/G33 remain untouched. Its relevant topic-6 B04 reading
and unchanged constitution were rechecked. B03 remains closed.

Pro's consequential numerical descriptions agree with the independently
recomputed B04 pair. Its distinction between four endpoint cells and a pooled
score applies: the main comparison was positive only on one panel; development
losses and each arm's absolute failures are part of use. Its source gap is
explicit: it did not read external raw binaries or perform our arithmetic audit.
That does not undermine its investment argument, and I do not attribute those
checks to Pro. `MATERIAL_DISSENT: no` is advice, not acceptance of a wider claim.

I verified the concrete implementation criticism: B04 CLI accepts only914021,
and its production_spec rejects other seeds and returns that default. Changing
only a tag or argument list would not deliver a fresh fit. The new selected seed
is **914173**, with lanes **914173–914176**. A targeted check finds no such seed
in this direction's retained run config/summary files; this is not a claim about
every unobserved historical task. The subsequent actual initialization/collection
fingerprints must differ from B04 and match within the new pair. Both model/RNG
and training worlds change; no isolated-initialization explanation is claimed.

**Prospective B05 comparison, before new results.** Same N/R intervention and
S7-S2/v3/reward-v2/arm-C conditions as B04: N=8, users30, k10, four lanes,
30×1500-step rollouts = **180k team transitions / 1.44M agent rows per arm**;
complete native high/low and discriminator learning, no auxiliary heads. N uses
original reward, R subtracts `2 * actual post-transition return_constraint_cost`
before native storage, so training coefficients are2/4. Both evaluate original2.
All networks, optimizer/update budgets, information, clipping, normalization,
termination/truncation, intrinsic rewards, entropy, cost cap/scale and PBRS remain
unchanged. CUDA FP32/TF32-off/four Torch threads on configured4070 after actual
admission. N then R, each initialized from scratch, without an N-performance gate.

Keep worlds937001–937008 at updates0/10/20/30 and worlds938001–938032 only at
update30, deterministic original-objective evaluation with RNG preservation and
zero optimizer updates. Both panels are now **already exposed development
worlds**; the inherited `final` name denotes a fixed endpoint, not fresh held-out
confirmation. Do not select checkpoints, change weights, add worlds, alter
horizon or tune after intermediate results. Native early ends remain included
with actual episode return and length, never padded/excluded for bad performance.

Primary reading: B05 R−N raw original J on the32-world endpoint, alongside QoS,
throughput, capped/uncapped actual cost, charging/cutoff/depletion, true episode
minimum battery and its lower tail. Keep every world's difference, losses and
amplitudes. Present both B04/B05 training blocks on both endpoint panels separately;
no pooled mean can hide a new adverse cell. Development curves constrain scope
without replacing the primary. Two training pairs remain exploratory; nested
worlds/checkpoints/lanes/agent rows do not increase independent training n.

Prewritten interpretation and investment branches:

- Repeated meaningful endpoint J gain with lower risk and compatible service,
  without substantial contrary development use, strengthens keeping this finite
  training candidate. It neither promotes coefficient4 to default nor selects
  confirmation. Read absolute service, bad worlds and cost before investing again.
- Repeated positive final and negative development cells strengthens a narrow
  panel-sensitive observation, not general use or a deployable world selector.
  Preserve both cells; a universal-default use remains unsupported.
- Endpoint net benefit disappears/reverses or is too small to change retention:
  lower investment in this fixed weighting recipe and end its further training
  by default. No third pair, alternate checkpoint, other panel or B04 pooled
  average rescues it. This does not reject all risk learning or end DM responsibility.
- Lower cost with lower original J fails net use; higher J without lower cost
  fails the proposed risk explanation. Preserve actual tradeoffs. Neither selects
  a coefficient search, critic replacement or revival of the old auxiliary head.
- Technical invalidity is separate, with its attempt and cost recorded; same-effect
  reconciliation and any repair preserve the fixed scientific contract. No blind retry.

There is no invented universal minimum-effect or tail-tolerance gate. The visible
service and loss amplitudes determine whether a result changes a practical
retention judgment; no arbitrary positive decimal guarantees further investment.
This is one new prospective study with a recurrence reason, not retroactive
extension or confirmation of the completed B04 batch.

**Exposure and cost.** Exactly **2 new fits / 360k train / 192k eval upper bound /
552k total team interactions**, 2.88M train agent rows, no fact/replay collection.
Reference sum fit wall286.676430min includes75.168429min evaluation; future wall
under shared-node load is unknown. Record actual wall/CPU/RSS scope and archive
bytes; independent rescoring adds no interactions. Preparation, narrow plumbing,
checks, independent review, staging, collection and full reading are additional
work, not a performance claim. No wider-world evaluation or third fit is selected.

**L0 implementation scope.** Add `b05/native.py` as the fixed production seed/spec
binding, `scripts/run_uav_service_auxiliary_b05.py` as the new guarded entry, and
mirrored B05 tests. Reuse the already-reviewed B04 collector, objective, learner,
evaluator, checkpoints and raw outputs. One narrowly justified change to the
current B04 helper is an optional `object_id` argument with its existing B04
value as default; B05 passes its own identity. This is metadata only, avoids a
copied numerical runner, and leaves the frozen914fc4843 source, old CLI/spec and
all results unchanged. No mutable-global patch or hidden default-seed substitution.

Check production CLI→spec→active-config seed, actual initialization/RNG/lane seeds,
unchanged fixed evaluation worlds and their physical initial states, correct new
object identity and unchanged B04 default, no-science-before-admission/SHA refusal,
and a short real storage/update/evaluation/checkpoint path. Reuse B04's nonconstant
risk/GAE/actor and terminal-view regressions; do not repeat generic engineering
work without a changed risk. Independent registered Reviewer checks the narrow
scientific-input/result-identity diff before acceptance. Commit and push exact
inputs, validate the changed path on the actual CUDA node, then admit N and
observe its original operation. No result-bearing fit has started in this entry.


**B05 implementation acceptance before remote validation.** The narrow new binding
and guarded entry now implement the fixed seed; the only B04 helper diff is the
optional output identity and its unchanged default. Combined B04/B05 checks:
**13 passed / 2 CUDA skips, 17.17 s**. The first invocation failed at collection
because the two files shared pytest module name `test_native`; renaming only the
new test to `b05/test_recurrence.py` resolves it. No scientific run occurred in
that collection failure. The final suite verifies actual new/old initialization
and first-collection differences, new-pair matching, config and all lane seeds,
new/default result identity, identical initial obs/state in all40 exposed worlds,
identical deterministic fixed-policy traces under either policy RNG seed, and
admission/SHA refusal. Existing real reward→GAE→actor and terminal-view regressions
remain covered. Independent registered Reviewer reports **no material findings**,
explicitly separating source/coverage review from actual CUDA validation still
pending. I accept this bounded implementation; actual-node checks precede any fit.

The full Pro answer is saved once and the exact READY event is consumed at
generation62, advancing observation to63. There is no active prior experiment
or pending answer; inspection finds no remaining tab for this completed private
conversation, and preserves all three unrelated browser targets. No repeat Send
or App message occurred. The next action is actual-node correctness on the
published B05 inputs, followed by native admission of the already-fixed N.

## 2026-09-23 — B05 N admitted after fixed-seed CUDA checks

Scientific source **`3de3e3f71c747e2422656126b52ae88beafb562a`** is committed and
published. Its retained, clean checkout on configured `wsl_4070` passed the
complete new B05 suite: **7 passed in 22.21 s**, including its actual CUDA
collection/update/evaluation/checkpoint path. The local combined B04/B05 result
remains 13 passed / 2 CUDA skips; independent review found no material findings.
No source change followed actual-node validation.

The fixed **N / seed914173** fit was natively accepted at
**2026-09-23T19:56:22.822292Z**. The launch kernel rechecked current main
`cfb058e5974d0f71304631659a6c8a0742f49abf`, the lifted pause, unchanged direction
and exact lead, published source and actual-node resources. Available physical
memory was **14,131,367,936 bytes**, above the **4,294,967,296-byte** floor.
[Native manifest](../../../../runs/uav_service_auxiliary/b05_n_914173_a01/launch-manifest.json),
[actual-node preflight](../../../../runs/uav_service_auxiliary/b05_n_914173_a01/admission-preflight.json)
and [observed native state](../../../../runs/uav_service_auxiliary/b05_n_914173_a01/launch-status.json)
retain the operation, command, source and original output paths. The supervising
and scientific process identities both match, records are consistent, and the
runner is **running** with no exit witness. Admission is not scientific acceptance:
**0 completed/accepted B05 results** at this observation.

Detached observation is registered and has adopted that same native operation,
generation **64**, 1500-second bounded window. The initial drain has no pending
events or undelivered Pro answer. Preserve this source and worker; a checkpoint
rearms observation without restarting it. Complete output collection, native
accounting, seed/fingerprint binding and the full fixed panels remain required
before accepting N. **R is already fixed as the second fit**, after N collection
and resource release, irrespective of N's performance. The pair remains exactly
2 fits / 360k train / 192k eval upper bound; no additional action is selected.

## 2026-09-23 — B05 N fully accepted; fixed R follows unchanged

**Complete acceptance.** The original N operation has a valid native exit-0
witness and consistent recorded process identities. All **46 remote files /
113,321,414 bytes** were collected and matched by SHA256; the full binary traces,
audit and checkpoint remain in the original remote output and this checkout.
[Summary](../../../../runs/uav_service_auxiliary/b05_n_914173_a01/summary.json),
[configuration](../../../../runs/uav_service_auxiliary/b05_n_914173_a01/config.json),
[exit witness](../../../../runs/uav_service_auxiliary/b05_n_914173_a01/process-exit.json)
and [final native status](../../../../runs/uav_service_auxiliary/b05_n_914173_a01/launch-status.json)
retain the evidence. Summary SHA256 is
`1af4318fdd21d5723054b12d8b89f99688d32190b4d89933074ce2913d9e12c9`;
checkpoint SHA256 is
`1a6a2b6c191d3dc74ac244b474dc6071905c71d6a973eea78a97e94e6fbcceb8`.

Independent arithmetic over all raw arrays reproduces every recorded training
lane return/metric sum, every evaluation world's fields and all aggregates.
Original reward recomputed from QoS, capped actual return cost, event counts and
PBRS agrees within **4.441e-16**; N's training reward is exactly native reward.
All 37 runner-recorded artifact hashes, config hash, finite arrays, bounded
actions and fixed evaluation seeds pass. Actual counts are **180k training /
1.44M agent rows / 30 updates / 120 episodes**, plus **96k evaluation / 64
episodes / zero evaluation updates**. Every episode truncates at1500, with no
early terminal or rollout-boundary straddling; stderr is empty.

The real first-rollout buffer agrees with its physical trajectory and native
discriminator reward components. Independent float64 low GAE/return recurrences
match FP32 storage with maximum errors **2.286e-6 / 4.109e-6**; high team/agent
GAE and returns match within the previously used combined tolerances
`atol=5e-5, rtol=3e-6` (maximum absolute difference **1.079e-4**). All600 high
rows span ten steps and have the expected terminal masks. Every learner moves
on every update. Final optimizer steps are high2250, low actor/critic67500 each,
team discriminator450, individual discriminator1800; all optimizer tensor steps
match the loaded checkpoint. L2 movements from initialization in that order are
**13.343682 / 36.659901 / 31.517461 / 2.948467 / 8.086486**.

The bound config and active seed are914173. Relative to B04, all scientific
settings match except that selected seed; the only additional literal config
difference is the inherited baseline path's checkout prefix. The comparison
gate is explicitly disabled in both native configs, and that file is absent
in both retained remote checkouts; it supplied no old-arm data to this run.
The new actual initialization and first-collection fingerprints both differ
from B04, as prospectively required:

- Initialization: `9cec1f0e1b0f0cb965c120af9587a7ca8bcd0b2a9deddbbd09570c4c35209d43`.
- First physical collection: `55d27fc4802d687ecb0a5bb793d5db40dca143e71515d5d531ed83d9494c9bc8`.
- First update: `381d49b17b57f94c1709a45f09f49bc6b4b1afbee55ccb37c448726d036c6cba`.
- Final policy: `22ade2e3aa948330acb4916445277edab0611a5159a1bef7beade8d1aefadc79`.

The checkpoint's actual parameter tensors independently reproduce the final
fingerprint, shared by development30 and the final panel. Initial evaluation
uses the initialization fingerprint. These are distinct training instances,
not isolated-initialization evidence; R must match this new pair's initial
policy and first physical collection before its treatment can be read.

**Full N reading before the fixed comparator.** Both evaluation panels remain
already exposed development worlds. The `final` label denotes the fixed
update30 endpoint, not fresh confirmation. QoS and cost are per-step means;
battery is the true minimum over each episode.

| Panel | Native J | QoS | Return cost | Mean episode battery minimum | P10 episode battery minimum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Development0 | -222.092843 | .105247 | .122681 | .351597 | .325471 |
| Development10 | -26.407571 | .218984 | .113952 | .364937 | .326567 |
| Development20 | +87.562908 | .237458 | .085035 | .386833 | .351716 |
| Development30 | -72.367636 | .276942 | .158086 | .378313 | .340282 |
| Final32 endpoint | **-232.025030** | **.216058** | **.180829** | **.361646** | **.319036** |

Final throughput is **6.481735 Mbps/step**, uncapped cost **.369444984**. Mean
episode QoS, capped cost and PBRS sums are **324.086770 / 271.243481 /
-13.624839**, reproducing native J. All32 world results are retained and read:
**14 negative J / 18 positive J**, range **[-1796.058763,+666.535107]**,
J P10 **-1561.212995**. Worst J is938005, with QoS.037220341 and cost.612961156.
World938021 has zero QoS, J **-1224.469675**, and the lowest episode battery
**.307733819**. A positive service mean does not remove these failures.

On the same eight development worlds, final30 minus initialization gives
J **+149.725207**, QoS **+.171694978**, throughput **+5.150849 Mbps/step**,
but capped return cost **+.035404663** and uncapped cost **+.060078610**.
QoS and battery minima improve in all8 worlds, while J improves in6 and falls
in937004/937006 (**-66.727501 / -39.639874**). Return cost rises in5 worlds,
falls in1 and ties in2. Thus battery minima alone do not establish lower return
risk, and ordinary native learning delivers more service without resolving the
net-use tradeoff. Development J falls **159.930544** from update20 to30 despite
higher mean QoS; the fixed endpoint is retained. The lower final-panel mean uses
the same update30 policy on other worlds, not additional training deterioration.
No initialization reading exists for those32 worlds, so no final-panel learning
increment is claimed. N alone leaves the R−N recurrence prediction unresolved;
B04/B03 shared judgments are unchanged at this incomplete-pair boundary.

No cutoff/depletion occurs in training or evaluation. Training records **3
charging UAV-steps / .833333333 Wh**, each one UAV in lane1 (zero based):
rollout25 steps1225/1249 and rollout27 step793 (zero based). Every evaluation
panel has zero charging or charger input. These sparse training events do not
establish improved charging recovery or catastrophe prevention.

**Cost and fixed continuation.** One completed fit, **276k total interactions**,
**124.628160 runner minutes**; CPU user/system **7169.527964 / 317.091823 s**.
Collection/update/evaluation wall seconds are **3210.558280 / 2023.930494 /
2240.020451**. Runner high-water RSS is **2,983,716 KiB / 2.845493 GiB**, not
simultaneous machine peak; local output including final status is **113,323,182
bytes**. Read-only verification added no interactions or optimizer updates.
Current main `f32cd55dc95e11b84b3661ddf00d5d2456a59159` keeps this direction,
lead and pause lift. Proceed with the already-fixed **R**, same published source
`3de3e3f71c747e2422656126b52ae88beafb562a`, seed914173, horizons and panels.
Its sole training intervention remains the extra `2 * actual return cost`;
evaluation remains native coefficient2. No observation above changes the
coefficient, endpoint, exposure or decision to execute this second fit.

## 2026-09-23 — B05 fixed R admitted on the same source

The preselected R fit is **natively accepted and running** on configured4070
at **2026-09-23T22:11:13.450180Z**, after N's full collection and independent
acceptance. Source remains **`3de3e3f71c747e2422656126b52ae88beafb562a`**,
seed914173, CUDA FP32/TF32-off/four threads, with the original frozen N/R
contract. The kernel refreshed main
`3d0b52e2841beb57054aa0aca9ac864a6fa430b0`, preserving this lead and pause lift,
and measured **13,293,408,256 bytes** available physical memory against the
**4,294,967,296-byte** floor. [Native manifest](../../../../runs/uav_service_auxiliary/b05_r_914173_a01/launch-manifest.json),
[actual-node preflight](../../../../runs/uav_service_auxiliary/b05_r_914173_a01/admission-preflight.json)
and [initial native status](../../../../runs/uav_service_auxiliary/b05_r_914173_a01/launch-status.json)
retain the exact operation, input command and identities. Both scientific child
and supervisor match the observed live processes; no exit witness exists.

The N READY event has been fully read and consumed at generation68. Detached
observation of R has adopted this native handle at **generation70**, with a
1500-second bounded window and no pending events. Preserve the original worker
and unchanged source. On completion, collect and hash all artifacts, independently
rescore the original objective, verify the new pair's matched initialization/
first collection and actual reward/GAE separation, then read both endpoint panels
and all loss worlds against N and the prewritten recurrence branches. Admission
does not establish R's scientific result. Current state: **1 completed/accepted
B05 fit, 1 fixed fit running**, no extra fit, Pro Send or App message.


## 2026-09-23 — B05 complete: endpoint risk savings recur, service gains do not

**Acceptance and source.** The original R operation has a consistent native
exit-0 witness (finished epoch1790209597.9591453), with both recorded processes
absent. All **46 remote files / 113,135,103 bytes** were collected and matched by
SHA256, including immutable admission/manifest records. The complete traces,
first-rollout audit and checkpoint remain locally under
`runs/uav_service_auxiliary/b05_r_914173_a01/` and on configured4070 at
`/home/wu/hmasd-worktrees/usa-b05-3de3e3f71/runs/uav_service_auxiliary/b05_r_914173_a01/`.
[Summary](../../../../runs/uav_service_auxiliary/b05_r_914173_a01/summary.json),
[configuration](../../../../runs/uav_service_auxiliary/b05_r_914173_a01/config.json),
[exit witness](../../../../runs/uav_service_auxiliary/b05_r_914173_a01/process-exit.json)
and [final native status](../../../../runs/uav_service_auxiliary/b05_r_914173_a01/launch-status.json)
are retained. Summary SHA256 is
`ed0210e281390f612e9b616e1f2767ae347f1bc93c353347cb9babb71f4c1969`;
checkpoint SHA256 is
`fd338b75475289fb01c6b9bfc2576ea3b042756e1094b65e0b2e08d5cd92f226`.
Both arms bind unchanged scientific source
`3de3e3f71c747e2422656126b52ae88beafb562a`, seed914173 and actual lanes914173–914176.

Independent arithmetic reproduces all30 raw training rollout returns/metrics,
all64 evaluation worlds and aggregates, original reward decomposition, capped
actual cost and the R training objective `native - 2*actual_cost`. All37 runner
artifact hashes and the config hash pass. Raw original-reward error is at most
4.441e-16; the training-objective identity is exact. R completes **180k training /
1.44M agent rows / 30 updates / 120 episodes**, plus **96k evaluation / 64 episodes
with zero evaluation optimizer updates**. All observed episodes truncate at1500;
there are no early ends or rollout-boundary straddles, and stderr is empty. This
is an observation, not an exclusion rule for adverse or short episodes.

The real first-rollout low GAE/returns independently recompute within maximum
errors4.192e-6/7.909e-6. High team/agent GAE and returns pass the existing combined
`atol=5e-5, rtol=3e-6` tolerance, maximum absolute error2.266e-4; all600 valid high
rows have their ten-step span and actual terminal masks. Every learner moves at
every update; final steps are high2250, low actor/critic67500 each, team
discriminator450, individual discriminator1800. Loaded optimizer tensor counts
agree. L2 movement from initialization is high12.765128, low actor36.607234,
critic31.673184, team2.818533, individual8.040014. All checkpoint tensors are finite;
actual parameter bytes independently reproduce the final policy fingerprint.

**Matched intervention.** N/R config differences are exactly arm and extra
training cost0/2. The two recorded initialization and first physical-collection
hashes match, and differ from B04. Independently retained first-rollout actions,
native rewards, all metrics and episode ends are array-identical; initialization
evaluation traces match in every world. Actual first-buffer values, masks,
intrinsic components and return cost also match. Thus the intervention is active
on the same physical data, before subsequent policy trajectories diverge.

- Shared initialization: `9cec1f0e1b0f0cb965c120af9587a7ca8bcd0b2a9deddbbd09570c4c35209d43`.
- Shared first collection: `55d27fc4802d687ecb0a5bb793d5db40dca143e71515d5d531ed83d9494c9bc8`.
- R first update: `c7762254c17506ff0bb7b6497ecbab918bce74524e5682e26d92dcc1d29371fe`.
- R final policy: `fc9db9351e74f38bcda00faef5e5686b22ac46f71ad91eaaaba46723ebebaea5`.

Training reward differs at1306/6000 first-rollout team transitions, mean delta
−.377832337 and maximum absolute2. Stored agent environment reward differs at
10448 entries, low GAE maximum delta33.613453, and high agent GAE maximum
142.007660. High reward changes at131 valid intervals. Both first-update and
final policy hashes differ from N; final development30 and final32 share R's
same final checkpoint. These checks establish real storage/learning exposure,
not which component of the subsequent adaptation caused the outcome.

**Complete fixed reading.** The protocol and investment branches were written
[before B05](#2026-09-23--b04-advice-adopted-b05-fixed-independent-training-recurrence).
Both panels are exposed development worlds; `final` is a fixed endpoint label,
not new held-out confirmation. QoS, cost and throughput below are per-step means;
J is the original raw episode return. No checkpoint/world/arm is selected out.

| Panel | N J | R J | R−N J | R−N QoS | R−N capped cost | J wins/losses |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Development0 | -222.092843 | -222.092843 | +0.000000 | +0.000000000 | +0.000000000 | 0/0 |
| Development10 | -26.407571 | +26.283545 | +52.691116 | -0.019354809 | -0.027283942 | 5/3 |
| Development20 | +87.562908 | +142.925395 | +55.362487 | -0.003838285 | -0.020360990 | 6/2 |
| Development30 | -72.367636 | -110.027297 | -37.659662 | -0.117039433 | -0.045606817 | 3/5 |
| Final32 | -232.025030 | +9.860423 | +241.885454 | -0.026788931 | -0.094165509 | 14/18 |

The primary endpoint improves **+241.885454 J**, but its median paired difference
is **−99.441797** with **14 wins / 18 losses**, range[−676.258092,+2042.732101].
Total positive differences are12783.176162 and losses−5042.841640. Final QoS
falls **.216057847→.189268916**, throughput **6.481735→5.678067 Mbps/step**;
QoS rises12/falls19/ties1 worlds. Capped cost falls **.180828987→.086663479**
(16 lower/12 higher/4 ties), uncapped cost **.369444984→.173588333**
(14 lower/14 higher/4 ties). The original-J accounting identity is service
**−40.183396**, the coefficient2 cost term **+282.496526**, PBRS **−.427676**.
Those terms sum to the observed difference; they are not independent causal shares.

R has **13 negative-J worlds**, eight zero-QoS worlds
**938004/06/07/08/09/14/21/23**, versus N's14 negative-J and one zero-QoS938021.
Six of R's14 J wins still deliver zero service:938004/06/07/09/21/23. Six worlds
improve both QoS and capped cost (938001/05/12/15/19/28); nine lower both QoS
and cost. Thus neither a universal no-service explanation nor a generally
service-compatible risk gain is supported. R's worst absolute J is
**−1343.076641 at938008**, with zero service and cost.442745031; best J is
+550.916909 at938001. Its J P10 is−598.208581 (N−1561.212995). The largest
relative losses are938030−676.258092,938016−648.502144 and938014−517.531872;
938030 also loses.221761384 QoS. The largest win938005+2042.732101 corrects
N's worst absolute world, including lower cost and more service.

Final true episode minimum battery mean rises **.361645883→.368945925**,
P10 **.319035567→.325502468**, worst **.307733819→.320263605**. Individual
minima improve18 and worsen14, worst difference−.056616208 at938031; R's
lowest absolute minimum is938032. Battery and geometric return cost remain
separate outcomes, not interchangeable risk measures.

On development30, R is **−37.659662 J** despite lower mean cost; QoS is
**.276942462→.159903029**, throughput8.308274→4.797091. There are3 wins/5 losses,
median−42.418403; strongest losses937001−446.897103,937002−433.814113 and
937005−419.076393. R has5 negative-J and2 zero-QoS worlds (937005/937007),
versus N's4 and0. Development R's own30−0 learning is **+112.065545 J**,
QoS+.054655545, cost−.010202154 and throughput+1.639666, with J5 up/3 down;
N's corresponding J+149.725207, QoS+.171694978 and cost+.035404663 remain.
R's QoS improves5/falls1/ties2 versus initialization; all8 battery minima improve.
The unchanged-panel R J falls **252.952693** from update20 to30; no earlier
checkpoint replaces the endpoint. No initialization measurement exists on the
final32 worlds, so their own learning increment cannot be inferred.

All endpoint worlds are retained below. Length is1500 for both arms in every
row; no event or length adjustment generates the ordering.

| Panel/world | N J | R J | ΔJ | N QoS | R QoS | N cost | R cost | N battery min | R battery min |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 937001 | 281.006204 | -165.890898 | -446.897103 | 0.194734 | 0.261912 | 0.000000 | 0.182190 | 0.393162 | 0.408536 |
| 937002 | -258.928491 | -692.742604 | -433.814113 | 0.244954 | 0.048203 | 0.204764 | 0.251673 | 0.436937 | 0.416640 |
| 937003 | 366.571828 | 349.894878 | -16.676950 | 0.465480 | 0.242311 | 0.105640 | 0.000000 | 0.371493 | 0.367136 |
| 937004 | -94.156202 | 57.338046 | 151.494248 | 0.393540 | 0.170040 | 0.223451 | 0.062200 | 0.370602 | 0.351079 |
| 937005 | 409.080037 | -9.996357 | -419.076393 | 0.281843 | 0.000000 | 0.000000 | 0.000000 | 0.432866 | 0.385667 |
| 937006 | 206.564970 | 479.237063 | 272.672093 | 0.210094 | 0.343866 | 0.031467 | 0.007039 | 0.346310 | 0.368186 |
| 937007 | -1023.588074 | -364.407295 | 659.180778 | 0.174786 | 0.000000 | 0.423721 | 0.116464 | 0.330786 | 0.381442 |
| 937008 | -465.491357 | -533.651212 | -68.159855 | 0.250110 | 0.212892 | 0.275646 | 0.280268 | 0.344352 | 0.333894 |
| 938001 | -187.990277 | 550.916909 | 738.907185 | 0.281652 | 0.377377 | 0.198643 | 0.000000 | 0.341567 | 0.362548 |
| 938002 | 304.681632 | -102.323559 | -407.005191 | 0.211052 | 0.255619 | 0.000000 | 0.157826 | 0.332845 | 0.376799 |
| 938003 | -285.235167 | -545.928645 | -260.693478 | 0.210874 | 0.045500 | 0.196347 | 0.201364 | 0.340932 | 0.335112 |
| 938004 | -1040.922537 | -1029.767743 | 11.154793 | 0.097845 | 0.000000 | 0.391483 | 0.338319 | 0.373240 | 0.383787 |
| 938005 | -1796.058763 | 246.673338 | 2042.732101 | 0.037220 | 0.174528 | 0.612961 | 0.000000 | 0.313620 | 0.369798 |
| 938006 | -880.517761 | -726.349576 | 154.168185 | 0.143121 | 0.000000 | 0.360789 | 0.237178 | 0.318845 | 0.355499 |
| 938007 | -297.303106 | -57.896777 | 239.406329 | 0.125488 | 0.000000 | 0.157258 | 0.014247 | 0.327238 | 0.361498 |
| 938008 | -1257.431391 | -1343.076641 | -85.645250 | 0.125527 | 0.000000 | 0.477848 | 0.442745 | 0.329083 | 0.357346 |
| 938009 | -1611.942492 | -36.492755 | 1575.449736 | 0.004222 | 0.000000 | 0.534817 | 0.007058 | 0.320755 | 0.370444 |
| 938010 | 385.535197 | 240.674779 | -144.860418 | 0.273256 | 0.169340 | 0.003335 | 0.000000 | 0.349557 | 0.345817 |
| 938011 | 595.705532 | 197.846947 | -397.858585 | 0.407251 | 0.205530 | 0.000000 | 0.032037 | 0.381638 | 0.359382 |
| 938012 | 182.694045 | 492.807143 | 310.113099 | 0.211788 | 0.337729 | 0.041053 | 0.000000 | 0.413075 | 0.437684 |
| 938013 | 607.339525 | 318.304534 | -289.034992 | 0.414423 | 0.220527 | 0.000000 | 0.000000 | 0.377124 | 0.326996 |
| 938014 | 262.644013 | -254.887859 | -517.531872 | 0.183699 | 0.000000 | 0.000000 | 0.082098 | 0.373599 | 0.322278 |
| 938015 | -1520.376718 | 383.874273 | 1904.250991 | 0.052689 | 0.293913 | 0.528511 | 0.013836 | 0.328531 | 0.372824 |
| 938016 | 131.370650 | -517.131494 | -648.502144 | 0.272036 | 0.178501 | 0.087564 | 0.257443 | 0.363861 | 0.340034 |
| 938017 | 418.179523 | 405.147445 | -13.032078 | 0.374194 | 0.279853 | 0.042493 | 0.000000 | 0.378572 | 0.360934 |
| 938018 | 583.507255 | 329.257722 | -254.249533 | 0.399342 | 0.246235 | 0.000000 | 0.008550 | 0.400974 | 0.365729 |
| 938019 | -754.504727 | 482.213228 | 1236.717955 | 0.009889 | 0.331413 | 0.252212 | 0.000000 | 0.386119 | 0.430694 |
| 938020 | 666.535107 | 493.590489 | -172.944618 | 0.454361 | 0.348868 | 0.000000 | 0.005132 | 0.413796 | 0.408802 |
| 938021 | -1224.469675 | -133.741015 | 1090.728660 | 0.000000 | 0.000000 | 0.404020 | 0.039640 | 0.307734 | 0.372870 |
| 938022 | 333.905437 | 220.667093 | -113.238344 | 0.230813 | 0.339106 | 0.000000 | 0.091376 | 0.351441 | 0.388137 |
| 938023 | -1565.750359 | -15.063101 | 1550.687258 | 0.012033 | 0.000000 | 0.523557 | 0.000000 | 0.323128 | 0.371432 |
| 938024 | -210.134824 | -604.017463 | -393.882639 | 0.293700 | 0.275246 | 0.211844 | 0.333911 | 0.365200 | 0.325337 |
| 938025 | 362.754967 | 134.035486 | -228.719481 | 0.252247 | 0.259704 | 0.000000 | 0.080185 | 0.410062 | 0.354122 |
| 938026 | 348.324970 | 141.536994 | -206.787975 | 0.279101 | 0.371549 | 0.018936 | 0.133474 | 0.364079 | 0.369205 |
| 938027 | 121.856158 | 337.312915 | 215.456757 | 0.088756 | 0.234015 | 0.000000 | 0.000000 | 0.388113 | 0.422108 |
| 938028 | -1607.928730 | 58.873495 | 1666.802225 | 0.060830 | 0.149371 | 0.562183 | 0.050078 | 0.313952 | 0.374587 |
| 938029 | 344.417567 | 391.018454 | 46.600888 | 0.237934 | 0.269794 | 0.000000 | 0.000000 | 0.471270 | 0.488481 |
| 938030 | 372.052300 | -304.205793 | -676.258092 | 0.386593 | 0.164832 | 0.064218 | 0.179108 | 0.374128 | 0.350860 |
| 938031 | 446.204619 | 329.051651 | -117.152968 | 0.306687 | 0.227842 | 0.000000 | 0.000000 | 0.381478 | 0.324862 |
| 938032 | 348.057057 | 232.613075 | -115.443982 | 0.475228 | 0.300214 | 0.116458 | 0.067628 | 0.357114 | 0.320264 |

**Recurrence, without pooling.** Read the four preselected endpoint cells:

| Training block | Panel | R−N J | R−N QoS | R−N capped cost |
| --- | --- | ---: | ---: | ---: |
| B04 | Development30 | -218.433452 | -0.091920514 | +0.027256861 |
| B04 | Final32 | +549.393528 | +0.108482684 | -0.129009370 |
| B05 | Development30 | -37.659662 | -0.117039433 | -0.045606817 |
| B05 | Final32 | +241.885454 | -0.026788931 | -0.094165509 |

The fixed final-panel J/cost signs recur in the independent new training pair,
weakening the narrow explanation that B04's final net gain was unique to that
one realized training instance. The development/final sign split also recurs,
strengthening the scope restriction. However, B04's final service improvement
does **not** recur: B05 has lower mean service, majority J losses and eight
zero-service worlds. It is not a repeated general service/risk improvement, a
coefficient ranking, a panel classifier or a validated controller. Two training
pairs, and nested worlds/lanes/checkpoints, do not establish population reliability.
No aggregate across B04/B05 or across panels rescues these adverse cells.

This is the previously advised **positive final / negative development** branch,
with a stronger service tradeoff. It is not the branch claiming disappearance of
the primary benefit. Keep the useful conditional risk-cost observation, but do
**not** select more training of the same fixed coefficient4 recipe, a third pair,
a coefficient sweep, an earlier checkpoint or confirmation. The evidence does
not justify further spending toward a general default controller through this
unchanged weighting intervention. That investment choice is not a universal
rejection of direct risk learning and does not end this DM's service/risk task.
The complete earlier Pro advice already covers this reading and its limits;
a materially different next intervention requires a focused new consultation.

Current published background was read at main
`9c9a5d2c1c1fc482a7215734f6751613b81ddabc`, topic6. The new result narrows its
B04 opportunity: **repeated final mean J/cost benefit can coexist with majority
paired losses and increased complete service failures**. Native N remains a
necessary control; returning to old service/MSE auxiliaries is not justified.
The owner pause remains lifted for this direction, and its exact lead is unchanged.

A **post-result, descriptive inspection** of retained final traces (zero new
interactions/updates) used six equal250-step bins, without selecting worlds.
In B05, N/R mean costs are respectively0/0,0/.000008349,.052370/.002454,
.212646/.046231,.325313/.140988,.494646/.330299. Their QoS means are
.088980/.083865,.161533/.126308,.211554/.163596,.262310/.194234,
.263353/.257090,.308617/.310520. Last-bin cap saturation is41.7375%/23.95%
of world-steps. B04 last-bin costs are.633737/.489203, cap saturation52.875%/
38.7875%. This localizes much of the *recorded cost*, but does not identify a
credit-assignment failure or prove those states were recoverable. B05 service
loss appears before material evaluated cost; training objectives may change the
whole policy, not just late risky decisions.

Source inspection at3de confirms current actor observations already include UAV
battery, raw return margin/threshold and relative station features
(`energy_aware.py::_energy_observation`); adding those same scalars is not a new
information intervention. `_raw_return_energy_margins` uses present battery minus
nearest-station return-energy estimate and reserve. A possible distinct question
is whether a fixed, observation-legal, margin-conditioned return feedback can
preserve useful N behavior while reducing late cost. It might instead disrupt
relay service or fail to avert cost. No heuristic rule, threshold, trial or
learning redesign is selected here. The **next action is a focused Pro comparison
of that cheaper execution intervention with a justified learning revision or
stopping**, using these full results and the actual information/action contract.
It will not reopen an old Pro key or turn the positive endpoint into automatic
additional fits. Any selected experiment needs its own prospective protocol.

**Cost and observation closure.** R uses **135.364231 runner minutes**, CPU
user/system7762.451981/370.666898s, collection/update/evaluation3448.894897/
2056.114872/2613.010093s. High-water RSS is2,994,108KiB/**2.855404GiB**, not
simultaneous machine memory. R local files including final status total
113,136,871bytes; both B05 outputs total226,460,053bytes. The batch is exactly
**2 completed fits /360k train /192k eval /552k total team interactions /
2.88M training agent rows**, **259.992391 summed runner minutes**, including
80.883842 evaluation minutes; N admission to R exit spans270.252281min.
Implementation, checks/review, collection and independent arithmetic are extra
engineering work, not additional fits or episodes. R has no charging, charger
input, cutoff or depletion in training/evaluation; N's three training charging
UAV-steps remain. Zero failures do not establish catastrophe prevention or
charging recovery.

After complete evidence reading, READY `053f99b959628ed7c3eede34` is consumed
with generation75/wake`a66ccde2-1f5b-4c21-830d-c6c14fe2ad29`, advancing to76.
Both original B05 workers are finished; no experiment, unconsumed event or old
Pro answer remains pending. No worker restart, repeat Send or App message occurs.


## Pro question 2026-09-23 b05-risk-service-next-intervention

Conversation: reuse the current Jev adviser conversation; its address remains
only in local operation state. The completed prior question is identified by
key `hmasd:9c663dfbd9d85af2ad743a57b23ff3bc2d7e48878eff62bd5252c071b8ece5c5`.
This is a new scientific question after a fully accepted new experiment, not a
retry, delivery repair or repetition of that accepted question.

**Question / impending choice.** B05重复了最终平均J/风险成本优势和开发终点损失，却没有
重复服务收益。当前固定系数4配方不再追加训练，也不升级为默认或确认。DM继续负责服务—风险
这个问题：**下一笔工作是否应先检验一个只用合法当前观察、按返航余量触发的简单执行反馈，
而不是再次改变整段训练的成本权重？** 请与最强的具体学习修订或有理由暂不新增实验比较，
选择最值得做的一个判别；不要把正最终均值当自动继续资格，也不要仅因两个区组便要求停掉
整个研究问题。这不是Portfolio、方向名额选择或请求owner逐项批准。

**Standing and changed evidence.** 请先读紧邻上方完整B05条目与全部40个端点世界表，
不是只看这里的均值。科学source3de3e3f71c747e2422656126b52ae88beafb562a，S7-S2/v3/reward-v2，
8UAV、30users、k10，30×1500×4=180k训练team transitions/臂，完整高低层与判别器学习。
N/R同实际初始化与首轮物理数据，唯一干预是训练中额外减2倍实际post-transition
`return_constraint_cost`，原生评价均系数2。R的真实buffer reward、两层GAE、实际优化器和
最终checkpoint均独立核验；不是失活机制或单纯固定策略。每臂180k train/96k eval，B05
实耗2fits、259.992391 runner min。原始二进制保留在条目指明的本地/节点；Git摘要和核验结果
不冒充你实际读取过二进制。四个endpoint格子必须分开：

| 区组/面板 | R−N J | R−N QoS | R−N capped cost |
| --- | ---: | ---: | ---: |
| B04 development30 | −218.433452 | −.091920514 | +.027256861 |
| B04 final32 | +549.393528 | +.108482684 | −.129009370 |
| B05 development30 | −37.659662 | −.117039433 | −.045606817 |
| B05 final32 | +241.885454 | −.026788931 | −.094165509 |

B05最终N/R的J−232.025030/+9.860423，QoS.216057847/.189268916，throughput
6.481735/5.678067Mbps；14胜18负，中位ΔJ−99.441797，最差−676.258092，最大+2042.732101。
R有13负J、8零QoS（N为14/1），其中6个J胜出世界仍零服务；但另6世界同时增服务降成本，
所以“全靠不服务”也过度。最终mean/P10/最差电池min提高，18world提高14降低；开发mean
电池min略降。开发R自身30−0 J+112.065545、QoS+.054655545，N相应+149.725207/+.171694978；
两臂有真实学习，不能用R的自身改善代替相对用途。R开发J20→30下降252.952693，不选较早
checkpoint。final没有初始化评价。两面板均已曝光，世界/时间/agent rows不增加独立训练n。

此前完整咨询已预写“最终正、开发负→有限面板用途，不支持一般默认”；我们据此保留观察而
不追加原样训练。这次新问题关注一个不同干预的投入价值，并非再次咨询该旧分支。B03的
服务/普通预测辅助在两块反号、共同MSE与用途相反的负证据也保留；没有新原因复活旧头。
原生N控制自身有实际服务学习，不能因为当前R较低绝对服务就废弃N为主控制。

**One concrete alternative to challenge, not an accepted experiment.** 当前policy合法观察
已经包含UAV电池、raw return margin/threshold、相对充电站位置；不是“缺一个风险标量”
的问题。native return cost是最差成员margin负部/.05并cap1，mean battery不是它的替代。
当前native motion law只有极低绝对电池的limp-home强制处理；请求dock在站点附近会改变动作。
可否用这些已开放的当前观察给两份原生N最终策略加一个事前固定、单一规则的margin-conditioned
返航反馈（含必要的确定性进入/退出约定），在未触发时原样执行，在触发时用已有station信息
调整该成员动作？比较每份相同N参数的原执行和反馈执行，仍按完整原生J/QoS/throughput/cost/
事件/真实battery尾部评价。不得读取未来、oracle rollout、其他策略隐藏状态或新的特权输入；
不得改physics、reward系数、终止、horizon或挑world；反馈也不自称安全保证。

这个候选的工作预测是：改变已实现的风险接近轨迹而无需把所有状态的学习目标统一增重，
有机会保留有用原生服务；最强反例是触发过晚/不可恢复、提前撤走关键relay、群体同时返航和
站点竞争，使成本不降或服务损失更大。只有运行真实的干预后轨迹才能读这些后果；对旧轨迹
换一个reward或挑零服务world不能检验它。现有保留数据没有逐成员ownership/动作影响诊断，
不能把共享cost归因缺陷、缺信息或不可逆风险当已证明的失败原因。

零交互的**事后描述**用六个250步bin检查final旧轨迹：B05 N/R cost为0/0、0/.000008349、
.052370/.002454、.212646/.046231、.325313/.140988、.494646/.330299；QoS为
.088980/.083865、.161533/.126308、.211554/.163596、.262310/.194234、.263353/.257090、
.308617/.310520。末bin cap饱和41.7375%/23.95%。这支持询问执行期条件动作，却不识别
延迟信用失败，也不证明feedback可恢复。你可以否定此候选，若别的实际学习修订更有信息价值，
请给一个有源码契约和不同预测支撑的具体选择；不泛列所有潜在解释或强制生成新模块。

**Prospective cost / exposure for advice, not a frozen launch.** 上述零更新候选可用全部两份
现存N最终策略（B04/B05，非挑最好），各比较两种执行规则，在全部旧8+32世界各一次：
2旧策略×2规则×40world×1500=**240k eval transitions upper bound、0新fits、0updates**，
原执行重现与干预都计成本。按B05 192k evaluation实际80.883842min粗参照，约101min evaluator
wall，主机并发等使未来时间未知；规则实现、合法信息检查、必要审阅与收取另计。旧学习是
已付成本，未形成新训练replicates；新反馈world也仅是开发条件下的执行证据。若更小固定设计
已能改变选择，请具体说明减少哪些工作而不选择有利旧实例；不能用“0fits”等同免费。
一个真正不同的完整学习比较若更合适，参考2臂×180k train、同原生评估预算、约260min
summed runner的量级，并说明为何其信息值得该额外成本。尚未决定阈值/公式、试验或任何新fit。
不得自动扫系数、第三对原样R/N、遍历规则、追加世界或确认；固定新协议由DM读完后另写。

**Context and source precedence.** Repository `CartmanFatass/My-paper-code`.
The actual send supplies full `source_sha`; references marked source_sha mean
that immutable question commit, not a moving branch.

- Current owner/governance at **2a736e873b72d7ca150668383d052e7ca7bb234d**:
  `docs/project/OPERATING_CONSTITUTION.md` §§1–5,7–8; and RESEARCH top owner/pause,
  own `uav_service_auxiliary` row, topic6. Owner resumed this DM, granted continued
  scientific autonomy after recipe failure and requested continuation; pause is
  lifted here, Claude FSD remains paused and G33 frozen. Advice does not change
  those states or require new owner/Root approval. This is one direction only.
- Current methods at that same published revision:
  `.agents/skills/hmasd-scientific-tools/SKILL.md`, Explore an idea, Update the
  working explanation, Comparators, Statistics and Cost and exposure. The new
  shared topic6 revision treats positive mean/tail savings and complete service
  failures together; it motivates comparison with a conditional intervention,
  not a claim that either risk weighting or risk feedback is generally useful.
- Primary local evidence at source_sha: this NOTES B05 complete entry and the
  earlier `2026-09-23 — B04 advice adopted; B05 fixed independent-training recurrence`
  entry including the immediately preceding full Pro Answer; B04 complete entry;
  `runs/uav_service_auxiliary/b05_n_914173_a01/summary.json` and corresponding R,
  and both B04 `b04_n_914021_a01` / `b04_r_914021_a01` summaries/configs.
  Check paired losses and absolute service, not only aggregate differences.
- Frozen numerical implementation at **3de3e3f71c747e2422656126b52ae88beafb562a**:
  `experiments/candidates/uav_service_auxiliary/b05/native.py` and reused
  `b04/native.py` (actual objective/storage/evaluation),
  `envs/pettingzoo/relay/energy_aware.py` methods `_energy_observation`,
  `_raw_return_energy_margins`, `_prepare_energy_actions`, `_is_uav_in_limp_home`,
  `_limp_home_velocity`, and reward construction around lines796–813. Read the
  matching B05 config for units and active settings. An approximate return-energy
  estimate, existing docking action and an actual hard feasibility guarantee are
  different things. If implementation facts differ, correct the premise.

The raw binary gap is explicit. Cite source passages actually used; do not claim
that a Git summary verifies raw trajectories you cannot read. No external paper
is required; use a verified primary passage only if an analogy changes the choice.

**Return.** 给出一个清晰的下一投入建议及最强替代，说明B05加强/削弱/未触及什么。重点判断
上述执行反馈是否现在值得做，若是，给最小但可执行的前瞻比较、合法信息/精确触发和退出语义、
中间与原生结果预测、反面结果怎样改变选择；不以观察到的收益反推阈值或任意服务容忍线。
若拒绝，说明缺哪一条可改变量/判别，选择一个更值得的明确学习比较或有证据的停止理由。
无需确认任何总体优势、创造固定数量候选或要求先做昂贵完整诊断。写明MATERIAL_DISSENT yes/no，
实质批评由DM回应，Pro不作批准或否决。

**Answer-only write constraint.** No training or repository changes except the
empty `### Answer` subsection of this question in
`docs/research/candidates/uav_service_auxiliary/NOTES.md`, branch
`codex/uav-service-predictive-control`. Read reasoning inputs at the pinned
source. For writing, fetch the latest target file and use its actual blob SHA;
preserve the question and every other byte, stopping on overlapping edits.
Return the actual commit on success. If GitHub writeback fails, return the
**complete substantive answer in chat**, not a SHA, receipt, link or promise.

### Answer

GitHub 读取可用，但当前可调用接口没有仓库文件写入动作，因此未写回；实际 Answer commit：无。 最后读取的目标 blob 为 28644de509bec265811d2f000a152febf6b5cd18，本次指定问题下的 ### Answer 仍为空。本轮没有修改仓库或启动实验。以下为完整答复。

B05 后续：先检验逐成员的返航余量反馈，不继续增加整段训练的风险权重

MATERIAL_DISSENT: no。

我支持先做一次固定的、零更新的执行反馈比较：保留 B04、B05 两份原生 N 最终策略，各比较原执行 O 与下文定义的余量恢复反馈 F，在全部既有 8＋32 世界上运行完整 episode。总量上限为 240k 评价 transitions、0 新 fits、0 optimizer updates。

我建议的 F 是逐成员、带滞回、朝最近充电站恢复返航余量的反馈，不是“触发后必须返站充满电”，也不是安全保证。具体采用 raw margin ≤0 进入、恢复至 ≥0.05 退出；其余情况下保留上一反馈状态。两个阈值的来源和动作公式见第三节。这是我提出的待固定协议，不是已实现或已验证有效的控制器。

此次不同时选择第三对原样 N/R、系数搜索、分项 critic、新辅助头或更大世界面板。最强的学习替代是保持原生系数 2 的成本／其余回报分解 critic，但当前证据对其估计瓶颈的支持弱于对这次直接执行比较的信息价值，故不优先购买。

一、B05 重复了什么，又明确没有重复什么

四个终点格子应继续分开。J 是完整 episode 的原始原生回报，QoS 和成本为每步均值；下表均为 R−N。

训练区组／面板	原生 J 差	QoS 差	封顶返航成本差
B04，development30	−218.433452	−0.091920514	+0.027256861
B04，final32	+549.393528	+0.108482684	−0.129009370
B05，development30	−37.659662	−0.117039433	−0.045606817
B05，final32	+241.885454	−0.026788931	−0.094165509

被加强的是条件性的原生风险节省用途，而不是一般的服务—风险共同改善。 B05 最终 N/R 原生 J 为 −232.025030／+9.860423，真实封顶成本从 0.180828987 降到 0.086663479，未封顶成本也下降。其回报差可算术分解为服务项 −40.183396、原生 −2×成本项 +282.496526、PBRS −0.427676。这是真正按原目标得到的净收益，不能因服务下降就抹掉；但它没有重复 B04 的服务增量，也不能把三个账面分量称为独立因果份额。

服务损失和世界间异质性直接限制继续投入的理由。 B05 最终只有 14 胜、18 负，中位差 −99.441797；R 的八个零服务世界多于 N 的一个，且六个 J 胜出世界仍然没有服务。全部 40 个端点世界表里，至少有三类不能混为一谈的事实：

938023：N/R 的 J 从 −1565.750359 到 −15.063101，成本从约 0.523557 到 0，QoS 却从约 0.012033 到 0。这里保留了很大的原生损失削减，但没有形成服务。

938005：J 改善 +2042.732101，同时 QoS 从约 0.037220 到 0.174528、成本从约 0.612961 到 0。因此“所有收益都来自放弃服务”同样不符合证据。

937005：开发世界的 QoS 从约 0.281843 到 0，两臂成本都为 0，J 损失 −419.076393。它尤其反对把每个服务损失都描述为该世界上必要的风险交换。它仍不单独识别训练中的哪条路径造成了损失。

这些观察与原生 N 自身有用学习并不矛盾。B05 开发面板上，N、R 从初始化到终点的 J 都提高，但 N 的增量和服务增量更大；R 的 update20→30 J 又下降 252.952693。自身学习、相对用途、时间退化和同一终点的面板差异需要分别读取。最终 32 世界没有初始化评价，不能补写其自身学习增量。

执行有效性不再是主要未决问题。两臂 summary 记录了每臂 180k 训练 transitions、30 rollouts、120 episodes、96k 评价 transitions，以及真实原生优化器更新；B05 的入口明确使用新 seed，并复用同一风险奖励存储路径。DM 的进一步数组、GAE 和 checkpoint 核验支持这是活跃的训练干预，而非未接通的损失。这些二进制核验属于 DM 的报告，不是本次由我重新完成的审计。

因此，当前更新应是：

加强“同一最终面板上的原生平均 J／风险成本增量不只出现在首个训练实例”；削弱“系数 4 能一般地保住服务并改善净用途”；未触及或未识别共享成本的成员信用问题、critic 是否错误估计风险、风险状态是否可恢复、以及具体中继撤离造成的后果。B03 的辅助预测反号和 MSE／用途不一致仍然约束解释，不能借 B05 的正均值重开旧头。指定版本的共享 topic6 已把这些正负证据放在一起，我据此保留 N 为主控制，并要求新干预直接测量服务后果，而不是再次依赖预测误差或电量均值。

二、为什么这次优先选择执行反馈

这次零更新候选与上一问未选中的“给旧策略再加 64 个世界”不同。它改变实际提交的动作，因而产生新的联合轨迹；不是仅提高旧两个 checkpoint 排名的评价精度。

它购买的判断是：

对两份已经学到原生服务的 N 策略，当某个成员的当前返航余量到达风险边界时，加入一个固定、合法、可执行的返航方向反馈，能否减少后续真实风险成本，同时保住值得保留的服务和完整原生 J？

这个问题目前有三个具体支点：风险变量已经进入合法观察；动作接口已经允许移动和请求 docking；原生强制 limp-home 使用的是极低绝对电量条件，并不等同于 raw return margin 触发。它不要求先把“缺信息”“信用失败”或“风险不可逆”诊断成事实。

事后六个时间 bin 只提供选题动机。B05 的大量记录成本出现在后段，服务差异却在显著成本出现前已经存在。这使“只在实际访问到的风险边界改变执行”成为一个有区别的干预，而不是证明条件反馈一定能修好学习。不能把这些 bin 变成“第 500 步后才启用反馈”的规则，也不能把后段成本集中称作延迟信用缺陷。

最强的反对理由

简单返航可能恰好把有用的关键中继撤走，而风险指标降低不足以抵偿其服务损失。 多个成员可能同时触发，集中到同一站；固定策略还会在干预后的新观察和历史上产生不同后续行为。即使反馈未触发时不覆盖命令，也没有“未触发阶段服务不受影响”的保证。

更根本地，raw margin 是基于距离和指定返航速度的能源估计，而不是硬可行域。以它触发返航，可能主要改善原生任务中的几何风险罚分，而非解决实际即将耗尽的危机。当前零评价 cutoff／depletion 不能帮助我们验证灾难预防。这个限制必须保留；它不是取消原生成本的理由，也不是宣称反馈安全的依据。

我仍选择这项比较，因为它能用明确的动作干预区分“存在可用的当前反馈机会”和“这样的撤回破坏服务或不能缓解风险”，其新增交互少于完整重训，且不需要先假定一个尚未被数据定位的学习缺陷。

最强的具体学习替代，以及为什么暂不选

我认为更有针对性的学习替代是：保留原生系数 2、actor 信息和高层原生学习，只把低层 critic 的标量估计改为成本／其余回报两个读出。

设实际低层混合奖励为 r
low,t
	​

，成本仍用原生封顶 c
t
	​

，则可以定义

r
rest,t
	​

=r
low,t
	​

+2c
t
	​

,V
low
	​

=V
rest
	​

−2V
c
	​

.

使用同一实际数据、终止 mask、折扣和回报语义训练两个读出，在原始单位合成 value 后进入原有 GAE／PPO，而不是将两份各自归一化的 advantage 直接相减。当前 runner 已有实际成本和奖励存储路径，因此标签来源明确；但双读出及其归一化、损失和回放接线尚未实现或验收。它仍会改变 critic 的拟合几何，不能称作一个完全不改变学习过程的“等价修复”。

它的不同预测是：对风险后果的估计改善，能在真正进入高风险状态前改变学得的动作，并在原目标下保住服务。**B05 没有提供“该 critic 估计错误是当前关键瓶颈”的证据。**仅凭后段成本或整体 R 的服务损失，不足以优先支付另一对完整训练及新增 critic 接线的成本。即使未来成本预测误差下降，B03 已表明仍须以原生用途判断。

暂不新增实验也是有力替代，尤其当任何反馈结果都不会改变使用或后续研究选择时。但当前存在合法变量、明确执行作用点和可区分的完整后果，我不认为“已有两个训练区组”本身足以否决这一不同问题。本次只选择反馈比较；学习替代不是反馈阴性后自动启动的下一格。

三、建议固定的 F：风险边界进入、一个成本尺度的滞回退出
1. 合法输入及必须纠正的混用

记成员 i 当前合法观察中的 raw return margin 为 m
i
	​

(t)。冻结实现中，它对应：

m
i
	​

=b
i
	​

−
3600C
battery
	​

P(v
limp
	​

,0)d
i
	​

/v
limp
	​

	​

−r
reserve
	​

,

其中 d
i
	​

 是到最近充电站的三维距离。当前配置中 v
limp
	​

=3 m/s、C
battery
	​

=160 Wh、reserve 为 0.1。_update_return_energy_state 将 raw margin 原值放入观察，同时把另一个 return threshold 截断到 [0.25,0.6]。因此，battery <= clipped_threshold 并不处处等价于 raw_margin <= 0，反馈不能将这两个判据互换。

F 只读取该成员现有的 actor 合法 observation，以及冻结任务配置中的常数。成员记录按 _energy_observation 的固定 UAV 索引排列，不是按距离重排的邻居槽；应沿既有 agent 到行的映射读取自身记录，不能用“相对位置恰为零”猜测身份。站点选择只使用该观察已有的相对位置和有效标志。相对坐标必须按原 area_size、高度跨度还原后再计算物理距离，不能直接比较不同量纲归一化坐标的欧氏范数。

不向 F 提供 critic 全局状态、环境私有数组、未来成本、另一个策略的隐藏状态或任何 oracle 分支。当前观察归一化关闭的事实也不能被实现者借机改成新的在线统计。合法输入未增加，但固定规则加入了手工构造的控制先验和一个模式位；不能把它描述为免费获得了新信息。

2. 精确进入、保持和退出

每个成员维护一个布尔模式 z
i
	​

，只记录本规则是否仍在执行余量恢复。每个真实 episode reset 时置 0；每个 primitive step，在当前观察到达后、动作提交前更新一次：

z
i
	​

(t)=
⎩
⎨
⎧
	​

1,
0,
z
i
	​

(t−1),
	​

m
i
	​

(t)≤0,
m
i
	​

(t)≥0.05,
0<m
i
	​

(t)<0.05.
	​


边界按上述含等号约定执行；初始观察也参与判定，不人为延迟到第二步。不等待 k=10 的技能重选点，不新增 episode 时间门槛。

**0 来自原生成本开始出现的余量边界；0.05 来自现有成本的 margin scale，用作固定滞回宽度。**把它作为正侧退出余量是我提出的工程选择，不是环境已经规定的最优控制阈值，更不是由 B04/B05 的分数反算出来的参数。它表示额外恢复 5 个百分点的容量比例余量，不能与“绝对电池降到 5% 才 limp-home”混同。该规则未测试前，不增加第二套阈值候选。原生成本确实由最差成员负 margin／0.05 再封顶构成。

选择 0 而不是一个拟合出来的提前量，是为了先检验已经到达声明风险边界时的直接反馈机会。margin 为 0 仍包含原来的 reserve 扣除，并不等于实际电池为零；但估计误差、离散步长和后续竞争仍可能使它过晚。若结果显示过晚，不能在同批把阈值提前后重新挑一个阳性。

退出只要求当前 m
i
	​

≥0.05。**不额外要求到站、充至 75% 或充满电。**它是有限撤回／余量恢复反馈，而不是完整返站充电日程；后者会引入另一种驻留和服务代价，不能在实现时悄悄替换。

3. 精确动作：只通过原四维接口执行

先让原 N 策略正常计算所有成员当前的四维命令 a
i
N
	​

。F 在同一份当前观察上合成提交命令，不按成员逐个推进环境。

当 z
i
	​

=0 时，四个分量原样传递，不另做裁剪、重采样或 docking 清零。原环境仍按其既有方式处理它。

当 z
i
	​

=1 时，从合法观察选三维距离最近的有效充电站；观察数值完全相等时选较小站点索引。每步重新选择最近站，不新增预约、站点分配或群体返航排序。令还原到米的相对向量为 r=(r
x
	​

,r
y
	​

,r
z
	​

)，距离 d=∥r∥。

在 d>160 m 时，采用一个不搜索参数的直线导航命令：

T=max(Δt,
30
∥r
xy
	​

∥
	​

,
5
∣r
z
	​

∣
	​

),v=
T
r
	​

,
a
i
F
	​

=(
30
v
x
	​

	​

,
30
v
y
	​

	​

,
5
v
z
	​

	​

,1).

这里 Δt=1 s，30 m/s 和 5 m/s 分别是现有水平和垂直速度限值；T 只是当前几何的动作缩放，不是预测 rollout。这个选择不声称能耗最优。

在 d≤160 m 时，提交 (0,0,0,1)，让原生 energy wrapper 实施其已有 docking 动作；在原生 capture 半径内，它会进一步停止运动并按现有资格／容量规则处理充电。**不直接调用会读取环境私有状态的 _limp_home_velocity 来替代观察解码，也不绕过 energy wrapper 写位置。**普通外部动作的垂直分量须除以 5，而不是照内部基底三维动作的转换统一除以 30。

这里有一个会影响科学解释的重要细节：第四维取 1 不仅请求 docking。冻结实现还允许有效返航请求、朝站点运动时通过相应的 backhaul action guard 分支。**这也是 F 干预包的一部分。**不能一面使用这个作用，一面声称比较只改变了一个无关紧要的速度分量。原有 clipping、位置限制、极低电量 limp-home、失效／耗尽处理及充电容量规则全部保留。

若固定配置的站点记录无法合法解析，应保留为技术无效，不能读取私有坐标补齐或静默丢弃世界。若原生物理处理使提交命令没有产生运动，则如实记录；合法的物理阻断不是靠强制移动来“修复”的实现问题。

4. 保留原策略的真实反馈历史

原 actor、技能调度与循环状态继续在F 实际产生的观察轨迹上运行。不开影子环境，不沿用 O 的后续动作，不在反馈开始／退出时清空 GRU，也不暂停或重置 k 时钟。只有原生 episode reset 重置其原有状态，同时重置 F 的模式位。

因此，“未触发时原样执行”的精确含义是：**当下不覆盖该 actor 基于当下真实历史提出的命令。**第一次真正干预之后，即使某成员暂时退出 F，其观察、循环状态和命令也可能已经不同于 O。只有第一次实际覆盖之前的共同前缀，才应按匹配设计重现。这个区别决定了本比较为什么必须运行完整的新轨迹，而不能在旧轨迹上替换奖励或拼接动作。

四、最小完整比较：保留两份 N、两个面板和原执行重现

使用全部两份 N 的 update-30 终点，不根据 B04/B05 哪一份更强再选择：

保留的训练制品	原执行 O	同参数＋反馈 F
B04 N，seed 914021	937001–937008；938001–938032	相同两套世界
B05 N，seed 914173	937001–937008；938001–938032	相同两套世界

两份 N 的终点参数指纹分别以 3fee4d9c…、22ade2e3… 开头，应按保留的完整 checkpoint／summary 绑定，而不是重新初始化一个“同 seed”模型。原生 N 已付的训练成本仍属于这些制品的历史成本。此次 0 新训练不等于从未训练的控制器，也不产生新的学习复制。

我保留完整 240k 上限，而不是删去开发八世界或其中一个训练制品。删开发面板会删掉已经两次出现的相反用途；删一个制品会使结果更依赖一次已选学习轨迹。更便宜的工作可以只测试接线，却不能同样回答当前的服务保留问题。原执行重现就是 O 这部分评价，不在它之外再附加一轮完整重复。

每次从对应 checkpoint 和原生 reset 开始；O/F 使用相同世界与该制品原有的评价随机性绑定。保持 S7-S2、N8、k10、1500-step horizon、原生系数 2、确定性策略执行和全部原 reward 分量。禁止训练存储／optimizer 更新，也不更新 normalizer。新产生的早终 episode 按真实长度和完整回报保留，不补零、不剔除、不人为强撑至 1500。冻结 evaluator 的原生奖励核对、完整回报、真正 episode minimum battery 和零更新语义可复用，但它当前没有 F 的命令变换及逐成员诊断接线，需要一个窄的后继实现。

对制品 b、面板 p 分别报告：

D
b,p
J
	​

=
∣W
p
	​

∣
1
	​

w∈W
p
	​

∑
	​

[J(N
b
	​

+F,w)−J(N
b
	​

+O,w)].

同样报告 QoS、交付吞吐、封顶／未封顶成本、真实 episode 最低电量与尾部差异。**final32 是各制品的主要用途面板，开发八世界约束其范围；四个反馈效应格子不能用一个池化均值替代。**这些世界均已曝光，不是新 held-out 确认；两个旧训练制品也不是两个新训练处理重复。配对世界可以描述这些固定策略的条件差异，不能生成学习方法总体可靠性。

每个世界保留绝对 J／服务、相对差、中位数、胜负计数和不利尾部，另列相对 O 新增、消除和保留的零服务 episode。原生 J 中的风险节省仍是正当收益，但“J 赢而无服务”必须有单独可见的位置。固定需求下吞吐与 QoS 的倍数关系不增加独立正证据；最低电量也不能替代位置相关返航成本。新比较可能实际激活充电或其他事件，不能预设它仍为零。

五、中间预测与真正有用的诊断

中间预测是：F 在真实风险边界产生可观察的动作覆盖，改变实际路径，使负 margin 的持续程度、未封顶缺口或成本饱和暴露下降。原生预测是：这些变化能在完整 episode 中形成更高 J，同时避免再次以明显服务退化和新增零服务世界换取平均风险节省。前者发生而后者失败，仍是这个候选用途未兑现。

诊断只需覆盖这条链，不需要另开完整归因研究。保留各成员的当前 margin／电量、模式进入退出、所选站点、原命令和实际提交命令；记录覆盖次数、持续时间、同时覆盖人数，以及实际运动或未运动。再与后续真实成本、服务、充电／排队和终止相连。不要仅凭“模式位变为 1”就宣称控制已生效，也不要把被触发成员直接称为团队服务损失的因果责任者。

从现有 margin 定义可直接看出：

Δm
i
	​

=Δb
i
	​

−κΔd
i
	​

,

其中 κ 来自原来的返航能耗估计。朝站点移动减少距离，但同时消耗电量；到站、等待和充电又产生不同后果。**方向指向站点并不在逻辑上保证 margin 立即改善，更不保证团队服务改善。**所以应读取实际后果，而不是将动作方向当作风险减少的替代品。

既有六个 250-step bin 可作为预先保留的描述面板继续使用，但不是新的主终点。不能只挑触发后“恢复成功”的片段计算服务；触发会依赖策略自身访问，条件片段之间也不是随机对照。所有世界、未触发轨迹、未恢复的持续覆盖和提前结束都进入完整读数。

必要的正确性检查围绕这次真实变化：合法字段／成员映射、阈值等号与滞回、坐标反归一化和垂直动作尺度、reset、不改变随机流、O 重现、F 的真实命令覆盖以及零学习更新。它们不要求一个正面 pilot，也不增加第二套试验规则。原执行到首次覆盖前的共同前缀是实现检查；科学信息来自覆盖之后的完整联合后果，不能把前缀一致本身算作性能证据。

六、哪些结果应结束或改变这一规则的投入
固定比较的结果	判断与投入变化
两份 N 上均有可保留的 J／风险改善，服务得到保留或改善；开发面板不出现实质相反用途	加强这一个反馈包在这些制品和世界上的用途理由。保留全部不利世界与成本，不能升级为安全保证、一般最优规则或新学习成果，也不自动重训或确认。
成本下降、J 上升，但主要伴随明显服务损失或新增零服务 episode	保留原生风险节省的真实价值；不称为本次所寻求的服务兼容改善。若只是重现 B05 式的服务—风险交换，默认不为这一固定规则继续投入。
动作和实际轨迹已改变，但成本不降，或服务损失使原生 J 更差	降低当前反馈设计的用途判断，结束本规则的追加。可能涉及时机、导航能耗、关键中继或竞争，但不能凭一个负结果任选一种解释，再自动提前阈值、改速度或增加协调模块。
一份制品／一个面板有利，另一份明显不利	保留有范围的观察，不挑“适合反馈”的旧策略或 seed，也不由这些开发分数构造部署选择器。按当前通用用途目标，不自动追加制品、世界或规则。
没有实际动作干预，或实现未兑现合法输入／执行合同	前者没有检验到足够的新增反馈作用，应解释真实未激活原因；后者是技术无效，保留成本和输出。二者均不能冒充“有效反馈有害”或“已经解决风险”。

我把“成本下降、J 增加、服务不下降”作为最有力的联合保留模式，而不是结果出来后才决定服务是否重要；但它不是以任意微小正负小数自动裁决的认证标准。材料没有提供经过验证的服务容忍区间或尾部合格线，我不从旧效果大小反推一个。应公开幅度、零服务变化和最差损失，让有限收益与其代价保持可见。

同样，不要求每个世界都改善，也不能因为均值正就略去重大相反后果。一个规则可以留下有用的条件性观察，却仍不值得继续支付成本。**成功没有自动训练后继，失败也没有自动规则搜索后继。**较早介入、驻留充电或分配站点都会是新的科学干预，须有来自实际结果的不同预测，而不是当前候选的默认补丁。

七、成本、范围与最后选择

完整设计为：

2 个旧 N 制品×2 种执行×40 世界×1500=240,000

团队评价 transitions 上限，共 160 个完整 episode 尝试；0 新 fits、0 optimizer updates。其中 O 和 F 各占 120k 上限。它不是 240k 个独立样本，也不是额外训练曝光。

hmasd-pro-question-usa-b05-next…

B05 的 192k 评价实测 80.883842 分钟，按交互量比例换算约为 101.1 分钟，只能作为历史成本尺度；未来节点并发、制品加载、反馈及记录开销均未测得。B05 的 259.992391 分钟完整 runner 成本也不是新双读出 critic 的成本保证。实现、合法信息检查、必要审阅、收取、存储和完整判读另外计入；不通过省略原执行或失败世界来宣称便宜。

来源范围如下：本次读取了 f5b078557b2f438300af1a3e58dbbe84d2f2c5c6 的新问题、完整 B05 结果及全部 40 个端点世界表、B04 完整条目，以及上一轮完整 Pro Answer 和 B05 采纳／前瞻条目。核对了 B05 两份 summary 的计数、终点聚合、参数／优化器记录和成本，并读取相关配置参数；B04 的 summary/config 当前 blob 与前次实际读取的文件一致，本次也重新核对其终点字段。这里没有将 summary 的局部核对描述为对所有原始训练数据的再次逐字节审计。

治理、方法和当前背景按 2a736e873b72d7ca150668383d052e7ca7bb234d 读取；数值／动作契约按 3de3e3f71c747e2422656126b52ae88beafb562a 的 B05 入口、复用的 B04 存储／评价以及 energy observation、margin、docking 和 guard 路径读取。**没有发现阻止上述事前比较的关键文字来源缺口；但没有取得并独立复核仓库外 NPZ/checkpoint，也没有 F 的实现、实际干预结果或可恢复性证据。**这些未决内容限制有效性和安全性断言，不需要以外部论文或聊天记忆补全。

**最终选择：只购买一次 O/F 完整执行比较，用原生 N 已有的服务能力检验一个精确定义的余量恢复反馈。**它值得做，是因为现在有合法可用的信息、实际可改的动作和会改变下一步判断的反面分支；不是因为 B05 的平均 J 再次为正，也不是因为必须延长研究链条。若这条规则仍主要制造服务空窗，或不能把实际风险变化转成值得保留的原生用途，就结束这条规则的追加投入，保留已获得的认识，不自动再改阈值、权重或网络。


## 2026-09-23 — B05 advice adopted; B06 fixed observation-only return feedback

**Full advice and delivery.** The exact new-key chat answer above was read in
full and saved from chat after same-key `deliver` returned **NOT_DELIVERED**,
with no answer commit. The quoted28644de509bec265811d2f000a152febf6b5cd18 is
verified as the unchanged target **blob**, not a commit. Source/question and
empty Answer agreed byte-for-byte with current remote before insertion.
Collected body has10778 characters and SHA256
`796eca63736062e2447d3c84d10f5f065c39ca0a09879395a6e7b5f3c698f14a`;
the driver's saved text adds its documented trailing newline (10779 characters,
25253 UTF-8 bytes), SHA256
`d6072a8916aa53c9f45b6643ba0a89bf9fce52490b58ea98931d050c49024778`.
This transport distinction is resolved; no repeat question or pending delivery.
READY9cbc1d2080ed5ff45c63f0f7 was read and consumed with generation77 /
wake528c1230-5f72-45ac-9c08-9818e361717c, advancing to78.

**Judgment and source checks.** Adopt the single O/F zero-update comparison,
including its adverse branches, complete panels and cost. Pro's `MATERIAL_DISSENT:
no` is advice, not scientific acceptance. Its scope statement distinguishes
repository-reading and our reported binary audit; no recommendation is attributed
to independent access to NPZ/checkpoints. Existing B05 interpretation is unchanged:
repeated final cost/J gains coexist with development losses and unreplicated
service gains. Current fixed coefficient4 training does not continue. This new
intervention buys actual modified joint trajectories, not another ranking of
old checkpoints on added worlds. It neither selects confirmation nor automatically
queues a new learning comparison after success/failure.

I checked consequential implementation claims in the retained3de environment:
actor energy records contain raw margin at own indexed UAV record (13 fields),
station records have8 fields including valid flag; the365-dimensional observation
has a120-field energy suffix under this configuration (8 UAV records,2 stations).
Own identity is the native array-agent index, not a zero-relative-position guess.
`_raw_return_energy_margins` subtracts a nearest-station 3D-distance estimate at
limp speed3m/s and reserve.1 from battery ratio; `_update_return_energy_state`
separately clips the threshold to[.25,.6]. The raw margin criterion is not
interchangeable with that clipped threshold or absolute battery.05 limp-home.
Observation normalization is disabled in the inherited native configuration;
no new normalizer or additional actor information is introduced.

The four-dimensional action maps horizontal norm to at most30m/s and vertical
coordinate to5m/s. Dock requests above.5 populate a station target; within160m
the native wrapper chooses docking movement, within20m capture it stops and
applies unchanged physical/charging eligibility. An explicit request moving
toward its target also follows the existing backhaul guard exception. I accept
that this is part of the **feedback package**, not pure velocity causality.
Feedback code must use only legal observations and fixed task constants; telemetry
may inspect native realized physics after the decision, never feed it into F.
Source-level claims were checked directly, not inferred from Pro agreement.

The stronger alternative, separate cost/rest critic with native coefficient2,
is not selected: no current evidence identifies critic estimation as the useful
bottleneck, and it costs a new full learning comparison plus value/GAE wiring.
The 250-step cost descriptions motivate a distinct feedback question but do not
prove delayed-credit failure, recoverability or justify a time-based trigger.
Simple feedback might remove critical relays or concentrate returns at a station;
its real adverse consequences can change the next investment. Current published
main **76b5a7c4eaaee5d5cbc1e033c315a65765f45204** keeps our lead and lifted pause;
its relevant topic6 retains the B05 service/cost limitation published at2a736e873.
That limitation selects full service/zero-service readings alongside cost, and
keeps both old N instances and both panels instead of selecting a favorable cell.

**Prospective B06, fixed before new evaluation.** Load the complete final N
checkpoints from B04 seed914021 and B05 seed914173. For each compare original
execution **O** and observation-only margin feedback **F**, with identical frozen
parameters. Every cell evaluates development worlds937001–937008 and final
worlds938001–938032, once at their original1500-step horizon. Use original policy
seed per block, deterministic CUDA FP32/TF32-off evaluation and4 Torch threads,
on configured4070 after native admission. Source inputs, config, summary,
checkpoint and both old endpoint trajectory files must match their recorded
SHA256s; original O is rerun and compared directly with the retained arrays.
No R checkpoint, new world, chosen old best policy or checkpoint is added.

Bindings (summary then checkpoint; their summaries retain config/trace digests):

- B04 N: summary`ab814a3e1d1861bcc8413c15c828dd39ed25c55106b1a71a6dc76a267f7bff78`;
  checkpoint`403908c044ee1c1952e36102959fbe53ab365d4845bacb17acbb7953d1a5def6`;
  trained at`914fc484368cc6c41af211b169c45b02e4a10425`, final policy
  `3fee4d9c751aac8dd3c0b5d84839624da63ca22a93f05f744647b1dc8f111408`.
- B05 N: summary`1af4318fdd21d5723054b12d8b89f99688d32190b4d89933074ce2913d9e12c9`;
  checkpoint`1a6a2b6c191d3dc74ac244b474dc6071905c71d6a973eea78a97e94e6fbcceb8`;
  trained at`3de3e3f71c747e2422656126b52ae88beafb562a`, final policy
  `22ade2e3aa948330acb4916445277edab0611a5159a1bef7beade8d1aefadc79`.

All S7-S2/v3/reward-v2/arm-C physics,8UAV/30users,k10, original reward coefficient2,
observations, native high/low policies, discriminator state, normalizers and
termination/truncation remain as bound. Every cell starts from its checkpoint and
native reset. Reuse the evaluator's actual policy calls; no optimizer, training
storage or statistics update. Agent recurrent state and skill clock continue on
F's actual new observations, with native reset only at episode reset. Do not
pause the policy, copy O's later actions, use a shadow environment or reset GRU
at feedback entry/exit. All actual early ends remain with their lengths and raw
returns; no padding, dropping, time rescue or new failure assumption.

**Exact F rule.** The feedback state is one bool per UAV, initiallyfalse at each
real reset. On every primitive step, including the first observation, before
submitting the simultaneously computed team command, use that member's current
legal raw margin m: if m<=0 enter; if m>=.05 exit; otherwise retain the previous
mode. Equalities follow those conditions; no k-clock wait or extra time trigger.
0 is the native risk boundary; positive.05 is one existing margin scale used as
a fixed engineering hysteresis width, not an optimal threshold or fitted score.
No second threshold or alternate navigation rule is in this study.

Inactive F passes all four current policy command components unchanged. Active
F decodes all valid station relative vectors from that member's observation,
rescales xy by8000m and z by150m, and selects minimum physical3D distance with
lowest station index on exact ties; nearest station is recomputed each step.
For vector r and d=norm(r), if d>160m use
`T=max(1, norm(r_xy)/30, abs(r_z)/5)`, `v=r/T`, and submit
`(v_x/30,v_y/30,v_z/5,1)` as float32. If d<=160m submit`(0,0,0,1)` and let the
original wrapper apply docking/capture. Do not call private navigation methods,
write positions or override native clipping, failure, depletion, guard or charging
capacity. Invalid legal fields/absent valid stations are a technical failure,
not permission to read private state or silently skip a world. This is margin
recovery, not a requirement to reach a station or recharge to a new level.

“Unchanged while inactive” means the command of the original actor on F's actual
current history is passed through. After an earlier intervention, that history
and command can differ from O even when F is now inactive. Only the common prefix
before the first actual command change should reproduce O; continuing equivalence
is not claimed. Present distance and battery do not guarantee that the proposed
move improves margin (energy is spent), let alone preserves relay service.

**Readout and prospective branches.** Each block's final32 mean raw original J
F−O is the primary use reading; its development8 mean restricts scope. Keep all
four block×panel effects separately, absolute QoS/throughput, capped/uncapped
return cost, events, actual episode minimum battery/P10/worst, every loss world,
median/amplitudes and zero-service episodes newly created/removed/retained.
Six fixed250-step descriptive bins are secondary, never another endpoint.
Episode/world observations do not create new independent training replication.

Intermediate prediction: legal F triggers real command and physical-path changes,
reducing negative-margin duration, uncapped deficits or cost saturation. Native
prediction: risk changes yield worthwhile original J while preserving useful
service, rather than creating another B05-like mean gain with more service gaps.
Keep raw per-member legal pre/post margin and battery, mode/entry/exit, station
choice/distance, original/submitted actions, realized displacement, charging and
queue information. Record override time, duration and simultaneous counts. Logging
physics is measurement only, separated from pure observation-to-command code.
A mode bit alone is not proof of effective action; realized blocking is retained.
Do not condition the scientific comparison on successful recovery or active worlds.

- Two artifacts show useful final J/risk gains with compatible service and no
  material contrary development use: retain this finite feedback package; no
  safety guarantee, new learning claim, automatic training or confirmation.
- Cost/J improve mainly with service loss or new zero-service worlds: retain
  risk savings but do not count service-compatible use as fulfilled; default end
  additional investment in this fixed rule.
- Real action/path change but no cost improvement or worse J from lost service:
  lower this rule's value and end further investment. No automatic timing, speed,
  station-coordination or neural repair after seeing its outcome.
- One artifact/panel helps and another is materially adverse: bounded observation,
  no choice of favorable old policy/worlds or automatic extra panels/rules.
- No actual intervention is nonactivation, not proof active F harms or succeeds;
  information/execution contract failure is technical invalidity with cost and
  artifacts retained. Reconcile accepted operations; never blindly restart.

No invented tiny-positive pass rule, service tolerance or tail safety threshold.
Read actual magnitudes and contrary outcomes. New learning, earlier activation,
station assignment or dwell/charging changes would require a new justified idea;
none is a default successor to this batch.

**Cost and L0.** One fixed execution batch, **0 new fits / 0 optimizer updates /
160 episode attempts /240k evaluation team transitions upper bound** (O120k,
F120k),1.92M agent-step observations upper bound. Two historical N trainings are
sunk artifact costs, not new replications. B05's80.883842min/192k eval gives a
rough **101.1min** evaluation reference, not a deadline; node load and new telemetry
may change wall. Count actual wall/CPU/RSS/output bytes and true ended lengths.
Implementation, necessary checks/review, collection and reading are extra work.
No extra full reproduction panel beyond the O arm is planned.

Deliverable: disposable `experiments/candidates/uav_service_auxiliary/b06/feedback.py`
(pure legal decoder/mode/action function) and `b06/native.py` (fixed source binding,
O/F evaluator, traces/diagnostics, native accounting, zero-update and reproduction
checks), guarded `scripts/run_uav_service_auxiliary_b06.py`, and focused tests in
`tests/experiments/candidates/uav_service_auxiliary/b06/`. Reuse B04 metric units,
aggregation and existing native construction/checkpoint helpers without changing
frozen/shared environment, learner or evaluator code. CLI accepts only the two
source roots, fixed CUDA/four-thread production contract, launch SHA and new out.
A private small fixture spec may support correctness checks; production cannot
use it or vary source/seeds/worlds/rule/horizon.

Check observation decoding against native fields, own-index identity, station
validity and tie handling, threshold equalities/hysteresis/reset, physical coordinate
and vertical scaling, original command pass-through, actual wrapper motion/docking
including native blockers, RNG/recurrent/skill continuity, actual checkpoint and
normalizer immutability, zero updates, early terminal retention, strict input-digest
and native-admission/SHA refusal, and original O trajectory reproduction. Tests
own scratch under the configured pytest lifecycle. Actual CUDA path validation
precedes the result entry. The registered Implementer may own only those new
code/test paths; no NOTES, shared source, scientific choice, result launch or
subdelegation. An independent registered Reviewer checks changed scientific/input/
RNG semantics before DM acceptance. DM owns interpretation, source publication,
actual-node admission and full collection. Stop dependent work for an actual
semantic/input/admission failure; report it, do not broaden the study.

## 2026-09-23 — B06 implementation accepted for actual-node validation

The registered Implementer returned the five new paths fixed in the B06 L0;
no shared/frozen learner, environment or previous evaluator changed. I read the
rule, source restoration, evaluation and failure paths and accepted the bounded
diff after independent registered Reviewer inspection. This accepts engineering
for further checks, not a scientific result or a result launch.

Two concrete defects were resolved before execution. A freshly constructed
config had the current checkout's unused absolute baseline-metrics path rather
than the historical source path. Both real retained inputs now pass verification:
the exact saved checkpoint config is restored, its materialized active fields
must match digest-bound config.json, and only the known path difference against
a freshly reconstructed config is allowed while both recorded consumers are
disabled. Other configuration differences refuse. No scientific field or old
checkpoint is edited. Independent review also found that nullable first-entry
and override times could crash a panel containing both activating and nonactivating
worlds. These are now conditional timing diagnostics with explicit observed-world
counts; all worlds remain in the primary outcome means. Both orderings are tested.

O reproduces retained common arrays immediately before its dependent F panel.
Legal pre/post observation fields and higher-precision physical telemetry are
separately labeled. Returned transitions and attempted episodes are counted before
subsequent telemetry validation; completed worlds and a failing world's partial
trace remain recoverable. Mode intervals, actual commands and realized displacement
are recorded separately. These changes preserve the fixed study and its adverse
branches; no new arm, world, threshold or optimizer update is introduced.

Implementer CPU checks: **11 passed, 2 CUDA cases skipped**,4.50s. The short O
path compares against the unchanged B04 evaluator's raw arrays, rather than a
second candidate implementation; it is a correctness fixture, not another full
production panel. Checks also cover legal decoding/rule boundaries, real native
movement/docking/depletion blocking, recurrent/skill reset continuity, mixed
activation summaries, raw-array mismatch, partial-failure retention and guarded
CLI refusal. Both actual local B04/B05 source bundles passed verify_source, using
their complete checkpoint configs. The independent Reviewer inspected the nullable
repair and regression and reported **no outstanding material findings**. Syntax
and whitespace checks passed. I additionally made the pending CUDA fixtures use
four Torch threads and explicitly compare CUDA RNG state before/after; TF32 stays
disabled. No production result interaction has started. Full original endpoint
reproduction remains a runtime condition inside B06, not established by the short
fixtures. Publish this source, run the two actual-node CUDA correctness cases,
then admit the unchanged batch only if those checks pass.

The adopted B06 plan and exact Pro answer are already published on main
`ac232d3b8c97656bda51a0f4555599b566ea95b5`. A read-only browser cleanup check found
zero targets for this operation and three unrelated targets; no tab was closed
by that check and no question was resent.

## 2026-09-23 — B06 admitted after actual CUDA checks

The published implementation source is
`f92a94b017816467662115dbbc1409793858613c`. Its two CUDA correctness cases passed
on the configured RTX4070 Laptop /Torch2.7.0+cu118 in **5.28s**, with four Torch
threads and TF32 disabled: original raw-array parity against the unchanged B04
evaluator (including Python/NumPy/Torch/CUDA RNG preservation), and feedback-mode
switching without an added recurrent reset or skill-clock change. Both real
retained source bundles also passed verify_source on that actual node and used
their digest-bound checkpoint configs. Tracked source stayed clean. These are
short correctness fixtures, not the full retained endpoint reproduction.

Source preparation encountered network timeouts before any result admission:
fetch and the partial clone's checkout object fetch needed the configured network
shell. I reconciled and terminated only those identified preparation processes,
removed only that new worktree's stale checkout lock after its Git processes had
exited, and completed the same pinned checkout through the configured shell.
No scientific worker existed during that recovery; no experiment was retried.
The canonical checkout and unrelated processes/artifacts were preserved.

The fixed B06 batch was accepted once at2026-09-24T01:50:18Z. Its original native
handle, exact invocation, input roots, source, process identities and resource
admission are retained in
[launch manifest](../../../../runs/uav_service_auxiliary/b06_of_a01/launch-manifest.json),
[preflight](../../../../runs/uav_service_auxiliary/b06_of_a01/admission-preflight.json)
and [child admission](../../../../runs/uav_service_auxiliary/b06_of_a01/launch-status.json).
These three static files were copied back with byte-digest equality. Kernel
control observation was current main`b84bc737ffbf3da044335ebe77193a74e247edeb`;
launch-bound lead and owner pause passed the native guard. The first native status
showed the recorded runner and supervisor alive with consistent records; no exit
witness and no scientific failure. The existing checkpoint loader reports that
its training-only discriminator buffer is empty; no training or buffer update is
part of this fixed-policy comparison.

Detached observation job`launch-usa-b06-of-a01` adopted the same original status
handle at **generation79**,1500-second window, with zero observation errors. All
previous experiment/Pro notices remain consumed; there is no new Pro request.
The batch remains **0 new fits /0 optimizer updates /160 episode attempts /
240k evaluation team transitions upper bound**. Current status is running and
scientifically incomplete. Full O reproduction is checked before each dependent
F panel; complete collection, all four block-by-panel comparisons, service losses,
nonactivation and actual physical effects still require reading. A checkpoint
rearms observation only; it never restarts the worker or changes the rule.

## 2026-09-23 — B06 complete fixed feedback preserves mean service while reducing return-margin cost

**Decision and scope.** Accept the completed fixed B06 comparison and retain this
finite observation-only feedback package for the two historical N policies and
these exposed S7-S2 worlds. Both final panels and both development panels have
higher mean original J, lower capped/raw return-margin cost and higher mean QoS;
there are no new zero-service worlds. This follows the useful finite-package
branch in the complete [prior Pro advice](#pro-question-2026-09-23-b05-risk-service-next-intervention)
and [pre-result B06 rule](#2026-09-23--b05-advice-adopted-b06-fixed-observation-only-return-feedback).
It does not make the feedback a safety guarantee or a learned improvement.
Local service losses, two retained zero-service episodes and worse battery
minima remain consequential. No threshold, world, source, endpoint or stopping
rule was changed after observation; no automatic training or confirmation follows.

**Execution, collection and verification.** The original accepted operation at
source `f92a94b017816467662115dbbc1409793858613c` exited with code0 and a valid
native identity witness at2026-09-24T03:29:39Z. Its unchanged [manifest](../../../../runs/uav_service_auxiliary/b06_of_a01/launch-manifest.json),
[config](../../../../runs/uav_service_auxiliary/b06_of_a01/config.json),
[exit witness](../../../../runs/uav_service_auxiliary/b06_of_a01/process-exit.json)
and [complete runner summary](../../../../runs/uav_service_auxiliary/b06_of_a01/summary.json)
retain the binding. Sixteen collected files,228714437 bytes, matched remote
sizes and SHA256s. The summary itself is1210118 bytes, SHA256
`82de2a2033417bcb2c1447bd23cc453044ec870e661363dea38bee5db21a7bcf`.
All eight NPZs and both historical source bundles remain recoverable locally
and on the recorded node; no output or source worktree was deleted.

Actual cost is **0 new fits /0 optimizer updates /160 episode attempts /
240000 evaluation team transitions /1920000 agent-step observations**, all
episodes1500 steps and native truncations. O and F each use120000 transitions.
All nonactivating worlds are retained; there are no extra training replications,
omitted worlds or early-end padding. B04/B05 retain seeds914021/914173, development937001–937008,
final938001–938032, native reward coefficient2, CUDA FP32, TF32 off and four
Torch threads. Runner wall5958.012672s (**99.300211min**), userCPU5809.094707s,
systemCPU157.202009s, runner-process peakRSS1472072KiB. Output bytes measured
inside the runner are228713887; the later550-byte supervisor exit witness
explains the collection total. Implementation/checks, transport, reading and
support work are additional, not included in runner wall; no speed claim.

The DM read all four paired panels, every world and the promised diagnostics.
The independent registered Verifier read all eight raw NPZs without calling the
candidate rule or aggregation helpers as proof: exact original O equality with
retained B04/B05 common arrays (41 development and161 final arrays per source),
all pre-command-change common prefixes, native reward identity, seed/length/end
counts, hysteresis and entry/exit bits, inactive pass-through and vector-to-action
formula had zero mismatches. It independently recomputed7268 world/reduction
fields and260 paired aggregate fields plus row effects/zero-service flags;
maximum absolute numeric error was0. Full actor observation/state arrays are not
stored: prefix verification covers retained legal margin/battery, positions,
actions, skills, rewards/metrics and end flags, not independently recovered full
actor inputs. Actual-state actor/recurrent continuation and legal observation
ownership are also checked in the reviewed frozen source and prelaunch tests.

All eight cells record identical before/after policy fingerprints and optimizer
snapshots and assert normalizer immutability. Historical optimizer counters are
not new updates. Immutability during execution is a recorded runtime assertion,
not an inference from good scores or a fresh offline observation of every state.
The two existing empty training-discriminator-buffer loader notices are the full
stderr; evaluation uses no training buffer and there was no exception. The READY
event was read and consumed under generation82, advancing observation to83; no
experiment was restarted and no Pro question was resent.

**Four separate complete-panel readings.** QoS, throughput and cost are per-step
means; J is the full1500-step original return. Final32 is primary for each
historical policy; development8 restricts use. World counts do not add training n.

| Source/panel | J O | J F | J F−O | QoS O | QoS F | QoS F−O |
| --- | --- | --- | --- | --- | --- | --- |
| B04 development | 50.842834 | 366.759692 | 315.916858 | 0.252992371 | 0.253492381 | 0.000500010 |
| B04 final | -496.301830 | 258.691011 | 754.992840 | 0.158025257 | 0.181629811 | 0.023604554 |
| B05 development | -72.367636 | 418.260942 | 490.628577 | 0.276942462 | 0.287947935 | 0.011005473 |
| B05 final | -232.025030 | 320.851159 | 552.876189 | 0.216057847 | 0.223176241 | 0.007118394 |

| Source/panel | Mbps O | Mbps F | Capped cost O | Capped cost F | Raw cost O | Raw cost F |
| --- | --- | --- | --- | --- | --- | --- |
| B04 development | 7.589771126 | 7.604771440 | 0.105076924 | 0.000017033 | 0.159489740 | 0.000017033 |
| B04 final | 4.740757721 | 5.448894337 | 0.239923270 | 0.000042644 | 0.482361201 | 0.000042644 |
| B05 development | 8.308273861 | 8.638438040 | 0.158086006 | 0.000038551 | 0.277330490 | 0.000038551 |
| B05 final | 6.481735407 | 6.695287219 | 0.180828987 | 0.000042278 | 0.369444984 | 0.000042278 |

The fixed-demand Mbps/QoS relationship is not independent positive evidence.
Bookkeeping of mean J changes (service sum, negative2×cost sum, other reward
components) is B04 development(+.750016,+315.179673,−.012831), B04 final
(+35.406831,+719.641878,−.055868), B05 development(+16.508209,+474.142367,−.021998),
and B05 final(+10.677591,+542.360129,−.161530). Return-margin penalty savings
dominate these gains. This is reward accounting, not component-causal attribution.

| Source/panel | J +/0/− worlds | Median deltaJ | DeltaJ range | Amplitude | QoS-loss worlds | Zero service O→F |
| --- | --- | --- | --- | --- | --- | --- |
| B04 development | 5/3/0 | 224.748339 | [0.000000, 841.200659] | 841.200659 | 2 | 0→0 |
| B04 final | 27/5/0 | 673.149142 | [0.000000, 1757.180103] | 1757.180103 | 4 | 6→1 |
| B05 development | 6/2/0 | 475.959619 | [0.000000, 1349.912413] | 1349.912413 | 1 | 0→0 |
| B05 final | 22/10/0 | 228.139102 | [0.000000, 1945.907801] | 1945.907801 | 8 | 1→1 |

There is no J-loss world in this finite evaluation. The5/27/6/22 positive
differences coincide with actual intervention; the20 nonactivating source-worlds
remain exact ties and stay in the means. Positive counts include the very small
B04 final938010(+.246716) and B05 final938014(+.000310) changes at late first
overrides; no post-result practical-success threshold is invented.

B04 final removes zero service in938004/938011/938017/938025/938032, while938030
remains zero QoS with F J−14.356006 despite its+1491.681624 improvement. B05 final
retains zero service in938021, F J−13.116204 despite+1211.353471. No panel creates
a new zero-service world. Those two remaining worlds prevent interpreting all
positive J changes as service restoration. Absolute mean F QoS remains only
.181630/.223176 in the final panels; broad usefulness is not settled by risk savings.

**Battery and adverse service readings.** These are true episode minima including
initial legal battery and all physical post-transition member readings, not the
mean of per-step minima. Lower minimum battery and better spatial return margin
can coexist; neither metric substitutes for the other.

| Source/panel | Mean min O | Mean min F | P10 O | P10 F | Worst O | Worst F | Battery-loss worlds |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B04 development | 0.366579732 | 0.355666712 | 0.341325436 | 0.326217495 | 0.337171152 | 0.312420516 | 5 |
| B04 final | 0.353111020 | 0.337402785 | 0.325910225 | 0.298954994 | 0.311067401 | 0.285397155 | 25 |
| B05 development | 0.378313489 | 0.366323025 | 0.340282104 | 0.315998802 | 0.330785595 | 0.300439710 | 6 |
| B05 final | 0.361645883 | 0.348680473 | 0.319035567 | 0.270643692 | 0.307733819 | 0.258197998 | 19 |

B04 final worst F battery is.285397155 in938032; B05 final is.258197998 in938009.
The largest paired battery loss is−.053979039 at B04 final938030 and−.069742687
at B05 final938015. Mean minimum return margin improves in all four panels,
but this does not certify either a battery floor or future recovery.

QoS and throughput fall in2/4/1/8 worlds for B04dev/B04final/B05dev/B05final.
The worst mean-QoS losses are−.008551409(937007),−.005573438(938024),
−.000377888(937006),−.010742923(938007), respectively. The full tables below
retain every service and battery loss, including their favorable J outcomes.

**Physical intermediate prediction.** Total actual command overrides are
13330 member-steps, matching mode-active steps. Every override has nonzero
realized motion; none is logged as blocked. All observed active steps move
toward the selected station, reduce its distance by approximately30m and
increase legal margin(.002063539 to.002116784) while spending battery. This
is direct conditional telemetry for this batch, not a theorem that any
toward-station command always improves margin. Path separation from O is real.

| Source/panel | Active worlds | Override member-steps | Entries/exits | Interval steps | Max simultaneous | First override range (0-based) | Mean negative-margin member-steps O→F | Mean saturated team-steps O→F |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B04 development | 5 | 665 | 29/26 | 6–25 | 3 | 956–1389 | 411.000→3.625 | 107.000→0.000 |
| B04 final | 27 | 6293 | 268/251 | 1–25 | 4 | 569–1494 | 1070.375→8.375 | 282.844→0.000 |
| B05 development | 6 | 1136 | 49/44 | 4–25 | 3 | 680–1373 | 692.250→6.125 | 180.000→0.000 |
| B05 final | 22 | 5236 | 219/212 | 1–25 | 4 | 530–1499 | 907.906→6.875 | 217.062→0.000 |

Intervals ending at the horizon are included, not labeled completed recovery.
Median observed mode interval is24 steps in each panel. Mode-active station
distance never enters the160m docking radius (minimum1330.946661m across the
batch). This is short margin-restoring movement, not arrival or recharging.
All160 episodes still have **zero charging, charger input, cutoff and depletion**;
station occupancy/queues remain zero. The fourth action coordinate and existing
backhaul guard are part of the F package, so movement, guard effects and downstream
policy adaptation are not isolated causal components. No full battery cycle,
congestion handling or physical failure prevention was tested.

**Fixed250-step descriptions.** These are secondary complete-world means and
do not select a new endpoint or only successful post-trigger segments.

| Source/panel | Steps | DeltaJ in bin | DeltaQoS | Delta capped cost | Delta raw cost |
| --- | --- | --- | --- | --- | --- |
| B04 development | 0–250 | 0.000000 | 0.000000000 | 0.000000000 | 0.000000000 |
| B04 development | 250–500 | 0.000000 | 0.000000000 | 0.000000000 | 0.000000000 |
| B04 development | 500–750 | 0.000000 | 0.000000000 | 0.000000000 | 0.000000000 |
| B04 development | 750–1000 | 1.391738 | -0.000041597 | -0.002804275 | -0.002804275 |
| B04 development | 1000–1250 | 79.940052 | -0.002531078 | -0.161143248 | -0.168667734 |
| B04 development | 1250–1500 | 234.585068 | 0.005572737 | -0.466411823 | -0.785364232 |
| B04 final | 0–250 | 0.000000 | 0.000000000 | 0.000000000 | 0.000000000 |
| B04 final | 250–500 | 0.000000 | 0.000000000 | 0.000000000 | 0.000000000 |
| B04 final | 500–750 | 19.508331 | 0.000906659 | -0.038565406 | -0.038565406 |
| B04 final | 750–1000 | 146.435398 | 0.017292146 | -0.284231791 | -0.373720248 |
| B04 final | 1000–1250 | 250.420159 | 0.035914913 | -0.482914718 | -0.900630951 |
| B04 final | 1250–1500 | 338.628952 | 0.087513604 | -0.633571842 | -1.580994742 |
| B05 development | 0–250 | 0.000000 | 0.000000000 | 0.000000000 | 0.000000000 |
| B05 development | 250–500 | 0.000000 | 0.000000000 | 0.000000000 | 0.000000000 |
| B05 development | 500–750 | 2.765206 | -0.000048897 | -0.005555485 | -0.005555485 |
| B05 development | 750–1000 | 31.082062 | -0.000134690 | -0.062228018 | -0.063283038 |
| B05 development | 1000–1250 | 143.822292 | 0.018391461 | -0.278443441 | -0.432201401 |
| B05 development | 1250–1500 | 312.959017 | 0.047824961 | -0.602057789 | -1.162711711 |
| B05 final | 0–250 | 0.000000 | 0.000000000 | 0.000000000 | 0.000000000 |
| B05 final | 250–500 | 0.000000 | 0.000000000 | 0.000000000 | 0.000000000 |
| B05 final | 500–750 | 26.223631 | 0.000166667 | -0.052360132 | -0.060230316 |
| B05 final | 750–1000 | 106.917931 | 0.002615619 | -0.212581259 | -0.338486643 |
| B05 final | 1000–1250 | 167.519312 | 0.019939356 | -0.325230595 | -0.713652547 |
| B05 final | 1250–1500 | 252.215316 | 0.019988720 | -0.494548271 | -1.104046732 |

**All complete world readings.** J is absolute raw return; service/cost are
per-step means. Battery is the true episode minimum. All rows enter panel means;
zero service, nonactivation and losses are not filtered. Full throughput/raw-cost,
event, interval, bin and margin fields remain in the linked runner summary/NPZs.

**B04 development**

| World | J O | J F | DeltaJ | QoS O | QoS F | Cost O | Cost F | Min battery O | Min battery F | Override member-steps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 937001 | 303.743662 | 303.743662 | 0.000000 | 0.210050087 | 0.210050087 | 0.000000000 | 0.000000000 | 0.377877870 | 0.377877870 | 0 |
| 937002 | -577.833704 | 223.333626 | 801.167330 | 0.146016387 | 0.156951439 | 0.261689771 | 0.000066420 | 0.414504474 | 0.384285067 | 332 |
| 937003 | 388.841047 | 388.841047 | 0.000000 | 0.267897216 | 0.267897216 | 0.000000000 | 0.000000000 | 0.363308388 | 0.363308388 | 0 |
| 937004 | 63.889124 | 447.371109 | 383.481985 | 0.305692904 | 0.307470220 | 0.126985203 | 0.000047417 | 0.337171152 | 0.312420516 | 117 |
| 937005 | 187.918165 | 187.918165 | 0.000000 | 0.133968947 | 0.133968947 | 0.000000000 | 0.000000000 | 0.391297960 | 0.391297960 | 0 |
| 937006 | 339.754194 | 405.768887 | 66.014694 | 0.285804708 | 0.280589137 | 0.024616006 | 0.000003323 | 0.355398003 | 0.351013193 | 24 |
| 937007 | -367.290467 | 473.910191 | 841.200659 | 0.334601897 | 0.326050489 | 0.284685066 | 0.000009142 | 0.343105843 | 0.332130485 | 96 |
| 937008 | 67.720649 | 503.190847 | 435.470197 | 0.339906821 | 0.344961516 | 0.142639346 | 0.000009961 | 0.349974165 | 0.333000213 | 96 |

**B04 final**

| World | J O | J F | DeltaJ | QoS O | QoS F | Cost O | Cost F | Min battery O | Min battery F | Override member-steps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 938001 | -876.165009 | 397.525291 | 1273.690299 | 0.266074060 | 0.274740114 | 0.420239908 | 0.000007576 | 0.335210634 | 0.309586364 | 144 |
| 938002 | 304.295543 | 304.295543 | 0.000000 | 0.210346355 | 0.210346355 | 0.000000000 | 0.000000000 | 0.346237028 | 0.346237028 | 0 |
| 938003 | -336.553081 | 294.968628 | 631.521709 | 0.194758185 | 0.205080149 | 0.205514653 | 0.000119542 | 0.339606263 | 0.315045543 | 387 |
| 938004 | -1035.744855 | 91.709410 | 1127.454265 | 0.000000000 | 0.070742213 | 0.340485926 | 0.000038945 | 0.381030895 | 0.342662450 | 293 |
| 938005 | -1394.507223 | 229.374058 | 1623.881282 | 0.143495659 | 0.162253883 | 0.532073772 | 0.000017443 | 0.332630758 | 0.345992905 | 186 |
| 938006 | -499.094901 | 402.873599 | 901.968500 | 0.257748759 | 0.277777435 | 0.290663443 | 0.000022096 | 0.347631278 | 0.336081163 | 168 |
| 938007 | 94.403898 | 441.273494 | 346.869596 | 0.302476983 | 0.304024160 | 0.114852264 | 0.000002654 | 0.325417669 | 0.322233033 | 48 |
| 938008 | -1484.760602 | 189.553653 | 1674.314256 | 0.120105395 | 0.135474767 | 0.550440201 | 0.000029617 | 0.337851272 | 0.322922019 | 304 |
| 938009 | -784.334361 | 268.059297 | 1052.393659 | 0.176843948 | 0.188585014 | 0.344981352 | 0.000046394 | 0.360146508 | 0.357939644 | 337 |
| 938010 | 345.871096 | 346.117813 | 0.246716 | 0.240104177 | 0.240104177 | 0.000085152 | 0.000002921 | 0.359629341 | 0.357572120 | 6 |
| 938011 | -624.503496 | 90.273078 | 714.776574 | 0.000000000 | 0.069345510 | 0.203617839 | 0.000022216 | 0.346415617 | 0.336281837 | 89 |
| 938012 | 76.060876 | 331.833025 | 255.772149 | 0.228434757 | 0.229509677 | 0.084733754 | 0.000005024 | 0.395598946 | 0.379558730 | 48 |
| 938013 | 283.359371 | 363.404585 | 80.045214 | 0.250415869 | 0.250291656 | 0.026744835 | 0.000000873 | 0.325651582 | 0.318020917 | 24 |
| 938014 | -155.605685 | 149.927347 | 305.533032 | 0.107733333 | 0.107733333 | 0.101851475 | 0.000006715 | 0.313548464 | 0.299033823 | 72 |
| 938015 | -1290.896840 | 318.931003 | 1609.827843 | 0.162586641 | 0.222799355 | 0.506869307 | 0.000231029 | 0.349697350 | 0.297424133 | 777 |
| 938016 | -914.169805 | 261.902626 | 1176.072432 | 0.129794123 | 0.182877844 | 0.365715665 | 0.000047619 | 0.349894633 | 0.335657245 | 289 |
| 938017 | -266.916911 | 41.955252 | 308.872164 | 0.000000000 | 0.038184990 | 0.083912741 | 0.000047848 | 0.351980656 | 0.340960967 | 117 |
| 938018 | -603.156456 | 13.673577 | 616.830033 | 0.020357698 | 0.019156262 | 0.206214741 | 0.000003790 | 0.382711448 | 0.370029383 | 72 |
| 938019 | 101.090234 | 279.246750 | 178.156515 | 0.195357608 | 0.195576005 | 0.059287460 | 0.000009823 | 0.399537689 | 0.385744196 | 35 |
| 938020 | -891.134440 | 318.639590 | 1209.774030 | 0.178865577 | 0.221683076 | 0.382148781 | 0.000178056 | 0.379736345 | 0.336047863 | 611 |
| 938021 | 131.628216 | 131.628216 | 0.000000 | 0.097151555 | 0.097151555 | 0.000000000 | 0.000000000 | 0.348999675 | 0.348999675 | 0 |
| 938022 | 431.154043 | 431.154043 | 0.000000 | 0.295783593 | 0.295783593 | 0.000000000 | 0.000000000 | 0.351308657 | 0.351308657 | 0 |
| 938023 | -1252.867887 | 367.410112 | 1620.277999 | 0.233882498 | 0.254588277 | 0.529776070 | 0.000013820 | 0.328238009 | 0.296523858 | 120 |
| 938024 | -483.329470 | 351.406237 | 834.735707 | 0.250027386 | 0.244453948 | 0.281053759 | 0.000024881 | 0.333705023 | 0.320133558 | 192 |
| 938025 | -1198.684186 | 124.236652 | 1322.920837 | 0.000000000 | 0.092990272 | 0.394508739 | 0.000023483 | 0.358841348 | 0.330585284 | 133 |
| 938026 | 337.549766 | 534.424674 | 196.874908 | 0.366640192 | 0.366271612 | 0.065839315 | 0.000030055 | 0.359230638 | 0.360358156 | 121 |
| 938027 | 185.714621 | 185.714621 | 0.000000 | 0.132300357 | 0.132300357 | 0.000000000 | 0.000000000 | 0.379850347 | 0.379850347 | 0 |
| 938028 | -1375.314685 | 312.493648 | 1687.808333 | 0.147583941 | 0.218152087 | 0.527563158 | 0.000250810 | 0.341049595 | 0.303613391 | 945 |
| 938029 | 316.524526 | 316.524526 | 0.000000 | 0.219732176 | 0.219732176 | 0.000000000 | 0.000000000 | 0.442478182 | 0.442478182 | 0 |
| 938030 | -1506.037629 | -14.356006 | 1491.681624 | 0.000000000 | 0.000000000 | 0.497305144 | 0.000045918 | 0.352925274 | 0.298946235 | 217 |
| 938031 | 21.844910 | 182.136020 | 160.291111 | 0.128207407 | 0.128459259 | 0.053312054 | 0.000004307 | 0.331694112 | 0.323663253 | 47 |
| 938032 | -1537.378126 | 219.801977 | 1757.180103 | 0.000000000 | 0.155984845 | 0.507753122 | 0.000131143 | 0.311067401 | 0.285397155 | 511 |

**B05 development**

| World | J O | J F | DeltaJ | QoS O | QoS F | Cost O | Cost F | Min battery O | Min battery F | Override member-steps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 937001 | 281.006204 | 281.006204 | 0.000000 | 0.194733840 | 0.194733840 | 0.000000000 | 0.000000000 | 0.393161605 | 0.393161605 | 0 |
| 937002 | -258.928491 | 373.562278 | 632.490769 | 0.244953696 | 0.257470162 | 0.204763712 | 0.000138140 | 0.436937331 | 0.401187014 | 395 |
| 937003 | 366.571828 | 686.000297 | 319.428468 | 0.465480173 | 0.467213453 | 0.105639910 | 0.000017415 | 0.371493050 | 0.371458820 | 72 |
| 937004 | -94.156202 | 590.716628 | 684.872830 | 0.393540367 | 0.403246815 | 0.223451071 | 0.000007439 | 0.370602315 | 0.370235470 | 72 |
| 937005 | 409.080037 | 409.080037 | 0.000000 | 0.281843001 | 0.281843001 | 0.000000000 | 0.000000000 | 0.432866343 | 0.432866343 | 0 |
| 937006 | 206.564970 | 300.404478 | 93.839507 | 0.210093553 | 0.209715664 | 0.031466832 | 0.000001677 | 0.346309637 | 0.338568253 | 24 |
| 937007 | -1023.588074 | 326.324340 | 1349.912413 | 0.174785536 | 0.227364948 | 0.423720908 | 0.000075072 | 0.330785595 | 0.300439710 | 379 |
| 937008 | -465.491357 | 378.993274 | 844.484631 | 0.250109531 | 0.261995595 | 0.275645617 | 0.000068662 | 0.344352037 | 0.322666984 | 194 |

**B05 final**

| World | J O | J F | DeltaJ | QoS O | QoS F | Cost O | Cost F | Min battery O | Min battery F | Override member-steps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 938001 | -187.990277 | 431.308497 | 619.298774 | 0.281651559 | 0.297354191 | 0.198642781 | 0.000023144 | 0.341567143 | 0.332525706 | 121 |
| 938002 | 304.681632 | 304.681632 | 0.000000 | 0.211052091 | 0.211052091 | 0.000000000 | 0.000000000 | 0.332845421 | 0.332845421 | 0 |
| 938003 | -285.235167 | 299.771945 | 585.007112 | 0.210874174 | 0.208197118 | 0.196347291 | 0.000023431 | 0.340932293 | 0.326217218 | 144 |
| 938004 | -1040.922537 | 183.935142 | 1224.857678 | 0.097844788 | 0.131840192 | 0.391482952 | 0.000079132 | 0.373240214 | 0.362124330 | 318 |
| 938005 | -1796.058763 | 149.849038 | 1945.907801 | 0.037220341 | 0.109295763 | 0.612961156 | 0.000133485 | 0.313619565 | 0.268703771 | 602 |
| 938006 | -880.517761 | 207.437396 | 1087.955157 | 0.143121033 | 0.146959981 | 0.360788964 | 0.000049459 | 0.318844569 | 0.305012778 | 245 |
| 938007 | -297.303106 | 158.373126 | 455.676233 | 0.125488008 | 0.114745085 | 0.157257500 | 0.000002613 | 0.327238138 | 0.322238785 | 24 |
| 938008 | -1257.431391 | 172.892817 | 1430.324208 | 0.125526562 | 0.123372387 | 0.477847770 | 0.000038003 | 0.329082937 | 0.323195987 | 240 |
| 938009 | -1611.942492 | 6.501484 | 1618.443976 | 0.004222222 | 0.014568627 | 0.534816733 | 0.000138078 | 0.320754550 | 0.258197998 | 397 |
| 938010 | 385.535197 | 395.696295 | 10.161097 | 0.273256121 | 0.273367510 | 0.003334621 | 0.000003328 | 0.349556988 | 0.341732045 | 24 |
| 938011 | 595.705532 | 595.705532 | 0.000000 | 0.407250694 | 0.407250694 | 0.000000000 | 0.000000000 | 0.381637964 | 0.381637964 | 0 |
| 938012 | 182.694045 | 303.698838 | 121.004793 | 0.211787761 | 0.210391925 | 0.041053287 | 0.000034953 | 0.413075285 | 0.393885999 | 131 |
| 938013 | 607.339525 | 607.339525 | 0.000000 | 0.414423244 | 0.414423244 | 0.000000000 | 0.000000000 | 0.377124043 | 0.377124043 | 0 |
| 938014 | 262.644013 | 262.644322 | 0.000310 | 0.183699472 | 0.183699472 | 0.000000339 | 0.000000236 | 0.373599153 | 0.373599153 | 1 |
| 938015 | -1520.376718 | 69.091854 | 1589.468572 | 0.052689409 | 0.056677917 | 0.528510931 | 0.000326961 | 0.328531028 | 0.258788341 | 904 |
| 938016 | 131.370650 | 393.703297 | 262.332647 | 0.272036213 | 0.271812008 | 0.087564020 | 0.000011913 | 0.363860567 | 0.347234395 | 72 |
| 938017 | 418.179523 | 547.175022 | 128.995499 | 0.374194091 | 0.375232186 | 0.042493109 | 0.000013657 | 0.378571780 | 0.380161321 | 43 |
| 938018 | 583.507255 | 583.507255 | 0.000000 | 0.399342115 | 0.399342115 | 0.000000000 | 0.000000000 | 0.400974300 | 0.400974300 | 0 |
| 938019 | -754.504727 | 66.260420 | 820.765146 | 0.009888889 | 0.052993251 | 0.252211529 | 0.000058755 | 0.386119481 | 0.352889925 | 353 |
| 938020 | 666.535107 | 666.535107 | 0.000000 | 0.454360552 | 0.454360552 | 0.000000000 | 0.000000000 | 0.413796232 | 0.413796232 | 0 |
| 938021 | -1224.469675 | -13.116204 | 1211.353471 | 0.000000000 | 0.000000000 | 0.404019744 | 0.000041326 | 0.307733819 | 0.308871499 | 218 |
| 938022 | 333.905437 | 333.905437 | 0.000000 | 0.230813124 | 0.230813124 | 0.000000000 | 0.000000000 | 0.351440637 | 0.351440637 | 0 |
| 938023 | -1565.750359 | 107.818352 | 1673.568711 | 0.012032549 | 0.081111695 | 0.523557072 | 0.000060544 | 0.323127515 | 0.288102983 | 360 |
| 938024 | -210.134824 | 412.483489 | 622.618313 | 0.293700088 | 0.285180436 | 0.211843945 | 0.000049386 | 0.365200024 | 0.350725440 | 208 |
| 938025 | 362.754967 | 362.754967 | 0.000000 | 0.252246706 | 0.252246706 | 0.000000000 | 0.000000000 | 0.410061828 | 0.410061828 | 0 |
| 938026 | 348.324970 | 402.772280 | 54.447311 | 0.279101203 | 0.277534576 | 0.018935681 | 0.000000585 | 0.364078825 | 0.363368800 | 24 |
| 938027 | 121.856158 | 121.856158 | 0.000000 | 0.088756063 | 0.088756063 | 0.000000000 | 0.000000000 | 0.388112592 | 0.388112592 | 0 |
| 938028 | -1607.928730 | 74.298639 | 1682.227368 | 0.060830256 | 0.058816657 | 0.562182751 | 0.000228594 | 0.313951786 | 0.267871512 | 709 |
| 938029 | 344.417567 | 344.417567 | 0.000000 | 0.237933755 | 0.237933755 | 0.000000000 | 0.000000000 | 0.471269721 | 0.471269721 | 0 |
| 938030 | 372.052300 | 565.997856 | 193.945556 | 0.386593155 | 0.387482657 | 0.064217704 | 0.000013936 | 0.374127747 | 0.370523542 | 25 |
| 938031 | 446.204619 | 446.204619 | 0.000000 | 0.306686858 | 0.306686858 | 0.000000000 | 0.000000000 | 0.381478478 | 0.381478478 | 0 |
| 938032 | 348.057057 | 701.735373 | 353.678316 | 0.475228005 | 0.478140864 | 0.116457707 | 0.000021364 | 0.357113636 | 0.353062398 | 73 |

**Cumulative update and next decision.** Current main background at
`4f1f1f9eecf00c4218d827033bf858dd7f79a740`, topic6 and the service/risk plan,
was read together with the owner-adopted September23 DM-autonomy/workflow changes.
The B05 lesson made preservation of service and all contrary worlds decisive;
B06 now supplies a concrete conditional counterexample to the idea that reducing
these policies' return-margin penalty must mainly sacrifice service. It strengthens
the value of an ordinary legal current-observation feedback comparator before
paying for another predictive auxiliary or critic. B03's unreplicated auxiliary
gains and B04/B05's coefficient4 service limitation are unchanged; nothing here
revives those recipes, identifies a representation/credit bottleneck, establishes
MARL population superiority or adds new training replication.

The main gap has become more specific: all observed feedback is brief movement
far from stations, while battery minima worsen and charging never occurs. There
is useful finite-horizon control evidence, but no observed sustained service/
energy cycle. A new direct learning comparison would need a reason to beat this
stronger executable baseline; another set of1500-step worlds would mostly measure
more of the already-tested conditional use. A separately declared native longer
operation comparison could test the unobserved cycle, but would be a new task
contract/exposure, not an extension of B06 or a remedy selected to improve its score.

Selected next action is a focused Pro scientific consultation on that investment
choice, after publishing this complete result: whether a source-defined longer
native-operation comparison has greater information value than a new learning
comparison or retaining the bounded result without more computation. This uses
section5 because the next question/comparator or claim scope may change. The prior
advice already covers B06 retention; it did not select a sustained-operation or
new learning study. No successor experiment, threshold search, safety claim or
confirmation is launched by this result. The active DM responsibility continues;
this is a chosen decision step, not a missing permission or fabricated dependency.

**Raw recovery.** Config, complete per-world summary and native status are
versioned unchanged. Bulk raw output is retained under
`/home/wu/hmasd-worktrees/usa-b06-f92a94b01/runs/uav_service_auxiliary/b06_of_a01`
on `wsl_4070` (`hmasd-wsl-node`), with a verified collection copy at
`/home/fires/.codex/worktrees/d319/hmasd-wsl/runs/uav_service_auxiliary/b06_of_a01`.
Source and its operation metadata remain intact. Paths below are relative to
that output root and hashes are also present in the original summary.

| Raw path | Bytes | SHA256 |
| --- | --- | --- |
| B04/trajectories/development_F.npz | 11078841 | `b741be06e83bf6ab57365da41dcda745b87e189daa19c7ac1f5985637f007f25` |
| B04/trajectories/development_O.npz | 11023687 | `f928ddce074dcbcc77014dc7da9787c1f5c03151542040eb480ff7e549d9d9b1` |
| B04/trajectories/final_F.npz | 45008934 | `c579759efb2ce0197923e50ae685a5a1c2f545b418a1e43057acb7ff95774398` |
| B04/trajectories/final_O.npz | 44775904 | `f5afe84a354791c9071ed957a1f2b17ae515a00d7dc187a8b12ccbd0c965a832` |
| B05/trajectories/development_F.npz | 11451771 | `3c2f2c31448ec2ab1e870a7fd7fee8a1f80af2f82ce48214cd5a1fbc793b6e9d` |
| B05/trajectories/development_O.npz | 11458985 | `1dd048b1b476733c344559d86ed9cf9feb1123b96131d68b93ccb920a9c0d6f8` |
| B05/trajectories/final_F.npz | 46358433 | `a5fda1fa3d121d8d7d2440e3b88e5e8ec73d5743ef2312aee320cbcfb7b0231b` |
| B05/trajectories/final_O.npz | 46337207 | `adba5176519eee5bfcadf22a1e645fd2002798bbbf4b58f7415078c5c000a8fc` |

## Pro question 2026-09-23 b06-feedback-use-and-next-investment

Conversation: reuse this direction's existing Jev conversation; its URL remains in local operation metadata only.

Question: B06 的固定合法余量反馈已在两个旧 N 制品的两个面板上改善平均原生 J、成本与服务，但没有到站充电，且最低电池变差。下一笔科学投入应优先检验更长原生运行中的持续服务/能量循环，还是需要一个新的学习比较，或有理由止于当前有限用途？请判断这个具体选择，给出最有信息价值且可执行的下一观察及反面分支；不需要再次批准 B06，不要求新增架构或固定数量候选。

### Standing and decision boundary

B06 已完整收取、独立数值核验并按事前分支保留有限反馈包。完整新条目是本文件
`2026-09-23 — B06 complete fixed feedback preserves mean service while reducing return-margin cost`，
含全部80个配对世界、绝对数值、服务/电池损失、六段250-step描述和原始产物定位。
原执行 O 与 retained B04/B05 N 的共同数组完全复现；全部先于首次实际覆盖的保留诊断前缀一致。
规则/汇总独立核验未调用候选答案作证明，数值差0。完整 actor observation/state 数组未记录，
不可把诊断前缀匹配说成对全部 actor 输入的独立逐数组核验。源码/测试另核验合法信息和真实历史。

两份历史 N：B04 seed914021，B05 seed914173，最终 update30/各180k训练；不是新训练。
此次固定 CUDA FP32/TF32off/4threads、S7-S2、N8、k10、每世界1500步，O/F各80回合，
0新fits、0更新、共240k评价team transitions、1.92M成员观察、runner99.300211min。
原生评价 J 保持 QoS − 2×capped return cost − 原事件罚 + 原 PBRS，不改奖励/需求/电量。
两来源都用 development937001–937008、final938001–938032；final是各制品主要用途读数，
开发约束范围。这些世界已曝光，不能当新 held-out 确认，世界数不增加训练 n。

| 来源/面板 | J O→F；差 | QoS O→F | capped cost O→F | J正/平/负 | 零服务O→F |
| --- | --- | --- | --- | --- | --- |
| B04 dev8 | 50.842834→366.759692；+315.916858 | .252992371→.253492381 | .105076924→.000017033 | 5/3/0 | 0→0 |
| B04 final32 | −496.301830→258.691011；+754.992840 | .158025257→.181629811 | .239923270→.000042644 | 27/5/0 | 6→1 |
| B05 dev8 | −72.367636→418.260942；+490.628577 | .276942462→.287947935 | .158086006→.000038551 | 6/2/0 | 0→0 |
| B05 final32 | −232.025030→320.851159；+552.876189 | .216057847→.223176241 | .180828987→.000042278 | 22/10/0 | 1→1 |

风险账面节省主导J变化，吞吐与QoS固定倍数不增加证据。不是所有服务都改善：四格有2/4/1/8个
QoS损失世界，最差依次−.008551409/−.005573438/−.000377888/−.010742923。B04 final938030、
B05 final938021仍为零服务，F J为−14.356006/−13.116204，尽管各自J差+1491.681624/+1211.353471。
四格最低电池均值依次从.366579732/.353111020/.378313489/.361645883降至
.355666712/.337402785/.366323025/.348680473；P10也全低。B04/B05 final的P10为
.325910225→.298954994、.319035567→.270643692，最差电池.311067401→.285397155、
.307733819→.258197998。成本不是电量，两个指标必须分读。

F 保持原网络/normalizer，actor在F实际历史每步运行，skill/GRU仅原生episode reset，不用影子O动作。
它只读当前合法观察里的自身raw margin和有效站点相对坐标：margin<=0进入，>=.05退出；
按当前3D最近站点、固定30m/s水平/5m/s垂直尺度，T=max(1,||r_xy||/30,|r_z|/5)，
v=r/T，提交(vx/30,vy/30,vz/5,1)；d<=160时提交(0,0,0,1)。第四维及原backhaul guard
例外也是包的一部分，没有纯速度因果主张。未激活时传递当前actor基于当前F历史的原命令。

实际60/80来源-世界激活，20个未激活仍全留在均值。共13330成员覆盖步，每步都有约30m朝站点
实际位移、合法margin增加(.002063539–.002116784)，同时消耗电量。覆盖段中位24步，最多25步；
最近站点距离仍至少1330.946661m，没有覆盖进入160m docking半径。所有160回合均在1500原生
truncation结束，充电/输入能量/排队/切断/耗尽全零。它是短时空间余量修复，没有观察完整能量循环。

之前的负证据仍成立：B03两个D/S/G完整共同学习区组的收益未复制、共同事实MSE不选择原生用途；
B04/B05训练系数2→4的最终J收益复制，但开发均值均负，B05最终QoS下降且R有8个零服务世界。
这些配方不复活。B06给了更强的简单可执行对照，不能因新平均正值就宣称预测、critic或更强学习必需。

上一轮完整Pro回答已明确覆盖“双方最终与开发有用则保留有限包、无自动训练/确认”的分支，本次
保留据此完成；它没有选择后继持续运行任务或新的学习比较。现在问的是发生实质变化的下一投入选择，
不是每批结果的重复评审。当前无运行中的结果批次、无重复Send、无待验收的旧Pro答复。

### The source-defined distinction that may change the next choice

我的暂定偏好是先问当前强简单反馈在完整能量使用过程中还剩什么服务问题，再买新训练。
直接改评价horizon可能有信息，但不是把旧轨迹无改动地接长：独立只读Scout发现原生
`current_step/max_steps`进入actor观察和中央state，排队等待也按max_steps归一化。
将max_steps1500改3000从step1就改变时间信息，冻结策略动作/循环历史可能随即改变。
因此“头1499步应完全复现B06”不是可用合同；固定动作序列的物理前缀与策略闭环前缀是两回事。
只为保前缀而另造时间分母/剪裁也会是新的观察干预，不能偷偷叫原生长时运行。

冻结B06 source verifier要求保存checkpoint的episode_length=1500，新研究必须保留该训练身份，
另显式声明评价配置差异，不能改旧config/digest或放松B06再重跑。当前actor/技能代码没有1500步
强制结构reset，k10刷新仍可继续；评价config/buffer语义及时间输入要分别处理。

实际S2源配置：160Wh，初始比例uniform[.75,1]，reserve.1，emergency.05，cutoff.02；
两站每站容量1、1000W充电、160m docking、20m capture、实际速度<=1m/s且有合法dock请求才可入站；
每步先耗能再充电，所有成员电池耗尽可提前terminate。更长运行仅增加机会，代码并不保证这些策略会
到站充电；不造低电量开局、掉线、oracle位置或强制排队来追求阳性事件。

请基于这些源事实判断：若选原生更长任务，它回答的是冻结策略+F在新时间信息/任务范围下的用途，
而非纯延长能量暴露机制；这个代价是否仍值得？如果不值得，指出比它更有决策价值的实际学习或其他
窄比较，说明哪个中间变化和原生服务/风险后果能区分最强替代解释。也可建议不再支付计算，给出真实
信息价值/机会成本理由；完成一个配方本身不是停止理由。不要按B06结果搜阈值、速度或站点协调参数。

### Prospective cost and constraints

这是科学选择咨询，尚非新实验注册。长时路线的具体可比成本尺度是两旧N×O/F×40旧世界×3000步，
**0新fits、160次episode尝试、最多480k评价team transitions/3.84M成员观察**；H3000是待论证的
任务候选，不是从新运行中选择、也不保证充电。按B06吞吐约198.6 runner分钟仅作量级参考，实际新增
低电量/充電逻辑与存储成本未知。可以据源码和问题选择更小且诚实的固定比较，不能事后加长直到事件出现。
保留开发/最终、两个来源、实际早终及全部损失的科学价值，需要同成本一起比较。

若主张新的完整学习比较，成本参照是一对独立新训练实例、每臂180k的2fits/360k训练，加原B05式
两臂192k评价，至少552k team transitions和实施/核验；这只是成本参照，不指定新网络/种子/配方，
也不是确认。必须说明为何当前简单反馈这个更强参照仍留下值得学的缺口。要做确认须另有实际claim、
3–5新独立训练seed/arm的固定前瞻与批评，本问题不批准确认。

Owner pause当前lifted；owner于2026-09-23授权DM自主选题/转向、失败或完成后回看项目证据并选有价值
的下一步，继续保留全部反证。这个授权不改B06冻结合同，不接管其他DM，不要求新任务或跨task通信。
Pro只给建议，不启动实验、不改代码/阈值/控制，不建立新许可门槛。当前仅此一个科学选择。

### Context and source precedence

- **当前治理/方法/项目背景**明确用main `4f1f1f9eecf00c4218d827033bf858dd7f79a740`：
  `docs/project/OPERATING_CONSTITUTION.md` §§1–5、7–8；`.agents/skills/hmasd-scientific-tools/SKILL.md`
  的 Update the working explanation、Comparators、Statistics、Cost and exposure、Pro；
  `.agents/skills/hmasd-research-engineering/SKILL.md` 的 Checks and review、Publishing direction results。
  `docs/research/RESEARCH.md` topic6中服务/风险条目和 Current research plan 的服务线：旧B05反证促成B06
  的服务保留读法；本问题给出的新B06事实更新该背景。其他方向的用途/部署区别可用来约束类比，
  不要求读完整项目历史或接管其工作。
- **新结果与旧咨询**用本次 `source_sha` 的
  `docs/research/candidates/uav_service_auxiliary/NOTES.md`：上面的完整B06结果、
  `2026-09-23 — B05 advice adopted; B06 fixed observation-only return feedback`，
  `Pro question 2026-09-23 b05-risk-service-next-intervention` 的完整Answer，及
  `2026-09-23 — B05 complete endpoint risk savings recur service gains do not`。
  `runs/uav_service_auxiliary/b06_of_a01/{config,summary,launch-manifest,process-exit}.json`为本次完整结果；
  必要时读取B04/B05 N/R summary，不能把summary核对说成自己读到了仓库外二进制原始轨迹。
- **冻结实现/源事实**用 `f92a94b017816467662115dbbc1409793858613c`：
  `experiments/candidates/uav_service_auxiliary/b06/{feedback,native}.py`（合法F、原执行、保存配置和身份），
  `experiments/candidates/uav_service_auxiliary/b01/native.py`（make_config、make_env），
  `experiments/candidates/uav_service_auxiliary/b04/evaluation.py`，
  `envs/pettingzoo/relay/routed_core.py`（truncation、time_ratio actor/state），
  `envs/pettingzoo/relay/energy_aware.py`（margin、能量/充电、等待归一化、终止和原reward），
  `hmasd/agent.py`（step、reset_env_state、原skill clock），`configs/config_1.py`。
  重点核对max_steps/观察与实际低电量/充电规则；不要求改已冻结实现。

当前明确的治理/方法替代旧会话中冲突的指令；历史/冻结材料只按其原实验含义使用。
不要用移动branch或聊天记忆替代给定revision。若关键源不可读，指出影响哪个判断，其他可支持的推理继续。
不需要资料读取回执表或额外结果文件。

Constraints: no training, no experiment launch, no source/control edits. Write only inside the
empty `### Answer` subsection of this exact question in
`docs/research/candidates/uav_service_auxiliary/NOTES.md` on branch
`codex/uav-service-predictive-control`, repository `CartmanFatass/My-paper-code`.
Read at the supplied immutable source_sha, but fetch the latest target file before
writing and use its actual blob SHA. Preserve the question and every other byte;
stop on overlapping edits. Return the actual answer commit on successful write.
If GitHub writeback fails, return the complete answer in chat, not a receipt or link.

Return: 说明哪些判断被加强/削弱/保持，最强反对意见，选定下一投入及其信息价值。
若建议新比较，给最小完整的可前瞻方案、匹配条件/必要配置区别、实际成本、先于结果的中间与原生
预测、失败/非激活如何改变投入；不要把建议变成新增许可要求或自动排队实验。
给出MATERIAL_DISSENT: yes/no，引用实际使用的关键源并说明未读的关键材料。

### Answer

Saved from chat (2026-09-23 PDT). Same accepted question key `hmasd:5c8754639c02f1a11610163143efcd3fdfbd24cac75ec66640f961646e7fc366`; the complete answer was read. Delivery verification returned `NOT_DELIVERED`: `dd240572aa3c83b2ce39ae4ab3c46ac999e077a2` is the unchanged source target blob, not an answer commit. Remote source and local target matched `2c73e4c420773ce0b0991bb53f105bcd24c762cf`; the assigned Answer remained empty. Original chat text follows verbatim, including rendered formula line breaks and attachment citation labels. Body SHA-256 `a71d5d72d34633aef02af18aa652ab186e6529651f9290e77d6b259eea902933`; saved file SHA-256 `6c096e318b440f945632bdfa6b80fbe0e24669e23be81c189ee1448fb1fe1980` (one trailing newline). Private conversation address remains only in local transport state.

GitHub 读取可用，但本轮可调用接口没有仓库文件写入动作，因此未写回；实际 Answer commit：无。 最后读取的目标 blob 为 dd240572aa3c83b2ce39ae4ab3c46ac999e077a2，本次指定问题下的 ### Answer 仍为空。本轮没有修改仓库或启动实验。以下为完整答复。

B06 后续：选择一次固定 H3000 的原生长任务比较，不先购买新的学习模块

MATERIAL_DISSENT: no。

我支持优先执行一次固定 H3000 比较：两份既有 N 最终制品，各自比较原执行 O 与完全不变的反馈 F，保留全部既有 development8／final32 世界。上限为 160 次 episode 尝试、480k 评价团队 transitions、0 新 fits、0 optimizer updates。

这次要回答的是：**在时间信息与任务时域都按原生规则改变的 3000 步任务中，这两份冻结策略加 F 是否仍有值得保留的服务—风险用途，以及实际发生了怎样的能量消耗、补充和服务恢复。**它不是把 B06 的轨迹原样接长，也不是一个隔离了“增加能量暴露”的机制实验。

我不同时选择新的学习比较、时间分母消融、更多世界、阈值搜索或确认。支持 H3000 的理由不是“B06 阳性，所以还应继续”，而是 B06 已把剩余问题具体化为：空间返航余量的修复，能否在更深的能量消耗过程中继续支持服务。现在直接观察这个强简单对照，比先假定预测器或 critic 存在可修复缺陷更有信息价值。

一、B06 加强了有限用途，尚未建立持续能量循环

四个用途格子都应保留。下表的 J 是完整原生 episode 回报，成本仍是原来的封顶返航成本；没有将反馈后的表现换成另一套奖励。

hmasd-pro-question-usa-b06-next…

来源／面板	O→F 原生 J	F−O J	QoS：O→F	返航成本：O→F
B04，development8	50.842834→366.759692	+315.916858	.252992371→.253492381	.105076924→.000017033
B04，final32	−496.301830→258.691011	+754.992840	.158025257→.181629811	.239923270→.000042644
B05，development8	−72.367636→418.260942	+490.628577	.276942462→.287947935	.158086006→.000038551
B05，final32	−232.025030→320.851159	+552.876189	.216057847→.223176241	.180828987→.000042278

**加强的判断有两项。**第一，在这两份已经训练好的 N 制品、这些世界及 1500 步范围内，合法执行反馈可以产生实际原生增量，不需要为这个增量再训练一个预测头或改变整段训练奖励。第二，相比 B04/B05 的风险重加权结果，B06 的平均服务保留更好：四格平均 QoS 都提高，全部 80 个来源—世界配对没有 J 损失。这支持已完成的“保留有限反馈包”决定，不能再把它只描述为风险代理量变好。它仍依赖已训练的 N；零新增学习不等于既有学习没有作用。

hmasd-pro-question-usa-b06-next…

**被削弱的是“风险节省必然需要明显牺牲服务”的强解释，而不是所有服务代价。**四格仍分别有 2／4／1／8 个 QoS 损失世界。B04 的 final938030 和 B05 的 final938021 仍没有服务，虽然其 J 因成本节省大幅改善。因此，J 没有负配对不等于服务逐世界占优，更不等于已经得到高绝对服务水平。

hmasd-pro-question-usa-b06-next…

尚未建立的是节电、到站补能、持续服务和灾难预防。四格最低电池的均值和 P10 都变差；两个 final 面板的最差电池分别从 .311067401／.307733819 降至 .285397155／.258197998。与此同时，反馈覆盖产生朝站点的实际运动和 margin 增加，但没有进入 160 米 docking 区域，最近仍有约 1331 米；所有 episode 的充电、输入能量、排队、切断和耗尽均为零。正确描述是短时空间余量修复，不是一个已经观察到的能量循环。

hmasd-pro-question-usa-b06-next…

这个区别不是措辞保守，而是下一比较的实际依据。源码中的 margin 同时受电量和到站距离影响；移动可以降低估计返航需求，却继续消耗储能。最低电池变差不自动推翻原生 J 收益，也不能被“返航成本接近零”抵消掉。

B03 的辅助预测反证和 B04/B05 的服务—风险取舍仍成立。指定主线计划要求把风险收益、服务损失和最低电池一起读；B06 的新结果加强了简单执行对照的地位，而没有为旧 MSE 头或固定系数 4 配方提供重开理由。

二、一个源码推论使长时比较具有不同于重复 B06 的价值

对当前有有效站点的 S2 条件，源码中的 raw margin 可写为

m
i
	​

=b
i
	​

−κd
i
	​

−0.1,κ=
v
limp
	​

3600C
battery
	​

P(v
limp
	​

,0)
	​

>0.

这里 d
i
	​

 是最近站点的三维距离，b
i
	​

 是电池比例。F 的退出条件是 m
i
	​

≥0.05，所以已触发 F 的成员要退出，必须满足

b
i
	​

≥0.15+κd
i
	​

.

这是由已读源码和固定 F 规则直接推出的必要条件，不是新增控制阈值。电量低于 15% 时，即使把距离缩到零，也无法仅靠几何移动满足退出条件；在现有能量模型下，需要实际净补能才能重新达到该退出余量。电量达到 15% 也不是充分条件，因为距离项仍在。

hmasd-pro-question-usa-b06-next…

B06 中观察到的覆盖段短、margin 很快恢复、没有到站，符合“当前储能尚容许通过缩短距离退出反馈”的范围。它没有回答储能进一步下降后，固定规则会表现为持续返站、成功补能、短促反复出入，还是服务中断。这正是一个不同的、可观察的用途问题，而不是已证明 F 有缺陷后寻找修补。

源码还给出不能略过的条件：每步先根据实际运动耗能，再决定充电；只有合法 docking 请求、位置与速度条件满足后才有充电资格，站点容量和选择次序仍会约束实际获得能量的成员。到达附近、发出请求、成为候选、获得输入能量、净电量恢复，是不同事件。

因此，我选择 H3000 来观察这个规则在更长任务中的后果，但不预测 H3000 必然到站或完成循环。它将原生任务时长加倍，同时保留原电池、初始比例和全部物理条件，是一个明确且有限的新任务范围；不是从试跑中挑选出的“恰好出现充电”的时长。不能依据 B06 的平均耗电斜率线性外推新轨迹，也不能在 3000 步没有事件后自动延长。

三、时间信息改变是实质代价，但不使这项用途比较失去意义

必须接受附件指出的区别：current_step/max_steps 进入 actor 观察和中央 state，等待时间也以 max_steps 归一化。将 max_steps 从 1500 改为 3000，时间推进后的同一物理时刻会给出不同时间比例。因此，不存在“头 1499 步闭环动作应完全重现 B06”的合理合同。初始时刻时间比例同为零，也不能据此推导后续历史相同。

hmasd-pro-question-usa-b06-next…

还有一个奖励边界区别：原生 PBRS 在 episode 结束时把下一势函数置零。H3000 在第 1500 步通常尚未结束，所以即使人为固定了相同物理动作前缀，第 1500 步的终端 shaping 处理也不能照搬 H1500。新任务可以保持同一个原生奖励函数，却不保持旧截断位置的奖励序列。

这些差异限制的是机制归因，不妨碍下面这个直接比较：

在共同的 H3000 原生时间信息、终止规则和世界下，同一份冻结 N 参数，使用 F 相比 O 是否仍改善完整任务用途？

O/F 都接受相同的新时间定义，因此其 H3000 内部的反馈包对比仍明确。但 H3000 结果相对 B06 的变化，会同时包含时间信息、延长的历史与能量暴露、后续访问轨迹及终止边界的影响，不能归因于其中一个因素。

我不建议额外加入“保持 1500 时间分母但跑到 3000”的臂。它会引入新的观察干预，甚至涉及时间值是否裁剪等选择；当前决策又不是估计纯粹的时域因果效应。为了获得一个并非本题所需的分解而追加整组运行，信息价值不足。

最强的反对意见与替代

**最强替代是止于当前 H1500 的有限用途，暂不新增计算。**B06 已得到可保留结果；H3000 要付接近两倍 B06 的评价工作，还可能主要暴露冻结策略对新时间信息的敏感性，而不是给出一个可直接修复的能量问题。即使出现充电，一次有限 episode 也不能证明持续循环。这个反对理由比“应该再找一个新网络”更有力。

我仍支持 H3000，是因为这条方向当前的用途问题包含持续服务与返航风险，而 B06 的正结果恰好尚未跨入实际补能阶段，并伴随更低储能。**若研究用途明确只限于现有 1500 步任务，停止计算会更合适；但按本次提出的持续服务问题，H3000 能改变是否扩大 F 的使用范围，以及下一步是否真的存在值得学习的缺口。**这不是算出的最优资源配置，而是对信息价值和机会成本的判断。

目前不优先选择新学习比较。低绝对 QoS 和未充电，并未定位到一个预测、critic 或技能学习瓶颈；已有 F 又构成了比只用 O 更强的执行参照。新的学习候选必须说明在这个参照下还要改善什么，不能仅重复“胜过 O”就宣称解决了当前问题。现阶段购买另一对完整训练，会同时增加学习变化和执行适应，而对当前能量循环缺口的解释未必比直接长任务更清楚。

四、建议固定的最小完整方案
制品与对照保持不变

保留 B04 N／seed914021 和 B05 N／seed914173 的真实 update30 最终 checkpoint；各自都有历史 180k 训练，但此次不增加任何学习。每份制品分别执行 O 与 F，使用全部 development937001–937008 和 final938001–938032。两套面板、两个来源各自保留，不选择较强制品、已知触发世界或最有利面板。

hmasd-pro-question-usa-b06-next…

O 是该冻结策略在 H3000 下的正常闭环执行，不是旧 O1500 数组。F 完全复用 B06 的进入／退出、当前最近站点、速度转换、第四维请求和原 backhaul guard 例外；不因预计低电量而改成提前触发、到站充满、固定站点或预约排队。未覆盖时，继续使用 actor 基于当下 F 实际历史产生的命令。

hmasd-pro-question-usa-b06-next…

严格区分训练身份与评价配置

先按原 1500 步保存配置核验源制品及 checkpoint 身份，再构造独立的评价配置副本。**源训练配置仍是 1500；新评价的 episode_length 与实际环境 max_steps 显式设为 3000。**冻结 B06 的 source verifier 和生产入口不能直接当作一个可任意改时域的执行器，也不应为新问题放宽旧 B06 身份检查。需要独立的后继入口及来源版本，保留训练身份、评价差异和输出定位。

hmasd-pro-question-usa-b06-next…

评价所需的单环境配置、buffer 分配及由配置计算出的尺寸应按实际初始化路径处理并记录。它们不能静默覆盖 checkpoint 的训练身份，也不能触发训练存储、optimizer 更新或 normalizer 更新。核心匹配条件继续是 S7-S2、N8、k10、原生奖励系数 2、相同信息权限、初始电量分布、充电与动作物理、CUDA FP32／TF32 off／四线程。H3000 不增加低电量开局、故障、强制队列或特殊站点。

hmasd-pro-question-usa-b06-next…

连续运行，不在旧边界重置

actor 每步在真实新观察上运行，技能按原 k10 时钟刷新；F 模式、GRU 和技能状态只在原生 episode reset 时重置。第 1500 步不是新 reset、不是保存后重新开始，也不是清 buffer 后重建历史的人工边界。冻结 agent 的固定技能时钟本身不要求在 1500 步结构性复位。

每个 episode 到 3000 步原生截断，或按未改的物理规则提前终止。成员切断、耗尽或失去服务不能成为剔除世界、重新开局或人为延长的理由；全体电池耗尽造成的原生提前终止也必须保留。O/F 的实际长度可以不同。

在新 H3000 内，O/F 仍应有匹配的外生世界与随机性绑定，首次实际覆盖前的可比诊断前缀仍可用于检查实现。**这个检查属于新比较内部，不是要求重现 B06 的旧前缀。**正确性工作集中于新配置确实传入环境、时间与终止一致、跨 1500 连续运行、真实历史、身份及零更新，不需要另加一个“必须先充电成功”的 pilot。

五、主读数是完整用途，能量循环需要另外读清楚

对来源制品 b、面板 p，主对比保持为

D
b,p
J
	​

(3000)=
∣W
p
	​

∣
1
	​

w∈W
p
	​

∑
	​

[J
3000
	​

(N
b
	​

+F,w)−J
3000
	​

(N
b
	​

+O,w)].

final32 是每份制品的主要用途面板，development8 约束范围；四个格子分别报告。原生 J 按各自实际 episode 的全部奖励求和，保留全部世界、差值、绝对水平和损失尾部，不将两个来源或两个面板池化成一个掩盖相反结果的均值。H3000 的总 J 不能直接与 B06 的总 J 相减，称作“多运行 1500 步的收益”。

服务与提前结束

同时报告累计交付量、累计 QoS、实际每步服务、实际 episode 长度，以及零服务 episode 和不利世界。为比较计划中的 3000 步服务窗口，可另报

S
H
	​

=
3000
1
	​

t=0
∑
L−1
	​

q
t
	​

,

其中 L 为实际执行长度。它只是将已经交付的服务按共同任务窗口归一化，不补造未执行的奖励或轨迹，也不替换原生 J。这样，提前耗尽后因少承受后续负奖励而较高的 J，不会被误写成更好的持续服务。

已有逐步记录可以按预先固定的前／后 1500 步及 250 步分段描述，不增加环境调用。未进入后半程的 episode 标明其暴露长度，不能把“后半程未观察到风险”当成安全。也不能事后选择最有利时间段替代完整终点。

储能、充电与返回服务

这里最重要的新增记录是逐成员的能量账：初始与实际电池比例、实际消耗 Wh、输入 Wh、实际净储能变化，结合已有 margin、距离、覆盖命令和真实运动。再记录进入 docking／capture、获得充电资格、实际获配站点、等待、充电开始结束、退出反馈和后续服务的时间关系。源码中先耗能再充电，且所谓净充电字段有自己的截断定义，故不能只累计“有充电”标志来替代真实电池恢复；能量核对应服从原代码的容量限制和最终裁剪。

对“循环”的证据应分层描述，而不合成一个新评分：

**到站或一次正输入能量，只证明发生了该事件。**更有用的循环迹象是，同一成员完成实际净储能恢复，随后退出返航／充电状态，并在剩余任务中重新参与有服务的联合运行。队伍总服务恢复不自动证明该成员的独立因果贡献；没有相应链路／交付记录时，不作这个归因。即使观察到若干次循环，也只支持该有限时域，不能声称稳定的无限持续服务。

这类描述复用现有轨迹，只增加决定问题所需的能量和事件字段；不必为此另建全观察回放、额外 probe 或 oracle 路径搜索。诊断允许读取环境实际状态作事后核验，但那些额外记录不得成为 F 或 actor 的新输入。

六、先于结果的预测，以及哪些结果改变投入

中间预测不是“必然充电”，而是：在更深的能量消耗下，固定退出规则将使空间修复与净补能之间的区别显现。可以观察其是否变成更长的连续覆盖、逐步接近站点、实际补能后退出，也可能观察到撤离服务区、等待、反复出入或无法恢复。低于退出必要储能条件之后，仅靠距离缩短不能解释模式退出；若没有净补能却出现这种结果，应先核查实际输入和规则实现，而不是给出新的科学故事。

原生用途预测是：F 在共同 H3000 条件下仍能通过减少真实返航成本，保留累计服务并改善完整 J，而不是把成本降低换成更早服务中断。最强相反预测是：B06 的几何修复只在当前储能窗口内有利；在更长任务中，额外耗电、返站驻留、站点竞争或新时间信息引起的轨迹变化，使服务或净用途明显恶化。仅凭这种恶化出现，仍不能从上述原因中任意挑一个作为已识别机制。

固定 H3000 观察	对判断及下一笔投入的影响
两来源主要面板仍有值得保留的 J／成本增量，累计服务相容；同时观察到净补能及后续服务恢复	扩大这一个包的有限长任务用途，并记录实际出现的能量循环。不是新学习成果、总体安全保证或自动确认；也不因此必须购买一个学习模块。
J／成本改善，但累计服务、服务空窗或提前结束明显更差	保留原生风险账面的收益，但不判为持续服务成功。不能以少运行造成的低成本掩盖失败；默认不继续扩展这套固定 F 的长期用途。
F 实际改变路径却没有净用途，或两来源／两面板出现实质反向	缩小 H3000 的使用判断，保留 B06 原有 H1500 结果。新任务阴性不能追溯抹掉旧阳性，也不自动授权改阈值、速度、驻留或站点协调。
H3000 服务仍有用，但没有到站充电，或没有足够的低电量／反馈激活	最多得到 H3000 的有限用途，能量循环问题仍未被充分检验。不加长到事件出现为止，不制造低电量开局，也不把非激活算成活跃机制失败。

技术无效另行保留其尝试、输出和成本，不计作科学阴性。需要真正解释不同科学后果时，才从实际证据选择新的问题；当前没有自动排队的训练、规则修订或确认。

我不从 B06 的效果幅度反推出一个服务容忍百分比，也不把任何微小正差视作保留资格。最有说服力的模式仍是完整 J 有用、累计服务得到保留、真实风险与储能后果可接受地同时呈现；当这些分量冲突时，报告实际幅度、损失世界和任务范围，不用一个后选综合分数消除冲突。

七、成本与推断范围

所选完整比较的上限是

2 来源×2 执行规则×40 世界×3000=480,000

评价团队 transitions，160 次 episode 尝试、3.84M 成员步观察；0 新 fits、0 更新。按 B06 的 99.300211 runner 分钟及相同吞吐简单外推，约 198.6 分钟只是工作量尺度，不是未来运行时间承诺；低电量逻辑、充电、存储和节点并发可能改变实际成本。源制品既有训练是历史成本，后继实现、检查、必要审阅、收取和完整判读另外记录。

hmasd-pro-question-usa-b06-next… +1

我保留四组 O/F 面板，而不再附加一个 H1500 重跑网格。新 O3000 必须真实执行，不能用旧 O1500 替代；删去旧开发八世界会省下部分工作，却丢掉这个方向此前反复出现相反用途的范围约束。若只关心单一制品的窄部署，确实可以做更小研究；但那不是本次保留两个来源、两个面板的判断。

这仍是两份固定历史策略上的任务迁移／执行比较。80 个配对世界、160 个 episode、更多时间点和成员观察，都不增加训练复制数。旧世界继续是已曝光开发条件；不因 horizon 新了就变成训练方法的 held-out 确认。将来若选择训练程序的总体主张，仍需实际 claim、匹配主对照、选择曝光和独立新训练批次；本问题没有选中那一步。

hmasd-pro-question-usa-b06-next… +1

八、来源边界与最终判断

本答复使用附件指定的三组版本：2c73e4c420773ce0b0991bb53f105bcd24c762cf 的新问题、完整 B06 条目、80 个配对世界及前次完整咨询／采纳记录；4f1f1f9eecf00c4218d827033bf858dd7f79a740 的治理、方法及共享背景；f92a94b017816467662115dbbc1409793858613c 的冻结反馈、制品身份、评价、时间输入及能量／充电代码。B06 的 config、summary、manifest 和退出记录已取得；summary 核对用于实际计数、聚合及身份，不冒充新的原始数组重算。

**没有取得并独立复核仓库外 NPZ／checkpoint。**B06 的“数值差 0”、原执行数组复现和诊断前缀一致，归属于已读 DM 核验；完整 actor observation/state 数组未保存，也不能被本答复升级为已经完成的逐数组输入审计。未实现的 H3000 接线、实际充电／恢复行为和新成本仍是未决事项，不以记忆补全。

hmasd-pro-question-usa-b06-next… +1

**最终建议：只购买一次 H3000 原生长任务的 O/F 比较，接受并明确记录其时间信息改变；以完整服务、风险和能量过程决定是否扩大当前反馈包的有限用途。**B06 已经提供了一个有力的简单执行参照。现在最值得弄清楚的是它在更深能量消耗下实际还能做什么，而不是先替它发明学习缺陷。若长任务只留下风险账面节省、却损害持续服务，或仍未产生所需暴露，就按该范围结束本次投入，不自动加时长、改控制或转入训练。

## 2026-09-23 — H3000 advice adopted: fixed B07 native long-task O/F comparison and L0

### Decision and working explanation

The complete [B06 next-investment advice](#pro-question-2026-09-23-b06-feedback-use-and-next-investment)
is saved verbatim above at `1ee90f44b` after same-key delivery verification; its reported hash
was the unchanged target blob, not a writeback commit. The accepted question was not resent.
The collected event was consumed with generation 85 / wake `d0f606a8-e06d-462c-a5fb-403a2e7b4d6d`
/ event `7b615876462450cb9d1696ac`, advancing observation to 86. The operation's tab was already
absent; unrelated tabs and the browser were preserved. There is no outstanding Pro producer.

Adopt Pro's single fixed H3000 comparison. MATERIAL_DISSENT is no; agreement is advice, not
new empirical evidence. This is a successor study, not an extension or rerun of the completed
B06 batch. Current published background at
[`8810bcc10978941638470aec79460faf1e4ff0c0`, RESEARCH topic 6](https://github.com/CartmanFatass/My-paper-code/blob/8810bcc10978941638470aec79460faf1e4ff0c0/docs/research/RESEARCH.md#6-实证研究是在具体条件下缩小解释空间)
changes the choice concretely: B03 did not repeat auxiliary-package gains; B04/B05 risk training
traded away service in consequential worlds; B06 made the unchanged N checkpoints a stronger
simple executable comparator. No identified predictor, critic or skill bottleneck presently
justifies buying a new learning module. Preserve all those adverse results and the two-block,
already-exposed-world limits. Main's owner pause is lifted; the active direction and its exact
lead `Codex DM (independent session)` are unchanged. Current constitution section 2 authorizes
this independently selected, prospectively declared continuation.

B06 strengthens finite H1500 feedback-package usefulness, weakens the claim that this
information necessarily forces a service-for-return-cost exchange, and leaves sustainable
energy recovery unresolved. Its shorter return distances improved margin while every active
move consumed battery; charging never activated and battery tails worsened. The strongest
alternative is to keep that bounded result and spend nothing further. I choose B07 because
sustained service belongs to this direction's question, and the fixed rule makes a discriminating
prediction when stored energy becomes low: under the native margin `m=b-kappa*d-0.1`, `kappa>0`,
exiting at `m>=0.05` requires `b>=0.15+kappa*d` (up to observation rounding). Below 0.15,
shrinking distance alone cannot restore the exit margin. This is a necessary condition for
this existing controller, not a new threshold or evidence that H3000 will reach it.

The expected intermediate difference is that F continues to reduce the native return-margin
penalty, with later low-battery exposure potentially producing longer return modes, station
arrival/admission and genuine battery replenishment rather than B06's short geometric repairs.
The useful-package prediction is compatible cumulative service and native J gains on each final
panel, with actual energy/service sequences explaining the scope. It can fail through stranded
return modes, waiting, service gaps, early exhaustion, adverse worlds, or absence of that exposure.
A positive J alone does not satisfy the sustained-service question.

### Consequential source checks and changed task semantics

The read-only source bridge verified `energy_aware.py:581-625,944-952`: the terminal/truncation
transition sets PBRS next potential to zero. In H3000 the old t=1499 transition is nonterminal
unless endogenous termination occurs; the terminal boundary is now t=2999. In addition,
`routed_core.py:4169-4171,4906-4908` supplies `current_step/max_steps`, and
`energy_aware.py:2243-2257,2318-2320` uses `waiting/max_steps`. Thus policy inputs can differ
from the start, and the old reward boundary changes even under a hypothetical identical physical
prefix. B07 is the native H3000 task comparison, not B06's unchanged trajectory continued for
1500 steps or an isolated causal test of greater energy exposure. No denominator ablation is added.

`energy_aware.py:1762-1833,1843-1889` consumes movement energy before charging, applies station
capacity, then clips battery into [0,1]. Per-member `last_net_energy_charged_wh` is
`max(0,actual_charge_wh-consumed_wh)`; it is not the signed stored-energy delta. The successor
will read exact physical pre/post battery and per-member consumption/input postdecision, retain
capacity and clipping residual, and verify their accounting. Flags or arrival alone cannot be
called recovery. These arrays are measurement only; F continues to use only legal actor observations.
No shared environment/observation/reward/controller code is changed.

### Frozen comparison, exposure and stopping rule

- Two retained N final checkpoints: B04 training seed 914021 and B05 training seed 914173;
  all source digests and original H1500 training identity remain those of the B06 bindings.
  Verify original summary/config/checkpoint/retained-trace hashes with the unchanged B06 verifier
  before deriving a separate evaluation config. No parameter, optimizer or normalizer update.
- For each checkpoint, newly execute O3000 and F3000 on development `937001..937008` and final
  `938001..938032`. Two blocks, two modes, two panels: 160 episode attempts, **0 new fits,
  0 optimizer updates, at most 480,000 team evaluation transitions and 3,840,000 member-step
  observations**. Actual early termination shortens exposure; never pad, replace or silently retry.
  No new worlds, checkpoint search, training, auxiliary loss or extra H1500 evaluation.
- Evaluation copy sets only `episode_length=max_steps=3000`, one evaluator lane and its derived
  buffer sizes. Preserve the complete saved training config separately, record every evaluation
  config difference and derived size, and retain saved training exposure as historical identity.
  No storage insertion/update is performed merely because an evaluator buffer exists.
- S7-S2, N8, k10, 30 users, native return coefficient 2, battery/charging physics, stochastic
  streams, legal information, action wrapper, deterministic actor, CUDA FP32, TF32 off and four
  Torch threads remain matched. Expected actual node is configured `wsl_4070`.
- F is imported unchanged from frozen B06: own legal margin enter <=0, exit >=.05, per-member
  hysteresis; current nearest valid physical station (lowest-index exact ties); >160m return
  command with existing 30m/s horizontal and 5m/s vertical normalization, <=160m dock command,
  fixed fourth command component 1. No full-charge arrival rule, lower battery threshold,
  station coordinator, capacity reservation, speed tuning or altered backhaul guard.
- Each mode owns its actual policy observation/history. Native actor GRU, team/individual skill
  clocks and F modes reset only at the episode boundary, never at step1500 or mode entry/exit.
  Each episode ends at native exhaustion termination or H3000 truncation. O and F may have
  different lengths. Run all fixed cells once even if an earlier result is adverse; technical
  exceptions stop the attempt, preserve its cost and partial outputs, and require reconciliation.
- Check O/F common prefixes within the new task through the first actual submitted-command
  difference. Do not assert H3000 reproduces H1500 O arrays. Preserve immutable policy,
  optimizer counters, normalizer state and RNG through evaluation.

Dominant work is the 160 fixed rollouts: at most twice B06's 240k evaluation transitions;
there is no nested search, branch rollout or model fitting. B06's 99.300211 runner minutes
suggest approximately 198.6 runner minutes before instrumentation/resource variation, not a
deadline or promised speed. Record actual preparation/check cost, wall, CPU, runner RSS scope,
artifact bytes and actual transition counts; missing resource measurements remain unknown.
The batch ends after these fixed episodes or a technical failure. No adaptive horizon extension
until charging, no tuning to a world, and no automatic third block/confirmation follow.

### Readout fixed before outcomes

Keep B04/B05 and development/final as four separate comparisons; final32 is primary within
each block, development8 remains a scope check. The primary native estimand is total raw J over
actual episode length, with absolute levels, per-world paired differences, losses, medians and
extremes. Never pool blocks to erase disagreement or subtract B06 H1500 J as an extra-half causal gain.

Read cumulative QoS and delivered throughput, actual per-step service, actual length, terminal
kind, zero-service episodes, service-free intervals, lower tails and all adverse worlds. Also
report planned-window service `sum(q_t)/3000` and throughput `sum(T_t)/3000`; these are fixed
budget denominators, not invented post-termination trajectory/reward or replacements for raw J.
Report first/second1500 separately and twelve fixed 250-step bins with actual exposure; a
missing second half is not evidence of safety or equal service. Retain return-cost/raw margin,
cutoff/depletion, minimum battery and tail readings alongside service.

Retain B06's action/mode/geometry/skill traces and add exact per-member energy accounting:
physical initial/pre/post battery and 160Wh capacity, consumed Wh, charger-input Wh, native
clipped-positive net-charge field, signed stored-energy delta and capacity/lower-bound clipping
residual. Record request, chosen native station, capture/arrival, charging eligibility,
admission/actual charge, wait age, station occupancy/queue, charge start/end, F entry/exit and
later positive *joint* service. Raw traces must allow reading the same entity through arrival,
net stored replenishment and later service; do not invent an energy-cycle composite score or
attribute joint service to that member without link/throughput ownership evidence. End-of-episode
unfinished intervals remain censored. Additional physics never becomes an actor/critic/F input.

Outcome branches:

1. Compatible cumulative service and useful J/cost on both final panels, with actual net battery
   replenishment followed by later service, would extend this package's finite H3000 use; it
   would not establish general safety, training-method superiority or automatic confirmation.
2. J/cost savings with consequential cumulative-service loss, gaps or early ends support only
   bounded risk bookkeeping, not sustained service; default to ending this F long-use extension.
3. Activated path change without useful package performance, or material block/panel reversal,
   narrows H3000 use while preserving H1500's bounded evidence; no automatic rescue tuning.
4. Useful H3000 readings without enough low-energy/charging exposure retain only finite task
   use and leave energy-cycle claims unresolved; no automatic extra horizon or low-battery setup.
5. Technical failure is separate from scientific failure; preserve actual cost and narrower
   reliable observations, reconcile before any newly declared repair attempt.

No tiny-positive success cutoff, service/safety tolerance, MEI or population-confidence claim
is manufactured for this exploration. All prior selection exposure and zero new training
replication remain explicit.

### L0: successor-only evaluator and measurements

Deliver one admission-guarded B07 entry and evaluator for the exact comparison above. Owned
code: `experiments/candidates/uav_service_auxiliary/b07/`,
`scripts/run_uav_service_auxiliary_b07.py`, mirrored tests under
`tests/experiments/candidates/uav_service_auxiliary/b07/`. Reuse the immutable B06 controller,
source verifier and appropriate small helpers; preserve all B01–B06/shared sources and historical
outputs. This scoped evaluator may copy the existing rollout path where instrumentation and
H3000-specific summaries require it; no general framework or runtime monkeypatch of frozen code.
Only the DM edits NOTES/main publication and stages/commits in this checkout. An assigned
Implementer owns only those B07 paths, performs no result launch/Pro/science, and returns diff,
checks, deviations and risks. It is not alone in the checkout and preserves other edits.

Required focused evidence: separate saved H1500 identity vs evaluation H3000 config (including
rejected source mutations), actual native time/PBRS terminal behavior, no reset/update at1500,
unchanged F semantics, exact energy accounting including capacity clipping and charging with
negative net change, unequal/early lengths and empty second-half bins, complete partial-failure
counts/traces, policy/optimizer/normalizer/RNG immutability and pre-change paired prefixes. Use
small native/fixture paths plus the actual-node CUDA check appropriate to the changed surface;
these are correctness checks, not a positive charging pilot or extra scientific panel. An
independent Reviewer checks the evaluator/result identity and recurrent/measurement boundaries;
the DM reads and accepts. Commit and push exact inputs before guarded detached execution,
retain accepted process handles, then arm the same native status operation with hmasd_wait.

## 2026-09-23 — B07 evaluator accepted locally; actual-node CUDA check remains

The DM accepts the bounded Implementer's three new B07 files against the preceding L0 and
has read the code and focused checks. B01–B06, the shared environment, agent, config and admission
code remain unchanged. B07 imports the existing controller and original source verifier;
H1500 source identity is checked before deriving H3000/one-lane evaluation, with exactly the
seven recorded differences: episode_length, max_steps, num_envs, batch_size, buffer_size,
low_level_buffer_size and high_level_buffer_size. high_level_batch_size remains 128.
The Implementer also ran the unchanged verifier against both real retained B04/B05 source
sets; both passed all bound artifacts and derivation, with only the already permitted unused
baseline-path difference. This did not execute new scientific episodes or train a model.

The independent Reviewer found a real draft failure-preservation defect: later environment
construction/close, world summarization or final immutability exceptions could discard completed
panel arrays; derived ledger rejection could lose available telemetry from a counted transition.
These were repaired before any result launch. Raw native service and physical pre/post energy
inputs are captured before derivation; the whole panel lifecycle persists accumulated arrays on
failure. Regression fixtures retain a returned transition after ledger rejection and the completed
first world when the second environment constructor fails. Derived and raw arrays remain
separate when validation fails, with INCOMPLETE/failure metadata, not a fabricated valid row.
The new test filename was made unique after an initial combined-collection module-name collision;
frozen B06 tests and repository pytest settings were not changed.

Implementer checks: B07 10 passed / 1 CUDA skip in 5.48s; standard combined B06+B07 21 passed /
3 CUDA skips in 6.77s. Independent Reviewer reran the stable combined suites: 21 passed /
3 CUDA skips in 6.63s, and verified the final source digests. It reports no remaining material
finding. The DM adopts that engineering result, not a scientific outcome. Code compilation and
whitespace checks passed. The next required check is the actual-node CUDA case; no production
B07 batch has started at this entry. Test/support work is not a new fit; implementation/review
wall and aggregate support CPU were not separately instrumented and remain unknown.

Coverage is deliberately stated at its actual level: the 1500-crossing clock/reset check uses
a 3000-step fixture; the real native boundary/PBRS checks are short executions with controlled
clock positions. The unchanged real agent reset/step and time/wait-denominator source paths
were read, not represented as a newly tested 1500-step native GRU replay. The short real native
O-path test checks equality against the frozen evaluator, policy/normalizer/optimizer invariance
and Python/NumPy/Torch RNG restoration; CUDA is skipped on this CPU host. The B07 source-mutation
fixture mocks the unchanged verifier and rejects a horizon change; actual artifact verification
above is the Implementer's separate run, not an independent corrupt-artifact test. Existing
B06 feedback/real mode-transition evidence is reused without claiming new training replication.

Stable reviewed SHA-256: `b07/native.py` =
`0e99410d74943a7566e1d9437a74f488d7c4f6f114414360122402024e8f63e7`;
B07 entry = `3a1ebe8218bd61b471e11272bbc187931fd8a9b7b7c0f391050c2ee50acabb56`;
B07 test = `a1dcd00addeab3d67da694eea8a5d63906b6a01a22b344b884353dc829e00b8a`.
These are code-check identities, not another result record.

## 2026-09-23 — B07 actual-node CUDA check passed; fixed batch admitted and observed

The exact published source `47d56c9bcdc9fa9d6edee43ae0b4d44755115708` passed the remaining
actual-node check on `wsl_4070` / `LAPTOP-U9TDKC8A`, using Torch 2.7.0+cu118 and the NVIDIA
GeForce RTX 4070 Laptop GPU. The focused case
`test_h3000_native.py::test_real_h3000_loop_keeps_checkpoint_rng_and_normalizers_immutable[cuda]`
passed: 1 passed, 14 dependency deprecation warnings, 4.66 seconds, exit 0. CUDA availability
was asserted before testing; the case did not silently skip. FP32, TF32 disabled and four
threads match the production binding. Source status was clean before and after the check.
This closes the CUDA engineering check above; it does not extend its stated short-path coverage.

The fixed B07 launch was submitted once through the configured `agent-task` supervisor and
accepted by `hmasd_launch.py` at `2026-09-24T04:57:19.859770Z`. Native admission observed current
main `d2e34d45c724c4248e5966d6c323afdda02b31e9`, the unpaused active direction and the exact lead
`Codex DM (independent session)`. Its fresh actual-node preflight measured 14,547,607,552 bytes
available against the 4,294,967,296-byte floor and passed. Main was refreshed again before this
record; the relevant owner-control and direction records had not changed.

The launch binds the preceding fixed H3000 O/F design, both retained B04/B05 N sources, CUDA,
four threads and zero new fits/optimizer updates. The cap remains 160 episode attempts and
480,000 team transitions, subject to native early endings or actual technical failure. No
additional panel, controller adjustment, restart or replacement episode is authorized by this
launch observation. Actual scientific cost and results remain pending.

Runner-written admission artifacts were copied byte-for-byte to
`runs/uav_service_auxiliary/b07_of_a01/`: `launch-manifest.json` (4,363 bytes; SHA-256
`92d98535aaf2c6b31b9ca700cf578d480a42b465f84ff23a5363ad7bb1657edf`) and
`admission-preflight.json` (765 bytes; SHA-256
`6cddd4488cbab27594b688128afb6222e5f829c5792848b732088ddef33afe75`). The immutable result source
and durable output root are `/home/wu/hmasd-worktrees/usa-b07-47d56c9bc` and its
`runs/uav_service_auxiliary/b07_of_a01/`. Preserve that manual worktree and its outputs.

The accepted operation is
`/home/wu/projects/HMASD/.git/hmasd-admission/b0a21e1561c71e2544e1ee5b291b6c50879ec313bc69851232e8a6dcd08f6b93.json`.
Its native supervisor is PID 488398 / start ticks 58534548; the runner is PID 488399 / start
ticks 58534550, both in session 488398 under boot ID `bb732fcb-1a33-4659-a786-331110ae41d3`.
Read-only native status confirmed accepted admission, consistent records and both matching
identities running; no process-exit witness was present. The outer task
`usa-b07-admit-47d56c9bc` finished successfully after admission, which is not completion of B07.

Detached read-only observation `launch-usa-b07-of-a01` now follows that same operation in this
assigning session's existing hmasd_wait state. Generation 87 / observer PID 3072710 uses a
30-second probe interval and 1,500-second window. The first adopted observation at
`2026-09-24T05:02:56.694335Z` confirmed the same running identities with zero probe errors;
there were no pending events. A completion, error or bounded checkpoint returns control here
for evidence reading and exact-generation rearming. A present live summary or successful
process exit will not be treated as scientific acceptance. The earlier Pro answer has already
been read fully, saved verbatim and published with the prospective plan; no Pro operation is
pending and no question was resent.


## 2026-09-24 — B07 complete: native H3000 feedback restores energy with material service-loss worlds

### Accepted execution, evidence and cost

The fixed [B07 prospective design](#2026-09-23--h3000-advice-adopted-fixed-b07-native-long-task-of-comparison-and-l0)
is complete at immutable source `47d56c9bcdc9fa9d6edee43ae0b4d44755115708`. The same admitted
operation exited 0, with valid native exit witness and both recorded process identities absent.
All eight panels are COMPLETE: 160 attempts, 480,000 actual team transitions and 3,840,000
member steps; all 160 episodes reached native H3000 truncation, with no early ending, retry,
replacement, extension or omitted world. New fits, optimizer updates and independent training
replications are all zero. These are the two existing B04/B05 N policies, originally trained
for 180,000 transitions each at H1500; their learning is historical, not newly replicated here.

The DM collected all 16 files (750,519,657 bytes) and matched every SHA-256 against the terminal
actual-node files. The runner's output_bytes is 750,519,107; the additional 550 bytes are the
subsequent native process-exit witness. Summary SHA-256:
`a33d88cd3c0c9309983a69dac92d373b4516843c3ed28c379468506a59085d36`.
The runner used CUDA FP32, TF32 disabled and four Torch threads. Actual runner wall was
13,832.5682585 seconds = 230.5428043 minutes; CPU user/system were 13,510.072504 / 334.839316
seconds. Peak RSS was 2,058,460 KiB for the B07 runner process only. The 198.6-minute forecast
was a workload estimate, not a scientific endpoint; the declared transition budget did not change.
Collection and total authoring/support wall were not separately instrumented and remain unknown.

Compact, unchanged runner-written JSON is retained in
`runs/uav_service_auxiliary/b07_of_a01/` (summary, config, admission and terminal records).
Bulk NPZ and logs remain outside Git, both in the authoring checkout at that relative path and
at durable node `wsl_4070` / host `LAPTOP-U9TDKC8A`, root
`/home/wu/hmasd-worktrees/usa-b07-47d56c9bc/runs/uav_service_auxiliary/b07_of_a01/`.
The source is a manual worktree containing required outputs, not a disposable admission snapshot;
it is retained. Neither copy may be removed without verified recovery elsewhere.

The DM read the complete summary and separately recomputed raw metrics, all scalar world
readings, service intervals, both halves and all twelve 250-step bins directly from the NPZ.
The arithmetic reader imported no candidate summarizer or controller: 37,402 scalar/array checks,
maximum scalar discrepancy 7.5634e-15; physical energy-closure error at most 5.5512e-17 in battery
ratio. A further 1,592 aggregate/paired checks had discrepancy zero. Checks cover native
pre/consume/input/clip closure, raw-versus-derived telemetry, unchanged action pass-through,
fixed F hysteresis/commands, battery and mode continuity, actual native truncation and station
capacity. The adapter's Python sum of eight shared rewards was respected; its raw reward and
reward-info scalar can differ by floating-point summation roundoff. No recorded reward was edited.
The raw arithmetic pass took 6.646 seconds locally and launched no environment or learner.

All 80 within-H3000 O/F pre-intervention prefixes agree on the retained actor-action, legal
margin/battery, position, skill, reward/metric and termination fields: 94,527 transition-prefix
steps. No full-observation/state or hidden-state replay claim is added. The seven allowed H3000
config differences and unchanged source artifacts were verified; runner checks preserve each
original policy fingerprint, optimizer counters and normalizers. The code's RNG-preservation
checks and prelaunch engineering evidence retain their actual scope. stderr contains only two
known notices that discriminator buffers were absent in historical checkpoints and replaced by
empty buffers; there are no new discriminator updates in this fixed-policy evaluation.

The READY event was read and consumed using generation 95, wake
`618e825f-aafb-4342-b505-2345aa88d93a`, event `603f33afe762c2542cea4cc3`, advancing the observer to
96. No experiment remains running and this terminal observation was not used to relaunch it.

### Native service and risk, four comparisons kept separate

J is the full raw native episode sum. QoS is the actual-step mean; because every length is 3000,
it also equals the prospectively fixed planned-window service. Throughput is delivered Mbps.
No H1500 score is subtracted to interpret a causal extra-half gain. H3000 changes native time
inputs and the PBRS terminal boundary from the outset, as recorded prospectively.

| Block / panel | J O | J F | F−O J | QoS O | QoS F | F−O cumulative QoS | Throughput O → F Mbps | J/QoS loss worlds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| B04 / development8 | -2129.970807132 | 1057.256306166 | 3187.227113297 | 0.317626864173 | 0.362227358309 | 133.801482408 | 9.528805925 → 10.866820749 | 0 / 1 |
| B04 / final32 | -2804.180424208 | 976.959893055 | 3781.140317263 | 0.268582607591 | 0.335449392683 | 200.600355277 | 8.057478228 → 10.063481780 | 0 / 5 |
| B05 / development8 | -2529.868024214 | 1042.549140884 | 3572.417165097 | 0.281283443285 | 0.357407117400 | 228.371022346 | 8.438503299 → 10.722213522 | 0 / 0 |
| B05 / final32 | -2656.450673687 | 968.141721500 | 3624.592395187 | 0.286178473198 | 0.334037886410 | 143.578239636 | 8.585354196 → 10.021136592 | 0 / 3 |

All 80 J differences are positive, but this does not imply per-world service dominance. Final
B04 J difference median/range is 3940.010906188 / [1427.792308197, 5571.410321644]; B05 is
3343.831047703 / [2229.295455621, 5084.041092316]. Native return-cost savings dominate these J
increments; the service increases and adverse worlds are reported independently.

| Block / panel | Mean return cost O → F | Raw return cost O → F | Native cutoff/depletion events O → F | Zero-service episodes O → F |
| --- | --- | --- | --- | --- |
| B04 / development | 0.503784967504 → 0.000287429078 | 2.345591437187 → 0.000287429078 | 21/16 → 0/0 | 0 → 0 |
| B04 / final | 0.589177151217 → 0.000244113302 | 2.767881689463 → 0.000244113302 | 119/92 → 0/0 | 1 → 0 |
| B05 / development | 0.552902622780 → 0.000388535265 | 3.112513030275 → 0.000388535265 | 20/14 → 0/0 | 0 → 0 |
| B05 / final | 0.573505430165 → 0.000965636774 | 3.002438339640 → 0.000965636774 | 115/90 → 0/0 | 1 → 1 |

O has cutoff in 79/80 worlds and depletion in 77/80, totaling 275 and 212 native events; F has
zero of both in these same finite comparisons. This is actual exposure to the event path,
unlike B06's all-zero risk-event panels, but is still not a deployment-safety guarantee.
B04 final's zero-service O world 938032 becomes nonzero; B05 final 938021 remains zero in O/F.

The final service losses are substantial in some worlds. B04 has 938002, 938008, 938027,
938029 and 938030; the last loses .194845486708 mean QoS (.271313588378 → .076468101670).
F obtains service during steps 1024–1606 (apart from a two-step gap), then none from 1607
through the end, despite charging beginning at 1946 and 204.166666667 Wh total input.
O first serves at 1759 and continues thereafter. B05 loses service in 938027, 938028 and
938029; 938028 loses .240545271713 (.273223182693 → .032677910980). Its F service occurs only
at 2146–2324; the initial gap grows from 1298 to 2146 steps, and a 675-step right-censored
final gap follows, despite 258.055555556 Wh charger input. These temporal facts do not identify
waiting, native backhaul guards, recurrent history or training-distribution mismatch as the cause.
B05 938021 charges 231.111111111 Wh but has no service anywhere. Energy replenishment is not
sufficient for service restoration.

Maximum service gaps never worsen in the B04 pairs. B05 has three worsened gaps: development
937007, 686→694; final938009, 1496→1516; final938028, 1298→2146. These coexist with lower mean
maximum gaps (final B04 −132.46875, B05 −39.53125 steps); no average erases them.

### Physical energy and finite return-to-service sequences

| Block / panel | Episode-minimum battery mean O → F | F P10 / worst minimum | Mean consumed Wh O → F | Mean charger input Wh O → F | Mean signed stored delta Wh O → F |
| --- | --- | --- | --- | --- | --- |
| B04 / development | 0.000000000 → 0.101548270 | 0.100293555 / 0.100231260 | 1067.067170743 → 1115.969421802 | 1.493055556 → 145.312500000 | -1052.969826032 → -970.656921802 |
| B04 / final | 0.000600029 → 0.103588469 | 0.100688914 / 0.099904440 | 1065.875142477 → 1115.042446599 | 0.286458333 → 165.208333333 | -1044.605602348 → -949.834113265 |
| B05 / development | 0.002266089 → 0.105803768 | 0.100157940 / 0.099766674 | 1066.453579952 → 1144.954835699 | 0.000000000 → 177.465277778 | -1051.690929078 → -967.489557921 |
| B05 / final | 0.002220757 → 0.102438883 | 0.093748167 / 0.086567360 | 1063.325618304 → 1138.186810580 | 0.000000000 → 184.557291667 | -1041.296688018 → -953.629518913 |

Every F world has actual charger input and positive physical stored-energy increments (609 of
640 member-worlds receive input); O charges in only one B04 development world and one B04
final world, and no B05 world. F consumes more native energy on average, not less. Its whole
initial-to-final stored-energy change remains negative; it is neither energy-neutral over the
whole episode nor evidence of indefinite sustainability. O's lower-bound clipping residual is
retained in the raw ledger; native clipped-positive net charge is not substituted for signed
physical stored change. F has no upper/lower clipping event. Minimum F battery falls below the
.1 reserve in 0/1/1/7 worlds for B04 dev/final and B05 dev/final respectively, including the
.086567360011 minimum in B05 final938028; zero cutoff does not certify a reserve invariant.

Same-entity sequences were read from each recorded F-mode interval. All 1500 intervals with
positive input have a preceding native arrival for that member. Of these, 998 exit F before
H3000; every such interval has positive net stored gain from its first actual charger input
until exit (range .230975 to 9.403811111 Wh across panels). 977 then have positive joint team
QoS at or after exit, covering 78/80 worlds. The exceptions to this latter world condition are
B04 final938030 and B05 final938021, described above. This sequence does not attribute joint
service to the recharged member: member-level link/delivery ownership was not recorded.
The other 502 input-bearing intervals remain unfinished at the horizon and are right-censored,
not completed cycles or proof of an eventual failure/success.

| Block / panel | F input-bearing intervals | Exit before horizon | Then positive joint service (intervals / worlds) | Unfinished at horizon | Longest F mode / max wait age |
| --- | ---: | ---: | --- | ---: | --- |
| B04 / development | 137 | 85 | 85 / 8 | 52 | 574 / 89 |
| B04 / final | 594 | 384 | 369 / 31 | 210 | 855 / 86 |
| B05 / development | 146 | 88 | 88 / 8 | 58 | 631 / 108 |
| B05 / final | 623 | 441 | 435 / 31 | 182 | 942 / 110 |

For example, B04 final938001 member0 arrives/receives input at step2211, distance17.182960966m:
battery .137324280579→.138767874329 in that transition (+.230975Wh). It exits at2221 with
battery .151760218079 and legal margin .050193510950; joint QoS at2221 is .391875. B05
final938001 member0 similarly receives input at2311 (distance19.645607018m),
.128196872687→.129640466437, exits2328 at battery .152737966437 / margin .050946719944,
and joint QoS is .832275004207. These are illustrative readings from the complete counts,
not selected experiments. Event indices are zero-based transitions.

F reaches eight simultaneous return modes and station queue length seven; maximum wait ages
are in the table. Admission starts/ends can alternate under native station scheduling and are
not counted as independent complete recovery cycles. Physical nonmovement during many overrides
includes actual docking/waiting; it is not automatically failed commanded motion. These are
possible constraints on service, not an identified causal bottleneck or permission to tune stations.

### Fixed temporal readout and all paired worlds

Both halves have their full 1500 transitions in every episode. Each cell below is the average
QoS O→F; development/final panels stay separate.

| Panel | First 1500 | Second 1500 |
| --- | --- | --- |
| B04/development | 0.258409267273 → 0.260093954303 | 0.376844461073 → 0.464360762315 |
| B04/final | 0.169671915946 → 0.196428948456 | 0.367493299235 → 0.474469836910 |
| B05/development | 0.280840404659 → 0.284559815099 | 0.281726481911 → 0.430254419701 |
| B05/final | 0.210788384556 → 0.218079056979 | 0.361568561841 → 0.449996715841 |

The twelve fixed 250-step bins are descriptive, never substitute endpoints. Entries are QoS O→F.

| Steps | B04 dev8 | B04 final32 | B05 dev8 | B05 final32 |
| --- | --- | --- | --- | --- |
| 0–249 | 0.133856811→0.133856811 | 0.076170792→0.076170792 | 0.164157537→0.164157537 | 0.089311458→0.089311458 |
| 250–499 | 0.186786732→0.186786732 | 0.110360411→0.110360411 | 0.228993776→0.228993776 | 0.161268038→0.161268038 |
| 500–749 | 0.269378776→0.269378776 | 0.162968435→0.163874815 | 0.297802384→0.296418667 | 0.208468075→0.208168075 |
| 750–999 | 0.301018526→0.301018526 | 0.195392668→0.211775096 | 0.333043781→0.330529811 | 0.254293737→0.257331363 |
| 1000–1249 | 0.315877244→0.315990384 | 0.221959823→0.278321381 | 0.330837619→0.330242746 | 0.265325710→0.288310793 |
| 1250–1499 | 0.343537515→0.353532497 | 0.251179365→0.338071196 | 0.330207331→0.357016354 | 0.286063289→0.304084614 |
| 1500–1749 | 0.382982153→0.398149092 | 0.298737469→0.384267431 | 0.333674282→0.383313644 | 0.345776847→0.342653086 |
| 1750–1999 | 0.366406849→0.439904145 | 0.362863680→0.449324665 | 0.339791617→0.394150245 | 0.398876028→0.427850543 |
| 2000–2249 | 0.375579373→0.480107493 | 0.388558789→0.511145145 | 0.308223385→0.471624898 | 0.418288223→0.487700254 |
| 2250–2499 | 0.399850321→0.492981868 | 0.387851084→0.526279151 | 0.276928437→0.463879634 | 0.384557506→0.506402709 |
| 2500–2749 | 0.384506384→0.492160997 | 0.403847731→0.511664099 | 0.230368287→0.412953091 | 0.337990578→0.476714071 |
| 2750–2999 | 0.351741687→0.482860979 | 0.363101043→0.464138530 | 0.201372884→0.455605006 | 0.283922190→0.458659632 |

All pair differences below retain the original panel/world ordering. ΔQoS is the mean ratio,
not percentage points. Absolute per-world levels, energy, intervals, halves and bins are in the
unchanged runner summary and verified raw artifacts.

| Block/panel | World | ΔJ F−O | ΔQoS F−O | Minimum battery O→F | F charger input Wh | Maximum service gap O→F |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| B04/development | 937001 | 2514.189345798 | 0.003104141260 | 0.000000000→0.101669743 | 105.833333333 | 0→0 |
| B04/development | 937002 | 4225.342893795 | 0.138678714884 | 0.000000000→0.101132285 | 130.277777778 | 67→67 |
| B04/development | 937003 | 2175.063753706 | -0.021027703925 | 0.000000000→0.100320253 | 167.777777778 | 0→0 |
| B04/development | 937004 | 3619.065444431 | 0.067654435326 | 0.000000000→0.101507184 | 201.944444444 | 0→0 |
| B04/development | 937005 | 2149.919451777 | 0.042508807436 | 0.000000000→0.105342596 | 119.166666667 | 418→418 |
| B04/development | 937006 | 3224.193519887 | 0.034767974406 | 0.000000000→0.100930282 | 135.555555556 | 0→0 |
| B04/development | 937007 | 4041.284082925 | 0.066365667059 | 0.000000000→0.100231260 | 148.888888889 | 390→390 |
| B04/development | 937008 | 3548.758414059 | 0.024751916643 | 0.000000000→0.101252559 | 153.055555556 | 0→0 |
| B04/final | 938001 | 4397.948116378 | 0.035783909887 | 0.000000000→0.101491546 | 119.444444444 | 0→0 |
| B04/final | 938002 | 2149.047109928 | -0.010449239348 | 0.000000000→0.100856500 | 133.611111111 | 0→0 |
| B04/final | 938003 | 4262.407172106 | 0.188306466139 | 0.000000000→0.101445456 | 226.666666667 | 631→0 |
| B04/final | 938004 | 3889.324785069 | 0.094536343663 | 0.000000000→0.103844302 | 181.388888889 | 699→699 |
| B04/final | 938005 | 4792.089847493 | 0.072788203171 | 0.000000000→0.101063027 | 133.888888889 | 595→595 |
| B04/final | 938006 | 4112.797386889 | 0.097833986511 | 0.000000000→0.101465335 | 168.611111111 | 216→216 |
| B04/final | 938007 | 3920.329694179 | 0.046073916359 | 0.000000000→0.103216212 | 118.611111111 | 337→337 |
| B04/final | 938008 | 4119.662129248 | -0.006533184586 | 0.000000000→0.100996964 | 170.000000000 | 534→534 |
| B04/final | 938009 | 4315.837881304 | 0.079042901374 | 0.000000000→0.107527541 | 134.444444444 | 628→628 |
| B04/final | 938010 | 2372.198756027 | 0.037758264305 | 0.000000000→0.099904440 | 163.888888889 | 0→0 |
| B04/final | 938011 | 3248.476403404 | 0.110835559065 | 0.000000000→0.101219465 | 191.944444444 | 1532→1170 |
| B04/final | 938012 | 3407.598994353 | 0.034609160582 | 0.000000000→0.103514471 | 147.222222222 | 0→0 |
| B04/final | 938013 | 2876.994663024 | 0.009061089415 | 0.000000000→0.109943930 | 172.222222222 | 0→0 |
| B04/final | 938014 | 3535.272147806 | 0.051688362056 | 0.000000000→0.105216261 | 177.777777778 | 438→438 |
| B04/final | 938015 | 5137.903227035 | 0.185610372131 | 0.000000000→0.100811629 | 188.888888889 | 397→397 |
| B04/final | 938016 | 4282.829947477 | 0.053045144408 | 0.000000000→0.113423329 | 207.222222222 | 122→122 |
| B04/final | 938017 | 3298.788091472 | 0.022671678033 | 0.000000000→0.100615758 | 189.444444444 | 1159→1159 |
| B04/final | 938018 | 4789.272060671 | 0.145435185040 | 0.000000000→0.100676491 | 200.555555556 | 1528→1157 |
| B04/final | 938019 | 3468.586137774 | 0.049056324071 | 0.000000000→0.112016520 | 122.777777778 | 285→285 |
| B04/final | 938020 | 4638.782489814 | 0.182652928573 | 0.000000000→0.100800722 | 167.500000000 | 0→0 |
| B04/final | 938021 | 2684.774746572 | 0.024422652983 | 0.000000000→0.103361803 | 125.277777778 | 1018→1018 |
| B04/final | 938022 | 2681.912897304 | 0.022412161793 | 0.000000000→0.107289899 | 158.333333333 | 0→0 |
| B04/final | 938023 | 4819.947259499 | 0.067207471655 | 0.000000000→0.101361340 | 126.666666667 | 552→552 |
| B04/final | 938024 | 4067.859279228 | 0.052890361977 | 0.000000000→0.103433681 | 224.444444444 | 0→0 |
| B04/final | 938025 | 4311.112998140 | 0.044354511133 | 0.000000000→0.107492731 | 158.888888889 | 1259→1139 |
| B04/final | 938026 | 3349.955109420 | 0.045950844321 | 0.000000000→0.100997113 | 161.666666667 | 220→0 |
| B04/final | 938027 | 2511.038331307 | -0.004894553282 | 0.000000000→0.107738082 | 138.333333333 | 327→327 |
| B04/final | 938028 | 5399.706183559 | 0.238501626935 | 0.000000000→0.101405889 | 272.500000000 | 566→566 |
| B04/final | 938029 | 1427.792308197 | -0.011859605173 | 0.019200935→0.100262135 | 67.500000000 | 0→0 |
| B04/final | 938030 | 3959.692118197 | -0.194845486708 | 0.000000000→0.100979710 | 204.166666667 | 1759→1393 |
| B04/final | 938031 | 3195.141557899 | 0.035309432692 | 0.000000000→0.105868414 | 137.777777778 | 0→0 |
| B04/final | 938032 | 5571.410321644 | 0.340480333781 | 0.000000000→0.104590314 | 195.000000000 | 3000→831 |
| B05/development | 937001 | 2853.361972631 | 0.041693980600 | 0.000000000→0.100920165 | 142.777777778 | 0→0 |
| B05/development | 937002 | 4090.882573513 | 0.131706587840 | 0.000000000→0.101358649 | 163.888888889 | 114→0 |
| B05/development | 937003 | 3514.959094743 | 0.068658133071 | 0.000000000→0.109042620 | 194.444444444 | 0→0 |
| B05/development | 937004 | 3936.311390022 | 0.068105822885 | 0.000000000→0.100325626 | 151.388888889 | 0→0 |
| B05/development | 937005 | 2024.943257258 | 0.061471498648 | 0.018128715→0.114685717 | 112.222222222 | 511→157 |
| B05/development | 937006 | 3310.968958601 | 0.072235982516 | 0.000000000→0.112823893 | 227.777777778 | 317→0 |
| B05/development | 937007 | 4812.503758953 | 0.114178064900 | 0.000000000→0.099766674 | 245.833333333 | 686→694 |
| B05/development | 937008 | 4035.406315060 | 0.050939322464 | 0.000000000→0.107506802 | 181.388888889 | 0→0 |
| B05/final | 938001 | 4105.314418307 | 0.130089714942 | 0.000000000→0.110409424 | 166.388888889 | 0→0 |
| B05/final | 938002 | 2841.654117882 | 0.021580543305 | 0.000000000→0.112678065 | 168.055555556 | 0→0 |
| B05/final | 938003 | 3852.501615745 | 0.053706204925 | 0.000000000→0.103596672 | 195.833333333 | 99→0 |
| B05/final | 938004 | 4609.495887672 | 0.123809513454 | 0.000000000→0.099553910 | 270.833333333 | 736→725 |
| B05/final | 938005 | 5084.041092316 | 0.070227979952 | 0.000000000→0.101118499 | 172.777777778 | 1393→939 |
| B05/final | 938006 | 4305.460315152 | 0.056361809626 | 0.000000000→0.101036808 | 250.000000000 | 665→665 |
| B05/final | 938007 | 4283.483540891 | 0.134534571502 | 0.000000000→0.093219679 | 230.000000000 | 888→888 |
| B05/final | 938008 | 4990.387267399 | 0.065289775838 | 0.000000000→0.100470052 | 193.888888889 | 846→576 |
| B05/final | 938009 | 4954.754052138 | 0.106675153140 | 0.000000000→0.094275193 | 203.055555556 | 1496→1516 |
| B05/final | 938010 | 3071.134081153 | 0.038125384593 | 0.000000000→0.103074406 | 155.555555556 | 0→0 |
| B05/final | 938011 | 2767.656744299 | 0.081447264398 | 0.000000000→0.105574006 | 156.666666667 | 313→313 |
| B05/final | 938012 | 3291.514166880 | 0.013533839732 | 0.000000000→0.101283302 | 142.777777778 | 0→0 |
| B05/final | 938013 | 3107.789971628 | 0.061579268944 | 0.000000000→0.110211854 | 172.500000000 | 0→0 |
| B05/final | 938014 | 3161.807211789 | 0.090411461067 | 0.000000000→0.110881718 | 176.944444444 | 697→190 |
| B05/final | 938015 | 4707.103333057 | 0.029852226320 | 0.000000000→0.101267165 | 302.777777778 | 1276→1247 |
| B05/final | 938016 | 3282.906708763 | 0.022869005018 | 0.000000000→0.111442548 | 164.722222222 | 35→35 |
| B05/final | 938017 | 3076.697720959 | 0.085351220541 | 0.000000000→0.101041105 | 207.222222222 | 384→384 |
| B05/final | 938018 | 3102.003082151 | 0.087890837931 | 0.000000000→0.100814686 | 179.722222222 | 320→320 |
| B05/final | 938019 | 3958.384688470 | 0.047366154327 | 0.000000000→0.106886777 | 170.277777778 | 1524→1130 |
| B05/final | 938020 | 2938.355036437 | 0.097632564148 | 0.000000000→0.103977152 | 181.944444444 | 0→0 |
| B05/final | 938021 | 4324.216875944 | 0.000000000000 | 0.000000000→0.093689609 | 231.111111111 | 3000→3000 |
| B05/final | 938022 | 2229.295455621 | 0.009932113183 | 0.000000000→0.115686212 | 161.944444444 | 36→0 |
| B05/final | 938023 | 4779.234803157 | 0.063958485664 | 0.000000000→0.102706773 | 157.222222222 | 1438→1139 |
| B05/final | 938024 | 4004.292682995 | 0.099495696847 | 0.000000000→0.109565247 | 232.222222222 | 34→0 |
| B05/final | 938025 | 2709.366697536 | 0.008741459234 | 0.000000000→0.101359669 | 117.777777778 | 760→760 |
| B05/final | 938026 | 3142.841923288 | 0.007143445755 | 0.000000000→0.105801739 | 208.888888889 | 0→0 |
| B05/final | 938027 | 2526.866504298 | -0.066240828148 | 0.000000000→0.102545360 | 122.500000000 | 245→245 |
| B05/final | 938028 | 3974.923728919 | -0.240545271713 | 0.000000000→0.086567360 | 258.055555556 | 1298→2146 |
| B05/final | 938029 | 2376.838469522 | -0.011741694082 | 0.071064212→0.086827046 | 67.500000000 | 0→0 |
| B05/final | 938030 | 3396.147928526 | 0.107472107888 | 0.000000000→0.097898949 | 152.222222222 | 394→394 |
| B05/final | 938031 | 3034.299897130 | 0.045823580286 | 0.000000000→0.101525538 | 129.166666667 | 0→0 |
| B05/final | 938032 | 3996.186625948 | 0.089127634170 | 0.000000000→0.101057738 | 205.277777778 | 91→91 |

### Judgment changed and next useful decision

Retain this package's **finite H3000 mean usefulness on these two retained policies and exposed
worlds**, under the outcome branch already covered by the complete B06 Pro advice. The native
risk path now activates in O, while F combines mean service improvement, lower return cost,
actual stored-energy replenishment and later joint service in most worlds. This strengthens the
physical-energy part beyond B06's geometric-only H1500 observation. It weakens the explanation
that the useful feedback effect must disappear once native batteries become depleted. It does
not establish per-world service preservation: the large, persistent losses above rule out that
stronger use claim. No whole-run energy neutrality, sustained infinite operation, new learning
advantage, learned-auxiliary mechanism, causal component attribution or general safety is claimed.

The inherited [current shared background, topic 6 and service/risk discussion](https://github.com/CartmanFatass/My-paper-code/blob/63e382485f2a37cccd378436212b911b0fb4d2ae/docs/research/RESEARCH.md)
makes the simpler comparator do work: B03 auxiliary benefit failed to recur, B04/B05 risk
reweighting traded away service, and F now supplies a competent ordinary execution baseline
through actual charging. A predictive head is still not justified by its availability. The new
observation is a narrower unresolved link: arrival and stored-energy recovery can coexist with
persistent loss of joint service. Current telemetry cannot decide whether the binding limitation
is state/history exposure of a frozen H1500-trained actor, network geometry/native wrapper effects,
station competition, or ordinary training variability. These are hypotheses, not equally endorsed
rescue explanations. The severe gaps start before or survive charging, so a charging-only story
is insufficient. Other directions' generic-auxiliary and learned-high reversal evidence reinforces
the need for an ordinary matched learning comparison; it does not establish this specific cause.

The strongest alternative is to retain F as a bounded reference and spend no more fits. I choose
one focused Pro consultation on whether a matched **feedback-aware training** comparison is now
worthwhile before any new predictor or control tuning. The prospective candidate is ordinary
HMASD trained with exactly this F in the environment/action path; the comparator gets the same
H3000 training opportunity and is also deployed with F. This tests adaptation of the learned
service policy to the actual intervention-conditioned history, not whether new weights beat old
weights or a new learner beats unprotected O. The conjecture predicts changed service-bearing
behavior under F and a native cumulative-service increment, not merely fewer margin penalties or
lower MSE. It remains unproven, and this question may rationally reject the expenditure. No new
fit, horizon, threshold, station coordinator, extra panel or confirmation batch is selected here.
This ends the fixed B07 attempt, not by itself the broader direction's scientific responsibility.

### Retained file identities

All paths below are relative to the two durable run roots stated above; every file was verified.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `B04/trajectories/development_F.npz` | 36335319 | `0efd278acffbc38dbe118ba6502010901b6cdac3899812923135fc06e5639a1d` |
| `B04/trajectories/development_O.npz` | 38002649 | `9bbd417372146a56f9953a4c2bf8ee79b3565bf250488ade3d6df3c1bc60d922` |
| `B04/trajectories/final_F.npz` | 145899689 | `ce9bfa110398590bffc412aac435e0eb9ba16c977775fd1c4dfa6948e6d7d009` |
| `B04/trajectories/final_O.npz` | 153874665 | `db9a60d4f338c11276cd1897cfec40b536cacb4be9af95aa5d8db28d723235cb` |
| `B05/trajectories/development_F.npz` | 36419023 | `44b905e120ffd779f268194be1dab25b792b0090d6baf0114914db3f9092924b` |
| `B05/trajectories/development_O.npz` | 37490880 | `2c3d483e7bd8329a27b7e0bbb3a3c97cbf8990ae352e06930a731deeecab6e02` |
| `B05/trajectories/final_F.npz` | 147414370 | `94e82b4a3b2b7261b3ed79691d14f6fc066c42c6c0c8b7aa7576c77b4235500b` |
| `B05/trajectories/final_O.npz` | 152958693 | `540c9b2c1b5ddf582b8f1dd1d1edd930c849b00154115e1413a82458ceed689b` |
| `admission-preflight.json` | 765 | `6cddd4488cbab27594b688128afb6222e5f829c5792848b732088ddef33afe75` |
| `config.json` | 60778 | `b6b420fb9acc8c608b794e8ed403aa5db624152eea3e774911644a609ebe0ef8` |
| `launch-manifest.json` | 4363 | `92d98535aaf2c6b31b9ca700cf578d480a42b465f84ff23a5363ad7bb1657edf` |
| `launch-status.json` | 614 | `de1b04427430238a9c710c2d8d2d81e2c687bddcde2095082c04e8cec5c80527` |
| `process-exit.json` | 550 | `a90fb4bd4adf98f988e25ce59666e3022fc55f3755a5319481c55ec593789012` |
| `stderr.log` | 156 | `c296e315064bfab04d5e2a2247193534c3cfa0c68bac96afe848524cbb5ce7b3` |
| `stdout.log` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `summary.json` | 2057143 | `a33d88cd3c0c9309983a69dac92d373b4516843c3ed28c379468506a59085d36` |

## Pro question 2026-09-24 feedback-aware-training-after-h3000

Conversation: same direction Jev conversation; its private URL remains only in local operation state.

Question: Does the new B07 evidence justify a small matched experiment in which ordinary
HMASD is trained with the unchanged feedback F that it will face at deployment, compared with
equally trained ordinary HMASD deployed with that same F? Or is retaining the bounded frozen
F reference, with no further fits, the better current investment? Critique the proposed
comparison and its discriminating prediction; this is a new hypothesis/key-comparator decision
under constitution §5, not a request to approve B07 or repeat its already covered interpretation.

### Standing and what materially changed

The complete prior answer under `Pro question 2026-09-23 b06-feedback-use-and-next-investment`
already covered the fixed H3000 O/F investigation and its finite-use interpretation. It was
read in full and saved verbatim after verifying that GitHub delivery had failed. That question
must not be resent. B07 is now complete, with no extension: two old N policies, each originally
trained for 180k transitions at H1500; S7-S2, N8, k10, 30 users; each evaluated with O and the
same F at native H3000 on all old development8/final32 worlds. These are exposed worlds and
two retained training artifacts, not new independent learning replications. Native H3000
changes time-normalized inputs and terminal PBRS from the outset; it is not an H1500 rollout
continued after its former terminal boundary.

The preceding `B07 complete: native H3000 feedback restores energy with material service-loss
worlds` entry contains the complete result, all 80 paired worlds, fixed time bins, adverse
service intervals, energy sequences, costs and recoverable raw identities. Briefly:

- Final B04 F−O is +3781.140317 native J and +.066866785 mean QoS; B05 is +3624.592395 J
  and +.047859413 QoS. Both development panels also improve in mean service/J. All 80 paired
  J differences are positive, largely through native return-cost savings. Final service loss
  worlds number 5/32 and 3/32; development losses are 1/8 and 0/8. Do not substitute J for service.
- O now has 275 native cutoff and 212 depletion events; F has zero. F has actual charger
  input and positive stored-energy increments in every world. In 78/80 worlds, a member has
  native arrival/input, positive net stored gain through exit from F, then later positive
  joint service. This does not assign that joint service to the recharged member. Of 1500
  input-bearing mode intervals, 502 are unfinished at H3000 and remain right-censored.
- Physical recovery is insufficient for service: B04 final938030 loses .194845487 mean QoS
  and has no service from step1607 through2999 despite input beginning at1946. B05 final938028
  loses .240545272 QoS; service exists only during2146–2324, despite258.055556Wh input.
  B05 final938021 charges231.111111Wh and serves nobody in O or F. These are important adverse
  facts, not worlds to remove or a diagnosis of a particular bottleneck.
- All160 episodes end by native truncation at3000. F consumes more energy on average, has
  negative full-episode stored-energy change, and sometimes crosses the .1 reserve (worst
  .086567360). The finite absence of cutoff/depletion is not an invariant or indefinite viability.
- The complete 480k-transition comparison cost 0fits and230.542804 runner minutes. Raw physical
  and service arithmetic was independently recomputed from all NPZ files without importing the
  candidate summarizer/controller; retained pre-intervention fields agree in all80 O/F pairs.
  Full observation/state/GRU arrays and member-owned delivered service were not saved. The
  summary is derived evidence; full trajectory arrays are retained off Git at the recorded
  locations and hashes, and are not presumed accessible to you through GitHub.

Earlier B03 auxiliary gains failed to recur; B04/B05 stronger risk-weight training traded
service, and B06's simple feedback improved means without actual charging. B07 strengthens
finite ordinary feedback as the competent reference and the reality of energy recovery, while
its service tails defeat a stronger preservation claim. It does not identify a predictive
head, recurrent memory, station coordination or representation bottleneck. In the inherited
shared topic6, this keeps native service/risk and a competent matched ordinary comparator
ahead of proxy MSE or architecture. Other directions' generic-auxiliary/learned-high reversals
make that comparison more useful; their different hosts do not prove a cause here.

### Conjecture, strongest alternatives and proposed discriminator

The narrow conjecture is that training on histories induced by the unchanged F can teach the
ordinary service policy to make better use of the actual deployment process. A policy trained
at H1500 without F need not know how to resume useful joint service after F has altered the
team's positions, energy and history. That is an untested explanation, not a conclusion from
charging plus a service gap. Native backhaul/geometry constraints, station competition, the
ordinary policy/optimization budget or training variability could instead bind performance.
The strongest expenditure alternative is to keep the useful finite F reference and stop
investing in this repair. A cheaper observation is preferable if it would actually distinguish
the live hypotheses; neither exhaustive diagnosis nor proof of a mechanism is a prerequisite.

The proposed exploratory comparison, open to rejection or revision before selection, is:

| Arm | Training | Fixed endpoint evaluation |
| --- | --- | --- |
| Feedback-aware ordinary HMASD | Complete ordinary joint learning, unchanged F between actor proposal and native environment | Same unchanged F |
| Matched ordinary HMASD | Same complete learner, initialization, legal information, training horizon and update opportunity, without F during training | Same unchanged F |

Both would train **from the same fresh initialization**, at native H3000 and180k actual
training transitions each, with the same S7-S2/N8/k10 host, physical constants, full high/low/
discriminator updates and declared training exposure. The historical N objective is native
lambda_return=2 with **zero extra training-cost coefficient**; it is not lambda_return=0.
Use that common objective here, not the abandoned coefficient4 repair. Both get H3000 training
opportunity, so the primary comparison does not confound F-conditioned training with a longer
episode than the new baseline. No auxiliary head, new actor input, F threshold, station rule,
reset at1500, checkpoint selection or extra tuning is included. Fresh equal-budget ordinary
learning plus F is the comparator; the two old N policies are descriptive context only.

The intervention changes the actual training state/action consequences. Actor-proposed actions
must remain coupled to their sampled log-probabilities in storage and updates; forced F commands
cannot be recorded as if the actor sampled them. The controller mode is common deployment
state for both arms, not a new privileged actor feature. Whether ignored proposal dimensions
or the full learning/reward path creates an important credit/variance issue is part of the
scientific and engineering criticism, not a reason to assume a masked loss or new estimator
silently. Exact storage semantics would be checked in the later L0/implementation if selected.

The predicted intermediate change is more useful service-bearing behavior in the actual
F-conditioned process (with explicit opportunities/denominators and censored gaps), rather than
merely greater weight movement, smaller entropy/MSE or more charging. The practical prediction
is higher native cumulative QoS/throughput against the fresh ordinary+F comparator, read with
raw J, zero-service worlds, battery/risk and all adverse worlds. A result driven only by lower
return penalties or more energy input would not support the proposed service repair. Useful
endpoint learning relative to the common initialization must also be shown. A positive single
training pair would remain exploratory and would not isolate the hypothesized history mechanism.

Please test whether this intermediate prediction and the one-pair contrast are informative
enough at the proposed exposure. Recommend a more useful bounded discriminator, or no new
experiment, if warranted. Do not expand this into a compulsory grid of controls or interpret
the old final worlds as a fresh confirmatory population. Exact new training/world seeds and
the readout would be prospectively fixed after the DM's decision; no new fit or panel is yet selected.

### Context and prospective cost

`source_sha` means the full immutable question commit supplied in the send message. The
explicit current governance/method revision is
`63e382485f2a37cccd378436212b911b0fb4d2ae`, published main when this question was authored.

- Current governance, at that explicit revision: `docs/project/OPERATING_CONSTITUTION.md`
  §§1–5,7–8; `docs/research/RESEARCH.md` owner pause and uav_service_auxiliary row. Owner pause
  is lifted; three independent DMs continue under the delegated scientific scope. This task
  owns only this direction. Advice grants no authority and creates no approval stage.
- Current methods, at that revision: `.agents/skills/hmasd-scientific-tools/SKILL.md`,
  `Explore an idea`, `Update the working explanation`, `Use and revise shared understanding`,
  `Comparators and MARL information`, `Statistics`, `Cost and exposure`, `Pro`;
  `.agents/skills/hmasd-research-engineering/SKILL.md`, `Carried-over engineering standards`
  and `Checks and review`, only for relevant storage/learning and resource semantics.
- Shared background, same revision: `docs/research/RESEARCH.md` topic6's B03/B04/B05/B06
  discussion, plus the current-plan service/risk paragraph. These are inherited, revisable
  judgments; they predate this complete B07 reading. The new evidence and proposed choice
  above supersede the row's old B07 implementation status, not its owner control.
- Evidence at source_sha: this notebook's B07 complete entry and prior B06 Pro question,
  answer and adoption; `runs/uav_service_auxiliary/b07_of_a01/summary.json`, `config.json`,
  `launch-manifest.json`, `process-exit.json`; the B04/B05 N config files in
  `runs/uav_service_auxiliary/b04_n_914021_a01/` and `b05_n_914173_a01/` for the training objective.
- Frozen B07 contract/code at `47d56c9bcdc9fa9d6edee43ae0b4d44755115708`:
  the notebook's `2026-09-23 — H3000 advice adopted: fixed B07 native long-task O/F comparison and L0`,
  `experiments/candidates/uav_service_auxiliary/b07/native.py`,
  `experiments/candidates/uav_service_auxiliary/b06/feedback.py`, and
  `experiments/candidates/uav_service_auxiliary/b04/native.py` for the inherited objective.
  Read code when needed for a consequential feasibility claim; no new training implementation exists.
  These are bounded experimental inputs, not current governance.

Prospective cost **if this one-pair idea is selected**: 2new fits, each180k transitions at H3000,
360k total training. A single actual common-initial F panel (only after identical initialization
is verified) plus two endpoint F panels, each8development+32final worlds at3000, would add
120episodes/360k evaluation transitions. Otherwise separately evaluating unequal initial
artifacts changes that cost and must be declared. New evaluation worlds and seed assignments
are not yet fixed; no reuse of B07 outcomes as these results. Non-fit work includes the action/
storage integration, proportionate tests/review, raw service/physical telemetry and reading.
Those costs and fresh-fit wall time are unknown; B07's230.54minutes for480k fixed-policy steps
is context, not a calibrated learner-time estimate. No sweep, automatic replication, extra
evaluation mode, training extension or confirmation is bundled with the proposal. Critique
whether these costs buy a useful update relative to preserving F and spending no fits.

Constraints: no experiments or training; no changes outside the empty `### Answer` subsection
of this exact question on branch `codex/uav-service-predictive-control`, repository
`CartmanFatass/My-paper-code`. Read the pinned question/Context, but fetch the **latest** target
file before editing and use its actual blob SHA. Preserve the question and every other byte;
stop on overlapping edits. Report the actual commit after a successful write. If delivery
fails, return the complete answer in chat, not only a SHA, status or link. Keep private
conversation/account identifiers out of repository content.

Return: source-grounded advice on the impending comparison/investment, including which
judgments are strengthened, weakened or untouched; the strongest alternative explanation and
investment; the smallest useful discriminating observation, its intermediate/native predictions
and fit/non-fit cost; scope and decision-critical source gaps; and `MATERIAL_DISSENT: yes/no`
for the proposed comparison. No fixed candidate count, new architecture, universal negative
claim, permission requirement or proof prerequisite is requested. If the proposed two-fit
comparison is worthwhile, state what it can and cannot establish and the outcome that should
end that specific investment. The DM owns the final choice.

### Answer

GitHub 读取可用，但本轮连接器没有仓库文件写入动作，因此未写回；实际 Answer commit：无。 最后核对到目标文件的 blob SHA 为 ebc62816e1aabd4569622ac50ab2c0a81ab69689，本次指定问题的 ### Answer 仍为空。本轮没有修改仓库或启动实验。以下是完整答复。

B07 后的投入选择：支持一次同部署 F 的匹配训练比较，但收紧中间预测

MATERIAL_DISSENT: no。

**我支持这一次两臂、每臂 H3000／180k transitions 的探索性训练比较：候选在训练时接入完全不变的 F，对照在训练时不接入 F，两者最终都在同一个 F 下评价。**保留相同新初始化、完整普通 HMASD 学习和原生目标，不增加网络、模式输入、损失遮罩、阈值搜索、额外部署模式或确认批次。

需要实质落实的不是第三个对照，而是两处设计细节：**把训练时域、采集边界和更新机会写清楚；把“更有服务的反馈后行为”变成带机会分母、实际服务量和删失标记的读数。**原提议足以作为有限训练包比较，却不能仅凭“充电后又出现过服务”来区分恢复能力，也不能把正终点差直接解释成历史适应机制。

一、B07 改变了什么，为什么现在可以问这个训练问题
加强的是反馈参照的实际用途，不是某个学习缺陷

B07 的两个 final 面板分别增加 3781.140317／3624.592395 原生 J，平均 QoS 增加 .066866785／.047859413，两个 development 面板的平均服务和 J 也改善。O 实际出现了 275 次 cutoff 和 212 次 depletion，F 在这些有限轨迹中没有出现两类事件。这比 B06 的“几何余量修复、没有充电和失效事件”多了一条重要证据：当前简单执行反馈在真实能量压力下仍有有限用途。

hmasd-pro-question-usa-feedback…

实际补能也不再是假定。每个 F 世界都有充电输入和正储能增量；998 个输入承载区间在时域内退出 F，退出前均有正净储能恢复，其中 977 个区间之后出现过正的联合服务。不过，另有 502 个区间尚未结束；“后来有联合服务”不能归属于那个刚充电的成员。

hmasd-pro-question-usa-feedback…

因此，被削弱的是“电池进一步消耗后，反馈收益必然消失”的解释。没有被证明的是：剩余服务不足来自没有在 F 历史上训练。

服务损失使恢复假说值得检验，却没有把它诊断出来

最有约束力的反证不是平均 QoS 仍低，而是补能和持续服务可以明显分离。B04 final938030 在 1607–2999 步没有服务，尽管 1946 步开始充电；B05 final938028 获得 258.055556 Wh 输入，却仅在 2146–2324 步有服务；B05 final938021 充电后仍全程零服务。前两个世界的平均 QoS 损失分别达到 .194845487 和 .240545272。

hmasd-pro-question-usa-feedback…

这些事实反驳“补能发生就足以恢复服务”，但不能在训练历史、几何／backhaul、原生动作包装、站点竞争之间选定原因。尤其是部分缺口在充电前已经开始，不能把它们全部叫作“充电后不会恢复”。

同时，F 平均耗能更多、全回合储能变化仍为负，最差电池降到 .086567360。有限的零 cutoff／depletion 不是储备余量不变量，也不是无限持续运行的证明。新训练比较应保留这些实际风险读数，不能将 F 当成已经解决安全问题的外部保证。

hmasd-pro-question-usa-feedback…

既有负证据保持不变

B03 的辅助收益未重复、共同 MSE 不排序原生用途，以及 B04/B05 风险重加权中的服务交换，均没有被 B07 撤销。共享背景的具体作用是：**新候选必须面对“新训练的普通 HMASD＋F”，而不是只打败旧 O；也没有理由复活预测头或系数 4。**本次选择检验训练与实际执行过程的匹配，而不是把简单反馈的阳性转成某种新架构的资格。

hmasd-pro-question-usa-feedback…

二、为什么这两次训练比继续描述旧轨迹更有信息价值

这次比较有一个清楚的、可以失败的用途问题：

在相同原生 H3000 任务、初始化和训练预算下，训练时接入部署中必有的 F，是否比训练时不接入 F，得到更有服务用途的最终策略？

两臂都从 H3000 开始训练，排除了“候选只是获得了长任务训练，对照仍停留在 H1500”的明显混杂；两臂都部署 F，又排除了“候选只是多了执行保护”。这正是原提议中最有价值的匹配。

hmasd-pro-question-usa-feedback…

最强的替代解释是：即使补能成功，原生网络几何、包装规则与资源约束仍会限制服务；或者同样预算的普通 H3000 训练本来就足以改善这些轨迹，专门接入 F 没有额外价值。相同的新训练机会使后一种解释在本次比较中真正有机会成立。前一种解释则不能被这个两臂比较完全识别，但会约束实际能得到的服务增量。

**最强的投入替代是保留现有有限 F 参照，不再支付 fits。**它的理由很实在：现有包已经有用途，180k 不保证学到更好的联合恢复行为，而一次训练对也无法估计训练结果的总体稳定性。不能把未解决的服务缺口自动兑换成重训义务。

我仍倾向购买这一次比较，因为干预直接作用于部署时实际存在的训练—执行差异，而且不需要先引入一个未经定位的模块。旧轨迹上的几何分析、服务区间重算或固定参数回放可以描述失败，却不能产生“普通策略在 F 过程中更新后会怎样”的闭环结果。要回答这次学习用途问题，一个真正匹配的学习对通常比进一步堆叠固定策略诊断更直接；这不是认定其成功概率高，也不是认定所有诊断都无价值。现行方法同样允许有限学习比较先于穷尽机制诊断。

hmasd-pro-question-usa-feedback… +1

三、最小完整比较：保留两臂，明确 180k 到底包含什么

建议采用下面这一组，不附带第三臂：

项目	候选 A：反馈条件训练	对照 B：普通训练
初始化	同一份新初始化的真实副本	同一份新初始化的真实副本
训练环境	原生 H3000，actor 提议经过固定 F 再进入原环境	原生 H3000，actor 提议直接进入原环境
训练目标与学习器	原生 N 目标、完整高／低层及判别器学习	完全匹配
训练暴露	180k 实际团队 transitions	180k 实际团队 transitions
最终评价	固定终点，在同一个 F 下评价	固定终点，在同一个 F 下评价

历史 N 的目标应准确写成 lambda_return=2、额外训练成本系数为 0。额外系数为零并不是取消原生风险惩罚。B04/B05 N 的配置及继承的训练代码支持这一点。原生混合奖励、熵项、判别器学习也保持，不顺手变成另一种“纯服务”算法。

训练时域与更新机会

为把该预算具体化，我建议两臂均采用：

2 个同步环境×3000 步×30 个完整更新阶段=180,000 团队 transitions.

这使每阶段仍采集 6000 个团队 transitions，保留 30 个完整联合更新阶段，同时不在 1500 步处人为切断 H3000 历史。它是本次建议的采集组织方式，不是已经存在的新训练实现，也不是声称改变并行数没有影响。

源码中 make_config 将 episode_length 与 spec.rollout_length 联系起来；旧 B04 收集器在每阶段更新后调用 clear_buffers()。因此，不能只改一个评价 horizon，或不经核对沿用旧采集循环，就宣称接通了完整 H3000 训练。应区分环境终止、采集边界和学习更新边界，并核对它们是否意外改变技能／循环状态。

在没有提前终止时，上述配置每臂包含 60 个完整 H3000 训练回合。这提供了多次完整能量过程的学习机会，但不是 60 次独立训练复制，也不是已经证明暴露充分。若发生提前终止，则记录实际回合数、剩余采集段和状态连续性；未结束的物理回合不能仅因清理训练 buffer 而重置 F、技能或 GRU。两臂使用同一个处理合同。

各优化器的 epochs、minibatch、归一化、GAE 和技能时钟也应按共同配置固定，实际 optimizer 步数另行记录。30 个更新阶段不等于 30 个 optimizer steps，总 transitions 相等也不自动证明更新机会匹配。

初始化与评价

共享初始评价成立的条件，应包括实际模型参数、必要 buffers、normalizer 与评价状态一致，而不只是 seed 名字相同。评价必须隔离 RNG 和训练状态，不能让先运行的初始面板改变某一臂后续训练。两臂训练轨迹在 F 实际干预后理应分开，不要求继续逐数组一致。

保留原提议的一次共同初始 F 面板＋两次最终 F 面板，每个面板为新固定的 8 个 development 世界与 32 个 final 世界。final32 是主要用途读数，development8 约束范围；不因其中一面板有利而池化掩盖另一面板。训练和世界种子由 DM 在选择后前瞻固定，不按 B07 的有利或不利世界挑选。历史两份 N 仅作背景，不加一轮旧制品评价。

hmasd-pro-question-usa-feedback… +1

四、动作覆盖不必使训练成为“伪 on-policy”，但存储和信用路径不能含混

设 u
t
	​

 是 actor 实际采样、具有原生 log-probability 的提议，m
t
	​

 是 F 的模式状态，提交命令为

a
t
	​

=g
F
	​

(o
t
	​

,m
t
	​

,u
t
	​

).

固定 F 激活时替换命令，未激活时传递当前提议；原生环境还可能进一步解释 docking 或改变实际运动。**actor 提议、提交命令和实际物理运动是三个不同对象。**冻结反馈代码已经给出了这种替换／传递结构。

我的训练语义建议是：

**学习存储保留 u
t
	​

 与采样它时的 log-probability；执行日志另存 a
t
	​

。**用于收益、价值目标、两层 GAE、判别器数据和下一观察的，必须是实际执行 a
t
	​

 后得到的真实轨迹，而不是无 F 的影子后果。PPO 比率针对同一个被采样变量构造：

ρ
t
	​

(θ)=
π
old
	​

(u
t
	​

∣h
t
	​

,z
t
	​

)
π
θ
	​

(u
t
	​

∣h
t
	​

,z
t
	​

)
	​

.

原策略自身的动作变换及概率计算照旧；这里不需要把 F 强制命令伪装成 actor 样本，也不需要为 F 的硬覆盖另套一个动作密度 Jacobian。这是把固定、无待学习参数的 F 看作实际交互过程一部分的推导，不是对现有 PPO／GAE 实现无偏性或收敛性的证明。

被忽略的提议确实可能造成信用效率问题。条件于完整历史，若某成员被全部覆盖，而且其本次提议不经其他通道影响后果，则其当前提议对于相应外部后果没有行动区分作用；有限样本、近似 advantage、PPO clipping、熵和混合学习仍可能产生更新。关于普通动作裁剪的研究也区分了“按原采样变量学习仍有正确概率语义”与“利用执行等价性降低估计方差”；但那个结论不能直接移植成此处多智能体滞回反馈的现成估计器。
arXiv

因此，我不建议默默遮掉覆盖步的 actor loss，更不能一起删掉高层／critic 的这些转移。那会把比较改成“F 条件训练＋新信用规则”。高层技能、其他成员的行动及之前的路径仍可能影响这些时段，循环状态也应继续随真实观察演化。

另一个边界是：F 的滞回模式属于实际过程状态，但不能据此给候选新增模式特征。两臂部署时保持相同的信息权限；模式未显式输入可能带来部分可观测性，不能预先认定现有记忆一定能解决它。原提议已正确要求不新增这种特权输入。

hmasd-pro-question-usa-feedback…

这项实现最值得检查的是提议／log-probability 一致、命令未覆盖掉存储样本、实际 reward／next observation 贯穿全部学习路径，以及更新边界没有假 reset。这些是既有工程方法下的针对性检查，不是额外的科学许可阶段。

hmasd-pro-question-usa-feedback…

五、让中间预测真正提供额外信息

原提议的中间预测方向合理，但“更多有服务的行为”仍接近终点目标的重述。特别是 B07 的“补能退出后曾有正联合服务”已经覆盖 78/80 个世界，容易出现天花板；最大服务缺口也不能单独代表用途——B04 final938030 的最大缺口缩短，却同时损失大量累计服务。

hmasd-pro-question-usa-feedback… +1

我建议不加新面板，只在已有训练和评价轨迹上固定一个较窄的描述：

以实际恢复后的行动机会为锚，而不是以“发生充电”为成功

每个世界取第一次某成员经历实际输入、具有正净储能恢复，并退出 F 的时刻作为描述性锚点；每世界至多一个，避免拥有大量短区间的世界支配结果。退出 F 只表示 F 恢复传递该成员提议，不保证原生包装不会再改变其命令。

以随后固定 250 个原始时间步为窗口，记录实际累计 QoS／交付量、正服务步数及服务空窗，并区分锚点时队伍已经有服务，还是从零服务恢复。250 步沿用现有描述尺度，不是按新结果选择最有利时窗，也不替代完整终点。

同时保留机会分母：多少世界激活 F，多少有输入，多少完成退出；没有输入、输入后未退出、退出后剩余时间不足的世界分别标记。窗口只有 e<250 个实际步时，报告 e 和已观察服务，不把未观察部分填成成功或失败。窗口内再次进入 F 是实际后果，不能删去以美化恢复读数；所有未完成区间继续右删失。训练阶段另记录实际未被 F 覆盖的提议机会，不能用 180k 总步数代替可学习的服务行动暴露。

这个中间预测是：候选在真实恢复后的有限机会中产生更多服务量，而不只是多完成一次模式切换或更快出现一次微小正值。

但事件由策略自身决定。候选和对照的退出时间、位置与入选世界可能不同，所以这一条件读数不是相同状态上的因果对照。它用于解释完整包结果，而不能证明“恢复能力”中介，更不能把联合服务归属于刚恢复电量的成员。世界均权的完整终点仍覆盖所有未激活、未退出及不利世界。

主读数仍是完整任务的实际服务

对每个世界报告

S=
t=0
∑
L−1
	​

q
t
	​

,
S
ˉ
H
	​

=
3000
S
	​

,

其中 L 为真实 episode 长度。累计交付量使用实际 delivered throughput 及原生时间步长，不用链路容量替代。若提前结束，实际每步平均另报；共同计划窗口的分母避免把“较早停止服务”误读成较高服务效率。

主要比较是最终 S
A
	​

−S
B
	​

，并列读取原生 J、返航成本、零服务世界、全部损失、真实最低电池及尾部、cutoff／depletion、消耗与输入能量。仅 J 或充电量上升不支持服务修复。风险与服务发生冲突时，报告幅度和任务范围，不事后发明一个综合分数消掉冲突。

相对胜出与自身学习分开

用真实共同初始化在 F 下的服务 S
0
	​

，分别读取

I
A
	​

=S
A
	​

−S
0
	​

,I
B
	​

=S
B
	​

−S
0
	​

.

S
A
	​

−S
B
	​

=I
A
	​

−I
B
	​

 只是恒等式，不是初始化与学习的因果份额。**候选仅比一个退化的对照少退化，不足以称作有用服务学习。**候选自身改善、对照也改善而候选更多，是更有力的有限用途模式；即便如此，也不证明普通基线已经充分调优。共同初始 F 面板正是为这个区别付出的必要评价成本。

hmasd-pro-question-usa-feedback… +1

六、一对训练能改变什么，以及什么结果应结束这个配方的投入

先于结果的完整预测是：A 相对共同初始化有实际服务学习，并在共同 F 下超过新训练的 B；恢复机会中的服务量与完整累计服务方向相容，原生 J／风险没有出现抵消用途的严重代价。

最强的相反预测是：两臂即使都学到服务，F 条件训练仍没有额外累计服务价值；或者其局部恢复改善被较差的其他时段、几何布局或风险尾部抵消。也可能 F 条件训练只是改变了惩罚规模和优化过程，而没有改善服务。

固定终点观察	应怎样更新判断与投入
A 有自身服务学习，超过 B，完整服务／J／风险相容，中间读数也有支持	保留这一有限训练包及“与恢复假说相容”的解释；不宣称机制已识别，不自动追加复制或确认。
两臂都学习，但 A 没有值得保留的额外服务增量，或 A 服务更差	结束这一固定 180k 配方的继续投入。保留普通学习和 F 的已有用途；不将小差说成等价，也不自动延长训练。
只有 J／返航成本／充电输入改善，累计服务不改善；或相对胜出而候选自身也没有有用服务学习	不接受所提服务修复。保留真实风险收益或相对退化事实，但不据此继续买同一配方。
恢复窗口看似更好，完整任务服务或风险明显更坏	局部预测不够形成净用途；不能只选择有退出机会的世界。结束该用途扩展。
完整服务确有有用增量，但恢复窗口预测不支持	保留包收益，削弱“更会充电后恢复”的解释；收益也可能来自提前规避、保持布局或其他共同变化，不补做控制来追认机制。

如果训练中 F 很少激活、几乎没有恢复后的有效提议机会，或者大量机会在终点删失，这会限制对恢复假说的检验，不是活跃机制的负效应证据。但“未充分区分”也不产生追加预算的义务；在固定成本下没有获得值得继续追问的读数，可以有理由结束该配方，而不延长到它出现阳性。

一对训练只能提供一个匹配训练实现下的探索结果。40 个世界、多个恢复区间和更多时间步都不能增加训练样本数，也不能通过 world bootstrap 变成训练总体精度。新世界避免重复使用 B07 结果，却不把这次结果驱动提出的假说和单对训练升级为确认。

hmasd-pro-question-usa-feedback…

七、成本：这不是免费接线，也不需要先购买额外诊断批次

本建议保留原提议的支出边界：

工作	固定规模
新训练	2 fits，合计 360k 实际团队 transitions
共同初始 F 评价	40 个 episode，最多 120k transitions
两个最终 F 评价	80 个 episode，最多 240k transitions
合计	360k 训练＋最多 360k 评价＝最多 720k transitions

名义训练回合为每臂 60 个，评价为 120 次 episode；提前终止时评价 transitions 按实际计，不通过补跑填满。没有另购 O 部署评价、旧制品评价、probe、阈值扫描或训练中间 checkpoint 面板。训练阶段已有 rollout 读数和最终轨迹可以支持上述诊断。

B07 的 480k 固定策略评价用了 230.542804 runner 分钟。按同吞吐缩放，360k 评价约为 172.9 分钟的工作量尺度，但新策略访问、资源并发和实现会改变它；尤其不能据此给出新 fits 的校准耗时。学习 wall、接线与检查、必要审阅、轨迹保存、收取和完整判读仍有未知成本。

hmasd-pro-question-usa-feedback… +1

支持支出的理由，是这一次训练比较可以直接改变是否保留“训练时接入 F”的决定，而不是成本很小。若接线实际要求更换信用估计器、扩大信息接口或重写一套循环学习算法，原先“小型匹配比较”的成本前提就变了，不应把那些工作默认为本建议的一部分。

八、来源范围与未完成的独立核验

本答复已读完整附件，包括新问题、完整 B07 结果与全部 80 个配对世界、所附治理／方法／共享背景，以及前次完整 B06 Answer；并按指定版本读取了 GitHub 上的新问题和相关 notebook、H3000 采纳条目、共享研究状态、反馈与继承训练代码、B04/B05 N 的目标配置，以及 B07 配置和启动／退出记录。推理依据区分了本次 e49da2a…、治理方法 63e3824… 与冻结实现 47d56c9…，没有用最新可写分支替换它们。

有两类限制需要保留。

**其一，GitHub 大文件读取限制使我未完成约 2 MB summary.json 正文的逐项核对。**文件正文接口没有返回可读内容，另一路报告过大或不支持；blob 路径取得的是 Base64 响应，不能据此声称完成了摘要审计。这里的详细结果依据已完整读取的结果条目与全部世界表，而不是我重新生成的机器汇总。

**其二，没有独立取得并重算仓库外 NPZ／checkpoint。**37402 项检查、能量闭合与全部前缀匹配，是所读 DM 核验的结果，不是本次重新执行的核验；完整 observation／state／GRU 和成员交付归属未保存，也不能补成已知事实。新训练实现尚不存在，因此以上给出的是应保持的语义和可执行范围，不是对新 collector／learner 已通过验证的声明。

hmasd-pro-question-usa-feedback… +2

这些缺口限制独立数值审计和机制归因，但已有完整结果记录足以支持这次有限投入建议。

最终判断：选择这一次两臂、同部署 F 的真实学习比较，而不是先增加模块或继续堆叠旧轨迹诊断。它应以候选自身有用学习、对新普通＋F 对照的累计服务增量，以及完整风险与损失共同决定去留。若只有惩罚节省、更多充电或局部窗口变好，就结束这一固定训练配方的继续投入；若完整用途成立而恢复解释不成立，保留用途、修订解释。最终选择仍由 DM 作出。


## 2026-09-24 — Feedback-training advice saved from chat; fixed B08 A/N comparison and L0

### Delivery, complete reading and adoption

The new question at `e49da2a9d2a69bb6750afa5ecadc372e36ebe848` was sent once with key
`hmasd:a1a242eb51cff8e9a319c7e277e036505e6369827198029853ebf134aaee2f5f`, 6 Pro, exact attachment
seen. The READY observation was generation97, wake `2386ed41-343b-47a2-a2c7-a12abce82ccc`, event
`f134ff54a9825ff602ec491b`; it was consumed at generation98 after full reading. The complete
answer above is **saved from chat**, verbatim: body9246 characters, body SHA-256
`f3dbd881ff6e86cc574a24d99e48aec4485a19a200c239026c264b16a10e286e`; saved file9247 characters,
21,960 bytes including final newline, file SHA-256
`61534b7066f88ff7131e34585569de9e7160b8e47e2bd793ff1f450aa89f3533`.
The deliver verifier returned NOT_DELIVERED. The cited `ebc62816e1aabd4569622ac50ab2c0a81ab69689`
is the unchanged target blob, not an Answer commit; the actual branch still held the unique
empty subsection and unchanged question. Pro explicitly reported no write capability and
relinquished it. No answer or other author's edit was overwritten. No operation tab remains;
14 unrelated targets were preserved. Private conversation details remain in local operation state.

The DM read the full answer. It supports the proposed two-fit comparison, with MATERIAL_DISSENT:no,
and makes two useful refinements: 2 synchronous lanes ×3000 collection steps ×30 joint updates,
and a first-recovery opportunity description with actual exposure and service, not an almost
saturated indicator of any eventual service. I adopt both. The current source confirms that
`make_config` binds both native episode_length/max_steps and collection length explicitly;
B04 calls `clear_buffers` after updates, and that method resets temporal bookkeeping. B08
must distinguish buffer clearing from physical termination and preserve live state if a native
early ending offsets a lane from the fixed collection boundary. `energy_aware.step` can end
when all batteries are exhausted without charging, so this case is reachable, not assumed away.

The historical N objective is native lambda_return=2 plus zero extra penalty coefficient, as
verified in both saved N configs and B04 code. The current Pro text contains flattened math
and citation labels from browser extraction; it is preserved rather than silently repaired.
Implementation keeps the existing native proposal/log-prob/PPO contract, including the native
new-versus-behavior probability ratio; the flattened formula is not executable authority. I do
not use the unlinked clipped-action literature mention to claim an unbiased MARL estimator.
Pro could not independently audit the large summary body or off-Git NPZ/checkpoints. Its advice
uses the complete result entry and source code; our prior direct numerical reading remains the
empirical evidence, not a newly independent validation by Pro.

Shared background was refreshed from published main
`1d9196d76d4d58e0d138d2094923a03510df89a8`, especially topic6's B03–B07 service/risk evidence.
Owner pause is lifted and this direction/lead remains active. F's finite energy/service
usefulness is strengthened, but representation or recurrent-history deficiency remains
unidentified. The new B15 confirmation uncertainty in the shared programme is consistent with
keeping actual training units separate from worlds; it neither vetoes nor confirms this S7
one-pair development test. The useful ordinary baseline must get the same H3000 learning
opportunity and F deployment. Reusing old H1500 weights as the main comparator would not test
this choice. No learned predictor, coefficient4 repair or extra deployment control is selected.

I choose this one new training pair because it directly tests whether learning in the actual
F-conditioned process improves finite native service beyond fresh ordinary learning plus F.
The strongest alternative remains keeping B07 and spending no fits. A new module or more old
trajectory descriptions would not answer the same learning question. This is a selected
exploration, not confirmation, a diagnosed history mechanism or an extension of B07.

### Fixed scientific scope and cost, before implementation or results

Object `UAV-SERVICE-FEEDBACK-TRAINING-B08`, direction `uav_service_auxiliary`. One new matched
training block, seed **915031**, fixed order **N then A**, both complete HMASD:

| Arm | Training action path | Evaluation action path | Actual training budget |
| --- | --- | --- | --- |
| N | Native actor proposal into the original adapter/environment | The unchanged B06/B07 F | 2lanes ×3000steps ×30rollouts =180,000 transitions |
| A | Same actor proposal, then unchanged F, then original adapter/environment | That same F | 2lanes ×3000steps ×30rollouts =180,000 transitions |

S7-S2, N8, k10,30users, native H3000 from reset; complete high/low actor/critic and both
discriminator learning, native mixed rewards and entropy terms unchanged. Both use native
return coefficient2, extra training-cost coefficient0. No auxiliary head, extra actor input,
loss mask, estimator change, mode feature, station scheduler, altered physics, coefficient
search or best-checkpoint selection. Both receive identical ordinary training/tuning rights.
The only between-arm treatment is whether F transforms commands during training.

Use 2 synchronous training environments, lane initial seeds915031 and915032 and each native
environment's continued seeded reset stream. Both arms start with identical newly initialized
parameters, model buffers, normalizers and required evaluation state; seed_everything is
explicit for each arm and equality is checked over actual artifacts, not just seed labels.
Both get 30 joint update phases containing6000 transitions each, with the same original PPO
and discriminator epochs/minibatches/normalization settings. Retain actual optimizer counters,
parameter displacement and per-rollout learning curves. The changed lane count and horizon are
common to both arms, not claimed equivalent to old4×1500 training.

Fresh fixed evaluation worlds are **development941001–941008** and **final942001–942032**.
No such seed occurs in this direction's prior code/config/NOTES search. One actual common
initial F evaluation (40episodes, at most120k transitions) and both fixed final endpoints
(40episodes each, at most240k combined). The final32 panel is the primary descriptive package
comparison; development8 is reported separately. No intermediate checkpoint panel or O
readout, no old-checkpoint panel, no world selection or extra random streams. Reuse the B07
native deterministic evaluation rule and RNG isolation, with common policy initialization seed
915031. The common initial evaluation is reused only after both arms' actual initial state
matches; mismatch is an implementation failure, not a second quietly added panel.

The proposed single admission-guarded batch writes one root
`runs/uav_service_auxiliary/b08_an_915031_a01/`, a common initialization/evaluation and separate
N/A fit records. Fits started are recorded per arm; an error stops the dependent batch and
retains partial output, with no automatic retry. Sequential execution is an engineering
choice, not an outcome-based choice of whether A runs. A is the fixed second arm when the
unchanged first arm completes technically, irrespective of its scientific score.

**Planned: 2fits at180k each =360k training transitions, plus at most360k evaluation transitions;
120 evaluation episodes and at most720k total transitions.** A nonterminal training trajectory
continues across a collection/update boundary: no invented environment, F, skill or GRU reset.
Native terminal/truncated lanes reset through the original path; true early endings, episode
lengths, ended episodes and straddling lanes are counted. Evaluation attempts stop on the
native ending; no replacement or top-up toH3000. Nominal no-early-end training is60 full
H3000 episodes per arm, not60 independent training seeds. One pair gives training n=1 per arm.

Execution node is configured `wsl_4070`, CUDA FP32, TF32off,4Torch threads, after exact-source
publication and fresh native admission. Actual fit/phase wall, CPU and runner peak RSS are
measured. B07's throughput would scale360k fixed-policy evaluation to about172.9 minutes;
that is an uncalibrated workload scale, not new learner wall or a stop rule. Integration,
checks/review, actual training wall and collection support remain unknown. No speed claim.
No additional fits, threshold/horizon changes, tuning, replication or confirmation are bundled.

### Native readings, opportunity description and interpretation

Retain full raw J, cumulative actual QoS S, S/3000 planned-window service, actual-step mean,
actual delivered volume using native timestep duration, native costs, zero-service worlds,
all signed per-world N/A effects, min/P10 battery, cutoff/depletion, consumed/input/stored
energy and partial horizons. Report final A−N and each arm minus the **actual common initial**
service/J. A beating a deteriorated N while itself failing to learn useful service is not a
service-learning success. Do not pool development and final or count worlds as training n.

The intermediate description uses at most one anchor per world: the first chronologically
completed F interval in which a member received actual charger input, gained positive net
physical stored energy from first input through exit, and exited F. Break simultaneous exits
by member index. The exit-step decision is the anchor; the window covers that transition and
at most the next249 transitions, capped by the real ending. Record member, interval, input,
net stored gain, anchor time, time remaining, actual e<=250, cumulative QoS/delivered volume,
positive-service steps, zero-service intervals and re-entry into F. Distinguish service already
present immediately before the exit from new positive service afterward; step0 has no prior
transition and is marked unknown. No joint delivery is attributed to the selected member.

Include denominators for F activation, input, qualifying exit, no input, input without qualifying
exit, no positive-gain exit, and insufficient residual window. Never impute the unobserved
part of e<250 as success or failure. Do not drop a world or re-entry because it worsens the
window. Every unfinished feedback interval is right-censored. Training additionally records
actual per-member proposal opportunities passed by F (for N, all proposals pass this external
controller), native wrapper changes separately where available, and actual post-recovery
opportunity exposure. Restored proposal transmission is not guaranteed physical execution.
The world-uniform complete task result includes all no-opportunity and adverse worlds.

Prediction: A has native service learning from the common initialization and exceeds N under
common F deployment; post-recovery service quantity is directionally compatible, with full
J/risk and loss tails retained. Event time/position/eligibility are policy-dependent, so that
window is descriptive support, not matched-state causality or a learned-recovery mediator.
A true full-package service gain without window support retains the package observation but
weakens that recovery explanation. Only risk penalty, charger input, entropy or window gains
without complete-task service learning do not support the proposed service repair. Adverse,
small or mixed effects can end this fixed recipe without proving equality or universal harm.
Rare activation or censoring limits discrimination, not proof of an active mechanism's failure;
it does not automatically authorize longer training. No arbitrary new significance or MEI
gate is imposed on this single-pair exploration; all magnitudes and practical costs are read.

### L0: bounded candidate implementation and checks

Deliver a fixed B08 native training/evaluation batch under
`experiments/candidates/uav_service_auxiliary/b08/`, one admission-guarded entry
`scripts/run_uav_service_auxiliary_b08.py`, and focused tests under
`tests/experiments/candidates/uav_service_auxiliary/b08/`. These are the only executable edit
paths. Reuse B01/B04 configuration/learning helpers, unchanged B06 feedback and B07 physical
telemetry/evaluation where they fit. Do not modify frozen B01–B07, shared HMASD/learner/env,
transport, launch kernel, control files or existing results; report a necessary shared repair
before broadening this implementation. DM owns NOTES, publication, scientific choices and launches.

Keep the actor proposal and its existing sampled log-prob/step_data coupled through storage;
keep the submitted F command separate, and store actual executed reward/next observation/state
through both hierarchy returns, discriminator input and subsequent recurrent history. No shadow
reward/trajectory or treating a forced command as a sampled proposal. F observes only its
unchanged legal fields, uses unchanged mode thresholds/closest-station command, and resets
only on genuine native environment resets. F state is not an actor feature. Native wrapper
energy/backhaul changes remain in the actual path. Snapshot/clear only genuinely rollout-scoped
storage at updates; preserve live-lane temporal state when an episode straddles a boundary,
without carrying stale buffer indices or double-counting a closed high-level transition.
Any inability to maintain this ordinary interface is a concrete engineering issue to resolve
before launching, not silent introduction of a new credit rule.

Output compact source/config/native status, per-fit counters/curves, per-world readings,
initial-state identities, endpoint comparisons, opportunity denominators and costs in summary.
Keep necessary checkpoint, per-transition training proposal/submission/ends/reward/storage
telemetry, physical state and evaluation trajectories off Git under the run's raw/ or equivalent
subdirectories, with bytes and hashes in summary. Retain all failures. A large interval/trajectory
array does not become compact merely by being placed in summary.json. Partial output and native
exit evidence remain recoverable. Do not mutate a runner summary during publication.

Tests must exercise the real collector→storage→update path with active F: proposal/log-prob
consistency, actual reward/next-state, genuine updates of all learner groups, F mode continuity,
normal and early-end reset handling, and preservation across a nonterminal collection boundary.
Compare training configuration rights exactly; test common initialization and evaluation
isolation/RNG preservation. Test first-exit anchor/tie/censor/re-entry/zero-service cases against
independent known arrays and actual delivered-time units. Preserve existing raw energy-closure
checks and native H3000 semantics. Tests are engineering fixtures, not outcome-bearing pilot
fits; they own and clean scratch through pytest. Use existing local scientific venv; install
nothing. Independent engineering Reviewer checks the resulting high-risk collector/evaluator
and boundary changes; the DM accepts. No result-bearing launch before exact reviewed inputs
are committed, pushed and admitted on the actual configured node.

## 2026-09-24 — B08 implementation exposes an unresolved ordinary high-level boundary contract

No B08 fit or result-bearing attempt has started. The existing feedback-training Pro operation
is fully reconciled, its complete answer saved and read. This entry records new source evidence
from implementing its selected comparison, not a failed scientific prediction or a request to
resend that consultation. The independent evaluator/config/opportunity work can proceed; the
training entry fails before output creation until a coherent boundary contract is selected.

The Implementer and independent engineering Reviewer traced ordinary strict HMASD at
`001dd55b2e6ed7e6a5e5dc746dcc86818dae01a0` and found three coupled defects:

1. `hmasd/agent.py::_store_coordinator_experience` closes strict high samples only at
   `skill_timer == k-1`, ignoring an earlier native ending. The collector then calls
   `reset_env_state`, which removes the pending decision/reward. Thus an actual terminal
   skill can lose credit and a preceding nonterminal high sample can link in GAE to the
   next episode. The native all-exhausted/no-charging ending exists in
   `envs/pettingzoo/relay/energy_aware.py::step`. Its occurrence in B08 is unknown; it cannot
   be treated as impossible or as a technical failure that selectively excludes an adverse run.
2. `clear_buffers` clears timers and pending/reward state. On the next `step`, a lane missing
   a timer gets random skills and reset recurrent arrays. Preserving physical/F state alone
   therefore does not preserve the held skill and GRU of a live native episode.
3. A pending ordinary high decision stores a rollout-local `time_step`. Closure writes its
   old likelihood/value to that row, and the high sampler gets decision state/observation/skills
   from the corresponding low row. Elapsed duration is also computed by local-row subtraction.
   Restoring the dictionary after buffer reset can write to unrelated data or fail. Separately,
   high GAE currently bootstraps the last completed decision from the global collection boundary;
   if a new pending segment began earlier, its actual decision value is the appropriate next
   high-decision successor. Snapshot/restore does not repair either issue.

There is no ordinary handoff/flush API. D2 has a private segment flush and a different contract;
turning on D2 is not an implementation of the selected ordinary comparator. The Reviewer ran
12 existing storage/recurrent-mask checks successfully, but they do not cover this boundary.
The meaningful regression is k4, collection12, one native ending at row5: row4's decision closes
terminally after two rewards, row10's decision survives the update and closes after two further
transitions with its original facts and four actual rewards, and the preceding completed decision
bootstraps from row10. Low rows must retain their intended exactly-once epoch eligibility.

The old behavior log-probability by itself is not a corrupted PPO denominator. A deferred high
sample may, however, finish under the updated low policy and enter the following high update;
this changes completion/update eligibility and the stationarity premise. An unfinished high
sample at the fixed thirtieth endpoint also needs an explicit rule. We have not established
that a small bookkeeping-only repair preserves every previously selected condition. This is
not proof that a valid continuation implementation is impossible.

The DM retains the scientific A/N question and favors keeping equal actual interaction exposure
with a common, explicitly described complete-segment repair if its learning semantics are sound.
Equal counts of whole native episodes would give outcome-dependent and potentially unequal
actual exposure; silently changing to that comparator is not acceptable. Neither dropping/resetting
live history, inventing a fresh action at a collection boundary, padding after termination, nor
treating an adverse native ending as run failure resolves the selected question. A substantially
larger algorithm project may not be worth this one exploratory comparison. The unresolved choice
therefore changes the ordinary-training premise, rather than merely requesting code approval.

Current published main `60ecab12875492dd4a1407dc238bd3c7e83e5bc4` was refreshed and read. Pause
remains lifted and the direction/lead remains active. Shared background topic6 still supports
F's finite physical usefulness while retaining B07's material service losses and unresolved
training-exposure/geometry explanations. None of these source defects diagnoses the cause of
B07's fixed-policy losses or invalidates its retained observations. No shared learner was changed.

## Pro question 2026-09-24 ordinary-boundary-training-premise

Conversation: reuse the current private Jev direction conversation from the reconciled local
operation; its address remains local. This is a new source-grounded follow-up, not a resend of
`feedback-aware-training-after-h3000`.

Question: Given the newly demonstrated ordinary strict-HMASD boundary defects above, what is
the smallest defensible common training contract for the selected A-versus-N, same-F-deployment
comparison? In particular, can independent decision-time high storage with complete segments
deferred across a low-policy update still support this ordinary-learning package comparison,
and exactly how should completion eligibility, high GAE and the final unfinished segment work?
If that is not a sound bounded repair, choose and justify one concrete smaller revision or
recommend ending this unstarted recipe. Please resolve the scientific premise and estimator
meaning; an engineering approval or another generic reminder to preserve state would not answer it.

Standing: The immediately preceding entry supplies the actual new evidence and the DM's working
preference. The preceding full Pro Answer and fixed B08 L0 remain the intended comparison,
including same new initialization, S7-S2/N8/k10/native H3000, unchanged F only in A training,
common F deployment, full native HMASD objective and learner groups, seed915031, N then A,
2lanes ×3000 steps ×30 updates =180k actual training transitions per arm, dev941001–941008,
final942001–942032, one common initial F panel and two endpoints. No B08 fit has started and
these new worlds have not been evaluated. The complete B07 result still supports considering
the training intervention; the source defects do not turn its service-loss worlds into a
diagnosed training failure. One pair remains exploratory, with training n1 per arm.

The complete prior advice explicitly required preserving native live history on an early-ending
offset but did not specify cross-buffer high sample storage, eligibility or final censoring;
its claim that the implementation did not yet exist was correct. These are now material facts.
The candidate-only L0 cannot provide them through the present API. Ordinary terminal closure
and separating live-state reset from storage clear look like necessary common correctness
repairs, but they alone do not settle high-level continuation.

Please test the favored repair against the strongest alternative: keeping whole complete
episodes/skills and prospectively revising update or actual-interaction exposure. Do not quietly
equate those exposures, call mixed-policy high transitions strictly on-policy, invent a
sampled action for a suffix, erase rewards, add a loss mask/new head/mode feature, or assume
no native early ending. The native likelihood remains the actor's proposal; F only maps its
executed command. If the fixed cadence, exposure and unaltered estimator cannot all be kept,
name which condition must change and what narrower comparison it would measure. A useful
minimal counterexample or reasoning model is welcome; no new framework, result run, theory
survey or confirmation is requested.

Context (immutable reasoning inputs; attached excerpts will preserve these source meanings):

- Governance at source_sha: `docs/project/OPERATING_CONSTITUTION.md` sections1–8, especially
  DM autonomy, advisory consultation, shared correctness and the five scientific minimums.
  Owner pause and actual direction lead are read at main
  `60ecab12875492dd4a1407dc238bd3c7e83e5bc4`; no newer stop instruction is present.
- Methods at source_sha: `.agents/skills/hmasd-scientific-tools/SKILL.md`, sections on updating
  explanations, comparators and cost/exposure; `.agents/skills/hmasd-research-engineering/SKILL.md`,
  Core versus experimental, Checks and review, and runtime notes on policy freshness/tails.
  These are methods under the constitution, not extra permission requirements.
- Shared background at main `60ecab12875492dd4a1407dc238bd3c7e83e5bc4`:
  `docs/research/RESEARCH.md` topic6's B03–B07 service/risk/feedback evidence and active B08 row.
  Its effect here is to require a competent genuinely trained ordinary comparison and actual
  service readings while keeping geometry, state exposure and learning explanations unresolved.
- Exact source at `001dd55b2e6ed7e6a5e5dc746dcc86818dae01a0`: `hmasd/agent.py` methods
  `clear_buffers`, `reset_env_state`, `_batched_assign_skills`, `step`,
  `_store_coordinator_experience`, `store_transition`, `store_transition_batch`, `update`;
  `hmasd/utils.py::RolloutBuffer` high data storage, high GAE and high sampler;
  `experiments/candidates/uav_service_auxiliary/b04/native.py` collector/update/clear path;
  `envs/pettingzoo/relay/energy_aware.py::step` native early ending. D2 flush is contrast only.
- This NOTES file at source_sha: the full Answer to
  `Pro question 2026-09-24 feedback-aware-training-after-h3000`, the fixed B08 comparison/L0,
  the new boundary finding entry and this question. Prior empirical results retain their
  immutable evidence: B07 execution `47d56c9bcdc9fa9d6edee43ae0b4d44755115708`, interpreted
  in the complete B07 entry saved at `e49da2a9d2a69bb6750afa5ecadc372e36ebe848`.
  No raw re-audit of B07 is needed to settle this boundary decision; identify limits if citing it.

Prospective cost: no new training has started. The existing selected plan is 2fits/360k train
and at most360k evaluation transitions, 120 evaluation episodes. Any recommended change must
state its actual exposure/update/tail meaning and dominant engineering cost before DM selection;
do not expand fits, tune F, reuse old weights as the main baseline, or add panels. The strongest
investment alternative remains retaining B07 and declining this unstarted recipe. This is an
ordinary scientific choice, not an owner approval stage or an obligation to build infrastructure.

Constraints: no experiments or changes outside the unique empty `### Answer` below in
`docs/research/candidates/uav_service_auxiliary/NOTES.md`, branch
`codex/uav-service-predictive-control`, repository `CartmanFatass/My-paper-code`. Reason from
the immutable source_sha supplied in the actual message, then fetch the latest target blob
before writing. Preserve the question and every byte outside this Answer; stop on overlapping
edits. Return the actual Answer commit on successful write. If writing is unavailable, return
the complete answer in chat, not a blob SHA, receipt or link. Do not create another record.

Return: choose a concrete defensible contract or explain why the fixed recipe should stop;
separate unchanged learner mathematics from changed behavior/eligibility or return semantics;
resolve native termination, a mid-skill collection boundary and the fixed last endpoint;
identify the smallest discriminating engineering reproduction and the scientific interpretation
that remains supported. State MATERIAL_DISSENT yes/no about the unamended B08 training premise,
source use and any unread consequential evidence. The DM decides after reading the full advice.

### Answer

**GitHub 读取成功，但本轮未完成写回，实际 Answer commit：无。**本轮可见的文件写入动作要求整份文件替换；我没有完成能够逐字节保留其余长笔记的完整替换载荷，因此没有发出修改请求，不能将其说成 GitHub 拒绝了写入。最后核对的目标 blob 为 f91e1c60d0e4cb2cd114cc7a6f4177f8fe575818，指定 ### Answer 仍为空。没有修改仓库、另建答复文件或运行实验。以下是完整答复。

B08 边界前提：保留固定交互预算，明确采用完成段延期更新及最终删失

MATERIAL_DISSENT: yes。

异议针对未修订的 B08 训练前提：现在不能再同时声称“只需候选目录接线”“普通高层估计器的含义未变”“跨更新保留全部技能后果”而不规定高层存储、完成资格和最终尾段。它不是对 A/N 科学问题的否定，也不意味着 B07 的服务损失已经被诊断为训练边界故障。新发现明确发生在尚未启动的训练实现上。

hmasd-pro-question-usa-ordinary…

我选择的合同是：保留每臂精确 180k 实际训练 transitions 和 30 个更新阶段；两臂共同采用独立的决策时刻高层记录，真实终止立即闭合，跨采集边界的技能保持执行，完整段在首次完成后的更新阶段进入高层训练；固定最后端点的未完成段显式删失，不补采、不伪造闭合。

这一方案可以支持明确修订后的、有限预算的普通 HMASD 学习包比较。它保留原生损失公式，但改变高层样本的更新资格、部分 bootstrap 连接和最终信用覆盖；跨低层更新完成的高层段是混合行为版本的数据，不能称为严格 on-policy，也不能视为单纯存储重构的数学等价实现。

一、三个缺陷需要一起修，单独保存 live state 不够

附件给出的代码足以支持以下区别。

**真实终止不是未完成数据。**当前 strict 路径仅在 skill_timer == k-1 时存高层样本，随后 reset_env_state 又移除 pending 决策。一个在技能中途结束的真实 episode 因此可能丢掉其最后高层决策的已实现奖励，并使高层序列错误地接到下一 episode。原生“全部耗尽且无人充电”的终止路径确实存在，不能把它当成不允许出现的运行异常。

hmasd-pro-question-usa-ordinary… +2

清训练存储不是重置执行历史。clear_buffers 清除 timers、pending 和累计奖励；下一次 step 发现 timer 缺失，会初始化技能并重置循环数组。只保留物理环境和 F 模式，不能阻止这个执行变化。

hmasd-pro-question-usa-ordinary… +1

**pending 字典不是自足的高层样本。**当前决策保存 rollout-local time_step，闭合用局部行差求持续时间；高层 sampler 又从那一低层行读取 state、observation 和技能。复制旧字典到新 buffer 后，即使 log-probability 数值仍正确，也可能把它配到另一个决策输入上。

hmasd-pro-question-usa-ordinary… +2

所以，共同修复至少要覆盖决策事实的所有权、终止闭合、执行状态与存储分离，以及高层序列的真实相邻关系。不能仅做 snapshot/restore，也不能开启具有另一套片段合同的 D2 来替代普通参照。

hmasd-pro-question-usa-ordinary…

二、我建议采用的精确共同合同
1. 高层记录在真实决策时刻建立，不依附低层行

对每个环境 lane，用持续递增的交互计数、episode ID 和决策 ID 标识样本。一次真实高层采样建立一份独立记录，复制保存：

决策时实际使用的 state、observations、团队／个体技能及其各自行为 log-probability。

决策时的团队／个体 value，按当时 ValueNorm 还原到真实回报单位保存。

决策开始位置、行为高层版本、实际持续步数、逐步累计奖励及闭合原因；跨更新时另保留低层版本的变化。

这些数据必须拥有自己的存储，不能是随后会被 reset 或复用的低层数组视图。高层 sampler 的输入、回报、ValueNorm 数据和相关诊断，都从同一批独立记录构造；不能只替换 sampler，却仍让别的高层读取函数沿用低层有效行索引。

**再次抽到相同技能标签仍是一次真实新决策；F 进入、退出或覆盖命令本身不是高层重采样。**执行更新频率仍遵循原生 k10，而不按标签是否改变判定决策。

2. 真实终止立即闭合，之后才 reset

每次原生转移先保存真实 reward、next observation/state 和结束标志，更新该高层段的奖励累计与持续步数，然后按以下顺序处理：

**出现原生 termination 或本任务的有限 H3000 truncation时，立即把当前高层决策闭合为 terminal。**即使只执行了 1 至 9 步，也是一条已经完整观察到终点的高层样本；其 duration 使用真实步数，后继 value 为零，GAE 不能越过 reset。

正常执行到 k 步而未结束 episode 时，闭合为 nonterminal。结束标志与 k 边界同时出现时，只闭合一次，并保留 terminal 语义。完成记录保存后，才允许原生 reset 清除该 lane 的执行状态。

这里将 H3000 truncation 按既定有限任务结束处理，不是在新比较中采用另一个无限任务的 time-limit bootstrap。环境奖励及终端 PBRS 也不重新计算。原生代码已经把实际 episode 结束传入奖励构造。

hmasd-pro-question-usa-ordinary…

3. 中途采集边界只改变学习阶段，不制造决策或终止

在每个 3000-step/lane 采集边界：

低层和判别器使用本阶段实际采集的数据，按原定 epochs 和 sampler 规则获得一次阶段资格。“一次资格”不是只做一次梯度使用；PPO 的多 epoch 保留。上一阶段的低层前缀不能因为高层段尚未完成而在下一阶段重放一遍。

仍在执行的物理 episode 保留其 F 模式、held skills、技能时钟、actor/critic hidden state，以及独立 pending 高层记录。清除的只是已消费的训练存储，不是这些 live state。

参数更新后，下一真实动作由更新后的网络、保留下来的实际循环状态和下一观察产生。保留 hidden state 不等于它已由新参数从 episode 起点重新计算；这是明确的跨更新执行合同，不增设整段历史重建。原来的高层动作继续持有到真实 k 边界或原生结束，不为后缀虚构另一次技能采样。

4. 完成资格采用“首次完成后的阶段”，不按开始行或回报筛选

记第 j 个采集阶段结束时的每-lane 交互位置为 B
j
	​

=3000j。本阶段高层训练集合为：

E
j
	​

={d: d 已真实闭合，闭合位置不晚于 B
j
	​

， d 尚未获得过高层阶段资格}.

这包括上一阶段开始、这一阶段才完成的段，也包括这一阶段内真实提前终止的短段。未完成段不进入 E
j
	​

。所有 eligible 记录统一使用既定高层 PPO epochs；末尾不足整 minibatch 的真实记录也应保留，不能按回报、版本年龄或是否发生 F 覆盖筛选。

更新前冻结这一集合及其 targets。一个高层样本完成该阶段训练后即标记为已消费，不因下一阶段得到了更长未来而回头修改它或再次训练它。低层的阶段资格和高层的完成资格是两条不同时间线。

这一合同保留 30 次计划更新阶段，却不保证两臂高层样本数或实际 optimizer steps 完全相同。提前终止会改变决策数量和 minibatch 数量；人为复制样本来配平不是相同训练机会。原高层 sampler 本来就是遍历实际有效样本并保留最后一个小批。

hmasd-pro-question-usa-ordinary…

三、高层 GAE：必须沿决策序列，不沿全局 buffer 末行
保留原生数值约定，而不是悄悄换成另一种回报

冻结普通路径累计的是段内未折扣奖励和；高层 continuation discount 则是 γ
τ
。其辅助函数递推使用一次 lam，并不是 λ
τ
。这三点应原样保留：不能借边界修复加入段内折扣、改固定 γ
k
，或改成逐 primitive 的 lambda 权重。

hmasd-pro-question-usa-ordinary… +1

对已完成高层段 i，定义

R
i
	​

=
t=s
i
	​

∑
s
i
	​

+τ
i
	​

−1
	​

r
t
	​

,d
i
	​

=γ
τ
i
	​

,D
i
	​

=1{原生 episode 在该段结束}.

分别对团队 value 和每个个体 value 使用下式，记相应决策时真实单位的旧估计为 V
i
b
	​

：

δ
i
	​

=R
i
	​

+d
i
	​

(1−D
i
	​

)V
i
+
	​

−V
i
b
	​

,
A
i
	​

=δ
i
	​

+d
i
	​

λ
h
	​

(1−D
i
	​

)
A
next
	​

,
G
i
	​

=
A
i
	​

+V
i
b
	​

.

其中 
A
next
	​

 只在同一 episode、同一冻结资格集合中的真实连续下一决策存在时递推；资格集合的末端取零尾 trace。terminal 同时切断 bootstrap 和 trace。

这是对当前宏段奖励约定的保留，不应包装成对逐 primitive 折扣目标的精确重新表达。边界修复改变的是哪些真实记录进入递推以及后继在哪里，而不是偷偷统一整个项目的折扣约定。

V
i
+
	​

 的四种情况必须固定
已完成段的实际后继	使用的 bootstrap
该段原生 terminal/truncated	零；不读下一 episode 的值
下一真实高层决策已采样，且也在本次 eligible 序列	下一决策记录中保存的真实单位 value
下一真实决策已采样，但它的段仍 pending	该 pending 决策开始时保存的 value；本次 trace 在这里截断
段恰好在采集末端完成，下一决策尚未采样	在这个实际下一决策边界，用更新前网络作一次纯 value 查询；不抽技能、不推进环境或循环历史

第三行是本题的关键：若 pending 段在 row10 开始、采集在 row12 停止，前一完整段的后继是 row10 的决策 value，不是 row12 的全局 collector-boundary value。

第四行是普通的边界 bootstrap，并不伪造一个后继高层动作。它也不应要求跨更新后的实际下一决策 value 与这次更新前的 bootstrap 完全相同。查询所用参数与 normalizer 版本必须确定，不能在高层更新后再改变已构造的 target。

pending 段在下阶段完成时，用它保存的原始 V
i
b
	​

、完整实际奖励和真实后继，构造自己的首次 target。不把它的前缀奖励提前塞进上一完整段，不以其未来 advantage 回填已训练的前一段。

所有已存 value 均已是决策时还原的真实单位，不能用更新后的 ValueNorm 再反归一化一次。原高层 loss 仍按本次 eligible returns 更新统计并归一化 targets；原有 clipping、优势归一化、团队／个体 PPO 比率及熵项不变。

hmasd-pro-question-usa-ordinary… +2

四、旧 likelihood 正确，不代表混合高层转移变成严格 on-policy

我同意题面指出的区别：**决策时的行为 log-probability 本身不因延期就损坏。**应保持

ρ
i
	​

(θ)=
π
b
i
	​

	​

(z
i
	​

∣x
i
	​

)
π
θ
	​

(z
i
	​

∣x
i
	​

)
	​

,

团队和个体分别沿原实现计算。不能在段闭合时把分母刷新成当前策略概率，也不能把旧动作绑定到新 buffer 中恰好同号的行。冻结代码明确使用新旧 log-probability 之差形成比率。

hmasd-pro-question-usa-ordinary…

但跨边界段的前缀由低层版本 ϕ
j
	​

 执行，后缀由 ϕ
j+1
	​

 执行；它首次进入高层训练时，高层也可能已经对其他样本更新过一次。这个单一高层比率没有校正低层策略变化、随之改变的转移分布，或跨阶段 GAE 的全部分布差异。

一个最小反例

考虑一个两步技能，高层在开始时选 z∈{−1,+1}，两种选择概率一直都是 1/2。每步回报为 r
t
	​

=za
t
	​

。

旧低层总选 a=+1，新低层总选 a=−1。若两步都由旧低层执行，段回报是 2z；两步都由新低层执行，则为 −2z。若恰好在两步中间更新低层，实际段回报为零。

高层概率完全没变，ρ=1，却不能把这个零回报变成任一冻结低层的回报。这个推理例子只去掉了 UAV、队友和神经优化的复杂性，说明：

保存正确旧 likelihood 解决的是“这个动作由谁采样”，不是“完整技能由同一低层行为过程生成”。

因此，我接受的是有明确行为版本和完成资格的经验 PPO 近似更新，不是一个已证明无偏的高层策略梯度。保留原损失代数并不意味着统计估计对象完全不变。

这仍可用于有限包比较：两臂共同使用同一明确算法，分别真实训练，再在共同 F 下测量完整服务。它测量的是 F 训练接入与该共同更新制度一起产生的有限学习后果，不能把结果唯一归因为“学会了干预后的历史恢复”。

两臂使用同一修复也不保证偏差相消。F 可能改变提前终止频率、段跨界数量以及旧记录进入下一次高层更新的比例。应保留这些实际计数，不把“共用代码”当作忽略它们的依据。

五、固定最后端点：未完成段删失，不伪造终止

第 30 次采集结束时，按既定预算停止环境交互，然后执行第 30 次更新。处理如下。

所有已经完成的段，包括在最后一条实际转移上 terminal 或刚完成 k 步的段，正常进入最后的高层资格集合。

仍然 pending 的段保留其原始决策事实、已观察 duration、奖励前缀和末端状态，标记为“训练预算端点删失”。它不变成 terminal，不被强制闭合成一个短技能，不用当前高层 state value 假装还剩技能的精确 continuation，也不制造一个用于后缀的 sampled action。

该前缀的每条原始转移仍留在原生轨迹和成本中，并接受第 30 阶段既定的低层／判别器训练资格；只是没有形成该决策的完整高层训练 target。最后一个完成段仍按上一节规则，在真实下一决策处 bootstrap。

**这不是“所有已观察奖励都获得了高层信用”。**最终 pending 前缀没有作为完整高层段被训练，必须明确报告。它也不是依 F 状态添加的 loss mask，而是两臂共同的完整样本资格规则；最终删失依赖实际 episode 相位，不能假定随机缺失。

在固定 k10、两 lanes 下，最终至多有两条这样的 pending 段，每条已观察前缀最多 9 个 transitions，即至多 18 个团队 transitions 的前缀未形成完整高层 target。这个计数上界不证明其科学影响可以忽略，尤其不能忽略其中的有符号奖励或极端事件。

同理，29 个内部边界至多各留下每 lane 一条跨界段，即至多 58 条延期高层段；它们在下一阶段开始后的至多 9 步内应正常完成或遇到原生结束。这里的“一阶段延迟”包含那一阶段实际发生的多次 optimizer 更新，不能理解为参数只走了一个很小的梯度步。

若坚持“每个已采集奖励最终都必须进入一个完整高层样本”，那么精确预算端点与这一完整段规则就不能同时保证；必须改暴露、终点，或引入另一个截断 target 估计器。我在本建议中选择保留预算与终点，明确放弃无删失的高层信用覆盖。

六、最小复现应直接检验这些语义，而不是再跑一个阳性 pilot

题面给出的 k4、collection12、row5 原生结束已经是一个很好的最小复现。建议用两次采集阶段，并让另一 lane 保持正常对齐；以下 row 为该 lane 持续递增的真实交互位置。

hmasd-pro-question-usa-ordinary…

高层决策开始位置	实际奖励范围	闭合与首次资格
0	r
0
	​

,…,r
3
	​

	正常完整段；更新1
4	r
4
	​

,r
5
	​

	row5 terminal，duration2；更新1
6	r
6
	​

,…,r
9
	​

	新 episode 的完整段；更新1
10	更新1前 r
10
	​

,r
11
	​

，更新1后 r
12
	​

,r
13
	​

	保留原决策，duration4；更新2
14、18	各自四个实际奖励	更新2
22	r
22
	​

,r
23
	​

	固定两阶段端点未完成，删失；不进入高层更新

这个复现至少要有以下可区分预期。

**终止链条正确。**row4 的 target 含两次奖励、bootstrap 零；row0 的 trace 可以接 row4，但不能接 row6 的新 episode。

**第一次边界正确。**row6 的最后 delta 为

δ
6
	​

=R
6
	​

+γ
4
V
10
b
	​

−V
6
b
	​

,

并在 pending row10 处截断本次 trace。令 fixture 中 V
10
	​

 与 V
12
	​

 明显不同，就能检测错误地使用 collector 末端 bootstrap；不需要 UAV 成绩来判断。

**延期身份正确。**第二阶段的 local row0/1 只是原 row10 技能的后两步。高层重放必须得到原 row10 的 state、observations、标签、旧 likelihood/value 和四个奖励，不能得到第二个 buffer 的 local row10。让后者拥有刻意不同的数据，可以直接检出错配。

**更新资格正确。**低层 row0–11 只属于更新1，row12–23 只属于更新2；规定的每个 epoch 内照原 sampler 使用，不因延期高层而重复旧低层前缀。高层 row10 只在更新2获得一次阶段资格，row22 不进入最终高层集合，但其原始奖励仍可恢复。

**概率与版本检查正确。**在更新1中确实改变高层／低层参数。更新2开始时，延期 row10 的当前概率可以不同于其保存的行为概率；不能要求其比率必为1。要检查的是分母确实来自决策时刻，而不是拿当前网络反算后覆盖。

再以实际 terminal/truncation 重合边界、无提前结束的对齐路径覆盖相邻情况。独立算术预期应直接从已知奖励、duration、value 和 episode ID 计算，不复用候选 GAE 函数作答案。正常对齐路径应尽可能保留原样本顺序、归一化和随机流行为，任何差异按实际改变解释。

这些是给修复者的工程复现要求，本轮没有执行它们。此前 12 项检查通过仍是题面报告的既有证据，不能冒充已覆盖这条新边界路径。工程方法也明确要求区分重放、统计复制和算法等价。

hmasd-pro-question-usa-ordinary…

七、最强替代不是忽略尾段，而是先完成技能再更新

最有力的竞争合同是：

每阶段先采集每 lane 3000 步，再在更新前的同一网络版本下继续完成该 lane 当前技能；已到真实技能／episode 边界的 lane 暂停，待各 lane 都闭合后再更新。

这可以避免一个高层段的低层执行跨参数更新，并消除最终未完成高层段。它不是坏方案；其额外交互上界甚至不大：固定 k10 下每 lane 每阶段至多再需要 9 步，因此每臂

T
arm
	​

=180000+
j=1
∑
30
	​

ℓ=1
∑
2
	​

ϵ
jℓ
	​

,0≤ϵ
jℓ
	​

≤9,

即至多 180540 个实际训练 transitions。

但必须承认它换了什么：

**实际暴露和更新时刻变为轨迹依赖，两臂不再保证精确相等。**不能把这些额外步称作“仅 bookkeeping、不计训练”；也不能只采高层尾段而丢弃其真实低层训练数据。

**两 lane 的技能相位可能不同，继续同步推进固定步数并不保证两者同时闭合。**需要处理真实暂停／非矩形采集，不能靠伪造 no-op 转移填满数组。低层 sampler 的不足整 chunk 尾部也要明确处理；当前源码存在按整 chunk 取有效长度的路径，因此“追加几步即可、其余全部原样”并不成立。

若进一步要求每次更新只使用整个完整 episode，则代价更大。每阶段各 lane 恰好一个完整 episode、共30阶段时，实际训练量是两臂各自 episode 长度之和，最多180k但可能不同；收集更多完整 episodes 直到达到固定步数，又会产生不同的超额暴露。不能把这些合同与精确180k视为等价。

我仍优先选固定暴露、延期完整段的合同，因为本题要比较有限相同交互预算下接入 F 的用途；独立高层记录可以把变更集中在高层事实、资格和连接上，不必同时重做可变长度低层收集与尾部采样。其代价是明确接受跨版本的近似高层更新，而不是声称这个代价不存在。

若 DM 的实际研究目标必须要求每个高层段在单一冻结低层下执行，那么上述“完成技能后更新”应成为一个明确改暴露的替代计划；不应继续使用我选的延期合同又称其严格 on-policy。若两种共同修订的工程成本都已不值这一次探索，保留 B07、结束未启动的 B08 也是有根据的选择，不产生额外审批或必须建设基础设施的义务。

八、哪些原条件保留，哪些必须修订
条件	本建议的处理
seed915031、N后A、两 lane、每 lane每阶段3000步、30阶段	保留
每臂180k实际训练；共同初始F评价和两个终点F评价	保留
新初始化、H3000、N8、k10、原生目标、全部学习器组、F本身	保留
原团队／个体PPO、价值损失、熵项及原生段奖励／折扣代数	保留其公式，不借修复换算法组件
strict终止闭合、live state与storage clear分离	共同正确性修复
依附低层行的高层存储与sampler	改为独立决策记录
高层完成资格、跨资格边界的bootstrap／trace、最终pending处理	明确修订
每条高层转移严格来自同一冻结低层；所有观察奖励均形成最终高层target	不再声称

原 L0 限制只改候选目录，已经不足以容纳这个正确性合同。需要 DM 明确调整共有学习接口的实现范围，至少涉及 hmasd/agent.py 与 RolloutBuffer 高层消费路径；不能用候选 monkeypatch 或旧字典复原来隐藏这项改变。历史 B01–B07 代码和结果仍按各自冻结版本解释，不追溯修改。核心变更采用现有的相应检查与独立 review，不增加新的审批制度。

hmasd-pro-question-usa-ordinary… +1

所选合同仍为 2 fits／360k训练，加最多360k评价 transitions、120评价 episodes。高层延期记录不增加环境交互；每 lane 只需持有至多一个 open 决策及当前 eligible 记录，不需要长期经验库或新模型。但独立高层数据消费、GAE连接、终止/reset分离与回归检查，是实质新增工程，不能记为零成本。实际高层样本数、各优化器步数、跨版本段数、最终删失前缀及其有符号回报都应保留；实际 wall 和支持成本目前未知。

hmasd-pro-question-usa-ordinary…

九、剩下可支持的科学判断

**被加强的是共同边界修复的必要性；被削弱的是上一答复把它留作普通接线细节即可的前提。**这次明确的错误路径要求修改训练合同，而不是再提醒一次“保留状态”。

**保持的是 A/N 的有限用途问题及 B07 的既有解释。**共享背景要求一个真正完成学习、拥有相同训练权利并共同部署 F 的普通对照；这里的修复应同时作用于 N/A，不应成为候选专属增强。B07 的物理补能与服务损失仍然是旧制品上的观察，不能从源码缺陷反推其某个坏世界的原因。

hmasd-pro-question-usa-ordinary…

修订后的比较仍可以问：**在这套精确预算、完成段近似更新制度下，A 是否相对共同初始化学到实际服务，并在同 F 部署下超过新训练的 N，同时保留原生 J／风险和全部不利世界。**它不单独识别历史恢复机制、终止修复的贡献或训练总体排名；一次训练对仍是每臂 n=1。

原先的投入结束分支继续适用：没有值得保留的额外完整服务，只有成本节省或条件窗口改善，或者候选自己并未学到有用服务，都不足以继续这一固定配方。边界处理正确只使这些读数有意义，不提供阳性结果，也不自动授权第二对、训练延长或新的估计器。

hmasd-pro-question-usa-ordinary…

来源与未完成的工作

我已阅读全文附件，包括上轮完整 Answer、固定 B08、边界发现、治理／方法、共享背景和全部选定代码；并读取了指定提交的 GitHub 问题、治理与方法、主线 owner/方向状态，以及精确实现中的 GAE辅助函数和低层尾部采样路径。正文中的修订合同与两步反例是基于这些代码提出的推理，不是已实现结果。

没有独立运行新的边界复现、验证一个修复后的共有学习器，也没有重审 B07 的仓库外原始轨迹；本题不需要以那项原始重审来决定边界语义。目前没有缺少到必须猜测的关键文字来源，真正未完成的是所选共同修复的实现、数值／资格回归和实际训练观察。

最终建议：以 MATERIAL_DISSENT: yes 修订未加说明的 B08 前提，保留固定交互预算，采用独立决策记录、首次完成资格、真实决策后继 GAE，以及最后未完成段的显式删失。可以继续的是这个范围清楚的近似学习包比较，不是“所有 estimator 与行为前提都原封不动”的 B08。

## 2026-09-24 — B08 boundary advice saved; common completed-segment contract adopted and core L0

### Complete reading, material dissent and DM choice

The new question at `640b6665e6fead6544543488f9310814ea26d0d9` was sent once with key
`hmasd:3a29755582c377fb921faa938b5d3c279c795419f913c0e3620737fc73aa4b8b`. The generation100
READY event `25372edd00edbdde5391299a` under wake `1f9cf746-579d-41b5-bf14-6399eee3e3c9`
collected the complete11198-character body, SHA-256
`330e09b3e70046d278405808485086ea92cc21bfbd6781c54d262967ad5baa53`.
The saved11199-character/25079-byte file including final newline has SHA-256
`102d6a9573fdc575e0f0d8d9879b5245c51dc43d685fbbd64d2ba3ac26f9429e`.
The full text above is **saved from chat**, verbatim. Deliver returned NOT_DELIVERED, with
no Answer commits. Before taking the subsection back, the local and fetched target still
matched the pinned empty question. Pro reported a visible whole-file write action but did not
construct/send its replacement payload; this is not a rejected GitHub write or missing write
capability. The reported hash is a blob identity, not a delivered commit.

The DM read the full answer and accepts MATERIAL_DISSENT:yes about the unamended training
premise. Keeping actual interaction exposure, state continuity and complete high-decision facts
requires an explicit eligibility/return contract; it cannot be called an equivalent candidate-only
rewiring. I choose Pro's completed-segment contract as a bounded common repair for both N/A.
It retains the scientific question and original fixed exposure while honestly narrowing the
meaning to a matched approximate learning package. The strongest alternative, completing each
lane's skill before updates, would require nonrectangular low-level collection and trajectory-
dependent extra exposure (at most540 additional transitions per arm under fixed k10). That is
not selected. Neither original zero-cost equivalence nor strict on-policy high transitions is claimed.

The source confirms decision values are already denormalized in `_batched_assign_skills` and
ordinary GAE is called with `value_normalizer=None`; the new path must preserve real units
across ValueNorm changes. Native high reward is the undiscounted actual segment reward sum;
continuation uses gamma**duration and one native high GAE lambda factor. The browser-flattened
formula in the verbatim answer is not executable authority: PPO remains exp(new_logp-old_logp).
The two-step counterexample correctly shows that a valid high likelihood cannot correct a
low-policy change inside a held skill. This is a reasoning example, not empirical evidence.

Current main `426c33aa9b50f227eff7bac1dc98e91cd32d61f3` was refreshed; relevant shared topic6 is
unchanged from the prior reading, pause remains lifted, and the direction/lead remains active.
B07's finite physical benefit, service losses and unresolved explanations are untouched. Its
fixed-policy bad worlds are not retrospectively diagnosed by these prospective learner defects.
The revised comparison still has training n1 per arm and cannot identify recovery mediation,
repair contribution or population superiority. The already fixed service/J/risk interpretation,
adverse-world retention and no automatic extension branches remain in force.

### Revised common contract before any B08 fit

All original seed915031, N-then-A order, lane seeds, native H3000/N8/k10, reward coefficients,
model/normalizer initialization equality, native learner groups, F definition, evaluation worlds,
common initial panel, two endpoints and physical/opportunity readings remain fixed. Cost stays
2fits/360k actual training plus at most360k evaluation transitions,120 evaluation episodes.
Each arm has exactly2 synchronous lanes ×3000 actual steps ×30 update phases. Actual optimizer
counts need not be equal when native endings create different high sample counts; retain them.
No extra environment interaction, low-level prefix replay, loss mask, input, network or panel.
No B08 fit has started. Engineering work and actual wall remain additional, presently unknown costs.

For both arms:

- A genuine high decision creates an owned record of its lane, episode and persistent decision
  identity, global lane interaction index, copied decision state/observation/skills, original
  team/agent likelihoods and real-unit values, high behavior version, and accumulated actual
  reward/duration. Repeated sampled labels are distinct decisions. F mode changes are not decisions.
- Actual terminal or finite-H3000 truncated transitions close immediately, with actual duration
  and terminal flag, before reset. A k-boundary coincident with native ending closes once.
  Nonterminal k-complete segments also close once. Episode identity prevents cross-reset GAE.
- Completed, not-yet-consumed records receive high training eligibility at the first subsequent
  update phase. Freeze that collection and its targets before parameter/ValueNorm updates; apply
  unchanged PPO epochs, shuffle and remainder-minibatch rules. Consume each record in one phase.
  Every low/discriminator row keeps only its own original phase's native training eligibility.
- GAE follows true consecutive high decisions within lane/episode and this eligible set. A terminal
  successor is zero; an eligible next decision supplies its saved value and recursive advantage;
  an already sampled pending next decision supplies its saved value but ends this phase's trace;
  when the next decision has not yet been sampled at a true boundary, query the pre-update value
  there without sampling skills, stepping the environment or advancing GRU. No global-boundary
  substitution when a pending successor started earlier, no later backfill of consumed targets.
- Preserve the original undiscounted segment reward sum, gamma**actual_duration, one native GAE
  lambda factor, team/agent losses, advantage normalization, entropy and ValueNorm conventions.
  Saved decision values remain real-unit values, never denormalized again under newer statistics.
- At a nonterminal update boundary retain physical/F state, held skills/timers, actor/critic
  history and the independent open decision. Updated networks act from the retained history;
  it is not reconstructed under new weights. A crossing segment records all actual lower-policy
  versions; its complete target enters the next phase. This is a bounded mixed-behavior PPO
  approximation. Correct behavior denominators neither establish unbiasedness nor cancel bias
  between arms; record crossing/staleness counts and signed rewards.
- After the thirtieth collection, train all completed records normally. Remaining open records
  are explicitly budget-censored: preserve their original facts, observed reward prefix/duration
  and last state; do not force terminal/closure, bootstrap an invented suffix or top up interactions.
  Their observed low/discriminator rows still train in phase30. At most2 final prefixes/18 actual
  transitions lack a complete high target, and at most58 segments cross the29 internal boundaries.
  Preserve their signed rewards and events; these count bounds do not prove negligible impact.

### L0: shared ordinary completed-segment path, then candidate integration

The immediate Implementer task owns only `hmasd/agent.py`, `hmasd/utils.py` and a focused
`tests/hmasd/test_ordinary_completed_segments.py`. Implement this contract in shared code,
not candidate monkeypatches. DM owns NOTES, scientific choices, candidate integration,
publication and launch. Other writers may work in candidate files; do not revert their edits.
No result-bearing run, additional consultation, commit/push or child is assigned to the Implementer.

Use a narrowly enabled config field `ordinary_completed_segments=True`, selected identically
by B08 N/A; default false preserves existing callers and frozen/default behavior. Restrict this
new path to ordinary strict fixed-k HMASD, reject D2/HA or incompatible alternate flow. B08's
state/observation normalizers are disabled; explicitly reject those unsupported input-normalized
combinations in this first path rather than silently replay a changed input scale. ValueNorm is
supported and covered by tests. Do not modify frozen B01–B07, environment physics, models,
control/transport/admission or another direction. This opt-in is a common baseline repair and
explicit eligibility change for B08, not an arm-specific treatment or retroactive historical fix.

Agent transition storage must create/copy/open/advance/close ordinary records through the real
existing collector API. RolloutBuffer supplies an independent high data view for count checks,
likelihood diagnostics, GAE, get_all_high_level_returns, sampler and update statistics; none may
fall back to a stale low row. Preserve the real standard coordinator optimizer/loss implementation.
All high consumers must read the same frozen eligible collection. New records should retain the
old time-major/lane-major sample order in the aligned case where feasible. Incompatible R39A
same-policy likelihood-equals-current checks must not silently reject valid deferred behavior;
likelihood provenance is checked at sampling and preserved, while current ratios may differ.

On this enabled path, `clear_buffers()` disposes only consumed rollout/discriminator/high training
storage and per-rollout diagnostics, preserving live execution and open decisions. Native
`reset_env_state` owns actual episode resets and must not silently discard an unclosed record.
Provide `ordinary_high_level_snapshot(final=False)` for the caller to copy current completed/
consumed records, pending records and counters for raw artifacts; `final=True` reports pending
records as budget-censored after the last update without manufacturing credit or another action.
Expose lane/episode/decision IDs, start/end/duration/rewards, behavior and consumed phase versions,
terminal/reason, successor/bootstrap facts and cross-version information needed to audit targets.
Keep storage bounded to the current phase plus at most one open record per lane, not a replay bank.
Return the concrete snapshot field schema to the DM for candidate integration.

Required checks use real step/store/storage/sampler/update paths: k4, collection12, row5 native
ending in one of two lanes, two phases with actual high/low parameter movement, preserved live
skill/GRU/F-compatible state, exact original row10 decision facts across buffer reset, original
likelihoods despite a changed current policy, and row22 final censoring. Independently calculate
known reward/duration/value GAE with V10 different from V12; prove terminal cuts and pending
successor trace cutoff. Check high phase eligibility and original low row membership under all
native epochs, ValueNorm real-unit stability, same-label resampling, exact-boundary terminal once,
aligned/default-path compatibility, and final prefix recoverability. Pytest owns/cleans scratch.
Use existing scientific venv with its bin on PATH for Ninja; install nothing. Independent Reviewer
checks the actual diff and reproduction after author checks; DM accepts before integration/launch.

The DM will then complete the candidate collector/runner in the already assigned B08 paths,
select this same shared contract for both arms, retain fixed initialization/evaluation isolation,
and write raw high records/censoring plus proposal/submission/actual-transition diagnostics.
That integration and an active-F native smoke also require independent engineering review before
exact input publication and admission. This is scoped implementation within the revised choice,
not another scientific decision round.

## 2026-09-24 — B08 implementation accepted after independent core and collector review

The DM read and accepted the shared ordinary completed-segment diff and candidate integration
against the preceding revised contract. The core Implementer owned `hmasd/agent.py`,
`hmasd/utils.py` and its focused test; the DM implemented the B08 collector/batch. Separate
read-only Reviewers examined core semantics and candidate execution. Neither reported a
remaining material finding. Review is engineering evidence, not scientific acceptance or an
additional grant of research authority. B08 remains unstarted at this commit.

The common opt-in retains genuine high decision facts independently of low rollout rows,
freezes first-eligible completed targets, preserves live history and pending records across
update/clear, and records final prefixes without manufactured high credit. One interface
clarification: a pending record's `end_interaction_index` is the last observed prefix transition;
`end_phase_version` and `close_reason` remain null until actual closure. DM review also required
true-boundary value queries to fail before learner/global-step mutation and the opt-in phase200
monitor to avoid the legacy row mask and forced collection. Default behavior remains selected
when the new flag is absent/false; no historical result is reinterpreted.

The candidate saves original proposals/log-probs, F-submitted commands, actual native rewards,
ends/episode clocks, physical source energy facts, service metrics, F opportunities and boundary
state in runner artifacts. Source facts are saved before derived ledger validation. The storage
assertion compares actual proposal/log-prob/native-reward arrays to the real low buffer. Actual
post-transition observations/state enter native intrinsic/discriminator storage before episode
reset into distinct arrays. High before/after snapshots preserve complete original decision
facts, successor/target/version data, consumed identities and final observed prefixes. The
runner records actual native sample presentations and optimizer counts rather than inferring
identical optimization exposure from identical interaction budgets. Per-fit wall and process
high-water RSS are measured; CPU user/system time is measured only for the batch.

The fixed batch constructs N and A separately from copies of one frozen configuration, verifies
actual parameter/buffer/normalizer/sampler/global-RNG/evaluation-state initialization equality,
evaluates one common initial F panel (development/final slices), and runs the fixed N-then-A
training and endpoints without a score-conditioned branch. Evaluation uses a separate learner
and preserves the training agent's final pending prefix. Technical failure keeps partial
artifacts and halts the batch without an automatic retry; all signed endpoint effects remain.
No other seed, arm, intermediate panel, loss, F threshold or native environment change was added.

Validation before result execution:

- Core author's focused/default recurrent-buffer set:19 passed; updated focused file:8 passed.
  Core Reviewer independently ran19 checks in2.77s and the two updated compatibility checks in2.64s.
- The real k4/two-lane/two-phase fixture includes row5 native ending, original row10 deferred
  decision, distinct V10/V12, changed-current versus original likelihood, actual high/low movement,
  phase-only low membership, real-unit ValueNorm and row22 final prefix. The aligned enabled/default
  single-phase comparison captured every coordinator presentation plus targets/losses/all learner
  state tensors: observed maximum drift0.0; allowed tolerance8 times FP32 epsilon. Absent/false
  is exact in its fixture. This does not establish historical prepatch bitwise equivalence.
- The historical update-phase equivalence harness was unavailable: its missing tape regenerated
  with a pinned-digest mismatch before comparison (8b6f… versus d870…). The owned generated tape
  was removed. This is an unexecuted historical comparison, not a passing compatibility result.
- Candidate suite:17 passed in6.38s; separate Reviewer17 passed in6.16s. Later batch fixtures:
  3 passed in2.32s, including adverse N with A still executed, technical N failure, mismatched A
  initialization and output reuse refusal. Actual short native N/A collection with active F,
  native H7/k4 endings, two phases and immutable F evaluation after final censoring:3 passed,
  2 CUDA cases skipped locally in6.17s. Partial ledger rejection preserves the already executed
  row's raw facts and distinguishes executed, validated and stored rows.
- Compile/diff whitespace checks pass for changed code. A separate actual-node CUDA version of
  the same native collector/update/evaluator test is available and will be read before launch;
  no GPU correctness claim is made from CPU verification.

Accepted production-file SHA256s at this boundary: core agent
`f74e37c70a982b0a0a4230e648912df352659df8ae6232fa0e0a0c3f347c7f44`, core buffer
`cd5b4d9ba22bbae6826e81a65ead8d1b828ac5f56b60494b78e6e92c6c29a375`, B08 batch/evaluator
`6a0ab0066aac5b66152a5723328d5a6dd35dbb797e736d0273f8174294680eb3`, B08 collector
`26e403ab068d7c6053f7eb3a6820adba1334107d8b8c8b8d9689c8d5acc0bc57`.
The separate core test's final digest is
`63508369b2e20fd71bda61600eff0f652348ea2920315ec50fe125ff7ac65190`.
The earlier scientific interpretation is unchanged: this tests one finite trained package pair
under an explicit mixed-behavior/eligibility approximation, not an unbiased estimator, recovery
mediator, universal superiority or cancellation of approximation bias between arms.

## 2026-09-24 — B08 fixed batch admitted and initial F panel running

The actual `wsl_4070` CUDA collector/update/evaluator checks for N and A passed:2 passed,
3 deselected in8.69s, using committed input8725d2f3e924a9d3c0dc8d87c7ff470850854081.
The four reviewed production-file digests on the node match the accepted local files; the
prepared source has no tracked diff. These are short technical fixtures, not B08 fits or
scientific worlds. During preparation, an HTTP helper fetching a missing partial-clone object
stalled in the plain shell. Only that retained Git helper was terminated; Git removed the
uncompleted checkout itself. Preparation in the configured network shell completed at the same
SHA, followed by the actual CUDA tests. No scientific operation existed during that recovery.
Unrelated commit-graph/auto-gc warnings were observed; no repository-wide repair or reset was
attempted, and exact requested source plus admission were independently verified.

The fixed batch has now received actual native admission. The recoverable
[runner-written manifest](../../../../runs/uav_service_auxiliary/b08_an_915031_a01/launch-manifest.json),
[fresh node preflight](../../../../runs/uav_service_auxiliary/b08_an_915031_a01/admission-preflight.json)
and [runner-written configuration](../../../../runs/uav_service_auxiliary/b08_an_915031_a01/config.json)
are copied verbatim here. The manifest is authoritative for the exact source, output, command,
node, controls, native process identities and stable operation handle. Fresh effective memory
was13,808,148,480bytes against the4GiB floor. Runner config confirms the common opt-in, seed,
N8/k10/H3000/two-lane/180k binding, native return coefficient2 and N-then-A intervention mapping.

The first detached observation reports accepted admission, consistent records and both original
native processes running; no exit witness exists. The same task's observation controller is
armed at generation102 against that operation. A subsequent compact progress read shows the
common initial F evaluation underway:4,000 actual evaluation transitions,2 episodes attempted,
1 completed;0 fits and0 training transitions yet. These are operational counts, not accepted
scientific findings. The fixed runner will proceed from this one common initial panel through
N then A, independent of their scores; no extra fit, panel, retry or early scientific judgment
was added. Completion/error/checkpoint wakes return to this task for same-handle reconciliation
and full artifact reading. B07 and the explicit B08 approximation/censoring limits remain intact.

## 2026-09-24 — B08 technical failure during A collection; fixed pair incomplete

The accepted B08 process terminated at2026-09-24T16:17:42.931522Z with exit code-11
(SIGSEGV), recorded by the native supervisor in the
[unchanged exit witness](../../../../runs/uav_service_auxiliary/b08_an_915031_a01/process-exit.json).
The same operation reports both original process identities absent, consistent admission/manifest
records and no explicit retry. The terminal observation was read and consumed at generation114;
no running observation or pending event remains. No worker was restarted, no additional fit or
Pro question was submitted, and no other App task was contacted. Current main still records
the owner pause as lifted; the failure itself is not permission to extend this fixed batch.

**Observed execution and preservation.** The two planned fits started; N completed all30 phases
and180,000 native transitions, with its endpoint saved. The common initial and N endpoint F
panels each completed all40 episodes:80 episodes and240,000 evaluation transitions in total.
A completed23 phases (138,000 fully persisted transitions); its separate
[arm summary](../../../../runs/uav_service_auxiliary/b08_an_915031_a01/A/summary.json)
records140,000 transitions and the last progress event is phase24, step1000 across two lanes.
The [batch summary](../../../../runs/uav_service_auxiliary/b08_an_915031_a01/summary.json)
lags this by200 transitions: it reports A139,800 and total319,800. These source files are copied
verbatim, not reconciled by overwriting runner evidence. The arm/progress evidence therefore
establishes **at least320,000 total training transitions**, not an exact terminal count.
Further execution after the last persisted notification is unknown. A has no phase24 raw tape,
partial tape, final checkpoint, final-prefix record or endpoint evaluation.

The [progress stream](../../../../runs/uav_service_auxiliary/b08_an_915031_a01/progress.jsonl),
[N summary](../../../../runs/uav_service_auxiliary/b08_an_915031_a01/N/summary.json), admission
status and exit witness are preserved with the existing config, manifest and preflight. The
batch and A summaries remain `INCOMPLETE` with `failure: null`; the asynchronous signal bypassed
their ordinary Python exception/finally path. A null exception field does not negate the native
exit witness. The admission-only `launch-status.json` is not the terminal process status.

Read-only artifact checks verified all219 recorded SHA256 references, totaling1,626,056,941bytes,
with no missing file or digest mismatch. All30 N and23 A training NPZ files load with full
3000-by-2 masks: valid execution, diagnostics and stored-transition counts each total180,000
for N and138,000 for A; none is marked partial. This checks preservation and recorded coverage,
not every numerical result or the missing phase24 trajectory. Full raw files and both available
checkpoints remain at the manifest's output root:
`/home/wu/hmasd-worktrees/usa-b08-8725d2f3e/runs/uav_service_auxiliary/b08_an_915031_a01`.
No remote file was removed. Copied batch/A/N summary SHA256s are respectively
`ccf880cca55bdba7881afd53e938fc05a2733cec82e66bd1b4ffc75e5f837e1c`,
`8ab9263f940e5a5d9d98494aadb68786a0c640aa6247555dd542c3fbe7da7fd9` and
`8365f168498f012cf42132627c27ec703b9df924bb021a3ae51480f75991585b`.

**Diagnostic limit and cost.** Stderr is empty; stdout ends after A phase23. Neither the run
source directory nor the standard Linux crash directories contain a usable core. The inspected
kernel segfault line names a different PID and cannot be bound to this process, so it is not
used to identify a cause. No recorded stack or reproduction identifies a faulty component;
the cause remains unresolved. The latest progress places the failure after A phase24 collection
step1000, but does not identify the crashing instruction. No GPU, memory, interpreter, native
environment or learning defect is inferred from the signal alone.

Cost is2 started fits,1 completed training fit and1 technically failed fit on `wsl_4070`, plus
the80 completed evaluation episodes. Admission-to-exit elapsed wall time from the two native
timestamps is17,414.392244s (290.239871min), including evaluation. N's runner-measured training
wall is6,692.306691s (111.538445min), and its process high-water RSS is3,447,460KiB at that
boundary. A and final batch resource telemetry did not execute; their peak RSS and CPU times
are `resources_unmeasured`, not zero. The earlier N process peak is not the missing batch peak.

**Reading and next action.** This is a technical failure and an incomplete fixed comparison.
There is no A endpoint with which to calculate the predeclared A-minus-N or A self-learning
effects, and no full-pair acceptance. Preserved N/initial outputs remain narrower artifacts;
their existence is not acceptance of a replacement one-arm scientific study. The failure does
not strengthen or weaken the feedback-training hypothesis, invalidate B07's bounded physical
observations, or establish a negative learning result. No directly affected shared scientific
background requires revision from this signal.

The fixed attempt is over and the direction remains exploring with **no selected next run**,
pending Pro request or active producer. A future retry would require a concrete diagnostic or
repair reason and a new prospective decision that retains this failed fit and all selection
exposure; it cannot be labeled continuation or recovered from an absent A checkpoint. No new
scientific route closure, confirmation, seed, arm, host or training budget is selected here.

## 2026-09-24 — New direct DM continuation and B09 prospective matched feedback learning

The owner-requested new independent DM task is `01a0d621-fad7-7863-ab0a-89b148926205`
on `local`, authoring `/home/fires/.codex/worktrees/31f5/hmasd-wsl` on
`codex/uav-service-feedback-b09`. This task actually adopts the existing direction; it does
not create a second DM or resume the old task/failed process. The launch-bound lead remains
`Codex DM (independent session)`. Main was fetched at
`40eb5c0e79bf0ff023e9458dc7fc301edbf9afab`; the clean new checkout already contains that revision
and the owner's helper configurations. The complete existing notebook is present on main and
matches published direction tip `da1e68dbd6b6935dd6ba742730b8454b24c9fcde`; no historical text is
replaced. B08 and its costs, missing A endpoint, old N exposure and all B07 adverse worlds remain.

### Scientific reading, decision and cost

I read the full Answer and Root Decision in
[the completed September 24 investment review](../../archive/2026-09-24/RESEARCH-next-investment-after-b18-b09-b08.md),
and the current shared background (especially topic 6), Current research plan and Shared runtime
diagnosis at the main revision above. I adopt its selected new N/A exploration. The opportunity
is B07's observed replenishment under F with remaining service failures; it does not diagnose
an auxiliary prediction/representation bottleneck. B08 provides no A-minus-N endpoint. The
strongest alternative is retaining F without buying training, not adding a third learner.
A complete new pair can resolve whether training inside the deployment feedback has incremental
finite service value. The prior complete advice covers this comparison, completed-segment
contract and investment; routine implementation needs no repeated consultation.

B09 is one fresh initialization block: training seed **925031**, lane seeds **925031/925032**,
N then A, two lanes, 30 phases of 3000 actual steps per lane, native S7-S2/H3000/N8/k10.
Each arm starts from genuinely matched parameters, buffers, normalizers, RNG and evaluation
state. N sends the native proposal to the original adapter; A maps that proposal through the
unchanged B06/B07 F first. All native learners, rewards (return coefficient 2), entropy terms,
information, optimizer schedules and common ordinary completed-segment eligibility remain.
Cross-version high segments remain an explicit mixed-behavior PPO approximation; correct old
likelihoods do not make it strictly on-policy or establish cancellation between arms.

The single fixed primary evaluation panel is **952001 through 952032**, with original native
H3000 endings, one real common initial F evaluation and both fixed endpoint F evaluations.
There is no development panel, interim selection, replacement episode or interaction top-up.
These seeds are new to this direction's recorded source/inputs; implementation will assert the
actual panel order and common initial identity. Planned cost is **2 fits x 180,000 = 360,000
training team transitions**, plus **96 episodes and at most 288,000 evaluation transitions**,
thus at most **648,000 total team transitions**. Checks, engineering, collection/storage and
reading have additional cost; actual wall time is unknown and will be measured. This is n=1
per arm exploration, not confirmation. No old N is paired with a replacement A.

Read every world: cumulative native QoS, planned-window and actual-step service, delivered
volume, J, return cost, minimum/low battery, cutoff/depletion, charging/consumption/storage,
zero service and all adverse signed effects. Prediction: A learns useful full-task service
relative to the actual common initialization and adds service over N under common F deployment.
Report each arm's own learning and A-minus-N. The first qualifying actual-input/positive-net-
stored-gain/F-exit event followed by 250 steps of team service is descriptive intermediate
support only; retain no event, no exit, re-entry and incomplete-window denominators. It is
neither a same-state effect nor same-aircraft recovery. Full service improvement without that
window pattern weakens the recovery account; penalty savings, charging or local-window gains
alone do not fulfill the service prediction. Mixed/adverse outcomes are preserved without
automatic extension, threshold change, another arm or confirmation.

### Technical execution choice and L0

Root's completed, identity-bound B08 core inspection localizes the immediate failure to
`b01.native._write_progress` serializing the whole nested batch summary, reached from B08
collection progress. The CPython instruction/metadata anomaly does not identify a JSON, NumPy,
CUDA or hardware defect. It is different from B18's clip-error cleanup path; common cause
remains unknown. I reuse the supplied bounded core summary instead of repeating a large dump
investigation. No verified root-cause repair is claimed.

The new execution path keeps configured `wsl_4070`, CUDA FP32/TF32 off and four torch threads,
but removes repeated growing whole-summary serialization from collection/step progress. B09
will append compact progress with actual counters and persist complete summaries atomically at
completed episode/phase/panel/fit/error boundaries, using compact `json.dumps` (no indented
Python generator walk) where it owns JSON writing. Existing raw training/high-segment and
evaluation evidence remains required; snapshots are not silently omitted for speed. This is a
bounded reduction of the observed repeated persistence path and torn-summary risk, not proof
that the unknown native crash is cured. Short actual-node collector/update/evaluator and
persistence checks cover the chosen path before a new long fit. A native signal can still lose
in-flight work; the supervisor exit witness and last durable counters remain authoritative.
No automatic retry follows another failure.

First recover only the published direction source dependencies and checks from
`da1e68dbd6b6935dd6ba742730b8454b24c9fcde`: `experiments/candidates/uav_service_auxiliary/`,
its matching tests and runner entries, plus the already reviewed common opt-in code in
`hmasd/agent.py`, `hmasd/utils.py` and `tests/hmasd/test_ordinary_completed_segments.py`.
Current main's two core files exactly match the pre-B08 commit, so this recovery introduces
only the accepted completed-segment patch, with no removal of later shared changes. The old
checks/review are reusable; targeted current integration checks will verify restored imports
and interfaces. Do not import unrelated branch history, old run artifacts or control/config files.

The bounded new implementation owns `experiments/candidates/uav_service_auxiliary/b09/`,
`scripts/run_uav_service_auxiliary_b09.py`, and corresponding `tests/experiments/candidates/`
`uav_service_auxiliary/b09/` only. Reuse unchanged B08 identity/endpoint/metrics and B07 evaluator
helpers; create successor-specific spec/batch/persistence and, if needed, a local collector copy
with only persistence changes. Preserve B01-B08, common learner/env, F and all historical contracts.
The admission guard must precede scientific effects. Check fixed exposure/panel/seed and actual
initial equality, score-independent N-then-A execution, reuse refusal and partial failure,
compact progress versus completed-boundary persistence, atomic readable summary replacement,
actual proposal/storage/reward/update/F/reset/censor semantics, raw artifacts, evaluation RNG
isolation, and early-ending counts. Compare the old/new short collector's substantive outputs
where practicable; no claim of historical long-run bitwise equivalence. Engineering fixtures
are not result-bearing fits or scientific pilots, and pytest owns all scratch. Independent
Reviewer inspects this high-risk runner/persistence diff. DM owns NOTES, acceptance, publication
and launch; helpers own no index or scientific decision. Stop only a dependent action if a
material contract conflict emerges; do not substitute a new learning algorithm.

### B09 persistence refinement and preparation checks

The preserved B08 batch summary is 6,549,333 bytes (3,829,104 bytes with compact JSON); the
A arm summary is 1,661,785 bytes. These are file-structure measurements only, not new outcome
readings. Much of the nested detail is completed-world/episode recovery intervals, repeatedly
walked during later collection. In B09 keep compact scalar world/episode readings, the selected
anchor and all denominators in the main summary; retain full interval-level detail in hashed
raw gzip JSON at its completion boundary. Preserve the original NPZ/high-segment evidence.
This is a storage/persistence refinement within the L0, with no change in metric definitions,
selection, exposure or planned readings. Full detail remains recoverable, not dropped to claim
speed. The native launch waiter uses process identity, native exit witness and artifact presence;
it does not require a whole-summary rewrite at each hundred-step notification.

The restored opt-in core, B08 opportunity metrics and evaluation/configuration interface checks
passed locally: 22 passed in 6.42 s using the configured scientific interpreter. The two core
files matched the old patch's parent exactly before recovery; old reviewed implementations
were imported byte-for-byte. The configured result node was read-only checked: the named
Python/NumPy/Torch stack and CUDA are available. This is not launch admission or a diagnosis of
the old crash; actual-source CUDA checks, independent review and fresh memory admission remain.
The new-task routing/prospective note was published to main at `68b9d762d67db1db0714882b02d3685437ac6b6a`;
concurrent DM1 publication was merged without changing its records. Scientific preparation has
started no B09 fit and made no new Pro request.

### B09 implementation handback and residual before actual-node checks

The Implementer returned the B09-only diff and checks without changing scientific scope,
historical candidate/core code, the index or notebook. The successor collector differs from
B08 only in persistence/imports/messages: actual environment, proposal/likelihood storage,
learner update and completed-segment flow are retained. Local focused suite: 12 passed,
2 CUDA cases skipped in 11.20 s; after extending the old/new equivalence assertion to all four
native module state dictionaries, that single check passed in 3.91 s. It also compares actual
raw NPZ arrays, training counts, episode scalars, opportunity totals, optimizer counts and
parameter displacement. This is a short fixed CPU fixture, not long-run equivalence or proof
against native crashes. Independent review and actual-source CUDA checks are in progress.

Full completed panel/episode opportunity detail, including omitted interval lists and window
zero-service intervals, is retained in hashed raw gzip JSON; the main summary keeps anchors,
denominators and scalar readings. The inherited B07 evaluator supplies full panel arrays only
at panel completion. Consequently `evaluation_world` persists completed-episode counters but
not that world's complete required measurements. A fatal signal inside a panel can still lose
its in-memory world measurements; a Python exception follows the inherited partial-NPZ path.
The current evaluation panel is not counted as a complete scientific result from counters alone.
No broader evaluator rewrite is selected merely to eliminate every possible loss. Training
phase raw NPZ/high records are saved at their existing boundaries; signal-time in-flight loss
remains possible. These residuals are accepted for a new bounded attempt, not described as fixed.

### B09 engineering acceptance and actual-node execution decision

Independent Reviewer ran the original focused suite (12 passed, 2 CUDA skips, 11.03 s) and
found one concrete persistence gap: three B07 world-detail lists still entered the compact
summary. The repair at `3c8e4a1c4292f57eb01586a4f65b727c54d17812` saves the complete raw panel
first, then omits service-free intervals, per-UAV mode durations and descriptive 250-step bins
from summary worlds. All scalar counts, half-window summaries, opportunity anchors and
denominators stay. The real-shaped fixture verifies raw retention and compact omission;
3 focused checks passed in 5.24 s. The Reviewer reread this patch and returned no remaining
material finding. DM accepts this narrow implementation, with the documented signal-time
loss and unknown crash cause unchanged.

On the configured actual `wsl_4070` stack, the full B09 focused suite at that published source
passed **14 tests in 12.74 s**, including both CUDA N/A collector/update/evaluator cases with
four torch threads and TF32 disabled. No CUDA case was skipped. This covers real native
proposal/storage/reward flow, F activation, native endings, cross-phase execution state,
learner movement, final-prefix censoring and evaluation isolation, together with persistence
and fixed-batch fixtures. No performance score or positive pilot was used to authorize the
comparison. The test source was clean; no interpreter or numerical library was installed or
upgraded. These short checks do not guarantee a multi-hour run cannot crash.

Accepted executable SHA256s: B09 native `4de8e49e9123898c23d1e0efe09efc3e5a4bc5b5e8209cd119a031d904cc7be3`,
persistence `ea1b0b0596887a776266dc162228de4a3d63b9df6f68dab8719ff99f07350586`,
collector `1272932ddac374e031a67fb7603a95e69d32462a539cc887e633bba21af4c13b`,
entry `8b43dfbb801f6a003ddb6d6bf5ac32b2cb455e9abc5cc5dcabfdcc4e29037bdd`.
The node's pre-existing commit-graph/automatic-GC warnings occurred during successful Git
preparation; exact requested checkout, tracked-byte checks and the actual tests succeeded.
No repository-wide repair, reset or cleanup of others' work was attempted. Preparation/tests
started zero result-bearing fits. Proceed with the fixed new pair after this accepted input is
published and fresh kernel memory/control admission; no further Pro/Root/owner approval is
needed for the already adopted comparison.

## 2026-09-24 — B09 fixed new pair admitted; common initial F evaluation underway

The new fixed batch received actual kernel admission from published input
`e5e53534c2c0c4a059cfdfa5f3aff4cbc2166f46`. The unchanged
[launch manifest](../../../../runs/uav_service_auxiliary/b09_an_925031_a01/launch-manifest.json),
[fresh preflight](../../../../runs/uav_service_auxiliary/b09_an_925031_a01/admission-preflight.json),
[admission status](../../../../runs/uav_service_auxiliary/b09_an_925031_a01/launch-status.json) and
[runner configuration](../../../../runs/uav_service_auxiliary/b09_an_925031_a01/config.json)
are copied here. The manifest owns command, executing source/output paths, native identities,
node, source and stable operation reference. The actual node had 14,939,668,480 effective
available bytes against the 4 GiB floor. Config readback confirms seed 925031, two lanes,
30 phases/H3000, 32 primary worlds, no development panel and the same F/action-path contract.
All four reviewed B09 executable digests on the node match the accepted files.

The assigning task's own observer is armed at generation 1. Its first probe reports accepted
admission, consistent records, both native process identities running, and no exit witness.
The first arm registration was refused before creating a job because the request used a
nonabsolute `ssh` executable; replacing only that probe argv with `/usr/bin/ssh` registered
observation of the same accepted operation. No scientific Send/launch was repeated, no old
observer state adopted, and no `--resume-jobs` was used. Private request/state stay task-local.

A compact progress read shows the real common-initial F panel in progress: 5,700 evaluation
transitions, 2 episodes attempted and 1 completed; zero training fits/transitions started at
that observation. The fixed N-then-A sequence follows this panel independently of scores.
These are execution facts, not an A-minus-N finding. Same-handle checkpoints/terminal notices
return to this task for collection, complete reading and its own result publication. B08's
failed attempt and cost remain separate. No automatic repeat or extension is selected.

### B09 first observation checkpoint — 2026-09-24

Generation 1 returned only a CHECKPOINT, with the same accepted operation and both original
native process identities running, consistent records, zero probe errors and no exit witness.
The compact progress read reached 77,000 initial-primary evaluation transitions: 25/32 worlds
completed, the 26th attempted; zero training fits/transitions yet. The last boundary summary
records 75,000 transitions/25 worlds, with no completed panel, no failure and empty stderr.
This is expected boundary-versus-journal cadence, not a rewritten count discrepancy. No result
is accepted before the full required panel artifacts are available. Continue the fixed batch
and rearm the same handle; no new launch, fit, panel, Pro request or shared-index change.

### B09 common initial panel complete; N learning underway — 2026-09-24

Generation 2 returned a CHECKPOINT on the same running native identities, with consistent
records and no observation errors or exit witness. The initial F panel completed all 32 fixed
worlds 952001–952032 and 96,000 actual evaluation transitions, with zero new optimizer updates
and the recorded full-state immutability check. All four root artifact references (config,
common initial checkpoint, full raw panel JSON and NPZ) match their recorded SHA256s on node;
no artifact was removed or promoted into a complete paired result.

N has started and collected 42,000/180,000 transitions. At the read boundary six updates were
complete and phase 7 collection had finished; all five learner groups moved in the sixth
update. This distinction prevents counting a collected phase as an already finished update.
The original initial-plus-N-then-A batch continues, stderr is empty, and A has not started.
No endpoint contrast is available. Rearm the same operation; no scientific scope or index change.

### B09 third observation checkpoint — 2026-09-24

Generation 3 returned only CHECKPOINT `2ac9e4e65b0f34e262b0977d`: both original native
identities remain running, records are consistent, observation errors are zero and no exit
witness exists. The boundary summary records N at 96,000 transitions, 16 completed updates
and 32 native episodes; the subsequent journal read reaches 97,800 transitions during phase
17 collection. The 16th update moved all five learner groups. Initial evaluation remains
32/32 worlds and 96,000 transitions; neither endpoint evaluation nor A has started. Stderr
is empty and the batch summary remains INCOMPLETE without a recorded failure.

Fresh main controls still record owner pause lifted and this task as the same direction lead.
The newer constitution clarification of question continuity and the three-track resource
ceiling changes neither this accepted pair nor its frozen inputs. Continue observation of
the same operation and rearm with the returned generation/wake/event; no new execution or
scientific conclusion is selected from this checkpoint.

### B09 fourth observation checkpoint — 2026-09-24

Generation 4 returned only CHECKPOINT `4790e5d9b9b99d5eebb3d346`, with consistent original
native identities running, zero probe errors and no exit witness. N's completed boundary is
150,000 transitions / 25 updates / 50 native episodes; the later journal read reaches
153,200 transitions during phase 26 collection. All five learner groups moved in update 25.
Initial evaluation remains the sole completed panel (32 worlds, 96,000 transitions); neither
endpoint evaluation nor A has started. The summary is INCOMPLETE without a recorded failure,
stderr is empty, and fresh main retains the same lead and lifted owner pause. Rearm the same
accepted operation; this checkpoint supplies no endpoint comparison or change in scope.

### B09 N fit complete; endpoint panel underway — 2026-09-24

Generation 5 returned only CHECKPOINT `9287472100b050314382ffe6`, with both original native
identities running, consistent records, zero probe errors and no exit witness. The runner
reports N training COMPLETE at exactly 180,000 transitions / 30 updates / 60 native episodes;
all five learner groups moved in update 30. This is a training completion record, not final
paired scientific acceptance. The N endpoint panel has completed 10/32 worlds and attempted
the 11th; the journal records 30,500 N evaluation transitions (126,500 including the 96,000
common initial transitions). Only initial_primary is a completed panel in the summary.

A has not started; the batch remains INCOMPLETE without a recorded failure and stderr is
empty. Fresh main keeps the same lead and lifted owner pause; its project-plan wording does
not change this accepted comparison. Continue the fixed N endpoint-then-A sequence and
rearm the same operation. Full panel artifacts and the A endpoint remain required for reading
the declared contrast; this checkpoint does not select or extend a run.

### B09 N endpoint panel complete; matched A started — 2026-09-24

Generation 6 returned only CHECKPOINT `9b3688ab7d8e3d3477827b23`, with original native
identities running, consistent records, zero probe errors and no exit witness. N's endpoint
panel now contains all 32 fixed worlds and 96,000 actual transitions; together with the initial
panel, 64 episodes / 192,000 evaluation transitions are complete. The N panel reports zero
new optimizer updates and full-state immutability. Its endpoint checkpoint, full raw JSON and
NPZ each match the registered SHA256 on the node (three new artifact references checked).

A has started with its recorded initialization equal to N/common initial; both per-arm equality
flags are true and the complete identity records match. The journal read reaches A phase 1,
200 collection steps per lane (400 transitions), with no completed A update yet. The batch
remains INCOMPLETE, stderr is empty and no paired result is available. Fresh main retains the
same lead and lifted pause. Preserve the completed N evidence and continue only the already
fixed A fit/panel; rearm the same operation without altering the comparison.

### B09 seventh observation checkpoint — 2026-09-24

Generation 7 returned only CHECKPOINT `2e0d085118e06f336d781c7e`, with both original native
identities running, consistent records, zero probe errors and no exit witness. A has collected
48,000/180,000 transitions: phase 8 collection is complete while seven updates are recorded;
all five learner groups moved in update 7. N remains complete and the two completed evaluation
panels total 64 worlds / 192,000 transitions. A has no endpoint yet. The batch is INCOMPLETE
without a recorded failure and stderr is empty. Fresh main retains the same lead and lifted
pause. Rearm the same accepted operation; there is no change to the fixed comparison.

### B09 eighth observation checkpoint — 2026-09-24

Generation 8 returned only CHECKPOINT `c1970404404e0aea8733a816`: original native identities
running, consistent records, zero probe errors and no exit witness. A's boundary summary is
90,000 transitions / 15 completed updates / 30 native episodes; the journal reaches 90,400
transitions during phase 16 collection. All five learner groups moved in update 15. N and the
initial/N panels remain complete; A has no endpoint. The batch is INCOMPLETE with no recorded
failure and empty stderr. Fresh main retains the same lead and lifted pause. Rearm the same
operation with the comparison unchanged.

### B09 ninth observation checkpoint — 2026-09-24

Generation 9 returned only CHECKPOINT `9b2962f1d11c25b5ccb0d4fe`, with original native
identities running, consistent records, zero probe errors and no exit witness. A has collected
132,000/180,000 transitions: phase 22 collection is complete while 21 updates are recorded.
All five learner groups moved in update 21. N and the initial/N panels remain complete, while
A has no endpoint. The batch remains INCOMPLETE without a recorded failure, stderr is empty,
and fresh main retains the same lead and lifted pause. Rearm the same accepted operation;
the declared comparison and reading remain unchanged.

### B09 tenth observation checkpoint — 2026-09-24

Generation 10 returned only CHECKPOINT `03d91bd4a38c5d1fd628865a`, with original native
identities running, consistent records, zero probe errors and no exit witness. A's completed
boundary is 174,000 transitions / 29 updates / 58 native episodes; the journal reaches
177,200 transitions during phase 30 collection. All five learner groups moved in update 29.
The initial and N panels remain the only completed evaluations (64 worlds / 192,000 steps).
The batch is INCOMPLETE without a recorded failure, stderr is empty, and fresh main retains
the same lead and lifted pause. Rearm the same operation; A's fit completion and fixed endpoint
panel are still pending, so no paired conclusion is available.

### B09 both fits complete; A endpoint panel underway — 2026-09-24

Generation 11 returned only CHECKPOINT `f02e8c2ad4ac6d3d2b4e583c`, with original native
identities running, consistent records, zero probe errors and no exit witness. The runner
reports both N and A training COMPLETE, each exactly 180,000 transitions / 30 updates /
60 native episodes, totaling two completed fits and 360,000 training transitions. All five
learner groups moved in A's final update. Training completion alone does not accept the pair.

A's fixed endpoint panel has completed 20/32 worlds and attempted the 21st; its journal read
reaches 62,400 transitions (254,400 across all evaluation panels). Only initial_primary and
N_primary are complete panels in the summary. The batch remains INCOMPLETE without a recorded
failure, stderr is empty, and fresh main retains the same lead and lifted pause. Rearm the
same operation for the remaining fixed evaluation and final collection; no extension is selected.

### B09 bounded post-result trace inspection scope — 2026-09-24

The complete fixed pair has returned. Before choosing renewed investment, inspect the already
saved 96 evaluation trajectories for the current shared-plan B2 station-continuity question:
count a loss of charging after a charged tick while the member remains eligible at the same
station, plus all eligible waiting exposure and continuous charging spell lengths/censoring.
Read every world and the existing first/second-half service summaries. This is post-result
existing-data diagnosis, not a new prospective result, a causal explanation of A-minus-N,
or permission for a queue intervention. It has zero new fits/environment steps and bounded
NPZ/source-reading cost. Its purpose is to decide whether a concrete station rule remains a
worthwhile next comparison; no source or frozen B09 measurement is altered.

## 2026-09-24 — B09 complete: both arms learn service, feedback training adds no mean endpoint gain

### Execution, collection and acceptance

The fixed new pair completed at input `e5e53534c2c0c4a059cfdfa5f3aff4cbc2166f46` on
`wsl_4070`, seed 925031. Native exit is 0 at 2026-09-25 06:32:18.666692 UTC, with matching
recorded identities and no stderr. I accept the **complete exploratory comparison** after
reading the outputs and verifying the evidence, not from exit status alone. The
[summary](../../../../runs/uav_service_auxiliary/b09_an_925031_a01/summary.json),
[configuration](../../../../runs/uav_service_auxiliary/b09_an_925031_a01/config.json),
[manifest](../../../../runs/uav_service_auxiliary/b09_an_925031_a01/launch-manifest.json),
[terminal status](../../../../runs/uav_service_auxiliary/b09_an_925031_a01/launch-status.json)
and [exit witness](../../../../runs/uav_service_auxiliary/b09_an_925031_a01/process-exit.json)
retain the accepted source and operation identity.

Both arms have exactly 180,000 actual team transitions, 30 completed updates, 60 native
episodes and 1,440,000 action rows. Each consumed 18,000 complete high records; none remained
pending, unconsumed or finally censored. Cross-version completion was zero in these actual
trajectories; the common implementation's general mixed-behavior limitation is unchanged.
Both initial identity records equal the real common initialization. Each fit made 2,250 high,
67,500 low actor, 67,500 low critic, 450 team discriminator and 1,800 individual discriminator
optimizer steps; every phase moved all five learner groups. All 60 training NPZs reconcile
360,000 actual transitions and per-lane native J with their phase summaries; none is partial.
All three evaluation panels contain exactly seeds 952001–952032, 32 native H3000 truncations,
96,000 steps each, zero new fits/updates and unchanged full learner/normalizer state. The raw
96-world NPZs reproduce recorded cumulative QoS/J, consumption/input/stored-energy and the
selected 250-step service windows. Total exposure is **2 started / 2 completed fits,
360,000 training + 288,000 evaluation = 648,000 team transitions**, without top-up or selection.

All **382 files / 1,926,640,753 bytes** were copied from the manifest's node output root to
`/home/fires/hmasd-artifacts/uav_service_auxiliary/b09_an_925031_a01`, outside this worktree.
Every file's SHA256 and size agree between source and collection. The **370 registered artifact
references / 1,923,375,867 bytes** also match their existing root/arm metadata, including all
checkpoints, raw gzip details, NPZs and high-state snapshots. Full files remain at both locations;
only compact source/config/summary/native status are versioned here. The runner summary is
1,215,991 bytes, SHA256 `a96db3a1e945af8099e54ad2a22173ff050df134bb95918818357f16502458cf`.
The 1,277,033-byte progress journal and logs remain in those verified complete copies.

Measured runner wall is 17,441.906742 s (290.698446 min); fit bodies are N 5,022.150777 s
(83.702513 min) and A 6,092.920086 s (101.548668 min). Admission-to-exit wall is
17,870.138655 s (297.835644 min). Runner user/system CPU is 17,108.175704 / 774.306820 s;
peak RSS is 3,488,380 KiB for this runner process high-water mark, not whole-node memory.
These are measurements under concurrent node use, not a causal speed comparison. Preparation,
checks, publication and reading are additional work. B08's failed two-started/one-completed
attempt and at least 320k training / 240k evaluation cost remain separate; no old N was reused.
This successful execution does not establish that the unknown B08 SIGSEGV cause was repaired.
The terminal observer event was consumed on the same handle; no result worker was restarted.

### Native endpoint reading

All policies in the following table deploy the unchanged F. QoS per actual step equals
planned-window QoS because all worlds ran 3000 steps. J and cumulative QoS are per-world
sums; return cost is the per-world sum of the native cost term, before its reward coefficient 2.
This is one independent training initialization per arm; the 32 worlds do not increase training n.

| Reading | Common initial | N endpoint | A endpoint |
| --- | ---: | ---: | ---: |
| Native J | 609.522260919 | 986.436461366 | 904.269870649 |
| Cumulative QoS | 642.397611880 | 1016.228609224 | 934.664387959 |
| QoS / planned step | 0.214132537 | 0.338742870 | 0.311554796 |
| Delivered megabits | 19271.928356388 | 30486.858276725 | 28039.931638772 |
| Minimum battery, mean across worlds | 0.098619260 | 0.108617649 | 0.106018764 |
| Minimum battery, world P10 | 0.092561647 | 0.101310513 | 0.100450564 |
| Minimum battery, worst world | 0.089335503 | 0.100904998 | 0.093677673 |
| Consumed Wh | 1180.086051713 | 1113.432139283 | 1144.108479887 |
| Charger input Wh | 193.776041667 | 158.237847222 | 185.312500000 |
| Signed stored-energy change Wh | -986.310010047 | -955.194292060 | -958.795979887 |
| Return cost sum | 3.344579281 | 0.832824334 | 1.147486809 |
| Zero-service / negative-J worlds | 4 / 4 | 1 / 1 | 2 / 2 |
| Cutoff / depletion events | 0 / 0 | 0 / 0 | 0 / 0 |

Both arms show useful **finite own learning** on these worlds: N−initial mean J +376.914200447,
QoS/step +.124610332; A−initial +294.747609731 and +.097422259. N has 25 favorable and seven
adverse J worlds, with service 25 favorable / six adverse / one tied; A has 25 favorable /
seven adverse J worlds and service 24 / seven / one. Their worst own J differences are
−106.979245725 and −705.300524119. Own learning does not imply an A training advantage.

The predeclared incremental service prediction fails here: **A−N mean J −82.166590716,
cumulative QoS −81.564221265, QoS/step −.027188074, delivered volume −2446.926637953 Mb**.
J has 16 favorable and 16 adverse worlds; service has 16 favorable / 15 adverse / one tied.
The J median is nevertheless +10.787658751 and service median +.003939476 per step. Preserve
both signs: a favorable median/half the worlds does not erase the negative mean, while one
negative mean does not establish general harm or equivalence. The worst world is 952016:
A has zero service, N QoS .323065444, J difference −970.330951537. The largest positive J
difference is +454.004581453 on 952009. A's additional zero-service world is 952016; 952014
is zero service for both. Initial zero-service worlds are 952014/17/21/23; A and N both
recover service on 17/21/23 under their own trajectories.

A's mean return cost is .314662475 higher, despite a median decrease of .018488422 and
17/32 cost-favorable worlds; 952007 contributes +8.590514712 cost while still improving service.
A's mean minimum battery is .002598885 lower (18 worlds lower, 14 higher), worst A battery
.093677673 versus N .100904998. All three panels have zero cutoff/depletion, including the
initial policy, so this comparison establishes no incremental prevention of those events.
A consumes 30.676340605 Wh more and takes 27.074652778 Wh more charger input per world,
leaving signed stored-energy change 3.601687827 Wh more negative. All panels have real charging
and positive per-step storage in every world, yet their total stored energy declines.
No safety invariant, indefinite operation or same-UAV service restoration follows.

### All fixed worlds

Columns show full J, QoS/step, and the signed A−N return-cost sum. All other per-world energy,
minimum battery, opportunity, half-window and censor fields remain in the linked summary/raws.

| World | Initial J | N J | A J | Initial QoS | N QoS | A QoS | A−N J | A−N cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 952001 | 921.376223964 | 862.701430320 | 711.017863648 | 0.316405537 | 0.298512455 | 0.247875296 | -151.683566672 | -0.052873576 |
| 952002 | 948.302040941 | 1255.708904364 | 1295.562059789 | 0.325018666 | 0.428782673 | 0.441911508 | 39.853155425 | -0.181376850 |
| 952003 | 924.646912109 | 1204.785707656 | 1131.376425046 | 0.317485039 | 0.410993636 | 0.387207965 | -73.409282610 | -0.093763834 |
| 952004 | 440.153882583 | 658.181633755 | 401.147730127 | 0.165108422 | 0.229240936 | 0.142804383 | -257.033903628 | 0.220018262 |
| 952005 | 441.203504037 | 1372.606343033 | 1228.415781454 | 0.160450664 | 0.467739751 | 0.420164023 | -144.190561579 | 0.274664333 |
| 952006 | 872.368412407 | 912.128795187 | 857.821655500 | 0.302323238 | 0.312702195 | 0.294699055 | -54.307139687 | 0.159049974 |
| 952007 | 728.537533505 | 834.059026890 | 1131.469222502 | 0.263873098 | 0.286567226 | 0.391737015 | 297.410195612 | 8.590514712 |
| 952008 | 814.716594819 | 1424.122615724 | 1560.301865587 | 0.281349872 | 0.485936187 | 0.530774766 | 136.179249862 | -0.715485338 |
| 952009 | 547.029125889 | 548.075865273 | 1002.080446726 | 0.190979979 | 0.193258230 | 0.344677761 | 454.004581453 | -0.029120082 |
| 952010 | 703.419801556 | 814.858816351 | 710.988651500 | 0.245183429 | 0.282296045 | 0.247872987 | -103.870164850 | 0.322268109 |
| 952011 | 1090.121201823 | 1197.633523704 | 1265.864378066 | 0.372629655 | 0.409709948 | 0.432769378 | 68.230854362 | 0.517911152 |
| 952012 | 467.650430830 | 1357.199756963 | 1251.174646150 | 0.163895357 | 0.462984865 | 0.427840003 | -106.025110812 | 0.428385275 |
| 952013 | 498.589479476 | 1503.187608162 | 949.996636729 | 0.174834012 | 0.511704388 | 0.327110044 | -553.190971433 | -0.099890454 |
| 952014 | -30.493015458 | -32.650748632 | -32.810844093 | 0.000000000 | 0.000000000 | 0.000000000 | -0.160095461 | 0.126660221 |
| 952015 | 747.169592192 | 724.797829238 | 755.568474939 | 0.265829862 | 0.250842656 | 0.261272849 | 30.770645702 | -0.187822425 |
| 952016 | 672.674298366 | 937.704725784 | -32.626225753 | 0.233979121 | 0.323065444 | 0.000000000 | -970.330951537 | 0.472567286 |
| 952017 | -69.113460094 | 759.234203182 | 1180.331314875 | 0.000000000 | 0.263300977 | 0.403940470 | 421.097111693 | 0.141612364 |
| 952018 | 357.480263721 | 634.158956816 | 669.927753901 | 0.130490176 | 0.219956263 | 0.231806389 | 35.768797084 | -0.212650450 |
| 952019 | 733.036167862 | 903.319273439 | 1010.299661339 | 0.254403774 | 0.310566714 | 0.346599717 | 106.980387900 | 0.013450539 |
| 952020 | 609.479165443 | 737.565727190 | 898.877845628 | 0.211409525 | 0.254069722 | 0.308187510 | 161.312118438 | -0.024368923 |
| 952021 | -38.330032041 | 1640.580187551 | 770.194978928 | 0.000000000 | 0.557599819 | 0.267542682 | -870.385208623 | -0.065559446 |
| 952022 | 363.714958342 | 1494.584592279 | 799.008993139 | 0.128562098 | 0.508543639 | 0.276078886 | -695.575599139 | -0.012607922 |
| 952023 | -30.134270331 | 866.057971018 | 773.038043734 | 0.000000000 | 0.298606475 | 0.267847288 | -93.019927284 | -0.034085517 |
| 952024 | 604.037741180 | 715.711177756 | 1109.175703365 | 0.210205671 | 0.249099032 | 0.379943811 | 393.464525609 | -0.429820609 |
| 952025 | 857.938765044 | 1490.277241464 | 1512.012654427 | 0.294906527 | 0.507519373 | 0.515398325 | 21.735412963 | 1.013654172 |
| 952026 | 627.204697818 | 566.349083150 | 897.899544798 | 0.218168771 | 0.197551272 | 0.308550171 | 331.550461648 | -0.207986017 |
| 952027 | 870.856441019 | 1540.038069952 | 974.336226116 | 0.299429655 | 0.523703451 | 0.334593224 | -565.701843836 | 0.242814474 |
| 952028 | 1090.352231811 | 995.457842129 | 1115.330097586 | 0.372264456 | 0.341558551 | 0.381404047 | 119.872255457 | -0.304527192 |
| 952029 | 479.933303711 | 1174.547119672 | 573.364248437 | 0.167744054 | 0.401436622 | 0.199504431 | -601.182871236 | -0.347493785 |
| 952030 | 678.733672935 | 577.249731236 | 638.870737087 | 0.235625918 | 0.201469367 | 0.221957420 | 61.621005851 | 0.076470204 |
| 952031 | 901.519017189 | 1322.175332067 | 1211.326352526 | 0.309597579 | 0.450981026 | 0.414416125 | -110.848979541 | 0.659102490 |
| 952032 | 680.537666756 | 573.558421031 | 615.292936978 | 0.240087038 | 0.199472894 | 0.213265943 | 41.734515947 | -0.190511953 |

### Intermediate prediction and censoring

Initial/N/A all have a qualifying first actual-input/positive-net-storage/F-exit anchor in
32/32 worlds, and all selected windows have the full 250 steps; no missing selected event or
short selected window is silently discarded. Mean window cumulative team QoS is
82.960640149 / 110.222368002 / 110.295557785. Thus A−N is only +.073189783 in this descriptive
window; positive-service ticks total 7000 / 7216 / 7500 out of 8000. Positive-window worlds
are 28 / 29 / 30. Every selected window has a feedback re-entry; these are not uninterrupted
recovery intervals. The two zero-service A windows are 952014/16, while N also has a zero
window on 952009 despite later full-episode service. On 952021, A's selected-window QoS
190.298716924 exceeds N's 186.467373559, yet full QoS/step is .267542682 versus .557599819.
This directly limits using a favorable local window as a substitute for full service.

Initial/N/A feedback activation intervals are 1777 / 2710 / 2772; input intervals
467 / 624 / 638, qualifying positive-gain exits 215 / 408 / 413, input intervals without a
qualifying exit 252 / 216 / 225, and right-censored feedback intervals 253 / 231 / 238.
Completed input intervals without positive gain are zero. Counts refer to different native
interval populations, not independent samples or per-member causal service attribution.
A's training really activates F: 341,431/1,440,000 proposal rows are mapped, all 60 training
episodes have qualifying anchors, and 592 positive-gain exits occur. The other 1,098,569
proposal rows pass through. No F mapping occurs in N training. Nonactivation is therefore
not an explanation of this finite A−N outcome.

The existing half-window reading is also adverse for A: first-half cumulative QoS means
N/A 374.452624363 / 312.191779644; second-half 641.775984862 / 622.472608315. The first half
already includes some F use, so this does not identify a pure pre-feedback causal effect.
Post-charge local opportunity and complete service consequences remain separate judgments.

### Post-result station-continuity inspection and next judgment

The bounded read declared above finds losses of charging while still eligible at the same
station in every world: initial/N/A totals **17,361 / 12,093 / 15,319**. Their continuous
charging spells number 17,608 / 12,536 / 15,771, of which 17,259 / 12,024 / 15,251 last one
tick. Median and P90 spell length are both one tick; maxima are 35 / 35 / 36. Spells active
at the observation horizon are 32 / 35 / 38 and are right-censored. Eligible waiting exposure
is 92,685 / 52,814 / 67,090 UAV-ticks; waiting-age median/P95/max is 4/16/121, 3/11/78,
and 3/12/98. Minimum post-battery while waiting is .089335503 / .100904998 / .093677673.
These are post-result trace facts, not added training n or a causal explanation of A's loss.
They describe a concrete action of the existing lowest-battery-first station rule. Source
inspection confirms that current charging is cleared before selection and the old rule ranks
eligible arrivals each tick by battery, wait age and member id. A successor must preserve the
previous-tick actual charging snapshot if it tests persistence; power/capacity/eligibility/F
and the selected policy must otherwise match.

**Working update and decision:** the service-learning opportunity itself is active: both arms
learn useful service under F deployment. The stronger claim that matching training to F is
sufficient to add mean full-task service over ordinary N is weakened by this complete pair;
local window support and more charging do not rescue it. Retain N+F as the stronger ordinary
reference in this finite reading, while preserving A's favorable worlds and the n=1 limit.
Reuse the complete prior Pro advice's no-additional-use branch to end investment in this
unchanged B09 recipe: no top-up, replacement seed, threshold tuning, additional arm or
confirmation is selected. This does not close the energy-constrained service question.

The current published shared plan's B2 candidate has a concrete observable intervention site,
but its value remains untested: retaining still-eligible charging members may reduce switching
while making lower-battery waiters worse, or alter energy without restoring wireless service.
I will obtain focused Pro criticism of that next investment using this new evidence and the
strong alternative of retaining N+F without further execution. Proposed scope to assess is
one role-fixed ordinary N checkpoint, original versus incumbent-retaining station allocation,
32 new fixed H3000 worlds, 0 new fits / 192k evaluation steps plus implementation/review and
full physical/service evidence. This is a new scientific comparison, not repair of B09 or
proof that queues caused its outcome. No successor result run has been selected or launched.

## Pro question 2026-09-24 b09-result-and-station-continuity

Conversation: reuse the direction's current Jev adviser conversation; its private address
stays only in local operation metadata. This is a new scientific question after a complete
new result, not a resend of any prior accepted question.

Question: Given the complete B09 result and the bounded post-result station trace reading
above, is the existing shared-plan B2 station-continuity comparison now worth executing, or
should this DM retain ordinary N+F and choose a different next observation/no further execution?
Criticize my tentative choice of the narrow B2 comparison, including its strongest competing
explanation, actual estimand and adverse branch. I own the energy-constrained service question,
not a duty to rescue the unchanged feedback-training recipe.

Standing: The previous complete investment advice already covered ending the unchanged
training recipe if both arms learn without an additional A use; I apply that branch to B09.
This question concerns the next investment under materially new evidence. B09 is one fresh
matched initialization, N then A, each 180k native H3000/N8/k10 steps; all three 32-world panels
deploy identical F. Counts, real updates, state immutability and all 382 files/370 registered
artifact references are verified. Both arms improve mean J/service versus the actual common
initial policy. A−N mean J is −82.166590716 and QoS/step −.027188074, with 16/32 J wins and
positive J/service medians. Worst A−N J is −970.330951537 and A adds a zero-service world.
All cutoff/depletion counts are zero, including the initialization; A consumes more energy,
charges more and has slightly lower minimum battery than N. The first qualifying exit's
250-step mean team-service difference is only +.073189783 cumulative QoS; it does not rescue
the complete service prediction. This is n=1 exploration, not general harm or equivalence.
The complete reading, every signed world, censoring and source identities are in the entry above.

The new bounded NPZ reading finds same-station loss of actual charging while still eligible:
12,093 N events across all 32 worlds, versus 15,319 for A. N has 12,536 charging spells,
12,024 only one tick long; 35 spells remain active at the horizon. N eligible waiting exposure
is 52,814 UAV-ticks; waiting-age median/P95/max 3/11/78 and worst waiting battery .100904998.
These data identify a modifiable allocation behavior, not its responsibility for lost service.
The current source clears `uav_charging` before selection and sorts eligible candidates each
tick by battery, descending wait age, then member id. The prospective incumbent rule needs
the preceding tick's actual charging snapshot. The full result also retains B07's benefits
and service-loss counterexamples and B08's incomplete technical failure/cost.

Tentative comparator to assess: freeze the **ordinary N925031 endpoint** by its role as the
primary no-feedback-trained baseline, not by a new score search. Deploy the same unchanged F
under (O) original tickwise station allocation and (C) still-eligible incumbents retain their
station slots; empty slots use the unchanged original ordering. Keep eligibility definition,
station-local information, capacity, power, nearest-station rule, reward and all policy weights
fixed. Each rule executes its own full closed-loop trajectory; actual eligibility sets can
then differ. No new actor mode input, loss mask, learning head, remote-station intention,
reservation or power/threshold change. Use one predeclared set of 32 fresh H3000 worlds with
paired initial worlds and fixed evaluation semantics, and read all outcomes. This changes a
station resource-allocation rule; it is not an actor ablation in an unchanged environment.

Prospective cost if selected: 0 new fits, 2 rules × 32 worlds × 3000 = at most 192k actual
team evaluation transitions (1.536M UAV action rows), no nested planner/search, plus a bounded
station implementation, independent high-risk review, complete traces, storage and reading.
New wall time is unmeasured; B09's complete three-panel/two-fit runner wall was 290.698446 min,
with N/A fit bodies 83.702513/101.548668 min. The strongest alternative is retain N+F without
buying this observation. This is not an additional B09 batch or a confirmation plan.

Context and source precedence:
- Current governance and plan at **4fde2d73466fc80d91c3afbbbf0e3afc9f3ba8a1**:
  `docs/project/OPERATING_CONSTITUTION.md` §§1–5, 7–9; owner pause is lifted, this task remains
  the independent DM, ordinary choices need no renewed approval, and three tracks is a runtime
  ceiling. Claude FSD stays owner-paused and G33 frozen. No App cross-task messaging is requested.
  `docs/research/RESEARCH.md` shared topic 6 and Current research plan, especially B1/B2 and
  “B2明确改变站端规则”; the source-picked B2 suggestion is revisable, not permission or a diagnosis.
- Existing advice at the same current-main revision:
  `docs/research/archive/2026-09-24/RESEARCH-next-investment-after-b18-b09-b08.md`, Answer's DM3
  comparison/branches and Decision item 2; and
  `docs/research/archive/2026-09-24/RESEARCH-question-led-programme-adopted.md`, Answer section
  “六、B2” and its Decision. These support prior investment reasoning, not new B09 measurements.
- Current methods at source_sha: `.agents/skills/hmasd-scientific-tools/SKILL.md`, Update the
  working explanation / Comparators / Statistics / Cost and exposure / Pro;
  `.agents/skills/hmasd-research-engineering/SKILL.md`, Core versus experimental / Checks and
  review. Use them proportionately, not as extra approval stages.
- Evidence at source_sha: this notebook's B09 prospective entry, complete B09 result and
  post-result inspection scope, and `runs/uav_service_auxiliary/b09_an_925031_a01/summary.json`
  plus its config/manifest/exit/status. Raw NPZs/checkpoints are retained at the two verified
  filesystem locations in the result entry, outside Git; they are not remotely readable via
  the connector. Do not claim to have independently read those bytes. Their summary and the
  DM's explicit verification/derived-read scope are available here.
- Frozen B09 inputs remain **e5e53534c2c0c4a059cfdfa5f3aff4cbc2166f46**. At source_sha,
  `envs/pettingzoo/relay/energy_aware.py` methods `_apply_energy_dynamics`,
  `_charging_candidates_by_station`, `_select_charging_uavs` and
  `experiments/candidates/uav_service_auxiliary/b07/native.py` energy diagnostics show the
  relevant unchanged rule and saved observation semantics. This is feasibility evidence,
  not an implemented successor.

Return: identify what B09 strengthens, weakens and leaves unresolved; decide whether the
narrow B2 investment is worth its real cost and why. If yes, sharpen the intermediate and
whole-episode predictions, useful adverse reading (especially waiters, failed exits and
censoring), and any smallest necessary comparator correction. Explain what observation would
make the allocation interpretation less credible without inventing a numerical pass gate or
requiring positive pilots. If no, identify a materially more informative feasible observation
or explain why no additional investment is warranted now. A new idea is not owed. Distinguish
mean/tail tradeoffs, post-result diagnosis and causal claims; return MATERIAL_DISSENT yes/no.
Answer in Chinese. Cite sources actually used and state consequential unread gaps.

Constraints: Give advice only; do not train, evaluate, change governance, launch a successor,
or edit outside the empty `### Answer` below on branch `codex/uav-service-feedback-b09`.
Read the pinned question, then fetch the latest target file before writing and use its actual
blob SHA. Preserve the question and all other bytes; stop on overlapping edits. On successful
write return the actual commit. If writing fails, return the **complete answer in chat**,
not only a status, link or purported SHA. Advice is not approval; the DM will own the choice.

### Answer

Saved from chat, 2026-09-25. The same accepted key `hmasd:182a489922f30764dcc02897f2eeea7ffceca02db9071056a0834a82d1a92a4b` completed. Delivery verification returned `NOT_DELIVERED`, with no answer commits and the pinned Answer still empty. The reply explicitly reports read-only GitHub access. Its `e6edf89575cf05d17a42b25e01724c5c58c56a6a` is the verified original NOTES blob, not an answer commit. Complete collected text follows unchanged; body SHA256 `a86fa17648b2e5db6da9d44e060ee9d5218920e2220c778feec12e75aff4d3d8` (9525 characters, before the collector newline). The observer closes its owned read tab in its finally path; no resend or cross-task message.

**GitHub 读取可用，但本轮可调用接口没有仓库文件写入或提交动作，因此未发出修改请求，实际 Answer commit：无。**最后核对的目标 blob 为 e6edf89575cf05d17a42b25e01724c5c58c56a6a，指定问题下的 ### Answer 仍为空。本轮没有修改仓库或运行实验。以下为完整答复。

B09 后的投入：支持一次站端连续准入比较，但不把“少抢占”当作服务成功

MATERIAL_DISSENT: no。

**我支持这一次窄 B2 比较：按原主要普通对照的角色固定 N925031 最终策略，保留完全相同的 F，在一组事前固定的 32 个新 H3000 世界上，比较原逐 tick 站端分配 O 与仍合格在充成员优先保留的 C。**总量保持为 0 新 fits、0 更新、64 次 episode 尝试、最多 192k 团队评价 transitions，不加入 A、额外策略、功率／阈值搜索或新训练。

支持它的理由是：新的完整结果与事后读取把一个实际发生、能被单独改变的站端分配行为明确了出来；它不再只是“有队列，所以可能需要调度”的泛泛猜测。需要收紧的是解释和读数：减少仍合格充电者被替换，是规则直接保证的行为变化；它既不自动增加供能，也不自动恢复无线服务。真正值得购买的观察，是这种能量分配时序能否改善完整服务，以及它会不会伤害被延后的等待者。

一、B09 加强了普通学习的用途，削弱了原样反馈训练的追加理由

B09 的共同初始策略和两个终点都部署同一个 F。以下是完整结果条目的原始尺度，不能用旧 B07 的终点代替，也不能把训练时是否接入 F 与部署时是否接入 F 混为一谈。

读数	共同初始化	N 终点	A 终点
原生完整回报 J	609.522261	986.436461	904.269871
累计 QoS	642.397612	1016.228609	934.664388
QoS／计划步	0.214133	0.338743	0.311555
平均充电输入 Wh	193.776042	158.237847	185.312500
平均 episode 最低电池比例	0.098619	0.108618	0.106019
零服务世界数	4	1	2

**被加强的是有限预算下的实际服务学习。**N 和 A 相对共同初始化的平均 J 分别增加 376.914200、294.747610，平均服务也均提高。真实训练、参数更新和 F 激活已有记录支持；本次不能用“候选没有真正训练”或“F 没有进入训练”解释结果。它也不是候选只比退化对照少退化的情形。

**被削弱的是：这套固定反馈条件训练能在同部署 F 下增加完整服务的预测。**A−N 的平均 J 为 −82.166590716，累计 QoS 为 −81.564221265，每步 QoS 为 −0.027188074。同时必须保留相反的一面：J 有 16 胜、16 负，J 中位差为正，服务中位差也为正。负均值不是逐世界伤害，正中位数也不能替代事前完整均值。最差世界 952016 中，N 的 QoS 为 0.323065444，A 为零，J 损失 −970.330951537；而 952009 的 A−N J 又提高 454.004581453。

局部恢复窗口没有挽救完整预测。两终点的首个合格退出后窗口都有完整 250 步，平均窗口累计 QoS 的 A−N 仅为 +0.073189783；每个选中窗口又都包含 F 再进入。世界 952021 尤其清楚：A 的窗口累计 QoS 高于 N，但完整每步服务只有约 0.267543，对照为 0.557600。这里不能把窗口叫作不受干扰的恢复阶段，更不能把那一点局部增量当作完整任务收益。

**仍未解决的是收益和损失的机制。**A 消耗更多能量、获得更多输入，却没有更高完整服务；所有三面板的 cutoff／depletion 均为零，包含初始化，所以本比较也没有识别出“新训练学会了避免这些事件”。站点分配、几何与 backhaul、策略访问历史和有限学习过程仍需区分。B08 的不完整技术失败及已付成本必须单列，不能拼作另一份完整 A/N 科学反例。

因此，我支持 DM 沿已有分支结束原样 B09 训练配方的追加投入。B2 是一个改变站端规则的新问题，不是为 A 找到一个有利环境后重新宣布 B09 成功。既有 B2 建议也明确把它视为资源分配干预，而非未变环境中的 actor 消融。

二、站点读数为何值得重视，又为何不足以诊断服务损失

新的事后读取比简单的“charge start/end 很多”更有针对性：N 在全部 32 世界中，共有 12,093 次上一 tick 实际充电、当前仍在同站合格却失去充电的事件。N 的 12,536 个连续充电段中，12,024 个只有一 tick，另有 35 个在观察终点仍未结束。它还保留了 52,814 个合格等待成员 tick，等待年龄的中位数／P95／最大值为 3／11／78，等待中的最低电池比例为 0.100904998。

这些事实加强了存在可修改分配时序的判断，却没有说明有多少服务能够因此恢复。A 的对应抢占次数更高，但两策略的到站、合格、驻留和充电暴露都由各自轨迹产生；原始次数差不能直接承担 A−N 的因果解释。

最强的竞争解释：原规则在做低电量均衡，而不只是制造无用切换

源码每步先按实际运动扣除能量，再在当前合格成员中排序，主键是电池比例，等待年龄和成员编号是后续排序键。一个成员充上一 tick 后电量提高，下次换给另一个较低电量成员，正可能是该规则的行为，而不是一次损坏的会话。等待年龄也不是严格的先来先服务保证。

更重要的是，当前这条能量路径没有额外的换人停机、重新接入耗能或充电启动损失项。每次获选成员直接取得本 tick 的充电量，受电池剩余容量限制。因此，对于同一个瞬时合格集合、相同容量和功率，且各获选者都有足够未充容量的情形，任一填满可用槽位的规则都有相同的瞬时总输入：

G
t
	​

=
3600
PΔt
	​

s
∑
	​

min(c
s
	​

,∣E
s
	​

(t)∣).

这是从当前代码推出的局部计量关系，不是说 O/C 的完整闭环总能量必然相同。两条轨迹会改变资格集合、运动、剩余容量和后续占位。它说明的是：不能把“减少切换”直接写成“省下切换能量”。

C 可能把相同的能量集中给一位成员，使其更早满足退出 F 的条件并回到服务过程；也可能让它继续占位，而较低电量的等待者持续耗能，延迟关键成员返回。甚至可能充得更连续，却仍不能恢复有用的无线几何。这是应当与候选正预测同等认真对待的反解释。

另外，当前 charging_wait_steps 在获选或不再合格时归零；逐 tick 记录的等待年龄分位数，并不是“每个到站成员完成等待时间”的分布。**不能把 P95=11 解释成 95% 的到站成员在 11 步内完成充电准入。**只读完成充电段，也会漏掉最需要关注的未获准入和仍在等待者。

三、为什么仍选择这次比较，而不是继续训练或立即停止

**最强的投入替代仍是保留 N＋F，不再支付这项观察。**普通参照已经有用；当前等待年龄并没有单独证明重大拥塞成本；连续优先还可能削弱低电量保护。192k 评价、站端实现和完整判读并非免费，不能因为 B2 已出现在共享计划中就自动执行。

我仍支持这一次比较，理由是它现在同时具备三个条件：干预位置已经由实际轨迹和源码定位；两规则能在不改 actor、F、功率和容量的情况下明确区分；正反结果都会改变是否保留这种分配方式的判断。它购买的是能量分配顺序的实际用途，不是再重复一次“多充电能否提高代理指标”。

这也解释了为什么不先再买一个反馈训练 fit 或新的预测头。B09 已对原样训练的增量作出不利观察，站端干预则作用于一个不同环节；无需先把全部学习或几何机制诊断完，才能检验这个有限选择。反过来，当前也没有理由扩成多个调度规则、多个策略或 A×站端规则网格。已有建议支持这条窄比较及其反面分支，但不替本次新证据作出决定。

四、C 的最小明确合同：保留真实在充成员，而不是保留意图或旧目标

这里我不要求新增对照臂，必要修订集中在上一 tick 的事实状态及其使用时刻。

1. 在正确的位置保存“谁实际在本站充电”

_apply_energy_dynamics 会先复制 charging_before，随后清空 uav_charging；更早的 _prepare_energy_actions 又会把当前 uav_target_stations 清为 −1 后重新赋值。因此，C 不能在清空后的数组上寻找 incumbent，也不能将本 tick 新产生的目标站误当作上一 tick 的实际服务站。

应保留上一 tick 实际有充电输入的成员及其当时获配站点，或者等价的站端实际服务集合。在 episode reset 时清空。它不是“曾经充过电”的永久权利，不包含仍在路上的返站意图，也不包含仅提出 docking 请求却未获电的成员。

2. 当前资格仍由原代码计算

当前合格集合仍在实际运动和耗能之后，由原条件产生：充电启用、成员未故障、有 docking 请求、实际速度满足条件、当前目标站合法且已进入 capture 范围。不得因为它是 incumbent 就豁免这些条件。原代码没有额外的“已经充满即不合格”或“退出 F 即不合格”条件，也不能在这个比较里默默补上。

对站点 s，令 E
s
	​

(t) 为本轨迹当前合格集合，P
s
	​

(t−1) 为上一 tick 在该站实际充电的集合。则

I
s
	​

(t)=P
s
	​

(t−1)∩E
s
	​

(t),
S
s
C
	​

(t)=I
s
	​

(t) ∪ Top
c
s
	​

−∣I
s
	​

(t)∣
	​

(E
s
	​

(t)∖I
s
	​

(t); b
i
	​

,−w
i
	​

,i).

空槽按原电量、等待年龄、成员编号顺序补足。排序使用原执行时刻的电量与等待状态，保留先选择、再按本次选择更新等待年龄的原顺序；不能通过提前更新等待状态再悄悄改变第二个优先级。

仍合格的本地 incumbent 保留；失去资格即释放。换到另一站不能把旧站的优先权带过去；中断后重新到站按新候选参加排序。F 的进入／退出、最近站点选择、运动与 docking 请求完全不变。

**这不是“充满再离开”规则，也不是最低驻留时间、超时抢占或紧急电量优先规则。**C 可能在 F 已退出而 actor 仍发出合法 docking 请求时继续保留服务；应读这个实际后果，而不是以更“合理”的隐含释放条件替换候选。若出现饥饿或无用占位，它就是当前固定规则需要承受的反面结果。

3. 相同的是资格定义和信息权限，不是实际资格集合

两规则各自运行完整闭环。充电分配第一次不同时，电量及下一观察就可能分叉，随后 actor、GRU、F、位置和资格集合都可能不同。不能把 O 的合格集合、动作或循环状态用于 C 的后续执行。

因此，应将旧建议中“相同候选集合”理解为相同定义和同一快照上的可比决策，而不是强迫两条已分叉轨迹保持同一集合。题面已经明确了这一点。这是一项站端规则干预；没有新增 actor 输入特征，但 actor 读到的原有电量、等待、占用等数值可以随新环境过程改变。

hmasd-pro-question-b09-result-a…

五、比较和估计对象：条件于一份策略的完整环境干预效果

固定 N925031 的实际最终 checkpoint、模型与 normalizer 状态以及原训练身份。选择它的依据是原主要普通对照的角色，不是在多个 checkpoint 中重新搜分数；但规则是在看过 B09 后提出的，新世界不会清除这段开发选择历史。

本次 O 是“原站端分配＋同一个 F”，不是 B06/B07 中没有外部 F 的旧 O。C 则是“连续准入站端分配＋同一个 F”。两者都从真实 reset 开始，保持 S7-S2、N8、k10、H3000、原生奖励、确定性评价、实际物理常数和信息接口。新 32 世界及匹配随机性在执行前固定，不选择旧抢占最多或服务最差的世界，不因前几个结果改变后续面板。

hmasd-pro-question-b09-result-a…

对每个世界 w，分别计算实际 episode 长度内的

S
w
r
	​

=
t=0
∑
L
w
r
	​

−1
	​

q
w,t
r
	​

,J
w
r
	​

=
t=0
∑
L
w
r
	​

−1
	​

r
w,t
r
	​

,r∈{O,C}.

主要读数是 32 世界等权的 S
C
−S
O
 与 J
C
−J
O
，并列保留累计实际交付量、S/3000 的计划窗口尺度、实际每步服务和 episode 长度。真实早终不能被替换、补跑或填成虚构奖励；仅用实际每步均值，会掩盖提前停止服务的代价。

**这是一个可以解释为固定策略及所选任务条件下、改变站端分配规则的总效果比较。**它比事后抢占次数与服务的相关关系更有判别力。但总效果包含后续电量分配、状态访问、actor 反馈和联合几何的全部变化，不等于“充电连续性”作为独立中介的因果份额。即使 C 成功，也不能反推 B09 的 A−N 损失由原分配规则造成，更不能宣布 A 已被修复。

32 个新世界可以描述这份固定策略的世界差异，不增加独立训练重复数；本次没有检验训练程序在 C 下重新学习会怎样，也不建立所有普通策略或所有调度器的排名。

六、把中间预测分成三个环节，等待者与未完成者始终在分母内
第一环节：规则是否真的改变了有竞争的分配

保留每 tick 的上一实际充电成员／站点、当前合格集合、原排序键、获选集合和实际输入。一个廉价且有用的诊断是：在 C 自己当前的同一快照上，另算原排序会选择谁。这只是确定性局部排序，不启动影子环境或分支规划，也不把它当作完整 O 的反事实轨迹。它可以区分“C 处于启用状态”和“C 确实保留了一位原规则会替换的 incumbent”。

同站仍合格抢占在正确 C 下应被规则排除；其归零主要是实现和暴露证据，不能被当作收益已成立的中间发现。充电段结束还应区分：失去资格、目标站变化、规则替换、实际 episode 结束，不能全部标成“无效抢占”。

第二环节：连续准入是否改变了恢复的机会，而不只是段长度

有区别的中间预测应是：

在实际有竞争的准入机会中，C 将供能集中给仍合格成员，使其更早完成实际净储能恢复并获得退出 F、恢复 actor 提议执行的机会；这种变化没有仅仅把长等待和低电量风险转嫁给其他成员。

不要求总充电 Wh 增加，也不要求“充电次数”更多。较少再进入、较少重复充电可能与更好用途相容；反之，长连续段可能只是长期占位。实际储能使用物理 pre/post 电池差，并保留输入、消耗和 clipping 的能量账，不能把源码的 max(0,input−consumed) 字段当作全程有符号储能变化。

等待者是这个预测的核心反面，不是补充图表。至少应读取每世界合格但未获电的成员 tick、每成员累计等待、等待中的最低电量及尾部、实际首次获电时刻，以及一直没有获电的合格成员。原 wait_age 可以保留，但要与完整等待区间分开，不能只统计最终成功充电者。

对连续合格等待区间，应区分“获得实际输入”“未获输入就失去资格或离站”“观察终点仍在等待”。前两种是不同的已观察结局，第三种才是仍未观察到结局的删失。真实耗尽、cutoff 或任务提前结束另行保留，不能统统包装成无害的未完成。

第三环节：恢复是否转成完整服务

沿用既有第一合格恢复退出后的 250 步描述是合理的，不需要另加评价面板。但应继续记录实际窗口长度、退出前是否已有服务、窗口内再进入 F、实际离站／继续停留及联合服务量。F 退出只恢复提议传递，不保证已经离站，不保证后续命令原样转成运动，也不保证队伍恢复服务。

“失败退出”应具体说明是退出后仍无服务、很快再进入 F、或未离开占位；不要把几种现象混成一个新成功分数。输入后未退出的 F 区间、仍在充电的连续段、仍在等待的区间，是三个不同分母。仅因 H3000 到达而未完成，不能断言永远失败；只观察到很短的退出后窗口，也不能填成成功。

B09 已展示这种分母区别：N 有 624 个输入承载 F 区间、408 个合格退出、216 个输入后无合格退出，以及 231 个整体右删失 F 区间；这些不能与终点仍在充电的 35 个连续充电段互换。

最终仍以所有世界的完整服务承接结论。退出事件和发生时间由规则影响，所以退出后窗口不是相同状态上的随机对照；没有成员拥有的链路／交付证据时，也不能把后续联合服务归因于刚充过电的那一架 UAV。

七、什么结果会削弱分配解释，什么结果值得保留
固定比较的观察	判断与投入变化
有竞争的实际分配改变；净恢复／有效退出更及时；完整服务和 J 有值得保留的增量，等待者风险与不利世界未抵消用途	保留这份 N＋F＋C 的有限用途，以及与分配时序解释相容的证据；不升级为一般调度优势、训练收益或安全保证。
连续段变长、抢占归零，但恢复没有更及时，等待尾部或最低电量更差	明显削弱“碎片化是当前可用恢复瓶颈”的解释。原最低电量优先可能在维持有价值的均衡；不通过追加紧急阈值或最长占位时间挽救本规则。
净储能恢复／退出改善，却没有完整服务增量	说明这一物理环节可改变，但不足以兑现所求服务用途。保留物理响应，结束当前 C 的服务改进投入；不能直接宣布几何就是唯一剩余原因。
平均服务或 J 提高，但少数等待者出现严重低电量、长服务空窗、新增零服务世界或事件	保留真实收益和真实代价，不能称作普遍改进或默认替换。平均值、正中位数和“已完成者更快”均不能隐去这些后果。
新世界中几乎没有实际 O/C 分配分歧	属于干预机会不足，不能据此否定活跃连续准入的作用；但也不自动筛选拥塞世界、加长时域或制造低电量开局来追求阳性。

其中，**最能降低当前分配解释可信度的不是 C 的切换数没下降，而是它已经按合同消除了相应替换、也充分改变了实际获电顺序，却仍没有改善可用恢复机会或完整服务，甚至损害等待者。**前者才是在机制已真正作用时得到的反面证据。若残余“仍合格同站 incumbent 被替换”来自保存了已清空状态或错误站点身份，则是实现问题，不能算作候选的科学失败。

我不从 B09 均值或历史等待 P95 反推一个数值通过线。服务、J、低电量尾部、零服务世界和实际成本发生冲突时，应公开其幅度并据用途判断，而不是事后挑一个有利指标。一次比较可以留下有用认识，却不值得继续支付同一规则的改造成本；正面结果也不自动接上重训、扩样或确认。

八、成本和最小必要工程

所选比较仍为：

2 规则×32 世界×3000=192,000

团队评价 transitions 上限，64 次 episode 尝试、1.536M UAV 动作行。O/C 各自真实执行，不能用旧 B09 的 O 类轨迹替代新世界中的原分配对照。旧 N 的 180k 训练是已有资产成本，0 新 fits 不等于一个未训练或免费控制器。

hmasd-pro-question-b09-result-a…

主要新增工程是：正确保存上一实际服务站点、一个有明确默认 O 路径的窄站端选择入口，以及支持上述等待／恢复／删失读数的完整轨迹。无需一般预约框架、全局调度器或多候选规划。

最小有判别力的工程复现可以让两架同站合格 UAV 竞争一个槽位：上一 tick 实际在充者当前电量较高，原 O 应选择较低电量等待者，C 应保留前者；随后分别改变 incumbent 的资格、目标站和 episode reset，检查优先权是否正确消失。再核对原顺序下的耗能、等待年龄更新、实际输入和能量闭合。这是规则语义检查，不是要求先有一个正面服务 pilot，也不是另一次科学面板。

新 O/C 的诊断共同前缀应保持到首次实际站端分配不同，不是到首次 F 覆盖。两臂 F 完全相同，早先共同发生 F 覆盖不会破坏配对；分配后的观察／动作分叉则是应保留的真实后果。模型、normalizer、optimizer 与评价随机性保持原零更新合同。

B09 的 290.698446 分钟是两 fits 加三面板的实际 runner 总耗时，N/A fit body 为 83.702513／101.548668 分钟；它们不能直接当作本次 192k 评价的校准耗时或规则固有速度。新 wall、站端实现、相应检查／独立高风险 review、存储、收取和完整判读均需计入，尚未测得的成本保持未知。

九、来源边界与最后判断

本答复阅读全文附件，并按指定版本读取了 B09 前瞻与完整结果、全部 32 个有符号世界、事后检查范围，当前治理／共享计划、两份指定旧建议中的 DM3／B2 段及采纳决定，以及相关方法、站端分配和能量诊断代码。推理输入分别保持为：

问题与 B09 证据：a8981446675a4b238da3a36940299fc67062b375。

指定治理与共享计划：4fde2d73466fc80d91c3afbbbf0e3afc9f3ba8a1。

B09 原执行身份：e5e53534c2c0c4a059cfdfa5f3aff4cbc2166f46，不因后继建议而改写。

**独立核验仍有明确缺口。**较大的 summary.json 正文读取返回空内容，另一读取接口报告文件过大或不支持；blob 接口得到 Base64 内容，但我没有完成解码后的逐项审阅。因此，本文数值依据是已完整读取的 B09 结果条目和逐世界表，并以 config／manifest／exit／status 核对执行记录，不能称为我独立重算了完整机器摘要。

仓库外 NPZ 与 checkpoint 没有被本次读取。382 个文件、370 个注册引用的核验，以及 12,093 次事件等派生计数，均明确归属于 DM 已报告的核验与限定范围事后读取。本站端后继规则尚未实现，新世界的暴露、等待者代价和完整服务效果都未知。现有来源足以支持这个事前投入判断，但不足以预先确认机制或收益。

**最终选择：结束原样 B09 训练配方的追加，保留普通 N＋F；同时支持仅一次上述窄 B2，以真实上一 tick 充电身份定义 incumbent，用完整服务和等待者的代价检验连续准入是否值得使用。**它值得做，是因为现在存在明确可改的分配行为和会改变判断的反面分支，不是因为 B2 已被写入计划，也不是为了挽救反馈训练。若只得到更长充电段、更少抢占或更多输入，而没有值得保留的完整用途，就结束这一固定规则的追加投入。

## 2026-09-25 — B10 adopted: one fixed-policy station-continuity comparison

### Decision, source use and limits

I read the complete preceding Pro answer, including its source-access limits and adverse branches. Adopt its narrow B2 investment as **B10 / UAV-SERVICE-STATION-CONTINUITY-B10**, not another B09 training attempt. `MATERIAL_DISSENT: no` is advice, not acceptance evidence. Pro did not independently recompute the large machine summary or inspect external NPZ/checkpoints; the B09 counts retain their existing DM verification provenance.

Current published main consulted at `5dda303f935ba8f4b6fa068179dd3bb6f6a83ad3`: [shared topic 6 and B09](https://github.com/CartmanFatass/My-paper-code/blob/5dda303f935ba8f4b6fa068179dd3bb6f6a83ad3/docs/research/RESEARCH.md#6-实证研究是在具体条件下缩小解释空间), [current B1/B2 investment](https://github.com/CartmanFatass/My-paper-code/blob/5dda303f935ba8f4b6fa068179dd3bb6f6a83ad3/docs/research/RESEARCH.md#current-research-plan). The B09 native gain of both trained arms strengthens the ordinary learned reference, while the negative A−N full-service mean and positive recovery-window/median counterexamples weaken unchanged feedback-training investment. The B07 physical recovery plus remaining service losses, B04/B05 reward/service trade-offs and B03 proxy reversals are inherited constraints: a longer charging spell, more input, or lower proxy cannot stand in for full service. Keep B08 technical failure separate. B2 remains the third project-plan priority; this direction owns the selected bounded comparison and does not take over another lead.

Verified the consequential code claims in `envs/pettingzoo/relay/energy_aware.py`: `_prepare_energy_actions` clears/recomputes targets before `_apply_energy_dynamics`; the latter snapshots then clears `uav_charging`, consumes motion energy, computes current eligibility, selects, supplies per-tick charge, updates waits and clips battery. Original sorting is post-consumption battery, negative prior wait age, member index. There is no extra switching/startup energy term on this path. Thus preserve the prior actual charging station before preparation resets it; neither return intent nor a cleared current mask defines incumbency. No new literature premise is needed for this code-local comparison.

Choose this once over stopping at N+F because observed switching is widespread and this intervention has distinct favorable and adverse predictions at affordable zero-new-fit exposure. Do not treat the retrospective 12,093 N replacements as a diagnosis of A−N loss. The strongest alternative is useful low-battery balancing: continuing incumbents may delay lower-battery waiters, waste occupancy or fail to restore useful wireless geometry. No additional feedback-training seed, auxiliary head, A arm, threshold search, dwell timer, emergency override or population training is selected.

### Fixed comparison and costs, before implementation or new outcomes

- One retained policy: B09 ordinary N925031 final endpoint, selected by its original primary-baseline role, with the exact saved model/config/normalizers. Source execution `e5e53534c2c0c4a059cfdfa5f3aff4cbc2166f46`; source root `b09_an_925031_a01`; checkpoint `N/endpoint/agent.pt`, SHA256 `2ba395b9f2761a9a761bd648d399b525c61b7babdb84edbe293319d269eeff5a`. Durable copy `/home/fires/hmasd-artifacts/uav_service_auxiliary/b09_an_925031_a01`; original node output `/home/wu/hmasd-worktrees/usa-b09-48388289d/runs/uav_service_auxiliary/b09_an_925031_a01`. No selection among other checkpoints or arms. Old N construction cost remains 180k training; B09/B08/full direction exposure remains recorded above.
- Two station rules **O then C**, both always deploy unchanged B06/B07 F. Here O means original station allocation WITH F; it is not old B06/B07's no-F O. S7-S2, N8/k10, native H3000 from reset, deterministic policy evaluation, native reward coefficients including return coefficient 2, same physical constants, eligibility definition, information features, adapter, F, nearest station, reset and recurrent semantics. Derive only one-lane evaluation storage from the saved H3000 config; do not rewrite training identity.
- **32 new paired evaluation world seeds 953001 through 953032 inclusive**, all fixed now; no prior result from this panel read or run. Complete O panel then C panel in increasing seed order. Same per-world policy/RNG initialization and exogenous reset identity; each trajectory thereafter evolves independently. Preserve prefix equality through the first differing station selection (which can occur after earlier common F overrides); no shadow rollout, reused O candidate sets after divergence, branching simulator or optimizer update.
- **0 new fits, 0 training transitions, 0 optimizer updates; 64 episode attempts, at most 192,000 team evaluation transitions / 1,536,000 UAV action rows.** Real native early terminations reduce actual exposure and remain outcomes; no padding reward, replacement world, top-up, interim checkpoint or development panel. No new trained-seed inference: 32 worlds are conditional on one historical trained policy and these chosen task conditions. New world seeds do not erase post-B09 design exposure.
- Configured `wsl_4070`, CUDA FP32, 4 torch threads, TF32 off, same native backend. Fresh actual-node admission after source publication. Dominant work is the 192k closed-loop native steps plus bounded same-snapshot ordering over 8 members, not another learned model or trajectory search. Full new wall is not yet measured; B09's 290.70 min includes two fits, three panels and other work and is not a B10 calibration. Record runner/evaluation wall, CPU user/system, RSS scope, preparation/check/review and collection cost; unknown is not zero. No score-dependent extension; a technical failure is retained and never automatically retried.

### C rule and discriminating readings

For each station, retain members who actually received positive charging input at that station on the previous tick AND are currently eligible there under the original definition. Fill remaining original-capacity slots with the original `(battery, -wait_age, member_id)` ordering at the original execution point. Reset clears incumbency; ineligibility or a station change releases it; interruption confers no persistent priority. Do not add a full-battery, F-exit, minimum-stay or emergency-release clause. Capacity, power and all other environment rules stay as in the original host; state values, eligibility sets and later actions may differ in the two complete closed loops.

Primary finite comparisons are equal-world mean **C−O cumulative native QoS and native J** on all 32 paired worlds, with each signed world, mean/median/wins/losses, actual delivered Mb, QoS/3000 planned-window scale, actual per-step service and episode length. Keep return cost, minimum battery and its lower tail, cutoff/depletion/failure, zero-service worlds, longest service-free intervals, input/consumed/signed stored Wh and clipping. No calibrated training-population CI, equivalence or universal scheduler/safety claim. Conflicting service/J/risk outcomes must be read together rather than choosing a favorable score after the fact.

The useful positive prediction is that, where C really changes contested allocation, energy reaches a retained member in a sequence that improves net recovery and availability to exit F/resume actor proposals, WITHOUT merely shifting long waits or low-battery exposure onto others, and that complete service/J show useful benefit. Zero remaining same-station eligible-incumbent replacement is primarily implementation/exposure evidence, not a gain. More total charge is not required because no switching loss is modeled.

Retain per-tick prior actual charging mask/station, current eligibility/target, post-consumption battery and prior wait-age keys, actual selected members/input, and deterministic original-rule selection on C's own snapshot. That extra sort is diagnostic only. Charging-spell endings distinguish ineligibility, station change, actual rule replacement and end-of-observation censoring. Preserve all eligible waiting UAV ticks, per-member cumulative waits, waiting battery tails, first actual input and eligible members never charged. Contiguous eligible waiting intervals keep three different endings: actual input, loss of eligibility/station departure without input, and still waiting at observation end. True depletion/cutoff/early terminal events remain explicit. Wait-age percentiles are tick-weighted ages, not completed arrival-wait-time quantiles.

Reuse the full physical ledger and B08 opportunity intervals, including input-bearing F intervals without qualifying exit, no-positive-gain intervals, and right-censored F intervals. Keep the first qualifying physical-recovery/F-exit 250-step team-service window with actual length, pre-exit service, F re-entry, actual station departure/continued occupancy and signed stored energy. Charging spells, waiting intervals and F intervals are different denominators. A qualifying exit restores proposal passing; it does not guarantee departure or same-UAV delivery. Post-exit windows are descriptive, not matched-state causal estimates.

Decision branches fixed now: useful complete service/J with tolerable observed waiting/risk costs retains only this conditional package; longer spells with no recovery/use, or worsened waiting, weakens the current fragmentation explanation and ends unchanged C investment. Physical recovery improvement without full service ends this service-improvement recipe while preserving physical facts. Gains with serious adverse worlds are trade-offs, not default replacement. Little actual rule disagreement means opportunity insufficient in this panel, with no automatic congestion selection/horizon extension. No branch automatically buys retraining, another policy, another rule, extra worlds or confirmation. The result cannot diagnose B09 A−N loss or repair A retrospectively. Further responsibility follows the scientific question, not an endless rescue of C.

### L0 — bounded B10 implementation and acceptance

Deliver a station-rule evaluator plus the diagnostics above under new owned paths `experiments/candidates/uav_service_auxiliary/b10/`, `scripts/run_uav_service_auxiliary_b10.py`, and `tests/experiments/candidates/uav_service_auxiliary/b10/`. Prefer a candidate-local `UAVEnergyAwareRelayEnv` subclass/adapter with an explicit O default and C override, using the existing native eligibility/energy/reward path, so frozen B01–B09 and shared environment sources remain byte-identical. Reuse B07 `evaluate_world`, B08 opportunity metrics, B09 persistence and standard policy-state utilities where adequate; do not globally monkeypatch a frozen module. Capture prior station/charging before target preparation, snapshot ordering inputs at selection, and collect matching diagnostics for O and C. Current rules do not require a general reservation framework.

The new runner must call native admission before scientific imports/effects; enforce fixed source checkpoint/config/summary digests and saved config identity, production seeds/horizon/rules/device/threads. Restore the checkpoint and normalizers, compare full learner/optimizer/normalizer states before/after each panel and keep zero new updates explicit. Write compact aggregate/per-world summary/config/progress and content-hashed per-world raw NPZ/details outside Git; retain completed and partial traces on failure with no output overwrite or resume. Test fixtures may use tiny horizons/seeds only in internal APIs, never weaken production CLI bindings.

Focused checks: two eligible UAVs/one slot shows O chooses the lower battery waiter and C retains the true prior incumbent; real preparation/energy path captures original station before clearing; eligibility loss/station switch/reset release priority; original wait ordering, capacity, energy closure and input facts; O off-path native equality; correct interval endings and incomplete/no-input denominators; independent paired prefixes through first differing allocation, immutable policy state and zero updates on a tiny native fixture; source-binding and admission-before-effects failures. All test scratch follows `tests/AGENTS.md`. Use the registered independent Reviewer for this change's scientific state and result identity risk. Implementer, if used, owns only those new executable/test paths, makes no scientific decision or launch, and does not edit NOTES/index; DM reads the diff/checks, resolves findings and accepts. No result-bearing launch until accepted exact inputs are published. B10 source SHA and launch manifest will be linked after acceptance; this is a new prospective operation, not a B09 restart.

Prior housekeeping reconciled: after B09's two copies and all hashes were verified, its terminal disposable launch snapshot `aec8e9ed68e44668899fa55c7a3b1060` was removed by the native snapshot collector. Initial preview refused an inaccessible `/proc/660/cwd`; documented read-only `--sudo-process-scan` then proved eligibility and `--apply` returned removed. Original output, independent durable copy, authoring checkout, published source and admission claim remain. The clean main publication worktree was removed only after remote commit verification; its branch is retained.

## 2026-09-25 — B10 implementation prepared and local checks read

The bounded Implementer returned only the six new candidate/runner/test files in the L0. DM read all production paths and the focused tests; frozen B01–B09, `hmasd/`, `envs/` and config source bytes remain identical to the B09 execution source. Station C reuses the native physical path through a candidate-local subclass; O is its explicit default. Source checkpoint, config and summary digests were independently re-read from the durable copy; saved checkpoint config matches bound config.json, including the original H3000/two training lanes and available model/optimizer/value-normalizer state.

Resolved during implementation: compare selected membership rather than ordering; break waiting intervals on station change; separate selected-without-positive-input endings; accept native launch metadata without accepting old scientific output; supply the paired megabytes field; use the checkpoint-saved config; refer exit-window departure to the last actual charging station in the qualifying interval; keep compact journal updates separate from world/panel summaries. Completed physical NPZ is persisted before derived diagnostics, and existing raw evidence is hashed into the incomplete summary on an ordinary failure. A fault-injection fixture checks that postprocessing failure retains reward, battery and station evidence. Fatal process signals can still interrupt the current world; last persisted worlds and journal counts, not assumed completion, then bound the claim.

Implementer reports **14 passed, 1 CUDA skipped** for B10 plus reused B08 opportunity tests on the configured CPU interpreter. Independent Reviewer ran the then-current B10 suite: **7 passed, 1 CUDA skipped in 5.49 s**, with no material finding; final native-file changes are receiving the focused final read. Other production file digests match that review. Local CPU fixtures use only tiny test worlds, not the production panel. The CUDA fixture on the actual node remains required for the intended execution path; no new scientific fit or production world has run. Full implementation is published before node-side checks and result admission. The narrow station/denominator tests exercise competition, waiting and reset, while the tiny evaluator checks binding, prefix and immutability; neither is a positive-service pilot or a full charging-cycle result.

## 2026-09-25 — B10 implementation accepted for the fixed production comparison

DM accepts implementation `315fe22233f567f314a0b43c5a7c5dffea8a774f` after full source/test reading and the independent Reviewer's final targeted read of native SHA256 `2adfb205e60272eb4b315bb031d9f7a13822b0a8642b86b4d213f1124ef53719`: no material remaining issue. The complete world NPZ precedes diagnostic calculation; ordinary failure registers raw files and persists an incomplete summary. Final node checks at that published source, using configured `wsl_4070` interpreter and source-root override, passed **15 tests / 0 skips in 7.83 s** (8.777 s command wall), including real CUDA FP32/4-thread/TF32-off tiny evaluation, CPU path, source binding, original native path, state immutability, prefix and injected postprocessing failure. Fourteen third-party matplotlib/pyparsing deprecation warnings did not change the result. No additional unchanged tests are needed. Full H3000 charging/service behavior remains the prospective observation, not an engineering claim.

Preparation had no scientific effects: one node test invocation was issued before the new checkout existed and never started pytest. Its log is retained in local scratch. The initial read-only Git fetch used a non-login shell without configured proxy variables and remained pending; after verifying its exact owned process identity, only that fetch and its two children were terminated. The configured `zsh -lic` network environment then fetched the same published source and created the clean node authoring checkout `/home/wu/hmasd-worktrees/usa-b10-315fe2223`. Its shell startup printed zle/monitor/gitstatus warnings but the fetch, checkout and checks succeeded. No experiment worker, accepted Pro request or previous scientific operation was restarted.

Proceed with the fixed O then C comparison, tag `b10_oc_925031_a01`, original source artifacts and production world seeds in the prospective entry. The final input commit contains only this acceptance append beyond the checked implementation; executable bytes stay unchanged. Publish it before launch. Native admission still checks fresh pause/lead/published identity and actual-node memory; current run/wait handles will be linked after actual acceptance. The model-free observer will then own waiting on the same operation. This does not expand the 0-new-fit/64-attempt/192k-step maximum or prewritten interpretation branches.
