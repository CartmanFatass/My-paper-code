"""Counted native facade; model reconstruction accepts public state only.

No host is constructed at import. Native dynamics/RF methods remain inherited.
"""
from copy import deepcopy

import numpy as np

from experiments.candidates.coupled_host_joint_skills_stage1.host import (
    CoupledRelayHost, ContractError, HOST_CONTRACT_KWARGS)
from experiments.candidates.uav_decision_generalization.b03_joint_window.adapter import (
    RegisteredHost, snapshot as host_snapshot)
from experiments.candidates.uav_decision_generalization.b03_joint_window.task import world_registry

from .contract import HORIZON, NATIVE_EVENT_NAMES
from .task import PublicState, _array, _integer, slot_positions, steer


def check_request_contract(host):
    """B03 constants, with H1200 declared before construction."""
    expected = {
        "channel_model": "free_space", "max_connections": 10,
        "noise_power": -80, "tx_power": 23, "min_sinr": 3,
        "carrier_frequency": 2e9, "bandwidth": 20e6,
        "ground_bs_tx_power": 23, "n_uavs": 6, "n_users": 50,
        "n_ground_bs": 1, "max_hops": 3, "use_fdma": True,
        "user_distribution": "cluster", "max_steps": HORIZON,
        "paper_reward": False, "use_shadowing": False,
        "area_size": 5000, "max_speed": 30, "time_step": 1.0,
        "height_range": (50, 150), "a2a_enabled": True,
    }
    failed = {name: (getattr(host, name), value) for name, value in expected.items()
              if getattr(host, name) != value}
    if failed:
        raise ContractError(f"request host contract violated (actual, declared): {failed}")
    if (host.ground_bs_positions.shape != (1, 3)
            or not np.array_equal(host.ground_bs_positions, [[2500., 2500., 30.]])):
        raise ContractError("request host BS must be at (2500,2500,30)")
    if not np.asarray(host.transmitter_mask).all():
        raise ContractError("all six transmitters must remain on")


class NativeCounts(dict):
    """A numerical event sink survives model cancellation without new physics."""
    def __init__(self, values, sink=None):
        super().__init__(values)
        self.sink = sink

    def __setitem__(self, key, value):
        before = self.get(key, 0)
        super().__setitem__(key, value)
        if self.sink is not None and value != before:
            self.sink(key, int(value - before))

    def __deepcopy__(self, memo):
        # A function sink owns the same parent-created numerical trace; copying
        # a public native model never copies a live memmap or emits new events.
        return NativeCounts(dict(self), self.sink)


