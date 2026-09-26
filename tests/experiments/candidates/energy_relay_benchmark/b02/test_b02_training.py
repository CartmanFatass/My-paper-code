"""B02 collector: parity with B09 ``train_arm``, save-without-RNG, held central snapshot."""

from __future__ import annotations

import copy
from dataclasses import replace

import numpy as np
import pytest
import torch

from experiments.candidates.energy_relay_benchmark.b02 import configuration as cfg
from experiments.candidates.energy_relay_benchmark.b02 import training as tr
from experiments.candidates.uav_service_auxiliary.b01.native import (
    _rng_state, make_config, optimizer_steps,
)
from experiments.candidates.uav_service_auxiliary.b09 import native as b09
from experiments.candidates.uav_service_auxiliary.b09 import training as b09_training

MODULES = ("skill_coordinator", "skill_discoverer", "team_discriminator",
           "individual_discriminator")


def _assert_same_modules(left, right):
    for name in MODULES:
        a, b = getattr(left, name), getattr(right, name)
        assert (a is None) == (b is None), name
        if a is None:
            continue
        sa, sb = a.state_dict(), b.state_dict()
        assert sa.keys() == sb.keys()
        for key in sa:
            torch.testing.assert_close(sa[key], sb[key], rtol=0, atol=0)


def test_collector_equals_b09_train_arm_on_ordinary_hmasd(tmp_path):
    """Same init, same tiny HMASD config (B09's short-collector fixture): bit-identical learners."""
    torch.set_num_threads(1)
    spec = replace(b09.B09Spec(), seed=317749, lanes=2, rollouts=2, rollout_length=12,
                   episode_length=7, hidden_size=32, gru_hidden_size=32, ppo_epochs=1)
    config = make_config(spec)
    config.k = 4
    config.ordinary_completed_segments = True
    config.initial_battery_ratio_range = (0.03, 0.03)
    config.sequence_length = 4
    config.sequence_batch_size = 8
    old_agent, _ = b09.new_initialized_agent(copy.deepcopy(config), device=torch.device("cpu"),
                                             log_dir=tmp_path / "old_logs", seed=spec.seed)
    old = b09_training.train_arm(old_agent, old_agent.config, spec, arm="A", out=tmp_path / "old")
    new_agent, _ = tr.new_agent(copy.deepcopy(config), device=torch.device("cpu"),
                                log_dir=tmp_path / "new_logs", seed=spec.seed)
    new = tr.collect_and_train(new_agent, new_agent.config, spec, feedback=True)
    _assert_same_modules(old_agent, new_agent)
    assert old["optimizer_steps"] == optimizer_steps(new_agent)
    assert old["counts"]["transitions"] == new["counts"]["transitions"] == 48
    assert old["counts"]["native_episodes"] == new["counts"]["native_episodes"]
    for phase, rollout in zip(old["phases"], new["rollouts"], strict=True):
        assert tr._scalar_update(phase["native_update"]) == rollout["native_update"]
        np.testing.assert_array_equal(phase["raw_native_J_by_lane"], rollout["lane_native_J"])
    exposure = old["training_exposure"]
    assert sum(r["f_mapped_commands"] for r in new["rollouts"]) == \
        exposure["feedback_mapped_command_uav_steps"] > 0
    assert sum(r["f_mode_uav_steps"] for r in new["rollouts"]) == \
        exposure["actor_proposal_uav_steps"] - exposure["feedback_passed_proposal_uav_steps"]


def _tiny_set(**changes):
    spec = replace(cfg.B02Spec(), seed=317751, rollouts=2, rollout_length=12, episode_length=12,
                   hidden_size=32, gru_hidden_size=32, ppo_epochs=1,
                   checkpoint_every_transitions=24)
    spec = replace(spec, **changes)
    config = cfg.make_b02_config(spec)
    config.initial_battery_ratio_range = (0.03, 0.03)   # forces shield entries
    return spec, config


def test_checkpoint_saving_draws_no_random_number(tmp_path):
    torch.set_num_threads(1)
    spec, config = _tiny_set()
    finals, records = [], []
    for label, save in (("saving", True), ("plain", False)):
        agent, _ = tr.new_agent(copy.deepcopy(config), device=torch.device("cpu"),
                                log_dir=tmp_path / label / "logs", seed=spec.seed)
        saved = []

        def after(rollout, record, agent=agent, label=label, saved=saved):
            if not save:
                return
            before = _rng_state()
            sampler = agent.rollout_buffer.get_sampler_rng_state()
            meta = tr.save_checkpoint(agent, agent.config, spec, tmp_path / label, rollout,
                                      rollout=rollout, transitions=record["transitions"],
                                      started=0.0, launch_sha="test")
            after_state = _rng_state()
            assert before["python"] == after_state["python"]
            assert all(np.array_equal(a, b) for a, b in zip(before["numpy"][1:2], after_state["numpy"][1:2]))
            assert before["numpy"][2:] == after_state["numpy"][2:]
            assert torch.equal(before["torch"], after_state["torch"])
            assert agent.rollout_buffer.get_sampler_rng_state() == sampler
            stored = torch.load(tmp_path / label / "checkpoints" / f"c{rollout:02d}" / "agent.pt",
                                map_location="cpu", weights_only=False)
            for key, value in agent.skill_discoverer.state_dict().items():
                torch.testing.assert_close(stored["skill_discoverer"][key], value, rtol=0, atol=0)
            saved.append(meta)

        result = tr.collect_and_train(agent, agent.config, spec, feedback=True,
                                      after_rollout=after)
        finals.append(agent)
        records.append(result)
    _assert_same_modules(*finals)
    assert [r["native_update"] for r in records[0]["rollouts"]] == \
        [r["native_update"] for r in records[1]["rollouts"]]
    assert sum(r["f_mapped_commands"] for r in records[0]["rollouts"]) > 0
    assert optimizer_steps(finals[0])["high"] == 0 and optimizer_steps(finals[0])["low_actor"] > 0


