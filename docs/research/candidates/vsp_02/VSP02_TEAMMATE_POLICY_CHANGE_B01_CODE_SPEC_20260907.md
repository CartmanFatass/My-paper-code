# VSP02 teammate-policy-change B01 — complete code specification

This is the **one common implementation specification** for P14-VSP02-B-CARD-AND-CM-COMPARISON-01.
Implement the accepted scientific design below, not the historical VSP02 learner. The companion
B card defines the claim/interpretation; the full Pro source is
`pro_packets/20260907_teammate_policy_change_convergence/archive/RESPONSE.md` at
`1eb3b21b61747b21f374d252005fa48c32e4838d`. No model-specific summary or alternate specification.
The complete committed package returned by DM is Root's common starting SHA for all five arms;
Root records that full SHA in its capture. No implementation has started in this source package.

## 1. Deliverable, ownership and dependencies

Deliver a runnable CPU implementation of the new cooperative host, recurrent PPO, shared-prefix
full-Adam fork, sampled evaluator and primary-output publication, plus focused tests. Leave a diff
and actual check evidence in the isolated worktree supplied by Root. **Do not commit/push, create
branches, spawn children, message other tasks, read another arm's work, send Pro requests or run
scientific B01.** Root performs independent scientific-risk review and production integration
outside the timed implementations. P14 authorizes coding through that route, not a research run.

Owned research paths (new files only):

- `experiments/candidates/vsp_02/teammate_policy_change_b01/__init__.py`
- `experiments/candidates/vsp_02/teammate_policy_change_b01/host.py`
- `experiments/candidates/vsp_02/teammate_policy_change_b01/learner.py`
- `experiments/candidates/vsp_02/teammate_policy_change_b01/study.py`
- `scripts/run_vsp02_teammate_policy_change_b01.py`
- `tests/experiments/candidates/vsp_02/teammate_policy_change_b01/test_host.py`
- `tests/experiments/candidates/vsp_02/teammate_policy_change_b01/test_learner.py`
- `tests/experiments/candidates/vsp_02/teammate_policy_change_b01/test_study.py`

No existing VSP02 attempt, core package, generic trainer, governance/configuration, science document
or dependency manifest is owned by an implementation arm. Keep helpers in these files; no new
framework or unlisted source module is necessary. The direction's eventual production checkout is
`C:/Projects/HMASD-worktrees/dm-vsp02` on `codex/vsp02`; comparison worktrees are temporary isolation
already authorized by the comparison protocol, not new authoring branches.

Use the existing local scientific interpreter
`C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe`. Read-only metadata on 2026-09-07 reports
CPython3.10.20, torch2.7.0, numpy1.26.3, pytest9.1.1, matplotlib3.10.0. Torch CPU2.7 is the repository's
local scientific environment. No install, upgrade or import-time download. Use stdlib plus torch
and Matplotlib Agg for the figure; NumPy is available if useful for array conversion. No Gym,
PettingZoo, TorchRL, BenchMARL or external framework is required. Do not encode an absolute
interpreter path in source. Relative imports must work from the listed root-level commands.

Keep public testable boundaries named `HandoffEnv`, `RecurrentPolicy`, `make_optimizer`,
`compute_gae`, `fork_agents`, `StudyConfig` and `run_study` in the logical files above. Ordinary
internal helper choices are free within this specification. Host/reset/step and policy shapes
are fixed below; wrappers may expose these names without changing semantics.

## 2. Host and observation contract

Fixed entities A (receiver) and B (courier), with distinct fixed roles and N=2. Positions are integers
-2,-1,0,1,2. Actions use indices 0=LEFT, 1=RIGHT, 2=WAIT, 3=RECEIVE for A / DELIVER for B. All four
are allowed; do not mask ineffective transfer actions. Moving beyond an endpoint stays there;
robots may co-locate without collision cost. One action never both moves and transfers.