class RequestHost(RegisteredHost):
    def __init__(self, world, public_state=None, event_sink=None):
        world = _integer(world, "world", 0, 2**63-1)
        if public_state is not None:
            if not isinstance(public_state, PublicState) or public_state.world != world:
                raise TypeError("model construction requires matching PublicState")
            positions = public_state.positions
            if (np.any(positions[:, :2] < 0) or np.any(positions[:, :2] > 5000)
                    or np.any(positions[:, 2] < 50) or np.any(positions[:, 2] > 150)):
                raise ValueError("public UAV positions outside native arena")
        self._public_model = public_state is not None
        # Retain only public geometry for the constructor hook, not the state
        # object, queue data, an actual wrapper, or any RNG/arrival suffix.
        self._initial_positions = None if public_state is None else public_state.positions.copy()
        self._initial_users = None if public_state is None else public_state.users.copy()
        self.event_counts = NativeCounts(dict.fromkeys(NATIVE_EVENT_NAMES, 0), event_sink)
        self.event_counts['constructor_calls'] += 1
        self.registry = None
        kwargs = dict(HOST_CONTRACT_KWARGS, max_steps=HORIZON)
        CoupledRelayHost.__init__(self, area_size=5000, seed=world, **kwargs)
        # Scenario2.__init__ clears links/routes after its dynamically dispatched
        # reset. Restore those same completed reset facts, without RF recompute.
        links, bs_links, paths = self._completed_reset_topology
        self.uav_connections = links
        self.uav_bs_connections = bs_links
        self.routing_paths = paths
        del self._completed_reset_topology
        self.event_counts["constructor_topology_restorations"] += 1
        check_request_contract(self)
        if public_state is not None:
            self.current_step = public_state.tick
            if not np.array_equal(self.ack(), public_state.ack):
                raise ValueError("public ACK differs from reconstructed native routing")

    def reset(self, seed=None, options=None):
        seed = _integer(seed, "reset world", 0, 2**63-1)
        if self._public_model and seed != self.world_seed:
            raise ValueError("public model cannot reset to another world")
        if not self._public_model:
            self.event_counts["registry_calls"] += 1
            self.registry = world_registry(seed)
        self.event_counts["reset_calls"] += 1
        result = CoupledRelayHost.reset(self, seed=seed, options=options)
        self._completed_reset_topology = (
            self.uav_connections.copy(), self.uav_bs_connections.copy(),
            deepcopy(self.routing_paths))
        return result

    def _generate_user_positions(self):
        if self._public_model:
            # The parent has drawn initial UAV positions already; overwrite
            # here, before its first path-loss/channel-state update.
            self.uav_positions = self._initial_positions.copy()
            return self._initial_users.astype(np.float64)
        return self.registry[0].astype(np.float64)

    def _begin_path_loss_step(self):
        self.event_counts["physical_state_update_attempts"] += 1
        return super()._begin_path_loss_step()

    def _update_channel_state(self, *args, **kwargs):
        self.event_counts["channel_state_update_attempts"] += 1
        return super()._update_channel_state(*args, **kwargs)

    def _update_uav_connections(self):
        self.event_counts["link_update_attempts"] += 1
        return super()._update_uav_connections()

    def _compute_routing_paths(self):
        self.event_counts["routing_update_attempts"] += 1
        return super()._compute_routing_paths()

    def snapshot(self):
        return host_snapshot(self, full=True)

    def ack(self):
        routed = np.array(sorted(self.routing_paths), dtype=np.int64)
        if not len(routed):
            return np.zeros(50, dtype=bool)
        return np.asarray(self.connections[routed], dtype=bool).any(axis=0)

    def advance(self, slots, users):
        """Return copied (raw float64[6,3], executed float64[6,3], full snapshot)."""
        before = _integer(self.current_step, "native clock", 0, HORIZON-1)
        users = _array(users, np.int32, (50, 2), "users")
        if not np.array_equal(self.user_positions, users):
            raise ValueError("executor users differ from native static map")
        slots = _array(slots, np.uint8, (6,), "slots")
        targets = slot_positions(users, slots)
        actions = steer(self.uav_positions, targets)
        _, _, terminated, truncated, _ = self.step(
            {agent: actions[i].copy() for i, agent in enumerate(self.possible_agents)})
        if self.current_step != before+1:
            raise ValueError("native clock failed to advance by exactly one")
        agents = set(self.possible_agents)
        if (set(terminated) != agents or set(truncated) != agents
                or any(bool(value) for value in truncated.values())
                or any(bool(value) != (self.current_step == HORIZON)
                       for value in terminated.values())):
            raise ValueError("native termination must occur exactly at1200, without truncation")
        return self.last_raw_actions.copy(), self.last_executed_actions.copy(), self.snapshot()


def from_public_state(state, event_sink=None):
    if not isinstance(state, PublicState):
        raise TypeError("only PublicState may enter native model reconstruction")
    return RequestHost(state.world, public_state=state, event_sink=event_sink)


def clone_public_host(host):
    """Copy only an explicitly public-reconstructed native model, never task state."""
    if not isinstance(host, RequestHost) or not host._public_model:
        raise TypeError("only a public-reconstructed RequestHost can be cloned")
    host.event_counts["public_clone_calls"] += 1
    result = deepcopy(host)
    # This clone performs no native constructor/reset/RF work of its own.
    result.event_counts = NativeCounts(dict.fromkeys(host.event_counts, 0),
                                      getattr(host.event_counts, 'sink', None))
    return result
