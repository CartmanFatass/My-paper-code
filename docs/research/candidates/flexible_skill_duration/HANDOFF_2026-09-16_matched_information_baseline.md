# FSD handoff — matched-information baseline B01 fixed, implementation not started (2026-09-16 05:40Z, Claude hub)

**State: approved set v1.1, lane CONFIRM, priority 1. The first object is fixed by
`em:flexible_skill_duration:convergence` (2026-09-16 05:19Z, option C, PRO_FINAL):
[FSD_MATCHED_INFORMATION_BASELINE_B01](FSD_MATCHED_INFORMATION_BASELINE_B01_PROSPECTIVE_CARD_20260916.md).
No producer, no launch, no open Pro request (registry key `em:flexible_skill_duration:convergence`
ARCHIVED; only the protected default tab open). The owner asked to pause at a clean stopping point
(2026-09-15 22:23 PDT); this handoff is that point.** Authoring checkout
`C:/Projects/HMASD-worktrees/codex-fsd`, branch `codex/fsd` (head after this commit is the one that
adds this file); the hub mirrors direction-owned paths onto `main`.

## What is decided

- The DM's host headroom card (private-actor FLAT as a tuned same-information baseline, 2s / 1s rule,
  .67 J reference, I1280 arm) is **rejected**; its thin entry `scripts/run_fsd_host_headroom_b01.py`,
  launch script and tests (codex/fsd `4357579b9`, main `d29af5fc5`) are superseded and are to be
  replaced by the new runner, not launched.
- The replacement object is transcribed in the card above: D1280 (standing recipe) versus a
  central-input flat CF; stage 0 tunes CF's learning rate over λ ∈ {0.5, 1, 2} on blocks 772603 /
  772703 with the fixed selection rule (max mean J45; ties in order 1, 0.5, 2 within the maximal set;
  `SELECTION_INCOMPLETE` on any missing fit); stage 1 five fresh blocks 772803 … 773203, 45 rollouts,
  nine panels; primary mean over blocks of G_b = J45(D1280) − J45(CF); MEI .05 J; labels
  D_REFERENCE_ABOVE / SMALL_SIGNED / CF_REFERENCE_ABOVE plus INTERVAL_POSITIVE / NEGATIVE /
  INCLUDES_ZERO; `PRIMARY_INCOMPLETE_OR_INVALID`; 16 fits; ordinary plan about 183,500 s native;
  `headroom_record: not established`. Records: intake
  `pro_packets/20260916_host_headroom_card_convergence/INTAKE.md`, ledger row 43, approved set v1.1.
- The result is read by the card's own rule at completion; no result review unless an uncovered
  event changes the comparison's meaning. Lifecycle only at the owner-triggered review.

## First resume step: implement the CF comparator (L0), then review, then launch stage 0

Code map (read-only scout, 2026-09-16 05:35Z; verify line numbers before editing):

1. **Actor.** `hmasd/networks.py:1401` `R_Actor` takes `obs_dim` only; the skill enters by FiLM
   (`film_generator`, :1418, :1449-1452), never by concatenation. The GRU is `self.rnn` (:1421) with
   state passed in and out; persistent per-lane hidden states live on `HMASDAgent`
   (`env_hidden_states`, reset in `reset_env_state` `hmasd/agent.py:1559-1581`; batched mirrors
   `actor_hidden_np` :1762-1784).
2. **Existing precedent, not the mechanism.** `SkillDiscoverer` (`networks.py:1575`) has an optional
   additive, zero-initialised adapter `_apply_compact_context` (:1644-1673) gated by
   `use_compact_in_low_level_actor`, fed by a trainable extractor
   (`_compute_low_level_compact_context`, `agent.py:4059`) recomputed every step from
   `(states, joint_observations)`. CF needs a **new, separately gated pathway** (a new config flag,
   default False in `configs/config_1.py` and `configs/config_test.py`, never set by
   `apply_algorithm_config("mappo")`, set only in the CF branch of `make_config`): a raw central
   snapshot (global state + six joint observations in fixed UAV order) plus a six-dim ego one-hot,
   held constant between the k = 10 team-decision steps, cleared and rebuilt at lane reset.
3. **Collection call sites.** Batched path used by the FSD runners:
   `HMASDAgent._batched_assign_skills` (`agent.py:1917`; compact block :2944-2955; actor call
   :2958-2964; critic :2972-2977). Single-env path `select_action` (:1732; :1787-1795). The k-block
   boundary test is `skill_timer == config.k - 1` (:3386, :3399, :3414, :3431;
   `_should_close_high_level_sample` :3382); the step with `skill_timer == 0` is where a fresh
   snapshot is taken. Lane reset: `reset_env_state` (:1559) is where the per-lane snapshot cache is
   cleared too.