`HandoffEnv(batch_size)` represents an ordinary **in-process** batch of complete independent
48-step episodes. `reset(lights, changed)` accepts a CPU integer light tensor `[B,16]` with values
-1/+1 and a common boolean regime/change-notification bit; returns FP32 observations `[B,18]`.
Positions start at zero; there is one fresh package per round. The light is stationed at coordinate
zero and remains fixed throughout its three-step round. It is visible to an agent iff the agent's
current position is within distance1 of zero. Each round's light is drawn independently with p=1/2
by the collector, never by the policy. Pre-drawing exogenous lights does not expose future values.

At pre-action time `t=0..47`, `round=t//3` and `clock=t%3`. For clocks0 and1, B chooses one move
toward `light[round]` in the old regime or its negative in the new regime. At clock2 B chooses
DELIVER. B reads its own local initial light and follows this fixed script; no training, script
selection, replacement or co-adaptation. `changed` is private host configuration except for the
same public 0/1 notification field given to A; do not include target endpoint or script internals.

`step(receiver_actions: int64[B])` executes a simultaneous step and returns
`(next_obs_or_None, reward: float32[B], done: bool)`. The order is:

1. Use only the current observation to choose A's action; compute B's simultaneous scripted action.
   No current B action is visible before A selects.
2. Record whether B was within distance1 of A **at the start of this step**. That determines whether
   this executed B action may appear as an observed past action on the next observation.
3. Award exactly 1 iff pre-action positions coincide at -2 or +2 and the actions are RECEIVE and
   DELIVER. All other rewards are0. Apply each move clipped to the corridor. A transfer action does
   not move; thus simultaneous movement cannot also earn a transfer. No other reward or shaping.
4. Record A's just-executed action, the actually visible B action/mask and the realized reward.
   After clock2, discard any unserved package and reset **positions/task package** for the next
   round, retaining previous-action/reward signals. Do not reset GRU or change entity identities.
5. After t=47, done is true and next observation is None. Otherwise form the next pre-action
   observation with the appropriate new clock/light. There is no early termination.

One courier DELIVER opportunity per round enforces at most one service per package. The return
0..16 follows this service definition, not an exact policy search or a headroom experiment.

Exact observation columns (raw FP32 scalars/one-hots, without scaling or running normalization):

| Slice/index | Field |
| --- | --- |
| 0 | A's own position (-2..2) |
| 1 | Current within-round clock (0,1,2) |
| 2 | Current round index (0..15) |
| 3,4 | Visible light sign (-1/+1, or0 when missing), and its visibility bit |
| 5,6 | Current B-minus-A relative position when abs(distance)<=1 (otherwise0), and its visibility bit |
| 7:11 | One-hot B action from the previous executed step iff it was observable under step2 (otherwise four zeros) |
| 11 | Previous B-action visibility bit |
| 12:16 | A's own previous executed action one-hot |
| 16 | Previous realized shared reward (0/1) |
| 17 | Public change-notification bit (old0/new1) |

At complete-episode reset all previous-action one-hots, previous-action visibility and previous
reward are zero. At service-round reset they persist as last observed signals; recurrent state
also persists. No absolute training-episode index, global positions beyond local B visibility,
private regime label beyond the notification, target, future light/action or correctness sign.
Actor and critic consume **only this same tensor and its recurrent history**. Test visibility by
changing hidden B/light quantities while A is out of range and checking the specified fields.
The lamp radius, past-action sensing time and exact encoding are disclosed DM concretizations of
Pro's local-observation description, not broader information access.

## 3. Policy, returns and PPO

`RecurrentPolicy` constructs modules in this order: `nn.Linear(18,64)` encoder, one
`nn.GRU(64,64,num_layers=1,batch_first=True,bias=True,dropout=0,bidirectional=False)`,
`nn.Linear(64,4)` actor, `nn.Linear(64,1)` critic. Use standard PyTorch reset_parameters defaults
under the initialization seed, tanh only after the encoder, and direct GRU output into both heads.
No layer normalization, extra layers, attention, dropout, auxiliary target, pretrained policy,
action oracle or separate critic observations. This has 26,501 trainable scalars in ten parameter
tensors. FP32 on CPU throughout; no autocast, compile/JIT or device substitution.

