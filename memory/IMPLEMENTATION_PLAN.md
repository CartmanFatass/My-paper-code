# HA-CTSE Implementation Plan

Purpose: staged core-algorithm work only. The binding research target, S7-S1
parity definition, baseline hierarchy, promotion ladder, and failure-review gate
live in `memory/ALGORITHM_PRINCIPLES.md`; they are not repeated here.

## Post-R28 On-Policy Target Gate

Active causal edge:

```text
on-policy state visitation
-> support-compatible, non-shortcut individual differentiation signal
```

The R28-G1 frozen reward design remains evidence, but its launch package is
blocked before formal execution. The disposition and cross-round baseline
matrix live in `memory/LTM/R26_R27_R28_FAILURE_REVIEW_20260713.md`.

Completed boundary:

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

Current boundary:

1. R29-G0 passed the three-checkpoint reward-off gate. The natural on-policy
   action-information target is positive against the cyclic sham and the
   inactive-FiLM control is numerical zero.
2. External review modified R29-G1 into R29-T10. For each complete natural skill
   lifetime, the collection actor is replayed from the stored pre-step hidden
   state under each fixed candidate skill. The uniform density ratio uses the
   final 10 action likelihoods, then adds one detached clipped reward at the
   lifetime endpoint. Length-batched replay keeps this tractable on GPU.
3. Run the authorized single-seed `probe_only` versus `real_reward` pair at
   +320K steps per arm. The run itself is the implementation check; after final
   R26/task evidence, prepare the raw result package for GPT-5.6 Pro.

Core MARL impact: when R29-T10 is enabled, only the low-level reward, GAE/returns,
and low actor/critic optimizer updates change. High-level returns/policy,
collector semantics, environment dynamics, team intent, credit assignment, and
skill lifetime remain unchanged.

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


## Archived Plan History

Completed R22/R24/R26/R27 implementation detail is preserved by the frozen
designs, `memory/LTM/IMPLEMENTATION_PLAN_ARCHIVE_20260713.md`, and
`memory/LTM/EXPERIMENT_ARCHIVE.md`. Older completed/superseded rounds are in the
same plan archive. Read them only when this plan points there or the user asks
for history.
