# HA-CTSE Implementation Plan

Purpose: staged core-algorithm work only. The binding research target, S7-S1
parity definition, baseline hierarchy, promotion ladder, and failure-review gate
live in `memory/ALGORITHM_PRINCIPLES.md`; they are not repeated here.

## R39 S7 Compatibility Boundary

R38 completed as a valid `FAIL_R38_CTS_ACCESS`; its replacement environment and
ordinary-MAPPO access route are retired. The accepted structural direction is
to return to S7 and compare current fixed-`k` HMASD with a same-substrate
per-agent KEEP/SET treatment. Environment-specific intrinsic reward remains
prohibited.

The GPT-5.6 Pro follow-up is accepted with controller closures in
`docs/external-review/gpt5_6_pro/20260715_r38_cts_access_result/`.
The only positive historical checkpoint was saved at 1.760M on the former
six-agent, three-action S7 stack; it remains reference-only. Current S7 uses the
eight-agent, four-action interface-v3 contract, and standalone R30 is not the
HMASD coordinator/trainer.

The user selected a lightweight synthetic mechanism gate before paying the S7
compute cost. This does not alter the accepted serial S7 route or implement
native-HMASD R39B. The completed standalone stage-0 diagnostic sequence used:

1. two agents receive identical constant local observations while centralized
   high context exposes one slow and one fast action target;
2. the shared dense external reward is invariant to swapping agent roles;
3. a single categorical final-skill action maps the incumbent to `KEEP` in the
   adaptive arm and maps every draw to `SET`, including the incumbent, in the
   full-refresh control;
4. both arms use the same 32-wide feedforward low policy and 16-dimensional
   compact/team representations, with every intrinsic and process auxiliary
   objective disabled;
5. the paired 12.8K-step run is the implementation and mechanism check.

First-run disposition: invalid `INVALID_R39_TOY_LOW_PPO`. The feedforward
learner crossed interleaved environments when computing returns, ignored the
registered three PPO epochs, and used a clipped-Normal likelihood that did not
describe executed actions. Its match and lifetime outcomes are not evidence.
The repair uses env-grouped bootstrapped GAE, three PPO epochs, and a
tanh-squashed Gaussian while retaining the 32-wide model and original compute
budget. Its valid rerun still failed dense access: adaptive/control match was
`0.445716/0.445838`, with all slow/fast components below `0.46`. The next toy
boundary therefore removes low learning entirely: four fixed axis primitives,
zero low parameters or optimizer steps, and the same 32-wide high stack. This
is only a high-controller positive control; it cannot establish skill discovery.

GPT-5.6 Pro subsequently accepted the controller's sequencing disposition. The
native-HMASD fixed-`N` positive credit anchor on the same
`two_timescale_role_free_actions` substrate froze two agents,
`n_Z=n_z=4`, `k0=5`, episode/rollout 40, high hidden 32, 16 environments, 12,800
steps, 20 outer updates, three high PPO epochs, seed 39041, 32 stochastic final
evaluations, zero trainable low parameters, and zero intrinsic reward. Sampling
and replay use the stored `Z,z_{<i}` chain and native team/agent values,
advantages, and ratios. The result owner is one
`result/r39_native_hmasd_toy_credit.json`.

The gate completed as valid `VALID_FAIL_R39_NATIVE_TOY_CREDIT_ANCHOR`: M0 passed
with 20/20 outer updates, 60 high optimizer updates, replay error
`4.76837158203125e-7`, and zero low/discriminator updates, while
match/slow/fast were `0.455078125/0.46484375/0.4453125`. Retire this native
GAE/PPO credit route without rescue. The active boundary is now one fixed-`N`
joint-credit failure review that must select a structurally different causal
edge before any open-roster implementation or new compute.

The preserved R39A package boundary is:

1. native HMASD PPO teacher-forces stored `Z,z_{<i}`;
2. coordinator encoder/decoder dropout is zero so the stored joint action has
   one replayable conditional likelihood while categorical sampling remains
   stochastic;
3. one strict 1.6M-step/100-update CUDA runner trains from scratch and one
   independent stochastic evaluator owns the registered 100-episode decision;
4. launch is deferred until the toy gate reaches its registered result.