`forward(obs[B,T,18], hidden[1,B,64] or None)` returns logits[B,T,4], values[B,T], and next hidden.
None means zeros. Collection calls T=1 and carries hidden for all48 steps; recurrent PPO evaluates
complete episode sequences from zeros. No hidden reset/detach at the three-step round boundaries
and no truncation of training sequences; gradients span a whole48-step minibatch sequence.
Collection/evaluation use no_grad. Sampling is categorical with softmax(logits) and
`torch.multinomial(...,num_samples=1,generator=<named private CPU generator>)`; use standard
Categorical log_prob/entropy or mathematically equivalent torch functions. No argmax sampling.

`make_optimizer(model)` returns one torch.optim.Adam over all ten trainable parameter tensors:
lr=0.0003, betas=(0.9,0.999), eps=1e-8, weight_decay=0, amsgrad=False, foreach=False, fused=False.
The shared trunk, actor and critic have one backward/step. No separate optimizers or gradient
accumulation. Constant learning rate and entropy coefficient for prefix and adaptation.

A rollout contains16 complete48-step episodes under one unchanged policy and courier regime.
Store observed inputs, sampled actions, old log-probabilities, old values and native rewards;
these actual on-policy trajectories are fixed during that rollout's PPO update. Never replace
post-fork data with another arm's trajectories. Do not use B's private state when forming labels.

`compute_gae(rewards[B,H],values[B,H])` uses gamma1 and lambda0.95 independently per episode:
`delta_t = reward_t + value_(t+1) - value_t`, with `value_H=0`; then
`A_t = delta_t + 0.95*A_(t+1)`, with `A_H=0`; value target is `A_t+value_t`.
Only the complete-episode boundary has zero bootstrap; service rounds are continuing states.
Targets and old log-probabilities/values are detached. Standardize all16*48 unnormalized advantages
once per rollout using population std (`unbiased=False`) plus1e-8; value targets stay unnormalized.

For each of four PPO epochs, privately permute the16 **episode** indices and divide into four
minibatches of four complete episodes. No timestep shuffle, padding, dropped tail or chunk split.
Recompute each minibatch's recurrent sequence with current parameters from zero hidden state.
For ratio `r=exp(new_logp-old_logp)` the policy loss is
`-mean(min(r*A, clamp(r,0.8,1.2)*A))` over all minibatch episode/time entries.
Value loss is `mean((current_value-detached_target)^2)` (no additional one-half factor, no value
clipping or Huber loss). Entropy is mean categorical entropy over the same entries. Joint loss is
`policy_loss + 0.5*value_loss - 0.01*entropy`. Zero gradients, backward once, clip the **joint**
parameter gradient norm at0.5, and call Adam.step once. Exactly16 actual steps per complete rollout.
No normalization or hidden update from data outside the current rollout.

Tests must independently check a small formula case: rewards[0,1], old values[0.2,0.4] give
unnormalized advantages[0.77,0.6] and targets[0.97,1.0]. Ratios[1.5,0.5], advantages[1,-1] and clip0.2
give policy loss -0.2. These are fixture arithmetic, not a benchmark. FP32 numerical checks use
scale-appropriate atol1e-6/rtol1e-5 where applicable, not project-wide extreme equality tolerances.
Integer counts, masks and explicit same-object copies are exact semantic checks.

## 4. Prefix, full-state fork, RNG and adaptation

Scientific StudyConfig is fixed: seed1103, P4096, Q1024 per descendant, rollout16, H48, E64,
post-update evaluation q=(16,32,64,128,256,512,768,1024), wall_seconds1800. No CLI sweep knobs for
these dimensions. One independent prefix only; no no-change arm, extra seed or policy pair.

Ordinary CPU generator seeds are `master + offset`, using this fixed table. Do not use Python hash,
an addressed RNG service, implicit global draws after initialization, or a different stream per arm.

