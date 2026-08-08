"""Focused tests for the EOCIV sibling environment."""

import numpy as np
import pytest

from envs.continuous_roster import runtime_capacity as roster_env
from experiments.candidates.eociv_lite import sibling_env as sib

MASTER_SEED = 20260807
SIBLING_SEED = 90731
PROFILE = roster_env.TRAIN_PROFILES[0]


def _ledger(episode_id: int = 0):
    return roster_env.make_ledger(episode_id, master_seed=MASTER_SEED, profile=PROFILE)


def _drive_to(env, time: int) -> None:
    while env.time < time:
        env.step(roster_env.constructive_actions(env.observe()))


class TestLifecycleFsm:
    def test_full_episode_epochs(self):
        env = sib.EocivSiblingRosterEnv(_ledger(), sibling_seed=SIBLING_SEED)
        _drive_to(env, roster_env.HORIZON)
        ledger = env.ledger
        # Initial members that never left hold spell epoch 1.
        stayed = set(ledger.initial_keys) - set(ledger.temporarily_absent)
        for key in stayed:
            assert env._fsm.receipt(key, 47).spell_epoch == 1
        # Temporarily absent members rejoined: epoch 2.
        for key in ledger.temporarily_absent:
            assert env._fsm.receipt(key, 47).spell_epoch == 2
        # Fresh joiners: epoch 1, opened at t=24.
        for key in ledger.fresh_join:
            receipt = env._fsm.receipt(key, 47)
            assert receipt.spell_epoch == 1 and receipt.opened_at == 24

    def test_fsm_fail_closed(self):
        fsm = sib.LifecycleFsm(4)
        with pytest.raises(sib.LifecycleError):
            fsm.apply(roster_env.MembershipChange(temporarily_left=(0,)), 12)
        fsm.apply(roster_env.MembershipChange(joined=(0,)), 0)
        with pytest.raises(sib.LifecycleError):
            fsm.apply(roster_env.MembershipChange(joined=(0,)), 1)
        with pytest.raises(sib.LifecycleError):
            fsm.apply(roster_env.MembershipChange(rejoined=(0,)), 2)
        fsm.apply(roster_env.MembershipChange(temporarily_left=(0,)), 12)
        with pytest.raises(sib.LifecycleError):
            fsm.apply(roster_env.MembershipChange(joined=(0,)), 24)
        fsm.apply(roster_env.MembershipChange(rejoined=(0,)), 24)
        assert fsm.receipt(0, 24).spell_epoch == 2

    def test_age_is_not_the_epoch(self):
        # Pro's correction: rejoined members retain age; fresh joins reset it.
        # The FSM's epochs must disagree with any age-derived notion.
        env = sib.EocivSiblingRosterEnv(_ledger(), sibling_seed=SIBLING_SEED)
        _drive_to(env, 25)
        rejoined = env.ledger.temporarily_absent[0]
        fresh = env.ledger.fresh_join[0]
        assert env._fsm.receipt(rejoined, 24).spell_epoch == 2
        assert env._fsm.receipt(fresh, 24).spell_epoch == 1
        # Both were (re)activated at t=24, but their base-env ages differ.
        assert env._base.age[rejoined] != env._base.age[fresh]