R39B remains unimplemented in native HMASD. Only a toy mechanism PASS followed
by `PASS_R39A_CURRENT_FIXED_HMASD_ANCHOR` may authorize its S7 implementation
and 320K matched temporal gate.

Do not partially load the old checkpoint, cross into the standalone R30 trainer,
or invent an experiment result before the source anchor and team-`Z` semantics
are closed.

## R37 Actor-Visible Task-Identity Access Gate

Active causal edge:

```text
actor-visible current task identity
-> removal of the hidden-information bottleneck
-> positive sparse collection access under constant-code recurrent MAPPO
```

Authorized by the valid R35--R36 access failures and accepted from GPT-5.6 Pro
with the capacity-matched control clarification in
`docs/external-review/gpt5_6_pro/20260715_r36_aem_access_result/DISPOSITION.md`.
R36 itself is retired: it expanded coarse joint-position coverage `3.8552x`
without one collection or successful cycle.

One coherent implementation/evidence boundary:

1. Reuse the R35 constant-code recurrent MAPPO actor and centralized critic.
   Add no skill, high policy, latent, classifier, intrinsic reward, shaping, or
   new optimization path.
2. Give both arms one identical 16-value actor layout: the original 12 values
   followed by two active-plate and two active-target slots. Treatment fills
   the slots with current true one-hots; control fills them with zeros. The
   existing 19-value centralized critic state is unchanged.
3. Keep the external reward collection-only. Do not expose clocks, contacts,
   collection/progress state, reward-derived fields, future state, distance, or
   oracle actions to either actor.
4. Compare the two trained arms from one common neutral zero-step
   initialization using seed `38031`, concurrent local CUDA, 16 environments
   per arm, rollout 80, 320,000 steps, 250 low updates, five PPO epochs,
   recurrent sequence length 10/batch 64, and 64 paired stochastic episodes.
5. The registered M0--M3 access gate in `memory/ExpRecord.md` is also the
   implementation check. Do not insert a smoke, identity ablation menu,
   threshold change, retuning, seed expansion, or longer budget.

This is an environment/access-instrument repair, not an algorithm contribution.
PASS establishes only a positive access floor under the repaired observation
contract. FAIL retires sparse Alice--Bob as the current algorithm-comparison
gate.

Result boundary complete: R37 is a valid `FAIL_R37_ACCESS`. Current-task
identity caused nonzero access but cycle success `0.01953125` remained below the
registered `0.05` floor. Retire this environment as an algorithm gate. No new
core implementation begins until one replacement benchmark/access contract is
selected and registered.

## R30 Fixed-Clock Autoregressive Edit Gate

Active causal edge:

```text
fixed global check clock k0
-> complete all-agent autoregressive KEEP/SET action
-> lifetime learned by KEEP survival without duration shortcut
```

Accepted design:
`docs/research/R30_FIXED_CLOCK_AR_EDIT_DESIGN_20260714.md`.

One coherent implementation boundary:

1. Replace the active duration head with separate keep and conditional
   switch-skill heads. Mask initial `KEEP` and normal `SET(current_skill)`.
2. At every `k0` check, give every agent one token in a stored order. Apply each
   token immediately to the working roster before evaluating the next agent.
3. Move high PPO from completed variable segments to a fixed-check buffer with
   per-environment check-sequence GAE, one prefix-independent scalar critic,
   and one shared block advantage. Re-evaluate stored token sequences with
   applied-roster teacher forcing and one combined ratio per executed token.
4. Keep process segments independent of the high buffer: `KEEP` continues the
   active segment; `SET` closes and opens it; process records never train the
   high controller.
5. Remove duration candidates, duration entropy floors, edit/switch penalties,
   forced maximum age, and lifetime rewards from the active mode. Initialize
   `p_keep=0.6` for the current `{1,2,3,4}`-block source.
6. Preserve `pi_l(a_i | o_i, z_i)`. Do not add a semantic reward in this
   implementation; retain only the fixed, duration-blind `W=k0` interface for
   the later realized-effect target.
7. Use deterministic expected bridge context, a per-environment
   `steps_to_check` clock, and actor-invalid continuation rows across PPO update
   boundaries. Preserve skills, ages, clock, and low recurrent state.