| Purpose | Offset / pairing |
| --- | --- |
| Base model initialization | 0; seed global torch once before constructing the single prefix model |
| Prefix light/action/minibatch permutation | 1 / 2 / 3, separate private generators |
| Adaptation light/action/minibatch permutation | 11 / 12 / 13; clone the initial generator states for CARRY/RESET |
| Old-prefix endpoint evaluation light/action | 101 / 102 |
| Shared post-switch q=0 evaluation light/action | 201 / 202 |
| Post-update checkpoint i=1..8 in the declared order | 1000+10*i / 1001+10*i; fresh identical generators for both arms at each checkpoint |

For a collector batch of B episodes draw `[B,16]` lights with private
`torch.randint(0,2,...)*2-1`. Advance each arm's own stream normally. Action sampling uses its
own generator and actual current probabilities; paired streams do not force identical actions.
Training minibatch permutations use the specified shuffle generator. Evaluations never touch
any training generator or mutate network/optimizer/global training progress. Different checkpoints
use the separate seed pairs above. No reseeding to choose a result.

Train the prefix for exactly256 rollout batches; preserve all4096 actual episode returns and
actual4096 optimizer steps. Perform its old-policy evaluation with the old courier and change bit0.
After the final prefix update and discarding consumed rollout data, `fork_agents` constructs
independent models, optimizers and generator objects for two descendants. They carry identical
network parameters, fixed hyperparameters, global progress4096 and zero episode hidden state.
CARRY deep-copies complete Adam state; RESET clears the joint optimizer state, including moments
and every per-parameter step counter, while keeping the same new arm's parameter references and
parameter groups. No shared tensor storage may make an arm update mutate the other or the prefix.
This is in-memory algorithm state, not checkpoint/resume machinery. Do not reset the network,
critic alone, global progress or constant schedule. Model copying must not alter named RNG streams.

Switch the courier to the new rule/change bit1; evaluate the common policy once at q0 (64 episodes).
Then alternate CARRY rollout/update, RESET rollout/update at each adaptation batch index, so both
have the same planned16-episode progress. Evaluate both when both reach a declared checkpoint.
Each arm uses its own real interactions and hidden states, resetting only between complete episodes.
Each complete descendant has64 rollout batches and1024 actual updates. Its global update count is
5120; CARRY's Adam per-parameter steps end at5120 while RESET's end at1024. These state facts do not
imply any expected reward sign. Report both actual results.

Capture initial model parameters in memory for displacement measurements. Publish initial parameter
RMS; displacement RMS after the first completed prefix rollout and at prefix end; arm displacement
RMS from fork at final/cutoff state; actual steps at each reading. A numeric fork summary records
model max absolute difference, global progress, Adam state-entry counts, moment norms and min/max
step counts before adaptation. No hash, byte manifest, runtime provenance guard or score threshold.
A meaningful nonzero parameter change on the bounded engineering fixture demonstrates the real
update path; no fixture return improvement is required.

## 5. Evaluation, primary output and incomplete work

Old-prefix evaluation is64 sampled full episodes, labelled PREFIX/old. Shared q0 evaluation is one
64-episode sample, labelled SHARED/new, referenced by both evaluation curves, not duplicated as128
actual episodes. Each later checkpoint evaluates64 per arm with fresh paired exogenous/action
streams. Evaluation runs frozen stochastic policies without optimizer access; GRU starts at zero
for each episode and persists across rounds. Batches up to16 are ordinary in-process batching;
the E4 engineering fixture uses a4-episode evaluation batch. No greedy, extra exploration mixture,
checkpoint search, or training from evaluation.

`run_study(StudyConfig, out_dir, clock=...)` drives this one straight prefix/fork/pair chain and
returns its summary. Injectable monotonic clock is solely a focused timeout test seam; do not add a
scheduler/worker system. The CLI accepts `--out`, `--seed` (scientific default1103) and
`--engineering-fixture`. The fixture is the only shortened mode; no unrestricted P/Q/arm/sweep menu.
The production invocation uses seed1103; a different scientific seed needs a separate assignment.
Record the actual requested seed rather than pretending a changed seed was1103.

Outputs under the supplied run directory:

