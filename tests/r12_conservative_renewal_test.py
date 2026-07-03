from ha_ctse_process.situation_hazard import (
    ConservativeRenewalConfig,
    ConservativeRenewalGate,
    should_force_renewal,
)


def test_should_force_renewal_respects_guard_allowed():
    assert should_force_renewal(
        mode="oracle_change",
        situation_changed=True,
        skill_age=20,
        min_age=10,
        hazard_action=0,
        guard_allowed=True,
    )
    assert not should_force_renewal(
        mode="oracle_change",
        situation_changed=True,
        skill_age=20,
        min_age=10,
        hazard_action=0,
        guard_allowed=False,
    )


def test_conservative_gate_blocks_until_confirmed_change_count():
    gate = ConservativeRenewalGate(
        num_envs=1,
        n_agents=2,
        config=ConservativeRenewalConfig(
            enabled=True,
            min_dwell_checks=0,
            confirm_changes=2,
            max_force_rate=1.0,
            rate_window=8,
        ),
    )

    first = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=True,
        skill_age=30,
        step=10,
    )
    second = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=True,
        skill_age=40,
        step=20,
    )

    assert not first.allowed
    assert first.block_reason == "confirm"
    assert second.allowed
    assert second.block_reason == "allow"


def test_conservative_gate_blocks_until_min_dwell_checks():
    gate = ConservativeRenewalGate(
        num_envs=1,
        n_agents=1,
        config=ConservativeRenewalConfig(
            enabled=True,
            min_dwell_checks=3,
            confirm_changes=1,
            max_force_rate=1.0,
            rate_window=8,
        ),
    )

    blocked = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=True,
        skill_age=30,
        step=10,
        stable_count=2,
    )
    allowed = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=True,
        skill_age=40,
        step=20,
        stable_count=3,
    )

    assert not blocked.allowed
    assert blocked.block_reason == "dwell"
    assert allowed.allowed


def test_pending_confirmed_change_renews_after_changed_pulse_ends():
    gate = ConservativeRenewalGate(
        num_envs=1,
        n_agents=1,
        config=ConservativeRenewalConfig(
            enabled=True,
            min_dwell_checks=2,
            confirm_changes=2,
            max_force_rate=1.0,
            rate_window=8,
        ),
    )

    first = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=True,
        skill_age=30,
        step=10,
        stable_count=1,
    )
    second = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=False,
        skill_age=40,
        step=20,
        stable_count=2,
    )

    assert not first.allowed
    assert first.block_reason == "dwell"
    assert first.renewal_signal
    assert second.allowed
    assert second.block_reason == "allow"
    assert second.renewal_signal
    assert should_force_renewal(
        mode="oracle_change",
        situation_changed=second.renewal_signal,
        skill_age=40,
        min_age=10,
        hazard_action=0,
        guard_allowed=second.allowed,
    )


def test_pending_change_is_carried_while_min_age_blocks_renewal():
    gate = ConservativeRenewalGate(
        num_envs=1,
        n_agents=1,
        config=ConservativeRenewalConfig(
            enabled=True,
            min_dwell_checks=0,
            confirm_changes=2,
            max_force_rate=1.0,
            rate_window=8,
        ),
    )

    first = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=True,
        skill_age=1,
        step=10,
    )
    first_forced = should_force_renewal(
        mode="oracle_change",
        situation_changed=first.renewal_signal,
        skill_age=1,
        min_age=5,
        hazard_action=0,
        guard_allowed=first.allowed,
    )
    gate.record_decision(first, forced=first_forced)

    second = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=False,
        skill_age=5,
        step=20,
    )

    assert not first.allowed
    assert first.block_reason == "confirm"
    assert first.renewal_signal
    assert not first_forced
    assert second.allowed
    assert second.renewal_signal
    assert should_force_renewal(
        mode="oracle_change",
        situation_changed=second.renewal_signal,
        skill_age=5,
        min_age=5,
        hazard_action=0,
        guard_allowed=second.allowed,
    )


def test_no_pending_no_change_is_blocked_without_renewal_signal():
    gate = ConservativeRenewalGate(
        num_envs=1,
        n_agents=1,
        config=ConservativeRenewalConfig(
            enabled=True,
            min_dwell_checks=0,
            confirm_changes=1,
            max_force_rate=1.0,
            rate_window=8,
        ),
    )

    decision = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=False,
        skill_age=30,
        step=10,
    )

    assert not decision.allowed
    assert decision.block_reason == "no_change"
    assert not decision.renewal_signal


def test_conservative_gate_rate_cap_allows_until_window_is_full():
    gate = ConservativeRenewalGate(
        num_envs=1,
        n_agents=1,
        config=ConservativeRenewalConfig(
            enabled=True,
            min_dwell_checks=0,
            confirm_changes=1,
            max_force_rate=0.25,
            rate_window=4,
        ),
    )

    first = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=True,
        skill_age=30,
        step=10,
    )
    assert first.allowed
    gate.record_decision(first, forced=True)

    for step in (20, 30, 40):
        decision = gate.check(
            env_id=0,
            agent_id=0,
            situation_changed=True,
            skill_age=30,
            step=step,
        )
        assert decision.allowed
        assert decision.block_reason == "allow"
        gate.record_decision(decision, forced=True)

    capped = gate.check(
        env_id=0,
        agent_id=0,
        situation_changed=True,
        skill_age=30,
        step=50,
    )
    assert not capped.allowed
    assert capped.block_reason == "rate_cap"
    gate.record_decision(capped, forced=False)

    metrics = gate.metrics(reset=False)
    assert metrics["situation_hazard_guard_rate_cap_block_rate"] == 0.2
    assert metrics["situation_hazard_guard_allow_rate"] == 0.8
