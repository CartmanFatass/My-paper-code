"""Mock-only native plumbing; no scientific map draw or RF computation."""
from dataclasses import replace

import numpy as np
import pytest

from experiments.candidates.uav_decision_generalization.b05_request_schedule import native
from experiments.candidates.uav_decision_generalization.b05_request_schedule.task import (
    PublicState, slot_positions, steer)


def users():
    return np.repeat(np.array([[2500, 2500], [500, 500], [4500, 500],
                               [4500, 4500], [500, 4500]], dtype=np.int32), 10, axis=0)


def public(tick=20):
    slots = np.arange(6, dtype=np.uint8)
    positions = slot_positions(users(), slots) + [123.4567890123, 0, 0]
    ack = np.zeros(50, bool)
    ack[10:20] = True
    return PublicState(123, tick, users(), np.array([6, 3, 2, 1]), positions,
                       ack, np.zeros(4, int), np.zeros(4, int), slots,
                       ((0, 1), (2, 3), (4, 5)))


@pytest.fixture
def mocked_physics(monkeypatch):
    events = []

    def constructor(self, **kwargs):
        events.append(("constructor", kwargs.copy()))
        for name, value in kwargs.items():
            setattr(self, name, value)
        self.world_seed = kwargs["seed"]
        self.noise_power = -80
        self.tx_power = 23
        self.carrier_frequency = 2e9
        self.paper_reward = False
        self.a2a_enabled = True
        self.ground_bs_positions = np.array([[2500., 2500., 30.]])
        self.possible_agents = [f"uav_{i}" for i in range(6)]
        self._transmitter_mask = np.ones(6, bool)
        self.reset(seed=kwargs["seed"])
        # Reproduce the actual post-reset constructor overwrite.
        self.uav_connections = np.zeros((6, 6), bool)
        self.uav_bs_connections = np.zeros((6, 1), bool)
        self.routing_paths = {}

    def reset(self, seed=None, options=None):
        events.append(("reset", seed))
        self.current_step = 0
        self.uav_positions = np.full((6, 3), 100.0)
        self.user_positions = self._generate_user_positions()
        self._begin_path_loss_step()
        self._update_channel_state()
        self._update_uav_connections()
        self._compute_routing_paths()
        return {}, {}

    def begin(self):
        events.append(("physical", self.uav_positions.copy(), self.user_positions.copy()))

    def channel(self, *args, **kwargs):
        events.append(("channel", self.uav_positions.copy(), self.user_positions.copy()))
        self.connections = np.zeros((6, 50), bool)
        self.connections[0, 10:20] = True
        self.connections[1, 20:30] = True  # This UAV has no route.
        self.sinr_matrix = np.arange(300, dtype=np.float64).reshape(6, 50)
        self.uav_sinr_matrix = np.arange(36, dtype=np.float64).reshape(6, 6)

    def links(self):
        self.uav_connections = np.eye(6, dtype=bool)
        self.uav_bs_connections = np.zeros((6, 1), bool)
        self.uav_bs_connections[0, 0] = True

    def routes(self):
        self.routing_paths = {0: [("uav", 0), ("ground_bs", 0)]}

    def step(self, actions):
        for i, agent in enumerate(self.possible_agents):
            action = actions[agent].copy()
            assert action.dtype == np.float64
            norm = np.linalg.norm(action)
            if norm > 1:
                action /= norm
            self.uav_positions[i] += 30*action
        self._begin_path_loss_step()
        self._update_channel_state()
        self._update_uav_connections()
        self._compute_routing_paths()
        self.current_step += 1
        done = {a: self.current_step >= self.max_steps for a in self.possible_agents}
        trunc = {a: False for a in self.possible_agents}
        return {}, {}, done, trunc, {}

    def registry(seed):
        events.append(("registry", seed))
        return users(), np.arange(4, dtype=np.uint8), np.zeros(404, np.uint8)

    for method, replacement in (("__init__", constructor), ("reset", reset),
                                ("_begin_path_loss_step", begin),
                                ("_update_channel_state", channel),
                                ("_update_uav_connections", links),
                                ("_compute_routing_paths", routes), ("step", step)):
        monkeypatch.setattr(native.CoupledRelayHost, method, replacement)
    monkeypatch.setattr(native, "world_registry", registry)
    return events


def test_public_installed_before_first_mock_channel_and_topology_restored(mocked_physics):
    state = public()
    host = native.from_public_state(state)
    assert host.max_steps == 1200 and host.current_step == 20
    assert not any(event[0] == "registry" for event in mocked_physics)
    constructor = mocked_physics[0][1]
    assert constructor["max_steps"] == 1200
    assert native.HOST_CONTRACT_KWARGS["max_steps"] == 500
    for event in mocked_physics:
        if event[0] in ("physical", "channel"):
            np.testing.assert_array_equal(event[1], state.positions)
            np.testing.assert_array_equal(event[2], state.users)
    np.testing.assert_array_equal(host.ack(), state.ack)
    assert host.routing_paths == {0: [("uav", 0), ("ground_bs", 0)]}
    assert host.event_counts["constructor_calls"] == host.event_counts["reset_calls"] == 1
    for name in ("physical_state_update_attempts", "channel_state_update_attempts",
                 "link_update_attempts", "routing_update_attempts", "constructor_topology_restorations"):
        assert host.event_counts[name] == 1