8. Load R30 checkpoints through an explicit versioned migration: reuse only
   compatible representation/low-policy/high-actor parameters and reinitialize
   keep head, high critic, high ValueNorm, high optimizer, clocks, and buffers.

The evidence-bearing check after implementation is one reward-pure,
mechanism-matched short comparison at approximately 320K transitions per arm,
16 environments, CUDA, seed 30031. It reads only: token/replay validity,
lifetime breadth, asynchronous switch-skill supply, and immediate task safety.
It does not add a duration sweep, team mechanism, or semantic reward.

Implementation status: complete. The next boundary is the registered paired
run in `memory/ExpRecord.md`; implementation and experiment are not separated
by another validation stage.

## R31 Natural-Window Causal Fixed-Window Effect Information

Active causal edge:

```text
natural on-policy prefix
-> persistent skill intervention under policy-matched stochastic execution
-> task-generic realized environment-effect separation
```

Accepted design source:
`docs/external-review/gpt5_6_pro/20260714_r30_sparse_exploration_review/RESPONSE_RAW.md`.
Controller disposition: `DISPOSITION.md` in the same directory.

R28 completed boundary:

- a separate default-off low-level reward module using frozen scorer/source
  continuity, exact same-forward deterministic-action evidence, natural clocks,
  common support, sham derangement, terminal-ten-step attribution, and
  fail-closed OOD/reward-ratio guards;
- checkpoint and CLI integration, R26 sidecar/export, family analyzer, and
  focused tests;
- explicit non-resumable tagging for engineering-smoke checkpoints.
- two exact one-update engineering smokes plus support-distance diagnostics;
  both support kills occurred before any R28 reward application;
- a feature-construction audit confirming shared feature code, action transform,
  duration mapping, source identity, and support-distance semantics.
- a separate paired transport sidecar that holds checkpoint, prefix, forced
  skill, scorer, and features fixed while changing only deterministic versus
  six-agent stochastic environment execution; no R27 artifact semantics were
  changed;
- reset-0 local CUDA smoke: 16 paired windows, deterministic OOD `0.0625`,
  stochastic OOD `1.0`, with the same temporal-standard-deviation shift.
- 64-reset decision: `FAIL_STOCHASTIC_SUPPORT_TRANSPORT`; deterministic OOD
  `0.068359`, stochastic OOD `0.823242`, and 64 rows in every label-duration
  cell. Random action execution is sufficient to break the frozen support.

R29 completed boundary:

1. R29-G0 passed the three-checkpoint reward-off gate. The natural on-policy
   action-information target is positive against the cyclic sham and the
   inactive-FiLM control is numerical zero.
2. External review modified R29-G1 into R29-T10. For each complete natural skill
   lifetime, the collection actor is replayed from the stored pre-step hidden
   state under each fixed candidate skill. The uniform density ratio uses the
   final 10 action likelihoods, then adds one detached clipped reward at the
   lifetime endpoint. Length-batched replay keeps this tractable on GPU; the
   actual-skill column is anchored to PPO's stored old likelihood after removing
   the common tanh Jacobian, while cross-skill columns follow full replay. This
   avoids CUDA GRU batch-shape drift without weakening the source likelihood.
3. The authorized single-seed `probe_only` versus `real_reward` pair completed
   at +320K steps per arm. Implementation was valid, but the score, R26
   transfer, and task-safety gates failed.
4. GPT-5.6 Pro returned `RETIRE`; the disposition and failure review accepted
   R29 as diagnostic-only and retired the online actor-density-ratio family.

Completed R31 boundary:

1. Keep R30 unchanged. Each genuine post-edit check opens one complete natural
   stochastic window per agent with fixed `W=k0`; incomplete terminal/update
   windows are invalid.
2. Alice--Bob effect input is normalized joint agent positions only. Build a
   focal/teammate endpoint and late-half displacement effect, conditioned on
   start positions and teammate skills. Exclude action, task reward, task
   identity, button/target/contact/phase, age, length, agent ID, and OPT compact.
3. Train a full effect posterior and context-only posterior on natural windows.
   Use signed `log q_full - log q_context`; matched shuffle is gate-only.
4. Score a rollout with the posterior frozen after the previous rollout, inject
   no reward in `probe_only`, run low PPO, then update the posterior from the
   detached natural windows. A later `real_reward` mode may inject one detached
   signed clipped endpoint reward per fixed block; it never enters R30 high
   return.