- `training_returns.csv`: phase (prefix/adaptation), arm (PREFIX/CARRY/RESET), one-based phase
  episode, actual return, actual joint steps, complete_episode flag, and policy's actual global
  optimizer-step count before collection. Preserve every completed and cutoff partial episode.
- `evaluation_returns.csv`: phase (prefix/post), arm (PREFIX/SHARED/CARRY/RESET), checkpoint q
  (P for prefix), episode, actual return, actual joint steps and complete_episode. Shared q0 rows
  occur only once. Do not report evaluation episodes as independent training samples.
- `training_curve.csv`: phase, arm, through_episode, episodes_in_bin, mean_return, from
  non-overlapping16-episode bins of the raw complete episodes; label any last partial bin size.
- `updates.csv`: one row per completed or interrupted rollout update, with phase/arm, rollout
  index, actual optimizer steps in that update, total global steps, complete_update, and mean
  policy/value/entropy losses plus maximum pre-clip gradient norm over steps actually performed.
  Maintain actual counters per Adam.step, including an interrupted minibatch sequence.
- `curves.png`: Matplotlib Agg, prefix training curve, both adaptation training curves, and both
  sampled evaluation curves/endpoints. Use all bins/checkpoints; no smoothing that drops data,
  selected best result, GUI or training-population confidence band. On a deadline/error, report
  any missing figure explicitly; a missing display does not erase trustworthy raw measurements.
- `summary.json`: object_id, `run_kind` (B_EXPLORE or ENGINEERING_FIXTURE), actual config/seed,
  source Git revision when readable (record only; no refusal guard), Python/torch/platform/device,
  status (COMPLETE / TIME_LIMIT / ERROR), error or stopping reason, actual exposure counts by
  phase/arm and total, prefix/post evaluations and terminal means, primary and partial readings,
  movement/fork summaries, wall_seconds, optional peak_rss_bytes and resources_unmeasured flag,
  and output paths. No schema versioning framework or manifest.

For a **complete** scientific pair, primary is the mean of each arm's1024 actual adaptation
training-episode returns and their RESET-CARRY difference. Set `primary_window_complete=true`
when both complete Q windows were actually observed. Set `scientific_comparison_complete=true`
only when the scientific mode also completed its declared training/update/evaluation counts without
a comparison-threatening failure; state one independent prefix and the one-pair claim ceiling.
If either Q window is incomplete, `primary_window_complete=false` and `primary=null`; preserve
`partial_observations` with actual episode/update counts and clearly partial observed means.
If the Q windows are complete but a later update or secondary evaluation is incomplete, preserve
the directly observed full-window primary, set scientific completeness false and name that narrower
limitation. Missing secondary outputs cannot erase independently trustworthy native-return facts.
Do not relabel a shorter window as B01's full primary or replace it with evaluation AUC. Optional
resource/visual gaps follow the same dependent-claim rule, not automatic annulment.

For ENGINEERING_FIXTURE, output the same arithmetic primary for its reduced Q, but always
`scientific_comparison_complete=false` and explicitly state that it is engineering-only. Never
combine fixture observations with seed1103 or report an arm as scientifically superior from tests.

Start the whole-invocation monotonic clock in the runner before scientific/plot imports. Set one
CPU compute thread, including torch intra-op/inter-op settings before compute; no subprocess or GPU.
The logical cap includes imports, setup, interaction, optimization, evaluation and publication.
Check its deadline between environment steps and optimizer steps, before evaluation and final
publication. Keep raw rows incrementally readable. A cutoff/error retains actual counts, partial
raw rows and a best-effort final summary; do not update on an incomplete rollout, fill missing
outputs, retry, resume or append another arm's budget. An indivisible operation can cross a clock
boundary; report the actual elapsed wall and TIME_LIMIT rather than asserting an on-time complete
run. Short in-process stop checks implement the selected cap, not a new monitoring service.

