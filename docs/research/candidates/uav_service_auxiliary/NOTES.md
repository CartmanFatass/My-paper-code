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