5. Keep the one-step transition discriminator as legacy diagnostic-only and
   fail closed if its reward, R28/R29 reward, environment shaping, wrong window
   length, forbidden input, incomplete-window reward, or high reward injection
   is active in R31 mode.
6. Implement a reward-off forced stochastic audit from matched simulator/RNG/
   recurrent-state contexts. Teammates resample their policy under common random
   numbers rather than replaying an action tape. Forced windows never train the
   natural scorer.
7. Only a reward-off PASS authorizes the registered 160K paired R31 reward
   comparison. FAIL retires CFEI; UNDERPOWERED adds only the same reset batch.

Core MARL impact: R31 reconstructs only the individual persistent-effect half
of HMASD's intrinsic exploration loop. It does not establish team composition,
delayed cooperative credit, sparse-task improvement, asynchronous-lifetime
benefit, or HMASD parity.

Gate result: valid `FAIL`. Natural heldout information was positive, but the
direct forced-skill between/within ratio was below one. The old absolute
near-zero matched-shuffle null was invalid and is no longer a failure reason;
the direct M2 independently retires R31-CFEI and its conditional reward pair.

## R32 Interventional Fixed-Window Effect Policy Gradient

Active causal edge:

```text
randomized focal-skill intervention
-> noise-corrected persistent effect separation
-> skill-FiLM-only actor change
-> natural joint-state coverage
```

Accepted design source: the raw `VALID FAIL / R32-IFEPG` response under
`docs/external-review/gpt5_6_pro/20260714_r31_cfei_gate_result/`.

One coherent implementation and evidence boundary:

1. From natural adaptive-R30 decision snapshots, force every focal skill for
   two independent stochastic `W=k0=10` replicas. Freeze the teammate behavior
   actor at each auxiliary round and keep teammate skills fixed.
2. Compute the signed cross-replica U-statistic over the existing eight-value
   normalized-position effect and average across six skill pairs and eight
   effect dimensions. Do not rectify negative scores.
3. Standardize each context score against a leave-one-context baseline and use
   it in one focal-action PPO-clipped surrogate epoch (`clip=0.10`, gradient
   clip `0.5`). Use the existing low actor learning rate `3e-4`, because the
   external contract introduced no separate auxiliary learning rate.
4. Train only `low.actor_film`; freeze actor base/RNN/action head/log standard
   deviation, critic, R30 high controller, OPT/bridge, and all posterior paths.
   No reward, value loss, GAE, entropy objective, task return, or high update
   enters the auxiliary step.
5. Keep R32 out of the normal trainer. The paired gate compares no-step
   `probe_only` with `real_update` from the same frozen R30 checkpoint and
   source context bank: 20 x 32 training contexts, 128 heldout contexts, four
   skills, two replicas, and one seed `32031`.
6. M0 checks exact branch counts, focal replay likelihood, FiLM/non-FiLM drift,
   and forbidden updates. M1 requires heldout causal SNR improvement; M2
   requires increased between-skill effect without within-skill noise growth;
   M3 requires natural 625-cell coverage transport while preserving R30
   lifetime and switch-skill supply.
7. M0 failure is implementation-invalid and permits only repair. Any valid
   M1--M3 failure retires direct IFEPG with no tuning or UNDERPOWERED branch.
   PASS authorizes only later production integration from a genuinely sparse,
   unshaped R30 source.

Core MARL impact: effect tensors are `[context, skill, replica, 8]`; actor
likelihood replay is `[context, skill, replica, W]`. Old behavior likelihoods,
effect scores, and standardized advantages are detached. The only gradient path
is current focal log-probability -> frozen actor stack -> skill FiLM. Natural
R30 clocks, masks, skill rosters, high returns, collectors, and checkpoint
format remain unchanged.

Gate result: valid `FAIL_M1_RETIRE_R32_IFEPG`. M0 passed, including exact
branch counts, maximum replay error `4.77e-6`, positive finite FiLM drift, zero
non-FiLM drift/gradient escape, and zero forbidden updates. The real causal
ratio reached only `1.015540` (CI `[0.877865, 1.207808]`), paired gain was
`0.028746` rather than `0.40`, and skills 0/1 remained below pooled ratio one.
Between-effect growth was `1.029965x` with unchanged within noise; natural
coverage grew only `1.012821x` with a paired CI crossing zero. R30 lifetime and
switch-skill safety passed. Retire direct IFEPG and all learning-rate,
update-count, window, replica, effect, threshold, seed, or scope variants.

