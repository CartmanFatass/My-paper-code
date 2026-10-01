"""Native masked host with one addressed user-link residual per physical state."""

from copy import deepcopy

import numpy as np

from envs.pettingzoo.env_adapter import ParallelToArrayAdapter
from envs.pettingzoo.uav_env import MultiUAVEnv
from . import contract as c
from .randomness import _identifier, physical_normals


class CorrelatedShadowEnv(MultiUAVEnv):
    def __init__(self, seed, *, horizon=c.HORIZON, sigma=c.SIGMA_DB):
        seed = _identifier(seed, 'seed')
        if seed >= 2**32:
            raise ValueError('native RandomState seed must be below2**32')
        if isinstance(horizon, (bool, np.bool_)) or not isinstance(horizon, (int, np.integer)) or not 8 <= horizon <= c.HORIZON or horizon % c.HOLD:
            raise ValueError('horizon must be a multiple of4 from8 to256')
        if isinstance(sigma, (bool, np.bool_)) or not np.isscalar(sigma) or not np.isfinite(sigma) or sigma < 0:
            raise ValueError('sigma must be finite and nonnegative')
        self._sigma, self._horizon = float(sigma), int(horizon)
        self._world, self._physical_tick = seed, 0
        self._residual = None
        self._physical_positions, self._physical_users = None, None
        self._lifecycle, self._pending_generation = None, False
        self._in_constructor = True
        self._constructor_reset_output = None
        names = ('constructor_calls_attempted', 'constructor_calls_completed',
                 'constructor_reset_calls_attempted', 'constructor_reset_calls_completed',
                 'explicit_reset_calls_attempted', 'explicit_reset_calls_completed',
                 'native_step_calls_attempted', 'native_step_calls_completed',
                 'physical_normal_blocks_attempted', 'physical_normal_blocks_completed',
                 'physical_normal_values_attempted', 'physical_normal_values_completed',
                 'physical_initializations', 'physical_updates')
        self._physical_counters = dict.fromkeys(names, 0)
        self._physical_counters['constructor_calls_attempted'] = 1
        try:
            super().__init__(n_uavs=c.N_UAVS, n_users=c.N_USERS, area_size=c.AREA_METRES,
                height_range=(c.MIN_HEIGHT, c.MAX_HEIGHT), max_speed=c.COMPONENT_METRES, time_step=1.,
                max_steps=self._horizon, user_distribution='uniform', channel_model='free_space',
                render_mode=None, seed=seed, max_observed_users=20, max_observed_uavs=10,
                use_shadowing=False, paper_reward=False, use_fdma=False, bandwidth=20e6,
                ground_bs_tx_power=30, step_path_loss_cache=True, channel_backend='vectorized',
                enable_transmitter_mask=True)
            self._physical_counters['constructor_calls_completed'] += 1
        finally:
            self._in_constructor = False

    @property
    def sigma(self):
        return self._sigma

    @property
    def physical_counters(self):
        return self._physical_counters.copy()

    @property
    def constructor_reset_output(self):
        return deepcopy(self._constructor_reset_output)

    def _assert_configuration(self):
        fixed = dict(n_uavs=c.N_UAVS, n_users=c.N_USERS, area_size=c.AREA_METRES,
            max_speed=c.COMPONENT_METRES, time_step=1., max_steps=self._horizon,
            user_distribution='uniform', channel_model='free_space', use_shadowing=False,
            paper_reward=False, use_fdma=False, step_path_loss_cache=True, channel_backend='vectorized',
            enable_transmitter_mask=True, carrier_frequency=c.CARRIER_HZ, tx_power=c.TRANSMIT_DBM,
            noise_power=c.NOISE_DBM, min_sinr=c.MIN_SINR_DB, max_connections=c.CAPACITY,
            max_observed_users=20, max_observed_uavs=10)
        if any(getattr(self, name) != value for name, value in fixed.items()) or tuple(self.height_range) != (c.MIN_HEIGHT, c.MAX_HEIGHT):
            raise RuntimeError('correlated host configuration was mutated')

    def _assert_physical_arrays(self):
        self._assert_configuration()
        if (self._physical_positions is None or self._physical_users is None or
            not np.array_equal(self.uav_positions, self._physical_positions) or
            not np.array_equal(self.user_positions, self._physical_users)):
            raise RuntimeError('physical geometry changed outside native reset/step')
        allowed = (self._physical_tick-1, self._physical_tick) if self._lifecycle == 'step' else (self._physical_tick,)
        if self.current_step not in allowed:
            raise RuntimeError('native and addressed physical clocks disagree')

    def _draw_physical(self, tick):
        self._physical_counters['physical_normal_blocks_attempted'] += 1
        self._physical_counters['physical_normal_values_attempted'] += c.N_UAVS*c.N_USERS
        values = physical_normals(self._world, tick)
        self._physical_counters['physical_normal_blocks_completed'] += 1
        self._physical_counters['physical_normal_values_completed'] += values.size
        if values.shape != (c.N_UAVS, c.N_USERS) or values.dtype != np.float64 or not np.isfinite(values).all():
            raise ValueError('physical normals have invalid shape/dtype/values')
        return values

    def reset(self, seed=None, options=None):
        key = 'constructor_reset' if self._in_constructor else 'explicit_reset'
        self._physical_counters[key + '_calls_attempted'] += 1
        world = self._world if seed is None else _identifier(seed, 'seed')
        if world >= 2**32:
            raise ValueError('native RandomState seed must be below2**32')
        if self._lifecycle is not None:
            raise RuntimeError('nested native lifecycle is unsupported')
        self._world, self._physical_tick = world, 0
        self._lifecycle, self._pending_generation = 'reset', True
        try:
            result = super().reset(seed=seed, options=options)
            if self._pending_generation:
                raise RuntimeError('native reset did not initialize its physical channel')
            self._assert_physical_arrays()
            if self._in_constructor:
                self._constructor_reset_output = deepcopy(result)
            self._physical_counters[key + '_calls_completed'] += 1
            return result
        finally:
            self._lifecycle, self._pending_generation = None, False

    def step(self, actions):
        self._physical_counters['native_step_calls_attempted'] += 1
        self._assert_physical_arrays()
        if self._lifecycle is not None:
            raise RuntimeError('nested native lifecycle is unsupported')
        if self.current_step >= self.max_steps:
            raise RuntimeError('step after native terminal boundary')
        for agent, action in actions.items():
            value = np.asarray(action)
            if agent not in self.agents or value.shape != (3,) or not np.isfinite(value).all() or np.any(np.abs(value) > 1):
                raise ValueError('invalid native action')
        self._lifecycle, self._pending_generation = 'step', True
        try:
            result = super().step(actions)
            if self._pending_generation:
                raise RuntimeError('native step did not advance its physical channel')
            self._assert_physical_arrays()
            self._physical_counters['native_step_calls_completed'] += 1
            return result
        finally:
            self._lifecycle, self._pending_generation = None, False

    def _begin_path_loss_step(self):
        if self._pending_generation:
            self._assert_configuration()
            if self._lifecycle == 'reset':
                values = self._draw_physical(0)
                residual = self._sigma*values
                tick = 0
                counter = 'physical_initializations'
            elif self._lifecycle == 'step':
                if not np.array_equal(self.user_positions, self._physical_users) or self.current_step != self._physical_tick:
                    raise RuntimeError('unsupported geometry or clock mutation during native step')
                displacement = np.linalg.norm(self.uav_positions-self._physical_positions, axis=1)
                tick = self._physical_tick+1
                values = self._draw_physical(tick)
                rho = np.exp(-displacement/c.CORRELATION_METRES)[:, None]
                residual = rho*self._residual + self._sigma*np.sqrt(1.-rho*rho)*values
                counter = 'physical_updates'
            else:
                raise RuntimeError('physical generation lacks native lifecycle')
            if residual.shape != (c.N_UAVS, c.N_USERS) or not np.isfinite(residual).all():
                raise FloatingPointError('nonfinite user-link residual')
            self._residual, self._physical_tick = residual, tick
            self._physical_positions = self.uav_positions.copy()
            self._physical_users = self.user_positions.copy()
            self._pending_generation = False
            self._physical_counters[counter] += 1
        else:
            self._assert_physical_arrays()
        super()._begin_path_loss_step()

    def _compute_path_loss_matrix(self):
        self._assert_physical_arrays()
        return super()._compute_path_loss_matrix() + self._residual

    def _compute_uav_path_loss_matrix(self):
        self._assert_physical_arrays()
        return super()._compute_uav_path_loss_matrix()

    def _compute_path_loss(self, uav_pos, user_pos):
        self._assert_physical_arrays()
        uavs = np.flatnonzero(np.all(self.uav_positions == np.asarray(uav_pos), axis=1))
        if isinstance(user_pos, (int, np.integer)):
            user_idx = _identifier(user_pos, 'user index')
            if user_idx >= c.N_USERS:
                raise ValueError('user index outside registered links')
            users = np.array([user_idx])
        else:
            users = np.flatnonzero(np.all(self.user_positions == np.asarray(user_pos), axis=1))
        if len(uavs) != 1 or len(users) != 1:
            raise ValueError('scalar correlated loss requires an unambiguous registered link')
        return self._cached_uav_user_path_loss(int(uavs[0]), int(users[0]))

    def _update_channel_state(self, reuse_physical_channel=False):
        self._assert_physical_arrays()
        return super()._update_channel_state(reuse_physical_channel=reuse_physical_channel)

    def _get_observation(self, agent):
        self._assert_physical_arrays()
        return super()._get_observation(agent)

    def set_transmitter_mask(self, mask):
        self._assert_physical_arrays()
        return super().set_transmitter_mask(mask)

    def _cached_uav_user_path_loss(self, uav_idx, user_idx):
        self._assert_physical_arrays()
        if not self._path_loss_matrices_are_current():
            raise RuntimeError('correlated user-loss cache is stale')
        return super()._cached_uav_user_path_loss(uav_idx, user_idx)

    def physical_snapshot(self):
        self._assert_physical_arrays()
        if not self._path_loss_matrices_are_current() or not self._vector_channel_state_is_current():
            raise RuntimeError('snapshot requires the existing current native channel')
        return dict(world=int(self._world), tick=int(self._physical_tick), positions=self.uav_positions.copy(),
            users=self.user_positions.copy(), residual=self._residual.copy(), user_loss=self._uav_user_path_loss_matrix.copy(),
            sinr=self.sinr_matrix.copy(), peer_sinr=self.uav_sinr_matrix.copy(), connections=self.connections.copy(),
            transmitter_mask=self.transmitter_mask, counters=self.physical_counters)


def make_env(seed, horizon=c.HORIZON, sigma=c.SIGMA_DB):
    return ParallelToArrayAdapter(CorrelatedShadowEnv(seed, horizon=horizon, sigma=sigma), seed=seed)