Optional RSS uses the existing platform's standard facility when available (e.g. resource on
Linux); if unavailable on this Windows fixture, report null/resources_unmeasured without installing
psutil or changing validity. Do not add resource telemetry beyond wall and RSS. A future scientific
launch has the external adjacent resource-preflight/agent-task route; do not embed another admission
checker, hash/currentness predicate, lock or provenance gate in this runner.

## 6. Bounded engineering checks and original acceptance commands

Write focused tests for changed behavior and the actual output, not mirrors of arbitrary helpers.
Use exact integer/mask/state-copy checks where the claim is exact and FP32 tolerances as in §3.
Do not require performance gains, all-positive seeds, full-history replay, support census or a new
cost experiment. Research unit checks: <=300s total, excluding the single <=60s runner fixture.
Beyond that fixture, unit checks use at most8 complete H48 environment episodes and at most2
synthetic16-episode PPO rollout updates per invocation of the unit suite. No full study in tests.

Required focused coverage:

1. Host service and information: simultaneous-action ordering; matched endpoint transfer and
   mismatch/ineffective-action nonreward; light/courier old/new script behavior; three-step
   positions/task reset versus48-step terminal; persisted past signals; hidden-field masking,
   missing markers and no current/future courier-action leak. Use constructed short trajectories.
2. Learner:18->64->64->heads shape and26501 parameters; recurrent continuity across round boundaries
   and zero start per episode; GAE terminal/continuing-round cases and clipped-loss arithmetic;
   one synthetic rollout performs exactly16 joint steps with finite gradients and nonzero
   parameter displacement. No normalization, separate-optimizer or whole-history fixtures.
3. Fork/RNG: populate Adam, copy identical-but-independent models/state; CARRY retains all moments
   and step counters, RESET clears all optimizer state only; subsequent mutation cannot affect
   another arm. Named training streams are unaffected by an intervening evaluation draw and
   paired exogenous/permutation streams match despite separate arm objects. Do not demand equal
   endogenous actions or cross-platform bitwise learner output.
4. Publication/deadline: compute full primary from raw training returns, not selected evaluation;
   count shared q0 once; retain negative/zero differences; partial Q gives a null full-window primary; incomplete updates/evaluation gives false scientific
   completeness while independently complete native windows remain visible. Preserve actual counts. A fake
   clock/finite stub checks cutoff behavior without waiting for a real timeout or running B01.

One end-to-end runner fixture uses the **same implementation and scientific hyperparameters**,
seed17, P16, Q16 per arm, E4, post-update checkpoint q=(16,), wall cap60 seconds. H48, the sixteen
service rounds, architecture, complete-episode minibatches and16 updates/rollout remain unchanged.
It should complete48 training episodes/48 Adam steps and16 evaluation episodes, i.e.3072 joint
steps. It is not a science result, baseline qualification, host search or a timing projection for
B01. Run once for unchanged code; repeat only after a concrete failed check or source correction,
retain all attempts in the arm's evidence and stay in the same engineering time budget.

Run these original commands from the assigned isolated checkout in PowerShell. They have the same
relative output paths in every isolated arm; do not point them into the shared authoring worktree.

```powershell
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q -p no:cacheprovider --basetemp temp/directions/vsp_02/test/tpc_b01_pytest tests/experiments/candidates/vsp_02/teammate_policy_change_b01/
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe scripts/run_vsp02_teammate_policy_change_b01.py --engineering-fixture --seed 17 --out temp/directions/vsp_02/test/tpc_b01_fixture
& C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -c "import csv,json,math; from pathlib import Path; p=Path('temp/directions/vsp_02/test/tpc_b01_fixture'); s=json.loads((p/'summary.json').read_text()); rows=list(csv.DictReader((p/'training_returns.csv').open(newline=''))); ev=list(csv.DictReader((p/'evaluation_returns.csv').open(newline=''))); c=s['counts']['total']; assert s['run_kind']=='ENGINEERING_FIXTURE' and s['status']=='COMPLETE' and s['scientific_comparison_complete'] is False; assert (c['training_episodes'],c['training_joint_steps'],c['optimizer_steps'],c['evaluation_episodes'],c['evaluation_joint_steps'])==(48,2304,48,16,768); assert len(rows)==48 and len(ev)==16; a={k:[float(r['return']) for r in rows if r['phase']=='adaptation' and r['arm']==k] for k in ('CARRY','RESET')}; assert all(len(v)==16 for v in a.values()); expected=sum(a['RESET'])/16-sum(a['CARRY'])/16; assert math.isclose(s['primary']['delta_reset_minus_carry'],expected,rel_tol=1e-6,abs_tol=1e-6); assert (p/'curves.png').is_file(); print('bounded fixture counts and raw-return primary verified')"
git diff --check
```

