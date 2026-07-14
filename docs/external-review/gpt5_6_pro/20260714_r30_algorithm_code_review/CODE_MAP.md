# R30 Code Review Map

Target commit: `f62baf626f6f37903b3929c4732952f95d2bc2ab`

Line numbers are orientation aids. Use class/function names as the stable
anchors.

## Primary HA-CTSE Implementation

### `ha_ctse_process/standalone_agent.py`

- `HighActionSample`, approximately lines 905-918: current sampled
  skill/duration parts.
- `SkillDurationPolicy`, approximately lines 920-1158: shared token trunk,
  independent skill and duration heads, value head, act/evaluate, and entropy.
  Note that the value uses features containing `ar_prefix`.
- `Segment` and `SegmentManager`, approximately lines 1190-1518: variable
  low-level process record, renewal semantics, rollout indices, high sample
  fields, and boundary flushes.
- `StandaloneProcessAgent.__init__`, approximately lines 1540-1950: duration
  candidates, autoregressive mode, entropy floors, penalties, compact encoder,
  high policy construction, and optimizers.
- `reset_env_state` / `reset_all_policy_state`, approximately lines 2623-2690:
  episode and policy-update invalidation.
- `_build_roster_ar_prefix` and reconstruction helpers, approximately lines
  2726-2832: current roster/age prefix representation and duration-dependent age
  scale.
- `maybe_assign_skills`, approximately lines 2890-3290: expired-agent detection,
  context construction, sparse autoregressive loop, duration sampling,
  countdown mutation, segment renewal, and per-step age/countdown ticking.
- `process_update`, approximately lines 4838-5900: completed-segment ownership,
  auxiliary/reward paths, low reward injection, and the call that currently
  updates high PPO from segments.
- `update_high_from_segments`, approximately lines 6333-6710: high policy/value
  recomputation, SMDP returns, PPO ratio, entropy floors, and optimizer update.

Primary question: identify the smallest clean split between a new fixed-check
high buffer/update and the retained variable process-segment path. Do not patch
the old segment high fields into a fake all-agent check batch.

### `ha_ctse_process/train.py`

- CLI/config fields around lines 480-910 and 1150-1200: `skill_interval`,
  lifetime candidates, entropy floors, penalties, and autoregressive flags.
- checkpoint save/load and metadata around lines 1390-1850: duration/source
  identity and state restoration.
- R28/R29 locked validators around lines 1900-2250: historical paths that R30
  must not accidentally reactivate.
- main collector loop around lines 3460-3575: interleaved `rollout_idx` passed to
  `maybe_assign_skills`, environment step collection, segment append, episode
  reset, and update flush.
- post-update policy-state reset around line 3965.

Primary question: define the per-environment `k0` clock, high-block close path,
and update-boundary handling without using interleaved global rollout indices
as time.

### `ha_ctse_process/config.py`

- early high-policy and duration defaults around lines 20-60;
- entropy defaults around lines 145-165;
- edit/switch penalties around lines 375-385.

Primary question: which fields disappear from active R30 mode, which remain
only for the frozen legacy comparator, and what new configuration is genuinely
necessary.

## HMASD / OPT Reference Code

### `hmasd/networks.py`

- `OPT`, approximately lines 168-300: interaction-prototype implementation.
- `SkillCoordinator`, approximately lines 702-940: original team skill plus
  autoregressive individual skill chain and training evaluation.
- low recurrent actor/critic paths around lines 1150-1460.

Use this to assess what HMASD-style sequential assignment and low-level skill
conditioning should be retained. Do not copy its synchronized lifetime or old
discriminator reward blindly.

### `hmasd/ha_ctse.py`

- `OPTCompactExtractor`, approximately lines 51-120.
- `HorizonSkillEditor`, approximately lines 284-815, especially
  `_assign_autoregressive_from_features`, `assign_and_value_batch`, and
  `evaluate_training_batch`.

This is an earlier integrated horizon editor with termination, skill, and
duration paths. It is reference/provenance, not the active standalone core.

### `hmasd/agent.py`

- duration-aware batched assignment around lines 1769-1992;
- pending high-level sample closure around lines 2469-2646;
- high-level advantage/update entry around lines 3667 onward.

Review only where useful for identifying already-solved buffer or checkpoint
issues. The implementation target remains `ha_ctse_process`.

## Algorithm And Evidence Contracts

- `docs/research/R30_FIXED_CLOCK_AR_EDIT_DESIGN_20260714.md`: proposed R30.
- `memory/ALGORITHM_PRINCIPLES.md`: binding causal and algorithm constraints.
- `memory/IMPLEMENTATION_PLAN.md`: accepted implementation boundary.
- `memory/LTM/R29_ACTOR_DENSITY_RATIO_FAILURE_REVIEW_20260714.md`: why the
  semantic reward cannot be bundled into R30.
- `docs/external-review/gpt5_6_pro/20260714_fixed_clock_keep_set/DISPOSITION.md`:
  prior response disposition and controller modifications.
