# HA-CTSE Implementation Plan

Purpose: staged core-algorithm work only. The binding research target, S7-S1
parity definition, baseline hierarchy, promotion ladder, and failure-review gate
live in `memory/ALGORITHM_PRINCIPLES.md`; they are not repeated here.

## Round 28 Action-Process Target And Future G1 Reward

Active causal edge: `distinct z_i -> naturally expressed, behaviorally
differentiated skills`.

The frozen design and scientific contract live in
`docs/research/R28_G1_CAUSAL_SKILL_FORCING_REWARD_DESIGN_20260713.md` and the
single active block in `memory/ExpRecord.md`. G1 consumes the immutable scorer
referenced there.

Implemented boundary:

- a separate default-off low-level reward module using frozen scorer/source
  continuity, exact same-forward deterministic-action evidence, natural clocks,
  common support, sham derangement, terminal-ten-step attribution, and
  fail-closed OOD/reward-ratio guards;
- checkpoint and CLI integration, R26 sidecar/export, family analyzer, focused
  tests, and a reusable parallel cloud runner;
- explicit non-resumable tagging for engineering-smoke checkpoints.

Stage order:

1. The local implementation smoke recorded in `CURRENT_WORK.md` reached one PPO
   update but failed the frozen support guard before R28 reward injection.
2. Diagnose feature construction versus genuine natural-distribution shift
   without changing any frozen scorer or support rule.
3. A confirmed construction bug permits one exact smoke repetition. A genuine
   support mismatch blocks this G1 target and enters its failure-review branch.

Core MARL impact: when `r28_g1_arm=off`, reward, actor/critic/FiLM/GRU,
optimizer/loss/GAE/PPO, collector semantics, environment dynamics, credit
assignment, team intent, and latent-lifetime semantics remain unchanged.

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
