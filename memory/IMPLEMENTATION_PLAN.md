# HA-CTSE Implementation Plan

Purpose: staged core-algorithm work only. The binding research target, S7-S1
parity definition, baseline hierarchy, promotion ladder, and failure-review gate
live in `memory/ALGORITHM_PRINCIPLES.md`; they are not repeated here.

## Post-R28 Natural-Expression Transport Gate

Active transport edge:

```text
R27-proven forced skill regime
-> support-compatible action process under on-policy state visitation
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

Next stage order:

1. Execute the 64-reset paired diagnostic through the four-worker local CUDA
   runner; reuse the frozen scorer only as a diagnostic ruler.
2. If stochastic forced trajectories remain supported, isolate forced hold
   versus natural assignment/renewal under identical stochastic execution.
3. Only a passed transport/activation edge may authorize design of a new
   stage-3 reward test. A transport failure instead returns to observational
   target design without changing the actor.

Core MARL impact: none from the completed diagnostics or review. Reward,
actor/critic/FiLM/GRU, optimizer/loss/GAE/PPO, collector semantics, environment
dynamics, credit assignment, team intent, and latent-lifetime semantics remain
unchanged.

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