def test_actual_facade_reuses_registry_mock_and_ack_has_only_routed_users(mocked_physics):
    host = native.RequestHost(123)
    assert host.event_counts["registry_calls"] == 1
    assert any(event[0] == "registry" for event in mocked_physics)
    np.testing.assert_array_equal(host.user_positions, users())
    assert host.ack().sum() == 10 and not host.ack()[20:30].any()
    host.routing_paths = {}
    assert not host.ack().any()


def test_snapshot_is_full_and_copied_without_mock_native_updates(mocked_physics):
    host = native.from_public_state(public())
    before = host.event_counts.copy()
    result = host.snapshot()
    assert set(result) == {"positions", "connections", "routes", "route_lengths",
                           "transmitter_mask", "user_sinr", "uav_sinr",
                           "uav_connections", "bs_connections"}
    assert result["routes"][0, :2].tolist() == [0, 6]
    assert result["route_lengths"][0] == 2
    for value in result.values():
        value[:] = 0
    assert host.connections[0, 10] and host.uav_bs_connections[0, 0]
    assert host.routing_paths[0] == [("uav", 0), ("ground_bs", 0)]
    assert host.event_counts == before


def test_advance_float64_true_position_actions_and_exact_clock(mocked_physics):
    state = public(1199)
    host = native.from_public_state(state)
    targets = slot_positions(state.users, state.active_slots)
    expected = steer(state.positions, targets)
    raw, executed, result = host.advance(state.active_slots, state.users)
    np.testing.assert_array_equal(raw, expected)
    assert raw.dtype == executed.dtype == np.float64
    np.testing.assert_allclose(result["positions"], state.positions+30*executed, rtol=0, atol=0)
    assert host.current_step == 1200
    assert host.event_counts["native_step_calls"] == host.event_counts["native_steps"] == 1
    with pytest.raises(ValueError):
        host.advance(state.active_slots, state.users)
    assert host.event_counts["native_step_calls"] == 1


@pytest.mark.parametrize("defect", ["early_done", "missing_done", "truncate", "clock"])
def test_advance_rejects_mock_termination_or_clock_defect(mocked_physics, monkeypatch, defect):
    host = native.from_public_state(public())
    original = native.CoupledRelayHost.step

    def bad_step(self, actions):
        obs, reward, done, trunc, info = original(self, actions)
        if defect == "early_done":
            done["uav_0"] = True
        elif defect == "missing_done":
            del done["uav_0"]
        elif defect == "truncate":
            trunc["uav_0"] = True
        else:
            self.current_step += 1
        return obs, reward, done, trunc, info

    monkeypatch.setattr(native.CoupledRelayHost, "step", bad_step)
    with pytest.raises(ValueError):
        host.advance(public().active_slots, users())
    assert host.event_counts["native_step_calls"] == 1
    assert host.event_counts["native_steps"] == (2 if defect == "clock" else 1)


def test_only_public_reconstruction_and_tagged_model_clone(mocked_physics):
    model = native.from_public_state(public())
    before = len(mocked_physics)
    clone = native.clone_public_host(model)
    assert len(mocked_physics) == before
    assert model.event_counts["public_clone_calls"] == 1
    assert all(value == 0 for value in clone.event_counts.values())
    assert clone.current_step == model.current_step and clone._public_model
    clone.uav_positions[:] = 0
    assert np.any(model.uav_positions != 0)
    for wrong in (object(), {"world": 123}, native.RequestHost(123)):
        with pytest.raises(TypeError):
            native.from_public_state(wrong)
        with pytest.raises(TypeError):
            native.clone_public_host(wrong)


def test_public_mismatch_and_bad_geometry_refused(mocked_physics):
    with pytest.raises(TypeError):
        native.RequestHost(456, public_state=public())
    with pytest.raises(ValueError):
        native.from_public_state(replace(public(), ack=np.zeros(50, bool)))
    before = len(mocked_physics)
    with pytest.raises(ValueError):
        native.from_public_state(replace(public(), positions=np.full((6, 3), 9999.0)))
    assert len(mocked_physics) == before


def test_contract_rejects_frozen500_without_mutating_host(mocked_physics):
    host = native.from_public_state(public())
    host.max_steps = 500
    with pytest.raises(native.ContractError):
        native.check_request_contract(host)
    assert host.max_steps == 500
    host.max_steps = 1200
    host.noise_power = -70
    with pytest.raises(native.ContractError):
        native.check_request_contract(host)
