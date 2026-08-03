from __future__ import annotations

from copy import deepcopy

import numpy as np

from ha_ctse_process.dynamic_roster_clean_process_testbed import (
    CleanProcessDynamicRosterEnv,
    audit_clean_process_contract,
    make_clean_process_dynamic_roster_ledger,
)
from ha_ctse_process.dynamic_roster_testbed import (
    HORIZON,
    GenericShortDynamicRosterEnv,
    constructive_actions,
)
from scripts.run_clean_process_direct_access import (
    run_clean_process_qualification,
)


def test_clean_process_channel_is_task_neutral_and_lifecycle_owned() -> None:
    assert all(audit_clean_process_contract().values())

    ledger = make_clean_process_dynamic_roster_ledger(7, master_seed=12_345)
    clean = CleanProcessDynamicRosterEnv(ledger)
    reference = GenericShortDynamicRosterEnv(deepcopy(ledger))
    absent_state: dict[int, np.ndarray] = {}

    for time_index in range(HORIZON):
        clean_view = clean.observe()
        reference_view = reference.observe()
        assert clean_view.active_keys == reference_view.active_keys
        assert np.array_equal(clean_view.observations, reference_view.observations)

        if time_index == 20:
            absent_state = {
                key: clean.process_states[key].copy()
                for key in ledger.temporary_leave
            }
        if 20 <= time_index < 40:
            for key, expected in absent_state.items():
                assert np.array_equal(clean.process_states[key], expected)
        if time_index == 40:
            for key, expected in absent_state.items():
                assert np.array_equal(clean.process_states[key], expected)
            for key in (4, 5):
                assert np.array_equal(clean.process_states[key], np.zeros(2))

        actions = constructive_actions(clean, clean_view)
        clean_reward, clean_terminal, _ = clean.step(actions)
        reference_reward, reference_terminal, _ = reference.step(actions)
        assert clean_reward == reference_reward
        assert clean_terminal == reference_terminal

        if time_index == 40:
            for key, expected in absent_state.items():
                assert not np.array_equal(clean.process_states[key], expected)

        if time_index == 24:
            snapshot = clean.snapshot_state()
            restored = CleanProcessDynamicRosterEnv.from_snapshot_state(snapshot)
            assert restored.time == clean.time
            assert restored.active_keys == clean.active_keys
            assert restored.persistent_units == clean.persistent_units
            assert restored.short_completed_total == clean.short_completed_total
            assert restored.reward_trace == clean.reward_trace
            for key in clean.process_states:
                assert np.array_equal(
                    restored.process_states[key], clean.process_states[key]
                )


def test_clean_process_direct_runner_smoke(tmp_path) -> None:
    result = run_clean_process_qualification(
        output_root=tmp_path / "clean-process-smoke",
        device_name="cpu",
        num_envs=2,
        updates=1,
        eval_episodes=4,
        smoke=True,
    )

    assert result["status"] == "SMOKE_COMPLETE"
    assert result["implementation_valid"] is True
    assert all(result["carrier_audit"].values())
    assert result["contract"]["environment_transitions"] == 160
    assert result["contract"]["optimizer_steps"] == 4
    assert result["direct"]["counts"]["environment_steps"] == 160
    assert result["direct"]["counts"]["optimizer_steps"] == 4
    assert result["direct"]["counts"]["skill_updates"] == 0
    assert result["direct"]["counts"]["high_updates"] == 0
    assert result["direct"]["counts"]["intrinsic_reward_reads"] == 0
    assert max(result["direct"]["replay"].values()) <= 1e-6
    assert result["process_channel"] == {
        "fields": ["actuator_position", "actuator_velocity"],
        "input_to_actor": False,
        "input_to_critic": False,
        "input_to_reward": False,
        "input_to_gae_or_ppo": False,
    }
