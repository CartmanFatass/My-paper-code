# HA-CTSE Current Work

Updated: 2026-07-14

Purpose: the single mandatory first read. Keep only controller ownership, the
current objective, next actions, immediate constraints, and pointers. Evidence
and history live in their owning files.

## Controller Handoff

- **Active controller:** Codex on branch `aggressive`. Codex and Claude Code
  alternate; only one controller may modify the repository at a time.
- **Workflow authority:** `AGENTS.md`. Retired delegated-agent, Superpowers,
  routing, review-package, and lifecycle files are provenance only.
- **Versioning:** Git only; no application-layer hashes or checksums.
- **Project boundary:** IMOD is separate and is not evidence for HMASD. Its
  operational conventions may be consulted without importing its algorithms or
  experiment parameters.
- **Shared GPU scheduling:** Codex task
  `019f5aca-bde7-70b3-8c94-24584136c2c9` is the IMOD/HMASD lease controller.
  Formal cloud jobs must be registered there from an exact committed contract.

## Current Objective

Select one post-R31 causal edge that can create persistent task-agnostic skill
effects rather than classify natural correlations:

```text
R29 action-pattern reward failed
-> R31 observational effect scorer failed causal persistence
-> one intervention-anchored effect-creation route
```

No R32 implementation or reward run is authorized until the manual GPT-5.6 Pro
review selects that single route and its smallest abandonment gate.

- R27-G2 established forced persistent conditional capacity and a local effect;
  R26 remains the natural observational negative. This does not establish
  natural selection, reward usefulness, cooperation, credit, or task gain.
- R28-G0 `PASS_TARGET_NULLS` froze the only accepted scorer.
- Two exact R28-G1 one-update engineering smokes reproduced
  `FAIL_SUPPORT_OOD`: OOD `0.950617` and `0.9375`, one support kill each, and
  zero R28 reward-applied steps. The formal three-arm reward experiment never
  ran and has no scientific outcome.
- Feature/order/action/duration/distance parity is confirmed. The dominant
  residuals are all four temporal action standard deviations, consistent with
  a real forced-deterministic to natural-on-policy trajectory-domain shift.
- The frozen G1 launch package is therefore `BLOCKED_SUPPORT_OOD`; the completed
  cross-round review is
  `memory/LTM/R26_R27_R28_FAILURE_REVIEW_20260713.md`.
- The 64-reset paired transport diagnostic returned
  `FAIL_STOCHASTIC_SUPPORT_TRANSPORT`: deterministic OOD `0.068359` versus
  stochastic OOD `0.823242` across 1,024 paired windows per mode. Random action
  execution alone reproduces the action-std domain shift.
- The forced-deterministic R28-G0 scorer family is retired from online reward
  use. It must not be refit, widened, or carried into another reward package.
- R29-G0 passed at update25, update30, and final. Active action-information
  means are `0.017050`, `0.017990`, and `0.019208` nats; the inactive control is
  numerical zero and every active skill clears its floor. A support-native
  individual action-information target therefore exists on natural on-policy
  states; this does not yet establish reward usefulness or task gain.
- GPT-5.6 Pro modified the pointwise reward into R29-T10: fixed-skill recurrent
  replay over each complete natural lifetime, final-10-step density ratio, one
  endpoint reward, low GAE only. The pointwise online reward is retired.
- The authorized single-seed R29-T10 pair completed as `PRELIMINARY_FAIL`.
  Implementation validity passed, but the reward arm did not preserve the
  probe-only R26 signal and failed both the score and task-safety gates. This
  blocks promotion, retuning, or seed expansion on the current reward line.
- GPT-5.6 Pro returned `RETIRE`, accepted on 2026-07-14. R29 and variants that
  only change prior/window/aggregation/scale/clip are retired as online reward;
  R29 remains diagnostic-only. The reusable failure is that state-conditional
  action-mean separation need not produce stable natural effects.
- GPT-5.6 Pro identified the current `(skill,duration)` / expired-agent update
  as a structural conflict with complete MAT-style sequential editing. The
  accepted R30 correction retires duration selection from the core: every agent
  emits `KEEP` or `SET(other_skill)` every `k0`, high PPO moves to fixed check
  blocks, and variable process segments remain low-level records only.
- GPT-5.6 Pro returned `MODIFY R30`, accepted on 2026-07-14. R30 now uses a
  deterministic expected bridge, one prefix-independent critic value per high
  row, per-environment clocks with critic-only update continuation, a dedicated
  high-check buffer, and one combined PPO ratio per `SET` token.
- The corrected R30 implementation boundary is complete: active duration
  actions are absent in R30 mode, high PPO is isolated in `HighCheckBuffer`,
  legacy checkpoint migration is explicit, and the registered reward-pure
  paired runner/analyzer are ready.
- `alice_bob_asymmetric_cycles` is now the role-free fast mechanism sandbox:
  the button subtask persists for four `k0` blocks while the target subtask
  changes every block. The environment never assigns either task to an agent;
  complementary skill allocation is inferred from behavior. The legacy
  one-step transition reward is now disabled; R31 uses only complete natural
  fixed-window joint-position effects, and the fixed-clock high buffer continues
  to receive raw sparse task reward only.