Next boundary: external review must choose exactly one structurally different
R33 edge and its smallest Alice--Bob abandonment gate. It must explicitly
decide whether the individual-effect line is exhausted and complementary team
composition is now the missing causal level. Do not implement another R32
rescue or normal-trainer path.

## R33 Interventional Role-Swap Complementarity

Active causal edge:

```text
natural R30 context
-> randomized complete-roster effects
-> non-additive stable role-swap complementarity
-> exact high-level complementary-roster selection
-> natural joint and role-free coverage
```

The raw GPT-5.6 Pro review selected complete-roster composition. Controller
disposition is `MODIFY` because its original contrast was also large for
independently executed skills. For each agent and replica, R33 double-centers
the complete `4 x 4` effect table over both roster axes, then scores the
antisymmetric role-swap component minus the symmetric orientation component.
This removes agent/skill additive main effects and rejects one-sided pair
effects.

One implementation/evidence boundary:

1. Collect 16 complete final rosters, two independent replicas, and `W=10`
   stochastic steps from each natural R30 context. The branch-effect tensor is
   `[context,4,4,2,2,4]`; intervention trajectories are shared by both arms.
2. Compare `real_complementarity` with the fixed pair-permutation `pair_sham`.
   Their per-context roster-score multisets are identical.
3. Teacher-force all 16 KEEP/SET sequences through the existing R30
   `evaluate_sequence` and minimize the exact expectation of the detached
   standardized score. The roster-probability tensor is `[context,16]`.
4. Gradient enters only `FixedClockAREditPolicy.skill_head`. Keep the low
   actor, KEEP head/shared trunk, critics, OPT/bridge, posteriors, environment,
   reward, GAE, and normal high PPO frozen/outside the objective.
5. Add only
   `ha_ctse_process/r33_interventional_roster_complementarity.py` and
   `scripts/r33_roster_complementarity_gate.py` before the mechanism result.
   Do not modify the normal controller, trainer, or Alice--Bob environment.

The exact budget, thresholds, null, validity rules, and abandonment branches
are owned by `memory/ExpRecord.md`.

Gate result: valid `FAIL_M1_RETIRE_R33_IRSC`. M0 passed with exact roster
probabilities, score-multiset parity, finite head-only gradients and zero
non-head drift. Real mapping produced only `0.001955` heldout expected-score
gain and `0.001250` correct-top-two-pair mass gain; both were positive but two
orders of magnitude below their gates. Natural joint and nonredundant coverage
were slightly below pair-sham while R30 lifetime and skill supply remained
healthy. Retire direct intervention-scored roster-complementarity selection;
do not tune or integrate it.

## R34 Balanced Hindsight Mode Distillation

Active causal edge:

```text
unlabeled natural focal trajectories
-> balanced hindsight mode labels
-> full-episode recurrent low-actor distillation
-> intervention-reproducible numerical skills
-> frozen-R30 natural use
-> joint-state coverage transport
```

The two GPT-5.6 Pro responses selected the same route. Controller disposition
is `MODIFY`: response B's full-episode replay supersedes stale block-start
hidden replay; a frozen-source anchor prevents sham damage from masquerading as
mode creation; focal-only displacement labels keep the target controllable by
the focal skill; and mode formation, zero-shot selector use, and coverage are
separate result branches.

One implementation/evidence boundary:

1. Add only `ha_ctse_process/r34_balanced_hindsight_mode_distillation.py` and
   `scripts/r34_bhmd_gate.py` before the gate result.
2. Fit exact-balanced four-mode prototypes on train-only focal displacement
   sequences, then align their names to old numerical skills only for R30
   interface compatibility.
3. Compare `real_modes` and a maximum-Hamming episode-sequence sham from paired
   initial actors, with the unchanged source as a no-update anchor.
4. Replay complete 80-step source episodes from zero hidden and update only
   low actor FiLM, recurrent layers, and action mean. Recompute current prefix
   hidden for every heldout forced block.