@pytest.mark.parametrize("episode_length", [25, 40], ids=["aligned", "live-boundary"])
def test_batched_step_holds_central_snapshot_for_k_steps(tmp_path, episode_length):
    torch.set_num_threads(1)
    spec, config = _tiny_set(rollout_length=25, episode_length=episode_length)
    agent, _ = tr.new_agent(config, device=torch.device("cpu"), log_dir=tmp_path / "logs",
                            seed=spec.seed)
    seen = []
    # Legacy clear_buffers (ordinary_completed_segments = False) empties env_timers; the next
    # step() re-initialises every lane missing from it (timer 0, np.random.randint skills,
    # _reset_hidden_state_arrays_for_env) before the actor forward.  Record each such in-step
    # reset: the interaction index, the lane and whether its GRU state was nonzero before.
    in_step = [None]
    step_resets = []
    original_step = agent.step
    original_reset = agent._reset_hidden_state_arrays_for_env

    def step(*args, **kwargs):
        in_step[0] = len(seen)
        try:
            return original_step(*args, **kwargs)
        finally:
            in_step[0] = None

    def reset(env_id):
        allocated = agent.actor_hidden_np is not None   # None before the first forward
        if in_step[0] is not None and allocated:
            before = (bool(np.any(agent.actor_hidden_np[env_id] != 0)),
                      bool(np.any(agent.critic_hidden_np[env_id] != 0)))
        original_reset(env_id)
        if in_step[0] is not None:
            if allocated:
                assert not np.any(agent.actor_hidden_np[env_id])
                assert not np.any(agent.critic_hidden_np[env_id])
            step_resets.append((in_step[0], int(env_id), before if allocated else None))

    agent.step = step
    agent._reset_hidden_state_arrays_for_env = reset

    def observe(agent, step_data, step):
        seen.append((agent._central_snapshot_states[:spec.lanes].copy(),
                     np.asarray([agent.env_timers.get(lane) for lane in range(spec.lanes)]),
                     agent.actor_hidden_np[:spec.lanes].copy()))

    result = tr.collect_and_train(agent, agent.config, spec, feedback=True, observe_step=observe)
    previous = np.zeros_like(seen[0][0])
    decided_steps = []
    for index, (snapshot, timers, _) in enumerate(seen):
        changed = np.any(snapshot != previous, axis=1)
        np.testing.assert_array_equal(changed, timers == 0, err_msg=f"interaction {index}")
        decided_steps.append(np.flatnonzero(timers == 0).tolist())
        previous = snapshot
    # The snapshot is refreshed exactly at episode steps 0, 10, 20, ... (hmasd/agent.py
    # ``_batched_assign_skills``: ``env_steps % k == 0 | dones``).  With a lane live at the
    # rollout boundary the legacy clear (forced by ordinary_completed_segments = False) empties
    # ``env_timers`` but the cadence stays on the episode step: no extra refresh at step 25.
    expected = [[0, 1] if (index % episode_length) % 10 == 0 else [] for index in range(len(seen))]
    assert decided_steps == expected
    live = [r["live_lanes_at_boundary"] for r in result["rollouts"]]
    # Both lanes are re-initialised inside step() at the first interaction and at the first
    # interaction after the rollout boundary (index 25), in both cases.
    assert sorted({(index, lane) for index, lane, _ in step_resets}) == \
        [(0, 0), (0, 1), (25, 0), (25, 1)]
    boundary = {lane: before for index, lane, before in step_resets if index == 25}
    # The GRU state the actor carried out of interaction 24 was nonzero in both cases.
    assert all(np.any(seen[24][2][lane]) for lane in range(spec.lanes))
    if episode_length == 25:
        # Aligned: both lanes ended at step 24 and were reset as new episodes before the
        # boundary, so the in-step re-init zeroes nothing mid-episode.
        assert live == [0, 0]
        assert boundary == {0: (False, False), 1: (False, False)}
    else:
        assert live[0] == 2 and result["rollouts"][0]["live_lane_timers_reset_by_clear"] == 2
        timers = [t.tolist() for _, t, _ in seen]
        assert timers[24] == [4, 4] and timers[25] == [1, 1] and timers[30] == [0, 0]
        # Live at the boundary: the step-25 agent.step zeroes a nonzero mid-episode actor and
        # critic GRU state before the actor forward (episode step 25, not an episode start).
        assert boundary == {0: (True, True), 1: (True, True)}
