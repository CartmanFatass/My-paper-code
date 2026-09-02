# D2 execution handoff — paused after Phase 2 (2026-09-02)

Written by the executing session at the owner's request, at a clean phase boundary. Phases 0-2 are
complete, committed, and pushed; Phase 3 has design notes but no code; Phases 4-8 untouched. The
working tree carries no uncommitted D2 changes. The plan is the specification and is unchanged from
the delivered version (`D2_IMPLEMENTATION_PLAN_20260902.md`, commit `570b2e989`); where this
handoff and the plan disagree, the plan wins. Do not edit the plan, the ADR, or the review.

## State

| Phase | Status | Commit |
| --- | --- | --- |
| 0 — baseline fingerprint | done | `307992fe` |
| 1 — configuration | done | `a85fe706` |
| 2 — coordinator API | done | `368206861` (rebased onto `cd1d1b5be`) |
| 3 — rollout logic | design notes below, no code | — |
| 4-8 | untouched | — |

Phase 0 artifacts: `tests/flexible_skill_duration_d2_test.py` (fingerprint driver, `__main__`
regenerates the fixture; test 1 compares a fresh run against it) and
`tests/fixtures/flexible_skill_duration_d2/fingerprint_off.json` (canonical sha256
`3c525b9c3d26ef0385231c660f25a962eccdee87103feb39a4fc361dd225d937`). Test 1 passes as of this
handoff and was re-run after every phase; it is the guard for invariant 1.

Phase 1 (`config_1.py`): D2 parameter block after the loss weights (~line 170), validation in
`_validate_policy_interruption()` called from `validate_config()` (inert in `off`), and the
scenario-7 `episode_length % k` check (~line 726) is mode-guarded (kept in `off`, skipped in `d2`).

Phase 2 (`hmasd/networks.py:960-1220`): `evaluate_held_batch`, `assign_partial_batch`,
`evaluate_training_batch_ordered` on `SkillCoordinator`. Verified by six smoke checks
(`temp/pytest_d2_policy_interrupt/phase2_smoke.py`, gitignored, may vanish): (1) held evaluation
draws no RNG; (2) all-sampled canonical `assign_partial_batch` is bit-equal to
`assign_and_value_batch`; (3) all-sampled canonical ordered replay is bit-equal to
`evaluate_training_batch`; (4) partial order/forced/team-forcing semantics with a scripted S_t;
(5) ordered replay reproduces the collection log-probs exactly (old-log-prob consistency);
(6) gradients flow through the ordered replay.

## Next

1. Phase 3 (`hmasd/agent.py`, `_batched_assign_skills` at 1865): implement the d2 branch per plan
   §5 with the design notes below. First read `_store_coordinator_experience` (agent.py:2743-2900)
   and the `env_pending_high_level` mechanism to fix the Phase 3→4 metadata contract (open design
   point below).
2. Phases 4-8 in plan order. Phase 4 is the per-agent segment tables (`hmasd/utils.py` +
   storage helpers); the buffer-clearing behavior noted in the discrepancy list applies.
3. Phase 8 report: fold in the discrepancy list below, unedited in substance.

## Phase 3 design notes (paused session; no code written)

- The d2 branch lives inside `_batched_assign_skills`, guarded by the mode; `off` keeps lines
  1885-1975 exactly as they are. Return contract stays
  `(team_skills_batch, agent_skills_batch, log_probs_list)` with the log-probs dict shape
  `{'team_log_prob', 'agent_log_probs', 'state_value', 'agent_values'}` (consumed by
  `_batched_select_action` at 2456, `step_data`, and the storage path).
- Per-env state: `env_team_ages` (new dict, int per env); `env_skill_ages` already exists
  (agent.py:802) but is only maintained on the HA-CTSE path (increment at 2027) — the d2 base path
  must maintain it itself.
- Trigger per env per step:
  1. reset/done/invalid skills (`invalid_skills_mask` at 1894, `dones_batch`): team decision, all
     agents sampled, ages reset, cause `reset`.
  2. otherwise `evaluate_held_batch` on the non-reset subset; `g_Z = Z_logits.max(-1) -
     Z_logits[held_Z]`, `g_i` likewise from `z_logits` `[B, N, n_z]` (the softmax normaliser
     cancels in the gap; use the same clamped logits the sampler uses).
  3. team decision iff `g_Z >= c_Z` or `a_Z >= k_Z` → `sampled_mask` all-ones (cause `team_gap` /
     `team_cap`); else `sampled_mask[i] = (g_i >= c) or (a_i >= k_max)` (cause `gap` / `cap`).
  4. any sampled → `assign_partial_batch` for those envs (reset envs included: all-sampled
     canonical is bit-equal to `assign_and_value_batch` per smoke check 2, so one code path
     suffices); ages: sampled agents → 0, others +1, team age → 0 on team decision else +1.
     None sampled → ages +1, no RNG draw, no buffer row.
