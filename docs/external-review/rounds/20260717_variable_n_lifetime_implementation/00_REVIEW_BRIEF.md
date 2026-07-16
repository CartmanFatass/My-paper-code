# Variable-N + Variable-Lifetime Implementation Review Brief

## Purpose

This is the second round of the blind dual-divergent review workflow. The first
round closed the architecture contract and retained only:

- `F0`: Active-Set Scheduled Recurrent MARL, the ordinary-MARL baseline;
- `F1`: Exchangeable Exogenous-Opportunity Event-Frontier Commitment Editor;
- learned event time, deferred.

This round reviews the resulting implementation plan against the actual HMASD
codebase. It is not an invitation to reopen the portfolio, invent a new
experiment, add modules or tune a gate.

Gemini and an open GPT-5.6 Pro conversation review independently. Neither sees
the other's current response. Codex compares both raw reviews before the
existing GPT-5.6 Pro consultation conversation issues one convergent plan
disposition.

## Frozen causal distinction

F0 and F1 must use the same lifecycle table, opportunity schedule, collector,
ragged packing, model graph, parameter count, low policy, critic, event credit,
PPO update, checkpoint and data exposure. Their only intervention is:

```text
F0 decoder context = g(initial active commitment set)
F1 decoder context = g(current applied-prefix commitment set)
```

F1 is scientifically distinct only when an earlier applied edit changes a
later token's relative learned scores on common legal support. Mask-only
serialization is F0.

## Proposed implementation boundary

The plan proposes:

1. one new production core, `ha_ctse_process/variable_roster_event.py`;
2. default-off dispatch through the existing `StandaloneProcessAgent` and
   `train_loop` rather than a second trainer;
3. active-only flat member tensors with environment/event offsets and routing
   keys kept outside model inputs;
4. a policy-independent per-member bounded renewal opportunity schedule with
   integer gaps 1--19 and mean 10 active steps;
5. a native K-way commitment action where the incumbent channel means `KEEP`;
6. a shared sum/count encoder and recurrent per-member commitment policy;
7. member-owned `gamma^Delta` event returns and same-owner macro GAE;
8. the existing skill-conditioned low actor interface with a variable-N
   active-set critic in the new path;
9. strict schema-3 resume including lifecycle records, open event traces and
   both RNG streams;
10. focused engineering checks only, followed by a stop before any environment
    or training launch.

## Actual repository constraints

- `FixedClockAREditPolicy` already implements a native categorical KEEP/SET
  mapping and teacher-forced applied-roster replay, but its roster encoding and
  buffers have fixed `n_agents` shapes.
- `StandaloneProcessAgent` owns fixed `[num_envs, n_agents, ...]` skill and
  recurrent arrays and a monolithic collection/update surface.
- `StrictHMASDMAPPOLowLevelPolicy` preserves the actor interface
  `pi_low(a_i | o_i, z_i)`, but its centralized critic consumes fixed-shape
  state/team-code assumptions.
- `train_loop` assumes fixed `env.n_uavs`, fixed action arrays and one fixed-N
  rollout shape.
- R49 proved only a synthetic interface fact: identity-free active-set
  encoding, exact random-order replay and applied-prefix gradients are
  implementable. Its code is not a production module.
- Original HMASD and R30 remain runnable comparison paths and must not be
  silently migrated into the event path.

## Non-negotiable constraints

- No permanent member identity, lifecycle key, membership epoch or padded slot
  enters a policy-visible tensor.
- No task-specific intrinsic reward or shaping. Task labels, goals, contacts,
  phases, success predicates, distances and external reward cannot customize
  intrinsic reward.
- No learned event-time hazard, sampled team latent, bridge, fixed slot,
  attention/graph stack, learned order or post-sampling conflict repair.
- F0 cannot receive weaker infrastructure or capacity than F1.
- Existing R30/legacy checkpoint paths remain unchanged. Event schema v1 has no
  implicit migration from them.
- This round may modify the implementation plan, return it to architecture
  design, or stop F1 at F0. It cannot authorize training.

## Decision required

Determine whether the written implementation plan is:

- `ACCEPT_PLAN`: internally complete enough for one staged implementation;
- `MODIFY_PLAN`: viable after a finite list of exact plan corrections;
- `RETURN_TO_ARCHITECTURE`: a correctness question remains unresolved before
  code;
- `STOP_AT_F0`: the only possible F1 dependence is mask-only or requires a
  forbidden asymmetry/module.

The final answer must identify exact file/interface consequences and must not
replace a concrete implementation issue with another isolated gate.