class TestShockModel:
    def test_cell_classes_and_states(self):
        env = sib.EocivSiblingRosterEnv(_ledger(), sibling_seed=SIBLING_SEED)
        assert sib.CELL_CLASS == ("CRITICAL", "NEUTRAL", "CRITICAL")
        states = env._shock_states
        assert states[1] == sib.SHOCK_NONE
        assert states[0] in (sib.SHOCK_A, sib.SHOCK_B)
        assert states[2] in (sib.SHOCK_A, sib.SHOCK_B)
        # Measured draw for episode 0 under the registered seeds.
        assert states == (sib.SHOCK_A, sib.SHOCK_NONE, sib.SHOCK_B)

    def test_shock_not_disclosed_in_observations(self):
        forced_a = sib.EocivSiblingRosterEnv(
            _ledger(), sibling_seed=SIBLING_SEED, shock_states=("A", "NONE", "A")
        )
        forced_b = sib.EocivSiblingRosterEnv(
            _ledger(), sibling_seed=SIBLING_SEED, shock_states=("B", "NONE", "B")
        )
        for env in (forced_a, forced_b):
            _drive_to(env, 12)
        view_a, view_b = forced_a.observe(), forced_b.observe()
        assert np.array_equal(view_a.observations, view_b.observations)
        assert view_a.load == view_b.load and view_a.target_mix == view_b.target_mix

    def test_shock_changes_reward(self):
        rewards = {}
        for state in (sib.SHOCK_A, sib.SHOCK_B):
            env = sib.EocivSiblingRosterEnv(
                _ledger(), sibling_seed=SIBLING_SEED,
                shock_states=(state, "NONE", state),
            )
            _drive_to(env, 13)
            rewards[state] = env.reward_trace[12]
        assert rewards[sib.SHOCK_A] != rewards[sib.SHOCK_B]

    def test_forced_states_respect_cell_classes(self):
        with pytest.raises(ValueError):
            sib.EocivSiblingRosterEnv(
                _ledger(), sibling_seed=SIBLING_SEED, shock_states=("A", "A", "A")
            )
        with pytest.raises(ValueError):
            sib.EocivSiblingRosterEnv(
                _ledger(), sibling_seed=SIBLING_SEED, shock_states=("NONE", "NONE", "A")
            )

    def test_pre_event_segment_unshocked(self):
        env = sib.EocivSiblingRosterEnv(_ledger(), sibling_seed=SIBLING_SEED)
        for time in range(12):
            assert env.shock_state_at(time) == sib.SHOCK_NONE


class TestOpportunity:
    def test_measured_primary_identity(self):
        env = sib.EocivSiblingRosterEnv(_ledger(), sibling_seed=SIBLING_SEED)
        _drive_to(env, 12)
        opportunity = env.opportunity(0)
        assert opportunity.identity == sib.EdgeIdentity(
            episode_id=0,
            receiver_member_key=1,
            receiver_active_spell_epoch=1,
            source_member_key=2,
            source_active_spell_epoch=1,
            lifecycle_event_index=0,
        )
        assert opportunity.eligible and opportunity.cell_class == "CRITICAL"
        assert opportunity.cluster_id == "ep0-ev0"

    def test_opportunity_only_at_the_boundary(self):
        env = sib.EocivSiblingRosterEnv(_ledger(), sibling_seed=SIBLING_SEED)
        _drive_to(env, 11)
        with pytest.raises(RuntimeError):
            env.opportunity(0)
        _drive_to(env, 13)
        with pytest.raises(RuntimeError):
            env.opportunity(0)

    def test_receiver_differs_from_source(self):
        for episode_id in range(8):
            env = sib.EocivSiblingRosterEnv(
                _ledger(episode_id), sibling_seed=SIBLING_SEED
            )
            for event_index, tick in enumerate(sib.EVENT_TIMES):
                _drive_to(env, tick)
                opportunity = env.opportunity(event_index)
                identity = opportunity.identity
                assert identity.receiver_member_key != identity.source_member_key