4. **Storage and replay.** `store_transition_batch` (`agent.py:3862`) stores per-agent obs/states,
   skills, log-probs, values, `skill_timer` (:3875-3889); it stores no snapshot. `joint_observations`
   for the existing compact path is **reconstructed at chunk time** from `data["obs"]` in
   `hmasd/utils.py get_discoverer_sampler` (`flatten_and_chunk_joint_observations` :1197,
   chunking :1180-1238, GRU chunk starts :1228), i.e. always current, which is not CF's held
   snapshot. CF must store its per-step snapshot (or the k-block index it was taken at) so replay
   uses the identical tensor. Consumer: `update_discoverer_from_rollout` (:6088; compact block
   :6172-6239, obs-normalisation of joint obs :6180-6182).
5. **Normalisation.** `obs_norm` / `state_norm` on the agent, `_normalize_observations` (:1353) and
   `_normalize_states` (:1405), updated only when training; the evaluator deep-copies both from the
   learner (`scripts/run_flexible_skill_duration_e0.py:327-328`). Snapshot components reuse those
   semantics; the ego one-hot is never normalised.
6. **Config surfaces to extend.** `CONFIG_DUMP_FIELDS` (`e0.py:208-217`, read by `config_snapshot`
   `run_fsd_uav_individual_renewal_b01.py:100`) must list the new flag; `PLANNED_CONFIG_DIFFERENCES`
   (`run_fsd_baseline_interruption_b01.py:35-38`) must include it; `make_config` (:44) gets a `CF`
   branch after the `mappo` switch and `k = 10`. `n_agents`: confirm the instantiated config carries
   6 (config_1.py:25 vs a stage override at :436).
7. **Runner.** New `scripts/run_fsd_matched_information_baseline_b01.py` as a thin entry over the B01
   runner (loop, panel law, `arm_panels` validation), arms `{"D1280", "CF"}`, `--stage`,
   `--lr-multiplier` (CF only; multiply every active actor/critic optimizer group once, on the
   schedule output if any), `select-stage0` and `reduce` implementing card sections 3 and 6 verbatim.
   Salvage from the superseded `run_fsd_host_headroom_b01.py`: the bind pattern, the
   `base_summary` wrapper recording stage/multiplier, the stage guards, the selection scaffold
   (change the tie order to 1, 0.5, 2 and add `SELECTION_INCOMPLETE`), and the launch script shape
   (`experiments/candidates/flexible_skill_duration/host_headroom_b01/launch_fit.sh`). Delete the
   superseded files in the same commit.
8. **Tests** (card section 8): snapshot fields and refresh steps and lane reset; identical inputs in
   collection, replay and evaluator; multiplier on CF groups only, D1280 unchanged; every stage-0
   tie case; 45 / nine-panel binding; label and interval boundaries, zero variance, missing pairs,
   invalid selection. Extend `tests/experiments/candidates/flexible_skill_duration/baseline_interruption_b01/test_real_tiny.py`'s
   pattern (2 lanes, 20-step horizon) with a CF arm. Scratch under
   `temp/directions/flexible_skill_duration/test/<tag>`, removed afterwards.
9. **Review and launch.** Independent `hmasd-reviewer` on the agent/networks/utils diff (actor
   input, replay, normalisation, reset). Then commit and push, create the exact-sha worktree on the
   node (`mkdir -p temp/directions/flexible_skill_duration/{test,exp}` there), fresh admission per
   fit, stage 0 first (six CF fits; up to four concurrent, watch RSS), `SELECTION.json` before any
   stage-1 read, then ten stage-1 fits, all through `hmasd-experiment-operator`. Node facts: 20
   cores, about 15 GB, no GPU, idle at 05:00Z.

Ordinary plan, not caps: CF about 12,000 s and D1280 about 10,300 s per fit; stage 0 about 4–6 h,
stage 1 about 12–16 h at four concurrent, subject to admission and RSS (CF unmeasured).

## Records on both branches

codex/fsd: `b8c41ad27` (rejected card), `fd9502467` / `a8a04757e` (request), `1462d3954` (Pro),
`4357579b9` (superseded L0), `09771b5f0` (intake, new card, DIRECTION), then this handoff. main
mirrors: `999e838cf`, `d29af5fc5`, `345b9474f`, then the handoff mirror. Transport archive:
`temp/sessions/hmasd-chatgpt-pro-transport/archive/flexible_skill_duration/2026-09-16-fsd-host-headroom-card-convergence-01/`
(prompt sha256 5d335567…, response sha256 0e9f6ca3…, delivery comment 5692440074).

## Predictions

DM (card section 10): D_REFERENCE_ABOVE .25, SMALL_SIGNED .50, CF_REFERENCE_ABOVE .25;
INTERVAL_INCLUDES_ZERO .80. Owner slot open until the first stage-1 panel is read.