The runner's stable summary key `counts.total` uses the five count names in that readback command.
`training_episodes` and `evaluation_episodes` count completed full H48 episodes; add separate
`*_episodes_started` counts when partial episodes exist. Joint-step counts include every actually
executed partial step; optimizer_steps counts actual Adam.step calls. Phase/arm detail uses the same
units and may have additional explicit keys. `primary.delta_reset_minus_carry` is required.
The CSV `return`, `phase` and `arm` labels above are exact interfaces; remaining column names follow
§5 clearly. Record actual elapsed checks, output paths, every failure/correction and any missing
measurement in the arm return. A mere successful process exit is not acceptance.

Do **not** invoke the runner without --engineering-fixture during this engineering assignment.
The future scientific command will be a separately allocated detached exact-SHA invocation with
adjacent resource admission on the configured node; no such command is released here.

## 7. Budget, source reuse and common stop

Common initial engineering limit:3600 seconds per arm under the Root comparison protocol.
Research source additions (the new package plus runner) <=2000 lines, excluding tests/docs;
runner <=600. Orchestration30% is a review signal, not an automatic rejection threshold. Report
actual added-source/runner/test line counts without gaming file boundaries or compressing code.
Required ordinary checks are as above. Stop at the common task limit or return a concrete
scientific/implementation conflict; do not substitute a different design or silently relax a check.
No automatic new revision budget follows the first return; Root retains first-return evidence
and uses the same agents/sessions for an explicitly assigned correction.

Engineering-scope §4 machinery required by B01: none. The owner-authorized comparison capture and
headless clients remain Root's existing control-plane tooling, outside this implementation diff.
No new source/test framework, compatibility shim, retry/resume, registries, hash/tamper evidence,
background worker, GPU, parameter search or telemetry framework. The later production integration
changes only the accepted implementation plus normal evidence, not all five alternative arms.

The bounded adapter check used the scientific-tools adapters route. Verified fixed source pointers:

- `C:/Projects/ref-lib/on-policy`, commit `de66d7a4b23fac2513f56f96f73b3f5cb96695ac`,
  `onpolicy/algorithms/r_mappo/r_mappo.py` ppo_update/train (policy ratio/clipping and per-epoch
  minibatches), and `onpolicy/utils/shared_buffer.py` compute_returns (GAE recursion).
- That source's `algorithm/rMAPPOPolicy.py` creates **separate** actor/critic networks and Adam
  optimizers, with a centralized-critic input path. It cannot be imported wholesale for the
  selected shared64/64 representation and one-Adam fork.
- `C:/Projects/ref-lib/epymarl`, commit `cbc38c09588064eab978501d0f12c2cf58fa7fc2`,
  `src/learners/ppo_learner.py` initializer/train also has separate optimizers, a target critic
  and optional reward/return normalization. It is not the selected learner.
- HMASD `hmasd/r_mappo_utils.py` RNNLayer adds LayerNorm and alternate sequence machinery;
  the DISH recurrent trainer uses different policy/state and normalization paths. The old VSP02
  oracle-sign objects also do not implement this ordinary PPO comparator.

Therefore reuse torch's fixed GRU/distribution/Adam implementations and the standard formulas
specified here, without importing/vendoring either full trainer or changing shared code. No upstream
file must be reread to complete this self-contained contract; exact source pointers are explanatory,
not additional acceptance or launch obligations. Prior P11 literature retrieval remains the
scientific basis for equal legal history and supplies no Adam-reset result or novelty claim.