- The paired 64K Alice--Bob screen completed with valid R30 replay and
  non-degenerate lifetime use, but neither arm contacted the target or completed
  a cycle and natural context-residual skill differentiation was not established.
  The historical run also used a `0.20 * Delta potential` environment reward,
  so it is mechanism evidence only, not a sparse-exploration result. The active
  Alice--Bob environment is now collection-only sparse reward; distance and
  progress shaping have been removed from reward and advantage.
- GPT-5.6 Pro returned `ACCEPT R31`, archived raw on 2026-07-14. The unique
  route is natural-window CFEI with forced stochastic branches used only for a
  reward-off causal audit. It was implemented at commit `a7b985b` and evaluated
  by the registered local gate below.
- The registered R31 gate completed `FAIL`: natural heldout information was
  `0.487866` nats, but forced-skill median between/within ratio was `0.889613`
  and matched shuffle was `-2.068` nats. The implementation/comparator was
  valid; no policy update or gate checkpoint occurred. R31 and its 160K reward
  pair are retired.

## Next Actions

1. Manually submit
   `docs/external-review/gpt5_6_pro/20260714_r31_cfei_gate_result/GPT5_6_PRO_QUESTION.md`
   to GPT-5.6 Pro using the private GitHub repository.
2. Archive and disposition the raw response, then implement only its one
   accepted intervention-anchored causal edge and smallest Alice--Bob gate.

Completed run: `logs/r29_t10_paired_320k_20260714_010026`; formal result detail
is in `memory/ExpRecord.md`. The manual review package is under
`docs/external-review/gpt5_6_pro/20260714_r29_t10_result/`.

## Immediate Constraints

- Do not refit, retune, or sweep the frozen R28-G0 scorer.
- Do not launch the blocked R28-G1 cloud package or repeat the identical local
  smoke.
- Do not rerun the fixed HMASD baseline or R25 arm0/arm2 references without
  explicit user approval.
- Keep the old `q_d/q_D` reward paths and default-off `q_A` disabled. Do not add
  team reward, communication-intrinsic mechanisms, kappa/hazard, or DADS while
  the individual-differentiation gate is open.
- Do not reinterpret forced R27 capacity as natural use or a team-level claim.
- Keep R29 diagnostic-only. Its online `real_reward` path and variants that
  alter only prior, window, aggregation, coefficient, normalization, or clip
  are retired.
- Do not tune or enlarge duration candidates, restore a duration head or
  duration entropy floor, or use duration as a skill-semantic input in the
  active core.
- R30 uses no keep entropy, edit/switch penalty, forced maximum lifetime, or
  positive lifetime reward. Long survival must be learned from delayed task
  advantage rather than paid for directly.
- Do not use environment potential/progress shaping in Alice--Bob sparse
  exploration claims, and do not count shaped progress as algorithmic intrinsic
  reward. The completed 64K shaped pair remains mechanism-only evidence.
- Do not inject another individual-skill reward before a reward-off diagnostic
  establishes the selected realized-effect target under policy-matched
  stochastic execution.
- Do not launch R31 reward, its 160K pair, an identical-batch append, or any
  R31 coefficient/window/prior/posterior/null/threshold variant.

## Pointers

- `memory/ALGORITHM_PRINCIPLES.md` — binding research contract.
- `memory/IMPLEMENTATION_PLAN.md` — active transport implementation boundary.
- `memory/ExpRecord.md` — formal experiment contracts, evidence, and decisions.
- `docs/research/R28_G1_CAUSAL_SKILL_FORCING_REWARD_DESIGN_20260713.md` — frozen
  R28-G0/G1 design.
- `docs/research/R27_G2_FORCED_Z_TRAJECTORY_EFFECT_DESIGN_20260712.md` — frozen
  R27-G2 design.
- `memory/LTM/IMPLEMENTATION_PLAN_ARCHIVE_20260713.md` and
  `memory/LTM/EXPERIMENT_ARCHIVE.md` — superseded/completed detail.
- `memory/LTM/R29_ACTOR_DENSITY_RATIO_FAILURE_REVIEW_20260714.md` — accepted
  R29 retirement and next causal edge.
- `docs/research/R30_FIXED_CLOCK_AR_EDIT_DESIGN_20260714.md` — accepted temporal
  controller and implementation boundary.
- `docs/external-review/gpt5_6_pro/20260714_fixed_clock_keep_set/` — raw external
  response and controller disposition.
- `docs/external-review/gpt5_6_pro/20260714_r30_algorithm_code_review/` — raw
  `MODIFY R30` review and accepted controller disposition.
- `docs/external-review/gpt5_6_pro/20260714_r30_sparse_exploration_review/` —
  current result boundary and manual review entry for the next intrinsic route.
- `memory/LTM/external_reviews/` — raw external-review evidence and index.