5. Keep the normal trainer, R30 controller, environment, rewards, critics,
   OPT/bridge, and posteriors unchanged. The exact budget and decision contract
   are owned by `memory/ExpRecord.md`.

Gate result: valid `FAIL_M1_RETIRE_R34_BHMD`. All M0 checks passed and the
maximum-Hamming sham was strongly disrupted. Real distillation raised forced
fidelity only `0.0654` over the frozen source, below the registered `0.15`
gain, while persistent-mode SNR fell from `1.7608` to `1.5235`
(`real-source=-0.2962`, wholly negative CI). Natural mode agreement improved
only `0.0488`, and joint coverage did not improve over source under the paired
reset statistic. R30 safety passed. Retire fixed balanced hindsight mode
distillation and do not tune or integrate it; the next implementation boundary
must come from one structurally different post-R34 causal edge.

## R35 Sparse MAPPO Reset Baseline

Active causal question:

```text
matched sparse-reward low-level optimization
-> observation/history-only recurrent MAPPO versus active R30 skill editing
-> Alice--Bob task access and paired noninferiority
-> decide the optimization baseline, not a new paper contribution
```

The final GPT-5.6 Pro response correctly closes R35-OCSF, CBF, and TMPF and
selects a no-skill reset. Its trained-versus-frozen comparison is invalid, so
the controller accepts one modified pair:

1. Construct one neutral zero-step R30 checkpoint and load it into both arms.
2. `constant_code_mappo` keeps the existing four-column low FiLM and recurrent
   centralized critic shapes, but supplies dummy skill/team code zero at every
   step. It never executes or updates the high editor. Constant conditioning
   makes its behavior observation/history-only while preserving low capacity.
3. `reward_pure_r30` trains the same low stack and its KEEP/SET high editor.
   Both arms receive only the sparse Alice--Bob collection reward.
4. Match low rollout, recurrent minibatch, PPO epoch, actor/critic optimizer,
   environment-step, reset, and evaluation exposure. Report R30's additional
   high optimizer steps as the treatment rather than calling total optimizer
   exposure matched.
5. Add only the episode-level 625-cell joint-position coverage and zero-cycle
   flag required by the gate. Do not add a classifier, intrinsic reward, OPT
   actor input, new scheduler, or trained-checkpoint migration.

The exact budget, access floor, noninferiority margins, outcome branches, and
single result source are owned by `memory/ExpRecord.md`.

## Legacy Compatibility Boundary

- This branch is for constructing the new HA-CTSE/process algorithm, not for
  conservative HMASD maintenance.
- Keep old `hmasd`/`hmasd_original` runnable only as comparison baselines when
  doing so does not block the new algorithm.
- Do not keep fixed-k HMASD data-flow assumptions inside the HA-CTSE core just
  to preserve old behavior.
- Preserve archived `_server_package_*` folders by not editing them.

## Ruled Out / Stop Rules

- Segment posterior `q(z | S, g)`, context-residual posterior, and
  future-cooperation outcome residual probes repeatedly failed to beat
  shortcut/context baselines as reliable positive intrinsic rewards. Keep them
  diagnostic-only unless a new run pre-commits a falsification metric.
- Topology-role discrimination is the final classifier-style semantic probe in
  this family. If its full classifier does not sustainably beat the
  OPT/context/duration shortcut, stop adding new residual-discriminator heads.
- Duration-only shortcut is now a hard gate for segment-posterior intrinsic
  reward: if duration-only accuracy is not worse than posterior accuracy by the
  configured margin, segment posterior reward is zeroed before it can affect
  either high or low policy updates.
- Process reward with magnitude far below environment reward remains
  diagnostic-only unless explicitly changed to a centered/advantage-style
  shaping mode.
- Detached same-action actor-density ratios are diagnostic-only. Do not create
  online variants by changing their prior, window, aggregation, coefficient,
  normalization, or clip.


## Archived Plan History

Completed R22/R24/R26/R27 implementation detail is preserved by the frozen
designs, `memory/LTM/IMPLEMENTATION_PLAN_ARCHIVE_20260713.md`, and
`memory/LTM/EXPERIMENT_ARCHIVE.md`. Older completed/superseded rounds are in the
same plan archive. Read them only when this plan points there or the user asks
for history.