- `skill_changed` (agent.py:2463-2469, base path `(env_steps % k) == 0 | dones`) needs a d2
  branch: `skill_changed = sampled_mask.any(-1)` (a team decision implies all-sampled).
- Metadata for Phase 4 (sampled mask, order, sample-Z flag, log-probs, values, causes) can flow
  via `step_data` (already passed through `store_transition_batch`) and/or an agent-side
  `env_d2_last_decision[env_id]` dict; decide after reading the pending mechanism.
- Metrics to accumulate (plan §5): g_i/g_Z histograms, |S_t|, switch rate by agent index,
  boundary-cause counts, sampled/forced counts, coordinator inference time
  (`_add_transition_profile`, agent.py:1131).
- Cheap d2-only asserts: `c = inf` implies no `gap` cause; team decision implies
  `sampled_mask.all()`.

### Open design points

- Read `_store_coordinator_experience` (2743-2900) and the pending mechanism before wiring
  metadata: in `off`, a pending high-level sample is created when a decision happens and closed by
  timer/done/force-collection. Phase 4 replaces the close rules with per-agent segment tables; the
  metadata contract should hook the same creation/closure points.
- Until Phase 4 lands, a d2 rollout is not storage-coherent (the old pending path mis-closes under
  per-agent ages). Accepted intermediate state per the plan's phase order; only `off` must stay
  byte-identical at every commit.

## Plan-vs-code discrepancies found (record in the Phase 8 report; do not edit the plan)

- §2 cites `tests/hmasd_run_test.py` as the construction pattern; it is a subprocess run-manifest
  harness. The usable patterns: agent construction per `tests/intrinsic_reward_batch_test.py`
  (`HMASDAgent(config, log_dir=..., device=...)`); batched rollout loop per
  `train_multiproc_config_1.py:4567-5036` (`agent.step` at agent.py:2399 → env step with
  terminal-state storage semantics → `store_transition_batch` at 3159 → per-env reset bookkeeping
  → discoverer bootstrap at 4942-5005 → `agent.update` at 5712 → `clear_buffers` at 5132);
  scenario-1 env `UAVBaseStationEnv` (main.py:389; `envs/pettingzoo/scenario1.py:4`) with
  `max_steps = episode_length` and per-env seeds `base_seed + rank`, wrapped in
  `ParallelToArrayAdapter` (`envs/pettingzoo/env_adapter.py:17`).
- §4 cites `evaluate_training_batch` at networks.py:868; the def is at 862.
- §4 says "Two new methods" but lists three; three were implemented.
- The `episode_length % k == 0` check at config_1.py:719 sits inside `_validate_scenario7_preset`
  (scenario-7 only), not a general assertion. Phase 1 implemented the plan's intent literally
  (mode-guarded at that site; cap validation in `validate_config()`).
- The real route calls `agent.clear_buffers()` after `agent.update()` (train_multiproc:5132);
  the fingerprint driver mirrors this — without it the second rollout's stores are rejected as
  time steps going backwards.
- `agent.step` is called with `build_infos=False` in the real non-debug route → `infos_batch=None`
  to `store_transition_batch`; `step_data` carries what storage needs.
- After a done, the policy keeps the terminal state (no `reset_state` on the SubprocVecEnv path,
  train_multiproc:4898-4905) while observations use the post-reset obs; the driver mirrors this.
- `use_ha_ctse = bool(getattr(config, 'use_horizon_window', False))` (agent.py:473); config_1 does
  not set `use_horizon_window`, so the base route is the default — D2 configs must not set it.

## Operating notes for the next session

- Verify the boundary before starting: `git status --porcelain` limited to `config_1.py`,
  `hmasd/networks.py`, `hmasd/agent.py`, `hmasd/utils.py`,
  `tests/flexible_skill_duration_d2_test.py`, `tests/fixtures/flexible_skill_duration_d2/` must
  be empty, and test 1 must pass:
  `C:/Users/fires/.conda/envs/hmasd-amd-cpu/python.exe -m pytest -q
  tests/flexible_skill_duration_d2_test.py --basetemp
  C:/Projects/HMASD/temp/pytest_d2_policy_interrupt`
- Run `scripts/hmasd_resource_preflight.py admit-memory --out <receipt>` (explicit interpreter)
  before any model-creating run; require the 4 GiB floors to pass.
- Commit per phase ("D2 phase N: ...") and push immediately (standing authorization). Another
  session is actively pushing relay-corridor work to `main`; push rejections are expected — fetch,
  `git pull --rebase --autostash`, push. Never force-push.
- A stale reflog file `.git/logs/refs/remotes/origin/claude` was removed this session (it blocked
  creation of `claude/*` remote-tracking refs); if that fetch error reappears, this is the cause.
