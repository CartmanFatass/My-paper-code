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
