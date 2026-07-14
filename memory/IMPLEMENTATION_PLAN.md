# HA-CTSE Implementation Plan

Purpose: staged core-algorithm work only. The binding research target, S7-S1
parity definition, baseline hierarchy, promotion ladder, and failure-review gate
live in `memory/ALGORITHM_PRINCIPLES.md`; they are not repeated here.

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

Active R31 boundary:

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
