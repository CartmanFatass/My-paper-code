# HA-CTSE Current Work

Updated: 2026-07-18

## Controller Ownership

- Active controller: Codex root task `019f5c78-0c91-7612-adb4-c1fcfe4484c8`
- Controller status: ACTIVE
- Workspace: `C:\project\HMASD`
- Branch: `aggressive`
- Ownership since: `2026-07-17T18:02:29.8227942+08:00`
- Previous controller: none
- Handoff state: NONE

## Objective

The generic-`SHORT` environment passed Stage A and the direct primitive-AR
carrier passed Stage B. The fresh paired Stage C run from commit `bf933a3` is a
valid terminal `SUPPORT_H2_SKILL_LIMIT` result at
`logs/f0f1_dynamic_roster_stage_c_20260717_221247`.

F1 changed its natural later-token distribution and showed a small forced
skill effect, but neither arm transported skill conditioning into executable
natural behavior or task access. Both final arms have `P/S/U=0/1/0.5`; the
paired F1-minus-F0 utility CI95 is `[0,0,0]`. The current F0/F1 route therefore
stops at an upstream skill-execution bottleneck. It cannot be rescued by
retuning F1, adding a module, or reading the timing branch.

## Causal Portfolio

- **H0 / F0 sufficiency:** rejected on this testbed; F0 has no task access.
- **H1 / F1 applied-prefix value:** conditional distribution response exists,
  but task transport is rejected under the frozen Stage C contract.
- **H2 / skill execution failure:** supported; both arms lack executable
  naturally used skills despite the Stage B carrier.
- **H3 / exogenous timing limitation:** unread because its registered upstream
  prerequisites failed; learned event time remains deferred.

F0 and F1 must share the complete runtime, model, optimization, ledgers and
exposure. Their sole treatment difference is:

```text
F0 -> initial_summary
F1 -> working_summary
```

## Next Actions

1. Count the closed Stage C disposition as overnight iteration 1 of 5.
2. For iteration 2, use the frozen Stage C evidence to distinguish coordinator
   skill supply, low-level skill-conditioned execution, and natural-context
   transport as competing causes of H2. Prefer analysis-only evidence; do not
   add a module or retrain Stage C.
3. Continue only if that attribution leaves a defensible falsifiable successor;
   otherwise stop before consuming the remaining iteration allowance.

## Overnight Autonomous Boundary

- User authorization on 2026-07-18 covers five total serialized causal research
  iterations, with the terminal Stage C result counted as iteration 1.
- One iteration closes only on terminal evidence plus a controller disposition;
  an operational retry does not consume an iteration.
- Each later iteration must name one falsifiable question, one strongest matched
  comparator, one exact implementation/experiment contract and one active
  evidence source. No parallel training, parameter rescue or arbitrary gate
  sequence is authorized.
- Stop before five if a binding result has no defensible successor, the next
  action would violate a retired/prohibited branch, or safe progress requires
  user authority outside this five-iteration research boundary.

## Immediate Constraints

- The accepted testbed uses anonymous `4 -> 2 -> 6 -> 4` membership, one
  generic `SHORT` action, a persistent duty, variable-`N` reactive workload,
  horizon 80 and one terminal external utility.
- Evidence is serialized:
  `carrier -> direct primitive-AR -> paired F0/F1 -> conditional timing read`.
- The generic-`SHORT` environment has a typed event adapter, collector
  transport and one shared F0/F1 execution/update branch. Focused evidence does
  not pre-judge the formal CUDA/subprocess result.
- Stage A result `logs/f0f1_dynamic_roster_stage_a_20260717_143552` is valid:
  all M0 checks pass; constructive `P=S=U=1.0`; random positive-utility fraction
  `1.0` with mean utility `0.331217`; optimizer and intrinsic reads are zero.
- Stage B uses a 14,980-parameter anonymous recurrent primitive actor-critic,
  token-factor PPO with one shared team advantage/value, raw current-step
  action-count prefixes and strict standalone schema-3 checkpoints. Its
  focused test passed; a CUDA fresh-to-resume smoke preserved exact ledger and
  cumulative counters, and replay maxima are below `5e-7`.
- The valid Stage B run is
  `logs/f0f1_dynamic_roster_stage_b_20260717_160956`: all M0 checks and replay
  errors pass, final deterministic `P/S/U=1/0.998210/0.999105`, final
  stochastic `U=0.986654`, and paired utility-gain CI95 is
  `[0.498535,0.499105,0.499593]`.
- Each learned arm is frozen at 320,000 transitions, 16 environments, rollout
  80, 250 updates and PPO4. Failure cannot trigger a budget, seed, threshold,
  reward or model rescue.
- Retry2 stopped cleanly at 39,680/320,000 transitions and 124/1,000 high/low
  optimizer steps per arm. Its monitor is paused and its status is
  `stopped/performance_refactor`; it must not be resumed across source commits.
- Batched ragged low inference and one-time PPO4 rollout packing pass all 20
  focused CPU/CUDA checks and combined review. Concurrent 16-env steady-state
  throughput improved from 138--161 to 44--45 seconds/update (3.1--3.6x), while
  real-scale replay errors remained at most `4.77e-7`.
- The first launch root without a retry suffix failed before training because
  the restricted desktop process could not atomically replace status files.
  The same write succeeded with full permission; `_retry2` therefore changes
  only the launch permission boundary and preserves the frozen experiment.
- Stage C introduces no intrinsic reward. Intrinsic-applied counts remain zero;
  the only learning reward is the registered sparse terminal external utility.
  No task field may be relabeled as intrinsic reward or shaping.
- Strict schema-3 vector live resume now saves and restores shared models,
  optimizers/normalizers, every environment runtime/ledger/RNG, simulator
  snapshots and counters. Fresh evaluation is explicitly model-only.
- Intrinsic reward remains environment-agnostic. Task fields, identities,
  roles, success predicates, progress and external reward cannot enter it.
- Stage C is terminal `SUPPORT_H2_SKILL_LIMIT`: M0 passes; F0/F1 have 1,932
  eligible natural prefix rows each, replay maxima below `3.71e-7`, final
  `P/S/U=0/1/0.5`, and no executable naturally used skills. F1 forced
  `rho=0.070304` does not establish natural task transport.
- R41B remains the positive fixed-`N` source anchor. R51--R55 exact contracts
  are retired and inactive.
- Do not add graph, attention, slots, critical residuals, team latent, a new
  discriminator, learned ordering, learned event time, task-specific intrinsic
  reward or reward shaping to this route.
- Git history and `memory/ExpRecord.md` preserve retired-result detail; do not
  duplicate it here or reopen a retired branch by retuning.

## Pointers

- `memory/ALGORITHM_PRINCIPLES.md` — durable research contract.
- `memory/IMPLEMENTATION_PLAN.md` — latest staged core implementation state.
- `memory/ExpRecord.md` — formal experiment contracts and terminal decisions.
- `docs/research/designs/F0_F1_DYNAMIC_ROSTER_TESTBED_CONTRACT.md` — accepted
  design-only contract and exact evidence branches.
- `docs/research/designs/VARIABLE_N_LIFETIME_EVENT_ARCHITECTURE_CONTRACT.md` —
  retained event-runtime architecture boundary.
- `docs/external-review/rounds/20260717_f0_f1_dynamic_testbed_design/` — blind
  reviews, controller synthesis, convergent raw response and disposition.
- `docs/external-review/rounds/20260717_variable_n_lifetime_architecture/` —
  preceding architecture review.
- `docs/external-review/rounds/20260717_variable_n_lifetime_implementation/` —
  preceding implementation-plan review.
