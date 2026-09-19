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

## 2026-09-18 evening — CF comparator and B01 runner accepted; independent review; plan for stage 0

**Accepted work (DM).** Implementer commits `f8532f99e` (flag-gated CF pathway in
`hmasd/networks.py`, `hmasd/agent.py`, `hmasd/utils.py`, flag default False in both configs,
`CONFIG_DUMP_FIELDS`) and `f3d082f81` (runner
`scripts/run_fsd_matched_information_baseline_b01.py`, launch entry, 57 tests; the superseded
host-headroom runner, launch script and test deleted). I read the core diff and the card
transcriptions myself. Checks: new object tests 57 passed; the whole FSD test tree 201 passed
(`--import-mode=importlib`; duplicate test basenames across frozen directories predate this);
D2 guard 13 passed. Known failures that predate this change and were reproduced at the parent
commit: `tests/ha_ctse_test.py::test_process_mode_clear_buffers_invalidates_old_policy_state`
(stub agent lacks `d2_enabled`) and the host-dependent P4 tape digest in
`tests/update_phase_equivalence_test.py` — the tape rebuilt from the parent and from this
change is identical on this host, which is the flag-off identity evidence.

**How the card's interface was realised.** CF runs the `off` route. The held snapshot refreshes
exactly where that route re-decides skills, `(env_steps % k == 0) | done | invalid skill`, with
k = 10, i.e. steps 0, 10, 20, … of an episode and the first step after a lane reset, from that
step's state and joint observations, before the actor forward. Raw values are held and stored
per step; normalisation is applied at use by the same code in collection, replay and evaluator.
Both arms instantiate `use_obsnorm = use_statenorm = False`, so the normalisers are the identity
and replay of the actor input is bit-exact; with them forced on, the snapshot would share the
private observation's existing end-of-rollout-statistics mismatch, no new one. Actor input
104 → 853 (state 119 + 6 × 104 + ego 6); only the actor's input projection widens. The frozen
B01 runner gained a `FLAT_ARM` constant (same value) so an arm named CF is validated as the flat.

**Independent review (`hmasd-reviewer`).** One material finding, operational: stage-1 CF could
not launch as documented, because the kernel's snapshot rebinds an absolute author path and
refuses one absent from the published snapshot, and `runs/` outputs are never in it. Repair
chosen: after stage 0, `SELECTION.json` is committed and stage 1 launches from that sha with
the repository-relative path; this also pins λ in Git before any stage-1 fit (card section 3).
Launch-script comment corrected. No leak, cadence, pairing, isolation or D1280-perturbation
finding; config differences CF versus D1280 are all inside the planned set. Nits repaired in
the same follow-up commit: the single-environment `select_action` route now refuses the flag
(it never advances the timer and would have read the centre every step; unreachable for this
object); dead `_central_snapshot_source_step` removed; `stage_guard` runs before the single-use
admission; `fit_endpoint` checks the flag in the evaluation config too. Left as is, on purpose:
`interval_inside_mei` uses the closed interval the card words ("entirely inside [−.05, +.05]");
the inherited descriptive `cost_law` string; the evaluator's unused snapshot buffer (≈48 MB).
After the repairs: object + frozen B01 + D2 guard + buffer/RNN suites 105 passed.

**Cost facts (timing probe by the Implementer, one rollout at full training shape, outside
`runs/`, no endpoint, no admission; not a fit).** CF 70.4 s per rollout and peak RSS 870 MiB;
flag-off flat 66.0 s and 845 MiB on this host. Collection and update alone extrapolate to about
3,200 s per CF fit; the nine 32-world panels are not included, so the card's 12,000 s ordinary
plan is kept as the watchdog basis until the first fit reports.

**Stage 0 plan.** Six CF fits (λ ∈ {0.5, 1, 2} × blocks 772603, 772703) on `wsl_4070`, each
through `launch_fit.sh` and the admission kernel from the published sha. Two first, RSS and
per-rollout wall read from their progress, then up to four concurrent. No stage-1 fit or panel
is read before `SELECTION.json` is committed.
