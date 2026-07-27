# Restart handoff — 2026-07-27, clean seam

Successor PM: read this, then `docs/project/CURRENT_WORK.md`. Everything below
is committed and pushed on `untied-k`. Nothing is half-applied.

Replaces the 2026-07-26 handoff, whose one open deliverable (task 14,
`user_world_seed` controlling generation) is **done and closed** — Stage B round
`20260727_d7_s_stage_b_fingerprint_closure` returned `ALIGNED`, zero blockers.

## The only boundary

```text
next_boundary = USER_COMPUTE_AUTHORIZATION_FOR_THE_D7S_AUDIT
```

Every gate is passed. To launch:

```
git tag d7s-audit-2 && git push origin d7s-audit-2
```

That tag push is **user authority** (`formal_compute=user authority only`), and
the last attempt to run it was refused by the auto-mode classifier. Ask; do not
retry it silently. `d7s-benchmark-*` pushes do succeed, so the block is specific
to this tag pattern, not to tagging.

## What the last six iterations were

Supporting work only — iterations 24–29, no conclusion-bearing quota consumed.
`iterations_remaining=17` unchanged. **The next conclusion-bearing report is 30
and it is the audit result itself.**

All of it is one investigation: **guards that cannot go red**. Ten instances so
far, evidence notes dated `20260727_*` under
`docs/research/cdc/EVIDENCE_NOTES/`, and the accumulated rule is
`.claude/skills/hmasd-acceptance-gate/SKILL.md`, section *A guard test needs a
paired negative*. Read that section before writing any test here.

The method converged: **sweep mechanically before you sweep by reading.**
Perturb a constant, disable a guard clause, rerun. It reads nothing, so a
plausible test name cannot talk it out of a finding — which is how the first
eight instances survived. Harnesses live in the session scratchpad
(`mutsweep.py`, `constsweep.py`, `poolsweep.py`); they are disposable, rewrite
them per surface.

## Open findings — two confirmed, un-repaired

A sweep found these on 2026-07-27. **I reproduced both myself with independent
mutations**; they are not un-verified child claims. Both are UNGUARDED and both
reach the estimator, so neither is cosmetic:

1. **`test_user_world_seed_is_disjoint_from_every_other_registered_seed`**
   probes the `stream_seed` namespace at exactly **one** coordinate
   (`phase="evaluate", limb="stable", event_index=0, replicate_index=0`).
   Collapsing `user_world_seed` into `stream_seed` at `phase="select"` collides
   exactly, and the suite stays **177 passed**. The seed reaches
   `build_pinned_env` → `regenerate_user_world` → `qos_satisfaction_ratio` →
   `compute_G`. It corrupts an estimator input, not a recorded field.

2. **`test_legal_set_never_excludes_for_unreachability_within_delta`** exercises
   only the `post_leave_targets` half of `Z(h)`. Excluding the **vacated
   pre-LEAVE target** for unreachability leaves the suite **177 passed**. That is
   the worse half to lose: it controls `has_legal_set_alternative`, hence
   `EXCLUDE_EMPTY_SET_ALT` → `REJECT_EMPTY_LEGAL_SET`, so it silently shrinks the
   admitted event set, biased toward "persistence is necessary" — the
   claim-favouring direction.

Repair both before the audit result is read. Neither blocks the launch.

### And seven more in Scenario-7 — reported by a sweep, two verified by me

A second sweep covered `tests/scenario7_energy_aware_test.py` against
`envs/pettingzoo/scenario7_energy_aware.py` (42 tests here; the sweep ran on an
older worktree at 34, so **treat its line numbers as approximate and re-anchor
by text**). It reported seven UNGUARDED and five CLEAN.

**I reproduced the top two myself on the current tree, each anchor matching
exactly once — 42 passed under both mutations:**

- **Hover gate.** Disabling
  `if np.linalg.norm(actual_velocities[uav_idx]) > self.charging_hover_speed_threshold`
  credits charging to a *moving* UAV and nothing notices. Reaches `uav_charging`
  and the battery credit → `_energy_failure_mask` → cutoff/depletion counts →
  the 5.0/10.0-weighted penalties in `safety_reward_before_pbrs`. Also
  trajectory-changing (gates termination) and an observation feature. Highest
  severity of the set.
- **Termination quantifier.** `np.all(self.uav_battery_ratios <= 0.0)` →
  `np.any(...)` ends the episode on the *first* dead UAV, green. Feeds
  `terminations` → `episode_done` → the `terminal` flag that zeroes
  `potential_next` in the graph-PBRS term of `G`.

**The remaining five are the child's claims and are NOT yet verified** — treat
them as leads with stated anchors, not as record, and reproduce before repairing:
per-slot observation identity (`start = uav_idx * energy_uav_obs_dim` reversed,
green — every policy input silently re-bound); `set_scenario7_safety_dual` side
effects unobserved, so *only* in that test's name is vacuous; the five
parametrized reward-ablation variants collapsing to two numeric outcomes at the
fixture's seed; docking horizontal speed 3.0 → 1.0 undetected behind a
clamp-tautology assertion; and the station layout not reproducing across
processes.

The sweep also named what it did **not** mutate — seven tests plus one
observation that `test_constrained_safety_reward_metrics_are_exposed` is a
second copy of the production formula. Read that list before assuming the file
is covered.

## Two user rulings from this session

- **Subagent dispatch is granted.** It was never blocked by this repository —
  routing, roster and registrations were intact throughout. The block was one
  line in the session system prompt, lifted by the user on 2026-07-27.
- **Do not pin a model in an agent definition; assign it per dispatch — and
  assign it *explicitly*.** `general-purpose` pins no model and neither does
  `hmasd-guard-sweeper`, so an omitted `model` **inherits the orchestrator's**;
  on an Opus session, omitting gets you Opus. Two mechanical sweeps ran on Opus
  on 2026-07-27 for exactly that reason. Downgrade deliberately: swapping
  anchors and reading pytest exit codes is haiku work; tracing a mutated
  quantity to `compute_G` is not. (`hmasd-experiment-operator` stays pinned to
  haiku — that is a standing constraint, not a default.)

## Standing constraints that make a decision wrong if forgotten

```text
branch_scope=untied-k only, never touch another branch
formal_compute=user authority only
intermediate_authorization_prompts=forbidden
same_file_concurrent_writes=forbidden
```

The workstation is shared with another research line — check for foreign
processes before any local run, never touch them. Never bypass hooks; the drift
guard has blocked ~13 commits and every one was correct.

**Unresolved and the user's to settle:** ownership of `untied-k`. Another
session committed `d3e0f72` asking that ownership be established first.

## Two operational traps, both paid for

- `pytest` here raises `PermissionError [WinError 5]` on the system temp dir.
  Always pass `--basetemp` into the session scratchpad.
- A sweep script that rewrites a tracked file must verify its restore with
  `git diff --quiet`, **not** a string compare — a line-ending round trip
  through `write_text` leaves the string equal and the file modified.