class TestActuation:
    def _opportunity(self):
        env = sib.EocivSiblingRosterEnv(_ledger(), sibling_seed=SIBLING_SEED)
        _drive_to(env, 12)
        return env, env.opportunity(0)

    def test_arm_routes(self):
        env, opportunity = self._opportunity()
        body = env.focal_payload(0)
        for arm, d_l, d_c, route, source in (
            ("LS", True, False, "REAL", "D_L"),
            ("LS", False, True, "NEUTRAL", "D_L"),
            ("CS", False, True, "REAL", "D_C"),
            ("CS", True, False, "NEUTRAL", "D_C"),
            ("LR", False, False, "REAL", "ALWAYS_REAL"),
            ("CR", False, False, "REAL", "ALWAYS_REAL"),
        ):
            actuation = sib.actuate(arm, opportunity, body, d_learned=d_l, d_control=d_c)
            assert (actuation.route, actuation.decision_source) == (route, source)
            assert len(actuation.slot) == sib.PAYLOAD_SLOT_BYTES

    def test_neutral_token_carries_nothing(self):
        env, opportunity = self._opportunity()
        neutral = sib.actuate(
            "LS", opportunity, env.focal_payload(0), d_learned=False, d_control=False
        )
        assert neutral.body == sib.NEUTRAL_TOKEN
        assert b"SIGNAL" not in neutral.body
        assert neutral.ingestion_cost == sib.INGESTION_COST

    def test_suppressed_when_ineligible(self):
        env, opportunity = self._opportunity()
        blocked = sib.Opportunity(
            identity=opportunity.identity,
            physical_tick=opportunity.physical_tick,
            cell_class=opportunity.cell_class,
            cluster_id=opportunity.cluster_id,
            receiver_receipt=opportunity.receiver_receipt,
            source_receipt=opportunity.source_receipt,
            eligible=False,
            ineligibility_reason="just_departed_owner_suppressed",
        )
        actuation = sib.actuate(
            "LR", blocked, env.focal_payload(0), d_learned=True, d_control=True
        )
        assert (actuation.route, actuation.decision_source) == ("SUPPRESSED", "G=0")

    def test_payload_bodies(self):
        assert sib.real_payload_body("A") == b"EOCIV-SIGNAL:A"
        with pytest.raises(ValueError):
            sib.real_payload_body("Z")
        assert sib.NEUTRAL_TOKEN != sib.PATTERN_TOKEN


class TestControlTape:
    def test_tape_is_deterministic_and_body_free(self):
        first = sib.control_tape_open(3, 1, tape_seed=41211)
        second = sib.control_tape_open(3, 1, tape_seed=41211)
        assert first == second
        import inspect

        parameters = inspect.signature(sib.control_tape_open).parameters
        assert set(parameters) == {"episode_id", "event_index", "tape_seed"}


class TestDisabledProjection:
    def test_disabled_matches_base_full_episode(self):
        ledger = _ledger(5)
        base = roster_env.RuntimeCapacityRosterEnv(ledger)
        disabled = sib.EocivSiblingRosterEnv(
            ledger, sibling_seed=SIBLING_SEED, intervention_enabled=False
        )
        for _ in range(roster_env.HORIZON):
            view = base.observe()
            assert np.array_equal(view.observations, disabled.observe().observations)
            actions = roster_env.constructive_actions(view)
            assert base.step(actions)[0] == disabled.step(actions)[0]
        assert base.outcome().reward_trace == tuple(disabled.reward_trace)

    def test_disabled_projection_has_no_payload_channel(self):
        disabled = sib.EocivSiblingRosterEnv(
            _ledger(), sibling_seed=SIBLING_SEED, intervention_enabled=False
        )
        with pytest.raises(RuntimeError):
            disabled.focal_payload(0)

    def test_enabled_bookkeeping_matches_base_semantics(self):
        # The enabled step() mirrors the base env's advancement tail inline
        # (only the reward target differs).  This drift test pins that mirror:
        # driven with identical actions, the enabled sibling's base bookkeeping
        # must equal a disabled run's, even though the reward traces differ.
        ledger = _ledger(3)
        enabled = sib.EocivSiblingRosterEnv(ledger, sibling_seed=SIBLING_SEED)
        disabled = sib.EocivSiblingRosterEnv(
            ledger, sibling_seed=SIBLING_SEED, intervention_enabled=False
        )
        for _ in range(roster_env.HORIZON):
            actions = roster_env.constructive_actions(disabled.observe())
            enabled.step(actions)
            disabled.step(actions)
        assert enabled._base.time == disabled._base.time == roster_env.HORIZON
        assert np.array_equal(enabled._base.age, disabled._base.age)
        assert np.array_equal(
            enabled._base.previous_actions, disabled._base.previous_actions
        )
        assert enabled._base.roster_sizes == disabled._base.roster_sizes
        assert enabled._base._terminated and disabled._base._terminated
        # The shock is real: the traces themselves must differ...
        assert tuple(enabled.reward_trace) != tuple(disabled.reward_trace)
        # ...but only inside shocked (critical) segments.
        assert enabled.reward_trace[:12] == disabled.reward_trace[:12]
        assert enabled.reward_trace[24:36] == disabled.reward_trace[24:36]
