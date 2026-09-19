# flexible_skill_duration — notebook

Append-only (constitution section 4). Lead: Claude session. The last section is the handover.
Frozen object: [FSD_MATCHED_INFORMATION_BASELINE_B01](FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md);
the card stands in for the claim note and is read by its own section 6. History before this
file lives in `DIRECTION.md` and the dated cards beside it (evidence, not maintained).

## 2026-09-18 17:55 PDT — resumption; L0 for the CF comparator and the B01 runner

**Resumption.** The owner resumed research in the Claude session on the WSL host
(`/home/fires/hmasd-wsl`) with "我们继续研究". By the constitution the first execution batch is
B01 exactly as frozen. Work branch `claude/fsd-b01` from main `c7df86504`. No producer, no live
handle and no open Pro request were inherited (handoff of 2026-09-16).

**Source state checked before scoping.**
- The handoff's code map still matches main: `R_Actor` `hmasd/networks.py:1401`,
  `SkillDiscoverer` :1575, `_apply_compact_context` :1664; `hmasd/agent.py` `reset_env_state`
  :1559, `select_action` :1732, `_batched_assign_skills` :1917, `_should_close_high_level_sample`
  :3382, `store_transition_batch` :3862, `_compute_low_level_compact_context` :4059,
  `update_discoverer_from_rollout` :6088.
- The truncation/termination GAE fixes of 2026-09-18 (`5a7c31c45`, `d60c5f439`) touch only
  `ha_ctse_process/`. The FSD path (`hmasd/agent.py`) is unchanged, so D1280 is still the
  standing recipe the card names, and both arms share whatever boundary arithmetic that path
  has. Not altered for this object (card section 1, "kept unchanged").
- The superseded `scripts/run_fsd_host_headroom_b01.py`, its launch script and tests are still
  on main and are replaced in the same change, never launched.

**L0 scope.**
- *Deliverable.* (1) A CF ("central-input flat") actor input pathway behind a new config flag,
  default False in `configs/config_1.py` and `configs/config_test.py`, never set by
  `apply_algorithm_config("mappo")`, set only by the CF branch of the new runner's `make_config`.
  Per-lane central snapshot = normalised global state + six normalised joint observations in
  fixed UAV order, taken at the step after a lane reset and at every `skill_timer == 0` step
  with k = 10, held for the intervening steps, cleared at `reset_env_state`; actor input =
  private observation + held snapshot + six-dimensional ego one-hot (never normalised) +
  constant skill + own GRU state. The snapshot actually used at collection is stored per step
  and replayed byte-for-byte in the recurrent update; the evaluator builds it by the same code.
  (2) `scripts/run_fsd_matched_information_baseline_b01.py`: thin entry over the baseline
  interruption B01 runner, arms `D1280` and `CF`, 45 rollouts, panels after 5, 10, …, 45,
  `--stage {0,1}`, `--lr-multiplier` (CF only; every actor and critic optimizer group that
  trains, once, on the schedule output if any), `select-stage0` (card section 3 verbatim: max
  mean J45, tie order 1, 0.5, 2 within the maximal set, `SELECTION_INCOMPLETE`) and `reduce`
  (card sections 5 and 6 verbatim, including `PRIMARY_INCOMPLETE_OR_INVALID`). Launch script
  under `experiments/candidates/flexible_skill_duration/matched_information_baseline_b01/`;
  new result entry goes through `scripts/hmasd_launch.py` with the admission guard.
  (3) Tests of card section 8. Delete the superseded host-headroom runner, launch script and
  tests in the same change.
- *Owned paths.* `hmasd/networks.py`, `hmasd/agent.py`, `hmasd/utils.py` (flag-gated additions
  only), `configs/config_1.py`, `configs/config_test.py`, `scripts/run_flexible_skill_duration_e0.py`
  (`CONFIG_DUMP_FIELDS`), the new runner, launch directory and tests.
- *Must not change.* With the flag off every existing arm is bit-identical: no new RNG draw, no
  parameter, buffer field or module constructed, no change in initialisation order. D1280's
  inputs, recipe and optimizer rates. Actor hidden width, action head, critic input, PPO loss,
  discount/GAE/termination arithmetic. Seeds, blocks, panel law, MEI, labels and the reading
  rule of the card. Training normalisers, buffers and RNG are untouched by evaluation panels.
- *Checks.* Card section 8 tests; the existing FSD guards
  (`tests/flexible_skill_duration_d2_test.py`, the baseline interruption B01 tests) still pass
  with the flag off; real-tiny CF run (2 lanes, 20-step horizon) through collection, replay and
  evaluator. Scratch under `temp/`, removed. No result-bearing smoke.
- *Review.* Independent `hmasd-reviewer` on the agent/networks/utils diff before any launch.
- *Budget and stop.* No fit is consumed by this step. Stop and return on any conflict between
  the card's interface and the code that would need a scientific choice.

**Plan after acceptance.** Commit and push; publish the lifted pause and this direction row on
`main` (the launcher compares the local `RESEARCH.md` with `origin/main`); stage 0 = six CF
fits on `wsl_4070` with fresh admission per fit, `SELECTION.json` before any stage-1 read,
then ten stage-1 fits. CF wall and RSS are unmeasured: the first stage-0 fits are watched for
RSS before filling four concurrent slots.
